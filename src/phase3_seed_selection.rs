//! Resumable, coverage-guided selection of the five Phase 3 seed notes.

use std::collections::{BTreeMap, BTreeSet};
use std::fs::{self, File, OpenOptions};
use std::io::{BufWriter, Write};
use std::path::{Path, PathBuf};

use nostrdb::{Ndb, Transaction};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

use crate::candidate_order::{CANDIDATE_DEPTH, CandidateOrderOracle};
use crate::evaluator::{
    CompletionView, EvaluatorDecision, EvaluatorUi, RATING_ANCHORS, RATING_QUESTION, RatingOutcome,
    RatingView, RecoveryOutcome, RecoveryView, RestOutcome, RestView, WRONG_LANGUAGE_RULE,
};
use crate::fp32_oracle::{SimilarNotesRequest, SimilarNotesResponse};
use crate::phase3_binding::Phase3SeedBinding;
use crate::quota_resolution::PriorPresentation;
use crate::representation::EventId;
use crate::snapshot::{
    Error, Result, Validation, io_error, ndb_error, open_existing_ndb, read_manifest,
};

const SESSION_SCHEMA_VERSION: u32 = 1;
const HANDOFF_SCHEMA_VERSION: u32 = 1;
const PURPOSE: &str = "phase3-seed-selection-v1";
const SELECTION_POLICY: &str = "similar-notes-1024-maximum-marginal-event-id-union-v1";
const SEED_COUNT: usize = 5;
const ORACLE_WAVE_SIZE: usize = 40;
const REST_INTERVAL: usize = 20;

/// Immutable inputs for one private seed-screening session.
#[derive(Clone, Debug)]
pub struct Phase3SeedSelectionConfig {
    /// Disposable NostrDB used to display the curated source notes.
    pub corpus_path: PathBuf,
    /// Verified identity shared with the later Phase 3 run.
    pub corpus_identity: String,
    /// Durable private screening transcript.
    pub session_path: PathBuf,
    /// Create-once handoff published only after five positive ratings.
    pub handoff_path: PathBuf,
    /// Exact public representation used by `similar_notes`.
    pub representation_version: String,
    /// Ordered, curated, represented, self-contained source-note IDs.
    pub candidate_event_ids: Vec<EventId>,
}

/// Result of one invocation of the seed-selection session.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum Phase3SeedSelectionOutcome {
    Paused,
    Complete(Box<Phase3SeedSelectionHandoff>),
}

/// The exact screening judgment stored for one presented source note.
#[derive(Clone, Copy, Debug, Eq, PartialEq, Deserialize, Serialize)]
#[serde(rename_all = "snake_case", tag = "kind", content = "rating")]
pub enum ScreeningDecision {
    Rating(u8),
    WrongLanguage,
}

/// One source-note presentation in immutable screening order.
#[derive(Clone, Debug, Eq, PartialEq, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ScreeningPresentation {
    event_id: EventId,
    decision: ScreeningDecision,
    marginal_new_event_ids: Option<usize>,
    selection_response_sha256: Option<String>,
}

impl ScreeningPresentation {
    pub const fn event_id(&self) -> EventId {
        self.event_id
    }

    pub const fn decision(&self) -> ScreeningDecision {
        self.decision
    }

    pub const fn marginal_new_event_ids(&self) -> Option<usize> {
        self.marginal_new_event_ids
    }
}

/// Create-once output consumed by the Phase 3 launcher.
#[derive(Clone, Debug, Eq, PartialEq, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct Phase3SeedSelectionHandoff {
    schema_version: u32,
    purpose: String,
    identity_sha256: String,
    corpus_identity: String,
    representation_version: String,
    candidate_depth: usize,
    candidate_pool_sha256: String,
    selection_policy: String,
    evaluator_question: String,
    evaluator_anchors: [String; 7],
    wrong_language_rule: String,
    presentations: Vec<ScreeningPresentation>,
    seeds: Vec<Phase3SeedBinding>,
    oracle_responses: Vec<CachedResponseRef>,
}

impl Phase3SeedSelectionHandoff {
    pub fn identity_sha256(&self) -> &str {
        &self.identity_sha256
    }

    pub fn corpus_identity(&self) -> &str {
        &self.corpus_identity
    }

    pub fn representation_version(&self) -> &str {
        &self.representation_version
    }

    pub const fn candidate_depth(&self) -> usize {
        self.candidate_depth
    }

    pub fn selection_policy(&self) -> &str {
        &self.selection_policy
    }

    pub fn presentations(&self) -> &[ScreeningPresentation] {
        &self.presentations
    }

    pub fn seeds(&self) -> &[Phase3SeedBinding] {
        &self.seeds
    }

    /// Screening notes that must never become personalizer evidence but must
    /// remain in the exact-ID no-repeat ledger.
    pub fn initial_presentations(
        &self,
    ) -> std::result::Result<BTreeMap<EventId, PriorPresentation>, String> {
        let seeds = self
            .seeds
            .iter()
            .map(Phase3SeedBinding::event_id)
            .collect::<std::result::Result<BTreeSet<_>, _>>()?;
        Ok(self
            .presentations
            .iter()
            .filter(|presentation| !seeds.contains(&presentation.event_id))
            .map(|presentation| {
                let state = match presentation.decision {
                    ScreeningDecision::Rating(_) => PriorPresentation::EligibleUnrated,
                    ScreeningDecision::WrongLanguage => PriorPresentation::WrongLanguage,
                };
                (presentation.event_id, state)
            })
            .collect())
    }

