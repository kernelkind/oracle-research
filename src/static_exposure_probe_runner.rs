//! Durable runner for the bounded static-pool exposure-aware live probe.

use std::collections::{BTreeMap, BTreeSet};
use std::fs::{self, File, OpenOptions};
use std::io::{BufWriter, Write};
use std::path::{Path, PathBuf};

use nostrdb::{Ndb, Transaction};
use serde::{Deserialize, Serialize};

use crate::adjacent_novelty::{
    CREC_102_EXPOSURE_HALF_LIFE, CREC_102_TYPICAL_PAIR_COSINE, ExposureCandidate,
    ExposureSelection, STATIC_EXPOSURE_TRANCHE_SIZE, StaticExposureSelector,
};
use crate::artifact::hash_bytes;
use crate::candidate_order::CandidateDisposition;
use crate::evaluator::{
    CompletionView, EvaluatorDecision, EvaluatorSubmission, EvaluatorUi, RATING_ANCHORS,
    RATING_QUESTION, REPETITION_QUESTION, RatingOutcome, RatingView, RecoveryOutcome, RecoveryView,
    RepetitionAnswer, RepetitionOutcome, RepetitionUi, RepetitionView, RestOutcome, RestView,
    WRONG_LANGUAGE_RULE,
};
use crate::final_evaluation_runner::FrozenFinalEvaluationReplay;
use crate::representation::EventId;
use crate::snapshot::{
    Error, Result, Validation, io_error, ndb_error, open_existing_ndb, require_directory,
};

const SESSION_SCHEMA_VERSION: u32 = 1;
const REPORT_SCHEMA_VERSION: u32 = 1;
pub const STATIC_EXPOSURE_PROBE_PURPOSE: &str = "static-pool-exposure-aware-live-probe-v1";
const VALID_RATING_QUOTA: usize = 40;
const REST_INTERVAL: usize = 10;
const MAXIMUM_WRONG_LANGUAGE_PRESENTATIONS: usize = 2;

/// One candidate in the already-frozen descending Compact support order.
#[derive(Clone, Debug, Serialize)]
pub struct StaticExposureProbeCandidate {
    event_id: EventId,
    vector: Vec<f32>,
    frozen_support_score: f64,
}

impl StaticExposureProbeCandidate {
    pub fn new(event_id: EventId, vector: Vec<f32>, frozen_support_score: f64) -> Result<Self> {
        ExposureCandidate::new(event_id, vector.clone())
            .map_err(|error| Error::ExperimentState(error.to_string()))?;
        if !frozen_support_score.is_finite() || frozen_support_score <= 0.0 {
            return Err(Error::ExperimentState(
                "static probe candidate support score must be finite and positive".to_owned(),
            ));
        }
        Ok(Self {
            event_id,
            vector,
            frozen_support_score,
        })
    }

    pub const fn event_id(&self) -> EventId {
        self.event_id
    }

    pub fn vector(&self) -> &[f32] {
        &self.vector
    }

    pub const fn frozen_support_score(&self) -> f64 {
        self.frozen_support_score
    }
}

/// The complete immutable input to one static probe.
#[derive(Clone, Debug, Serialize)]
pub struct StaticExposureProbeInput {
    representation_version: String,
    frozen_compact_order_identity_sha256: String,
    candidates: Vec<StaticExposureProbeCandidate>,
    historical_presented_event_ids: BTreeSet<EventId>,
    #[serde(skip_serializing_if = "Option::is_none")]
    source_provenance: Option<StaticExposureProbeSourceProvenance>,
}

impl StaticExposureProbeInput {
    pub fn new(
        representation_version: impl Into<String>,
        frozen_compact_order_identity_sha256: impl Into<String>,
        candidates: Vec<StaticExposureProbeCandidate>,
        historical_presented_event_ids: BTreeSet<EventId>,
    ) -> Result<Self> {
        let representation_version = representation_version.into();
        let frozen_compact_order_identity_sha256 = frozen_compact_order_identity_sha256.into();
        if representation_version.is_empty() {
            return Err(Error::ExperimentState(
                "static probe representation version must not be empty".to_owned(),
            ));
        }
        require_sha256(
            &frozen_compact_order_identity_sha256,
            "frozen Compact order identity",
        )?;
        if candidates.is_empty() {
            return Err(Error::ExperimentState(
                "static probe candidate order must not be empty".to_owned(),
            ));
        }
        let mut event_ids = BTreeSet::new();
        let mut previous_score = f64::INFINITY;
        for candidate in &candidates {
            if !event_ids.insert(candidate.event_id) {
                return Err(Error::ExperimentState(
                    "static probe candidate order contains a duplicate event".to_owned(),
                ));
            }
            if candidate.frozen_support_score > previous_score {
                return Err(Error::ExperimentState(
                    "static probe candidates are not in descending frozen support order".to_owned(),
                ));
            }
            previous_score = candidate.frozen_support_score;
        }
        if event_ids
            .difference(&historical_presented_event_ids)
            .count()
            < VALID_RATING_QUOTA
        {
            return Err(Error::ExperimentState(
                "static probe has fewer than 40 unseen candidates".to_owned(),
            ));
        }
        Ok(Self {
            representation_version,
            frozen_compact_order_identity_sha256,
            candidates,
            historical_presented_event_ids,
            source_provenance: None,
        })
    }

    pub fn representation_version(&self) -> &str {
        &self.representation_version
    }

    pub fn frozen_compact_order_identity_sha256(&self) -> &str {
        &self.frozen_compact_order_identity_sha256
    }

    pub fn candidates(&self) -> &[StaticExposureProbeCandidate] {
        &self.candidates
    }

    pub fn historical_presented_event_ids(&self) -> &BTreeSet<EventId> {
        &self.historical_presented_event_ids
    }

    pub fn with_source_provenance(
        mut self,
        source_provenance: StaticExposureProbeSourceProvenance,
    ) -> Self {
        self.source_provenance = Some(source_provenance);
        self
    }

    pub fn source_provenance(&self) -> Option<&StaticExposureProbeSourceProvenance> {
        self.source_provenance.as_ref()
    }
}

