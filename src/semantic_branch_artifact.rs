//! Blind, auditable input preparation for the semantic-branch diagnostic.

use std::collections::{BTreeMap, BTreeSet};
use std::fs::{self, File, OpenOptions};
use std::io::{self, BufRead, BufReader, BufWriter, Read, Write};
use std::path::{Path, PathBuf};

use nostrdb::Transaction;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use thiserror::Error;

use crate::fp32_oracle::{Fp32Candidate, SimilarNotesResponse};
use crate::representation::EventId;
use crate::semantic_branch_geometry::{BranchLabel, BranchLabelSet};
use crate::snapshot::{Validation, open_existing_ndb};

const ARTIFACT_SCHEMA_VERSION: u32 = 1;
const DIAGNOSTIC_ID: &str = "crec-110-semantic-branch-geometry-v1";
const CANDIDATE_DEPTH: usize = 1_024;
const QUARTILE_WIDTH: usize = 256;
const SAMPLES_PER_QUARTILE: usize = 40;
const SAMPLE_COUNT: usize = SAMPLES_PER_QUARTILE * 4;
pub const LABELER_A_PACKET_FILE: &str = "blind-labeler-a.jsonl";
pub const LABELER_B_PACKET_FILE: &str = "blind-labeler-b.jsonl";
pub const PRIVATE_KEY_FILE: &str = "private-key.jsonl";
pub const LABELER_A_LABELS_FILE: &str = "labels-a.jsonl";
pub const LABELER_B_LABELS_FILE: &str = "labels-b.jsonl";
const RUBRIC_FILE: &str = "branch-rubric.json";
const PREPARE_MANIFEST_FILE: &str = "prepare-manifest.json";
const LABEL_SEAL_FILE: &str = "label-seal.json";
const SELECTION_POLICY: &str = "smallest-domain-sha256-event-id-40-per-rank-quartile-v1";

pub type Result<T> = std::result::Result<T, SemanticBranchArtifactError>;

