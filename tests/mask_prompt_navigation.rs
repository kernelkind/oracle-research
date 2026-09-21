use std::fs;

use crossterm::event::{Event, KeyCode, KeyEvent, KeyModifiers};
use oracle_mvp::mask_prompt_review::{
    MaskPromptReviewOutcome, run_mask_prompt_review, run_mask_prompt_review_from,
};
use oracle_mvp::reference_map::ReviewOutcome;
use oracle_mvp::reference_tui::{ApprovalScreen, ApprovalTuiAction, ApprovalTuiModel};
use ratatui::{Terminal, backend::TestBackend};
use serde_json::{Value, json};

fn write_batch(path: &std::path::Path, count: usize) {
    let items = (1..=count)
        .map(|index| {
            json!({
                "item_id": format!("M{index:02}"),
                "note_id": format!("note-{index}"),
                "subject": format!("Subject {index}"),
                "note": format!("Full source note {index}."),
                "fragments": [{"text": format!("source note {index}"), "occurrence": 1}]
            })
        })
        .collect::<Vec<_>>();
    fs::write(
        path,
        serde_json::to_vec(&json!({
            "schema_version": 1, "batch_id": "navigation", "items": items
        }))
        .unwrap(),
    )
    .unwrap();
}

fn key(code: KeyCode) -> Event {
    Event::Key(KeyEvent::new(code, KeyModifiers::NONE))
}

fn render(model: &mut ApprovalTuiModel) -> String {
    let mut terminal = Terminal::new(TestBackend::new(72, 24)).unwrap();
    terminal.draw(|frame| model.render(frame)).unwrap();
    terminal
        .backend()
        .buffer()
        .content()
        .iter()
        .map(|cell| cell.symbol())
        .collect()
}

fn navigate(screen: ApprovalScreen, comment: String, code: KeyCode) -> ApprovalTuiAction {
    let mut model = ApprovalTuiModel::new_navigable_stacked_review(screen, comment);
    render(&mut model);
    model.handle_event(key(code))
}

#[test]
fn arrow_keys_reach_m08_and_go_back_without_recording_decisions() {
    let dir = tempfile::tempdir().unwrap();
    let input = dir.path().join("input.json");
    let session = dir.path().join("session.json");
    write_batch(&input, 12);
    let mut original = Vec::new();
    let mut calls = 0;
    let outcome = run_mask_prompt_review(&input, &session, |screen, comment| {
        calls += 1;
        if calls == 1 {
            original = fs::read(&session).unwrap();
        }
        let expected = if calls <= 8 { calls } else { 7 };
        assert_eq!(
            screen.title.as_deref(),
            Some(format!("Subject {expected}").as_str())
        );
        assert!(screen.heading.contains(&format!("M{expected:02}")));
        assert_eq!(comment, "");
        Ok(match calls {
            1..=7 => navigate(screen, comment, KeyCode::Right),
            8 => navigate(screen, comment, KeyCode::Left),
            9 => ApprovalTuiAction::Pause,
            _ => panic!("unexpected extra screen"),
        })
    })
    .unwrap();
    assert_eq!(outcome, MaskPromptReviewOutcome::Paused);
    assert_eq!(calls, 9);
    assert_eq!(fs::read(&session).unwrap(), original);
}

