use std::collections::{BTreeMap, BTreeSet};

use oracle_mvp::candidate_order::{
    B16Boundary, CANDIDATE_DEPTH, CandidateDisposition, CandidateExclusionReason,
    CandidateOrderError, CandidateOrderOracle, CandidateOrderOutcome, CandidateOrderPhase,
    CandidateOrderRequest, CandidateVectorCache, build_compact_candidate_order,
    build_rbf_candidate_order,
};
use oracle_mvp::fp32_oracle::{
    Fp32Candidate, SimilarNotesRequest, SimilarNotesResponse, SimilarNotesWaveMetrics,
    SimilarNotesWaveResponse, StoredNoteVector, VectorsForNotesResponse,
};
use oracle_mvp::local_personalizer::{CompactSupportScorer, RatedVector, RbfKernelRidgeScorer};
use oracle_mvp::personalizer_learning::{
    BatchCandidate, BatchRating, CandidateBatch, CompactLearningController,
    CompactLearningSettings, EvidenceNote, RbfLearningController, RbfLearningSettings, ScaleLevel,
};
use oracle_mvp::representation::EventId;
use oracle_mvp::snapshot::{Error as SnapshotError, Result as SnapshotResult};
use sha2::{Digest, Sha256};

const VERSION: &str = "representation-v1";
const ROWS: u64 = 10_000;
const TOLERANCE: f64 = 1e-12;

fn id(value: u16) -> EventId {
    let mut event_id = [0_u8; 32];
    event_id[..2].copy_from_slice(&value.to_le_bytes());
    event_id
}

fn evidence(event_id: u16, vector: &[f32], rating: u8) -> EvidenceNote {
    EvidenceNote::new(id(event_id), vector.to_vec(), rating).expect("valid evidence")
}

fn compact_controller(notes: Vec<EvidenceNote>) -> CompactLearningController {
    CompactLearningController::new(
        CompactLearningSettings::new(VERSION, 0.5, 1.0, 2.0, ScaleLevel::Mass64)
            .expect("compact settings"),
        notes,
    )
    .expect("compact controller")
}

fn rbf_controller(notes: Vec<EvidenceNote>) -> RbfLearningController {
    RbfLearningController::new(
        RbfLearningSettings::new(VERSION, 0.5, 1.0, 2.0).expect("RBF settings"),
        notes,
    )
    .expect("RBF controller")
}

fn request(
    phase: CandidateOrderPhase,
    b16: f64,
    disallowed: impl IntoIterator<Item = EventId>,
) -> CandidateOrderRequest {
    CandidateOrderRequest::new(
        phase,
        B16Boundary::new(VERSION, b16).expect("B16 boundary"),
        disallowed.into_iter().collect(),
    )
}

fn frozen(outcome: CandidateOrderOutcome) -> oracle_mvp::candidate_order::FrozenCandidateOrder {
    match outcome {
        CandidateOrderOutcome::Frozen(frozen) => frozen,
        CandidateOrderOutcome::Insufficient(failure) => panic!(
            "expected a frozen order, accepted {} of {}",
            failure.accepted_count(),
            failure.required_count()
        ),
    }
}

fn assert_close(actual: f64, expected: f64) {
    assert!(
        (actual - expected).abs() <= TOLERANCE,
        "expected {expected}, got {actual}"
    );
}

fn candidate_tie(event_id: EventId) -> [u8; 32] {
    let mut hasher = Sha256::new();
    hasher.update(b"oracle-mvp-candidate-tie-v1\0");
    hasher.update(u64::try_from(VERSION.len()).unwrap().to_le_bytes());
    hasher.update(VERSION.as_bytes());
    hasher.update(event_id);
    hasher.finalize().into()
}

fn unit_angle(degrees: f32) -> Vec<f32> {
    let angle = degrees.to_radians();
    vec![angle.cos(), angle.sin()]
}

struct RecordingOracle {
    representation_version: String,
    responses: BTreeMap<EventId, Vec<Fp32Candidate>>,
    vectors: BTreeMap<EventId, Vec<f32>>,
    artifact_rows_override: Option<u64>,
    cached_sources: BTreeSet<EventId>,
    encoded_waves: Vec<Vec<SimilarNotesRequest>>,
    vector_requests: Vec<Vec<EventId>>,
    response_version_override: Option<String>,
    vector_version_override: Option<String>,
    vector_ids_override: Option<Vec<EventId>>,
}

