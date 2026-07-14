//! Exact-content deduplication of the filtered MVP corpus.

use std::collections::BTreeMap;
use std::fs::{self, File, OpenOptions};
use std::io::{BufReader, BufWriter, Read, Write};
use std::path::{Path, PathBuf};
use std::thread;
use std::time::{Duration, Instant};

use nostrdb::{Config, Error as NdbError, Filter, Ndb, Note, Transaction};
use serde::Serialize;
use sha2::{Digest, Sha256};
use thiserror::Error;

const EVENT_ID_BYTES: usize = 32;
const INDEX_RECORD_BYTES: usize = EVENT_ID_BYTES * 2;
const ROW_ORDER_DOMAIN: &[u8] = b"oracle-mvp/canonical-row-order/v1\0";
const NDB_MAP_SIZE: usize = 256 * 1_024 * 1_024 * 1_024;
const NDB_NO_FULLTEXT: i32 = 1 << 2;
const NDB_NO_NOTE_BLOCKS: i32 = 1 << 3;
const NDB_NO_STATS: i32 = 1 << 4;
const INGEST_RETRY_DELAY: Duration = Duration::from_millis(100);
const PERSISTENCE_CHECKPOINT_EVENTS: usize = 16 * 1_024;
const PERSISTENCE_POLL_DELAY: Duration = Duration::from_millis(50);
const PERSISTENCE_STALL_POLLS: u8 = 4;
const PERSISTENCE_TIMEOUT: Duration = Duration::from_secs(60);

type EventId = [u8; EVENT_ID_BYTES];
type IndexRecord = [u8; INDEX_RECORD_BYTES];

/// Counts produced by Stage 4.
#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
pub struct CorpusDedupSummary {
    /// Events read from `filtered.ndb`.
    pub scanned_events: u64,
    /// Events copied to `deduplicated/ndb`.
    pub retained_events: u64,
    /// Events omitted because another event had byte-identical content.
    pub duplicate_events: u64,
}

/// A Stage 4 corpus-deduplication failure.
#[derive(Debug, Error)]
pub enum CorpusDedupError {
    /// A filesystem operation failed.
    #[error("failed to {operation} `{path}`: {source}")]
    Io {
        operation: &'static str,
        path: PathBuf,
        #[source]
        source: std::io::Error,
    },

