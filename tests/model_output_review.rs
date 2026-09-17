use std::fs;
use std::process::Command;

use crossterm::event::{Event, KeyCode, KeyEvent, KeyModifiers};
use oracle_mvp::model_output_review::{ModelOutputReview, ModelOutputReviewAction};
use ratatui::{Terminal, backend::TestBackend};
use serde_json::{Value, json};
use unicode_width::UnicodeWidthStr;

fn key(code: KeyCode) -> Event {
    Event::Key(KeyEvent::new(code, KeyModifiers::NONE))
}

fn packet() -> Value {
    let results = json!([
        {"model": "Astra", "output": "1. Archived Astra subject.", "comment": "Astra is a reference, not gold."},
        {"model": "DeepSeek", "output": "1. DeepSeek subject.", "comment": "DeepSeek comment."},
        {"model": "Muse", "output": "1. Muse subject.", "comment": "Muse comment."},
        {"model": "GLM", "output": "FAILED: no valid output (HTTP error).", "comment": "No GLM subjects are available."}
    ]);
    json!({
        "schema_version": 1,
        "title": "Saved subject comparison",
        "notes": [
            {"id": "H06", "title": "First note", "text": "Original first note 日本語\nhttps://example.com/",
             "model_input": "Prepared first note.", "results": results},
            {"id": "H21", "title": "Second note", "text": "Original second note.", "results": results}
        ]
    })
}

fn load(data: &Value, start_at: Option<&str>) -> ModelOutputReview {
    let directory = tempfile::tempdir().unwrap();
    let path = directory.path().join("review.json");
    fs::write(&path, serde_json::to_vec(data).unwrap()).unwrap();
    ModelOutputReview::load(path, start_at).unwrap()
}

fn render(model: &mut ModelOutputReview, width: u16, height: u16) -> String {
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
                x += u16::try_from(symbol.width().max(1)).unwrap();
            }
            line
        })
        .collect::<Vec<_>>()
        .join("\n")
}

#[test]
fn original_note_output_and_separate_comments_are_visible_at_both_layout_sizes() {
    for (width, height) in [(72, 24), (120, 32)] {
        let mut model = load(&packet(), None);
        let screen = render(&mut model, width, height);
        for expected in [
            "Read-only",
            "H06",
            "1 of 2",
            "Complete note",
            "Original first note 日本語",
            "Astra",
            "DeepSeek",
            "Muse",
            "GLM",
            "Archived Astra subject.",
            "My comments",
            "Astra is a reference, not gold.",
        ] {
            assert!(screen.contains(expected), "Missing {expected}:\n{screen}");
        }
        for absent in ["Approve", "Disapprove", "Title review", "Masks"] {
            assert!(!screen.contains(absent), "Unexpected {absent}:\n{screen}");
        }
    }
}

#[test]
fn model_selection_keeps_note_and_note_navigation_keeps_model() {
    let mut model = load(&packet(), None);
    for (code, output) in [
        ('2', "DeepSeek subject."),
        ('3', "Muse subject."),
        ('4', "FAILED: no valid output"),
        (']', "Archived Astra subject."),
        ('[', "FAILED: no valid output"),
    ] {
        model.handle_event(key(KeyCode::Char(code)));
        let screen = render(&mut model, 72, 24);
        assert!(screen.contains("Original first note"), "{screen}");
        assert!(screen.contains(output), "{screen}");
    }
    for code in [
        KeyCode::Right,
        KeyCode::Char('l'),
        KeyCode::Char('n'),
        KeyCode::Left,
        KeyCode::Char('h'),
        KeyCode::Char('p'),
    ] {
        model.handle_event(key(code));
        let screen = render(&mut model, 72, 24);
        assert!(screen.contains("H21"), "{screen}");
        assert!(screen.contains("FAILED: no valid output"), "{screen}");
        model.handle_event(key(code));
        assert!(render(&mut model, 72, 24).contains("H06"));
    }
}

#[test]
fn every_pane_reaches_last_line_at_minimum_size_and_scroll_resets_are_scoped() {
    let mut data = packet();
    data["notes"][0]["text"] = json!(format!(
        "Note first\n{}Note last",
        "A long source line.\n".repeat(80)
    ));
    for result in data["notes"][0]["results"].as_array_mut().unwrap() {
        result["output"] = json!(format!(
            "Output first\n{}Output last",
            "A long subject line.\n".repeat(80)
        ));
        result["comment"] = json!(format!(
            "Comment first\n{}Comment last",
            "A long comment line.\n".repeat(80)
        ));
    }
    let mut model = load(&data, None);
    render(&mut model, 72, 24);
    for last in ["Note last", "Output last", "Comment last"] {
        model.handle_event(key(KeyCode::Char('G')));
        let screen = render(&mut model, 72, 24);
        assert!(screen.contains(last), "{screen}");
        model.handle_event(key(KeyCode::Tab));
    }
    model.handle_event(key(KeyCode::Char('2')));
    let screen = render(&mut model, 72, 24);
    assert!(screen.contains("Note last"), "{screen}");
    assert!(screen.contains("Output first"), "{screen}");
    assert!(screen.contains("Comment first"), "{screen}");
    model.handle_event(key(KeyCode::Right));
    model.handle_event(key(KeyCode::Left));
    let screen = render(&mut model, 72, 24);
    assert!(screen.contains("Note first"), "{screen}");
    assert!(screen.contains("Output first"), "{screen}");
    assert!(screen.contains("Comment first"), "{screen}");
}

