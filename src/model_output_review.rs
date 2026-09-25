//! Comparison of saved model outputs with optional, separately persisted user comments.

use std::collections::{BTreeMap, BTreeSet};
use std::io;
use std::path::{Path, PathBuf};

use crossterm::event::{Event, KeyCode, KeyEventKind, KeyModifiers};
use ratatui::Frame;
use ratatui::layout::{Constraint, Layout};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Paragraph, Wrap};
use serde::{Deserialize, Serialize};

use crate::review_state::{acquire_session_lock, load_session, save_session, value_sha256};

use crate::reference_tui::{
    InteractiveReviewModel, MIN_HEIGHT, MIN_WIDTH, ReferenceTerminal, accent_style,
    is_control_c_event, render_scrollable_panel, secondary_style, terminal_safe,
};

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Review {
    schema_version: u32,
    title: String,
    notes: Vec<Note>,
    #[serde(default)]
    orderings: Vec<ReviewOrdering>,
    #[serde(default)]
    labels: ReviewLabels,
}

/// Optional presentation labels let saved non-post comparisons use the same viewer.
#[derive(Default, Deserialize)]
#[serde(deny_unknown_fields)]
struct ReviewLabels {
    source: Option<String>,
    alternate_source: Option<String>,
    output: Option<String>,
    comment: Option<String>,
    item: Option<String>,
    variant: Option<String>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ReviewOrdering {
    name: String,
    note_ids: Vec<String>,
}

impl Review {
    fn apply_ordering(&mut self, index: usize) {
        let positions: BTreeMap<_, _> = self.orderings[index]
            .note_ids
            .iter()
            .enumerate()
            .map(|(i, id)| (id.as_str(), i))
            .collect();
        self.notes.sort_by_key(|note| positions[note.id.as_str()]);
    }
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Note {
    id: String,
    title: String,
    text: String,
    model_input: Option<String>,
    summary: Option<String>,
    results: Vec<ModelResult>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ModelResult {
    model: String,
    output: String,
    comment: String,
    #[serde(default)]
    comment_key: Option<String>,
}

#[derive(Clone, Default, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct UserComments {
    comments: BTreeMap<String, UserComment>,
}

#[derive(Clone, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct UserComment {
    note_id: String,
    model: String,
    comment: String,
}

struct CommentSession {
    path: PathBuf,
    _lock: std::fs::File,
    saved: UserComments,
}

#[derive(Debug, PartialEq, Eq)]
pub enum ModelOutputReviewAction {
    None,
    Quit,
}

/// Saved inputs/outputs are never changed; optional comments use a separate session.
pub struct ModelOutputReview {
    review: Review,
    note: usize,
    model: usize,
    ordering: usize,
    panel: usize,
    show_model_input: bool,
    scroll: [u16; 3],
    half_page_lines: [u16; 3],
    focus_panel: Option<usize>,
    focus_scroll: u16,
    focus_half_page: u16,
    comments: Option<CommentSession>,
    comment_buffer: Option<String>,
    comment_error: Option<String>,
}

impl ModelOutputReview {
    pub fn load(path: impl AsRef<Path>, start_at: Option<&str>) -> io::Result<Self> {
        let mut review: Review = serde_json::from_slice(&std::fs::read(path)?)
            .map_err(|error| invalid(format!("invalid model-output review: {error}")))?;
        if review.schema_version != 1 || review.title.trim().is_empty() || review.notes.is_empty() {
            return Err(invalid("expected a nonempty schema-1 model-output review"));
        }
        let labels = &review.labels;
        if [
            &labels.source,
            &labels.alternate_source,
            &labels.output,
            &labels.comment,
            &labels.item,
            &labels.variant,
        ]
        .into_iter()
        .flatten()
        .any(|s| s.trim().is_empty())
        {
            return Err(invalid("review labels must not be empty"));
        }
        let models: Vec<_> = review.notes[0]
            .results
            .iter()
            .map(|result| result.model.as_str())
            .collect();
        if models.is_empty() || models.iter().collect::<BTreeSet<_>>().len() != models.len() {
            return Err(invalid("expected a nonempty list of distinct models"));
        }
        let mut ids = BTreeSet::new();
        for note in &review.notes {
            if note
                .summary
                .as_ref()
                .is_some_and(|summary| summary.trim().is_empty() || note.results.len() != 1)
            {
                return Err(invalid(
                    "summary reviews require nonempty summaries and one result per item",
                ));
            }
            if [&note.id, &note.title, &note.text]
                .iter()
                .any(|value| value.trim().is_empty())
                || note
                    .model_input
                    .as_ref()
                    .is_some_and(|text| text.trim().is_empty())
                || !ids.insert(&note.id)
            {
                return Err(invalid("empty note fields or duplicate note IDs"));
            }
            if !note
                .results
                .iter()
                .map(|result| result.model.as_str())
                .eq(models.iter().copied())
            {
                return Err(invalid(
                    "all notes must have the same models in the same order",
                ));
            }
            if note.results.iter().any(|result| {
                [&result.model, &result.output, &result.comment]
                    .iter()
                    .any(|value| value.trim().is_empty())
            }) {
                return Err(invalid(
                    "model names, outputs, and comments must not be empty",
                ));
            }
        }
        let mut ordering_names = BTreeSet::new();
        for ordering in &review.orderings {
            if ordering.name.trim().is_empty()
                || !ordering_names.insert(&ordering.name)
                || ordering.note_ids.len() != ids.len()
                || ordering.note_ids.iter().collect::<BTreeSet<_>>() != ids
            {
                return Err(invalid(
                    "orderings require distinct names and complete note-ID permutations",
                ));
            }
        }
        if !review.orderings.is_empty() {
            review.apply_ordering(0);
        }
        let note = match start_at {
            Some(id) => review
                .notes
                .iter()
                .position(|note| note.id == id)
                .ok_or_else(|| invalid(format!("unknown note: {id}")))?,
            None => 0,
        };
        Ok(Self {
            review,
            note,
            model: 0,
            ordering: 0,
            panel: 0,
            show_model_input: false,
            scroll: [0; 3],
            half_page_lines: [1; 3],
            focus_panel: None,
            focus_scroll: 0,
            focus_half_page: 1,
            comments: None,
            comment_buffer: None,
            comment_error: None,
        })
    }

