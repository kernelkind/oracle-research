//! One causally frozen adaptive-learning round shared by both personalizers.

use std::collections::{BTreeMap, BTreeSet};

use thiserror::Error;

use crate::candidate_order::{
    ActivePersonalizerParameters, CandidateOrderPhase, FrozenCandidateOrder,
};
use crate::personalizer_learning::{
    BatchRating, CompactLearningController, CompactRoundRecord, EvidenceIdentity,
    PersonalizerLearningError, PreparedCompactCompletion, PreparedRbfCompletion,
    RbfLearningController, RbfRoundRecord,
};
use crate::quota_resolution::{
    LanguageEligibility, PersonalizerId, PriorPresentation, QuotaResolutionMetadata,
    ResolvedPersonalizerQuota, ResolvedQuota,
};
use crate::representation::EventId;

const LEARNING_ROUNDS: usize = 10;

pub type Result<T> = std::result::Result<T, SharedLearningRoundError>;

#[derive(Debug, Error, PartialEq)]
pub enum SharedLearningRoundError {
    #[error("shared learning requires learning candidate orders; got {0:?}")]
    InvalidPhase(CandidateOrderPhase),
    #[error("resolved quota role is {actual:?}; expected {expected:?}")]
    RoleMismatch {
        expected: PersonalizerId,
        actual: PersonalizerId,
    },
    #[error("{personalizer:?} representation version does not match its frozen order")]
    RepresentationVersionMismatch { personalizer: PersonalizerId },
    #[error("{personalizer:?} evidence does not match its frozen order")]
    EvidenceIdentityMismatch { personalizer: PersonalizerId },
    #[error("{personalizer:?} active parameters do not match its frozen order")]
    ActiveParametersMismatch { personalizer: PersonalizerId },
    #[error("{personalizer:?} already has a pending learning batch")]
    BatchPending { personalizer: PersonalizerId },
    #[error("personalizers expect different rounds: Compact={compact_round}, RBF={rbf_round}")]
    RoundMismatch {
        compact_round: usize,
        rbf_round: usize,
    },
    #[error("all {LEARNING_ROUNDS} adaptive-learning rounds are already complete")]
    LearningRoundsComplete,
    #[error("failed to freeze {personalizer:?}: {source}")]
    FreezeFailed {
        personalizer: PersonalizerId,
        source: PersonalizerLearningError,
    },
    #[error("ratings repeat event {event_id:?}")]
    DuplicateRating { event_id: EventId },
    #[error("rating references event {event_id:?} outside the shared frozen round")]
    UnexpectedRating { event_id: EventId },
    #[error("shared frozen event {event_id:?} has no rating")]
    MissingRating { event_id: EventId },
    #[error("the shared learning round is already complete")]
    AlreadyComplete,
    #[error(
        "the shared learning round ended after an unexpected {personalizer:?} failure: {message}"
    )]
    TerminalFailure {
        personalizer: PersonalizerId,
        message: String,
    },
    #[error("shared-learning invariant failed: {0}")]
    InternalInvariant(String),
}

#[derive(Clone, Debug, PartialEq, serde::Serialize)]
#[serde(rename_all = "snake_case", tag = "kind")]
pub enum SharedLearningAuditEvent {
    BatchesFrozen {
        round: usize,
        compact_event_ids: Vec<EventId>,
        rbf_event_ids: Vec<EventId>,
    },
    RatingsApplied {
        ratings: Vec<BatchRating>,
    },
    RoundCompleted {
        round: usize,
        compact_evidence_after: EvidenceIdentity,
        rbf_evidence_after: EvidenceIdentity,
    },
    TerminalFailure {
        personalizer: PersonalizerId,
        message: String,
    },
}

#[derive(Clone, Debug, PartialEq)]
pub struct SharedLearningRoundRecord {
    round: usize,
    compact_order: FrozenCandidateOrder,
    rbf_order: FrozenCandidateOrder,
    quota_metadata: QuotaResolutionMetadata,
    compact_round: CompactRoundRecord,
    rbf_round: RbfRoundRecord,
    ratings: Vec<BatchRating>,
    presentation_ledger_entries: BTreeMap<EventId, PriorPresentation>,
    audit: Vec<SharedLearningAuditEvent>,
}

impl SharedLearningRoundRecord {
    pub const fn round(&self) -> usize {
        self.round
    }

