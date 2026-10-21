use crossterm::event::{Event, KeyCode, KeyEvent, KeyModifiers};
use oracle_mvp::reference_map::{
    ApprovedHierarchy, HierarchyNote, LeafMembership, MembershipStrength, ReviewOutcome,
    SubjectNode,
};
use oracle_mvp::reference_tui::{
    ApprovalEvidence, ApprovalEvidenceLayout, ApprovalGuidance, ApprovalScreen, ApprovalTuiAction,
    ApprovalTuiModel, NavigationTuiAction, ReferenceNavigationTuiModel,
};
use ratatui::Terminal;
use ratatui::backend::TestBackend;
use sha2::{Digest, Sha256};

fn key(code: KeyCode) -> Event {
    Event::Key(KeyEvent::new(code, KeyModifiers::NONE))
}

fn approval_screen() -> ApprovalScreen {
    ApprovalScreen {
        heading: "Candidate 7 of 48 · 4 approved · 2 rejected".to_owned(),
        title: Some("Slot 07".to_owned()),
        scope:
            "Is there a concrete reason this note should not be included in the 48-note reference set?"
                .to_owned(),
        approve_label: "Approve — no disqualifying problem".to_owned(),
        reject_label: "Reject — explain the problem".to_owned(),
        rejection_help: "Explain what must change before rejecting.".to_owned(),
        guidance: Some(ApprovalGuidance {
            title: "Rejection guide".to_owned(),
            body: "Reject only when:\n\n\
                   • Text is corrupt, truncated, or effectively empty.\n\
                   • The note is in a language you cannot judge.\n\
                   • Essential meaning depends on missing context.\n\
                   • It duplicates or nearly duplicates another selected note.\n\
                   • A diagnostic annotation is wrong.\n\n\
                   Do not reject merely because:\n\n\
                   • You disagree with it.\n\
                   • It has several subjects.\n\
                   • It is niche, ambiguous, old, or personally uninteresting.\n\n\
                   A URL is only a problem when its contents are necessary to understand the note."
                .to_owned(),
        }),
        evidence: ApprovalEvidenceLayout::Paged(vec![
            ApprovalEvidence {
                title: "Candidate note".to_owned(),
                annotation: "Related-but-different pair · contrast-03".to_owned(),
                body: "A Rust programmer makes sourdough while listening to jazz.".to_owned(),
            },
            ApprovalEvidence {
                title: "Comparison note · Slot 08".to_owned(),
                annotation:
                    "Shown only to judge the relationship; reviewed separately.".to_owned(),
                body: "A systems programmer compares Rust and C memory models.".to_owned(),
            },
        ]),
    }
}

fn stacked_approval_screen(note: &str, subject_map: &str) -> ApprovalScreen {
    let mut screen = approval_screen();
    screen.scope = "Are these subject assignments correct?".to_owned();
    screen.approve_label = "Approve these assignments".to_owned();
    screen.evidence = ApprovalEvidenceLayout::Stacked {
        top: ApprovalEvidence {
            title: "Note".to_owned(),
            annotation: String::new(),
            body: note.to_owned(),
        },
        bottom: ApprovalEvidence {
            title: "Proposed subject map".to_owned(),
            annotation: String::new(),
            body: subject_map.to_owned(),
        },
    };
    screen
}

fn render_approval(model: &mut ApprovalTuiModel) -> String {
    render_approval_at(model, 100, 32)
}

fn render_approval_at(model: &mut ApprovalTuiModel, width: u16, height: u16) -> String {
    let backend = TestBackend::new(width, height);
    let mut terminal = Terminal::new(backend).expect("test terminal");
    terminal
        .draw(|frame| model.render(frame))
        .expect("render approval");
    terminal
        .backend()
        .buffer()
        .content()
        .iter()
        .map(|cell| cell.symbol())
        .collect()
}