    /// Enable durable comments without mutating the review's inputs or outputs.
    pub fn with_comments(mut self, path: impl AsRef<Path>) -> io::Result<Self> {
        let path = std::env::current_dir()?.join(path);
        let lock = acquire_session_lock(&path).map_err(io::Error::other)?;
        let saved: UserComments = load_session(&path)
            .map_err(io::Error::other)?
            .unwrap_or_default();
        let mut keys = BTreeSet::new();
        for note in &self.review.notes {
            for result in &note.results {
                let key = Self::comment_key(note, result);
                if !keys.insert(key.clone()) {
                    return Err(invalid("duplicate comment identity"));
                }
                if let Some(comment) = saved.comments.get(&key) {
                    if comment.note_id != note.id || comment.model != result.model {
                        return Err(invalid("comment identity differs from review item"));
                    }
                }
            }
        }
        self.comments = Some(CommentSession {
            path,
            _lock: lock,
            saved,
        });
        Ok(self)
    }

    fn comment_key(note: &Note, result: &ModelResult) -> String {
        result.comment_key.clone().unwrap_or_else(|| {
            value_sha256(&(
                &note.id,
                &result.model,
                &note.text,
                &note.model_input,
                &result.output,
            ))
            .expect("string tuples serialize")
        })
    }

    fn user_comment(&self) -> &str {
        let note = &self.review.notes[self.note];
        self.comments
            .as_ref()
            .and_then(|session| {
                session
                    .saved
                    .comments
                    .get(&Self::comment_key(note, &note.results[self.model]))
            })
            .map_or("", |comment| comment.comment.as_str())
    }

