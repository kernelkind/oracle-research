use std::fs;

use oracle_mvp::mask_prompt_review::{MaskPromptReviewOutcome, run_mask_prompt_review};
use oracle_mvp::reference_map::ReviewOutcome;
use oracle_mvp::reference_tui::{ApprovalEvidenceLayout, ApprovalTuiAction, ApprovalTuiModel};
use ratatui::{Terminal, backend::TestBackend};
use serde_json::{Value, json};

fn batch() -> Value {
    json!({
        "schema_version": 1,
        "batch_id": "mask-probe",
        "items": [
            {"item_id":"M01", "note_id":"n1", "subject":"Café reading",
             "note":"At the café, I read; the café was quiet.",
             "fragments":[{"text":"café","occurrence":1},{"text":"I read","occurrence":1}]},
            {"item_id":"M02", "note_id":"n1", "subject":"A quiet café",
             "note":"At the café, I read; the café was quiet.",
             "fragments":[{"text":"café was quiet","occurrence":1}]},
            {"item_id":"M03", "note_id":"n2", "subject":"Birdsong",
             "note":"A bird sang.", "fragments":[{"text":"bird sang","occurrence":1}]}
        ]
    })
}

fn write(path: &std::path::Path, value: &Value) {
    fs::write(path, serde_json::to_vec_pretty(value).unwrap()).unwrap();
}

#[test]
fn mask_only_review_preserves_comments_decisions_and_pause_without_subject_questions() {
    let dir = tempfile::tempdir().unwrap();
    let input = dir.path().join("input.json");
    let session = dir.path().join("session.json");
    write(&input, &batch());
    let mut calls = 0;
    let outcome = run_mask_prompt_review(&input, &session, |screen, comment| {
        calls += 1;
        match calls {
            1 => {
                assert_eq!(screen.title.as_deref(), Some("Café reading"));
                assert!(screen.scope.contains("mask"));
                let ApprovalEvidenceLayout::Paged(evidence) = &screen.evidence else {
                    panic!()
                };
                assert_eq!(evidence.len(), 1);
                assert_eq!(evidence[0].title, "Note");
                assert_eq!(
                    evidence[0].body,
                    "At the ⟦café⟧, ⟦I read⟧; the café was quiet."
                );
                assert_eq!(comment, "");
                Ok(ApprovalTuiAction::SaveComment {
                    comment: "Keep this question.".into(),
                })
            }
            2 => {
                assert_eq!(comment, "Keep this question.");
                Ok(ApprovalTuiAction::Submit {
                    outcome: ReviewOutcome::Rejected,
                    comment,
                })
            }
            3 => {
                assert_eq!(screen.title.as_deref(), Some("A quiet café"));
                Ok(ApprovalTuiAction::Skip {
                    comment: "Later".into(),
                })
            }
            4 => {
                assert_eq!(screen.title.as_deref(), Some("Birdsong"));
                Ok(ApprovalTuiAction::Pause)
            }
            _ => panic!("unexpected extra review"),
        }
    })
    .unwrap();
    assert_eq!(outcome, MaskPromptReviewOutcome::Paused);
    assert_eq!(calls, 4);
    let stored: Value = serde_json::from_slice(&fs::read(&session).unwrap()).unwrap();
    assert_eq!(stored["session"]["decisions"]["M01"]["outcome"], "rejected");
    assert_eq!(
        stored["session"]["decisions"]["M01"]["comment"],
        "Keep this question."
    );
    assert_eq!(stored["session"]["decisions"]["M02"]["outcome"], "skipped");
    assert!(stored["session"]["decisions"]["M03"]["outcome"].is_null());
    let outcome = run_mask_prompt_review(&input, &session, |screen, _| {
        assert_eq!(screen.title.as_deref(), Some("Birdsong"));
        Ok(ApprovalTuiAction::Submit {
            outcome: ReviewOutcome::Approved,
            comment: String::new(),
        })
    })
    .unwrap();
    assert_eq!(
        outcome,
        MaskPromptReviewOutcome::Completed {
            approved: 1,
            rejected: 1,
            skipped: 1
        }
    );
    run_mask_prompt_review(&input, &session, |_, _| {
        panic!("completed decisions must not recur")
    })
    .unwrap();
}

#[test]
fn changed_input_cannot_inherit_review_decisions() {
    let dir = tempfile::tempdir().unwrap();
    let input = dir.path().join("input.json");
    let session = dir.path().join("session.json");
    let mut data = batch();
    write(&input, &data);
    run_mask_prompt_review(&input, &session, |_, _| Ok(ApprovalTuiAction::Pause)).unwrap();
    let original_session = fs::read(&session).unwrap();
    data["items"][0]["subject"] = json!("Different subject");
    write(&input, &data);
    let error =
        run_mask_prompt_review(&input, &session, |_, _| panic!("must reject changed input"))
            .unwrap_err()
            .to_string();
    assert!(error.contains("different mask batch"), "{error}");
    assert_eq!(fs::read(&session).unwrap(), original_session);
}

