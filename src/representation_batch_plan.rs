//! Immutable production batching derived from exact ordered GTE token lengths.

use std::collections::BTreeMap;
use std::fs::{self, File, OpenOptions};
use std::io::{BufWriter, Write};
use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};

use crate::artifact::{hash_bytes, hash_file};
use crate::ordered_gte_token_audit::{OrderedGteTokenAudit, open_ordered_gte_token_audit_store};
use crate::representation::RepresentationDescriptor;
use crate::snapshot::{Error, Result, io_error, read_manifest, require_file};

const SCHEMA_VERSION: u32 = 1;
const MANIFEST_FILE: &str = "manifest.json";
const EVENT_ID_BYTES: u64 = 32;

pub const BATCHING_RULE: &str = "document-token-length-ascending-within-output-shard-v1";

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RepresentationBatchPlanConfig {
    pub shard_rows: u64,
    pub batch_rows: usize,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct RepresentationBatchShapeCount {
    pub rows_per_batch: u32,
    pub padded_tokens_per_row: u32,
    pub batches: u64,
    pub effective_tokens: u64,
    pub padded_tokens: u64,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct RepresentationBatchPlanManifest {
    pub schema_version: u32,
    pub corpus_data_sha256: String,
    pub ordered_event_ids_sha256: String,
    pub token_audit_manifest_sha256: String,
    pub tokenization_contract_sha256: String,
    pub total_rows: u64,
    pub shard_rows: u64,
    pub batch_rows: u32,
    pub batching_rule: String,
    pub total_batches: u64,
    pub total_effective_tokens: u64,
    pub total_padded_tokens: u64,
    pub batch_shapes: Vec<RepresentationBatchShapeCount>,
}

/// Compact identity embedded in every representation and shard manifest.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct RepresentationBatchPlanIdentity {
    pub manifest_sha256: String,
    pub corpus_data_sha256: String,
    pub ordered_event_ids_sha256: String,
    pub token_audit_manifest_sha256: String,
    pub tokenization_contract_sha256: String,
    pub total_rows: u64,
    pub shard_rows: u64,
    pub batch_rows: u32,
    pub batching_rule: String,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct PlannedRepresentationRow {
    pub row_offset: u64,
    pub tokens: u32,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct PlannedRepresentationBatch {
    pub rows: Vec<PlannedRepresentationRow>,
    pub padded_tokens_per_row: u32,
    pub effective_tokens: u64,
}

#[derive(Debug)]
pub struct RepresentationBatchPlan {
    manifest: RepresentationBatchPlanManifest,
    identity: RepresentationBatchPlanIdentity,
    audit: OrderedGteTokenAudit,
}

impl RepresentationBatchPlan {
    pub fn manifest(&self) -> &RepresentationBatchPlanManifest {
        &self.manifest
    }

    pub fn identity(&self) -> &RepresentationBatchPlanIdentity {
        &self.identity
    }

    pub fn shard_batches(&self, ordinal: u32) -> Result<Vec<PlannedRepresentationBatch>> {
        let start_row = u64::from(ordinal)
            .checked_mul(self.manifest.shard_rows)
            .ok_or_else(|| Error::Invariant("batch-plan shard start overflowed".to_owned()))?;
        if start_row >= self.manifest.total_rows {
            return Err(Error::Invariant(format!(
                "batch-plan shard ordinal {ordinal} starts beyond the corpus"
            )));
        }
        let rows = self
            .manifest
            .shard_rows
            .min(self.manifest.total_rows - start_row);
        let lengths = self.audit.document_lengths(start_row, rows)?;
        plan_batches(&lengths, self.manifest.batch_rows as usize)
    }
}

pub fn create_representation_batch_plan(
    ordered_event_ids_path: impl AsRef<Path>,
    token_audit_path: impl AsRef<Path>,
    output_path: impl AsRef<Path>,
    config: &RepresentationBatchPlanConfig,
) -> Result<RepresentationBatchPlan> {
    validate_config(config)?;
    let ordered_path = ordered_event_ids_path.as_ref();
    let audit_path = token_audit_path.as_ref();
    let root = output_path.as_ref();
    let manifest_path = root.join(MANIFEST_FILE);
    if manifest_path.exists() {
        let plan = open_representation_batch_plan(ordered_path, audit_path, root)?;
        if plan.manifest.shard_rows != config.shard_rows
            || plan.manifest.batch_rows != config.batch_rows as u32
        {
            return Err(Error::Invariant(
                "existing batch plan belongs to different settings".to_owned(),
            ));
        }
        return Ok(plan);
    }
    if root.exists() {
        let mut entries = fs::read_dir(root).map_err(|source| io_error("read", root, source))?;
        if entries
            .next()
            .transpose()
            .map_err(|source| io_error("read", root, source))?
            .is_some()
        {
            return Err(Error::Invariant(
                "batch-plan directory contains an unpublished artifact".to_owned(),
            ));
        }
    } else {
        fs::create_dir_all(root).map_err(|source| io_error("create", root, source))?;
    }

    let audit = open_ordered_gte_token_audit_store(ordered_path, audit_path)?;
    let ordered_sha256 = hash_file(ordered_path)?;
    if ordered_sha256 != audit.manifest().ordered_event_ids_sha256 {
        return Err(Error::Invariant(
            "batch plan and token audit use different ordered event IDs".to_owned(),
        ));
    }
    let (batch_shapes, total_batches, total_effective_tokens, total_padded_tokens) =
        summarize_plan(&audit, config.shard_rows, config.batch_rows)?;
    let manifest = RepresentationBatchPlanManifest {
        schema_version: SCHEMA_VERSION,
        corpus_data_sha256: audit.manifest().corpus_data_sha256.clone(),
        ordered_event_ids_sha256: ordered_sha256,
        token_audit_manifest_sha256: audit.manifest_sha256().to_owned(),
        tokenization_contract_sha256: tokenization_contract_sha256(&audit.manifest().descriptor)?,
        total_rows: audit.manifest().total_rows,
        shard_rows: config.shard_rows,
        batch_rows: u32::try_from(config.batch_rows)
            .map_err(|_| Error::Invariant("batch rows do not fit u32".to_owned()))?,
        batching_rule: BATCHING_RULE.to_owned(),
        total_batches,
        total_effective_tokens,
        total_padded_tokens,
        batch_shapes,
    };
    let temporary = root.join(format!(".{MANIFEST_FILE}.tmp"));
    if temporary.exists() {
        fs::remove_file(&temporary).map_err(|source| io_error("remove", &temporary, source))?;
    }
    write_json_new(&temporary, &manifest)?;
    fs::rename(&temporary, &manifest_path)
        .map_err(|source| io_error("publish", &manifest_path, source))?;
    sync_directory(root)?;
    open_representation_batch_plan(ordered_path, audit_path, root)
}

pub fn open_representation_batch_plan(
    ordered_event_ids_path: impl AsRef<Path>,
    token_audit_path: impl AsRef<Path>,
    output_path: impl AsRef<Path>,
) -> Result<RepresentationBatchPlan> {
    let ordered_path = ordered_event_ids_path.as_ref();
    let root = output_path.as_ref();
    let manifest_path = root.join(MANIFEST_FILE);
    require_file(&manifest_path)?;
    let manifest: RepresentationBatchPlanManifest = read_manifest(&manifest_path)?;
    validate_manifest(&manifest)?;
    require_file(ordered_path)?;
    if hash_file(ordered_path)? != manifest.ordered_event_ids_sha256
        || fs::metadata(ordered_path)
            .map_err(|source| io_error("read metadata for", ordered_path, source))?
            .len()
            != manifest.total_rows * EVENT_ID_BYTES
    {
        return Err(Error::Invariant(
            "batch plan does not match the ordered event IDs".to_owned(),
        ));
    }
    let audit = open_ordered_gte_token_audit_store(ordered_path, token_audit_path)?;
    if audit.manifest().corpus_data_sha256 != manifest.corpus_data_sha256
        || audit.manifest_sha256() != manifest.token_audit_manifest_sha256
        || tokenization_contract_sha256(&audit.manifest().descriptor)?
            != manifest.tokenization_contract_sha256
        || audit.manifest().total_rows != manifest.total_rows
    {
        return Err(Error::Invariant(
            "batch plan does not match the verified token audit".to_owned(),
        ));
    }
    let (batch_shapes, total_batches, total_effective_tokens, total_padded_tokens) =
        summarize_plan(&audit, manifest.shard_rows, manifest.batch_rows as usize)?;
    if batch_shapes != manifest.batch_shapes
        || total_batches != manifest.total_batches
        || total_effective_tokens != manifest.total_effective_tokens
        || total_padded_tokens != manifest.total_padded_tokens
    {
        return Err(Error::Invariant(
            "batch-plan aggregates do not match the audited row schedule".to_owned(),
        ));
    }
    let identity = RepresentationBatchPlanIdentity {
        manifest_sha256: hash_file(&manifest_path)?,
        corpus_data_sha256: manifest.corpus_data_sha256.clone(),
        ordered_event_ids_sha256: manifest.ordered_event_ids_sha256.clone(),
        token_audit_manifest_sha256: manifest.token_audit_manifest_sha256.clone(),
        tokenization_contract_sha256: manifest.tokenization_contract_sha256.clone(),
        total_rows: manifest.total_rows,
        shard_rows: manifest.shard_rows,
        batch_rows: manifest.batch_rows,
        batching_rule: manifest.batching_rule.clone(),
    };
    Ok(RepresentationBatchPlan {
        manifest,
        identity,
        audit,
    })
}

pub fn tokenization_contract_sha256(descriptor: &RepresentationDescriptor) -> Result<String> {
    #[derive(Serialize)]
    struct TokenizationContract<'a> {
        contract: &'static str,
        model_id: &'a str,
        model_revision: &'a str,
        model_lock_sha256: &'a str,
        worker_sha256: &'a str,
        dependency_lock_sha256: &'a str,
        transformers_version: &'a str,
        model_token_ceiling: u32,
        document_input: &'a str,
        query_instruction: &'a str,
    }
    let encoded = serde_json::to_vec(&TokenizationContract {
        contract: "gte-tokenization-contract-v2",
        model_id: &descriptor.model_id,
        model_revision: &descriptor.model_revision,
        model_lock_sha256: &descriptor.model_lock_sha256,
        worker_sha256: &descriptor.worker_sha256,
        dependency_lock_sha256: &descriptor.dependency_lock_sha256,
        transformers_version: &descriptor.transformers_version,
        model_token_ceiling: descriptor.model_token_ceiling,
        document_input: &descriptor.document_input,
        query_instruction: &descriptor.query_instruction,
    })
    .map_err(|source| Error::Manifest {
        operation: "encode",
        path: PathBuf::from("<tokenization-contract>"),
        source,
    })?;
    Ok(hash_bytes(&encoded))
}

fn summarize_plan(
    audit: &OrderedGteTokenAudit,
    shard_rows: u64,
    batch_rows: usize,
) -> Result<(Vec<RepresentationBatchShapeCount>, u64, u64, u64)> {
    let mut shapes = BTreeMap::<(u32, u32), RepresentationBatchShapeCount>::new();
    let mut total_batches = 0_u64;
    let mut total_effective_tokens = 0_u64;
    let mut total_padded_tokens = 0_u64;
    let shard_count = audit.manifest().total_rows.div_ceil(shard_rows);
    for ordinal in 0..shard_count {
        let start_row = ordinal * shard_rows;
        let rows = shard_rows.min(audit.manifest().total_rows - start_row);
        let lengths = audit.document_lengths(start_row, rows)?;
        for batch in plan_batches(&lengths, batch_rows)? {
            let rows_per_batch = u32::try_from(batch.rows.len())
                .map_err(|_| Error::Invariant("planned batch rows do not fit u32".to_owned()))?;
            let padded_tokens = u64::from(rows_per_batch)
                .checked_mul(u64::from(batch.padded_tokens_per_row))
                .ok_or_else(|| Error::Invariant("planned padded tokens overflowed".to_owned()))?;
            let shape = shapes
                .entry((rows_per_batch, batch.padded_tokens_per_row))
                .or_insert(RepresentationBatchShapeCount {
                    rows_per_batch,
                    padded_tokens_per_row: batch.padded_tokens_per_row,
                    batches: 0,
                    effective_tokens: 0,
                    padded_tokens: 0,
                });
            shape.batches = shape
                .batches
                .checked_add(1)
                .ok_or_else(|| Error::Invariant("planned batch count overflowed".to_owned()))?;
            shape.effective_tokens = shape
                .effective_tokens
                .checked_add(batch.effective_tokens)
                .ok_or_else(|| {
                    Error::Invariant("planned effective tokens overflowed".to_owned())
                })?;
            shape.padded_tokens = shape
                .padded_tokens
                .checked_add(padded_tokens)
                .ok_or_else(|| Error::Invariant("planned padded tokens overflowed".to_owned()))?;
            total_batches = total_batches
                .checked_add(1)
                .ok_or_else(|| Error::Invariant("planned batch count overflowed".to_owned()))?;
            total_effective_tokens = total_effective_tokens
                .checked_add(batch.effective_tokens)
                .ok_or_else(|| {
                    Error::Invariant("planned effective tokens overflowed".to_owned())
                })?;
            total_padded_tokens = total_padded_tokens
                .checked_add(padded_tokens)
                .ok_or_else(|| Error::Invariant("planned padded tokens overflowed".to_owned()))?;
        }
    }
    Ok((
        shapes.into_values().collect(),
        total_batches,
        total_effective_tokens,
        total_padded_tokens,
    ))
}

fn plan_batches(lengths: &[u32], batch_rows: usize) -> Result<Vec<PlannedRepresentationBatch>> {
    if lengths.is_empty() || batch_rows == 0 {
        return Err(Error::Invariant(
            "batch planning requires nonempty lengths and positive batch rows".to_owned(),
        ));
    }
    let mut schedule = lengths
        .iter()
        .copied()
        .enumerate()
        .map(|(row_offset, tokens)| {
            if tokens == 0 {
                return Err(Error::Invariant(
                    "batch plan contains a zero token length".to_owned(),
                ));
            }
            Ok(PlannedRepresentationRow {
                row_offset: u64::try_from(row_offset)
                    .map_err(|_| Error::Invariant("row offset does not fit u64".to_owned()))?,
                tokens,
            })
        })
        .collect::<Result<Vec<_>>>()?;
    schedule.sort_unstable_by_key(|row| (row.tokens, row.row_offset));
    schedule
        .chunks(batch_rows)
        .map(|rows| {
            let effective_tokens = rows.iter().try_fold(0_u64, |total, row| {
                total
                    .checked_add(u64::from(row.tokens))
                    .ok_or_else(|| Error::Invariant("batch effective tokens overflowed".to_owned()))
            })?;
            Ok(PlannedRepresentationBatch {
                rows: rows.to_vec(),
                padded_tokens_per_row: rows.last().expect("batch chunk is nonempty").tokens,
                effective_tokens,
            })
        })
        .collect()
}

fn validate_config(config: &RepresentationBatchPlanConfig) -> Result<()> {
    if config.shard_rows == 0 || config.batch_rows == 0 {
        return Err(Error::Invariant(
            "batch-plan shard and batch rows must be positive".to_owned(),
        ));
    }
    if config.batch_rows > u32::MAX as usize {
        return Err(Error::Invariant("batch rows do not fit u32".to_owned()));
    }
    Ok(())
}

fn validate_manifest(manifest: &RepresentationBatchPlanManifest) -> Result<()> {
    if manifest.schema_version != SCHEMA_VERSION
        || manifest.total_rows == 0
        || manifest.shard_rows == 0
        || manifest.batch_rows == 0
        || manifest.batching_rule != BATCHING_RULE
        || manifest.total_batches == 0
        || manifest.total_effective_tokens == 0
        || manifest.total_padded_tokens < manifest.total_effective_tokens
        || manifest.batch_shapes.is_empty()
    {
        return Err(Error::Invariant(
            "representation batch-plan manifest is incompatible".to_owned(),
        ));
    }
    for hash in [
        &manifest.corpus_data_sha256,
        &manifest.ordered_event_ids_sha256,
        &manifest.token_audit_manifest_sha256,
        &manifest.tokenization_contract_sha256,
    ] {
        if hash.len() != 64 || !hash.bytes().all(|byte| byte.is_ascii_hexdigit()) {
            return Err(Error::Invariant(
                "representation batch plan has an invalid SHA-256".to_owned(),
            ));
        }
    }
    Ok(())
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
