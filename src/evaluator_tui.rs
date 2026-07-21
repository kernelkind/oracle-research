//! Full-screen terminal implementation of the evaluator protocol.

use std::io::{self, Stdout};
use std::time::Duration;

use crossterm::cursor::{Hide, Show};
use crossterm::event::{
    self, DisableBracketedPaste, EnableBracketedPaste, Event, KeyCode, KeyEvent, KeyEventKind,
    KeyModifiers,
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
use ratatui::widgets::{Block, Borders, Padding, Paragraph, Wrap};

use crate::evaluator::{
    CompletionView, EvaluatorDecision, EvaluatorSubmission, EvaluatorUi, RATING_ANCHORS,
    RATING_QUESTION, RatingOutcome, RatingView, RecoveryOutcome, RecoveryView, RestOutcome,
    RestView, WRONG_LANGUAGE_RULE,
};

const MIN_WIDTH: u16 = 72;
const MIN_HEIGHT: u16 = 24;
const MAX_CONTENT_WIDTH: u16 = 82;
const PAGE_LINES: u16 = 10;
const RECOVERY_NOTE: &str = "This note may already have appeared before the previous session stopped.\n\nRate it from memory, or press R to explicitly redisplay it.";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum EvaluatorTuiAction {
    None,
    Submit {
        decision: EvaluatorDecision,
        pause_after: bool,
    },
    Pause,
    Redisplay {
        pause_after: bool,
    },
    Continue,
}

#[derive(Clone, Debug)]
enum EvaluatorScreen {
    Rating {
        note: String,
        presentation_number: usize,
        break_in: usize,
    },
    Recovery {
        presentation_number: usize,
        break_in: usize,
    },
    Rest {
        presentations_stored: usize,
    },
    Preparing,
    Complete {
        presentations_stored: usize,
    },
}

/// Production render state and event reducer for the evaluator TUI.
#[derive(Clone, Debug)]
pub struct EvaluatorTuiModel {
    screen: EvaluatorScreen,
    scroll: u16,
    selected_decision: Option<EvaluatorDecision>,
    pause_after_rating: bool,
    interaction_enabled: bool,
}

impl EvaluatorTuiModel {
    pub fn rating(note: impl AsRef<str>, presentation_number: usize, break_in: usize) -> Self {
        Self::new(EvaluatorScreen::Rating {
            note: terminal_safe(note.as_ref()),
            presentation_number,
            break_in,
        })
    }

    /// Recreate a rating screen after recovery without losing an armed pause.
    pub fn rating_with_pause(
        note: impl AsRef<str>,
        presentation_number: usize,
        break_in: usize,
        pause_after_rating: bool,
    ) -> Self {
        let mut model = Self::rating(note, presentation_number, break_in);
        model.pause_after_rating = pause_after_rating;
        model
    }

    pub fn recovery(presentation_number: usize, break_in: usize) -> Self {
        Self::new(EvaluatorScreen::Recovery {
            presentation_number,
            break_in,
        })
    }

    pub fn rest(presentations_stored: usize) -> Self {
        Self::new(EvaluatorScreen::Rest {
            presentations_stored,
        })
    }

    pub fn preparing() -> Self {
        Self::new(EvaluatorScreen::Preparing)
    }

    pub fn complete(presentations_stored: usize) -> Self {
        Self::new(EvaluatorScreen::Complete {
            presentations_stored,
        })
    }

    fn new(screen: EvaluatorScreen) -> Self {
        Self {
            screen,
            scroll: 0,
            selected_decision: None,
            pause_after_rating: false,
            interaction_enabled: true,
        }
    }

    pub const fn pause_after_rating(&self) -> bool {
        self.pause_after_rating
    }

    /// Interpret an event already waiting before a screen is presented.
    ///
    /// A fresh Ctrl-C remains an explicit pause request. Every other queued
    /// event is stale input and must not act on the new presentation.
    pub fn pre_screen_action(event: Event) -> EvaluatorTuiAction {
        match event {
            Event::Key(key) if key.kind == KeyEventKind::Press && is_control_c(key) => {
                EvaluatorTuiAction::Pause
            }
            _ => EvaluatorTuiAction::None,
        }
    }

    pub fn handle_event(&mut self, event: Event) -> EvaluatorTuiAction {
        let Event::Key(key) = event else {
            return EvaluatorTuiAction::None;
        };
        if key.kind != KeyEventKind::Press {
            return EvaluatorTuiAction::None;
        }
        if is_control_c(key) {
            return EvaluatorTuiAction::Pause;
        }
        if !self.interaction_enabled {
            return EvaluatorTuiAction::None;
        }

        if matches!(
            self.screen,
            EvaluatorScreen::Rating { .. } | EvaluatorScreen::Recovery { .. }
        ) && key.modifiers == KeyModifiers::CONTROL
        {
            match key.code {
                KeyCode::Char('n' | 'N') => {
                    self.move_rating_selection(1);
                    return EvaluatorTuiAction::None;
                }
                KeyCode::Char('p' | 'P') => {
                    self.move_rating_selection(-1);
                    return EvaluatorTuiAction::None;
                }
                _ => {}
            }
        }
        if has_command_modifier(key.modifiers) {
            return EvaluatorTuiAction::None;
        }

        match self.screen {
            EvaluatorScreen::Rating { .. } => self.handle_rating_key(key, false),
            EvaluatorScreen::Recovery { .. } => self.handle_rating_key(key, true),
            EvaluatorScreen::Rest { .. } => match key.code {
                KeyCode::Enter | KeyCode::Char(' ') | KeyCode::Char('c' | 'C') => {
                    EvaluatorTuiAction::Continue
                }
                KeyCode::Char('p' | 'P' | 'q' | 'Q') | KeyCode::Esc => EvaluatorTuiAction::Pause,
                _ => EvaluatorTuiAction::None,
            },
            EvaluatorScreen::Preparing => EvaluatorTuiAction::None,
            EvaluatorScreen::Complete { .. } => match key.code {
                KeyCode::Enter | KeyCode::Char(' ') | KeyCode::Char('c' | 'C') | KeyCode::Esc => {
                    EvaluatorTuiAction::Continue
                }
                _ => EvaluatorTuiAction::None,
            },
        }
    }

    fn handle_rating_key(&mut self, key: KeyEvent, recovery: bool) -> EvaluatorTuiAction {
        match key.code {
            KeyCode::Char(value @ '1'..='7') => {
                self.selected_decision = Some(EvaluatorDecision::Rating(value as u8 - b'0'));
                EvaluatorTuiAction::None
            }
            KeyCode::Char('l' | 'L') => {
                self.selected_decision = Some(EvaluatorDecision::WrongLanguage);
                EvaluatorTuiAction::None
            }
            KeyCode::Enter => self
                .selected_decision
                .map_or(EvaluatorTuiAction::None, |decision| {
                    EvaluatorTuiAction::Submit {
                        decision,
                        pause_after: self.pause_after_rating,
                    }
                }),
            KeyCode::Char('p' | 'P') => {
                self.pause_after_rating = true;
                EvaluatorTuiAction::None
            }
            KeyCode::Esc if self.pause_after_rating => {
                self.pause_after_rating = false;
                EvaluatorTuiAction::None
            }
            KeyCode::Char('r' | 'R') if recovery => EvaluatorTuiAction::Redisplay {
                pause_after: self.pause_after_rating,
            },
            KeyCode::Down | KeyCode::Char('j' | 'J') => {
                self.scroll = self.scroll.saturating_add(1);
                EvaluatorTuiAction::None
            }
            KeyCode::Up | KeyCode::Char('k' | 'K') => {
                self.scroll = self.scroll.saturating_sub(1);
                EvaluatorTuiAction::None
            }
            KeyCode::PageDown => {
                self.scroll = self.scroll.saturating_add(PAGE_LINES);
                EvaluatorTuiAction::None
            }
            KeyCode::PageUp => {
                self.scroll = self.scroll.saturating_sub(PAGE_LINES);
                EvaluatorTuiAction::None
            }
            KeyCode::Home => {
                self.scroll = 0;
                EvaluatorTuiAction::None
            }
            _ => EvaluatorTuiAction::None,
        }
    }

    fn move_rating_selection(&mut self, change: i8) {
        let rating = match self.selected_decision {
            Some(EvaluatorDecision::Rating(rating)) => {
                u8::try_from(i16::from(rating) + i16::from(change))
                    .unwrap_or(rating)
                    .clamp(1, 7)
            }
            Some(EvaluatorDecision::WrongLanguage) | None if change > 0 => 1,
            Some(EvaluatorDecision::WrongLanguage) | None => 7,
        };
        self.selected_decision = Some(EvaluatorDecision::Rating(rating));
    }

    pub fn render(&mut self, frame: &mut Frame<'_>) {
        let area = frame.area();
        self.interaction_enabled = area.width >= MIN_WIDTH && area.height >= MIN_HEIGHT;
        if !self.interaction_enabled {
            frame.render_widget(
                Paragraph::new(format!(
                    "Terminal too small\nResize to at least {MIN_WIDTH} × {MIN_HEIGHT}."
                ))
                .block(Block::default().borders(Borders::ALL).title("Evaluator")),
                area,
            );
            return;
        }

        match &self.screen {
            EvaluatorScreen::Rating {
                note,
                presentation_number,
                break_in,
            } => render_rating(
                frame,
                area,
                note,
                *presentation_number,
                *break_in,
                &mut self.scroll,
                self.selected_decision,
                self.pause_after_rating,
                false,
            ),
            EvaluatorScreen::Recovery {
                presentation_number,
                break_in,
            } => render_rating(
                frame,
                area,
                RECOVERY_NOTE,
                *presentation_number,
                *break_in,
                &mut self.scroll,
                self.selected_decision,
                self.pause_after_rating,
                true,
            ),
            EvaluatorScreen::Rest {
                presentations_stored,
            } => render_message(
                frame,
                area,
                "Take a break",
                &format!(
                    "{presentations_stored} presentations reviewed.\n\n[Enter/C] Continue    [P] Pause"
                ),
            ),
            EvaluatorScreen::Preparing => render_message(
                frame,
                area,
                "Preparing",
                "Preparing the next notes…\n\nNo input is needed.",
            ),
            EvaluatorScreen::Complete {
                presentations_stored,
            } => render_message(
                frame,
                area,
                "Complete",
                &format!(
                    "This rating session is complete.\n{presentations_stored} presentations reviewed.\n\n[Enter] Close"
                ),
            ),
        }
    }
}

#[allow(clippy::too_many_arguments)]
fn render_rating(
    frame: &mut Frame<'_>,
    area: ratatui::layout::Rect,
    note: &str,
    presentation_number: usize,
    break_in: usize,
    scroll: &mut u16,
    selected_decision: Option<EvaluatorDecision>,
    pause_after_rating: bool,
    recovery: bool,
) {
    let area = centered_reading_area(area);
    let rows = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(1),
            Constraint::Min(3),
            Constraint::Length(2),
            Constraint::Length(7),
            Constraint::Length(3),
            Constraint::Length(2),
        ])
        .split(area);

    frame.render_widget(
        Paragraph::new(format!(
            "{} reviewed · break in {break_in}",
            presentation_number.saturating_sub(1)
        ))
        .style(secondary_style()),
        rows[0],
    );
    let note_block = Block::default()
        .borders(Borders::ALL)
        .border_style(border_style())
        .padding(Padding::horizontal(1));
    let note_inner = note_block.inner(rows[1]);
    let rendered_lines = Paragraph::new(note)
        .wrap(Wrap { trim: false })
        .line_count(note_inner.width);
    let visible_lines = note_inner.height as usize;
    let maximum_scroll = rendered_lines.saturating_sub(visible_lines);
    *scroll = (*scroll).min(u16::try_from(maximum_scroll).unwrap_or(u16::MAX));
    let note_title = match (*scroll > 0, usize::from(*scroll) < maximum_scroll) {
        (false, true) => "Note · more below",
        (true, true) => "Note · more above and below",
        (true, false) => "Note · more above",
        _ => "Note",
    };
    let note_panel = Paragraph::new(note)
        .wrap(Wrap { trim: false })
        .block(note_block.title(note_title).title_style(accent_style()));
    frame.render_widget(note_panel.scroll((*scroll, 0)), rows[1]);

    frame.render_widget(
        Paragraph::new(RATING_QUESTION)
            .style(accent_style())
            .wrap(Wrap { trim: false }),
        rows[2],
    );
    let anchors = RATING_ANCHORS
        .iter()
        .enumerate()
        .map(|(index, anchor)| {
            let (key, description) = anchor
                .split_once(' ')
                .expect("a frozen rating anchor has a key and description");
            let selected = selected_decision
                == Some(EvaluatorDecision::Rating(
                    u8::try_from(index + 1).expect("the rating scale has seven entries"),
                ));
            let key_style = if selected {
                accent_style().bg(Color::DarkGray)
            } else {
                accent_style()
            };
            let answer_style = if selected {
                Style::default().bg(Color::DarkGray)
            } else {
                Style::default()
            };
            Line::from(vec![
                Span::styled(key, key_style),
                Span::styled(" ", answer_style),
                Span::styled(description, answer_style),
            ])
        })
        .collect::<Vec<_>>();
    frame.render_widget(Paragraph::new(anchors), rows[3]);
    frame.render_widget(
        Paragraph::new(WRONG_LANGUAGE_RULE)
            .style(secondary_style())
            .wrap(Wrap { trim: false }),
        rows[4],
    );

    frame.render_widget(
        Paragraph::new(control_lines(
            recovery,
            selected_decision,
            pause_after_rating,
        )),
        rows[5],
    );
}

