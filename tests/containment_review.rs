use std::fs;

use crossterm::event::{Event, KeyCode, KeyEvent, KeyModifiers};
use oracle_mvp::containment_review::{ContainmentReview, ContainmentReviewAction};
use ratatui::{Terminal, backend::TestBackend};
use serde_json::{Value, json};

fn key(code: KeyCode) -> Event {
    Event::Key(KeyEvent::new(code, KeyModifiers::NONE))
}

fn packet() -> Value {
    json!({
        "schema_version": 1,
        "experiment": "TRUE04",
        "threshold": 0.142,
        "items": [
            {
                "item_id": "I01", "a": "Food", "b": "Nostr",
                "assessment": "Incorrect", "reason": "Food does not contain Nostr.",
                "decisions": [{
                    "id": "S001-contains-S002", "a_id": "S001", "b_id": "S002",
                    "native": true, "score": 0.54680001234, "cutoff": true,
                    "model_input": "premise: This text is about Nostr. hypothesis: This text is about Food."
                }]
            },
            {
                "item_id": "A01", "a": "Coffee", "b": "Coffee shops",
                "assessment": "Ambiguous", "reason": "The relation depends on the intended scope.",
                "decisions": [{
                    "id": "S003-contains-S004", "a_id": "S003", "b_id": "S004",
                    "native": false, "score": 0.2, "cutoff": true,
                    "model_input": "premise: This text is about Coffee shops. hypothesis: This text is about Coffee."
                }]
            }
        ]
    })
}

fn load(data: &Value, start_at: Option<&str>) -> ContainmentReview {
    let directory = tempfile::tempdir().unwrap();
    let input = directory.path().join("pairs.json");
    fs::write(&input, serde_json::to_vec(data).unwrap()).unwrap();
    ContainmentReview::load(input, start_at).unwrap()
}

fn render_at(model: &mut ContainmentReview, width: u16, height: u16) -> String {
    let mut terminal = Terminal::new(TestBackend::new(width, height)).unwrap();
    terminal.draw(|frame| model.render(frame)).unwrap();
    let buffer = terminal.backend().buffer();
    (0..height)
        .map(|y| {
            (0..width)
                .map(|x| buffer[(x, y)].symbol())
                .collect::<String>()
        })
        .collect::<Vec<_>>()
        .join("\n")
}

fn render(model: &mut ContainmentReview) -> String {
    render_at(model, 72, 24)
}

#[test]
fn shows_one_pair_and_navigates_without_deciding() {
    let mut model = load(&packet(), None);
    let initial = render(&mut model);
    for expected in [
        "TRUE04",
        "1 of 2",
        "I01",
        "My assessment: Incorrect",
        "A (parent): Food",
        "B (child): Nostr",
        "Does A contain B?",
        "Native: Yes",
        "Cutoff: Yes",
        "0.142",
        "Score: 0.546800",
        "Food does not contain Nostr.",
    ] {
        assert!(initial.contains(expected), "missing {expected}:\n{initial}");
    }
    assert!(!initial.contains("Coffee shops"), "{initial}");
    assert_eq!(
        model.handle_event(key(KeyCode::Right)),
        ContainmentReviewAction::None
    );
    let next = render(&mut model);
    for expected in [
        "2 of 2",
        "A01",
        "My assessment: Ambiguous",
        "Native: No",
        "Cutoff: Yes",
    ] {
        assert!(next.contains(expected), "missing {expected}:\n{next}");
    }
    assert_eq!(
        model.handle_event(key(KeyCode::Char('q'))),
        ContainmentReviewAction::Quit
    );
}

