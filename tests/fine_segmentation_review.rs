use std::collections::VecDeque;
use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::process::Command;

use crossterm::event::{Event, KeyCode, KeyEvent, KeyModifiers};
use oracle_mvp::fine_segmentation_review::{
    FineSegmentationPacketState, FineSegmentationReviewAction, FineSegmentationReviewRunOutcome,
    FineSegmentationReviewScreen, FineSegmentationReviewTuiModel, FineSegmentationReviewUi,
    FineSegmentationReviewVerdict, run_fine_segmentation_review,
};
use ratatui::Terminal;
use ratatui::backend::TestBackend;
use serde_json::{Value, json};

struct Fixture {
    _root: tempfile::TempDir,
    reviewer_path: PathBuf,
    session_path: PathBuf,
    response_path: PathBuf,
}

impl Fixture {
    fn new() -> Self {
        let root = tempfile::tempdir_in("/dev/shm").expect("temporary directory");
        let reviewer_path = root.path().join("reviewer.json");
        let session_path = root.path().join("session.json");
        let response_path = root.path().join("response.json");
        let packets = (1..=177)
            .map(|ordinal| {
                json!({
                    "packet": format!("P{ordinal:03}"),
                    "question": "Are all instances recognizable as refinements of one fine subject?",
                    "verdicts": ["valid", "invalid", "uncertain"],
                    "instances": [
                        {"instance": "I01", "fragments": [format!("First neutral mask {ordinal}")]},
                        {"instance": "I02", "fragments": [format!("Second neutral mask {ordinal}")]}
                    ]
                })
            })
            .collect::<Vec<_>>();
        write_json(
            &reviewer_path,
            &json!({
                "schema_version": 1,
                "review_set": "R-hdbscan-post-hoc-v1",
                "instructions": {
                    "question": "For each packet, decide whether all instances are recognizable as refinements of one fine subject.",
                    "valid": "Every instance is recognizable as a refinement of one fine subject.",
                    "invalid": "No one recognizable, non-disjunctive fine subject covers every instance.",
                    "uncertain": "The masks do not support a confident valid/invalid decision."
                },
                "packets": packets,
                "response_contract": {
                    "schema_version": 1,
                    "review_set": "R-hdbscan-post-hoc-v1",
                    "judgments": "exactly one judgment for every packet",
                    "judgment_fields": ["packet", "verdict"],
                    "allowed_verdicts": ["valid", "invalid", "uncertain"]
                }
            }),
        );
        Self {
            _root: root,
            reviewer_path,
            session_path,
            response_path,
        }
    }
}

struct ScriptedUi {
    actions: VecDeque<FineSegmentationReviewAction>,
    screens: Vec<FineSegmentationReviewScreen>,
    drain_requests: Vec<bool>,
}

impl ScriptedUi {
    fn new(actions: impl IntoIterator<Item = FineSegmentationReviewAction>) -> Self {
        Self {
            actions: actions.into_iter().collect(),
            screens: Vec::new(),
            drain_requests: Vec::new(),
        }
    }
}

impl FineSegmentationReviewUi for ScriptedUi {
    fn review(
        &mut self,
        model: &mut FineSegmentationReviewTuiModel,
        drain_stale_input: bool,
    ) -> io::Result<FineSegmentationReviewAction> {
        self.screens.push(model.screen().clone());
        self.drain_requests.push(drain_stale_input);
        Ok(self.actions.pop_front().expect("scripted review action"))
    }
}

