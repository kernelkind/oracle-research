use crossterm::event::{Event, KeyCode, KeyEvent, KeyEventKind, KeyModifiers};
use oracle_mvp::evaluator::{
    EvaluatorDecision, RATING_ANCHORS, RATING_QUESTION, WRONG_LANGUAGE_RULE,
};
use oracle_mvp::evaluator_tui::{EvaluatorTuiAction, EvaluatorTuiModel};
use ratatui::Terminal;
use ratatui::backend::TestBackend;
use ratatui::buffer::Buffer;
use ratatui::style::{Color, Modifier};

const EXPECTED_QUESTION: &str =
    "Considering the attention it required, how glad are you that you saw this note?";
const EXPECTED_ANCHORS: [&str; 7] = [
    "1: Actively wish it had not been shown.",
    "2: Clearly not worth seeing.",
    "3: Little personal value.",
    "4: Indifferent.",
    "5: Mildly glad to have seen it.",
    "6: Clearly glad; personally valuable.",
    "7: Exceptionally valuable.",
];

#[test]
fn rating_screen_keeps_the_frozen_protocol_visible_neutral_and_blinded() {
    assert_eq!(RATING_QUESTION, EXPECTED_QUESTION);
    assert_eq!(RATING_ANCHORS, EXPECTED_ANCHORS);

    let model = EvaluatorTuiModel::rating("A plain Nostr note about Rust ownership.", 143, 7);
    let buffer = render(&model, 120, 30);
    let text = buffer_text(&buffer);

    assert!(text.contains(EXPECTED_QUESTION));
    assert!(
        normalized_words(&text).contains(&normalized_words(WRONG_LANGUAGE_RULE)),
        "the complete wrong-language rule must remain visible"
    );
    for anchor in EXPECTED_ANCHORS {
        assert!(text.contains(anchor), "missing rating anchor `{anchor}`");
    }

    let anchor_styles =
        ["1:", "2:", "3:", "4:", "5:", "6:", "7:"].map(|anchor| style_at(&buffer, anchor));
    assert!(
        anchor_styles.windows(2).all(|pair| pair[0] == pair[1]),
        "the rating scale must not visually favor an answer"
    );
    assert_eq!(anchor_styles[0].fg, Some(Color::Cyan));
    assert!(anchor_styles[0].add_modifier.contains(Modifier::BOLD));
    let anchor_descriptions = EXPECTED_ANCHORS.map(|anchor| {
        anchor
            .split_once(": ")
            .expect("every frozen anchor has a key and description")
            .1
    });
    let description_styles = anchor_descriptions.map(|description| style_at(&buffer, description));
    assert!(
        description_styles.windows(2).all(|pair| pair[0] == pair[1]),
        "the rating descriptions must have identical styling"
    );
    for (description, style) in anchor_descriptions.into_iter().zip(description_styles) {
        assert_eq!(
            style.fg,
            Some(Color::Reset),
            "anchor description `{description}` must remain neutral"
        );
        assert!(
            style.add_modifier.is_empty(),
            "anchor description `{description}` must not be emphasized"
        );
    }

    let question_style = style_at(&buffer, EXPECTED_QUESTION);
    assert_eq!(question_style.fg, Some(Color::Cyan));
    assert!(question_style.add_modifier.contains(Modifier::BOLD));
    assert!(
        position_of(&buffer, EXPECTED_QUESTION).1 < position_of(&buffer, EXPECTED_ANCHORS[0]).1,
        "the question must introduce the rating scale"
    );

    assert_eq!(position_of(&buffer, "┌Note").0, 19);
    assert_eq!(position_of(&buffer, "┐").0, 100);
    assert_eq!(position_of(&buffer, "A plain Nostr note").0, 21);
    assert_eq!(style_at(&buffer, "┌Note").fg, Some(Color::DarkGray));
    assert_eq!(style_at(&buffer, "Note").fg, Some(Color::Cyan));
    assert_eq!(
        style_at(&buffer, "A plain Nostr note").fg,
        Some(Color::Reset)
    );

    let language_rule_style = style_at(&buffer, "Use wrong_language only");
    assert_eq!(language_rule_style.fg, Some(Color::Reset));
    assert!(language_rule_style.add_modifier.contains(Modifier::DIM));
    for key in ["[1–7]", "[L]", "[P]"] {
        assert_eq!(style_at(&buffer, key).fg, Some(Color::Cyan));
    }
    for help in ["Rate", "Wrong language", "Pause after decision"] {
        let style = style_at(&buffer, help);
        assert_eq!(style.fg, Some(Color::Reset));
        assert!(style.add_modifier.contains(Modifier::DIM));
    }

    assert!(text.contains("142 reviewed"));
    assert!(!text.contains("Rating 143"));
    assert!(text.contains("break in 7"));
    assert!(text.contains("[1–7]"));
    assert!(text.contains("[L]"));
    assert!(text.contains("[P]"));
    let header_style = style_at(&buffer, "142 reviewed");
    assert_eq!(header_style.fg, Some(Color::Reset));
    assert!(header_style.add_modifier.contains(Modifier::DIM));
    assert!(!header_style.add_modifier.contains(Modifier::BOLD));

    let lowercase = text.to_lowercase();
    for concealed in [
        "compact",
        "rbf",
        "similarity",
        "score",
        "rank",
        "source",
        "learning",
        "final",
    ] {
        assert!(
            !lowercase.contains(concealed),
            "the evaluator screen leaked `{concealed}`"
        );
    }
}