    fn save_comment(&mut self) -> io::Result<()> {
        let note = &self.review.notes[self.note];
        let result = &note.results[self.model];
        let key = Self::comment_key(note, result);
        let session = self.comments.as_mut().expect("comment mode enabled");
        let mut saved = session.saved.clone();
        saved.comments.insert(
            key,
            UserComment {
                note_id: note.id.clone(),
                model: result.model.clone(),
                comment: self
                    .comment_buffer
                    .as_deref()
                    .unwrap_or_default()
                    .trim()
                    .to_owned(),
            },
        );
        save_session(&session.path, &saved).map_err(io::Error::other)?;
        session.saved = saved;
        self.comment_buffer = None;
        self.comment_error = None;
        Ok(())
    }

    pub fn check_summary(&self) -> String {
        format!(
            "{}: {} {}s, {} {}s; {}, no model calls or saved decisions.",
            terminal_safe(&self.review.title),
            self.review.notes.len(),
            terminal_safe(self.review.labels.item.as_deref().unwrap_or("note")),
            self.review.notes[0].results.len(),
            terminal_safe(self.review.labels.variant.as_deref().unwrap_or("model")),
            if self.comments.is_some() {
                "user comments enabled"
            } else {
                "read-only saved outputs"
            },
        )
    }

    pub fn run(self) -> io::Result<()> {
        ReferenceTerminal::new()?.run_review_model(self)?;
        Ok(())
    }

    fn select_model(&mut self, model: usize) {
        if model < self.review.notes[self.note].results.len() && model != self.model {
            self.model = model;
            self.scroll[1..].fill(0);
        }
    }

    fn select_note(&mut self, note: usize) {
        self.note = note;
        self.scroll.fill(0);
        self.show_model_input = false;
        self.focus_panel = None;
        self.focus_scroll = 0;
    }

