//! Ten-round adaptive learning over the two approved personalizers.

use std::collections::{BTreeMap, BTreeSet};

use thiserror::Error;

use crate::candidate_order::{
    B16Boundary, CANDIDATE_DEPTH, CandidateOrderError, CandidateOrderOracle, CandidateOrderOutcome,
    CandidateOrderPhase, CandidateOrderRequest, CandidateVectorCache,
    build_compact_candidate_order, build_rbf_candidate_order,
};
use crate::fp32_oracle::{SimilarNotesRequest, SimilarNotesWaveMetrics};
use crate::personalizer_learning::{
    BatchRating, CompactLearningController, GladnessRating, RbfLearningController,
};
use crate::quota_resolution::{
    EventLanguageOutcome, LanguageEligibility, PersonalizerId, PresentationLedgerSnapshot,
    PriorPresentation, QuotaResolutionError, QuotaResolutionFailure, QuotaResolutionProgress,
    SharedQuotaResolver,
};
use crate::representation::EventId;
use crate::shared_learning_round::{
    SharedLearningRoundRecord, SharedLearningRoundState, discard_shared_learning_round_state,
    finish_shared_learning_round_state, prepare_shared_learning_round_state,
    submit_shared_learning_round_ratings,
};
use crate::snapshot::Error as SnapshotError;

pub(crate) const SEED_COUNT: usize = 5;
pub(crate) const LEARNING_ROUNDS: usize = 10;
pub(crate) const MAX_WRONG_LANGUAGE_PRESENTATIONS: usize = 21;

