use std::collections::{BTreeMap, BTreeSet};
use std::ops::{Deref, DerefMut};

use oracle_mvp::adaptive_learning::{
    AdaptiveLearningCoordinator, AdaptiveLearningError, AdaptiveLearningProgress,
    CompletedAdaptiveLearning,
};
use oracle_mvp::candidate_order::{
    ActivePersonalizerParameters, B16Boundary, CandidateOrderAttempt, CandidateOrderOracle,
};
use oracle_mvp::fp32_oracle::{
    Fp32Candidate, SimilarNotesRequest, SimilarNotesResponse, SimilarNotesWaveMetrics,
    SimilarNotesWaveResponse, StoredNoteVector, VectorsForNotesResponse,
};
use oracle_mvp::personalizer_learning::{
    BatchCandidate, BatchRating, CandidateBatch, CompactLearningController,
    CompactLearningSettings, EvidenceNote, RbfLearningController, RbfLearningSettings, ScaleLevel,
};
use oracle_mvp::quota_resolution::{EventLanguageOutcome, LanguageEligibility, PriorPresentation};
use oracle_mvp::representation::EventId;
use oracle_mvp::snapshot::{Error as SnapshotError, Result as SnapshotResult};

const VERSION: &str = "representation-v1";
const CORPUS_ROWS: u64 = 10_000;

struct CoordinatorFixture<O> {
    coordinator: AdaptiveLearningCoordinator,
    oracle: O,
}

impl<O: CandidateOrderOracle> CoordinatorFixture<O> {
    fn new(
        oracle: O,
        compact: CompactLearningController,
        rbf: RbfLearningController,
        b16: B16Boundary,
    ) -> Result<Self, AdaptiveLearningError> {
        let coordinator = AdaptiveLearningCoordinator::new(&oracle, compact, rbf, b16)?;
        Ok(Self {
            coordinator,
            oracle,
        })
    }

    fn start_next_round(&mut self) -> Result<(), AdaptiveLearningError> {
        self.coordinator.start_next_round(&mut self.oracle)
    }

    fn oracle(&self) -> &O {
        &self.oracle
    }

    fn into_completed(self) -> Result<CompletedAdaptiveLearning, Box<CoordinatorFixture<O>>> {
        match self.coordinator.into_completed() {
            Ok(completed) => Ok(completed),
            Err(coordinator) => Err(Box::new(Self {
                coordinator: *coordinator,
                oracle: self.oracle,
            })),
        }
    }
}

impl<O> Deref for CoordinatorFixture<O> {
    type Target = AdaptiveLearningCoordinator;

    fn deref(&self) -> &Self::Target {
        &self.coordinator
    }
}

impl<O> DerefMut for CoordinatorFixture<O> {
    fn deref_mut(&mut self) -> &mut Self::Target {
        &mut self.coordinator
    }
}

fn id(value: u16) -> EventId {
    let mut event_id = [0_u8; 32];
    event_id[..2].copy_from_slice(&value.to_le_bytes());
    event_id
}

fn id_value(event_id: EventId) -> u16 {
    u16::from_le_bytes([event_id[0], event_id[1]])
}

fn compact_attempt_scale(attempt: &CandidateOrderAttempt) -> ScaleLevel {
    match attempt.active_parameters() {
        ActivePersonalizerParameters::Compact(parameter_tuple) => parameter_tuple.scale_level(),
        ActivePersonalizerParameters::Rbf(_) => panic!("expected Compact attempt"),
    }
}

fn vector_for(_event_id: EventId) -> Vec<f32> {
    vec![1.0, 0.0]
}

fn seed(event_id: u16) -> EvidenceNote {
    EvidenceNote::new(id(event_id), vector_for(id(event_id)), 7).expect("positive seed")
}

fn controllers() -> (CompactLearningController, RbfLearningController) {
    let compact = CompactLearningController::new(
        CompactLearningSettings::new(VERSION, 0.5, 1.0, 2.0, ScaleLevel::Mass64)
            .expect("compact settings"),
        (1..=5).map(seed).collect(),
    )
    .expect("compact controller");
    let rbf = RbfLearningController::new(
        RbfLearningSettings::new(VERSION, 0.5, 1.0, 2.0).expect("RBF settings"),
        (1..=5).map(seed).collect(),
    )
    .expect("RBF controller");
    (compact, rbf)
}

fn h256_fallback_controllers() -> (CompactLearningController, RbfLearningController) {
    let evidence = || {
        (1..=5)
            .map(|event_id| {
                let vector = if event_id == 1 {
                    vec![1.0, 0.0]
                } else {
                    vec![0.0, -1.0]
                };
                EvidenceNote::new(id(event_id), vector, 7).expect("positive seed")
            })
            .collect()
    };
    let compact = CompactLearningController::new(
        CompactLearningSettings::new(VERSION, 0.5, 1.0, 2.0, ScaleLevel::Mass64)
            .expect("compact settings"),
        evidence(),
    )
    .expect("compact controller");
    let rbf = RbfLearningController::new(
        RbfLearningSettings::new(VERSION, 0.5, 1.0, 2.0).expect("RBF settings"),
        evidence(),
    )
    .expect("RBF controller");
    (compact, rbf)
}

/// A fixed public similarity graph with an immutable response cache.
struct RoundOracle {
    cache: BTreeMap<EventId, SimilarNotesResponse>,
    matrix_passes: usize,
    logical_wave_calls: usize,
    wrong_seed: Option<EventId>,
    positive_candidates: usize,
    h256_only_candidates: bool,
    version: &'static str,
}

impl RoundOracle {
    fn new() -> Self {
        Self {
            cache: BTreeMap::new(),
            matrix_passes: 0,
            logical_wave_calls: 0,
            wrong_seed: None,
            positive_candidates: usize::MAX,
            h256_only_candidates: false,
            version: VERSION,
        }
    }

    fn response(source_event_id: EventId) -> SimilarNotesResponse {
        SimilarNotesResponse {
            representation_version: VERSION.to_owned(),
            represented_rows: CORPUS_ROWS,
            total_rows: CORPUS_ROWS,
            complete: true,
            candidates: (0..1_025)
                .map(|offset| id(1_000 + u16::try_from(offset).expect("cached offset")))
                .filter(|event_id| *event_id != source_event_id)
                .take(1_024)
                .enumerate()
                .map(|(offset, event_id)| Fp32Candidate {
                    event_id,
                    rank: offset + 1,
                    cosine_score: 1.0 - offset as f32 / 10_000.0,
                })
                .collect(),
        }
    }
}

impl CandidateOrderOracle for RoundOracle {
    fn representation_version(&self) -> &str {
        self.version
    }