#[derive(Debug, Error)]
pub enum SemanticBranchArtifactError {
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
    #[error("artifact already exists at `{0}`")]
    ArtifactExists(PathBuf),
    #[error("artifact is missing at `{0}`")]
    ArtifactMissing(PathBuf),
    #[error("label seal is missing at `{0}`")]
    MissingLabelSeal(PathBuf),
    #[error("hash mismatch for `{path}`: expected {expected}, got {actual}")]
    HashMismatch {
        path: PathBuf,
        expected: String,
        actual: String,
    },
    #[error("NostrDB operation failed: {0}")]
    Ndb(String),
    #[error("semantic-branch artifact invariant failed: {0}")]
    Invariant(String),
    #[error(transparent)]
    Snapshot(#[from] crate::snapshot::Error),
    #[error(transparent)]
    Geometry(#[from] crate::semantic_branch_geometry::BranchGeometryError),
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SemanticBranchPrepareConfig {
    pub cached_response_path: PathBuf,
    pub expected_cached_response_sha256: String,
    pub corpus_path: PathBuf,
    pub expected_corpus_data_sha256: String,
    pub output_path: PathBuf,
    pub source_event_id: EventId,
    pub representation_version: String,
    pub represented_rows: u64,
}

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(deny_unknown_fields)]
struct ResponseCacheKey {
    representation_version: String,
    source_event_id: EventId,
    candidate_depth: usize,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct CachedResponseEnvelope {
    key: ResponseCacheKey,
    response: SimilarNotesResponse,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct BlindRecord {
    record_id: String,
    content: String,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct PrivateKeyRecord {
    candidate_id: String,
    labeler_a_record_id: String,
    labeler_b_record_id: String,
    event_id: String,
    rank: u32,
    rank_quartile: u8,
    cached_cosine_score: f64,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct PrepareManifest {
    schema_version: u32,
    diagnostic_id: String,
    source_event_id: String,
    representation_version: String,
    represented_rows: u64,
    candidate_depth: usize,
    selection_policy: String,
    samples_per_quartile: usize,
    sample_count: usize,
    cached_response_path: PathBuf,
    cached_response_sha256: String,
    corpus_data_path: PathBuf,
    corpus_data_sha256: String,
    labeler_a_packet_sha256: String,
    labeler_b_packet_sha256: String,
    private_key_sha256: String,
    rubric_sha256: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct LabelSeal {
    schema_version: u32,
    diagnostic_id: String,
    prepare_manifest_sha256: String,
    labeler_a_packet_sha256: String,
    labeler_b_packet_sha256: String,
    private_key_sha256: String,
    rubric_sha256: String,
    labeler_a_labels_sha256: String,
    labeler_b_labels_sha256: String,
    record_count: usize,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct BranchRubric {
    schema_version: u32,
    diagnostic_id: String,
    instruction: String,
    rules: Vec<String>,
    definitions: BTreeMap<crate::semantic_branch_geometry::Theme, String>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SemanticBranchLabelRecord {
    pub record_id: String,
    pub label: BranchLabel,
}

#[derive(Clone, Debug, PartialEq)]
pub struct SealedBranchRecord {
    candidate_id: String,
    event_id: EventId,
    rank: u32,
    rank_quartile: u8,
    cached_cosine_score: f64,
}

impl SealedBranchRecord {
    pub fn candidate_id(&self) -> &str {
        &self.candidate_id
    }

    pub const fn event_id(&self) -> EventId {
        self.event_id
    }

    pub const fn rank(&self) -> u32 {
        self.rank
    }

    pub const fn rank_quartile(&self) -> u8 {
        self.rank_quartile
    }

    pub const fn cached_cosine_score(&self) -> f64 {
        self.cached_cosine_score
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct SealedSemanticBranchInput {
    source_event_id: EventId,
    representation_version: String,
    represented_rows: u64,
    records: Vec<SealedBranchRecord>,
    label_sets: [BranchLabelSet; 2],
}

impl SealedSemanticBranchInput {
    pub const fn source_event_id(&self) -> EventId {
        self.source_event_id
    }

    pub fn representation_version(&self) -> &str {
        &self.representation_version
    }

    pub const fn represented_rows(&self) -> u64 {
        self.represented_rows
    }

    pub fn records(&self) -> &[SealedBranchRecord] {
        &self.records
    }

    pub fn label_sets(&self) -> &[BranchLabelSet; 2] {
        &self.label_sets
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct SampledBranchCandidate {
    pub event_id: EventId,
    pub rank: usize,
    pub rank_quartile: u8,
    pub cached_cosine_score: f32,
}

pub fn select_semantic_branch_candidates(
    response: &SimilarNotesResponse,
    source_event_id: EventId,
) -> Result<Vec<SampledBranchCandidate>> {
    validate_complete_response(response, source_event_id)?;
    let mut selected = Vec::with_capacity(SAMPLES_PER_QUARTILE * 4);
    for quartile in 0..4 {
        let start = quartile * QUARTILE_WIDTH;
        let mut candidates = response.candidates[start..start + QUARTILE_WIDTH]
            .iter()
            .map(|candidate| (sample_key(&candidate.event_id), candidate))
            .collect::<Vec<_>>();
        candidates.sort_unstable_by(|left, right| {
            left.0
                .cmp(&right.0)
                .then_with(|| left.1.event_id.cmp(&right.1.event_id))
        });
        selected.extend(
            candidates
                .into_iter()
                .take(SAMPLES_PER_QUARTILE)
                .map(|(_, candidate)| sampled_candidate(candidate)),
        );
    }
    Ok(selected)
}

pub fn read_cached_semantic_branch_response(
    path: impl AsRef<Path>,
    expected_sha256: &str,
    source_event_id: EventId,
    representation_version: &str,
    represented_rows: u64,
) -> Result<SimilarNotesResponse> {
    let path = path.as_ref();
    require_hash(path, expected_sha256)?;
    let envelope: CachedResponseEnvelope = read_json(path)?;
    let expected_key = ResponseCacheKey {
        representation_version: representation_version.to_owned(),
        source_event_id,
        candidate_depth: CANDIDATE_DEPTH,
    };
    if envelope.key != expected_key {
        return Err(SemanticBranchArtifactError::Invariant(
            "cached Oracle response violates its immutable key".to_owned(),
        ));
    }
    if envelope.response.representation_version != representation_version
        || envelope.response.represented_rows != represented_rows
        || envelope.response.total_rows != represented_rows
    {
        return Err(SemanticBranchArtifactError::Invariant(
            "cached Oracle response violates its representation identity".to_owned(),
        ));
    }
    validate_complete_response(&envelope.response, source_event_id)?;
    Ok(envelope.response)
}

pub fn prepare_semantic_branch_artifact(config: &SemanticBranchPrepareConfig) -> Result<PathBuf> {
    validate_prepare_config(config)?;
    if config.output_path.exists() {
        return Err(SemanticBranchArtifactError::ArtifactExists(
            config.output_path.clone(),
        ));
    }
    let corpus_data_path = config.corpus_path.join("data.mdb");
    require_hash(&corpus_data_path, &config.expected_corpus_data_sha256)?;
    let response = read_cached_semantic_branch_response(
        &config.cached_response_path,
        &config.expected_cached_response_sha256,
        config.source_event_id,
        &config.representation_version,
        config.represented_rows,
    )?;
    let mut sampled = select_semantic_branch_candidates(&response, config.source_event_id)?;
    sampled.sort_unstable_by_key(|candidate| candidate.rank);
    let contents = load_sampled_contents(&config.corpus_path, &sampled)?;
    require_hash(&corpus_data_path, &config.expected_corpus_data_sha256)?;
    require_hash(
        &config.cached_response_path,
        &config.expected_cached_response_sha256,
    )?;

    let (packet_a, packet_b, key) = build_blind_packets(&sampled, &contents)?;
    let stage = temporary_sibling(&config.output_path);
    if stage.exists() {
        return Err(SemanticBranchArtifactError::ArtifactExists(stage));
    }
    fs::create_dir_all(&stage).map_err(|source| io_error("create directory", &stage, source))?;
    let write_result = write_prepared_artifact(
        config,
        &corpus_data_path,
        &packet_a,
        &packet_b,
        &key,
        &stage,
    );
    if let Err(error) = write_result {
        let _ = fs::remove_dir_all(&stage);
        return Err(error);
    }
    require_hash(&corpus_data_path, &config.expected_corpus_data_sha256)?;
    require_hash(
        &config.cached_response_path,
        &config.expected_cached_response_sha256,
    )?;
    fs::rename(&stage, &config.output_path)
        .map_err(|source| io_error("publish", &config.output_path, source))?;
    sync_parent(&config.output_path)?;
    Ok(config.output_path.clone())
}

pub fn seal_semantic_branch_labels(run_path: impl AsRef<Path>) -> Result<PathBuf> {
    let run_path = run_path.as_ref();
    let seal_path = run_path.join(LABEL_SEAL_FILE);
    if seal_path.exists() {
        return Err(SemanticBranchArtifactError::ArtifactExists(seal_path));
    }
    let (manifest_path, manifest) = read_verified_prepare_manifest(run_path)?;
    verify_source_artifacts(&manifest)?;
    let packet_a_path = run_path.join(LABELER_A_PACKET_FILE);
    let packet_b_path = run_path.join(LABELER_B_PACKET_FILE);
    let key_path = run_path.join(PRIVATE_KEY_FILE);
    let rubric_path = run_path.join(RUBRIC_FILE);
    require_hash(&packet_a_path, &manifest.labeler_a_packet_sha256)?;
    require_hash(&packet_b_path, &manifest.labeler_b_packet_sha256)?;
    require_hash(&key_path, &manifest.private_key_sha256)?;
    require_hash(&rubric_path, &manifest.rubric_sha256)?;
    let packet_a = read_json_lines::<BlindRecord>(&packet_a_path)?;
    let packet_b = read_json_lines::<BlindRecord>(&packet_b_path)?;
    let key = read_json_lines::<PrivateKeyRecord>(&key_path)?;
    validate_prepared_records(&packet_a, &packet_b, &key)?;
    let labels_a_path = run_path.join(LABELER_A_LABELS_FILE);
    let labels_b_path = run_path.join(LABELER_B_LABELS_FILE);
    validate_label_file(&labels_a_path, &packet_a)?;
    validate_label_file(&labels_b_path, &packet_b)?;

    let seal = LabelSeal {
        schema_version: ARTIFACT_SCHEMA_VERSION,
        diagnostic_id: DIAGNOSTIC_ID.to_owned(),
        prepare_manifest_sha256: hash_file(&manifest_path)?,
        labeler_a_packet_sha256: hash_file(&packet_a_path)?,
        labeler_b_packet_sha256: hash_file(&packet_b_path)?,
        private_key_sha256: hash_file(&key_path)?,
        rubric_sha256: hash_file(&rubric_path)?,
        labeler_a_labels_sha256: hash_file(&labels_a_path)?,
        labeler_b_labels_sha256: hash_file(&labels_b_path)?,
        record_count: key.len(),
    };
    write_json_exclusive(&seal_path, &seal)?;
    Ok(seal_path)
}

pub fn open_sealed_semantic_branch_input(
    run_path: impl AsRef<Path>,
) -> Result<SealedSemanticBranchInput> {
    let run_path = run_path.as_ref();
    let seal_path = run_path.join(LABEL_SEAL_FILE);
    if !seal_path.is_file() {
        return Err(SemanticBranchArtifactError::MissingLabelSeal(seal_path));
    }
    let (manifest_path, manifest) = read_verified_prepare_manifest(run_path)?;
    let seal: LabelSeal = read_json(&seal_path)?;
    validate_seal(run_path, &manifest_path, &manifest, &seal)?;
    verify_source_artifacts(&manifest)?;
    let response = read_cached_semantic_branch_response(
        &manifest.cached_response_path,
        &manifest.cached_response_sha256,
        decode_event_id(&manifest.source_event_id)?,
        &manifest.representation_version,
        manifest.represented_rows,
    )?;
    let mut selected =
        select_semantic_branch_candidates(&response, decode_event_id(&manifest.source_event_id)?)?;
    selected.sort_unstable_by_key(|candidate| candidate.rank);

    let packet_a = read_json_lines::<BlindRecord>(&run_path.join(LABELER_A_PACKET_FILE))?;
    let packet_b = read_json_lines::<BlindRecord>(&run_path.join(LABELER_B_PACKET_FILE))?;
    let key = read_json_lines::<PrivateKeyRecord>(&run_path.join(PRIVATE_KEY_FILE))?;
    validate_prepared_records(&packet_a, &packet_b, &key)?;
    validate_key_against_selection(&key, &selected)?;
    let labels_a = load_labels(&run_path.join(LABELER_A_LABELS_FILE), &packet_a)?;
    let labels_b = load_labels(&run_path.join(LABELER_B_LABELS_FILE), &packet_b)?;

    let by_a_record = labels_a;
    let by_b_record = labels_b;
    let mut first_labels = BTreeMap::new();
    let mut second_labels = BTreeMap::new();
    let mut records = Vec::with_capacity(key.len());
    for record in key {
        first_labels.insert(
            record.candidate_id.clone(),
            by_a_record[&record.labeler_a_record_id].clone(),
        );
        second_labels.insert(
            record.candidate_id.clone(),
            by_b_record[&record.labeler_b_record_id].clone(),
        );
        records.push(SealedBranchRecord {
            candidate_id: record.candidate_id,
            event_id: decode_event_id(&record.event_id)?,
            rank: record.rank,
            rank_quartile: record.rank_quartile,
            cached_cosine_score: record.cached_cosine_score,
        });
    }
    records.sort_unstable_by_key(|record| record.rank);
    Ok(SealedSemanticBranchInput {
        source_event_id: decode_event_id(&manifest.source_event_id)?,
        representation_version: manifest.representation_version,
        represented_rows: manifest.represented_rows,
        records,
        label_sets: [
            BranchLabelSet::new("labeler-a", first_labels)?,
            BranchLabelSet::new("labeler-b", second_labels)?,
        ],
    })
}

fn validate_complete_response(
    response: &SimilarNotesResponse,
    source_event_id: EventId,
) -> Result<()> {
    if !response.complete
        || response.total_rows == 0
        || response.represented_rows != response.total_rows
        || response.candidates.len() != CANDIDATE_DEPTH
    {
        return Err(SemanticBranchArtifactError::Invariant(
            "cached Oracle response is not a complete top-1024 response".to_owned(),
        ));
    }
    let mut event_ids = BTreeSet::new();
    for (index, candidate) in response.candidates.iter().enumerate() {
        if candidate.rank != index + 1
            || candidate.event_id == source_event_id
            || !candidate.cosine_score.is_finite()
            || !event_ids.insert(candidate.event_id)
        {
            return Err(SemanticBranchArtifactError::Invariant(
                "cached Oracle response has invalid candidates".to_owned(),
            ));
        }
    }
    Ok(())
}

fn sampled_candidate(candidate: &Fp32Candidate) -> SampledBranchCandidate {
    SampledBranchCandidate {
        event_id: candidate.event_id,
        rank: candidate.rank,
        rank_quartile: ((candidate.rank - 1) / QUARTILE_WIDTH) as u8,
        cached_cosine_score: candidate.cosine_score,
    }
}

fn sample_key(event_id: &EventId) -> [u8; 32] {
    let mut digest = Sha256::new();
    digest.update(b"oracle-mvp-semantic-branch-quartile-sample-v1\0");
    digest.update(event_id);
    digest.finalize().into()
}

fn validate_prepare_config(config: &SemanticBranchPrepareConfig) -> Result<()> {
    if !is_sha256(&config.expected_cached_response_sha256)
        || !is_sha256(&config.expected_corpus_data_sha256)
        || !is_sha256(&config.representation_version)
        || config.represented_rows <= CANDIDATE_DEPTH as u64
        || config.cached_response_path == config.output_path
        || config.corpus_path == config.output_path
    {
        return Err(SemanticBranchArtifactError::Invariant(
            "prepare config has invalid identities or paths".to_owned(),
        ));
    }
    Ok(())
}

fn load_sampled_contents(
    corpus_path: &Path,
    sampled: &[SampledBranchCandidate],
) -> Result<BTreeMap<EventId, String>> {
    let corpus = open_existing_ndb(corpus_path, Validation::TrustedSource)?;
    let transaction = Transaction::new(&corpus)
        .map_err(|error| SemanticBranchArtifactError::Ndb(error.to_string()))?;
    let mut contents = BTreeMap::new();
    for candidate in sampled {
        let note = corpus
            .get_note_by_id(&transaction, &candidate.event_id)
            .map_err(|error| {
                SemanticBranchArtifactError::Ndb(format!(
                    "load event {}: {error}",
                    encode_hex(&candidate.event_id)
                ))
            })?;
        contents.insert(candidate.event_id, note.content().to_owned());
    }
    Ok(contents)
}

fn build_blind_packets(
    sampled: &[SampledBranchCandidate],
    contents: &BTreeMap<EventId, String>,
) -> Result<(Vec<BlindRecord>, Vec<BlindRecord>, Vec<PrivateKeyRecord>)> {
    if sampled.len() != SAMPLE_COUNT || contents.len() != SAMPLE_COUNT {
        return Err(SemanticBranchArtifactError::Invariant(
            "prepared sample does not contain exactly 160 notes".to_owned(),
        ));
    }
    let mut by_rank = sampled.iter().collect::<Vec<_>>();
    by_rank.sort_unstable_by_key(|candidate| candidate.rank);
    let candidate_ids = by_rank
        .iter()
        .enumerate()
        .map(|(index, candidate)| (candidate.event_id, format!("C{:03}", index + 1)))
        .collect::<BTreeMap<_, _>>();

    let packet_a_order = blind_order(sampled, b"labeler-a");
    let packet_b_order = blind_order(sampled, b"labeler-b");
    let a_record_ids = packet_a_order
        .iter()
        .enumerate()
        .map(|(index, candidate)| (candidate.event_id, format!("A{:03}", index + 1)))
        .collect::<BTreeMap<_, _>>();
    let b_record_ids = packet_b_order
        .iter()
        .enumerate()
        .map(|(index, candidate)| (candidate.event_id, format!("B{:03}", index + 1)))
        .collect::<BTreeMap<_, _>>();
    let packet_a = packet_a_order
        .into_iter()
        .map(|candidate| {
            Ok(BlindRecord {
                record_id: a_record_ids[&candidate.event_id].clone(),
                content: contents
                    .get(&candidate.event_id)
                    .ok_or_else(|| {
                        SemanticBranchArtifactError::Invariant(
                            "sampled candidate lacks corpus content".to_owned(),
                        )
                    })?
                    .clone(),
            })
        })
        .collect::<Result<Vec<_>>>()?;
    let packet_b = packet_b_order
        .into_iter()
        .map(|candidate| {
            Ok(BlindRecord {
                record_id: b_record_ids[&candidate.event_id].clone(),
                content: contents
                    .get(&candidate.event_id)
                    .ok_or_else(|| {
                        SemanticBranchArtifactError::Invariant(
                            "sampled candidate lacks corpus content".to_owned(),
                        )
                    })?
                    .clone(),
            })
        })
        .collect::<Result<Vec<_>>>()?;
    let key = by_rank
        .into_iter()
        .map(|candidate| {
            Ok(PrivateKeyRecord {
                candidate_id: candidate_ids[&candidate.event_id].clone(),
                labeler_a_record_id: a_record_ids[&candidate.event_id].clone(),
                labeler_b_record_id: b_record_ids[&candidate.event_id].clone(),
                event_id: encode_hex(&candidate.event_id),
                rank: u32::try_from(candidate.rank).map_err(|_| {
                    SemanticBranchArtifactError::Invariant(
                        "candidate rank does not fit u32".to_owned(),
                    )
                })?,
                rank_quartile: candidate.rank_quartile,
                cached_cosine_score: f64::from(candidate.cached_cosine_score),
            })
        })
        .collect::<Result<Vec<_>>>()?;
    validate_prepared_records(&packet_a, &packet_b, &key)?;
    Ok((packet_a, packet_b, key))
}

fn blind_order<'a>(
    sampled: &'a [SampledBranchCandidate],
    labeler: &[u8],
) -> Vec<&'a SampledBranchCandidate> {
    let mut order = sampled
        .iter()
        .map(|candidate| {
            let mut digest = Sha256::new();
            digest.update(b"oracle-mvp-semantic-branch-blind-order-v1\0");
            digest.update((labeler.len() as u64).to_le_bytes());
            digest.update(labeler);
            digest.update(candidate.event_id);
            (Into::<[u8; 32]>::into(digest.finalize()), candidate)
        })
        .collect::<Vec<_>>();
    order.sort_unstable_by(|left, right| {
        left.0
            .cmp(&right.0)
            .then_with(|| left.1.event_id.cmp(&right.1.event_id))
    });
    order.into_iter().map(|(_, candidate)| candidate).collect()
}

fn write_prepared_artifact(
    config: &SemanticBranchPrepareConfig,
    corpus_data_path: &Path,
    packet_a: &[BlindRecord],
    packet_b: &[BlindRecord],
    key: &[PrivateKeyRecord],
    stage: &Path,
) -> Result<()> {
    let packet_a_path = stage.join(LABELER_A_PACKET_FILE);
    let packet_b_path = stage.join(LABELER_B_PACKET_FILE);
    let key_path = stage.join(PRIVATE_KEY_FILE);
    let rubric_path = stage.join(RUBRIC_FILE);
    write_json_lines(&packet_a_path, packet_a)?;
    write_json_lines(&packet_b_path, packet_b)?;
    write_json_lines(&key_path, key)?;
    write_json_exclusive(&rubric_path, &branch_rubric())?;
    let manifest = PrepareManifest {
        schema_version: ARTIFACT_SCHEMA_VERSION,
        diagnostic_id: DIAGNOSTIC_ID.to_owned(),
        source_event_id: encode_hex(&config.source_event_id),
        representation_version: config.representation_version.clone(),
        represented_rows: config.represented_rows,
        candidate_depth: CANDIDATE_DEPTH,
        selection_policy: SELECTION_POLICY.to_owned(),
        samples_per_quartile: SAMPLES_PER_QUARTILE,
        sample_count: SAMPLE_COUNT,
        cached_response_path: config.cached_response_path.clone(),
        cached_response_sha256: config.expected_cached_response_sha256.clone(),
        corpus_data_path: corpus_data_path.to_owned(),
        corpus_data_sha256: config.expected_corpus_data_sha256.clone(),
        labeler_a_packet_sha256: hash_file(&packet_a_path)?,
        labeler_b_packet_sha256: hash_file(&packet_b_path)?,
        private_key_sha256: hash_file(&key_path)?,
        rubric_sha256: hash_file(&rubric_path)?,
    };
    write_json_exclusive(&stage.join(PREPARE_MANIFEST_FILE), &manifest)
}

fn branch_rubric() -> BranchRubric {
    use crate::semantic_branch_geometry::Theme;
    BranchRubric {
        schema_version: ARTIFACT_SCHEMA_VERSION,
        diagnostic_id: DIAGNOSTIC_ID.to_owned(),
        instruction: "Judge only the supplied note text. Select every substantive semantic facet, select no facets when none applies, or mark the note unusable."
            .to_owned(),
        rules: vec![
            "Select multiple facets when more than one is substantive.".to_owned(),
            "An empty facet set means neither; it is a valid usable label.".to_owned(),
            "Use unusable only for unreadable, primarily non-English, or missing-context text."
                .to_owned(),
            "Do not infer from identity, retrieval rank, score, source, or vector information."
                .to_owned(),
        ],
        definitions: BTreeMap::from([
            (
                Theme::Physical,
                "Bodily exercise, fitness, or physical activity.".to_owned(),
            ),
            (
                Theme::Mental,
                "Learning, reading, writing, creating, knowledge, or cognitive development."
                    .to_owned(),
            ),
            (
                Theme::Spiritual,
                "Prayer, meditation, religion, or inner spiritual practice.".to_owned(),
            ),
        ]),
    }
}

fn read_verified_prepare_manifest(run_path: &Path) -> Result<(PathBuf, PrepareManifest)> {
    let path = run_path.join(PREPARE_MANIFEST_FILE);
    let manifest: PrepareManifest = read_json(&path)?;
    if manifest.schema_version != ARTIFACT_SCHEMA_VERSION
        || manifest.diagnostic_id != DIAGNOSTIC_ID
        || manifest.candidate_depth != CANDIDATE_DEPTH
        || manifest.selection_policy != SELECTION_POLICY
        || manifest.samples_per_quartile != SAMPLES_PER_QUARTILE
        || manifest.sample_count != SAMPLE_COUNT
        || !is_sha256(&manifest.cached_response_sha256)
        || !is_sha256(&manifest.corpus_data_sha256)
        || !is_sha256(&manifest.representation_version)
        || manifest.represented_rows <= CANDIDATE_DEPTH as u64
    {
        return Err(SemanticBranchArtifactError::Invariant(
            "prepare manifest violates the semantic-branch protocol".to_owned(),
        ));
    }
    Ok((path, manifest))
}

fn verify_source_artifacts(manifest: &PrepareManifest) -> Result<()> {
    require_hash(
        &manifest.cached_response_path,
        &manifest.cached_response_sha256,
    )?;
    require_hash(&manifest.corpus_data_path, &manifest.corpus_data_sha256)
}

fn validate_seal(
    run_path: &Path,
    manifest_path: &Path,
    manifest: &PrepareManifest,
    seal: &LabelSeal,
) -> Result<()> {
    if seal.schema_version != ARTIFACT_SCHEMA_VERSION
        || seal.diagnostic_id != DIAGNOSTIC_ID
        || seal.record_count != SAMPLE_COUNT
    {
        return Err(SemanticBranchArtifactError::Invariant(
            "label seal violates the semantic-branch protocol".to_owned(),
        ));
    }
    require_hash(manifest_path, &seal.prepare_manifest_sha256)?;
    require_hash(
        &run_path.join(LABELER_A_PACKET_FILE),
        &seal.labeler_a_packet_sha256,
    )?;
    require_hash(
        &run_path.join(LABELER_B_PACKET_FILE),
        &seal.labeler_b_packet_sha256,
    )?;
    require_hash(&run_path.join(PRIVATE_KEY_FILE), &seal.private_key_sha256)?;
    require_hash(&run_path.join(RUBRIC_FILE), &seal.rubric_sha256)?;
    require_hash(
        &run_path.join(LABELER_A_LABELS_FILE),
        &seal.labeler_a_labels_sha256,
    )?;
    require_hash(
        &run_path.join(LABELER_B_LABELS_FILE),
        &seal.labeler_b_labels_sha256,
    )?;
    if seal.labeler_a_packet_sha256 != manifest.labeler_a_packet_sha256
        || seal.labeler_b_packet_sha256 != manifest.labeler_b_packet_sha256
        || seal.private_key_sha256 != manifest.private_key_sha256
        || seal.rubric_sha256 != manifest.rubric_sha256
    {
        return Err(SemanticBranchArtifactError::Invariant(
            "label seal and prepare manifest differ".to_owned(),
        ));
    }
    Ok(())
}

fn validate_prepared_records(
    packet_a: &[BlindRecord],
    packet_b: &[BlindRecord],
    key: &[PrivateKeyRecord],
) -> Result<()> {
    if packet_a.len() != SAMPLE_COUNT || packet_b.len() != SAMPLE_COUNT || key.len() != SAMPLE_COUNT
    {
        return Err(SemanticBranchArtifactError::Invariant(
            "blind packets and private key must each contain 160 records".to_owned(),
        ));
    }
    let a_ids = unique_blind_ids(packet_a, "labeler A")?;
    let b_ids = unique_blind_ids(packet_b, "labeler B")?;
    let mut candidate_ids = BTreeSet::new();
    let mut event_ids = BTreeSet::new();
    let mut ranks = BTreeSet::new();
    let mut mapped_a = BTreeSet::new();
    let mut mapped_b = BTreeSet::new();
    let mut quartiles = BTreeMap::<u8, usize>::new();
    for record in key {
        let event_id = decode_event_id(&record.event_id)?;
        if record.candidate_id.is_empty()
            || !candidate_ids.insert(record.candidate_id.clone())
            || !event_ids.insert(event_id)
            || record.rank == 0
            || record.rank > CANDIDATE_DEPTH as u32
            || !ranks.insert(record.rank)
            || record.rank_quartile != ((record.rank - 1) / QUARTILE_WIDTH as u32) as u8
            || !record.cached_cosine_score.is_finite()
            || !(-1.0..=1.0).contains(&record.cached_cosine_score)
            || !mapped_a.insert(record.labeler_a_record_id.clone())
            || !mapped_b.insert(record.labeler_b_record_id.clone())
        {
            return Err(SemanticBranchArtifactError::Invariant(
                "private key contains invalid or repeated candidate metadata".to_owned(),
            ));
        }
        *quartiles.entry(record.rank_quartile).or_insert(0) += 1;
    }
    if mapped_a != a_ids
        || mapped_b != b_ids
        || quartiles != BTreeMap::from([(0, 40), (1, 40), (2, 40), (3, 40)])
    {
        return Err(SemanticBranchArtifactError::Invariant(
            "private key does not exactly map the balanced blind packets".to_owned(),
        ));
    }
    Ok(())
}

fn unique_blind_ids(records: &[BlindRecord], name: &str) -> Result<BTreeSet<String>> {
    let ids = records
        .iter()
        .map(|record| record.record_id.clone())
        .collect::<BTreeSet<_>>();
    if ids.len() != records.len() || ids.contains("") {
        return Err(SemanticBranchArtifactError::Invariant(format!(
            "{name} blind packet repeats or omits record IDs"
        )));
    }
    Ok(ids)
}

fn validate_label_file(path: &Path, packet: &[BlindRecord]) -> Result<()> {
    load_labels(path, packet).map(|_| ())
}

fn load_labels(path: &Path, packet: &[BlindRecord]) -> Result<BTreeMap<String, BranchLabel>> {
    let expected = packet
        .iter()
        .map(|record| record.record_id.clone())
        .collect::<BTreeSet<_>>();
    let mut labels = BTreeMap::new();
    for record in read_json_lines::<SemanticBranchLabelRecord>(path)? {
        if record.record_id.is_empty()
            || labels
                .insert(record.record_id.clone(), record.label)
                .is_some()
        {
            return Err(SemanticBranchArtifactError::Invariant(
                "label file repeats or omits a record ID".to_owned(),
            ));
        }
    }
    if labels.keys().cloned().collect::<BTreeSet<_>>() != expected {
        return Err(SemanticBranchArtifactError::Invariant(
            "label file does not exactly cover its blind packet".to_owned(),
        ));
    }
    Ok(labels)
}

fn validate_key_against_selection(
    key: &[PrivateKeyRecord],
    selected: &[SampledBranchCandidate],
) -> Result<()> {
    if key.len() != selected.len() {
        return Err(SemanticBranchArtifactError::Invariant(
            "private key and cached response selection differ".to_owned(),
        ));
    }
    let by_rank = key
        .iter()
        .map(|record| (record.rank as usize, record))
        .collect::<BTreeMap<_, _>>();
    for candidate in selected {
        let Some(record) = by_rank.get(&candidate.rank) else {
            return Err(SemanticBranchArtifactError::Invariant(
                "private key omits a selected cached-response rank".to_owned(),
            ));
        };
        if decode_event_id(&record.event_id)? != candidate.event_id
            || record.rank_quartile != candidate.rank_quartile
            || record.cached_cosine_score != f64::from(candidate.cached_cosine_score)
        {
            return Err(SemanticBranchArtifactError::Invariant(
                "private key differs from the cached response selection".to_owned(),
            ));
        }
    }
    Ok(())
}

fn read_json<T: for<'de> Deserialize<'de>>(path: &Path) -> Result<T> {
    let file = File::open(path).map_err(|source| io_error("open", path, source))?;
    serde_json::from_reader(BufReader::new(file)).map_err(|source| json_error("read", path, source))
}

fn read_json_lines<T: for<'de> Deserialize<'de>>(path: &Path) -> Result<Vec<T>> {
    let file = File::open(path).map_err(|source| io_error("open", path, source))?;
    BufReader::new(file)
        .lines()
        .enumerate()
        .map(|(index, line)| {
            let line = line.map_err(|source| io_error("read", path, source))?;
            serde_json::from_str(&line).map_err(|source| {
                json_error(
                    "read",
                    path,
                    serde_json::Error::io(io::Error::new(
                        io::ErrorKind::InvalidData,
                        format!("line {}: {source}", index + 1),
                    )),
                )
            })
        })
        .collect()
}

fn write_json_lines<T: Serialize>(path: &Path, records: &[T]) -> Result<()> {
    let file = create_new(path)?;
    let mut writer = BufWriter::new(file);
    for record in records {
        serde_json::to_writer(&mut writer, record)
            .map_err(|source| json_error("write", path, source))?;
        writer
            .write_all(b"\n")
            .map_err(|source| io_error("write", path, source))?;
    }
    writer
        .flush()
        .map_err(|source| io_error("flush", path, source))?;
    writer
        .get_ref()
        .sync_all()
        .map_err(|source| io_error("sync", path, source))
}

fn write_json_exclusive<T: Serialize>(path: &Path, value: &T) -> Result<()> {
    let file = create_new(path)?;
    let mut writer = BufWriter::new(file);
    serde_json::to_writer_pretty(&mut writer, value)
        .map_err(|source| json_error("write", path, source))?;
    writer
        .write_all(b"\n")
        .map_err(|source| io_error("write", path, source))?;
    writer
        .flush()
        .map_err(|source| io_error("flush", path, source))?;
    writer
        .get_ref()
        .sync_all()
        .map_err(|source| io_error("sync", path, source))
}

fn create_new(path: &Path) -> Result<File> {
    OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(path)
        .map_err(|source| {
            if source.kind() == io::ErrorKind::AlreadyExists {
                SemanticBranchArtifactError::ArtifactExists(path.to_owned())
            } else {
                io_error("create", path, source)
            }
        })
}

fn temporary_sibling(path: &Path) -> PathBuf {
    let name = path
        .file_name()
        .and_then(|value| value.to_str())
        .unwrap_or("semantic-branch");
    path.with_file_name(format!(".{name}.tmp-{}", std::process::id()))
}

fn sync_parent(path: &Path) -> Result<()> {
    let parent = path.parent().ok_or_else(|| {
        SemanticBranchArtifactError::Invariant(format!(
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
    if !path.is_file() {
        return Err(SemanticBranchArtifactError::ArtifactMissing(
            path.to_owned(),
        ));
    }
    let actual = hash_file(path)?;
    if actual == expected {
        Ok(())
    } else {
        Err(SemanticBranchArtifactError::HashMismatch {
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

fn decode_event_id(value: &str) -> Result<EventId> {
    if value.len() != 64 {
        return Err(SemanticBranchArtifactError::Invariant(format!(
            "invalid event ID `{value}`"
        )));
    }
    let mut event_id = [0_u8; 32];
    for (index, byte) in event_id.iter_mut().enumerate() {
        *byte = u8::from_str_radix(&value[index * 2..index * 2 + 2], 16).map_err(|_| {
            SemanticBranchArtifactError::Invariant(format!("invalid event ID `{value}`"))
        })?;
    }
    Ok(event_id)
}

fn encode_hex(bytes: &[u8]) -> String {
    bytes.iter().map(|byte| format!("{byte:02x}")).collect()
}

fn io_error(
    operation: &'static str,
    path: impl AsRef<Path>,
    source: io::Error,
) -> SemanticBranchArtifactError {
    SemanticBranchArtifactError::Io {
        operation,
        path: path.as_ref().to_owned(),
        source,
    }
}

fn json_error(
    operation: &'static str,
    path: impl AsRef<Path>,
    source: serde_json::Error,
) -> SemanticBranchArtifactError {
    SemanticBranchArtifactError::Json {
        operation,
        path: path.as_ref().to_owned(),
        source,
    }
}
