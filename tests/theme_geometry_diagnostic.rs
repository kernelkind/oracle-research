use std::collections::{BTreeMap, BTreeSet};

use oracle_mvp::theme_geometry_diagnostic::{
    DiagnosticDecision, GeometryAnalysisSettings, Theme, ThemeLabelSet, ThemeNote, analyze_geometry,
};

#[test]
fn clear_multi_theme_geometry_proceeds_to_exposure_replay() {
    let notes = (0..30)
        .map(|index| {
            let vector = match index / 10 {
                0 => vec![1.0, 0.0, 0.0],
                1 => vec![0.0, 1.0, 0.0],
                _ => vec![0.0, 0.0, 1.0],
            };
            ThemeNote::new(format!("T{:03}", index + 1), vector)
                .expect("construct normalized fixture note")
        })
        .collect::<Vec<_>>();
    let labels = (0..30)
        .map(|index| {
            let theme = match index / 10 {
                0 => Theme::Nostr,
                1 => Theme::Cryptocurrency,
                _ => Theme::Other,
            };
            (format!("T{:03}", index + 1), BTreeSet::from([theme]))
        })
        .collect::<BTreeMap<_, _>>();
    let label_sets = [
        ThemeLabelSet::new("labeler-a", labels.clone()).expect("construct first label set"),
        ThemeLabelSet::new("labeler-b", labels).expect("construct second label set"),
    ];
    let settings = GeometryAnalysisSettings::new(8, 500, "theme-geometry-diagnostic-test-v1")
        .expect("construct analysis settings");

    let report = analyze_geometry(&notes, &label_sets, &settings).expect("analyze clear geometry");

    assert_eq!(
        report.decision(),
        DiagnosticDecision::ProceedToExposureReplay
    );
    assert_eq!(
        report.common_significant_themes(),
        &BTreeSet::from([Theme::Cryptocurrency, Theme::Nostr])
    );
}

#[test]
fn absent_qualifying_themes_are_underdetermined_not_evidence_to_stop() {
    let notes = (0..10)
        .map(|index| {
            let angle = index as f32 * 0.1;
            ThemeNote::new(format!("T{:03}", index + 1), vec![angle.cos(), angle.sin()])
                .expect("construct normalized fixture note")
        })
        .collect::<Vec<_>>();
    let labels = (0..10)
        .map(|index| (format!("T{:03}", index + 1), BTreeSet::from([Theme::Other])))
        .collect::<BTreeMap<_, _>>();
    let label_sets = [
        ThemeLabelSet::new("labeler-a", labels.clone()).expect("construct first label set"),
        ThemeLabelSet::new("labeler-b", labels).expect("construct second label set"),
    ];
    let settings = GeometryAnalysisSettings::new(8, 100, "no-qualifying-theme-test-v1")
        .expect("construct analysis settings");

    let report = analyze_geometry(&notes, &label_sets, &settings).expect("analyze absent themes");

    assert_eq!(report.decision(), DiagnosticDecision::Underdetermined);
}

#[test]
fn one_qualifying_theme_is_underdetermined_even_without_separation() {
    let notes = (0..20)
        .map(|index| {
            ThemeNote::new(format!("T{:03}", index + 1), vec![1.0, 0.0])
                .expect("construct normalized fixture note")
        })
        .collect::<Vec<_>>();
    let labels = (0..20)
        .map(|index| {
            let theme = if index < 10 {
                Theme::Nostr
            } else {
                Theme::Other
            };
            (format!("T{:03}", index + 1), BTreeSet::from([theme]))
        })
        .collect::<BTreeMap<_, _>>();
    let label_sets = [
        ThemeLabelSet::new("labeler-a", labels.clone()).expect("construct first label set"),
        ThemeLabelSet::new("labeler-b", labels).expect("construct second label set"),
    ];
    let settings = GeometryAnalysisSettings::new(8, 100, "one-qualifying-theme-test-v1")
        .expect("construct analysis settings");

    let report = analyze_geometry(&notes, &label_sets, &settings).expect("analyze one theme");

    assert_eq!(report.decision(), DiagnosticDecision::Underdetermined);
}

#[test]
fn coextensive_theme_labels_do_not_count_as_two_distinct_regions() {
    let notes = (0..30)
        .map(|index| {
            let vector = if index < 10 {
                vec![1.0, 0.0]
            } else {
                vec![0.0, 1.0]
            };
            ThemeNote::new(format!("T{:03}", index + 1), vector)
                .expect("construct normalized fixture note")
        })
        .collect::<Vec<_>>();
    let labels = (0..30)
        .map(|index| {
            let themes = if index < 10 {
                BTreeSet::from([Theme::Nostr, Theme::Cryptocurrency])
            } else {
                BTreeSet::from([Theme::Other])
            };
            (format!("T{:03}", index + 1), themes)
        })
        .collect::<BTreeMap<_, _>>();
    let label_sets = [
        ThemeLabelSet::new("labeler-a", labels.clone()).expect("construct first label set"),
        ThemeLabelSet::new("labeler-b", labels).expect("construct second label set"),
    ];
    let settings = GeometryAnalysisSettings::new(8, 500, "coextensive-theme-labels-test-v1")
        .expect("construct analysis settings");

    let report =
        analyze_geometry(&notes, &label_sets, &settings).expect("analyze coextensive themes");

    assert_eq!(report.decision(), DiagnosticDecision::Underdetermined);
}

#[test]
fn two_distinct_themes_without_geometry_stop_the_vector_exposure_path() {
    let notes = (0..30)
        .map(|index| {
            ThemeNote::new(format!("T{:03}", index + 1), vec![1.0, 0.0])
                .expect("construct normalized fixture note")
        })
        .collect::<Vec<_>>();
    let labels = (0..30)
        .map(|index| {
            let theme = match index / 10 {
                0 => Theme::Nostr,
                1 => Theme::Cryptocurrency,
                _ => Theme::Other,
            };
            (format!("T{:03}", index + 1), BTreeSet::from([theme]))
        })
        .collect::<BTreeMap<_, _>>();
    let label_sets = [
        ThemeLabelSet::new("labeler-a", labels.clone()).expect("construct first label set"),
        ThemeLabelSet::new("labeler-b", labels).expect("construct second label set"),
    ];
    let settings = GeometryAnalysisSettings::new(8, 500, "no-theme-geometry-test-v1")
        .expect("construct analysis settings");

    let report = analyze_geometry(&notes, &label_sets, &settings).expect("analyze absent geometry");

    assert_eq!(
        report.decision(),
        DiagnosticDecision::StopCurrentVectorExposure
    );
}