#[test]
fn only_fresh_single_key_ratings_and_wrong_language_are_accepted() {
    for rating in 1..=7 {
        let mut model = rating_model();
        assert_eq!(
            model.handle_event(key(
                KeyCode::Char(char::from(b'0' + rating)),
                KeyEventKind::Press
            )),
            EvaluatorTuiAction::Submit {
                decision: EvaluatorDecision::Rating(rating),
                pause_after: false,
            }
        );
    }

    for key_code in [KeyCode::Char('l'), KeyCode::Char('L')] {
        let mut model = rating_model();
        assert_eq!(
            model.handle_event(key(key_code, KeyEventKind::Press)),
            EvaluatorTuiAction::Submit {
                decision: EvaluatorDecision::WrongLanguage,
                pause_after: false,
            }
        );
    }

    for ignored in [
        key(KeyCode::Char('7'), KeyEventKind::Repeat),
        key(KeyCode::Char('7'), KeyEventKind::Release),
        Event::Paste("7".to_owned()),
        key(KeyCode::Enter, KeyEventKind::Press),
    ] {
        let mut model = rating_model();
        assert_eq!(model.handle_event(ignored), EvaluatorTuiAction::None);
    }

    for modifiers in [
        KeyModifiers::CONTROL,
        KeyModifiers::ALT,
        KeyModifiers::SUPER,
        KeyModifiers::HYPER,
        KeyModifiers::META,
        KeyModifiers::CONTROL | KeyModifiers::SHIFT,
    ] {
        for code in [
            KeyCode::Char('7'),
            KeyCode::Char('l'),
            KeyCode::Char('L'),
            KeyCode::Char('p'),
            KeyCode::Char('P'),
        ] {
            let mut model = rating_model();
            assert_eq!(
                model.handle_event(key_with_modifiers(code, modifiers, KeyEventKind::Press,)),
                EvaluatorTuiAction::None,
                "{modifiers:?}+{code:?} must not alter the presentation"
            );
            assert!(!model.pause_after_rating());
        }
    }

    let mut shifted = rating_model();
    assert_eq!(
        shifted.handle_event(key_with_modifiers(
            KeyCode::Char('L'),
            KeyModifiers::SHIFT,
            KeyEventKind::Press,
        )),
        EvaluatorTuiAction::Submit {
            decision: EvaluatorDecision::WrongLanguage,
            pause_after: false,
        }
    );
}

