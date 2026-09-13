use std::fs;
use std::path::Path;
use std::process::{Command, Stdio};

use crossterm::event::{Event, KeyCode, KeyEvent, KeyModifiers};
use oracle_mvp::reference_map::ReviewOutcome;
use oracle_mvp::reference_tui::{
    ApprovalEvidenceLayout, ApprovalScreen, ApprovalTuiAction, ApprovalTuiModel,
};
use oracle_mvp::title_prompt_review::{
    TitlePromptReviewOutcome, run_title_prompt_review, run_title_prompt_review_with_comments,
};
use ratatui::{Terminal, backend::TestBackend};
use serde_json::{Value, json};
use unicode_width::UnicodeWidthStr;

const COMMENT: &str = "Every mask shows sea salt used in food. “Sea salt” names the ingredient, but could also describe its production or chemical properties. “Foods with sea salt” captures the narrower subject these masks share.\n\nI lean toward accepting “Sea salt” because it’s accurate; I’m unsure whether the extra specificity would make the category more useful.";

fn batch() -> Value {
    json!({
        "schema_version": 1, "batch_id": "uncertain", "candidate_version": "v4", "baseline_version": "v3",
        "items": [{
            "item_id": "S001", "candidate_title": "Sea salt", "baseline_title": "Foods with Sea Salt",
            "assessment": "ORIGINAL assessment: unsure about shared food-use context.",
            "instances": [
                {"instance": "V362", "fragments": ["bagels", "sea salt flakes"]},
                {"instance": "V538", "fragments": ["Mushroom Risotto with Shrimp", "Sea Salt"]},
                {"instance": "V360", "fragments": ["bagels", "sesame", "sea salt flakes", "plain"]}
            ]
        }]
    })
}

fn write(path: &Path, value: &Value) {
    fs::write(path, serde_json::to_vec(value).unwrap()).unwrap();
}

fn read(path: &Path) -> Value {
    serde_json::from_slice(&fs::read(path).unwrap()).unwrap()
}

fn initialize(input: &Path, session: &Path) -> ApprovalScreen {
    let mut result = None;
    run_title_prompt_review(input, session, None, |screen, _| {
        result = Some(screen);
        Ok(ApprovalTuiAction::Pause)
    })
    .unwrap();
    result.unwrap()
}

fn comments(session: &Path, text: &str) -> Value {
    json!({
        "schema_version": 1,
        "batch_sha256": read(session)["session"]["batch_sha256"],
        "comments": {"S001": {"assessment_summary": "Leaning approve.", "comment": text}}
    })
}

fn model(input: &Path, session: &Path, comments: &Path) -> ApprovalTuiModel {
    let mut result = None;
    run_title_prompt_review_with_comments(
        input,
        session,
        None,
        Some(comments),
        |screen, user_comment, assistant| {
            let assistant = assistant.unwrap();
            result = Some(ApprovalTuiModel::new_title_review_with_comment(
                screen,
                user_comment,
                &assistant.assessment_summary,
                &assistant.comment,
            ));
            Ok(ApprovalTuiAction::Pause)
        },
    )
    .unwrap();
    result.unwrap()
}

fn render(model: &mut ApprovalTuiModel, width: u16, height: u16) -> String {
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
                x += UnicodeWidthStr::width(symbol).max(1) as u16;
            }
            line
        })
        .collect::<Vec<_>>()
        .join("\n")
}

fn key(model: &mut ApprovalTuiModel, code: KeyCode) -> ApprovalTuiAction {
    model.handle_event(Event::Key(KeyEvent::new(code, KeyModifiers::NONE)))
}

fn flat(text: &str) -> String {
    text.replace('│', " ")
        .split_whitespace()
        .collect::<Vec<_>>()
        .join(" ")
}

#[test]
fn comments_option_supports_either_start_at_order() {
    for options in [
        vec!["--comments", "comments.json"],
        vec!["--comments", "comments.json", "--start-at", "S001"],
        vec!["--start-at", "S001", "--comments", "comments.json"],
    ] {
        let output = Command::new(env!("CARGO_BIN_EXE_sse-mask-review"))
            .args(["review-titles", "titles.json", "session.json"])
            .args(options)
            .stdin(Stdio::null())
            .output()
            .unwrap();
        let error = String::from_utf8_lossy(&output.stderr);
        assert!(
            error.contains("title prompt review must be started from an interactive terminal"),
            "expected title-review entrypoint, got: {error}"
        );
    }
}

