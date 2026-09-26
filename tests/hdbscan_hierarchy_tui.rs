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
fn group_note_scopes_show_full_posts_and_keep_outside_masks_separate() {
    let mut hierarchy = fixture();
    // A direct mask's post also occurs deeper in a child: D includes it, O does not.
    let mut shared = hierarchy.vectors[&1][0].clone();
    shared.id = "V008".into();
    hierarchy.vectors.insert(6, vec![shared]);
    let mut second = hierarchy.vectors[&0][0].clone();
    second.id = "V009".into();
    let start = second.text.find("Original context").unwrap();
    second.byte_spans = vec![(start, start + "Original context".len())];
    second.fragments = vec!["Original context".into()];
    hierarchy.vectors.insert(7, vec![second]);
    hierarchy
        .groups
        .get_mut(&10)
        .unwrap()
        .vectors
        .extend([6, 7]);
    hierarchy.groups.get_mut(&10).unwrap().vector_count = 8;
    // Two masks of one post use the same complete source text.
    for (point, fragment) in [(2, "Beach"), (3, "Shoreline")] {
        let mask = &mut hierarchy.vectors.get_mut(&point).unwrap()[0];
        mask.text = "Before Beach Shoreline after. Original context.".into();
        let start = mask.text.find(fragment).unwrap();
        mask.byte_spans = vec![(start, start + fragment.len())];
    }
    let mut model = HierarchyExplorer::new_note_navigation(hierarchy, Some(10)).unwrap();
    key(&mut model, KeyCode::Char('o'));
    let outside = screen(&mut model, 120, 30);
    assert!(outside.contains("Notes outside children"), "{outside}");
    assert!(outside.contains("Note 1 of 1"));
    assert!(outside.contains("V001") && outside.contains("Mask 1 of 2"));
    assert!(outside.contains("Before ⟦Root-only meaning⟧ after. Original context."));
    assert!(!outside.contains("⟦Original context⟧"));
    key(&mut model, KeyCode::Char(']'));
    let second = screen(&mut model, 120, 30);
    assert!(second.contains("V009") && second.contains("Mask 2 of 2"));
    assert!(second.contains("Before Root-only meaning after. ⟦Original context⟧."));
    key(&mut model, KeyCode::Char('d'));
    let direct = screen(&mut model, 120, 30);
    assert!(direct.contains("Direct notes") && direct.contains("Note 1 of 2"));
    assert!(direct.contains("⟦Root-only meaning⟧ after. ⟦Original context⟧"));
    key(&mut model, KeyCode::Right);
    assert!(screen(&mut model, 120, 30).contains("Before ⟦Parent-only meaning⟧ after."));
    key(&mut model, KeyCode::Char('n'));
    assert!(screen(&mut model, 120, 30).contains("Note 1 of 5"));
    key(&mut model, KeyCode::Right);
    key(&mut model, KeyCode::Right);
    assert!(screen(&mut model, 120, 30).contains("Before ⟦Beach⟧ ⟦Shoreline⟧ after."));
    key(&mut model, KeyCode::Esc);
    assert!(screen(&mut model, 120, 30).contains("Showing branch 10"));
}

#[test]
fn group_notes_handle_empty_outside_and_leaf_membership() {
    let mut hierarchy = fixture();
    hierarchy.groups.get_mut(&10).unwrap().vectors.clear();
    let mut model = HierarchyExplorer::new(hierarchy.clone(), Some(10)).unwrap();
    key(&mut model, KeyCode::Char('o'));
    let empty = screen(&mut model, 100, 25);
    assert!(empty.contains("No notes outside children."), "{empty}");
    key(&mut model, KeyCode::Right);
    key(&mut model, KeyCode::Char(']'));
    assert!(screen(&mut model, 100, 25).contains("No notes outside children."));
    let mut leaf = HierarchyExplorer::new(hierarchy, Some(12)).unwrap();
    key(&mut leaf, KeyCode::Char('o'));
    let content = screen(&mut leaf, 100, 25);
    assert!(content.contains("Note 1 of 1") && content.contains("Before ⟦Coffee⟧ after."));
}

#[test]
fn outside_notes_exclude_grandchild_posts_and_preserve_alias_ids() {
    let mut hierarchy = fixture();
    let mut shared = hierarchy.vectors[&4][0].clone();
    shared.id = "V010".into();
    hierarchy.vectors.insert(6, vec![shared]);
    hierarchy.groups.get_mut(&10).unwrap().vectors.push(6);
    let mut alias = hierarchy.vectors[&0][0].clone();
    alias.id = "V011".into();
    hierarchy.vectors.get_mut(&0).unwrap().push(alias);
    let mut model = HierarchyExplorer::new_selection(hierarchy.clone(), Some(10)).unwrap();
    key(&mut model, KeyCode::Char('O'));
    let outside = screen(&mut model, 100, 25);
    assert!(outside.contains("Note 1 of 1"), "{outside}");
    assert!(outside.contains("V001, V011") && outside.contains("Mask 1 of 1"));
    key(&mut model, KeyCode::Char('D'));
    assert!(screen(&mut model, 100, 25).contains("Note 1 of 2"));
    key(&mut model, KeyCode::Char('l'));
    assert!(screen(&mut model, 100, 25).contains("Before ⟦Office⟧ after."));
    key(&mut model, KeyCode::Backspace);
    // Raw view puts direct masks before children; selection view does the opposite.
    let mut model = HierarchyExplorer::new(hierarchy, Some(10)).unwrap();
    key(&mut model, KeyCode::Down); // root's own mask, not a group row
    key(&mut model, KeyCode::Char('O'));
    assert!(screen(&mut model, 100, 25).contains("Group 10"));
}

