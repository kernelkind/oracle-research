//! Deterministic, non-evaluative local inputs for exercising the production Phase 3 workflow.

use std::collections::BTreeMap;
use std::f32::consts::TAU;
use std::fs;
use std::path::Path;
use std::thread;
use std::time::{Duration, Instant};

use nostrdb::NoteBuilder;

use crate::adaptive_learning_runner::{
    AdaptiveLearningRunnerConfig, AdaptiveLearningRunnerOutcome, AdaptiveLearningSeed,
    run_adaptive_learning,
};
use crate::candidate_order::{B16Boundary, CANDIDATE_DEPTH, CandidateOrderOracle};
use crate::evaluator::EvaluatorUi;
use crate::fp32_oracle::{
    Fp32Candidate, SimilarNotesRequest, SimilarNotesResponse, SimilarNotesWaveMetrics,
    SimilarNotesWaveResponse, StoredNoteVector, VectorsForNotesResponse,
};
use crate::personalizer_learning::{CompactLearningSettings, RbfLearningSettings, ScaleLevel};
use crate::representation::EventId;
use crate::snapshot::{Error, Result, Validation, count_with_db, io_error, ndb_error, open_ndb};

const PREVIEW_VERSION: &str = "phase3-tui-preview-v1";
const PREVIEW_CORPUS_IDENTITY: &str = "phase3-tui-preview-corpus-v1";
const PREVIEW_NOTE_COUNT: usize = CANDIDATE_DEPTH + 1;
const PREVIEW_INTEREST_COUNT: usize = 5;
const PREVIEW_VECTOR_DIMENSIONS: usize = PREVIEW_INTEREST_COUNT + 2;
const PREVIEW_CREATED_AT: u64 = 1_700_200_000;
const PREVIEW_SECRET_KEY: [u8; 32] = [9; 32];
const INGEST_TIMEOUT: Duration = Duration::from_secs(30);

const OVERFLOWING_NOTE: &str = "A deliberately long note demonstrates the real scrolling behavior at the minimum supported 72 × 24 terminal size.\n\nRust ownership makes resource lifetimes explicit.\nSmall interfaces are easier to reason about.\nDeterministic artifacts make experiments auditable.\nLocal judgments remain separate from public retrieval.\nPositive examples provide nearby support.\nNegative examples provide nearby conflict.\nNeutral examples pull nearby predictions toward neutral.\nDistant evidence contributes nothing.\nRepeated agreement strengthens a region.\nConflicting evidence preserves uncertainty.\nCandidate orders remain frozen while they are judged.\nEvery presented event ID remains in one no-repeat ledger.\nThe question and all seven anchors stay fixed below this pane.\nUse arrows, J/K, Page Up, Page Down, or Home to inspect the whole note.";

const DISPLAY_NOTES: [&str; PREVIEW_INTEREST_COUNT] = [
    OVERFLOWING_NOTE,
    "I finally replaced a proprietary tool with a tiny open-source program that does exactly one thing well. The best feature is the code I no longer have to maintain.",
    "A short note with a link that is shown as text only:\nhttps://example.com/an-article\n\nThe evaluator does not open it or infer what is behind it.",
    "Code-heavy notes remain readable and rateable:\n\nfn distance(left: &[f32], right: &[f32]) -> f32 {\n    left.iter().zip(right).map(|(a, b)| (a - b) * (a - b)).sum()\n}",
    "A note can mix several ideas at once: debugging a distributed system, drinking coffee outside, and wondering whether simple protocols outlive clever platforms.",
];

/// Run the production adaptive-learning runner over deterministic local fixtures.
///
/// `workspace` holds the real temporary NostrDB, session, and Oracle cache artifacts.
/// The caller owns its lifecycle. Reusing the same workspace exercises production recovery.
pub fn run_phase3_preview<U>(
    workspace: impl AsRef<Path>,
    evaluator: &mut U,
) -> Result<AdaptiveLearningRunnerOutcome>
where
    U: EvaluatorUi,
{
    let workspace = workspace.as_ref();
    fs::create_dir_all(workspace).map_err(|source| io_error("create", workspace, source))?;
    let corpus_path = workspace.join("corpus.ndb");
    let event_ids = build_preview_corpus(&corpus_path)?;
    let config = preview_config(workspace, &corpus_path, &event_ids)?;
    let mut oracle = PreviewOracle::new(event_ids);
    run_adaptive_learning(&config, &mut oracle, evaluator)
}

