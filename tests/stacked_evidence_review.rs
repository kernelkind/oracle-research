use crossterm::event::{Event, KeyCode, KeyEvent, KeyModifiers};
use oracle_mvp::reference_map::ReviewOutcome;
use oracle_mvp::reference_tui::{
    ApprovalEvidence, ApprovalEvidenceLayout, ApprovalGuidance, ApprovalScreen, ApprovalTuiAction,
    ApprovalTuiModel,
};
use ratatui::{Terminal, backend::TestBackend};

fn screen() -> ApprovalScreen {
    ApprovalScreen {
        heading: "Containment · pair 1 of 2 · Pending".into(),
        title: None,
        scope: "Does A contain B?".into(),
        approve_label: "Approve".into(),
        reject_label: "Reject".into(),
        rejection_help: String::new(),
        guidance: Some(ApprovalGuidance {
            title: "Details".into(),
            body: "Pair details: original proposal and saved decision.".into(),
        }),
        evidence: ApprovalEvidenceLayout::Paged(vec![
            ApprovalEvidence {
                title: "A — proposed parent: Cooking".into(),
                annotation: String::new(),
                body: "A000: preparing ingredients\nA001: cooking at home".into(),
            },
            ApprovalEvidence {
                title: "B — proposed child: Baking bread".into(),
                annotation: String::new(),
                body: "B000: kneading dough\nB001: bread from the oven".into(),
            },
            ApprovalEvidence {
                title: "My comment".into(),
                annotation: String::new(),
                body: "Baking bread is a kind of cooking.".into(),
            },
        ]),
    }
}

fn model() -> ApprovalTuiModel {
    ApprovalTuiModel::new_navigable_stacked_review(screen(), String::new())
}

fn key(model: &mut ApprovalTuiModel, code: KeyCode) -> ApprovalTuiAction {
    model.handle_event(Event::Key(KeyEvent::new(code, KeyModifiers::NONE)))
}

fn render(model: &mut ApprovalTuiModel, width: u16, height: u16) -> String {
    let mut terminal = Terminal::new(TestBackend::new(width, height)).unwrap();
    terminal.draw(|frame| model.render(frame)).unwrap();
    let buffer = terminal.backend().buffer();
    (0..height)
        .map(|y| {
            (0..width)
                .map(|x| buffer[(x, y)].symbol())
                .collect::<String>()
        })
        .collect::<Vec<_>>()
        .join("\n")
}

fn flat(text: &str) -> String {
    text.split_whitespace().collect::<Vec<_>>().join(" ")
}

#[test]
fn both_titles_masks_and_my_comment_are_visible_together_at_minimum_size() {
    let rendered = render(&mut model(), 72, 24);
    for expected in [
        "A — proposed parent: Cooking",
        "A000: preparing ingredients",
        "B — proposed child: Baking bread",
        "B000: kneading dough",
        "My comment",
        "Baking bread is a kind of cooking.",
        "[A] Approve",
        "[R] Reject",
        "[C] Your comment",
        "[S] Skip",
        "[←/→]",
        "[Tab/Shift-Tab] Panel",
        "[j/k] Scroll",
        "[?] Details",
        "[Ctrl-C] Save/exit",
    ] {
        assert!(
            flat(&rendered).contains(expected),
            "missing {expected}:\n{rendered}"
        );
    }
    let lines: Vec<_> = rendered.lines().collect();
    for title in ["A — proposed parent:", "B — proposed child:", "My comment"] {
        let row = lines.iter().position(|line| line.contains(title)).unwrap();
        assert!(
            !lines[row].contains('┌'),
            "title belongs above box:\n{rendered}"
        );
        assert!(
            lines[row + 1].starts_with('┌'),
            "box follows title:\n{rendered}"
        );
    }
}

#[test]
fn full_titles_wrap_above_boxes_instead_of_being_truncated_in_borders() {
    let mut screen = screen();
    let ApprovalEvidenceLayout::Paged(evidence) = &mut screen.evidence else {
        unreachable!()
    };
    evidence[0].title = "A — proposed parent: Preparing food with carefully selected ingredients for friends and family at home".into();
    evidence[1].title = "B — proposed child: Baking traditional bread using slow fermentation and a wood fired oven at home".into();
    let titles = [evidence[0].title.clone(), evidence[1].title.clone()];
    let mut model = ApprovalTuiModel::new_navigable_stacked_review(screen, String::new());
    let rendered = render(&mut model, 72, 24);
    for title in titles {
        assert!(
            flat(&rendered).contains(&title),
            "title clipped:\n{rendered}"
        );
    }
    for expected in [
        "A000",
        "B000",
        "My comment",
        "Baking bread",
        "[A]",
        "[Ctrl-C]",
    ] {
        assert!(
            rendered.contains(expected),
            "missing {expected}:\n{rendered}"
        );
    }
}

