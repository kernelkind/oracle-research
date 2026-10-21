use std::fs;

use crossterm::event::{Event, KeyCode, KeyEvent, KeyModifiers};
use oracle_mvp::note_sample_review::{NoteSampleReview, NoteSampleReviewAction};
use ratatui::{Terminal, backend::TestBackend};
use serde_json::{Value, json};
use unicode_width::UnicodeWidthStr;

fn key(code: KeyCode) -> Event {
    Event::Key(KeyEvent::new(code, KeyModifiers::NONE))
}

fn packet() -> Value {
    json!({
        "schema_version": 1,
        "title": "Model comparison notes",
        "purpose": "Inspect the inputs before running models.",
        "notes": [
            {
                "id": "H23", "title": "Homemade buns", "note_id": "a".repeat(64),
                "text": "My bunz #Bread #homemade\n\nhttps://example.com/image.jpg",
                "why": "An ordinary post whose hashtags add context.",
                "source": {"path": "input.json", "index": 23}
            },
            {
                "id": "H05", "title": "Conditional trade", "note_id": "b".repeat(64),
                "text": "A player may request a trade if the team struggles.",
                "why": "Check that a possibility remains conditional.",
                "source": {"path": "input.json", "index": 5}
            }
        ]
    })
}

fn load(data: &Value, start_at: Option<&str>) -> NoteSampleReview {
    let directory = tempfile::tempdir().unwrap();
    let path = directory.path().join("selection.json");
    fs::write(&path, serde_json::to_vec(data).unwrap()).unwrap();
    NoteSampleReview::load(path, start_at).unwrap()
}

fn render(model: &mut NoteSampleReview, width: u16, height: u16) -> String {
    let mut terminal = Terminal::new(TestBackend::new(width, height)).unwrap();
    terminal.draw(|frame| model.render(frame)).unwrap();
    let buffer = terminal.backend().buffer();
    (0..height)
        .map(|y| {
            let mut line = String::new();
            let mut x = 0;
            while x < width {
                let symbol = buffer[(x, y)].symbol();
                line.push_str(symbol);
                // Wide glyphs occupy two terminal cells; the second is not another space.
                x += u16::try_from(symbol.width().max(1)).unwrap();
            }
            line
        })
        .collect::<Vec<_>>()
        .join("\n")
}

#[test]
fn displays_original_note_and_reason_without_annotation_decisions() {
    let mut model = load(&packet(), None);
    let screen = render(&mut model, 80, 24);
    for expected in [
        "H23",
        "1 of 2",
        "Homemade buns",
        "Complete note",
        "My bunz",
        "#Bread #homemade",
        "https://example.com/image.jpg",
        "Why included",
        "An ordinary post whose hashtags add context.",
        "Read-only",
    ] {
        assert!(screen.contains(expected), "Missing {expected}:\n{screen}");
    }
    for absent in ["Approve", "Disapprove", "Mask review", "Proposed subjects"] {
        assert!(!screen.contains(absent), "Unexpected {absent}");
    }
}

#[test]
fn previous_and_next_visit_every_note_without_decisions() {
    let mut model = load(&packet(), Some("H05"));
    assert!(render(&mut model, 80, 24).contains("2 of 2"));
    for code in [
        KeyCode::Right,
        KeyCode::Char('l'),
        KeyCode::Char('n'),
        KeyCode::Left,
        KeyCode::Char('h'),
        KeyCode::Char('p'),
    ] {
        assert_eq!(model.handle_event(key(code)), NoteSampleReviewAction::None);
        assert!(render(&mut model, 80, 24).contains("H23"));
        model.handle_event(key(code));
        assert!(render(&mut model, 80, 24).contains("H05"));
    }
}

