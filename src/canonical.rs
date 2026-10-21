//! Exact-content canonicalization and deterministic corpus row ordering.

use std::cmp::Reverse;
use std::collections::{BTreeMap, BinaryHeap};
use std::fs::{self, File, OpenOptions};
use std::io::{BufReader, BufWriter, Read, Write};
use std::ops::ControlFlow;
use std::path::{Path, PathBuf};

use nostrdb::{Filter, Ndb, Note, Transaction};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

use crate::artifact::{ArtifactFile, describe_fixed_artifact};
use crate::snapshot::{
    CorpusManifest, DamusSnapshot, EligibilityRules, Error, Result, Validation, count_with_db,
    create_directory, io_error, ndb_error, open_ndb, read_manifest, require_directory,
    require_file, verify_corpus_manifest, write_manifest,
};

pub(crate) const CONTENT_RULE: &str = "byte-identical-utf8-v1";
pub(crate) const CANONICAL_EVENT_RULE: &str = "lowest-event-id-v1";
pub(crate) const ROW_ORDER_RULE: &str = "sha256-domain-separated-event-id-v1";
const CANONICAL_MANIFEST_SCHEMA_VERSION: u32 = 2;
const ROW_ORDER_DOMAIN: &[u8] = b"oracle-mvp/canonical-row-order/v1\0";
const EVENT_ID_BYTES: usize = 32;
const CONTENT_INDEX_BYTES: usize = EVENT_ID_BYTES * 2;
const ALIAS_RECORD_BYTES: usize = EVENT_ID_BYTES * 2;
const ROW_SORT_RECORD_BYTES: usize = EVENT_ID_BYTES * 2;
const SORT_BUFFER_BYTES: usize = 64 * 1024 * 1024;

type EventId = [u8; EVENT_ID_BYTES];

/// Counts produced by exact-content canonicalization.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct CanonicalCounts {
    /// Eligible events read from the corpus NostrDB.
    pub eligible_events: u64,
    /// Unique byte-identical content groups.
    pub canonical_rows: u64,
    /// Eligible events represented by another event's canonical row.
    pub duplicate_events: u64,
}

/// Backward-compatible name for canonical fixed-record artifacts.
pub type CanonicalArtifact = ArtifactFile;

/// Durable description of canonical event rows and event aliases.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct CanonicalManifest {
    /// Manifest schema version.
    pub schema_version: u32,
    /// SHA-256 inherited from the source snapshot import.
    pub source_snapshot_sha256: String,
    /// Eligibility contract inherited from corpus derivation.
    pub eligibility: EligibilityRules,
    /// Exact content-equivalence rule.
    pub content_rule: String,
    /// Rule used to select one event from an exact-content group.
    pub canonical_event_rule: String,
    /// Rule used to assign canonical events to deterministic rows.
    pub row_order_rule: String,
    /// Canonicalization counts.
    pub counts: CanonicalCounts,
    /// Canonical event IDs in deterministic row order, one 32-byte ID per record.
    pub rows: CanonicalArtifact,
    /// Event ID followed by canonical event ID, sorted by event ID.
    pub aliases: CanonicalArtifact,
}

