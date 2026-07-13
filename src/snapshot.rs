//! Damus snapshot ingestion and corpus eligibility.

use std::fs::{self, File, OpenOptions};
use std::io::{self, BufRead, BufReader, BufWriter, Read, Write};
use std::ops::ControlFlow;
use std::path::{Path, PathBuf};

use nostrdb::{Config, Filter, Ndb, Note, NoteReply, Transaction};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use thiserror::Error;

pub use crate::canonical::{CanonicalCounts, CanonicalManifest};

/// Result type for snapshot pipeline operations.
pub type Result<T> = std::result::Result<T, Error>;

/// A snapshot pipeline failure.
#[derive(Debug, Error)]
pub enum Error {
    /// A filesystem operation failed.
    #[error("failed to {operation} `{path}`: {source}")]
    Io {
        /// Filesystem operation being attempted.
        operation: &'static str,
        /// Path on which the operation failed.
        path: PathBuf,
        /// Underlying filesystem error.
        #[source]
        source: io::Error,
    },

    /// A NostrDB operation failed.
    #[error("failed to {operation} NostrDB `{path}`: {source}")]
    Ndb {
        /// Database operation being attempted.
        operation: &'static str,
        /// Database path on which the operation failed.
        path: PathBuf,
        /// Underlying NostrDB error.
        #[source]
        source: nostrdb::Error,
    },

    /// A manifest could not be encoded or decoded.
    #[error("failed to {operation} manifest `{path}`: {source}")]
    Manifest {
        /// Manifest operation being attempted.
        operation: &'static str,
        /// Manifest path on which the operation failed.
        path: PathBuf,
        /// Underlying JSON error.
        #[source]
        source: serde_json::Error,
    },

    /// A completed artifact would be overwritten.
    #[error("artifact already exists at `{0}`")]
    ArtifactExists(PathBuf),

    /// A required completed artifact is absent.
    #[error("required artifact is missing at `{0}`")]
    ArtifactMissing(PathBuf),

    /// An interrupted stage must be inspected or removed before retrying.
    #[error("incomplete stage already exists at `{0}`")]
    IncompleteStage(PathBuf),

    /// NostrDB cannot open a path that is not UTF-8.
    #[error("NostrDB path is not valid UTF-8: `{0}`")]
    NonUtf8Path(PathBuf),

    /// An input record cannot be represented by NostrDB's signed length.
    #[error("snapshot record {record} is too large for NostrDB: {bytes} bytes")]
    RecordTooLarge {
        /// One-based JSONL record number.
        record: u64,
        /// Record size in bytes.
        bytes: usize,
    },

    /// Stored state contradicted the pipeline's accounting.
    #[error("snapshot pipeline invariant failed: {0}")]
    Invariant(String),
}

/// Files and directories owned by one snapshot pipeline run.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SnapshotLayout {
    root: PathBuf,
}

impl SnapshotLayout {
    /// Define the data layout beneath `root`.
    pub fn new(root: impl Into<PathBuf>) -> Self {
        Self { root: root.into() }
    }

    /// Return the pipeline's data root.
    pub fn root(&self) -> &Path {
        &self.root
    }

    /// Return the compressed snapshot input path.
    pub fn snapshot(&self) -> PathBuf {
        self.root
            .join("input")
            .join("damus-relay-2025-04-24.json.zst")
    }

    /// Return the validated source NostrDB path.
    pub fn source_db(&self) -> PathBuf {
        self.root.join("source").join("ndb")
    }

    /// Return the source import manifest path.
    pub fn source_manifest(&self) -> PathBuf {
        self.root.join("source").join("manifest.json")
    }

    /// Return the eligible corpus NostrDB path.
    pub fn corpus_db(&self) -> PathBuf {
        self.root.join("corpus").join("ndb")
    }

    /// Return the corpus derivation manifest path.
    pub fn corpus_manifest(&self) -> PathBuf {
        self.root.join("corpus").join("manifest.json")
    }

    /// Return the canonical-row manifest path.
    pub fn canonical_manifest(&self) -> PathBuf {
        self.root.join("canonical").join("manifest.json")
    }