impl RecordingOracle {
    fn new() -> Self {
        Self {
            representation_version: VERSION.to_owned(),
            responses: BTreeMap::new(),
            vectors: BTreeMap::new(),
            artifact_rows_override: None,
            cached_sources: BTreeSet::new(),
            encoded_waves: Vec::new(),
            vector_requests: Vec::new(),
            response_version_override: None,
            vector_version_override: None,
            vector_ids_override: None,
        }
    }

    fn add_response(&mut self, source: u16, candidate_ids: impl IntoIterator<Item = EventId>) {
        self.responses.insert(
            id(source),
            candidate_ids
                .into_iter()
                .enumerate()
                .map(|(offset, event_id)| Fp32Candidate {
                    event_id,
                    rank: offset + 1,
                    cosine_score: 1.0 - offset as f32 / 10_000.0,
                })
                .collect(),
        );
    }

    fn add_vector(&mut self, event_id: EventId, vector: Vec<f32>) {
        self.vectors.insert(event_id, vector);
    }

    fn artifact_rows(&self) -> u64 {
        self.artifact_rows_override.unwrap_or_else(|| {
            self.responses
                .values()
                .map(Vec::len)
                .max()
                .expect("at least one response") as u64
                + 1
        })
    }
}

impl CandidateOrderOracle for RecordingOracle {
    fn representation_version(&self) -> &str {
        &self.representation_version
    }

    fn similar_notes_wave(
        &mut self,
        requests: &[SimilarNotesRequest],
        representation_version: &str,
    ) -> SnapshotResult<SimilarNotesWaveResponse> {
        if representation_version != self.representation_version {
            return Err(SnapshotError::InvalidQuery(
                "unexpected representation version".to_owned(),
            ));
        }
        let misses = requests
            .iter()
            .copied()
            .filter(|request| !self.cached_sources.contains(&request.note_id))
            .collect::<Vec<_>>();
        if !misses.is_empty() {
            self.encoded_waves.push(misses.clone());
        }
        self.cached_sources
            .extend(requests.iter().map(|request| request.note_id));
        let artifact_rows = self.artifact_rows();
        let responses =
            requests
                .iter()
                .map(|request| {
                    Ok(SimilarNotesResponse {
                        representation_version: self
                            .response_version_override
                            .clone()
                            .unwrap_or_else(|| self.representation_version.clone()),
                        represented_rows: artifact_rows,
                        total_rows: artifact_rows,
                        complete: true,
                        candidates: self.responses.get(&request.note_id).cloned().ok_or_else(
                            || SnapshotError::EventNotFound(format!("{:?}", request.note_id)),
                        )?,
                    })
                })
                .collect::<SnapshotResult<Vec<_>>>()?;
        Ok(SimilarNotesWaveResponse {
            responses,
            metrics: SimilarNotesWaveMetrics {
                source_loading_ns: 0,
                query_encoding_ns: 0,
                matrix_scan_ns: 0,
                result_merge_ns: 0,
                encoded_queries: misses.len() as u64,
                cache_hits: (requests.len() - misses.len()) as u64,
                matrix_passes: u64::from(!misses.is_empty()),
                scanned_rows: if misses.is_empty() { 0 } else { artifact_rows },
                scan_block_rows: 4_096,
            },
        })
    }

    fn vectors_for_notes(
        &mut self,
        note_ids: &[EventId],
        representation_version: &str,
    ) -> SnapshotResult<VectorsForNotesResponse> {
        if representation_version != self.representation_version {
            return Err(SnapshotError::InvalidQuery(
                "unexpected representation version".to_owned(),
            ));
        }
        self.vector_requests.push(note_ids.to_vec());
        let artifact_rows = self.artifact_rows();
        let returned_ids = self
            .vector_ids_override
            .clone()
            .unwrap_or_else(|| note_ids.to_vec());
        let vectors =
            returned_ids
                .into_iter()
                .map(|event_id| {
                    Ok(StoredNoteVector {
                        event_id,
                        vector: self.vectors.get(&event_id).cloned().ok_or_else(|| {
                            SnapshotError::EventNotFound(format!("{:?}", event_id))
                        })?,
                    })
                })
                .collect::<SnapshotResult<Vec<_>>>()?;
        Ok(VectorsForNotesResponse {
            representation_version: self
                .vector_version_override
                .clone()
                .unwrap_or_else(|| self.representation_version.clone()),
            represented_rows: artifact_rows,
            total_rows: artifact_rows,
            complete: true,
            lookup_elapsed_ns: 0,
            vectors,
        })
    }
}

