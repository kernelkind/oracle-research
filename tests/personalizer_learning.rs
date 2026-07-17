use oracle_mvp::local_personalizer::{CompactNeighborCount, CompactSupportScorer, RatedVector};
use oracle_mvp::personalizer_learning::{
    BatchCandidate, BatchRating, CandidateBatch, CompactLearningController,
    CompactLearningSettings, EvidenceNote, GladnessRating, PersonalizerLearningError,
    RbfLearningController, RbfLearningSettings, ScaleLevel,
};

const VERSION: &str = "representation-v1";
const TOLERANCE: f64 = 1e-12;

fn id(value: u8) -> [u8; 32] {
    [value; 32]
}

fn compact_settings() -> CompactLearningSettings {
    CompactLearningSettings::new(VERSION, 0.5, 1.0, 2.0, ScaleLevel::Mass64)
        .expect("valid compact settings")
}

fn rbf_settings() -> RbfLearningSettings {
    RbfLearningSettings::new(VERSION, 0.5, 1.0, 2.0).expect("valid RBF settings")
}

fn evidence(event_id: u8, vector: &[f32], rating: u8) -> EvidenceNote {
    EvidenceNote::new(id(event_id), vector.to_vec(), rating).expect("valid evidence")
}

fn candidate(event_id: u8, vector: &[f32]) -> BatchCandidate {
    BatchCandidate::new(id(event_id), vector.to_vec()).expect("valid candidate")
}

fn batch(candidates: Vec<BatchCandidate>) -> CandidateBatch {
    CandidateBatch::new(VERSION, candidates).expect("valid batch")
}

fn rating(event_id: u8, value: u8) -> BatchRating {
    BatchRating::new(id(event_id), value).expect("valid rating")
}

fn assert_close(actual: f64, expected: f64) {
    assert!(
        (actual - expected).abs() <= TOLERANCE,
        "expected {expected}, got {actual}"
    );
}

#[test]
fn compact_predictions_are_frozen_before_feedback() {
    let mut learner =
        CompactLearningController::new(compact_settings(), vec![evidence(1, &[1.0, 0.0], 7)])
            .expect("valid learner");
    let identity_before = learner.evidence_identity().clone();

    let frozen = learner
        .freeze_batch(batch(vec![candidate(2, &[1.0, 0.0])]))
        .expect("freeze predictions")
        .clone();
    let completed = learner
        .complete_batch(vec![rating(2, 1)])
        .expect("complete batch")
        .clone();

    assert_eq!(completed.frozen_batch(), &frozen);
    assert_eq!(completed.outcomes()[0].target(), -1.0);
    assert_eq!(frozen.evidence_identity(), &identity_before);
    assert_eq!(completed.evidence_after().event_count(), 2);
    assert_ne!(completed.evidence_after(), &identity_before);
    assert_eq!(learner.evidence_count(), 2);
}

#[test]
fn invalid_completion_is_atomic_and_valid_ratings_match_by_event_id() {
    let mut learner =
        CompactLearningController::new(compact_settings(), vec![evidence(1, &[1.0, 0.0], 7)])
            .expect("valid learner");
    let frozen = learner
        .freeze_batch(batch(vec![
            candidate(2, &[1.0, 0.0]),
            candidate(3, &[0.0, 1.0]),
        ]))
        .expect("freeze batch")
        .clone();
    let identity = learner.evidence_identity().clone();
    let active = learner.active_tuple();

    assert!(matches!(
        learner.complete_batch(vec![rating(2, 7)]),
        Err(PersonalizerLearningError::MissingRating { event_id }) if event_id == id(3)
    ));
    assert!(matches!(
        learner.complete_batch(vec![rating(2, 7), rating(2, 1), rating(3, 4)]),
        Err(PersonalizerLearningError::DuplicateRating { event_id }) if event_id == id(2)
    ));
    assert!(matches!(
        learner.complete_batch(vec![rating(2, 7), rating(3, 4), rating(9, 1)]),
        Err(PersonalizerLearningError::UnexpectedRating { event_id }) if event_id == id(9)
    ));
    assert!(matches!(
        learner.freeze_batch(batch(vec![candidate(4, &[1.0, 0.0])])),
        Err(PersonalizerLearningError::BatchAlreadyFrozen)
    ));
    assert_eq!(
        BatchRating::new(id(2), 0),
        Err(PersonalizerLearningError::InvalidRating(0))
    );
    assert_eq!(learner.evidence_count(), 1);
    assert_eq!(learner.evidence_identity(), &identity);
    assert_eq!(learner.active_tuple(), active);
    assert!(learner.history().is_empty());
    assert_eq!(learner.pending_batch(), Some(&frozen));

    let completed = learner
        .complete_batch(vec![rating(3, 1), rating(2, 7)])
        .expect("retry valid completion")
        .clone();
    assert_eq!(completed.outcomes()[0].event_id(), id(2));
    assert_eq!(completed.outcomes()[0].rating().value(), 7);
    assert_eq!(completed.outcomes()[1].event_id(), id(3));
    assert_eq!(completed.outcomes()[1].rating().value(), 1);
    assert_eq!(learner.evidence_count(), 3);
    assert!(learner.pending_batch().is_none());
    assert!(matches!(
        learner.complete_batch(Vec::new()),
        Err(PersonalizerLearningError::NoFrozenBatch)
    ));
}

