use std::collections::BTreeSet;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;

use crossterm::event::{Event, KeyCode, KeyEvent, KeyModifiers};
use oracle_mvp::manual_note_hierarchy::ManualNoteHierarchy;
use oracle_mvp::manual_note_hierarchy_tui::ManualNoteExplorer;
use ratatui::Terminal;
use ratatui::backend::TestBackend;
use serde_json::{Value, json};
use sha2::{Digest, Sha256};

struct Fixture {
    _directory: tempfile::TempDir,
    spec: PathBuf,
    source: PathBuf,
}

impl Fixture {
    fn new(edit: impl FnOnce(&mut Value)) -> Self {
        let directory = tempfile::tempdir().unwrap();
        let source = directory.path().join("source.json");
        let spec = directory.path().join("categories.json");
        let bytes = serde_json::to_vec(&json!({"notes": [
            {"note_id": "original-1", "text": "Left shared right."},
            {"note_id": "original-2", "text": "Separate original note."}
        ]}))
        .unwrap();
        fs::write(&source, &bytes).unwrap();
        let mut data = json!({
            "schema_version": 2,
            "hierarchy_id": "diamond",
            "source_sha256": format!("{:x}", Sha256::digest(&bytes)),
            "root_node_id": "root",
            "notes": [
                {"note_id": "original-1", "note_short_id": "N001"},
                {"note_id": "original-2", "note_short_id": "N002"}
            ],
            "nodes": [
                {"node_id": "root", "label": "Subjects", "children": ["left", "right"], "note_ids": ["N002"]},
                {"node_id": "left", "label": "Left", "children": ["shared"], "note_ids": ["N001"]},
                {"node_id": "right", "label": "Right", "children": ["shared"], "note_ids": ["N001"]},
                {"node_id": "shared", "label": "Shared", "children": [], "note_ids": ["N001"]}
            ],
            "note_masks": {
                "root": {"N001": [[12, 17], [5, 9], [0, 4], [7, 11]], "N002": [[0, 23]]},
                "left": {"N001": [[0, 4], [5, 11]]},
                "right": {"N001": [[5, 11], [12, 17]]},
                "shared": {"N001": [[5, 11]]}
            }
        });
        edit(&mut data);
        fs::write(&spec, serde_json::to_vec(&data).unwrap()).unwrap();
        Self {
            _directory: directory,
            spec,
            source,
        }
    }
}

