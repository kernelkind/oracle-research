//! Immutable Oracle row order derived from the complete English-eligible corpus.

use std::ffi::OsString;
use std::fmt::Write as _;
use std::fs::{self, File, OpenOptions};
use std::io::{BufReader, BufWriter, Read, Write};
use std::path::{Path, PathBuf};

use nostrdb::{Config, Ndb, Transaction};
use serde::{Deserialize, Serialize};

use crate::artifact::hash_file;
use crate::snapshot::{
    Error, Result, io_error, ndb_error, read_manifest, require_file, write_manifest,
};

const SCHEMA_VERSION: u32 = 1;
const EVENT_ID_BYTES: usize = 32;
const MANIFEST_FILE: &str = "manifest.json";
const ORDERED_EVENT_IDS_FILE: &str = "ordered-event-ids.bin";
const NDB_DATA_FILE: &str = "data.mdb";
const NDB_MAP_SIZE: usize = 256 * 1_024 * 1_024 * 1_024;
const NDB_NO_MIGRATE: i32 = 1;
const NDB_NO_FULLTEXT: i32 = 1 << 2;
const NDB_NO_NOTE_BLOCKS: i32 = 1 << 3;
const NDB_NO_STATS: i32 = 1 << 4;

/// The complete and exact Oracle row-selection rule.
pub const SEMANTIC_ORDER_SELECTION_RULE: &str =
    "preserve-source-order-exclude-raw-content-trim-empty-v1";

type EventId = [u8; EVENT_ID_BYTES];

/// One source row omitted because its raw note content is empty after `trim()`.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ExcludedSemanticOrderEvent {
    /// Zero-based row in the source order.
    pub original_row: u64,
    /// Lowercase hexadecimal event ID.
    pub event_id: String,
    /// Byte length of the unmodified raw content.
    pub content_bytes: u64,
}

/// Complete identity and accounting for the Oracle ordered-ID artifact.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SemanticOrderManifest {
    /// Manifest schema version.
    pub schema_version: u32,
    /// Exact row-selection rule.
    pub selection_rule: String,
    /// SHA-256 of the source NostrDB's `data.mdb`.
    pub source_ndb_data_sha256: String,
    /// SHA-256 of the complete source ordered-ID file.
    pub source_ordered_event_ids_sha256: String,
    /// SHA-256 of the derived Oracle ordered-ID file.
    pub output_ordered_event_ids_sha256: String,
    /// Source ordered rows examined.
    pub input_events: u64,
    /// Rows retained in the Oracle order.
    pub retained_events: u64,
    /// Rows excluded by the selection rule.
    pub excluded_events: u64,
    /// Exact source rows excluded by the selection rule.
    pub excluded: Vec<ExcludedSemanticOrderEvent>,
}

/// Derive and atomically publish the Oracle order, or deeply verify an existing artifact.
pub fn derive_semantic_order(
    source_ndb_path: impl AsRef<Path>,
    source_ordered_event_ids_path: impl AsRef<Path>,
    output_path: impl AsRef<Path>,
) -> Result<SemanticOrderManifest> {
    let source_ndb_path = source_ndb_path.as_ref();
    let source_ordered_event_ids_path = source_ordered_event_ids_path.as_ref();
    let output_path = output_path.as_ref();
    require_file(&source_ndb_path.join(NDB_DATA_FILE))?;
    require_file(source_ordered_event_ids_path)?;

    if output_path.exists() {
        return verify_semantic_order(source_ndb_path, source_ordered_event_ids_path, output_path);
    }

    let parent = output_path.parent().unwrap_or_else(|| Path::new("."));
    fs::create_dir_all(parent).map_err(|source| io_error("create", parent, source))?;
    let stage_path = stage_path(output_path)?;
    match fs::create_dir(&stage_path) {
        Ok(()) => {}
        Err(source) if source.kind() == std::io::ErrorKind::AlreadyExists => {
            return Err(Error::IncompleteStage(stage_path));
        }
        Err(source) => return Err(io_error("create", &stage_path, source)),
    }

    let result = derive_in_stage(source_ndb_path, source_ordered_event_ids_path, &stage_path);
    let manifest = match result {
        Ok(manifest) => manifest,
        Err(error) => {
            let _ = fs::remove_dir_all(&stage_path);
            return Err(error);
        }
    };
    if output_path.exists() {
        let _ = fs::remove_dir_all(&stage_path);
        return Err(Error::ArtifactExists(output_path.to_owned()));
    }
    fs::rename(&stage_path, output_path)
        .map_err(|source| io_error("publish", output_path, source))?;
    File::open(parent)
        .and_then(|directory| directory.sync_all())
        .map_err(|source| io_error("sync", parent, source))?;
    Ok(manifest)
}

