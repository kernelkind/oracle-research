use std::collections::BTreeSet;
use std::fs;
use std::path::{Path, PathBuf};

use crossterm::event::{Event, KeyCode, KeyEvent, KeyModifiers};
use oracle_mvp::hdbscan_hierarchy::Hierarchy;
use oracle_mvp::manual_note_hierarchy_tui::ManualNoteExplorer;
use oracle_mvp::titled_merge_hierarchy::TitledMergeHierarchy;
use ratatui::Terminal;
use ratatui::backend::TestBackend;
use serde_json::{Value, json};
use sha2::{Digest, Sha256};

struct Fixture {
    directory: tempfile::TempDir,
    inputs: [PathBuf; 3],
    titles: Value,
    saved: Hierarchy,
}

impl Fixture {
    fn new() -> Self {
        let root = Path::new(env!("CARGO_MANIFEST_DIR")).join("sse_multivector");
        let inputs = [
            root.join("merge-rule-exploration-v1/M06.json"),
            root.join("real-note-fine-segmentation-v1/vectors/vector-map.json"),
            root.join("real-note-fine-segmentation-v1/reviewed-input.json"),
        ];
        let saved =
            Hierarchy::load_merge_history_with_min_notes(&inputs[0], &inputs[1], &inputs[2], 5)
                .unwrap();
        let hashes = ["merge_history", "vector_map", "source_notes"]
            .into_iter()
            .zip(&inputs)
            .map(|(name, path)| {
                (
                    name,
                    format!("{:x}", Sha256::digest(fs::read(path).unwrap())),
                )
            })
            .collect::<std::collections::BTreeMap<_, _>>();
        let titles = json!({
            "schema_version": 1, "run_id": "M06", "min_notes": 5,
            "input_sha256": hashes,
            "titles": saved.groups.keys().map(|id| json!({
                "group_id": id,
                "label": if *id == 1605 { "Coffee" } else { "Mixed subjects" },
                "analysis": format!("Analysis marker for {id}; not original note text.")
            })).collect::<Vec<_>>()
        });
        Self {
            directory: tempfile::tempdir().unwrap(),
            inputs,
            titles,
            saved,
        }
    }

    fn load(&self) -> Result<TitledMergeHierarchy, Box<dyn std::error::Error>> {
        let titles = self.directory.path().join("titles.json");
        fs::write(&titles, serde_json::to_vec(&self.titles).unwrap()).unwrap();
        TitledMergeHierarchy::load(
            &self.inputs[0],
            &self.inputs[1],
            &self.inputs[2],
            &titles,
            5,
        )
    }
}

#[test]
fn every_original_group_child_note_and_alias_membership_is_preserved() {
    let fixture = Fixture::new();
    let titled = fixture.load().unwrap();
    let h = &titled.hierarchy;
    assert_eq!(h.root_node_id, fixture.saved.root.to_string());
    assert_eq!(h.nodes.len(), fixture.saved.groups.len());
    let vectors: Value = serde_json::from_slice(&fs::read(&fixture.inputs[1]).unwrap()).unwrap();
    let note_short_ids = vectors["vectors"]
        .as_array()
        .unwrap()
        .iter()
        .map(|v| {
            (
                v["note_id"].as_str().unwrap(),
                v["note_short_id"].as_str().unwrap(),
            )
        })
        .collect::<std::collections::BTreeMap<_, _>>();
    for (&id, group) in &fixture.saved.groups {
        let category = &h.nodes[&id.to_string()];
        assert_eq!(
            category.children,
            group
                .children
                .iter()
                .map(usize::to_string)
                .collect::<Vec<_>>()
        );
        let mut expected = BTreeSet::new();
        let mut pending = vec![id];
        while let Some(group) = pending.pop() {
            let group = &fixture.saved.groups[&group];
            pending.extend(&group.children);
            for point in &group.vectors {
                for mask in &fixture.saved.vectors[point] {
                    let short = note_short_ids[mask.note_id.as_str()];
                    expected.insert(short.to_owned());
                    assert_eq!(h.notes[short].note_id, mask.note_id);
                    assert_eq!(h.notes[short].content, mask.text);
                }
            }
        }
        assert_eq!(
            h.note_ids(&id.to_string()),
            expected.into_iter().collect::<Vec<_>>(),
            "group {id}"
        );
        assert_eq!(h.note_ids(&id.to_string()).len(), group.note_count);
    }
    assert_eq!(h.note_ids("1830").len(), 100);
    assert_eq!(h.note_ids("1605").len(), 19);
}

