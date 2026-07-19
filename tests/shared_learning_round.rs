use std::collections::{BTreeMap, BTreeSet};

use oracle_mvp::candidate_order::{
    B16Boundary, CandidateOrderOracle, CandidateOrderOutcome, CandidateOrderPhase,
    CandidateOrderRequest, CandidateVectorCache, FrozenCandidateOrder,
    build_compact_candidate_order, build_rbf_candidate_order,
};
use oracle_mvp::fp32_oracle::{
    Fp32Candidate, SimilarNotesRequest, SimilarNotesResponse, SimilarNotesWaveMetrics,
    SimilarNotesWaveResponse, StoredNoteVector, VectorsForNotesResponse,
};
use oracle_mvp::personalizer_learning::{
    BatchCandidate, BatchRating, CandidateBatch, CompactLearningController,
    CompactLearningSettings, EvidenceNote, RbfLearningController, RbfLearningSettings, ScaleLevel,
};
use oracle_mvp::quota_resolution::{
    EventLanguageOutcome, LanguageEligibility, PersonalizerId, PresentationLedgerSnapshot,
    PriorPresentation, QuotaResolutionProgress, ResolvedQuota, SharedQuotaResolver,
};
use oracle_mvp::representation::EventId;
use oracle_mvp::shared_learning_round::{
    SharedLearningAuditEvent, SharedLearningRoundError, begin_shared_learning_round,
};
use oracle_mvp::snapshot::{Error as SnapshotError, Result as SnapshotResult};

const VERSION: &str = "representation-v1";

fn id(value: u16) -> EventId {
    let mut event_id = [0_u8; 32];
    event_id[..2].copy_from_slice(&value.to_le_bytes());
    event_id
}

fn vector(position: usize) -> Vec<f32> {
    let angle = (position as f32 + 1.0) * 0.001;
    vec![angle.cos(), angle.sin()]
}

fn evidence(event_id: EventId) -> EvidenceNote {
    EvidenceNote::new(event_id, vec![1.0, 0.0], 7).expect("test evidence")
}

fn compact_controller() -> CompactLearningController {
    CompactLearningController::new(
        CompactLearningSettings::new(VERSION, 0.5, 1.0, 2.0, ScaleLevel::Mass64)
            .expect("compact settings"),
        vec![evidence(id(1))],
    )
    .expect("compact controller")
}

fn rbf_controller() -> RbfLearningController {
    RbfLearningController::new(
        RbfLearningSettings::new(VERSION, 0.5, 1.0, 2.0).expect("RBF settings"),
        vec![evidence(id(2))],
    )
    .expect("RBF controller")
}

struct TestOracle {
    source: EventId,
    candidates: Vec<(EventId, Vec<f32>)>,
}

impl CandidateOrderOracle for TestOracle {
    fn representation_version(&self) -> &str {
        VERSION
    }