#[test]
fn rating_targets_are_exact_and_neutral_evidence_is_retained() {
    let expected = [-1.0, -2.0 / 3.0, -1.0 / 3.0, 0.0, 1.0 / 3.0, 2.0 / 3.0, 1.0];
    for (value, expected) in (1..=7).zip(expected) {
        assert_close(
            GladnessRating::new(value).expect("valid rating").target(),
            expected,
        );
    }

    let mut learner =
        CompactLearningController::new(compact_settings(), vec![evidence(1, &[1.0, 0.0], 7)])
            .expect("valid learner");
    let first = learner
        .freeze_batch(batch(vec![candidate(2, &[1.0, 0.0])]))
        .expect("freeze first batch")
        .clone();
    let first_score = first
        .predictions()
        .iter()
        .find(|predictions| predictions.parameter_tuple() == first.active_tuple())
        .expect("active tuple predictions")
        .scores()[0];
    let completed = learner
        .complete_batch(vec![rating(2, 4)])
        .expect("retain neutral rating")
        .clone();
    assert_eq!(completed.outcomes()[0].target(), 0.0);

    let second = learner
        .freeze_batch(batch(vec![candidate(3, &[1.0, 0.0])]))
        .expect("freeze second batch");
    let second_score = second
        .predictions()
        .iter()
        .find(|predictions| predictions.parameter_tuple() == second.active_tuple())
        .expect("active tuple predictions")
        .scores()[0];
    assert!(
        second_score < first_score,
        "neutral evidence must pull the score toward zero"
    );
}

#[test]
fn cumulative_error_uses_each_rounds_retained_predictions() {
    let mut learner =
        CompactLearningController::new(compact_settings(), vec![evidence(1, &[1.0, 0.0], 7)])
            .expect("valid learner");

    learner
        .freeze_batch(batch(vec![candidate(2, &[1.0, 0.0])]))
        .expect("freeze round one");
    let first = learner
        .complete_batch(vec![rating(2, 1)])
        .expect("complete round one")
        .clone();
    let retained_first = first.clone();

    learner
        .freeze_batch(batch(vec![candidate(3, &[0.0, 1.0])]))
        .expect("freeze round two");
    let second = learner
        .complete_batch(vec![rating(3, 7)])
        .expect("complete round two")
        .clone();

    assert_eq!(&learner.history()[0], &retained_first);
    for second_error in second.errors() {
        let first_error = first
            .errors()
            .iter()
            .find(|error| error.parameter_tuple() == second_error.parameter_tuple())
            .expect("same tuple in both rounds");
        assert_close(
            second_error.cumulative_mse(),
            (first_error.batch_mse() + second_error.batch_mse()) / 2.0,
        );
    }
}

#[test]
fn exact_error_ties_use_the_approved_parameter_orders() {
    let neutral = vec![evidence(1, &[1.0, 0.0], 4)];
    let mut compact =
        CompactLearningController::new(compact_settings(), neutral.clone()).expect("compact");
    compact
        .freeze_batch(batch(vec![candidate(2, &[0.0, 1.0])]))
        .expect("freeze compact");
    let compact_record = compact
        .complete_batch(vec![rating(2, 4)])
        .expect("complete compact")
        .clone();
    let compact_next = compact_record.next_tuple();
    assert_eq!(compact_next.scale_level(), ScaleLevel::Mass16);
    assert_eq!(compact_next.maximum_distance(), 0.5);
    assert_eq!(
        compact_next.neighbor_count(),
        CompactNeighborCount::Finite(1)
    );
    assert_eq!(compact_next.neutral_weight(), 2.0);
    assert_eq!(compact_record.frozen_batch().predictions().len(), 63);

    let mut rbf = RbfLearningController::new(rbf_settings(), neutral).expect("RBF");
    rbf.freeze_batch(batch(vec![candidate(2, &[0.0, 1.0])]))
        .expect("freeze RBF");
    let rbf_record = rbf
        .complete_batch(vec![rating(2, 4)])
        .expect("complete RBF")
        .clone();
    let rbf_next = rbf_record.next_tuple();
    assert_eq!(rbf_next.scale_level(), ScaleLevel::Mass16);
    assert_eq!(rbf_next.scale(), 0.5);
    assert_eq!(rbf_next.regularization(), 4.0);
    assert_eq!(rbf_record.frozen_batch().predictions().len(), 9);
}

