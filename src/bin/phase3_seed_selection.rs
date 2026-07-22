//! Full-screen execution of a prepared Phase 3 seed-selection workspace.

use std::collections::BTreeSet;
use std::env;
use std::fs::File;
use std::io::{BufReader, IsTerminal};
use std::path::{Path, PathBuf};
use std::process::ExitCode;

use nostrdb::{Config, Ndb, Transaction};
use oracle_mvp::evaluator_tui::FullScreenEvaluator;
use oracle_mvp::fp32_oracle::{Fp32OfflineOracle, vectors_for_notes};
use oracle_mvp::gte::{GteProcessEncoder, GteWorkerConfig};
use oracle_mvp::phase3_seed_selection::{
    Phase3SeedSelectionConfig, Phase3SeedSelectionOutcome, run_phase3_seed_selection,
};
use oracle_mvp::representation::{EventId, RepresentationManifest};
use serde::Deserialize;

const CONFIG_SCHEMA_VERSION: u32 = 1;
const PURPOSE: &str = "phase3-seed-selection-v1";

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct LaunchConfig {
    schema_version: u32,
    purpose: String,
    workspace_path: PathBuf,
    corpus_path: PathBuf,
    ordered_event_ids_path: PathBuf,
    representation_path: PathBuf,
    model_bundle_path: PathBuf,
    candidate_event_ids_path: PathBuf,
    session_path: PathBuf,
    handoff_path: PathBuf,
    expected_representation_version: String,
}

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("phase3 seed selection failed: {error}");
            ExitCode::FAILURE
        }
    }
}

fn run() -> Result<(), String> {
    if !std::io::stdin().is_terminal() || !std::io::stdout().is_terminal() {
        return Err("seed selection must be started from an interactive terminal".to_owned());
    }
    let mut arguments = env::args_os().skip(1);
    let config_path = arguments.next().map(PathBuf::from).ok_or_else(usage)?;
    if arguments.next().is_some() {
        return Err(usage());
    }
    let config_path = std::fs::canonicalize(&config_path).map_err(|error| {
        format!(
            "could not resolve seed-selection config `{}`: {error}",
            config_path.display()
        )
    })?;
    let config: LaunchConfig = serde_json::from_reader(BufReader::new(
        File::open(&config_path)
            .map_err(|error| format!("could not open `{}`: {error}", config_path.display()))?,
    ))
    .map_err(|error| format!("could not decode `{}`: {error}", config_path.display()))?;
    validate_config(&config)?;

    let candidate_event_ids = read_candidate_ids(&config.candidate_event_ids_path)?;
    let represented = vectors_for_notes(
        &config.ordered_event_ids_path,
        &config.representation_path,
        &candidate_event_ids,
        &config.expected_representation_version,
    )
    .map_err(|error| error.to_string())?;
    if represented.vectors.len() != candidate_event_ids.len()
        || represented
            .vectors
            .iter()
            .zip(&candidate_event_ids)
            .any(|(stored, expected)| stored.event_id != *expected)
    {
        return Err("curated candidate list is not fully represented".to_owned());
    }
    let corpus = Ndb::new(
        config
            .corpus_path
            .to_str()
            .ok_or_else(|| "prepared corpus path is not UTF-8".to_owned())?,
        &Config::new().skip_validation(true),
    )
    .map_err(|error| error.to_string())?;
    let transaction = Transaction::new(&corpus).map_err(|error| error.to_string())?;
    for event_id in &candidate_event_ids {
        corpus.get_note_by_id(&transaction, event_id).map_err(|_| {
            format!(
                "curated candidate {} is absent from the prepared corpus",
                hex(event_id)
            )
        })?;
    }
    drop(transaction);
    drop(corpus);

    let representation_manifest: RepresentationManifest =
        read_json(&config.representation_path.join("manifest.json"))?;
    let corpus_identity = format!("sha256:{}", representation_manifest.corpus_data_sha256);
    let descriptor = representation_manifest.descriptor;
    let encoder = GteProcessEncoder::start(GteWorkerConfig {
        program: "/opt/gte-venv/bin/python".into(),
        prefix_arguments: Vec::new(),
        worker_path: Some("/opt/oracle-mvp/gte/worker.py".into()),
        model_dir: config.model_bundle_path.join("model"),
        model_lock_path: config.model_bundle_path.join("model-lock.json"),
        dependency_lock_path: "/tmp/gte-locks/requirements.lock".into(),
        device: "cpu".to_owned(),
        model_lock_sha256: descriptor.model_lock_sha256,
        worker_sha256: descriptor.worker_sha256,
        dependency_lock_sha256: descriptor.dependency_lock_sha256,
        container_image: descriptor.container_image,
        torch_version: descriptor.torch_version,
        transformers_version: descriptor.transformers_version,
        cuda_version: descriptor.cuda_version,
    })
    .map_err(|error| error.to_string())?;
    let runner_config = Phase3SeedSelectionConfig {
        corpus_path: config.corpus_path.clone(),
        corpus_identity,
        session_path: config.session_path.clone(),
        handoff_path: config.handoff_path.clone(),
        representation_version: config.expected_representation_version.clone(),
        candidate_event_ids,
    };
    let mut oracle = Fp32OfflineOracle::open(
        &config.corpus_path,
        &config.ordered_event_ids_path,
        &config.representation_path,
        encoder,
    )
    .map_err(|error| error.to_string())?;
    let mut evaluator = FullScreenEvaluator::new().map_err(|error| error.to_string())?;
    match run_phase3_seed_selection(&runner_config, &mut oracle, &mut evaluator)
        .map_err(|error| error.to_string())?
    {
        Phase3SeedSelectionOutcome::Paused => {
            eprintln!("Seed selection paused safely. Run the same command to resume.");
        }
        Phase3SeedSelectionOutcome::Complete(_) => {
            eprintln!("Seed selection completed and the immutable handoff was published.");
        }
    }
    Ok(())
}