#[test]
fn all_notes_union_overlapping_masks_and_deduplicate_shared_children() {
    let mut hierarchy = fixture();
    // Two routes reach the same child; all-note membership must not be doubled.
    hierarchy.groups.get_mut(&12).unwrap().children.push(14);
    let mut overlap = hierarchy.vectors[&0][0].clone();
    overlap.id = "V012".into();
    overlap.byte_spans = vec![(0, 11)];
    overlap.fragments = vec![overlap.text[..11].into()];
    hierarchy.vectors.insert(6, vec![overlap]);
    hierarchy.groups.get_mut(&10).unwrap().vectors.push(6);
    let mut model = HierarchyExplorer::new(hierarchy, Some(10)).unwrap();
    key(&mut model, KeyCode::Char('N'));
    let all = screen(&mut model, 100, 25);
    assert!(all.contains("Note 1 of 5"), "{all}");
    assert!(all.contains("⟦Before Root-only meaning⟧ after."));
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
fn showing_parent_places_unopened_children_above_expanded_children() {
    let mut model = HierarchyExplorer::new(fixture(), Some(11)).unwrap();
    key(&mut model, KeyCode::Down); // parent-only mask
    key(&mut model, KeyCode::Down); // child 13
    key(&mut model, KeyCode::Right);
    key(&mut model, KeyCode::Char('u'));
    let parent = screen(&mut model, 100, 40);
    assert!(
        parent.find("├─ ▸ 12").unwrap() < parent.find("└─ ▾ 11").unwrap(),
        "{parent}"
    );
    assert!(parent.contains("   ├─ ▾ 13"), "{parent}");
    assert!(parent.contains("⟦Beach⟧"));
    assert!(parent.contains("⟦Parent-only meaning⟧"));
    assert!(parent.contains("10 · 5 notes"));
    // Reordering keeps selection on the previously selected nested child.
    key(&mut model, KeyCode::Left);
    assert!(!screen(&mut model, 100, 40).contains("⟦Beach⟧"));
}

#[test]
fn opening_an_unopened_section_after_showing_parent_keeps_its_position() {
    let mut model = HierarchyExplorer::new(fixture(), Some(11)).unwrap();
    key(&mut model, KeyCode::Char('u'));
    key(&mut model, KeyCode::Up); // unopened sibling 12, now above 11
    key(&mut model, KeyCode::Right);
    let opened = screen(&mut model, 100, 40);
    assert!(
        opened.find("├─ ▾ 12").unwrap() < opened.find("└─ ▾ 11").unwrap(),
        "{opened}"
    );
    assert!(opened.contains("⟦Coffee⟧"));
    key(&mut model, KeyCode::Down);
    key(&mut model, KeyCode::Enter);
    assert!(screen(&mut model, 100, 40).contains("Before ⟦Coffee⟧ after. Original context."));
    key(&mut model, KeyCode::Esc);
    key(&mut model, KeyCode::Left); // containing group 12
    key(&mut model, KeyCode::Left); // collapse 12
    let collapsed = screen(&mut model, 100, 40);
    assert!(
        collapsed.find("├─ ▸ 12").unwrap() < collapsed.find("└─ ▾ 11").unwrap(),
        "{collapsed}"
    );
}

#[test]
fn showing_parent_in_selection_view_preserves_saved_child_order() {
    let mut model = HierarchyExplorer::new_selection(fixture(), Some(11)).unwrap();
    key(&mut model, KeyCode::Char('u'));
    let parent = screen(&mut model, 100, 40);
    assert!(parent.find("▾ 11").unwrap() < parent.find("▸ 12").unwrap());
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

#[test]
fn vim_direction_keys_match_existing_tree_navigation() {
    let mut vim = HierarchyExplorer::new(fixture(), Some(11)).unwrap();
    let mut arrows = HierarchyExplorer::new(fixture(), Some(11)).unwrap();
    for (letter, arrow) in [
        ('j', KeyCode::Down),
        ('j', KeyCode::Down),
        ('l', KeyCode::Right),
        ('j', KeyCode::Down),
        ('h', KeyCode::Left),
        ('h', KeyCode::Left),
        ('l', KeyCode::Right),
        ('k', KeyCode::Up),
    ] {
        key(&mut vim, KeyCode::Char(letter));
        key(&mut arrows, arrow);
        assert_eq!(
            screen(&mut vim, 80, 24),
            screen(&mut arrows, 80, 24),
            "{letter}"
        );
    }
}

#[test]
fn vim_scroll_and_jump_keys_work_in_tree_notes_and_help() {
    let mut data = fixture();
    let mask = &mut data.vectors.get_mut(&1).unwrap()[0];
    mask.text = (0..80)
        .map(|i| format!("Line {i:02}: source text.\n"))
        .collect();
    mask.fragments = vec![mask.text.clone()];
    mask.byte_spans = vec![(0, mask.text.len())];
    for mode in ["tree", "note", "help"] {
        let mut vim = HierarchyExplorer::new(data.clone(), Some(11)).unwrap();
        let mut existing = HierarchyExplorer::new(data.clone(), Some(11)).unwrap();
        for model in [&mut vim, &mut existing] {
            match mode {
                "note" => {
                    key(model, KeyCode::Down);
                    key(model, KeyCode::Enter);
                }
                "help" => {
                    key(model, KeyCode::Char('?'));
                }
                _ => {}
            }
            screen(model, 80, 18);
        }
        for (code, modifiers, old) in [
            (KeyCode::Char('f'), KeyModifiers::CONTROL, KeyCode::PageDown),
            (KeyCode::Char('b'), KeyModifiers::CONTROL, KeyCode::PageUp),
            (KeyCode::Char('j'), KeyModifiers::NONE, KeyCode::Down),
            (KeyCode::Char('k'), KeyModifiers::NONE, KeyCode::Up),
            (KeyCode::Char('G'), KeyModifiers::SHIFT, KeyCode::End),
        ] {
            vim.handle_event(Event::Key(KeyEvent::new(code, modifiers)));
            key(&mut existing, old);
            assert_eq!(
                screen(&mut vim, 80, 18),
                screen(&mut existing, 80, 18),
                "{mode}: {code:?}"
            );
        }
        key(&mut vim, KeyCode::Char('g'));
        key(&mut vim, KeyCode::Char('g'));
        key(&mut existing, KeyCode::Home);
        assert_eq!(
            screen(&mut vim, 80, 18),
            screen(&mut existing, 80, 18),
            "{mode}: gg"
        );
    }
}

#[test]
fn vim_gg_requires_two_consecutive_g_keys_and_ignores_key_releases() {
    let mut model = HierarchyExplorer::new(fixture(), Some(11)).unwrap();
    screen(&mut model, 80, 24);
    key(&mut model, KeyCode::Down);
    let original = screen(&mut model, 80, 24);
    key(&mut model, KeyCode::Char('g'));
    assert_eq!(screen(&mut model, 80, 24), original);
    key(&mut model, KeyCode::Char('x')); // cancels the unfinished command
    key(&mut model, KeyCode::Char('g'));
    assert_eq!(screen(&mut model, 80, 24), original);
    let mut release = KeyEvent::new(KeyCode::Char('g'), KeyModifiers::NONE);
    release.kind = crossterm::event::KeyEventKind::Release;
    model.handle_event(Event::Key(release));
    key(&mut model, KeyCode::Char('g'));
    let top = screen(&mut model, 80, 24);
    assert!(top.contains("▶ ▾ 11"), "{top}");
}

#[test]
fn vim_bindings_are_visible_in_the_key_guide() {
    let mut model = HierarchyExplorer::new(fixture(), Some(11)).unwrap();
    let tree = screen(&mut model, 60, 24);
    assert!(tree.contains("j/k"));
    assert!(tree.contains("h/l"));
    key(&mut model, KeyCode::Char('?'));
    let help = screen(&mut model, 100, 50);
    for shortcut in ["h/j/k/l", "gg", "Ctrl-F/B", "Ctrl-U/D"] {
        assert!(help.contains(shortcut), "missing {shortcut}: {help}");
    }
}

#[test]
fn vim_g_selects_the_last_visible_item_even_when_the_tree_fits() {
    let mut model = HierarchyExplorer::new(fixture(), Some(11)).unwrap();
    screen(&mut model, 80, 24);
    key(&mut model, KeyCode::Char('G'));
    let bottom = screen(&mut model, 80, 24);
    assert!(bottom.contains("▶ └─ ▸ 14"), "{bottom}");
    key(&mut model, KeyCode::Enter);
    key(&mut model, KeyCode::Char('G'));
    let expanded = screen(&mut model, 80, 24);
    assert!(
        expanded
            .lines()
            .any(|line| line.contains('▶') && line.contains("⟦Office⟧")),
        "{expanded}"
    );
}

#[test]
fn vim_g_keeps_a_deep_last_item_readable() {
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
    for _ in 0..60 {
        key(&mut model, KeyCode::Char('l'));
    }
    key(&mut model, KeyCode::Home);
    screen(&mut model, 60, 24);
    key(&mut model, KeyCode::Char('G'));
    let bottom = screen(&mut model, 60, 24);
    assert!(
        bottom
            .lines()
            .any(|line| line.contains('▶') && line.contains("V001")),
        "{bottom}"
    );
}