    fn similar_notes_wave(
        &mut self,
        requests: &[SimilarNotesRequest],
        representation_version: &str,
    ) -> SnapshotResult<SimilarNotesWaveResponse> {
        if representation_version != VERSION
            || requests
                != [SimilarNotesRequest {
                    note_id: self.source,
                    candidate_depth: 1_024,
                }]
        {
            return Err(SnapshotError::InvalidQuery(
                "unexpected test query".to_owned(),
            ));
        }
        let rows = u64::try_from(self.candidates.len() + 1)
            .map_err(|_| SnapshotError::Invariant("test row overflow".to_owned()))?;
        Ok(SimilarNotesWaveResponse {
            responses: vec![SimilarNotesResponse {
                representation_version: VERSION.to_owned(),
                represented_rows: rows,
                total_rows: rows,
                complete: true,
                candidates: self
                    .candidates
                    .iter()
                    .enumerate()
                    .map(|(offset, (event_id, _))| Fp32Candidate {
                        event_id: *event_id,
                        rank: offset + 1,
                        cosine_score: 1.0 - offset as f32 / 10_000.0,
                    })
                    .collect(),
            }],
            metrics: SimilarNotesWaveMetrics {
                source_loading_ns: 0,
                query_encoding_ns: 0,
                matrix_scan_ns: 0,
                result_merge_ns: 0,
                encoded_queries: 1,
                cache_hits: 0,
                matrix_passes: 1,
                scanned_rows: rows,
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
                "unexpected test representation".to_owned(),
            ));
        }
        let by_id = self
            .candidates
            .iter()
            .map(|(event_id, vector)| (*event_id, vector.clone()))
            .collect::<BTreeMap<_, _>>();
        let vectors = note_ids
            .iter()
            .map(|event_id| {
                Ok(StoredNoteVector {
                    event_id: *event_id,
                    vector: by_id
                        .get(event_id)
                        .cloned()
                        .ok_or_else(|| SnapshotError::EventNotFound(format!("{event_id:?}")))?,
                })
            })
            .collect::<SnapshotResult<Vec<_>>>()?;
        let rows = u64::try_from(self.candidates.len() + 1)
            .map_err(|_| SnapshotError::Invariant("test row overflow".to_owned()))?;
        Ok(VectorsForNotesResponse {
            representation_version: VERSION.to_owned(),
            represented_rows: rows,
            total_rows: rows,
            complete: true,
            lookup_elapsed_ns: 0,
            vectors,
        })
    }
}

fn frozen(outcome: CandidateOrderOutcome) -> FrozenCandidateOrder {
    match outcome {
        CandidateOrderOutcome::Frozen(order) => order,
        CandidateOrderOutcome::Insufficient(failure) => panic!(
            "test order accepted {} of {}",
            failure.accepted_count(),
            failure.required_count()
        ),
    }
}

fn compact_order(
    controller: &CompactLearningController,
    phase: CandidateOrderPhase,
    candidates: Vec<(EventId, Vec<f32>)>,
) -> FrozenCandidateOrder {
    let mut oracle = TestOracle {
        source: id(1),
        candidates,
    };
    let mut cache = CandidateVectorCache::new(VERSION).expect("compact cache");
    frozen(
        build_compact_candidate_order(
            controller,
            &mut oracle,
            &mut cache,
            &CandidateOrderRequest::new(
                phase,
                B16Boundary::new(VERSION, 0.0).expect("B16"),
                BTreeSet::new(),
            ),
        )
        .expect("compact order"),
    )
}

fn rbf_order(
    controller: &RbfLearningController,
    phase: CandidateOrderPhase,
    candidates: Vec<(EventId, Vec<f32>)>,
) -> FrozenCandidateOrder {
    let mut oracle = TestOracle {
        source: id(2),
        candidates,
    };
    let mut cache = CandidateVectorCache::new(VERSION).expect("RBF cache");
    frozen(
        build_rbf_candidate_order(
            controller,
            &mut oracle,
            &mut cache,
            &CandidateOrderRequest::new(
                phase,
                B16Boundary::new(VERSION, 0.0).expect("B16"),
                BTreeSet::new(),
            ),
        )
        .expect("RBF order"),
    )
}

fn compact_candidates(count: usize) -> Vec<(EventId, Vec<f32>)> {
    (0..count)
        .map(|position| {
            let event_id = match position {
                0 => id(100),
                1..=9 => id(100 + u16::try_from(position).expect("shared index")),
                _ => id(200 + u16::try_from(position).expect("compact index")),
            };
            (event_id, vector(position))
        })
        .collect()
}

fn rbf_candidates(count: usize) -> Vec<(EventId, Vec<f32>)> {
    (0..count)
        .map(|position| {
            let event_id = match position {
                1..=9 => id(100 + u16::try_from(position).expect("shared index")),
                _ => id(1_000 + u16::try_from(position).expect("RBF index")),
            };
            (event_id, vector(position))
        })
        .collect()
}

