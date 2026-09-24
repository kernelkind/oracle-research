use std::fs;
use std::path::Path;

use crossterm::event::{Event, KeyCode, KeyEvent, KeyModifiers};
use oracle_mvp::reference_tui::{
    ApprovalEvidenceLayout, ApprovalScreen, ApprovalTuiAction, ApprovalTuiModel,
};
use oracle_mvp::title_prompt_review::{TitlePromptReviewOutcome, run_title_prompt_review};
use ratatui::{Terminal, backend::TestBackend};
use serde_json::{Value, json};

fn batch() -> Value {
    json!({
        "schema_version": 1,
        "batch_id": "title-comparison",
        "candidate_version": "v4",
        "baseline_version": "v3",
        "items": [
            {
                "item_id": "S001",
                "candidate_title": "**Coffee preparation**\n",
                "baseline_title": "Home coffee preparation\n",
                "instances": [
                    {"instance":"V001", "fragments":["café", "beans"]},
                    {"instance":"V002", "fragments":["café", "beans"]},
                    {"instance":"V003", "fragments":["grind coffee beans"]}
                ]
            },
            {
                "item_id": "S002", "candidate_title": "Art", "baseline_title": "Art keywords",
                "instances": [{"instance":"V004", "fragments":["Art"]}]
            },
            {
                "item_id": "S003", "candidate_title": "Family", "baseline_title": "Family life",
                "instances": [{"instance":"V005", "fragments":["Focus on", "family"]}]
            }
        ]
    })
}

fn write(path: &Path, value: &Value) {
    fs::write(path, serde_json::to_vec_pretty(value).unwrap()).unwrap();
}

fn read(path: &Path) -> Value {
    serde_json::from_slice(&fs::read(path).unwrap()).unwrap()
}

fn key(code: KeyCode) -> Event {
    Event::Key(KeyEvent::new(code, KeyModifiers::NONE))
}

fn render(model: &mut ApprovalTuiModel) -> String {
    let mut terminal = Terminal::new(TestBackend::new(72, 24)).unwrap();
    terminal.draw(|frame| model.render(frame)).unwrap();
    let buffer = terminal.backend().buffer();
    (0..24)
        .map(|y| (0..72).map(|x| buffer[(x, y)].symbol()).collect::<String>())
        .collect::<Vec<_>>()
        .join("\n")
}

fn action(screen: ApprovalScreen, comment: String, code: KeyCode) -> ApprovalTuiAction {
    let mut model = ApprovalTuiModel::new_navigable_prompt_iteration(screen, comment);
    render(&mut model);
    model.handle_event(key(code))
}

#[test]
fn candidate_only_question_preserves_all_mask_instances_and_raw_titles() {
    let directory = tempfile::tempdir().unwrap();
    let input = directory.path().join("input.json");
    let session = directory.path().join("session.json");
    write(&input, &batch());
    let original = fs::read(&input).unwrap();
    let outcome = run_title_prompt_review(&input, &session, None, |screen, comment| {
        assert!(screen.heading.contains("S001"));
        assert!(screen.scope.contains("v4"));
        assert!(screen.scope.contains("every instance"));
        assert_eq!(screen.approve_label, "Approve v4 title");
        assert_eq!(screen.reject_label, "Disapprove v4 title");
        let ApprovalEvidenceLayout::Paged(evidence) = &screen.evidence else {
            panic!("all masks must be together in one scrollable panel")
        };
        assert_eq!(evidence.len(), 1);
        assert_eq!(
            evidence[0].body,
            "v4 title under review:\n**Coffee preparation**\n\n\n\
             v3 baseline — context only, not being approved:\nHome coffee preparation\n\n\n\
             Exact member masks:\n\
             V001: ⟦café⟧ ⟦beans⟧\n\
             V002: ⟦café⟧ ⟦beans⟧\n\
             V003: ⟦grind coffee beans⟧"
        );
        assert_eq!(comment, "");
        let mut model = ApprovalTuiModel::new_navigable_prompt_iteration(screen, comment);
        let text = render(&mut model);
        assert!(text.contains("Coffee preparation"), "{text}");
        assert!(text.contains("[C] Comment"), "{text}");
        assert!(text.contains("[S] Skip"), "{text}");
        assert!(text.contains("[←/→] Previous/next item"), "{text}");
        Ok(ApprovalTuiAction::Pause)
    })
    .unwrap();
    assert_eq!(outcome, TitlePromptReviewOutcome::Paused);
    assert_eq!(fs::read(&input).unwrap(), original);
}