#[test]
fn completed_decisions_can_be_revisited_and_only_explicit_edits_change_them() {
    let dir = tempfile::tempdir().unwrap();
    let input = dir.path().join("input.json");
    let session = dir.path().join("session.json");
    write_batch(&input, 3);
    let mut decisions = [
        ApprovalTuiAction::Submit {
            outcome: ReviewOutcome::Approved,
            comment: "keep approval".into(),
        },
        ApprovalTuiAction::Submit {
            outcome: ReviewOutcome::Rejected,
            comment: "old concern".into(),
        },
        ApprovalTuiAction::Skip {
            comment: "keep skip".into(),
        },
    ]
    .into_iter();
    run_mask_prompt_review(&input, &session, |_, _| Ok(decisions.next().unwrap())).unwrap();
    let before = fs::read(&session).unwrap();
    let mut calls = 0;
    let outcome = run_mask_prompt_review_from(&input, &session, Some("M02"), |screen, comment| {
        calls += 1;
        assert_eq!(
            fs::read(&session).unwrap(),
            before,
            "navigation must not modify the session"
        );
        Ok(match calls {
            1 => {
                assert_eq!(screen.title.as_deref(), Some("Subject 2"));
                assert!(screen.heading.contains("Disapproved"));
                assert_eq!(comment, "old concern");
                navigate(screen, comment, KeyCode::Right)
            }
            2 => {
                assert_eq!(screen.title.as_deref(), Some("Subject 3"));
                assert!(screen.heading.contains("Skipped"));
                assert_eq!(comment, "keep skip");
                navigate(screen, comment, KeyCode::Right)
            }
            3 => {
                assert_eq!(screen.title.as_deref(), Some("Subject 1"));
                assert!(screen.heading.contains("Approved"));
                assert_eq!(comment, "keep approval");
                navigate(screen, comment, KeyCode::Left)
            }
            4 => {
                assert_eq!(screen.title.as_deref(), Some("Subject 3"));
                navigate(screen, comment, KeyCode::Left)
            }
            5 => ApprovalTuiAction::Pause,
            _ => panic!("unexpected extra screen"),
        })
    })
    .unwrap();
    assert_eq!(outcome, MaskPromptReviewOutcome::Paused);
    assert_eq!(fs::read(&session).unwrap(), before);

    let mut calls = 0;
    let outcome = run_mask_prompt_review_from(&input, &session, Some("M02"), |screen, comment| {
        calls += 1;
        assert_eq!(screen.title.as_deref(), Some("Subject 2"));
        Ok(match calls {
            1 => ApprovalTuiAction::SaveComment {
                comment: "reconsidered".into(),
            },
            2 => {
                assert_eq!(comment, "reconsidered");
                navigate(screen, comment, KeyCode::Char('a'))
            }
            _ => panic!("unexpected extra screen"),
        })
    })
    .unwrap();
    assert_eq!(
        outcome,
        MaskPromptReviewOutcome::Completed {
            approved: 2,
            rejected: 0,
            skipped: 1
        }
    );
    let old: Value = serde_json::from_slice(&before).unwrap();
    let new: Value = serde_json::from_slice(&fs::read(&session).unwrap()).unwrap();
    for id in ["M01", "M03"] {
        assert_eq!(
            new["session"]["decisions"][id],
            old["session"]["decisions"][id]
        );
    }
    assert_eq!(new["session"]["decisions"]["M02"]["outcome"], "approved");
    assert_eq!(
        new["session"]["decisions"]["M02"]["comment"],
        "reconsidered"
    );
}

#[test]
fn unknown_start_item_is_rejected_before_creating_a_session() {
    let dir = tempfile::tempdir().unwrap();
    let input = dir.path().join("input.json");
    let session = dir.path().join("session.json");
    write_batch(&input, 3);
    let error = run_mask_prompt_review_from(&input, &session, Some("M08"), |_, _| {
        panic!("invalid item must not reach the UI")
    })
    .unwrap_err()
    .to_string();
    assert!(error.contains("unknown mask review item M08"), "{error}");
    assert!(!session.exists());
}

#[test]
fn item_navigation_is_separate_from_note_scroll_help_and_comment_editing() {
    let dir = tempfile::tempdir().unwrap();
    let input = dir.path().join("input.json");
    let session = dir.path().join("session.json");
    write_batch(&input, 1);
    run_mask_prompt_review(&input, &session, |mut screen, comment| {
        let oracle_mvp::reference_tui::ApprovalEvidenceLayout::Paged(items) = &mut screen.evidence
        else {
            panic!()
        };
        items[0].body = (1..=50)
            .map(|n| format!("note line {n:02}"))
            .collect::<Vec<_>>()
            .join("\n");
        let mut model = ApprovalTuiModel::new_navigable_stacked_review(screen.clone(), comment);
        let initial = render(&mut model);
        assert!(initial.contains("[←/→] Previous/next item"), "{initial}");
        assert!(initial.contains("note line 01"), "{initial}");
        assert_eq!(
            model.handle_event(key(KeyCode::Down)),
            ApprovalTuiAction::None
        );
        assert!(!render(&mut model).contains("note line 01"));
        assert_eq!(
            model.handle_event(key(KeyCode::Left)),
            ApprovalTuiAction::PreviousItem
        );
        assert_eq!(
            model.handle_event(key(KeyCode::Right)),
            ApprovalTuiAction::NextItem
        );

        model.handle_event(key(KeyCode::Char('?')));
        assert_eq!(
            model.handle_event(key(KeyCode::Right)),
            ApprovalTuiAction::None
        );
        model.handle_event(key(KeyCode::Esc));
        model.handle_event(key(KeyCode::Char('c')));
        assert_eq!(
            model.handle_event(key(KeyCode::Right)),
            ApprovalTuiAction::None
        );
        model.handle_event(Event::Paste("still editing".into()));
        assert_eq!(
            model.handle_event(key(KeyCode::Enter)),
            ApprovalTuiAction::SaveComment {
                comment: "still editing".into()
            }
        );

        let mut plain = ApprovalTuiModel::new_prompt_iteration(screen, String::new());
        assert_eq!(
            plain.handle_event(key(KeyCode::Right)),
            ApprovalTuiAction::None
        );
        assert!(!render(&mut plain).contains("Previous/next item"));
        Ok(ApprovalTuiAction::Pause)
    })
    .unwrap();
}
