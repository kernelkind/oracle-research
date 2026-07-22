//! Guarded, non-evaluative execution of all ten Phase 3 learning rounds.

use std::collections::BTreeMap;
use std::env;
use std::ffi::OsString;
use std::fs::{self, File, OpenOptions};
use std::io::{BufReader, BufWriter, Read, Write};
use std::os::unix::fs::{DirBuilderExt, MetadataExt, OpenOptionsExt, PermissionsExt};
use std::path::{Path, PathBuf};
use std::process::ExitCode;
use std::sync::Arc;
use std::sync::atomic::{AtomicBool, Ordering};
use std::thread;
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};

use oracle_mvp::adaptive_learning::CompletedAdaptiveLearning;
use oracle_mvp::adaptive_learning_runner::{AdaptiveLearningRunnerConfig, AdaptiveLearningSeed};
use oracle_mvp::candidate_order::B16Boundary;
use oracle_mvp::fp32_oracle::Fp32OfflineOracle;
use oracle_mvp::gte::{GteProcessEncoder, GteWorkerConfig};
use oracle_mvp::personalizer_learning::{CompactLearningSettings, RbfLearningSettings, ScaleLevel};
use oracle_mvp::phase3_capacity_stress::{
    CapacityMaxima, CapacityReachedCounts, CapacityStressEvaluatorObservation,
    CombinedMemoryLimitObservation, HostMemoryAdmissionObservation, audited_capacity_maxima,
    evict_file_cache, require_combined_memory_limit, require_host_memory_admission,
    resident_file_cache, resolve_unified_cgroup_path, run_capacity_stress,
};
use oracle_mvp::phase3_cost_preflight::{
    create_private_preflight_directory, immutable_tree_metadata_fingerprint,
    prepare_disposable_representation_view, write_private_json_atomic,
};
use oracle_mvp::representation::{EventId, RepresentationManifest, verify_representation};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

const CONFIG_SCHEMA_VERSION: u32 = 1;
const BINDING_SCHEMA_VERSION: u32 = 1;
const REPORT_SCHEMA_VERSION: u32 = 2;
const MEMORY_SAMPLE_INTERVAL: Duration = Duration::from_millis(250);
const CGROUP_MOUNT: &str = "/sys/fs/cgroup";
const MAX_EXTERNAL_INPUT_RESIDENCY_BYTES: u64 = 512 * 1024 * 1024;

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("phase3 capacity stress failed: {error}");
            ExitCode::FAILURE
        }
    }
}

fn run() -> Result<(), String> {
    let mut arguments = env::args_os().skip(1);
    let command = arguments.next().ok_or_else(usage)?;
    let config_path = arguments.next().ok_or_else(usage)?;
    require_no_more(arguments)?;
    let config_path = fs::canonicalize(&config_path).map_err(|error| {
        format!(
            "could not resolve capacity config `{}`: {error}",
            Path::new(&config_path).display()
        )
    })?;
    let config: CapacityStressConfig = read_json(&config_path)?;
    config.validate()?;
    match command.to_str() {
        Some("prepare") => prepare_inputs(&config, &config_path),
        Some("evict-cache") => evict_input_cache(&config, &config_path),
        Some("run") => run_guarded_stress(&config, &config_path),
        _ => Err(usage()),
    }
}

#[derive(Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct CapacityStressConfig {
    schema_version: u32,
    workspace_path: PathBuf,
    report_path: PathBuf,
    memory_samples_path: PathBuf,
    cache_eviction_report_path: PathBuf,
    source_corpus_data_path: PathBuf,
    source_ordered_event_ids_path: PathBuf,
    source_representation_path: PathBuf,
    source_runner_binding_path: PathBuf,
    model_bundle_path: PathBuf,
    expected_representation_version: String,
    expected_geometry_version: String,
    expected_runner_binding_sha256: String,
    expected_memory_max_bytes: u64,
    host_memory_reserve_bytes: u64,
}

impl CapacityStressConfig {
    fn validate(&self) -> Result<(), String> {
        if self.schema_version != CONFIG_SCHEMA_VERSION {
            return Err("capacity config has the wrong schema".to_owned());
        }
        require_sha256(
            &self.expected_representation_version,
            "expected representation version",
        )?;
        require_sha256(&self.expected_geometry_version, "expected geometry version")?;
        require_sha256(
            &self.expected_runner_binding_sha256,
            "expected runner binding SHA-256",
        )?;
        if self.expected_memory_max_bytes == 0 {
            return Err("expected memory ceiling must be positive".to_owned());
        }
        if self.host_memory_reserve_bytes == 0 {
            return Err("host memory reserve must be positive".to_owned());
        }
        let workspace = absolute_lexical(&self.workspace_path)?;
        let workspace_real = resolve_existing_or_absent_child(&workspace)?;
        for output in [
            &self.report_path,
            &self.memory_samples_path,
            &self.cache_eviction_report_path,
        ] {
            let output = absolute_lexical(output)?;
            if !output.starts_with(&workspace) {
                return Err(format!(
                    "capacity output `{}` must remain inside workspace `{}`",
                    output.display(),
                    workspace.display()
                ));
            }
        }
        for source in [
            &self.source_corpus_data_path,
            &self.source_ordered_event_ids_path,
            &self.source_representation_path,
            &self.source_runner_binding_path,
            &self.model_bundle_path,
        ] {
            let source = absolute_lexical(source)?;
            let source = fs::canonicalize(&source)
                .map_err(|error| format!("could not resolve `{}`: {error}", source.display()))?;
            if source.starts_with(&workspace_real) || workspace_real.starts_with(&source) {
                return Err(format!(
                    "capacity source `{}` and workspace `{}` overlap",
                    source.display(),
                    workspace_real.display()
                ));
            }
        }
        Ok(())
    }

    fn corpus_path(&self) -> PathBuf {
        self.workspace_path.join("corpus.ndb")
    }

    fn ordered_event_ids_path(&self) -> PathBuf {
        self.workspace_path.join("ordered-event-ids.bin")
    }

    fn representation_path(&self) -> PathBuf {
        self.workspace_path.join("representation")
    }

    fn prepared_model_bundle_path(&self) -> PathBuf {
        self.workspace_path.join("model-bundle")
    }

    fn session_path(&self) -> PathBuf {
        self.workspace_path.join("phase3-capacity-session.json")
    }

