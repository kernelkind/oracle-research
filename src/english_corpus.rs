//! Streaming construction of the complete English-eligible MVP corpus.

use std::fs::{self, File, OpenOptions};
use std::io::{BufReader, BufWriter, Read, Write};
use std::path::{Path, PathBuf};
use std::thread;
use std::time::{Duration, Instant};

use fasttext::FastText;
use nostrdb::{Config, Error as NdbError, Ndb, Note, Transaction};
use serde::{Deserialize, Serialize};
use thiserror::Error;

use crate::artifact::hash_file;
use crate::english_filter::{
    self, CLASSIFICATION_POLICY, ClassifierDecision, GLOTLID_V3_REPOSITORY_COMMIT,
    GLOTLID_V3_SHA256, NORMALIZATION_POLICY, classifier_decision, classifier_input,
    validate_model_labels,
};
use crate::snapshot::{
    self, Validation, count_with_db, io_error, ndb_error, open_ndb, write_manifest,
};

const SCHEMA_VERSION: u32 = 1;
const EVENT_ID_BYTES: usize = 32;
const NDB_MAP_SIZE: usize = 256 * 1_024 * 1_024 * 1_024;
const NDB_NO_MIGRATE: i32 = 1;
const NDB_NO_FULLTEXT: i32 = 1 << 2;
const NDB_NO_NOTE_BLOCKS: i32 = 1 << 3;
const NDB_NO_STATS: i32 = 1 << 4;
const INGEST_RETRY_DELAY: Duration = Duration::from_millis(100);
const PERSISTENCE_CHECKPOINT_EVENTS: usize = 16 * 1_024;
const PERSISTENCE_POLL_DELAY: Duration = Duration::from_millis(50);
const PERSISTENCE_STALL_POLLS: u8 = 4;
const PERSISTENCE_TIMEOUT: Duration = Duration::from_secs(60);

type EventId = [u8; EVENT_ID_BYTES];

/// A complete English-corpus build failure.
#[derive(Debug, Error)]
pub enum Error {
    /// Shared normalization or model-label validation failed.
    #[error(transparent)]
    EnglishFilter(#[from] english_filter::Error),

    /// Shared snapshot storage or artifact handling failed.
    #[error(transparent)]
    Snapshot(#[from] snapshot::Error),

    /// The FastText model could not be loaded.
    #[error("failed to load language model `{path}`: {message}")]
    Model { path: PathBuf, message: String },

    /// A completed artifact would be overwritten.
    #[error("English-eligible corpus already exists: `{0}`")]
    OutputExists(PathBuf),

    /// An interrupted partial build must be inspected or removed before retrying.
    #[error("incomplete English-eligible corpus already exists: `{0}`")]
    IncompleteStage(PathBuf),

    /// A model lock or corpus artifact violated its contract.
    #[error("English-corpus invariant failed: {0}")]
    Invariant(String),

    /// A stored event cannot be serialized through NostrDB's signed-size interface.
    #[error("stored event is too large for NostrDB's signed length")]
    EventTooLarge,

    /// NostrDB did not persist all submitted events after bounded retries.
    #[error("NostrDB did not persist {missing_events} retained events within 60 seconds")]
    PersistenceTimeout { missing_events: usize },
}

/// Immutable identity required before a FastText language model may classify a corpus.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct EnglishModelLock {
    model_sha256: String,
    model_repository_commit: String,
}

impl EnglishModelLock {
    /// Construct a validated model lock.
    pub fn new(
        model_sha256: impl Into<String>,
        model_repository_commit: impl Into<String>,
    ) -> Result<Self, Error> {
        let lock = Self {
            model_sha256: model_sha256.into(),
            model_repository_commit: model_repository_commit.into(),
        };
        if !valid_sha256(&lock.model_sha256) || lock.model_repository_commit.is_empty() {
            return Err(Error::Invariant(
                "language-model lock has an invalid SHA-256 or empty repository revision"
                    .to_owned(),
            ));
        }
        Ok(lock)
    }
}

/// Return the exact GlotLID v3 model lock approved by CREC-59.
pub fn glotlid_v3_lock() -> EnglishModelLock {
    EnglishModelLock {
        model_sha256: GLOTLID_V3_SHA256.to_owned(),
        model_repository_commit: GLOTLID_V3_REPOSITORY_COMMIT.to_owned(),
    }
}

/// A loaded FastText model whose bytes and required labels were verified.
pub struct FrozenEnglishClassifier {
    model: FastText,
    lock: EnglishModelLock,
}

impl FrozenEnglishClassifier {
    /// Verify the model file against its lock, then load it once for inference.
    pub fn load(model_path: impl AsRef<Path>, lock: EnglishModelLock) -> Result<Self, Error> {
        let model_path = model_path.as_ref();
        let actual_sha256 = hash_file(model_path)?;
        if actual_sha256 != lock.model_sha256 {
            return Err(Error::Invariant(format!(
                "language model SHA-256 is {actual_sha256}; lock requires {}",
                lock.model_sha256
            )));
        }
        let model = FastText::load_model(model_path).map_err(|source| Error::Model {
            path: model_path.to_owned(),
            message: source.to_string(),
        })?;
        let (labels, _) = model.get_labels();
        validate_model_labels(&labels)?;
        Ok(Self { model, lock })
    }