fn build_preview_corpus(corpus_path: &Path) -> Result<Vec<EventId>> {
    let ndb = open_ndb(corpus_path, Validation::Verify)?;
    let mut event_ids = Vec::with_capacity(PREVIEW_NOTE_COUNT);
    for index in 0..PREVIEW_NOTE_COUNT {
        let content = preview_content(index);
        let mut builder = NoteBuilder::new()
            .kind(1)
            .content(&content)
            .created_at(PREVIEW_CREATED_AT + index as u64)
            .sign(&PREVIEW_SECRET_KEY);
        let note = builder
            .build()
            .ok_or_else(|| Error::Invariant(format!("failed to build preview note {index}")))?;
        let event_id = *note.id();
        let event = note
            .json()
            .map_err(|source| ndb_error("encode preview event for", corpus_path, source))?;
        ndb.process_event(&event)
            .map_err(|source| ndb_error("ingest preview event into", corpus_path, source))?;
        event_ids.push(event_id);
    }
    wait_for_preview_corpus(&ndb, corpus_path, PREVIEW_NOTE_COUNT)?;
    drop(ndb);
    Ok(event_ids)
}

fn preview_content(index: usize) -> String {
    if index < 5 {
        return format!("Phase 3 preview seed note {}", index + 1);
    }
    let body = DISPLAY_NOTES[index % PREVIEW_INTEREST_COUNT];
    format!("{body}\n\nPreview fixture note {index:04}.")
}

fn wait_for_preview_corpus(ndb: &nostrdb::Ndb, corpus_path: &Path, expected: usize) -> Result<()> {
    let expected = u64::try_from(expected)
        .map_err(|_| Error::Invariant("preview note count does not fit u64".to_owned()))?;
    let deadline = Instant::now() + INGEST_TIMEOUT;
    loop {
        let count = count_with_db(ndb, corpus_path, None)?;
        if count == expected {
            return Ok(());
        }
        if Instant::now() >= deadline {
            return Err(Error::ExperimentState(format!(
                "preview corpus stored {count} of {expected} notes before timeout"
            )));
        }
        thread::sleep(Duration::from_millis(10));
    }
}

fn preview_config(
    workspace: &Path,
    corpus_path: &Path,
    event_ids: &[EventId],
) -> Result<AdaptiveLearningRunnerConfig> {
    let compact_settings =
        CompactLearningSettings::new(PREVIEW_VERSION, 0.5, 1.0, 2.0, ScaleLevel::Mass64)
            .map_err(|error| Error::ExperimentState(error.to_string()))?;
    let rbf_settings = RbfLearningSettings::new(PREVIEW_VERSION, 0.5, 1.0, 2.0)
        .map_err(|error| Error::ExperimentState(error.to_string()))?;
    let b16 = B16Boundary::new(PREVIEW_VERSION, 0.0)
        .map_err(|error| Error::ExperimentState(error.to_string()))?;
    let seeds = event_ids[..5]
        .iter()
        .copied()
        .map(|event_id| AdaptiveLearningSeed::new(event_id, 7))
        .collect::<Result<Vec<_>>>()?;
    Ok(AdaptiveLearningRunnerConfig {
        corpus_path: corpus_path.to_owned(),
        corpus_identity: PREVIEW_CORPUS_IDENTITY.to_owned(),
        session_path: workspace.join("session.json"),
        compact_settings,
        rbf_settings,
        b16,
        seeds,
    })
}

struct PreviewOracle {
    event_ids: Vec<EventId>,
    vectors: BTreeMap<EventId, Vec<f32>>,
    responses: BTreeMap<EventId, SimilarNotesResponse>,
}

impl PreviewOracle {
    fn new(event_ids: Vec<EventId>) -> Self {
        let vectors = event_ids
            .iter()
            .copied()
            .enumerate()
            .map(|(index, event_id)| (event_id, preview_vector(index)))
            .collect();
        Self {
            event_ids,
            vectors,
            responses: BTreeMap::new(),
        }
    }

