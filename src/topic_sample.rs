//! Pressure-gated materialization of a real, author-disjoint topic-model sample.

use std::collections::BTreeSet;
use std::ffi::CString;
use std::fs::{self, File};
use std::io::{self, BufWriter, Read, Write};
use std::os::unix::ffi::OsStrExt;
use std::os::unix::fs::symlink;
use std::path::{Path, PathBuf};

use lmdb::{
    Cursor, Database, Environment, EnvironmentFlags, RoTransaction, Transaction as LmdbTransaction,
};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use thiserror::Error;

use crate::io_pressure::{IoPressureController, IoPressureError};

const SCHEMA_VERSION: u32 = 1;
const EVENT_ID_BYTES: usize = 32;
const NDB_NOTE_MINIMUM_BYTES: usize = 160;
const NDB_NOTE_ID_OFFSET: usize = 4;
const NDB_NOTE_PUBKEY_OFFSET: usize = 36;
const NDB_NOTE_CONTENT_LENGTH_OFFSET: usize = 144;
const NDB_NOTE_CONTENT_OFFSET: usize = 148;
const NDB_NOTE_STRINGS_OFFSET: usize = 152;
const NDB_PACKED_STR: u8 = 1;
const NDB_MAP_SIZE: usize = 256 * 1_024 * 1_024 * 1_024;
const SAMPLE_FILE: &str = "sample.jsonl";
const MANIFEST_FILE: &str = "manifest.json";
const AUTHOR_SPLIT_DOMAIN: &[u8] = b"oracle-mvp/topic-sample-author-split/v1\0";
const SELECTION_RULE: &str = "semantic-order-prefix-author-hash-disjoint-learning-first-v1";
const SEMANTIC_ORDER_RULE: &str = "preserve-source-order-exclude-raw-content-trim-empty-v1";
const TMPFS_MAGIC: libc::c_long = 0x0102_1994;

/// Configuration for one bounded real-note sample.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct TopicSampleConfig {
    /// Immutable source NostrDB. It is never opened directly.
    pub source_corpus_path: PathBuf,
    /// Frozen semantic event-ID order.
    pub ordered_event_ids_path: PathBuf,
    /// Existing manifest binding the source NostrDB and event-ID order.
    pub semantic_manifest_path: PathBuf,
    /// Create-once artifact directory on tmpfs.
    pub output_path: PathBuf,
    /// Required learning-note count.
    pub learning_rows: u64,
    /// Required author-disjoint evaluation-note count.
    pub evaluation_rows: u64,
    /// Hard bound on prefix rows that may be logically consumed.
    pub max_examined_rows: u64,
    /// Hard bound on serialized sample bytes retained in tmpfs.
    pub max_sample_bytes: u64,
    /// Public deterministic author-split seed as 64 lowercase hex digits.
    pub author_split_seed_hex: String,
}

/// One learning-first serialized sample row.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct TopicSampleRecord {
    /// `learning` or `evaluation`.
    pub split: String,
    /// Nostr event ID as lowercase hex.
    pub note_id: String,
    /// Nostr author public key as lowercase hex.
    pub pubkey: String,
    /// Exact stored kind-1 content.
    pub content: String,
}

/// One file in the completed sample artifact.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct TopicSampleFile {
    /// Relative filename.
    pub file: String,
    /// Exact file bytes.
    pub bytes: u64,
    /// Exact JSONL record count.
    pub records: u64,
    /// SHA-256 over the complete file.
    pub sha256: String,
}