#[test]
fn learning_candidate_order_has_the_frozen_primary_and_reserve_bound() {
    let cache = CandidateVectorCache::new(VERSION).expect("representation-bound cache");

    assert_eq!(cache.representation_version(), VERSION);
    assert_eq!(CandidateOrderPhase::Learning.primary_count(), 20);
    assert_eq!(CandidateOrderPhase::Learning.reserve_count(), 21);
    assert_eq!(CandidateOrderPhase::Learning.accepted_count(), 41);
    assert_eq!(CandidateOrderPhase::Final.primary_count(), 200);
    assert_eq!(CandidateOrderPhase::Final.reserve_count(), 21);
    assert_eq!(CandidateOrderPhase::Final.accepted_count(), 221);
}

#[test]
fn discovery_uses_only_positive_sources_and_reuses_public_caches() {
    let controller = compact_controller(vec![
        evidence(1, &[1.0, 0.0], 7),
        evidence(2, &[1.0, 0.0], 5),
        evidence(3, &[0.0, 1.0], 4),
        evidence(4, &[0.0, 1.0], 3),
    ]);
    let ordinary_ids = (10..=51).map(id).collect::<Vec<_>>();
    let all_events = [id(1), id(2), id(3), id(4)]
        .into_iter()
        .chain(ordinary_ids.iter().copied())
        .collect::<Vec<_>>();
    let mut oracle = RecordingOracle::new();
    oracle.add_response(
        1,
        all_events.iter().copied().filter(|event| *event != id(1)),
    );
    oracle.add_response(
        2,
        all_events
            .iter()
            .copied()
            .rev()
            .filter(|event| *event != id(2)),
    );
    for event_id in &ordinary_ids {
        oracle.add_vector(*event_id, vec![1.0, 0.0]);
    }
    let disallowed = [id(3), id(10)];
    let request = request(CandidateOrderPhase::Learning, 0.0, disallowed);
    let mut cache = CandidateVectorCache::new(VERSION).expect("vector cache");
    let identity_before = controller.evidence_identity().clone();

    let first = frozen(
        build_compact_candidate_order(&controller, &mut oracle, &mut cache, &request)
            .expect("first frozen order"),
    );

    assert_eq!(oracle.encoded_waves.len(), 1);
    assert_eq!(
        oracle.encoded_waves[0]
            .iter()
            .map(|request| (request.note_id, request.candidate_depth))
            .collect::<Vec<_>>(),
        vec![(id(1), CANDIDATE_DEPTH), (id(2), CANDIDATE_DEPTH)]
    );
    assert_eq!(oracle.vector_requests.len(), 1);
    assert!(!oracle.vector_requests[0].contains(&id(2)));
    assert!(!oracle.vector_requests[0].contains(&id(3)));
    assert!(!oracle.vector_requests[0].contains(&id(4)));
    assert!(!oracle.vector_requests[0].contains(&id(10)));
    assert_eq!(cache.vector_count(), 41);
    assert_eq!(first.accepted().len(), 41);
    assert_eq!(first.primary().len(), 20);
    assert_eq!(first.reserve().len(), 21);
    assert_eq!(first.evidence_identity(), &identity_before);
    assert_eq!(controller.evidence_identity(), &identity_before);

    let shared = first
        .candidate_audit(id(20))
        .expect("shared candidate audit");
    assert_eq!(shared.attributions().len(), 2);
    assert!(
        shared
            .attributions()
            .iter()
            .all(|attribution| attribution.rank() > 0
                && attribution.cosine_score().is_finite()
                && attribution.response_identity_sha256().len() == 64)
    );
    assert_eq!(
        shared
            .attributions()
            .iter()
            .map(|attribution| attribution.source_event_id())
            .collect::<Vec<_>>(),
        vec![id(1), id(2)]
    );
    let evidence_and_disallowed = first.candidate_audit(id(3)).expect("excluded evidence");
    assert_eq!(
        evidence_and_disallowed.exclusion_reasons(),
        &[
            CandidateExclusionReason::ExistingEvidence,
            CandidateExclusionReason::CallerDisallowed,
        ]
    );

    let second = frozen(
        build_compact_candidate_order(&controller, &mut oracle, &mut cache, &request)
            .expect("cached frozen order"),
    );
    assert_eq!(oracle.encoded_waves.len(), 1);
    assert_eq!(oracle.vector_requests.len(), 1);
    assert_eq!(first.attempt().source_responses().len(), 2);
    assert_eq!(first.attempt().candidate_pool_identity_sha256().len(), 64);
    assert_eq!(
        first.attempt().candidate_pool_identity_sha256(),
        second.attempt().candidate_pool_identity_sha256()
    );
    assert_eq!(
        first
            .accepted()
            .iter()
            .map(|candidate| candidate.event_id())
            .collect::<Vec<_>>(),
        second
            .accepted()
            .iter()
            .map(|candidate| candidate.event_id())
            .collect::<Vec<_>>()
    );
}

