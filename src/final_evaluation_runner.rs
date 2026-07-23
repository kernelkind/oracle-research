//! Durable presentation and reporting for the frozen Phase 4 evaluation.

use std::collections::{BTreeMap, BTreeSet};
use std::fs::{self, File, OpenOptions};
use std::io::{BufWriter, Write};
use std::path::{Path, PathBuf};

use nostrdb::{Ndb, Transaction};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

use crate::adaptive_learning::CompletedAdaptiveLearning;
use crate::artifact::hash_bytes;
use crate::candidate_order::CandidateOrderOracle;
use crate::evaluator::{
    CompletionView, EvaluatorDecision, EvaluatorSubmission, EvaluatorUi, RATING_ANCHORS,
    RATING_QUESTION, RatingOutcome, RatingView, RecoveryOutcome, RecoveryView, RestOutcome,
    RestView, WRONG_LANGUAGE_RULE,
};
use crate::evaluator_tui::FullScreenEvaluator;
use crate::final_evaluation::FinalEvaluationCoordinator;
use crate::final_evaluation_report::{
    FinalEvaluationReportProvenance, build_final_evaluation_report,
};
use crate::fp32_oracle::{SimilarNotesRequest, SimilarNotesWaveResponse, VectorsForNotesResponse};
use crate::personalizer_learning::GladnessRating;
use crate::quota_resolution::{
    EventLanguageOutcome, LanguageEligibility, PresentationWave, QuotaResolutionProgress,
};
use crate::representation::EventId;
use crate::snapshot::{
    Error, Result, Validation, io_error, ndb_error, open_existing_ndb, read_manifest,
    require_directory,
};

const SESSION_SCHEMA_VERSION: u32 = 2;
const ORDERS_SCHEMA_VERSION: u32 = 1;
const SHUFFLE_POLICY: &str = "phase4-final-sha256-concealed-v1";
const ORACLE_CACHE_POLICY: &str = "phase4-final-request-response-cache-v1";
const EVALUATOR_PROTOCOL: &str = "phase4-final-gladness-confirmed-v1";
const REST_INTERVAL: usize = 20;
const MAXIMUM_WRONG_LANGUAGE_PRESENTATIONS: usize = 21;

/// Immutable inputs and private outputs for one final evaluation.
#[derive(Clone, Debug)]
pub struct FinalEvaluationRunnerConfig {
    /// Raw kind-1 NostrDB used only to display stored note content.
    pub corpus_path: PathBuf,
    /// Already-verified immutable identity of that corpus.
    pub corpus_identity: String,
    /// Small mutable, atomically replaced evaluator transcript.
    pub session_path: PathBuf,
    /// Immutable serialized final orders and construction audit.
    pub frozen_orders_path: PathBuf,
    /// Immutable final result written only after both quotas resolve.
    pub report_path: PathBuf,
    /// Durable public-response cache used to reconstruct orders without a new
    /// full-matrix scan after every evaluator pause.
    pub oracle_cache_path: PathBuf,
    /// SHA-256 identity of the completed Phase 3 handoff.
    pub phase3_handoff_identity_sha256: String,
    /// SHA-256 identity of the exact guarded Phase 4 launch receipt.
    pub guarded_launch_identity_sha256: String,
    /// Frozen public geometry artifact identity.
    pub geometry_version: String,
}

/// Result of one terminal invocation.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum FinalEvaluationRunnerOutcome {
    /// The evaluator paused; every accepted decision is durable.
    Paused,
    /// Both frozen 200-rating result sets and the final report are complete.
    Complete,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
struct StaticBinding {
    corpus_identity: String,
    representation_version: String,
    geometry_version: String,
    phase3_handoff_identity_sha256: String,
    guarded_launch_identity_sha256: String,
    frozen_orders_identity_sha256: String,
    evaluator_protocol_identity_sha256: String,
    oracle_cache_policy: String,
    shuffle_policy: String,
    rest_interval: usize,
    maximum_wrong_language_presentations: usize,
    required_rating_count: usize,
    mean_rating_sum_threshold: u16,
    maximum_low_ratings: usize,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
struct SessionBinding {
    fixed: StaticBinding,
    identity_sha256: String,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
enum SessionPhase {
    Evaluating,
    Complete,
    Failed,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
struct FinalEvaluationSession {
    schema_version: u32,
    binding: SessionBinding,
    phase: SessionPhase,
    waves: Vec<WaveTranscript>,
    pending_presentation: Option<PendingPresentation>,
    rest_checkpoints: Vec<RestCheckpoint>,
    pause_checkpoints: Vec<PauseCheckpoint>,
    pause_reason: Option<String>,
    completion: Option<CompletionSeal>,
    failure: Option<FailureSeal>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
struct WaveTranscript {
    wave_id: u64,
    coordinator_event_ids: Vec<EventId>,
    presentation_order: Vec<EventId>,
    decisions: Vec<StoredDecision>,
    submitted: bool,
    decision_checksum_sha256: String,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case", tag = "outcome")]
enum StoredDecision {
    Rated { event_id: EventId, rating: u8 },
    WrongLanguage { event_id: EventId },
}

impl StoredDecision {
    const fn event_id(self) -> EventId {
        match self {
            Self::Rated { event_id, .. } | Self::WrongLanguage { event_id } => event_id,
        }
    }

    const fn language(self) -> LanguageEligibility {
        match self {
            Self::Rated { .. } => LanguageEligibility::Eligible,
            Self::WrongLanguage { .. } => LanguageEligibility::WrongLanguage,
        }
    }

