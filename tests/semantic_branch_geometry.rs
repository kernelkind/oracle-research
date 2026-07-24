use std::collections::{BTreeMap, BTreeSet};

use oracle_mvp::semantic_branch_geometry::{
    BranchGeometryError, BranchLabel, BranchLabelSet, BranchSettings, SemanticBranchCandidate,
    SemanticBranchDecision, Theme, ThemePair, analyze_semantic_branches,
};

#[test]
fn tangent_geometry_recovers_two_exclusive_themes_across_retrieval_radii() {
    let mut candidates = Vec::new();
    let mut labels = BTreeMap::new();
    for quartile in 0..4_u8 {
        for within_quartile in 0..4_u32 {
            let rank = u32::from(quartile) * 256 + within_quartile + 1;
            let theme = if within_quartile < 2 {
                Theme::Physical
            } else {
                Theme::Mental
            };
            let direction = match theme {
                Theme::Physical => [1.0, 0.0],
                Theme::Mental => [0.0, 1.0],
                Theme::Spiritual => unreachable!("fixture uses two themes"),
            };
            let id = format!("Q{quartile}-E{within_quartile}");
            candidates.push(candidate(&id, rank, quartile, direction));
            labels.insert(id, BranchLabel::themes([theme]));
        }
    }

    let overlap_id = "overlap".to_owned();
    candidates.push(candidate(&overlap_id, 1_020, 3, [FRAC, FRAC]));
    labels.insert(
        overlap_id,
        BranchLabel::themes([Theme::Physical, Theme::Mental]),
    );
    let neither_id = "neither".to_owned();
    candidates.push(candidate(&neither_id, 1_021, 3, [-FRAC, FRAC]));
    labels.insert(neither_id, BranchLabel::themes([]));
    let unusable_id = "unusable".to_owned();
    candidates.push(candidate(&unusable_id, 1_022, 3, [-1.0, 0.0]));
    labels.insert(unusable_id, BranchLabel::Unusable);

    let label_sets = [
        BranchLabelSet::new("labeler-a", labels.clone()).expect("first independent label set"),
        BranchLabelSet::new("labeler-b", labels).expect("second independent label set"),
    ];
    let settings =
        BranchSettings::new(8, 500, "clear-tangent-branches-v1").expect("valid settings");

    let first = analyze_semantic_branches(&candidates, &label_sets, &settings)
        .expect("analyze clear tangent branches");
    let second = analyze_semantic_branches(&candidates, &label_sets, &settings)
        .expect("repeat deterministic analysis");

    assert_eq!(first, second);
    assert_eq!(first.decision, SemanticBranchDecision::RecoverableBranches);
    assert_eq!(
        first.common_significant_themes,
        BTreeSet::from([Theme::Physical, Theme::Mental])
    );
    for report in &first.label_sets {
        assert_eq!(report.supply.exclusive[&Theme::Physical], 8);
        assert_eq!(report.supply.exclusive[&Theme::Mental], 8);
        assert_eq!(report.supply.overlap, 1);
        assert_eq!(report.supply.neither, 1);
        assert_eq!(report.supply.unusable, 1);
        assert_eq!(report.macro_mean_anchor_auroc, Some(1.0));
        assert!(report.macro_above_permutation_95th_percentile);
        assert_eq!(report.pair_metrics.len(), 1);
        assert_eq!(
            report.pair_metrics[0].pair,
            ThemePair {
                first: Theme::Physical,
                second: Theme::Mental,
            }
        );
        assert_eq!(report.pair_metrics[0].mean_anchor_auroc, 1.0);
        assert!(report.pair_metrics[0].above_permutation_95th_percentile);
    }
}

