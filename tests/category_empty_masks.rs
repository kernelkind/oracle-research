use crossterm::event::{Event, KeyCode, KeyEvent, KeyModifiers};
use oracle_mvp::manual_note_hierarchy::ManualNoteHierarchy;
use oracle_mvp::manual_note_hierarchy_tui::ManualNoteExplorer;
use ratatui::{Terminal, backend::TestBackend};
use serde_json::json;
use sha2::{Digest, Sha256};
use std::fs;

#[test]
fn empty_subject_mask_keeps_full_source_visible_without_invented_highlights() {
    let directory = tempfile::tempdir().unwrap();
    let source = directory.path().join("posts.json");
    let spec = directory.path().join("categories.json");
    let bytes = serde_json::to_vec(&json!({"notes": [{"note_id": "post", "text": "Original post without selected fragments."}]})).unwrap();
    fs::write(&source, &bytes).unwrap();
    fs::write(&spec, serde_json::to_vec(&json!({
        "schema_version": 2,
        "hierarchy_id": "Empty-mask SP subject",
        "source_sha256": format!("{:x}", Sha256::digest(&bytes)),
        "root_node_id": "root",
        "notes": [{"note_id": "post", "note_short_id": "N001"}],
        "nodes": [
            {"node_id": "root", "label": "Subjects", "children": ["empty"], "note_ids": []},
            {"node_id": "empty", "label": "Unmasked subject", "children": [], "note_ids": ["N001"]}
        ],
        "note_masks": {"root": {"N001": []}, "empty": {"N001": []}},
        "mask_instances": {"root": {"N001": []}, "empty": {"N001": []}}
    })).unwrap()).unwrap();
    let (hierarchy, masks) = ManualNoteHierarchy::load_with_masks(&spec, &source).unwrap();
    assert_eq!(hierarchy.note_ids("empty"), ["N001"]);
    assert!(masks.as_ref().unwrap().spans("empty", "N001").is_empty());
    let mut model = ManualNoteExplorer::categories_with_masks(hierarchy, masks, false);
    model.handle_event(Event::Key(KeyEvent::new(
        KeyCode::Enter,
        KeyModifiers::NONE,
    )));
    let mut terminal = Terminal::new(TestBackend::new(100, 25)).unwrap();
    for mode in ['N', 'D', 'O'] {
        model.handle_event(Event::Key(KeyEvent::new(
            KeyCode::Char(mode),
            KeyModifiers::NONE,
        )));
        terminal.draw(|frame| model.render(frame)).unwrap();
        let buffer = terminal.backend().buffer();
        let screen = (0..25)
            .map(|y| {
                (0..100)
                    .map(|x| buffer[(x, y)].symbol())
                    .collect::<String>()
            })
            .collect::<Vec<_>>()
            .join("\n");
        assert!(
            screen.contains("Original post without selected fragments."),
            "{screen}"
        );
        assert!(screen.contains("No selected fragments"), "{screen}");
        assert!(!screen.contains("Individual masks unavailable"), "{screen}");
        assert!(!screen.contains('⟦'), "{screen}");
    }
}