#[test]
fn invalid_fragments_and_duplicate_ids_fail_before_review() {
    let dir = tempfile::tempdir().unwrap();
    let input = dir.path().join("input.json");
    let session = dir.path().join("session.json");
    let invalid = [
        json!([]),
        json!([{"text":"absent","occurrence":1}]),
        json!([{"text":"café","occurrence":0}]),
        json!([{"text":"I read","occurrence":1},{"text":"café","occurrence":1}]),
        json!([{"text":"At the café","occurrence":1},{"text":"café","occurrence":1}]),
    ];
    for fragments in invalid {
        let mut data = batch();
        data["items"][0]["fragments"] = fragments;
        write(&input, &data);
        assert!(
            run_mask_prompt_review(&input, &session, |_, _| panic!("invalid mask reached UI"))
                .is_err()
        );
        assert!(!session.exists());
    }
    let mut data = batch();
    data["items"][1]["item_id"] = json!("M01");
    write(&input, &data);
    assert!(
        run_mask_prompt_review(&input, &session, |_, _| panic!("duplicate ID reached UI")).is_err()
    );
    assert!(!session.exists());
}

#[test]
fn subject_wraps_above_full_note_and_review_controls_are_optional() {
    let dir = tempfile::tempdir().unwrap();
    let input = dir.path().join("input.json");
    let session = dir.path().join("session.json");
    let mut data = batch();
    data["items"][0]["subject"] = json!(
        "Reading a book at a quiet café while keeping enough context to identify the activity and location — SUBJECT END"
    );
    write(&input, &data);
    run_mask_prompt_review(&input, &session, |screen, comment| {
        let mut model = ApprovalTuiModel::new_prompt_iteration(screen, comment);
        let mut terminal = Terminal::new(TestBackend::new(100, 32)).unwrap();
        terminal.draw(|frame| model.render(frame)).unwrap();
        let buffer = terminal.backend().buffer();
        let rendered = (0..32)
            .map(|y| {
                (0..100)
                    .map(|x| buffer[(x, y)].symbol())
                    .collect::<String>()
            })
            .collect::<Vec<_>>()
            .join("\n");
        assert!(rendered.contains("SUBJECT END"), "{rendered}");
        assert!(rendered.contains("⟦café⟧"), "{rendered}");
        assert!(rendered.contains("[C] Comment"), "{rendered}");
        assert!(rendered.contains("[S] Skip"), "{rendered}");
        assert!(rendered.find("SUBJECT END").unwrap() < rendered.find("┌Note").unwrap());
        Ok(ApprovalTuiAction::Pause)
    })
    .unwrap();
}

#[test]
fn mask_review_shows_reasoning_below_the_complete_note_without_prefilling_a_decision() {
    let dir = tempfile::tempdir().unwrap();
    let input = dir.path().join("input.json");
    let session = dir.path().join("session.json");
    let mut data = batch();
    let assessment = "The mask includes both the reading activity and its location.";
    data["items"][0]["assessment"] = json!(assessment);
    write(&input, &data);
    let original = fs::read(&input).unwrap();

    run_mask_prompt_review(&input, &session, |screen, comment| {
        assert_eq!(screen.title.as_deref(), Some("Café reading"));
        assert!(screen.heading.contains("Not reviewed"));
        assert!(comment.is_empty());
        let ApprovalEvidenceLayout::Paged(panels) = &screen.evidence else {
            panic!("expected the complete note and separate reasoning")
        };
        assert_eq!(panels.len(), 2, "the saved assessment must be visible");
        assert_eq!(
            panels[0].body,
            "At the ⟦café⟧, ⟦I read⟧; the café was quiet."
        );
        assert_eq!(panels[1].title, "My reasoning");
        assert_eq!(panels[1].body, assessment);

        for (width, height) in [(72, 24), (100, 32), (120, 40)] {
            let mut model =
                ApprovalTuiModel::new_navigable_stacked_review(screen.clone(), comment.clone());
            let mut terminal = Terminal::new(TestBackend::new(width, height)).unwrap();
            terminal.draw(|frame| model.render(frame)).unwrap();
            let buffer = terminal.backend().buffer();
            let lines = (0..height)
                .map(|y| {
                    (0..width)
                        .map(|x| buffer[(x, y)].symbol())
                        .collect::<String>()
                })
                .collect::<Vec<_>>();
            let rendered = lines.join("\n");
            for expected in [
                "Café reading",
                "⟦café⟧",
                "⟦I read⟧",
                "My reasoning",
                assessment,
                "[A]",
                "[R]",
                "[C]",
                "[S]",
                "[←/→]",
                "[Tab/Shift-Tab]",
                "[Ctrl-C]",
            ] {
                assert!(
                    rendered.contains(expected),
                    "missing {expected}:\n{rendered}"
                );
            }
            let note_row = lines
                .iter()
                .position(|line| line.contains("⟦café⟧"))
                .unwrap();
            let reasoning_row = lines
                .iter()
                .position(|line| line.contains("My reasoning"))
                .unwrap();
            assert!(note_row < reasoning_row, "{rendered}");
        }
        Ok(ApprovalTuiAction::Pause)
    })
    .unwrap();

    assert_eq!(fs::read(&input).unwrap(), original);
    let saved: Value = serde_json::from_slice(&fs::read(&session).unwrap()).unwrap();
    assert!(
        saved["session"]["decisions"]
            .as_object()
            .unwrap()
            .values()
            .all(|decision| { decision["outcome"].is_null() && decision["comment"] == "" })
    );
}

