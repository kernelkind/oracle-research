//! Source-bound SSE worker input and deterministic subject-vector diagnostics.

use std::cmp::Ordering;
use std::collections::{BTreeMap, BTreeSet};
use std::ffi::CString;
use std::fs::{self, File, OpenOptions};
use std::io::{self, BufWriter, Read, Write};
use std::os::unix::ffi::OsStrExt;
use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};
use serde_json::Value;
use sha2::{Digest, Sha256};
use thiserror::Error;

use crate::sse_mask_review::{
    ProposedMaskFragment, VerifiedSubjectEncodingNote, load_verified_subject_mask_proposal,
};

const SCHEMA_VERSION: u32 = 1;
const DIAGNOSTIC_ID: &str = "sse-multivector-geometry-v1";
const RAW_VECTORS_FILE: &str = "raw-vectors.f32le";
const NORMALIZED_VECTORS_FILE: &str = "normalized-vectors.f32le";
const WORKER_RECEIPT_FILE: &str = "worker-receipt.json";
const ANALYSIS_FILE: &str = "analysis.json";
const MARKDOWN_FILE: &str = "analysis.md";
const MANIFEST_FILE: &str = "manifest.json";
const TREE_HASH_RULE: &str = "sorted-relative-path-type-size-content-sha256-v1";
const VECTOR_FORMAT: &str = "row-major-f32le-v1";
const POOLING_RULE: &str = "selected-contextual-token-mean-linear-relu-linear-v1";

pub type Result<T> = std::result::Result<T, SseVectorDiagnosticError>;

