use std::fs;
use std::path::PathBuf;
use std::process::{Command, Output};

use crossterm::event::{Event, KeyCode, KeyEvent, KeyModifiers};
use oracle_mvp::hdbscan_hierarchy::{Hierarchy, load_note_short_ids};
use oracle_mvp::hdbscan_hierarchy_tui::HierarchyExplorer;
use ratatui::Terminal;
use ratatui::backend::TestBackend;
use serde_json::{Value, json};
use sha2::{Digest, Sha256};

fn fixture() -> (Value, Value, Value) {
    let mut hierarchy = json!({
        "schema_version": "infomap-hierarchy-v1",
        "vector_count": 5,
        "canonical_unique_ids": ["v0", "v1", "v2", "v3", "v4"],
        "alias_groups": [["v0"], ["v1", "alias"], ["v2"], ["v3"], ["v4"]],
        "paths": [
            {"node_id": 4, "module_path": [3]},
            {"node_id": 2, "module_path": [1, 2]},
            {"node_id": 0, "module_path": [1]},
            {"node_id": 3, "module_path": [2]},
            {"node_id": 1, "module_path": [1, 1]}
        ]
    });
    let vectors = json!({"vectors": [
        {"vector_id":"v0","short_id":"V0","note_id":"a","note_short_id":"N001","byte_spans":[[0,5]],"fragments":["café"]},
        {"vector_id":"v1","short_id":"V1","note_id":"a","note_short_id":"N001","byte_spans":[[6,9]],"fragments":["one"]},
        {"vector_id":"alias","short_id":"VA","note_id":"b","note_short_id":"N002","byte_spans":[[0,3]],"fragments":["tea"]},
        {"vector_id":"v2","short_id":"V2","note_id":"a","note_short_id":"N001","byte_spans":[[10,13]],"fragments":["two"]},
        {"vector_id":"v3","short_id":"V3","note_id":"c","note_short_id":"N003","byte_spans":[[0,5]],"fragments":["stock"]},
        {"vector_id":"v4","short_id":"V4","note_id":"d","note_short_id":"N004","byte_spans":[[0,5]],"fragments":["other"]}
    ]});
    let notes = json!({"notes": [
        {"note_id":"a","text":"café one two, full original tail"},
        {"note_id":"b","text":"tea original"},
        {"note_id":"c","text":"stock original"},
        {"note_id":"d","text":"other original"}
    ]});
    seal_sources(&mut hierarchy, &vectors, &notes);
    (hierarchy, vectors, notes)
}

fn seal_sources(hierarchy: &mut Value, vectors: &Value, notes: &Value) {
    hierarchy["sources"] = json!({
        "vector_map": {"path": "vectors.json", "sha256": format!("{:x}", Sha256::digest(serde_json::to_vec(vectors).unwrap()))},
        "notes": {"path": "notes.json", "sha256": format!("{:x}", Sha256::digest(serde_json::to_vec(notes).unwrap()))}
    });
}

fn saved_fixture(values: &(Value, Value, Value)) -> (tempfile::TempDir, [PathBuf; 3]) {
    let directory = tempfile::tempdir().unwrap();
    let paths = [
        directory.path().join("hierarchy.json"),
        directory.path().join("vectors.json"),
        directory.path().join("notes.json"),
    ];
    for (path, value) in paths.iter().zip([&values.0, &values.1, &values.2]) {
        fs::write(path, serde_json::to_vec(value).unwrap()).unwrap();
    }
    (directory, paths)
}

fn run_cli(paths: &[PathBuf; 3], options: &[&str]) -> Output {
    Command::new(env!("CARGO_BIN_EXE_hdbscan-hierarchy"))
        .args(paths)
        .args(options)
        .output()
        .unwrap()
}

#[test]
fn infomap_cli_validates_native_modules_without_source_writes() {
    let (directory, paths) = saved_fixture(&fixture());
    let before = paths
        .iter()
        .map(fs::read)
        .collect::<Result<Vec<_>, _>>()
        .unwrap();
    let output = run_cli(&paths, &["--infomap", "--start-at", "7", "--check"]);
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let text = String::from_utf8_lossy(&output.stdout);
    for expected in [
        "Infomap hierarchy",
        "6 groups",
        "5 unique vectors",
        "6 original IDs",
        "4 notes",
        "Starting branch 7",
    ] {
        assert!(text.contains(expected), "Missing {expected}: {text}");
    }
    assert!(!text.contains("Merge-tree"), "{text}");
    assert_eq!(
        before,
        paths
            .iter()
            .map(fs::read)
            .collect::<Result<Vec<_>, _>>()
            .unwrap()
    );
    assert_eq!(fs::read_dir(directory.path()).unwrap().count(), 3);
}