    pub fn handle_event(&mut self, event: Event) -> ModelOutputReviewAction {
        if is_control_c_event(&event) {
            return ModelOutputReviewAction::Quit;
        }
        if self.comment_buffer.is_some() {
            match event {
                Event::Paste(text) => self
                    .comment_buffer
                    .as_mut()
                    .unwrap()
                    .push_str(&terminal_safe(&text)),
                Event::Key(key)
                    if matches!(key.kind, KeyEventKind::Press | KeyEventKind::Repeat) =>
                {
                    if key
                        .modifiers
                        .intersects(KeyModifiers::CONTROL | KeyModifiers::ALT | KeyModifiers::SUPER)
                    {
                        return ModelOutputReviewAction::None;
                    }
                    match key.code {
                        KeyCode::Enter => {
                            if let Err(error) = self.save_comment() {
                                self.comment_error = Some(format!("Not saved: {error}"));
                            }
                        }
                        KeyCode::Esc => {
                            self.comment_buffer = None;
                            self.comment_error = None;
                        }
                        KeyCode::Backspace => {
                            self.comment_buffer.as_mut().unwrap().pop();
                        }
                        KeyCode::Char(c) => self.comment_buffer.as_mut().unwrap().push(c),
                        _ => {}
                    }
                }
                _ => {}
            }
            return ModelOutputReviewAction::None;
        }
        let Event::Key(key) = event else {
            return ModelOutputReviewAction::None;
        };
        if !matches!(key.kind, KeyEventKind::Press | KeyEventKind::Repeat) {
            return ModelOutputReviewAction::None;
        }
        let focused = self.review.notes[self.note].summary.is_some();
        let scroll = if focused {
            &mut self.focus_scroll
        } else {
            &mut self.scroll[self.panel]
        };
        let half_page = if focused {
            self.focus_half_page
        } else {
            self.half_page_lines[self.panel]
        };
        if key.modifiers == KeyModifiers::CONTROL {
            match key.code {
                KeyCode::Char('d') => *scroll = scroll.saturating_add(half_page),
                KeyCode::Char('u') => *scroll = scroll.saturating_sub(half_page),
                _ => {}
            }
            return ModelOutputReviewAction::None;
        }
        if key
            .modifiers
            .intersects(KeyModifiers::CONTROL | KeyModifiers::ALT | KeyModifiers::SUPER)
        {
            return ModelOutputReviewAction::None;
        }
        let models = self.review.notes[self.note].results.len();
        match key.code {
            KeyCode::Char('e') if self.comments.is_some() => {
                self.comment_buffer = Some(self.user_comment().to_owned());
            }
            KeyCode::Char('c') if self.comments.is_some() && !focused => {
                self.comment_buffer = Some(self.user_comment().to_owned());
            }
            KeyCode::Esc if focused && self.focus_panel.is_some() => {
                self.focus_panel = None;
                self.focus_scroll = 0;
            }
            KeyCode::Char('q') | KeyCode::Esc => return ModelOutputReviewAction::Quit,
            KeyCode::Char(action @ ('m' | 'w' | 'c')) if focused => {
                self.focus_panel = Some(match action {
                    'm' => 0,
                    'c' => 1,
                    _ => 2,
                });
                self.focus_scroll = 0;
                self.show_model_input = false;
            }
            KeyCode::Left | KeyCode::Char('h' | 'p') => {
                self.select_note(
                    (self.note + self.review.notes.len() - 1) % self.review.notes.len(),
                );
            }
            KeyCode::Right | KeyCode::Char('l' | 'n') => {
                self.select_note((self.note + 1) % self.review.notes.len());
            }
            KeyCode::Char('[') => self.select_model((self.model + models - 1) % models),
            KeyCode::Char(']') => self.select_model((self.model + 1) % models),
            KeyCode::Char(number @ '1'..='9') => self.select_model(number as usize - '1' as usize),
            KeyCode::Char('s') if !self.review.orderings.is_empty() => {
                self.ordering = (self.ordering + 1) % self.review.orderings.len();
                self.review.apply_ordering(self.ordering);
                self.select_note(self.note);
            }
            KeyCode::Char('i')
                if self.review.notes[self.note].model_input.is_some()
                    && (!focused || self.focus_panel == Some(0)) =>
            {
                self.show_model_input = !self.show_model_input;
                self.scroll[0] = 0;
                self.focus_scroll = 0;
            }
            KeyCode::Tab if !focused => self.panel = (self.panel + 1) % 3,
            KeyCode::BackTab if !focused => self.panel = (self.panel + 2) % 3,
            KeyCode::Up | KeyCode::Char('k') => *scroll = scroll.saturating_sub(1),
            KeyCode::Down | KeyCode::Char('j') => *scroll = scroll.saturating_add(1),
            KeyCode::PageUp => *scroll = scroll.saturating_sub(half_page.saturating_mul(2)),
            KeyCode::PageDown => *scroll = scroll.saturating_add(half_page.saturating_mul(2)),
            KeyCode::Home | KeyCode::Char('g') => *scroll = 0,
            KeyCode::End | KeyCode::Char('G') => *scroll = u16::MAX,
            _ => {}
        }
        ModelOutputReviewAction::None
    }

