//! Stateless source-specific query interface over the exact meaning map.

use serde::{Deserialize, Serialize};

use crate::canonical::{CanonicalManifest, verify_canonical_rows};
use crate::embedding::{EmbeddingEncoder, EmbeddingManifest};
use crate::event::EventId;
use crate::retrieval::{ExactRetriever, RetrievalCandidate};
use crate::snapshot::{
    CorpusManifest, DamusSnapshot, EligibilityRules, Error, Result, read_manifest, require_file,
    verify_corpus_manifest,
};

const RETRIEVER_ALGORITHM_VERSION: &str = "exact-int8-cosine-v1";
const ALL_CANONICAL_ROWS_SELECTION: &str = "all-stable-canonical-rows-v1";
const EXACT_SEARCH_IMPLEMENTATION: &str = "rust-scalar-sharded-exact-int8-cosine-v1";

/// Artifact identities required to reproduce one oracle response.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct OracleVersions {
    /// SHA-256 of the canonical corpus manifest represented by the matrix.
    pub corpus: String,
    /// Exact retrieval algorithm and embedding-manifest checksum.
    pub retriever: String,
}

impl OracleVersions {
    pub(crate) fn from_embedding(manifest: &EmbeddingManifest, manifest_sha256: &str) -> Self {
        Self {
            corpus: manifest.corpus_stage.as_ref().map_or_else(
                || manifest.canonical_manifest_sha256.clone(),
                |stage| stage.manifest_sha256.clone(),
            ),
            retriever: format!("{RETRIEVER_ALGORITHM_VERSION}:{manifest_sha256}"),
        }
    }
}

/// One source-specific oracle candidate.
#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
pub struct OracleCandidate {
    /// Canonical corpus event ID.
    pub event_id: EventId,
    /// One-based position in this query's exact cosine order.
    pub rank: u64,
    /// Native-INT8 cosine score for this query alone.
    pub cosine_score: f32,
}

/// Explicit inputs and implementation details required to reproduce one response.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct OracleProvenance {
    /// SHA-256 of the compressed source snapshot.
    pub source_snapshot_sha256: String,
    /// Name of the selected immutable stage, or `None` for the full canonical reservoir.
    pub corpus_stage_name: Option<String>,
    /// Exact number of canonical events searched.
    pub corpus_stage_event_count: u64,
    /// Deterministic rule used to select those events.
    pub corpus_stage_selection_rule: String,
    /// Exact rules used to decide which source events were eligible.
    pub eligibility: EligibilityRules,
    /// Versioned rule applied to raw event content before model inference.
    pub content_preprocessing_rule: String,
    /// Maximum model-token count accepted for one content input.
    pub content_length_limit_tokens: u32,
    /// Stable upstream embedding-model identifier.
    pub model_id: String,
    /// Immutable upstream embedding-model revision.
    pub model_revision: String,
    /// Elements searched in each stored embedding.
    pub embedding_dimensions: u32,
    /// On-disk vector and norm representation.
    pub matrix_format: String,
    /// Requested number of source-specific candidates.
    pub candidate_depth: u64,
    /// Versioned exact-scanner implementation used for this response.
    pub exact_search_implementation: String,
}

/// Deterministic evidence returned for exactly one text or note query.
#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
pub struct OracleResponse {
    /// Corpus and retriever identities shared by every candidate.
    pub versions: OracleVersions,
    /// Explicit reproducibility metadata for this exact query.
    pub provenance: OracleProvenance,
    /// Candidates in exact source-specific rank order.
    pub candidates: Vec<OracleCandidate>,
}

/// The stateless boundary available to the private experiment runner.
pub trait Oracle {
    /// Encode one arbitrary string and search the complete current matrix.
    fn search_text(&mut self, text: &str, candidate_depth: usize) -> Result<OracleResponse>;

    /// Load one stored note vector and search without returning its canonical source.
    fn similar_notes(&mut self, note_id: EventId, candidate_depth: usize)
    -> Result<OracleResponse>;
}

/// Offline implementation backed by one verified matrix and its matching encoder.
pub struct OfflineOracle<E> {
    retriever: ExactRetriever,
    encoder: E,
    versions: OracleVersions,
    identity: OracleIdentity,
}

#[derive(Clone, Debug)]
struct OracleIdentity {
    source_snapshot_sha256: String,
    corpus_stage_name: Option<String>,
    corpus_stage_event_count: u64,
    corpus_stage_selection_rule: String,
    eligibility: EligibilityRules,
    content_preprocessing_rule: String,
    content_length_limit_tokens: u32,
    model_id: String,
    model_revision: String,
    embedding_dimensions: u32,
    matrix_format: String,
}

impl<E> OfflineOracle<E>
where
    E: EmbeddingEncoder,
{
    /// Open a verified matrix and require an exactly matching text encoder.
    pub fn open(pipeline: &DamusSnapshot, artifact_name: &str, encoder: E) -> Result<Self> {
        let retriever = ExactRetriever::open(pipeline, artifact_name)?;
        if retriever.manifest().encoder != *encoder.descriptor() {
            return Err(Error::Invariant(
                "query encoder identity differs from the embedding artifact".to_owned(),
            ));
        }
        let versions =
            OracleVersions::from_embedding(retriever.manifest(), retriever.manifest_sha256());
        let identity = OracleIdentity::from_verified_artifacts(pipeline, retriever.manifest())?;
        Ok(Self {
            retriever,
            encoder,
            versions,
            identity,
        })
    }

    /// Return the exact identities attached to every response.
    pub fn versions(&self) -> &OracleVersions {
        &self.versions
    }

    fn response(
        &self,
        candidates: Vec<RetrievalCandidate>,
        candidate_depth: usize,
    ) -> Result<OracleResponse> {
        let candidates = candidates
            .into_iter()
            .enumerate()
            .map(|(index, candidate)| {
                Ok(OracleCandidate {
                    event_id: EventId::from(candidate.event_id),
                    rank: u64::try_from(index)
                        .ok()
                        .and_then(|rank| rank.checked_add(1))
                        .ok_or_else(|| {
                            Error::Invariant("oracle candidate rank overflowed u64".to_owned())
                        })?,
                    cosine_score: candidate.cosine_score,
                })
            })
            .collect::<Result<Vec<_>>>()?;
        Ok(OracleResponse {
            versions: self.versions.clone(),
            provenance: self.identity.for_depth(candidate_depth)?,
            candidates,
        })
    }
}

