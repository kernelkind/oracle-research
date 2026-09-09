use std::collections::BTreeMap;

use crossterm::event::{Event, KeyCode, KeyEvent, KeyModifiers};
use oracle_mvp::hdbscan_hierarchy::{Group, Hierarchy, MaskInstance};
use oracle_mvp::hdbscan_hierarchy_tui::HierarchyExplorer;
use ratatui::Terminal;
use ratatui::backend::TestBackend;
use unicode_width::UnicodeWidthStr;

fn mask(point: usize, fragments: &[&str]) -> MaskInstance {
    let mut text = String::from("Original beginning. ");
    let mut byte_spans = Vec::new();
    for fragment in fragments {
        let start = text.len();
        text.push_str(fragment);
        byte_spans.push((start, text.len()));
        text.push_str(" Original context. ");
    }
    text.push_str("Original ending.");
    MaskInstance {
        id: format!("V{point:03}"),
        vector_id: format!("vector-{point}"),
        note_id: format!("note-{point}"),
        text,
        byte_spans,
        fragments: fragments
            .iter()
            .map(|fragment| (*fragment).to_owned())
            .collect(),
    }
}

// This is the retained hierarchy supplied by the production selection loader.
// Missing raw levels are already skipped, and vectors are exact direct members.
fn fixture() -> Hierarchy {
    let groups = [
        (10, None, vec![11, 12], vec![0], 6, 6),
        (11, Some(10), vec![13, 14], vec![1], 4, 4),
        (12, Some(10), vec![], vec![5], 1, 1),
        (13, Some(11), vec![], vec![2, 3], 2, 2),
        (14, Some(11), vec![], vec![4], 1, 1),
    ]
    .into_iter()
    .map(
        |(id, parent, children, vectors, note_count, vector_count)| {
            (
                id,
                Group {
                    id,
                    parent,
                    children,
                    vectors,
                    note_count,
                    vector_count,
                },
            )
        },
    )
    .collect();
    let vectors = [
        (0, vec![mask(0, &["Root remaining meaning"])]),
        (1, vec![mask(1, &["Café morning", "shoreline 🌊"])]),
        (2, vec![mask(2, &["Beach"])]),
        (3, vec![mask(3, &["Sand"])]),
        (4, vec![mask(4, &["Office"])]),
        (5, vec![mask(5, &["Coffee"])]),
    ]
    .into_iter()
    .collect::<BTreeMap<_, _>>();
    Hierarchy {
        root: 10,
        groups,
        vectors,
    }
}

fn key(model: &mut HierarchyExplorer, code: KeyCode) -> bool {
    model.handle_event(Event::Key(KeyEvent::new(code, KeyModifiers::NONE)))
}

fn screen(model: &mut HierarchyExplorer, width: u16, height: u16) -> String {
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
                // Wide graphemes occupy following cells, whose blank placeholders
                // are not additional source spaces on the actual terminal.
                x += symbol.width().max(1) as u16;
            }
            line
        })
        .collect::<Vec<_>>()
        .join("\n")
}

#[test]
fn selection_preserves_nested_groups_and_expansion_when_showing_parent() {
    let mut model = HierarchyExplorer::new_selection(fixture(), Some(11)).unwrap();
    let initial = screen(&mut model, 100, 40);
    assert!(initial.contains("Showing branch 11"));
    assert!(initial.contains("▸ 13"));
    assert!(initial.contains("▸ 14"));
    assert!(!initial.contains("⟦Beach⟧"));
    key(&mut model, KeyCode::Char('j')); // first retained child, not parent masks
    key(&mut model, KeyCode::Char('l'));
    assert!(screen(&mut model, 100, 40).contains("⟦Beach⟧"));
    key(&mut model, KeyCode::Char('U'));
    let parent = screen(&mut model, 100, 40);
    for text in [
        "Showing branch 10",
        "▾ 11",
        "▾ 13",
        "▸ 14",
        "▸ 12",
        "⟦Beach⟧",
        "⟦Root remaining meaning⟧",
    ] {
        assert!(parent.contains(text), "missing {text}: {parent}");
    }
    // U preserves selection too: h must collapse 13 rather than the new branch.
    key(&mut model, KeyCode::Char('h'));
    let collapsed = screen(&mut model, 100, 40);
    assert!(!collapsed.contains("⟦Beach⟧"));
    assert!(collapsed.contains("▾ 11"));
    key(&mut model, KeyCode::Char('l'));
    assert!(screen(&mut model, 100, 40).contains("⟦Beach⟧"));
    key(&mut model, KeyCode::Char('F'));
    assert!(screen(&mut model, 100, 40).contains("Showing branch 13"));
    key(&mut model, KeyCode::Char('U'));
    assert!(screen(&mut model, 100, 40).contains("Showing branch 11"));
}

