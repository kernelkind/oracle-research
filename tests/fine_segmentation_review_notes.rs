use std::collections::VecDeque;
use std::fs;
use std::io;

use crossterm::event::{Event, KeyCode, KeyEvent, KeyModifiers};
use oracle_mvp::fine_segmentation_review::{
    FineSegmentationReviewAction, FineSegmentationReviewRunOutcome, FineSegmentationReviewTuiModel,
    FineSegmentationReviewUi, run_fine_segmentation_review,
};
use ratatui::Terminal;
use ratatui::backend::TestBackend;
use serde_json::{Value, json};

fn reviewer() -> Value {
    json!({
        "schema_version": 3,
        "review_set": "real-note-review",
        "instructions": {
            "question": "For each packet, decide whether all instances are recognizable as refinements of one fine subject.",
            "valid": "Every instance is recognizable as a refinement of one fine subject.",
            "invalid": "No one recognizable, non-disjunctive fine subject covers every instance.",
            "uncertain": "The masks do not support a confident valid/invalid decision."
        },
        "packets": [{
            "packet": "S001",
            "question": "Are all instances recognizable as refinements of one fine subject?",
            "verdicts": ["valid", "invalid", "uncertain"],
            "instances": [{
                "instance": "V001",
                "note_id": "a".repeat(64),
                "vector_id": "1".repeat(64),
                "text": "café\tfirst café end",
                "byte_spans": [[12, 17]]
            }, {
                "instance": "V002",
                "note_id": "b".repeat(64),
                "vector_id": "2".repeat(64),
                "text": "Other complete original note.",
                "byte_spans": [[0, 5]]
            }]
        }],
        "response_contract": {
            "schema_version": 3,
            "review_set": "real-note-review",
            "judgments": "zero or one judgment for every packet",
            "judgment_fields": ["packet", "verdict", "comment"],
            "allowed_verdicts": ["valid", "invalid", "uncertain"]
        }
    })
}

fn render(model: &mut FineSegmentationReviewTuiModel) -> String {
    let mut terminal = Terminal::new(TestBackend::new(100, 32)).expect("test terminal");
    terminal.draw(|frame| model.render(frame)).expect("render");
    let buffer = terminal.backend().buffer();
    (0..32)
        .map(|y| {
            (0..100)
                .map(|x| buffer[(x, y)].symbol())
                .collect::<String>()
        })
        .collect::<Vec<_>>()
        .join("\n")
}

struct PausingUi {
    rendered: String,
}

impl FineSegmentationReviewUi for PausingUi {
    fn review(
        &mut self,
        model: &mut FineSegmentationReviewTuiModel,
        _drain_stale_input: bool,
    ) -> io::Result<FineSegmentationReviewAction> {
        self.rendered = render(model);
        Ok(FineSegmentationReviewAction::Pause)
    }
}

#[test]
fn full_note_review_accepts_one_segment_and_highlights_the_chosen_utf8_occurrence() {
    let root = tempfile::tempdir_in("/dev/shm").expect("temporary directory");
    let input = root.path().join("review.json");
    let session = root.path().join("session.json");
    let response = root.path().join("response.json");
    fs::write(
        &input,
        serde_json::to_vec(&reviewer()).expect("encode reviewer"),
    )
    .expect("write reviewer");
    let mut ui = PausingUi {
        rendered: String::new(),
    };
    let outcome = run_fine_segmentation_review(&input, &session, &response, &mut ui)
        .expect("open one complete-note segment with exact UTF-8 mask");
    assert_eq!(outcome, FineSegmentationReviewRunOutcome::Paused);
    assert!(ui.rendered.contains("Segment 1 of 1"), "{}", ui.rendered);
    assert!(
        ui.rendered.contains("café    first ⟦café⟧ end"),
        "{}",
        ui.rendered
    );
    assert!(!ui.rendered.contains("Other complete original note."));
    let response: Value = serde_json::from_slice(&fs::read(response).expect("partial response"))
        .expect("decode partial response");
    assert_eq!(response["judgments"], json!([]));
}

struct EventUi {
    events: VecDeque<Event>,
    frames: Vec<String>,
}

