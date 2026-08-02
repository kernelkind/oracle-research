//! Deterministic execution and analysis for the approved SSE context counterfactual.

use std::collections::{BTreeMap, BTreeSet};
use std::ffi::CString;
use std::fs::{self, File, OpenOptions};
use std::io::{self, Read, Write};
use std::os::unix::ffi::OsStrExt;
use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use thiserror::Error;

use crate::sse_vector_diagnostic::{
    SseFileIdentity, SseWorkerInput, SseWorkerNote, SseWorkerReceipt, SseWorkerSubject,
};

const SCHEMA_VERSION: u32 = 1;
const WORKER_INPUT_FILE: &str = "worker-input.json";
const WORKER_CONFIG_FILE: &str = "worker-config.json";
const COMPILE_MANIFEST_FILE: &str = "compile-manifest.json";
const RAW_VECTORS_FILE: &str = "raw-vectors.f32le";
const WORKER_RECEIPT_FILE: &str = "worker-receipt.json";
const ANALYSIS_FILE: &str = "analysis.json";
const MARKDOWN_FILE: &str = "analysis.md";
const ANALYSIS_MANIFEST_FILE: &str = "manifest.json";
const WORKER_SOURCE: &str = "sse_multivector/worker.py";
const APPROVED_FIXTURE_SHA256: &str =
    "3a791d395234b5ab4b9304c2c399480b94bf7244febf05f73390c95bf6cc8c48";

pub type Result<T> = std::result::Result<T, ContextCounterfactualError>;