pub(crate) fn canonicalize_corpus(pipeline: &DamusSnapshot) -> Result<CanonicalManifest> {
    let layout = pipeline.layout();
    let corpus_manifest_path = layout.corpus_manifest();
    let corpus_path = layout.corpus_db();
    require_file(&corpus_manifest_path)?;
    require_directory(&corpus_path)?;
    let corpus_manifest: CorpusManifest = read_manifest(&corpus_manifest_path)?;
    verify_corpus_manifest(&corpus_manifest)?;
    let corpus_db = open_ndb(&corpus_path, Validation::TrustedSource)?;
    let corpus_total = count_with_db(&corpus_db, &corpus_path, None)?;
    if corpus_total != corpus_manifest.eligible_events {
        return Err(Error::Invariant(format!(
            "corpus manifest records {} eligible events but corpus NostrDB contains {corpus_total}",
            corpus_manifest.eligible_events
        )));
    }

    let stage = pipeline.prepare_stage(&layout.canonical_dir(), &layout.canonical_stage())?;
    let temporary = stage.join("temporary");
    create_directory(&temporary)?;

    let content_unsorted = temporary.join("content-index.unsorted.bin");
    let content_sorted = temporary.join("content-index.sorted.bin");
    let indexed = write_content_index(&corpus_db, &corpus_path, &content_unsorted)?;
    if indexed != corpus_total {
        return Err(Error::Invariant(format!(
            "indexed {indexed} corpus events but expected {corpus_total}"
        )));
    }
    let content_records = external_sort::<CONTENT_INDEX_BYTES>(
        &content_unsorted,
        &content_sorted,
        &temporary.join("content-sort-runs"),
    )?;
    remove_file(&content_unsorted)?;
    if content_records != corpus_total {
        return Err(Error::Invariant(format!(
            "sorted {content_records} content records but expected {corpus_total}"
        )));
    }

    let rows_unsorted = temporary.join("rows.unsorted.bin");
    let aliases_unsorted = temporary.join("aliases.unsorted.bin");
    let counts = write_canonical_records(
        &corpus_db,
        &corpus_path,
        &content_sorted,
        &rows_unsorted,
        &aliases_unsorted,
    )?;
    remove_file(&content_sorted)?;
    if counts.eligible_events != corpus_total {
        return Err(Error::Invariant(format!(
            "canonicalized {} corpus events but expected {corpus_total}",
            counts.eligible_events
        )));
    }

    let rows_sorted = temporary.join("rows.sorted.bin");
    let sorted_rows = external_sort::<ROW_SORT_RECORD_BYTES>(
        &rows_unsorted,
        &rows_sorted,
        &temporary.join("row-sort-runs"),
    )?;
    remove_file(&rows_unsorted)?;
    if sorted_rows != counts.canonical_rows {
        return Err(Error::Invariant(format!(
            "sorted {sorted_rows} canonical rows but expected {}",
            counts.canonical_rows
        )));
    }
    write_rows(&rows_sorted, &stage.join("rows.bin"), counts.canonical_rows)?;
    remove_file(&rows_sorted)?;

    let aliases_path = stage.join("aliases.bin");
    let sorted_aliases = external_sort::<ALIAS_RECORD_BYTES>(
        &aliases_unsorted,
        &aliases_path,
        &temporary.join("alias-sort-runs"),
    )?;
    remove_file(&aliases_unsorted)?;
    if sorted_aliases != counts.eligible_events {
        return Err(Error::Invariant(format!(
            "sorted {sorted_aliases} aliases but expected {}",
            counts.eligible_events
        )));
    }

    let rows = describe_fixed_artifact(
        &stage.join("rows.bin"),
        "rows.bin",
        EVENT_ID_BYTES,
        counts.canonical_rows,
    )?;
    let aliases = describe_fixed_artifact(
        &aliases_path,
        "aliases.bin",
        ALIAS_RECORD_BYTES,
        counts.eligible_events,
    )?;
    fs::remove_dir_all(&temporary).map_err(|source| io_error("remove", &temporary, source))?;

    let manifest = CanonicalManifest {
        schema_version: CANONICAL_MANIFEST_SCHEMA_VERSION,
        source_snapshot_sha256: corpus_manifest.source_snapshot_sha256,
        eligibility: corpus_manifest.eligibility,
        content_rule: CONTENT_RULE.to_owned(),
        canonical_event_rule: CANONICAL_EVENT_RULE.to_owned(),
        row_order_rule: ROW_ORDER_RULE.to_owned(),
        counts,
        rows,
        aliases,
    };
    write_manifest(&stage.join("manifest.json"), &manifest)?;
    drop(corpus_db);
    pipeline.publish_stage(&stage, &layout.canonical_dir())?;
    Ok(manifest)
}

