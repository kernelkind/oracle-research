//! Resumable terminal execution of the frozen Phase 3 learning protocol.

use std::collections::{BTreeMap, BTreeSet};
use std::fs::{self, File, OpenOptions};
use std::io::{BufWriter, Write};
use std::path::{Path, PathBuf};

use nostrdb::{Ndb, Transaction};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

use crate::adaptive_learning::{
    AdaptiveLearningCoordinator, AdaptiveLearningError, AdaptiveLearningProgress,
    CompletedAdaptiveLearning, LEARNING_ROUNDS, MAX_WRONG_LANGUAGE_PRESENTATIONS, SEED_COUNT,
};
use crate::artifact::hash_bytes;
use crate::candidate_order::{
    B16Boundary, CANDIDATE_DEPTH, CandidateOrderAttempt, CandidateOrderOracle, CandidateOrderPhase,
};
use crate::evaluator::{
    CompletionView, EvaluatorDecision, EvaluatorSubmission, EvaluatorUi, RATING_ANCHORS,
    RATING_QUESTION, RatingOutcome, RatingView, RecoveryOutcome, RecoveryView, RestOutcome,
    RestView, WRONG_LANGUAGE_RULE,
};
use crate::evaluator_tui::FullScreenEvaluator;
use crate::fp32_oracle::{
    SimilarNotesRequest, SimilarNotesResponse, SimilarNotesWaveMetrics, SimilarNotesWaveResponse,
    VectorsForNotesResponse,
};
use crate::personalizer_learning::{
    BatchRating, CompactLearningController, CompactLearningSettings, EvidenceIdentity,
    EvidenceNote, GladnessRating, RbfLearningController, RbfLearningSettings, ScaleLevel,
};
use crate::quota_resolution::{EventLanguageOutcome, LanguageEligibility, PriorPresentation};
use crate::representation::{EventId, FP32_SCAN_BLOCK_ROWS};
use crate::shared_learning_round::SharedLearningRoundRecord;
use crate::snapshot::{
    Error, Result, Validation, io_error, ndb_error, open_existing_ndb, read_manifest,
    require_directory,
};

const SESSION_SCHEMA_VERSION: u32 = 8;
const ORACLE_RESPONSE_CONTRACT: &str = "candidate-order-oracle-v1";
const SHUFFLE_POLICY: &str = "phase3-learning-sha256-concealed-v1";
const SCORER_POLICY: &str = "compact-rbf-forward-only-h64-h256-fallback-v2";
const DIAGNOSTIC_SEAL_DOMAIN: &[u8] = b"oracle-mvp-phase3-diagnostic-v1\0";
const REST_INTERVAL: usize = 20;
// Schema-5 serialized compatibility values. These reproduce the already-frozen
// presentation-order identity and must never be used as current evaluator copy.
const LEGACY_ORDER_RATING_QUESTION: &str =
    "Considering the attention it required, how glad are you that you saw this note?";
const LEGACY_ORDER_RATING_ANCHORS: [&str; 7] = [
    "1: Actively wish it had not been shown.",
    "2: Clearly not worth seeing.",
    "3: Little personal value.",
    "4: Indifferent.",
    "5: Mildly glad to have seen it.",
    "6: Clearly glad; personally valuable.",
    "7: Exceptionally valuable.",
];
const LEGACY_ORDER_WRONG_LANGUAGE_RULE: &str = "Use wrong_language only when the note is clearly primarily non-English. Mixed-language, code-heavy, and ambiguous notes remain eligible and must be rated.";
const LEGACY_ORDER_RATING_SUFFIX: &str =
    " [1–7, `l` = wrong_language; append `q` to save and stop]: ";

/// One verified positive note used to initialize both personalizers.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct AdaptiveLearningSeed {
    event_id: EventId,
    rating: u8,
}

impl AdaptiveLearningSeed {
    pub fn new(event_id: EventId, rating: u8) -> Result<Self> {
        GladnessRating::new(rating).map_err(|error| Error::ExperimentState(error.to_string()))?;
        if rating <= 4 {
            return Err(Error::ExperimentState(
                "an adaptive-learning seed must have a positive 5–7 rating".to_owned(),
            ));
        }
        Ok(Self { event_id, rating })
    }

    pub const fn event_id(self) -> EventId {
        self.event_id
    }

    pub const fn rating(self) -> u8 {
        self.rating
    }
}

/// Immutable inputs for one Phase 3 learning session.
#[derive(Clone, Debug)]
pub struct AdaptiveLearningRunnerConfig {
    /// Raw kind-1 NostrDB used only to display stored note content.
    pub corpus_path: PathBuf,
    /// Already-verified immutable identity of that corpus.
    pub corpus_identity: String,
    /// Durable evaluator transcript. Oracle response files are stored beside it.
    pub session_path: PathBuf,
    /// Supplied Compact geometry and initial scale.
    pub compact_settings: CompactLearningSettings,
    /// Supplied RBF geometry.
    pub rbf_settings: RbfLearningSettings,
    /// Supplied representation-bound near-duplicate boundary.
    pub b16: B16Boundary,
    /// Exactly five ordered positive seeds shared by both personalizers.
    pub seeds: Vec<AdaptiveLearningSeed>,
}

