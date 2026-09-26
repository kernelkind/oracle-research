use std::collections::BTreeMap;

use crossterm::event::{Event, KeyCode, KeyEvent, KeyModifiers};
use oracle_mvp::manual_note_hierarchy::{ManualCategory, ManualNote, ManualNoteHierarchy};
use oracle_mvp::manual_note_hierarchy_tui::ManualNoteExplorer;
use ratatui::Terminal;
use ratatui::backend::TestBackend;

fn hierarchy(labels: &[&str]) -> ManualNoteHierarchy {
    ManualNoteHierarchy {
        hierarchy_id: "GDC09".to_owned(),
        root_node_id: "0".to_owned(),
        nodes: labels
            .iter()
            .enumerate()
            .map(|(level, label)| {
                let node_id = level.to_string();
                let is_leaf = level + 1 == labels.len();
                (
                    node_id.clone(),
                    ManualCategory {
                        node_id,
                        label: (*label).to_owned(),
                        children: if is_leaf {
                            vec![]
                        } else {
                            vec![(level + 1).to_string()]
                        },
                        note_ids: if is_leaf {
                            vec!["N001".to_owned()]
                        } else {
                            vec![]
                        },
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
                content: format!(
                    "Original opening.\n{}\nOriginal ending marker.",
                    (0..120)
                        .map(|index| format!("Original line {index:03}."))
                        .collect::<Vec<_>>()
                        .join("\n")
                ),
            },
        )]),
    }
}

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

fn assert_breadcrumb(rendered: &str, labels: &[&str]) {
    let unwrapped = rendered.split_whitespace().collect::<Vec<_>>().join(" ");
    let expected = labels.join(" > ");
    assert!(
        unwrapped.contains(&expected),
        "missing full breadcrumb {expected:?}:\n{rendered}"
    );
    assert!(!rendered.contains("Parent:"), "{rendered}");
    assert!(rendered.contains("GDC09"), "{rendered}");
}

const SHORT_PATH: &[&str] = &["Subjects", "Food", "Drinks", "Coffee", "Espresso"];

#[test]
fn category_breadcrumbs_keep_every_ancestor_at_every_depth() {
    let mut model = ManualNoteExplorer::categories(hierarchy(SHORT_PATH));
    for depth in 1..=SHORT_PATH.len() {
        let menu = screen(&mut model);
        assert_breadcrumb(&menu, &SHORT_PATH[..depth]);
        if depth < SHORT_PATH.len() {
            assert!(menu.contains("N Notes"), "{menu}");
        }
        key(&mut model, KeyCode::Enter);
    }
    let leaf = screen(&mut model);
    assert!(leaf.contains("Original opening."), "{leaf}");
}

#[test]
fn original_notes_keep_every_ancestor_at_every_depth() {
    let mut model = ManualNoteExplorer::categories(hierarchy(SHORT_PATH));
    for depth in 1..=SHORT_PATH.len() {
        let menu = screen(&mut model);
        key(&mut model, KeyCode::Char('N'));
        let note = screen(&mut model);
        assert_breadcrumb(&note, &SHORT_PATH[..depth]);
        assert!(note.contains("Original opening."), "{note}");
        assert!(note.contains("Note 1 of 1"), "{note}");
        if depth == SHORT_PATH.len() {
            break;
        }
        key(&mut model, KeyCode::Esc);
        assert_eq!(screen(&mut model), menu);
        key(&mut model, KeyCode::Enter);
    }
}

#[test]
fn category_analysis_keeps_every_ancestor_at_every_depth() {
    let mut model = ManualNoteExplorer::categories(hierarchy(SHORT_PATH));
    for depth in 1..=SHORT_PATH.len() {
        let menu = screen(&mut model);
        key(&mut model, KeyCode::Char('?'));
        let analysis = screen(&mut model);
        assert_breadcrumb(&analysis, &SHORT_PATH[..depth]);
        assert!(
            analysis.contains("Original category analysis."),
            "{analysis}"
        );
        key(&mut model, KeyCode::Esc);
        assert_eq!(screen(&mut model), menu);
        key(&mut model, KeyCode::Enter);
    }
}

#[test]
fn wrapped_full_breadcrumbs_preserve_notes_and_navigation_at_80_by_24() {
    let labels = [
        "Root subjects",
        "Everyday food and drink",
        "Preparation techniques",
        "Coffee drinks and brewing",
        "Espresso extraction",
    ];
    let expected = labels.join(" > ");
    assert!(expected.len() > 80);
    let mut model = ManualNoteExplorer::categories(hierarchy(&labels));
    for _ in 1..labels.len() {
        key(&mut model, KeyCode::Enter);
    }
    let menu = screen(&mut model);
    assert_breadcrumb(&menu, &labels);
    assert!(menu.contains("Original opening."), "{menu}");

    key(&mut model, KeyCode::Char('N'));
    let note = screen(&mut model);
    assert_breadcrumb(&note, &labels);
    for expected in ["Original opening.", "Original line 010.", "Note 1 of 1"] {
        assert!(note.contains(expected), "missing {expected}:\n{note}");
    }
    key(&mut model, KeyCode::Char('j'));
    let scrolled = screen(&mut model);
    assert_breadcrumb(&scrolled, &labels);
    assert!(!scrolled.contains("Original opening."), "{scrolled}");
    key(&mut model, KeyCode::Char('G'));
    let ending = screen(&mut model);
    assert_breadcrumb(&ending, &labels);
    assert!(ending.contains("Original ending marker."), "{ending}");

    key(&mut model, KeyCode::Char('?'));
    let analysis = screen(&mut model);
    assert_breadcrumb(&analysis, &labels);
    assert!(
        analysis.contains("Original category analysis."),
        "{analysis}"
    );
    key(&mut model, KeyCode::Esc);
    assert_eq!(screen(&mut model), ending);
    key(&mut model, KeyCode::Esc);
    let parent = screen(&mut model);
    assert_breadcrumb(&parent, &labels[..labels.len() - 1]);
    key(&mut model, KeyCode::Enter);
    assert_eq!(screen(&mut model), menu);
}