#[test]
fn compact_guidance_preserves_the_note_and_controls_at_minimum_terminal_size() {
    let mut model = ApprovalTuiModel::new(approval_screen());
    let rendered = render_approval_at(&mut model, 72, 24);
    let normalized = rendered.split_whitespace().collect::<Vec<_>>().join(" ");

    assert!(normalized.contains("[?] Rejection guide"), "{rendered}");
    assert!(
        !normalized.contains("missing essential context"),
        "{rendered}"
    );
    assert!(normalized.contains("Rust programmer"), "{rendered}");
    assert!(normalized.contains("[A] Approve"), "{rendered}");
}

#[test]
fn long_approval_title_wraps_without_clipping_at_minimum_terminal_size() {
    let title = "Wistful nostalgia for a simpler time when evil could be defeated by throwing a piece of jewelry into an active volcano";
    let mut screen = approval_screen();
    screen.title = Some(title.to_owned());
    screen.scope =
        "Is this a valid atomic subject explicitly and substantively discussed in this note?"
            .to_owned();
    screen.approve_label = "Approve".to_owned();
    screen.reject_label = "Disapprove".to_owned();
    screen.evidence = ApprovalEvidenceLayout::Paged(vec![ApprovalEvidence {
        title: "Note".to_owned(),
        annotation: String::new(),
        body: "Wistfully remembering a time when we could defeat evil by throwing a piece of jewelry into a live volcano ...".to_owned(),
    }]);
    let mut model = ApprovalTuiModel::new_prompt_iteration(screen, String::new());

    let rendered = render_approval_at(&mut model, 72, 24);
    let normalized = rendered.split_whitespace().collect::<Vec<_>>().join(" ");

    assert!(normalized.contains(title), "{rendered}");
    assert!(normalized.contains("into a live volcano"), "{rendered}");
    assert!(normalized.contains("[C] Comment"), "{rendered}");
    assert!(normalized.contains("[S] Skip"), "{rendered}");
    assert!(normalized.contains("Save/exit"), "{rendered}");
}

#[test]
fn title_area_grows_beyond_two_lines_without_hiding_the_note_or_controls() {
    let title = "Wistful nostalgia for a simpler time when evil could be defeated by throwing a piece of jewelry into an active volcano, expressed through a deliberately long generated atomic-subject description that needs a third terminal line";
    let mut screen = approval_screen();
    screen.title = Some(title.to_owned());
    screen.evidence = ApprovalEvidenceLayout::Paged(vec![ApprovalEvidence {
        title: "Note".to_owned(),
        annotation: String::new(),
        body: "The complete note remains visible.".to_owned(),
    }]);
    let mut model = ApprovalTuiModel::new_prompt_iteration(screen, String::new());

    let rendered = render_approval_at(&mut model, 72, 24);
    let normalized = rendered.split_whitespace().collect::<Vec<_>>().join(" ");

    assert!(normalized.contains(title), "{rendered}");
    assert!(
        normalized.contains("The complete note remains visible."),
        "{rendered}"
    );
    assert!(normalized.contains("Save/exit"), "{rendered}");
}

#[test]
fn a_single_evidence_claim_does_not_advertise_evidence_navigation() {
    let mut screen = approval_screen();
    let first = match &screen.evidence {
        ApprovalEvidenceLayout::Paged(evidence) => evidence[0].clone(),
        ApprovalEvidenceLayout::Stacked { top, .. } => top.clone(),
    };
    screen.evidence = ApprovalEvidenceLayout::Paged(vec![first]);
    let mut model = ApprovalTuiModel::new(screen);

    let rendered = render_approval(&mut model);
    assert!(!rendered.contains("[Tab/←/→] Evidence"), "{rendered}");
}

#[test]
fn stacked_evidence_shows_the_note_and_subject_map_together() {
    let mut model = ApprovalTuiModel::new(stacked_approval_screen(
        "The exact raw note text.",
        "Books and reading — Central",
    ));

    let rendered = render_approval(&mut model);
    assert!(rendered.contains("┌Note"), "{rendered}");
    assert!(rendered.contains("The exact raw note text."), "{rendered}");
    assert!(rendered.contains("┌Proposed subject map"), "{rendered}");
    assert!(
        rendered.contains("Books and reading — Central"),
        "{rendered}"
    );
    assert!(
        !rendered.contains("Note · 1 of 2"),
        "stacked panels are not paged evidence: {rendered}"
    );
    assert!(rendered.contains("Approve these assignments"), "{rendered}");
}