#[test]
fn local_tie_order_is_independent_of_oracle_rank_and_cosine() {
    let controller = compact_controller(vec![evidence(1, &[1.0, 0.0], 7)]);
    let candidate_ids = (10..=50).map(id).collect::<Vec<_>>();
    let mut ascending = RecordingOracle::new();
    ascending.add_response(1, candidate_ids.iter().copied());
    let mut descending = RecordingOracle::new();
    descending.add_response(1, candidate_ids.iter().copied().rev());
    for event_id in &candidate_ids {
        ascending.add_vector(*event_id, vec![1.0, 0.0]);
        descending.add_vector(*event_id, vec![1.0, 0.0]);
    }
    let request = request(CandidateOrderPhase::Learning, 0.0, []);
    let mut ascending_cache = CandidateVectorCache::new(VERSION).expect("ascending cache");
    let mut descending_cache = CandidateVectorCache::new(VERSION).expect("descending cache");

    let ascending = frozen(
        build_compact_candidate_order(&controller, &mut ascending, &mut ascending_cache, &request)
            .expect("ascending order"),
    );
    let descending = frozen(
        build_compact_candidate_order(
            &controller,
            &mut descending,
            &mut descending_cache,
            &request,
        )
        .expect("descending order"),
    );

    assert_eq!(
        ascending
            .accepted()
            .iter()
            .map(|candidate| candidate.event_id())
            .collect::<Vec<_>>(),
        descending
            .accepted()
            .iter()
            .map(|candidate| candidate.event_id())
            .collect::<Vec<_>>()
    );
}

#[test]
fn compact_order_uses_the_active_scorer_and_strictly_excludes_zero() {
    let controller = compact_controller(vec![evidence(1, &[1.0, 0.0], 7)]);
    let positive_ids = (10..=50).map(id).collect::<Vec<_>>();
    let mut response_ids = positive_ids.clone();
    response_ids.push(id(51));
    let mut oracle = RecordingOracle::new();
    oracle.add_response(1, response_ids);
    for event_id in &positive_ids {
        oracle.add_vector(*event_id, vec![0.8, 0.6]);
    }
    oracle.add_vector(id(51), vec![-1.0, 0.0]);
    let mut cache = CandidateVectorCache::new(VERSION).expect("vector cache");

    let order = frozen(
        build_compact_candidate_order(
            &controller,
            &mut oracle,
            &mut cache,
            &request(CandidateOrderPhase::Learning, 0.0, []),
        )
        .expect("compact order"),
    );

    let rated_vectors = [RatedVector::new(vec![1.0, 0.0], 1.0).expect("positive")];
    let scorer = CompactSupportScorer::new(&rated_vectors, controller.active_tuple().parameters())
        .expect("active compact scorer");
    let expected = scorer.score(&[0.8, 0.6]).expect("expected score");
    let scored = order
        .accepted()
        .iter()
        .find(|candidate| candidate.event_id() == id(10))
        .expect("scored candidate");
    assert_close(scored.raw_score(), expected);
    assert_close(scored.deployed_score(), expected);
    assert!(expected > 0.0);
    assert!(matches!(
        order.candidate_audit(id(51)).unwrap().disposition(),
        CandidateDisposition::NonPositive {
            raw_score: 0.0,
            deployed_score: 0.0,
        }
    ));
}

