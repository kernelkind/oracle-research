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
    CompactLearningController, CompactLearningSettings, EvidenceNote, RbfLearningController,
    RbfLearningSettings, ScaleLevel,
};
use oracle_mvp::quota_resolution::{
    ChoiceRatingSource, ClaimOrigin, EventLanguageOutcome, LanguageEligibility, PersonalizerId,
    PresentationLedgerSnapshot, PriorPresentation, QuotaAuditEvent, QuotaResolutionError,
    QuotaResolutionFailure, QuotaResolutionProgress, SharedQuotaResolver,
};
use oracle_mvp::representation::EventId;
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

fn candidates(start: u16, count: usize) -> Vec<(EventId, Vec<f32>)> {
    candidates_at(start, count, 0)
}

fn candidates_at(start: u16, count: usize, position_offset: usize) -> Vec<(EventId, Vec<f32>)> {
    (0..count)
        .map(|position| {
            (
                id(start + u16::try_from(position).expect("test candidate index")),
                vector(position + position_offset),
            )
        })
        .collect()
}

fn candidate(event_id: u16, position: usize) -> (EventId, Vec<f32>) {
    (id(event_id), vector(position))
}

fn descending_candidates(high: u16, count: usize) -> Vec<(EventId, Vec<f32>)> {
    (0..count)
        .map(|position| {
            (
                id(high - u16::try_from(position).expect("test candidate index")),
                vector(position),
            )
        })
        .collect()
}

fn eligible_outcomes(event_ids: &[EventId]) -> Vec<EventLanguageOutcome> {
    event_ids
        .iter()
        .map(|event_id| EventLanguageOutcome::new(*event_id, LanguageEligibility::Eligible))
        .collect()
}

fn batch_ids(batch: &oracle_mvp::personalizer_learning::CandidateBatch) -> Vec<EventId> {
    batch
        .candidates()
        .iter()
        .map(oracle_mvp::personalizer_learning::BatchCandidate::event_id)
        .collect()
}

fn resolver_error(
    result: Result<SharedQuotaResolver, QuotaResolutionError>,
) -> QuotaResolutionError {
    match result {
        Ok(_) => panic!("expected quota-resolution error"),
        Err(error) => error,
    }
}

struct TestOracle {
    version: String,
    source: EventId,
    candidates: Vec<(EventId, Vec<f32>)>,
}

impl CandidateOrderOracle for TestOracle {
    fn representation_version(&self) -> &str {
        &self.version
    }

    fn similar_notes_wave(
        &mut self,
        requests: &[SimilarNotesRequest],
        representation_version: &str,
    ) -> SnapshotResult<SimilarNotesWaveResponse> {
        if representation_version != self.version
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
                representation_version: self.version.clone(),
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
        if representation_version != self.version {
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
            representation_version: self.version.clone(),
            represented_rows: rows,
            total_rows: rows,
            complete: true,
            lookup_elapsed_ns: 0,
            vectors,
        })
    }
}

fn evidence(event_id: EventId) -> EvidenceNote {
    EvidenceNote::new(event_id, vec![1.0, 0.0], 7).expect("test evidence")
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
    phase: CandidateOrderPhase,
    version: &str,
    candidates: Vec<(EventId, Vec<f32>)>,
) -> FrozenCandidateOrder {
    compact_order_with_b16(phase, version, candidates, 0.0)
}

fn compact_order_with_b16(
    phase: CandidateOrderPhase,
    version: &str,
    candidates: Vec<(EventId, Vec<f32>)>,
    b16: f64,
) -> FrozenCandidateOrder {
    let source = id(1);
    let controller = CompactLearningController::new(
        CompactLearningSettings::new(version, 0.5, 1.0, 2.0, ScaleLevel::Mass64)
            .expect("compact settings"),
        vec![evidence(source)],
    )
    .expect("compact controller");
    let mut oracle = TestOracle {
        version: version.to_owned(),
        source,
        candidates,
    };
    let mut cache = CandidateVectorCache::new(version).expect("compact cache");
    frozen(
        build_compact_candidate_order(
            &controller,
            &mut oracle,
            &mut cache,
            &CandidateOrderRequest::new(
                phase,
                B16Boundary::new(version, b16).expect("B16"),
                Default::default(),
            ),
        )
        .expect("compact order"),
    )
}

fn rbf_order(
    phase: CandidateOrderPhase,
    version: &str,
    candidates: Vec<(EventId, Vec<f32>)>,
) -> FrozenCandidateOrder {
    rbf_order_with_b16(phase, version, candidates, 0.0)
}

