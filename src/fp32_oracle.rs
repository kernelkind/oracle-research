//! Offline Oracle operations over the approved FP32 public representation.

use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::time::{Duration, Instant};

use nostrdb::{Ndb, Transaction};

use crate::representation::{
    EventId, FP32_SCAN_BLOCK_ROWS, RepresentationEncoder, RepresentationStore,
    open_verified_representation,
};
use crate::snapshot::{Error, Result, Validation, ndb_error, open_existing_ndb, require_file};

#[derive(Clone, Debug, serde::Deserialize, PartialEq, serde::Serialize)]
pub struct Fp32Candidate {
    pub event_id: EventId,
    pub rank: usize,
    pub cosine_score: f32,
}

#[derive(Clone, Debug, serde::Deserialize, PartialEq, serde::Serialize)]
pub struct SimilarNotesResponse {
    pub representation_version: String,
    pub represented_rows: u64,
    pub total_rows: u64,
    pub complete: bool,
    pub candidates: Vec<Fp32Candidate>,
}

#[derive(Clone, Copy, Debug, serde::Deserialize, Eq, PartialEq, serde::Serialize)]
pub struct SimilarNotesRequest {
    pub note_id: EventId,
    pub candidate_depth: usize,
}

#[derive(Clone, Debug, serde::Deserialize, Eq, PartialEq, serde::Serialize)]
pub struct SimilarNotesWaveMetrics {
    pub source_loading_ns: u64,
    pub query_encoding_ns: u64,
    pub matrix_scan_ns: u64,
    pub result_merge_ns: u64,
    pub encoded_queries: u64,
    pub cache_hits: u64,
    pub matrix_passes: u64,
    pub scanned_rows: u64,
    pub scan_block_rows: u64,
}

#[derive(Clone, Debug, PartialEq)]
pub struct SimilarNotesWaveResponse {
    pub responses: Vec<SimilarNotesResponse>,
    pub metrics: SimilarNotesWaveMetrics,
}

#[derive(Clone, Debug, serde::Deserialize, PartialEq, serde::Serialize)]
pub struct StoredNoteVector {
    pub event_id: EventId,
    pub vector: Vec<f32>,
}

#[derive(Clone, Debug, serde::Deserialize, PartialEq, serde::Serialize)]
pub struct VectorsForNotesResponse {
    pub representation_version: String,
    pub represented_rows: u64,
    pub total_rows: u64,
    pub complete: bool,
    pub lookup_elapsed_ns: u64,
    pub vectors: Vec<StoredNoteVector>,
}

#[derive(Clone, Debug, Eq, Hash, PartialEq)]
struct SimilarNotesCacheKey {
    representation_version: String,
    note_id: EventId,
    candidate_depth: usize,
}

/// Return exact stored candidate-role vectors without starting query inference.
pub fn vectors_for_notes(
    ordered_event_ids_path: impl AsRef<Path>,
    representation_path: impl AsRef<Path>,
    note_ids: &[EventId],
    representation_version: &str,
) -> Result<VectorsForNotesResponse> {
    let representation = open_verified_representation(ordered_event_ids_path, representation_path)?;
    read_vectors(&representation, note_ids, representation_version)
}

/// The Oracle sees only public note IDs and text. Ratings remain outside this type.
pub struct Fp32OfflineOracle<E> {
    corpus_path: PathBuf,
    ordered_path: PathBuf,
    corpus: Ndb,
    representation: RepresentationStore,
    encoder: E,
    similar_notes_cache: HashMap<SimilarNotesCacheKey, SimilarNotesResponse>,
}

