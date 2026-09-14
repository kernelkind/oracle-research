//! View existing TRUE04 evidence, optionally saving separate human decisions.

use std::collections::{BTreeMap, BTreeSet};
use std::io;
use std::path::{Path, PathBuf};

use crossterm::event::{Event, KeyCode, KeyEventKind, KeyModifiers};
use ratatui::Frame;
use ratatui::layout::{Constraint, Layout};
use ratatui::text::{Line, Span};
use ratatui::widgets::Paragraph;
use serde::{Deserialize, Serialize};

use crate::reference_map::ReviewOutcome;
use crate::reference_tui::{
    ApprovalEvidence, ApprovalEvidenceLayout, ApprovalGuidance, ApprovalScreen, ApprovalTuiAction,
    InteractiveReviewModel, MIN_HEIGHT, MIN_WIDTH, ReferenceTerminal, accent_style, centered,
    is_control_c_event, render_scrollable_panel, secondary_style, terminal_safe,
};
use crate::review_state::{acquire_session_lock, load_session, save_session, value_sha256};
use crate::snapshot::{Error, Result, io_error};

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct Packet {
    schema_version: u32,
    experiment: String,
    threshold: f64,
    items: Vec<Item>,
}

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct Item {
    item_id: String,
    a: String,
    b: String,
    assessment: String,
    reason: String,
    decisions: Vec<Decision>,
}

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct Decision {
    id: String,
    a_id: String,
    b_id: String,
    native: bool,
    score: f64,
    cutoff: bool,
    model_input: String,
}

#[derive(Deserialize)]
struct TitleCatalog {
    schema_version: u32,
    groups: Vec<TitleGroup>,
}

#[derive(Deserialize)]
struct TitleGroup {
    group: String,
    title: String,
    instances: Vec<MaskInstance>,
}

#[derive(Deserialize)]
struct MaskInstance {
    instance: String,
    fragments: Vec<String>,
}

impl Packet {
    fn validate(&self) -> io::Result<()> {
        if self.schema_version != 1
            || self.experiment != "TRUE04"
            || self.threshold != 0.142
            || self.items.is_empty()
        {
            return Err(invalid(
                "expected a nonempty TRUE04 schema-1 packet with threshold 0.142",
            ));
        }
        let mut item_ids = BTreeSet::new();
        let mut record_ids = BTreeSet::new();
        for item in &self.items {
            if [&item.item_id, &item.a, &item.b, &item.reason]
                .iter()
                .any(|text| text.trim().is_empty())
                || !matches!(item.assessment.as_str(), "Incorrect" | "Ambiguous")
                || item.decisions.is_empty()
                || !item_ids.insert(&item.item_id)
            {
                return Err(invalid(
                    "empty or invalid containment item, or duplicate item ID",
                ));
            }
            let expected_input = format!(
                "premise: This text is about {}. hypothesis: This text is about {}.",
                item.b, item.a
            );
            for decision in &item.decisions {
                if [&decision.id, &decision.a_id, &decision.b_id]
                    .iter()
                    .any(|text| text.trim().is_empty())
                    || decision.id != format!("{}-contains-{}", decision.a_id, decision.b_id)
                    || !record_ids.insert(&decision.id)
                    || !decision.score.is_finite()
                    || !(0.0..=1.0).contains(&decision.score)
                    || decision.cutoff != (decision.score > self.threshold)
                    || decision.model_input != expected_input
                {
                    return Err(invalid(format!(
                        "invalid source IDs, score, cutoff, or exact model input for {}",
                        item.item_id
                    )));
                }
            }
        }
        Ok(())
    }
}

fn invalid(message: impl Into<String>) -> io::Error {
    io::Error::new(io::ErrorKind::InvalidData, message.into())
}

/// The viewer has no decisions to submit and no persisted session.
#[derive(Debug, PartialEq, Eq)]
pub enum ContainmentReviewAction {
    None,
    Quit,
}

pub struct ContainmentReview {
    packet: Packet,
    packet_path: PathBuf,
    titles: Option<BTreeMap<String, TitleGroup>>,
    titles_path: Option<PathBuf>,
    index: usize,
    details: bool,
    scroll: u16,
    half_page_lines: u16,
}