fn render_message(frame: &mut Frame<'_>, area: ratatui::layout::Rect, title: &str, text: &str) {
    let area = centered_reading_area(area);
    frame.render_widget(
        Paragraph::new(text)
            .block(
                Block::default()
                    .borders(Borders::ALL)
                    .border_style(border_style())
                    .title(title)
                    .title_style(accent_style()),
            )
            .wrap(Wrap { trim: false }),
        area,
    );
}

fn centered_reading_area(area: Rect) -> Rect {
    let width = area.width.min(MAX_CONTENT_WIDTH);
    Rect {
        x: area.x + area.width.saturating_sub(width) / 2,
        width,
        ..area
    }
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

fn control_lines(
    recovery: bool,
    selected_decision: Option<EvaluatorDecision>,
    pause_after_rating: bool,
) -> Vec<Line<'static>> {
    let primary = Line::from(vec![
        Span::styled("[1–7]", accent_style()),
        Span::styled(" Select  ", secondary_style()),
        Span::styled("[Ctrl-N/P]", accent_style()),
        Span::styled(" Move  ", secondary_style()),
        Span::styled("[Enter]", accent_style()),
        Span::styled(" Confirm", secondary_style()),
    ]);
    let wrong_language_selected = selected_decision == Some(EvaluatorDecision::WrongLanguage);
    let wrong_language_key_style = if wrong_language_selected {
        accent_style().bg(Color::DarkGray)
    } else {
        accent_style()
    };
    let wrong_language_text_style = if wrong_language_selected {
        Style::default().bg(Color::DarkGray)
    } else {
        secondary_style()
    };
    let mut controls = vec![
        Span::styled("[L]", wrong_language_key_style),
        Span::styled(" Wrong language", wrong_language_text_style),
        Span::raw("  "),
    ];
    if recovery {
        controls.extend([
            Span::styled("[R]", accent_style()),
            Span::styled(" Redisplay  ", secondary_style()),
        ]);
    }
    if pause_after_rating {
        controls.extend([
            Span::styled("[Esc]", accent_style()),
            Span::styled(" Cancel pause", accent_style()),
        ]);
    } else {
        controls.extend([
            Span::styled("[P]", accent_style()),
            Span::styled(" Pause after decision", secondary_style()),
        ]);
    }
    if !recovery {
        controls.extend([
            Span::styled("  [↑/↓]", accent_style()),
            Span::styled(" Scroll", secondary_style()),
        ]);
    }
    vec![primary, Line::from(controls)]
}

