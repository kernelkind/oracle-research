//! Frozen final evaluation over both completed Phase 3 personalizers.

use std::error::Error as StdError;
use std::fmt;

use thiserror::Error;

use crate::adaptive_learning::{CompletedAdaptiveLearning, FinalCandidateOrderBuildError};
use crate::candidate_order::{
    CandidateOrderAttempt, CandidateOrderError, CandidateOrderOracle, FrozenCandidateOrder,
};
use crate::quota_resolution::{
    EventLanguageOutcome, LanguageDelta, PersonalizerId, PresentationLedgerDelta,
    PresentationLedgerSnapshot, PresentationWave, QuotaAuditEvent, QuotaResolutionError,
    QuotaResolutionFailure, QuotaResolutionProgress, ResolvedQuota, SharedQuotaResolver,
};

pub type Result<T> = std::result::Result<T, FinalEvaluationStartError>;

#[derive(Debug, Error)]
pub enum FinalEvaluationFailure {
    #[error("{personalizer:?} final candidate-order construction failed: {source}")]
    CandidateOrder {
        personalizer: PersonalizerId,
        #[source]
        source: CandidateOrderError,
    },
    #[error(
        "{personalizer:?} final candidate order accepted {accepted} events; {required} are required"
    )]
    InsufficientCandidateOrder {
        personalizer: PersonalizerId,
        accepted: usize,
        required: usize,
        attempt: Box<CandidateOrderAttempt>,
    },
    #[error(transparent)]
    QuotaResolution(#[from] QuotaResolutionError),
}

impl FinalEvaluationFailure {
    pub fn candidate_order_attempt(&self) -> Option<&CandidateOrderAttempt> {
        match self {
            Self::InsufficientCandidateOrder { attempt, .. } => Some(attempt),
            Self::CandidateOrder { .. } | Self::QuotaResolution(_) => None,
        }
    }
}

/// A failed one-way transition into Phase 4.
///
/// The completed learning handoff is returned with every failure so a repaired
/// Oracle or candidate pool can be retried without replaying learning.
pub struct FinalEvaluationStartError {
    failure: FinalEvaluationFailure,
    completed_learning: Box<CompletedAdaptiveLearning>,
}

impl FinalEvaluationStartError {
    pub fn failure(&self) -> &FinalEvaluationFailure {
        &self.failure
    }

    pub fn completed_learning(&self) -> &CompletedAdaptiveLearning {
        &self.completed_learning
    }

    pub fn into_parts(self) -> (FinalEvaluationFailure, Box<CompletedAdaptiveLearning>) {
        (self.failure, self.completed_learning)
    }
}

impl fmt::Debug for FinalEvaluationStartError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("FinalEvaluationStartError")
            .field("failure", &self.failure)
            .finish_non_exhaustive()
    }
}

impl fmt::Display for FinalEvaluationStartError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        self.failure.fmt(formatter)
    }
}

impl StdError for FinalEvaluationStartError {
    fn source(&self) -> Option<&(dyn StdError + 'static)> {
        Some(&self.failure)
    }
}

/// The completed Phase 3 handoff paired with both resolved final quotas.
///
/// Final ratings are deliberately absent: quota resolution freezes which
/// events count for each personalizer before the evaluator rates them.
pub struct ResolvedFinalEvaluation {
    completed_learning: Box<CompletedAdaptiveLearning>,
    quota: ResolvedQuota,
}

impl ResolvedFinalEvaluation {
    pub fn completed_learning(&self) -> &CompletedAdaptiveLearning {
        &self.completed_learning
    }

    pub fn quota(&self) -> &ResolvedQuota {
        &self.quota
    }

    pub fn into_parts(self) -> (Box<CompletedAdaptiveLearning>, ResolvedQuota) {
        (self.completed_learning, self.quota)
    }
}

/// A failed one-way transition out of final quota resolution.
///
/// The Phase 3 handoff remains available for diagnosis. The quota error owns
/// the final presentation and language audit accumulated before failure.
pub struct FinalEvaluationResolutionError {
    source: QuotaResolutionError,
    completed_learning: Box<CompletedAdaptiveLearning>,
}

impl FinalEvaluationResolutionError {
    pub const fn source_error(&self) -> &QuotaResolutionError {
        &self.source
    }

    pub fn completed_learning(&self) -> &CompletedAdaptiveLearning {
        &self.completed_learning
    }

