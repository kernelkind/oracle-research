//! Resumable exact-token audit over the final ordered English corpus.

use std::collections::BTreeMap;
use std::fs::{self, File, OpenOptions};
use std::io::{BufReader, BufWriter, Read, Seek, SeekFrom, Write};
use std::path::{Path, PathBuf};

use nostrdb::Transaction;
use serde::{Deserialize, Serialize};

use crate::artifact::{ArtifactFile, describe_fixed_artifact, hash_bytes, hash_file};
use crate::gte::{GteProcessEncoder, TokenRole};
use crate::representation::RepresentationDescriptor;
use crate::snapshot::{
    Error, Result, Validation, io_error, ndb_error, open_existing_ndb, read_manifest, require_file,
};

const SCHEMA_VERSION: u32 = 1;
const SHARD_SCHEMA_VERSION: u32 = 1;
const EVENT_ID_BYTES: usize = 32;
const LENGTH_BYTES: usize = size_of::<u32>();
const MANIFEST_FILE: &str = "manifest.json";
const MANIFEST_TEMP_FILE: &str = ".manifest.json.tmp";
const DOCUMENT_FILE: &str = "document-lengths.u32le";
const QUERY_FILE: &str = "query-lengths.u32le";

pub trait OrderedGteTokenCounter {
    fn descriptor(&self) -> &RepresentationDescriptor;
    fn token_lengths(&mut self, role: TokenRole, texts: &[&str]) -> Result<Vec<u32>>;
}

impl OrderedGteTokenCounter for GteProcessEncoder {
    fn descriptor(&self) -> &RepresentationDescriptor {
        crate::representation::RepresentationEncoder::descriptor(self)
    }

