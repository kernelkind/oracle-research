//! Read-only full-scale cost preflight for the first Phase 3 learning wave.

use std::env;
use std::ffi::OsString;
use std::fs::{self, File};
use std::io::{BufReader, Read};
use std::os::unix::fs::MetadataExt;
use std::path::{Path, PathBuf};
use std::process::{Command, ExitCode, Stdio};
use std::thread;
use std::time::{Duration, Instant};

use oracle_mvp::adaptive_learning_runner::{AdaptiveLearningRunnerConfig, AdaptiveLearningSeed};
use oracle_mvp::candidate_order::{B16Boundary, CANDIDATE_DEPTH, CandidateOrderPhase};
use oracle_mvp::fp32_oracle::{Fp32OfflineOracle, SimilarNotesRequest, SimilarNotesWaveMetrics};
use oracle_mvp::gte::{GteProcessEncoder, GteWorkerConfig};
use oracle_mvp::personalizer_learning::{CompactLearningSettings, RbfLearningSettings, ScaleLevel};
use oracle_mvp::phase3_cost_preflight::{
    FirstRoundCostObservation, FirstRoundReplayObservation, RepresentationViewObservation,
    create_private_preflight_directory, gte_container_prefix_arguments,
    immutable_content_tree_identity, immutable_tree_metadata_fingerprint,
    prepare_disposable_representation_view, replay_first_round_cost_preflight,
    resolve_output_outside_tree, run_first_round_cost_preflight, write_private_json_atomic,
};
use oracle_mvp::representation::{
    EventId, FP32_SCAN_BLOCK_ROWS, RepresentationManifest, verify_representation,
};
use oracle_mvp::representation_geometry::{
    RepresentationGeometryArtifact, open_representation_geometry,
};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

const CONFIG_SCHEMA_VERSION: u32 = 1;
const REPORT_SCHEMA_VERSION: u32 = 1;
const BINDING_SCHEMA_VERSION: u32 = 1;
const REPLAY_SCHEMA_VERSION: u32 = 1;
const SESSION_FILE: &str = "phase3-session.json";
const RUNNER_BINDING_FILE: &str = "runner-binding.json";
const REPLAY_OBSERVATION_FILE: &str = "replay-observation.json";

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("phase3 cost preflight failed: {error}");
            ExitCode::FAILURE
        }
    }
}

fn run() -> Result<(), String> {
    let mut arguments = env::args_os().skip(1);
    let first = arguments.next().ok_or_else(usage)?;
    if first == "__replay" {
        let config_path = arguments.next().ok_or_else(usage)?;
        require_no_more(arguments)?;
        return replay_in_fresh_process(Path::new(&config_path));
    }
    require_no_more(arguments)?;
    run_full_preflight(Path::new(&first))
}