    /// Classify original note content with the exact CREC-59 normalization and keep rule.
    pub fn classify_content(&self, content: &str) -> ClassifierDecision {
        let input = classifier_input(content);
        let top_label = if input.is_empty() {
            None
        } else {
            self.model
                .predict(&input, 1, 0.0)
                .into_iter()
                .next()
                .map(|prediction| prediction.label)
        };
        classifier_decision(&input, top_label.as_deref())
    }
}

/// Immutable identity and accounting for the complete English-eligible corpus.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct EnglishCorpusManifest {
    /// Manifest format version.
    pub schema_version: u32,
    /// SHA-256 of CREC-12's complete source ordering.
    pub source_ordered_event_ids_sha256: String,
    /// Exact FastText model bytes.
    pub model_sha256: String,
    /// Exact upstream model repository revision.
    pub model_repository_commit: String,
    /// Exact classifier-input normalization rule.
    pub normalization_policy: String,
    /// Exact top-label eligibility rule.
    pub classification_policy: String,
    /// Ordered source events examined exactly once.
    pub input_events: u64,
    /// Original signed events copied into the output NostrDB.
    pub retained_events: u64,
    /// Source events omitted by the frozen language policy.
    pub excluded_events: u64,
    /// SHA-256 of the retained ordered event IDs.
    pub output_ordered_event_ids_sha256: String,
}

