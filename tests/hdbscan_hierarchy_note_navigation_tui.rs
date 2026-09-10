use std::path::Path;

use crossterm::event::{Event, KeyCode, KeyEvent, KeyModifiers};
use oracle_mvp::hdbscan_hierarchy::Hierarchy;
use oracle_mvp::hdbscan_hierarchy_tui::HierarchyExplorer;
use ratatui::Terminal;
use ratatui::backend::TestBackend;

fn model(start: usize) -> HierarchyExplorer {
    let base = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("sse_multivector/real-note-fine-segmentation-v1");
    let hierarchy = Hierarchy::load_note_navigation(
        &base.join("hdbv3-cross-note-edges-v1/response.json"),
        &base.join("vectors/vector-map.json"),
        &base.join("reviewed-input.json"),
    )
    .unwrap();
    HierarchyExplorer::new_note_navigation(hierarchy, Some(start)).unwrap()
}

fn screen(model: &mut HierarchyExplorer) -> String {
    let mut terminal = Terminal::new(TestBackend::new(120, 55)).unwrap();
    terminal.draw(|frame| model.render(frame)).unwrap();
    let buffer = terminal.backend().buffer();
    (0..55)
        .map(|y| {
            (0..120)
                .map(|x| buffer[(x, y)].symbol())
                .collect::<String>()
        })
        .collect::<Vec<_>>()
        .join("\n")
}

fn key(model: &mut HierarchyExplorer, code: KeyCode) {
    model.handle_event(Event::Key(KeyEvent::new(code, KeyModifiers::NONE)));
}

#[test]
fn smaller_note_set_is_a_nested_choice_with_all_original_masks() {
    let mut model = model(1254);
    let initial = screen(&mut model);
    assert!(initial.contains("Merge-tree note navigation"), "{initial}");
    assert!(!initial.contains("HDBv2"));
    assert!(initial.contains("1254 · 3 notes"), "{initial}");
    assert!(initial.contains("▸ 1204 · 2 notes"), "{initial}");
    assert!(initial.contains("V098"), "{initial}");
    assert!(!initial.contains("V114"), "{initial}");

    key(&mut model, KeyCode::Char('j')); // stock mask
    key(&mut model, KeyCode::Char('j')); // six-mask child
    key(&mut model, KeyCode::Char('l'));
    let expanded = screen(&mut model);
    assert!(expanded.contains("└─ ▾ 1204"), "{expanded}");
    for id in ["V113", "V114", "V115", "V672", "V673", "V674"] {
        assert!(expanded.contains(id), "Missing {id}: {expanded}");
    }
    key(&mut model, KeyCode::Char('f'));
    let focused = screen(&mut model);
    assert!(
        focused.contains("Showing branch 1204 · 2 notes"),
        "{focused}"
    );
    assert!(!focused.contains("V098"), "{focused}");
    key(&mut model, KeyCode::Char('u'));
    let parent = screen(&mut model);
    assert!(parent.contains("Showing branch 1254 · 3 notes"), "{parent}");
    assert!(parent.contains("V114"), "{parent}");
}

#[test]
fn help_explains_merge_ids_and_note_filter_without_false_condensed_claims() {
    let mut model = model(1204);
    key(&mut model, KeyCode::Char('?'));
    let help = screen(&mut model);
    for phrase in [
        "merge-tree IDs",
        "two distinct notes",
        "same notes",
        "not condensed-tree IDs",
    ] {
        assert!(help.contains(phrase), "Missing {phrase}: {help}");
    }
    assert!(!help.contains("no groups are removed"), "{help}");
    key(&mut model, KeyCode::Esc);
    key(&mut model, KeyCode::Char('j'));
    key(&mut model, KeyCode::Enter);
    let note = screen(&mut model);
    assert!(note.contains("Original note"), "{note}");
    assert!(note.contains('⟦') && note.contains('⟧'), "{note}");
    assert!(note.contains("tea") || note.contains("chocolate"), "{note}");
}