#[test]
fn stacked_evidence_keeps_both_panels_visible_and_scrolls_them_independently() {
    let note = (1..=30)
        .map(|line| format!("note line {line:02}"))
        .collect::<Vec<_>>()
        .join("\n");
    let subject_map = (1..=30)
        .map(|line| format!("Subject {line:02} — Central"))
        .collect::<Vec<_>>()
        .join("\n");
    let mut model = ApprovalTuiModel::new(stacked_approval_screen(&note, &subject_map));

    let initial = render_approval_at(&mut model, 72, 24);
    assert!(initial.contains("Note · more below"), "{initial}");
    assert!(
        initial.contains("Proposed subject map · more below"),
        "{initial}"
    );
    assert!(initial.contains("[Tab/←/→] Panel"), "{initial}");
    assert!(!initial.contains("[Tab/←/→] Evidence"), "{initial}");

    assert_eq!(
        model.handle_event(key(KeyCode::Down)),
        ApprovalTuiAction::None
    );
    let note_scrolled = render_approval_at(&mut model, 72, 24);
    assert!(
        note_scrolled.contains("Note · more above and below"),
        "{note_scrolled}"
    );
    assert!(
        note_scrolled.contains("Proposed subject map · more below"),
        "{note_scrolled}"
    );

    assert_eq!(
        model.handle_event(key(KeyCode::Tab)),
        ApprovalTuiAction::None
    );
    assert_eq!(
        model.handle_event(key(KeyCode::Down)),
        ApprovalTuiAction::None
    );
    let both_scrolled = render_approval_at(&mut model, 72, 24);
    assert!(
        both_scrolled.contains("Note · more above and below"),
        "{both_scrolled}"
    );
    assert!(
        both_scrolled.contains("Proposed subject map · more above and below"),
        "{both_scrolled}"
    );

    assert_eq!(
        model.handle_event(key(KeyCode::Home)),
        ApprovalTuiAction::None
    );
    let map_reset = render_approval_at(&mut model, 72, 24);
    assert!(
        map_reset.contains("Note · more above and below"),
        "{map_reset}"
    );
    assert!(
        map_reset.contains("Proposed subject map · more below"),
        "{map_reset}"
    );
}

#[test]
fn approval_ui_shows_the_negative_review_question_and_switches_to_the_comparison_note() {
    let mut model = ApprovalTuiModel::new(approval_screen());
    let first = render_approval(&mut model);
    let normalized = first.split_whitespace().collect::<Vec<_>>().join(" ");
    assert!(first.contains("Candidate note"), "{first}");
    assert!(first.contains("Rust programmer"), "{first}");
    assert!(
        normalized.contains("Is there a concrete reason this note should not be included"),
        "{first}"
    );
    assert!(normalized.contains("[?] Rejection guide"), "{first}");
    assert!(!normalized.contains("missing essential context"), "{first}");
    assert!(
        first.contains("Approve — no disqualifying problem"),
        "{first}"
    );
    assert!(first.contains("Reject — explain the problem"), "{first}");
    assert!(!first.contains("Mixed subject"), "{first}");

    assert_eq!(
        model.handle_event(key(KeyCode::Tab)),
        ApprovalTuiAction::None
    );
    let second = render_approval(&mut model);
    assert!(second.contains("Comparison note"), "{second}");
    assert!(second.contains("reviewed separately"), "{second}");
    assert!(second.contains("memory models"), "{second}");
}

