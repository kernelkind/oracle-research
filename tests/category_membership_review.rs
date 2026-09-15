use std::fs;

use oracle_mvp::mask_prompt_review::{run_category_membership_review_from, run_mask_prompt_review};
use oracle_mvp::reference_map::ReviewOutcome;
use oracle_mvp::reference_tui::{ApprovalEvidenceLayout, ApprovalTuiAction, ApprovalTuiModel};
use ratatui::{Terminal, backend::TestBackend};
use serde_json::{Value, json};

fn batch() -> Value {
    json!({"schema_version":1, "batch_id":"membership", "items":[
        {"item_id":"N004", "note_id":"note-a", "subject":"Coffee",
         "note":"At the café: coffee and music.",
         "fragments":[{"text":"café","occurrence":1},{"text":"music","occurrence":1}],
         "assessment":"I am unsure whether the setting justifies Coffee membership.",
         "details":"V034 and V036 exceeded the cutoff; native answers were No."},
        {"item_id":"N005", "note_id":"note-b", "subject":"Coffee",
         "note":"Coffee is ready.", "fragments":[{"text":"Coffee","occurrence":1}],
         "assessment":"This explicitly mentions coffee."}
    ]})
}

#[test]
fn membership_question_full_note_reasoning_and_controls_are_visible() {
    let dir = tempfile::tempdir().unwrap();
    let input = dir.path().join("batch.json");
    let session = dir.path().join("session.json");
    fs::write(&input, serde_json::to_vec(&batch()).unwrap()).unwrap();
    run_category_membership_review_from(&input, &session, None, |screen, comment| {
        assert_eq!(screen.title.as_deref(), Some("Coffee"));
        assert_eq!(
            screen.scope,
            "Does the highlighted evidence justify adding this note to Coffee?"
        );
        assert!(screen.heading.contains("1 of 2 · N004 · Not reviewed"));
        assert!(
            screen
                .guidance
                .as_ref()
                .unwrap()
                .body
                .contains("V034 and V036")
        );
        let ApprovalEvidenceLayout::Paged(panels) = &screen.evidence else {
            panic!()
        };
        assert_eq!(panels.len(), 2);
        assert_eq!(panels[0].body, "At the ⟦café⟧: coffee and ⟦music⟧.");
        assert_eq!(panels[1].title, "My reasoning");
        let mut model = ApprovalTuiModel::new_navigable_stacked_review(screen, comment);
        let mut terminal = Terminal::new(TestBackend::new(72, 24)).unwrap();
        terminal.draw(|frame| model.render(frame)).unwrap();
        let buffer = terminal.backend().buffer();
        let rendered = (0..24)
            .map(|y| (0..72).map(|x| buffer[(x, y)].symbol()).collect::<String>())
            .collect::<Vec<_>>()
            .join("\n");
        for expected in [
            "⟦café⟧",
            "⟦music⟧",
            "My reasoning",
            "I am unsure",
            "[A]",
            "[R]",
            "[C]",
            "[S]",
            "[Ctrl-C]",
        ] {
            assert!(
                rendered.contains(expected),
                "missing {expected}:\n{rendered}"
            );
        }
        Ok(ApprovalTuiAction::Pause)
    })
    .unwrap();
}