impl<E: RepresentationEncoder> Fp32OfflineOracle<E> {
    pub fn open(
        corpus_path: impl AsRef<Path>,
        ordered_event_ids_path: impl AsRef<Path>,
        representation_path: impl AsRef<Path>,
        encoder: E,
    ) -> Result<Self> {
        let corpus_path = corpus_path.as_ref().to_owned();
        let ordered_path = ordered_event_ids_path.as_ref().to_owned();
        let representation = open_verified_representation(&ordered_path, representation_path)?;
        let mut query_descriptor = encoder.descriptor().clone();
        query_descriptor.execution_device = representation
            .manifest()
            .descriptor
            .execution_device
            .clone();
        if representation.manifest().descriptor != query_descriptor {
            return Err(Error::Invariant(
                "query encoder does not match the stored semantic and runtime contract".to_owned(),
            ));
        }
        let corpus_data = corpus_path.join("data.mdb");
        require_file(&corpus_data)?;
        representation.require_verified_corpus(&corpus_data)?;
        let corpus = open_existing_ndb(&corpus_path, Validation::TrustedSource)?;
        representation.require_verified_corpus(&corpus_data)?;
        Ok(Self {
            corpus_path,
            ordered_path,
            corpus,
            representation,
            encoder,
            similar_notes_cache: HashMap::new(),
        })
    }

    pub fn representation_version(&self) -> &str {
        self.representation.representation_version()
    }

    /// Lazily query-encode one public note and scan every completed candidate shard.
    pub fn similar_notes(
        &mut self,
        note_id: EventId,
        candidate_depth: usize,
        representation_version: &str,
    ) -> Result<SimilarNotesResponse> {
        let mut wave = self.similar_notes_wave(
            &[SimilarNotesRequest {
                note_id,
                candidate_depth,
            }],
            representation_version,
        )?;
        wave.responses
            .pop()
            .ok_or_else(|| Error::Invariant("single-note wave returned no response".to_owned()))
    }

    /// Co-schedule independent logical requests into one query batch and matrix pass.
    pub fn similar_notes_wave(
        &mut self,
        requests: &[SimilarNotesRequest],
        representation_version: &str,
    ) -> Result<SimilarNotesWaveResponse> {
        self.representation
            .require_version(representation_version)?;
        if requests.is_empty() {
            return Err(Error::InvalidQuery(
                "similar_notes requires at least one source note".to_owned(),
            ));
        }

        struct Pending {
            output_index: usize,
            key: SimilarNotesCacheKey,
            source_row: u64,
            content: String,
            candidate_depth: usize,
        }

        let loading_started = Instant::now();
        let mut responses = vec![None; requests.len()];
        let mut pending = Vec::new();
        let transaction = Transaction::new(&self.corpus)
            .map_err(|source| ndb_error("open transaction on", &self.corpus_path, source))?;
        let mut cache_hits = 0_u64;
        for (output_index, request) in requests.iter().enumerate() {
            if request.candidate_depth == 0 {
                return Err(Error::InvalidQuery(
                    "candidate depth must be positive".to_owned(),
                ));
            }
            let key = SimilarNotesCacheKey {
                representation_version: representation_version.to_owned(),
                note_id: request.note_id,
                candidate_depth: request.candidate_depth,
            };
            if let Some(response) = self.similar_notes_cache.get(&key) {
                responses[output_index] = Some(response.clone());
                cache_hits += 1;
                continue;
            }
            let source_row = self
                .representation
                .row_for_event(request.note_id)?
                .ok_or_else(|| Error::EventNotFound(hex_id(request.note_id)))?;
            let note = self
                .corpus
                .get_note_by_id(&transaction, &request.note_id)
                .map_err(|source| ndb_error("load event from", &self.corpus_path, source))?;
            pending.push(Pending {
                output_index,
                key,
                source_row,
                content: note.content().to_owned(),
                candidate_depth: request.candidate_depth,
            });
        }
        drop(transaction);
        let source_loading_ns = duration_ns(loading_started.elapsed());

        let encoding_started = Instant::now();
        let query_values = if pending.is_empty() {
            Vec::new()
        } else {
            let texts = pending
                .iter()
                .map(|request| request.content.as_str())
                .collect::<Vec<_>>();
            self.encoder.encode_queries(&texts)?
        };
        let dimensions = usize::try_from(self.representation.manifest().descriptor.dimensions)
            .map_err(|_| Error::Invariant("dimensions do not fit usize".to_owned()))?;
        let expected_values = pending
            .len()
            .checked_mul(dimensions)
            .ok_or_else(|| Error::Invariant("query batch width overflowed".to_owned()))?;
        if query_values.len() != expected_values {
            return Err(Error::Encoder {
                operation: "encode query",
                message: format!(
                    "query encoder returned {} values instead of {expected_values}",
                    query_values.len()
                ),
            });
        }
        let queries = query_values.chunks_exact(dimensions).collect::<Vec<_>>();
        let query_encoding_ns = duration_ns(encoding_started.elapsed());

        let scan_started = Instant::now();
        let ranked = if pending.is_empty() {
            Vec::new()
        } else {
            self.representation.search_many(
                &queries,
                &pending
                    .iter()
                    .map(|request| request.candidate_depth)
                    .collect::<Vec<_>>(),
                &pending
                    .iter()
                    .map(|request| Some(request.source_row))
                    .collect::<Vec<_>>(),
            )?
        };
        let matrix_scan_ns = duration_ns(scan_started.elapsed());

        let merge_started = Instant::now();
        for (request, ranked) in pending.iter().zip(ranked) {
            let candidates = ranked
                .into_iter()
                .enumerate()
                .map(|(index, (row, cosine_score))| {
                    self.representation
                        .event_for_row(&self.ordered_path, row)
                        .map(|event_id| Fp32Candidate {
                            event_id,
                            rank: index + 1,
                            cosine_score,
                        })
                })
                .collect::<Result<Vec<_>>>()?;
            let response = SimilarNotesResponse {
                representation_version: self.representation.representation_version().to_owned(),
                represented_rows: self.representation.manifest().completed_rows,
                total_rows: self.representation.manifest().total_rows,
                complete: self.representation.manifest().complete,
                candidates,
            };
            self.similar_notes_cache
                .insert(request.key.clone(), response.clone());
            responses[request.output_index] = Some(response);
        }
        let responses = responses
            .into_iter()
            .map(|response| {
                response.ok_or_else(|| {
                    Error::Invariant("similar-note wave lost a logical response".to_owned())
                })
            })
            .collect::<Result<Vec<_>>>()?;
        let result_merge_ns = duration_ns(merge_started.elapsed());
        let encoded_queries = u64::try_from(pending.len())
            .map_err(|_| Error::Invariant("query count does not fit u64".to_owned()))?;
        Ok(SimilarNotesWaveResponse {
            responses,
            metrics: SimilarNotesWaveMetrics {
                source_loading_ns,
                query_encoding_ns,
                matrix_scan_ns,
                result_merge_ns,
                encoded_queries,
                cache_hits,
                matrix_passes: u64::from(!pending.is_empty()),
                scanned_rows: if pending.is_empty() {
                    0
                } else {
                    self.representation.manifest().completed_rows
                },
                scan_block_rows: FP32_SCAN_BLOCK_ROWS as u64,
            },
        })
    }

