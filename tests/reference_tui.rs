use crossterm::event::{Event, KeyCode, KeyEvent, KeyModifiers};
use oracle_mvp::reference_map::{
    ApprovedHierarchy, HierarchyNote, LeafMembership, MembershipStrength, ReviewOutcome,
    SubjectNode,
};
use oracle_mvp::reference_tui::{
    ApprovalEvidence, ApprovalScreen, ApprovalTuiAction, ApprovalTuiModel, NavigationTuiAction,
    ReferenceNavigationTuiModel,
};
use ratatui::Terminal;
use ratatui::backend::TestBackend;
use sha2::{Digest, Sha256};

fn key(code: KeyCode) -> Event {
    Event::Key(KeyEvent::new(code, KeyModifiers::NONE))
}

fn approval_screen() -> ApprovalScreen {
    ApprovalScreen {
        heading: "Candidate 7 of 64 · 4 approved · 2 rejected".to_owned(),
        title: "Slot 07 · Mixed subject".to_owned(),
        scope: "Chosen as one half of contrast pair contrast-03.".to_owned(),
        evidence: vec![
            ApprovalEvidence {
                title: "Candidate note".to_owned(),
                annotation: "Mixed · niche: none".to_owned(),
                body: "A Rust programmer makes sourdough while listening to jazz.".to_owned(),
            },
            ApprovalEvidence {
                title: "Paired note".to_owned(),
                annotation: "Contrast pair contrast-03".to_owned(),
                body: "A systems programmer compares Rust and C memory models.".to_owned(),
            },
        ],
    }
}

fn render_approval(model: &mut ApprovalTuiModel) -> String {
    let backend = TestBackend::new(100, 32);
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
fn approval_ui_shows_context_and_switches_to_the_paired_note() {
    let mut model = ApprovalTuiModel::new(approval_screen());
    let first = render_approval(&mut model);
    assert!(first.contains("Candidate note"), "{first}");
    assert!(first.contains("Rust programmer"), "{first}");
    assert!(first.contains("Chosen as one half"), "{first}");

    assert_eq!(
        model.handle_event(key(KeyCode::Tab)),
        ApprovalTuiAction::None
    );
    let second = render_approval(&mut model);
    assert!(second.contains("Paired note"), "{second}");
    assert!(second.contains("memory models"), "{second}");
}

#[test]
fn approval_ui_collects_a_unicode_comment_before_confirming() {
    let mut model = ApprovalTuiModel::new(approval_screen());
    assert_eq!(
        model.handle_event(key(KeyCode::Char('r'))),
        ApprovalTuiAction::None
    );
    for character in "Wrong category 🤔".chars() {
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
            comment: "Wrong category .".to_owned(),
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

fn hierarchy() -> ApprovedHierarchy {
    let notes = (0..64)
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
    let technology_memberships = memberships(0..32);
    let cooking_memberships = memberships(32..64);
    let approved_notes_sha256 = "a".repeat(64);
    let hierarchy_draft_sha256 = "b".repeat(64);
    let root_node_id = "root".to_owned();
    let nodes = vec![
        SubjectNode {
            node_id: "root".to_owned(),
            label: "All subjects".to_owned(),
            scope: "Hidden root".to_owned(),
            children: vec!["technology".to_owned(), "cooking".to_owned()],
            memberships: vec![],
        },
        SubjectNode {
            node_id: "technology".to_owned(),
            label: "Technology".to_owned(),
            scope: "Software and engineered systems".to_owned(),
            children: vec![],
            memberships: technology_memberships,
        },
        SubjectNode {
            node_id: "cooking".to_owned(),
            label: "Food and cooking".to_owned(),
            scope: "Preparing and understanding food".to_owned(),
            children: vec![],
            memberships: cooking_memberships,
        },
    ];
    let artifact_sha256 = format!(
        "{:x}",
        Sha256::digest(
            serde_json::to_vec(&(
                1_u32,
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
        schema_version: 1,
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