impl<E> Oracle for OfflineOracle<E>
where
    E: EmbeddingEncoder,
{
    fn search_text(&mut self, text: &str, candidate_depth: usize) -> Result<OracleResponse> {
        require_positive_depth(candidate_depth)?;
        let vector = self.encoder.encode(&[text])?;
        let expected = usize::try_from(self.retriever.manifest().encoder.dimensions)
            .map_err(|_| Error::Invariant("encoder dimensions do not fit usize".to_owned()))?;
        if vector.len() != expected {
            return Err(Error::Invariant(format!(
                "query encoder returned {} elements but expected {expected}",
                vector.len()
            )));
        }
        self.response(
            self.retriever.search(&vector, candidate_depth, None)?,
            candidate_depth,
        )
    }

    fn similar_notes(
        &mut self,
        note_id: EventId,
        candidate_depth: usize,
    ) -> Result<OracleResponse> {
        require_positive_depth(candidate_depth)?;
        let Some((canonical_id, vector)) = self.retriever.canonical_vector(note_id.into_bytes())?
        else {
            return Err(Error::EventNotFound(note_id.to_string()));
        };
        self.response(
            self.retriever
                .search(&vector, candidate_depth, Some(canonical_id))?,
            candidate_depth,
        )
    }
}

impl OracleIdentity {
    fn from_verified_artifacts(
        pipeline: &DamusSnapshot,
        embedding: &EmbeddingManifest,
    ) -> Result<Self> {
        let corpus_path = pipeline.layout().corpus_manifest();
        let canonical_path = pipeline.layout().canonical_manifest();
        require_file(&corpus_path)?;
        require_file(&canonical_path)?;
        let corpus: CorpusManifest = read_manifest(&corpus_path)?;
        verify_corpus_manifest(&corpus)?;
        let canonical: CanonicalManifest = read_manifest(&canonical_path)?;
        verify_canonical_rows(&pipeline.layout().canonical_dir(), &canonical)?;
        if corpus.source_snapshot_sha256 != canonical.source_snapshot_sha256
            || corpus.eligibility != canonical.eligibility
            || corpus.eligible_events != canonical.counts.eligible_events
            || embedding.source_snapshot_sha256 != corpus.source_snapshot_sha256
        {
            return Err(Error::Invariant(
                "oracle artifacts contain incompatible snapshot or eligibility provenance"
                    .to_owned(),
            ));
        }

        let (corpus_stage_name, corpus_stage_selection_rule) =
            embedding.corpus_stage.as_ref().map_or_else(
                || (None, ALL_CANONICAL_ROWS_SELECTION.to_owned()),
                |stage| (Some(stage.name.clone()), stage.selection_rule.clone()),
            );
        Ok(Self {
            source_snapshot_sha256: embedding.source_snapshot_sha256.clone(),
            corpus_stage_name,
            corpus_stage_event_count: embedding.total_rows,
            corpus_stage_selection_rule,
            eligibility: corpus.eligibility,
            content_preprocessing_rule: embedding.encoder.input_rule.clone(),
            content_length_limit_tokens: embedding.encoder.max_tokens,
            model_id: embedding.encoder.model_id.clone(),
            model_revision: embedding.encoder.model_revision.clone(),
            embedding_dimensions: embedding.encoder.dimensions,
            matrix_format: embedding.matrix_format.clone(),
        })
    }

    fn for_depth(&self, candidate_depth: usize) -> Result<OracleProvenance> {
        Ok(OracleProvenance {
            source_snapshot_sha256: self.source_snapshot_sha256.clone(),
            corpus_stage_name: self.corpus_stage_name.clone(),
            corpus_stage_event_count: self.corpus_stage_event_count,
            corpus_stage_selection_rule: self.corpus_stage_selection_rule.clone(),
            eligibility: self.eligibility.clone(),
            content_preprocessing_rule: self.content_preprocessing_rule.clone(),
            content_length_limit_tokens: self.content_length_limit_tokens,
            model_id: self.model_id.clone(),
            model_revision: self.model_revision.clone(),
            embedding_dimensions: self.embedding_dimensions,
            matrix_format: self.matrix_format.clone(),
            candidate_depth: u64::try_from(candidate_depth).map_err(|_| {
                Error::Invariant("candidate depth does not fit reproducibility metadata".to_owned())
            })?,
            exact_search_implementation: EXACT_SEARCH_IMPLEMENTATION.to_owned(),
        })
    }
}

pub(crate) fn verified_oracle_provenance(
    pipeline: &DamusSnapshot,
    embedding: &EmbeddingManifest,
    candidate_depth: usize,
) -> Result<OracleProvenance> {
    OracleIdentity::from_verified_artifacts(pipeline, embedding)?.for_depth(candidate_depth)
}

fn require_positive_depth(candidate_depth: usize) -> Result<()> {
    if candidate_depth == 0 {
        Err(Error::InvalidQuery(
            "candidate depth must be positive".to_owned(),
        ))
    } else {
        Ok(())
    }
}
