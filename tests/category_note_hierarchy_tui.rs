use std::collections::BTreeMap;

use crossterm::event::{Event, KeyCode, KeyEvent, KeyModifiers};
use oracle_mvp::manual_note_hierarchy::{ManualCategory, ManualNote, ManualNoteHierarchy};
use oracle_mvp::manual_note_hierarchy_tui::ManualNoteExplorer;
use ratatui::Terminal;
use ratatui::backend::TestBackend;

fn hierarchy() -> ManualNoteHierarchy {
    let nodes = [
        ("root", "Subjects", vec!["coffee", "music"], vec!["N003"]),
        ("coffee", "Coffee", vec!["espresso"], vec!["N002"]),
        ("espresso", "Espresso", vec![], vec!["N001", "N002"]),
        ("music", "Music", vec![], vec!["N002"]),
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
                analysis: format!("Description for {label}; not original note text."),
            },
        )
    })
    .collect::<BTreeMap<_, _>>();
    let notes = [
        (
            "N001",
            format!(
                "Original opening.\n{}\nOriginal ending marker.",
                (0..120)
                    .map(|index| format!("Original line {index:03}."))
                    .collect::<Vec<_>>()
                    .join("\n")
            ),
        ),
        ("N002", "Shared original note.".to_owned()),
        ("N003", "Original note directly at root.".to_owned()),
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
        hierarchy_id: "saved-categories".to_owned(),
        root_node_id: "root".to_owned(),
        nodes,
        notes,
    }
}

fn key(model: &mut ManualNoteExplorer, code: KeyCode) -> bool {
    model.handle_event(Event::Key(KeyEvent::new(code, KeyModifiers::NONE)))
}

fn control(model: &mut ManualNoteExplorer, code: char) {
    model.handle_event(Event::Key(KeyEvent::new(
        KeyCode::Char(code),
        KeyModifiers::CONTROL,
    )));
}

fn screen(model: &mut ManualNoteExplorer) -> String {
    let mut terminal = Terminal::new(TestBackend::new(100, 30)).unwrap();
    terminal.draw(|frame| model.render(frame)).unwrap();
    let buffer = terminal.backend().buffer();
    (0..30)
        .map(|y| {
            (0..100)
                .map(|x| buffer[(x, y)].symbol())
                .collect::<String>()
        })
        .collect::<Vec<_>>()
        .join("\n")
}

#[test]
fn long_node_ids_are_hidden_while_browsing_but_available_in_analysis() {
    let mut data = hierarchy();
    let id = format!("merged-{}", "a".repeat(64));
    let title = "Coffee brewing and preparation";
    let mut coffee = data.nodes.remove("coffee").unwrap();
    coffee.node_id = id.clone();
    coffee.label = title.to_owned();
    data.nodes.insert(id.clone(), coffee);
    data.nodes.get_mut("root").unwrap().children[0] = id.clone();
    let mut model = ManualNoteExplorer::categories(data);

    let menu = screen(&mut model);
    assert!(menu.contains(title), "{menu}");
    assert!(!menu.contains("merged-"), "{menu}");
    assert!(!menu.contains("[root]"), "{menu}");
    key(&mut model, KeyCode::Enter);
    let child = screen(&mut model);
    assert!(child.contains(title), "{child}");
    assert!(!child.contains("merged-"), "{child}");
    for action in ['N', 'D', 'O'] {
        key(&mut model, KeyCode::Char(action));
        let notes = screen(&mut model);
        assert!(!notes.contains("merged-"), "{notes}");
        key(&mut model, KeyCode::Esc);
    }
    key(&mut model, KeyCode::Char('?'));
    let analysis = screen(&mut model);
    assert!(analysis.contains(&id), "{analysis}");
    key(&mut model, KeyCode::Esc);
    assert_eq!(screen(&mut model), child);
}

