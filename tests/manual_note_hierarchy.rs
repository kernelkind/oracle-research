use std::fs;
use std::path::Path;

use oracle_mvp::manual_note_hierarchy::ManualNoteHierarchy;
use serde_json::{Value, json};

const SPEC: &str = "sse_multivector/manual-coffee-hierarchy-v1/hierarchy.json";
const SOURCE: &str = "sse_multivector/real-note-fine-segmentation-v1/reviewed-input.json";

#[test]
fn coffee_proposal_preserves_full_originals_and_explicit_memberships() {
    let h = ManualNoteHierarchy::load(Path::new(SPEC), Path::new(SOURCE)).unwrap();
    assert_eq!(h.nodes.len(), 3);
    assert_eq!(h.note_ids("coffee").len(), 18);
    assert_eq!(
        h.note_ids("morning-coffee"),
        ["N018", "N041", "N043", "N058", "N071", "N095"]
    );
    assert_eq!(
        h.note_ids("coffee-preparation"),
        ["N036", "N045", "N052", "N060", "N086"]
    );
    assert_eq!(
        h.outside_child_note_ids("coffee"),
        ["N004", "N029", "N035", "N038", "N065", "N079", "N094"]
    );
    let original: Value = serde_json::from_slice(&fs::read(SOURCE).unwrap()).unwrap();
    let vectors: Value = serde_json::from_slice(
        &fs::read("sse_multivector/real-note-fine-segmentation-v1/vectors/vector-map.json")
            .unwrap(),
    )
    .unwrap();
    for (short_id, note) in &h.notes {
        let source = original["notes"]
            .as_array()
            .unwrap()
            .iter()
            .find(|n| n["note_id"] == note.note_id)
            .unwrap();
        assert_eq!(note.content, source["text"].as_str().unwrap());
        let vector = vectors["vectors"]
            .as_array()
            .unwrap()
            .iter()
            .find(|v| v["note_short_id"] == *short_id)
            .unwrap();
        assert_eq!(note.note_id, vector["note_id"].as_str().unwrap());
    }
}

fn modified(
    edit: impl FnOnce(&mut Value),
) -> Result<ManualNoteHierarchy, Box<dyn std::error::Error>> {
    let directory = tempfile::tempdir().unwrap();
    let path = directory.path().join("hierarchy.json");
    let mut spec: Value = serde_json::from_slice(&fs::read(SPEC).unwrap()).unwrap();
    edit(&mut spec);
    fs::write(&path, serde_json::to_vec(&spec).unwrap()).unwrap();
    ManualNoteHierarchy::load(&path, Path::new(SOURCE))
}

#[test]
fn overlaps_are_deduplicated_and_notes_remain_available_in_both_children() {
    let h = modified(|s| {
        s["nodes"][1]["note_ids"]
            .as_array_mut()
            .unwrap()
            .push(json!("N052"));
        s["nodes"][0]["note_ids"]
            .as_array_mut()
            .unwrap()
            .push(json!("N052"));
    })
    .unwrap();
    assert_eq!(h.note_ids("coffee").len(), 18);
    assert_eq!(h.note_ids("morning-coffee").len(), 7);
    assert!(h.note_ids("coffee-preparation").contains(&"N052".into()));
    assert!(!h.outside_child_note_ids("coffee").contains(&"N052".into()));
}

#[test]
fn changed_source_unknown_members_and_disconnected_categories_are_rejected() {
    for edit in [
        |s: &mut Value| s["source_sha256"] = json!("wrong"),
        |s: &mut Value| s["nodes"][1]["note_ids"][0] = json!("N999"),
        |s: &mut Value| s["nodes"][1]["children"] = json!(["coffee"]),
        |s: &mut Value| s["nodes"][0]["children"] = json!(["morning-coffee"]),
        |s: &mut Value| s["nodes"][1]["note_ids"] = json!(["N018", "N018"]),
        |s: &mut Value| s["notes"][0]["note_short_id"] = json!("N018"),
    ] {
        assert!(modified(edit).is_err());
    }
}