/// Durable identity and accounting for one completed sample.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct TopicSampleManifest {
    /// Artifact schema.
    pub schema_version: u32,
    /// Deterministic prefix and author-split rule.
    pub selection_rule: String,
    /// SHA-256 of the small frozen semantic-corpus manifest.
    pub semantic_manifest_sha256: String,
    /// Source NostrDB identity declared by the trusted semantic manifest.
    pub declared_source_ndb_data_sha256: String,
    /// Ordered-ID identity declared by the trusted semantic manifest.
    pub declared_ordered_event_ids_sha256: String,
    /// SHA-256 over exactly the ordered-ID prefix logically consumed.
    pub sampled_order_prefix_sha256: String,
    /// Source `data.mdb` bytes observed before opening it read-only.
    pub source_ndb_data_bytes: u64,
    /// Event-ID rows available to the sampler.
    pub available_rows: u64,
    /// Public author-split seed.
    pub author_split_seed_hex: String,
    /// Required and produced learning rows.
    pub learning_rows: u64,
    /// Required and produced evaluation rows.
    pub evaluation_rows: u64,
    /// Ordered-ID rows logically consumed before both quotas filled.
    pub examined_rows: u64,
    /// Configured hard limit on logically consumed ordered-ID rows.
    pub max_examined_rows: u64,
    /// Configured hard limit on final serialized sample bytes.
    pub max_sample_bytes: u64,
    /// Learning authors represented.
    pub learning_authors: u64,
    /// Evaluation authors represented.
    pub evaluation_authors: u64,
    /// Rows skipped because their deterministic split was already full.
    pub skipped_filled_split_rows: u64,
    /// Serialized sample artifact.
    pub sample: TopicSampleFile,
    /// Exact pressure-policy identity.
    pub pressure_control: String,
}

/// A real-note sampling failure.
#[derive(Debug, Error)]
pub enum TopicSampleError {
    /// A filesystem operation failed.
    #[error("failed to {operation} `{path}`: {source}")]
    Io {
        /// Operation being attempted.
        operation: &'static str,
        /// Relevant path.
        path: PathBuf,
        /// Underlying error.
        #[source]
        source: io::Error,
    },

    /// A JSON artifact could not be read or written.
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