#[test]
fn category_menus_show_only_immediate_children_and_enter_never_opens_notes() {
    let mut model = ManualNoteExplorer::categories(hierarchy());
    let root = screen(&mut model);
    for expected in ["Subjects", "Coffee", "Music", "3 notes", "N Notes"] {
        assert!(root.contains(expected), "missing {expected}: {root}");
    }
    for absent in [
        "Espresso",
        "View all",
        "outside children",
        "Original",
        "Description",
    ] {
        assert!(!root.contains(absent), "unexpected {absent}: {root}");
    }
    key(&mut model, KeyCode::Enter);
    let coffee = screen(&mut model);
    assert!(coffee.contains("Subjects > Coffee"), "{coffee}");
    assert!(coffee.contains("Espresso"), "{coffee}");
    assert!(!coffee.contains("Music"), "{coffee}");
    key(&mut model, KeyCode::Char('l'));
    let leaf = screen(&mut model);
    assert!(leaf.contains("Subjects > Coffee > Espresso"), "{leaf}");
    assert!(leaf.contains("No child categories"), "{leaf}");
    assert!(!leaf.contains("Original"), "{leaf}");
    assert!(!leaf.contains("View all"), "{leaf}");
    key(&mut model, KeyCode::Enter);
    assert_eq!(screen(&mut model), leaf);
    key(&mut model, KeyCode::Char('N'));
    let note = screen(&mut model);
    assert!(note.contains("Original opening."), "{note}");
    assert!(note.contains("Note 1 of 2"), "{note}");
    assert!(!note.contains("Description"), "{note}");
    key(&mut model, KeyCode::Esc);
    assert_eq!(screen(&mut model), leaf);
    key(&mut model, KeyCode::Esc);
    assert_eq!(screen(&mut model), coffee);
    key(&mut model, KeyCode::Char('h'));
    assert_eq!(screen(&mut model), root);
    assert!(!key(&mut model, KeyCode::Esc));
    assert_eq!(screen(&mut model), root);
}

#[test]
fn n_opens_current_level_with_recursive_deduplicated_notes_and_restores_selection() {
    let mut model = ManualNoteExplorer::categories(hierarchy());
    key(&mut model, KeyCode::Char('j'));
    let root_with_music_selected = screen(&mut model);
    key(&mut model, KeyCode::Char('N'));
    for (index, id) in ["N001", "N002", "N003"].into_iter().enumerate() {
        let note = screen(&mut model);
        assert!(note.contains(id), "{note}");
        assert!(note.contains(&format!("Note {} of 3", index + 1)), "{note}");
        assert!(!note.contains("Description"), "{note}");
        key(&mut model, KeyCode::Char('l'));
    }
    let last = screen(&mut model);
    assert!(last.contains("Original note directly at root."), "{last}");
    assert!(last.contains("Note 3 of 3"), "{last}");
    key(&mut model, KeyCode::Esc);
    assert_eq!(screen(&mut model), root_with_music_selected);
    key(&mut model, KeyCode::Enter);
    let music = screen(&mut model);
    assert!(music.contains("Subjects > Music"), "{music}");
    assert!(!music.contains("Shared original note."), "{music}");
    key(&mut model, KeyCode::Char('N'));
    let note = screen(&mut model);
    assert!(note.contains("Shared original note."), "{note}");
    assert!(note.contains("Note 1 of 1"), "{note}");
    key(&mut model, KeyCode::Esc);
    assert_eq!(screen(&mut model), music);
    key(&mut model, KeyCode::Esc);
    assert_eq!(screen(&mut model), root_with_music_selected);
    key(&mut model, KeyCode::Char('k'));
    key(&mut model, KeyCode::Enter);
    key(&mut model, KeyCode::Char('N'));
    assert!(screen(&mut model).contains("Note 1 of 2"));
}