impl ContainmentReview {
    /// Read and validate all input before a terminal enters raw mode.
    pub fn load(path: impl AsRef<Path>, start_at: Option<&str>) -> io::Result<Self> {
        let path = path.as_ref();
        let packet: Packet = serde_json::from_slice(&std::fs::read(path)?)
            .map_err(|error| invalid(format!("invalid containment packet: {error}")))?;
        packet.validate()?;
        let index = match start_at {
            Some(id) => packet
                .items
                .iter()
                .position(|item| item.item_id == id)
                .ok_or_else(|| invalid(format!("unknown containment card: {id}")))?,
            None => 0,
        };
        Ok(Self {
            packet,
            packet_path: path.to_owned(),
            titles: None,
            titles_path: None,
            index,
            details: false,
            scroll: 0,
            half_page_lines: 1,
        })
    }

    /// Attach source masks for display without changing the reviewed questions
    /// or the hash that binds existing answers to those questions.
    pub fn with_titles(mut self, path: impl AsRef<Path>) -> io::Result<Self> {
        let path = path.as_ref();
        let catalog: TitleCatalog = serde_json::from_slice(&std::fs::read(path)?)
            .map_err(|error| invalid(format!("invalid title catalog: {error}")))?;
        if catalog.schema_version != 1 || catalog.groups.is_empty() {
            return Err(invalid("expected a nonempty schema-1 title catalog"));
        }
        let mut groups = BTreeMap::new();
        let mut masks = BTreeMap::new();
        for group in catalog.groups {
            if group.group.trim().is_empty()
                || group.title.trim().is_empty()
                || group.instances.is_empty()
            {
                return Err(invalid("empty source group, title, or masks"));
            }
            for mask in &group.instances {
                if mask.instance.trim().is_empty()
                    || mask.fragments.is_empty()
                    || mask.fragments.iter().any(|text| text.trim().is_empty())
                {
                    return Err(invalid("empty vector ID or mask fragments"));
                }
                if masks
                    .insert(mask.instance.clone(), mask.fragments.clone())
                    .is_some_and(|previous| previous != mask.fragments)
                {
                    return Err(invalid(format!("conflicting masks for {}", mask.instance)));
                }
            }
            if groups.insert(group.group.clone(), group).is_some() {
                return Err(invalid("duplicate source group ID"));
            }
        }
        for item in &self.packet.items {
            for decision in &item.decisions {
                for (id, expected_title) in [(&decision.a_id, &item.a), (&decision.b_id, &item.b)] {
                    let group = groups
                        .get(id)
                        .ok_or_else(|| invalid(format!("missing source masks for {id}")))?;
                    if group.title != *expected_title {
                        return Err(invalid(format!("source title mismatch for {id}")));
                    }
                }
            }
        }
        self.titles = Some(groups);
        self.titles_path = Some(path.to_owned());
        Ok(self)
    }

    pub fn run(self) -> io::Result<()> {
        ReferenceTerminal::new()?.run_review_model(self)?;
        Ok(())
    }

    pub fn handle_event(&mut self, event: Event) -> ContainmentReviewAction {
        if is_control_c_event(&event) {
            return ContainmentReviewAction::Quit;
        }
        let Event::Key(key) = event else {
            return ContainmentReviewAction::None;
        };
        if key.kind != KeyEventKind::Press {
            return ContainmentReviewAction::None;
        }
        if key.modifiers == KeyModifiers::CONTROL {
            match key.code {
                KeyCode::Char('d') => {
                    self.scroll = self.scroll.saturating_add(self.half_page_lines)
                }
                KeyCode::Char('u') => {
                    self.scroll = self.scroll.saturating_sub(self.half_page_lines)
                }
                _ => {}
            }
            return ContainmentReviewAction::None;
        }
        if key
            .modifiers
            .intersects(KeyModifiers::CONTROL | KeyModifiers::ALT | KeyModifiers::SUPER)
        {
            return ContainmentReviewAction::None;
        }
        match key.code {
            KeyCode::Char('q') | KeyCode::Esc => return ContainmentReviewAction::Quit,
            KeyCode::Left | KeyCode::Char('h' | 'p') => {
                self.index = (self.index + self.packet.items.len() - 1) % self.packet.items.len();
                self.scroll = 0;
            }
            KeyCode::Right | KeyCode::Char('l' | 'n') => {
                self.index = (self.index + 1) % self.packet.items.len();
                self.scroll = 0;
            }
            KeyCode::Up | KeyCode::Char('k') => self.scroll = self.scroll.saturating_sub(1),
            KeyCode::Down | KeyCode::Char('j') => self.scroll = self.scroll.saturating_add(1),
            KeyCode::PageUp => self.scroll = self.scroll.saturating_sub(self.half_page_lines * 2),
            KeyCode::PageDown => self.scroll = self.scroll.saturating_add(self.half_page_lines * 2),
            KeyCode::Char('d') => {
                self.details = !self.details;
                self.scroll = 0;
            }
            _ => {}
        }
        ContainmentReviewAction::None
    }