#[test]
fn pause_is_armed_then_attached_to_the_next_accepted_decision() {
    let mut model = rating_model();

    assert_eq!(
        model.handle_event(key(KeyCode::Char('p'), KeyEventKind::Press)),
        EvaluatorTuiAction::None
    );
    assert!(model.pause_after_rating());
    assert_eq!(
        model.handle_event(key(KeyCode::Char('p'), KeyEventKind::Press)),
        EvaluatorTuiAction::None
    );
    assert!(
        model.pause_after_rating(),
        "P arms pause idempotently so a held key cannot disarm it"
    );
    assert_eq!(
        model.handle_event(key(KeyCode::Char('6'), KeyEventKind::Press)),
        EvaluatorTuiAction::Submit {
            decision: EvaluatorDecision::Rating(6),
            pause_after: true,
        }
    );
}

#[test]
fn scrolling_changes_the_note_body_without_moving_the_controls() {
    let note = (0..80)
        .map(|line| format!("distinct note line {line:02}"))
        .collect::<Vec<_>>()
        .join("\n");
    let mut model = EvaluatorTuiModel::rating(note, 143, 7);
    let before = render(&model, 100, 30);
    let before_text = buffer_text(&before);
    assert!(before_text.contains("distinct note line 00"));

    let fixed_positions = [
        EXPECTED_QUESTION,
        EXPECTED_ANCHORS[0],
        EXPECTED_ANCHORS[3],
        EXPECTED_ANCHORS[6],
        "[1–7]",
        "[L]",
        "[P]",
    ]
    .map(|text| position_of(&before, text));

    assert_eq!(
        model.handle_event(key(KeyCode::PageDown, KeyEventKind::Press)),
        EvaluatorTuiAction::None
    );
    let after = render(&model, 100, 30);
    let after_text = buffer_text(&after);

    assert!(!after_text.contains("distinct note line 00"));
    assert!(after_text.contains("distinct note line 10"));
    assert_eq!(
        [
            EXPECTED_QUESTION,
            EXPECTED_ANCHORS[0],
            EXPECTED_ANCHORS[3],
            EXPECTED_ANCHORS[6],
            "[1–7]",
            "[L]",
            "[P]",
        ]
        .map(|text| position_of(&after, text)),
        fixed_positions
    );
}

#[test]
fn scrolling_stops_at_the_note_boundary() {
    let note = (0..80)
        .map(|line| format!("bounded note line {line:02}"))
        .collect::<Vec<_>>()
        .join("\n");
    let mut model = EvaluatorTuiModel::rating(note, 1, 20);
    assert!(buffer_text(&render(&model, 100, 30)).contains("more below"));
    for _ in 0..100 {
        model.handle_event(key(KeyCode::PageDown, KeyEventKind::Press));
        let _ = render_mut(&mut model, 100, 30);
    }

    let bottom = render(&model, 100, 30);
    assert!(buffer_text(&bottom).contains("bounded note line 79"));
    assert!(buffer_text(&bottom).contains("more above"));
    assert!(!buffer_text(&bottom).contains("more below"));
    model.handle_event(key(KeyCode::Up, KeyEventKind::Press));
    let one_line_up = render(&model, 100, 30);
    assert_ne!(buffer_text(&bottom), buffer_text(&one_line_up));
}

#[test]
fn recovery_and_rest_accept_only_their_explicit_controls() {
    let mut recovery = EvaluatorTuiModel::recovery(21, 20);
    assert_eq!(
        recovery.handle_event(key(KeyCode::Char('r'), KeyEventKind::Press)),
        EvaluatorTuiAction::Redisplay { pause_after: false }
    );
    assert_eq!(
        recovery.handle_event(key(KeyCode::Char('6'), KeyEventKind::Press)),
        EvaluatorTuiAction::Submit {
            decision: EvaluatorDecision::Rating(6),
            pause_after: false,
        }
    );

    let mut rest = EvaluatorTuiModel::rest(20);
    assert_eq!(
        rest.handle_event(key(KeyCode::Enter, KeyEventKind::Press)),
        EvaluatorTuiAction::Continue
    );
    assert_eq!(
        rest.handle_event(key(KeyCode::Char('p'), KeyEventKind::Press)),
        EvaluatorTuiAction::Pause
    );
    assert_eq!(
        rest.handle_event(key(KeyCode::Char('7'), KeyEventKind::Press)),
        EvaluatorTuiAction::None
    );
}