#[test]
fn all_navigation_aliases_wrap_and_start_at_selects_a_card() {
    let mut model = load(&packet(), Some("A01"));
    assert!(render(&mut model).contains("2 of 2"));
    for code in [KeyCode::Right, KeyCode::Char('l'), KeyCode::Char('n')] {
        model.handle_event(key(code));
        assert!(render(&mut model).contains("I01"));
        model.handle_event(key(code));
        assert!(render(&mut model).contains("A01"));
    }
    for code in [KeyCode::Left, KeyCode::Char('h'), KeyCode::Char('p')] {
        model.handle_event(key(code));
        assert!(render(&mut model).contains("I01"));
        model.handle_event(key(code));
        assert!(render(&mut model).contains("A01"));
    }
}

fn collect_scrolled(model: &mut ContainmentReview) -> String {
    let mut all = render(model);
    for _ in 0..220 {
        model.handle_event(key(KeyCode::Down));
        let rendered = render(model);
        all.push_str(&rendered);
        // Preserve both the screen and its text across visual line wrapping.
        all.push('\n');
        all.push_str(
            &rendered
                .lines()
                .filter_map(|line| line.strip_prefix('│')?.strip_suffix('│'))
                .map(str::trim)
                .collect::<Vec<_>>()
                .join(" "),
        );
    }
    all
}

#[test]
fn exact_details_preserve_every_source_and_full_precision_duplicate_score() {
    let mut data = packet();
    let mut duplicate = data["items"][0]["decisions"][0].clone();
    duplicate["id"] = json!("S005-contains-S002");
    duplicate["a_id"] = json!("S005");
    duplicate["score"] = json!(0.54680000111);
    data["items"][0]["decisions"]
        .as_array_mut()
        .unwrap()
        .push(duplicate);
    let mut model = load(&data, None);
    let summary = render(&mut model);
    assert!(summary.contains("Duplicate-score range:"), "{summary}");
    assert!(summary.contains("0.54680000111"), "{summary}");
    assert!(summary.contains("0.54680001234"), "{summary}");
    assert!(!summary.contains("S001-contains-S002"));
    model.handle_event(key(KeyCode::Char('d')));
    let details = collect_scrolled(&mut model);
    assert!(
        details.contains(
            data["items"][0]["decisions"][0]["model_input"]
                .as_str()
                .unwrap()
        )
    );
    for expected in [
        "Exact details",
        "Full-vocabulary probability",
        "first output token",
        "not calibrated containment confidence",
        "S001-contains-S002",
        "S005-contains-S002",
        "A source: S001",
        "A source: S005",
        "B source: S002",
        "0.54680001234",
        "0.54680000111",
        "Exact model input:",
        "premise: This text is about Nostr.",
        "hypothesis: This text is about Food.",
    ] {
        assert!(details.contains(expected), "missing {expected}:\n{details}");
    }
    model.handle_event(key(KeyCode::Char('d')));
    assert_eq!(render(&mut model), summary);
}

#[test]
fn long_pair_and_reason_are_fully_scrollable_with_visible_controls_and_resize_clamping() {
    let mut data = packet();
    data["items"][0]["a"] = json!(format!("{}PARENT-END", "long parent text ".repeat(65)));
    data["items"][0]["b"] = json!(format!("{}CHILD-END", "long child text ".repeat(65)));
    data["items"][0]["reason"] = json!(format!("{}REASON-END", "unchanged reason ".repeat(65)));
    data["items"][0]["decisions"][0]["model_input"] = json!(format!(
        "premise: This text is about {}. hypothesis: This text is about {}.",
        data["items"][0]["b"].as_str().unwrap(),
        data["items"][0]["a"].as_str().unwrap()
    ));
    let mut model = load(&data, None);
    let initial = render(&mut model);
    let all = collect_scrolled(&mut model);
    for expected in [
        "PARENT-END",
        "CHILD-END",
        "REASON-END",
        "Does A contain B?",
        "Score:",
    ] {
        assert!(all.contains(expected), "missing {expected}");
    }
    let bottom = render(&mut model);
    for expected in [
        "Prev/next",
        "Scroll",
        "PgUp/PgDown",
        "Ctrl-U/Ctrl-D",
        "Exact details",
        "q/Esc/Ctrl-C",
    ] {
        assert!(bottom.contains(expected), "missing {expected}:\n{bottom}");
    }
    assert!(bottom.contains("more above"), "{bottom}");
    assert!(!bottom.contains("more above and below"), "{bottom}");
    let taller = render_at(&mut model, 100, 55);
    assert!(taller.contains("REASON-END"), "{taller}");
    for _ in 0..220 {
        model.handle_event(key(KeyCode::Up));
    }
    assert_eq!(render(&mut model), initial);
    for (down, up) in [
        (key(KeyCode::Char('j')), key(KeyCode::Char('k'))),
        (key(KeyCode::PageDown), key(KeyCode::PageUp)),
        (
            Event::Key(KeyEvent::new(KeyCode::Char('d'), KeyModifiers::CONTROL)),
            Event::Key(KeyEvent::new(KeyCode::Char('u'), KeyModifiers::CONTROL)),
        ),
    ] {
        model.handle_event(down);
        assert_ne!(render(&mut model), initial);
        model.handle_event(up);
        assert_eq!(render(&mut model), initial);
    }
    model.handle_event(key(KeyCode::PageDown));
    model.handle_event(key(KeyCode::Right));
    assert!(render(&mut model).contains("A (parent): Coffee"));
}