#[test]
fn every_verdict_requires_confirmation_and_session_has_no_label_or_suggestion_state() {
    let fixture = Fixture::new();
    let mut first = ScriptedUi::new([
        FineSegmentationReviewAction::Select(FineSegmentationReviewVerdict::Valid),
        FineSegmentationReviewAction::Pause,
    ]);

    let outcome = run_fine_segmentation_review(
        &fixture.reviewer_path,
        &fixture.session_path,
        &fixture.response_path,
        &mut first,
    )
    .expect("pause with selected valid verdict");

    assert_eq!(outcome, FineSegmentationReviewRunOutcome::Paused);
    let session = read_session(&fixture.session_path);
    assert_eq!(session["packets"][0]["state"]["status"], "selected");
    assert_eq!(session["packets"][0]["state"]["proposed"], "valid");
    assert!(session["packets"][0]["state"]["prior"].is_null());
    assert_label_free(&session);
    assert!(!fixture.response_path.exists());

    let mut resumed = ScriptedUi::new([
        FineSegmentationReviewAction::Confirm,
        FineSegmentationReviewAction::Select(FineSegmentationReviewVerdict::Invalid),
        FineSegmentationReviewAction::Confirm,
        FineSegmentationReviewAction::Select(FineSegmentationReviewVerdict::Uncertain),
        FineSegmentationReviewAction::Confirm,
        FineSegmentationReviewAction::Pause,
    ]);
    run_fine_segmentation_review(
        &fixture.reviewer_path,
        &fixture.session_path,
        &fixture.response_path,
        &mut resumed,
    )
    .expect("confirm each verdict");

    assert!(matches!(
        resumed.screens[0],
        FineSegmentationReviewScreen::Packet {
            packet_index: 0,
            state: FineSegmentationPacketState::Selected {
                proposed: FineSegmentationReviewVerdict::Valid,
                prior: None,
            },
            ..
        }
    ));
    assert!(matches!(
        resumed.screens[2],
        FineSegmentationReviewScreen::Packet {
            packet_index: 1,
            state: FineSegmentationPacketState::Selected {
                proposed: FineSegmentationReviewVerdict::Invalid,
                prior: None,
            },
            ..
        }
    ));
    assert!(matches!(
        resumed.screens[4],
        FineSegmentationReviewScreen::Packet {
            packet_index: 2,
            state: FineSegmentationPacketState::Selected {
                proposed: FineSegmentationReviewVerdict::Uncertain,
                prior: None,
            },
            ..
        }
    ));
    let session = read_session(&fixture.session_path);
    assert_eq!(session["packets"][0]["state"]["status"], "decided");
    assert_eq!(session["packets"][0]["state"]["verdict"], "valid");
    assert_eq!(session["packets"][1]["state"]["status"], "decided");
    assert_eq!(session["packets"][1]["state"]["verdict"], "invalid");
    assert_eq!(session["packets"][2]["state"]["status"], "decided");
    assert_eq!(session["packets"][2]["state"]["verdict"], "uncertain");
    assert_label_free(&session);
}

#[test]
fn all_packets_complete_without_any_suggestion_input() {
    let fixture = Fixture::new();
    let actions = completed_actions(177, |ordinal| match ordinal % 3 {
        0 => FineSegmentationReviewVerdict::Valid,
        1 => FineSegmentationReviewVerdict::Invalid,
        _ => FineSegmentationReviewVerdict::Uncertain,
    });
    let mut ui = ScriptedUi::new(actions);

    let outcome = run_fine_segmentation_review(
        &fixture.reviewer_path,
        &fixture.session_path,
        &fixture.response_path,
        &mut ui,
    )
    .expect("complete review without suggestions");

    assert_eq!(
        outcome,
        FineSegmentationReviewRunOutcome::Completed {
            valid: 59,
            invalid: 59,
            uncertain: 59,
        }
    );
    let response = read_json(&fixture.response_path);
    let judgments = response["judgments"].as_array().expect("judgments");
    assert_eq!(judgments.len(), 177);
    assert!(judgments.iter().all(|judgment| {
        let fields = judgment.as_object().expect("judgment object");
        fields.len() == 2 && fields.contains_key("packet") && fields.contains_key("verdict")
    }));
    assert_label_free(&read_session(&fixture.session_path));
}

#[test]
fn resume_and_revision_preserve_the_exact_packet_position() {
    let fixture = Fixture::new();
    let mut first = ScriptedUi::new([
        FineSegmentationReviewAction::Select(FineSegmentationReviewVerdict::Invalid),
        FineSegmentationReviewAction::Pause,
    ]);
    run_fine_segmentation_review(
        &fixture.reviewer_path,
        &fixture.session_path,
        &fixture.response_path,
        &mut first,
    )
    .expect("pause with selected invalid verdict");

    let mut resumed = ScriptedUi::new([
        FineSegmentationReviewAction::Confirm,
        FineSegmentationReviewAction::PreviousPacket,
        FineSegmentationReviewAction::Select(FineSegmentationReviewVerdict::Uncertain),
        FineSegmentationReviewAction::Confirm,
        FineSegmentationReviewAction::Pause,
    ]);
    run_fine_segmentation_review(
        &fixture.reviewer_path,
        &fixture.session_path,
        &fixture.response_path,
        &mut resumed,
    )
    .expect("confirm and revise prior packet");

    assert!(matches!(
        resumed.screens[0],
        FineSegmentationReviewScreen::Packet {
            packet_index: 0,
            state: FineSegmentationPacketState::Selected {
                proposed: FineSegmentationReviewVerdict::Invalid,
                prior: None,
            },
            ..
        }
    ));
    assert!(matches!(
        resumed.screens[1],
        FineSegmentationReviewScreen::Packet {
            packet_index: 1,
            ..
        }
    ));
    let session = read_session(&fixture.session_path);
    assert_eq!(session["current_packet_index"], 1);
    assert_eq!(session["packets"][0]["state"]["status"], "decided");
    assert_eq!(session["packets"][0]["state"]["verdict"], "uncertain");
    assert!(!fixture.response_path.exists());
}