pub type Result<T> = std::result::Result<T, AdaptiveLearningError>;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum AdaptiveLearningProgress {
    Ready,
    AwaitingLanguage,
    AwaitingRatings,
    Complete,
    Paused,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum AdaptiveLearningFailure {
    SeedVectorMismatch {
        event_id: EventId,
    },
    InsufficientCandidateOrder {
        personalizer: PersonalizerId,
        accepted: usize,
        required: usize,
    },
    QuotaResolution(QuotaResolutionFailure),
    WrongLanguageLimit {
        wrong_language: usize,
        unique_presentations: usize,
    },
    FinalLanguageCeiling {
        wrong_language: usize,
        unique_presentations: usize,
    },
    SharedRound(String),
    InternalInvariant(String),
}

#[derive(Debug, Error)]
pub enum AdaptiveLearningError {
    #[error(transparent)]
    CandidateOrder(#[from] CandidateOrderError),
    #[error(transparent)]
    Oracle(#[from] SnapshotError),
    #[error(transparent)]
    QuotaResolution(#[from] QuotaResolutionError),
    #[error("the Oracle, both personalizers, and B16 must use one representation version")]
    RepresentationVersionMismatch,
    #[error("both personalizers must start from exactly {SEED_COUNT} seed notes")]
    InvalidSeedCount,
    #[error("both personalizers must start from the same ordered seed evidence")]
    SeedEvidenceMismatch,
    #[error("seed {event_id:?} is not positive evidence")]
    NonPositiveSeed { event_id: EventId },
    #[error("adaptive learning requires empty histories and no pending batches")]
    LearningAlreadyStarted,
    #[error("adaptive learning is {actual:?}; expected {expected:?}")]
    InvalidProgress {
        expected: AdaptiveLearningProgress,
        actual: AdaptiveLearningProgress,
    },
    #[error("rating repeats event {event_id:?}")]
    DuplicateRating { event_id: EventId },
    #[error("rating references event {event_id:?} outside the pending new-rating set")]
    UnexpectedRating { event_id: EventId },
    #[error("pending new-rating event {event_id:?} has no rating")]
    MissingRating { event_id: EventId },
    #[error("stored event {event_id:?} has no retained numeric rating")]
    MissingStoredRating { event_id: EventId },
    #[error("all adaptive-learning rounds are complete")]
    LearningComplete,
    #[error("adaptive learning is paused: {0:?}")]
    PhasePaused(AdaptiveLearningFailure),
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct LearningLanguageTotals {
    eligible_presentations: usize,
    wrong_language_presentations: usize,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct LearningSourceWaveRecord {
    round: usize,
    source_event_ids: Vec<EventId>,
    metrics: SimilarNotesWaveMetrics,
    accepted: bool,
}

impl LearningSourceWaveRecord {
    pub const fn round(&self) -> usize {
        self.round
    }

    pub fn source_event_ids(&self) -> &[EventId] {
        &self.source_event_ids
    }

    pub const fn metrics(&self) -> &SimilarNotesWaveMetrics {
        &self.metrics
    }

    pub const fn accepted(&self) -> bool {
        self.accepted
    }
}

impl LearningLanguageTotals {
    pub const fn eligible_presentations(self) -> usize {
        self.eligible_presentations
    }

    pub const fn wrong_language_presentations(self) -> usize {
        self.wrong_language_presentations
    }

    pub const fn unique_presentations(self) -> usize {
        self.eligible_presentations + self.wrong_language_presentations
    }

    fn record(&mut self, eligibility: LanguageEligibility) {
        match eligibility {
            LanguageEligibility::Eligible => self.eligible_presentations += 1,
            LanguageEligibility::WrongLanguage => self.wrong_language_presentations += 1,
        }
    }

    fn within_ceiling(self) -> bool {
        (self.wrong_language_presentations as u128) * 20 <= self.unique_presentations() as u128
    }
}

enum LearningState {
    Ready,
    Resolving(Box<SharedQuotaResolver>),
    AwaitingRatings(Box<SharedLearningRoundState>),
    Complete,
    Paused(AdaptiveLearningFailure),
}

pub struct AdaptiveLearningCoordinator {
    compact: CompactLearningController,
    rbf: RbfLearningController,
    vector_cache: CandidateVectorCache,
    b16: B16Boundary,
    presentation_ledger: BTreeMap<EventId, PriorPresentation>,
    ratings: BTreeMap<EventId, GladnessRating>,
    language_totals: LearningLanguageTotals,
    source_wave_records: Vec<LearningSourceWaveRecord>,
    round_records: Vec<SharedLearningRoundRecord>,
    seed_vectors_verified: bool,
    state: LearningState,
}

impl AdaptiveLearningCoordinator {
    pub fn new<O: CandidateOrderOracle>(
        oracle: &O,
        compact: CompactLearningController,
        rbf: RbfLearningController,
        b16: B16Boundary,
    ) -> Result<Self> {
        let version = compact.representation_version();
        if rbf.representation_version() != version
            || oracle.representation_version() != version
            || b16.representation_version() != version
        {
            return Err(AdaptiveLearningError::RepresentationVersionMismatch);
        }
        if !compact.history().is_empty()
            || !rbf.history().is_empty()
            || compact.pending_batch().is_some()
            || rbf.pending_batch().is_some()
        {
            return Err(AdaptiveLearningError::LearningAlreadyStarted);
        }
        if compact.evidence_count() != SEED_COUNT || rbf.evidence_count() != SEED_COUNT {
            return Err(AdaptiveLearningError::InvalidSeedCount);
        }
        if compact.evidence_identity() != rbf.evidence_identity() {
            return Err(AdaptiveLearningError::SeedEvidenceMismatch);
        }
        for (event_id, rating) in compact
            .evidence_event_ids()
            .iter()
            .copied()
            .zip(compact.evidence_ratings().iter().copied())
        {
            if rating.target() <= 0.0 {
                return Err(AdaptiveLearningError::NonPositiveSeed { event_id });
            }
        }

        let vector_cache = CandidateVectorCache::new(version)?;

        let mut presentation_ledger = BTreeMap::new();
        let mut ratings = BTreeMap::new();
        for (event_id, rating) in compact
            .evidence_event_ids()
            .iter()
            .copied()
            .zip(compact.evidence_ratings().iter().copied())
        {
            presentation_ledger.insert(
                event_id,
                PriorPresentation::rated_by([PersonalizerId::Compact, PersonalizerId::Rbf])?,
            );
            ratings.insert(event_id, rating);
        }
        Ok(Self {
            compact,
            rbf,
            vector_cache,
            b16,
            presentation_ledger,
            ratings,
            language_totals: LearningLanguageTotals::default(),
            source_wave_records: Vec::new(),
            round_records: Vec::with_capacity(LEARNING_ROUNDS),
            seed_vectors_verified: false,
            state: LearningState::Ready,
        })
    }

    pub fn progress(&self) -> AdaptiveLearningProgress {
        match self.state {
            LearningState::Ready => AdaptiveLearningProgress::Ready,
            LearningState::Resolving(_) => AdaptiveLearningProgress::AwaitingLanguage,
            LearningState::AwaitingRatings(_) => AdaptiveLearningProgress::AwaitingRatings,
            LearningState::Complete => AdaptiveLearningProgress::Complete,
            LearningState::Paused(_) => AdaptiveLearningProgress::Paused,
        }
    }

    pub fn next_round(&self) -> Option<usize> {
        matches!(self.state, LearningState::Ready).then(|| self.round_records.len() + 1)
    }

    pub fn compact_controller(&self) -> &CompactLearningController {
        &self.compact
    }

    pub fn rbf_controller(&self) -> &RbfLearningController {
        &self.rbf
    }

    pub fn presentation_ledger(&self) -> &BTreeMap<EventId, PriorPresentation> {
        &self.presentation_ledger
    }

    pub fn ratings(&self) -> &BTreeMap<EventId, GladnessRating> {
        &self.ratings
    }

    pub const fn language_totals(&self) -> LearningLanguageTotals {
        self.language_totals
    }

    pub fn round_records(&self) -> &[SharedLearningRoundRecord] {
        &self.round_records
    }

    pub fn source_wave_records(&self) -> &[LearningSourceWaveRecord] {
        &self.source_wave_records
    }

    pub fn pause_reason(&self) -> Option<&AdaptiveLearningFailure> {
        match &self.state {
            LearningState::Paused(reason) => Some(reason),
            _ => None,
        }
    }

    pub fn start_next_round<O: CandidateOrderOracle>(&mut self, oracle: &mut O) -> Result<()> {
        match &self.state {
            LearningState::Complete => return Err(AdaptiveLearningError::LearningComplete),
            LearningState::Paused(reason) => {
                return Err(AdaptiveLearningError::PhasePaused(reason.clone()));
            }
            LearningState::Ready => {}
            _ => return Err(self.invalid_progress(AdaptiveLearningProgress::Ready)),
        }
        if self.round_records.len() == LEARNING_ROUNDS {
            self.state = LearningState::Complete;
            return Err(AdaptiveLearningError::LearningComplete);
        }

        if oracle.representation_version() != self.compact.representation_version() {
            return Err(AdaptiveLearningError::RepresentationVersionMismatch);
        }
        self.verify_seed_vectors(oracle)?;
        let source_wave_index = self.prefetch_positive_sources(oracle)?;

        let disallowed = self.learning_disallowed_event_ids();
        let request =
            CandidateOrderRequest::new(CandidateOrderPhase::Learning, self.b16.clone(), disallowed);
        let compact_order = match build_compact_candidate_order(
            &self.compact,
            oracle,
            &mut self.vector_cache,
            &request,
        )? {
            CandidateOrderOutcome::Frozen(order) => order,
            CandidateOrderOutcome::Insufficient(insufficient) => {
                return self.pause(AdaptiveLearningFailure::InsufficientCandidateOrder {
                    personalizer: PersonalizerId::Compact,
                    accepted: insufficient.accepted_count(),
                    required: insufficient.required_count(),
                });
            }
        };
        let rbf_order =
            match build_rbf_candidate_order(&self.rbf, oracle, &mut self.vector_cache, &request)? {
                CandidateOrderOutcome::Frozen(order) => order,
                CandidateOrderOutcome::Insufficient(insufficient) => {
                    return self.pause(AdaptiveLearningFailure::InsufficientCandidateOrder {
                        personalizer: PersonalizerId::Rbf,
                        accepted: insufficient.accepted_count(),
                        required: insufficient.required_count(),
                    });
                }
            };
        let ledger = PresentationLedgerSnapshot::new(self.presentation_ledger.clone())?;
        let resolver = match SharedQuotaResolver::new(compact_order, rbf_order, ledger) {
            Ok(resolver) => resolver,
            Err(error) => {
                return self.pause(AdaptiveLearningFailure::InternalInvariant(
                    error.to_string(),
                ));
            }
        };
        self.source_wave_records[source_wave_index].accepted = true;
        let progress = resolver.progress();
        self.state = LearningState::Resolving(Box::new(resolver));
        match progress {
            QuotaResolutionProgress::AwaitingLanguage => Ok(()),
            QuotaResolutionProgress::Complete => self.prepare_pending_ratings(),
            QuotaResolutionProgress::Failed => {
                self.pause(AdaptiveLearningFailure::InternalInvariant(
                    "new quota resolver started in a failed state".to_owned(),
                ))
            }
        }
    }

    pub fn pending_language_wave(&self) -> Option<&crate::quota_resolution::PresentationWave> {
        match &self.state {
            LearningState::Resolving(resolver) => resolver.pending_wave(),
            _ => None,
        }
    }

    pub fn submit_language_outcomes(
        &mut self,
        wave_id: u64,
        outcomes: Vec<EventLanguageOutcome>,
    ) -> Result<()> {
        let actual = self.progress();
        let resolver = match &mut self.state {
            LearningState::Resolving(resolver) => resolver,
            LearningState::Paused(reason) => {
                return Err(AdaptiveLearningError::PhasePaused(reason.clone()));
            }
            _ => {
                return Err(AdaptiveLearningError::InvalidProgress {
                    expected: AdaptiveLearningProgress::AwaitingLanguage,
                    actual,
                });
            }
        };
        if let Some(existing) = resolver
            .pending_wave()
            .and_then(|wave| {
                wave.event_ids()
                    .iter()
                    .find(|event_id| self.presentation_ledger.contains_key(*event_id))
            })
            .copied()
        {
            return self.pause(AdaptiveLearningFailure::InternalInvariant(format!(
                "pending language event {existing:?} is already in the presentation ledger"
            )));
        }

        resolver.submit_language_outcomes(wave_id, outcomes.clone())?;
        let resolution_progress = resolver.progress();
        self.record_presentations(&outcomes);

        let before_final_round = self.round_records.len() + 1 < LEARNING_ROUNDS;
        if before_final_round
            && self.language_totals.wrong_language_presentations > MAX_WRONG_LANGUAGE_PRESENTATIONS
        {
            return self.pause(AdaptiveLearningFailure::WrongLanguageLimit {
                wrong_language: self.language_totals.wrong_language_presentations,
                unique_presentations: self.language_totals.unique_presentations(),
            });
        }

        match resolution_progress {
            QuotaResolutionProgress::AwaitingLanguage => Ok(()),
            QuotaResolutionProgress::Failed => {
                let resolver = self.take_resolver();
                match resolver.into_result() {
                    Err(QuotaResolutionError::ResolutionFailed(failed)) => self.pause(
                        AdaptiveLearningFailure::QuotaResolution(failed.failure().clone()),
                    ),
                    Err(error) => self.pause(AdaptiveLearningFailure::InternalInvariant(
                        error.to_string(),
                    )),
                    Ok(_) => self.pause(AdaptiveLearningFailure::InternalInvariant(
                        "failed quota resolver unexpectedly produced a result".to_owned(),
                    )),
                }
            }
            QuotaResolutionProgress::Complete => self.prepare_pending_ratings(),
        }
    }

    pub fn pending_rating_event_ids(&self) -> Option<&[EventId]> {
        match &self.state {
            LearningState::AwaitingRatings(state) => Some(state.new_rating_event_ids()),
            _ => None,
        }
    }

    pub fn submit_ratings(&mut self, ratings: Vec<BatchRating>) -> Result<()> {
        let actual = self.progress();
        let required_event_ids = match &self.state {
            LearningState::AwaitingRatings(state) => state.new_rating_event_ids().to_vec(),
            LearningState::Paused(reason) => {
                return Err(AdaptiveLearningError::PhasePaused(reason.clone()));
            }
            _ => {
                return Err(AdaptiveLearningError::InvalidProgress {
                    expected: AdaptiveLearningProgress::AwaitingRatings,
                    actual,
                });
            }
        };
        let new_ratings = validate_new_ratings(&required_event_ids, ratings)?;
        let mut state = self.take_pending_ratings();
        let all_required_event_ids = state.required_rating_event_ids().to_vec();
        let mut merged_ratings = Vec::with_capacity(all_required_event_ids.len());
        for event_id in all_required_event_ids {
            if let Some(rating) = new_ratings.get(&event_id) {
                merged_ratings.push(*rating);
            } else {
                let rating = match self.ratings.get(&event_id).copied() {
                    Some(rating) => rating,
                    None => {
                        self.state = LearningState::AwaitingRatings(state);
                        return Err(AdaptiveLearningError::MissingStoredRating { event_id });
                    }
                };
                merged_ratings.push(
                    BatchRating::new(event_id, rating.value())
                        .expect("retained GladnessRating remains valid"),
                );
            }
        }

        if let Err(error) = submit_shared_learning_round_ratings(
            &mut state,
            &mut self.compact,
            &mut self.rbf,
            merged_ratings,
        ) {
            discard_shared_learning_round_state(state, &mut self.compact, &mut self.rbf);
            return self.pause(AdaptiveLearningFailure::SharedRound(error.to_string()));
        }
        let record =
            match finish_shared_learning_round_state(state, &mut self.compact, &mut self.rbf) {
                Ok(record) => record,
                Err(state) => {
                    discard_shared_learning_round_state(state, &mut self.compact, &mut self.rbf);
                    return self.pause(AdaptiveLearningFailure::InternalInvariant(
                        "completed shared round did not produce a record".to_owned(),
                    ));
                }
            };
        self.commit_round(record, new_ratings);
        Ok(())
    }

    pub fn into_completed(
        self,
    ) -> std::result::Result<CompletedAdaptiveLearning, Box<AdaptiveLearningCoordinator>> {
        if !matches!(self.state, LearningState::Complete) {
            return Err(Box::new(self));
        }
        Ok(CompletedAdaptiveLearning {
            compact: self.compact,
            rbf: self.rbf,
            vector_cache: self.vector_cache,
            b16: self.b16,
            presentation_ledger: self.presentation_ledger,
            ratings: self.ratings,
            language_totals: self.language_totals,
            source_wave_records: self.source_wave_records,
            round_records: self.round_records,
        })
    }

    fn learning_disallowed_event_ids(&self) -> BTreeSet<EventId> {
        self.presentation_ledger
            .iter()
            .filter_map(|(event_id, presentation)| {
                (!matches!(presentation, PriorPresentation::Rated { .. })).then_some(*event_id)
            })
            .collect()
    }

    fn verify_seed_vectors<O: CandidateOrderOracle>(&mut self, oracle: &mut O) -> Result<()> {
        if self.seed_vectors_verified {
            return Ok(());
        }
        let seed_event_ids = self.compact.evidence_event_ids().to_vec();
        let seed_response =
            oracle.vectors_for_notes(&seed_event_ids, self.compact.representation_version())?;
        for ((event_id, evidence), stored) in seed_event_ids
            .iter()
            .zip(self.compact.evidence_vectors())
            .zip(&seed_response.vectors)
        {
            if stored.event_id != *event_id || !same_vector_bits(&stored.vector, evidence.vector())
            {
                return self.pause(AdaptiveLearningFailure::SeedVectorMismatch {
                    event_id: *event_id,
                });
            }
        }
        self.vector_cache.insert_verified_vectors(
            seed_response,
            &seed_event_ids,
            self.compact.evidence_identity().vector_dimensions(),
        )?;
        self.seed_vectors_verified = true;
        Ok(())
    }

    fn prefetch_positive_sources<O: CandidateOrderOracle>(
        &mut self,
        oracle: &mut O,
    ) -> Result<usize> {
        let source_event_ids = self
            .compact
            .evidence_event_ids()
            .iter()
            .copied()
            .zip(self.compact.evidence_ratings().iter().copied())
            .chain(
                self.rbf
                    .evidence_event_ids()
                    .iter()
                    .copied()
                    .zip(self.rbf.evidence_ratings().iter().copied()),
            )
            .filter_map(|(event_id, rating)| (rating.target() > 0.0).then_some(event_id))
            .collect::<BTreeSet<_>>()
            .into_iter()
            .collect::<Vec<_>>();
        let requests = source_event_ids
            .iter()
            .map(|event_id| SimilarNotesRequest {
                note_id: *event_id,
                candidate_depth: CANDIDATE_DEPTH,
            })
            .collect::<Vec<_>>();
        let wave = oracle.similar_notes_wave(&requests, self.compact.representation_version())?;
        if wave.responses.len() != requests.len() {
            return Err(AdaptiveLearningError::Oracle(SnapshotError::Invariant(
                format!(
                    "combined source wave returned {} responses for {} requests",
                    wave.responses.len(),
                    requests.len()
                ),
            )));
        }
        self.source_wave_records.push(LearningSourceWaveRecord {
            round: self.round_records.len() + 1,
            source_event_ids,
            metrics: wave.metrics,
            accepted: false,
        });
        Ok(self.source_wave_records.len() - 1)
    }

    fn record_presentations(&mut self, outcomes: &[EventLanguageOutcome]) {
        for outcome in outcomes {
            let presentation = match outcome.eligibility() {
                LanguageEligibility::Eligible => PriorPresentation::EligibleUnrated,
                LanguageEligibility::WrongLanguage => PriorPresentation::WrongLanguage,
            };
            let previous = self
                .presentation_ledger
                .insert(outcome.event_id(), presentation);
            debug_assert!(previous.is_none());
            self.language_totals.record(outcome.eligibility());
        }
    }

    fn prepare_pending_ratings(&mut self) -> Result<()> {
        let resolver = self.take_resolver();
        let quota = match resolver.into_result() {
            Ok(quota) => quota,
            Err(QuotaResolutionError::ResolutionFailed(failed)) => {
                return self.pause(AdaptiveLearningFailure::QuotaResolution(
                    failed.failure().clone(),
                ));
            }
            Err(error) => {
                return self.pause(AdaptiveLearningFailure::InternalInvariant(
                    error.to_string(),
                ));
            }
        };

        if self.round_records.len() + 1 == LEARNING_ROUNDS && !self.language_totals.within_ceiling()
        {
            return self.pause(AdaptiveLearningFailure::FinalLanguageCeiling {
                wrong_language: self.language_totals.wrong_language_presentations,
                unique_presentations: self.language_totals.unique_presentations(),
            });
        }
        for route in quota.stored_rating_reuse_routes() {
            if !self.ratings.contains_key(&route.event_id()) {
                return self.pause(AdaptiveLearningFailure::InternalInvariant(format!(
                    "stored route for {:?} has no retained rating",
                    route.event_id()
                )));
            }
        }
        let pending =
            match prepare_shared_learning_round_state(quota, &mut self.compact, &mut self.rbf) {
                Ok(pending) => pending,
                Err(error) => {
                    return self.pause(AdaptiveLearningFailure::SharedRound(error.to_string()));
                }
            };
        let has_no_new_ratings = pending.new_rating_event_ids().is_empty();
        self.state = LearningState::AwaitingRatings(pending);
        if has_no_new_ratings {
            self.submit_ratings(Vec::new())
        } else {
            Ok(())
        }
    }

    fn commit_round(
        &mut self,
        record: SharedLearningRoundRecord,
        new_ratings: BTreeMap<EventId, BatchRating>,
    ) {
        for (event_id, presentation) in record.presentation_ledger_entries() {
            self.presentation_ledger
                .insert(*event_id, presentation.clone());
        }
        for route in record.quota_metadata().stored_rating_reuse_routes() {
            match self.presentation_ledger.get_mut(&route.event_id()) {
                Some(PriorPresentation::Rated { selected_by }) => {
                    selected_by.insert(route.personalizer());
                }
                _ => debug_assert!(false, "validated stored route lost its rated ledger entry"),
            }
        }
        for (event_id, rating) in new_ratings {
            self.ratings.insert(event_id, rating.rating());
        }
        self.round_records.push(record);
        self.state = if self.round_records.len() == LEARNING_ROUNDS {
            LearningState::Complete
        } else {
            LearningState::Ready
        };
    }

    fn take_resolver(&mut self) -> Box<SharedQuotaResolver> {
        match std::mem::replace(&mut self.state, LearningState::Ready) {
            LearningState::Resolving(resolver) => resolver,
            _ => unreachable!("resolver was checked before transition"),
        }
    }

    fn take_pending_ratings(&mut self) -> Box<SharedLearningRoundState> {
        match std::mem::replace(&mut self.state, LearningState::Ready) {
            LearningState::AwaitingRatings(state) => state,
            _ => unreachable!("pending ratings were checked before transition"),
        }
    }

    fn invalid_progress(&self, expected: AdaptiveLearningProgress) -> AdaptiveLearningError {
        AdaptiveLearningError::InvalidProgress {
            expected,
            actual: self.progress(),
        }
    }

    fn pause<T>(&mut self, reason: AdaptiveLearningFailure) -> Result<T> {
        self.state = LearningState::Paused(reason.clone());
        Err(AdaptiveLearningError::PhasePaused(reason))
    }
}

pub struct CompletedAdaptiveLearning {
    compact: CompactLearningController,
    rbf: RbfLearningController,
    vector_cache: CandidateVectorCache,
    b16: B16Boundary,
    presentation_ledger: BTreeMap<EventId, PriorPresentation>,
    ratings: BTreeMap<EventId, GladnessRating>,
    language_totals: LearningLanguageTotals,
    source_wave_records: Vec<LearningSourceWaveRecord>,
    round_records: Vec<SharedLearningRoundRecord>,
}

impl CompletedAdaptiveLearning {
    pub fn compact_controller(&self) -> &CompactLearningController {
        &self.compact
    }

    pub fn rbf_controller(&self) -> &RbfLearningController {
        &self.rbf
    }

    pub fn b16(&self) -> &B16Boundary {
        &self.b16
    }

    pub fn cached_vector_count(&self) -> usize {
        self.vector_cache.vector_count()
    }

    pub fn presentation_ledger(&self) -> &BTreeMap<EventId, PriorPresentation> {
        &self.presentation_ledger
    }

    pub fn ratings(&self) -> &BTreeMap<EventId, GladnessRating> {
        &self.ratings
    }

    pub const fn language_totals(&self) -> LearningLanguageTotals {
        self.language_totals
    }

    pub fn round_records(&self) -> &[SharedLearningRoundRecord] {
        &self.round_records
    }

    pub fn source_wave_records(&self) -> &[LearningSourceWaveRecord] {
        &self.source_wave_records
    }
}

fn validate_new_ratings(
    required_event_ids: &[EventId],
    ratings: Vec<BatchRating>,
) -> Result<BTreeMap<EventId, BatchRating>> {
    let required = required_event_ids.iter().copied().collect::<BTreeSet<_>>();
    let mut validated = BTreeMap::new();
    for rating in ratings {
        if !required.contains(&rating.event_id()) {
            return Err(AdaptiveLearningError::UnexpectedRating {
                event_id: rating.event_id(),
            });
        }
        if validated.insert(rating.event_id(), rating).is_some() {
            return Err(AdaptiveLearningError::DuplicateRating {
                event_id: rating.event_id(),
            });
        }
    }
    if let Some(event_id) = required_event_ids
        .iter()
        .find(|event_id| !validated.contains_key(*event_id))
    {
        return Err(AdaptiveLearningError::MissingRating {
            event_id: *event_id,
        });
    }
    Ok(validated)
}

fn same_vector_bits(left: &[f32], right: &[f32]) -> bool {
    left.len() == right.len()
        && left
            .iter()
            .zip(right)
            .all(|(left, right)| left.to_bits() == right.to_bits())
}