fn rbf_order_with_b16(
    phase: CandidateOrderPhase,
    version: &str,
    candidates: Vec<(EventId, Vec<f32>)>,
    b16: f64,
) -> FrozenCandidateOrder {
    let source = id(2);
    let controller = RbfLearningController::new(
        RbfLearningSettings::new(version, 0.5, 1.0, 2.0).expect("RBF settings"),
        vec![evidence(source)],
    )
    .expect("RBF controller");
    let mut oracle = TestOracle {
        version: version.to_owned(),
        source,
        candidates,
    };
    let mut cache = CandidateVectorCache::new(version).expect("RBF cache");
    frozen(
        build_rbf_candidate_order(
            &controller,
            &mut oracle,
            &mut cache,
            &CandidateOrderRequest::new(
                phase,
                B16Boundary::new(version, b16).expect("B16"),
                Default::default(),
            ),
        )
        .expect("RBF order"),
    )
}

#[test]
fn disjoint_learning_claims_resolve_to_two_exact_batches() {
    let compact = compact_order(
        CandidateOrderPhase::Learning,
        VERSION,
        descending_candidates(140, 41),
    );
    let rbf = rbf_order(
        CandidateOrderPhase::Learning,
        VERSION,
        candidates(1_000, 41),
    );
    let mut resolver = SharedQuotaResolver::new(compact, rbf, PresentationLedgerSnapshot::empty())
        .expect("quota resolver");
    assert_eq!(
        resolver.progress(),
        QuotaResolutionProgress::AwaitingLanguage
    );
    let wave = resolver.pending_wave().expect("initial wave").clone();
    assert_eq!(wave.event_ids().len(), 40);

    resolver
        .submit_language_outcomes(
            wave.wave_id(),
            wave.event_ids()
                .iter()
                .rev()
                .map(|event_id| EventLanguageOutcome::new(*event_id, LanguageEligibility::Eligible))
                .collect(),
        )
        .expect("language outcomes");

    assert_eq!(resolver.progress(), QuotaResolutionProgress::Complete);
    let result = resolver.into_result().expect("resolved quotas");
    assert_eq!(result.compact_batch().candidates().len(), 20);
    assert_eq!(result.rbf_batch().candidates().len(), 20);
    assert_eq!(
        batch_ids(result.compact_batch()),
        (121..=140).rev().map(id).collect::<Vec<_>>()
    );
    assert_eq!(result.presentation_ledger_delta().len(), 40);
    assert_eq!(result.language_delta().eligible_presentations(), 40);
    assert_eq!(result.language_delta().wrong_language_presentations(), 0);
    assert_eq!(
        result.presentation_ledger_delta().outcomes(),
        wave.event_ids()
            .iter()
            .map(|event_id| { EventLanguageOutcome::new(*event_id, LanguageEligibility::Eligible) })
            .collect::<Vec<_>>()
    );
    let compact_ids = batch_ids(result.compact_batch());
    let rbf_ids = batch_ids(result.rbf_batch());
    let mut expected_audit = Vec::new();
    for (personalizer, event_ids) in [
        (PersonalizerId::Compact, &compact_ids),
        (PersonalizerId::Rbf, &rbf_ids),
    ] {
        expected_audit.extend(event_ids.iter().enumerate().map(|(order_index, event_id)| {
            QuotaAuditEvent::Claimed {
                personalizer,
                event_id: *event_id,
                order_index,
                origin: ClaimOrigin::Primary,
            }
        }));
    }
    expected_audit.push(QuotaAuditEvent::PresentationWaveFrozen {
        wave_id: wave.wave_id(),
        event_ids: wave.event_ids().to_vec(),
    });
    expected_audit.extend(wave.event_ids().iter().map(|event_id| {
        QuotaAuditEvent::LanguageRecorded {
            wave_id: wave.wave_id(),
            event_id: *event_id,
            eligibility: LanguageEligibility::Eligible,
        }
    }));
    expected_audit.extend(wave.event_ids().iter().map(|event_id| {
        let (personalizer, order_index) = compact_ids
            .iter()
            .position(|candidate| candidate == event_id)
            .map(|index| (PersonalizerId::Compact, index))
            .or_else(|| {
                rbf_ids
                    .iter()
                    .position(|candidate| candidate == event_id)
                    .map(|index| (PersonalizerId::Rbf, index))
            })
            .expect("disjoint batch event");
        QuotaAuditEvent::Accepted {
            personalizer,
            event_id: *event_id,
            order_index,
            rating_source: ChoiceRatingSource::NewRating {
                first_presentation_wave: wave.wave_id(),
            },
        }
    }));
    assert_eq!(result.audit(), expected_audit);
    let (compact, rbf, metadata) = result.into_parts();
    assert_eq!(compact.personalizer(), PersonalizerId::Compact);
    assert_eq!(rbf.personalizer(), PersonalizerId::Rbf);
    let (compact_order, compact_batch) = compact.into_parts();
    let (rbf_order, rbf_batch) = rbf.into_parts();
    assert_eq!(
        compact_order.attempt().phase(),
        CandidateOrderPhase::Learning
    );
    assert_eq!(rbf_order.attempt().phase(), CandidateOrderPhase::Learning);
    assert_eq!(compact_batch.candidates().len(), 20);
    assert_eq!(rbf_batch.candidates().len(), 20);
    assert_eq!(metadata.presentation_ledger_delta().len(), 40);
}