#[test]
fn assistant_comment_is_separate_from_exact_masks_and_fits_default_and_tall_screens() {
    let directory = tempfile::tempdir().unwrap();
    let input = directory.path().join("input.json");
    let session = directory.path().join("session.json");
    let sidecar = directory.path().join("comments.json");
    write(&input, &batch());
    let original = initialize(&input, &session);
    write(&sidecar, &comments(&session, COMMENT));
    run_title_prompt_review_with_comments(
        &input,
        &session,
        None,
        Some(&sidecar),
        |screen, user_comment, assistant| {
            assert_eq!(
                screen, original,
                "sidecar must not alter original reviewed data"
            );
            assert!(user_comment.is_empty());
            assert_eq!(assistant.unwrap().comment, COMMENT);
            Ok(ApprovalTuiAction::Pause)
        },
    )
    .unwrap();
    let ApprovalEvidenceLayout::Paged(evidence) = original.evidence else {
        panic!("masks")
    };
    let mut model = model(&input, &session, &sidecar);
    for (width, height) in [(72, 24), (80, 40)] {
        let rendered = render(&mut model, width, height);
        for expected in [
            "Sea salt",
            "My assessment: Leaning approve.",
            "┌My comment",
            "[C] Your comment",
            "[Tab] Masks/My comment",
            "[Ctrl-C] Save/exit",
        ] {
            assert!(
                rendered.contains(expected),
                "missing {expected}:\n{rendered}"
            );
        }
        for mask in evidence[0].body.lines().filter(|line| !line.is_empty()) {
            assert!(
                rendered.contains(mask),
                "missing exact mask {mask}:\n{rendered}"
            );
        }
        for paragraph in COMMENT.split("\n\n") {
            assert!(
                flat(&rendered).contains(&flat(paragraph)),
                "comment clipped:\n{rendered}"
            );
        }
        let lines: Vec<_> = rendered.lines().collect();
        let last_mask = lines
            .iter()
            .position(|line| line.contains("V360:"))
            .unwrap();
        let assessment = lines
            .iter()
            .position(|line| line.contains("My assessment:"))
            .unwrap();
        let comment = lines
            .iter()
            .position(|line| line.contains("My comment") && !line.contains("[Tab]"))
            .unwrap();
        assert_eq!(assessment, last_mask + 2, "{rendered}");
        assert_eq!(comment, assessment + 1, "{rendered}");
        assert!(!rendered.contains("ORIGINAL assessment"));
    }
}

#[test]
fn supplementary_comment_changes_neither_requeue_nor_replace_user_approval() {
    let directory = tempfile::tempdir().unwrap();
    let input = directory.path().join("input.json");
    let session = directory.path().join("session.json");
    let sidecar = directory.path().join("comments.json");
    write(&input, &batch());
    run_title_prompt_review(&input, &session, None, |_, _| {
        Ok(ApprovalTuiAction::Submit {
            outcome: ReviewOutcome::Approved,
            comment: "user's saved comment".into(),
        })
    })
    .unwrap();
    let saved = fs::read(&session).unwrap();
    for text in [COMMENT, "A changed assistant comment."] {
        write(&sidecar, &comments(&session, text));
        let outcome = run_title_prompt_review_with_comments(
            &input,
            &session,
            None,
            Some(&sidecar),
            |_, _, _| panic!("must not requeue completed approval"),
        )
        .unwrap();
        assert_eq!(
            outcome,
            TitlePromptReviewOutcome::Completed {
                approved: 1,
                rejected: 0,
                skipped: 0
            }
        );
        assert_eq!(fs::read(&session).unwrap(), saved);
    }
    run_title_prompt_review_with_comments(
        &input,
        &session,
        Some("S001"),
        Some(&sidecar),
        |screen, user_comment, assistant| {
            assert!(screen.heading.ends_with("Approved"));
            assert_eq!(user_comment, "user's saved comment");
            assert_eq!(assistant.unwrap().comment, "A changed assistant comment.");
            Ok(ApprovalTuiAction::Pause)
        },
    )
    .unwrap();
    assert_eq!(
        read(&session)["session"]["decisions"]["S001"],
        json!({"outcome": "approved", "comment": "user's saved comment"})
    );
}