    fn render_summary(&mut self, frame: &mut Frame<'_>) {
        let note = &self.review.notes[self.note];
        let result = &note.results[0];
        let rows = Layout::vertical([
            Constraint::Length(2),
            Constraint::Min(4),
            Constraint::Length(2),
        ])
        .split(frame.area());
        frame.render_widget(
            Paragraph::new(format!(
                "{} {} of {}",
                terminal_safe(self.review.labels.item.as_deref().unwrap_or("Item")),
                self.note + 1,
                self.review.notes.len()
            ))
            .style(accent_style()),
            rows[0],
        );
        let (title, content, controls) = match self.focus_panel {
            None => (
                "Question",
                note.summary.as_deref().expect("summary view"),
                "m Masks   w Why merged?   q Quit",
            ),
            Some(0) => (
                if self.show_model_input {
                    "Full posts"
                } else {
                    "Masks · original groups"
                },
                if self.show_model_input {
                    note.model_input.as_deref().unwrap_or(&note.text)
                } else {
                    &note.text
                },
                "↑/↓ Scroll   i Masks/full posts   Esc Back   q Quit",
            ),
            Some(1) => (
                "Resulting connections",
                result.output.as_str(),
                "↑/↓ Scroll   Esc Back   q Quit",
            ),
            Some(_) => (
                "Why merged?",
                result.comment.as_str(),
                "↑/↓ Scroll   c Connections   Esc Back   q Quit",
            ),
        };
        render_scrollable_panel(
            frame,
            rows[1],
            title,
            &terminal_safe(content),
            &mut self.focus_scroll,
            &mut self.focus_half_page,
            true,
        );
        frame.render_widget(
            Paragraph::new(vec![
                Line::from(controls),
                Line::from(if self.comments.is_some() {
                    "←/→ Previous/next   e Your comment"
                } else {
                    "←/→ Previous/next   Read-only"
                }),
            ])
            .style(secondary_style()),
            rows[2],
        );
    }