#[derive(Debug, Error)]
pub enum ContextCounterfactualError {
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
    #[error("SSE context counterfactual artifact already exists at `{0}`")]
    ArtifactExists(PathBuf),
    #[error("SSE context counterfactual artifact is missing at `{0}`")]
    ArtifactMissing(PathBuf),
    #[error("SSE context counterfactual invariant failed: {0}")]
    Invariant(String),
    #[error(
        "SSE context counterfactual hash mismatch for `{path}`: expected {expected}, got {actual}"
    )]
    HashMismatch {
        path: PathBuf,
        expected: String,
        actual: String,
    },
    #[error("SSE context counterfactual replay differs at `{0}`")]
    ReplayMismatch(PathBuf),
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ContextExecutionContract {
    pub base_model: String,
    pub base_model_artifact_tree_sha256: String,
    pub checkpoint_sha256: String,
    pub container_image: String,
    pub worker_sha256: String,
    pub device: String,
    pub note_batch_size: u32,
    pub dimensions: u32,
    pub maximum_tokens: u32,
    pub pooling: String,
    pub vector_format: String,
    pub base_model_tree_hash_rule: String,
    pub cosine: String,
    pub invalid_vector_result: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ContextCompileRow {
    pub ordinal: usize,
    pub note_id: String,
    pub subject_id: String,
    pub target_id: Option<String>,
    pub preferred_group_id: String,
    pub alternative_group_ids: Vec<String>,
    pub reference_group_id: Option<String>,
    pub reference_index: Option<usize>,
}

/// One row in the exact worker-output order.
pub type ContextRowBinding = ContextCompileRow;

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ContextCompileManifest {
    pub schema_version: u32,
    pub fixture_id: String,
    pub fixture_sha256: String,
    pub request_sha256: String,
    pub worker_sha256: String,
    pub note_count: usize,
    pub target_count: usize,
    pub reference_count: usize,
    pub execution: ContextExecutionContract,
    pub rows: Vec<ContextCompileRow>,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ContextReferenceCosine {
    pub reference_index: usize,
    pub reference_ordinal: usize,
    pub reference_note_id: String,
    pub reference_subject_id: String,
    pub cosine: f64,
}

pub type ReferenceCosine = ContextReferenceCosine;

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ContextComparison {
    pub alternative_group_id: String,
    pub preferred_median: f64,
    pub alternative_median: f64,
    pub passed: bool,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ContextPrediction {
    pub target_id: String,
    pub target_ordinal: usize,
    pub preferred_group_id: String,
    pub preferred_median: f64,
    pub reference_cosines: BTreeMap<String, Vec<ContextReferenceCosine>>,
    pub group_medians: BTreeMap<String, f64>,
    pub comparisons: Vec<ContextComparison>,
    pub passed: bool,
}

pub type TargetPrediction = ContextPrediction;

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ContextVerdict {
    pub target_ids: Vec<String>,
    pub requires: Vec<String>,
    pub passed: bool,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ContextAnalysisReport {
    pub schema_version: u32,
    pub fixture_id: String,
    pub fixture_sha256: String,
    pub request_sha256: String,
    pub dimensions: u32,
    pub target_reference_cosine_count: usize,
    pub group_median_count: usize,
    pub predictions: Vec<ContextPrediction>,
    pub verdicts: BTreeMap<String, ContextVerdict>,
}

#[derive(Clone, Debug, Deserialize)]
struct Fixture {
    schema_version: u32,
    fixture_id: String,
    review_status: String,
    inference_authorized: bool,
    sse_execution_contract: ContextExecutionContract,
    target_contract: TargetContract,
    counts: FixtureCounts,
    verdicts: BTreeMap<String, VerdictSpec>,
    source_artifacts: Vec<SourceArtifact>,
    reference_groups: Vec<ReferenceGroup>,
    self_contained_cases: Vec<SelfContainedCase>,
    context_resolution_cases: Vec<ContextResolutionCase>,
    mixed_note_cases: Vec<MixedNoteCase>,
}

#[derive(Clone, Debug, Deserialize)]
struct TargetContract {
    order: String,
    reference_order: String,
    worker_row_order: String,
    self_contained_target: String,
    context_resolution_target: String,
    mixed_note_target: String,
    verdict_rule: String,
    id_derivation: IdDerivation,
}

#[derive(Clone, Debug, Deserialize)]
struct IdDerivation {
    algorithm: String,
    note_domain: String,
    subject_domain: String,
    target_note_fields: Vec<String>,
    target_subject_fields: Vec<String>,
    reference_note_and_subject_fields: Vec<String>,
    note_digest_bytes: usize,
    subject_digest_bytes: usize,
}

#[derive(Clone, Debug, Deserialize)]
struct FixtureCounts {
    constructed_note_instances: usize,
    untouched_mixed_notes: usize,
    target_vectors: usize,
    reference_groups: usize,
    references_per_group: usize,
    reference_vectors: usize,
    total_vectors: usize,
    predeclared_predictions: usize,
}

#[derive(Clone, Debug, Deserialize)]
struct VerdictSpec {
    target_ids: Vec<String>,
    requires: Vec<String>,
}

#[derive(Clone, Debug, Deserialize)]
struct SourceArtifact {
    path: String,
    path_base: String,
    sha256: String,
}

#[derive(Clone, Debug, Deserialize)]
struct ReferenceGroup {
    group_id: String,
    references: Vec<String>,
}

#[derive(Clone, Debug, Deserialize)]
struct MaskFragment {
    text: String,
    occurrence: usize,
}

#[derive(Clone, Debug, Deserialize)]
struct ConstructedVariant {
    fixture_note_id: String,
    text: String,
    mask: Vec<MaskFragment>,
}

#[derive(Clone, Debug, Deserialize)]
struct SelfContainedCase {
    target_group_id: String,
    variants: Vec<ConstructedVariant>,
    alternative_group_ids: Vec<String>,
}

#[derive(Clone, Debug, Deserialize)]
struct ContextVariant {
    fixture_note_id: String,
    text: String,
    mask: Vec<MaskFragment>,
    preferred_group_id: String,
    alternative_group_ids: Vec<String>,
}

#[derive(Clone, Debug, Deserialize)]
struct ContextResolutionCase {
    variants: Vec<ContextVariant>,
}

#[derive(Clone, Debug, Deserialize)]
struct MixedMeaning {
    meaning_id: String,
    mask: Vec<MaskFragment>,
    preferred_group_id: String,
    alternative_group_ids: Vec<String>,
}

#[derive(Clone, Debug, Deserialize)]
struct MixedNoteCase {
    fixture_note_id: String,
    text: String,
    meanings: Vec<MixedMeaning>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct AnalysisManifest {
    schema_version: u32,
    fixture_id: String,
    fixture_sha256: String,
    request_sha256: String,
    compile_manifest_sha256: String,
    files: BTreeMap<String, SseFileIdentity>,
}

struct LoadedFixture {
    fixture: Fixture,
    fixture_sha256: String,
}

struct CompiledPacket {
    manifest: ContextCompileManifest,
    request_bytes: Vec<u8>,
    config_bytes: Vec<u8>,
    manifest_bytes: Vec<u8>,
}

/// Validate and compile the approved fixture into the exact label-free SSE worker packet.
pub fn prepare_sse_context_counterfactual(
    fixture_path: impl AsRef<Path>,
    output_path: impl AsRef<Path>,
) -> Result<ContextCompileManifest> {
    let fixture_path = fixture_path.as_ref();
    let output_path = output_path.as_ref();
    let loaded = load_fixture(fixture_path)?;
    let packet = compile_packet(&loaded)?;
    publish_prepared(output_path, &packet, || {
        revalidate_fixture_and_sources(fixture_path, &loaded)
    })?;
    Ok(packet.manifest)
}

/// Validate a bound worker result, score every declared comparison, and atomically publish it.
pub fn analyze_sse_context_counterfactual(
    fixture_path: impl AsRef<Path>,
    prepared_path: impl AsRef<Path>,
    worker_output_path: impl AsRef<Path>,
    output_path: impl AsRef<Path>,
) -> Result<ContextAnalysisReport> {
    let fixture_path = fixture_path.as_ref();
    let prepared_path = prepared_path.as_ref();
    let worker_output_path = worker_output_path.as_ref();
    let output_path = output_path.as_ref();
    if output_path.exists() {
        return Err(ContextCounterfactualError::ArtifactExists(
            output_path.to_owned(),
        ));
    }

    let loaded = load_fixture(fixture_path)?;
    let packet = compile_packet(&loaded)?;
    validate_prepared(prepared_path, &packet)?;
    let receipt_path = worker_output_path.join(WORKER_RECEIPT_FILE);
    let raw_path = worker_output_path.join(RAW_VECTORS_FILE);
    let receipt_bytes = read_file(&receipt_path)?;
    let raw_bytes = read_file(&raw_path)?;
    let receipt: SseWorkerReceipt = decode_json(&receipt_path, &receipt_bytes)?;
    validate_worker_output(&packet, &receipt, &raw_bytes, &raw_path)?;
    let report = compute_report(&loaded.fixture, &packet, &receipt, &raw_bytes)?;
    let report_bytes = encode_json(Path::new(ANALYSIS_FILE), &report)?;
    let markdown_bytes = render_markdown(&report).into_bytes();
    let manifest = build_analysis_manifest(
        &packet,
        &receipt_bytes,
        &raw_bytes,
        &report_bytes,
        &markdown_bytes,
    );
    let manifest_bytes = encode_json(Path::new(ANALYSIS_MANIFEST_FILE), &manifest)?;
    publish_analysis(
        output_path,
        &receipt_bytes,
        &raw_bytes,
        &report_bytes,
        &markdown_bytes,
        &manifest_bytes,
        || revalidate_fixture_and_sources(fixture_path, &loaded),
    )?;
    Ok(report)
}

/// Revalidate every immutable input and replay a published result without writing.
pub fn verify_sse_context_counterfactual(
    fixture_path: impl AsRef<Path>,
    output_path: impl AsRef<Path>,
) -> Result<ContextAnalysisReport> {
    let fixture_path = fixture_path.as_ref();
    let output_path = output_path.as_ref();
    if !output_path.is_dir() {
        return Err(ContextCounterfactualError::ArtifactMissing(
            output_path.to_owned(),
        ));
    }
    let loaded = load_fixture(fixture_path)?;
    let packet = compile_packet(&loaded)?;
    let manifest_path = output_path.join(ANALYSIS_MANIFEST_FILE);
    let manifest_bytes = read_file(&manifest_path)?;
    let manifest: AnalysisManifest = decode_json(&manifest_path, &manifest_bytes)?;
    let files = read_manifest_files(output_path, &manifest)?;
    let receipt_path = output_path.join(WORKER_RECEIPT_FILE);
    let receipt: SseWorkerReceipt = decode_json(
        &receipt_path,
        files
            .get(WORKER_RECEIPT_FILE)
            .expect("required file checked"),
    )?;
    let raw = files.get(RAW_VECTORS_FILE).expect("required file checked");
    validate_worker_output(&packet, &receipt, raw, &output_path.join(RAW_VECTORS_FILE))?;
    let report = compute_report(&loaded.fixture, &packet, &receipt, raw)?;
    let expected_report = encode_json(Path::new(ANALYSIS_FILE), &report)?;
    let expected_markdown = render_markdown(&report).into_bytes();
    compare_bytes(
        &output_path.join(ANALYSIS_FILE),
        files.get(ANALYSIS_FILE).expect("required file checked"),
        &expected_report,
    )?;
    compare_bytes(
        &output_path.join(MARKDOWN_FILE),
        files.get(MARKDOWN_FILE).expect("required file checked"),
        &expected_markdown,
    )?;
    let expected_manifest = build_analysis_manifest(
        &packet,
        files
            .get(WORKER_RECEIPT_FILE)
            .expect("required file checked"),
        raw,
        &expected_report,
        &expected_markdown,
    );
    compare_bytes(
        &manifest_path,
        &manifest_bytes,
        &encode_json(&manifest_path, &expected_manifest)?,
    )?;
    revalidate_fixture_and_sources(fixture_path, &loaded)?;
    for (name, bytes) in &files {
        compare_bytes(
            &output_path.join(name),
            bytes,
            &read_file(&output_path.join(name))?,
        )?;
    }
    compare_bytes(&manifest_path, &manifest_bytes, &read_file(&manifest_path)?)?;
    Ok(report)
}

fn load_fixture(path: &Path) -> Result<LoadedFixture> {
    let bytes = read_file(path)?;
    let fixture_sha256 = hash_bytes(&bytes);
    if fixture_sha256 != APPROVED_FIXTURE_SHA256 {
        return Err(ContextCounterfactualError::HashMismatch {
            path: path.to_owned(),
            expected: APPROVED_FIXTURE_SHA256.to_owned(),
            actual: fixture_sha256,
        });
    }
    let fixture: Fixture = decode_json(path, &bytes)?;
    if fixture.schema_version != SCHEMA_VERSION
        || fixture.fixture_id != "sse-context-counterfactual-v1"
        || fixture.review_status != "approved"
        || !fixture.inference_authorized
    {
        return invariant("fixture is not the approved, inference-authorized Stage-1 fixture");
    }
    let repository_root = path
        .parent()
        .and_then(Path::parent)
        .ok_or_else(|| {
            ContextCounterfactualError::Invariant("fixture path has no repository root".to_owned())
        })?
        .to_owned();
    validate_contract(&fixture)?;
    validate_sources(&fixture, &repository_root)?;
    Ok(LoadedFixture {
        fixture,
        fixture_sha256: APPROVED_FIXTURE_SHA256.to_owned(),
    })
}

fn revalidate_fixture_and_sources(path: &Path, loaded: &LoadedFixture) -> Result<()> {
    require_hash(path, APPROVED_FIXTURE_SHA256)?;
    let repository_root = path.parent().and_then(Path::parent).ok_or_else(|| {
        ContextCounterfactualError::Invariant("fixture path has no repository root".to_owned())
    })?;
    validate_sources(&loaded.fixture, repository_root)
}

fn validate_contract(fixture: &Fixture) -> Result<()> {
    let execution = &fixture.sse_execution_contract;
    if execution.base_model != "sentence-transformers/sentence-t5-base"
        || !is_sha256(&execution.base_model_artifact_tree_sha256)
        || !is_sha256(&execution.checkpoint_sha256)
        || !is_sha256(&execution.worker_sha256)
        || execution.device != "cpu"
        || execution.note_batch_size == 0
        || execution.dimensions != 768
        || execution.maximum_tokens != 512
        || execution.pooling != "selected-contextual-token-mean-linear-relu-linear-v1"
        || execution.vector_format != "row-major-f32le-v1"
        || execution.base_model_tree_hash_rule != "sorted-relative-path-type-size-content-sha256-v1"
        || execution.cosine
            != "f64-dot-and-f64-norms-over-ordered-raw-f32-coordinates-v1; compare unrounded f64 values"
        || execution.invalid_vector_result
            != "Stage 1 fails if any required vector is missing, zero-norm, or non-finite."
        || !execution
            .container_image
            .rsplit_once("@sha256:")
            .is_some_and(|(name, digest)| !name.is_empty() && is_sha256(digest))
    {
        return invariant("fixture has an unsupported SSE execution contract");
    }
    let contract = &fixture.target_contract;
    if contract.order
        != "self_contained_cases in file order, then context_resolution_cases in file order, then mixed_note_cases in file order"
        || contract.reference_order
            != "reference_groups in file order, then each group's references in file order"
        || contract.worker_row_order
            != "all targets in target order, then all references in reference order"
        || contract.self_contained_target
            != "each variants[] entry is one target; target_id is fixture_note_id; preferred and alternative groups are inherited from its case"
        || contract.context_resolution_target
            != "each variants[] entry is one target; target_id is fixture_note_id; preferred and alternative groups are stored on the variant"
        || contract.mixed_note_target
            != "each meanings[] entry is one target; target_id is meaning_id; preferred and alternative groups are stored on the meaning"
        || contract.verdict_rule
            != "a verdict passes exactly when every listed target prediction and every listed required verdict passes"
    {
        return invariant("fixture target ordering or verdict contract changed");
    }
    let ids = &contract.id_derivation;
    if ids.algorithm != "sha256-domain-and-u64be-length-prefixed-utf8-fields-v1"
        || ids.note_digest_bytes != 32
        || ids.subject_digest_bytes != 8
        || ids.target_note_fields != ["fixture_id", "target", "fixture_note_id"]
        || ids.target_subject_fields != ["fixture_id", "target", "target_id"]
        || ids.reference_note_and_subject_fields
            != [
                "fixture_id",
                "reference",
                "group_id",
                "one-based reference index as ASCII",
            ]
    {
        return invariant("fixture identifier derivation contract changed");
    }
    Ok(())
}

fn validate_sources(fixture: &Fixture, repository_root: &Path) -> Result<()> {
    for source in &fixture.source_artifacts {
        if source.path_base != "repository root" || !is_sha256(&source.sha256) {
            return invariant("fixture source artifact has an invalid binding");
        }
        require_hash(&repository_root.join(&source.path), &source.sha256)?;
    }
    require_hash(
        &repository_root.join(WORKER_SOURCE),
        &fixture.sse_execution_contract.worker_sha256,
    )
}

fn compile_packet(loaded: &LoadedFixture) -> Result<CompiledPacket> {
    let fixture = &loaded.fixture;
    let mut target_notes = Vec::new();
    let mut rows = Vec::new();
    for case in &fixture.self_contained_cases {
        for variant in &case.variants {
            push_single_target(
                fixture,
                &mut target_notes,
                &mut rows,
                &variant.fixture_note_id,
                &variant.fixture_note_id,
                &variant.text,
                &variant.mask,
                &case.target_group_id,
                &case.alternative_group_ids,
            )?;
        }
    }
    for case in &fixture.context_resolution_cases {
        for variant in &case.variants {
            push_single_target(
                fixture,
                &mut target_notes,
                &mut rows,
                &variant.fixture_note_id,
                &variant.fixture_note_id,
                &variant.text,
                &variant.mask,
                &variant.preferred_group_id,
                &variant.alternative_group_ids,
            )?;
        }
    }
    for note in &fixture.mixed_note_cases {
        if note.text.is_empty() || note.meanings.is_empty() {
            return invariant("mixed-note target is empty");
        }
        let note_id = target_note_id(fixture, &note.fixture_note_id);
        let mut subjects = Vec::new();
        for meaning in &note.meanings {
            let subject_id = target_subject_id(fixture, &meaning.meaning_id);
            subjects.push(SseWorkerSubject {
                subject_id: subject_id.clone(),
                byte_spans: resolve_mask(&note.text, &meaning.mask)?,
            });
            rows.push(ContextCompileRow {
                ordinal: rows.len(),
                note_id: note_id.clone(),
                subject_id,
                target_id: Some(meaning.meaning_id.clone()),
                preferred_group_id: meaning.preferred_group_id.clone(),
                alternative_group_ids: meaning.alternative_group_ids.clone(),
                reference_group_id: None,
                reference_index: None,
            });
        }
        target_notes.push(SseWorkerNote {
            note_id,
            text: note.text.clone(),
            subjects,
        });
    }

    let target_count = rows.len();
    let mut reference_notes = Vec::new();
    for group in &fixture.reference_groups {
        for (index, reference) in group.references.iter().enumerate() {
            if reference.is_empty() {
                return invariant("reference text is empty");
            }
            let one_based = (index + 1).to_string();
            let fields = [
                fixture.fixture_id.as_str(),
                "reference",
                group.group_id.as_str(),
                one_based.as_str(),
            ];
            let note_id = derive_id(
                &fixture.target_contract.id_derivation.note_domain,
                &fields,
                fixture.target_contract.id_derivation.note_digest_bytes,
            );
            let subject_id = derive_id(
                &fixture.target_contract.id_derivation.subject_domain,
                &fields,
                fixture.target_contract.id_derivation.subject_digest_bytes,
            );
            reference_notes.push(SseWorkerNote {
                note_id: note_id.clone(),
                text: reference.clone(),
                subjects: vec![SseWorkerSubject {
                    subject_id: subject_id.clone(),
                    byte_spans: vec![[0, reference.len()]],
                }],
            });
            rows.push(ContextCompileRow {
                ordinal: rows.len(),
                note_id,
                subject_id,
                target_id: None,
                preferred_group_id: String::new(),
                alternative_group_ids: Vec::new(),
                reference_group_id: Some(group.group_id.clone()),
                reference_index: Some(index + 1),
            });
        }
    }
    let reference_count = rows.len() - target_count;
    let mut notes = target_notes;
    notes.extend(reference_notes);
    validate_compilation(fixture, &notes, &rows, target_count, reference_count)?;
    let request = SseWorkerInput {
        schema_version: SCHEMA_VERSION,
        proposal_sha256: loaded.fixture_sha256.clone(),
        notes,
    };
    let request_bytes = encode_json(Path::new(WORKER_INPUT_FILE), &request)?;
    let request_sha256 = hash_bytes(&request_bytes);
    let manifest = ContextCompileManifest {
        schema_version: SCHEMA_VERSION,
        fixture_id: fixture.fixture_id.clone(),
        fixture_sha256: loaded.fixture_sha256.clone(),
        request_sha256: request_sha256.clone(),
        worker_sha256: fixture.sse_execution_contract.worker_sha256.clone(),
        note_count: request.notes.len(),
        target_count,
        reference_count,
        execution: fixture.sse_execution_contract.clone(),
        rows,
    };
    let config = json!({
        "schema_version": SCHEMA_VERSION,
        "request_path": "/input/worker-input.json",
        "request_sha256": request_sha256,
        "checkpoint_path": "/checkpoint/subencoder_st5_base.ckpt",
        "checkpoint_sha256": fixture.sse_execution_contract.checkpoint_sha256,
        "base_model_artifact_path": "/model",
        "base_model_artifact_tree_sha256": fixture.sse_execution_contract.base_model_artifact_tree_sha256,
        "model": {
            "base_model": fixture.sse_execution_contract.base_model,
            "dimensions": fixture.sse_execution_contract.dimensions,
            "maximum_tokens": fixture.sse_execution_contract.maximum_tokens,
            "pooling": fixture.sse_execution_contract.pooling,
        },
        "device": fixture.sse_execution_contract.device,
        "container_image": fixture.sse_execution_contract.container_image,
        "note_batch_size": fixture.sse_execution_contract.note_batch_size,
        "output_path": "/output/worker-output"
    });
    let config_bytes = encode_json(Path::new(WORKER_CONFIG_FILE), &config)?;
    let manifest_bytes = encode_json(Path::new(COMPILE_MANIFEST_FILE), &manifest)?;
    Ok(CompiledPacket {
        manifest,
        request_bytes,
        config_bytes,
        manifest_bytes,
    })
}

#[allow(clippy::too_many_arguments)]
fn push_single_target(
    fixture: &Fixture,
    notes: &mut Vec<SseWorkerNote>,
    rows: &mut Vec<ContextCompileRow>,
    fixture_note_id: &str,
    target_id: &str,
    text: &str,
    mask: &[MaskFragment],
    preferred_group_id: &str,
    alternative_group_ids: &[String],
) -> Result<()> {
    if text.is_empty() {
        return invariant("constructed target text is empty");
    }
    let note_id = target_note_id(fixture, fixture_note_id);
    let subject_id = target_subject_id(fixture, target_id);
    notes.push(SseWorkerNote {
        note_id: note_id.clone(),
        text: text.to_owned(),
        subjects: vec![SseWorkerSubject {
            subject_id: subject_id.clone(),
            byte_spans: resolve_mask(text, mask)?,
        }],
    });
    rows.push(ContextCompileRow {
        ordinal: rows.len(),
        note_id,
        subject_id,
        target_id: Some(target_id.to_owned()),
        preferred_group_id: preferred_group_id.to_owned(),
        alternative_group_ids: alternative_group_ids.to_vec(),
        reference_group_id: None,
        reference_index: None,
    });
    Ok(())
}

fn target_note_id(fixture: &Fixture, fixture_note_id: &str) -> String {
    derive_id(
        &fixture.target_contract.id_derivation.note_domain,
        &[fixture.fixture_id.as_str(), "target", fixture_note_id],
        fixture.target_contract.id_derivation.note_digest_bytes,
    )
}

fn target_subject_id(fixture: &Fixture, target_id: &str) -> String {
    derive_id(
        &fixture.target_contract.id_derivation.subject_domain,
        &[fixture.fixture_id.as_str(), "target", target_id],
        fixture.target_contract.id_derivation.subject_digest_bytes,
    )
}

fn derive_id(domain: &str, fields: &[&str], digest_bytes: usize) -> String {
    let mut hash = Sha256::new();
    hash.update(domain.as_bytes());
    for field in fields {
        hash.update((field.len() as u64).to_be_bytes());
        hash.update(field.as_bytes());
    }
    let digest = hash.finalize();
    digest[..digest_bytes]
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect()
}

fn resolve_mask(text: &str, fragments: &[MaskFragment]) -> Result<Vec<[usize; 2]>> {
    if fragments.is_empty() {
        return invariant("target mask is empty");
    }
    let mut spans = Vec::with_capacity(fragments.len());
    for fragment in fragments {
        if fragment.text.is_empty() || fragment.occurrence == 0 {
            return invariant("target mask has an empty fragment or zero occurrence");
        }
        let start = text
            .match_indices(&fragment.text)
            .nth(fragment.occurrence - 1)
            .map(|(start, _)| start)
            .ok_or_else(|| {
                ContextCounterfactualError::Invariant(format!(
                    "mask fragment occurrence {} of `{}` is absent",
                    fragment.occurrence, fragment.text
                ))
            })?;
        spans.push([start, start + fragment.text.len()]);
    }
    if spans.windows(2).any(|pair| pair[0][1] > pair[1][0]) {
        return invariant("target mask fragments overlap or are out of source order");
    }
    Ok(spans)
}

fn validate_compilation(
    fixture: &Fixture,
    notes: &[SseWorkerNote],
    rows: &[ContextCompileRow],
    target_count: usize,
    reference_count: usize,
) -> Result<()> {
    let counts = &fixture.counts;
    let constructed_note_instances = fixture
        .self_contained_cases
        .iter()
        .map(|case| case.variants.len())
        .sum::<usize>()
        + fixture
            .context_resolution_cases
            .iter()
            .map(|case| case.variants.len())
            .sum::<usize>();
    if constructed_note_instances != counts.constructed_note_instances
        || fixture.mixed_note_cases.len() != counts.untouched_mixed_notes
        || notes.len()
            != counts.constructed_note_instances
                + counts.untouched_mixed_notes
                + counts.reference_vectors
        || target_count != counts.target_vectors
        || reference_count != counts.reference_vectors
        || rows.len() != counts.total_vectors
        || counts.predeclared_predictions != target_count
        || fixture.reference_groups.len() != counts.reference_groups
        || fixture
            .reference_groups
            .iter()
            .any(|group| group.references.len() != counts.references_per_group)
    {
        return invariant("compiled packet does not match the fixture's declared counts");
    }
    let group_ids = fixture
        .reference_groups
        .iter()
        .map(|group| group.group_id.as_str())
        .collect::<BTreeSet<_>>();
    if group_ids.len() != fixture.reference_groups.len() {
        return invariant("reference group identifiers are not unique");
    }
    let target_ids = rows[..target_count]
        .iter()
        .map(|row| row.target_id.as_deref().expect("target row"))
        .collect::<BTreeSet<_>>();
    if target_ids.len() != target_count {
        return invariant("target identifiers are not unique");
    }
    for row in &rows[..target_count] {
        if !group_ids.contains(row.preferred_group_id.as_str())
            || row.alternative_group_ids.is_empty()
            || row.alternative_group_ids.iter().any(|group| {
                group == &row.preferred_group_id || !group_ids.contains(group.as_str())
            })
            || row
                .alternative_group_ids
                .iter()
                .collect::<BTreeSet<_>>()
                .len()
                != row.alternative_group_ids.len()
        {
            return invariant(format!(
                "target {} has invalid comparison groups",
                row.target_id.as_deref().unwrap()
            ));
        }
    }
    let note_ids = notes
        .iter()
        .map(|note| note.note_id.as_str())
        .collect::<BTreeSet<_>>();
    let subject_ids = notes
        .iter()
        .flat_map(|note| {
            note.subjects
                .iter()
                .map(|subject| subject.subject_id.as_str())
        })
        .collect::<BTreeSet<_>>();
    if note_ids.len() != notes.len()
        || subject_ids.len() != rows.len()
        || note_ids.iter().any(|id| !is_lower_hex(id, 64))
        || subject_ids.iter().any(|id| !is_lower_hex(id, 16))
    {
        return invariant("derived worker identifiers collide or have the wrong form");
    }
    validate_verdict_graph(fixture, &target_ids)?;
    Ok(())
}

fn validate_verdict_graph(fixture: &Fixture, target_ids: &BTreeSet<&str>) -> Result<()> {
    if !fixture.verdicts.contains_key("overall") {
        return invariant("fixture has no overall verdict");
    }
    let mut directly_declared = BTreeSet::new();
    for (id, verdict) in &fixture.verdicts {
        for target in &verdict.target_ids {
            if !target_ids.contains(target.as_str()) || !directly_declared.insert(target.as_str()) {
                return invariant(format!("verdict {id} has an unknown or duplicate target"));
            }
        }
        if verdict
            .requires
            .iter()
            .any(|required| !fixture.verdicts.contains_key(required))
        {
            return invariant(format!("verdict {id} has an unknown dependency"));
        }
    }
    if directly_declared != *target_ids {
        return invariant("atomic verdict targets do not exactly partition the target rows");
    }
    let mut visiting = BTreeSet::new();
    let mut reached = BTreeSet::new();
    collect_verdict_targets("overall", &fixture.verdicts, &mut visiting, &mut reached)?;
    if reached != *target_ids {
        return invariant("overall verdict does not depend on every target prediction");
    }
    Ok(())
}

fn collect_verdict_targets<'a>(
    id: &'a str,
    specs: &'a BTreeMap<String, VerdictSpec>,
    visiting: &mut BTreeSet<&'a str>,
    reached: &mut BTreeSet<&'a str>,
) -> Result<()> {
    if !visiting.insert(id) {
        return invariant("verdict dependency graph contains a cycle");
    }
    let spec = &specs[id];
    reached.extend(spec.target_ids.iter().map(String::as_str));
    for required in &spec.requires {
        collect_verdict_targets(required, specs, visiting, reached)?;
    }
    visiting.remove(id);
    Ok(())
}

fn validate_prepared(path: &Path, packet: &CompiledPacket) -> Result<()> {
    if !path.is_dir() {
        return Err(ContextCounterfactualError::ArtifactMissing(path.to_owned()));
    }
    compare_bytes(
        &path.join(WORKER_INPUT_FILE),
        &read_file(&path.join(WORKER_INPUT_FILE))?,
        &packet.request_bytes,
    )?;
    compare_bytes(
        &path.join(WORKER_CONFIG_FILE),
        &read_file(&path.join(WORKER_CONFIG_FILE))?,
        &packet.config_bytes,
    )?;
    compare_bytes(
        &path.join(COMPILE_MANIFEST_FILE),
        &read_file(&path.join(COMPILE_MANIFEST_FILE))?,
        &packet.manifest_bytes,
    )
}

fn validate_worker_output(
    packet: &CompiledPacket,
    receipt: &SseWorkerReceipt,
    raw: &[u8],
    raw_path: &Path,
) -> Result<()> {
    let execution = &packet.manifest.execution;
    let raw_identity = receipt.files.get(RAW_VECTORS_FILE).ok_or_else(|| {
        ContextCounterfactualError::Invariant(
            "worker receipt does not identify raw-vectors.f32le".to_owned(),
        )
    })?;
    if receipt.schema_version != SCHEMA_VERSION
        || receipt.proposal_sha256 != packet.manifest.fixture_sha256
        || receipt.request_sha256 != packet.manifest.request_sha256
        || receipt.checkpoint_sha256 != execution.checkpoint_sha256
        || receipt.base_model_artifact_tree_sha256 != execution.base_model_artifact_tree_sha256
        || receipt.tree_hash_rule != execution.base_model_tree_hash_rule
        || receipt.model.base_model != execution.base_model
        || receipt.model.dimensions != execution.dimensions
        || receipt.model.maximum_tokens != execution.maximum_tokens
        || receipt.model.pooling != execution.pooling
        || !receipt.runtime.is_object()
        || receipt.device != execution.device
        || receipt.container_image != execution.container_image
        || receipt.note_batch_size != execution.note_batch_size
        || receipt.vector_format != execution.vector_format
        || receipt.dimensions != execution.dimensions
        || receipt.row_count != packet.manifest.rows.len()
        || receipt.rows.len() != packet.manifest.rows.len()
        || receipt.files.len() != 1
    {
        return invariant("worker receipt has the wrong pinned execution or input contract");
    }
    if receipt.runtime.get("worker_sha256").and_then(Value::as_str)
        != Some(execution.worker_sha256.as_str())
    {
        return invariant("worker receipt reports a different worker source hash");
    }
    let expected_bytes = packet
        .manifest
        .rows
        .len()
        .checked_mul(execution.dimensions as usize)
        .and_then(|count| count.checked_mul(size_of::<f32>()))
        .ok_or_else(|| {
            ContextCounterfactualError::Invariant("worker vector byte count overflowed".to_owned())
        })?;
    let actual_hash = hash_bytes(raw);
    if raw.len() != expected_bytes
        || raw_identity.bytes != expected_bytes as u64
        || raw_identity.sha256 != actual_hash
    {
        return Err(ContextCounterfactualError::HashMismatch {
            path: raw_path.to_owned(),
            expected: raw_identity.sha256.clone(),
            actual: actual_hash,
        });
    }
    let mut token_counts = BTreeMap::new();
    for (ordinal, (receipt_row, expected)) in
        receipt.rows.iter().zip(&packet.manifest.rows).enumerate()
    {
        if receipt_row.ordinal != ordinal
            || receipt_row.note_id != expected.note_id
            || receipt_row.subject_id != expected.subject_id
            || receipt_row.token_count == 0
            || receipt_row.selected_token_indices.is_empty()
            || receipt_row
                .selected_token_indices
                .iter()
                .any(|index| *index >= receipt_row.token_count)
            || receipt_row
                .selected_token_indices
                .windows(2)
                .any(|pair| pair[0] >= pair[1])
        {
            return invariant(format!(
                "worker row {ordinal} has an invalid identity or token selection"
            ));
        }
        match token_counts.insert(receipt_row.note_id.as_str(), receipt_row.token_count) {
            Some(previous) if previous != receipt_row.token_count => {
                return invariant(format!(
                    "worker rows for note {} disagree on token count",
                    receipt_row.note_id
                ));
            }
            _ => {}
        }
    }
    Ok(())
}

fn compute_report(
    fixture: &Fixture,
    packet: &CompiledPacket,
    receipt: &SseWorkerReceipt,
    raw_bytes: &[u8],
) -> Result<ContextAnalysisReport> {
    let dimensions = receipt.dimensions as usize;
    let raw = raw_bytes
        .chunks_exact(size_of::<f32>())
        .map(|bytes| f32::from_le_bytes(bytes.try_into().expect("f32 width")))
        .collect::<Vec<_>>();
    if raw.iter().any(|value| !value.is_finite()) {
        return invariant("worker returned a non-finite vector coordinate");
    }
    let mut norms = Vec::with_capacity(packet.manifest.rows.len());
    for vector in raw.chunks_exact(dimensions) {
        let norm = vector
            .iter()
            .map(|value| f64::from(*value).powi(2))
            .sum::<f64>()
            .sqrt();
        if norm == 0.0 || !norm.is_finite() {
            return invariant("worker returned a zero-norm or non-finite vector");
        }
        norms.push(norm);
    }
    let reference_rows = &packet.manifest.rows[packet.manifest.target_count..];
    let mut references_by_group: BTreeMap<&str, Vec<usize>> = BTreeMap::new();
    for row in reference_rows {
        references_by_group
            .entry(row.reference_group_id.as_deref().expect("reference row"))
            .or_default()
            .push(row.ordinal);
    }
    let mut predictions = Vec::with_capacity(packet.manifest.target_count);
    let mut cosine_count = 0;
    let mut median_count = 0;
    for row in &packet.manifest.rows[..packet.manifest.target_count] {
        let mut reference_cosines = BTreeMap::new();
        let mut group_medians = BTreeMap::new();
        for (group_id, reference_ordinals) in &references_by_group {
            let mut scores = Vec::with_capacity(reference_ordinals.len());
            for &reference_ordinal in reference_ordinals {
                scores.push(ContextReferenceCosine {
                    reference_index: packet.manifest.rows[reference_ordinal]
                        .reference_index
                        .expect("reference row"),
                    reference_ordinal,
                    reference_note_id: packet.manifest.rows[reference_ordinal].note_id.clone(),
                    reference_subject_id: packet.manifest.rows[reference_ordinal]
                        .subject_id
                        .clone(),
                    cosine: cosine_rows(&raw, dimensions, &norms, row.ordinal, reference_ordinal)?,
                });
                cosine_count += 1;
            }
            let mut ordered = scores.iter().map(|score| score.cosine).collect::<Vec<_>>();
            ordered.sort_by(f64::total_cmp);
            if ordered.len() % 2 != 1 {
                return invariant(format!(
                    "reference group {group_id} does not have an odd size"
                ));
            }
            let median = ordered[ordered.len() / 2];
            reference_cosines.insert((*group_id).to_owned(), scores);
            group_medians.insert((*group_id).to_owned(), median);
            median_count += 1;
        }
        let preferred_median = *group_medians.get(&row.preferred_group_id).ok_or_else(|| {
            ContextCounterfactualError::Invariant(format!(
                "target {} has no preferred group",
                row.target_id.as_deref().unwrap()
            ))
        })?;
        let comparisons = row
            .alternative_group_ids
            .iter()
            .map(|alternative| {
                let alternative_median = group_medians[alternative];
                ContextComparison {
                    alternative_group_id: alternative.clone(),
                    preferred_median,
                    alternative_median,
                    passed: preferred_median > alternative_median,
                }
            })
            .collect::<Vec<_>>();
        predictions.push(ContextPrediction {
            target_id: row.target_id.clone().expect("target row"),
            target_ordinal: row.ordinal,
            preferred_group_id: row.preferred_group_id.clone(),
            preferred_median,
            reference_cosines,
            group_medians,
            passed: comparisons.iter().all(|comparison| comparison.passed),
            comparisons,
        });
    }
    let expected_cosines = packet.manifest.target_count * packet.manifest.reference_count;
    let expected_medians = packet.manifest.target_count * references_by_group.len();
    if cosine_count != expected_cosines || median_count != expected_medians {
        return invariant("analysis omitted a target-to-reference cosine or group median");
    }
    let prediction_results = predictions
        .iter()
        .map(|prediction| (prediction.target_id.as_str(), prediction.passed))
        .collect::<BTreeMap<_, _>>();
    let mut verdicts = BTreeMap::new();
    let mut visiting = BTreeSet::new();
    evaluate_verdict(
        "overall",
        &fixture.verdicts,
        &prediction_results,
        &mut verdicts,
        &mut visiting,
    )?;
    if verdicts.len() != fixture.verdicts.len() {
        return invariant("overall verdict does not reach every declared verdict");
    }
    Ok(ContextAnalysisReport {
        schema_version: SCHEMA_VERSION,
        fixture_id: fixture.fixture_id.clone(),
        fixture_sha256: packet.manifest.fixture_sha256.clone(),
        request_sha256: packet.manifest.request_sha256.clone(),
        dimensions: receipt.dimensions,
        target_reference_cosine_count: cosine_count,
        group_median_count: median_count,
        predictions,
        verdicts,
    })
}

fn cosine_rows(
    raw: &[f32],
    dimensions: usize,
    norms: &[f64],
    left: usize,
    right: usize,
) -> Result<f64> {
    let left_row = &raw[left * dimensions..(left + 1) * dimensions];
    let right_row = &raw[right * dimensions..(right + 1) * dimensions];
    let dot = left_row
        .iter()
        .zip(right_row)
        .map(|(left, right)| f64::from(*left) * f64::from(*right))
        .sum::<f64>();
    let cosine = dot / (norms[left] * norms[right]);
    if !cosine.is_finite() {
        return invariant("cosine calculation produced a non-finite value");
    }
    Ok(cosine)
}

fn evaluate_verdict<'a>(
    id: &'a str,
    specs: &'a BTreeMap<String, VerdictSpec>,
    predictions: &BTreeMap<&str, bool>,
    output: &mut BTreeMap<String, ContextVerdict>,
    visiting: &mut BTreeSet<&'a str>,
) -> Result<bool> {
    if let Some(verdict) = output.get(id) {
        return Ok(verdict.passed);
    }
    if !visiting.insert(id) {
        return invariant("verdict dependency graph contains a cycle");
    }
    let spec = specs.get(id).ok_or_else(|| {
        ContextCounterfactualError::Invariant(format!("unknown verdict dependency {id}"))
    })?;
    let mut passed = true;
    for target in &spec.target_ids {
        passed &= *predictions.get(target.as_str()).ok_or_else(|| {
            ContextCounterfactualError::Invariant(format!(
                "verdict {id} names unknown target {target}"
            ))
        })?;
    }
    for required in &spec.requires {
        passed &= evaluate_verdict(required, specs, predictions, output, visiting)?;
    }
    visiting.remove(id);
    output.insert(
        id.to_owned(),
        ContextVerdict {
            target_ids: spec.target_ids.clone(),
            requires: spec.requires.clone(),
            passed,
        },
    );
    Ok(passed)
}

fn publish_prepared<F>(output: &Path, packet: &CompiledPacket, revalidate: F) -> Result<()>
where
    F: FnOnce() -> Result<()>,
{
    publish_directory(
        output,
        &[
            (WORKER_INPUT_FILE, packet.request_bytes.as_slice()),
            (WORKER_CONFIG_FILE, packet.config_bytes.as_slice()),
            (COMPILE_MANIFEST_FILE, packet.manifest_bytes.as_slice()),
        ],
        revalidate,
    )
}

fn publish_analysis<F>(
    output: &Path,
    receipt: &[u8],
    raw: &[u8],
    analysis: &[u8],
    markdown: &[u8],
    manifest: &[u8],
    revalidate: F,
) -> Result<()>
where
    F: FnOnce() -> Result<()>,
{
    publish_directory(
        output,
        &[
            (WORKER_RECEIPT_FILE, receipt),
            (RAW_VECTORS_FILE, raw),
            (ANALYSIS_FILE, analysis),
            (MARKDOWN_FILE, markdown),
            (ANALYSIS_MANIFEST_FILE, manifest),
        ],
        revalidate,
    )
}

fn publish_directory<F>(output: &Path, files: &[(&str, &[u8])], revalidate: F) -> Result<()>
where
    F: FnOnce() -> Result<()>,
{
    if output.exists() {
        return Err(ContextCounterfactualError::ArtifactExists(
            output.to_owned(),
        ));
    }
    let parent = output.parent().unwrap_or_else(|| Path::new("."));
    fs::create_dir_all(parent).map_err(|source| io_error("create directory", parent, source))?;
    let stage = stage_path(output)?;
    fs::create_dir(&stage).map_err(|source| {
        if source.kind() == io::ErrorKind::AlreadyExists {
            ContextCounterfactualError::ArtifactExists(stage.clone())
        } else {
            io_error("create staging directory", &stage, source)
        }
    })?;
    let result = (|| {
        for (name, bytes) in files {
            write_new_file(&stage.join(name), bytes)?;
        }
        sync_directory(&stage)?;
        revalidate()?;
        rename_no_replace(&stage, output)?;
        sync_directory(parent)
    })();
    if result.is_err() {
        let _ = fs::remove_dir_all(&stage);
    }
    result
}

fn build_analysis_manifest(
    packet: &CompiledPacket,
    receipt: &[u8],
    raw: &[u8],
    analysis: &[u8],
    markdown: &[u8],
) -> AnalysisManifest {
    AnalysisManifest {
        schema_version: SCHEMA_VERSION,
        fixture_id: packet.manifest.fixture_id.clone(),
        fixture_sha256: packet.manifest.fixture_sha256.clone(),
        request_sha256: packet.manifest.request_sha256.clone(),
        compile_manifest_sha256: hash_bytes(&packet.manifest_bytes),
        files: BTreeMap::from([
            (WORKER_RECEIPT_FILE.to_owned(), identity(receipt)),
            (RAW_VECTORS_FILE.to_owned(), identity(raw)),
            (ANALYSIS_FILE.to_owned(), identity(analysis)),
            (MARKDOWN_FILE.to_owned(), identity(markdown)),
        ]),
    }
}

fn read_manifest_files(
    output: &Path,
    manifest: &AnalysisManifest,
) -> Result<BTreeMap<String, Vec<u8>>> {
    let required = BTreeSet::from([
        WORKER_RECEIPT_FILE,
        RAW_VECTORS_FILE,
        ANALYSIS_FILE,
        MARKDOWN_FILE,
    ]);
    if manifest.schema_version != SCHEMA_VERSION
        || manifest
            .files
            .keys()
            .map(String::as_str)
            .collect::<BTreeSet<_>>()
            != required
    {
        return invariant("analysis manifest has the wrong schema or file set");
    }
    let mut files = BTreeMap::new();
    for (name, expected) in &manifest.files {
        let path = output.join(name);
        let bytes = read_file(&path)?;
        let actual = identity(&bytes);
        if &actual != expected {
            return Err(ContextCounterfactualError::HashMismatch {
                path,
                expected: expected.sha256.clone(),
                actual: actual.sha256,
            });
        }
        files.insert(name.clone(), bytes);
    }
    Ok(files)
}

fn render_markdown(report: &ContextAnalysisReport) -> String {
    let mut output = format!(
        "# SSE context counterfactual\n\nOverall: **{}**\n\n| Target | Preferred group | Preferred median | Result |\n|---|---|---:|---|\n",
        if report.verdicts["overall"].passed {
            "PASS"
        } else {
            "FAIL"
        }
    );
    for prediction in &report.predictions {
        output.push_str(&format!(
            "| {} | {} | {:.9} | {} |\n",
            prediction.target_id,
            prediction.preferred_group_id,
            prediction.preferred_median,
            if prediction.passed { "PASS" } else { "FAIL" }
        ));
    }
    output
}

fn identity(bytes: &[u8]) -> SseFileIdentity {
    SseFileIdentity {
        bytes: bytes.len() as u64,
        sha256: hash_bytes(bytes),
    }
}

fn read_file(path: &Path) -> Result<Vec<u8>> {
    let mut file = File::open(path).map_err(|source| {
        if source.kind() == io::ErrorKind::NotFound {
            ContextCounterfactualError::ArtifactMissing(path.to_owned())
        } else {
            io_error("open", path, source)
        }
    })?;
    let mut bytes = Vec::new();
    file.read_to_end(&mut bytes)
        .map_err(|source| io_error("read", path, source))?;
    Ok(bytes)
}

fn write_new_file(path: &Path, bytes: &[u8]) -> Result<()> {
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(path)
        .map_err(|source| io_error("create", path, source))?;
    file.write_all(bytes)
        .map_err(|source| io_error("write", path, source))?;
    file.sync_all()
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

fn require_hash(path: &Path, expected: &str) -> Result<()> {
    let actual = hash_bytes(&read_file(path)?);
    if actual == expected {
        Ok(())
    } else {
        Err(ContextCounterfactualError::HashMismatch {
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
    is_lower_hex(value, 64)
}

fn is_lower_hex(value: &str, length: usize) -> bool {
    value.len() == length
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

fn compare_bytes(path: &Path, actual: &[u8], expected: &[u8]) -> Result<()> {
    if actual == expected {
        Ok(())
    } else {
        Err(ContextCounterfactualError::ReplayMismatch(path.to_owned()))
    }
}

fn stage_path(output: &Path) -> Result<PathBuf> {
    let name = output
        .file_name()
        .and_then(|name| name.to_str())
        .ok_or_else(|| {
            ContextCounterfactualError::Invariant(format!(
                "output path `{}` has no UTF-8 filename",
                output.display()
            ))
        })?;
    Ok(output.with_file_name(format!(".{name}.stage-{}", std::process::id())))
}

fn rename_no_replace(source: &Path, destination: &Path) -> Result<()> {
    let destination_path = destination.to_owned();
    let source = CString::new(source.as_os_str().as_bytes()).map_err(|_| {
        ContextCounterfactualError::Invariant("staging path contains a null byte".to_owned())
    })?;
    let destination = CString::new(destination.as_os_str().as_bytes()).map_err(|_| {
        ContextCounterfactualError::Invariant("destination path contains a null byte".to_owned())
    })?;
    // SAFETY: both path buffers are live, null terminated, and valid for this call.
    let result = unsafe {
        libc::renameat2(
            libc::AT_FDCWD,
            source.as_ptr(),
            libc::AT_FDCWD,
            destination.as_ptr(),
            libc::RENAME_NOREPLACE,
        )
    };
    if result == 0 {
        return Ok(());
    }
    let error = io::Error::last_os_error();
    if error.kind() == io::ErrorKind::AlreadyExists {
        Err(ContextCounterfactualError::ArtifactExists(destination_path))
    } else {
        Err(ContextCounterfactualError::Io {
            operation: "publish",
            path: destination_path,
            source: error,
        })
    }
}

fn sync_directory(path: &Path) -> Result<()> {
    File::open(path)
        .and_then(|directory| directory.sync_all())
        .map_err(|source| io_error("sync directory", path, source))
}

fn invariant<T>(message: impl Into<String>) -> Result<T> {
    Err(ContextCounterfactualError::Invariant(message.into()))
}

fn io_error(
    operation: &'static str,
    path: impl AsRef<Path>,
    source: io::Error,
) -> ContextCounterfactualError {
    ContextCounterfactualError::Io {
        operation,
        path: path.as_ref().to_owned(),
        source,
    }
}

fn json_error(
    operation: &'static str,
    path: impl AsRef<Path>,
    source: serde_json::Error,
) -> ContextCounterfactualError {
    ContextCounterfactualError::Json {
        operation,
        path: path.as_ref().to_owned(),
        source,
    }
}
