use std::fs;
use std::process::Command;

use serde_json::json;
use sha2::{Digest, Sha256};

#[test]
fn manual_notes_mode_checks_categories_and_direct_parent_notes_without_a_terminal() {
    let directory = tempfile::tempdir().unwrap();
    let source = directory.path().join("notes.json");
    let spec = directory.path().join("hierarchy.json");
    let bytes = serde_json::to_vec(&json!({"notes": [
        {"note_id":"a", "text":"First original note."},
        {"note_id":"b", "text":"Second original note."},
        {"note_id":"c", "text":"Only at the parent."}
    ]}))
    .unwrap();
    fs::write(&source, &bytes).unwrap();
    fs::write(&spec, serde_json::to_vec(&json!({
        "schema_version":1, "hierarchy_id":"manual-test",
        "source_sha256":format!("{:x}", Sha256::digest(&bytes)),
        "root_node_id":"coffee",
        "notes":[
            {"note_id":"a", "note_short_id":"N001"},
            {"note_id":"b", "note_short_id":"N002"},
            {"note_id":"c", "note_short_id":"N003"}
        ],
        "nodes":[
            {"node_id":"coffee", "label":"Coffee", "children":["morning","preparation"], "note_ids":["N003"]},
            {"node_id":"morning", "label":"Morning coffee", "children":[], "note_ids":["N001","N002"]},
            {"node_id":"preparation", "label":"Coffee preparation", "children":[], "note_ids":["N002"]}
        ]
    })).unwrap()).unwrap();
    let before = [fs::read(&spec).unwrap(), fs::read(&source).unwrap()];
    let output = Command::new(env!("CARGO_BIN_EXE_sse-subject-navigation"))
        .arg("--notes")
        .arg(&spec)
        .arg(&source)
        .arg("--check")
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let stdout = String::from_utf8_lossy(&output.stdout);
    for expected in [
        "manual-test",
        "Coffee",
        "3 notes",
        "3 categories",
        "Morning coffee",
        "2 notes",
        "Coffee preparation",
        "1 note",
        "N003",
    ] {
        assert!(stdout.contains(expected), "missing {expected}: {stdout}");
    }
    assert_eq!(
        before,
        [fs::read(&spec).unwrap(), fs::read(&source).unwrap()]
    );
}

#[test]
fn old_fine_segment_invocation_still_loads_without_the_manual_notes_mode() {
    let output = Command::new(env!("CARGO_BIN_EXE_sse-subject-navigation"))
        .args([
            "sse_multivector/manual-subject-hierarchy-v1/hierarchy.json",
            "sse_multivector/fine-region-hierarchy-result-v2/analysis.json",
            "sse_multivector/fine-region-partition-result-v1/analysis.json",
        ])
        .output()
        .unwrap();
    assert!(!output.status.success());
    assert!(
        String::from_utf8_lossy(&output.stderr)
            .contains("must be started from an interactive terminal")
    );
}

#[test]
fn unknown_manual_option_is_rejected_before_display() {
    let output = Command::new(env!("CARGO_BIN_EXE_sse-subject-navigation"))
        .args(["--notes", "a", "b", "--approve"])
        .output()
        .unwrap();
    assert!(!output.status.success());
    assert!(String::from_utf8_lossy(&output.stderr).contains("usage:"));
}
