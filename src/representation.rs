//! Immutable FP32 representation shards over the final ordered corpus.

use std::cmp::Reverse;
use std::collections::{BTreeMap, BinaryHeap};
use std::fs::{self, File, OpenOptions};
use std::io::{BufReader, BufWriter, Read, Seek, SeekFrom, Write};
use std::os::unix::fs::MetadataExt;
use std::path::{Path, PathBuf};
use std::time::{Duration, Instant};

use memmap2::{Mmap, MmapOptions};
use nostrdb::Transaction;
use serde::{Deserialize, Serialize};

use crate::artifact::{ArtifactFile, describe_fixed_artifact, hash_bytes, hash_file};
use crate::representation_batch_plan::{
    BATCHING_RULE, RepresentationBatchPlan, RepresentationBatchPlanIdentity,
    open_representation_batch_plan, tokenization_contract_sha256,
};
use crate::snapshot::{
    Error, Result, Validation, io_error, ndb_error, open_existing_ndb, read_manifest, require_file,
};

const SCHEMA_VERSION: u32 = 2;
const SHARD_SCHEMA_VERSION: u32 = 2;
const INDEX_SCHEMA_VERSION: u32 = 1;
const BUILD_IDENTITY_SCHEMA_VERSION: u32 = 1;
const VERIFICATION_SCHEMA_VERSION: u32 = 1;
const EVENT_ID_BYTES: usize = 32;
const INDEX_RECORD_BYTES: usize = EVENT_ID_BYTES + size_of::<u32>();
const INDEX_FILE: &str = "event-id-to-row.bin";
const INDEX_DIRECTORY: &str = "index";
const INDEX_MANIFEST_FILE: &str = "index-manifest.json";
const BUILD_IDENTITY_FILE: &str = "build-identity.json";
const MANIFEST_FILE: &str = "manifest.json";
const VERIFICATION_FILE: &str = "verification.json";
const VECTOR_FILE: &str = "vectors.f32le";

pub const FP32_SCAN_BLOCK_ROWS: usize = 4_096;

pub type EventId = [u8; EVENT_ID_BYTES];

/// Everything that can change the public semantic coordinate assigned to a note.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct RepresentationDescriptor {
    pub model_id: String,
    pub model_revision: String,
    pub model_lock_sha256: String,
    pub worker_sha256: String,
    pub dependency_lock_sha256: String,
    pub container_image: String,
    pub torch_version: String,
    pub transformers_version: String,
    pub cuda_version: String,
    pub execution_device: String,
    pub dimensions: u32,
    pub model_token_ceiling: u32,
    pub document_input: String,
    pub query_instruction: String,
    pub pooling: String,
    pub normalization: String,
    pub numeric_format: String,
}

