//! Auditable execution boundary for the sealed semantic-branch diagnostic.

use std::collections::BTreeMap;
use std::fs::{File, OpenOptions};
use std::io::{self, BufReader, BufWriter, Read, Write};
use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use thiserror::Error;

use crate::fp32_oracle::{StoredNoteVector, vectors_for_notes};
use crate::semantic_branch_artifact::{
    LABELER_A_LABELS_FILE, LABELER_B_LABELS_FILE, PRIVATE_KEY_FILE, SemanticBranchArtifactError,
    SemanticBranchPrepareConfig, open_sealed_semantic_branch_input,
};
use crate::semantic_branch_geometry::{
    BranchGeometryError, BranchSettings, SemanticBranchCandidate, SemanticBranchDecision,
    SemanticBranchReport, analyze_semantic_branches,
};
use crate::snapshot;

const ARTIFACT_SCHEMA_VERSION: u32 = 1;
const DIAGNOSTIC_ID: &str = "crec-110-semantic-branch-geometry-v1";
const PREPARE_MANIFEST_FILE: &str = "prepare-manifest.json";
const LABEL_SEAL_FILE: &str = "label-seal.json";
const EXPECTED_CANDIDATES: usize = 160;
const MINIMUM_EXCLUSIVE_NOTES: usize = 8;
const PERMUTATIONS: usize = 10_000;
const PERMUTATION_SEED: &str = "crec-110-semantic-branch-permutations-v1";

pub const SEMANTIC_BRANCH_REPORT_FILE: &str = "semantic-branch-report.json";

pub type Result<T> = std::result::Result<T, SemanticBranchAnalysisError>;

