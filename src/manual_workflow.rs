//! Guided local evaluation of the ordered final-corpus meaning map.

use std::collections::BTreeSet;
use std::fs::{self, File, OpenOptions};
use std::io::{BufRead, BufWriter, Write};
use std::path::{Path, PathBuf};

use nostrdb::{Ndb, Transaction};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use whatlang::{Lang, detect};

use crate::embedding::EmbeddingEncoder;
use crate::event::EventId;
use crate::oracle::{Oracle, OracleCandidate, OracleResponse, OrderedOfflineOracle};
use crate::runner::{ExperimentRunner, ExperimentState, InterestId, LocalCandidate, WorthJudgment};
use crate::snapshot::{Error, Result, Validation, io_error, ndb_error, open_ndb, read_manifest};

const SESSION_SCHEMA_VERSION: u32 = 3;
const BOOTSTRAP_RETRIEVAL_MULTIPLIER: usize = 10;
const LANGUAGE_FILTER_POLICY: &str =
    "whatlang-0.18.0:strip-context-exclude-reliable-non-english-v2";
const RECOMMENDATION_SAMPLING_POLICY: &str = "even-rank-coverage-sha256-blinded-order-v1";

/// Files and fixed experiment limits for one guided session.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ManualWorkflowConfig {
    /// Deduplicated final-corpus NostrDB.
    pub corpus_path: PathBuf,
    /// Complete deterministic final-corpus event-ID order.
    pub ordered_event_ids_path: PathBuf,
    /// Ordered embedding prefix produced by CREC-42.
    pub embedding_artifact_path: PathBuf,
    /// Private, resumable evidence file written after every decision.
    pub session_path: PathBuf,
    /// Maximum topic-bootstrap candidates shown after local filtering.
    pub onboarding_depth: usize,
    /// Raw semantic neighbors requested independently for each selected source.
    pub neighbor_depth: usize,
    /// Maximum recommendation judgments in this session.
    pub recommendation_limit: usize,
}

/// Durable point reached by the guided session.
#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ManualSessionPhase {
    /// Onboarding candidates exist but source choices have not been submitted.
    SelectSources,
    /// The fixed sampled and blinded recommendation list is being judged.
    JudgeRecommendations,
    /// No further input belongs to this session.
    Complete,
}

/// Why a completed session stopped presenting recommendations.
#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ManualCompletionReason {
    /// No onboarding note was suitable as a positive source.
    NoPositiveSources,
    /// Every sampled candidate was judged before the fixed limit.
    CandidatesExhausted,
    /// The fixed manual-judgment limit was reached.
    RecommendationLimitReached,
}

/// One explicit response to one displayed recommendation.
#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ManualDecisionKind {
    /// This person was glad to see the note.
    WorthSeeing,
    /// This person was not glad to see the note.
    NotWorthSeeing,
    /// The note had already been seen outside this session.
    AlreadySeen,
    /// Linked context required for a judgment could not be viewed.
    CannotJudgeMissingContext,
}

/// The unmodified source-specific response recorded for one selected note.
#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
pub struct ManualSourceResponse {
    /// Selected positive note queried independently.
    pub source_note_id: EventId,
    /// Exact response returned for this source.
    pub response: OracleResponse,
}

/// One displayed recommendation and the person's event-specific judgment.
#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
pub struct ManualDecision {
    /// Candidate and all public source evidence used by local ordering.
    pub candidate: LocalCandidate,
    /// Explicit response applying only to this event.
    pub judgment: ManualDecisionKind,
}