#[test]
fn original_note_box_keeps_full_text_and_vim_scrolling() {
    let mut model = ManualNoteExplorer::categories(hierarchy());
    key(&mut model, KeyCode::Char('N'));
    let first = screen(&mut model);
    assert!(first.contains("Original opening."), "{first}");
    let body = first
        .lines()
        .filter(|line| line.contains('│'))
        .collect::<String>();
    for absent in ["Description", "N001", "Subjects"] {
        assert!(!body.contains(absent), "unexpected {absent}: {body}");
    }
    key(&mut model, KeyCode::Char('j'));
    assert!(!screen(&mut model).contains("Original opening."));
    key(&mut model, KeyCode::Char('k'));
    assert_eq!(screen(&mut model), first);
    control(&mut model, 'd');
    assert!(!screen(&mut model).contains("Original opening."));
    control(&mut model, 'u');
    assert_eq!(screen(&mut model), first);
    key(&mut model, KeyCode::Char('G'));
    assert!(screen(&mut model).contains("Original ending marker."));
    key(&mut model, KeyCode::Char('g'));
    key(&mut model, KeyCode::Char('g'));
    assert_eq!(screen(&mut model), first);
    key(&mut model, KeyCode::Char('l'));
    assert!(screen(&mut model).contains("Shared original note."));
    key(&mut model, KeyCode::Char('h'));
    assert_eq!(screen(&mut model), first);
}

#[test]
fn leaf_root_starts_on_a_category_screen_and_notes_return_to_it() {
    let mut data = hierarchy();
    data.root_node_id = "espresso".to_owned();
    data.nodes.retain(|id, _| id == "espresso");
    data.notes.retain(|id, _| id != "N003");
    let mut model = ManualNoteExplorer::categories(data);
    let initial = screen(&mut model);
    assert!(initial.contains("No child categories"), "{initial}");
    assert!(!initial.contains("Original"), "{initial}");
    key(&mut model, KeyCode::Char('N'));
    assert!(screen(&mut model).contains("Original opening."));
    key(&mut model, KeyCode::Esc);
    assert_eq!(screen(&mut model), initial);
    assert!(key(&mut model, KeyCode::Char('q')));
}

fn compact_screen(model: &mut ManualNoteExplorer) -> String {
    let mut terminal = Terminal::new(TestBackend::new(80, 24)).unwrap();
    terminal.draw(|frame| model.render(frame)).unwrap();
    let buffer = terminal.backend().buffer();
    (0..24)
        .map(|y| (0..80).map(|x| buffer[(x, y)].symbol()).collect::<String>())
        .collect::<Vec<_>>()
        .join("\n")
}

#[test]
fn forty_ancestors_keep_the_current_category_and_original_notes_usable_at_80_columns() {
    let mut data = hierarchy();
    data.hierarchy_id = "GDC09".to_owned();
    data.root_node_id = "0".to_owned();
    data.notes.retain(|id, _| id == "N001");
    data.nodes = (0..=41)
        .map(|level| {
            let node_id = level.to_string();
            let node = ManualCategory {
                node_id: node_id.clone(),
                label: match level {
                    40 => "Current subject".to_owned(),
                    41 => "Leaf subject".to_owned(),
                    _ => format!("Food and drink ancestor {level:02}"),
                },
                children: if level < 41 {
                    vec![(level + 1).to_string()]
                } else {
                    vec![]
                },
                note_ids: if level == 41 {
                    vec!["N001".to_owned()]
                } else {
                    vec![]
                },
                analysis: String::new(),
            };
            (node_id, node)
        })
        .collect();
    let mut model = ManualNoteExplorer::categories(data);
    for _ in 0..40 {
        key(&mut model, KeyCode::Enter);
    }
    let menu = compact_screen(&mut model);
    for expected in ["Current subject", "Leaf subject", "N Notes", "GDC09"] {
        assert!(menu.contains(expected), "missing {expected}: {menu}");
    }
    assert!(
        menu.lines().filter(|line| line.contains('│')).count() >= 12,
        "{menu}"
    );
    key(&mut model, KeyCode::Char('N'));
    let note = compact_screen(&mut model);
    for expected in [
        "Current subject",
        "GDC09",
        "Original opening.",
        "Original line 010.",
    ] {
        assert!(note.contains(expected), "missing {expected}: {note}");
    }
    key(&mut model, KeyCode::Char('G'));
    assert!(compact_screen(&mut model).contains("Original ending marker."));
    key(&mut model, KeyCode::Esc);
    assert_eq!(compact_screen(&mut model), menu);
    key(&mut model, KeyCode::Enter);
    let leaf = compact_screen(&mut model);
    assert!(leaf.contains("Leaf subject"), "{leaf}");
    assert!(leaf.contains("No child categories"), "{leaf}");
    key(&mut model, KeyCode::Esc);
    assert_eq!(compact_screen(&mut model), menu);
}

