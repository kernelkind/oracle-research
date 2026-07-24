//! Deterministic exposure-aware selection over one frozen support order.

use std::collections::BTreeSet;

use thiserror::Error;

use crate::representation::EventId;

const UNIT_NORM_TOLERANCE: f64 = 1.0e-5;

/// The median pairwise cosine frozen by CREC-102.
pub const CREC_102_TYPICAL_PAIR_COSINE: f64 = 0.420_874_672_461_660_55;
/// Presentation-distance half-life frozen by CREC-102.
pub const CREC_102_EXPOSURE_HALF_LIFE: u32 = 20;
/// Number of highest-support remaining candidates eligible at each step.
pub const STATIC_EXPOSURE_TRANCHE_SIZE: usize = 64;
/// Maximum number of presentations in the static live probe.
pub const STATIC_EXPOSURE_PRESENTATION_QUOTA: usize = 40;

pub type Result<T> = std::result::Result<T, AdjacentNoveltyError>;

#[derive(Debug, Error, PartialEq)]
pub enum AdjacentNoveltyError {
    #[error("candidate vector must not be empty")]
    EmptyVector,
    #[error("candidate vector coordinate {index} is not finite")]
    NonFiniteCoordinate { index: usize },
    #[error("candidate vector must be unit normalized")]
    NonUnitVector,
    #[error("candidate {event_id:?} is duplicated in the frozen support order")]
    DuplicateCandidate { event_id: EventId },
    #[error("seeded exposure event {event_id:?} is already in the older exclusion history")]
    SeededHistoryAlreadyExcluded { event_id: EventId },
    #[error("candidate vector dimension mismatch: expected {expected}, got {actual}")]
    DimensionMismatch { expected: usize, actual: usize },
    #[error("presentation quota must be positive")]
    InvalidPresentationQuota,
    #[error("exposure ceiling must be finite and positive")]
    InvalidExposureCeiling,
    #[error("a selected presentation is already pending")]
    PresentationPending,
    #[error("there is no selected presentation to record")]
    NoPendingPresentation,
    #[error("exposure calculation produced a non-finite value")]
    NonFiniteExposure,
}

/// One public note in the already-frozen descending support order.
#[derive(Clone, Debug, PartialEq)]
pub struct ExposureCandidate {
    event_id: EventId,
    vector: Vec<f32>,
}

impl ExposureCandidate {
    pub fn new(event_id: EventId, vector: Vec<f32>) -> Result<Self> {
        validate_vector(&vector)?;
        Ok(Self { event_id, vector })
    }

    pub const fn event_id(&self) -> EventId {
        self.event_id
    }

    pub fn vector(&self) -> &[f32] {
        &self.vector
    }
}

/// One candidate considered in an exposure-aware selection step.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct ExposureTrancheEntry {
    event_id: EventId,
    support_order_index: usize,
    exposure: f64,
}

impl ExposureTrancheEntry {
    pub const fn event_id(self) -> EventId {
        self.event_id
    }

    pub const fn support_order_index(self) -> usize {
        self.support_order_index
    }

    pub const fn exposure(self) -> f64 {
        self.exposure
    }
}

/// The next pending presentation selected from the frozen support order.
#[derive(Clone, Debug, PartialEq)]
pub struct ExposureSelection {
    event_id: EventId,
    support_order_index: usize,
    exposure: f64,
    tranche: Vec<ExposureTrancheEntry>,
}

impl ExposureSelection {
    pub const fn event_id(&self) -> EventId {
        self.event_id
    }

    pub const fn support_order_index(&self) -> usize {
        self.support_order_index
    }

    pub const fn exposure(&self) -> f64 {
        self.exposure
    }

    pub fn tranche(&self) -> &[ExposureTrancheEntry] {
        &self.tranche
    }
}

/// Pure static selector used by the bounded adjacent-novelty live probe.
///
/// Candidate order is support order. Recent presentation exposure may reorder
/// only the first 64 remaining candidates. A selected note becomes excluded
/// and starts contributing exposure only when [`Self::record_presentation`] is
/// called. The method deliberately accepts no rating or diagnostic outcome.
pub struct StaticExposureSelector {
    candidates: Vec<ExposureCandidate>,
    excluded_event_ids: BTreeSet<EventId>,
    presented_candidate_indices: Vec<usize>,
    presentation_quota: usize,
    pending: Option<ExposureSelection>,
}