    /// Return canonical event IDs in deterministic row order.
    pub fn canonical_rows(&self) -> PathBuf {
        self.root.join("canonical").join("rows.bin")
    }

    /// Return the event-ID to canonical-event-ID index.
    pub fn canonical_aliases(&self) -> PathBuf {
        self.root.join("canonical").join("aliases.bin")
    }

    fn source_dir(&self) -> PathBuf {
        self.root.join("source")
    }

    fn corpus_dir(&self) -> PathBuf {
        self.root.join("corpus")
    }

    pub(crate) fn canonical_dir(&self) -> PathBuf {
        self.root.join("canonical")
    }

    fn work_dir(&self) -> PathBuf {
        self.root.join("work")
    }

    fn source_stage(&self) -> PathBuf {
        self.work_dir().join("source")
    }

    fn corpus_stage(&self) -> PathBuf {
        self.work_dir().join("corpus")
    }

    pub(crate) fn canonical_stage(&self) -> PathBuf {
        self.work_dir().join("canonical")
    }
}

/// Counts recorded after NostrDB validates the source snapshot.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct SourceCounts {
    /// Top-level JSONL records submitted from the compressed snapshot.
    pub snapshot_records: u64,
    /// Events stored after validation and NostrDB ingestion semantics.
    ///
    /// This is independent of `snapshot_records`: NostrDB rejects invalid and
    /// duplicate events but also validates and stores signed events embedded in
    /// kind `6` repost content.
    pub stored_events: u64,
}

/// Durable description of a completed source import.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct SourceManifest {
    /// Manifest schema version.
    pub schema_version: u32,
    /// SHA-256 of the compressed input.
    pub snapshot_sha256: String,
    /// Compressed input size in bytes.
    pub snapshot_bytes: u64,
    /// Source import counts.
    pub counts: SourceCounts,
}

/// Mutually exclusive eligibility rejection counts.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct EligibilityRejections {
    /// Valid source events whose kind is not `1`.
    pub non_kind_1: u64,
    /// Kind `1` replies, including events that are also quotes.
    pub replies: u64,
    /// Root kind `1` quote notes.
    pub quotes: u64,
}

/// Durable description of a completed eligible-corpus derivation.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct CorpusManifest {
    /// Manifest schema version.
    pub schema_version: u32,
    /// SHA-256 inherited from the source import.
    pub source_snapshot_sha256: String,
    /// Mutually exclusive rejection counts.
    pub rejections: EligibilityRejections,
    /// Root, non-quote kind `1` events retained in the corpus.
    pub eligible_events: u64,
}

/// Builds persistent NostrDB artifacts from the static Damus snapshot.
#[derive(Clone, Debug)]
pub struct DamusSnapshot {
    layout: SnapshotLayout,
}

impl DamusSnapshot {
    /// Create a pipeline whose artifacts are confined beneath `root`.
    pub fn new(root: impl Into<PathBuf>) -> Self {
        Self {
            layout: SnapshotLayout::new(root),
        }
    }

    /// Return the pipeline's explicit filesystem layout.
    pub fn layout(&self) -> &SnapshotLayout {
        &self.layout
    }