#[test]
fn segment_shows_all_four_masks_together_without_text_outside_the_masks() {
    let root = tempfile::tempdir_in("/dev/shm").unwrap();
    let input = root.path().join("review.json");
    let mut artifact = reviewer();
    let instances = artifact["packets"][0]["instances"].as_array_mut().unwrap();
    for (index, text, spans) in [
        (
            3,
            "Before my gap Blueberry cheesecake after",
            json!([[7, 9], [14, 34]]),
        ),
        (4, "Before fourth mask after", json!([[7, 18]])),
    ] {
        instances.push(json!({
            "instance": format!("V{index:03}"),
            "note_id": format!("{index:064x}"),
            "vector_id": format!("{:064x}", index + 10),
            "text": text,
            "byte_spans": spans
        }));
    }
    let original = serde_json::to_vec(&artifact).unwrap();
    fs::write(&input, &original).unwrap();
    let mut ui = PausingUi {
        rendered: String::new(),
    };
    run_fine_segmentation_review(
        &input,
        root.path().join("session.json"),
        root.path().join("response.json"),
        &mut ui,
    )
    .unwrap();
    for expected in [
        "Masks · 4",
        "V001",
        "⟦café⟧",
        "V002",
        "⟦Other⟧",
        "V003",
        "⟦my⟧ ⟦Blueberry cheesecake⟧",
        "V004",
        "⟦fourth mask⟧",
    ] {
        assert!(
            ui.rendered.contains(expected),
            "missing {expected}:\n{}",
            ui.rendered
        );
    }
    for outside in [
        "first",
        "complete original note",
        "Before",
        " gap ",
        "⟧ after",
        "Note 1 of 4",
        "[Tab/Shift-Tab]",
    ] {
        assert!(
            !ui.rendered.contains(outside),
            "unexpected {outside}:\n{}",
            ui.rendered
        );
    }
    assert_eq!(fs::read(&input).unwrap(), original);
}

impl EventUi {
    fn new(events: impl IntoIterator<Item = Event>) -> Self {
        Self {
            events: events.into_iter().collect(),
            frames: Vec::new(),
        }
    }
}

impl FineSegmentationReviewUi for EventUi {
    fn review(
        &mut self,
        model: &mut FineSegmentationReviewTuiModel,
        _drain_stale_input: bool,
    ) -> io::Result<FineSegmentationReviewAction> {
        loop {
            self.frames.push(render(model));
            let event = self.events.pop_front().expect("scripted terminal event");
            let action = model.handle_event(event);
            if action != FineSegmentationReviewAction::None {
                return Ok(action);
            }
        }
    }
}

fn key(code: KeyCode) -> Event {
    Event::Key(KeyEvent::new(code, KeyModifiers::NONE))
}

fn pause() -> Event {
    Event::Key(KeyEvent::new(KeyCode::Char('c'), KeyModifiers::CONTROL))
}

fn read_json(path: impl AsRef<std::path::Path>) -> Value {
    serde_json::from_slice(&fs::read(path).expect("read JSON")).expect("decode JSON")
}

