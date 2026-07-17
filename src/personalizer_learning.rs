//! Forward-only learning over frozen local-personalizer predictions.

use std::cmp::Ordering;
use std::collections::{BTreeMap, BTreeSet};

use thiserror::Error;

use crate::artifact::hash_bytes;
use crate::local_personalizer::{
    CompactNeighborCount, CompactParameters, CompactSupportScorer, LocalPersonalizerError,
    RatedVector, RbfKernelRidgeParameters, RbfKernelRidgeScore, RbfKernelRidgeScorer,
    validate_evidence, validate_vector,
};
use crate::representation::EventId;

const EVIDENCE_IDENTITY_DOMAIN: &[u8] = b"oracle-mvp-personalizer-evidence-v1\0";
const COMPACT_NEIGHBOR_COUNTS: [CompactNeighborCount; 7] = [
    CompactNeighborCount::Finite(1),
    CompactNeighborCount::Finite(2),
    CompactNeighborCount::Finite(4),
    CompactNeighborCount::Finite(8),
    CompactNeighborCount::Finite(16),
    CompactNeighborCount::Finite(32),
    CompactNeighborCount::Infinite,
];
const COMPACT_NEUTRAL_WEIGHTS: [f64; 3] = [0.5, 1.0, 2.0];
const RBF_REGULARIZATIONS: [f64; 3] = [0.25, 1.0, 4.0];

pub type Result<T> = std::result::Result<T, PersonalizerLearningError>;

