//! Frozen, order-independent sample for the scaled semantic-map experiment.

use std::cmp::Ordering;
use std::collections::{BTreeSet, BinaryHeap};
use std::ffi::{CString, OsString};
use std::fs::{self, File, OpenOptions};
use std::io::{BufReader, BufWriter, Read, Write};
use std::os::unix::ffi::OsStrExt;
use std::os::unix::fs::{MetadataExt, symlink};
use std::path::{Path, PathBuf};

use lmdb::{Cursor, Database, Environment, EnvironmentFlags, Transaction as LmdbTransaction};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use thiserror::Error;

use crate::english_filter::{
    CLASSIFICATION_POLICY, GLOTLID_V3_REPOSITORY_COMMIT, GLOTLID_V3_SHA256, NORMALIZATION_POLICY,
    classifier_input,
};

const SCHEMA_VERSION: u32 = 1;
const EVENT_ID_BYTES: usize = 32;
const NDB_NOTE_MINIMUM_BYTES: usize = 160;
const NDB_NOTE_ID_OFFSET: usize = 4;
const NDB_NOTE_CONTENT_LENGTH_OFFSET: usize = 144;
const NDB_NOTE_CONTENT_OFFSET: usize = 148;
const NDB_NOTE_STRINGS_OFFSET: usize = 152;
const NDB_PACKED_STR: u8 = 1;
const NDB_MAP_SIZE: usize = 256 * 1_024 * 1_024 * 1_024;
const MANIFEST_FILE: &str = "manifest.json";
const ORDERED_EVENT_IDS_FILE: &str = "ordered-event-ids.bin";
const ORDERED_EVENT_IDS_CHECKSUM_FILE: &str = "ordered-event-ids.sha256";
const RUNTIME_NDB_DIRECTORY: &str = ".runtime-ndb";
const SELECTION_DOMAIN: &[u8] = b"oracle-mvp/scaled-semantic-map-sample/v1\0";

/// Exact deterministic selection rule frozen by CREC-120.
pub const SELECTION_RULE: &str =
    "bottom-domain-separated-sha256-then-event-id-over-usable-fresh-english-event-ids-v1";
/// Complete frozen sample size.
pub const SAMPLE_ROWS: usize = 1_000;
/// Prefix consumed by the initial scaled run.
pub const INITIAL_SAMPLE_ROWS: usize = 500;

type EventId = [u8; EVENT_ID_BYTES];

/// Inputs for one CREC-120 sample derivation.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SemanticMapSampleConfig {
    /// Sealed NostrDB containing every event addressed by the English order.
    pub source_corpus_path: PathBuf,
    /// Complete English-eligible event-ID order from the fresh publication.
    pub source_ordered_event_ids_path: PathBuf,
    /// Manifest binding the English order to its sealed source.
    pub source_manifest_path: PathBuf,
    /// Create-once output artifact directory.
    pub output_path: PathBuf,
}

/// Identity of one file used or produced by the derivation.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SemanticMapSampleFile {
    /// Stable artifact-relative filename.
    pub file: String,
    /// Complete fixed-width record count, or zero for a non-record file.
    pub records: u64,
    /// Complete file length.
    pub bytes: u64,
    /// SHA-256 over the complete file.
    pub sha256: String,
}

/// Frozen sample identity and complete selection accounting.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SemanticMapSampleManifest {
    /// Artifact schema version.
    pub schema_version: u32,
    /// Exact deterministic selection rule.
    pub selection_rule: String,
    /// Domain supplied before each event ID when deriving its selection key.
    pub selection_domain: String,
    /// Existing normalization used only to decide whether usable text remains.
    pub usable_text_normalization_policy: String,
    /// Source language policy already applied by the publication.
    pub source_classification_policy: String,
    /// Exact source English-manifest file.
    pub source_manifest: SemanticMapSampleFile,
    /// Declared identity of the sealed source NostrDB data.
    pub declared_source_ndb_data_sha256: String,
    /// Declared identity of the source derivation ledger.
    pub source_derivation_ledger_sha256: String,
    /// Declared identity of the source deduplication manifest.
    pub source_dedup_manifest_sha256: String,
    /// Declared identity of the ordered IDs before English filtering.
    pub source_pre_english_ordered_event_ids_sha256: String,
    /// Exact complete English-eligible ordered-ID identity.
    pub source_english_ordered_event_ids_sha256: String,
    /// English-eligible IDs examined exactly once.
    pub scanned_english_events: u64,
    /// Notes whose temporary normalized input retained usable text.
    pub usable_text_events: u64,
    /// Notes omitted because the temporary normalized input was empty.
    pub excluded_no_usable_text: u64,
    /// Notes retained in the frozen output.
    pub selected_events: u64,
    /// Prefix rows reserved for the initial run.
    pub initial_rows: u64,
    /// Suffix rows reserved for the fixed extension.
    pub extension_rows: u64,
    /// Frozen ordered event-ID output.
    pub ordered_event_ids: SemanticMapSampleFile,
}