#[test]
fn infomap_cli_rejects_conflicting_or_repeated_modes_before_loading_files() {
    let paths = ["missing.json", "missing-vectors.json", "missing-notes.json"].map(PathBuf::from);
    for options in [
        vec!["--infomap", "--note-navigation"],
        vec!["--infomap", "--merge-history"],
        vec!["--infomap", "--selection", "missing-selection.json"],
        vec!["--infomap", "--min-notes", "2"],
        vec!["--infomap", "--infomap"],
    ] {
        let output = run_cli(&paths, &options);
        assert!(!output.status.success(), "accepted {options:?}");
        let error = String::from_utf8_lossy(&output.stderr);
        assert!(error.contains("--infomap"), "{options:?}: {error}");
        assert!(!error.contains("No such file"), "{options:?}: {error}");
    }
}

#[test]
fn infomap_cli_explains_native_view_and_rejects_unknown_start_or_nonterminal() {
    let help = Command::new(env!("CARGO_BIN_EXE_hdbscan-hierarchy"))
        .arg("--help")
        .output()
        .unwrap();
    let text = String::from_utf8_lossy(&help.stdout);
    assert!(text.contains("--infomap"), "{text}");
    assert!(text.contains("native module"), "{text}");
    let (_directory, paths) = saved_fixture(&fixture());
    for (options, expected) in [
        (
            vec!["--infomap", "--start-at", "999", "--check"],
            "unknown group 999",
        ),
        (vec!["--infomap"], "interactive terminal"),
    ] {
        let output = run_cli(&paths, &options);
        assert!(!output.status.success());
        let error = String::from_utf8_lossy(&output.stderr);
        assert!(error.contains(expected), "{error}");
    }
}

#[test]
fn infomap_cli_rejects_changed_sources_even_when_all_masks_still_match() {
    for source_index in [1, 2] {
        let (_directory, paths) = saved_fixture(&fixture());
        let mut bytes = fs::read(&paths[source_index]).unwrap();
        bytes.push(b'\n');
        fs::write(&paths[source_index], bytes).unwrap();
        let output = run_cli(&paths, &["--infomap", "--check"]);
        assert!(!output.status.success());
        let error = String::from_utf8_lossy(&output.stderr);
        assert!(
            error.contains("Infomap source checksum mismatch"),
            "{error}"
        );
    }
}

#[test]
fn native_modules_keep_every_prefix_direct_vector_alias_and_full_original() {
    let values = fixture();
    let (_directory, paths) = saved_fixture(&values);
    let hierarchy = Hierarchy::load_infomap(&paths[0], &paths[1], &paths[2]).unwrap();
    assert_eq!(hierarchy.root, 5);
    assert_eq!(
        hierarchy.groups.keys().copied().collect::<Vec<_>>(),
        [5, 6, 7, 8, 9, 10]
    );
    assert_eq!(hierarchy.groups[&5].children, [6, 9, 10]);
    assert_eq!(hierarchy.groups[&6].children, [7, 8]);
    assert_eq!(hierarchy.groups[&6].parent, Some(5));
    assert_eq!(hierarchy.groups[&7].parent, Some(6));
    assert_eq!(hierarchy.groups[&8].parent, Some(6));
    assert_eq!(hierarchy.groups[&6].vectors, [0]);
    assert_eq!(hierarchy.groups[&7].vectors, [1]);
    assert_eq!(hierarchy.groups[&8].vectors, [2]);
    assert_eq!(hierarchy.groups[&9].vectors, [3]);
    assert_eq!(hierarchy.groups[&10].vectors, [4]);
    assert!(hierarchy.groups[&5].vectors.is_empty());
    assert_eq!(
        (
            hierarchy.groups[&5].vector_count,
            hierarchy.groups[&5].note_count
        ),
        (5, 4)
    );
    assert_eq!(
        (
            hierarchy.groups[&6].vector_count,
            hierarchy.groups[&6].note_count
        ),
        (3, 2)
    );
    assert_eq!(
        (
            hierarchy.groups[&7].vector_count,
            hierarchy.groups[&7].note_count
        ),
        (1, 2)
    );
    assert_eq!(
        (
            hierarchy.groups[&8].vector_count,
            hierarchy.groups[&8].note_count
        ),
        (1, 1)
    );
    assert_eq!(hierarchy.vectors.values().map(Vec::len).sum::<usize>(), 6);
    for original in values.1["vectors"].as_array().unwrap() {
        let actual = hierarchy
            .vectors
            .values()
            .flatten()
            .find(|mask| mask.vector_id == original["vector_id"].as_str().unwrap())
            .unwrap();
        assert_eq!(actual.id, original["short_id"]);
        assert_eq!(actual.note_id, original["note_id"]);
        assert_eq!(
            serde_json::to_value(&actual.fragments).unwrap(),
            original["fragments"]
        );
        assert_eq!(
            serde_json::to_value(&actual.byte_spans).unwrap(),
            original["byte_spans"]
        );
        let source = values.2["notes"]
            .as_array()
            .unwrap()
            .iter()
            .find(|note| note["note_id"] == original["note_id"])
            .unwrap();
        assert_eq!(actual.text, source["text"]);
    }
}

