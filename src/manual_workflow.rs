//! Guided local evaluation of the ordered final-corpus meaning map.

use std::collections::BTreeSet;
use std::fs::{self, File, OpenOptions};
use std::io::{BufRead, BufWriter, Write};
use std::path::{Path, PathBuf};

use nostrdb::{Ndb, Transaction};
use serde::{Deserialize, Serialize};

use crate::embedding::EmbeddingEncoder;
use crate::event::EventId;
use crate::oracle::{Oracle, OracleResponse, OrderedOfflineOracle};
use crate::runner::{ExperimentRunner, ExperimentState, InterestId, LocalCandidate, WorthJudgment};
use crate::snapshot::{Error, Result, Validation, io_error, ndb_error, open_ndb, read_manifest};

const SESSION_SCHEMA_VERSION: u32 = 1;

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
    /// Topic-bootstrap candidates shown before sources are selected.
    pub onboarding_depth: usize,
    /// Semantic neighbors requested independently for each selected source.
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
    /// The fixed locally ordered recommendation list is being judged.
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
    /// Every locally ordered candidate was judged before the fixed limit.
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
    /// The note was displayed but no worth judgment was made.
    Skipped,
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
    /// Fixed per-source neighbor depth for this session.
    pub neighbor_depth: usize,
    /// Fixed maximum number of recommendation judgments.
    pub recommendation_limit: usize,
    /// Interest created by the topic bootstrap.
    pub interest_id: InterestId,
    /// Complete public response used to show onboarding candidates.
    pub bootstrap_response: OracleResponse,
    /// Onboarding notes explicitly selected as independent positive sources.
    pub selected_source_ids: Vec<EventId>,
    /// Complete public response for every independently queried source.
    pub source_responses: Vec<ManualSourceResponse>,
    /// Fixed unseen candidate order produced before any recommendation judgment.
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
        let mut runner = ExperimentRunner::new();
        let bootstrap = runner.bootstrap(&mut oracle, topic.clone(), config.onboarding_depth)?;
        let session = ManualSession {
            schema_version: SESSION_SCHEMA_VERSION,
            phase: ManualSessionPhase::SelectSources,
            topic,
            onboarding_depth: config.onboarding_depth,
            neighbor_depth: config.neighbor_depth,
            recommendation_limit: config.recommendation_limit,
            interest_id: bootstrap.interest_id,
            bootstrap_response: bootstrap.response,
            selected_source_ids: Vec::new(),
            source_responses: Vec::new(),
            recommendation_candidates: Vec::new(),
            decisions: Vec::new(),
            runner_state: runner.into_state(),
            completion_reason: None,
        };
        save_session(&config.session_path, &session)?;
        session
    };
    let corpus = open_ndb(&config.corpus_path, Validation::TrustedSource)?;
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
        "\nChoose worthwhile source notes. These are onboarding examples, not recommendation judgments.\n",
    )?;
    for (index, candidate) in session.bootstrap_response.candidates.iter().enumerate() {
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
            "Select one or more numbers (comma-separated), `none`, or `q`: ",
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
        let Some(indices) = parse_indices(&line, session.bootstrap_response.candidates.len())
        else {
            write_output(output, "Enter valid displayed numbers, `none`, or `q`.\n")?;
            continue;
        };

        let mut runner = ExperimentRunner::restore(session.runner_state.clone())?;
        let mut selected_source_ids = Vec::with_capacity(indices.len());
        for index in indices {
            let event_id = session.bootstrap_response.candidates[index - 1].event_id;
            runner.select_positive_source(session.interest_id, event_id)?;
            selected_source_ids.push(event_id);
        }

        let mut recording = RecordingOracle::new(oracle);
        let recommendation_candidates = runner.recommend(&mut recording, config.neighbor_depth)?;
        session.selected_source_ids = selected_source_ids;
        session.source_responses = recording.responses;
        session.recommendation_candidates = recommendation_candidates;
        session.runner_state = runner.into_state();
        session.phase = ManualSessionPhase::JudgeRecommendations;
        save_session(&config.session_path, session)?;
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
                "Worth seeing? [w = yes, n = no, a = already seen, s = skip]: ",
            )?
            else {
                apply_decision(session, candidate, ManualDecisionKind::Skipped)?;
                save_session(&config.session_path, session)?;
                return Ok(ManualWorkflowOutcome::Paused);
            };
            match line.trim() {
                "w" => break ManualDecisionKind::WorthSeeing,
                "n" => break ManualDecisionKind::NotWorthSeeing,
                "a" => break ManualDecisionKind::AlreadySeen,
                "s" => break ManualDecisionKind::Skipped,
                _ => write_output(output, "Enter `w`, `n`, `a`, or `s`.\n")?,
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
        ManualDecisionKind::AlreadySeen | ManualDecisionKind::Skipped => {
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
    Ok(())
}

fn validate_session(session: &ManualSession, config: &ManualWorkflowConfig) -> Result<()> {
    if session.schema_version != SESSION_SCHEMA_VERSION
        || session.onboarding_depth != config.onboarding_depth
        || session.neighbor_depth != config.neighbor_depth
        || session.recommendation_limit != config.recommendation_limit
    {
        return Err(Error::ExperimentState(
            "manual session does not match the requested workflow version or limits".to_owned(),
        ));
    }
    if session.topic.is_empty()
        || session.completion_reason.is_some() != (session.phase == ManualSessionPhase::Complete)
        || session.decisions.len() > session.recommendation_limit
        || session.decisions.len() > session.recommendation_candidates.len()
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
                .bootstrap_response
                .candidates
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
            ManualDecisionKind::AlreadySeen | ManualDecisionKind::Skipped => None,
        };
        if runner.state().worth_judgment(candidate.event_id) != expected {
            return Err(Error::ExperimentState(
                "manual judgment disagrees with private runner state".to_owned(),
            ));
        }
    }
    Ok(())
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
    let neutral = session.decisions.len() - worth - not_worth;
    write_output(
        output,
        &format!(
            "\nSession complete: {worth} worth seeing, {not_worth} not worth seeing, {neutral} unjudged.\nEvidence: {}\n",
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