#[test]
fn an_unacknowledged_break_is_saved_and_repeated_after_every_twenty_completions() {
    let fixture = Fixture::new();
    let mut actions = completed_actions(20, |_| FineSegmentationReviewVerdict::Invalid);
    actions.push(FineSegmentationReviewAction::Pause);
    let mut first = ScriptedUi::new(actions);

    let outcome = run_fine_segmentation_review(
        &fixture.reviewer_path,
        &fixture.session_path,
        &fixture.response_path,
        &mut first,
    )
    .expect("reach first break");

    assert_eq!(outcome, FineSegmentationReviewRunOutcome::Paused);
    assert!(matches!(
        first.screens.last(),
        Some(FineSegmentationReviewScreen::Break {
            completed_packet_count: 20
        })
    ));
    let session = read_session(&fixture.session_path);
    assert_eq!(session["break_checkpoints"][0]["after_packets"], 20);
    assert_eq!(session["break_checkpoints"][0]["continued"], false);

    let mut resumed = ScriptedUi::new([
        FineSegmentationReviewAction::ContinueBreak,
        FineSegmentationReviewAction::Pause,
    ]);
    run_fine_segmentation_review(
        &fixture.reviewer_path,
        &fixture.session_path,
        &fixture.response_path,
        &mut resumed,
    )
    .expect("continue saved break");
    assert!(matches!(
        resumed.screens[0],
        FineSegmentationReviewScreen::Break {
            completed_packet_count: 20
        }
    ));
    assert!(matches!(
        resumed.screens[1],
        FineSegmentationReviewScreen::Packet {
            packet_index: 20,
            ..
        }
    ));
    assert_eq!(
        read_session(&fixture.session_path)["break_checkpoints"][0]["continued"],
        true
    );
}

#[test]
fn the_complete_response_is_not_published_until_every_packet_is_confirmed() {
    let fixture = Fixture::new();
    let mut actions = completed_actions(176, |_| FineSegmentationReviewVerdict::Invalid);
    actions.push(FineSegmentationReviewAction::Pause);
    let mut first = ScriptedUi::new(actions);
    let outcome = run_fine_segmentation_review(
        &fixture.reviewer_path,
        &fixture.session_path,
        &fixture.response_path,
        &mut first,
    )
    .expect("pause before final packet");
    assert_eq!(outcome, FineSegmentationReviewRunOutcome::Paused);
    assert!(!fixture.response_path.exists());

    let mut resumed = ScriptedUi::new([
        FineSegmentationReviewAction::Select(FineSegmentationReviewVerdict::Valid),
        FineSegmentationReviewAction::Confirm,
    ]);
    let outcome = run_fine_segmentation_review(
        &fixture.reviewer_path,
        &fixture.session_path,
        &fixture.response_path,
        &mut resumed,
    )
    .expect("complete final packet");
    assert_eq!(
        outcome,
        FineSegmentationReviewRunOutcome::Completed {
            valid: 1,
            invalid: 176,
            uncertain: 0,
        }
    );
    let response = read_json(&fixture.response_path);
    assert_eq!(
        response["judgments"].as_array().expect("judgments").len(),
        177
    );
    assert_eq!(
        response["judgments"][176],
        json!({"packet": "P177", "verdict": "valid"})
    );
}