fn run_full_preflight(config_path: &Path) -> Result<(), String> {
    let total_started = Instant::now();
    let executable_path = fs::canonicalize(
        env::current_exe().map_err(|error| format!("could not locate executable: {error}"))?,
    )
    .map_err(|error| format!("could not resolve executable: {error}"))?;
    let executable_sha256 = hash_file(&executable_path)?;
    let config_path = fs::canonicalize(config_path)
        .map_err(|error| format!("could not resolve `{}`: {error}", config_path.display()))?;
    let config_sha256 = hash_file(&config_path)?;
    let config: FullScalePreflightConfig = read_json(&config_path)?;
    config.validate()?;
    let outputs = resolve_preflight_outputs(&config)?;

    let source_manifest_path = config.source_representation_path.join("manifest.json");
    let source_manifest: RepresentationManifest = read_json(&source_manifest_path)?;
    let representation_version = hash_file(&source_manifest_path)?;
    if representation_version != config.expected_representation_version {
        return Err(
            "source representation version does not match the configured version".to_owned(),
        );
    }
    if source_manifest.descriptor.container_image != config.container_image {
        return Err("configured container image does not match the representation".to_owned());
    }
    let geometry_manifest_path = config.geometry_path.join("manifest.json");
    if hash_file(&geometry_manifest_path)? != config.expected_geometry_version {
        return Err("geometry manifest does not match the configured version".to_owned());
    }
    let image_id = docker_image_id(&config.container_runtime, &config.container_image)?;
    require_container_name_available(&config.container_runtime, &config.container_name)?;
    let worker_config = worker_config(&config, &source_manifest)?;
    let source_representation_metadata_before =
        immutable_tree_metadata_fingerprint(&config.source_representation_path)
            .map_err(|error| error.to_string())?;

    eprintln!("staging disposable inputs");
    create_private_preflight_directory(&outputs.workspace_path)
        .map_err(|error| error.to_string())?;
    let staging_started = Instant::now();
    let corpus_path = outputs.workspace_path.join("corpus.ndb");
    fs::create_dir(&corpus_path)
        .map_err(|error| format!("could not create `{}`: {error}", corpus_path.display()))?;
    let corpus_data_path = corpus_path.join("data.mdb");
    copy_and_require_sha256(
        &config.source_corpus_data_path,
        &corpus_data_path,
        &source_manifest.corpus_data_sha256,
    )?;
    let ordered_path = outputs.workspace_path.join("ordered-event-ids.bin");
    copy_and_require_sha256(
        &config.source_ordered_event_ids_path,
        &ordered_path,
        &source_manifest.ordered_event_ids_sha256,
    )?;
    let representation_path = outputs.workspace_path.join("representation");
    let representation_view = prepare_disposable_representation_view(
        &config.source_representation_path,
        &representation_path,
    )
    .map_err(|error| error.to_string())?;
    let staging_elapsed_ns = elapsed_ns(staging_started);

    eprintln!("deep-verifying the disposable representation view");
    let verification_started = Instant::now();
    let verified = verify_representation(&corpus_path, &ordered_path, &representation_path)
        .map_err(|error| error.to_string())?;
    if verified.representation_version() != config.expected_representation_version {
        return Err("disposable representation view has the wrong version".to_owned());
    }
    let verification_elapsed_ns = elapsed_ns(verification_started);
    drop(verified);

    eprintln!("opening the frozen representation geometry");
    let geometry_started = Instant::now();
    let geometry =
        open_representation_geometry(&ordered_path, &representation_path, &config.geometry_path)
            .map_err(|error| error.to_string())?;
    if geometry.geometry_version() != config.expected_geometry_version {
        return Err("geometry artifact version does not match the configured version".to_owned());
    }
    let geometry_open_elapsed_ns = elapsed_ns(geometry_started);
    let binding = RunnerBinding::from_verified_inputs(
        &config,
        &geometry,
        corpus_path.clone(),
        outputs.workspace_path.join(SESSION_FILE),
    )?;
    let binding_path = outputs.workspace_path.join(RUNNER_BINDING_FILE);
    write_private_json_atomic(&binding_path, &binding).map_err(|error| error.to_string())?;
    let binding_sha256 = hash_file(&binding_path)?;
    let runner_config = binding.runner_config()?;

    eprintln!("starting the exact CPU query-role worker");
    let worker_started = Instant::now();
    let encoder = GteProcessEncoder::start(worker_config).map_err(|error| error.to_string())?;
    let worker_startup_elapsed_ns = elapsed_ns(worker_started);
    let worker_pid = docker_container_pid(&config.container_runtime, &config.container_name)?;
    process_peak_rss_bytes(worker_pid)?;
    let oracle_open_started = Instant::now();
    let mut oracle =
        Fp32OfflineOracle::open(&corpus_path, &ordered_path, &representation_path, encoder)
            .map_err(|error| error.to_string())?;
    let oracle_open_elapsed_ns = elapsed_ns(oracle_open_started);

    eprintln!("running one exact five-query matrix scan and building both first-round orders");
    let first_round = run_first_round_cost_preflight(&runner_config, &mut oracle)
        .map_err(|error| error.to_string())?;
    let worker_peak_rss_bytes = process_peak_rss_bytes(worker_pid)?;
    let controller_peak_rss_bytes = process_peak_rss_bytes(std::process::id())?;
    drop(oracle);
    let worker_removed_after_shutdown = wait_for_container_removal(
        &config.container_runtime,
        &config.container_name,
        Duration::from_secs(10),
    )?;
    if !worker_removed_after_shutdown {
        return Err("query worker container remained after its clean shutdown".to_owned());
    }

    let cache_path = oracle_cache_path(&runner_config.session_path)?;
    let replay_artifacts_before =
        ReplayArtifactState::capture(&runner_config.session_path, &cache_path)?;
    let replay_path = outputs.workspace_path.join(REPLAY_OBSERVATION_FILE);
    eprintln!("proving fresh-process recovery from the durable cache only");
    let replay_started = Instant::now();
    let status = Command::new(env::current_exe().map_err(|error| error.to_string())?)
        .arg("__replay")
        .arg(&config_path)
        .stdin(Stdio::null())
        .stdout(Stdio::inherit())
        .stderr(Stdio::inherit())
        .status()
        .map_err(|error| format!("could not start cache-only replay: {error}"))?;
    if !status.success() {
        return Err(format!("cache-only replay exited with {status}"));
    }
    let replay_process_elapsed_ns = elapsed_ns(replay_started);
    let replay: ReplayProcessObservation = read_json(&replay_path)?;
    if replay.schema_version != REPLAY_SCHEMA_VERSION {
        return Err("cache-only replay observation has the wrong schema".to_owned());
    }
    let replay_artifacts_after =
        ReplayArtifactState::capture(&runner_config.session_path, &cache_path)?;
    let replay_artifacts = ReplayArtifactComparison {
        cache_unchanged: replay_artifacts_before.cache_content_sha256
            == replay_artifacts_after.cache_content_sha256,
        before: replay_artifacts_before,
        after: replay_artifacts_after,
    };
    if !replay_artifacts.cache_unchanged {
        return Err("cache-only replay changed the durable Oracle cache".to_owned());
    }

    let seed_ids = binding
        .seeds
        .iter()
        .map(|seed| parse_event_id(&seed.event_id))
        .collect::<Result<Vec<_>, _>>()?;
    let session_metrics = read_session_metrics(
        &runner_config.session_path,
        &seed_ids,
        source_manifest.total_rows,
    )?;
    let workspace_usage = path_usage(&outputs.workspace_path)?;
    let cache_usage = path_usage(&cache_path)?;
    let session_bytes = fs::metadata(&runner_config.session_path)
        .map_err(|error| format!("could not stat session: {error}"))?
        .len();
    let session_sha256 = hash_file(&runner_config.session_path)?;
    let corpus_sha256_after = hash_file(&corpus_data_path)?;
    if corpus_sha256_after != source_manifest.corpus_data_sha256 {
        return Err("the disposable NostrDB data file changed during lookup".to_owned());
    }
    let source_representation_metadata_after =
        immutable_tree_metadata_fingerprint(&config.source_representation_path)
            .map_err(|error| error.to_string())?;
    if source_representation_metadata_after != source_representation_metadata_before {
        return Err("the rental representation changed during the preflight".to_owned());
    }

    let report = FullScalePreflightReport {
        schema_version: REPORT_SCHEMA_VERSION,
        purpose: "non-evaluative first-round Phase 3 cost preflight".to_owned(),
        quality_claim: false,
        spend_micro_usd: 0,
        executable_path,
        executable_sha256,
        config_path,
        config_sha256,
        representation_version,
        geometry_version: geometry.geometry_version().to_owned(),
        represented_rows: source_manifest.total_rows,
        dimensions: source_manifest.descriptor.dimensions,
        source_representation_path: config.source_representation_path.clone(),
        source_representation_metadata_before,
        source_representation_metadata_after,
        source_representation_unchanged: true,
        disposable_corpus_path: corpus_path,
        disposable_ordered_event_ids_path: ordered_path,
        disposable_representation_path: representation_path,
        representation_view,
        binding_path,
        binding_sha256,
        staging_elapsed_ns,
        verification_elapsed_ns,
        geometry_open_elapsed_ns,
        matrix_scan_cache_condition: "uncontrolled, warm-biased: the required complete deep verification read every vector shard immediately before the scan".to_owned(),
        cold_start_timing_valid: false,
        worker: WorkerObservation {
            container_image: config.container_image.clone(),
            local_image_id: image_id,
            container_name: config.container_name.clone(),
            query_device: "cpu".to_owned(),
            startup_elapsed_ns: worker_startup_elapsed_ns,
            peak_rss_bytes: worker_peak_rss_bytes,
            removed_after_shutdown: worker_removed_after_shutdown,
        },
        oracle_open_elapsed_ns,
        controller_peak_rss_bytes,
        first_round,
        session_metrics,
        replay_cache_condition: "warm-biased: the complete durable cache was content-hashed immediately before replay".to_owned(),
        replay_process_elapsed_ns,
        replay,
        replay_artifacts,
        session_path: runner_config.session_path,
        session_bytes,
        session_sha256,
        cache_path,
        cache_usage,
        workspace_usage,
        configured_per_personalizer_order_quota: CandidateOrderPhase::Learning.accepted_count(),
        configured_learning_primary_quota: CandidateOrderPhase::Learning.primary_count(),
        total_elapsed_ns: elapsed_ns(total_started),
        scope_limit: "one first round measures the real initial cost but does not bound all ten adaptive rounds".to_owned(),
        next_measurement: "use these measured coefficients to bound later-round source and cache growth before beginning human ratings".to_owned(),
    };
    eprintln!("publishing the preflight report");
    write_private_json_atomic(&outputs.report_path, &report).map_err(|error| error.to_string())?;
    println!("{}", outputs.report_path.display());
    Ok(())
}