    fn similar_notes_wave(
        &mut self,
        requests: &[SimilarNotesRequest],
        representation_version: &str,
    ) -> SnapshotResult<SimilarNotesWaveResponse> {
        self.logical_wave_calls += 1;
        if representation_version != VERSION || requests.is_empty() {
            return Err(SnapshotError::InvalidQuery(
                "unexpected cached test query".to_owned(),
            ));
        }
        if requests
            .iter()
            .any(|request| request.candidate_depth != 1_024)
        {
            return Err(SnapshotError::InvalidQuery(
                "unexpected cached candidate depth".to_owned(),
            ));
        }
        let missing = requests
            .iter()
            .filter(|request| !self.cache.contains_key(&request.note_id))
            .map(|request| request.note_id)
            .collect::<Vec<_>>();
        if !missing.is_empty() {
            self.matrix_passes += 1;
            for event_id in &missing {
                self.cache.insert(*event_id, Self::response(*event_id));
            }
        }
        Ok(SimilarNotesWaveResponse {
            responses: requests
                .iter()
                .map(|request| self.cache[&request.note_id].clone())
                .collect(),
            metrics: SimilarNotesWaveMetrics {
                source_loading_ns: 0,
                query_encoding_ns: 0,
                matrix_scan_ns: 0,
                result_merge_ns: 0,
                encoded_queries: u64::try_from(missing.len()).expect("missing count"),
                cache_hits: u64::try_from(requests.len() - missing.len()).expect("cache hits"),
                matrix_passes: u64::from(!missing.is_empty()),
                scanned_rows: if missing.is_empty() { 0 } else { CORPUS_ROWS },
                scan_block_rows: 4_096,
            },
        })
    }

    fn vectors_for_notes(
        &mut self,
        note_ids: &[EventId],
        representation_version: &str,
    ) -> SnapshotResult<VectorsForNotesResponse> {
        if representation_version != VERSION {
            return Err(SnapshotError::InvalidQuery(
                "unexpected cached test representation".to_owned(),
            ));
        }
        Ok(VectorsForNotesResponse {
            representation_version: VERSION.to_owned(),
            represented_rows: CORPUS_ROWS,
            total_rows: CORPUS_ROWS,
            complete: true,
            lookup_elapsed_ns: 0,
            vectors: note_ids
                .iter()
                .map(|event_id| StoredNoteVector {
                    event_id: *event_id,
                    vector: if self.wrong_seed == Some(*event_id) {
                        vec![1.0, -0.0]
                    } else if self.h256_only_candidates && id_value(*event_id) == 1 {
                        vec![1.0, 0.0]
                    } else if self.h256_only_candidates && (2..=5).contains(&id_value(*event_id)) {
                        vec![0.0, -1.0]
                    } else if id_value(*event_id) >= 1_000
                        && usize::from(id_value(*event_id) - 1_000) >= self.positive_candidates
                    {
                        vec![-1.0, 0.0]
                    } else if id_value(*event_id) >= 1_000 && self.h256_only_candidates {
                        vec![0.0, 1.0]
                    } else {
                        vector_for(*event_id)
                    },
                })
                .collect(),
        })
    }
}

fn coordinator() -> CoordinatorFixture<RoundOracle> {
    let (compact, rbf) = controllers();
    CoordinatorFixture::new(
        RoundOracle::new(),
        compact,
        rbf,
        B16Boundary::new(VERSION, 0.0).expect("B16"),
    )
    .expect("adaptive-learning coordinator")
}

fn eligible(event_ids: &[EventId]) -> Vec<EventLanguageOutcome> {
    event_ids
        .iter()
        .map(|event_id| EventLanguageOutcome::new(*event_id, LanguageEligibility::Eligible))
        .collect()
}

fn positive_ratings(event_ids: &[EventId]) -> Vec<BatchRating> {
    event_ids
        .iter()
        .enumerate()
        .map(|(index, event_id)| {
            BatchRating::new(*event_id, if index == 0 { 7 } else { 4 }).expect("learning rating")
        })
        .collect()
}

fn neutral_ratings_with_one_positive(event_ids: &[EventId]) -> Vec<BatchRating> {
    event_ids
        .iter()
        .enumerate()
        .map(|(index, event_id)| {
            BatchRating::new(*event_id, if index == 0 { 7 } else { 4 }).expect("learning rating")
        })
        .collect()
}

fn resolve_current_wave(coordinator: &mut CoordinatorFixture<RoundOracle>) {
    let wave = coordinator
        .pending_language_wave()
        .expect("pending language wave")
        .clone();
    coordinator
        .submit_language_outcomes(wave.wave_id(), eligible(wave.event_ids()))
        .expect("eligible language outcomes");
}

#[test]
fn malformed_language_and_rating_input_is_atomic_and_retryable() {
    let mut coordinator = coordinator();
    coordinator.start_next_round().expect("start round one");
    let wave = coordinator
        .pending_language_wave()
        .expect("round-one language wave")
        .clone();
    let mut missing_language = eligible(wave.event_ids());
    missing_language.pop();

    assert!(
        coordinator
            .submit_language_outcomes(wave.wave_id(), missing_language)
            .is_err()
    );
    assert_eq!(
        coordinator.progress(),
        AdaptiveLearningProgress::AwaitingLanguage
    );
    assert_eq!(coordinator.presentation_ledger().len(), 5);
    assert_eq!(coordinator.language_totals().unique_presentations(), 0);
    assert_eq!(coordinator.compact_controller().history().len(), 0);
    assert_eq!(coordinator.rbf_controller().history().len(), 0);

    coordinator
        .submit_language_outcomes(wave.wave_id(), eligible(wave.event_ids()))
        .expect("retry valid language outcomes");
    assert_eq!(
        coordinator.progress(),
        AdaptiveLearningProgress::AwaitingRatings
    );
    assert!(coordinator.compact_controller().pending_batch().is_some());
    assert!(coordinator.rbf_controller().pending_batch().is_some());
    assert_eq!(coordinator.pending_rating_event_ids().unwrap().len(), 20);
    assert_eq!(coordinator.presentation_ledger().len(), 25);
    assert_eq!(
        coordinator
            .presentation_ledger()
            .values()
            .filter(|presentation| matches!(presentation, PriorPresentation::EligibleUnrated))
            .count(),
        20
    );

    let required = coordinator
        .pending_rating_event_ids()
        .expect("new ratings")
        .to_vec();
    let mut missing_rating = positive_ratings(&required);
    missing_rating.pop();
    assert!(coordinator.submit_ratings(missing_rating).is_err());
    assert_eq!(coordinator.compact_controller().history().len(), 0);
    assert_eq!(coordinator.rbf_controller().history().len(), 0);
    assert!(coordinator.compact_controller().pending_batch().is_some());
    assert!(coordinator.rbf_controller().pending_batch().is_some());

    coordinator
        .submit_ratings(positive_ratings(&required))
        .expect("retry valid ratings");
    assert_eq!(coordinator.progress(), AdaptiveLearningProgress::Ready);
    assert_eq!(coordinator.next_round(), Some(2));
    assert_eq!(coordinator.compact_controller().history().len(), 1);
    assert_eq!(coordinator.rbf_controller().history().len(), 1);
    assert!(
        coordinator
            .presentation_ledger()
            .values()
            .all(|presentation| matches!(presentation, PriorPresentation::Rated { .. }))
    );
}

