//! Production command boundary for the GTE/FP32 Oracle path.

use std::env;
use std::ffi::OsString;
use std::fs::{self, File};
use std::io::{self, BufReader, Read, Write};
use std::path::{Path, PathBuf};
use std::process::ExitCode;
use std::time::{Duration, Instant};

use oracle_mvp::budget::MicroUsd;
use oracle_mvp::fp32_oracle::{Fp32OfflineOracle, SimilarNotesRequest, vectors_for_notes};
use oracle_mvp::gte::{GteProcessEncoder, GteWorkerConfig};
use oracle_mvp::gte_budget::{
    CalibrationEvidencePaths, CalibrationRecorder, CalibrationRecorderConfig,
    read_calibration_execution_identity, reserve_calibration, validate_calibration_selection,
};
use oracle_mvp::ordered_gte_token_audit::{OrderedGteTokenAuditConfig, audit_ordered_gte_tokens};
use oracle_mvp::representation::{
    RepresentationBuildConfig, RepresentationEncoder, build_representation_shards,
    build_representation_shards_observed, prepare_representation_index, verify_representation,
};
use oracle_mvp::representation_batch_plan::{
    RepresentationBatchPlanConfig, create_representation_batch_plan,
};
use oracle_mvp::semantic_order::derive_semantic_order;
use serde::Deserialize;
use serde_json::json;
use sha2::{Digest, Sha256};

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("error: {error}");
            ExitCode::FAILURE
        }
    }
}

