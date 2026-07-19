//! One causally frozen adaptive-learning round shared by both personalizers.

use std::collections::{BTreeMap, BTreeSet};

use thiserror::Error;

use crate::candidate_order::{
    ActivePersonalizerParameters, CandidateOrderPhase, FrozenCandidateOrder,
};
use crate::personalizer_learning::{
    BatchRating, CompactLearningController, CompactRoundRecord, EvidenceIdentity,
    PersonalizerLearningError, RbfLearningController, RbfRoundRecord,
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

#[derive(Clone, Debug, PartialEq)]
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
    round: usize,
    compact_order: FrozenCandidateOrder,
    rbf_order: FrozenCandidateOrder,
    metadata: QuotaResolutionMetadata,
    routes: PreparedRoutes,
    compact_event_ids: Vec<EventId>,
    rbf_event_ids: Vec<EventId>,
    audit: Vec<SharedLearningAuditEvent>,
    terminal_failure: Option<(PersonalizerId, String)>,
    completed: Option<SharedLearningRoundRecord>,
}

impl PendingSharedLearningRound<'_> {
    pub const fn round(&self) -> usize {
        self.round
    }

    pub fn new_rating_event_ids(&self) -> &[EventId] {
        &self.routes.new_event_ids
    }

    pub fn stored_rating_event_ids(&self) -> &[EventId] {
        &self.routes.stored_event_ids
    }

    pub fn required_rating_event_ids(&self) -> &[EventId] {
        &self.routes.required_event_ids
    }

    pub const fn is_complete(&self) -> bool {
        self.completed.is_some()
    }

    pub fn audit(&self) -> &[SharedLearningAuditEvent] {
        &self.audit
    }

    pub fn terminal_failure(&self) -> Option<(PersonalizerId, &str)> {
        self.terminal_failure
            .as_ref()
            .map(|(personalizer, message)| (*personalizer, message.as_str()))
    }

    pub fn submit_ratings(&mut self, ratings: Vec<BatchRating>) -> Result<()> {
        if self.completed.is_some() {
            return Err(SharedLearningRoundError::AlreadyComplete);
        }
        if let Some((personalizer, message)) = &self.terminal_failure {
            return Err(SharedLearningRoundError::TerminalFailure {
                personalizer: *personalizer,
                message: message.clone(),
            });
        }

        let ratings = validate_rating_set(&self.routes.required_event_ids, ratings)?;
        let canonical_ratings = self
            .routes
            .required_event_ids
            .iter()
            .map(|event_id| ratings[event_id])
            .collect::<Vec<_>>();
        let compact_ratings = ratings_for_event_ids(&self.compact_event_ids, &ratings)?;
        let rbf_ratings = ratings_for_event_ids(&self.rbf_event_ids, &ratings)?;

        let rbf_prepared = match self.rbf_controller.prepare_completion(rbf_ratings) {
            Ok(prepared) => prepared,
            Err(error) => {
                return Err(self.record_terminal_failure(PersonalizerId::Rbf, error));
            }
        };
        let compact_prepared = match self.compact_controller.prepare_completion(compact_ratings) {
            Ok(prepared) => prepared,
            Err(error) => {
                return Err(self.record_terminal_failure(PersonalizerId::Compact, error));
            }
        };
        let rbf_round = self
            .rbf_controller
            .commit_prepared_completion(rbf_prepared)
            .clone();
        let compact_round = self
            .compact_controller
            .commit_prepared_completion(compact_prepared)
            .clone();

        self.audit.push(SharedLearningAuditEvent::RatingsApplied {
            ratings: canonical_ratings.clone(),
        });
        self.audit.push(SharedLearningAuditEvent::RoundCompleted {
            round: self.round,
            compact_evidence_after: compact_round.evidence_after().clone(),
            rbf_evidence_after: rbf_round.evidence_after().clone(),
        });
        self.completed = Some(SharedLearningRoundRecord {
            round: self.round,
            compact_order: self.compact_order.clone(),
            rbf_order: self.rbf_order.clone(),
            quota_metadata: self.metadata.clone(),
            compact_round,
            rbf_round,
            ratings: canonical_ratings,
            presentation_ledger_entries: self.routes.presentation_ledger_entries.clone(),
            audit: self.audit.clone(),
        });
        Ok(())
    }

    pub fn finish(mut self) -> std::result::Result<SharedLearningRoundRecord, Box<Self>> {
        if self.completed.is_none() {
            return Err(Box::new(self));
        }
        Ok(self
            .completed
            .take()
            .expect("completed record was checked before consuming the pending round"))
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

impl Drop for PendingSharedLearningRound<'_> {
    fn drop(&mut self) {
        self.compact_controller.discard_pending_batch();
        self.rbf_controller.discard_pending_batch();
    }
}

pub fn begin_shared_learning_round<'a>(
    quota: ResolvedQuota,
    compact_controller: &'a mut CompactLearningController,
    rbf_controller: &'a mut RbfLearningController,
) -> Result<PendingSharedLearningRound<'a>> {
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

    Ok(PendingSharedLearningRound {
        compact_controller,
        rbf_controller,
        round,
        compact_order,
        rbf_order,
        metadata,
        routes,
        compact_event_ids,
        rbf_event_ids,
        audit,
        terminal_failure: None,
        completed: None,
    })
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