#[test]
fn every_mask_is_reachable_and_panel_scrolls_survive_focus_changes() {
    let mut screen = screen();
    let ApprovalEvidenceLayout::Paged(evidence) = &mut screen.evidence else {
        unreachable!()
    };
    for (index, prefix) in ['A', 'B', 'C'].into_iter().enumerate() {
        evidence[index].body = (0..40)
            .map(|line| format!("{prefix}{line:03}: exact fragment"))
            .collect::<Vec<_>>()
            .join("\n");
    }
    let mut model = ApprovalTuiModel::new_navigable_stacked_review(screen, String::new());
    render(&mut model, 72, 24);
    for prefix in ['A', 'B', 'C'] {
        let mut seen = String::new();
        for _ in 0..45 {
            seen.push_str(&render(&mut model, 72, 24));
            assert_eq!(key(&mut model, KeyCode::Char('j')), ApprovalTuiAction::None);
        }
        for line in 0..40 {
            assert!(seen.contains(&format!("{prefix}{line:03}: exact fragment")));
        }
        assert_eq!(key(&mut model, KeyCode::Tab), ApprovalTuiAction::None);
    }
    let rendered = render(&mut model, 72, 24);
    for expected in ["A039", "B039", "C039"] {
        assert!(
            rendered.contains(expected),
            "lost scroll {expected}:\n{rendered}"
        );
    }
    key(&mut model, KeyCode::Home);
    let rendered = render(&mut model, 72, 24);
    for expected in ["A000", "B039", "C039"] {
        assert!(
            rendered.contains(expected),
            "independent scroll {expected}:\n{rendered}"
        );
    }
    key(&mut model, KeyCode::BackTab);
    let rendered = render(&mut model, 72, 24);
    assert!(
        rendered.contains("C039"),
        "reverse Tab resets scroll:\n{rendered}"
    );
}

#[test]
fn larger_screens_show_more_masks_without_changing_titles_or_comments() {
    let mut screen = screen();
    let ApprovalEvidenceLayout::Paged(evidence) = &mut screen.evidence else {
        unreachable!()
    };
    for (index, prefix) in ['A', 'B'].into_iter().enumerate() {
        evidence[index].body = (0..20)
            .map(|line| format!("{prefix}{line:03}: exact fragment"))
            .collect::<Vec<_>>()
            .join("\n");
    }
    let mut model = ApprovalTuiModel::new_navigable_stacked_review(screen, String::new());
    let small = render(&mut model, 72, 24);
    let large = render(&mut model, 100, 60);
    assert!(large.matches("exact fragment").count() > small.matches("exact fragment").count());
    for expected in ["A019", "B019", "Baking bread is a kind of cooking."] {
        assert!(large.contains(expected), "missing {expected}:\n{large}");
    }
}

#[test]
fn decisions_navigation_comment_editing_and_details_use_existing_actions() {
    let mut model = ApprovalTuiModel::new_navigable_stacked_review(screen(), "saved note".into());
    render(&mut model, 72, 24);
    for (code, action) in [
        (KeyCode::Left, ApprovalTuiAction::PreviousItem),
        (KeyCode::Right, ApprovalTuiAction::NextItem),
        (
            KeyCode::Char('a'),
            ApprovalTuiAction::Submit {
                outcome: ReviewOutcome::Approved,
                comment: "saved note".into(),
            },
        ),
        (
            KeyCode::Char('r'),
            ApprovalTuiAction::Submit {
                outcome: ReviewOutcome::Rejected,
                comment: "saved note".into(),
            },
        ),
        (
            KeyCode::Char('s'),
            ApprovalTuiAction::Skip {
                comment: "saved note".into(),
            },
        ),
    ] {
        assert_eq!(key(&mut model, code), action);
    }
    key(&mut model, KeyCode::Char('c'));
    let rendered = render(&mut model, 72, 24);
    for expected in [
        "Your comment (optional)",
        "> saved note",
        "[Enter] Save",
        "[Esc] Cancel",
        "My comment",
    ] {
        assert!(
            flat(&rendered).contains(expected),
            "missing {expected}:\n{rendered}"
        );
    }
    model.handle_event(Event::Paste(" revised".into()));
    assert_eq!(
        key(&mut model, KeyCode::Enter),
        ApprovalTuiAction::SaveComment {
            comment: "saved note revised".into()
        }
    );
    key(&mut model, KeyCode::Char('?'));
    let rendered = render(&mut model, 72, 24);
    assert!(rendered.contains("Pair details: original proposal and saved decision."));
    assert_eq!(key(&mut model, KeyCode::Char('a')), ApprovalTuiAction::None);
    key(&mut model, KeyCode::Esc);
    assert!(render(&mut model, 72, 24).contains("Baking bread is a kind of cooking."));
    assert_eq!(
        model.handle_event(Event::Key(KeyEvent::new(
            KeyCode::Char('c'),
            KeyModifiers::CONTROL
        ))),
        ApprovalTuiAction::Pause
    );
}

#[test]
fn titles_that_cannot_fit_require_more_space_instead_of_covering_controls() {
    let mut screen = screen();
    let ApprovalEvidenceLayout::Paged(evidence) = &mut screen.evidence else {
        unreachable!()
    };
    evidence[0].title = format!(
        "A — proposed parent: {}",
        "a long category title ".repeat(60)
    );
    let mut model = ApprovalTuiModel::new_navigable_stacked_review(screen, String::new());
    let rendered = render(&mut model, 72, 24);
    assert!(
        rendered.contains("Resize"),
        "impossible layout must be explicit:\n{rendered}"
    );
    assert_eq!(key(&mut model, KeyCode::Char('a')), ApprovalTuiAction::None);
    let rendered = render(&mut model, 100, 60);
    assert!(
        rendered.contains("B000: kneading dough"),
        "resize recovers all boxes:\n{rendered}"
    );
    assert_eq!(
        key(&mut model, KeyCode::Char('a')),
        ApprovalTuiAction::Submit {
            outcome: ReviewOutcome::Approved,
            comment: String::new()
        }
    );
}