#[test]
fn titles_must_cover_exactly_the_frozen_projection_with_matching_input_hashes() {
    let mut fixture = Fixture::new();
    let original = fixture.titles.clone();
    for name in ["merge_history", "vector_map", "source_notes"] {
        fixture.titles["input_sha256"][name] = json!("bad");
        let error = fixture.load().err().unwrap().to_string();
        assert!(
            error.contains(&format!("{name} SHA-256 mismatch")),
            "{error}"
        );
        fixture.titles = original.clone();
    }
    fixture.titles["titles"].as_array_mut().unwrap().pop();
    assert!(
        fixture
            .load()
            .err()
            .unwrap()
            .to_string()
            .contains("missing")
    );
    fixture.titles = original.clone();
    fixture.titles["titles"]
        .as_array_mut()
        .unwrap()
        .push(json!({"group_id": 951,"label":"Not displayed"}));
    assert!(
        fixture
            .load()
            .err()
            .unwrap()
            .to_string()
            .contains("extra [951]")
    );
    fixture.titles = original.clone();
    let duplicate = fixture.titles["titles"][0].clone();
    fixture.titles["titles"]
        .as_array_mut()
        .unwrap()
        .push(duplicate);
    assert!(fixture.load().is_err());
    fixture.titles = original.clone();
    fixture.titles["titles"][0]["label"] = json!("  ");
    assert!(fixture.load().is_err());
    fixture.titles = original.clone();
    fixture.titles["run_id"] = json!("M07");
    assert!(fixture.load().err().unwrap().to_string().contains("run ID"));
    fixture.titles = original;
    fixture.titles["min_notes"] = json!(2);
    assert!(
        fixture
            .load()
            .err()
            .unwrap()
            .to_string()
            .contains("minimum note count")
    );
}

#[test]
fn inconsistent_note_short_ids_are_rejected_even_with_matching_hashes() {
    let mut fixture = Fixture::new();
    let mut vectors: Value =
        serde_json::from_slice(&fs::read(&fixture.inputs[1]).unwrap()).unwrap();
    let first_note = vectors["vectors"][0]["note_id"].clone();
    let second = vectors["vectors"]
        .as_array_mut()
        .unwrap()
        .iter_mut()
        .skip(1)
        .find(|v| v["note_id"] == first_note)
        .unwrap();
    second["note_short_id"] = json!("N999");
    let path = fixture.directory.path().join("vectors.json");
    fs::write(&path, serde_json::to_vec(&vectors).unwrap()).unwrap();
    fixture.titles["input_sha256"]["vector_map"] =
        json!(format!("{:x}", Sha256::digest(fs::read(&path).unwrap())));
    fixture.inputs[1] = path;
    assert!(
        fixture
            .load()
            .err()
            .unwrap()
            .to_string()
            .contains("conflicting source note short IDs")
    );
}

