//! Shared language-eligibility and quota resolution for two frozen orders.

use std::collections::{BTreeMap, BTreeSet, VecDeque};

use thiserror::Error;

use crate::candidate_order::{
    ActivePersonalizerParameters, CandidateOrderPhase, FrozenCandidateOrder,
};
use crate::personalizer_learning::{BatchCandidate, CandidateBatch};
use crate::representation::EventId;

pub type Result<T> = std::result::Result<T, QuotaResolutionError>;

#[derive(
    Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd, serde::Deserialize, serde::Serialize,
)]
#[serde(rename_all = "snake_case")]
pub enum PersonalizerId {
    Compact,
    Rbf,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, serde::Serialize)]
#[serde(rename_all = "snake_case")]
pub enum LanguageEligibility {
    Eligible,
    WrongLanguage,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, serde::Serialize)]
pub struct EventLanguageOutcome {
    event_id: EventId,
    eligibility: LanguageEligibility,
}

impl EventLanguageOutcome {
    pub const fn new(event_id: EventId, eligibility: LanguageEligibility) -> Self {
        Self {
            event_id,
            eligibility,
        }
    }

    pub const fn event_id(self) -> EventId {
        self.event_id
    }

    pub const fn eligibility(self) -> LanguageEligibility {
        self.eligibility
    }
}

#[derive(Clone, Debug, Eq, PartialEq, serde::Deserialize, serde::Serialize)]
#[serde(rename_all = "snake_case", tag = "kind")]
pub enum PriorPresentation {
    Rated {
        selected_by: BTreeSet<PersonalizerId>,
    },
    EligibleUnrated,
    WrongLanguage,
}

impl PriorPresentation {
    pub fn rated_by(selected_by: impl IntoIterator<Item = PersonalizerId>) -> Result<Self> {
        let selected_by = selected_by.into_iter().collect::<BTreeSet<_>>();
        if selected_by.is_empty() {
            return Err(QuotaResolutionError::RatedPresentationWithoutSelector);
        }
        Ok(Self::Rated { selected_by })
    }
}

#[derive(Clone, Debug, Default, Eq, PartialEq)]
pub struct PresentationLedgerSnapshot {
    entries: BTreeMap<EventId, PriorPresentation>,
}

impl PresentationLedgerSnapshot {
    pub const fn empty() -> Self {
        Self {
            entries: BTreeMap::new(),
        }
    }

    pub fn new(entries: BTreeMap<EventId, PriorPresentation>) -> Result<Self> {
        for presentation in entries.values() {
            if let PriorPresentation::Rated { selected_by } = presentation
                && selected_by.is_empty()
            {
                return Err(QuotaResolutionError::RatedPresentationWithoutSelector);
            }
        }
        Ok(Self { entries })
    }