/// Production inference boundary. Implementations may keep a model process alive.
pub trait RepresentationEncoder {
    fn descriptor(&self) -> &RepresentationDescriptor;
    fn encode_documents(&mut self, texts: &[&str]) -> Result<Vec<f32>>;
    fn encode_queries(&mut self, texts: &[&str]) -> Result<Vec<f32>>;
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum RepresentationArtifactPhase {
    ShardSetup,
    Write,
    Checkpoint,
    ManifestPublication,
    Verification,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RepresentationBatchShape {
    pub rows: u32,
    pub padded_tokens_per_row: u32,
    pub effective_tokens: u64,
}

/// Measurement and stop boundary around the exact production build loop.
pub trait RepresentationBuildObserver {
    fn check_continue(
        &mut self,
        _shard_ordinal: u32,
        _batch_ordinal: u32,
        _next: &RepresentationBatchShape,
    ) -> Result<()> {
        Ok(())
    }

    fn check_artifact_phase(
        &mut self,
        _phase: RepresentationArtifactPhase,
        _shard_ordinal: Option<u32>,
    ) -> Result<()> {
        Ok(())
    }

    fn completed_batch(
        &mut self,
        _shard_ordinal: u32,
        _batch_ordinal: u32,
        _shape: &RepresentationBatchShape,
        _elapsed: Duration,
    ) -> Result<()> {
        Ok(())
    }

    fn artifact_phase(
        &mut self,
        _phase: RepresentationArtifactPhase,
        _shard_ordinal: Option<u32>,
        _elapsed: Duration,
    ) -> Result<()> {
        Ok(())
    }

    fn completed_shard(&mut self, _shard: &RepresentationShard) {}
}

struct NoopRepresentationBuildObserver;

impl RepresentationBuildObserver for NoopRepresentationBuildObserver {}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct RepresentationIndexManifest {
    pub schema_version: u32,
    pub corpus_data_sha256: String,
    pub ordered_event_ids_sha256: String,
    pub total_rows: u64,
    pub event_id_to_row: ArtifactFile,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
struct RepresentationBuildIdentity {
    schema_version: u32,
    corpus_data_sha256: String,
    ordered_event_ids_sha256: String,
    total_rows: u64,
    descriptor_sha256: String,
    batch_plan: RepresentationBatchPlanIdentity,
    index_manifest_sha256: String,
}

/// Complete immutable identity for one vector shard.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct RepresentationShard {
    pub schema_version: u32,
    pub ordinal: u32,
    pub start_row: u64,
    pub rows: u64,
    pub descriptor_sha256: String,
    pub batch_plan_sha256: String,
    pub build_identity_sha256: String,
    pub batches: u64,
    pub effective_tokens: u64,
    pub padded_tokens: u64,
    pub vectors: ArtifactFile,
}

/// Current verified set of completed shards for one fixed representation.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct RepresentationManifest {
    pub schema_version: u32,
    pub corpus_data_sha256: String,
    pub ordered_event_ids_sha256: String,
    pub total_rows: u64,
    pub descriptor: RepresentationDescriptor,
    pub descriptor_sha256: String,
    pub batch_plan: RepresentationBatchPlanIdentity,
    pub build_identity_sha256: String,
    pub index_manifest_sha256: String,
    pub matrix_format: String,
    pub event_id_to_row: ArtifactFile,
    pub completed_rows: u64,
    pub complete: bool,
    pub shards: Vec<RepresentationShard>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
struct ImmutableFileIdentity {
    file: String,
    bytes: u64,
    device: u64,
    inode: u64,
    modified_seconds: i64,
    modified_nanoseconds: i64,
    changed_seconds: i64,
    changed_nanoseconds: i64,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
struct RepresentationVerification {
    schema_version: u32,
    representation_version: String,
    corpus_data_sha256: String,
    ordered_event_ids_sha256: String,
    corpus_data: ImmutableFileIdentity,
    ordered_event_ids: ImmutableFileIdentity,
    event_id_to_row: ImmutableFileIdentity,
    vector_shards: Vec<ImmutableFileIdentity>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
struct VerificationSnapshot {
    corpus_data: ImmutableFileIdentity,
    ordered_event_ids: ImmutableFileIdentity,
    event_id_to_row: ImmutableFileIdentity,
    vector_shards: Vec<ImmutableFileIdentity>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RepresentationBuildConfig {
    pub token_audit_path: PathBuf,
    pub batch_plan_path: PathBuf,
    pub shard_ordinals: Vec<u32>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RepresentationBuildResult {
    pub manifest: RepresentationManifest,
    pub representation_version: String,
    pub encoded_rows: u64,
    pub reused_rows: u64,
}

/// Open, checksum-verified public coordinates and their compact ID index.
#[derive(Debug)]
pub struct RepresentationStore {
    manifest: RepresentationManifest,
    representation_version: String,
    verification: Option<RepresentationVerification>,
    mapped: Option<MappedRepresentation>,
}

#[derive(Debug)]
struct MappedRepresentation {
    ordered_event_ids: Mmap,
    event_id_to_row: Mmap,
    shards: Vec<MappedRepresentationShard>,
}

#[derive(Debug)]
struct MappedRepresentationShard {
    start_row: u64,
    rows: u64,
    vectors: Mmap,
}

#[derive(Clone, Copy, Debug)]
struct RankedRow {
    row: u64,
    score: f32,
}

impl PartialEq for RankedRow {
    fn eq(&self, other: &Self) -> bool {
        rank_cmp((self.row, self.score), (other.row, other.score)).is_eq()
    }
}

impl Eq for RankedRow {}

impl PartialOrd for RankedRow {
    fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
        Some(self.cmp(other))
    }
}

impl Ord for RankedRow {
    fn cmp(&self, other: &Self) -> std::cmp::Ordering {
        rank_cmp((self.row, self.score), (other.row, other.score))
    }
}

impl RepresentationStore {
    pub fn manifest(&self) -> &RepresentationManifest {
        &self.manifest
    }

    pub fn representation_version(&self) -> &str {
        &self.representation_version
    }

    pub(crate) fn require_version(&self, requested: &str) -> Result<()> {
        if requested != self.representation_version {
            return Err(Error::InvalidQuery(format!(
                "representation version `{requested}` does not match `{}`",
                self.representation_version
            )));
        }
        Ok(())
    }

    pub(crate) fn require_verified_corpus(&self, corpus_data_path: &Path) -> Result<()> {
        let verification = self.verification.as_ref().ok_or_else(|| {
            Error::Invariant(
                "representation is not sealed; run verify representation before lookup".to_owned(),
            )
        })?;
        require_unchanged_file(corpus_data_path, &verification.corpus_data)
    }

    pub(crate) fn row_for_event(&self, event_id: EventId) -> Result<Option<u64>> {
        let mapped = self.mapped.as_ref().ok_or_else(unsealed_lookup_error)?;
        let bytes = &mapped.event_id_to_row;
        let mut low = 0_u64;
        let mut high = self.manifest.total_rows;
        while low < high {
            let middle = low + (high - low) / 2;
            let start = usize::try_from(middle)
                .ok()
                .and_then(|row| row.checked_mul(INDEX_RECORD_BYTES))
                .ok_or_else(|| Error::Invariant("event-ID index offset overflowed".to_owned()))?;
            let end = start + INDEX_RECORD_BYTES;
            let record = bytes.get(start..end).ok_or_else(|| {
                Error::Invariant("event-ID index mapping is shorter than its manifest".to_owned())
            })?;
            match record[..EVENT_ID_BYTES].cmp(&event_id) {
                std::cmp::Ordering::Less => low = middle + 1,
                std::cmp::Ordering::Greater => high = middle,
                std::cmp::Ordering::Equal => {
                    let row =
                        u32::from_le_bytes(record[EVENT_ID_BYTES..].try_into().expect("row width"));
                    return Ok(Some(u64::from(row)));
                }
            }
        }
        Ok(None)
    }

    pub(crate) fn event_for_row(&self, ordered_path: &Path, row: u64) -> Result<EventId> {
        if row >= self.manifest.total_rows {
            return Err(Error::Invariant(format!(
                "representation row {row} is outside the ordered corpus"
            )));
        }
        let _ = ordered_path;
        let mapped = self.mapped.as_ref().ok_or_else(unsealed_lookup_error)?;
        let start = usize::try_from(row)
            .ok()
            .and_then(|row| row.checked_mul(EVENT_ID_BYTES))
            .ok_or_else(|| Error::Invariant("ordered event-ID offset overflowed".to_owned()))?;
        let end = start + EVENT_ID_BYTES;
        mapped
            .ordered_event_ids
            .get(start..end)
            .ok_or_else(|| {
                Error::Invariant("ordered event-ID mapping is shorter than its manifest".to_owned())
            })?
            .try_into()
            .map_err(|_| Error::Invariant("ordered event ID has the wrong width".to_owned()))
    }

    pub(crate) fn vector_for_row(&self, row: u64) -> Result<Vec<f32>> {
        let mapped = self.mapped.as_ref().ok_or_else(unsealed_lookup_error)?;
        let shard = mapped
            .shards
            .iter()
            .find(|shard| row >= shard.start_row && row < shard.start_row + shard.rows)
            .ok_or_else(|| {
                Error::InvalidQuery(format!(
                    "ordered corpus row {row} has not been represented yet"
                ))
            })?;
        let dimensions = usize::try_from(self.manifest.descriptor.dimensions)
            .map_err(|_| Error::Invariant("dimensions do not fit usize".to_owned()))?;
        let local_row = row - shard.start_row;
        let row_bytes = dimensions
            .checked_mul(size_of::<f32>())
            .ok_or_else(|| Error::Invariant("vector row width overflowed".to_owned()))?;
        let start = usize::try_from(local_row)
            .ok()
            .and_then(|row| row.checked_mul(row_bytes))
            .ok_or_else(|| Error::Invariant("vector mapping offset overflowed".to_owned()))?;
        let end = start + row_bytes;
        decode_vector(
            shard.vectors.get(start..end).ok_or_else(|| {
                Error::Invariant("vector mapping is shorter than its manifest".to_owned())
            })?,
            dimensions,
        )
    }

    /// Visit represented vectors in corpus-row order without materializing the matrix.
    pub(crate) fn scan_vector_blocks(
        &self,
        block_rows: usize,
        mut visitor: impl FnMut(u64, &[f32]) -> Result<()>,
    ) -> Result<()> {
        if block_rows == 0 {
            return Err(Error::InvalidQuery(
                "vector scan block size must be positive".to_owned(),
            ));
        }

        let mapped = self.mapped.as_ref().ok_or_else(unsealed_lookup_error)?;
        let dimensions = usize::try_from(self.manifest.descriptor.dimensions)
            .map_err(|_| Error::Invariant("dimensions do not fit usize".to_owned()))?;
        let row_bytes = dimensions
            .checked_mul(size_of::<f32>())
            .ok_or_else(|| Error::Invariant("vector row width overflowed".to_owned()))?;
        let capacity_rows = mapped
            .shards
            .iter()
            .try_fold(0_usize, |maximum, shard| {
                usize::try_from(shard.rows)
                    .map(|rows| maximum.max(rows))
                    .map_err(|_| Error::Invariant("mapped shard rows do not fit usize".to_owned()))
            })?
            .min(block_rows);
        let capacity = capacity_rows
            .checked_mul(dimensions)
            .ok_or_else(|| Error::Invariant("vector scan block size overflowed".to_owned()))?;
        let mut decoded = Vec::with_capacity(capacity);

        for shard in &mapped.shards {
            let shard_rows = usize::try_from(shard.rows)
                .map_err(|_| Error::Invariant("mapped shard rows do not fit usize".to_owned()))?;
            let mut block_start = 0_usize;
            while block_start < shard_rows {
                let rows = block_rows.min(shard_rows - block_start);
                let values = rows.checked_mul(dimensions).ok_or_else(|| {
                    Error::Invariant("vector scan block size overflowed".to_owned())
                })?;
                let start = block_start.checked_mul(row_bytes).ok_or_else(|| {
                    Error::Invariant("mapped vector block offset overflowed".to_owned())
                })?;
                let bytes = values.checked_mul(size_of::<f32>()).ok_or_else(|| {
                    Error::Invariant("mapped vector block width overflowed".to_owned())
                })?;
                let end = start.checked_add(bytes).ok_or_else(|| {
                    Error::Invariant("mapped vector block end overflowed".to_owned())
                })?;
                let encoded = shard.vectors.get(start..end).ok_or_else(|| {
                    Error::Invariant("mapped vector shard is shorter than its manifest".to_owned())
                })?;

                decoded.clear();
                for bytes in encoded.chunks_exact(size_of::<f32>()) {
                    let value = f32::from_le_bytes(bytes.try_into().expect("f32 width"));
                    if !value.is_finite() {
                        return Err(Error::Invariant(
                            "stored vector contains a non-finite value".to_owned(),
                        ));
                    }
                    decoded.push(value);
                }

                let start_row = shard
                    .start_row
                    .checked_add(u64::try_from(block_start).map_err(|_| {
                        Error::Invariant("vector block row does not fit u64".to_owned())
                    })?)
                    .ok_or_else(|| Error::Invariant("vector block row overflowed".to_owned()))?;
                visitor(start_row, &decoded)?;
                block_start += rows;
            }
        }

        Ok(())
    }

    /// Scan every represented row once for a co-scheduled group of independent queries.
    pub(crate) fn search_many(
        &self,
        queries: &[&[f32]],
        depths: &[usize],
        excluded_rows: &[Option<u64>],
    ) -> Result<Vec<Vec<(u64, f32)>>> {
        if queries.is_empty()
            || queries.len() != depths.len()
            || queries.len() != excluded_rows.len()
        {
            return Err(Error::InvalidQuery(
                "co-scheduled search requires matching nonempty query, depth, and exclusion sets"
                    .to_owned(),
            ));
        }
        if depths.contains(&0) {
            return Err(Error::InvalidQuery(
                "candidate depth must be positive".to_owned(),
            ));
        }
        let dimensions = usize::try_from(self.manifest.descriptor.dimensions)
            .map_err(|_| Error::Invariant("dimensions do not fit usize".to_owned()))?;
        for query in queries {
            validate_vector(query, dimensions, "query")?;
        }
        let mapped = self.mapped.as_ref().ok_or_else(unsealed_lookup_error)?;
        let mut best = depths
            .iter()
            .map(|depth| {
                BinaryHeap::<Reverse<RankedRow>>::with_capacity(
                    (*depth)
                        .min(usize::try_from(self.manifest.completed_rows).unwrap_or(usize::MAX)),
                )
            })
            .collect::<Vec<_>>();
        let row_bytes = dimensions
            .checked_mul(size_of::<f32>())
            .ok_or_else(|| Error::Invariant("vector row width overflowed".to_owned()))?;

        for shard in &mapped.shards {
            let shard_rows = usize::try_from(shard.rows)
                .map_err(|_| Error::Invariant("mapped shard rows do not fit usize".to_owned()))?;
            let mut scores = vec![0.0_f32; queries.len()];
            for block_start in (0..shard_rows).step_by(FP32_SCAN_BLOCK_ROWS) {
                let block_end = (block_start + FP32_SCAN_BLOCK_ROWS).min(shard_rows);
                for local_row in block_start..block_end {
                    let start = local_row.checked_mul(row_bytes).ok_or_else(|| {
                        Error::Invariant("mapped vector row offset overflowed".to_owned())
                    })?;
                    let end = start + row_bytes;
                    let encoded = shard.vectors.get(start..end).ok_or_else(|| {
                        Error::Invariant(
                            "mapped vector shard is shorter than its manifest".to_owned(),
                        )
                    })?;
                    scores.fill(0.0);
                    for (dimension, bytes) in encoded.chunks_exact(size_of::<f32>()).enumerate() {
                        let candidate = f32::from_le_bytes(bytes.try_into().expect("f32 width"));
                        if !candidate.is_finite() {
                            return Err(Error::Invariant(
                                "stored vector contains a non-finite value".to_owned(),
                            ));
                        }
                        for (score, query) in scores.iter_mut().zip(queries) {
                            *score += candidate * query[dimension];
                        }
                    }
                    let row = shard.start_row + local_row as u64;
                    for query_index in 0..queries.len() {
                        if excluded_rows[query_index] == Some(row) {
                            continue;
                        }
                        let score = scores[query_index];
                        if !score.is_finite() {
                            return Err(Error::Invariant("cosine score is not finite".to_owned()));
                        }
                        retain_ranked_row(
                            &mut best[query_index],
                            depths[query_index],
                            RankedRow { row, score },
                        );
                    }
                }
            }
        }

        Ok(best
            .into_iter()
            .map(|heap| {
                let mut rows = heap
                    .into_iter()
                    .map(|Reverse(row)| (row.row, row.score))
                    .collect::<Vec<_>>();
                rows.sort_unstable_by(|left, right| rank_cmp(*right, *left));
                rows
            })
            .collect())
    }
}

/// Encode only complete, reusable row-range shards named by `shard_ordinals`.
pub fn build_representation_shards(
    corpus_path: impl AsRef<Path>,
    ordered_event_ids_path: impl AsRef<Path>,
    output_path: impl AsRef<Path>,
    config: &RepresentationBuildConfig,
    encoder: &mut dyn RepresentationEncoder,
) -> Result<RepresentationBuildResult> {
    let mut observer = NoopRepresentationBuildObserver;
    build_representation_shards_observed(
        corpus_path,
        ordered_event_ids_path,
        output_path,
        config,
        encoder,
        &mut observer,
    )
}

/// Continue the fixed representation plan through every shard. Existing valid
/// checkpoints are reused; callers cannot accidentally publish a selected
/// subset as the complete build.
pub fn complete_representation(
    corpus_path: impl AsRef<Path>,
    ordered_event_ids_path: impl AsRef<Path>,
    output_path: impl AsRef<Path>,
    token_audit_path: impl AsRef<Path>,
    batch_plan_path: impl AsRef<Path>,
    encoder: &mut dyn RepresentationEncoder,
) -> Result<RepresentationBuildResult> {
    let ordered_path = ordered_event_ids_path.as_ref();
    let token_audit_path = token_audit_path.as_ref();
    let batch_plan_path = batch_plan_path.as_ref();
    let plan = open_representation_batch_plan(ordered_path, token_audit_path, batch_plan_path)?;
    let total_shards = plan
        .identity()
        .total_rows
        .div_ceil(plan.identity().shard_rows);
    let shard_ordinals = (0..total_shards)
        .map(|ordinal| {
            u32::try_from(ordinal)
                .map_err(|_| Error::Invariant("representation shard ordinal overflowed".to_owned()))
        })
        .collect::<Result<Vec<_>>>()?;
    let result = build_representation_shards(
        corpus_path,
        ordered_path,
        output_path,
        &RepresentationBuildConfig {
            token_audit_path: token_audit_path.to_owned(),
            batch_plan_path: batch_plan_path.to_owned(),
            shard_ordinals,
        },
        encoder,
    )?;
    if !result.manifest.complete {
        return Err(Error::Invariant(
            "complete representation plan did not publish every shard".to_owned(),
        ));
    }
    Ok(result)
}

/// Build through the same production path while exposing exact batch and
/// artifact measurements to a calibration or budget observer.
pub fn build_representation_shards_observed(
    corpus_path: impl AsRef<Path>,
    ordered_event_ids_path: impl AsRef<Path>,
    output_path: impl AsRef<Path>,
    config: &RepresentationBuildConfig,
    encoder: &mut dyn RepresentationEncoder,
    observer: &mut dyn RepresentationBuildObserver,
) -> Result<RepresentationBuildResult> {
    let corpus_path = corpus_path.as_ref();
    let ordered_path = ordered_event_ids_path.as_ref();
    let root = output_path.as_ref();
    validate_config(config, encoder.descriptor())?;
    let plan = open_representation_batch_plan(
        ordered_path,
        &config.token_audit_path,
        &config.batch_plan_path,
    )?;
    if tokenization_contract_sha256(encoder.descriptor())?
        != plan.identity().tokenization_contract_sha256
    {
        return Err(Error::Invariant(
            "representation encoder does not match the batch plan's tokenization contract"
                .to_owned(),
        ));
    }
    let index = prepare_representation_index(corpus_path, ordered_path, root)?;
    let total_rows = index.total_rows;
    let corpus_data_sha256 = index.corpus_data_sha256.clone();
    let ordered_sha256 = index.ordered_event_ids_sha256.clone();
    if plan.identity().corpus_data_sha256 != corpus_data_sha256 {
        return Err(Error::Invariant(
            "token audit and batch plan belong to a different NostrDB corpus".to_owned(),
        ));
    }
    let descriptor = encoder.descriptor().clone();
    let descriptor_sha256 = representation_descriptor_sha256(&descriptor)?;
    let index_manifest_sha256 = hash_file(&root.join(INDEX_DIRECTORY).join(INDEX_MANIFEST_FILE))?;
    let build_identity_sha256 = ensure_build_identity(
        root,
        &RepresentationBuildIdentity {
            schema_version: BUILD_IDENTITY_SCHEMA_VERSION,
            corpus_data_sha256: corpus_data_sha256.clone(),
            ordered_event_ids_sha256: ordered_sha256.clone(),
            total_rows,
            descriptor_sha256: descriptor_sha256.clone(),
            batch_plan: plan.identity().clone(),
            index_manifest_sha256: index_manifest_sha256.clone(),
        },
    )?;
    fs::create_dir_all(root.join("shards"))
        .map_err(|source| io_error("create", root.join("shards"), source))?;
    let existing = existing_manifest(root)?;
    if let Some(existing) = &existing {
        validate_manifest_identity(
            existing,
            &corpus_data_sha256,
            &ordered_sha256,
            total_rows,
            &descriptor,
            &descriptor_sha256,
            plan.identity(),
            &build_identity_sha256,
            &index_manifest_sha256,
            &index.event_id_to_row,
        )?;
    }

    let mut shards = discover_shards(
        root,
        total_rows,
        &descriptor_sha256,
        &build_identity_sha256,
        &plan,
        descriptor.dimensions,
    )?;
    let corpus = open_existing_ndb(corpus_path, Validation::TrustedSource)?;
    let transaction = Transaction::new(&corpus)
        .map_err(|source| ndb_error("open transaction on", corpus_path, source))?;
    let mut encoded_rows = 0_u64;
    let mut reused_rows = 0_u64;
    for &ordinal in &config.shard_ordinals {
        let start_row = u64::from(ordinal)
            .checked_mul(plan.identity().shard_rows)
            .ok_or_else(|| Error::Invariant("shard start row overflowed".to_owned()))?;
        if start_row >= total_rows {
            return Err(Error::Invariant(format!(
                "shard ordinal {ordinal} starts beyond the corpus"
            )));
        }
        let rows = plan.identity().shard_rows.min(total_rows - start_row);
        if let Some(existing) = shards.get(&ordinal) {
            if existing.start_row != start_row || existing.rows != rows {
                return Err(Error::Invariant(format!(
                    "existing shard {ordinal} has the wrong row range"
                )));
            }
            reused_rows += rows;
            continue;
        }
        let shard = encode_shard(
            root,
            corpus_path,
            &corpus,
            &transaction,
            ordered_path,
            ordinal,
            start_row,
            rows,
            &plan,
            &descriptor_sha256,
            &build_identity_sha256,
            encoder,
            observer,
        )?;
        encoded_rows += rows;
        shards.insert(ordinal, shard);
    }
    drop(transaction);
    drop(corpus);

    let shards = shards.into_values().collect::<Vec<_>>();
    let completed_rows = shards.iter().try_fold(0_u64, |sum, shard| {
        sum.checked_add(shard.rows)
            .ok_or_else(|| Error::Invariant("completed row count overflowed".to_owned()))
    })?;
    let complete = completed_rows == total_rows && shards_cover_all(&shards, total_rows);
    let manifest = RepresentationManifest {
        schema_version: SCHEMA_VERSION,
        corpus_data_sha256,
        ordered_event_ids_sha256: ordered_sha256,
        total_rows,
        descriptor,
        descriptor_sha256,
        batch_plan: plan.identity().clone(),
        build_identity_sha256,
        index_manifest_sha256,
        matrix_format: "row-major-normalized-f32le-v1".to_owned(),
        event_id_to_row: index.event_id_to_row,
        completed_rows,
        complete,
        shards,
    };
    observer.check_artifact_phase(RepresentationArtifactPhase::ManifestPublication, None)?;
    let publication_started = Instant::now();
    publish_manifest(root, &manifest)?;
    observer.artifact_phase(
        RepresentationArtifactPhase::ManifestPublication,
        None,
        publication_started.elapsed(),
    )?;
    observer.check_artifact_phase(RepresentationArtifactPhase::Verification, None)?;
    let verification_started = Instant::now();
    let opened = verify_representation(corpus_path, ordered_path, root)?;
    observer.artifact_phase(
        RepresentationArtifactPhase::Verification,
        None,
        verification_started.elapsed(),
    )?;
    Ok(RepresentationBuildResult {
        manifest: opened.manifest,
        representation_version: opened.representation_version,
        encoded_rows,
        reused_rows,
    })
}

/// Reopen and verify the complete manifest, index, and every published shard.
pub fn open_representation(
    ordered_event_ids_path: impl AsRef<Path>,
    output_path: impl AsRef<Path>,
) -> Result<RepresentationStore> {
    let ordered_path = ordered_event_ids_path.as_ref();
    let root = output_path.as_ref();
    let manifest_path = root.join(MANIFEST_FILE);
    require_file(&manifest_path)?;
    let manifest: RepresentationManifest = read_manifest(&manifest_path)?;
    verify_manifest(root, ordered_path, &manifest)?;
    let representation_version = hash_file(&manifest_path)?;
    Ok(RepresentationStore {
        manifest,
        representation_version,
        verification: None,
        mapped: None,
    })
}

/// Deeply verify every immutable input once, then publish a cheap lookup seal.
pub fn verify_representation(
    corpus_path: impl AsRef<Path>,
    ordered_event_ids_path: impl AsRef<Path>,
    output_path: impl AsRef<Path>,
) -> Result<RepresentationStore> {
    let corpus_data_path = corpus_path.as_ref().join("data.mdb");
    let ordered_path = ordered_event_ids_path.as_ref();
    let root = output_path.as_ref();
    require_file(&corpus_data_path)?;
    require_file(ordered_path)?;
    let manifest_path = root.join(MANIFEST_FILE);
    require_file(&manifest_path)?;
    let initial_manifest: RepresentationManifest = read_manifest(&manifest_path)?;
    let initial_version = hash_file(&manifest_path)?;
    let before = verification_snapshot(&corpus_data_path, ordered_path, root, &initial_manifest)?;

    let mut store = open_representation(ordered_path, root)?;
    if store.representation_version != initial_version || store.manifest != initial_manifest {
        return Err(Error::Invariant(
            "representation manifest changed during verification".to_owned(),
        ));
    }
    if hash_file(&corpus_data_path)? != store.manifest.corpus_data_sha256 {
        return Err(Error::Invariant(
            "NostrDB corpus does not match the representation".to_owned(),
        ));
    }
    let after = verification_snapshot(&corpus_data_path, ordered_path, root, &store.manifest)?;
    if before != after {
        return Err(Error::Invariant(
            "an immutable representation input changed during verification".to_owned(),
        ));
    }
    let verification = RepresentationVerification {
        schema_version: VERIFICATION_SCHEMA_VERSION,
        representation_version: store.representation_version.clone(),
        corpus_data_sha256: store.manifest.corpus_data_sha256.clone(),
        ordered_event_ids_sha256: store.manifest.ordered_event_ids_sha256.clone(),
        corpus_data: after.corpus_data,
        ordered_event_ids: after.ordered_event_ids,
        event_id_to_row: after.event_id_to_row,
        vector_shards: after.vector_shards,
    };
    publish_verification(root, &verification)?;
    store.verification = Some(verification);
    Ok(store)
}

/// Open only a previously deep-verified immutable representation.
pub(crate) fn open_verified_representation(
    ordered_event_ids_path: impl AsRef<Path>,
    output_path: impl AsRef<Path>,
) -> Result<RepresentationStore> {
    let ordered_path = ordered_event_ids_path.as_ref();
    let root = output_path.as_ref();
    let manifest_path = root.join(MANIFEST_FILE);
    require_file(&manifest_path)?;
    let manifest: RepresentationManifest = read_manifest(&manifest_path)?;
    verify_manifest_structure(root, ordered_path, &manifest)?;
    let representation_version = hash_file(&manifest_path)?;
    let verification_path = root.join(VERIFICATION_FILE);
    if !verification_path.is_file() {
        return Err(Error::Invariant(
            "representation is not sealed; run verify representation before lookup".to_owned(),
        ));
    }
    let verification: RepresentationVerification = read_manifest(&verification_path)?;
    validate_verification(
        root,
        ordered_path,
        &manifest,
        &representation_version,
        &verification,
    )?;
    let mapped = map_verified_representation(root, ordered_path, &manifest)?;
    Ok(RepresentationStore {
        manifest,
        representation_version,
        verification: Some(verification),
        mapped: Some(mapped),
    })
}

#[allow(clippy::too_many_arguments)]
fn encode_shard(
    root: &Path,
    corpus_path: &Path,
    corpus: &nostrdb::Ndb,
    transaction: &Transaction,
    ordered_path: &Path,
    ordinal: u32,
    start_row: u64,
    rows: u64,
    plan: &RepresentationBatchPlan,
    descriptor_sha256: &str,
    build_identity_sha256: &str,
    encoder: &mut dyn RepresentationEncoder,
    observer: &mut dyn RepresentationBuildObserver,
) -> Result<RepresentationShard> {
    observer.check_artifact_phase(RepresentationArtifactPhase::ShardSetup, Some(ordinal))?;
    let setup_started = Instant::now();
    let shard_name = format!("{ordinal:06}");
    let target = root.join("shards").join(&shard_name);
    let temporary = root.join("shards").join(format!(".{shard_name}.tmp"));
    if temporary.exists() {
        fs::remove_dir_all(&temporary).map_err(|source| io_error("remove", &temporary, source))?;
    }
    fs::create_dir(&temporary).map_err(|source| io_error("create", &temporary, source))?;
    let result = (|| {
        let mut ordered =
            File::open(ordered_path).map_err(|source| io_error("open", ordered_path, source))?;
        ordered
            .seek(SeekFrom::Start(start_row * EVENT_ID_BYTES as u64))
            .map_err(|source| io_error("seek", ordered_path, source))?;
        let row_capacity = usize::try_from(rows)
            .map_err(|_| Error::Invariant("shard rows do not fit usize".to_owned()))?;
        let mut ids = Vec::with_capacity(row_capacity);
        for _ in 0..rows {
            let mut id = [0_u8; EVENT_ID_BYTES];
            ordered
                .read_exact(&mut id)
                .map_err(|source| io_error("read", ordered_path, source))?;
            ids.push(id);
        }

        let dimensions = usize::try_from(encoder.descriptor().dimensions)
            .map_err(|_| Error::Invariant("dimensions do not fit usize".to_owned()))?;
        let row_bytes = dimensions
            .checked_mul(size_of::<f32>())
            .ok_or_else(|| Error::Invariant("vector row width overflowed".to_owned()))?;
        let vector_bytes = rows
            .checked_mul(row_bytes as u64)
            .ok_or_else(|| Error::Invariant("vector shard size overflowed".to_owned()))?;
        let vector_path = temporary.join(VECTOR_FILE);
        let mut vector_file = OpenOptions::new()
            .create_new(true)
            .read(true)
            .write(true)
            .open(&vector_path)
            .map_err(|source| io_error("create", &vector_path, source))?;
        vector_file
            .set_len(vector_bytes)
            .map_err(|source| io_error("size", &vector_path, source))?;

        let batches = plan.shard_batches(ordinal)?;
        observer.artifact_phase(
            RepresentationArtifactPhase::ShardSetup,
            Some(ordinal),
            setup_started.elapsed(),
        )?;
        let mut effective_tokens = 0_u64;
        let mut padded_tokens = 0_u64;
        for (batch_ordinal, batch) in batches.iter().enumerate() {
            let batch_ordinal = u32::try_from(batch_ordinal)
                .map_err(|_| Error::Invariant("batch ordinal does not fit u32".to_owned()))?;
            let shape = RepresentationBatchShape {
                rows: u32::try_from(batch.rows.len()).map_err(|_| {
                    Error::Invariant("planned batch rows do not fit u32".to_owned())
                })?,
                padded_tokens_per_row: batch.padded_tokens_per_row,
                effective_tokens: batch.effective_tokens,
            };
            observer.check_continue(ordinal, batch_ordinal, &shape)?;
            let batch_started = Instant::now();
            let mut texts = Vec::with_capacity(batch.rows.len());
            for row in &batch.rows {
                let row_offset = usize::try_from(row.row_offset)
                    .map_err(|_| Error::Invariant("row offset does not fit usize".to_owned()))?;
                let id = ids.get(row_offset).ok_or_else(|| {
                    Error::Invariant("batch-plan row is outside its output shard".to_owned())
                })?;
                let note = corpus
                    .get_note_by_id(transaction, id)
                    .map_err(|source| ndb_error("load ordered note from", corpus_path, source))?;
                texts.push(note.content().to_owned());
            }
            let borrowed = texts.iter().map(String::as_str).collect::<Vec<_>>();
            let encoded = encoder.encode_documents(&borrowed)?;
            let expected = borrowed
                .len()
                .checked_mul(dimensions)
                .ok_or_else(|| Error::Invariant("encoded batch width overflowed".to_owned()))?;
            if encoded.len() != expected {
                return Err(Error::Encoder {
                    operation: "encode documents",
                    message: format!(
                        "encoder returned {} values for {expected} expected values",
                        encoded.len()
                    ),
                });
            }
            let write_started = Instant::now();
            for (row, vector) in batch.rows.iter().zip(encoded.chunks_exact(dimensions)) {
                validate_vector(vector, dimensions, "document")?;
                let offset = row
                    .row_offset
                    .checked_mul(row_bytes as u64)
                    .ok_or_else(|| Error::Invariant("vector write offset overflowed".to_owned()))?;
                vector_file
                    .seek(SeekFrom::Start(offset))
                    .map_err(|source| io_error("seek", &vector_path, source))?;
                for value in vector {
                    vector_file
                        .write_all(&value.to_le_bytes())
                        .map_err(|source| io_error("write", &vector_path, source))?;
                }
            }
            observer.artifact_phase(
                RepresentationArtifactPhase::Write,
                Some(ordinal),
                write_started.elapsed(),
            )?;
            observer.completed_batch(ordinal, batch_ordinal, &shape, batch_started.elapsed())?;
            effective_tokens = effective_tokens
                .checked_add(batch.effective_tokens)
                .ok_or_else(|| Error::Invariant("shard effective tokens overflowed".to_owned()))?;
            padded_tokens = padded_tokens
                .checked_add(
                    u64::from(shape.rows)
                        .checked_mul(u64::from(shape.padded_tokens_per_row))
                        .ok_or_else(|| {
                            Error::Invariant("shard padded tokens overflowed".to_owned())
                        })?,
                )
                .ok_or_else(|| Error::Invariant("shard padded tokens overflowed".to_owned()))?;
        }

        observer.check_artifact_phase(RepresentationArtifactPhase::Checkpoint, Some(ordinal))?;
        let checkpoint_started = Instant::now();
        vector_file
            .sync_all()
            .map_err(|source| io_error("sync", &vector_path, source))?;
        let relative_vector = format!("shards/{shard_name}/{VECTOR_FILE}");
        let vectors = describe_fixed_artifact(&vector_path, &relative_vector, row_bytes, rows)?;
        let manifest = RepresentationShard {
            schema_version: SHARD_SCHEMA_VERSION,
            ordinal,
            start_row,
            rows,
            descriptor_sha256: descriptor_sha256.to_owned(),
            batch_plan_sha256: plan.identity().manifest_sha256.clone(),
            build_identity_sha256: build_identity_sha256.to_owned(),
            batches: u64::try_from(batches.len())
                .map_err(|_| Error::Invariant("shard batch count does not fit u64".to_owned()))?,
            effective_tokens,
            padded_tokens,
            vectors,
        };
        write_json_new(&temporary.join(MANIFEST_FILE), &manifest)?;
        sync_directory(&temporary)?;
        Ok((manifest, checkpoint_started))
    })();
    let (manifest, checkpoint_started) = match result {
        Ok(completed) => completed,
        Err(error) => {
            let _ = fs::remove_dir_all(&temporary);
            return Err(error);
        }
    };
    if target.exists() {
        return Err(Error::ArtifactExists(target));
    }
    fs::rename(&temporary, &target).map_err(|source| io_error("publish", &target, source))?;
    sync_directory(&root.join("shards"))?;
    observer.artifact_phase(
        RepresentationArtifactPhase::Checkpoint,
        Some(ordinal),
        checkpoint_started.elapsed(),
    )?;
    observer.completed_shard(&manifest);
    Ok(manifest)
}

/// Prepare the complete event-ID index locally without loading an encoder.
/// The index and its corpus/order identity publish as one directory.
pub fn prepare_representation_index(
    corpus_path: impl AsRef<Path>,
    ordered_event_ids_path: impl AsRef<Path>,
    output_path: impl AsRef<Path>,
) -> Result<RepresentationIndexManifest> {
    let corpus_path = corpus_path.as_ref();
    let ordered_path = ordered_event_ids_path.as_ref();
    let root = output_path.as_ref();
    require_file(ordered_path)?;
    let ordered_bytes = fs::metadata(ordered_path)
        .map_err(|source| io_error("read metadata for", ordered_path, source))?
        .len();
    if ordered_bytes == 0 || !ordered_bytes.is_multiple_of(EVENT_ID_BYTES as u64) {
        return Err(Error::Invariant(
            "ordered event IDs are empty or contain a partial record".to_owned(),
        ));
    }
    let total_rows = ordered_bytes / EVENT_ID_BYTES as u64;
    if total_rows > u64::from(u32::MAX) {
        return Err(Error::Invariant(
            "ordered event-ID count does not fit a u32 row index".to_owned(),
        ));
    }
    let corpus_data_path = corpus_path.join("data.mdb");
    require_file(&corpus_data_path)?;
    let corpus_data_sha256 = hash_file(&corpus_data_path)?;
    let ordered_event_ids_sha256 = hash_file(ordered_path)?;
    fs::create_dir_all(root).map_err(|source| io_error("create", root, source))?;
    if root.join(INDEX_FILE).exists() {
        return Err(Error::Invariant(
            "representation contains an unpublished index without identity".to_owned(),
        ));
    }
    let target = root.join(INDEX_DIRECTORY);
    let manifest_path = target.join(INDEX_MANIFEST_FILE);
    if target.exists() {
        if !manifest_path.is_file() {
            return Err(Error::Invariant(
                "representation contains an unpublished index without identity".to_owned(),
            ));
        }
        let manifest: RepresentationIndexManifest = read_manifest(&manifest_path)?;
        verify_index_manifest(root, &manifest)?;
        if manifest.corpus_data_sha256 != corpus_data_sha256
            || manifest.ordered_event_ids_sha256 != ordered_event_ids_sha256
            || manifest.total_rows != total_rows
        {
            return Err(Error::Invariant(
                "existing representation index belongs to a different corpus or order".to_owned(),
            ));
        }
        return Ok(manifest);
    }

    let temporary = root.join(format!(".{INDEX_DIRECTORY}.tmp"));
    if temporary.exists() {
        fs::remove_dir_all(&temporary).map_err(|source| io_error("remove", &temporary, source))?;
    }
    fs::create_dir(&temporary).map_err(|source| io_error("create", &temporary, source))?;
    let index_path = temporary.join(INDEX_FILE);
    let mut ordered = BufReader::new(
        File::open(ordered_path).map_err(|source| io_error("open", ordered_path, source))?,
    );
    let mut records = Vec::with_capacity(total_rows as usize);
    for row in 0..total_rows {
        let mut id = [0_u8; EVENT_ID_BYTES];
        ordered
            .read_exact(&mut id)
            .map_err(|source| io_error("read", ordered_path, source))?;
        records.push((id, row as u32));
    }
    records.sort_unstable_by_key(|(id, _)| *id);
    if records.windows(2).any(|pair| pair[0].0 == pair[1].0) {
        return Err(Error::Invariant(
            "ordered corpus contains duplicate event IDs".to_owned(),
        ));
    }
    let file = OpenOptions::new()
        .create_new(true)
        .write(true)
        .open(&index_path)
        .map_err(|source| io_error("create", &index_path, source))?;
    let mut writer = BufWriter::new(file);
    for (id, row) in records {
        writer
            .write_all(&id)
            .and_then(|()| writer.write_all(&row.to_le_bytes()))
            .map_err(|source| io_error("write", &index_path, source))?;
    }
    writer
        .flush()
        .map_err(|source| io_error("flush", &index_path, source))?;
    writer
        .get_ref()
        .sync_all()
        .map_err(|source| io_error("sync", &index_path, source))?;
    let manifest = RepresentationIndexManifest {
        schema_version: INDEX_SCHEMA_VERSION,
        corpus_data_sha256,
        ordered_event_ids_sha256,
        total_rows,
        event_id_to_row: describe_fixed_artifact(
            &index_path,
            &format!("{INDEX_DIRECTORY}/{INDEX_FILE}"),
            INDEX_RECORD_BYTES,
            total_rows,
        )?,
    };
    write_json_new(&temporary.join(INDEX_MANIFEST_FILE), &manifest)?;
    sync_directory(&temporary)?;
    fs::rename(&temporary, &target).map_err(|source| io_error("publish", &target, source))?;
    sync_directory(root)?;
    Ok(manifest)
}

fn verify_index_manifest(root: &Path, manifest: &RepresentationIndexManifest) -> Result<()> {
    if manifest.schema_version != INDEX_SCHEMA_VERSION
        || manifest.total_rows == 0
        || manifest.total_rows > u64::from(u32::MAX)
        || !is_sha256(&manifest.corpus_data_sha256)
        || !is_sha256(&manifest.ordered_event_ids_sha256)
    {
        return Err(Error::Invariant(
            "representation index manifest is incompatible".to_owned(),
        ));
    }
    let expected_file = format!("{INDEX_DIRECTORY}/{INDEX_FILE}");
    let actual = describe_fixed_artifact(
        &root.join(&expected_file),
        &expected_file,
        INDEX_RECORD_BYTES,
        manifest.total_rows,
    )?;
    if actual != manifest.event_id_to_row {
        return Err(Error::Invariant(
            "event-ID index does not match its immutable identity".to_owned(),
        ));
    }
    Ok(())
}

fn ensure_build_identity(root: &Path, expected: &RepresentationBuildIdentity) -> Result<String> {
    let path = root.join(BUILD_IDENTITY_FILE);
    if path.exists() {
        let actual: RepresentationBuildIdentity = read_manifest(&path)?;
        if &actual != expected {
            return Err(Error::Invariant(
                "existing representation shards belong to different inputs or settings".to_owned(),
            ));
        }
        return hash_file(&path);
    }
    let shard_root = root.join("shards");
    if shard_root.exists() {
        for entry in
            fs::read_dir(&shard_root).map_err(|source| io_error("read", &shard_root, source))?
        {
            let entry = entry.map_err(|source| io_error("read", &shard_root, source))?;
            let name = entry.file_name().to_string_lossy().into_owned();
            if name.starts_with('.') {
                if entry.path().is_dir() {
                    fs::remove_dir_all(entry.path())
                        .map_err(|source| io_error("remove", entry.path(), source))?;
                } else {
                    fs::remove_file(entry.path())
                        .map_err(|source| io_error("remove", entry.path(), source))?;
                }
                continue;
            }
            return Err(Error::Invariant(
                "representation contains orphan shards without a build identity".to_owned(),
            ));
        }
    }
    let temporary = root.join(format!(".{BUILD_IDENTITY_FILE}.tmp"));
    if temporary.exists() {
        fs::remove_file(&temporary).map_err(|source| io_error("remove", &temporary, source))?;
    }
    write_json_new(&temporary, expected)?;
    fs::rename(&temporary, &path).map_err(|source| io_error("publish", &path, source))?;
    sync_directory(root)?;
    hash_file(&path)
}

fn discover_shards(
    root: &Path,
    total_rows: u64,
    descriptor_sha256: &str,
    build_identity_sha256: &str,
    plan: &RepresentationBatchPlan,
    dimensions: u32,
) -> Result<BTreeMap<u32, RepresentationShard>> {
    let directory = root.join("shards");
    let mut shards = BTreeMap::new();
    for entry in fs::read_dir(&directory).map_err(|source| io_error("read", &directory, source))? {
        let entry = entry.map_err(|source| io_error("read", &directory, source))?;
        let name = entry.file_name();
        let name = name.to_string_lossy();
        if name.starts_with('.') {
            fs::remove_dir_all(entry.path())
                .map_err(|source| io_error("remove", entry.path(), source))?;
            continue;
        }
        let ordinal = name.parse::<u32>().map_err(|_| {
            Error::Invariant(format!("unexpected representation shard entry `{name}`"))
        })?;
        let manifest_path = entry.path().join(MANIFEST_FILE);
        require_file(&manifest_path)?;
        let shard: RepresentationShard = read_manifest(&manifest_path)?;
        if shard.ordinal != ordinal {
            return Err(Error::Invariant(format!(
                "representation shard directory {ordinal} contains ordinal {}",
                shard.ordinal
            )));
        }
        verify_shard(
            root,
            &shard,
            total_rows,
            descriptor_sha256,
            build_identity_sha256,
            plan.identity(),
            dimensions,
        )?;
        verify_shard_schedule(&shard, plan)?;
        if shards.insert(ordinal, shard).is_some() {
            return Err(Error::Invariant(format!(
                "duplicate representation shard ordinal {ordinal}"
            )));
        }
    }
    Ok(shards)
}

fn verify_manifest(
    root: &Path,
    ordered_path: &Path,
    manifest: &RepresentationManifest,
) -> Result<()> {
    if manifest.schema_version != SCHEMA_VERSION
        || manifest.total_rows == 0
        || manifest.total_rows > u64::from(u32::MAX)
        || manifest.matrix_format != "row-major-normalized-f32le-v1"
    {
        return Err(Error::Invariant(
            "representation manifest has unsupported global settings".to_owned(),
        ));
    }
    validate_descriptor(&manifest.descriptor)?;
    if representation_descriptor_sha256(&manifest.descriptor)? != manifest.descriptor_sha256 {
        return Err(Error::Invariant(
            "representation descriptor checksum does not match".to_owned(),
        ));
    }
    validate_batch_plan_identity(&manifest.batch_plan)?;
    if !is_sha256(&manifest.corpus_data_sha256)
        || !is_sha256(&manifest.ordered_event_ids_sha256)
        || !is_sha256(&manifest.descriptor_sha256)
        || !is_sha256(&manifest.build_identity_sha256)
        || !is_sha256(&manifest.index_manifest_sha256)
        || manifest.batch_plan.total_rows != manifest.total_rows
        || manifest.batch_plan.ordered_event_ids_sha256 != manifest.ordered_event_ids_sha256
    {
        return Err(Error::Invariant(
            "representation build, index, or batch-plan identity does not match".to_owned(),
        ));
    }
    verify_build_identity(root, manifest)?;
    let index_manifest_path = root.join(INDEX_DIRECTORY).join(INDEX_MANIFEST_FILE);
    require_file(&index_manifest_path)?;
    if hash_file(&index_manifest_path)? != manifest.index_manifest_sha256 {
        return Err(Error::Invariant(
            "representation index identity does not match".to_owned(),
        ));
    }
    let index_manifest: RepresentationIndexManifest = read_manifest(&index_manifest_path)?;
    verify_index_manifest(root, &index_manifest)?;
    if index_manifest.corpus_data_sha256 != manifest.corpus_data_sha256
        || index_manifest.ordered_event_ids_sha256 != manifest.ordered_event_ids_sha256
        || index_manifest.total_rows != manifest.total_rows
        || index_manifest.event_id_to_row != manifest.event_id_to_row
    {
        return Err(Error::Invariant(
            "representation index does not match the representation manifest".to_owned(),
        ));
    }
    require_file(ordered_path)?;
    let ordered_bytes = fs::metadata(ordered_path)
        .map_err(|source| io_error("read metadata for", ordered_path, source))?
        .len();
    if ordered_bytes != manifest.total_rows * EVENT_ID_BYTES as u64
        || hash_file(ordered_path)? != manifest.ordered_event_ids_sha256
    {
        return Err(Error::Invariant(
            "ordered event IDs do not match the representation".to_owned(),
        ));
    }
    let mut completed_rows = 0_u64;
    let mut previous_ordinal = None;
    for shard in &manifest.shards {
        if previous_ordinal.is_some_and(|previous| previous >= shard.ordinal) {
            return Err(Error::Invariant(
                "representation shards are not in unique ordinal order".to_owned(),
            ));
        }
        verify_shard(
            root,
            shard,
            manifest.total_rows,
            &manifest.descriptor_sha256,
            &manifest.build_identity_sha256,
            &manifest.batch_plan,
            manifest.descriptor.dimensions,
        )?;
        completed_rows = completed_rows
            .checked_add(shard.rows)
            .ok_or_else(|| Error::Invariant("completed row count overflowed".to_owned()))?;
        previous_ordinal = Some(shard.ordinal);
    }
    if completed_rows != manifest.completed_rows
        || manifest.complete
            != (completed_rows == manifest.total_rows
                && shards_cover_all(&manifest.shards, manifest.total_rows))
    {
        return Err(Error::Invariant(
            "representation completion state is inconsistent".to_owned(),
        ));
    }
    Ok(())
}

fn verify_manifest_structure(
    root: &Path,
    ordered_path: &Path,
    manifest: &RepresentationManifest,
) -> Result<()> {
    if manifest.schema_version != SCHEMA_VERSION
        || manifest.total_rows == 0
        || manifest.total_rows > u64::from(u32::MAX)
        || manifest.matrix_format != "row-major-normalized-f32le-v1"
    {
        return Err(Error::Invariant(
            "representation manifest has unsupported global settings".to_owned(),
        ));
    }
    validate_descriptor(&manifest.descriptor)?;
    if representation_descriptor_sha256(&manifest.descriptor)? != manifest.descriptor_sha256 {
        return Err(Error::Invariant(
            "representation descriptor checksum does not match".to_owned(),
        ));
    }
    validate_batch_plan_identity(&manifest.batch_plan)?;
    if !is_sha256(&manifest.corpus_data_sha256)
        || !is_sha256(&manifest.ordered_event_ids_sha256)
        || !is_sha256(&manifest.descriptor_sha256)
        || !is_sha256(&manifest.build_identity_sha256)
        || !is_sha256(&manifest.index_manifest_sha256)
        || manifest.batch_plan.total_rows != manifest.total_rows
        || manifest.batch_plan.ordered_event_ids_sha256 != manifest.ordered_event_ids_sha256
    {
        return Err(Error::Invariant(
            "representation build, index, or batch-plan identity does not match".to_owned(),
        ));
    }
    verify_build_identity(root, manifest)?;
    let index_manifest_path = root.join(INDEX_DIRECTORY).join(INDEX_MANIFEST_FILE);
    require_file(&index_manifest_path)?;
    if hash_file(&index_manifest_path)? != manifest.index_manifest_sha256 {
        return Err(Error::Invariant(
            "representation index identity does not match".to_owned(),
        ));
    }
    let index_manifest: RepresentationIndexManifest = read_manifest(&index_manifest_path)?;
    verify_index_manifest_structure(root, &index_manifest)?;
    if index_manifest.corpus_data_sha256 != manifest.corpus_data_sha256
        || index_manifest.ordered_event_ids_sha256 != manifest.ordered_event_ids_sha256
        || index_manifest.total_rows != manifest.total_rows
        || index_manifest.event_id_to_row != manifest.event_id_to_row
    {
        return Err(Error::Invariant(
            "representation index does not match the representation manifest".to_owned(),
        ));
    }
    require_file(ordered_path)?;
    let ordered_bytes = fs::metadata(ordered_path)
        .map_err(|source| io_error("read metadata for", ordered_path, source))?
        .len();
    if ordered_bytes != manifest.total_rows * EVENT_ID_BYTES as u64 {
        return Err(Error::Invariant(
            "ordered event IDs do not match the representation".to_owned(),
        ));
    }
    let mut completed_rows = 0_u64;
    let mut previous_ordinal = None;
    for shard in &manifest.shards {
        if previous_ordinal.is_some_and(|previous| previous >= shard.ordinal) {
            return Err(Error::Invariant(
                "representation shards are not in unique ordinal order".to_owned(),
            ));
        }
        verify_shard_structure(
            root,
            shard,
            manifest.total_rows,
            &manifest.descriptor_sha256,
            &manifest.build_identity_sha256,
            &manifest.batch_plan,
            manifest.descriptor.dimensions,
        )?;
        completed_rows = completed_rows
            .checked_add(shard.rows)
            .ok_or_else(|| Error::Invariant("completed row count overflowed".to_owned()))?;
        previous_ordinal = Some(shard.ordinal);
    }
    if completed_rows != manifest.completed_rows
        || manifest.complete
            != (completed_rows == manifest.total_rows
                && shards_cover_all(&manifest.shards, manifest.total_rows))
    {
        return Err(Error::Invariant(
            "representation completion state is inconsistent".to_owned(),
        ));
    }
    Ok(())
}

fn verify_index_manifest_structure(
    root: &Path,
    manifest: &RepresentationIndexManifest,
) -> Result<()> {
    if manifest.schema_version != INDEX_SCHEMA_VERSION
        || manifest.total_rows == 0
        || manifest.total_rows > u64::from(u32::MAX)
        || !is_sha256(&manifest.corpus_data_sha256)
        || !is_sha256(&manifest.ordered_event_ids_sha256)
    {
        return Err(Error::Invariant(
            "representation index manifest is incompatible".to_owned(),
        ));
    }
    let expected_file = format!("{INDEX_DIRECTORY}/{INDEX_FILE}");
    verify_artifact_shape(
        &root.join(&expected_file),
        &manifest.event_id_to_row,
        &expected_file,
        INDEX_RECORD_BYTES,
        manifest.total_rows,
    )
}

#[allow(clippy::too_many_arguments)]
fn verify_shard_structure(
    root: &Path,
    shard: &RepresentationShard,
    total_rows: u64,
    descriptor_sha256: &str,
    build_identity_sha256: &str,
    batch_plan: &RepresentationBatchPlanIdentity,
    dimensions: u32,
) -> Result<()> {
    let expected_start = u64::from(shard.ordinal)
        .checked_mul(batch_plan.shard_rows)
        .ok_or_else(|| Error::Invariant("shard start row overflowed".to_owned()))?;
    let expected_rows = batch_plan
        .shard_rows
        .min(total_rows.saturating_sub(expected_start));
    let expected_file = format!("shards/{:06}/{VECTOR_FILE}", shard.ordinal);
    if shard.schema_version != SHARD_SCHEMA_VERSION
        || shard.start_row != expected_start
        || shard.rows == 0
        || shard.rows != expected_rows
        || shard.descriptor_sha256 != descriptor_sha256
        || shard.batch_plan_sha256 != batch_plan.manifest_sha256
        || shard.build_identity_sha256 != build_identity_sha256
        || shard.batches == 0
        || shard.effective_tokens < shard.rows
        || shard.padded_tokens < shard.effective_tokens
    {
        return Err(Error::Invariant(format!(
            "representation shard {} has incompatible identity",
            shard.ordinal
        )));
    }
    verify_artifact_shape(
        &root.join(&expected_file),
        &shard.vectors,
        &expected_file,
        usize::try_from(dimensions)
            .map_err(|_| Error::Invariant("dimensions do not fit usize".to_owned()))?
            * size_of::<f32>(),
        shard.rows,
    )
}

fn verify_artifact_shape(
    path: &Path,
    artifact: &ArtifactFile,
    expected_file: &str,
    expected_record_bytes: usize,
    expected_records: u64,
) -> Result<()> {
    let expected_bytes = expected_records
        .checked_mul(expected_record_bytes as u64)
        .ok_or_else(|| Error::Invariant("artifact byte length overflowed".to_owned()))?;
    let metadata =
        fs::metadata(path).map_err(|source| io_error("read metadata for", path, source))?;
    if !metadata.is_file()
        || artifact.file != expected_file
        || artifact.record_bytes != expected_record_bytes as u32
        || artifact.records != expected_records
        || artifact.bytes != expected_bytes
        || metadata.len() != expected_bytes
        || !is_sha256(&artifact.sha256)
    {
        return Err(Error::Invariant(format!(
            "artifact `{}` has incompatible immutable metadata",
            path.display()
        )));
    }
    Ok(())
}

#[allow(clippy::too_many_arguments)]
fn verify_shard(
    root: &Path,
    shard: &RepresentationShard,
    total_rows: u64,
    descriptor_sha256: &str,
    build_identity_sha256: &str,
    batch_plan: &RepresentationBatchPlanIdentity,
    dimensions: u32,
) -> Result<()> {
    let expected_start = u64::from(shard.ordinal)
        .checked_mul(batch_plan.shard_rows)
        .ok_or_else(|| Error::Invariant("shard start row overflowed".to_owned()))?;
    let expected_rows = batch_plan
        .shard_rows
        .min(total_rows.saturating_sub(expected_start));
    let expected_file = format!("shards/{:06}/{VECTOR_FILE}", shard.ordinal);
    if shard.schema_version != SHARD_SCHEMA_VERSION
        || shard.start_row != expected_start
        || shard.rows == 0
        || shard.rows != expected_rows
        || shard.descriptor_sha256 != descriptor_sha256
        || shard.batch_plan_sha256 != batch_plan.manifest_sha256
        || shard.build_identity_sha256 != build_identity_sha256
        || shard.batches == 0
        || shard.effective_tokens < shard.rows
        || shard.padded_tokens < shard.effective_tokens
        || shard.vectors.file != expected_file
    {
        return Err(Error::Invariant(format!(
            "representation shard {} has incompatible identity",
            shard.ordinal
        )));
    }
    let actual = describe_fixed_artifact(
        &root.join(&expected_file),
        &expected_file,
        usize::try_from(dimensions)
            .map_err(|_| Error::Invariant("dimensions do not fit usize".to_owned()))?
            * size_of::<f32>(),
        shard.rows,
    )?;
    if actual != shard.vectors {
        return Err(Error::Invariant(format!(
            "representation shard {} checksum does not match",
            shard.ordinal
        )));
    }
    Ok(())
}

fn verify_shard_schedule(
    shard: &RepresentationShard,
    plan: &RepresentationBatchPlan,
) -> Result<()> {
    let batches = plan.shard_batches(shard.ordinal)?;
    let effective_tokens = batches.iter().try_fold(0_u64, |total, batch| {
        total
            .checked_add(batch.effective_tokens)
            .ok_or_else(|| Error::Invariant("shard effective tokens overflowed".to_owned()))
    })?;
    let padded_tokens = batches.iter().try_fold(0_u64, |total, batch| {
        let batch_tokens = u64::try_from(batch.rows.len())
            .ok()
            .and_then(|rows| rows.checked_mul(u64::from(batch.padded_tokens_per_row)))
            .ok_or_else(|| Error::Invariant("shard padded tokens overflowed".to_owned()))?;
        total
            .checked_add(batch_tokens)
            .ok_or_else(|| Error::Invariant("shard padded tokens overflowed".to_owned()))
    })?;
    let batch_count = u64::try_from(batches.len())
        .map_err(|_| Error::Invariant("shard batch count does not fit u64".to_owned()))?;
    if shard.batches != batch_count
        || shard.effective_tokens != effective_tokens
        || shard.padded_tokens != padded_tokens
    {
        return Err(Error::Invariant(format!(
            "representation shard {} does not match its audited batch schedule",
            shard.ordinal
        )));
    }
    Ok(())
}

fn verify_build_identity(root: &Path, manifest: &RepresentationManifest) -> Result<()> {
    let path = root.join(BUILD_IDENTITY_FILE);
    require_file(&path)?;
    if hash_file(&path)? != manifest.build_identity_sha256 {
        return Err(Error::Invariant(
            "representation build identity checksum does not match".to_owned(),
        ));
    }
    let actual: RepresentationBuildIdentity = read_manifest(&path)?;
    let expected = RepresentationBuildIdentity {
        schema_version: BUILD_IDENTITY_SCHEMA_VERSION,
        corpus_data_sha256: manifest.corpus_data_sha256.clone(),
        ordered_event_ids_sha256: manifest.ordered_event_ids_sha256.clone(),
        total_rows: manifest.total_rows,
        descriptor_sha256: manifest.descriptor_sha256.clone(),
        batch_plan: manifest.batch_plan.clone(),
        index_manifest_sha256: manifest.index_manifest_sha256.clone(),
    };
    if actual != expected {
        return Err(Error::Invariant(
            "representation build identity does not match its manifest".to_owned(),
        ));
    }
    Ok(())
}

#[allow(clippy::too_many_arguments)]
fn validate_manifest_identity(
    manifest: &RepresentationManifest,
    corpus_data_sha256: &str,
    ordered_sha256: &str,
    total_rows: u64,
    descriptor: &RepresentationDescriptor,
    descriptor_sha256: &str,
    batch_plan: &RepresentationBatchPlanIdentity,
    build_identity_sha256: &str,
    index_manifest_sha256: &str,
    index: &ArtifactFile,
) -> Result<()> {
    if manifest.corpus_data_sha256 != corpus_data_sha256
        || manifest.ordered_event_ids_sha256 != ordered_sha256
        || manifest.total_rows != total_rows
        || &manifest.descriptor != descriptor
        || manifest.descriptor_sha256 != descriptor_sha256
        || &manifest.batch_plan != batch_plan
        || manifest.build_identity_sha256 != build_identity_sha256
        || manifest.index_manifest_sha256 != index_manifest_sha256
        || &manifest.event_id_to_row != index
    {
        return Err(Error::Invariant(
            "existing representation belongs to different inputs or settings".to_owned(),
        ));
    }
    Ok(())
}

fn existing_manifest(root: &Path) -> Result<Option<RepresentationManifest>> {
    let path = root.join(MANIFEST_FILE);
    if path.exists() {
        read_manifest(&path).map(Some)
    } else {
        Ok(None)
    }
}

fn verification_snapshot(
    corpus_data_path: &Path,
    ordered_path: &Path,
    root: &Path,
    manifest: &RepresentationManifest,
) -> Result<VerificationSnapshot> {
    let vector_shards = manifest
        .shards
        .iter()
        .map(|shard| immutable_file_identity(&root.join(&shard.vectors.file), &shard.vectors.file))
        .collect::<Result<Vec<_>>>()?;
    Ok(VerificationSnapshot {
        corpus_data: immutable_file_identity(corpus_data_path, "corpus/data.mdb")?,
        ordered_event_ids: immutable_file_identity(ordered_path, "ordered-event-ids.bin")?,
        event_id_to_row: immutable_file_identity(
            &root.join(&manifest.event_id_to_row.file),
            &manifest.event_id_to_row.file,
        )?,
        vector_shards,
    })
}

fn immutable_file_identity(path: &Path, file: &str) -> Result<ImmutableFileIdentity> {
    let metadata =
        fs::metadata(path).map_err(|source| io_error("read metadata for", path, source))?;
    if !metadata.is_file() {
        return Err(Error::Invariant(format!(
            "immutable artifact `{}` is not a file",
            path.display()
        )));
    }
    Ok(ImmutableFileIdentity {
        file: file.to_owned(),
        bytes: metadata.len(),
        device: metadata.dev(),
        inode: metadata.ino(),
        modified_seconds: metadata.mtime(),
        modified_nanoseconds: metadata.mtime_nsec(),
        changed_seconds: metadata.ctime(),
        changed_nanoseconds: metadata.ctime_nsec(),
    })
}

fn require_unchanged_file(path: &Path, expected: &ImmutableFileIdentity) -> Result<()> {
    let actual = immutable_file_identity(path, &expected.file)?;
    if &actual != expected {
        return Err(Error::Invariant(format!(
            "immutable artifact `{}` changed after verification; run verify representation again",
            path.display()
        )));
    }
    Ok(())
}

fn validate_verification(
    root: &Path,
    ordered_path: &Path,
    manifest: &RepresentationManifest,
    representation_version: &str,
    verification: &RepresentationVerification,
) -> Result<()> {
    if verification.schema_version != VERIFICATION_SCHEMA_VERSION
        || verification.representation_version != representation_version
        || verification.corpus_data_sha256 != manifest.corpus_data_sha256
        || verification.ordered_event_ids_sha256 != manifest.ordered_event_ids_sha256
        || verification.corpus_data.file != "corpus/data.mdb"
        || verification.ordered_event_ids.file != "ordered-event-ids.bin"
        || verification.event_id_to_row.file != manifest.event_id_to_row.file
        || verification.vector_shards.len() != manifest.shards.len()
        || verification
            .vector_shards
            .iter()
            .zip(&manifest.shards)
            .any(|(identity, shard)| identity.file != shard.vectors.file)
    {
        return Err(Error::Invariant(
            "representation verification receipt is stale; run verify representation again"
                .to_owned(),
        ));
    }
    require_unchanged_file(ordered_path, &verification.ordered_event_ids)?;
    require_unchanged_file(
        &root.join(&manifest.event_id_to_row.file),
        &verification.event_id_to_row,
    )?;
    for (identity, shard) in verification.vector_shards.iter().zip(&manifest.shards) {
        require_unchanged_file(&root.join(&shard.vectors.file), identity)?;
    }
    Ok(())
}

fn publish_verification(root: &Path, verification: &RepresentationVerification) -> Result<()> {
    let temporary = root.join(format!(".{VERIFICATION_FILE}.next"));
    if temporary.exists() {
        fs::remove_file(&temporary).map_err(|source| io_error("remove", &temporary, source))?;
    }
    write_json_new(&temporary, verification)?;
    fs::rename(&temporary, root.join(VERIFICATION_FILE))
        .map_err(|source| io_error("publish", root.join(VERIFICATION_FILE), source))?;
    sync_directory(root)
}

fn map_verified_representation(
    root: &Path,
    ordered_path: &Path,
    manifest: &RepresentationManifest,
) -> Result<MappedRepresentation> {
    let ordered_event_ids = map_read_only(ordered_path)?;
    let event_id_to_row = map_read_only(&root.join(&manifest.event_id_to_row.file))?;
    let shards = manifest
        .shards
        .iter()
        .map(|shard| {
            Ok(MappedRepresentationShard {
                start_row: shard.start_row,
                rows: shard.rows,
                vectors: map_read_only(&root.join(&shard.vectors.file))?,
            })
        })
        .collect::<Result<Vec<_>>>()?;
    Ok(MappedRepresentation {
        ordered_event_ids,
        event_id_to_row,
        shards,
    })
}

fn map_read_only(path: &Path) -> Result<Mmap> {
    let file = File::open(path).map_err(|source| io_error("open", path, source))?;
    // Safety: the file was deeply verified, sealed by immutable stat identity,
    // and is mapped read-only. Callers must reverify after any transfer/change.
    unsafe { MmapOptions::new().map(&file) }.map_err(|source| io_error("map", path, source))
}

fn publish_manifest(root: &Path, manifest: &RepresentationManifest) -> Result<()> {
    let temporary = root.join(format!(".{MANIFEST_FILE}.next"));
    if temporary.exists() {
        fs::remove_file(&temporary).map_err(|source| io_error("remove", &temporary, source))?;
    }
    write_json_new(&temporary, manifest)?;
    fs::rename(&temporary, root.join(MANIFEST_FILE))
        .map_err(|source| io_error("publish", root.join(MANIFEST_FILE), source))?;
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

fn validate_config(
    config: &RepresentationBuildConfig,
    descriptor: &RepresentationDescriptor,
) -> Result<()> {
    if config.token_audit_path.as_os_str().is_empty()
        || config.batch_plan_path.as_os_str().is_empty()
        || config.shard_ordinals.is_empty()
    {
        return Err(Error::Invariant(
            "token audit, batch plan, and requested shard ordinals must be provided".to_owned(),
        ));
    }
    let mut ordinals = config.shard_ordinals.clone();
    ordinals.sort_unstable();
    if ordinals.windows(2).any(|pair| pair[0] == pair[1]) {
        return Err(Error::Invariant(
            "requested shard ordinals contain duplicates".to_owned(),
        ));
    }
    validate_descriptor(descriptor)
}

fn validate_batch_plan_identity(identity: &RepresentationBatchPlanIdentity) -> Result<()> {
    if identity.total_rows == 0
        || identity.shard_rows == 0
        || identity.batch_rows == 0
        || identity.batching_rule != BATCHING_RULE
    {
        return Err(Error::Invariant(
            "representation contains an invalid batch-plan identity".to_owned(),
        ));
    }
    for hash in [
        &identity.manifest_sha256,
        &identity.ordered_event_ids_sha256,
        &identity.token_audit_manifest_sha256,
        &identity.tokenization_contract_sha256,
    ] {
        if hash.len() != 64 || !hash.bytes().all(|byte| byte.is_ascii_hexdigit()) {
            return Err(Error::Invariant(
                "representation batch-plan identity has an invalid SHA-256".to_owned(),
            ));
        }
    }
    Ok(())
}

fn validate_descriptor(descriptor: &RepresentationDescriptor) -> Result<()> {
    let required = [
        descriptor.model_id.as_str(),
        descriptor.model_revision.as_str(),
        descriptor.model_lock_sha256.as_str(),
        descriptor.worker_sha256.as_str(),
        descriptor.dependency_lock_sha256.as_str(),
        descriptor.container_image.as_str(),
        descriptor.torch_version.as_str(),
        descriptor.transformers_version.as_str(),
        descriptor.cuda_version.as_str(),
        descriptor.execution_device.as_str(),
        descriptor.document_input.as_str(),
        descriptor.query_instruction.as_str(),
        descriptor.pooling.as_str(),
        descriptor.normalization.as_str(),
        descriptor.numeric_format.as_str(),
    ];
    if descriptor.dimensions == 0
        || descriptor.model_token_ceiling == 0
        || required.iter().any(|value| value.is_empty())
    {
        return Err(Error::Invariant(
            "representation descriptor has an empty required value".to_owned(),
        ));
    }
    for value in [
        &descriptor.model_lock_sha256,
        &descriptor.worker_sha256,
        &descriptor.dependency_lock_sha256,
    ] {
        if value.len() != 64 || !value.bytes().all(|byte| byte.is_ascii_hexdigit()) {
            return Err(Error::Invariant(
                "representation descriptor has an invalid SHA-256".to_owned(),
            ));
        }
    }
    if descriptor.document_input != "raw-note-content"
        || !matches!(descriptor.execution_device.as_str(), "cpu" | "cuda")
        || descriptor.pooling != "last-token"
        || descriptor.normalization != "l2"
        || descriptor.numeric_format != "f32le"
    {
        return Err(Error::Invariant(
            "representation descriptor does not use the approved input, pooling, normalization, and FP32 format"
                .to_owned(),
        ));
    }
    Ok(())
}

pub fn representation_descriptor_sha256(descriptor: &RepresentationDescriptor) -> Result<String> {
    let bytes = serde_json::to_vec(descriptor).map_err(|source| Error::Manifest {
        operation: "encode",
        path: PathBuf::from("<representation-descriptor>"),
        source,
    })?;
    Ok(hash_bytes(&bytes))
}

fn is_sha256(value: &str) -> bool {
    value.len() == 64 && value.bytes().all(|byte| byte.is_ascii_hexdigit())
}

fn validate_vector(vector: &[f32], dimensions: usize, role: &str) -> Result<()> {
    if vector.len() != dimensions || vector.iter().any(|value| !value.is_finite()) {
        return Err(Error::Encoder {
            operation: "validate vector",
            message: format!("{role} vector has an invalid width or non-finite value"),
        });
    }
    let norm = vector.iter().map(|value| value * value).sum::<f32>().sqrt();
    if (norm - 1.0).abs() > 1e-4 {
        return Err(Error::Encoder {
            operation: "validate vector",
            message: format!("{role} vector is not L2-normalized: {norm}"),
        });
    }
    Ok(())
}

fn decode_vector(bytes: &[u8], dimensions: usize) -> Result<Vec<f32>> {
    if bytes.len() != dimensions * size_of::<f32>() {
        return Err(Error::Invariant(
            "stored vector bytes have the wrong width".to_owned(),
        ));
    }
    let vector = bytes
        .chunks_exact(size_of::<f32>())
        .map(|value| f32::from_le_bytes(value.try_into().expect("f32 width")))
        .collect::<Vec<_>>();
    validate_vector(&vector, dimensions, "stored")?;
    Ok(vector)
}

fn unsealed_lookup_error() -> Error {
    Error::Invariant(
        "representation is not sealed; run verify representation before lookup".to_owned(),
    )
}

fn retain_ranked_row(
    best: &mut BinaryHeap<Reverse<RankedRow>>,
    depth: usize,
    candidate: RankedRow,
) {
    if best.len() < depth {
        best.push(Reverse(candidate));
        return;
    }
    let worst = best.peek().expect("bounded heap is nonempty").0;
    if candidate > worst {
        best.pop();
        best.push(Reverse(candidate));
    }
}

fn rank_cmp(left: (u64, f32), right: (u64, f32)) -> std::cmp::Ordering {
    left.1
        .total_cmp(&right.1)
        .then_with(|| right.0.cmp(&left.0))
}

fn shards_cover_all(shards: &[RepresentationShard], total_rows: u64) -> bool {
    let mut expected = 0_u64;
    for shard in shards {
        if shard.start_row != expected {
            return false;
        }
        expected += shard.rows;
    }
    expected == total_rows
}