fn replay_in_fresh_process(config_path: &Path) -> Result<(), String> {
    let config: FullScalePreflightConfig = read_json(config_path)?;
    config.validate()?;
    let workspace_path = require_existing_output_outside_inputs(&config, &config.workspace_path)?;
    let binding_path = workspace_path.join(RUNNER_BINDING_FILE);
    let binding: RunnerBinding = read_json(&binding_path)?;
    if binding.schema_version != BINDING_SCHEMA_VERSION {
        return Err("runner binding has the wrong schema".to_owned());
    }
    let source_manifest: RepresentationManifest =
        read_json(&config.source_representation_path.join("manifest.json"))?;
    if binding.corpus_path != workspace_path.join("corpus.ndb")
        || binding.session_path != workspace_path.join(SESSION_FILE)
        || binding.corpus_identity != format!("sha256:{}", source_manifest.corpus_data_sha256)
        || binding.representation_version != config.expected_representation_version
        || binding.geometry_version != config.expected_geometry_version
        || binding.seeds != config.seeds
    {
        return Err(
            "runner binding does not match the configured disposable replay inputs".to_owned(),
        );
    }
    let runner_config = binding.runner_config()?;
    let observation =
        replay_first_round_cost_preflight(&runner_config).map_err(|error| error.to_string())?;
    let process = ReplayProcessObservation {
        schema_version: REPLAY_SCHEMA_VERSION,
        observation,
        peak_rss_bytes: process_peak_rss_bytes(std::process::id())?,
    };
    write_private_json_atomic(workspace_path.join(REPLAY_OBSERVATION_FILE), &process)
        .map_err(|error| error.to_string())
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct FullScalePreflightConfig {
    schema_version: u32,
    workspace_path: PathBuf,
    report_path: PathBuf,
    source_corpus_data_path: PathBuf,
    source_ordered_event_ids_path: PathBuf,
    source_representation_path: PathBuf,
    geometry_path: PathBuf,
    model_bundle_path: PathBuf,
    container_runtime: PathBuf,
    container_name: String,
    container_image: String,
    expected_representation_version: String,
    expected_geometry_version: String,
    seeds: Vec<SeedConfig>,
}

impl FullScalePreflightConfig {
    fn validate(&self) -> Result<(), String> {
        if self.schema_version != CONFIG_SCHEMA_VERSION {
            return Err(format!(
                "config schema {} does not match {CONFIG_SCHEMA_VERSION}",
                self.schema_version
            ));
        }
        for (name, path) in [
            ("workspace_path", &self.workspace_path),
            ("report_path", &self.report_path),
            ("source_corpus_data_path", &self.source_corpus_data_path),
            (
                "source_ordered_event_ids_path",
                &self.source_ordered_event_ids_path,
            ),
            (
                "source_representation_path",
                &self.source_representation_path,
            ),
            ("geometry_path", &self.geometry_path),
            ("model_bundle_path", &self.model_bundle_path),
            ("container_runtime", &self.container_runtime),
        ] {
            if !path.is_absolute() {
                return Err(format!("{name} must be absolute: `{}`", path.display()));
            }
        }
        if self.container_name.is_empty()
            || !self
                .container_name
                .bytes()
                .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'.' | b'_' | b'-'))
        {
            return Err("container_name is invalid".to_owned());
        }
        require_sha256(
            &self.expected_representation_version,
            "expected_representation_version",
        )?;
        require_sha256(&self.expected_geometry_version, "expected_geometry_version")?;
        if self.seeds.len() != 5 {
            return Err("preflight requires exactly five seeds".to_owned());
        }
        let mut parsed = self
            .seeds
            .iter()
            .map(|seed| parse_event_id(&seed.event_id))
            .collect::<Result<Vec<_>, _>>()?;
        parsed.sort_unstable();
        parsed.dedup();
        if parsed.len() != 5
            || self
                .seeds
                .iter()
                .any(|seed| !(5..=7).contains(&seed.rating))
        {
            return Err("preflight seeds must be five distinct positive notes".to_owned());
        }
        Ok(())
    }
}