#[test]
fn read_only_events_and_exit_never_create_or_change_files() {
    let directory = tempfile::tempdir().unwrap();
    let input = directory.path().join("pairs.json");
    let original = serde_json::to_vec(&packet()).unwrap();
    fs::write(&input, &original).unwrap();
    let mut permissions = fs::metadata(&input).unwrap().permissions();
    permissions.set_readonly(true);
    fs::set_permissions(&input, permissions).unwrap();
    let mut model = ContainmentReview::load(&input, None).unwrap();
    let initial = render(&mut model);
    for event in [
        key(KeyCode::Char('a')),
        key(KeyCode::Char('r')),
        key(KeyCode::Char('s')),
        key(KeyCode::Char('c')),
        key(KeyCode::Enter),
        Event::Paste("no decisions".into()),
    ] {
        assert_eq!(model.handle_event(event), ContainmentReviewAction::None);
        assert_eq!(render(&mut model), initial);
    }
    for event in [
        key(KeyCode::Char('q')),
        key(KeyCode::Esc),
        Event::Key(KeyEvent::new(KeyCode::Char('c'), KeyModifiers::CONTROL)),
    ] {
        assert_eq!(model.handle_event(event), ContainmentReviewAction::Quit);
    }
    assert_eq!(fs::read(&input).unwrap(), original);
    assert_eq!(fs::read_dir(directory.path()).unwrap().count(), 1);
}

#[test]
fn loader_rejects_invalid_or_mismatched_evidence_and_unknown_start_card() {
    let directory = tempfile::tempdir().unwrap();
    let input = directory.path().join("pairs.json");
    let mut invalid = Vec::new();
    for (pointer, value) in [
        ("/schema_version", json!(2)),
        ("/experiment", json!("TRUE03")),
        ("/threshold", json!(0.5)),
        ("/items", json!([])),
        ("/items/0/item_id", json!("")),
        ("/items/0/a", json!(" ")),
        ("/items/0/b", json!("")),
        ("/items/0/reason", json!("")),
        ("/items/0/assessment", json!("Correct")),
        ("/items/0/decisions", json!([])),
        ("/items/0/decisions/0/native", json!("yes")),
        ("/items/0/decisions/0/score", json!(-0.1)),
        ("/items/0/decisions/0/score", json!(1.1)),
        ("/items/0/decisions/0/cutoff", json!(false)),
        (
            "/items/0/decisions/0/model_input",
            json!("reversed or changed input"),
        ),
        ("/items/0/decisions/0/a_id", json!("S999")),
        ("/items/0/decisions/0/b_id", json!("")),
        ("/items/0/decisions/0/id", json!("")),
    ] {
        let mut data = packet();
        *data.pointer_mut(pointer).unwrap() = value;
        invalid.push(data);
    }
    let mut repeated_item = packet();
    repeated_item["items"][1]["item_id"] = json!("I01");
    invalid.push(repeated_item);
    let mut repeated_record = packet();
    let duplicate = repeated_record["items"][0]["decisions"][0].clone();
    repeated_record["items"][0]["decisions"]
        .as_array_mut()
        .unwrap()
        .push(duplicate);
    invalid.push(repeated_record);
    for data in invalid {
        fs::write(&input, serde_json::to_vec(&data).unwrap()).unwrap();
        assert!(
            ContainmentReview::load(&input, None).is_err(),
            "accepted {data}"
        );
    }
    fs::write(
        &input,
        br#"{"schema_version":1,"experiment":"TRUE04","threshold":1e400,"items":[]}"#,
    )
    .unwrap();
    assert!(ContainmentReview::load(&input, None).is_err());
    fs::write(&input, serde_json::to_vec(&packet()).unwrap()).unwrap();
    assert!(ContainmentReview::load(&input, Some("missing")).is_err());
}