    pub fn render(&mut self, frame: &mut Frame<'_>) {
        let area = centered(frame.area());
        if area.width < MIN_WIDTH || area.height < MIN_HEIGHT {
            frame.render_widget(
                Paragraph::new("TRUE04: resize to at least 72 × 24.\nq / Esc / Ctrl-C exits."),
                area,
            );
            return;
        }
        let rows = Layout::vertical([
            Constraint::Length(2),
            Constraint::Min(3),
            Constraint::Length(3),
        ])
        .split(area);
        let item = &self.packet.items[self.index];
        frame.render_widget(
            Paragraph::new(vec![
                Line::from(vec![
                    Span::styled(
                        format!(
                            "TRUE04 · {} of {} · {}",
                            self.index + 1,
                            self.packet.items.len(),
                            terminal_safe(&item.item_id)
                        ),
                        accent_style(),
                    ),
                    Span::styled(" · Read-only", secondary_style()),
                ]),
                Line::from(format!("My assessment: {}", item.assessment)),
            ]),
            rows[0],
        );
        let content = terminal_safe(&if self.details {
            self.exact_details()
        } else {
            self.summary()
        });
        render_scrollable_panel(
            frame,
            rows[1],
            if self.details {
                "Exact details"
            } else {
                "Pair"
            },
            &content,
            &mut self.scroll,
            &mut self.half_page_lines,
            true,
        );
        frame.render_widget(
            Paragraph::new(vec![
                Line::from("Left/Right h/l n/p Prev/next   Up/Down j/k Scroll"),
                Line::from("PgUp/PgDown Page   Ctrl-U/Ctrl-D Half-page"),
                Line::from("d Exact details   q/Esc/Ctrl-C Exit   Read-only"),
            ])
            .style(secondary_style()),
            rows[2],
        );
    }

    fn summary(&self) -> String {
        let item = &self.packet.items[self.index];
        let minimum = item
            .decisions
            .iter()
            .map(|d| d.score)
            .fold(f64::INFINITY, f64::min);
        let maximum = item
            .decisions
            .iter()
            .map(|d| d.score)
            .fold(f64::NEG_INFINITY, f64::max);
        let score = if minimum == maximum {
            format!("{minimum:.6}")
        } else {
            format!("{minimum:.6}–{maximum:.6}")
        };
        let mut text = format!(
            "A (parent): {}\nB (child): {}\n\nDoes A contain B?\nNative: {}    Cutoff: {} (score > {})\nScore: {} (first-token 1 probability)\n",
            item.a,
            item.b,
            verdicts(item.decisions.iter().map(|d| d.native)),
            verdicts(item.decisions.iter().map(|d| d.cutoff)),
            self.packet.threshold,
            score
        );
        if minimum != maximum {
            text.push_str(&format!("Duplicate-score range: {minimum} to {maximum}\n"));
        }
        text.push_str(&format!("\nReason:\n{}", item.reason));
        text
    }

    fn exact_details(&self) -> String {
        let item = &self.packet.items[self.index];
        let mut text = format!(
            "A (parent): {}\nB (child): {}\n\nDoes A contain B?\n\nScore definition:\nFull-vocabulary probability of the first output token being 1;\nnot calibrated containment confidence.\nNot 0/1-normalized. Token ID: 209.\nNative: full generated label (1 = Yes; 0 = No).\nCutoff: score > {}.\n\nExact model input:\n{}",
            item.a, item.b, self.packet.threshold, item.decisions[0].model_input
        );
        for (index, decision) in item.decisions.iter().enumerate() {
            text.push_str(&format!(
                "\n\nSource record {} of {}\nID: {}\nA source: {}\nB source: {}\nNative: {}    Cutoff: {}\nScore (full precision): {}",
                index + 1, item.decisions.len(), decision.id, decision.a_id, decision.b_id,
                yes_no(decision.native), yes_no(decision.cutoff), decision.score
            ));
        }
        text
    }
}