struct ResolvedOutputs {
    workspace_path: PathBuf,
    report_path: PathBuf,
}

fn resolve_preflight_outputs(config: &FullScalePreflightConfig) -> Result<ResolvedOutputs, String> {
    let roots = immutable_input_roots(config)?;
    let workspace_path = resolve_absent_output_against_roots(&roots, &config.workspace_path)?;
    let report_path = resolve_absent_output_against_roots(&roots, &config.report_path)?;
    if workspace_path == report_path {
        return Err("workspace_path and report_path resolve to the same output".to_owned());
    }
    Ok(ResolvedOutputs {
        workspace_path,
        report_path,
    })
}

fn resolve_absent_output_against_roots(
    immutable_roots: &[PathBuf],
    output: &Path,
) -> Result<PathBuf, String> {
    let mut resolved = None;
    for root in immutable_roots {
        let candidate =
            resolve_output_outside_tree(root, output).map_err(|error| error.to_string())?;
        if let Some(previous) = &resolved
            && previous != &candidate
        {
            return Err(format!(
                "output `{}` resolved inconsistently across immutable inputs",
                output.display()
            ));
        }
        resolved = Some(candidate);
    }
    resolved.ok_or_else(|| "preflight has no immutable input roots".to_owned())
}

fn require_existing_output_outside_inputs(
    config: &FullScalePreflightConfig,
    output: &Path,
) -> Result<PathBuf, String> {
    let resolved = fs::canonicalize(output)
        .map_err(|error| format!("could not resolve `{}`: {error}", output.display()))?;
    for root in immutable_input_roots(config)? {
        if resolved.starts_with(&root) {
            return Err(format!(
                "output `{}` is inside immutable input `{}`",
                resolved.display(),
                root.display()
            ));
        }
    }
    Ok(resolved)
}