    /// A NostrDB operation failed.
    #[error("NostrDB operation failed: {0}")]
    Ndb(#[from] NdbError),

    /// The requested output already exists and must not be replaced.
    #[error("output already exists: `{0}`")]
    OutputExists(PathBuf),

    /// A required input or output invariant was violated.
    #[error("corpus invariant failed: {0}")]
    Invariant(String),

    /// A NostrDB event cannot be serialized through its signed-size interface.
    #[error("stored event is too large for NostrDB's signed length")]
    EventTooLarge,

    /// NostrDB did not persist every submitted representative in time.
    #[error("NostrDB did not persist {missing_events} retained events within 60 seconds")]
    PersistenceTimeout { missing_events: usize },
}

/// Build and atomically publish the deduplicated corpus directory.
pub fn build_deduplicated_corpus(
    filtered_path: impl AsRef<Path>,
    output_path: impl AsRef<Path>,
) -> Result<CorpusDedupSummary, CorpusDedupError> {
    let filtered_path = filtered_path.as_ref();
    let output_path = output_path.as_ref();
    if !filtered_path.is_dir() {
        return Err(CorpusDedupError::Invariant(format!(
            "filtered NostrDB does not exist: {}",
            filtered_path.display()
        )));
    }
    if output_path.exists() {
        return Err(CorpusDedupError::OutputExists(output_path.to_owned()));
    }

    let parent = output_path.parent().unwrap_or_else(|| Path::new("."));
    fs::create_dir_all(parent).map_err(|source| io_error("create", parent, source))?;
    let stage_path = create_stage_directory(output_path)?;
    let result = build_in_stage(filtered_path, &stage_path);
    let summary = match result {
        Ok(summary) => summary,
        Err(error) => {
            let _ = fs::remove_dir_all(&stage_path);
            return Err(error);
        }
    };

    if output_path.exists() {
        let _ = fs::remove_dir_all(&stage_path);
        return Err(CorpusDedupError::OutputExists(output_path.to_owned()));
    }
    fs::rename(&stage_path, output_path)
        .map_err(|source| io_error("publish", output_path, source))?;
    File::open(parent)
        .and_then(|directory| directory.sync_all())
        .map_err(|source| io_error("sync", parent, source))?;
    Ok(summary)
}

fn build_in_stage(
    filtered_path: &Path,
    stage_path: &Path,
) -> Result<CorpusDedupSummary, CorpusDedupError> {
    let filtered = open_ndb(filtered_path, false)?;
    let mut index = build_content_index(&filtered)?;
    index.sort_unstable();
    let scanned_events = u64::try_from(index.len())
        .map_err(|_| CorpusDedupError::Invariant("event count does not fit u64".to_owned()))?;

    let deduplicated_path = stage_path.join("ndb");
    let deduplicated = open_ndb(&deduplicated_path, true)?;
    let representatives = copy_representatives(&filtered, &deduplicated, &index)?;
    drop(deduplicated);
    drop(index);

    let retained_events = u64::try_from(representatives.len()).map_err(|_| {
        CorpusDedupError::Invariant("representative count does not fit u64".to_owned())
    })?;
    let duplicate_events = scanned_events.checked_sub(retained_events).ok_or_else(|| {
        CorpusDedupError::Invariant(format!(
            "retained {retained_events} events after scanning {scanned_events}"
        ))
    })?;

    let verified = open_ndb(&deduplicated_path, true)?;
    verify_unique_ids(&representatives)?;
    let stored = count_events(&verified)?;
    if stored != retained_events {
        return Err(CorpusDedupError::Invariant(format!(
            "deduplicated NostrDB contains {stored} events; expected {retained_events}"
        )));
    }
    let ordered_path = stage_path.join("ordered-event-ids.bin");
    write_ordered_ids(&verified, representatives, &ordered_path, retained_events)?;
    drop(verified);
    write_checksum(&ordered_path, &stage_path.join("ordered-event-ids.sha256"))?;

    Ok(CorpusDedupSummary {
        scanned_events,
        retained_events,
        duplicate_events,
    })
}

fn build_content_index(ndb: &Ndb) -> Result<Vec<IndexRecord>, CorpusDedupError> {
    let txn = Transaction::new(ndb)?;
    let all = Filter::new().build();
    ndb.fold(&txn, &[all], Vec::new(), |mut index, note| {
        let mut record = [0_u8; INDEX_RECORD_BYTES];
        record[..EVENT_ID_BYTES].copy_from_slice(&Sha256::digest(note.content().as_bytes()));
        record[EVENT_ID_BYTES..].copy_from_slice(note.id());
        index.push(record);
        index
    })
    .map_err(Into::into)
}

fn copy_representatives(
    source: &Ndb,
    destination: &Ndb,
    index: &[IndexRecord],
) -> Result<Vec<EventId>, CorpusDedupError> {
    let source_txn = Transaction::new(source)?;
    let mut representatives = Vec::with_capacity(index.len());
    let mut unconfirmed = Vec::with_capacity(PERSISTENCE_CHECKPOINT_EVENTS);
    let mut offset = 0;

    while offset < index.len() {
        let hash = index[offset][..EVENT_ID_BYTES]
            .try_into()
            .expect("content hash width");
        let mut end = offset + 1;
        while end < index.len() && index[end][..EVENT_ID_BYTES] == index[offset][..EVENT_ID_BYTES] {
            end += 1;
        }

        if end == offset + 1 {
            let id = event_id(&index[offset]);
            copy_event(source, &source_txn, destination, id, &mut unconfirmed)?;
            representatives.push(id);
        } else {
            let exact = exact_representatives(source, &source_txn, hash, &index[offset..end])?;
            for id in exact.into_values() {
                copy_event(source, &source_txn, destination, id, &mut unconfirmed)?;
                representatives.push(id);
            }
        }
        if unconfirmed.len() >= PERSISTENCE_CHECKPOINT_EVENTS {
            confirm_persistence(destination, &mut unconfirmed)?;
        }
        offset = end;
    }
    confirm_persistence(destination, &mut unconfirmed)?;
    Ok(representatives)
}

fn exact_representatives(
    source: &Ndb,
    source_txn: &Transaction,
    expected_hash: EventId,
    records: &[IndexRecord],
) -> Result<BTreeMap<Vec<u8>, EventId>, CorpusDedupError> {
    let mut exact = BTreeMap::new();
    for record in records {
        let id = event_id(record);
        let note = source.get_note_by_id(source_txn, &id)?;
        if Sha256::digest(note.content().as_bytes()).as_slice() != expected_hash {
            return Err(CorpusDedupError::Invariant(format!(
                "event {} does not match its content-index hash",
                encode_hex(&id)
            )));
        }
        exact
            .entry(note.content().as_bytes().to_vec())
            .and_modify(|current: &mut EventId| *current = (*current).min(id))
            .or_insert(id);
    }
    Ok(exact)
}

struct PendingEvent {
    id: EventId,
    json: String,
}

fn copy_event(
    source: &Ndb,
    source_txn: &Transaction,
    destination: &Ndb,
    id: EventId,
    unconfirmed: &mut Vec<PendingEvent>,
) -> Result<(), CorpusDedupError> {
    let note = source.get_note_by_id(source_txn, &id)?;
    let json = note_json(&note)?;
    submit_with_retry(destination, &json)?;
    unconfirmed.push(PendingEvent { id, json });
    Ok(())
}

fn confirm_persistence(
    destination: &Ndb,
    unconfirmed: &mut Vec<PendingEvent>,
) -> Result<(), CorpusDedupError> {
    if unconfirmed.is_empty() {
        return Ok(());
    }
    let deadline = Instant::now() + PERSISTENCE_TIMEOUT;
    let mut unresolved = std::mem::take(unconfirmed);
    let mut previous_missing = usize::MAX;
    let mut stalled_polls = 0_u8;

    loop {
        thread::sleep(PERSISTENCE_POLL_DELAY);
        unresolved = missing_events(destination, unresolved)?;
        if unresolved.is_empty() {
            unconfirmed.reserve(PERSISTENCE_CHECKPOINT_EVENTS);
            return Ok(());
        }
        if Instant::now() >= deadline {
            return Err(CorpusDedupError::PersistenceTimeout {
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
                submit_with_retry(destination, &event.json)?;
            }
            previous_missing = usize::MAX;
            stalled_polls = 0;
        }
    }
}

fn missing_events(
    destination: &Ndb,
    events: Vec<PendingEvent>,
) -> Result<Vec<PendingEvent>, CorpusDedupError> {
    let txn = Transaction::new(destination)?;
    let mut missing = Vec::with_capacity(events.len());
    for event in events {
        match destination.get_note_by_id(&txn, &event.id) {
            Ok(_) => {}
            Err(NdbError::NotFound) => missing.push(event),
            Err(error) => return Err(error.into()),
        }
    }
    Ok(missing)
}

fn write_ordered_ids(
    ndb: &Ndb,
    representatives: Vec<EventId>,
    path: &Path,
    expected: u64,
) -> Result<(), CorpusDedupError> {
    let mut ordered = Vec::with_capacity(representatives.len());
    for id in representatives {
        let mut record = [0_u8; INDEX_RECORD_BYTES];
        record[..EVENT_ID_BYTES].copy_from_slice(&row_order_key(&id));
        record[EVENT_ID_BYTES..].copy_from_slice(&id);
        ordered.push(record);
    }
    ordered.sort_unstable();

    let mut writer = BufWriter::new(create_new_file(path)?);
    let txn = Transaction::new(ndb)?;
    let mut written = 0_u64;
    for record in ordered {
        let id = event_id(&record);
        ndb.get_note_by_id(&txn, &id)?;
        writer
            .write_all(&id)
            .map_err(|source| io_error("write", path, source))?;
        written = written.checked_add(1).ok_or_else(|| {
            CorpusDedupError::Invariant("ordered event count overflowed u64".to_owned())
        })?;
    }
    finish_writer(&mut writer, path)?;
    if written != expected {
        return Err(CorpusDedupError::Invariant(format!(
            "wrote {written} ordered event IDs; expected {expected}"
        )));
    }
    Ok(())
}

fn verify_unique_ids(ids: &[EventId]) -> Result<(), CorpusDedupError> {
    let mut sorted = ids.to_vec();
    sorted.sort_unstable();
    if let Some(duplicate) = sorted.windows(2).find(|pair| pair[0] == pair[1]) {
        return Err(CorpusDedupError::Invariant(format!(
            "representative event ID appears more than once: {}",
            encode_hex(&duplicate[0])
        )));
    }
    Ok(())
}

fn count_events(ndb: &Ndb) -> Result<u64, CorpusDedupError> {
    let txn = Transaction::new(ndb)?;
    let all = Filter::new().build();
    ndb.fold(&txn, &[all], 0_u64, |count, _| count + 1)
        .map_err(Into::into)
}

fn write_checksum(input: &Path, output: &Path) -> Result<(), CorpusDedupError> {
    let mut reader =
        BufReader::new(File::open(input).map_err(|source| io_error("open", input, source))?);
    let mut hasher = Sha256::new();
    let mut buffer = [0_u8; 64 * 1_024];
    loop {
        let bytes = reader
            .read(&mut buffer)
            .map_err(|source| io_error("read", input, source))?;
        if bytes == 0 {
            break;
        }
        hasher.update(&buffer[..bytes]);
    }
    let mut writer = BufWriter::new(create_new_file(output)?);
    writeln!(writer, "{:x}  ordered-event-ids.bin", hasher.finalize())
        .map_err(|source| io_error("write", output, source))?;
    finish_writer(&mut writer, output)
}

fn note_json(note: &Note<'_>) -> Result<String, CorpusDedupError> {
    let mut capacity = note.size().saturating_mul(2).max(1_024);
    loop {
        if capacity > i32::MAX as usize {
            return Err(CorpusDedupError::EventTooLarge);
        }
        match note.json_with_bufsize(capacity) {
            Ok(json) if json.len() <= i32::MAX as usize => return Ok(json),
            Ok(_) => return Err(CorpusDedupError::EventTooLarge),
            Err(NdbError::BufferOverflow) => {
                capacity = capacity
                    .checked_mul(2)
                    .ok_or(CorpusDedupError::EventTooLarge)?;
            }
            Err(error) => return Err(error.into()),
        }
    }
}

fn submit_with_retry(ndb: &Ndb, event: &str) -> Result<(), CorpusDedupError> {
    loop {
        match ndb.process_event(event) {
            Ok(()) => return Ok(()),
            Err(NdbError::NoteProcessFailed) => thread::sleep(INGEST_RETRY_DELAY),
            Err(error) => return Err(error.into()),
        }
    }
}

fn open_ndb(path: &Path, trusted_source: bool) -> Result<Ndb, CorpusDedupError> {
    let path_string = path.to_str().ok_or_else(|| {
        CorpusDedupError::Invariant(format!(
            "NostrDB path is not valid UTF-8: {}",
            path.display()
        ))
    })?;
    let flags = NDB_NO_FULLTEXT | NDB_NO_NOTE_BLOCKS | NDB_NO_STATS;
    let config = Config::new()
        .set_flags(flags)
        .set_mapsize(NDB_MAP_SIZE)
        .skip_validation(trusted_source)
        .set_ingester_threads(1);
    Ndb::new(path_string, &config).map_err(Into::into)
}

fn create_stage_directory(output: &Path) -> Result<PathBuf, CorpusDedupError> {
    let parent = output.parent().unwrap_or_else(|| Path::new("."));
    let name = output
        .file_name()
        .and_then(|name| name.to_str())
        .ok_or_else(|| {
            CorpusDedupError::Invariant(format!("invalid output directory: {}", output.display()))
        })?;
    for attempt in 0..100_u8 {
        let stage = parent.join(format!(".{name}.stage4-{}-{attempt}", std::process::id()));
        match fs::create_dir(&stage) {
            Ok(()) => return Ok(stage),
            Err(error) if error.kind() == std::io::ErrorKind::AlreadyExists => {}
            Err(source) => return Err(io_error("create", &stage, source)),
        }
    }
    Err(CorpusDedupError::Invariant(format!(
        "could not reserve a staging directory beside {}",
        output.display()
    )))
}

fn create_new_file(path: &Path) -> Result<File, CorpusDedupError> {
    OpenOptions::new()
        .create_new(true)
        .write(true)
        .open(path)
        .map_err(|source| io_error("create", path, source))
}

fn finish_writer(writer: &mut BufWriter<File>, path: &Path) -> Result<(), CorpusDedupError> {
    writer
        .flush()
        .map_err(|source| io_error("flush", path, source))?;
    writer
        .get_ref()
        .sync_all()
        .map_err(|source| io_error("sync", path, source))
}

fn event_id(record: &IndexRecord) -> EventId {
    record[EVENT_ID_BYTES..].try_into().expect("event ID width")
}

fn row_order_key(id: &EventId) -> EventId {
    let mut hasher = Sha256::new();
    hasher.update(ROW_ORDER_DOMAIN);
    hasher.update(id);
    hasher.finalize().into()
}

fn encode_hex(bytes: &[u8]) -> String {
    const HEX: &[u8; 16] = b"0123456789abcdef";
    let mut encoded = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        encoded.push(char::from(HEX[usize::from(byte >> 4)]));
        encoded.push(char::from(HEX[usize::from(byte & 0x0f)]));
    }
    encoded
}

fn io_error(operation: &'static str, path: &Path, source: std::io::Error) -> CorpusDedupError {
    CorpusDedupError::Io {
        operation,
        path: path.to_owned(),
        source,
    }
}