#[test]
fn ten_real_rounds_complete_once_without_repeated_presentations() {
    let mut coordinator = coordinator();
    let mut presented = (1..=5).map(id).collect::<BTreeSet<_>>();
    for round in 1..=10 {
        assert_eq!(coordinator.next_round(), Some(round));
        coordinator
            .start_next_round()
            .expect("start learning round");
        for event_id in coordinator
            .pending_language_wave()
            .expect("pending presentation wave")
            .event_ids()
        {
            assert!(presented.insert(*event_id), "event was presented twice");
        }
        resolve_current_wave(&mut coordinator);
        let rating_ids = coordinator
            .pending_rating_event_ids()
            .expect("pending new rating IDs")
            .to_vec();
        assert_eq!(rating_ids.len(), 20);
        coordinator
            .submit_ratings(positive_ratings(&rating_ids))
            .expect("complete learning round");
    }

    assert_eq!(coordinator.progress(), AdaptiveLearningProgress::Complete);
    assert_eq!(coordinator.next_round(), None);
    assert!(matches!(
        coordinator.start_next_round(),
        Err(AdaptiveLearningError::LearningComplete)
    ));

    let completed = match coordinator.into_completed() {
        Ok(completed) => completed,
        Err(_) => panic!("completed phase must convert"),
    };
    assert_eq!(completed.round_records().len(), 10);
    assert_eq!(
        completed
            .round_records()
            .iter()
            .map(|record| record.round())
            .collect::<Vec<_>>(),
        (1..=10).collect::<Vec<_>>()
    );
    assert_eq!(completed.compact_controller().history().len(), 10);
    assert_eq!(completed.rbf_controller().history().len(), 10);
    assert_eq!(completed.compact_controller().evidence_count(), 205);
    assert_eq!(completed.rbf_controller().evidence_count(), 205);
    assert_eq!(completed.language_totals().eligible_presentations(), 200);
    assert_eq!(
        completed.language_totals().wrong_language_presentations(),
        0
    );
    assert_eq!(completed.presentation_ledger().len(), 205);
    assert_eq!(completed.ratings().len(), 205);
    assert_eq!(completed.b16().representation_version(), VERSION);
    assert!(completed.cached_vector_count() > 5);
    assert_eq!(completed.source_wave_records().len(), 10);
    assert_eq!(
        presented,
        completed.presentation_ledger().keys().copied().collect()
    );
    for record in completed.round_records() {
        assert!(record.compact_order().reserve().iter().all(|candidate| {
            !record
                .presentation_ledger_entries()
                .contains_key(&candidate.event_id())
        }));
        assert!(record.rbf_order().reserve().iter().all(|candidate| {
            !record
                .presentation_ledger_entries()
                .contains_key(&candidate.event_id())
        }));
    }
}

#[test]
fn constructor_rejects_any_nonpositive_or_mismatched_seed_profile() {
    let compact = CompactLearningController::new(
        CompactLearningSettings::new(VERSION, 0.5, 1.0, 2.0, ScaleLevel::Mass64)
            .expect("compact settings"),
        (1..=4).map(seed).collect(),
    )
    .expect("four-seed Compact controller");
    let rbf = RbfLearningController::new(
        RbfLearningSettings::new(VERSION, 0.5, 1.0, 2.0).expect("RBF settings"),
        (1..=4).map(seed).collect(),
    )
    .expect("four-seed RBF controller");
    assert!(matches!(
        CoordinatorFixture::new(
            RoundOracle::new(),
            compact,
            rbf,
            B16Boundary::new(VERSION, 0.0).expect("B16")
        ),
        Err(AdaptiveLearningError::InvalidSeedCount)
    ));

    let (compact, _) = controllers();
    let rbf = RbfLearningController::new(
        RbfLearningSettings::new(VERSION, 0.5, 1.0, 2.0).expect("RBF settings"),
        (1..=4).chain(std::iter::once(6)).map(seed).collect(),
    )
    .expect("mismatched RBF controller");
    assert!(matches!(
        CoordinatorFixture::new(
            RoundOracle::new(),
            compact,
            rbf,
            B16Boundary::new(VERSION, 0.0).expect("B16")
        ),
        Err(AdaptiveLearningError::SeedEvidenceMismatch)
    ));

    let (mut compact, rbf) = controllers();
    compact
        .freeze_batch(
            CandidateBatch::new(
                VERSION,
                vec![BatchCandidate::new(id(99), vector_for(id(99))).expect("pending candidate")],
            )
            .expect("pending batch"),
        )
        .expect("freeze pending batch");
    assert!(matches!(
        CoordinatorFixture::new(
            RoundOracle::new(),
            compact,
            rbf,
            B16Boundary::new(VERSION, 0.0).expect("B16")
        ),
        Err(AdaptiveLearningError::LearningAlreadyStarted)
    ));

    let compact = CompactLearningController::new(
        CompactLearningSettings::new(VERSION, 0.5, 1.0, 2.0, ScaleLevel::Mass64)
            .expect("compact settings"),
        (1..=5)
            .map(|event_id| {
                EvidenceNote::new(
                    id(event_id),
                    vector_for(id(event_id)),
                    if event_id == 5 { 4 } else { 7 },
                )
                .expect("seed")
            })
            .collect(),
    )
    .expect("compact controller");
    let rbf = RbfLearningController::new(
        RbfLearningSettings::new(VERSION, 0.5, 1.0, 2.0).expect("RBF settings"),
        (1..=5)
            .map(|event_id| {
                EvidenceNote::new(
                    id(event_id),
                    vector_for(id(event_id)),
                    if event_id == 5 { 4 } else { 7 },
                )
                .expect("seed")
            })
            .collect(),
    )
    .expect("RBF controller");
    assert!(matches!(
        CoordinatorFixture::new(
            RoundOracle::new(),
            compact,
            rbf,
            B16Boundary::new(VERSION, 0.0).expect("B16")
        ),
        Err(AdaptiveLearningError::NonPositiveSeed { event_id }) if event_id == id(5)
    ));

    let (compact, rbf) = controllers();
    assert!(matches!(
        CoordinatorFixture::new(
            RoundOracle::new(),
            compact,
            rbf,
            B16Boundary::new("other-representation", 0.0).expect("other B16")
        ),
        Err(AdaptiveLearningError::RepresentationVersionMismatch)
    ));

    let (compact, rbf) = controllers();
    let mut wrong_version_oracle = RoundOracle::new();
    wrong_version_oracle.version = "other-representation";
    assert!(matches!(
        CoordinatorFixture::new(
            wrong_version_oracle,
            compact,
            rbf,
            B16Boundary::new(VERSION, 0.0).expect("B16")
        ),
        Err(AdaptiveLearningError::RepresentationVersionMismatch)
    ));
}

#[test]
fn seed_vectors_are_verified_and_all_new_sources_share_one_matrix_pass() {
    let (compact, rbf) = controllers();
    let mut wrong_seed_oracle = RoundOracle::new();
    wrong_seed_oracle.wrong_seed = Some(id(5));
    let mut mismatched = CoordinatorFixture::new(
        wrong_seed_oracle,
        compact,
        rbf,
        B16Boundary::new(VERSION, 0.0).expect("B16"),
    )
    .expect("in-memory seed profile is initially valid");
    assert!(matches!(
        mismatched.start_next_round(),
        Err(AdaptiveLearningError::PhasePaused(
            oracle_mvp::adaptive_learning::AdaptiveLearningFailure::SeedVectorMismatch {
                event_id
            }
        )) if event_id == id(5)
    ));
    assert_eq!(mismatched.progress(), AdaptiveLearningProgress::Paused);

    let (compact, rbf) = controllers();
    let mut coordinator = CoordinatorFixture::new(
        RoundOracle::new(),
        compact,
        rbf,
        B16Boundary::new(VERSION, 0.0).expect("B16"),
    )
    .expect("cached coordinator");
    coordinator.start_next_round().expect("start cached round");
    assert_eq!(coordinator.oracle().matrix_passes, 1);
    assert_eq!(coordinator.oracle().logical_wave_calls, 3);
    assert_eq!(coordinator.source_wave_records().len(), 1);
    let source_wave = &coordinator.source_wave_records()[0];
    assert_eq!(source_wave.round(), 1);
    assert_eq!(source_wave.source_event_ids().len(), 5);
    assert_eq!(source_wave.metrics().matrix_passes, 1);
    assert!(source_wave.accepted());
    assert_eq!(
        coordinator
            .compact_controller()
            .active_tuple()
            .scale_level(),
        ScaleLevel::Mass64,
        "an available H64 order must not activate the fallback"
    );
}