#[test]
fn decisions_comments_skips_and_note_position_survive_partial_review_and_resumption() {
    let root = tempfile::tempdir_in("/dev/shm").unwrap();
    let input = root.path().join("review.json");
    let session = root.path().join("session.json");
    let response = root.path().join("response.json");
    let mut artifact = reviewer();
    let mut second = artifact["packets"][0].clone();
    second["packet"] = json!("S002");
    artifact["packets"].as_array_mut().unwrap().push(second);
    fs::write(&input, serde_json::to_vec(&artifact).unwrap()).unwrap();
    let mut first = EventUi::new([
        key(KeyCode::Char('c')),
        Event::Paste("specific mask evidence".into()),
        key(KeyCode::Enter),
        key(KeyCode::Char('v')),
        key(KeyCode::Enter),
        key(KeyCode::Char('s')),
        key(KeyCode::Tab),
        pause(),
    ]);
    assert_eq!(
        run_fine_segmentation_review(&input, &session, &response, &mut first).unwrap(),
        FineSegmentationReviewRunOutcome::Paused
    );
    let saved = read_json(&session);
    assert_eq!(saved["session"]["current_packet_index"], 1);
    assert_eq!(saved["session"]["current_instance_index"], 1);
    assert_eq!(saved["session"]["packets"][1]["state"]["status"], "skipped");
    assert_eq!(
        read_json(&response)["judgments"],
        json!([{
            "packet": "S001", "verdict": "valid", "comment": "specific mask evidence"
        }])
    );
    assert!(
        first
            .frames
            .iter()
            .any(|frame| frame.contains("⟦Other⟧ complete original note."))
    );

    let mut resumed = EventUi::new([
        key(KeyCode::Char('u')),
        key(KeyCode::Enter),
        key(KeyCode::Left),
        key(KeyCode::Char('c')),
        Event::Paste(" revised".into()),
        key(KeyCode::Enter),
        key(KeyCode::Char('i')),
        key(KeyCode::Enter),
        pause(),
    ]);
    run_fine_segmentation_review(&input, &session, &response, &mut resumed).unwrap();
    assert!(resumed.frames[0].contains("Segment 2 of 2"));
    assert!(resumed.frames[0].contains("⟦Other⟧ complete original note."));
    assert!(resumed.frames[0].contains("skipped"));
    assert_eq!(
        read_json(&response)["judgments"],
        json!([
            {"packet": "S001", "verdict": "invalid", "comment": "specific mask evidence revised"},
            {"packet": "S002", "verdict": "uncertain", "comment": ""}
        ])
    );
}

#[test]
fn full_notes_scroll_cycle_and_keep_instructions_outside_source_text() {
    let root = tempfile::tempdir_in("/dev/shm").unwrap();
    let input = root.path().join("review.json");
    let mut artifact = reviewer();
    artifact["packets"][0]["instances"][0]["text"] = json!(
        (0..70)
            .map(|line| format!("Original note line {line:02}"))
            .collect::<Vec<_>>()
            .join("\n")
    );
    artifact["packets"][0]["instances"][0]["byte_spans"] = json!([[0, 8]]);
    fs::write(&input, serde_json::to_vec(&artifact).unwrap()).unwrap();
    let mut ui = EventUi::new([
        key(KeyCode::PageDown),
        key(KeyCode::Home),
        key(KeyCode::Tab),
        key(KeyCode::BackTab),
        pause(),
    ]);
    run_fine_segmentation_review(
        &input,
        root.path().join("session.json"),
        root.path().join("response.json"),
        &mut ui,
    )
    .unwrap();
    assert!(ui.frames[0].contains("⟦Original⟧ note line 00"));
    assert!(!ui.frames[1].contains("note line 00"));
    assert!(ui.frames[2].contains("⟦Original⟧ note line 00"));
    assert!(ui.frames[3].contains("⟦Other⟧ complete original note."));
    assert!(ui.frames[4].contains("⟦Original⟧ note line 00"));
}

#[test]
fn empty_review_renders_no_segments_and_records_no_judgments() {
    let root = tempfile::tempdir_in("/dev/shm").unwrap();
    let input = root.path().join("review.json");
    let response = root.path().join("response.json");
    let mut artifact = reviewer();
    artifact["packets"] = json!([]);
    fs::write(&input, serde_json::to_vec(&artifact).unwrap()).unwrap();
    let mut ui = PausingUi {
        rendered: String::new(),
    };
    let result =
        run_fine_segmentation_review(&input, root.path().join("session.json"), &response, &mut ui)
            .unwrap();
    assert_eq!(
        result,
        FineSegmentationReviewRunOutcome::Completed {
            valid: 0,
            invalid: 0,
            uncertain: 0,
        }
    );
    assert!(ui.rendered.contains("No segments"));
    assert_eq!(read_json(response)["judgments"], json!([]));
}

