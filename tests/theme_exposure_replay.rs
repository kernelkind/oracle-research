use std::collections::{BTreeMap, BTreeSet};

use oracle_mvp::theme_exposure_replay::{
    ExposureReplayDecision, ExposureReplaySettings, analyze_exposure_replay,
};
use oracle_mvp::theme_geometry_diagnostic::{Theme, ThemeLabelSet, ThemeNote};

#[test]
fn cumulative_vector_exposure_tracks_three_repeated_theme_histories() {
    let mut labels = BTreeMap::new();
    let notes = (0..30)
        .map(|index| {
            let (theme, vector) = match index % 3 {
                0 => (Theme::Nostr, vec![1.0, 0.0, 0.0]),
                1 => (Theme::Cryptocurrency, vec![0.0, 1.0, 0.0]),
                _ => (Theme::LlmAi, vec![0.0, 0.0, 1.0]),
            };
            let id = format!("T{:03}", index + 1);
            labels.insert(id.clone(), BTreeSet::from([theme]));
            ThemeNote::new(id, vector).expect("construct normalized theme note")
        })
        .collect::<Vec<_>>();
    let label_sets = [
        ThemeLabelSet::new("labeler-a", labels.clone()).expect("construct first label set"),
        ThemeLabelSet::new("labeler-b", labels).expect("construct second label set"),
    ];
    let settings =
        ExposureReplaySettings::new(8, 20, [10, 40], 500, "theme-exposure-replay-test-v1")
            .expect("construct replay settings");

    let report = analyze_exposure_replay(&notes, &label_sets, &settings)
        .expect("analyze cumulative exposure");

    assert_eq!(
        report.decision(),
        ExposureReplayDecision::ProceedToLiveProbe
    );
    assert_eq!(report.typical_pair_cosine(), 0.0);
    assert_eq!(
        report.common_primary_significant_families(),
        &BTreeSet::from([Theme::Cryptocurrency, Theme::LlmAi, Theme::Nostr])
    );
    assert_eq!(
        report.label_sets[0].primary, report.label_sets[1].primary,
        "one vector permutation stream must be shared across both label sets"
    );
    let primary = &report.label_sets[0].primary;
    assert_eq!(primary.macro_permutation_valid_draws, 500);
    assert!(
        (primary
            .macro_permutation_95th_percentile
            .expect("testable macro null")
            - 0.963_636_363_636_363_7)
            .abs()
            < 1.0e-12,
        "this exact null locks in vector-identity permutation rather than label permutation"
    );
    assert!(
        (primary
            .macro_permutation_p_value
            .expect("testable macro p-value")
            - 0.001_996_007_984_031_936)
            .abs()
            < 1.0e-15
    );
    for metric in primary.family_metrics.values() {
        assert_eq!(metric.permutation_valid_draws, 500);
        assert!(
            (metric
                .permutation_95th_percentile
                .expect("testable family null")
                - 0.975_757_575_757_575_7)
                .abs()
                < 1.0e-12
        );
    }

    let repeated = analyze_exposure_replay(&notes, &label_sets, &settings)
        .expect("repeat deterministic cumulative exposure analysis");
    assert_eq!(report, repeated);
}

#[test]
fn exposure_uses_only_prior_presentations_and_the_declared_decay() {
    let vectors = [
        vec![1.0, 0.0, 0.0],
        vec![1.0, 0.0, 0.0],
        vec![0.0, 1.0, 0.0],
        vec![0.0, 1.0, 0.0],
    ];
    let notes = vectors
        .into_iter()
        .enumerate()
        .map(|(index, vector)| {
            ThemeNote::new(format!("T{:03}", index + 1), vector)
                .expect("construct normalized replay note")
        })
        .collect::<Vec<_>>();
    let labels = notes
        .iter()
        .map(|note| (note.id().to_owned(), BTreeSet::from([Theme::Nostr])))
        .collect::<BTreeMap<_, _>>();
    let label_sets = [
        ThemeLabelSet::new("labeler-a", labels.clone()).expect("construct first label set"),
        ThemeLabelSet::new("labeler-b", labels).expect("construct second label set"),
    ];
    let settings = ExposureReplaySettings::new(2, 20, [10, 40], 20, "causal-exposure-test-v1")
        .expect("construct replay settings");

    let report =
        analyze_exposure_replay(&notes, &label_sets, &settings).expect("analyze prior exposure");
    let trace = report.exposure_trace(20).expect("primary exposure trace");
    let one_step_decay = 2.0_f64.powf(-1.0 / 20.0);

    assert_eq!(report.typical_pair_cosine(), 0.0);
    assert_eq!(trace[0].exposure, 0.0);
    assert!((trace[1].exposure - one_step_decay).abs() < 1.0e-12);
    assert_eq!(
        trace[2].exposure, 0.0,
        "a similar future note must not contribute before it is shown"
    );
    assert!((trace[3].exposure - one_step_decay).abs() < 1.0e-12);
}

