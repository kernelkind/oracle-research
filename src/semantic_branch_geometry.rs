//! Geometry diagnostic for semantic directions around one hidden retrieval query.

use std::cmp::Ordering;
use std::collections::{BTreeMap, BTreeSet};

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use thiserror::Error;

const UNIT_NORM_TOLERANCE: f64 = 1.0e-4;
const TANGENT_COSINE_TOLERANCE: f64 = 1.0e-5;
const NULL_QUANTILE_NUMERATOR: usize = 95;
const NULL_QUANTILE_DENOMINATOR: usize = 100;
const RANK_QUARTILES: std::ops::RangeInclusive<u8> = 0..=3;

pub type Result<T> = std::result::Result<T, BranchGeometryError>;

#[derive(Debug, Error, PartialEq)]
pub enum BranchGeometryError {
    #[error("semantic-branch candidate ID must be nonempty")]
    EmptyCandidateId,
    #[error("semantic-branch candidate rank must be positive")]
    InvalidRank,
    #[error("semantic-branch candidate rank quartile must be between zero and three")]
    InvalidRankQuartile,
    #[error("semantic-branch candidate vector must be nonempty")]
    EmptyVector,
    #[error("semantic-branch candidate vector coordinate {index} is not finite")]
    NonFiniteCoordinate { index: usize },
    #[error("semantic-branch candidate vector is not unit normalized")]
    NonUnitVector,
    #[error("semantic-branch cached cosine must be finite and between negative one and one")]
    CachedCosineOutOfRange,
    #[error("semantic-branch cached cosine leaves no tangent direction")]
    DegenerateTangentDirection,
    #[error("semantic-branch label-set name must be nonempty")]
    EmptyLabelSetName,
    #[error("minimum exclusive-theme notes must be at least two")]
    InvalidMinimumExclusiveNotes,
    #[error("permutation count must be positive")]
    InvalidPermutationCount,
    #[error("permutation seed must be nonempty")]
    EmptyPermutationSeed,
    #[error("semantic-branch analysis requires at least two candidates")]
    TooFewCandidates,
    #[error("semantic-branch analysis requires exactly two independent label sets")]
    WrongLabelSetCount,
    #[error("semantic-branch label-set names must be distinct")]
    DuplicateLabelSetName,
    #[error("duplicate semantic-branch candidate ID `{0}`")]
    DuplicateCandidateId(String),
    #[error("duplicate semantic-branch candidate rank {0}")]
    DuplicateRank(u32),
    #[error("candidate vector dimension mismatch: expected {expected}, got {actual}")]
    DimensionMismatch { expected: usize, actual: usize },
    #[error("cached cosine increases as retrieval rank worsens")]
    CachedCosineRankOrder,
    #[error("label set `{label_set}` does not exactly cover the candidate IDs")]
    LabelCoverage { label_set: String },
    #[error("semantic-branch geometry produced an invalid tangent cosine")]
    InvalidTangentCosine,
    #[error("semantic-branch geometry produced a non-finite result")]
    NonFiniteResult,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum Theme {
    Physical,
    Mental,
    Spiritual,
}

impl Theme {
    const ALL: [Self; 3] = [Self::Physical, Self::Mental, Self::Spiritual];
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum BranchLabel {
    Themes { themes: BTreeSet<Theme> },
    Unusable,
}

impl BranchLabel {
    pub fn themes(themes: impl IntoIterator<Item = Theme>) -> Self {
        Self::Themes {
            themes: themes.into_iter().collect(),
        }
    }