fn yes_no(value: bool) -> &'static str {
    if value { "Yes" } else { "No" }
}

fn verdicts(values: impl Iterator<Item = bool>) -> &'static str {
    let values: BTreeSet<_> = values.collect();
    if values.len() == 1 {
        yes_no(*values.first().unwrap())
    } else {
        "Yes / No"
    }
}

impl InteractiveReviewModel for ContainmentReview {
    type Action = ContainmentReviewAction;

    fn none_action() -> Self::Action {
        ContainmentReviewAction::None
    }
    fn pause_action() -> Self::Action {
        ContainmentReviewAction::Quit
    }
    fn handle_terminal_event(&mut self, event: Event) -> Self::Action {
        self.handle_event(event)
    }
    fn render_terminal(&mut self, frame: &mut Frame<'_>) {
        self.render(frame);
    }
}

#[derive(Clone, Copy, Deserialize, Serialize)]
#[serde(rename_all = "snake_case")]
enum ContainmentDecision {
    Yes,
    No,
    Skipped,
}

#[derive(Default, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct ContainmentDecisionRecord {
    outcome: Option<ContainmentDecision>,
    comment: String,
}

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct ContainmentDecisionSession {
    schema_version: u32,
    batch_sha256: String,
    current_item: Option<String>,
    decisions: BTreeMap<String, ContainmentDecisionRecord>,
}

#[derive(Debug, Eq, PartialEq)]
pub enum ContainmentDecisionReviewOutcome {
    Paused,
    Completed {
        yes: usize,
        no: usize,
        skipped: usize,
    },
}

impl ContainmentReview {
    fn masks_for_groups<'a>(&self, ids: impl Iterator<Item = &'a str>) -> String {
        let groups = self.titles.as_ref().expect("source masks loaded");
        let mut seen = BTreeSet::new();
        let mut lines = Vec::new();
        for id in ids {
            for mask in &groups[id].instances {
                if seen.insert(&mask.instance) {
                    lines.push(format!(
                        "{}  {}",
                        mask.instance,
                        mask.fragments
                            .iter()
                            .map(|fragment| format!("⟦{fragment}⟧"))
                            .collect::<Vec<_>>()
                            .join(" ")
                    ));
                }
            }
        }
        lines.join("\n\n")
    }

    fn decision_screen(&self, decision: &ContainmentDecisionRecord) -> ApprovalScreen {
        let item = &self.packet.items[self.index];
        let status = match decision.outcome {
            None => "Not reviewed",
            Some(ContainmentDecision::Yes) => "Yes (contains)",
            Some(ContainmentDecision::No) => "No (does not contain)",
            Some(ContainmentDecision::Skipped) => "Skipped",
        };
        let mut screen = ApprovalScreen {
            heading: format!(
                "TRUE04 · {} of {} · {} · {status}",
                self.index + 1,
                self.packet.items.len(),
                item.item_id
            ),
            title: None,
            scope: "Does category A contain category B?".into(),
            approve_label: "Yes (contains)".into(),
            reject_label: "No (does not contain)".into(),
            rejection_help: String::new(),
            guidance: Some(ApprovalGuidance {
                title: "Details".into(),
                body: format!(
                    "Answer containment in the supplied direction: does A contain B? A is the proposed parent; B is the proposed child. Judge containment, not whether my uncertainty is justified. My comment is context, not an answer key. Native answers and scores are saved source evidence, not your decision.\n\nA records Yes; R records No; S records a skip. Each answer advances to an unfinished card. C edits your optional comment; Enter saves it. Left/right visits all cards, including reviewed cards. Tab changes the panel scrolled by up/down or j/k. Ctrl-C exits with saved decisions, comments and the current card. Resume with the same command; --start-at reopens any card. No graph changes are applied.\n\n{}",
                    self.exact_details()
                ),
            }),
            evidence: ApprovalEvidenceLayout::Stacked {
                top: ApprovalEvidence {
                    title: "Categories".into(),
                    annotation: String::new(),
                    body: format!(
                        "A (proposed parent): {}\n\nB (proposed child): {}",
                        item.a, item.b
                    ),
                },
                bottom: ApprovalEvidence {
                    title: "My comment".into(),
                    annotation: String::new(),
                    body: item.reason.clone(),
                },
            },
        };
        if self.titles.is_some() {
            screen.evidence = ApprovalEvidenceLayout::Paged(vec![
                ApprovalEvidence {
                    title: format!("A (proposed parent): {}", item.a),
                    annotation: String::new(),
                    body: self.masks_for_groups(item.decisions.iter().map(|d| d.a_id.as_str())),
                },
                ApprovalEvidence {
                    title: format!("B (proposed child): {}", item.b),
                    annotation: String::new(),
                    body: self.masks_for_groups(item.decisions.iter().map(|d| d.b_id.as_str())),
                },
                ApprovalEvidence {
                    title: "My comment".into(),
                    annotation: String::new(),
                    body: item.reason.clone(),
                },
            ]);
            screen.guidance.as_mut().expect("review guidance").body.push_str(
                "\n\nThe masks show the source of each title. TRUE saw only the category titles, not these masks. Where an identical title represents multiple groups, all their source masks are shown. Only repeated vector IDs are deduplicated."
            );
        }
        screen
    }
}