#[test]
fn both_nontracking_label_sets_stop_the_current_formula() {
    let notes = block_notes();
    let labels = labels_from_family_order(
        &notes,
        &[
            2, 2, 1, 2, 1, 1, 2, 0, 2, 1, 1, 2, 1, 2, 0, 0, 1, 1, 0, 0, 2, 0, 0, 0,
        ],
    );
    let label_sets = [
        ThemeLabelSet::new("labeler-a", labels.clone()).expect("construct first label set"),
        ThemeLabelSet::new("labeler-b", labels).expect("construct second label set"),
    ];

    let report = analyze_exposure_replay(&notes, &label_sets, &replay_settings())
        .expect("analyze nontracking histories");

    assert_eq!(
        report.decision(),
        ExposureReplayDecision::StopCurrentFormula
    );
}

#[test]
fn disagreement_between_label_sets_is_underdetermined() {
    let notes = block_notes();
    let matching = labels_from_family_order(
        &notes,
        &[
            0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2,
        ],
    );
    let nontracking = labels_from_family_order(
        &notes,
        &[
            2, 2, 1, 2, 1, 1, 2, 0, 2, 1, 1, 2, 1, 2, 0, 0, 1, 1, 0, 0, 2, 0, 0, 0,
        ],
    );
    let label_sets = [
        ThemeLabelSet::new("labeler-a", matching).expect("construct matching label set"),
        ThemeLabelSet::new("labeler-b", nontracking).expect("construct nontracking label set"),
    ];

    let report = analyze_exposure_replay(&notes, &label_sets, &replay_settings())
        .expect("analyze disagreeing histories");

    assert_eq!(report.decision(), ExposureReplayDecision::Underdetermined);
}

#[test]
fn undefined_correlations_remain_underdetermined_instead_of_becoming_zero() {
    let notes = (0..8)
        .map(|index| {
            ThemeNote::new(format!("T{:03}", index + 1), vec![1.0, 0.0, 0.0])
                .expect("construct identical note vector")
        })
        .collect::<Vec<_>>();
    let labels = notes
        .iter()
        .map(|note| (note.id().to_owned(), BTreeSet::from([Theme::Nostr])))
        .collect::<BTreeMap<_, _>>();
    let label_sets = [
        ThemeLabelSet::new("labeler-a", labels.clone()).expect("construct first label set"),
        ThemeLabelSet::new("labeler-b", labels).expect("construct second label set"),
    ];

    let report = analyze_exposure_replay(&notes, &label_sets, &replay_settings())
        .expect("analyze constant exposure");
    let metric = &report.label_sets[0].primary.family_metrics[&Theme::Nostr];

    assert_eq!(metric.spearman, None);
    assert_eq!(metric.permutation_valid_draws, 0);
    assert_eq!(metric.permutation_95th_percentile, None);
    assert_eq!(report.decision(), ExposureReplayDecision::Underdetermined);
}

#[test]
fn even_pair_median_and_tied_spearman_ranks_are_exact() {
    let notes = [
        vec![1.0, 0.0],
        vec![0.0, 1.0],
        vec![1.0, 0.0],
        vec![1.0, 0.0],
    ]
    .into_iter()
    .enumerate()
    .map(|(index, vector)| {
        ThemeNote::new(format!("T{:03}", index + 1), vector).expect("construct tied-rank note")
    })
    .collect::<Vec<_>>();
    let labels = notes
        .iter()
        .map(|note| (note.id().to_owned(), BTreeSet::from([Theme::Nostr])))
        .collect::<BTreeMap<_, _>>();
    let label_sets = [
        ThemeLabelSet::new("labeler-a", labels.clone()).expect("construct first label set"),
        ThemeLabelSet::new("labeler-b", labels).expect("construct second label set"),
    ];
    let settings = ExposureReplaySettings::new(2, 20, [10, 40], 20, "tied-rank-test-v1")
        .expect("construct replay settings");

    let report =
        analyze_exposure_replay(&notes, &label_sets, &settings).expect("analyze tied ranks");
    let rho = report.label_sets[0].primary.family_metrics[&Theme::Nostr]
        .spearman
        .expect("testable tied-rank correlation");

    assert_eq!(report.typical_pair_cosine(), 0.5);
    assert!((rho - 0.9_f64.sqrt()).abs() < 1.0e-12);
}

fn block_notes() -> Vec<ThemeNote> {
    (0..24)
        .map(|index| {
            let vector = match index / 8 {
                0 => vec![1.0, 0.0, 0.0],
                1 => vec![0.0, 1.0, 0.0],
                _ => vec![0.0, 0.0, 1.0],
            };
            ThemeNote::new(format!("T{:03}", index + 1), vector).expect("construct block note")
        })
        .collect()
}

fn labels_from_family_order(
    notes: &[ThemeNote],
    family_order: &[usize],
) -> BTreeMap<String, BTreeSet<Theme>> {
    let families = [Theme::Nostr, Theme::Cryptocurrency, Theme::LlmAi];
    notes
        .iter()
        .zip(family_order)
        .map(|(note, family)| (note.id().to_owned(), BTreeSet::from([families[*family]])))
        .collect()
}

fn replay_settings() -> ExposureReplaySettings {
    ExposureReplaySettings::new(8, 20, [10, 40], 500, "decision-boundary-test-v1")
        .expect("construct replay settings")
}