#[test]
fn selection_children_are_reachable_before_hundreds_of_direct_masks() {
    let mut data = fixture();
    let parent = data.groups.get_mut(&11).unwrap();
    parent.vectors = (100..700).collect();
    parent.note_count = 603;
    parent.vector_count = 603;
    for point in 100..700 {
        data.vectors
            .insert(point, vec![mask(point, &[&format!("Parent mask {point}")])]);
    }
    let mut model = HierarchyExplorer::new_selection(data, Some(11)).unwrap();
    let initial = screen(&mut model, 100, 18);
    assert!(initial.contains("▸ 13"), "{initial}");
    assert!(initial.contains("▸ 14"), "{initial}");
    assert!(initial.find("▸ 14").unwrap() < initial.find("⟦Parent mask 100⟧").unwrap());
    key(&mut model, KeyCode::Char('j'));
    key(&mut model, KeyCode::Char('l'));
    let child = screen(&mut model, 100, 18);
    assert!(child.contains("⟦Beach⟧"), "{child}");
    key(&mut model, KeyCode::Char('G'));
    let last = screen(&mut model, 100, 18);
    assert!(last.contains("⟦Parent mask 699⟧"), "{last}");
    key(&mut model, KeyCode::Enter);
    assert!(
        screen(&mut model, 100, 18)
            .contains("Original beginning. ⟦Parent mask 699⟧ Original context. Original ending.")
    );
    key(&mut model, KeyCode::Esc);
    key(&mut model, KeyCode::Char('h'));
    let containing_group = screen(&mut model, 100, 18);
    assert!(containing_group.contains("▶ ▾ 11"), "{containing_group}");
}

#[test]
fn selection_shows_exact_space_separated_masks_aliases_and_full_source_note() {
    let mut data = fixture();
    let mut alias = data.vectors[&1][0].clone();
    alias.id = "V999".to_owned();
    alias.vector_id = "same-source-alias".to_owned();
    data.vectors.get_mut(&1).unwrap().push(alias);
    let mut model = HierarchyExplorer::new_selection(data, Some(11)).unwrap();
    let tree = screen(&mut model, 120, 24);
    assert!(
        tree.contains("V001, V999  ⟦Café morning⟧ ⟦shoreline 🌊⟧"),
        "{tree}"
    );
    assert!(!tree.contains("Original context."));
    key(&mut model, KeyCode::Char('G')); // direct mask follows retained children
    key(&mut model, KeyCode::Enter);
    let note = screen(&mut model, 150, 24);
    assert!(note.contains("Original beginning. ⟦Café morning⟧ Original context. ⟦shoreline 🌊⟧ Original context. Original ending."), "{note}");
    assert!(note.contains("V001, V999"));
    key(&mut model, KeyCode::Esc);
    assert!(screen(&mut model, 120, 24).contains("Showing branch 11"));
    assert!(key(&mut model, KeyCode::Char('q')));
}

#[test]
fn selection_heading_and_help_identify_the_saved_read_only_proposal() {
    let mut model = HierarchyExplorer::new_selection(fixture(), None).unwrap();
    let tree = screen(&mut model, 120, 24);
    assert!(
        tree.contains("HDBv2 selection · proposal · read-only"),
        "{tree}"
    );
    assert!(tree.contains("j/k"));
    assert!(tree.contains("h/l"));
    key(&mut model, KeyCode::Char('?'));
    let help = screen(&mut model, 150, 60);
    for text in [
        "saved selection",
        "retained",
        "displayed ancestor",
        "proposal",
        "read-only",
        "distinct source notes",
        "h/j/k/l",
        "Ctrl-F/B",
        "Ctrl-U/D",
        "gg",
    ] {
        assert!(help.contains(text), "missing {text}: {help}");
    }
    assert!(!help.contains("No groups or members are filtered"));
    assert!(!help.contains("belong to that parent in the saved tree"));
    assert!(!help.contains("They have not been discarded or moved"));
}

#[test]
fn selection_vim_keys_share_tree_note_and_help_navigation() {
    let mut data = fixture();
    let long = (0..80)
        .map(|line| format!("Original line {line:02}.\n"))
        .collect::<String>();
    data.vectors.insert(1, vec![mask(1, &[&long])]);
    for mode in ["tree", "note", "help"] {
        let mut vim = HierarchyExplorer::new_selection(data.clone(), Some(11)).unwrap();
        let mut arrows = HierarchyExplorer::new_selection(data.clone(), Some(11)).unwrap();
        for model in [&mut vim, &mut arrows] {
            if mode == "note" {
                key(model, KeyCode::End);
                key(model, KeyCode::Enter);
            } else if mode == "help" {
                key(model, KeyCode::Char('?'));
            }
            screen(model, 100, 18);
        }
        for (letter, existing, modifiers) in [
            ('j', KeyCode::Down, KeyModifiers::NONE),
            ('l', KeyCode::Right, KeyModifiers::NONE),
            ('h', KeyCode::Left, KeyModifiers::NONE),
            ('k', KeyCode::Up, KeyModifiers::NONE),
            ('f', KeyCode::PageDown, KeyModifiers::CONTROL),
            ('b', KeyCode::PageUp, KeyModifiers::CONTROL),
            ('G', KeyCode::End, KeyModifiers::NONE),
        ] {
            vim.handle_event(Event::Key(KeyEvent::new(KeyCode::Char(letter), modifiers)));
            key(&mut arrows, existing);
            assert_eq!(
                screen(&mut vim, 100, 18),
                screen(&mut arrows, 100, 18),
                "{mode}: {letter}"
            );
        }
        key(&mut vim, KeyCode::Char('g'));
        key(&mut vim, KeyCode::Char('g'));
        key(&mut arrows, KeyCode::Home);
        assert_eq!(
            screen(&mut vim, 100, 18),
            screen(&mut arrows, 100, 18),
            "{mode}: gg"
        );
    }
}
