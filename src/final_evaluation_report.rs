//! Deterministic report calculation over one resolved final evaluation.

use std::collections::{BTreeMap, BTreeSet};

use thiserror::Error;

use crate::artifact::hash_bytes;
use crate::personalizer_learning::GladnessRating;
use crate::quota_resolution::{
    LanguageDelta, LanguageEligibility, PersonalizerId, QuotaAuditEvent, ResolvedQuota,
};
use crate::representation::EventId;

pub const FINAL_RATINGS_PER_PERSONALIZER: usize = 200;
pub const PASS_RATING_SUM: u64 = 1_000;
pub const MAX_LOW_RATINGS: usize = 20;

pub type Result<T> = std::result::Result<T, FinalEvaluationReportError>;

#[derive(Debug, Error, PartialEq)]
pub enum FinalEvaluationReportError {
    #[error("final report provenance field `{field}` is invalid")]
    InvalidProvenance { field: &'static str },
    #[error(
        "final report representation version `{actual}` does not match resolved quota `{expected}`"
    )]
    RepresentationVersionMismatch { expected: String, actual: String },
    #[error("failed to encode the final quota audit: {0}")]
    QuotaAuditEncoding(String),
    #[error(
        "final quota audit identity `{actual}` does not match the exact audit bytes `{expected}`"
    )]
    QuotaAuditIdentityMismatch { expected: String, actual: String },
    #[error("final quota unexpectedly reuses a stored rating for event {event_id:?}")]
    StoredRatingReuse { event_id: EventId },
    #[error("final rating is missing for event {event_id:?}")]
    MissingRating { event_id: EventId },
    #[error("final rating includes event {event_id:?}, which has no new-rating route")]
    UnexpectedRating { event_id: EventId },
    #[error("{personalizer:?} final choice {event_id:?} has no matching rating route")]
    MissingRatingRoute {
        personalizer: PersonalizerId,
        event_id: EventId,
    },
    #[error(
        "{personalizer:?} final report contains {actual} ratings; exactly {expected} are required"
    )]
    RatingCount {
        personalizer: PersonalizerId,
        expected: usize,
        actual: usize,
    },
    #[error(
        "final wrong-language ceiling exceeded: {wrong_language_presentations} of {unique_presentations} unique presentations"
    )]
    WrongLanguageCeilingExceeded {
        wrong_language_presentations: usize,
        unique_presentations: usize,
    },
}

/// Immutable identities required to reproduce and audit the final result.
#[derive(Clone, Debug, Eq, PartialEq, serde::Serialize)]
pub struct FinalEvaluationReportProvenance {
    corpus_identity: String,
    representation_version: String,
    geometry_version: String,
    phase3_handoff_identity_sha256: String,
    guarded_launch_identity_sha256: String,
    final_orders_identity_sha256: String,
    evaluator_protocol_identity_sha256: String,
    evaluator_transcript_identity_sha256: String,
    quota_audit_identity_sha256: String,
}