#[test]
fn overlapping_claims_are_presented_once_and_routed_to_both_batches() {
    let compact_candidates = candidates(100, 41);
    let mut rbf_candidates = compact_candidates[..10].to_vec();
    rbf_candidates.extend(candidates_at(1_000, 31, 10));
    let compact = compact_order(CandidateOrderPhase::Learning, VERSION, compact_candidates);
    let rbf = rbf_order(CandidateOrderPhase::Learning, VERSION, rbf_candidates);
    let mut resolver = SharedQuotaResolver::new(compact, rbf, PresentationLedgerSnapshot::empty())
        .expect("quota resolver");
    let wave = resolver.pending_wave().expect("initial wave").clone();
    assert_eq!(wave.event_ids().len(), 30);

    resolver
        .submit_language_outcomes(wave.wave_id(), eligible_outcomes(wave.event_ids()))
        .expect("language outcomes");
    let result = resolver.into_result().expect("resolved quotas");

    assert_eq!(result.presentation_ledger_delta().len(), 30);
    assert_eq!(result.compact_batch().candidates().len(), 20);
    assert_eq!(result.rbf_batch().candidates().len(), 20);
    assert!(result.stored_rating_reuse_routes().is_empty());
    assert_eq!(result.new_rating_routes().len(), 30);
    let compact_ids = batch_ids(result.compact_batch());
    let rbf_ids = batch_ids(result.rbf_batch());
    for route in result.new_rating_routes() {
        let mut expected = BTreeSet::new();
        if compact_ids.contains(&route.event_id()) {
            expected.insert(PersonalizerId::Compact);
        }
        if rbf_ids.contains(&route.event_id()) {
            expected.insert(PersonalizerId::Rbf);
        }
        assert_eq!(route.selected_by(), &expected);
    }
    for shared_id in 100..110 {
        let route = result
            .new_rating_routes()
            .iter()
            .find(|route| route.event_id() == id(shared_id))
            .expect("shared rating route");
        assert_eq!(
            route.selected_by().iter().copied().collect::<Vec<_>>(),
            vec![PersonalizerId::Compact, PersonalizerId::Rbf]
        );
    }
}