    /// Validate and import the compressed snapshot into the source NostrDB.
    ///
    /// The completed `source/` directory is published only after NostrDB has
    /// drained its ingestion queue, reopened successfully, and been counted.
    #[profiling::function]
    pub fn import_source(&self) -> Result<SourceManifest> {
        let input = self.layout.snapshot();
        require_file(&input)?;
        let file = open_file(&input)?;
        let snapshot_bytes = metadata_len(&input)?;
        let hashing = HashingReader::new(file);
        let compressed = BufReader::new(hashing);
        let decoder = zstd::stream::read::Decoder::with_buffer(compressed)
            .map_err(|source| io_error("open zstd decoder for", &input, source))?;
        let mut reader = BufReader::new(decoder);
        let stage = self.prepare_stage(&self.layout.source_dir(), &self.layout.source_stage())?;
        let staged_db = stage.join("ndb");
        let ndb = open_ndb(&staged_db, Validation::Verify)?;
        let mut snapshot_records = 0_u64;
        let mut line = String::new();

        loop {
            line.clear();
            let bytes = reader
                .read_line(&mut line)
                .map_err(|source| io_error("read", &input, source))?;
            if bytes == 0 {
                break;
            }
            snapshot_records = snapshot_records.checked_add(1).ok_or_else(|| {
                Error::Invariant("snapshot record count overflowed u64".to_owned())
            })?;
            if bytes > i32::MAX as usize {
                return Err(Error::RecordTooLarge {
                    record: snapshot_records,
                    bytes,
                });
            }
            ndb.process_event(&line)
                .map_err(|source| ndb_error("submit event to", &staged_db, source))?;
        }

        let decoder = reader.into_inner();
        let compressed = decoder.finish();
        let hashing = compressed.into_inner();
        let hashed_bytes = hashing.bytes_read();
        let snapshot_sha256 = hashing.finish();
        if hashed_bytes != snapshot_bytes {
            return Err(Error::Invariant(format!(
                "hashed {hashed_bytes} compressed bytes but input has {snapshot_bytes}"
            )));
        }

        drop(ndb);
        let stored_events = count_all(&staged_db, Validation::Verify)?;
        let manifest = SourceManifest {
            schema_version: 1,
            snapshot_sha256,
            snapshot_bytes,
            counts: SourceCounts {
                snapshot_records,
                stored_events,
            },
        };
        write_manifest(&stage.join("manifest.json"), &manifest)?;
        self.publish_stage(&stage, &self.layout.source_dir())?;
        Ok(manifest)
    }

    /// Derive the root, non-quote kind `1` corpus from the source NostrDB.
    ///
    /// Replies are rejected before quote notes so every source event contributes
    /// to exactly one eligibility count. A quote is either a NIP-18 `q` tag or
    /// the legacy NIP-10 `e` tag with a `mention` marker.
    #[profiling::function]
    pub fn derive_corpus(&self) -> Result<CorpusManifest> {
        let source_manifest_path = self.layout.source_manifest();
        let source_path = self.layout.source_db();
        require_file(&source_manifest_path)?;
        require_directory(&source_path)?;
        let source_manifest: SourceManifest = read_manifest(&source_manifest_path)?;
        let source_db = open_ndb(&source_path, Validation::Verify)?;
        let source_total = count_with_db(&source_db, &source_path, None)?;
        if source_total != source_manifest.counts.stored_events {
            return Err(Error::Invariant(format!(
                "source manifest records {} stored events but source NostrDB contains {source_total}",
                source_manifest.counts.stored_events
            )));
        }

        let stage = self.prepare_stage(&self.layout.corpus_dir(), &self.layout.corpus_stage())?;
        let staged_db = stage.join("ndb");
        let kind_one = Filter::new().kinds([1]).build();
        let corpus_db = open_ndb(&staged_db, Validation::TrustedSource)?;
        let txn = Transaction::new(&source_db)
            .map_err(|source| ndb_error("open transaction on", &source_path, source))?;

        let derived = source_db
            .try_fold(
                &txn,
                &[kind_one],
                Ok(DerivedCounts::default()),
                |state, note| derive_note(state, note, &source_path, &corpus_db, &staged_db),
            )
            .map_err(|source| ndb_error("scan", &source_path, source))??;
        let classified = derived
            .replies
            .checked_add(derived.quotes)
            .and_then(|count| count.checked_add(derived.eligible))
            .ok_or_else(|| Error::Invariant("eligibility count overflowed u64".to_owned()))?;
        let non_kind_1 = source_total.checked_sub(classified).ok_or_else(|| {
            Error::Invariant(format!(
                "classified {classified} kind 1 events from {source_total} source events"
            ))
        })?;

        drop(txn);
        drop(source_db);
        drop(corpus_db);
        let corpus_total = count_all(&staged_db, Validation::TrustedSource)?;
        if corpus_total != derived.eligible {
            return Err(Error::Invariant(format!(
                "submitted {} eligible events but corpus NostrDB contains {corpus_total}",
                derived.eligible
            )));
        }

        let manifest = CorpusManifest {
            schema_version: 1,
            source_snapshot_sha256: source_manifest.snapshot_sha256,
            rejections: EligibilityRejections {
                non_kind_1,
                replies: derived.replies,
                quotes: derived.quotes,
            },
            eligible_events: derived.eligible,
        };
        write_manifest(&stage.join("manifest.json"), &manifest)?;
        self.publish_stage(&stage, &self.layout.corpus_dir())?;
        Ok(manifest)
    }