/// Build and atomically publish a separate English-eligible corpus directory.
pub fn build_english_corpus(
    deduplicated_directory: impl AsRef<Path>,
    output_directory: impl AsRef<Path>,
    classifier: &FrozenEnglishClassifier,
) -> Result<EnglishCorpusManifest, Error> {
    let deduplicated_directory = deduplicated_directory.as_ref();
    let output_directory = output_directory.as_ref();
    let source_db_path = deduplicated_directory.join("ndb");
    let source_ordered_path = deduplicated_directory.join("ordered-event-ids.bin");
    let source_checksum_path = deduplicated_directory.join("ordered-event-ids.sha256");
    if !source_db_path.is_dir() || !source_ordered_path.is_file() || !source_checksum_path.is_file()
    {
        return Err(Error::Invariant(format!(
            "deduplicated corpus is incomplete at {}",
            deduplicated_directory.display()
        )));
    }
    if output_directory.exists() {
        return Err(Error::OutputExists(output_directory.to_owned()));
    }
    let source_ordered_event_ids_sha256 =
        validate_ordered_checksum(&source_ordered_path, &source_checksum_path)?;

    let parent = output_directory.parent().unwrap_or_else(|| Path::new("."));
    fs::create_dir_all(parent).map_err(|source| io_error("create", parent, source))?;
    let stage = stage_path(output_directory)?;
    match fs::create_dir(&stage) {
        Ok(()) => {}
        Err(source) if source.kind() == std::io::ErrorKind::AlreadyExists => {
            return Err(Error::IncompleteStage(stage));
        }
        Err(source) => return Err(io_error("create", &stage, source).into()),
    }

    let result = build_in_stage(
        &source_db_path,
        &source_ordered_path,
        source_ordered_event_ids_sha256,
        classifier,
        &stage,
    );
    let manifest = match result {
        Ok(manifest) => manifest,
        Err(error) => {
            let _ = fs::remove_dir_all(&stage);
            return Err(error);
        }
    };
    if output_directory.exists() {
        let _ = fs::remove_dir_all(&stage);
        return Err(Error::OutputExists(output_directory.to_owned()));
    }
    fs::rename(&stage, output_directory)
        .map_err(|source| io_error("publish", output_directory, source))?;
    File::open(parent)
        .and_then(|directory| directory.sync_all())
        .map_err(|source| io_error("sync", parent, source))?;
    Ok(manifest)
}

fn build_in_stage(
    source_db_path: &Path,
    source_ordered_path: &Path,
    source_ordered_event_ids_sha256: String,
    classifier: &FrozenEnglishClassifier,
    stage: &Path,
) -> Result<EnglishCorpusManifest, Error> {
    let input_events = ordered_record_count(source_ordered_path)?;
    let source = open_source_ndb(source_db_path)?;
    let source_count = count_with_db(&source, source_db_path, None)?;
    if source_count != input_events {
        return Err(Error::Invariant(format!(
            "source NostrDB contains {source_count} events but its ordered-ID file contains {input_events}"
        )));
    }
    let source_transaction = Transaction::new(&source)
        .map_err(|source| ndb_error("open transaction on", source_db_path, source))?;
    let output_db_path = stage.join("ndb");
    let output = open_output_ndb(&output_db_path)?;
    let output_ordered_path = stage.join("ordered-event-ids.bin");
    let mut ordered_reader = BufReader::new(
        File::open(source_ordered_path)
            .map_err(|source| io_error("open", source_ordered_path, source))?,
    );
    let output_file = OpenOptions::new()
        .create_new(true)
        .write(true)
        .open(&output_ordered_path)
        .map_err(|source| io_error("create", &output_ordered_path, source))?;
    let mut ordered_writer = BufWriter::new(output_file);
    let mut unconfirmed = Vec::with_capacity(PERSISTENCE_CHECKPOINT_EVENTS);
    let mut retained_events = 0_u64;
    let mut excluded_events = 0_u64;

    for _ in 0..input_events {
        let mut id = [0_u8; EVENT_ID_BYTES];
        ordered_reader
            .read_exact(&mut id)
            .map_err(|source| io_error("read", source_ordered_path, source))?;
        let note = source
            .get_note_by_id(&source_transaction, &id)
            .map_err(|source| ndb_error("load ordered event from", source_db_path, source))?;
        match classifier.classify_content(note.content()) {
            ClassifierDecision::KeepEnglish | ClassifierDecision::KeepLanguageNeutral => {
                let json = note_json(&note, source_db_path)?;
                submit_with_retry(&output, &output_db_path, &json)?;
                ordered_writer
                    .write_all(&id)
                    .map_err(|source| io_error("write", &output_ordered_path, source))?;
                unconfirmed.push(PendingEvent { id, json });
                retained_events = increment(retained_events)?;
                if unconfirmed.len() >= PERSISTENCE_CHECKPOINT_EVENTS {
                    confirm_persistence(&output, &output_db_path, &mut unconfirmed)?;
                }
            }
            ClassifierDecision::Exclude => excluded_events = increment(excluded_events)?,
        }
    }
    confirm_persistence(&output, &output_db_path, &mut unconfirmed)?;
    ordered_writer
        .flush()
        .map_err(|source| io_error("flush", &output_ordered_path, source))?;
    ordered_writer
        .get_ref()
        .sync_all()
        .map_err(|source| io_error("sync", &output_ordered_path, source))?;
    if retained_events.checked_add(excluded_events) != Some(input_events) {
        return Err(Error::Invariant(format!(
            "classified {retained_events} retained plus {excluded_events} excluded events from {input_events} inputs"
        )));
    }
    drop(ordered_writer);
    drop(output);
    drop(source_transaction);
    drop(source);

    verify_output(
        source_ordered_path,
        input_events,
        &output_db_path,
        &output_ordered_path,
        retained_events,
    )?;
    let manifest = EnglishCorpusManifest {
        schema_version: SCHEMA_VERSION,
        source_ordered_event_ids_sha256,
        model_sha256: classifier.lock.model_sha256.clone(),
        model_repository_commit: classifier.lock.model_repository_commit.clone(),
        normalization_policy: NORMALIZATION_POLICY.to_owned(),
        classification_policy: CLASSIFICATION_POLICY.to_owned(),
        input_events,
        retained_events,
        excluded_events,
        output_ordered_event_ids_sha256: hash_file(&output_ordered_path)?,
    };
    write_manifest(&stage.join("manifest.json"), &manifest)?;
    File::open(stage)
        .and_then(|directory| directory.sync_all())
        .map_err(|source| io_error("sync", stage, source))?;
    Ok(manifest)
}