    fn entry(&self, event_id: EventId) -> Option<&PriorPresentation> {
        self.entries.get(&event_id)
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum QuotaResolutionProgress {
    AwaitingLanguage,
    Complete,
    Failed,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct PresentationWave {
    wave_id: u64,
    event_ids: Vec<EventId>,
}

impl PresentationWave {
    pub const fn wave_id(&self) -> u64 {
        self.wave_id
    }

    pub fn event_ids(&self) -> &[EventId] {
        &self.event_ids
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq, serde::Serialize)]
pub struct LanguageDelta {
    eligible_presentations: usize,
    wrong_language_presentations: usize,
}

impl LanguageDelta {
    pub const fn eligible_presentations(self) -> usize {
        self.eligible_presentations
    }

    pub const fn wrong_language_presentations(self) -> usize {
        self.wrong_language_presentations
    }

    pub const fn unique_presentations(self) -> usize {
        self.eligible_presentations + self.wrong_language_presentations
    }
}

#[derive(Clone, Debug, Default, Eq, PartialEq, serde::Serialize)]
pub struct PresentationLedgerDelta {
    outcomes: Vec<EventLanguageOutcome>,
}

impl PresentationLedgerDelta {
    pub fn outcomes(&self) -> &[EventLanguageOutcome] {
        &self.outcomes
    }

    pub fn event_ids(&self) -> impl ExactSizeIterator<Item = EventId> + '_ {
        self.outcomes.iter().map(|outcome| outcome.event_id())
    }

    pub fn len(&self) -> usize {
        self.outcomes.len()
    }

    pub fn is_empty(&self) -> bool {
        self.outcomes.is_empty()
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, serde::Serialize)]
#[serde(rename_all = "snake_case", tag = "kind")]
pub enum ClaimOrigin {
    Primary,
    ReservePromotion {
        replaced_event_id: EventId,
        replaced_order_index: usize,
    },
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, serde::Serialize)]
#[serde(rename_all = "snake_case", tag = "kind")]
pub enum ChoiceRatingSource {
    NewRating { first_presentation_wave: u64 },
    StoredRating,
}

#[derive(Clone, Debug, Eq, PartialEq, serde::Serialize)]
#[serde(rename_all = "snake_case", tag = "kind")]
pub enum QuotaAuditEvent {
    Claimed {
        personalizer: PersonalizerId,
        event_id: EventId,
        order_index: usize,
        origin: ClaimOrigin,
    },
    PresentationWaveFrozen {
        wave_id: u64,
        event_ids: Vec<EventId>,
    },
    LanguageRecorded {
        wave_id: u64,
        event_id: EventId,
        eligibility: LanguageEligibility,
    },
    Accepted {
        personalizer: PersonalizerId,
        event_id: EventId,
        order_index: usize,
        rating_source: ChoiceRatingSource,
    },
    WrongLanguageRejected {
        personalizer: PersonalizerId,
        event_id: EventId,
        order_index: usize,
    },
    Failed(QuotaResolutionFailure),
}

#[derive(Clone, Debug, Eq, PartialEq, serde::Serialize)]
pub struct StoredRatingReuseRoute {
    event_id: EventId,
    personalizer: PersonalizerId,
}

impl StoredRatingReuseRoute {
    pub const fn event_id(&self) -> EventId {
        self.event_id
    }

    pub const fn personalizer(&self) -> PersonalizerId {
        self.personalizer
    }
}

#[derive(Clone, Debug, Eq, PartialEq, serde::Serialize)]
pub struct NewRatingRoute {
    event_id: EventId,
    selected_by: BTreeSet<PersonalizerId>,
}

impl NewRatingRoute {
    pub const fn event_id(&self) -> EventId {
        self.event_id
    }

    pub fn selected_by(&self) -> &BTreeSet<PersonalizerId> {
        &self.selected_by
    }
}

#[derive(Clone, Debug, PartialEq, serde::Serialize)]
pub struct QuotaResolutionMetadata {
    presentation_ledger_delta: PresentationLedgerDelta,
    stored_rating_reuse_routes: Vec<StoredRatingReuseRoute>,
    new_rating_routes: Vec<NewRatingRoute>,
    language_delta: LanguageDelta,
    audit: Vec<QuotaAuditEvent>,
}

impl QuotaResolutionMetadata {
    pub fn presentation_ledger_delta(&self) -> &PresentationLedgerDelta {
        &self.presentation_ledger_delta
    }

    pub fn stored_rating_reuse_routes(&self) -> &[StoredRatingReuseRoute] {
        &self.stored_rating_reuse_routes
    }

    pub fn new_rating_routes(&self) -> &[NewRatingRoute] {
        &self.new_rating_routes
    }

    pub const fn language_delta(&self) -> LanguageDelta {
        self.language_delta
    }

    pub fn audit(&self) -> &[QuotaAuditEvent] {
        &self.audit
    }
}

#[derive(Debug, PartialEq)]
pub struct ResolvedPersonalizerQuota {
    personalizer: PersonalizerId,
    order: FrozenCandidateOrder,
    batch: CandidateBatch,
}

impl ResolvedPersonalizerQuota {
    pub const fn personalizer(&self) -> PersonalizerId {
        self.personalizer
    }

    pub fn order(&self) -> &FrozenCandidateOrder {
        &self.order
    }

    pub fn batch(&self) -> &CandidateBatch {
        &self.batch
    }

    pub fn into_parts(self) -> (FrozenCandidateOrder, CandidateBatch) {
        (self.order, self.batch)
    }
}

#[derive(Debug, PartialEq)]
pub struct ResolvedQuota {
    compact: ResolvedPersonalizerQuota,
    rbf: ResolvedPersonalizerQuota,
    metadata: QuotaResolutionMetadata,
}

impl ResolvedQuota {
    pub fn compact(&self) -> &ResolvedPersonalizerQuota {
        &self.compact
    }