fn run() -> Result<(), String> {
    let mut arguments = env::args_os().skip(1);
    let operation = arguments.next().ok_or_else(usage)?;
    let config_path = arguments.next().ok_or_else(usage)?;
    let config: RunConfig = read_json(Path::new(&config_path))?;
    let operation = operation
        .to_str()
        .ok_or_else(|| "operation is not UTF-8".to_owned())?;
    if config.worker.device == "cuda"
        && operation != "calibrate-shards"
        && operation != "validate-calibration-selection"
    {
        return Err(
            "gte-oracle refuses unadmitted CUDA work; the paid calibration requires a separate ledger-bound execution command"
                .to_owned(),
        );
    }
    match operation {
        "model-smoke" => {
            require_no_more(arguments)?;
            let mut encoder = config.start_worker()?;
            let texts = [
                "A detailed Rust memory-safety and compiler performance investigation.",
                "Open-source Linux kernel development and reproducible benchmarking.",
            ];
            let first_documents = encoder
                .encode_documents(&texts)
                .map_err(|error| error.to_string())?;
            let second_documents = encoder
                .encode_documents(&texts)
                .map_err(|error| error.to_string())?;
            let first_queries = encoder
                .encode_queries(&texts)
                .map_err(|error| error.to_string())?;
            let second_queries = encoder
                .encode_queries(&texts)
                .map_err(|error| error.to_string())?;
            if first_documents != second_documents
                || first_queries != second_queries
                || first_documents == first_queries
            {
                return Err(
                    "repeated GTE outputs are not deterministic or query/document roles collapsed"
                        .to_owned(),
                );
            }
            print_json(&json!({
                "status": "pass",
                "document_vectors_sha256": hash_f32(&first_documents),
                "query_vectors_sha256": hash_f32(&first_queries),
                "descriptor": encoder.descriptor(),
            }))
        }
        "audit-tokens" => {
            require_no_more(arguments)?;
            let mut counter = config.start_worker()?;
            let result = audit_ordered_gte_tokens(
                &config.corpus_path,
                &config.ordered_event_ids_path,
                &config.token_audit_path,
                &OrderedGteTokenAuditConfig {
                    batch_size: config.batch_size,
                    shard_rows: config.shard_rows,
                },
                &mut counter,
            )
            .map_err(|error| error.to_string())?;
            print_json(&json!({
                "audited_rows": result.audited_rows,
                "reused_rows": result.reused_rows,
                "manifest": result.manifest,
            }))
        }
        "prepare-semantic-order" => {
            require_no_more(arguments)?;
            let source_order = config
                .source_ordered_event_ids_path
                .as_ref()
                .ok_or_else(|| {
                    "prepare-semantic-order requires source_ordered_event_ids_path".to_owned()
                })?;
            let semantic_root = config
                .semantic_order_path
                .as_ref()
                .ok_or_else(|| "prepare-semantic-order requires semantic_order_path".to_owned())?;
            let expected_order = semantic_root.join("ordered-event-ids.bin");
            if config.ordered_event_ids_path != expected_order {
                return Err(format!(
                    "ordered_event_ids_path must be `{}` for this semantic order",
                    expected_order.display()
                ));
            }
            let manifest = derive_semantic_order(&config.corpus_path, source_order, semantic_root)
                .map_err(|error| error.to_string())?;
            print_json(&json!({
                "manifest": manifest,
            }))
        }
        "plan-batches" => {
            require_no_more(arguments)?;
            let plan = create_representation_batch_plan(
                &config.ordered_event_ids_path,
                &config.token_audit_path,
                &config.batch_plan_path,
                &RepresentationBatchPlanConfig {
                    shard_rows: config.shard_rows,
                    batch_rows: config.batch_size,
                },
            )
            .map_err(|error| error.to_string())?;
            print_json(&json!({
                "identity": plan.identity(),
                "manifest": plan.manifest(),
            }))
        }
        "prepare-representation" => {
            require_no_more(arguments)?;
            let manifest = prepare_representation_index(
                &config.corpus_path,
                &config.ordered_event_ids_path,
                &config.representation_path,
            )
            .map_err(|error| error.to_string())?;
            print_json(&json!({
                "index": manifest,
            }))
        }
        "validate-calibration-selection" => {
            let ordinals = parse_ordinals(&arguments.next().ok_or_else(usage)?)?;
            let token_range_upper_bounds = parse_u32_list(
                &arguments.next().ok_or_else(usage)?,
                "TOKEN_RANGE_UPPER_BOUNDS",
                false,
            )?;
            require_no_more(arguments)?;
            validate_calibration_selection(
                &config.ordered_event_ids_path,
                &config.token_audit_path,
                &config.batch_plan_path,
                &ordinals,
                &token_range_upper_bounds,
            )
            .map_err(|error| error.to_string())?;
            print_json(&json!({
                "status": "pass",
                "shard_ordinals": ordinals,
                "token_range_upper_bounds": token_range_upper_bounds,
            }))
        }
        "embed-shards" => {
            let ordinals = arguments.next().ok_or_else(usage)?;
            require_no_more(arguments)?;
            let ordinals = parse_ordinals(&ordinals)?;
            let mut encoder = config.start_worker()?;
            let result = build_representation_shards(
                &config.corpus_path,
                &config.ordered_event_ids_path,
                &config.representation_path,
                &RepresentationBuildConfig {
                    token_audit_path: config.token_audit_path.clone(),
                    batch_plan_path: config.batch_plan_path.clone(),
                    shard_ordinals: ordinals,
                },
                &mut encoder,
            )
            .map_err(|error| error.to_string())?;
            print_json(&json!({
                "encoded_rows": result.encoded_rows,
                "reused_rows": result.reused_rows,
                "representation_version": result.representation_version,
                "manifest": result.manifest,
            }))
        }
        "calibrate-shards" => {
            let ordinals = arguments.next().ok_or_else(usage)?;
            require_no_more(arguments)?;
            let ordinals = parse_ordinals(&ordinals)?;
            let calibration = config.calibration.as_ref().ok_or_else(|| {
                "calibrate-shards requires calibration settings in the run config".to_owned()
            })?;
            if config.worker.device != "cuda" {
                return Err("calibrate-shards requires the approved CUDA worker".to_owned());
            }
            calibration.validate(&config)?;
            validate_calibration_selection(
                &config.ordered_event_ids_path,
                &config.token_audit_path,
                &config.batch_plan_path,
                &ordinals,
                &calibration.token_range_upper_bounds,
            )
            .map_err(|error| error.to_string())?;
            let execution_identity =
                read_calibration_execution_identity(&calibration.execution_identity_path)
                    .map_err(|error| error.to_string())?;
            let rental_started_at = Instant::now();
            let admission = reserve_calibration(
                &calibration.ledger_path,
                &calibration.reservation_id,
                MicroUsd(calibration.maximum_charge_micro_usd),
                &calibration.recorded_at_utc,
            )
            .map_err(|error| error.to_string())?;
            let mut recorder = CalibrationRecorder::new(CalibrationRecorderConfig {
                rental_started_at,
                rental_rate_per_hour: execution_identity.rental_rate_per_hour,
                maximum_charge: admission.maximum_new_charge,
                maximum_work_unit: Duration::from_secs(calibration.maximum_work_unit_seconds),
                reservation: admission.evidence_binding(),
            })
            .map_err(|error| error.to_string())?;
            recorder
                .check_startup()
                .map_err(|error| error.to_string())?;
            let mut encoder = config.start_worker()?;
            encoder
                .encode_documents(&[
                    "A detailed Rust memory-safety and compiler performance investigation.",
                ])
                .map_err(|error| error.to_string())?;
            let result = build_representation_shards_observed(
                &config.corpus_path,
                &config.ordered_event_ids_path,
                &config.representation_path,
                &RepresentationBuildConfig {
                    token_audit_path: config.token_audit_path.clone(),
                    batch_plan_path: config.batch_plan_path.clone(),
                    shard_ordinals: ordinals,
                },
                &mut encoder,
                &mut recorder,
            )
            .map_err(|error| error.to_string())?;
            let evidence = recorder
                .publish(
                    &calibration.evidence_path,
                    &CalibrationEvidencePaths {
                        ordered_event_ids_path: config.ordered_event_ids_path.clone(),
                        token_audit_path: config.token_audit_path.clone(),
                        batch_plan_path: config.batch_plan_path.clone(),
                        representation_path: config.representation_path.clone(),
                        execution_identity_path: calibration.execution_identity_path.clone(),
                    },
                    calibration.token_range_upper_bounds.clone(),
                )
                .map_err(|error| error.to_string())?;
            print_json(&json!({
                "calibration_evidence_sha256": evidence.evidence_sha256(),
                "encoded_rows": result.encoded_rows,
                "representation_version": result.representation_version,
                "reservation_ledger_sha256": admission.ledger_sha256,
            }))
        }
        "verify-representation" => {
            require_no_more(arguments)?;
            let opened = verify_representation(
                &config.corpus_path,
                &config.ordered_event_ids_path,
                &config.representation_path,
            )
            .map_err(|error| error.to_string())?;
            print_json(&json!({
                "representation_version": opened.representation_version(),
                "manifest": opened.manifest(),
            }))
        }
        "similar-notes" => {
            let note_ids = parse_event_ids(&arguments.next().ok_or_else(usage)?)?;
            let depth = parse_positive_usize(&arguments.next().ok_or_else(usage)?, "DEPTH")?;
            let version = arguments.next().ok_or_else(usage)?;
            require_no_more(arguments)?;
            let encoder = config.start_worker()?;
            let mut oracle = Fp32OfflineOracle::open(
                &config.corpus_path,
                &config.ordered_event_ids_path,
                &config.representation_path,
                encoder,
            )
            .map_err(|error| error.to_string())?;
            let requests = note_ids
                .into_iter()
                .map(|note_id| SimilarNotesRequest {
                    note_id,
                    candidate_depth: depth,
                })
                .collect::<Vec<_>>();
            let wave = oracle
                .similar_notes_wave(
                    &requests,
                    version
                        .to_str()
                        .ok_or_else(|| "representation version is not UTF-8".to_owned())?,
                )
                .map_err(|error| error.to_string())?;
            let responses = wave
                .responses
                .into_iter()
                .zip(requests)
                .map(|(response, request)| {
                    let candidates = response
                        .candidates
                        .into_iter()
                        .map(|candidate| {
                            json!({
                                "event_id": encode_event_id(candidate.event_id),
                                "rank": candidate.rank,
                                "cosine_score": candidate.cosine_score,
                            })
                        })
                        .collect::<Vec<_>>();
                    json!({
                        "source_event_id": encode_event_id(request.note_id),
                        "representation_version": response.representation_version,
                        "represented_rows": response.represented_rows,
                        "total_rows": response.total_rows,
                        "complete": response.complete,
                        "candidates": candidates,
                    })
                })
                .collect::<Vec<_>>();
            print_json(&json!({
                "metrics": wave.metrics,
                "responses": responses,
            }))
        }
        "vectors-for-notes" => {
            let ids = parse_event_ids(&arguments.next().ok_or_else(usage)?)?;
            let version = arguments.next().ok_or_else(usage)?;
            require_no_more(arguments)?;
            let response = vectors_for_notes(
                &config.ordered_event_ids_path,
                &config.representation_path,
                &ids,
                version
                    .to_str()
                    .ok_or_else(|| "representation version is not UTF-8".to_owned())?,
            )
            .map_err(|error| error.to_string())?;
            let vectors = response
                .vectors
                .into_iter()
                .map(|vector| {
                    json!({
                        "event_id": encode_event_id(vector.event_id),
                        "vector_sha256": hash_f32(&vector.vector),
                        "dimensions": vector.vector.len(),
                        "vector": vector.vector,
                    })
                })
                .collect::<Vec<_>>();
            print_json(&json!({
                "representation_version": response.representation_version,
                "represented_rows": response.represented_rows,
                "total_rows": response.total_rows,
                "complete": response.complete,
                "lookup_elapsed_ns": response.lookup_elapsed_ns,
                "vectors": vectors,
            }))
        }
        _ => Err(usage()),
    }
}

