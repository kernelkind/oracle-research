//! Private experiment state and deterministic local candidate ordering.

use std::collections::{BTreeMap, BTreeSet};

use serde::{Deserialize, Serialize};

use crate::event::EventId;
use crate::oracle::{Oracle, OracleResponse, OracleVersions};
use crate::snapshot::{Error, Result};

const STATE_SCHEMA_VERSION: u32 = 1;

/// Stable identifier for one locally entered interest string.
#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(transparent)]
pub struct InterestId(u64);

impl InterestId {
    /// Return the local numeric identifier.
    pub const fn get(self) -> u64 {
        self.0
    }
}

/// One local interest and the onboarding choices made for it.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct InterestState {
    text: String,
    onboarding_ids: BTreeSet<EventId>,
    positive_sources: BTreeSet<EventId>,
}

impl InterestState {
    /// Return the exact arbitrary interest string entered locally.
    pub fn text(&self) -> &str {
        &self.text
    }

    /// Return every onboarding candidate, all of which are excluded from evaluation.
    pub fn onboarding_ids(&self) -> &BTreeSet<EventId> {
        &self.onboarding_ids
    }

    /// Return the notes explicitly selected as independent retrieval sources.
    pub fn positive_sources(&self) -> &BTreeSet<EventId> {
        &self.positive_sources
    }
}

/// An explicit judgment about only the named event.
#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum WorthJudgment {
    /// The person was glad to see this event.
    WorthSeeing,
    /// The person was not glad to see this event.
    NotWorthSeeing,
}

/// An uninterpreted instruction intended to control future recommendations.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct RecommendationControlInstruction {
    interest_id: InterestId,
    instruction: String,
}

impl RecommendationControlInstruction {
    /// Return the interest to which the instruction was attached.
    pub const fn interest_id(&self) -> InterestId {
        self.interest_id
    }

    /// Return the exact locally entered instruction.
    pub fn instruction(&self) -> &str {
        &self.instruction
    }
}

/// Serializable private state owned by one device.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct ExperimentState {
    schema_version: u32,
    next_interest_id: u64,
    interests: BTreeMap<InterestId, InterestState>,
    current_interest: Option<InterestId>,
    worth_judgments: BTreeMap<EventId, WorthJudgment>,
    recommendation_controls: Vec<RecommendationControlInstruction>,
    seen: BTreeSet<EventId>,
}

impl ExperimentState {
    /// Return one interest by its stable local identifier.
    pub fn interest(&self, interest_id: InterestId) -> Option<&InterestState> {
        self.interests.get(&interest_id)
    }

    /// Return all interests in stable identifier order.
    pub fn interests(&self) -> &BTreeMap<InterestId, InterestState> {
        &self.interests
    }

    /// Return the interest currently prioritized by local ordering.
    pub const fn current_interest(&self) -> Option<InterestId> {
        self.current_interest
    }

    /// Return the exact worth judgment for one event, if any.
    pub fn worth_judgment(&self, event_id: EventId) -> Option<WorthJudgment> {
        self.worth_judgments.get(&event_id).copied()
    }

    /// Return recommendation-control instructions separately from worth judgments.
    pub fn recommendation_controls(&self) -> &[RecommendationControlInstruction] {
        &self.recommendation_controls
    }

    /// Return per-device seen event IDs.
    pub fn seen(&self) -> &BTreeSet<EventId> {
        &self.seen
    }
}

impl Default for ExperimentState {
    fn default() -> Self {
        Self {
            schema_version: STATE_SCHEMA_VERSION,
            next_interest_id: 1,
            interests: BTreeMap::new(),
            current_interest: None,
            worth_judgments: BTreeMap::new(),
            recommendation_controls: Vec::new(),
            seen: BTreeSet::new(),
        }
    }
}

/// Result of one topic-bootstrap transition.
#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
pub struct BootstrapResult {
    /// Local interest created for the exact input string.
    pub interest_id: InterestId,
    /// Source-specific onboarding evidence returned by the oracle.
    pub response: OracleResponse,
}

