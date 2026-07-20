//! Bounded candidate discovery and local ordering for one personalizer.

use std::cmp::Ordering;
use std::collections::{BTreeMap, BTreeSet};

use sha2::{Digest, Sha256};
use thiserror::Error;

use crate::artifact::hash_bytes;
use crate::fp32_oracle::{
    Fp32OfflineOracle, SimilarNotesRequest, SimilarNotesResponse, SimilarNotesWaveMetrics,
    SimilarNotesWaveResponse, VectorsForNotesResponse,
};
use crate::local_personalizer::{
    CompactSupportScorer, LocalPersonalizerError, RatedVector, RbfKernelRidgeScorer,
    squared_chord_distance,
};
use crate::personalizer_learning::{
    CompactLearningController, CompactTuple, EvidenceIdentity, GladnessRating,
    RbfLearningController, RbfTuple,
};
use crate::representation::{EventId, RepresentationEncoder};
use crate::snapshot::{Error as SnapshotError, Result as SnapshotResult};

const RESPONSE_IDENTITY_DOMAIN: &[u8] = b"oracle-mvp-similar-notes-response-v1\0";
const CANDIDATE_POOL_IDENTITY_DOMAIN: &[u8] = b"oracle-mvp-candidate-pool-v1\0";
const CANDIDATE_TIE_DOMAIN: &[u8] = b"oracle-mvp-candidate-tie-v1\0";

pub const CANDIDATE_DEPTH: usize = 1_024;
const RESERVE_COUNT: usize = 21;

pub type Result<T> = std::result::Result<T, CandidateOrderError>;