    fn response(&self, source: EventId) -> SimilarNotesResponse {
        let rows = self.event_ids.len() as u64;
        let source_vector = &self.vectors[&source];
        let mut candidates = self
            .event_ids
            .iter()
            .copied()
            .filter(|event_id| *event_id != source)
            .map(|event_id| {
                let cosine_score = source_vector
                    .iter()
                    .zip(&self.vectors[&event_id])
                    .map(|(left, right)| left * right)
                    .sum::<f32>();
                (event_id, cosine_score)
            })
            .collect::<Vec<_>>();
        candidates.sort_by(|left, right| {
            right
                .1
                .total_cmp(&left.1)
                .then_with(|| left.0.cmp(&right.0))
        });
        SimilarNotesResponse {
            representation_version: PREVIEW_VERSION.to_owned(),
            represented_rows: rows,
            total_rows: rows,
            complete: true,
            candidates: candidates
                .into_iter()
                .take(CANDIDATE_DEPTH)
                .enumerate()
                .map(|(index, (event_id, cosine_score))| Fp32Candidate {
                    event_id,
                    rank: index + 1,
                    cosine_score,
                })
                .collect(),
        }
    }

    fn validate_request(&self, request: SimilarNotesRequest) -> Result<()> {
        if request.candidate_depth != CANDIDATE_DEPTH {
            return Err(Error::InvalidQuery(format!(
                "preview requires candidate depth {CANDIDATE_DEPTH}"
            )));
        }
        if !self.vectors.contains_key(&request.note_id) {
            return Err(Error::EventNotFound(format!("{:02x?}", request.note_id)));
        }
        Ok(())
    }
}

impl CandidateOrderOracle for PreviewOracle {
    fn representation_version(&self) -> &str {
        PREVIEW_VERSION
    }

    fn similar_notes_wave(
        &mut self,
        requests: &[SimilarNotesRequest],
        representation_version: &str,
    ) -> Result<SimilarNotesWaveResponse> {
        if representation_version != PREVIEW_VERSION || requests.is_empty() {
            return Err(Error::InvalidQuery(
                "unexpected Phase 3 preview query".to_owned(),
            ));
        }
        for request in requests.iter().copied() {
            self.validate_request(request)?;
        }
        let missing = requests
            .iter()
            .filter(|request| !self.responses.contains_key(&request.note_id))
            .map(|request| request.note_id)
            .collect::<Vec<_>>();
        for event_id in missing.iter().copied() {
            self.responses.insert(event_id, self.response(event_id));
        }
        let rows = self.event_ids.len() as u64;
        Ok(SimilarNotesWaveResponse {
            responses: requests
                .iter()
                .map(|request| self.responses[&request.note_id].clone())
                .collect(),
            metrics: SimilarNotesWaveMetrics {
                source_loading_ns: 0,
                query_encoding_ns: 0,
                matrix_scan_ns: 0,
                result_merge_ns: 0,
                encoded_queries: missing.len() as u64,
                cache_hits: (requests.len() - missing.len()) as u64,
                matrix_passes: u64::from(!missing.is_empty()),
                scanned_rows: if missing.is_empty() { 0 } else { rows },
                scan_block_rows: 4_096,
            },
        })
    }

    fn vectors_for_notes(
        &mut self,
        note_ids: &[EventId],
        representation_version: &str,
    ) -> Result<VectorsForNotesResponse> {
        if representation_version != PREVIEW_VERSION {
            return Err(Error::InvalidQuery(
                "unexpected Phase 3 preview representation".to_owned(),
            ));
        }
        for event_id in note_ids {
            if !self.vectors.contains_key(event_id) {
                return Err(Error::EventNotFound(format!("{event_id:02x?}")));
            }
        }
        let rows = self.event_ids.len() as u64;
        Ok(VectorsForNotesResponse {
            representation_version: PREVIEW_VERSION.to_owned(),
            represented_rows: rows,
            total_rows: rows,
            complete: true,
            lookup_elapsed_ns: 0,
            vectors: note_ids
                .iter()
                .copied()
                .map(|event_id| StoredNoteVector {
                    event_id,
                    vector: self.vectors[&event_id].clone(),
                })
                .collect(),
        })
    }
}

fn preview_vector(index: usize) -> Vec<f32> {
    let mut vector = vec![0.0; PREVIEW_VECTOR_DIMENSIONS];
    vector[index % PREVIEW_INTEREST_COUNT] = 1.0;
    let ordinal = index / PREVIEW_INTEREST_COUNT;
    let ordinals_per_interest = PREVIEW_NOTE_COUNT.div_ceil(PREVIEW_INTEREST_COUNT);
    let angle = TAU * ordinal as f32 / ordinals_per_interest as f32;
    vector[PREVIEW_INTEREST_COUNT] = 0.05 * angle.cos();
    vector[PREVIEW_INTEREST_COUNT + 1] = 0.05 * angle.sin();
    let norm = vector.iter().map(|value| value * value).sum::<f32>().sqrt();
    for value in &mut vector {
        *value /= norm;
    }
    vector
}