fn validate_config(config: &LaunchConfig) -> Result<(), String> {
    if config.schema_version != CONFIG_SCHEMA_VERSION || config.purpose != PURPOSE {
        return Err("seed-selection config has an incompatible schema or purpose".to_owned());
    }
    let workspace = canonical_directory(&config.workspace_path, "workspace")?;
    for (label, path) in [
        ("corpus", config.corpus_path.as_path()),
        ("ordered event IDs", config.ordered_event_ids_path.as_path()),
        ("representation", config.representation_path.as_path()),
        (
            "candidate event IDs",
            config.candidate_event_ids_path.as_path(),
        ),
        ("session", config.session_path.as_path()),
        ("handoff", config.handoff_path.as_path()),
    ] {
        if !path.is_absolute() || !resolved_path(path, label)?.starts_with(&workspace) {
            return Err(format!(
                "prepared seed-selection {label} must be inside the private workspace"
            ));
        }
    }
    if !config.model_bundle_path.is_absolute()
        || !config.model_bundle_path.join("model-lock.json").is_file()
    {
        return Err("seed-selection model bundle is invalid".to_owned());
    }
    if config.expected_representation_version.len() != 64
        || !config
            .expected_representation_version
            .bytes()
            .all(|byte| byte.is_ascii_hexdigit() && !byte.is_ascii_uppercase())
    {
        return Err("seed-selection representation version is invalid".to_owned());
    }
    Ok(())
}

fn canonical_directory(path: &Path, label: &str) -> Result<PathBuf, String> {
    let canonical = std::fs::canonicalize(path)
        .map_err(|error| format!("could not resolve {label} `{}`: {error}", path.display()))?;
    if !canonical.is_dir() {
        return Err(format!("{label} is not a directory"));
    }
    Ok(canonical)
}

fn resolved_path(path: &Path, label: &str) -> Result<PathBuf, String> {
    if path.exists() {
        return std::fs::canonicalize(path)
            .map_err(|error| format!("could not resolve {label} `{}`: {error}", path.display()));
    }
    let parent = path
        .parent()
        .ok_or_else(|| format!("prepared seed-selection {label} has no parent directory"))?;
    let file_name = path
        .file_name()
        .ok_or_else(|| format!("prepared seed-selection {label} has no file name"))?;
    let parent = std::fs::canonicalize(parent).map_err(|error| {
        format!(
            "could not resolve parent of prepared seed-selection {label} `{}`: {error}",
            path.display()
        )
    })?;
    Ok(parent.join(file_name))
}

fn read_candidate_ids(path: &Path) -> Result<Vec<EventId>, String> {
    let encoded: Vec<String> = read_json(path)?;
    let event_ids = encoded
        .iter()
        .map(|value| parse_event_id(value))
        .collect::<Result<Vec<_>, _>>()?;
    if event_ids.len() < 5
        || event_ids.iter().copied().collect::<BTreeSet<_>>().len() != event_ids.len()
    {
        return Err(
            "curated candidate list must contain at least five unique event IDs".to_owned(),
        );
    }
    Ok(event_ids)
}

fn parse_event_id(value: &str) -> Result<EventId, String> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_hexdigit() && !byte.is_ascii_uppercase())
    {
        return Err("candidate event IDs must be lowercase 64-digit hexadecimal".to_owned());
    }
    let mut event_id = [0_u8; 32];
    for (index, pair) in value.as_bytes().chunks_exact(2).enumerate() {
        event_id[index] = (hex_digit(pair[0])? << 4) | hex_digit(pair[1])?;
    }
    Ok(event_id)
}

fn hex_digit(byte: u8) -> Result<u8, String> {
    match byte {
        b'0'..=b'9' => Ok(byte - b'0'),
        b'a'..=b'f' => Ok(byte - b'a' + 10),
        _ => Err("invalid lowercase hexadecimal".to_owned()),
    }
}

fn read_json<T: serde::de::DeserializeOwned>(path: &Path) -> Result<T, String> {
    serde_json::from_reader(BufReader::new(
        File::open(path)
            .map_err(|error| format!("could not open `{}`: {error}", path.display()))?,
    ))
    .map_err(|error| format!("could not decode `{}`: {error}", path.display()))
}

fn hex(event_id: &EventId) -> String {
    event_id.iter().map(|byte| format!("{byte:02x}")).collect()
}

fn usage() -> String {
    "usage: phase3-seed-selection <prepared-config.json>".to_owned()
}