#[test]
fn rejection_guide_temporarily_replaces_the_note_without_changing_review_state() {
    let mut model = ApprovalTuiModel::new(approval_screen());

    assert_eq!(
        model.handle_event(key(KeyCode::Char('?'))),
        ApprovalTuiAction::None
    );
    let guide = render_approval_at(&mut model, 100, 40);
    let normalized = guide.split_whitespace().collect::<Vec<_>>().join(" ");
    assert!(normalized.contains("Rejection guide"), "{guide}");
    assert!(normalized.contains("missing context"), "{guide}");
    assert!(normalized.contains("A URL is only a problem"), "{guide}");
    assert!(!guide.contains("Rust programmer"), "{guide}");
    assert!(normalized.contains("[?]/[Esc] Back to note"), "{guide}");

    assert_eq!(
        model.handle_event(key(KeyCode::Char('a'))),
        ApprovalTuiAction::None
    );
    assert_eq!(
        model.handle_event(key(KeyCode::Tab)),
        ApprovalTuiAction::None
    );
    assert_eq!(
        model.handle_event(key(KeyCode::Char('?'))),
        ApprovalTuiAction::None
    );

    let restored = render_approval(&mut model);
    assert!(restored.contains("Candidate note · 1 of 2"), "{restored}");
    assert!(restored.contains("Rust programmer"), "{restored}");
    assert!(!restored.contains("Approve comment"), "{restored}");

    assert_eq!(
        model.handle_event(key(KeyCode::Char('?'))),
        ApprovalTuiAction::None
    );
    assert_eq!(
        model.handle_event(key(KeyCode::Esc)),
        ApprovalTuiAction::None
    );
    let restored_with_escape = render_approval(&mut model);
    assert!(
        restored_with_escape.contains("Rust programmer"),
        "{restored_with_escape}"
    );
}

#[test]
fn approval_help_uses_the_screen_specific_title() {
    let mut screen = approval_screen();
    screen.guidance = Some(ApprovalGuidance {
        title: "Membership scale".to_owned(),
        body: "Central: one of the note's main points.\n\
               Substantive: materially matters, but is not a main point.\n\
               Incidental: minor or supporting detail."
            .to_owned(),
    });
    let mut model = ApprovalTuiModel::new(screen);

    let initial = render_approval(&mut model);
    assert!(initial.contains("[?] Membership scale"), "{initial}");
    assert!(!initial.contains("[?] Rejection guide"), "{initial}");

    assert_eq!(
        model.handle_event(key(KeyCode::Char('?'))),
        ApprovalTuiAction::None
    );
    let help = render_approval(&mut model);
    assert!(help.contains("Membership scale"), "{help}");
    assert!(help.contains("Central:"), "{help}");
    assert!(help.contains("Substantive:"), "{help}");
    assert!(help.contains("Incidental:"), "{help}");
}

#[test]
fn screens_without_guidance_do_not_advertise_or_open_it() {
    let mut screen = approval_screen();
    screen.guidance = None;
    let mut model = ApprovalTuiModel::new(screen);

    let initial = render_approval(&mut model);
    assert!(!initial.contains("Rejection guide"), "{initial}");
    assert_eq!(
        model.handle_event(key(KeyCode::Char('?'))),
        ApprovalTuiAction::None
    );
    let unchanged = render_approval(&mut model);
    assert!(unchanged.contains("Rust programmer"), "{unchanged}");
    assert!(!unchanged.contains("Rejection guide"), "{unchanged}");
}

#[test]
fn multiline_evidence_annotation_is_fully_visible() {
    let mut screen = approval_screen();
    screen.scope.clear();
    screen.guidance = None;
    screen.evidence = ApprovalEvidenceLayout::Paged(vec![ApprovalEvidence {
        title: "Note".to_owned(),
        annotation: "Memberships:\n\
                     • Everyday fulfillment — Central\n\
                     • Nature and fleeting moments — Central\n\
                     • Meals and diets — Substantive\n\
                     • Gardening and homesteading — Substantive\n\
                     • Music and rhythm — Incidental"
            .to_owned(),
        body: "The exact note text remains the primary evidence.".to_owned(),
    }]);
    let mut model = ApprovalTuiModel::new(screen);

    let rendered = render_approval_at(&mut model, 100, 32);
    assert!(rendered.contains("exact note text"), "{rendered}");
    assert!(rendered.contains("Everyday fulfillment"), "{rendered}");
    assert!(rendered.contains("Music and rhythm"), "{rendered}");
}