/// Complete local evidence for one resumable manual experiment session.
#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
pub struct ManualSession {
    /// Session schema used to validate resumable state.
    pub schema_version: u32,
    /// Current durable phase.
    pub phase: ManualSessionPhase,
    /// Exact arbitrary interest string entered locally.
    pub topic: String,
    /// Fixed bootstrap depth for this session.
    pub onboarding_depth: usize,
    /// Raw topic-search depth used before local presentation filtering.
    pub bootstrap_retrieval_depth: usize,
    /// Fixed per-source neighbor depth for this session.
    pub neighbor_depth: usize,
    /// Fixed maximum number of recommendation judgments.
    pub recommendation_limit: usize,
    /// Interest created by the topic bootstrap.
    pub interest_id: InterestId,
    /// Complete raw public response retained before local presentation filtering.
    pub bootstrap_response: OracleResponse,
    /// Fixed experiment-only local language-filter policy.
    pub language_filter_policy: String,
    /// Bootstrap candidates that passed the local filter and were presented.
    pub onboarding_candidates: Vec<OracleCandidate>,
    /// Onboarding notes explicitly selected as independent positive sources.
    pub selected_source_ids: Vec<EventId>,
    /// Complete public response for every independently queried source.
    pub source_responses: Vec<ManualSourceResponse>,
    /// Local unseen candidate order before experiment-only language filtering.
    pub unfiltered_recommendation_candidates: Vec<LocalCandidate>,
    /// Complete locally ordered candidate pool after language filtering.
    pub eligible_recommendation_candidates: Vec<LocalCandidate>,
    /// Fixed policy used to sample and blind the presented candidates.
    pub recommendation_sampling_policy: String,
    /// Fixed sampled presentation order produced before any judgment.
    pub recommendation_candidates: Vec<LocalCandidate>,
    /// Submitted judgments in presentation order.
    pub decisions: Vec<ManualDecision>,
    /// Private runner state after the last durable transition.
    pub runner_state: ExperimentState,
    /// Present only after the session reaches `complete`.
    pub completion_reason: Option<ManualCompletionReason>,
}

/// Whether the invocation completed the session or saved it for later.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ManualWorkflowOutcome {
    /// More guided input remains.
    Paused,
    /// The evidence file represents a completed session.
    Complete,
}

enum SourceSelectionOutcome {
    Paused,
    Ready,
    Complete,
}

/// Run or resume the complete guided workflow through ordinary terminal I/O.
pub fn run_manual_workflow<E, R, W>(
    config: &ManualWorkflowConfig,
    encoder: E,
    mut input: R,
    output: &mut W,
) -> Result<ManualWorkflowOutcome>
where
    E: EmbeddingEncoder,
    R: BufRead,
    W: Write,
{
    validate_config(config)?;
    let loaded = if config.session_path.exists() {
        let session: ManualSession = read_manifest(&config.session_path)?;
        validate_session(&session, config)?;
        Some(session)
    } else {
        None
    };
    if let Some(session) = loaded.as_ref()
        && session.phase == ManualSessionPhase::Complete
    {
        print_summary(output, session, &config.session_path)?;
        return Ok(ManualWorkflowOutcome::Complete);
    }

    let mut oracle = OrderedOfflineOracle::open(
        &config.corpus_path,
        &config.ordered_event_ids_path,
        &config.embedding_artifact_path,
        encoder,
    )?;
    let corpus = open_ndb(&config.corpus_path, Validation::TrustedSource)?;
    let mut session = if let Some(session) = loaded {
        session
    } else {
        write_output(
            output,
            "This private experiment uses one interest and saves every choice locally.\n\n",
        )?;
        let topic = loop {
            let Some(line) = prompt_line(output, &mut input, "Enter one interest: ")? else {
                return Ok(ManualWorkflowOutcome::Paused);
            };
            if line.trim().is_empty() {
                write_output(output, "The interest must not be empty.\n")?;
                continue;
            }
            break line;
        };
        let bootstrap_retrieval_depth = bootstrap_retrieval_depth(config.onboarding_depth)?;
        let bootstrap_response = oracle.search_text(&topic, bootstrap_retrieval_depth)?;
        let onboarding_candidates = filter_oracle_candidates(
            &corpus,
            &config.corpus_path,
            &bootstrap_response.candidates,
            config.onboarding_depth,
        )?;
        let onboarding_ids = onboarding_candidates
            .iter()
            .map(|candidate| candidate.event_id)
            .collect();
        let mut runner = ExperimentRunner::new();
        let bootstrap = runner.bootstrap_with_onboarding(
            topic.clone(),
            bootstrap_response,
            bootstrap_retrieval_depth,
            onboarding_ids,
        )?;
        let session = ManualSession {
            schema_version: SESSION_SCHEMA_VERSION,
            phase: ManualSessionPhase::SelectSources,
            topic,
            onboarding_depth: config.onboarding_depth,
            bootstrap_retrieval_depth,
            neighbor_depth: config.neighbor_depth,
            recommendation_limit: config.recommendation_limit,
            interest_id: bootstrap.interest_id,
            bootstrap_response: bootstrap.response,
            language_filter_policy: LANGUAGE_FILTER_POLICY.to_owned(),
            onboarding_candidates,
            selected_source_ids: Vec::new(),
            source_responses: Vec::new(),
            unfiltered_recommendation_candidates: Vec::new(),
            eligible_recommendation_candidates: Vec::new(),
            recommendation_sampling_policy: RECOMMENDATION_SAMPLING_POLICY.to_owned(),
            recommendation_candidates: Vec::new(),
            decisions: Vec::new(),
            runner_state: runner.into_state(),
            completion_reason: None,
        };
        save_session(&config.session_path, &session)?;
        session
    };
    if session.phase == ManualSessionPhase::SelectSources {
        let outcome = select_sources(
            config,
            &corpus,
            &mut oracle,
            &mut session,
            &mut input,
            output,
        )?;
        match outcome {
            SourceSelectionOutcome::Paused => return Ok(ManualWorkflowOutcome::Paused),
            SourceSelectionOutcome::Complete => {
                print_summary(output, &session, &config.session_path)?;
                return Ok(ManualWorkflowOutcome::Complete);
            }
            SourceSelectionOutcome::Ready => {}
        }
    }

    judge_recommendations(config, &corpus, &mut session, &mut input, output)
}