fn terminal_safe(content: &str) -> String {
    content
        .chars()
        .map(|character| match character {
            '\n' | '\t' => character,
            _ if character.is_control() => ' ',
            _ => character,
        })
        .collect()
}

fn is_control_c(key: KeyEvent) -> bool {
    key.code == KeyCode::Char('c') && key.modifiers == KeyModifiers::CONTROL
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

/// Real full-screen terminal evaluator used by Phase 3 runners.
pub struct FullScreenEvaluator {
    terminal: Terminal<CrosstermBackend<Stdout>>,
    pause_after_redisplay: bool,
}

impl FullScreenEvaluator {
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
        Ok(Self {
            terminal,
            pause_after_redisplay: false,
        })
    }

    fn draw(&mut self, model: &mut EvaluatorTuiModel) -> io::Result<()> {
        self.terminal.draw(|frame| model.render(frame)).map(|_| ())
    }

    fn run(&mut self, mut model: EvaluatorTuiModel) -> io::Result<EvaluatorTuiAction> {
        let mut queued_pause = false;
        while event::poll(Duration::ZERO)? {
            let queued_event = event::read()?;
            if EvaluatorTuiModel::pre_screen_action(queued_event.clone())
                == EvaluatorTuiAction::Pause
            {
                queued_pause = true;
            }
        }
        if queued_pause {
            return Ok(EvaluatorTuiAction::Pause);
        }
        loop {
            self.draw(&mut model)?;
            let input = event::read()?;
            let action = model.handle_event(input);
            if action != EvaluatorTuiAction::None {
                return Ok(action);
            }
        }
    }
}