#[test]
fn wrong_language_promotions_reuse_an_already_presented_eligible_event() {
    let mut compact_candidates = vec![candidate(100, 0)];
    compact_candidates.extend(candidates_at(101, 19, 1));
    compact_candidates.push(candidate(200, 20));
    compact_candidates.push(candidate(300, 21));
    compact_candidates.extend(candidates_at(201, 19, 22));

    let mut rbf_candidates = vec![candidate(100, 0)];
    rbf_candidates.extend(candidates_at(1_000, 19, 1));
    rbf_candidates.push(candidate(300, 21));
    rbf_candidates.extend(candidates_at(1_100, 20, 22));

    let compact = compact_order(CandidateOrderPhase::Learning, VERSION, compact_candidates);
    let rbf = rbf_order(CandidateOrderPhase::Learning, VERSION, rbf_candidates);
    let mut resolver = SharedQuotaResolver::new(compact, rbf, PresentationLedgerSnapshot::empty())
        .expect("quota resolver");

    let first = resolver.pending_wave().expect("initial wave").clone();
    assert_eq!(first.event_ids().len(), 39);
    resolver
        .submit_language_outcomes(
            first.wave_id(),
            first
                .event_ids()
                .iter()
                .rev()
                .map(|event_id| {
                    EventLanguageOutcome::new(
                        *event_id,
                        if *event_id == id(100) {
                            LanguageEligibility::WrongLanguage
                        } else {
                            LanguageEligibility::Eligible
                        },
                    )
                })
                .collect(),
        )
        .expect("initial outcomes");

    let second = resolver.pending_wave().expect("promotion wave").clone();
    assert_eq!(second.event_ids(), &[id(200), id(300)]);
    resolver
        .submit_language_outcomes(
            second.wave_id(),
            vec![
                EventLanguageOutcome::new(id(300), LanguageEligibility::Eligible),
                EventLanguageOutcome::new(id(200), LanguageEligibility::WrongLanguage),
            ],
        )
        .expect("promotion outcomes");

    assert_eq!(resolver.progress(), QuotaResolutionProgress::Complete);
    let result = resolver.into_result().expect("resolved quotas");
    assert_eq!(result.presentation_ledger_delta().len(), 41);
    assert_eq!(result.language_delta().eligible_presentations(), 39);
    assert_eq!(result.language_delta().wrong_language_presentations(), 2);
    let mut expected_compact = (101..120).map(id).collect::<Vec<_>>();
    expected_compact.push(id(300));
    let mut expected_rbf = (1_000..1_019).map(id).collect::<Vec<_>>();
    expected_rbf.push(id(300));
    assert_eq!(batch_ids(result.compact_batch()), expected_compact);
    assert_eq!(batch_ids(result.rbf_batch()), expected_rbf);
    assert_eq!(
        result
            .compact_batch()
            .candidates()
            .last()
            .expect("choice")
            .vector(),
        vector(21)
    );
    assert_eq!(result.new_rating_routes().len(), 39);
    let shared_route = result
        .new_rating_routes()
        .iter()
        .find(|route| route.event_id() == id(300))
        .expect("shared promotion route");
    assert_eq!(
        shared_route
            .selected_by()
            .iter()
            .copied()
            .collect::<Vec<_>>(),
        vec![PersonalizerId::Compact, PersonalizerId::Rbf]
    );

    let relevant_audit = result
        .audit()
        .iter()
        .filter(|entry| match entry {
            QuotaAuditEvent::Claimed { event_id, .. }
            | QuotaAuditEvent::LanguageRecorded { event_id, .. }
            | QuotaAuditEvent::Accepted { event_id, .. }
            | QuotaAuditEvent::WrongLanguageRejected { event_id, .. } => {
                [id(100), id(200), id(300)].contains(event_id)
            }
            QuotaAuditEvent::PresentationWaveFrozen { .. } => true,
            QuotaAuditEvent::Failed(_) => false,
        })
        .cloned()
        .collect::<Vec<_>>();
    assert_eq!(
        relevant_audit,
        vec![
            QuotaAuditEvent::Claimed {
                personalizer: PersonalizerId::Compact,
                event_id: id(100),
                order_index: 0,
                origin: ClaimOrigin::Primary,
            },
            QuotaAuditEvent::Claimed {
                personalizer: PersonalizerId::Rbf,
                event_id: id(100),
                order_index: 0,
                origin: ClaimOrigin::Primary,
            },
            QuotaAuditEvent::PresentationWaveFrozen {
                wave_id: first.wave_id(),
                event_ids: first.event_ids().to_vec(),
            },
            QuotaAuditEvent::LanguageRecorded {
                wave_id: first.wave_id(),
                event_id: id(100),
                eligibility: LanguageEligibility::WrongLanguage,
            },
            QuotaAuditEvent::WrongLanguageRejected {
                personalizer: PersonalizerId::Compact,
                event_id: id(100),
                order_index: 0,
            },
            QuotaAuditEvent::Claimed {
                personalizer: PersonalizerId::Compact,
                event_id: id(200),
                order_index: 20,
                origin: ClaimOrigin::ReservePromotion {
                    replaced_event_id: id(100),
                    replaced_order_index: 0,
                },
            },
            QuotaAuditEvent::WrongLanguageRejected {
                personalizer: PersonalizerId::Rbf,
                event_id: id(100),
                order_index: 0,
            },
            QuotaAuditEvent::Claimed {
                personalizer: PersonalizerId::Rbf,
                event_id: id(300),
                order_index: 20,
                origin: ClaimOrigin::ReservePromotion {
                    replaced_event_id: id(100),
                    replaced_order_index: 0,
                },
            },
            QuotaAuditEvent::PresentationWaveFrozen {
                wave_id: second.wave_id(),
                event_ids: second.event_ids().to_vec(),
            },
            QuotaAuditEvent::LanguageRecorded {
                wave_id: second.wave_id(),
                event_id: id(200),
                eligibility: LanguageEligibility::WrongLanguage,
            },
            QuotaAuditEvent::LanguageRecorded {
                wave_id: second.wave_id(),
                event_id: id(300),
                eligibility: LanguageEligibility::Eligible,
            },
            QuotaAuditEvent::WrongLanguageRejected {
                personalizer: PersonalizerId::Compact,
                event_id: id(200),
                order_index: 20,
            },
            QuotaAuditEvent::Claimed {
                personalizer: PersonalizerId::Compact,
                event_id: id(300),
                order_index: 21,
                origin: ClaimOrigin::ReservePromotion {
                    replaced_event_id: id(200),
                    replaced_order_index: 20,
                },
            },
            QuotaAuditEvent::Accepted {
                personalizer: PersonalizerId::Rbf,
                event_id: id(300),
                order_index: 20,
                rating_source: ChoiceRatingSource::NewRating {
                    first_presentation_wave: second.wave_id(),
                },
            },
            QuotaAuditEvent::Accepted {
                personalizer: PersonalizerId::Compact,
                event_id: id(300),
                order_index: 21,
                rating_source: ChoiceRatingSource::NewRating {
                    first_presentation_wave: second.wave_id(),
                },
            },
        ]
    );
}