#[test]
fn page_half_page_line_and_reverse_tab_controls_scroll_focused_pane() {
    let mut data = packet();
    data["notes"][0]["text"] = json!(
        (0..80)
            .map(|i| format!("Source line {i:02}"))
            .collect::<Vec<_>>()
            .join("\n")
    );
    data["notes"][0]["results"][0]["comment"] = json!(
        (0..80)
            .map(|i| format!("Comment line {i:02}"))
            .collect::<Vec<_>>()
            .join("\n")
    );
    let mut model = load(&data, None);
    let top = render(&mut model, 72, 24);
    for code in [KeyCode::Down, KeyCode::Char('j'), KeyCode::PageDown] {
        model.handle_event(key(code));
        assert!(!render(&mut model, 72, 24).contains("Source line 00"));
        model.handle_event(key(KeyCode::Home));
    }
    model.handle_event(Event::Key(KeyEvent::new(
        KeyCode::Char('d'),
        KeyModifiers::CONTROL,
    )));
    assert!(!render(&mut model, 72, 24).contains("Source line 00"));
    model.handle_event(Event::Key(KeyEvent::new(
        KeyCode::Char('u'),
        KeyModifiers::CONTROL,
    )));
    assert_eq!(render(&mut model, 72, 24), top);
    model.handle_event(key(KeyCode::PageDown));
    model.handle_event(key(KeyCode::PageUp));
    assert_eq!(render(&mut model, 72, 24), top);
    model.handle_event(key(KeyCode::Down));
    model.handle_event(key(KeyCode::Up));
    assert_eq!(render(&mut model, 72, 24), top);
    model.handle_event(key(KeyCode::Char('j')));
    model.handle_event(key(KeyCode::Char('k')));
    assert_eq!(render(&mut model, 72, 24), top);
    model.handle_event(key(KeyCode::BackTab));
    model.handle_event(key(KeyCode::End));
    let bottom = render(&mut model, 72, 24);
    assert!(bottom.contains("Comment line 79"), "{bottom}");
    assert!(bottom.contains("Source line 00"), "{bottom}");
    model.handle_event(key(KeyCode::Char('g')));
    assert!(render(&mut model, 72, 24).contains("Comment line 00"));
}

#[test]
fn prepared_input_is_explicitly_toggled_and_exit_never_requires_decisions() {
    let mut model = load(&packet(), Some("H06"));
    model.handle_event(key(KeyCode::Char('i')));
    let prepared = render(&mut model, 72, 24);
    assert!(prepared.contains("Model input"), "{prepared}");
    assert!(prepared.contains("Prepared first note."), "{prepared}");
    assert!(!prepared.contains("Original first note"), "{prepared}");
    model.handle_event(key(KeyCode::Char('i')));
    assert!(render(&mut model, 72, 24).contains("Original first note"));
    model.handle_event(key(KeyCode::Right));
    model.handle_event(key(KeyCode::Char('i')));
    assert!(render(&mut model, 72, 24).contains("Original second note"));
    for event in [
        key(KeyCode::Char('q')),
        key(KeyCode::Esc),
        Event::Key(KeyEvent::new(KeyCode::Char('c'), KeyModifiers::CONTROL)),
    ] {
        assert_eq!(model.handle_event(event), ModelOutputReviewAction::Quit);
    }
    assert!(render(&mut model, 40, 12).contains("Resize"));
}

