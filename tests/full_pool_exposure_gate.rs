use std::collections::BTreeSet;

use oracle_mvp::adjacent_novelty::{
    AdjacentNoveltyError, CREC_102_EXPOSURE_HALF_LIFE, CREC_102_TYPICAL_PAIR_COSINE,
    ExposureCandidate, FullPoolExposureGateSelector,
};
use oracle_mvp::representation::EventId;

#[test]
fn seeded_exposure_rejects_an_exhausted_top_candidate_and_scans_the_full_pool() {
    let mut candidates = (1..=65)
        .map(|index| candidate(index, [1.0, 0.0]))
        .collect::<Vec<_>>();
    candidates.push(candidate(66, [0.0, 1.0]));
    let seeded_history = vec![candidate(100, [1.0, 0.0])];
    let mut selector = FullPoolExposureGateSelector::new(
        candidates,
        BTreeSet::new(),
        seeded_history,
        0.326_866_384_608_866_58,
        20,
    )
    .expect("construct full-pool selector");

    let selected = selector
        .select_next()
        .expect("select from the full pool")
        .expect("one candidate survives the ceiling");

    assert_eq!(selected.event_id(), event_id(66));
    assert_eq!(selected.support_order_index(), 65);
    assert_eq!(selected.survivor_count(), 1);
    assert_eq!(selected.rejected_by_ceiling_count(), 65);
    assert!(selected.exposure() < selector.exposure_ceiling());
}

#[test]
fn highest_support_survivor_wins_even_when_a_lower_candidate_has_less_exposure() {
    let candidates = vec![candidate(1, [0.6, 0.8]), candidate(2, [0.0, 1.0])];
    let mut selector = FullPoolExposureGateSelector::new(
        candidates,
        BTreeSet::new(),
        vec![candidate(100, [1.0, 0.0])],
        0.326_866_384_608_866_58,
        20,
    )
    .expect("construct selector");

    let selected = selector
        .select_next()
        .expect("scan full pool")
        .expect("two candidates survive");

    assert_eq!(selected.event_id(), event_id(1));
    assert_eq!(selected.support_order_index(), 0);
    assert_eq!(selected.survivor_count(), 2);
}

#[test]
fn exposure_equal_to_the_ceiling_is_rejected_without_a_fallback() {
    let cosine = 0.75_f32;
    let unit_y = (1.0_f32 - cosine * cosine).sqrt();
    let decay = 2.0_f64.powf(-1.0 / f64::from(CREC_102_EXPOSURE_HALF_LIFE));
    let exact_exposure = decay * (f64::from(cosine) - CREC_102_TYPICAL_PAIR_COSINE).max(0.0);
    let mut selector = FullPoolExposureGateSelector::new(
        vec![candidate(1, [cosine, unit_y])],
        BTreeSet::new(),
        vec![candidate(100, [1.0, 0.0])],
        exact_exposure,
        20,
    )
    .expect("construct selector");

    assert_eq!(
        selector.select_next().expect("scan full pool"),
        None,
        "the hard gate is strict and must not fall back to an over-ceiling note"
    );
}

#[test]
fn incremental_exposure_matches_the_frozen_direct_formula() {
    let seed = candidate(100, [1.0, 0.0]);
    let shown_first = candidate(1, [0.0, 1.0]);
    let shown_second = candidate(2, [0.6, 0.8]);
    let target = candidate(3, [0.8, 0.6]);
    let history = [
        seed.vector().to_vec(),
        shown_first.vector().to_vec(),
        shown_second.vector().to_vec(),
    ];
    let mut selector = FullPoolExposureGateSelector::new(
        vec![shown_first, shown_second, target.clone()],
        BTreeSet::new(),
        vec![seed],
        10.0,
        3,
    )
    .expect("construct selector");

    for expected in [event_id(1), event_id(2)] {
        let selected = selector
            .select_next()
            .expect("select")
            .expect("candidate remains");
        assert_eq!(selected.event_id(), expected);
        selector.record_presentation().expect("record");
    }
    let selected = selector
        .select_next()
        .expect("select target")
        .expect("target remains");

    let direct = direct_exposure(target.vector(), &history);
    assert!(
        (selected.exposure() - direct).abs() < 1.0e-12,
        "incremental={}, direct={direct}",
        selected.exposure()
    );
}

#[test]
fn seeded_exposure_history_must_be_distinct_from_preexisting_exclusions() {
    let error = match FullPoolExposureGateSelector::new(
        vec![candidate(1, [0.0, 1.0])],
        BTreeSet::from([event_id(100)]),
        vec![candidate(100, [1.0, 0.0])],
        0.326_866_384_608_866_58,
        20,
    ) {
        Ok(_) => panic!("seeded history must not silently overlap older exclusions"),
        Err(error) => error,
    };

    assert_eq!(
        error,
        AdjacentNoveltyError::SeededHistoryAlreadyExcluded {
            event_id: event_id(100)
        }
    );
}

fn direct_exposure(candidate: &[f32], history: &[Vec<f32>]) -> f64 {
    history
        .iter()
        .enumerate()
        .map(|(index, prior)| {
            let cosine = candidate
                .iter()
                .zip(prior)
                .map(|(left, right)| f64::from(*left) * f64::from(*right))
                .sum::<f64>();
            let age = history.len() - index;
            let decay = 2.0_f64.powf(-(age as f64) / f64::from(CREC_102_EXPOSURE_HALF_LIFE));
            decay * (cosine - CREC_102_TYPICAL_PAIR_COSINE).max(0.0)
        })
        .sum()
}

fn candidate(index: u8, vector: [f32; 2]) -> ExposureCandidate {
    ExposureCandidate::new(event_id(index), vector.to_vec()).expect("construct candidate")
}

fn event_id(index: u8) -> EventId {
    [index; 32]
}