    fn token_lengths(&mut self, role: TokenRole, texts: &[&str]) -> Result<Vec<u32>> {
        GteProcessEncoder::token_lengths(self, role, texts)
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct OrderedGteTokenAuditConfig {
    pub batch_size: usize,
    pub shard_rows: u64,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct TokenLengthCount {
    pub tokens: u32,
    pub rows: u64,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct OrderedGteTokenAuditShard {
    pub schema_version: u32,
    pub ordinal: u32,
    pub start_row: u64,
    pub rows: u64,
    pub corpus_data_sha256: String,
    pub ordered_event_ids_sha256: String,
    pub descriptor_sha256: String,
    pub document_lengths: ArtifactFile,
    pub query_lengths: ArtifactFile,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct OrderedGteTokenAuditManifest {
    pub schema_version: u32,
    pub corpus_data_sha256: String,
    pub ordered_event_ids_sha256: String,
    pub total_rows: u64,
    pub descriptor: RepresentationDescriptor,
    pub descriptor_sha256: String,
    pub batch_size: u32,
    pub shard_rows: u64,
    pub document_total_tokens: u64,
    pub document_minimum_tokens: u32,
    pub document_maximum_tokens: u32,
    pub document_distribution: Vec<TokenLengthCount>,
    pub query_total_tokens: u64,
    pub query_minimum_tokens: u32,
    pub query_maximum_tokens: u32,
    pub query_distribution: Vec<TokenLengthCount>,
    pub shards: Vec<OrderedGteTokenAuditShard>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct OrderedGteTokenAuditResult {
    pub manifest: OrderedGteTokenAuditManifest,
    pub audited_rows: u64,
    pub reused_rows: u64,
}

/// A checksum-verified token audit with random access to its ordered lengths.
#[derive(Debug)]
pub struct OrderedGteTokenAudit {
    root: PathBuf,
    manifest: OrderedGteTokenAuditManifest,
    manifest_sha256: String,
}

impl OrderedGteTokenAudit {
    pub fn manifest(&self) -> &OrderedGteTokenAuditManifest {
        &self.manifest
    }

    pub fn manifest_sha256(&self) -> &str {
        &self.manifest_sha256
    }

    /// Read document-role lengths for one contiguous range in ordered-row space.
    pub fn document_lengths(&self, start_row: u64, rows: u64) -> Result<Vec<u32>> {
        self.read_document_lengths(start_row, rows)
    }

    fn read_document_lengths(&self, start_row: u64, rows: u64) -> Result<Vec<u32>> {
        if rows == 0 {
            return Err(Error::Invariant(
                "token-length range must contain at least one row".to_owned(),
            ));
        }
        let end_row = start_row
            .checked_add(rows)
            .ok_or_else(|| Error::Invariant("token-length range overflowed".to_owned()))?;
        if end_row > self.manifest.total_rows {
            return Err(Error::Invariant(format!(
                "token-length range {start_row}..{end_row} exceeds {} audited rows",
                self.manifest.total_rows
            )));
        }

        let capacity = usize::try_from(rows).map_err(|_| {
            Error::Invariant("token-length row count does not fit usize".to_owned())
        })?;
        let mut output = Vec::with_capacity(capacity);
        for shard in &self.manifest.shards {
            let shard_end = shard.start_row + shard.rows;
            let read_start = start_row.max(shard.start_row);
            let read_end = end_row.min(shard_end);
            if read_start >= read_end {
                continue;
            }
            let item = &shard.document_lengths;
            let path = self.root.join(&item.file);
            let local_start = read_start - shard.start_row;
            let read_rows = read_end - read_start;
            let bytes = usize::try_from(read_rows)
                .ok()
                .and_then(|rows| rows.checked_mul(LENGTH_BYTES))
                .ok_or_else(|| {
                    Error::Invariant("token-length read size overflowed usize".to_owned())
                })?;
            let mut file = File::open(&path).map_err(|source| io_error("open", &path, source))?;
            file.seek(SeekFrom::Start(local_start * LENGTH_BYTES as u64))
                .map_err(|source| io_error("seek", &path, source))?;
            let mut encoded = vec![0_u8; bytes];
            file.read_exact(&mut encoded)
                .map_err(|source| io_error("read", &path, source))?;
            output.extend(
                encoded
                    .chunks_exact(LENGTH_BYTES)
                    .map(|bytes| u32::from_le_bytes(bytes.try_into().expect("u32 width"))),
            );
        }
        if output.len() != capacity {
            return Err(Error::Invariant(format!(
                "token audit returned {} lengths for {rows} requested rows",
                output.len()
            )));
        }
        Ok(output)
    }
}

pub fn audit_ordered_gte_tokens(
    corpus_path: impl AsRef<Path>,
    ordered_event_ids_path: impl AsRef<Path>,
    output_path: impl AsRef<Path>,
    config: &OrderedGteTokenAuditConfig,
    counter: &mut dyn OrderedGteTokenCounter,
) -> Result<OrderedGteTokenAuditResult> {
    if config.batch_size == 0 || config.shard_rows == 0 {
        return Err(Error::Invariant(
            "token-audit batch and shard sizes must be positive".to_owned(),
        ));
    }
    let corpus_path = corpus_path.as_ref();
    let ordered_path = ordered_event_ids_path.as_ref();
    let root = output_path.as_ref();
    require_file(ordered_path)?;
    let bytes = fs::metadata(ordered_path)
        .map_err(|source| io_error("read metadata for", ordered_path, source))?
        .len();
    if bytes == 0 || !bytes.is_multiple_of(EVENT_ID_BYTES as u64) {
        return Err(Error::Invariant(
            "ordered event IDs are empty or contain a partial record".to_owned(),
        ));
    }
    let total_rows = bytes / EVENT_ID_BYTES as u64;
    let corpus_data = corpus_path.join("data.mdb");
    require_file(&corpus_data)?;
    let corpus_sha256 = hash_file(&corpus_data)?;
    let ordered_sha256 = hash_file(ordered_path)?;
    let descriptor = counter.descriptor().clone();
    if descriptor.model_token_ceiling == 0 {
        return Err(Error::Invariant(
            "token-audit descriptor has no model token ceiling".to_owned(),
        ));
    }
    let descriptor_sha256 = descriptor_hash(&descriptor)?;
    if root.join(MANIFEST_FILE).exists() {
        let manifest = open_ordered_gte_token_audit(ordered_path, root)?;
        validate_identity(
            &manifest,
            &corpus_sha256,
            &ordered_sha256,
            total_rows,
            &descriptor,
            &descriptor_sha256,
            config,
        )?;
        return Ok(OrderedGteTokenAuditResult {
            reused_rows: total_rows,
            audited_rows: 0,
            manifest,
        });
    }
    fs::create_dir_all(root.join("shards"))
        .map_err(|source| io_error("create", root.join("shards"), source))?;
    let mut shards = discover_shards(
        root,
        total_rows,
        config.shard_rows,
        &corpus_sha256,
        &ordered_sha256,
        &descriptor_sha256,
    )?;
    let corpus = open_existing_ndb(corpus_path, Validation::TrustedSource)?;
    let transaction = Transaction::new(&corpus)
        .map_err(|source| ndb_error("open transaction on", corpus_path, source))?;
    let mut ordered =
        File::open(ordered_path).map_err(|source| io_error("open", ordered_path, source))?;
    let shard_count = total_rows.div_ceil(config.shard_rows);
    let mut audited_rows = 0_u64;
    let mut reused_rows = 0_u64;
    for ordinal in 0..shard_count {
        let ordinal = u32::try_from(ordinal).map_err(|_| {
            Error::Invariant("token-audit shard ordinal does not fit u32".to_owned())
        })?;
        if let Some(shard) = shards.get(&ordinal) {
            reused_rows += shard.rows;
            continue;
        }
        let start_row = u64::from(ordinal) * config.shard_rows;
        let rows = config.shard_rows.min(total_rows - start_row);
        let shard = audit_shard(
            root,
            corpus_path,
            &corpus,
            &transaction,
            ordered_path,
            &mut ordered,
            ordinal,
            start_row,
            rows,
            config,
            &corpus_sha256,
            &ordered_sha256,
            &descriptor_sha256,
            descriptor.model_token_ceiling,
            counter,
        )?;
        audited_rows += rows;
        shards.insert(ordinal, shard);
    }
    drop(transaction);
    drop(corpus);
    if hash_file(&corpus_data)? != corpus_sha256 || hash_file(ordered_path)? != ordered_sha256 {
        return Err(Error::Invariant(
            "token-audit input changed while it was being audited".to_owned(),
        ));
    }
    let shards = shards.into_values().collect::<Vec<_>>();
    let aggregates = aggregate(root, &shards)?;
    let manifest = OrderedGteTokenAuditManifest {
        schema_version: SCHEMA_VERSION,
        corpus_data_sha256: corpus_sha256,
        ordered_event_ids_sha256: ordered_sha256,
        total_rows,
        descriptor,
        descriptor_sha256,
        batch_size: u32::try_from(config.batch_size)
            .map_err(|_| Error::Invariant("token-audit batch size does not fit u32".to_owned()))?,
        shard_rows: config.shard_rows,
        document_total_tokens: aggregates.document_total,
        document_minimum_tokens: aggregates.document_minimum,
        document_maximum_tokens: aggregates.document_maximum,
        document_distribution: counts(aggregates.document_counts),
        query_total_tokens: aggregates.query_total,
        query_minimum_tokens: aggregates.query_minimum,
        query_maximum_tokens: aggregates.query_maximum,
        query_distribution: counts(aggregates.query_counts),
        shards,
    };
    publish_manifest(root, &manifest)?;
    let verified = open_ordered_gte_token_audit(ordered_path, root)?;
    Ok(OrderedGteTokenAuditResult {
        manifest: verified,
        audited_rows,
        reused_rows,
    })
}

pub fn open_ordered_gte_token_audit(
    ordered_event_ids_path: impl AsRef<Path>,
    output_path: impl AsRef<Path>,
) -> Result<OrderedGteTokenAuditManifest> {
    open_ordered_gte_token_audit_store(ordered_event_ids_path, output_path)
        .map(|audit| audit.manifest)
}

pub fn open_ordered_gte_token_audit_store(
    ordered_event_ids_path: impl AsRef<Path>,
    output_path: impl AsRef<Path>,
) -> Result<OrderedGteTokenAudit> {
    let ordered_path = ordered_event_ids_path.as_ref();
    let root = output_path.as_ref();
    let manifest_path = root.join(MANIFEST_FILE);
    require_file(&manifest_path)?;
    let manifest: OrderedGteTokenAuditManifest = read_manifest(&manifest_path)?;
    if manifest.schema_version != SCHEMA_VERSION
        || manifest.total_rows == 0
        || manifest.batch_size == 0
        || manifest.shard_rows == 0
        || descriptor_hash(&manifest.descriptor)? != manifest.descriptor_sha256
    {
        return Err(Error::Invariant(
            "ordered GTE token-audit manifest is incompatible".to_owned(),
        ));
    }
    require_file(ordered_path)?;
    let bytes = fs::metadata(ordered_path)
        .map_err(|source| io_error("read metadata for", ordered_path, source))?
        .len();
    if bytes != manifest.total_rows * EVENT_ID_BYTES as u64
        || hash_file(ordered_path)? != manifest.ordered_event_ids_sha256
    {
        return Err(Error::Invariant(
            "token audit does not match the ordered event IDs".to_owned(),
        ));
    }
    let discovered = discover_shards(
        root,
        manifest.total_rows,
        manifest.shard_rows,
        &manifest.corpus_data_sha256,
        &manifest.ordered_event_ids_sha256,
        &manifest.descriptor_sha256,
    )?
    .into_values()
    .collect::<Vec<_>>();
    if discovered != manifest.shards {
        return Err(Error::Invariant(
            "token-audit shard set does not match its manifest".to_owned(),
        ));
    }
    let aggregates = aggregate(root, &manifest.shards)?;
    if manifest.document_total_tokens != aggregates.document_total
        || manifest.document_minimum_tokens != aggregates.document_minimum
        || manifest.document_maximum_tokens != aggregates.document_maximum
        || manifest.document_distribution != counts(aggregates.document_counts)
        || manifest.query_total_tokens != aggregates.query_total
        || manifest.query_minimum_tokens != aggregates.query_minimum
        || manifest.query_maximum_tokens != aggregates.query_maximum
        || manifest.query_distribution != counts(aggregates.query_counts)
    {
        return Err(Error::Invariant(
            "token-audit aggregates do not match its row lengths".to_owned(),
        ));
    }
    let manifest_sha256 = hash_file(&manifest_path)?;
    Ok(OrderedGteTokenAudit {
        root: root.to_owned(),
        manifest,
        manifest_sha256,
    })
}

#[allow(clippy::too_many_arguments)]
fn audit_shard(
    root: &Path,
    corpus_path: &Path,
    corpus: &nostrdb::Ndb,
    transaction: &Transaction,
    ordered_path: &Path,
    ordered: &mut File,
    ordinal: u32,
    start_row: u64,
    rows: u64,
    config: &OrderedGteTokenAuditConfig,
    corpus_sha256: &str,
    ordered_sha256: &str,
    descriptor_sha256: &str,
    ceiling: u32,
    counter: &mut dyn OrderedGteTokenCounter,
) -> Result<OrderedGteTokenAuditShard> {
    let name = format!("{ordinal:06}");
    let target = root.join("shards").join(&name);
    let temporary = root.join("shards").join(format!(".{name}.tmp"));
    if temporary.exists() {
        fs::remove_dir_all(&temporary).map_err(|source| io_error("remove", &temporary, source))?;
    }
    fs::create_dir(&temporary).map_err(|source| io_error("create", &temporary, source))?;
    let result = (|| {
        let document_path = temporary.join(DOCUMENT_FILE);
        let query_path = temporary.join(QUERY_FILE);
        let mut documents = BufWriter::new(
            OpenOptions::new()
                .create_new(true)
                .write(true)
                .open(&document_path)
                .map_err(|source| io_error("create", &document_path, source))?,
        );
        let mut queries = BufWriter::new(
            OpenOptions::new()
                .create_new(true)
                .write(true)
                .open(&query_path)
                .map_err(|source| io_error("create", &query_path, source))?,
        );
        ordered
            .seek(SeekFrom::Start(start_row * EVENT_ID_BYTES as u64))
            .map_err(|source| io_error("seek", ordered_path, source))?;
        let mut remaining = rows;
        while remaining > 0 {
            let batch_rows = remaining.min(config.batch_size as u64);
            let mut texts = Vec::with_capacity(batch_rows as usize);
            for _ in 0..batch_rows {
                let mut id = [0_u8; EVENT_ID_BYTES];
                ordered
                    .read_exact(&mut id)
                    .map_err(|source| io_error("read", ordered_path, source))?;
                let note = corpus
                    .get_note_by_id(transaction, &id)
                    .map_err(|source| ndb_error("load ordered note from", corpus_path, source))?;
                texts.push(note.content().to_owned());
            }
            let borrowed = texts.iter().map(String::as_str).collect::<Vec<_>>();
            let document_lengths = counter.token_lengths(TokenRole::Document, &borrowed)?;
            let query_lengths = counter.token_lengths(TokenRole::Query, &borrowed)?;
            if document_lengths.len() != borrowed.len() || query_lengths.len() != borrowed.len() {
                return Err(Error::Encoder {
                    operation: "audit token lengths",
                    message: "token counter returned the wrong row count".to_owned(),
                });
            }
            for (role, lengths, writer) in [
                ("document", document_lengths, &mut documents),
                ("query", query_lengths, &mut queries),
            ] {
                for length in lengths {
                    if length == 0 || length > ceiling {
                        return Err(Error::Encoder {
                            operation: "audit token lengths",
                            message: format!(
                                "{role} input has {length} tokens and would require truncation at {ceiling}"
                            ),
                        });
                    }
                    writer
                        .write_all(&length.to_le_bytes())
                        .map_err(|source| io_error("write", &temporary, source))?;
                }
            }
            remaining -= batch_rows;
        }
        for (path, writer) in [
            (&document_path, &mut documents),
            (&query_path, &mut queries),
        ] {
            writer
                .flush()
                .map_err(|source| io_error("flush", path, source))?;
            writer
                .get_ref()
                .sync_all()
                .map_err(|source| io_error("sync", path, source))?;
        }
        let shard = OrderedGteTokenAuditShard {
            schema_version: SHARD_SCHEMA_VERSION,
            ordinal,
            start_row,
            rows,
            corpus_data_sha256: corpus_sha256.to_owned(),
            ordered_event_ids_sha256: ordered_sha256.to_owned(),
            descriptor_sha256: descriptor_sha256.to_owned(),
            document_lengths: describe_fixed_artifact(
                &document_path,
                &format!("shards/{name}/{DOCUMENT_FILE}"),
                LENGTH_BYTES,
                rows,
            )?,
            query_lengths: describe_fixed_artifact(
                &query_path,
                &format!("shards/{name}/{QUERY_FILE}"),
                LENGTH_BYTES,
                rows,
            )?,
        };
        write_json_new(&temporary.join(MANIFEST_FILE), &shard)?;
        sync_directory(&temporary)?;
        Ok(shard)
    })();
    let shard = match result {
        Ok(shard) => shard,
        Err(error) => {
            let _ = fs::remove_dir_all(&temporary);
            return Err(error);
        }
    };
    fs::rename(&temporary, &target).map_err(|source| io_error("publish", &target, source))?;
    sync_directory(&root.join("shards"))?;
    Ok(shard)
}

fn discover_shards(
    root: &Path,
    total_rows: u64,
    shard_rows: u64,
    corpus_sha256: &str,
    ordered_sha256: &str,
    descriptor_sha256: &str,
) -> Result<BTreeMap<u32, OrderedGteTokenAuditShard>> {
    let directory = root.join("shards");
    let mut shards = BTreeMap::new();
    for entry in fs::read_dir(&directory).map_err(|source| io_error("read", &directory, source))? {
        let entry = entry.map_err(|source| io_error("read", &directory, source))?;
        let name = entry.file_name().to_string_lossy().into_owned();
        if name.starts_with('.') {
            fs::remove_dir_all(entry.path())
                .map_err(|source| io_error("remove", entry.path(), source))?;
            continue;
        }
        let ordinal = name.parse::<u32>().map_err(|_| {
            Error::Invariant(format!("unexpected token-audit shard entry `{name}`"))
        })?;
        let shard: OrderedGteTokenAuditShard = read_manifest(&entry.path().join(MANIFEST_FILE))?;
        let start_row = u64::from(ordinal) * shard_rows;
        let rows = shard_rows.min(total_rows.saturating_sub(start_row));
        if shard.schema_version != SHARD_SCHEMA_VERSION
            || shard.ordinal != ordinal
            || shard.start_row != start_row
            || shard.rows == 0
            || shard.rows != rows
            || shard.corpus_data_sha256 != corpus_sha256
            || shard.ordered_event_ids_sha256 != ordered_sha256
            || shard.descriptor_sha256 != descriptor_sha256
        {
            return Err(Error::Invariant(format!(
                "token-audit shard {ordinal} belongs to a different corpus, ordered input, or audit contract"
            )));
        }
        for (artifact, file) in [
            (&shard.document_lengths, DOCUMENT_FILE),
            (&shard.query_lengths, QUERY_FILE),
        ] {
            let expected = format!("shards/{name}/{file}");
            let actual =
                describe_fixed_artifact(&root.join(&expected), &expected, LENGTH_BYTES, rows)?;
            if &actual != artifact {
                return Err(Error::Invariant(format!(
                    "token-audit shard {ordinal} checksum does not match"
                )));
            }
        }
        shards.insert(ordinal, shard);
    }
    Ok(shards)
}

struct Aggregates {
    document_total: u64,
    document_minimum: u32,
    document_maximum: u32,
    document_counts: BTreeMap<u32, u64>,
    query_total: u64,
    query_minimum: u32,
    query_maximum: u32,
    query_counts: BTreeMap<u32, u64>,
}

fn aggregate(root: &Path, shards: &[OrderedGteTokenAuditShard]) -> Result<Aggregates> {
    let mut documents = Vec::new();
    let mut queries = Vec::new();
    for shard in shards {
        read_lengths(root, &shard.document_lengths, &mut documents)?;
        read_lengths(root, &shard.query_lengths, &mut queries)?;
    }
    let (document_total, document_minimum, document_maximum, document_counts) =
        summarize(&documents)?;
    let (query_total, query_minimum, query_maximum, query_counts) = summarize(&queries)?;
    Ok(Aggregates {
        document_total,
        document_minimum,
        document_maximum,
        document_counts,
        query_total,
        query_minimum,
        query_maximum,
        query_counts,
    })
}

fn read_lengths(root: &Path, artifact: &ArtifactFile, output: &mut Vec<u32>) -> Result<()> {
    let path = root.join(&artifact.file);
    let mut reader =
        BufReader::new(File::open(&path).map_err(|source| io_error("open", &path, source))?);
    for _ in 0..artifact.records {
        let mut bytes = [0_u8; LENGTH_BYTES];
        reader
            .read_exact(&mut bytes)
            .map_err(|source| io_error("read", &path, source))?;
        output.push(u32::from_le_bytes(bytes));
    }
    Ok(())
}

fn summarize(values: &[u32]) -> Result<(u64, u32, u32, BTreeMap<u32, u64>)> {
    let minimum = values
        .iter()
        .copied()
        .min()
        .ok_or_else(|| Error::Invariant("cannot summarize empty token lengths".to_owned()))?;
    let maximum = values.iter().copied().max().expect("nonempty lengths");
    let mut total = 0_u64;
    let mut counts = BTreeMap::new();
    for &value in values {
        total = total
            .checked_add(u64::from(value))
            .ok_or_else(|| Error::Invariant("token total overflowed".to_owned()))?;
        *counts.entry(value).or_insert(0) += 1;
    }
    Ok((total, minimum, maximum, counts))
}

fn counts(values: BTreeMap<u32, u64>) -> Vec<TokenLengthCount> {
    values
        .into_iter()
        .map(|(tokens, rows)| TokenLengthCount { tokens, rows })
        .collect()
}

fn validate_identity(
    manifest: &OrderedGteTokenAuditManifest,
    corpus_sha256: &str,
    ordered_sha256: &str,
    total_rows: u64,
    descriptor: &RepresentationDescriptor,
    descriptor_sha256: &str,
    config: &OrderedGteTokenAuditConfig,
) -> Result<()> {
    if manifest.corpus_data_sha256 != corpus_sha256
        || manifest.ordered_event_ids_sha256 != ordered_sha256
        || manifest.total_rows != total_rows
        || &manifest.descriptor != descriptor
        || manifest.descriptor_sha256 != descriptor_sha256
        || manifest.batch_size != config.batch_size as u32
        || manifest.shard_rows != config.shard_rows
    {
        return Err(Error::Invariant(
            "existing token audit belongs to different inputs or settings".to_owned(),
        ));
    }
    Ok(())
}

fn descriptor_hash(descriptor: &RepresentationDescriptor) -> Result<String> {
    let bytes = serde_json::to_vec(descriptor).map_err(|source| Error::Manifest {
        operation: "encode",
        path: PathBuf::from("<token-audit-descriptor>"),
        source,
    })?;
    Ok(hash_bytes(&bytes))
}

fn publish_manifest(root: &Path, manifest: &OrderedGteTokenAuditManifest) -> Result<()> {
    let temporary = root.join(MANIFEST_TEMP_FILE);
    if temporary.exists() {
        fs::remove_file(&temporary).map_err(|source| io_error("remove", &temporary, source))?;
    }
    write_json_new(&temporary, manifest)?;
    let target = root.join(MANIFEST_FILE);
    fs::rename(&temporary, &target).map_err(|source| io_error("publish", &target, source))?;
    sync_directory(root)
}

fn write_json_new<T: Serialize>(path: &Path, value: &T) -> Result<()> {
    let file = OpenOptions::new()
        .create_new(true)
        .write(true)
        .open(path)
        .map_err(|source| io_error("create", path, source))?;
    let mut writer = BufWriter::new(file);
    serde_json::to_writer_pretty(&mut writer, value).map_err(|source| Error::Manifest {
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

fn sync_directory(path: &Path) -> Result<()> {
    File::open(path)
        .and_then(|file| file.sync_all())
        .map_err(|source| io_error("sync", path, source))
}