fn select_sources<E, R, W>(
    config: &ManualWorkflowConfig,
    corpus: &Ndb,
    oracle: &mut OrderedOfflineOracle<E>,
    session: &mut ManualSession,
    input: &mut R,
    output: &mut W,
) -> Result<SourceSelectionOutcome>
where
    E: EmbeddingEncoder,
    R: BufRead,
    W: Write,
{
    write_output(
        output,
        &format!(
            "\nChoose only notes that represent `{}` and that you want more notes like. A merely worthwhile note is not a source; use `none` if nothing fits.\n",
            session.topic
        ),
    )?;
    write_sparsity_notice(
        output,
        "onboarding",
        session.onboarding_candidates.len(),
        session.onboarding_depth,
    )?;
    for (index, candidate) in session.onboarding_candidates.iter().enumerate() {
        display_note(
            output,
            corpus,
            &config.corpus_path,
            index + 1,
            candidate.event_id,
        )?;
    }

    loop {
        let Some(line) = prompt_line(
            output,
            input,
            "Select numbers (comma-separated), `open N`, `none`, or `q`: ",
        )?
        else {
            return Ok(SourceSelectionOutcome::Paused);
        };
        match line.trim() {
            "q" => return Ok(SourceSelectionOutcome::Paused),
            "none" => {
                session.phase = ManualSessionPhase::Complete;
                session.completion_reason = Some(ManualCompletionReason::NoPositiveSources);
                save_session(&config.session_path, session)?;
                return Ok(SourceSelectionOutcome::Complete);
            }
            _ => {}
        }
        match requested_open_index(&line) {
            Ok(Some(index)) if index > 0 && index <= session.onboarding_candidates.len() => {
                open_linked_context(
                    output,
                    corpus,
                    &config.corpus_path,
                    session.onboarding_candidates[index - 1].event_id,
                )?;
                continue;
            }
            Ok(Some(_)) | Err(()) => {
                write_output(output, "Use `open N` with a displayed note number.\n")?;
                continue;
            }
            Ok(None) => {}
        }
        let Some(indices) = parse_indices(&line, session.onboarding_candidates.len()) else {
            write_output(
                output,
                "Enter valid displayed numbers, `open N`, `none`, or `q`.\n",
            )?;
            continue;
        };

        let mut runner = ExperimentRunner::restore(session.runner_state.clone())?;
        let mut selected_source_ids = Vec::with_capacity(indices.len());
        for index in indices {
            let event_id = session.onboarding_candidates[index - 1].event_id;
            runner.select_positive_source(session.interest_id, event_id)?;
            selected_source_ids.push(event_id);
        }

        let mut recording = RecordingOracle::new(oracle);
        let unfiltered_recommendation_candidates =
            runner.recommend(&mut recording, config.neighbor_depth)?;
        let eligible_recommendation_candidates = filter_local_candidates(
            corpus,
            &config.corpus_path,
            &unfiltered_recommendation_candidates,
        )?;
        let recommendation_candidates = sample_recommendation_candidates(
            &session.topic,
            &eligible_recommendation_candidates,
            session.recommendation_limit,
        );
        session.selected_source_ids = selected_source_ids;
        session.source_responses = recording.responses;
        session.unfiltered_recommendation_candidates = unfiltered_recommendation_candidates;
        session.eligible_recommendation_candidates = eligible_recommendation_candidates;
        session.recommendation_candidates = recommendation_candidates;
        session.runner_state = runner.into_state();
        session.phase = ManualSessionPhase::JudgeRecommendations;
        save_session(&config.session_path, session)?;
        write_sparsity_notice(
            output,
            "recommendation",
            session.eligible_recommendation_candidates.len(),
            session.recommendation_limit,
        )?;
        return Ok(SourceSelectionOutcome::Ready);
    }
}

