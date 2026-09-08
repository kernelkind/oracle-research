use std::collections::VecDeque;
use std::fs;
use std::io;
use std::path::Path;

use crossterm::event::{Event, KeyCode, KeyEvent, KeyModifiers};
use oracle_mvp::fine_segmentation_review::{
    FineSegmentationPacketState, FineSegmentationReviewAction, FineSegmentationReviewRunOutcome,
    FineSegmentationReviewTuiModel, FineSegmentationReviewUi, FineSegmentationReviewVerdict,
    run_fine_segmentation_review,
};
use ratatui::{Terminal, backend::TestBackend};
use serde::{Deserialize, Serialize};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};

fn reviewer(multinote: bool) -> Value {
    let packets = (1..=5)
        .map(|ordinal| {
            let instances = (0..2)
                .map(|index| {
                    let note = ordinal * 10
                        + if multinote && ordinal % 2 == 0 {
                            index
                        } else {
                            0
                        };
                    json!({
                        "instance": format!("V{:03}", ordinal * 10 + index),
                        "note_id": format!("{note:064x}"),
                        "vector_id": format!("{:064x}", 1000 + ordinal * 10 + index),
                        "text": "prefix Alpha gap Omega suffix",
                        "byte_spans": [[7, 12], [17, 22]]
                    })
                })
                .collect::<Vec<_>>();
            json!({
                "packet": format!("S{ordinal:03}"),
                "question": "Are all instances recognizable as refinements of one fine subject?",
                "verdicts": ["valid", "invalid", "uncertain"],
                "instances": instances
            })
        })
        .collect::<Vec<_>>();
    json!({
        "schema_version": 3,
        "review_set": "multinote-review",
        "instructions": {
            "question": "For each packet, decide whether all instances are recognizable as refinements of one fine subject.",
            "valid": "Every instance is recognizable as a refinement of one fine subject.",
            "invalid": "No one recognizable, non-disjunctive fine subject covers every instance.",
            "uncertain": "The masks do not support a confident valid/invalid decision."
        },
        "packets": packets,
        "response_contract": {
            "schema_version": 3,
            "review_set": "multinote-review",
            "judgments": "zero or one judgment for every packet",
            "judgment_fields": ["packet", "verdict", "comment"],
            "allowed_verdicts": ["valid", "invalid", "uncertain"]
        }
    })
}

fn key(code: KeyCode) -> Event {
    Event::Key(KeyEvent::new(code, KeyModifiers::NONE))
}

fn pause() -> Event {
    Event::Key(KeyEvent::new(KeyCode::Char('c'), KeyModifiers::CONTROL))
}

fn read_json(path: impl AsRef<Path>) -> Value {
    serde_json::from_slice(&fs::read(path).unwrap()).unwrap()
}

struct EventUi {
    events: VecDeque<Event>,
    frames: Vec<String>,
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
            let mut terminal = Terminal::new(TestBackend::new(110, 34)).expect("test terminal");
            terminal
                .draw(|frame| model.render(frame))
                .expect("render review");
            let buffer = terminal.backend().buffer();
            self.frames.push(
                (0..34)
                    .map(|y| {
                        (0..110)
                            .map(|x| buffer[(x, y)].symbol())
                            .collect::<String>()
                    })
                    .collect::<Vec<_>>()
                    .join("\n"),
            );
            let action = model.handle_event(self.events.pop_front().expect("scripted event"));
            if action != FineSegmentationReviewAction::None {
                return Ok(action);
            }
        }
    }
}

#[test]
fn only_distinct_multinote_groups_are_visible_without_changing_saved_evidence() {
    let root = tempfile::tempdir_in("/dev/shm").unwrap();
    let input = root.path().join("review.json");
    let session = root.path().join("session.json");
    let response = root.path().join("response.json");
    let artifact = reviewer(true);
    let original = serde_json::to_vec(&artifact).unwrap();
    fs::write(&input, &original).unwrap();
    let mut ui = EventUi::new([pause()]);
    run_fine_segmentation_review(&input, &session, &response, &mut ui).unwrap();
    let frame = &ui.frames[0];
    assert!(
        frame.contains("S002"),
        "first visible group must be S002:\n{frame}"
    );
    assert!(
        frame.contains("of 2"),
        "only two groups are visible:\n{frame}"
    );
    assert!(
        !frame.contains("S001"),
        "one-note, two-vector group must be hidden"
    );
    assert!(frame.contains("V020") && frame.contains("V021"));
    assert!(
        frame.contains("⟦Alpha⟧ ⟦Omega⟧"),
        "fragments use spaces:\n{frame}"
    );
    assert!(!frame.contains("⟦Alpha⟧; ⟦Omega⟧"));
    assert_eq!(fs::read(&input).unwrap(), original);
    let saved = read_json(&session);
    assert_eq!(saved["session"]["packets"].as_array().unwrap().len(), 5);
    assert_eq!(
        saved["session"]["reviewer_artifact_sha256"],
        format!("{:x}", Sha256::digest(&original))
    );
    for (stored, packet) in saved["session"]["packets"]
        .as_array()
        .unwrap()
        .iter()
        .zip(artifact["packets"].as_array().unwrap())
    {
        assert_eq!(stored["packet"], packet["packet"]);
        assert_eq!(stored["packet_sha256"].as_str().unwrap().len(), 64);
    }
    assert_eq!(read_json(response)["judgments"], json!([]));
}

