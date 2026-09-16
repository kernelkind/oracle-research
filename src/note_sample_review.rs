//! Read-only inspection of a note sample and the reasons for selecting it.

use std::collections::BTreeSet;
use std::io;
use std::path::Path;

use crossterm::event::{Event, KeyCode, KeyEventKind, KeyModifiers};
use ratatui::Frame;
use ratatui::layout::{Constraint, Layout};
use ratatui::text::Line;
use ratatui::widgets::{Paragraph, Wrap};
use serde::Deserialize;

use crate::reference_tui::{
    InteractiveReviewModel, MIN_HEIGHT, MIN_WIDTH, ReferenceTerminal, accent_style, centered,
    is_control_c_event, render_scrollable_panel, secondary_style, terminal_safe,
};

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Selection {
    schema_version: u32,
    title: String,
    purpose: String,
    notes: Vec<Note>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Note {
    id: String,
    title: String,
    note_id: String,
    text: String,
    why: String,
    source: Source,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Source {
    path: String,
    /// One-based position in the original notes array.
    index: usize,
}

#[derive(Debug, PartialEq, Eq)]
pub enum NoteSampleReviewAction {
    None,
    Quit,
}

/// Navigation and scrolling only: this viewer neither generates data nor saves decisions.
pub struct NoteSampleReview {
    selection: Selection,
    index: usize,
    panel: usize,
    scroll: [u16; 2],
    half_page_lines: [u16; 2],
}

impl NoteSampleReview {
    pub fn load(path: impl AsRef<Path>, start_at: Option<&str>) -> io::Result<Self> {
        let selection: Selection = serde_json::from_slice(&std::fs::read(path)?)
            .map_err(|error| invalid(format!("invalid note selection: {error}")))?;
        if selection.schema_version != 1
            || selection.title.trim().is_empty()
            || selection.purpose.trim().is_empty()
            || selection.notes.is_empty()
        {
            return Err(invalid("expected a nonempty schema-1 note selection"));
        }
        let mut ids = BTreeSet::new();
        let mut note_ids = BTreeSet::new();
        for note in &selection.notes {
            if [
                &note.id,
                &note.title,
                &note.text,
                &note.why,
                &note.source.path,
            ]
            .iter()
            .any(|value| value.trim().is_empty())
                || note.source.index == 0
                || note.note_id.len() != 64
                || !note.note_id.bytes().all(|byte| byte.is_ascii_hexdigit())
                || !ids.insert(&note.id)
                || !note_ids.insert(&note.note_id)
            {
                return Err(invalid(
                    "empty or invalid note fields, or duplicate note IDs",
                ));
            }
        }
        let index = match start_at {
            Some(id) => selection
                .notes
                .iter()
                .position(|note| note.id == id)
                .ok_or_else(|| invalid(format!("unknown note: {id}")))?,
            None => 0,
        };
        Ok(Self {
            selection,
            index,
            panel: 0,
            scroll: [0; 2],
            half_page_lines: [1; 2],
        })
    }

    pub fn run(self) -> io::Result<()> {
        ReferenceTerminal::new()?.run_review_model(self)?;
        Ok(())
    }

    pub fn handle_event(&mut self, event: Event) -> NoteSampleReviewAction {
        if is_control_c_event(&event) {
            return NoteSampleReviewAction::Quit;
        }
        let Event::Key(key) = event else {
            return NoteSampleReviewAction::None;
        };
        if !matches!(key.kind, KeyEventKind::Press | KeyEventKind::Repeat) {
            return NoteSampleReviewAction::None;
        }
        let scroll = &mut self.scroll[self.panel];
        let half_page = self.half_page_lines[self.panel];
        if key.modifiers == KeyModifiers::CONTROL {
            match key.code {
                KeyCode::Char('d') => *scroll = scroll.saturating_add(half_page),
                KeyCode::Char('u') => *scroll = scroll.saturating_sub(half_page),
                _ => {}
            }
            return NoteSampleReviewAction::None;
        }
        if key
            .modifiers
            .intersects(KeyModifiers::CONTROL | KeyModifiers::ALT | KeyModifiers::SUPER)
        {
            return NoteSampleReviewAction::None;
        }
        match key.code {
            KeyCode::Char('q') | KeyCode::Esc => return NoteSampleReviewAction::Quit,
            KeyCode::Left | KeyCode::Char('h' | 'p') => {
                self.index =
                    (self.index + self.selection.notes.len() - 1) % self.selection.notes.len();
                self.scroll = [0; 2];
                self.panel = 0;
            }
            KeyCode::Right | KeyCode::Char('l' | 'n') => {
                self.index = (self.index + 1) % self.selection.notes.len();
                self.scroll = [0; 2];
                self.panel = 0;
            }
            KeyCode::Tab | KeyCode::BackTab => self.panel = 1 - self.panel,
            KeyCode::Up | KeyCode::Char('k') => *scroll = scroll.saturating_sub(1),
            KeyCode::Down | KeyCode::Char('j') => *scroll = scroll.saturating_add(1),
            KeyCode::PageUp => *scroll = scroll.saturating_sub(half_page.saturating_mul(2)),
            KeyCode::PageDown => *scroll = scroll.saturating_add(half_page.saturating_mul(2)),
            KeyCode::Home | KeyCode::Char('g') => *scroll = 0,
            KeyCode::End | KeyCode::Char('G') => *scroll = u16::MAX,
            _ => {}
        }
        NoteSampleReviewAction::None
    }

    pub fn render(&mut self, frame: &mut Frame<'_>) {
        let area = centered(frame.area());
        if area.width < MIN_WIDTH || area.height < MIN_HEIGHT {
            frame.render_widget(
                Paragraph::new("Resize to at least 72 × 24.\nq / Esc / Ctrl-C exits."),
                area,
            );
            return;
        }
        let note = &self.selection.notes[self.index];
        let why = terminal_safe(&note.why);
        let why_lines = Paragraph::new(why.as_str())
            .wrap(Wrap { trim: false })
            .line_count(area.width.saturating_sub(4));
        let why_height = u16::try_from(why_lines.saturating_add(2))
            .unwrap_or(u16::MAX)
            .clamp(3, 7);
        let rows = Layout::vertical([
            Constraint::Length(2),
            Constraint::Min(5),
            Constraint::Length(why_height),
            Constraint::Length(3),
        ])
        .split(area);
        frame.render_widget(
            Paragraph::new(vec![
                Line::styled(
                    format!("{} · Read-only", terminal_safe(&self.selection.title)),
                    accent_style(),
                ),
                Line::from(format!(
                    "{} · {} of {} · {}",
                    note.id,
                    self.index + 1,
                    self.selection.notes.len(),
                    terminal_safe(&note.title)
                )),
            ]),
            rows[0],
        );
        for (panel, title, content) in [
            (0, "Complete note", terminal_safe(&note.text)),
            (1, "Why included", why),
        ] {
            render_scrollable_panel(
                frame,
                rows[panel + 1],
                title,
                &content,
                &mut self.scroll[panel],
                &mut self.half_page_lines[panel],
                self.panel == panel,
            );
        }
        frame.render_widget(
            Paragraph::new(vec![
                Line::from("←/→ h/l  Previous/next note    ↑/↓ j/k  Scroll    Tab  Panel"),
                Line::from("PgUp/PgDown  Page    Ctrl-U/D  Half-page    g/G  Top/bottom"),
                Line::from("q / Esc / Ctrl-C  Exit    No decisions are saved"),
            ])
            .style(secondary_style()),
            rows[3],
        );
    }
}

impl InteractiveReviewModel for NoteSampleReview {
    type Action = NoteSampleReviewAction;

    fn none_action() -> Self::Action {
        NoteSampleReviewAction::None
    }
    fn pause_action() -> Self::Action {
        NoteSampleReviewAction::Quit
    }
    fn handle_terminal_event(&mut self, event: Event) -> Self::Action {
        self.handle_event(event)
    }
    fn render_terminal(&mut self, frame: &mut Frame<'_>) {
        self.render(frame);
    }
}

fn invalid(message: impl Into<String>) -> io::Error {
    io::Error::new(io::ErrorKind::InvalidData, message.into())
}