fn key(model: &mut ManualNoteExplorer, code: KeyCode) {
    model.handle_event(Event::Key(KeyEvent::new(code, KeyModifiers::NONE)));
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
fn diamond_loads_once_and_both_category_routes_keep_masks_breadcrumbs_and_back() {
    let fixture = Fixture::new(|_| {});
    let (hierarchy, masks) =
        ManualNoteHierarchy::load_with_masks(&fixture.spec, &fixture.source).unwrap();
    assert_eq!(hierarchy.nodes.len(), 4);
    assert_eq!(hierarchy.nodes["left"].children, ["shared"]);
    assert_eq!(hierarchy.nodes["right"].children, ["shared"]);
    assert_eq!(hierarchy.note_ids("root"), ["N001", "N002"]);
    for category in ["left", "right", "shared"] {
        assert_eq!(hierarchy.note_ids(category), ["N001"]);
    }
    let masks = masks.unwrap();
    assert_eq!(masks.spans("root", "N001"), [(0, 4), (5, 11), (12, 17)]);
    let mut model = ManualNoteExplorer::categories_with_masks(hierarchy, Some(masks), false);
    key(&mut model, KeyCode::Char('N'));
    let root_note = screen(&mut model);
    assert!(
        root_note.contains("⟦Left⟧ ⟦shared⟧ ⟦right⟧."),
        "{root_note}"
    );
    assert!(root_note.contains("Note 1 of 2"), "{root_note}");
    key(&mut model, KeyCode::Char('l'));
    let second_note = screen(&mut model);
    assert!(
        second_note.contains("⟦Separate original note.⟧"),
        "{second_note}"
    );
    assert!(second_note.contains("Note 2 of 2"), "{second_note}");
    key(&mut model, KeyCode::Esc);

    for (parent_label, expected_mask) in [
        ("Left", "⟦Left⟧ ⟦shared⟧ right."),
        ("Right", "Left ⟦shared⟧ ⟦right⟧."),
    ] {
        let root = screen(&mut model);
        key(&mut model, KeyCode::Enter);
        let parent = screen(&mut model);
        assert!(
            parent.contains(&format!("Subjects > {parent_label}")),
            "{parent}"
        );
        key(&mut model, KeyCode::Char('N'));
        let parent_note = screen(&mut model);
        assert!(parent_note.contains(expected_mask), "{parent_note}");
        assert!(parent_note.contains("Note 1 of 1"), "{parent_note}");
        key(&mut model, KeyCode::Esc);
        assert_eq!(screen(&mut model), parent);
        key(&mut model, KeyCode::Enter);
        let shared = screen(&mut model);
        assert!(
            shared.contains(&format!("Subjects > {parent_label} > Shared")),
            "{shared}"
        );
        assert!(shared.contains("Left ⟦shared⟧ right."), "{shared}");
        key(&mut model, KeyCode::Char('N'));
        let shared_note = screen(&mut model);
        assert!(
            shared_note.contains("Left ⟦shared⟧ right."),
            "{shared_note}"
        );
        assert!(shared_note.contains("Note 1 of 1"), "{shared_note}");
        assert!(
            shared_note.contains(&format!("Subjects > {parent_label} > Shared")),
            "{shared_note}"
        );
        key(&mut model, KeyCode::Esc);
        assert_eq!(screen(&mut model), parent);
        key(&mut model, KeyCode::Esc);
        assert_eq!(screen(&mut model), root);
        key(&mut model, KeyCode::Char('j'));
    }
}

#[test]
fn schema_one_still_rejects_shared_categories_and_unknown_versions_are_rejected() {
    let fixture = Fixture::new(|data| data["schema_version"] = json!(1));
    let error = ManualNoteHierarchy::load(&fixture.spec, &fixture.source)
        .unwrap_err()
        .to_string();
    assert!(error.contains("invalid parent count"), "{error}");
    for version in [0, 3] {
        let fixture = Fixture::new(|data| data["schema_version"] = json!(version));
        assert!(ManualNoteHierarchy::load(&fixture.spec, &fixture.source).is_err());
    }
}

#[test]
fn schema_two_rejects_true_cycles_parents_on_root_and_missing_or_unreachable_categories() {
    let fixture = Fixture::new(|data| data["nodes"][3]["children"] = json!(["left"]));
    let error = ManualNoteHierarchy::load(&fixture.spec, &fixture.source)
        .unwrap_err()
        .to_string();
    assert!(error.contains("cycle"), "{error}");
    for edit in [
        |data: &mut Value| data["nodes"][3]["children"] = json!(["root"]),
        |data: &mut Value| data["nodes"][3]["children"] = json!(["missing"]),
        |data: &mut Value| data["nodes"][0]["children"] = json!(["left", "left", "right"]),
        |data: &mut Value| data["nodes"][0]["children"] = json!(["left"]),
        |data: &mut Value| {
            data["nodes"].as_array_mut().unwrap().push(json!({
                "node_id": "unreachable", "label": "Unreachable",
                "children": ["unreachable"], "note_ids": ["N001"]
            }));
        },
    ] {
        let fixture = Fixture::new(edit);
        assert!(ManualNoteHierarchy::load(&fixture.spec, &fixture.source).is_err());
    }
}

#[test]
fn shared_category_masks_must_be_covered_by_every_parent() {
    for parent in ["left", "right"] {
        let fixture = Fixture::new(|data| {
            data["note_masks"][parent]["N001"] = json!([[0, 4]]);
        });
        let error = ManualNoteHierarchy::load(&fixture.spec, &fixture.source)
            .unwrap_err()
            .to_string();
        assert!(
            error.contains(&format!("category {parent} mask omits child shared/N001")),
            "{error}"
        );
    }
}

#[test]
fn absorption_leaves_shared_categories_unchanged_and_cli_rejects_the_option() {
    let fixture = Fixture::new(|_| {});
    let mut hierarchy = ManualNoteHierarchy::load(&fixture.spec, &fixture.source).unwrap();
    let before = format!("{hierarchy:?}");
    assert_eq!(hierarchy.absorb_single_children(), 0);
    assert_eq!(format!("{hierarchy:?}"), before);

    let output = Command::new(env!("CARGO_BIN_EXE_sse-subject-navigation"))
        .arg("--categories")
        .arg(&fixture.spec)
        .arg(&fixture.source)
        .args(["--absorb-single-children", "--check"])
        .output()
        .unwrap();
    assert!(!output.status.success());
    let stderr = String::from_utf8_lossy(&output.stderr);
    assert!(stderr.contains("--absorb-single-children"), "{stderr}");
    assert!(stderr.contains("shared categories"), "{stderr}");
}

#[test]
fn schema_two_tree_inputs_still_allow_single_child_absorption() {
    let fixture = Fixture::new(|data| data["nodes"][2]["children"] = json!([]));
    let mut hierarchy = ManualNoteHierarchy::load(&fixture.spec, &fixture.source).unwrap();
    let before = hierarchy.note_ids("root");
    assert_eq!(hierarchy.absorb_single_children(), 1);
    assert_eq!(hierarchy.note_ids("root"), before);
    assert!(!hierarchy.nodes.contains_key("shared"));
    assert!(hierarchy.nodes["left"].children.is_empty());
}

#[test]
fn category_cli_checks_the_unchanged_shared_graph_without_a_terminal() {
    let fixture = Fixture::new(|_| {});
    let before = fs::read(&fixture.spec).unwrap();
    let output = Command::new(env!("CARGO_BIN_EXE_sse-subject-navigation"))
        .arg("--categories")
        .arg(&fixture.spec)
        .arg(&fixture.source)
        .arg("--check")
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains("4 categories · 2 notes"), "{stdout}");
    assert_eq!(stdout.matches("Children: shared").count(), 2, "{stdout}");
    assert_eq!(fs::read(&fixture.spec).unwrap(), before);
}