#[test]
fn compact_frozen_grid_matches_each_approved_scorer() {
    let seeds = vec![
        evidence(1, &[1.0, 0.0], 7),
        evidence(2, &[0.0, 1.0], 1),
        evidence(3, &[0.8, 0.6], 4),
    ];
    let rated_vectors = vec![
        RatedVector::new(vec![1.0, 0.0], 1.0).expect("positive evidence"),
        RatedVector::new(vec![0.0, 1.0], -1.0).expect("negative evidence"),
        RatedVector::new(vec![0.8, 0.6], 0.0).expect("neutral evidence"),
    ];
    let candidates = vec![candidate(4, &[0.9, 0.1]), candidate(5, &[0.1, 0.9])];
    let candidate_vectors = candidates
        .iter()
        .map(|candidate| candidate.vector().to_vec())
        .collect::<Vec<_>>();
    let mut learner =
        CompactLearningController::new(compact_settings(), seeds).expect("compact learner");

    let frozen = learner
        .freeze_batch(batch(candidates))
        .expect("freeze compact grid");

    for predictions in frozen.predictions() {
        let scorer =
            CompactSupportScorer::new(&rated_vectors, predictions.parameter_tuple().parameters())
                .expect("individual scorer");
        for (candidate, frozen_score) in candidate_vectors.iter().zip(predictions.scores()) {
            assert_close(
                *frozen_score,
                scorer.score(candidate).expect("individual prediction"),
            );
        }
    }
}

#[test]
fn rbf_error_uses_deployed_scores_but_retains_raw_scores() {
    let settings =
        RbfLearningSettings::new(VERSION, 0.425_735_198_529_48, 0.5, 0.75).expect("RBF settings");
    let seeds = vec![
        evidence(1, &[0.191_892_13, 0.981_416], 1),
        evidence(2, &[0.976_130_55, 0.217_184_66], 7),
        evidence(3, &[0.513_804_4, 0.857_907_36], 7),
    ];
    let mut learner = RbfLearningController::new(settings, seeds).expect("RBF learner");
    let frozen = learner
        .freeze_batch(batch(vec![candidate(4, &[0.761_519, 0.648_142_5])]))
        .expect("freeze RBF batch")
        .clone();
    let tuple_predictions = frozen
        .predictions()
        .iter()
        .find(|predictions| {
            predictions.parameter_tuple().scale_level() == ScaleLevel::Mass16
                && predictions.parameter_tuple().regularization() == 0.25
        })
        .expect("clamped tuple");
    assert!(tuple_predictions.scores()[0].raw > 1.0);
    assert_eq!(tuple_predictions.scores()[0].deployed, 1.0);

    let completed = learner
        .complete_batch(vec![rating(4, 7)])
        .expect("complete RBF batch")
        .clone();
    let tuple_error = completed
        .errors()
        .iter()
        .find(|error| {
            error.parameter_tuple().scale_level() == ScaleLevel::Mass16
                && error.parameter_tuple().regularization() == 0.25
        })
        .expect("clamped tuple error");
    assert_eq!(tuple_error.batch_mse(), 0.0);
    assert_eq!(completed.frozen_batch(), &frozen);
}

#[test]
fn compact_and_rbf_learning_states_are_independent() {
    let seeds = vec![evidence(1, &[1.0, 0.0], 7)];
    let mut compact =
        CompactLearningController::new(compact_settings(), seeds.clone()).expect("compact");
    let mut rbf = RbfLearningController::new(rbf_settings(), seeds).expect("RBF");
    let rbf_identity = rbf.evidence_identity().clone();
    let rbf_active = rbf.active_tuple();

    compact
        .freeze_batch(batch(vec![candidate(2, &[1.0, 0.0])]))
        .expect("freeze compact");
    compact
        .complete_batch(vec![rating(2, 1)])
        .expect("complete compact");
    assert_eq!(rbf.evidence_count(), 1);
    assert_eq!(rbf.evidence_identity(), &rbf_identity);
    assert_eq!(rbf.active_tuple(), rbf_active);
    assert!(rbf.history().is_empty());
    assert!(rbf.pending_batch().is_none());

    let compact_identity = compact.evidence_identity().clone();
    let compact_active = compact.active_tuple();
    rbf.freeze_batch(batch(vec![candidate(3, &[0.0, 1.0])]))
        .expect("freeze RBF");
    rbf.complete_batch(vec![rating(3, 7)])
        .expect("complete RBF");
    assert_eq!(compact.evidence_count(), 2);
    assert_eq!(compact.evidence_identity(), &compact_identity);
    assert_eq!(compact.active_tuple(), compact_active);
    assert_eq!(compact.history().len(), 1);
}