#[test]
fn recovery_pause_state_survives_explicit_redisplay() {
    let mut recovery = EvaluatorTuiModel::recovery(21, 20);
    assert_eq!(
        recovery.handle_event(key_with_modifiers(
            KeyCode::Char('P'),
            KeyModifiers::SHIFT,
            KeyEventKind::Press,
        )),
        EvaluatorTuiAction::None
    );
    let EvaluatorTuiAction::Redisplay { pause_after } = recovery.handle_event(key_with_modifiers(
        KeyCode::Char('R'),
        KeyModifiers::SHIFT,
        KeyEventKind::Press,
    )) else {
        panic!("recovery must request redisplay with its armed pause state");
    };
    assert!(pause_after);

    let mut redisplayed =
        EvaluatorTuiModel::rating_with_pause("The redisplayed note.", 21, 20, pause_after);
    assert_eq!(
        redisplayed.handle_event(key(KeyCode::Char('6'), KeyEventKind::Press)),
        EvaluatorTuiAction::Submit {
            decision: EvaluatorDecision::Rating(6),
            pause_after: true,
        }
    );
}

#[test]
fn pre_screen_input_preserves_only_a_fresh_control_c_pause() {
    assert_eq!(
        EvaluatorTuiModel::pre_screen_action(key_with_modifiers(
            KeyCode::Char('c'),
            KeyModifiers::CONTROL,
            KeyEventKind::Press,
        )),
        EvaluatorTuiAction::Pause
    );

    for discarded in [
        key(KeyCode::Char('7'), KeyEventKind::Press),
        key(KeyCode::Char('l'), KeyEventKind::Press),
        key(KeyCode::Char('p'), KeyEventKind::Press),
        key_with_modifiers(
            KeyCode::Char('c'),
            KeyModifiers::CONTROL,
            KeyEventKind::Repeat,
        ),
        key_with_modifiers(
            KeyCode::Char('C'),
            KeyModifiers::CONTROL | KeyModifiers::SHIFT,
            KeyEventKind::Press,
        ),
        Event::Paste("777".to_owned()),
        Event::Resize(100, 30),
    ] {
        assert_eq!(
            EvaluatorTuiModel::pre_screen_action(discarded),
            EvaluatorTuiAction::None
        );
    }
}

#[test]
fn minimum_supported_preview_size_can_scroll_an_overflowing_note() {
    let note = (0..24)
        .map(|line| format!("preview overflow line {line:02}: enough text to remain readable"))
        .collect::<Vec<_>>()
        .join("\n");
    let mut model = EvaluatorTuiModel::rating(note, 1, 20);
    let before = render(&model, 72, 24);
    let before_text = buffer_text(&before);
    assert!(before_text.contains("more below"));
    assert!(normalized_words(&before_text).contains(&normalized_words(EXPECTED_QUESTION)));
    for anchor in EXPECTED_ANCHORS {
        assert!(
            before_text.contains(anchor),
            "missing rating anchor `{anchor}`"
        );
    }
    assert!(
        normalized_words(&before_text).contains(&normalized_words(WRONG_LANGUAGE_RULE)),
        "the complete wrong-language rule must fit at the minimum size"
    );
    for control in ["[1–7]", "[L]", "[P] Pause after decision", "[↑/↓] Scroll"] {
        assert!(before_text.contains(control), "missing control `{control}`");
    }

    assert_eq!(
        model.handle_event(key(KeyCode::PageDown, KeyEventKind::Press)),
        EvaluatorTuiAction::None
    );
    let after = render(&model, 72, 24);
    assert_ne!(buffer_text(&before), buffer_text(&after));
    assert!(normalized_words(&buffer_text(&after)).contains(&normalized_words(EXPECTED_QUESTION)));
}