fn judge_recommendations<R, W>(
    config: &ManualWorkflowConfig,
    corpus: &Ndb,
    session: &mut ManualSession,
    input: &mut R,
    output: &mut W,
) -> Result<ManualWorkflowOutcome>
where
    R: BufRead,
    W: Write,
{
    loop {
        let target = session
            .recommendation_limit
            .min(session.recommendation_candidates.len());
        if session.decisions.len() >= target {
            complete_session(config, session)?;
            print_summary(output, session, &config.session_path)?;
            return Ok(ManualWorkflowOutcome::Complete);
        }

        let candidate = session.recommendation_candidates[session.decisions.len()].clone();
        write_output(output, "\nRecommendation\n")?;
        display_note(output, corpus, &config.corpus_path, 0, candidate.event_id)?;
        let judgment = loop {
            let Some(line) = prompt_line(
                output,
                input,
                "Worth seeing? [w = yes, n = no, a = already seen, c = cannot judge, o = show context links, q = stop]: ",
            )?
            else {
                return Ok(ManualWorkflowOutcome::Paused);
            };
            match line.trim() {
                "w" => break ManualDecisionKind::WorthSeeing,
                "n" => break ManualDecisionKind::NotWorthSeeing,
                "a" => break ManualDecisionKind::AlreadySeen,
                "c" => break ManualDecisionKind::CannotJudgeMissingContext,
                "o" => {
                    open_linked_context(output, corpus, &config.corpus_path, candidate.event_id)?
                }
                "q" => return Ok(ManualWorkflowOutcome::Paused),
                _ => write_output(output, "Enter `w`, `n`, `a`, `c`, `o`, or `q`.\n")?,
            }
        };
        apply_decision(session, candidate, judgment)?;
        save_session(&config.session_path, session)?;

        let target = session
            .recommendation_limit
            .min(session.recommendation_candidates.len());
        if session.decisions.len() >= target {
            complete_session(config, session)?;
            print_summary(output, session, &config.session_path)?;
            return Ok(ManualWorkflowOutcome::Complete);
        }
        loop {
            let Some(line) = prompt_line(
                output,
                input,
                "Press Enter for the next recommendation, or `q` to save and stop: ",
            )?
            else {
                return Ok(ManualWorkflowOutcome::Paused);
            };
            match line.trim() {
                "" => break,
                "q" => return Ok(ManualWorkflowOutcome::Paused),
                _ => write_output(output, "Press Enter or type `q`.\n")?,
            }
        }
    }
}