impl FinalEvaluationReportProvenance {
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        corpus_identity: impl Into<String>,
        representation_version: impl Into<String>,
        geometry_version: impl Into<String>,
        phase3_handoff_identity_sha256: impl Into<String>,
        guarded_launch_identity_sha256: impl Into<String>,
        final_orders_identity_sha256: impl Into<String>,
        evaluator_protocol_identity_sha256: impl Into<String>,
        evaluator_transcript_identity_sha256: impl Into<String>,
        quota_audit_identity_sha256: impl Into<String>,
    ) -> Result<Self> {
        let provenance = Self {
            corpus_identity: corpus_identity.into(),
            representation_version: representation_version.into(),
            geometry_version: geometry_version.into(),
            phase3_handoff_identity_sha256: phase3_handoff_identity_sha256.into(),
            guarded_launch_identity_sha256: guarded_launch_identity_sha256.into(),
            final_orders_identity_sha256: final_orders_identity_sha256.into(),
            evaluator_protocol_identity_sha256: evaluator_protocol_identity_sha256.into(),
            evaluator_transcript_identity_sha256: evaluator_transcript_identity_sha256.into(),
            quota_audit_identity_sha256: quota_audit_identity_sha256.into(),
        };
        provenance.validate()?;
        Ok(provenance)
    }

    pub fn corpus_identity(&self) -> &str {
        &self.corpus_identity
    }

    pub fn representation_version(&self) -> &str {
        &self.representation_version
    }

    pub fn geometry_version(&self) -> &str {
        &self.geometry_version
    }

    pub fn phase3_handoff_identity_sha256(&self) -> &str {
        &self.phase3_handoff_identity_sha256
    }

    pub fn guarded_launch_identity_sha256(&self) -> &str {
        &self.guarded_launch_identity_sha256
    }

    pub fn final_orders_identity_sha256(&self) -> &str {
        &self.final_orders_identity_sha256
    }

    pub fn evaluator_protocol_identity_sha256(&self) -> &str {
        &self.evaluator_protocol_identity_sha256
    }

    pub fn evaluator_transcript_identity_sha256(&self) -> &str {
        &self.evaluator_transcript_identity_sha256
    }

    pub fn quota_audit_identity_sha256(&self) -> &str {
        &self.quota_audit_identity_sha256
    }

    fn validate(&self) -> Result<()> {
        let corpus_sha256 = self.corpus_identity.strip_prefix("sha256:").ok_or(
            FinalEvaluationReportError::InvalidProvenance {
                field: "corpus_identity",
            },
        )?;
        if !is_sha256(corpus_sha256) {
            return Err(FinalEvaluationReportError::InvalidProvenance {
                field: "corpus_identity",
            });
        }
        for (field, value) in [
            (
                "representation_version",
                self.representation_version.as_str(),
            ),
            ("geometry_version", self.geometry_version.as_str()),
        ] {
            if value.is_empty() {
                return Err(FinalEvaluationReportError::InvalidProvenance { field });
            }
        }
        for (field, value) in [
            (
                "phase3_handoff_identity_sha256",
                self.phase3_handoff_identity_sha256.as_str(),
            ),
            (
                "guarded_launch_identity_sha256",
                self.guarded_launch_identity_sha256.as_str(),
            ),
            (
                "final_orders_identity_sha256",
                self.final_orders_identity_sha256.as_str(),
            ),
            (
                "evaluator_protocol_identity_sha256",
                self.evaluator_protocol_identity_sha256.as_str(),
            ),
            (
                "evaluator_transcript_identity_sha256",
                self.evaluator_transcript_identity_sha256.as_str(),
            ),
            (
                "quota_audit_identity_sha256",
                self.quota_audit_identity_sha256.as_str(),
            ),
        ] {
            if !is_sha256(value) {
                return Err(FinalEvaluationReportError::InvalidProvenance { field });
            }
        }
        Ok(())
    }
}

/// One exact final rating attributed to one personalizer.
#[derive(Clone, Copy, Debug, Eq, PartialEq, serde::Serialize)]
pub struct FinalRatingRecord {
    event_id: EventId,
    rating: GladnessRating,
}

impl FinalRatingRecord {
    pub const fn event_id(&self) -> EventId {
        self.event_id
    }

    pub const fn rating(&self) -> GladnessRating {
        self.rating
    }
}

#[derive(Clone, Debug, PartialEq, serde::Serialize)]
pub struct PersonalizerFinalReport {
    personalizer: PersonalizerId,
    ratings: Vec<FinalRatingRecord>,
    rating_distribution: [usize; 7],
    rating_sum: u64,
    mean_rating: f64,
    low_rating_count: usize,
    low_rating_percentage: f64,
    wrong_language_event_ids: Vec<EventId>,
    wrong_language_percentage: f64,
    passed: bool,
}

impl PersonalizerFinalReport {
    pub const fn personalizer(&self) -> PersonalizerId {
        self.personalizer
    }

    pub fn ratings(&self) -> &[FinalRatingRecord] {
        &self.ratings
    }

    pub const fn rating_distribution(&self) -> &[usize; 7] {
        &self.rating_distribution
    }

    pub const fn rating_sum(&self) -> u64 {
        self.rating_sum
    }

    pub const fn mean_rating(&self) -> f64 {
        self.mean_rating
    }

    pub const fn low_rating_count(&self) -> usize {
        self.low_rating_count
    }

    pub const fn low_rating_percentage(&self) -> f64 {
        self.low_rating_percentage
    }

    pub fn wrong_language_event_ids(&self) -> &[EventId] {
        &self.wrong_language_event_ids
    }

    pub fn wrong_language_presentations(&self) -> usize {
        self.wrong_language_event_ids.len()
    }

    pub const fn wrong_language_percentage(&self) -> f64 {
        self.wrong_language_percentage
    }

    pub const fn passed(&self) -> bool {
        self.passed
    }
}