fn resolve_all_eligible(
    compact: FrozenCandidateOrder,
    rbf: FrozenCandidateOrder,
    ledger: PresentationLedgerSnapshot,
) -> ResolvedQuota {
    let mut resolver = SharedQuotaResolver::new(compact, rbf, ledger).expect("quota resolver");
    while resolver.progress() == QuotaResolutionProgress::AwaitingLanguage {
        let wave = resolver.pending_wave().expect("pending wave").clone();
        resolver
            .submit_language_outcomes(
                wave.wave_id(),
                wave.event_ids()
                    .iter()
                    .map(|event_id| {
                        EventLanguageOutcome::new(*event_id, LanguageEligibility::Eligible)
                    })
                    .collect(),
            )
            .expect("language outcomes");
    }
    resolver.into_result().expect("resolved quota")
}

fn resolve_with_wrong_language(
    compact: FrozenCandidateOrder,
    rbf: FrozenCandidateOrder,
    wrong_language_event_id: EventId,
) -> ResolvedQuota {
    let mut resolver = SharedQuotaResolver::new(compact, rbf, PresentationLedgerSnapshot::empty())
        .expect("quota resolver");
    while resolver.progress() == QuotaResolutionProgress::AwaitingLanguage {
        let wave = resolver.pending_wave().expect("pending wave").clone();
        resolver
            .submit_language_outcomes(
                wave.wave_id(),
                wave.event_ids()
                    .iter()
                    .map(|event_id| {
                        EventLanguageOutcome::new(
                            *event_id,
                            if *event_id == wrong_language_event_id {
                                LanguageEligibility::WrongLanguage
                            } else {
                                LanguageEligibility::Eligible
                            },
                        )
                    })
                    .collect(),
            )
            .expect("language outcomes");
    }
    resolver.into_result().expect("resolved quota")
}

fn learning_fixture(
    stored_compact_choice: bool,
) -> (
    CompactLearningController,
    RbfLearningController,
    ResolvedQuota,
) {
    let compact = compact_controller();
    let rbf = rbf_controller();
    let compact_order = compact_order(
        &compact,
        CandidateOrderPhase::Learning,
        compact_candidates(41),
    );
    let rbf_order = rbf_order(&rbf, CandidateOrderPhase::Learning, rbf_candidates(41));
    let ledger = if stored_compact_choice {
        PresentationLedgerSnapshot::new(BTreeMap::from([(
            id(100),
            PriorPresentation::rated_by([PersonalizerId::Rbf]).expect("stored selector"),
        )]))
        .expect("stored ledger")
    } else {
        PresentationLedgerSnapshot::empty()
    };
    let quota = resolve_all_eligible(compact_order, rbf_order, ledger);
    (compact, rbf, quota)
}

fn exact_ratings(event_ids: &[EventId]) -> Vec<BatchRating> {
    event_ids
        .iter()
        .map(|event_id| {
            BatchRating::new(*event_id, if *event_id == id(101) { 4 } else { 7 })
                .expect("valid rating")
        })
        .collect()
}

#[test]
fn begin_freezes_both_batches_before_accepting_the_exact_required_ratings() {
    let (mut compact, mut rbf, quota) = learning_fixture(true);
    let compact_ids = quota
        .compact_batch()
        .candidates()
        .iter()
        .map(BatchCandidate::event_id)
        .collect::<Vec<_>>();
    let rbf_ids = quota
        .rbf_batch()
        .candidates()
        .iter()
        .map(BatchCandidate::event_id)
        .collect::<Vec<_>>();

    let pending = begin_shared_learning_round(quota, &mut compact, &mut rbf)
        .expect("begin shared learning round");

    assert_eq!(pending.round(), 1);
    assert!(matches!(
        pending.audit().first(),
        Some(SharedLearningAuditEvent::BatchesFrozen {
            round: 1,
            compact_event_ids,
            rbf_event_ids,
        }) if compact_event_ids == &compact_ids && rbf_event_ids == &rbf_ids
    ));
    assert_eq!(pending.new_rating_event_ids().len(), 30);
    assert_eq!(pending.stored_rating_event_ids(), &[id(100)]);
    assert_eq!(pending.required_rating_event_ids().len(), 31);
    assert!(!pending.is_complete());
    let pending = match pending.finish() {
        Ok(_) => panic!("unfinished round must not produce a record"),
        Err(pending) => pending,
    };
    assert_eq!(pending.required_rating_event_ids().len(), 31);
    drop(pending);
    assert!(compact.pending_batch().is_none());
    assert!(rbf.pending_batch().is_none());
    assert!(compact.history().is_empty());
    assert!(rbf.history().is_empty());
}

