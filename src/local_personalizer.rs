//! Local scoring over frozen public candidate/document vectors.

use std::collections::BTreeMap;

use thiserror::Error;

pub type Result<T> = std::result::Result<T, LocalPersonalizerError>;

#[derive(Debug, Error, PartialEq)]
pub enum LocalPersonalizerError {
    #[error("vectors must contain at least one coordinate")]
    EmptyVector,
    #[error("vector dimension mismatch: expected {expected}, got {actual}")]
    DimensionMismatch { expected: usize, actual: usize },
    #[error("vector coordinate {index} is not finite")]
    NonFiniteCoordinate { index: usize },
    #[error("rated target must be finite and within [-1, 1]")]
    InvalidTarget,
    #[error("at least one rated vector is required")]
    EmptyEvidence,
    #[error("finite compact neighbor count must be greater than zero")]
    InvalidNeighborCount,
    #[error("compact maximum distance must be finite and greater than zero")]
    InvalidMaximumDistance,
    #[error("compact neutral weight must be finite and greater than zero")]
    InvalidNeutralWeight,
    #[error("RBF scale must be finite and greater than zero")]
    InvalidRbfScale,
    #[error("RBF regularization must be finite and greater than zero")]
    InvalidRbfRegularization,
    #[error("RBF kernel-ridge system was not positive definite")]
    NonPositiveDefiniteSystem,
    #[error("local scorer produced a non-finite value")]
    NonFiniteScore,
}

#[derive(Clone, Debug, PartialEq)]
pub struct RatedVector {
    vector: Vec<f32>,
    target: f64,
}

impl RatedVector {
    pub fn new(vector: Vec<f32>, target: f64) -> Result<Self> {
        validate_vector(&vector)?;
        if !target.is_finite() || !(-1.0..=1.0).contains(&target) {
            return Err(LocalPersonalizerError::InvalidTarget);
        }
        Ok(Self { vector, target })
    }

    pub fn vector(&self) -> &[f32] {
        &self.vector
    }