#[test]
fn invalid_comments_fail_before_touching_session() {
    let directory = tempfile::tempdir().unwrap();
    let input = directory.path().join("input.json");
    let session = directory.path().join("session.json");
    let sidecar = directory.path().join("comments.json");
    write(&input, &batch());
    initialize(&input, &session);
    let saved = fs::read(&session).unwrap();
    let original = comments(&session, COMMENT);
    for (pointer, value) in [
        ("/schema_version", json!(2)),
        ("/batch_sha256", json!("wrong batch")),
        ("/comments/S001/assessment_summary", json!(" ")),
        ("/comments/S001/comment", json!("\n")),
        (
            "/comments",
            json!({"unknown": {"assessment_summary": "Approve.", "comment": COMMENT}}),
        ),
        (
            "/comments",
            json!({"S001": {"assessment_summary": "Approve.", "comment": COMMENT, "unknown": true}}),
        ),
    ] {
        let mut invalid = original.clone();
        *invalid.pointer_mut(pointer).unwrap() = value;
        write(&sidecar, &invalid);
        assert!(
            run_title_prompt_review_with_comments(
                &input,
                &session,
                None,
                Some(&sidecar),
                |_, _, _| panic!("invalid sidecar shown")
            )
            .is_err(),
            "{pointer}"
        );
        assert_eq!(fs::read(&session).unwrap(), saved);
    }
}

#[test]
fn changed_review_input_still_cannot_inherit_approval_even_with_rebound_comments() {
    let directory = tempfile::tempdir().unwrap();
    let input = directory.path().join("input.json");
    let session = directory.path().join("session.json");
    let sidecar = directory.path().join("comments.json");
    write(&input, &batch());
    run_title_prompt_review(&input, &session, None, |_, _| {
        Ok(ApprovalTuiAction::Submit {
            outcome: ReviewOutcome::Approved,
            comment: String::new(),
        })
    })
    .unwrap();
    let saved = fs::read(&session).unwrap();
    for (index, pointer) in [
        "/items/0/assessment",
        "/items/0/candidate_title",
        "/items/0/baseline_title",
        "/items/0/instances/0/fragments/0",
    ]
    .into_iter()
    .enumerate()
    {
        let mut changed = batch();
        *changed.pointer_mut(pointer).unwrap() = json!("Changed reviewed input");
        write(&input, &changed);
        let other_session = directory.path().join(format!("other-{index}.json"));
        initialize(&input, &other_session);
        write(&sidecar, &comments(&other_session, COMMENT));
        let error = run_title_prompt_review_with_comments(
            &input,
            &session,
            Some("S001"),
            Some(&sidecar),
            |_, _, _| panic!("changed input shown"),
        )
        .unwrap_err();
        assert!(
            error
                .to_string()
                .contains("review session belongs to a different title batch"),
            "{error}"
        );
        assert_eq!(fs::read(&session).unwrap(), saved);
    }
}

#[test]
fn comparison_and_user_comment_do_not_confuse_assistant_comment_or_approval() {
    let directory = tempfile::tempdir().unwrap();
    let input = directory.path().join("input.json");
    let session = directory.path().join("session.json");
    let sidecar = directory.path().join("comments.json");
    write(&input, &batch());
    initialize(&input, &session);
    write(&sidecar, &comments(&session, COMMENT));
    let mut model = model(&input, &session, &sidecar);
    let initial = render(&mut model, 72, 24);
    key(&mut model, KeyCode::Char('b'));
    let mut comparison = render(&mut model, 72, 24);
    for _ in 0..30 {
        key(&mut model, KeyCode::Down);
        comparison.push_str(&render(&mut model, 72, 24));
    }
    for expected in [
        "Foods with Sea Salt",
        "My assessment: ORIGINAL assessment",
        "not to my later comment",
    ] {
        assert!(
            flat(&comparison).contains(expected),
            "missing {expected}: {comparison}"
        );
    }
    assert_eq!(key(&mut model, KeyCode::Char('a')), ApprovalTuiAction::None);
    key(&mut model, KeyCode::Esc);
    assert_eq!(render(&mut model, 72, 24), initial);
    key(&mut model, KeyCode::Char('c'));
    key(&mut model, KeyCode::Char('b'));
    key(&mut model, KeyCode::Char('B'));
    let editing = render(&mut model, 72, 24);
    assert!(editing.contains("Your comment (optional)"));
    assert!(editing.contains("> bB"));
    assert!(editing.contains("My comment"));
    assert_eq!(
        key(&mut model, KeyCode::Enter),
        ApprovalTuiAction::SaveComment {
            comment: "bB".into()
        }
    );
    assert_eq!(
        key(&mut model, KeyCode::Char('a')),
        ApprovalTuiAction::Submit {
            outcome: ReviewOutcome::Approved,
            comment: "bB".into()
        }
    );
}

