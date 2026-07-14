//! Private experiment state and deterministic local candidate ordering.

use std::cmp::Ordering;
use std::collections::{BTreeMap, BTreeSet};

use serde::{Deserialize, Serialize};

use crate::event::EventId;
use crate::oracle::{Oracle, OracleProvenance, OracleResponse, OracleVersions};
use crate::snapshot::{Error, Result};

const STATE_SCHEMA_VERSION: u32 = 4;

/// Version of the runner semantics recorded by reproducible experiment evidence.
pub const EXPERIMENT_RUNNER_VERSION: &str = "experiment-runner-v4";

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
    bootstrap_versions: OracleVersions,
    bootstrap_provenance: OracleProvenance,
    current_versions: OracleVersions,
    current_provenance: OracleProvenance,
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

    /// Return the immutable corpus and retriever used for onboarding.
    pub fn bootstrap_versions(&self) -> &OracleVersions {
        &self.bootstrap_versions
    }

    /// Return the exact provenance recorded by the onboarding query.
    pub fn bootstrap_provenance(&self) -> &OracleProvenance {
        &self.bootstrap_provenance
    }

    /// Return the oracle artifact identity currently authorized for this interest.
    pub fn current_versions(&self) -> &OracleVersions {
        &self.current_versions
    }

    /// Return the oracle provenance currently authorized for this interest.
    pub fn current_provenance(&self) -> &OracleProvenance {
        &self.current_provenance
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

/// An explicit local transition that changes whether an interest contributes candidates.
#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum RecommendationControl {
    /// Include the interest in subsequent recommendation runs.
    EnableInterest,
    /// Exclude the interest from subsequent recommendation runs.
    DisableInterest,
}

/// One applied recommendation-control transition, kept separate from worth judgments.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct RecommendationControlTransition {
    interest_id: InterestId,
    control: RecommendationControl,
}

/// One explicit transition authorizing an interest to use a different oracle artifact.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct OracleRebindTransition {
    interest_id: InterestId,
    from_versions: OracleVersions,
    from_provenance: OracleProvenance,
    to_versions: OracleVersions,
    to_provenance: OracleProvenance,
}

impl OracleRebindTransition {
    /// Return the interest whose oracle identity changed.
    pub const fn interest_id(&self) -> InterestId {
        self.interest_id
    }

    /// Return the previously authorized artifact versions.
    pub fn from_versions(&self) -> &OracleVersions {
        &self.from_versions
    }

    /// Return the newly authorized artifact versions.
    pub fn to_versions(&self) -> &OracleVersions {
        &self.to_versions
    }
}

impl RecommendationControlTransition {
    /// Return the interest changed by this transition.
    pub const fn interest_id(&self) -> InterestId {
        self.interest_id
    }