    /// Canonicalize byte-identical corpus content and assign stable row order.
    #[profiling::function]
    pub fn canonicalize_corpus(&self) -> Result<CanonicalManifest> {
        crate::canonical::canonicalize_corpus(self)
    }

    pub(crate) fn prepare_stage(&self, artifact: &Path, stage: &Path) -> Result<PathBuf> {
        if artifact.exists() {
            return Err(Error::ArtifactExists(artifact.to_owned()));
        }
        if stage.exists() {
            return Err(Error::IncompleteStage(stage.to_owned()));
        }
        create_directory(&self.layout.work_dir())?;
        fs::create_dir(stage).map_err(|source| io_error("create", stage, source))?;
        Ok(stage.to_owned())
    }

    pub(crate) fn publish_stage(&self, stage: &Path, artifact: &Path) -> Result<()> {
        fs::rename(stage, artifact).map_err(|source| io_error("publish", artifact, source))?;
        let _ = fs::remove_dir(self.layout.work_dir());
        Ok(())
    }
}

#[derive(Clone, Copy, Debug, Default)]
struct DerivedCounts {
    replies: u64,
    quotes: u64,
    eligible: u64,
}

fn derive_note(
    state: Result<DerivedCounts>,
    note: Note<'_>,
    source_path: &Path,
    corpus_db: &Ndb,
    corpus_path: &Path,
) -> ControlFlow<Result<DerivedCounts>, Result<DerivedCounts>> {
    let Ok(mut state) = state else {
        return ControlFlow::Break(state);
    };

    let reply = NoteReply::new(note.tags());
    if reply.is_reply() {
        state.replies += 1;
        return ControlFlow::Continue(Ok(state));
    }
    if reply.mention().is_some() || has_quote_tag(&note) {
        state.quotes += 1;
        return ControlFlow::Continue(Ok(state));
    }

    let json = match note_json(&note, source_path) {
        Ok(json) => json,
        Err(error) => return ControlFlow::Break(Err(error)),
    };
    if let Err(source) = corpus_db.process_event(&json) {
        return ControlFlow::Break(Err(ndb_error(
            "submit eligible event to",
            corpus_path,
            source,
        )));
    }
    state.eligible += 1;
    ControlFlow::Continue(Ok(state))
}

fn has_quote_tag(note: &Note<'_>) -> bool {
    note.tags()
        .into_iter()
        .any(|tag| tag.get_str(0) == Some("q"))
}

fn note_json(note: &Note<'_>, source_path: &Path) -> Result<String> {
    let mut capacity = note.size().saturating_mul(2).max(1_024);
    loop {
        match note.json_with_bufsize(capacity) {
            Ok(json) => return Ok(json),
            Err(nostrdb::Error::BufferOverflow) => {
                capacity = capacity.checked_mul(2).ok_or_else(|| {
                    Error::Invariant("note JSON buffer size overflowed usize".to_owned())
                })?;
            }
            Err(source) => {
                return Err(ndb_error(
                    "serialize eligible event from",
                    source_path,
                    source,
                ));
            }
        }
    }
}

fn count_all(path: &Path, validation: Validation) -> Result<u64> {
    let ndb = open_ndb(path, validation)?;
    count_with_db(&ndb, path, None)
}

pub(crate) fn count_with_db(ndb: &Ndb, path: &Path, filter: Option<&Filter>) -> Result<u64> {
    let txn =
        Transaction::new(ndb).map_err(|source| ndb_error("open transaction on", path, source))?;
    let all;
    let filters = match filter {
        Some(filter) => std::slice::from_ref(filter),
        None => {
            all = Filter::new().build();
            std::slice::from_ref(&all)
        }
    };
    let count = ndb
        .count(&txn, filters)
        .map_err(|source| ndb_error("count", path, source))?;
    u64::try_from(count)
        .map_err(|_| Error::Invariant(format!("NostrDB count {count} does not fit u64")))
}

