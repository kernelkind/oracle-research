use std::collections::BTreeSet;
use std::fs;
use std::path::PathBuf;
use std::process::Command;

use crossterm::event::{Event, KeyCode, KeyEvent, KeyModifiers};
use oracle_mvp::hdbscan_hierarchy::Hierarchy;
use oracle_mvp::hdbscan_hierarchy_tui::HierarchyExplorer;
use ratatui::{Terminal, backend::TestBackend};
use serde_json::json;

fn fixture() -> (tempfile::TempDir, [PathBuf; 3]) {
    let directory = tempfile::tempdir().unwrap();
    let paths =
        ["history.json", "vectors.json", "notes.json"].map(|name| directory.path().join(name));
    let pairs = [(0, 1), (2, 3), (8, 9), (4, 5), (10, 11), (6, 12), (7, 13)];
    let mut sizes = vec![1; 15];
    let merges: Vec<_> = pairs
        .into_iter()
        .enumerate()
        .map(|(offset, (left, right))| {
            let id = 8 + offset;
            sizes[id] = sizes[left] + sizes[right];
            json!({"id":id,"left":left,"right":right,"size":sizes[id],"merge_score":0.1})
        })
        .collect();
    let ids: Vec<_> = (0..8).map(|i| format!("v{i}")).collect();
    let mut aliases: Vec<_> = ids.iter().map(|id| vec![id.clone()]).collect();
    aliases[6].push("alias".into());
    let mut vectors: Vec<_> = ["a", "a", "b", "c", "d", "e", "f", "g"]
        .into_iter()
        .enumerate()
        .map(|(i, note)| {
            json!({"vector_id":format!("v{i}"),"short_id":format!("V{i}"),
                "note_id":note,"byte_spans":[[0,1]],"fragments":[note]})
        })
        .collect();
    vectors.push(json!({"vector_id":"alias","short_id":"VA","note_id":"b",
        "byte_spans":[[0,1]],"fragments":["b"]}));
    let notes: Vec<_> = ["a", "b", "c", "d", "e", "f", "g"]
        .into_iter()
        .map(|note| json!({"note_id":note,"text":note}))
        .collect();
    let values = [
        json!({"vector_count":8,"canonical_unique_ids":ids,"alias_groups":aliases,"merges":merges}),
        json!({"vectors":vectors}),
        json!({"notes":notes}),
    ];
    for (path, value) in paths.iter().zip(values) {
        fs::write(path, serde_json::to_vec(&value).unwrap()).unwrap();
    }
    (directory, paths)
}

#[test]
fn minimum_five_notes_keeps_the_boundary_group_and_every_source() {
    let (_directory, paths) = fixture();
    let before: Vec<_> = paths.iter().map(|p| fs::read(p).unwrap()).collect();
    let output = Command::new(env!("CARGO_BIN_EXE_hdbscan-hierarchy"))
        .args(&paths)
        .args([
            "--merge-history",
            "--min-notes",
            "5",
            "--start-at",
            "12",
            "--check",
        ])
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let text = String::from_utf8_lossy(&output.stdout);
    for expected in [
        "Minimum group size: 5 distinct notes",
        "3 groups",
        "8 unique vectors",
        "9 original IDs",
        "7 notes",
        "Starting branch 12",
    ] {
        assert!(text.contains(expected), "Missing {expected}: {text}");
    }
    assert_eq!(
        before,
        paths
            .iter()
            .map(|p| fs::read(p).unwrap())
            .collect::<Vec<_>>()
    );
}

fn load(paths: &[PathBuf; 3], minimum: usize) -> Hierarchy {
    Hierarchy::load_merge_history_with_min_notes(&paths[0], &paths[1], &paths[2], minimum).unwrap()
}

fn members(hierarchy: &Hierarchy, start: usize) -> BTreeSet<usize> {
    let mut points = BTreeSet::new();
    let mut pending = vec![start];
    while let Some(id) = pending.pop() {
        let group = &hierarchy.groups[&id];
        points.extend(&group.vectors);
        pending.extend(&group.children);
    }
    points
}

