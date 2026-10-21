use std::collections::BTreeMap;

use crossterm::event::{Event, KeyCode, KeyEvent, KeyModifiers};
use oracle_mvp::hdbscan_hierarchy::{Group, Hierarchy, MaskInstance};
use oracle_mvp::hdbscan_hierarchy_tui::HierarchyExplorer;
use ratatui::{Terminal, backend::TestBackend};

fn fixture() -> Hierarchy {
    let groups = [
        (10, None, vec![11, 13], vec![0, 1], 4, 6),
        (11, Some(10), vec![12], vec![2], 2, 3),
        (12, Some(11), vec![], vec![3, 4], 2, 2),
        (13, Some(10), vec![], vec![5], 1, 1),
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
        ("a", "Parent A"),
        ("b", "Parent B"),
        ("c", "Parent C"),
        ("a", "Leaf A"),
        ("c", "Leaf C"),
        ("d", "Leaf D"),
    ]
    .into_iter()
    .enumerate()
    .map(|(point, (note_id, fragment))| {
        let text = format!("Before {fragment} after.");
        (
            point,
            vec![MaskInstance {
                id: format!("V{point}"),
                vector_id: format!("v{point}"),
                note_id: note_id.into(),
                byte_spans: vec![(7, 7 + fragment.len())],
                text,
                fragments: vec![fragment.into()],
            }],
        )
    })
    .collect::<BTreeMap<_, _>>();
    Hierarchy {
        root: 10,
        groups,
        vectors,
    }
}

fn key(model: &mut HierarchyExplorer, code: KeyCode) {
    model.handle_event(Event::Key(KeyEvent::new(code, KeyModifiers::NONE)));
}

fn screen(model: &mut HierarchyExplorer) -> String {
    let mut terminal = Terminal::new(TestBackend::new(120, 40)).unwrap();
    terminal.draw(|f| model.render(f)).unwrap();
    let buffer = terminal.backend().buffer();
    (0..40)
        .map(|y| {
            (0..120)
                .map(|x| buffer[(x, y)].symbol())
                .collect::<String>()
        })
        .collect::<Vec<_>>()
        .join("\n")
}

#[test]
fn raw_parent_masks_are_hidden_by_recursive_note_membership_before_expansion() {
    let mut model = HierarchyExplorer::new(fixture(), Some(10)).unwrap();
    let initial = screen(&mut model);
    assert!(!initial.contains("⟦Parent A⟧"), "{initial}");
    assert!(initial.contains("⟦Parent B⟧"));
    assert!(initial.contains("10 · 4 notes"));
    assert!(initial.contains("▸ 11"));
    assert!(!initial.contains("Leaf A"));
    // Hidden rows must not remain selectable. The first move opens Parent B.
    key(&mut model, KeyCode::Char('j'));
    key(&mut model, KeyCode::Enter);
    assert!(screen(&mut model).contains("Before ⟦Parent B⟧ after."));
    key(&mut model, KeyCode::Esc);
    key(&mut model, KeyCode::Char('j')); // 11
    key(&mut model, KeyCode::Char('l'));
    assert!(!screen(&mut model).contains("⟦Parent C⟧"));
    key(&mut model, KeyCode::Char('j')); // 12
    key(&mut model, KeyCode::Char('l'));
    let expanded = screen(&mut model);
    assert!(expanded.contains("⟦Leaf A⟧"));
    assert!(expanded.contains("⟦Leaf C⟧"));
    assert!(!expanded.contains("⟦Parent A⟧"));
    key(&mut model, KeyCode::Char('h'));
    assert!(!screen(&mut model).contains("⟦Parent A⟧"));
}

#[test]
fn fully_hidden_parent_masks_do_not_leave_an_empty_section() {
    let mut model = HierarchyExplorer::new(fixture(), Some(11)).unwrap();
    let rendered = screen(&mut model);
    assert!(!rendered.contains("⟦Parent C⟧"), "{rendered}");
    assert!(!rendered.contains("Masks outside"));
    assert!(rendered.contains("11 · 2 notes"));
    assert!(rendered.contains("▸ 12"));
}

#[test]
fn cross_note_aliases_are_filtered_individually() {
    let mut data = fixture();
    let mut other = data.vectors[&0][0].clone();
    other.id = "V-other".into();
    other.vector_id = "other".into();
    other.note_id = "other-note".into();
    data.vectors.get_mut(&0).unwrap().push(other);
    data.groups.get_mut(&10).unwrap().note_count = 5;
    let mut model = HierarchyExplorer::new(data, Some(10)).unwrap();
    let rendered = screen(&mut model);
    assert!(rendered.contains("V-other  ⟦Parent A⟧"), "{rendered}");
    assert!(!rendered.contains("V0  ⟦Parent A⟧"));
}

#[test]
fn sibling_membership_does_not_hide_leaf_masks() {
    let mut data = fixture();
    data.vectors.get_mut(&5).unwrap()[0].note_id = "a".into();
    let mut model = HierarchyExplorer::new(data, Some(13)).unwrap();
    assert!(screen(&mut model).contains("⟦Leaf D⟧"));
}

#[test]
fn sibling_membership_does_not_hide_an_internal_groups_direct_mask() {
    let mut data = fixture();
    // Group 11's note c occurs in sibling 13, but not in child 12.
    data.vectors.get_mut(&4).unwrap()[0].note_id = "b".into();
    data.vectors.get_mut(&5).unwrap()[0].note_id = "c".into();
    data.groups.get_mut(&10).unwrap().note_count = 3;
    data.groups.get_mut(&11).unwrap().note_count = 3;
    let mut model = HierarchyExplorer::new(data, Some(11)).unwrap();
    let rendered = screen(&mut model);
    assert!(rendered.contains("⟦Parent C⟧"), "{rendered}");
    assert!(rendered.contains("▸ 12"));
}

#[test]
fn manual_selection_view_keeps_parent_masks_from_repeated_notes() {
    let mut model = HierarchyExplorer::new_selection(fixture(), Some(10)).unwrap();
    let rendered = screen(&mut model);
    assert!(rendered.contains("⟦Parent A⟧"));
    assert!(rendered.contains("⟦Parent B⟧"));
}