#[test]
fn adaptive_learning_requires_h64_as_the_compact_initial_scale() {
    let compact = CompactLearningController::new(
        CompactLearningSettings::new(VERSION, 0.5, 1.0, 2.0, ScaleLevel::Mass256)
            .expect("standalone Compact settings may select H256"),
        (1..=5).map(seed).collect(),
    )
    .expect("standalone Compact controller");
    let rbf = RbfLearningController::new(
        RbfLearningSettings::new(VERSION, 0.5, 1.0, 2.0).expect("RBF settings"),
        (1..=5).map(seed).collect(),
    )
    .expect("RBF controller");

    assert!(matches!(
        CoordinatorFixture::new(
            RoundOracle::new(),
            compact,
            rbf,
            B16Boundary::new(VERSION, 0.0).expect("B16")
        ),
        Err(AdaptiveLearningError::InvalidInitialCompactScale)
    ));
}

#[test]
fn first_round_retries_h256_before_any_presentation_or_learning() {
    let (compact, rbf) = h256_fallback_controllers();
    let mut oracle = RoundOracle::new();
    oracle.h256_only_candidates = true;
    let mut coordinator = CoordinatorFixture::new(
        oracle,
        compact,
        rbf,
        B16Boundary::new(VERSION, 0.0).expect("B16"),
    )
    .expect("fallback coordinator");

    coordinator
        .start_next_round()
        .expect("H256 must rescue the unavailable H64 first round");

    assert_eq!(
        coordinator
            .compact_controller()
            .active_tuple()
            .scale_level(),
        ScaleLevel::Mass256
    );
    assert_eq!(
        coordinator.progress(),
        AdaptiveLearningProgress::AwaitingLanguage
    );
    assert_eq!(coordinator.presentation_ledger().len(), 5);
    assert_eq!(coordinator.language_totals().unique_presentations(), 0);
    assert!(coordinator.compact_controller().history().is_empty());
    assert!(coordinator.rbf_controller().history().is_empty());
    assert_eq!(coordinator.oracle().matrix_passes, 1);
    assert_eq!(coordinator.oracle().logical_wave_calls, 4);
    assert_eq!(coordinator.failed_candidate_order_attempts().len(), 1);
    assert_eq!(
        compact_attempt_scale(&coordinator.failed_candidate_order_attempts()[0]),
        ScaleLevel::Mass64
    );

    resolve_current_wave(&mut coordinator);
    let rating_ids = coordinator
        .pending_rating_event_ids()
        .expect("fallback round ratings")
        .to_vec();
    coordinator
        .submit_ratings(positive_ratings(&rating_ids))
        .expect("complete fallback round");
    let first_round = &coordinator.round_records()[0];
    assert_eq!(
        compact_attempt_scale(first_round.compact_order().attempt()),
        ScaleLevel::Mass256,
        "the causally frozen round must record the tuple that generated its order"
    );
    assert_eq!(coordinator.failed_candidate_order_attempts().len(), 1);
}

#[test]
fn h64_and_h256_insufficiency_pauses_before_any_presentation_or_learning() {
    let (compact, rbf) = controllers();
    let mut oracle = RoundOracle::new();
    oracle.positive_candidates = 40;
    let mut coordinator = CoordinatorFixture::new(
        oracle,
        compact,
        rbf,
        B16Boundary::new(VERSION, 0.0).expect("B16"),
    )
    .expect("insufficient coordinator");

    assert!(matches!(
        coordinator.start_next_round(),
        Err(AdaptiveLearningError::PhasePaused(
            oracle_mvp::adaptive_learning::AdaptiveLearningFailure::CompactGeometryMismatch {
                h64_accepted: 40,
                h256_accepted: 40,
                required: 41,
            }
        ))
    ));
    assert_eq!(coordinator.progress(), AdaptiveLearningProgress::Paused);
    assert_eq!(coordinator.presentation_ledger().len(), 5);
    assert_eq!(coordinator.language_totals().unique_presentations(), 0);
    assert!(coordinator.compact_controller().history().is_empty());
    assert!(coordinator.rbf_controller().history().is_empty());
    assert!(coordinator.compact_controller().pending_batch().is_none());
    assert!(coordinator.rbf_controller().pending_batch().is_none());
    assert_eq!(
        coordinator
            .compact_controller()
            .active_tuple()
            .scale_level(),
        ScaleLevel::Mass64,
        "an unsuccessful speculative fallback must not mutate the controller"
    );
    let attempts = coordinator.failed_candidate_order_attempts();
    assert_eq!(attempts.len(), 2);
    assert_eq!(compact_attempt_scale(&attempts[0]), ScaleLevel::Mass64);
    assert_eq!(compact_attempt_scale(&attempts[1]), ScaleLevel::Mass256);
    assert_eq!(
        attempts[0].evidence_identity(),
        attempts[1].evidence_identity()
    );
    assert_eq!(attempts[0].b16(), attempts[1].b16());
    assert_eq!(
        attempts[0].candidate_pool_identity_sha256(),
        attempts[1].candidate_pool_identity_sha256()
    );
    assert_eq!(
        attempts[0].source_responses(),
        attempts[1].source_responses()
    );
    assert_eq!(attempts[0].accepted().len(), 40);
    assert_eq!(attempts[1].accepted().len(), 40);
    assert_eq!(coordinator.oracle().logical_wave_calls, 3);
    assert_eq!(coordinator.source_wave_records().len(), 1);
    assert!(!coordinator.source_wave_records()[0].accepted());
}

#[test]
fn a_wrong_language_presentation_is_never_presented_again() {
    let (compact, rbf) = controllers();
    let mut coordinator = CoordinatorFixture::new(
        RoundOracle::new(),
        compact,
        rbf,
        B16Boundary::new(VERSION, 0.0).expect("B16"),
    )
    .expect("cached coordinator");

    coordinator.start_next_round().expect("start round one");
    let primary = coordinator
        .pending_language_wave()
        .expect("round-one primary wave")
        .clone();
    let wrong_language = primary.event_ids()[0];
    let outcomes = primary
        .event_ids()
        .iter()
        .map(|event_id| {
            EventLanguageOutcome::new(
                *event_id,
                if *event_id == wrong_language {
                    LanguageEligibility::WrongLanguage
                } else {
                    LanguageEligibility::Eligible
                },
            )
        })
        .collect();
    coordinator
        .submit_language_outcomes(primary.wave_id(), outcomes)
        .expect("record wrong-language outcome");
    let replacement = coordinator
        .pending_language_wave()
        .expect("one replacement")
        .clone();
    coordinator
        .submit_language_outcomes(replacement.wave_id(), eligible(replacement.event_ids()))
        .expect("accept replacement");
    let rating_ids = coordinator
        .pending_rating_event_ids()
        .expect("round-one ratings")
        .to_vec();
    coordinator
        .submit_ratings(neutral_ratings_with_one_positive(&rating_ids))
        .expect("complete round one");

    coordinator.start_next_round().expect("start round two");
    assert!(
        !coordinator
            .pending_language_wave()
            .expect("round-two primary wave")
            .event_ids()
            .contains(&wrong_language)
    );
    assert!(matches!(
        coordinator.presentation_ledger().get(&wrong_language),
        Some(PriorPresentation::WrongLanguage)
    ));
}