#[derive(Debug, Error)]
pub enum CandidateOrderError {
    #[error(transparent)]
    Oracle(#[from] SnapshotError),
    #[error(transparent)]
    Scorer(#[from] LocalPersonalizerError),
    #[error("representation version must not be empty")]
    EmptyRepresentationVersion,
    #[error("{context} representation version `{actual}` does not match `{expected}`")]
    RepresentationVersionMismatch {
        context: &'static str,
        expected: String,
        actual: String,
    },
    #[error("B16 must be finite and non-negative")]
    InvalidB16,
    #[error("a learning batch is already pending for this personalizer")]
    LearningBatchPending,
    #[error("the personalizer has no positive evidence for candidate discovery")]
    NoPositiveSources,
    #[error("invalid similar_notes response for source {source_event_id:?}: {message}")]
    InvalidOracleResponse {
        source_event_id: EventId,
        message: String,
    },
    #[error("invalid vectors_for_notes response: {message}")]
    InvalidVectorResponse { message: String },
    #[error("personalizer evidence vector {event_id:?} is invalid: {message}")]
    InvalidEvidenceVector { event_id: EventId, message: String },
    #[error("candidate-order audit length does not fit u64")]
    AuditLengthOverflow,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, serde::Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CandidateOrderPhase {
    Learning,
    Final,
}

impl CandidateOrderPhase {
    pub const fn primary_count(self) -> usize {
        match self {
            Self::Learning => 20,
            Self::Final => 200,
        }
    }

    pub const fn reserve_count(self) -> usize {
        RESERVE_COUNT
    }

    pub const fn accepted_count(self) -> usize {
        self.primary_count() + self.reserve_count()
    }
}

#[derive(Clone, Debug, PartialEq, serde::Serialize)]
pub struct B16Boundary {
    representation_version: String,
    distance: f64,
}

impl B16Boundary {
    pub fn new(representation_version: impl Into<String>, distance: f64) -> Result<Self> {
        let representation_version = representation_version.into();
        validate_version(&representation_version)?;
        if !distance.is_finite() || distance < 0.0 {
            return Err(CandidateOrderError::InvalidB16);
        }
        Ok(Self {
            representation_version,
            distance,
        })
    }

    pub fn representation_version(&self) -> &str {
        &self.representation_version
    }

    pub fn distance(&self) -> f64 {
        self.distance
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct CandidateOrderRequest {
    phase: CandidateOrderPhase,
    b16: B16Boundary,
    disallowed_event_ids: BTreeSet<EventId>,
}

impl CandidateOrderRequest {
    pub fn new(
        phase: CandidateOrderPhase,
        b16: B16Boundary,
        disallowed_event_ids: BTreeSet<EventId>,
    ) -> Self {
        Self {
            phase,
            b16,
            disallowed_event_ids,
        }
    }

    pub fn phase(&self) -> CandidateOrderPhase {
        self.phase
    }

    pub fn b16(&self) -> &B16Boundary {
        &self.b16
    }

    pub fn disallowed_event_ids(&self) -> &BTreeSet<EventId> {
        &self.disallowed_event_ids
    }
}

/// The public Oracle boundary required by local candidate construction.
///
/// Implementations own the immutable `similar_notes` response cache. Repeating
/// the same `(representation_version, source event, depth)` request must return
/// the same response without another matrix pass. The local builder owns only
/// its shared candidate/document vector cache.
pub trait CandidateOrderOracle {
    fn representation_version(&self) -> &str;

    /// Return exactly one fixed-depth response per request, in request order.
    fn similar_notes_wave(
        &mut self,
        requests: &[SimilarNotesRequest],
        representation_version: &str,
    ) -> SnapshotResult<SimilarNotesWaveResponse>;

    fn vectors_for_notes(
        &mut self,
        note_ids: &[EventId],
        representation_version: &str,
    ) -> SnapshotResult<VectorsForNotesResponse>;
}

impl<E: RepresentationEncoder> CandidateOrderOracle for Fp32OfflineOracle<E> {
    fn representation_version(&self) -> &str {
        Fp32OfflineOracle::representation_version(self)
    }

    fn similar_notes_wave(
        &mut self,
        requests: &[SimilarNotesRequest],
        representation_version: &str,
    ) -> SnapshotResult<SimilarNotesWaveResponse> {
        Fp32OfflineOracle::similar_notes_wave(self, requests, representation_version)
    }

    fn vectors_for_notes(
        &mut self,
        note_ids: &[EventId],
        representation_version: &str,
    ) -> SnapshotResult<VectorsForNotesResponse> {
        Fp32OfflineOracle::vectors_for_notes(self, note_ids, representation_version)
    }
}

/// Shared cache of immutable public candidate/document vectors.
pub struct CandidateVectorCache {
    representation_version: String,
    artifact_rows: Option<(u64, u64)>,
    vectors: BTreeMap<EventId, Vec<f32>>,
}

impl CandidateVectorCache {
    pub fn new(representation_version: impl Into<String>) -> Result<Self> {
        let representation_version = representation_version.into();
        validate_version(&representation_version)?;
        Ok(Self {
            representation_version,
            artifact_rows: None,
            vectors: BTreeMap::new(),
        })
    }

    pub fn representation_version(&self) -> &str {
        &self.representation_version
    }

    pub fn vector_count(&self) -> usize {
        self.vectors.len()
    }

    pub(crate) fn insert_verified_vectors(
        &mut self,
        response: VectorsForNotesResponse,
        requested: &[EventId],
        dimensions: usize,
    ) -> Result<()> {
        let represented_rows = response.represented_rows;
        let total_rows = response.total_rows;
        if represented_rows == 0 || represented_rows != total_rows {
            return Err(CandidateOrderError::InvalidVectorResponse {
                message: format!("representation is incomplete ({represented_rows}/{total_rows})"),
            });
        }
        self.require_rows(represented_rows, total_rows)?;
        validate_vector_response(
            &response,
            &self.representation_version,
            represented_rows,
            total_rows,
            dimensions,
            requested,
        )?;
        let vectors = response
            .vectors
            .into_iter()
            .map(|stored| (stored.event_id, stored.vector))
            .collect();
        self.insert_validated(represented_rows, total_rows, vectors);
        Ok(())
    }

    fn require_rows(&self, represented_rows: u64, total_rows: u64) -> Result<()> {
        if let Some(expected) = self.artifact_rows
            && expected != (represented_rows, total_rows)
        {
            return Err(CandidateOrderError::InvalidVectorResponse {
                message: format!(
                    "artifact rows ({represented_rows}, {total_rows}) differ from cached ({}, {})",
                    expected.0, expected.1
                ),
            });
        }
        Ok(())
    }

    fn insert_validated(
        &mut self,
        represented_rows: u64,
        total_rows: u64,
        vectors: BTreeMap<EventId, Vec<f32>>,
    ) {
        self.artifact_rows = Some((represented_rows, total_rows));
        self.vectors.extend(vectors);
    }
}

#[derive(Clone, Copy, Debug, PartialEq, serde::Serialize)]
#[serde(rename_all = "snake_case", tag = "kind", content = "parameter_tuple")]
pub enum ActivePersonalizerParameters {
    Compact(CompactTuple),
    Rbf(RbfTuple),
}

#[derive(Clone, Debug, PartialEq, serde::Serialize)]
pub struct CandidateSourceAttribution {
    source_event_id: EventId,
    response_identity_sha256: String,
    rank: usize,
    cosine_score: f32,
}

impl CandidateSourceAttribution {
    pub fn source_event_id(&self) -> EventId {
        self.source_event_id
    }

    pub fn response_identity_sha256(&self) -> &str {
        &self.response_identity_sha256
    }

    pub fn rank(&self) -> usize {
        self.rank
    }

    pub fn cosine_score(&self) -> f32 {
        self.cosine_score
    }
}

#[derive(Clone, Debug, PartialEq, serde::Serialize)]
pub struct SourceResponseAudit {
    source_event_id: EventId,
    response_identity_sha256: String,
    candidate_count: usize,
}

impl SourceResponseAudit {
    pub fn source_event_id(&self) -> EventId {
        self.source_event_id
    }

    pub fn response_identity_sha256(&self) -> &str {
        &self.response_identity_sha256
    }

    pub fn candidate_count(&self) -> usize {
        self.candidate_count
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd, serde::Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CandidateExclusionReason {
    ExistingEvidence,
    CallerDisallowed,
}

#[derive(Clone, Debug, PartialEq, serde::Serialize)]
#[serde(rename_all = "snake_case", tag = "kind")]
pub enum CandidateDisposition {
    Excluded {
        reasons: Vec<CandidateExclusionReason>,
    },
    NonPositive {
        raw_score: f64,
        deployed_score: f64,
    },
    Accepted {
        accepted_index: usize,
        raw_score: f64,
        deployed_score: f64,
        tie_break_sha256: [u8; 32],
    },
    NearDuplicate {
        raw_score: f64,
        deployed_score: f64,
        tie_break_sha256: [u8; 32],
        blocker_event_id: EventId,
        blocker_distance: f64,
    },
    NotWalkedAfterBound {
        raw_score: f64,
        deployed_score: f64,
        tie_break_sha256: [u8; 32],
    },
}

#[derive(Clone, Debug, PartialEq, serde::Serialize)]
pub struct CandidateAudit {
    event_id: EventId,
    attributions: Vec<CandidateSourceAttribution>,
    disposition: CandidateDisposition,
}

impl CandidateAudit {
    pub fn event_id(&self) -> EventId {
        self.event_id
    }

    pub fn attributions(&self) -> &[CandidateSourceAttribution] {
        &self.attributions
    }

    pub fn disposition(&self) -> &CandidateDisposition {
        &self.disposition
    }

    pub fn exclusion_reasons(&self) -> &[CandidateExclusionReason] {
        match &self.disposition {
            CandidateDisposition::Excluded { reasons } => reasons,
            _ => &[],
        }
    }

    pub fn is_nonpositive(&self) -> bool {
        matches!(self.disposition, CandidateDisposition::NonPositive { .. })
    }

    pub fn near_duplicate_blocker(&self) -> Option<(EventId, f64)> {
        match self.disposition {
            CandidateDisposition::NearDuplicate {
                blocker_event_id,
                blocker_distance,
                ..
            } => Some((blocker_event_id, blocker_distance)),
            _ => None,
        }
    }
}

#[derive(Clone, Debug, PartialEq, serde::Serialize)]
pub struct FrozenCandidate {
    event_id: EventId,
    vector: Vec<f32>,
    attributions: Vec<CandidateSourceAttribution>,
    raw_score: f64,
    deployed_score: f64,
    tie_break_sha256: [u8; 32],
}

impl FrozenCandidate {
    pub fn event_id(&self) -> EventId {
        self.event_id
    }

    pub fn vector(&self) -> &[f32] {
        &self.vector
    }

    pub fn attributions(&self) -> &[CandidateSourceAttribution] {
        &self.attributions
    }

    pub fn raw_score(&self) -> f64 {
        self.raw_score
    }

    pub fn deployed_score(&self) -> f64 {
        self.deployed_score
    }

    pub fn tie_break_sha256(&self) -> &[u8; 32] {
        &self.tie_break_sha256
    }
}

#[derive(Clone, Debug, PartialEq, serde::Serialize)]
pub struct CandidateOrderAttempt {
    phase: CandidateOrderPhase,
    representation_version: String,
    evidence_identity: EvidenceIdentity,
    active_parameters: ActivePersonalizerParameters,
    b16: B16Boundary,
    discovery_metrics: SimilarNotesWaveMetrics,
    source_responses: Vec<SourceResponseAudit>,
    candidate_pool_identity_sha256: String,
    candidates: Vec<CandidateAudit>,
    accepted: Vec<FrozenCandidate>,
}

impl CandidateOrderAttempt {
    pub fn phase(&self) -> CandidateOrderPhase {
        self.phase
    }

    pub fn representation_version(&self) -> &str {
        &self.representation_version
    }

    pub fn evidence_identity(&self) -> &EvidenceIdentity {
        &self.evidence_identity
    }

    pub fn active_parameters(&self) -> ActivePersonalizerParameters {
        self.active_parameters
    }

    pub fn b16(&self) -> &B16Boundary {
        &self.b16
    }

    pub fn discovery_metrics(&self) -> &SimilarNotesWaveMetrics {
        &self.discovery_metrics
    }

    pub fn source_responses(&self) -> &[SourceResponseAudit] {
        &self.source_responses
    }

    pub fn candidate_pool_identity_sha256(&self) -> &str {
        &self.candidate_pool_identity_sha256
    }

    pub fn candidates(&self) -> &[CandidateAudit] {
        &self.candidates
    }

    pub fn candidate_audit(&self, event_id: EventId) -> Option<&CandidateAudit> {
        self.candidates
            .binary_search_by_key(&event_id, CandidateAudit::event_id)
            .ok()
            .map(|index| &self.candidates[index])
    }

    pub fn accepted(&self) -> &[FrozenCandidate] {
        &self.accepted
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct FrozenCandidateOrder {
    attempt: CandidateOrderAttempt,
}

impl FrozenCandidateOrder {
    pub fn attempt(&self) -> &CandidateOrderAttempt {
        &self.attempt
    }

    pub fn evidence_identity(&self) -> &EvidenceIdentity {
        self.attempt.evidence_identity()
    }

    pub fn accepted(&self) -> &[FrozenCandidate] {
        self.attempt.accepted()
    }

    pub fn primary(&self) -> &[FrozenCandidate] {
        &self.accepted()[..self.attempt.phase.primary_count()]
    }

    pub fn reserve(&self) -> &[FrozenCandidate] {
        &self.accepted()[self.attempt.phase.primary_count()..]
    }

    pub fn candidate_audit(&self, event_id: EventId) -> Option<&CandidateAudit> {
        self.attempt.candidate_audit(event_id)
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct InsufficientCandidateOrder {
    attempt: CandidateOrderAttempt,
    required_count: usize,
}

impl InsufficientCandidateOrder {
    pub fn attempt(&self) -> &CandidateOrderAttempt {
        &self.attempt
    }

    pub fn accepted_count(&self) -> usize {
        self.attempt.accepted.len()
    }

    pub fn required_count(&self) -> usize {
        self.required_count
    }

    pub(crate) fn into_attempt(self) -> CandidateOrderAttempt {
        self.attempt
    }
}

#[derive(Clone, Debug, PartialEq)]
pub enum CandidateOrderOutcome {
    Frozen(FrozenCandidateOrder),
    Insufficient(InsufficientCandidateOrder),
}

pub fn build_compact_candidate_order<O: CandidateOrderOracle>(
    controller: &CompactLearningController,
    oracle: &mut O,
    cache: &mut CandidateVectorCache,
    request: &CandidateOrderRequest,
) -> Result<CandidateOrderOutcome> {
    build_compact_candidate_order_with_tuple(
        controller,
        controller.active_tuple(),
        oracle,
        cache,
        request,
    )
}

pub(crate) fn build_compact_candidate_order_with_tuple<O: CandidateOrderOracle>(
    controller: &CompactLearningController,
    parameter_tuple: CompactTuple,
    oracle: &mut O,
    cache: &mut CandidateVectorCache,
    request: &CandidateOrderRequest,
) -> Result<CandidateOrderOutcome> {
    if controller.pending_batch().is_some() {
        return Err(CandidateOrderError::LearningBatchPending);
    }
    let scorer =
        CompactSupportScorer::new(controller.evidence_vectors(), parameter_tuple.parameters())?;
    build_candidate_order(
        PersonalizerView {
            representation_version: controller.representation_version(),
            evidence_identity: controller.evidence_identity(),
            evidence_event_ids: controller.evidence_event_ids(),
            evidence_ratings: controller.evidence_ratings(),
            evidence_vectors: controller.evidence_vectors(),
            active_parameters: ActivePersonalizerParameters::Compact(parameter_tuple),
        },
        oracle,
        cache,
        request,
        |vector| {
            let score = scorer.score(vector)?;
            Ok(CandidateScore {
                raw: score,
                deployed: score,
            })
        },
    )
}

pub fn build_rbf_candidate_order<O: CandidateOrderOracle>(
    controller: &RbfLearningController,
    oracle: &mut O,
    cache: &mut CandidateVectorCache,
    request: &CandidateOrderRequest,
) -> Result<CandidateOrderOutcome> {
    if controller.pending_batch().is_some() {
        return Err(CandidateOrderError::LearningBatchPending);
    }
    let scorer = RbfKernelRidgeScorer::fit(
        controller.evidence_vectors(),
        controller.active_tuple().parameters(),
    )?;
    build_candidate_order(
        PersonalizerView {
            representation_version: controller.representation_version(),
            evidence_identity: controller.evidence_identity(),
            evidence_event_ids: controller.evidence_event_ids(),
            evidence_ratings: controller.evidence_ratings(),
            evidence_vectors: controller.evidence_vectors(),
            active_parameters: ActivePersonalizerParameters::Rbf(controller.active_tuple()),
        },
        oracle,
        cache,
        request,
        |vector| {
            let score = scorer.score(vector)?;
            Ok(CandidateScore {
                raw: score.raw,
                deployed: score.deployed,
            })
        },
    )
}

#[derive(Clone, Copy)]
struct CandidateScore {
    raw: f64,
    deployed: f64,
}

struct ScoredCandidate {
    event_id: EventId,
    raw_score: f64,
    deployed_score: f64,
    tie_break_sha256: [u8; 32],
}

struct PersonalizerView<'a> {
    representation_version: &'a str,
    evidence_identity: &'a EvidenceIdentity,
    evidence_event_ids: &'a [EventId],
    evidence_ratings: &'a [GladnessRating],
    evidence_vectors: &'a [RatedVector],
    active_parameters: ActivePersonalizerParameters,
}

fn build_candidate_order<O, F>(
    personalizer: PersonalizerView<'_>,
    oracle: &mut O,
    cache: &mut CandidateVectorCache,
    request: &CandidateOrderRequest,
    mut score: F,
) -> Result<CandidateOrderOutcome>
where
    O: CandidateOrderOracle,
    F: FnMut(&[f32]) -> std::result::Result<CandidateScore, LocalPersonalizerError>,
{
    let representation_version = personalizer.representation_version;
    require_version(
        "B16",
        representation_version,
        request.b16.representation_version(),
    )?;
    require_version(
        "vector cache",
        representation_version,
        cache.representation_version(),
    )?;
    require_version(
        "Oracle",
        representation_version,
        oracle.representation_version(),
    )?;

    let dimensions = personalizer
        .evidence_vectors
        .first()
        .expect("learning controllers always contain evidence")
        .vector()
        .len();
    for (event_id, vector) in personalizer
        .evidence_event_ids
        .iter()
        .zip(personalizer.evidence_vectors)
    {
        validate_representation_vector(vector.vector(), dimensions).map_err(|message| {
            CandidateOrderError::InvalidEvidenceVector {
                event_id: *event_id,
                message,
            }
        })?;
    }

    let positive_sources = personalizer
        .evidence_event_ids
        .iter()
        .zip(personalizer.evidence_ratings)
        .filter_map(|(event_id, rating)| (rating.value() >= 5).then_some(*event_id))
        .collect::<BTreeSet<_>>();
    if positive_sources.is_empty() {
        return Err(CandidateOrderError::NoPositiveSources);
    }
    let requests = positive_sources
        .iter()
        .map(|event_id| SimilarNotesRequest {
            note_id: *event_id,
            candidate_depth: CANDIDATE_DEPTH,
        })
        .collect::<Vec<_>>();
    let wave = oracle.similar_notes_wave(&requests, representation_version)?;
    if wave.responses.len() != requests.len() {
        return Err(CandidateOrderError::InvalidOracleResponse {
            source_event_id: requests[0].note_id,
            message: format!(
                "wave returned {} responses for {} requests",
                wave.responses.len(),
                requests.len()
            ),
        });
    }

    let mut expected_rows = None;
    let mut source_responses = Vec::with_capacity(requests.len());
    let mut attributions_by_event: BTreeMap<EventId, Vec<CandidateSourceAttribution>> =
        BTreeMap::new();
    for (request, response) in requests.iter().zip(&wave.responses) {
        validate_similar_notes_response(
            request.note_id,
            response,
            representation_version,
            &mut expected_rows,
        )?;
        let response_identity = response_identity(request.note_id, response)?;
        source_responses.push(SourceResponseAudit {
            source_event_id: request.note_id,
            response_identity_sha256: response_identity.clone(),
            candidate_count: response.candidates.len(),
        });
        for candidate in &response.candidates {
            attributions_by_event
                .entry(candidate.event_id)
                .or_default()
                .push(CandidateSourceAttribution {
                    source_event_id: request.note_id,
                    response_identity_sha256: response_identity.clone(),
                    rank: candidate.rank,
                    cosine_score: candidate.cosine_score,
                });
        }
    }
    let (represented_rows, total_rows) =
        expected_rows.expect("at least one source response was validated");
    cache.require_rows(represented_rows, total_rows)?;
    source_responses.sort_by_key(SourceResponseAudit::source_event_id);
    for attributions in attributions_by_event.values_mut() {
        attributions.sort_by(attribution_order);
    }
    let candidate_pool_identity_sha256 =
        candidate_pool_identity(representation_version, &attributions_by_event)?;

    let evidence_ids = personalizer
        .evidence_event_ids
        .iter()
        .copied()
        .collect::<BTreeSet<_>>();
    let mut candidate_audits = BTreeMap::new();
    let mut eligible_ids = Vec::new();
    for (event_id, attributions) in &attributions_by_event {
        let mut reasons = Vec::new();
        if evidence_ids.contains(event_id) {
            reasons.push(CandidateExclusionReason::ExistingEvidence);
        }
        if request.disallowed_event_ids.contains(event_id) {
            reasons.push(CandidateExclusionReason::CallerDisallowed);
        }
        if reasons.is_empty() {
            eligible_ids.push(*event_id);
        } else {
            candidate_audits.insert(
                *event_id,
                CandidateAudit {
                    event_id: *event_id,
                    attributions: attributions.clone(),
                    disposition: CandidateDisposition::Excluded { reasons },
                },
            );
        }
    }

    fill_vector_cache(
        oracle,
        cache,
        representation_version,
        represented_rows,
        total_rows,
        dimensions,
        &eligible_ids,
    )?;

    let mut scored = Vec::new();
    for event_id in eligible_ids {
        let vector = cache
            .vectors
            .get(&event_id)
            .expect("all eligible vectors were cached");
        let CandidateScore { raw, deployed } = score(vector)?;
        if !raw.is_finite() || !deployed.is_finite() {
            return Err(LocalPersonalizerError::NonFiniteScore.into());
        }
        let attributions = attributions_by_event
            .get(&event_id)
            .expect("union attribution exists")
            .clone();
        if deployed <= 0.0 {
            candidate_audits.insert(
                event_id,
                CandidateAudit {
                    event_id,
                    attributions,
                    disposition: CandidateDisposition::NonPositive {
                        raw_score: raw,
                        deployed_score: deployed,
                    },
                },
            );
            continue;
        }
        let tie_break_sha256 = candidate_tie(representation_version, event_id);
        candidate_audits.insert(
            event_id,
            CandidateAudit {
                event_id,
                attributions,
                disposition: CandidateDisposition::NotWalkedAfterBound {
                    raw_score: raw,
                    deployed_score: deployed,
                    tie_break_sha256,
                },
            },
        );
        scored.push(ScoredCandidate {
            event_id,
            raw_score: raw,
            deployed_score: deployed,
            tie_break_sha256,
        });
    }
    scored.sort_by(scored_candidate_order);

    let required_count = request.phase.accepted_count();
    let mut accepted: Vec<FrozenCandidate> = Vec::with_capacity(required_count);
    for candidate in scored {
        if accepted.len() == required_count {
            break;
        }
        let vector = cache
            .vectors
            .get(&candidate.event_id)
            .expect("scored vector remains cached");
        let mut blocker = None;
        for accepted_candidate in &accepted {
            let distance = squared_chord_distance(vector, accepted_candidate.vector())?.sqrt();
            if distance < request.b16.distance {
                blocker = Some((accepted_candidate.event_id(), distance));
                break;
            }
        }
        let audit = candidate_audits
            .get_mut(&candidate.event_id)
            .expect("scored candidate audit exists");
        if let Some((blocker_event_id, blocker_distance)) = blocker {
            audit.disposition = CandidateDisposition::NearDuplicate {
                raw_score: candidate.raw_score,
                deployed_score: candidate.deployed_score,
                tie_break_sha256: candidate.tie_break_sha256,
                blocker_event_id,
                blocker_distance,
            };
            continue;
        }
        let accepted_index = accepted.len();
        audit.disposition = CandidateDisposition::Accepted {
            accepted_index,
            raw_score: candidate.raw_score,
            deployed_score: candidate.deployed_score,
            tie_break_sha256: candidate.tie_break_sha256,
        };
        accepted.push(FrozenCandidate {
            event_id: candidate.event_id,
            vector: vector.clone(),
            attributions: audit.attributions.clone(),
            raw_score: candidate.raw_score,
            deployed_score: candidate.deployed_score,
            tie_break_sha256: candidate.tie_break_sha256,
        });
    }

    let attempt = CandidateOrderAttempt {
        phase: request.phase,
        representation_version: representation_version.to_owned(),
        evidence_identity: personalizer.evidence_identity.clone(),
        active_parameters: personalizer.active_parameters,
        b16: request.b16.clone(),
        discovery_metrics: wave.metrics,
        source_responses,
        candidate_pool_identity_sha256,
        candidates: candidate_audits.into_values().collect(),
        accepted,
    };
    if attempt.accepted.len() == required_count {
        Ok(CandidateOrderOutcome::Frozen(FrozenCandidateOrder {
            attempt,
        }))
    } else {
        Ok(CandidateOrderOutcome::Insufficient(
            InsufficientCandidateOrder {
                attempt,
                required_count,
            },
        ))
    }
}

fn fill_vector_cache<O: CandidateOrderOracle>(
    oracle: &mut O,
    cache: &mut CandidateVectorCache,
    representation_version: &str,
    represented_rows: u64,
    total_rows: u64,
    dimensions: usize,
    eligible_ids: &[EventId],
) -> Result<()> {
    let missing = eligible_ids
        .iter()
        .copied()
        .filter(|event_id| !cache.vectors.contains_key(event_id))
        .collect::<Vec<_>>();
    if missing.is_empty() {
        if cache.artifact_rows.is_none() {
            cache.artifact_rows = Some((represented_rows, total_rows));
        }
        return Ok(());
    }
    let response = oracle.vectors_for_notes(&missing, representation_version)?;
    validate_vector_response(
        &response,
        representation_version,
        represented_rows,
        total_rows,
        dimensions,
        &missing,
    )?;
    let staged = response
        .vectors
        .into_iter()
        .map(|stored| (stored.event_id, stored.vector))
        .collect();
    cache.insert_validated(represented_rows, total_rows, staged);
    Ok(())
}

fn validate_similar_notes_response(
    source_event_id: EventId,
    response: &SimilarNotesResponse,
    representation_version: &str,
    expected_rows: &mut Option<(u64, u64)>,
) -> Result<()> {
    let invalid = |message: String| CandidateOrderError::InvalidOracleResponse {
        source_event_id,
        message,
    };
    if response.representation_version != representation_version {
        return Err(invalid(format!(
            "representation version `{}` differs from `{representation_version}`",
            response.representation_version
        )));
    }
    if !response.complete
        || response.represented_rows == 0
        || response.represented_rows != response.total_rows
    {
        return Err(invalid(format!(
            "representation is incomplete ({}/{})",
            response.represented_rows, response.total_rows
        )));
    }
    if let Some(expected) = expected_rows {
        if *expected != (response.represented_rows, response.total_rows) {
            return Err(invalid(
                "artifact row identity differs across sources".to_owned(),
            ));
        }
    } else {
        *expected_rows = Some((response.represented_rows, response.total_rows));
    }
    let expected_candidate_count = usize::try_from(response.total_rows.saturating_sub(1))
        .unwrap_or(usize::MAX)
        .min(CANDIDATE_DEPTH);
    if response.candidates.len() != expected_candidate_count {
        return Err(invalid(format!(
            "response contains {} candidates instead of {expected_candidate_count} for depth {CANDIDATE_DEPTH}",
            response.candidates.len(),
        )));
    }
    let mut ids = BTreeSet::new();
    for (offset, candidate) in response.candidates.iter().enumerate() {
        let expected_rank = offset + 1;
        if candidate.rank != expected_rank {
            return Err(invalid(format!(
                "candidate at offset {offset} has rank {} instead of {expected_rank}",
                candidate.rank
            )));
        }
        if !candidate.cosine_score.is_finite() {
            return Err(invalid(format!(
                "candidate at rank {expected_rank} has a non-finite cosine score"
            )));
        }
        if candidate.event_id == source_event_id {
            return Err(invalid("response contains its source event".to_owned()));
        }
        if !ids.insert(candidate.event_id) {
            return Err(invalid(format!(
                "candidate {:?} appears more than once",
                candidate.event_id
            )));
        }
    }
    Ok(())
}

fn validate_vector_response(
    response: &VectorsForNotesResponse,
    representation_version: &str,
    represented_rows: u64,
    total_rows: u64,
    dimensions: usize,
    requested: &[EventId],
) -> Result<()> {
    let invalid = |message: String| CandidateOrderError::InvalidVectorResponse { message };
    if response.representation_version != representation_version {
        return Err(invalid(format!(
            "representation version `{}` differs from `{representation_version}`",
            response.representation_version
        )));
    }
    if !response.complete
        || response.represented_rows != represented_rows
        || response.total_rows != total_rows
    {
        return Err(invalid(format!(
            "artifact rows ({}, {}) differ from expected ({represented_rows}, {total_rows})",
            response.represented_rows, response.total_rows
        )));
    }
    if response.vectors.len() != requested.len() {
        return Err(invalid(format!(
            "returned {} vectors for {} requested events",
            response.vectors.len(),
            requested.len()
        )));
    }
    let mut staged_ids = BTreeSet::new();
    for (offset, (stored, requested_id)) in response.vectors.iter().zip(requested).enumerate() {
        if stored.event_id != *requested_id {
            return Err(invalid(format!(
                "vector at offset {offset} belongs to {:?} instead of {:?}",
                stored.event_id, requested_id
            )));
        }
        if !staged_ids.insert(stored.event_id) {
            return Err(invalid(format!(
                "vector for {:?} appears more than once",
                stored.event_id
            )));
        }
        validate_representation_vector(&stored.vector, dimensions).map_err(|message| {
            invalid(format!(
                "vector for {:?} is invalid: {message}",
                stored.event_id
            ))
        })?;
    }
    Ok(())
}

fn response_identity(source_event_id: EventId, response: &SimilarNotesResponse) -> Result<String> {
    let mut bytes = Vec::new();
    bytes.extend_from_slice(RESPONSE_IDENTITY_DOMAIN);
    append_string(&mut bytes, &response.representation_version)?;
    bytes.extend_from_slice(&source_event_id);
    append_usize(&mut bytes, CANDIDATE_DEPTH)?;
    bytes.extend_from_slice(&response.represented_rows.to_le_bytes());
    bytes.extend_from_slice(&response.total_rows.to_le_bytes());
    bytes.push(u8::from(response.complete));
    append_usize(&mut bytes, response.candidates.len())?;
    for candidate in &response.candidates {
        bytes.extend_from_slice(&candidate.event_id);
        append_usize(&mut bytes, candidate.rank)?;
        bytes.extend_from_slice(&candidate.cosine_score.to_bits().to_le_bytes());
    }
    Ok(hash_bytes(&bytes))
}

fn candidate_pool_identity(
    representation_version: &str,
    attributions_by_event: &BTreeMap<EventId, Vec<CandidateSourceAttribution>>,
) -> Result<String> {
    let mut bytes = Vec::new();
    bytes.extend_from_slice(CANDIDATE_POOL_IDENTITY_DOMAIN);
    append_string(&mut bytes, representation_version)?;
    append_usize(&mut bytes, attributions_by_event.len())?;
    for (event_id, attributions) in attributions_by_event {
        bytes.extend_from_slice(event_id);
        append_usize(&mut bytes, attributions.len())?;
        for attribution in attributions {
            bytes.extend_from_slice(&attribution.source_event_id);
            append_string(&mut bytes, &attribution.response_identity_sha256)?;
            append_usize(&mut bytes, attribution.rank)?;
            bytes.extend_from_slice(&attribution.cosine_score.to_bits().to_le_bytes());
        }
    }
    Ok(hash_bytes(&bytes))
}

fn candidate_tie(representation_version: &str, event_id: EventId) -> [u8; 32] {
    let mut hasher = Sha256::new();
    hasher.update(CANDIDATE_TIE_DOMAIN);
    hasher.update(
        u64::try_from(representation_version.len())
            .expect("representation version length fits u64")
            .to_le_bytes(),
    );
    hasher.update(representation_version.as_bytes());
    hasher.update(event_id);
    hasher.finalize().into()
}

fn append_string(bytes: &mut Vec<u8>, value: &str) -> Result<()> {
    append_usize(bytes, value.len())?;
    bytes.extend_from_slice(value.as_bytes());
    Ok(())
}

fn append_usize(bytes: &mut Vec<u8>, value: usize) -> Result<()> {
    bytes.extend_from_slice(
        &u64::try_from(value)
            .map_err(|_| CandidateOrderError::AuditLengthOverflow)?
            .to_le_bytes(),
    );
    Ok(())
}

fn attribution_order(
    left: &CandidateSourceAttribution,
    right: &CandidateSourceAttribution,
) -> Ordering {
    left.source_event_id
        .cmp(&right.source_event_id)
        .then_with(|| left.rank.cmp(&right.rank))
        .then_with(|| left.cosine_score.total_cmp(&right.cosine_score))
        .then_with(|| {
            left.response_identity_sha256
                .cmp(&right.response_identity_sha256)
        })
}

fn scored_candidate_order(left: &ScoredCandidate, right: &ScoredCandidate) -> Ordering {
    right
        .deployed_score
        .total_cmp(&left.deployed_score)
        .then_with(|| left.tie_break_sha256.cmp(&right.tie_break_sha256))
        .then_with(|| left.event_id.cmp(&right.event_id))
}

fn validate_version(representation_version: &str) -> Result<()> {
    if representation_version.is_empty() {
        Err(CandidateOrderError::EmptyRepresentationVersion)
    } else {
        Ok(())
    }
}

fn require_version(context: &'static str, expected: &str, actual: &str) -> Result<()> {
    if actual == expected {
        Ok(())
    } else {
        Err(CandidateOrderError::RepresentationVersionMismatch {
            context,
            expected: expected.to_owned(),
            actual: actual.to_owned(),
        })
    }
}

fn validate_representation_vector(
    vector: &[f32],
    dimensions: usize,
) -> std::result::Result<(), String> {
    if vector.len() != dimensions || vector.iter().any(|value| !value.is_finite()) {
        return Err("invalid width or non-finite value".to_owned());
    }
    let norm = vector.iter().map(|value| value * value).sum::<f32>().sqrt();
    if (norm - 1.0).abs() > 1e-4 {
        return Err(format!("not L2-normalized: {norm}"));
    }
    Ok(())
}