#[derive(Clone, Debug, PartialEq, serde::Serialize)]
pub struct FinalLanguageDiagnostics {
    eligible_presentations: usize,
    wrong_language_presentations: usize,
    unique_presentations: usize,
    wrong_language_percentage: f64,
    wrong_language_event_ids: Vec<EventId>,
}

impl FinalLanguageDiagnostics {
    pub const fn eligible_presentations(&self) -> usize {
        self.eligible_presentations
    }

    pub const fn wrong_language_presentations(&self) -> usize {
        self.wrong_language_presentations
    }

    pub const fn unique_presentations(&self) -> usize {
        self.unique_presentations
    }

    pub const fn wrong_language_percentage(&self) -> f64 {
        self.wrong_language_percentage
    }

    pub fn wrong_language_event_ids(&self) -> &[EventId] {
        &self.wrong_language_event_ids
    }
}

#[derive(Clone, Debug, PartialEq, serde::Serialize)]
pub struct FinalEvaluationReport {
    provenance: FinalEvaluationReportProvenance,
    language: FinalLanguageDiagnostics,
    quota_audit: Vec<QuotaAuditEvent>,
    compact: PersonalizerFinalReport,
    rbf: PersonalizerFinalReport,
    passed: bool,
}

impl FinalEvaluationReport {
    pub const fn provenance(&self) -> &FinalEvaluationReportProvenance {
        &self.provenance
    }

    pub const fn language(&self) -> &FinalLanguageDiagnostics {
        &self.language
    }

    pub fn quota_audit(&self) -> &[QuotaAuditEvent] {
        &self.quota_audit
    }

    pub const fn compact(&self) -> &PersonalizerFinalReport {
        &self.compact
    }

    pub const fn rbf(&self) -> &PersonalizerFinalReport {
        &self.rbf
    }

    pub const fn passed(&self) -> bool {
        self.passed
    }
}

/// Route one evaluator rating per unique event into both exact personalizer
/// result sets selected by the frozen quota resolver.
pub fn build_final_evaluation_report(
    quota: &ResolvedQuota,
    ratings: &BTreeMap<EventId, GladnessRating>,
    provenance: FinalEvaluationReportProvenance,
) -> Result<FinalEvaluationReport> {
    let expected_representation = quota.compact_batch().representation_version();
    if provenance.representation_version() != expected_representation {
        return Err(FinalEvaluationReportError::RepresentationVersionMismatch {
            expected: expected_representation.to_owned(),
            actual: provenance.representation_version().to_owned(),
        });
    }
    let quota_audit_bytes = serde_json::to_vec(quota.audit())
        .map_err(|source| FinalEvaluationReportError::QuotaAuditEncoding(source.to_string()))?;
    let expected_audit_identity = hash_bytes(&quota_audit_bytes);
    if provenance.quota_audit_identity_sha256() != expected_audit_identity {
        return Err(FinalEvaluationReportError::QuotaAuditIdentityMismatch {
            expected: expected_audit_identity,
            actual: provenance.quota_audit_identity_sha256().to_owned(),
        });
    }
    let quota_audit = quota.audit().to_vec();

    if let Some(route) = quota.stored_rating_reuse_routes().first() {
        return Err(FinalEvaluationReportError::StoredRatingReuse {
            event_id: route.event_id(),
        });
    }

    let routed_ids = quota
        .new_rating_routes()
        .iter()
        .map(|route| route.event_id())
        .collect::<BTreeSet<_>>();
    if let Some(event_id) = routed_ids
        .iter()
        .find(|event_id| !ratings.contains_key(*event_id))
    {
        return Err(FinalEvaluationReportError::MissingRating {
            event_id: *event_id,
        });
    }
    if let Some(event_id) = ratings
        .keys()
        .find(|event_id| !routed_ids.contains(*event_id))
    {
        return Err(FinalEvaluationReportError::UnexpectedRating {
            event_id: *event_id,
        });
    }

    let routes = quota
        .new_rating_routes()
        .iter()
        .map(|route| (route.event_id(), route.selected_by()))
        .collect::<BTreeMap<_, _>>();
    let compact = build_personalizer_report(
        PersonalizerId::Compact,
        quota.compact_batch(),
        &routes,
        ratings,
        personalizer_wrong_language_event_ids(quota, PersonalizerId::Compact),
    )?;
    let rbf = build_personalizer_report(
        PersonalizerId::Rbf,
        quota.rbf_batch(),
        &routes,
        ratings,
        personalizer_wrong_language_event_ids(quota, PersonalizerId::Rbf),
    )?;
    let language = build_language_diagnostics(quota)?;

    Ok(FinalEvaluationReport {
        provenance,
        language,
        quota_audit,
        passed: compact.passed || rbf.passed,
        compact,
        rbf,
    })
}