#[test]
fn invalid_packets_are_rejected_and_review_leaves_input_directory_unchanged() {
    let directory = tempfile::tempdir().unwrap();
    let path = directory.path().join("review.json");
    let changes: Vec<(&str, Value)> = vec![
        ("/schema_version", json!(2)),
        ("/title", json!(" ")),
        ("/notes", json!([])),
        ("/notes/0/id", json!("H21")),
        ("/notes/0/title", json!("")),
        ("/notes/0/text", json!("")),
        ("/notes/0/model_input", json!(" ")),
        ("/notes/0/results", json!([])),
        ("/notes/0/results/0/model", json!("")),
        ("/notes/0/results/0/output", json!("")),
        ("/notes/0/results/0/comment", json!("")),
        ("/notes/1/results/0/model", json!("Different")),
        ("/notes/0/results/1/model", json!("Astra")),
    ];
    for (pointer, value) in changes {
        let mut bad = packet();
        *bad.pointer_mut(pointer).unwrap() = value;
        fs::write(&path, serde_json::to_vec(&bad).unwrap()).unwrap();
        assert!(
            ModelOutputReview::load(&path, None).is_err(),
            "Accepted invalid {pointer}"
        );
    }
    let original = serde_json::to_vec(&packet()).unwrap();
    fs::write(&path, &original).unwrap();
    assert!(ModelOutputReview::load(&path, Some("missing")).is_err());
    let mut model = ModelOutputReview::load(&path, None).unwrap();
    model.handle_event(key(KeyCode::Right));
    model.handle_event(key(KeyCode::Char('4')));
    render(&mut model, 72, 24);
    model.handle_event(key(KeyCode::Char('q')));
    assert_eq!(fs::read(&path).unwrap(), original);
    assert_eq!(fs::read_dir(directory.path()).unwrap().count(), 1);
}

#[test]
fn cli_check_and_help_work_without_a_terminal_and_invalid_start_is_validated_first() {
    let binary = env!("CARGO_BIN_EXE_model-output-review");
    let directory = tempfile::tempdir().unwrap();
    let path = directory.path().join("review.json");
    fs::write(&path, serde_json::to_vec(&packet()).unwrap()).unwrap();
    let help = Command::new(binary).arg("--help").output().unwrap();
    assert!(help.status.success());
    assert!(String::from_utf8_lossy(&help.stdout).contains("No model calls or saved decisions"));
    let checked = Command::new(binary)
        .arg(&path)
        .arg("--check")
        .output()
        .unwrap();
    assert!(
        checked.status.success(),
        "{}",
        String::from_utf8_lossy(&checked.stderr)
    );
    let summary = String::from_utf8_lossy(&checked.stdout);
    assert!(
        summary.contains("2 notes") && summary.contains("4 models"),
        "{summary}"
    );
    let invalid = Command::new(binary)
        .arg(&path)
        .args(["--start-at", "missing"])
        .output()
        .unwrap();
    assert!(!invalid.status.success());
    assert!(String::from_utf8_lossy(&invalid.stderr).contains("unknown note: missing"));
    let redirected = Command::new(binary).arg(&path).output().unwrap();
    assert!(!redirected.status.success());
    assert!(String::from_utf8_lossy(&redirected.stderr).contains("interactive terminal"));
    assert!(redirected.stdout.is_empty());
    assert_eq!(fs::read_dir(directory.path()).unwrap().count(), 1);
}

#[test]
fn saved_diagnostic_failure_long_output_and_prepared_input_are_accessible() {
    let path = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("sse_multivector/frontier-model-comparison-v1/asv6.23-diagnostic-v2/review.json");
    let mut model = ModelOutputReview::load(&path, Some("H06")).unwrap();
    model.handle_event(key(KeyCode::Char('4')));
    let failure = render(&mut model, 72, 24);
    for expected in [
        "Astra (saved)",
        "Muse",
        "DeepSeek",
        "GLM",
        "Complete note",
        "My comments",
        "No output",
        "HTTP 429",
    ] {
        assert!(failure.contains(expected), "Missing {expected}:\n{failure}");
    }
    println!("72 × 24 saved-diagnostic screen:\n{failure}");

    let mut model = ModelOutputReview::load(&path, Some("H48")).unwrap();
    model.handle_event(key(KeyCode::Char('3')));
    render(&mut model, 72, 24);
    model.handle_event(key(KeyCode::Tab));
    model.handle_event(key(KeyCode::End));
    let bottom = render(&mut model, 72, 24);
    assert!(bottom.contains("27. Tor."), "{bottom}");
    assert!(bottom.contains("Complete note"), "{bottom}");
    assert!(bottom.contains("My comments"), "{bottom}");

    let mut model = ModelOutputReview::load(&path, Some("H49")).unwrap();
    let original = render(&mut model, 72, 24);
    assert!(original.contains("Complete note"), "{original}");
    model.handle_event(key(KeyCode::Char('i')));
    let prepared = render(&mut model, 72, 24);
    assert!(prepared.contains("Model input"), "{prepared}");
    assert_ne!(prepared, original);
    model.handle_event(key(KeyCode::Char('i')));
    assert_eq!(render(&mut model, 72, 24), original);

    let wide = render(&mut model, 120, 32);
    let note_border = wide
        .lines()
        .position(|line| line.contains("Complete note"))
        .unwrap();
    let output_border = wide
        .lines()
        .position(|line| line.contains("Astra (saved) output"))
        .unwrap();
    assert_eq!(
        note_border, output_border,
        "Wide layout should put source and output side-by-side:\n{wide}"
    );
}