#[test]
fn decisions_comments_skips_and_current_card_survive_pause_and_rereview() {
    let directory = tempfile::tempdir().unwrap();
    let input = directory.path().join("input.json");
    let session = directory.path().join("session.json");
    write(&input, &batch());
    let mut calls = 0;
    run_title_prompt_review(&input, &session, None, |screen, comment| {
        calls += 1;
        Ok(match calls {
            1 => {
                let mut model = ApprovalTuiModel::new_navigable_prompt_iteration(screen, comment);
                render(&mut model);
                assert_eq!(
                    model.handle_event(key(KeyCode::Char('c'))),
                    ApprovalTuiAction::None
                );
                model.handle_event(Event::Paste("All three masks fit.".into()));
                model.handle_event(key(KeyCode::Enter))
            }
            2 => {
                assert_eq!(comment, "All three masks fit.");
                action(screen, comment, KeyCode::Char('a'))
            }
            3 => action(screen, "Later".into(), KeyCode::Char('s')),
            4 => ApprovalTuiAction::Pause,
            _ => panic!("unexpected card"),
        })
    })
    .unwrap();
    let stored = read(&session);
    assert_eq!(
        stored["session"]["decisions"]["S001"]["outcome"],
        "approved"
    );
    assert_eq!(
        stored["session"]["decisions"]["S001"]["comment"],
        "All three masks fit."
    );
    assert_eq!(stored["session"]["decisions"]["S002"]["outcome"], "skipped");
    assert_eq!(stored["session"]["current_item"], "S003");
    let completed = run_title_prompt_review(&input, &session, None, |screen, comment| {
        assert!(screen.heading.contains("S003"));
        Ok(action(screen, comment, KeyCode::Char('a')))
    })
    .unwrap();
    assert_eq!(
        completed,
        TitlePromptReviewOutcome::Completed {
            approved: 2,
            rejected: 0,
            skipped: 1
        }
    );
    run_title_prompt_review(&input, &session, None, |_, _| {
        panic!("completed cards recur")
    })
    .unwrap();

    let before = read(&session);
    let mut calls = 0;
    run_title_prompt_review(&input, &session, Some("S001"), |screen, comment| {
        calls += 1;
        Ok(match calls {
            1 => {
                assert!(screen.heading.contains("Approved"));
                assert_eq!(comment, "All three masks fit.");
                action(screen, comment, KeyCode::Right)
            }
            2 => {
                assert!(screen.heading.contains("Skipped"));
                assert_eq!(comment, "Later");
                action(screen, comment, KeyCode::Left)
            }
            3 => action(screen, "Reconsidered.".into(), KeyCode::Char('r')),
            _ => panic!("unexpected rereview"),
        })
    })
    .unwrap();
    let after = read(&session);
    assert_eq!(after["session"]["decisions"]["S001"]["outcome"], "rejected");
    assert_eq!(
        after["session"]["decisions"]["S001"]["comment"],
        "Reconsidered."
    );
    for id in ["S002", "S003"] {
        assert_eq!(
            after["session"]["decisions"][id],
            before["session"]["decisions"][id]
        );
    }
}

#[test]
fn navigation_wraps_and_resumes_the_current_card_without_deciding() {
    let directory = tempfile::tempdir().unwrap();
    let input = directory.path().join("input.json");
    let session = directory.path().join("session.json");
    write(&input, &batch());
    let mut calls = 0;
    run_title_prompt_review(&input, &session, None, |screen, comment| {
        calls += 1;
        Ok(match calls {
            1 => action(screen, comment, KeyCode::Left),
            2 => {
                assert!(screen.heading.contains("S003"));
                action(screen, comment, KeyCode::Right)
            }
            3 => action(screen, comment, KeyCode::Right),
            4 => ApprovalTuiAction::Pause,
            _ => panic!("unexpected card"),
        })
    })
    .unwrap();
    assert_eq!(read(&session)["session"]["current_item"], "S002");
    run_title_prompt_review(&input, &session, None, |screen, _| {
        assert!(screen.heading.contains("S002"));
        Ok(ApprovalTuiAction::Pause)
    })
    .unwrap();
    for id in ["S001", "S002", "S003"] {
        assert!(read(&session)["session"]["decisions"][id]["outcome"].is_null());
    }
}

#[test]
fn same_prompt_comparisons_preserve_candidate_baseline_and_saved_decisions() {
    for assessed in [false, true] {
        let directory = tempfile::tempdir().unwrap();
        let input = directory.path().join("input.json");
        let session = directory.path().join("session.json");
        let mut data = batch();
        data["baseline_version"] = data["candidate_version"].clone();
        data["items"].as_array_mut().unwrap().truncate(1);
        if assessed {
            data["items"][0]["assessment"] = json!("Uncertain: review the scope.");
        }
        write(&input, &data);
        let original = fs::read(&input).unwrap();
        let outcome = run_title_prompt_review(&input, &session, None, |screen, comment| {
            let comparison = if assessed {
                screen.guidance.as_ref().unwrap().body.as_str()
            } else {
                let ApprovalEvidenceLayout::Paged(evidence) = &screen.evidence else {
                    panic!("missing title evidence")
                };
                evidence[0].body.as_str()
            };
            assert!(comparison.contains("v4"));
            assert!(comparison.contains("baseline"));
            assert!(comparison.contains("Coffee preparation"));
            assert!(comparison.contains("Home coffee preparation"));
            Ok(action(screen, comment, KeyCode::Char('a')))
        })
        .unwrap();
        assert_eq!(
            outcome,
            TitlePromptReviewOutcome::Completed {
                approved: 1,
                rejected: 0,
                skipped: 0,
            }
        );
        assert_eq!(
            read(&session)["session"]["decisions"]["S001"]["outcome"],
            "approved"
        );
        run_title_prompt_review(&input, &session, None, |_, _| {
            panic!("completed decision was lost")
        })
        .unwrap();
        assert_eq!(fs::read(&input).unwrap(), original);
    }
}