#[derive(Debug, Error)]
pub enum SseVectorDiagnosticError {
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
    #[error("SSE vector diagnostic artifact already exists at `{0}`")]
    ArtifactExists(PathBuf),
    #[error("SSE vector diagnostic artifact is missing at `{0}`")]
    ArtifactMissing(PathBuf),
    #[error("SSE vector diagnostic invariant failed: {0}")]
    Invariant(String),
    #[error("SSE vector diagnostic hash mismatch for `{path}`: expected {expected}, got {actual}")]
    HashMismatch {
        path: PathBuf,
        expected: String,
        actual: String,
    },
    #[error("SSE vector diagnostic output differs from its deterministic replay: `{0}`")]
    ReplayMismatch(PathBuf),
    #[error(transparent)]
    Source(#[from] crate::snapshot::Error),
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SseWorkerInput {
    pub schema_version: u32,
    pub proposal_sha256: String,
    pub notes: Vec<SseWorkerNote>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SseWorkerNote {
    pub note_id: String,
    pub text: String,
    pub subjects: Vec<SseWorkerSubject>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SseWorkerSubject {
    pub subject_id: String,
    pub byte_spans: Vec<[usize; 2]>,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SseWorkerReceipt {
    pub schema_version: u32,
    pub proposal_sha256: String,
    pub request_sha256: String,
    pub checkpoint_sha256: String,
    pub base_model_artifact_tree_sha256: String,
    pub tree_hash_rule: String,
    pub model: SseWorkerModel,
    pub runtime: Value,
    pub device: String,
    pub container_image: String,
    pub note_batch_size: u32,
    pub vector_format: String,
    pub dimensions: u32,
    pub row_count: usize,
    pub rows: Vec<SseWorkerReceiptRow>,
    pub files: BTreeMap<String, SseFileIdentity>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SseWorkerModel {
    pub base_model: String,
    pub dimensions: u32,
    pub maximum_tokens: u32,
    pub pooling: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SseWorkerReceiptRow {
    pub ordinal: usize,
    pub note_id: String,
    pub subject_id: String,
    pub token_count: u32,
    pub selected_token_indices: Vec<u32>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SseFileIdentity {
    pub bytes: u64,
    pub sha256: String,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SseVectorDiagnosticManifest {
    pub schema_version: u32,
    pub diagnostic_id: String,
    pub proposal_sha256: String,
    pub note_set_sha256: String,
    pub request_sha256: String,
    pub worker: SseWorkerExecution,
    pub note_count: usize,
    pub subject_count: usize,
    pub dimensions: u32,
    pub files: BTreeMap<String, SseFileIdentity>,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SseWorkerExecution {
    pub checkpoint_sha256: String,
    pub base_model_artifact_tree_sha256: String,
    pub tree_hash_rule: String,
    pub model: SseWorkerModel,
    pub runtime: Value,
    pub device: String,
    pub container_image: String,
    pub note_batch_size: u32,
    pub vector_format: String,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SseVectorAnalysisReport {
    pub schema_version: u32,
    pub diagnostic_id: String,
    pub proposal_sha256: String,
    pub note_count: usize,
    pub subject_count: usize,
    pub dimensions: u32,
    pub rules: SseAnalysisRules,
    pub pair_counts: PairCounts,
    pub distributions: SimilarityDistributions,
    pub nearest_overall_from_same_note: usize,
    pub nearest_overall_from_other_note: usize,
    pub subjects: Vec<SubjectAnalysis>,
    pub pairs: Vec<SubjectPairAnalysis>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SseAnalysisRules {
    pub cosine: String,
    pub normalization: String,
    pub pair_order: String,
    pub ranking: String,
    pub cross_note_percentile: String,
    pub distribution_quantiles: String,
    pub token_overlap: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct PairCounts {
    pub all: usize,
    pub same_note: usize,
    pub cross_note: usize,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SimilarityDistributions {
    pub same_note: DistributionSummary,
    pub same_note_disjoint_tokens: DistributionSummary,
    pub same_note_overlapping_tokens: DistributionSummary,
    pub cross_note: DistributionSummary,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct DistributionSummary {
    pub count: usize,
    pub minimum: Option<f64>,
    pub p05: Option<f64>,
    pub p25: Option<f64>,
    pub median: Option<f64>,
    pub p75: Option<f64>,
    pub p95: Option<f64>,
    pub maximum: Option<f64>,
    pub mean: Option<f64>,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SubjectAnalysis {
    pub ordinal: usize,
    pub note_id: String,
    pub subject_id: String,
    pub label: String,
    pub fragments: Vec<ProposedMaskFragment>,
    pub selected_token_indices: Vec<u32>,
    pub raw_norm: f64,
    pub nearest_overall: NeighborRank,
    pub cross_note_ranking: Vec<NeighborRank>,
    pub top_cross_note_neighbors: Vec<DetailedNeighbor>,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct NeighborRank {
    pub ordinal: usize,
    pub note_id: String,
    pub subject_id: String,
    pub cosine: f64,
    pub cross_note_percentile: Option<f64>,
    pub same_note: bool,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct DetailedNeighbor {
    pub ordinal: usize,
    pub note_id: String,
    pub subject_id: String,
    pub label: String,
    pub fragments: Vec<ProposedMaskFragment>,
    pub cosine: f64,
    pub cross_note_percentile: f64,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SubjectPairAnalysis {
    pub left_ordinal: usize,
    pub right_ordinal: usize,
    pub left_note_id: String,
    pub left_subject_id: String,
    pub right_note_id: String,
    pub right_subject_id: String,
    pub same_note: bool,
    pub cosine: f64,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub token_overlap: Option<TokenOverlap>,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TokenOverlap {
    pub left_selected_tokens: usize,
    pub right_selected_tokens: usize,
    pub intersection_tokens: usize,
    pub union_tokens: usize,
    pub jaccard: f64,
    pub relationship: TokenOverlapRelationship,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TokenOverlapRelationship {
    Disjoint,
    Equal,
    LeftSubset,
    RightSubset,
    Partial,
}

#[derive(Clone)]
struct SubjectMetadata {
    ordinal: usize,
    note_index: usize,
    note_id: String,
    subject_id: String,
    label: String,
    fragments: Vec<ProposedMaskFragment>,
}

struct ComputedDiagnostic {
    normalized_vectors: Vec<u8>,
    analysis: SseVectorAnalysisReport,
    analysis_bytes: Vec<u8>,
    markdown_bytes: Vec<u8>,
}

/// Validate all proposal/source bindings and publish the label-free worker packet.
pub fn prepare_sse_worker_input(
    proposal_path: impl AsRef<Path>,
    worker_input_path: impl AsRef<Path>,
) -> Result<()> {
    let proposal_path = proposal_path.as_ref();
    let worker_input_path = worker_input_path.as_ref();
    let (proposal_sha256, _, _, worker_input_bytes) = load_inputs(proposal_path)?;
    require_hash(proposal_path, &proposal_sha256)?;
    publish_new_file(worker_input_path, &worker_input_bytes)
}

/// Validate one worker result, compute the complete analysis, and atomically publish it.
pub fn analyze_sse_vectors(
    proposal_path: impl AsRef<Path>,
    worker_receipt_path: impl AsRef<Path>,
    raw_vectors_path: impl AsRef<Path>,
    output_path: impl AsRef<Path>,
) -> Result<SseVectorAnalysisReport> {
    let proposal_path = proposal_path.as_ref();
    let worker_receipt_path = worker_receipt_path.as_ref();
    let raw_vectors_path = raw_vectors_path.as_ref();
    let output_path = output_path.as_ref();
    if output_path.exists() {
        return Err(SseVectorDiagnosticError::ArtifactExists(
            output_path.to_owned(),
        ));
    }
    let (proposal_sha256, note_set_sha256, metadata, worker_input_bytes) =
        load_inputs(proposal_path)?;
    let worker_input_sha256 = hash_bytes(&worker_input_bytes);
    let worker_receipt_bytes = read_file(worker_receipt_path)?;
    let receipt: SseWorkerReceipt = decode_json(worker_receipt_path, &worker_receipt_bytes)?;
    let raw_vectors = read_file(raw_vectors_path)?;
    validate_receipt(
        &receipt,
        &proposal_sha256,
        &metadata,
        &worker_input_sha256,
        &raw_vectors,
        raw_vectors_path,
    )?;
    let computed = compute_diagnostic(&proposal_sha256, &metadata, &receipt, &raw_vectors)?;
    require_hash(proposal_path, &proposal_sha256)?;
    let parent = output_path.parent().unwrap_or_else(|| Path::new("."));
    fs::create_dir_all(parent).map_err(|source| io_error("create directory", parent, source))?;
    let stage = stage_path(output_path)?;
    fs::create_dir(&stage).map_err(|source| {
        if source.kind() == io::ErrorKind::AlreadyExists {
            SseVectorDiagnosticError::ArtifactExists(stage.clone())
        } else {
            io_error("create directory", &stage, source)
        }
    })?;
    let publication = publish_analysis_stage(
        &stage,
        &proposal_sha256,
        &note_set_sha256,
        &worker_input_sha256,
        &metadata,
        &receipt,
        &worker_receipt_bytes,
        &raw_vectors,
        &computed,
    );
    if let Err(error) = publication {
        let _ = fs::remove_dir_all(&stage);
        return Err(error);
    }
    require_hash(proposal_path, &proposal_sha256)?;
    if let Err(error) = rename_no_replace(&stage, output_path) {
        let _ = fs::remove_dir_all(&stage);
        return Err(error);
    }
    sync_directory(parent)?;
    Ok(computed.analysis)
}

/// Rebind every source and deterministically replay the published analysis without writing.
pub fn verify_sse_vector_diagnostic(
    proposal_path: impl AsRef<Path>,
    output_path: impl AsRef<Path>,
) -> Result<SseVectorAnalysisReport> {
    let proposal_path = proposal_path.as_ref();
    let output_path = output_path.as_ref();
    if !output_path.is_dir() {
        return Err(SseVectorDiagnosticError::ArtifactMissing(
            output_path.to_owned(),
        ));
    }
    let (proposal_sha256, note_set_sha256, metadata, worker_input_bytes) =
        load_inputs(proposal_path)?;
    let worker_input_sha256 = hash_bytes(&worker_input_bytes);
    let manifest_path = output_path.join(MANIFEST_FILE);
    let manifest_bytes = read_file(&manifest_path)?;
    let manifest: SseVectorDiagnosticManifest = decode_json(&manifest_path, &manifest_bytes)?;
    let file_bytes = read_and_validate_artifact_files(output_path, &manifest)?;
    let receipt_path = output_path.join(WORKER_RECEIPT_FILE);
    let receipt: SseWorkerReceipt = decode_json(
        &receipt_path,
        file_bytes
            .get(WORKER_RECEIPT_FILE)
            .expect("validated required file"),
    )?;
    let raw_vectors = file_bytes
        .get(RAW_VECTORS_FILE)
        .expect("validated required file");
    validate_receipt(
        &receipt,
        &proposal_sha256,
        &metadata,
        &worker_input_sha256,
        raw_vectors,
        &output_path.join(RAW_VECTORS_FILE),
    )?;
    let computed = compute_diagnostic(&proposal_sha256, &metadata, &receipt, raw_vectors)?;
    let expected_manifest = build_manifest(
        &proposal_sha256,
        &note_set_sha256,
        &worker_input_sha256,
        &metadata,
        &receipt,
        &file_bytes,
    )?;
    compare_bytes(
        &output_path.join(NORMALIZED_VECTORS_FILE),
        file_bytes
            .get(NORMALIZED_VECTORS_FILE)
            .expect("validated required file"),
        &computed.normalized_vectors,
    )?;
    compare_bytes(
        &output_path.join(ANALYSIS_FILE),
        file_bytes
            .get(ANALYSIS_FILE)
            .expect("validated required file"),
        &computed.analysis_bytes,
    )?;
    compare_bytes(
        &output_path.join(MARKDOWN_FILE),
        file_bytes
            .get(MARKDOWN_FILE)
            .expect("validated required file"),
        &computed.markdown_bytes,
    )?;
    compare_bytes(
        &manifest_path,
        &manifest_bytes,
        &encode_json(&manifest_path, &expected_manifest)?,
    )?;
    require_hash(proposal_path, &proposal_sha256)?;
    for (name, bytes) in &file_bytes {
        compare_bytes(
            &output_path.join(name),
            bytes,
            &read_file(&output_path.join(name))?,
        )?;
    }
    compare_bytes(&manifest_path, &manifest_bytes, &read_file(&manifest_path)?)?;
    Ok(computed.analysis)
}

fn load_inputs(proposal_path: &Path) -> Result<(String, String, Vec<SubjectMetadata>, Vec<u8>)> {
    let proposal_sha256 = hash_file(proposal_path)?;
    let proposal = load_verified_subject_mask_proposal(proposal_path)?;
    let note_set_sha256 = proposal.note_set_sha256().to_owned();
    let notes = proposal.encoding_notes();
    if notes.len() < 2 || proposal.subject_count() < 2 {
        return invariant("the diagnostic requires at least two notes and two subjects");
    }
    let worker_input = build_worker_input(&proposal_sha256, &notes);
    let worker_input_bytes = encode_json(proposal_path, &worker_input)?;
    let metadata = flatten_metadata(&notes);
    Ok((
        proposal_sha256,
        note_set_sha256,
        metadata,
        worker_input_bytes,
    ))
}

fn build_worker_input(
    proposal_sha256: &str,
    notes: &[VerifiedSubjectEncodingNote],
) -> SseWorkerInput {
    SseWorkerInput {
        schema_version: SCHEMA_VERSION,
        proposal_sha256: proposal_sha256.to_owned(),
        notes: notes
            .iter()
            .map(|note| SseWorkerNote {
                note_id: note.note_id.clone(),
                text: note.content.clone(),
                subjects: note
                    .subjects
                    .iter()
                    .map(|subject| SseWorkerSubject {
                        subject_id: subject.subject_id.clone(),
                        byte_spans: subject
                            .byte_spans
                            .iter()
                            .map(|&(start_byte, end_byte)| [start_byte, end_byte])
                            .collect(),
                    })
                    .collect(),
            })
            .collect(),
    }
}

fn flatten_metadata(notes: &[VerifiedSubjectEncodingNote]) -> Vec<SubjectMetadata> {
    let mut metadata = Vec::new();
    for (note_index, note) in notes.iter().enumerate() {
        for subject in &note.subjects {
            metadata.push(SubjectMetadata {
                ordinal: metadata.len(),
                note_index,
                note_id: note.note_id.clone(),
                subject_id: subject.subject_id.clone(),
                label: subject.label.clone(),
                fragments: subject.fragments.clone(),
            });
        }
    }
    metadata
}

fn validate_receipt(
    receipt: &SseWorkerReceipt,
    proposal_sha256: &str,
    metadata: &[SubjectMetadata],
    worker_input_sha256: &str,
    raw_vectors: &[u8],
    raw_vectors_path: &Path,
) -> Result<()> {
    let raw_identity = receipt.files.get(RAW_VECTORS_FILE).ok_or_else(|| {
        SseVectorDiagnosticError::Invariant(
            "worker receipt does not identify raw-vectors.f32le".to_owned(),
        )
    })?;
    if receipt.schema_version != SCHEMA_VERSION
        || receipt.proposal_sha256 != proposal_sha256
        || receipt.request_sha256 != worker_input_sha256
        || !is_sha256(&receipt.checkpoint_sha256)
        || !is_sha256(&receipt.base_model_artifact_tree_sha256)
        || receipt.tree_hash_rule != TREE_HASH_RULE
        || receipt.model.base_model.trim().is_empty()
        || receipt.model.dimensions != receipt.dimensions
        || receipt.model.maximum_tokens == 0
        || receipt.model.pooling != POOLING_RULE
        || !receipt.runtime.is_object()
        || receipt.device != "cpu"
        || !is_immutable_image(&receipt.container_image)
        || receipt.note_batch_size == 0
        || receipt.vector_format != VECTOR_FORMAT
        || receipt.dimensions == 0
        || receipt.row_count != metadata.len()
        || receipt.files.len() != 1
        || !is_sha256(&raw_identity.sha256)
        || receipt.rows.len() != metadata.len()
    {
        return invariant("worker receipt has the wrong schema, input, dimensions, or row count");
    }
    let expected_bytes = metadata
        .len()
        .checked_mul(receipt.dimensions as usize)
        .and_then(|values| values.checked_mul(size_of::<f32>()))
        .ok_or_else(|| {
            SseVectorDiagnosticError::Invariant("worker vector byte length overflowed".to_owned())
        })?;
    if raw_vectors.len() != expected_bytes
        || raw_identity.bytes != expected_bytes as u64
        || hash_bytes(raw_vectors) != raw_identity.sha256
    {
        return Err(SseVectorDiagnosticError::HashMismatch {
            path: raw_vectors_path.to_owned(),
            expected: raw_identity.sha256.clone(),
            actual: hash_bytes(raw_vectors),
        });
    }
    let mut note_token_counts = BTreeMap::new();
    for (ordinal, (row, expected)) in receipt.rows.iter().zip(metadata).enumerate() {
        if row.ordinal != ordinal
            || row.note_id != expected.note_id
            || row.subject_id != expected.subject_id
            || row.token_count == 0
            || row.selected_token_indices.is_empty()
            || row
                .selected_token_indices
                .iter()
                .any(|index| *index >= row.token_count)
            || row
                .selected_token_indices
                .windows(2)
                .any(|pair| pair[0] >= pair[1])
        {
            return invariant(format!(
                "worker row {} has the wrong identity or invalid selected token indices",
                expected.ordinal
            ));
        }
        match note_token_counts.insert(row.note_id.as_str(), row.token_count) {
            Some(previous) if previous != row.token_count => {
                return invariant(format!(
                    "worker rows for note {} disagree on token count",
                    row.note_id
                ));
            }
            _ => {}
        }
    }
    Ok(())
}

fn compute_diagnostic(
    proposal_sha256: &str,
    metadata: &[SubjectMetadata],
    receipt: &SseWorkerReceipt,
    raw_vectors: &[u8],
) -> Result<ComputedDiagnostic> {
    let dimensions = receipt.dimensions as usize;
    let raw = raw_vectors
        .chunks_exact(size_of::<f32>())
        .map(|bytes| f32::from_le_bytes(bytes.try_into().expect("f32 width")))
        .collect::<Vec<_>>();
    if raw.iter().any(|value| !value.is_finite()) {
        return invariant("worker returned a non-finite vector coordinate");
    }
    let mut norms = Vec::with_capacity(metadata.len());
    let mut normalized = Vec::with_capacity(raw.len());
    for row in raw.chunks_exact(dimensions) {
        let norm = row
            .iter()
            .map(|value| {
                let value = f64::from(*value);
                value * value
            })
            .sum::<f64>()
            .sqrt();
        if !norm.is_finite() || norm == 0.0 {
            return invariant("worker returned a zero-norm or non-finite vector");
        }
        norms.push(norm);
        normalized.extend(row.iter().map(|value| (f64::from(*value) / norm) as f32));
    }
    let normalized_vectors = normalized
        .iter()
        .flat_map(|value| value.to_le_bytes())
        .collect::<Vec<_>>();
    let count = metadata.len();
    let mut cosine_matrix = vec![1.0_f64; count * count];
    let mut pairs = Vec::with_capacity(count * (count - 1) / 2);
    let mut same_values = Vec::new();
    let mut same_disjoint_values = Vec::new();
    let mut same_overlap_values = Vec::new();
    let mut cross_values = Vec::new();
    for left in 0..count {
        for right in (left + 1)..count {
            let cosine = cosine(
                &raw[left * dimensions..(left + 1) * dimensions],
                norms[left],
                &raw[right * dimensions..(right + 1) * dimensions],
                norms[right],
            )?;
            cosine_matrix[left * count + right] = cosine;
            cosine_matrix[right * count + left] = cosine;
            let same_note = metadata[left].note_index == metadata[right].note_index;
            let token_overlap = same_note.then(|| {
                token_overlap(
                    &receipt.rows[left].selected_token_indices,
                    &receipt.rows[right].selected_token_indices,
                )
            });
            if same_note {
                same_values.push(cosine);
                if token_overlap
                    .as_ref()
                    .is_some_and(|overlap| overlap.intersection_tokens == 0)
                {
                    same_disjoint_values.push(cosine);
                } else {
                    same_overlap_values.push(cosine);
                }
            } else {
                cross_values.push(cosine);
            }
            pairs.push(SubjectPairAnalysis {
                left_ordinal: left,
                right_ordinal: right,
                left_note_id: metadata[left].note_id.clone(),
                left_subject_id: metadata[left].subject_id.clone(),
                right_note_id: metadata[right].note_id.clone(),
                right_subject_id: metadata[right].subject_id.clone(),
                same_note,
                cosine,
                token_overlap,
            });
        }
    }
    if cross_values.is_empty() {
        return invariant("the diagnostic has no cross-note subject pairs");
    }
    let mut sorted_cross = cross_values.clone();
    sorted_cross.sort_by(f64::total_cmp);
    let mut subjects = Vec::with_capacity(count);
    let mut nearest_same_note = 0;
    for source in 0..count {
        let mut all_neighbors = (0..count)
            .filter(|candidate| *candidate != source)
            .collect::<Vec<_>>();
        sort_neighbors(&mut all_neighbors, source, &cosine_matrix, count, metadata);
        let nearest = all_neighbors[0];
        let nearest_same = metadata[source].note_index == metadata[nearest].note_index;
        nearest_same_note += usize::from(nearest_same);
        let mut cross_neighbors = all_neighbors
            .into_iter()
            .filter(|candidate| metadata[source].note_index != metadata[*candidate].note_index)
            .collect::<Vec<_>>();
        sort_neighbors(
            &mut cross_neighbors,
            source,
            &cosine_matrix,
            count,
            metadata,
        );
        let cross_note_ranking = cross_neighbors
            .iter()
            .map(|candidate| {
                let cosine = cosine_matrix[source * count + *candidate];
                NeighborRank {
                    ordinal: *candidate,
                    note_id: metadata[*candidate].note_id.clone(),
                    subject_id: metadata[*candidate].subject_id.clone(),
                    cosine,
                    cross_note_percentile: Some(inclusive_percentile(&sorted_cross, cosine)),
                    same_note: false,
                }
            })
            .collect::<Vec<_>>();
        let top_cross_note_neighbors = cross_neighbors
            .iter()
            .take(5)
            .map(|candidate| {
                let cosine = cosine_matrix[source * count + *candidate];
                DetailedNeighbor {
                    ordinal: *candidate,
                    note_id: metadata[*candidate].note_id.clone(),
                    subject_id: metadata[*candidate].subject_id.clone(),
                    label: metadata[*candidate].label.clone(),
                    fragments: metadata[*candidate].fragments.clone(),
                    cosine,
                    cross_note_percentile: inclusive_percentile(&sorted_cross, cosine),
                }
            })
            .collect();
        let nearest_cosine = cosine_matrix[source * count + nearest];
        subjects.push(SubjectAnalysis {
            ordinal: source,
            note_id: metadata[source].note_id.clone(),
            subject_id: metadata[source].subject_id.clone(),
            label: metadata[source].label.clone(),
            fragments: metadata[source].fragments.clone(),
            selected_token_indices: receipt.rows[source].selected_token_indices.clone(),
            raw_norm: norms[source],
            nearest_overall: NeighborRank {
                ordinal: nearest,
                note_id: metadata[nearest].note_id.clone(),
                subject_id: metadata[nearest].subject_id.clone(),
                cosine: nearest_cosine,
                cross_note_percentile: (!nearest_same)
                    .then(|| inclusive_percentile(&sorted_cross, nearest_cosine)),
                same_note: nearest_same,
            },
            cross_note_ranking,
            top_cross_note_neighbors,
        });
    }
    let same_note = same_values.len();
    let cross_note = cross_values.len();
    let analysis = SseVectorAnalysisReport {
        schema_version: SCHEMA_VERSION,
        diagnostic_id: DIAGNOSTIC_ID.to_owned(),
        proposal_sha256: proposal_sha256.to_owned(),
        note_count: metadata
            .iter()
            .map(|item| item.note_index)
            .collect::<BTreeSet<_>>()
            .len(),
        subject_count: count,
        dimensions: receipt.dimensions,
        rules: analysis_rules(),
        pair_counts: PairCounts {
            all: pairs.len(),
            same_note,
            cross_note,
        },
        distributions: SimilarityDistributions {
            same_note: distribution(&same_values),
            same_note_disjoint_tokens: distribution(&same_disjoint_values),
            same_note_overlapping_tokens: distribution(&same_overlap_values),
            cross_note: distribution(&cross_values),
        },
        nearest_overall_from_same_note: nearest_same_note,
        nearest_overall_from_other_note: count - nearest_same_note,
        subjects,
        pairs,
    };
    let analysis_path = Path::new(ANALYSIS_FILE);
    let analysis_bytes = encode_json(analysis_path, &analysis)?;
    let markdown_bytes = markdown_report(&analysis).into_bytes();
    Ok(ComputedDiagnostic {
        normalized_vectors,
        analysis,
        analysis_bytes,
        markdown_bytes,
    })
}

fn cosine(left: &[f32], left_norm: f64, right: &[f32], right_norm: f64) -> Result<f64> {
    let dot = left
        .iter()
        .zip(right)
        .map(|(left, right)| f64::from(*left) * f64::from(*right))
        .sum::<f64>();
    let cosine = dot / (left_norm * right_norm);
    if !cosine.is_finite() {
        return invariant("cosine computation produced a non-finite value");
    }
    Ok(cosine)
}

fn token_overlap(left: &[u32], right: &[u32]) -> TokenOverlap {
    let mut left_cursor = 0;
    let mut right_cursor = 0;
    let mut intersection = 0;
    while left_cursor < left.len() && right_cursor < right.len() {
        match left[left_cursor].cmp(&right[right_cursor]) {
            Ordering::Less => left_cursor += 1,
            Ordering::Greater => right_cursor += 1,
            Ordering::Equal => {
                intersection += 1;
                left_cursor += 1;
                right_cursor += 1;
            }
        }
    }
    let union = left.len() + right.len() - intersection;
    let relationship = if intersection == 0 {
        TokenOverlapRelationship::Disjoint
    } else if left == right {
        TokenOverlapRelationship::Equal
    } else if intersection == left.len() {
        TokenOverlapRelationship::LeftSubset
    } else if intersection == right.len() {
        TokenOverlapRelationship::RightSubset
    } else {
        TokenOverlapRelationship::Partial
    };
    TokenOverlap {
        left_selected_tokens: left.len(),
        right_selected_tokens: right.len(),
        intersection_tokens: intersection,
        union_tokens: union,
        jaccard: intersection as f64 / union as f64,
        relationship,
    }
}

fn sort_neighbors(
    neighbors: &mut [usize],
    source: usize,
    cosines: &[f64],
    count: usize,
    metadata: &[SubjectMetadata],
) {
    neighbors.sort_by(|left, right| {
        cosines[source * count + *right]
            .total_cmp(&cosines[source * count + *left])
            .then_with(|| metadata[*left].note_id.cmp(&metadata[*right].note_id))
            .then_with(|| metadata[*left].subject_id.cmp(&metadata[*right].subject_id))
    });
}

fn inclusive_percentile(sorted: &[f64], value: f64) -> f64 {
    let count = sorted.partition_point(|candidate| candidate.total_cmp(&value).is_le());
    count as f64 / sorted.len() as f64
}

fn distribution(values: &[f64]) -> DistributionSummary {
    if values.is_empty() {
        return DistributionSummary {
            count: 0,
            minimum: None,
            p05: None,
            p25: None,
            median: None,
            p75: None,
            p95: None,
            maximum: None,
            mean: None,
        };
    }
    let mut sorted = values.to_vec();
    sorted.sort_by(f64::total_cmp);
    DistributionSummary {
        count: sorted.len(),
        minimum: sorted.first().copied(),
        p05: Some(nearest_rank_quantile(&sorted, 5)),
        p25: Some(nearest_rank_quantile(&sorted, 25)),
        median: Some(nearest_rank_quantile(&sorted, 50)),
        p75: Some(nearest_rank_quantile(&sorted, 75)),
        p95: Some(nearest_rank_quantile(&sorted, 95)),
        maximum: sorted.last().copied(),
        mean: Some(values.iter().sum::<f64>() / values.len() as f64),
    }
}

fn nearest_rank_quantile(sorted: &[f64], percentile: usize) -> f64 {
    let rank = (sorted.len() - 1) * percentile / 100;
    sorted[rank]
}

fn analysis_rules() -> SseAnalysisRules {
    SseAnalysisRules {
        cosine: "f64-dot-and-f64-norms-over-ordered-raw-f32-coordinates-v1".to_owned(),
        normalization: "raw-f32-to-f64-l2-divide-round-each-coordinate-to-f32-v1".to_owned(),
        pair_order: "left-proposal-ordinal-then-right-proposal-ordinal-v1".to_owned(),
        ranking: "descending-cosine-then-note-id-then-subject-id-v1".to_owned(),
        cross_note_percentile: "inclusive-count-less-than-or-equal-over-all-cross-note-pairs-v1"
            .to_owned(),
        distribution_quantiles: "ascending-nearest-rank-floor-n-minus-one-times-p-v1".to_owned(),
        token_overlap: "intersection-of-worker-selected-token-indices-v1".to_owned(),
    }
}

#[allow(clippy::too_many_arguments)]
fn publish_analysis_stage(
    stage: &Path,
    proposal_sha256: &str,
    note_set_sha256: &str,
    worker_input_sha256: &str,
    metadata: &[SubjectMetadata],
    receipt: &SseWorkerReceipt,
    worker_receipt_bytes: &[u8],
    raw_vectors: &[u8],
    computed: &ComputedDiagnostic,
) -> Result<()> {
    write_bytes_exclusive(&stage.join(RAW_VECTORS_FILE), raw_vectors)?;
    write_bytes_exclusive(
        &stage.join(NORMALIZED_VECTORS_FILE),
        &computed.normalized_vectors,
    )?;
    write_bytes_exclusive(&stage.join(WORKER_RECEIPT_FILE), worker_receipt_bytes)?;
    write_bytes_exclusive(&stage.join(ANALYSIS_FILE), &computed.analysis_bytes)?;
    write_bytes_exclusive(&stage.join(MARKDOWN_FILE), &computed.markdown_bytes)?;
    let files = read_required_files(stage)?;
    let manifest = build_manifest(
        proposal_sha256,
        note_set_sha256,
        worker_input_sha256,
        metadata,
        receipt,
        &files,
    )?;
    write_bytes_exclusive(
        &stage.join(MANIFEST_FILE),
        &encode_json(&stage.join(MANIFEST_FILE), &manifest)?,
    )?;
    sync_directory(stage)
}

fn build_manifest(
    proposal_sha256: &str,
    note_set_sha256: &str,
    worker_input_sha256: &str,
    metadata: &[SubjectMetadata],
    receipt: &SseWorkerReceipt,
    files: &BTreeMap<String, Vec<u8>>,
) -> Result<SseVectorDiagnosticManifest> {
    if files.keys().map(String::as_str).collect::<BTreeSet<_>>()
        != required_files().into_iter().collect()
    {
        return invariant("diagnostic artifact file set is incomplete");
    }
    Ok(SseVectorDiagnosticManifest {
        schema_version: SCHEMA_VERSION,
        diagnostic_id: DIAGNOSTIC_ID.to_owned(),
        proposal_sha256: proposal_sha256.to_owned(),
        note_set_sha256: note_set_sha256.to_owned(),
        request_sha256: worker_input_sha256.to_owned(),
        worker: SseWorkerExecution {
            checkpoint_sha256: receipt.checkpoint_sha256.clone(),
            base_model_artifact_tree_sha256: receipt.base_model_artifact_tree_sha256.clone(),
            tree_hash_rule: receipt.tree_hash_rule.clone(),
            model: receipt.model.clone(),
            runtime: receipt.runtime.clone(),
            device: receipt.device.clone(),
            container_image: receipt.container_image.clone(),
            note_batch_size: receipt.note_batch_size,
            vector_format: receipt.vector_format.clone(),
        },
        note_count: metadata
            .iter()
            .map(|item| item.note_index)
            .collect::<BTreeSet<_>>()
            .len(),
        subject_count: metadata.len(),
        dimensions: receipt.dimensions,
        files: files
            .iter()
            .map(|(name, bytes)| {
                (
                    name.clone(),
                    SseFileIdentity {
                        bytes: bytes.len() as u64,
                        sha256: hash_bytes(bytes),
                    },
                )
            })
            .collect(),
    })
}

fn read_and_validate_artifact_files(
    output_path: &Path,
    manifest: &SseVectorDiagnosticManifest,
) -> Result<BTreeMap<String, Vec<u8>>> {
    if manifest.schema_version != SCHEMA_VERSION
        || manifest.diagnostic_id != DIAGNOSTIC_ID
        || !is_sha256(&manifest.proposal_sha256)
        || !is_sha256(&manifest.note_set_sha256)
        || !is_sha256(&manifest.request_sha256)
        || manifest.note_count < 2
        || manifest.subject_count < 2
        || manifest.dimensions == 0
        || manifest
            .files
            .keys()
            .map(String::as_str)
            .collect::<BTreeSet<_>>()
            != required_files().into_iter().collect()
    {
        return invariant("published diagnostic manifest is invalid");
    }
    let files = read_required_files(output_path)?;
    for (name, bytes) in &files {
        let identity = manifest
            .files
            .get(name)
            .expect("validated complete file set");
        if identity.bytes != bytes.len() as u64 || identity.sha256 != hash_bytes(bytes) {
            return Err(SseVectorDiagnosticError::HashMismatch {
                path: output_path.join(name),
                expected: identity.sha256.clone(),
                actual: hash_bytes(bytes),
            });
        }
    }
    Ok(files)
}

fn read_required_files(root: &Path) -> Result<BTreeMap<String, Vec<u8>>> {
    required_files()
        .into_iter()
        .map(|name| Ok((name.to_owned(), read_file(&root.join(name))?)))
        .collect()
}

fn required_files() -> [&'static str; 5] {
    [
        RAW_VECTORS_FILE,
        NORMALIZED_VECTORS_FILE,
        WORKER_RECEIPT_FILE,
        ANALYSIS_FILE,
        MARKDOWN_FILE,
    ]
}

fn markdown_report(report: &SseVectorAnalysisReport) -> String {
    let mut output = format!(
        "# SSE Multi-Vector Diagnostic\n\n\
         This report describes measured geometry. It does not declare a pass or failure.\n\n\
         - Notes: {}\n\
         - Subjects: {}\n\
         - Dimensions: {}\n\
         - Unordered pairs: {} ({} same-note, {} cross-note)\n\
         - Nearest overall neighbor from the same note: {}\n\
         - Nearest overall neighbor from another note: {}\n\n\
         ## Similarity distributions\n\n\
         | Group | n | min | p05 | p25 | median | p75 | p95 | max | mean |\n\
         |---|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n",
        report.note_count,
        report.subject_count,
        report.dimensions,
        report.pair_counts.all,
        report.pair_counts.same_note,
        report.pair_counts.cross_note,
        report.nearest_overall_from_same_note,
        report.nearest_overall_from_other_note,
    );
    for (name, distribution) in [
        ("Same note", &report.distributions.same_note),
        (
            "Same note, disjoint selected tokens",
            &report.distributions.same_note_disjoint_tokens,
        ),
        (
            "Same note, overlapping selected tokens",
            &report.distributions.same_note_overlapping_tokens,
        ),
        ("Cross note", &report.distributions.cross_note),
    ] {
        output.push_str(&format!(
            "| {name} | {} | {} | {} | {} | {} | {} | {} | {} | {} |\n",
            distribution.count,
            metric(distribution.minimum),
            metric(distribution.p05),
            metric(distribution.p25),
            metric(distribution.median),
            metric(distribution.p75),
            metric(distribution.p95),
            metric(distribution.maximum),
            metric(distribution.mean),
        ));
    }
    output.push_str("\n## Per-subject nearest cross-note subjects\n\n");
    for subject in &report.subjects {
        output.push_str(&format!(
            "### {} · `{}` / `{}`\n\n",
            markdown_text(&subject.label),
            subject.note_id,
            subject.subject_id
        ));
        for neighbor in &subject.top_cross_note_neighbors {
            let fragments = neighbor
                .fragments
                .iter()
                .map(|fragment| markdown_text(&fragment.text))
                .collect::<Vec<_>>()
                .join(" · ");
            output.push_str(&format!(
                "- {:.6} (percentile {:.6}) — {} · `{}` / `{}` — {}\n",
                neighbor.cosine,
                neighbor.cross_note_percentile,
                markdown_text(&neighbor.label),
                neighbor.note_id,
                neighbor.subject_id,
                fragments,
            ));
        }
        output.push('\n');
    }
    output
}

fn metric(value: Option<f64>) -> String {
    value.map_or_else(|| "—".to_owned(), |value| format!("{value:.6}"))
}

fn markdown_text(value: &str) -> String {
    value
        .replace('\\', "\\\\")
        .replace('`', "\\`")
        .replace(['\r', '\n'], " ")
}

fn publish_new_file(path: &Path, bytes: &[u8]) -> Result<()> {
    if path.exists() {
        return Err(SseVectorDiagnosticError::ArtifactExists(path.to_owned()));
    }
    let parent = path.parent().unwrap_or_else(|| Path::new("."));
    fs::create_dir_all(parent).map_err(|source| io_error("create directory", parent, source))?;
    let name = path
        .file_name()
        .and_then(|name| name.to_str())
        .unwrap_or("sse-worker-input");
    let temporary = path.with_file_name(format!(".{name}.tmp-{}", std::process::id()));
    if temporary.exists() {
        return Err(SseVectorDiagnosticError::ArtifactExists(temporary));
    }
    if let Err(error) = write_bytes_exclusive(&temporary, bytes) {
        let _ = fs::remove_file(&temporary);
        return Err(error);
    }
    if let Err(error) = rename_no_replace(&temporary, path) {
        let _ = fs::remove_file(&temporary);
        return Err(error);
    }
    sync_directory(parent)
}

fn write_bytes_exclusive(path: &Path, bytes: &[u8]) -> Result<()> {
    let file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(path)
        .map_err(|source| {
            if source.kind() == io::ErrorKind::AlreadyExists {
                SseVectorDiagnosticError::ArtifactExists(path.to_owned())
            } else {
                io_error("create", path, source)
            }
        })?;
    let mut writer = BufWriter::new(file);
    writer
        .write_all(bytes)
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

fn decode_json<T: for<'de> Deserialize<'de>>(path: &Path, bytes: &[u8]) -> Result<T> {
    serde_json::from_slice(bytes).map_err(|source| json_error("decode", path, source))
}

fn read_file(path: &Path) -> Result<Vec<u8>> {
    let mut file = File::open(path).map_err(|source| {
        if source.kind() == io::ErrorKind::NotFound {
            SseVectorDiagnosticError::ArtifactMissing(path.to_owned())
        } else {
            io_error("open", path, source)
        }
    })?;
    let mut bytes = Vec::new();
    file.read_to_end(&mut bytes)
        .map_err(|source| io_error("read", path, source))?;
    Ok(bytes)
}

fn hash_file(path: &Path) -> Result<String> {
    Ok(hash_bytes(&read_file(path)?))
}

fn require_hash(path: &Path, expected: &str) -> Result<()> {
    let actual = hash_file(path)?;
    if actual == expected {
        Ok(())
    } else {
        Err(SseVectorDiagnosticError::HashMismatch {
            path: path.to_owned(),
            expected: expected.to_owned(),
            actual,
        })
    }
}

fn hash_bytes(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}

fn is_sha256(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

fn is_immutable_image(value: &str) -> bool {
    value
        .rsplit_once("@sha256:")
        .is_some_and(|(name, digest)| !name.is_empty() && is_sha256(digest))
}

fn compare_bytes(path: &Path, actual: &[u8], expected: &[u8]) -> Result<()> {
    if actual == expected {
        Ok(())
    } else {
        Err(SseVectorDiagnosticError::ReplayMismatch(path.to_owned()))
    }
}

fn stage_path(output: &Path) -> Result<PathBuf> {
    let name = output
        .file_name()
        .and_then(|name| name.to_str())
        .ok_or_else(|| {
            SseVectorDiagnosticError::Invariant(format!(
                "output path `{}` has no UTF-8 filename",
                output.display()
            ))
        })?;
    Ok(output.with_file_name(format!(".{name}.stage-{}", std::process::id())))
}

fn rename_no_replace(source: &Path, destination: &Path) -> Result<()> {
    let source_bytes = CString::new(source.as_os_str().as_bytes()).map_err(|_| {
        SseVectorDiagnosticError::Invariant(format!(
            "source path `{}` contains a null byte",
            source.display()
        ))
    })?;
    let destination_bytes = CString::new(destination.as_os_str().as_bytes()).map_err(|_| {
        SseVectorDiagnosticError::Invariant(format!(
            "destination path `{}` contains a null byte",
            destination.display()
        ))
    })?;
    // SAFETY: both strings are live, null-terminated path names. RENAME_NOREPLACE
    // atomically refuses a destination created by a competing process.
    let result = unsafe {
        libc::renameat2(
            libc::AT_FDCWD,
            source_bytes.as_ptr(),
            libc::AT_FDCWD,
            destination_bytes.as_ptr(),
            libc::RENAME_NOREPLACE,
        )
    };
    if result == 0 {
        return Ok(());
    }
    let error = io::Error::last_os_error();
    if error.kind() == io::ErrorKind::AlreadyExists {
        Err(SseVectorDiagnosticError::ArtifactExists(
            destination.to_owned(),
        ))
    } else {
        Err(io_error("publish", destination, error))
    }
}

fn sync_directory(path: &Path) -> Result<()> {
    File::open(path)
        .and_then(|directory| directory.sync_all())
        .map_err(|source| io_error("sync directory", path, source))
}

fn invariant<T>(message: impl Into<String>) -> Result<T> {
    Err(SseVectorDiagnosticError::Invariant(message.into()))
}

fn io_error(
    operation: &'static str,
    path: impl AsRef<Path>,
    source: io::Error,
) -> SseVectorDiagnosticError {
    SseVectorDiagnosticError::Io {
        operation,
        path: path.as_ref().to_owned(),
        source,
    }
}

fn json_error(
    operation: &'static str,
    path: impl AsRef<Path>,
    source: serde_json::Error,
) -> SseVectorDiagnosticError {
    SseVectorDiagnosticError::Json {
        operation,
        path: path.as_ref().to_owned(),
        source,
    }
}