#[test]
fn category_headers_identify_the_saved_hierarchy_on_menus_notes_and_analysis() {
    let mut model = ManualNoteExplorer::categories(hierarchy());
    let menu = compact_screen(&mut model);
    assert!(menu.contains("saved-categories"), "{menu}");
    key(&mut model, KeyCode::Char('N'));
    let note = compact_screen(&mut model);
    assert!(note.contains("saved-categories"), "{note}");
    assert!(note.contains("Original opening."), "{note}");
    key(&mut model, KeyCode::Char('?'));
    let analysis = compact_screen(&mut model);
    assert!(analysis.contains("saved-categories"), "{analysis}");
}

#[test]
fn d_opens_only_direct_notes_of_current_category_and_restores_selection() {
    let mut model = ManualNoteExplorer::categories(hierarchy());
    key(&mut model, KeyCode::Char('j'));
    let menu = compact_screen(&mut model);
    assert!(menu.contains("D Direct notes"), "{menu}");
    key(&mut model, KeyCode::Char('D'));
    let direct = compact_screen(&mut model);
    for expected in [
        "Direct notes",
        "N003",
        "Note 1 of 1",
        "Original note directly at root.",
    ] {
        assert!(direct.contains(expected), "missing {expected}: {direct}");
    }
    assert!(!direct.contains("Shared original note."), "{direct}");
    assert!(!direct.contains("Original opening."), "{direct}");
    key(&mut model, KeyCode::Esc);
    assert_eq!(compact_screen(&mut model), menu);
    key(&mut model, KeyCode::Char('N'));
    assert!(compact_screen(&mut model).contains("Note 1 of 3"));
}

#[test]
fn direct_notes_include_direct_members_that_also_belong_to_children() {
    let mut model = ManualNoteExplorer::categories(hierarchy());
    key(&mut model, KeyCode::Enter);
    let menu = compact_screen(&mut model);
    key(&mut model, KeyCode::Char('d'));
    let direct = compact_screen(&mut model);
    assert!(direct.contains("Subjects > Coffee"), "{direct}");
    assert!(direct.contains("N002"), "{direct}");
    assert!(direct.contains("Note 1 of 1"), "{direct}");
    assert!(direct.contains("Shared original note."), "{direct}");
    for code in [KeyCode::Char('l'), KeyCode::Char('h')] {
        key(&mut model, code);
        assert_eq!(compact_screen(&mut model), direct);
    }
    key(&mut model, KeyCode::Esc);
    assert_eq!(compact_screen(&mut model), menu);
    key(&mut model, KeyCode::Char('N'));
    let recursive = compact_screen(&mut model);
    assert!(recursive.contains("N001"), "{recursive}");
    assert!(recursive.contains("Note 1 of 2"), "{recursive}");
}

#[test]
fn empty_direct_notes_are_explicit_and_navigation_is_safe() {
    let mut data = hierarchy();
    data.nodes.get_mut("root").unwrap().note_ids.clear();
    let mut model = ManualNoteExplorer::categories(data);
    let menu = compact_screen(&mut model);
    key(&mut model, KeyCode::Char('D'));
    let direct = compact_screen(&mut model);
    assert!(direct.contains("Direct notes"), "{direct}");
    assert!(direct.contains("0 notes"), "{direct}");
    assert!(
        direct.contains("No notes are assigned directly to this category."),
        "{direct}"
    );
    assert!(!direct.contains("Note 1 of 0"), "{direct}");
    for code in [
        KeyCode::Char('h'),
        KeyCode::Char('l'),
        KeyCode::Char('j'),
        KeyCode::Char('G'),
    ] {
        key(&mut model, code);
        assert_eq!(compact_screen(&mut model), direct);
    }
    key(&mut model, KeyCode::Char('?'));
    key(&mut model, KeyCode::Esc);
    assert_eq!(compact_screen(&mut model), direct);
    key(&mut model, KeyCode::Esc);
    assert_eq!(compact_screen(&mut model), menu);
    key(&mut model, KeyCode::Char('N'));
    assert!(compact_screen(&mut model).contains("Note 1 of 2"));
}