#[test]
fn hidden_groups_transfer_every_point_to_the_nearest_retained_ancestor() {
    let (_directory, paths) = fixture();
    let before = Hierarchy::load_merge_history(&paths[0], &paths[1], &paths[2]).unwrap();
    let after = load(&paths, 5);
    assert_eq!(
        after.groups.keys().copied().collect::<Vec<_>>(),
        [12, 13, 14]
    );
    assert_eq!(after.groups[&12].vectors, [0, 1, 2, 3, 4, 5]);
    assert!(after.groups[&12].children.is_empty());
    assert_eq!(after.groups[&13].vectors, [6]);
    assert_eq!(after.groups[&13].children, [12]);
    assert_eq!(after.groups[&14].vectors, [7]);
    assert_eq!(after.groups[&14].children, [13]);
    for (&id, group) in &after.groups {
        assert_eq!(members(&before, id), members(&after, id));
        assert_eq!(group.note_count, before.groups[&id].note_count);
        assert_eq!(group.vector_count, before.groups[&id].vector_count);
        assert_eq!(group.parent, before.groups[&id].parent);
    }
    for (id, originals) in &before.vectors {
        for (old, new) in originals.iter().zip(&after.vectors[id]) {
            assert_eq!(old.vector_id, new.vector_id);
            assert_eq!(old.note_id, new.note_id);
            assert_eq!(old.text, new.text);
            assert_eq!(old.fragments, new.fragments);
            assert_eq!(old.byte_spans, new.byte_spans);
        }
    }
    assert_eq!(
        after
            .groups
            .values()
            .map(|g| g.vectors.len())
            .sum::<usize>(),
        8
    );
}

#[test]
fn note_minimum_counts_distinct_notes_not_points_or_original_masks() {
    let (_directory, paths) = fixture();
    // Group 10 has four points but only notes a/b/c. Group 12 has six
    // points but five notes. Neither may satisfy a larger note minimum.
    assert!(!load(&paths, 4).groups.contains_key(&10));
    assert!(!load(&paths, 6).groups.contains_key(&12));
    // An alias from a genuinely different source note does count.
    let mut vectors: serde_json::Value =
        serde_json::from_slice(&fs::read(&paths[1]).unwrap()).unwrap();
    vectors["vectors"][8]["note_id"] = json!("h");
    vectors["vectors"][8]["fragments"] = json!(["h"]);
    let mut notes: serde_json::Value =
        serde_json::from_slice(&fs::read(&paths[2]).unwrap()).unwrap();
    notes["notes"]
        .as_array_mut()
        .unwrap()
        .push(json!({"note_id":"h","text":"h"}));
    fs::write(&paths[1], serde_json::to_vec(&vectors).unwrap()).unwrap();
    fs::write(&paths[2], serde_json::to_vec(&notes).unwrap()).unwrap();
    assert_eq!(load(&paths, 7).groups[&13].note_count, 7);
}

#[test]
fn corpus_smaller_than_minimum_remains_accessible_at_root() {
    let (_directory, paths) = fixture();
    let hierarchy = load(&paths, 8);
    assert_eq!(hierarchy.groups.keys().copied().collect::<Vec<_>>(), [14]);
    assert_eq!(hierarchy.groups[&14].note_count, 7);
    assert_eq!(hierarchy.groups[&14].vectors, (0..8).collect::<Vec<_>>());
    assert_eq!(hierarchy.vectors.values().map(Vec::len).sum::<usize>(), 9);
}