/// One selection made by scanning the complete frozen support order and
/// applying a hard exposure ceiling.
#[derive(Clone, Debug, PartialEq)]
pub struct FullPoolExposureSelection {
    event_id: EventId,
    support_order_index: usize,
    exposure: f64,
    survivor_count: usize,
    rejected_by_ceiling_count: usize,
}

impl FullPoolExposureSelection {
    pub const fn event_id(&self) -> EventId {
        self.event_id
    }

    pub const fn support_order_index(&self) -> usize {
        self.support_order_index
    }

    pub const fn exposure(&self) -> f64 {
        self.exposure
    }

    pub const fn survivor_count(&self) -> usize {
        self.survivor_count
    }

    pub const fn rejected_by_ceiling_count(&self) -> usize {
        self.rejected_by_ceiling_count
    }
}

/// Select the highest-supported candidate whose exposure remains below one
/// frozen ceiling.
///
/// Candidate order is the frozen support order. `seeded_history` contributes
/// exposure before the first new presentation but does not consume the new
/// run's presentation quota. Ratings and repetition answers are deliberately
/// absent from this state transition.
pub struct FullPoolExposureGateSelector {
    candidates: Vec<ExposureCandidate>,
    excluded_event_ids: BTreeSet<EventId>,
    candidate_exposures: Vec<f64>,
    exposure_ceiling: f64,
    presentation_quota: usize,
    presentations_recorded: usize,
    pending: Option<FullPoolExposureSelection>,
}

impl FullPoolExposureGateSelector {
    pub fn new(
        candidates: Vec<ExposureCandidate>,
        mut historical_event_ids: BTreeSet<EventId>,
        seeded_history: Vec<ExposureCandidate>,
        exposure_ceiling: f64,
        presentation_quota: usize,
    ) -> Result<Self> {
        if !exposure_ceiling.is_finite() || exposure_ceiling <= 0.0 {
            return Err(AdjacentNoveltyError::InvalidExposureCeiling);
        }
        if presentation_quota == 0 {
            return Err(AdjacentNoveltyError::InvalidPresentationQuota);
        }
        let dimensions = candidates
            .first()
            .map(|candidate| candidate.vector.len())
            .or_else(|| {
                seeded_history
                    .first()
                    .map(|candidate| candidate.vector.len())
            })
            .unwrap_or(0);
        let mut candidate_ids = BTreeSet::new();
        for candidate in &candidates {
            if candidate.vector.len() != dimensions {
                return Err(AdjacentNoveltyError::DimensionMismatch {
                    expected: dimensions,
                    actual: candidate.vector.len(),
                });
            }
            if !candidate_ids.insert(candidate.event_id) {
                return Err(AdjacentNoveltyError::DuplicateCandidate {
                    event_id: candidate.event_id,
                });
            }
        }
        let mut history_ids = BTreeSet::new();
        let mut exposure_history = Vec::with_capacity(seeded_history.len());
        for presentation in seeded_history {
            if presentation.vector.len() != dimensions {
                return Err(AdjacentNoveltyError::DimensionMismatch {
                    expected: dimensions,
                    actual: presentation.vector.len(),
                });
            }
            if !history_ids.insert(presentation.event_id) {
                return Err(AdjacentNoveltyError::DuplicateCandidate {
                    event_id: presentation.event_id,
                });
            }
            if historical_event_ids.contains(&presentation.event_id) {
                return Err(AdjacentNoveltyError::SeededHistoryAlreadyExcluded {
                    event_id: presentation.event_id,
                });
            }
            historical_event_ids.insert(presentation.event_id);
            exposure_history.push(presentation.vector);
        }
        let candidate_exposures = candidates
            .iter()
            .map(|candidate| {
                exposure_from_iter(
                    candidate.vector(),
                    exposure_history.iter().map(Vec::as_slice),
                )
            })
            .collect::<Result<Vec<_>>>()?;
        Ok(Self {
            candidates,
            excluded_event_ids: historical_event_ids,
            candidate_exposures,
            exposure_ceiling,
            presentation_quota,
            presentations_recorded: 0,
            pending: None,
        })
    }

