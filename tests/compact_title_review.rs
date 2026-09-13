use std::fs;

use crossterm::event::{Event, KeyCode, KeyEvent, KeyModifiers};
use oracle_mvp::reference_map::ReviewOutcome;
use oracle_mvp::reference_tui::{
    ApprovalEvidenceLayout, ApprovalScreen, ApprovalTuiAction, ApprovalTuiModel,
};
use oracle_mvp::title_prompt_review::run_title_prompt_review;
use ratatui::{Terminal, backend::TestBackend};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use unicode_width::UnicodeWidthStr;

fn key(code: KeyCode) -> Event {
    Event::Key(KeyEvent::new(code, KeyModifiers::NONE))
}

fn render(model: &mut ApprovalTuiModel) -> String {
    render_at(model, 72, 24)
}

fn render_at(model: &mut ApprovalTuiModel, width: u16, height: u16) -> String {
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
                // Wide characters occupy continuation cells, not extra spaces.
                x += UnicodeWidthStr::width(symbol).max(1) as u16;
            }
            line
        })
        .collect::<Vec<_>>()
        .join("\n")
}

#[test]
fn short_masks_keep_the_assessment_nearby_on_a_tall_terminal() {
    let mut model = ApprovalTuiModel::new_title_review(screen(&batch()), String::new());
    let rendered = render_at(&mut model, 80, 40);
    let lines: Vec<_> = rendered.lines().collect();
    let final_mask = lines
        .iter()
        .position(|line| line.contains("V003:"))
        .unwrap();
    let assessment = lines
        .iter()
        .position(|line| line.contains("My assessment:"))
        .unwrap();
    assert!(assessment <= final_mask + 3, "{rendered}");
}