    pub const fn compact_order(&self) -> &FrozenCandidateOrder {
        &self.compact_order
    }

    pub const fn rbf_order(&self) -> &FrozenCandidateOrder {
        &self.rbf_order
    }

    pub const fn quota_metadata(&self) -> &QuotaResolutionMetadata {
        &self.quota_metadata
    }

    pub const fn compact_round(&self) -> &CompactRoundRecord {
        &self.compact_round
    }

    pub const fn rbf_round(&self) -> &RbfRoundRecord {
        &self.rbf_round
    }

    pub fn ratings(&self) -> &[BatchRating] {
        &self.ratings
    }

    pub const fn presentation_ledger_entries(&self) -> &BTreeMap<EventId, PriorPresentation> {
        &self.presentation_ledger_entries
    }

    pub fn audit(&self) -> &[SharedLearningAuditEvent] {
        &self.audit
    }
}

struct PreparedRoutes {
    new_event_ids: Vec<EventId>,
    stored_event_ids: Vec<EventId>,
    required_event_ids: Vec<EventId>,
    presentation_ledger_entries: BTreeMap<EventId, PriorPresentation>,
}

/// The only state in which numeric feedback can complete a shared round.
///
/// The exclusive controller borrows prevent either personalizer from being
/// advanced separately after the two prediction batches have been frozen.
pub struct PendingSharedLearningRound<'a> {
    compact_controller: &'a mut CompactLearningController,
    rbf_controller: &'a mut RbfLearningController,
    state: Option<Box<SharedLearningRoundState>>,
}

pub(crate) struct SharedLearningRoundState {
    round: usize,
    compact_order: FrozenCandidateOrder,
    rbf_order: FrozenCandidateOrder,
    metadata: QuotaResolutionMetadata,
    routes: PreparedRoutes,
    compact_event_ids: Vec<EventId>,
    rbf_event_ids: Vec<EventId>,
    audit: Vec<SharedLearningAuditEvent>,
    terminal_failure: Option<(PersonalizerId, String)>,
    prepared_completion: Option<PreparedSharedRoundCompletion>,
}

struct PreparedSharedRoundCompletion {
    compact: PreparedCompactCompletion,
    rbf: PreparedRbfCompletion,
    ratings: Vec<BatchRating>,
}

impl SharedLearningRoundState {
    pub(crate) const fn round(&self) -> usize {
        self.round
    }

    pub(crate) fn new_rating_event_ids(&self) -> &[EventId] {
        &self.routes.new_event_ids
    }

    pub(crate) fn stored_rating_event_ids(&self) -> &[EventId] {
        &self.routes.stored_event_ids
    }

    pub(crate) fn required_rating_event_ids(&self) -> &[EventId] {
        &self.routes.required_event_ids
    }

    const fn is_complete(&self) -> bool {
        self.prepared_completion.is_some()
    }

    fn audit(&self) -> &[SharedLearningAuditEvent] {
        &self.audit
    }

    fn terminal_failure(&self) -> Option<(PersonalizerId, &str)> {
        self.terminal_failure
            .as_ref()
            .map(|(personalizer, message)| (*personalizer, message.as_str()))
    }

    fn record_terminal_failure(
        &mut self,
        personalizer: PersonalizerId,
        error: PersonalizerLearningError,
    ) -> SharedLearningRoundError {
        let message = error.to_string();
        self.audit.push(SharedLearningAuditEvent::TerminalFailure {
            personalizer,
            message: message.clone(),
        });
        self.terminal_failure = Some((personalizer, message.clone()));
        SharedLearningRoundError::TerminalFailure {
            personalizer,
            message,
        }
    }
}