#[derive(Debug, Deserialize)]
struct RunConfig {
    corpus_path: PathBuf,
    ordered_event_ids_path: PathBuf,
    source_ordered_event_ids_path: Option<PathBuf>,
    semantic_order_path: Option<PathBuf>,
    token_audit_path: PathBuf,
    batch_plan_path: PathBuf,
    representation_path: PathBuf,
    model_lock_path: PathBuf,
    worker_source_path: PathBuf,
    dependency_lock_path: PathBuf,
    container_image: String,
    torch_version: String,
    transformers_version: String,
    cuda_version: String,
    worker: WorkerLaunch,
    batch_size: usize,
    shard_rows: u64,
    calibration: Option<CalibrationRunSettings>,
}

#[derive(Debug, Deserialize)]
struct CalibrationRunSettings {
    ledger_path: PathBuf,
    reservation_id: String,
    maximum_charge_micro_usd: u64,
    recorded_at_utc: String,
    execution_identity_path: PathBuf,
    evidence_path: PathBuf,
    token_range_upper_bounds: Vec<u32>,
    maximum_work_unit_seconds: u64,
}

impl CalibrationRunSettings {
    fn validate(&self, config: &RunConfig) -> Result<(), String> {
        if self.maximum_charge_micro_usd == 0
            || self.maximum_work_unit_seconds == 0
            || self.token_range_upper_bounds.is_empty()
            || self.token_range_upper_bounds.contains(&0)
            || self
                .token_range_upper_bounds
                .windows(2)
                .any(|pair| pair[0] >= pair[1])
        {
            return Err("calibration settings contain an invalid cap or token range".to_owned());
        }
        for path in [
            self.ledger_path.as_path(),
            self.execution_identity_path.as_path(),
            config.corpus_path.join("data.mdb").as_path(),
            config.ordered_event_ids_path.as_path(),
            config.token_audit_path.join("manifest.json").as_path(),
            config.batch_plan_path.join("manifest.json").as_path(),
            config.model_lock_path.as_path(),
            config.worker_source_path.as_path(),
            config.dependency_lock_path.as_path(),
            config.worker.program.as_path(),
            config.worker.model_lock_path.as_path(),
            config.worker.dependency_lock_path.as_path(),
        ] {
            if !path.is_file() {
                return Err(format!(
                    "calibration input `{}` is not a file",
                    path.display()
                ));
            }
        }
        if !config.worker.model_dir.is_dir() {
            return Err(format!(
                "calibration model directory `{}` does not exist",
                config.worker.model_dir.display()
            ));
        }
        if let Some(worker_path) = &config.worker.worker_path
            && !worker_path.is_file()
        {
            return Err(format!(
                "calibration worker `{}` is not a file",
                worker_path.display()
            ));
        }
        if self.evidence_path.exists() {
            return Err(format!(
                "calibration evidence already exists at `{}`",
                self.evidence_path.display()
            ));
        }
        let manifest_path = config.representation_path.join("manifest.json");
        let shards_path = config.representation_path.join("shards");
        let has_shards = shards_path.is_dir()
            && fs::read_dir(&shards_path)
                .map_err(|error| format!("could not inspect `{}`: {error}", shards_path.display()))?
                .next()
                .transpose()
                .map_err(|error| format!("could not inspect `{}`: {error}", shards_path.display()))?
                .is_some();
        if manifest_path.exists() || has_shards {
            return Err(
                "calibrate-shards requires a fresh representation shard set so every reused calibration shard has measurements"
                    .to_owned(),
            );
        }
        Ok(())
    }
}

