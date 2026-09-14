use std::fs;

use crossterm::event::{Event, KeyCode, KeyEvent, KeyModifiers};
use oracle_mvp::containment_review::{
    ContainmentDecisionReviewOutcome, run_containment_decision_review,
};
use oracle_mvp::reference_tui::{
    ApprovalEvidenceLayout, ApprovalScreen, ApprovalTuiAction, ApprovalTuiModel,
};
use ratatui::{Terminal, backend::TestBackend};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};

fn packet() -> Value {
    json!({
        "schema_version": 1,
        "experiment": "TRUE04",
        "threshold": 0.142,
        "items": [{
            "item_id": "U001",
            "a": "Coffee",
            "b": "Coffee preparation",
            "assessment": "Ambiguous",
            "reason": "Preparation may be a narrower subject than coffee.",
            "decisions": [{
                "id": "S001-contains-S002",
                "a_id": "S001",
                "b_id": "S002",
                "native": false,
                "score": 0.2468012345,
                "cutoff": true,
                "model_input": "premise: This text is about Coffee preparation. hypothesis: This text is about Coffee."
            }]
        }]
    })
}

#[test]
fn session_cli_accepts_either_flag_order_but_non_tty_creates_no_session() {
    let directory = tempfile::tempdir().unwrap();
    let input = directory.path().join("pairs.json");
    let session = directory.path().join("session.json");
    let original = serde_json::to_vec(&packet()).unwrap();
    fs::write(&input, &original).unwrap();
    for flags in [
        vec!["--session", session.to_str().unwrap(), "--start-at", "U001"],
        vec!["--start-at", "U001", "--session", session.to_str().unwrap()],
    ] {
        let output = std::process::Command::new(env!("CARGO_BIN_EXE_true-review"))
            .arg(&input)
            .args(flags)
            .output()
            .unwrap();
        assert!(!output.status.success());
        let error = String::from_utf8_lossy(&output.stderr);
        assert!(error.contains("interactive terminal"), "{error}");
        assert!(output.stdout.is_empty());
        assert!(!output.stderr.contains(&0x1b));
        assert!(!session.exists());
        assert_eq!(fs::read(&input).unwrap(), original);
        assert_eq!(fs::read_dir(directory.path()).unwrap().count(), 1);
    }
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

fn three_cards() -> Value {
    let mut data = packet();
    for number in 2..=3 {
        let mut item = data["items"][0].clone();
        item["item_id"] = json!(format!("U{number:03}"));
        item["decisions"][0]["a_id"] = json!(format!("S{number:03}"));
        item["decisions"][0]["id"] = json!(format!("S{number:03}-contains-S002"));
        data["items"].as_array_mut().unwrap().push(item);
    }
    data
}

fn write(path: &std::path::Path, data: &Value) {
    fs::write(path, serde_json::to_vec(data).unwrap()).unwrap();
}

fn stored(path: &std::path::Path) -> Value {
    serde_json::from_slice(&fs::read(path).unwrap()).unwrap()
}

fn screen(data: &Value) -> ApprovalScreen {
    let directory = tempfile::tempdir().unwrap();
    let input = directory.path().join("pairs.json");
    write(&input, data);
    let mut result = None;
    run_containment_decision_review(
        &input,
        directory.path().join("session.json"),
        None,
        |screen, _| {
            result = Some(screen);
            Ok(ApprovalTuiAction::Pause)
        },
    )
    .unwrap();
    result.unwrap()
}

#[test]
fn yes_no_skip_and_optional_comment_persist_without_changing_packet() {
    let directory = tempfile::tempdir().unwrap();
    let input = directory.path().join("pairs.json");
    let session = directory.path().join("session.json");
    write(&input, &three_cards());
    let original = fs::read(&input).unwrap();
    let mut permissions = fs::metadata(&input).unwrap().permissions();
    permissions.set_readonly(true);
    fs::set_permissions(&input, permissions).unwrap();
    let mut calls = 0;
    let outcome = run_containment_decision_review(&input, &session, None, |screen, comment| {
        calls += 1;
        let mut model = ApprovalTuiModel::new_navigable_prompt_iteration(screen, comment);
        render(&mut model);
        Ok(match calls {
            1 => {
                model.handle_event(key(KeyCode::Char('c')));
                model.handle_event(Event::Paste("My optional containment comment".into()));
                model.handle_event(key(KeyCode::Enter))
            }
            2 => {
                assert!(render(&mut model).contains("Comment: My optional containment comment"));
                model.handle_event(key(KeyCode::Char('A')))
            }
            3 => model.handle_event(key(KeyCode::Char('R'))),
            4 => model.handle_event(key(KeyCode::Char('S'))),
            _ => panic!("unexpected extra review"),
        })
    })
    .unwrap();
    assert_eq!(
        outcome,
        ContainmentDecisionReviewOutcome::Completed {
            yes: 1,
            no: 1,
            skipped: 1
        }
    );
    assert_eq!(calls, 4);
    let state = stored(&session);
    assert_eq!(state["session"]["decisions"]["U001"]["outcome"], "yes");
    assert_eq!(
        state["session"]["decisions"]["U001"]["comment"],
        "My optional containment comment"
    );
    assert_eq!(state["session"]["decisions"]["U002"]["outcome"], "no");
    assert_eq!(state["session"]["decisions"]["U002"]["comment"], "");
    assert_eq!(state["session"]["decisions"]["U003"]["outcome"], "skipped");
    assert!(state["session"]["current_item"].is_null());
    run_containment_decision_review(&input, &session, None, |_, _| {
        panic!("completed session reopened")
    })
    .unwrap();
    assert_eq!(stored(&session), state);
    assert_eq!(fs::read(input).unwrap(), original);
}

#[test]
fn navigation_autosaves_reviewed_cursor_pause_resumes_and_start_at_reopens_completed() {
    let directory = tempfile::tempdir().unwrap();
    let input = directory.path().join("pairs.json");
    let session = directory.path().join("session.json");
    write(&input, &three_cards());
    let mut calls = 0;
    let outcome = run_containment_decision_review(&input, &session, None, |screen, comment| {
        calls += 1;
        let expected = match calls {
            1 | 3 | 4 => "U001",
            2 => "U002",
            _ => panic!(),
        };
        assert!(screen.heading.contains(expected));
        assert_eq!(stored(&session)["session"]["current_item"], expected);
        if calls >= 3 {
            assert!(screen.heading.contains("Yes (contains)"));
        }
        let mut model = ApprovalTuiModel::new_navigable_prompt_iteration(screen, comment);
        render(&mut model);
        Ok(match calls {
            1 => model.handle_event(key(KeyCode::Char('a'))),
            2 => model.handle_event(key(KeyCode::Left)),
            3 => {
                model.handle_event(key(KeyCode::Char('c')));
                model.handle_event(Event::Paste("saved while revisiting".into()));
                model.handle_event(key(KeyCode::Enter))
            }
            4 => model.handle_event(Event::Key(KeyEvent::new(
                KeyCode::Char('c'),
                KeyModifiers::CONTROL,
            ))),
            _ => panic!(),
        })
    })
    .unwrap();
    assert_eq!(outcome, ContainmentDecisionReviewOutcome::Paused);
    assert_eq!(calls, 4);
    let mut calls = 0;
    run_containment_decision_review(&input, &session, None, |screen, comment| {
        calls += 1;
        let expected = match calls {
            1 | 3 => "U001",
            2 | 5 => "U003",
            4 => "U002",
            _ => panic!(),
        };
        assert!(screen.heading.contains(expected));
        assert_eq!(stored(&session)["session"]["current_item"], expected);
        if calls == 1 {
            assert_eq!(comment, "saved while revisiting");
        }
        Ok(match calls {
            1 => ApprovalTuiAction::PreviousItem,
            2 | 3 => ApprovalTuiAction::NextItem,
            4 | 5 => ApprovalTuiAction::Skip { comment },
            _ => panic!(),
        })
    })
    .unwrap();
    assert_eq!(calls, 5);
    let mut calls = 0;
    run_containment_decision_review(&input, &session, Some("U001"), |screen, comment| {
        calls += 1;
        assert!(screen.heading.contains("U001"));
        assert!(screen.heading.contains("Yes (contains)"));
        let mut model = ApprovalTuiModel::new_navigable_prompt_iteration(screen, comment);
        render(&mut model);
        Ok(model.handle_event(key(KeyCode::Char('r'))))
    })
    .unwrap();
    assert_eq!(calls, 1);
    assert_eq!(
        stored(&session)["session"]["decisions"]["U001"]["outcome"],
        "no"
    );
}

#[test]
fn categories_and_my_comment_are_visible_without_native_answer_at_72_by_24() {
    let data = packet();
    let screen = screen(&data);
    assert_eq!(screen.scope, "Does category A contain category B?");
    assert!(screen.title.is_none());
    assert_eq!(screen.approve_label, "Yes (contains)");
    assert_eq!(screen.reject_label, "No (does not contain)");
    let ApprovalEvidenceLayout::Stacked { top, bottom } = &screen.evidence else {
        panic!("expected stacked categories/comment")
    };
    assert_eq!(top.title, "Categories");
    assert_eq!(
        top.body,
        "A (proposed parent): Coffee\n\nB (proposed child): Coffee preparation"
    );
    assert_eq!(bottom.title, "My comment");
    assert_eq!(bottom.body, data["items"][0]["reason"].as_str().unwrap());
    let mut model = ApprovalTuiModel::new_navigable_prompt_iteration(screen, String::new());
    let initial = render(&mut model);
    for expected in [
        "U001",
        "1 of 1",
        "Not reviewed",
        "Does category A contain category B?",
        "Categories",
        "A (proposed parent): Coffee",
        "B (proposed child): Coffee preparation",
        "My comment",
        "Preparation may be a narrower subject than coffee.",
        "[A] Yes (contains)",
        "[R] No (does not contain)",
        "[C] Comment",
        "[S] Skip",
        "[←/→]",
        "[Tab/Shift-Tab]",
        "[?]",
        "[Ctrl-C]",
    ] {
        assert!(initial.contains(expected), "missing {expected}:\n{initial}");
    }
    for excluded in [
        "Native:",
        "Cutoff:",
        "Score:",
        "0.2468012345",
        "S001-contains-S002",
        "My assessment:",
    ] {
        assert!(!initial.contains(excluded), "{initial}");
    }
    model.handle_event(key(KeyCode::Char('?')));
    let mut details = render(&mut model);
    assert_eq!(
        model.handle_event(key(KeyCode::Char('a'))),
        ApprovalTuiAction::None
    );
    for _ in 0..80 {
        model.handle_event(key(KeyCode::Char('j')));
        let rendered = render(&mut model);
        details.push_str(&rendered);
        details.push_str(
            &rendered
                .lines()
                .filter_map(|line| line.strip_prefix('│')?.strip_suffix('│'))
                .map(str::trim)
                .collect::<Vec<_>>()
                .join(" "),
        );
    }
    for expected in [
        "containment",
        "not whether",
        "Exact model input:",
        "premise: This text is about Coffee preparation.",
        "hypothesis: This text is about Coffee.",
        "S001-contains-S002",
        "A source: S001",
        "B source: S002",
        "Native: No",
        "Cutoff: Yes",
        "0.2468012345",
    ] {
        assert!(details.contains(expected), "missing {expected}:\n{details}");
    }
    model.handle_event(key(KeyCode::Esc));
    assert_eq!(render(&mut model), initial);
}

#[test]
fn exact_long_categories_and_comment_scroll_in_independent_existing_panels() {
    let mut data = packet();
    let item = &mut data["items"][0];
    item["a"] = json!(format!("{}PARENT-END", "complete parent text ".repeat(90)));
    item["b"] = json!(format!("{}CHILD-END", "complete child text ".repeat(90)));
    item["reason"] = json!(format!(
        "{}REASON-END",
        "complete assistant reason ".repeat(90)
    ));
    item["decisions"][0]["model_input"] = json!(format!(
        "premise: This text is about {}. hypothesis: This text is about {}.",
        item["b"].as_str().unwrap(),
        item["a"].as_str().unwrap()
    ));
    let screen = screen(&data);
    let item = &data["items"][0];
    let ApprovalEvidenceLayout::Stacked { top, bottom } = &screen.evidence else {
        panic!()
    };
    assert!(top.body.contains(item["a"].as_str().unwrap()));
    assert!(top.body.contains(item["b"].as_str().unwrap()));
    assert_eq!(bottom.body, item["reason"].as_str().unwrap());
    let mut model = ApprovalTuiModel::new_navigable_prompt_iteration(screen, String::new());
    let initial = render(&mut model);
    assert!(initial.contains("more below"));
    model.handle_event(key(KeyCode::Char('j')));
    assert_ne!(render(&mut model), initial);
    model.handle_event(key(KeyCode::Char('k')));
    assert_eq!(render(&mut model), initial);
    let mut all = initial;
    for _ in 0..180 {
        model.handle_event(key(KeyCode::Char('j')));
        all.push_str(&render(&mut model));
    }
    assert!(all.contains("PARENT-END"));
    assert!(all.contains("CHILD-END"));
    assert!(!all.contains("REASON-END"));
    model.handle_event(key(KeyCode::Tab));
    for _ in 0..150 {
        model.handle_event(key(KeyCode::Char('j')));
        all.push_str(&render(&mut model));
    }
    assert!(all.contains("REASON-END"));
    let bottom = render(&mut model);
    assert!(bottom.contains("[A] Yes (contains)"));
    assert!(bottom.contains("[Ctrl-C]"));
}

// Recompute the hash using the production session's explicit field order so
// membership/cursor validation is tested independently of envelope corruption.
fn reseal(state: &mut Value) {
    let session = &state["session"];
    let decisions = session["decisions"]
        .as_object()
        .unwrap()
        .iter()
        .map(|(id, decision)| {
            format!(
                "{}:{{\"outcome\":{},\"comment\":{}}}",
                serde_json::to_string(id).unwrap(),
                decision["outcome"],
                decision["comment"]
            )
        })
        .collect::<Vec<_>>()
        .join(",");
    let serialized = format!(
        "{{\"schema_version\":{},\"batch_sha256\":{},\"current_item\":{},\"decisions\":{{{decisions}}}}}",
        session["schema_version"], session["batch_sha256"], session["current_item"]
    );
    state["state_sha256"] = json!(format!("{:x}", Sha256::digest(serialized.as_bytes())));
}

#[test]
fn corruption_changed_batch_membership_and_cursor_fail_before_review_or_mutation() {
    let directory = tempfile::tempdir().unwrap();
    let input = directory.path().join("pairs.json");
    let session = directory.path().join("session.json");
    write(&input, &packet());
    run_containment_decision_review(&input, &session, None, |_, _| Ok(ApprovalTuiAction::Pause))
        .unwrap();
    let original = stored(&session);
    let mut cases = Vec::new();
    let mut corrupt = original.clone();
    corrupt["session"]["decisions"]["U001"]["comment"] = json!("corrupted");
    cases.push((corrupt, "state hash"));
    for (pointer, value, expected) in [
        (
            "/session/batch_sha256",
            json!("different"),
            "different containment batch",
        ),
        (
            "/session/decisions",
            json!({}),
            "different containment batch",
        ),
        (
            "/session/current_item",
            json!("unknown"),
            "invalid current item",
        ),
        ("/session/current_item", Value::Null, "invalid current item"),
    ] {
        let mut state = original.clone();
        *state.pointer_mut(pointer).unwrap() = value;
        reseal(&mut state);
        cases.push((state, expected));
    }
    for (state, expected) in cases {
        write(&session, &state);
        let bytes = fs::read(&session).unwrap();
        let error = run_containment_decision_review(&input, &session, None, |_, _| {
            panic!("invalid session reached UI")
        })
        .unwrap_err();
        assert!(error.to_string().contains(expected), "{error}");
        assert_eq!(fs::read(&session).unwrap(), bytes);
    }
    write(&session, &original);
    let before = fs::read(&session).unwrap();
    let mut changed = packet();
    changed["items"][0]["reason"] = json!("A changed reason is a different packet.");
    write(&input, &changed);
    let error = run_containment_decision_review(&input, &session, None, |_, _| {
        panic!("different batch reached UI")
    })
    .unwrap_err();
    assert!(error.to_string().contains("different containment batch"));
    assert_eq!(fs::read(&session).unwrap(), before);
}

#[test]
fn invalid_packet_unknown_start_same_file_and_active_session_are_rejected() {
    let directory = tempfile::tempdir().unwrap();
    let input = directory.path().join("pairs.json");
    let session = directory.path().join("session.json");
    let mut invalid = packet();
    invalid["items"][0]["decisions"][0]["cutoff"] = json!(false);
    write(&input, &invalid);
    let error =
        run_containment_decision_review(&input, &session, None, |_, _| panic!()).unwrap_err();
    assert!(error.to_string().contains("cutoff"));
    assert!(!session.exists());
    write(&input, &packet());
    let original = fs::read(&input).unwrap();
    let error = run_containment_decision_review(&input, &session, Some("missing"), |_, _| panic!())
        .unwrap_err();
    assert!(error.to_string().contains("unknown containment card"));
    assert!(!session.exists());
    let alias = directory.path().join("alias.json");
    fs::hard_link(&input, &alias).unwrap();
    for path in [&input, &alias] {
        let error =
            run_containment_decision_review(&input, path, None, |_, _| panic!()).unwrap_err();
        assert!(error.to_string().contains("different files"), "{error}");
        assert_eq!(fs::read(&input).unwrap(), original);
    }
    run_containment_decision_review(&input, &session, None, |_, _| {
        let before = fs::read(&session).unwrap();
        let error = run_containment_decision_review(&input, &session, None, |_, _| {
            panic!("concurrent review entered UI")
        })
        .unwrap_err();
        assert!(error.to_string().contains("already active"));
        assert_eq!(fs::read(&session).unwrap(), before);
        Ok(ApprovalTuiAction::Pause)
    })
    .unwrap();
}

#[test]
fn default_cli_stays_read_only_and_validation_precedes_non_tty_guard() {
    let directory = tempfile::tempdir().unwrap();
    let input = directory.path().join("pairs.json");
    let session = directory.path().join("session.json");
    write(&input, &packet());
    let help = std::process::Command::new(env!("CARGO_BIN_EXE_true-review"))
        .arg("--help")
        .output()
        .unwrap();
    assert!(help.status.success());
    let help = String::from_utf8_lossy(&help.stdout);
    assert!(help.contains("Read-only"));
    assert!(help.contains("--session"));
    let output = std::process::Command::new(env!("CARGO_BIN_EXE_true-review"))
        .arg(&input)
        .output()
        .unwrap();
    assert!(String::from_utf8_lossy(&output.stderr).contains("interactive terminal"));
    assert_eq!(fs::read_dir(directory.path()).unwrap().count(), 1);
    for (data, start, expected) in [
        (packet(), "missing", "unknown containment card"),
        (
            {
                let mut data = packet();
                data["items"][0]["decisions"][0]["model_input"] = json!("wrong direction");
                data
            },
            "U001",
            "exact model input",
        ),
    ] {
        write(&input, &data);
        let output = std::process::Command::new(env!("CARGO_BIN_EXE_true-review"))
            .arg(&input)
            .arg("--session")
            .arg(&session)
            .args(["--start-at", start])
            .output()
            .unwrap();
        assert!(!output.status.success());
        assert!(String::from_utf8_lossy(&output.stderr).contains(expected));
        assert!(!output.stderr.contains(&0x1b));
        assert!(output.stdout.is_empty());
        assert!(!session.exists());
        assert_eq!(fs::read_dir(directory.path()).unwrap().count(), 1);
    }
}

#[test]
fn actual_uncertainty_packet_has_65_undecided_directional_cards_and_unchanged_evidence() {
    let input = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join(
        "sse_multivector/navigation-research-v1/TRUE04/collection-review/uncertainty-review.json",
    );
    let original = fs::read(&input).unwrap();
    let data: Value = serde_json::from_slice(&original).unwrap();
    let cards = data["items"].as_array().unwrap();
    assert_eq!(cards.len(), 65);
    let directory = tempfile::tempdir().unwrap();
    let session = directory.path().join("session.json");
    let mut index = 0;
    run_containment_decision_review(&input, &session, None, |screen, comment| {
        let item = &cards[index];
        assert_eq!(item["item_id"], format!("U{:03}", index + 1));
        assert!(screen.heading.contains(item["item_id"].as_str().unwrap()));
        assert!(screen.heading.contains("Not reviewed"));
        assert!(comment.is_empty());
        let ApprovalEvidenceLayout::Stacked { top, bottom } = &screen.evidence else {
            panic!()
        };
        assert_eq!(
            top.body,
            format!(
                "A (proposed parent): {}\n\nB (proposed child): {}",
                item["a"].as_str().unwrap(),
                item["b"].as_str().unwrap()
            )
        );
        assert_eq!(bottom.body, item["reason"].as_str().unwrap());
        let mut model = ApprovalTuiModel::new_navigable_prompt_iteration(screen, comment);
        let rendered = render(&mut model);
        for expected in [
            "Categories",
            "My comment",
            "[A] Yes (contains)",
            "[R] No (does not contain)",
            "[S] Skip",
        ] {
            assert!(
                rendered.contains(expected),
                "missing {expected}:\n{rendered}"
            );
        }
        assert!(!rendered.contains("Native:"));
        index += 1;
        Ok(if index == cards.len() {
            ApprovalTuiAction::Pause
        } else {
            model.handle_event(key(KeyCode::Right))
        })
    })
    .unwrap();
    assert_eq!(index, 65);
    let state = stored(&session);
    assert_eq!(state["session"]["current_item"], "U065");
    assert!(
        state["session"]["decisions"]
            .as_object()
            .unwrap()
            .values()
            .all(|record| record["outcome"].is_null())
    );
    assert_eq!(fs::read(input).unwrap(), original);
}
