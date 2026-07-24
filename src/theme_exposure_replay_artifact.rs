//! Sealed CREC-102 replay artifact runner.

use std::collections::{BTreeMap, BTreeSet};
use std::ffi::CString;
use std::fs::{self, File, OpenOptions};
use std::io::{self, BufRead, BufReader, BufWriter, Read, Write};
use std::os::unix::ffi::OsStrExt;
use std::path::{Component, Path, PathBuf};

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use thiserror::Error;

use crate::fp32_oracle::{StoredNoteVector, vectors_for_notes};
use crate::representation::EventId;
use crate::theme_exposure_replay::{
    ExposureReplayError, ExposureReplayReport, ExposureReplaySettings, analyze_exposure_replay,
};
use crate::theme_geometry_artifact::{ThemeGeometryArtifactError, derive_analysis_label_set};
use crate::theme_geometry_diagnostic::{
    DiagnosticDecision, Theme, ThemeGeometryError, ThemeLabelSet, ThemeNote,
};

const ARTIFACT_SCHEMA_VERSION: u32 = 1;
const DIAGNOSTIC_ID: &str = "crec-102-cumulative-theme-exposure-replay-v1";
const SOURCE_DIAGNOSTIC_ID: &str = "crec-101-theme-vector-separation-v1";
const SOURCE_REPORT_FILE: &str = "geometry-report.json";
const SOURCE_MANIFEST_FILE: &str = "prepare-manifest.json";
const SOURCE_BLIND_FILE: &str = "blind-theme-notes.jsonl";
const SOURCE_KEY_FILE: &str = "blind-key.jsonl";
const SOURCE_RUBRIC_FILE: &str = "theme-rubric.json";
const SOURCE_LABEL_A_FILE: &str = "labels-a.jsonl";
const SOURCE_LABEL_B_FILE: &str = "labels-b.jsonl";
const SOURCE_SEAL_FILE: &str = "label-seal.json";
const REPORT_FILE: &str = "exposure-replay-report.json";
const REPORT_MARKDOWN_FILE: &str = "exposure-replay-report.md";
const ARTIFACT_MANIFEST_FILE: &str = "artifact-manifest.json";

const EXPECTED_SOURCE_NOTES: usize = 140;
const EXPECTED_SOURCE_REPORT_SHA256: &str =
    "5273e99c555ddc6f6e825b3a8810b1d65ea707a6f48c8fbb73ef186165606297";
const EXPECTED_LABEL_SEAL_SHA256: &str =
    "d9d72b9e027c2f3d2277cec582da6bbad2d4ecf64c1f37d84a5970662bcf22a8";
const EXPECTED_ORDERED_EVENT_IDS_SHA256: &str =
    "5b161558645a66ac93418d47ac6fc77daff761940200f6fddc07b30587e78c39";
const EXPECTED_REPRESENTATION_VERSION: &str =
    "5365b29f5e41d361cfae4b3a1754501d5320728053887236449071d680302c50";
const EXPECTED_VECTOR_SET_SHA256: &str =
    "f8df0e9e607a578e3906eee9c9d072e4f1d8adec6a988dba6ec35c1c782dfeeb";
const EXPECTED_MINIMUM_FAMILY_NOTES: usize = 8;
const EXPECTED_PRIMARY_HALF_LIFE: u32 = 20;
const EXPECTED_SENSITIVITY_HALF_LIVES: [u32; 2] = [10, 40];
const EXPECTED_PERMUTATIONS: usize = 10_000;
const EXPECTED_PERMUTATION_SEED: &str = "crec-102-cumulative-theme-exposure-vector-permutations-v1";

pub type Result<T> = std::result::Result<T, ExposureReplayArtifactError>;