#[derive(Debug, Deserialize)]
struct WorkerLaunch {
    program: PathBuf,
    #[serde(default)]
    prefix_arguments: Vec<String>,
    worker_path: Option<PathBuf>,
    model_dir: PathBuf,
    model_lock_path: PathBuf,
    dependency_lock_path: PathBuf,
    device: String,
}

impl RunConfig {
    fn start_worker(&self) -> Result<GteProcessEncoder, String> {
        GteProcessEncoder::start(GteWorkerConfig {
            program: self.worker.program.clone(),
            prefix_arguments: self
                .worker
                .prefix_arguments
                .iter()
                .map(OsString::from)
                .collect(),
            worker_path: self.worker.worker_path.clone(),
            model_dir: self.worker.model_dir.clone(),
            model_lock_path: self.worker.model_lock_path.clone(),
            dependency_lock_path: self.worker.dependency_lock_path.clone(),
            device: self.worker.device.clone(),
            model_lock_sha256: hash_file(&self.model_lock_path)?,
            worker_sha256: hash_file(&self.worker_source_path)?,
            dependency_lock_sha256: hash_file(&self.dependency_lock_path)?,
            container_image: self.container_image.clone(),
            torch_version: self.torch_version.clone(),
            transformers_version: self.transformers_version.clone(),
            cuda_version: self.cuda_version.clone(),
        })
        .map_err(|error| error.to_string())
    }
}

