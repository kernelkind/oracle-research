//! Resumable terminal execution of the frozen Phase 3 learning protocol.

use std::collections::{BTreeMap, BTreeSet};
use std::fs::{self, File, OpenOptions};
use std::io::{BufRead, BufWriter, Write};
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
    B16Boundary, CANDIDATE_DEPTH, CandidateOrderOracle, CandidateOrderPhase,
};
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
use crate::snapshot::{
    Error, Result, Validation, io_error, ndb_error, open_existing_ndb, read_manifest,
};

const SESSION_SCHEMA_VERSION: u32 = 2;
const ORACLE_RESPONSE_CONTRACT: &str = "candidate-order-oracle-v1";
const SHUFFLE_POLICY: &str = "phase3-learning-sha256-concealed-v1";
const SCORER_POLICY: &str = "compact-rbf-forward-only-h64-h256-fallback-v2";
const RATING_INSTRUCTIONS: &str = "1: Actively wish it had not been shown.\n2: Clearly not worth seeing.\n3: Little personal value.\n4: Indifferent.\n5: Mildly glad to have seen it.\n6: Clearly glad; personally valuable.\n7: Exceptionally valuable.\nUse wrong_language only when the note is clearly primarily non-English. Mixed-language, code-heavy, and ambiguous notes remain eligible and must be rated.\n";
const RATING_PROMPT: &str = "Considering the attention it required, how glad are you that you saw this note? [1–7, `l` = wrong_language; append `q` to save and stop]: ";

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
    /// Input ended or the evaluator chose to stop; all accepted input is durable.
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
    scorer_policy: String,
    rating_prompt: String,
    rating_instructions: String,
    shuffle_policy: String,
    candidate_depth: usize,
    learning_rounds: usize,
    learning_primary: usize,
    learning_reserve: usize,
    maximum_wrong_language_presentations: usize,
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