#[test]
fn pending_replacement_retains_the_prior_verdict_and_blocks_publication() {
    let fixture = Fixture::new();
    let mut actions = completed_actions(176, |_| FineSegmentationReviewVerdict::Invalid);
    actions.extend([
        FineSegmentationReviewAction::PreviousPacket,
        FineSegmentationReviewAction::Select(FineSegmentationReviewVerdict::Uncertain),
        FineSegmentationReviewAction::NextPacket,
        FineSegmentationReviewAction::Select(FineSegmentationReviewVerdict::Valid),
        FineSegmentationReviewAction::Confirm,
        FineSegmentationReviewAction::Pause,
    ]);
    let mut first = ScriptedUi::new(actions);

    let outcome = run_fine_segmentation_review(
        &fixture.reviewer_path,
        &fixture.session_path,
        &fixture.response_path,
        &mut first,
    )
    .expect("pause with one pending replacement");

    assert_eq!(outcome, FineSegmentationReviewRunOutcome::Paused);
    assert!(!fixture.response_path.exists());
    let session = read_session(&fixture.session_path);
    assert_eq!(session["current_packet_index"], 175);
    assert_eq!(session["packets"][175]["state"]["status"], "selected");
    assert_eq!(session["packets"][175]["state"]["proposed"], "uncertain");
    assert_eq!(session["packets"][175]["state"]["prior"], "invalid");
    assert!(matches!(
        first.screens.last(),
        Some(FineSegmentationReviewScreen::Packet {
            completed_packet_count: 177,
            ..
        })
    ));
    let mut replacement_model = FineSegmentationReviewTuiModel::new(
        first.screens.last().expect("replacement screen").clone(),
    );
    assert_eq!(
        replacement_model.handle_event(key(KeyCode::Esc)),
        FineSegmentationReviewAction::CancelSelection
    );

    let mut resumed = ScriptedUi::new([FineSegmentationReviewAction::CancelSelection]);
    let outcome = run_fine_segmentation_review(
        &fixture.reviewer_path,
        &fixture.session_path,
        &fixture.response_path,
        &mut resumed,
    )
    .expect("cancel replacement and restore prior verdict");
    assert!(matches!(
        resumed.screens[0],
        FineSegmentationReviewScreen::Packet {
            state: FineSegmentationPacketState::Selected {
                proposed: FineSegmentationReviewVerdict::Uncertain,
                prior: Some(FineSegmentationReviewVerdict::Invalid),
            },
            ..
        }
    ));
    assert_eq!(
        outcome,
        FineSegmentationReviewRunOutcome::Completed {
            valid: 1,
            invalid: 176,
            uncertain: 0,
        }
    );
    assert_eq!(
        read_json(&fixture.response_path)["judgments"][175],
        json!({"packet": "P176", "verdict": "invalid"})
    );
}

#[test]
fn reviewer_artifact_rejects_internal_provenance_fields() {
    let fixture = Fixture::new();
    let mut reviewer = read_json(&fixture.reviewer_path);
    reviewer["packets"][0]["configuration_id"] = json!("must-stay-hidden");
    write_json(&fixture.reviewer_path, &reviewer);
    let mut ui = ScriptedUi::new([]);

    let error = run_fine_segmentation_review(
        &fixture.reviewer_path,
        &fixture.session_path,
        &fixture.response_path,
        &mut ui,
    )
    .expect_err("reviewer input must be strictly neutral");

    assert!(error.to_string().contains("configuration_id"), "{error}");
    assert!(ui.screens.is_empty());
}

#[test]
fn reviewer_artifact_requires_the_exact_label_free_response_contract() {
    let fixture = Fixture::new();
    let mut reviewer = read_json(&fixture.reviewer_path);
    reviewer["response_contract"]["judgment_fields"] = json!(["packet", "verdict", "fine_subject"]);
    write_json(&fixture.reviewer_path, &reviewer);
    let mut ui = ScriptedUi::new([]);

    let error = run_fine_segmentation_review(
        &fixture.reviewer_path,
        &fixture.session_path,
        &fixture.response_path,
        &mut ui,
    )
    .expect_err("reviewer response contract must be label-free and exact");

    assert!(error.to_string().contains("response contract"), "{error}");
    assert!(ui.screens.is_empty());
}