/// Evidence retained from one independently queried positive source.
#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
pub struct SourceEvidence {
    /// Interest under which the source note was selected.
    pub interest_id: InterestId,
    /// Positive note queried independently.
    pub source_note_id: EventId,
    /// One-based rank in that source's oracle response.
    pub source_rank: u64,
    /// Cosine score in that source's oracle response.
    pub cosine_score: f32,
    /// Corpus and retriever identities for this evidence.
    pub versions: OracleVersions,
}

/// One unseen candidate after local filtering and duplicate removal.
#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
pub struct LocalCandidate {
    /// Canonical event ID presented at most once in the local union.
    pub event_id: EventId,
    /// One-based deterministic position in the local order.
    pub local_rank: u64,
    /// Unmodified evidence from every source that returned this event.
    pub evidence: Vec<SourceEvidence>,
}

/// Owns private state and orchestrates stateless source-specific oracle calls.
pub struct ExperimentRunner {
    state: ExperimentState,
}

impl ExperimentRunner {
    /// Create empty per-device experiment state.
    pub fn new() -> Self {
        Self {
            state: ExperimentState::default(),
        }
    }

    /// Restore serialized state after validating every local invariant.
    pub fn restore(state: ExperimentState) -> Result<Self> {
        validate_state(&state)?;
        Ok(Self { state })
    }

    /// Return read-only private state for UI and persistence.
    pub const fn state(&self) -> &ExperimentState {
        &self.state
    }

    /// Consume the runner and return its serializable private state.
    pub fn into_state(self) -> ExperimentState {
        self.state
    }

    /// Search one arbitrary interest string and mark every onboarding result seen.
    pub fn bootstrap(
        &mut self,
        oracle: &mut impl Oracle,
        text: String,
        candidate_depth: usize,
    ) -> Result<BootstrapResult> {
        let response = oracle.search_text(&text, candidate_depth)?;
        validate_response(&response)?;
        let interest_id = InterestId(self.state.next_interest_id);
        let next_interest_id = self
            .state
            .next_interest_id
            .checked_add(1)
            .ok_or_else(|| Error::ExperimentState("interest ID overflowed u64".to_owned()))?;
        let onboarding_ids = response
            .candidates
            .iter()
            .map(|candidate| candidate.event_id)
            .collect::<BTreeSet<_>>();
        self.state.seen.extend(onboarding_ids.iter().copied());
        self.state.interests.insert(
            interest_id,
            InterestState {
                text,
                onboarding_ids,
                positive_sources: BTreeSet::new(),
            },
        );
        self.state.next_interest_id = next_interest_id;
        self.state.current_interest = Some(interest_id);
        Ok(BootstrapResult {
            interest_id,
            response,
        })
    }

    /// Select one of an interest's onboarding notes as an independent source.
    pub fn select_positive_source(
        &mut self,
        interest_id: InterestId,
        event_id: EventId,
    ) -> Result<()> {
        let interest = self
            .state
            .interests
            .get_mut(&interest_id)
            .ok_or(Error::InterestNotFound(interest_id.get()))?;
        if !interest.onboarding_ids.contains(&event_id) {
            return Err(Error::InvalidPositiveSource {
                event_id: event_id.to_string(),
                interest_id: interest_id.get(),
            });
        }
        interest.positive_sources.insert(event_id);
        Ok(())
    }

    /// Change which interest receives the first opportunity in each local round.
    pub fn set_current_interest(&mut self, interest_id: InterestId) -> Result<()> {
        if !self.state.interests.contains_key(&interest_id) {
            return Err(Error::InterestNotFound(interest_id.get()));
        }
        self.state.current_interest = Some(interest_id);
        Ok(())
    }

    /// Record a worth judgment for exactly one event and mark that event seen.
    pub fn record_worth(&mut self, event_id: EventId, judgment: WorthJudgment) {
        self.state.worth_judgments.insert(event_id, judgment);
        self.state.seen.insert(event_id);
    }

    /// Mark exactly one event seen on this device without inferring a preference.
    pub fn mark_seen(&mut self, event_id: EventId) {
        self.state.seen.insert(event_id);
    }

