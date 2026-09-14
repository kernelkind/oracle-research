//! Read-only viewing of existing TRUE04 containment decisions and assessments.

use std::collections::BTreeSet;
use std::io;
use std::path::Path;

use crossterm::event::{Event, KeyCode, KeyEventKind, KeyModifiers};
use ratatui::Frame;
use ratatui::layout::{Constraint, Layout};
use ratatui::text::{Line, Span};
use ratatui::widgets::Paragraph;
use serde::Deserialize;

use crate::reference_tui::{
    InteractiveReviewModel, MIN_HEIGHT, MIN_WIDTH, ReferenceTerminal, accent_style, centered,
    is_control_c_event, render_scrollable_panel, secondary_style, terminal_safe,
};

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Packet {
    schema_version: u32,
    experiment: String,
    threshold: f64,
    items: Vec<Item>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Item {
    item_id: String,
    a: String,
    b: String,
    assessment: String,
    reason: String,
    decisions: Vec<Decision>,
}

#[derive(Deserialize)]
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
    index: usize,
    details: bool,
    scroll: u16,
    half_page_lines: u16,
}

impl ContainmentReview {
    /// Read and validate all input before a terminal enters raw mode.
    pub fn load(path: impl AsRef<Path>, start_at: Option<&str>) -> io::Result<Self> {
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
            index,
            details: false,
            scroll: 0,
            half_page_lines: 1,
        })
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