/// Content identities of every frozen Phase 3/4 source used to derive the
/// probe input.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct StaticExposureProbeSourceProvenance {
    phase3_runner_binding_sha256: String,
    phase3_session_sha256: String,
    phase4_session_sha256: String,
    phase4_frozen_orders_sha256: String,
    phase4_oracle_cache_identity_sha256: String,
    phase4_launch_receipt_sha256: String,
}

impl StaticExposureProbeSourceProvenance {
    pub fn new(
        phase3_runner_binding_sha256: String,
        phase3_session_sha256: String,
        phase4_session_sha256: String,
        phase4_frozen_orders_sha256: String,
        phase4_oracle_cache_identity_sha256: String,
        phase4_launch_receipt_sha256: String,
    ) -> Result<Self> {
        for (label, identity) in [
            ("Phase 3 runner binding", &phase3_runner_binding_sha256),
            ("Phase 3 session", &phase3_session_sha256),
            ("Phase 4 session", &phase4_session_sha256),
            ("Phase 4 frozen orders", &phase4_frozen_orders_sha256),
            ("Phase 4 Oracle cache", &phase4_oracle_cache_identity_sha256),
            ("Phase 4 launch receipt", &phase4_launch_receipt_sha256),
        ] {
            require_sha256(identity, label)?;
        }
        Ok(Self {
            phase3_runner_binding_sha256,
            phase3_session_sha256,
            phase4_session_sha256,
            phase4_frozen_orders_sha256,
            phase4_oracle_cache_identity_sha256,
            phase4_launch_receipt_sha256,
        })
    }
}

/// Display corpus and private output paths for one probe.
#[derive(Clone, Debug)]
pub struct StaticExposureProbeRunnerConfig {
    pub corpus_path: PathBuf,
    pub corpus_identity: String,
    pub session_path: PathBuf,
    pub report_path: PathBuf,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum StaticExposureProbeRunnerOutcome {
    Paused,
    Complete,
}

/// Read-only status of a probe transcript and its deterministic report.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum StaticExposureProbeVerification {
    Ready,
    Active {
        presentations: usize,
        valid_ratings: usize,
        pending_presentation: bool,
    },
    Complete {
        presentations: usize,
        valid_ratings: usize,
    },
}