#[test]
fn malformed_rating_sets_change_neither_personalizer_and_can_be_retried() {
    let (mut compact, mut rbf, quota) = learning_fixture(true);
    let mut pending = begin_shared_learning_round(quota, &mut compact, &mut rbf)
        .expect("begin shared learning round");
    let required = pending.required_rating_event_ids().to_vec();
    let original_audit = pending.audit().to_vec();

    let mut missing = exact_ratings(&required);
    let missing_id = missing.pop().expect("one rating").event_id();
    assert_eq!(
        pending.submit_ratings(missing),
        Err(SharedLearningRoundError::MissingRating {
            event_id: missing_id
        })
    );
    let mut duplicate = exact_ratings(&required);
    duplicate.push(duplicate[0]);
    assert_eq!(
        pending.submit_ratings(duplicate),
        Err(SharedLearningRoundError::DuplicateRating {
            event_id: required[0]
        })
    );
    let mut unexpected = exact_ratings(&required);
    unexpected.push(BatchRating::new(id(60_000), 7).expect("extra rating"));
    assert_eq!(
        pending.submit_ratings(unexpected),
        Err(SharedLearningRoundError::UnexpectedRating {
            event_id: id(60_000)
        })
    );
    assert_eq!(pending.audit(), original_audit);
    assert!(!pending.is_complete());

    pending
        .submit_ratings(exact_ratings(&required))
        .expect("retry exact ratings");
    let record = match pending.finish() {
        Ok(record) => record,
        Err(_) => panic!("completed round must finish"),
    };

    assert_eq!(compact.history().len(), 1);
    assert_eq!(rbf.history().len(), 1);
    assert!(compact.pending_batch().is_none());
    assert!(rbf.pending_batch().is_none());
    assert_eq!(record.compact_round(), &compact.history()[0]);
    assert_eq!(record.rbf_round(), &rbf.history()[0]);
}