fn write_content_index(ndb: &Ndb, ndb_path: &Path, output: &Path) -> Result<u64> {
    let file = create_new_file(output)?;
    let mut writer = BufWriter::new(file);
    let txn = Transaction::new(ndb)
        .map_err(|source| ndb_error("open transaction on", ndb_path, source))?;
    let all = Filter::new().build();
    let count = ndb
        .try_fold(&txn, &[all], Ok(0_u64), |state, note| {
            index_note(state, note, &mut writer, output)
        })
        .map_err(|source| ndb_error("scan", ndb_path, source))??;
    finish_writer(&mut writer, output)?;
    Ok(count)
}

fn index_note(
    state: Result<u64>,
    note: Note<'_>,
    writer: &mut BufWriter<File>,
    output: &Path,
) -> ControlFlow<Result<u64>, Result<u64>> {
    let Ok(count) = state else {
        return ControlFlow::Break(state);
    };
    let mut record = [0_u8; CONTENT_INDEX_BYTES];
    record[..EVENT_ID_BYTES].copy_from_slice(&content_hash(note.content()));
    record[EVENT_ID_BYTES..].copy_from_slice(note.id());
    if let Err(source) = writer.write_all(&record) {
        return ControlFlow::Break(Err(io_error("write", output, source)));
    }
    match count.checked_add(1) {
        Some(count) => ControlFlow::Continue(Ok(count)),
        None => ControlFlow::Break(Err(Error::Invariant(
            "content-index count overflowed u64".to_owned(),
        ))),
    }
}

fn write_canonical_records(
    ndb: &Ndb,
    ndb_path: &Path,
    content_index: &Path,
    rows_output: &Path,
    aliases_output: &Path,
) -> Result<CanonicalCounts> {
    let mut reader = BufReader::new(open_file(content_index)?);
    let mut rows = BufWriter::new(create_new_file(rows_output)?);
    let mut aliases = BufWriter::new(create_new_file(aliases_output)?);
    let mut output = CanonicalRecordOutput {
        rows: &mut rows,
        rows_path: rows_output,
        aliases: &mut aliases,
        aliases_path: aliases_output,
    };
    let txn = Transaction::new(ndb)
        .map_err(|source| ndb_error("open transaction on", ndb_path, source))?;
    let mut current_hash: Option<[u8; EVENT_ID_BYTES]> = None;
    let mut event_ids = Vec::new();
    let mut eligible_events = 0_u64;
    let mut canonical_rows = 0_u64;

    while let Some(record) = read_record::<CONTENT_INDEX_BYTES>(&mut reader, content_index)? {
        let hash: [u8; EVENT_ID_BYTES] = record[..EVENT_ID_BYTES]
            .try_into()
            .expect("content hash width");
        let event_id: EventId = record[EVENT_ID_BYTES..].try_into().expect("event ID width");
        if current_hash.is_some_and(|current| current != hash) {
            let group_hash = current_hash.expect("current content hash");
            let group = write_hash_group(ndb, ndb_path, &txn, group_hash, &event_ids, &mut output)?;
            eligible_events = checked_add(eligible_events, group.eligible_events, "eligible")?;
            canonical_rows = checked_add(canonical_rows, group.canonical_rows, "canonical")?;
            event_ids.clear();
        }
        current_hash = Some(hash);
        event_ids.push(event_id);
    }

    if let Some(group_hash) = current_hash {
        let group = write_hash_group(ndb, ndb_path, &txn, group_hash, &event_ids, &mut output)?;
        eligible_events = checked_add(eligible_events, group.eligible_events, "eligible")?;
        canonical_rows = checked_add(canonical_rows, group.canonical_rows, "canonical")?;
    }

    finish_writer(output.rows, rows_output)?;
    finish_writer(output.aliases, aliases_output)?;
    let duplicate_events = eligible_events.checked_sub(canonical_rows).ok_or_else(|| {
        Error::Invariant(format!(
            "created {canonical_rows} canonical rows from {eligible_events} events"
        ))
    })?;
    Ok(CanonicalCounts {
        eligible_events,
        canonical_rows,
        duplicate_events,
    })
}