fn verify_output(
    source_ordered_path: &Path,
    source_events: u64,
    output_db_path: &Path,
    output_ordered_path: &Path,
    retained_events: u64,
) -> Result<(), Error> {
    if ordered_record_count(output_ordered_path)? != retained_events {
        return Err(Error::Invariant(
            "output ordered-ID count does not match retained count".to_owned(),
        ));
    }
    let output = open_ndb(output_db_path, Validation::TrustedSource)?;
    let stored = count_with_db(&output, output_db_path, None)?;
    if stored != retained_events {
        return Err(Error::Invariant(format!(
            "English-eligible NostrDB contains {stored} events; expected {retained_events}"
        )));
    }
    let transaction = Transaction::new(&output)
        .map_err(|source| ndb_error("open transaction on", output_db_path, source))?;
    let mut output_reader = BufReader::new(
        File::open(output_ordered_path)
            .map_err(|source| io_error("open", output_ordered_path, source))?,
    );
    for _ in 0..retained_events {
        let mut id = [0_u8; EVENT_ID_BYTES];
        output_reader
            .read_exact(&mut id)
            .map_err(|source| io_error("read", output_ordered_path, source))?;
        output
            .get_note_by_id(&transaction, &id)
            .map_err(|source| ndb_error("load ordered event from", output_db_path, source))?;
    }
    drop(transaction);
    drop(output);
    verify_ordered_subsequence(
        source_ordered_path,
        source_events,
        output_ordered_path,
        retained_events,
    )
}