#[test]
fn rank_only_theme_separation_does_not_beat_rank_stratified_null() {
    let mut candidates = Vec::new();
    let mut labels = BTreeMap::new();
    for quartile in 0..4_u8 {
        for within_quartile in 0..4_u32 {
            let rank = u32::from(quartile) * 256 + within_quartile + 1;
            let theme = if quartile < 2 {
                Theme::Physical
            } else {
                Theme::Mental
            };
            let direction = if quartile < 2 { [1.0, 0.0] } else { [0.0, 1.0] };
            let id = format!("Q{quartile}-R{within_quartile}");
            candidates.push(candidate(&id, rank, quartile, direction));
            labels.insert(id, BranchLabel::themes([theme]));
        }
    }
    let label_sets = [
        BranchLabelSet::new("labeler-a", labels.clone()).expect("first independent label set"),
        BranchLabelSet::new("labeler-b", labels).expect("second independent label set"),
    ];
    let settings = BranchSettings::new(8, 100, "rank-confounding-v1").expect("valid settings");

    let report = analyze_semantic_branches(&candidates, &label_sets, &settings)
        .expect("analyze rank-confounded geometry");

    assert_eq!(
        report.decision,
        SemanticBranchDecision::NoRecoverableBranches
    );
    for label_set in report.label_sets {
        assert_eq!(label_set.macro_mean_anchor_auroc, Some(1.0));
        assert_eq!(label_set.macro_permutation_95th_percentile, Some(1.0));
        assert!(!label_set.macro_above_permutation_95th_percentile);
    }
}

#[test]
fn themes_that_only_separate_from_a_third_theme_are_not_recoverable_as_a_pair() {
    let mut candidates = Vec::new();
    let mut labels = BTreeMap::new();
    let mut rank = 1_u32;
    for quartile in 0..4_u8 {
        for within_quartile in 0..2 {
            let physical_id = format!("Q{quartile}-P{within_quartile}");
            candidates.push(candidate(&physical_id, rank, quartile, [1.0, 0.0]));
            labels.insert(physical_id, BranchLabel::themes([Theme::Physical]));
            rank += 1;

            let mental_id = format!("Q{quartile}-M{within_quartile}");
            candidates.push(candidate(&mental_id, rank, quartile, [1.0, 0.0]));
            labels.insert(mental_id, BranchLabel::themes([Theme::Mental]));
            rank += 1;
        }

        let spiritual_in_quartile = if quartile < 3 { 2 } else { 1 };
        for within_quartile in 0..spiritual_in_quartile {
            let spiritual_id = format!("Q{quartile}-S{within_quartile}");
            candidates.push(candidate(&spiritual_id, rank, quartile, [-1.0, 0.0]));
            labels.insert(spiritual_id, BranchLabel::themes([Theme::Spiritual]));
            rank += 1;
        }
    }
    let label_sets = [
        BranchLabelSet::new("labeler-a", labels.clone()).expect("first independent label set"),
        BranchLabelSet::new("labeler-b", labels).expect("second independent label set"),
    ];
    let settings = BranchSettings::new(8, 500, "pairwise-separation-v1").expect("valid settings");

    let report = analyze_semantic_branches(&candidates, &label_sets, &settings)
        .expect("analyze themes sharing one direction");

    assert_eq!(
        report.decision,
        SemanticBranchDecision::NoRecoverableBranches
    );
    assert!(report.common_distinct_significant_pairs.is_empty());
    for label_set in report.label_sets {
        assert!(label_set.macro_above_permutation_95th_percentile);
        assert_eq!(label_set.pair_metrics.len(), 1);
        let pair = &label_set.pair_metrics[0];
        assert_eq!(
            pair.pair,
            ThemePair {
                first: Theme::Physical,
                second: Theme::Mental,
            }
        );
        assert_eq!(pair.first_exclusive_notes, 8);
        assert_eq!(pair.second_exclusive_notes, 8);
        assert!((pair.mean_anchor_auroc - 0.5).abs() < 0.03);
        assert!(pair.permutation_95th_percentile >= pair.mean_anchor_auroc);
        assert!(pair.permutation_p_value > 0.05);
        assert!(!pair.above_permutation_95th_percentile);
    }
}

#[test]
fn candidate_rejects_non_unit_vectors_and_invalid_cached_cosines() {
    assert_eq!(
        SemanticBranchCandidate::new("note".to_owned(), 1, 0, 0.5, vec![2.0, 0.0]),
        Err(BranchGeometryError::NonUnitVector)
    );
    assert_eq!(
        SemanticBranchCandidate::new("note".to_owned(), 1, 0, 1.1, vec![1.0, 0.0]),
        Err(BranchGeometryError::CachedCosineOutOfRange)
    );
    assert_eq!(
        SemanticBranchCandidate::new("note".to_owned(), 1, 0, 1.0, vec![1.0, 0.0]),
        Err(BranchGeometryError::DegenerateTangentDirection)
    );
}