#[derive(Clone, Copy, Debug, Default)]
struct GroupCounts {
    eligible_events: u64,
    canonical_rows: u64,
}

struct CanonicalRecordOutput<'a> {
    rows: &'a mut BufWriter<File>,
    rows_path: &'a Path,
    aliases: &'a mut BufWriter<File>,
    aliases_path: &'a Path,
}

fn write_hash_group(
    ndb: &Ndb,
    ndb_path: &Path,
    txn: &Transaction,
    expected_hash: [u8; EVENT_ID_BYTES],
    event_ids: &[EventId],
    output: &mut CanonicalRecordOutput<'_>,
) -> Result<GroupCounts> {
    let mut exact_groups: BTreeMap<Vec<u8>, Vec<EventId>> = BTreeMap::new();
    for event_id in event_ids {
        let note = ndb
            .get_note_by_id(txn, event_id)
            .map_err(|source| ndb_error("load note from", ndb_path, source))?;
        let actual_hash = content_hash(note.content());
        if actual_hash != expected_hash {
            return Err(Error::Invariant(format!(
                "event {} does not match its content-index hash",
                encode_hex(event_id)
            )));
        }
        exact_groups
            .entry(note.content().as_bytes().to_vec())
            .or_default()
            .push(*event_id);
    }

    let mut counts = GroupCounts::default();
    for event_ids in exact_groups.values_mut() {
        event_ids.sort_unstable();
        let canonical = event_ids[0];
        let mut row_record = [0_u8; ROW_SORT_RECORD_BYTES];
        row_record[..EVENT_ID_BYTES].copy_from_slice(&row_order_key(&canonical));
        row_record[EVENT_ID_BYTES..].copy_from_slice(&canonical);
        output
            .rows
            .write_all(&row_record)
            .map_err(|source| io_error("write", output.rows_path, source))?;

        for event_id in event_ids.iter() {
            let mut alias_record = [0_u8; ALIAS_RECORD_BYTES];
            alias_record[..EVENT_ID_BYTES].copy_from_slice(event_id);
            alias_record[EVENT_ID_BYTES..].copy_from_slice(&canonical);
            output
                .aliases
                .write_all(&alias_record)
                .map_err(|source| io_error("write", output.aliases_path, source))?;
        }
        counts.eligible_events = checked_add(
            counts.eligible_events,
            u64::try_from(event_ids.len()).map_err(|_| {
                Error::Invariant("content group length does not fit u64".to_owned())
            })?,
            "content-group eligible",
        )?;
        counts.canonical_rows = checked_add(counts.canonical_rows, 1, "content-group rows")?;
    }
    Ok(counts)
}

fn write_rows(sorted_rows: &Path, output: &Path, expected: u64) -> Result<()> {
    let mut reader = BufReader::new(open_file(sorted_rows)?);
    let mut writer = BufWriter::new(create_new_file(output)?);
    let mut records = 0_u64;
    while let Some(record) = read_record::<ROW_SORT_RECORD_BYTES>(&mut reader, sorted_rows)? {
        writer
            .write_all(&record[EVENT_ID_BYTES..])
            .map_err(|source| io_error("write", output, source))?;
        records = checked_add(records, 1, "row output")?;
    }
    finish_writer(&mut writer, output)?;
    if records != expected {
        return Err(Error::Invariant(format!(
            "wrote {records} row records but expected {expected}"
        )));
    }
    Ok(())
}