    pub fn into_parts(self) -> (QuotaResolutionError, Box<CompletedAdaptiveLearning>) {
        (self.source, self.completed_learning)
    }
}

impl fmt::Debug for FinalEvaluationResolutionError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("FinalEvaluationResolutionError")
            .field("source", &self.source)
            .finish_non_exhaustive()
    }
}

impl fmt::Display for FinalEvaluationResolutionError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        self.source.fmt(formatter)
    }
}

impl StdError for FinalEvaluationResolutionError {
    fn source(&self) -> Option<&(dyn StdError + 'static)> {
        Some(&self.source)
    }
}

/// Both untouched final candidate orders and their shared presentation state.
///
/// Construction freezes the orders before any evaluator outcome exists. The
/// learned controllers are read only; only their immutable public-vector cache
/// may gain rows requested while constructing the final orders.
pub struct FinalEvaluationCoordinator {
    completed_learning: Box<CompletedAdaptiveLearning>,
    resolver: SharedQuotaResolver,
}

impl FinalEvaluationCoordinator {
    pub fn begin<O: CandidateOrderOracle>(
        mut completed_learning: Box<CompletedAdaptiveLearning>,
        oracle: &mut O,
    ) -> Result<Self> {
        match freeze_resolver(&mut completed_learning, oracle) {
            Ok(resolver) => Ok(Self {
                completed_learning,
                resolver,
            }),
            Err(failure) => Err(FinalEvaluationStartError {
                failure,
                completed_learning,
            }),
        }
    }

    pub fn completed_learning(&self) -> &CompletedAdaptiveLearning {
        &self.completed_learning
    }

    pub fn compact_order(&self) -> &FrozenCandidateOrder {
        self.resolver.compact_order()
    }

    pub fn rbf_order(&self) -> &FrozenCandidateOrder {
        self.resolver.rbf_order()
    }

    pub fn pending_wave(&self) -> Option<&PresentationWave> {
        self.resolver.pending_wave()
    }

    pub fn progress(&self) -> QuotaResolutionProgress {
        self.resolver.progress()
    }

    pub fn failure(&self) -> Option<&QuotaResolutionFailure> {
        self.resolver.failure()
    }

    pub fn presentation_ledger_delta(&self) -> &PresentationLedgerDelta {
        self.resolver.presentation_ledger_delta()
    }

    pub fn language_delta(&self) -> LanguageDelta {
        self.resolver.language_delta()
    }

    pub fn audit(&self) -> &[QuotaAuditEvent] {
        self.resolver.audit()
    }

    pub fn submit_language_outcomes(
        &mut self,
        wave_id: u64,
        outcomes: Vec<EventLanguageOutcome>,
    ) -> std::result::Result<(), QuotaResolutionError> {
        self.resolver.submit_language_outcomes(wave_id, outcomes)
    }

    pub fn into_result(
        self,
    ) -> std::result::Result<ResolvedFinalEvaluation, FinalEvaluationResolutionError> {
        let Self {
            completed_learning,
            resolver,
        } = self;
        match resolver.into_result() {
            Ok(quota) => Ok(ResolvedFinalEvaluation {
                completed_learning,
                quota,
            }),
            Err(source) => Err(FinalEvaluationResolutionError {
                source,
                completed_learning,
            }),
        }
    }
}

fn freeze_resolver<O: CandidateOrderOracle>(
    completed_learning: &mut CompletedAdaptiveLearning,
    oracle: &mut O,
) -> std::result::Result<SharedQuotaResolver, FinalEvaluationFailure> {
    let (compact, rbf) = completed_learning
        .build_final_candidate_orders(oracle)
        .map_err(|error| match error {
            FinalCandidateOrderBuildError::CandidateOrder {
                personalizer,
                source,
            } => FinalEvaluationFailure::CandidateOrder {
                personalizer,
                source,
            },
            FinalCandidateOrderBuildError::Insufficient {
                personalizer,
                failure,
            } => FinalEvaluationFailure::InsufficientCandidateOrder {
                personalizer,
                accepted: failure.accepted_count(),
                required: failure.required_count(),
                attempt: Box::new((*failure).into_attempt()),
            },
        })?;
    let prior_ledger =
        PresentationLedgerSnapshot::new(completed_learning.presentation_ledger().clone())?;
    SharedQuotaResolver::new(compact, rbf, prior_ledger).map_err(Into::into)
}