#[derive(Clone, Debug, Deserialize, Serialize)]
struct AdaptiveLearningSession {
    schema_version: u32,
    binding: SessionBinding,
    phase: SessionPhase,
    rounds: Vec<RoundTranscript>,
    oracle_calls: Vec<PersistedOracleCall>,
    oracle_responses: Vec<CachedResponseRef>,
    vector_responses: Vec<CachedVectorResponseRef>,
    completion: Option<CompletedHandoff>,
    pause_reason: Option<String>,
    failure: Option<String>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
struct RoundTranscript {
    round: usize,
    waves: Vec<WaveTranscript>,
    ratings_submitted: bool,
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
    compact_rounds: usize,
    rbf_rounds: usize,
    presentation_ledger: Vec<PersistedLedgerEntry>,
    ratings: Vec<PersistedRating>,
    eligible_presentations: usize,
    wrong_language_presentations: usize,
    source_waves: Vec<PersistedSourceWave>,
    ordered_rounds: Vec<PersistedRoundSeal>,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
struct PersistedLedgerEntry {
    event_id: EventId,
    state: String,
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
    compact_candidate_pool_sha256: String,
    compact_accepted_event_ids: Vec<EventId>,
    compact_evidence_after: SeedEvidenceBinding,
    rbf_candidate_pool_sha256: String,
    rbf_accepted_event_ids: Vec<EventId>,
    rbf_evidence_after: SeedEvidenceBinding,
    ratings: Vec<PersistedRating>,
    presentation_ledger: Vec<PersistedLedgerEntry>,
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

struct SessionOracle<'a, O> {
    inner: &'a mut O,
    representation_version: String,
    cache_dir: PathBuf,
    calls: Vec<PersistedOracleCall>,
    call_cursor: usize,
    response_refs: BTreeMap<ResponseCacheKey, CachedResponseRef>,
    loaded: BTreeMap<ResponseCacheKey, SimilarNotesResponse>,
    vector_response_refs: BTreeMap<VectorResponseCacheKey, CachedVectorResponseRef>,
    loaded_vectors: BTreeMap<VectorResponseCacheKey, VectorsForNotesResponse>,
}

/// Run a new session or resume its first incomplete evaluator input.
pub fn run_adaptive_learning<O, R, W>(
    config: &AdaptiveLearningRunnerConfig,
    oracle: &mut O,
    mut input: R,
    output: &mut W,
) -> Result<AdaptiveLearningRunnerOutcome>
where
    O: CandidateOrderOracle,
    R: BufRead,
    W: Write,
{
    let _session_lock = acquire_session_lock(&config.session_path)?;
    let fixed_binding = validate_config(config, oracle)?;
    let loaded = if config.session_path.exists() {
        let session: AdaptiveLearningSession = read_manifest(&config.session_path)?;
        validate_loaded_static_session(&session, &fixed_binding)?;
        Some(session)
    } else {
        None
    };

    if let Some(session) = &loaded
        && session.phase == SessionPhase::Failed
    {
        let reason = session
            .failure
            .as_deref()
            .unwrap_or("the learning session previously failed");
        write_output(output, &format!("Phase 3 learning is stopped: {reason}\n"))?;
        return Err(Error::ExperimentState(reason.to_owned()));
    }

    let mut corpus = None;
    let cache_dir = oracle_cache_dir(&config.session_path)?;
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
                completion: None,
                pause_reason: None,
                failure: None,
            };
            sync_oracle_state(&mut session, &session_oracle);
            save_session(&config.session_path, &session)?;
            session
        }
    };
    let mut coordinator =
        AdaptiveLearningCoordinator::new(&session_oracle, compact, rbf, config.b16.clone())
            .map_err(adaptive_error)?;
    replay_session(&mut coordinator, &session, &mut session_oracle)?;
    if session_oracle.call_cursor != session_oracle.calls.len() {
        return Err(Error::ExperimentState(
            "the stored Oracle call tape extends beyond the replayed learning state".to_owned(),
        ));
    }

    if coordinator.progress() != AdaptiveLearningProgress::Complete {
        write_output(output, RATING_INSTRUCTIONS)?;
    }

    loop {
        match coordinator.progress() {
            AdaptiveLearningProgress::Ready => {
                let round = coordinator.next_round().ok_or_else(|| {
                    Error::Invariant("ready learning coordinator has no next round".to_owned())
                })?;
                let completed_before = coordinator.round_records().len();
                if let Err(error) = coordinator.start_next_round(&mut session_oracle) {
                    return record_coordinator_failure(
                        config,
                        &mut session,
                        &session_oracle,
                        output,
                        error,
                    );
                }
                sync_oracle_state(&mut session, &session_oracle);
                if coordinator.round_records().len() == completed_before + 1 {
                    session.rounds.push(RoundTranscript {
                        round,
                        waves: Vec::new(),
                        ratings_submitted: true,
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
                });
                save_session(&config.session_path, &session)?;
            }
            AdaptiveLearningProgress::AwaitingLanguage => {
                if corpus.is_none() {
                    corpus = Some(open_existing_ndb(
                        &config.corpus_path,
                        Validation::TrustedSource,
                    )?);
                }
                let round_index = session.rounds.len().checked_sub(1).ok_or_else(|| {
                    Error::Invariant("pending language state has no session round".to_owned())
                })?;
                let needs_derived_wave = session.rounds[round_index]
                    .waves
                    .last()
                    .is_some_and(|wave| wave.submitted);
                if needs_derived_wave {
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
                    corpus.as_ref().expect("display corpus was opened"),
                    &mut session,
                    &session_oracle,
                    &mut input,
                    output,
                )? {
                    return Ok(AdaptiveLearningRunnerOutcome::Paused);
                }
                let wave_index = session.rounds[round_index].waves.len() - 1;
                let outcomes = language_outcomes(&session.rounds[round_index].waves[wave_index])?;
                let wave_id = session.rounds[round_index].waves[wave_index].wave_id;
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
                            output,
                            error,
                        );
                    }
                }
                match coordinator.progress() {
                    AdaptiveLearningProgress::AwaitingLanguage => {
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
                let ratings = ratings_for_pending_round(&coordinator, &session)?;
                if let Err(error) = coordinator.submit_ratings(ratings) {
                    return record_coordinator_failure(
                        config,
                        &mut session,
                        &session_oracle,
                        output,
                        error,
                    );
                }
                let round = session.rounds.last_mut().ok_or_else(|| {
                    Error::Invariant("ratings are pending without a session round".to_owned())
                })?;
                round.ratings_submitted = true;
                save_session(&config.session_path, &session)?;
            }
            AdaptiveLearningProgress::Complete => {
                let completed = coordinator.into_completed().map_err(|_| {
                    Error::Invariant("complete coordinator rejected its handoff".to_owned())
                })?;
                let handoff = completed_handoff(&session.binding, &completed);
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
                write_summary(output, &completed, &config.session_path)?;
                return Ok(AdaptiveLearningRunnerOutcome::Complete(Box::new(completed)));
            }
            AdaptiveLearningProgress::Paused => {
                let reason = coordinator
                    .pause_reason()
                    .map(|reason| format!("{reason:?}"))
                    .unwrap_or_else(|| "unknown coordinator pause".to_owned());
                session.phase = SessionPhase::Failed;
                session.pause_reason = None;
                session.failure = Some(reason.clone());
                sync_oracle_state(&mut session, &session_oracle);
                save_session(&config.session_path, &session)?;
                write_output(output, &format!("Phase 3 learning stopped: {reason}\n"))?;
                return Err(Error::ExperimentState(reason));
            }
        }
    }
}