#[test]
fn rbf_order_uses_active_raw_and_deployed_scores_and_excludes_nonpositive_candidates() {
    let controller = rbf_controller(vec![
        evidence(1, &[1.0, 0.0], 7),
        evidence(2, &[0.0, 1.0], 1),
    ]);
    let positive_ids = (10..=50).map(id).collect::<Vec<_>>();
    let mut response_ids = positive_ids.clone();
    response_ids.push(id(51));
    let mut oracle = RecordingOracle::new();
    oracle.add_response(1, response_ids);
    for event_id in &positive_ids {
        oracle.add_vector(*event_id, vec![1.0, 0.0]);
    }
    oracle.add_vector(id(51), vec![0.0, 1.0]);
    let mut cache = CandidateVectorCache::new(VERSION).expect("vector cache");

    let order = frozen(
        build_rbf_candidate_order(
            &controller,
            &mut oracle,
            &mut cache,
            &request(CandidateOrderPhase::Learning, 0.0, []),
        )
        .expect("RBF order"),
    );

    let rated_vectors = [
        RatedVector::new(vec![1.0, 0.0], 1.0).expect("positive"),
        RatedVector::new(vec![0.0, 1.0], -1.0).expect("negative"),
    ];
    let scorer = RbfKernelRidgeScorer::fit(&rated_vectors, controller.active_tuple().parameters())
        .expect("active RBF scorer");
    let expected = scorer.score(&[1.0, 0.0]).expect("expected score");
    assert_close(order.accepted()[0].raw_score(), expected.raw);
    assert_close(order.accepted()[0].deployed_score(), expected.deployed);
    assert_eq!(order.accepted().len(), 41);
    assert!(order.candidate_audit(id(51)).unwrap().is_nonpositive());
}

#[test]
fn rbf_clipped_scores_tie_by_hash_without_using_raw_score() {
    let seed_rows = [
        (1, vec![0.191_892_13, 0.981_416], 1),
        (2, vec![0.976_130_55, 0.217_184_66], 7),
        (3, vec![0.513_804_4, 0.857_907_36], 7),
    ];
    let mut controller = RbfLearningController::new(
        RbfLearningSettings::new(VERSION, 0.425_735_198_529_48, 0.5, 0.75).expect("RBF settings"),
        seed_rows
            .iter()
            .map(|(event_id, vector, rating)| evidence(*event_id, vector, *rating))
            .collect(),
    )
    .expect("RBF controller");
    let learned_vector = vec![0.761_519, 0.648_142_5];
    controller
        .freeze_batch(
            CandidateBatch::new(
                VERSION,
                vec![BatchCandidate::new(id(4), learned_vector.clone()).expect("candidate")],
            )
            .expect("learning batch"),
        )
        .expect("freeze learning batch");
    controller
        .complete_batch(vec![BatchRating::new(id(4), 7).expect("rating")])
        .expect("complete learning batch");
    assert_eq!(controller.active_tuple().scale_level(), ScaleLevel::Mass16);
    assert_eq!(controller.active_tuple().regularization(), 0.25);

    let mut candidate_ids = (10..=50).map(id).collect::<Vec<_>>();
    candidate_ids.sort_by_key(|event_id| candidate_tie(*event_id));
    let low_raw_id = candidate_ids[0];
    let high_raw_id = candidate_ids[candidate_ids.len() - 1];
    let all_events = [id(1), id(2), id(3), id(4)]
        .into_iter()
        .chain(candidate_ids.iter().copied())
        .collect::<Vec<_>>();
    let mut oracle = RecordingOracle::new();
    for source_number in 2..=4 {
        let source = id(source_number);
        oracle.add_response(
            source_number,
            all_events
                .iter()
                .copied()
                .filter(|event_id| *event_id != source),
        );
    }
    for event_id in &candidate_ids {
        let vector = if *event_id == low_raw_id {
            unit_angle(27.0)
        } else if *event_id == high_raw_id {
            unit_angle(36.0)
        } else {
            unit_angle(30.0)
        };
        oracle.add_vector(*event_id, vector);
    }
    let mut cache = CandidateVectorCache::new(VERSION).expect("vector cache");

    let order = frozen(
        build_rbf_candidate_order(
            &controller,
            &mut oracle,
            &mut cache,
            &request(CandidateOrderPhase::Learning, 0.0, []),
        )
        .expect("RBF clipped order"),
    );

    assert_eq!(
        order
            .accepted()
            .iter()
            .map(|candidate| candidate.event_id())
            .collect::<Vec<_>>(),
        candidate_ids
    );
    let low = order.accepted().first().expect("lowest hash candidate");
    let high = order.accepted().last().expect("highest hash candidate");
    assert!(low.raw_score() > 1.0);
    assert!(high.raw_score() > low.raw_score());
    assert_eq!(low.deployed_score(), 1.0);
    assert_eq!(high.deployed_score(), 1.0);
}