#[test]
fn rejection_guide_scrolls_at_the_minimum_terminal_size() {
    let mut model = ApprovalTuiModel::new(approval_screen());
    assert_eq!(
        model.handle_event(key(KeyCode::Char('?'))),
        ApprovalTuiAction::None
    );

    let top = render_approval_at(&mut model, 72, 24);
    assert!(top.contains("Rejection guide · more below"), "{top}");
    assert_eq!(
        model.handle_event(Event::Key(KeyEvent::new(
            KeyCode::Char('d'),
            KeyModifiers::CONTROL,
        ))),
        ApprovalTuiAction::None
    );
    let scrolled = render_approval_at(&mut model, 72, 24);
    assert!(scrolled.contains("more above"), "{scrolled}");
}

#[test]
fn approval_ui_collects_a_unicode_comment_before_confirming() {
    let mut model = ApprovalTuiModel::new(approval_screen());
    assert_eq!(
        model.handle_event(key(KeyCode::Char('r'))),
        ApprovalTuiAction::None
    );
    for character in "The note is truncated 🤔".chars() {
        assert_eq!(
            model.handle_event(key(KeyCode::Char(character))),
            ApprovalTuiAction::None
        );
    }
    assert_eq!(
        model.handle_event(key(KeyCode::Backspace)),
        ApprovalTuiAction::None
    );
    assert_eq!(
        model.handle_event(Event::Paste(".".to_owned())),
        ApprovalTuiAction::None
    );
    assert_eq!(
        model.handle_event(key(KeyCode::Enter)),
        ApprovalTuiAction::Submit {
            outcome: ReviewOutcome::Rejected,
            comment: "The note is truncated .".to_owned(),
        }
    );
}

#[test]
fn approval_ui_requires_a_reason_for_rejection() {
    let mut model = ApprovalTuiModel::new(approval_screen());
    assert_eq!(
        model.handle_event(key(KeyCode::Char('r'))),
        ApprovalTuiAction::None
    );
    assert_eq!(
        model.handle_event(key(KeyCode::Enter)),
        ApprovalTuiAction::None
    );
    let rendered = render_approval(&mut model);
    assert!(
        rendered.contains("Explain what must change before rejecting."),
        "{rendered}"
    );
}

#[test]
fn approval_ui_shows_screen_specific_rejection_help() {
    let mut screen = approval_screen();
    screen.rejection_help = "Examples:\n\
                             [02] Title is unclear.\n\
                             [03] Does not belong under [01].\n\
                             Missing \"Expected subject\" under [01]."
        .to_owned();
    let mut model = ApprovalTuiModel::new(screen);
    assert_eq!(
        model.handle_event(key(KeyCode::Char('r'))),
        ApprovalTuiAction::None
    );

    let rendered = render_approval(&mut model);
    for expected in [
        "[02] Title is unclear.",
        "[03] Does not belong under [01].",
        "Missing \"Expected subject\" under [01].",
    ] {
        assert!(rendered.contains(expected), "{rendered}");
    }
}

#[test]
fn approval_ui_keeps_the_end_of_a_long_rejection_comment_visible() {
    let mut model = ApprovalTuiModel::new(approval_screen());
    assert_eq!(
        model.handle_event(key(KeyCode::Char('r'))),
        ApprovalTuiAction::None
    );
    let comment = format!(
        "{}VISIBLE COMMENT TAIL",
        "Detailed correction context. ".repeat(12)
    );
    assert_eq!(
        model.handle_event(Event::Paste(comment)),
        ApprovalTuiAction::None
    );

    let rendered = render_approval(&mut model);
    assert!(rendered.contains("VISIBLE COMMENT TAIL"), "{rendered}");
    assert!(rendered.contains("[Enter] Confirm"), "{rendered}");
}