fn validate_config<O: CandidateOrderOracle>(
    config: &AdaptiveLearningRunnerConfig,
    oracle: &O,
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
    let version = config.compact_settings.representation_version();
    if config.rbf_settings.representation_version() != version
        || config.b16.representation_version() != version
        || oracle.representation_version() != version
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
        scorer_policy: SCORER_POLICY.to_owned(),
        rating_prompt: RATING_PROMPT.to_owned(),
        rating_instructions: RATING_INSTRUCTIONS.to_owned(),
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
    Ok(SessionBinding {
        fixed,
        seed_evidence,
        identity_sha256,
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

fn evidence_binding(identity: &EvidenceIdentity) -> SeedEvidenceBinding {
    SeedEvidenceBinding {
        event_count: identity.event_count(),
        vector_dimensions: identity.vector_dimensions(),
        sha256: identity.sha256().to_owned(),
    }
}

fn replay_session<O: CandidateOrderOracle>(
    coordinator: &mut AdaptiveLearningCoordinator,
    session: &AdaptiveLearningSession,
    oracle: &mut SessionOracle<'_, O>,
) -> Result<()> {
    for (round_index, transcript) in session.rounds.iter().enumerate() {
        if transcript.round != round_index + 1 || coordinator.next_round() != Some(transcript.round)
        {
            return Err(Error::ExperimentState(
                "the stored learning rounds are not a contiguous coordinator transcript".to_owned(),
            ));
        }
        let completed_before = coordinator.round_records().len();
        coordinator
            .start_next_round(oracle)
            .map_err(adaptive_error)?;
        if transcript.waves.is_empty() {
            if !transcript.ratings_submitted
                || coordinator.round_records().len() != completed_before + 1
            {
                return Err(Error::ExperimentState(
                    "a no-input learning round does not match coordinator replay".to_owned(),
                ));
            }
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
                return Ok(());
            }
            if wave.decisions.len() != wave.presentation_order.len() {
                return Err(Error::ExperimentState(
                    "a submitted language wave is missing staged decisions".to_owned(),
                ));
            }
            coordinator
                .submit_language_outcomes(wave.wave_id, language_outcomes(wave)?)
                .map_err(adaptive_error)?;
        }

        if transcript.ratings_submitted {
            if coordinator.progress() == AdaptiveLearningProgress::AwaitingRatings {
                let ratings = ratings_for_round(coordinator, transcript)?;
                coordinator
                    .submit_ratings(ratings)
                    .map_err(adaptive_error)?;
            }
            if coordinator.round_records().len() != completed_before + 1 {
                return Err(Error::ExperimentState(
                    "a completed stored round did not complete during coordinator replay"
                        .to_owned(),
                ));
            }
        } else {
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
            return Ok(());
        }
    }

    match session.phase {
        SessionPhase::Complete if coordinator.progress() != AdaptiveLearningProgress::Complete => {
            Err(Error::ExperimentState(
                "the stored complete session does not reconstruct a complete coordinator"
                    .to_owned(),
            ))
        }
        SessionPhase::Learning if coordinator.progress() == AdaptiveLearningProgress::Complete => {
            Ok(())
        }
        _ => Ok(()),
    }
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
    hasher.update(binding.identity_sha256.as_bytes());
    hasher.update([0]);
    hasher.update(round.to_le_bytes());
    hasher.update(wave_id.to_le_bytes());
    hasher.update(event_id);
    hasher.finalize().into()
}

fn collect_current_wave<O, R, W>(
    config: &AdaptiveLearningRunnerConfig,
    corpus: &Ndb,
    session: &mut AdaptiveLearningSession,
    oracle: &SessionOracle<'_, O>,
    input: &mut R,
    output: &mut W,
) -> Result<bool>
where
    O: CandidateOrderOracle,
    R: BufRead,
    W: Write,
{
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
        if let Err(error) = display_raw_note(output, corpus, &config.corpus_path, event_id) {
            let reason = format!(
                "failed while displaying learning event {}: {error}",
                hex_event_id(event_id)
            );
            session.phase = SessionPhase::Failed;
            session.pause_reason = None;
            session.failure = Some(reason.clone());
            sync_oracle_state(session, oracle);
            save_session(&config.session_path, session)?;
            let _ = write_output(output, &format!("Phase 3 learning stopped: {reason}\n"));
            return Err(error);
        }
        let (decision, stop_after) = loop {
            let Some(line) = prompt_line(output, input, RATING_PROMPT)? else {
                record_evaluator_pause(config, session, oracle, output, "terminal input closed")?;
                return Ok(false);
            };
            let value = line.trim();
            if value == "q" {
                write_output(
                    output,
                    "Rate the displayed note, then append `q` to stop (for example, `6q` or `lq`).\n",
                )?;
                continue;
            }
            let (decision_value, stop_after) = value
                .strip_suffix('q')
                .map_or((value, false), |decision| (decision, true));
            if decision_value == "l" {
                break (StagedDecision::WrongLanguage { event_id }, stop_after);
            }
            if let Ok(rating) = decision_value.parse::<u8>()
                && (1..=7).contains(&rating)
            {
                break (StagedDecision::Rated { event_id, rating }, stop_after);
            }
            write_output(
                output,
                "Enter 1 to 7 or `l`; append `q` to save that decision and stop.\n",
            )?;
        };
        session.rounds[round_index].waves[wave_index]
            .decisions
            .push(decision);
        session.pause_reason =
            stop_after.then(|| "evaluator chose to stop after the accepted decision".to_owned());
        sync_oracle_state(session, oracle);
        save_session(&config.session_path, session)?;
        if stop_after {
            write_output(
                output,
                "Phase 3 learning paused: evaluator chose to stop after the accepted decision.\n",
            )?;
            return Ok(false);
        }
    }
}

fn record_evaluator_pause<O, W>(
    config: &AdaptiveLearningRunnerConfig,
    session: &mut AdaptiveLearningSession,
    oracle: &SessionOracle<'_, O>,
    output: &mut W,
    reason: &str,
) -> Result<()>
where
    O: CandidateOrderOracle,
    W: Write,
{
    session.pause_reason = Some(reason.to_owned());
    sync_oracle_state(session, oracle);
    save_session(&config.session_path, session)?;
    write_output(output, &format!("Phase 3 learning paused: {reason}.\n"))
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

fn display_raw_note<W: Write>(
    output: &mut W,
    corpus: &Ndb,
    corpus_path: &Path,
    event_id: EventId,
) -> Result<()> {
    let transaction = Transaction::new(corpus)
        .map_err(|source| ndb_error("open transaction on", corpus_path, source))?;
    let note = corpus
        .get_note_by_id(&transaction, &event_id)
        .map_err(|source| ndb_error("load event from", corpus_path, source))?;
    write_output(output, "\n")?;
    write_output(output, &terminal_safe(note.content()))?;
    write_output(output, "\n")
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
) -> CompletedHandoff {
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
    CompletedHandoff {
        binding_identity_sha256: binding.identity_sha256.clone(),
        compact_evidence: evidence_binding(completed.compact_controller().evidence_identity()),
        rbf_evidence: evidence_binding(completed.rbf_controller().evidence_identity()),
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
        ordered_rounds: completed
            .round_records()
            .iter()
            .map(|record| PersistedRoundSeal {
                round: record.round(),
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
            })
            .collect(),
    }
}

fn persisted_ledger_entry(event_id: EventId, state: &PriorPresentation) -> PersistedLedgerEntry {
    PersistedLedgerEntry {
        event_id,
        state: match state {
            PriorPresentation::Rated { selected_by } => format!("rated:{selected_by:?}"),
            PriorPresentation::EligibleUnrated => "eligible_unrated".to_owned(),
            PriorPresentation::WrongLanguage => "wrong_language".to_owned(),
        },
    }
}

fn write_summary<W: Write>(
    output: &mut W,
    completed: &CompletedAdaptiveLearning,
    session_path: &Path,
) -> Result<()> {
    write_output(
        output,
        &format!(
            "\nPhase 3 learning complete: {} rounds, {} rated notes, {} wrong-language presentations.\nSession: {}\n",
            completed.round_records().len(),
            completed.ratings().len(),
            completed.language_totals().wrong_language_presentations(),
            session_path.display()
        ),
    )
}

fn record_coordinator_failure<O, W>(
    config: &AdaptiveLearningRunnerConfig,
    session: &mut AdaptiveLearningSession,
    oracle: &SessionOracle<'_, O>,
    output: &mut W,
    error: AdaptiveLearningError,
) -> Result<AdaptiveLearningRunnerOutcome>
where
    O: CandidateOrderOracle,
    W: Write,
{
    let reason = error.to_string();
    session.phase = SessionPhase::Failed;
    session.pause_reason = None;
    session.failure = Some(reason.clone());
    sync_oracle_state(session, oracle);
    save_session(&config.session_path, session)?;
    write_output(output, &format!("Phase 3 learning stopped: {reason}\n"))?;
    Err(Error::ExperimentState(reason))
}

fn adaptive_error(error: AdaptiveLearningError) -> Error {
    Error::ExperimentState(error.to_string())
}

impl<'a, O: CandidateOrderOracle> SessionOracle<'a, O> {
    fn new(
        inner: &'a mut O,
        cache_dir: PathBuf,
        calls: Vec<PersistedOracleCall>,
        response_refs: Vec<CachedResponseRef>,
        vector_response_refs: Vec<CachedVectorResponseRef>,
    ) -> Result<Self> {
        let representation_version = inner.representation_version().to_owned();
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

impl<O: CandidateOrderOracle> CandidateOrderOracle for SessionOracle<'_, O> {
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
        if self.recover_cached_vectors(&key)? {
            return self.load_cached_vectors(&key);
        }
        let response = self
            .inner
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

fn sync_oracle_state<O: CandidateOrderOracle>(
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
    fs::create_dir_all(parent).map_err(|source| io_error("create", parent, source))?;
    let path = parent.join(format!(".{name}.lock"));
    let file = OpenOptions::new()
        .create(true)
        .read(true)
        .write(true)
        .truncate(false)
        .open(&path)
        .map_err(|source| io_error("open", &path, source))?;
    match file.try_lock() {
        Ok(()) => Ok(file),
        Err(fs::TryLockError::WouldBlock) => Err(Error::ExperimentState(format!(
            "Phase 3 session `{}` is already active",
            session_path.display()
        ))),
        Err(fs::TryLockError::Error(source)) => Err(io_error("lock", &path, source)),
    }
}

fn prompt_line<R: BufRead, W: Write>(
    output: &mut W,
    input: &mut R,
    prompt: &str,
) -> Result<Option<String>> {
    write_output(output, prompt)?;
    output
        .flush()
        .map_err(|source| io_error("flush", "<terminal-output>", source))?;
    let mut line = String::new();
    let bytes = input
        .read_line(&mut line)
        .map_err(|source| io_error("read", "<terminal-input>", source))?;
    if bytes == 0 {
        return Ok(None);
    }
    while line.ends_with(['\n', '\r']) {
        line.pop();
    }
    Ok(Some(line))
}

fn write_output(output: &mut impl Write, value: &str) -> Result<()> {
    output
        .write_all(value.as_bytes())
        .map_err(|source| io_error("write", "<terminal-output>", source))
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
        fs::create_dir_all(parent).map_err(|source| io_error("create", parent, source))?;
    }
    let name = path
        .file_name()
        .and_then(|name| name.to_str())
        .ok_or_else(|| Error::NonUtf8Path(path.to_owned()))?;
    let temporary = path.with_file_name(format!(".{name}.tmp"));
    let file = OpenOptions::new()
        .create(true)
        .truncate(true)
        .write(true)
        .open(&temporary)
        .map_err(|source| io_error("create", &temporary, source))?;
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

fn hex_event_id(event_id: EventId) -> String {
    let mut encoded = String::with_capacity(64);
    for byte in event_id {
        use std::fmt::Write as _;
        write!(&mut encoded, "{byte:02x}").expect("writing to String cannot fail");
    }
    encoded
}