#[test]
fn candidate_accepts_the_representation_unit_norm_tolerance() {
    SemanticBranchCandidate::new("note".to_owned(), 1, 0, 0.5, vec![1.000_05, 0.0])
        .expect("representation-valid unit vector must remain valid for branch analysis");
}

#[test]
fn analysis_rejects_cached_scores_that_increase_with_worse_rank() {
    let candidates = [
        SemanticBranchCandidate::new("first".to_owned(), 1, 0, 0.5, vec![1.0, 0.0])
            .expect("first candidate"),
        SemanticBranchCandidate::new("second".to_owned(), 2, 0, 0.6, vec![0.0, 1.0])
            .expect("second candidate"),
    ];
    let labels = BTreeMap::from([
        ("first".to_owned(), BranchLabel::themes([Theme::Physical])),
        ("second".to_owned(), BranchLabel::themes([Theme::Mental])),
    ]);
    let label_sets = [
        BranchLabelSet::new("labeler-a", labels.clone()).expect("first label set"),
        BranchLabelSet::new("labeler-b", labels).expect("second label set"),
    ];
    let settings = BranchSettings::new(2, 10, "invalid-score-order-v1").expect("valid settings");

    assert_eq!(
        analyze_semantic_branches(&candidates, &label_sets, &settings),
        Err(BranchGeometryError::CachedCosineRankOrder)
    );
}

#[test]
fn fewer_than_two_qualifying_exclusive_themes_is_underdetermined() {
    let mut candidates = Vec::new();
    let mut labels = BTreeMap::new();
    for index in 0..15_u32 {
        let id = format!("N{index}");
        candidates.push(candidate(
            &id,
            index + 1,
            0,
            if index < 8 { [1.0, 0.0] } else { [0.0, 1.0] },
        ));
        labels.insert(
            id,
            BranchLabel::themes([if index < 8 {
                Theme::Physical
            } else {
                Theme::Mental
            }]),
        );
    }
    let label_sets = [
        BranchLabelSet::new("labeler-a", labels.clone()).expect("first label set"),
        BranchLabelSet::new("labeler-b", labels).expect("second label set"),
    ];
    let settings =
        BranchSettings::new(8, 20, "insufficient-exclusive-themes-v1").expect("valid settings");

    let report = analyze_semantic_branches(&candidates, &label_sets, &settings)
        .expect("analyze insufficient exclusive themes");

    assert_eq!(report.decision, SemanticBranchDecision::Underdetermined);
    assert!(report.common_distinct_qualifying_pairs.is_empty());
}

#[test]
fn analysis_requires_exactly_two_independent_label_sets() {
    let candidates = [
        candidate("first", 1, 0, [1.0, 0.0]),
        candidate("second", 2, 0, [0.0, 1.0]),
    ];
    let labels = BTreeMap::from([
        ("first".to_owned(), BranchLabel::themes([Theme::Physical])),
        ("second".to_owned(), BranchLabel::themes([Theme::Mental])),
    ]);
    let one_label_set =
        [BranchLabelSet::new("labeler-a", labels).expect("construct one label set")];
    let settings = BranchSettings::new(2, 10, "two-label-sets-v1").expect("valid settings");

    assert_eq!(
        analyze_semantic_branches(&candidates, &one_label_set, &settings),
        Err(BranchGeometryError::WrongLabelSetCount)
    );
}

const FRAC: f64 = std::f64::consts::FRAC_1_SQRT_2;

fn candidate(
    id: &str,
    rank: u32,
    rank_quartile: u8,
    tangent_direction: [f64; 2],
) -> SemanticBranchCandidate {
    let cached_cosine = 0.9 - f64::from(rank) * 0.000_1;
    let tangent_scale = (1.0 - cached_cosine * cached_cosine).sqrt();
    SemanticBranchCandidate::new(
        id.to_owned(),
        rank,
        rank_quartile,
        cached_cosine,
        vec![
            cached_cosine as f32,
            (tangent_scale * tangent_direction[0]) as f32,
            (tangent_scale * tangent_direction[1]) as f32,
        ],
    )
    .expect("construct valid branch candidate")
}