/// Result of one terminal invocation.
pub enum AdaptiveLearningRunnerOutcome {
    /// The evaluator paused; all accepted decisions are durable.
    Paused,
    /// All ten rounds completed and the frozen handoff was reconstructed.
    Complete(Box<CompletedAdaptiveLearning>),
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
struct StaticSessionBinding {
    corpus_identity: String,
    representation_version: String,
    oracle_response_contract: String,
    compact_scale_bits: [u64; 3],
    compact_initial_scale: u16,
    rbf_scale_bits: [u64; 3],
    b16_bits: u64,
    seeds: Vec<PersistedSeed>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    initial_presentations: Vec<PersistedLedgerEntry>,
    scorer_policy: String,
    evaluator_protocol: EvaluatorProtocolBinding,
    shuffle_policy: String,
    candidate_depth: usize,
    learning_rounds: usize,
    learning_primary: usize,
    learning_reserve: usize,
    maximum_wrong_language_presentations: usize,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
struct EvaluatorProtocolBinding {
    question: String,
    rating_anchors: [String; 7],
    wrong_language_rule: String,
    controls: EvaluatorControlsBinding,
    input_policy: EvaluatorInputPolicyBinding,
    wrong_language_counts_toward_rest: bool,
    rest_interval: usize,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
struct EvaluatorControlsBinding {
    accepted_ratings: [u8; 7],
    wrong_language_key: String,
    #[serde(default)]
    decision_confirmation_key: String,
    #[serde(default)]
    next_rating_key: String,
    #[serde(default)]
    previous_rating_key: String,
    #[serde(default)]
    next_rating_from_non_rating_selection: u8,
    #[serde(default)]
    previous_rating_from_non_rating_selection: u8,
    pause_after_decision_key: String,
    #[serde(default)]
    pause_after_decision_cancel_key: String,
    recovery_redisplay_key: String,
    letter_keys_case_insensitive: bool,
    rest_continue_keys: [String; 3],
    rest_pause_keys: [String; 3],
    immediate_pause_key: String,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
struct EvaluatorInputPolicyBinding {
    fresh_key_press_only: bool,
    paste_accepted: bool,
    repeat_accepted: bool,
    release_accepted: bool,
    #[serde(default)]
    unlisted_command_modifiers_accepted: bool,
    #[serde(default)]
    selection_confirmation_required: bool,
    #[serde(default)]
    new_selection_replaces_unconfirmed: bool,
    #[serde(default)]
    selection_discarded_on_screen_exit: bool,
    #[serde(default)]
    pause_cancel_preserves_selection: bool,
    #[serde(default)]
    rating_navigation_wraps: bool,
    stale_input_discarded_before_screen: bool,
    queued_ctrl_c_pause_preserved: bool,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
struct SeedEvidenceBinding {
    event_count: usize,
    vector_dimensions: usize,
    sha256: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
struct SessionBinding {
    fixed: StaticSessionBinding,
    seed_evidence: SeedEvidenceBinding,
    identity_sha256: String,
    presentation_order_identity_sha256: String,
}

/// Unpersisted compatibility projection used only to keep the already-frozen
/// presentation order stable while evaluator metadata becomes structured.
#[derive(Serialize)]
struct LegacyPresentationOrderBinding<'a> {
    corpus_identity: &'a str,
    representation_version: &'a str,
    oracle_response_contract: &'a str,
    compact_scale_bits: [u64; 3],
    compact_initial_scale: u16,
    rbf_scale_bits: [u64; 3],
    b16_bits: u64,
    seeds: &'a [PersistedSeed],
    scorer_policy: &'a str,
    rating_prompt: String,
    rating_instructions: String,
    shuffle_policy: &'a str,
    candidate_depth: usize,
    learning_rounds: usize,
    learning_primary: usize,
    learning_reserve: usize,
    maximum_wrong_language_presentations: usize,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
struct PersistedSeed {
    event_id: EventId,
    rating: u8,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
enum SessionPhase {
    Learning,
    Complete,
    Failed,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum SessionReplayOutcome {
    Current,
    Failed,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
struct AdaptiveLearningSession {
    schema_version: u32,
    binding: SessionBinding,
    phase: SessionPhase,
    rounds: Vec<RoundTranscript>,
    oracle_calls: Vec<PersistedOracleCall>,
    oracle_responses: Vec<CachedResponseRef>,
    vector_responses: Vec<CachedVectorResponseRef>,
    pending_presentation: Option<PendingPresentation>,
    rest_checkpoints: Vec<RestCheckpoint>,
    pause_checkpoints: Vec<PauseCheckpoint>,
    completion: Option<CompletedHandoff>,
    pause_reason: Option<String>,
    failure: Option<PersistedFailure>,
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

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
struct PendingPresentation {
    round: usize,
    wave_id: u64,
    event_id: EventId,
}

enum PreloadedNoteContent {
    Available(String),
    Unavailable(String),
}

#[derive(Clone, Debug, Deserialize, Serialize)]
struct RoundTranscript {
    round: usize,
    waves: Vec<WaveTranscript>,
    ratings_submitted: bool,
    diagnostic_seal: Option<PersistedRoundSeal>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
struct WaveTranscript {
    wave_id: u64,
    coordinator_event_ids: Vec<EventId>,
    presentation_order: Vec<EventId>,
    decisions: Vec<StagedDecision>,
    submitted: bool,
}

#[derive(Clone, Copy, Debug, Deserialize, Serialize)]
#[serde(rename_all = "snake_case", tag = "outcome")]
enum StagedDecision {
    Rated { event_id: EventId, rating: u8 },
    WrongLanguage { event_id: EventId },
}

impl StagedDecision {
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

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
struct CompletedHandoff {
    binding_identity_sha256: String,
    compact_evidence: SeedEvidenceBinding,
    rbf_evidence: SeedEvidenceBinding,
    compact_active_tuple: serde_json::Value,
    rbf_active_tuple: serde_json::Value,
    compact_rounds: usize,
    rbf_rounds: usize,
    presentation_ledger: Vec<PersistedLedgerEntry>,
    ratings: Vec<PersistedRating>,
    eligible_presentations: usize,
    wrong_language_presentations: usize,
    source_waves: Vec<PersistedSourceWave>,
    failed_candidate_order_attempts: Vec<SealedCandidateOrderAttempt>,
    ordered_rounds: Vec<PersistedRoundSeal>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
struct PersistedFailure {
    sha256: String,
    reason: String,
    transition: PersistedFailureTransition,
    transition_input_sha256: String,
    candidate_order_attempts: Vec<SealedCandidateOrderAttempt>,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case", tag = "kind")]
enum PersistedFailureTransition {
    StartRound { round: usize },
    SubmitLanguage { round: usize, wave_id: u64 },
    SubmitRatings { round: usize },
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
struct PersistedLedgerEntry {
    event_id: EventId,
    state: PriorPresentation,
}

#[derive(Clone, Copy, Debug, Deserialize, PartialEq, Serialize)]
struct PersistedRating {
    event_id: EventId,
    rating: u8,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
struct PersistedSourceWave {
    round: usize,
    source_event_ids: Vec<EventId>,
    metrics: SimilarNotesWaveMetrics,
    accepted: bool,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
struct PersistedRoundSeal {
    round: usize,
    round_record_sha256: String,
    compact_candidate_pool_sha256: String,
    compact_accepted_event_ids: Vec<EventId>,
    compact_evidence_after: SeedEvidenceBinding,
    rbf_candidate_pool_sha256: String,
    rbf_accepted_event_ids: Vec<EventId>,
    rbf_evidence_after: SeedEvidenceBinding,
    ratings: Vec<PersistedRating>,
    presentation_ledger: Vec<PersistedLedgerEntry>,
    frozen_predictions_sha256: String,
    errors_sha256: String,
    next_tuples_sha256: String,
    candidate_order_audit_sha256: String,
    shared_round_audit_sha256: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
struct SealedCandidateOrderAttempt {
    sha256: String,
    record: serde_json::Value,
}

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
struct ResponseCacheKey {
    representation_version: String,
    source_event_id: EventId,
    candidate_depth: usize,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
struct CachedResponseRef {
    key: ResponseCacheKey,
    sha256: String,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
struct CachedResponseEnvelope {
    key: ResponseCacheKey,
    response: SimilarNotesResponse,
}

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
struct VectorResponseCacheKey {
    representation_version: String,
    note_ids: Vec<EventId>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
struct CachedVectorResponseRef {
    key: VectorResponseCacheKey,
    sha256: String,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
struct CachedVectorResponseEnvelope {
    key: VectorResponseCacheKey,
    response: VectorsForNotesResponse,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
struct PersistedOracleCall {
    representation_version: String,
    requests: Vec<SimilarNotesRequest>,
    metrics: SimilarNotesWaveMetrics,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
struct PersistedOracleCallEnvelope {
    call: PersistedOracleCall,
    responses: Vec<SimilarNotesResponse>,
}

struct SessionOracle<'a, O: ?Sized> {
    inner: Option<&'a mut O>,
    representation_version: String,
    cache_dir: PathBuf,
    calls: Vec<PersistedOracleCall>,
    call_cursor: usize,
    response_refs: BTreeMap<ResponseCacheKey, CachedResponseRef>,
    loaded: BTreeMap<ResponseCacheKey, SimilarNotesResponse>,
    vector_response_refs: BTreeMap<VectorResponseCacheKey, CachedVectorResponseRef>,
    loaded_vectors: BTreeMap<VectorResponseCacheKey, VectorsForNotesResponse>,
}

/// Run Phase 3 with the production full-screen terminal evaluator.
pub fn run_adaptive_learning_tui<O>(
    config: &AdaptiveLearningRunnerConfig,
    oracle: &mut O,
) -> Result<AdaptiveLearningRunnerOutcome>
where
    O: CandidateOrderOracle,
{
    let mut evaluator = FullScreenEvaluator::new()
        .map_err(|source| io_error("initialize", "<terminal>", source))?;
    run_adaptive_learning(config, oracle, &mut evaluator)
}

/// Run Phase 3 with screening-only exact-ID no-repeat state.
pub fn run_adaptive_learning_tui_with_initial_presentations<O>(
    config: &AdaptiveLearningRunnerConfig,
    initial_presentations: &BTreeMap<EventId, PriorPresentation>,
    oracle: &mut O,
) -> Result<AdaptiveLearningRunnerOutcome>
where
    O: CandidateOrderOracle,
{
    let mut evaluator = FullScreenEvaluator::new()
        .map_err(|source| io_error("initialize", "<terminal>", source))?;
    run_adaptive_learning_with_initial_presentations(
        config,
        initial_presentations,
        oracle,
        &mut evaluator,
    )
}

/// Reconstruct a completed Phase 3 handoff from its immutable session and
/// manifested Oracle cache.
///
/// This path is intentionally read-only: it does not acquire a session lock,
/// change permissions, recover orphaned files, create artifacts, or delegate
/// missing work to an Oracle backend.
pub fn replay_completed_adaptive_learning(
    config: &AdaptiveLearningRunnerConfig,
    initial_presentations: &BTreeMap<EventId, PriorPresentation>,
) -> Result<Box<CompletedAdaptiveLearning>> {
    let representation_version = config.compact_settings.representation_version();
    let fixed_binding =
        validate_config_for_representation(config, initial_presentations, representation_version)?;
    let session: AdaptiveLearningSession = read_manifest(&config.session_path)?;
    validate_loaded_static_session(&session, &fixed_binding)?;
    if session.phase != SessionPhase::Complete {
        return Err(Error::ExperimentState(
            "read-only Phase 3 replay requires a completed session".to_owned(),
        ));
    }
    let cache_dir = oracle_cache_dir(&config.session_path)?;
    let mut session_oracle = SessionOracle::<dyn CandidateOrderOracle>::new_read_only(
        representation_version.to_owned(),
        cache_dir,
        session.oracle_calls.clone(),
        session.oracle_responses.clone(),
        session.vector_responses.clone(),
    )?;
    let (compact, rbf, seed_evidence) = build_seed_controllers(config, &mut session_oracle)?;
    let binding = build_session_binding(fixed_binding, seed_evidence)?;
    if session.binding != binding {
        return Err(Error::ExperimentState(
            "the stored seed evidence does not match this immutable session".to_owned(),
        ));
    }
    let mut coordinator = AdaptiveLearningCoordinator::new_with_initial_presentations(
        &session_oracle,
        compact,
        rbf,
        config.b16.clone(),
        initial_presentations.clone(),
    )
    .map_err(adaptive_error)?;
    if replay_session(&mut coordinator, &session, &mut session_oracle)?
        != SessionReplayOutcome::Current
    {
        return Err(Error::ExperimentState(
            "a completed Phase 3 session replayed as failed".to_owned(),
        ));
    }
    if session_oracle.call_cursor != session_oracle.calls.len() {
        return Err(Error::ExperimentState(
            "the stored Oracle call tape extends beyond the replayed learning state".to_owned(),
        ));
    }
    if coordinator.progress() != AdaptiveLearningProgress::Complete {
        return Err(Error::ExperimentState(
            "the stored complete session does not reconstruct a complete coordinator".to_owned(),
        ));
    }
    let completed = coordinator.into_completed().map_err(|_| {
        Error::Invariant("complete coordinator rejected its read-only handoff".to_owned())
    })?;
    let handoff = completed_handoff(&session.binding, &completed, &session.rounds)?;
    if session.completion.as_ref() != Some(&handoff) {
        return Err(Error::ExperimentState(
            "the persisted Phase 3 handoff does not match deterministic replay".to_owned(),
        ));
    }
    Ok(Box::new(completed))
}

fn legacy_order_rating_instructions() -> String {
    format!(
        "{}\n{LEGACY_ORDER_WRONG_LANGUAGE_RULE}\n",
        LEGACY_ORDER_RATING_ANCHORS.join("\n")
    )
}

fn legacy_order_rating_prompt() -> String {
    format!("{LEGACY_ORDER_RATING_QUESTION}{LEGACY_ORDER_RATING_SUFFIX}")
}

fn evaluator_protocol_binding() -> EvaluatorProtocolBinding {
    EvaluatorProtocolBinding {
        question: RATING_QUESTION.to_owned(),
        rating_anchors: RATING_ANCHORS.map(str::to_owned),
        wrong_language_rule: WRONG_LANGUAGE_RULE.to_owned(),
        controls: EvaluatorControlsBinding {
            accepted_ratings: [1, 2, 3, 4, 5, 6, 7],
            wrong_language_key: "L".to_owned(),
            decision_confirmation_key: "Enter".to_owned(),
            next_rating_key: "Ctrl-N".to_owned(),
            previous_rating_key: "Ctrl-P".to_owned(),
            next_rating_from_non_rating_selection: 1,
            previous_rating_from_non_rating_selection: 7,
            pause_after_decision_key: "P".to_owned(),
            pause_after_decision_cancel_key: "Escape".to_owned(),
            recovery_redisplay_key: "R".to_owned(),
            letter_keys_case_insensitive: true,
            rest_continue_keys: ["Enter".to_owned(), "Space".to_owned(), "C".to_owned()],
            rest_pause_keys: ["P".to_owned(), "Q".to_owned(), "Escape".to_owned()],
            immediate_pause_key: "Ctrl-C".to_owned(),
        },
        input_policy: EvaluatorInputPolicyBinding {
            fresh_key_press_only: true,
            paste_accepted: false,
            repeat_accepted: false,
            release_accepted: false,
            unlisted_command_modifiers_accepted: false,
            selection_confirmation_required: true,
            new_selection_replaces_unconfirmed: true,
            selection_discarded_on_screen_exit: true,
            pause_cancel_preserves_selection: true,
            rating_navigation_wraps: false,
            stale_input_discarded_before_screen: true,
            queued_ctrl_c_pause_preserved: true,
        },
        wrong_language_counts_toward_rest: true,
        rest_interval: REST_INTERVAL,
    }
}

/// Run a new session or resume its first incomplete evaluator input through a
/// provenance-free evaluator boundary.
pub fn run_adaptive_learning<O, U>(
    config: &AdaptiveLearningRunnerConfig,
    oracle: &mut O,
    evaluator: &mut U,
) -> Result<AdaptiveLearningRunnerOutcome>
where
    O: CandidateOrderOracle,
    U: EvaluatorUi,
{
    run_adaptive_learning_with_initial_presentations(config, &BTreeMap::new(), oracle, evaluator)
}

/// Run a session whose immutable initial no-repeat ledger came from seed
/// screening. The entries affect only exact-ID presentation eligibility.
pub fn run_adaptive_learning_with_initial_presentations<O, U>(
    config: &AdaptiveLearningRunnerConfig,
    initial_presentations: &BTreeMap<EventId, PriorPresentation>,
    oracle: &mut O,
    evaluator: &mut U,
) -> Result<AdaptiveLearningRunnerOutcome>
where
    O: CandidateOrderOracle,
    U: EvaluatorUi,
{
    let fixed_binding = validate_config(config, initial_presentations, oracle)?;
    let _session_lock = acquire_session_lock(&config.session_path)?;
    protect_existing_private_file(&config.session_path)?;
    protect_existing_private_file(&atomic_temporary_path(&config.session_path)?)?;
    let cache_dir = oracle_cache_dir(&config.session_path)?;
    prepare_private_cache_directory(&cache_dir)?;
    let loaded = if config.session_path.exists() {
        let session: AdaptiveLearningSession = read_manifest(&config.session_path)?;
        validate_loaded_static_session(&session, &fixed_binding)?;
        Some(session)
    } else {
        None
    };

    evaluator
        .preparing()
        .map_err(|source| io_error("write", "<terminal-output>", source))?;

    let mut corpus = None;
    let mut session_oracle = SessionOracle::new(
        oracle,
        cache_dir,
        loaded
            .as_ref()
            .map(|session| session.oracle_calls.clone())
            .unwrap_or_default(),
        loaded
            .as_ref()
            .map(|session| session.oracle_responses.clone())
            .unwrap_or_default(),
        loaded
            .as_ref()
            .map(|session| session.vector_responses.clone())
            .unwrap_or_default(),
    )?;
    let (compact, rbf, seed_evidence) = build_seed_controllers(config, &mut session_oracle)?;
    let binding = build_session_binding(fixed_binding, seed_evidence)?;
    let mut session = match loaded {
        Some(mut session) => {
            if session.binding != binding {
                return Err(Error::ExperimentState(
                    "the stored seed evidence does not match this immutable session".to_owned(),
                ));
            }
            sync_oracle_state(&mut session, &session_oracle);
            session
        }
        None => {
            let mut session = AdaptiveLearningSession {
                schema_version: SESSION_SCHEMA_VERSION,
                binding,
                phase: SessionPhase::Learning,
                rounds: Vec::new(),
                oracle_calls: Vec::new(),
                oracle_responses: Vec::new(),
                vector_responses: Vec::new(),
                pending_presentation: None,
                rest_checkpoints: Vec::new(),
                pause_checkpoints: Vec::new(),
                completion: None,
                pause_reason: None,
                failure: None,
            };
            sync_oracle_state(&mut session, &session_oracle);
            save_session(&config.session_path, &session)?;
            session
        }
    };
    let mut coordinator = AdaptiveLearningCoordinator::new_with_initial_presentations(
        &session_oracle,
        compact,
        rbf,
        config.b16.clone(),
        initial_presentations.clone(),
    )
    .map_err(adaptive_error)?;
    if replay_session(&mut coordinator, &session, &mut session_oracle)?
        == SessionReplayOutcome::Failed
    {
        let failure = session.failure.as_ref().ok_or_else(|| {
            Error::Invariant("replayed failure has no persisted failure".to_owned())
        })?;
        return Err(Error::ExperimentState(failure.reason.clone()));
    }
    if session_oracle.call_cursor != session_oracle.calls.len() {
        return Err(Error::ExperimentState(
            "the stored Oracle call tape extends beyond the replayed learning state".to_owned(),
        ));
    }

    loop {
        match coordinator.progress() {
            AdaptiveLearningProgress::Ready => {
                if !take_due_rest(config, &mut session, &session_oracle, evaluator)? {
                    return Ok(AdaptiveLearningRunnerOutcome::Paused);
                }
                if !show_preparing(config, &mut session, &session_oracle, evaluator)? {
                    return Ok(AdaptiveLearningRunnerOutcome::Paused);
                }
                let round = coordinator.next_round().ok_or_else(|| {
                    Error::Invariant("ready learning coordinator has no next round".to_owned())
                })?;
                let completed_before = coordinator.round_records().len();
                if let Err(error) = coordinator.start_next_round(&mut session_oracle) {
                    return record_coordinator_failure(
                        config,
                        &mut session,
                        &session_oracle,
                        &coordinator,
                        PersistedFailureTransition::StartRound { round },
                        error,
                    );
                }
                sync_oracle_state(&mut session, &session_oracle);
                if coordinator.round_records().len() == completed_before + 1 {
                    let diagnostic_seal = completed_round_seal(&coordinator, round)?;
                    session.rounds.push(RoundTranscript {
                        round,
                        waves: Vec::new(),
                        ratings_submitted: true,
                        diagnostic_seal: Some(diagnostic_seal),
                    });
                    save_session(&config.session_path, &session)?;
                    continue;
                }
                let wave = coordinator.pending_language_wave().ok_or_else(|| {
                    Error::Invariant(
                        "a started learning round produced neither completion nor a language wave"
                            .to_owned(),
                    )
                })?;
                let transcript = freeze_wave(&session.binding, round, wave)?;
                session.rounds.push(RoundTranscript {
                    round,
                    waves: vec![transcript],
                    ratings_submitted: false,
                    diagnostic_seal: None,
                });
                save_session(&config.session_path, &session)?;
            }
            AdaptiveLearningProgress::AwaitingLanguage => {
                let round_index = session.rounds.len().checked_sub(1).ok_or_else(|| {
                    Error::Invariant("pending language state has no session round".to_owned())
                })?;
                let needs_derived_wave = session.rounds[round_index]
                    .waves
                    .last()
                    .is_some_and(|wave| wave.submitted);
                if needs_derived_wave {
                    if !show_preparing(config, &mut session, &session_oracle, evaluator)? {
                        return Ok(AdaptiveLearningRunnerOutcome::Paused);
                    }
                    let pending = coordinator.pending_language_wave().ok_or_else(|| {
                        Error::Invariant(
                            "language replacement state has no pending wave".to_owned(),
                        )
                    })?;
                    let round = session.rounds[round_index].round;
                    session.rounds[round_index].waves.push(freeze_wave(
                        &session.binding,
                        round,
                        pending,
                    )?);
                    save_session(&config.session_path, &session)?;
                }
                if !collect_current_wave(
                    config,
                    &mut corpus,
                    &mut session,
                    &session_oracle,
                    evaluator,
                )? {
                    return Ok(AdaptiveLearningRunnerOutcome::Paused);
                }
                let wave_index = session.rounds[round_index].waves.len() - 1;
                let outcomes = language_outcomes(&session.rounds[round_index].waves[wave_index])?;
                let wave_id = session.rounds[round_index].waves[wave_index].wave_id;
                let round_number = session.rounds[round_index].round;
                match coordinator.submit_language_outcomes(wave_id, outcomes) {
                    Ok(()) => {
                        session.rounds[round_index].waves[wave_index].submitted = true;
                    }
                    Err(error) => {
                        session.rounds[round_index].waves[wave_index].submitted = true;
                        return record_coordinator_failure(
                            config,
                            &mut session,
                            &session_oracle,
                            &coordinator,
                            PersistedFailureTransition::SubmitLanguage {
                                round: round_number,
                                wave_id,
                            },
                            error,
                        );
                    }
                }
                match coordinator.progress() {
                    AdaptiveLearningProgress::AwaitingLanguage => {
                        if !show_preparing(config, &mut session, &session_oracle, evaluator)? {
                            return Ok(AdaptiveLearningRunnerOutcome::Paused);
                        }
                        let wave = coordinator.pending_language_wave().ok_or_else(|| {
                            Error::Invariant(
                                "language replacement state has no pending wave".to_owned(),
                            )
                        })?;
                        let round = session.rounds[round_index].round;
                        session.rounds[round_index].waves.push(freeze_wave(
                            &session.binding,
                            round,
                            wave,
                        )?);
                    }
                    AdaptiveLearningProgress::Ready | AdaptiveLearningProgress::Complete => {
                        session.rounds[round_index].ratings_submitted = true;
                        let round = session.rounds[round_index].round;
                        session.rounds[round_index].diagnostic_seal =
                            Some(completed_round_seal(&coordinator, round)?);
                    }
                    AdaptiveLearningProgress::AwaitingRatings => {}
                    AdaptiveLearningProgress::Paused => {
                        return Err(Error::Invariant(
                            "successful language submission paused the coordinator".to_owned(),
                        ));
                    }
                }
                save_session(&config.session_path, &session)?;
            }
            AdaptiveLearningProgress::AwaitingRatings => {
                let round_number =
                    session
                        .rounds
                        .last()
                        .map(|round| round.round)
                        .ok_or_else(|| {
                            Error::Invariant(
                                "ratings are pending without a session round".to_owned(),
                            )
                        })?;
                let ratings = ratings_for_pending_round(&coordinator, &session)?;
                if let Err(error) = coordinator.submit_ratings(ratings) {
                    return record_coordinator_failure(
                        config,
                        &mut session,
                        &session_oracle,
                        &coordinator,
                        PersistedFailureTransition::SubmitRatings {
                            round: round_number,
                        },
                        error,
                    );
                }
                let round = session.rounds.last_mut().ok_or_else(|| {
                    Error::Invariant("ratings are pending without a session round".to_owned())
                })?;
                round.ratings_submitted = true;
                round.diagnostic_seal = Some(completed_round_seal(&coordinator, round.round)?);
                save_session(&config.session_path, &session)?;
            }
            AdaptiveLearningProgress::Complete => {
                let completed = coordinator.into_completed().map_err(|_| {
                    Error::Invariant("complete coordinator rejected its handoff".to_owned())
                })?;
                let handoff = completed_handoff(&session.binding, &completed, &session.rounds)?;
                if session.phase == SessionPhase::Complete {
                    if session.completion.as_ref() != Some(&handoff) {
                        return Err(Error::ExperimentState(
                            "the persisted Phase 3 handoff does not match deterministic replay"
                                .to_owned(),
                        ));
                    }
                } else {
                    session.phase = SessionPhase::Complete;
                    session.pause_reason = None;
                    session.failure = None;
                    session.completion = Some(handoff);
                    sync_oracle_state(&mut session, &session_oracle);
                    save_session(&config.session_path, &session)?;
                }
                if let Err(error) =
                    evaluator.complete(CompletionView::new(stored_presentation_count(&session)))
                {
                    return Err(io_error("write", "<terminal-output>", error));
                }
                return Ok(AdaptiveLearningRunnerOutcome::Complete(Box::new(completed)));
            }
            AdaptiveLearningProgress::Paused => {
                return Err(Error::Invariant(
                    "learning coordinator entered a paused state without returning its failed transition"
                        .to_owned(),
                ));
            }
        }
    }
}

fn validate_config<O: CandidateOrderOracle>(
    config: &AdaptiveLearningRunnerConfig,
    initial_presentations: &BTreeMap<EventId, PriorPresentation>,
    oracle: &O,
) -> Result<StaticSessionBinding> {
    validate_config_for_representation(
        config,
        initial_presentations,
        oracle.representation_version(),
    )
}

fn validate_config_for_representation(
    config: &AdaptiveLearningRunnerConfig,
    initial_presentations: &BTreeMap<EventId, PriorPresentation>,
    oracle_representation_version: &str,
) -> Result<StaticSessionBinding> {
    if config.corpus_identity.trim().is_empty() {
        return Err(Error::ExperimentState(
            "corpus identity must not be empty".to_owned(),
        ));
    }
    if config.seeds.len() != SEED_COUNT {
        return Err(Error::ExperimentState(format!(
            "Phase 3 requires exactly {SEED_COUNT} ordered positive seeds"
        )));
    }
    let mut seed_ids = BTreeSet::new();
    for seed in &config.seeds {
        if !seed_ids.insert(seed.event_id) {
            return Err(Error::ExperimentState(
                "Phase 3 seeds must have distinct event IDs".to_owned(),
            ));
        }
        if seed.rating <= 4 || seed.rating > 7 {
            return Err(Error::ExperimentState(
                "Phase 3 seeds must have positive 5–7 ratings".to_owned(),
            ));
        }
    }
    for (event_id, presentation) in initial_presentations {
        if seed_ids.contains(event_id) {
            return Err(Error::ExperimentState(
                "an initial screening presentation overlaps positive seed evidence".to_owned(),
            ));
        }
        if matches!(presentation, PriorPresentation::Rated { .. }) {
            return Err(Error::ExperimentState(
                "initial screening presentations must not contain rated evidence".to_owned(),
            ));
        }
    }
    let version = config.compact_settings.representation_version();
    if config.rbf_settings.representation_version() != version
        || config.b16.representation_version() != version
        || oracle_representation_version != version
    {
        return Err(Error::ExperimentState(
            "the Oracle, scorer settings, and B16 must use one representation version".to_owned(),
        ));
    }
    let initial_scale = match config.compact_settings.initial_scale() {
        ScaleLevel::Mass16 => 16,
        ScaleLevel::Mass64 => 64,
        ScaleLevel::Mass256 => 256,
    };
    Ok(StaticSessionBinding {
        corpus_identity: config.corpus_identity.clone(),
        representation_version: version.to_owned(),
        oracle_response_contract: ORACLE_RESPONSE_CONTRACT.to_owned(),
        compact_scale_bits: [
            config.compact_settings.scale(ScaleLevel::Mass16).to_bits(),
            config.compact_settings.scale(ScaleLevel::Mass64).to_bits(),
            config.compact_settings.scale(ScaleLevel::Mass256).to_bits(),
        ],
        compact_initial_scale: initial_scale,
        rbf_scale_bits: [
            config.rbf_settings.scale(ScaleLevel::Mass16).to_bits(),
            config.rbf_settings.scale(ScaleLevel::Mass64).to_bits(),
            config.rbf_settings.scale(ScaleLevel::Mass256).to_bits(),
        ],
        b16_bits: config.b16.distance().to_bits(),
        seeds: config
            .seeds
            .iter()
            .map(|seed| PersistedSeed {
                event_id: seed.event_id,
                rating: seed.rating,
            })
            .collect(),
        initial_presentations: initial_presentations
            .iter()
            .map(|(event_id, state)| PersistedLedgerEntry {
                event_id: *event_id,
                state: state.clone(),
            })
            .collect(),
        scorer_policy: SCORER_POLICY.to_owned(),
        evaluator_protocol: evaluator_protocol_binding(),
        shuffle_policy: SHUFFLE_POLICY.to_owned(),
        candidate_depth: CANDIDATE_DEPTH,
        learning_rounds: LEARNING_ROUNDS,
        learning_primary: CandidateOrderPhase::Learning.primary_count(),
        learning_reserve: CandidateOrderPhase::Learning.reserve_count(),
        maximum_wrong_language_presentations: MAX_WRONG_LANGUAGE_PRESENTATIONS,
    })
}

fn validate_loaded_static_session(
    session: &AdaptiveLearningSession,
    expected: &StaticSessionBinding,
) -> Result<()> {
    if session.schema_version != SESSION_SCHEMA_VERSION {
        return Err(Error::ExperimentState(format!(
            "learning session schema {} does not match {SESSION_SCHEMA_VERSION}",
            session.schema_version
        )));
    }
    if &session.binding.fixed != expected {
        return Err(Error::ExperimentState(
            "the stored Phase 3 session does not match the supplied immutable configuration"
                .to_owned(),
        ));
    }
    let expected_identity =
        binding_identity(&session.binding.fixed, &session.binding.seed_evidence)?;
    if session.binding.identity_sha256 != expected_identity {
        return Err(Error::ExperimentState(
            "the stored Phase 3 session binding identity is invalid".to_owned(),
        ));
    }
    let expected_order_identity =
        presentation_order_identity(&session.binding.fixed, &session.binding.seed_evidence)?;
    if session.binding.presentation_order_identity_sha256 != expected_order_identity {
        return Err(Error::ExperimentState(
            "the stored Phase 3 presentation-order identity is invalid".to_owned(),
        ));
    }
    let phase_is_valid = match session.phase {
        SessionPhase::Learning => session.completion.is_none() && session.failure.is_none(),
        SessionPhase::Complete => {
            session.completion.is_some()
                && session.pause_reason.is_none()
                && session.failure.is_none()
        }
        SessionPhase::Failed => {
            session.completion.is_none()
                && session.pause_reason.is_none()
                && session.failure.is_some()
        }
    };
    if !phase_is_valid {
        return Err(Error::ExperimentState(
            "the stored Phase 3 session phase markers are inconsistent".to_owned(),
        ));
    }
    if let Some(failure) = &session.failure {
        let expected = persisted_failure_sha256(
            &failure.reason,
            failure.transition,
            &failure.transition_input_sha256,
            &failure.candidate_order_attempts,
        )?;
        if failure.sha256 != expected {
            return Err(Error::ExperimentState(
                "the persisted Phase 3 failure failed its checksum".to_owned(),
            ));
        }
        let transition_input_sha256 = failed_transition_input_sha256(session, failure.transition)?;
        if failure.transition_input_sha256 != transition_input_sha256 {
            return Err(Error::ExperimentState(
                "the persisted Phase 3 failed transition input failed its checksum".to_owned(),
            ));
        }
        validate_candidate_order_attempt_seals(&failure.candidate_order_attempts)?;
    }
    if let Some(completion) = &session.completion {
        validate_candidate_order_attempt_seals(&completion.failed_candidate_order_attempts)?;
    }
    for round in &session.rounds {
        if round.ratings_submitted != round.diagnostic_seal.is_some() {
            return Err(Error::ExperimentState(
                "a completed round diagnostic does not match its stored completion marker"
                    .to_owned(),
            ));
        }
        if let Some(seal) = &round.diagnostic_seal
            && seal.round != round.round
        {
            return Err(Error::ExperimentState(
                "a completed round diagnostic identifies the wrong learning round".to_owned(),
            ));
        }
    }
    validate_pending_presentation(session)?;
    validate_rest_checkpoints(session)?;
    validate_pause_checkpoints(session)?;
    Ok(())
}

fn validate_rest_checkpoints(session: &AdaptiveLearningSession) -> Result<()> {
    let presentations = stored_presentation_count(session);
    let completed_boundary_count = presentations.saturating_sub(1) / REST_INTERVAL;
    let current_boundary_count =
        usize::from(presentations != 0 && presentations % REST_INTERVAL == 0);
    let checkpoint_count = session.rest_checkpoints.len();
    if checkpoint_count < completed_boundary_count
        || checkpoint_count > completed_boundary_count + current_boundary_count
    {
        return Err(Error::ExperimentState(
            "the stored evaluator rest checkpoints are invalid".to_owned(),
        ));
    }
    for (index, checkpoint) in session.rest_checkpoints.iter().enumerate() {
        let expected_boundary = (index + 1).checked_mul(REST_INTERVAL).ok_or_else(|| {
            Error::ExperimentState("the stored evaluator rest checkpoints are invalid".to_owned())
        })?;
        if checkpoint.after_presentations != expected_boundary
            || checkpoint.after_presentations > presentations
            || (checkpoint.after_presentations < presentations && !checkpoint.continued)
        {
            return Err(Error::ExperimentState(
                "the stored evaluator rest checkpoints are invalid".to_owned(),
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
            "a pending evaluator rest cannot coexist with a pending presentation".to_owned(),
        ));
    }
    Ok(())
}

fn validate_pause_checkpoints(session: &AdaptiveLearningSession) -> Result<()> {
    let presentations = stored_presentation_count(session);
    let mut previous = None;
    for checkpoint in &session.pause_checkpoints {
        if checkpoint.reason.trim().is_empty()
            || checkpoint.after_presentations > presentations
            || previous.is_some_and(|previous| checkpoint.after_presentations < previous)
        {
            return Err(Error::ExperimentState(
                "the stored evaluator pause checkpoints are invalid".to_owned(),
            ));
        }
        previous = Some(checkpoint.after_presentations);
    }
    Ok(())
}

fn validate_candidate_order_attempt_seals(attempts: &[SealedCandidateOrderAttempt]) -> Result<()> {
    for attempt in attempts {
        let expected = diagnostic_sha256("candidate-order-attempt", &attempt.record)?;
        if attempt.sha256 != expected {
            return Err(Error::ExperimentState(
                "a persisted candidate-order diagnostic failed its checksum".to_owned(),
            ));
        }
    }
    Ok(())
}

fn validate_pending_presentation(session: &AdaptiveLearningSession) -> Result<()> {
    let Some(pending) = session.pending_presentation else {
        return Ok(());
    };
    if session.phase != SessionPhase::Learning {
        return Err(Error::ExperimentState(
            "only an active learning session may retain a pending presentation".to_owned(),
        ));
    }
    let round = session.rounds.last().ok_or_else(|| {
        Error::ExperimentState("pending presentation has no learning round".to_owned())
    })?;
    let wave = round.waves.last().ok_or_else(|| {
        Error::ExperimentState("pending presentation has no learning wave".to_owned())
    })?;
    let next_event_id = wave.presentation_order.get(wave.decisions.len()).copied();
    if wave.submitted
        || round.round != pending.round
        || wave.wave_id != pending.wave_id
        || next_event_id != Some(pending.event_id)
    {
        return Err(Error::ExperimentState(
            "pending presentation does not identify the next event in the final frozen wave"
                .to_owned(),
        ));
    }
    Ok(())
}

fn build_seed_controllers<O: CandidateOrderOracle>(
    config: &AdaptiveLearningRunnerConfig,
    oracle: &mut O,
) -> Result<(
    CompactLearningController,
    RbfLearningController,
    SeedEvidenceBinding,
)> {
    let event_ids = config
        .seeds
        .iter()
        .map(|seed| seed.event_id)
        .collect::<Vec<_>>();
    let response =
        oracle.vectors_for_notes(&event_ids, config.compact_settings.representation_version())?;
    validate_seed_vector_response(
        &response,
        &event_ids,
        config.compact_settings.representation_version(),
    )?;
    let evidence = response
        .vectors
        .into_iter()
        .zip(config.seeds.iter())
        .map(|(stored, seed)| {
            EvidenceNote::new(stored.event_id, stored.vector, seed.rating)
                .map_err(|error| Error::ExperimentState(error.to_string()))
        })
        .collect::<Result<Vec<_>>>()?;
    let compact = CompactLearningController::new(config.compact_settings.clone(), evidence.clone())
        .map_err(|error| Error::ExperimentState(error.to_string()))?;
    let rbf = RbfLearningController::new(config.rbf_settings.clone(), evidence)
        .map_err(|error| Error::ExperimentState(error.to_string()))?;
    if compact.evidence_identity() != rbf.evidence_identity() {
        return Err(Error::Invariant(
            "shared seed evidence produced different controller identities".to_owned(),
        ));
    }
    let binding = evidence_binding(compact.evidence_identity());
    Ok((compact, rbf, binding))
}

fn validate_seed_vector_response(
    response: &VectorsForNotesResponse,
    expected_ids: &[EventId],
    expected_version: &str,
) -> Result<()> {
    if response.representation_version != expected_version
        || !response.complete
        || response.represented_rows == 0
        || response.represented_rows != response.total_rows
        || response.vectors.len() != expected_ids.len()
        || response
            .vectors
            .iter()
            .map(|stored| stored.event_id)
            .ne(expected_ids.iter().copied())
    {
        return Err(Error::ExperimentState(
            "the Oracle returned invalid or incomplete seed vectors".to_owned(),
        ));
    }
    Ok(())
}

fn build_session_binding(
    fixed: StaticSessionBinding,
    seed_evidence: SeedEvidenceBinding,
) -> Result<SessionBinding> {
    let identity_sha256 = binding_identity(&fixed, &seed_evidence)?;
    let presentation_order_identity_sha256 = presentation_order_identity(&fixed, &seed_evidence)?;
    Ok(SessionBinding {
        fixed,
        seed_evidence,
        identity_sha256,
        presentation_order_identity_sha256,
    })
}

fn binding_identity(
    fixed: &StaticSessionBinding,
    seed_evidence: &SeedEvidenceBinding,
) -> Result<String> {
    let bytes = serde_json::to_vec(&(fixed, seed_evidence)).map_err(|source| Error::Manifest {
        operation: "encode",
        path: PathBuf::from("<phase3-session-binding>"),
        source,
    })?;
    Ok(hash_bytes(&bytes))
}

fn presentation_order_identity(
    fixed: &StaticSessionBinding,
    seed_evidence: &SeedEvidenceBinding,
) -> Result<String> {
    let compatibility = LegacyPresentationOrderBinding {
        corpus_identity: &fixed.corpus_identity,
        representation_version: &fixed.representation_version,
        oracle_response_contract: &fixed.oracle_response_contract,
        compact_scale_bits: fixed.compact_scale_bits,
        compact_initial_scale: fixed.compact_initial_scale,
        rbf_scale_bits: fixed.rbf_scale_bits,
        b16_bits: fixed.b16_bits,
        seeds: &fixed.seeds,
        scorer_policy: &fixed.scorer_policy,
        rating_prompt: legacy_order_rating_prompt(),
        rating_instructions: legacy_order_rating_instructions(),
        shuffle_policy: &fixed.shuffle_policy,
        candidate_depth: fixed.candidate_depth,
        learning_rounds: fixed.learning_rounds,
        learning_primary: fixed.learning_primary,
        learning_reserve: fixed.learning_reserve,
        maximum_wrong_language_presentations: fixed.maximum_wrong_language_presentations,
    };
    let bytes =
        serde_json::to_vec(&(compatibility, seed_evidence)).map_err(|source| Error::Manifest {
            operation: "encode",
            path: PathBuf::from("<phase3-presentation-order-binding>"),
            source,
        })?;
    Ok(hash_bytes(&bytes))
}

fn evidence_binding(identity: &EvidenceIdentity) -> SeedEvidenceBinding {
    SeedEvidenceBinding {
        event_count: identity.event_count(),
        vector_dimensions: identity.vector_dimensions(),
        sha256: identity.sha256().to_owned(),
    }
}

fn replay_session<O: CandidateOrderOracle + ?Sized>(
    coordinator: &mut AdaptiveLearningCoordinator,
    session: &AdaptiveLearningSession,
    oracle: &mut SessionOracle<'_, O>,
) -> Result<SessionReplayOutcome> {
    for (round_index, transcript) in session.rounds.iter().enumerate() {
        if transcript.round != round_index + 1 || coordinator.next_round() != Some(transcript.round)
        {
            return Err(Error::ExperimentState(
                "the stored learning rounds are not a contiguous coordinator transcript".to_owned(),
            ));
        }
        let completed_before = coordinator.round_records().len();
        if let Err(error) = coordinator.start_next_round(oracle) {
            return verify_replayed_failure(
                coordinator,
                session,
                oracle,
                PersistedFailureTransition::StartRound {
                    round: transcript.round,
                },
                error,
            );
        }
        if transcript.waves.is_empty() {
            if !transcript.ratings_submitted
                || coordinator.round_records().len() != completed_before + 1
            {
                return Err(Error::ExperimentState(
                    "a no-input learning round does not match coordinator replay".to_owned(),
                ));
            }
            verify_completed_round_seal(coordinator, transcript)?;
            continue;
        }

        for (wave_index, wave) in transcript.waves.iter().enumerate() {
            let pending = coordinator.pending_language_wave().ok_or_else(|| {
                Error::ExperimentState(
                    "the stored language wave has no matching coordinator wave".to_owned(),
                )
            })?;
            verify_wave(&session.binding, transcript.round, pending, wave)?;
            if !wave.submitted {
                if round_index + 1 != session.rounds.len()
                    || wave_index + 1 != transcript.waves.len()
                    || transcript.ratings_submitted
                {
                    return Err(Error::ExperimentState(
                        "an incomplete language wave is not the final stored transition".to_owned(),
                    ));
                }
                return Ok(SessionReplayOutcome::Current);
            }
            if wave.decisions.len() != wave.presentation_order.len() {
                return Err(Error::ExperimentState(
                    "a submitted language wave is missing staged decisions".to_owned(),
                ));
            }
            if let Err(error) =
                coordinator.submit_language_outcomes(wave.wave_id, language_outcomes(wave)?)
            {
                return verify_replayed_failure(
                    coordinator,
                    session,
                    oracle,
                    PersistedFailureTransition::SubmitLanguage {
                        round: transcript.round,
                        wave_id: wave.wave_id,
                    },
                    error,
                );
            }
        }

        if transcript.ratings_submitted {
            if coordinator.progress() == AdaptiveLearningProgress::AwaitingRatings {
                let ratings = ratings_for_round(coordinator, transcript)?;
                if let Err(error) = coordinator.submit_ratings(ratings) {
                    return verify_replayed_failure(
                        coordinator,
                        session,
                        oracle,
                        PersistedFailureTransition::SubmitRatings {
                            round: transcript.round,
                        },
                        error,
                    );
                }
            }
            if coordinator.round_records().len() != completed_before + 1 {
                return Err(Error::ExperimentState(
                    "a completed stored round did not complete during coordinator replay"
                        .to_owned(),
                ));
            }
            verify_completed_round_seal(coordinator, transcript)?;
        } else if session.failure.as_ref().is_some_and(|failure| {
            failure.transition
                == PersistedFailureTransition::SubmitRatings {
                    round: transcript.round,
                }
        }) {
            if round_index + 1 != session.rounds.len()
                || coordinator.progress() != AdaptiveLearningProgress::AwaitingRatings
            {
                return Err(Error::ExperimentState(
                    "the persisted failed rating transition is not the final replay state"
                        .to_owned(),
                ));
            }
            let ratings = ratings_for_round(coordinator, transcript)?;
            match coordinator.submit_ratings(ratings) {
                Err(error) => {
                    return verify_replayed_failure(
                        coordinator,
                        session,
                        oracle,
                        PersistedFailureTransition::SubmitRatings {
                            round: transcript.round,
                        },
                        error,
                    );
                }
                Ok(()) => {
                    return Err(Error::ExperimentState(
                        "the persisted failed rating transition did not recur during deterministic replay"
                            .to_owned(),
                    ));
                }
            }
        } else {
            if transcript.diagnostic_seal.is_some() {
                return Err(Error::ExperimentState(
                    "an incomplete learning round has a completed round diagnostic".to_owned(),
                ));
            }
            if round_index + 1 != session.rounds.len()
                || !matches!(
                    coordinator.progress(),
                    AdaptiveLearningProgress::AwaitingRatings
                        | AdaptiveLearningProgress::AwaitingLanguage
                )
            {
                return Err(Error::ExperimentState(
                    "an incomplete rating transition is not the final stored state".to_owned(),
                ));
            }
            if session.phase == SessionPhase::Failed {
                return Err(Error::ExperimentState(
                    "the persisted failed transition did not recur during deterministic replay"
                        .to_owned(),
                ));
            }
            return Ok(SessionReplayOutcome::Current);
        }
    }

    if session.phase == SessionPhase::Failed {
        let failure = session.failure.as_ref().ok_or_else(|| {
            Error::ExperimentState("a failed session has no persisted failure".to_owned())
        })?;
        let PersistedFailureTransition::StartRound { round } = failure.transition else {
            return Err(Error::ExperimentState(
                "the persisted failed transition did not recur during deterministic replay"
                    .to_owned(),
            ));
        };
        if coordinator.next_round() != Some(round) {
            return Err(Error::ExperimentState(
                "the persisted failed start-round transition identifies the wrong round".to_owned(),
            ));
        }
        return match coordinator.start_next_round(oracle) {
            Err(error) => verify_replayed_failure(
                coordinator,
                session,
                oracle,
                PersistedFailureTransition::StartRound { round },
                error,
            ),
            Ok(()) => Err(Error::ExperimentState(
                "the persisted failed start-round transition did not recur during deterministic replay"
                    .to_owned(),
            )),
        };
    }

    match session.phase {
        SessionPhase::Complete if coordinator.progress() != AdaptiveLearningProgress::Complete => {
            Err(Error::ExperimentState(
                "the stored complete session does not reconstruct a complete coordinator"
                    .to_owned(),
            ))
        }
        SessionPhase::Learning if coordinator.progress() == AdaptiveLearningProgress::Complete => {
            Ok(SessionReplayOutcome::Current)
        }
        _ => Ok(SessionReplayOutcome::Current),
    }
}

fn verify_replayed_failure<O: CandidateOrderOracle + ?Sized>(
    coordinator: &AdaptiveLearningCoordinator,
    session: &AdaptiveLearningSession,
    oracle: &SessionOracle<'_, O>,
    transition: PersistedFailureTransition,
    error: AdaptiveLearningError,
) -> Result<SessionReplayOutcome> {
    let Some(stored) = session.failure.as_ref() else {
        return Err(adaptive_error(error));
    };
    let replayed = persisted_failure_record(
        coordinator,
        error.to_string(),
        transition,
        failed_transition_input_sha256(session, transition)?,
    )?;
    if &replayed != stored || oracle.call_cursor != oracle.calls.len() {
        return Err(Error::ExperimentState(
            "the persisted Phase 3 failure does not match deterministic replay".to_owned(),
        ));
    }
    Ok(SessionReplayOutcome::Failed)
}

fn completed_round_seal(
    coordinator: &AdaptiveLearningCoordinator,
    expected_round: usize,
) -> Result<PersistedRoundSeal> {
    let record = coordinator.round_records().last().ok_or_else(|| {
        Error::Invariant("a completed learning round has no round record".to_owned())
    })?;
    if record.round() != expected_round {
        return Err(Error::Invariant(format!(
            "completed round record {} does not match expected round {expected_round}",
            record.round()
        )));
    }
    persisted_round_seal(record, coordinator.failed_candidate_order_attempts())
}

fn verify_completed_round_seal(
    coordinator: &AdaptiveLearningCoordinator,
    transcript: &RoundTranscript,
) -> Result<()> {
    let stored = transcript.diagnostic_seal.as_ref().ok_or_else(|| {
        Error::ExperimentState(
            "a completed learning round is missing its completed round diagnostic".to_owned(),
        )
    })?;
    let replayed = completed_round_seal(coordinator, transcript.round)?;
    if stored != &replayed {
        return Err(Error::ExperimentState(format!(
            "completed round diagnostic for learning round {} does not match deterministic replay",
            transcript.round
        )));
    }
    Ok(())
}

fn freeze_wave(
    binding: &SessionBinding,
    round: usize,
    wave: &crate::quota_resolution::PresentationWave,
) -> Result<WaveTranscript> {
    let mut unique = wave.event_ids().iter().copied().collect::<BTreeSet<_>>();
    if unique.len() != wave.event_ids().len() {
        return Err(Error::Invariant(
            "the coordinator produced a duplicated presentation wave".to_owned(),
        ));
    }
    let mut presentation_order = unique.iter().copied().collect::<Vec<_>>();
    presentation_order.sort_by(|left, right| {
        presentation_key(binding, round, wave.wave_id(), *left)
            .cmp(&presentation_key(binding, round, wave.wave_id(), *right))
            .then_with(|| left.cmp(right))
    });
    unique.clear();
    Ok(WaveTranscript {
        wave_id: wave.wave_id(),
        coordinator_event_ids: wave.event_ids().to_vec(),
        presentation_order,
        decisions: Vec::new(),
        submitted: false,
    })
}

fn verify_wave(
    binding: &SessionBinding,
    round: usize,
    pending: &crate::quota_resolution::PresentationWave,
    stored: &WaveTranscript,
) -> Result<()> {
    if pending.wave_id() != stored.wave_id || pending.event_ids() != stored.coordinator_event_ids {
        return Err(Error::ExperimentState(
            "the stored language wave differs from coordinator replay".to_owned(),
        ));
    }
    let expected = freeze_wave(binding, round, pending)?;
    if stored.presentation_order != expected.presentation_order
        || stored.decisions.len() > stored.presentation_order.len()
        || stored
            .decisions
            .iter()
            .zip(&stored.presentation_order)
            .any(|(decision, event_id)| decision.event_id() != *event_id)
    {
        return Err(Error::ExperimentState(
            "the stored concealed order or decision prefix is invalid".to_owned(),
        ));
    }
    for decision in &stored.decisions {
        if let Some(rating) = decision.rating()
            && !(1..=7).contains(&rating)
        {
            return Err(Error::ExperimentState(
                "the stored staged rating is outside 1–7".to_owned(),
            ));
        }
    }
    Ok(())
}

fn presentation_key(
    binding: &SessionBinding,
    round: usize,
    wave_id: u64,
    event_id: EventId,
) -> [u8; 32] {
    let mut hasher = Sha256::new();
    hasher.update(SHUFFLE_POLICY.as_bytes());
    hasher.update([0]);
    hasher.update(binding.presentation_order_identity_sha256.as_bytes());
    hasher.update([0]);
    hasher.update(round.to_le_bytes());
    hasher.update(wave_id.to_le_bytes());
    hasher.update(event_id);
    hasher.finalize().into()
}

fn stored_presentation_count(session: &AdaptiveLearningSession) -> usize {
    session
        .rounds
        .iter()
        .flat_map(|round| &round.waves)
        .map(|wave| wave.decisions.len())
        .sum()
}

fn presentations_until_rest(session: &AdaptiveLearningSession) -> usize {
    let remainder = stored_presentation_count(session) % REST_INTERVAL;
    if remainder == 0 {
        REST_INTERVAL
    } else {
        REST_INTERVAL - remainder
    }
}

fn record_pause_checkpoint(session: &mut AdaptiveLearningSession, reason: &str) {
    let checkpoint = PauseCheckpoint {
        after_presentations: stored_presentation_count(session),
        reason: reason.to_owned(),
    };
    if session.pause_checkpoints.last() != Some(&checkpoint) {
        session.pause_checkpoints.push(checkpoint);
    }
}

fn show_preparing<O, U>(
    config: &AdaptiveLearningRunnerConfig,
    session: &mut AdaptiveLearningSession,
    oracle: &SessionOracle<'_, O>,
    evaluator: &mut U,
) -> Result<bool>
where
    O: CandidateOrderOracle + ?Sized,
    U: EvaluatorUi,
{
    match evaluator.preparing() {
        Ok(()) => Ok(true),
        Err(error) => {
            persist_recoverable_pause(
                config,
                session,
                oracle,
                &format!("terminal failed while preparing the next wave: {error}"),
            )?;
            Ok(false)
        }
    }
}

fn take_due_rest<O, U>(
    config: &AdaptiveLearningRunnerConfig,
    session: &mut AdaptiveLearningSession,
    oracle: &SessionOracle<'_, O>,
    evaluator: &mut U,
) -> Result<bool>
where
    O: CandidateOrderOracle + ?Sized,
    U: EvaluatorUi,
{
    let presentations = stored_presentation_count(session);
    if presentations == 0 || presentations % REST_INTERVAL != 0 {
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
            sync_oracle_state(session, oracle);
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
            sync_oracle_state(session, oracle);
            save_session(&config.session_path, session)?;
            Ok(true)
        }
        Ok(RestOutcome::Paused) => {
            persist_recoverable_pause(
                config,
                session,
                oracle,
                "evaluator paused at a scheduled rest",
            )?;
            Ok(false)
        }
        Err(error) => {
            persist_recoverable_pause(
                config,
                session,
                oracle,
                &format!("terminal failed at a scheduled rest: {error}"),
            )?;
            Ok(false)
        }
    }
}

fn collect_current_wave<O, U>(
    config: &AdaptiveLearningRunnerConfig,
    corpus: &mut Option<Ndb>,
    session: &mut AdaptiveLearningSession,
    oracle: &SessionOracle<'_, O>,
    evaluator: &mut U,
) -> Result<bool>
where
    O: CandidateOrderOracle + ?Sized,
    U: EvaluatorUi,
{
    let mut loaded_contents = None;
    loop {
        let round_index = session.rounds.len().checked_sub(1).ok_or_else(|| {
            Error::Invariant("pending language input has no session round".to_owned())
        })?;
        let wave_index = session.rounds[round_index]
            .waves
            .len()
            .checked_sub(1)
            .ok_or_else(|| Error::Invariant("pending language input has no wave".to_owned()))?;
        let wave = &session.rounds[round_index].waves[wave_index];
        if wave.submitted {
            return Err(Error::Invariant(
                "submitted language wave requested evaluator input".to_owned(),
            ));
        }
        if wave.decisions.len() == wave.presentation_order.len() {
            return Ok(true);
        }
        let event_id = wave.presentation_order[wave.decisions.len()];
        let round = session.rounds[round_index].round;
        let wave_id = wave.wave_id;
        if let Some(pending) = session.pending_presentation
            && (pending.round != round
                || pending.wave_id != wave_id
                || pending.event_id != event_id)
        {
            return Err(Error::Invariant(
                "pending presentation does not match the next frozen event".to_owned(),
            ));
        }

        let mut submission = None;
        let mut display_requested = session.pending_presentation.is_none();
        if session.pending_presentation.is_some() {
            let view = RecoveryView::new(
                stored_presentation_count(session) + 1,
                presentations_until_rest(session),
            );
            match evaluator.recover(view) {
                Ok(RecoveryOutcome::Submitted(value)) => submission = Some(value),
                Ok(RecoveryOutcome::Redisplay) => {
                    display_requested = true;
                }
                Ok(RecoveryOutcome::Paused) => {
                    persist_recoverable_pause(
                        config,
                        session,
                        oracle,
                        "evaluator paused with an uncertain presentation",
                    )?;
                    return Ok(false);
                }
                Err(error) => {
                    persist_recoverable_pause(
                        config,
                        session,
                        oracle,
                        &format!("terminal failed during presentation recovery: {error}"),
                    )?;
                    return Ok(false);
                }
            }
        } else if !take_due_rest(config, session, oracle, evaluator)? {
            return Ok(false);
        }

        if display_requested {
            if loaded_contents.is_none() {
                let remaining = session.rounds[round_index].waves[wave_index].presentation_order
                    [session.rounds[round_index].waves[wave_index]
                        .decisions
                        .len()..]
                    .to_vec();
                let contents =
                    match preload_raw_note_contents(corpus, &config.corpus_path, &remaining) {
                        Ok(contents) => contents,
                        Err(error) => {
                            let reason = format!(
                                "display corpus unavailable for learning event {}: {error}",
                                hex_event_id(event_id)
                            );
                            persist_recoverable_pause(config, session, oracle, &reason)?;
                            return Ok(false);
                        }
                    };
                loaded_contents = Some(contents);
            }
            let content = match loaded_contents
                .as_ref()
                .and_then(|contents| contents.get(&event_id))
            {
                Some(PreloadedNoteContent::Available(content)) => content,
                Some(PreloadedNoteContent::Unavailable(error)) => {
                    let reason = format!(
                        "display corpus unavailable for learning event {}: {error}",
                        hex_event_id(event_id)
                    );
                    persist_recoverable_pause(config, session, oracle, &reason)?;
                    return Ok(false);
                }
                None => {
                    return Err(Error::Invariant(
                        "preloaded display wave is missing its next event".to_owned(),
                    ));
                }
            };
            if session.pending_presentation.is_none() {
                session.pending_presentation = Some(PendingPresentation {
                    round,
                    wave_id,
                    event_id,
                });
                session.pause_reason = None;
                sync_oracle_state(session, oracle);
                save_session(&config.session_path, session)?;
            }
            let view = RatingView::new(
                content,
                stored_presentation_count(session) + 1,
                presentations_until_rest(session),
            );
            match evaluator.rate(view) {
                Ok(RatingOutcome::Submitted(value)) => submission = Some(value),
                Ok(RatingOutcome::Paused) => {
                    persist_recoverable_pause(
                        config,
                        session,
                        oracle,
                        "evaluator paused before rating the pending presentation",
                    )?;
                    return Ok(false);
                }
                Err(error) => {
                    persist_recoverable_pause(
                        config,
                        session,
                        oracle,
                        &format!("terminal failed while requesting a rating: {error}"),
                    )?;
                    return Ok(false);
                }
            }
        }

        let submission = submission.ok_or_else(|| {
            Error::Invariant("evaluator returned no decision for the current note".to_owned())
        })?;
        store_evaluator_submission(
            config,
            session,
            oracle,
            round_index,
            wave_index,
            event_id,
            submission,
        )?;
        if submission.pause_after() {
            return Ok(false);
        }
    }
}

#[allow(clippy::too_many_arguments)]
fn store_evaluator_submission<O>(
    config: &AdaptiveLearningRunnerConfig,
    session: &mut AdaptiveLearningSession,
    oracle: &SessionOracle<'_, O>,
    round_index: usize,
    wave_index: usize,
    event_id: EventId,
    submission: EvaluatorSubmission,
) -> Result<()>
where
    O: CandidateOrderOracle + ?Sized,
{
    let decision = match submission.decision() {
        EvaluatorDecision::Rating(rating) if (1..=7).contains(&rating) => {
            StagedDecision::Rated { event_id, rating }
        }
        EvaluatorDecision::Rating(_) => {
            return Err(Error::ExperimentState(
                "the evaluator returned a rating outside 1–7".to_owned(),
            ));
        }
        EvaluatorDecision::WrongLanguage => StagedDecision::WrongLanguage { event_id },
    };
    session.rounds[round_index].waves[wave_index]
        .decisions
        .push(decision);
    session.pending_presentation = None;
    if submission.pause_after() {
        let reason = "evaluator chose to pause after the accepted decision";
        session.pause_reason = Some(reason.to_owned());
        record_pause_checkpoint(session, reason);
    } else {
        session.pause_reason = None;
    }
    sync_oracle_state(session, oracle);
    save_session(&config.session_path, session)
}

fn persist_recoverable_pause<O>(
    config: &AdaptiveLearningRunnerConfig,
    session: &mut AdaptiveLearningSession,
    oracle: &SessionOracle<'_, O>,
    reason: &str,
) -> Result<()>
where
    O: CandidateOrderOracle + ?Sized,
{
    session.pause_reason = Some(reason.to_owned());
    record_pause_checkpoint(session, reason);
    sync_oracle_state(session, oracle);
    save_session(&config.session_path, session)
}

fn language_outcomes(wave: &WaveTranscript) -> Result<Vec<EventLanguageOutcome>> {
    let decisions = wave
        .decisions
        .iter()
        .copied()
        .map(|decision| (decision.event_id(), decision))
        .collect::<BTreeMap<_, _>>();
    wave.coordinator_event_ids
        .iter()
        .map(|event_id| {
            decisions
                .get(event_id)
                .copied()
                .map(|decision| EventLanguageOutcome::new(*event_id, decision.language()))
                .ok_or_else(|| {
                    Error::ExperimentState(
                        "a complete language wave is missing an event decision".to_owned(),
                    )
                })
        })
        .collect()
}

fn ratings_for_pending_round(
    coordinator: &AdaptiveLearningCoordinator,
    session: &AdaptiveLearningSession,
) -> Result<Vec<BatchRating>> {
    let round = session.rounds.last().ok_or_else(|| {
        Error::Invariant("pending coordinator ratings have no session round".to_owned())
    })?;
    ratings_for_round(coordinator, round)
}

fn ratings_for_round(
    coordinator: &AdaptiveLearningCoordinator,
    round: &RoundTranscript,
) -> Result<Vec<BatchRating>> {
    let staged = round
        .waves
        .iter()
        .flat_map(|wave| wave.decisions.iter().copied())
        .filter_map(|decision| {
            decision
                .rating()
                .map(|rating| (decision.event_id(), rating))
        })
        .collect::<BTreeMap<_, _>>();
    coordinator
        .pending_rating_event_ids()
        .ok_or_else(|| Error::Invariant("coordinator has no pending rating IDs".to_owned()))?
        .iter()
        .map(|event_id| {
            let rating = staged.get(event_id).copied().ok_or_else(|| {
                Error::ExperimentState(format!(
                    "pending event {} has no staged evaluator rating",
                    hex_event_id(*event_id)
                ))
            })?;
            BatchRating::new(*event_id, rating)
                .map_err(|error| Error::ExperimentState(error.to_string()))
        })
        .collect()
}

fn preload_raw_note_contents(
    corpus: &mut Option<Ndb>,
    corpus_path: &Path,
    event_ids: &[EventId],
) -> Result<BTreeMap<EventId, PreloadedNoteContent>> {
    if corpus.is_none() {
        require_directory(corpus_path)?;
        *corpus = Some(open_existing_ndb(corpus_path, Validation::TrustedSource)?);
    }
    let corpus = corpus.as_ref().expect("display corpus was opened");
    let transaction = Transaction::new(corpus)
        .map_err(|source| ndb_error("open transaction on", corpus_path, source))?;
    Ok(event_ids
        .iter()
        .copied()
        .map(|event_id| {
            let content = match corpus.get_note_by_id(&transaction, &event_id) {
                Ok(note) => PreloadedNoteContent::Available(terminal_safe(note.content())),
                Err(source) => PreloadedNoteContent::Unavailable(
                    ndb_error("load event from", corpus_path, source).to_string(),
                ),
            };
            (event_id, content)
        })
        .collect())
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

fn completed_handoff(
    binding: &SessionBinding,
    completed: &CompletedAdaptiveLearning,
    transcripts: &[RoundTranscript],
) -> Result<CompletedHandoff> {
    let presentation_ledger = completed
        .presentation_ledger()
        .iter()
        .map(|(event_id, state)| persisted_ledger_entry(*event_id, state))
        .collect();
    let ratings = completed
        .ratings()
        .iter()
        .map(|(event_id, rating)| PersistedRating {
            event_id: *event_id,
            rating: rating.value(),
        })
        .collect();
    if transcripts.len() != completed.round_records().len() {
        return Err(Error::Invariant(
            "completed transcript and coordinator contain different round counts".to_owned(),
        ));
    }
    let ordered_rounds = transcripts
        .iter()
        .zip(completed.round_records())
        .map(|(transcript, record)| {
            if transcript.round != record.round() {
                return Err(Error::Invariant(
                    "completed transcript and coordinator round order differ".to_owned(),
                ));
            }
            transcript.diagnostic_seal.clone().ok_or_else(|| {
                Error::Invariant("completed handoff contains an unsealed round".to_owned())
            })
        })
        .collect::<Result<Vec<_>>>()?;
    let compact_active_tuple = diagnostic_value(completed.compact_controller().active_tuple())?;
    let rbf_active_tuple = diagnostic_value(completed.rbf_controller().active_tuple())?;
    Ok(CompletedHandoff {
        binding_identity_sha256: binding.identity_sha256.clone(),
        compact_evidence: evidence_binding(completed.compact_controller().evidence_identity()),
        rbf_evidence: evidence_binding(completed.rbf_controller().evidence_identity()),
        compact_active_tuple,
        rbf_active_tuple,
        compact_rounds: completed.compact_controller().history().len(),
        rbf_rounds: completed.rbf_controller().history().len(),
        presentation_ledger,
        ratings,
        eligible_presentations: completed.language_totals().eligible_presentations(),
        wrong_language_presentations: completed.language_totals().wrong_language_presentations(),
        source_waves: completed
            .source_wave_records()
            .iter()
            .map(|record| PersistedSourceWave {
                round: record.round(),
                source_event_ids: record.source_event_ids().to_vec(),
                metrics: record.metrics().clone(),
                accepted: record.accepted(),
            })
            .collect(),
        failed_candidate_order_attempts: seal_candidate_order_attempts(
            completed.failed_candidate_order_attempts(),
        )?,
        ordered_rounds,
    })
}

fn persisted_round_seal(
    record: &SharedLearningRoundRecord,
    failed_candidate_order_attempts: &[CandidateOrderAttempt],
) -> Result<PersistedRoundSeal> {
    Ok(PersistedRoundSeal {
        round: record.round(),
        round_record_sha256: diagnostic_sha256("shared-learning-round", record)?,
        compact_candidate_pool_sha256: record
            .compact_order()
            .attempt()
            .candidate_pool_identity_sha256()
            .to_owned(),
        compact_accepted_event_ids: record
            .compact_order()
            .accepted()
            .iter()
            .map(|candidate| candidate.event_id())
            .collect(),
        compact_evidence_after: evidence_binding(record.compact_round().evidence_after()),
        rbf_candidate_pool_sha256: record
            .rbf_order()
            .attempt()
            .candidate_pool_identity_sha256()
            .to_owned(),
        rbf_accepted_event_ids: record
            .rbf_order()
            .accepted()
            .iter()
            .map(|candidate| candidate.event_id())
            .collect(),
        rbf_evidence_after: evidence_binding(record.rbf_round().evidence_after()),
        ratings: record
            .ratings()
            .iter()
            .map(|rating| PersistedRating {
                event_id: rating.event_id(),
                rating: rating.rating().value(),
            })
            .collect(),
        presentation_ledger: record
            .presentation_ledger_entries()
            .iter()
            .map(|(event_id, state)| persisted_ledger_entry(*event_id, state))
            .collect(),
        frozen_predictions_sha256: diagnostic_sha256(
            "frozen-predictions",
            &(
                record.round(),
                record.compact_round().frozen_batch(),
                record.rbf_round().frozen_batch(),
            ),
        )?,
        errors_sha256: diagnostic_sha256(
            "tuple-errors",
            &(
                record.round(),
                record.compact_round().outcomes(),
                record.compact_round().errors(),
                record.rbf_round().outcomes(),
                record.rbf_round().errors(),
            ),
        )?,
        next_tuples_sha256: diagnostic_sha256(
            "next-tuples",
            &(
                record.round(),
                record.compact_round().next_tuple(),
                record.rbf_round().next_tuple(),
            ),
        )?,
        candidate_order_audit_sha256: diagnostic_sha256(
            "candidate-order-audit",
            &(
                record.round(),
                record.compact_order().attempt(),
                record.rbf_order().attempt(),
                failed_candidate_order_attempts,
            ),
        )?,
        shared_round_audit_sha256: diagnostic_sha256(
            "shared-round-audit",
            &(record.round(), record.quota_metadata(), record.audit()),
        )?,
    })
}

fn diagnostic_sha256<T: Serialize>(kind: &str, record: &T) -> Result<String> {
    struct Sha256Writer(Sha256);

    impl Write for Sha256Writer {
        fn write(&mut self, bytes: &[u8]) -> std::io::Result<usize> {
            self.0.update(bytes);
            Ok(bytes.len())
        }

        fn flush(&mut self) -> std::io::Result<()> {
            Ok(())
        }
    }

    let mut writer = Sha256Writer(Sha256::new());
    writer
        .write_all(DIAGNOSTIC_SEAL_DOMAIN)
        .expect("SHA-256 writer cannot fail");
    writer
        .write_all(kind.as_bytes())
        .expect("SHA-256 writer cannot fail");
    writer.write_all(&[0]).expect("SHA-256 writer cannot fail");
    serde_json::to_writer(&mut writer, record).map_err(|source| Error::Manifest {
        operation: "encode",
        path: PathBuf::from("<phase3-diagnostic>"),
        source,
    })?;
    Ok(format!("{:x}", writer.0.finalize()))
}

fn persisted_failure_sha256(
    reason: &str,
    transition: PersistedFailureTransition,
    transition_input_sha256: &str,
    attempts: &[SealedCandidateOrderAttempt],
) -> Result<String> {
    diagnostic_sha256(
        "failure",
        &(reason, transition, transition_input_sha256, attempts),
    )
}

fn failed_transition_input_sha256(
    session: &AdaptiveLearningSession,
    transition: PersistedFailureTransition,
) -> Result<String> {
    match transition {
        PersistedFailureTransition::StartRound { .. } => {
            diagnostic_sha256("failed-transition-input", &transition)
        }
        PersistedFailureTransition::SubmitLanguage { round, .. }
        | PersistedFailureTransition::SubmitRatings { round } => {
            let transcript = session
                .rounds
                .iter()
                .find(|transcript| transcript.round == round)
                .ok_or_else(|| {
                    Error::ExperimentState(
                        "the persisted failed transition has no matching round transcript"
                            .to_owned(),
                    )
                })?;
            diagnostic_sha256("failed-transition-input", &(transition, transcript))
        }
    }
}

fn diagnostic_value<T: Serialize>(record: T) -> Result<serde_json::Value> {
    let bytes = serde_json::to_vec(&record).map_err(|source| Error::Manifest {
        operation: "encode",
        path: PathBuf::from("<phase3-diagnostic>"),
        source,
    })?;
    serde_json::from_slice(&bytes).map_err(|source| Error::Manifest {
        operation: "decode",
        path: PathBuf::from("<phase3-diagnostic>"),
        source,
    })
}

fn seal_candidate_order_attempts(
    attempts: &[CandidateOrderAttempt],
) -> Result<Vec<SealedCandidateOrderAttempt>> {
    attempts
        .iter()
        .map(|attempt| {
            let record = diagnostic_value(attempt)?;
            let sha256 = diagnostic_sha256("candidate-order-attempt", &record)?;
            Ok(SealedCandidateOrderAttempt { sha256, record })
        })
        .collect()
}

fn persisted_ledger_entry(event_id: EventId, state: &PriorPresentation) -> PersistedLedgerEntry {
    PersistedLedgerEntry {
        event_id,
        state: state.clone(),
    }
}

fn persisted_failure_record(
    coordinator: &AdaptiveLearningCoordinator,
    reason: String,
    transition: PersistedFailureTransition,
    transition_input_sha256: String,
) -> Result<PersistedFailure> {
    let candidate_order_attempts =
        seal_candidate_order_attempts(coordinator.failed_candidate_order_attempts())?;
    let sha256 = persisted_failure_sha256(
        &reason,
        transition,
        &transition_input_sha256,
        &candidate_order_attempts,
    )?;
    Ok(PersistedFailure {
        sha256,
        reason,
        transition,
        transition_input_sha256,
        candidate_order_attempts,
    })
}

fn record_coordinator_failure<O>(
    config: &AdaptiveLearningRunnerConfig,
    session: &mut AdaptiveLearningSession,
    oracle: &SessionOracle<'_, O>,
    coordinator: &AdaptiveLearningCoordinator,
    transition: PersistedFailureTransition,
    error: AdaptiveLearningError,
) -> Result<AdaptiveLearningRunnerOutcome>
where
    O: CandidateOrderOracle + ?Sized,
{
    let reason = error.to_string();
    if !matches!(&error, AdaptiveLearningError::PhasePaused(_)) {
        persist_recoverable_pause(config, session, oracle, &reason)?;
        return Err(adaptive_error(error));
    }
    let transition_input_sha256 = failed_transition_input_sha256(session, transition)?;
    let failure = persisted_failure_record(
        coordinator,
        reason.clone(),
        transition,
        transition_input_sha256,
    )?;
    session.phase = SessionPhase::Failed;
    session.pause_reason = None;
    session.failure = Some(failure);
    sync_oracle_state(session, oracle);
    save_session(&config.session_path, session)?;
    Err(Error::ExperimentState(reason))
}

fn adaptive_error(error: AdaptiveLearningError) -> Error {
    Error::ExperimentState(error.to_string())
}

impl<'a, O: CandidateOrderOracle + ?Sized> SessionOracle<'a, O> {
    fn new(
        inner: &'a mut O,
        cache_dir: PathBuf,
        calls: Vec<PersistedOracleCall>,
        response_refs: Vec<CachedResponseRef>,
        vector_response_refs: Vec<CachedVectorResponseRef>,
    ) -> Result<Self> {
        let representation_version = inner.representation_version().to_owned();
        Self::from_parts(
            Some(inner),
            representation_version,
            cache_dir,
            calls,
            response_refs,
            vector_response_refs,
        )
    }

    fn from_parts(
        inner: Option<&'a mut O>,
        representation_version: String,
        cache_dir: PathBuf,
        calls: Vec<PersistedOracleCall>,
        response_refs: Vec<CachedResponseRef>,
        vector_response_refs: Vec<CachedVectorResponseRef>,
    ) -> Result<Self> {
        let mut indexed = BTreeMap::new();
        for response_ref in response_refs {
            if response_ref.key.representation_version != representation_version {
                return Err(Error::ExperimentState(
                    "cached Oracle response uses a different representation".to_owned(),
                ));
            }
            if indexed
                .insert(response_ref.key.clone(), response_ref)
                .is_some()
            {
                return Err(Error::ExperimentState(
                    "the Oracle response manifest repeats a cache key".to_owned(),
                ));
            }
        }
        let mut indexed_vectors = BTreeMap::new();
        for response_ref in vector_response_refs {
            if response_ref.key.representation_version != representation_version {
                return Err(Error::ExperimentState(
                    "cached vector response uses a different representation".to_owned(),
                ));
            }
            if indexed_vectors
                .insert(response_ref.key.clone(), response_ref)
                .is_some()
            {
                return Err(Error::ExperimentState(
                    "the vector response manifest repeats a cache key".to_owned(),
                ));
            }
        }
        Ok(Self {
            inner,
            representation_version,
            cache_dir,
            calls,
            call_cursor: 0,
            response_refs: indexed,
            loaded: BTreeMap::new(),
            vector_response_refs: indexed_vectors,
            loaded_vectors: BTreeMap::new(),
        })
    }

    fn response_refs(&self) -> Vec<CachedResponseRef> {
        self.response_refs.values().cloned().collect()
    }

    fn vector_response_refs(&self) -> Vec<CachedVectorResponseRef> {
        self.vector_response_refs.values().cloned().collect()
    }

    fn load_cached(&mut self, key: &ResponseCacheKey) -> Result<SimilarNotesResponse> {
        if let Some(response) = self.loaded.get(key) {
            return Ok(response.clone());
        }
        let response_ref = self.response_refs.get(key).ok_or_else(|| {
            Error::ExperimentState("Oracle call references an absent cached response".to_owned())
        })?;
        let path = response_cache_path(&self.cache_dir, key)?;
        let bytes = fs::read(&path).map_err(|source| io_error("read", &path, source))?;
        if hash_bytes(&bytes) != response_ref.sha256 {
            return Err(Error::ExperimentState(format!(
                "cached Oracle response `{}` failed its checksum",
                path.display()
            )));
        }
        let envelope: CachedResponseEnvelope =
            serde_json::from_slice(&bytes).map_err(|source| Error::Manifest {
                operation: "decode",
                path: path.clone(),
                source,
            })?;
        if &envelope.key != key {
            return Err(Error::ExperimentState(format!(
                "cached Oracle response `{}` is bound to a different request",
                path.display()
            )));
        }
        let response = envelope.response;
        validate_cached_response(key, &response)?;
        self.loaded.insert(key.clone(), response.clone());
        Ok(response)
    }

    fn recover_cached(&mut self, key: &ResponseCacheKey) -> Result<bool> {
        if self.response_refs.contains_key(key) {
            return Ok(true);
        }
        let path = response_cache_path(&self.cache_dir, key)?;
        if !path.exists() {
            return Ok(false);
        }
        let bytes = fs::read(&path).map_err(|source| io_error("read", &path, source))?;
        let envelope: CachedResponseEnvelope =
            serde_json::from_slice(&bytes).map_err(|source| Error::Manifest {
                operation: "decode",
                path: path.clone(),
                source,
            })?;
        if &envelope.key != key {
            return Err(Error::ExperimentState(format!(
                "orphaned Oracle response `{}` is bound to a different request",
                path.display()
            )));
        }
        validate_cached_response(key, &envelope.response)?;
        let sha256 = hash_bytes(&bytes);
        self.response_refs.insert(
            key.clone(),
            CachedResponseRef {
                key: key.clone(),
                sha256,
            },
        );
        self.loaded.insert(key.clone(), envelope.response);
        Ok(true)
    }

    fn store_response(
        &mut self,
        key: ResponseCacheKey,
        response: SimilarNotesResponse,
    ) -> Result<()> {
        validate_cached_response(&key, &response)?;
        let envelope = CachedResponseEnvelope {
            key: key.clone(),
            response: response.clone(),
        };
        let bytes = serde_json::to_vec(&envelope).map_err(|source| Error::Manifest {
            operation: "encode",
            path: self.cache_dir.clone(),
            source,
        })?;
        let sha256 = hash_bytes(&bytes);
        let path = response_cache_path(&self.cache_dir, &key)?;
        if path.exists() {
            let existing = fs::read(&path).map_err(|source| io_error("read", &path, source))?;
            if existing != bytes {
                return Err(Error::Invariant(
                    "content-addressed Oracle response path contains different bytes".to_owned(),
                ));
            }
        } else {
            save_bytes_atomic(&path, &bytes)?;
        }
        self.response_refs.insert(
            key.clone(),
            CachedResponseRef {
                key: key.clone(),
                sha256,
            },
        );
        self.loaded.insert(key, response);
        Ok(())
    }

    fn load_cached_vectors(
        &mut self,
        key: &VectorResponseCacheKey,
    ) -> Result<VectorsForNotesResponse> {
        if let Some(response) = self.loaded_vectors.get(key) {
            return Ok(response.clone());
        }
        let response_ref = self.vector_response_refs.get(key).ok_or_else(|| {
            Error::ExperimentState("vector lookup references an absent cached response".to_owned())
        })?;
        let path = vector_response_cache_path(&self.cache_dir, key)?;
        let bytes = fs::read(&path).map_err(|source| io_error("read", &path, source))?;
        if hash_bytes(&bytes) != response_ref.sha256 {
            return Err(Error::ExperimentState(format!(
                "cached vector response `{}` failed its checksum",
                path.display()
            )));
        }
        let envelope: CachedVectorResponseEnvelope =
            serde_json::from_slice(&bytes).map_err(|source| Error::Manifest {
                operation: "decode",
                path: path.clone(),
                source,
            })?;
        if &envelope.key != key {
            return Err(Error::ExperimentState(format!(
                "cached vector response `{}` is bound to a different request",
                path.display()
            )));
        }
        let response = envelope.response;
        validate_cached_vector_response(key, &response)?;
        self.loaded_vectors.insert(key.clone(), response.clone());
        Ok(response)
    }

    fn recover_cached_vectors(&mut self, key: &VectorResponseCacheKey) -> Result<bool> {
        if self.vector_response_refs.contains_key(key) {
            return Ok(true);
        }
        let path = vector_response_cache_path(&self.cache_dir, key)?;
        if !path.exists() {
            return Ok(false);
        }
        let bytes = fs::read(&path).map_err(|source| io_error("read", &path, source))?;
        let envelope: CachedVectorResponseEnvelope =
            serde_json::from_slice(&bytes).map_err(|source| Error::Manifest {
                operation: "decode",
                path: path.clone(),
                source,
            })?;
        if &envelope.key != key {
            return Err(Error::ExperimentState(format!(
                "orphaned vector response `{}` is bound to a different request",
                path.display()
            )));
        }
        validate_cached_vector_response(key, &envelope.response)?;
        let sha256 = hash_bytes(&bytes);
        self.vector_response_refs.insert(
            key.clone(),
            CachedVectorResponseRef {
                key: key.clone(),
                sha256,
            },
        );
        self.loaded_vectors.insert(key.clone(), envelope.response);
        Ok(true)
    }

    fn store_vector_response(
        &mut self,
        key: VectorResponseCacheKey,
        response: VectorsForNotesResponse,
    ) -> Result<()> {
        validate_cached_vector_response(&key, &response)?;
        let envelope = CachedVectorResponseEnvelope {
            key: key.clone(),
            response: response.clone(),
        };
        let bytes = serde_json::to_vec(&envelope).map_err(|source| Error::Manifest {
            operation: "encode",
            path: self.cache_dir.clone(),
            source,
        })?;
        let sha256 = hash_bytes(&bytes);
        let path = vector_response_cache_path(&self.cache_dir, &key)?;
        if path.exists() {
            let existing = fs::read(&path).map_err(|source| io_error("read", &path, source))?;
            if existing != bytes {
                return Err(Error::Invariant(
                    "content-addressed vector response path contains different bytes".to_owned(),
                ));
            }
        } else {
            save_bytes_atomic(&path, &bytes)?;
        }
        self.vector_response_refs.insert(
            key.clone(),
            CachedVectorResponseRef {
                key: key.clone(),
                sha256,
            },
        );
        self.loaded_vectors.insert(key, response);
        Ok(())
    }

    fn recover_call(
        &mut self,
        requests: &[SimilarNotesRequest],
        representation_version: &str,
    ) -> Result<Option<PersistedOracleCall>> {
        let path = oracle_call_cache_path(
            &self.cache_dir,
            self.call_cursor,
            representation_version,
            requests,
        )?;
        if !path.exists() {
            return Ok(None);
        }
        let envelope: PersistedOracleCallEnvelope = read_manifest(&path)?;
        let call = envelope.call;
        if call.representation_version != representation_version || call.requests != requests {
            return Err(Error::ExperimentState(format!(
                "orphaned Oracle call `{}` is bound to a different logical request",
                path.display()
            )));
        }
        if envelope.responses.len() != requests.len() {
            return Err(Error::ExperimentState(format!(
                "orphaned Oracle call `{}` has the wrong response count",
                path.display()
            )));
        }
        for (request, response) in requests.iter().copied().zip(envelope.responses) {
            let key = response_key(representation_version, request);
            if self.recover_cached(&key)? {
                if self.load_cached(&key)? != response {
                    return Err(Error::ExperimentState(format!(
                        "orphaned Oracle call `{}` disagrees with response {}",
                        path.display(),
                        hex_event_id(request.note_id)
                    )));
                }
            } else {
                self.store_response(key, response)?;
            }
        }
        Ok(Some(call))
    }

    fn store_call(
        &self,
        call: &PersistedOracleCall,
        responses: &[SimilarNotesResponse],
    ) -> Result<()> {
        let path = oracle_call_cache_path(
            &self.cache_dir,
            self.call_cursor,
            &call.representation_version,
            &call.requests,
        )?;
        let envelope = PersistedOracleCallEnvelope {
            call: call.clone(),
            responses: responses.to_vec(),
        };
        let bytes = serde_json::to_vec(&envelope).map_err(|source| Error::Manifest {
            operation: "encode",
            path: path.clone(),
            source,
        })?;
        if path.exists() {
            let existing = fs::read(&path).map_err(|source| io_error("read", &path, source))?;
            if existing != bytes {
                return Err(Error::Invariant(
                    "durable Oracle call path contains different bytes".to_owned(),
                ));
            }
        } else {
            save_bytes_atomic(&path, &bytes)?;
        }
        Ok(())
    }
}

impl SessionOracle<'static, dyn CandidateOrderOracle> {
    fn new_read_only(
        representation_version: String,
        cache_dir: PathBuf,
        calls: Vec<PersistedOracleCall>,
        response_refs: Vec<CachedResponseRef>,
        vector_response_refs: Vec<CachedVectorResponseRef>,
    ) -> Result<Self> {
        Self::from_parts(
            None,
            representation_version,
            cache_dir,
            calls,
            response_refs,
            vector_response_refs,
        )
    }
}

impl<O: CandidateOrderOracle + ?Sized> CandidateOrderOracle for SessionOracle<'_, O> {
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
                "session Oracle representation mismatch".to_owned(),
            ));
        }
        if let Some(call) = self.calls.get(self.call_cursor).cloned() {
            if call.representation_version != representation_version || call.requests != requests {
                return Err(Error::ExperimentState(
                    "coordinator replay diverged from the durable Oracle call tape".to_owned(),
                ));
            }
            let responses = requests
                .iter()
                .map(|request| self.load_cached(&response_key(representation_version, *request)))
                .collect::<Result<Vec<_>>>()?;
            self.call_cursor += 1;
            return Ok(SimilarNotesWaveResponse {
                responses,
                metrics: call.metrics,
            });
        }

        if self.inner.is_none() {
            return Err(Error::ExperimentState(
                "read-only Phase 3 replay is missing a persisted Oracle call".to_owned(),
            ));
        }
        if let Some(call) = self.recover_call(requests, representation_version)? {
            let responses = requests
                .iter()
                .map(|request| self.load_cached(&response_key(representation_version, *request)))
                .collect::<Result<Vec<_>>>()?;
            self.calls.push(call.clone());
            self.call_cursor += 1;
            return Ok(SimilarNotesWaveResponse {
                responses,
                metrics: call.metrics,
            });
        }

        let mut missing_requests = Vec::new();
        let mut missing_keys = BTreeSet::new();
        for request in requests {
            let key = response_key(representation_version, *request);
            if !self.recover_cached(&key)? && missing_keys.insert(key) {
                missing_requests.push(*request);
            }
        }
        let (mut metrics, missing_responses) = if missing_requests.is_empty() {
            (
                SimilarNotesWaveMetrics {
                    source_loading_ns: 0,
                    query_encoding_ns: 0,
                    matrix_scan_ns: 0,
                    result_merge_ns: 0,
                    encoded_queries: 0,
                    cache_hits: requests.len() as u64,
                    matrix_passes: 0,
                    scanned_rows: 0,
                    scan_block_rows: FP32_SCAN_BLOCK_ROWS as u64,
                },
                BTreeMap::new(),
            )
        } else {
            let delegated = self
                .inner
                .as_deref_mut()
                .ok_or_else(|| {
                    Error::Invariant(
                        "writable Phase 3 Oracle has no backing implementation".to_owned(),
                    )
                })?
                .similar_notes_wave(&missing_requests, representation_version)?;
            if delegated.responses.len() != missing_requests.len() {
                return Err(Error::InvalidOracleResponse(
                    "Oracle response count does not match the missing request count".to_owned(),
                ));
            }
            let mut delegated_metrics = delegated.metrics;
            let mut missing_responses = BTreeMap::new();
            for (request, response) in missing_requests.iter().copied().zip(delegated.responses) {
                let key = response_key(representation_version, request);
                validate_cached_response(&key, &response)?;
                missing_responses.insert(key, response);
            }
            delegated_metrics.cache_hits = delegated_metrics
                .cache_hits
                .saturating_add((requests.len() - missing_requests.len()) as u64);
            (delegated_metrics, missing_responses)
        };
        if metrics.scan_block_rows == 0 {
            metrics.scan_block_rows = FP32_SCAN_BLOCK_ROWS as u64;
        }
        let responses = requests
            .iter()
            .map(|request| {
                let key = response_key(representation_version, *request);
                match missing_responses.get(&key) {
                    Some(response) => Ok(response.clone()),
                    None => self.load_cached(&key),
                }
            })
            .collect::<Result<Vec<_>>>()?;
        let call = PersistedOracleCall {
            representation_version: representation_version.to_owned(),
            requests: requests.to_vec(),
            metrics: metrics.clone(),
        };
        self.store_call(&call, &responses)?;
        for (key, response) in missing_responses {
            self.store_response(key, response)?;
        }
        self.calls.push(call);
        self.call_cursor += 1;
        Ok(SimilarNotesWaveResponse { responses, metrics })
    }

    fn vectors_for_notes(
        &mut self,
        note_ids: &[EventId],
        representation_version: &str,
    ) -> Result<VectorsForNotesResponse> {
        if representation_version != self.representation_version {
            return Err(Error::InvalidQuery(
                "session Oracle representation mismatch".to_owned(),
            ));
        }
        let key = VectorResponseCacheKey {
            representation_version: representation_version.to_owned(),
            note_ids: note_ids.to_vec(),
        };
        if self.vector_response_refs.contains_key(&key) {
            return self.load_cached_vectors(&key);
        }
        if self.inner.is_none() {
            return Err(Error::ExperimentState(
                "read-only Phase 3 replay is missing a manifested vector response".to_owned(),
            ));
        }
        if self.recover_cached_vectors(&key)? {
            return self.load_cached_vectors(&key);
        }
        let response = self
            .inner
            .as_deref_mut()
            .ok_or_else(|| {
                Error::Invariant("writable Phase 3 Oracle has no backing implementation".to_owned())
            })?
            .vectors_for_notes(note_ids, representation_version)?;
        self.store_vector_response(key, response.clone())?;
        Ok(response)
    }
}

fn response_key(representation_version: &str, request: SimilarNotesRequest) -> ResponseCacheKey {
    ResponseCacheKey {
        representation_version: representation_version.to_owned(),
        source_event_id: request.note_id,
        candidate_depth: request.candidate_depth,
    }
}

fn response_cache_path(cache_dir: &Path, key: &ResponseCacheKey) -> Result<PathBuf> {
    let bytes = serde_json::to_vec(key).map_err(|source| Error::Manifest {
        operation: "encode",
        path: cache_dir.to_owned(),
        source,
    })?;
    Ok(cache_dir.join(format!("{}.json", hash_bytes(&bytes))))
}

fn vector_response_cache_path(cache_dir: &Path, key: &VectorResponseCacheKey) -> Result<PathBuf> {
    let bytes = serde_json::to_vec(key).map_err(|source| Error::Manifest {
        operation: "encode",
        path: cache_dir.to_owned(),
        source,
    })?;
    Ok(cache_dir.join(format!("vectors-{}.json", hash_bytes(&bytes))))
}

fn oracle_call_cache_path(
    cache_dir: &Path,
    ordinal: usize,
    representation_version: &str,
    requests: &[SimilarNotesRequest],
) -> Result<PathBuf> {
    let bytes =
        serde_json::to_vec(&(ordinal, representation_version, requests)).map_err(|source| {
            Error::Manifest {
                operation: "encode",
                path: cache_dir.to_owned(),
                source,
            }
        })?;
    Ok(cache_dir.join(format!("call-{}.json", hash_bytes(&bytes))))
}

fn validate_cached_response(key: &ResponseCacheKey, response: &SimilarNotesResponse) -> Result<()> {
    let expected_candidate_count = usize::try_from(response.total_rows.saturating_sub(1))
        .unwrap_or(usize::MAX)
        .min(key.candidate_depth);
    if response.representation_version != key.representation_version
        || !response.complete
        || response.represented_rows == 0
        || response.represented_rows != response.total_rows
        || response.candidates.len() != expected_candidate_count
    {
        return Err(Error::InvalidOracleResponse(format!(
            "cached response for {} violates its immutable key",
            hex_event_id(key.source_event_id)
        )));
    }
    Ok(())
}

fn validate_cached_vector_response(
    key: &VectorResponseCacheKey,
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
            "cached vector response violates its immutable key".to_owned(),
        ));
    }
    Ok(())
}

fn sync_oracle_state<O: CandidateOrderOracle + ?Sized>(
    session: &mut AdaptiveLearningSession,
    oracle: &SessionOracle<'_, O>,
) {
    session.oracle_calls = oracle.calls.clone();
    session.oracle_responses = oracle.response_refs();
    session.vector_responses = oracle.vector_response_refs();
}

fn oracle_cache_dir(session_path: &Path) -> Result<PathBuf> {
    let name = session_path
        .file_name()
        .and_then(|name| name.to_str())
        .ok_or_else(|| Error::NonUtf8Path(session_path.to_owned()))?;
    Ok(session_path
        .parent()
        .unwrap_or_else(|| Path::new("."))
        .join(format!(".{name}.oracle-responses")))
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
            "Phase 3 session `{}` is already active",
            session_path.display()
        ))),
        Err(fs::TryLockError::Error(source)) => Err(io_error("lock", &path, source)),
    }
}

fn save_session(path: &Path, session: &AdaptiveLearningSession) -> Result<()> {
    let bytes = serde_json::to_vec_pretty(session).map_err(|source| Error::Manifest {
        operation: "encode",
        path: path.to_owned(),
        source,
    })?;
    let mut terminated = bytes;
    terminated.push(b'\n');
    save_bytes_atomic(path, &terminated)
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

fn prepare_private_cache_directory(path: &Path) -> Result<()> {
    create_private_directories(path)?;
    let metadata =
        fs::symlink_metadata(path).map_err(|source| io_error("inspect", path, source))?;
    if !metadata.file_type().is_dir() {
        return Err(Error::ExperimentState(format!(
            "private Phase 3 cache `{}` is not a directory",
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

fn protect_existing_private_file(path: &Path) -> Result<()> {
    let metadata = match fs::symlink_metadata(path) {
        Ok(metadata) => metadata,
        Err(source) if source.kind() == std::io::ErrorKind::NotFound => return Ok(()),
        Err(source) => return Err(io_error("inspect", path, source)),
    };
    if !metadata.file_type().is_file() {
        return Err(Error::ExperimentState(format!(
            "private Phase 3 artifact `{}` is not a regular file",
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
            "private Phase 3 temporary `{}` is not a regular file",
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
