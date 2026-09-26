use std::fs;

use crossterm::event::{Event, KeyCode, KeyEvent, KeyModifiers};
use oracle_mvp::manual_note_hierarchy::ManualNoteHierarchy;
use oracle_mvp::manual_note_hierarchy_tui::ManualNoteExplorer;
use ratatui::Terminal;
use ratatui::backend::TestBackend;
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use tempfile::TempDir;

const TEXT: &str = "café coffee with milk; tea later. coffee again.";

fn range(phrase: &str) -> Value {
    let start = TEXT.find(phrase).unwrap();
    json!([start, start + phrase.len()])
}

fn fixture() -> (TempDir, Value) {
    let dir = TempDir::new().unwrap();
    let source = serde_json::to_vec(&json!({
        "notes": [{"note_id": "real", "text": TEXT}]
    }))
    .unwrap();
    fs::write(dir.path().join("notes.json"), &source).unwrap();
    let coffee = vec![
        range("coffee with"),
        range("with milk"),
        range("coffee with"),
    ];
    let tea = vec![range("tea")];
    let all = [coffee.clone(), tea.clone(), vec![range("café")]].concat();
    let spec = json!({
        "schema_version": 1, "hierarchy_id": "mask-categories",
        "source_sha256": format!("{:x}", Sha256::digest(source)),
        "root_node_id": "root",
        "notes": [{"note_id": "real", "note_short_id": "N001"}],
        "nodes": [
            {"node_id": "root", "label": "All notes", "children": ["coffee", "tea"], "note_ids": []},
            {"node_id": "coffee", "label": "Coffee", "children": ["milk"], "note_ids": []},
            {"node_id": "milk", "label": "Coffee with milk", "children": [], "note_ids": ["N001"]},
            {"node_id": "tea", "label": "Tea", "children": [], "note_ids": ["N001"]}
        ],
        "note_masks": {
            "root": {"N001": all},
            "coffee": {"N001": coffee.clone()},
            "milk": {"N001": coffee},
            "tea": {"N001": tea}
        }
    });
    (dir, spec)
}

fn save(dir: &TempDir, spec: &Value) {
    fs::write(
        dir.path().join("categories.json"),
        serde_json::to_vec(spec).unwrap(),
    )
    .unwrap();
}

#[test]
fn category_loader_accepts_source_bound_masks_without_changing_original_notes() {
    let (dir, spec) = fixture();
    save(&dir, &spec);
    let h = ManualNoteHierarchy::load(
        &dir.path().join("categories.json"),
        &dir.path().join("notes.json"),
    )
    .expect("category masks must load alongside the unchanged original text");
    assert_eq!(h.notes["N001"].content, TEXT);
    assert_eq!(h.note_ids("root"), vec!["N001"]);
}

fn explorer(dir: &TempDir, spec: &Value) -> ManualNoteExplorer {
    save(dir, spec);
    let (h, masks) = ManualNoteHierarchy::load_with_masks(
        &dir.path().join("categories.json"),
        &dir.path().join("notes.json"),
    )
    .unwrap();
    ManualNoteExplorer::categories_with_masks(h, masks, false)
}