const COMPACT_GROUP_START: u16 = 1_000;
const RBF_GROUP_START: u16 = 2_000;
const FILLER_GROUP_START: u16 = 3_000;

fn divergent_seed_vectors() -> [Vec<f32>; 5] {
    [
        unit_vector(0.0),
        unit_vector(180.0),
        unit_vector(90.0),
        unit_vector(270.0),
        unit_vector(45.0),
    ]
}

fn unit_vector(degrees: f32) -> Vec<f32> {
    let radians = degrees.to_radians();
    vec![radians.cos(), radians.sin()]
}

fn divergent_controllers() -> (CompactLearningController, RbfLearningController) {
    let evidence = divergent_seed_vectors()
        .into_iter()
        .enumerate()
        .map(|(index, vector)| {
            EvidenceNote::new(id(u16::try_from(index + 1).expect("seed ID")), vector, 7)
                .expect("divergent seed")
        })
        .collect::<Vec<_>>();
    let compact = CompactLearningController::new(
        CompactLearningSettings::new(VERSION, 0.5, 1.0, 2.0, ScaleLevel::Mass64)
            .expect("compact settings"),
        evidence.clone(),
    )
    .expect("compact controller");
    let rbf = RbfLearningController::new(
        RbfLearningSettings::new(VERSION, 0.5, 1.0, 2.0).expect("RBF settings"),
        evidence,
    )
    .expect("RBF controller");
    (compact, rbf)
}

fn divergent_vector(event_id: EventId) -> Option<Vec<f32>> {
    let value = id_value(event_id);
    match value {
        1..=5 => Some(divergent_seed_vectors()[usize::from(value - 1)].clone()),
        COMPACT_GROUP_START..=1_019 => Some(unit_vector(122.0)),
        RBF_GROUP_START..=2_019 => Some(unit_vector(70.0)),
        FILLER_GROUP_START..=3_984 => Some(unit_vector(214.0)),
        _ => None,
    }
}

struct StaticReuseOracle {
    cache: BTreeMap<EventId, SimilarNotesResponse>,
    matrix_passes: usize,
}

impl StaticReuseOracle {
    fn new() -> Self {
        Self {
            cache: BTreeMap::new(),
            matrix_passes: 0,
        }
    }

    fn response(source_event_id: EventId) -> SimilarNotesResponse {
        let event_ids = (COMPACT_GROUP_START..=1_019)
            .chain(RBF_GROUP_START..=2_019)
            .chain(FILLER_GROUP_START..=3_984)
            .map(id)
            .filter(|event_id| *event_id != source_event_id)
            .take(1_024);
        SimilarNotesResponse {
            representation_version: VERSION.to_owned(),
            represented_rows: CORPUS_ROWS,
            total_rows: CORPUS_ROWS,
            complete: true,
            candidates: event_ids
                .enumerate()
                .map(|(offset, event_id)| Fp32Candidate {
                    event_id,
                    rank: offset + 1,
                    cosine_score: 1.0 - offset as f32 / 10_000.0,
                })
                .collect(),
        }
    }
}

impl CandidateOrderOracle for StaticReuseOracle {
    fn representation_version(&self) -> &str {
        VERSION
    }

    fn similar_notes_wave(
        &mut self,
        requests: &[SimilarNotesRequest],
        representation_version: &str,
    ) -> SnapshotResult<SimilarNotesWaveResponse> {
        if representation_version != VERSION || requests.is_empty() {
            return Err(SnapshotError::InvalidQuery(
                "unexpected stored-reuse test query".to_owned(),
            ));
        }
        if requests
            .iter()
            .any(|request| request.candidate_depth != 1_024)
        {
            return Err(SnapshotError::InvalidQuery(
                "unexpected stored-reuse candidate depth".to_owned(),
            ));
        }
        let missing = requests
            .iter()
            .filter(|request| !self.cache.contains_key(&request.note_id))
            .map(|request| request.note_id)
            .collect::<Vec<_>>();
        if !missing.is_empty() {
            self.matrix_passes += 1;
            for event_id in &missing {
                self.cache.insert(*event_id, Self::response(*event_id));
            }
        }
        Ok(SimilarNotesWaveResponse {
            responses: requests
                .iter()
                .map(|request| self.cache[&request.note_id].clone())
                .collect(),
            metrics: SimilarNotesWaveMetrics {
                source_loading_ns: 0,
                query_encoding_ns: 0,
                matrix_scan_ns: 0,
                result_merge_ns: 0,
                encoded_queries: u64::try_from(missing.len()).expect("request count"),
                cache_hits: u64::try_from(requests.len() - missing.len()).expect("cache hits"),
                matrix_passes: u64::from(!missing.is_empty()),
                scanned_rows: if missing.is_empty() { 0 } else { CORPUS_ROWS },
                scan_block_rows: 4_096,
            },
        })
    }

    fn vectors_for_notes(
        &mut self,
        note_ids: &[EventId],
        representation_version: &str,
    ) -> SnapshotResult<VectorsForNotesResponse> {
        if representation_version != VERSION {
            return Err(SnapshotError::InvalidQuery(
                "unexpected stored-reuse test representation".to_owned(),
            ));
        }
        let vectors = note_ids
            .iter()
            .map(|event_id| {
                Ok(StoredNoteVector {
                    event_id: *event_id,
                    vector: divergent_vector(*event_id)
                        .ok_or_else(|| SnapshotError::EventNotFound(format!("{event_id:?}")))?,
                })
            })
            .collect::<SnapshotResult<Vec<_>>>()?;
        Ok(VectorsForNotesResponse {
            representation_version: VERSION.to_owned(),
            represented_rows: CORPUS_ROWS,
            total_rows: CORPUS_ROWS,
            complete: true,
            lookup_elapsed_ns: 0,
            vectors,
        })
    }
}