fn read_json<T: for<'de> Deserialize<'de>>(path: &Path) -> Result<T, String> {
    let file = File::open(path)
        .map_err(|error| format!("could not open `{}`: {error}", path.display()))?;
    serde_json::from_reader(BufReader::new(file))
        .map_err(|error| format!("could not decode `{}`: {error}", path.display()))
}

fn hash_file(path: &Path) -> Result<String, String> {
    let mut file = File::open(path)
        .map_err(|error| format!("could not open `{}`: {error}", path.display()))?;
    let mut digest = Sha256::new();
    let mut buffer = [0_u8; 64 * 1024];
    loop {
        let bytes = file
            .read(&mut buffer)
            .map_err(|error| format!("could not read `{}`: {error}", path.display()))?;
        if bytes == 0 {
            break;
        }
        digest.update(&buffer[..bytes]);
    }
    Ok(format!("{:x}", digest.finalize()))
}

fn hash_f32(values: &[f32]) -> String {
    let mut digest = Sha256::new();
    for value in values {
        digest.update(value.to_le_bytes());
    }
    format!("{:x}", digest.finalize())
}

fn parse_ordinals(value: &OsString) -> Result<Vec<u32>, String> {
    parse_u32_list(value, "SHARD_ORDINALS", true)
}

fn parse_u32_list(value: &OsString, name: &str, allow_zero: bool) -> Result<Vec<u32>, String> {
    let value = value
        .to_str()
        .ok_or_else(|| format!("{name} is not UTF-8"))?;
    let values = value
        .split(',')
        .map(|part| {
            part.parse::<u32>()
                .ok()
                .filter(|value| allow_zero || *value > 0)
                .ok_or_else(|| format!("invalid {name} value `{part}`"))
        })
        .collect::<Result<Vec<_>, _>>()?;
    if values.is_empty() {
        return Err(format!("at least one {name} value is required"));
    }
    Ok(values)
}