    /// Return the explicit control that was applied.
    pub const fn control(&self) -> RecommendationControl {
        self.control
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
    recommendation_controls: Vec<RecommendationControlTransition>,
    oracle_rebindings: Vec<OracleRebindTransition>,
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

    /// Return applied recommendation controls separately from worth judgments.
    pub fn recommendation_controls(&self) -> &[RecommendationControlTransition] {
        &self.recommendation_controls
    }

    /// Return every explicit oracle-identity change in application order.
    pub fn oracle_rebindings(&self) -> &[OracleRebindTransition] {
        &self.oracle_rebindings
    }

    /// Return whether an existing interest contributes to recommendation runs.
    pub fn interest_is_enabled(&self, interest_id: InterestId) -> Option<bool> {
        self.interests.contains_key(&interest_id).then(|| {
            self.recommendation_controls
                .iter()
                .filter(|transition| transition.interest_id == interest_id)
                .fold(true, |_, transition| {
                    transition.control == RecommendationControl::EnableInterest
                })
        })
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
            oracle_rebindings: Vec::new(),
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
    /// Explicit reproducibility inputs for the source-specific oracle response.
    pub provenance: OracleProvenance,
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
        let onboarding_ids = response
            .candidates
            .iter()
            .map(|candidate| candidate.event_id)
            .collect();
        self.bootstrap_with_onboarding(text, response, candidate_depth, onboarding_ids)
    }

    /// Register the locally presented subset of one unmodified bootstrap response.
    pub(crate) fn bootstrap_with_onboarding(
        &mut self,
        text: String,
        response: OracleResponse,
        candidate_depth: usize,
        onboarding_ids: BTreeSet<EventId>,
    ) -> Result<BootstrapResult> {
        validate_response(&response, candidate_depth)?;
        let response_ids = response
            .candidates
            .iter()
            .map(|candidate| candidate.event_id)
            .collect::<BTreeSet<_>>();
        if !onboarding_ids.is_subset(&response_ids) {
            return Err(Error::InvalidOracleResponse(
                "locally presented onboarding IDs are not a subset of the bootstrap response"
                    .to_owned(),
            ));
        }
        for interest in self.state.interests.values() {
            if response.versions != interest.current_versions {
                return Err(Error::OracleVersionMismatch);
            }
            if !same_oracle_identity(&response.provenance, &interest.current_provenance) {
                return Err(Error::InvalidOracleResponse(
                    "new interest provenance differs from the authorized experiment oracle"
                        .to_owned(),
                ));
            }
        }
        let interest_id = InterestId(self.state.next_interest_id);
        let next_interest_id = self
            .state
            .next_interest_id
            .checked_add(1)
            .ok_or_else(|| Error::ExperimentState("interest ID overflowed u64".to_owned()))?;
        self.state.seen.extend(onboarding_ids.iter().copied());
        self.state.interests.insert(
            interest_id,
            InterestState {
                text,
                onboarding_ids,
                positive_sources: BTreeSet::new(),
                bootstrap_versions: response.versions.clone(),
                bootstrap_provenance: response.provenance.clone(),
                current_versions: response.versions.clone(),
                current_provenance: response.provenance.clone(),
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

    /// Apply an explicit recommendation control without treating it as a worth judgment.
    pub fn apply_recommendation_control(
        &mut self,
        interest_id: InterestId,
        control: RecommendationControl,
    ) -> Result<()> {
        if !self.state.interests.contains_key(&interest_id) {
            return Err(Error::InterestNotFound(interest_id.get()));
        }
        self.state
            .recommendation_controls
            .push(RecommendationControlTransition {
                interest_id,
                control,
            });
        Ok(())
    }

    /// Explicitly authorize every interest to use one oracle identity proven by real queries.
    ///
    /// Existing onboarding choices, positive sources, judgments, and seen state remain unchanged.
    pub fn rebind_oracle(
        &mut self,
        oracle: &mut impl Oracle,
        candidate_depth: usize,
    ) -> Result<()> {
        let probes = self
            .state
            .interests
            .iter()
            .map(|(interest_id, interest)| {
                (
                    *interest_id,
                    interest.text.clone(),
                    interest
                        .positive_sources
                        .iter()
                        .copied()
                        .collect::<Vec<_>>(),
                    interest.current_versions.clone(),
                    interest.current_provenance.clone(),
                )
            })
            .collect::<Vec<_>>();
        if probes.is_empty() {
            return Err(Error::ExperimentState(
                "cannot rebind an experiment without interests".to_owned(),
            ));
        }

        let mut target: Option<(OracleVersions, OracleProvenance)> = None;
        for (_, text, sources, _, _) in &probes {
            if sources.is_empty() {
                accept_rebind_response(
                    oracle.search_text(text, candidate_depth)?,
                    candidate_depth,
                    &mut target,
                )?;
            } else {
                for source in sources {
                    accept_rebind_response(
                        oracle.similar_notes(*source, candidate_depth)?,
                        candidate_depth,
                        &mut target,
                    )?;
                }
            }
        }
        let (to_versions, to_provenance) = target.ok_or_else(|| {
            Error::Invariant("oracle rebind produced no verification response".to_owned())
        })?;
        for (interest_id, _, _, from_versions, from_provenance) in probes {
            if from_versions == to_versions
                && same_oracle_identity(&from_provenance, &to_provenance)
            {
                continue;
            }
            let interest = self
                .state
                .interests
                .get_mut(&interest_id)
                .expect("all interests were captured before oracle calls");
            interest.current_versions = to_versions.clone();
            interest.current_provenance = to_provenance.clone();
            self.state.oracle_rebindings.push(OracleRebindTransition {
                interest_id,
                from_versions,
                from_provenance,
                to_versions: to_versions.clone(),
                to_provenance: to_provenance.clone(),
            });
        }
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
        let mut candidates_by_interest: BTreeMap<InterestId, BTreeSet<EventId>> = BTreeMap::new();
        let mut expected_versions: Option<OracleVersions> = None;
        let mut expected_provenance: Option<OracleProvenance> = None;

        for interest_id in &interest_order {
            let interest = self
                .state
                .interests
                .get(interest_id)
                .expect("ordered interest exists");
            for source_note_id in &interest.positive_sources {
                let response = oracle.similar_notes(*source_note_id, candidate_depth)?;
                validate_response(&response, candidate_depth)?;
                if response.versions != interest.current_versions {
                    return Err(Error::OracleVersionMismatch);
                }
                if !same_oracle_identity(&response.provenance, &interest.current_provenance) {
                    return Err(Error::InvalidOracleResponse(format!(
                        "source response provenance differs from interest {} authorized provenance",
                        interest_id.get()
                    )));
                }
                match &expected_versions {
                    Some(versions) if versions != &response.versions => {
                        return Err(Error::OracleVersionMismatch);
                    }
                    None => expected_versions = Some(response.versions.clone()),
                    _ => {}
                }
                match &expected_provenance {
                    Some(provenance) if provenance != &response.provenance => {
                        return Err(Error::InvalidOracleResponse(
                            "provenance differs across source responses".to_owned(),
                        ));
                    }
                    None => expected_provenance = Some(response.provenance.clone()),
                    _ => {}
                }
                for candidate in response.candidates {
                    if onboarding.contains(&candidate.event_id)
                        || self.state.seen.contains(&candidate.event_id)
                        || self.state.worth_judgment(candidate.event_id)
                            == Some(WorthJudgment::NotWorthSeeing)
                    {
                        continue;
                    }
                    candidates_by_interest
                        .entry(*interest_id)
                        .or_default()
                        .insert(candidate.event_id);
                    evidence
                        .entry(candidate.event_id)
                        .or_default()
                        .push(SourceEvidence {
                            interest_id: *interest_id,
                            source_note_id: *source_note_id,
                            source_rank: candidate.rank,
                            cosine_score: candidate.cosine_score,
                            versions: response.versions.clone(),
                            provenance: response.provenance.clone(),
                        });
                }
            }
        }

        let mut queues = Vec::new();
        for interest_id in interest_order {
            let Some(candidate_ids) = candidates_by_interest.remove(&interest_id) else {
                continue;
            };
            let mut candidates = candidate_ids.into_iter().collect::<Vec<_>>();
            candidates.sort_by(|left, right| {
                compare_for_interest(
                    interest_id,
                    *left,
                    evidence.get(left).expect("candidate evidence exists"),
                    *right,
                    evidence.get(right).expect("candidate evidence exists"),
                )
            });
            queues.push(InterestQueue {
                candidates,
                offset: 0,
            });
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
            let mut candidate_evidence = evidence.remove(&event_id).ok_or_else(|| {
                Error::Invariant(format!(
                    "local candidate `{event_id}` has no source evidence"
                ))
            })?;
            candidate_evidence.sort_by(source_evidence_identity_order);
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
        let mut ordered = self
            .state
            .interests
            .keys()
            .copied()
            .filter(|interest_id| self.state.interest_is_enabled(*interest_id) == Some(true))
            .collect::<Vec<_>>();
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

struct InterestQueue {
    candidates: Vec<EventId>,
    offset: usize,
}

impl InterestQueue {
    fn next_candidate(&mut self, emitted: &BTreeSet<EventId>) -> Option<EventId> {
        while let Some(candidate) = self.candidates.get(self.offset).copied() {
            self.offset += 1;
            if !emitted.contains(&candidate) {
                return Some(candidate);
            }
        }
        None
    }
}

fn compare_for_interest(
    interest_id: InterestId,
    left_id: EventId,
    left_evidence: &[SourceEvidence],
    right_id: EventId,
    right_evidence: &[SourceEvidence],
) -> Ordering {
    let mut left = left_evidence
        .iter()
        .filter(|evidence| evidence.interest_id == interest_id)
        .collect::<Vec<_>>();
    let mut right = right_evidence
        .iter()
        .filter(|evidence| evidence.interest_id == interest_id)
        .collect::<Vec<_>>();
    left.sort_by(|left, right| source_evidence_rank_order(left, right));
    right.sort_by(|left, right| source_evidence_rank_order(left, right));

    right
        .len()
        .cmp(&left.len())
        .then_with(|| {
            left.iter()
                .zip(&right)
                .find_map(|(left, right)| {
                    let ordering = left
                        .source_rank
                        .cmp(&right.source_rank)
                        .then_with(|| right.cosine_score.total_cmp(&left.cosine_score));
                    (ordering != Ordering::Equal).then_some(ordering)
                })
                .unwrap_or(Ordering::Equal)
        })
        .then_with(|| left_id.cmp(&right_id))
}

fn source_evidence_rank_order(left: &SourceEvidence, right: &SourceEvidence) -> Ordering {
    left.source_rank
        .cmp(&right.source_rank)
        .then_with(|| right.cosine_score.total_cmp(&left.cosine_score))
        .then_with(|| left.source_note_id.cmp(&right.source_note_id))
}

fn source_evidence_identity_order(left: &SourceEvidence, right: &SourceEvidence) -> Ordering {
    left.interest_id
        .cmp(&right.interest_id)
        .then_with(|| left.source_note_id.cmp(&right.source_note_id))
        .then_with(|| left.source_rank.cmp(&right.source_rank))
        .then_with(|| right.cosine_score.total_cmp(&left.cosine_score))
}

fn validate_response(response: &OracleResponse, candidate_depth: usize) -> Result<()> {
    if response.versions.corpus.is_empty() || response.versions.retriever.is_empty() {
        return Err(Error::InvalidOracleResponse(
            "artifact versions must not be empty".to_owned(),
        ));
    }
    let expected_depth = u64::try_from(candidate_depth)
        .map_err(|_| Error::Invariant("candidate depth does not fit u64".to_owned()))?;
    if response.provenance.candidate_depth != expected_depth {
        return Err(Error::InvalidOracleResponse(format!(
            "provenance candidate depth {} differs from requested depth {expected_depth}",
            response.provenance.candidate_depth
        )));
    }
    if response.candidates.len() > candidate_depth {
        return Err(Error::InvalidOracleResponse(format!(
            "response contains {} candidates for requested depth {candidate_depth}",
            response.candidates.len()
        )));
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

fn accept_rebind_response(
    response: OracleResponse,
    candidate_depth: usize,
    target: &mut Option<(OracleVersions, OracleProvenance)>,
) -> Result<()> {
    validate_response(&response, candidate_depth)?;
    match target {
        Some((versions, provenance))
            if versions != &response.versions || provenance != &response.provenance =>
        {
            Err(Error::InvalidOracleResponse(
                "oracle rebind responses do not share one artifact identity".to_owned(),
            ))
        }
        Some(_) => Ok(()),
        None => {
            *target = Some((response.versions, response.provenance));
            Ok(())
        }
    }
}

fn same_oracle_identity(left: &OracleProvenance, right: &OracleProvenance) -> bool {
    let mut left = left.clone();
    let mut right = right.clone();
    left.candidate_depth = 0;
    right.candidate_depth = 0;
    left == right
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
    if state.next_interest_id == 0 {
        return Err(Error::ExperimentState(
            "next interest ID zero is reserved".to_owned(),
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
        if !valid_persisted_identity(&interest.bootstrap_versions, &interest.bootstrap_provenance)
            || u64::try_from(interest.onboarding_ids.len()).ok()
                > Some(interest.bootstrap_provenance.candidate_depth)
        {
            return Err(Error::ExperimentState(format!(
                "interest {} has invalid bootstrap oracle identity",
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
    }
    let mut authorized = state
        .interests
        .iter()
        .map(|(interest_id, interest)| {
            (
                *interest_id,
                (
                    interest.bootstrap_versions.clone(),
                    interest.bootstrap_provenance.clone(),
                ),
            )
        })
        .collect::<BTreeMap<_, _>>();
    for transition in &state.oracle_rebindings {
        let current = authorized.get_mut(&transition.interest_id).ok_or_else(|| {
            Error::ExperimentState(format!(
                "oracle rebind names unknown interest {}",
                transition.interest_id.get()
            ))
        })?;
        if current.0 != transition.from_versions || current.1 != transition.from_provenance {
            return Err(Error::ExperimentState(format!(
                "oracle rebind chain for interest {} is discontinuous",
                transition.interest_id.get()
            )));
        }
        if !valid_persisted_identity(&transition.to_versions, &transition.to_provenance)
            || (transition.to_versions == transition.from_versions
                && same_oracle_identity(&transition.to_provenance, &transition.from_provenance))
        {
            return Err(Error::ExperimentState(format!(
                "oracle rebind for interest {} has an invalid target identity",
                transition.interest_id.get()
            )));
        }
        *current = (
            transition.to_versions.clone(),
            transition.to_provenance.clone(),
        );
    }
    for (interest_id, interest) in &state.interests {
        let current = authorized
            .get(interest_id)
            .expect("every interest initialized an oracle identity");
        if current.0 != interest.current_versions || current.1 != interest.current_provenance {
            return Err(Error::ExperimentState(format!(
                "interest {} current oracle identity does not match its rebind history",
                interest_id.get()
            )));
        }
    }
    if let Some(first) = state.interests.values().next() {
        for interest in state.interests.values().skip(1) {
            if interest.current_versions != first.current_versions
                || !same_oracle_identity(&interest.current_provenance, &first.current_provenance)
            {
                return Err(Error::ExperimentState(
                    "interests do not share one authorized oracle identity".to_owned(),
                ));
            }
        }
    }
    Ok(())
}

fn valid_persisted_identity(versions: &OracleVersions, provenance: &OracleProvenance) -> bool {
    !versions.corpus.is_empty()
        && !versions.retriever.is_empty()
        && !provenance.source_snapshot_sha256.is_empty()
        && provenance.corpus_stage_event_count > 0
        && !provenance.corpus_stage_selection_rule.is_empty()
        && !provenance.content_preprocessing_rule.is_empty()
        && provenance.content_length_limit_tokens > 0
        && !provenance.model_id.is_empty()
        && !provenance.model_revision.is_empty()
        && provenance.embedding_dimensions > 0
        && !provenance.matrix_format.is_empty()
        && provenance.candidate_depth > 0
        && !provenance.exact_search_implementation.is_empty()
}
