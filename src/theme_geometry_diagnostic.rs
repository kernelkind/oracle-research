//! Blind diagnostic for broad-theme structure in stored Oracle document vectors.

use std::cmp::Ordering;
use std::collections::{BTreeMap, BTreeSet};

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use thiserror::Error;

const UNIT_NORM_TOLERANCE: f64 = 1.0e-5;
const NULL_QUANTILE_NUMERATOR: usize = 95;
const NULL_QUANTILE_DENOMINATOR: usize = 100;

pub type Result<T> = std::result::Result<T, ThemeGeometryError>;

#[derive(Debug, Error, PartialEq)]
pub enum ThemeGeometryError {
    #[error("theme note ID must be nonempty")]
    EmptyNoteId,
    #[error("theme note vector must be nonempty")]
    EmptyVector,
    #[error("theme note vector coordinate {index} is not finite")]
    NonFiniteCoordinate { index: usize },
    #[error("theme note vector is not unit normalized")]
    NonUnitVector,
    #[error("label-set name must be nonempty")]
    EmptyLabelSetName,
    #[error("theme labels must be nonempty")]
    EmptyThemes,
    #[error("other cannot be combined with a named theme")]
    OtherWithNamedTheme,
    #[error("minimum qualifying-theme notes must be at least two")]
    InvalidMinimumThemeNotes,
    #[error("permutation count must be positive")]
    InvalidPermutationCount,
    #[error("permutation seed must be nonempty")]
    EmptyPermutationSeed,
    #[error("the diagnostic requires at least two notes")]
    TooFewNotes,
    #[error("the diagnostic requires exactly two independent label sets")]
    WrongLabelSetCount,
    #[error("duplicate theme note ID `{0}`")]
    DuplicateNoteId(String),
    #[error("vector dimension mismatch: expected {expected}, got {actual}")]
    DimensionMismatch { expected: usize, actual: usize },
    #[error("label set `{label_set}` does not exactly cover the note IDs")]
    LabelCoverage { label_set: String },
    #[error("theme geometry produced a non-finite value")]
    NonFiniteResult,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum Theme {
    Nostr,
    Bitcoin,
    Monero,
    Cryptocurrency,
    LlmAi,
    AlcoholRecovery,
    Other,
}

impl Theme {
    const ANALYZED: [Self; 4] = [
        Self::Nostr,
        Self::Cryptocurrency,
        Self::LlmAi,
        Self::AlcoholRecovery,
    ];
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub struct DistinctThemePair {
    pub first: Theme,
    pub second: Theme,
}

#[derive(Clone, Debug, PartialEq)]
pub struct ThemeNote {
    id: String,
    vector: Vec<f32>,
}

impl ThemeNote {
    pub fn new(id: String, vector: Vec<f32>) -> Result<Self> {
        if id.is_empty() {
            return Err(ThemeGeometryError::EmptyNoteId);
        }
        if vector.is_empty() {
            return Err(ThemeGeometryError::EmptyVector);
        }
        let mut norm_squared = 0.0_f64;
        for (index, coordinate) in vector.iter().copied().enumerate() {
            if !coordinate.is_finite() {
                return Err(ThemeGeometryError::NonFiniteCoordinate { index });
            }
            norm_squared += f64::from(coordinate) * f64::from(coordinate);
        }
        if (norm_squared - 1.0).abs() > UNIT_NORM_TOLERANCE {
            return Err(ThemeGeometryError::NonUnitVector);
        }
        Ok(Self { id, vector })
    }

    pub fn id(&self) -> &str {
        &self.id
    }

