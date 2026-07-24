//! Frozen replay of presentation-based thematic exposure.

use std::collections::{BTreeMap, BTreeSet};

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use thiserror::Error;

use crate::theme_geometry_diagnostic::{Theme, ThemeLabelSet, ThemeNote};

const NULL_QUANTILE_NUMERATOR: usize = 95;
const NULL_QUANTILE_DENOMINATOR: usize = 100;
const EXPOSURE_FAMILIES: [Theme; 3] = [Theme::Nostr, Theme::Cryptocurrency, Theme::LlmAi];

pub type Result<T> = std::result::Result<T, ExposureReplayError>;

#[derive(Debug, Error, PartialEq)]
pub enum ExposureReplayError {
    #[error("minimum family notes must be at least two")]
    InvalidMinimumFamilyNotes,
    #[error("primary half-life must be positive")]
    InvalidPrimaryHalfLife,
    #[error("sensitivity half-lives must be positive and distinct")]
    InvalidSensitivityHalfLives,
    #[error("permutation count must be positive")]
    InvalidPermutationCount,
    #[error("permutation seed must be nonempty")]
    EmptyPermutationSeed,
    #[error("the replay requires at least two notes")]
    TooFewNotes,
    #[error("the replay requires exactly two independent label sets")]
    WrongLabelSetCount,
    #[error("duplicate replay note ID `{0}`")]
    DuplicateNoteId(String),
    #[error("vector dimension mismatch: expected {expected}, got {actual}")]
    DimensionMismatch { expected: usize, actual: usize },
    #[error("label set `{label_set}` does not exactly cover the note IDs")]
    LabelCoverage { label_set: String },
    #[error("replay calculation produced a non-finite value")]
    NonFiniteResult,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ExposureReplaySettings {
    minimum_family_notes: usize,
    primary_half_life: u32,
    sensitivity_half_lives: [u32; 2],
    permutations: usize,
    permutation_seed: String,
}

impl ExposureReplaySettings {
    pub fn new(
        minimum_family_notes: usize,
        primary_half_life: u32,
        sensitivity_half_lives: [u32; 2],
        permutations: usize,
        permutation_seed: impl Into<String>,
    ) -> Result<Self> {
        if minimum_family_notes < 2 {
            return Err(ExposureReplayError::InvalidMinimumFamilyNotes);
        }
        if primary_half_life == 0 {
            return Err(ExposureReplayError::InvalidPrimaryHalfLife);
        }
        if sensitivity_half_lives[0] == 0
            || sensitivity_half_lives[1] == 0
            || sensitivity_half_lives[0] == sensitivity_half_lives[1]
            || sensitivity_half_lives.contains(&primary_half_life)
        {
            return Err(ExposureReplayError::InvalidSensitivityHalfLives);
        }
        if permutations == 0 {
            return Err(ExposureReplayError::InvalidPermutationCount);
        }
        let permutation_seed = permutation_seed.into();
        if permutation_seed.is_empty() {
            return Err(ExposureReplayError::EmptyPermutationSeed);
        }
        Ok(Self {
            minimum_family_notes,
            primary_half_life,
            sensitivity_half_lives,
            permutations,
            permutation_seed,
        })
    }

    pub fn minimum_family_notes(&self) -> usize {
        self.minimum_family_notes
    }

    pub fn primary_half_life(&self) -> u32 {
        self.primary_half_life
    }

    pub fn sensitivity_half_lives(&self) -> [u32; 2] {
        self.sensitivity_half_lives
    }

    pub fn permutations(&self) -> usize {
        self.permutations
    }