    pub fn rbf(&self) -> &ResolvedPersonalizerQuota {
        &self.rbf
    }

    pub fn compact_order(&self) -> &FrozenCandidateOrder {
        self.compact.order()
    }

    pub fn rbf_order(&self) -> &FrozenCandidateOrder {
        self.rbf.order()
    }

    pub fn compact_batch(&self) -> &CandidateBatch {
        self.compact.batch()
    }

    pub fn rbf_batch(&self) -> &CandidateBatch {
        self.rbf.batch()
    }

    pub fn presentation_ledger_delta(&self) -> &PresentationLedgerDelta {
        self.metadata.presentation_ledger_delta()
    }

    pub fn stored_rating_reuse_routes(&self) -> &[StoredRatingReuseRoute] {
        self.metadata.stored_rating_reuse_routes()
    }

    pub fn new_rating_routes(&self) -> &[NewRatingRoute] {
        self.metadata.new_rating_routes()
    }

    pub const fn language_delta(&self) -> LanguageDelta {
        self.metadata.language_delta()
    }

    pub fn audit(&self) -> &[QuotaAuditEvent] {
        self.metadata.audit()
    }

    pub fn into_parts(
        self,
    ) -> (
        ResolvedPersonalizerQuota,
        ResolvedPersonalizerQuota,
        QuotaResolutionMetadata,
    ) {
        (self.compact, self.rbf, self.metadata)
    }
}

#[derive(Clone, Debug, Eq, PartialEq, serde::Serialize)]
#[serde(rename_all = "snake_case", tag = "kind")]
pub enum QuotaResolutionFailure {
    ReserveExhausted {
        personalizer: PersonalizerId,
        accepted_choices: usize,
        required_choices: usize,
    },
    InternalInvariant(String),
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct FailedQuotaResolution {
    failure: QuotaResolutionFailure,
    presentation_ledger_delta: PresentationLedgerDelta,
    language_delta: LanguageDelta,
    audit: Vec<QuotaAuditEvent>,
}

impl FailedQuotaResolution {
    pub const fn failure(&self) -> &QuotaResolutionFailure {
        &self.failure
    }

    pub const fn presentation_ledger_delta(&self) -> &PresentationLedgerDelta {
        &self.presentation_ledger_delta
    }

    pub const fn language_delta(&self) -> LanguageDelta {
        self.language_delta
    }