    pub fn render(&mut self, frame: &mut Frame<'_>) {
        let area = frame.area();
        if let Some(buffer) = &self.comment_buffer {
            let rows = Layout::vertical([Constraint::Min(1), Constraint::Length(3)]).split(area);
            frame.render_widget(
                Paragraph::new(format!(
                    "Your comment · {} · {}\n\n{}",
                    terminal_safe(&self.review.notes[self.note].id),
                    terminal_safe(&self.review.notes[self.note].results[self.model].model),
                    terminal_safe(buffer),
                ))
                .wrap(Wrap { trim: false }),
                rows[0],
            );
            frame.render_widget(
                Paragraph::new(format!(
                    "{}\nEnter Save · Esc Cancel · Backspace Delete · Paste supported",
                    self.comment_error
                        .as_deref()
                        .map(terminal_safe)
                        .unwrap_or_default(),
                )),
                rows[1],
            );
            return;
        }
        if area.width < MIN_WIDTH || area.height < MIN_HEIGHT {
            frame.render_widget(
                Paragraph::new("Resize to at least 72 × 24.\nq / Esc / Ctrl-C exits."),
                area,
            );
            return;
        }
        if self.review.notes[self.note].summary.is_some() {
            self.render_summary(frame);
            return;
        }
        let note = &self.review.notes[self.note];
        let result = &note.results[self.model];
        let choices = Line::from(
            note.results
                .iter()
                .enumerate()
                .flat_map(|(index, result)| {
                    let name = format!("{} {}", index + 1, terminal_safe(&result.model));
                    let choice = if index == self.model {
                        Span::styled(name, accent_style())
                    } else {
                        Span::raw(name)
                    };
                    [Span::raw(if index == 0 { "" } else { "  ·  " }), choice]
                })
                .collect::<Vec<_>>(),
        );
        let choices_height = Paragraph::new(choices.clone())
            .wrap(Wrap { trim: false })
            .line_count(area.width)
            .clamp(1, 3) as u16;
        let header_height = if self.review.orderings.is_empty() {
            2
        } else {
            3
        };
        let rows = Layout::vertical([
            Constraint::Length(header_height + choices_height),
            Constraint::Min(12),
            Constraint::Length(3),
        ])
        .split(area);
        let header = Layout::vertical([Constraint::Length(header_height), Constraint::Min(1)])
            .split(rows[0]);
        let mut heading = vec![
            Line::styled(
                format!(
                    "{} · {}",
                    if self.comments.is_some() {
                        "Review"
                    } else {
                        "Read-only"
                    },
                    terminal_safe(&self.review.title)
                ),
                accent_style(),
            ),
            Line::from(format!(
                "{} · {} of {} · {}",
                terminal_safe(&note.id),
                self.note + 1,
                self.review.notes.len(),
                terminal_safe(&note.title)
            )),
        ];
        if let Some(ordering) = self.review.orderings.get(self.ordering) {
            heading.push(Line::from(format!(
                "Order: {} · s: change order, keep position",
                terminal_safe(&ordering.name)
            )));
        }
        frame.render_widget(Paragraph::new(heading), header[0]);
        frame.render_widget(
            Paragraph::new(choices).wrap(Wrap { trim: false }),
            header[1],
        );
        let panes = if area.width >= 110 {
            let vertical = Layout::vertical([
                Constraint::Min(8),
                Constraint::Length((rows[1].height / 4).max(4)),
            ])
            .split(rows[1]);
            let columns =
                Layout::horizontal([Constraint::Percentage(45), Constraint::Percentage(55)])
                    .split(vertical[0]);
            [columns[0], columns[1], vertical[1]]
        } else {
            let stacked = Layout::vertical([
                Constraint::Ratio(1, 3),
                Constraint::Ratio(4, 9),
                Constraint::Ratio(2, 9),
            ])
            .split(rows[1]);
            [stacked[0], stacked[1], stacked[2]]
        };
        let labels = &self.review.labels;
        let source_label = labels.source.as_deref().unwrap_or("Complete note");
        let alternate_label = labels.alternate_source.as_deref().unwrap_or("Model input");
        let (note_title, note_text) = match (self.show_model_input, &note.model_input) {
            (true, Some(input)) => (format!("{alternate_label} · i: {source_label}"), input),
            (false, Some(_)) => (format!("{source_label} · i: {alternate_label}"), &note.text),
            _ => (source_label.to_owned(), &note.text),
        };
        let output_title = labels
            .output
            .clone()
            .unwrap_or_else(|| format!("{} output", result.model));
        let comments = if self.comments.is_some() {
            format!(
                "{}\n\nYour comment:\n{}",
                result.comment,
                if self.user_comment().is_empty() {
                    "(none — c to add)"
                } else {
                    self.user_comment()
                }
            )
        } else {
            result.comment.clone()
        };
        for (panel, title, content) in [
            (0, note_title.as_str(), note_text.as_str()),
            (1, output_title.as_str(), result.output.as_str()),
            (
                2,
                labels.comment.as_deref().unwrap_or("My comments"),
                comments.as_str(),
            ),
        ] {
            render_scrollable_panel(
                frame,
                panes[panel],
                &terminal_safe(title),
                &terminal_safe(content),
                &mut self.scroll[panel],
                &mut self.half_page_lines[panel],
                self.panel == panel,
            );
        }
        frame.render_widget(
            Paragraph::new(vec![
                Line::from(format!(
                    "1–4 / [ ] {}   ←/→ h/l n/p {}   Tab / Shift-Tab Pane",
                    terminal_safe(labels.variant.as_deref().unwrap_or("Model")),
                    terminal_safe(labels.item.as_deref().unwrap_or("Note"))
                )),
                Line::from("↑/↓ j/k Scroll   PgUp/Dn Page   Ctrl-U/D Half-page   g/G Top/end"),
                Line::from(if self.comments.is_some() {
                    "c/e Add/edit comment   i Model input   q / Esc Exit"
                } else if labels.source.is_some() {
                    "i Toggle left pane   q / Esc / Ctrl-C Exit   No saved decisions"
                } else {
                    "i Original/model input   q / Esc / Ctrl-C Exit   No saved decisions"
                }),
            ])
            .style(secondary_style()),
            rows[2],
        );
    }
}

impl InteractiveReviewModel for ModelOutputReview {
    type Action = ModelOutputReviewAction;

    fn none_action() -> Self::Action {
        ModelOutputReviewAction::None
    }
    fn pause_action() -> Self::Action {
        ModelOutputReviewAction::Quit
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