    pub fn permutation_seed(&self) -> &str {
        &self.permutation_seed
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ExposureReplayDecision {
    ProceedToLiveProbe,
    StopCurrentFormula,
    Underdetermined,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
pub struct ExposureTracePoint {
    pub presentation_ordinal: u32,
    pub note_id: String,
    pub exposure: f64,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
pub struct ExposureCorrelationMetric {
    pub labeled_notes: usize,
    pub spearman: Option<f64>,
    pub permutation_valid_draws: usize,
    pub permutation_95th_percentile: Option<f64>,
    pub permutation_p_value: Option<f64>,
    pub above_permutation_95th_percentile: bool,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
pub struct ExposureHalfLifeReport {
    pub half_life: u32,
    pub family_metrics: BTreeMap<Theme, ExposureCorrelationMetric>,
    pub macro_spearman: Option<f64>,
    pub macro_permutation_valid_draws: usize,
    pub macro_permutation_95th_percentile: Option<f64>,
    pub macro_permutation_p_value: Option<f64>,
    pub macro_above_permutation_95th_percentile: bool,
    pub significant_families: BTreeSet<Theme>,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
pub struct ExposureLabelSetReport {
    pub label_set: String,
    pub primary: ExposureHalfLifeReport,
    pub sensitivities: BTreeMap<u32, ExposureHalfLifeReport>,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
pub struct ExposureReplayReport {
    pub note_count: usize,
    pub typical_pair_cosine: f64,
    pub minimum_family_notes: usize,
    pub primary_half_life: u32,
    pub sensitivity_half_lives: [u32; 2],
    pub permutations: usize,
    pub permutation_seed: String,
    pub exposure_traces: BTreeMap<u32, Vec<ExposureTracePoint>>,
    pub label_sets: Vec<ExposureLabelSetReport>,
    pub common_primary_significant_families: BTreeSet<Theme>,
    pub decision: ExposureReplayDecision,
}

impl ExposureReplayReport {
    pub fn decision(&self) -> ExposureReplayDecision {
        self.decision
    }

    pub fn typical_pair_cosine(&self) -> f64 {
        self.typical_pair_cosine
    }

    pub fn exposure_trace(&self, half_life: u32) -> Option<&[ExposureTracePoint]> {
        self.exposure_traces.get(&half_life).map(Vec::as_slice)
    }

    pub fn common_primary_significant_families(&self) -> &BTreeSet<Theme> {
        &self.common_primary_significant_families
    }
}

pub fn analyze_exposure_replay(
    notes: &[ThemeNote],
    label_sets: &[ThemeLabelSet],
    settings: &ExposureReplaySettings,
) -> Result<ExposureReplayReport> {
    validate_inputs(notes, label_sets)?;
    let cosines = cosine_matrix(notes)?;
    let typical_pair_cosine = median_pair_cosine(&cosines, notes.len())?;
    let identity = (0..notes.len()).collect::<Vec<_>>();
    let mut exposure_by_half_life = BTreeMap::new();
    for half_life in [
        settings.primary_half_life,
        settings.sensitivity_half_lives[0],
        settings.sensitivity_half_lives[1],
    ] {
        exposure_by_half_life.insert(
            half_life,
            vector_exposure(
                &cosines,
                notes.len(),
                typical_pair_cosine,
                half_life,
                &identity,
            )?,
        );
    }

    let ordered_labels = label_sets
        .iter()
        .map(|label_set| labels_in_note_order(notes, label_set))
        .collect::<Result<Vec<_>>>()?;
    let qualifying = ordered_labels
        .iter()
        .map(|labels| qualifying_families(labels, settings.minimum_family_notes))
        .collect::<Vec<_>>();
    let primary_exposure = exposure_by_half_life
        .get(&settings.primary_half_life)
        .expect("primary exposure was calculated");
    let observed_primary = ordered_labels
        .iter()
        .zip(&qualifying)
        .map(|(labels, families)| {
            observed_correlations(
                primary_exposure,
                labels,
                families,
                settings.primary_half_life,
            )
        })
        .collect::<Result<Vec<_>>>()?;

    let mut family_nulls = qualifying
        .iter()
        .map(|families| {
            families
                .iter()
                .copied()
                .map(|family| (family, Vec::with_capacity(settings.permutations)))
                .collect::<BTreeMap<_, _>>()
        })
        .collect::<Vec<_>>();
    let mut macro_nulls = label_sets
        .iter()
        .map(|_| Vec::with_capacity(settings.permutations))
        .collect::<Vec<_>>();
    let mut permutation = identity.clone();
    let mut rng = SplitMix64::new(permutation_seed(&settings.permutation_seed));
    for _ in 0..settings.permutations {
        permutation.copy_from_slice(&identity);
        shuffle(&mut permutation, &mut rng);
        let permuted_exposure = vector_exposure(
            &cosines,
            notes.len(),
            typical_pair_cosine,
            settings.primary_half_life,
            &permutation,
        )?;
        for label_index in 0..label_sets.len() {
            let metrics = observed_correlations(
                &permuted_exposure,
                &ordered_labels[label_index],
                &qualifying[label_index],
                settings.primary_half_life,
            )?;
            for family in &qualifying[label_index] {
                if let Some(value) = metrics.get(family).and_then(|metric| metric.spearman) {
                    family_nulls[label_index]
                        .get_mut(family)
                        .expect("qualifying family has null storage")
                        .push(value);
                }
            }
            if let Some(value) = macro_correlation(&metrics) {
                macro_nulls[label_index].push(value);
            }
        }
    }

    let mut reports = Vec::with_capacity(label_sets.len());
    for label_index in 0..label_sets.len() {
        let primary = finalize_primary_report(
            settings.primary_half_life,
            observed_primary[label_index].clone(),
            &mut family_nulls[label_index],
            &mut macro_nulls[label_index],
            settings.permutations,
        );
        let sensitivities = settings
            .sensitivity_half_lives
            .iter()
            .copied()
            .map(|half_life| {
                let exposure = exposure_by_half_life
                    .get(&half_life)
                    .expect("sensitivity exposure was calculated");
                analyze_observed_half_life(
                    exposure,
                    &ordered_labels[label_index],
                    &qualifying[label_index],
                    half_life,
                )
                .map(|report| (half_life, report))
            })
            .collect::<Result<BTreeMap<_, _>>>()?;
        reports.push(ExposureLabelSetReport {
            label_set: label_sets[label_index].name().to_owned(),
            primary,
            sensitivities,
        });
    }

    let common_primary_significant_families = reports
        .iter()
        .map(|report| report.primary.significant_families.clone())
        .reduce(|left, right| left.intersection(&right).copied().collect())
        .unwrap_or_default();
    let primary_macro_pass = reports
        .iter()
        .all(|report| report.primary.macro_above_permutation_95th_percentile);
    let sensitivity_pass = settings.sensitivity_half_lives.iter().all(|half_life| {
        reports.iter().all(|report| {
            let Some(sensitivity) = report.sensitivities.get(half_life) else {
                return false;
            };
            sensitivity
                .macro_spearman
                .is_some_and(|correlation| correlation > 0.0)
                && common_primary_significant_families.iter().all(|family| {
                    sensitivity
                        .family_metrics
                        .get(family)
                        .and_then(|metric| metric.spearman)
                        .is_some_and(|correlation| correlation > 0.0)
                })
        })
    });
    let decision =
        if primary_macro_pass && common_primary_significant_families.len() >= 2 && sensitivity_pass
        {
            ExposureReplayDecision::ProceedToLiveProbe
        } else if reports.iter().all(|report| {
            report.primary.macro_spearman.is_some()
                && report.primary.macro_permutation_95th_percentile.is_some()
                && !report.primary.macro_above_permutation_95th_percentile
        }) {
            ExposureReplayDecision::StopCurrentFormula
        } else {
            ExposureReplayDecision::Underdetermined
        };

    let exposure_traces = exposure_by_half_life
        .into_iter()
        .map(|(half_life, exposure)| {
            let trace = notes
                .iter()
                .zip(exposure)
                .enumerate()
                .map(|(index, (note, exposure))| ExposureTracePoint {
                    presentation_ordinal: u32::try_from(index + 1)
                        .expect("validated replay size fits u32"),
                    note_id: note.id().to_owned(),
                    exposure,
                })
                .collect();
            (half_life, trace)
        })
        .collect();

    Ok(ExposureReplayReport {
        note_count: notes.len(),
        typical_pair_cosine,
        minimum_family_notes: settings.minimum_family_notes,
        primary_half_life: settings.primary_half_life,
        sensitivity_half_lives: settings.sensitivity_half_lives,
        permutations: settings.permutations,
        permutation_seed: settings.permutation_seed.clone(),
        exposure_traces,
        label_sets: reports,
        common_primary_significant_families,
        decision,
    })
}

fn validate_inputs(notes: &[ThemeNote], label_sets: &[ThemeLabelSet]) -> Result<()> {
    if notes.len() < 2 {
        return Err(ExposureReplayError::TooFewNotes);
    }
    if label_sets.len() != 2 {
        return Err(ExposureReplayError::WrongLabelSetCount);
    }
    let dimension = notes[0].vector().len();
    let mut note_ids = BTreeSet::new();
    for note in notes {
        if !note_ids.insert(note.id().to_owned()) {
            return Err(ExposureReplayError::DuplicateNoteId(note.id().to_owned()));
        }
        if note.vector().len() != dimension {
            return Err(ExposureReplayError::DimensionMismatch {
                expected: dimension,
                actual: note.vector().len(),
            });
        }
    }
    for label_set in label_sets {
        if label_set.labels().keys().collect::<BTreeSet<_>>()
            != note_ids.iter().collect::<BTreeSet<_>>()
        {
            return Err(ExposureReplayError::LabelCoverage {
                label_set: label_set.name().to_owned(),
            });
        }
    }
    Ok(())
}

fn cosine_matrix(notes: &[ThemeNote]) -> Result<Vec<f64>> {
    let count = notes.len();
    let mut cosines = vec![0.0; count * count];
    for left in 0..count {
        cosines[left * count + left] = 1.0;
        for right in 0..left {
            let cosine = notes[left]
                .vector()
                .iter()
                .zip(notes[right].vector())
                .map(|(left, right)| f64::from(*left) * f64::from(*right))
                .sum::<f64>();
            if !cosine.is_finite() {
                return Err(ExposureReplayError::NonFiniteResult);
            }
            cosines[left * count + right] = cosine;
            cosines[right * count + left] = cosine;
        }
    }
    Ok(cosines)
}

fn median_pair_cosine(cosines: &[f64], count: usize) -> Result<f64> {
    let mut values = Vec::with_capacity(count.saturating_mul(count.saturating_sub(1)) / 2);
    for left in 0..count {
        for right in 0..left {
            values.push(cosines[left * count + right]);
        }
    }
    values.sort_unstable_by(f64::total_cmp);
    let middle = values.len() / 2;
    let median = if values.len() % 2 == 0 {
        (values[middle - 1] + values[middle]) / 2.0
    } else {
        values[middle]
    };
    if median.is_finite() {
        Ok(median)
    } else {
        Err(ExposureReplayError::NonFiniteResult)
    }
}

fn vector_exposure(
    cosines: &[f64],
    count: usize,
    baseline: f64,
    half_life: u32,
    vector_order: &[usize],
) -> Result<Vec<f64>> {
    let mut exposure = vec![0.0; count];
    let decay_by_age = (0..count)
        .map(|age| 2.0_f64.powf(-(age as f64) / f64::from(half_life)))
        .collect::<Vec<_>>();
    for current in 1..count {
        let current_vector = vector_order[current];
        for (prior, prior_vector) in vector_order.iter().copied().enumerate().take(current) {
            let age = current - prior;
            exposure[current] += decay_by_age[age]
                * (cosines[current_vector * count + prior_vector] - baseline).max(0.0);
        }
        if !exposure[current].is_finite() {
            return Err(ExposureReplayError::NonFiniteResult);
        }
    }
    Ok(exposure)
}

fn labels_in_note_order(
    notes: &[ThemeNote],
    label_set: &ThemeLabelSet,
) -> Result<Vec<BTreeSet<Theme>>> {
    notes
        .iter()
        .map(|note| {
            label_set.labels().get(note.id()).cloned().ok_or_else(|| {
                ExposureReplayError::LabelCoverage {
                    label_set: label_set.name().to_owned(),
                }
            })
        })
        .collect()
}

fn qualifying_families(labels: &[BTreeSet<Theme>], minimum_family_notes: usize) -> Vec<Theme> {
    EXPOSURE_FAMILIES
        .into_iter()
        .filter(|family| {
            labels
                .iter()
                .filter(|themes| themes.contains(family))
                .count()
                >= minimum_family_notes
        })
        .collect()
}

fn finalize_primary_report(
    half_life: u32,
    mut family_metrics: BTreeMap<Theme, ExposureCorrelationMetric>,
    family_nulls: &mut BTreeMap<Theme, Vec<f64>>,
    macro_null: &mut [f64],
    expected_permutations: usize,
) -> ExposureHalfLifeReport {
    let mut significant_families = BTreeSet::new();
    for (family, metric) in &mut family_metrics {
        let null = family_nulls
            .get_mut(family)
            .expect("qualifying family has null storage");
        metric.permutation_valid_draws = null.len();
        if null.len() == expected_permutations {
            let threshold = percentile_95(null);
            metric.permutation_95th_percentile = Some(threshold);
            if let Some(correlation) = metric.spearman {
                metric.permutation_p_value = Some(permutation_p_value(null, correlation));
                metric.above_permutation_95th_percentile = correlation > threshold;
                if metric.above_permutation_95th_percentile {
                    significant_families.insert(*family);
                }
            }
        }
    }
    let macro_spearman = macro_correlation(&family_metrics);
    let macro_permutation_valid_draws = macro_null.len();
    let macro_permutation_95th_percentile =
        (macro_null.len() == expected_permutations).then(|| percentile_95(macro_null));
    let macro_permutation_p_value = match (macro_spearman, macro_permutation_95th_percentile) {
        (Some(observed), Some(_)) => Some(permutation_p_value(macro_null, observed)),
        _ => None,
    };
    let macro_above_permutation_95th_percentile = matches!((macro_spearman, macro_permutation_95th_percentile),
            (Some(observed), Some(threshold)) if observed > threshold);

    ExposureHalfLifeReport {
        half_life,
        family_metrics,
        macro_spearman,
        macro_permutation_valid_draws,
        macro_permutation_95th_percentile,
        macro_permutation_p_value,
        macro_above_permutation_95th_percentile,
        significant_families,
    }
}

fn analyze_observed_half_life(
    vector_exposure: &[f64],
    labels: &[BTreeSet<Theme>],
    qualifying: &[Theme],
    half_life: u32,
) -> Result<ExposureHalfLifeReport> {
    let family_metrics = observed_correlations(vector_exposure, labels, qualifying, half_life)?;
    Ok(ExposureHalfLifeReport {
        half_life,
        macro_spearman: macro_correlation(&family_metrics),
        family_metrics,
        macro_permutation_valid_draws: 0,
        macro_permutation_95th_percentile: None,
        macro_permutation_p_value: None,
        macro_above_permutation_95th_percentile: false,
        significant_families: BTreeSet::new(),
    })
}

fn observed_correlations(
    vector_exposure: &[f64],
    labels: &[BTreeSet<Theme>],
    qualifying: &[Theme],
    half_life: u32,
) -> Result<BTreeMap<Theme, ExposureCorrelationMetric>> {
    let mut metrics = BTreeMap::new();
    for family in qualifying {
        let reference = labeled_exposure(labels, *family, half_life)?;
        let anchors = labels
            .iter()
            .enumerate()
            .filter(|(_, themes)| themes.contains(family))
            .map(|(index, _)| index)
            .collect::<Vec<_>>();
        let vector_values = anchors
            .iter()
            .map(|index| vector_exposure[*index])
            .collect::<Vec<_>>();
        let reference_values = anchors
            .iter()
            .map(|index| reference[*index])
            .collect::<Vec<_>>();
        metrics.insert(
            *family,
            ExposureCorrelationMetric {
                labeled_notes: anchors.len(),
                spearman: spearman(&vector_values, &reference_values)?,
                permutation_valid_draws: 0,
                permutation_95th_percentile: None,
                permutation_p_value: None,
                above_permutation_95th_percentile: false,
            },
        );
    }
    Ok(metrics)
}

fn labeled_exposure(labels: &[BTreeSet<Theme>], family: Theme, half_life: u32) -> Result<Vec<f64>> {
    let decay = 2.0_f64.powf(-1.0 / f64::from(half_life));
    let mut exposure = vec![0.0; labels.len()];
    for current in 1..labels.len() {
        let prior_contribution = if labels[current - 1].contains(&family) {
            1.0
        } else {
            0.0
        };
        exposure[current] = decay * (exposure[current - 1] + prior_contribution);
        if !exposure[current].is_finite() {
            return Err(ExposureReplayError::NonFiniteResult);
        }
    }
    Ok(exposure)
}

fn macro_correlation(metrics: &BTreeMap<Theme, ExposureCorrelationMetric>) -> Option<f64> {
    if metrics.len() != EXPOSURE_FAMILIES.len() {
        return None;
    }
    let values = EXPOSURE_FAMILIES
        .iter()
        .map(|family| metrics.get(family)?.spearman)
        .collect::<Option<Vec<_>>>()?;
    Some(mean(&values))
}

fn spearman(left: &[f64], right: &[f64]) -> Result<Option<f64>> {
    if left.len() != right.len() || left.len() < 2 {
        return Ok(None);
    }
    if left.iter().chain(right).any(|value| !value.is_finite()) {
        return Err(ExposureReplayError::NonFiniteResult);
    }
    let left_ranks = average_ranks(left);
    let right_ranks = average_ranks(right);
    let left_mean = mean(&left_ranks);
    let right_mean = mean(&right_ranks);
    let mut covariance = 0.0;
    let mut left_variance = 0.0;
    let mut right_variance = 0.0;
    for (left, right) in left_ranks.iter().zip(&right_ranks) {
        let left_delta = *left - left_mean;
        let right_delta = *right - right_mean;
        covariance += left_delta * right_delta;
        left_variance += left_delta * left_delta;
        right_variance += right_delta * right_delta;
    }
    if left_variance == 0.0 || right_variance == 0.0 {
        return Ok(None);
    }
    let correlation = covariance / (left_variance * right_variance).sqrt();
    if correlation.is_finite() {
        Ok(Some(correlation.clamp(-1.0, 1.0)))
    } else {
        Err(ExposureReplayError::NonFiniteResult)
    }
}

fn average_ranks(values: &[f64]) -> Vec<f64> {
    let mut indexed = values
        .iter()
        .copied()
        .enumerate()
        .map(|(index, value)| (canonical_zero(value), index))
        .collect::<Vec<_>>();
    indexed.sort_unstable_by(|left, right| {
        left.0
            .total_cmp(&right.0)
            .then_with(|| left.1.cmp(&right.1))
    });
    let mut ranks = vec![0.0; values.len()];
    let mut start = 0;
    while start < indexed.len() {
        let mut end = start + 1;
        while end < indexed.len()
            && indexed[start].0.total_cmp(&indexed[end].0) == std::cmp::Ordering::Equal
        {
            end += 1;
        }
        let midrank = (start + 1 + end) as f64 / 2.0;
        for (_, index) in &indexed[start..end] {
            ranks[*index] = midrank;
        }
        start = end;
    }
    ranks
}

fn canonical_zero(value: f64) -> f64 {
    if value == 0.0 { 0.0 } else { value }
}

fn mean(values: &[f64]) -> f64 {
    values.iter().sum::<f64>() / values.len() as f64
}

fn percentile_95(values: &mut [f64]) -> f64 {
    values.sort_unstable_by(f64::total_cmp);
    let rank = values
        .len()
        .saturating_mul(NULL_QUANTILE_NUMERATOR)
        .div_ceil(NULL_QUANTILE_DENOMINATOR)
        .saturating_sub(1);
    values[rank]
}

fn permutation_p_value(null: &[f64], observed: f64) -> f64 {
    let at_least_observed = null.iter().filter(|value| **value >= observed).count();
    (at_least_observed + 1) as f64 / (null.len() + 1) as f64
}

fn permutation_seed(seed: &str) -> u64 {
    let mut digest = Sha256::new();
    digest.update(b"oracle-mvp-theme-exposure-vector-permutation-v1\0");
    digest.update((seed.len() as u64).to_le_bytes());
    digest.update(seed.as_bytes());
    u64::from_le_bytes(digest.finalize()[..8].try_into().expect("SHA-256 prefix"))
}

fn shuffle(values: &mut [usize], rng: &mut SplitMix64) {
    for end in (1..values.len()).rev() {
        let chosen = (rng.next_u64() % (end as u64 + 1)) as usize;
        values.swap(end, chosen);
    }
}

struct SplitMix64 {
    state: u64,
}

impl SplitMix64 {
    fn new(state: u64) -> Self {
        Self { state }
    }

    fn next_u64(&mut self) -> u64 {
        self.state = self.state.wrapping_add(0x9e37_79b9_7f4a_7c15);
        let mut value = self.state;
        value = (value ^ (value >> 30)).wrapping_mul(0xbf58_476d_1ce4_e5b9);
        value = (value ^ (value >> 27)).wrapping_mul(0x94d0_49bb_1331_11eb);
        value ^ (value >> 31)
    }
}