    pub fn target(&self) -> f64 {
        self.target
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum CompactNeighborCount {
    Finite(usize),
    Infinite,
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct CompactParameters {
    neighbor_count: CompactNeighborCount,
    maximum_distance: f64,
    neutral_weight: f64,
}

impl CompactParameters {
    pub fn new(
        neighbor_count: CompactNeighborCount,
        maximum_distance: f64,
        neutral_weight: f64,
    ) -> Result<Self> {
        if matches!(neighbor_count, CompactNeighborCount::Finite(0)) {
            return Err(LocalPersonalizerError::InvalidNeighborCount);
        }
        if !maximum_distance.is_finite() || maximum_distance <= 0.0 {
            return Err(LocalPersonalizerError::InvalidMaximumDistance);
        }
        if !neutral_weight.is_finite() || neutral_weight <= 0.0 {
            return Err(LocalPersonalizerError::InvalidNeutralWeight);
        }
        Ok(Self {
            neighbor_count,
            maximum_distance,
            neutral_weight,
        })
    }

    pub fn neighbor_count(self) -> CompactNeighborCount {
        self.neighbor_count
    }

    pub fn maximum_distance(self) -> f64 {
        self.maximum_distance
    }

    pub fn neutral_weight(self) -> f64 {
        self.neutral_weight
    }
}

pub struct CompactSupportScorer<'a> {
    evidence: &'a [RatedVector],
    parameters: CompactParameters,
    dimension: usize,
}

impl<'a> CompactSupportScorer<'a> {
    pub fn new(evidence: &'a [RatedVector], parameters: CompactParameters) -> Result<Self> {
        let dimension = validate_evidence(evidence)?;
        Ok(Self {
            evidence,
            parameters,
            dimension,
        })
    }

    pub fn parameters(&self) -> CompactParameters {
        self.parameters
    }

    pub fn score(&self, candidate: &[f32]) -> Result<f64> {
        Ok(self.score_parameters(candidate, &[self.parameters])?[0])
    }

    pub(crate) fn score_parameters(
        &self,
        candidate: &[f32],
        parameters: &[CompactParameters],
    ) -> Result<Vec<f64>> {
        validate_candidate(candidate, self.dimension)?;

        let mut distances = self
            .evidence
            .iter()
            .map(|rated| {
                (
                    squared_chord_distance_unchecked(candidate, rated.vector()),
                    rated.target(),
                )
            })
            .collect::<Vec<_>>();
        distances.sort_unstable_by(|left, right| left.0.total_cmp(&right.0));

        let mut support_by_geometry = BTreeMap::new();
        parameters
            .iter()
            .map(|parameters| {
                let neighbor_count =
                    effective_neighbor_count(parameters.neighbor_count, distances.len());
                let support = *support_by_geometry
                    .entry((neighbor_count, parameters.maximum_distance.to_bits()))
                    .or_insert_with(|| {
                        compact_weighted_support(
                            &distances,
                            neighbor_count,
                            parameters.maximum_distance,
                        )
                    });
                let score = support.0 / (parameters.neutral_weight + support.1);
                if !score.is_finite() {
                    return Err(LocalPersonalizerError::NonFiniteScore);
                }
                Ok(score)
            })
            .collect()
    }
}

fn effective_neighbor_count(neighbor_count: CompactNeighborCount, evidence_count: usize) -> usize {
    match neighbor_count {
        CompactNeighborCount::Finite(k) if evidence_count > k => k,
        CompactNeighborCount::Finite(_) | CompactNeighborCount::Infinite => usize::MAX,
    }
}

fn compact_weighted_support(
    distances: &[(f64, f64)],
    effective_neighbor_count: usize,
    maximum_distance: f64,
) -> (f64, f64) {
    let bandwidth = if effective_neighbor_count == usize::MAX {
        maximum_distance
    } else {
        maximum_distance.min(distances[effective_neighbor_count].0.sqrt())
    };

    let mut weighted_targets = 0.0;
    let mut total_weight = 0.0;
    for (distance_squared, target) in distances {
        let weight = if *distance_squared == 0.0 {
            1.0
        } else {
            let distance = distance_squared.sqrt();
            if distance < bandwidth {
                let ratio_cubed = (distance / bandwidth).powi(3);
                (1.0 - ratio_cubed).powi(3)
            } else {
                0.0
            }
        };
        weighted_targets += weight * target;
        total_weight += weight;
    }
    (weighted_targets, total_weight)
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct RbfKernelRidgeParameters {
    scale: f64,
    regularization: f64,
}

impl RbfKernelRidgeParameters {
    pub fn new(scale: f64, regularization: f64) -> Result<Self> {
        let kernel_denominator = 2.0 * scale * scale;
        if !scale.is_finite()
            || scale <= 0.0
            || !kernel_denominator.is_finite()
            || kernel_denominator <= 0.0
        {
            return Err(LocalPersonalizerError::InvalidRbfScale);
        }
        if !regularization.is_finite() || regularization <= 0.0 {
            return Err(LocalPersonalizerError::InvalidRbfRegularization);
        }
        Ok(Self {
            scale,
            regularization,
        })
    }

    pub fn scale(self) -> f64 {
        self.scale
    }

    pub fn regularization(self) -> f64 {
        self.regularization
    }
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct RbfKernelRidgeScore {
    pub raw: f64,
    pub deployed: f64,
}

pub struct RbfKernelRidgeScorer<'a> {
    evidence: &'a [RatedVector],
    parameters: RbfKernelRidgeParameters,
    coefficients: Vec<f64>,
    dimension: usize,
}

impl<'a> RbfKernelRidgeScorer<'a> {
    pub fn fit(evidence: &'a [RatedVector], parameters: RbfKernelRidgeParameters) -> Result<Self> {
        let dimension = validate_evidence(evidence)?;
        let count = evidence.len();
        let mut system = vec![0.0; count * count];
        let kernel_denominator = 2.0 * parameters.scale * parameters.scale;

        for row in 0..count {
            system[row * count + row] = 1.0 + parameters.regularization;
            for column in 0..row {
                let distance_squared = squared_chord_distance_unchecked(
                    evidence[row].vector(),
                    evidence[column].vector(),
                );
                let kernel = (-distance_squared / kernel_denominator).exp();
                system[row * count + column] = kernel;
                system[column * count + row] = kernel;
            }
        }

        let targets = evidence.iter().map(RatedVector::target).collect::<Vec<_>>();
        let coefficients = cholesky_solve(&system, &targets)?;
        Ok(Self {
            evidence,
            parameters,
            coefficients,
            dimension,
        })
    }

    pub fn parameters(&self) -> RbfKernelRidgeParameters {
        self.parameters
    }

    pub fn score(&self, candidate: &[f32]) -> Result<RbfKernelRidgeScore> {
        validate_candidate(candidate, self.dimension)?;
        let kernel_denominator = 2.0 * self.parameters.scale * self.parameters.scale;
        let raw = self
            .evidence
            .iter()
            .zip(&self.coefficients)
            .map(|(rated, coefficient)| {
                let distance_squared = squared_chord_distance_unchecked(candidate, rated.vector());
                (-distance_squared / kernel_denominator).exp() * coefficient
            })
            .sum::<f64>();
        if !raw.is_finite() {
            return Err(LocalPersonalizerError::NonFiniteScore);
        }
        Ok(RbfKernelRidgeScore {
            raw,
            deployed: raw.clamp(-1.0, 1.0),
        })
    }
}

pub fn squared_chord_distance(left: &[f32], right: &[f32]) -> Result<f64> {
    validate_vector(left)?;
    validate_vector(right)?;
    if left.len() != right.len() {
        return Err(LocalPersonalizerError::DimensionMismatch {
            expected: left.len(),
            actual: right.len(),
        });
    }
    Ok(squared_chord_distance_unchecked(left, right))
}

fn squared_chord_distance_unchecked(left: &[f32], right: &[f32]) -> f64 {
    left.iter()
        .zip(right)
        .map(|(left, right)| {
            let difference = f64::from(*left) - f64::from(*right);
            difference * difference
        })
        .sum()
}

pub(crate) fn validate_vector(vector: &[f32]) -> Result<()> {
    if vector.is_empty() {
        return Err(LocalPersonalizerError::EmptyVector);
    }
    if let Some(index) = vector.iter().position(|coordinate| !coordinate.is_finite()) {
        return Err(LocalPersonalizerError::NonFiniteCoordinate { index });
    }
    Ok(())
}

pub(crate) fn validate_evidence(evidence: &[RatedVector]) -> Result<usize> {
    let first = evidence
        .first()
        .ok_or(LocalPersonalizerError::EmptyEvidence)?;
    let dimension = first.vector().len();
    for rated in &evidence[1..] {
        if rated.vector().len() != dimension {
            return Err(LocalPersonalizerError::DimensionMismatch {
                expected: dimension,
                actual: rated.vector().len(),
            });
        }
    }
    Ok(dimension)
}

fn validate_candidate(candidate: &[f32], dimension: usize) -> Result<()> {
    validate_vector(candidate)?;
    if candidate.len() != dimension {
        return Err(LocalPersonalizerError::DimensionMismatch {
            expected: dimension,
            actual: candidate.len(),
        });
    }
    Ok(())
}

fn cholesky_solve(system: &[f64], targets: &[f64]) -> Result<Vec<f64>> {
    let count = targets.len();
    let mut lower = vec![0.0; count * count];
    for row in 0..count {
        for column in 0..=row {
            let prior = (0..column)
                .map(|index| lower[row * count + index] * lower[column * count + index])
                .sum::<f64>();
            let residual = system[row * count + column] - prior;
            if row == column {
                if !residual.is_finite() || residual <= 0.0 {
                    return Err(LocalPersonalizerError::NonPositiveDefiniteSystem);
                }
                lower[row * count + column] = residual.sqrt();
            } else {
                let value = residual / lower[column * count + column];
                if !value.is_finite() {
                    return Err(LocalPersonalizerError::NonPositiveDefiniteSystem);
                }
                lower[row * count + column] = value;
            }
        }
    }

    let mut forward = vec![0.0; count];
    for row in 0..count {
        let prior = (0..row)
            .map(|column| lower[row * count + column] * forward[column])
            .sum::<f64>();
        forward[row] = (targets[row] - prior) / lower[row * count + row];
    }

    let mut solution = vec![0.0; count];
    for row in (0..count).rev() {
        let prior = ((row + 1)..count)
            .map(|column| lower[column * count + row] * solution[column])
            .sum::<f64>();
        solution[row] = (forward[row] - prior) / lower[row * count + row];
        if !solution[row].is_finite() {
            return Err(LocalPersonalizerError::NonPositiveDefiniteSystem);
        }
    }
    Ok(solution)
}