fn immutable_input_roots(config: &FullScalePreflightConfig) -> Result<Vec<PathBuf>, String> {
    let corpus_parent = config
        .source_corpus_data_path
        .parent()
        .ok_or_else(|| "source_corpus_data_path has no parent".to_owned())?;
    let ordered_parent = config
        .source_ordered_event_ids_path
        .parent()
        .ok_or_else(|| "source_ordered_event_ids_path has no parent".to_owned())?;
    [
        config.source_representation_path.as_path(),
        config.geometry_path.as_path(),
        config.model_bundle_path.as_path(),
        corpus_parent,
        ordered_parent,
    ]
    .into_iter()
    .map(|path| {
        fs::canonicalize(path).map_err(|error| {
            format!(
                "could not resolve immutable input `{}`: {error}",
                path.display()
            )
        })
    })
    .collect()
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct SeedConfig {
    event_id: String,
    rating: u8,
}

#[derive(Debug, Deserialize, Serialize)]
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
    fn from_verified_inputs(
        config: &FullScalePreflightConfig,
        geometry: &RepresentationGeometryArtifact,
        corpus_path: PathBuf,
        session_path: PathBuf,
    ) -> Result<Self, String> {
        let values = &geometry.manifest().values;
        Ok(Self {
            schema_version: BINDING_SCHEMA_VERSION,
            corpus_path,
            corpus_identity: format!(
                "sha256:{}",
                geometry.manifest().representation.corpus_data_sha256
            ),
            session_path,
            representation_version: geometry
                .manifest()
                .representation
                .representation_version
                .clone(),
            geometry_version: geometry.geometry_version().to_owned(),
            b16_bits: values.b16.bits.clone(),
            h16_bits: values.h16.bits.clone(),
            h64_bits: values.h64.bits.clone(),
            h256_bits: values.h256.bits.clone(),
            s16_bits: values.s16.bits.clone(),
            s64_bits: values.s64.bits.clone(),
            s256_bits: values.s256.bits.clone(),
            seeds: config.seeds.clone(),
        })
    }

    fn runner_config(&self) -> Result<AdaptiveLearningRunnerConfig, String> {
        if self.schema_version != BINDING_SCHEMA_VERSION {
            return Err("runner binding has the wrong schema".to_owned());
        }
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
            corpus_path: self.corpus_path.clone(),
            corpus_identity: self.corpus_identity.clone(),
            session_path: self.session_path.clone(),
            compact_settings,
            rbf_settings,
            b16,
            seeds,
        })
    }
}

#[derive(Debug, Serialize)]
struct FullScalePreflightReport {
    schema_version: u32,
    purpose: String,
    quality_claim: bool,
    spend_micro_usd: u64,
    executable_path: PathBuf,
    executable_sha256: String,
    config_path: PathBuf,
    config_sha256: String,
    representation_version: String,
    geometry_version: String,
    represented_rows: u64,
    dimensions: u32,
    source_representation_path: PathBuf,
    source_representation_metadata_before: String,
    source_representation_metadata_after: String,
    source_representation_unchanged: bool,
    disposable_corpus_path: PathBuf,
    disposable_ordered_event_ids_path: PathBuf,
    disposable_representation_path: PathBuf,
    representation_view: RepresentationViewObservation,
    binding_path: PathBuf,
    binding_sha256: String,
    staging_elapsed_ns: u64,
    verification_elapsed_ns: u64,
    geometry_open_elapsed_ns: u64,
    matrix_scan_cache_condition: String,
    cold_start_timing_valid: bool,
    worker: WorkerObservation,
    oracle_open_elapsed_ns: u64,
    controller_peak_rss_bytes: u64,
    first_round: FirstRoundCostObservation,
    session_metrics: SessionMetrics,
    replay_cache_condition: String,
    replay_process_elapsed_ns: u64,
    replay: ReplayProcessObservation,
    replay_artifacts: ReplayArtifactComparison,
    session_path: PathBuf,
    session_bytes: u64,
    session_sha256: String,
    cache_path: PathBuf,
    cache_usage: PathUsage,
    workspace_usage: PathUsage,
    configured_per_personalizer_order_quota: usize,
    configured_learning_primary_quota: usize,
    total_elapsed_ns: u64,
    scope_limit: String,
    next_measurement: String,
}

#[derive(Debug, Serialize)]
struct WorkerObservation {
    container_image: String,
    local_image_id: String,
    container_name: String,
    query_device: String,
    startup_elapsed_ns: u64,
    peak_rss_bytes: u64,
    removed_after_shutdown: bool,
}

#[derive(Debug, Deserialize, Serialize)]
struct ReplayProcessObservation {
    schema_version: u32,
    observation: FirstRoundReplayObservation,
    peak_rss_bytes: u64,
}

#[derive(Debug, Serialize)]
struct ReplayArtifactComparison {
    before: ReplayArtifactState,
    after: ReplayArtifactState,
    cache_unchanged: bool,
}

#[derive(Debug, Serialize)]
struct ReplayArtifactState {
    session_bytes: u64,
    session_sha256: String,
    cache_usage: PathUsage,
    cache_content_sha256: String,
}