    fn validate(&self) -> Result<()> {
        if self.schema_version != HANDOFF_SCHEMA_VERSION
            || self.purpose != PURPOSE
            || self.candidate_depth != CANDIDATE_DEPTH
            || self.selection_policy != SELECTION_POLICY
            || self.evaluator_question != RATING_QUESTION
            || self.evaluator_anchors != RATING_ANCHORS.map(str::to_owned)
            || self.wrong_language_rule != WRONG_LANGUAGE_RULE
        {
            return Err(Error::ExperimentState(
                "seed-selection handoff has an incompatible protocol".to_owned(),
            ));
        }
        if self.corpus_identity.trim().is_empty()
            || !is_sha256(&self.representation_version)
            || !is_sha256(&self.candidate_pool_sha256)
        {
            return Err(Error::ExperimentState(
                "seed-selection handoff has invalid input identities".to_owned(),
            ));
        }
        validate_handoff_transcript(&self.presentations, &self.seeds)?;
        let mut response_sources = BTreeSet::new();
        for response in &self.oracle_responses {
            if response.representation_version != self.representation_version
                || response.candidate_depth != CANDIDATE_DEPTH
                || !is_sha256(&response.sha256)
                || !response_sources.insert(response.source_event_id)
            {
                return Err(Error::ExperimentState(
                    "seed-selection handoff has invalid Oracle response identities".to_owned(),
                ));
            }
        }
        validate_selection_provenance(&self.presentations, &self.oracle_responses, true)?;
        if self.identity_sha256 != handoff_identity(self)? {
            return Err(Error::ExperimentState(
                "seed-selection handoff identity is invalid".to_owned(),
            ));
        }
        Ok(())
    }
}

/// Read and fully validate a completed private handoff.
pub fn read_phase3_seed_selection_handoff(
    path: impl AsRef<Path>,
) -> Result<Phase3SeedSelectionHandoff> {
    let handoff: Phase3SeedSelectionHandoff = read_manifest(path.as_ref())?;
    handoff.validate()?;
    Ok(handoff)
}

#[derive(Clone, Debug, Eq, PartialEq, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct StaticBinding {
    corpus_identity: String,
    representation_version: String,
    candidate_depth: usize,
    candidate_pool_sha256: String,
    candidate_event_ids: Vec<EventId>,
    selection_policy: String,
    evaluator_question: String,
    evaluator_anchors: [String; 7],
    wrong_language_rule: String,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Deserialize, Serialize)]
