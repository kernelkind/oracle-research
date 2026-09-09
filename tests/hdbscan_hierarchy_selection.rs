use std::collections::BTreeSet;
use std::fs;
use std::path::{Path, PathBuf};

use oracle_mvp::hdbscan_hierarchy::Hierarchy;
use serde_json::{Value, json};
use tempfile::tempdir;

fn paths() -> [PathBuf; 4] {
    let base = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("sse_multivector/real-note-fine-segmentation-v1");
    [
        base.join("hdbscan-cross-note/response.json"),
        base.join("vectors/vector-map.json"),
        base.join("reviewed-input.json"),
        base.join("cross-note-density-v1/hierarchy-selection-v1.json"),
    ]
}

fn points(tree: &Hierarchy, id: usize) -> BTreeSet<usize> {
    let mut pending = vec![id];
    let mut result = BTreeSet::new();
    while let Some(id) = pending.pop() {
        let group = &tree.groups[&id];
        pending.extend(&group.children);
        for point in &group.vectors {
            assert!(result.insert(*point));
        }
    }
    result
}

#[test]
fn selected_view_preserves_complete_memberships_aliases_and_nested_children() {
    let p = paths();
    let raw = Hierarchy::load(&p[0], &p[1], &p[2]).unwrap();
    let selected = Hierarchy::load_selection(&p[0], &p[1], &p[2], &p[3]).unwrap();
    assert_eq!(selected.groups.len(), 55);
    assert_eq!(selected.groups[&916].children.len(), 34);
    assert_eq!(selected.groups[&916].vectors.len(), 600);
    assert_eq!(selected.groups[&1030].children, [1038, 1043]);
    assert_eq!(selected.groups[&1043].parent, Some(1030));
    assert_eq!(selected.groups[&1043].children, [1044, 1045]);
    assert!(!selected.groups.contains_key(&1039));
    assert_eq!(raw.groups[&1043].parent, Some(1039));
    for (&id, group) in &selected.groups {
        assert_eq!(
            points(&selected, id),
            points(&raw, id),
            "Group {id} changed membership"
        );
        assert_eq!(group.note_count, raw.groups[&id].note_count);
    }
    assert_eq!(points(&selected, 916), (0..916).collect());
    for (point, masks) in &raw.vectors {
        let actual = &selected.vectors[point];
        assert_eq!(actual.len(), masks.len());
        for (a, b) in actual.iter().zip(masks) {
            assert_eq!(
                (
                    &a.id,
                    &a.vector_id,
                    &a.note_id,
                    &a.text,
                    &a.byte_spans,
                    &a.fragments
                ),
                (
                    &b.id,
                    &b.vector_id,
                    &b.note_id,
                    &b.text,
                    &b.byte_spans,
                    &b.fragments
                )
            );
        }
    }
}

#[test]
fn selection_rejects_mismatched_source_checksums() {
    let mut p = paths();
    let dir = tempdir().unwrap();
    let mut bytes = fs::read(&p[2]).unwrap();
    bytes.push(b' ');
    p[2] = dir.path().join("changed-notes.json");
    fs::write(&p[2], bytes).unwrap();
    let error = Hierarchy::load_selection(&p[0], &p[1], &p[2], &p[3]).unwrap_err();
    assert!(error.to_string().contains("checksum"), "{error}");
}

#[test]
fn selection_rejects_membership_or_ancestry_changes_and_invalid_records() {
    let mut p = paths();
    let original: Value = serde_json::from_slice(&fs::read(&p[3]).unwrap()).unwrap();
    let dir = tempdir().unwrap();
    p[3] = dir.path().join("selection.json");
    for case in [
        "point",
        "parent",
        "children",
        "count",
        "duplicate",
        "root",
        "raw parent",
        "missing points",
        "duplicate point",
    ] {
        let mut changed = original.clone();
        let groups = changed["retained_groups"].as_array_mut().unwrap();
        match case {
            "point" => groups[0]["direct_points"][0] = json!(100000),
            "parent" => groups[1]["display_parent"] = json!(1044),
            "children" => groups[0]["display_children"] = json!([]),
            "count" => groups[0]["distinct_notes"] = json!(999),
            "duplicate" => groups.push(groups[1].clone()),
            "root" => {
                groups.remove(0);
            }
            "raw parent" => groups[1]["raw_parent"] = json!(1044),
            "missing points" => groups[0]["direct_points"] = json!([]),
            "duplicate point" => {
                let points = groups[0]["direct_points"].as_array_mut().unwrap();
                points.push(points[0].clone());
            }
            _ => unreachable!(),
        }
        fs::write(&p[3], serde_json::to_vec(&changed).unwrap()).unwrap();
        assert!(
            Hierarchy::load_selection(&p[0], &p[1], &p[2], &p[3]).is_err(),
            "Accepted {case}"
        );
    }
}
