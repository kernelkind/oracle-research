//! Exact cosine retrieval over immutable native-INT8 embedding shards.

use std::cmp::{Ordering, Reverse};
use std::collections::BinaryHeap;
use std::fs::File;
use std::io::{BufReader, Read, Seek, SeekFrom};
use std::path::{Path, PathBuf};

use crate::artifact::{hash_file, verify_fixed_artifact};
use crate::canonical::CanonicalManifest;
use crate::embedding::{EmbeddingManifest, EmbeddingShardManifest};
use crate::ordered_embedding::{OrderedEmbeddingManifest, open_ordered_embedding_artifact};
use crate::snapshot::{DamusSnapshot, Error, Result, io_error, read_manifest};

const EVENT_ID_BYTES: usize = 32;
const ALIAS_RECORD_BYTES: usize = EVENT_ID_BYTES * 2;
const NORM_BYTES: usize = size_of::<f32>();

/// A canonical corpus event returned by exact dense retrieval.
#[derive(Clone, Debug, PartialEq)]
pub struct RetrievalCandidate {
    /// Canonical Nostr event ID.
    pub event_id: [u8; EVENT_ID_BYTES],
    /// Native-INT8 cosine score for the source-specific query.
    pub cosine_score: f32,
}

/// Verified exact scanner over one immutable embedding artifact.
pub struct ExactRetriever {
    artifact_root: PathBuf,
    aliases_path: PathBuf,
    alias_records: u64,
    manifest_sha256: String,
    manifest: EmbeddingManifest,
}

/// Verified exact scanner over an ordered final-corpus embedding artifact.
pub struct OrderedExactRetriever {
    artifact_root: PathBuf,
    manifest_sha256: String,
    manifest: OrderedEmbeddingManifest,
}

impl ExactRetriever {
    /// Open the artifact and verify every manifest, checksum, and row mapping.
    pub fn open(pipeline: &DamusSnapshot, artifact_name: &str) -> Result<Self> {
        let manifest = pipeline.open_embedding_artifact(artifact_name)?;
        let layout = pipeline.layout();
        let canonical_root = layout
            .canonical_manifest()
            .parent()
            .expect("canonical manifest has a parent")
            .to_owned();
        let canonical: CanonicalManifest = read_manifest(&layout.canonical_manifest())?;
        verify_fixed_artifact(
            &canonical_root,
            &canonical.aliases,
            "aliases.bin",
            ALIAS_RECORD_BYTES,
            canonical.counts.eligible_events,
        )?;
        let artifact_root = layout.embedding_dir(artifact_name);
        let manifest_sha256 = hash_file(&artifact_root.join("manifest.json"))?;
        Ok(Self {
            artifact_root,
            aliases_path: layout.canonical_aliases(),
            alias_records: canonical.counts.eligible_events,
            manifest_sha256,
            manifest,
        })
    }

    /// Return the verified embedding manifest used by this scanner.
    pub fn manifest(&self) -> &EmbeddingManifest {
        &self.manifest
    }

    /// Return the checksum of the exact embedding manifest being searched.
    pub fn manifest_sha256(&self) -> &str {
        &self.manifest_sha256
    }

    /// Scan every row, retaining an exact global top set across all shards.
    pub fn search(
        &self,
        query: &[i8],
        candidate_depth: usize,
        excluded_event: Option<[u8; EVENT_ID_BYTES]>,
    ) -> Result<Vec<RetrievalCandidate>> {
        let dimensions = self.dimensions()?;
        search_matrix(
            &self.artifact_root,
            &self.manifest.shards,
            self.manifest.total_rows,
            dimensions,
            query,
            candidate_depth,
            excluded_event,
        )
    }

    pub(crate) fn canonical_vector(
        &self,
        event_id: [u8; EVENT_ID_BYTES],
    ) -> Result<Option<([u8; EVENT_ID_BYTES], Vec<i8>)>> {
        let Some(canonical_id) = self.resolve_alias(event_id)? else {
            return Ok(None);
        };
        stored_vector(
            &self.artifact_root,
            &self.manifest.shards,
            self.dimensions()?,
            canonical_id,
        )
        .map(|vector| vector.map(|vector| (canonical_id, vector)))
    }

    fn resolve_alias(
        &self,
        event_id: [u8; EVENT_ID_BYTES],
    ) -> Result<Option<[u8; EVENT_ID_BYTES]>> {
        let mut aliases = open_file(&self.aliases_path)?;
        let mut low = 0_u64;
        let mut high = self.alias_records;
        let mut record = [0_u8; ALIAS_RECORD_BYTES];
        while low < high {
            let middle = low + (high - low) / 2;
            aliases
                .seek(SeekFrom::Start(middle * ALIAS_RECORD_BYTES as u64))
                .map_err(|source| io_error("seek", &self.aliases_path, source))?;
            aliases
                .read_exact(&mut record)
                .map_err(|source| io_error("read", &self.aliases_path, source))?;
            match record[..EVENT_ID_BYTES].cmp(&event_id) {
                Ordering::Less => low = middle + 1,
                Ordering::Greater => high = middle,
                Ordering::Equal => {
                    return Ok(Some(
                        record[EVENT_ID_BYTES..]
                            .try_into()
                            .expect("canonical event ID width"),
                    ));
                }
            }
        }
        Ok(None)
    }