impl PendingSharedLearningRound<'_> {
    fn state(&self) -> &SharedLearningRoundState {
        self.state
            .as_ref()
            .expect("pending shared round retains its state until it is consumed")
    }

    pub const fn round(&self) -> usize {
        self.state
            .as_ref()
            .expect("pending shared round retains its state until it is consumed")
            .round()
    }

    pub fn new_rating_event_ids(&self) -> &[EventId] {
        self.state().new_rating_event_ids()
    }

    pub fn stored_rating_event_ids(&self) -> &[EventId] {
        self.state().stored_rating_event_ids()
    }

    pub fn required_rating_event_ids(&self) -> &[EventId] {
        self.state().required_rating_event_ids()
    }

    pub const fn is_complete(&self) -> bool {
        self.state
            .as_ref()
            .expect("pending shared round retains its state until it is consumed")
            .is_complete()
    }

    pub fn audit(&self) -> &[SharedLearningAuditEvent] {
        self.state().audit()
    }

    pub fn terminal_failure(&self) -> Option<(PersonalizerId, &str)> {
        self.state().terminal_failure()
    }

    pub fn submit_ratings(&mut self, ratings: Vec<BatchRating>) -> Result<()> {
        submit_shared_learning_round_ratings(
            self.state
                .as_mut()
                .expect("pending shared round retains its state until it is consumed"),
            self.compact_controller,
            self.rbf_controller,
            ratings,
        )
    }

    pub fn finish(mut self) -> std::result::Result<SharedLearningRoundRecord, Box<Self>> {
        if !self.state().is_complete() {
            return Err(Box::new(self));
        }
        let state = self
            .state
            .take()
            .expect("completed pending shared round retains its state until it is consumed");
        finish_shared_learning_round_state(state, self.compact_controller, self.rbf_controller)
            .map_err(|state| {
                self.state = Some(state);
                Box::new(self)
            })
    }
}

impl Drop for PendingSharedLearningRound<'_> {
    fn drop(&mut self) {
        if let Some(state) = self.state.take() {
            discard_shared_learning_round_state(
                state,
                self.compact_controller,
                self.rbf_controller,
            );
        }
    }
}

pub fn begin_shared_learning_round<'a>(
    quota: ResolvedQuota,
    compact_controller: &'a mut CompactLearningController,
    rbf_controller: &'a mut RbfLearningController,
) -> Result<PendingSharedLearningRound<'a>> {
    let state = prepare_shared_learning_round_state(quota, compact_controller, rbf_controller)?;
    Ok(PendingSharedLearningRound {
        compact_controller,
        rbf_controller,
        state: Some(state),
    })
}

pub(crate) fn prepare_shared_learning_round_state(
    quota: ResolvedQuota,
    compact_controller: &mut CompactLearningController,
    rbf_controller: &mut RbfLearningController,
) -> Result<Box<SharedLearningRoundState>> {
    validate_bindings(&quota, compact_controller, rbf_controller)?;
    let round = compact_controller.history().len() + 1;
    let (compact, rbf, metadata) = quota.into_parts();
    let routes = prepare_routes(&metadata)?;
    let (compact_order, compact_batch) = compact.into_parts();
    let (rbf_order, rbf_batch) = rbf.into_parts();

    let rbf_prepared = rbf_controller.prepare_batch(rbf_batch).map_err(|source| {
        SharedLearningRoundError::FreezeFailed {
            personalizer: PersonalizerId::Rbf,
            source,
        }
    })?;
    let compact_prepared = compact_controller
        .prepare_batch(compact_batch)
        .map_err(|source| SharedLearningRoundError::FreezeFailed {
            personalizer: PersonalizerId::Compact,
            source,
        })?;

    validate_frozen_batch(
        PersonalizerId::Compact,
        round,
        compact_order.evidence_identity(),
        compact_prepared.frozen().round(),
        compact_prepared.frozen().evidence_identity(),
    )?;
    validate_frozen_batch(
        PersonalizerId::Rbf,
        round,
        rbf_order.evidence_identity(),
        rbf_prepared.frozen().round(),
        rbf_prepared.frozen().evidence_identity(),
    )?;
    let compact_event_ids = compact_prepared.frozen().candidate_ids().to_vec();
    let rbf_event_ids = rbf_prepared.frozen().candidate_ids().to_vec();
    rbf_controller.commit_prepared_batch(rbf_prepared);
    compact_controller.commit_prepared_batch(compact_prepared);
    let audit = vec![SharedLearningAuditEvent::BatchesFrozen {
        round,
        compact_event_ids: compact_event_ids.clone(),
        rbf_event_ids: rbf_event_ids.clone(),
    }];

    Ok(Box::new(SharedLearningRoundState {
        round,
        compact_order,
        rbf_order,
        metadata,
        routes,
        compact_event_ids,
        rbf_event_ids,
        audit,
        terminal_failure: None,
        prepared_completion: None,
    }))
}