#[test]
fn queued_control_c_is_preserved_as_a_pause_request() {
    let event = Event::Key(KeyEvent::new(KeyCode::Char('c'), KeyModifiers::CONTROL));
    let mut model = ApprovalTuiModel::new(approval_screen());
    assert_eq!(model.handle_event(event), ApprovalTuiAction::Pause);
}

#[test]
fn prompt_iteration_controls_make_decisions_directly_and_keep_comments_optional() {
    let mut approved = ApprovalTuiModel::new_prompt_iteration(approval_screen(), String::new());
    let rendered = render_approval(&mut approved);
    assert!(
        rendered.contains("[A] Approve — no disqualifying problem"),
        "{rendered}"
    );
    assert!(
        rendered.contains("[R] Reject — explain the problem"),
        "{rendered}"
    );
    assert!(rendered.contains("[C] Comment"), "{rendered}");
    assert!(rendered.contains("[S] Skip"), "{rendered}");
    assert_eq!(
        approved.handle_event(key(KeyCode::Char('a'))),
        ApprovalTuiAction::Submit {
            outcome: ReviewOutcome::Approved,
            comment: String::new(),
        }
    );

    let mut rejected = ApprovalTuiModel::new_prompt_iteration(approval_screen(), String::new());
    assert_eq!(
        rejected.handle_event(key(KeyCode::Char('r'))),
        ApprovalTuiAction::Submit {
            outcome: ReviewOutcome::Rejected,
            comment: String::new(),
        }
    );

    let mut commented = ApprovalTuiModel::new_prompt_iteration(approval_screen(), String::new());
    assert_eq!(
        commented.handle_event(key(KeyCode::Char('c'))),
        ApprovalTuiAction::None
    );
    assert_eq!(
        commented.handle_event(Event::Paste("Mask includes extra context".to_owned())),
        ApprovalTuiAction::None
    );
    assert_eq!(
        commented.handle_event(key(KeyCode::Enter)),
        ApprovalTuiAction::SaveComment {
            comment: "Mask includes extra context".to_owned(),
        }
    );
    let mut commented = ApprovalTuiModel::new_prompt_iteration(
        approval_screen(),
        "Mask includes extra context".to_owned(),
    );
    assert_eq!(
        commented.handle_event(key(KeyCode::Char('r'))),
        ApprovalTuiAction::Submit {
            outcome: ReviewOutcome::Rejected,
            comment: "Mask includes extra context".to_owned(),
        }
    );

    let mut skipped = ApprovalTuiModel::new_prompt_iteration(approval_screen(), String::new());
    assert_eq!(
        skipped.handle_event(key(KeyCode::Char('s'))),
        ApprovalTuiAction::Skip {
            comment: String::new(),
        }
    );
}

#[test]
fn prompt_iteration_controls_use_the_screen_specific_decision_labels() {
    let mut screen = approval_screen();
    screen.title = None;
    screen.approve_label = "No missing or repeated subjects".to_owned();
    screen.reject_label = "Missing or repeated subjects found".to_owned();
    let mut model = ApprovalTuiModel::new_prompt_iteration(screen, String::new());

    let rendered = render_approval_at(&mut model, 72, 24);
    let normalized = rendered.split_whitespace().collect::<Vec<_>>().join(" ");

    assert!(
        normalized.contains("[A] No missing or repeated subjects"),
        "{rendered}"
    );
    assert!(
        normalized.contains("[R] Missing or repeated subjects found"),
        "{rendered}"
    );
}

#[test]
fn a_screen_without_a_title_uses_the_released_rows_for_its_annotation() {
    let mut screen = approval_screen();
    screen.title = None;
    screen.scope.clear();
    screen.guidance = None;
    let annotation = (1..=13)
        .map(|line| format!("annotation-{line:02}"))
        .collect::<Vec<_>>()
        .join("\n");
    screen.evidence = ApprovalEvidenceLayout::Paged(vec![ApprovalEvidence {
        title: "Note".to_owned(),
        annotation,
        body: "The note remains visible.".to_owned(),
    }]);
    let mut model = ApprovalTuiModel::new_prompt_iteration(screen, String::new());

    let rendered = render_approval_at(&mut model, 72, 24);

    assert!(rendered.contains("annotation-13"), "{rendered}");
}