#[test]
fn another_personalizers_rating_is_reused_after_freeze_without_redisplay() {
    let (compact, rbf) = divergent_controllers();
    let mut coordinator = CoordinatorFixture::new(
        StaticReuseOracle::new(),
        compact,
        rbf,
        B16Boundary::new(VERSION, 0.0).expect("B16"),
    )
    .expect("reuse coordinator");

    coordinator.start_next_round().expect("round one");
    let wave = coordinator
        .pending_language_wave()
        .expect("round-one wave")
        .clone();
    let compact_selected = wave
        .event_ids()
        .iter()
        .filter(|event_id| (COMPACT_GROUP_START..=1_019).contains(&id_value(**event_id)))
        .copied()
        .collect::<Vec<_>>();
    let rbf_selected = wave
        .event_ids()
        .iter()
        .filter(|event_id| (RBF_GROUP_START..=2_019).contains(&id_value(**event_id)))
        .copied()
        .collect::<Vec<_>>();
    assert_eq!(compact_selected.len(), 20);
    assert_eq!(rbf_selected.len(), 20);
    let reused = wave
        .event_ids()
        .iter()
        .copied()
        .find(|event_id| (RBF_GROUP_START..=2_019).contains(&id_value(*event_id)))
        .expect("RBF-only event");
    coordinator
        .submit_language_outcomes(wave.wave_id(), eligible(wave.event_ids()))
        .expect("round-one language");
    let round_one_ids = coordinator
        .pending_rating_event_ids()
        .expect("round-one ratings")
        .to_vec();
    coordinator
        .submit_ratings(
            round_one_ids
                .iter()
                .map(|event_id| BatchRating::new(*event_id, 7).expect("round-one rating"))
                .collect(),
        )
        .expect("complete round one");

    coordinator
        .start_next_round()
        .expect("all-stored round completes internally");
    assert_eq!(coordinator.progress(), AdaptiveLearningProgress::Ready);
    assert!(coordinator.pending_language_wave().is_none());
    assert!(coordinator.pending_rating_event_ids().is_none());
    assert_eq!(coordinator.language_totals().unique_presentations(), 40);

    let record = &coordinator.round_records()[1];
    assert!(record.quota_metadata().new_rating_routes().is_empty());
    assert_eq!(
        record.quota_metadata().stored_rating_reuse_routes().len(),
        40
    );
    assert!(
        record
            .quota_metadata()
            .stored_rating_reuse_routes()
            .iter()
            .any(|route| route.event_id() == reused
                && route.personalizer() == oracle_mvp::quota_resolution::PersonalizerId::Compact)
    );
    let reused_outcome = record
        .compact_round()
        .outcomes()
        .iter()
        .find(|outcome| outcome.event_id() == reused)
        .expect("stored Compact outcome");
    assert_eq!(reused_outcome.rating().value(), 7);
    assert!(
        !record
            .rbf_round()
            .outcomes()
            .iter()
            .any(|outcome| outcome.event_id() == reused)
    );
    assert!(matches!(
        coordinator.presentation_ledger().get(&reused),
        Some(PriorPresentation::Rated { selected_by })
            if selected_by == &BTreeSet::from([
                oracle_mvp::quota_resolution::PersonalizerId::Compact,
                oracle_mvp::quota_resolution::PersonalizerId::Rbf,
            ])
    ));
    assert_eq!(
        coordinator.source_wave_records()[1].metrics().matrix_passes,
        1
    );
    assert!(
        coordinator.source_wave_records()[1]
            .metrics()
            .encoded_queries
            > 0
    );
}

#[test]
fn a_round_with_only_stored_ratings_completes_without_requesting_input() {
    let (compact, rbf) = divergent_controllers();
    let mut coordinator = CoordinatorFixture::new(
        StaticReuseOracle::new(),
        compact,
        rbf,
        B16Boundary::new(VERSION, 0.0).expect("B16"),
    )
    .expect("all-stored coordinator");

    coordinator.start_next_round().expect("round one");
    let wave = coordinator
        .pending_language_wave()
        .expect("round-one wave")
        .clone();
    assert_eq!(wave.event_ids().len(), 40);
    coordinator
        .submit_language_outcomes(wave.wave_id(), eligible(wave.event_ids()))
        .expect("round-one language");
    let rating_ids = coordinator
        .pending_rating_event_ids()
        .expect("round-one ratings")
        .to_vec();
    coordinator
        .submit_ratings(
            rating_ids
                .iter()
                .map(|event_id| BatchRating::new(*event_id, 7).expect("positive rating"))
                .collect(),
        )
        .expect("complete round one");

    coordinator
        .start_next_round()
        .expect("all-stored round completes internally");
    assert_eq!(coordinator.progress(), AdaptiveLearningProgress::Ready);
    assert_eq!(coordinator.next_round(), Some(3));
    assert!(coordinator.pending_language_wave().is_none());
    assert!(coordinator.pending_rating_event_ids().is_none());
    assert_eq!(coordinator.compact_controller().history().len(), 2);
    assert_eq!(coordinator.rbf_controller().history().len(), 2);
    assert_eq!(coordinator.presentation_ledger().len(), 45);
    assert_eq!(coordinator.language_totals().unique_presentations(), 40);
    assert!(
        coordinator.round_records()[1]
            .quota_metadata()
            .new_rating_routes()
            .is_empty()
    );
    assert_eq!(
        coordinator.round_records()[1]
            .quota_metadata()
            .stored_rating_reuse_routes()
            .len(),
        40
    );
}

const BOUNDARY_COMPACT_START: u16 = 10_000;
const BOUNDARY_COMPACT_END: u16 = 10_219;
const BOUNDARY_RBF_START: u16 = 20_000;
const BOUNDARY_RBF_END: u16 = 20_200;
const BOUNDARY_FILLER_START: u16 = 30_000;
const BOUNDARY_FILLER_END: u16 = 30_602;
const BOUNDARY_SPARE: u16 = 40_000;

fn is_boundary_compact(event_id: EventId) -> bool {
    (BOUNDARY_COMPACT_START..=BOUNDARY_COMPACT_END).contains(&id_value(event_id))
}

fn is_boundary_rbf(event_id: EventId) -> bool {
    (BOUNDARY_RBF_START..=BOUNDARY_RBF_END).contains(&id_value(event_id))
}

fn boundary_candidate_ids() -> Vec<EventId> {
    (BOUNDARY_COMPACT_START..=BOUNDARY_COMPACT_END)
        .chain(BOUNDARY_RBF_START..=BOUNDARY_RBF_END)
        .chain(BOUNDARY_FILLER_START..=BOUNDARY_FILLER_END)
        .map(id)
        .collect()
}

fn boundary_vector(event_id: EventId) -> Option<Vec<f32>> {
    let value = id_value(event_id);
    match value {
        1..=5 => Some(divergent_seed_vectors()[usize::from(value - 1)].clone()),
        BOUNDARY_COMPACT_START..=BOUNDARY_COMPACT_END => Some(unit_vector(263.0)),
        BOUNDARY_RBF_START..=BOUNDARY_RBF_END => Some(unit_vector(67.0)),
        BOUNDARY_FILLER_START..=BOUNDARY_FILLER_END | BOUNDARY_SPARE => Some(unit_vector(245.0)),
        _ => None,
    }
}

struct StaticBoundaryOracle {
    cache: BTreeMap<EventId, SimilarNotesResponse>,
}

impl StaticBoundaryOracle {
    fn new() -> Self {
        Self {
            cache: BTreeMap::new(),
        }
    }

    fn response(source_event_id: EventId) -> SimilarNotesResponse {
        let mut event_ids = boundary_candidate_ids()
            .into_iter()
            .filter(|event_id| *event_id != source_event_id)
            .collect::<Vec<_>>();
        if event_ids.len() == 1_023 {
            event_ids.push(id(BOUNDARY_SPARE));
        }
        assert_eq!(event_ids.len(), 1_024);
        SimilarNotesResponse {
            representation_version: VERSION.to_owned(),
            represented_rows: CORPUS_ROWS,
            total_rows: CORPUS_ROWS,
            complete: true,
            candidates: event_ids
                .into_iter()
                .enumerate()
                .map(|(offset, event_id)| Fp32Candidate {
                    event_id,
                    rank: offset + 1,
                    cosine_score: 1.0 - offset as f32 / 10_000.0,
                })
                .collect(),
        }
    }
}