#[test]
fn b16_uses_only_accepted_blockers_and_accepts_the_exact_boundary() {
    let dimensions = 42;
    let mut seed = vec![0.0_f32; dimensions];
    seed[0] = 1.0;
    let controller = compact_controller(vec![evidence(1, &seed, 7)]);
    let mut oracle = RecordingOracle::new();
    let mut exact = vec![0.0_f32; dimensions];
    exact[0] = 1.0;
    let mut near = vec![0.0_f32; dimensions];
    near[0] = 0.1_f32.cos();
    near[1] = 0.1_f32.sin();
    let mut separated = vec![0.0_f32; dimensions];
    separated[0] = 0.2_f32.cos();
    separated[1] = 0.2_f32.sin();
    assert!(
        oracle_mvp::local_personalizer::squared_chord_distance(&near, &separated)
            .expect("near-to-separated distance")
            .sqrt()
            < 0.15
    );
    let mut candidate_ids = vec![id(10), id(11), id(12)];
    candidate_ids.extend((20..=58).map(id));
    oracle.add_response(1, candidate_ids);
    oracle.add_vector(id(10), exact);
    oracle.add_vector(id(11), near);
    oracle.add_vector(id(12), separated);
    for value in 20..=58 {
        let mut vector = vec![0.0_f32; dimensions];
        vector[0] = 0.8;
        vector[usize::from(value - 20) + 3] = 0.6;
        oracle.add_vector(id(value), vector);
    }
    let mut cache = CandidateVectorCache::new(VERSION).expect("vector cache");

    let order = frozen(
        build_compact_candidate_order(
            &controller,
            &mut oracle,
            &mut cache,
            &request(CandidateOrderPhase::Learning, 0.15, []),
        )
        .expect("B16 order"),
    );

    let rejected = order.candidate_audit(id(11)).expect("near-duplicate audit");
    let (blocker, distance) = rejected
        .near_duplicate_blocker()
        .expect("near-duplicate rejection");
    assert_eq!(blocker, id(10));
    assert!(distance < 0.15);
    assert!(
        order
            .accepted()
            .iter()
            .any(|candidate| candidate.event_id() == id(12))
    );

    let dimensions = 43;
    let mut boundary_oracle = RecordingOracle::new();
    let mut boundary_seed = vec![0.0_f32; dimensions];
    boundary_seed[0] = 1.0;
    let a = 0.8_f32;
    let b = (1.0_f32 - a * a).sqrt();
    let mut boundary_ids = Vec::new();
    for offset in 0..41_u16 {
        let event_id = id(100 + offset);
        boundary_ids.push(event_id);
        let mut vector = vec![0.0_f32; dimensions];
        vector[0] = a;
        vector[usize::from(offset) + 1] = b;
        boundary_oracle.add_vector(event_id, vector);
    }
    boundary_oracle.add_response(1, boundary_ids);
    let exact_boundary = (2.0_f64 * f64::from(b) * f64::from(b)).sqrt();
    let boundary_controller = compact_controller(vec![evidence(1, &boundary_seed, 7)]);
    let mut boundary_cache = CandidateVectorCache::new(VERSION).expect("boundary cache");
    let boundary_order = frozen(
        build_compact_candidate_order(
            &boundary_controller,
            &mut boundary_oracle,
            &mut boundary_cache,
            &request(CandidateOrderPhase::Learning, exact_boundary, []),
        )
        .expect("exact-boundary order"),
    );
    assert_eq!(boundary_order.accepted().len(), 41);
}