impl ReplayArtifactState {
    fn capture(session_path: &Path, cache_path: &Path) -> Result<Self, String> {
        Ok(Self {
            session_bytes: fs::metadata(session_path)
                .map_err(|error| format!("could not stat `{}`: {error}", session_path.display()))?
                .len(),
            session_sha256: hash_file(session_path)?,
            cache_usage: path_usage(cache_path)?,
            cache_content_sha256: immutable_content_tree_identity(cache_path)
                .map_err(|error| error.to_string())?,
        })
    }
}

#[derive(Debug, Serialize)]
struct SessionMetrics {
    oracle_wave_calls: usize,
    logical_similar_note_requests: usize,
    candidate_depth: usize,
    source_loading_ns: u64,
    query_encoding_ns: u64,
    matrix_scan_ns: u64,
    result_merge_ns: u64,
    encoded_queries: u64,
    cache_hits: u64,
    matrix_passes: u64,
    scanned_rows: u64,
    cached_similar_note_responses: usize,
    cached_vector_batches: usize,
    seed_vector_count: usize,
    candidate_vector_count: usize,
}

#[derive(Debug, Deserialize)]
struct SessionExcerpt {
    oracle_calls: Vec<OracleCallExcerpt>,
    oracle_responses: Vec<CachedResponseExcerpt>,
    vector_responses: Vec<VectorResponseExcerpt>,
}

#[derive(Debug, Deserialize)]
struct OracleCallExcerpt {
    requests: Vec<SimilarNotesRequest>,
    metrics: SimilarNotesWaveMetrics,
}

#[derive(Debug, Deserialize)]
struct CachedResponseExcerpt {
    key: ResponseKeyExcerpt,
}

#[derive(Debug, Deserialize)]
struct ResponseKeyExcerpt {
    source_event_id: EventId,
    candidate_depth: usize,
}

#[derive(Debug, Deserialize)]
struct VectorResponseExcerpt {
    key: VectorResponseKeyExcerpt,
}

#[derive(Debug, Deserialize)]
struct VectorResponseKeyExcerpt {
    note_ids: Vec<EventId>,
}

#[derive(Debug, Serialize)]
struct PathUsage {
    apparent_bytes: u64,
    allocated_bytes: u64,
    regular_files: u64,
    directories: u64,
    symbolic_links: u64,
}

fn worker_config(
    config: &FullScalePreflightConfig,
    manifest: &RepresentationManifest,
) -> Result<GteWorkerConfig, String> {
    let bundle = fs::canonicalize(&config.model_bundle_path).map_err(|error| {
        format!(
            "could not resolve model bundle `{}`: {error}",
            config.model_bundle_path.display()
        )
    })?;
    let model_lock = bundle.join("model-lock.json");
    if hash_file(&model_lock)? != manifest.descriptor.model_lock_sha256 {
        return Err("local model bundle does not match the representation".to_owned());
    }
    let mount = format!("{}:/bundle:ro", bundle.display());
    Ok(GteWorkerConfig {
        program: config.container_runtime.clone(),
        prefix_arguments: gte_container_prefix_arguments(
            &config.container_name,
            &mount,
            &config.container_image,
        ),
        worker_path: Some("/opt/oracle-mvp/gte/worker.py".into()),
        model_dir: "/bundle/model".into(),
        model_lock_path: "/bundle/model-lock.json".into(),
        dependency_lock_path: "/tmp/gte-locks/requirements.lock".into(),
        device: "cpu".to_owned(),
        model_lock_sha256: manifest.descriptor.model_lock_sha256.clone(),
        worker_sha256: manifest.descriptor.worker_sha256.clone(),
        dependency_lock_sha256: manifest.descriptor.dependency_lock_sha256.clone(),
        container_image: manifest.descriptor.container_image.clone(),
        torch_version: manifest.descriptor.torch_version.clone(),
        transformers_version: manifest.descriptor.transformers_version.clone(),
        cuda_version: manifest.descriptor.cuda_version.clone(),
    })
}

