use std::collections::BTreeMap;

use crossterm::event::{Event, KeyCode, KeyEvent, KeyModifiers};
use oracle_mvp::hdbscan_hierarchy::{Group, Hierarchy, MaskInstance};
use oracle_mvp::hdbscan_hierarchy_tui::HierarchyExplorer;
use ratatui::Terminal;
use ratatui::backend::TestBackend;

fn fixture() -> Hierarchy {
    let groups = [
        (10, None, vec![11, 12], vec![0], 5, 6),
        (11, Some(10), vec![13, 14], vec![1], 3, 4),
        (12, Some(10), vec![], vec![5], 1, 1),
        (13, Some(11), vec![], vec![2, 3], 1, 2),
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
        "Root-only meaning",
        "Parent-only meaning",
        "Beach",
        "Shoreline",
        "Office",
        "Coffee",
    ]
    .into_iter()
    .enumerate()
    .map(|(i, fragment)| {
        let text = format!("Before {fragment} after. Original context.");
        let start = text.find(fragment).unwrap();
        let mask = MaskInstance {
            id: format!("V{:03}", i + 1),
            vector_id: format!("vector-{i}"),
            note_id: format!("note-{}", if i == 3 { 2 } else { i }),
            text,
            byte_spans: vec![(start, start + fragment.len())],
            fragments: vec![fragment.to_owned()],
        };
        (i, vec![mask])
    })
    .collect::<BTreeMap<_, _>>();
    Hierarchy {
        root: 10,
        groups,
        vectors,
    }
}

fn key(model: &mut HierarchyExplorer, key: KeyCode) -> bool {
    model.handle_event(Event::Key(KeyEvent::new(key, KeyModifiers::NONE)))
}