#[test]
fn cutoff_is_strictly_greater_than_threshold_and_native_is_independent() {
    let mut data = packet();
    data["items"][0]["decisions"][0]["score"] = json!(0.142);
    data["items"][0]["decisions"][0]["cutoff"] = json!(false);
    let screen = render(&mut load(&data, None));
    assert!(screen.contains("Native: Yes"), "{screen}");
    assert!(screen.contains("Cutoff: No"), "{screen}");
}

#[test]
fn actual_true04_packet_renders_all_eleven_cards_at_72_by_24() {
    let path = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("sse_multivector/navigation-research-v1/TRUE04/review-pairs.json");
    let original = fs::read(&path).unwrap();
    let data: Value = serde_json::from_slice(&original).unwrap();
    let mut model = ContainmentReview::load(&path, None).unwrap();
    for (index, item) in data["items"].as_array().unwrap().iter().enumerate() {
        let screen = render(&mut model);
        assert!(screen.contains(&format!("{} of 11", index + 1)), "{screen}");
        for field in ["item_id", "a", "b", "assessment"] {
            assert!(
                screen.contains(item[field].as_str().unwrap()),
                "missing {field}:\n{screen}"
            );
        }
        assert!(screen.contains("Cutoff: Yes"), "{screen}");
        assert!(screen.contains("Reason:"), "{screen}");
        assert!(
            !screen.contains("more below"),
            "normal card clipped:\n{screen}"
        );
        model.handle_event(key(KeyCode::Right));
    }
    assert!(render(&mut model).contains("1 of 11"));
    assert_eq!(fs::read(path).unwrap(), original);
}

#[test]
fn cli_rejects_redirected_terminals_and_invalid_data_without_escape_sequences() {
    let directory = tempfile::tempdir().unwrap();
    let input = directory.path().join("pairs.json");
    fs::write(&input, serde_json::to_vec(&packet()).unwrap()).unwrap();
    let output = std::process::Command::new(env!("CARGO_BIN_EXE_true-review"))
        .arg(&input)
        .args(["--start-at", "A01"])
        .output()
        .unwrap();
    assert!(!output.status.success());
    assert!(String::from_utf8_lossy(&output.stderr).contains("interactive terminal"));
    assert!(output.stdout.is_empty());
    assert!(!output.stderr.contains(&0x1b));

    let mut data = packet();
    data["items"][0]["decisions"][0]["score"] = json!(0.142);
    fs::write(&input, serde_json::to_vec(&data).unwrap()).unwrap();
    let output = std::process::Command::new(env!("CARGO_BIN_EXE_true-review"))
        .arg(&input)
        .output()
        .unwrap();
    assert!(!output.status.success());
    assert!(String::from_utf8_lossy(&output.stderr).contains("cutoff"));
    assert!(output.stdout.is_empty());
    assert!(!output.stderr.contains(&0x1b));
    assert_eq!(fs::read_dir(directory.path()).unwrap().count(), 1);
}