#[test]
fn valid_ratings_are_routed_once_and_ledgered_only_for_new_presentations() {
    let run = |reverse: bool| {
        let (mut compact, mut rbf, quota) = learning_fixture(true);
        let mut pending = begin_shared_learning_round(quota, &mut compact, &mut rbf)
            .expect("begin shared learning round");
        let mut ratings = exact_ratings(pending.required_rating_event_ids());
        if reverse {
            ratings.reverse();
        }
        pending.submit_ratings(ratings).expect("complete round");
        let record = match pending.finish() {
            Ok(record) => record,
            Err(_) => panic!("completed round must finish"),
        };
        (record, compact, rbf)
    };

    let (forward, compact, rbf) = run(false);
    let (reversed, _, _) = run(true);
    assert_eq!(forward, reversed);

    let shared_rating = forward
        .ratings()
        .iter()
        .find(|rating| rating.event_id() == id(101))
        .expect("shared rating");
    assert_eq!(shared_rating.rating().value(), 4);
    let shared_route = forward
        .quota_metadata()
        .new_rating_routes()
        .iter()
        .find(|route| route.event_id() == id(101))
        .expect("shared route");
    assert_eq!(
        shared_route.selected_by(),
        &BTreeSet::from([PersonalizerId::Compact, PersonalizerId::Rbf])
    );
    let stored = forward
        .quota_metadata()
        .stored_rating_reuse_routes()
        .iter()
        .find(|route| route.event_id() == id(100))
        .expect("stored route");
    assert_eq!(stored.personalizer(), PersonalizerId::Compact);

    let compact_private = id(210);
    let rbf_private = id(1_000);
    assert!(
        forward
            .compact_round()
            .outcomes()
            .iter()
            .any(|outcome| outcome.event_id() == compact_private)
    );
    assert!(
        forward
            .rbf_round()
            .outcomes()
            .iter()
            .all(|outcome| outcome.event_id() != compact_private)
    );
    assert!(
        forward
            .rbf_round()
            .outcomes()
            .iter()
            .any(|outcome| outcome.event_id() == rbf_private)
    );
    assert!(
        forward
            .compact_round()
            .outcomes()
            .iter()
            .all(|outcome| outcome.event_id() != rbf_private)
    );

    assert_eq!(
        forward
            .compact_round()
            .outcomes()
            .iter()
            .find(|outcome| outcome.event_id() == id(101))
            .expect("compact shared outcome")
            .target(),
        0.0
    );
    assert_eq!(
        forward
            .rbf_round()
            .outcomes()
            .iter()
            .find(|outcome| outcome.event_id() == id(101))
            .expect("RBF shared outcome")
            .target(),
        0.0
    );
    assert_eq!(compact.evidence_count(), 21);
    assert_eq!(rbf.evidence_count(), 21);
    assert_eq!(forward.presentation_ledger_entries().len(), 30);
    assert!(!forward.presentation_ledger_entries().contains_key(&id(100)));
    assert_eq!(
        forward.presentation_ledger_entries().get(&id(101)),
        Some(
            &PriorPresentation::rated_by([PersonalizerId::Compact, PersonalizerId::Rbf,])
                .expect("shared ledger entry")
        )
    );
    assert!(matches!(
        forward.audit().first(),
        Some(SharedLearningAuditEvent::BatchesFrozen { round: 1, .. })
    ));
    assert!(matches!(
        forward.audit().last(),
        Some(SharedLearningAuditEvent::RoundCompleted { round: 1, .. })
    ));
}

#[test]
fn wrong_language_presentations_need_no_rating_and_remain_in_the_ledger() {
    let mut compact = compact_controller();
    let mut rbf = rbf_controller();
    let wrong_language_event_id = id(210);
    let quota = resolve_with_wrong_language(
        compact_order(
            &compact,
            CandidateOrderPhase::Learning,
            compact_candidates(41),
        ),
        rbf_order(&rbf, CandidateOrderPhase::Learning, rbf_candidates(41)),
        wrong_language_event_id,
    );
    let mut pending = begin_shared_learning_round(quota, &mut compact, &mut rbf)
        .expect("begin shared learning round");
    assert!(
        !pending
            .required_rating_event_ids()
            .contains(&wrong_language_event_id)
    );
    let ratings = exact_ratings(pending.required_rating_event_ids());
    pending.submit_ratings(ratings).expect("complete round");
    let record = match pending.finish() {
        Ok(record) => record,
        Err(_) => panic!("completed round must finish"),
    };

    assert_eq!(
        record
            .presentation_ledger_entries()
            .get(&wrong_language_event_id),
        Some(&PriorPresentation::WrongLanguage)
    );
    assert!(
        record
            .compact_round()
            .outcomes()
            .iter()
            .chain(record.rbf_round().outcomes())
            .all(|outcome| outcome.event_id() != wrong_language_event_id)
    );
}