fn screen(data: &Value) -> ApprovalScreen {
    let directory = tempfile::tempdir().unwrap();
    let input = directory.path().join("input.json");
    fs::write(&input, serde_json::to_vec(data).unwrap()).unwrap();
    let mut result = None;
    run_title_prompt_review(
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

fn batch() -> Value {
    json!({
        "schema_version": 1,
        "batch_id": "uncertain-titles",
        "candidate_version": "v4",
        "baseline_version": "v3",
        "items": [{
            "item_id": "S001",
            "candidate_title": "**Coffee preparation**\n",
            "baseline_title": "BASELINE brewing coffee\n",
            "assessment": "Unsure: the masks may not all describe preparation.",
            "instances": [
                {"instance": "V001", "fragments": ["I grind beans.", "Then brew coffee."]},
                {"instance": "V002", "fragments": ["Coffee tastes good. café 🧡"]},
                {"instance": "V003", "fragments": ["Coffee tastes good. café 🧡"]}
            ]
        }]
    })
}

#[test]
fn assessed_batch_shows_the_raw_title_spaced_masks_and_separate_assessment() {
    let directory = tempfile::tempdir().unwrap();
    let input = directory.path().join("input.json");
    let session = directory.path().join("session.json");
    fs::write(&input, serde_json::to_vec(&batch()).unwrap()).unwrap();
    run_title_prompt_review(&input, &session, None, |screen, comment| {
        assert_eq!(screen.heading, "1 of 1 · S001 · v4 · Not reviewed");
        assert_eq!(screen.title.as_deref(), Some("**Coffee preparation**\n"));
        assert_eq!(screen.scope, "Does this title fit every mask?");
        assert!(comment.is_empty());
        let ApprovalEvidenceLayout::Paged(panels) = &screen.evidence else {
            panic!("expected one mask panel");
        };
        assert_eq!(panels.len(), 1);
        assert_eq!(panels[0].body, "V001: ⟦I grind beans.⟧ ⟦Then brew coffee.⟧\n\nV002: ⟦Coffee tastes good. café 🧡⟧\n\nV003: ⟦Coffee tastes good. café 🧡⟧");
        assert_eq!(panels[0].annotation, "My assessment: Unsure: the masks may not all describe preparation.");
        let comparison = &screen.guidance.as_ref().unwrap().body;
        assert!(comparison.contains("**Coffee preparation**\n"));
        assert!(comparison.contains("BASELINE brewing coffee\n"));
        Ok(ApprovalTuiAction::Pause)
    }).unwrap();
    let stored: Value = serde_json::from_slice(&fs::read(session).unwrap()).unwrap();
    assert!(stored["session"]["decisions"]["S001"]["outcome"].is_null());
}

#[test]
fn compact_render_keeps_title_masks_assessment_and_controls_visible_at_72_by_24() {
    let mut model = ApprovalTuiModel::new_title_review(screen(&batch()), String::new());
    let initial = render(&mut model);
    for expected in [
        "1 of 1 · S001 · v4 · Not reviewed",
        "**Coffee preparation**",
        "Does this title fit every mask?",
        "V001: ⟦I grind beans.⟧ ⟦Then brew coffee.⟧",
        "V002: ⟦Coffee tastes good. café 🧡⟧",
        "V003: ⟦Coffee tastes good. café 🧡⟧",
        "My assessment: Unsure:",
        "[A] Approve",
        "[R] Reject",
        "[C] Comment",
        "[S] Skip",
        "[B] Compare",
        "[Ctrl-C] Save/exit",
    ] {
        assert!(initial.contains(expected), "missing {expected}:\n{initial}");
    }
    assert!(!initial.contains("BASELINE"), "{initial}");
    let lines: Vec<_> = initial.lines().collect();
    let first_mask = lines
        .iter()
        .position(|line| line.contains("V001:"))
        .unwrap();
    let second_mask = lines
        .iter()
        .position(|line| line.contains("V002:"))
        .unwrap();
    assert_eq!(second_mask, first_mask + 2, "{initial}");
    assert!(!lines[first_mask + 1].contains('⟦'));
    assert_eq!(
        model.handle_event(key(KeyCode::Char('b'))),
        ApprovalTuiAction::None
    );
    let comparison = render(&mut model);
    assert!(
        comparison.contains("BASELINE brewing coffee"),
        "{comparison}"
    );
    assert!(!comparison.contains("[A] Approve"));
    assert_eq!(
        model.handle_event(key(KeyCode::Char('a'))),
        ApprovalTuiAction::None
    );
    model.handle_event(key(KeyCode::Char('B')));
    assert_eq!(render(&mut model), initial);
    model.handle_event(key(KeyCode::Char('b')));
    model.handle_event(key(KeyCode::Esc));
    assert_eq!(render(&mut model), initial);
}

#[test]
fn complete_masks_scroll_with_a_pinned_title_and_long_text_has_explicit_access() {
    let mut data = batch();
    data["items"][0]["candidate_title"] = json!(format!(
        "PINNED TITLE {}CANDIDATE END",
        "long title words ".repeat(100)
    ));
    data["items"][0]["baseline_title"] = json!(format!(
        "{}BASELINE END",
        "long baseline words ".repeat(100)
    ));
    data["items"][0]["assessment"] = json!(format!(
        "{}ASSESSMENT END",
        "uncertain opinion ".repeat(100)
    ));
    data["items"][0]["instances"] = json!((1..=30).map(|id| json!({"instance": format!("V{id:03}"), "fragments": [format!("Exact mask {id:03}: café 🧡"), format!("Separate fragment {id:03}")]})).collect::<Vec<_>>());
    let mut model = ApprovalTuiModel::new_title_review(screen(&data), String::new());
    let initial = render(&mut model);
    assert!(initial.contains("… [B] Full title"), "{initial}");
    assert!(initial.contains("… [B] Full assessment"), "{initial}");
    let mut all_masks = initial;
    for _ in 0..100 {
        model.handle_event(key(KeyCode::Down));
        let rendered = render(&mut model);
        assert!(rendered.contains("PINNED TITLE"), "{rendered}");
        assert!(rendered.contains("My assessment:"), "{rendered}");
        all_masks.push_str(&rendered);
    }
    for id in 1..=30 {
        assert!(all_masks.contains(&format!(
            "V{id:03}: ⟦Exact mask {id:03}: café 🧡⟧ ⟦Separate fragment {id:03}⟧"
        )));
    }
    assert!(!all_masks.contains("BASELINE END"));
    let before_compare = render(&mut model);
    model.handle_event(key(KeyCode::Char('b')));
    let mut comparison = render(&mut model);
    for _ in 0..200 {
        model.handle_event(key(KeyCode::Down));
        comparison.push_str(&render(&mut model));
    }
    for expected in ["CANDIDATE END", "BASELINE END", "ASSESSMENT END"] {
        assert!(comparison.contains(expected), "missing {expected}");
    }
    model.handle_event(key(KeyCode::Esc));
    assert_eq!(render(&mut model), before_compare);
}

#[test]
fn comparison_does_not_intercept_comment_text_or_change_the_users_decision() {
    let mut model = ApprovalTuiModel::new_title_review(screen(&batch()), "saved ".into());
    render(&mut model);
    model.handle_event(key(KeyCode::Char('c')));
    model.handle_event(key(KeyCode::Char('b')));
    model.handle_event(key(KeyCode::Char('B')));
    assert!(render(&mut model).contains("> saved bB"));
    assert_eq!(
        model.handle_event(key(KeyCode::Enter)),
        ApprovalTuiAction::SaveComment {
            comment: "saved bB".into()
        }
    );
    model.handle_event(key(KeyCode::Char('b')));
    model.handle_event(key(KeyCode::Esc));
    assert_eq!(
        model.handle_event(key(KeyCode::Char('r'))),
        ApprovalTuiAction::Submit {
            outcome: ReviewOutcome::Rejected,
            comment: "saved bB".into()
        }
    );
    assert_eq!(
        model.handle_event(key(KeyCode::Char('s'))),
        ApprovalTuiAction::Skip {
            comment: "saved bB".into()
        }
    );
    assert_eq!(
        model.handle_event(key(KeyCode::Left)),
        ApprovalTuiAction::PreviousItem
    );
    assert_eq!(
        model.handle_event(key(KeyCode::Right)),
        ApprovalTuiAction::NextItem
    );
    assert_eq!(
        model.handle_event(Event::Key(KeyEvent::new(
            KeyCode::Char('c'),
            KeyModifiers::CONTROL
        ))),
        ApprovalTuiAction::Pause
    );
}

#[test]
fn changed_assessment_cannot_inherit_decisions_and_blank_assessment_is_invalid() {
    let directory = tempfile::tempdir().unwrap();
    let input = directory.path().join("input.json");
    let session = directory.path().join("session.json");
    let mut data = batch();
    fs::write(&input, serde_json::to_vec(&data).unwrap()).unwrap();
    run_title_prompt_review(&input, &session, None, |screen, comment| {
        let mut model = ApprovalTuiModel::new_title_review(screen, comment);
        render(&mut model);
        Ok(model.handle_event(key(KeyCode::Char('a'))))
    })
    .unwrap();
    let before = fs::read(&session).unwrap();
    data["items"][0]["assessment"] = json!("Now I think reject.");
    fs::write(&input, serde_json::to_vec(&data).unwrap()).unwrap();
    let error = run_title_prompt_review(&input, &session, None, |_, _| {
        panic!("changed assessment reached UI")
    })
    .unwrap_err();
    assert!(error.to_string().contains("different title batch"));
    assert_eq!(before, fs::read(&session).unwrap());
    data["items"][0]["assessment"] = json!(" \n ");
    fs::write(&input, serde_json::to_vec(&data).unwrap()).unwrap();
    assert!(
        run_title_prompt_review(
            &input,
            directory.path().join("invalid.json"),
            None,
            |_, _| panic!("empty assessment reached UI")
        )
        .is_err()
    );
    assert!(!directory.path().join("invalid.json").exists());
}

#[test]
fn legacy_batch_serialization_and_saved_sessions_are_unchanged() {
    // Exact field order of the pre-assessment production batch serialization.
    let legacy = r#"{"schema_version":1,"batch_id":"legacy","candidate_version":"v4","baseline_version":"v3","items":[{"item_id":"S001","candidate_title":"Coffee","baseline_title":"Brewing coffee","instances":[{"instance":"V001","fragments":["coffee"]}]}]}"#;
    let directory = tempfile::tempdir().unwrap();
    let input = directory.path().join("legacy.json");
    let session = directory.path().join("session.json");
    fs::write(&input, legacy).unwrap();
    let mut calls = 0;
    run_title_prompt_review(&input, &session, None, |screen, _| {
        assert!(screen.title.is_none());
        calls += 1;
        Ok(if calls == 1 {
            ApprovalTuiAction::SaveComment {
                comment: "Existing comment".into(),
            }
        } else {
            ApprovalTuiAction::Pause
        })
    })
    .unwrap();
    let before = fs::read(&session).unwrap();
    let stored: Value = serde_json::from_slice(&before).unwrap();
    assert_eq!(
        stored["session"]["batch_sha256"],
        format!("{:x}", Sha256::digest(legacy.as_bytes()))
    );
    run_title_prompt_review(&input, &session, None, |screen, comment| {
        assert!(screen.title.is_none());
        assert!(screen.heading.contains("Not reviewed"));
        assert_eq!(comment, "Existing comment");
        let mut model = ApprovalTuiModel::new_navigable_prompt_iteration(screen, comment);
        let initial = render(&mut model);
        assert!(initial.contains("Brewing coffee"));
        model.handle_event(key(KeyCode::Char('b')));
        assert_eq!(render(&mut model), initial);
        Ok(ApprovalTuiAction::Pause)
    })
    .unwrap();
    assert_eq!(before, fs::read(session).unwrap());
}

#[test]
fn uncertain_artifact_is_one_undecided_card_with_original_titles_and_complete_masks() {
    let root = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("sse_multivector/hdbv2-node-description-probe-v4");
    let uncertain: Value =
        serde_json::from_slice(&fs::read(root.join("review-uncertain.json")).unwrap()).unwrap();
    let original: Value =
        serde_json::from_slice(&fs::read(root.join("review.json")).unwrap()).unwrap();
    let cards = uncertain["items"].as_array().unwrap();
    assert_eq!(cards.len(), 1);
    assert_eq!(cards[0]["item_id"], "Sfd8645f195");
    let source = original["items"]
        .as_array()
        .unwrap()
        .iter()
        .find(|item| item["item_id"] == cards[0]["item_id"])
        .unwrap();
    for field in ["candidate_title", "baseline_title", "instances"] {
        assert_eq!(cards[0][field], source[field]);
    }
    let screen = screen(&uncertain);
    assert!(screen.heading.contains("Not reviewed"));
    let mut model = ApprovalTuiModel::new_title_review(screen, String::new());
    let rendered = render(&mut model);
    assert!(
        rendered.contains("1 of 1 · Sfd8645f195 · v4 · Not reviewed"),
        "{rendered}"
    );
    let normalized = rendered.split_whitespace().collect::<Vec<_>>().join(" ");
    assert!(
        normalized.contains(cards[0]["assessment"].as_str().unwrap()),
        "{rendered}"
    );
    for instance in cards[0]["instances"].as_array().unwrap() {
        assert!(
            rendered.contains(instance["instance"].as_str().unwrap()),
            "{rendered}"
        );
        for fragment in instance["fragments"].as_array().unwrap() {
            assert!(
                normalized.contains(fragment.as_str().unwrap()),
                "{rendered}"
            );
        }
    }
    assert!(!rendered.contains("Full assessment"), "{rendered}");
    assert!(
        !rendered.contains(source["baseline_title"].as_str().unwrap().trim()),
        "{rendered}"
    );
}