fn key(model: &mut ManualNoteExplorer, key: KeyCode) {
    assert!(!model.handle_event(Event::Key(KeyEvent::new(key, KeyModifiers::NONE))));
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
fn direct_notes_keep_category_highlights_and_complete_original_text() {
    let (dir, mut spec) = fixture();
    spec["nodes"][1]["note_ids"] = json!(["N001"]);
    let mut model = explorer(&dir, &spec);
    key(&mut model, KeyCode::Enter);
    key(&mut model, KeyCode::Char('D'));
    let direct = screen(&mut model);
    assert!(direct.contains("Direct notes"), "{direct}");
    assert!(direct.contains("N001"), "{direct}");
    assert!(
        direct.contains("café ⟦coffee with milk⟧; tea later. coffee again."),
        "{direct}"
    );
    assert!(!direct.contains("⟦tea⟧"), "{direct}");
}

#[test]
fn outside_children_keeps_full_notes_with_only_current_category_masks() {
    let (dir, mut spec) = fixture();
    spec["nodes"][1]["note_ids"] = json!(["N001"]);
    spec["nodes"][1]["children"] = json!([]);
    spec["nodes"].as_array_mut().unwrap().remove(2);
    spec["note_masks"].as_object_mut().unwrap().remove("milk");
    let mut model = explorer(&dir, &spec);
    key(&mut model, KeyCode::Enter);
    key(&mut model, KeyCode::Char('O'));
    let outside = screen(&mut model);
    assert!(outside.contains("Notes outside children"), "{outside}");
    assert!(outside.contains("Note 1 of 1"), "{outside}");
    assert!(
        outside.contains("café ⟦coffee with milk⟧; tea later. coffee again."),
        "{outside}"
    );
    assert!(!outside.contains("⟦tea⟧"), "{outside}");
}

#[test]
fn note_view_overlays_all_category_masks_at_once_and_keeps_source_occurrences() {
    let (dir, spec) = fixture();
    let mut model = explorer(&dir, &spec);
    key(&mut model, KeyCode::Char('N'));
    let root = screen(&mut model);
    assert!(
        root.contains("⟦café⟧ ⟦coffee with milk⟧; ⟦tea⟧ later. coffee again."),
        "{root}"
    );
    assert!(!root.contains("Mask 1 of"), "{root}");
    key(&mut model, KeyCode::Esc);
    key(&mut model, KeyCode::Enter);
    key(&mut model, KeyCode::Char('N'));
    let coffee = screen(&mut model);
    assert!(
        coffee.contains("café ⟦coffee with milk⟧; tea later. coffee again."),
        "{coffee}"
    );
    assert!(
        !coffee.contains("⟦tea⟧") && !coffee.contains("⟦café⟧"),
        "{coffee}"
    );
    key(&mut model, KeyCode::Esc);
    key(&mut model, KeyCode::Esc);
    key(&mut model, KeyCode::Down);
    key(&mut model, KeyCode::Enter);
    key(&mut model, KeyCode::Char('N'));
    let tea = screen(&mut model);
    assert!(
        tea.contains("café coffee with milk; ⟦tea⟧ later. coffee again."),
        "{tea}"
    );
    assert!(tea.contains("Note 1 of 1"), "{tea}");
}

#[test]
fn loader_unions_overlap_duplicates_and_adjacent_ranges_without_filling_gaps() {
    let (dir, mut spec) = fixture();
    spec["note_masks"]["root"]["N001"] = json!([
        range("café"),
        [5, 6],
        range("coffee with"),
        range("with milk"),
        range("tea"),
        range("coffee with")
    ]);
    save(&dir, &spec);
    let (_, masks) = ManualNoteHierarchy::load_with_masks(
        &dir.path().join("categories.json"),
        &dir.path().join("notes.json"),
    )
    .unwrap();
    let end = TEXT.find(';').unwrap();
    let tea = TEXT.find("tea").unwrap();
    assert_eq!(
        masks.unwrap().spans("root", "N001"),
        &[(0, end), (tea, tea + 3)]
    );
}

#[test]
fn masks_reject_bad_bytes_wrong_memberships_and_missing_descendant_evidence() {
    let (dir, original) = fixture();
    for case in 0..7 {
        let mut spec = original.clone();
        match case {
            0 => {
                spec["note_masks"]["tea"]["N001"] = json!([[3, 4]]);
            }
            1 => {
                spec["note_masks"]["tea"]["N001"] = json!([[0, 9999]]);
            }
            2 => {
                spec["note_masks"]["tea"]["N001"] = json!([[3, 3]]);
            }
            3 => {
                spec["note_masks"].as_object_mut().unwrap().remove("tea");
            }
            4 => {
                spec["note_masks"]["tea"]["N002"] = json!([[0, 1]]);
            }
            5 => {
                spec["note_masks"]["coffee"]["N001"] = json!([range("coffee with")]);
            }
            6 => {
                spec["note_masks"]["tea"]["N001"] = json!([]);
            }
            _ => unreachable!(),
        }
        save(&dir, &spec);
        let result = ManualNoteHierarchy::load(
            &dir.path().join("categories.json"),
            &dir.path().join("notes.json"),
        );
        assert!(result.is_err(), "accepted invalid mask case {case}");
    }
}

#[test]
fn category_files_without_masks_keep_the_original_note_view() {
    let (dir, mut spec) = fixture();
    spec.as_object_mut().unwrap().remove("note_masks");
    let mut model = explorer(&dir, &spec);
    key(&mut model, KeyCode::Char('N'));
    let output = screen(&mut model);
    assert!(output.contains(TEXT), "{output}");
    assert!(!output.contains('⟦'), "{output}");
}

fn individual_fixture() -> (TempDir, Value) {
    let (dir, mut spec) = fixture();
    spec["nodes"][1]["note_ids"] = json!(["N001"]);
    spec["nodes"][1]["children"] = json!([]);
    spec["nodes"].as_array_mut().unwrap().remove(2);
    spec["note_masks"].as_object_mut().unwrap().remove("milk");
    let coffee = json!([
        {"ids": ["V001"], "byte_spans": [range("coffee with")]},
        {"ids": ["V002", "V009"], "byte_spans": [range("with milk")]}
    ]);
    let tea = json!({"ids": ["V003"], "byte_spans": [range("tea")]});
    let mut all = coffee.as_array().unwrap().clone();
    all.push(tea.clone());
    all.push(json!({"ids": ["V004"], "byte_spans": [range("café")]}));
    spec["mask_instances"] = json!({
        "root": {"N001": all},
        "coffee": {"N001": coffee},
        "tea": {"N001": [tea]}
    });
    (dir, spec)
}

#[test]
fn o_shows_one_original_mask_and_its_ids_without_changing_n_or_d() {
    let (dir, spec) = individual_fixture();
    let mut model = explorer(&dir, &spec);
    let parent = screen(&mut model);
    key(&mut model, KeyCode::Enter);
    let menu = screen(&mut model);
    key(&mut model, KeyCode::Char('O'));
    let first = screen(&mut model);
    for expected in [
        "N001",
        "V001",
        "Mask 1 of 2",
        "café ⟦coffee with⟧ milk; tea later. coffee again.",
    ] {
        assert!(first.contains(expected), "missing {expected}: {first}");
    }
    assert!(!first.contains("⟦coffee with milk⟧"), "{first}");
    key(&mut model, KeyCode::Char(']'));
    let second = screen(&mut model);
    for expected in [
        "V002",
        "V009",
        "Mask 2 of 2",
        "café coffee ⟦with milk⟧; tea later. coffee again.",
    ] {
        assert!(second.contains(expected), "missing {expected}: {second}");
    }
    key(&mut model, KeyCode::Char(']'));
    assert_eq!(screen(&mut model), second);
    key(&mut model, KeyCode::Char('['));
    assert_eq!(screen(&mut model), first);
    key(&mut model, KeyCode::Char('['));
    assert_eq!(screen(&mut model), first);
    key(&mut model, KeyCode::Esc);
    assert_eq!(screen(&mut model), parent);
    for action in ['N', 'D'] {
        key(&mut model, KeyCode::Enter);
        assert_eq!(screen(&mut model), menu);
        key(&mut model, KeyCode::Char(action));
        let combined = screen(&mut model);
        assert!(
            combined.contains("café ⟦coffee with milk⟧; tea later. coffee again."),
            "{combined}"
        );
        assert!(!combined.contains("Mask 1 of"), "{combined}");
        key(&mut model, KeyCode::Char(']'));
        assert_eq!(screen(&mut model), combined);
        key(&mut model, KeyCode::Esc);
    }
}

#[test]
fn individual_masks_reject_incomplete_inconsistent_or_invalid_provenance() {
    let (dir, original) = individual_fixture();
    for case in 0..9 {
        let mut spec = original.clone();
        match case {
            0 => {
                spec["mask_instances"]
                    .as_object_mut()
                    .unwrap()
                    .remove("coffee");
            }
            1 => {
                spec["mask_instances"]["coffee"]["N001"][0]["ids"] = json!([]);
            }
            2 => {
                spec["mask_instances"]["coffee"]["N001"][0]["byte_spans"] = json!([[3, 4]]);
            }
            3 => {
                spec["mask_instances"]["coffee"]["N001"]
                    .as_array_mut()
                    .unwrap()
                    .pop();
            }
            4 => {
                spec["mask_instances"]["coffee"]["N001"][0]["ids"] = json!(["V003"]);
            }
            5 => {
                spec["mask_instances"]["coffee"]["N001"][0]["byte_spans"] = json!([]);
            }
            6 => {
                spec["mask_instances"]["coffee"]["N002"] =
                    spec["mask_instances"]["coffee"]["N001"].clone();
            }
            7 => {
                spec.as_object_mut().unwrap().remove("note_masks");
            }
            8 => {
                spec["mask_instances"]["coffee"]["N001"][0]["ids"] = json!([" "]);
            }
            _ => unreachable!(),
        }
        save(&dir, &spec);
        assert!(
            ManualNoteHierarchy::load_with_masks(
                &dir.path().join("categories.json"),
                &dir.path().join("notes.json")
            )
            .is_err(),
            "accepted invalid individual masks case {case}"
        );
    }
}

#[test]
fn changing_notes_resets_the_individual_mask_and_analysis_preserves_it() {
    let (dir, mut spec) = individual_fixture();
    let source = serde_json::to_vec(&json!({"notes": [
        {"note_id": "real", "text": TEXT},
        {"note_id": "real-2", "text": TEXT}
    ]}))
    .unwrap();
    fs::write(dir.path().join("notes.json"), &source).unwrap();
    spec["source_sha256"] = json!(format!("{:x}", Sha256::digest(source)));
    spec["notes"]
        .as_array_mut()
        .unwrap()
        .push(json!({"note_id": "real-2", "note_short_id": "N002"}));
    spec["nodes"][1]["note_ids"] = json!(["N001", "N002"]);
    for category in ["root", "coffee"] {
        spec["note_masks"][category]["N002"] = spec["note_masks"]["coffee"]["N001"].clone();
        spec["mask_instances"][category]["N002"] = json!([
            {"ids": ["V101"], "byte_spans": [range("coffee with")]},
            {"ids": ["V102"], "byte_spans": [range("with milk")]}
        ]);
    }
    let mut model = explorer(&dir, &spec);
    key(&mut model, KeyCode::Enter);
    key(&mut model, KeyCode::Char('O'));
    let first = screen(&mut model);
    key(&mut model, KeyCode::Char(']'));
    let second_mask = screen(&mut model);
    key(&mut model, KeyCode::Char('?'));
    let analysis = screen(&mut model);
    key(&mut model, KeyCode::Char(']'));
    assert_eq!(screen(&mut model), analysis);
    key(&mut model, KeyCode::Esc);
    assert_eq!(screen(&mut model), second_mask);
    key(&mut model, KeyCode::Char('l'));
    let next = screen(&mut model);
    for expected in ["N002", "Note 2 of 2", "V101", "Mask 1 of 2"] {
        assert!(next.contains(expected), "missing {expected}: {next}");
    }
    key(&mut model, KeyCode::Char('h'));
    assert_eq!(screen(&mut model), first);
}

#[test]
fn one_mask_keeps_all_its_separated_fragments_under_one_id() {
    let (dir, mut spec) = individual_fixture();
    for category in ["root", "coffee"] {
        spec["mask_instances"][category]["N001"][0]["byte_spans"] =
            json!([range("coffee"), range("milk")]);
        let spans: Vec<_> = spec["mask_instances"][category]["N001"]
            .as_array()
            .unwrap()
            .iter()
            .flat_map(|mask| mask["byte_spans"].as_array().unwrap().iter().cloned())
            .collect();
        spec["note_masks"][category]["N001"] = json!(spans);
    }
    let mut model = explorer(&dir, &spec);
    key(&mut model, KeyCode::Enter);
    key(&mut model, KeyCode::Char('O'));
    let first = screen(&mut model);
    for expected in [
        "V001",
        "Mask 1 of 2",
        "café ⟦coffee⟧ with ⟦milk⟧; tea later. coffee again.",
    ] {
        assert!(first.contains(expected), "missing {expected}: {first}");
    }
}