impl CandidateOrderOracle for StaticBoundaryOracle {
    fn representation_version(&self) -> &str {
        VERSION
    }

    fn similar_notes_wave(
        &mut self,
        requests: &[SimilarNotesRequest],
        representation_version: &str,
    ) -> SnapshotResult<SimilarNotesWaveResponse> {
        if representation_version != VERSION || requests.is_empty() {
            return Err(SnapshotError::InvalidQuery(
                "unexpected language-boundary test query".to_owned(),
            ));
        }
        if requests
            .iter()
            .any(|request| request.candidate_depth != 1_024)
        {
            return Err(SnapshotError::InvalidQuery(
                "unexpected language-boundary candidate depth".to_owned(),
            ));
        }
        let missing = requests
            .iter()
            .filter(|request| !self.cache.contains_key(&request.note_id))
            .map(|request| request.note_id)
            .collect::<Vec<_>>();
        for source_event_id in &missing {
            self.cache
                .insert(*source_event_id, Self::response(*source_event_id));
        }
        Ok(SimilarNotesWaveResponse {
            responses: requests
                .iter()
                .map(|request| self.cache[&request.note_id].clone())
                .collect(),
            metrics: SimilarNotesWaveMetrics {
                source_loading_ns: 0,
                query_encoding_ns: 0,
                matrix_scan_ns: 0,
                result_merge_ns: 0,
                encoded_queries: u64::try_from(missing.len()).expect("request count"),
                cache_hits: u64::try_from(requests.len() - missing.len()).expect("cache hits"),
                matrix_passes: u64::from(!missing.is_empty()),
                scanned_rows: if missing.is_empty() { 0 } else { CORPUS_ROWS },
                scan_block_rows: 4_096,
            },
        })
    }

    fn vectors_for_notes(
        &mut self,
        note_ids: &[EventId],
        representation_version: &str,
    ) -> SnapshotResult<VectorsForNotesResponse> {
        if representation_version != VERSION {
            return Err(SnapshotError::InvalidQuery(
                "unexpected language-boundary test representation".to_owned(),
            ));
        }
        let vectors = note_ids
            .iter()
            .map(|event_id| {
                Ok(StoredNoteVector {
                    event_id: *event_id,
                    vector: boundary_vector(*event_id)
                        .ok_or_else(|| SnapshotError::EventNotFound(format!("{event_id:?}")))?,
                })
            })
            .collect::<SnapshotResult<Vec<_>>>()?;
        Ok(VectorsForNotesResponse {
            representation_version: VERSION.to_owned(),
            represented_rows: CORPUS_ROWS,
            total_rows: CORPUS_ROWS,
            complete: true,
            lookup_elapsed_ns: 0,
            vectors,
        })
    }
}

fn boundary_coordinator() -> CoordinatorFixture<StaticBoundaryOracle> {
    let (compact, rbf) = divergent_controllers();
    CoordinatorFixture::new(
        StaticBoundaryOracle::new(),
        compact,
        rbf,
        B16Boundary::new(VERSION, 0.0).expect("B16"),
    )
    .expect("language-boundary coordinator")
}

fn assert_boundary_cohorts(event_ids: &[EventId], compact: usize, rbf: usize) {
    assert_eq!(event_ids.len(), compact + rbf);
    assert_eq!(
        event_ids
            .iter()
            .filter(|event_id| is_boundary_compact(**event_id))
            .count(),
        compact
    );
    assert_eq!(
        event_ids
            .iter()
            .filter(|event_id| is_boundary_rbf(**event_id))
            .count(),
        rbf
    );
}

fn assert_boundary_primary(event_ids: &[EventId]) {
    assert_boundary_cohorts(event_ids, 20, 20);
    assert!(
        event_ids[..20]
            .iter()
            .all(|event_id| is_boundary_compact(*event_id))
    );
    assert!(
        event_ids[20..]
            .iter()
            .all(|event_id| is_boundary_rbf(*event_id))
    );
}

fn boundary_ratings(event_ids: &[EventId]) -> Vec<BatchRating> {
    assert_boundary_cohorts(event_ids, 20, 20);
    let mut compact_seen = 0;
    let mut rbf_seen = 0;
    event_ids
        .iter()
        .map(|event_id| {
            let selected_seen = if is_boundary_compact(*event_id) {
                &mut compact_seen
            } else if is_boundary_rbf(*event_id) {
                &mut rbf_seen
            } else {
                panic!("rating references an event outside the boundary cohorts")
            };
            let rating = if *selected_seen < 4 { 7 } else { 4 };
            *selected_seen += 1;
            BatchRating::new(*event_id, rating).expect("boundary rating")
        })
        .collect()
}

fn rate_pending_boundary(coordinator: &mut CoordinatorFixture<StaticBoundaryOracle>) {
    let ids = coordinator
        .pending_rating_event_ids()
        .expect("pending ratings")
        .to_vec();
    coordinator
        .submit_ratings(boundary_ratings(&ids))
        .expect("complete language-boundary round");
}

fn complete_clean_boundary_round(coordinator: &mut CoordinatorFixture<StaticBoundaryOracle>) {
    let presentations_before = coordinator.language_totals().unique_presentations();
    let ledger_before = coordinator.presentation_ledger().len();
    coordinator.start_next_round().expect("start clean round");
    let wave = coordinator
        .pending_language_wave()
        .expect("clean wave")
        .clone();
    assert_boundary_primary(wave.event_ids());
    assert!(
        wave.event_ids()
            .iter()
            .all(|event_id| !coordinator.presentation_ledger().contains_key(event_id))
    );
    coordinator
        .submit_language_outcomes(wave.wave_id(), eligible(wave.event_ids()))
        .expect("clean language outcomes");
    rate_pending_boundary(coordinator);
    assert_eq!(
        coordinator.language_totals().unique_presentations(),
        presentations_before + 40
    );
    assert_eq!(coordinator.presentation_ledger().len(), ledger_before + 40);
}