    fn dimensions(&self) -> Result<usize> {
        usize::try_from(self.manifest.encoder.dimensions)
            .map_err(|_| Error::Invariant("encoder dimensions do not fit usize".to_owned()))
    }
}

impl OrderedExactRetriever {
    /// Open and verify the ordered source, final corpus, and every matrix shard.
    pub fn open(
        corpus_path: impl AsRef<Path>,
        ordered_event_ids_path: impl AsRef<Path>,
        artifact_path: impl AsRef<Path>,
    ) -> Result<Self> {
        let artifact_root = artifact_path.as_ref().to_owned();
        let manifest =
            open_ordered_embedding_artifact(corpus_path, ordered_event_ids_path, &artifact_root)?;
        let manifest_sha256 = hash_file(&artifact_root.join("manifest.json"))?;
        Ok(Self {
            artifact_root,
            manifest_sha256,
            manifest,
        })
    }

    /// Return the verified ordered embedding manifest used by this scanner.
    pub fn manifest(&self) -> &OrderedEmbeddingManifest {
        &self.manifest
    }

    /// Return the checksum of the exact ordered embedding manifest.
    pub fn manifest_sha256(&self) -> &str {
        &self.manifest_sha256
    }

    /// Scan every ordered row, retaining the exact global top set.
    pub fn search(
        &self,
        query: &[i8],
        candidate_depth: usize,
        excluded_event: Option<[u8; EVENT_ID_BYTES]>,
    ) -> Result<Vec<RetrievalCandidate>> {
        search_matrix(
            &self.artifact_root,
            &self.manifest.shards,
            self.manifest.total_rows,
            self.dimensions()?,
            query,
            candidate_depth,
            excluded_event,
        )
    }

    /// Load the stored vector for an event in this exact ordered prefix.
    pub(crate) fn event_vector(&self, event_id: [u8; EVENT_ID_BYTES]) -> Result<Option<Vec<i8>>> {
        stored_vector(
            &self.artifact_root,
            &self.manifest.shards,
            self.dimensions()?,
            event_id,
        )
    }

    fn dimensions(&self) -> Result<usize> {
        usize::try_from(self.manifest.encoder.dimensions)
            .map_err(|_| Error::Invariant("encoder dimensions do not fit usize".to_owned()))
    }
}

#[allow(clippy::too_many_arguments)]
fn search_matrix(
    artifact_root: &Path,
    shards: &[EmbeddingShardManifest],
    total_rows: u64,
    dimensions: usize,
    query: &[i8],
    candidate_depth: usize,
    excluded_event: Option<[u8; EVENT_ID_BYTES]>,
) -> Result<Vec<RetrievalCandidate>> {
    if candidate_depth == 0 {
        return Err(Error::InvalidQuery(
            "candidate depth must be positive".to_owned(),
        ));
    }
    if query.len() != dimensions {
        return Err(Error::InvalidQuery(format!(
            "query has {} dimensions but the corpus has {dimensions}",
            query.len()
        )));
    }
    let query_norm = vector_norm(query)?;
    let capacity = candidate_depth.min(usize::try_from(total_rows).unwrap_or(usize::MAX));
    let mut global = BinaryHeap::with_capacity(capacity);
    for shard in shards {
        let local = search_shard(
            artifact_root,
            shard,
            query,
            query_norm,
            candidate_depth,
            excluded_event,
        )?;
        for candidate in local {
            retain_best(&mut global, candidate, capacity);
        }
    }
    let mut ordered = global
        .into_iter()
        .map(|Reverse(candidate)| candidate)
        .collect::<Vec<_>>();
    ordered.sort_unstable_by(|left, right| right.cmp(left));
    Ok(ordered
        .into_iter()
        .map(|candidate| candidate.candidate)
        .collect())
}

