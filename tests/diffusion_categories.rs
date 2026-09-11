use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::path::Path;
use std::process::Command;

use oracle_mvp::manual_note_hierarchy::ManualNoteHierarchy;
use serde_json::Value;
use sha2::{Digest, Sha256};

const RUN: &str = "sse_multivector/geometric-hierarchy-v1/GDC09";
const SOURCE: &str = "sse_multivector/real-note-fine-segmentation-v1/reviewed-input.json";

fn read(path: impl AsRef<Path>) -> Value {
    serde_json::from_slice(&fs::read(path).unwrap()).unwrap()
}

#[test]
fn saved_diffusion_categories_preserve_all_notes_and_every_retained_membership() {
    let spec = Path::new(RUN).join("categories.json");
    let h = ManualNoteHierarchy::load(&spec, Path::new(SOURCE)).unwrap();
    assert_eq!(h.root_node_id, "1753");
    assert_eq!(h.nodes.len(), 219);
    assert_eq!(h.notes.len(), 100);
    let native = read(Path::new(RUN).join("hierarchy.json"));
    let native: BTreeMap<_, _> = native["nodes"]
        .as_array()
        .unwrap()
        .iter()
        .map(|n| (n["id"].as_u64().unwrap().to_string(), n))
        .collect();
    let original = read(SOURCE);
    for note in h.notes.values() {
        let original = original["notes"]
            .as_array()
            .unwrap()
            .iter()
            .find(|n| n["note_id"] == note.note_id)
            .unwrap();
        assert_eq!(note.content, original["text"].as_str().unwrap());
    }
    for (id, node) in &h.nodes {
        let expected = native[id]["note_ids"]
            .as_array()
            .unwrap()
            .iter()
            .map(|v| v.as_str().unwrap().to_owned())
            .collect::<Vec<_>>();
        let actual = h.note_ids(id);
        assert_eq!(actual, expected, "changed membership at {id}");
        assert!(actual.len() >= 2, "one-note category {id}");
        assert!(!node.label.trim().is_empty());
        for child in &node.children {
            let child_notes = h.note_ids(child);
            assert!(
                child_notes.len() < actual.len(),
                "equal-note step {id}->{child}"
            );
            assert!(child_notes.iter().all(|n| actual.contains(n)));
        }
    }
    let provenance = read(Path::new(RUN).join("category-projection.json"));
    assert_eq!(provenance["native_groups"].as_array().unwrap().len(), 838);
    for group in provenance["native_groups"].as_array().unwrap() {
        let retained = group["retained_node_id"].as_str().unwrap();
        let native_id = group["native_node_id"].as_u64().unwrap().to_string();
        assert_eq!(group["note_ids"], native[&native_id]["note_ids"]);
        let notes = group["note_ids"].as_array().unwrap();
        match group["disposition"].as_str().unwrap() {
            "retained" | "equal-note-set" => {
                assert_eq!(
                    serde_json::to_value(h.note_ids(retained)).unwrap(),
                    group["note_ids"]
                );
            }
            "fewer-than-two-notes" => {
                assert!(notes.len() < 2);
                assert!(notes.iter().all(|n| {
                    h.note_ids(retained)
                        .contains(&n.as_str().unwrap().to_owned())
                }));
            }
            other => panic!("unknown disposition {other}"),
        }
    }
    assert_eq!(
        provenance["categories_sha256"],
        format!("{:x}", Sha256::digest(fs::read(spec).unwrap()))
    );
    for (name, source) in provenance["sources"].as_object().unwrap() {
        let path = match name.as_str() {
            "notes" => Path::new(SOURCE).to_path_buf(),
            "vector_map" => {
                Path::new("sse_multivector/real-note-fine-segmentation-v1/vectors/vector-map.json")
                    .to_path_buf()
            }
            "titles" => Path::new(RUN).join("category-titles.json"),
            other => Path::new(RUN).join(format!("{other}.json")),
        };
        let bytes = fs::read(path).unwrap();
        assert_eq!(source["sha256"], format!("{:x}", Sha256::digest(bytes)));
    }
}

#[test]
fn cross_branch_equal_note_sets_keep_the_reviewed_distinct_mask_meanings() {
    let h = ManualNoteHierarchy::load(&Path::new(RUN).join("categories.json"), Path::new(SOURCE))
        .unwrap();
    let mut duplicates = BTreeMap::<Vec<String>, Vec<String>>::new();
    for id in h.nodes.keys() {
        duplicates
            .entry(h.note_ids(id))
            .or_default()
            .push(id.clone());
    }
    let actual: BTreeSet<_> = duplicates
        .into_values()
        .filter(|ids| ids.len() > 1)
        .collect();
    let expected: BTreeSet<Vec<String>> = [
        vec!["961", "1749"],
        vec!["982", "1008"],
        vec!["1305", "1355"],
        vec!["1705", "1717", "1732"],
        vec!["1621", "1683"],
    ]
    .into_iter()
    .map(|ids| {
        let mut ids = ids.into_iter().map(str::to_owned).collect::<Vec<_>>();
        ids.sort();
        ids
    })
    .collect();
    assert_eq!(actual, expected);
    let audit = read(Path::new(RUN).join("category-mask-review.json"));
    let audited: BTreeSet<Vec<String>> = audit["cross_branch_checks"]
        .as_array()
        .unwrap()
        .iter()
        .map(|entry| {
            assert_eq!(entry["decision"], "keep-separate");
            let mut ids = entry["node_ids"]
                .as_array()
                .unwrap()
                .iter()
                .map(|id| id.as_str().unwrap().to_owned())
                .collect::<Vec<_>>();
            ids.sort();
            ids
        })
        .collect();
    assert_eq!(actual, audited);
}

#[test]
fn real_category_cli_loads_the_frozen_run() {
    let output = Command::new(env!("CARGO_BIN_EXE_sse-subject-navigation"))
        .args([
            "--categories",
            &format!("{RUN}/categories.json"),
            SOURCE,
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
        "GDC09-note-categories",
        "219 categories · 100 notes",
        "Coffee",
        "Kitchen equipment",
    ] {
        assert!(text.contains(expected), "missing {expected}");
    }
}