/// Deeply verify an existing Oracle order against its current source files.
pub fn verify_semantic_order(
    source_ndb_path: impl AsRef<Path>,
    source_ordered_event_ids_path: impl AsRef<Path>,
    output_path: impl AsRef<Path>,
) -> Result<SemanticOrderManifest> {
    let source_ndb_path = source_ndb_path.as_ref();
    let source_ordered_event_ids_path = source_ordered_event_ids_path.as_ref();
    let output_path = output_path.as_ref();
    let source_data_path = source_ndb_path.join(NDB_DATA_FILE);
    let output_ordered_path = output_path.join(ORDERED_EVENT_IDS_FILE);
    let manifest_path = output_path.join(MANIFEST_FILE);
    require_file(&source_data_path)?;
    require_file(source_ordered_event_ids_path)?;
    require_file(&output_ordered_path)?;
    require_file(&manifest_path)?;

    let manifest: SemanticOrderManifest = read_manifest(&manifest_path)?;
    validate_manifest_shape(&manifest)?;
    let source_data_sha256 = hash_file(&source_data_path)?;
    require_hash(
        "source NostrDB data",
        &source_data_sha256,
        &manifest.source_ndb_data_sha256,
    )?;
    let source_ordered_sha256 = hash_file(source_ordered_event_ids_path)?;
    require_hash(
        "source ordered-ID",
        &source_ordered_sha256,
        &manifest.source_ordered_event_ids_sha256,
    )?;
    let output_ordered_sha256 = hash_file(&output_ordered_path)?;
    require_hash(
        "output ordered-ID",
        &output_ordered_sha256,
        &manifest.output_ordered_event_ids_sha256,
    )?;
    require_record_count(
        source_ordered_event_ids_path,
        manifest.input_events,
        "source ordered-ID",
    )?;
    require_record_count(
        &output_ordered_path,
        manifest.retained_events,
        "output ordered-ID",
    )?;

    verify_rows(
        source_ndb_path,
        source_ordered_event_ids_path,
        &output_ordered_path,
        &manifest,
    )?;

    require_hash(
        "source NostrDB data",
        &hash_file(&source_data_path)?,
        &source_data_sha256,
    )?;
    require_hash(
        "source ordered-ID",
        &hash_file(source_ordered_event_ids_path)?,
        &source_ordered_sha256,
    )?;
    require_hash(
        "output ordered-ID",
        &hash_file(&output_ordered_path)?,
        &output_ordered_sha256,
    )?;
    Ok(manifest)
}