#[test]
fn tui_shows_definitions_and_supports_scrolling_and_two_step_valid_confirmation() {
    let fixture = Fixture::new();
    let mut reviewer = read_json(&fixture.reviewer_path);
    reviewer["packets"][0]["instances"][0]["fragments"][0] = json!(
        (0..50)
            .map(|line| format!("Scrollable neutral mask line {line:02}"))
            .collect::<Vec<_>>()
            .join("\n")
    );
    write_json(&fixture.reviewer_path, &reviewer);
    let mut initial = ScriptedUi::new([FineSegmentationReviewAction::Pause]);
    run_fine_segmentation_review(
        &fixture.reviewer_path,
        &fixture.session_path,
        &fixture.response_path,
        &mut initial,
    )
    .expect("open initial packet");
    let mut model = FineSegmentationReviewTuiModel::new(initial.screens.remove(0));
    let initial_text = render(&mut model, 72, 24);
    assert!(initial_text.contains("Packet 1 of 177"), "{initial_text}");
    assert!(
        initial_text.contains("Valid = one recognizable"),
        "{initial_text}"
    );
    assert!(
        initial_text.contains("non-disjunctive fine subject"),
        "{initial_text}"
    );
    assert!(
        initial_text.contains("covers every instance"),
        "{initial_text}"
    );
    assert!(
        initial_text.contains("Invalid = no such subject"),
        "{initial_text}"
    );
    assert!(
        initial_text.contains("Uncertain = masks do not support a confident decision"),
        "{initial_text}"
    );
    assert!(initial_text.contains("Scrollable neutral mask line 00"));
    assert!(initial_text.contains("[V] Valid"), "{initial_text}");
    assert!(
        initial_text.contains("[Ctrl-C] Save/exit"),
        "{initial_text}"
    );
    assert!(!initial_text.contains("Suggestion"), "{initial_text}");
    assert!(!initial_text.contains("label"), "{initial_text}");
    assert_eq!(
        model.handle_event(key(KeyCode::PageDown)),
        FineSegmentationReviewAction::None
    );
    let scrolled = render(&mut model, 72, 24);
    assert!(!scrolled.contains("Scrollable neutral mask line 00"));
    assert_eq!(
        model.handle_event(key(KeyCode::Char('v'))),
        FineSegmentationReviewAction::Select(FineSegmentationReviewVerdict::Valid)
    );

    let mut select_valid = ScriptedUi::new([
        FineSegmentationReviewAction::Select(FineSegmentationReviewVerdict::Valid),
        FineSegmentationReviewAction::Pause,
    ]);
    run_fine_segmentation_review(
        &fixture.reviewer_path,
        &fixture.session_path,
        &fixture.response_path,
        &mut select_valid,
    )
    .expect("select valid and open confirmation step");
    let mut confirmation_model =
        FineSegmentationReviewTuiModel::new(select_valid.screens.remove(1));
    let confirmation_text = render(&mut confirmation_model, 72, 24);
    assert!(
        confirmation_text.contains("valid selected; press Enter to confirm"),
        "{confirmation_text}"
    );
    assert!(
        confirmation_text.contains("[Enter] Confirm selection"),
        "{confirmation_text}"
    );
    assert!(
        !confirmation_text.contains("Suggestion"),
        "{confirmation_text}"
    );
    assert!(!confirmation_text.contains("label"), "{confirmation_text}");
    assert_eq!(
        confirmation_model.handle_event(key(KeyCode::Enter)),
        FineSegmentationReviewAction::Confirm
    );
}

#[test]
fn cli_reports_the_three_required_review_paths() {
    let output = Command::new(env!("CARGO_BIN_EXE_fine-segmentation-review"))
        .output()
        .expect("run review CLI");
    assert!(!output.status.success());
    let stderr = String::from_utf8(output.stderr).expect("UTF-8 stderr");
    assert!(
        stderr.contains("usage: fine-segmentation-review REVIEWER.json SESSION.json RESPONSE.json"),
        "{stderr}"
    );
}

fn completed_actions(
    count: usize,
    verdict: impl Fn(usize) -> FineSegmentationReviewVerdict,
) -> Vec<FineSegmentationReviewAction> {
    let mut actions = Vec::new();
    for ordinal in 0..count {
        actions.push(FineSegmentationReviewAction::Select(verdict(ordinal)));
        actions.push(FineSegmentationReviewAction::Confirm);
        if (ordinal + 1).is_multiple_of(20) && ordinal + 1 < count {
            actions.push(FineSegmentationReviewAction::ContinueBreak);
        }
    }
    actions
}

fn key(code: KeyCode) -> Event {
    Event::Key(KeyEvent::new(code, KeyModifiers::NONE))
}

fn render(model: &mut FineSegmentationReviewTuiModel, width: u16, height: u16) -> String {
    let backend = TestBackend::new(width, height);
    let mut terminal = Terminal::new(backend).expect("test terminal");
    terminal
        .draw(|frame| model.render(frame))
        .expect("render review screen");
    terminal
        .backend()
        .buffer()
        .content()
        .iter()
        .map(|cell| cell.symbol())
        .collect::<String>()
}

fn assert_label_free(value: &Value) {
    let serialized = serde_json::to_string(value).expect("serialize JSON");
    for forbidden in ["suggestion", "label", "fine_subject"] {
        assert!(
            !serialized.contains(forbidden),
            "found {forbidden}: {serialized}"
        );
    }
}

fn read_session(path: &Path) -> Value {
    read_json(path)["session"].clone()
}

fn read_json(path: &Path) -> Value {
    serde_json::from_slice(&fs::read(path).expect("read JSON")).expect("decode JSON")
}

fn write_json(path: &Path, value: &Value) {
    fs::write(path, serde_json::to_vec_pretty(value).expect("encode JSON")).expect("write JSON");
}