fn parse_event_ids(value: &OsString) -> Result<Vec<[u8; 32]>, String> {
    value
        .to_str()
        .ok_or_else(|| "EVENT_IDS is not UTF-8".to_owned())?
        .split(',')
        .map(|value| parse_event_id(&OsString::from(value)))
        .collect()
}

fn parse_event_id(value: &OsString) -> Result<[u8; 32], String> {
    let value = value
        .to_str()
        .ok_or_else(|| "event ID is not UTF-8".to_owned())?;
    if value.len() != 64 {
        return Err("event ID must contain 64 hexadecimal characters".to_owned());
    }
    let mut output = [0_u8; 32];
    for (index, chunk) in value.as_bytes().chunks_exact(2).enumerate() {
        output[index] = (decode_hex(chunk[0])? << 4) | decode_hex(chunk[1])?;
    }
    Ok(output)
}

fn decode_hex(value: u8) -> Result<u8, String> {
    match value {
        b'0'..=b'9' => Ok(value - b'0'),
        b'a'..=b'f' => Ok(value - b'a' + 10),
        b'A'..=b'F' => Ok(value - b'A' + 10),
        _ => Err("event ID contains a non-hexadecimal character".to_owned()),
    }
}

fn encode_event_id(value: [u8; 32]) -> String {
    value.iter().map(|byte| format!("{byte:02x}")).collect()
}

fn parse_positive_usize(value: &OsString, name: &str) -> Result<usize, String> {
    value
        .to_str()
        .and_then(|value| value.parse::<usize>().ok())
        .filter(|value| *value > 0)
        .ok_or_else(|| format!("{name} must be a positive integer"))
}

fn require_no_more(mut arguments: impl Iterator<Item = OsString>) -> Result<(), String> {
    if arguments.next().is_some() {
        Err(usage())
    } else {
        Ok(())
    }
}

fn print_json(value: &impl serde::Serialize) -> Result<(), String> {
    let stdout = io::stdout();
    let mut output = stdout.lock();
    serde_json::to_writer_pretty(&mut output, value)
        .map_err(|error| format!("could not encode result: {error}"))?;
    writeln!(output).map_err(|error| format!("could not write result: {error}"))
}

fn usage() -> String {
    "usage: gte-oracle <operation> CONFIG_JSON [arguments]\n\noperations:\n  model-smoke CONFIG_JSON\n  prepare-semantic-order CONFIG_JSON\n  audit-tokens CONFIG_JSON\n  plan-batches CONFIG_JSON\n  prepare-representation CONFIG_JSON\n  validate-calibration-selection CONFIG_JSON SHARD_ORDINALS TOKEN_RANGE_UPPER_BOUNDS\n  embed-shards CONFIG_JSON SHARD_ORDINALS\n  calibrate-shards CONFIG_JSON SHARD_ORDINALS\n  verify-representation CONFIG_JSON\n  similar-notes CONFIG_JSON EVENT_IDS DEPTH REPRESENTATION_VERSION\n  vectors-for-notes CONFIG_JSON EVENT_IDS REPRESENTATION_VERSION"
        .to_owned()
}