#[test]
fn module_ids_use_numeric_lexicographic_prefixes_without_path_collisions() {
    let (mut input, vectors, notes) = fixture();
    input["paths"] = json!([
        {"node_id": 0, "module_path": [1, 12]},
        {"node_id": 1, "module_path": [11, 2]},
        {"node_id": 2, "module_path": [1, 2]},
        {"node_id": 3, "module_path": [1, 2]},
        {"node_id": 4, "module_path": []}
    ]);
    let (_directory, paths) = saved_fixture(&(input.clone(), vectors.clone(), notes.clone()));
    let hierarchy = Hierarchy::load_infomap(&paths[0], &paths[1], &paths[2]).unwrap();
    assert_eq!(hierarchy.groups[&5].children, [6, 9]);
    assert_eq!(hierarchy.groups[&6].children, [7, 8]);
    assert_eq!(hierarchy.groups[&9].children, [10]);
    assert_eq!(hierarchy.groups[&5].vectors, [4]);
    assert_eq!(hierarchy.groups[&7].vectors, [2, 3]);
    assert_eq!(hierarchy.groups[&8].vectors, [0]);
    assert_eq!(hierarchy.groups[&10].vectors, [1]);
    input["paths"].as_array_mut().unwrap().reverse();
    // Other producer fields never define or override membership.
    input["modules"] = json!([{"group_id": 7, "module_path": [999]}]);
    input["labels"] = json!(["do not render"]);
    let (_reordered, reordered_paths) = saved_fixture(&(input, vectors, notes));
    let reordered = Hierarchy::load_infomap(
        &reordered_paths[0],
        &reordered_paths[1],
        &reordered_paths[2],
    )
    .unwrap();
    for (id, group) in hierarchy.groups {
        let other = &reordered.groups[&id];
        assert_eq!(
            (group.parent, group.children, group.vectors),
            (other.parent, other.children.clone(), other.vectors.clone())
        );
    }
}

#[test]
fn one_vector_root_and_deep_same_note_module_chains_are_not_pruned() {
    for module_path in [vec![], vec![4], vec![2; 96]] {
        let (mut input, mut vectors, mut notes) = fixture();
        input["vector_count"] = json!(1);
        input["canonical_unique_ids"] = json!(["v0"]);
        input["alias_groups"] = json!([["v0"]]);
        input["paths"] = json!([{"node_id": 0, "module_path": module_path}]);
        vectors["vectors"].as_array_mut().unwrap().truncate(1);
        notes["notes"].as_array_mut().unwrap().truncate(1);
        seal_sources(&mut input, &vectors, &notes);
        let (_directory, paths) = saved_fixture(&(input, vectors, notes));
        let hierarchy = Hierarchy::load_infomap(&paths[0], &paths[1], &paths[2]).unwrap();
        assert_eq!(hierarchy.root, 1);
        assert_eq!(hierarchy.groups.len(), module_path.len() + 1);
        for (&id, group) in &hierarchy.groups {
            assert_eq!((group.vector_count, group.note_count), (1, 1));
            assert_eq!(group.parent, if id == 1 { None } else { Some(id - 1) });
            if id == module_path.len() + 1 {
                assert_eq!(group.vectors, [0]);
                assert!(group.children.is_empty());
            } else {
                assert!(group.vectors.is_empty());
                assert_eq!(group.children, [id + 1]);
            }
        }
    }
}