    pub fn audit(&self) -> &[QuotaAuditEvent] {
        &self.audit
    }
}

#[derive(Debug, Error, PartialEq)]
pub enum QuotaResolutionError {
    #[error("compact input does not contain compact-personalizer parameters")]
    CompactRoleMismatch,
    #[error("RBF input does not contain RBF-personalizer parameters")]
    RbfRoleMismatch,
    #[error("candidate-order phases differ: compact={compact:?}, RBF={rbf:?}")]
    PhaseMismatch {
        compact: CandidateOrderPhase,
        rbf: CandidateOrderPhase,
    },
    #[error("candidate-order representation versions differ: compact={compact}, RBF={rbf}")]
    RepresentationVersionMismatch { compact: String, rbf: String },
    #[error("candidate-order B16 boundaries differ")]
    BoundaryMismatch,
    #[error("candidate vector for event {event_id:?} has dimension {actual}; expected {expected}")]
    VectorDimensionMismatch {
        event_id: EventId,
        expected: usize,
        actual: usize,
    },
    #[error("shared event {event_id:?} has different vectors in the two orders")]
    SharedVectorMismatch { event_id: EventId },
    #[error("a prior rated presentation has no selecting personalizer")]
    RatedPresentationWithoutSelector,
    #[error("{personalizer:?} order contains its own previously rated event {event_id:?}")]
    OwnPriorRatingInLearningOrder {
        personalizer: PersonalizerId,
        event_id: EventId,
    },
    #[error("learning order contains prior wrong-language event {event_id:?}")]
    PriorWrongLanguageInLearningOrder { event_id: EventId },
    #[error("learning order contains prior eligible but unrated event {event_id:?}")]
    PriorUnratedPresentationInLearningOrder { event_id: EventId },
    #[error("final order contains previously presented event {event_id:?}")]
    FinalOrderContainsPriorPresentation { event_id: EventId },
    #[error("there is no pending language wave")]
    NoPendingWave,
    #[error("language outcomes are for wave {actual}; expected wave {expected}")]
    WaveIdMismatch { expected: u64, actual: u64 },
    #[error("language outcomes repeat event {event_id:?}")]
    DuplicateLanguageOutcome { event_id: EventId },
    #[error("language outcome includes unexpected event {event_id:?}")]
    UnexpectedLanguageOutcome { event_id: EventId },
    #[error("language outcome is missing event {event_id:?}")]
    MissingLanguageOutcome { event_id: EventId },
    #[error("quota resolution failed: {0:?}")]
    ResolutionFailed(FailedQuotaResolution),
    #[error("quota resolution is not complete")]
    NotComplete,
}

#[derive(Clone)]
struct Claim {
    personalizer: PersonalizerId,
    order_index: usize,
    event_id: EventId,
}

#[derive(Clone, Copy)]
struct CurrentPresentation {
    eligibility: LanguageEligibility,
    first_wave_id: u64,
}

struct PendingWaveState {
    wave: PresentationWave,
    claims_by_event: BTreeMap<EventId, Vec<Claim>>,
}

struct AlgorithmState {
    personalizer: PersonalizerId,
    order: FrozenCandidateOrder,
    quota: usize,
    next_reserve_index: usize,
    accepted: BTreeMap<usize, ChoiceRatingSource>,
}

impl AlgorithmState {
    fn new(personalizer: PersonalizerId, order: FrozenCandidateOrder) -> Self {
        let quota = order.attempt().phase().primary_count();
        Self {
            personalizer,
            order,
            quota,
            next_reserve_index: quota,
            accepted: BTreeMap::new(),
        }
    }

    fn claim(&self, order_index: usize) -> Claim {
        Claim {
            personalizer: self.personalizer,
            order_index,
            event_id: self.order.accepted()[order_index].event_id(),
        }
    }
}

pub struct SharedQuotaResolver {
    compact: AlgorithmState,
    rbf: AlgorithmState,
    prior_ledger: PresentationLedgerSnapshot,
    current_presentations: BTreeMap<EventId, CurrentPresentation>,
    pending: Option<PendingWaveState>,
    complete: bool,
    failure: Option<QuotaResolutionFailure>,
    next_wave_id: u64,
    presentation_ledger_delta: PresentationLedgerDelta,
    language_delta: LanguageDelta,
    audit: Vec<QuotaAuditEvent>,
}

impl SharedQuotaResolver {
    pub fn new(
        compact_order: FrozenCandidateOrder,
        rbf_order: FrozenCandidateOrder,
        prior_ledger: PresentationLedgerSnapshot,
    ) -> Result<Self> {
        validate_inputs(&compact_order, &rbf_order, &prior_ledger)?;

        let mut resolver = Self {
            compact: AlgorithmState::new(PersonalizerId::Compact, compact_order),
            rbf: AlgorithmState::new(PersonalizerId::Rbf, rbf_order),
            prior_ledger,
            current_presentations: BTreeMap::new(),
            pending: None,
            complete: false,
            failure: None,
            next_wave_id: 1,
            presentation_ledger_delta: PresentationLedgerDelta::default(),
            language_delta: LanguageDelta::default(),
            audit: Vec::new(),
        };

        let mut initial = Vec::with_capacity(resolver.compact.quota + resolver.rbf.quota);
        for personalizer in [PersonalizerId::Compact, PersonalizerId::Rbf] {
            let quota = resolver.algorithm(personalizer).quota;
            for order_index in 0..quota {
                initial.push(resolver.record_claim(
                    personalizer,
                    order_index,
                    ClaimOrigin::Primary,
                ));
            }
        }
        resolver.process_claims(initial);
        Ok(resolver)
    }

    pub fn progress(&self) -> QuotaResolutionProgress {
        if self.complete {
            QuotaResolutionProgress::Complete
        } else if self.failure.is_some() {
            QuotaResolutionProgress::Failed
        } else {
            QuotaResolutionProgress::AwaitingLanguage
        }
    }