/// Record human answers to directional containment without modifying the packet.
/// All packet/session validation precedes the first terminal callback. `start_at`
/// explicitly reopens any card, including an already completed card.
pub fn run_containment_decision_review(
    packet_path: impl AsRef<Path>,
    session_path: impl AsRef<Path>,
    start_at: Option<&str>,
    review: impl FnMut(ApprovalScreen, String) -> io::Result<ApprovalTuiAction>,
) -> Result<ContainmentDecisionReviewOutcome> {
    let packet_path = packet_path.as_ref();
    ContainmentReview::load(packet_path, start_at)
        .map_err(|source| io_error("read", packet_path, source))?
        .run_decisions(session_path, start_at, review)
}

impl ContainmentReview {
    /// Save decisions on the loaded questions, with any attached masks as display evidence.
    pub fn run_decisions(
        self,
        session_path: impl AsRef<Path>,
        start_at: Option<&str>,
        mut review: impl FnMut(ApprovalScreen, String) -> io::Result<ApprovalTuiAction>,
    ) -> Result<ContainmentDecisionReviewOutcome> {
        let mut viewer = self;
        let input = viewer.packet_path.clone();
        let packet_path = input.as_path();
        if let Some(id) = start_at {
            viewer.index = viewer
                .packet
                .items
                .iter()
                .position(|item| item.item_id == id)
                .ok_or_else(|| invalid(format!("unknown containment card: {id}")))
                .map_err(|source| io_error("read", packet_path, source))?;
        }
        // Resolve existing symlinks so aliases share the same session lock and writes.
        let session_path = std::fs::canonicalize(session_path.as_ref())
            .or_else(|error| {
                if error.kind() == io::ErrorKind::NotFound {
                    std::path::absolute(session_path.as_ref())
                } else {
                    Err(error)
                }
            })
            .map_err(|source| io_error("resolve", session_path.as_ref(), source))?;
        let session_path = session_path.as_path();
        for source_path in std::iter::once(packet_path).chain(viewer.titles_path.as_deref()) {
            let same_file =
                std::fs::canonicalize(source_path).is_ok_and(|path| path == session_path);
            #[cfg(unix)]
            let same_file = {
                use std::os::unix::fs::MetadataExt;
                same_file
                    || match (
                        std::fs::metadata(source_path),
                        std::fs::metadata(session_path),
                    ) {
                        (Ok(packet), Ok(session)) => {
                            packet.dev() == session.dev() && packet.ino() == session.ino()
                        }
                        _ => false,
                    }
            };
            if same_file {
                return Err(Error::ExperimentState(
                    "containment inputs and review session must be different files".into(),
                ));
            }
        }
        let ids: BTreeSet<_> = viewer
            .packet
            .items
            .iter()
            .map(|item| item.item_id.as_str())
            .collect();
        let batch_sha256 = value_sha256(&viewer.packet)?;
        let _lock = acquire_session_lock(session_path)?;
        let mut session = match load_session::<ContainmentDecisionSession>(session_path)? {
            Some(session) => {
                if session.schema_version != 1
                    || session.batch_sha256 != batch_sha256
                    || session
                        .decisions
                        .keys()
                        .map(String::as_str)
                        .collect::<BTreeSet<_>>()
                        != ids
                {
                    return Err(Error::ExperimentState(
                        "review session belongs to a different containment batch".into(),
                    ));
                }
                if session
                    .current_item
                    .as_deref()
                    .is_some_and(|id| !ids.contains(id))
                    || (session.current_item.is_none()
                        && session
                            .decisions
                            .values()
                            .any(|record| record.outcome.is_none()))
                {
                    return Err(Error::ExperimentState(
                        "containment review session has an invalid current item".into(),
                    ));
                }
                session
            }
            None => ContainmentDecisionSession {
                schema_version: 1,
                batch_sha256,
                current_item: Some(viewer.packet.items[viewer.index].item_id.clone()),
                decisions: viewer
                    .packet
                    .items
                    .iter()
                    .map(|item| (item.item_id.clone(), ContainmentDecisionRecord::default()))
                    .collect(),
            },
        };
        if let Some(id) = start_at {
            session.current_item = Some(id.to_owned());
        }
        save_session(session_path, &session)?;
        while let Some(id) = &session.current_item {
            viewer.index = viewer
                .packet
                .items
                .iter()
                .position(|item| &item.item_id == id)
                .expect("validated current item");
            let decision = &session.decisions[id];
            let action = review(viewer.decision_screen(decision), decision.comment.clone())
                .map_err(|source| io_error("review containment from", packet_path, source))?;
            let advance = matches!(
                action,
                ApprovalTuiAction::Submit { .. } | ApprovalTuiAction::Skip { .. }
            );
            let decision = session.decisions.get_mut(id).expect("validated item ID");
            match action {
                ApprovalTuiAction::Pause => return Ok(ContainmentDecisionReviewOutcome::Paused),
                ApprovalTuiAction::None => {
                    return Err(Error::ExperimentState(
                        "containment review returned without an action".into(),
                    ));
                }
                ApprovalTuiAction::PreviousItem => {
                    session.current_item = Some(
                        viewer.packet.items[(viewer.index + viewer.packet.items.len() - 1)
                            % viewer.packet.items.len()]
                        .item_id
                        .clone(),
                    );
                }
                ApprovalTuiAction::NextItem => {
                    session.current_item = Some(
                        viewer.packet.items[(viewer.index + 1) % viewer.packet.items.len()]
                            .item_id
                            .clone(),
                    );
                }
                ApprovalTuiAction::SaveComment { comment } => decision.comment = comment,
                ApprovalTuiAction::Submit { outcome, comment } => {
                    decision.outcome = Some(match outcome {
                        ReviewOutcome::Approved => ContainmentDecision::Yes,
                        ReviewOutcome::Rejected => ContainmentDecision::No,
                    });
                    decision.comment = comment;
                }
                ApprovalTuiAction::Skip { comment } => {
                    decision.outcome = Some(ContainmentDecision::Skipped);
                    decision.comment = comment;
                }
            }
            if advance {
                session.current_item = (1..=viewer.packet.items.len())
                    .map(|offset| {
                        &viewer.packet.items[(viewer.index + offset) % viewer.packet.items.len()]
                            .item_id
                    })
                    .find(|id| session.decisions[*id].outcome.is_none())
                    .cloned();
            }
            save_session(session_path, &session)?;
        }
        let (mut yes, mut no, mut skipped) = (0, 0, 0);
        for decision in session.decisions.values() {
            match decision.outcome {
                Some(ContainmentDecision::Yes) => yes += 1,
                Some(ContainmentDecision::No) => no += 1,
                Some(ContainmentDecision::Skipped) => skipped += 1,
                None => unreachable!("all cards have decisions"),
            }
        }
        Ok(ContainmentDecisionReviewOutcome::Completed { yes, no, skipped })
    }
}