#[test]
fn malformed_infomap_inputs_are_rejected_without_panics_or_partial_trees() {
    for case in [
        "schema",
        "missing schema",
        "missing sources",
        "missing vector source",
        "missing note hash",
        "zero vectors",
        "wrong aliases",
        "wrong canonical count",
        "duplicate canonical",
        "duplicate alias",
        "empty aliases",
        "unmapped vector",
        "missing node",
        "extra node",
        "duplicate node",
        "outside node",
        "negative node",
        "fractional node",
        "zero component",
        "negative component",
        "fractional component",
        "string component",
        "null path",
        "missing path",
        "wrong fragment",
        "invalid span",
        "overlap",
        "missing note",
        "duplicate note",
        "duplicate vector",
        "duplicate short id",
    ] {
        let (mut input, mut vectors, mut notes) = fixture();
        match case {
            "schema" => input["schema_version"] = json!("other-v1"),
            "missing schema" => {
                input.as_object_mut().unwrap().remove("schema_version");
            }
            "missing sources" => {
                input.as_object_mut().unwrap().remove("sources");
            }
            "missing vector source" => {
                input["sources"]
                    .as_object_mut()
                    .unwrap()
                    .remove("vector_map");
            }
            "missing note hash" => {
                input["sources"]["notes"]
                    .as_object_mut()
                    .unwrap()
                    .remove("sha256");
            }
            "zero vectors" => input["vector_count"] = json!(0),
            "wrong aliases" => {
                input["alias_groups"].as_array_mut().unwrap().pop();
            }
            "wrong canonical count" => {
                input["canonical_unique_ids"].as_array_mut().unwrap().pop();
            }
            "duplicate canonical" => input["canonical_unique_ids"][1] = json!("v0"),
            "duplicate alias" => input["alias_groups"][1] = json!(["v1", "v0"]),
            "empty aliases" => input["alias_groups"][0] = json!([]),
            "unmapped vector" => input["alias_groups"][1] = json!(["v1"]),
            "missing node" => {
                input["paths"].as_array_mut().unwrap().pop();
            }
            "extra node" => {
                let row = input["paths"][0].clone();
                input["paths"].as_array_mut().unwrap().push(row);
            }
            "duplicate node" => input["paths"][0]["node_id"] = json!(0),
            "outside node" => input["paths"][0]["node_id"] = json!(5),
            "negative node" => input["paths"][0]["node_id"] = json!(-1),
            "fractional node" => input["paths"][0]["node_id"] = json!(1.5),
            "zero component" => input["paths"][0]["module_path"] = json!([0]),
            "negative component" => input["paths"][0]["module_path"] = json!([-1]),
            "fractional component" => input["paths"][0]["module_path"] = json!([1.5]),
            "string component" => input["paths"][0]["module_path"] = json!(["1"]),
            "null path" => input["paths"][0]["module_path"] = Value::Null,
            "missing path" => {
                input["paths"][0]
                    .as_object_mut()
                    .unwrap()
                    .remove("module_path");
            }
            "wrong fragment" => vectors["vectors"][0]["fragments"] = json!(["cafe"]),
            "invalid span" => vectors["vectors"][0]["byte_spans"] = json!([[0, 4]]),
            "overlap" => {
                vectors["vectors"][0]["byte_spans"] = json!([[0, 5], [0, 5]]);
                vectors["vectors"][0]["fragments"] = json!(["café", "café"]);
            }
            "missing note" => {
                notes["notes"].as_array_mut().unwrap().pop();
            }
            "duplicate note" => {
                let row = notes["notes"][0].clone();
                notes["notes"].as_array_mut().unwrap().push(row);
            }
            "duplicate vector" => {
                let row = vectors["vectors"][0].clone();
                vectors["vectors"].as_array_mut().unwrap().push(row);
            }
            "duplicate short id" => vectors["vectors"][1]["short_id"] = json!("V0"),
            _ => unreachable!(),
        }
        if vectors != fixture().1 || notes != fixture().2 {
            seal_sources(&mut input, &vectors, &notes);
        }
        let (_directory, paths) = saved_fixture(&(input, vectors, notes));
        let error = Hierarchy::load_infomap(&paths[0], &paths[1], &paths[2]).expect_err(case);
        assert!(
            !error.to_string().contains("checksum mismatch"),
            "{case}: should exercise structural/source-mask validation, got {error}"
        );
    }
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
fn infomap_tui_preserves_native_choices_and_exposes_exact_masks_and_originals() {
    let (_directory, paths) = saved_fixture(&fixture());
    let hierarchy = Hierarchy::load_infomap(&paths[0], &paths[1], &paths[2]).unwrap();
    let short_ids = load_note_short_ids(&paths[1]).unwrap();
    let mut model = HierarchyExplorer::new_infomap(hierarchy, Some(6), short_ids).unwrap();
    let initial = screen(&mut model);
    for text in [
        "Infomap hierarchy",
        "Showing branch 6 · 2 notes",
        "▸ 7 · 2 notes",
        "▸ 8 · 1 note",
        "a Show parent masks",
    ] {
        assert!(initial.contains(text), "Missing {text}: {initial}");
    }
    assert!(
        !initial.contains("V0"),
        "same-note parent mask starts hidden: {initial}"
    );
    key(&mut model, KeyCode::Char('j'));
    key(&mut model, KeyCode::Char('l'));
    let expanded = screen(&mut model);
    for text in ["├─ ▾ 7", "V1 · N001  ⟦one⟧", "VA · N002  ⟦tea⟧"] {
        assert!(expanded.contains(text), "Missing {text}: {expanded}");
    }
    key(&mut model, KeyCode::Char('f'));
    assert!(screen(&mut model).contains("Showing branch 7 · 2 notes"));
    key(&mut model, KeyCode::Char('u'));
    assert!(screen(&mut model).contains("Showing branch 6 · 2 notes"));
    key(&mut model, KeyCode::Char('a'));
    let all = screen(&mut model);
    assert!(all.contains("V0 · N001  ⟦café⟧"), "{all}");
    assert!(
        all.contains("▾ 7 · 2 notes") && all.contains("▸ 8 · 1 note"),
        "{all}"
    );
    key(&mut model, KeyCode::Home);
    key(&mut model, KeyCode::Down);
    key(&mut model, KeyCode::Enter);
    let note = screen(&mut model);
    for text in [
        "Original note",
        "V0 · N001",
        "Source note ID: a",
        "⟦café⟧ one two, full original tail",
    ] {
        assert!(note.contains(text), "Missing {text}: {note}");
    }
    key(&mut model, KeyCode::Esc);
    key(&mut model, KeyCode::Char('a'));
    assert!(!screen(&mut model).contains("V0"));
}

#[test]
fn infomap_help_names_native_modules_without_merge_or_note_projection_claims() {
    let (_directory, paths) = saved_fixture(&fixture());
    let hierarchy = Hierarchy::load_infomap(&paths[0], &paths[1], &paths[2]).unwrap();
    let mut model =
        HierarchyExplorer::new_infomap(hierarchy, None, load_note_short_ids(&paths[1]).unwrap())
            .unwrap();
    let root = screen(&mut model);
    for text in ["▸ 6 · 2 notes", "▸ 9 · 1 note", "▸ 10 · 1 note"] {
        assert!(root.contains(text), "Missing {text}: {root}");
    }
    key(&mut model, KeyCode::Char('?'));
    let help = screen(&mut model);
    for text in [
        "native module",
        "within this run",
        "another run can have different contents",
        "Counts are distinct source notes",
        "No modules are removed",
        "a shows or hides",
        "N numbers",
        "V numbers",
    ] {
        assert!(help.contains(text), "Missing {text}: {help}");
    }
    for false_claim in [
        "merge-tree IDs",
        "condensed-tree IDs",
        "at least two distinct notes",
        "remaining descendants are promoted",
        "IDs in the saved tree",
        "lexicographic",
        "vector_count",
    ] {
        assert!(
            !help.contains(false_claim),
            "False claim {false_claim}: {help}"
        );
    }
}

#[test]
fn infomap_cli_checks_note_short_ids_without_requiring_a_terminal() {
    for case in ["missing", "empty", "conflicting note", "conflicting short"] {
        let (mut input, mut vectors, notes) = fixture();
        match case {
            "missing" => {
                vectors["vectors"][0]
                    .as_object_mut()
                    .unwrap()
                    .remove("note_short_id");
            }
            "empty" => vectors["vectors"][0]["note_short_id"] = json!(" "),
            "conflicting note" => vectors["vectors"][0]["note_short_id"] = json!("N099"),
            "conflicting short" => vectors["vectors"][2]["note_short_id"] = json!("N001"),
            _ => unreachable!(),
        }
        seal_sources(&mut input, &vectors, &notes);
        let (_directory, paths) = saved_fixture(&(input, vectors, notes));
        let output = run_cli(&paths, &["--infomap", "--check"]);
        assert!(!output.status.success(), "accepted {case}");
        let error = String::from_utf8_lossy(&output.stderr);
        assert!(!error.contains("checksum mismatch"), "{error}");
    }
}

#[test]
fn all_saved_runs_match_native_module_memberships_counts_and_source_note_ids() {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let source = root.join("sse_multivector/real-note-fine-segmentation-v1");
    let vectors = source.join("vectors/vector-map.json");
    let notes = source.join("reviewed-input.json");
    let vector_bytes = fs::read(&vectors).unwrap();
    let note_bytes = fs::read(&notes).unwrap();
    let short_ids = load_note_short_ids(&vectors).unwrap();
    assert_eq!(short_ids.len(), 100);
    let originals: Value = serde_json::from_slice(&vector_bytes).unwrap();
    for original in originals["vectors"].as_array().unwrap() {
        assert_eq!(
            short_ids[original["note_id"].as_str().unwrap()],
            original["note_short_id"]
        );
    }
    for (run, groups) in [("I01", 2), ("I02", 44), ("I03", 29), ("I04", 17)] {
        let path = root.join(format!(
            "sse_multivector/infomap-experiment-v1/{run}/hierarchy.json"
        ));
        let before = fs::read(&path).unwrap();
        let input: Value = serde_json::from_slice(&before).unwrap();
        let hierarchy = Hierarchy::load_infomap(&path, &vectors, &notes).unwrap();
        assert_eq!(hierarchy.root, 916, "{run}");
        assert_eq!(hierarchy.groups.len(), groups, "{run}");
        assert_eq!(hierarchy.vectors.len(), 916, "{run}");
        assert_eq!(
            hierarchy.vectors.values().map(Vec::len).sum::<usize>(),
            945,
            "{run}"
        );
        assert_eq!(hierarchy.groups[&916].note_count, 100, "{run}");
        for native in input["modules"].as_array().unwrap() {
            let group = &hierarchy.groups[&(native["id"].as_u64().unwrap() as usize)];
            assert_eq!(
                serde_json::to_value(group.parent).unwrap(),
                native["parent"],
                "{run}"
            );
            assert_eq!(
                serde_json::to_value(&group.children).unwrap(),
                native["children"],
                "{run}"
            );
            assert_eq!(
                serde_json::to_value(&group.vectors).unwrap(),
                native["direct_vectors"],
                "{run}"
            );
            assert_eq!(
                group.vector_count,
                native["vector_ids"].as_array().unwrap().len(),
                "{run}"
            );
            assert_eq!(
                group.note_count,
                native["note_ids"].as_array().unwrap().len(),
                "{run}"
            );
        }
        if run == "I01" {
            assert_eq!(hierarchy.groups[&916].children, [917]);
            assert_eq!(hierarchy.groups[&917].vector_count, 916);
            assert_eq!(hierarchy.groups[&917].note_count, 100);
        }
        assert_eq!(fs::read(path).unwrap(), before);
    }
    assert_eq!(fs::read(vectors).unwrap(), vector_bytes);
    assert_eq!(fs::read(notes).unwrap(), note_bytes);
}

#[test]
fn identical_same_note_aliases_keep_every_id_in_the_native_view_and_note_detail() {
    let (mut input, mut vectors, notes) = fixture();
    let mut alias = vectors["vectors"][1].clone();
    alias["vector_id"] = json!("same-mask-alias");
    alias["short_id"] = json!("VX");
    vectors["vectors"].as_array_mut().unwrap().push(alias);
    input["alias_groups"][1]
        .as_array_mut()
        .unwrap()
        .push(json!("same-mask-alias"));
    seal_sources(&mut input, &vectors, &notes);
    let (_directory, paths) = saved_fixture(&(input, vectors, notes));
    let hierarchy = Hierarchy::load_infomap(&paths[0], &paths[1], &paths[2]).unwrap();
    assert_eq!(hierarchy.vectors[&1].len(), 3);
    let mut model =
        HierarchyExplorer::new_infomap(hierarchy, Some(7), load_note_short_ids(&paths[1]).unwrap())
            .unwrap();
    let visible = screen(&mut model);
    assert!(visible.contains("V1, VX · N001  ⟦one⟧"), "{visible}");
    assert!(visible.contains("VA · N002  ⟦tea⟧"), "{visible}");
    key(&mut model, KeyCode::Down);
    key(&mut model, KeyCode::Enter);
    let original = screen(&mut model);
    assert!(original.contains("V1, VX · N001"), "{original}");
    assert!(
        original.contains("café ⟦one⟧ two, full original tail"),
        "{original}"
    );
}

#[test]
fn infomap_review_note_keeps_the_parent_mask_status_visible() {
    let (_directory, paths) = saved_fixture(&fixture());
    let hierarchy = Hierarchy::load_infomap(&paths[0], &paths[1], &paths[2]).unwrap();
    let mut model =
        HierarchyExplorer::new_infomap(hierarchy, Some(6), load_note_short_ids(&paths[1]).unwrap())
            .unwrap();
    key(&mut model, KeyCode::Char('a'));
    key(&mut model, KeyCode::Down);
    key(&mut model, KeyCode::Enter);
    let original = screen(&mut model);
    for text in [
        "Original note · V0 · N001",
        "Source note ID: a",
        "All parent masks shown in hierarchy",
        "⟦café⟧ one two, full original tail",
        "Esc Return to hierarchy",
    ] {
        assert!(original.contains(text), "Missing {text}: {original}");
    }
}

#[test]
fn infomap_review_cli_reports_the_saved_run_id_not_the_filename() {
    let (mut input, vectors, notes) = fixture();
    input["run_id"] = json!("saved-experiment-42");
    let (_directory, paths) = saved_fixture(&(input, vectors, notes));
    let output = run_cli(&paths, &["--infomap", "--check"]);
    assert!(output.status.success());
    let text = String::from_utf8_lossy(&output.stdout);
    assert!(
        text.contains("Infomap hierarchy · saved-experiment-42"),
        "{text}"
    );
}

#[test]
fn infomap_review_identity_survives_note_help_and_parent_navigation() {
    let (mut input, vectors, notes) = fixture();
    input["run_id"] = json!("saved-experiment-42");
    let (_directory, paths) = saved_fixture(&(input, vectors, notes));
    let (hierarchy, run_id) =
        Hierarchy::load_infomap_with_run_id(&paths[0], &paths[1], &paths[2]).unwrap();
    assert_eq!(run_id.as_deref(), Some("saved-experiment-42"));
    let mut model =
        HierarchyExplorer::new_infomap(hierarchy, Some(7), load_note_short_ids(&paths[1]).unwrap())
            .unwrap()
            .with_run_id(run_id);
    let tree = screen(&mut model);
    assert!(
        tree.contains("Infomap hierarchy · saved-experiment-42"),
        "{tree}"
    );
    key(&mut model, KeyCode::Down);
    key(&mut model, KeyCode::Enter);
    let note = screen(&mut model);
    assert!(
        note.contains("Original note · saved-experiment-42 · V1 · N001"),
        "{note}"
    );
    key(&mut model, KeyCode::Esc);
    key(&mut model, KeyCode::Char('u'));
    let parent = screen(&mut model);
    assert!(
        parent.contains("Infomap hierarchy · saved-experiment-42"),
        "{parent}"
    );
    assert!(parent.contains("Showing branch 6"), "{parent}");
    key(&mut model, KeyCode::Char('?'));
    let help = screen(&mut model);
    assert!(help.contains("saved-experiment-42"), "{help}");
}

#[test]
fn infomap_review_narrow_note_header_keeps_full_source_id_status_and_controls() {
    let (mut input, mut vectors, mut notes) = fixture();
    input["run_id"] = json!("I03");
    let source_id = "a".repeat(64);
    notes["notes"][0]["note_id"] = json!(source_id);
    for vector in vectors["vectors"].as_array_mut().unwrap() {
        if vector["note_id"] == "a" {
            vector["note_id"] = json!(source_id);
        }
    }
    seal_sources(&mut input, &vectors, &notes);
    let (_directory, paths) = saved_fixture(&(input, vectors, notes));
    let (hierarchy, run_id) =
        Hierarchy::load_infomap_with_run_id(&paths[0], &paths[1], &paths[2]).unwrap();
    let mut model =
        HierarchyExplorer::new_infomap(hierarchy, Some(6), load_note_short_ids(&paths[1]).unwrap())
            .unwrap()
            .with_run_id(run_id);
    key(&mut model, KeyCode::Char('a'));
    key(&mut model, KeyCode::Down);
    key(&mut model, KeyCode::Enter);
    for (width, height) in [(60, 12), (80, 24)] {
        let mut terminal = Terminal::new(TestBackend::new(width, height)).unwrap();
        terminal.draw(|frame| model.render(frame)).unwrap();
        let buffer = terminal.backend().buffer();
        let lines = (0..height)
            .map(|y| {
                (0..width)
                    .map(|x| buffer[(x, y)].symbol())
                    .collect::<String>()
            })
            .collect::<Vec<_>>();
        let screen = lines.join("\n");
        let header = lines
            .iter()
            .take_while(|line| !line.starts_with('┌'))
            .map(|line| line.trim())
            .collect::<String>();
        for text in [
            "Original note · I03",
            "Source note ID:",
            &source_id,
            "All parent masks shown in hierarchy",
        ] {
            assert!(header.contains(text), "Missing {text}: {screen}");
        }
        assert!(
            screen.contains("⟦café⟧ one two, full original tail"),
            "{screen}"
        );
        assert!(screen.contains("Esc Return to hierarchy"), "{screen}");
    }
}

#[test]
fn infomap_review_rejects_an_empty_saved_run_id_without_inventing_one() {
    for run_id in ["", " ", "\n\t"] {
        let (mut input, vectors, notes) = fixture();
        input["run_id"] = json!(run_id);
        let (_directory, paths) = saved_fixture(&(input, vectors, notes));
        let output = run_cli(&paths, &["--infomap", "--check"]);
        assert!(!output.status.success());
        assert!(String::from_utf8_lossy(&output.stderr).contains("run_id"));
    }
}

#[test]
fn infomap_review_all_saved_run_ids_are_visible_at_root_masks_note_and_help() {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let source = root.join("sse_multivector/real-note-fine-segmentation-v1");
    let vectors = source.join("vectors/vector-map.json");
    let notes = source.join("reviewed-input.json");
    for run in ["I01", "I02", "I03", "I04"] {
        let path = root.join(format!(
            "sse_multivector/infomap-experiment-v1/{run}/hierarchy.json"
        ));
        let (hierarchy, run_id) =
            Hierarchy::load_infomap_with_run_id(&path, &vectors, &notes).unwrap();
        assert_eq!(run_id.as_deref(), Some(run));
        let mut model =
            HierarchyExplorer::new_infomap(hierarchy, None, load_note_short_ids(&vectors).unwrap())
                .unwrap()
                .with_run_id(run_id);
        let heading = format!("Infomap hierarchy · {run}");
        let root = screen(&mut model);
        assert!(root.contains(&heading), "{root}");
        key(&mut model, KeyCode::Down);
        key(&mut model, KeyCode::Char('f'));
        let masks = screen(&mut model);
        assert!(masks.contains(&heading), "{masks}");
        assert!(masks.contains(" · N"), "{masks}");
        key(&mut model, KeyCode::Down);
        key(&mut model, KeyCode::Enter);
        let note = screen(&mut model);
        assert!(note.contains(&format!("Original note · {run}")), "{note}");
        key(&mut model, KeyCode::Esc);
        key(&mut model, KeyCode::Char('?'));
        let help = screen(&mut model);
        assert!(
            help.contains(&format!("Infomap hierarchy help · {run}")),
            "{help}"
        );
    }
}
