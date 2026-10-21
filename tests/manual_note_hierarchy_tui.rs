use std::collections::BTreeMap;

use crossterm::event::{Event, KeyCode, KeyEvent, KeyModifiers};
use oracle_mvp::manual_note_hierarchy::{ManualCategory, ManualNote, ManualNoteHierarchy};
use oracle_mvp::manual_note_hierarchy_tui::ManualNoteExplorer;
use ratatui::Terminal;
use ratatui::backend::TestBackend;
use unicode_width::UnicodeWidthStr;

fn key(model: &mut ManualNoteExplorer, code: KeyCode) -> bool {
    model.handle_event(Event::Key(KeyEvent::new(code, KeyModifiers::NONE)))
}

fn control(model: &mut ManualNoteExplorer, code: char) -> bool {
    model.handle_event(Event::Key(KeyEvent::new(
        KeyCode::Char(code),
        KeyModifiers::CONTROL,
    )))
}

fn screen(model: &mut ManualNoteExplorer, width: u16, height: u16) -> String {
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
                x += symbol.width().max(1) as u16;
            }
            line
        })
        .collect::<Vec<_>>()
        .join("\n")
}

fn nested() -> ManualNoteHierarchy {
    let nodes = [
        (
            "coffee",
            "Coffee",
            vec!["morning"],
            vec!["N001", "N002", "N003"],
        ),
        (
            "morning",
            "Morning coffee",
            vec!["espresso"],
            vec!["N001", "N002"],
        ),
        ("espresso", "Espresso", vec![], vec!["N001"]),
    ]
    .into_iter()
    .map(|(id, label, children, note_ids)| {
        (
            id.to_owned(),
            ManualCategory {
                node_id: id.to_owned(),
                label: label.to_owned(),
                children: children.into_iter().map(str::to_owned).collect(),
                note_ids: note_ids.into_iter().map(str::to_owned).collect(),
                analysis: format!("Analysis for {label}; not original note text."),
            },
        )
    })
    .collect::<BTreeMap<_, _>>();
    let notes = [
        (
            "N001",
            format!(
                "Original opening 👩🏽‍💻.\n{}\nOriginal ending marker.",
                (0..120)
                    .map(|index| format!("Original line {index:03}: coffee and espresso."))
                    .collect::<Vec<_>>()
                    .join("\n")
            ),
        ),
        ("N002", "Second original note.".to_owned()),
        ("N003", "Third original note.".to_owned()),
    ]
    .into_iter()
    .map(|(id, content)| {
        (
            id.to_owned(),
            ManualNote {
                note_id: format!("original-{id}"),
                note_short_id: id.to_owned(),
                content,
            },
        )
    })
    .collect();
    ManualNoteHierarchy {
        hierarchy_id: "manual-nested-notes".to_owned(),
        root_node_id: "coffee".to_owned(),
        nodes,
        notes,
    }
}

#[test]
fn nested_categories_stay_nested_and_analysis_is_a_separate_screen() {
    let mut model = ManualNoteExplorer::new(nested());
    let root = screen(&mut model, 80, 24);
    assert!(root.contains("Morning coffee"), "{root}");
    assert!(!root.contains("Espresso"), "{root}");
    assert!(!root.contains("Analysis for"), "{root}");
    key(&mut model, KeyCode::Enter);
    let morning = screen(&mut model, 80, 24);
    assert!(morning.contains("Coffee > Morning coffee"), "{morning}");
    assert!(morning.contains("Espresso"), "{morning}");
    key(&mut model, KeyCode::Char('?'));
    let analysis = screen(&mut model, 80, 24);
    assert!(
        analysis.contains("Analysis for Morning coffee"),
        "{analysis}"
    );
    assert!(analysis.contains("j/k"), "{analysis}");
    key(&mut model, KeyCode::Esc);
    assert_eq!(screen(&mut model, 80, 24), morning);
    key(&mut model, KeyCode::Enter);
    let note = screen(&mut model, 80, 24);
    assert!(
        note.contains("Coffee > Morning coffee > Espresso"),
        "{note}"
    );
    assert!(note.contains("N001"), "{note}");
    assert!(note.contains("Original opening 👩🏽‍💻."), "{note}");
    assert!(!note.contains("Analysis for"), "{note}");
    let body = note
        .lines()
        .filter(|line| line.starts_with('│'))
        .collect::<String>();
    assert!(
        !body.contains("N001"),
        "ID must stay outside original note: {note}"
    );
    key(&mut model, KeyCode::Backspace);
    assert_eq!(screen(&mut model, 80, 24), morning);
    key(&mut model, KeyCode::Char('h'));
    assert_eq!(screen(&mut model, 80, 24), root);
}

#[test]
fn long_original_notes_support_vim_scroll_and_jump_without_changing_note() {
    let mut model = ManualNoteExplorer::new(nested());
    key(&mut model, KeyCode::Enter);
    key(&mut model, KeyCode::Enter);
    let first = screen(&mut model, 80, 24);
    assert!(first.contains("Original opening"), "{first}");
    key(&mut model, KeyCode::Char('j'));
    let scrolled = screen(&mut model, 80, 24);
    assert!(!scrolled.contains("Original opening"), "{scrolled}");
    assert!(scrolled.contains("N001"), "{scrolled}");
    key(&mut model, KeyCode::Char('k'));
    assert_eq!(screen(&mut model, 80, 24), first);
    control(&mut model, 'd');
    assert!(!screen(&mut model, 80, 24).contains("Original opening"));
    control(&mut model, 'u');
    assert_eq!(screen(&mut model, 80, 24), first);
    key(&mut model, KeyCode::Char('G'));
    let end = screen(&mut model, 80, 24);
    assert!(end.contains("Original ending marker."), "{end}");
    key(&mut model, KeyCode::Char('g'));
    assert_eq!(screen(&mut model, 80, 24), end);
    key(&mut model, KeyCode::Char('g'));
    assert_eq!(screen(&mut model, 80, 24), first);
    control(&mut model, 'f');
    assert!(!screen(&mut model, 80, 24).contains("Original opening"));
    control(&mut model, 'b');
    assert_eq!(screen(&mut model, 80, 24), first);
}

#[test]
fn overlap_is_deduplicated_and_does_not_create_an_empty_outside_action() {
    let mut data = nested();
    data.nodes.get_mut("coffee").unwrap().note_ids = vec!["N001".to_owned()];
    data.nodes.get_mut("morning").unwrap().note_ids = vec!["N001".to_owned()];
    let mut model = ManualNoteExplorer::new(data);
    let root = screen(&mut model, 80, 24);
    assert!(root.contains("View all 1 note"), "{root}");
    assert!(!root.contains("outside children"), "{root}");
}