#[test]
fn complete_note_and_reasoning_scroll_independently_in_mask_review() {
    use crossterm::event::{Event, KeyCode, KeyEvent, KeyModifiers};

    let dir = tempfile::tempdir().unwrap();
    let input = dir.path().join("input.json");
    let session = dir.path().join("session.json");
    let note = (0..40)
        .map(|n| format!("Note line {n:02}."))
        .collect::<Vec<_>>()
        .join("\n");
    let assessment = (0..40)
        .map(|n| format!("Reasoning line {n:02}."))
        .collect::<Vec<_>>()
        .join("\n");
    write(
        &input,
        &json!({
            "schema_version": 1, "batch_id": "long-mask-review", "items": [{
                "item_id": "M01", "note_id": "note1", "subject": "Long note",
                "note": note, "assessment": assessment,
                "fragments": [{"text": "Note line 00.", "occurrence": 1}]
            }]
        }),
    );

    run_mask_prompt_review(&input, &session, |screen, comment| {
        let mut model = ApprovalTuiModel::new_navigable_stacked_review(screen, comment);
        let mut terminal = Terminal::new(TestBackend::new(72, 24)).unwrap();
        let render = |terminal: &mut Terminal<TestBackend>, model: &mut ApprovalTuiModel| {
            terminal.draw(|frame| model.render(frame)).unwrap();
            let buffer = terminal.backend().buffer();
            (0..24)
                .map(|y| (0..72).map(|x| buffer[(x, y)].symbol()).collect::<String>())
                .collect::<Vec<_>>()
                .join("\n")
        };
        let press = |model: &mut ApprovalTuiModel, code| {
            model.handle_event(Event::Key(KeyEvent::new(code, KeyModifiers::NONE)))
        };
        let first = render(&mut terminal, &mut model);
        assert!(first.contains("⟦Note line 00.⟧"), "{first}");
        assert!(first.contains("Reasoning line 00."), "{first}");

        let mut seen = String::new();
        for _ in 0..45 {
            let rendered = render(&mut terminal, &mut model);
            assert!(rendered.contains("Reasoning line 00."), "{rendered}");
            seen.push_str(&rendered);
            assert_eq!(
                press(&mut model, KeyCode::Char('j')),
                ApprovalTuiAction::None
            );
        }
        for line in 0..40 {
            assert!(seen.contains(&format!("Note line {line:02}.")));
        }
        press(&mut model, KeyCode::Tab);
        seen.clear();
        for _ in 0..45 {
            let rendered = render(&mut terminal, &mut model);
            assert!(rendered.contains("Note line 39."), "{rendered}");
            seen.push_str(&rendered);
            assert_eq!(press(&mut model, KeyCode::Down), ApprovalTuiAction::None);
        }
        for line in 0..40 {
            assert!(seen.contains(&format!("Reasoning line {line:02}.")));
        }
        press(&mut model, KeyCode::BackTab);
        let last = render(&mut terminal, &mut model);
        assert!(last.contains("Note line 39."), "{last}");
        assert!(last.contains("Reasoning line 39."), "{last}");
        press(&mut model, KeyCode::Home);
        let reset_note = render(&mut terminal, &mut model);
        assert!(reset_note.contains("⟦Note line 00.⟧"), "{reset_note}");
        assert!(reset_note.contains("Reasoning line 39."), "{reset_note}");

        assert_eq!(
            press(&mut model, KeyCode::Right),
            ApprovalTuiAction::NextItem
        );
        assert_eq!(
            press(&mut model, KeyCode::Left),
            ApprovalTuiAction::PreviousItem
        );
        Ok(ApprovalTuiAction::Pause)
    })
    .unwrap();
}