#[test]
fn learning_can_route_another_personalizers_stored_rating_without_redisplay() {
    let compact = compact_order(CandidateOrderPhase::Learning, VERSION, candidates(100, 41));
    let rbf = rbf_order(
        CandidateOrderPhase::Learning,
        VERSION,
        candidates(1_000, 41),
    );
    let mut entries = BTreeMap::new();
    entries.insert(
        id(100),
        PriorPresentation::rated_by([PersonalizerId::Rbf]).expect("prior rating"),
    );
    let ledger = PresentationLedgerSnapshot::new(entries).expect("ledger");
    let mut resolver = SharedQuotaResolver::new(compact, rbf, ledger).expect("quota resolver");

    let wave = resolver.pending_wave().expect("initial wave").clone();
    assert_eq!(wave.event_ids().len(), 39);
    assert!(!wave.event_ids().contains(&id(100)));
    resolver
        .submit_language_outcomes(wave.wave_id(), eligible_outcomes(wave.event_ids()))
        .expect("language outcomes");
    let result = resolver.into_result().expect("resolved quotas");

    assert_eq!(result.stored_rating_reuse_routes().len(), 1);
    assert_eq!(result.stored_rating_reuse_routes()[0].event_id(), id(100));
    assert_eq!(
        result.stored_rating_reuse_routes()[0].personalizer(),
        PersonalizerId::Compact
    );
}

#[test]
fn learning_rejects_own_prior_ratings_and_prior_language_failures() {
    let compact = compact_order(CandidateOrderPhase::Learning, VERSION, candidates(100, 41));
    let rbf = rbf_order(
        CandidateOrderPhase::Learning,
        VERSION,
        candidates(1_000, 41),
    );
    let mut entries = BTreeMap::new();
    entries.insert(
        id(100),
        PriorPresentation::rated_by([PersonalizerId::Compact]).expect("prior rating"),
    );
    assert_eq!(
        resolver_error(SharedQuotaResolver::new(
            compact,
            rbf,
            PresentationLedgerSnapshot::new(entries).expect("ledger"),
        )),
        QuotaResolutionError::OwnPriorRatingInLearningOrder {
            personalizer: PersonalizerId::Compact,
            event_id: id(100),
        }
    );

    let compact = compact_order(CandidateOrderPhase::Learning, VERSION, candidates(100, 41));
    let rbf = rbf_order(
        CandidateOrderPhase::Learning,
        VERSION,
        candidates(1_000, 41),
    );
    let mut entries = BTreeMap::new();
    entries.insert(id(100), PriorPresentation::WrongLanguage);
    assert_eq!(
        resolver_error(SharedQuotaResolver::new(
            compact,
            rbf,
            PresentationLedgerSnapshot::new(entries).expect("ledger"),
        )),
        QuotaResolutionError::PriorWrongLanguageInLearningOrder { event_id: id(100) }
    );
}