#[derive(Debug, Error, PartialEq)]
pub enum PersonalizerLearningError {
    #[error(transparent)]
    Scorer(#[from] LocalPersonalizerError),
    #[error("representation version must not be empty")]
    EmptyRepresentationVersion,
    #[error("representation version `{actual}` does not match `{expected}`")]
    RepresentationVersionMismatch { expected: String, actual: String },
    #[error("gladness rating must be within 1..=7; got {0}")]
    InvalidRating(u8),
    #[error("compact scales must be positive, finite, and ordered H16 <= H64 <= H256")]
    InvalidCompactScales,
    #[error("RBF scales must be positive, finite, and ordered S16 <= S64 <= S256")]
    InvalidRbfScales,
    #[error("the first compact scale must be H64 or H256")]
    InvalidInitialCompactScale,
    #[error("initial evidence repeats event {event_id:?}")]
    DuplicateEvidence { event_id: EventId },
    #[error("a learning batch must contain at least one candidate")]
    EmptyBatch,
    #[error("a learning batch repeats candidate {event_id:?}")]
    DuplicateCandidate { event_id: EventId },
    #[error("candidate {event_id:?} is already present in this personalizer's evidence")]
    CandidateAlreadyInEvidence { event_id: EventId },
    #[error("a learning batch is already frozen")]
    BatchAlreadyFrozen,
    #[error("there is no frozen learning batch to complete")]
    NoFrozenBatch,
    #[error("ratings repeat candidate {event_id:?}")]
    DuplicateRating { event_id: EventId },
    #[error("rating references event {event_id:?} outside the frozen batch")]
    UnexpectedRating { event_id: EventId },
    #[error("frozen candidate {event_id:?} has no rating")]
    MissingRating { event_id: EventId },
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct GladnessRating(u8);

impl GladnessRating {
    pub fn new(value: u8) -> Result<Self> {
        if !(1..=7).contains(&value) {
            return Err(PersonalizerLearningError::InvalidRating(value));
        }
        Ok(Self(value))
    }

    pub fn value(self) -> u8 {
        self.0
    }

    pub fn target(self) -> f64 {
        (f64::from(self.0) - 4.0) / 3.0
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct EvidenceNote {
    event_id: EventId,
    rating: GladnessRating,
    vector: RatedVector,
}

impl EvidenceNote {
    pub fn new(event_id: EventId, vector: Vec<f32>, rating: u8) -> Result<Self> {
        let rating = GladnessRating::new(rating)?;
        let vector = RatedVector::new(vector, rating.target())?;
        Ok(Self {
            event_id,
            rating,
            vector,
        })
    }

    pub fn event_id(&self) -> EventId {
        self.event_id
    }

    pub fn rating(&self) -> GladnessRating {
        self.rating
    }

    pub fn vector(&self) -> &[f32] {
        self.vector.vector()
    }

    pub fn target(&self) -> f64 {
        self.vector.target()
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct BatchCandidate {
    event_id: EventId,
    vector: Vec<f32>,
}

impl BatchCandidate {
    pub fn new(event_id: EventId, vector: Vec<f32>) -> Result<Self> {
        validate_vector(&vector)?;
        Ok(Self { event_id, vector })
    }

    pub fn event_id(&self) -> EventId {
        self.event_id
    }

    pub fn vector(&self) -> &[f32] {
        &self.vector
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct CandidateBatch {
    representation_version: String,
    candidates: Vec<BatchCandidate>,
}

impl CandidateBatch {
    pub fn new(
        representation_version: impl Into<String>,
        candidates: Vec<BatchCandidate>,
    ) -> Result<Self> {
        let representation_version = representation_version.into();
        validate_representation_version(&representation_version)?;
        if candidates.is_empty() {
            return Err(PersonalizerLearningError::EmptyBatch);
        }
        let mut event_ids = BTreeSet::new();
        let expected_dimension = candidates[0].vector.len();
        for candidate in &candidates {
            if !event_ids.insert(candidate.event_id) {
                return Err(PersonalizerLearningError::DuplicateCandidate {
                    event_id: candidate.event_id,
                });
            }
            if candidate.vector.len() != expected_dimension {
                return Err(LocalPersonalizerError::DimensionMismatch {
                    expected: expected_dimension,
                    actual: candidate.vector.len(),
                }
                .into());
            }
        }
        Ok(Self {
            representation_version,
            candidates,
        })
    }

    pub fn representation_version(&self) -> &str {
        &self.representation_version
    }

    pub fn candidates(&self) -> &[BatchCandidate] {
        &self.candidates
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct BatchRating {
    event_id: EventId,
    rating: GladnessRating,
}

impl BatchRating {
    pub fn new(event_id: EventId, rating: u8) -> Result<Self> {
        Ok(Self {
            event_id,
            rating: GladnessRating::new(rating)?,
        })
    }

    pub fn event_id(self) -> EventId {
        self.event_id
    }

    pub fn rating(self) -> GladnessRating {
        self.rating
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum ScaleLevel {
    Mass16,
    Mass64,
    Mass256,
}

impl ScaleLevel {
    const ALL: [Self; 3] = [Self::Mass16, Self::Mass64, Self::Mass256];

    fn index(self) -> usize {
        match self {
            Self::Mass16 => 0,
            Self::Mass64 => 1,
            Self::Mass256 => 2,
        }
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct CompactLearningSettings {
    representation_version: String,
    scales: [f64; 3],
    initial_scale: ScaleLevel,
}

impl CompactLearningSettings {
    pub fn new(
        representation_version: impl Into<String>,
        h16: f64,
        h64: f64,
        h256: f64,
        initial_scale: ScaleLevel,
    ) -> Result<Self> {
        let representation_version = representation_version.into();
        validate_representation_version(&representation_version)?;
        let scales = [h16, h64, h256];
        if !valid_scales(scales) {
            return Err(PersonalizerLearningError::InvalidCompactScales);
        }
        if !matches!(initial_scale, ScaleLevel::Mass64 | ScaleLevel::Mass256) {
            return Err(PersonalizerLearningError::InvalidInitialCompactScale);
        }
        Ok(Self {
            representation_version,
            scales,
            initial_scale,
        })
    }

    pub fn representation_version(&self) -> &str {
        &self.representation_version
    }

    pub fn scale(&self, level: ScaleLevel) -> f64 {
        self.scales[level.index()]
    }

    pub fn initial_scale(&self) -> ScaleLevel {
        self.initial_scale
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct RbfLearningSettings {
    representation_version: String,
    scales: [f64; 3],
}

impl RbfLearningSettings {
    pub fn new(
        representation_version: impl Into<String>,
        s16: f64,
        s64: f64,
        s256: f64,
    ) -> Result<Self> {
        let representation_version = representation_version.into();
        validate_representation_version(&representation_version)?;
        let scales = [s16, s64, s256];
        if !valid_rbf_scales(scales) {
            return Err(PersonalizerLearningError::InvalidRbfScales);
        }
        Ok(Self {
            representation_version,
            scales,
        })
    }

    pub fn representation_version(&self) -> &str {
        &self.representation_version
    }

    pub fn scale(&self, level: ScaleLevel) -> f64 {
        self.scales[level.index()]
    }
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct CompactTuple {
    scale_level: ScaleLevel,
    parameters: CompactParameters,
}

impl CompactTuple {
    pub fn scale_level(self) -> ScaleLevel {
        self.scale_level
    }

    pub fn neighbor_count(self) -> CompactNeighborCount {
        self.parameters.neighbor_count()
    }

    pub fn maximum_distance(self) -> f64 {
        self.parameters.maximum_distance()
    }

    pub fn neutral_weight(self) -> f64 {
        self.parameters.neutral_weight()
    }

    pub fn parameters(self) -> CompactParameters {
        self.parameters
    }
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct RbfTuple {
    scale_level: ScaleLevel,
    parameters: RbfKernelRidgeParameters,
}

impl RbfTuple {
    pub fn scale_level(self) -> ScaleLevel {
        self.scale_level
    }

    pub fn scale(self) -> f64 {
        self.parameters.scale()
    }

    pub fn regularization(self) -> f64 {
        self.parameters.regularization()
    }

    pub fn parameters(self) -> RbfKernelRidgeParameters {
        self.parameters
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct EvidenceIdentity {
    representation_version: String,
    event_count: usize,
    vector_dimensions: usize,
    sha256: String,
}

impl EvidenceIdentity {
    pub fn representation_version(&self) -> &str {
        &self.representation_version
    }

    pub fn event_count(&self) -> usize {
        self.event_count
    }

    pub fn vector_dimensions(&self) -> usize {
        self.vector_dimensions
    }

    pub fn sha256(&self) -> &str {
        &self.sha256
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct RatedOutcome {
    event_id: EventId,
    rating: GladnessRating,
    target: f64,
}

impl RatedOutcome {
    pub fn event_id(&self) -> EventId {
        self.event_id
    }

    pub fn rating(&self) -> GladnessRating {
        self.rating
    }

    pub fn target(&self) -> f64 {
        self.target
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct CompactTuplePredictions {
    parameter_tuple: CompactTuple,
    scores: Vec<f64>,
}

impl CompactTuplePredictions {
    pub fn parameter_tuple(&self) -> CompactTuple {
        self.parameter_tuple
    }

    pub fn scores(&self) -> &[f64] {
        &self.scores
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct RbfTuplePredictions {
    parameter_tuple: RbfTuple,
    scores: Vec<RbfKernelRidgeScore>,
}

impl RbfTuplePredictions {
    pub fn parameter_tuple(&self) -> RbfTuple {
        self.parameter_tuple
    }

    pub fn scores(&self) -> &[RbfKernelRidgeScore] {
        &self.scores
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct CompactFrozenBatch {
    round: usize,
    evidence_identity: EvidenceIdentity,
    active_tuple: CompactTuple,
    candidate_ids: Vec<EventId>,
    predictions: Vec<CompactTuplePredictions>,
}

impl CompactFrozenBatch {
    pub fn round(&self) -> usize {
        self.round
    }

    pub fn evidence_identity(&self) -> &EvidenceIdentity {
        &self.evidence_identity
    }

    pub fn active_tuple(&self) -> CompactTuple {
        self.active_tuple
    }

    pub fn candidate_ids(&self) -> &[EventId] {
        &self.candidate_ids
    }

    pub fn predictions(&self) -> &[CompactTuplePredictions] {
        &self.predictions
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct RbfFrozenBatch {
    round: usize,
    evidence_identity: EvidenceIdentity,
    active_tuple: RbfTuple,
    candidate_ids: Vec<EventId>,
    predictions: Vec<RbfTuplePredictions>,
}

impl RbfFrozenBatch {
    pub fn round(&self) -> usize {
        self.round
    }

    pub fn evidence_identity(&self) -> &EvidenceIdentity {
        &self.evidence_identity
    }

    pub fn active_tuple(&self) -> RbfTuple {
        self.active_tuple
    }

    pub fn candidate_ids(&self) -> &[EventId] {
        &self.candidate_ids
    }

    pub fn predictions(&self) -> &[RbfTuplePredictions] {
        &self.predictions
    }
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct CompactTupleError {
    parameter_tuple: CompactTuple,
    batch_mse: f64,
    cumulative_mse: f64,
}

impl CompactTupleError {
    pub fn parameter_tuple(self) -> CompactTuple {
        self.parameter_tuple
    }

    pub fn batch_mse(self) -> f64 {
        self.batch_mse
    }

    pub fn cumulative_mse(self) -> f64 {
        self.cumulative_mse
    }
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct RbfTupleError {
    parameter_tuple: RbfTuple,
    batch_mse: f64,
    cumulative_mse: f64,
}

impl RbfTupleError {
    pub fn parameter_tuple(self) -> RbfTuple {
        self.parameter_tuple
    }

    pub fn batch_mse(self) -> f64 {
        self.batch_mse
    }

    pub fn cumulative_mse(self) -> f64 {
        self.cumulative_mse
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct CompactRoundRecord {
    frozen_batch: CompactFrozenBatch,
    outcomes: Vec<RatedOutcome>,
    errors: Vec<CompactTupleError>,
    evidence_after: EvidenceIdentity,
    next_tuple: CompactTuple,
}

impl CompactRoundRecord {
    pub fn frozen_batch(&self) -> &CompactFrozenBatch {
        &self.frozen_batch
    }

    pub fn outcomes(&self) -> &[RatedOutcome] {
        &self.outcomes
    }

    pub fn errors(&self) -> &[CompactTupleError] {
        &self.errors
    }

    pub fn evidence_after(&self) -> &EvidenceIdentity {
        &self.evidence_after
    }

    pub fn next_tuple(&self) -> CompactTuple {
        self.next_tuple
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct RbfRoundRecord {
    frozen_batch: RbfFrozenBatch,
    outcomes: Vec<RatedOutcome>,
    errors: Vec<RbfTupleError>,
    evidence_after: EvidenceIdentity,
    next_tuple: RbfTuple,
}

impl RbfRoundRecord {
    pub fn frozen_batch(&self) -> &RbfFrozenBatch {
        &self.frozen_batch
    }

    pub fn outcomes(&self) -> &[RatedOutcome] {
        &self.outcomes
    }

    pub fn errors(&self) -> &[RbfTupleError] {
        &self.errors
    }

    pub fn evidence_after(&self) -> &EvidenceIdentity {
        &self.evidence_after
    }

    pub fn next_tuple(&self) -> RbfTuple {
        self.next_tuple
    }
}

struct EvidenceState {
    event_ids: Vec<EventId>,
    ratings: Vec<GladnessRating>,
    vectors: Vec<RatedVector>,
    identity: EvidenceIdentity,
}

impl EvidenceState {
    fn new(representation_version: &str, notes: Vec<EvidenceNote>) -> Result<Self> {
        if notes.is_empty() {
            return Err(LocalPersonalizerError::EmptyEvidence.into());
        }
        let mut seen = BTreeSet::new();
        let mut event_ids = Vec::with_capacity(notes.len());
        let mut ratings = Vec::with_capacity(notes.len());
        let mut vectors = Vec::with_capacity(notes.len());
        for note in notes {
            if !seen.insert(note.event_id) {
                return Err(PersonalizerLearningError::DuplicateEvidence {
                    event_id: note.event_id,
                });
            }
            event_ids.push(note.event_id);
            ratings.push(note.rating);
            vectors.push(note.vector);
        }
        let dimensions = validate_evidence(&vectors)?;
        let identity = evidence_identity(
            representation_version,
            dimensions,
            event_ids.iter().copied(),
            ratings.iter().copied(),
            vectors.iter(),
        );
        Ok(Self {
            event_ids,
            ratings,
            vectors,
            identity,
        })
    }

    fn contains(&self, event_id: EventId) -> bool {
        self.event_ids.contains(&event_id)
    }

    fn prospective_identity(
        &self,
        representation_version: &str,
        event_ids: &[EventId],
        ratings: &[GladnessRating],
        vectors: &[RatedVector],
    ) -> EvidenceIdentity {
        evidence_identity(
            representation_version,
            self.identity.vector_dimensions,
            self.event_ids
                .iter()
                .copied()
                .chain(event_ids.iter().copied()),
            self.ratings.iter().copied().chain(ratings.iter().copied()),
            self.vectors.iter().chain(vectors.iter()),
        )
    }

    fn append(
        &mut self,
        event_ids: Vec<EventId>,
        ratings: Vec<GladnessRating>,
        vectors: Vec<RatedVector>,
        identity: EvidenceIdentity,
    ) {
        self.event_ids.extend(event_ids);
        self.ratings.extend(ratings);
        self.vectors.extend(vectors);
        self.identity = identity;
    }
}

#[derive(Clone, Copy)]
struct ErrorAggregate {
    batch_mse_sum: f64,
    completed_batches: usize,
}

impl ErrorAggregate {
    fn add(self, batch_mse: f64) -> Self {
        Self {
            batch_mse_sum: self.batch_mse_sum + batch_mse,
            completed_batches: self.completed_batches + 1,
        }
    }

    fn mean(self) -> f64 {
        self.batch_mse_sum / self.completed_batches as f64
    }
}

struct PendingCompactBatch {
    frozen: CompactFrozenBatch,
    candidates: Vec<BatchCandidate>,
}

pub struct CompactLearningController {
    representation_version: String,
    evidence: EvidenceState,
    grid: Vec<CompactTuple>,
    active_index: usize,
    errors: Vec<ErrorAggregate>,
    pending: Option<PendingCompactBatch>,
    history: Vec<CompactRoundRecord>,
}

impl CompactLearningController {
    pub fn new(settings: CompactLearningSettings, evidence: Vec<EvidenceNote>) -> Result<Self> {
        let grid = compact_grid(&settings)?;
        let active_index = grid
            .iter()
            .position(|parameter_tuple| {
                parameter_tuple.scale_level == settings.initial_scale
                    && parameter_tuple.neighbor_count() == CompactNeighborCount::Finite(1)
                    && parameter_tuple.neutral_weight() == 1.0
            })
            .expect("approved initial compact tuple is in the generated grid");
        let evidence = EvidenceState::new(&settings.representation_version, evidence)?;
        let errors = vec![
            ErrorAggregate {
                batch_mse_sum: 0.0,
                completed_batches: 0,
            };
            grid.len()
        ];
        Ok(Self {
            representation_version: settings.representation_version,
            evidence,
            grid,
            active_index,
            errors,
            pending: None,
            history: Vec::new(),
        })
    }

    pub fn representation_version(&self) -> &str {
        &self.representation_version
    }

    pub fn evidence_count(&self) -> usize {
        self.evidence.vectors.len()
    }

    pub fn evidence_identity(&self) -> &EvidenceIdentity {
        &self.evidence.identity
    }

    pub fn active_tuple(&self) -> CompactTuple {
        self.grid[self.active_index]
    }

    pub fn pending_batch(&self) -> Option<&CompactFrozenBatch> {
        self.pending.as_ref().map(|pending| &pending.frozen)
    }

    pub fn history(&self) -> &[CompactRoundRecord] {
        &self.history
    }

    pub fn freeze_batch(&mut self, batch: CandidateBatch) -> Result<&CompactFrozenBatch> {
        if self.pending.is_some() {
            return Err(PersonalizerLearningError::BatchAlreadyFrozen);
        }
        require_representation_version(
            &self.representation_version,
            &batch.representation_version,
        )?;
        validate_new_candidates(&self.evidence, &batch.candidates)?;

        let parameters = self
            .grid
            .iter()
            .map(|parameter_tuple| parameter_tuple.parameters())
            .collect::<Vec<_>>();
        let scorer = CompactSupportScorer::new(&self.evidence.vectors, parameters[0])?;
        let mut scores_by_tuple = vec![Vec::with_capacity(batch.candidates.len()); self.grid.len()];
        for candidate in &batch.candidates {
            let candidate_scores = scorer.score_parameters(&candidate.vector, &parameters)?;
            for (scores, score) in scores_by_tuple.iter_mut().zip(candidate_scores) {
                scores.push(score);
            }
        }
        let predictions = self
            .grid
            .iter()
            .copied()
            .zip(scores_by_tuple)
            .map(|(parameter_tuple, scores)| CompactTuplePredictions {
                parameter_tuple,
                scores,
            })
            .collect();

        let frozen = CompactFrozenBatch {
            round: self.history.len() + 1,
            evidence_identity: self.evidence.identity.clone(),
            active_tuple: self.active_tuple(),
            candidate_ids: batch
                .candidates
                .iter()
                .map(BatchCandidate::event_id)
                .collect(),
            predictions,
        };
        self.pending = Some(PendingCompactBatch {
            frozen,
            candidates: batch.candidates,
        });
        Ok(&self.pending.as_ref().expect("pending batch was set").frozen)
    }

    pub fn complete_batch(&mut self, ratings: Vec<BatchRating>) -> Result<&CompactRoundRecord> {
        let pending = self
            .pending
            .as_ref()
            .ok_or(PersonalizerLearningError::NoFrozenBatch)?;
        let aligned_ratings = align_ratings(&pending.frozen.candidate_ids, &ratings)?;
        let outcomes = outcomes(&pending.frozen.candidate_ids, &aligned_ratings);
        let new_vectors = rated_candidate_vectors(&pending.candidates, &aligned_ratings)?;
        let new_errors = pending
            .frozen
            .predictions
            .iter()
            .zip(&self.errors)
            .map(|(predictions, aggregate)| {
                let batch_mse = mean_squared_error(&predictions.scores, &aligned_ratings);
                let aggregate = aggregate.add(batch_mse);
                (aggregate, batch_mse, aggregate.mean())
            })
            .collect::<Vec<_>>();
        let evaluations = pending
            .frozen
            .predictions
            .iter()
            .zip(&new_errors)
            .map(
                |(predictions, (_, batch_mse, cumulative_mse))| CompactTupleError {
                    parameter_tuple: predictions.parameter_tuple,
                    batch_mse: *batch_mse,
                    cumulative_mse: *cumulative_mse,
                },
            )
            .collect::<Vec<_>>();
        let next_index = select_compact_tuple(&evaluations);
        let next_tuple = self.grid[next_index];
        let event_ids = pending.frozen.candidate_ids.clone();
        let next_identity = self.evidence.prospective_identity(
            &self.representation_version,
            &event_ids,
            &aligned_ratings,
            &new_vectors,
        );
        let frozen = pending.frozen.clone();

        self.evidence.append(
            event_ids,
            aligned_ratings,
            new_vectors,
            next_identity.clone(),
        );
        self.errors = new_errors
            .into_iter()
            .map(|(aggregate, _, _)| aggregate)
            .collect();
        self.active_index = next_index;
        self.pending = None;
        self.history.push(CompactRoundRecord {
            frozen_batch: frozen,
            outcomes,
            errors: evaluations,
            evidence_after: next_identity,
            next_tuple,
        });
        Ok(self.history.last().expect("completed round was retained"))
    }
}

struct PendingRbfBatch {
    frozen: RbfFrozenBatch,
    candidates: Vec<BatchCandidate>,
}

pub struct RbfLearningController {
    representation_version: String,
    evidence: EvidenceState,
    grid: Vec<RbfTuple>,
    active_index: usize,
    errors: Vec<ErrorAggregate>,
    pending: Option<PendingRbfBatch>,
    history: Vec<RbfRoundRecord>,
}

impl RbfLearningController {
    pub fn new(settings: RbfLearningSettings, evidence: Vec<EvidenceNote>) -> Result<Self> {
        let grid = rbf_grid(&settings)?;
        let active_index = grid
            .iter()
            .position(|parameter_tuple| {
                parameter_tuple.scale_level == ScaleLevel::Mass64
                    && parameter_tuple.regularization() == 1.0
            })
            .expect("approved initial RBF tuple is in the generated grid");
        let evidence = EvidenceState::new(&settings.representation_version, evidence)?;
        let errors = vec![
            ErrorAggregate {
                batch_mse_sum: 0.0,
                completed_batches: 0,
            };
            grid.len()
        ];
        Ok(Self {
            representation_version: settings.representation_version,
            evidence,
            grid,
            active_index,
            errors,
            pending: None,
            history: Vec::new(),
        })
    }

    pub fn representation_version(&self) -> &str {
        &self.representation_version
    }

    pub fn evidence_count(&self) -> usize {
        self.evidence.vectors.len()
    }

    pub fn evidence_identity(&self) -> &EvidenceIdentity {
        &self.evidence.identity
    }

    pub fn active_tuple(&self) -> RbfTuple {
        self.grid[self.active_index]
    }

    pub fn pending_batch(&self) -> Option<&RbfFrozenBatch> {
        self.pending.as_ref().map(|pending| &pending.frozen)
    }

    pub fn history(&self) -> &[RbfRoundRecord] {
        &self.history
    }

    pub fn freeze_batch(&mut self, batch: CandidateBatch) -> Result<&RbfFrozenBatch> {
        if self.pending.is_some() {
            return Err(PersonalizerLearningError::BatchAlreadyFrozen);
        }
        require_representation_version(
            &self.representation_version,
            &batch.representation_version,
        )?;
        validate_new_candidates(&self.evidence, &batch.candidates)?;

        let mut predictions = Vec::with_capacity(self.grid.len());
        for parameter_tuple in &self.grid {
            let scorer =
                RbfKernelRidgeScorer::fit(&self.evidence.vectors, parameter_tuple.parameters())?;
            let scores = batch
                .candidates
                .iter()
                .map(|candidate| scorer.score(&candidate.vector))
                .collect::<std::result::Result<Vec<_>, _>>()?;
            predictions.push(RbfTuplePredictions {
                parameter_tuple: *parameter_tuple,
                scores,
            });
        }

        let frozen = RbfFrozenBatch {
            round: self.history.len() + 1,
            evidence_identity: self.evidence.identity.clone(),
            active_tuple: self.active_tuple(),
            candidate_ids: batch
                .candidates
                .iter()
                .map(BatchCandidate::event_id)
                .collect(),
            predictions,
        };
        self.pending = Some(PendingRbfBatch {
            frozen,
            candidates: batch.candidates,
        });
        Ok(&self.pending.as_ref().expect("pending batch was set").frozen)
    }

    pub fn complete_batch(&mut self, ratings: Vec<BatchRating>) -> Result<&RbfRoundRecord> {
        let pending = self
            .pending
            .as_ref()
            .ok_or(PersonalizerLearningError::NoFrozenBatch)?;
        let aligned_ratings = align_ratings(&pending.frozen.candidate_ids, &ratings)?;
        let outcomes = outcomes(&pending.frozen.candidate_ids, &aligned_ratings);
        let new_vectors = rated_candidate_vectors(&pending.candidates, &aligned_ratings)?;
        let new_errors = pending
            .frozen
            .predictions
            .iter()
            .zip(&self.errors)
            .map(|(predictions, aggregate)| {
                let deployed = predictions
                    .scores
                    .iter()
                    .map(|score| score.deployed)
                    .collect::<Vec<_>>();
                let batch_mse = mean_squared_error(&deployed, &aligned_ratings);
                let aggregate = aggregate.add(batch_mse);
                (aggregate, batch_mse, aggregate.mean())
            })
            .collect::<Vec<_>>();
        let evaluations = pending
            .frozen
            .predictions
            .iter()
            .zip(&new_errors)
            .map(
                |(predictions, (_, batch_mse, cumulative_mse))| RbfTupleError {
                    parameter_tuple: predictions.parameter_tuple,
                    batch_mse: *batch_mse,
                    cumulative_mse: *cumulative_mse,
                },
            )
            .collect::<Vec<_>>();
        let next_index = select_rbf_tuple(&evaluations);
        let next_tuple = self.grid[next_index];
        let event_ids = pending.frozen.candidate_ids.clone();
        let next_identity = self.evidence.prospective_identity(
            &self.representation_version,
            &event_ids,
            &aligned_ratings,
            &new_vectors,
        );
        let frozen = pending.frozen.clone();

        self.evidence.append(
            event_ids,
            aligned_ratings,
            new_vectors,
            next_identity.clone(),
        );
        self.errors = new_errors
            .into_iter()
            .map(|(aggregate, _, _)| aggregate)
            .collect();
        self.active_index = next_index;
        self.pending = None;
        self.history.push(RbfRoundRecord {
            frozen_batch: frozen,
            outcomes,
            errors: evaluations,
            evidence_after: next_identity,
            next_tuple,
        });
        Ok(self.history.last().expect("completed round was retained"))
    }
}

fn compact_grid(settings: &CompactLearningSettings) -> Result<Vec<CompactTuple>> {
    let mut grid = Vec::with_capacity(
        ScaleLevel::ALL.len() * COMPACT_NEIGHBOR_COUNTS.len() * COMPACT_NEUTRAL_WEIGHTS.len(),
    );
    for scale_level in ScaleLevel::ALL {
        for neighbor_count in COMPACT_NEIGHBOR_COUNTS {
            for neutral_weight in COMPACT_NEUTRAL_WEIGHTS {
                grid.push(CompactTuple {
                    scale_level,
                    parameters: CompactParameters::new(
                        neighbor_count,
                        settings.scale(scale_level),
                        neutral_weight,
                    )?,
                });
            }
        }
    }
    Ok(grid)
}

fn rbf_grid(settings: &RbfLearningSettings) -> Result<Vec<RbfTuple>> {
    let mut grid = Vec::with_capacity(ScaleLevel::ALL.len() * RBF_REGULARIZATIONS.len());
    for scale_level in ScaleLevel::ALL {
        for regularization in RBF_REGULARIZATIONS {
            grid.push(RbfTuple {
                scale_level,
                parameters: RbfKernelRidgeParameters::new(
                    settings.scale(scale_level),
                    regularization,
                )?,
            });
        }
    }
    Ok(grid)
}

fn validate_representation_version(representation_version: &str) -> Result<()> {
    if representation_version.is_empty() {
        return Err(PersonalizerLearningError::EmptyRepresentationVersion);
    }
    Ok(())
}

fn require_representation_version(expected: &str, actual: &str) -> Result<()> {
    if actual != expected {
        return Err(PersonalizerLearningError::RepresentationVersionMismatch {
            expected: expected.to_owned(),
            actual: actual.to_owned(),
        });
    }
    Ok(())
}

fn valid_scales(scales: [f64; 3]) -> bool {
    scales.iter().all(|scale| scale.is_finite() && *scale > 0.0)
        && scales[0] <= scales[1]
        && scales[1] <= scales[2]
}

fn valid_rbf_scales(scales: [f64; 3]) -> bool {
    scales
        .iter()
        .all(|scale| RbfKernelRidgeParameters::new(*scale, 1.0).is_ok())
        && scales[0] <= scales[1]
        && scales[1] <= scales[2]
}

fn validate_new_candidates(evidence: &EvidenceState, candidates: &[BatchCandidate]) -> Result<()> {
    for candidate in candidates {
        if evidence.contains(candidate.event_id) {
            return Err(PersonalizerLearningError::CandidateAlreadyInEvidence {
                event_id: candidate.event_id,
            });
        }
    }
    Ok(())
}

fn align_ratings(
    candidate_ids: &[EventId],
    ratings: &[BatchRating],
) -> Result<Vec<GladnessRating>> {
    let expected = candidate_ids.iter().copied().collect::<BTreeSet<_>>();
    let mut by_event = BTreeMap::new();
    for rating in ratings {
        if !expected.contains(&rating.event_id) {
            return Err(PersonalizerLearningError::UnexpectedRating {
                event_id: rating.event_id,
            });
        }
        if by_event.insert(rating.event_id, rating.rating).is_some() {
            return Err(PersonalizerLearningError::DuplicateRating {
                event_id: rating.event_id,
            });
        }
    }
    candidate_ids
        .iter()
        .map(|event_id| {
            by_event
                .get(event_id)
                .copied()
                .ok_or(PersonalizerLearningError::MissingRating {
                    event_id: *event_id,
                })
        })
        .collect()
}

fn outcomes(event_ids: &[EventId], ratings: &[GladnessRating]) -> Vec<RatedOutcome> {
    event_ids
        .iter()
        .zip(ratings)
        .map(|(event_id, rating)| RatedOutcome {
            event_id: *event_id,
            rating: *rating,
            target: rating.target(),
        })
        .collect()
}

fn rated_candidate_vectors(
    candidates: &[BatchCandidate],
    ratings: &[GladnessRating],
) -> Result<Vec<RatedVector>> {
    candidates
        .iter()
        .zip(ratings)
        .map(|(candidate, rating)| {
            RatedVector::new(candidate.vector.clone(), rating.target()).map_err(Into::into)
        })
        .collect()
}

fn mean_squared_error(predictions: &[f64], ratings: &[GladnessRating]) -> f64 {
    let sum = predictions
        .iter()
        .zip(ratings)
        .map(|(prediction, rating)| {
            let residual = prediction - rating.target();
            residual * residual
        })
        .sum::<f64>();
    sum / predictions.len() as f64
}

fn select_compact_tuple(errors: &[CompactTupleError]) -> usize {
    let mut best = 0;
    for candidate in 1..errors.len() {
        let ordering = errors[candidate]
            .cumulative_mse
            .total_cmp(&errors[best].cumulative_mse)
            .then_with(|| {
                compare_compact_tie(
                    errors[candidate].parameter_tuple,
                    errors[best].parameter_tuple,
                )
            });
        if ordering == Ordering::Less {
            best = candidate;
        }
    }
    best
}

fn compare_compact_tie(left: CompactTuple, right: CompactTuple) -> Ordering {
    left.maximum_distance()
        .total_cmp(&right.maximum_distance())
        .then_with(|| {
            neighbor_count_key(left.neighbor_count())
                .cmp(&neighbor_count_key(right.neighbor_count()))
        })
        .then_with(|| right.neutral_weight().total_cmp(&left.neutral_weight()))
}

fn neighbor_count_key(neighbor_count: CompactNeighborCount) -> usize {
    match neighbor_count {
        CompactNeighborCount::Finite(value) => value,
        CompactNeighborCount::Infinite => usize::MAX,
    }
}

fn select_rbf_tuple(errors: &[RbfTupleError]) -> usize {
    let mut best = 0;
    for candidate in 1..errors.len() {
        let ordering = errors[candidate]
            .cumulative_mse
            .total_cmp(&errors[best].cumulative_mse)
            .then_with(|| {
                compare_rbf_tie(
                    errors[candidate].parameter_tuple,
                    errors[best].parameter_tuple,
                )
            });
        if ordering == Ordering::Less {
            best = candidate;
        }
    }
    best
}

fn compare_rbf_tie(left: RbfTuple, right: RbfTuple) -> Ordering {
    left.scale()
        .total_cmp(&right.scale())
        .then_with(|| right.regularization().total_cmp(&left.regularization()))
}

fn evidence_identity<'a>(
    representation_version: &str,
    vector_dimensions: usize,
    event_ids: impl Iterator<Item = EventId>,
    ratings: impl Iterator<Item = GladnessRating>,
    vectors: impl Iterator<Item = &'a RatedVector>,
) -> EvidenceIdentity {
    let event_ids = event_ids.collect::<Vec<_>>();
    let ratings = ratings.collect::<Vec<_>>();
    let vectors = vectors.collect::<Vec<_>>();
    debug_assert_eq!(event_ids.len(), ratings.len());
    debug_assert_eq!(event_ids.len(), vectors.len());

    let mut bytes = Vec::new();
    bytes.extend_from_slice(EVIDENCE_IDENTITY_DOMAIN);
    append_usize(&mut bytes, representation_version.len());
    bytes.extend_from_slice(representation_version.as_bytes());
    append_usize(&mut bytes, event_ids.len());
    append_usize(&mut bytes, vector_dimensions);
    for ((event_id, rating), vector) in event_ids.iter().zip(&ratings).zip(&vectors) {
        bytes.extend_from_slice(event_id);
        bytes.push(rating.value());
        bytes.extend_from_slice(&vector.target().to_bits().to_le_bytes());
        append_usize(&mut bytes, vector.vector().len());
        for coordinate in vector.vector() {
            bytes.extend_from_slice(&coordinate.to_bits().to_le_bytes());
        }
    }

    EvidenceIdentity {
        representation_version: representation_version.to_owned(),
        event_count: event_ids.len(),
        vector_dimensions,
        sha256: hash_bytes(&bytes),
    }
}

fn append_usize(bytes: &mut Vec<u8>, value: usize) {
    bytes.extend_from_slice(
        &u64::try_from(value)
            .expect("in-memory collection length fits u64")
            .to_le_bytes(),
    );
}