    /// Pressure control failed closed.
    #[error(transparent)]
    Pressure(#[from] IoPressureError),

    /// Inputs or observed state violated the frozen contract.
    #[error("topic sample invariant failed: {0}")]
    Invariant(String),
}

#[derive(Deserialize)]
struct SemanticCorpusManifest {
    schema_version: u32,
    selection_rule: String,
    source_ndb_data_sha256: String,
    output_ordered_event_ids_sha256: String,
    retained_events: u64,
}

struct OwnedNote {
    event_id: [u8; 32],
    pubkey: [u8; 32],
    content: String,
}

struct ReadOnlyCorpus {
    environment: Environment,
    note_id: Database,
    note: Database,
}

/// Read a JSON configuration and run under this process's cgroup controller.
pub fn materialize_topic_sample_from_config(
    path: impl AsRef<Path>,
) -> Result<TopicSampleManifest, TopicSampleError> {
    let path = path.as_ref();
    let config: TopicSampleConfig =
        serde_json::from_reader(File::open(path).map_err(|source| io_error("open", path, source))?)
            .map_err(|source| json_error("decode", path, source))?;
    let controller = IoPressureController::for_current_cgroup()?;
    let result = materialize_topic_sample_with_controller(&config, &controller);
    let shutdown = controller.shutdown();
    match (result, shutdown) {
        (Ok(manifest), Ok(())) => Ok(manifest),
        (Err(error), _) => Err(error),
        (Ok(_), Err(error)) => Err(error.into()),
    }
}

/// Materialize one sample through an already-running production controller.
pub fn materialize_topic_sample_with_controller(
    config: &TopicSampleConfig,
    controller: &IoPressureController,
) -> Result<TopicSampleManifest, TopicSampleError> {
    validate_config(config)?;
    let output_parent = config
        .output_path
        .parent()
        .unwrap_or_else(|| Path::new("."));
    require_tmpfs(output_parent)?;
    if config.output_path.exists() {
        return Err(TopicSampleError::Invariant(format!(
            "output already exists: {}",
            config.output_path.display()
        )));
    }
    let stage = reserve_stage(&config.output_path)?;
    let result = materialize_in_stage(config, controller, &stage);
    match result {
        Ok(manifest) => {
            if config.output_path.exists() {
                let _ = fs::remove_dir_all(&stage);
                return Err(TopicSampleError::Invariant(format!(
                    "output appeared during sampling: {}",
                    config.output_path.display()
                )));
            }
            fs::rename(&stage, &config.output_path)
                .map_err(|source| io_error("publish", &config.output_path, source))?;
            Ok(manifest)
        }
        Err(error) => {
            let _ = fs::remove_dir_all(&stage);
            Err(error)
        }
    }
}

fn materialize_in_stage(
    config: &TopicSampleConfig,
    controller: &IoPressureController,
    stage: &Path,
) -> Result<TopicSampleManifest, TopicSampleError> {
    let seed = decode_hex_32(&config.author_split_seed_hex, "author split seed")?;

    let source_permit = controller.wait_for_read()?;
    let semantic_bytes = fs::read(&config.semantic_manifest_path)
        .map_err(|source| io_error("read", &config.semantic_manifest_path, source))?;
    let semantic: SemanticCorpusManifest = serde_json::from_slice(&semantic_bytes)
        .map_err(|source| json_error("decode", &config.semantic_manifest_path, source))?;
    let ordered_bytes = fs::metadata(&config.ordered_event_ids_path)
        .map_err(|source| io_error("read metadata for", &config.ordered_event_ids_path, source))?
        .len();
    let source_data_path = config.source_corpus_path.join("data.mdb");
    let source_data_bytes = fs::metadata(&source_data_path)
        .map_err(|source| io_error("read metadata for", &source_data_path, source))?
        .len();
    let canonical_data = fs::canonicalize(&source_data_path)
        .map_err(|source| io_error("resolve", &source_data_path, source))?;
    source_permit.complete()?;
    validate_source(&semantic, ordered_bytes, source_data_bytes, config)?;

    let runtime_ndb = stage.join(".runtime-ndb");
    fs::create_dir(&runtime_ndb).map_err(|source| io_error("create", &runtime_ndb, source))?;
    symlink(&canonical_data, runtime_ndb.join("data.mdb"))
        .map_err(|source| io_error("link", runtime_ndb.join("data.mdb"), source))?;

    let open_permit = controller.wait_for_read()?;
    let corpus = open_read_only_corpus(&runtime_ndb)?;
    let transaction = corpus.environment.begin_ro_txn()?;
    let mut ordered = File::open(&config.ordered_event_ids_path)
        .map_err(|source| io_error("open", &config.ordered_event_ids_path, source))?;
    open_permit.complete()?;

    let sample_temporary_path = stage.join(".sample.jsonl.tmp");
    let mut learning_output = BufWriter::new(
        File::create(&sample_temporary_path)
            .map_err(|source| io_error("create", &sample_temporary_path, source))?,
    );
    let mut evaluation_output = Vec::<u8>::new();
    let total_target = config
        .learning_rows
        .checked_add(config.evaluation_rows)
        .ok_or_else(|| TopicSampleError::Invariant("sample row count overflowed".to_owned()))?;
    let mut learning_rows = 0_u64;
    let mut evaluation_rows = 0_u64;
    let mut examined_rows = 0_u64;
    let mut skipped_filled_split_rows = 0_u64;
    let mut serialized_bytes = 0_u64;
    let mut learning_authors = BTreeSet::new();
    let mut evaluation_authors = BTreeSet::new();
    let mut sampled_order_prefix = Sha256::new();

    while learning_rows != config.learning_rows || evaluation_rows != config.evaluation_rows {
        if examined_rows == config.max_examined_rows {
            return Err(TopicSampleError::Invariant(format!(
                "examined-row limit reached with {learning_rows}/{} learning and {evaluation_rows}/{} evaluation rows",
                config.learning_rows, config.evaluation_rows
            )));
        }
        let permit = controller.wait_for_read()?;
        let mut event_id = [0_u8; EVENT_ID_BYTES];
        ordered.read_exact(&mut event_id).map_err(|source| {
            io_error(
                "read next event ID from",
                &config.ordered_event_ids_path,
                source,
            )
        })?;
        let owned = read_note(&transaction, corpus.note_id, corpus.note, event_id)?;
        permit.complete()?;
        examined_rows += 1;
        sampled_order_prefix.update(event_id);

        let evaluation =
            is_evaluation_author(&seed, &owned.pubkey, config.evaluation_rows, total_target);
        let (split, rows, quota, authors) = if evaluation {
            (
                "evaluation",
                &mut evaluation_rows,
                config.evaluation_rows,
                &mut evaluation_authors,
            )
        } else {
            (
                "learning",
                &mut learning_rows,
                config.learning_rows,
                &mut learning_authors,
            )
        };
        if *rows == quota {
            skipped_filled_split_rows += 1;
            continue;
        }
        let record = TopicSampleRecord {
            split: split.to_owned(),
            note_id: hex(&owned.event_id),
            pubkey: hex(&owned.pubkey),
            content: owned.content,
        };
        let mut encoded = serde_json::to_vec(&record)
            .map_err(|source| json_error("encode record for", &sample_temporary_path, source))?;
        encoded.push(b'\n');
        let encoded_bytes = u64::try_from(encoded.len())
            .map_err(|_| TopicSampleError::Invariant("record size does not fit u64".to_owned()))?;
        serialized_bytes = serialized_bytes.checked_add(encoded_bytes).ok_or_else(|| {
            TopicSampleError::Invariant("sample byte count overflowed".to_owned())
        })?;
        if serialized_bytes > config.max_sample_bytes {
            return Err(TopicSampleError::Invariant(format!(
                "sample exceeded its {}-byte tmpfs budget",
                config.max_sample_bytes
            )));
        }
        if evaluation {
            evaluation_output.try_reserve(encoded.len()).map_err(|_| {
                TopicSampleError::Invariant(
                    "evaluation sample could not be retained within memory".to_owned(),
                )
            })?;
            evaluation_output.extend_from_slice(&encoded);
        } else {
            learning_output
                .write_all(&encoded)
                .map_err(|source| io_error("write", &sample_temporary_path, source))?;
        }
        authors.insert(owned.pubkey);
        *rows += 1;
    }
    learning_output
        .write_all(&evaluation_output)
        .map_err(|source| io_error("write", &sample_temporary_path, source))?;
    learning_output
        .flush()
        .map_err(|source| io_error("flush", &sample_temporary_path, source))?;
    drop(learning_output);
    drop(evaluation_output);
    drop(transaction);
    drop(corpus);
    fs::remove_dir_all(&runtime_ndb).map_err(|source| io_error("remove", &runtime_ndb, source))?;

    let sample = fs::OpenOptions::new()
        .read(true)
        .open(&sample_temporary_path)
        .map_err(|source| io_error("open", &sample_temporary_path, source))?;
    sample
        .sync_all()
        .map_err(|source| io_error("sync", &sample_temporary_path, source))?;
    drop(sample);
    let sample_path = stage.join(SAMPLE_FILE);
    fs::rename(&sample_temporary_path, &sample_path)
        .map_err(|source| io_error("publish", &sample_path, source))?;

    let sample_bytes = fs::metadata(&sample_path)
        .map_err(|source| io_error("read metadata for", &sample_path, source))?
        .len();
    if sample_bytes != serialized_bytes {
        return Err(TopicSampleError::Invariant(format!(
            "sample contains {sample_bytes} bytes but accounting recorded {serialized_bytes}"
        )));
    }
    let manifest = TopicSampleManifest {
        schema_version: SCHEMA_VERSION,
        selection_rule: SELECTION_RULE.to_owned(),
        semantic_manifest_sha256: hex(&Sha256::digest(&semantic_bytes)),
        declared_source_ndb_data_sha256: semantic.source_ndb_data_sha256,
        declared_ordered_event_ids_sha256: semantic.output_ordered_event_ids_sha256,
        sampled_order_prefix_sha256: hex(&sampled_order_prefix.finalize()),
        source_ndb_data_bytes: source_data_bytes,
        available_rows: semantic.retained_events,
        author_split_seed_hex: config.author_split_seed_hex.clone(),
        learning_rows,
        evaluation_rows,
        examined_rows,
        max_examined_rows: config.max_examined_rows,
        max_sample_bytes: config.max_sample_bytes,
        learning_authors: u64::try_from(learning_authors.len()).map_err(|_| {
            TopicSampleError::Invariant("learning author count does not fit u64".to_owned())
        })?,
        evaluation_authors: u64::try_from(evaluation_authors.len()).map_err(|_| {
            TopicSampleError::Invariant("evaluation author count does not fit u64".to_owned())
        })?,
        skipped_filled_split_rows,
        sample: TopicSampleFile {
            file: SAMPLE_FILE.to_owned(),
            bytes: sample_bytes,
            records: total_target,
            sha256: hash_file(&sample_path)?,
        },
        pressure_control:
            "cgroup-v2-io-pressure-some-250ms-window2s-pause20-low5x10s-probe1-fail60s-v1"
                .to_owned(),
    };
    let manifest_path = stage.join(MANIFEST_FILE);
    let manifest_file = File::create(&manifest_path)
        .map_err(|source| io_error("create", &manifest_path, source))?;
    serde_json::to_writer_pretty(manifest_file, &manifest)
        .map_err(|source| json_error("encode", &manifest_path, source))?;
    Ok(manifest)
}

fn open_read_only_corpus(path: &Path) -> Result<ReadOnlyCorpus, TopicSampleError> {
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

fn read_note(
    transaction: &RoTransaction<'_>,
    note_id_database: Database,
    note_database: Database,
    event_id: [u8; EVENT_ID_BYTES],
) -> Result<OwnedNote, TopicSampleError> {
    let mut low_key = [0_u8; EVENT_ID_BYTES + 8];
    low_key[..EVENT_ID_BYTES].copy_from_slice(&event_id);
    let cursor = transaction.open_ro_cursor(note_id_database)?;
    let (stored_key, primary_key) = cursor.get(Some(&low_key), None, 17)?;
    let stored_key = stored_key.unwrap_or(&low_key);
    if stored_key.len() != low_key.len() || stored_key[..EVENT_ID_BYTES] != event_id {
        return Err(TopicSampleError::Invariant(format!(
            "event {} is absent from the source NostrDB",
            hex(&event_id)
        )));
    }
    if primary_key.len() != 8 {
        return Err(TopicSampleError::Invariant(format!(
            "event {} has a malformed NostrDB primary key",
            hex(&event_id)
        )));
    }
    let note = transaction.get(note_database, &primary_key)?;
    decode_stored_note(note, event_id)
}

fn decode_stored_note(
    note: &[u8],
    expected_event_id: [u8; EVENT_ID_BYTES],
) -> Result<OwnedNote, TopicSampleError> {
    if note.len() < NDB_NOTE_MINIMUM_BYTES || note[0] != 1 {
        return Err(TopicSampleError::Invariant(
            "source NostrDB returned an incompatible stored note".to_owned(),
        ));
    }
    let stored_event_id: [u8; EVENT_ID_BYTES] = note
        [NDB_NOTE_ID_OFFSET..NDB_NOTE_ID_OFFSET + EVENT_ID_BYTES]
        .try_into()
        .expect("validated note header");
    if stored_event_id != expected_event_id {
        return Err(TopicSampleError::Invariant(format!(
            "source NostrDB returned {} for requested event {}",
            hex(&stored_event_id),
            hex(&expected_event_id)
        )));
    }
    let kind = u32::from_le_bytes(note[140..144].try_into().expect("validated note header"));
    if kind != 1 {
        return Err(TopicSampleError::Invariant(format!(
            "source NostrDB returned kind {kind} for event {}",
            hex(&expected_event_id)
        )));
    }
    let pubkey = note[NDB_NOTE_PUBKEY_OFFSET..NDB_NOTE_PUBKEY_OFFSET + EVENT_ID_BYTES]
        .try_into()
        .expect("validated note header");
    let content_length = usize::try_from(u32::from_le_bytes(
        note[NDB_NOTE_CONTENT_LENGTH_OFFSET..NDB_NOTE_CONTENT_LENGTH_OFFSET + 4]
            .try_into()
            .expect("validated note header"),
    ))
    .expect("u32 fits usize");
    let descriptor = &note[NDB_NOTE_CONTENT_OFFSET..NDB_NOTE_CONTENT_OFFSET + 4];
    let content = if descriptor[3] == NDB_PACKED_STR {
        if content_length > 3 {
            return Err(TopicSampleError::Invariant(format!(
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
            TopicSampleError::Invariant(format!(
                "event {} content offset overflowed",
                hex(&expected_event_id)
            ))
        })?;
        let end = start.checked_add(content_length).ok_or_else(|| {
            TopicSampleError::Invariant(format!(
                "event {} content length overflowed",
                hex(&expected_event_id)
            ))
        })?;
        note.get(start..end).ok_or_else(|| {
            TopicSampleError::Invariant(format!(
                "event {} content lies outside its stored note",
                hex(&expected_event_id)
            ))
        })?
    };
    let content = std::str::from_utf8(content)
        .map_err(|_| {
            TopicSampleError::Invariant(format!(
                "event {} content is not UTF-8",
                hex(&expected_event_id)
            ))
        })?
        .to_owned();
    Ok(OwnedNote {
        event_id: expected_event_id,
        pubkey,
        content,
    })
}

fn validate_config(config: &TopicSampleConfig) -> Result<(), TopicSampleError> {
    if config.learning_rows == 0
        || config.evaluation_rows == 0
        || config.max_examined_rows == 0
        || config.max_sample_bytes == 0
    {
        return Err(TopicSampleError::Invariant(
            "sample quotas and resource bounds must be positive".to_owned(),
        ));
    }
    let target = config
        .learning_rows
        .checked_add(config.evaluation_rows)
        .ok_or_else(|| TopicSampleError::Invariant("sample row count overflowed".to_owned()))?;
    if config.max_examined_rows < target {
        return Err(TopicSampleError::Invariant(
            "examined-row bound is smaller than the requested sample".to_owned(),
        ));
    }
    decode_hex_32(&config.author_split_seed_hex, "author split seed")?;
    Ok(())
}

fn validate_source(
    semantic: &SemanticCorpusManifest,
    ordered_bytes: u64,
    source_data_bytes: u64,
    config: &TopicSampleConfig,
) -> Result<(), TopicSampleError> {
    if semantic.schema_version != 1
        || semantic.selection_rule != SEMANTIC_ORDER_RULE
        || !is_sha256(&semantic.source_ndb_data_sha256)
        || !is_sha256(&semantic.output_ordered_event_ids_sha256)
        || semantic.retained_events == 0
        || source_data_bytes == 0
    {
        return Err(TopicSampleError::Invariant(
            "semantic corpus manifest is incompatible".to_owned(),
        ));
    }
    let expected_ordered_bytes = semantic
        .retained_events
        .checked_mul(EVENT_ID_BYTES as u64)
        .ok_or_else(|| TopicSampleError::Invariant("ordered-ID size overflowed".to_owned()))?;
    if ordered_bytes != expected_ordered_bytes {
        return Err(TopicSampleError::Invariant(format!(
            "ordered-ID file contains {ordered_bytes} bytes but its manifest requires {expected_ordered_bytes}"
        )));
    }
    if config.max_examined_rows > semantic.retained_events {
        return Err(TopicSampleError::Invariant(
            "examined-row bound exceeds the available semantic order".to_owned(),
        ));
    }
    Ok(())
}

fn is_evaluation_author(
    seed: &[u8; 32],
    pubkey: &[u8; 32],
    evaluation_rows: u64,
    total_rows: u64,
) -> bool {
    let mut hasher = Sha256::new();
    hasher.update(AUTHOR_SPLIT_DOMAIN);
    hasher.update(seed);
    hasher.update(pubkey);
    let digest = hasher.finalize();
    let value = u64::from_be_bytes(digest[..8].try_into().expect("SHA-256 prefix"));
    u128::from(value) * u128::from(total_rows) < (u128::from(evaluation_rows) << u64::BITS)
}

fn reserve_stage(output: &Path) -> Result<PathBuf, TopicSampleError> {
    let parent = output.parent().unwrap_or_else(|| Path::new("."));
    let name = output
        .file_name()
        .and_then(|value| value.to_str())
        .ok_or_else(|| {
            TopicSampleError::Invariant(format!("invalid output path: {}", output.display()))
        })?;
    for attempt in 0..100_u8 {
        let candidate = parent.join(format!(
            ".{name}.topic-sample-{}-{attempt}",
            std::process::id()
        ));
        match fs::create_dir(&candidate) {
            Ok(()) => return Ok(candidate),
            Err(error) if error.kind() == io::ErrorKind::AlreadyExists => {}
            Err(source) => return Err(io_error("create", &candidate, source)),
        }
    }
    Err(TopicSampleError::Invariant(format!(
        "could not reserve a staging directory beside {}",
        output.display()
    )))
}

fn require_tmpfs(path: &Path) -> Result<(), TopicSampleError> {
    let encoded = CString::new(path.as_os_str().as_bytes()).map_err(|_| {
        TopicSampleError::Invariant(format!("path contains an interior NUL: {}", path.display()))
    })?;
    let mut status = std::mem::MaybeUninit::<libc::statfs>::uninit();
    // SAFETY: `encoded` is NUL-terminated and `status` points to writable storage.
    let result = unsafe { libc::statfs(encoded.as_ptr(), status.as_mut_ptr()) };
    if result != 0 {
        return Err(io_error(
            "inspect filesystem for",
            path,
            io::Error::last_os_error(),
        ));
    }
    // SAFETY: `statfs` returned success and initialized `status`.
    let status = unsafe { status.assume_init() };
    if status.f_type != TMPFS_MAGIC {
        return Err(TopicSampleError::Invariant(format!(
            "sample output must be on tmpfs: {}",
            path.display()
        )));
    }
    Ok(())
}

fn hash_file(path: &Path) -> Result<String, TopicSampleError> {
    let mut file = File::open(path).map_err(|source| io_error("open", path, source))?;
    let mut hasher = Sha256::new();
    let mut buffer = [0_u8; 64 * 1024];
    loop {
        let read = file
            .read(&mut buffer)
            .map_err(|source| io_error("read", path, source))?;
        if read == 0 {
            break;
        }
        hasher.update(&buffer[..read]);
    }
    Ok(hex(&hasher.finalize()))
}

fn decode_hex_32(encoded: &str, name: &str) -> Result<[u8; 32], TopicSampleError> {
    if encoded.len() != 64 || !encoded.bytes().all(|byte| byte.is_ascii_hexdigit()) {
        return Err(TopicSampleError::Invariant(format!(
            "{name} must contain exactly 64 hex digits"
        )));
    }
    let mut output = [0_u8; 32];
    for (index, chunk) in encoded.as_bytes().chunks_exact(2).enumerate() {
        output[index] = (decode_nibble(chunk[0]) << 4) | decode_nibble(chunk[1]);
    }
    Ok(output)
}

fn decode_nibble(value: u8) -> u8 {
    match value {
        b'0'..=b'9' => value - b'0',
        b'a'..=b'f' => value - b'a' + 10,
        b'A'..=b'F' => value - b'A' + 10,
        _ => unreachable!("validated hexadecimal digit"),
    }
}

fn is_sha256(value: &str) -> bool {
    value.len() == 64 && value.bytes().all(|byte| byte.is_ascii_hexdigit())
}

fn hex(bytes: &[u8]) -> String {
    let mut output = String::with_capacity(bytes.len() * 2);
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    for byte in bytes {
        output.push(char::from(DIGITS[usize::from(byte >> 4)]));
        output.push(char::from(DIGITS[usize::from(byte & 0x0f)]));
    }
    output
}

fn io_error(
    operation: &'static str,
    path: impl AsRef<Path>,
    source: io::Error,
) -> TopicSampleError {
    TopicSampleError::Io {
        operation,
        path: path.as_ref().to_owned(),
        source,
    }
}

fn json_error(
    operation: &'static str,
    path: impl AsRef<Path>,
    source: serde_json::Error,
) -> TopicSampleError {
    TopicSampleError::Json {
        operation,
        path: path.as_ref().to_owned(),
        source,
    }
}