fn apply_decision(
    session: &mut ManualSession,
    candidate: LocalCandidate,
    judgment: ManualDecisionKind,
) -> Result<()> {
    let mut runner = ExperimentRunner::restore(session.runner_state.clone())?;
    match judgment {
        ManualDecisionKind::WorthSeeing => {
            runner.record_worth(candidate.event_id, WorthJudgment::WorthSeeing);
        }
        ManualDecisionKind::NotWorthSeeing => {
            runner.record_worth(candidate.event_id, WorthJudgment::NotWorthSeeing);
        }
        ManualDecisionKind::AlreadySeen | ManualDecisionKind::CannotJudgeMissingContext => {
            runner.mark_seen(candidate.event_id);
        }
    }
    session.decisions.push(ManualDecision {
        candidate,
        judgment,
    });
    session.runner_state = runner.into_state();
    Ok(())
}

fn complete_session(config: &ManualWorkflowConfig, session: &mut ManualSession) -> Result<()> {
    session.phase = ManualSessionPhase::Complete;
    session.completion_reason = Some(
        if session.decisions.len() >= session.recommendation_limit
            && session.recommendation_candidates.len() >= session.recommendation_limit
        {
            ManualCompletionReason::RecommendationLimitReached
        } else {
            ManualCompletionReason::CandidatesExhausted
        },
    );
    save_session(&config.session_path, session)
}

fn validate_config(config: &ManualWorkflowConfig) -> Result<()> {
    if config.onboarding_depth == 0
        || config.neighbor_depth == 0
        || config.recommendation_limit == 0
    {
        return Err(Error::ExperimentState(
            "manual workflow depths and recommendation limit must be positive".to_owned(),
        ));
    }
    bootstrap_retrieval_depth(config.onboarding_depth)?;
    Ok(())
}

fn validate_session(session: &ManualSession, config: &ManualWorkflowConfig) -> Result<()> {
    let expected_bootstrap_retrieval_depth = bootstrap_retrieval_depth(config.onboarding_depth)?;
    if session.schema_version != SESSION_SCHEMA_VERSION
        || session.onboarding_depth != config.onboarding_depth
        || session.bootstrap_retrieval_depth != expected_bootstrap_retrieval_depth
        || session.neighbor_depth != config.neighbor_depth
        || session.recommendation_limit != config.recommendation_limit
        || session.language_filter_policy != LANGUAGE_FILTER_POLICY
        || session.recommendation_sampling_policy != RECOMMENDATION_SAMPLING_POLICY
    {
        return Err(Error::ExperimentState(
            "manual session does not match the requested workflow version or limits".to_owned(),
        ));
    }
    if session.topic.is_empty()
        || session.completion_reason.is_some() != (session.phase == ManualSessionPhase::Complete)
        || session.decisions.len() > session.recommendation_limit
        || session.decisions.len() > session.recommendation_candidates.len()
        || session.recommendation_candidates.len() > session.recommendation_limit
        || session.onboarding_candidates.len() > session.onboarding_depth
        || session.bootstrap_response.provenance.candidate_depth
            != u64::try_from(session.bootstrap_retrieval_depth).map_err(|_| {
                Error::ExperimentState(
                    "manual bootstrap retrieval depth does not fit u64".to_owned(),
                )
            })?
        || !is_ordered_subset(
            &session.bootstrap_response.candidates,
            &session.onboarding_candidates,
        )
        || !is_ordered_subset(
            &session.unfiltered_recommendation_candidates,
            &session.eligible_recommendation_candidates,
        )
        || session.recommendation_candidates
            != sample_recommendation_candidates(
                &session.topic,
                &session.eligible_recommendation_candidates,
                session.recommendation_limit,
            )
    {
        return Err(Error::ExperimentState(
            "manual session phase or counts are inconsistent".to_owned(),
        ));
    }
    let runner = ExperimentRunner::restore(session.runner_state.clone())?;
    let interest = runner
        .state()
        .interest(session.interest_id)
        .ok_or_else(|| Error::InterestNotFound(session.interest_id.get()))?;
    if interest.text() != session.topic
        || interest.onboarding_ids()
            != &session
                .onboarding_candidates
                .iter()
                .map(|candidate| candidate.event_id)
                .collect::<BTreeSet<_>>()
        || interest.positive_sources()
            != &session
                .selected_source_ids
                .iter()
                .copied()
                .collect::<BTreeSet<_>>()
    {
        return Err(Error::ExperimentState(
            "manual session disagrees with its private runner state".to_owned(),
        ));
    }
    for (decision, candidate) in session
        .decisions
        .iter()
        .zip(&session.recommendation_candidates)
    {
        if decision.candidate != *candidate || !runner.state().seen().contains(&candidate.event_id)
        {
            return Err(Error::ExperimentState(
                "manual decision order or seen state is inconsistent".to_owned(),
            ));
        }
        let expected = match decision.judgment {
            ManualDecisionKind::WorthSeeing => Some(WorthJudgment::WorthSeeing),
            ManualDecisionKind::NotWorthSeeing => Some(WorthJudgment::NotWorthSeeing),
            ManualDecisionKind::AlreadySeen | ManualDecisionKind::CannotJudgeMissingContext => None,
        };
        if runner.state().worth_judgment(candidate.event_id) != expected {
            return Err(Error::ExperimentState(
                "manual judgment disagrees with private runner state".to_owned(),
            ));
        }
    }
    Ok(())
}