#[derive(Debug, Error)]
pub enum ExposureReplayArtifactError {
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
    #[error(transparent)]
    Replay(#[from] ExposureReplayError),
    #[error(transparent)]
    ThemeGeometry(#[from] ThemeGeometryError),
    #[error(transparent)]
    SourceGeometry(#[from] ThemeGeometryArtifactError),
    #[error(transparent)]
    Snapshot(#[from] crate::snapshot::Error),
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct ThemeExposureReplayConfig {
    pub source_artifact_path: PathBuf,
    pub expected_source_report_sha256: String,
    pub expected_label_seal_sha256: String,
    pub ordered_event_ids_path: PathBuf,
    pub expected_ordered_event_ids_sha256: String,
    pub representation_path: PathBuf,
    pub representation_version: String,
    pub expected_vector_set_sha256: String,
    pub output_path: PathBuf,
    pub minimum_family_notes: usize,
    pub primary_half_life: u32,
    pub sensitivity_half_lives: [u32; 2],
    pub permutations: usize,
    pub permutation_seed: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct SealedReplayIdentity {
    pub record_id: String,
    pub presentation_ordinal: u32,
    pub event_id: String,
}

#[derive(Clone, Debug, PartialEq)]
pub struct SealedReplayInput {
    identities_in_blind_order: Vec<SealedReplayIdentity>,
    label_sets: [ThemeLabelSet; 2],
    source: SourceGeometryReport,
    label_seal_sha256: String,
}

impl SealedReplayInput {
    pub fn identities_in_blind_order(&self) -> &[SealedReplayIdentity] {
        &self.identities_in_blind_order
    }

    pub fn chronological_identities(&self) -> Vec<SealedReplayIdentity> {
        let mut identities = self.identities_in_blind_order.clone();
        identities.sort_unstable_by_key(|identity| identity.presentation_ordinal);
        identities
    }

    pub fn label_sets(&self) -> &[ThemeLabelSet; 2] {
        &self.label_sets
    }
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
pub struct ThemeExposureArtifactReport {
    pub schema_version: u32,
    pub diagnostic_id: String,
    pub mechanism_check_only: bool,
    pub config_sha256: String,
    pub source_geometry_report_sha256: String,
    pub label_seal_sha256: String,
    pub ordered_event_ids_sha256: String,
    pub representation_version: String,
    pub represented_rows: u64,
    pub vector_dimension: usize,
    pub vector_set_sha256: String,
    pub chronology: Vec<SealedReplayIdentity>,
    pub exposure_formula: String,
    pub null_policy: String,
    pub interpretation_boundary: String,
    pub replay: ExposureReplayReport,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
struct ArtifactManifest {
    schema_version: u32,
    diagnostic_id: String,
    config_sha256: String,
    source_geometry_report_sha256: String,
    label_seal_sha256: String,
    report_file: String,
    report_sha256: String,
    markdown_file: String,
    markdown_sha256: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq)]
struct SourceGeometryReport {
    diagnostic_id: String,
    source_prefix_notes: usize,
    ordered_event_ids_sha256: String,
    representation_version: String,
    represented_rows: u64,
    vector_dimension: usize,
    vector_set_sha256: String,
    label_seal_sha256: String,
    decision: DiagnosticDecision,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq)]
struct SourcePrepareManifest {
    schema_version: u32,
    diagnostic_id: String,
    prefix_notes: usize,
    blind_file: String,
    blind_sha256: String,
    key_file: String,
    key_sha256: String,
    rubric_file: String,
    rubric_sha256: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq)]
struct SourceLabelSeal {
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

#[derive(Clone, Debug, Deserialize, Eq, PartialEq)]
struct SourceBlindRecord {
    record_id: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq)]
struct SourceKeyRecord {
    record_id: String,
    presentation_ordinal: u32,
    event_id: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq)]
struct SourceLabelRecord {
    record_id: String,
    themes: BTreeSet<Theme>,
}

pub fn read_theme_exposure_replay_config(
    path: impl AsRef<Path>,
) -> Result<ThemeExposureReplayConfig> {
    read_json(path.as_ref())
}

pub fn run_theme_exposure_replay_from_config(
    path: impl AsRef<Path>,
) -> Result<ThemeExposureArtifactReport> {
    let path = path.as_ref();
    let (config_sha256, config) = read_hashed_json(path)?;
    validate_theme_exposure_replay_config(&config)?;
    publish_report(&config, config_sha256)
}

pub fn verify_theme_exposure_replay_from_config(
    path: impl AsRef<Path>,
) -> Result<ThemeExposureArtifactReport> {
    let path = path.as_ref();
    let (config_sha256, config) = read_hashed_json(path)?;
    validate_theme_exposure_replay_config(&config)?;
    let manifest_path = config.output_path.join(ARTIFACT_MANIFEST_FILE);
    let manifest: ArtifactManifest = read_json(&manifest_path)?;
    if manifest.schema_version != ARTIFACT_SCHEMA_VERSION
        || manifest.diagnostic_id != DIAGNOSTIC_ID
        || manifest.config_sha256 != config_sha256
        || manifest.source_geometry_report_sha256 != config.expected_source_report_sha256
        || manifest.label_seal_sha256 != config.expected_label_seal_sha256
        || manifest.report_file != REPORT_FILE
        || manifest.markdown_file != REPORT_MARKDOWN_FILE
    {
        return Err(ExposureReplayArtifactError::Invariant(
            "published manifest does not match the frozen CREC-102 config".to_owned(),
        ));
    }
    let report_path = config.output_path.join(REPORT_FILE);
    let (report_sha256, stored) = read_hashed_json::<ThemeExposureArtifactReport>(&report_path)?;
    require_actual_hash(&report_path, &report_sha256, &manifest.report_sha256)?;
    let markdown_path = config.output_path.join(REPORT_MARKDOWN_FILE);
    let markdown = read_all(&markdown_path)?;
    require_actual_hash(
        &markdown_path,
        &hash_bytes(&markdown),
        &manifest.markdown_sha256,
    )?;
    if markdown != markdown_report(&stored).as_bytes() {
        return Err(ExposureReplayArtifactError::Invariant(
            "published Markdown does not render the published JSON report".to_owned(),
        ));
    }
    let repeated = build_report(&config, config_sha256)?;
    let stored_value = serde_json::to_value(&stored)
        .map_err(|source| json_error("compare", &report_path, source))?;
    let repeated_value = serde_json::to_value(&repeated)
        .map_err(|source| json_error("compare", &report_path, source))?;
    if let Some(difference) = first_json_difference(&stored_value, &repeated_value, "$") {
        return Err(ExposureReplayArtifactError::Invariant(difference));
    }
    Ok(stored)
}

pub fn validate_theme_exposure_replay_config(config: &ThemeExposureReplayConfig) -> Result<()> {
    enforce_crec102_contract(config)?;
    if !config.output_path.is_absolute()
        || config
            .output_path
            .components()
            .any(|component| matches!(component, Component::CurDir | Component::ParentDir))
    {
        return Err(ExposureReplayArtifactError::Invariant(
            "output path must be absolute and normalized".to_owned(),
        ));
    }
    let output = resolve_destination(&config.output_path)?;
    for protected in [
        &config.source_artifact_path,
        &config.representation_path,
        config.ordered_event_ids_path.parent().ok_or_else(|| {
            ExposureReplayArtifactError::Invariant("ordered-event-ID path has no parent".to_owned())
        })?,
    ] {
        let protected = fs::canonicalize(protected)
            .map_err(|source| io_error("canonicalize", protected, source))?;
        if output.starts_with(&protected) {
            return Err(ExposureReplayArtifactError::Invariant(format!(
                "output path `{}` is inside protected input `{}`",
                config.output_path.display(),
                protected.display()
            )));
        }
    }
    Ok(())
}

pub fn load_sealed_replay_input(
    source_artifact_path: impl AsRef<Path>,
    expected_source_report_sha256: &str,
    expected_label_seal_sha256: &str,
) -> Result<SealedReplayInput> {
    let source_artifact_path = source_artifact_path.as_ref();
    let source_report_path = source_artifact_path.join(SOURCE_REPORT_FILE);
    let source_seal_path = source_artifact_path.join(SOURCE_SEAL_FILE);
    let (source_report_sha256, source) =
        read_hashed_json::<SourceGeometryReport>(&source_report_path)?;
    require_actual_hash(
        &source_report_path,
        &source_report_sha256,
        expected_source_report_sha256,
    )?;
    let (label_seal_sha256, seal) = read_hashed_json::<SourceLabelSeal>(&source_seal_path)?;
    require_actual_hash(
        &source_seal_path,
        &label_seal_sha256,
        expected_label_seal_sha256,
    )?;
    let manifest_path = source_artifact_path.join(SOURCE_MANIFEST_FILE);
    let (manifest_sha256, manifest) = read_hashed_json::<SourcePrepareManifest>(&manifest_path)?;
    if source.diagnostic_id != SOURCE_DIAGNOSTIC_ID
        || seal.diagnostic_id != SOURCE_DIAGNOSTIC_ID
        || manifest.diagnostic_id != SOURCE_DIAGNOSTIC_ID
        || seal.schema_version != 1
        || manifest.schema_version != 1
        || source.decision != DiagnosticDecision::ProceedToExposureReplay
    {
        return Err(ExposureReplayArtifactError::Invariant(
            "source is not the approved CREC-101 artifact".to_owned(),
        ));
    }
    if source.label_seal_sha256 != expected_label_seal_sha256 {
        return Err(ExposureReplayArtifactError::Invariant(
            "source report and expected label seal differ".to_owned(),
        ));
    }
    require_actual_hash(
        &manifest_path,
        &manifest_sha256,
        &seal.prepare_manifest_sha256,
    )?;
    let blind_path = source_artifact_path.join(&manifest.blind_file);
    let key_path = source_artifact_path.join(&manifest.key_file);
    let rubric_path = source_artifact_path.join(&manifest.rubric_file);
    let (blind_sha256, blind) = read_hashed_json_lines::<SourceBlindRecord>(&blind_path)?;
    require_actual_hash(&blind_path, &blind_sha256, &manifest.blind_sha256)?;
    require_actual_hash(&blind_path, &blind_sha256, &seal.blind_sha256)?;
    let (key_sha256, key) = read_hashed_json_lines::<SourceKeyRecord>(&key_path)?;
    require_actual_hash(&key_path, &key_sha256, &manifest.key_sha256)?;
    require_actual_hash(&key_path, &key_sha256, &seal.key_sha256)?;
    require_hash(&rubric_path, &manifest.rubric_sha256)?;
    require_hash(&rubric_path, &seal.rubric_sha256)?;
    let labels_a_path = source_artifact_path.join(SOURCE_LABEL_A_FILE);
    let (labels_a_sha256, labels_a_records) =
        read_hashed_json_lines::<SourceLabelRecord>(&labels_a_path)?;
    require_actual_hash(&labels_a_path, &labels_a_sha256, &seal.labels_a_sha256)?;
    let labels_b_path = source_artifact_path.join(SOURCE_LABEL_B_FILE);
    let (labels_b_sha256, labels_b_records) =
        read_hashed_json_lines::<SourceLabelRecord>(&labels_b_path)?;
    require_actual_hash(&labels_b_path, &labels_b_sha256, &seal.labels_b_sha256)?;
    if manifest.blind_file != SOURCE_BLIND_FILE
        || manifest.key_file != SOURCE_KEY_FILE
        || manifest.rubric_file != SOURCE_RUBRIC_FILE
    {
        return Err(ExposureReplayArtifactError::Invariant(
            "source manifest names unexpected files".to_owned(),
        ));
    }

    if blind.len() != key.len()
        || blind.len() != seal.record_count
        || blind.len() != manifest.prefix_notes
        || blind.len() != source.source_prefix_notes
    {
        return Err(ExposureReplayArtifactError::Invariant(
            "source record counts differ".to_owned(),
        ));
    }
    let mut record_ids = BTreeSet::new();
    let mut ordinals = BTreeSet::new();
    let mut event_ids = BTreeSet::new();
    let mut identities = Vec::with_capacity(key.len());
    for (blind_record, key_record) in blind.iter().zip(&key) {
        if blind_record.record_id != key_record.record_id
            || !record_ids.insert(key_record.record_id.clone())
            || !ordinals.insert(key_record.presentation_ordinal)
        {
            return Err(ExposureReplayArtifactError::Invariant(
                "source blind key is not one-to-one".to_owned(),
            ));
        }
        let event_id = decode_event_id(&key_record.event_id)?;
        if !event_ids.insert(event_id) {
            return Err(ExposureReplayArtifactError::Invariant(
                "source blind key repeats an event ID".to_owned(),
            ));
        }
        identities.push(SealedReplayIdentity {
            record_id: key_record.record_id.clone(),
            presentation_ordinal: key_record.presentation_ordinal,
            event_id: key_record.event_id.clone(),
        });
    }
    let expected_ordinals = (1..=u32::try_from(key.len()).map_err(|_| {
        ExposureReplayArtifactError::Invariant("source record count does not fit u32".to_owned())
    })?)
        .collect::<BTreeSet<_>>();
    if ordinals != expected_ordinals {
        return Err(ExposureReplayArtifactError::Invariant(
            "source presentation ordinals are not exactly contiguous".to_owned(),
        ));
    }

    let raw_a = build_label_set("labeler-a", labels_a_records, &record_ids)?;
    let raw_b = build_label_set("labeler-b", labels_b_records, &record_ids)?;
    let label_sets = [
        derive_analysis_label_set(&raw_a)?,
        derive_analysis_label_set(&raw_b)?,
    ];
    Ok(SealedReplayInput {
        identities_in_blind_order: identities,
        label_sets,
        source,
        label_seal_sha256: expected_label_seal_sha256.to_owned(),
    })
}

fn publish_report(
    config: &ThemeExposureReplayConfig,
    config_sha256: String,
) -> Result<ThemeExposureArtifactReport> {
    if config.output_path.exists() {
        return Err(ExposureReplayArtifactError::ArtifactExists(
            config.output_path.clone(),
        ));
    }
    let report = build_report(config, config_sha256.clone())?;
    let parent = config.output_path.parent().ok_or_else(|| {
        ExposureReplayArtifactError::Invariant(format!(
            "output path `{}` has no parent",
            config.output_path.display()
        ))
    })?;
    fs::create_dir_all(parent).map_err(|source| io_error("create directory", parent, source))?;
    let stage = temporary_sibling(&config.output_path);
    if stage.exists() {
        return Err(ExposureReplayArtifactError::ArtifactExists(stage));
    }
    fs::create_dir(&stage).map_err(|source| io_error("create directory", &stage, source))?;
    let result = (|| {
        let report_path = stage.join(REPORT_FILE);
        let markdown_path = stage.join(REPORT_MARKDOWN_FILE);
        write_json_exclusive(&report_path, &report)?;
        write_text_exclusive(&markdown_path, &markdown_report(&report))?;
        let manifest = ArtifactManifest {
            schema_version: ARTIFACT_SCHEMA_VERSION,
            diagnostic_id: DIAGNOSTIC_ID.to_owned(),
            config_sha256,
            source_geometry_report_sha256: config.expected_source_report_sha256.clone(),
            label_seal_sha256: config.expected_label_seal_sha256.clone(),
            report_file: REPORT_FILE.to_owned(),
            report_sha256: hash_file(&report_path)?,
            markdown_file: REPORT_MARKDOWN_FILE.to_owned(),
            markdown_sha256: hash_file(&markdown_path)?,
        };
        write_json_exclusive(&stage.join(ARTIFACT_MANIFEST_FILE), &manifest)
    })();
    if let Err(error) = result {
        let _ = fs::remove_dir_all(&stage);
        return Err(error);
    }
    if let Err(error) = sync_directory(&stage) {
        let _ = fs::remove_dir_all(&stage);
        return Err(error);
    }
    if let Err(error) = rename_no_replace(&stage, &config.output_path) {
        let _ = fs::remove_dir_all(&stage);
        return Err(error);
    }
    sync_parent(&config.output_path)?;
    Ok(report)
}

fn build_report(
    config: &ThemeExposureReplayConfig,
    config_sha256: String,
) -> Result<ThemeExposureArtifactReport> {
    require_hash(
        &config.ordered_event_ids_path,
        &config.expected_ordered_event_ids_sha256,
    )?;
    let input = load_sealed_replay_input(
        &config.source_artifact_path,
        &config.expected_source_report_sha256,
        &config.expected_label_seal_sha256,
    )?;
    if input.source.source_prefix_notes != EXPECTED_SOURCE_NOTES
        || input.source.ordered_event_ids_sha256 != config.expected_ordered_event_ids_sha256
        || input.source.representation_version != config.representation_version
        || input.source.vector_set_sha256 != config.expected_vector_set_sha256
    {
        return Err(ExposureReplayArtifactError::Invariant(
            "source report does not match the frozen representation".to_owned(),
        ));
    }
    let event_ids = input
        .identities_in_blind_order
        .iter()
        .map(|identity| decode_event_id(&identity.event_id))
        .collect::<Result<Vec<_>>>()?;
    let vector_response = vectors_for_notes(
        &config.ordered_event_ids_path,
        &config.representation_path,
        &event_ids,
        &config.representation_version,
    )?;
    if !vector_response.complete
        || vector_response.vectors.len() != event_ids.len()
        || vector_response.representation_version != config.representation_version
        || vector_response.represented_rows != input.source.represented_rows
        || vector_response.total_rows != input.source.represented_rows
    {
        return Err(ExposureReplayArtifactError::Invariant(
            "stored vector response is incomplete or identifies another representation".to_owned(),
        ));
    }
    if hash_vector_set(&input.identities_in_blind_order, &vector_response.vectors)
        != config.expected_vector_set_sha256
    {
        return Err(ExposureReplayArtifactError::Invariant(
            "stored vector set differs from the CREC-101 vector set".to_owned(),
        ));
    }

    let mut chronological = input
        .identities_in_blind_order
        .iter()
        .cloned()
        .zip(vector_response.vectors)
        .map(|(identity, stored)| {
            let expected_event_id = decode_event_id(&identity.event_id)?;
            if stored.event_id != expected_event_id
                || stored.vector.len() != input.source.vector_dimension
            {
                return Err(ExposureReplayArtifactError::Invariant(
                    "stored vector is outside the requested identity or dimension".to_owned(),
                ));
            }
            let note = ThemeNote::new(identity.record_id.clone(), stored.vector)?;
            Ok((identity, note))
        })
        .collect::<Result<Vec<_>>>()?;
    chronological.sort_unstable_by_key(|(identity, _)| identity.presentation_ordinal);
    let chronology = chronological
        .iter()
        .map(|(identity, _)| identity.clone())
        .collect::<Vec<_>>();
    let notes = chronological
        .into_iter()
        .map(|(_, note)| note)
        .collect::<Vec<_>>();
    let settings = ExposureReplaySettings::new(
        config.minimum_family_notes,
        config.primary_half_life,
        config.sensitivity_half_lives,
        config.permutations,
        &config.permutation_seed,
    )?;
    let replay = analyze_exposure_replay(&notes, &input.label_sets, &settings)?;
    Ok(ThemeExposureArtifactReport {
        schema_version: ARTIFACT_SCHEMA_VERSION,
        diagnostic_id: DIAGNOSTIC_ID.to_owned(),
        mechanism_check_only: true,
        config_sha256,
        source_geometry_report_sha256: config.expected_source_report_sha256.clone(),
        label_seal_sha256: input.label_seal_sha256,
        ordered_event_ids_sha256: config.expected_ordered_event_ids_sha256.clone(),
        representation_version: config.representation_version.clone(),
        represented_rows: input.source.represented_rows,
        vector_dimension: input.source.vector_dimension,
        vector_set_sha256: config.expected_vector_set_sha256.clone(),
        chronology,
        exposure_formula:
            "sum(i<t) 2^(-(t-i)/H) * max(0, cosine(v_t,v_i)-median_all_140_pair_cosines)"
                .to_owned(),
        null_policy: "keep labels and chronology fixed; shuffle complete document-vector identities across presentation positions once per draw"
            .to_owned(),
        interpretation_boundary: "A pass means only that this vector score tracks recent broad-theme recurrence on this frozen sequence. It does not establish human saturation, a live threshold, improved recommendations, or candidate availability."
            .to_owned(),
        replay,
    })
}

fn build_label_set(
    name: &str,
    records: Vec<SourceLabelRecord>,
    expected_ids: &BTreeSet<String>,
) -> Result<ThemeLabelSet> {
    let mut labels = BTreeMap::new();
    for record in records {
        if record.themes.contains(&Theme::Cryptocurrency) {
            return Err(ExposureReplayArtifactError::Invariant(format!(
                "{name} contains the derived cryptocurrency family"
            )));
        }
        if labels
            .insert(record.record_id.clone(), record.themes)
            .is_some()
        {
            return Err(ExposureReplayArtifactError::Invariant(format!(
                "{name} repeats record {}",
                record.record_id
            )));
        }
    }
    if labels.keys().collect::<BTreeSet<_>>() != expected_ids.iter().collect::<BTreeSet<_>>() {
        return Err(ExposureReplayArtifactError::Invariant(format!(
            "{name} does not exactly cover the sealed source"
        )));
    }
    ThemeLabelSet::new(name, labels).map_err(Into::into)
}

fn enforce_crec102_contract(config: &ThemeExposureReplayConfig) -> Result<()> {
    if config.expected_source_report_sha256 != EXPECTED_SOURCE_REPORT_SHA256
        || config.expected_label_seal_sha256 != EXPECTED_LABEL_SEAL_SHA256
        || config.expected_ordered_event_ids_sha256 != EXPECTED_ORDERED_EVENT_IDS_SHA256
        || config.representation_version != EXPECTED_REPRESENTATION_VERSION
        || config.expected_vector_set_sha256 != EXPECTED_VECTOR_SET_SHA256
        || config.minimum_family_notes != EXPECTED_MINIMUM_FAMILY_NOTES
        || config.primary_half_life != EXPECTED_PRIMARY_HALF_LIFE
        || config.sensitivity_half_lives != EXPECTED_SENSITIVITY_HALF_LIVES
        || config.permutations != EXPECTED_PERMUTATIONS
        || config.permutation_seed != EXPECTED_PERMUTATION_SEED
    {
        return Err(ExposureReplayArtifactError::Invariant(
            "config does not match the frozen CREC-102 contract".to_owned(),
        ));
    }
    Ok(())
}

fn resolve_destination(path: &Path) -> Result<PathBuf> {
    let mut existing = path;
    let mut missing = Vec::new();
    while !existing.exists() {
        let name = existing.file_name().ok_or_else(|| {
            ExposureReplayArtifactError::Invariant(format!(
                "cannot resolve output path `{}`",
                path.display()
            ))
        })?;
        missing.push(name.to_owned());
        existing = existing.parent().ok_or_else(|| {
            ExposureReplayArtifactError::Invariant(format!(
                "cannot resolve output path `{}`",
                path.display()
            ))
        })?;
    }
    let mut resolved =
        fs::canonicalize(existing).map_err(|source| io_error("canonicalize", existing, source))?;
    for component in missing.into_iter().rev() {
        resolved.push(component);
    }
    Ok(resolved)
}

fn hash_vector_set(identities: &[SealedReplayIdentity], vectors: &[StoredNoteVector]) -> String {
    let mut digest = Sha256::new();
    digest.update(b"oracle-mvp-theme-geometry-vector-set-v1\0");
    for (identity, stored) in identities.iter().zip(vectors) {
        digest.update((identity.record_id.len() as u64).to_le_bytes());
        digest.update(identity.record_id.as_bytes());
        digest.update(stored.event_id);
        digest.update((stored.vector.len() as u64).to_le_bytes());
        for coordinate in &stored.vector {
            digest.update(coordinate.to_le_bytes());
        }
    }
    encode_hex(&digest.finalize())
}

fn markdown_report(report: &ThemeExposureArtifactReport) -> String {
    let mut output = format!(
        "# CREC-102 Cumulative Theme-Exposure Replay\n\n\
         This is a mechanism check, not a recommendation-quality result.\n\n\
         - Decision: `{:?}`\n\
         - Presentations: {}\n\
         - Representation: `{}`\n\
         - Typical pair cosine: {:.6}\n\
         - Primary half-life: {}\n\
         - Sensitivity half-lives: {:?}\n\
         - Vector-identity permutations: {}\n\
         - Common significant families: {:?}\n\n",
        report.replay.decision,
        report.replay.note_count,
        report.representation_version,
        report.replay.typical_pair_cosine,
        report.replay.primary_half_life,
        report.replay.sensitivity_half_lives,
        report.replay.permutations,
        report.replay.common_primary_significant_families,
    );
    for label_set in &report.replay.label_sets {
        output.push_str(&format!(
            "## {}\n\n- Primary macro Spearman: {}\n- Macro valid null draws: {}/{}\n- Macro null 95th percentile: {}\n- Macro p-value: {}\n- Macro above null: {}\n\n",
            label_set.label_set,
            optional_metric(label_set.primary.macro_spearman),
            label_set.primary.macro_permutation_valid_draws,
            report.replay.permutations,
            optional_metric(label_set.primary.macro_permutation_95th_percentile),
            optional_metric(label_set.primary.macro_permutation_p_value),
            label_set.primary.macro_above_permutation_95th_percentile,
        ));
        for (family, metric) in &label_set.primary.family_metrics {
            output.push_str(&format!(
                "- `{:?}`: n={}, rho={}, valid_null={}/{}, null95={}, p={}, significant={}\n",
                family,
                metric.labeled_notes,
                optional_metric(metric.spearman),
                metric.permutation_valid_draws,
                report.replay.permutations,
                optional_metric(metric.permutation_95th_percentile),
                optional_metric(metric.permutation_p_value),
                metric.above_permutation_95th_percentile,
            ));
        }
        output.push('\n');
        for (half_life, sensitivity) in &label_set.sensitivities {
            output.push_str(&format!(
                "- H={half_life} sensitivity macro rho: {}\n",
                optional_metric(sensitivity.macro_spearman)
            ));
            for (family, metric) in &sensitivity.family_metrics {
                output.push_str(&format!(
                    "  - `{:?}` rho: {}\n",
                    family,
                    optional_metric(metric.spearman)
                ));
            }
        }
        output.push('\n');
    }
    output.push_str("## Interpretation Boundary\n\n");
    output.push_str(&report.interpretation_boundary);
    output.push('\n');
    output
}

fn optional_metric(value: Option<f64>) -> String {
    value
        .map(|value| format!("{value:.4}"))
        .unwrap_or_else(|| "n/a".to_owned())
}

fn first_json_difference(
    stored: &serde_json::Value,
    repeated: &serde_json::Value,
    path: &str,
) -> Option<String> {
    match (stored, repeated) {
        (serde_json::Value::Object(stored), serde_json::Value::Object(repeated)) => {
            for key in stored
                .keys()
                .chain(repeated.keys())
                .collect::<BTreeSet<_>>()
            {
                let next = format!("{path}.{key}");
                match (stored.get(key), repeated.get(key)) {
                    (Some(stored), Some(repeated)) => {
                        if let Some(difference) = first_json_difference(stored, repeated, &next) {
                            return Some(difference);
                        }
                    }
                    _ => return Some(format!("{next} exists in only one replay")),
                }
            }
            None
        }
        (serde_json::Value::Array(stored), serde_json::Value::Array(repeated)) => {
            if stored.len() != repeated.len() {
                return Some(format!(
                    "{path} length differs: stored {}, repeated {}",
                    stored.len(),
                    repeated.len()
                ));
            }
            for (index, (stored, repeated)) in stored.iter().zip(repeated).enumerate() {
                if let Some(difference) =
                    first_json_difference(stored, repeated, &format!("{path}[{index}]"))
                {
                    return Some(difference);
                }
            }
            None
        }
        (serde_json::Value::Number(stored), serde_json::Value::Number(repeated))
            if stored.is_f64() && repeated.is_f64() =>
        {
            let stored = stored.as_f64().expect("f64 JSON number");
            let repeated = repeated.as_f64().expect("f64 JSON number");
            let tolerance = 8.0 * f64::EPSILON * stored.abs().max(repeated.abs()).max(1.0);
            if (stored - repeated).abs() <= tolerance {
                None
            } else {
                Some(format!(
                    "{path} differs beyond floating tolerance: stored {stored}, repeated {repeated}"
                ))
            }
        }
        _ if stored == repeated => None,
        _ => Some(format!(
            "{path} differs: stored {stored}, repeated {repeated}"
        )),
    }
}

fn read_json<T: for<'de> Deserialize<'de>>(path: &Path) -> Result<T> {
    let file = File::open(path).map_err(|source| io_error("open", path, source))?;
    serde_json::from_reader(BufReader::new(file)).map_err(|source| json_error("read", path, source))
}

fn read_hashed_json<T: for<'de> Deserialize<'de>>(path: &Path) -> Result<(String, T)> {
    let bytes = read_all(path)?;
    let hash = hash_bytes(&bytes);
    let value =
        serde_json::from_slice(&bytes).map_err(|source| json_error("read", path, source))?;
    Ok((hash, value))
}

fn read_hashed_json_lines<T: for<'de> Deserialize<'de>>(path: &Path) -> Result<(String, Vec<T>)> {
    let bytes = read_all(path)?;
    let hash = hash_bytes(&bytes);
    let values = BufReader::new(io::Cursor::new(&bytes))
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
        .collect::<Result<Vec<_>>>()?;
    Ok((hash, values))
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
                ExposureReplayArtifactError::ArtifactExists(path.to_owned())
            } else {
                io_error("create", path, source)
            }
        })
}

fn temporary_sibling(path: &Path) -> PathBuf {
    let name = path
        .file_name()
        .and_then(|name| name.to_str())
        .unwrap_or("theme-exposure");
    path.with_file_name(format!(".{name}.tmp-{}", std::process::id()))
}

fn sync_parent(path: &Path) -> Result<()> {
    let parent = path.parent().ok_or_else(|| {
        ExposureReplayArtifactError::Invariant(format!(
            "artifact path `{}` has no parent",
            path.display()
        ))
    })?;
    sync_directory(parent)
}

fn sync_directory(path: &Path) -> Result<()> {
    File::open(path)
        .and_then(|directory| directory.sync_all())
        .map_err(|source| io_error("sync directory", path, source))
}

fn rename_no_replace(source: &Path, destination: &Path) -> Result<()> {
    let source_bytes = CString::new(source.as_os_str().as_bytes()).map_err(|_| {
        ExposureReplayArtifactError::Invariant(format!(
            "staging path `{}` contains a null byte",
            source.display()
        ))
    })?;
    let destination_bytes = CString::new(destination.as_os_str().as_bytes()).map_err(|_| {
        ExposureReplayArtifactError::Invariant(format!(
            "output path `{}` contains a null byte",
            destination.display()
        ))
    })?;
    // SAFETY: both C strings remain alive for the call and point to
    // null-terminated path bytes. RENAME_NOREPLACE makes publication atomic
    // without replacing a concurrently created artifact.
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
    let source = io::Error::last_os_error();
    if source.kind() == io::ErrorKind::AlreadyExists {
        Err(ExposureReplayArtifactError::ArtifactExists(
            destination.to_owned(),
        ))
    } else {
        Err(io_error("publish", destination, source))
    }
}

fn hash_file(path: &Path) -> Result<String> {
    let mut file = File::open(path).map_err(|source| {
        if source.kind() == io::ErrorKind::NotFound {
            ExposureReplayArtifactError::ArtifactMissing(path.to_owned())
        } else {
            io_error("open", path, source)
        }
    })?;
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

fn read_all(path: &Path) -> Result<Vec<u8>> {
    fs::read(path).map_err(|source| {
        if source.kind() == io::ErrorKind::NotFound {
            ExposureReplayArtifactError::ArtifactMissing(path.to_owned())
        } else {
            io_error("read", path, source)
        }
    })
}

fn hash_bytes(bytes: &[u8]) -> String {
    encode_hex(&Sha256::digest(bytes))
}

fn require_hash(path: &Path, expected: &str) -> Result<()> {
    let actual = hash_file(path)?;
    require_actual_hash(path, &actual, expected)
}

fn require_actual_hash(path: &Path, actual: &str, expected: &str) -> Result<()> {
    if actual == expected {
        Ok(())
    } else {
        Err(ExposureReplayArtifactError::HashMismatch {
            path: path.to_owned(),
            expected: expected.to_owned(),
            actual: actual.to_owned(),
        })
    }
}

fn decode_event_id(value: &str) -> Result<EventId> {
    if value.len() != 64 {
        return Err(ExposureReplayArtifactError::InvalidEventId(
            value.to_owned(),
        ));
    }
    let mut id = [0_u8; 32];
    for (index, byte) in id.iter_mut().enumerate() {
        *byte = u8::from_str_radix(&value[index * 2..index * 2 + 2], 16)
            .map_err(|_| ExposureReplayArtifactError::InvalidEventId(value.to_owned()))?;
    }
    Ok(id)
}

fn encode_hex(bytes: &[u8]) -> String {
    let mut output = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        use std::fmt::Write as _;
        write!(&mut output, "{byte:02x}").expect("writing to String cannot fail");
    }
    output
}

fn io_error(
    operation: &'static str,
    path: &Path,
    source: io::Error,
) -> ExposureReplayArtifactError {
    ExposureReplayArtifactError::Io {
        operation,
        path: path.to_owned(),
        source,
    }
}

fn json_error(
    operation: &'static str,
    path: &Path,
    source: serde_json::Error,
) -> ExposureReplayArtifactError {
    ExposureReplayArtifactError::Json {
        operation,
        path: path.to_owned(),
        source,
    }
}