#[test]
fn invalid_masks_and_conflicting_source_evidence_are_rejected_before_review() {
    let mut cases = Vec::new();
    for spans in [
        json!([[16, 17]]),
        json!([[12, 30]]),
        json!([[12, 17], [14, 17]]),
        json!([]),
    ] {
        let mut artifact = reviewer();
        artifact["packets"][0]["instances"][0]["byte_spans"] = spans;
        cases.push(artifact);
    }
    let mut conflicting_note = reviewer();
    conflicting_note["packets"][0]["instances"][1]["note_id"] = json!("a".repeat(64));
    cases.push(conflicting_note);
    let mut duplicate_vector = reviewer();
    duplicate_vector["packets"][0]["instances"][1]["vector_id"] = json!("1".repeat(64));
    cases.push(duplicate_vector);
    let mut generated_title = reviewer();
    generated_title["packets"][0]["title"] = json!("Not permitted");
    cases.push(generated_title);
    for artifact in cases {
        let root = tempfile::tempdir_in("/dev/shm").unwrap();
        let input = root.path().join("review.json");
        let session = root.path().join("session.json");
        fs::write(&input, serde_json::to_vec(&artifact).unwrap()).unwrap();
        let mut ui = PausingUi {
            rendered: String::new(),
        };
        assert!(
            run_fine_segmentation_review(
                &input,
                &session,
                root.path().join("response.json"),
                &mut ui,
            )
            .is_err()
        );
        assert!(ui.rendered.is_empty());
        assert!(!session.exists());
    }
}

#[test]
fn save_and_exit_preserves_a_comment_being_edited() {
    let root = tempfile::tempdir_in("/dev/shm").unwrap();
    let input = root.path().join("review.json");
    let session = root.path().join("session.json");
    let response = root.path().join("response.json");
    fs::write(&input, serde_json::to_vec(&reviewer()).unwrap()).unwrap();
    let mut ui = EventUi::new([
        key(KeyCode::Char('c')),
        Event::Paste("unfinished comment retained on exit".into()),
        pause(),
    ]);
    run_fine_segmentation_review(&input, &session, &response, &mut ui).unwrap();
    assert_eq!(
        read_json(&session)["session"]["packets"][0]["comment"],
        "unfinished comment retained on exit"
    );
    let mut resumed = EventUi::new([pause()]);
    run_fine_segmentation_review(&input, &session, &response, &mut resumed).unwrap();
    assert!(resumed.frames[0].contains("unfinished comment retained on exit"));
    assert_eq!(read_json(response)["judgments"], json!([]));
}

#[test]
fn cancelling_an_unconfirmed_verdict_restores_a_skipped_segment_after_resume() {
    let root = tempfile::tempdir_in("/dev/shm").unwrap();
    let input = root.path().join("review.json");
    let session = root.path().join("session.json");
    let response = root.path().join("response.json");
    fs::write(&input, serde_json::to_vec(&reviewer()).unwrap()).unwrap();
    let mut ui = EventUi::new([key(KeyCode::Char('s')), key(KeyCode::Char('v')), pause()]);
    run_fine_segmentation_review(&input, &session, &response, &mut ui).unwrap();
    let mut resumed = EventUi::new([key(KeyCode::Esc), pause()]);
    run_fine_segmentation_review(&input, &session, &response, &mut resumed).unwrap();
    assert_eq!(
        read_json(&session)["session"]["packets"][0]["state"]["status"],
        "skipped"
    );
    assert_eq!(read_json(response)["judgments"], json!([]));
}

#[test]
fn an_existing_response_is_not_erased_when_the_session_path_is_missing() {
    let root = tempfile::tempdir_in("/dev/shm").unwrap();
    let input = root.path().join("review.json");
    let session = root.path().join("session.json");
    let response = root.path().join("response.json");
    fs::write(&input, serde_json::to_vec(&reviewer()).unwrap()).unwrap();
    let mut ui = EventUi::new([key(KeyCode::Char('v')), key(KeyCode::Enter), pause()]);
    run_fine_segmentation_review(&input, &session, &response, &mut ui).unwrap();
    let saved = fs::read(&response).unwrap();
    let absent_session = root.path().join("different-session.json");
    let mut reopened = EventUi::new([pause()]);
    assert!(
        run_fine_segmentation_review(&input, &absent_session, &response, &mut reopened).is_err()
    );
    assert_eq!(fs::read(response).unwrap(), saved);
    assert!(!absent_session.exists());
    assert!(reopened.frames.is_empty());
}