fn bootstrap_retrieval_depth(onboarding_depth: usize) -> Result<usize> {
    onboarding_depth
        .checked_mul(BOOTSTRAP_RETRIEVAL_MULTIPLIER)
        .ok_or_else(|| {
            Error::ExperimentState("bootstrap retrieval depth overflowed usize".to_owned())
        })
}

fn filter_oracle_candidates(
    corpus: &Ndb,
    corpus_path: &Path,
    candidates: &[OracleCandidate],
    limit: usize,
) -> Result<Vec<OracleCandidate>> {
    let transaction = Transaction::new(corpus)
        .map_err(|source| ndb_error("open transaction on", corpus_path, source))?;
    let mut filtered = Vec::with_capacity(limit.min(candidates.len()));
    for candidate in candidates {
        if event_is_english_eligible(corpus, &transaction, corpus_path, candidate.event_id)? {
            filtered.push(candidate.clone());
            if filtered.len() == limit {
                break;
            }
        }
    }
    Ok(filtered)
}

fn filter_local_candidates(
    corpus: &Ndb,
    corpus_path: &Path,
    candidates: &[LocalCandidate],
) -> Result<Vec<LocalCandidate>> {
    let transaction = Transaction::new(corpus)
        .map_err(|source| ndb_error("open transaction on", corpus_path, source))?;
    let mut filtered = Vec::with_capacity(candidates.len());
    for candidate in candidates {
        if event_is_english_eligible(corpus, &transaction, corpus_path, candidate.event_id)? {
            filtered.push(candidate.clone());
        }
    }
    Ok(filtered)
}

fn event_is_english_eligible(
    corpus: &Ndb,
    transaction: &Transaction,
    corpus_path: &Path,
    event_id: EventId,
) -> Result<bool> {
    let note = corpus
        .get_note_by_id(transaction, event_id.as_bytes())
        .map_err(|source| ndb_error("load event from", corpus_path, source))?;
    let detection_text = language_detection_text(note.content());
    Ok(match detect(&detection_text) {
        Some(info) if info.is_reliable() => info.lang() == Lang::Eng,
        Some(_) | None => true,
    })
}

fn language_detection_text(content: &str) -> String {
    content
        .split_whitespace()
        .filter(|token| context_url_for_token(token).is_none())
        .collect::<Vec<_>>()
        .join(" ")
}