#[test]
fn complete_phase_language_ceiling_accepts_21_of_421_and_rejects_the_22nd() {
    let mut passing = boundary_coordinator();
    for _ in 0..9 {
        complete_clean_boundary_round(&mut passing);
    }
    assert_eq!(passing.language_totals().unique_presentations(), 360);
    passing.start_next_round().expect("start passing round ten");
    let initial = passing
        .pending_language_wave()
        .expect("round-ten primary wave")
        .clone();
    assert_boundary_primary(initial.event_ids());
    assert!(
        initial
            .event_ids()
            .iter()
            .all(|event_id| !passing.presentation_ledger().contains_key(event_id))
    );
    let outcomes = initial
        .event_ids()
        .iter()
        .enumerate()
        .map(|(index, event_id)| {
            EventLanguageOutcome::new(
                *event_id,
                if index <= 20 {
                    LanguageEligibility::WrongLanguage
                } else {
                    LanguageEligibility::Eligible
                },
            )
        })
        .collect();
    passing
        .submit_language_outcomes(initial.wave_id(), outcomes)
        .expect("21 wrong-language outcomes remain recoverable");
    let replacements = passing
        .pending_language_wave()
        .expect("frozen replacement wave")
        .clone();
    assert_boundary_cohorts(replacements.event_ids(), 20, 1);
    assert!(
        replacements
            .event_ids()
            .iter()
            .all(|event_id| !passing.presentation_ledger().contains_key(event_id))
    );
    passing
        .submit_language_outcomes(replacements.wave_id(), eligible(replacements.event_ids()))
        .expect("replacement wave completes valid phase ratio");
    assert_eq!(passing.language_totals().eligible_presentations(), 400);
    assert_eq!(passing.language_totals().wrong_language_presentations(), 21);
    assert_eq!(passing.language_totals().unique_presentations(), 421);
    rate_pending_boundary(&mut passing);
    assert_eq!(passing.progress(), AdaptiveLearningProgress::Complete);

    let mut failing = boundary_coordinator();
    failing
        .start_next_round()
        .expect("start first failing run round");
    let first = failing
        .pending_language_wave()
        .expect("first primary wave")
        .clone();
    assert_boundary_primary(first.event_ids());
    assert!(
        first
            .event_ids()
            .iter()
            .all(|event_id| !failing.presentation_ledger().contains_key(event_id))
    );
    let first_outcomes = first
        .event_ids()
        .iter()
        .enumerate()
        .map(|(index, event_id)| {
            EventLanguageOutcome::new(
                *event_id,
                if index == 0 {
                    LanguageEligibility::WrongLanguage
                } else {
                    LanguageEligibility::Eligible
                },
            )
        })
        .collect();
    failing
        .submit_language_outcomes(first.wave_id(), first_outcomes)
        .expect("one early language failure");
    let first_replacement = failing
        .pending_language_wave()
        .expect("first replacement")
        .clone();
    assert_boundary_cohorts(first_replacement.event_ids(), 1, 0);
    assert!(
        first_replacement
            .event_ids()
            .iter()
            .all(|event_id| !failing.presentation_ledger().contains_key(event_id))
    );
    failing
        .submit_language_outcomes(
            first_replacement.wave_id(),
            eligible(first_replacement.event_ids()),
        )
        .expect("first replacement eligible");
    rate_pending_boundary(&mut failing);
    for _ in 1..9 {
        complete_clean_boundary_round(&mut failing);
    }

    failing.start_next_round().expect("start failing round ten");
    let final_primary = failing
        .pending_language_wave()
        .expect("failing final primary")
        .clone();
    assert_boundary_primary(final_primary.event_ids());
    assert!(
        final_primary
            .event_ids()
            .iter()
            .all(|event_id| !failing.presentation_ledger().contains_key(event_id))
    );
    let final_outcomes = final_primary
        .event_ids()
        .iter()
        .enumerate()
        .map(|(index, event_id)| {
            EventLanguageOutcome::new(
                *event_id,
                if index <= 20 {
                    LanguageEligibility::WrongLanguage
                } else {
                    LanguageEligibility::Eligible
                },
            )
        })
        .collect();
    failing
        .submit_language_outcomes(final_primary.wave_id(), final_outcomes)
        .expect("round ten reaches its exact final-ratio check");
    let final_replacements = failing
        .pending_language_wave()
        .expect("failing final replacement wave")
        .clone();
    assert_eq!(final_replacements.event_ids().len(), 21);
    assert!(
        final_replacements
            .event_ids()
            .iter()
            .all(|event_id| !failing.presentation_ledger().contains_key(event_id))
    );
    assert!(matches!(
        failing.submit_language_outcomes(
            final_replacements.wave_id(),
            eligible(final_replacements.event_ids()),
        ),
        Err(AdaptiveLearningError::PhasePaused(
            oracle_mvp::adaptive_learning::AdaptiveLearningFailure::FinalLanguageCeiling {
                wrong_language: 22,
                unique_presentations: 422,
            }
        ))
    ));
    assert_eq!(failing.progress(), AdaptiveLearningProgress::Paused);
    assert_eq!(failing.compact_controller().history().len(), 9);
    assert_eq!(failing.rbf_controller().history().len(), 9);
    assert!(failing.compact_controller().pending_batch().is_none());
    assert!(failing.rbf_controller().pending_batch().is_none());
    assert_eq!(failing.language_totals().wrong_language_presentations(), 22);
    assert_eq!(failing.language_totals().unique_presentations(), 422);
    assert_eq!(failing.presentation_ledger().len(), 427);
}

#[test]
fn the_twenty_second_wrong_language_outcome_stops_before_round_ten() {
    let mut coordinator = boundary_coordinator();
    coordinator.start_next_round().expect("start round one");
    let wave = coordinator
        .pending_language_wave()
        .expect("round-one primary wave")
        .clone();
    let outcomes = wave
        .event_ids()
        .iter()
        .enumerate()
        .map(|(index, event_id)| {
            EventLanguageOutcome::new(
                *event_id,
                if index < 22 {
                    LanguageEligibility::WrongLanguage
                } else {
                    LanguageEligibility::Eligible
                },
            )
        })
        .collect();

    assert!(matches!(
        coordinator.submit_language_outcomes(wave.wave_id(), outcomes),
        Err(AdaptiveLearningError::PhasePaused(
            oracle_mvp::adaptive_learning::AdaptiveLearningFailure::WrongLanguageLimit {
                wrong_language: 22,
                unique_presentations: 40,
            }
        ))
    ));
    assert!(coordinator.compact_controller().history().is_empty());
    assert!(coordinator.rbf_controller().history().is_empty());
    assert_eq!(coordinator.presentation_ledger().len(), 45);
}

#[test]
fn round_ten_rejects_a_complete_phase_above_five_percent_wrong_language() {
    let mut coordinator = coordinator();
    for _ in 0..9 {
        coordinator.start_next_round().expect("start clean round");
        resolve_current_wave(&mut coordinator);
        let rating_ids = coordinator
            .pending_rating_event_ids()
            .expect("clean-round ratings")
            .to_vec();
        coordinator
            .submit_ratings(neutral_ratings_with_one_positive(&rating_ids))
            .expect("complete clean round");
    }

    coordinator.start_next_round().expect("start round ten");
    let primary = coordinator
        .pending_language_wave()
        .expect("round-ten primary wave")
        .clone();
    assert_eq!(primary.event_ids().len(), 20);
    let outcomes = primary
        .event_ids()
        .iter()
        .enumerate()
        .map(|(index, event_id)| {
            EventLanguageOutcome::new(
                *event_id,
                if index < 11 {
                    LanguageEligibility::WrongLanguage
                } else {
                    LanguageEligibility::Eligible
                },
            )
        })
        .collect();
    coordinator
        .submit_language_outcomes(primary.wave_id(), outcomes)
        .expect("eleven failures remain below the early-stop bound");
    let replacements = coordinator
        .pending_language_wave()
        .expect("round-ten replacements")
        .clone();
    assert_eq!(replacements.event_ids().len(), 11);

    assert!(matches!(
        coordinator
            .submit_language_outcomes(replacements.wave_id(), eligible(replacements.event_ids()),),
        Err(AdaptiveLearningError::PhasePaused(
            oracle_mvp::adaptive_learning::AdaptiveLearningFailure::FinalLanguageCeiling {
                wrong_language: 11,
                unique_presentations: 211,
            }
        ))
    ));
    assert_eq!(coordinator.progress(), AdaptiveLearningProgress::Paused);
    assert_eq!(coordinator.compact_controller().history().len(), 9);
    assert_eq!(coordinator.rbf_controller().history().len(), 9);
    assert_eq!(coordinator.language_totals().eligible_presentations(), 200);
}