#[test]
fn final_resolution_requires_fresh_complete_orders_and_builds_exact_batches() {
    let compact = compact_order(CandidateOrderPhase::Final, VERSION, candidates(10_000, 221));
    let rbf = rbf_order(CandidateOrderPhase::Final, VERSION, candidates(20_000, 221));
    let mut resolver = SharedQuotaResolver::new(compact, rbf, PresentationLedgerSnapshot::empty())
        .expect("quota resolver");
    let wave = resolver.pending_wave().expect("final wave").clone();
    assert_eq!(wave.event_ids().len(), 400);
    resolver
        .submit_language_outcomes(wave.wave_id(), eligible_outcomes(wave.event_ids()))
        .expect("final outcomes");
    let result = resolver.into_result().expect("resolved final quotas");
    assert_eq!(result.compact_batch().candidates().len(), 200);
    assert_eq!(result.rbf_batch().candidates().len(), 200);

    let compact = compact_order(CandidateOrderPhase::Final, VERSION, candidates(10_000, 221));
    let rbf = rbf_order(CandidateOrderPhase::Final, VERSION, candidates(20_000, 221));
    let mut entries = BTreeMap::new();
    entries.insert(
        id(10_220),
        PriorPresentation::rated_by([PersonalizerId::Rbf]).expect("prior rating"),
    );
    assert_eq!(
        resolver_error(SharedQuotaResolver::new(
            compact,
            rbf,
            PresentationLedgerSnapshot::new(entries).expect("ledger"),
        )),
        QuotaResolutionError::FinalOrderContainsPriorPresentation {
            event_id: id(10_220),
        }
    );
}

#[test]
fn reserve_exhaustion_is_terminal_but_keeps_every_displayed_outcome() {
    let compact = compact_order(CandidateOrderPhase::Learning, VERSION, candidates(100, 41));
    let rbf = rbf_order(
        CandidateOrderPhase::Learning,
        VERSION,
        candidates(1_000, 41),
    );
    let mut resolver = SharedQuotaResolver::new(compact, rbf, PresentationLedgerSnapshot::empty())
        .expect("quota resolver");
    let first = resolver.pending_wave().expect("initial wave").clone();
    resolver
        .submit_language_outcomes(
            first.wave_id(),
            first
                .event_ids()
                .iter()
                .map(|event_id| {
                    EventLanguageOutcome::new(
                        *event_id,
                        if (100..120).contains(&u16::from_le_bytes([event_id[0], event_id[1]])) {
                            LanguageEligibility::WrongLanguage
                        } else {
                            LanguageEligibility::Eligible
                        },
                    )
                })
                .collect(),
        )
        .expect("initial outcomes");

    let second = resolver.pending_wave().expect("reserve wave").clone();
    assert_eq!(second.event_ids().len(), 20);
    resolver
        .submit_language_outcomes(
            second.wave_id(),
            second
                .event_ids()
                .iter()
                .enumerate()
                .map(|(index, event_id)| {
                    EventLanguageOutcome::new(
                        *event_id,
                        if index < 2 {
                            LanguageEligibility::WrongLanguage
                        } else {
                            LanguageEligibility::Eligible
                        },
                    )
                })
                .collect(),
        )
        .expect("reserve outcomes are valid even though resolution fails");

    assert_eq!(resolver.progress(), QuotaResolutionProgress::Failed);
    assert_eq!(
        resolver.failure(),
        Some(&QuotaResolutionFailure::ReserveExhausted {
            personalizer: PersonalizerId::Compact,
            accepted_choices: 18,
            required_choices: 20,
        })
    );
    assert_eq!(resolver.presentation_ledger_delta().len(), 60);
    assert_eq!(resolver.language_delta().eligible_presentations(), 38);
    assert_eq!(resolver.language_delta().wrong_language_presentations(), 22);
    assert!(resolver.pending_wave().is_none());

    let report = match resolver.into_result().expect_err("terminal failure") {
        QuotaResolutionError::ResolutionFailed(report) => report,
        error => panic!("unexpected terminal error: {error}"),
    };
    assert_eq!(
        report.failure(),
        &QuotaResolutionFailure::ReserveExhausted {
            personalizer: PersonalizerId::Compact,
            accepted_choices: 18,
            required_choices: 20,
        }
    );
    assert_eq!(report.presentation_ledger_delta().len(), 60);
    assert_eq!(
        report
            .presentation_ledger_delta()
            .outcomes()
            .iter()
            .filter(|outcome| { outcome.eligibility() == LanguageEligibility::WrongLanguage })
            .count(),
        22
    );
    assert!(matches!(
        report.audit().last(),
        Some(QuotaAuditEvent::Failed(
            QuotaResolutionFailure::ReserveExhausted { .. }
        ))
    ));

    let replay_id = report
        .presentation_ledger_delta()
        .outcomes()
        .iter()
        .find(|outcome| outcome.eligibility() == LanguageEligibility::Eligible)
        .expect("eligible presentation")
        .event_id();
    let entries = report
        .presentation_ledger_delta()
        .outcomes()
        .iter()
        .map(|outcome| {
            (
                outcome.event_id(),
                match outcome.eligibility() {
                    LanguageEligibility::Eligible => PriorPresentation::EligibleUnrated,
                    LanguageEligibility::WrongLanguage => PriorPresentation::WrongLanguage,
                },
            )
        })
        .collect();
    let mut compact_candidates = vec![(replay_id, vector(0))];
    compact_candidates.extend(candidates_at(30_000, 40, 1));
    let compact = compact_order(CandidateOrderPhase::Learning, VERSION, compact_candidates);
    let rbf = rbf_order(
        CandidateOrderPhase::Learning,
        VERSION,
        candidates(40_000, 41),
    );
    assert_eq!(
        resolver_error(SharedQuotaResolver::new(
            compact,
            rbf,
            PresentationLedgerSnapshot::new(entries).expect("failed-run ledger"),
        )),
        QuotaResolutionError::PriorUnratedPresentationInLearningOrder {
            event_id: replay_id,
        }
    );
}

