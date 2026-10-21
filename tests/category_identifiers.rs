use std::collections::BTreeMap;

use crossterm::event::{Event, KeyCode, KeyEvent, KeyModifiers};
use oracle_mvp::manual_note_hierarchy::{ManualCategory, ManualNote, ManualNoteHierarchy};
use oracle_mvp::manual_note_hierarchy_tui::ManualNoteExplorer;
use ratatui::Terminal;
use ratatui::backend::TestBackend;

fn key(model: &mut ManualNoteExplorer, code: KeyCode) {
    assert!(!model.handle_event(Event::Key(KeyEvent::new(code, KeyModifiers::NONE))));
}

fn screen(model: &mut ManualNoteExplorer) -> String {
    let mut terminal = Terminal::new(TestBackend::new(80, 24)).unwrap();
    terminal.draw(|frame| model.render(frame)).unwrap();
    let buffer = terminal.backend().buffer();
    (0..24)
        .map(|y| (0..80).map(|x| buffer[(x, y)].symbol()).collect::<String>())
        .collect::<Vec<_>>()
        .join("\n")
}

#[test]
fn repeated_labels_keep_the_current_id_across_notes_analysis_and_back_navigation() {
    let hierarchy = ManualNoteHierarchy {
        hierarchy_id: "GDC09".to_owned(),
        root_node_id: "0".to_owned(),
        nodes: [
            ("0", "All notes", vec!["17", "29"], vec![]),
            ("17", "Coffee", vec![], vec!["N001"]),
            ("29", "Coffee", vec![], vec!["N001"]),
        ]
        .into_iter()
        .map(|(id, label, children, notes)| {
            (
                id.to_owned(),
                ManualCategory {
                    node_id: id.to_owned(),
                    label: label.to_owned(),
                    children: children.into_iter().map(str::to_owned).collect(),
                    note_ids: notes.into_iter().map(str::to_owned).collect(),
                    analysis: "Original category analysis.".to_owned(),
                },
            )
        })
        .collect(),
        notes: BTreeMap::from([(
            "N001".to_owned(),
            ManualNote {
                note_id: "original-note".to_owned(),
                note_short_id: "N001".to_owned(),
                content: "Original note text, without category metadata.".to_owned(),
            },
        )]),
    };
    let mut model = ManualNoteExplorer::categories(hierarchy);
    let root = screen(&mut model);
    for expected in ["All notes", "Coffee · 1 note"] {
        assert!(root.contains(expected), "missing {expected}:\n{root}");
    }
    assert_eq!(root.matches("Coffee · 1 note").count(), 2, "{root}");
    for id in ["[0]", "[17]", "[29]"] {
        assert!(!root.contains(id), "{root}");
    }
    for id in ["17", "29"] {
        let selected_root = screen(&mut model);
        key(&mut model, KeyCode::Enter);
        let category = screen(&mut model);
        let breadcrumb = "All notes > Coffee";
        assert!(category.contains(breadcrumb), "{category}");
        assert!(!category.contains("All notes [0] >"), "{category}");
        assert!(category.contains("Original note text"), "{category}");

        key(&mut model, KeyCode::Char('N'));
        let note = screen(&mut model);
        assert!(note.contains(breadcrumb), "{note}");
        assert!(
            note.contains("Original note text, without category metadata."),
            "{note}"
        );
        let body = note
            .lines()
            .filter(|line| line.contains('│'))
            .collect::<String>();
        for absent in ["[0]", "[17]", "[29]", "Coffee", "GDC09", "N001"] {
            assert!(!body.contains(absent), "unexpected {absent}:\n{body}");
        }
        key(&mut model, KeyCode::Char('?'));
        let analysis = screen(&mut model);
        assert!(
            analysis.contains(&format!("{breadcrumb} [{id}]")),
            "{analysis}"
        );
        assert!(analysis.contains("GDC09"), "{analysis}");
        assert!(
            analysis.contains("Original category analysis."),
            "{analysis}"
        );
        key(&mut model, KeyCode::Esc);
        assert_eq!(screen(&mut model), note);
        key(&mut model, KeyCode::Char('?'));
        assert_eq!(screen(&mut model), analysis);
        key(&mut model, KeyCode::Esc);
        assert_eq!(screen(&mut model), category);
        key(&mut model, KeyCode::Esc);
        assert_eq!(screen(&mut model), selected_root);
        key(&mut model, KeyCode::Enter);
        assert_eq!(screen(&mut model), category);
        key(&mut model, KeyCode::Esc);
        key(&mut model, KeyCode::Down);
    }
}