#[test]
fn long_notes_scroll_to_the_end_and_reset_on_navigation() {
    let mut data = packet();
    data["notes"][0]["text"] = json!(format!(
        "First line 日本語\n{}\nLast line",
        "A complete source line.\n".repeat(80)
    ));
    let mut model = load(&data, None);
    assert!(render(&mut model, 72, 24).contains("First line 日本語"));
    model.handle_event(key(KeyCode::Char('G')));
    let bottom = render(&mut model, 72, 24);
    assert!(bottom.contains("Last line"), "{bottom}");
    assert!(bottom.contains("Why included"));
    model.handle_event(key(KeyCode::Right));
    model.handle_event(key(KeyCode::Left));
    assert!(render(&mut model, 72, 24).contains("First line 日本語"));
    for _ in 0..100 {
        model.handle_event(key(KeyCode::Char('j')));
        render(&mut model, 72, 24);
    }
    assert!(render(&mut model, 72, 24).contains("Last line"));
    model.handle_event(key(KeyCode::Home));
    assert!(render(&mut model, 72, 24).contains("First line 日本語"));
}

#[test]
fn both_panels_are_scrollable_and_exiting_does_not_require_review() {
    let mut data = packet();
    data["notes"][0]["why"] = json!(format!(
        "Reason begins\n{}\nReason ends",
        "Supporting detail.\n".repeat(30)
    ));
    let mut model = load(&data, None);
    render(&mut model, 72, 24);
    model.handle_event(key(KeyCode::Tab));
    model.handle_event(key(KeyCode::End));
    assert!(render(&mut model, 72, 24).contains("Reason ends"));
    for event in [
        key(KeyCode::Char('q')),
        key(KeyCode::Esc),
        Event::Key(KeyEvent::new(KeyCode::Char('c'), KeyModifiers::CONTROL)),
    ] {
        assert_eq!(model.handle_event(event), NoteSampleReviewAction::Quit);
    }
    let small = render(&mut model, 40, 12);
    assert!(small.contains("Resize"));
}

#[test]
fn rejects_bad_selection_or_unknown_start_before_opening_terminal() {
    let directory = tempfile::tempdir().unwrap();
    let path = directory.path().join("selection.json");
    let mut bad = packet();
    bad["notes"][1]["id"] = json!("H23");
    fs::write(&path, serde_json::to_vec(&bad).unwrap()).unwrap();
    assert!(NoteSampleReview::load(&path, None).is_err());
    bad = packet();
    bad["notes"] = json!([]);
    fs::write(&path, serde_json::to_vec(&bad).unwrap()).unwrap();
    assert!(NoteSampleReview::load(&path, None).is_err());
    let original = serde_json::to_vec(&packet()).unwrap();
    fs::write(&path, &original).unwrap();
    assert!(NoteSampleReview::load(&path, Some("missing")).is_err());
    let mut model = NoteSampleReview::load(&path, None).unwrap();
    model.handle_event(key(KeyCode::Right));
    model.handle_event(key(KeyCode::Char('q')));
    assert_eq!(fs::read(&path).unwrap(), original);
    assert_eq!(fs::read_dir(directory.path()).unwrap().count(), 1);
}

#[test]
fn cli_validates_before_raw_mode_and_provides_plain_help() {
    let binary = env!("CARGO_BIN_EXE_note-sample-review");
    let help = std::process::Command::new(binary)
        .arg("--help")
        .output()
        .unwrap();
    assert!(help.status.success());
    assert!(String::from_utf8_lossy(&help.stdout).contains("No model calls or saved decisions"));
    let directory = tempfile::tempdir().unwrap();
    let path = directory.path().join("selection.json");
    fs::write(&path, serde_json::to_vec(&packet()).unwrap()).unwrap();
    let invalid = std::process::Command::new(binary)
        .arg(&path)
        .args(["--start-at", "absent"])
        .output()
        .unwrap();
    assert!(!invalid.status.success());
    assert!(String::from_utf8_lossy(&invalid.stderr).contains("unknown note: absent"));
    let redirected = std::process::Command::new(binary)
        .arg(&path)
        .output()
        .unwrap();
    assert!(!redirected.status.success());
    assert!(String::from_utf8_lossy(&redirected.stderr).contains("interactive terminal"));
    assert!(redirected.stdout.is_empty());
}