#[test]
fn exact_phase_bounds_freeze_or_report_an_atomic_shortage() {
    for (phase, available) in [
        (CandidateOrderPhase::Learning, 41_u16),
        (CandidateOrderPhase::Final, 221_u16),
    ] {
        let controller = compact_controller(vec![evidence(1, &[1.0, 0.0], 7)]);
        let candidate_ids = (0..available)
            .map(|offset| id(100 + offset))
            .collect::<Vec<_>>();
        let mut oracle = RecordingOracle::new();
        oracle.add_response(1, candidate_ids.iter().copied());
        for event_id in candidate_ids {
            oracle.add_vector(event_id, vec![1.0, 0.0]);
        }
        let mut cache = CandidateVectorCache::new(VERSION).expect("vector cache");
        let order = frozen(
            build_compact_candidate_order(
                &controller,
                &mut oracle,
                &mut cache,
                &request(phase, 0.0, []),
            )
            .expect("complete order"),
        );
        assert_eq!(order.accepted().len(), phase.accepted_count());
        assert_eq!(order.primary().len(), phase.primary_count());
        assert_eq!(order.reserve().len(), 21);
    }

    let controller = compact_controller(vec![evidence(1, &[1.0, 0.0], 7)]);
    let identity_before = controller.evidence_identity().clone();
    let candidate_ids = (100..140).map(id).collect::<Vec<_>>();
    let mut oracle = RecordingOracle::new();
    oracle.add_response(1, candidate_ids.iter().copied());
    for event_id in candidate_ids {
        oracle.add_vector(event_id, vec![1.0, 0.0]);
    }
    let mut cache = CandidateVectorCache::new(VERSION).expect("vector cache");
    let outcome = build_compact_candidate_order(
        &controller,
        &mut oracle,
        &mut cache,
        &request(CandidateOrderPhase::Learning, 0.0, []),
    )
    .expect("domain shortage outcome");
    let CandidateOrderOutcome::Insufficient(failure) = outcome else {
        panic!("a partial candidate pool must not publish a frozen order");
    };
    assert_eq!(failure.accepted_count(), 40);
    assert_eq!(failure.required_count(), 41);
    assert_eq!(controller.evidence_identity(), &identity_before);
    assert!(controller.history().is_empty());
    assert_eq!(cache.vector_count(), 40);
}

#[test]
fn malformed_oracle_results_do_not_partially_fill_the_vector_cache() {
    let controller = compact_controller(vec![evidence(1, &[1.0, 0.0], 7)]);
    let candidate_ids = (10..=50).map(id).collect::<Vec<_>>();
    let request = request(CandidateOrderPhase::Learning, 0.0, []);

    let mut wrong_response = RecordingOracle::new();
    wrong_response.add_response(1, candidate_ids.iter().copied());
    wrong_response.response_version_override = Some("wrong-version".to_owned());
    let mut cache = CandidateVectorCache::new(VERSION).expect("response cache");
    assert!(matches!(
        build_compact_candidate_order(&controller, &mut wrong_response, &mut cache, &request,),
        Err(CandidateOrderError::InvalidOracleResponse { .. })
    ));
    assert_eq!(cache.vector_count(), 0);

    let mut wrong_vectors = RecordingOracle::new();
    wrong_vectors.add_response(1, candidate_ids.iter().copied());
    for event_id in &candidate_ids {
        wrong_vectors.add_vector(*event_id, vec![1.0, 0.0]);
    }
    wrong_vectors.vector_version_override = Some("wrong-version".to_owned());
    let mut cache = CandidateVectorCache::new(VERSION).expect("vector cache");
    assert!(matches!(
        build_compact_candidate_order(&controller, &mut wrong_vectors, &mut cache, &request,),
        Err(CandidateOrderError::InvalidVectorResponse { .. })
    ));
    assert_eq!(cache.vector_count(), 0);

    let mut reordered_vectors = RecordingOracle::new();
    reordered_vectors.add_response(1, candidate_ids.iter().copied());
    for event_id in &candidate_ids {
        reordered_vectors.add_vector(*event_id, vec![1.0, 0.0]);
    }
    reordered_vectors.vector_ids_override = Some(candidate_ids.iter().copied().rev().collect());
    let mut cache = CandidateVectorCache::new(VERSION).expect("vector cache");
    assert!(matches!(
        build_compact_candidate_order(&controller, &mut reordered_vectors, &mut cache, &request,),
        Err(CandidateOrderError::InvalidVectorResponse { .. })
    ));
    assert_eq!(cache.vector_count(), 0);
}