#[test]
fn repeated_event_ids_are_rejected_but_equal_vectors_remain_independent() {
    let duplicate_evidence = vec![evidence(1, &[1.0, 0.0], 7), evidence(1, &[0.0, 1.0], 1)];
    assert!(matches!(
        CompactLearningController::new(compact_settings(), duplicate_evidence),
        Err(PersonalizerLearningError::DuplicateEvidence { event_id }) if event_id == id(1)
    ));
    assert!(matches!(
        CandidateBatch::new(
            VERSION,
            vec![candidate(2, &[1.0, 0.0]), candidate(2, &[0.0, 1.0])]
        ),
        Err(PersonalizerLearningError::DuplicateCandidate { event_id }) if event_id == id(2)
    ));

    let mut learner =
        CompactLearningController::new(compact_settings(), vec![evidence(1, &[1.0, 0.0], 7)])
            .expect("learner");
    assert!(matches!(
        learner.freeze_batch(batch(vec![candidate(1, &[0.0, 1.0])])),
        Err(PersonalizerLearningError::CandidateAlreadyInEvidence { event_id })
            if event_id == id(1)
    ));
    learner
        .freeze_batch(batch(vec![
            candidate(2, &[1.0, 0.0]),
            candidate(3, &[1.0, 0.0]),
        ]))
        .expect("distinct IDs with equal vectors remain distinct");
    learner
        .complete_batch(vec![rating(2, 7), rating(3, 1)])
        .expect("complete independent observations");
    assert_eq!(learner.evidence_count(), 3);
}

#[test]
fn representation_and_input_validation_precede_state_changes() {
    assert!(matches!(
        CompactLearningSettings::new("", 0.5, 1.0, 2.0, ScaleLevel::Mass64),
        Err(PersonalizerLearningError::EmptyRepresentationVersion)
    ));
    assert!(matches!(
        CompactLearningSettings::new(VERSION, 1.0, 0.5, 2.0, ScaleLevel::Mass64),
        Err(PersonalizerLearningError::InvalidCompactScales)
    ));
    assert!(matches!(
        CompactLearningSettings::new(VERSION, 0.5, 1.0, 2.0, ScaleLevel::Mass16),
        Err(PersonalizerLearningError::InvalidInitialCompactScale)
    ));
    assert!(matches!(
        RbfLearningSettings::new(VERSION, 0.5, f64::NAN, 2.0),
        Err(PersonalizerLearningError::InvalidRbfScales)
    ));
    assert!(matches!(
        RbfLearningSettings::new(VERSION, f64::MIN_POSITIVE, 1.0, 2.0),
        Err(PersonalizerLearningError::InvalidRbfScales)
    ));
    assert!(matches!(
        CandidateBatch::new(VERSION, Vec::new()),
        Err(PersonalizerLearningError::EmptyBatch)
    ));
    assert!(BatchCandidate::new(id(2), vec![f32::NAN]).is_err());
    assert!(
        CandidateBatch::new(
            VERSION,
            vec![candidate(2, &[1.0, 0.0]), candidate(3, &[1.0, 0.0, 0.0])]
        )
        .is_err()
    );

    let mut learner =
        CompactLearningController::new(compact_settings(), vec![evidence(1, &[1.0, 0.0], 7)])
            .expect("learner");
    let identity = learner.evidence_identity().clone();
    let wrong_version = CandidateBatch::new("representation-v2", vec![candidate(2, &[1.0, 0.0])])
        .expect("structurally valid batch");
    assert!(matches!(
        learner.freeze_batch(wrong_version),
        Err(PersonalizerLearningError::RepresentationVersionMismatch { expected, actual })
            if expected == VERSION && actual == "representation-v2"
    ));
    assert_eq!(learner.evidence_identity(), &identity);
    assert!(learner.pending_batch().is_none());

    assert!(
        learner
            .freeze_batch(batch(vec![candidate(2, &[1.0, 0.0, 0.0])]))
            .is_err()
    );
    assert_eq!(learner.evidence_identity(), &identity);
    assert!(learner.pending_batch().is_none());
}