#[serde(rename_all = "snake_case")]
enum SessionPhase {
    Screening,
    Complete,
    Exhausted,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct SeedSelectionSession {
    schema_version: u32,
    purpose: String,
    state_sha256: String,
    binding: StaticBinding,
    phase: SessionPhase,
    response_refs: Vec<CachedResponseRef>,
    presentations: Vec<ScreeningPresentation>,
    pending_presentation: Option<PendingPresentation>,
    completed_rests: Vec<usize>,
    failure_reason: Option<String>,
    handoff_sha256: Option<String>,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct PendingPresentation {
    event_id: EventId,
    marginal_new_event_ids: Option<usize>,
    selection_response_sha256: Option<[u8; 32]>,
}

#[derive(Clone, Debug, Eq, Ord, PartialEq, PartialOrd, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct CachedResponseRef {
    representation_version: String,
    source_event_id: EventId,
    candidate_depth: usize,
    sha256: String,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct CachedResponseEnvelope {
    representation_version: String,
    source_event_id: EventId,
    candidate_depth: usize,
    response: SimilarNotesResponse,
}

/// Run or resume the production seed selector through the shared evaluator UI.
pub fn run_phase3_seed_selection<O, U>(
    config: &Phase3SeedSelectionConfig,
    oracle: &mut O,
    evaluator: &mut U,
) -> Result<Phase3SeedSelectionOutcome>
where
    O: CandidateOrderOracle,
    U: EvaluatorUi,
{
    let binding = validate_config(config, oracle)?;
    let _lock = acquire_session_lock(&config.session_path)?;
    let cache_dir = response_cache_dir(&config.session_path)?;
    prepare_private_directory(&cache_dir)?;
    protect_optional_private_file(&config.session_path)?;
    protect_optional_private_file(&config.handoff_path)?;

    let resumed = config.session_path.exists();
    let mut session = if resumed {
        let session: SeedSelectionSession = read_manifest(&config.session_path)?;
        validate_session(&session, &binding, &cache_dir)?;
        session
    } else {
        if config.handoff_path.exists() {
            return Err(Error::ExperimentState(
                "seed-selection handoff exists without its durable session".to_owned(),
            ));
        }
        let session = SeedSelectionSession {
            schema_version: SESSION_SCHEMA_VERSION,
            purpose: PURPOSE.to_owned(),
            state_sha256: String::new(),
            binding,
            phase: SessionPhase::Screening,
            response_refs: Vec::new(),
            presentations: Vec::new(),
            pending_presentation: None,
            completed_rests: Vec::new(),
            failure_reason: None,
            handoff_sha256: None,
        };
        save_session(&config.session_path, &session)?;
        session
    };

    match session.phase {
        SessionPhase::Complete => {
            let handoff = read_phase3_seed_selection_handoff(&config.handoff_path)?;
            validate_completed_session(&session, &handoff)?;
            evaluator
                .complete(CompletionView::new(session.presentations.len()))
                .map_err(|source| io_error("write", "<terminal-output>", source))?;
            return Ok(Phase3SeedSelectionOutcome::Complete(Box::new(handoff)));
        }
        SessionPhase::Exhausted => {
            return Err(Error::ExperimentState(
                session.failure_reason.clone().ok_or_else(|| {
                    Error::Invariant("exhausted seed session has no failure reason".to_owned())
                })?,
            ));
        }
        SessionPhase::Screening => {}
    }

    let mut recover_pending = resumed && session.pending_presentation.is_some();
    let corpus = open_existing_ndb(&config.corpus_path, Validation::TrustedSource)?;
    loop {
        if accepted_seed_count(&session.presentations) == SEED_COUNT {
            let handoff = publish_handoff(config, &mut session)?;
            evaluator
                .complete(CompletionView::new(session.presentations.len()))
                .map_err(|source| io_error("write", "<terminal-output>", source))?;
            return Ok(Phase3SeedSelectionOutcome::Complete(Box::new(handoff)));
        }

        if !take_due_rest(config, &mut session, evaluator)? {
            return Ok(Phase3SeedSelectionOutcome::Paused);
        }

        let (pending, recover) = match session.pending_presentation {
            Some(pending) => {
                let recover = recover_pending;
                recover_pending = false;
                (pending, recover)
            }
            None => {
                let next = choose_next(config, &mut session, oracle, evaluator, &cache_dir)?;
                let Some(next) = next else {
                    let reason = format!(
                        "seed-selection source pool exhausted after {} presentations with {} positive seeds",
                        session.presentations.len(),
                        accepted_seed_count(&session.presentations)
                    );
                    session.phase = SessionPhase::Exhausted;
                    session.failure_reason = Some(reason.clone());
                    save_session(&config.session_path, &session)?;
                    return Err(Error::ExperimentState(reason));
                };
                session.pending_presentation = Some(next);
                save_session(&config.session_path, &session)?;
                (next, false)
            }
        };

        let submission = if recover {
            match evaluator
                .recover(RecoveryView::new(
                    session.presentations.len() + 1,
                    break_in(session.presentations.len()),
                ))
                .map_err(|source| io_error("read", "<terminal-input>", source))?
            {
                RecoveryOutcome::Submitted(submission) => Some(submission),
                RecoveryOutcome::Redisplay => {
                    rate_pending(&corpus, config, &session, pending, evaluator)?
                }
                RecoveryOutcome::Paused => return Ok(Phase3SeedSelectionOutcome::Paused),
            }
        } else {
            rate_pending(&corpus, config, &session, pending, evaluator)?
        };
        let Some(submission) = submission else {
            return Ok(Phase3SeedSelectionOutcome::Paused);
        };
        store_submission(config, &mut session, pending, submission.decision())?;
        if accepted_seed_count(&session.presentations) == SEED_COUNT {
            continue;
        }
        if submission.pause_after() {
            return Ok(Phase3SeedSelectionOutcome::Paused);
        }
    }
}

fn rate_pending<U: EvaluatorUi>(
    corpus: &Ndb,
    config: &Phase3SeedSelectionConfig,
    session: &SeedSelectionSession,
    pending: PendingPresentation,
    evaluator: &mut U,
) -> Result<Option<crate::evaluator::EvaluatorSubmission>> {
    let transaction = Transaction::new(corpus)
        .map_err(|source| ndb_error("open transaction on", &config.corpus_path, source))?;
    let note = corpus
        .get_note_by_id(&transaction, &pending.event_id)
        .map_err(|source| ndb_error("load seed candidate from", &config.corpus_path, source))?;
    match evaluator
        .rate(RatingView::new(
            note.content(),
            session.presentations.len() + 1,
            break_in(session.presentations.len()),
        ))
        .map_err(|source| io_error("read", "<terminal-input>", source))?
    {
        RatingOutcome::Submitted(submission) => Ok(Some(submission)),
        RatingOutcome::Paused => Ok(None),
    }
}

fn store_submission(
    config: &Phase3SeedSelectionConfig,
    session: &mut SeedSelectionSession,
    pending: PendingPresentation,
    decision: EvaluatorDecision,
) -> Result<()> {
    let decision = match decision {
        EvaluatorDecision::Rating(rating @ 1..=7) => ScreeningDecision::Rating(rating),
        EvaluatorDecision::Rating(_) => {
            return Err(Error::ExperimentState(
                "seed-selection evaluator returned a rating outside 1–7".to_owned(),
            ));
        }
        EvaluatorDecision::WrongLanguage => ScreeningDecision::WrongLanguage,
    };
    let response_sha256 = pending
        .selection_response_sha256
        .map(|bytes| bytes.iter().map(|byte| format!("{byte:02x}")).collect());
    session.presentations.push(ScreeningPresentation {
        event_id: pending.event_id,
        decision,
        marginal_new_event_ids: pending.marginal_new_event_ids,
        selection_response_sha256: response_sha256,
    });
    session.pending_presentation = None;
    save_session(&config.session_path, session)
}

fn choose_next<O, U>(
    config: &Phase3SeedSelectionConfig,
    session: &mut SeedSelectionSession,
    oracle: &mut O,
    evaluator: &mut U,
    cache_dir: &Path,
) -> Result<Option<PendingPresentation>>
where
    O: CandidateOrderOracle,
    U: EvaluatorUi,
{
    let presented = session
        .presentations
        .iter()
        .map(ScreeningPresentation::event_id)
        .collect::<BTreeSet<_>>();
    let remaining = session
        .binding
        .candidate_event_ids
        .iter()
        .copied()
        .filter(|event_id| !presented.contains(event_id))
        .collect::<Vec<_>>();
    if remaining.is_empty() {
        return Ok(None);
    }
    let accepted = accepted_seed_ids(&session.presentations);
    if accepted.is_empty() {
        return Ok(Some(PendingPresentation {
            event_id: remaining[0],
            marginal_new_event_ids: None,
            selection_response_sha256: None,
        }));
    }

    evaluator
        .preparing()
        .map_err(|source| io_error("write", "<terminal-output>", source))?;
    let required = accepted
        .iter()
        .copied()
        .chain(remaining.iter().copied())
        .collect::<BTreeSet<_>>();
    ensure_responses(config, session, oracle, cache_dir, &required)?;
    let responses = load_responses(session, cache_dir)?;
    let mut union = BTreeSet::new();
    for seed in &accepted {
        union.extend(
            responses
                .get(seed)
                .ok_or_else(|| {
                    Error::Invariant("accepted seed lacks a cached response".to_owned())
                })?
                .candidates
                .iter()
                .map(|candidate| candidate.event_id),
        );
    }

    let mut best = None;
    for event_id in remaining {
        let response = responses.get(&event_id).ok_or_else(|| {
            Error::Invariant("remaining seed candidate lacks a cached response".to_owned())
        })?;
        let marginal = response
            .candidates
            .iter()
            .filter(|candidate| !union.contains(&candidate.event_id))
            .count();
        if best
            .as_ref()
            .is_none_or(|(_, best_marginal, _)| marginal > *best_marginal)
        {
            let sha256 = session
                .response_refs
                .iter()
                .find(|reference| reference.source_event_id == event_id)
                .ok_or_else(|| Error::Invariant("cached response lost its identity".to_owned()))?
                .sha256
                .clone();
            best = Some((event_id, marginal, sha256));
        }
    }
    best.map(|(event_id, marginal, sha256)| {
        let bytes = decode_sha256(&sha256)?;
        Ok(PendingPresentation {
            event_id,
            marginal_new_event_ids: Some(marginal),
            selection_response_sha256: Some(bytes),
        })
    })
    .transpose()
}

fn ensure_responses<O: CandidateOrderOracle>(
    config: &Phase3SeedSelectionConfig,
    session: &mut SeedSelectionSession,
    oracle: &mut O,
    cache_dir: &Path,
    required: &BTreeSet<EventId>,
) -> Result<()> {
    recover_orphaned_responses(config, session, cache_dir, required)?;
    let existing = session
        .response_refs
        .iter()
        .map(|reference| reference.source_event_id)
        .collect::<BTreeSet<_>>();
    let missing = session
        .binding
        .candidate_event_ids
        .iter()
        .copied()
        .filter(|event_id| required.contains(event_id) && !existing.contains(event_id))
        .collect::<Vec<_>>();
    for sources in missing.chunks(ORACLE_WAVE_SIZE) {
        let requests = sources
            .iter()
            .copied()
            .map(|note_id| SimilarNotesRequest {
                note_id,
                candidate_depth: CANDIDATE_DEPTH,
            })
            .collect::<Vec<_>>();
        let wave = oracle.similar_notes_wave(&requests, &config.representation_version)?;
        if wave.responses.len() != requests.len() {
            return Err(Error::Invariant(
                "seed-selection Oracle returned the wrong response count".to_owned(),
            ));
        }
        for (request, response) in requests.into_iter().zip(wave.responses) {
            validate_response(&response, request.note_id, &config.representation_version)?;
            let envelope = CachedResponseEnvelope {
                representation_version: config.representation_version.clone(),
                source_event_id: request.note_id,
                candidate_depth: CANDIDATE_DEPTH,
                response,
            };
            let bytes = canonical_json(&envelope, cache_dir)?;
            let sha256 = sha256_bytes(&bytes);
            let reference = CachedResponseRef {
                representation_version: config.representation_version.clone(),
                source_event_id: request.note_id,
                candidate_depth: CANDIDATE_DEPTH,
                sha256,
            };
            write_cache_entry(cache_dir, &reference, &bytes)?;
            session.response_refs.push(reference);
        }
        session.response_refs.sort();
        save_session(&config.session_path, session)?;
    }
    Ok(())
}

fn recover_orphaned_responses(
    config: &Phase3SeedSelectionConfig,
    session: &mut SeedSelectionSession,
    cache_dir: &Path,
    required: &BTreeSet<EventId>,
) -> Result<()> {
    let existing = session
        .response_refs
        .iter()
        .map(|reference| reference.source_event_id)
        .collect::<BTreeSet<_>>();
    let mut recovered = false;
    for source_event_id in required {
        if existing.contains(source_event_id) {
            continue;
        }
        let reference_without_hash = CachedResponseRef {
            representation_version: config.representation_version.clone(),
            source_event_id: *source_event_id,
            candidate_depth: CANDIDATE_DEPTH,
            sha256: String::new(),
        };
        let path = response_path(cache_dir, &reference_without_hash);
        if !path.exists() {
            continue;
        }
        protect_optional_private_file(&path)?;
        let bytes = fs::read(&path).map_err(|source| io_error("read", &path, source))?;
        let reference = CachedResponseRef {
            sha256: sha256_bytes(&bytes),
            ..reference_without_hash
        };
        read_cached_response(cache_dir, &reference)?;
        session.response_refs.push(reference);
        recovered = true;
    }
    if recovered {
        session.response_refs.sort();
        save_session(&config.session_path, session)?;
    }
    Ok(())
}

fn load_responses(
    session: &SeedSelectionSession,
    cache_dir: &Path,
) -> Result<BTreeMap<EventId, SimilarNotesResponse>> {
    session
        .response_refs
        .iter()
        .map(|reference| {
            let envelope = read_cached_response(cache_dir, reference)?;
            Ok((reference.source_event_id, envelope.response))
        })
        .collect()
}

fn validate_response(
    response: &SimilarNotesResponse,
    source: EventId,
    representation_version: &str,
) -> Result<()> {
    if response.representation_version != representation_version
        || !response.complete
        || response.represented_rows != response.total_rows
        || response.total_rows == 0
    {
        return Err(Error::ExperimentState(
            "seed-selection Oracle returned an incomplete or incompatible response".to_owned(),
        ));
    }
    let expected = usize::try_from(response.total_rows.saturating_sub(1))
        .unwrap_or(usize::MAX)
        .min(CANDIDATE_DEPTH);
    if response.candidates.len() != expected {
        return Err(Error::ExperimentState(format!(
            "seed-selection Oracle returned {} candidates instead of {expected}",
            response.candidates.len()
        )));
    }
    let mut ids = BTreeSet::new();
    for (index, candidate) in response.candidates.iter().enumerate() {
        if candidate.rank != index + 1
            || candidate.event_id == source
            || !candidate.cosine_score.is_finite()
            || !ids.insert(candidate.event_id)
        {
            return Err(Error::ExperimentState(
                "seed-selection Oracle response has invalid ranks or event IDs".to_owned(),
            ));
        }
    }
    Ok(())
}

fn validate_config<O: CandidateOrderOracle>(
    config: &Phase3SeedSelectionConfig,
    oracle: &O,
) -> Result<StaticBinding> {
    if config.corpus_identity.trim().is_empty()
        || !is_sha256(&config.representation_version)
        || oracle.representation_version() != config.representation_version
        || config.session_path == config.handoff_path
    {
        return Err(Error::ExperimentState(
            "seed-selection inputs have incompatible identities or paths".to_owned(),
        ));
    }
    if config.candidate_event_ids.len() < SEED_COUNT {
        return Err(Error::ExperimentState(
            "seed selection requires at least five curated candidates".to_owned(),
        ));
    }
    let unique = config
        .candidate_event_ids
        .iter()
        .copied()
        .collect::<BTreeSet<_>>();
    if unique.len() != config.candidate_event_ids.len() {
        return Err(Error::ExperimentState(
            "seed-selection candidate IDs must be unique".to_owned(),
        ));
    }
    Ok(StaticBinding {
        corpus_identity: config.corpus_identity.clone(),
        representation_version: config.representation_version.clone(),
        candidate_depth: CANDIDATE_DEPTH,
        candidate_pool_sha256: candidate_pool_identity(&config.candidate_event_ids),
        candidate_event_ids: config.candidate_event_ids.clone(),
        selection_policy: SELECTION_POLICY.to_owned(),
        evaluator_question: RATING_QUESTION.to_owned(),
        evaluator_anchors: RATING_ANCHORS.map(str::to_owned),
        wrong_language_rule: WRONG_LANGUAGE_RULE.to_owned(),
    })
}

fn validate_session(
    session: &SeedSelectionSession,
    expected: &StaticBinding,
    cache_dir: &Path,
) -> Result<()> {
    if session.schema_version != SESSION_SCHEMA_VERSION
        || session.purpose != PURPOSE
        || &session.binding != expected
        || session.state_sha256 != session_identity(session)?
    {
        return Err(Error::ExperimentState(
            "stored seed-selection session does not match its immutable inputs".to_owned(),
        ));
    }
    let candidate_ids = expected
        .candidate_event_ids
        .iter()
        .copied()
        .collect::<BTreeSet<_>>();
    let mut presented = BTreeSet::new();
    for presentation in &session.presentations {
        if !candidate_ids.contains(&presentation.event_id)
            || !presented.insert(presentation.event_id)
        {
            return Err(Error::ExperimentState(
                "stored seed-selection transcript has invalid source IDs".to_owned(),
            ));
        }
        validate_decision(presentation.decision)?;
    }
    if let Some(pending) = session.pending_presentation
        && (!candidate_ids.contains(&pending.event_id) || presented.contains(&pending.event_id))
    {
        return Err(Error::ExperimentState(
            "stored seed-selection pending presentation is invalid".to_owned(),
        ));
    }
    let mut sources = BTreeSet::new();
    for reference in &session.response_refs {
        if reference.representation_version != expected.representation_version
            || reference.candidate_depth != CANDIDATE_DEPTH
            || !candidate_ids.contains(&reference.source_event_id)
            || !sources.insert(reference.source_event_id)
        {
            return Err(Error::ExperimentState(
                "stored seed-selection response ledger is invalid".to_owned(),
            ));
        }
        read_cached_response(cache_dir, reference)?;
    }
    validate_selection_provenance(&session.presentations, &session.response_refs, false)?;
    if let Some(pending) = session.pending_presentation {
        validate_pending_provenance(
            pending,
            accepted_seed_count(&session.presentations) > 0,
            &session.response_refs,
        )?;
    }
    match session.phase {
        SessionPhase::Screening => {
            let accepted = accepted_seed_count(&session.presentations);
            if session.failure_reason.is_some()
                || session.handoff_sha256.is_some()
                || accepted > SEED_COUNT
                || (accepted == SEED_COUNT && session.pending_presentation.is_some())
            {
                return Err(Error::ExperimentState(
                    "active seed-selection session has invalid terminal state".to_owned(),
                ));
            }
        }
        SessionPhase::Complete => {
            if session.pending_presentation.is_some()
                || session.failure_reason.is_some()
                || session
                    .handoff_sha256
                    .as_ref()
                    .is_none_or(|hash| !is_sha256(hash))
                || accepted_seed_count(&session.presentations) != SEED_COUNT
            {
                return Err(Error::ExperimentState(
                    "completed seed-selection session is invalid".to_owned(),
                ));
            }
        }
        SessionPhase::Exhausted => {
            if session.pending_presentation.is_some()
                || session.handoff_sha256.is_some()
                || session
                    .failure_reason
                    .as_ref()
                    .is_none_or(|reason| reason.is_empty())
                || session.presentations.len() != expected.candidate_event_ids.len()
                || accepted_seed_count(&session.presentations) >= SEED_COUNT
            {
                return Err(Error::ExperimentState(
                    "exhausted seed-selection session is invalid".to_owned(),
                ));
            }
        }
    }
    Ok(())
}

fn validate_handoff_transcript(
    presentations: &[ScreeningPresentation],
    seeds: &[Phase3SeedBinding],
) -> Result<()> {
    if seeds.len() != SEED_COUNT || presentations.is_empty() {
        return Err(Error::ExperimentState(
            "seed-selection handoff must contain exactly five seeds".to_owned(),
        ));
    }
    let mut seen = BTreeSet::new();
    let accepted = presentations
        .iter()
        .filter_map(|presentation| {
            validate_decision(presentation.decision).ok()?;
            seen.insert(presentation.event_id).then_some(presentation)
        })
        .filter_map(|presentation| match presentation.decision {
            ScreeningDecision::Rating(rating @ 5..=7) => Some((presentation.event_id, rating)),
            _ => None,
        })
        .collect::<Vec<_>>();
    if seen.len() != presentations.len()
        || accepted.len() != SEED_COUNT
        || !matches!(
            presentations
                .last()
                .map(|presentation| presentation.decision),
            Some(ScreeningDecision::Rating(5..=7))
        )
    {
        return Err(Error::ExperimentState(
            "seed-selection handoff transcript is inconsistent".to_owned(),
        ));
    }
    let serialized_seeds = seeds
        .iter()
        .map(|seed| {
            Ok((
                seed.event_id().map_err(Error::ExperimentState)?,
                seed.rating(),
            ))
        })
        .collect::<Result<Vec<_>>>()?;
    if serialized_seeds != accepted {
        return Err(Error::ExperimentState(
            "seed-selection handoff seeds do not match its positive transcript".to_owned(),
        ));
    }
    Ok(())
}

fn validate_selection_provenance(
    presentations: &[ScreeningPresentation],
    response_refs: &[CachedResponseRef],
    require_seed_responses: bool,
) -> Result<()> {
    let responses = response_refs
        .iter()
        .map(|reference| (reference.source_event_id, reference.sha256.as_str()))
        .collect::<BTreeMap<_, _>>();
    let mut accepted_before = false;
    for presentation in presentations {
        match (
            accepted_before,
            presentation.marginal_new_event_ids,
            presentation.selection_response_sha256.as_deref(),
        ) {
            (false, None, None) => {}
            (true, Some(_), Some(sha256))
                if responses.get(&presentation.event_id).copied() == Some(sha256) => {}
            _ => {
                return Err(Error::ExperimentState(
                    "seed-selection transcript has invalid Oracle selection provenance".to_owned(),
                ));
            }
        }
        if matches!(presentation.decision, ScreeningDecision::Rating(5..=7)) {
            accepted_before = true;
        }
    }
    if require_seed_responses
        && accepted_seed_ids(presentations)
            .iter()
            .any(|event_id| !responses.contains_key(event_id))
    {
        return Err(Error::ExperimentState(
            "seed-selection handoff is missing a seed Oracle response identity".to_owned(),
        ));
    }
    Ok(())
}

fn validate_pending_provenance(
    pending: PendingPresentation,
    accepted_before: bool,
    response_refs: &[CachedResponseRef],
) -> Result<()> {
    match (
        accepted_before,
        pending.marginal_new_event_ids,
        pending.selection_response_sha256,
    ) {
        (false, None, None) => Ok(()),
        (true, Some(_), Some(sha256)) => {
            let encoded = sha256
                .iter()
                .map(|byte| format!("{byte:02x}"))
                .collect::<String>();
            if response_refs.iter().any(|reference| {
                reference.source_event_id == pending.event_id && reference.sha256 == encoded
            }) {
                Ok(())
            } else {
                Err(Error::ExperimentState(
                    "pending seed-selection presentation has invalid Oracle provenance".to_owned(),
                ))
            }
        }
        _ => Err(Error::ExperimentState(
            "pending seed-selection presentation has invalid Oracle provenance".to_owned(),
        )),
    }
}

fn validate_decision(decision: ScreeningDecision) -> Result<()> {
    match decision {
        ScreeningDecision::Rating(1..=7) | ScreeningDecision::WrongLanguage => Ok(()),
        ScreeningDecision::Rating(_) => Err(Error::ExperimentState(
            "seed-selection transcript contains a rating outside 1–7".to_owned(),
        )),
    }
}

fn publish_handoff(
    config: &Phase3SeedSelectionConfig,
    session: &mut SeedSelectionSession,
) -> Result<Phase3SeedSelectionHandoff> {
    let seeds = session
        .presentations
        .iter()
        .filter_map(|presentation| match presentation.decision {
            ScreeningDecision::Rating(rating @ 5..=7) => Some(Phase3SeedBinding::new(
                event_id_hex(presentation.event_id),
                rating,
            )),
            _ => None,
        })
        .collect::<Vec<_>>();
    let mut handoff = Phase3SeedSelectionHandoff {
        schema_version: HANDOFF_SCHEMA_VERSION,
        purpose: PURPOSE.to_owned(),
        identity_sha256: String::new(),
        corpus_identity: session.binding.corpus_identity.clone(),
        representation_version: session.binding.representation_version.clone(),
        candidate_depth: CANDIDATE_DEPTH,
        candidate_pool_sha256: session.binding.candidate_pool_sha256.clone(),
        selection_policy: SELECTION_POLICY.to_owned(),
        evaluator_question: RATING_QUESTION.to_owned(),
        evaluator_anchors: RATING_ANCHORS.map(str::to_owned),
        wrong_language_rule: WRONG_LANGUAGE_RULE.to_owned(),
        presentations: session.presentations.clone(),
        seeds,
        oracle_responses: session.response_refs.clone(),
    };
    handoff.identity_sha256 = handoff_identity(&handoff)?;
    handoff.validate()?;
    let bytes = canonical_json(&handoff, &config.handoff_path)?;
    if config.handoff_path.exists() {
        protect_optional_private_file(&config.handoff_path)?;
        let existing = fs::read(&config.handoff_path)
            .map_err(|source| io_error("read", &config.handoff_path, source))?;
        if existing != bytes {
            return Err(Error::ExperimentState(
                "existing seed-selection handoff differs from deterministic completion".to_owned(),
            ));
        }
    } else {
        write_create_once(&config.handoff_path, &bytes)?;
    }
    session.phase = SessionPhase::Complete;
    session.handoff_sha256 = Some(sha256_bytes(&bytes));
    session.pending_presentation = None;
    save_session(&config.session_path, session)?;
    Ok(handoff)
}

fn validate_completed_session(
    session: &SeedSelectionSession,
    handoff: &Phase3SeedSelectionHandoff,
) -> Result<()> {
    let handoff_bytes = canonical_json(handoff, Path::new("<handoff>"))?;
    if session.handoff_sha256.as_deref() != Some(&sha256_bytes(&handoff_bytes))
        || session.presentations != handoff.presentations
        || session.response_refs != handoff.oracle_responses
        || session.binding.corpus_identity != handoff.corpus_identity
        || session.binding.representation_version != handoff.representation_version
        || session.binding.candidate_pool_sha256 != handoff.candidate_pool_sha256
    {
        return Err(Error::ExperimentState(
            "completed seed-selection handoff does not match its durable session".to_owned(),
        ));
    }
    Ok(())
}

fn accepted_seed_ids(presentations: &[ScreeningPresentation]) -> Vec<EventId> {
    presentations
        .iter()
        .filter_map(|presentation| {
            matches!(presentation.decision, ScreeningDecision::Rating(5..=7))
                .then_some(presentation.event_id)
        })
        .collect()
}

fn accepted_seed_count(presentations: &[ScreeningPresentation]) -> usize {
    accepted_seed_ids(presentations).len()
}

fn take_due_rest<U: EvaluatorUi>(
    config: &Phase3SeedSelectionConfig,
    session: &mut SeedSelectionSession,
    evaluator: &mut U,
) -> Result<bool> {
    let count = session.presentations.len();
    if count == 0
        || !count.is_multiple_of(REST_INTERVAL)
        || session.completed_rests.contains(&count)
    {
        return Ok(true);
    }
    match evaluator
        .rest(RestView::new(count))
        .map_err(|source| io_error("read", "<terminal-input>", source))?
    {
        RestOutcome::Paused => Ok(false),
        RestOutcome::Continue => {
            session.completed_rests.push(count);
            save_session(&config.session_path, session)?;
            Ok(true)
        }
    }
}

fn break_in(stored: usize) -> usize {
    REST_INTERVAL - stored % REST_INTERVAL
}

fn candidate_pool_identity(event_ids: &[EventId]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(b"oracle-mvp-phase3-seed-candidate-pool-v1\0");
    for event_id in event_ids {
        hasher.update(event_id);
    }
    format!("{:x}", hasher.finalize())
}

fn handoff_identity(handoff: &Phase3SeedSelectionHandoff) -> Result<String> {
    let mut identity_input = handoff.clone();
    identity_input.identity_sha256.clear();
    Ok(sha256_bytes(&canonical_json(
        &identity_input,
        Path::new("<handoff-identity>"),
    )?))
}

fn response_cache_dir(session_path: &Path) -> Result<PathBuf> {
    let name = session_path
        .file_name()
        .and_then(|name| name.to_str())
        .ok_or_else(|| Error::NonUtf8Path(session_path.to_owned()))?;
    Ok(session_path
        .parent()
        .unwrap_or_else(|| Path::new("."))
        .join(format!(".{name}.oracle-responses")))
}

fn response_path(cache_dir: &Path, reference: &CachedResponseRef) -> PathBuf {
    cache_dir.join(format!(
        "response-{}.json",
        event_id_hex(reference.source_event_id)
    ))
}

fn write_cache_entry(cache_dir: &Path, reference: &CachedResponseRef, bytes: &[u8]) -> Result<()> {
    let path = response_path(cache_dir, reference);
    if path.exists() {
        let existing = fs::read(&path).map_err(|source| io_error("read", &path, source))?;
        if existing != bytes || sha256_bytes(&existing) != reference.sha256 {
            return Err(Error::ExperimentState(
                "existing seed-selection Oracle cache entry differs".to_owned(),
            ));
        }
        return Ok(());
    }
    write_create_once(&path, bytes)
}

fn read_cached_response(
    cache_dir: &Path,
    reference: &CachedResponseRef,
) -> Result<CachedResponseEnvelope> {
    let path = response_path(cache_dir, reference);
    protect_optional_private_file(&path)?;
    let bytes = fs::read(&path).map_err(|source| io_error("read", &path, source))?;
    if sha256_bytes(&bytes) != reference.sha256 {
        return Err(Error::ExperimentState(
            "seed-selection Oracle cache entry failed its identity".to_owned(),
        ));
    }
    let envelope: CachedResponseEnvelope =
        serde_json::from_slice(&bytes).map_err(|source| Error::Manifest {
            operation: "decode",
            path: path.clone(),
            source,
        })?;
    if envelope.representation_version != reference.representation_version
        || envelope.source_event_id != reference.source_event_id
        || envelope.candidate_depth != reference.candidate_depth
    {
        return Err(Error::ExperimentState(
            "seed-selection Oracle cache key is invalid".to_owned(),
        ));
    }
    validate_response(
        &envelope.response,
        envelope.source_event_id,
        &envelope.representation_version,
    )?;
    Ok(envelope)
}

fn save_session(path: &Path, session: &SeedSelectionSession) -> Result<()> {
    let mut stored = session.clone();
    stored.state_sha256 = session_identity(&stored)?;
    let bytes = canonical_json(&stored, path)?;
    save_replace_atomic(path, &bytes)
}

fn session_identity(session: &SeedSelectionSession) -> Result<String> {
    let mut identity_input = session.clone();
    identity_input.state_sha256.clear();
    Ok(sha256_bytes(&canonical_json(
        &identity_input,
        Path::new("<seed-selection-session-identity>"),
    )?))
}

fn canonical_json<T: Serialize>(value: &T, path: &Path) -> Result<Vec<u8>> {
    let mut bytes = serde_json::to_vec_pretty(value).map_err(|source| Error::Manifest {
        operation: "encode",
        path: path.to_owned(),
        source,
    })?;
    bytes.push(b'\n');
    Ok(bytes)
}

fn save_replace_atomic(path: &Path, bytes: &[u8]) -> Result<()> {
    let parent = path.parent().unwrap_or_else(|| Path::new("."));
    prepare_private_directory(parent)?;
    protect_optional_private_file(path)?;
    let temporary = temporary_path(path)?;
    if temporary.exists() {
        protect_optional_private_file(&temporary)?;
        fs::remove_file(&temporary).map_err(|source| io_error("remove", &temporary, source))?;
    }
    write_new_file(&temporary, bytes)?;
    fs::rename(&temporary, path).map_err(|source| io_error("publish", path, source))?;
    sync_parent(parent)
}

fn write_create_once(path: &Path, bytes: &[u8]) -> Result<()> {
    let parent = path.parent().unwrap_or_else(|| Path::new("."));
    prepare_private_directory(parent)?;
    if path.exists() {
        return Err(Error::ArtifactExists(path.to_owned()));
    }
    let temporary = temporary_path(path)?;
    if temporary.exists() {
        protect_optional_private_file(&temporary)?;
        fs::remove_file(&temporary).map_err(|source| io_error("remove", &temporary, source))?;
    }
    write_new_file(&temporary, bytes)?;
    fs::rename(&temporary, path).map_err(|source| io_error("publish", path, source))?;
    sync_parent(parent)
}

fn write_new_file(path: &Path, bytes: &[u8]) -> Result<()> {
    let mut options = OpenOptions::new();
    options.create_new(true).write(true);
    #[cfg(unix)]
    {
        use std::os::unix::fs::OpenOptionsExt as _;
        options.mode(0o600);
    }
    let file = options
        .open(path)
        .map_err(|source| io_error("create", path, source))?;
    set_private_file(&file, path)?;
    let mut writer = BufWriter::new(file);
    writer
        .write_all(bytes)
        .and_then(|()| writer.flush())
        .map_err(|source| io_error("write", path, source))?;
    writer
        .get_ref()
        .sync_all()
        .map_err(|source| io_error("sync", path, source))
}

fn acquire_session_lock(session_path: &Path) -> Result<File> {
    let parent = session_path.parent().unwrap_or_else(|| Path::new("."));
    prepare_private_directory(parent)?;
    let name = session_path
        .file_name()
        .and_then(|name| name.to_str())
        .ok_or_else(|| Error::NonUtf8Path(session_path.to_owned()))?;
    let path = parent.join(format!(".{name}.lock"));
    protect_optional_private_file(&path)?;
    let mut options = OpenOptions::new();
    options.create(true).read(true).write(true).truncate(false);
    #[cfg(unix)]
    {
        use std::os::unix::fs::OpenOptionsExt as _;
        options.mode(0o600);
    }
    let file = options
        .open(&path)
        .map_err(|source| io_error("open", &path, source))?;
    set_private_file(&file, &path)?;
    match file.try_lock() {
        Ok(()) => Ok(file),
        Err(fs::TryLockError::WouldBlock) => Err(Error::ExperimentState(format!(
            "seed-selection session `{}` is already active",
            session_path.display()
        ))),
        Err(fs::TryLockError::Error(source)) => Err(io_error("lock", &path, source)),
    }
}

fn prepare_private_directory(path: &Path) -> Result<()> {
    let mut builder = fs::DirBuilder::new();
    builder.recursive(true);
    #[cfg(unix)]
    {
        use std::os::unix::fs::DirBuilderExt as _;
        builder.mode(0o700);
    }
    builder
        .create(path)
        .map_err(|source| io_error("create", path, source))?;
    #[cfg(unix)]
    fs::set_permissions(path, std::os::unix::fs::PermissionsExt::from_mode(0o700))
        .map_err(|source| io_error("set permissions on", path, source))?;
    Ok(())
}

fn protect_optional_private_file(path: &Path) -> Result<()> {
    let metadata = match fs::symlink_metadata(path) {
        Ok(metadata) => metadata,
        Err(source) if source.kind() == std::io::ErrorKind::NotFound => return Ok(()),
        Err(source) => return Err(io_error("inspect", path, source)),
    };
    if !metadata.file_type().is_file() {
        return Err(Error::ExperimentState(format!(
            "private seed-selection artifact `{}` is not a regular file",
            path.display()
        )));
    }
    #[cfg(unix)]
    fs::set_permissions(path, std::os::unix::fs::PermissionsExt::from_mode(0o600))
        .map_err(|source| io_error("set permissions on", path, source))?;
    Ok(())
}

fn set_private_file(file: &File, path: &Path) -> Result<()> {
    #[cfg(unix)]
    file.set_permissions(std::os::unix::fs::PermissionsExt::from_mode(0o600))
        .map_err(|source| io_error("set permissions on", path, source))?;
    Ok(())
}

fn temporary_path(path: &Path) -> Result<PathBuf> {
    let name = path
        .file_name()
        .and_then(|name| name.to_str())
        .ok_or_else(|| Error::NonUtf8Path(path.to_owned()))?;
    Ok(path.with_file_name(format!(".{name}.tmp")))
}

fn sync_parent(parent: &Path) -> Result<()> {
    File::open(parent)
        .and_then(|directory| directory.sync_all())
        .map_err(|source| io_error("sync", parent, source))
}

fn sha256_bytes(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}

fn is_sha256(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

fn decode_sha256(value: &str) -> Result<[u8; 32]> {
    if !is_sha256(value) {
        return Err(Error::Invariant("invalid SHA-256 identity".to_owned()));
    }
    let mut output = [0_u8; 32];
    for (index, pair) in value.as_bytes().chunks_exact(2).enumerate() {
        output[index] = (decode_hex(pair[0])? << 4) | decode_hex(pair[1])?;
    }
    Ok(output)
}

fn decode_hex(byte: u8) -> Result<u8> {
    match byte {
        b'0'..=b'9' => Ok(byte - b'0'),
        b'a'..=b'f' => Ok(byte - b'a' + 10),
        _ => Err(Error::Invariant("invalid lowercase hexadecimal".to_owned())),
    }
}

fn event_id_hex(event_id: EventId) -> String {
    event_id.iter().map(|byte| format!("{byte:02x}")).collect()
}