#[test]
fn a_truncated_fixed_depth_response_is_rejected() {
    let controller = compact_controller(vec![evidence(1, &[1.0, 0.0], 7)]);
    let candidate_ids = (10..=50).map(id).collect::<Vec<_>>();
    let mut oracle = RecordingOracle::new();
    oracle.artifact_rows_override = Some(ROWS);
    oracle.add_response(1, candidate_ids.iter().copied());
    for event_id in candidate_ids {
        oracle.add_vector(event_id, vec![1.0, 0.0]);
    }
    let mut cache = CandidateVectorCache::new(VERSION).expect("vector cache");

    assert!(matches!(
        build_compact_candidate_order(
            &controller,
            &mut oracle,
            &mut cache,
            &request(CandidateOrderPhase::Learning, 0.0, []),
        ),
        Err(CandidateOrderError::InvalidOracleResponse { .. })
    ));
    assert_eq!(cache.vector_count(), 0);
}

#[test]
fn invalid_b16_is_rejected_before_oracle_work() {
    assert!(B16Boundary::new(VERSION, 0.0).is_ok());
    assert!(B16Boundary::new(VERSION, -0.1).is_err());
    assert!(B16Boundary::new(VERSION, f64::NAN).is_err());
    assert!(B16Boundary::new(VERSION, f64::INFINITY).is_err());
}

#[test]
fn version_mismatches_and_a_pending_batch_fail_before_oracle_work() {
    let controller = compact_controller(vec![evidence(1, &[1.0, 0.0], 7)]);
    let mut oracle = RecordingOracle::new();
    let mut cache = CandidateVectorCache::new(VERSION).expect("vector cache");
    let wrong_b16 = CandidateOrderRequest::new(
        CandidateOrderPhase::Learning,
        B16Boundary::new("wrong-version", 0.0).expect("wrong-version B16"),
        BTreeSet::new(),
    );
    assert!(matches!(
        build_compact_candidate_order(&controller, &mut oracle, &mut cache, &wrong_b16),
        Err(CandidateOrderError::RepresentationVersionMismatch { context: "B16", .. })
    ));

    let mut wrong_cache = CandidateVectorCache::new("wrong-version").expect("wrong-version cache");
    assert!(matches!(
        build_compact_candidate_order(
            &controller,
            &mut oracle,
            &mut wrong_cache,
            &request(CandidateOrderPhase::Learning, 0.0, []),
        ),
        Err(CandidateOrderError::RepresentationVersionMismatch {
            context: "vector cache",
            ..
        })
    ));

    let mut wrong_oracle = RecordingOracle::new();
    wrong_oracle.representation_version = "wrong-version".to_owned();
    assert!(matches!(
        build_compact_candidate_order(
            &controller,
            &mut wrong_oracle,
            &mut cache,
            &request(CandidateOrderPhase::Learning, 0.0, []),
        ),
        Err(CandidateOrderError::RepresentationVersionMismatch {
            context: "Oracle",
            ..
        })
    ));

    let mut pending = compact_controller(vec![evidence(1, &[1.0, 0.0], 7)]);
    pending
        .freeze_batch(
            CandidateBatch::new(
                VERSION,
                vec![BatchCandidate::new(id(2), vec![1.0, 0.0]).expect("candidate")],
            )
            .expect("pending batch"),
        )
        .expect("freeze pending batch");
    assert!(matches!(
        build_compact_candidate_order(
            &pending,
            &mut oracle,
            &mut cache,
            &request(CandidateOrderPhase::Learning, 0.0, []),
        ),
        Err(CandidateOrderError::LearningBatchPending)
    ));
    assert!(oracle.encoded_waves.is_empty());
    assert!(oracle.vector_requests.is_empty());
}
