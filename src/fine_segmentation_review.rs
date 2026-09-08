//! Resumable, post-hoc semantic review for the blinded HDBSCAN* packet pool.

use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::io;
use std::path::Path;

use crossterm::event::{Event, KeyCode, KeyEventKind, KeyModifiers};
use ratatui::Frame;
use ratatui::layout::{Constraint, Direction, Layout, Rect};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Borders, Paragraph, Wrap};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

use crate::reference_tui::{
    InteractiveReviewModel, MIN_HEIGHT, MIN_WIDTH, ReferenceTerminal, accent_style, centered,
    has_command_modifier, is_control_c_event, render_scrollable_panel, secondary_style,
    terminal_safe,
};
use crate::review_state::{
    acquire_session_lock, load_json, publish_json, replace_json, save_session, value_sha256,
};
use crate::snapshot::{Error, Result, io_error};

const SCHEMA_VERSION: u32 = 2;
const NOTE_SCHEMA_VERSION: u32 = 3;
const REVIEW_PROTOCOL: &str = "fine-segmentation-exp2-hdbscan-post-hoc-review-v2";
const NOTE_REVIEW_PROTOCOL: &str = "fine-segmentation-full-note-review-v3";
const REVIEW_QUESTION: &str = "Are all instances recognizable as refinements of one fine subject?";
const INSTRUCTION_QUESTION: &str = "For each packet, decide whether all instances are recognizable as refinements of one fine subject.";
const VALID_INSTRUCTION: &str =
    "Every instance is recognizable as a refinement of one fine subject.";
const INVALID_INSTRUCTION: &str =
    "No one recognizable, non-disjunctive fine subject covers every instance.";
const UNCERTAIN_INSTRUCTION: &str = "The masks do not support a confident valid/invalid decision.";
const RESPONSE_JUDGMENTS: &str = "exactly one judgment for every packet";
const RESPONSE_JUDGMENT_FIELDS: [&str; 2] = ["packet", "verdict"];
const NOTE_RESPONSE_JUDGMENTS: &str = "zero or one judgment for every packet";
const NOTE_RESPONSE_JUDGMENT_FIELDS: [&str; 3] = ["packet", "verdict", "comment"];
const REVIEW_VERDICTS: [&str; 3] = ["valid", "invalid", "uncertain"];
const REQUIRED_PACKET_COUNT: usize = 9;
const PAGE_LINES: u16 = 10;

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum FineSegmentationReviewVerdict {
    Valid,
    Invalid,
    Uncertain,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "status", rename_all = "snake_case", deny_unknown_fields)]
pub enum FineSegmentationPacketState {
    Pending,
    Skipped,
    Selected {
        proposed: FineSegmentationReviewVerdict,
        prior: Option<FineSegmentationReviewVerdict>,
    },
    SelectedAfterSkip {
        proposed: FineSegmentationReviewVerdict,
    },
    Decided {
        verdict: FineSegmentationReviewVerdict,
    },
}

impl FineSegmentationPacketState {
    fn is_resolved(&self) -> bool {
        matches!(self, Self::Decided { .. })
    }

    fn confirmed_verdict(&self) -> Option<FineSegmentationReviewVerdict> {
        match self {
            Self::Selected { prior, .. } => *prior,
            Self::Decided { verdict } => Some(*verdict),
            Self::Pending | Self::Skipped | Self::SelectedAfterSkip { .. } => None,
        }
    }