    pub fn pending_wave(&self) -> Option<&PresentationWave> {
        self.pending.as_ref().map(|pending| &pending.wave)
    }

    pub fn failure(&self) -> Option<&QuotaResolutionFailure> {
        self.failure.as_ref()
    }

    pub const fn presentation_ledger_delta(&self) -> &PresentationLedgerDelta {
        &self.presentation_ledger_delta
    }

    pub const fn language_delta(&self) -> LanguageDelta {
        self.language_delta
    }

    pub fn audit(&self) -> &[QuotaAuditEvent] {
        &self.audit
    }

    pub fn submit_language_outcomes(
        &mut self,
        wave_id: u64,
        outcomes: Vec<EventLanguageOutcome>,
    ) -> Result<()> {
        let pending = self
            .pending
            .as_ref()
            .ok_or(QuotaResolutionError::NoPendingWave)?;
        if pending.wave.wave_id != wave_id {
            return Err(QuotaResolutionError::WaveIdMismatch {
                expected: pending.wave.wave_id,
                actual: wave_id,
            });
        }

        let expected = pending
            .wave
            .event_ids
            .iter()
            .copied()
            .collect::<BTreeSet<_>>();
        let mut validated = BTreeMap::new();
        for outcome in outcomes {
            if !expected.contains(&outcome.event_id) {
                return Err(QuotaResolutionError::UnexpectedLanguageOutcome {
                    event_id: outcome.event_id,
                });
            }
            if validated
                .insert(outcome.event_id, outcome.eligibility)
                .is_some()
            {
                return Err(QuotaResolutionError::DuplicateLanguageOutcome {
                    event_id: outcome.event_id,
                });
            }
        }
        if let Some(event_id) = expected
            .iter()
            .find(|event_id| !validated.contains_key(*event_id))
        {
            return Err(QuotaResolutionError::MissingLanguageOutcome {
                event_id: *event_id,
            });
        }

        let pending = self
            .pending
            .take()
            .ok_or(QuotaResolutionError::NoPendingWave)?;
        for event_id in &pending.wave.event_ids {
            let eligibility = validated[event_id];
            self.current_presentations.insert(
                *event_id,
                CurrentPresentation {
                    eligibility,
                    first_wave_id: pending.wave.wave_id,
                },
            );
            self.presentation_ledger_delta
                .outcomes
                .push(EventLanguageOutcome::new(*event_id, eligibility));
            match eligibility {
                LanguageEligibility::Eligible => {
                    self.language_delta.eligible_presentations += 1;
                }
                LanguageEligibility::WrongLanguage => {
                    self.language_delta.wrong_language_presentations += 1;
                }
            }
            self.audit.push(QuotaAuditEvent::LanguageRecorded {
                wave_id: pending.wave.wave_id,
                event_id: *event_id,
                eligibility,
            });
        }

        let mut claims = Vec::new();
        for event_id in &pending.wave.event_ids {
            let Some(event_claims) = pending.claims_by_event.get(event_id) else {
                self.fail(QuotaResolutionFailure::InternalInvariant(format!(
                    "pending event {event_id:?} has no claims"
                )));
                return Ok(());
            };
            claims.extend(event_claims.iter().cloned());
        }
        self.process_claims(claims);
        Ok(())
    }