    /// Store a recommendation-control instruction without treating it as a judgment.
    pub fn record_recommendation_control(
        &mut self,
        interest_id: InterestId,
        instruction: String,
    ) -> Result<()> {
        if !self.state.interests.contains_key(&interest_id) {
            return Err(Error::InterestNotFound(interest_id.get()));
        }
        if instruction.trim().is_empty() {
            return Err(Error::InvalidQuery(
                "recommendation-control instruction must not be empty".to_owned(),
            ));
        }
        self.state
            .recommendation_controls
            .push(RecommendationControlInstruction {
                interest_id,
                instruction,
            });
        Ok(())
    }

    /// Query every positive source separately, then filter and order only locally.
    pub fn recommend(
        &self,
        oracle: &mut impl Oracle,
        candidate_depth: usize,
    ) -> Result<Vec<LocalCandidate>> {
        let interest_order = self.interest_order();
        let onboarding = self
            .state
            .interests
            .values()
            .flat_map(|interest| interest.onboarding_ids.iter().copied())
            .collect::<BTreeSet<_>>();
        let mut evidence: BTreeMap<EventId, Vec<SourceEvidence>> = BTreeMap::new();
        let mut queues = Vec::new();
        let mut expected_versions: Option<OracleVersions> = None;

        for interest_id in interest_order {
            let interest = self
                .state
                .interests
                .get(&interest_id)
                .expect("ordered interest exists");
            let mut source_queues = Vec::new();
            for source_note_id in &interest.positive_sources {
                let response = oracle.similar_notes(*source_note_id, candidate_depth)?;
                validate_response(&response)?;
                match &expected_versions {
                    Some(versions) if versions != &response.versions => {
                        return Err(Error::OracleVersionMismatch);
                    }
                    None => expected_versions = Some(response.versions.clone()),
                    _ => {}
                }
                let mut candidates = Vec::new();
                for candidate in response.candidates {
                    if onboarding.contains(&candidate.event_id)
                        || self.state.seen.contains(&candidate.event_id)
                        || self.state.worth_judgment(candidate.event_id)
                            == Some(WorthJudgment::NotWorthSeeing)
                    {
                        continue;
                    }
                    candidates.push(candidate.event_id);
                    evidence
                        .entry(candidate.event_id)
                        .or_default()
                        .push(SourceEvidence {
                            interest_id,
                            source_note_id: *source_note_id,
                            source_rank: candidate.rank,
                            cosine_score: candidate.cosine_score,
                            versions: response.versions.clone(),
                        });
                }
                source_queues.push(SourceQueue {
                    candidates,
                    offset: 0,
                });
            }
            if !source_queues.is_empty() {
                queues.push(InterestQueue {
                    sources: source_queues,
                    next_source: 0,
                });
            }
        }

        let mut emitted = BTreeSet::new();
        let mut ordered_ids = Vec::new();
        loop {
            let mut progressed = false;
            for queue in &mut queues {
                if let Some(event_id) = queue.next_candidate(&emitted) {
                    emitted.insert(event_id);
                    ordered_ids.push(event_id);
                    progressed = true;
                }
            }
            if !progressed {
                break;
            }
        }

        let mut candidates = Vec::with_capacity(ordered_ids.len());
        for (index, event_id) in ordered_ids.into_iter().enumerate() {
            let candidate_evidence = evidence.remove(&event_id).ok_or_else(|| {
                Error::Invariant(format!(
                    "local candidate `{event_id}` has no source evidence"
                ))
            })?;
            candidates.push(LocalCandidate {
                event_id,
                local_rank: u64::try_from(index)
                    .ok()
                    .and_then(|rank| rank.checked_add(1))
                    .ok_or_else(|| {
                        Error::Invariant("local candidate rank overflowed u64".to_owned())
                    })?,
                evidence: candidate_evidence,
            });
        }
        if !evidence.is_empty() {
            return Err(Error::Invariant(
                "local ordering did not consume every candidate".to_owned(),
            ));
        }
        Ok(candidates)
    }

    fn interest_order(&self) -> Vec<InterestId> {
        let mut ordered = self.state.interests.keys().copied().collect::<Vec<_>>();
        if let Some(current) = self.state.current_interest
            && let Some(index) = ordered.iter().position(|interest| *interest == current)
        {
            ordered.remove(index);
            ordered.insert(0, current);
        }
        ordered
    }
}