fn derive_in_stage(
    source_ndb_path: &Path,
    source_ordered_event_ids_path: &Path,
    stage_path: &Path,
) -> Result<SemanticOrderManifest> {
    let source_data_path = source_ndb_path.join(NDB_DATA_FILE);
    let source_ndb_data_sha256 = hash_file(&source_data_path)?;
    let source_ordered_event_ids_sha256 = hash_file(source_ordered_event_ids_path)?;
    let input_events = record_count(source_ordered_event_ids_path, "source ordered-ID")?;

    let source = open_source_ndb(source_ndb_path)?;
    let transaction = Transaction::new(&source)
        .map_err(|source| ndb_error("open transaction on", source_ndb_path, source))?;
    let mut source_ordered = BufReader::new(
        File::open(source_ordered_event_ids_path)
            .map_err(|source| io_error("open", source_ordered_event_ids_path, source))?,
    );
    let output_ordered_path = stage_path.join(ORDERED_EVENT_IDS_FILE);
    let output = OpenOptions::new()
        .create_new(true)
        .write(true)
        .open(&output_ordered_path)
        .map_err(|source| io_error("create", &output_ordered_path, source))?;
    let mut output_ordered = BufWriter::new(output);
    let mut retained_events = 0_u64;
    let mut excluded = Vec::new();

    for original_row in 0..input_events {
        let id = read_id(&mut source_ordered, source_ordered_event_ids_path)?;
        let note = source
            .get_note_by_id(&transaction, &id)
            .map_err(|source| ndb_error("load ordered event from", source_ndb_path, source))?;
        let content = note.content();
        if content.trim().is_empty() {
            excluded.push(ExcludedSemanticOrderEvent {
                original_row,
                event_id: encode_hex(&id),
                content_bytes: u64::try_from(content.len()).map_err(|_| {
                    Error::Invariant("note content byte length does not fit u64".to_owned())
                })?,
            });
        } else {
            output_ordered
                .write_all(&id)
                .map_err(|source| io_error("write", &output_ordered_path, source))?;
            retained_events = increment(retained_events, "retained event count")?;
        }
    }
    output_ordered
        .flush()
        .map_err(|source| io_error("flush", &output_ordered_path, source))?;
    output_ordered
        .get_ref()
        .sync_all()
        .map_err(|source| io_error("sync", &output_ordered_path, source))?;
    drop(output_ordered);
    drop(transaction);
    drop(source);

    require_hash(
        "source NostrDB data",
        &hash_file(&source_data_path)?,
        &source_ndb_data_sha256,
    )?;
    require_hash(
        "source ordered-ID",
        &hash_file(source_ordered_event_ids_path)?,
        &source_ordered_event_ids_sha256,
    )?;
    let excluded_events = u64::try_from(excluded.len())
        .map_err(|_| Error::Invariant("excluded event count does not fit u64".to_owned()))?;
    if retained_events.checked_add(excluded_events) != Some(input_events) {
        return Err(Error::Invariant(format!(
            "derived {retained_events} retained plus {excluded_events} excluded rows from {input_events} source rows"
        )));
    }
    require_record_count(&output_ordered_path, retained_events, "output ordered-ID")?;

    let manifest = SemanticOrderManifest {
        schema_version: SCHEMA_VERSION,
        selection_rule: SEMANTIC_ORDER_SELECTION_RULE.to_owned(),
        source_ndb_data_sha256,
        source_ordered_event_ids_sha256,
        output_ordered_event_ids_sha256: hash_file(&output_ordered_path)?,
        input_events,
        retained_events,
        excluded_events,
        excluded,
    };
    validate_manifest_shape(&manifest)?;
    write_manifest(&stage_path.join(MANIFEST_FILE), &manifest)?;
    File::open(stage_path)
        .and_then(|directory| directory.sync_all())
        .map_err(|source| io_error("sync", stage_path, source))?;
    Ok(manifest)
}

fn verify_rows(
    source_ndb_path: &Path,
    source_ordered_event_ids_path: &Path,
    output_ordered_event_ids_path: &Path,
    manifest: &SemanticOrderManifest,
) -> Result<()> {
    let source = open_source_ndb(source_ndb_path)?;
    let transaction = Transaction::new(&source)
        .map_err(|source| ndb_error("open transaction on", source_ndb_path, source))?;
    let mut source_ordered = BufReader::new(
        File::open(source_ordered_event_ids_path)
            .map_err(|source| io_error("open", source_ordered_event_ids_path, source))?,
    );
    let mut output_ordered = BufReader::new(
        File::open(output_ordered_event_ids_path)
            .map_err(|source| io_error("open", output_ordered_event_ids_path, source))?,
    );
    let mut output_row = 0_u64;
    let mut excluded_index = 0_usize;

    for original_row in 0..manifest.input_events {
        let id = read_id(&mut source_ordered, source_ordered_event_ids_path)?;
        let note = source
            .get_note_by_id(&transaction, &id)
            .map_err(|source| ndb_error("load ordered event from", source_ndb_path, source))?;
        if note.content().trim().is_empty() {
            let actual = ExcludedSemanticOrderEvent {
                original_row,
                event_id: encode_hex(&id),
                content_bytes: u64::try_from(note.content().len()).map_err(|_| {
                    Error::Invariant("note content byte length does not fit u64".to_owned())
                })?,
            };
            let expected = manifest.excluded.get(excluded_index).ok_or_else(|| {
                Error::Invariant(format!(
                    "source row {original_row} is trim-empty but is absent from the exclusion manifest"
                ))
            })?;
            if expected != &actual {
                return Err(Error::Invariant(format!(
                    "source row {original_row} exclusion does not match the manifest"
                )));
            }
            excluded_index += 1;
        } else {
            let output_id = read_id(&mut output_ordered, output_ordered_event_ids_path)?;
            if output_id != id {
                return Err(Error::Invariant(format!(
                    "retained output row {output_row} contains event {} but source row {original_row} requires {}",
                    encode_hex(&output_id),
                    encode_hex(&id)
                )));
            }
            output_row = increment(output_row, "retained output row")?;
        }
    }
    if output_row != manifest.retained_events || excluded_index != manifest.excluded.len() {
        return Err(Error::Invariant(format!(
            "verified {output_row} retained and {excluded_index} excluded rows; manifest records {} retained and {} excluded",
            manifest.retained_events,
            manifest.excluded.len()
        )));
    }
    Ok(())
}