#[test]
fn start_at_keeps_membership_and_rejects_hidden_or_unknown_groups() {
    let mut titled = Fixture::new().load().unwrap();
    let notes = titled.hierarchy.note_ids("1605");
    titled.start_at(1605).unwrap();
    assert_eq!(titled.hierarchy.root_node_id, "1830");
    assert_eq!(titled.hierarchy.note_ids("1605"), notes);
    assert!(titled.start_at(951).is_err());
    assert!(titled.start_at(9999).is_err());
    assert_eq!(titled.hierarchy.root_node_id, "1830");
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

fn key(model: &mut ManualNoteExplorer, code: KeyCode) {
    assert!(!model.handle_event(Event::Key(KeyEvent::new(code, KeyModifiers::NONE))));
}

#[test]
fn saved_group_menu_keeps_nesting_ids_and_analysis_outside_original_notes() {
    let mut titled = Fixture::new().load().unwrap();
    titled.start_at(1605).unwrap();
    let mut model = ManualNoteExplorer::from_merge(titled);
    let initial = screen(&mut model);
    for text in [
        "M06/1605 · Coffee",
        "19 notes",
        "M06/1234",
        "provisional titles",
        "minimum 5 notes",
    ] {
        assert!(initial.contains(text), "Missing {text}: {initial}");
    }
    assert!(!initial.contains("Manual hierarchy"));
    assert!(!initial.contains("Analysis marker"));
    key(&mut model, KeyCode::Char('l'));
    let child = screen(&mut model);
    assert!(child.contains("Parent: M06/1605"), "{child}");
    assert!(child.contains("M06/1234 · Mixed subjects"), "{child}");
    key(&mut model, KeyCode::Char('?'));
    let analysis = screen(&mut model);
    assert!(analysis.contains("Analysis marker for 1234"), "{analysis}");
    key(&mut model, KeyCode::Esc);
    key(&mut model, KeyCode::Char('h'));
    assert!(screen(&mut model).contains("M06/1605 · Coffee"));
    key(&mut model, KeyCode::Char('j'));
    key(&mut model, KeyCode::Enter);
    let first = screen(&mut model);
    assert!(first.contains("N004 · Note 1 of 19"), "{first}");
    assert!(!first.contains("Analysis marker"));
    for _ in 0..13 {
        key(&mut model, KeyCode::Char('l'));
    }
    let coffee = screen(&mut model);
    assert!(coffee.contains("N060 · Note 14 of 19"), "{coffee}");
    assert!(
        coffee.contains("Made my coffee with raw cream and a raw egg yolk today #coffeechain"),
        "{coffee}"
    );
    assert!(coffee.contains("provisional titles"), "{coffee}");
    key(&mut model, KeyCode::Backspace);
    assert!(screen(&mut model).contains("View all 19 notes"));
}

#[test]
fn starting_inside_a_group_keeps_the_complete_tree_and_named_parent_navigation() {
    let fixture = Fixture::new();
    let mut titled = fixture.load().unwrap();
    let root_children = titled.hierarchy.nodes["1830"].children.clone();
    titled.start_at(1605).unwrap();
    assert_eq!(titled.hierarchy.root_node_id, "1830");
    assert_eq!(titled.hierarchy.note_ids("1830").len(), 100);
    assert_eq!(titled.hierarchy.nodes["1830"].children, root_children);
    let mut model = ManualNoteExplorer::from_merge(titled);
    let initial = screen(&mut model);
    assert!(initial.contains("M06/1605 · Coffee"), "{initial}");
    assert!(
        initial.contains("Parent: M06/1627 · Mixed subjects"),
        "{initial}"
    );
    key(&mut model, KeyCode::Char('h'));
    let parent = screen(&mut model);
    assert!(parent.contains("M06/1627 · Mixed subjects ·"), "{parent}");
    key(&mut model, KeyCode::Enter);
    assert!(screen(&mut model).contains("M06/1605 · Coffee · 19 notes"));
    let mut ancestor = 1605;
    while let Some(parent) = fixture.saved.groups[&ancestor].parent {
        key(&mut model, KeyCode::Backspace);
        let shown = screen(&mut model);
        assert!(
            shown.contains(&format!("M06/{parent} · Mixed subjects ·")),
            "{shown}"
        );
        ancestor = parent;
    }
    assert_eq!(ancestor, 1830);
    let root = screen(&mut model);
    assert!(root.contains("100 notes"), "{root}");
    assert!(!root.contains("Parent:"), "{root}");
}

#[test]
fn current_group_names_its_immediate_parent_as_well_as_its_id() {
    let fixture = Fixture::new();
    let mut model = ManualNoteExplorer::from_merge(fixture.load().unwrap());
    screen(&mut model);
    key(&mut model, KeyCode::Enter);
    let child = screen(&mut model);
    assert!(
        child.contains("Parent: M06/1830 · Mixed subjects"),
        "{child}"
    );
}