pub(crate) fn submit_shared_learning_round_ratings(
    state: &mut SharedLearningRoundState,
    compact_controller: &mut CompactLearningController,
    rbf_controller: &mut RbfLearningController,
    ratings: Vec<BatchRating>,
) -> Result<()> {
    if state.prepared_completion.is_some() {
        return Err(SharedLearningRoundError::AlreadyComplete);
    }
    if let Some((personalizer, message)) = &state.terminal_failure {
        return Err(SharedLearningRoundError::TerminalFailure {
            personalizer: *personalizer,
            message: message.clone(),
        });
    }
    validate_state_bindings(state, compact_controller, rbf_controller)?;

    let ratings = validate_rating_set(&state.routes.required_event_ids, ratings)?;
    let canonical_ratings = state
        .routes
        .required_event_ids
        .iter()
        .map(|event_id| ratings[event_id])
        .collect::<Vec<_>>();
    let compact_ratings = ratings_for_event_ids(&state.compact_event_ids, &ratings)?;
    let rbf_ratings = ratings_for_event_ids(&state.rbf_event_ids, &ratings)?;

    let rbf_prepared = match rbf_controller.prepare_completion(rbf_ratings) {
        Ok(prepared) => prepared,
        Err(error) => {
            return Err(state.record_terminal_failure(PersonalizerId::Rbf, error));
        }
    };
    let compact_prepared = match compact_controller.prepare_completion(compact_ratings) {
        Ok(prepared) => prepared,
        Err(error) => {
            return Err(state.record_terminal_failure(PersonalizerId::Compact, error));
        }
    };
    state.prepared_completion = Some(PreparedSharedRoundCompletion {
        compact: compact_prepared,
        rbf: rbf_prepared,
        ratings: canonical_ratings,
    });
    Ok(())
}

pub(crate) fn finish_shared_learning_round_state(
    state: Box<SharedLearningRoundState>,
    compact_controller: &mut CompactLearningController,
    rbf_controller: &mut RbfLearningController,
) -> std::result::Result<SharedLearningRoundRecord, Box<SharedLearningRoundState>> {
    if state.prepared_completion.is_none()
        || validate_state_bindings(&state, compact_controller, rbf_controller).is_err()
    {
        return Err(state);
    }
    let SharedLearningRoundState {
        round,
        compact_order,
        rbf_order,
        metadata,
        routes,
        compact_event_ids: _,
        rbf_event_ids: _,
        mut audit,
        terminal_failure: _,
        prepared_completion,
    } = *state;
    let prepared = prepared_completion.expect("prepared completion was checked");
    let compact_round = prepared.compact.record().clone();
    let rbf_round = prepared.rbf.record().clone();
    audit.push(SharedLearningAuditEvent::RatingsApplied {
        ratings: prepared.ratings.clone(),
    });
    audit.push(SharedLearningAuditEvent::RoundCompleted {
        round,
        compact_evidence_after: compact_round.evidence_after().clone(),
        rbf_evidence_after: rbf_round.evidence_after().clone(),
    });
    let record = SharedLearningRoundRecord {
        round,
        compact_order,
        rbf_order,
        quota_metadata: metadata,
        compact_round,
        rbf_round,
        ratings: prepared.ratings,
        presentation_ledger_entries: routes.presentation_ledger_entries,
        audit,
    };
    rbf_controller.commit_prepared_completion(prepared.rbf);
    compact_controller.commit_prepared_completion(prepared.compact);
    Ok(record)
}

pub(crate) fn discard_shared_learning_round_state(
    state: Box<SharedLearningRoundState>,
    compact_controller: &mut CompactLearningController,
    rbf_controller: &mut RbfLearningController,
) {
    if validate_state_bindings(&state, compact_controller, rbf_controller).is_ok() {
        compact_controller.discard_pending_batch();
        rbf_controller.discard_pending_batch();
    }
}

