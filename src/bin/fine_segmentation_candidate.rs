//! Fresh-process command boundary for the controlled fine-segmentation candidates.

use std::collections::BTreeMap;
use std::env;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::ExitCode;

use oracle_mvp::fine_region_candidate::{
    FineRegionCandidateInput, HDBSCAN_CONTROLLED_SUITE_CONFIG_V1,
    HDBSCAN_CONTROLLED_SUITE_CONFIG_VERSION, HDBSCAN_CROSS_NOTE_CONTROLLED_SUITE_CONFIG_VERSION,
    HDBSCAN_CROSS_NOTE_EDGES_CONTROLLED_SUITE_CONFIG_VERSION, SNN_CONTROLLED_SUITE_CONFIG_V1,
    SNN_CONTROLLED_SUITE_CONFIG_VERSION,
};
use oracle_mvp::fine_region_candidate_artifact::{
    build_hdbscan_candidate_artifact, build_hdbscan_cross_note_candidate_artifact,
    build_hdbscan_cross_note_edges_candidate_artifact, build_snn_candidate_artifact,
};
use oracle_mvp::fine_region_hdbscan::HdbscanConfig;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use thiserror::Error;

const SCHEMA_VERSION: u32 = 1;
const USAGE: &str = "usage: fine-segmentation-candidate REQUEST.json [--threads N]";

type Result<T> = std::result::Result<T, CliError>;