#[test]
fn saved_true11_keeps_every_canonical_category_edge_and_original_note_membership() {
    let directory = Path::new("sse_multivector/navigation-research-v1/TRUE11");
    let (hierarchy, masks) = ManualNoteHierarchy::load_with_masks(
        &directory.join("categories.json"),
        Path::new("sse_multivector/real-note-fine-segmentation-v1/reviewed-input.json"),
    )
    .unwrap();
    let native: Value =
        serde_json::from_slice(&fs::read(directory.join("native-notes.json")).unwrap()).unwrap();
    let graph: Value =
        serde_json::from_slice(&fs::read(directory.join("native-graph.json")).unwrap()).unwrap();
    let nodes = native["nodes"].as_array().unwrap();
    assert_eq!(nodes.len(), 58);
    assert_eq!(hierarchy.nodes.len(), 59);
    assert_eq!(hierarchy.note_ids(&hierarchy.root_node_id).len(), 77);
    assert!(hierarchy.has_shared_categories());
    assert!(masks.is_some());
    let strings = |value: &Value| {
        value
            .as_array()
            .unwrap()
            .iter()
            .map(|item| item.as_str().unwrap().to_owned())
            .collect::<BTreeSet<_>>()
    };
    let originals = |short_ids: &[String]| {
        short_ids
            .iter()
            .map(|short| hierarchy.notes[short].note_id.clone())
            .collect::<BTreeSet<_>>()
    };
    assert_eq!(
        hierarchy.nodes[&hierarchy.root_node_id]
            .children
            .iter()
            .cloned()
            .collect::<BTreeSet<_>>(),
        strings(&graph["roots"])
    );
    for node in nodes {
        let id = node["group"].as_str().unwrap();
        let category = &hierarchy.nodes[id];
        assert_eq!(category.node_id, id);
        assert_eq!(category.label, node["title"].as_str().unwrap());
        assert_eq!(
            originals(&category.note_ids),
            strings(&node["own_note_ids"]),
            "{id}"
        );
        assert_eq!(
            originals(&hierarchy.note_ids(id)),
            strings(&node["recursive_note_ids"]),
            "{id}"
        );
        let expected_children = graph["transitive_reduced_edges"]
            .as_array()
            .unwrap()
            .iter()
            .filter(|edge| edge["a_id"] == id)
            .map(|edge| edge["b_id"].as_str().unwrap().to_owned())
            .collect::<BTreeSet<_>>();
        assert_eq!(
            category.children.iter().cloned().collect::<BTreeSet<_>>(),
            expected_children,
            "{id}"
        );
    }
}
