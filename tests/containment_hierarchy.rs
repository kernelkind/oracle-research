use std::fs;
use std::path::PathBuf;
use std::process::{Command, Output};

use crossterm::event::{Event, KeyCode, KeyEvent, KeyModifiers};
use oracle_mvp::hdbscan_hierarchy::{Hierarchy, load_note_short_ids};
use oracle_mvp::hdbscan_hierarchy_tui::HierarchyExplorer;
use ratatui::{Terminal, backend::TestBackend};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};

fn fixture() -> (Value, Value, Value) {
    let vectors = json!({"vectors": [
        {"vector_id":"v0","short_id":"V0","note_id":"a","note_short_id":"N001","byte_spans":[[14,20]],"fragments":["Leaf A"]},
        {"vector_id":"v1","short_id":"V1","note_id":"b","note_short_id":"N002","byte_spans":[[0,3],[4,10]],"fragments":["hot","coffee"]},
        {"vector_id":"alias","short_id":"VA","note_id":"b","note_short_id":"N002","byte_spans":[[0,3],[4,10]],"fragments":["hot","coffee"]},
        {"vector_id":"v2","short_id":"V2","note_id":"c","note_short_id":"N003","byte_spans":[[0,3]],"fragments":["tea"]},
        {"vector_id":"v3","short_id":"V3","note_id":"a","note_short_id":"N001","byte_spans":[[0,8]],"fragments":["Parent A"]},
        {"vector_id":"v4","short_id":"V4","note_id":"d","note_short_id":"N004","byte_spans":[[0,5]],"fragments":["stock"]},
        {"vector_id":"v5","short_id":"V5","note_id":"e","note_short_id":"N005","byte_spans":[[0,5]],"fragments":["spare"]}
    ]});
    let notes = json!({"notes": [
        {"note_id":"a","text":"Parent A then Leaf A, complete original tail"},
        {"note_id":"b","text":"hot coffee full original"},
        {"note_id":"c","text":"tea full original"},
        {"note_id":"d","text":"stock full original"},
        {"note_id":"e","text":"spare full original"}
    ]});
    let hierarchy = json!({
        "schema_version":"containment-hierarchy-v1", "run_id":"HDFv1",
        "method":"hidef_weighted_leiden_strict_containment", "root":6, "vector_count":6,
        "canonical_unique_ids":["v0","v1","v2","v3","v4","v5"],
        "alias_groups":[["v0"],["v1","alias"],["v2"],["v3"],["v4"],["v5"]],
        "sources": {
            "vector_map":{"sha256":format!("{:x}", Sha256::digest(serde_json::to_vec(&vectors).unwrap()))},
            "notes":{"sha256":format!("{:x}", Sha256::digest(serde_json::to_vec(&notes).unwrap()))}
        },
        "groups":[
            {"id":6,"kind":"root","vector_ids":[0,1,2,3,4,5],"note_ids":["a","b","c","d","e"],"parents":[],"children":[7,8]},
            {"id":7,"kind":"persistent","vector_ids":[0,1,2,3],"note_ids":["a","b","c"],"parents":[6],"children":[10,11]},
            {"id":8,"kind":"persistent","vector_ids":[1,2,4],"note_ids":["b","c","d"],"parents":[6],"children":[9]},
            {"id":9,"kind":"persistent","vector_ids":[1,2],"note_ids":["b","c"],"parents":[8,10],"children":[]},
            {"id":10,"kind":"persistent","vector_ids":[0,1,2],"note_ids":["a","b","c"],"parents":[7],"children":[9]},
            {"id":11,"kind":"persistent","vector_ids":[3],"note_ids":["a"],"parents":[7],"children":[]}
        ]
    });
    (hierarchy, vectors, notes)
}