#[test]
fn both_panes_scroll_independently_and_complete_long_text_remains_accessible() {
    let directory = tempfile::tempdir().unwrap();
    let input = directory.path().join("input.json");
    let session = directory.path().join("session.json");
    let sidecar = directory.path().join("comments.json");
    let mut data = batch();
    data["items"][0]["candidate_title"] = json!(format!(
        "PINNED TITLE {} CANDIDATE END",
        "long title ".repeat(100)
    ));
    data["items"][0]["instances"] = json!((1..=30).map(|id| json!({"instance": format!("V{id:03}"), "fragments": [format!("Exact mask {id:03}: café 🧡"), format!("Separate fragment {id:03}")]})).collect::<Vec<_>>());
    write(&input, &data);
    initialize(&input, &session);
    let mut supplemental = comments(
        &session,
        &(1..=60)
            .map(|id| format!("Comment line {id:03}: café 🧡"))
            .collect::<Vec<_>>()
            .join("\n"),
    );
    supplemental["comments"]["S001"]["assessment_summary"] =
        json!(format!("{} SUMMARY END", "long summary ".repeat(100)));
    write(&sidecar, &supplemental);
    let mut model = model(&input, &session, &sidecar);
    let mut seen_masks = render(&mut model, 72, 24);
    assert!(seen_masks.contains("… [B] Full title"));
    assert!(seen_masks.contains("… [B] Full assessment"));
    for _ in 0..90 {
        key(&mut model, KeyCode::Down);
        let rendered = render(&mut model, 72, 24);
        assert!(rendered.contains("PINNED TITLE"));
        assert!(
            rendered.contains("Comment line 001"),
            "mask scroll moved comment: {rendered}"
        );
        seen_masks.push_str(&rendered);
    }
    for id in 1..=30 {
        assert!(seen_masks.contains(&format!(
            "V{id:03}: ⟦Exact mask {id:03}: café 🧡⟧ ⟦Separate fragment {id:03}⟧"
        )));
    }
    key(&mut model, KeyCode::Tab);
    let mut seen_comments = render(&mut model, 72, 24);
    for _ in 0..90 {
        key(&mut model, KeyCode::Down);
        let rendered = render(&mut model, 72, 24);
        assert!(
            rendered.contains("V030:"),
            "comment scroll moved masks: {rendered}"
        );
        seen_comments.push_str(&rendered);
    }
    for id in 1..=60 {
        assert!(seen_comments.contains(&format!("Comment line {id:03}: café 🧡")));
    }
    let before_compare = render(&mut model, 72, 24);
    key(&mut model, KeyCode::Char('b'));
    let mut comparison = render(&mut model, 72, 24);
    for _ in 0..160 {
        key(&mut model, KeyCode::Down);
        comparison.push_str(&render(&mut model, 72, 24));
    }
    assert!(flat(&comparison).contains("CANDIDATE END"));
    assert!(flat(&comparison).contains("SUMMARY END"));
    key(&mut model, KeyCode::Esc);
    assert_eq!(render(&mut model, 72, 24), before_compare);
    key(&mut model, KeyCode::BackTab);
    let refocused_masks = render(&mut model, 72, 24);
    assert!(
        refocused_masks.contains("V030:"),
        "changing focus reset the masks: {refocused_masks}"
    );
    assert!(refocused_masks.contains("Comment line 060"));
    key(&mut model, KeyCode::Home);
    let reset_masks = render(&mut model, 72, 24);
    assert!(reset_masks.contains("V001:"));
    assert!(reset_masks.contains("Comment line 060"));
}

#[test]
fn supplementary_comments_reject_legacy_unassessed_items_before_session_mutation() {
    let directory = tempfile::tempdir().unwrap();
    let input = directory.path().join("input.json");
    let session = directory.path().join("session.json");
    let sidecar = directory.path().join("comments.json");
    let mut data = batch();
    data["items"][0]
        .as_object_mut()
        .unwrap()
        .remove("assessment");
    write(&input, &data);
    initialize(&input, &session);
    let saved = fs::read(&session).unwrap();
    write(&sidecar, &comments(&session, COMMENT));
    let error =
        run_title_prompt_review_with_comments(&input, &session, None, Some(&sidecar), |_, _, _| {
            Ok(ApprovalTuiAction::Pause)
        })
        .unwrap_err();
    assert!(
        error
            .to_string()
            .contains("comments require an assessed title review item"),
        "{error}"
    );
    assert_eq!(fs::read(&session).unwrap(), saved);
}
