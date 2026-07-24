use std::collections::BTreeSet;

use oracle_mvp::adjacent_novelty::{ExposureCandidate, StaticExposureSelector};
use oracle_mvp::representation::EventId;

const CREC_102_TYPICAL_PAIR_COSINE: f64 = 0.420_874_672_461_660_55;
const CREC_102_HALF_LIFE: f64 = 20.0;

#[test]
fn selection_excludes_history_and_never_repeats_a_recorded_presentation() {
    let candidates = (0..45).map(|index| candidate(index, [1.0, 0.0])).collect();
    let historical = BTreeSet::from([event_id(0), event_id(2)]);
    let mut selector =
        StaticExposureSelector::new(candidates, historical).expect("construct selector");

    let selected = select_all(&mut selector);

    assert_eq!(selected.len(), 40, "the static live-probe quota is fixed");
    assert_eq!(selected[0], event_id(1));
    assert_eq!(selected[1], event_id(3));
    assert!(!selected.contains(&event_id(0)));
    assert!(!selected.contains(&event_id(2)));
    assert_eq!(
        selected.iter().copied().collect::<BTreeSet<_>>().len(),
        selected.len(),
        "recorded presentations must never be selected again"
    );
    assert_eq!(selector.presentations_recorded(), 40);
    assert!(selector.is_complete());
}

#[test]
fn each_step_minimizes_exposure_only_within_the_top_64_remaining_candidates() {
    let mut candidates = Vec::new();
    candidates.push(candidate(0, [1.0, 0.0]));
    for index in 1..=66 {
        let vector = match index {
            65 => [0.5, 0.75_f32.sqrt()],
            66 => [0.0, 1.0],
            _ => [1.0, 0.0],
        };
        candidates.push(candidate(index, vector));
    }
    let mut selector = StaticExposureSelector::new(candidates, BTreeSet::from([event_id(1)]))
        .expect("construct selector");

    let first = selector
        .select_next()
        .expect("select first candidate")
        .expect("first candidate exists");
    assert_eq!(first.event_id(), event_id(0));
    selector
        .record_presentation()
        .expect("record first presentation");

    let second = selector
        .select_next()
        .expect("select second candidate")
        .expect("second candidate exists");

    assert_eq!(
        second.event_id(),
        event_id(65),
        "the least-exposed candidate inside the top-64 window must win"
    );
    assert_eq!(second.support_order_index(), 65);
    assert!(second.exposure() > 0.0);
    assert_ne!(
        second.event_id(),
        event_id(66),
        "a lower-exposure candidate outside the top-64 window is not eligible"
    );
}

#[test]
fn exposure_uses_the_frozen_crec_102_baseline_and_half_life() {
    let candidates = vec![candidate(0, [1.0, 0.0]), candidate(1, [1.0, 0.0])];
    let mut selector =
        StaticExposureSelector::new(candidates, BTreeSet::new()).expect("construct selector");

    let first = selector
        .select_next()
        .expect("select first candidate")
        .expect("first candidate exists");
    assert_eq!(first.exposure(), 0.0);
    selector
        .record_presentation()
        .expect("record first presentation");

    let second = selector
        .select_next()
        .expect("select second candidate")
        .expect("second candidate exists");
    let expected = (1.0 - CREC_102_TYPICAL_PAIR_COSINE) * 2.0_f64.powf(-1.0 / CREC_102_HALF_LIFE);

    assert!(
        (second.exposure() - expected).abs() < 1.0e-12,
        "expected {expected}, got {}",
        second.exposure()
    );
}

#[test]
fn recording_a_presentation_updates_exposure_without_any_outcome_input() {
    let candidates = vec![
        candidate(0, [1.0, 0.0]),
        candidate(1, [1.0, 0.0]),
        candidate(2, [0.0, 1.0]),
    ];
    let mut selector =
        StaticExposureSelector::new(candidates, BTreeSet::new()).expect("construct selector");

    let first = selector
        .select_next()
        .expect("select first candidate")
        .expect("first candidate exists");
    assert_eq!(first.event_id(), event_id(0));

    // Rating, wrong-language, and any later diagnostic outcome live outside
    // this pure core. Once presentation is recorded, its vector must affect
    // the next choice identically for every outcome.
    selector
        .record_presentation()
        .expect("record outcome-independent presentation");

    let second = selector
        .select_next()
        .expect("select second candidate")
        .expect("second candidate exists");
    assert_eq!(
        second.event_id(),
        event_id(2),
        "the recorded first vector must make the orthogonal note least exposed"
    );
}

#[test]
fn exposure_ties_preserve_frozen_support_order_and_the_run_is_deterministic() {
    let historical = BTreeSet::from([event_id(1)]);
    let mut first = StaticExposureSelector::new(
        (0..45).map(|index| candidate(index, [1.0, 0.0])).collect(),
        historical.clone(),
    )
    .expect("construct first selector");
    let mut repeated = StaticExposureSelector::new(
        (0..45).map(|index| candidate(index, [1.0, 0.0])).collect(),
        historical,
    )
    .expect("construct repeated selector");

    let first_order = select_all(&mut first);
    let repeated_order = select_all(&mut repeated);
    let expected = std::iter::once(event_id(0))
        .chain((2..=40).map(event_id))
        .collect::<Vec<_>>();

    assert_eq!(first_order, expected);
    assert_eq!(repeated_order, expected);
    assert!(
        first
            .select_next()
            .expect("query completed selector")
            .is_none(),
        "eligible candidates beyond the quota must not extend the run"
    );
}

fn select_all(selector: &mut StaticExposureSelector) -> Vec<EventId> {
    let mut event_ids = Vec::new();
    while let Some(selection) = selector.select_next().expect("select next candidate") {
        event_ids.push(selection.event_id());
        selector
            .record_presentation()
            .expect("record selected presentation");
    }
    event_ids
}

fn candidate(index: u8, vector: [f32; 2]) -> ExposureCandidate {
    ExposureCandidate::new(event_id(index), vector.to_vec()).expect("construct candidate")
}

fn event_id(index: u8) -> EventId {
    [index; 32]
}