#[derive(Debug, Error)]
pub enum SemanticBranchAnalysisError {
    #[error("failed to {operation} `{path}`: {source}")]
    Io {
        operation: &'static str,
        path: PathBuf,
        #[source]
        source: io::Error,
    },
    #[error("failed to {operation} JSON `{path}`: {source}")]
    Json {
        operation: &'static str,
        path: PathBuf,
        #[source]
        source: serde_json::Error,
    },
    #[error("semantic-branch report already exists at `{0}`")]
    ArtifactExists(PathBuf),
    #[error("semantic-branch report does not exactly match recomputed analysis at `{0}`")]
    ReportMismatch(PathBuf),
    #[error("semantic-branch analysis invariant failed: {0}")]
    Invariant(String),
    #[error("hash mismatch for `{path}`: expected {expected}, got {actual}")]
    HashMismatch {
        path: PathBuf,
        expected: String,
        actual: String,
    },
    #[error(transparent)]
    Artifact(#[from] SemanticBranchArtifactError),
    #[error(transparent)]
    Geometry(#[from] BranchGeometryError),
    #[error(transparent)]
    Snapshot(#[from] snapshot::Error),
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SemanticBranchAnalysisConfig {
    pub run_path: PathBuf,
    pub ordered_event_ids_path: PathBuf,
    pub expected_ordered_event_ids_sha256: String,
    pub representation_path: PathBuf,
    pub representation_version: String,
    pub represented_rows: u64,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SemanticBranchAnalysisReport {
    pub schema_version: u32,
    pub diagnostic_id: String,
    pub necessary_condition_only: bool,
    pub analysis_config_sha256: String,
    pub run_input_sha256: BTreeMap<String, String>,
    pub ordered_event_ids_sha256: String,
    pub representation_version: String,
    pub represented_rows: u64,
    pub total_rows: u64,
    pub complete: bool,
    pub source_event_id: String,
    pub candidate_count: usize,
    pub vector_dimension: usize,
    pub vector_set_sha256: String,
    pub geometry: SemanticBranchReport,
    pub decision: SemanticBranchDecision,
}

pub fn read_semantic_branch_prepare_config(
    path: impl AsRef<Path>,
) -> Result<SemanticBranchPrepareConfig> {
    read_json(path.as_ref())
}

pub fn read_semantic_branch_analysis_config(
    path: impl AsRef<Path>,
) -> Result<SemanticBranchAnalysisConfig> {
    read_json(path.as_ref())
}

pub fn analyze_semantic_branch_from_config(
    path: impl AsRef<Path>,
) -> Result<SemanticBranchAnalysisReport> {
    let path = path.as_ref();
    let analysis_config_sha256 = hash_file(path)?;
    let config = read_semantic_branch_analysis_config(path)?;
    let report_path = config.run_path.join(SEMANTIC_BRANCH_REPORT_FILE);
    if report_path.exists() {
        return Err(SemanticBranchAnalysisError::ArtifactExists(report_path));
    }
    let report = compute_semantic_branch_report(&config, path, &analysis_config_sha256)?;
    write_json_exclusive(&report_path, &report)?;
    sync_parent(&report_path)?;
    Ok(report)
}

pub fn verify_semantic_branch_from_config(
    path: impl AsRef<Path>,
) -> Result<SemanticBranchAnalysisReport> {
    let path = path.as_ref();
    let analysis_config_sha256 = hash_file(path)?;
    let config = read_semantic_branch_analysis_config(path)?;
    let report_path = config.run_path.join(SEMANTIC_BRANCH_REPORT_FILE);
    let published = read_bytes(&report_path)?;
    let recomputed = compute_semantic_branch_report(&config, path, &analysis_config_sha256)?;
    let expected = encode_json(&report_path, &recomputed)?;
    if published != expected || read_bytes(&report_path)? != published {
        return Err(SemanticBranchAnalysisError::ReportMismatch(report_path));
    }
    Ok(recomputed)
}

fn compute_semantic_branch_report(
    config: &SemanticBranchAnalysisConfig,
    config_path: &Path,
    analysis_config_sha256: &str,
) -> Result<SemanticBranchAnalysisReport> {
    validate_analysis_config(config)?;

    // This must remain the first operation that reads prepared diagnostic inputs.
    // It verifies the label seal and every source hash before vector access.
    let sealed = open_sealed_semantic_branch_input(&config.run_path)?;
    if sealed.records().len() != EXPECTED_CANDIDATES {
        return Err(SemanticBranchAnalysisError::Invariant(format!(
            "sealed input has {} candidates; {EXPECTED_CANDIDATES} required",
            sealed.records().len()
        )));
    }
    if sealed.representation_version() != config.representation_version
        || sealed.represented_rows() != config.represented_rows
    {
        return Err(SemanticBranchAnalysisError::Invariant(
            "analysis config and sealed input name different representations".to_owned(),
        ));
    }
    let run_input_sha256 = run_input_hashes(&config.run_path)?;
    require_hash(
        &config.ordered_event_ids_path,
        &config.expected_ordered_event_ids_sha256,
    )?;

    let event_ids = sealed
        .records()
        .iter()
        .map(|record| record.event_id())
        .collect::<Vec<_>>();
    if event_ids.len() != EXPECTED_CANDIDATES {
        return Err(SemanticBranchAnalysisError::Invariant(
            "vector request does not contain exactly 160 event IDs".to_owned(),
        ));
    }
    let vector_response = vectors_for_notes(
        &config.ordered_event_ids_path,
        &config.representation_path,
        &event_ids,
        &config.representation_version,
    )?;
    validate_vector_response(config, &event_ids, &vector_response)?;

    let candidates = sealed
        .records()
        .iter()
        .zip(&vector_response.vectors)
        .map(|(record, stored)| {
            SemanticBranchCandidate::new(
                record.candidate_id().to_owned(),
                record.rank(),
                record.rank_quartile(),
                record.cached_cosine_score(),
                stored.vector.clone(),
            )
        })
        .collect::<std::result::Result<Vec<_>, _>>()?;

    let settings = BranchSettings::new(MINIMUM_EXCLUSIVE_NOTES, PERMUTATIONS, PERMUTATION_SEED)?;
    let geometry = analyze_semantic_branches(&candidates, sealed.label_sets(), &settings)?;

    let reopened = open_sealed_semantic_branch_input(&config.run_path)?;
    if reopened != sealed {
        return Err(SemanticBranchAnalysisError::Invariant(
            "sealed semantic-branch input changed during analysis".to_owned(),
        ));
    }
    require_hash(config_path, analysis_config_sha256)?;
    require_hash(
        &config.ordered_event_ids_path,
        &config.expected_ordered_event_ids_sha256,
    )?;
    if run_input_hashes(&config.run_path)? != run_input_sha256 {
        return Err(SemanticBranchAnalysisError::Invariant(
            "sealed run inputs changed during analysis".to_owned(),
        ));
    }

    let vector_dimension = vector_response
        .vectors
        .first()
        .map(|stored| stored.vector.len())
        .ok_or_else(|| {
            SemanticBranchAnalysisError::Invariant("Oracle vector response is empty".to_owned())
        })?;
    let report = SemanticBranchAnalysisReport {
        schema_version: ARTIFACT_SCHEMA_VERSION,
        diagnostic_id: DIAGNOSTIC_ID.to_owned(),
        necessary_condition_only: true,
        analysis_config_sha256: analysis_config_sha256.to_owned(),
        run_input_sha256,
        ordered_event_ids_sha256: config.expected_ordered_event_ids_sha256.clone(),
        representation_version: vector_response.representation_version,
        represented_rows: vector_response.represented_rows,
        total_rows: vector_response.total_rows,
        complete: vector_response.complete,
        source_event_id: encode_hex(&sealed.source_event_id()),
        candidate_count: candidates.len(),
        vector_dimension,
        vector_set_sha256: hash_vector_set(&candidates, &vector_response.vectors),
        decision: geometry.decision,
        geometry,
    };
    Ok(report)
}

fn validate_analysis_config(config: &SemanticBranchAnalysisConfig) -> Result<()> {
    if !is_sha256(&config.expected_ordered_event_ids_sha256)
        || !is_sha256(&config.representation_version)
        || config.represented_rows <= 1_024
        || config.run_path == config.representation_path
        || config.run_path == config.ordered_event_ids_path
    {
        return Err(SemanticBranchAnalysisError::Invariant(
            "analysis config has invalid identities or paths".to_owned(),
        ));
    }
    Ok(())
}

fn validate_vector_response(
    config: &SemanticBranchAnalysisConfig,
    event_ids: &[[u8; 32]],
    response: &crate::fp32_oracle::VectorsForNotesResponse,
) -> Result<()> {
    if !response.complete
        || response.representation_version != config.representation_version
        || response.represented_rows != config.represented_rows
        || response.total_rows != config.represented_rows
        || response.vectors.len() != EXPECTED_CANDIDATES
        || response.vectors.len() != event_ids.len()
    {
        return Err(SemanticBranchAnalysisError::Invariant(
            "Oracle vector response has the wrong version, row count, or completeness".to_owned(),
        ));
    }
    for (expected, stored) in event_ids.iter().zip(&response.vectors) {
        if stored.event_id != *expected {
            return Err(SemanticBranchAnalysisError::Invariant(
                "Oracle returned vectors outside the sealed request order".to_owned(),
            ));
        }
    }
    Ok(())
}

fn run_input_hashes(run_path: &Path) -> Result<BTreeMap<String, String>> {
    [
        PREPARE_MANIFEST_FILE,
        LABEL_SEAL_FILE,
        PRIVATE_KEY_FILE,
        LABELER_A_LABELS_FILE,
        LABELER_B_LABELS_FILE,
    ]
    .into_iter()
    .map(|name| {
        let path = run_path.join(name);
        Ok((name.to_owned(), hash_file(&path)?))
    })
    .collect()
}

fn hash_vector_set(candidates: &[SemanticBranchCandidate], vectors: &[StoredNoteVector]) -> String {
    let mut digest = Sha256::new();
    digest.update(b"oracle-mvp-semantic-branch-vector-set-v1\0");
    for (candidate, stored) in candidates.iter().zip(vectors) {
        digest.update((candidate.id().len() as u64).to_le_bytes());
        digest.update(candidate.id().as_bytes());
        digest.update(stored.event_id);
        digest.update((stored.vector.len() as u64).to_le_bytes());
        for coordinate in &stored.vector {
            digest.update(coordinate.to_bits().to_le_bytes());
        }
    }
    encode_hex(&digest.finalize())
}

fn read_json<T: for<'de> Deserialize<'de>>(path: &Path) -> Result<T> {
    let file = File::open(path).map_err(|source| io_error("open", path, source))?;
    serde_json::from_reader(BufReader::new(file)).map_err(|source| json_error("read", path, source))
}

fn write_json_exclusive<T: Serialize>(path: &Path, value: &T) -> Result<()> {
    let bytes = encode_json(path, value)?;
    let file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(path)
        .map_err(|source| {
            if source.kind() == io::ErrorKind::AlreadyExists {
                SemanticBranchAnalysisError::ArtifactExists(path.to_owned())
            } else {
                io_error("create", path, source)
            }
        })?;
    let mut writer = BufWriter::new(file);
    writer
        .write_all(&bytes)
        .map_err(|source| io_error("write", path, source))?;
    writer
        .flush()
        .map_err(|source| io_error("flush", path, source))?;
    writer
        .get_ref()
        .sync_all()
        .map_err(|source| io_error("sync", path, source))
}

fn encode_json<T: Serialize>(path: &Path, value: &T) -> Result<Vec<u8>> {
    let mut bytes =
        serde_json::to_vec_pretty(value).map_err(|source| json_error("encode", path, source))?;
    bytes.push(b'\n');
    Ok(bytes)
}

fn read_bytes(path: &Path) -> Result<Vec<u8>> {
    let mut file = File::open(path).map_err(|source| io_error("open", path, source))?;
    let mut bytes = Vec::new();
    file.read_to_end(&mut bytes)
        .map_err(|source| io_error("read", path, source))?;
    Ok(bytes)
}

fn sync_parent(path: &Path) -> Result<()> {
    let parent = path.parent().ok_or_else(|| {
        SemanticBranchAnalysisError::Invariant(format!(
            "artifact path `{}` has no parent",
            path.display()
        ))
    })?;
    File::open(parent)
        .and_then(|directory| directory.sync_all())
        .map_err(|source| io_error("sync directory", parent, source))
}

fn hash_file(path: &Path) -> Result<String> {
    let mut file = File::open(path).map_err(|source| io_error("open", path, source))?;
    let mut digest = Sha256::new();
    let mut buffer = [0_u8; 1024 * 1024];
    loop {
        let bytes = file
            .read(&mut buffer)
            .map_err(|source| io_error("read", path, source))?;
        if bytes == 0 {
            break;
        }
        digest.update(&buffer[..bytes]);
    }
    Ok(encode_hex(&digest.finalize()))
}

fn require_hash(path: &Path, expected: &str) -> Result<()> {
    let actual = hash_file(path)?;
    if actual == expected {
        Ok(())
    } else {
        Err(SemanticBranchAnalysisError::HashMismatch {
            path: path.to_owned(),
            expected: expected.to_owned(),
            actual,
        })
    }
}

fn is_sha256(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

fn encode_hex(bytes: &[u8]) -> String {
    bytes.iter().map(|byte| format!("{byte:02x}")).collect()
}

fn io_error(
    operation: &'static str,
    path: impl AsRef<Path>,
    source: io::Error,
) -> SemanticBranchAnalysisError {
    SemanticBranchAnalysisError::Io {
        operation,
        path: path.as_ref().to_owned(),
        source,
    }
}

fn json_error(
    operation: &'static str,
    path: impl AsRef<Path>,
    source: serde_json::Error,
) -> SemanticBranchAnalysisError {
    SemanticBranchAnalysisError::Json {
        operation,
        path: path.as_ref().to_owned(),
        source,
    }
}