fn read_session_metrics(
    path: &Path,
    expected_seeds: &[EventId],
    total_rows: u64,
) -> Result<SessionMetrics, String> {
    let session: SessionExcerpt = read_json(path)?;
    if session.oracle_calls.is_empty() {
        return Err("first-round session contains no Oracle calls".to_owned());
    }
    let mut expected_sources = expected_seeds.to_vec();
    expected_sources.sort_unstable();
    for (ordinal, call) in session.oracle_calls.iter().enumerate() {
        let actual_sources = call
            .requests
            .iter()
            .map(|request| request.note_id)
            .collect::<Vec<_>>();
        if actual_sources != expected_sources
            || call
                .requests
                .iter()
                .any(|request| request.candidate_depth != CANDIDATE_DEPTH)
            || call.metrics.scan_block_rows != FP32_SCAN_BLOCK_ROWS as u64
        {
            return Err("a first-round Oracle call did not contain the five configured depth-1024 seed queries".to_owned());
        }
        let metrics = &call.metrics;
        let valid = if ordinal == 0 {
            metrics.encoded_queries == expected_seeds.len() as u64
                && metrics.cache_hits == 0
                && metrics.matrix_passes == 1
                && metrics.scanned_rows == total_rows
        } else {
            metrics.source_loading_ns == 0
                && metrics.query_encoding_ns == 0
                && metrics.matrix_scan_ns == 0
                && metrics.result_merge_ns == 0
                && metrics.encoded_queries == 0
                && metrics.cache_hits == expected_seeds.len() as u64
                && metrics.matrix_passes == 0
                && metrics.scanned_rows == 0
        };
        if !valid {
            return Err("first-round Oracle calls do not describe one full-matrix pass followed only by in-memory cache reuse".to_owned());
        }
    }
    let mut cached_sources = session
        .oracle_responses
        .iter()
        .map(|response| response.key.source_event_id)
        .collect::<Vec<_>>();
    cached_sources.sort_unstable();
    if cached_sources != expected_sources
        || session
            .oracle_responses
            .iter()
            .any(|response| response.key.candidate_depth != CANDIDATE_DEPTH)
    {
        return Err(
            "durable cache does not contain exactly the five configured depth-1024 responses"
                .to_owned(),
        );
    }
    if session.vector_responses.len() != 2 {
        return Err(format!(
            "expected one seed and one candidate vector batch, found {}",
            session.vector_responses.len()
        ));
    }
    let seed_batches = session
        .vector_responses
        .iter()
        .filter(|response| response.key.note_ids.as_slice() == expected_seeds)
        .count();
    if seed_batches != 1 {
        return Err(
            "durable cache does not contain exactly one configured seed-vector batch".to_owned(),
        );
    }
    let candidate_vector_count = session
        .vector_responses
        .iter()
        .find(|response| response.key.note_ids.as_slice() != expected_seeds)
        .map(|response| response.key.note_ids.len())
        .unwrap_or(0);
    if candidate_vector_count <= CandidateOrderPhase::Learning.primary_count() {
        return Err(
            "durable candidate-vector batch is too small to build the first learning wave"
                .to_owned(),
        );
    }
    let summed = |field: fn(&SimilarNotesWaveMetrics) -> u64| {
        session
            .oracle_calls
            .iter()
            .map(|call| field(&call.metrics))
            .fold(0_u64, u64::saturating_add)
    };
    Ok(SessionMetrics {
        oracle_wave_calls: session.oracle_calls.len(),
        logical_similar_note_requests: session
            .oracle_calls
            .iter()
            .map(|call| call.requests.len())
            .sum(),
        candidate_depth: CANDIDATE_DEPTH,
        source_loading_ns: summed(|metrics| metrics.source_loading_ns),
        query_encoding_ns: summed(|metrics| metrics.query_encoding_ns),
        matrix_scan_ns: summed(|metrics| metrics.matrix_scan_ns),
        result_merge_ns: summed(|metrics| metrics.result_merge_ns),
        encoded_queries: summed(|metrics| metrics.encoded_queries),
        cache_hits: summed(|metrics| metrics.cache_hits),
        matrix_passes: summed(|metrics| metrics.matrix_passes),
        scanned_rows: summed(|metrics| metrics.scanned_rows),
        cached_similar_note_responses: session.oracle_responses.len(),
        cached_vector_batches: session.vector_responses.len(),
        seed_vector_count: expected_seeds.len(),
        candidate_vector_count,
    })
}

fn path_usage(path: &Path) -> Result<PathUsage, String> {
    let mut usage = PathUsage {
        apparent_bytes: 0,
        allocated_bytes: 0,
        regular_files: 0,
        directories: 0,
        symbolic_links: 0,
    };
    accumulate_path_usage(path, &mut usage)?;
    Ok(usage)
}

fn accumulate_path_usage(path: &Path, usage: &mut PathUsage) -> Result<(), String> {
    let metadata = fs::symlink_metadata(path)
        .map_err(|error| format!("could not stat `{}`: {error}", path.display()))?;
    usage.apparent_bytes = usage.apparent_bytes.saturating_add(metadata.len());
    usage.allocated_bytes = usage
        .allocated_bytes
        .saturating_add(metadata.blocks().saturating_mul(512));
    if metadata.file_type().is_symlink() {
        usage.symbolic_links += 1;
    } else if metadata.is_file() {
        usage.regular_files += 1;
    } else if metadata.is_dir() {
        usage.directories += 1;
        for entry in fs::read_dir(path)
            .map_err(|error| format!("could not read `{}`: {error}", path.display()))?
        {
            let entry =
                entry.map_err(|error| format!("could not read `{}`: {error}", path.display()))?;
            accumulate_path_usage(&entry.path(), usage)?;
        }
    }
    Ok(())
}