#[test]
fn membership_decisions_resume_and_can_be_revisited_without_modifying_inputs() {
    let dir = tempfile::tempdir().unwrap();
    let input = dir.path().join("batch.json");
    let session = dir.path().join("session.json");
    let original = serde_json::to_vec(&batch()).unwrap();
    fs::write(&input, &original).unwrap();
    let mut calls = 0;
    run_category_membership_review_from(&input, &session, None, |screen, comment| {
        calls += 1;
        match calls {
            1 => Ok(ApprovalTuiAction::SaveComment {
                comment: "Tag alone is enough.".into(),
            }),
            2 => {
                assert_eq!(comment, "Tag alone is enough.");
                Ok(ApprovalTuiAction::Submit {
                    outcome: ReviewOutcome::Approved,
                    comment,
                })
            }
            3 => {
                assert!(screen.heading.contains("N005 · Not reviewed"));
                Ok(ApprovalTuiAction::Pause)
            }
            _ => panic!(),
        }
    })
    .unwrap();
    run_category_membership_review_from(&input, &session, None, |screen, _| {
        assert!(screen.heading.contains("N005 · Not reviewed"));
        Ok(ApprovalTuiAction::Skip {
            comment: "Unsure; revisit".into(),
        })
    })
    .unwrap();
    run_category_membership_review_from(&input, &session, Some("N004"), |screen, comment| {
        assert!(screen.heading.contains("N004 · Approved"));
        assert_eq!(comment, "Tag alone is enough.");
        Ok(ApprovalTuiAction::Submit {
            outcome: ReviewOutcome::Rejected,
            comment,
        })
    })
    .unwrap();
    let saved: Value = serde_json::from_slice(&fs::read(&session).unwrap()).unwrap();
    assert_eq!(saved["session"]["decisions"]["N004"]["outcome"], "rejected");
    assert_eq!(saved["session"]["decisions"]["N005"]["outcome"], "skipped");
    assert_eq!(fs::read(&input).unwrap(), original);
    assert!(
        run_mask_prompt_review(&input, &session, |_, _| panic!(
            "different question must not inherit decisions"
        ))
        .is_err()
    );
}

#[test]
fn membership_cli_is_distinct_from_mask_quality_review() {
    let output = std::process::Command::new(env!("CARGO_BIN_EXE_sse-mask-review"))
        .args(["review-membership", "batch.json", "session.json"])
        .stdin(std::process::Stdio::null())
        .output()
        .unwrap();
    assert!(!output.status.success());
    let error = String::from_utf8_lossy(&output.stderr);
    assert!(
        error.contains("category membership review must be started from an interactive terminal"),
        "{error}"
    );
}

#[test]
fn true12_packet_shows_all_six_notes_without_prefilled_decisions() {
    use crossterm::event::{Event, KeyCode, KeyEvent, KeyModifiers};
    let dir = tempfile::tempdir().unwrap();
    let session = dir.path().join("session.json");
    let input = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("sse_multivector/navigation-research-v1/TRUE12/membership-review.json");
    let packet: Value = serde_json::from_slice(&fs::read(&input).unwrap()).unwrap();
    let mut index = 0;
    run_category_membership_review_from(&input, &session, None, |screen, comment| {
        let item = &packet["items"][index];
        assert!(screen.heading.contains(item["item_id"].as_str().unwrap()));
        assert!(screen.heading.contains("Not reviewed"));
        assert_eq!(comment, "");
        let ApprovalEvidenceLayout::Paged(panels) = &screen.evidence else {
            panic!()
        };
        let unmarked = panels[0].body.replace(['⟦', '⟧'], "");
        assert_eq!(unmarked, item["note"].as_str().unwrap());
        let mut model = ApprovalTuiModel::new_navigable_stacked_review(screen, comment);
        for (width, height) in [(72, 24), (100, 32)] {
            let mut terminal = Terminal::new(TestBackend::new(width, height)).unwrap();
            terminal.draw(|frame| model.render(frame)).unwrap();
            let buffer = terminal.backend().buffer();
            let rendered = (0..height)
                .map(|y| {
                    (0..width)
                        .map(|x| buffer[(x, y)].symbol())
                        .collect::<String>()
                })
                .collect::<Vec<_>>()
                .join("\n");
            for expected in [
                item["item_id"].as_str().unwrap(),
                "Coffee",
                "My reasoning",
                "[A]",
                "[R]",
                "[C]",
                "[S]",
                "[Ctrl-C]",
            ] {
                assert!(
                    rendered.contains(expected),
                    "missing {expected}:\n{rendered}"
                );
            }
            if width == 100 && item["item_id"] == "N065" {
                println!("{rendered}");
            }
            // Real reviewer navigation is item navigation, not mask cycling.
            assert_eq!(
                model.handle_event(Event::Key(KeyEvent::new(
                    KeyCode::Right,
                    KeyModifiers::NONE
                ))),
                ApprovalTuiAction::NextItem
            );
            assert_eq!(
                model.handle_event(Event::Key(KeyEvent::new(KeyCode::Left, KeyModifiers::NONE))),
                ApprovalTuiAction::PreviousItem
            );
        }
        index += 1;
        Ok(ApprovalTuiAction::Skip {
            comment: String::new(),
        })
    })
    .unwrap();
    assert_eq!(index, 6);
}