fn screen(model: &mut HierarchyExplorer, width: u16, height: u16) -> String {
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

#[test]
fn showing_parent_preserves_nested_expansion_and_parent_only_masks() {
    let mut model = HierarchyExplorer::new(fixture(), Some(11)).unwrap();
    let initial = screen(&mut model, 100, 40);
    assert!(initial.contains("Showing branch 11"));
    assert!(initial.contains("⟦Parent-only meaning⟧"));
    assert!(!initial.contains("⟦Beach⟧"));
    key(&mut model, KeyCode::Down); // parent-only mask
    key(&mut model, KeyCode::Down); // child 13
    key(&mut model, KeyCode::Right);
    assert!(screen(&mut model, 100, 40).contains("⟦Beach⟧"));
    key(&mut model, KeyCode::Char('u'));
    let parent = screen(&mut model, 100, 40);
    assert!(parent.contains("Showing branch 10"));
    assert!(parent.contains("⟦Root-only meaning⟧"));
    assert!(parent.contains("⟦Beach⟧"));
    assert!(parent.contains("▾ 11"));
    assert!(parent.contains("▾ 13"));
    assert!(parent.contains("▸ 12"));
    // Upward navigation kept selection on 13 as well as expansion state.
    key(&mut model, KeyCode::Left);
    assert!(!screen(&mut model, 100, 40).contains("⟦Beach⟧"));
    key(&mut model, KeyCode::Right);
    assert!(screen(&mut model, 100, 40).contains("⟦Beach⟧"));
}

#[test]
fn original_note_is_opened_with_exact_inline_mask_and_returns_to_tree() {
    let mut model = HierarchyExplorer::new(fixture(), Some(11)).unwrap();
    screen(&mut model, 80, 24);
    key(&mut model, KeyCode::Down);
    key(&mut model, KeyCode::Enter);
    let note = screen(&mut model, 80, 24);
    assert!(note.contains("Before ⟦Parent-only meaning⟧ after. Original context."));
    assert!(note.contains("V002"));
    key(&mut model, KeyCode::Esc);
    let tree = screen(&mut model, 80, 24);
    assert!(tree.contains("Showing branch 11"));
    assert!(!tree.contains("Original context."));
    assert!(key(&mut model, KeyCode::Char('q')));
}

#[test]
fn long_masks_and_notes_are_scrollable_without_clipping_their_ends() {
    let mut data = fixture();
    let fragment = format!("{}MASK-END", "long meaningful text ".repeat(150));
    let mask = &mut data.vectors.get_mut(&1).unwrap()[0];
    mask.text = format!("Before {fragment} after NOTE-END");
    mask.byte_spans = vec![(7, 7 + fragment.len())];
    mask.fragments = vec![fragment];
    let mut model = HierarchyExplorer::new(data, Some(11)).unwrap();
    screen(&mut model, 64, 18);
    key(&mut model, KeyCode::Down);
    for _ in 0..30 {
        key(&mut model, KeyCode::PageDown);
        screen(&mut model, 64, 18);
    }
    assert!(screen(&mut model, 64, 18).contains("MASK-END"));
    key(&mut model, KeyCode::Enter);
    key(&mut model, KeyCode::End);
    let note = screen(&mut model, 64, 18);
    assert!(note.contains("NOTE-END"));
    assert!(note.contains("MASK-END"));
}

#[test]
fn help_explains_counts_parent_masks_and_read_only_behavior() {
    let mut model = HierarchyExplorer::new(fixture(), Some(11)).unwrap();
    key(&mut model, KeyCode::Char('?'));
    let help = screen(&mut model, 100, 40);
    assert!(help.contains("distinct source notes"));
    assert!(help.contains("outside its child groups"));
    assert!(help.contains("read-only"));
    key(&mut model, KeyCode::Esc);
    assert!(screen(&mut model, 100, 40).contains("Showing branch 11"));
}

#[test]
fn invalid_start_is_rejected_and_small_terminal_can_still_exit() {
    assert!(HierarchyExplorer::new(fixture(), Some(999)).is_err());
    let mut model = HierarchyExplorer::new(fixture(), Some(11)).unwrap();
    assert!(screen(&mut model, 30, 8).contains("Resize"));
    assert!(key(&mut model, KeyCode::Char('q')));
}

#[test]
fn long_alias_lists_wrap_without_hiding_their_mask() {
    let mut data = fixture();
    let original = data.vectors[&1][0].clone();
    data.vectors.insert(
        1,
        (0..20)
            .map(|i| {
                let mut alias = original.clone();
                alias.id = format!("V{:03}", 100 + i);
                alias.vector_id = format!("alias-{i}");
                alias
            })
            .collect(),
    );
    let mut model = HierarchyExplorer::new(data, Some(11)).unwrap();
    let rendered = screen(&mut model, 60, 24);
    assert!(rendered.contains("⟦Parent-only meaning⟧"), "{rendered}");
    assert!(rendered.contains("V100"));
    assert!(rendered.contains("V119"));
}

#[test]
fn shrinking_terminal_preserves_selection() {
    let mut model = HierarchyExplorer::new(fixture(), Some(11)).unwrap();
    screen(&mut model, 100, 40);
    for code in [
        KeyCode::Down,
        KeyCode::Down,
        KeyCode::Right,
        KeyCode::Down,
        KeyCode::Down,
        KeyCode::Down,
    ] {
        key(&mut model, code);
    }
    screen(&mut model, 100, 40);
    let small = screen(&mut model, 100, 12);
    assert!(small.contains("▶ └─ ▸ 14"), "{small}");
    key(&mut model, KeyCode::Enter);
    key(&mut model, KeyCode::Down);
    assert!(screen(&mut model, 100, 12).contains("⟦Office⟧"));
}

#[test]
fn narrowing_terminal_keeps_deep_group_readable() {
    let mut data = fixture();
    data.groups.clear();
    for id in 10..=40 {
        data.groups.insert(
            id,
            Group {
                id,
                parent: (id > 10).then_some(id - 1),
                children: if id < 40 { vec![id + 1] } else { vec![] },
                vectors: if id == 40 { vec![0] } else { vec![] },
                note_count: 1,
                vector_count: 1,
            },
        );
    }
    let mut model = HierarchyExplorer::new(data, None).unwrap();
    for _ in 0..25 {
        key(&mut model, KeyCode::Right);
        key(&mut model, KeyCode::Right);
    }
    screen(&mut model, 220, 80);
    let small = screen(&mut model, 60, 24);
    assert!(
        small
            .lines()
            .any(|line| line.contains('▶') && line.contains("35 · 1 note")),
        "{small}"
    );
}

#[test]
fn wrapping_preserves_emoji_graphemes_in_the_original_note() {
    let mut data = fixture();
    let mask = &mut data.vectors.get_mut(&1).unwrap()[0];
    mask.text = format!("{}👨‍👩‍👧‍👦 TAIL", "x".repeat(55));
    mask.byte_spans = vec![(0, mask.text.len())];
    mask.fragments = vec![mask.text.clone()];
    let mut model = HierarchyExplorer::new(data, Some(11)).unwrap();
    screen(&mut model, 60, 24);
    key(&mut model, KeyCode::Down);
    key(&mut model, KeyCode::Enter);
    let note = screen(&mut model, 60, 24);
    assert!(note.contains("👨‍👩‍👧‍👦"), "{note}");
    assert!(note.contains("TAIL"));
}