#[test]
fn a_terminal_too_small_to_show_the_protocol_refuses_decisions() {
    let mut model = rating_model();
    let buffer = render_mut(&mut model, 20, 8);
    assert!(buffer_text(&buffer).contains("Terminal too small"));
    assert_eq!(
        style_at(&buffer, "Terminal too small").fg,
        Some(Color::Reset)
    );

    assert_eq!(
        model.handle_event(key(KeyCode::Char('7'), KeyEventKind::Press)),
        EvaluatorTuiAction::None
    );
    assert_eq!(
        model.handle_event(key(KeyCode::Char('l'), KeyEventKind::Press)),
        EvaluatorTuiAction::None
    );
}

#[test]
fn evaluator_message_screens_use_the_terminal_default_foreground() {
    for (model, required_text) in [
        (EvaluatorTuiModel::rest(20), "20 presentations reviewed."),
        (EvaluatorTuiModel::preparing(), "Preparing the next notes"),
        (
            EvaluatorTuiModel::complete(200),
            "This rating session is complete.",
        ),
    ] {
        let buffer = render(&model, 72, 24);
        assert_eq!(
            style_at(&buffer, required_text).fg,
            Some(Color::Reset),
            "message text `{required_text}` must use the terminal's default foreground"
        );
    }
}

fn rating_model() -> EvaluatorTuiModel {
    EvaluatorTuiModel::rating("A note to evaluate.", 1, 20)
}

fn key(code: KeyCode, kind: KeyEventKind) -> Event {
    Event::Key(KeyEvent::new_with_kind(code, KeyModifiers::NONE, kind))
}

fn key_with_modifiers(code: KeyCode, modifiers: KeyModifiers, kind: KeyEventKind) -> Event {
    Event::Key(KeyEvent::new_with_kind(code, modifiers, kind))
}

fn render(model: &EvaluatorTuiModel, width: u16, height: u16) -> Buffer {
    let mut model = model.clone();
    render_mut(&mut model, width, height)
}

fn render_mut(model: &mut EvaluatorTuiModel, width: u16, height: u16) -> Buffer {
    let backend = TestBackend::new(width, height);
    let mut terminal = Terminal::new(backend).expect("create test terminal");
    terminal
        .draw(|frame| model.render(frame))
        .expect("render evaluator TUI");
    terminal.backend().buffer().clone()
}

fn buffer_text(buffer: &Buffer) -> String {
    let mut output = String::new();
    for y in buffer.area.top()..buffer.area.bottom() {
        for x in buffer.area.left()..buffer.area.right() {
            output.push_str(buffer[(x, y)].symbol());
        }
        output.push('\n');
    }
    output
}

fn normalized_words(value: &str) -> String {
    value.split_whitespace().collect::<Vec<_>>().join(" ")
}

fn position_of(buffer: &Buffer, needle: &str) -> (u16, u16) {
    for y in buffer.area.top()..buffer.area.bottom() {
        let mut row = String::new();
        let mut cell_starts = Vec::new();
        for x in buffer.area.left()..buffer.area.right() {
            cell_starts.push((row.len(), x));
            row.push_str(buffer[(x, y)].symbol());
        }
        if let Some(byte_offset) = row.find(needle) {
            let (_, column) = cell_starts
                .into_iter()
                .find(|(start, _)| *start == byte_offset)
                .expect("rendered text begins on a terminal cell boundary");
            return (column, y);
        }
    }
    panic!("rendered buffer is missing `{needle}`")
}

fn style_at(buffer: &Buffer, needle: &str) -> ratatui::style::Style {
    let (x, y) = position_of(buffer, needle);
    buffer[(x, y)].style()
}