    pub fn into_result(mut self) -> Result<ResolvedQuota> {
        if self.complete {
            let batches = build_batch(&self.compact)
                .and_then(|compact| build_batch(&self.rbf).map(|rbf| (compact, rbf)));
            let (compact_batch, rbf_batch) = match batches {
                Ok(batches) => batches,
                Err(message) => {
                    let failure = QuotaResolutionFailure::InternalInvariant(message);
                    self.audit.push(QuotaAuditEvent::Failed(failure.clone()));
                    return Err(QuotaResolutionError::ResolutionFailed(
                        FailedQuotaResolution {
                            failure,
                            presentation_ledger_delta: self.presentation_ledger_delta,
                            language_delta: self.language_delta,
                            audit: self.audit,
                        },
                    ));
                }
            };
            let (stored_rating_reuse_routes, new_rating_routes) =
                build_rating_routes(&self.compact, &self.rbf);
            return Ok(ResolvedQuota {
                compact: ResolvedPersonalizerQuota {
                    personalizer: PersonalizerId::Compact,
                    order: self.compact.order,
                    batch: compact_batch,
                },
                rbf: ResolvedPersonalizerQuota {
                    personalizer: PersonalizerId::Rbf,
                    order: self.rbf.order,
                    batch: rbf_batch,
                },
                metadata: QuotaResolutionMetadata {
                    presentation_ledger_delta: self.presentation_ledger_delta,
                    stored_rating_reuse_routes,
                    new_rating_routes,
                    language_delta: self.language_delta,
                    audit: self.audit,
                },
            });
        }
        if let Some(failure) = self.failure.take() {
            return Err(QuotaResolutionError::ResolutionFailed(
                FailedQuotaResolution {
                    failure,
                    presentation_ledger_delta: self.presentation_ledger_delta,
                    language_delta: self.language_delta,
                    audit: self.audit,
                },
            ));
        }
        Err(QuotaResolutionError::NotComplete)
    }

    fn algorithm(&self, personalizer: PersonalizerId) -> &AlgorithmState {
        match personalizer {
            PersonalizerId::Compact => &self.compact,
            PersonalizerId::Rbf => &self.rbf,
        }
    }

    fn algorithm_mut(&mut self, personalizer: PersonalizerId) -> &mut AlgorithmState {
        match personalizer {
            PersonalizerId::Compact => &mut self.compact,
            PersonalizerId::Rbf => &mut self.rbf,
        }
    }

    fn record_claim(
        &mut self,
        personalizer: PersonalizerId,
        order_index: usize,
        origin: ClaimOrigin,
    ) -> Claim {
        let claim = self.algorithm(personalizer).claim(order_index);
        self.audit.push(QuotaAuditEvent::Claimed {
            personalizer,
            event_id: claim.event_id,
            order_index,
            origin,
        });
        claim
    }

    fn process_claims(&mut self, claims: Vec<Claim>) {
        if self.failure.is_some() || self.complete {
            return;
        }

        let mut queue = VecDeque::from(claims);
        let mut pending_event_ids = Vec::new();
        let mut pending_claims = BTreeMap::<EventId, Vec<Claim>>::new();
        let mut exhausted_personalizer = None;

        while let Some(claim) = queue.pop_front() {
            let prior = self.prior_ledger.entry(claim.event_id).cloned();
            if let Some(PriorPresentation::Rated { .. }) = prior {
                self.accept_claim(claim, ChoiceRatingSource::StoredRating);
                continue;
            }

            if let Some(presentation) = self.current_presentations.get(&claim.event_id).copied() {
                match presentation.eligibility {
                    LanguageEligibility::Eligible => self.accept_claim(
                        claim,
                        ChoiceRatingSource::NewRating {
                            first_presentation_wave: presentation.first_wave_id,
                        },
                    ),
                    LanguageEligibility::WrongLanguage => {
                        if exhausted_personalizer.is_some() {
                            self.record_wrong_language_rejection(&claim);
                        } else {
                            match self.reject_and_promote(claim) {
                                Ok(promotion) => queue.push_back(promotion),
                                Err(personalizer) => {
                                    exhausted_personalizer = Some(personalizer);
                                }
                            }
                        }
                    }
                }
                if self.failure.is_some() {
                    break;
                }
                continue;
            }

            if !pending_claims.contains_key(&claim.event_id) {
                pending_event_ids.push(claim.event_id);
            }
            pending_claims
                .entry(claim.event_id)
                .or_default()
                .push(claim);
        }

        if self.failure.is_some() {
            return;
        }
        if let Some(personalizer) = exhausted_personalizer {
            let state = self.algorithm(personalizer);
            self.fail(QuotaResolutionFailure::ReserveExhausted {
                personalizer,
                accepted_choices: state.accepted.len(),
                required_choices: state.quota,
            });
            return;
        }
        if !pending_event_ids.is_empty() {
            let wave_id = self.next_wave_id;
            let Some(next_wave_id) = self.next_wave_id.checked_add(1) else {
                self.fail(QuotaResolutionFailure::InternalInvariant(
                    "presentation wave identifier overflowed".to_owned(),
                ));
                return;
            };
            self.next_wave_id = next_wave_id;
            let wave = PresentationWave {
                wave_id,
                event_ids: pending_event_ids,
            };
            self.audit.push(QuotaAuditEvent::PresentationWaveFrozen {
                wave_id,
                event_ids: wave.event_ids.clone(),
            });
            self.pending = Some(PendingWaveState {
                wave,
                claims_by_event: pending_claims,
            });
            return;
        }

        if self.compact.accepted.len() == self.compact.quota
            && self.rbf.accepted.len() == self.rbf.quota
        {
            self.complete = true;
        } else {
            self.fail(QuotaResolutionFailure::InternalInvariant(
                "quota resolution stopped without a pending wave".to_owned(),
            ));
        }
    }