#[derive(Clone, Copy)]
pub(crate) enum Validation {
    Verify,
    TrustedSource,
}

pub(crate) fn open_ndb(path: &Path, validation: Validation) -> Result<Ndb> {
    let path_str = path
        .to_str()
        .ok_or_else(|| Error::NonUtf8Path(path.to_owned()))?;
    let map_size = 256_usize.saturating_mul(1_024 * 1_024 * 1_024);
    let no_fulltext = 1 << 2;
    let no_note_blocks = 1 << 3;
    let no_stats = 1 << 4;
    let skip_validation = matches!(validation, Validation::TrustedSource);
    let config = Config::new()
        .set_flags(no_fulltext | no_note_blocks | no_stats)
        .set_mapsize(map_size)
        .skip_validation(skip_validation);
    Ndb::new(path_str, &config).map_err(|source| ndb_error("open", path, source))
}

pub(crate) fn require_file(path: &Path) -> Result<()> {
    if path.is_file() {
        Ok(())
    } else {
        Err(Error::ArtifactMissing(path.to_owned()))
    }
}

pub(crate) fn require_directory(path: &Path) -> Result<()> {
    if path.is_dir() {
        Ok(())
    } else {
        Err(Error::ArtifactMissing(path.to_owned()))
    }
}

fn open_file(path: &Path) -> Result<File> {
    File::open(path).map_err(|source| io_error("open", path, source))
}

fn metadata_len(path: &Path) -> Result<u64> {
    fs::metadata(path)
        .map(|metadata| metadata.len())
        .map_err(|source| io_error("read metadata for", path, source))
}

pub(crate) fn create_directory(path: &Path) -> Result<()> {
    fs::create_dir_all(path).map_err(|source| io_error("create", path, source))
}

pub(crate) fn read_manifest<T>(path: &Path) -> Result<T>
where
    T: serde::de::DeserializeOwned,
{
    let reader = BufReader::new(open_file(path)?);
    serde_json::from_reader(reader).map_err(|source| Error::Manifest {
        operation: "decode",
        path: path.to_owned(),
        source,
    })
}

pub(crate) fn write_manifest<T>(path: &Path, manifest: &T) -> Result<()>
where
    T: Serialize,
{
    let file = OpenOptions::new()
        .create_new(true)
        .write(true)
        .open(path)
        .map_err(|source| io_error("create", path, source))?;
    let mut writer = BufWriter::new(file);
    serde_json::to_writer_pretty(&mut writer, manifest).map_err(|source| Error::Manifest {
        operation: "encode",
        path: path.to_owned(),
        source,
    })?;
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

pub(crate) fn io_error(
    operation: &'static str,
    path: impl AsRef<Path>,
    source: io::Error,
) -> Error {
    Error::Io {
        operation,
        path: path.as_ref().to_owned(),
        source,
    }
}

pub(crate) fn ndb_error(
    operation: &'static str,
    path: impl AsRef<Path>,
    source: nostrdb::Error,
) -> Error {
    Error::Ndb {
        operation,
        path: path.as_ref().to_owned(),
        source,
    }
}

struct HashingReader<R> {
    inner: R,
    hasher: Sha256,
    bytes_read: u64,
}

impl<R> HashingReader<R> {
    fn new(inner: R) -> Self {
        Self {
            inner,
            hasher: Sha256::new(),
            bytes_read: 0,
        }
    }

    fn bytes_read(&self) -> u64 {
        self.bytes_read
    }

    fn finish(self) -> String {
        format!("{:x}", self.hasher.finalize())
    }
}

impl<R> Read for HashingReader<R>
where
    R: Read,
{
    fn read(&mut self, buffer: &mut [u8]) -> io::Result<usize> {
        let bytes = self.inner.read(buffer)?;
        self.hasher.update(&buffer[..bytes]);
        self.bytes_read = self
            .bytes_read
            .checked_add(bytes as u64)
            .ok_or_else(|| io::Error::other("compressed byte count overflowed u64"))?;
        Ok(bytes)
    }
}