    pub fn vector(&self) -> &[f32] {
        &self.vector
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct ThemeLabelSet {
    name: String,
    labels: BTreeMap<String, BTreeSet<Theme>>,
}

impl ThemeLabelSet {
    pub fn new(name: impl Into<String>, labels: BTreeMap<String, BTreeSet<Theme>>) -> Result<Self> {
        let name = name.into();
        if name.is_empty() {
            return Err(ThemeGeometryError::EmptyLabelSetName);
        }
        for themes in labels.values() {
            validate_themes(themes)?;
        }
        Ok(Self { name, labels })
    }

    pub fn name(&self) -> &str {
        &self.name
    }

    pub fn labels(&self) -> &BTreeMap<String, BTreeSet<Theme>> {
        &self.labels
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct GeometryAnalysisSettings {
    minimum_theme_notes: usize,
    permutations: usize,
    permutation_seed: String,
}

impl GeometryAnalysisSettings {
    pub fn new(
        minimum_theme_notes: usize,
        permutations: usize,
        permutation_seed: impl Into<String>,
    ) -> Result<Self> {
        if minimum_theme_notes < 2 {
            return Err(ThemeGeometryError::InvalidMinimumThemeNotes);
        }
        if permutations == 0 {
            return Err(ThemeGeometryError::InvalidPermutationCount);
        }
        let permutation_seed = permutation_seed.into();
        if permutation_seed.is_empty() {
            return Err(ThemeGeometryError::EmptyPermutationSeed);
        }
        Ok(Self {
            minimum_theme_notes,
            permutations,
            permutation_seed,
        })
    }

    pub fn minimum_theme_notes(&self) -> usize {
        self.minimum_theme_notes
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
pub enum DiagnosticDecision {
    ProceedToExposureReplay,
    StopCurrentVectorExposure,
    Underdetermined,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
pub struct ThemeMetric {
    pub labeled_notes: usize,
    pub mean_anchor_auroc: f64,
    pub permutation_95th_percentile: f64,
    pub permutation_p_value: f64,
    pub above_permutation_95th_percentile: bool,
    pub nearest_1_same_theme_rate: f64,
    pub nearest_5_same_theme_rate: f64,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
pub struct LabelSetGeometryReport {
    pub label_set: String,
    pub qualifying_themes: BTreeMap<Theme, ThemeMetric>,
    pub distinct_qualifying_pairs: BTreeSet<DistinctThemePair>,
    pub distinct_significant_pairs: BTreeSet<DistinctThemePair>,
    pub macro_auroc: Option<f64>,
    pub macro_permutation_95th_percentile: Option<f64>,
    pub macro_permutation_p_value: Option<f64>,
    pub macro_above_permutation_95th_percentile: bool,
    pub significant_themes: BTreeSet<Theme>,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
pub struct ThemeGeometryReport {
    pub note_count: usize,
    pub minimum_theme_notes: usize,
    pub permutations: usize,
    pub permutation_seed: String,
    pub label_sets: Vec<LabelSetGeometryReport>,
    pub common_qualifying_themes: BTreeSet<Theme>,
    pub common_significant_themes: BTreeSet<Theme>,
    pub common_distinct_qualifying_pairs: BTreeSet<DistinctThemePair>,
    pub common_distinct_significant_pairs: BTreeSet<DistinctThemePair>,
    pub decision: DiagnosticDecision,
}

impl ThemeGeometryReport {
    pub fn decision(&self) -> DiagnosticDecision {
        self.decision
    }

    pub fn common_significant_themes(&self) -> &BTreeSet<Theme> {
        &self.common_significant_themes
    }
}

pub fn analyze_geometry(
    notes: &[ThemeNote],
    label_sets: &[ThemeLabelSet],
    settings: &GeometryAnalysisSettings,
) -> Result<ThemeGeometryReport> {
    if notes.len() < 2 {
        return Err(ThemeGeometryError::TooFewNotes);
    }
    if label_sets.len() != 2 {
        return Err(ThemeGeometryError::WrongLabelSetCount);
    }
    let dimension = notes[0].vector.len();
    let mut note_ids = BTreeSet::new();
    for note in notes {
        if !note_ids.insert(note.id.clone()) {
            return Err(ThemeGeometryError::DuplicateNoteId(note.id.clone()));
        }
        if note.vector.len() != dimension {
            return Err(ThemeGeometryError::DimensionMismatch {
                expected: dimension,
                actual: note.vector.len(),
            });
        }
    }
    for label_set in label_sets {
        if label_set.labels.keys().collect::<BTreeSet<_>>()
            != note_ids.iter().collect::<BTreeSet<_>>()
        {
            return Err(ThemeGeometryError::LabelCoverage {
                label_set: label_set.name.clone(),
            });
        }
    }

    let cosines = cosine_matrix(notes)?;
    let ranks = rank_matrix(&cosines, notes.len());
    let nearest = nearest_order(&cosines, notes.len());
    let reports = label_sets
        .iter()
        .map(|label_set| analyze_label_set(notes, label_set, settings, &ranks, &nearest))
        .collect::<Result<Vec<_>>>()?;

    let common_qualifying_themes = reports
        .iter()
        .map(|report| {
            report
                .qualifying_themes
                .keys()
                .copied()
                .collect::<BTreeSet<_>>()
        })
        .reduce(|left, right| left.intersection(&right).copied().collect())
        .unwrap_or_default();
    let common_significant_themes = reports
        .iter()
        .map(|report| report.significant_themes.clone())
        .reduce(|left, right| left.intersection(&right).copied().collect())
        .unwrap_or_default();
    let common_distinct_qualifying_pairs = reports
        .iter()
        .map(|report| report.distinct_qualifying_pairs.clone())
        .reduce(|left, right| left.intersection(&right).copied().collect())
        .unwrap_or_default();
    let common_distinct_significant_pairs = reports
        .iter()
        .map(|report| report.distinct_significant_pairs.clone())
        .reduce(|left, right| left.intersection(&right).copied().collect())
        .unwrap_or_default();
    let macro_significance = reports
        .iter()
        .map(|report| report.macro_above_permutation_95th_percentile)
        .collect::<Vec<_>>();
    let decision = if common_distinct_qualifying_pairs.is_empty() {
        DiagnosticDecision::Underdetermined
    } else if macro_significance.iter().all(|value| *value)
        && !common_distinct_significant_pairs.is_empty()
    {
        DiagnosticDecision::ProceedToExposureReplay
    } else if reports.iter().all(|report| {
        report.macro_auroc.is_some() && !report.macro_above_permutation_95th_percentile
    }) {
        DiagnosticDecision::StopCurrentVectorExposure
    } else {
        DiagnosticDecision::Underdetermined
    };

    Ok(ThemeGeometryReport {
        note_count: notes.len(),
        minimum_theme_notes: settings.minimum_theme_notes,
        permutations: settings.permutations,
        permutation_seed: settings.permutation_seed.clone(),
        label_sets: reports,
        common_qualifying_themes,
        common_significant_themes,
        common_distinct_qualifying_pairs,
        common_distinct_significant_pairs,
        decision,
    })
}

fn validate_themes(themes: &BTreeSet<Theme>) -> Result<()> {
    if themes.is_empty() {
        return Err(ThemeGeometryError::EmptyThemes);
    }
    if themes.contains(&Theme::Other) && themes.len() != 1 {
        return Err(ThemeGeometryError::OtherWithNamedTheme);
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
                .vector
                .iter()
                .zip(&notes[right].vector)
                .map(|(left, right)| f64::from(*left) * f64::from(*right))
                .sum::<f64>();
            if !cosine.is_finite() {
                return Err(ThemeGeometryError::NonFiniteResult);
            }
            cosines[left * count + right] = cosine;
            cosines[right * count + left] = cosine;
        }
    }
    Ok(cosines)
}

fn rank_matrix(cosines: &[f64], count: usize) -> Vec<f64> {
    let mut ranks = vec![0.0; count * count];
    for anchor in 0..count {
        let mut scored = (0..count)
            .filter(|candidate| *candidate != anchor)
            .map(|candidate| (cosines[anchor * count + candidate], candidate))
            .collect::<Vec<_>>();
        scored.sort_unstable_by(|left, right| {
            left.0
                .total_cmp(&right.0)
                .then_with(|| left.1.cmp(&right.1))
        });
        let mut start = 0;
        while start < scored.len() {
            let mut end = start + 1;
            while end < scored.len() && scored[start].0.total_cmp(&scored[end].0) == Ordering::Equal
            {
                end += 1;
            }
            let midrank = ((start + 1 + end) as f64) / 2.0;
            for (_, candidate) in &scored[start..end] {
                ranks[anchor * count + *candidate] = midrank;
            }
            start = end;
        }
    }
    ranks
}

fn nearest_order(cosines: &[f64], count: usize) -> Vec<Vec<usize>> {
    (0..count)
        .map(|anchor| {
            let mut candidates = (0..count)
                .filter(|candidate| *candidate != anchor)
                .collect::<Vec<_>>();
            candidates.sort_unstable_by(|left, right| {
                cosines[anchor * count + *right]
                    .total_cmp(&cosines[anchor * count + *left])
                    .then_with(|| left.cmp(right))
            });
            candidates
        })
        .collect()
}

fn analyze_label_set(
    notes: &[ThemeNote],
    label_set: &ThemeLabelSet,
    settings: &GeometryAnalysisSettings,
    ranks: &[f64],
    nearest: &[Vec<usize>],
) -> Result<LabelSetGeometryReport> {
    let labels = notes
        .iter()
        .map(|note| {
            label_set.labels.get(&note.id).cloned().ok_or_else(|| {
                ThemeGeometryError::LabelCoverage {
                    label_set: label_set.name.clone(),
                }
            })
        })
        .collect::<Result<Vec<_>>>()?;
    let qualifying = Theme::ANALYZED
        .into_iter()
        .filter(|theme| {
            labels
                .iter()
                .filter(|themes| themes.contains(theme))
                .count()
                >= settings.minimum_theme_notes
        })
        .collect::<Vec<_>>();
    let distinct_qualifying_pairs =
        distinct_pairs(&labels, &qualifying, settings.minimum_theme_notes);
    let observed = qualifying
        .iter()
        .copied()
        .map(|theme| {
            let mask = theme_mask(&labels, theme);
            (
                theme,
                (
                    theme_auroc(ranks, notes.len(), &mask),
                    nearest_rates(nearest, &mask),
                ),
            )
        })
        .collect::<BTreeMap<_, _>>();

    let mut theme_nulls = qualifying
        .iter()
        .copied()
        .map(|theme| (theme, Vec::with_capacity(settings.permutations)))
        .collect::<BTreeMap<_, _>>();
    let mut macro_null = Vec::with_capacity(settings.permutations);
    let mut permutation = (0..notes.len()).collect::<Vec<_>>();
    let mut rng = SplitMix64::new(permutation_seed(
        &settings.permutation_seed,
        &label_set.name,
    ));
    for _ in 0..settings.permutations {
        for (index, slot) in permutation.iter_mut().enumerate() {
            *slot = index;
        }
        shuffle(&mut permutation, &mut rng);
        let mut values = Vec::with_capacity(qualifying.len());
        for theme in &qualifying {
            let mask = permutation
                .iter()
                .map(|index| labels[*index].contains(theme))
                .collect::<Vec<_>>();
            let value = theme_auroc(ranks, notes.len(), &mask);
            theme_nulls
                .get_mut(theme)
                .expect("qualifying theme has null storage")
                .push(value);
            values.push(value);
        }
        if !values.is_empty() {
            macro_null.push(mean(&values));
        }
    }

    let mut significant_themes = BTreeSet::new();
    let mut theme_reports = BTreeMap::new();
    for theme in qualifying {
        let (mean_anchor_auroc, (nearest_1, nearest_5)) = observed[&theme];
        let null = theme_nulls
            .get_mut(&theme)
            .expect("qualifying theme has null values");
        let threshold = percentile_95(null);
        let significant = mean_anchor_auroc > threshold;
        if significant {
            significant_themes.insert(theme);
        }
        theme_reports.insert(
            theme,
            ThemeMetric {
                labeled_notes: labels
                    .iter()
                    .filter(|themes| themes.contains(&theme))
                    .count(),
                mean_anchor_auroc,
                permutation_95th_percentile: threshold,
                permutation_p_value: permutation_p_value(null, mean_anchor_auroc),
                above_permutation_95th_percentile: significant,
                nearest_1_same_theme_rate: nearest_1,
                nearest_5_same_theme_rate: nearest_5,
            },
        );
    }
    let macro_auroc = if theme_reports.is_empty() {
        None
    } else {
        Some(mean(
            &theme_reports
                .values()
                .map(|metric| metric.mean_anchor_auroc)
                .collect::<Vec<_>>(),
        ))
    };
    let macro_permutation_95th_percentile = if macro_null.is_empty() {
        None
    } else {
        Some(percentile_95(&mut macro_null))
    };
    let macro_permutation_p_value =
        macro_auroc.map(|observed| permutation_p_value(&macro_null, observed));
    let macro_above_permutation_95th_percentile = matches!((macro_auroc, macro_permutation_95th_percentile),
            (Some(observed), Some(threshold)) if observed > threshold);
    let distinct_significant_pairs = distinct_qualifying_pairs
        .iter()
        .copied()
        .filter(|pair| {
            significant_themes.contains(&pair.first) && significant_themes.contains(&pair.second)
        })
        .collect();

    Ok(LabelSetGeometryReport {
        label_set: label_set.name.clone(),
        qualifying_themes: theme_reports,
        distinct_qualifying_pairs,
        distinct_significant_pairs,
        macro_auroc,
        macro_permutation_95th_percentile,
        macro_permutation_p_value,
        macro_above_permutation_95th_percentile,
        significant_themes,
    })
}

fn distinct_pairs(
    labels: &[BTreeSet<Theme>],
    qualifying: &[Theme],
    minimum_theme_notes: usize,
) -> BTreeSet<DistinctThemePair> {
    let mut pairs = BTreeSet::new();
    for (left_index, left) in qualifying.iter().copied().enumerate() {
        for right in qualifying.iter().copied().skip(left_index + 1) {
            let left_only = labels
                .iter()
                .filter(|themes| themes.contains(&left) && !themes.contains(&right))
                .count();
            let right_only = labels
                .iter()
                .filter(|themes| themes.contains(&right) && !themes.contains(&left))
                .count();
            if left_only >= minimum_theme_notes && right_only >= minimum_theme_notes {
                pairs.insert(DistinctThemePair {
                    first: left,
                    second: right,
                });
            }
        }
    }
    pairs
}

fn theme_mask(labels: &[BTreeSet<Theme>], theme: Theme) -> Vec<bool> {
    labels
        .iter()
        .map(|themes| themes.contains(&theme))
        .collect()
}

fn theme_auroc(ranks: &[f64], count: usize, mask: &[bool]) -> f64 {
    let positives = mask.iter().filter(|value| **value).count();
    let negatives = count - positives;
    if positives < 2 || negatives == 0 {
        return f64::NAN;
    }
    let positive_neighbors = positives - 1;
    let baseline = (positive_neighbors * (positive_neighbors + 1)) as f64 / 2.0;
    let denominator = (positive_neighbors * negatives) as f64;
    let mut values = Vec::with_capacity(positives);
    for anchor in 0..count {
        if !mask[anchor] {
            continue;
        }
        let rank_sum = (0..count)
            .filter(|candidate| *candidate != anchor && mask[*candidate])
            .map(|candidate| ranks[anchor * count + candidate])
            .sum::<f64>();
        values.push((rank_sum - baseline) / denominator);
    }
    mean(&values)
}

fn nearest_rates(nearest: &[Vec<usize>], mask: &[bool]) -> (f64, f64) {
    let mut anchors = 0_usize;
    let mut nearest_one = 0_usize;
    let mut nearest_five = 0_usize;
    let mut nearest_five_slots = 0_usize;
    for anchor in 0..mask.len() {
        if !mask[anchor] {
            continue;
        }
        anchors += 1;
        if nearest[anchor].first().is_some_and(|index| mask[*index]) {
            nearest_one += 1;
        }
        for index in nearest[anchor].iter().take(5) {
            nearest_five_slots += 1;
            nearest_five += usize::from(mask[*index]);
        }
    }
    (
        nearest_one as f64 / anchors as f64,
        nearest_five as f64 / nearest_five_slots as f64,
    )
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

fn permutation_seed(seed: &str, label_set: &str) -> u64 {
    let mut digest = Sha256::new();
    digest.update(b"oracle-mvp-theme-geometry-permutation-v1\0");
    digest.update((seed.len() as u64).to_le_bytes());
    digest.update(seed.as_bytes());
    digest.update((label_set.len() as u64).to_le_bytes());
    digest.update(label_set.as_bytes());
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