fn context_url_for_token(token: &str) -> Option<String> {
    let token = trim_context_token(token);
    if token.starts_with("https://") || token.starts_with("http://") {
        return Some(token.to_owned());
    }
    let identifier = token.strip_prefix("nostr:").unwrap_or(token);
    let supported = ["note1", "nevent1", "npub1", "nprofile1", "naddr1"]
        .iter()
        .any(|prefix| identifier.starts_with(prefix));
    if supported
        && identifier
            .chars()
            .all(|character| character.is_ascii_lowercase() || character.is_ascii_digit())
    {
        Some(format!("https://njump.me/{identifier}"))
    } else {
        None
    }
}

fn trim_context_token(token: &str) -> &str {
    token
        .trim_start_matches(['(', '[', '{', '<', '"', '\''])
        .trim_end_matches(['.', ',', ';', ':', '!', '?', ')', ']', '}', '>', '"', '\''])
}

fn sample_recommendation_candidates(
    topic: &str,
    candidates: &[LocalCandidate],
    limit: usize,
) -> Vec<LocalCandidate> {
    let sample_size = limit.min(candidates.len());
    if sample_size == 0 {
        return Vec::new();
    }
    let mut sampled = (0..sample_size)
        .map(|sample_index| {
            let candidate_index = if sample_size == 1 {
                0
            } else {
                let numerator = sample_index as u128 * (candidates.len() - 1) as u128;
                let denominator = (sample_size - 1) as u128;
                usize::try_from(numerator / denominator)
                    .expect("sample index is bounded by the candidate slice")
            };
            candidates[candidate_index].clone()
        })
        .collect::<Vec<_>>();
    sampled.sort_by(|left, right| {
        blinded_order_key(topic, left.event_id)
            .cmp(&blinded_order_key(topic, right.event_id))
            .then_with(|| left.event_id.cmp(&right.event_id))
    });
    sampled
}

fn blinded_order_key(topic: &str, event_id: EventId) -> [u8; 32] {
    let mut hasher = Sha256::new();
    hasher.update(RECOMMENDATION_SAMPLING_POLICY.as_bytes());
    hasher.update([0]);
    hasher.update(topic.as_bytes());
    hasher.update([0]);
    hasher.update(event_id.as_bytes());
    hasher.finalize().into()
}

fn is_ordered_subset<T: PartialEq>(all: &[T], subset: &[T]) -> bool {
    let mut remaining = all.iter();
    subset
        .iter()
        .all(|expected| remaining.by_ref().any(|candidate| candidate == expected))
}

fn write_sparsity_notice(
    output: &mut impl Write,
    candidate_kind: &str,
    available: usize,
    requested: usize,
) -> Result<()> {
    if available >= requested {
        return Ok(());
    }
    write_output(
        output,
        &format!(
            "Only {available} English-eligible {candidate_kind} notes are available. Treat this shortage as 10K corpus sparsity, not recommendation-quality evidence.\n"
        ),
    )
}

fn requested_open_index(line: &str) -> std::result::Result<Option<usize>, ()> {
    let mut parts = line.split_whitespace();
    let Some(command) = parts.next() else {
        return Ok(None);
    };
    if command != "open" && command != "o" {
        return Ok(None);
    }
    let index = parts.next().ok_or(())?.parse::<usize>().map_err(|_| ())?;
    if parts.next().is_some() {
        return Err(());
    }
    Ok(Some(index))
}

fn parse_indices(line: &str, candidate_count: usize) -> Option<Vec<usize>> {
    let mut selected = BTreeSet::new();
    for value in line.split(|character: char| character == ',' || character.is_whitespace()) {
        if value.is_empty() {
            continue;
        }
        let index = value.parse::<usize>().ok()?;
        if index == 0 || index > candidate_count {
            return None;
        }
        selected.insert(index);
    }
    (!selected.is_empty()).then(|| selected.into_iter().collect())
}