    fn proposed_verdict(&self) -> Option<FineSegmentationReviewVerdict> {
        match self {
            Self::Selected { proposed, .. } | Self::SelectedAfterSkip { proposed } => {
                Some(*proposed)
            }
            _ => None,
        }
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(untagged, deny_unknown_fields)]
pub enum FineSegmentationReviewInstance {
    Fragments {
        instance: String,
        fragments: Vec<String>,
    },
    Note {
        instance: String,
        note_id: String,
        vector_id: String,
        text: String,
        byte_spans: Vec<(usize, usize)>,
    },
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum FineSegmentationReviewScreen {
    Empty,
    Packet {
        schema_version: u32,
        packet_index: usize,
        packet_count: usize,
        packet: String,
        instances: Vec<FineSegmentationReviewInstance>,
        state: FineSegmentationPacketState,
        completed_packet_count: usize,
        current_instance_index: usize,
        comment: String,
    },
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum FineSegmentationReviewAction {
    None,
    Select(FineSegmentationReviewVerdict),
    Confirm,
    CancelSelection,
    PreviousPacket,
    NextPacket,
    SaveComment(String),
    Skip,
    Pause,
}

pub trait FineSegmentationReviewUi {
    fn review(
        &mut self,
        model: &mut FineSegmentationReviewTuiModel,
        drain_stale_input: bool,
    ) -> io::Result<FineSegmentationReviewAction>;
}

impl FineSegmentationReviewUi for ReferenceTerminal {
    fn review(
        &mut self,
        model: &mut FineSegmentationReviewTuiModel,
        drain_stale_input: bool,
    ) -> io::Result<FineSegmentationReviewAction> {
        self.run_review_model_stateful(model, drain_stale_input)
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum FineSegmentationReviewRunOutcome {
    Paused,
    Completed {
        valid: usize,
        invalid: usize,
        uncertain: usize,
    },
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct ReviewerArtifact {
    schema_version: u32,
    review_set: String,
    instructions: ReviewerInstructions,
    packets: Vec<ReviewerPacket>,
    response_contract: ReviewerResponseContract,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct ReviewerInstructions {
    question: String,
    valid: String,
    invalid: String,
    uncertain: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct ReviewerResponseContract {
    schema_version: u32,
    review_set: String,
    judgments: String,
    judgment_fields: Vec<String>,
    allowed_verdicts: Vec<String>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct ReviewerPacket {
    packet: String,
    question: String,
    verdicts: Vec<String>,
    instances: Vec<FineSegmentationReviewInstance>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct PacketSessionState {
    packet: String,
    packet_sha256: String,
    state: FineSegmentationPacketState,
    #[serde(default, skip_serializing_if = "String::is_empty")]
    comment: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct FineSegmentationReviewSession {
    schema_version: u32,
    review_protocol: String,
    review_set: String,
    reviewer_artifact_sha256: String,
    current_packet_index: usize,
    #[serde(default, skip_serializing_if = "is_zero")]
    current_instance_index: usize,
    packets: Vec<PacketSessionState>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct FineSegmentationReviewResponse {
    pub schema_version: u32,
    pub review_set: String,
    pub judgments: Vec<FineSegmentationReviewJudgment>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct FineSegmentationReviewJudgment {
    pub packet: String,
    pub verdict: FineSegmentationReviewVerdict,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub comment: Option<String>,
}

/// Run or resume a legacy v2 review or a masks-only, multi-note v3 review.
pub fn run_fine_segmentation_review(
    reviewer_path: impl AsRef<Path>,
    session_path: impl AsRef<Path>,
    response_path: impl AsRef<Path>,
    ui: &mut impl FineSegmentationReviewUi,
) -> Result<FineSegmentationReviewRunOutcome> {
    let reviewer_path = reviewer_path.as_ref();
    let session_path = session_path.as_ref();
    let response_path = response_path.as_ref();
    require_distinct_paths(reviewer_path, session_path, response_path)?;
    let (reviewer, reviewer_artifact_sha256) = load_reviewer_artifact(reviewer_path)?;
    let review_indices = reviewer.review_indices();
    let _lock = acquire_session_lock(session_path)?;
    let mut session =
        match crate::review_state::load_session::<FineSegmentationReviewSession>(session_path)? {
            Some(session) => {
                session.validate(&reviewer, &reviewer_artifact_sha256)?;
                session
            }
            None => {
                if response_path.exists() {
                    return invalid("an existing response requires its original review session");
                }
                FineSegmentationReviewSession::new(&reviewer, reviewer_artifact_sha256)?
            }
        };
    if !reviewer.is_note_review() && response_path.exists() && !session.all_complete() {
        return invalid("a complete response exists for an incomplete review session");
    }
    if reviewer.is_note_review() && response_path.exists() {
        let response: FineSegmentationReviewResponse = load_json(response_path)?;
        if response.schema_version != NOTE_SCHEMA_VERSION
            || response.review_set != reviewer.review_set
        {
            return invalid("response belongs to a different review set or protocol");
        }
    }
    // Filtering changes navigation only. Keep all artifact hashes and saved decisions.
    if !review_indices.contains(&session.current_packet_index) {
        if let Some(&index) = review_indices
            .iter()
            .find(|&&index| index >= session.current_packet_index)
            .or_else(|| review_indices.first())
        {
            session.move_to(index);
        }
    }
    persist_review(session_path, response_path, &session)?;

    let mut model =
        FineSegmentationReviewTuiModel::new(session.screen(&reviewer, &review_indices)?);
    let mut drain_stale_input = true;
    loop {
        if !reviewer.is_note_review() && session.all_complete() {
            let response = session.response()?;
            publish_json(response_path, &response)?;
            return Ok(session.completed_outcome());
        }

        model.replace_screen(session.screen(&reviewer, &review_indices)?);
        let action = ui.review(&mut model, drain_stale_input).map_err(|source| {
            io_error("run fine-segmentation review UI for", reviewer_path, source)
        })?;
        drain_stale_input = false;
        if review_indices.is_empty() && action != FineSegmentationReviewAction::Pause {
            return invalid("an empty review has no decision or browsing actions");
        }
        match action {
            FineSegmentationReviewAction::None => {
                return invalid("fine-segmentation review UI returned without an action");
            }
            FineSegmentationReviewAction::Pause => {
                if model.editing_comment {
                    session.require_note_review()?;
                    session.packets[session.current_packet_index].comment =
                        terminal_safe(&model.comment_buffer);
                }
                persist_review(session_path, response_path, &session)?;
                return Ok(if review_indices.is_empty() {
                    FineSegmentationReviewRunOutcome::Completed {
                        valid: 0,
                        invalid: 0,
                        uncertain: 0,
                    }
                } else {
                    FineSegmentationReviewRunOutcome::Paused
                });
            }
            FineSegmentationReviewAction::Select(verdict) => session.select(verdict),
            FineSegmentationReviewAction::Confirm => session.confirm(&review_indices)?,
            FineSegmentationReviewAction::CancelSelection => session.cancel_selection(),
            FineSegmentationReviewAction::PreviousPacket => session.move_previous(&review_indices),
            FineSegmentationReviewAction::NextPacket => session.move_next(&review_indices),
            FineSegmentationReviewAction::SaveComment(comment) => {
                session.require_note_review()?;
                session.packets[session.current_packet_index].comment = terminal_safe(&comment);
            }
            FineSegmentationReviewAction::Skip => {
                session.require_note_review()?;
                *session.current_state_mut() = FineSegmentationPacketState::Skipped;
                session.move_to_next_pending(&review_indices);
            }
        }
        persist_review(session_path, response_path, &session)?;
    }
}

fn persist_review(
    session_path: &Path,
    response_path: &Path,
    session: &FineSegmentationReviewSession,
) -> Result<()> {
    save_session(session_path, session)?;
    if session.schema_version == NOTE_SCHEMA_VERSION {
        replace_json(response_path, &session.response()?)?;
    }
    Ok(())
}

fn require_distinct_paths(reviewer: &Path, session: &Path, response: &Path) -> Result<()> {
    for (left, right) in [
        (reviewer, session),
        (reviewer, response),
        (session, response),
    ] {
        if left == right
            || fs::canonicalize(left)
                .ok()
                .is_some_and(|canonical| fs::canonicalize(right).ok().as_ref() == Some(&canonical))
        {
            return invalid("review input, session, and response must be different files");
        }
    }
    Ok(())
}

fn load_reviewer_artifact(path: &Path) -> Result<(ReviewerArtifact, String)> {
    let bytes = fs::read(path).map_err(|source| io_error("read", path, source))?;
    let artifact: ReviewerArtifact =
        serde_json::from_slice(&bytes).map_err(|source| Error::Manifest {
            operation: "decode fine-segmentation reviewer",
            path: path.to_owned(),
            source,
        })?;
    artifact.validate()?;
    Ok((artifact, sha256_bytes(&bytes)))
}

impl ReviewerArtifact {
    fn review_indices(&self) -> Vec<usize> {
        self.packets
            .iter()
            .enumerate()
            .filter_map(|(index, packet)| {
                if !self.is_note_review() {
                    return Some(index);
                }
                let mut notes = packet
                    .instances
                    .iter()
                    .filter_map(|instance| match instance {
                        FineSegmentationReviewInstance::Note { note_id, .. } => Some(note_id),
                        _ => None,
                    });
                let first = notes.next()?;
                notes.any(|note| note != first).then_some(index)
            })
            .collect()
    }

    fn is_note_review(&self) -> bool {
        self.schema_version == NOTE_SCHEMA_VERSION
    }

    fn protocol(&self) -> &'static str {
        if self.is_note_review() {
            NOTE_REVIEW_PROTOCOL
        } else {
            REVIEW_PROTOCOL
        }
    }

    fn validate(&self) -> Result<()> {
        if !matches!(self.schema_version, SCHEMA_VERSION | NOTE_SCHEMA_VERSION)
            || self.review_set.trim().is_empty()
        {
            return invalid("reviewer artifact schema or review-set identity is invalid");
        }
        if self.instructions.question != INSTRUCTION_QUESTION
            || self.instructions.valid != VALID_INSTRUCTION
            || self.instructions.invalid != INVALID_INSTRUCTION
            || self.instructions.uncertain != UNCERTAIN_INSTRUCTION
        {
            return invalid("reviewer artifact instructions differ from the review protocol");
        }
        let (response_judgments, response_fields): (&str, &[&str]) = if self.is_note_review() {
            (NOTE_RESPONSE_JUDGMENTS, &NOTE_RESPONSE_JUDGMENT_FIELDS)
        } else {
            (RESPONSE_JUDGMENTS, &RESPONSE_JUDGMENT_FIELDS)
        };
        if self.response_contract.schema_version != self.schema_version
            || self.response_contract.review_set != self.review_set
            || self.response_contract.judgments != response_judgments
            || self.response_contract.judgment_fields.as_slice() != response_fields
            || self.response_contract.allowed_verdicts.as_slice() != REVIEW_VERDICTS
        {
            return invalid("reviewer artifact response contract differs from the review protocol");
        }
        if !self.is_note_review() && self.packets.len() != REQUIRED_PACKET_COUNT {
            return invalid(format!(
                "reviewer artifact must contain exactly {REQUIRED_PACKET_COUNT} packets"
            ));
        }
        let mut packet_ids = BTreeSet::new();
        let mut note_texts = BTreeMap::new();
        let mut vector_evidence = BTreeMap::new();
        for (packet_index, packet) in self.packets.iter().enumerate() {
            let expected_packet = format!("P{:03}", packet_index + 1);
            if (!self.is_note_review() && packet.packet != expected_packet)
                || packet.packet.trim().is_empty()
                || !packet_ids.insert(&packet.packet)
                || packet.question != REVIEW_QUESTION
                || packet.verdicts.as_slice() != REVIEW_VERDICTS
                || packet.instances.len() < 2
            {
                return invalid(format!(
                    "reviewer packet {} has an invalid identity, protocol, or instance count",
                    packet.packet
                ));
            }
            let mut instance_ids = BTreeSet::new();
            let mut vector_ids = BTreeSet::new();
            for (instance_index, evidence) in packet.instances.iter().enumerate() {
                match evidence {
                    FineSegmentationReviewInstance::Fragments {
                        instance,
                        fragments,
                    } if !self.is_note_review() => {
                        if instance != &format!("I{:02}", instance_index + 1)
                            || fragments.is_empty()
                            || fragments.iter().any(|fragment| fragment.trim().is_empty())
                        {
                            return invalid("reviewer packet contains an invalid neutral instance");
                        }
                    }
                    FineSegmentationReviewInstance::Note {
                        instance,
                        note_id,
                        vector_id,
                        text,
                        byte_spans,
                    } if self.is_note_review() => {
                        if instance.trim().is_empty()
                            || !instance_ids.insert(instance)
                            || !is_sha256(note_id)
                            || !is_sha256(vector_id)
                            || !vector_ids.insert(vector_id)
                            || text.is_empty()
                            || byte_spans.is_empty()
                        {
                            return invalid(
                                "reviewer segment contains an invalid note or vector identity",
                            );
                        }
                        let mut previous_end = 0;
                        for &(start, end) in byte_spans {
                            if start < previous_end
                                || start >= end
                                || end > text.len()
                                || !text.is_char_boundary(start)
                                || !text.is_char_boundary(end)
                            {
                                return invalid(
                                    "reviewer mask has invalid, overlapping, or out-of-order UTF-8 byte spans",
                                );
                            }
                            previous_end = end;
                        }
                        if note_texts
                            .insert(note_id, text)
                            .is_some_and(|previous| previous != text)
                        {
                            return invalid("one note ID has conflicting original source text");
                        }
                        let source = (note_id, text, byte_spans);
                        if vector_evidence
                            .insert(vector_id, source)
                            .is_some_and(|previous| previous != source)
                        {
                            return invalid("one vector ID has conflicting note or mask evidence");
                        }
                    }
                    _ => return invalid("review instance does not match its schema version"),
                }
            }
        }
        Ok(())
    }
}

impl FineSegmentationReviewSession {
    fn new(reviewer: &ReviewerArtifact, reviewer_artifact_sha256: String) -> Result<Self> {
        let packets = reviewer
            .packets
            .iter()
            .map(|packet| {
                Ok(PacketSessionState {
                    packet: packet.packet.clone(),
                    packet_sha256: value_sha256(packet)?,
                    state: FineSegmentationPacketState::Pending,
                    comment: String::new(),
                })
            })
            .collect::<Result<Vec<_>>>()?;
        Ok(Self {
            schema_version: reviewer.schema_version,
            review_protocol: reviewer.protocol().to_owned(),
            review_set: reviewer.review_set.clone(),
            reviewer_artifact_sha256,
            current_packet_index: 0,
            current_instance_index: 0,
            packets,
        })
    }

    fn validate(&self, reviewer: &ReviewerArtifact, reviewer_sha256: &str) -> Result<()> {
        if self.schema_version != reviewer.schema_version
            || self.review_protocol != reviewer.protocol()
            || self.review_set != reviewer.review_set
            || self.reviewer_artifact_sha256 != reviewer_sha256
        {
            return invalid("review session belongs to a different reviewer artifact or protocol");
        }
        if self.packets.len() != reviewer.packets.len()
            || (!self.packets.is_empty() && self.current_packet_index >= self.packets.len())
            || (self.packets.is_empty()
                && (self.current_packet_index != 0 || self.current_instance_index != 0))
            || reviewer
                .packets
                .get(self.current_packet_index)
                .is_some_and(|packet| self.current_instance_index >= packet.instances.len())
        {
            return invalid("review session has an invalid packet count or position");
        }
        for (stored, packet) in self.packets.iter().zip(&reviewer.packets) {
            if stored.packet != packet.packet || stored.packet_sha256 != value_sha256(packet)? {
                return invalid(
                    "review session packet identity differs from the reviewer artifact",
                );
            }
            if !reviewer.is_note_review()
                && (!stored.comment.is_empty()
                    || matches!(
                        stored.state,
                        FineSegmentationPacketState::Skipped
                            | FineSegmentationPacketState::SelectedAfterSkip { .. }
                    )
                    || self.current_instance_index != 0)
            {
                return invalid("legacy review session contains complete-note review state");
            }
        }
        Ok(())
    }

    fn current_state(&self) -> &FineSegmentationPacketState {
        &self.packets[self.current_packet_index].state
    }

    fn require_note_review(&self) -> Result<()> {
        if self.schema_version != NOTE_SCHEMA_VERSION || self.packets.is_empty() {
            return invalid("this action requires a nonempty complete-note review");
        }
        Ok(())
    }

    fn current_state_mut(&mut self) -> &mut FineSegmentationPacketState {
        &mut self.packets[self.current_packet_index].state
    }

    fn completed_count(&self, review_indices: &[usize]) -> usize {
        review_indices
            .iter()
            .filter(|&&index| self.packets[index].state.confirmed_verdict().is_some())
            .count()
    }

    fn all_complete(&self) -> bool {
        self.packets.iter().all(|packet| packet.state.is_resolved())
    }

    fn select(&mut self, verdict: FineSegmentationReviewVerdict) {
        if matches!(
            self.current_state(),
            FineSegmentationPacketState::Skipped
                | FineSegmentationPacketState::SelectedAfterSkip { .. }
        ) {
            *self.current_state_mut() =
                FineSegmentationPacketState::SelectedAfterSkip { proposed: verdict };
            return;
        }
        let prior = match self.current_state() {
            FineSegmentationPacketState::Pending
            | FineSegmentationPacketState::Skipped
            | FineSegmentationPacketState::SelectedAfterSkip { .. } => None,
            FineSegmentationPacketState::Selected { prior, .. } => *prior,
            FineSegmentationPacketState::Decided { verdict } => Some(*verdict),
        };
        *self.current_state_mut() = FineSegmentationPacketState::Selected {
            proposed: verdict,
            prior,
        };
    }

    fn confirm(&mut self, review_indices: &[usize]) -> Result<()> {
        let Some(verdict) = self.current_state().proposed_verdict() else {
            return invalid("only a selected verdict can be confirmed");
        };
        *self.current_state_mut() = FineSegmentationPacketState::Decided { verdict };
        self.move_to_next_pending(review_indices);
        Ok(())
    }

    fn cancel_selection(&mut self) {
        let replacement = match self.current_state() {
            FineSegmentationPacketState::SelectedAfterSkip { .. } => {
                Some(FineSegmentationPacketState::Skipped)
            }
            FineSegmentationPacketState::Selected {
                prior: Some(verdict),
                ..
            } => Some(FineSegmentationPacketState::Decided { verdict: *verdict }),
            FineSegmentationPacketState::Selected { prior: None, .. } => {
                Some(FineSegmentationPacketState::Pending)
            }
            _ => None,
        };
        if let Some(replacement) = replacement {
            *self.current_state_mut() = replacement;
        }
    }

    fn move_previous(&mut self, review_indices: &[usize]) {
        if let Some(&index) = review_indices
            .iter()
            .rev()
            .find(|&&index| index < self.current_packet_index)
        {
            self.move_to(index);
        }
    }

    fn move_next(&mut self, review_indices: &[usize]) {
        if let Some(&index) = review_indices
            .iter()
            .find(|&&index| index > self.current_packet_index)
        {
            self.move_to(index);
        }
    }

    fn move_to(&mut self, index: usize) {
        if self.current_packet_index != index {
            self.current_packet_index = index;
            self.current_instance_index = 0;
        }
    }

    fn move_to_next_pending(&mut self, review_indices: &[usize]) {
        let Some(position) = review_indices
            .iter()
            .position(|&index| index == self.current_packet_index)
        else {
            return;
        };
        for offset in 1..=review_indices.len() {
            let candidate = review_indices[(position + offset) % review_indices.len()];
            if matches!(
                self.packets[candidate].state,
                FineSegmentationPacketState::Pending
                    | FineSegmentationPacketState::Selected { .. }
                    | FineSegmentationPacketState::SelectedAfterSkip { .. }
            ) {
                self.move_to(candidate);
                return;
            }
        }
    }

    fn screen(
        &self,
        reviewer: &ReviewerArtifact,
        review_indices: &[usize],
    ) -> Result<FineSegmentationReviewScreen> {
        if review_indices.is_empty() {
            return Ok(FineSegmentationReviewScreen::Empty);
        }
        let packet = reviewer
            .packets
            .get(self.current_packet_index)
            .ok_or_else(|| {
                Error::ExperimentState("current reviewer packet is absent".to_owned())
            })?;
        let completed = self.completed_count(review_indices);
        let packet_index = review_indices
            .iter()
            .position(|&index| index == self.current_packet_index)
            .ok_or_else(|| {
                Error::ExperimentState("current reviewer packet is hidden".to_owned())
            })?;
        Ok(FineSegmentationReviewScreen::Packet {
            schema_version: self.schema_version,
            packet_index,
            packet_count: review_indices.len(),
            packet: packet.packet.clone(),
            instances: packet.instances.clone(),
            state: self.current_state().clone(),
            completed_packet_count: completed,
            current_instance_index: self.current_instance_index,
            comment: self.packets[self.current_packet_index].comment.clone(),
        })
    }

    fn response(&self) -> Result<FineSegmentationReviewResponse> {
        if self.schema_version == SCHEMA_VERSION && !self.all_complete() {
            return invalid("an incomplete review cannot publish a response");
        }
        let judgments = self
            .packets
            .iter()
            .filter_map(|packet| {
                packet
                    .state
                    .confirmed_verdict()
                    .map(|verdict| FineSegmentationReviewJudgment {
                        packet: packet.packet.clone(),
                        verdict,
                        comment: (self.schema_version == NOTE_SCHEMA_VERSION)
                            .then(|| packet.comment.clone()),
                    })
            })
            .collect();
        Ok(FineSegmentationReviewResponse {
            schema_version: self.schema_version,
            review_set: self.review_set.clone(),
            judgments,
        })
    }

    fn completed_outcome(&self) -> FineSegmentationReviewRunOutcome {
        let valid = self
            .packets
            .iter()
            .filter(|packet| {
                packet.state.confirmed_verdict() == Some(FineSegmentationReviewVerdict::Valid)
            })
            .count();
        let invalid = self
            .packets
            .iter()
            .filter(|packet| {
                packet.state.confirmed_verdict() == Some(FineSegmentationReviewVerdict::Invalid)
            })
            .count();
        let uncertain = self
            .packets
            .iter()
            .filter(|packet| {
                packet.state.confirmed_verdict() == Some(FineSegmentationReviewVerdict::Uncertain)
            })
            .count();
        FineSegmentationReviewRunOutcome::Completed {
            valid,
            invalid,
            uncertain,
        }
    }
}

fn sha256_bytes(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}

fn is_zero(value: &usize) -> bool {
    *value == 0
}

fn is_sha256(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

fn invalid<T>(message: impl Into<String>) -> Result<T> {
    Err(Error::ExperimentState(message.into()))
}

#[derive(Clone, Debug)]
pub struct FineSegmentationReviewTuiModel {
    screen: FineSegmentationReviewScreen,
    instance_scroll: u16,
    half_page_lines: u16,
    interaction_enabled: bool,
    editing_comment: bool,
    comment_buffer: String,
}

impl FineSegmentationReviewTuiModel {
    pub fn new(screen: FineSegmentationReviewScreen) -> Self {
        let screen = sanitize_screen(screen);
        Self {
            screen,
            instance_scroll: 0,
            half_page_lines: 1,
            interaction_enabled: true,
            editing_comment: false,
            comment_buffer: String::new(),
        }
    }

    pub fn screen(&self) -> &FineSegmentationReviewScreen {
        &self.screen
    }

    pub fn replace_screen(&mut self, screen: FineSegmentationReviewScreen) {
        let screen = sanitize_screen(screen);
        let position_changed = screen_position(&self.screen) != screen_position(&screen);
        if position_changed {
            self.instance_scroll = 0;
            self.editing_comment = false;
            self.comment_buffer.clear();
        }
        self.screen = screen;
    }

    pub fn handle_event(&mut self, event: Event) -> FineSegmentationReviewAction {
        if is_control_c_event(&event) {
            return FineSegmentationReviewAction::Pause;
        }
        if !self.interaction_enabled {
            return FineSegmentationReviewAction::None;
        }
        if self.editing_comment {
            return self.handle_comment_event(event);
        }
        let Event::Key(key) = &event else {
            return FineSegmentationReviewAction::None;
        };
        if key.kind != KeyEventKind::Press {
            return FineSegmentationReviewAction::None;
        }
        if key.modifiers == KeyModifiers::CONTROL {
            match key.code {
                KeyCode::Char('d' | 'D') => {
                    self.instance_scroll =
                        self.instance_scroll.saturating_add(self.half_page_lines);
                }
                KeyCode::Char('u' | 'U') => {
                    self.instance_scroll =
                        self.instance_scroll.saturating_sub(self.half_page_lines);
                }
                _ => {}
            }
            return FineSegmentationReviewAction::None;
        }
        if has_command_modifier(key.modifiers) {
            return FineSegmentationReviewAction::None;
        }
        match &self.screen {
            FineSegmentationReviewScreen::Empty => match key.code {
                KeyCode::Enter | KeyCode::Esc | KeyCode::Char('q' | 'Q') => {
                    FineSegmentationReviewAction::Pause
                }
                _ => FineSegmentationReviewAction::None,
            },
            FineSegmentationReviewScreen::Packet {
                state,
                schema_version,
                comment,
                ..
            } => match key.code {
                KeyCode::Char('c' | 'C') if *schema_version == NOTE_SCHEMA_VERSION => {
                    self.comment_buffer.clone_from(comment);
                    self.editing_comment = true;
                    FineSegmentationReviewAction::None
                }
                KeyCode::Char('s' | 'S') if *schema_version == NOTE_SCHEMA_VERSION => {
                    FineSegmentationReviewAction::Skip
                }
                KeyCode::Char('v' | 'V') => {
                    FineSegmentationReviewAction::Select(FineSegmentationReviewVerdict::Valid)
                }
                KeyCode::Char('i' | 'I') => {
                    FineSegmentationReviewAction::Select(FineSegmentationReviewVerdict::Invalid)
                }
                KeyCode::Char('u' | 'U') => {
                    FineSegmentationReviewAction::Select(FineSegmentationReviewVerdict::Uncertain)
                }
                KeyCode::Enter if state.proposed_verdict().is_some() => {
                    FineSegmentationReviewAction::Confirm
                }
                KeyCode::Esc if state.proposed_verdict().is_some() => {
                    FineSegmentationReviewAction::CancelSelection
                }
                KeyCode::Left | KeyCode::Char('p' | 'P') => {
                    FineSegmentationReviewAction::PreviousPacket
                }
                KeyCode::Right | KeyCode::Char('n' | 'N') => {
                    FineSegmentationReviewAction::NextPacket
                }
                KeyCode::Down | KeyCode::Char('j' | 'J') => {
                    self.instance_scroll = self.instance_scroll.saturating_add(1);
                    FineSegmentationReviewAction::None
                }
                KeyCode::Up | KeyCode::Char('k' | 'K') => {
                    self.instance_scroll = self.instance_scroll.saturating_sub(1);
                    FineSegmentationReviewAction::None
                }
                KeyCode::PageDown => {
                    self.instance_scroll = self.instance_scroll.saturating_add(PAGE_LINES);
                    FineSegmentationReviewAction::None
                }
                KeyCode::PageUp => {
                    self.instance_scroll = self.instance_scroll.saturating_sub(PAGE_LINES);
                    FineSegmentationReviewAction::None
                }
                KeyCode::Home => {
                    self.instance_scroll = 0;
                    FineSegmentationReviewAction::None
                }
                _ => FineSegmentationReviewAction::None,
            },
        }
    }

    fn handle_comment_event(&mut self, event: Event) -> FineSegmentationReviewAction {
        match event {
            Event::Paste(text) => self.comment_buffer.push_str(&terminal_safe(&text)),
            Event::Key(key) if key.kind == KeyEventKind::Press => match key.code {
                KeyCode::Enter => {
                    self.editing_comment = false;
                    return FineSegmentationReviewAction::SaveComment(self.comment_buffer.clone());
                }
                KeyCode::Esc => {
                    self.editing_comment = false;
                    self.comment_buffer.clear();
                }
                KeyCode::Backspace if !has_command_modifier(key.modifiers) => {
                    self.comment_buffer.pop();
                }
                KeyCode::Char(character) if !has_command_modifier(key.modifiers) => {
                    self.comment_buffer.push(character)
                }
                _ => {}
            },
            _ => {}
        }
        FineSegmentationReviewAction::None
    }

    pub fn render(&mut self, frame: &mut Frame<'_>) {
        let terminal_area = frame.area();
        self.interaction_enabled =
            terminal_area.width >= MIN_WIDTH && terminal_area.height >= MIN_HEIGHT;
        if !self.interaction_enabled {
            frame.render_widget(
                Paragraph::new(format!(
                    "Terminal too small\nResize to at least {MIN_WIDTH} × {MIN_HEIGHT}."
                ))
                .block(
                    Block::default()
                        .borders(Borders::ALL)
                        .title("Semantic review"),
                ),
                terminal_area,
            );
            return;
        }
        let area = centered(terminal_area);
        match self.screen.clone() {
            FineSegmentationReviewScreen::Empty => {
                frame.render_widget(Paragraph::new("No segments to review\n\nOnly segments containing at least two distinct notes are shown. Stored evidence and decisions are unchanged.\n\n[Enter / Ctrl-C] Exit")
                    .wrap(Wrap { trim: false })
                    .block(Block::default().borders(Borders::ALL).title("Fine segmentation review")), area);
            }
            FineSegmentationReviewScreen::Packet {
                schema_version,
                packet_index,
                packet_count,
                packet,
                instances,
                state,
                completed_packet_count,
                comment,
                ..
            } => self.render_packet(
                frame,
                area,
                packet_index,
                packet_count,
                &packet,
                &instances,
                &state,
                completed_packet_count,
                schema_version == NOTE_SCHEMA_VERSION,
                &comment,
            ),
        }
    }

    #[allow(clippy::too_many_arguments)]
    fn render_packet(
        &mut self,
        frame: &mut Frame<'_>,
        area: Rect,
        packet_index: usize,
        packet_count: usize,
        packet: &str,
        instances: &[FineSegmentationReviewInstance],
        state: &FineSegmentationPacketState,
        completed: usize,
        note_review: bool,
        comment: &str,
    ) {
        let rows = Layout::default()
            .direction(Direction::Vertical)
            .constraints([
                Constraint::Length(1),
                Constraint::Length(2),
                Constraint::Length(4),
                Constraint::Min(6),
                Constraint::Length(if note_review { 4 } else { 2 }),
                Constraint::Length(if note_review { 6 } else { 5 }),
            ])
            .split(area);
        frame.render_widget(
            Paragraph::new(format!(
                "{} {} of {packet_count} · {completed} reviewed · {packet}",
                if note_review { "Segment" } else { "Packet" },
                packet_index + 1
            ))
            .style(secondary_style()),
            rows[0],
        );
        frame.render_widget(
            Paragraph::new(REVIEW_QUESTION)
                .style(accent_style())
                .wrap(Wrap { trim: false }),
            rows[1],
        );
        self.render_verdict_definitions(frame, rows[2]);
        let instance_title = if note_review {
            format!("Masks · {}", instances.len())
        } else {
            "Instances".to_owned()
        };
        render_scrollable_panel(
            frame,
            rows[3],
            &instance_title,
            &render_instances(instances),
            &mut self.instance_scroll,
            &mut self.half_page_lines,
            false,
        );
        let status = if self.editing_comment {
            format!(
                "Comment: {}\n[Enter] Save comment · [Esc] Cancel",
                self.comment_buffer
            )
        } else if note_review {
            format!(
                "{}\nComment: {}",
                packet_status(state),
                if comment.is_empty() {
                    "(optional)"
                } else {
                    comment
                }
            )
        } else {
            packet_status(state)
        };
        frame.render_widget(Paragraph::new(status).wrap(Wrap { trim: false }), rows[4]);
        self.render_packet_controls(frame, rows[5], state, note_review);
    }

    fn render_verdict_definitions(&self, frame: &mut Frame<'_>, area: Rect) {
        frame.render_widget(
            Paragraph::new(vec![
                Line::from(vec![
                    Span::styled("Valid = ", accent_style()),
                    Span::raw("one recognizable non-disjunctive fine subject"),
                ]),
                Line::raw("        covers every instance"),
                Line::from(vec![
                    Span::styled("Invalid = ", accent_style()),
                    Span::raw("no such subject"),
                ]),
                Line::from(vec![
                    Span::styled("Uncertain = ", accent_style()),
                    Span::raw("masks do not support a confident decision"),
                ]),
            ]),
            area,
        );
    }

    fn render_packet_controls(
        &self,
        frame: &mut Frame<'_>,
        area: Rect,
        state: &FineSegmentationPacketState,
        note_review: bool,
    ) {
        let selected = |verdict| state.proposed_verdict() == Some(verdict);
        let verdict = |key, label, choice| {
            let style = if selected(choice) {
                accent_style()
            } else {
                ratatui::style::Style::default()
            };
            vec![
                Span::styled(if selected(choice) { "▶ " } else { "  " }, style),
                Span::styled(key, accent_style()),
                Span::styled(format!(" {label}  "), style),
            ]
        };
        let mut choices = Vec::new();
        choices.extend(verdict(
            "[V]",
            "Valid",
            FineSegmentationReviewVerdict::Valid,
        ));
        choices.extend(verdict(
            "[I]",
            "Invalid",
            FineSegmentationReviewVerdict::Invalid,
        ));
        choices.extend(verdict(
            "[U]",
            "Uncertain",
            FineSegmentationReviewVerdict::Uncertain,
        ));
        let confirm = if state.proposed_verdict().is_some() {
            "Confirm selection"
        } else {
            "Confirm after V/I/U"
        };
        let mut controls = vec![
            Line::from(choices),
            Line::from(vec![
                Span::styled("[Enter]", accent_style()),
                Span::styled(format!(" {confirm}  "), secondary_style()),
                Span::styled("[Esc]", accent_style()),
                Span::styled(" Cancel selection", secondary_style()),
            ]),
            Line::from(vec![
                Span::styled("[←/→]", accent_style()),
                Span::styled(
                    if note_review {
                        " Previous/next segment  "
                    } else {
                        " Previous/next packet  "
                    },
                    secondary_style(),
                ),
                Span::styled("[↑/↓]", accent_style()),
                Span::styled(" Scroll", secondary_style()),
            ]),
            Line::from(vec![
                Span::styled("[Ctrl-D/U]", accent_style()),
                Span::styled(" Half-page  ", secondary_style()),
                Span::styled("[Ctrl-C]", accent_style()),
                Span::styled(" Save/exit", secondary_style()),
            ]),
        ];
        if note_review {
            controls.push(Line::from(vec![
                Span::styled("[C]", accent_style()),
                Span::styled(" Comment  ", secondary_style()),
                Span::styled("[S]", accent_style()),
                Span::styled(" Skip", secondary_style()),
            ]));
        }
        frame.render_widget(Paragraph::new(controls), area);
    }
}

impl InteractiveReviewModel for FineSegmentationReviewTuiModel {
    type Action = FineSegmentationReviewAction;

    fn none_action() -> Self::Action {
        FineSegmentationReviewAction::None
    }

    fn pause_action() -> Self::Action {
        FineSegmentationReviewAction::Pause
    }

    fn handle_terminal_event(&mut self, event: Event) -> Self::Action {
        self.handle_event(event)
    }

    fn render_terminal(&mut self, frame: &mut Frame<'_>) {
        self.render(frame);
    }
}

fn sanitize_screen(mut screen: FineSegmentationReviewScreen) -> FineSegmentationReviewScreen {
    if let FineSegmentationReviewScreen::Packet {
        packet,
        instances,
        comment,
        ..
    } = &mut screen
    {
        *packet = terminal_safe(packet).replace('\n', " ");
        *comment = terminal_safe(comment);
        for evidence in instances {
            match evidence {
                FineSegmentationReviewInstance::Fragments {
                    instance,
                    fragments,
                } => {
                    *instance = terminal_safe(instance).replace('\n', " ");
                    for fragment in fragments {
                        *fragment = terminal_safe(fragment);
                    }
                }
                FineSegmentationReviewInstance::Note { instance, .. } => {
                    *instance = terminal_safe(instance).replace('\n', " ");
                    // Preserve the exact original text until its UTF-8 mask is rendered.
                    // Sanitizing it here would shift byte offsets (for example, tabs).
                }
            }
        }
    }
    screen
}

fn screen_position(screen: &FineSegmentationReviewScreen) -> Option<(usize, usize)> {
    match screen {
        FineSegmentationReviewScreen::Empty => None,
        FineSegmentationReviewScreen::Packet {
            packet_index,
            current_instance_index,
            ..
        } => Some((*packet_index, *current_instance_index)),
    }
}

fn render_instances(instances: &[FineSegmentationReviewInstance]) -> String {
    instances
        .iter()
        .enumerate()
        .map(|(index, instance)| {
            if let FineSegmentationReviewInstance::Note {
                instance,
                text,
                byte_spans,
                ..
            } = instance
            {
                let fragments = byte_spans
                    .iter()
                    .map(|&(start, end)| format!("⟦{}⟧", terminal_safe(&text[start..end])))
                    .collect::<Vec<_>>()
                    .join(" ");
                return format!("{instance}  {fragments}");
            }
            let FineSegmentationReviewInstance::Fragments { fragments, .. } = instance else {
                return String::new();
            };
            let prefix = format!("{}. ", index + 1);
            let continuation = " ".repeat(prefix.chars().count());
            fragments
                .iter()
                .enumerate()
                .map(|(fragment_index, fragment)| {
                    format!(
                        "{}{}",
                        if fragment_index == 0 {
                            prefix.as_str()
                        } else {
                            continuation.as_str()
                        },
                        fragment
                    )
                })
                .collect::<Vec<_>>()
                .join("\n")
        })
        .collect::<Vec<_>>()
        .join("\n\n")
}

fn packet_status(state: &FineSegmentationPacketState) -> String {
    match state {
        FineSegmentationPacketState::Pending => "Decision: pending".to_owned(),
        FineSegmentationPacketState::Skipped => "Decision: skipped (no verdict)".to_owned(),
        FineSegmentationPacketState::SelectedAfterSkip { proposed } => format!(
            "Decision: {} selected; Enter confirms, Esc keeps skipped",
            verdict_name(*proposed)
        ),
        FineSegmentationPacketState::Selected {
            proposed,
            prior: Some(prior),
        } => format!(
            "Decision: {} selected to replace stored {}; Enter confirms, Esc keeps {}",
            verdict_name(*proposed),
            verdict_name(*prior),
            verdict_name(*prior),
        ),
        FineSegmentationPacketState::Selected {
            proposed,
            prior: None,
        } => format!(
            "Decision: {} selected; press Enter to confirm",
            verdict_name(*proposed)
        ),
        FineSegmentationPacketState::Decided { verdict } => {
            format!("Stored decision: {}", verdict_name(*verdict))
        }
    }
}

fn verdict_name(verdict: FineSegmentationReviewVerdict) -> &'static str {
    match verdict {
        FineSegmentationReviewVerdict::Valid => "valid",
        FineSegmentationReviewVerdict::Invalid => "invalid",
        FineSegmentationReviewVerdict::Uncertain => "uncertain",
    }
}