fn external_sort<const N: usize>(input: &Path, output: &Path, run_dir: &Path) -> Result<u64> {
    if N == 0 {
        return Err(Error::Invariant(
            "cannot sort zero-width records".to_owned(),
        ));
    }
    fs::create_dir(run_dir).map_err(|source| io_error("create", run_dir, source))?;
    let mut input_reader = BufReader::new(open_file(input)?);
    let records_per_run = (SORT_BUFFER_BYTES / N).max(1);
    let mut run_paths = Vec::new();

    loop {
        let mut records = Vec::with_capacity(records_per_run);
        while records.len() < records_per_run {
            match read_record::<N>(&mut input_reader, input)? {
                Some(record) => records.push(record),
                None => break,
            }
        }
        if records.is_empty() {
            break;
        }
        records.sort_unstable();
        let run_path = run_dir.join(format!("run-{:06}.bin", run_paths.len()));
        let mut writer = BufWriter::new(create_new_file(&run_path)?);
        for record in records {
            writer
                .write_all(&record)
                .map_err(|source| io_error("write", &run_path, source))?;
        }
        finish_writer(&mut writer, &run_path)?;
        run_paths.push(run_path);
    }

    let total = merge_runs::<N>(&run_paths, output)?;
    fs::remove_dir_all(run_dir).map_err(|source| io_error("remove", run_dir, source))?;
    Ok(total)
}

fn merge_runs<const N: usize>(run_paths: &[PathBuf], output: &Path) -> Result<u64> {
    let mut readers = run_paths
        .iter()
        .map(|path| open_file(path).map(BufReader::new))
        .collect::<Result<Vec<_>>>()?;
    let mut heap: BinaryHeap<Reverse<([u8; N], usize)>> = BinaryHeap::new();
    for (index, reader) in readers.iter_mut().enumerate() {
        if let Some(record) = read_record::<N>(reader, &run_paths[index])? {
            heap.push(Reverse((record, index)));
        }
    }

    let mut writer = BufWriter::new(create_new_file(output)?);
    let mut count = 0_u64;
    while let Some(Reverse((record, run_index))) = heap.pop() {
        writer
            .write_all(&record)
            .map_err(|source| io_error("write", output, source))?;
        count = checked_add(count, 1, "external-sort output")?;
        if let Some(next) = read_record::<N>(&mut readers[run_index], &run_paths[run_index])? {
            heap.push(Reverse((next, run_index)));
        }
    }
    finish_writer(&mut writer, output)?;
    Ok(count)
}

fn read_record<const N: usize>(reader: &mut impl Read, path: &Path) -> Result<Option<[u8; N]>> {
    let mut record = [0_u8; N];
    let mut offset = 0;
    while offset < N {
        let bytes = reader
            .read(&mut record[offset..])
            .map_err(|source| io_error("read", path, source))?;
        if bytes == 0 {
            if offset == 0 {
                return Ok(None);
            }
            return Err(Error::Invariant(format!(
                "artifact `{}` ends with a partial {N}-byte record",
                path.display()
            )));
        }
        offset += bytes;
    }
    Ok(Some(record))
}

fn create_new_file(path: &Path) -> Result<File> {
    OpenOptions::new()
        .create_new(true)
        .write(true)
        .open(path)
        .map_err(|source| io_error("create", path, source))
}

fn open_file(path: &Path) -> Result<File> {
    File::open(path).map_err(|source| io_error("open", path, source))
}

fn remove_file(path: &Path) -> Result<()> {
    fs::remove_file(path).map_err(|source| io_error("remove", path, source))
}

fn finish_writer(writer: &mut BufWriter<File>, path: &Path) -> Result<()> {
    writer
        .flush()
        .map_err(|source| io_error("flush", path, source))?;
    writer
        .get_ref()
        .sync_all()
        .map_err(|source| io_error("sync", path, source))
}

fn content_hash(content: &str) -> [u8; EVENT_ID_BYTES] {
    Sha256::digest(content.as_bytes()).into()
}

fn row_order_key(event_id: &EventId) -> [u8; EVENT_ID_BYTES] {
    let mut hasher = Sha256::new();
    hasher.update(ROW_ORDER_DOMAIN);
    hasher.update(event_id);
    hasher.finalize().into()
}

fn checked_add(left: u64, right: u64, name: &str) -> Result<u64> {
    left.checked_add(right)
        .ok_or_else(|| Error::Invariant(format!("{name} count overflowed u64")))
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