/// A deterministic sample derivation or verification failure.
#[derive(Debug, Error)]
pub enum SemanticMapSampleError {
    /// A filesystem operation failed.
    #[error("failed to {operation} `{path}`: {source}")]
    Io {
        /// Operation being attempted.
        operation: &'static str,
        /// Relevant path.
        path: PathBuf,
        /// Underlying error.
        #[source]
        source: std::io::Error,
    },

    /// JSON could not be decoded or encoded.
    #[error("failed to {operation} JSON `{path}`: {source}")]
    Json {
        /// Operation being attempted.
        operation: &'static str,
        /// Relevant path.
        path: PathBuf,
        /// Underlying error.
        #[source]
        source: serde_json::Error,
    },

    /// Read-only LMDB access failed.
    #[error("read-only NostrDB access failed: {0}")]
    Lmdb(#[from] lmdb::Error),

    /// An input or output violated the frozen contract.
    #[error("semantic-map sample invariant failed: {0}")]
    Invariant(String),

    /// A create-once output or interrupted stage already exists.
    #[error("semantic-map sample output already exists: {0}")]
    OutputExists(PathBuf),

    /// An interrupted create-once stage requires explicit inspection.
    #[error("incomplete semantic-map sample stage exists: {0}")]
    IncompleteStage(PathBuf),
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct FreshEnglishManifest {
    schema_version: u32,
    source_ordered_event_ids_sha256: String,
    source_ndb_data_sha256: String,
    source_derivation_ledger_sha256: String,
    source_dedup_manifest_sha256: String,
    model_sha256: String,
    model_repository_commit: String,
    normalization_policy: String,
    classification_policy: String,
    input_events: u64,
    retained_events: u64,
    excluded_events: u64,
    output_ordered_event_ids_sha256: String,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct SelectedId {
    key: [u8; 32],
    id: EventId,
}

impl Ord for SelectedId {
    fn cmp(&self, other: &Self) -> Ordering {
        self.key.cmp(&other.key).then(self.id.cmp(&other.id))
    }
}

impl PartialOrd for SelectedId {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct FileState {
    device: u64,
    inode: u64,
    bytes: u64,
    modified_seconds: i64,
    modified_nanoseconds: i64,
}

struct ReadOnlyCorpus {
    environment: Environment,
    note_id: Database,
    note: Database,
}

struct SelectionResult {
    selected: Vec<EventId>,
    source_ordered_sha256: String,
    scanned_events: u64,
    usable_events: u64,
    excluded_no_usable_text: u64,
}

/// Build and atomically publish the frozen CREC-120 sample.
pub fn freeze_semantic_map_sample(
    config: &SemanticMapSampleConfig,
) -> Result<SemanticMapSampleManifest, SemanticMapSampleError> {
    validate_config(config)?;
    if config.output_path.exists() {
        return verify_semantic_map_sample(config);
    }

    let parent = config
        .output_path
        .parent()
        .unwrap_or_else(|| Path::new("."));
    fs::create_dir_all(parent).map_err(|source| io_error("create", parent, source))?;
    let stage = stage_path(&config.output_path)?;
    match fs::create_dir(&stage) {
        Ok(()) => {}
        Err(source) if source.kind() == std::io::ErrorKind::AlreadyExists => {
            return Err(SemanticMapSampleError::IncompleteStage(stage));
        }
        Err(source) => return Err(io_error("create", &stage, source)),
    }

    let result = freeze_in_stage(config, &stage);
    let manifest = match result {
        Ok(manifest) => manifest,
        Err(error) => {
            let _ = fs::remove_dir_all(&stage);
            return Err(error);
        }
    };
    publish_no_replace(&stage, &config.output_path)?;
    sync_directory(parent)?;
    Ok(manifest)
}

/// Deeply verify an existing sample against the frozen source population.
pub fn verify_semantic_map_sample(
    config: &SemanticMapSampleConfig,
) -> Result<SemanticMapSampleManifest, SemanticMapSampleError> {
    validate_config(config)?;
    let manifest_path = config.output_path.join(MANIFEST_FILE);
    verify_output_entries(&config.output_path)?;
    let manifest = read_json::<SemanticMapSampleManifest>(&manifest_path)?;
    validate_output_manifest(&manifest)?;

    let runtime = verification_runtime_path(&config.output_path)?;
    if runtime.exists() {
        return Err(SemanticMapSampleError::IncompleteStage(runtime));
    }
    fs::create_dir(&runtime).map_err(|source| io_error("create", &runtime, source))?;
    let result = derive_expected(config, &runtime);
    let cleanup = fs::remove_dir_all(&runtime);
    let (source, fresh, selection) = result?;
    cleanup.map_err(|source| io_error("remove", &runtime, source))?;
    let expected = expected_manifest(source, &fresh, &selection, None)?;

    let output_ordered_path = config.output_path.join(ORDERED_EVENT_IDS_FILE);
    let output_file = file_manifest(&output_ordered_path, SAMPLE_ROWS as u64)?;
    let expected = SemanticMapSampleManifest {
        ordered_event_ids: output_file.clone(),
        ..expected
    };
    if manifest != expected {
        return Err(SemanticMapSampleError::Invariant(
            "stored manifest does not match the frozen source and selection".to_owned(),
        ));
    }
    if read_event_ids(&output_ordered_path)? != selection.selected {
        return Err(SemanticMapSampleError::Invariant(
            "stored event-ID order does not match the recomputed selection".to_owned(),
        ));
    }
    verify_checksum_sidecar(
        &config.output_path.join(ORDERED_EVENT_IDS_CHECKSUM_FILE),
        &output_file.sha256,
    )?;
    Ok(manifest)
}

fn freeze_in_stage(
    config: &SemanticMapSampleConfig,
    stage: &Path,
) -> Result<SemanticMapSampleManifest, SemanticMapSampleError> {
    let runtime = stage.join(RUNTIME_NDB_DIRECTORY);
    fs::create_dir(&runtime).map_err(|source| io_error("create", &runtime, source))?;
    let (source_manifest, fresh, selection) = derive_expected(config, &runtime)?;
    fs::remove_dir_all(&runtime).map_err(|source| io_error("remove", &runtime, source))?;

    let output_ordered_path = stage.join(ORDERED_EVENT_IDS_FILE);
    write_event_ids(&output_ordered_path, &selection.selected)?;
    let output_file = file_manifest(&output_ordered_path, SAMPLE_ROWS as u64)?;
    write_checksum_sidecar(
        &stage.join(ORDERED_EVENT_IDS_CHECKSUM_FILE),
        &output_file.sha256,
    )?;
    let manifest = expected_manifest(source_manifest, &fresh, &selection, Some(output_file))?;
    write_json(&stage.join(MANIFEST_FILE), &manifest)?;
    verify_stage(stage, &manifest, &selection.selected)?;
    sync_directory(stage)?;
    Ok(manifest)
}

fn derive_expected(
    config: &SemanticMapSampleConfig,
    runtime: &Path,
) -> Result<(SemanticMapSampleFile, FreshEnglishManifest, SelectionResult), SemanticMapSampleError>
{
    let source_data_path = config.source_corpus_path.join("data.mdb");
    let source_before = file_state(&source_data_path)?;
    let ordered_before = file_state(&config.source_ordered_event_ids_path)?;
    let manifest_before = file_state(&config.source_manifest_path)?;
    let source_manifest_bytes = fs::read(&config.source_manifest_path)
        .map_err(|source| io_error("read", &config.source_manifest_path, source))?;
    let fresh: FreshEnglishManifest = serde_json::from_slice(&source_manifest_bytes)
        .map_err(|source| json_error("decode", &config.source_manifest_path, source))?;
    validate_source_manifest(&fresh)?;
    let source_manifest = SemanticMapSampleFile {
        file: MANIFEST_FILE.to_owned(),
        records: 0,
        bytes: source_manifest_bytes.len() as u64,
        sha256: sha256_bytes(&source_manifest_bytes),
    };

    let source_ndb_data_sha256 = sha256_file(&source_data_path)?;
    if source_ndb_data_sha256 != fresh.source_ndb_data_sha256 {
        return Err(SemanticMapSampleError::Invariant(format!(
            "source NostrDB data SHA-256 is {source_ndb_data_sha256}; manifest declares {}",
            fresh.source_ndb_data_sha256
        )));
    }
    let canonical_data = fs::canonicalize(&source_data_path)
        .map_err(|source| io_error("resolve", &source_data_path, source))?;
    symlink(&canonical_data, runtime.join("data.mdb"))
        .map_err(|source| io_error("link", runtime.join("data.mdb"), source))?;

    let selection = select_from_source(
        runtime,
        &config.source_ordered_event_ids_path,
        fresh.retained_events,
    )?;
    if selection.source_ordered_sha256 != fresh.output_ordered_event_ids_sha256 {
        return Err(SemanticMapSampleError::Invariant(format!(
            "source English ordered-ID SHA-256 is {}; manifest declares {}",
            selection.source_ordered_sha256, fresh.output_ordered_event_ids_sha256
        )));
    }
    require_same_file(
        "source NostrDB data",
        source_before,
        file_state(&source_data_path)?,
    )?;
    require_same_file(
        "source English ordered IDs",
        ordered_before,
        file_state(&config.source_ordered_event_ids_path)?,
    )?;
    require_same_file(
        "source English manifest",
        manifest_before,
        file_state(&config.source_manifest_path)?,
    )?;
    Ok((source_manifest, fresh, selection))
}

fn select_from_source(
    runtime: &Path,
    ordered_path: &Path,
    expected_events: u64,
) -> Result<SelectionResult, SemanticMapSampleError> {
    let corpus = open_read_only_corpus(runtime)?;
    let transaction = corpus.environment.begin_ro_txn()?;
    let mut note_id_cursor = transaction.open_ro_cursor(corpus.note_id)?;
    let mut ordered = BufReader::new(
        File::open(ordered_path).map_err(|source| io_error("open", ordered_path, source))?,
    );
    let mut ordered_hasher = Sha256::new();
    let mut selected = BinaryHeap::<SelectedId>::with_capacity(SAMPLE_ROWS);
    let mut scanned_events = 0_u64;
    let mut usable_events = 0_u64;
    let mut excluded_no_usable_text = 0_u64;

    while scanned_events < expected_events {
        let id = read_event_id(&mut ordered, ordered_path)?;
        ordered_hasher.update(id);
        let content = load_content(&transaction, &mut note_id_cursor, corpus.note, id)?;
        scanned_events = increment(scanned_events, "scanned event count")?;
        if classifier_input(content).is_empty() {
            excluded_no_usable_text =
                increment(excluded_no_usable_text, "no-usable-text exclusion count")?;
            continue;
        }
        usable_events = increment(usable_events, "usable-text event count")?;
        let candidate = SelectedId {
            key: selection_key(&id),
            id,
        };
        if selected.len() < SAMPLE_ROWS {
            selected.push(candidate);
        } else if selected.peek().is_some_and(|largest| candidate < *largest) {
            selected.pop();
            selected.push(candidate);
        }
    }
    let mut trailing = [0_u8; 1];
    if ordered
        .read(&mut trailing)
        .map_err(|source| io_error("read", ordered_path, source))?
        != 0
    {
        return Err(SemanticMapSampleError::Invariant(format!(
            "source ordered-ID file contains more than {expected_events} records"
        )));
    }
    if usable_events.checked_add(excluded_no_usable_text) != Some(scanned_events) {
        return Err(SemanticMapSampleError::Invariant(
            "usable and excluded counts do not account for every source event".to_owned(),
        ));
    }
    if selected.len() != SAMPLE_ROWS {
        return Err(SemanticMapSampleError::Invariant(format!(
            "source contains only {usable_events} notes with usable text; {SAMPLE_ROWS} required"
        )));
    }
    let mut selected = selected.into_vec();
    selected.sort_unstable();
    let selected = selected.into_iter().map(|candidate| candidate.id).collect();
    Ok(SelectionResult {
        selected,
        source_ordered_sha256: format!("{:x}", ordered_hasher.finalize()),
        scanned_events,
        usable_events,
        excluded_no_usable_text,
    })
}

fn load_content<'transaction>(
    transaction: &'transaction lmdb::RoTransaction<'_>,
    cursor: &mut lmdb::RoCursor<'transaction>,
    note_database: Database,
    event_id: EventId,
) -> Result<&'transaction str, SemanticMapSampleError> {
    let mut low_key = [0_u8; EVENT_ID_BYTES + 8];
    low_key[..EVENT_ID_BYTES].copy_from_slice(&event_id);
    let (stored_key, primary_key) = cursor.get(Some(&low_key), None, 17)?;
    let stored_key = stored_key.unwrap_or(&low_key);
    if stored_key.len() != low_key.len() || stored_key[..EVENT_ID_BYTES] != event_id {
        return Err(SemanticMapSampleError::Invariant(format!(
            "event {} is absent from the source NostrDB",
            hex(&event_id)
        )));
    }
    if primary_key.len() != 8 {
        return Err(SemanticMapSampleError::Invariant(format!(
            "event {} has a malformed NostrDB primary key",
            hex(&event_id)
        )));
    }
    let note = transaction.get(note_database, &primary_key)?;
    decode_stored_content(note, event_id)
}

fn decode_stored_content(
    note: &[u8],
    expected_event_id: EventId,
) -> Result<&str, SemanticMapSampleError> {
    if note.len() < NDB_NOTE_MINIMUM_BYTES || note[0] != 1 {
        return Err(SemanticMapSampleError::Invariant(
            "source NostrDB returned an incompatible stored note".to_owned(),
        ));
    }
    let stored_event_id: EventId = note[NDB_NOTE_ID_OFFSET..NDB_NOTE_ID_OFFSET + EVENT_ID_BYTES]
        .try_into()
        .expect("validated note header");
    if stored_event_id != expected_event_id {
        return Err(SemanticMapSampleError::Invariant(format!(
            "source NostrDB returned {} for requested event {}",
            hex(&stored_event_id),
            hex(&expected_event_id)
        )));
    }
    let kind = u32::from_le_bytes(note[140..144].try_into().expect("validated note header"));
    if kind != 1 {
        return Err(SemanticMapSampleError::Invariant(format!(
            "source NostrDB returned kind {kind} for event {}",
            hex(&expected_event_id)
        )));
    }
    let content_length = usize::try_from(u32::from_le_bytes(
        note[NDB_NOTE_CONTENT_LENGTH_OFFSET..NDB_NOTE_CONTENT_LENGTH_OFFSET + 4]
            .try_into()
            .expect("validated note header"),
    ))
    .expect("u32 fits usize");
    let descriptor = &note[NDB_NOTE_CONTENT_OFFSET..NDB_NOTE_CONTENT_OFFSET + 4];
    let content = if descriptor[3] == NDB_PACKED_STR {
        if content_length > 3 {
            return Err(SemanticMapSampleError::Invariant(format!(
                "event {} has an invalid packed content length",
                hex(&expected_event_id)
            )));
        }
        &descriptor[..content_length]
    } else {
        let relative = usize::try_from(
            u32::from_le_bytes(descriptor.try_into().expect("content descriptor")) & 0x00ff_ffff,
        )
        .expect("24-bit offset fits usize");
        let strings = usize::try_from(u32::from_le_bytes(
            note[NDB_NOTE_STRINGS_OFFSET..NDB_NOTE_STRINGS_OFFSET + 4]
                .try_into()
                .expect("validated note header"),
        ))
        .expect("u32 fits usize");
        let start = strings.checked_add(relative).ok_or_else(|| {
            SemanticMapSampleError::Invariant(format!(
                "event {} content offset overflowed",
                hex(&expected_event_id)
            ))
        })?;
        let end = start.checked_add(content_length).ok_or_else(|| {
            SemanticMapSampleError::Invariant(format!(
                "event {} content length overflowed",
                hex(&expected_event_id)
            ))
        })?;
        note.get(start..end).ok_or_else(|| {
            SemanticMapSampleError::Invariant(format!(
                "event {} content lies outside its stored note",
                hex(&expected_event_id)
            ))
        })?
    };
    std::str::from_utf8(content).map_err(|_| {
        SemanticMapSampleError::Invariant(format!(
            "event {} content is not UTF-8",
            hex(&expected_event_id)
        ))
    })
}

fn expected_manifest(
    source_manifest: SemanticMapSampleFile,
    fresh: &FreshEnglishManifest,
    selection: &SelectionResult,
    output_file: Option<SemanticMapSampleFile>,
) -> Result<SemanticMapSampleManifest, SemanticMapSampleError> {
    let output_file = output_file.unwrap_or(SemanticMapSampleFile {
        file: ORDERED_EVENT_IDS_FILE.to_owned(),
        records: SAMPLE_ROWS as u64,
        bytes: (SAMPLE_ROWS * EVENT_ID_BYTES) as u64,
        sha256: sha256_event_ids(&selection.selected),
    });
    Ok(SemanticMapSampleManifest {
        schema_version: SCHEMA_VERSION,
        selection_rule: SELECTION_RULE.to_owned(),
        selection_domain: String::from_utf8_lossy(SELECTION_DOMAIN).into_owned(),
        usable_text_normalization_policy: NORMALIZATION_POLICY.to_owned(),
        source_classification_policy: CLASSIFICATION_POLICY.to_owned(),
        source_manifest,
        declared_source_ndb_data_sha256: fresh.source_ndb_data_sha256.clone(),
        source_derivation_ledger_sha256: fresh.source_derivation_ledger_sha256.clone(),
        source_dedup_manifest_sha256: fresh.source_dedup_manifest_sha256.clone(),
        source_pre_english_ordered_event_ids_sha256: fresh.source_ordered_event_ids_sha256.clone(),
        source_english_ordered_event_ids_sha256: selection.source_ordered_sha256.clone(),
        scanned_english_events: selection.scanned_events,
        usable_text_events: selection.usable_events,
        excluded_no_usable_text: selection.excluded_no_usable_text,
        selected_events: SAMPLE_ROWS as u64,
        initial_rows: INITIAL_SAMPLE_ROWS as u64,
        extension_rows: (SAMPLE_ROWS - INITIAL_SAMPLE_ROWS) as u64,
        ordered_event_ids: output_file,
    })
}

fn validate_config(config: &SemanticMapSampleConfig) -> Result<(), SemanticMapSampleError> {
    if config
        .output_path
        .symlink_metadata()
        .is_ok_and(|metadata| metadata.file_type().is_symlink())
    {
        return Err(SemanticMapSampleError::Invariant(format!(
            "output path must not be a symbolic link: {}",
            config.output_path.display()
        )));
    }
    let source_corpus = fs::canonicalize(&config.source_corpus_path)
        .map_err(|source| io_error("resolve", &config.source_corpus_path, source))?;
    let source_order = fs::canonicalize(&config.source_ordered_event_ids_path)
        .map_err(|source| io_error("resolve", &config.source_ordered_event_ids_path, source))?;
    let source_manifest = fs::canonicalize(&config.source_manifest_path)
        .map_err(|source| io_error("resolve", &config.source_manifest_path, source))?;
    let output = resolve_for_comparison(&config.output_path)?;
    if output.starts_with(&source_corpus) || output == source_order || output == source_manifest {
        return Err(SemanticMapSampleError::Invariant(
            "sample output overlaps a source artifact".to_owned(),
        ));
    }
    if !config.source_corpus_path.join("data.mdb").is_file() {
        return Err(SemanticMapSampleError::Invariant(format!(
            "source NostrDB data is missing: {}",
            config.source_corpus_path.join("data.mdb").display()
        )));
    }
    if !config.source_ordered_event_ids_path.is_file() || !config.source_manifest_path.is_file() {
        return Err(SemanticMapSampleError::Invariant(
            "source ordered IDs and English manifest must be regular files".to_owned(),
        ));
    }
    Ok(())
}

fn validate_source_manifest(manifest: &FreshEnglishManifest) -> Result<(), SemanticMapSampleError> {
    if manifest.model_sha256 != GLOTLID_V3_SHA256
        || manifest.model_repository_commit != GLOTLID_V3_REPOSITORY_COMMIT
    {
        return Err(SemanticMapSampleError::Invariant(
            "source classifier model does not match the pinned GlotLID v3 identity".to_owned(),
        ));
    }
    if manifest.schema_version != 2
        || manifest.normalization_policy != NORMALIZATION_POLICY
        || manifest.classification_policy != CLASSIFICATION_POLICY
        || manifest.retained_events < SAMPLE_ROWS as u64
        || manifest
            .retained_events
            .checked_add(manifest.excluded_events)
            != Some(manifest.input_events)
        || !valid_sha256(&manifest.source_ordered_event_ids_sha256)
        || !valid_sha256(&manifest.source_ndb_data_sha256)
        || !valid_sha256(&manifest.source_derivation_ledger_sha256)
        || !valid_sha256(&manifest.source_dedup_manifest_sha256)
        || !valid_sha256(&manifest.output_ordered_event_ids_sha256)
    {
        return Err(SemanticMapSampleError::Invariant(
            "source English manifest does not satisfy the frozen publication contract".to_owned(),
        ));
    }
    Ok(())
}

fn validate_output_manifest(
    manifest: &SemanticMapSampleManifest,
) -> Result<(), SemanticMapSampleError> {
    let expected_domain = String::from_utf8_lossy(SELECTION_DOMAIN);
    if manifest.schema_version != SCHEMA_VERSION
        || manifest.selection_rule != SELECTION_RULE
        || manifest.selection_domain != expected_domain
        || manifest.usable_text_normalization_policy != NORMALIZATION_POLICY
        || manifest.source_classification_policy != CLASSIFICATION_POLICY
        || manifest.selected_events != SAMPLE_ROWS as u64
        || manifest.initial_rows != INITIAL_SAMPLE_ROWS as u64
        || manifest.extension_rows != (SAMPLE_ROWS - INITIAL_SAMPLE_ROWS) as u64
        || manifest
            .usable_text_events
            .checked_add(manifest.excluded_no_usable_text)
            != Some(manifest.scanned_english_events)
        || manifest.ordered_event_ids.file != ORDERED_EVENT_IDS_FILE
        || manifest.ordered_event_ids.records != SAMPLE_ROWS as u64
        || manifest.ordered_event_ids.bytes != (SAMPLE_ROWS * EVENT_ID_BYTES) as u64
        || !valid_sha256(&manifest.ordered_event_ids.sha256)
    {
        return Err(SemanticMapSampleError::Invariant(
            "stored sample manifest violates the frozen contract".to_owned(),
        ));
    }
    Ok(())
}

fn verify_stage(
    stage: &Path,
    manifest: &SemanticMapSampleManifest,
    expected_ids: &[EventId],
) -> Result<(), SemanticMapSampleError> {
    verify_output_entries(stage)?;
    validate_output_manifest(manifest)?;
    let ordered_path = stage.join(ORDERED_EVENT_IDS_FILE);
    let actual = read_event_ids(&ordered_path)?;
    if actual != expected_ids {
        return Err(SemanticMapSampleError::Invariant(
            "published event-ID bytes differ from the selected order".to_owned(),
        ));
    }
    if actual.iter().copied().collect::<BTreeSet<_>>().len() != SAMPLE_ROWS {
        return Err(SemanticMapSampleError::Invariant(
            "selected event IDs are not unique".to_owned(),
        ));
    }
    let output_file = file_manifest(&ordered_path, SAMPLE_ROWS as u64)?;
    if output_file != manifest.ordered_event_ids {
        return Err(SemanticMapSampleError::Invariant(
            "ordered event-ID file identity differs from the manifest".to_owned(),
        ));
    }
    verify_checksum_sidecar(
        &stage.join(ORDERED_EVENT_IDS_CHECKSUM_FILE),
        &output_file.sha256,
    )?;
    if read_json::<SemanticMapSampleManifest>(&stage.join(MANIFEST_FILE))? != *manifest {
        return Err(SemanticMapSampleError::Invariant(
            "stored manifest differs from the verified manifest".to_owned(),
        ));
    }
    Ok(())
}

fn verify_output_entries(path: &Path) -> Result<(), SemanticMapSampleError> {
    let actual = fs::read_dir(path)
        .map_err(|source| io_error("read", path, source))?
        .map(|entry| {
            let entry = entry.map_err(|source| io_error("read", path, source))?;
            let file_type = entry
                .file_type()
                .map_err(|source| io_error("read metadata for", entry.path(), source))?;
            if !file_type.is_file() {
                return Err(SemanticMapSampleError::Invariant(
                    "sample output entries must be non-symlink regular files".to_owned(),
                ));
            }
            entry.file_name().into_string().map_err(|name| {
                SemanticMapSampleError::Invariant(format!(
                    "sample output contains a non-UTF-8 entry: {}",
                    name.to_string_lossy()
                ))
            })
        })
        .collect::<Result<BTreeSet<_>, _>>()?;
    let expected = BTreeSet::from([
        MANIFEST_FILE.to_owned(),
        ORDERED_EVENT_IDS_FILE.to_owned(),
        ORDERED_EVENT_IDS_CHECKSUM_FILE.to_owned(),
    ]);
    if actual != expected {
        return Err(SemanticMapSampleError::Invariant(
            "sample output must contain exactly its three frozen files".to_owned(),
        ));
    }
    Ok(())
}

fn open_read_only_corpus(path: &Path) -> Result<ReadOnlyCorpus, SemanticMapSampleError> {
    let mut builder = Environment::new();
    builder
        .set_max_dbs(32)
        .set_map_size(NDB_MAP_SIZE)
        .set_flags(EnvironmentFlags::READ_ONLY | EnvironmentFlags::NO_READAHEAD);
    let environment = builder.open(path)?;
    let note_id = environment.open_db(Some("note_id"))?;
    let note = environment.open_db(Some("note"))?;
    Ok(ReadOnlyCorpus {
        environment,
        note_id,
        note,
    })
}

fn write_event_ids(path: &Path, ids: &[EventId]) -> Result<(), SemanticMapSampleError> {
    let file = OpenOptions::new()
        .create_new(true)
        .write(true)
        .open(path)
        .map_err(|source| io_error("create", path, source))?;
    let mut writer = BufWriter::new(file);
    for id in ids {
        writer
            .write_all(id)
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

fn read_event_ids(path: &Path) -> Result<Vec<EventId>, SemanticMapSampleError> {
    let bytes = fs::read(path).map_err(|source| io_error("read", path, source))?;
    let mut chunks = bytes.chunks_exact(EVENT_ID_BYTES);
    let ids = chunks
        .by_ref()
        .map(|chunk| chunk.try_into().expect("fixed-width event-ID chunk"))
        .collect::<Vec<_>>();
    if !chunks.remainder().is_empty() {
        return Err(SemanticMapSampleError::Invariant(format!(
            "event-ID file ends with a partial record: {}",
            path.display()
        )));
    }
    Ok(ids)
}

fn read_event_id(reader: &mut impl Read, path: &Path) -> Result<EventId, SemanticMapSampleError> {
    let mut id = [0_u8; EVENT_ID_BYTES];
    reader
        .read_exact(&mut id)
        .map_err(|source| io_error("read", path, source))?;
    Ok(id)
}

fn write_checksum_sidecar(path: &Path, sha256: &str) -> Result<(), SemanticMapSampleError> {
    let mut file = OpenOptions::new()
        .create_new(true)
        .write(true)
        .open(path)
        .map_err(|source| io_error("create", path, source))?;
    writeln!(file, "{sha256}  {ORDERED_EVENT_IDS_FILE}")
        .map_err(|source| io_error("write", path, source))?;
    file.sync_all()
        .map_err(|source| io_error("sync", path, source))
}

fn verify_checksum_sidecar(path: &Path, expected: &str) -> Result<(), SemanticMapSampleError> {
    let expected_record = format!("{expected}  {ORDERED_EVENT_IDS_FILE}\n");
    let actual = fs::read_to_string(path).map_err(|source| io_error("read", path, source))?;
    if actual != expected_record {
        return Err(SemanticMapSampleError::Invariant(format!(
            "ordered event-ID checksum sidecar is invalid: {}",
            path.display()
        )));
    }
    Ok(())
}

fn write_json<T: Serialize>(path: &Path, value: &T) -> Result<(), SemanticMapSampleError> {
    let file = OpenOptions::new()
        .create_new(true)
        .write(true)
        .open(path)
        .map_err(|source| io_error("create", path, source))?;
    let mut writer = BufWriter::new(file);
    serde_json::to_writer_pretty(&mut writer, value)
        .map_err(|source| json_error("encode", path, source))?;
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

fn read_json<T: for<'de> Deserialize<'de>>(path: &Path) -> Result<T, SemanticMapSampleError> {
    serde_json::from_reader(File::open(path).map_err(|source| io_error("open", path, source))?)
        .map_err(|source| json_error("decode", path, source))
}

fn file_manifest(
    path: &Path,
    records: u64,
) -> Result<SemanticMapSampleFile, SemanticMapSampleError> {
    let bytes = fs::metadata(path)
        .map_err(|source| io_error("read metadata for", path, source))?
        .len();
    Ok(SemanticMapSampleFile {
        file: path
            .file_name()
            .and_then(|name| name.to_str())
            .ok_or_else(|| {
                SemanticMapSampleError::Invariant(format!(
                    "artifact file has no UTF-8 name: {}",
                    path.display()
                ))
            })?
            .to_owned(),
        records,
        bytes,
        sha256: sha256_file(path)?,
    })
}

fn file_state(path: &Path) -> Result<FileState, SemanticMapSampleError> {
    let metadata =
        fs::metadata(path).map_err(|source| io_error("read metadata for", path, source))?;
    Ok(FileState {
        device: metadata.dev(),
        inode: metadata.ino(),
        bytes: metadata.len(),
        modified_seconds: metadata.mtime(),
        modified_nanoseconds: metadata.mtime_nsec(),
    })
}

fn require_same_file(
    label: &str,
    before: FileState,
    after: FileState,
) -> Result<(), SemanticMapSampleError> {
    if before != after {
        return Err(SemanticMapSampleError::Invariant(format!(
            "{label} changed while the sample was derived"
        )));
    }
    Ok(())
}

fn selection_key(id: &EventId) -> [u8; 32] {
    let mut hasher = Sha256::new();
    hasher.update(SELECTION_DOMAIN);
    hasher.update(id);
    hasher.finalize().into()
}

fn sha256_event_ids(ids: &[EventId]) -> String {
    let mut hasher = Sha256::new();
    for id in ids {
        hasher.update(id);
    }
    format!("{:x}", hasher.finalize())
}

fn sha256_file(path: &Path) -> Result<String, SemanticMapSampleError> {
    let mut reader =
        BufReader::new(File::open(path).map_err(|source| io_error("open", path, source))?);
    let mut hasher = Sha256::new();
    let mut buffer = vec![0_u8; 8 * 1_024 * 1_024];
    loop {
        let read = reader
            .read(&mut buffer)
            .map_err(|source| io_error("read", path, source))?;
        if read == 0 {
            break;
        }
        hasher.update(&buffer[..read]);
    }
    Ok(format!("{:x}", hasher.finalize()))
}

fn resolve_for_comparison(path: &Path) -> Result<PathBuf, SemanticMapSampleError> {
    let mut existing = path;
    let mut suffix = Vec::new();
    while !existing.exists() {
        let name = existing.file_name().ok_or_else(|| {
            SemanticMapSampleError::Invariant(format!(
                "output path has no existing ancestor: {}",
                path.display()
            ))
        })?;
        suffix.push(name.to_owned());
        existing = existing.parent().ok_or_else(|| {
            SemanticMapSampleError::Invariant(format!(
                "output path has no existing ancestor: {}",
                path.display()
            ))
        })?;
    }
    let mut resolved =
        fs::canonicalize(existing).map_err(|source| io_error("resolve", existing, source))?;
    for component in suffix.into_iter().rev() {
        resolved.push(component);
    }
    Ok(resolved)
}

fn publish_no_replace(source: &Path, destination: &Path) -> Result<(), SemanticMapSampleError> {
    let source_c = CString::new(source.as_os_str().as_bytes()).map_err(|_| {
        SemanticMapSampleError::Invariant(format!(
            "stage path contains a NUL byte: {}",
            source.display()
        ))
    })?;
    let destination_c = CString::new(destination.as_os_str().as_bytes()).map_err(|_| {
        SemanticMapSampleError::Invariant(format!(
            "output path contains a NUL byte: {}",
            destination.display()
        ))
    })?;
    // Linux renameat2 makes create-once publication atomic: the destination is
    // installed only if no entry with that name exists at the rename instant.
    let result = unsafe {
        libc::renameat2(
            libc::AT_FDCWD,
            source_c.as_ptr(),
            libc::AT_FDCWD,
            destination_c.as_ptr(),
            libc::RENAME_NOREPLACE,
        )
    };
    if result == 0 {
        return Ok(());
    }
    let source_error = std::io::Error::last_os_error();
    if source_error.raw_os_error() == Some(libc::EEXIST) {
        return Err(SemanticMapSampleError::OutputExists(destination.to_owned()));
    }
    Err(io_error("publish", destination, source_error))
}

fn sha256_bytes(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}

fn valid_sha256(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || matches!(byte, b'a'..=b'f'))
}

fn increment(value: u64, label: &str) -> Result<u64, SemanticMapSampleError> {
    value
        .checked_add(1)
        .ok_or_else(|| SemanticMapSampleError::Invariant(format!("{label} overflowed u64")))
}

fn stage_path(output: &Path) -> Result<PathBuf, SemanticMapSampleError> {
    let name = output.file_name().ok_or_else(|| {
        SemanticMapSampleError::Invariant(format!(
            "output path has no file name: {}",
            output.display()
        ))
    })?;
    let mut stage_name = OsString::from(".");
    stage_name.push(name);
    stage_name.push(".partial");
    Ok(output
        .parent()
        .unwrap_or_else(|| Path::new("."))
        .join(stage_name))
}

fn verification_runtime_path(output: &Path) -> Result<PathBuf, SemanticMapSampleError> {
    let name = output.file_name().ok_or_else(|| {
        SemanticMapSampleError::Invariant(format!(
            "output path has no file name: {}",
            output.display()
        ))
    })?;
    let mut runtime_name = OsString::from(".");
    runtime_name.push(name);
    runtime_name.push(".verify-runtime");
    Ok(output
        .parent()
        .unwrap_or_else(|| Path::new("."))
        .join(runtime_name))
}

fn sync_directory(path: &Path) -> Result<(), SemanticMapSampleError> {
    File::open(path)
        .and_then(|directory| directory.sync_all())
        .map_err(|source| io_error("sync", path, source))
}

fn hex(id: &EventId) -> String {
    id.iter().map(|byte| format!("{byte:02x}")).collect()
}

fn io_error(
    operation: &'static str,
    path: impl AsRef<Path>,
    source: std::io::Error,
) -> SemanticMapSampleError {
    SemanticMapSampleError::Io {
        operation,
        path: path.as_ref().to_owned(),
        source,
    }
}

fn json_error(
    operation: &'static str,
    path: impl AsRef<Path>,
    source: serde_json::Error,
) -> SemanticMapSampleError {
    SemanticMapSampleError::Json {
        operation,
        path: path.as_ref().to_owned(),
        source,
    }
}
