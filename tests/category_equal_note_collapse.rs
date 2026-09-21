use std::fs;
use std::path::PathBuf;
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

fn structure(edit: impl FnOnce(&mut Value)) -> Fixture {
    Fixture::new(|data| {
        data.as_object_mut().unwrap().remove("note_masks");
        data.as_object_mut().unwrap().remove("mask_instances");
        edit(data);
    })
}

fn key(model: &mut ManualNoteExplorer, code: KeyCode) {
    assert!(!model.handle_event(Event::Key(KeyEvent::new(code, KeyModifiers::NONE))));
}

fn screen(model: &mut ManualNoteExplorer) -> String {
    let mut terminal = Terminal::new(TestBackend::new(110, 34)).unwrap();
    terminal.draw(|frame| model.render(frame)).unwrap();
    let buffer = terminal.backend().buffer();
    (0..34)
        .map(|y| {
            (0..110)
                .map(|x| buffer[(x, y)].symbol())
                .collect::<String>()
        })
        .collect::<Vec<_>>()
        .join("\n")
}

impl Fixture {
    fn new(edit: impl FnOnce(&mut Value)) -> Self {
        let directory = tempfile::tempdir().unwrap();
        let source = directory.path().join("source.json");
        let spec = directory.path().join("categories.json");
        let bytes = serde_json::to_vec(&json!({"notes": [
            {"note_id": "one", "text": "alpha delta"},
            {"note_id": "two", "text": "gamma"},
            {"note_id": "three", "text": "beta"},
            {"note_id": "four", "text": "epsilon"}
        ]}))
        .unwrap();
        fs::write(&source, &bytes).unwrap();
        let mut data = json!({
            "schema_version": 2,
            "hierarchy_id": "shared-child-collapse",
            "source_sha256": format!("{:x}", Sha256::digest(&bytes)),
            "root_node_id": "root",
            "notes": [
                {"note_id": "one", "note_short_id": "N001"},
                {"note_id": "two", "note_short_id": "N002"},
                {"note_id": "three", "note_short_id": "N003"},
                {"note_id": "four", "note_short_id": "N004"}
            ],
            "nodes": [
                {"node_id": "root", "label": "All notes", "children": ["A", "B"], "note_ids": ["N004"]},
                {"node_id": "A", "label": "Parent A", "children": ["C"], "note_ids": ["N001"]},
                {"node_id": "B", "label": "Parent B", "children": ["C"], "note_ids": ["N003"]},
                {"node_id": "C", "label": "Shared C", "children": ["D"], "note_ids": ["N002"]},
                {"node_id": "D", "label": "Child D", "children": [], "note_ids": ["N001"]}
            ],
            "note_masks": {
                "root": {"N001": [[0,5],[6,11]], "N002": [[0,5]], "N003": [[0,4]], "N004": [[0,7]]},
                "A": {"N001": [[0,5],[6,11]], "N002": [[0,5]]},
                "B": {"N001": [[6,11]], "N002": [[0,5]], "N003": [[0,4]]},
                "C": {"N001": [[6,11]], "N002": [[0,5]]},
                "D": {"N001": [[6,11]]}
            },
            "mask_instances": {
                "root": {"N001": [{"ids":["VA"],"byte_spans":[[0,5]]},{"ids":["VD"],"byte_spans":[[6,11]]}], "N002": [{"ids":["VC"],"byte_spans":[[0,5]]}], "N003": [{"ids":["VB"],"byte_spans":[[0,4]]}], "N004": [{"ids":["VE"],"byte_spans":[[0,7]]}]},
                "A": {"N001": [{"ids":["VA"],"byte_spans":[[0,5]]},{"ids":["VD"],"byte_spans":[[6,11]]}], "N002": [{"ids":["VC"],"byte_spans":[[0,5]]}]},
                "B": {"N001": [{"ids":["VD"],"byte_spans":[[6,11]]}], "N002": [{"ids":["VC"],"byte_spans":[[0,5]]}], "N003": [{"ids":["VB"],"byte_spans":[[0,4]]}]},
                "C": {"N001": [{"ids":["VD"],"byte_spans":[[6,11]]}], "N002": [{"ids":["VC"],"byte_spans":[[0,5]]}]},
                "D": {"N001": [{"ids":["VD"],"byte_spans":[[6,11]]}]}
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

#[test]
fn cli_collapses_only_the_equal_route_without_rewriting_saved_data() {
    let fixture = Fixture::new(|_| {});
    let before = [
        fs::read(&fixture.spec).unwrap(),
        fs::read(&fixture.source).unwrap(),
    ];
    let output = Command::new(env!("CARGO_BIN_EXE_sse-subject-navigation"))
        .arg("--categories")
        .arg(&fixture.spec)
        .arg(&fixture.source)
        .args(["--collapse-equal-note-steps", "--check"])
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(
        stdout.contains("Parent A · 2 notes\n  Children: D"),
        "{stdout}"
    );
    assert!(
        stdout.contains("Parent B · 3 notes\n  Children: C"),
        "{stdout}"
    );
    assert!(stdout.contains("Collapsed here: C"), "{stdout}");
    assert!(stdout.contains("Notes outside children: N002"), "{stdout}");
    assert_eq!(
        before,
        [
            fs::read(&fixture.spec).unwrap(),
            fs::read(&fixture.source).unwrap()
        ]
    );
}

#[test]
fn projection_keeps_raw_nodes_direct_memberships_and_exact_masks_unchanged() {
    let fixture = Fixture::new(|_| {});
    let (hierarchy, masks) =
        ManualNoteHierarchy::load_with_masks(&fixture.spec, &fixture.source).unwrap();
    let before = format!("{hierarchy:?}{masks:?}");
    let a = hierarchy.category_navigation("A", true);
    assert_eq!(a.children, ["D"]);
    assert_eq!(a.collapsed, ["C"]);
    assert_eq!(a.outside_note_ids, ["N002"]);
    let b = hierarchy.category_navigation("B", true);
    assert_eq!(b.children, ["C"]);
    assert!(b.collapsed.is_empty());
    assert_eq!(b.outside_note_ids, ["N003"]);
    assert_eq!(hierarchy.nodes["A"].children, ["C"]);
    assert_eq!(hierarchy.nodes["A"].note_ids, ["N001"]);
    assert_eq!(hierarchy.note_ids("A"), ["N001", "N002"]);
    assert_eq!(hierarchy.category_navigation("A", false).children, ["C"]);
    assert!(
        hierarchy
            .category_navigation("A", false)
            .outside_note_ids
            .is_empty()
    );
    assert_eq!(format!("{hierarchy:?}{masks:?}"), before);
}

#[test]
fn tui_preserves_n_d_masks_other_route_and_back_while_o_uses_displayed_children() {
    let fixture = Fixture::new(|_| {});
    let (hierarchy, masks) =
        ManualNoteHierarchy::load_with_masks(&fixture.spec, &fixture.source).unwrap();
    let mut model = ManualNoteExplorer::categories_with_masks(hierarchy, masks, true);
    let root = screen(&mut model);
    key(&mut model, KeyCode::Enter);
    let a = screen(&mut model);
    assert!(a.contains("All notes > Parent A"), "{a}");
    assert!(a.contains("[D] Child D"), "{a}");
    assert!(!a.contains("Shared C"), "{a}");
    key(&mut model, KeyCode::Char('?'));
    let analysis = screen(&mut model);
    assert!(analysis.contains("Saved children: C"), "{analysis}");
    assert!(
        analysis.contains("[C] Shared C · saved children: D"),
        "{analysis}"
    );
    key(&mut model, KeyCode::Esc);
    assert_eq!(screen(&mut model), a);

    key(&mut model, KeyCode::Char('N'));
    let n = screen(&mut model);
    assert!(n.contains("Note 1 of 2"), "{n}");
    assert!(n.contains("⟦alpha⟧ ⟦delta⟧"), "{n}");
    key(&mut model, KeyCode::Right);
    let inherited = screen(&mut model);
    assert!(inherited.contains("⟦gamma⟧"), "{inherited}");
    key(&mut model, KeyCode::Esc);

    key(&mut model, KeyCode::Char('D'));
    let direct = screen(&mut model);
    assert!(direct.contains("Direct notes"), "{direct}");
    assert!(direct.contains("N001 · Note 1 of 1"), "{direct}");
    assert!(direct.contains("⟦alpha⟧ ⟦delta⟧"), "{direct}");
    key(&mut model, KeyCode::Esc);

    key(&mut model, KeyCode::Char('O'));
    let outside = screen(&mut model);
    assert!(
        outside.contains("N002 · Note 1 of 1 · VC · Mask 1 of 1"),
        "{outside}"
    );
    assert!(outside.contains("⟦gamma⟧"), "{outside}");
    key(&mut model, KeyCode::Esc);
    assert_eq!(screen(&mut model), a);
    key(&mut model, KeyCode::Enter);
    let promoted = screen(&mut model);
    assert!(
        promoted.contains("All notes > Parent A > Child D"),
        "{promoted}"
    );
    key(&mut model, KeyCode::Char('O'));
    let leaf = screen(&mut model);
    assert!(leaf.contains("VD · Mask 1 of 1"), "{leaf}");
    assert!(leaf.contains("alpha ⟦delta⟧"), "{leaf}");
    key(&mut model, KeyCode::Esc);
    key(&mut model, KeyCode::Esc);
    assert_eq!(screen(&mut model), a);
    key(&mut model, KeyCode::Esc);
    assert_eq!(screen(&mut model), root);

    key(&mut model, KeyCode::Down);
    let root_b_selected = screen(&mut model);
    key(&mut model, KeyCode::Enter);
    let b = screen(&mut model);
    assert!(b.contains("[C] Shared C"), "{b}");
    key(&mut model, KeyCode::Char('N'));
    let b_note = screen(&mut model);
    assert!(b_note.contains("Note 1 of 3"), "{b_note}");
    assert!(b_note.contains("alpha ⟦delta⟧"), "{b_note}");
    assert!(!b_note.contains("⟦alpha⟧"), "{b_note}");
    key(&mut model, KeyCode::Esc);
    key(&mut model, KeyCode::Enter);
    let shared = screen(&mut model);
    assert!(
        shared.contains("All notes > Parent B > Shared C"),
        "{shared}"
    );
    key(&mut model, KeyCode::Char('D'));
    let c_direct = screen(&mut model);
    assert!(c_direct.contains("N002 · Note 1 of 1"), "{c_direct}");
    key(&mut model, KeyCode::Esc);
    key(&mut model, KeyCode::Esc);
    assert_eq!(screen(&mut model), b);
    key(&mut model, KeyCode::Esc);
    assert_eq!(screen(&mut model), root_b_selected);
}

#[test]
fn equal_chains_including_leaves_collapse_without_losing_note_access() {
    let fixture = structure(|data| data["nodes"][4]["note_ids"] = json!(["N001", "N002"]));
    let hierarchy = ManualNoteHierarchy::load(&fixture.spec, &fixture.source).unwrap();
    let a = hierarchy.category_navigation("A", true);
    assert!(a.children.is_empty());
    assert_eq!(a.collapsed, ["C", "D"]);
    assert_eq!(a.outside_note_ids, ["N001", "N002"]);
    let mut model = ManualNoteExplorer::categories_with_masks(hierarchy, None, true);
    screen(&mut model);
    key(&mut model, KeyCode::Enter);
    let menu = screen(&mut model);
    assert!(menu.contains("No child categories"), "{menu}");
    key(&mut model, KeyCode::Enter);
    assert_eq!(screen(&mut model), menu);
    key(&mut model, KeyCode::Char('O'));
    assert!(screen(&mut model).contains("Note 1 of 2"));
}

#[test]
fn repeated_promoted_ids_deduplicate_but_equal_sibling_sets_and_titles_do_not() {
    let fixture = structure(|data| {
        data["nodes"].as_array_mut().unwrap().push(json!({
            "node_id":"E", "label":"Shared C", "children":["D"], "note_ids":["N002"]
        }));
        data["nodes"][1]["children"] = json!(["C", "E"]);
        data["nodes"][2]["children"] = json!(["C", "E"]);
    });
    let hierarchy = ManualNoteHierarchy::load(&fixture.spec, &fixture.source).unwrap();
    let a = hierarchy.category_navigation("A", true);
    assert_eq!(a.children, ["D"]);
    assert_eq!(a.collapsed, ["C", "E"]);
    assert_eq!(hierarchy.nodes["C"].children, ["D"]);
    assert_eq!(hierarchy.nodes["E"].children, ["D"]);
    let b = hierarchy.category_navigation("B", true);
    assert_eq!(b.children, ["C", "E"]);
    assert!(b.collapsed.is_empty());
}

#[test]
fn promotion_keeps_saved_order_and_distinct_ids_with_different_note_sets() {
    let fixture = structure(|data| {
        data["nodes"].as_array_mut().unwrap().push(json!({
            "node_id":"E", "label":"Second child", "children":[], "note_ids":["N002"]
        }));
        data["nodes"][1]["children"] = json!(["E", "C"]);
    });
    let hierarchy = ManualNoteHierarchy::load(&fixture.spec, &fixture.source).unwrap();
    assert_eq!(
        hierarchy.category_navigation("A", true).children,
        ["E", "D"]
    );
    assert_eq!(hierarchy.note_ids("E").len(), hierarchy.note_ids("D").len());
    assert_ne!(hierarchy.note_ids("E"), hierarchy.note_ids("D"));
}

#[test]
fn root_survives_even_when_every_child_step_is_equal() {
    let fixture = structure(|data| {
        for node in data["nodes"].as_array_mut().unwrap() {
            node["note_ids"] = json!(["N001", "N002", "N003", "N004"]);
        }
    });
    let hierarchy = ManualNoteHierarchy::load(&fixture.spec, &fixture.source).unwrap();
    let root = hierarchy.category_navigation("root", true);
    assert!(root.children.is_empty());
    assert_eq!(root.collapsed, ["A", "C", "D", "B"]);
    assert_eq!(root.outside_note_ids, ["N001", "N002", "N003", "N004"]);
    assert_eq!(hierarchy.nodes.len(), 5);
    let mut model = ManualNoteExplorer::categories_with_masks(hierarchy, None, true);
    let menu = screen(&mut model);
    assert!(menu.contains("All notes [root] · 4 notes"), "{menu}");
    assert!(menu.contains("No child categories"), "{menu}");
    key(&mut model, KeyCode::Char('N'));
    assert!(screen(&mut model).contains("Note 1 of 4"));
    key(&mut model, KeyCode::Esc);
    key(&mut model, KeyCode::Esc);
    assert_eq!(screen(&mut model), menu);
}

#[test]
fn collapse_is_opt_in_and_cannot_be_combined_with_destructive_absorption() {
    let fixture = Fixture::new(|_| {});
    let run = |mode, flags: &[&str]| {
        Command::new(env!("CARGO_BIN_EXE_sse-subject-navigation"))
            .arg(mode)
            .arg(&fixture.spec)
            .arg(&fixture.source)
            .args(flags)
            .output()
            .unwrap()
    };
    let raw = run("--categories", &["--check"]);
    assert!(raw.status.success());
    let stdout = String::from_utf8_lossy(&raw.stdout);
    assert!(
        stdout.contains("Parent A · 2 notes\n  Children: C"),
        "{stdout}"
    );
    assert!(!stdout.contains("Collapsed here"), "{stdout}");
    let both = run(
        "--categories",
        &[
            "--collapse-equal-note-steps",
            "--absorb-single-children",
            "--check",
        ],
    );
    assert!(!both.status.success());
    assert!(String::from_utf8_lossy(&both.stderr).contains("choose either"));
    assert!(
        !run("--notes", &["--collapse-equal-note-steps", "--check"])
            .status
            .success()
    );
}

#[test]
fn cycles_are_rejected_before_navigation_is_built() {
    let fixture = structure(|data| data["nodes"][4]["children"] = json!(["A"]));
    let output = Command::new(env!("CARGO_BIN_EXE_sse-subject-navigation"))
        .arg("--categories")
        .arg(&fixture.spec)
        .arg(&fixture.source)
        .args(["--collapse-equal-note-steps", "--check"])
        .output()
        .unwrap();
    assert!(!output.status.success());
    assert!(String::from_utf8_lossy(&output.stderr).contains("cycle"));
}

#[test]
fn refresh_launcher_uses_the_same_navigation_rule_for_both_views() {
    let fixture = Fixture::new(|_| {});
    let root = fixture.spec.parent().unwrap();
    let sse = root.join("sse_multivector");
    let run = sse.join("hierarchy-refresh-v1");
    let original = sse.join("real-note-fine-segmentation-v1");
    let binary_dir = root.join("target/infomap-review-build/debug");
    for directory in [&run, &original, &binary_dir] {
        fs::create_dir_all(directory).unwrap();
    }
    for name in ["categories.json", "baseline-categories.json"] {
        fs::copy(&fixture.spec, run.join(name)).unwrap();
    }
    fs::copy(&fixture.source, run.join("masked-posts.json")).unwrap();
    fs::copy(&fixture.source, original.join("reviewed-input.json")).unwrap();
    std::os::unix::fs::symlink(
        env!("CARGO_BIN_EXE_sse-subject-navigation"),
        binary_dir.join("sse-subject-navigation"),
    )
    .unwrap();
    let launcher = sse.join("run-hierarchy-refresh.sh");
    fs::copy(
        std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
            .join("sse_multivector/run-hierarchy-refresh.sh"),
        &launcher,
    )
    .unwrap();
    for baseline in [false, true] {
        let mut command = Command::new("bash");
        command.arg(&launcher).arg("--check").current_dir("/");
        if baseline {
            command.arg("--baseline");
        }
        let output = command.output().unwrap();
        assert!(
            output.status.success(),
            "{}",
            String::from_utf8_lossy(&output.stderr)
        );
        let stdout = String::from_utf8_lossy(&output.stdout);
        assert!(
            stdout.contains("Equal-note navigation collapse enabled"),
            "{stdout}"
        );
        assert!(
            stdout.contains("Parent A · 2 notes\n  Children: D"),
            "{stdout}"
        );
        assert!(
            stdout.contains("Parent B · 3 notes\n  Children: C"),
            "{stdout}"
        );
    }
}