    /// Scan all remaining candidates, then select the first survivor in frozen
    /// support order.
    pub fn select_next(&mut self) -> Result<Option<FullPoolExposureSelection>> {
        if self.pending.is_some() {
            return Err(AdjacentNoveltyError::PresentationPending);
        }
        if self.is_complete() {
            return Ok(None);
        }

        let mut selected = None;
        let mut survivor_count = 0_usize;
        let mut rejected_by_ceiling_count = 0_usize;
        for support_order_index in (0..self.candidates.len()).filter(|index| {
            !self
                .excluded_event_ids
                .contains(&self.candidates[*index].event_id)
        }) {
            let exposure = self.candidate_exposures[support_order_index];
            if exposure < self.exposure_ceiling {
                survivor_count += 1;
                if selected.is_none() {
                    selected = Some((support_order_index, exposure));
                }
            } else {
                rejected_by_ceiling_count += 1;
            }
        }

        let Some((support_order_index, exposure)) = selected else {
            return Ok(None);
        };
        let selection = FullPoolExposureSelection {
            event_id: self.candidates[support_order_index].event_id,
            support_order_index,
            exposure,
            survivor_count,
            rejected_by_ceiling_count,
        };
        self.pending = Some(selection.clone());
        Ok(Some(selection))
    }

    /// Record the pending note as shown, independent of every later outcome.
    pub fn record_presentation(&mut self) -> Result<()> {
        let selection = self
            .pending
            .take()
            .ok_or(AdjacentNoveltyError::NoPendingPresentation)?;
        let inserted = self.excluded_event_ids.insert(selection.event_id);
        debug_assert!(inserted, "a pending selection must not already be excluded");
        let shown_vector = self.candidates[selection.support_order_index].vector();
        let decay = 2.0_f64.powf(-1.0 / f64::from(CREC_102_EXPOSURE_HALF_LIFE));
        for (candidate, exposure) in self.candidates.iter().zip(&mut self.candidate_exposures) {
            let cosine = candidate
                .vector()
                .iter()
                .copied()
                .zip(shown_vector.iter().copied())
                .map(|(left, right)| f64::from(left) * f64::from(right))
                .sum::<f64>();
            let new_evidence = (cosine - CREC_102_TYPICAL_PAIR_COSINE).max(0.0);
            *exposure = decay * (*exposure + new_evidence);
            if !exposure.is_finite() {
                return Err(AdjacentNoveltyError::NonFiniteExposure);
            }
        }
        self.presentations_recorded += 1;
        Ok(())
    }

    pub const fn exposure_ceiling(&self) -> f64 {
        self.exposure_ceiling
    }

    pub const fn presentations_recorded(&self) -> usize {
        self.presentations_recorded
    }

    pub const fn presentation_quota(&self) -> usize {
        self.presentation_quota
    }

    pub const fn is_complete(&self) -> bool {
        self.presentations_recorded >= self.presentation_quota
    }
}

impl StaticExposureSelector {
    pub fn new(
        candidates: Vec<ExposureCandidate>,
        historical_event_ids: BTreeSet<EventId>,
    ) -> Result<Self> {
        Self::with_presentation_quota(
            candidates,
            historical_event_ids,
            STATIC_EXPOSURE_PRESENTATION_QUOTA,
        )
    }

    /// Construct a selector with an explicit presentation ceiling.
    ///
    /// This is used when a runner must reserve bounded replacement
    /// presentations for outcomes that do not consume its valid-rating quota.
    pub fn with_presentation_quota(
        candidates: Vec<ExposureCandidate>,
        historical_event_ids: BTreeSet<EventId>,
        presentation_quota: usize,
    ) -> Result<Self> {
        if presentation_quota == 0 {
            return Err(AdjacentNoveltyError::InvalidPresentationQuota);
        }
        let dimensions = candidates
            .first()
            .map(|candidate| candidate.vector.len())
            .unwrap_or(0);
        let mut candidate_ids = BTreeSet::new();
        for candidate in &candidates {
            if candidate.vector.len() != dimensions {
                return Err(AdjacentNoveltyError::DimensionMismatch {
                    expected: dimensions,
                    actual: candidate.vector.len(),
                });
            }
            if !candidate_ids.insert(candidate.event_id) {
                return Err(AdjacentNoveltyError::DuplicateCandidate {
                    event_id: candidate.event_id,
                });
            }
        }
        Ok(Self {
            candidates,
            excluded_event_ids: historical_event_ids,
            presented_candidate_indices: Vec::new(),
            presentation_quota,
            pending: None,
        })
    }

