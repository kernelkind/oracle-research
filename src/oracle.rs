//! Stateless source-specific query interface over the exact meaning map.

use serde::{Deserialize, Serialize};

use crate::embedding::EmbeddingEncoder;
use crate::event::EventId;
use crate::retrieval::{ExactRetriever, RetrievalCandidate};
use crate::snapshot::{DamusSnapshot, Error, Result};

const RETRIEVER_ALGORITHM_VERSION: &str = "exact-int8-cosine-v1";

/// Artifact identities required to reproduce one oracle response.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct OracleVersions {
    /// SHA-256 of the canonical corpus manifest represented by the matrix.
    pub corpus: String,
    /// Exact retrieval algorithm and embedding-manifest checksum.
    pub retriever: String,
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

/// Deterministic evidence returned for exactly one text or note query.
#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
pub struct OracleResponse {
    /// Corpus and retriever identities shared by every candidate.
    pub versions: OracleVersions,
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
        let versions = OracleVersions {
            corpus: retriever.manifest().canonical_manifest_sha256.clone(),
            retriever: format!(
                "{RETRIEVER_ALGORITHM_VERSION}:{}",
                retriever.manifest_sha256()
            ),
        };
        Ok(Self {
            retriever,
            encoder,
            versions,
        })
    }

    /// Return the exact identities attached to every response.
    pub fn versions(&self) -> &OracleVersions {
        &self.versions
    }

    fn response(&self, candidates: Vec<RetrievalCandidate>) -> Result<OracleResponse> {
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
        self.response(self.retriever.search(&vector, candidate_depth, None)?)
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
        )
    }
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