fn validate_state_bindings(
    state: &SharedLearningRoundState,
    compact: &CompactLearningController,
    rbf: &RbfLearningController,
) -> Result<()> {
    validate_pending_binding(
        PersonalizerId::Compact,
        state.round,
        state.compact_order.evidence_identity(),
        &state.compact_event_ids,
        compact.history().len(),
        compact.pending_batch().map(|batch| {
            (
                batch.round(),
                batch.evidence_identity(),
                batch.candidate_ids(),
            )
        }),
    )?;
    validate_pending_binding(
        PersonalizerId::Rbf,
        state.round,
        state.rbf_order.evidence_identity(),
        &state.rbf_event_ids,
        rbf.history().len(),
        rbf.pending_batch().map(|batch| {
            (
                batch.round(),
                batch.evidence_identity(),
                batch.candidate_ids(),
            )
        }),
    )
}

fn validate_pending_binding(
    personalizer: PersonalizerId,
    round: usize,
    evidence_identity: &EvidenceIdentity,
    event_ids: &[EventId],
    completed_rounds: usize,
    pending: Option<(usize, &EvidenceIdentity, &[EventId])>,
) -> Result<()> {
    let Some((pending_round, pending_evidence, pending_event_ids)) = pending else {
        return Err(invariant(format!(
            "{personalizer:?} lost its frozen shared-learning batch"
        )));
    };
    if completed_rounds + 1 != round
        || pending_round != round
        || pending_evidence != evidence_identity
        || pending_event_ids != event_ids
    {
        return Err(invariant(format!(
            "{personalizer:?} no longer matches its frozen shared-learning batch"
        )));
    }
    Ok(())
}

fn validate_bindings(
    quota: &ResolvedQuota,
    compact: &CompactLearningController,
    rbf: &RbfLearningController,
) -> Result<()> {
    validate_role(quota.compact().personalizer(), PersonalizerId::Compact)?;
    validate_role(quota.rbf().personalizer(), PersonalizerId::Rbf)?;
    let compact_phase = quota.compact_order().attempt().phase();
    let rbf_phase = quota.rbf_order().attempt().phase();
    if compact_phase != CandidateOrderPhase::Learning {
        return Err(SharedLearningRoundError::InvalidPhase(compact_phase));
    }
    if rbf_phase != CandidateOrderPhase::Learning {
        return Err(SharedLearningRoundError::InvalidPhase(rbf_phase));
    }
    validate_compact_binding(quota.compact(), compact)?;
    validate_rbf_binding(quota.rbf(), rbf)?;

    let compact_round = compact.history().len() + 1;
    let rbf_round = rbf.history().len() + 1;
    if compact_round != rbf_round {
        return Err(SharedLearningRoundError::RoundMismatch {
            compact_round,
            rbf_round,
        });
    }
    if compact_round > LEARNING_ROUNDS {
        return Err(SharedLearningRoundError::LearningRoundsComplete);
    }
    Ok(())
}

fn validate_role(actual: PersonalizerId, expected: PersonalizerId) -> Result<()> {
    if actual != expected {
        return Err(SharedLearningRoundError::RoleMismatch { expected, actual });
    }
    Ok(())
}

fn validate_compact_binding(
    resolved: &ResolvedPersonalizerQuota,
    controller: &CompactLearningController,
) -> Result<()> {
    let personalizer = PersonalizerId::Compact;
    let attempt = resolved.order().attempt();
    if attempt.representation_version() != controller.representation_version()
        || resolved.batch().representation_version() != controller.representation_version()
    {
        return Err(SharedLearningRoundError::RepresentationVersionMismatch { personalizer });
    }
    if attempt.evidence_identity() != controller.evidence_identity() {
        return Err(SharedLearningRoundError::EvidenceIdentityMismatch { personalizer });
    }
    if attempt.active_parameters()
        != ActivePersonalizerParameters::Compact(controller.active_tuple())
    {
        return Err(SharedLearningRoundError::ActiveParametersMismatch { personalizer });
    }
    if controller.pending_batch().is_some() {
        return Err(SharedLearningRoundError::BatchPending { personalizer });
    }
    Ok(())
}

fn validate_rbf_binding(
    resolved: &ResolvedPersonalizerQuota,
    controller: &RbfLearningController,
) -> Result<()> {
    let personalizer = PersonalizerId::Rbf;
    let attempt = resolved.order().attempt();
    if attempt.representation_version() != controller.representation_version()
        || resolved.batch().representation_version() != controller.representation_version()
    {
        return Err(SharedLearningRoundError::RepresentationVersionMismatch { personalizer });
    }
    if attempt.evidence_identity() != controller.evidence_identity() {
        return Err(SharedLearningRoundError::EvidenceIdentityMismatch { personalizer });
    }
    if attempt.active_parameters() != ActivePersonalizerParameters::Rbf(controller.active_tuple()) {
        return Err(SharedLearningRoundError::ActiveParametersMismatch { personalizer });
    }
    if controller.pending_batch().is_some() {
        return Err(SharedLearningRoundError::BatchPending { personalizer });
    }
    Ok(())
}