    /// Select the minimum-exposure note from the first 64 remaining candidates.
    ///
    /// Exact exposure ties preserve the frozen support order. The selected
    /// choice remains pending until the caller records that it was displayed.
    pub fn select_next(&mut self) -> Result<Option<ExposureSelection>> {
        if self.pending.is_some() {
            return Err(AdjacentNoveltyError::PresentationPending);
        }
        if self.is_complete() {
            return Ok(None);
        }

        let mut selected: Option<(usize, f64)> = None;
        let mut tranche = Vec::with_capacity(STATIC_EXPOSURE_TRANCHE_SIZE);
        for (support_order_index, candidate) in self
            .candidates
            .iter()
            .enumerate()
            .filter(|(_, candidate)| !self.excluded_event_ids.contains(&candidate.event_id))
            .take(STATIC_EXPOSURE_TRANCHE_SIZE)
        {
            let exposure = self.exposure(candidate.vector())?;
            tranche.push(ExposureTrancheEntry {
                event_id: candidate.event_id,
                support_order_index,
                exposure,
            });
            match selected {
                None => selected = Some((support_order_index, exposure)),
                Some((_, selected_exposure)) if exposure.total_cmp(&selected_exposure).is_lt() => {
                    selected = Some((support_order_index, exposure));
                }
                Some(_) => {}
            }
        }

        let Some((support_order_index, exposure)) = selected else {
            return Ok(None);
        };
        let selection = ExposureSelection {
            event_id: self.candidates[support_order_index].event_id,
            support_order_index,
            exposure,
            tranche,
        };
        self.pending = Some(selection.clone());
        Ok(Some(selection))
    }

    /// Record the pending note as presented, independent of its later outcome.
    pub fn record_presentation(&mut self) -> Result<()> {
        let selection = self
            .pending
            .take()
            .ok_or(AdjacentNoveltyError::NoPendingPresentation)?;
        let inserted = self.excluded_event_ids.insert(selection.event_id);
        debug_assert!(inserted, "a pending selection must not already be excluded");
        self.presented_candidate_indices
            .push(selection.support_order_index);
        Ok(())
    }

    pub fn presentations_recorded(&self) -> usize {
        self.presented_candidate_indices.len()
    }

    pub const fn presentation_quota(&self) -> usize {
        self.presentation_quota
    }

    pub fn is_complete(&self) -> bool {
        self.presentations_recorded() >= self.presentation_quota
    }

    fn exposure(&self, candidate: &[f32]) -> Result<f64> {
        exposure_from_iter(
            candidate,
            self.presented_candidate_indices
                .iter()
                .map(|index| self.candidates[*index].vector.as_slice()),
        )
    }
}

fn exposure_from_iter<'a>(
    candidate: &[f32],
    history: impl ExactSizeIterator<Item = &'a [f32]>,
) -> Result<f64> {
    let presentation_count = history.len();
    let mut exposure = 0.0_f64;
    for (prior_index, prior) in history.enumerate() {
        let cosine = candidate
            .iter()
            .copied()
            .zip(prior.iter().copied())
            .map(|(left, right)| f64::from(left) * f64::from(right))
            .sum::<f64>();
        let age = presentation_count - prior_index;
        let decay = 2.0_f64.powf(-(age as f64) / f64::from(CREC_102_EXPOSURE_HALF_LIFE));
        exposure += decay * (cosine - CREC_102_TYPICAL_PAIR_COSINE).max(0.0);
    }
    if exposure.is_finite() {
        Ok(exposure)
    } else {
        Err(AdjacentNoveltyError::NonFiniteExposure)
    }
}

fn validate_vector(vector: &[f32]) -> Result<()> {
    if vector.is_empty() {
        return Err(AdjacentNoveltyError::EmptyVector);
    }
    let mut norm_squared = 0.0_f64;
    for (index, coordinate) in vector.iter().copied().enumerate() {
        if !coordinate.is_finite() {
            return Err(AdjacentNoveltyError::NonFiniteCoordinate { index });
        }
        norm_squared += f64::from(coordinate) * f64::from(coordinate);
    }
    if (norm_squared - 1.0).abs() > UNIT_NORM_TOLERANCE {
        return Err(AdjacentNoveltyError::NonUnitVector);
    }
    Ok(())
}