fn search_shard(
    artifact_root: &Path,
    shard: &EmbeddingShardManifest,
    query: &[i8],
    query_norm: f32,
    candidate_depth: usize,
    excluded_event: Option<[u8; EVENT_ID_BYTES]>,
) -> Result<Vec<ScoredCandidate>> {
    let vectors_path = artifact_root.join(&shard.vectors.file);
    let norms_path = artifact_root.join(&shard.norms.file);
    let row_ids_path = artifact_root.join(&shard.row_ids.file);
    let mut vectors = BufReader::new(open_file(&vectors_path)?);
    let mut norms = BufReader::new(open_file(&norms_path)?);
    let mut row_ids = BufReader::new(open_file(&row_ids_path)?);
    let mut vector = vec![0_u8; query.len()];
    let mut norm = [0_u8; NORM_BYTES];
    let mut event_id = [0_u8; EVENT_ID_BYTES];
    let capacity = candidate_depth.min(usize::try_from(shard.rows).unwrap_or(usize::MAX));
    let mut best = BinaryHeap::with_capacity(capacity);

    for row in 0..shard.rows {
        vectors
            .read_exact(&mut vector)
            .map_err(|source| io_error("read", &vectors_path, source))?;
        norms
            .read_exact(&mut norm)
            .map_err(|source| io_error("read", &norms_path, source))?;
        row_ids
            .read_exact(&mut event_id)
            .map_err(|source| io_error("read", &row_ids_path, source))?;
        if excluded_event == Some(event_id) {
            continue;
        }
        let stored_norm = f32::from_le_bytes(norm);
        if !stored_norm.is_finite() || stored_norm <= 0.0 {
            return Err(Error::Invariant(format!(
                "embedding shard {} row {row} has invalid cosine norm {stored_norm}",
                shard.ordinal
            )));
        }
        let dot = query
            .iter()
            .zip(&vector)
            .try_fold(0_i64, |sum, (left, right)| {
                sum.checked_add(i64::from(*left) * i64::from(*right as i8))
            })
            .ok_or_else(|| Error::Invariant("INT8 dot product overflowed i64".to_owned()))?;
        let cosine_score = dot as f32 / (query_norm * stored_norm);
        if !cosine_score.is_finite() {
            return Err(Error::Invariant(format!(
                "embedding shard {} row {row} produced non-finite cosine score",
                shard.ordinal
            )));
        }
        retain_best(
            &mut best,
            ScoredCandidate {
                candidate: RetrievalCandidate {
                    event_id,
                    cosine_score,
                },
            },
            capacity,
        );
    }
    Ok(best
        .into_iter()
        .map(|Reverse(candidate)| candidate)
        .collect())
}

fn stored_vector(
    artifact_root: &Path,
    shards: &[EmbeddingShardManifest],
    dimensions: usize,
    event_id: [u8; EVENT_ID_BYTES],
) -> Result<Option<Vec<i8>>> {
    for shard in shards {
        let row_ids_path = artifact_root.join(&shard.row_ids.file);
        let mut row_ids = BufReader::new(open_file(&row_ids_path)?);
        let mut row_id = [0_u8; EVENT_ID_BYTES];
        for row in 0..shard.rows {
            row_ids
                .read_exact(&mut row_id)
                .map_err(|source| io_error("read", &row_ids_path, source))?;
            if row_id == event_id {
                let vectors_path = artifact_root.join(&shard.vectors.file);
                let mut vectors = open_file(&vectors_path)?;
                let offset = row
                    .checked_mul(u64::try_from(dimensions).expect("dimensions fit u64"))
                    .ok_or_else(|| {
                        Error::Invariant("vector byte offset overflowed u64".to_owned())
                    })?;
                vectors
                    .seek(SeekFrom::Start(offset))
                    .map_err(|source| io_error("seek", &vectors_path, source))?;
                let mut bytes = vec![0_u8; dimensions];
                vectors
                    .read_exact(&mut bytes)
                    .map_err(|source| io_error("read", &vectors_path, source))?;
                return Ok(Some(bytes.into_iter().map(|byte| byte as i8).collect()));
            }
        }
    }
    Ok(None)
}

#[derive(Clone, Debug)]
struct ScoredCandidate {
    candidate: RetrievalCandidate,
}

impl PartialEq for ScoredCandidate {
    fn eq(&self, other: &Self) -> bool {
        self.cmp(other) == Ordering::Equal
    }
}

impl Eq for ScoredCandidate {}

impl PartialOrd for ScoredCandidate {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

impl Ord for ScoredCandidate {
    fn cmp(&self, other: &Self) -> Ordering {
        self.candidate
            .cosine_score
            .total_cmp(&other.candidate.cosine_score)
            .then_with(|| other.candidate.event_id.cmp(&self.candidate.event_id))
    }
}

fn retain_best(
    heap: &mut BinaryHeap<Reverse<ScoredCandidate>>,
    candidate: ScoredCandidate,
    capacity: usize,
) {
    if capacity == 0 {
        return;
    }
    if heap.len() < capacity {
        heap.push(Reverse(candidate));
    } else if heap.peek().is_some_and(|worst| candidate > worst.0) {
        heap.pop();
        heap.push(Reverse(candidate));
    }
}

fn vector_norm(vector: &[i8]) -> Result<f32> {
    let squared = vector.iter().try_fold(0_u64, |sum, value| {
        let value = i64::from(*value);
        sum.checked_add(u64::try_from(value * value).expect("square is nonnegative"))
    });
    let norm = (squared
        .ok_or_else(|| Error::Invariant("query vector squared norm overflowed u64".to_owned()))?
        as f32)
        .sqrt();
    if norm == 0.0 {
        return Err(Error::InvalidQuery(
            "query vector must not be zero".to_owned(),
        ));
    }
    Ok(norm)
}

fn open_file(path: &Path) -> Result<File> {
    File::open(path).map_err(|source| io_error("open", path, source))
}