fn validate_manifest_shape(manifest: &SemanticOrderManifest) -> Result<()> {
    if manifest.schema_version != SCHEMA_VERSION {
        return Err(Error::Invariant(format!(
            "semantic-order schema {} does not match required {SCHEMA_VERSION}",
            manifest.schema_version
        )));
    }
    if manifest.selection_rule != SEMANTIC_ORDER_SELECTION_RULE {
        return Err(Error::Invariant(format!(
            "semantic-order selection rule `{}` does not match required `{SEMANTIC_ORDER_SELECTION_RULE}`",
            manifest.selection_rule
        )));
    }
    for (name, value) in [
        ("source NostrDB data", &manifest.source_ndb_data_sha256),
        (
            "source ordered-ID",
            &manifest.source_ordered_event_ids_sha256,
        ),
        (
            "output ordered-ID",
            &manifest.output_ordered_event_ids_sha256,
        ),
    ] {
        if !is_sha256(value) {
            return Err(Error::Invariant(format!(
                "semantic-order {name} SHA-256 is invalid"
            )));
        }
    }
    let excluded_events = u64::try_from(manifest.excluded.len())
        .map_err(|_| Error::Invariant("excluded event count does not fit u64".to_owned()))?;
    if manifest.excluded_events != excluded_events
        || manifest
            .retained_events
            .checked_add(manifest.excluded_events)
            != Some(manifest.input_events)
    {
        return Err(Error::Invariant(
            "semantic-order event counts are inconsistent".to_owned(),
        ));
    }
    Ok(())
}

fn open_source_ndb(path: &Path) -> Result<Ndb> {
    let path_string = path
        .to_str()
        .ok_or_else(|| Error::NonUtf8Path(path.to_owned()))?;
    let config = Config::new()
        .set_flags(NDB_NO_MIGRATE | NDB_NO_FULLTEXT | NDB_NO_NOTE_BLOCKS | NDB_NO_STATS)
        .set_mapsize(NDB_MAP_SIZE)
        .skip_validation(true)
        .set_ingester_threads(1);
    Ndb::new(path_string, &config)
        .map_err(|source| ndb_error("open without migration", path, source))
}

fn record_count(path: &Path, label: &str) -> Result<u64> {
    let bytes = fs::metadata(path)
        .map_err(|source| io_error("read metadata for", path, source))?
        .len();
    if !bytes.is_multiple_of(EVENT_ID_BYTES as u64) {
        return Err(Error::Invariant(format!(
            "{label} file `{}` ends with a partial 32-byte event ID",
            path.display()
        )));
    }
    Ok(bytes / EVENT_ID_BYTES as u64)
}

fn require_record_count(path: &Path, expected: u64, label: &str) -> Result<()> {
    let actual = record_count(path, label)?;
    if actual != expected {
        return Err(Error::Invariant(format!(
            "{label} file contains {actual} records; expected {expected}"
        )));
    }
    Ok(())
}

fn read_id(reader: &mut impl Read, path: &Path) -> Result<EventId> {
    let mut id = [0_u8; EVENT_ID_BYTES];
    reader
        .read_exact(&mut id)
        .map_err(|source| io_error("read", path, source))?;
    Ok(id)
}

fn require_hash(label: &str, actual: &str, expected: &str) -> Result<()> {
    if actual != expected {
        return Err(Error::Invariant(format!(
            "semantic-order {label} SHA-256 is {actual}; expected {expected}"
        )));
    }
    Ok(())
}

fn increment(value: u64, label: &str) -> Result<u64> {
    value
        .checked_add(1)
        .ok_or_else(|| Error::Invariant(format!("{label} overflowed u64")))
}

fn encode_hex(id: &EventId) -> String {
    let mut encoded = String::with_capacity(EVENT_ID_BYTES * 2);
    for byte in id {
        write!(&mut encoded, "{byte:02x}").expect("writing to a String cannot fail");
    }
    encoded
}

fn is_sha256(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || matches!(byte, b'a'..=b'f'))
}

fn stage_path(output_path: &Path) -> Result<PathBuf> {
    let name = output_path.file_name().ok_or_else(|| {
        Error::Invariant(format!(
            "semantic-order output has no file name: {}",
            output_path.display()
        ))
    })?;
    let mut stage_name = OsString::from(".");
    stage_name.push(name);
    stage_name.push(".partial");
    Ok(output_path
        .parent()
        .unwrap_or_else(|| Path::new("."))
        .join(stage_name))
}