    fn accept_claim(&mut self, claim: Claim, rating_source: ChoiceRatingSource) {
        let accepted = &mut self.algorithm_mut(claim.personalizer).accepted;
        if accepted.insert(claim.order_index, rating_source).is_some() {
            self.fail(QuotaResolutionFailure::InternalInvariant(format!(
                "{:?} accepted order index {} twice",
                claim.personalizer, claim.order_index
            )));
            return;
        }
        self.audit.push(QuotaAuditEvent::Accepted {
            personalizer: claim.personalizer,
            event_id: claim.event_id,
            order_index: claim.order_index,
            rating_source,
        });
    }

    fn record_wrong_language_rejection(&mut self, claim: &Claim) {
        self.audit.push(QuotaAuditEvent::WrongLanguageRejected {
            personalizer: claim.personalizer,
            event_id: claim.event_id,
            order_index: claim.order_index,
        });
    }

    fn reject_and_promote(&mut self, claim: Claim) -> std::result::Result<Claim, PersonalizerId> {
        self.record_wrong_language_rejection(&claim);

        let state = self.algorithm_mut(claim.personalizer);
        if state.next_reserve_index >= state.order.accepted().len() {
            return Err(claim.personalizer);
        }
        let order_index = state.next_reserve_index;
        state.next_reserve_index += 1;
        Ok(self.record_claim(
            claim.personalizer,
            order_index,
            ClaimOrigin::ReservePromotion {
                replaced_event_id: claim.event_id,
                replaced_order_index: claim.order_index,
            },
        ))
    }