    fn preparation_path(&self) -> PathBuf {
        self.workspace_path.join("preparation.json")
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct SeedConfig {
    event_id: String,
    rating: u8,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct RunnerBinding {
    schema_version: u32,
    corpus_path: PathBuf,
    corpus_identity: String,
    session_path: PathBuf,
    representation_version: String,
    geometry_version: String,
    b16_bits: String,
    h16_bits: String,
    h64_bits: String,
    h256_bits: String,
    s16_bits: String,
    s64_bits: String,
    s256_bits: String,
    seeds: Vec<SeedConfig>,
}

impl RunnerBinding {
    fn runner_config(
        &self,
        config: &CapacityStressConfig,
    ) -> Result<AdaptiveLearningRunnerConfig, String> {
        if self.schema_version != BINDING_SCHEMA_VERSION {
            return Err("source runner binding has the wrong schema".to_owned());
        }
        if self.representation_version != config.expected_representation_version
            || self.geometry_version != config.expected_geometry_version
        {
            return Err(
                "source runner binding does not match the configured representation and geometry"
                    .to_owned(),
            );
        }
        if self.corpus_identity.is_empty() {
            return Err("source runner binding has no corpus identity".to_owned());
        }
        let _ = (&self.corpus_path, &self.session_path);
        let compact_settings = CompactLearningSettings::new(
            self.representation_version.clone(),
            decode_f64_bits(&self.h16_bits, "h16")?,
            decode_f64_bits(&self.h64_bits, "h64")?,
            decode_f64_bits(&self.h256_bits, "h256")?,
            ScaleLevel::Mass64,
        )
        .map_err(|error| error.to_string())?;
        let rbf_settings = RbfLearningSettings::new(
            self.representation_version.clone(),
            decode_f64_bits(&self.s16_bits, "s16")?,
            decode_f64_bits(&self.s64_bits, "s64")?,
            decode_f64_bits(&self.s256_bits, "s256")?,
        )
        .map_err(|error| error.to_string())?;
        let b16 = B16Boundary::new(
            self.representation_version.clone(),
            decode_f64_bits(&self.b16_bits, "b16")?,
        )
        .map_err(|error| error.to_string())?;
        let seeds = self
            .seeds
            .iter()
            .map(|seed| {
                AdaptiveLearningSeed::new(parse_event_id(&seed.event_id)?, seed.rating)
                    .map_err(|error| error.to_string())
            })
            .collect::<Result<Vec<_>, _>>()?;
        Ok(AdaptiveLearningRunnerConfig {
            corpus_path: config.corpus_path(),
            corpus_identity: self.corpus_identity.clone(),
            session_path: config.session_path(),
            compact_settings,
            rbf_settings,
            b16,
            seeds,
        })
    }
}

#[derive(Debug, Serialize)]
struct PreparationReport {
    schema_version: u32,
    purpose: String,
    quality_claim: bool,
    spend_micro_usd: u64,
    config_path: PathBuf,
    config_sha256: String,
    source_representation_path: PathBuf,
    source_metadata_before: String,
    source_metadata_after: String,
    source_unchanged: bool,
    source_model_metadata_before: String,
    source_model_metadata_after: String,
    source_model_unchanged: bool,
    representation_version: String,
    runner_binding_sha256: String,
    represented_rows: u64,
    dimensions: u32,
    corpus_path: PathBuf,
    ordered_event_ids_path: PathBuf,
    representation_path: PathBuf,
    model_bundle_path: PathBuf,
    elapsed_ns: u64,
}

fn prepare_inputs(config: &CapacityStressConfig, config_path: &Path) -> Result<(), String> {
    if config.workspace_path.exists() {
        return Err(format!(
            "capacity workspace already exists: `{}`",
            config.workspace_path.display()
        ));
    }
    let runner_binding_sha256 = require_expected_file_hash(
        &config.source_runner_binding_path,
        &config.expected_runner_binding_sha256,
        "runner binding",
    )?;
    let started = Instant::now();
    let source_metadata_before =
        immutable_tree_metadata_fingerprint(&config.source_representation_path)
            .map_err(|error| error.to_string())?;
    let source_model_metadata_before =
        immutable_tree_metadata_fingerprint(&config.model_bundle_path)
            .map_err(|error| error.to_string())?;
    let parent = config
        .workspace_path
        .parent()
        .unwrap_or_else(|| Path::new("."));
    if !parent.is_dir() {
        return Err(format!(
            "capacity workspace parent is missing: `{}`",
            parent.display()
        ));
    }
    let name = config
        .workspace_path
        .file_name()
        .ok_or_else(|| "capacity workspace has no file name".to_owned())?;
    let stage = parent.join(format!(".{}.prepare", name.to_string_lossy()));
    if stage.exists() {
        return Err(format!(
            "incomplete capacity preparation exists: `{}`",
            stage.display()
        ));
    }
    create_private_preflight_directory(&stage).map_err(|error| error.to_string())?;
    let staged_config = CapacityStressConfig {
        workspace_path: stage.clone(),
        report_path: stage.join("report.json"),
        memory_samples_path: stage.join("memory-samples.jsonl"),
        cache_eviction_report_path: stage.join("cache-eviction.json"),
        ..clone_config(config)
    };
    let prepared = (|| {
        create_private_directory(&staged_config.corpus_path())?;
        copy_private_file(
            &config.source_corpus_data_path,
            &staged_config.corpus_path().join("data.mdb"),
        )?;
        copy_private_file(
            &config.source_ordered_event_ids_path,
            &staged_config.ordered_event_ids_path(),
        )?;
        prepare_disposable_representation_view(
            &config.source_representation_path,
            staged_config.representation_path(),
        )
        .map_err(|error| error.to_string())?;
        copy_private_tree(
            &config.model_bundle_path,
            &staged_config.prepared_model_bundle_path(),
        )?;
        let store = verify_representation(
            staged_config.corpus_path(),
            staged_config.ordered_event_ids_path(),
            staged_config.representation_path(),
        )
        .map_err(|error| error.to_string())?;
        if store.representation_version() != config.expected_representation_version {
            return Err("prepared representation has the wrong version".to_owned());
        }
        let source_metadata_after =
            immutable_tree_metadata_fingerprint(&config.source_representation_path)
                .map_err(|error| error.to_string())?;
        let source_model_metadata_after =
            immutable_tree_metadata_fingerprint(&config.model_bundle_path)
                .map_err(|error| error.to_string())?;
        if source_metadata_after != source_metadata_before {
            return Err("rental representation metadata changed during preparation".to_owned());
        }
        if source_model_metadata_after != source_model_metadata_before {
            return Err("source model bundle metadata changed during preparation".to_owned());
        }
        let report = PreparationReport {
            schema_version: REPORT_SCHEMA_VERSION,
            purpose: "prepare isolated inputs for the non-evaluative Phase 3 capacity run"
                .to_owned(),
            quality_claim: false,
            spend_micro_usd: 0,
            config_path: config_path.to_owned(),
            config_sha256: hash_file(config_path)?,
            source_representation_path: config.source_representation_path.clone(),
            source_metadata_before: source_metadata_before.clone(),
            source_metadata_after,
            source_unchanged: true,
            source_model_metadata_before: source_model_metadata_before.clone(),
            source_model_metadata_after,
            source_model_unchanged: true,
            representation_version: store.representation_version().to_owned(),
            runner_binding_sha256,
            represented_rows: store.manifest().completed_rows,
            dimensions: store.manifest().descriptor.dimensions,
            corpus_path: config.corpus_path(),
            ordered_event_ids_path: config.ordered_event_ids_path(),
            representation_path: config.representation_path(),
            model_bundle_path: config.prepared_model_bundle_path(),
            elapsed_ns: elapsed_ns(started),
        };
        write_private_json_atomic(staged_config.preparation_path(), &report)
            .map_err(|error| error.to_string())?;
        Ok(())
    })();
    prepared?;
    fs::rename(&stage, &config.workspace_path).map_err(|error| {
        format!(
            "could not publish capacity workspace `{}`: {error}",
            config.workspace_path.display()
        )
    })?;
    sync_directory(parent)?;
    Ok(())
}

fn clone_config(config: &CapacityStressConfig) -> CapacityStressConfig {
    CapacityStressConfig {
        schema_version: config.schema_version,
        workspace_path: config.workspace_path.clone(),
        report_path: config.report_path.clone(),
        memory_samples_path: config.memory_samples_path.clone(),
        cache_eviction_report_path: config.cache_eviction_report_path.clone(),
        source_corpus_data_path: config.source_corpus_data_path.clone(),
        source_ordered_event_ids_path: config.source_ordered_event_ids_path.clone(),
        source_representation_path: config.source_representation_path.clone(),
        source_runner_binding_path: config.source_runner_binding_path.clone(),
        model_bundle_path: config.model_bundle_path.clone(),
        expected_representation_version: config.expected_representation_version.clone(),
        expected_geometry_version: config.expected_geometry_version.clone(),
        expected_runner_binding_sha256: config.expected_runner_binding_sha256.clone(),
        expected_memory_max_bytes: config.expected_memory_max_bytes,
        host_memory_reserve_bytes: config.host_memory_reserve_bytes,
    }
}

fn create_private_directory(path: &Path) -> Result<(), String> {
    fs::DirBuilder::new()
        .mode(0o700)
        .create(path)
        .map_err(|error| format!("could not create `{}`: {error}", path.display()))
}

fn copy_private_file(source: &Path, destination: &Path) -> Result<(), String> {
    if !source.is_file() || destination.exists() {
        return Err(format!(
            "capacity copy requires an existing file and absent output: `{}` -> `{}`",
            source.display(),
            destination.display()
        ));
    }
    fs::copy(source, destination).map_err(|error| {
        format!(
            "could not copy `{}` to `{}`: {error}",
            source.display(),
            destination.display()
        )
    })?;
    fs::set_permissions(destination, fs::Permissions::from_mode(0o600))
        .map_err(|error| format!("could not protect `{}`: {error}", destination.display()))?;
    File::open(destination)
        .and_then(|file| file.sync_all())
        .map_err(|error| format!("could not sync `{}`: {error}", destination.display()))
}

fn copy_private_tree(source: &Path, destination: &Path) -> Result<(), String> {
    if !source.is_dir() || destination.exists() {
        return Err(format!(
            "capacity tree copy requires an existing directory and absent output: `{}` -> `{}`",
            source.display(),
            destination.display()
        ));
    }
    create_private_directory(destination)?;
    for entry in fs::read_dir(source)
        .map_err(|error| format!("could not list `{}`: {error}", source.display()))?
    {
        let entry =
            entry.map_err(|error| format!("could not read `{}`: {error}", source.display()))?;
        let metadata = entry
            .file_type()
            .map_err(|error| format!("could not inspect `{}`: {error}", entry.path().display()))?;
        let target = destination.join(entry.file_name());
        if metadata.is_dir() {
            copy_private_tree(&entry.path(), &target)?;
        } else if metadata.is_file() {
            copy_private_file(&entry.path(), &target)?;
        } else {
            return Err(format!(
                "model bundle contains an unsupported entry: `{}`",
                entry.path().display()
            ));
        }
    }
    sync_directory(destination)
}

fn sync_directory(path: &Path) -> Result<(), String> {
    File::open(path)
        .and_then(|file| file.sync_all())
        .map_err(|error| format!("could not sync directory `{}`: {error}", path.display()))
}

#[derive(Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct CacheEvictionReport {
    schema_version: u32,
    purpose: String,
    quality_claim: bool,
    spend_micro_usd: u64,
    config_path: PathBuf,
    config_sha256: String,
    input_files: usize,
    input_bytes: u64,
    resident_before_bytes: u64,
    resident_after_bytes: u64,
    maximum_accepted_resident_after_bytes: u64,
    unix_time_ns: u64,
    elapsed_ns: u64,
}

fn evict_input_cache(config: &CapacityStressConfig, config_path: &Path) -> Result<(), String> {
    require_prepared_inputs(config)?;
    let started = Instant::now();
    let files = collect_regular_files(&[
        config.corpus_path(),
        config.ordered_event_ids_path(),
        config.representation_path(),
        config.prepared_model_bundle_path(),
    ])?;
    let resident_before_bytes = resident_bytes(&files)?;
    let observation = evict_file_cache(&files).map_err(|error| error.to_string())?;
    let resident_after_bytes = resident_bytes(&files)?;
    if resident_after_bytes > MAX_EXTERNAL_INPUT_RESIDENCY_BYTES {
        return Err(format!(
            "immutable inputs retain {resident_after_bytes} page-cache bytes after eviction; maximum is {MAX_EXTERNAL_INPUT_RESIDENCY_BYTES}"
        ));
    }
    let report = CacheEvictionReport {
        schema_version: REPORT_SCHEMA_VERSION,
        purpose: "make the guarded container the first owner of immutable input pages".to_owned(),
        quality_claim: false,
        spend_micro_usd: 0,
        config_path: config_path.to_owned(),
        config_sha256: hash_file(config_path)?,
        input_files: observation.files(),
        input_bytes: observation.bytes(),
        resident_before_bytes,
        resident_after_bytes,
        maximum_accepted_resident_after_bytes: MAX_EXTERNAL_INPUT_RESIDENCY_BYTES,
        unix_time_ns: unix_time_ns()?,
        elapsed_ns: elapsed_ns(started),
    };
    append_private_json_line(&config.cache_eviction_report_path, &report)
}

fn require_prepared_inputs(config: &CapacityStressConfig) -> Result<(), String> {
    for path in [
        config.preparation_path(),
        config.corpus_path().join("data.mdb"),
        config.ordered_event_ids_path(),
        config.representation_path().join("manifest.json"),
        config.representation_path().join("verification.json"),
        config.prepared_model_bundle_path().join("model-lock.json"),
    ] {
        if !path.is_file() {
            return Err(format!(
                "prepared capacity input is missing: `{}`",
                path.display()
            ));
        }
    }
    let model_directory = config.prepared_model_bundle_path().join("model");
    if !model_directory.is_dir() {
        return Err(format!(
            "prepared capacity input is missing: `{}`",
            model_directory.display()
        ));
    }
    Ok(())
}

fn collect_regular_files(roots: &[PathBuf]) -> Result<Vec<PathBuf>, String> {
    let mut files = BTreeMap::new();
    let mut pending = roots.to_vec();
    while let Some(path) = pending.pop() {
        let metadata = fs::metadata(&path)
            .map_err(|error| format!("could not stat `{}`: {error}", path.display()))?;
        if metadata.is_dir() {
            for entry in fs::read_dir(&path)
                .map_err(|error| format!("could not list `{}`: {error}", path.display()))?
            {
                pending.push(
                    entry
                        .map_err(|error| format!("could not read `{}`: {error}", path.display()))?
                        .path(),
                );
            }
        } else if metadata.is_file() {
            let path = fs::canonicalize(&path)
                .map_err(|error| format!("could not resolve `{}`: {error}", path.display()))?;
            files
                .entry((metadata.dev(), metadata.ino()))
                .or_insert(path);
        } else {
            return Err(format!(
                "capacity cache input is neither a file nor directory: `{}`",
                path.display()
            ));
        }
    }
    Ok(files.into_values().collect())
}

fn resident_bytes(files: &[PathBuf]) -> Result<u64, String> {
    resident_file_cache(files)
        .map(|observation| observation.bytes())
        .map_err(|error| error.to_string())
}

#[derive(Clone, Debug, Serialize)]
struct MemorySample {
    invocation_id: String,
    unix_time_ns: u64,
    monotonic_elapsed_ns: u64,
    memory_current_bytes: u64,
    memory_peak_bytes: u64,
    memory_swap_current_bytes: u64,
    memory_anon_bytes: u64,
    memory_file_bytes: u64,
    memory_kernel_bytes: u64,
    memory_events_max: u64,
    memory_events_oom: u64,
    memory_events_oom_kill: u64,
    host_mem_available_bytes: u64,
    host_swap_used_bytes: u64,
    cgroup_pressure: String,
    host_pressure: String,
}

#[derive(Clone, Debug, Default, Serialize)]
struct MemorySummary {
    samples: u64,
    peak_memory_current_bytes: u64,
    cgroup_memory_peak_bytes: u64,
    peak_memory_swap_current_bytes: u64,
    peak_anon_bytes: u64,
    peak_file_bytes: u64,
    peak_kernel_bytes: u64,
    minimum_host_mem_available_bytes: u64,
    maximum_host_swap_used_bytes: u64,
    final_memory_events_max: u64,
    final_memory_events_oom: u64,
    final_memory_events_oom_kill: u64,
}

impl MemorySummary {
    fn observe(&mut self, sample: &MemorySample) {
        self.samples += 1;
        self.peak_memory_current_bytes = self
            .peak_memory_current_bytes
            .max(sample.memory_current_bytes);
        self.cgroup_memory_peak_bytes = self.cgroup_memory_peak_bytes.max(sample.memory_peak_bytes);
        self.peak_memory_swap_current_bytes = self
            .peak_memory_swap_current_bytes
            .max(sample.memory_swap_current_bytes);
        self.peak_anon_bytes = self.peak_anon_bytes.max(sample.memory_anon_bytes);
        self.peak_file_bytes = self.peak_file_bytes.max(sample.memory_file_bytes);
        self.peak_kernel_bytes = self.peak_kernel_bytes.max(sample.memory_kernel_bytes);
        self.minimum_host_mem_available_bytes = if self.minimum_host_mem_available_bytes == 0 {
            sample.host_mem_available_bytes
        } else {
            self.minimum_host_mem_available_bytes
                .min(sample.host_mem_available_bytes)
        };
        self.maximum_host_swap_used_bytes = self
            .maximum_host_swap_used_bytes
            .max(sample.host_swap_used_bytes);
        self.final_memory_events_max = sample.memory_events_max;
        self.final_memory_events_oom = sample.memory_events_oom;
        self.final_memory_events_oom_kill = sample.memory_events_oom_kill;
    }
}

struct MemorySampler {
    stop: Arc<AtomicBool>,
    handle: thread::JoinHandle<Result<MemorySummary, String>>,
}

impl MemorySampler {
    fn start(path: &Path) -> Result<Self, String> {
        let parent = path.parent().unwrap_or_else(|| Path::new("."));
        if !parent.is_dir() {
            return Err(format!(
                "memory-sample parent is missing: `{}`",
                parent.display()
            ));
        }
        let path = path.to_owned();
        let stop = Arc::new(AtomicBool::new(false));
        let thread_stop = Arc::clone(&stop);
        let handle = thread::Builder::new()
            .name("phase3-memory-sampler".to_owned())
            .spawn(move || sample_memory(&path, &thread_stop))
            .map_err(|error| format!("could not start memory sampler: {error}"))?;
        Ok(Self { stop, handle })
    }

    fn stop(self) -> Result<MemorySummary, String> {
        self.stop.store(true, Ordering::Release);
        self.handle
            .join()
            .map_err(|_| "memory sampler panicked".to_owned())?
    }
}

fn sample_memory(path: &Path, stop: &AtomicBool) -> Result<MemorySummary, String> {
    let invocation_id = format!("{}-{}", std::process::id(), unix_time_ns()?);
    let file = OpenOptions::new()
        .create(true)
        .append(true)
        .mode(0o600)
        .open(path)
        .map_err(|error| format!("could not open `{}`: {error}", path.display()))?;
    let mut writer = BufWriter::new(file);
    let started = Instant::now();
    let mut summary = MemorySummary::default();
    loop {
        let sample = read_memory_sample(&invocation_id, started)?;
        serde_json::to_writer(&mut writer, &sample)
            .map_err(|error| format!("could not encode memory sample: {error}"))?;
        writer
            .write_all(b"\n")
            .and_then(|()| writer.flush())
            .map_err(|error| format!("could not write `{}`: {error}", path.display()))?;
        summary.observe(&sample);
        if stop.load(Ordering::Acquire) {
            writer
                .get_ref()
                .sync_data()
                .map_err(|error| format!("could not sync `{}`: {error}", path.display()))?;
            return Ok(summary);
        }
        thread::sleep(MEMORY_SAMPLE_INTERVAL);
    }
}

fn read_memory_sample(invocation_id: &str, started: Instant) -> Result<MemorySample, String> {
    let cgroup = current_cgroup_root()?;
    let memory_stat = read_key_values(&cgroup.join("memory.stat"))?;
    let memory_events = read_key_values(&cgroup.join("memory.events.local"))?;
    let meminfo = read_meminfo(Path::new("/proc/meminfo"))?;
    let swap_total = required_value(&meminfo, "SwapTotal", "/proc/meminfo")?;
    let swap_free = required_value(&meminfo, "SwapFree", "/proc/meminfo")?;
    Ok(MemorySample {
        invocation_id: invocation_id.to_owned(),
        unix_time_ns: unix_time_ns()?,
        monotonic_elapsed_ns: u64::try_from(started.elapsed().as_nanos()).unwrap_or(u64::MAX),
        memory_current_bytes: read_u64(cgroup.join("memory.current"))?,
        memory_peak_bytes: read_u64(cgroup.join("memory.peak"))?,
        memory_swap_current_bytes: read_u64(cgroup.join("memory.swap.current"))?,
        memory_anon_bytes: required_value(&memory_stat, "anon", "memory.stat")?,
        memory_file_bytes: required_value(&memory_stat, "file", "memory.stat")?,
        memory_kernel_bytes: required_value(&memory_stat, "kernel", "memory.stat")?,
        memory_events_max: required_value(&memory_events, "max", "memory.events.local")?,
        memory_events_oom: required_value(&memory_events, "oom", "memory.events.local")?,
        memory_events_oom_kill: required_value(&memory_events, "oom_kill", "memory.events.local")?,
        host_mem_available_bytes: required_value(&meminfo, "MemAvailable", "/proc/meminfo")?,
        host_swap_used_bytes: swap_total.saturating_sub(swap_free),
        cgroup_pressure: read_trimmed(cgroup.join("memory.pressure"))?,
        host_pressure: read_trimmed("/proc/pressure/memory")?,
    })
}

fn read_key_values(path: &Path) -> Result<BTreeMap<String, u64>, String> {
    let contents = fs::read_to_string(path)
        .map_err(|error| format!("could not read `{}`: {error}", path.display()))?;
    contents
        .lines()
        .map(|line| {
            let mut fields = line.split_whitespace();
            let key = fields
                .next()
                .ok_or_else(|| format!("empty line in `{}`", path.display()))?;
            let value = fields
                .next()
                .ok_or_else(|| format!("missing value for `{key}` in `{}`", path.display()))?
                .parse::<u64>()
                .map_err(|error| format!("invalid value for `{key}`: {error}"))?;
            Ok((key.to_owned(), value))
        })
        .collect()
}

fn read_meminfo(path: &Path) -> Result<BTreeMap<String, u64>, String> {
    let contents = fs::read_to_string(path)
        .map_err(|error| format!("could not read `{}`: {error}", path.display()))?;
    contents
        .lines()
        .map(|line| {
            let mut fields = line.split_whitespace();
            let key = fields
                .next()
                .ok_or_else(|| format!("empty line in `{}`", path.display()))?
                .trim_end_matches(':');
            let kibibytes = fields
                .next()
                .ok_or_else(|| format!("missing value for `{key}` in `{}`", path.display()))?
                .parse::<u64>()
                .map_err(|error| format!("invalid value for `{key}`: {error}"))?;
            let bytes = kibibytes
                .checked_mul(1024)
                .ok_or_else(|| format!("`{key}` byte count overflowed"))?;
            Ok((key.to_owned(), bytes))
        })
        .collect()
}

fn required_value(values: &BTreeMap<String, u64>, key: &str, source: &str) -> Result<u64, String> {
    values
        .get(key)
        .copied()
        .ok_or_else(|| format!("`{source}` has no `{key}` value"))
}

fn read_u64(path: impl AsRef<Path>) -> Result<u64, String> {
    let path = path.as_ref();
    read_trimmed(path)?
        .parse()
        .map_err(|error| format!("`{}` is not a byte count: {error}", path.display()))
}

fn read_trimmed(path: impl AsRef<Path>) -> Result<String, String> {
    let path = path.as_ref();
    fs::read_to_string(path)
        .map(|value| value.trim().to_owned())
        .map_err(|error| format!("could not read `{}`: {error}", path.display()))
}

fn unix_time_ns() -> Result<u64, String> {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_err(|error| format!("wall clock precedes Unix epoch: {error}"))?
        .as_nanos()
        .try_into()
        .map_err(|_| "wall-clock nanoseconds exceed u64".to_owned())
}

fn current_cgroup_root() -> Result<PathBuf, String> {
    let process_cgroup = fs::read_to_string("/proc/self/cgroup")
        .map_err(|error| format!("could not read /proc/self/cgroup: {error}"))?;
    resolve_unified_cgroup_path(Path::new(CGROUP_MOUNT), &process_cgroup)
        .map_err(|error| error.to_string())
}

#[derive(Debug, Serialize)]
struct RoundCapacityCounts {
    round: usize,
    compact_sources: usize,
    rbf_sources: usize,
    compact_candidates: usize,
    rbf_candidates: usize,
    retained_attributions: usize,
    accepted_candidates: usize,
    new_rating_routes: usize,
    stored_rating_reuse_routes: usize,
    ratings: usize,
    quota_audit_events: usize,
    shared_audit_events: usize,
}

#[derive(Debug, Serialize)]
struct CacheUsage {
    files: u64,
    source_response_files: u64,
    logical_call_files: u64,
    vector_response_files: u64,
    bytes: u64,
}

#[derive(Debug, Serialize)]
struct CapacityStressReport {
    schema_version: u32,
    purpose: String,
    outcome: String,
    error: Option<String>,
    quality_claim: bool,
    synthetic_ratings_reusable: bool,
    spend_micro_usd: u64,
    config_path: PathBuf,
    config_sha256: String,
    executable_sha256: String,
    representation_version: String,
    geometry_version: String,
    runner_binding_sha256: String,
    represented_rows: u64,
    dimensions: u32,
    source_representation_path: PathBuf,
    source_metadata_before: String,
    source_metadata_after: String,
    source_unchanged: bool,
    memory_limit: CombinedMemoryLimitObservation,
    host_memory_admission: HostMemoryAdmissionObservation,
    cache_eviction: CacheEvictionReport,
    input_residency_at_start_bytes: u64,
    memory_samples_path: PathBuf,
    memory_samples_sha256: String,
    memory: MemorySummary,
    evaluator: Option<CapacityStressEvaluatorObservation>,
    reached: Option<CapacityReachedCounts>,
    maxima: CapacityMaxima,
    rounds: Vec<RoundCapacityCounts>,
    session_path: PathBuf,
    session_bytes: u64,
    cache: CacheUsage,
    boundary_log_path: PathBuf,
    boundary_log_sha256: Option<String>,
    elapsed_ns: u64,
}

struct SuccessfulStress {
    evaluator: CapacityStressEvaluatorObservation,
    reached: CapacityReachedCounts,
    rounds: Vec<RoundCapacityCounts>,
}

fn run_guarded_stress(config: &CapacityStressConfig, config_path: &Path) -> Result<(), String> {
    require_prepared_inputs(config)?;
    if config.report_path.exists() {
        return Err(format!(
            "capacity report already exists: `{}`",
            config.report_path.display()
        ));
    }
    let cache_eviction: CacheEvictionReport =
        read_last_json_line(&config.cache_eviction_report_path)?;
    if cache_eviction.schema_version != REPORT_SCHEMA_VERSION
        || cache_eviction.config_sha256 != hash_file(config_path)?
        || cache_eviction.resident_after_bytes > MAX_EXTERNAL_INPUT_RESIDENCY_BYTES
    {
        return Err("capacity cache-eviction receipt is incompatible".to_owned());
    }
    let input_files = collect_regular_files(&[
        config.corpus_path(),
        config.ordered_event_ids_path(),
        config.representation_path(),
        config.prepared_model_bundle_path(),
    ])?;
    let input_residency_at_start_bytes = resident_bytes(&input_files)?;
    if input_residency_at_start_bytes > MAX_EXTERNAL_INPUT_RESIDENCY_BYTES {
        return Err(format!(
            "immutable inputs regained {input_residency_at_start_bytes} resident bytes after eviction; run evict-cache again"
        ));
    }
    let cgroup_root = current_cgroup_root()?;
    let memory_limit =
        require_combined_memory_limit(&cgroup_root, config.expected_memory_max_bytes)
            .map_err(|error| error.to_string())?;
    let host_meminfo = read_meminfo(Path::new("/proc/meminfo"))?;
    let host_swap_total = required_value(&host_meminfo, "SwapTotal", "/proc/meminfo")?;
    let host_swap_free = required_value(&host_meminfo, "SwapFree", "/proc/meminfo")?;
    let host_memory_admission = require_host_memory_admission(
        required_value(&host_meminfo, "MemAvailable", "/proc/meminfo")?,
        host_swap_total.saturating_sub(host_swap_free),
        config.host_memory_reserve_bytes,
        config.expected_memory_max_bytes,
    )
    .map_err(|error| error.to_string())?;
    let manifest_path = config.representation_path().join("manifest.json");
    let representation_version = hash_file(&manifest_path)?;
    let manifest: RepresentationManifest = read_json(&manifest_path)?;
    if representation_version != config.expected_representation_version
        || !manifest.complete
        || manifest.completed_rows != manifest.total_rows
    {
        return Err("prepared representation is not the configured complete artifact".to_owned());
    }
    let binding: RunnerBinding = read_json(&config.source_runner_binding_path)?;
    let runner_binding_sha256 = require_expected_file_hash(
        &config.source_runner_binding_path,
        &config.expected_runner_binding_sha256,
        "runner binding",
    )?;
    let runner_config = binding.runner_config(config)?;
    let executable = fs::canonicalize(
        env::current_exe().map_err(|error| format!("could not locate executable: {error}"))?,
    )
    .map_err(|error| format!("could not resolve executable: {error}"))?;
    let source_metadata_before =
        immutable_tree_metadata_fingerprint(&config.source_representation_path)
            .map_err(|error| error.to_string())?;
    let sampler = MemorySampler::start(&config.memory_samples_path)?;
    let started = Instant::now();
    let execution = execute_stress(config, &manifest, &runner_config);
    let memory = sampler.stop()?;
    let source_metadata_after =
        immutable_tree_metadata_fingerprint(&config.source_representation_path)
            .map_err(|error| error.to_string())?;
    let source_unchanged = source_metadata_before == source_metadata_after;
    let cache_path = oracle_cache_path(&runner_config.session_path)?;
    let cache = directory_usage(&cache_path)?;
    let maxima = audited_capacity_maxima();
    let execution = match execution {
        Ok(success) => maxima
            .require_not_exceeded(
                &success.reached,
                cache.files,
                cache.source_response_files,
                cache.logical_call_files,
                cache.vector_response_files,
            )
            .map(|()| success)
            .map_err(|error| error.to_string()),
        Err(error) => Err(error),
    };
    let (outcome, error, evaluator, reached, rounds) = match execution {
        Ok(success) => (
            "complete".to_owned(),
            None,
            Some(success.evaluator),
            Some(success.reached),
            success.rounds,
        ),
        Err(error) => ("failed".to_owned(), Some(error), None, None, Vec::new()),
    };
    let session_bytes = fs::metadata(&runner_config.session_path)
        .map(|metadata| metadata.len())
        .unwrap_or(0);
    let boundary_log_path =
        oracle_mvp::phase3_capacity_stress::capacity_boundary_log_path(&runner_config.session_path)
            .map_err(|error| error.to_string())?;
    let report = CapacityStressReport {
        schema_version: REPORT_SCHEMA_VERSION,
        purpose: "measure unchanged ten-round Phase 3 capacity with synthetic all-7 ratings"
            .to_owned(),
        outcome: outcome.clone(),
        error: error.clone(),
        quality_claim: false,
        synthetic_ratings_reusable: false,
        spend_micro_usd: 0,
        config_path: config_path.to_owned(),
        config_sha256: hash_file(config_path)?,
        executable_sha256: hash_file(&executable)?,
        representation_version,
        geometry_version: binding.geometry_version,
        runner_binding_sha256,
        represented_rows: manifest.completed_rows,
        dimensions: manifest.descriptor.dimensions,
        source_representation_path: config.source_representation_path.clone(),
        source_metadata_before,
        source_metadata_after,
        source_unchanged,
        memory_limit,
        host_memory_admission,
        cache_eviction,
        input_residency_at_start_bytes,
        memory_samples_path: config.memory_samples_path.clone(),
        memory_samples_sha256: hash_file(&config.memory_samples_path)?,
        memory,
        evaluator,
        reached,
        maxima,
        rounds,
        session_path: runner_config.session_path.clone(),
        session_bytes,
        cache,
        boundary_log_sha256: boundary_log_path
            .is_file()
            .then(|| hash_file(&boundary_log_path))
            .transpose()?,
        boundary_log_path,
        elapsed_ns: elapsed_ns(started),
    };
    let report_path = if outcome == "complete" {
        config.report_path.clone()
    } else {
        failed_report_path(&config.report_path)?
    };
    write_private_json_atomic(&report_path, &report).map_err(|error| error.to_string())?;
    if !source_unchanged {
        return Err("rental representation metadata changed during capacity run".to_owned());
    }
    if let Some(error) = error {
        Err(format!(
            "capacity run failed; report written to `{}`: {error}",
            report_path.display()
        ))
    } else {
        Ok(())
    }
}

fn execute_stress(
    config: &CapacityStressConfig,
    manifest: &RepresentationManifest,
    runner_config: &AdaptiveLearningRunnerConfig,
) -> Result<SuccessfulStress, String> {
    let descriptor = &manifest.descriptor;
    let encoder = GteProcessEncoder::start(GteWorkerConfig {
        program: "/opt/gte-venv/bin/python".into(),
        prefix_arguments: Vec::new(),
        worker_path: Some("/opt/oracle-mvp/gte/worker.py".into()),
        model_dir: config.prepared_model_bundle_path().join("model"),
        model_lock_path: config.prepared_model_bundle_path().join("model-lock.json"),
        dependency_lock_path: "/tmp/gte-locks/requirements.lock".into(),
        device: "cpu".to_owned(),
        model_lock_sha256: descriptor.model_lock_sha256.clone(),
        worker_sha256: descriptor.worker_sha256.clone(),
        dependency_lock_sha256: descriptor.dependency_lock_sha256.clone(),
        container_image: descriptor.container_image.clone(),
        torch_version: descriptor.torch_version.clone(),
        transformers_version: descriptor.transformers_version.clone(),
        cuda_version: descriptor.cuda_version.clone(),
    })
    .map_err(|error| error.to_string())?;
    let mut oracle = Fp32OfflineOracle::open(
        config.corpus_path(),
        config.ordered_event_ids_path(),
        config.representation_path(),
        encoder,
    )
    .map_err(|error| error.to_string())?;
    let run = run_capacity_stress(runner_config, &mut oracle).map_err(|error| error.to_string())?;
    let seed_event_ids = runner_config
        .seeds
        .iter()
        .map(|seed| seed.event_id())
        .collect::<Vec<_>>();
    let reached = CapacityReachedCounts::from_completed(run.completed(), &seed_event_ids)
        .map_err(|error| error.to_string())?;
    let rounds = round_capacity_counts(run.completed());
    let evaluator = run.observation().clone();
    Ok(SuccessfulStress {
        evaluator,
        reached,
        rounds,
    })
}

fn round_capacity_counts(completed: &CompletedAdaptiveLearning) -> Vec<RoundCapacityCounts> {
    completed
        .round_records()
        .iter()
        .map(|round| {
            let compact = round.compact_order().attempt();
            let rbf = round.rbf_order().attempt();
            RoundCapacityCounts {
                round: round.round(),
                compact_sources: compact.source_responses().len(),
                rbf_sources: rbf.source_responses().len(),
                compact_candidates: compact.candidates().len(),
                rbf_candidates: rbf.candidates().len(),
                retained_attributions: compact
                    .candidates()
                    .iter()
                    .chain(rbf.candidates())
                    .map(|candidate| candidate.attributions().len())
                    .sum(),
                accepted_candidates: compact.accepted().len() + rbf.accepted().len(),
                new_rating_routes: round.quota_metadata().new_rating_routes().len(),
                stored_rating_reuse_routes: round
                    .quota_metadata()
                    .stored_rating_reuse_routes()
                    .len(),
                ratings: round.ratings().len(),
                quota_audit_events: round.quota_metadata().audit().len(),
                shared_audit_events: round.audit().len(),
            }
        })
        .collect()
}

fn oracle_cache_path(session_path: &Path) -> Result<PathBuf, String> {
    let name = session_path
        .file_name()
        .and_then(|name| name.to_str())
        .ok_or_else(|| format!("non-UTF-8 session path `{}`", session_path.display()))?;
    Ok(session_path
        .parent()
        .unwrap_or_else(|| Path::new("."))
        .join(format!(".{name}.oracle-responses")))
}

fn directory_usage(path: &Path) -> Result<CacheUsage, String> {
    if !path.exists() {
        return Ok(CacheUsage {
            files: 0,
            source_response_files: 0,
            logical_call_files: 0,
            vector_response_files: 0,
            bytes: 0,
        });
    }
    let mut files = 0_u64;
    let mut source_response_files = 0_u64;
    let mut logical_call_files = 0_u64;
    let mut vector_response_files = 0_u64;
    let mut bytes = 0_u64;
    let mut pending = vec![path.to_owned()];
    while let Some(path) = pending.pop() {
        let metadata = fs::symlink_metadata(&path)
            .map_err(|error| format!("could not stat `{}`: {error}", path.display()))?;
        if metadata.is_dir() {
            for entry in fs::read_dir(&path)
                .map_err(|error| format!("could not list `{}`: {error}", path.display()))?
            {
                pending.push(
                    entry
                        .map_err(|error| format!("could not read `{}`: {error}", path.display()))?
                        .path(),
                );
            }
        } else if metadata.is_file() {
            files += 1;
            if let Some(name) = path.file_name().and_then(|name| name.to_str()) {
                if is_hashed_json_name(name, "") {
                    source_response_files += 1;
                } else if is_hashed_json_name(name, "call-") {
                    logical_call_files += 1;
                } else if is_hashed_json_name(name, "vectors-") {
                    vector_response_files += 1;
                }
            }
            bytes = bytes
                .checked_add(metadata.len())
                .ok_or_else(|| "cache byte count overflowed".to_owned())?;
        }
    }
    Ok(CacheUsage {
        files,
        source_response_files,
        logical_call_files,
        vector_response_files,
        bytes,
    })
}

fn is_hashed_json_name(name: &str, prefix: &str) -> bool {
    let Some(hash) = name
        .strip_prefix(prefix)
        .and_then(|name| name.strip_suffix(".json"))
    else {
        return false;
    };
    hash.len() == 64
        && hash
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

fn failed_report_path(report_path: &Path) -> Result<PathBuf, String> {
    let name = report_path
        .file_name()
        .and_then(|name| name.to_str())
        .ok_or_else(|| format!("non-UTF-8 report path `{}`", report_path.display()))?;
    Ok(report_path
        .parent()
        .unwrap_or_else(|| Path::new("."))
        .join(format!("{name}.failed-{}.json", unix_time_ns()?)))
}

fn absolute_lexical(path: &Path) -> Result<PathBuf, String> {
    if !path.is_absolute()
        || path.components().any(|component| {
            matches!(
                component,
                std::path::Component::CurDir | std::path::Component::ParentDir
            )
        })
    {
        return Err(format!(
            "capacity path must be absolute and normalized: `{}`",
            path.display()
        ));
    }
    Ok(path.to_owned())
}

fn resolve_existing_or_absent_child(path: &Path) -> Result<PathBuf, String> {
    if path.exists() {
        return fs::canonicalize(path)
            .map_err(|error| format!("could not resolve `{}`: {error}", path.display()));
    }
    let parent = path
        .parent()
        .ok_or_else(|| format!("capacity path has no parent: `{}`", path.display()))?;
    let name = path
        .file_name()
        .ok_or_else(|| format!("capacity path has no file name: `{}`", path.display()))?;
    fs::canonicalize(parent)
        .map(|parent| parent.join(name))
        .map_err(|error| format!("could not resolve `{}`: {error}", parent.display()))
}

fn parse_event_id(value: &str) -> Result<EventId, String> {
    if value.len() != 64 {
        return Err("event ID must contain 64 lowercase hexadecimal digits".to_owned());
    }
    let mut event_id = [0_u8; 32];
    for (index, pair) in value.as_bytes().chunks_exact(2).enumerate() {
        event_id[index] = (decode_hex(pair[0])? << 4) | decode_hex(pair[1])?;
    }
    Ok(event_id)
}

fn decode_hex(byte: u8) -> Result<u8, String> {
    match byte {
        b'0'..=b'9' => Ok(byte - b'0'),
        b'a'..=b'f' => Ok(byte - b'a' + 10),
        _ => Err("event ID must use lowercase hexadecimal".to_owned()),
    }
}

fn decode_f64_bits(bits: &str, label: &str) -> Result<f64, String> {
    if bits.len() != 16
        || !bits
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err(format!(
            "{label} is not a lowercase 16-digit f64 bit pattern"
        ));
    }
    let value = f64::from_bits(
        u64::from_str_radix(bits, 16).map_err(|error| format!("invalid {label}: {error}"))?,
    );
    if !value.is_finite() || value < 0.0 {
        return Err(format!("{label} is not a finite nonnegative f64"));
    }
    Ok(value)
}

fn read_json<T: for<'de> Deserialize<'de>>(path: &Path) -> Result<T, String> {
    let file = File::open(path)
        .map_err(|error| format!("could not open `{}`: {error}", path.display()))?;
    serde_json::from_reader(BufReader::new(file))
        .map_err(|error| format!("could not decode `{}`: {error}", path.display()))
}

fn read_last_json_line<T: for<'de> Deserialize<'de>>(path: &Path) -> Result<T, String> {
    let contents = fs::read_to_string(path)
        .map_err(|error| format!("could not read `{}`: {error}", path.display()))?;
    let line = contents
        .lines()
        .next_back()
        .ok_or_else(|| format!("`{}` is empty", path.display()))?;
    serde_json::from_str(line).map_err(|error| {
        format!(
            "could not decode latest `{}` record: {error}",
            path.display()
        )
    })
}

fn append_private_json_line<T: Serialize>(path: &Path, value: &T) -> Result<(), String> {
    let mut file = OpenOptions::new()
        .create(true)
        .append(true)
        .mode(0o600)
        .open(path)
        .map_err(|error| format!("could not open `{}`: {error}", path.display()))?;
    serde_json::to_writer(&mut file, value)
        .map_err(|error| format!("could not encode `{}`: {error}", path.display()))?;
    file.write_all(b"\n")
        .and_then(|()| file.sync_data())
        .map_err(|error| format!("could not sync `{}`: {error}", path.display()))
}

fn hash_file(path: &Path) -> Result<String, String> {
    let file = File::open(path)
        .map_err(|error| format!("could not open `{}`: {error}", path.display()))?;
    let mut reader = BufReader::new(file);
    let mut hasher = Sha256::new();
    let mut buffer = [0_u8; 1024 * 1024];
    loop {
        let bytes = reader
            .read(&mut buffer)
            .map_err(|error| format!("could not read `{}`: {error}", path.display()))?;
        if bytes == 0 {
            break;
        }
        hasher.update(&buffer[..bytes]);
    }
    Ok(format!("{:x}", hasher.finalize()))
}

fn require_expected_file_hash(path: &Path, expected: &str, label: &str) -> Result<String, String> {
    let actual = hash_file(path)?;
    if actual != expected {
        return Err(format!("{label} SHA-256 is {actual}; expected {expected}"));
    }
    Ok(actual)
}

fn require_sha256(value: &str, label: &str) -> Result<(), String> {
    if value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        Ok(())
    } else {
        Err(format!("{label} must be a lowercase SHA-256"))
    }
}

fn elapsed_ns(started: Instant) -> u64 {
    u64::try_from(started.elapsed().as_nanos()).unwrap_or(u64::MAX)
}

fn require_no_more(mut arguments: impl Iterator<Item = OsString>) -> Result<(), String> {
    if arguments.next().is_some() {
        Err(usage())
    } else {
        Ok(())
    }
}

fn usage() -> String {
    "usage: phase3-capacity-stress <prepare|evict-cache|run> CONFIG.json".to_owned()
}