fn build_personalizer_report(
    personalizer: PersonalizerId,
    batch: &crate::personalizer_learning::CandidateBatch,
    routes: &BTreeMap<EventId, &BTreeSet<PersonalizerId>>,
    ratings: &BTreeMap<EventId, GladnessRating>,
    wrong_language_event_ids: Vec<EventId>,
) -> Result<PersonalizerFinalReport> {
    let mut records = Vec::with_capacity(batch.candidates().len());
    for candidate in batch.candidates() {
        let event_id = candidate.event_id();
        let Some(selected_by) = routes.get(&event_id) else {
            return Err(FinalEvaluationReportError::MissingRatingRoute {
                personalizer,
                event_id,
            });
        };
        if !selected_by.contains(&personalizer) {
            return Err(FinalEvaluationReportError::MissingRatingRoute {
                personalizer,
                event_id,
            });
        }
        let Some(&rating) = ratings.get(&event_id) else {
            return Err(FinalEvaluationReportError::MissingRating { event_id });
        };
        records.push(FinalRatingRecord { event_id, rating });
    }
    if records.len() != FINAL_RATINGS_PER_PERSONALIZER {
        return Err(FinalEvaluationReportError::RatingCount {
            personalizer,
            expected: FINAL_RATINGS_PER_PERSONALIZER,
            actual: records.len(),
        });
    }

    let mut rating_distribution = [0_usize; 7];
    let mut rating_sum = 0_u64;
    for record in &records {
        let value = record.rating.value();
        rating_distribution[usize::from(value - 1)] += 1;
        rating_sum += u64::from(value);
    }
    let low_rating_count = rating_distribution[0] + rating_distribution[1];
    let count = records.len() as f64;
    let mean_rating = rating_sum as f64 / count;
    let low_rating_percentage = 100.0 * low_rating_count as f64 / count;
    let wrong_language_percentage = 100.0 * wrong_language_event_ids.len() as f64
        / (records.len() + wrong_language_event_ids.len()) as f64;
    let passed = rating_sum >= PASS_RATING_SUM && low_rating_count <= MAX_LOW_RATINGS;

    Ok(PersonalizerFinalReport {
        personalizer,
        ratings: records,
        rating_distribution,
        rating_sum,
        mean_rating,
        low_rating_count,
        low_rating_percentage,
        wrong_language_event_ids,
        wrong_language_percentage,
        passed,
    })
}

fn personalizer_wrong_language_event_ids(
    quota: &ResolvedQuota,
    personalizer: PersonalizerId,
) -> Vec<EventId> {
    quota
        .audit()
        .iter()
        .filter_map(|event| match event {
            QuotaAuditEvent::WrongLanguageRejected {
                personalizer: rejected_by,
                event_id,
                ..
            } if *rejected_by == personalizer => Some(*event_id),
            _ => None,
        })
        .collect()
}

fn build_language_diagnostics(quota: &ResolvedQuota) -> Result<FinalLanguageDiagnostics> {
    let delta: LanguageDelta = quota.language_delta();
    let unique_presentations = delta.unique_presentations();
    let wrong_language_presentations = delta.wrong_language_presentations();
    if (wrong_language_presentations as u128) * 20 > unique_presentations as u128 {
        return Err(FinalEvaluationReportError::WrongLanguageCeilingExceeded {
            wrong_language_presentations,
            unique_presentations,
        });
    }
    let wrong_language_percentage = if unique_presentations == 0 {
        0.0
    } else {
        100.0 * wrong_language_presentations as f64 / unique_presentations as f64
    };
    let wrong_language_event_ids = quota
        .presentation_ledger_delta()
        .outcomes()
        .iter()
        .filter(|outcome| outcome.eligibility() == LanguageEligibility::WrongLanguage)
        .map(|outcome| outcome.event_id())
        .collect::<Vec<_>>();
    Ok(FinalLanguageDiagnostics {
        eligible_presentations: delta.eligible_presentations(),
        wrong_language_presentations,
        unique_presentations,
        wrong_language_percentage,
        wrong_language_event_ids,
    })
}

fn is_sha256(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}