fn prepare_routes(metadata: &QuotaResolutionMetadata) -> Result<PreparedRoutes> {
    let new_routes = metadata
        .new_rating_routes()
        .iter()
        .map(|route| (route.event_id(), route.selected_by()))
        .collect::<BTreeMap<_, _>>();
    let mut new_event_ids = Vec::with_capacity(new_routes.len());
    let mut presentation_ledger_entries = BTreeMap::new();
    for outcome in metadata.presentation_ledger_delta().outcomes() {
        match outcome.eligibility() {
            LanguageEligibility::Eligible => {
                let event_id = outcome.event_id();
                let selected_by = new_routes.get(&event_id).ok_or_else(|| {
                    invariant(format!(
                        "eligible new presentation {event_id:?} has no new-rating route"
                    ))
                })?;
                new_event_ids.push(event_id);
                presentation_ledger_entries.insert(
                    event_id,
                    PriorPresentation::rated_by(selected_by.iter().copied())
                        .map_err(|error| invariant(error.to_string()))?,
                );
            }
            LanguageEligibility::WrongLanguage => {
                presentation_ledger_entries
                    .insert(outcome.event_id(), PriorPresentation::WrongLanguage);
            }
        }
    }
    if new_event_ids.iter().copied().collect::<BTreeSet<_>>()
        != new_routes.keys().copied().collect()
    {
        return Err(invariant(
            "new-rating routes do not match eligible presentation outcomes",
        ));
    }

    let stored_event_ids = metadata
        .stored_rating_reuse_routes()
        .iter()
        .map(|route| route.event_id())
        .collect::<BTreeSet<_>>()
        .into_iter()
        .collect::<Vec<_>>();
    let mut required_event_ids = new_event_ids.clone();
    required_event_ids.extend(stored_event_ids.iter().copied());
    Ok(PreparedRoutes {
        new_event_ids,
        stored_event_ids,
        required_event_ids,
        presentation_ledger_entries,
    })
}

fn validate_rating_set(
    required_event_ids: &[EventId],
    ratings: Vec<BatchRating>,
) -> Result<BTreeMap<EventId, BatchRating>> {
    let required = required_event_ids.iter().copied().collect::<BTreeSet<_>>();
    let mut validated = BTreeMap::new();
    for rating in ratings {
        if !required.contains(&rating.event_id()) {
            return Err(SharedLearningRoundError::UnexpectedRating {
                event_id: rating.event_id(),
            });
        }
        if validated.insert(rating.event_id(), rating).is_some() {
            return Err(SharedLearningRoundError::DuplicateRating {
                event_id: rating.event_id(),
            });
        }
    }
    if let Some(event_id) = required_event_ids
        .iter()
        .find(|event_id| !validated.contains_key(*event_id))
    {
        return Err(SharedLearningRoundError::MissingRating {
            event_id: *event_id,
        });
    }
    Ok(validated)
}

fn ratings_for_event_ids(
    event_ids: &[EventId],
    ratings: &BTreeMap<EventId, BatchRating>,
) -> Result<Vec<BatchRating>> {
    event_ids
        .iter()
        .map(|event_id| {
            ratings.get(event_id).copied().ok_or_else(|| {
                invariant(format!(
                    "validated rating set lost batch event {event_id:?}"
                ))
            })
        })
        .collect()
}

fn validate_frozen_batch(
    personalizer: PersonalizerId,
    round: usize,
    evidence_identity: &EvidenceIdentity,
    frozen_round: usize,
    frozen_evidence_identity: &EvidenceIdentity,
) -> Result<()> {
    if frozen_round != round || frozen_evidence_identity != evidence_identity {
        return Err(invariant(format!(
            "{personalizer:?} installed a frozen batch with different bindings"
        )));
    }
    Ok(())
}

fn invariant(message: impl Into<String>) -> SharedLearningRoundError {
    SharedLearningRoundError::InternalInvariant(message.into())
}