    /// Return exact stored candidate-role vectors in the caller's requested order.
    pub fn vectors_for_notes(
        &self,
        note_ids: &[EventId],
        representation_version: &str,
    ) -> Result<VectorsForNotesResponse> {
        read_vectors(&self.representation, note_ids, representation_version)
    }
}

fn read_vectors(
    representation: &RepresentationStore,
    note_ids: &[EventId],
    representation_version: &str,
) -> Result<VectorsForNotesResponse> {
    let started = Instant::now();
    representation.require_version(representation_version)?;
    if note_ids.is_empty() {
        return Err(Error::InvalidQuery(
            "vectors_for_notes requires at least one event ID".to_owned(),
        ));
    }
    let vectors = note_ids
        .iter()
        .map(|event_id| {
            let row = representation
                .row_for_event(*event_id)?
                .ok_or_else(|| Error::EventNotFound(hex_id(*event_id)))?;
            let vector = representation.vector_for_row(row)?;
            Ok(StoredNoteVector {
                event_id: *event_id,
                vector,
            })
        })
        .collect::<Result<Vec<_>>>()?;
    Ok(VectorsForNotesResponse {
        representation_version: representation.representation_version().to_owned(),
        represented_rows: representation.manifest().completed_rows,
        total_rows: representation.manifest().total_rows,
        complete: representation.manifest().complete,
        lookup_elapsed_ns: duration_ns(started.elapsed()),
        vectors,
    })
}

fn duration_ns(duration: Duration) -> u64 {
    u64::try_from(duration.as_nanos()).unwrap_or(u64::MAX)
}

fn hex_id(id: EventId) -> String {
    id.iter().map(|byte| format!("{byte:02x}")).collect()
}