fn copy_and_require_sha256(
    source: &Path,
    destination: &Path,
    expected: &str,
) -> Result<(), String> {
    fs::copy(source, destination).map_err(|error| {
        format!(
            "could not copy `{}` to `{}`: {error}",
            source.display(),
            destination.display()
        )
    })?;
    File::open(destination)
        .and_then(|file| file.sync_all())
        .map_err(|error| format!("could not sync `{}`: {error}", destination.display()))?;
    let actual = hash_file(destination)?;
    if actual != expected {
        return Err(format!(
            "copied file `{}` has SHA-256 {actual}, expected {expected}",
            destination.display()
        ));
    }
    let source_metadata = fs::metadata(source)
        .map_err(|error| format!("could not stat `{}`: {error}", source.display()))?;
    let destination_metadata = fs::metadata(destination)
        .map_err(|error| format!("could not stat `{}`: {error}", destination.display()))?;
    if source_metadata.dev() == destination_metadata.dev()
        && source_metadata.ino() == destination_metadata.ino()
    {
        return Err(format!(
            "disposable copy `{}` aliases its immutable source inode",
            destination.display()
        ));
    }
    Ok(())
}

fn docker_image_id(runtime: &Path, image: &str) -> Result<String, String> {
    let output = Command::new(runtime)
        .args(["image", "inspect", image, "--format", "{{.Id}}"])
        .output()
        .map_err(|error| format!("could not inspect the pinned container image: {error}"))?;
    if !output.status.success() {
        return Err(format!(
            "pinned container image is unavailable locally: {}",
            String::from_utf8_lossy(&output.stderr).trim()
        ));
    }
    let id = String::from_utf8(output.stdout)
        .map_err(|_| "container image ID is not UTF-8".to_owned())?;
    let id = id.trim().to_owned();
    if !id.starts_with("sha256:") {
        return Err("container runtime returned an invalid image ID".to_owned());
    }
    Ok(id)
}

fn require_container_name_available(runtime: &Path, name: &str) -> Result<(), String> {
    let output = Command::new(runtime)
        .args(["container", "inspect", name])
        .output()
        .map_err(|error| format!("could not check query-worker container name: {error}"))?;
    if output.status.success() {
        return Err(format!(
            "query-worker container name `{name}` is already in use"
        ));
    }
    let stderr = String::from_utf8_lossy(&output.stderr);
    if stderr.contains("No such container") || stderr.contains("No such object") {
        Ok(())
    } else {
        Err(format!(
            "could not establish whether query-worker container name `{name}` is available: {}",
            stderr.trim()
        ))
    }
}

fn docker_container_pid(runtime: &Path, name: &str) -> Result<u32, String> {
    let output = Command::new(runtime)
        .args(["inspect", "--format", "{{.State.Pid}}", name])
        .output()
        .map_err(|error| format!("could not inspect query worker: {error}"))?;
    if !output.status.success() {
        return Err(format!(
            "could not inspect query worker: {}",
            String::from_utf8_lossy(&output.stderr).trim()
        ));
    }
    String::from_utf8(output.stdout)
        .ok()
        .and_then(|value| value.trim().parse::<u32>().ok())
        .filter(|pid| *pid > 0)
        .ok_or_else(|| "query worker container reported an invalid PID".to_owned())
}

fn wait_for_container_removal(
    runtime: &Path,
    name: &str,
    timeout: Duration,
) -> Result<bool, String> {
    let deadline = Instant::now() + timeout;
    loop {
        let output = Command::new(runtime)
            .args(["inspect", name])
            .output()
            .map_err(|error| format!("could not inspect query worker shutdown: {error}"))?;
        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            if stderr.contains("No such container") || stderr.contains("No such object") {
                return Ok(true);
            }
            return Err(format!(
                "could not inspect query worker shutdown: {}",
                stderr.trim()
            ));
        }
        if Instant::now() >= deadline {
            return Ok(false);
        }
        thread::sleep(Duration::from_millis(100));
    }
}

fn process_peak_rss_bytes(pid: u32) -> Result<u64, String> {
    let path = PathBuf::from(format!("/proc/{pid}/status"));
    let status = fs::read_to_string(&path)
        .map_err(|error| format!("could not read `{}`: {error}", path.display()))?;
    let kib = status
        .lines()
        .find_map(|line| line.strip_prefix("VmHWM:"))
        .and_then(|value| value.split_whitespace().next())
        .and_then(|value| value.parse::<u64>().ok())
        .ok_or_else(|| format!("`{}` has no VmHWM", path.display()))?;
    kib.checked_mul(1024)
        .ok_or_else(|| "peak RSS overflowed bytes".to_owned())
}

fn oracle_cache_path(session_path: &Path) -> Result<PathBuf, String> {
    let name = session_path
        .file_name()
        .and_then(|name| name.to_str())
        .ok_or_else(|| "session path has no UTF-8 file name".to_owned())?;
    Ok(session_path
        .parent()
        .unwrap_or_else(|| Path::new("."))
        .join(format!(".{name}.oracle-responses")))
}

fn parse_event_id(value: &str) -> Result<EventId, String> {
    if value.len() != 64 {
        return Err("event ID must contain 64 hexadecimal characters".to_owned());
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

fn require_sha256(value: &str, name: &str) -> Result<(), String> {
    if value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        Ok(())
    } else {
        Err(format!("{name} must be a lowercase SHA-256"))
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
    "usage: phase3-cost-preflight CONFIG.json".to_owned()
}
