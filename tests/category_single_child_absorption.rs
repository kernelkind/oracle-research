use std::collections::BTreeMap;
use std::path::Path;

use crossterm::event::{Event, KeyCode, KeyEvent, KeyModifiers};
use oracle_mvp::manual_note_hierarchy::{ManualCategory, ManualNote, ManualNoteHierarchy};
use oracle_mvp::manual_note_hierarchy_tui::ManualNoteExplorer;
use ratatui::Terminal;
use ratatui::backend::TestBackend;

fn fixture() -> ManualNoteHierarchy {
    ManualNoteHierarchy {
        hierarchy_id: "single-child-test".into(),
        root_node_id: "root".into(),
        nodes: [
            ("root", vec!["middle"], vec!["N0"]),
            ("middle", vec!["branch"], vec!["N1"]),
            ("branch", vec!["left", "right"], vec!["N1", "N2"]),
            ("left", vec!["leaf"], vec!["N3"]),
            ("leaf", vec![], vec!["N4"]),
            ("right", vec![], vec!["N2"]),
        ]
        .into_iter()
        .map(|(id, children, notes)| {
            (
                id.into(),
                ManualCategory {
                    node_id: id.into(),
                    label: format!("Title {id}"),
                    analysis: format!("Analysis {id}"),
                    children: children.into_iter().map(str::to_owned).collect(),
                    note_ids: notes.into_iter().map(str::to_owned).collect(),
                },
            )
        })
        .collect(),
        notes: (0..5)
            .map(|i| {
                let id = format!("N{i}");
                (
                    id.clone(),
                    ManualNote {
                        note_id: format!("original-{i}"),
                        note_short_id: id,
                        content: format!("Original note {i}."),
                    },
                )
            })
            .collect(),
    }
}

#[test]
fn parent_absorbs_entire_chain_and_leaf_without_changing_its_scope() {
    let mut hierarchy = fixture();
    let original = hierarchy.clone();
    assert_eq!(hierarchy.absorb_single_children(), 3);
    assert_eq!(hierarchy.root_node_id, "root");
    assert_eq!(
        hierarchy
            .nodes
            .keys()
            .map(String::as_str)
            .collect::<Vec<_>>(),
        ["left", "right", "root"]
    );
    assert_eq!(hierarchy.nodes["root"].children, ["left", "right"]);
    assert_eq!(hierarchy.nodes["root"].note_ids, ["N0", "N1", "N2"]);
    assert_eq!(hierarchy.nodes["left"].note_ids, ["N3", "N4"]);
    for (id, node) in &hierarchy.nodes {
        assert_eq!(node.label, original.nodes[id].label);
        assert_eq!(node.analysis, original.nodes[id].analysis);
        assert_eq!(hierarchy.note_ids(id), original.note_ids(id));
        assert_ne!(node.children.len(), 1);
    }
    assert_eq!(hierarchy.absorb_single_children(), 0);
    assert_eq!(hierarchy.notes.len(), original.notes.len());
    for (id, note) in &hierarchy.notes {
        assert_eq!(note.content, original.notes[id].content);
        assert_eq!(note.note_id, original.notes[id].note_id);
    }
}

#[test]
fn absorbed_categories_are_not_choices_and_all_their_notes_still_open() {
    let mut hierarchy = fixture();
    hierarchy.absorb_single_children();
    let mut model = ManualNoteExplorer::categories(hierarchy);
    let screen = |model: &mut ManualNoteExplorer| {
        let mut terminal = Terminal::new(TestBackend::new(80, 24)).unwrap();
        terminal.draw(|frame| model.render(frame)).unwrap();
        let buffer = terminal.backend().buffer();
        (0..24)
            .map(|y| (0..80).map(|x| buffer[(x, y)].symbol()).collect::<String>())
            .collect::<Vec<_>>()
            .join("\n")
    };
    let menu = screen(&mut model);
    for expected in ["Title root", "Title left", "Title right"] {
        assert!(menu.contains(expected), "{menu}");
    }
    for absent in [
        "Title middle",
        "Title branch",
        "Title leaf",
        "[root]",
        "[left]",
        "[right]",
    ] {
        assert!(!menu.contains(absent), "{menu}");
    }
    let key = |model: &mut ManualNoteExplorer, code| {
        assert!(!model.handle_event(Event::Key(KeyEvent::new(code, KeyModifiers::NONE))));
    };
    key(&mut model, KeyCode::Char('N'));
    for i in 0..5 {
        let note = screen(&mut model);
        assert!(note.contains(&format!("Original note {i}.")), "{note}");
        assert!(note.contains(&format!("Note {} of 5", i + 1)), "{note}");
        key(&mut model, KeyCode::Char('l'));
    }
    key(&mut model, KeyCode::Esc);
    assert_eq!(screen(&mut model), menu);
    key(&mut model, KeyCode::Enter);
    let left = screen(&mut model);
    assert!(left.contains("Title root > Title left"), "{left}");
    assert!(left.contains("No child categories"), "{left}");
    key(&mut model, KeyCode::Char('N'));
    assert!(screen(&mut model).contains("Original note 3."));
    key(&mut model, KeyCode::Char('l'));
    assert!(screen(&mut model).contains("Original note 4."));
    key(&mut model, KeyCode::Esc);
    key(&mut model, KeyCode::Esc);
    assert_eq!(screen(&mut model), menu);
}

#[test]
fn gdc09_preserves_every_retained_note_set_and_combined_mask() {
    let spec = Path::new("sse_multivector/geometric-hierarchy-v1/GDC09/categories.json");
    let source = Path::new("sse_multivector/real-note-fine-segmentation-v1/reviewed-input.json");
    let spec_before = std::fs::read(spec).unwrap();
    let source_before = std::fs::read(source).unwrap();
    let (original, masks) = ManualNoteHierarchy::load_with_masks(spec, source).unwrap();
    let masks = masks.unwrap();
    let snapshot = original
        .nodes
        .keys()
        .map(|id| {
            let notes = original.note_ids(id);
            let ranges = notes
                .iter()
                .map(|note| (note.clone(), masks.spans(id, note).to_vec()))
                .collect::<BTreeMap<_, _>>();
            (id.clone(), (notes, ranges))
        })
        .collect::<BTreeMap<_, _>>();
    let depth = |hierarchy: &ManualNoteHierarchy| {
        let mut pending = vec![(&hierarchy.root_node_id, 0)];
        let mut maximum = 0;
        while let Some((id, level)) = pending.pop() {
            maximum = maximum.max(level);
            pending.extend(
                hierarchy.nodes[id]
                    .children
                    .iter()
                    .map(|child| (child, level + 1)),
            );
        }
        maximum
    };
    assert_eq!(depth(&original), 40);
    let mut hierarchy = original.clone();
    assert_eq!(hierarchy.absorb_single_children(), 71);
    assert_eq!(hierarchy.nodes.len(), 148);
    assert_eq!(hierarchy.notes.len(), 100);
    assert_eq!(depth(&hierarchy), 28);
    for (id, node) in &hierarchy.nodes {
        assert_ne!(node.children.len(), 1);
        assert_eq!(node.label, original.nodes[id].label);
        assert_eq!(node.analysis, original.nodes[id].analysis);
        let notes = hierarchy.note_ids(id);
        assert_eq!(notes, snapshot[id].0);
        for note in notes {
            assert_eq!(masks.spans(id, &note), snapshot[id].1[&note]);
        }
    }
    assert_eq!(hierarchy.absorb_single_children(), 0);
    assert_eq!(std::fs::read(spec).unwrap(), spec_before);
    assert_eq!(std::fs::read(source).unwrap(), source_before);
}
