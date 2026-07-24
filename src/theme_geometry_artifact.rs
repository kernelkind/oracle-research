//! Auditable preparation and execution of the blind theme-geometry diagnostic.

use std::collections::{BTreeMap, BTreeSet};
use std::fs::{self, File, OpenOptions};
use std::io::{self, BufRead, BufReader, BufWriter, Read, Write};
use std::path::{Path, PathBuf};

use nostrdb::Transaction;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use thiserror::Error;

use crate::fp32_oracle::vectors_for_notes;
use crate::representation::EventId;
use crate::snapshot::{Validation, open_existing_ndb};
use crate::theme_geometry_diagnostic::{
    DiagnosticDecision, GeometryAnalysisSettings, Theme, ThemeGeometryError, ThemeGeometryReport,
    ThemeLabelSet, ThemeNote, analyze_geometry,
};

const ARTIFACT_SCHEMA_VERSION: u32 = 1;
const DIAGNOSTIC_ID: &str = "crec-101-theme-vector-separation-v1";
const BLIND_FILE: &str = "blind-theme-notes.jsonl";
const KEY_FILE: &str = "blind-key.jsonl";
const RUBRIC_FILE: &str = "theme-rubric.json";
const PREPARE_MANIFEST_FILE: &str = "prepare-manifest.json";
const LABEL_A_FILE: &str = "labels-a.jsonl";
const LABEL_B_FILE: &str = "labels-b.jsonl";
const LABEL_SEAL_FILE: &str = "label-seal.json";
const REPORT_FILE: &str = "geometry-report.json";
const REPORT_MARKDOWN_FILE: &str = "geometry-report.md";
const BLIND_ORDER_POLICY: &str = "sha256-event-id-concealed-v1";
const DUPLICATE_NORMALIZATION_POLICY: &str = "unicode-lowercase-whitespace-collapse-v1";
const ANALYSIS_FAMILY_POLICY: &str = "nostr-crypto-union-llm-ai-alcohol-distinct-exclusive-8-v1";
const EXPECTED_PREFIX_NOTES: usize = 140;
const EXPECTED_SESSION_SHA256: &str =
    "a7c6e21496049330fbcb0ebc3ab867f4c2e6f1a8c188912bbf0bea27765e4558";
const EXPECTED_CORPUS_DATA_SHA256: &str =
    "8c6e8b7798a52639f78bd4a0ba4276d72784e4d1f149e3d5925d95289ae62bad";
const EXPECTED_ORDERED_EVENT_IDS_SHA256: &str =
    "5b161558645a66ac93418d47ac6fc77daff761940200f6fddc07b30587e78c39";
const EXPECTED_REPRESENTATION_VERSION: &str =
    "5365b29f5e41d361cfae4b3a1754501d5320728053887236449071d680302c50";
const EXPECTED_MINIMUM_THEME_NOTES: usize = 8;
const EXPECTED_PERMUTATIONS: usize = 10_000;
const EXPECTED_SHUFFLE_SEED: &str = "crec-101-theme-vector-separation-blind-v1";
const EXPECTED_PERMUTATION_SEED: &str = "crec-101-theme-vector-separation-permutations-v1";

pub type Result<T> = std::result::Result<T, ThemeGeometryArtifactError>;