#[test]
fn invalid_minimum_options_and_hidden_starting_groups_are_explained() {
    let (_directory, paths) = fixture();
    let cases: &[(&[&str], &str)] = &[
        (&["--merge-history", "--min-notes", "0"], "at least 2"),
        (&["--merge-history", "--min-notes", "1"], "at least 2"),
        (
            &["--merge-history", "--min-notes", "5", "--min-notes", "5"],
            "repeated option",
        ),
        (
            &["--min-notes", "5"],
            "requires --note-navigation or --merge-history",
        ),
        (
            &["--selection", "unused", "--min-notes", "5"],
            "requires --note-navigation or --merge-history",
        ),
        (
            &["--merge-history", "--min-notes", "5", "--start-at", "10"],
            "omit --start-at to open the root",
        ),
    ];
    for (options, expected) in cases {
        let output = Command::new(env!("CARGO_BIN_EXE_hdbscan-hierarchy"))
            .args(&paths)
            .args(*options)
            .arg("--check")
            .output()
            .unwrap();
        assert!(!output.status.success());
        assert!(
            String::from_utf8_lossy(&output.stderr).contains(expected),
            "{:?}: {}",
            options,
            String::from_utf8_lossy(&output.stderr)
        );
    }
    let missing = Command::new(env!("CARGO_BIN_EXE_hdbscan-hierarchy"))
        .args(&paths)
        .args(["--merge-history", "--min-notes"])
        .output()
        .unwrap();
    assert!(!missing.status.success());
    assert!(String::from_utf8_lossy(&missing.stderr).contains("requires a count"));
    assert!(
        Hierarchy::load_merge_history_with_min_notes(&paths[0], &paths[1], &paths[2], 1).is_err()
    );
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
fn hidden_groups_notes_render_inline_and_keep_full_original_access() {
    let (_directory, paths) = fixture();
    let mut model = HierarchyExplorer::new_note_navigation(load(&paths, 5), Some(12)).unwrap();
    let shown = screen(&mut model);
    for id in ["V0", "V1", "V2", "V3", "V4", "V5"] {
        assert!(shown.contains(id), "Missing {id}: {shown}");
    }
    assert!(!shown.contains("▸ 10"));
    key(&mut model, KeyCode::Char('j'));
    key(&mut model, KeyCode::Enter);
    let note = screen(&mut model);
    assert!(note.contains("Original note"), "{note}");
    assert!(note.contains("⟦a⟧"), "{note}");
    key(&mut model, KeyCode::Esc);
    key(&mut model, KeyCode::Char('u'));
    let parent = screen(&mut model);
    assert!(parent.contains("13 · 6 notes"), "{parent}");
    assert!(parent.contains("V6"), "{parent}");
    assert!(
        !parent.contains("VA"),
        "alias note b is already accessible in child 12: {parent}"
    );
    // Once all children are hidden, b's alias must become visible again.
    let mut root = HierarchyExplorer::new_note_navigation(load(&paths, 8), None).unwrap();
    assert!(screen(&mut root).contains("VA"));
}

#[test]
fn real_m06_view_preserves_every_retained_membership_and_input_byte() {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let base = root.join("sse_multivector/real-note-fine-segmentation-v1");
    let paths = [
        root.join("sse_multivector/merge-rule-exploration-v1/M06.json"),
        base.join("vectors/vector-map.json"),
        base.join("reviewed-input.json"),
    ];
    let original_bytes: Vec<_> = paths.iter().map(|p| fs::read(p).unwrap()).collect();
    let original = Hierarchy::load_merge_history(&paths[0], &paths[1], &paths[2]).unwrap();
    let displayed = load(&paths, 5);
    assert_eq!(original.groups.len(), 488);
    assert_eq!(displayed.groups.len(), 150);
    assert_eq!(displayed.groups[&displayed.root].note_count, 100);
    assert_eq!(displayed.vectors.len(), 916);
    assert_eq!(displayed.vectors.values().map(Vec::len).sum::<usize>(), 945);
    assert_eq!(
        displayed.groups[&displayed.root].children,
        [1823, 1824, 1822, 1818, 1816, 1813, 1803, 1812]
    );
    for (&id, group) in &displayed.groups {
        assert!(group.note_count >= 5);
        assert_eq!(members(&original, id), members(&displayed, id));
        let mut expected_parent = original.groups[&id].parent;
        while let Some(parent) = expected_parent {
            if displayed.groups.contains_key(&parent) {
                break;
            }
            expected_parent = original.groups[&parent].parent;
        }
        assert_eq!(group.parent, expected_parent);
    }
    assert_eq!(
        displayed
            .groups
            .values()
            .map(|g| g.vectors.len())
            .sum::<usize>(),
        916
    );
    assert_eq!(members(&displayed, displayed.root).len(), 916);
    assert_eq!(
        displayed
            .groups
            .values()
            .filter(|g| g.children.is_empty())
            .count(),
        39
    );
    assert_eq!(
        original_bytes,
        paths
            .iter()
            .map(|p| fs::read(p).unwrap())
            .collect::<Vec<_>>()
    );
}

#[test]
fn saved_hdbscan_and_scored_history_use_the_same_minimum_projection() {
    let (_directory, paths) = fixture();
    let history: serde_json::Value = serde_json::from_slice(&fs::read(&paths[0]).unwrap()).unwrap();
    let mut rows = history["merges"].clone();
    for row in rows.as_array_mut().unwrap() {
        row["mutual_reachability_distance"] = row["merge_score"].clone();
    }
    let response = json!({"artifact":{"result":{
        "canonical_unique_ids":history["canonical_unique_ids"],
        "alias_groups":history["alias_groups"],
        "algorithm_result":{"vector_count":8,"single_linkage_tree":rows}
    }}});
    let response_path = paths[0].with_file_name("response.json");
    fs::write(&response_path, serde_json::to_vec(&response).unwrap()).unwrap();
    let hdbscan =
        Hierarchy::load_note_navigation_with_min_notes(&response_path, &paths[1], &paths[2], 5)
            .unwrap();
    let scored = load(&paths, 5);
    assert_eq!(
        hdbscan.groups.keys().collect::<Vec<_>>(),
        scored.groups.keys().collect::<Vec<_>>()
    );
    for (&id, group) in &hdbscan.groups {
        assert_eq!(group.parent, scored.groups[&id].parent);
        assert_eq!(group.children, scored.groups[&id].children);
        assert_eq!(group.vectors, scored.groups[&id].vectors);
        assert_eq!(members(&hdbscan, id), members(&scored, id));
    }
    let output = Command::new(env!("CARGO_BIN_EXE_hdbscan-hierarchy"))
        .args([&response_path, &paths[1], &paths[2]])
        .args(["--note-navigation", "--min-notes", "5", "--check"])
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert!(String::from_utf8_lossy(&output.stdout).contains("3 groups"));
}
