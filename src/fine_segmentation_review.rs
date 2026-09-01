//! Resumable, post-hoc semantic review for the blinded HDBSCAN* packet pool.

use std::collections::BTreeSet;
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
use crate::review_state::{acquire_session_lock, publish_json, save_session, value_sha256};
use crate::snapshot::{Error, Result, io_error};

const SCHEMA_VERSION: u32 = 1;
const REVIEW_PROTOCOL: &str = "fine-segmentation-exp2-hdbscan-post-hoc-review-v1";
const REVIEW_QUESTION: &str = "Are all instances recognizable as refinements of one fine subject?";
const INSTRUCTION_QUESTION: &str = "For each packet, decide whether all instances are recognizable as refinements of one fine subject.";
const VALID_INSTRUCTION: &str =
    "Every instance is recognizable as a refinement of one fine subject.";
const INVALID_INSTRUCTION: &str =
    "No one recognizable, non-disjunctive fine subject covers every instance.";
const UNCERTAIN_INSTRUCTION: &str = "The masks do not support a confident valid/invalid decision.";
const RESPONSE_JUDGMENTS: &str = "exactly one judgment for every packet";
const RESPONSE_JUDGMENT_FIELDS: [&str; 2] = ["packet", "verdict"];
const REVIEW_VERDICTS: [&str; 3] = ["valid", "invalid", "uncertain"];
const REQUIRED_PACKET_COUNT: usize = 177;
const BREAK_INTERVAL: usize = 20;
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
    Selected {
        proposed: FineSegmentationReviewVerdict,
        prior: Option<FineSegmentationReviewVerdict>,
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
            Self::Pending => None,
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct FineSegmentationReviewInstance {
    pub instance: String,
    pub fragments: Vec<String>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum FineSegmentationReviewScreen {
    Packet {
        packet_index: usize,
        packet_count: usize,
        packet: String,
        instances: Vec<FineSegmentationReviewInstance>,
        state: FineSegmentationPacketState,
        completed_packet_count: usize,
        break_in: usize,
    },
    Break {
        completed_packet_count: usize,
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
    ContinueBreak,
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
    instances: Vec<ReviewerInstance>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct ReviewerInstance {
    instance: String,
    fragments: Vec<String>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct PacketSessionState {
    packet: String,
    packet_sha256: String,
    state: FineSegmentationPacketState,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct BreakCheckpoint {
    after_packets: usize,
    continued: bool,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct FineSegmentationReviewSession {
    schema_version: u32,
    review_protocol: String,
    review_set: String,
    reviewer_artifact_sha256: String,
    current_packet_index: usize,
    packets: Vec<PacketSessionState>,
    break_checkpoints: Vec<BreakCheckpoint>,
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
}

/// Run or resume the complete 177-packet post-hoc review.
pub fn run_fine_segmentation_review(
    reviewer_path: impl AsRef<Path>,
    session_path: impl AsRef<Path>,
    response_path: impl AsRef<Path>,
    ui: &mut impl FineSegmentationReviewUi,
) -> Result<FineSegmentationReviewRunOutcome> {
    let reviewer_path = reviewer_path.as_ref();
    let session_path = session_path.as_ref();
    let response_path = response_path.as_ref();
    let (reviewer, reviewer_artifact_sha256) = load_reviewer_artifact(reviewer_path)?;
    let _lock = acquire_session_lock(session_path)?;
    let mut session =
        match crate::review_state::load_session::<FineSegmentationReviewSession>(session_path)? {
            Some(session) => {
                session.validate(&reviewer, &reviewer_artifact_sha256)?;
                session
            }
            None => FineSegmentationReviewSession::new(&reviewer, reviewer_artifact_sha256)?,
        };
    if response_path.exists() && !session.all_complete() {
        return invalid("a complete response exists for an incomplete review session");
    }
    save_session(session_path, &session)?;

    let mut model = FineSegmentationReviewTuiModel::new(FineSegmentationReviewScreen::Break {
        completed_packet_count: 0,
    });
    let mut drain_stale_input = true;
    loop {
        if session.all_complete() {
            let response = session.response()?;
            publish_json(response_path, &response)?;
            return Ok(session.completed_outcome());
        }

        if let Some((checkpoint_index, created)) = session.due_break_checkpoint() {
            if created {
                save_session(session_path, &session)?;
            }
            model.replace_screen(FineSegmentationReviewScreen::Break {
                completed_packet_count: session.completed_count(),
            });
            let action = ui.review(&mut model, drain_stale_input).map_err(|source| {
                io_error("run fine-segmentation review UI for", reviewer_path, source)
            })?;
            drain_stale_input = false;
            match action {
                FineSegmentationReviewAction::ContinueBreak => {
                    session.break_checkpoints[checkpoint_index].continued = true;
                    save_session(session_path, &session)?;
                }
                FineSegmentationReviewAction::Pause => {
                    save_session(session_path, &session)?;
                    return Ok(FineSegmentationReviewRunOutcome::Paused);
                }
                FineSegmentationReviewAction::None => {
                    return invalid("fine-segmentation break UI returned without an action");
                }
                _ => return invalid("fine-segmentation break UI returned an invalid action"),
            }
            continue;
        }

        model.replace_screen(session.screen(&reviewer)?);
        let action = ui.review(&mut model, drain_stale_input).map_err(|source| {
            io_error("run fine-segmentation review UI for", reviewer_path, source)
        })?;
        drain_stale_input = false;
        match action {
            FineSegmentationReviewAction::None => {
                return invalid("fine-segmentation review UI returned without an action");
            }
            FineSegmentationReviewAction::Pause => {
                save_session(session_path, &session)?;
                return Ok(FineSegmentationReviewRunOutcome::Paused);
            }
            FineSegmentationReviewAction::Select(verdict) => session.select(verdict),
            FineSegmentationReviewAction::Confirm => session.confirm()?,
            FineSegmentationReviewAction::CancelSelection => session.cancel_selection(),
            FineSegmentationReviewAction::PreviousPacket => session.move_previous(),
            FineSegmentationReviewAction::NextPacket => session.move_next(),
            FineSegmentationReviewAction::ContinueBreak => {
                return invalid("packet review UI continued a break that was not due");
            }
        }
        save_session(session_path, &session)?;
    }
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
    fn validate(&self) -> Result<()> {
        if self.schema_version != SCHEMA_VERSION || self.review_set.trim().is_empty() {
            return invalid("reviewer artifact schema or review-set identity is invalid");
        }
        if self.instructions.question != INSTRUCTION_QUESTION
            || self.instructions.valid != VALID_INSTRUCTION
            || self.instructions.invalid != INVALID_INSTRUCTION
            || self.instructions.uncertain != UNCERTAIN_INSTRUCTION
        {
            return invalid("reviewer artifact instructions differ from the review protocol");
        }
        if self.response_contract.schema_version != SCHEMA_VERSION
            || self.response_contract.review_set != self.review_set
            || self.response_contract.judgments != RESPONSE_JUDGMENTS
            || self.response_contract.judgment_fields.as_slice() != RESPONSE_JUDGMENT_FIELDS
            || self.response_contract.allowed_verdicts.as_slice() != REVIEW_VERDICTS
        {
            return invalid("reviewer artifact response contract differs from the review protocol");
        }
        if self.packets.len() != REQUIRED_PACKET_COUNT {
            return invalid(format!(
                "reviewer artifact must contain exactly {REQUIRED_PACKET_COUNT} packets"
            ));
        }
        for (packet_index, packet) in self.packets.iter().enumerate() {
            let expected_packet = format!("P{:03}", packet_index + 1);
            if packet.packet != expected_packet
                || packet.question != REVIEW_QUESTION
                || packet.verdicts.as_slice() != REVIEW_VERDICTS
                || packet.instances.len() < 2
            {
                return invalid(format!(
                    "reviewer packet {} has an invalid identity, protocol, or instance count",
                    packet.packet
                ));
            }
            for (instance_index, instance) in packet.instances.iter().enumerate() {
                if instance.instance != format!("I{:02}", instance_index + 1)
                    || instance.fragments.is_empty()
                    || instance
                        .fragments
                        .iter()
                        .any(|fragment| fragment.trim().is_empty())
                {
                    return invalid(format!(
                        "reviewer packet {} contains an invalid neutral instance",
                        packet.packet
                    ));
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
                })
            })
            .collect::<Result<Vec<_>>>()?;
        Ok(Self {
            schema_version: SCHEMA_VERSION,
            review_protocol: REVIEW_PROTOCOL.to_owned(),
            review_set: reviewer.review_set.clone(),
            reviewer_artifact_sha256,
            current_packet_index: 0,
            packets,
            break_checkpoints: Vec::new(),
        })
    }

    fn validate(&self, reviewer: &ReviewerArtifact, reviewer_sha256: &str) -> Result<()> {
        if self.schema_version != SCHEMA_VERSION
            || self.review_protocol != REVIEW_PROTOCOL
            || self.review_set != reviewer.review_set
            || self.reviewer_artifact_sha256 != reviewer_sha256
        {
            return invalid("review session belongs to a different reviewer artifact or protocol");
        }
        if self.packets.len() != reviewer.packets.len()
            || self.current_packet_index >= self.packets.len()
        {
            return invalid("review session has an invalid packet count or position");
        }
        for (stored, packet) in self.packets.iter().zip(&reviewer.packets) {
            if stored.packet != packet.packet || stored.packet_sha256 != value_sha256(packet)? {
                return invalid(
                    "review session packet identity differs from the reviewer artifact",
                );
            }
        }
        let mut seen_breaks = BTreeSet::new();
        for checkpoint in &self.break_checkpoints {
            if checkpoint.after_packets == 0
                || !checkpoint.after_packets.is_multiple_of(BREAK_INTERVAL)
                || checkpoint.after_packets >= REQUIRED_PACKET_COUNT
                || !seen_breaks.insert(checkpoint.after_packets)
            {
                return invalid("review session contains an invalid break checkpoint");
            }
        }
        Ok(())
    }

    fn current_state(&self) -> &FineSegmentationPacketState {
        &self.packets[self.current_packet_index].state
    }

    fn current_state_mut(&mut self) -> &mut FineSegmentationPacketState {
        &mut self.packets[self.current_packet_index].state
    }

    fn completed_count(&self) -> usize {
        self.packets
            .iter()
            .filter(|packet| packet.state.confirmed_verdict().is_some())
            .count()
    }

    fn all_complete(&self) -> bool {
        self.packets.iter().all(|packet| packet.state.is_resolved())
    }

    fn select(&mut self, verdict: FineSegmentationReviewVerdict) {
        let prior = match self.current_state() {
            FineSegmentationPacketState::Pending => None,
            FineSegmentationPacketState::Selected { prior, .. } => *prior,
            FineSegmentationPacketState::Decided { verdict } => Some(*verdict),
        };
        *self.current_state_mut() = FineSegmentationPacketState::Selected {
            proposed: verdict,
            prior,
        };
    }

    fn confirm(&mut self) -> Result<()> {
        let verdict = match self.current_state() {
            FineSegmentationPacketState::Selected { proposed, .. } => *proposed,
            _ => return invalid("only a selected verdict can be confirmed"),
        };
        *self.current_state_mut() = FineSegmentationPacketState::Decided { verdict };
        self.move_to_next_pending();
        Ok(())
    }

    fn cancel_selection(&mut self) {
        let replacement = match self.current_state() {
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

    fn move_previous(&mut self) {
        self.current_packet_index = self.current_packet_index.saturating_sub(1);
    }

    fn move_next(&mut self) {
        self.current_packet_index =
            (self.current_packet_index + 1).min(self.packets.len().saturating_sub(1));
    }

    fn move_to_next_pending(&mut self) {
        let packet_count = self.packets.len();
        for offset in 1..=packet_count {
            let candidate = (self.current_packet_index + offset) % packet_count;
            if !self.packets[candidate].state.is_resolved() {
                self.current_packet_index = candidate;
                return;
            }
        }
    }

    fn due_break_checkpoint(&mut self) -> Option<(usize, bool)> {
        let completed = self.completed_count();
        if completed == 0 || !completed.is_multiple_of(BREAK_INTERVAL) {
            return None;
        }
        if let Some(index) = self
            .break_checkpoints
            .iter()
            .position(|checkpoint| checkpoint.after_packets == completed)
        {
            return (!self.break_checkpoints[index].continued).then_some((index, false));
        }
        self.break_checkpoints.push(BreakCheckpoint {
            after_packets: completed,
            continued: false,
        });
        Some((self.break_checkpoints.len() - 1, true))
    }

    fn screen(&self, reviewer: &ReviewerArtifact) -> Result<FineSegmentationReviewScreen> {
        let packet = reviewer
            .packets
            .get(self.current_packet_index)
            .ok_or_else(|| {
                Error::ExperimentState("current reviewer packet is absent".to_owned())
            })?;
        let completed = self.completed_count();
        let remainder = completed % BREAK_INTERVAL;
        let break_in = if remainder == 0 {
            BREAK_INTERVAL
        } else {
            BREAK_INTERVAL - remainder
        };
        Ok(FineSegmentationReviewScreen::Packet {
            packet_index: self.current_packet_index,
            packet_count: reviewer.packets.len(),
            packet: packet.packet.clone(),
            instances: packet
                .instances
                .iter()
                .map(|instance| FineSegmentationReviewInstance {
                    instance: instance.instance.clone(),
                    fragments: instance.fragments.clone(),
                })
                .collect(),
            state: self.current_state().clone(),
            completed_packet_count: completed,
            break_in,
        })
    }

    fn response(&self) -> Result<FineSegmentationReviewResponse> {
        if !self.all_complete() {
            return invalid("an incomplete review cannot publish a response");
        }
        let judgments = self
            .packets
            .iter()
            .map(|packet| {
                let verdict = match &packet.state {
                    FineSegmentationPacketState::Decided { verdict } => *verdict,
                    _ => return invalid("an incomplete packet cannot publish a judgment"),
                };
                Ok(FineSegmentationReviewJudgment {
                    packet: packet.packet.clone(),
                    verdict,
                })
            })
            .collect::<Result<Vec<_>>>()?;
        Ok(FineSegmentationReviewResponse {
            schema_version: SCHEMA_VERSION,
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

fn invalid<T>(message: impl Into<String>) -> Result<T> {
    Err(Error::ExperimentState(message.into()))
}

#[derive(Clone, Debug)]
pub struct FineSegmentationReviewTuiModel {
    screen: FineSegmentationReviewScreen,
    instance_scroll: u16,
    half_page_lines: u16,
    interaction_enabled: bool,
}

impl FineSegmentationReviewTuiModel {
    pub fn new(screen: FineSegmentationReviewScreen) -> Self {
        let screen = sanitize_screen(screen);
        Self {
            screen,
            instance_scroll: 0,
            half_page_lines: 1,
            interaction_enabled: true,
        }
    }

    pub fn screen(&self) -> &FineSegmentationReviewScreen {
        &self.screen
    }

    pub fn replace_screen(&mut self, screen: FineSegmentationReviewScreen) {
        let screen = sanitize_screen(screen);
        let packet_changed = packet_index(&self.screen) != packet_index(&screen);
        if packet_changed {
            self.instance_scroll = 0;
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
        let Event::Key(key) = &event else {
            return FineSegmentationReviewAction::None;
        };
        if key.kind != KeyEventKind::Press {
            return FineSegmentationReviewAction::None;
        }
        if key.modifiers == KeyModifiers::CONTROL {
            match key.code {
                KeyCode::Char('d' | 'D')
                    if !matches!(self.screen, FineSegmentationReviewScreen::Break { .. }) =>
                {
                    self.instance_scroll =
                        self.instance_scroll.saturating_add(self.half_page_lines);
                }
                KeyCode::Char('u' | 'U')
                    if !matches!(self.screen, FineSegmentationReviewScreen::Break { .. }) =>
                {
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
            FineSegmentationReviewScreen::Break { .. } => match key.code {
                KeyCode::Enter | KeyCode::Char('c' | 'C') | KeyCode::Char(' ') => {
                    FineSegmentationReviewAction::ContinueBreak
                }
                KeyCode::Char('p' | 'P' | 'q' | 'Q') | KeyCode::Esc => {
                    FineSegmentationReviewAction::Pause
                }
                _ => FineSegmentationReviewAction::None,
            },
            FineSegmentationReviewScreen::Packet { state, .. } => match key.code {
                KeyCode::Char('v' | 'V') => {
                    FineSegmentationReviewAction::Select(FineSegmentationReviewVerdict::Valid)
                }
                KeyCode::Char('i' | 'I') => {
                    FineSegmentationReviewAction::Select(FineSegmentationReviewVerdict::Invalid)
                }
                KeyCode::Char('u' | 'U') => {
                    FineSegmentationReviewAction::Select(FineSegmentationReviewVerdict::Uncertain)
                }
                KeyCode::Enter if matches!(state, FineSegmentationPacketState::Selected { .. }) => {
                    FineSegmentationReviewAction::Confirm
                }
                KeyCode::Esc if matches!(state, FineSegmentationPacketState::Selected { .. }) => {
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
            FineSegmentationReviewScreen::Break {
                completed_packet_count,
            } => self.render_break(frame, area, completed_packet_count),
            FineSegmentationReviewScreen::Packet {
                packet_index,
                packet_count,
                packet,
                instances,
                state,
                completed_packet_count,
                break_in,
            } => self.render_packet(
                frame,
                area,
                packet_index,
                packet_count,
                &packet,
                &instances,
                &state,
                completed_packet_count,
                break_in,
            ),
        }
    }

    fn render_break(&self, frame: &mut Frame<'_>, area: Rect, completed: usize) {
        frame.render_widget(
            Paragraph::new(format!(
                "{completed} packets reviewed.\n\n[Enter/C] Continue    [P] Save/exit"
            ))
            .wrap(Wrap { trim: false })
            .block(
                Block::default()
                    .borders(Borders::ALL)
                    .title("Take a break")
                    .title_style(accent_style()),
            ),
            area,
        );
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
        break_in: usize,
    ) {
        let rows = Layout::default()
            .direction(Direction::Vertical)
            .constraints([
                Constraint::Length(1),
                Constraint::Length(2),
                Constraint::Length(4),
                Constraint::Min(6),
                Constraint::Length(2),
                Constraint::Length(5),
            ])
            .split(area);
        frame.render_widget(
            Paragraph::new(format!(
                "Packet {} of {packet_count} · {completed} reviewed · break in {break_in} · {packet}",
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
        let instance_text = render_instances(instances);
        render_scrollable_panel(
            frame,
            rows[3],
            "Instances",
            &instance_text,
            &mut self.instance_scroll,
            &mut self.half_page_lines,
            false,
        );
        frame.render_widget(
            Paragraph::new(packet_status(state)).wrap(Wrap { trim: false }),
            rows[4],
        );
        self.render_packet_controls(frame, rows[5], state);
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
    ) {
        let selected = |verdict| {
            matches!(
                state,
                FineSegmentationPacketState::Selected { proposed, .. }
                    if *proposed == verdict
            )
        };
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
        let confirm = if matches!(state, FineSegmentationPacketState::Selected { .. }) {
            "Confirm selection"
        } else {
            "Confirm after V/I/U"
        };
        frame.render_widget(
            Paragraph::new(vec![
                Line::from(choices),
                Line::from(vec![
                    Span::styled("[Enter]", accent_style()),
                    Span::styled(format!(" {confirm}  "), secondary_style()),
                    Span::styled("[Esc]", accent_style()),
                    Span::styled(" Cancel selection", secondary_style()),
                ]),
                Line::from(vec![
                    Span::styled("[←/→]", accent_style()),
                    Span::styled(" Previous/next packet  ", secondary_style()),
                    Span::styled("[↑/↓]", accent_style()),
                    Span::styled(" Scroll", secondary_style()),
                ]),
                Line::from(vec![
                    Span::styled("[Ctrl-D/U]", accent_style()),
                    Span::styled(" Half-page  ", secondary_style()),
                    Span::styled("[Ctrl-C]", accent_style()),
                    Span::styled(" Save/exit", secondary_style()),
                ]),
            ]),
            area,
        );
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
        packet, instances, ..
    } = &mut screen
    {
        *packet = terminal_safe(packet).replace('\n', " ");
        for instance in instances {
            instance.instance = terminal_safe(&instance.instance).replace('\n', " ");
            for fragment in &mut instance.fragments {
                *fragment = terminal_safe(fragment);
            }
        }
    }
    screen
}

fn packet_index(screen: &FineSegmentationReviewScreen) -> Option<usize> {
    match screen {
        FineSegmentationReviewScreen::Packet { packet_index, .. } => Some(*packet_index),
        FineSegmentationReviewScreen::Break { .. } => None,
    }
}

fn render_instances(instances: &[FineSegmentationReviewInstance]) -> String {
    instances
        .iter()
        .enumerate()
        .map(|(index, instance)| {
            let prefix = format!("{}. ", index + 1);
            let continuation = " ".repeat(prefix.chars().count());
            instance
                .fragments
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