#[test]
fn browsing_confirmation_and_skip_visit_only_multinote_groups() {
    let root = tempfile::tempdir_in("/dev/shm").unwrap();
    let input = root.path().join("review.json");
    let session = root.path().join("session.json");
    let response = root.path().join("response.json");
    let original = serde_json::to_vec(&reviewer(true)).unwrap();
    fs::write(&input, &original).unwrap();
    let mut ui = EventUi::new([
        key(KeyCode::Left),
        key(KeyCode::Right),
        key(KeyCode::Right),
        key(KeyCode::Left),
        key(KeyCode::Char('v')),
        key(KeyCode::Enter),
        key(KeyCode::Left),
        key(KeyCode::Right),
        key(KeyCode::Char('s')),
        key(KeyCode::Left),
        key(KeyCode::Right),
        pause(),
    ]);
    run_fine_segmentation_review(&input, &session, &response, &mut ui).unwrap();
    let expected = [
        "S002", "S002", "S004", "S004", "S002", "S002", "S004", "S002", "S004", "S004", "S002",
        "S004",
    ];
    assert_eq!(ui.frames.len(), expected.len());
    for (frame, packet) in ui.frames.iter().zip(expected) {
        assert!(frame.contains(packet), "expected {packet}:\n{frame}");
        assert!(frame.contains("of 2"), "visible count changed:\n{frame}");
        for hidden in ["S001", "S003", "S005"] {
            assert!(
                !frame.contains(hidden),
                "navigation exposed {hidden}:\n{frame}"
            );
        }
    }
    let saved = read_json(&session);
    let packets = saved["session"]["packets"].as_array().unwrap();
    assert_eq!(packets.len(), 5);
    for index in [0, 2, 4] {
        assert_eq!(packets[index]["state"]["status"], "pending");
    }
    assert_eq!(
        packets[1]["state"],
        json!({"status":"decided","verdict":"valid"})
    );
    assert_eq!(packets[3]["state"]["status"], "skipped");
    let response = read_json(response);
    assert_eq!(response["judgments"].as_array().unwrap().len(), 1);
    assert_eq!(response["judgments"][0]["packet"], "S002");
    assert_eq!(response["judgments"][0]["verdict"], "valid");
    assert_eq!(fs::read(input).unwrap(), original);
}

#[test]
fn all_same_note_groups_show_empty_without_discarding_original_session_packets() {
    let root = tempfile::tempdir_in("/dev/shm").unwrap();
    let input = root.path().join("review.json");
    let session = root.path().join("session.json");
    let response = root.path().join("response.json");
    let original = serde_json::to_vec(&reviewer(false)).unwrap();
    fs::write(&input, &original).unwrap();
    let mut ui = EventUi::new([pause()]);
    let result = run_fine_segmentation_review(&input, &session, &response, &mut ui).unwrap();
    assert!(ui.frames[0].contains("No segments"), "{}", ui.frames[0]);
    for hidden in ["S001", "S002", "S003", "S004", "S005"] {
        assert!(!ui.frames[0].contains(hidden));
    }
    assert_eq!(
        result,
        FineSegmentationReviewRunOutcome::Completed {
            valid: 0,
            invalid: 0,
            uncertain: 0,
        }
    );
    let saved = read_json(session);
    let packets = saved["session"]["packets"].as_array().unwrap();
    assert_eq!(packets.len(), 5);
    assert!(
        packets
            .iter()
            .all(|packet| packet["state"]["status"] == "pending")
    );
    assert_eq!(read_json(response)["judgments"], json!([]));
    assert_eq!(fs::read(input).unwrap(), original);
}

// These fixture types preserve the historical session's serialized field order
// when constructing a checksum-valid saved cursor/decision for the real loader.
// They are test input data, not alternate review logic or a production API.
#[derive(Deserialize, Serialize)]
struct SavedSession {
    schema_version: u32,
    review_protocol: String,
    review_set: String,
    reviewer_artifact_sha256: String,
    current_packet_index: usize,
    #[serde(default, skip_serializing_if = "is_zero")]
    current_instance_index: usize,
    packets: Vec<SavedPacket>,
}

#[derive(Deserialize, Serialize)]
struct SavedPacket {
    packet: String,
    packet_sha256: String,
    state: FineSegmentationPacketState,
    #[serde(default, skip_serializing_if = "String::is_empty")]
    comment: String,
}

fn is_zero(value: &usize) -> bool {
    *value == 0
}