    fn exclusive_theme(&self) -> Option<Theme> {
        match self {
            Self::Themes { themes } if themes.len() == 1 => themes.iter().next().copied(),
            Self::Themes { .. } | Self::Unusable => None,
        }
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct SemanticBranchCandidate {
    id: String,
    rank: u32,
    rank_quartile: u8,
    cached_cosine: f64,
    vector: Vec<f32>,
}

impl SemanticBranchCandidate {
    pub fn new(
        id: String,
        rank: u32,
        rank_quartile: u8,
        cached_cosine: f64,
        vector: Vec<f32>,
    ) -> Result<Self> {
        if id.is_empty() {
            return Err(BranchGeometryError::EmptyCandidateId);
        }
        if rank == 0 {
            return Err(BranchGeometryError::InvalidRank);
        }
        if !RANK_QUARTILES.contains(&rank_quartile) {
            return Err(BranchGeometryError::InvalidRankQuartile);
        }
        if vector.is_empty() {
            return Err(BranchGeometryError::EmptyVector);
        }
        let mut norm_squared = 0.0_f64;
        for (index, coordinate) in vector.iter().copied().enumerate() {
            if !coordinate.is_finite() {
                return Err(BranchGeometryError::NonFiniteCoordinate { index });
            }
            norm_squared += f64::from(coordinate) * f64::from(coordinate);
        }
        if (norm_squared.sqrt() - 1.0).abs() > UNIT_NORM_TOLERANCE {
            return Err(BranchGeometryError::NonUnitVector);
        }
        if !cached_cosine.is_finite() || !(-1.0..=1.0).contains(&cached_cosine) {
            return Err(BranchGeometryError::CachedCosineOutOfRange);
        }
        if 1.0 - cached_cosine * cached_cosine <= 0.0 {
            return Err(BranchGeometryError::DegenerateTangentDirection);
        }
        Ok(Self {
            id,
            rank,
            rank_quartile,
            cached_cosine,
            vector,
        })
    }

    pub fn id(&self) -> &str {
        &self.id
    }

    pub fn rank(&self) -> u32 {
        self.rank
    }

    pub fn rank_quartile(&self) -> u8 {
        self.rank_quartile
    }

    pub fn cached_cosine(&self) -> f64 {
        self.cached_cosine
    }

    pub fn vector(&self) -> &[f32] {
        &self.vector
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct BranchLabelSet {
    name: String,
    labels: BTreeMap<String, BranchLabel>,
}

impl BranchLabelSet {
    pub fn new(name: impl Into<String>, labels: BTreeMap<String, BranchLabel>) -> Result<Self> {
        let name = name.into();
        if name.is_empty() {
            return Err(BranchGeometryError::EmptyLabelSetName);
        }
        Ok(Self { name, labels })
    }

    pub fn name(&self) -> &str {
        &self.name
    }

    pub fn labels(&self) -> &BTreeMap<String, BranchLabel> {
        &self.labels
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct BranchSettings {
    minimum_exclusive_notes: usize,
    permutations: usize,
    permutation_seed: String,
}

impl BranchSettings {
    pub fn new(
        minimum_exclusive_notes: usize,
        permutations: usize,
        permutation_seed: impl Into<String>,
    ) -> Result<Self> {
        if minimum_exclusive_notes < 2 {
            return Err(BranchGeometryError::InvalidMinimumExclusiveNotes);
        }
        if permutations == 0 {
            return Err(BranchGeometryError::InvalidPermutationCount);
        }
        let permutation_seed = permutation_seed.into();
        if permutation_seed.is_empty() {
            return Err(BranchGeometryError::EmptyPermutationSeed);
        }
        Ok(Self {
            minimum_exclusive_notes,
            permutations,
            permutation_seed,
        })
    }

    pub fn minimum_exclusive_notes(&self) -> usize {
        self.minimum_exclusive_notes
    }

    pub fn permutations(&self) -> usize {
        self.permutations
    }

    pub fn permutation_seed(&self) -> &str {
        &self.permutation_seed
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub struct ThemePair {
    pub first: Theme,
    pub second: Theme,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum SemanticBranchDecision {
    RecoverableBranches,
    NoRecoverableBranches,
    Underdetermined,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct BranchSupply {
    pub exclusive: BTreeMap<Theme, usize>,
    pub overlap: usize,
    pub neither: usize,
    pub unusable: usize,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
pub struct BranchThemeMetric {
    pub exclusive_notes: usize,
    pub mean_anchor_auroc: f64,
    pub permutation_95th_percentile: f64,
    pub permutation_p_value: f64,
    pub above_permutation_95th_percentile: bool,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
pub struct BranchPairMetric {
    pub pair: ThemePair,
    pub first_exclusive_notes: usize,
    pub second_exclusive_notes: usize,
    pub mean_anchor_auroc: f64,
    pub permutation_95th_percentile: f64,
    pub permutation_p_value: f64,
    pub above_permutation_95th_percentile: bool,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
pub struct BranchLabelSetReport {
    pub label_set: String,
    pub supply: BranchSupply,
    pub qualifying_themes: BTreeMap<Theme, BranchThemeMetric>,
    pub significant_themes: BTreeSet<Theme>,
    pub distinct_qualifying_pairs: BTreeSet<ThemePair>,
    pub distinct_significant_pairs: BTreeSet<ThemePair>,
    pub pair_metrics: Vec<BranchPairMetric>,
    pub macro_mean_anchor_auroc: Option<f64>,
    pub macro_permutation_95th_percentile: Option<f64>,
    pub macro_permutation_p_value: Option<f64>,
    pub macro_above_permutation_95th_percentile: bool,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
pub struct SemanticBranchReport {
    pub candidate_count: usize,
    pub minimum_exclusive_notes: usize,
    pub permutations: usize,
    pub permutation_seed: String,
    pub label_sets: Vec<BranchLabelSetReport>,
    pub common_qualifying_themes: BTreeSet<Theme>,
    pub common_significant_themes: BTreeSet<Theme>,
    pub common_distinct_qualifying_pairs: BTreeSet<ThemePair>,
    pub common_distinct_significant_pairs: BTreeSet<ThemePair>,
    pub decision: SemanticBranchDecision,
}

pub fn analyze_semantic_branches(
    candidates: &[SemanticBranchCandidate],
    label_sets: &[BranchLabelSet],
    settings: &BranchSettings,
) -> Result<SemanticBranchReport> {
    validate_inputs(candidates, label_sets)?;
    let tangent_cosines = tangent_cosine_matrix(candidates)?;
    let reports = label_sets
        .iter()
        .map(|label_set| {
            analyze_label_set(candidates, label_set, settings, tangent_cosines.as_slice())
        })
        .collect::<Result<Vec<_>>>()?;

    let common_qualifying_themes = common_set(reports.iter().map(|report| {
        report
            .qualifying_themes
            .keys()
            .copied()
            .collect::<BTreeSet<_>>()
    }));
    let common_significant_themes = common_set(
        reports
            .iter()
            .map(|report| report.significant_themes.clone()),
    );
    let common_distinct_qualifying_pairs = common_set(
        reports
            .iter()
            .map(|report| report.distinct_qualifying_pairs.clone()),
    );
    let common_distinct_significant_pairs = common_set(
        reports
            .iter()
            .map(|report| report.distinct_significant_pairs.clone()),
    );
    let decision = if common_distinct_qualifying_pairs.is_empty() {
        SemanticBranchDecision::Underdetermined
    } else if reports
        .iter()
        .all(|report| report.macro_above_permutation_95th_percentile)
        && !common_distinct_significant_pairs.is_empty()
    {
        SemanticBranchDecision::RecoverableBranches
    } else {
        SemanticBranchDecision::NoRecoverableBranches
    };

    Ok(SemanticBranchReport {
        candidate_count: candidates.len(),
        minimum_exclusive_notes: settings.minimum_exclusive_notes,
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

fn validate_inputs(
    candidates: &[SemanticBranchCandidate],
    label_sets: &[BranchLabelSet],
) -> Result<()> {
    if candidates.len() < 2 {
        return Err(BranchGeometryError::TooFewCandidates);
    }
    if label_sets.len() != 2 {
        return Err(BranchGeometryError::WrongLabelSetCount);
    }
    if label_sets[0].name == label_sets[1].name {
        return Err(BranchGeometryError::DuplicateLabelSetName);
    }

    let dimension = candidates[0].vector.len();
    let mut ids = BTreeSet::new();
    let mut ranks = BTreeSet::new();
    for candidate in candidates {
        if !ids.insert(candidate.id.clone()) {
            return Err(BranchGeometryError::DuplicateCandidateId(
                candidate.id.clone(),
            ));
        }
        if !ranks.insert(candidate.rank) {
            return Err(BranchGeometryError::DuplicateRank(candidate.rank));
        }
        if candidate.vector.len() != dimension {
            return Err(BranchGeometryError::DimensionMismatch {
                expected: dimension,
                actual: candidate.vector.len(),
            });
        }
    }
    let mut by_rank = candidates.iter().collect::<Vec<_>>();
    by_rank.sort_unstable_by_key(|candidate| candidate.rank);
    if by_rank
        .windows(2)
        .any(|pair| pair[1].cached_cosine > pair[0].cached_cosine)
    {
        return Err(BranchGeometryError::CachedCosineRankOrder);
    }
    for label_set in label_sets {
        if label_set.labels.keys().collect::<BTreeSet<_>>() != ids.iter().collect::<BTreeSet<_>>() {
            return Err(BranchGeometryError::LabelCoverage {
                label_set: label_set.name.clone(),
            });
        }
    }
    Ok(())
}

fn tangent_cosine_matrix(candidates: &[SemanticBranchCandidate]) -> Result<Vec<f64>> {
    let count = candidates.len();
    let mut cosines = vec![0.0; count * count];
    for left in 0..count {
        cosines[left * count + left] = 1.0;
        for right in 0..left {
            let document_cosine = candidates[left]
                .vector
                .iter()
                .zip(&candidates[right].vector)
                .map(|(left, right)| f64::from(*left) * f64::from(*right))
                .sum::<f64>();
            let left_radius =
                (1.0 - candidates[left].cached_cosine * candidates[left].cached_cosine).sqrt();
            let right_radius =
                (1.0 - candidates[right].cached_cosine * candidates[right].cached_cosine).sqrt();
            let cosine = (document_cosine
                - candidates[left].cached_cosine * candidates[right].cached_cosine)
                / (left_radius * right_radius);
            let cosine = normalize_tangent_cosine(cosine)?;
            cosines[left * count + right] = cosine;
            cosines[right * count + left] = cosine;
        }
    }
    Ok(cosines)
}

fn normalize_tangent_cosine(value: f64) -> Result<f64> {
    if !value.is_finite() {
        return Err(BranchGeometryError::NonFiniteResult);
    }
    if !(-1.0 - TANGENT_COSINE_TOLERANCE..=1.0 + TANGENT_COSINE_TOLERANCE).contains(&value) {
        return Err(BranchGeometryError::InvalidTangentCosine);
    }
    Ok(value.clamp(-1.0, 1.0))
}

fn analyze_label_set(
    candidates: &[SemanticBranchCandidate],
    label_set: &BranchLabelSet,
    settings: &BranchSettings,
    tangent_cosines: &[f64],
) -> Result<BranchLabelSetReport> {
    let labels = candidates
        .iter()
        .map(|candidate| {
            label_set
                .labels
                .get(&candidate.id)
                .ok_or_else(|| BranchGeometryError::LabelCoverage {
                    label_set: label_set.name.clone(),
                })
        })
        .collect::<Result<Vec<_>>>()?;
    let supply = supply_counts(&labels);
    let qualifying = Theme::ALL
        .into_iter()
        .filter(|theme| supply.exclusive[theme] >= settings.minimum_exclusive_notes)
        .collect::<BTreeSet<_>>();
    let exclusive = labels
        .iter()
        .map(|label| label.exclusive_theme())
        .collect::<Vec<_>>();
    let observed = theme_metrics(tangent_cosines, candidates.len(), &exclusive, &qualifying)?;

    let mut theme_nulls = qualifying
        .iter()
        .copied()
        .map(|theme| (theme, Vec::with_capacity(settings.permutations)))
        .collect::<BTreeMap<_, _>>();
    let mut macro_null = Vec::with_capacity(settings.permutations);
    let mut rng = SplitMix64::new(permutation_seed(
        &settings.permutation_seed,
        &label_set.name,
    ));
    for _ in 0..settings.permutations {
        let permuted = permute_exclusive_within_quartiles(candidates, &exclusive, &mut rng);
        let metrics = theme_metrics(tangent_cosines, candidates.len(), &permuted, &qualifying)?;
        for (theme, value) in &metrics {
            theme_nulls
                .get_mut(theme)
                .expect("qualifying theme has null storage")
                .push(*value);
        }
        if !metrics.is_empty() {
            macro_null.push(mean(metrics.values().copied()));
        }
    }

    let mut significant_themes = BTreeSet::new();
    let mut qualifying_themes = BTreeMap::new();
    for (theme, mean_anchor_auroc) in observed {
        let null = theme_nulls
            .get_mut(&theme)
            .expect("qualifying theme has null values");
        let threshold = percentile_95(null);
        let significant = mean_anchor_auroc > threshold;
        if significant {
            significant_themes.insert(theme);
        }
        qualifying_themes.insert(
            theme,
            BranchThemeMetric {
                exclusive_notes: supply.exclusive[&theme],
                mean_anchor_auroc,
                permutation_95th_percentile: threshold,
                permutation_p_value: permutation_p_value(null, mean_anchor_auroc),
                above_permutation_95th_percentile: significant,
            },
        );
    }
    let macro_mean_anchor_auroc = if qualifying_themes.is_empty() {
        None
    } else {
        Some(mean(
            qualifying_themes
                .values()
                .map(|metric| metric.mean_anchor_auroc),
        ))
    };
    let macro_permutation_95th_percentile = if macro_null.is_empty() {
        None
    } else {
        Some(percentile_95(&mut macro_null))
    };
    let macro_permutation_p_value =
        macro_mean_anchor_auroc.map(|observed| permutation_p_value(&macro_null, observed));
    let macro_above_permutation_95th_percentile = matches!((macro_mean_anchor_auroc, macro_permutation_95th_percentile),
            (Some(observed), Some(threshold)) if observed > threshold);
    let distinct_qualifying_pairs = theme_pairs(&qualifying);
    let pair_metrics = pair_metrics(
        candidates,
        tangent_cosines,
        &exclusive,
        &distinct_qualifying_pairs,
        settings,
        &label_set.name,
    )?;
    let distinct_significant_pairs = pair_metrics
        .iter()
        .filter_map(|metric| {
            metric
                .above_permutation_95th_percentile
                .then_some(metric.pair)
        })
        .collect();

    Ok(BranchLabelSetReport {
        label_set: label_set.name.clone(),
        supply,
        qualifying_themes,
        significant_themes,
        distinct_qualifying_pairs,
        distinct_significant_pairs,
        pair_metrics,
        macro_mean_anchor_auroc,
        macro_permutation_95th_percentile,
        macro_permutation_p_value,
        macro_above_permutation_95th_percentile,
    })
}

fn supply_counts(labels: &[&BranchLabel]) -> BranchSupply {
    let mut exclusive = Theme::ALL
        .into_iter()
        .map(|theme| (theme, 0_usize))
        .collect::<BTreeMap<_, _>>();
    let mut overlap = 0;
    let mut neither = 0;
    let mut unusable = 0;
    for label in labels {
        match label {
            BranchLabel::Unusable => unusable += 1,
            BranchLabel::Themes { themes } if themes.is_empty() => neither += 1,
            BranchLabel::Themes { themes } if themes.len() == 1 => {
                *exclusive
                    .get_mut(themes.iter().next().expect("single theme"))
                    .expect("all semantic themes have counters") += 1;
            }
            BranchLabel::Themes { .. } => overlap += 1,
        }
    }
    BranchSupply {
        exclusive,
        overlap,
        neither,
        unusable,
    }
}

fn theme_metrics(
    tangent_cosines: &[f64],
    count: usize,
    exclusive: &[Option<Theme>],
    qualifying: &BTreeSet<Theme>,
) -> Result<BTreeMap<Theme, f64>> {
    qualifying
        .iter()
        .copied()
        .map(|theme| {
            mean_anchor_auroc(tangent_cosines, count, exclusive, theme).map(|auroc| (theme, auroc))
        })
        .collect()
}

fn pair_metrics(
    candidates: &[SemanticBranchCandidate],
    tangent_cosines: &[f64],
    exclusive: &[Option<Theme>],
    qualifying_pairs: &BTreeSet<ThemePair>,
    settings: &BranchSettings,
    label_set: &str,
) -> Result<Vec<BranchPairMetric>> {
    qualifying_pairs
        .iter()
        .copied()
        .map(|pair| {
            let pair_exclusive = exclusive
                .iter()
                .copied()
                .map(|theme| theme.filter(|theme| *theme == pair.first || *theme == pair.second))
                .collect::<Vec<_>>();
            let observed = pairwise_mean_anchor_auroc(
                tangent_cosines,
                candidates.len(),
                &pair_exclusive,
                pair,
            )?;
            let mut null = Vec::with_capacity(settings.permutations);
            let mut rng = SplitMix64::new(pair_permutation_seed(
                &settings.permutation_seed,
                label_set,
                pair,
            ));
            for _ in 0..settings.permutations {
                let permuted =
                    permute_exclusive_within_quartiles(candidates, &pair_exclusive, &mut rng);
                null.push(pairwise_mean_anchor_auroc(
                    tangent_cosines,
                    candidates.len(),
                    &permuted,
                    pair,
                )?);
            }
            let threshold = percentile_95(&mut null);
            Ok(BranchPairMetric {
                pair,
                first_exclusive_notes: pair_exclusive
                    .iter()
                    .filter(|theme| **theme == Some(pair.first))
                    .count(),
                second_exclusive_notes: pair_exclusive
                    .iter()
                    .filter(|theme| **theme == Some(pair.second))
                    .count(),
                mean_anchor_auroc: observed,
                permutation_95th_percentile: threshold,
                permutation_p_value: permutation_p_value(&null, observed),
                above_permutation_95th_percentile: observed > threshold,
            })
        })
        .collect()
}

fn pairwise_mean_anchor_auroc(
    tangent_cosines: &[f64],
    count: usize,
    pair_exclusive: &[Option<Theme>],
    pair: ThemePair,
) -> Result<f64> {
    Ok(mean([
        mean_anchor_auroc(tangent_cosines, count, pair_exclusive, pair.first)?,
        mean_anchor_auroc(tangent_cosines, count, pair_exclusive, pair.second)?,
    ]))
}

fn mean_anchor_auroc(
    tangent_cosines: &[f64],
    count: usize,
    exclusive: &[Option<Theme>],
    theme: Theme,
) -> Result<f64> {
    let anchors = exclusive
        .iter()
        .enumerate()
        .filter_map(|(index, value)| (*value == Some(theme)).then_some(index))
        .collect::<Vec<_>>();
    let negatives = exclusive
        .iter()
        .enumerate()
        .filter_map(|(index, value)| value.is_some_and(|value| value != theme).then_some(index))
        .collect::<Vec<_>>();
    let mut anchor_aurocs = Vec::with_capacity(anchors.len());
    for anchor in anchors.iter().copied() {
        let positives = anchors
            .iter()
            .copied()
            .filter(|candidate| *candidate != anchor)
            .collect::<Vec<_>>();
        if positives.is_empty() || negatives.is_empty() {
            return Err(BranchGeometryError::NonFiniteResult);
        }
        let mut wins = 0.0_f64;
        for positive in positives.iter().copied() {
            let positive_similarity = tangent_cosines[anchor * count + positive];
            for negative in negatives.iter().copied() {
                let negative_similarity = tangent_cosines[anchor * count + negative];
                wins += match positive_similarity.total_cmp(&negative_similarity) {
                    Ordering::Greater => 1.0,
                    Ordering::Equal => 0.5,
                    Ordering::Less => 0.0,
                };
            }
        }
        anchor_aurocs.push(wins / (positives.len() * negatives.len()) as f64);
    }
    let value = mean(anchor_aurocs);
    if !value.is_finite() {
        return Err(BranchGeometryError::NonFiniteResult);
    }
    Ok(value)
}

fn permute_exclusive_within_quartiles(
    candidates: &[SemanticBranchCandidate],
    exclusive: &[Option<Theme>],
    rng: &mut SplitMix64,
) -> Vec<Option<Theme>> {
    let mut permuted = exclusive.to_vec();
    for quartile in RANK_QUARTILES {
        let indices = candidates
            .iter()
            .enumerate()
            .filter_map(|(index, candidate)| {
                (candidate.rank_quartile == quartile && exclusive[index].is_some()).then_some(index)
            })
            .collect::<Vec<_>>();
        let mut themes = indices
            .iter()
            .map(|index| exclusive[*index].expect("exclusive index has a theme"))
            .collect::<Vec<_>>();
        shuffle(&mut themes, rng);
        for (index, theme) in indices.into_iter().zip(themes) {
            permuted[index] = Some(theme);
        }
    }
    permuted
}

fn theme_pairs(themes: &BTreeSet<Theme>) -> BTreeSet<ThemePair> {
    let themes = themes.iter().copied().collect::<Vec<_>>();
    let mut pairs = BTreeSet::new();
    for (left_index, first) in themes.iter().copied().enumerate() {
        for second in themes.iter().copied().skip(left_index + 1) {
            pairs.insert(ThemePair { first, second });
        }
    }
    pairs
}

fn common_set<T: Copy + Ord>(sets: impl Iterator<Item = BTreeSet<T>>) -> BTreeSet<T> {
    sets.reduce(|left, right| left.intersection(&right).copied().collect())
        .unwrap_or_default()
}

fn mean(values: impl IntoIterator<Item = f64>) -> f64 {
    let mut sum = 0.0_f64;
    let mut count = 0_usize;
    for value in values {
        sum += value;
        count += 1;
    }
    sum / count as f64
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
    digest.update(b"oracle-mvp-semantic-branch-permutation-v1\0");
    digest.update((seed.len() as u64).to_le_bytes());
    digest.update(seed.as_bytes());
    digest.update((label_set.len() as u64).to_le_bytes());
    digest.update(label_set.as_bytes());
    u64::from_le_bytes(digest.finalize()[..8].try_into().expect("SHA-256 prefix"))
}

fn pair_permutation_seed(seed: &str, label_set: &str, pair: ThemePair) -> u64 {
    let mut digest = Sha256::new();
    digest.update(b"oracle-mvp-semantic-branch-pair-permutation-v1\0");
    digest.update((seed.len() as u64).to_le_bytes());
    digest.update(seed.as_bytes());
    digest.update((label_set.len() as u64).to_le_bytes());
    digest.update(label_set.as_bytes());
    digest.update([theme_seed_byte(pair.first), theme_seed_byte(pair.second)]);
    u64::from_le_bytes(digest.finalize()[..8].try_into().expect("SHA-256 prefix"))
}

fn theme_seed_byte(theme: Theme) -> u8 {
    match theme {
        Theme::Physical => 0,
        Theme::Mental => 1,
        Theme::Spiritual => 2,
    }
}

fn shuffle<T>(values: &mut [T], rng: &mut SplitMix64) {
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