#[test]
fn binding_or_phase_errors_reject_before_either_controller_freezes() {
    let (mut compact, _, quota) = learning_fixture(false);
    let mut wrong_rbf = RbfLearningController::new(
        RbfLearningSettings::new(VERSION, 0.5, 1.0, 2.0).expect("RBF settings"),
        vec![evidence(id(3))],
    )
    .expect("wrong RBF controller");
    let error = match begin_shared_learning_round(quota, &mut compact, &mut wrong_rbf) {
        Ok(_) => panic!("mismatched evidence must fail"),
        Err(error) => error,
    };
    assert!(matches!(
        error,
        SharedLearningRoundError::EvidenceIdentityMismatch {
            personalizer: PersonalizerId::Rbf
        }
    ));
    assert!(compact.pending_batch().is_none());
    assert!(wrong_rbf.pending_batch().is_none());
    assert!(compact.history().is_empty());
    assert!(wrong_rbf.history().is_empty());

    let (_, mut rbf, quota) = learning_fixture(false);
    let mut wrong_compact = CompactLearningController::new(
        CompactLearningSettings::new(VERSION, 0.5, 1.0, 2.0, ScaleLevel::Mass256)
            .expect("compact settings"),
        vec![evidence(id(1))],
    )
    .expect("wrong Compact controller");
    let error = match begin_shared_learning_round(quota, &mut wrong_compact, &mut rbf) {
        Ok(_) => panic!("mismatched active parameters must fail"),
        Err(error) => error,
    };
    assert_eq!(
        error,
        SharedLearningRoundError::ActiveParametersMismatch {
            personalizer: PersonalizerId::Compact,
        }
    );
    assert!(wrong_compact.pending_batch().is_none());
    assert!(rbf.pending_batch().is_none());

    let (mut compact, mut rbf, quota) = learning_fixture(false);
    let existing_rbf_batch = rbf
        .freeze_batch(
            CandidateBatch::new(
                VERSION,
                vec![BatchCandidate::new(id(60_000), vector(500)).expect("pending candidate")],
            )
            .expect("pending batch"),
        )
        .expect("freeze existing RBF batch")
        .clone();
    let error = match begin_shared_learning_round(quota, &mut compact, &mut rbf) {
        Ok(_) => panic!("an existing pending batch must fail"),
        Err(error) => error,
    };
    assert_eq!(
        error,
        SharedLearningRoundError::BatchPending {
            personalizer: PersonalizerId::Rbf,
        }
    );
    assert!(compact.pending_batch().is_none());
    assert_eq!(rbf.pending_batch(), Some(&existing_rbf_batch));

    let mut compact = compact_controller();
    compact
        .freeze_batch(
            CandidateBatch::new(
                VERSION,
                vec![BatchCandidate::new(id(50), vector(500)).expect("round-one candidate")],
            )
            .expect("round-one batch"),
        )
        .expect("freeze round one");
    compact
        .complete_batch(vec![BatchRating::new(id(50), 1).expect("round-one rating")])
        .expect("complete round one");
    let mut rbf = rbf_controller();
    let quota = resolve_all_eligible(
        compact_order(
            &compact,
            CandidateOrderPhase::Learning,
            compact_candidates(41),
        ),
        rbf_order(&rbf, CandidateOrderPhase::Learning, rbf_candidates(41)),
        PresentationLedgerSnapshot::empty(),
    );
    let error = match begin_shared_learning_round(quota, &mut compact, &mut rbf) {
        Ok(_) => panic!("different next rounds must fail"),
        Err(error) => error,
    };
    assert_eq!(
        error,
        SharedLearningRoundError::RoundMismatch {
            compact_round: 2,
            rbf_round: 1,
        }
    );
    assert!(compact.pending_batch().is_none());
    assert!(rbf.pending_batch().is_none());

    let mut compact = compact_controller();
    let mut rbf = rbf_controller();
    let quota = resolve_all_eligible(
        compact_order(
            &compact,
            CandidateOrderPhase::Final,
            compact_candidates(221),
        ),
        rbf_order(&rbf, CandidateOrderPhase::Final, rbf_candidates(221)),
        PresentationLedgerSnapshot::empty(),
    );
    let error = match begin_shared_learning_round(quota, &mut compact, &mut rbf) {
        Ok(_) => panic!("final phase must fail"),
        Err(error) => error,
    };
    assert_eq!(
        error,
        SharedLearningRoundError::InvalidPhase(CandidateOrderPhase::Final)
    );
    assert!(compact.pending_batch().is_none());
    assert!(rbf.pending_batch().is_none());
}
