use oracle_mvp::local_personalizer::{
    CompactNeighborCount, CompactParameters, CompactSupportScorer, RatedVector,
    RbfKernelRidgeParameters, RbfKernelRidgeScorer, squared_chord_distance,
};

const TOLERANCE: f64 = 1e-12;

fn evidence(vector: &[f32], target: f64) -> RatedVector {
    RatedVector::new(vector.to_vec(), target).expect("valid rated vector")
}

fn assert_close(actual: f64, expected: f64) {
    assert!(
        (actual - expected).abs() <= TOLERANCE,
        "expected {expected}, got {actual}"
    );
}

#[test]
fn local_distance_distinguishes_a_near_vector_from_an_exact_match() {
    let exact = [1.0_f32, 0.0];
    let one_ulp_away = [f32::from_bits(1.0_f32.to_bits() - 1), 0.0];

    assert_eq!(
        squared_chord_distance(&exact, &exact).expect("exact distance"),
        0.0
    );
    assert!(squared_chord_distance(&exact, &one_ulp_away).expect("near distance") > 0.0);
    assert_eq!(
        squared_chord_distance(&[0.0], &[-0.0]).expect("signed zero distance"),
        0.0
    );
}

#[test]
fn compact_zero_bandwidth_keeps_all_exact_evidence_and_excludes_the_rest() {
    let rated = [
        evidence(&[1.0, 0.0], 1.0),
        evidence(&[1.0, 0.0], 0.0),
        evidence(&[0.0, 1.0], -1.0),
    ];
    let parameters = CompactParameters::new(CompactNeighborCount::Finite(1), 2.0, 1.0)
        .expect("compact parameters");
    let scorer = CompactSupportScorer::new(&rated, parameters).expect("compact scorer");

    // The second-closest distance is zero, so h = 0. Both exact rows remain
    // independent weight-one observations and the non-exact negative is excluded.
    assert_close(scorer.score(&[1.0, 0.0]).expect("compact score"), 1.0 / 3.0);
}

#[test]
fn compact_score_preserves_neutral_shrinkage_conflict_and_no_support() {
    let parameters = CompactParameters::new(CompactNeighborCount::Infinite, 0.5, 1.0)
        .expect("compact parameters");

    let positive = [evidence(&[1.0, 0.0], 1.0)];
    let scorer = CompactSupportScorer::new(&positive, parameters).expect("positive scorer");
    assert_close(scorer.score(&[1.0, 0.0]).expect("positive score"), 0.5);
    assert_close(scorer.score(&[-1.0, 0.0]).expect("unsupported score"), 0.0);

    let with_neutral = [evidence(&[1.0, 0.0], 1.0), evidence(&[1.0, 0.0], 0.0)];
    let scorer = CompactSupportScorer::new(&with_neutral, parameters).expect("neutral scorer");
    assert_close(scorer.score(&[1.0, 0.0]).expect("neutral score"), 1.0 / 3.0);

    let conflicting = [evidence(&[1.0, 0.0], 1.0), evidence(&[1.0, 0.0], -1.0)];
    let scorer = CompactSupportScorer::new(&conflicting, parameters).expect("conflicting scorer");
    assert_close(scorer.score(&[1.0, 0.0]).expect("conflicting score"), 0.0);
}

#[test]
fn compact_support_is_strict_at_the_bandwidth() {
    let rated = [evidence(&[0.0, 1.0], 1.0)];
    let parameters = CompactParameters::new(CompactNeighborCount::Infinite, 2.0_f64.sqrt(), 1.0)
        .expect("compact parameters");
    let scorer = CompactSupportScorer::new(&rated, parameters).expect("compact scorer");

    assert_close(scorer.score(&[1.0, 0.0]).expect("boundary score"), 0.0);
}

#[test]
fn rbf_exact_evidence_uses_fixed_regularization() {
    let rated = [evidence(&[1.0, 0.0], 1.0)];
    let parameters = RbfKernelRidgeParameters::new(0.5, 1.0).expect("RBF kernel-ridge parameters");
    let scorer = RbfKernelRidgeScorer::fit(&rated, parameters).expect("fit RBF scorer");
    let score = scorer.score(&[1.0, 0.0]).expect("RBF score");

    assert_close(score.raw, 0.5);
    assert_close(score.deployed, 0.5);
}

#[test]
fn rbf_keeps_matching_observations_distinct() {
    let agreeing = [evidence(&[1.0, 0.0], 1.0), evidence(&[1.0, 0.0], 1.0)];
    let parameters = RbfKernelRidgeParameters::new(0.5, 1.0).expect("RBF kernel-ridge parameters");
    let scorer = RbfKernelRidgeScorer::fit(&agreeing, parameters).expect("fit agreeing rows");
    assert_close(
        scorer.score(&[1.0, 0.0]).expect("agreeing score").raw,
        2.0 / 3.0,
    );

    let conflicting = [evidence(&[1.0, 0.0], 1.0), evidence(&[1.0, 0.0], -1.0)];
    let scorer = RbfKernelRidgeScorer::fit(&conflicting, parameters).expect("fit conflicting rows");
    assert_close(
        scorer.score(&[1.0, 0.0]).expect("conflicting score").raw,
        0.0,
    );
}

#[test]
fn rbf_clamps_only_the_deployed_score() {
    let rated = [
        evidence(&[0.191_892_13, 0.981_416], -1.0),
        evidence(&[0.976_130_55, 0.217_184_66], 1.0),
        evidence(&[0.513_804_4, 0.857_907_36], 1.0),
    ];
    let parameters = RbfKernelRidgeParameters::new(0.425_735_198_529_48, 0.25)
        .expect("RBF kernel-ridge parameters");
    let scorer = RbfKernelRidgeScorer::fit(&rated, parameters).expect("fit RBF scorer");
    let score = scorer.score(&[0.761_519, 0.648_142_5]).expect("RBF score");

    assert!(score.raw > 1.0, "fixture must exercise the deployed clamp");
    assert_eq!(score.deployed, 1.0);
}

#[test]
fn scorer_inputs_are_rejected_before_scoring() {
    assert!(RatedVector::new(Vec::new(), 0.0).is_err());
    assert!(RatedVector::new(vec![f32::NAN], 0.0).is_err());
    assert!(RatedVector::new(vec![1.0], f64::NAN).is_err());
    assert!(RatedVector::new(vec![1.0], 1.01).is_err());
    assert!(squared_chord_distance(&[1.0], &[1.0, 0.0]).is_err());

    assert!(CompactParameters::new(CompactNeighborCount::Finite(0), 1.0, 1.0).is_err());
    assert!(CompactParameters::new(CompactNeighborCount::Infinite, 0.0, 1.0).is_err());
    assert!(CompactParameters::new(CompactNeighborCount::Infinite, 1.0, 0.0).is_err());
    assert!(RbfKernelRidgeParameters::new(0.0, 1.0).is_err());
    assert!(RbfKernelRidgeParameters::new(1.0, 0.0).is_err());

    let mismatched = [evidence(&[1.0, 0.0], 1.0), evidence(&[1.0, 0.0, 0.0], 1.0)];
    let compact = CompactParameters::new(CompactNeighborCount::Infinite, 1.0, 1.0)
        .expect("compact parameters");
    assert!(CompactSupportScorer::new(&mismatched, compact).is_err());

    let valid = [evidence(&[1.0, 0.0], 1.0)];
    let scorer = CompactSupportScorer::new(&valid, compact).expect("compact scorer");
    assert!(scorer.score(&[1.0]).is_err());
}