    fn fail(&mut self, failure: QuotaResolutionFailure) {
        if self.failure.is_none() {
            self.audit.push(QuotaAuditEvent::Failed(failure.clone()));
            self.failure = Some(failure);
        }
        self.pending = None;
        self.complete = false;
    }
}

fn validate_inputs(
    compact: &FrozenCandidateOrder,
    rbf: &FrozenCandidateOrder,
    ledger: &PresentationLedgerSnapshot,
) -> Result<()> {
    if !matches!(
        compact.attempt().active_parameters(),
        ActivePersonalizerParameters::Compact(_)
    ) {
        return Err(QuotaResolutionError::CompactRoleMismatch);
    }
    if !matches!(
        rbf.attempt().active_parameters(),
        ActivePersonalizerParameters::Rbf(_)
    ) {
        return Err(QuotaResolutionError::RbfRoleMismatch);
    }

    let compact_phase = compact.attempt().phase();
    let rbf_phase = rbf.attempt().phase();
    if compact_phase != rbf_phase {
        return Err(QuotaResolutionError::PhaseMismatch {
            compact: compact_phase,
            rbf: rbf_phase,
        });
    }
    let compact_version = compact.attempt().representation_version();
    let rbf_version = rbf.attempt().representation_version();
    if compact_version != rbf_version {
        return Err(QuotaResolutionError::RepresentationVersionMismatch {
            compact: compact_version.to_owned(),
            rbf: rbf_version.to_owned(),
        });
    }
    let compact_b16 = compact.attempt().b16();
    let rbf_b16 = rbf.attempt().b16();
    if compact_b16.representation_version() != rbf_b16.representation_version()
        || compact_b16.distance().to_bits() != rbf_b16.distance().to_bits()
    {
        return Err(QuotaResolutionError::BoundaryMismatch);
    }

    let dimension = compact.accepted()[0].vector().len();
    let rbf_dimension = rbf.accepted()[0].vector().len();
    if dimension != rbf_dimension {
        return Err(QuotaResolutionError::VectorDimensionMismatch {
            event_id: rbf.accepted()[0].event_id(),
            expected: dimension,
            actual: rbf_dimension,
        });
    }

    let compact_vectors = compact
        .accepted()
        .iter()
        .map(|candidate| (candidate.event_id(), candidate.vector()))
        .collect::<BTreeMap<_, _>>();
    for candidate in rbf.accepted() {
        if let Some(compact_vector) = compact_vectors.get(&candidate.event_id())
            && !same_vector_bits(compact_vector, candidate.vector())
        {
            return Err(QuotaResolutionError::SharedVectorMismatch {
                event_id: candidate.event_id(),
            });
        }
    }

    for (personalizer, order) in [
        (PersonalizerId::Compact, compact),
        (PersonalizerId::Rbf, rbf),
    ] {
        for candidate in order.accepted() {
            let Some(prior) = ledger.entry(candidate.event_id()) else {
                continue;
            };
            match compact_phase {
                CandidateOrderPhase::Final => {
                    return Err(QuotaResolutionError::FinalOrderContainsPriorPresentation {
                        event_id: candidate.event_id(),
                    });
                }
                CandidateOrderPhase::Learning => match prior {
                    PriorPresentation::WrongLanguage => {
                        return Err(QuotaResolutionError::PriorWrongLanguageInLearningOrder {
                            event_id: candidate.event_id(),
                        });
                    }
                    PriorPresentation::EligibleUnrated => {
                        return Err(
                            QuotaResolutionError::PriorUnratedPresentationInLearningOrder {
                                event_id: candidate.event_id(),
                            },
                        );
                    }
                    PriorPresentation::Rated { selected_by }
                        if selected_by.contains(&personalizer) =>
                    {
                        return Err(QuotaResolutionError::OwnPriorRatingInLearningOrder {
                            personalizer,
                            event_id: candidate.event_id(),
                        });
                    }
                    PriorPresentation::Rated { .. } => {}
                },
            }
        }
    }
    Ok(())
}

fn same_vector_bits(left: &[f32], right: &[f32]) -> bool {
    left.len() == right.len()
        && left
            .iter()
            .zip(right)
            .all(|(left, right)| left.to_bits() == right.to_bits())
}

fn build_rating_routes(
    compact: &AlgorithmState,
    rbf: &AlgorithmState,
) -> (Vec<StoredRatingReuseRoute>, Vec<NewRatingRoute>) {
    let mut stored_rating_reuse_routes = Vec::new();
    let mut new_routes = BTreeMap::<EventId, BTreeSet<PersonalizerId>>::new();

    for state in [compact, rbf] {
        for (&order_index, &rating_source) in &state.accepted {
            let event_id = state.order.accepted()[order_index].event_id();
            match rating_source {
                ChoiceRatingSource::StoredRating => {
                    stored_rating_reuse_routes.push(StoredRatingReuseRoute {
                        event_id,
                        personalizer: state.personalizer,
                    });
                }
                ChoiceRatingSource::NewRating {
                    first_presentation_wave: _,
                } => {
                    new_routes
                        .entry(event_id)
                        .or_default()
                        .insert(state.personalizer);
                }
            }
        }
    }

    let new_rating_routes = new_routes
        .into_iter()
        .map(|(event_id, selected_by)| NewRatingRoute {
            event_id,
            selected_by,
        })
        .collect();
    (stored_rating_reuse_routes, new_rating_routes)
}

fn build_batch(state: &AlgorithmState) -> std::result::Result<CandidateBatch, String> {
    if state.accepted.len() != state.quota {
        return Err(format!(
            "{:?} resolved {} choices instead of {}",
            state.personalizer,
            state.accepted.len(),
            state.quota
        ));
    }
    let candidates = state
        .accepted
        .keys()
        .map(|&order_index| {
            let candidate = &state.order.accepted()[order_index];
            BatchCandidate::new(candidate.event_id(), candidate.vector().to_vec())
                .map_err(|error| error.to_string())
        })
        .collect::<std::result::Result<Vec<_>, _>>()?;
    CandidateBatch::new(state.order.attempt().representation_version(), candidates)
        .map_err(|error| error.to_string())
}
