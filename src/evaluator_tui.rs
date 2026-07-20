//! Full-screen terminal implementation of the evaluator protocol.

use std::io::{self, Stdout};
use std::time::Duration;

use crossterm::cursor::{Hide, Show};
use crossterm::event::{
    self, DisableBracketedPaste, EnableBracketedPaste, Event, KeyCode, KeyEvent, KeyEventKind,
    KeyModifiers, KeyboardEnhancementFlags, PopKeyboardEnhancementFlags,
    PushKeyboardEnhancementFlags,
};
use crossterm::execute;
use crossterm::terminal::{
    EnterAlternateScreen, LeaveAlternateScreen, disable_raw_mode, enable_raw_mode,
    supports_keyboard_enhancement,
};
use ratatui::Frame;
use ratatui::Terminal;
use ratatui::backend::CrosstermBackend;
use ratatui::layout::{Constraint, Direction, Layout};
use ratatui::style::{Modifier, Style};
use ratatui::text::Line;
use ratatui::widgets::{Block, Borders, Paragraph, Wrap};

use crate::evaluator::{
    CompletionView, EvaluatorDecision, EvaluatorSubmission, EvaluatorUi, RATING_ANCHORS,
    RATING_QUESTION, RatingOutcome, RatingView, RecoveryOutcome, RecoveryView, RestOutcome,
    RestView, WRONG_LANGUAGE_RULE,
};

const MIN_WIDTH: u16 = 72;
const MIN_HEIGHT: u16 = 24;
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
        if has_command_modifier(key.modifiers) {
            return EvaluatorTuiAction::None;
        }
        if !self.interaction_enabled {
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
            KeyCode::Char(value @ '1'..='7') => EvaluatorTuiAction::Submit {
                decision: EvaluatorDecision::Rating(value as u8 - b'0'),
                pause_after: self.pause_after_rating,
            },
            KeyCode::Char('l' | 'L') => EvaluatorTuiAction::Submit {
                decision: EvaluatorDecision::WrongLanguage,
                pause_after: self.pause_after_rating,
            },
            KeyCode::Char('p' | 'P') => {
                self.pause_after_rating = true;
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
    pause_after_rating: bool,
    recovery: bool,
) {
    let rows = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(1),
            Constraint::Min(3),
            Constraint::Length(7),
            Constraint::Length(2),
            Constraint::Length(3),
            Constraint::Length(1),
        ])
        .split(area);

    frame.render_widget(
        Paragraph::new(format!(
            "{} reviewed · break in {break_in}",
            presentation_number.saturating_sub(1)
        ))
        .style(Style::default().add_modifier(Modifier::BOLD)),
        rows[0],
    );
    let sizing_panel = Paragraph::new(note)
        .wrap(Wrap { trim: false })
        .block(Block::default().borders(Borders::ALL).title("Note"));
    let rendered_lines = sizing_panel.line_count(rows[1].width.saturating_sub(2));
    let visible_lines = rows[1].height.saturating_sub(2) as usize;
    let maximum_scroll = rendered_lines
        .saturating_sub(2)
        .saturating_sub(visible_lines);
    *scroll = (*scroll).min(u16::try_from(maximum_scroll).unwrap_or(u16::MAX));
    let note_title = match (*scroll > 0, usize::from(*scroll) < maximum_scroll) {
        (false, true) => "Note · more below",
        (true, true) => "Note · more above and below",
        (true, false) => "Note · more above",
        _ => "Note",
    };
    let note_panel = Paragraph::new(note)
        .wrap(Wrap { trim: false })
        .block(Block::default().borders(Borders::ALL).title(note_title));
    frame.render_widget(note_panel.scroll((*scroll, 0)), rows[1]);

    let anchors = RATING_ANCHORS
        .iter()
        .map(|anchor| Line::from(*anchor))
        .collect::<Vec<_>>();
    frame.render_widget(Paragraph::new(anchors), rows[2]);
    frame.render_widget(
        Paragraph::new(RATING_QUESTION)
            .style(Style::default().add_modifier(Modifier::BOLD))
            .wrap(Wrap { trim: false }),
        rows[3],
    );
    frame.render_widget(
        Paragraph::new(WRONG_LANGUAGE_RULE).wrap(Wrap { trim: false }),
        rows[4],
    );

    let pause = if pause_after_rating {
        "[P] Pause armed"
    } else {
        "[P] Pause after decision"
    };
    let controls = if recovery {
        format!("[1–7] Rate  [L] Wrong language  [R] Redisplay  {pause}")
    } else {
        format!("[1–7] Rate  [L] Wrong language  {pause}  [↑/↓] Scroll")
    };
    frame.render_widget(Paragraph::new(controls), rows[5]);
}

fn render_message(frame: &mut Frame<'_>, area: ratatui::layout::Rect, title: &str, text: &str) {
    frame.render_widget(
        Paragraph::new(text)
            .block(Block::default().borders(Borders::ALL).title(title))
            .wrap(Wrap { trim: false }),
        area,
    );
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
        match supports_keyboard_enhancement() {
            Ok(true) => {}
            Ok(false) => {
                let _ = disable_raw_mode();
                return Err(io::Error::new(
                    io::ErrorKind::Unsupported,
                    "this evaluator requires a terminal with key press/repeat/release reporting (the Kitty keyboard protocol)",
                ));
            }
            Err(error) => {
                let _ = disable_raw_mode();
                return Err(io::Error::new(
                    error.kind(),
                    format!("could not verify safe keyboard event reporting: {error}"),
                ));
            }
        }
        let mut stdout = io::stdout();
        if let Err(error) = execute!(
            &mut stdout,
            PushKeyboardEnhancementFlags(
                KeyboardEnhancementFlags::DISAMBIGUATE_ESCAPE_CODES
                    | KeyboardEnhancementFlags::REPORT_ALL_KEYS_AS_ESCAPE_CODES
                    | KeyboardEnhancementFlags::REPORT_EVENT_TYPES
            )
        ) {
            // `execute!` may have written the push sequence before a later
            // write or flush failed. Balance that possible mutation first.
            let _ = execute!(&mut stdout, PopKeyboardEnhancementFlags);
            let _ = disable_raw_mode();
            return Err(error);
        }
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
            if EvaluatorTuiModel::pre_screen_action(event::read()?) == EvaluatorTuiAction::Pause {
                queued_pause = true;
            }
        }
        if queued_pause {
            return Ok(EvaluatorTuiAction::Pause);
        }
        loop {
            self.draw(&mut model)?;
            let action = model.handle_event(event::read()?);
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
    let _ = execute!(io::stdout(), PopKeyboardEnhancementFlags);
    let _ = execute!(
        io::stdout(),
        DisableBracketedPaste,
        Show,
        LeaveAlternateScreen
    );
    let _ = disable_raw_mode();
}