fn verify_ordered_subsequence(
    source_path: &Path,
    source_events: u64,
    output_path: &Path,
    output_events: u64,
) -> Result<(), Error> {
    let mut source = BufReader::new(
        File::open(source_path).map_err(|source| io_error("open", source_path, source))?,
    );
    let mut output = BufReader::new(
        File::open(output_path).map_err(|source| io_error("open", output_path, source))?,
    );
    let mut next_output = if output_events == 0 {
        None
    } else {
        let mut id = [0_u8; EVENT_ID_BYTES];
        output
            .read_exact(&mut id)
            .map_err(|source| io_error("read", output_path, source))?;
        Some(id)
    };
    let mut matched = 0_u64;
    for _ in 0..source_events {
        let mut source_id = [0_u8; EVENT_ID_BYTES];
        source
            .read_exact(&mut source_id)
            .map_err(|source| io_error("read", source_path, source))?;
        if next_output == Some(source_id) {
            matched = increment(matched)?;
            next_output = if matched == output_events {
                None
            } else {
                let mut id = [0_u8; EVENT_ID_BYTES];
                output
                    .read_exact(&mut id)
                    .map_err(|source| io_error("read", output_path, source))?;
                Some(id)
            };
        }
    }
    if matched != output_events || next_output.is_some() {
        return Err(Error::Invariant(format!(
            "matched {matched} of {output_events} output IDs in source order"
        )));
    }
    Ok(())
}

struct PendingEvent {
    id: EventId,
    json: String,
}

fn confirm_persistence(
    output: &Ndb,
    output_db_path: &Path,
    unconfirmed: &mut Vec<PendingEvent>,
) -> Result<(), Error> {
    if unconfirmed.is_empty() {
        return Ok(());
    }
    let deadline = Instant::now() + PERSISTENCE_TIMEOUT;
    let mut unresolved = std::mem::take(unconfirmed);
    let mut previous_missing = usize::MAX;
    let mut stalled_polls = 0_u8;
    loop {
        thread::sleep(PERSISTENCE_POLL_DELAY);
        unresolved = missing_events(output, output_db_path, unresolved)?;
        if unresolved.is_empty() {
            unconfirmed.reserve(PERSISTENCE_CHECKPOINT_EVENTS);
            return Ok(());
        }
        if Instant::now() >= deadline {
            return Err(Error::PersistenceTimeout {
                missing_events: unresolved.len(),
            });
        }
        if unresolved.len() < previous_missing {
            stalled_polls = 0;
        } else {
            stalled_polls = stalled_polls.saturating_add(1);
        }
        previous_missing = unresolved.len();
        if stalled_polls >= PERSISTENCE_STALL_POLLS {
            for event in &unresolved {
                submit_with_retry(output, output_db_path, &event.json)?;
            }
            previous_missing = usize::MAX;
            stalled_polls = 0;
        }
    }
}

fn missing_events(
    output: &Ndb,
    output_db_path: &Path,
    events: Vec<PendingEvent>,
) -> Result<Vec<PendingEvent>, Error> {
    let transaction = Transaction::new(output)
        .map_err(|source| ndb_error("open transaction on", output_db_path, source))?;
    let mut missing = Vec::with_capacity(events.len());
    for event in events {
        match output.get_note_by_id(&transaction, &event.id) {
            Ok(_) => {}
            Err(NdbError::NotFound) => missing.push(event),
            Err(source) => {
                return Err(ndb_error("load retained event from", output_db_path, source).into());
            }
        }
    }
    Ok(missing)
}

fn note_json(note: &Note<'_>, source_db_path: &Path) -> Result<String, Error> {
    let mut capacity = note.size().saturating_mul(2).max(1_024);
    loop {
        if capacity > i32::MAX as usize {
            return Err(Error::EventTooLarge);
        }
        match note.json_with_bufsize(capacity) {
            Ok(json) if json.len() <= i32::MAX as usize => return Ok(json),
            Ok(_) => return Err(Error::EventTooLarge),
            Err(NdbError::BufferOverflow) => {
                capacity = capacity.checked_mul(2).ok_or(Error::EventTooLarge)?;
            }
            Err(source) => {
                return Err(
                    ndb_error("serialize retained event from", source_db_path, source).into(),
                );
            }
        }
    }
}

fn submit_with_retry(output: &Ndb, output_db_path: &Path, event: &str) -> Result<(), Error> {
    loop {
        match output.process_event(event) {
            Ok(()) => return Ok(()),
            Err(NdbError::NoteProcessFailed) => thread::sleep(INGEST_RETRY_DELAY),
            Err(source) => {
                return Err(ndb_error("submit retained event to", output_db_path, source).into());
            }
        }
    }
}

