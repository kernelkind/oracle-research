//! Full-screen review and navigation interfaces for the reference map.

use std::io::{self, Stdout};
use std::time::Duration;

use crossterm::cursor::{Hide, Show};
use crossterm::event::{
    self, DisableBracketedPaste, EnableBracketedPaste, Event, KeyCode, KeyEventKind, KeyModifiers,
};
use crossterm::execute;
use crossterm::terminal::{
    disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen,
};
use ratatui::backend::CrosstermBackend;
use ratatui::layout::{Constraint, Direction, Layout, Rect};
use ratatui::style::{Color, Modifier, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Borders, List, ListItem, ListState, Padding, Paragraph, Wrap};
use ratatui::Frame;
use ratatui::Terminal;

use crate::reference_map::{ApprovedHierarchy, ReferenceNavigation, ReviewOutcome};
use crate::snapshot::{Error, Result};

const MIN_WIDTH: u16 = 72;
const MIN_HEIGHT: u16 = 24;
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

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ApprovalEvidenceLayout {
    Paged,
    Stacked,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ApprovalScreen {
    pub heading: String,
    pub title: String,
    pub scope: String,
    pub approve_label: String,
    pub reject_label: String,
    pub guidance: Option<ApprovalGuidance>,
    pub evidence: Vec<ApprovalEvidence>,
    pub evidence_layout: ApprovalEvidenceLayout,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum ApprovalTuiAction {
    None,
    Submit {
        outcome: ReviewOutcome,
        comment: String,
    },
    Pause,
}

#[derive(Clone, Debug)]
pub struct ApprovalTuiModel {
    screen: ApprovalScreen,
    evidence_index: usize,
    evidence_scrolls: Vec<u16>,
    guidance_scroll: u16,
    guidance_visible: bool,
    half_page_lines: u16,
    pending_outcome: Option<ReviewOutcome>,
    comment: String,
    interaction_enabled: bool,
}

impl ApprovalTuiModel {
    pub fn new(mut screen: ApprovalScreen) -> Self {
        screen.heading = terminal_safe(&screen.heading);
        screen.title = terminal_safe(&screen.title);
        screen.scope = terminal_safe(&screen.scope);
        screen.approve_label = terminal_safe(&screen.approve_label);
        screen.reject_label = terminal_safe(&screen.reject_label);
        if let Some(guidance) = &mut screen.guidance {
            guidance.title = terminal_safe(&guidance.title);
            guidance.body = terminal_safe(&guidance.body);
        }
        for evidence in &mut screen.evidence {
            evidence.title = terminal_safe(&evidence.title);
            evidence.annotation = terminal_safe(&evidence.annotation);
            evidence.body = terminal_safe(&evidence.body);
        }
        let evidence_scrolls = vec![0; screen.evidence.len()];
        Self {
            screen,
            evidence_index: 0,
            evidence_scrolls,
            guidance_scroll: 0,
            guidance_visible: false,
            half_page_lines: 1,
            pending_outcome: None,
            comment: String::new(),
            interaction_enabled: true,
        }
    }

    pub fn handle_event(&mut self, event: Event) -> ApprovalTuiAction {
        if is_control_c_event(&event) {
            return ApprovalTuiAction::Pause;
        }
        if !self.interaction_enabled {
            return ApprovalTuiAction::None;
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
            KeyCode::Char('?') if self.screen.guidance.is_some() => {
                self.guidance_visible = true;
                self.guidance_scroll = 0;
            }
            KeyCode::Char('a' | 'A') => {
                self.pending_outcome = Some(ReviewOutcome::Approved);
                self.comment.clear();
            }
            KeyCode::Char('r' | 'R') => {
                self.pending_outcome = Some(ReviewOutcome::Rejected);
                self.comment.clear();
            }
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
        if self.screen.evidence_layout == ApprovalEvidenceLayout::Paged {
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
        if self.screen.evidence_layout == ApprovalEvidenceLayout::Paged {
            self.evidence_scrolls[self.evidence_index] = 0;
        }
    }

    pub fn render(&mut self, frame: &mut Frame<'_>) {
        let area = frame.area();
        self.interaction_enabled = area.width >= MIN_WIDTH && area.height >= MIN_HEIGHT;
        if !self.interaction_enabled {
            render_too_small(frame, area);
            return;
        }
        let area = centered(area);
        let footer_height = if self.pending_outcome.is_some() { 8 } else { 4 };
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
        let maximum_annotation_height = area
            .height
            .saturating_sub(1 + 2 + scope_height + 6 + footer_height);
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
                Constraint::Length(2),
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
        frame.render_widget(
            Paragraph::new(self.screen.title.as_str()).style(accent_style()),
            rows[1],
        );
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
        } else if self.screen.evidence_layout == ApprovalEvidenceLayout::Stacked
            && self.screen.evidence.len() == 2
        {
            let panels = stacked_evidence_areas(rows[3], &self.screen.evidence[1].body);
            for (index, area) in panels.into_iter().enumerate() {
                let evidence = &self.screen.evidence[index];
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
        } else if let Some(outcome) = self.pending_outcome {
            let decision = match outcome {
                ReviewOutcome::Approved => "Approve",
                ReviewOutcome::Rejected => "Reject",
            };
            let comment_requirement = match outcome {
                ReviewOutcome::Approved => " (optional)",
                ReviewOutcome::Rejected => " (required)",
            };
            vec![
                Line::from(vec![
                    Span::styled(format!("{decision} comment"), accent_style()),
                    Span::styled(comment_requirement, secondary_style()),
                ]),
                Line::raw(format!("> {}", self.comment)),
                if outcome == ReviewOutcome::Rejected && self.comment.trim().is_empty() {
                    Line::styled(
                        "Explain what must change before rejecting.",
                        Style::default().fg(Color::Yellow),
                    )
                } else {
                    Line::raw("")
                },
                Line::from(vec![
                    Span::styled("[Enter]", accent_style()),
                    Span::styled(" Confirm  ", secondary_style()),
                    Span::styled("[Esc]", accent_style()),
                    Span::styled(" Cancel", secondary_style()),
                ]),
            ]
        } else {
            let mut navigation_controls = Vec::new();
            if self.screen.evidence.len() > 1 {
                let target = match self.screen.evidence_layout {
                    ApprovalEvidenceLayout::Paged => " Evidence  ",
                    ApprovalEvidenceLayout::Stacked => " Panel  ",
                };
                navigation_controls.extend([
                    Span::styled("[Tab/←/→]", accent_style()),
                    Span::styled(target, secondary_style()),
                ]);
            }
            if self.screen.guidance.is_some() {
                let guidance_title = self
                    .screen
                    .guidance
                    .as_ref()
                    .expect("guidance presence was just checked")
                    .title
                    .as_str();
                navigation_controls.extend([
                    Span::styled("[?]", accent_style()),
                    Span::styled(format!(" {guidance_title}  "), secondary_style()),
                ]);
            }
            navigation_controls.extend([
                Span::styled("[↑/↓]", accent_style()),
                Span::styled(" Scroll  ", secondary_style()),
                Span::styled("[Ctrl-D/U]", accent_style()),
                Span::styled(" Half-page  ", secondary_style()),
                Span::styled("[Ctrl-C]", accent_style()),
                Span::styled(" Pause", secondary_style()),
            ]);
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
        let footer = Paragraph::new(footer).wrap(Wrap { trim: false });
        let rendered_lines = footer.line_count(rows[5].width);
        let footer_scroll = rendered_lines
            .saturating_sub(rows[5].height as usize)
            .try_into()
            .unwrap_or(u16::MAX);
        frame.render_widget(footer.scroll((footer_scroll, 0)), rows[5]);
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum NavigationTuiAction {
    None,
    Quit,
}

#[derive(Clone, Debug)]
pub struct ReferenceNavigationTuiModel {
    hierarchy: ApprovedHierarchy,
    navigation: ReferenceNavigation,
    scroll: u16,
    half_page_lines: u16,
    interaction_enabled: bool,
}

impl ReferenceNavigationTuiModel {
    pub fn new(hierarchy: ApprovedHierarchy) -> Result<Self> {
        let navigation = ReferenceNavigation::new(&hierarchy)?;
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
        let mut model = ApprovalTuiModel::new(screen);
        if drain_stale_input()? == ApprovalTuiAction::Pause {
            return Ok(ApprovalTuiAction::Pause);
        }
        loop {
            self.terminal.draw(|frame| model.render(frame))?;
            let action = model.handle_event(event::read()?);
            if action != ApprovalTuiAction::None {
                return Ok(action);
            }
        }
    }

    pub fn navigate(&mut self, hierarchy: ApprovedHierarchy) -> Result<()> {
        let mut model = ReferenceNavigationTuiModel::new(hierarchy)?;
        let stale_action = drain_stale_input().map_err(|source| Error::Io {
            operation: "drain terminal input for",
            path: "<reference-navigation-terminal>".into(),
            source,
        })?;
        if stale_action == ApprovalTuiAction::Pause {
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

fn drain_stale_input() -> io::Result<ApprovalTuiAction> {
    while event::poll(Duration::ZERO)? {
        let event = event::read()?;
        if is_control_c_event(&event) {
            return Ok(ApprovalTuiAction::Pause);
        }
    }
    Ok(ApprovalTuiAction::None)
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

fn render_scrollable_panel(
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
    let title = match (*scroll > 0, usize::from(*scroll) < maximum_scroll) {
        (false, true) => format!("{base_title} · more below"),
        (true, true) => format!("{base_title} · more above and below"),
        (true, false) => format!("{base_title} · more above"),
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

fn render_too_small(frame: &mut Frame<'_>, area: Rect) {
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

fn centered(area: Rect) -> Rect {
    let width = area.width.min(MAX_CONTENT_WIDTH);
    Rect {
        x: area.x + area.width.saturating_sub(width) / 2,
        width,
        ..area
    }
}

fn terminal_safe(content: &str) -> String {
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

fn accent_style() -> Style {
    Style::default()
        .fg(Color::Cyan)
        .add_modifier(Modifier::BOLD)
}

fn secondary_style() -> Style {
    Style::default().add_modifier(Modifier::DIM)
}

fn border_style() -> Style {
    Style::default().fg(Color::DarkGray)
}

fn is_control_c_event(event: &Event) -> bool {
    matches!(
        event,
        Event::Key(key)
            if key.kind == KeyEventKind::Press
                && key.code == KeyCode::Char('c')
                && key.modifiers == KeyModifiers::CONTROL
    )
}

fn has_command_modifier(modifiers: KeyModifiers) -> bool {
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