impl Default for ExperimentRunner {
    fn default() -> Self {
        Self::new()
    }
}

struct SourceQueue {
    candidates: Vec<EventId>,
    offset: usize,
}

struct InterestQueue {
    sources: Vec<SourceQueue>,
    next_source: usize,
}

impl InterestQueue {
    fn next_candidate(&mut self, emitted: &BTreeSet<EventId>) -> Option<EventId> {
        for _ in 0..self.sources.len() {
            let source_index = self.next_source;
            self.next_source = (self.next_source + 1) % self.sources.len();
            let source = &mut self.sources[source_index];
            while let Some(candidate) = source.candidates.get(source.offset).copied() {
                source.offset += 1;
                if !emitted.contains(&candidate) {
                    return Some(candidate);
                }
            }
        }
        None
    }
}

fn validate_response(response: &OracleResponse) -> Result<()> {
    if response.versions.corpus.is_empty() || response.versions.retriever.is_empty() {
        return Err(Error::InvalidOracleResponse(
            "artifact versions must not be empty".to_owned(),
        ));
    }
    let mut event_ids = BTreeSet::new();
    for (index, candidate) in response.candidates.iter().enumerate() {
        let expected_rank = u64::try_from(index)
            .ok()
            .and_then(|rank| rank.checked_add(1))
            .ok_or_else(|| Error::Invariant("oracle response rank overflowed u64".to_owned()))?;
        if candidate.rank != expected_rank {
            return Err(Error::InvalidOracleResponse(format!(
                "candidate at offset {index} has rank {} instead of {expected_rank}",
                candidate.rank
            )));
        }
        if !candidate.cosine_score.is_finite() {
            return Err(Error::InvalidOracleResponse(format!(
                "candidate at rank {expected_rank} has a non-finite cosine score"
            )));
        }
        if !event_ids.insert(candidate.event_id) {
            return Err(Error::InvalidOracleResponse(format!(
                "event `{}` appears more than once",
                candidate.event_id
            )));
        }
    }
    Ok(())
}

fn validate_state(state: &ExperimentState) -> Result<()> {
    if state.schema_version != STATE_SCHEMA_VERSION {
        return Err(Error::ExperimentState(format!(
            "schema version {} is not supported",
            state.schema_version
        )));
    }
    if state.interests.is_empty() != state.current_interest.is_none() {
        return Err(Error::ExperimentState(
            "current interest does not match the stored interests".to_owned(),
        ));
    }
    if let Some(current) = state.current_interest
        && !state.interests.contains_key(&current)
    {
        return Err(Error::ExperimentState(format!(
            "current interest {} does not exist",
            current.get()
        )));
    }
    if let Some(maximum) = state.interests.keys().map(|interest| interest.get()).max()
        && state.next_interest_id <= maximum
    {
        return Err(Error::ExperimentState(
            "next interest ID does not follow existing interests".to_owned(),
        ));
    }
    for (interest_id, interest) in &state.interests {
        if interest_id.get() == 0 {
            return Err(Error::ExperimentState(
                "interest ID zero is reserved".to_owned(),
            ));
        }
        if !interest
            .positive_sources
            .is_subset(&interest.onboarding_ids)
        {
            return Err(Error::ExperimentState(format!(
                "interest {} has a positive source outside onboarding",
                interest_id.get()
            )));
        }
        if !interest.onboarding_ids.is_subset(&state.seen) {
            return Err(Error::ExperimentState(format!(
                "interest {} has an unseen onboarding event",
                interest_id.get()
            )));
        }
    }
    for event_id in state.worth_judgments.keys() {
        if !state.seen.contains(event_id) {
            return Err(Error::ExperimentState(format!(
                "judged event `{event_id}` is not marked seen"
            )));
        }
    }
    for control in &state.recommendation_controls {
        if !state.interests.contains_key(&control.interest_id) {
            return Err(Error::ExperimentState(format!(
                "recommendation control names unknown interest {}",
                control.interest_id.get()
            )));
        }
        if control.instruction.trim().is_empty() {
            return Err(Error::ExperimentState(
                "recommendation control is empty".to_owned(),
            ));
        }
    }
    Ok(())
}