#[derive(Debug, Error)]
enum CliError {
    #[error("failed to read `{path}`: {source}")]
    Read {
        path: PathBuf,
        #[source]
        source: std::io::Error,
    },
    #[error("failed to decode `{path}`: {source}")]
    Decode {
        path: PathBuf,
        #[source]
        source: serde_json::Error,
    },
    #[error("failed to encode candidate result: {0}")]
    Encode(#[from] serde_json::Error),
    #[error("candidate request invariant failed: {0}")]
    Invariant(String),
    #[error(transparent)]
    CandidateArtifact(#[from] oracle_mvp::fine_region_candidate_artifact::CandidateArtifactError),
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct Request {
    schema_version: u32,
    candidate: String,
    source_vector_manifest_sha256: String,
    normalized_vector_sha256: String,
    inputs: Vec<FineRegionCandidateInput>,
    hdbscan_configuration: Option<HdbscanConfig>,
    source_note_ids: Option<BTreeMap<String, String>>,
}

#[derive(Debug, Serialize)]
#[serde(deny_unknown_fields)]
struct Response {
    schema_version: u32,
    candidate_identity: &'static str,
    artifact: Value,
}

fn main() -> ExitCode {
    match run() {
        Ok(response) => match serde_json::to_string(&response) {
            Ok(encoded) => {
                println!("{encoded}");
                ExitCode::SUCCESS
            }
            Err(error) => {
                eprintln!("fine-segmentation candidate failed: {error}");
                ExitCode::FAILURE
            }
        },
        Err(error) => {
            eprintln!("fine-segmentation candidate failed: {error}");
            ExitCode::FAILURE
        }
    }
}

fn run() -> Result<Response> {
    let arguments = env::args_os().skip(1).collect::<Vec<_>>();
    let (request_path, threads) = match arguments.as_slice() {
        [path] => (path, None),
        [path, flag, count] if flag == "--threads" => {
            let count = count
                .to_str()
                .and_then(|value| value.parse::<usize>().ok())
                .filter(|count| *count > 0)
                .ok_or_else(|| invalid(USAGE))?;
            (path, Some(count))
        }
        _ => return Err(invalid(USAGE)),
    };
    let threads = threads
        .or_else(|| {
            env::var("RAYON_NUM_THREADS")
                .ok()
                .and_then(|value| value.parse::<usize>().ok())
                .filter(|count| *count > 0)
        })
        .unwrap_or_else(|| {
            std::thread::available_parallelism()
                .map(|count| count.get().saturating_sub(4).max(1))
                .unwrap_or(1)
        });
    let pool = rayon::ThreadPoolBuilder::new()
        .num_threads(threads)
        .build()
        .map_err(|error| invalid(format!("cannot create numerical worker pool: {error}")))?;
    pool.install(|| run_request(Path::new(request_path)))
}

fn run_request(request_path: &Path) -> Result<Response> {
    let bytes = fs::read(request_path).map_err(|source| CliError::Read {
        path: request_path.to_path_buf(),
        source,
    })?;
    let request: Request = serde_json::from_slice(&bytes).map_err(|source| CliError::Decode {
        path: request_path.to_path_buf(),
        source,
    })?;
    if request.schema_version != SCHEMA_VERSION {
        return Err(invalid(format!(
            "unsupported schema version {}",
            request.schema_version
        )));
    }

    if request.hdbscan_configuration.is_some()
        && !matches!(
            request.candidate.as_str(),
            "hdbscan" | "hdbscan_cross_note" | "hdbscan_cross_note_edges"
        )
    {
        return Err(invalid(
            "hdbscan_configuration requires candidate `hdbscan`, `hdbscan_cross_note`, or `hdbscan_cross_note_edges`",
        ));
    }
    if request.source_note_ids.is_some()
        && !matches!(
            request.candidate.as_str(),
            "hdbscan_cross_note" | "hdbscan_cross_note_edges"
        )
    {
        return Err(invalid(
            "source_note_ids requires candidate `hdbscan_cross_note` or `hdbscan_cross_note_edges`",
        ));
    }

    let (candidate_identity, artifact) = match request.candidate.as_str() {
        "snn" => (
            SNN_CONTROLLED_SUITE_CONFIG_VERSION,
            serde_json::to_value(build_snn_candidate_artifact(
                &request.inputs,
                &request.source_vector_manifest_sha256,
                &request.normalized_vector_sha256,
                &SNN_CONTROLLED_SUITE_CONFIG_V1,
            )?)?,
        ),
        "hdbscan" => (
            if request.hdbscan_configuration.is_some() {
                "hdbscan-explicit-config-v1"
            } else {
                HDBSCAN_CONTROLLED_SUITE_CONFIG_VERSION
            },
            serde_json::to_value(build_hdbscan_candidate_artifact(
                &request.inputs,
                &request.source_vector_manifest_sha256,
                &request.normalized_vector_sha256,
                request
                    .hdbscan_configuration
                    .as_ref()
                    .unwrap_or(&HDBSCAN_CONTROLLED_SUITE_CONFIG_V1),
            )?)?,
        ),
        "hdbscan_cross_note" => (
            if request.hdbscan_configuration.is_some() {
                "hdbscan-cross-note-explicit-config-v1"
            } else {
                HDBSCAN_CROSS_NOTE_CONTROLLED_SUITE_CONFIG_VERSION
            },
            serde_json::to_value(build_hdbscan_cross_note_candidate_artifact(
                &request.inputs,
                request.source_note_ids.as_ref().ok_or_else(|| {
                    invalid("source_note_ids is required for candidate `hdbscan_cross_note`")
                })?,
                &request.source_vector_manifest_sha256,
                &request.normalized_vector_sha256,
                request
                    .hdbscan_configuration
                    .as_ref()
                    .unwrap_or(&HDBSCAN_CONTROLLED_SUITE_CONFIG_V1),
            )?)?,
        ),
        "hdbscan_cross_note_edges" => (
            if request.hdbscan_configuration.is_some() {
                "hdbscan-cross-note-edges-explicit-config-v1"
            } else {
                HDBSCAN_CROSS_NOTE_EDGES_CONTROLLED_SUITE_CONFIG_VERSION
            },
            serde_json::to_value(build_hdbscan_cross_note_edges_candidate_artifact(
                &request.inputs,
                request.source_note_ids.as_ref().ok_or_else(|| {
                    invalid("source_note_ids is required for candidate `hdbscan_cross_note_edges`")
                })?,
                &request.source_vector_manifest_sha256,
                &request.normalized_vector_sha256,
                request
                    .hdbscan_configuration
                    .as_ref()
                    .unwrap_or(&HDBSCAN_CONTROLLED_SUITE_CONFIG_V1),
            )?)?,
        ),
        candidate => {
            return Err(invalid(format!("unsupported candidate `{candidate}`")));
        }
    };

    Ok(Response {
        schema_version: SCHEMA_VERSION,
        candidate_identity,
        artifact,
    })
}

fn invalid(message: impl Into<String>) -> CliError {
    CliError::Invariant(message.into())
}