fn save_historical_session(path: &Path, session: &SavedSession) {
    let digest = format!("{:x}", Sha256::digest(serde_json::to_vec(session).unwrap()));
    fs::write(
        path,
        serde_json::to_vec(&json!({
            "schema_version": 1, "state_sha256": digest, "session": session,
        }))
        .unwrap(),
    )
    .unwrap();
}

#[test]
fn saved_hidden_decisions_and_original_packet_hashes_survive_filtered_resumption() {
    let root = tempfile::tempdir_in("/dev/shm").unwrap();
    let input = root.path().join("review.json");
    let session_path = root.path().join("session.json");
    let response_path = root.path().join("response.json");
    let original = serde_json::to_vec(&reviewer(true)).unwrap();
    fs::write(&input, &original).unwrap();
    run_fine_segmentation_review(
        &input,
        &session_path,
        &response_path,
        &mut EventUi::new([pause()]),
    )
    .unwrap();
    let mut saved: SavedSession =
        serde_json::from_value(read_json(&session_path)["session"].clone()).unwrap();
    saved.packets[0].state = FineSegmentationPacketState::Decided {
        verdict: FineSegmentationReviewVerdict::Valid,
    };
    saved.packets[0].comment = "Previously reviewed one-note group".into();
    saved.packets[2].state = FineSegmentationPacketState::Skipped;
    saved.packets[2].comment = "Previously skipped one-note group".into();
    saved.current_packet_index = 3;
    saved.current_instance_index = 1;
    save_historical_session(&session_path, &saved);
    let prior_packets = read_json(&session_path)["session"]["packets"].clone();
    let prior_response = json!({
        "schema_version": 3, "review_set": "multinote-review",
        "judgments": [{"packet":"S001","verdict":"valid",
            "comment":"Previously reviewed one-note group"}],
    });
    fs::write(&response_path, serde_json::to_vec(&prior_response).unwrap()).unwrap();
    let mut visible_resume = EventUi::new([pause()]);
    run_fine_segmentation_review(&input, &session_path, &response_path, &mut visible_resume)
        .unwrap();
    assert!(visible_resume.frames[0].contains("S004"));
    let resumed = read_json(&session_path);
    assert_eq!(resumed["session"]["current_packet_index"], 3);
    assert_eq!(resumed["session"]["current_instance_index"], 1);
    assert_eq!(resumed["session"]["packets"], prior_packets);
    assert_eq!(read_json(&response_path), prior_response);

    saved.current_packet_index = 0;
    save_historical_session(&session_path, &saved);
    let mut hidden_resume = EventUi::new([pause()]);
    run_fine_segmentation_review(&input, &session_path, &response_path, &mut hidden_resume)
        .unwrap();
    assert!(
        hidden_resume.frames[0].contains("S002"),
        "{}",
        hidden_resume.frames[0]
    );
    assert!(!hidden_resume.frames[0].contains("S001"));
    assert_eq!(
        read_json(&session_path)["session"]["packets"],
        prior_packets
    );
    assert_eq!(read_json(&response_path), prior_response);
    assert_eq!(fs::read(input).unwrap(), original);
}

#[test]
fn combined_mask_list_scrolls_and_tab_does_not_cycle_or_reset_it() {
    let root = tempfile::tempdir_in("/dev/shm").unwrap();
    let input = root.path().join("review.json");
    let mut artifact = reviewer(true);
    let mut packet = artifact["packets"][1].clone();
    let instances = packet["instances"].as_array_mut().unwrap();
    for index in 2..50 {
        let mut instance = instances[index % 2].clone();
        instance["instance"] = json!(format!("V{:03}", 300 + index));
        instance["vector_id"] = json!(format!("{:064x}", 2000 + index));
        instances.push(instance);
    }
    artifact["packets"] = json!([packet]);
    fs::write(&input, serde_json::to_vec(&artifact).unwrap()).unwrap();
    let mut ui = EventUi::new([
        key(KeyCode::PageDown),
        key(KeyCode::Tab),
        key(KeyCode::BackTab),
        key(KeyCode::Home),
        pause(),
    ]);
    run_fine_segmentation_review(
        &input,
        root.path().join("session.json"),
        root.path().join("response.json"),
        &mut ui,
    )
    .unwrap();
    assert!(ui.frames[0].contains("V020"));
    assert!(
        !ui.frames[1].contains("V020"),
        "PageDown must scroll the combined list"
    );
    assert_eq!(
        ui.frames[1], ui.frames[2],
        "Tab must preserve the visible mask list and scroll"
    );
    assert_eq!(ui.frames[2], ui.frames[3], "Shift-Tab must also be a no-op");
    assert!(
        ui.frames[4].contains("V020"),
        "Home returns to the first mask"
    );
    assert!(
        ui.frames
            .iter()
            .all(|frame| !frame.contains("prefix") && !frame.contains("suffix"))
    );
}