fn open_linked_context<W: Write>(
    output: &mut W,
    corpus: &Ndb,
    corpus_path: &Path,
    event_id: EventId,
) -> Result<()> {
    let urls = {
        let transaction = Transaction::new(corpus)
            .map_err(|source| ndb_error("open transaction on", corpus_path, source))?;
        let note = corpus
            .get_note_by_id(&transaction, event_id.as_bytes())
            .map_err(|source| ndb_error("load event from", corpus_path, source))?;
        let mut seen = BTreeSet::new();
        note.content()
            .split_whitespace()
            .filter_map(context_url_for_token)
            .filter(|url| seen.insert(url.clone()))
            .collect::<Vec<_>>()
    };

    if urls.is_empty() {
        return write_output(output, "No linked context was found in this note.\n");
    }
    write_output(output, "Linked context (open from your terminal):\n")?;
    for (index, url) in urls.iter().enumerate() {
        write_output(output, &format!("{}. {url}\n", index + 1))?;
    }
    Ok(())
}

fn display_note<W: Write>(
    output: &mut W,
    corpus: &Ndb,
    corpus_path: &Path,
    index: usize,
    event_id: EventId,
) -> Result<()> {
    let transaction = Transaction::new(corpus)
        .map_err(|source| ndb_error("open transaction on", corpus_path, source))?;
    let note = corpus
        .get_note_by_id(&transaction, event_id.as_bytes())
        .map_err(|source| ndb_error("load event from", corpus_path, source))?;
    let content = terminal_safe(note.content());
    if index == 0 {
        write_output(output, &format!("\n{content}\n"))
    } else {
        write_output(output, &format!("\n{index}.\n{content}\n"))
    }
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

fn print_summary<W: Write>(
    output: &mut W,
    session: &ManualSession,
    session_path: &Path,
) -> Result<()> {
    let worth = session
        .decisions
        .iter()
        .filter(|decision| decision.judgment == ManualDecisionKind::WorthSeeing)
        .count();
    let not_worth = session
        .decisions
        .iter()
        .filter(|decision| decision.judgment == ManualDecisionKind::NotWorthSeeing)
        .count();
    let missing_context = session
        .decisions
        .iter()
        .filter(|decision| decision.judgment == ManualDecisionKind::CannotJudgeMissingContext)
        .count();
    let already_seen = session
        .decisions
        .iter()
        .filter(|decision| decision.judgment == ManualDecisionKind::AlreadySeen)
        .count();
    write_output(
        output,
        &format!(
            "\nSession complete: {worth} worth seeing, {not_worth} not worth seeing, {missing_context} missing context, {already_seen} already seen.\nEvidence: {}\n",
            session_path.display()
        ),
    )
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

fn save_session(path: &Path, session: &ManualSession) -> Result<()> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|source| io_error("create", parent, source))?;
    }
    let file_name = path
        .file_name()
        .and_then(|name| name.to_str())
        .ok_or_else(|| Error::NonUtf8Path(path.to_owned()))?;
    let temporary = path.with_file_name(format!(".{file_name}.tmp"));
    let file = OpenOptions::new()
        .create(true)
        .truncate(true)
        .write(true)
        .open(&temporary)
        .map_err(|source| io_error("create", &temporary, source))?;
    let mut writer = BufWriter::new(file);
    serde_json::to_writer_pretty(&mut writer, session).map_err(|source| Error::Manifest {
        operation: "encode",
        path: temporary.clone(),
        source,
    })?;
    writer
        .write_all(b"\n")
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

struct RecordingOracle<'a, E> {
    oracle: &'a mut OrderedOfflineOracle<E>,
    responses: Vec<ManualSourceResponse>,
}

impl<'a, E> RecordingOracle<'a, E> {
    fn new(oracle: &'a mut OrderedOfflineOracle<E>) -> Self {
        Self {
            oracle,
            responses: Vec::new(),
        }
    }
}

impl<E> Oracle for RecordingOracle<'_, E>
where
    E: EmbeddingEncoder,
{
    fn search_text(&mut self, text: &str, candidate_depth: usize) -> Result<OracleResponse> {
        self.oracle.search_text(text, candidate_depth)
    }

    fn similar_notes(
        &mut self,
        note_id: EventId,
        candidate_depth: usize,
    ) -> Result<OracleResponse> {
        let response = self.oracle.similar_notes(note_id, candidate_depth)?;
        self.responses.push(ManualSourceResponse {
            source_note_id: note_id,
            response: response.clone(),
        });
        Ok(response)
    }
}