#[test]
fn direct_action_respects_analysis_notes_and_control_d_scrolling() {
    let mut model = ManualNoteExplorer::categories(hierarchy());
    key(&mut model, KeyCode::Char('?'));
    let analysis = compact_screen(&mut model);
    key(&mut model, KeyCode::Char('D'));
    assert_eq!(compact_screen(&mut model), analysis);
    key(&mut model, KeyCode::Esc);
    key(&mut model, KeyCode::Enter);
    key(&mut model, KeyCode::Enter);
    let leaf_menu = compact_screen(&mut model);
    key(&mut model, KeyCode::Char('D'));
    let first = compact_screen(&mut model);
    assert!(first.contains("Original opening."), "{first}");
    assert!(first.contains("Direct notes"), "{first}");
    assert!(first.contains("Note 1 of 2"), "{first}");
    key(&mut model, KeyCode::Char('d'));
    assert_eq!(compact_screen(&mut model), first);
    control(&mut model, 'd');
    assert!(!compact_screen(&mut model).contains("Original opening."));
    control(&mut model, 'u');
    assert_eq!(compact_screen(&mut model), first);
    key(&mut model, KeyCode::Esc);
    assert_eq!(compact_screen(&mut model), leaf_menu);
    let mut legacy = ManualNoteExplorer::new(hierarchy());
    let menu = compact_screen(&mut legacy);
    key(&mut legacy, KeyCode::Char('D'));
    assert_eq!(compact_screen(&mut legacy), menu);
}

#[test]
fn o_excludes_notes_in_any_descendant_and_restores_category_selection() {
    let mut data = hierarchy();
    data.nodes.get_mut("root").unwrap().note_ids =
        vec!["N001".into(), "N002".into(), "N003".into()];
    let mut model = ManualNoteExplorer::categories(data);
    key(&mut model, KeyCode::Char('j'));
    let menu = compact_screen(&mut model);
    key(&mut model, KeyCode::Char('O'));
    let outside = compact_screen(&mut model);
    for expected in [
        "Notes outside children",
        "N003",
        "Note 1 of 1",
        "Original note directly at root.",
    ] {
        assert!(outside.contains(expected), "missing {expected}: {outside}");
    }
    assert!(
        !outside.contains("N001"),
        "grandchild note was not excluded: {outside}"
    );
    assert!(
        !outside.contains("N002"),
        "shared child note was not excluded: {outside}"
    );
    key(&mut model, KeyCode::Esc);
    assert_eq!(compact_screen(&mut model), menu);
    assert!(menu.contains("O Notes not in children"), "{menu}");
    key(&mut model, KeyCode::Char('D'));
    assert!(compact_screen(&mut model).contains("Note 1 of 3"));
}

#[test]
fn o_handles_empty_categories_leaves_and_analysis_without_changing_other_views() {
    let mut model = ManualNoteExplorer::categories(hierarchy());
    key(&mut model, KeyCode::Enter);
    let menu = compact_screen(&mut model);
    key(&mut model, KeyCode::Char('o'));
    let empty = compact_screen(&mut model);
    assert!(empty.contains("0 notes"), "{empty}");
    assert!(empty.contains("No notes outside children."), "{empty}");
    for code in [
        KeyCode::Char('h'),
        KeyCode::Char('l'),
        KeyCode::Char('G'),
        KeyCode::Char('o'),
    ] {
        key(&mut model, code);
        assert_eq!(compact_screen(&mut model), empty);
    }
    key(&mut model, KeyCode::Esc);
    assert_eq!(compact_screen(&mut model), menu);
    key(&mut model, KeyCode::Char('?'));
    let analysis = compact_screen(&mut model);
    key(&mut model, KeyCode::Char('O'));
    assert_eq!(compact_screen(&mut model), analysis);
    key(&mut model, KeyCode::Esc);
    key(&mut model, KeyCode::Enter);
    key(&mut model, KeyCode::Char('O'));
    let leaf = compact_screen(&mut model);
    assert!(leaf.contains("Note 1 of 2"), "{leaf}");
    assert!(leaf.contains("Original opening."), "{leaf}");
}
