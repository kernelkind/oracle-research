//! Full-screen review and navigation interfaces for the reference map.

use std::io::{self, Stdout};
use std::time::Duration;

use crossterm::cursor::{Hide, Show};
use crossterm::event::{
    self, DisableBracketedPaste, EnableBracketedPaste, Event, KeyCode, KeyEventKind, KeyModifiers,
};
use crossterm::execute;
use crossterm::terminal::{
    EnterAlternateScreen, LeaveAlternateScreen, disable_raw_mode, enable_raw_mode,
};
use ratatui::Frame;
use ratatui::Terminal;
use ratatui::backend::CrosstermBackend;
use ratatui::layout::{Constraint, Direction, Layout, Rect};
use ratatui::style::{Color, Modifier, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Borders, List, ListItem, ListState, Padding, Paragraph, Wrap};

use crate::reference_map::{ApprovedHierarchy, ReviewOutcome};
use crate::snapshot::{Error, Result};
use crate::subject_navigation::{NavigationHierarchy, SubjectNavigation};

pub(crate) const MIN_WIDTH: u16 = 72;
pub(crate) const MIN_HEIGHT: u16 = 24;
const MAX_CONTENT_WIDTH: u16 = 100;
const PAGE_LINES: u16 = 10;

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ApprovalEvidence {
    pub title: String,
    pub annotation: String,
    pub body: String,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ApprovalGuidance {
    pub title: String,
    pub body: String,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum ApprovalEvidenceLayout {
    Paged(Vec<ApprovalEvidence>),
    Stacked {
        top: ApprovalEvidence,
        bottom: ApprovalEvidence,
    },
}

impl ApprovalEvidenceLayout {
    fn len(&self) -> usize {
        match self {
            Self::Paged(evidence) => evidence.len(),
            Self::Stacked { .. } => 2,
        }
    }

    fn is_empty(&self) -> bool {
        self.len() == 0
    }

    fn is_paged(&self) -> bool {
        matches!(self, Self::Paged(_))
    }

    fn get(&self, index: usize) -> Option<&ApprovalEvidence> {
        match self {
            Self::Paged(evidence) => evidence.get(index),
            Self::Stacked { top, bottom } => match index {
                0 => Some(top),
                1 => Some(bottom),
                _ => None,
            },
        }
    }

    fn iter_mut(&mut self) -> Box<dyn Iterator<Item = &mut ApprovalEvidence> + '_> {
        match self {
            Self::Paged(evidence) => Box::new(evidence.iter_mut()),
            Self::Stacked { top, bottom } => Box::new([top, bottom].into_iter()),
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ApprovalScreen {
    pub heading: String,
    pub title: Option<String>,
    pub scope: String,
    pub approve_label: String,
    pub reject_label: String,
    pub rejection_help: String,
    pub guidance: Option<ApprovalGuidance>,
    pub evidence: ApprovalEvidenceLayout,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum ApprovalTuiAction {
    None,
    Submit {
        outcome: ReviewOutcome,
        comment: String,
    },
    SaveComment {
        comment: String,
    },
    Skip {
        comment: String,
    },
    PreviousItem,
    NextItem,
    Pause,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum ApprovalInteraction {
    Production,
    PromptIteration,
}

pub(crate) trait InteractiveReviewModel {
    type Action: Eq;

    fn none_action() -> Self::Action;
    fn pause_action() -> Self::Action;
    fn handle_terminal_event(&mut self, event: Event) -> Self::Action;
    fn render_terminal(&mut self, frame: &mut Frame<'_>);
}

#[derive(Clone, Debug)]
pub struct ApprovalTuiModel {
    screen: ApprovalScreen,
    interaction: ApprovalInteraction,
    evidence_index: usize,
    evidence_scrolls: Vec<u16>,
    guidance_scroll: u16,
    guidance_visible: bool,
    half_page_lines: u16,
    pending_outcome: Option<ReviewOutcome>,
    comment: String,
    comment_before_edit: String,
    editing_prompt_comment: bool,
    interaction_enabled: bool,
    item_navigation: bool,
    compact_title: bool,
    title_comment: bool,
    stacked_review: bool,
}

impl ApprovalTuiModel {
    pub fn new(screen: ApprovalScreen) -> Self {
        Self::with_interaction(screen, ApprovalInteraction::Production, String::new())
    }

    pub fn new_prompt_iteration(screen: ApprovalScreen, comment: String) -> Self {
        Self::with_interaction(screen, ApprovalInteraction::PromptIteration, comment)
    }

    pub fn new_navigable_prompt_iteration(screen: ApprovalScreen, comment: String) -> Self {
        let mut model = Self::new_prompt_iteration(screen, comment);
        model.item_navigation = true;
        model
    }

    /// Keep every evidence title and independently scrollable box visible together.
    pub fn new_navigable_stacked_review(screen: ApprovalScreen, comment: String) -> Self {
        let mut model = Self::new_navigable_prompt_iteration(screen, comment);
        model.stacked_review = true;
        model
    }

    pub fn new_title_review(screen: ApprovalScreen, comment: String) -> Self {
        let mut model = Self::new_navigable_prompt_iteration(screen, comment);
        model.compact_title = true;
        model
    }

    /// Display supplementary assistant text separately from masks and user comments.
    pub fn new_title_review_with_comment(
        mut screen: ApprovalScreen,
        user_comment: String,
        assessment_summary: &str,
        assistant_comment: &str,
    ) -> Self {
        if let Some(guidance) = &mut screen.guidance {
            guidance.body.push_str(&format!(
                "\n\nMy assessment: {assessment_summary}\n\nMy comment is supplementary. Your saved decision applies to the original title review, not to my later comment."
            ));
        }
        let mut masks = screen.evidence.get(0).expect("title review masks").clone();
        masks.annotation = format!("My assessment: {assessment_summary}");
        screen.evidence = ApprovalEvidenceLayout::Stacked {
            top: masks,
            bottom: ApprovalEvidence {
                title: "My comment".into(),
                annotation: String::new(),
                body: assistant_comment.into(),
            },
        };
        let mut model = Self::new_title_review(screen, user_comment);
        model.title_comment = true;
        model
    }

    fn with_interaction(
        mut screen: ApprovalScreen,
        interaction: ApprovalInteraction,
        comment: String,
    ) -> Self {
        screen.heading = terminal_safe(&screen.heading);
        screen.title = screen.title.map(|title| terminal_safe(&title));
        screen.scope = terminal_safe(&screen.scope);
        screen.approve_label = terminal_safe(&screen.approve_label);
        screen.reject_label = terminal_safe(&screen.reject_label);
        screen.rejection_help = terminal_safe(&screen.rejection_help);
        if let Some(guidance) = &mut screen.guidance {
            guidance.title = terminal_safe(&guidance.title);
            guidance.body = terminal_safe(&guidance.body);
        }
        for evidence in screen.evidence.iter_mut() {
            evidence.title = terminal_safe(&evidence.title);
            evidence.annotation = terminal_safe(&evidence.annotation);
            evidence.body = terminal_safe(&evidence.body);
        }
        let evidence_scrolls = vec![0; screen.evidence.len()];
        Self {
            screen,
            interaction,
            evidence_index: 0,
            evidence_scrolls,
            guidance_scroll: 0,
            guidance_visible: false,
            half_page_lines: 1,
            pending_outcome: None,
            comment: terminal_safe(&comment),
            comment_before_edit: String::new(),
            editing_prompt_comment: false,
            interaction_enabled: true,
            item_navigation: false,
            compact_title: false,
            title_comment: false,
            stacked_review: false,
        }
    }

    pub fn handle_event(&mut self, event: Event) -> ApprovalTuiAction {
        if is_control_c_event(&event) {
            return ApprovalTuiAction::Pause;
        }
        if !self.interaction_enabled {
            return ApprovalTuiAction::None;
        }
        if self.editing_prompt_comment {
            return self.handle_prompt_comment_event(event);
        }
        if self.pending_outcome.is_some() {
            return self.handle_comment_event(event);
        }
        let Event::Key(key) = event else {
            return ApprovalTuiAction::None;
        };
        if key.kind != KeyEventKind::Press {
            return ApprovalTuiAction::None;
        }
        if key.modifiers == KeyModifiers::CONTROL {
            match key.code {
                KeyCode::Char('d' | 'D') => {
                    if self.guidance_visible {
                        self.guidance_scroll =
                            self.guidance_scroll.saturating_add(self.half_page_lines);
                    } else {
                        let half_page_lines = self.half_page_lines;
                        if let Some(scroll) = self.evidence_scrolls.get_mut(self.evidence_index) {
                            *scroll = scroll.saturating_add(half_page_lines);
                        }
                    }
                }
                KeyCode::Char('u' | 'U') => {
                    if self.guidance_visible {
                        self.guidance_scroll =
                            self.guidance_scroll.saturating_sub(self.half_page_lines);
                    } else {
                        let half_page_lines = self.half_page_lines;
                        if let Some(scroll) = self.evidence_scrolls.get_mut(self.evidence_index) {
                            *scroll = scroll.saturating_sub(half_page_lines);
                        }
                    }
                }
                _ => {}
            }
            return ApprovalTuiAction::None;
        }
        if has_command_modifier(key.modifiers) {
            return ApprovalTuiAction::None;
        }
        if self.guidance_visible {
            match key.code {
                KeyCode::Char('b' | 'B') if self.compact_title => {
                    self.guidance_visible = false;
                    self.guidance_scroll = 0;
                }
                KeyCode::Char('?') | KeyCode::Esc => {
                    self.guidance_visible = false;
                    self.guidance_scroll = 0;
                }
                KeyCode::Down | KeyCode::Char('j' | 'J') => {
                    self.guidance_scroll = self.guidance_scroll.saturating_add(1);
                }
                KeyCode::Up | KeyCode::Char('k' | 'K') => {
                    self.guidance_scroll = self.guidance_scroll.saturating_sub(1);
                }
                KeyCode::PageDown => {
                    self.guidance_scroll = self.guidance_scroll.saturating_add(PAGE_LINES);
                }
                KeyCode::PageUp => {
                    self.guidance_scroll = self.guidance_scroll.saturating_sub(PAGE_LINES);
                }
                KeyCode::Home => self.guidance_scroll = 0,
                _ => {}
            }
            return ApprovalTuiAction::None;
        }
        match key.code {
            KeyCode::Char('b' | 'B') if self.compact_title && self.screen.guidance.is_some() => {
                self.guidance_visible = true;
                self.guidance_scroll = 0;
            }
            KeyCode::Char('?') if self.screen.guidance.is_some() => {
                self.guidance_visible = true;
                self.guidance_scroll = 0;
            }
            KeyCode::Char('a' | 'A') => {
                if self.interaction == ApprovalInteraction::PromptIteration {
                    return ApprovalTuiAction::Submit {
                        outcome: ReviewOutcome::Approved,
                        comment: self.comment.trim().to_owned(),
                    };
                }
                self.pending_outcome = Some(ReviewOutcome::Approved);
                self.comment.clear();
            }
            KeyCode::Char('r' | 'R') => {
                if self.interaction == ApprovalInteraction::PromptIteration {
                    return ApprovalTuiAction::Submit {
                        outcome: ReviewOutcome::Rejected,
                        comment: self.comment.trim().to_owned(),
                    };
                }
                self.pending_outcome = Some(ReviewOutcome::Rejected);
                self.comment.clear();
            }
            KeyCode::Char('c' | 'C')
                if self.interaction == ApprovalInteraction::PromptIteration =>
            {
                self.comment_before_edit.clone_from(&self.comment);
                self.editing_prompt_comment = true;
            }
            KeyCode::Char('s' | 'S')
                if self.interaction == ApprovalInteraction::PromptIteration =>
            {
                return ApprovalTuiAction::Skip {
                    comment: self.comment.trim().to_owned(),
                };
            }
            KeyCode::Left if self.item_navigation => return ApprovalTuiAction::PreviousItem,
            KeyCode::Right if self.item_navigation => return ApprovalTuiAction::NextItem,
            KeyCode::Tab | KeyCode::Right => self.next_evidence(),
            KeyCode::BackTab | KeyCode::Left => self.previous_evidence(),
            KeyCode::Down | KeyCode::Char('j' | 'J') => {
                if let Some(scroll) = self.evidence_scrolls.get_mut(self.evidence_index) {
                    *scroll = scroll.saturating_add(1);
                }
            }
            KeyCode::Up | KeyCode::Char('k' | 'K') => {
                if let Some(scroll) = self.evidence_scrolls.get_mut(self.evidence_index) {
                    *scroll = scroll.saturating_sub(1);
                }
            }
            KeyCode::PageDown => {
                if let Some(scroll) = self.evidence_scrolls.get_mut(self.evidence_index) {
                    *scroll = scroll.saturating_add(PAGE_LINES);
                }
            }
            KeyCode::PageUp => {
                if let Some(scroll) = self.evidence_scrolls.get_mut(self.evidence_index) {
                    *scroll = scroll.saturating_sub(PAGE_LINES);
                }
            }
            KeyCode::Home => {
                if let Some(scroll) = self.evidence_scrolls.get_mut(self.evidence_index) {
                    *scroll = 0;
                }
            }
            _ => {}
        }
        ApprovalTuiAction::None
    }

    fn handle_prompt_comment_event(&mut self, event: Event) -> ApprovalTuiAction {
        match event {
            Event::Paste(text) => {
                self.comment.push_str(&terminal_safe(&text));
            }
            Event::Key(key) if key.kind == KeyEventKind::Press => match key.code {
                KeyCode::Enter => {
                    self.comment = self.comment.trim().to_owned();
                    self.comment_before_edit.clear();
                    self.editing_prompt_comment = false;
                    return ApprovalTuiAction::SaveComment {
                        comment: self.comment.clone(),
                    };
                }
                KeyCode::Esc => {
                    self.comment.clone_from(&self.comment_before_edit);
                    self.comment_before_edit.clear();
                    self.editing_prompt_comment = false;
                }
                KeyCode::Backspace if !has_command_modifier(key.modifiers) => {
                    self.comment.pop();
                }
                KeyCode::Char(character) if !has_command_modifier(key.modifiers) => {
                    self.comment.push(character);
                }
                _ => {}
            },
            _ => {}
        }
        ApprovalTuiAction::None
    }

    fn handle_comment_event(&mut self, event: Event) -> ApprovalTuiAction {
        match event {
            Event::Paste(text) => {
                self.comment.push_str(&terminal_safe(&text));
                ApprovalTuiAction::None
            }
            Event::Key(key) if key.kind == KeyEventKind::Press => match key.code {
                KeyCode::Enter
                    if self.pending_outcome == Some(ReviewOutcome::Rejected)
                        && self.comment.trim().is_empty() =>
                {
                    ApprovalTuiAction::None
                }
                KeyCode::Enter => ApprovalTuiAction::Submit {
                    outcome: self
                        .pending_outcome
                        .expect("comment entry always has a pending decision"),
                    comment: self.comment.trim().to_owned(),
                },
                KeyCode::Esc => {
                    self.pending_outcome = None;
                    self.comment.clear();
                    ApprovalTuiAction::None
                }
                KeyCode::Backspace if !has_command_modifier(key.modifiers) => {
                    self.comment.pop();
                    ApprovalTuiAction::None
                }
                KeyCode::Char(character) if !has_command_modifier(key.modifiers) => {
                    self.comment.push(character);
                    ApprovalTuiAction::None
                }
                _ => ApprovalTuiAction::None,
            },
            _ => ApprovalTuiAction::None,
        }
    }

    fn next_evidence(&mut self) {
        if self.screen.evidence.is_empty() {
            return;
        }
        self.evidence_index = (self.evidence_index + 1) % self.screen.evidence.len();
        if self.screen.evidence.is_paged() && !self.stacked_review {
            self.evidence_scrolls[self.evidence_index] = 0;
        }
    }

    fn previous_evidence(&mut self) {
        if self.screen.evidence.is_empty() {
            return;
        }
        self.evidence_index = if self.evidence_index == 0 {
            self.screen.evidence.len() - 1
        } else {
            self.evidence_index - 1
        };
        if self.screen.evidence.is_paged() && !self.stacked_review {
            self.evidence_scrolls[self.evidence_index] = 0;
        }
    }

    fn navigation_controls(&self, exit_label: &'static str) -> Vec<Span<'static>> {
        let mut controls = Vec::new();
        if self.item_navigation {
            controls.extend([
                Span::styled("[←/→]", accent_style()),
                Span::styled(" Previous/next item  ", secondary_style()),
            ]);
        }
        if self.screen.evidence.len() > 1 {
            let target = match &self.screen.evidence {
                ApprovalEvidenceLayout::Paged(_) if !self.stacked_review => " Evidence  ",
                _ => " Panel  ",
            };
            controls.extend([
                Span::styled(
                    if self.item_navigation {
                        "[Tab/Shift-Tab]"
                    } else {
                        "[Tab/←/→]"
                    },
                    accent_style(),
                ),
                Span::styled(target, secondary_style()),
            ]);
        }
        if let Some(guidance) = &self.screen.guidance {
            controls.extend([
                Span::styled("[?]", accent_style()),
                Span::styled(format!(" {}  ", guidance.title), secondary_style()),
            ]);
        }
        controls.extend([
            Span::styled(
                if self.stacked_review {
                    "[j/k]"
                } else {
                    "[↑/↓]"
                },
                accent_style(),
            ),
            Span::styled(" Scroll  ", secondary_style()),
            Span::styled("[Ctrl-D/U]", accent_style()),
            Span::styled(" Half-page  ", secondary_style()),
            Span::styled("[Ctrl-C]", accent_style()),
            Span::styled(exit_label, secondary_style()),
        ]);
        controls
    }

    pub fn render(&mut self, frame: &mut Frame<'_>) {
        let area = frame.area();
        self.interaction_enabled = area.width >= MIN_WIDTH && area.height >= MIN_HEIGHT;
        if !self.interaction_enabled {
            render_too_small(frame, area);
            return;
        }
        let area = centered(area);
        if self.stacked_review {
            self.render_stacked_review(frame, area);
            return;
        }
        if self.compact_title {
            self.render_title_review(frame, area);
            return;
        }
        let footer_height = if self.pending_outcome.is_some() {
            8
        } else if self.editing_prompt_comment {
            6
        } else {
            4
        };
        let scope = Paragraph::new(self.screen.scope.as_str())
            .style(secondary_style())
            .wrap(Wrap { trim: false });
        let scope_height = if self.screen.scope.is_empty() {
            0
        } else {
            u16::try_from(scope.line_count(area.width))
                .unwrap_or(u16::MAX)
                .clamp(3, 7)
        };
        let annotation_text = if self.guidance_visible {
            ""
        } else {
            self.screen
                .evidence
                .get(self.evidence_index)
                .map_or("", |evidence| evidence.annotation.as_str())
        };
        let annotation = Paragraph::new(annotation_text)
            .style(secondary_style())
            .wrap(Wrap { trim: false });
        let title = self.screen.title.as_deref().map(|title| {
            Paragraph::new(title)
                .style(accent_style())
                .wrap(Wrap { trim: false })
        });
        let maximum_title_height = area
            .height
            .saturating_sub(1 + scope_height + 6 + footer_height);
        let title_height = title.as_ref().map_or(0, |title| {
            u16::try_from(title.line_count(area.width))
                .unwrap_or(u16::MAX)
                .saturating_add(1)
                .min(maximum_title_height)
        });
        let maximum_annotation_height = area
            .height
            .saturating_sub(1 + title_height + scope_height + 6 + footer_height);
        let annotation_height = if annotation_text.is_empty() {
            0
        } else {
            u16::try_from(annotation.line_count(area.width))
                .unwrap_or(u16::MAX)
                .min(maximum_annotation_height)
        };
        let rows = Layout::default()
            .direction(Direction::Vertical)
            .constraints([
                Constraint::Length(1),
                Constraint::Length(title_height),
                Constraint::Length(scope_height),
                Constraint::Min(6),
                Constraint::Length(annotation_height),
                Constraint::Length(footer_height),
            ])
            .split(area);
        frame.render_widget(
            Paragraph::new(self.screen.heading.as_str()).style(secondary_style()),
            rows[0],
        );
        if let Some(title) = title {
            frame.render_widget(title, rows[1]);
        }
        frame.render_widget(scope, rows[2]);

        if self.guidance_visible {
            let guidance = self
                .screen
                .guidance
                .as_ref()
                .expect("visible guidance must be present");
            render_scrollable_panel(
                frame,
                rows[3],
                &guidance.title,
                &guidance.body,
                &mut self.guidance_scroll,
                &mut self.half_page_lines,
                false,
            );
        } else if let ApprovalEvidenceLayout::Stacked { top, bottom } = &self.screen.evidence {
            let panels = stacked_evidence_areas(rows[3], &bottom.body);
            let evidence = [top, bottom];
            for (index, area) in panels.into_iter().enumerate() {
                let evidence = evidence[index];
                let mut inactive_half_page_lines = 1;
                let half_page_lines = if index == self.evidence_index {
                    &mut self.half_page_lines
                } else {
                    &mut inactive_half_page_lines
                };
                render_scrollable_panel(
                    frame,
                    area,
                    &evidence.title,
                    &evidence.body,
                    &mut self.evidence_scrolls[index],
                    half_page_lines,
                    index == self.evidence_index,
                );
            }
            frame.render_widget(annotation, rows[4]);
        } else if let Some(evidence) = self.screen.evidence.get(self.evidence_index) {
            let title = if self.screen.evidence.len() > 1 {
                format!(
                    "{} · {} of {}",
                    evidence.title,
                    self.evidence_index + 1,
                    self.screen.evidence.len()
                )
            } else {
                evidence.title.clone()
            };
            render_scrollable_panel(
                frame,
                rows[3],
                &title,
                &evidence.body,
                &mut self.evidence_scrolls[self.evidence_index],
                &mut self.half_page_lines,
                false,
            );
            frame.render_widget(annotation, rows[4]);
        } else {
            frame.render_widget(
                Paragraph::new("No evidence was provided.")
                    .block(Block::default().borders(Borders::ALL)),
                rows[3],
            );
        }

        let footer = self.approval_footer();
        let rendered_lines = footer.line_count(rows[5].width);
        let footer_scroll = rendered_lines
            .saturating_sub(rows[5].height as usize)
            .try_into()
            .unwrap_or(u16::MAX);
        frame.render_widget(footer.scroll((footer_scroll, 0)), rows[5]);
    }

    fn approval_footer(&self) -> Paragraph<'static> {
        let footer = if self.guidance_visible {
            vec![
                Line::from(vec![
                    Span::styled("[?]/[Esc]", accent_style()),
                    Span::styled(" Back to note", secondary_style()),
                ]),
                Line::from(vec![
                    Span::styled("[↑/↓]", accent_style()),
                    Span::styled(" Scroll  ", secondary_style()),
                    Span::styled("[Ctrl-D/U]", accent_style()),
                    Span::styled(" Half-page  ", secondary_style()),
                    Span::styled("[Ctrl-C]", accent_style()),
                    Span::styled(" Pause", secondary_style()),
                ]),
            ]
        } else if self.editing_prompt_comment {
            vec![
                Line::from(vec![
                    Span::styled(
                        if self.stacked_review {
                            "Your comment"
                        } else {
                            "Comment"
                        },
                        accent_style(),
                    ),
                    Span::styled(" (optional)", secondary_style()),
                ]),
                Line::raw(format!("> {}", self.comment)),
                Line::from(vec![
                    Span::styled("[Enter]", accent_style()),
                    Span::styled(" Save  ", secondary_style()),
                    Span::styled("[Esc]", accent_style()),
                    Span::styled(" Cancel", secondary_style()),
                ]),
            ]
        } else if let Some(outcome) = self.pending_outcome {
            let decision = match outcome {
                ReviewOutcome::Approved => "Approve",
                ReviewOutcome::Rejected => "Reject",
            };
            let comment_requirement = match outcome {
                ReviewOutcome::Approved => " (optional)",
                ReviewOutcome::Rejected => " (required)",
            };
            let mut lines = vec![Line::from(vec![
                Span::styled(format!("{decision} comment"), accent_style()),
                Span::styled(comment_requirement, secondary_style()),
            ])];
            if outcome == ReviewOutcome::Rejected {
                lines.extend(
                    self.screen
                        .rejection_help
                        .lines()
                        .map(|line| Line::styled(line.to_owned(), secondary_style())),
                );
            } else {
                lines.push(Line::raw(""));
            }
            lines.extend([
                Line::raw(format!("> {}", self.comment)),
                Line::from(vec![
                    Span::styled("[Enter]", accent_style()),
                    Span::styled(" Confirm  ", secondary_style()),
                    Span::styled("[Esc]", accent_style()),
                    Span::styled(" Cancel", secondary_style()),
                ]),
            ]);
            lines
        } else if self.interaction == ApprovalInteraction::PromptIteration {
            let navigation_controls = self.navigation_controls(" Save/exit");
            let mut lines = vec![
                Line::from(vec![
                    Span::styled("[A]", accent_style()),
                    Span::styled(
                        format!(" {}  ", self.screen.approve_label),
                        secondary_style(),
                    ),
                    Span::styled("[R]", accent_style()),
                    Span::styled(
                        format!(" {}  ", self.screen.reject_label),
                        secondary_style(),
                    ),
                    Span::styled("[C]", accent_style()),
                    Span::styled(
                        if self.stacked_review {
                            " Your comment  "
                        } else {
                            " Comment  "
                        },
                        secondary_style(),
                    ),
                    Span::styled("[S]", accent_style()),
                    Span::styled(" Skip", secondary_style()),
                ]),
                Line::from(navigation_controls),
            ];
            if !self.comment.is_empty() {
                lines.insert(
                    1,
                    Line::styled(
                        if self.stacked_review {
                            "Your comment saved · [C] Edit".to_owned()
                        } else {
                            format!("Comment: {}", self.comment)
                        },
                        secondary_style(),
                    ),
                );
            }
            lines
        } else {
            let navigation_controls = self.navigation_controls(" Pause");
            vec![
                Line::from(vec![
                    Span::styled("[A]", accent_style()),
                    Span::styled(
                        format!(" {}  ", self.screen.approve_label),
                        secondary_style(),
                    ),
                    Span::styled("[R]", accent_style()),
                    Span::styled(
                        format!(" {}  ", self.screen.reject_label),
                        secondary_style(),
                    ),
                ]),
                Line::from(navigation_controls),
            ]
        };
        Paragraph::new(footer).wrap(Wrap { trim: false })
    }

    fn render_stacked_review(&mut self, frame: &mut Frame<'_>, area: Rect) {
        let mut heading = vec![Line::styled(
            self.screen.heading.as_str(),
            secondary_style(),
        )];
        if let Some(title) = &self.screen.title {
            heading.push(Line::styled(title.as_str(), accent_style()));
        }
        if !self.screen.scope.is_empty() {
            heading.push(Line::raw(self.screen.scope.as_str()));
        }
        let heading = Paragraph::new(heading).wrap(Wrap { trim: false });
        let heading_height = u16::try_from(heading.line_count(area.width)).unwrap_or(u16::MAX);
        let footer = self.approval_footer();
        let footer_lines = u16::try_from(footer.line_count(area.width)).unwrap_or(u16::MAX);
        let footer_height = if self.editing_prompt_comment {
            footer_lines.min(5)
        } else {
            footer_lines
        };
        let titles: Vec<_> = (0..self.screen.evidence.len())
            .map(|index| {
                let evidence = self.screen.evidence.get(index).expect("evidence panel");
                let mut lines = vec![Line::styled(evidence.title.as_str(), accent_style())];
                if !evidence.annotation.is_empty() {
                    lines.push(Line::styled(
                        evidence.annotation.as_str(),
                        secondary_style(),
                    ));
                }
                Paragraph::new(lines).wrap(Wrap { trim: false })
            })
            .collect();
        let title_heights: Vec<_> = titles
            .iter()
            .map(|title| u16::try_from(title.line_count(area.width)).unwrap_or(u16::MAX))
            .collect();
        let title_height: u16 = title_heights.iter().copied().fold(0, u16::saturating_add);
        let minimum_panels = u16::try_from(titles.len())
            .unwrap_or(u16::MAX)
            .saturating_mul(3);
        let required_height = heading_height
            .saturating_add(footer_height)
            .saturating_add(title_height)
            .saturating_add(minimum_panels);
        if !self.guidance_visible && required_height > area.height {
            self.interaction_enabled = false;
            frame.render_widget(
                Paragraph::new(format!(
                    "Resize to at least {} × {required_height} to show all evidence titles, boxes and controls.",
                    area.width
                ))
                .wrap(Wrap { trim: false })
                .block(Block::default().borders(Borders::ALL).title("Terminal too small")),
                area,
            );
            return;
        }
        let rows = Layout::vertical([
            Constraint::Length(heading_height),
            Constraint::Min(0),
            Constraint::Length(footer_height),
        ])
        .split(area);
        frame.render_widget(heading, rows[0]);
        frame.render_widget(
            footer.scroll((footer_lines.saturating_sub(footer_height), 0)),
            rows[2],
        );

        if self.guidance_visible {
            let guidance = self.screen.guidance.as_ref().expect("visible guidance");
            render_scrollable_panel(
                frame,
                rows[1],
                &guidance.title,
                &guidance.body,
                &mut self.guidance_scroll,
                &mut self.half_page_lines,
                false,
            );
            return;
        }

        let panel_height = rows[1].height.saturating_sub(title_height);
        let desired_heights: Vec<_> = (0..self.screen.evidence.len())
            .map(|index| {
                let evidence = self.screen.evidence.get(index).expect("evidence panel");
                let lines = Paragraph::new(evidence.body.as_str())
                    .wrap(Wrap { trim: false })
                    .line_count(area.width.saturating_sub(4));
                u16::try_from(lines.saturating_add(2))
                    .unwrap_or(u16::MAX)
                    .max(3)
            })
            .collect();
        let mut panel_heights = vec![3_u16; self.screen.evidence.len()];
        let mut remaining = panel_height.saturating_sub(minimum_panels);
        // Give each box a visible body line, then share additional space among
        // boxes that still have hidden content. Short comments need no extra rows.
        while remaining > 0 {
            let mut expanded = false;
            for (height, desired) in panel_heights.iter_mut().zip(&desired_heights) {
                if *height < *desired && remaining > 0 {
                    *height += 1;
                    remaining -= 1;
                    expanded = true;
                }
            }
            if !expanded {
                break;
            }
        }
        let mut y = rows[1].y;
        for (index, ((title, title_height), panel_height)) in titles
            .into_iter()
            .zip(title_heights)
            .zip(panel_heights)
            .enumerate()
        {
            frame.render_widget(title, Rect::new(area.x, y, area.width, title_height));
            y = y.saturating_add(title_height);
            let evidence = self.screen.evidence.get(index).expect("evidence panel");
            let mut half_page_lines = 1;
            render_scrollable_panel(
                frame,
                Rect::new(area.x, y, area.width, panel_height),
                "",
                &evidence.body,
                &mut self.evidence_scrolls[index],
                &mut half_page_lines,
                index == self.evidence_index,
            );
            if index == self.evidence_index {
                self.half_page_lines = half_page_lines;
            }
            y = y.saturating_add(panel_height);
        }
    }

    fn render_title_review(&mut self, frame: &mut Frame<'_>, area: Rect) {
        if self.title_comment && !self.guidance_visible {
            self.render_title_review_with_comment(frame, area);
            return;
        }
        let title = Paragraph::new(self.screen.title.as_deref().unwrap_or_default())
            .style(accent_style())
            .wrap(Wrap { trim: false });
        let title_lines = title.line_count(area.width);
        // Keep masks and controls usable even when the raw response is very long.
        // Any shortened pinned text has an explicit route to its complete text.
        let title_height = title_lines.min(4) as u16;
        let title_shortened = title_lines > usize::from(title_height);
        let annotation = if self.guidance_visible {
            ""
        } else {
            self.screen
                .evidence
                .get(self.evidence_index)
                .map_or("", |evidence| evidence.annotation.as_str())
        };
        let assessment = Paragraph::new(annotation).wrap(Wrap { trim: false });
        let assessment_lines = if annotation.is_empty() {
            0
        } else {
            assessment.line_count(area.width)
        };
        let assessment_height = assessment_lines.min(3) as u16;
        let assessment_shortened = assessment_lines > usize::from(assessment_height);
        let footer_height = if self.editing_prompt_comment { 5 } else { 3 };
        let annotation_height = assessment_height + u16::from(assessment_shortened) + 1;
        let panel_content = if self.guidance_visible {
            self.screen
                .guidance
                .as_ref()
                .map(|guidance| guidance.body.as_str())
        } else {
            self.screen
                .evidence
                .get(self.evidence_index)
                .map(|evidence| evidence.body.as_str())
        }
        .unwrap_or_default();
        let panel_lines = Paragraph::new(panel_content)
            .wrap(Wrap { trim: false })
            .line_count(area.width.saturating_sub(4));
        let available_panel_height = area
            .height
            .saturating_sub(2 + title_height + 1 + 2 + annotation_height + footer_height);
        let panel_height = u16::try_from(panel_lines.saturating_add(2))
            .unwrap_or(u16::MAX)
            .min(available_panel_height)
            .max(4);
        let rows = Layout::vertical([
            Constraint::Length(2),
            Constraint::Length(title_height),
            Constraint::Length(1),
            Constraint::Length(2),
            Constraint::Length(panel_height),
            Constraint::Length(annotation_height),
            Constraint::Length(footer_height),
            Constraint::Min(0),
        ])
        .split(area);
        frame.render_widget(
            Paragraph::new(self.screen.heading.as_str()).style(secondary_style()),
            rows[0],
        );
        frame.render_widget(title, rows[1]);
        if title_shortened {
            frame.render_widget(
                Paragraph::new("… [B] Full title").style(secondary_style()),
                rows[2],
            );
        }
        frame.render_widget(Paragraph::new(self.screen.scope.as_str()), rows[3]);
        if self.guidance_visible {
            let guidance = self
                .screen
                .guidance
                .as_ref()
                .expect("visible comparison is present");
            render_scrollable_panel(
                frame,
                rows[4],
                &guidance.title,
                &guidance.body,
                &mut self.guidance_scroll,
                &mut self.half_page_lines,
                false,
            );
        } else if let Some(evidence) = self.screen.evidence.get(self.evidence_index) {
            render_scrollable_panel(
                frame,
                rows[4],
                &evidence.title,
                &evidence.body,
                &mut self.evidence_scrolls[self.evidence_index],
                &mut self.half_page_lines,
                false,
            );
        }
        let assessment_area = Rect {
            height: assessment_height,
            ..rows[5]
        };
        frame.render_widget(assessment, assessment_area);
        if assessment_shortened {
            frame.render_widget(
                Paragraph::new("… [B] Full assessment").style(secondary_style()),
                Rect {
                    y: rows[5].y + assessment_height,
                    height: 1,
                    ..rows[5]
                },
            );
        }
        let footer = self.title_review_footer();
        let scroll = footer
            .line_count(rows[6].width)
            .saturating_sub(rows[6].height as usize);
        frame.render_widget(
            footer.scroll((u16::try_from(scroll).unwrap_or(u16::MAX), 0)),
            rows[6],
        );
    }

    fn render_title_review_with_comment(&mut self, frame: &mut Frame<'_>, area: Rect) {
        let title = Paragraph::new(self.screen.title.as_deref().unwrap_or_default())
            .style(accent_style())
            .wrap(Wrap { trim: false });
        let title_lines = title.line_count(area.width);
        let title_height = title_lines.min(2) as u16;
        let title_shortened = title_lines > usize::from(title_height);
        let masks = self.screen.evidence.get(0).expect("title masks");
        let comment = self
            .screen
            .evidence
            .get(1)
            .expect("assistant title comment");
        let assessment = Paragraph::new(masks.annotation.as_str()).wrap(Wrap { trim: false });
        let assessment_lines = assessment.line_count(area.width);
        let assessment_height = assessment_lines.min(2) as u16;
        let assessment_shortened = assessment_lines > usize::from(assessment_height);
        let header_height = 3 + title_height + u16::from(title_shortened);
        let annotation_height = assessment_height + u16::from(assessment_shortened);
        let footer_height = 3;
        let available = area
            .height
            .saturating_sub(header_height + annotation_height + footer_height);
        let content_width = area.width.saturating_sub(4);
        let panel_height = |body: &str| {
            u16::try_from(
                Paragraph::new(body)
                    .wrap(Wrap { trim: false })
                    .line_count(content_width)
                    .saturating_add(2),
            )
            .unwrap_or(u16::MAX)
        };
        let mask_desired = panel_height(&masks.body);
        let comment_desired = panel_height(&comment.body);
        // Fit short content tightly. For long text, keep both panes visible and
        // use the existing evidence focus/scroll state to reach every line.
        let mask_height = mask_desired
            .min(available.saturating_sub(comment_desired.min(available / 2)))
            .max(3);
        let comment_height = comment_desired
            .min(available.saturating_sub(mask_height))
            .max(3);
        let rows = Layout::vertical([
            Constraint::Length(1),
            Constraint::Length(title_height),
            Constraint::Length(u16::from(title_shortened)),
            Constraint::Length(2),
            Constraint::Length(mask_height),
            Constraint::Length(annotation_height),
            Constraint::Length(comment_height),
            Constraint::Length(footer_height),
            Constraint::Min(0),
        ])
        .split(area);
        frame.render_widget(
            Paragraph::new(self.screen.heading.as_str()).style(secondary_style()),
            rows[0],
        );
        frame.render_widget(title, rows[1]);
        if title_shortened {
            frame.render_widget(
                Paragraph::new("… [B] Full title").style(secondary_style()),
                rows[2],
            );
        }
        frame.render_widget(Paragraph::new(self.screen.scope.as_str()), rows[3]);
        for (index, row) in [(0, rows[4]), (1, rows[6])] {
            let evidence = self.screen.evidence.get(index).expect("title review pane");
            let mut half_page_lines = 1;
            render_scrollable_panel(
                frame,
                row,
                &evidence.title,
                &evidence.body,
                &mut self.evidence_scrolls[index],
                &mut half_page_lines,
                self.evidence_index == index,
            );
            if self.evidence_index == index {
                self.half_page_lines = half_page_lines;
            }
        }
        frame.render_widget(
            assessment,
            Rect {
                height: assessment_height,
                ..rows[5]
            },
        );
        if assessment_shortened {
            frame.render_widget(
                Paragraph::new("… [B] Full assessment").style(secondary_style()),
                Rect {
                    y: rows[5].y + assessment_height,
                    height: 1,
                    ..rows[5]
                },
            );
        }
        let footer = self.title_review_footer();
        let scroll = footer
            .line_count(rows[7].width)
            .saturating_sub(rows[7].height as usize);
        frame.render_widget(
            footer.scroll((u16::try_from(scroll).unwrap_or(u16::MAX), 0)),
            rows[7],
        );
    }

    fn title_review_footer(&self) -> Paragraph<'static> {
        let lines = if self.editing_prompt_comment {
            vec![
                Line::styled(
                    if self.title_comment {
                        "Your comment (optional)"
                    } else {
                        "Comment (optional)"
                    },
                    accent_style(),
                ),
                Line::raw(format!("> {}", self.comment)),
                Line::styled("[Enter] Save  [Esc] Cancel", secondary_style()),
            ]
        } else if self.guidance_visible {
            vec![Line::styled(
                "[B/Esc] Back  [↑/↓] Scroll  [Ctrl-C] Save/exit",
                secondary_style(),
            )]
        } else if self.title_comment {
            vec![
                Line::styled(
                    "[A] Approve  [R] Reject  [C] Your comment  [S] Skip",
                    accent_style(),
                ),
                Line::styled(
                    "[←/→] Previous/next  [↑/↓] Scroll  [Tab] Masks/My comment",
                    secondary_style(),
                ),
                Line::styled(
                    if self.comment.is_empty() {
                        "[B] Compare  [Ctrl-C] Save/exit"
                    } else {
                        "Your comment saved · [B] Compare  [Ctrl-C] Save/exit"
                    },
                    secondary_style(),
                ),
            ]
        } else {
            let mut lines = vec![
                Line::styled(
                    "[A] Approve  [R] Reject  [C] Comment  [S] Skip",
                    accent_style(),
                ),
                Line::styled(
                    "[←/→] Previous/next  [↑/↓] Scroll  [B] Compare  [Ctrl-C] Save/exit",
                    secondary_style(),
                ),
            ];
            if !self.comment.is_empty() {
                lines.push(Line::styled("Comment saved · [C] Edit", secondary_style()));
            }
            lines
        };
        Paragraph::new(lines).wrap(Wrap { trim: false })
    }
}

impl InteractiveReviewModel for ApprovalTuiModel {
    type Action = ApprovalTuiAction;

    fn none_action() -> Self::Action {
        ApprovalTuiAction::None
    }

    fn pause_action() -> Self::Action {
        ApprovalTuiAction::Pause
    }

    fn handle_terminal_event(&mut self, event: Event) -> Self::Action {
        self.handle_event(event)
    }

    fn render_terminal(&mut self, frame: &mut Frame<'_>) {
        self.render(frame);
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum NavigationTuiAction {
    None,
    Quit,
}

#[derive(Clone, Debug)]
pub struct ReferenceNavigationTuiModel {
    hierarchy: NavigationHierarchy,
    navigation: SubjectNavigation,
    scroll: u16,
    half_page_lines: u16,
    interaction_enabled: bool,
}

impl ReferenceNavigationTuiModel {
    pub fn new(hierarchy: ApprovedHierarchy) -> Result<Self> {
        Self::from_navigation_hierarchy(NavigationHierarchy::try_from(&hierarchy)?)
    }

    pub fn from_navigation_hierarchy(hierarchy: NavigationHierarchy) -> Result<Self> {
        let navigation = SubjectNavigation::new(&hierarchy)?;
        Ok(Self {
            hierarchy,
            navigation,
            scroll: 0,
            half_page_lines: 1,
            interaction_enabled: true,
        })
    }

    pub fn handle_event(&mut self, event: Event) -> NavigationTuiAction {
        if is_control_c_event(&event) {
            return NavigationTuiAction::Quit;
        }
        if !self.interaction_enabled {
            return NavigationTuiAction::None;
        }
        let Event::Key(key) = event else {
            return NavigationTuiAction::None;
        };
        if key.kind != KeyEventKind::Press {
            return NavigationTuiAction::None;
        }
        if key.code == KeyCode::Esc {
            return NavigationTuiAction::Quit;
        }
        if key.modifiers == KeyModifiers::CONTROL {
            match key.code {
                KeyCode::Char('d' | 'D') => {
                    self.scroll = self.scroll.saturating_add(self.half_page_lines);
                }
                KeyCode::Char('u' | 'U') => {
                    self.scroll = self.scroll.saturating_sub(self.half_page_lines);
                }
                _ => {}
            }
            return NavigationTuiAction::None;
        }
        if has_command_modifier(key.modifiers) {
            return NavigationTuiAction::None;
        }

        let leaf = self
            .hierarchy
            .node(self.navigation.current_node_id())
            .is_some_and(|node| node.is_leaf());
        match key.code {
            KeyCode::Backspace => {
                self.navigation.back();
                self.scroll = 0;
            }
            KeyCode::Enter if !leaf => {
                let _ = self.navigation.enter(&self.hierarchy);
                self.scroll = 0;
            }
            KeyCode::Down | KeyCode::Char('j' | 'J') if !leaf => {
                self.navigation.move_next(&self.hierarchy);
            }
            KeyCode::Up | KeyCode::Char('k' | 'K') if !leaf => {
                self.navigation.move_previous();
            }
            KeyCode::Right | KeyCode::Char('l' | 'L') if leaf => {
                self.navigation.move_next(&self.hierarchy);
                self.scroll = 0;
            }
            KeyCode::Left | KeyCode::Char('h' | 'H') if leaf => {
                self.navigation.move_previous();
                self.scroll = 0;
            }
            KeyCode::Down | KeyCode::Char('j' | 'J') if leaf => {
                self.scroll = self.scroll.saturating_add(1);
            }
            KeyCode::Up | KeyCode::Char('k' | 'K') if leaf => {
                self.scroll = self.scroll.saturating_sub(1);
            }
            KeyCode::PageDown if leaf => self.scroll = self.scroll.saturating_add(PAGE_LINES),
            KeyCode::PageUp if leaf => self.scroll = self.scroll.saturating_sub(PAGE_LINES),
            KeyCode::Home if leaf => self.scroll = 0,
            _ => {}
        }
        NavigationTuiAction::None
    }

    pub fn render(&mut self, frame: &mut Frame<'_>) {
        let area = frame.area();
        self.interaction_enabled = area.width >= MIN_WIDTH && area.height >= MIN_HEIGHT;
        if !self.interaction_enabled {
            render_too_small(frame, area);
            return;
        }
        let area = centered(area);
        let node = self
            .hierarchy
            .node(self.navigation.current_node_id())
            .expect("validated navigation node");
        if node.is_leaf() {
            self.render_leaf(frame, area);
        } else {
            self.render_subjects(frame, area);
        }
    }

    fn render_subjects(&self, frame: &mut Frame<'_>, area: Rect) {
        let node = self
            .hierarchy
            .node(self.navigation.current_node_id())
            .expect("validated navigation node");
        let breadcrumb = self
            .navigation
            .breadcrumb(&self.hierarchy)
            .expect("validated breadcrumb");
        let question = if breadcrumb.is_empty() {
            "What would you like to explore?".to_owned()
        } else {
            format!("{} — choose a narrower subject", breadcrumb.join(" > "))
        };
        let rows = Layout::default()
            .direction(Direction::Vertical)
            .constraints([
                Constraint::Length(2),
                Constraint::Min(6),
                Constraint::Length(2),
            ])
            .split(area);
        frame.render_widget(
            Paragraph::new(question)
                .style(accent_style())
                .wrap(Wrap { trim: false }),
            rows[0],
        );
        let items = node
            .children
            .iter()
            .map(|child| {
                let child = self.hierarchy.node(child).expect("validated child subject");
                ListItem::new(child.label.as_str())
            })
            .collect::<Vec<_>>();
        let mut state = ListState::default().with_selected(Some(self.navigation.selected_index()));
        frame.render_stateful_widget(
            List::new(items)
                .highlight_symbol("▶ ")
                .highlight_style(accent_style())
                .block(
                    Block::default()
                        .borders(Borders::ALL)
                        .border_style(border_style())
                        .padding(Padding::horizontal(1))
                        .title("Subjects")
                        .title_style(accent_style()),
                ),
            rows[1],
            &mut state,
        );
        frame.render_widget(
            Paragraph::new(Line::from(vec![
                Span::styled("[↑/↓]", accent_style()),
                Span::styled(" Choose  ", secondary_style()),
                Span::styled("[Enter]", accent_style()),
                Span::styled(" Open  ", secondary_style()),
                Span::styled("[Backspace]", accent_style()),
                Span::styled(" Back  ", secondary_style()),
                Span::styled("[Esc]", accent_style()),
                Span::styled(" Close", secondary_style()),
            ])),
            rows[2],
        );
    }

    fn render_leaf(&mut self, frame: &mut Frame<'_>, area: Rect) {
        let breadcrumb = self
            .navigation
            .breadcrumb(&self.hierarchy)
            .expect("validated breadcrumb");
        let note = self
            .navigation
            .selected_note(&self.hierarchy)
            .expect("validated leaf")
            .expect("validated leaf has notes");
        let count = self
            .hierarchy
            .leaf_notes(self.navigation.current_node_id())
            .expect("validated leaf")
            .len();
        let rows = Layout::default()
            .direction(Direction::Vertical)
            .constraints([
                Constraint::Length(2),
                Constraint::Min(6),
                Constraint::Length(2),
            ])
            .split(area);
        frame.render_widget(
            Paragraph::new(format!(
                "{} · Note {} of {count}",
                breadcrumb.join(" > "),
                self.navigation.selected_index() + 1
            ))
            .style(accent_style())
            .wrap(Wrap { trim: false }),
            rows[0],
        );
        render_scrollable_panel(
            frame,
            rows[1],
            "Note",
            &note.content,
            &mut self.scroll,
            &mut self.half_page_lines,
            false,
        );
        frame.render_widget(
            Paragraph::new(Line::from(vec![
                Span::styled("[←/→]", accent_style()),
                Span::styled(" Previous/next note  ", secondary_style()),
                Span::styled("[Backspace]", accent_style()),
                Span::styled(" Subjects  ", secondary_style()),
                Span::styled("[Ctrl-D/U]", accent_style()),
                Span::styled(" Scroll  ", secondary_style()),
                Span::styled("[Esc]", accent_style()),
                Span::styled(" Close", secondary_style()),
            ])),
            rows[2],
        );
    }
}

pub struct ReferenceTerminal {
    terminal: Terminal<CrosstermBackend<Stdout>>,
}

impl ReferenceTerminal {
    pub fn new() -> io::Result<Self> {
        enable_raw_mode()?;
        let mut stdout = io::stdout();
        if let Err(error) = execute!(
            &mut stdout,
            EnterAlternateScreen,
            EnableBracketedPaste,
            Hide
        ) {
            restore_terminal();
            return Err(error);
        }
        let terminal = match Terminal::new(CrosstermBackend::new(stdout)) {
            Ok(terminal) => terminal,
            Err(error) => {
                restore_terminal();
                return Err(error);
            }
        };
        Ok(Self { terminal })
    }

    pub fn review(&mut self, screen: ApprovalScreen) -> io::Result<ApprovalTuiAction> {
        self.run_review_model(ApprovalTuiModel::new(screen))
    }

    pub fn review_prompt_iteration(
        &mut self,
        screen: ApprovalScreen,
        comment: String,
    ) -> io::Result<ApprovalTuiAction> {
        self.run_review_model(ApprovalTuiModel::new_prompt_iteration(screen, comment))
    }

    pub fn review_navigable_prompt_iteration(
        &mut self,
        screen: ApprovalScreen,
        comment: String,
    ) -> io::Result<ApprovalTuiAction> {
        self.run_review_model(ApprovalTuiModel::new_navigable_prompt_iteration(
            screen, comment,
        ))
    }

    pub fn review_navigable_stacked(
        &mut self,
        screen: ApprovalScreen,
        comment: String,
    ) -> io::Result<ApprovalTuiAction> {
        self.run_review_model(ApprovalTuiModel::new_navigable_stacked_review(
            screen, comment,
        ))
    }

    pub fn review_title(
        &mut self,
        screen: ApprovalScreen,
        comment: String,
    ) -> io::Result<ApprovalTuiAction> {
        self.run_review_model(ApprovalTuiModel::new_title_review(screen, comment))
    }

    pub fn review_title_with_comment(
        &mut self,
        screen: ApprovalScreen,
        user_comment: String,
        assessment_summary: &str,
        assistant_comment: &str,
    ) -> io::Result<ApprovalTuiAction> {
        self.run_review_model(ApprovalTuiModel::new_title_review_with_comment(
            screen,
            user_comment,
            assessment_summary,
            assistant_comment,
        ))
    }

    pub(crate) fn run_review_model<M>(&mut self, mut model: M) -> io::Result<M::Action>
    where
        M: InteractiveReviewModel,
    {
        self.run_review_model_stateful(&mut model, true)
    }

    pub(crate) fn run_review_model_stateful<M>(
        &mut self,
        model: &mut M,
        drain_stale: bool,
    ) -> io::Result<M::Action>
    where
        M: InteractiveReviewModel,
    {
        if drain_stale && drain_stale_input()? {
            return Ok(M::pause_action());
        }
        loop {
            self.terminal.draw(|frame| model.render_terminal(frame))?;
            let action = model.handle_terminal_event(event::read()?);
            if action != M::none_action() {
                return Ok(action);
            }
        }
    }

    pub fn navigate(&mut self, hierarchy: ApprovedHierarchy) -> Result<()> {
        self.navigate_subjects(NavigationHierarchy::try_from(&hierarchy)?)
    }

    pub fn navigate_subjects(&mut self, hierarchy: NavigationHierarchy) -> Result<()> {
        let mut model = ReferenceNavigationTuiModel::from_navigation_hierarchy(hierarchy)?;
        let stale_action = drain_stale_input().map_err(|source| Error::Io {
            operation: "drain terminal input for",
            path: "<reference-navigation-terminal>".into(),
            source,
        })?;
        if stale_action {
            return Ok(());
        }
        loop {
            self.terminal
                .draw(|frame| model.render(frame))
                .map_err(|source| Error::Io {
                    operation: "draw",
                    path: "<reference-navigation-terminal>".into(),
                    source,
                })?;
            let input = event::read().map_err(|source| Error::Io {
                operation: "read input from",
                path: "<reference-navigation-terminal>".into(),
                source,
            })?;
            if model.handle_event(input) == NavigationTuiAction::Quit {
                return Ok(());
            }
        }
    }
}

impl Drop for ReferenceTerminal {
    fn drop(&mut self) {
        let _ = self.terminal.show_cursor();
        restore_terminal();
    }
}

fn drain_stale_input() -> io::Result<bool> {
    while event::poll(Duration::ZERO)? {
        let event = event::read()?;
        if is_control_c_event(&event) {
            return Ok(true);
        }
    }
    Ok(false)
}

fn stacked_evidence_areas(area: Rect, secondary_content: &str) -> [Rect; 2] {
    let inner_width = area.width.saturating_sub(4).max(1);
    let secondary_lines = Paragraph::new(secondary_content)
        .wrap(Wrap { trim: false })
        .line_count(inner_width);
    let maximum_secondary_height = area.height.saturating_sub(6).max(3);
    let desired_secondary_height = u16::try_from(secondary_lines.saturating_add(2))
        .unwrap_or(u16::MAX)
        .clamp(3, maximum_secondary_height);
    let rows = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Min(5),
            Constraint::Length(1),
            Constraint::Length(desired_secondary_height),
        ])
        .split(area);
    [rows[0], rows[2]]
}

pub(crate) fn render_scrollable_panel(
    frame: &mut Frame<'_>,
    area: Rect,
    base_title: &str,
    content: &str,
    scroll: &mut u16,
    half_page_lines: &mut u16,
    focused: bool,
) {
    let panel_border_style = if focused {
        accent_style()
    } else {
        border_style()
    };
    let block = Block::default()
        .borders(Borders::ALL)
        .border_style(panel_border_style)
        .padding(Padding::horizontal(1));
    let inner = block.inner(area);
    *half_page_lines = (inner.height / 2).max(1);
    let rendered_lines = Paragraph::new(content)
        .wrap(Wrap { trim: false })
        .line_count(inner.width);
    let maximum_scroll = rendered_lines.saturating_sub(inner.height as usize);
    *scroll = (*scroll).min(u16::try_from(maximum_scroll).unwrap_or(u16::MAX));
    let separator = if base_title.is_empty() { "" } else { " · " };
    let title = match (*scroll > 0, usize::from(*scroll) < maximum_scroll) {
        (false, true) => format!("{base_title}{separator}more below"),
        (true, true) => format!("{base_title}{separator}more above and below"),
        (true, false) => format!("{base_title}{separator}more above"),
        _ => base_title.to_owned(),
    };
    frame.render_widget(
        Paragraph::new(content)
            .wrap(Wrap { trim: false })
            .scroll((*scroll, 0))
            .block(block.title(title).title_style(accent_style())),
        area,
    );
}

pub(crate) fn render_too_small(frame: &mut Frame<'_>, area: Rect) {
    frame.render_widget(
        Paragraph::new(format!(
            "Terminal too small\nResize to at least {MIN_WIDTH} × {MIN_HEIGHT}."
        ))
        .block(
            Block::default()
                .borders(Borders::ALL)
                .title("Reference map"),
        ),
        area,
    );
}

pub(crate) fn centered(area: Rect) -> Rect {
    let width = area.width.min(MAX_CONTENT_WIDTH);
    Rect {
        x: area.x + area.width.saturating_sub(width) / 2,
        width,
        ..area
    }
}

pub(crate) fn terminal_safe(content: &str) -> String {
    let mut output = String::with_capacity(content.len());
    for character in content.chars() {
        match character {
            '\n' => output.push(character),
            '\t' => output.push_str("    "),
            '\u{2028}' | '\u{2029}' => output.push('\n'),
            _ if character.is_control() => output.push(' '),
            _ => output.push(character),
        }
    }
    output
}

pub(crate) fn accent_style() -> Style {
    Style::default()
        .fg(Color::Cyan)
        .add_modifier(Modifier::BOLD)
}

pub(crate) fn secondary_style() -> Style {
    Style::default().add_modifier(Modifier::DIM)
}

pub(crate) fn border_style() -> Style {
    Style::default().fg(Color::DarkGray)
}

pub(crate) fn is_control_c_event(event: &Event) -> bool {
    matches!(
        event,
        Event::Key(key)
            if key.kind == KeyEventKind::Press
                && key.code == KeyCode::Char('c')
                && key.modifiers == KeyModifiers::CONTROL
    )
}

pub(crate) fn has_command_modifier(modifiers: KeyModifiers) -> bool {
    modifiers.intersects(
        KeyModifiers::CONTROL
            | KeyModifiers::ALT
            | KeyModifiers::SUPER
            | KeyModifiers::HYPER
            | KeyModifiers::META,
    )
}

fn restore_terminal() {
    let _ = execute!(
        io::stdout(),
        DisableBracketedPaste,
        Show,
        LeaveAlternateScreen
    );
    let _ = disable_raw_mode();
}
