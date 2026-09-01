//! Fresh-process command boundary for the controlled fine-segmentation candidates.

use std::env;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::ExitCode;

use oracle_mvp::fine_region_candidate::{
    FineRegionCandidateInput, HDBSCAN_CONTROLLED_SUITE_CONFIG_V1,
    HDBSCAN_CONTROLLED_SUITE_CONFIG_VERSION, SNN_CONTROLLED_SUITE_CONFIG_V1,
    SNN_CONTROLLED_SUITE_CONFIG_VERSION,
};
use oracle_mvp::fine_region_candidate_artifact::{
    build_hdbscan_candidate_artifact, build_snn_candidate_artifact,
};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use thiserror::Error;

const SCHEMA_VERSION: u32 = 1;
const USAGE: &str = "usage: fine-segmentation-candidate REQUEST.json";

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
    let [request_path] = arguments.as_slice() else {
        return Err(invalid(USAGE));
    };
    let request_path = Path::new(request_path);
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
            HDBSCAN_CONTROLLED_SUITE_CONFIG_VERSION,
            serde_json::to_value(build_hdbscan_candidate_artifact(
                &request.inputs,
                &request.source_vector_manifest_sha256,
                &request.normalized_vector_sha256,
                &HDBSCAN_CONTROLLED_SUITE_CONFIG_V1,
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