#[test]
fn malformed_language_submissions_do_not_mutate_the_pending_wave() {
    let compact = compact_order(CandidateOrderPhase::Learning, VERSION, candidates(100, 41));
    let rbf = rbf_order(
        CandidateOrderPhase::Learning,
        VERSION,
        candidates(1_000, 41),
    );
    let mut resolver = SharedQuotaResolver::new(compact, rbf, PresentationLedgerSnapshot::empty())
        .expect("quota resolver");
    let wave = resolver.pending_wave().expect("initial wave").clone();
    let original_audit = resolver.audit().to_vec();

    assert_eq!(
        resolver
            .submit_language_outcomes(wave.wave_id() + 1, eligible_outcomes(wave.event_ids()))
            .expect_err("wrong wave"),
        QuotaResolutionError::WaveIdMismatch {
            expected: wave.wave_id(),
            actual: wave.wave_id() + 1,
        }
    );
    let mut missing = eligible_outcomes(wave.event_ids());
    let missing_id = missing.pop().expect("outcome").event_id();
    assert_eq!(
        resolver
            .submit_language_outcomes(wave.wave_id(), missing)
            .expect_err("missing outcome"),
        QuotaResolutionError::MissingLanguageOutcome {
            event_id: missing_id,
        }
    );
    let duplicate_id = wave.event_ids()[0];
    let mut duplicate = eligible_outcomes(wave.event_ids());
    duplicate.push(EventLanguageOutcome::new(
        duplicate_id,
        LanguageEligibility::Eligible,
    ));
    assert_eq!(
        resolver
            .submit_language_outcomes(wave.wave_id(), duplicate)
            .expect_err("duplicate outcome"),
        QuotaResolutionError::DuplicateLanguageOutcome {
            event_id: duplicate_id,
        }
    );
    let mut unexpected = eligible_outcomes(wave.event_ids());
    unexpected[0] = EventLanguageOutcome::new(id(50_000), LanguageEligibility::Eligible);
    assert_eq!(
        resolver
            .submit_language_outcomes(wave.wave_id(), unexpected)
            .expect_err("unexpected outcome"),
        QuotaResolutionError::UnexpectedLanguageOutcome {
            event_id: id(50_000),
        }
    );

    assert_eq!(resolver.pending_wave(), Some(&wave));
    assert!(resolver.presentation_ledger_delta().is_empty());
    assert_eq!(resolver.language_delta().unique_presentations(), 0);
    assert_eq!(resolver.audit(), original_audit);

    resolver
        .submit_language_outcomes(wave.wave_id(), eligible_outcomes(wave.event_ids()))
        .expect("valid retry");
    assert_eq!(resolver.progress(), QuotaResolutionProgress::Complete);
}