    const fn rating(self) -> Option<u8> {
        match self {
            Self::Rated { rating, .. } => Some(rating),
            Self::WrongLanguage { .. } => None,
        }
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
struct PendingPresentation {
    wave_id: u64,
    event_id: EventId,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
struct RestCheckpoint {
    after_presentations: usize,
    continued: bool,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
struct PauseCheckpoint {
    after_presentations: usize,
    reason: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
struct CompletionSeal {
    report_sha256: String,
    evaluator_transcript_identity_sha256: String,
    quota_audit_identity_sha256: String,
    compact_ratings: usize,
    rbf_ratings: usize,
    unique_presentations: usize,
    wrong_language_presentations: usize,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
struct FailureSeal {
    reason: String,
    after_presentations: usize,
}

#[derive(Serialize)]
struct EvaluatorTranscript<'a> {
    schema_version: u32,
    binding: &'a SessionBinding,
    waves: &'a [WaveTranscript],
    pending_presentation: Option<PendingPresentation>,
    rest_checkpoints: &'a [RestCheckpoint],
    pause_checkpoints: &'a [PauseCheckpoint],
    pause_reason: &'a Option<String>,
}

#[derive(Serialize)]
struct WaveDecisionSeal<'a> {
    wave_id: u64,
    coordinator_event_ids: &'a [EventId],
    presentation_order: &'a [EventId],
    decisions: &'a [StoredDecision],
    submitted: bool,
}

struct FinalReportArtifact {
    bytes: Vec<u8>,
    completion: CompletionSeal,
}

#[derive(Serialize)]
struct FrozenOrdersSidecar<'a> {
    schema_version: u32,
    corpus_identity: &'a str,
    representation_version: &'a str,
    geometry_version: &'a str,
    phase3_handoff_identity_sha256: &'a str,
    compact_order: &'a crate::candidate_order::FrozenCandidateOrder,
    rbf_order: &'a crate::candidate_order::FrozenCandidateOrder,
    initial_quota_audit: &'a [crate::quota_resolution::QuotaAuditEvent],
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
struct SimilarWaveCacheKey {
    policy: String,
    call_ordinal: usize,
    representation_version: String,
    requests: Vec<SimilarNotesRequest>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
struct SimilarWaveCacheEnvelope {
    key: SimilarWaveCacheKey,
    response_sha256: String,
    response: SimilarNotesWaveResponse,
}

#[derive(Serialize)]
struct BorrowedSimilarWaveCacheEnvelope<'a> {
    key: &'a SimilarWaveCacheKey,
    response_sha256: &'a str,
    response: &'a SimilarNotesWaveResponse,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
struct VectorCacheKey {
    policy: String,
    representation_version: String,
    note_ids: Vec<EventId>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
struct VectorCacheEnvelope {
    key: VectorCacheKey,
    response_sha256: String,
    response: VectorsForNotesResponse,
}

#[derive(Serialize)]
struct BorrowedVectorCacheEnvelope<'a> {
    key: &'a VectorCacheKey,
    response_sha256: &'a str,
    response: &'a VectorsForNotesResponse,
}

struct FinalEvaluationOracle<'a, O> {
    inner: &'a mut O,
    representation_version: String,
    cache_path: PathBuf,
    wave_call_cursor: usize,
    allow_oracle_work: bool,
}

struct CacheOnlyOracle {
    representation_version: String,
}

/// Run Phase 4 with the production full-screen evaluator.
pub fn run_final_evaluation_tui<O>(
    config: &FinalEvaluationRunnerConfig,
    completed_learning: Box<CompletedAdaptiveLearning>,
    oracle: &mut O,
) -> Result<FinalEvaluationRunnerOutcome>
where
    O: CandidateOrderOracle,
{
    let mut evaluator = FullScreenEvaluator::new()
        .map_err(|source| io_error("initialize", "<terminal>", source))?;
    run_final_evaluation(config, completed_learning, oracle, &mut evaluator)
}

/// Resume a frozen Phase 4 session from its durable public-response cache.
///
/// No embedding encoder or full-matrix Oracle is opened on this path.
pub fn resume_final_evaluation_tui(
    config: &FinalEvaluationRunnerConfig,
    completed_learning: Box<CompletedAdaptiveLearning>,
) -> Result<FinalEvaluationRunnerOutcome> {
    let mut evaluator = FullScreenEvaluator::new()
        .map_err(|source| io_error("initialize", "<terminal>", source))?;
    resume_final_evaluation(config, completed_learning, &mut evaluator)
}

/// Resume a frozen Phase 4 session without an Oracle backend.
pub fn resume_final_evaluation<U>(
    config: &FinalEvaluationRunnerConfig,
    completed_learning: Box<CompletedAdaptiveLearning>,
    evaluator: &mut U,
) -> Result<FinalEvaluationRunnerOutcome>
where
    U: EvaluatorUi,
{
    if !config.frozen_orders_path.exists() {
        return Err(Error::ArtifactMissing(config.frozen_orders_path.clone()));
    }
    let representation_version = completed_learning
        .compact_controller()
        .representation_version()
        .to_owned();
    let mut oracle = CacheOnlyOracle {
        representation_version,
    };
    run_final_evaluation(config, completed_learning, &mut oracle, evaluator)
}

/// Start or exactly resume the frozen final evaluation.
pub fn run_final_evaluation<O, U>(
    config: &FinalEvaluationRunnerConfig,
    completed_learning: Box<CompletedAdaptiveLearning>,
    oracle: &mut O,
    evaluator: &mut U,
) -> Result<FinalEvaluationRunnerOutcome>
where
    O: CandidateOrderOracle,
    U: EvaluatorUi,
{
    validate_config(config, &completed_learning, oracle)?;
    let _session_lock = acquire_session_lock(&config.session_path)?;
    if config.session_path.exists() && !config.frozen_orders_path.exists() {
        return Err(Error::ArtifactMissing(config.frozen_orders_path.clone()));
    }
    if !config.session_path.exists() && config.report_path.exists() {
        return Err(Error::ExperimentState(
            "a Phase 4 report exists without its durable session".to_owned(),
        ));
    }

    let allow_oracle_work = !config.session_path.exists() && !config.frozen_orders_path.exists();
    prepare_private_cache_directory(&config.oracle_cache_path)?;
    let mut durable_oracle =
        FinalEvaluationOracle::new(oracle, config.oracle_cache_path.clone(), allow_oracle_work)?;
    let mut coordinator =
        FinalEvaluationCoordinator::begin(completed_learning, &mut durable_oracle)
            .map_err(|error| Error::ExperimentState(error.to_string()))?;
    let orders_bytes = frozen_orders_bytes(config, &coordinator)?;
    let orders_identity = hash_bytes(&orders_bytes);
    publish_or_verify_immutable(&config.frozen_orders_path, &orders_bytes)?;
    let binding = build_binding(config, &coordinator, orders_identity)?;
    let mut session = load_or_create_session(config, binding)?;

    if session.phase == SessionPhase::Failed {
        let failure = session.failure.as_ref().ok_or_else(|| {
            Error::ExperimentState("failed Phase 4 session has no failure record".to_owned())
        })?;
        return Err(Error::ExperimentState(failure.reason.clone()));
    }

    replay_session(&mut coordinator, &session)?;
    if session.phase == SessionPhase::Complete {
        verify_completed_session(config, coordinator, &session)?;
        evaluator
            .complete(CompletionView::new(stored_presentation_count(&session)))
            .map_err(|source| io_error("write", "<terminal-output>", source))?;
        return Ok(FinalEvaluationRunnerOutcome::Complete);
    }
    if coordinator.progress() == QuotaResolutionProgress::Complete {
        return complete_session(config, coordinator, &mut session, evaluator);
    }

    if !show_preparing(config, &mut session, evaluator)? {
        return Ok(FinalEvaluationRunnerOutcome::Paused);
    }

    let mut corpus = None;
    loop {
        match coordinator.progress() {
            QuotaResolutionProgress::AwaitingLanguage => {
                ensure_current_wave(config, &coordinator, &mut session)?;
                if !collect_current_wave(config, &mut corpus, &mut session, evaluator)? {
                    return Ok(FinalEvaluationRunnerOutcome::Paused);
                }
                let wave_index = session.waves.len().checked_sub(1).ok_or_else(|| {
                    Error::Invariant("complete presentation wave is missing".to_owned())
                })?;
                let wave_id = session.waves[wave_index].wave_id;
                let outcomes = language_outcomes(&session.waves[wave_index])?;
                coordinator
                    .submit_language_outcomes(wave_id, outcomes)
                    .map_err(|error| Error::ExperimentState(error.to_string()))?;
                session.waves[wave_index].submitted = true;
                refresh_wave_decision_checksum(&mut session.waves[wave_index])?;
                save_session(&config.session_path, &session)?;
                if coordinator.language_delta().wrong_language_presentations()
                    > MAXIMUM_WRONG_LANGUAGE_PRESENTATIONS
                {
                    return fail_session(
                        config,
                        &mut session,
                        "final evaluation exceeded 21 wrong-language presentations",
                    );
                }
                if coordinator.progress() == QuotaResolutionProgress::AwaitingLanguage
                    && !show_preparing(config, &mut session, evaluator)?
                {
                    return Ok(FinalEvaluationRunnerOutcome::Paused);
                }
            }
            QuotaResolutionProgress::Complete => {
                return complete_session(config, coordinator, &mut session, evaluator);
            }
            QuotaResolutionProgress::Failed => {
                let reason = coordinator
                    .failure()
                    .map(|failure| format!("final quota resolution failed: {failure:?}"))
                    .unwrap_or_else(|| "final quota resolution failed without a reason".to_owned());
                return fail_session(config, &mut session, &reason);
            }
        }
    }
}

fn validate_config<O: CandidateOrderOracle>(
    config: &FinalEvaluationRunnerConfig,
    completed: &CompletedAdaptiveLearning,
    oracle: &O,
) -> Result<()> {
    if !config
        .corpus_identity
        .strip_prefix("sha256:")
        .is_some_and(|value| {
            value.len() == 64 && value.bytes().all(|byte| byte.is_ascii_hexdigit())
        })
    {
        return Err(Error::ExperimentState(
            "final evaluation corpus identity is not a SHA-256 content identity".to_owned(),
        ));
    }
    for (label, value) in [
        (
            "Phase 3 handoff identity",
            config.phase3_handoff_identity_sha256.as_str(),
        ),
        (
            "guarded Phase 4 launch identity",
            config.guarded_launch_identity_sha256.as_str(),
        ),
        ("geometry version", config.geometry_version.as_str()),
    ] {
        require_sha256(value, label)?;
    }
    if completed.compact_controller().representation_version()
        != completed.rbf_controller().representation_version()
        || completed.compact_controller().representation_version()
            != oracle.representation_version()
    {
        return Err(Error::ExperimentState(
            "Phase 3 handoff and Oracle use different representations".to_owned(),
        ));
    }
    require_directory(&config.corpus_path)?;
    let outputs = [
        config.session_path.as_path(),
        config.frozen_orders_path.as_path(),
        config.report_path.as_path(),
    ];
    if outputs[0] == outputs[1] || outputs[0] == outputs[2] || outputs[1] == outputs[2] {
        return Err(Error::ExperimentState(
            "Phase 4 session, order, and report paths must be distinct".to_owned(),
        ));
    }
    if outputs
        .iter()
        .any(|output| output.starts_with(&config.corpus_path))
        || config.oracle_cache_path.starts_with(&config.corpus_path)
    {
        return Err(Error::ExperimentState(
            "Phase 4 private outputs must not be inside the display corpus".to_owned(),
        ));
    }
    if outputs
        .iter()
        .any(|output| output.starts_with(&config.oracle_cache_path))
        || outputs
            .iter()
            .any(|output| config.oracle_cache_path.starts_with(output))
    {
        return Err(Error::ExperimentState(
            "Phase 4 Oracle cache must not overlap another output".to_owned(),
        ));
    }
    Ok(())
}

fn require_sha256(value: &str, label: &str) -> Result<()> {
    if value.len() != 64 || !value.bytes().all(|byte| byte.is_ascii_hexdigit()) {
        return Err(Error::ExperimentState(format!(
            "{label} is not a SHA-256 identity"
        )));
    }
    Ok(())
}

fn frozen_orders_bytes(
    config: &FinalEvaluationRunnerConfig,
    coordinator: &FinalEvaluationCoordinator,
) -> Result<Vec<u8>> {
    let sidecar = FrozenOrdersSidecar {
        schema_version: ORDERS_SCHEMA_VERSION,
        corpus_identity: &config.corpus_identity,
        representation_version: coordinator
            .completed_learning()
            .compact_controller()
            .representation_version(),
        geometry_version: &config.geometry_version,
        phase3_handoff_identity_sha256: &config.phase3_handoff_identity_sha256,
        compact_order: coordinator.compact_order(),
        rbf_order: coordinator.rbf_order(),
        initial_quota_audit: coordinator.audit(),
    };
    compact_json_bytes(&config.frozen_orders_path, &sidecar)
}

fn build_binding(
    config: &FinalEvaluationRunnerConfig,
    coordinator: &FinalEvaluationCoordinator,
    frozen_orders_identity_sha256: String,
) -> Result<SessionBinding> {
    let fixed = StaticBinding {
        corpus_identity: config.corpus_identity.clone(),
        representation_version: coordinator
            .completed_learning()
            .compact_controller()
            .representation_version()
            .to_owned(),
        geometry_version: config.geometry_version.clone(),
        phase3_handoff_identity_sha256: config.phase3_handoff_identity_sha256.clone(),
        guarded_launch_identity_sha256: config.guarded_launch_identity_sha256.clone(),
        frozen_orders_identity_sha256,
        evaluator_protocol_identity_sha256: evaluator_protocol_identity()?,
        oracle_cache_policy: ORACLE_CACHE_POLICY.to_owned(),
        shuffle_policy: SHUFFLE_POLICY.to_owned(),
        rest_interval: REST_INTERVAL,
        maximum_wrong_language_presentations: MAXIMUM_WRONG_LANGUAGE_PRESENTATIONS,
        required_rating_count: 200,
        mean_rating_sum_threshold: 1_000,
        maximum_low_ratings: 20,
    };
    let identity_sha256 = hash_serialized(&config.session_path, &fixed)?;
    Ok(SessionBinding {
        fixed,
        identity_sha256,
    })
}

fn evaluator_protocol_identity() -> Result<String> {
    #[derive(Serialize)]
    struct Protocol<'a> {
        name: &'a str,
        question: &'a str,
        anchors: [&'a str; 7],
        wrong_language_rule: &'a str,
        accepted_ratings: [u8; 7],
        confirmation_required: bool,
        pending_before_display: bool,
        recovery_requires_rating_or_explicit_redisplay: bool,
    }
    hash_serialized(
        Path::new("<evaluator-protocol>"),
        &Protocol {
            name: EVALUATOR_PROTOCOL,
            question: RATING_QUESTION,
            anchors: RATING_ANCHORS,
            wrong_language_rule: WRONG_LANGUAGE_RULE,
            accepted_ratings: [1, 2, 3, 4, 5, 6, 7],
            confirmation_required: true,
            pending_before_display: true,
            recovery_requires_rating_or_explicit_redisplay: true,
        },
    )
}

fn load_or_create_session(
    config: &FinalEvaluationRunnerConfig,
    binding: SessionBinding,
) -> Result<FinalEvaluationSession> {
    if config.session_path.exists() {
        let session: FinalEvaluationSession = read_manifest(&config.session_path)?;
        if session.schema_version != SESSION_SCHEMA_VERSION || session.binding != binding {
            return Err(Error::ExperimentState(
                "stored Phase 4 session differs from the frozen inputs".to_owned(),
            ));
        }
        validate_session_shape(&session)?;
        return Ok(session);
    }
    let session = FinalEvaluationSession {
        schema_version: SESSION_SCHEMA_VERSION,
        binding,
        phase: SessionPhase::Evaluating,
        waves: Vec::new(),
        pending_presentation: None,
        rest_checkpoints: Vec::new(),
        pause_checkpoints: Vec::new(),
        pause_reason: None,
        completion: None,
        failure: None,
    };
    save_session(&config.session_path, &session)?;
    Ok(session)
}

fn validate_session_shape(session: &FinalEvaluationSession) -> Result<()> {
    if session.schema_version != SESSION_SCHEMA_VERSION {
        return Err(Error::ExperimentState(
            "stored Phase 4 session has the wrong schema".to_owned(),
        ));
    }
    match session.phase {
        SessionPhase::Evaluating if session.completion.is_none() && session.failure.is_none() => {}
        SessionPhase::Complete if session.completion.is_some() && session.failure.is_none() => {}
        SessionPhase::Failed if session.completion.is_none() && session.failure.is_some() => {}
        _ => {
            return Err(Error::ExperimentState(
                "stored Phase 4 phase contradicts completion or failure state".to_owned(),
            ));
        }
    }
    let mut presented = BTreeSet::new();
    for wave in &session.waves {
        validate_stored_wave(wave)?;
        for decision in &wave.decisions {
            if !presented.insert(decision.event_id()) {
                return Err(Error::ExperimentState(
                    "stored Phase 4 decisions repeat an event".to_owned(),
                ));
            }
        }
    }
    if session.waves.iter().filter(|wave| !wave.submitted).count() > 1
        || session
            .waves
            .iter()
            .enumerate()
            .any(|(index, wave)| !wave.submitted && index + 1 != session.waves.len())
    {
        return Err(Error::ExperimentState(
            "only the last Phase 4 presentation wave may be incomplete".to_owned(),
        ));
    }
    if let Some(pending) = session.pending_presentation {
        let wave = session.waves.last().ok_or_else(|| {
            Error::ExperimentState("pending Phase 4 presentation has no wave".to_owned())
        })?;
        let next = wave.presentation_order.get(wave.decisions.len()).copied();
        if wave.submitted || pending.wave_id != wave.wave_id || next != Some(pending.event_id) {
            return Err(Error::ExperimentState(
                "pending Phase 4 presentation is not the next frozen event".to_owned(),
            ));
        }
    }
    validate_rest_checkpoints(session)?;
    validate_pause_checkpoints(session)?;
    if let Some(reason) = &session.pause_reason
        && (reason.trim().is_empty()
            || session.pause_checkpoints.last()
                != Some(&PauseCheckpoint {
                    after_presentations: stored_presentation_count(session),
                    reason: reason.clone(),
                }))
    {
        return Err(Error::ExperimentState(
            "stored Phase 4 pause reason has no matching checkpoint".to_owned(),
        ));
    }
    if session.phase == SessionPhase::Complete
        && (session.pending_presentation.is_some()
            || session.pause_reason.is_some()
            || session.waves.iter().any(|wave| !wave.submitted))
    {
        return Err(Error::ExperimentState(
            "completed Phase 4 session retains incomplete evaluator state".to_owned(),
        ));
    }
    if session.phase == SessionPhase::Failed {
        let failure = session.failure.as_ref().ok_or_else(|| {
            Error::ExperimentState("failed Phase 4 session has no failure record".to_owned())
        })?;
        if failure.reason.trim().is_empty()
            || failure.after_presentations != stored_presentation_count(session)
            || session.pending_presentation.is_some()
            || session.pause_reason.is_some()
        {
            return Err(Error::ExperimentState(
                "stored Phase 4 failure record is inconsistent".to_owned(),
            ));
        }
    }
    Ok(())
}

fn validate_rest_checkpoints(session: &FinalEvaluationSession) -> Result<()> {
    let presentations = stored_presentation_count(session);
    let completed_boundary_count = presentations.saturating_sub(1) / REST_INTERVAL;
    let current_boundary_count =
        usize::from(presentations != 0 && presentations.is_multiple_of(REST_INTERVAL));
    let checkpoint_count = session.rest_checkpoints.len();
    if checkpoint_count < completed_boundary_count
        || checkpoint_count > completed_boundary_count + current_boundary_count
    {
        return Err(Error::ExperimentState(
            "stored Phase 4 rest checkpoints are invalid".to_owned(),
        ));
    }
    for (index, checkpoint) in session.rest_checkpoints.iter().enumerate() {
        let expected_boundary = (index + 1).checked_mul(REST_INTERVAL).ok_or_else(|| {
            Error::ExperimentState("stored Phase 4 rest checkpoints are invalid".to_owned())
        })?;
        if checkpoint.after_presentations != expected_boundary
            || checkpoint.after_presentations > presentations
            || (checkpoint.after_presentations < presentations && !checkpoint.continued)
        {
            return Err(Error::ExperimentState(
                "stored Phase 4 rest checkpoints are invalid".to_owned(),
            ));
        }
    }
    let current_rest_continued = session.rest_checkpoints.last().is_some_and(|checkpoint| {
        checkpoint.after_presentations == presentations && checkpoint.continued
    });
    if session.pending_presentation.is_some()
        && current_boundary_count != 0
        && !current_rest_continued
    {
        return Err(Error::ExperimentState(
            "a pending Phase 4 rest cannot coexist with a pending presentation".to_owned(),
        ));
    }
    Ok(())
}

fn validate_pause_checkpoints(session: &FinalEvaluationSession) -> Result<()> {
    let presentations = stored_presentation_count(session);
    let mut previous = None;
    for checkpoint in &session.pause_checkpoints {
        if checkpoint.reason.trim().is_empty()
            || checkpoint.after_presentations > presentations
            || previous.is_some_and(|previous| checkpoint.after_presentations < previous)
        {
            return Err(Error::ExperimentState(
                "stored Phase 4 pause checkpoints are invalid".to_owned(),
            ));
        }
        previous = Some(checkpoint.after_presentations);
    }
    Ok(())
}

fn validate_stored_wave(wave: &WaveTranscript) -> Result<()> {
    if wave.decision_checksum_sha256 != wave_decision_checksum(wave)? {
        return Err(Error::ExperimentState(
            "stored Phase 4 decision checksum is invalid".to_owned(),
        ));
    }
    let coordinator_ids = wave
        .coordinator_event_ids
        .iter()
        .copied()
        .collect::<BTreeSet<_>>();
    let presentation_ids = wave
        .presentation_order
        .iter()
        .copied()
        .collect::<BTreeSet<_>>();
    if coordinator_ids.len() != wave.coordinator_event_ids.len()
        || presentation_ids.len() != wave.presentation_order.len()
        || coordinator_ids != presentation_ids
        || wave.decisions.len() > wave.presentation_order.len()
        || wave
            .decisions
            .iter()
            .zip(&wave.presentation_order)
            .any(|(decision, event_id)| decision.event_id() != *event_id)
        || wave.decisions.iter().any(|decision| {
            decision
                .rating()
                .is_some_and(|rating| !(1..=7).contains(&rating))
        })
        || wave.submitted && wave.decisions.len() != wave.presentation_order.len()
    {
        return Err(Error::ExperimentState(
            "stored Phase 4 wave violates its frozen order".to_owned(),
        ));
    }
    Ok(())
}

fn wave_decision_checksum(wave: &WaveTranscript) -> Result<String> {
    hash_serialized(
        Path::new("<phase4-wave-decisions>"),
        &WaveDecisionSeal {
            wave_id: wave.wave_id,
            coordinator_event_ids: &wave.coordinator_event_ids,
            presentation_order: &wave.presentation_order,
            decisions: &wave.decisions,
            submitted: wave.submitted,
        },
    )
}

fn refresh_wave_decision_checksum(wave: &mut WaveTranscript) -> Result<()> {
    wave.decision_checksum_sha256 = wave_decision_checksum(wave)?;
    Ok(())
}

fn replay_session(
    coordinator: &mut FinalEvaluationCoordinator,
    session: &FinalEvaluationSession,
) -> Result<()> {
    let mut presented = BTreeSet::new();
    for stored in &session.waves {
        let pending = coordinator.pending_wave().ok_or_else(|| {
            Error::ExperimentState(
                "stored Phase 4 transcript extends beyond quota replay".to_owned(),
            )
        })?;
        verify_wave(&session.binding, pending, stored)?;
        for decision in &stored.decisions {
            if !presented.insert(decision.event_id()) {
                return Err(Error::ExperimentState(
                    "Phase 4 replay encountered a repeated presentation".to_owned(),
                ));
            }
        }
        if stored.submitted {
            coordinator
                .submit_language_outcomes(stored.wave_id, language_outcomes(stored)?)
                .map_err(|error| Error::ExperimentState(error.to_string()))?;
        }
    }
    match session.phase {
        SessionPhase::Complete if coordinator.progress() != QuotaResolutionProgress::Complete => {
            Err(Error::ExperimentState(
                "completed Phase 4 session does not replay to completion".to_owned(),
            ))
        }
        _ => Ok(()),
    }
}

fn ensure_current_wave(
    config: &FinalEvaluationRunnerConfig,
    coordinator: &FinalEvaluationCoordinator,
    session: &mut FinalEvaluationSession,
) -> Result<()> {
    let pending = coordinator.pending_wave().ok_or_else(|| {
        Error::Invariant("Phase 4 awaits language without a presentation wave".to_owned())
    })?;
    if let Some(stored) = session.waves.last()
        && !stored.submitted
    {
        return verify_wave(&session.binding, pending, stored);
    }
    let transcript = freeze_wave(&session.binding, pending)?;
    let prior_presentations = session
        .waves
        .iter()
        .flat_map(|wave| wave.decisions.iter().map(|decision| decision.event_id()))
        .collect::<BTreeSet<_>>();
    if transcript
        .presentation_order
        .iter()
        .any(|event_id| prior_presentations.contains(event_id))
    {
        return Err(Error::ExperimentState(
            "new Phase 4 wave repeats an earlier presentation".to_owned(),
        ));
    }
    session.waves.push(transcript);
    session.pause_reason = None;
    save_session(&config.session_path, session)
}

fn freeze_wave(binding: &SessionBinding, wave: &PresentationWave) -> Result<WaveTranscript> {
    let unique = wave.event_ids().iter().copied().collect::<BTreeSet<_>>();
    if unique.len() != wave.event_ids().len() {
        return Err(Error::Invariant(
            "quota resolver produced a duplicated final presentation wave".to_owned(),
        ));
    }
    let mut presentation_order = unique.into_iter().collect::<Vec<_>>();
    presentation_order.sort_by(|left, right| {
        presentation_key(binding, wave.wave_id(), *left)
            .cmp(&presentation_key(binding, wave.wave_id(), *right))
            .then_with(|| left.cmp(right))
    });
    let mut transcript = WaveTranscript {
        wave_id: wave.wave_id(),
        coordinator_event_ids: wave.event_ids().to_vec(),
        presentation_order,
        decisions: Vec::new(),
        submitted: false,
        decision_checksum_sha256: String::new(),
    };
    refresh_wave_decision_checksum(&mut transcript)?;
    Ok(transcript)
}

fn verify_wave(
    binding: &SessionBinding,
    pending: &PresentationWave,
    stored: &WaveTranscript,
) -> Result<()> {
    if pending.wave_id() != stored.wave_id
        || pending.event_ids() != stored.coordinator_event_ids
        || freeze_wave(binding, pending)?.presentation_order != stored.presentation_order
    {
        return Err(Error::ExperimentState(
            "stored final wave differs from deterministic quota replay".to_owned(),
        ));
    }
    validate_stored_wave(stored)
}

fn presentation_key(binding: &SessionBinding, wave_id: u64, event_id: EventId) -> [u8; 32] {
    let mut hasher = Sha256::new();
    hasher.update(SHUFFLE_POLICY.as_bytes());
    hasher.update([0]);
    hasher.update(binding.identity_sha256.as_bytes());
    hasher.update([0]);
    hasher.update(wave_id.to_le_bytes());
    hasher.update(event_id);
    hasher.finalize().into()
}

fn collect_current_wave<U: EvaluatorUi>(
    config: &FinalEvaluationRunnerConfig,
    corpus: &mut Option<Ndb>,
    session: &mut FinalEvaluationSession,
    evaluator: &mut U,
) -> Result<bool> {
    loop {
        let wave = session
            .waves
            .last()
            .ok_or_else(|| Error::Invariant("Phase 4 evaluator has no current wave".to_owned()))?;
        if wave.submitted {
            return Err(Error::Invariant(
                "submitted Phase 4 wave requested evaluator input".to_owned(),
            ));
        }
        if wave.decisions.len() == wave.presentation_order.len() {
            return Ok(true);
        }
        let event_id = wave.presentation_order[wave.decisions.len()];
        let wave_id = wave.wave_id;
        if let Some(pending) = session.pending_presentation
            && (pending.wave_id != wave_id || pending.event_id != event_id)
        {
            return Err(Error::ExperimentState(
                "pending Phase 4 event differs from the next frozen event".to_owned(),
            ));
        }

        let mut submission = None;
        let mut display_requested = session.pending_presentation.is_none();
        if session.pending_presentation.is_some() {
            match evaluator.recover(RecoveryView::new(
                stored_presentation_count(session) + 1,
                presentations_until_rest(session),
            )) {
                Ok(RecoveryOutcome::Submitted(value)) => submission = Some(value),
                Ok(RecoveryOutcome::Redisplay) => display_requested = true,
                Ok(RecoveryOutcome::Paused) => {
                    persist_recoverable_pause(
                        config,
                        session,
                        "evaluator paused with an uncertain final presentation",
                    )?;
                    return Ok(false);
                }
                Err(error) => {
                    persist_recoverable_pause(
                        config,
                        session,
                        &format!("terminal failed during final presentation recovery: {error}"),
                    )?;
                    return Ok(false);
                }
            }
        } else if !take_due_rest(config, session, evaluator)? {
            return Ok(false);
        }

        if display_requested {
            let content = match load_raw_note_content(corpus, &config.corpus_path, event_id) {
                Ok(content) => content,
                Err(error) => {
                    persist_recoverable_pause(
                        config,
                        session,
                        &format!(
                            "display corpus unavailable for final event {}: {error}",
                            hex_event_id(event_id)
                        ),
                    )?;
                    return Ok(false);
                }
            };
            if session.pending_presentation.is_none() {
                session.pending_presentation = Some(PendingPresentation { wave_id, event_id });
                session.pause_reason = None;
                save_session(&config.session_path, session)?;
            }
            match evaluator.rate(RatingView::new(
                &content,
                stored_presentation_count(session) + 1,
                presentations_until_rest(session),
            )) {
                Ok(RatingOutcome::Submitted(value)) => submission = Some(value),
                Ok(RatingOutcome::Paused) => {
                    persist_recoverable_pause(
                        config,
                        session,
                        "evaluator paused before rating the pending final presentation",
                    )?;
                    return Ok(false);
                }
                Err(error) => {
                    persist_recoverable_pause(
                        config,
                        session,
                        &format!("terminal failed while requesting a final rating: {error}"),
                    )?;
                    return Ok(false);
                }
            }
        }

        let submission = submission
            .ok_or_else(|| Error::Invariant("evaluator returned no final decision".to_owned()))?;
        store_evaluator_submission(config, session, event_id, submission)?;
        if submission.pause_after() {
            return Ok(false);
        }
    }
}

fn store_evaluator_submission(
    config: &FinalEvaluationRunnerConfig,
    session: &mut FinalEvaluationSession,
    event_id: EventId,
    submission: EvaluatorSubmission,
) -> Result<()> {
    let decision = match submission.decision() {
        EvaluatorDecision::Rating(rating) if (1..=7).contains(&rating) => {
            StoredDecision::Rated { event_id, rating }
        }
        EvaluatorDecision::Rating(_) => {
            return Err(Error::ExperimentState(
                "evaluator returned a final rating outside 1–7".to_owned(),
            ));
        }
        EvaluatorDecision::WrongLanguage => StoredDecision::WrongLanguage { event_id },
    };
    let wave = session
        .waves
        .last_mut()
        .ok_or_else(|| Error::Invariant("final decision has no wave".to_owned()))?;
    wave.decisions.push(decision);
    refresh_wave_decision_checksum(wave)?;
    session.pending_presentation = None;
    if submission.pause_after() {
        let reason = "evaluator chose to pause after the accepted final decision";
        session.pause_reason = Some(reason.to_owned());
        record_pause_checkpoint(session, reason);
    } else {
        session.pause_reason = None;
    }
    if wrong_language_decision_count(session) > MAXIMUM_WRONG_LANGUAGE_PRESENTATIONS {
        return fail_session(
            config,
            session,
            "final evaluation exceeded 21 wrong-language presentations",
        );
    }
    save_session(&config.session_path, session)
}

fn take_due_rest<U: EvaluatorUi>(
    config: &FinalEvaluationRunnerConfig,
    session: &mut FinalEvaluationSession,
    evaluator: &mut U,
) -> Result<bool> {
    let presentations = stored_presentation_count(session);
    if presentations == 0 || !presentations.is_multiple_of(REST_INTERVAL) {
        return Ok(true);
    }
    let checkpoint_index = match session
        .rest_checkpoints
        .iter()
        .position(|checkpoint| checkpoint.after_presentations == presentations)
    {
        Some(index) => index,
        None => {
            session.rest_checkpoints.push(RestCheckpoint {
                after_presentations: presentations,
                continued: false,
            });
            save_session(&config.session_path, session)?;
            session.rest_checkpoints.len() - 1
        }
    };
    if session.rest_checkpoints[checkpoint_index].continued {
        return Ok(true);
    }
    match evaluator.rest(RestView::new(presentations)) {
        Ok(RestOutcome::Continue) => {
            session.rest_checkpoints[checkpoint_index].continued = true;
            session.pause_reason = None;
            save_session(&config.session_path, session)?;
            Ok(true)
        }
        Ok(RestOutcome::Paused) => {
            persist_recoverable_pause(
                config,
                session,
                "evaluator paused at a scheduled final rest",
            )?;
            Ok(false)
        }
        Err(error) => {
            persist_recoverable_pause(
                config,
                session,
                &format!("terminal failed at a scheduled final rest: {error}"),
            )?;
            Ok(false)
        }
    }
}

fn show_preparing<U: EvaluatorUi>(
    config: &FinalEvaluationRunnerConfig,
    session: &mut FinalEvaluationSession,
    evaluator: &mut U,
) -> Result<bool> {
    match evaluator.preparing() {
        Ok(()) => Ok(true),
        Err(error) => {
            persist_recoverable_pause(
                config,
                session,
                &format!("terminal failed while preparing final evaluation: {error}"),
            )?;
            Ok(false)
        }
    }
}

fn persist_recoverable_pause(
    config: &FinalEvaluationRunnerConfig,
    session: &mut FinalEvaluationSession,
    reason: &str,
) -> Result<()> {
    session.pause_reason = Some(reason.to_owned());
    record_pause_checkpoint(session, reason);
    save_session(&config.session_path, session)
}

fn record_pause_checkpoint(session: &mut FinalEvaluationSession, reason: &str) {
    let checkpoint = PauseCheckpoint {
        after_presentations: stored_presentation_count(session),
        reason: reason.to_owned(),
    };
    if session.pause_checkpoints.last() != Some(&checkpoint) {
        session.pause_checkpoints.push(checkpoint);
    }
}

fn stored_presentation_count(session: &FinalEvaluationSession) -> usize {
    session.waves.iter().map(|wave| wave.decisions.len()).sum()
}

fn wrong_language_decision_count(session: &FinalEvaluationSession) -> usize {
    session
        .waves
        .iter()
        .flat_map(|wave| &wave.decisions)
        .filter(|decision| matches!(decision, StoredDecision::WrongLanguage { .. }))
        .count()
}

fn presentations_until_rest(session: &FinalEvaluationSession) -> usize {
    let remainder = stored_presentation_count(session) % REST_INTERVAL;
    if remainder == 0 {
        REST_INTERVAL
    } else {
        REST_INTERVAL - remainder
    }
}

fn language_outcomes(wave: &WaveTranscript) -> Result<Vec<EventLanguageOutcome>> {
    if wave.decisions.len() != wave.presentation_order.len() {
        return Err(Error::ExperimentState(
            "incomplete final wave cannot be submitted".to_owned(),
        ));
    }
    let by_event = wave
        .decisions
        .iter()
        .copied()
        .map(|decision| (decision.event_id(), decision.language()))
        .collect::<BTreeMap<_, _>>();
    wave.coordinator_event_ids
        .iter()
        .map(|event_id| {
            by_event
                .get(event_id)
                .copied()
                .map(|eligibility| EventLanguageOutcome::new(*event_id, eligibility))
                .ok_or_else(|| {
                    Error::ExperimentState(
                        "complete final wave is missing an event decision".to_owned(),
                    )
                })
        })
        .collect()
}

fn complete_session<U: EvaluatorUi>(
    config: &FinalEvaluationRunnerConfig,
    coordinator: FinalEvaluationCoordinator,
    session: &mut FinalEvaluationSession,
    evaluator: &mut U,
) -> Result<FinalEvaluationRunnerOutcome> {
    let resolved = coordinator
        .into_result()
        .map_err(|error| Error::ExperimentState(error.to_string()))?;
    let language = resolved.quota().language_delta();
    if language.wrong_language_presentations() * 20 > language.unique_presentations() {
        return fail_session(
            config,
            session,
            "wrong-language presentations exceed 5% of the merged final phase",
        );
    }
    session.pause_reason = None;
    save_session(&config.session_path, session)?;
    let artifact = build_report_artifact(config, resolved.quota(), session)?;
    publish_or_verify_immutable(&config.report_path, &artifact.bytes)?;
    session.phase = SessionPhase::Complete;
    session.completion = Some(artifact.completion);
    save_session(&config.session_path, session)?;
    evaluator
        .complete(CompletionView::new(stored_presentation_count(session)))
        .map_err(|source| io_error("write", "<terminal-output>", source))?;
    Ok(FinalEvaluationRunnerOutcome::Complete)
}

fn verify_completed_session(
    config: &FinalEvaluationRunnerConfig,
    coordinator: FinalEvaluationCoordinator,
    session: &FinalEvaluationSession,
) -> Result<()> {
    let resolved = coordinator
        .into_result()
        .map_err(|error| Error::ExperimentState(error.to_string()))?;
    let expected = build_report_artifact(config, resolved.quota(), session)?;
    let completion = session.completion.as_ref().ok_or_else(|| {
        Error::ExperimentState("completed Phase 4 session has no completion seal".to_owned())
    })?;
    let report_bytes = fs::read(&config.report_path)
        .map_err(|source| io_error("read", &config.report_path, source))?;
    if report_bytes != expected.bytes {
        return Err(Error::ExperimentState(
            "completed Phase 4 report differs from deterministic reconstruction".to_owned(),
        ));
    }
    if completion != &expected.completion {
        return Err(Error::ExperimentState(
            "completed Phase 4 completion seal differs from deterministic reconstruction"
                .to_owned(),
        ));
    }
    Ok(())
}

fn build_report_artifact(
    config: &FinalEvaluationRunnerConfig,
    quota: &crate::quota_resolution::ResolvedQuota,
    session: &FinalEvaluationSession,
) -> Result<FinalReportArtifact> {
    let ratings = stored_ratings(session)?;
    let quota_audit_bytes =
        serde_json::to_vec(quota.audit()).map_err(|source| Error::Manifest {
            operation: "encode",
            path: config.report_path.clone(),
            source,
        })?;
    let quota_audit_identity_sha256 = hash_bytes(&quota_audit_bytes);
    let evaluator_transcript_identity_sha256 = evaluator_transcript_identity(session)?;
    let provenance = FinalEvaluationReportProvenance::new(
        config.corpus_identity.clone(),
        quota.compact_batch().representation_version().to_owned(),
        config.geometry_version.clone(),
        config.phase3_handoff_identity_sha256.clone(),
        config.guarded_launch_identity_sha256.clone(),
        session.binding.fixed.frozen_orders_identity_sha256.clone(),
        session
            .binding
            .fixed
            .evaluator_protocol_identity_sha256
            .clone(),
        evaluator_transcript_identity_sha256.clone(),
        quota_audit_identity_sha256.clone(),
    )
    .map_err(|error| Error::ExperimentState(error.to_string()))?;
    let report = build_final_evaluation_report(quota, &ratings, provenance)
        .map_err(|error| Error::ExperimentState(error.to_string()))?;
    let bytes = pretty_json_bytes(&config.report_path, &report)?;
    let language = quota.language_delta();
    let completion = CompletionSeal {
        report_sha256: hash_bytes(&bytes),
        evaluator_transcript_identity_sha256,
        quota_audit_identity_sha256,
        compact_ratings: report.compact().ratings().len(),
        rbf_ratings: report.rbf().ratings().len(),
        unique_presentations: language.unique_presentations(),
        wrong_language_presentations: language.wrong_language_presentations(),
    };
    Ok(FinalReportArtifact { bytes, completion })
}

fn evaluator_transcript_identity(session: &FinalEvaluationSession) -> Result<String> {
    hash_serialized(
        Path::new("<evaluator-transcript>"),
        &EvaluatorTranscript {
            schema_version: session.schema_version,
            binding: &session.binding,
            waves: &session.waves,
            pending_presentation: session.pending_presentation,
            rest_checkpoints: &session.rest_checkpoints,
            pause_checkpoints: &session.pause_checkpoints,
            pause_reason: &session.pause_reason,
        },
    )
}

fn stored_ratings(session: &FinalEvaluationSession) -> Result<BTreeMap<EventId, GladnessRating>> {
    session
        .waves
        .iter()
        .flat_map(|wave| wave.decisions.iter().copied())
        .filter_map(|decision| {
            decision
                .rating()
                .map(|rating| (decision.event_id(), rating))
        })
        .map(|(event_id, rating)| {
            GladnessRating::new(rating)
                .map(|rating| (event_id, rating))
                .map_err(|error| Error::ExperimentState(error.to_string()))
        })
        .collect()
}

fn fail_session<T>(
    config: &FinalEvaluationRunnerConfig,
    session: &mut FinalEvaluationSession,
    reason: &str,
) -> Result<T> {
    session.phase = SessionPhase::Failed;
    session.pause_reason = None;
    session.failure = Some(FailureSeal {
        reason: reason.to_owned(),
        after_presentations: stored_presentation_count(session),
    });
    save_session(&config.session_path, session)?;
    Err(Error::ExperimentState(reason.to_owned()))
}

fn load_raw_note_content(
    corpus: &mut Option<Ndb>,
    corpus_path: &Path,
    event_id: EventId,
) -> Result<String> {
    if corpus.is_none() {
        require_directory(corpus_path)?;
        *corpus = Some(open_existing_ndb(corpus_path, Validation::TrustedSource)?);
    }
    let corpus = corpus.as_ref().expect("display corpus was opened");
    let transaction = Transaction::new(corpus)
        .map_err(|source| ndb_error("open transaction on", corpus_path, source))?;
    let note = corpus
        .get_note_by_id(&transaction, &event_id)
        .map_err(|source| ndb_error("load event from", corpus_path, source))?;
    Ok(terminal_safe(note.content()))
}

fn terminal_safe(content: &str) -> String {
    content
        .chars()
        .map(|character| match character {
            '\n' | '\t' => character,
            _ if character.is_control() => ' ',
            _ => character,
        })
        .collect()
}

impl CandidateOrderOracle for CacheOnlyOracle {
    fn representation_version(&self) -> &str {
        &self.representation_version
    }

    fn similar_notes_wave(
        &mut self,
        _requests: &[SimilarNotesRequest],
        _representation_version: &str,
    ) -> Result<SimilarNotesWaveResponse> {
        Err(Error::ExperimentState(
            "frozen Phase 4 resume is missing a cached Oracle wave".to_owned(),
        ))
    }

    fn vectors_for_notes(
        &mut self,
        _note_ids: &[EventId],
        _representation_version: &str,
    ) -> Result<VectorsForNotesResponse> {
        Err(Error::ExperimentState(
            "frozen Phase 4 resume is missing a cached vector response".to_owned(),
        ))
    }
}

impl<'a, O: CandidateOrderOracle> FinalEvaluationOracle<'a, O> {
    fn new(inner: &'a mut O, cache_path: PathBuf, allow_oracle_work: bool) -> Result<Self> {
        let representation_version = inner.representation_version().to_owned();
        if representation_version.is_empty() {
            return Err(Error::ExperimentState(
                "Phase 4 Oracle representation version is empty".to_owned(),
            ));
        }
        Ok(Self {
            inner,
            representation_version,
            cache_path,
            wave_call_cursor: 0,
            allow_oracle_work,
        })
    }

    fn similar_wave_path(&self, key: &SimilarWaveCacheKey) -> Result<PathBuf> {
        let identity = hash_serialized(&self.cache_path, key)?;
        Ok(self.cache_path.join(format!("wave-{identity}.json")))
    }

    fn vector_path(&self, key: &VectorCacheKey) -> Result<PathBuf> {
        let identity = hash_serialized(&self.cache_path, key)?;
        Ok(self.cache_path.join(format!("vectors-{identity}.json")))
    }
}

impl<O: CandidateOrderOracle> CandidateOrderOracle for FinalEvaluationOracle<'_, O> {
    fn representation_version(&self) -> &str {
        &self.representation_version
    }

    fn similar_notes_wave(
        &mut self,
        requests: &[SimilarNotesRequest],
        representation_version: &str,
    ) -> Result<SimilarNotesWaveResponse> {
        if representation_version != self.representation_version {
            return Err(Error::InvalidQuery(
                "Phase 4 Oracle cache representation mismatch".to_owned(),
            ));
        }
        let key = SimilarWaveCacheKey {
            policy: ORACLE_CACHE_POLICY.to_owned(),
            call_ordinal: self.wave_call_cursor,
            representation_version: representation_version.to_owned(),
            requests: requests.to_vec(),
        };
        let path = self.similar_wave_path(&key)?;
        if path.exists() {
            let envelope: SimilarWaveCacheEnvelope = read_manifest(&path)?;
            if envelope.key != key {
                return Err(Error::ExperimentState(format!(
                    "cached Phase 4 Oracle wave `{}` has the wrong request key",
                    path.display()
                )));
            }
            if envelope.response_sha256 != hash_serialized(&path, &envelope.response)? {
                return Err(Error::ExperimentState(format!(
                    "cached Phase 4 Oracle wave `{}` failed its checksum",
                    path.display()
                )));
            }
            validate_similar_wave(&key, &envelope.response)?;
            self.wave_call_cursor += 1;
            return Ok(envelope.response);
        }
        if !self.allow_oracle_work {
            return Err(Error::ExperimentState(format!(
                "resuming Phase 4 is missing cached Oracle wave {}",
                self.wave_call_cursor
            )));
        }
        let response = self
            .inner
            .similar_notes_wave(requests, representation_version)?;
        validate_similar_wave(&key, &response)?;
        let response_sha256 = hash_serialized(&path, &response)?;
        let envelope = BorrowedSimilarWaveCacheEnvelope {
            key: &key,
            response_sha256: &response_sha256,
            response: &response,
        };
        let bytes = compact_json_bytes(&path, &envelope)?;
        publish_or_verify_immutable(&path, &bytes)?;
        self.wave_call_cursor += 1;
        Ok(response)
    }

    fn vectors_for_notes(
        &mut self,
        note_ids: &[EventId],
        representation_version: &str,
    ) -> Result<VectorsForNotesResponse> {
        if representation_version != self.representation_version {
            return Err(Error::InvalidQuery(
                "Phase 4 vector cache representation mismatch".to_owned(),
            ));
        }
        let key = VectorCacheKey {
            policy: ORACLE_CACHE_POLICY.to_owned(),
            representation_version: representation_version.to_owned(),
            note_ids: note_ids.to_vec(),
        };
        let path = self.vector_path(&key)?;
        if path.exists() {
            let envelope: VectorCacheEnvelope = read_manifest(&path)?;
            if envelope.key != key {
                return Err(Error::ExperimentState(format!(
                    "cached Phase 4 vector response `{}` has the wrong request key",
                    path.display()
                )));
            }
            if envelope.response_sha256 != hash_serialized(&path, &envelope.response)? {
                return Err(Error::ExperimentState(format!(
                    "cached Phase 4 vector response `{}` failed its checksum",
                    path.display()
                )));
            }
            validate_vector_response(&key, &envelope.response)?;
            return Ok(envelope.response);
        }
        if !self.allow_oracle_work {
            return Err(Error::ExperimentState(
                "resuming Phase 4 is missing a cached vector response".to_owned(),
            ));
        }
        let response = self
            .inner
            .vectors_for_notes(note_ids, representation_version)?;
        validate_vector_response(&key, &response)?;
        let response_sha256 = hash_serialized(&path, &response)?;
        let envelope = BorrowedVectorCacheEnvelope {
            key: &key,
            response_sha256: &response_sha256,
            response: &response,
        };
        let bytes = compact_json_bytes(&path, &envelope)?;
        publish_or_verify_immutable(&path, &bytes)?;
        Ok(response)
    }
}

fn validate_similar_wave(
    key: &SimilarWaveCacheKey,
    response: &SimilarNotesWaveResponse,
) -> Result<()> {
    if key.requests.is_empty() || response.responses.len() != key.requests.len() {
        return Err(Error::InvalidOracleResponse(
            "Phase 4 cached wave has the wrong response count".to_owned(),
        ));
    }
    let mut expected_rows = None;
    for (request, response) in key.requests.iter().zip(&response.responses) {
        let rows = (response.represented_rows, response.total_rows);
        let expected_candidates = usize::try_from(response.total_rows.saturating_sub(1))
            .unwrap_or(usize::MAX)
            .min(request.candidate_depth);
        if response.representation_version != key.representation_version
            || !response.complete
            || response.represented_rows == 0
            || response.represented_rows != response.total_rows
            || response.candidates.len() != expected_candidates
            || expected_rows.is_some_and(|expected| expected != rows)
        {
            return Err(Error::InvalidOracleResponse(format!(
                "Phase 4 cached response for {} violates its request",
                hex_event_id(request.note_id)
            )));
        }
        expected_rows = Some(rows);
    }
    Ok(())
}

fn validate_vector_response(
    key: &VectorCacheKey,
    response: &VectorsForNotesResponse,
) -> Result<()> {
    if response.representation_version != key.representation_version
        || !response.complete
        || response.represented_rows == 0
        || response.represented_rows != response.total_rows
        || response.vectors.len() != key.note_ids.len()
        || response
            .vectors
            .iter()
            .map(|stored| stored.event_id)
            .ne(key.note_ids.iter().copied())
    {
        return Err(Error::InvalidOracleResponse(
            "Phase 4 cached vector response violates its request".to_owned(),
        ));
    }
    Ok(())
}

fn publish_or_verify_immutable(path: &Path, bytes: &[u8]) -> Result<()> {
    if path.exists() {
        protect_existing_private_file(path)?;
        let existing = fs::read(path).map_err(|source| io_error("read", path, source))?;
        if existing != bytes {
            return Err(Error::ExperimentState(format!(
                "immutable Phase 4 artifact `{}` differs from reconstruction",
                path.display()
            )));
        }
        return Ok(());
    }
    save_bytes_atomic(path, bytes)
}

fn prepare_private_cache_directory(path: &Path) -> Result<()> {
    create_private_directories(path)?;
    let metadata =
        fs::symlink_metadata(path).map_err(|source| io_error("inspect", path, source))?;
    if !metadata.file_type().is_dir() {
        return Err(Error::ExperimentState(format!(
            "private Phase 4 Oracle cache `{}` is not a directory",
            path.display()
        )));
    }
    set_private_directory_permissions(path)?;
    for entry in fs::read_dir(path).map_err(|source| io_error("read", path, source))? {
        let entry = entry.map_err(|source| io_error("read", path, source))?;
        protect_existing_private_file(&entry.path())?;
    }
    Ok(())
}

fn save_session(path: &Path, session: &FinalEvaluationSession) -> Result<()> {
    let bytes = pretty_json_bytes(path, session)?;
    save_bytes_atomic(path, &bytes)
}

fn pretty_json_bytes(path: &Path, value: &impl Serialize) -> Result<Vec<u8>> {
    let mut bytes = serde_json::to_vec_pretty(value).map_err(|source| Error::Manifest {
        operation: "encode",
        path: path.to_owned(),
        source,
    })?;
    bytes.push(b'\n');
    Ok(bytes)
}

fn compact_json_bytes(path: &Path, value: &impl Serialize) -> Result<Vec<u8>> {
    let mut bytes = serde_json::to_vec(value).map_err(|source| Error::Manifest {
        operation: "encode",
        path: path.to_owned(),
        source,
    })?;
    bytes.push(b'\n');
    Ok(bytes)
}

fn hash_serialized(path: &Path, value: &impl Serialize) -> Result<String> {
    serde_json::to_vec(value)
        .map(|bytes| hash_bytes(&bytes))
        .map_err(|source| Error::Manifest {
            operation: "encode",
            path: path.to_owned(),
            source,
        })
}

fn acquire_session_lock(session_path: &Path) -> Result<File> {
    let name = session_path
        .file_name()
        .and_then(|name| name.to_str())
        .ok_or_else(|| Error::NonUtf8Path(session_path.to_owned()))?;
    let parent = session_path.parent().unwrap_or_else(|| Path::new("."));
    create_private_directories(parent)?;
    let path = parent.join(format!(".{name}.lock"));
    protect_existing_private_file(&path)?;
    let mut options = OpenOptions::new();
    options.create(true).read(true).write(true).truncate(false);
    set_private_creation_mode(&mut options);
    let file = options
        .open(&path)
        .map_err(|source| io_error("open", &path, source))?;
    set_private_file_permissions(&file, &path)?;
    match file.try_lock() {
        Ok(()) => Ok(file),
        Err(fs::TryLockError::WouldBlock) => Err(Error::ExperimentState(format!(
            "Phase 4 session `{}` is already active",
            session_path.display()
        ))),
        Err(fs::TryLockError::Error(source)) => Err(io_error("lock", &path, source)),
    }
}

fn save_bytes_atomic(path: &Path, bytes: &[u8]) -> Result<()> {
    if let Some(parent) = path.parent() {
        create_private_directories(parent)?;
    }
    protect_existing_private_file(path)?;
    let temporary = atomic_temporary_path(path)?;
    remove_stale_private_temporary(&temporary)?;
    let mut options = OpenOptions::new();
    options.create_new(true).write(true);
    set_private_creation_mode(&mut options);
    let file = options
        .open(&temporary)
        .map_err(|source| io_error("create", &temporary, source))?;
    set_private_file_permissions(&file, &temporary)?;
    let mut writer = BufWriter::new(file);
    writer
        .write_all(bytes)
        .map_err(|source| io_error("write", &temporary, source))?;
    writer
        .flush()
        .map_err(|source| io_error("flush", &temporary, source))?;
    writer
        .get_ref()
        .sync_all()
        .map_err(|source| io_error("sync", &temporary, source))?;
    fs::rename(&temporary, path).map_err(|source| io_error("publish", path, source))?;
    if let Some(parent) = path.parent() {
        File::open(parent)
            .and_then(|directory| directory.sync_all())
            .map_err(|source| io_error("sync", parent, source))?;
    }
    Ok(())
}

fn atomic_temporary_path(path: &Path) -> Result<PathBuf> {
    let name = path
        .file_name()
        .and_then(|name| name.to_str())
        .ok_or_else(|| Error::NonUtf8Path(path.to_owned()))?;
    Ok(path.with_file_name(format!(".{name}.tmp")))
}

fn create_private_directories(path: &Path) -> Result<()> {
    let mut builder = fs::DirBuilder::new();
    builder.recursive(true);
    #[cfg(unix)]
    {
        use std::os::unix::fs::DirBuilderExt as _;
        builder.mode(0o700);
    }
    builder
        .create(path)
        .map_err(|source| io_error("create", path, source))
}

fn protect_existing_private_file(path: &Path) -> Result<()> {
    let metadata = match fs::symlink_metadata(path) {
        Ok(metadata) => metadata,
        Err(source) if source.kind() == std::io::ErrorKind::NotFound => return Ok(()),
        Err(source) => return Err(io_error("inspect", path, source)),
    };
    if !metadata.file_type().is_file() {
        return Err(Error::ExperimentState(format!(
            "private Phase 4 artifact `{}` is not a regular file",
            path.display()
        )));
    }
    set_private_path_permissions(path)
}

fn remove_stale_private_temporary(path: &Path) -> Result<()> {
    let metadata = match fs::symlink_metadata(path) {
        Ok(metadata) => metadata,
        Err(source) if source.kind() == std::io::ErrorKind::NotFound => return Ok(()),
        Err(source) => return Err(io_error("inspect", path, source)),
    };
    if !metadata.file_type().is_file() {
        return Err(Error::ExperimentState(format!(
            "private Phase 4 temporary `{}` is not a regular file",
            path.display()
        )));
    }
    fs::remove_file(path).map_err(|source| io_error("remove", path, source))
}

fn set_private_creation_mode(options: &mut OpenOptions) {
    #[cfg(unix)]
    {
        use std::os::unix::fs::OpenOptionsExt as _;
        options.mode(0o600);
    }
}

fn set_private_file_permissions(file: &File, path: &Path) -> Result<()> {
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt as _;
        file.set_permissions(fs::Permissions::from_mode(0o600))
            .map_err(|source| io_error("protect", path, source))?;
    }
    #[cfg(not(unix))]
    let _ = (file, path);
    Ok(())
}

fn set_private_path_permissions(path: &Path) -> Result<()> {
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt as _;
        fs::set_permissions(path, fs::Permissions::from_mode(0o600))
            .map_err(|source| io_error("protect", path, source))?;
    }
    #[cfg(not(unix))]
    let _ = path;
    Ok(())
}

fn set_private_directory_permissions(path: &Path) -> Result<()> {
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt as _;
        fs::set_permissions(path, fs::Permissions::from_mode(0o700))
            .map_err(|source| io_error("protect", path, source))?;
    }
    #[cfg(not(unix))]
    let _ = path;
    Ok(())
}

fn hex_event_id(event_id: EventId) -> String {
    let mut encoded = String::with_capacity(64);
    for byte in event_id {
        use std::fmt::Write as _;
        write!(&mut encoded, "{byte:02x}").expect("writing to String cannot fail");
    }
    encoded
}