/// Derive the probe's complete positive Compact support order from a verified
/// frozen replay.
///
/// Historical events stay in this immutable order so recorded support ranks
/// remain the original ranks. The selector receives the replay's history and
/// excludes those events before forming each top-64 tranche.
pub fn build_static_exposure_probe_input(
    replay: &FrozenFinalEvaluationReplay,
    frozen_compact_order_identity_sha256: impl Into<String>,
) -> Result<StaticExposureProbeInput> {
    struct PositiveCandidate {
        event_id: EventId,
        deployed_score: f64,
        tie_break_sha256: [u8; 32],
    }

    let order = replay.compact_order();
    let mut positive = order
        .attempt()
        .candidates()
        .iter()
        .filter_map(|candidate| {
            let (deployed_score, tie_break_sha256) = match candidate.disposition() {
                CandidateDisposition::Accepted {
                    deployed_score,
                    tie_break_sha256,
                    ..
                }
                | CandidateDisposition::NearDuplicate {
                    deployed_score,
                    tie_break_sha256,
                    ..
                }
                | CandidateDisposition::NotWalkedAfterBound {
                    deployed_score,
                    tie_break_sha256,
                    ..
                } => (*deployed_score, *tie_break_sha256),
                CandidateDisposition::Excluded { .. }
                | CandidateDisposition::NonPositive { .. } => return None,
            };
            Some(PositiveCandidate {
                event_id: candidate.event_id(),
                deployed_score,
                tie_break_sha256,
            })
        })
        .collect::<Vec<_>>();
    positive.sort_by(|left, right| {
        right
            .deployed_score
            .total_cmp(&left.deployed_score)
            .then_with(|| left.tie_break_sha256.cmp(&right.tie_break_sha256))
            .then_with(|| left.event_id.cmp(&right.event_id))
    });
    let candidates = positive
        .into_iter()
        .map(|candidate| {
            let vector = replay
                .candidate_vector(candidate.event_id)
                .ok_or_else(|| {
                    Error::ExperimentState(
                        "positive Compact candidate is missing its reconstructed vector".to_owned(),
                    )
                })?
                .to_vec();
            StaticExposureProbeCandidate::new(candidate.event_id, vector, candidate.deployed_score)
        })
        .collect::<Result<Vec<_>>>()?;
    StaticExposureProbeInput::new(
        order.attempt().representation_version(),
        frozen_compact_order_identity_sha256,
        candidates,
        replay.historical_presented_event_ids().clone(),
    )
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
struct ProbeBinding {
    purpose: String,
    corpus_identity: String,
    representation_version: String,
    frozen_compact_order_identity_sha256: String,
    input_identity_sha256: String,
    source_provenance: Option<StaticExposureProbeSourceProvenance>,
    rating_question: String,
    rating_anchors: [String; 7],
    wrong_language_rule: String,
    repetition_question: String,
    valid_rating_quota: usize,
    rest_interval: usize,
    maximum_wrong_language_presentations: usize,
    tranche_size: usize,
    typical_pair_cosine_bits: String,
    exposure_half_life: u32,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
enum ProbePhase {
    Evaluating,
    Complete,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
struct ProbeSession {
    schema_version: u32,
    binding: ProbeBinding,
    phase: ProbePhase,
    presentations: Vec<StoredPresentation>,
    pending_presentation: Option<PendingPresentation>,
    rest_checkpoints: Vec<RestCheckpoint>,
    pause_checkpoints: Vec<PauseCheckpoint>,
    completion: Option<CompletionSeal>,
    transcript_checksum_sha256: String,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
struct StoredSelection {
    event_id: EventId,
    vector_identity_sha256: String,
    support_order_index: usize,
    support_rank: usize,
    frozen_support_score: f64,
    exposure: f64,
    tranche: Vec<StoredTrancheEntry>,
}

#[derive(Clone, Copy, Debug, Deserialize, PartialEq, Serialize)]
struct StoredTrancheEntry {
    event_id: EventId,
    support_order_index: usize,
    support_rank: usize,
    exposure: f64,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
struct PendingPresentation {
    selection: StoredSelection,
    rating: Option<u8>,
    wrong_language: bool,
    repetition: Option<RepetitionAnswer>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
struct StoredPresentation {
    event_id: EventId,
    vector_identity_sha256: String,
    support_order_index: usize,
    support_rank: usize,
    frozen_support_score: f64,
    exposure: f64,
    tranche: Vec<StoredTrancheEntry>,
    rating: Option<u8>,
    wrong_language: bool,
    repetition: Option<RepetitionAnswer>,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
struct RestCheckpoint {
    after_valid_ratings: usize,
    continued: bool,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
struct PauseCheckpoint {
    after_presentations: usize,
    after_valid_ratings: usize,
    reason: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
struct CompletionSeal {
    report_sha256: String,
    presentations: usize,
    valid_ratings: usize,
}

#[derive(Serialize)]
struct ProbeTranscript<'a> {
    schema_version: u32,
    binding: &'a ProbeBinding,
    phase: ProbePhase,
    presentations: &'a [StoredPresentation],
    pending_presentation: &'a Option<PendingPresentation>,
    rest_checkpoints: &'a [RestCheckpoint],
    pause_checkpoints: &'a [PauseCheckpoint],
    completion: &'a Option<CompletionSeal>,
}

#[derive(Serialize)]
struct ProbeReport<'a> {
    schema_version: u32,
    purpose: &'static str,
    binding: &'a ProbeBinding,
    presentations: usize,
    valid_ratings: usize,
    ratings: BTreeMap<String, usize>,
    repetition_answers: BTreeMap<&'static str, usize>,
    wrong_language_presentations: usize,
    selection: SelectionReport,
    presentation_audit: &'a [StoredPresentation],
    rest_checkpoints: &'a [RestCheckpoint],
    pause_checkpoints: &'a [PauseCheckpoint],
}

#[derive(Serialize)]
struct SelectionReport {
    policy: &'static str,
    tranche_size: usize,
    typical_pair_cosine: f64,
    half_life: u32,
}

/// Verify an absent, active, or completed probe without acquiring its lock,
/// writing artifacts, or requesting evaluator input.
pub fn verify_static_exposure_probe(
    config: &StaticExposureProbeRunnerConfig,
    input: &StaticExposureProbeInput,
) -> Result<StaticExposureProbeVerification> {
    validate_config(config)?;
    if !config.session_path.exists() {
        if config.report_path.exists() {
            return Err(Error::ExperimentState(
                "a static probe report exists without its durable session".to_owned(),
            ));
        }
        return Ok(StaticExposureProbeVerification::Ready);
    }
    let binding = build_binding(config, input)?;
    let session: ProbeSession = crate::snapshot::read_manifest(&config.session_path)?;
    if session.schema_version != SESSION_SCHEMA_VERSION || session.binding != binding {
        return Err(Error::ExperimentState(
            "stored static probe session does not match its frozen inputs".to_owned(),
        ));
    }
    verify_session_checksum(&config.session_path, &session)?;
    validate_session(&session)?;
    let _selector = replay_selector(input, &session)?;
    match session.phase {
        ProbePhase::Evaluating => {
            if config.report_path.exists() && valid_rating_count(&session) < VALID_RATING_QUOTA {
                return Err(Error::ExperimentState(
                    "an incomplete static probe unexpectedly has a report".to_owned(),
                ));
            }
            Ok(StaticExposureProbeVerification::Active {
                presentations: session.presentations.len(),
                valid_ratings: valid_rating_count(&session),
                pending_presentation: session.pending_presentation.is_some(),
            })
        }
        ProbePhase::Complete => {
            verify_complete(config, &session)?;
            Ok(StaticExposureProbeVerification::Complete {
                presentations: session.presentations.len(),
                valid_ratings: valid_rating_count(&session),
            })
        }
    }
}

/// Run or exactly resume the static exposure-aware probe.
pub fn run_static_exposure_probe<U>(
    config: &StaticExposureProbeRunnerConfig,
    input: &StaticExposureProbeInput,
    evaluator: &mut U,
) -> Result<StaticExposureProbeRunnerOutcome>
where
    U: EvaluatorUi + RepetitionUi,
{
    validate_config(config)?;
    let _lock = acquire_session_lock(&config.session_path)?;
    if !config.session_path.exists() && config.report_path.exists() {
        return Err(Error::ExperimentState(
            "a static probe report exists without its durable session".to_owned(),
        ));
    }
    let binding = build_binding(config, input)?;
    let mut session = load_or_create_session(&config.session_path, binding)?;
    let mut selector = replay_selector(input, &session)?;

    if session.phase == ProbePhase::Complete {
        verify_complete(config, &session)?;
        evaluator
            .complete(CompletionView::new(session.presentations.len()))
            .map_err(|source| io_error("write", "<terminal-output>", source))?;
        return Ok(StaticExposureProbeRunnerOutcome::Complete);
    }

    let mut corpus = None;
    loop {
        if valid_rating_count(&session) == VALID_RATING_QUOTA {
            return complete_probe(config, &mut session, evaluator);
        }
        if session.pending_presentation.is_none()
            && !take_due_rest(config, &mut session, evaluator)?
        {
            return Ok(StaticExposureProbeRunnerOutcome::Paused);
        }
        if session.pending_presentation.is_none() {
            let selection = selector
                .select_next()
                .map_err(|error| Error::ExperimentState(error.to_string()))?
                .ok_or_else(|| {
                    Error::ExperimentState(
                        "static probe exhausted candidate supply before 40 valid ratings"
                            .to_owned(),
                    )
                })?;
            let content =
                load_raw_note_content(&mut corpus, &config.corpus_path, selection.event_id())?;
            session.pending_presentation = Some(PendingPresentation {
                selection: store_selection(input, &selection)?,
                rating: None,
                wrong_language: false,
                repetition: None,
            });
            save_session(&config.session_path, &mut session)?;
            let view = RatingView::new(
                &content,
                session.presentations.len() + 1,
                valid_ratings_until_rest(&session),
            );
            let outcome = match evaluator.rate(view) {
                Ok(outcome) => outcome,
                Err(error) => {
                    record_pause(
                        config,
                        &mut session,
                        format!("terminal failed while requesting a probe rating: {error}"),
                    )?;
                    return Ok(StaticExposureProbeRunnerOutcome::Paused);
                }
            };
            if !store_rating_outcome(config, &mut session, outcome)? {
                return Ok(StaticExposureProbeRunnerOutcome::Paused);
            }
        } else if pending_needs_rating(&session) {
            let recovery = match evaluator.recover(RecoveryView::new(
                session.presentations.len() + 1,
                valid_ratings_until_rest(&session),
            )) {
                Ok(outcome) => outcome,
                Err(error) => {
                    record_pause(
                        config,
                        &mut session,
                        format!("terminal failed during probe presentation recovery: {error}"),
                    )?;
                    return Ok(StaticExposureProbeRunnerOutcome::Paused);
                }
            };
            match recovery {
                RecoveryOutcome::Submitted(submission) => {
                    if !store_submission(config, &mut session, submission)? {
                        return Ok(StaticExposureProbeRunnerOutcome::Paused);
                    }
                }
                RecoveryOutcome::Redisplay => {
                    let event_id = pending_event_id(&session)?;
                    let content =
                        load_raw_note_content(&mut corpus, &config.corpus_path, event_id)?;
                    let outcome = match evaluator.rate(RatingView::new(
                        &content,
                        session.presentations.len() + 1,
                        valid_ratings_until_rest(&session),
                    )) {
                        Ok(outcome) => outcome,
                        Err(error) => {
                            record_pause(
                                config,
                                &mut session,
                                format!("terminal failed while redisplaying a probe note: {error}"),
                            )?;
                            return Ok(StaticExposureProbeRunnerOutcome::Paused);
                        }
                    };
                    if !store_rating_outcome(config, &mut session, outcome)? {
                        return Ok(StaticExposureProbeRunnerOutcome::Paused);
                    }
                }
                RecoveryOutcome::Paused => {
                    record_pause(
                        config,
                        &mut session,
                        "evaluator paused with an uncertain probe presentation".to_owned(),
                    )?;
                    return Ok(StaticExposureProbeRunnerOutcome::Paused);
                }
            }
        }

        if pending_is_wrong_language(&session) {
            commit_pending(config, &mut session, &mut selector)?;
            continue;
        }
        if pending_needs_repetition(&session) {
            let event_id = pending_event_id(&session)?;
            let content = match load_raw_note_content(&mut corpus, &config.corpus_path, event_id) {
                Ok(content) => content,
                Err(error) => {
                    record_pause(
                        config,
                        &mut session,
                        format!("display corpus unavailable for probe repetition context: {error}"),
                    )?;
                    return Ok(StaticExposureProbeRunnerOutcome::Paused);
                }
            };
            let outcome = match evaluator.repetition(RepetitionView::new(
                &content,
                session.presentations.len() + 1,
            )) {
                Ok(outcome) => outcome,
                Err(error) => {
                    record_pause(
                        config,
                        &mut session,
                        format!("terminal failed while requesting repetition feedback: {error}"),
                    )?;
                    return Ok(StaticExposureProbeRunnerOutcome::Paused);
                }
            };
            match outcome {
                RepetitionOutcome::Answered(answer) => {
                    let pending = session.pending_presentation.as_mut().ok_or_else(|| {
                        Error::Invariant("repetition answer has no pending presentation".to_owned())
                    })?;
                    pending.repetition = Some(answer);
                    save_session(&config.session_path, &mut session)?;
                }
                RepetitionOutcome::Paused => {
                    record_pause(
                        config,
                        &mut session,
                        "evaluator paused before answering the repetition question".to_owned(),
                    )?;
                    return Ok(StaticExposureProbeRunnerOutcome::Paused);
                }
            }
        }
        if pending_is_complete(&session) {
            commit_pending(config, &mut session, &mut selector)?;
        }
    }
}

fn validate_config(config: &StaticExposureProbeRunnerConfig) -> Result<()> {
    require_directory(&config.corpus_path)?;
    if config.corpus_identity.is_empty() {
        return Err(Error::ExperimentState(
            "static probe corpus identity must not be empty".to_owned(),
        ));
    }
    if config.session_path == config.report_path
        || config.session_path.starts_with(&config.corpus_path)
        || config.report_path.starts_with(&config.corpus_path)
    {
        return Err(Error::ExperimentState(
            "static probe outputs must be distinct and outside its corpus".to_owned(),
        ));
    }
    Ok(())
}

fn build_binding(
    config: &StaticExposureProbeRunnerConfig,
    input: &StaticExposureProbeInput,
) -> Result<ProbeBinding> {
    let input_bytes = serde_json::to_vec(input).map_err(|source| Error::Manifest {
        operation: "encode",
        path: config.session_path.clone(),
        source,
    })?;
    Ok(ProbeBinding {
        purpose: STATIC_EXPOSURE_PROBE_PURPOSE.to_owned(),
        corpus_identity: config.corpus_identity.clone(),
        representation_version: input.representation_version.clone(),
        frozen_compact_order_identity_sha256: input.frozen_compact_order_identity_sha256.clone(),
        input_identity_sha256: hash_bytes(&input_bytes),
        source_provenance: input.source_provenance.clone(),
        rating_question: RATING_QUESTION.to_owned(),
        rating_anchors: RATING_ANCHORS.map(str::to_owned),
        wrong_language_rule: WRONG_LANGUAGE_RULE.to_owned(),
        repetition_question: REPETITION_QUESTION.to_owned(),
        valid_rating_quota: VALID_RATING_QUOTA,
        rest_interval: REST_INTERVAL,
        maximum_wrong_language_presentations: MAXIMUM_WRONG_LANGUAGE_PRESENTATIONS,
        tranche_size: STATIC_EXPOSURE_TRANCHE_SIZE,
        typical_pair_cosine_bits: format!("{:016x}", CREC_102_TYPICAL_PAIR_COSINE.to_bits()),
        exposure_half_life: CREC_102_EXPOSURE_HALF_LIFE,
    })
}

fn load_or_create_session(path: &Path, binding: ProbeBinding) -> Result<ProbeSession> {
    if path.exists() {
        let session: ProbeSession = crate::snapshot::read_manifest(path)?;
        if session.schema_version != SESSION_SCHEMA_VERSION || session.binding != binding {
            return Err(Error::ExperimentState(
                "stored static probe session does not match its frozen inputs".to_owned(),
            ));
        }
        verify_session_checksum(path, &session)?;
        validate_session(&session)?;
        return Ok(session);
    }
    let mut session = ProbeSession {
        schema_version: SESSION_SCHEMA_VERSION,
        binding,
        phase: ProbePhase::Evaluating,
        presentations: Vec::new(),
        pending_presentation: None,
        rest_checkpoints: Vec::new(),
        pause_checkpoints: Vec::new(),
        completion: None,
        transcript_checksum_sha256: String::new(),
    };
    save_session(path, &mut session)?;
    Ok(session)
}

fn replay_selector(
    input: &StaticExposureProbeInput,
    session: &ProbeSession,
) -> Result<StaticExposureSelector> {
    let candidates = input
        .candidates
        .iter()
        .map(|candidate| ExposureCandidate::new(candidate.event_id, candidate.vector.clone()))
        .collect::<std::result::Result<Vec<_>, _>>()
        .map_err(|error| Error::ExperimentState(error.to_string()))?;
    let mut selector = StaticExposureSelector::with_presentation_quota(
        candidates,
        input.historical_presented_event_ids.clone(),
        VALID_RATING_QUOTA + MAXIMUM_WRONG_LANGUAGE_PRESENTATIONS,
    )
    .map_err(|error| Error::ExperimentState(error.to_string()))?;
    for stored in &session.presentations {
        let selected = selector
            .select_next()
            .map_err(|error| Error::ExperimentState(error.to_string()))?
            .ok_or_else(|| {
                Error::ExperimentState(
                    "stored probe presentation extends beyond deterministic selection".to_owned(),
                )
            })?;
        if store_selection(input, &selected)? != selection_from_presentation(stored) {
            return Err(Error::ExperimentState(
                "stored probe presentation differs from deterministic replay".to_owned(),
            ));
        }
        selector
            .record_presentation()
            .map_err(|error| Error::ExperimentState(error.to_string()))?;
    }
    if let Some(pending) = &session.pending_presentation {
        let selected = selector
            .select_next()
            .map_err(|error| Error::ExperimentState(error.to_string()))?
            .ok_or_else(|| {
                Error::ExperimentState(
                    "pending probe presentation extends beyond deterministic selection".to_owned(),
                )
            })?;
        if store_selection(input, &selected)? != pending.selection {
            return Err(Error::ExperimentState(
                "pending probe presentation differs from deterministic replay".to_owned(),
            ));
        }
    }
    Ok(selector)
}

fn store_selection(
    input: &StaticExposureProbeInput,
    selection: &ExposureSelection,
) -> Result<StoredSelection> {
    let candidate = input
        .candidates
        .get(selection.support_order_index())
        .ok_or_else(|| Error::Invariant("selection support index is out of range".to_owned()))?;
    if candidate.event_id != selection.event_id() {
        return Err(Error::Invariant(
            "selection event differs from its frozen support index".to_owned(),
        ));
    }
    Ok(StoredSelection {
        event_id: selection.event_id(),
        vector_identity_sha256: vector_identity(input.representation_version(), candidate.vector()),
        support_order_index: selection.support_order_index(),
        support_rank: selection.support_order_index() + 1,
        frozen_support_score: candidate.frozen_support_score,
        exposure: selection.exposure(),
        tranche: selection
            .tranche()
            .iter()
            .map(|entry| StoredTrancheEntry {
                event_id: entry.event_id(),
                support_order_index: entry.support_order_index(),
                support_rank: entry.support_order_index() + 1,
                exposure: entry.exposure(),
            })
            .collect(),
    })
}

fn selection_from_presentation(stored: &StoredPresentation) -> StoredSelection {
    StoredSelection {
        event_id: stored.event_id,
        vector_identity_sha256: stored.vector_identity_sha256.clone(),
        support_order_index: stored.support_order_index,
        support_rank: stored.support_rank,
        frozen_support_score: stored.frozen_support_score,
        exposure: stored.exposure,
        tranche: stored.tranche.clone(),
    }
}

fn store_rating_outcome(
    config: &StaticExposureProbeRunnerConfig,
    session: &mut ProbeSession,
    outcome: RatingOutcome,
) -> Result<bool> {
    match outcome {
        RatingOutcome::Submitted(submission) => store_submission(config, session, submission),
        RatingOutcome::Paused => {
            record_pause(
                config,
                session,
                "evaluator paused before rating the pending probe presentation".to_owned(),
            )?;
            Ok(false)
        }
    }
}

fn store_submission(
    config: &StaticExposureProbeRunnerConfig,
    session: &mut ProbeSession,
    submission: EvaluatorSubmission,
) -> Result<bool> {
    let pending = session.pending_presentation.as_mut().ok_or_else(|| {
        Error::Invariant("probe evaluator submission has no pending presentation".to_owned())
    })?;
    if pending.rating.is_some() || pending.wrong_language {
        return Err(Error::ExperimentState(
            "pending probe presentation already has a rating outcome".to_owned(),
        ));
    }
    match submission.decision() {
        EvaluatorDecision::Rating(rating) if (1..=7).contains(&rating) => {
            pending.rating = Some(rating);
        }
        EvaluatorDecision::Rating(_) => {
            return Err(Error::ExperimentState(
                "evaluator returned a probe rating outside 1–7".to_owned(),
            ));
        }
        EvaluatorDecision::WrongLanguage => pending.wrong_language = true,
    }
    save_session(&config.session_path, session)?;
    if submission.pause_after() {
        record_pause(
            config,
            session,
            "evaluator chose to pause after the accepted probe rating".to_owned(),
        )?;
        Ok(false)
    } else {
        Ok(true)
    }
}

fn commit_pending(
    config: &StaticExposureProbeRunnerConfig,
    session: &mut ProbeSession,
    selector: &mut StaticExposureSelector,
) -> Result<()> {
    let pending = session.pending_presentation.take().ok_or_else(|| {
        Error::Invariant("probe has no pending presentation to commit".to_owned())
    })?;
    validate_pending(&pending)?;
    let stored = StoredPresentation {
        event_id: pending.selection.event_id,
        vector_identity_sha256: pending.selection.vector_identity_sha256,
        support_order_index: pending.selection.support_order_index,
        support_rank: pending.selection.support_rank,
        frozen_support_score: pending.selection.frozen_support_score,
        exposure: pending.selection.exposure,
        tranche: pending.selection.tranche,
        rating: pending.rating,
        wrong_language: pending.wrong_language,
        repetition: pending.repetition,
    };
    session.presentations.push(stored);
    save_session(&config.session_path, session)?;
    selector
        .record_presentation()
        .map_err(|error| Error::ExperimentState(error.to_string()))?;
    if wrong_language_count(session) > MAXIMUM_WRONG_LANGUAGE_PRESENTATIONS {
        return Err(Error::ExperimentState(format!(
            "static probe exceeded {MAXIMUM_WRONG_LANGUAGE_PRESENTATIONS} wrong-language presentations"
        )));
    }
    Ok(())
}

fn take_due_rest<U: EvaluatorUi>(
    config: &StaticExposureProbeRunnerConfig,
    session: &mut ProbeSession,
    evaluator: &mut U,
) -> Result<bool> {
    let valid_ratings = valid_rating_count(session);
    if valid_ratings == 0
        || valid_ratings == VALID_RATING_QUOTA
        || !valid_ratings.is_multiple_of(REST_INTERVAL)
    {
        return Ok(true);
    }
    let index = match session
        .rest_checkpoints
        .iter()
        .position(|checkpoint| checkpoint.after_valid_ratings == valid_ratings)
    {
        Some(index) => index,
        None => {
            session.rest_checkpoints.push(RestCheckpoint {
                after_valid_ratings: valid_ratings,
                continued: false,
            });
            save_session(&config.session_path, session)?;
            session.rest_checkpoints.len() - 1
        }
    };
    if session.rest_checkpoints[index].continued {
        return Ok(true);
    }
    match evaluator.rest(RestView::new(session.presentations.len())) {
        Ok(RestOutcome::Continue) => {
            session.rest_checkpoints[index].continued = true;
            save_session(&config.session_path, session)?;
            Ok(true)
        }
        Ok(RestOutcome::Paused) => {
            record_pause(
                config,
                session,
                "evaluator paused at a scheduled probe rest".to_owned(),
            )?;
            Ok(false)
        }
        Err(error) => {
            record_pause(
                config,
                session,
                format!("terminal failed at a scheduled probe rest: {error}"),
            )?;
            Ok(false)
        }
    }
}

fn complete_probe<U: EvaluatorUi>(
    config: &StaticExposureProbeRunnerConfig,
    session: &mut ProbeSession,
    evaluator: &mut U,
) -> Result<StaticExposureProbeRunnerOutcome> {
    if session.pending_presentation.is_some() || valid_rating_count(session) != VALID_RATING_QUOTA {
        return Err(Error::Invariant(
            "static probe completion was requested before exactly 40 valid ratings".to_owned(),
        ));
    }
    let report_bytes = build_report_bytes(config, session)?;
    publish_or_verify(&config.report_path, &report_bytes)?;
    session.phase = ProbePhase::Complete;
    session.completion = Some(CompletionSeal {
        report_sha256: hash_bytes(&report_bytes),
        presentations: session.presentations.len(),
        valid_ratings: VALID_RATING_QUOTA,
    });
    save_session(&config.session_path, session)?;
    evaluator
        .complete(CompletionView::new(session.presentations.len()))
        .map_err(|source| io_error("write", "<terminal-output>", source))?;
    Ok(StaticExposureProbeRunnerOutcome::Complete)
}

fn build_report_bytes(
    path_config: &StaticExposureProbeRunnerConfig,
    session: &ProbeSession,
) -> Result<Vec<u8>> {
    let mut ratings = (1..=7)
        .map(|rating| (rating.to_string(), 0_usize))
        .collect::<BTreeMap<_, _>>();
    let mut repetition_answers = BTreeMap::from([("yes", 0_usize), ("no", 0_usize)]);
    for presentation in &session.presentations {
        if let Some(rating) = presentation.rating {
            *ratings
                .get_mut(&rating.to_string())
                .expect("the complete rating histogram was initialized") += 1;
        }
        match presentation.repetition {
            Some(RepetitionAnswer::Yes) => {
                *repetition_answers
                    .get_mut("yes")
                    .expect("the repetition histogram contains yes") += 1;
            }
            Some(RepetitionAnswer::No) => {
                *repetition_answers
                    .get_mut("no")
                    .expect("the repetition histogram contains no") += 1;
            }
            None => {}
        }
    }
    let report = ProbeReport {
        schema_version: REPORT_SCHEMA_VERSION,
        purpose: STATIC_EXPOSURE_PROBE_PURPOSE,
        binding: &session.binding,
        presentations: session.presentations.len(),
        valid_ratings: valid_rating_count(session),
        ratings,
        repetition_answers,
        wrong_language_presentations: session
            .presentations
            .iter()
            .filter(|presentation| presentation.wrong_language)
            .count(),
        selection: SelectionReport {
            policy: "minimum-exposure-within-frozen-compact-top-64-v1",
            tranche_size: STATIC_EXPOSURE_TRANCHE_SIZE,
            typical_pair_cosine: CREC_102_TYPICAL_PAIR_COSINE,
            half_life: CREC_102_EXPOSURE_HALF_LIFE,
        },
        presentation_audit: &session.presentations,
        rest_checkpoints: &session.rest_checkpoints,
        pause_checkpoints: &session.pause_checkpoints,
    };
    pretty_json_bytes(&path_config.report_path, &report)
}

fn verify_complete(config: &StaticExposureProbeRunnerConfig, session: &ProbeSession) -> Result<()> {
    let completion = session.completion.as_ref().ok_or_else(|| {
        Error::ExperimentState("completed static probe has no completion seal".to_owned())
    })?;
    if session.pending_presentation.is_some()
        || completion.presentations != session.presentations.len()
        || completion.valid_ratings != valid_rating_count(session)
        || completion.valid_ratings != VALID_RATING_QUOTA
    {
        return Err(Error::ExperimentState(
            "completed static probe transcript contradicts its completion seal".to_owned(),
        ));
    }
    let expected = build_report_bytes(config, session)?;
    let actual = fs::read(&config.report_path)
        .map_err(|source| io_error("read", &config.report_path, source))?;
    if actual != expected || completion.report_sha256 != hash_bytes(&actual) {
        return Err(Error::ExperimentState(
            "completed static probe report differs from deterministic reconstruction".to_owned(),
        ));
    }
    Ok(())
}

fn validate_session(session: &ProbeSession) -> Result<()> {
    let mut seen = BTreeSet::new();
    for presentation in &session.presentations {
        if !seen.insert(presentation.event_id) {
            return Err(Error::ExperimentState(
                "static probe session repeats a presented event".to_owned(),
            ));
        }
        validate_stored_presentation(presentation)?;
    }
    if let Some(pending) = &session.pending_presentation {
        if !seen.insert(pending.selection.event_id) {
            return Err(Error::ExperimentState(
                "pending static probe event was already presented".to_owned(),
            ));
        }
        validate_pending_partial(pending)?;
    }
    if valid_rating_count(session) > VALID_RATING_QUOTA {
        return Err(Error::ExperimentState(
            "static probe session exceeds its valid-rating quota".to_owned(),
        ));
    }
    if wrong_language_count(session) > MAXIMUM_WRONG_LANGUAGE_PRESENTATIONS {
        return Err(Error::ExperimentState(format!(
            "static probe exceeds its {MAXIMUM_WRONG_LANGUAGE_PRESENTATIONS}-presentation wrong-language ceiling"
        )));
    }
    validate_rest_checkpoints(session)?;
    validate_pause_checkpoints(session)?;
    match session.phase {
        ProbePhase::Evaluating if session.completion.is_some() => Err(Error::ExperimentState(
            "evaluating static probe unexpectedly has a completion seal".to_owned(),
        )),
        ProbePhase::Complete if session.completion.is_none() => Err(Error::ExperimentState(
            "completed static probe is missing its completion seal".to_owned(),
        )),
        _ => Ok(()),
    }
}

fn validate_stored_presentation(presentation: &StoredPresentation) -> Result<()> {
    let pending = PendingPresentation {
        selection: selection_from_presentation(presentation),
        rating: presentation.rating,
        wrong_language: presentation.wrong_language,
        repetition: presentation.repetition,
    };
    validate_pending(&pending)
}

fn validate_pending_partial(pending: &PendingPresentation) -> Result<()> {
    if pending.rating.is_some() && pending.wrong_language {
        return Err(Error::ExperimentState(
            "pending probe presentation is both rated and wrong-language".to_owned(),
        ));
    }
    if pending
        .rating
        .is_some_and(|rating| !(1..=7).contains(&rating))
    {
        return Err(Error::ExperimentState(
            "pending probe rating lies outside 1–7".to_owned(),
        ));
    }
    if pending.repetition.is_some() && pending.rating.is_none() {
        return Err(Error::ExperimentState(
            "pending probe repetition answer has no numeric rating".to_owned(),
        ));
    }
    Ok(())
}

fn validate_pending(pending: &PendingPresentation) -> Result<()> {
    validate_pending_partial(pending)?;
    if pending.wrong_language {
        if pending.repetition.is_some() {
            return Err(Error::ExperimentState(
                "wrong-language probe presentation has repetition feedback".to_owned(),
            ));
        }
    } else if pending.rating.is_none() || pending.repetition.is_none() {
        return Err(Error::ExperimentState(
            "completed probe presentation lacks rating or repetition feedback".to_owned(),
        ));
    }
    Ok(())
}

fn valid_rating_count(session: &ProbeSession) -> usize {
    session
        .presentations
        .iter()
        .filter(|presentation| presentation.rating.is_some())
        .count()
}

fn wrong_language_count(session: &ProbeSession) -> usize {
    session
        .presentations
        .iter()
        .filter(|presentation| presentation.wrong_language)
        .count()
}

fn validate_rest_checkpoints(session: &ProbeSession) -> Result<()> {
    let valid_ratings = valid_rating_count(session);
    let mut previous = 0;
    for checkpoint in &session.rest_checkpoints {
        if ![10, 20, 30].contains(&checkpoint.after_valid_ratings)
            || checkpoint.after_valid_ratings <= previous
            || checkpoint.after_valid_ratings > valid_ratings
        {
            return Err(Error::ExperimentState(
                "static probe rest checkpoints are not exact increasing rating boundaries"
                    .to_owned(),
            ));
        }
        previous = checkpoint.after_valid_ratings;
    }
    for boundary in [10, 20, 30] {
        let checkpoint = session
            .rest_checkpoints
            .iter()
            .find(|checkpoint| checkpoint.after_valid_ratings == boundary);
        let must_have_continued = valid_ratings > boundary
            || (valid_ratings == boundary && session.pending_presentation.is_some())
            || session.phase == ProbePhase::Complete;
        if must_have_continued && !checkpoint.is_some_and(|checkpoint| checkpoint.continued) {
            return Err(Error::ExperimentState(format!(
                "static probe is missing its continued rest after {boundary} valid ratings"
            )));
        }
        if valid_ratings < boundary && checkpoint.is_some() {
            return Err(Error::ExperimentState(
                "static probe has a rest checkpoint beyond its valid ratings".to_owned(),
            ));
        }
    }
    Ok(())
}

fn validate_pause_checkpoints(session: &ProbeSession) -> Result<()> {
    let presentations = session.presentations.len();
    let valid_ratings = valid_rating_count(session);
    let mut previous_presentations = 0;
    let mut previous_ratings = 0;
    for checkpoint in &session.pause_checkpoints {
        if checkpoint.reason.is_empty()
            || checkpoint.after_presentations > presentations
            || checkpoint.after_valid_ratings > valid_ratings
            || checkpoint.after_presentations < previous_presentations
            || checkpoint.after_valid_ratings < previous_ratings
        {
            return Err(Error::ExperimentState(
                "static probe pause checkpoints are invalid or decreasing".to_owned(),
            ));
        }
        previous_presentations = checkpoint.after_presentations;
        previous_ratings = checkpoint.after_valid_ratings;
    }
    Ok(())
}

fn valid_ratings_until_rest(session: &ProbeSession) -> usize {
    let remainder = valid_rating_count(session) % REST_INTERVAL;
    if remainder == 0 {
        REST_INTERVAL
    } else {
        REST_INTERVAL - remainder
    }
}

fn pending_event_id(session: &ProbeSession) -> Result<EventId> {
    session
        .pending_presentation
        .as_ref()
        .map(|pending| pending.selection.event_id)
        .ok_or_else(|| Error::Invariant("probe session has no pending event".to_owned()))
}

fn pending_needs_rating(session: &ProbeSession) -> bool {
    session
        .pending_presentation
        .as_ref()
        .is_some_and(|pending| pending.rating.is_none() && !pending.wrong_language)
}

fn pending_is_wrong_language(session: &ProbeSession) -> bool {
    session
        .pending_presentation
        .as_ref()
        .is_some_and(|pending| pending.wrong_language)
}

fn pending_needs_repetition(session: &ProbeSession) -> bool {
    session
        .pending_presentation
        .as_ref()
        .is_some_and(|pending| pending.rating.is_some() && pending.repetition.is_none())
}

fn pending_is_complete(session: &ProbeSession) -> bool {
    session
        .pending_presentation
        .as_ref()
        .is_some_and(|pending| {
            pending.wrong_language || (pending.rating.is_some() && pending.repetition.is_some())
        })
}

fn record_pause(
    config: &StaticExposureProbeRunnerConfig,
    session: &mut ProbeSession,
    reason: String,
) -> Result<()> {
    session.pause_checkpoints.push(PauseCheckpoint {
        after_presentations: session.presentations.len(),
        after_valid_ratings: valid_rating_count(session),
        reason,
    });
    save_session(&config.session_path, session)
}

fn load_raw_note_content(
    corpus: &mut Option<Ndb>,
    corpus_path: &Path,
    event_id: EventId,
) -> Result<String> {
    if corpus.is_none() {
        *corpus = Some(open_existing_ndb(corpus_path, Validation::TrustedSource)?);
    }
    let corpus = corpus
        .as_ref()
        .expect("the probe display corpus was opened");
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

fn acquire_session_lock(session_path: &Path) -> Result<File> {
    let name = session_path
        .file_name()
        .and_then(|name| name.to_str())
        .ok_or_else(|| Error::NonUtf8Path(session_path.to_owned()))?;
    let parent = session_path.parent().unwrap_or_else(|| Path::new("."));
    fs::create_dir_all(parent).map_err(|source| io_error("create", parent, source))?;
    let lock_path = parent.join(format!(".{name}.lock"));
    let file = OpenOptions::new()
        .create(true)
        .read(true)
        .write(true)
        .truncate(false)
        .open(&lock_path)
        .map_err(|source| io_error("open", &lock_path, source))?;
    match file.try_lock() {
        Ok(()) => Ok(file),
        Err(fs::TryLockError::WouldBlock) => Err(Error::ExperimentState(format!(
            "static probe session `{}` is already active",
            session_path.display()
        ))),
        Err(fs::TryLockError::Error(source)) => Err(io_error("lock", &lock_path, source)),
    }
}

fn save_session(path: &Path, session: &mut ProbeSession) -> Result<()> {
    session.transcript_checksum_sha256 = session_checksum(path, session)?;
    let bytes = pretty_json_bytes(path, session)?;
    save_bytes_atomic(path, &bytes)
}

fn verify_session_checksum(path: &Path, session: &ProbeSession) -> Result<()> {
    if session.transcript_checksum_sha256 != session_checksum(path, session)? {
        return Err(Error::ExperimentState(
            "static probe transcript checksum does not match its stored decisions".to_owned(),
        ));
    }
    Ok(())
}

fn session_checksum(path: &Path, session: &ProbeSession) -> Result<String> {
    let transcript = ProbeTranscript {
        schema_version: session.schema_version,
        binding: &session.binding,
        phase: session.phase,
        presentations: &session.presentations,
        pending_presentation: &session.pending_presentation,
        rest_checkpoints: &session.rest_checkpoints,
        pause_checkpoints: &session.pause_checkpoints,
        completion: &session.completion,
    };
    let bytes = serde_json::to_vec(&transcript).map_err(|source| Error::Manifest {
        operation: "encode",
        path: path.to_owned(),
        source,
    })?;
    Ok(hash_bytes(&bytes))
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

fn publish_or_verify(path: &Path, bytes: &[u8]) -> Result<()> {
    if path.exists() {
        let existing = fs::read(path).map_err(|source| io_error("read", path, source))?;
        if existing != bytes {
            return Err(Error::ExperimentState(format!(
                "existing static probe artifact `{}` differs from reconstruction",
                path.display()
            )));
        }
        return Ok(());
    }
    save_bytes_atomic(path, bytes)
}

fn save_bytes_atomic(path: &Path, bytes: &[u8]) -> Result<()> {
    let parent = path.parent().unwrap_or_else(|| Path::new("."));
    fs::create_dir_all(parent).map_err(|source| io_error("create", parent, source))?;
    let name = path
        .file_name()
        .and_then(|name| name.to_str())
        .ok_or_else(|| Error::NonUtf8Path(path.to_owned()))?;
    let temporary = parent.join(format!(".{name}.tmp"));
    match fs::remove_file(&temporary) {
        Ok(()) => {}
        Err(source) if source.kind() == std::io::ErrorKind::NotFound => {}
        Err(source) => return Err(io_error("remove", &temporary, source)),
    }
    let mut options = OpenOptions::new();
    options.create_new(true).write(true);
    #[cfg(unix)]
    {
        use std::os::unix::fs::OpenOptionsExt as _;
        options.mode(0o600);
    }
    let file = options
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
    File::open(parent)
        .and_then(|directory| directory.sync_all())
        .map_err(|source| io_error("sync", parent, source))
}

fn require_sha256(value: &str, label: &str) -> Result<()> {
    if value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        Ok(())
    } else {
        Err(Error::ExperimentState(format!(
            "{label} must be 64 lowercase hexadecimal digits"
        )))
    }
}

fn vector_identity(representation_version: &str, vector: &[f32]) -> String {
    let mut bytes = Vec::with_capacity(
        representation_version
            .len()
            .saturating_add(1)
            .saturating_add(vector.len().saturating_mul(size_of::<f32>())),
    );
    bytes.extend_from_slice(representation_version.as_bytes());
    bytes.push(0);
    for coordinate in vector {
        bytes.extend_from_slice(&coordinate.to_bits().to_le_bytes());
    }
    hash_bytes(&bytes)
}