#[test]
fn constructor_rejects_mixed_roles_phases_versions_and_shared_vectors() {
    let compact = compact_order(CandidateOrderPhase::Learning, VERSION, candidates(100, 41));
    let rbf = rbf_order(
        CandidateOrderPhase::Learning,
        VERSION,
        candidates(1_000, 41),
    );
    assert_eq!(
        resolver_error(SharedQuotaResolver::new(
            rbf,
            compact,
            PresentationLedgerSnapshot::empty(),
        )),
        QuotaResolutionError::CompactRoleMismatch
    );

    let compact = compact_order(CandidateOrderPhase::Learning, VERSION, candidates(100, 41));
    let compact_as_rbf = compact_order(
        CandidateOrderPhase::Learning,
        VERSION,
        candidates(1_000, 41),
    );
    assert_eq!(
        resolver_error(SharedQuotaResolver::new(
            compact,
            compact_as_rbf,
            PresentationLedgerSnapshot::empty(),
        )),
        QuotaResolutionError::RbfRoleMismatch
    );

    let compact = compact_order(CandidateOrderPhase::Learning, VERSION, candidates(100, 41));
    let rbf = rbf_order(CandidateOrderPhase::Final, VERSION, candidates(1_000, 221));
    assert_eq!(
        resolver_error(SharedQuotaResolver::new(
            compact,
            rbf,
            PresentationLedgerSnapshot::empty(),
        )),
        QuotaResolutionError::PhaseMismatch {
            compact: CandidateOrderPhase::Learning,
            rbf: CandidateOrderPhase::Final,
        }
    );

    let compact = compact_order_with_b16(
        CandidateOrderPhase::Learning,
        VERSION,
        candidates(100, 41),
        0.0,
    );
    let rbf = rbf_order_with_b16(
        CandidateOrderPhase::Learning,
        VERSION,
        candidates(1_000, 41),
        0.000_01,
    );
    assert_eq!(
        resolver_error(SharedQuotaResolver::new(
            compact,
            rbf,
            PresentationLedgerSnapshot::empty(),
        )),
        QuotaResolutionError::BoundaryMismatch
    );

    let compact = compact_order(CandidateOrderPhase::Learning, VERSION, candidates(100, 41));
    let rbf = rbf_order(
        CandidateOrderPhase::Learning,
        "representation-v2",
        candidates(1_000, 41),
    );
    assert_eq!(
        resolver_error(SharedQuotaResolver::new(
            compact,
            rbf,
            PresentationLedgerSnapshot::empty(),
        )),
        QuotaResolutionError::RepresentationVersionMismatch {
            compact: VERSION.to_owned(),
            rbf: "representation-v2".to_owned(),
        }
    );

    let compact = compact_order(CandidateOrderPhase::Learning, VERSION, candidates(100, 41));
    let mut rbf_candidates = vec![(id(100), vec![0.0, 1.0])];
    rbf_candidates.extend(candidates_at(1_000, 40, 1));
    let rbf = rbf_order(CandidateOrderPhase::Learning, VERSION, rbf_candidates);
    assert_eq!(
        resolver_error(SharedQuotaResolver::new(
            compact,
            rbf,
            PresentationLedgerSnapshot::empty(),
        )),
        QuotaResolutionError::SharedVectorMismatch { event_id: id(100) }
    );
}

#[test]
fn resolver_records_language_delta_without_enforcing_the_phase_wide_limit() {
    let compact = compact_order(CandidateOrderPhase::Learning, VERSION, candidates(100, 41));
    let rbf = rbf_order(
        CandidateOrderPhase::Learning,
        VERSION,
        candidates(1_000, 41),
    );
    let mut resolver = SharedQuotaResolver::new(compact, rbf, PresentationLedgerSnapshot::empty())
        .expect("quota resolver");
    let first = resolver.pending_wave().expect("initial wave").clone();
    resolver
        .submit_language_outcomes(
            first.wave_id(),
            first
                .event_ids()
                .iter()
                .enumerate()
                .map(|(index, event_id)| {
                    EventLanguageOutcome::new(
                        *event_id,
                        if index < 3 {
                            LanguageEligibility::WrongLanguage
                        } else {
                            LanguageEligibility::Eligible
                        },
                    )
                })
                .collect(),
        )
        .expect("initial outcomes");
    let replacements = resolver.pending_wave().expect("replacement wave").clone();
    resolver
        .submit_language_outcomes(
            replacements.wave_id(),
            eligible_outcomes(replacements.event_ids()),
        )
        .expect("replacement outcomes");

    assert_eq!(resolver.progress(), QuotaResolutionProgress::Complete);
    let result = resolver.into_result().expect("resolved quotas");
    assert_eq!(result.language_delta().wrong_language_presentations(), 3);
    assert_eq!(result.language_delta().unique_presentations(), 43);
}