fn open_output_ndb(path: &Path) -> Result<Ndb, Error> {
    let path_string = path.to_str().ok_or_else(|| {
        Error::Invariant(format!(
            "NostrDB path is not valid UTF-8: {}",
            path.display()
        ))
    })?;
    let config = Config::new()
        .set_flags(NDB_NO_FULLTEXT | NDB_NO_NOTE_BLOCKS | NDB_NO_STATS)
        .set_mapsize(NDB_MAP_SIZE)
        .skip_validation(true);
    Ndb::new(path_string, &config)
        .map_err(|source| ndb_error("open", path, source))
        .map_err(Into::into)
}

fn open_source_ndb(path: &Path) -> Result<Ndb, Error> {
    let path_string = path.to_str().ok_or_else(|| {
        Error::Invariant(format!(
            "NostrDB path is not valid UTF-8: {}",
            path.display()
        ))
    })?;
    let config = Config::new()
        .set_flags(NDB_NO_MIGRATE | NDB_NO_FULLTEXT | NDB_NO_NOTE_BLOCKS | NDB_NO_STATS)
        .set_mapsize(NDB_MAP_SIZE)
        .skip_validation(true)
        .set_ingester_threads(1);
    Ndb::new(path_string, &config)
        .map_err(|source| ndb_error("open without migration", path, source))
        .map_err(Into::into)
}

fn validate_ordered_checksum(ordered_path: &Path, checksum_path: &Path) -> Result<String, Error> {
    let contents = fs::read_to_string(checksum_path)
        .map_err(|source| io_error("read", checksum_path, source))?;
    let mut lines = contents.lines();
    let line = lines.next().ok_or_else(|| {
        Error::Invariant(format!(
            "source checksum file is empty: {}",
            checksum_path.display()
        ))
    })?;
    if lines.next().is_some() {
        return Err(Error::Invariant(format!(
            "source checksum file has more than one record: {}",
            checksum_path.display()
        )));
    }
    let (expected, file_name) = line.split_once("  ").ok_or_else(|| {
        Error::Invariant(format!(
            "source checksum file has an invalid record: {}",
            checksum_path.display()
        ))
    })?;
    if !valid_sha256(expected) || file_name != "ordered-event-ids.bin" {
        return Err(Error::Invariant(format!(
            "source checksum file has an invalid record: {}",
            checksum_path.display()
        )));
    }
    let actual = hash_file(ordered_path)?;
    if actual != expected {
        return Err(Error::Invariant(format!(
            "source ordered-ID checksum is {actual}; CREC-12 recorded {expected}"
        )));
    }
    Ok(actual)
}

fn ordered_record_count(path: &Path) -> Result<u64, Error> {
    let bytes = fs::metadata(path)
        .map_err(|source| io_error("read metadata for", path, source))?
        .len();
    if bytes % EVENT_ID_BYTES as u64 != 0 {
        return Err(Error::Invariant(format!(
            "ordered event-ID file `{}` ends with a partial 32-byte record",
            path.display()
        )));
    }
    Ok(bytes / EVENT_ID_BYTES as u64)
}

fn increment(count: u64) -> Result<u64, Error> {
    count
        .checked_add(1)
        .ok_or_else(|| Error::Invariant("event count overflowed u64".to_owned()))
}

fn stage_path(output: &Path) -> Result<PathBuf, Error> {
    let parent = output.parent().unwrap_or_else(|| Path::new("."));
    let name = output
        .file_name()
        .and_then(|name| name.to_str())
        .ok_or_else(|| Error::Invariant(format!("invalid output path: {}", output.display())))?;
    Ok(parent.join(format!(".{name}.partial")))
}

fn valid_sha256(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || matches!(byte, b'a'..=b'f'))
}