impl EvaluatorUi for FullScreenEvaluator {
    fn rate(&mut self, view: RatingView<'_>) -> io::Result<RatingOutcome> {
        let pause_after_rating = std::mem::take(&mut self.pause_after_redisplay);
        match self.run(EvaluatorTuiModel::rating_with_pause(
            view.note(),
            view.presentation_number(),
            view.break_in(),
            pause_after_rating,
        ))? {
            EvaluatorTuiAction::Submit {
                decision,
                pause_after,
            } => Ok(RatingOutcome::Submitted(EvaluatorSubmission::new(
                decision,
                pause_after,
            ))),
            EvaluatorTuiAction::Pause => Ok(RatingOutcome::Paused),
            _ => Err(io::Error::other(
                "rating screen returned an invalid evaluator action",
            )),
        }
    }

    fn recover(&mut self, view: RecoveryView) -> io::Result<RecoveryOutcome> {
        // A redisplay arm belongs only to the recovery call that produced it.
        // If redisplay never reaches `rate` and recovery begins again, the new
        // recovery decision must not inherit that stale UI state.
        self.pause_after_redisplay = false;
        match self.run(EvaluatorTuiModel::recovery(
            view.presentation_number(),
            view.break_in(),
        ))? {
            EvaluatorTuiAction::Submit {
                decision,
                pause_after,
            } => Ok(RecoveryOutcome::Submitted(EvaluatorSubmission::new(
                decision,
                pause_after,
            ))),
            EvaluatorTuiAction::Redisplay { pause_after } => {
                self.pause_after_redisplay = pause_after;
                Ok(RecoveryOutcome::Redisplay)
            }
            EvaluatorTuiAction::Pause => Ok(RecoveryOutcome::Paused),
            _ => Err(io::Error::other(
                "recovery screen returned an invalid evaluator action",
            )),
        }
    }

    fn rest(&mut self, view: RestView) -> io::Result<RestOutcome> {
        match self.run(EvaluatorTuiModel::rest(view.presentations_stored()))? {
            EvaluatorTuiAction::Continue => Ok(RestOutcome::Continue),
            EvaluatorTuiAction::Pause => Ok(RestOutcome::Paused),
            _ => Err(io::Error::other(
                "rest screen returned an invalid evaluator action",
            )),
        }
    }

    fn preparing(&mut self) -> io::Result<()> {
        let mut model = EvaluatorTuiModel::preparing();
        self.draw(&mut model)
    }

    fn complete(&mut self, view: CompletionView) -> io::Result<()> {
        match self.run(EvaluatorTuiModel::complete(view.presentations_stored()))? {
            EvaluatorTuiAction::Continue | EvaluatorTuiAction::Pause => Ok(()),
            _ => Err(io::Error::other(
                "completion screen returned an invalid evaluator action",
            )),
        }
    }
}

impl Drop for FullScreenEvaluator {
    fn drop(&mut self) {
        let _ = self.terminal.show_cursor();
        restore_terminal();
    }
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