#[test]
fn invalid_input_or_start_id_fails_without_creating_a_session() {
    let directory = tempfile::tempdir().unwrap();
    let input = directory.path().join("input.json");
    let session = directory.path().join("session.json");
    for (pointer, value) in [
        ("/schema_version", json!(2)),
        ("/batch_id", json!(" ")),
        ("/candidate_version", json!("")),
        ("/baseline_version", json!(" ")),
        ("/items", json!([])),
        ("/items/0/candidate_title", json!("")),
        ("/items/0/baseline_title", json!(" ")),
        ("/items/1/item_id", json!("S001")),
        ("/items/0/instances", json!([])),
        ("/items/0/instances/0/instance", json!("")),
        ("/items/0/instances/1/instance", json!("V001")),
        ("/items/0/instances/0/fragments", json!([])),
        ("/items/0/instances/0/fragments/0", json!("")),
    ] {
        let mut data = batch();
        *data.pointer_mut(pointer).unwrap() = value;
        write(&input, &data);
        assert!(
            run_title_prompt_review(&input, &session, None, |_, _| panic!(
                "invalid input reached UI"
            ))
            .is_err(),
            "{pointer}"
        );
        assert!(!session.exists());
    }
    let mut data = batch();
    data["items"][0]["expected_verdict"] = json!("approve");
    write(&input, &data);
    assert!(run_title_prompt_review(&input, &session, None, |_, _| panic!()).is_err());
    write(&input, &batch());
    let error =
        run_title_prompt_review(&input, &session, Some("unknown"), |_, _| panic!()).unwrap_err();
    assert!(error.to_string().contains("unknown title review item"));
    assert!(!session.exists());
    let original = fs::read(&input).unwrap();
    assert!(run_title_prompt_review(&input, &input, None, |_, _| panic!()).is_err());
    assert_eq!(fs::read(&input).unwrap(), original);
}

#[test]
fn changed_titles_versions_or_masks_cannot_inherit_saved_decisions() {
    let directory = tempfile::tempdir().unwrap();
    let input = directory.path().join("input.json");
    let session = directory.path().join("session.json");
    write(&input, &batch());
    run_title_prompt_review(&input, &session, None, |_, _| Ok(ApprovalTuiAction::Pause)).unwrap();
    let original = fs::read(&session).unwrap();
    for (pointer, value) in [
        ("/candidate_version", json!("v5")),
        ("/items/0/candidate_title", json!("Different title")),
        ("/items/0/baseline_title", json!("Different context")),
        ("/items/0/instances/0/fragments/0", json!("Different mask")),
    ] {
        let mut data = batch();
        *data.pointer_mut(pointer).unwrap() = value;
        write(&input, &data);
        let error = run_title_prompt_review(&input, &session, None, |_, _| {
            panic!("changed input reached UI")
        })
        .unwrap_err();
        assert!(
            error.to_string().contains("different title batch"),
            "{error}"
        );
        assert_eq!(fs::read(&session).unwrap(), original);
    }
}

#[test]
fn long_titles_and_all_masks_remain_accessible_with_existing_scroll_controls() {
    let directory = tempfile::tempdir().unwrap();
    let input = directory.path().join("input.json");
    let session = directory.path().join("session.json");
    let mut data = batch();
    data["items"][0]["candidate_title"] =
        json!(format!("{}CANDIDATE END", "long title words ".repeat(100)));
    data["items"][0]["instances"][2]["fragments"][0] = json!("FINAL MASK café 🧡");
    write(&input, &data);
    run_title_prompt_review(&input, &session, None, |screen, comment| {
        let mut model = ApprovalTuiModel::new_navigable_prompt_iteration(screen, comment);
        let mut screens = render(&mut model);
        for _ in 0..50 {
            assert_eq!(
                model.handle_event(key(KeyCode::Down)),
                ApprovalTuiAction::None
            );
            screens.push_str(&render(&mut model));
        }
        for text in [
            "CANDIDATE END",
            "context only",
            "V001",
            "V002",
            "FINAL MASK",
            "café",
            "🧡",
        ] {
            assert!(screens.contains(text), "missing {text}");
        }
        Ok(ApprovalTuiAction::Pause)
    })
    .unwrap();
}