#[derive(Debug, Error)]
pub enum ThemeGeometryArtifactError {
    #[error("presentation ordinal must be positive")]
    InvalidPresentationOrdinal,
    #[error("source note content must be nonempty")]
    EmptyContent,
    #[error("blind shuffle seed must be nonempty")]
    EmptyShuffleSeed,
    #[error("source notes repeat presentation ordinal {0}")]
    DuplicatePresentationOrdinal(u32),
    #[error("source notes repeat an event ID")]
    DuplicateEventId,
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
    #[error("artifact invariant failed: {0}")]
    Invariant(String),
    #[error("hash mismatch for `{path}`: expected {expected}, got {actual}")]
    HashMismatch {
        path: PathBuf,
        expected: String,
        actual: String,
    },
    #[error("invalid event ID hex `{0}`")]
    InvalidEventId(String),
    #[error("NostrDB operation failed: {0}")]
    Ndb(String),
    #[error(transparent)]
    Snapshot(#[from] crate::snapshot::Error),
    #[error(transparent)]
    Geometry(#[from] ThemeGeometryError),
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct BlindSourceNote {
    presentation_ordinal: u32,
    event_id: EventId,
    content: String,
}

impl BlindSourceNote {
    pub fn new(presentation_ordinal: u32, event_id: EventId, content: String) -> Result<Self> {
        if presentation_ordinal == 0 {
            return Err(ThemeGeometryArtifactError::InvalidPresentationOrdinal);
        }
        if content.is_empty() {
            return Err(ThemeGeometryArtifactError::EmptyContent);
        }
        Ok(Self {
            presentation_ordinal,
            event_id,
            content,
        })
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct BlindThemeRecord {
    record_id: String,
    content: String,
}

impl BlindThemeRecord {
    pub fn record_id(&self) -> &str {
        &self.record_id
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct BlindKeyRecord {
    record_id: String,
    presentation_ordinal: u32,
    event_id: String,
}

impl BlindKeyRecord {
    pub fn record_id(&self) -> &str {
        &self.record_id
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct ThemeLabelRecord {
    pub record_id: String,
    pub themes: BTreeSet<Theme>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct ThemeRubric {
    schema_version: u32,
    diagnostic_id: String,
    instruction: String,
    rules: Vec<String>,
    definitions: BTreeMap<Theme, String>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct ThemeGeometryPrepareConfig {
    pub session_path: PathBuf,
    pub expected_session_sha256: String,
    pub corpus_path: PathBuf,
    pub expected_corpus_data_sha256: String,
    pub output_path: PathBuf,
    pub prefix_notes: usize,
    pub shuffle_seed: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct ThemeGeometryAnalysisConfig {
    pub run_path: PathBuf,
    pub prepare_config_path: PathBuf,
    pub ordered_event_ids_path: PathBuf,
    pub expected_ordered_event_ids_sha256: String,
    pub representation_path: PathBuf,
    pub representation_version: String,
    pub minimum_theme_notes: usize,
    pub permutations: usize,
    pub permutation_seed: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
struct PrepareManifest {
    schema_version: u32,
    diagnostic_id: String,
    prefix_notes: usize,
    session_path: PathBuf,
    session_sha256: String,
    corpus_data_sha256: String,
    blind_order_policy: String,
    shuffle_seed: String,
    blind_file: String,
    blind_sha256: String,
    key_file: String,
    key_sha256: String,
    rubric_file: String,
    rubric_sha256: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
struct LabelSeal {
    schema_version: u32,
    diagnostic_id: String,
    prepare_manifest_sha256: String,
    blind_sha256: String,
    key_sha256: String,
    rubric_sha256: String,
    labels_a_sha256: String,
    labels_b_sha256: String,
    record_count: usize,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
pub struct LabelAgreement {
    pub exact_record_agreement: usize,
    pub record_count: usize,
    pub exact_record_agreement_rate: f64,
    pub labeler_a_counts: BTreeMap<Theme, usize>,
    pub labeler_b_counts: BTreeMap<Theme, usize>,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
pub struct DuplicateSensitivityReport {
    pub normalization_policy: String,
    pub retained_notes: usize,
    pub removed_duplicate_presentations: usize,
    pub geometry: ThemeGeometryReport,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
pub struct ThemeGeometryArtifactReport {
    pub schema_version: u32,
    pub diagnostic_id: String,
    pub necessary_condition_only: bool,
    pub source_prefix_notes: usize,
    pub prepare_config_sha256: String,
    pub analysis_config_sha256: String,
    pub session_sha256: String,
    pub ordered_event_ids_sha256: String,
    pub representation_version: String,
    pub represented_rows: u64,
    pub vector_dimension: usize,
    pub vector_set_sha256: String,
    pub vector_lookup_elapsed_ns: u64,
    pub label_seal_sha256: String,
    pub analysis_family_policy: String,
    pub label_agreement: LabelAgreement,
    pub primary: ThemeGeometryReport,
    pub normalized_exact_duplicate_sensitivity: DuplicateSensitivityReport,
    pub decision: DiagnosticDecision,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct BlindPacket {
    blind_records: Vec<BlindThemeRecord>,
    key_records: Vec<BlindKeyRecord>,
}

impl BlindPacket {
    pub fn blind_records(&self) -> &[BlindThemeRecord] {
        &self.blind_records
    }

    pub fn key_records(&self) -> &[BlindKeyRecord] {
        &self.key_records
    }
}

pub fn build_blind_packet(notes: Vec<BlindSourceNote>, shuffle_seed: &str) -> Result<BlindPacket> {
    if shuffle_seed.is_empty() {
        return Err(ThemeGeometryArtifactError::EmptyShuffleSeed);
    }
    let mut ordinals = BTreeSet::new();
    let mut event_ids = BTreeSet::new();
    for note in &notes {
        if !ordinals.insert(note.presentation_ordinal) {
            return Err(ThemeGeometryArtifactError::DuplicatePresentationOrdinal(
                note.presentation_ordinal,
            ));
        }
        if !event_ids.insert(note.event_id) {
            return Err(ThemeGeometryArtifactError::DuplicateEventId);
        }
    }

    let mut shuffled = notes
        .into_iter()
        .map(|note| (blind_sort_key(shuffle_seed, &note.event_id), note))
        .collect::<Vec<_>>();
    shuffled.sort_unstable_by(|left, right| {
        left.0
            .cmp(&right.0)
            .then_with(|| left.1.event_id.cmp(&right.1.event_id))
    });

    let mut blind_records = Vec::with_capacity(shuffled.len());
    let mut key_records = Vec::with_capacity(shuffled.len());
    for (index, (_, note)) in shuffled.into_iter().enumerate() {
        let record_id = format!("T{:03}", index + 1);
        blind_records.push(BlindThemeRecord {
            record_id: record_id.clone(),
            content: note.content,
        });
        key_records.push(BlindKeyRecord {
            record_id,
            presentation_ordinal: note.presentation_ordinal,
            event_id: encode_hex(&note.event_id),
        });
    }
    Ok(BlindPacket {
        blind_records,
        key_records,
    })
}

pub fn read_prepare_config(path: impl AsRef<Path>) -> Result<ThemeGeometryPrepareConfig> {
    read_json(path.as_ref())
}

pub fn read_analysis_config(path: impl AsRef<Path>) -> Result<ThemeGeometryAnalysisConfig> {
    read_json(path.as_ref())
}

pub fn analyze_theme_geometry_from_config(
    path: impl AsRef<Path>,
) -> Result<ThemeGeometryArtifactReport> {
    let path = path.as_ref();
    let analysis_config_sha256 = hash_file(path)?;
    let config = read_analysis_config(path)?;
    let prepare_config_sha256 = hash_file(&config.prepare_config_path)?;
    analyze_theme_geometry(&config, prepare_config_sha256, analysis_config_sha256)
}

pub fn prepare_blind_artifact(config: &ThemeGeometryPrepareConfig) -> Result<PathBuf> {
    enforce_prepare_contract(config)?;
    if config.prefix_notes < 2 {
        return Err(ThemeGeometryArtifactError::Invariant(
            "source prefix must contain at least two notes".to_owned(),
        ));
    }
    if config.shuffle_seed.is_empty() {
        return Err(ThemeGeometryArtifactError::EmptyShuffleSeed);
    }
    require_hash(&config.session_path, &config.expected_session_sha256)?;
    let corpus_data_path = config.corpus_path.join("data.mdb");
    require_hash(&corpus_data_path, &config.expected_corpus_data_sha256)?;
    if config.output_path.exists() {
        return Err(ThemeGeometryArtifactError::ArtifactExists(
            config.output_path.clone(),
        ));
    }

    let session: SourceSession = read_json(&config.session_path)?;
    if session.schema_version != 2 {
        return Err(ThemeGeometryArtifactError::Invariant(format!(
            "expected Phase 4 session schema 2, got {}",
            session.schema_version
        )));
    }
    let wave = session.waves.first().ok_or_else(|| {
        ThemeGeometryArtifactError::Invariant("Phase 4 session has no wave".to_owned())
    })?;
    if wave.decisions.len() < config.prefix_notes {
        return Err(ThemeGeometryArtifactError::Invariant(format!(
            "Phase 4 session has only {} decisions; {} required",
            wave.decisions.len(),
            config.prefix_notes
        )));
    }

    let corpus = open_existing_ndb(&config.corpus_path, Validation::TrustedSource)?;
    let transaction = Transaction::new(&corpus)
        .map_err(|error| ThemeGeometryArtifactError::Ndb(error.to_string()))?;
    let mut notes = Vec::with_capacity(config.prefix_notes);
    for (index, decision) in wave.decisions.iter().take(config.prefix_notes).enumerate() {
        let event_id = match decision {
            SourceDecision::Rated { event_id, rating } => {
                if !(1..=7).contains(rating) {
                    return Err(ThemeGeometryArtifactError::Invariant(format!(
                        "presentation {} has invalid rating {}",
                        index + 1,
                        rating
                    )));
                }
                *event_id
            }
            SourceDecision::WrongLanguage { .. } => {
                return Err(ThemeGeometryArtifactError::Invariant(format!(
                    "presentation {} is not a rated decision",
                    index + 1
                )));
            }
        };
        let note = corpus
            .get_note_by_id(&transaction, &event_id)
            .map_err(|error| {
                ThemeGeometryArtifactError::Ndb(format!(
                    "load event {}: {error}",
                    encode_hex(&event_id)
                ))
            })?;
        notes.push(BlindSourceNote::new(
            u32::try_from(index + 1).map_err(|_| {
                ThemeGeometryArtifactError::Invariant(
                    "presentation ordinal does not fit u32".to_owned(),
                )
            })?,
            event_id,
            note.content().to_owned(),
        )?);
    }
    drop(transaction);
    drop(corpus);

    let packet = build_blind_packet(notes, &config.shuffle_seed)?;
    let stage = temporary_sibling(&config.output_path);
    if stage.exists() {
        return Err(ThemeGeometryArtifactError::ArtifactExists(stage));
    }
    create_directory(&stage)?;
    let result = write_prepared_artifact(config, &packet, &stage);
    if let Err(error) = result {
        let _ = fs::remove_dir_all(&stage);
        return Err(error);
    }
    fs::rename(&stage, &config.output_path)
        .map_err(|source| io_error("publish", &config.output_path, source))?;
    sync_parent(&config.output_path)?;
    Ok(config.output_path.clone())
}

pub fn seal_theme_labels(run_path: impl AsRef<Path>) -> Result<PathBuf> {
    let run_path = run_path.as_ref();
    let seal_path = run_path.join(LABEL_SEAL_FILE);
    if seal_path.exists() {
        return Err(ThemeGeometryArtifactError::ArtifactExists(seal_path));
    }
    let manifest_path = run_path.join(PREPARE_MANIFEST_FILE);
    let manifest: PrepareManifest = read_json(&manifest_path)?;
    require_diagnostic(&manifest.diagnostic_id)?;
    let blind_path = run_path.join(&manifest.blind_file);
    let key_path = run_path.join(&manifest.key_file);
    let rubric_path = run_path.join(&manifest.rubric_file);
    require_hash(&blind_path, &manifest.blind_sha256)?;
    require_hash(&key_path, &manifest.key_sha256)?;
    require_hash(&rubric_path, &manifest.rubric_sha256)?;
    let blind = read_json_lines::<BlindThemeRecord>(&blind_path)?;
    let expected_ids = blind
        .iter()
        .map(|record| record.record_id.clone())
        .collect::<BTreeSet<_>>();
    if expected_ids.len() != blind.len() {
        return Err(ThemeGeometryArtifactError::Invariant(
            "blind packet repeats record IDs".to_owned(),
        ));
    }
    let labels_a_path = run_path.join(LABEL_A_FILE);
    let labels_b_path = run_path.join(LABEL_B_FILE);
    validate_label_file("labeler-a", &labels_a_path, &expected_ids)?;
    validate_label_file("labeler-b", &labels_b_path, &expected_ids)?;

    let seal = LabelSeal {
        schema_version: ARTIFACT_SCHEMA_VERSION,
        diagnostic_id: DIAGNOSTIC_ID.to_owned(),
        prepare_manifest_sha256: hash_file(&manifest_path)?,
        blind_sha256: hash_file(&blind_path)?,
        key_sha256: hash_file(&key_path)?,
        rubric_sha256: hash_file(&rubric_path)?,
        labels_a_sha256: hash_file(&labels_a_path)?,
        labels_b_sha256: hash_file(&labels_b_path)?,
        record_count: blind.len(),
    };
    write_json_exclusive(&seal_path, &seal)?;
    Ok(seal_path)
}

fn analyze_theme_geometry(
    config: &ThemeGeometryAnalysisConfig,
    prepare_config_sha256: String,
    analysis_config_sha256: String,
) -> Result<ThemeGeometryArtifactReport> {
    enforce_analysis_contract(config)?;
    let report_path = config.run_path.join(REPORT_FILE);
    let report_markdown_path = config.run_path.join(REPORT_MARKDOWN_FILE);
    if report_path.exists() {
        return Err(ThemeGeometryArtifactError::ArtifactExists(report_path));
    }
    if report_markdown_path.exists() {
        return Err(ThemeGeometryArtifactError::ArtifactExists(
            report_markdown_path,
        ));
    }
    let manifest_path = config.run_path.join(PREPARE_MANIFEST_FILE);
    let manifest: PrepareManifest = read_json(&manifest_path)?;
    require_diagnostic(&manifest.diagnostic_id)?;
    enforce_prepare_manifest_contract(&manifest)?;
    let prepare_config = read_prepare_config(&config.prepare_config_path)?;
    enforce_prepare_contract(&prepare_config)?;
    if prepare_config.output_path != config.run_path {
        return Err(ThemeGeometryArtifactError::Invariant(
            "prepare and analysis configs name different run artifacts".to_owned(),
        ));
    }
    let seal_path = config.run_path.join(LABEL_SEAL_FILE);
    let seal: LabelSeal = read_json(&seal_path)?;
    require_diagnostic(&seal.diagnostic_id)?;
    verify_seal(&config.run_path, &manifest_path, &manifest, &seal)?;
    require_hash(
        &config.ordered_event_ids_path,
        &config.expected_ordered_event_ids_sha256,
    )?;

    let blind = read_json_lines::<BlindThemeRecord>(&config.run_path.join(BLIND_FILE))?;
    let key = read_json_lines::<BlindKeyRecord>(&config.run_path.join(KEY_FILE))?;
    if blind.len() != key.len() || blind.len() != seal.record_count {
        return Err(ThemeGeometryArtifactError::Invariant(
            "blind packet, key, and label seal counts differ".to_owned(),
        ));
    }
    for (blind_record, key_record) in blind.iter().zip(&key) {
        if blind_record.record_id != key_record.record_id {
            return Err(ThemeGeometryArtifactError::Invariant(
                "blind packet and key order differ".to_owned(),
            ));
        }
    }
    let raw_labels_a = load_label_set("labeler-a", &config.run_path.join(LABEL_A_FILE), &blind)?;
    let raw_labels_b = load_label_set("labeler-b", &config.run_path.join(LABEL_B_FILE), &blind)?;
    let labels_a = derive_analysis_label_set(&raw_labels_a)?;
    let labels_b = derive_analysis_label_set(&raw_labels_b)?;
    let event_ids = key
        .iter()
        .map(|record| decode_event_id(&record.event_id))
        .collect::<Result<Vec<_>>>()?;
    let vector_response = vectors_for_notes(
        &config.ordered_event_ids_path,
        &config.representation_path,
        &event_ids,
        &config.representation_version,
    )?;
    if !vector_response.complete
        || vector_response.represented_rows != vector_response.total_rows
        || vector_response.vectors.len() != blind.len()
    {
        return Err(ThemeGeometryArtifactError::Invariant(
            "Oracle vector response is incomplete".to_owned(),
        ));
    }
    let mut notes = Vec::with_capacity(blind.len());
    for ((blind_record, expected_event_id), stored) in
        blind.iter().zip(&event_ids).zip(&vector_response.vectors)
    {
        if stored.event_id != *expected_event_id {
            return Err(ThemeGeometryArtifactError::Invariant(
                "Oracle returned vectors outside requested order".to_owned(),
            ));
        }
        notes.push(ThemeNote::new(
            blind_record.record_id.clone(),
            stored.vector.clone(),
        )?);
    }
    let settings = GeometryAnalysisSettings::new(
        config.minimum_theme_notes,
        config.permutations,
        &config.permutation_seed,
    )?;
    let label_sets = [labels_a.clone(), labels_b.clone()];
    let primary = analyze_geometry(&notes, &label_sets, &settings)?;
    let retained_ids = duplicate_sensitivity_ids(&blind, &key);
    let sensitivity_notes = notes
        .iter()
        .filter(|note| retained_ids.contains(note.id()))
        .cloned()
        .collect::<Vec<_>>();
    let sensitivity_label_sets = [
        subset_label_set(&labels_a, &retained_ids)?,
        subset_label_set(&labels_b, &retained_ids)?,
    ];
    let sensitivity_geometry =
        analyze_geometry(&sensitivity_notes, &sensitivity_label_sets, &settings)?;
    let vector_dimension = vector_response
        .vectors
        .first()
        .map(|stored| stored.vector.len())
        .ok_or_else(|| {
            ThemeGeometryArtifactError::Invariant("Oracle vector response is empty".to_owned())
        })?;
    let report = ThemeGeometryArtifactReport {
        schema_version: ARTIFACT_SCHEMA_VERSION,
        diagnostic_id: DIAGNOSTIC_ID.to_owned(),
        necessary_condition_only: true,
        source_prefix_notes: blind.len(),
        prepare_config_sha256,
        analysis_config_sha256,
        session_sha256: manifest.session_sha256.clone(),
        ordered_event_ids_sha256: config.expected_ordered_event_ids_sha256.clone(),
        representation_version: vector_response.representation_version,
        represented_rows: vector_response.represented_rows,
        vector_dimension,
        vector_set_sha256: hash_vector_set(&blind, &vector_response.vectors),
        vector_lookup_elapsed_ns: vector_response.lookup_elapsed_ns,
        label_seal_sha256: hash_file(&seal_path)?,
        analysis_family_policy: ANALYSIS_FAMILY_POLICY.to_owned(),
        label_agreement: label_agreement(&raw_labels_a, &raw_labels_b),
        primary: primary.clone(),
        normalized_exact_duplicate_sensitivity: DuplicateSensitivityReport {
            normalization_policy: DUPLICATE_NORMALIZATION_POLICY.to_owned(),
            retained_notes: sensitivity_notes.len(),
            removed_duplicate_presentations: notes.len() - sensitivity_notes.len(),
            geometry: sensitivity_geometry,
        },
        decision: primary.decision(),
    };
    write_json_exclusive(&report_path, &report)?;
    write_text_exclusive(&report_markdown_path, &markdown_report(&report))?;
    Ok(report)
}

fn write_prepared_artifact(
    config: &ThemeGeometryPrepareConfig,
    packet: &BlindPacket,
    stage: &Path,
) -> Result<()> {
    let blind_path = stage.join(BLIND_FILE);
    let key_path = stage.join(KEY_FILE);
    let rubric_path = stage.join(RUBRIC_FILE);
    write_json_lines(&blind_path, &packet.blind_records)?;
    write_json_lines(&key_path, &packet.key_records)?;
    write_json_exclusive(&rubric_path, &theme_rubric())?;
    let manifest = PrepareManifest {
        schema_version: ARTIFACT_SCHEMA_VERSION,
        diagnostic_id: DIAGNOSTIC_ID.to_owned(),
        prefix_notes: packet.blind_records.len(),
        session_path: config.session_path.clone(),
        session_sha256: config.expected_session_sha256.clone(),
        corpus_data_sha256: config.expected_corpus_data_sha256.clone(),
        blind_order_policy: BLIND_ORDER_POLICY.to_owned(),
        shuffle_seed: config.shuffle_seed.clone(),
        blind_file: BLIND_FILE.to_owned(),
        blind_sha256: hash_file(&blind_path)?,
        key_file: KEY_FILE.to_owned(),
        key_sha256: hash_file(&key_path)?,
        rubric_file: RUBRIC_FILE.to_owned(),
        rubric_sha256: hash_file(&rubric_path)?,
    };
    write_json_exclusive(&stage.join(PREPARE_MANIFEST_FILE), &manifest)
}

fn theme_rubric() -> ThemeRubric {
    ThemeRubric {
        schema_version: ARTIFACT_SCHEMA_VERSION,
        diagnostic_id: DIAGNOSTIC_ID.to_owned(),
        instruction: "Label every note by the broad reported repetitive theme or themes that it substantively discusses. Judge only the supplied note text."
            .to_owned(),
        rules: vec![
            "Use every applicable named theme when more than one is substantively present."
                .to_owned(),
            "Use other only when none of the five named themes applies; never combine other with a named theme."
                .to_owned(),
            "Do not infer from author, event ID, presentation order, rating, source, or vector information."
                .to_owned(),
            "An incidental hashtag, name, or passing reference is not enough unless the note substantively discusses that theme."
                .to_owned(),
        ],
        definitions: BTreeMap::from([
            (
                Theme::Nostr,
                "Nostr protocol, NIPs, relays, clients, ecosystem, adoption, or building and operating Nostr software."
                    .to_owned(),
            ),
            (
                Theme::Bitcoin,
                "Bitcoin, Lightning, Bitcoin mining, Bitcoin monetary ideas, or Bitcoin-specific products and practice."
                    .to_owned(),
            ),
            (
                Theme::Monero,
                "Monero, XMR, Monero mining, Monero privacy, or Monero-specific ecosystem discussion."
                    .to_owned(),
            ),
            (
                Theme::LlmAi,
                "Large language models, generative AI, machine learning systems, AI products, or AI capabilities and consequences."
                    .to_owned(),
            ),
            (
                Theme::AlcoholRecovery,
                "Alcohol use, sobriety, addiction, recovery, or personal and social experiences centered on drinking."
                    .to_owned(),
            ),
            (
                Theme::Other,
                "None of the five named themes is substantively present.".to_owned(),
            ),
        ]),
    }
}

fn validate_label_file(
    name: &str,
    path: &Path,
    expected_ids: &BTreeSet<String>,
) -> Result<ThemeLabelSet> {
    let records = read_json_lines::<ThemeLabelRecord>(path)?;
    let mut labels = BTreeMap::new();
    for record in records {
        if record.themes.contains(&Theme::Cryptocurrency) {
            return Err(ThemeGeometryArtifactError::Invariant(format!(
                "{name} contains the derived cryptocurrency family"
            )));
        }
        if labels
            .insert(record.record_id.clone(), record.themes)
            .is_some()
        {
            return Err(ThemeGeometryArtifactError::Invariant(format!(
                "{name} repeats record {}",
                record.record_id
            )));
        }
    }
    if labels.keys().collect::<BTreeSet<_>>() != expected_ids.iter().collect::<BTreeSet<_>>() {
        return Err(ThemeGeometryArtifactError::Invariant(format!(
            "{name} does not exactly cover the blind packet"
        )));
    }
    ThemeLabelSet::new(name, labels).map_err(Into::into)
}

pub fn derive_analysis_label_set(source: &ThemeLabelSet) -> Result<ThemeLabelSet> {
    let labels = source
        .labels()
        .iter()
        .map(|(record_id, source_themes)| {
            let mut themes = source_themes.clone();
            let cryptocurrency = themes.remove(&Theme::Bitcoin) | themes.remove(&Theme::Monero);
            if cryptocurrency {
                themes.insert(Theme::Cryptocurrency);
            }
            (record_id.clone(), themes)
        })
        .collect();
    ThemeLabelSet::new(source.name(), labels).map_err(Into::into)
}

fn load_label_set(name: &str, path: &Path, blind: &[BlindThemeRecord]) -> Result<ThemeLabelSet> {
    let expected_ids = blind
        .iter()
        .map(|record| record.record_id.clone())
        .collect::<BTreeSet<_>>();
    validate_label_file(name, path, &expected_ids)
}

fn verify_seal(
    run_path: &Path,
    manifest_path: &Path,
    manifest: &PrepareManifest,
    seal: &LabelSeal,
) -> Result<()> {
    if seal.schema_version != ARTIFACT_SCHEMA_VERSION
        || manifest.schema_version != ARTIFACT_SCHEMA_VERSION
        || seal.record_count != manifest.prefix_notes
    {
        return Err(ThemeGeometryArtifactError::Invariant(
            "label seal and prepared artifact metadata differ".to_owned(),
        ));
    }
    require_hash(manifest_path, &seal.prepare_manifest_sha256)?;
    require_hash(&run_path.join(BLIND_FILE), &seal.blind_sha256)?;
    require_hash(&run_path.join(KEY_FILE), &seal.key_sha256)?;
    require_hash(&run_path.join(RUBRIC_FILE), &seal.rubric_sha256)?;
    require_hash(&run_path.join(LABEL_A_FILE), &seal.labels_a_sha256)?;
    require_hash(&run_path.join(LABEL_B_FILE), &seal.labels_b_sha256)
}

fn subset_label_set(
    source: &ThemeLabelSet,
    retained_ids: &BTreeSet<String>,
) -> Result<ThemeLabelSet> {
    let labels = source
        .labels()
        .iter()
        .filter(|(record_id, _)| retained_ids.contains(*record_id))
        .map(|(record_id, themes)| (record_id.clone(), themes.clone()))
        .collect();
    ThemeLabelSet::new(source.name(), labels).map_err(Into::into)
}

fn duplicate_sensitivity_ids(
    blind: &[BlindThemeRecord],
    key: &[BlindKeyRecord],
) -> BTreeSet<String> {
    let mut earliest = BTreeMap::<String, (u32, String)>::new();
    for (blind_record, key_record) in blind.iter().zip(key) {
        let normalized = normalize_content(&blind_record.content);
        let candidate = (
            key_record.presentation_ordinal,
            blind_record.record_id.clone(),
        );
        earliest
            .entry(normalized)
            .and_modify(|current| {
                if candidate.0 < current.0 {
                    *current = candidate.clone();
                }
            })
            .or_insert(candidate);
    }
    earliest
        .into_values()
        .map(|(_, record_id)| record_id)
        .collect()
}

fn normalize_content(content: &str) -> String {
    let mut normalized = String::new();
    let mut pending_space = false;
    for character in content.chars().flat_map(char::to_lowercase) {
        if character.is_whitespace() {
            pending_space = !normalized.is_empty();
        } else {
            if pending_space {
                normalized.push(' ');
                pending_space = false;
            }
            normalized.push(character);
        }
    }
    normalized
}

fn label_agreement(left: &ThemeLabelSet, right: &ThemeLabelSet) -> LabelAgreement {
    let exact_record_agreement = left
        .labels()
        .iter()
        .filter(|(record_id, themes)| right.labels().get(*record_id) == Some(*themes))
        .count();
    LabelAgreement {
        exact_record_agreement,
        record_count: left.labels().len(),
        exact_record_agreement_rate: exact_record_agreement as f64 / left.labels().len() as f64,
        labeler_a_counts: label_counts(left),
        labeler_b_counts: label_counts(right),
    }
}

fn label_counts(label_set: &ThemeLabelSet) -> BTreeMap<Theme, usize> {
    let mut counts = BTreeMap::new();
    for themes in label_set.labels().values() {
        for theme in themes {
            *counts.entry(*theme).or_insert(0) += 1;
        }
    }
    counts
}

fn hash_vector_set(
    blind: &[BlindThemeRecord],
    vectors: &[crate::fp32_oracle::StoredNoteVector],
) -> String {
    let mut digest = Sha256::new();
    digest.update(b"oracle-mvp-theme-geometry-vector-set-v1\0");
    for (record, stored) in blind.iter().zip(vectors) {
        digest.update((record.record_id.len() as u64).to_le_bytes());
        digest.update(record.record_id.as_bytes());
        digest.update(stored.event_id);
        digest.update((stored.vector.len() as u64).to_le_bytes());
        for coordinate in &stored.vector {
            digest.update(coordinate.to_le_bytes());
        }
    }
    encode_hex(&digest.finalize())
}

fn markdown_report(report: &ThemeGeometryArtifactReport) -> String {
    let mut output = format!(
        "# CREC-101 Theme-Vector Separation Result\n\n\
         This is a necessary-condition diagnostic, not a recommendation-quality result.\n\n\
         - Decision: `{:?}`\n\
         - Notes: {}\n\
         - Representation: `{}`\n\
         - Represented rows: {}\n\
         - Vector dimension: {}\n\
         - Analysis families: `{}`\n\
         - Exact label agreement: {}/{} ({:.1}%)\n\
         - Exact-content duplicates removed in sensitivity run: {}\n\n\
         ## Primary Result\n\n",
        report.decision,
        report.source_prefix_notes,
        report.representation_version,
        report.represented_rows,
        report.vector_dimension,
        report.analysis_family_policy,
        report.label_agreement.exact_record_agreement,
        report.label_agreement.record_count,
        100.0 * report.label_agreement.exact_record_agreement_rate,
        report
            .normalized_exact_duplicate_sensitivity
            .removed_duplicate_presentations,
    );
    for label_set in &report.primary.label_sets {
        output.push_str(&format!(
            "### {}\n\n- Macro AUROC: {}\n- Macro null 95th percentile: {}\n- Macro above null: {}\n\n",
            label_set.label_set,
            optional_metric(label_set.macro_auroc),
            optional_metric(label_set.macro_permutation_95th_percentile),
            label_set.macro_above_permutation_95th_percentile,
        ));
        for (theme, metric) in &label_set.qualifying_themes {
            output.push_str(&format!(
                "- `{:?}`: n={}, AUROC={:.4}, null95={:.4}, p={:.4}, significant={}\n",
                theme,
                metric.labeled_notes,
                metric.mean_anchor_auroc,
                metric.permutation_95th_percentile,
                metric.permutation_p_value,
                metric.above_permutation_95th_percentile,
            ));
        }
        output.push('\n');
    }
    output.push_str(
        "## Interpretation Boundary\n\n\
         `ProceedToExposureReplay` means only that the stored document vectors preserve enough of at least two reported broad themes to justify the next frozen-sequence exposure replay. It does not show that adjacent novelty, personalization, or recommendation quality works.\n",
    );
    output
}

fn optional_metric(value: Option<f64>) -> String {
    value
        .map(|value| format!("{value:.4}"))
        .unwrap_or_else(|| "n/a".to_owned())
}

fn enforce_prepare_contract(config: &ThemeGeometryPrepareConfig) -> Result<()> {
    if config.expected_session_sha256 != EXPECTED_SESSION_SHA256
        || config.expected_corpus_data_sha256 != EXPECTED_CORPUS_DATA_SHA256
        || config.prefix_notes != EXPECTED_PREFIX_NOTES
        || config.shuffle_seed != EXPECTED_SHUFFLE_SEED
    {
        return Err(ThemeGeometryArtifactError::Invariant(
            "prepare config does not match the fixed CREC-101 contract".to_owned(),
        ));
    }
    Ok(())
}

fn enforce_prepare_manifest_contract(manifest: &PrepareManifest) -> Result<()> {
    if manifest.prefix_notes != EXPECTED_PREFIX_NOTES
        || manifest.session_sha256 != EXPECTED_SESSION_SHA256
        || manifest.corpus_data_sha256 != EXPECTED_CORPUS_DATA_SHA256
        || manifest.blind_order_policy != BLIND_ORDER_POLICY
        || manifest.shuffle_seed != EXPECTED_SHUFFLE_SEED
    {
        return Err(ThemeGeometryArtifactError::Invariant(
            "prepared artifact does not match the fixed CREC-101 contract".to_owned(),
        ));
    }
    Ok(())
}

fn enforce_analysis_contract(config: &ThemeGeometryAnalysisConfig) -> Result<()> {
    if config.expected_ordered_event_ids_sha256 != EXPECTED_ORDERED_EVENT_IDS_SHA256
        || config.representation_version != EXPECTED_REPRESENTATION_VERSION
        || config.minimum_theme_notes != EXPECTED_MINIMUM_THEME_NOTES
        || config.permutations != EXPECTED_PERMUTATIONS
        || config.permutation_seed != EXPECTED_PERMUTATION_SEED
    {
        return Err(ThemeGeometryArtifactError::Invariant(
            "analysis config does not match the fixed CREC-101 contract".to_owned(),
        ));
    }
    Ok(())
}

fn require_diagnostic(actual: &str) -> Result<()> {
    if actual == DIAGNOSTIC_ID {
        Ok(())
    } else {
        Err(ThemeGeometryArtifactError::Invariant(format!(
            "expected diagnostic {DIAGNOSTIC_ID}, got {actual}"
        )))
    }
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

fn write_json_lines<T: Serialize>(path: &Path, values: &[T]) -> Result<()> {
    let file = create_new(path)?;
    let mut writer = BufWriter::new(file);
    for value in values {
        serde_json::to_writer(&mut writer, value)
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

fn write_text_exclusive(path: &Path, value: &str) -> Result<()> {
    let mut file = create_new(path)?;
    file.write_all(value.as_bytes())
        .map_err(|source| io_error("write", path, source))?;
    file.sync_all()
        .map_err(|source| io_error("sync", path, source))
}

fn create_new(path: &Path) -> Result<File> {
    OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(path)
        .map_err(|source| {
            if source.kind() == io::ErrorKind::AlreadyExists {
                ThemeGeometryArtifactError::ArtifactExists(path.to_owned())
            } else {
                io_error("create", path, source)
            }
        })
}

fn create_directory(path: &Path) -> Result<()> {
    fs::create_dir_all(path).map_err(|source| io_error("create directory", path, source))
}

fn temporary_sibling(path: &Path) -> PathBuf {
    let name = path
        .file_name()
        .and_then(|name| name.to_str())
        .unwrap_or("theme-geometry");
    path.with_file_name(format!(".{name}.tmp-{}", std::process::id()))
}

fn sync_parent(path: &Path) -> Result<()> {
    let parent = path.parent().ok_or_else(|| {
        ThemeGeometryArtifactError::Invariant(format!(
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
        return Err(ThemeGeometryArtifactError::ArtifactMissing(path.to_owned()));
    }
    let actual = hash_file(path)?;
    if actual == expected {
        Ok(())
    } else {
        Err(ThemeGeometryArtifactError::HashMismatch {
            path: path.to_owned(),
            expected: expected.to_owned(),
            actual,
        })
    }
}

fn decode_event_id(value: &str) -> Result<EventId> {
    if value.len() != 64 {
        return Err(ThemeGeometryArtifactError::InvalidEventId(value.to_owned()));
    }
    let mut event_id = [0_u8; 32];
    for (index, byte) in event_id.iter_mut().enumerate() {
        *byte = u8::from_str_radix(&value[index * 2..index * 2 + 2], 16)
            .map_err(|_| ThemeGeometryArtifactError::InvalidEventId(value.to_owned()))?;
    }
    Ok(event_id)
}

fn io_error(
    operation: &'static str,
    path: impl AsRef<Path>,
    source: io::Error,
) -> ThemeGeometryArtifactError {
    ThemeGeometryArtifactError::Io {
        operation,
        path: path.as_ref().to_owned(),
        source,
    }
}

fn json_error(
    operation: &'static str,
    path: impl AsRef<Path>,
    source: serde_json::Error,
) -> ThemeGeometryArtifactError {
    ThemeGeometryArtifactError::Json {
        operation,
        path: path.as_ref().to_owned(),
        source,
    }
}

#[derive(Deserialize)]
struct SourceSession {
    schema_version: u32,
    waves: Vec<SourceWave>,
}

#[derive(Deserialize)]
struct SourceWave {
    decisions: Vec<SourceDecision>,
}

#[derive(Clone, Copy, Deserialize)]
#[serde(rename_all = "snake_case", tag = "outcome")]
enum SourceDecision {
    Rated {
        event_id: EventId,
        rating: u8,
    },
    WrongLanguage {
        #[serde(rename = "event_id")]
        _event_id: EventId,
    },
}

fn blind_sort_key(seed: &str, event_id: &EventId) -> [u8; 32] {
    let mut digest = Sha256::new();
    digest.update(b"oracle-mvp-theme-geometry-blind-order-v1\0");
    digest.update((seed.len() as u64).to_le_bytes());
    digest.update(seed.as_bytes());
    digest.update(event_id);
    digest.finalize().into()
}

fn encode_hex(bytes: &[u8]) -> String {
    bytes.iter().map(|byte| format!("{byte:02x}")).collect()
}