fn saved_fixture(values: &(Value, Value, Value)) -> (tempfile::TempDir, [PathBuf; 3]) {
    let directory = tempfile::tempdir().unwrap();
    let paths =
        ["hierarchy.json", "vectors.json", "notes.json"].map(|name| directory.path().join(name));
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
fn containment_cli_preserves_shared_groups_without_double_counting_or_source_writes() {
    let (directory, paths) = saved_fixture(&fixture());
    let before = paths
        .iter()
        .map(fs::read)
        .collect::<Result<Vec<_>, _>>()
        .unwrap();
    let output = run_cli(&paths, &["--containment", "--check"]);
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let text = String::from_utf8_lossy(&output.stdout);
    for expected in [
        "Containment hierarchy",
        "HDFv1",
        "5 groups",
        "6 unique vectors",
        "7 original IDs",
        "5 notes",
    ] {
        assert!(text.contains(expected), "Missing {expected}: {text}");
    }
    assert!(!text.contains("Infomap"), "{text}");
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

fn load(paths: &[PathBuf; 3]) -> Hierarchy {
    Hierarchy::load_containment_with_run_id(&paths[0], &paths[1], &paths[2])
        .unwrap()
        .0
}

fn explorer(values: &(Value, Value, Value), start: Option<usize>) -> HierarchyExplorer {
    let (_directory, paths) = saved_fixture(values);
    HierarchyExplorer::new_containment(load(&paths), start, load_note_short_ids(&paths[1]).unwrap())
        .unwrap()
        .with_run_id(Some("HDFv1".to_owned()))
}

fn screen(model: &mut HierarchyExplorer) -> String {
    let mut terminal = Terminal::new(TestBackend::new(140, 65)).unwrap();
    terminal.draw(|frame| model.render(frame)).unwrap();
    terminal
        .backend()
        .buffer()
        .content
        .chunks(140)
        .map(|row| row.iter().map(|cell| cell.symbol()).collect::<String>())
        .collect::<Vec<_>>()
        .join("\n")
}

fn key(model: &mut HierarchyExplorer, code: KeyCode) {
    assert!(!model.handle_event(Event::Key(KeyEvent::new(code, KeyModifiers::NONE))));
}

fn select_group(model: &mut HierarchyExplorer, id: usize, occurrence: usize) {
    key(model, KeyCode::Home);
    let mut matches = 0;
    for _ in 0..100 {
        let text = screen(model);
        let selected = text.lines().find(|line| line.contains('▶')).unwrap();
        if selected.contains(&format!(" {id} ·")) {
            matches += 1;
            if matches == occurrence {
                return;
            }
        }
        key(model, KeyCode::Char('j'));
    }
    panic!("group {id}, occurrence {occurrence} not found");
}

#[test]
fn exact_memberships_keep_both_parents_and_root_inventory_without_child_sums() {
    let (_directory, paths) = saved_fixture(&fixture());
    let hierarchy = load(&paths);
    assert_eq!(
        hierarchy.groups.keys().copied().collect::<Vec<_>>(),
        [6, 7, 8, 9, 10]
    );
    assert_eq!(hierarchy.groups[&7].children, [10]);
    assert_eq!(hierarchy.groups[&8].children, [9]);
    assert_eq!(hierarchy.groups[&10].children, [9]);
    assert_eq!(hierarchy.groups[&9].parent, None);
    assert_eq!(hierarchy.groups[&10].parent, Some(7));
    assert_eq!(hierarchy.groups[&6].vectors, [5]);
    assert_eq!(hierarchy.groups[&7].vectors, [3]); // hidden one-note group's mask survives
    assert_eq!(hierarchy.groups[&9].vectors, [1, 2]);
    assert_eq!(hierarchy.groups[&6].vector_count, 6);
    assert_eq!(hierarchy.groups[&6].note_count, 5);
    assert_eq!(hierarchy.groups[&7].note_count, 3);
    assert_eq!(hierarchy.groups[&10].note_count, 3); // equal-note edge retained
    assert_eq!(hierarchy.vectors[&1].len(), 2);
    for saved in fixture().0["groups"]
        .as_array()
        .unwrap()
        .iter()
        .filter(|g| g["id"] != 11)
    {
        let id = saved["id"].as_u64().unwrap() as usize;
        let mut pending = vec![id];
        let mut points = std::collections::BTreeSet::new();
        while let Some(group) = pending.pop() {
            points.extend(&hierarchy.groups[&group].vectors);
            pending.extend(&hierarchy.groups[&group].children);
        }
        assert_eq!(
            points.into_iter().copied().collect::<Vec<_>>(),
            saved["vector_ids"]
                .as_array()
                .unwrap()
                .iter()
                .map(|v| v.as_u64().unwrap() as usize)
                .collect::<Vec<_>>()
        );
    }
}

#[test]
fn shared_start_opens_all_routes_and_expansion_stays_specific_to_each_route() {
    let mut model = explorer(&fixture(), Some(9));
    let text = screen(&mut model);
    assert!(text.contains("Showing branch 6 · 5 notes"), "{text}");
    assert_eq!(text.matches("▾ 9 · 2 notes · shared").count(), 2, "{text}");
    assert_eq!(
        text.matches("V1, VA · N002  ⟦hot⟧ ⟦coffee⟧").count(),
        2,
        "{text}"
    );
    assert!(text.contains("10 · 3 notes · same notes"), "{text}");
    assert!(!text.contains("11 ·"), "{text}");
    assert!(!text.contains("⟦Parent A⟧"), "{text}");
    select_group(&mut model, 9, 1);
    key(&mut model, KeyCode::Enter);
    let collapsed = screen(&mut model);
    assert_eq!(
        collapsed.matches("▸ 9 · 2 notes · shared").count(),
        1,
        "{collapsed}"
    );
    assert_eq!(
        collapsed.matches("▾ 9 · 2 notes · shared").count(),
        1,
        "{collapsed}"
    );
    assert_eq!(
        collapsed.matches("⟦hot⟧ ⟦coffee⟧").count(),
        1,
        "{collapsed}"
    );
    key(&mut model, KeyCode::Char('f'));
    key(&mut model, KeyCode::Char('u'));
    assert!(screen(&mut model).contains("Showing branch 10 · 3 notes"));
    let mut other = explorer(&fixture(), Some(9));
    select_group(&mut other, 9, 2);
    key(&mut other, KeyCode::Char('f'));
    key(&mut other, KeyCode::Char('u'));
    assert!(screen(&mut other).contains("Showing branch 8 · 3 notes"));
}

#[test]
fn upward_navigation_keeps_nesting_and_unopened_siblings_above_open_routes() {
    let mut model = explorer(&fixture(), Some(10));
    select_group(&mut model, 9, 1);
    key(&mut model, KeyCode::Char('l'));
    key(&mut model, KeyCode::Char('u'));
    key(&mut model, KeyCode::Char('u'));
    let text = screen(&mut model);
    assert!(text.contains("Showing branch 6 · 5 notes"), "{text}");
    assert!(
        text.find("▸ 8").unwrap() < text.find("▾ 7").unwrap(),
        "{text}"
    );
    assert!(
        text.find("▾ 7").unwrap() < text.find("▾ 10").unwrap(),
        "{text}"
    );
    assert!(
        text.find("▾ 10").unwrap() < text.find("▾ 9").unwrap(),
        "{text}"
    );
    assert!(
        text.lines()
            .any(|line| line.contains('▶') && line.contains("▾ 9")),
        "{text}"
    );
}

#[test]
fn masks_use_spaces_keep_ids_open_complete_original_and_hide_parents_recursively() {
    let mut model = explorer(&fixture(), Some(9));
    select_group(&mut model, 9, 1);
    key(&mut model, KeyCode::Char('j'));
    key(&mut model, KeyCode::Enter);
    let note = screen(&mut model);
    for expected in [
        "Original note · HDFv1",
        "V1, VA · N002",
        "Source note ID: b",
        "⟦hot⟧ ⟦coffee⟧ full original",
    ] {
        assert!(note.contains(expected), "Missing {expected}: {note}");
    }
    assert!(!note.contains("⟧;"), "{note}");
    key(&mut model, KeyCode::Esc);
    key(&mut model, KeyCode::Char('a'));
    assert!(screen(&mut model).contains("V3 · N001  ⟦Parent A⟧"));
    key(&mut model, KeyCode::Char('a'));
    assert!(!screen(&mut model).contains("⟦Parent A⟧"));
    key(&mut model, KeyCode::Char('?'));
    let help = screen(&mut model);
    for expected in [
        "exact-containment DAG",
        "same ID",
        "Each route expands independently",
        "same notes",
        "all routes",
        "Nothing is written",
    ] {
        assert!(help.contains(expected), "Missing {expected}: {help}");
    }
}

#[test]
fn hiding_a_shared_point_in_one_group_does_not_hide_it_under_another_group() {
    let mut values = fixture();
    values.0["groups"][2]["vector_ids"] = json!([1, 2, 3, 4]);
    values.0["groups"][2]["note_ids"] = json!(["a", "b", "c", "d"]);
    let mut first = explorer(&values, Some(7));
    assert!(!screen(&mut first).contains("⟦Parent A⟧"));
    let mut second = explorer(&values, Some(8));
    assert!(screen(&mut second).contains("V3 · N001  ⟦Parent A⟧"));
    key(&mut second, KeyCode::Char('j'));
    key(&mut second, KeyCode::Char('h'));
    let text = screen(&mut second);
    assert!(
        text.lines()
            .any(|line| line.contains('▶') && line.contains("▾ 8")),
        "{text}"
    );
}

#[test]
fn invalid_memberships_edges_inventory_identity_and_source_bytes_are_rejected() {
    for (pointer, replacement, expected) in [
        (
            "/schema_version",
            json!("infomap-hierarchy-v1"),
            "schema_version",
        ),
        ("/run_id", json!(" "), "run_id"),
        ("/root", json!(7), "root"),
        (
            "/groups/0/vector_ids",
            json!([0, 1, 2, 3, 4]),
            "note membership mismatch",
        ),
        (
            "/groups/1/note_ids",
            json!(["a", "b"]),
            "note membership mismatch",
        ),
        ("/groups/1/vector_ids", json!([1, 0, 2, 3]), "unsorted"),
        ("/groups/1/vector_ids", json!([0, 1, 2, 6]), "invalid"),
        ("/groups/3/parents", json!([8]), "disagree"),
        ("/groups/3/parents", json!([]), "disagree"),
        ("/groups/1/children", json!([8, 10, 11]), "disagree"),
        (
            "/groups/3/children",
            json!([999]),
            "unknown containment child",
        ),
        ("/groups/5/id", json!(9), "duplicate"),
        ("/canonical_unique_ids/1", json!("missing"), "canonical"),
    ] {
        let mut values = fixture();
        *values.0.pointer_mut(pointer).unwrap() = replacement;
        let (_directory, paths) = saved_fixture(&values);
        let error = Hierarchy::load_containment_with_run_id(&paths[0], &paths[1], &paths[2])
            .unwrap_err()
            .to_string();
        assert!(error.contains(expected), "{pointer}: {error}");
    }
    let mut values = fixture();
    values.0["groups"][2]["vector_ids"] = json!([0, 1, 4]);
    values.0["groups"][2]["note_ids"] = json!(["a", "b", "d"]);
    let (_directory, paths) = saved_fixture(&values);
    let error = Hierarchy::load_containment_with_run_id(&paths[0], &paths[1], &paths[2])
        .unwrap_err()
        .to_string();
    assert!(error.contains("not strictly contained"), "{error}");
    for index in [1, 2] {
        let (_directory, paths) = saved_fixture(&fixture());
        let mut bytes = fs::read(&paths[index]).unwrap();
        bytes.push(b'\n');
        fs::write(&paths[index], bytes).unwrap();
        let output = run_cli(&paths, &["--containment", "--check"]);
        assert!(!output.status.success());
        assert!(String::from_utf8_lossy(&output.stderr).contains("source checksum mismatch"));
    }
}

#[test]
fn saved_root_ids_and_child_order_do_not_need_to_follow_containment_export_order() {
    let mut values = fixture();
    values.0["run_id"] = json!("GDC09");
    values.0["root"] = json!(16);
    values.0["groups"][0]["id"] = json!(16);
    values.0["groups"][0]["children"] = json!([8, 7]);
    values.0["groups"][1]["parents"] = json!([16]);
    values.0["groups"][2]["parents"] = json!([16]);
    let (_directory, paths) = saved_fixture(&values);
    let hierarchy = load(&paths);
    assert_eq!(hierarchy.root, 16);
    assert_eq!(hierarchy.groups[&16].children, [8, 7]);
    assert_eq!(hierarchy.groups[&7].children, [10]);
    assert_eq!(hierarchy.groups[&10].children, [9]);
    assert_eq!(
        hierarchy.groups[&7].note_count,
        hierarchy.groups[&10].note_count
    );
    assert_eq!(hierarchy.groups[&16].vector_count, 6);
    assert_eq!(hierarchy.groups[&16].note_count, 5);
    assert_eq!(hierarchy.vectors[&1].len(), 2);
    let output = run_cli(&paths, &["--containment", "--start-at", "7", "--check"]);
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert!(String::from_utf8_lossy(&output.stdout).contains("GDC09"));
    let mut model = HierarchyExplorer::new_containment(
        hierarchy,
        Some(7),
        load_note_short_ids(&paths[1]).unwrap(),
    )
    .unwrap()
    .with_run_id(Some("GDC09".to_owned()));
    key(&mut model, KeyCode::Char('?'));
    let help = screen(&mut model);
    assert!(help.contains("GDC09"), "{help}");
    assert!(!help.contains("HiDeF"), "{help}");
}

#[test]
fn duplicate_containment_children_still_fail_without_requiring_sorted_order() {
    let mut values = fixture();
    values.0["groups"][0]["children"] = json!([8, 7, 8]);
    let (_directory, paths) = saved_fixture(&values);
    let error = Hierarchy::load_containment_with_run_id(&paths[0], &paths[1], &paths[2])
        .unwrap_err()
        .to_string();
    assert!(error.contains("invalid"), "{error}");
}

#[test]
fn saved_diffusion_view_preserves_every_multinote_group_membership_and_native_id() {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let run = root.join("sse_multivector/geometric-hierarchy-v1/GDC09");
    let data = root.join("sse_multivector/real-note-fine-segmentation-v1");
    let paths = [
        run.join("viewer.json"),
        data.join("vectors/vector-map.json"),
        data.join("reviewed-input.json"),
    ];
    let before = paths
        .iter()
        .map(fs::read)
        .collect::<Result<Vec<_>, _>>()
        .unwrap();
    let hierarchy = load(&paths);
    let raw: Value =
        serde_json::from_slice(&fs::read(run.join("hierarchy.json")).unwrap()).unwrap();
    let nodes = raw["nodes"]
        .as_array()
        .unwrap()
        .iter()
        .map(|n| (n["id"].as_u64().unwrap() as usize, n))
        .collect::<std::collections::BTreeMap<_, _>>();
    let retained = nodes
        .iter()
        .filter(|(_, n)| n["note_ids"].as_array().unwrap().len() >= 2)
        .map(|(id, _)| *id)
        .collect::<std::collections::BTreeSet<_>>();
    assert_eq!(hierarchy.root, 1753);
    assert_eq!(hierarchy.groups.len(), 360);
    assert_eq!(
        hierarchy
            .groups
            .keys()
            .copied()
            .collect::<std::collections::BTreeSet<_>>(),
        retained
    );
    assert_eq!(hierarchy.groups[&1753].children, [1752]); // native 1748 contains one note
    assert_eq!(hierarchy.vectors.len(), 916);
    assert_eq!(hierarchy.vectors.values().map(Vec::len).sum::<usize>(), 945);
    assert_eq!(hierarchy.groups[&1753].note_count, 100);
    for (id, group) in &hierarchy.groups {
        let native = nodes[id];
        let children = native["children"]
            .as_array()
            .unwrap()
            .iter()
            .map(|c| c.as_u64().unwrap() as usize)
            .filter(|c| retained.contains(c))
            .collect::<Vec<_>>();
        assert_eq!(group.children, children, "children of {id}");
        assert_eq!(
            group.note_count,
            native["note_ids"].as_array().unwrap().len(),
            "notes at {id}"
        );
        let mut pending = vec![*id];
        let mut members = std::collections::BTreeSet::new();
        while let Some(child) = pending.pop() {
            members.extend(hierarchy.groups[&child].vectors.iter().copied());
            pending.extend(&hierarchy.groups[&child].children);
        }
        assert_eq!(
            serde_json::to_value(members).unwrap(),
            native["members"],
            "membership at {id}"
        );
    }
    for start in [1487, 1598, 1533, 1629, 1671, 1700, 1753] {
        let output = run_cli(
            &paths,
            &["--containment", "--start-at", &start.to_string(), "--check"],
        );
        assert!(
            output.status.success(),
            "{}",
            String::from_utf8_lossy(&output.stderr)
        );
    }
    let mut model = HierarchyExplorer::new_containment(
        hierarchy,
        Some(1487),
        load_note_short_ids(&paths[1]).unwrap(),
    )
    .unwrap()
    .with_run_id(Some("GDC09".to_owned()));
    let displayed = screen(&mut model);
    assert!(displayed.contains("GDC09"), "{displayed}");
    assert!(displayed.contains("1487 · 19 notes"), "{displayed}");
    key(&mut model, KeyCode::Char('u'));
    assert!(screen(&mut model).contains("1487 · 19 notes"));
    assert_eq!(
        before,
        paths
            .iter()
            .map(fs::read)
            .collect::<Result<Vec<_>, _>>()
            .unwrap()
    );
}

#[test]
fn containment_cli_rejects_conflicting_modes_before_loading_inputs() {
    let paths = ["missing", "missing-vectors", "missing-notes"].map(PathBuf::from);
    for options in [
        vec!["--containment", "--infomap"],
        vec!["--containment", "--note-navigation"],
        vec!["--containment", "--merge-history"],
        vec!["--containment", "--selection", "missing"],
        vec!["--containment", "--min-notes", "2"],
        vec!["--containment", "--containment"],
    ] {
        let output = run_cli(&paths, &options);
        assert!(!output.status.success());
        let error = String::from_utf8_lossy(&output.stderr);
        assert!(error.contains("--containment"), "{error}");
        assert!(!error.contains("No such file"), "{error}");
    }
}

#[test]
fn default_root_does_not_unfold_unopened_shared_routes() {
    let mut model = explorer(&fixture(), None);
    let text = screen(&mut model);
    assert!(text.contains("▾ 6 · 5 notes"), "{text}");
    assert!(text.contains("▸ 7 · 3 notes"), "{text}");
    assert!(text.contains("▸ 8 · 3 notes"), "{text}");
    assert!(!text.contains(" 9 ·"), "{text}");
    assert!(!text.contains(" 10 ·"), "{text}");
    assert!(text.contains("V5 · N005  ⟦spare⟧"), "{text}");
}

#[test]
fn shared_ancestry_opens_all_routes_even_when_the_requested_group_has_one_parent() {
    let mut values = fixture();
    values.1["vectors"][2]["note_id"] = json!("c");
    values.1["vectors"][2]["note_short_id"] = json!("N003");
    values.1["vectors"][2]["byte_spans"] = json!([[0, 3]]);
    values.1["vectors"][2]["fragments"] = json!(["tea"]);
    values.0["sources"]["vector_map"]["sha256"] = json!(format!(
        "{:x}",
        Sha256::digest(serde_json::to_vec(&values.1).unwrap())
    ));
    values.0["groups"][3]["children"] = json!([12]);
    values.0["groups"].as_array_mut().unwrap().push(json!({
        "id":12,"kind":"persistent","vector_ids":[1],"note_ids":["b","c"],"parents":[9],"children":[]
    }));
    let mut model = explorer(&values, Some(12));
    let text = screen(&mut model);
    assert!(text.contains("Showing branch 6 · 5 notes"), "{text}");
    assert_eq!(
        text.matches("▾ 12 · 2 notes · same notes").count(),
        2,
        "{text}"
    );
    assert_eq!(
        text.matches("V1 · N002  ⟦hot⟧ ⟦coffee⟧").count(),
        2,
        "{text}"
    );
    assert_eq!(text.matches("VA · N003  ⟦tea⟧").count(), 2, "{text}");
    assert!(!text.contains("V2 ·"), "{text}"); // that parent mask repeats note c
}

#[test]
fn saved_seed_identity_is_kept_and_check_does_not_claim_a_shared_branch_was_chosen() {
    let mut values = fixture();
    values.0["run_id"] = json!("HDFv1-seed125");
    let (_directory, paths) = saved_fixture(&values);
    let output = run_cli(&paths, &["--containment", "--start-at", "9", "--check"]);
    assert!(output.status.success());
    let text = String::from_utf8_lossy(&output.stdout);
    assert!(text.contains("HDFv1-seed125"), "{text}");
    assert!(text.contains("Requested start group 9"), "{text}");
    assert!(text.contains("shared ancestry opens root"), "{text}");
    let (hierarchy, run_id) =
        Hierarchy::load_containment_with_run_id(&paths[0], &paths[1], &paths[2]).unwrap();
    let mut model = HierarchyExplorer::new_containment(
        hierarchy,
        Some(9),
        load_note_short_ids(&paths[1]).unwrap(),
    )
    .unwrap()
    .with_run_id(run_id);
    assert!(screen(&mut model).contains("Containment hierarchy · HDFv1-seed125"));
    select_group(&mut model, 9, 2);
    key(&mut model, KeyCode::Char('j'));
    key(&mut model, KeyCode::Enter);
    assert!(screen(&mut model).contains("Original note · HDFv1-seed125"));
}