fn hierarchy() -> ApprovedHierarchy {
    let notes = (0..48)
        .map(|index| HierarchyNote {
            note_id: format!("{:064x}", index + 1),
            content: format!("Reference note {index}"),
        })
        .collect::<Vec<_>>();
    let memberships = |range: std::ops::Range<usize>| {
        range
            .map(|index| LeafMembership {
                note_id: notes[index].note_id.clone(),
                strength: if index == 0 {
                    MembershipStrength::Central
                } else {
                    MembershipStrength::Substantive
                },
            })
            .collect()
    };
    let technology_memberships = memberships(0..24);
    let cooking_memberships = memberships(24..48);
    let approved_notes_sha256 = "a".repeat(64);
    let hierarchy_draft_sha256 = "b".repeat(64);
    let root_node_id = "root".to_owned();
    let nodes = vec![
        SubjectNode {
            node_id: "root".to_owned(),
            label: "All subjects".to_owned(),
            children: vec!["technology".to_owned(), "cooking".to_owned()],
            memberships: vec![],
        },
        SubjectNode {
            node_id: "technology".to_owned(),
            label: "Technology".to_owned(),
            children: vec![],
            memberships: technology_memberships,
        },
        SubjectNode {
            node_id: "cooking".to_owned(),
            label: "Food and cooking".to_owned(),
            children: vec![],
            memberships: cooking_memberships,
        },
    ];
    let artifact_sha256 = format!(
        "{:x}",
        Sha256::digest(
            serde_json::to_vec(&(
                2_u32,
                approved_notes_sha256.as_str(),
                hierarchy_draft_sha256.as_str(),
                root_node_id.as_str(),
                notes.as_slice(),
                nodes.as_slice(),
            ))
            .expect("encode approved hierarchy identity")
        )
    );
    ApprovedHierarchy {
        schema_version: 2,
        approved_notes_sha256,
        hierarchy_draft_sha256,
        artifact_sha256,
        root_node_id,
        notes,
        nodes,
    }
}

fn render_navigation(model: &mut ReferenceNavigationTuiModel) -> String {
    let backend = TestBackend::new(100, 30);
    let mut terminal = Terminal::new(backend).expect("test terminal");
    terminal
        .draw(|frame| model.render(frame))
        .expect("render navigation");
    terminal
        .backend()
        .buffer()
        .content()
        .iter()
        .map(|cell| cell.symbol())
        .collect()
}

#[test]
fn finished_navigation_uses_subject_choices_then_hidden_weight_note_browsing() {
    let mut model = ReferenceNavigationTuiModel::new(hierarchy()).expect("valid hierarchy");
    let root = render_navigation(&mut model);
    assert!(root.contains("What would you like to explore?"), "{root}");
    assert!(root.contains("Technology"), "{root}");
    assert!(!root.contains("engineered systems"), "{root}");

    assert_eq!(
        model.handle_event(key(KeyCode::Enter)),
        NavigationTuiAction::None
    );
    let leaf = render_navigation(&mut model);
    assert!(leaf.contains("Technology"), "{leaf}");
    assert!(leaf.contains("Reference note 0"), "{leaf}");
    assert!(!leaf.contains("Central"), "{leaf}");
    assert!(!leaf.contains("Substantive"), "{leaf}");
    assert!(!leaf.contains("weight"), "{leaf}");

    assert_eq!(
        model.handle_event(key(KeyCode::Backspace)),
        NavigationTuiAction::None
    );
    let restored = render_navigation(&mut model);
    assert!(restored.contains("What would you like to explore?"));
    assert!(restored.contains("Technology"));
}
