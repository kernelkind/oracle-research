//! Full-screen terminal implementation of the evaluator protocol.

use std::io::{self, Stdout};
use std::time::{Duration, Instant};

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
// A press-only terminal cannot identify one isolated late autorepeat. This
// short confirmation window rejects ordinary continuous repeat streams while
// preserving the one-key evaluator flow.
const PRESS_ONLY_DECISION_WINDOW: Duration = Duration::from_millis(150);
const PRESS_ONLY_DRAIN_QUIET: Duration = Duration::from_millis(100);
const RECOVERY_NOTE: &str = "This note may already have appeared before the previous session stopped.\n\nRate it from memory, or press R to explicitly redisplay it.";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum KeyboardReporting {
    PressRepeatRelease,
    PressOnly,
}

fn keyboard_reporting(support: io::Result<bool>) -> KeyboardReporting {
    match support {
        Ok(true) => KeyboardReporting::PressRepeatRelease,
        Ok(false) | Err(_) => KeyboardReporting::PressOnly,
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum PressOnlyDecisionOutcome {
    Waiting,
    Resolved(EvaluatorTuiAction),
    Cancelled,
}

#[derive(Clone, Copy, Debug)]
enum PressOnlyDecisionPhase {
    Confirming { deadline: Instant },
    Draining { quiet_deadline: Instant },
}

#[derive(Clone, Debug)]
struct PressOnlyDecisionState {
    code: KeyCode,
    action: EvaluatorTuiAction,
    phase: PressOnlyDecisionPhase,
}

impl PressOnlyDecisionState {
    fn new(code: KeyCode, action: EvaluatorTuiAction, now: Instant) -> Self {
        Self {
            code,
            action,
            phase: PressOnlyDecisionPhase::Confirming {
                deadline: now + PRESS_ONLY_DECISION_WINDOW,
            },
        }
    }

    fn wait_duration(&self, now: Instant) -> Duration {
        self.deadline().saturating_duration_since(now)
    }

    fn on_timeout(&self, now: Instant) -> PressOnlyDecisionOutcome {
        if now < self.deadline() {
            return PressOnlyDecisionOutcome::Waiting;
        }
        match self.phase {
            PressOnlyDecisionPhase::Confirming { .. } => {
                PressOnlyDecisionOutcome::Resolved(self.action)
            }
            PressOnlyDecisionPhase::Draining { .. } => PressOnlyDecisionOutcome::Cancelled,
        }
    }

    fn on_event(&mut self, event: &Event, now: Instant) -> PressOnlyDecisionOutcome {
        if EvaluatorTuiModel::pre_screen_action(event.clone()) == EvaluatorTuiAction::Pause {
            return PressOnlyDecisionOutcome::Resolved(match self.phase {
                PressOnlyDecisionPhase::Confirming { .. } => pause_after(self.action),
                PressOnlyDecisionPhase::Draining { .. } => EvaluatorTuiAction::Pause,
            });
        }

        match self.phase {
            PressOnlyDecisionPhase::Confirming { .. } => {
                let Event::Key(key) = event else {
                    return PressOnlyDecisionOutcome::Waiting;
                };
                if key.code != self.code {
                    return PressOnlyDecisionOutcome::Waiting;
                }
                match key.kind {
                    KeyEventKind::Release => PressOnlyDecisionOutcome::Resolved(self.action),
                    KeyEventKind::Press | KeyEventKind::Repeat => {
                        self.phase = PressOnlyDecisionPhase::Draining {
                            quiet_deadline: now + PRESS_ONLY_DRAIN_QUIET,
                        };
                        PressOnlyDecisionOutcome::Waiting
                    }
                }
            }
            PressOnlyDecisionPhase::Draining { .. } => {
                self.phase = PressOnlyDecisionPhase::Draining {
                    quiet_deadline: now + PRESS_ONLY_DRAIN_QUIET,
                };
                PressOnlyDecisionOutcome::Waiting
            }
        }
    }

    fn deadline(&self) -> Instant {
        match self.phase {
            PressOnlyDecisionPhase::Confirming { deadline } => deadline,
            PressOnlyDecisionPhase::Draining { quiet_deadline } => quiet_deadline,
        }
    }
}

fn pause_after(action: EvaluatorTuiAction) -> EvaluatorTuiAction {
    match action {
        EvaluatorTuiAction::Submit { decision, .. } => EvaluatorTuiAction::Submit {
            decision,
            pause_after: true,
        },
        action => action,
    }
}

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
    let area = centered_reading_area(area);
    let rows = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(1),
            Constraint::Min(3),
            Constraint::Length(2),
            Constraint::Length(7),
            Constraint::Length(3),
            Constraint::Length(1),
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
        .map(|anchor| {
            let (key, description) = anchor.split_at(2);
            Line::from(vec![
                Span::styled(key, accent_style()),
                Span::raw(description),
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
        Paragraph::new(control_line(recovery, pause_after_rating)),
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

fn control_line(recovery: bool, pause_after_rating: bool) -> Line<'static> {
    let mut controls = vec![
        Span::styled("[1–7]", accent_style()),
        Span::styled(" Rate  ", secondary_style()),
        Span::styled("[L]", accent_style()),
        Span::styled(" Wrong language  ", secondary_style()),
    ];
    if recovery {
        controls.extend([
            Span::styled("[R]", accent_style()),
            Span::styled(" Redisplay  ", secondary_style()),
        ]);
    }
    controls.push(Span::styled("[P]", accent_style()));
    controls.push(Span::styled(
        if pause_after_rating {
            " Pause armed"
        } else {
            " Pause after decision"
        },
        if pause_after_rating {
            accent_style()
        } else {
            secondary_style()
        },
    ));
    if !recovery {
        controls.extend([
            Span::styled("  [↑/↓]", accent_style()),
            Span::styled(" Scroll", secondary_style()),
        ]);
    }
    Line::from(controls)
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
    keyboard_reporting: KeyboardReporting,
}

impl FullScreenEvaluator {
    pub fn new() -> io::Result<Self> {
        enable_raw_mode()?;
        let keyboard_reporting = keyboard_reporting(supports_keyboard_enhancement());
        let mut stdout = io::stdout();
        if keyboard_reporting == KeyboardReporting::PressRepeatRelease
            && let Err(error) = execute!(
                &mut stdout,
                PushKeyboardEnhancementFlags(
                    KeyboardEnhancementFlags::DISAMBIGUATE_ESCAPE_CODES
                        | KeyboardEnhancementFlags::REPORT_ALL_KEYS_AS_ESCAPE_CODES
                        | KeyboardEnhancementFlags::REPORT_EVENT_TYPES
                )
            )
        {
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
            restore_terminal(keyboard_reporting);
            return Err(error);
        }
        let terminal = match Terminal::new(CrosstermBackend::new(stdout)) {
            Ok(terminal) => terminal,
            Err(error) => {
                restore_terminal(keyboard_reporting);
                return Err(error);
            }
        };
        Ok(Self {
            terminal,
            pause_after_redisplay: false,
            keyboard_reporting,
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
            let decision_key = match &input {
                Event::Key(key) => Some(key.code),
                _ => None,
            };
            let action = model.handle_event(input);
            if action != EvaluatorTuiAction::None {
                if self.keyboard_reporting == KeyboardReporting::PressOnly
                    && matches!(action, EvaluatorTuiAction::Submit { .. })
                {
                    if let Some(action) = self.confirm_press_only_decision(
                        decision_key.expect("a submission always comes from a key event"),
                        action,
                    )? {
                        return Ok(action);
                    }
                    continue;
                }
                return Ok(action);
            }
        }
    }

    fn confirm_press_only_decision(
        &mut self,
        code: KeyCode,
        action: EvaluatorTuiAction,
    ) -> io::Result<Option<EvaluatorTuiAction>> {
        let mut state = PressOnlyDecisionState::new(code, action, Instant::now());
        loop {
            let now = Instant::now();
            match state.on_timeout(now) {
                PressOnlyDecisionOutcome::Resolved(action) => return Ok(Some(action)),
                PressOnlyDecisionOutcome::Cancelled => return Ok(None),
                PressOnlyDecisionOutcome::Waiting => {}
            }
            if !event::poll(state.wait_duration(now))? {
                continue;
            }
            let input = event::read()?;
            match state.on_event(&input, Instant::now()) {
                PressOnlyDecisionOutcome::Resolved(action) => return Ok(Some(action)),
                PressOnlyDecisionOutcome::Cancelled => return Ok(None),
                PressOnlyDecisionOutcome::Waiting => {}
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
        restore_terminal(self.keyboard_reporting);
    }
}

fn restore_terminal(keyboard_reporting: KeyboardReporting) {
    if keyboard_reporting == KeyboardReporting::PressRepeatRelease {
        let _ = execute!(io::stdout(), PopKeyboardEnhancementFlags);
    }
    let _ = execute!(
        io::stdout(),
        DisableBracketedPaste,
        Show,
        LeaveAlternateScreen
    );
    let _ = disable_raw_mode();
}

#[test]
fn terminals_without_event_type_reporting_use_the_press_only_path() {
    assert_eq!(
        keyboard_reporting(Ok(true)),
        KeyboardReporting::PressRepeatRelease
    );
    assert_eq!(keyboard_reporting(Ok(false)), KeyboardReporting::PressOnly);
    assert_eq!(
        keyboard_reporting(Err(io::Error::other("terminal did not answer"))),
        KeyboardReporting::PressOnly
    );
}

#[test]
fn press_only_input_does_not_apply_a_held_decision_to_the_next_note() {
    let started_at = Instant::now();
    let submit_seven = EvaluatorTuiAction::Submit {
        decision: EvaluatorDecision::Rating(7),
        pause_after: false,
    };
    let held_seven = Event::Key(KeyEvent::new_with_kind(
        KeyCode::Char('7'),
        KeyModifiers::NONE,
        KeyEventKind::Press,
    ));

    let first_note = PressOnlyDecisionState::new(KeyCode::Char('7'), submit_seven, started_at);
    assert_eq!(
        first_note.on_timeout(started_at + PRESS_ONLY_DECISION_WINDOW),
        PressOnlyDecisionOutcome::Resolved(submit_seven),
        "a normal tap remains a one-key decision"
    );

    let mut next_note = PressOnlyDecisionState::new(
        KeyCode::Char('7'),
        submit_seven,
        started_at + Duration::from_millis(500),
    );
    assert_eq!(
        next_note.on_event(&held_seven, started_at + Duration::from_millis(550)),
        PressOnlyDecisionOutcome::Waiting,
        "the second press starts draining the repeating stream"
    );
    assert_eq!(
        next_note.on_timeout(started_at + Duration::from_millis(550) + PRESS_ONLY_DRAIN_QUIET),
        PressOnlyDecisionOutcome::Cancelled,
        "the repeated candidate is cancelled after the stream becomes quiet"
    );

    let deliberate_same_rating = PressOnlyDecisionState::new(
        KeyCode::Char('7'),
        submit_seven,
        started_at + Duration::from_millis(800),
    );
    assert_eq!(
        deliberate_same_rating
            .on_timeout(started_at + Duration::from_millis(800) + PRESS_ONLY_DECISION_WINDOW,),
        PressOnlyDecisionOutcome::Resolved(submit_seven),
        "a later deliberate press of the same rating still needs only one key"
    );
}

#[test]
fn control_c_during_press_only_confirmation_keeps_the_entered_rating() {
    let started_at = Instant::now();
    let submit = EvaluatorTuiAction::Submit {
        decision: EvaluatorDecision::Rating(6),
        pause_after: false,
    };
    let mut state = PressOnlyDecisionState::new(KeyCode::Char('6'), submit, started_at);
    let control_c = Event::Key(KeyEvent::new_with_kind(
        KeyCode::Char('c'),
        KeyModifiers::CONTROL,
        KeyEventKind::Press,
    ));

    assert_eq!(
        state.on_event(&control_c, started_at + Duration::from_millis(10)),
        PressOnlyDecisionOutcome::Resolved(EvaluatorTuiAction::Submit {
            decision: EvaluatorDecision::Rating(6),
            pause_after: true,
        })
    );

    let held_six = Event::Key(KeyEvent::new_with_kind(
        KeyCode::Char('6'),
        KeyModifiers::NONE,
        KeyEventKind::Press,
    ));
    let mut draining = PressOnlyDecisionState::new(KeyCode::Char('6'), submit, started_at);
    assert_eq!(
        draining.on_event(&held_six, started_at + Duration::from_millis(10)),
        PressOnlyDecisionOutcome::Waiting
    );
    assert_eq!(
        draining.on_event(&control_c, started_at + Duration::from_millis(20)),
        PressOnlyDecisionOutcome::Resolved(EvaluatorTuiAction::Pause),
        "Ctrl-C pauses without accepting a candidate already proven to be a repeat"
    );
}
