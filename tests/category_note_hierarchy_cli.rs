use std::fs;
use std::path::Path;
use std::process::Command;

use serde_json::json;
use sha2::{Digest, Sha256};

fn write_fixture(directory: &Path) -> (std::path::PathBuf, std::path::PathBuf) {
    let source = directory.join("source.json");
    let hierarchy = directory.join("hierarchy.json");
    let bytes = serde_json::to_vec(&json!({"notes": [
        {"note_id": "one", "text": "First post"},
        {"note_id": "two", "text": "Second post"},
        {"note_id": "three", "text": "Third post"}
    ]}))
    .unwrap();
    fs::write(&source, &bytes).unwrap();
    let nodes = [
        (
            "root",
            "All posts",
            vec!["singleton", "two-descendants", "repeated"],
            vec![],
        ),
        ("singleton", "Singleton", vec![], vec!["N003"]),
        (
            "two-descendants",
            "Two descendant posts",
            vec!["first", "second"],
            vec![],
        ),
        ("first", "First descendant", vec![], vec!["N001"]),
        ("second", "Second descendant", vec![], vec!["N002"]),
        (
            "repeated",
            "Repeated single post",
            vec!["duplicate-one", "duplicate-two"],
            vec![],
        ),
        ("duplicate-one", "Duplicate one", vec![], vec!["N001"]),
        ("duplicate-two", "Duplicate two", vec![], vec!["N001"]),
    ]
    .into_iter()
    .map(|(id, label, children, notes)| {
        json!({
            "node_id": id, "label": label, "children": children, "note_ids": notes
        })
    })
    .collect::<Vec<_>>();
    fs::write(
        &hierarchy,
        serde_json::to_vec(&json!({
            "schema_version": 1, "hierarchy_id": "minimum-notes-test",
            "source_sha256": format!("{:x}", Sha256::digest(&bytes)), "root_node_id": "root",
            "notes": [
                {"note_id": "one", "note_short_id": "N001"},
                {"note_id": "two", "note_short_id": "N002"},
                {"note_id": "three", "note_short_id": "N003"}
            ], "nodes": nodes
        }))
        .unwrap(),
    )
    .unwrap();
    (hierarchy, source)
}

#[test]
fn category_minimum_notes_filters_display_only_and_counts_distinct_descendant_posts() {
    let directory = tempfile::tempdir().unwrap();
    let (hierarchy, source) = write_fixture(directory.path());
    let original = (fs::read(&hierarchy).unwrap(), fs::read(&source).unwrap());
    let check = |options: &[&str]| {
        let output = Command::new(env!("CARGO_BIN_EXE_sse-subject-navigation"))
            .arg("--categories")
            .arg(&hierarchy)
            .arg(&source)
            .args(options)
            .arg("--check")
            .output()
            .unwrap();
        assert!(
            output.status.success(),
            "{}",
            String::from_utf8_lossy(&output.stderr)
        );
        String::from_utf8(output.stdout).unwrap()
    };
    let filtered = check(&["--min-notes", "2"]);
    assert!(
        filtered.contains("Minimum notes per displayed category: 2"),
        "{filtered}"
    );
    assert!(
        filtered.contains("Displayed root children: 1"),
        "{filtered}"
    );
    assert!(filtered.contains("8 categories · 3 notes"), "{filtered}");
    assert!(filtered.contains("All posts · 3 notes"), "{filtered}");
    assert!(
        filtered.contains("Two descendant posts · 2 notes"),
        "{filtered}"
    );
    for hidden in [
        "Singleton",
        "First descendant",
        "Second descendant",
        "Repeated single post",
        "Duplicate one",
        "Duplicate two",
    ] {
        assert!(!filtered.contains(hidden), "displayed {hidden}: {filtered}");
    }
    assert!(!filtered.contains("Children: singleton"), "{filtered}");
    let default = check(&[]);
    assert_eq!(default, check(&["--min-notes", "1"]));
    assert!(default.contains("Singleton · 1 notes"), "{default}");
    assert!(
        default.contains("Repeated single post · 1 notes"),
        "{default}"
    );
    let above_root = check(&["--min-notes", "4"]);
    assert!(above_root.contains("All posts · 3 notes"), "{above_root}");
    assert!(
        above_root.contains("Displayed root children: 0"),
        "{above_root}"
    );
    assert_eq!(
        original,
        (fs::read(&hierarchy).unwrap(), fs::read(&source).unwrap())
    );
}

#[test]
fn category_minimum_notes_rejects_invalid_options_before_loading_sources() {
    for (mode, options) in [
        ("--categories", vec!["--min-notes"]),
        ("--categories", vec!["--min-notes", "0"]),
        ("--categories", vec!["--min-notes", "many"]),
        ("--categories", vec!["--min-notes", "2", "--min-notes", "2"]),
        ("--notes", vec!["--min-notes", "2"]),
    ] {
        let output = Command::new(env!("CARGO_BIN_EXE_sse-subject-navigation"))
            .args([mode, "missing-hierarchy.json", "missing-source.json"])
            .args(&options)
            .arg("--check")
            .output()
            .unwrap();
        assert!(!output.status.success(), "accepted {mode} {options:?}");
        let stderr = String::from_utf8_lossy(&output.stderr);
        assert!(stderr.contains("--min-notes"), "{stderr}");
        assert!(
            !stderr.contains("No such file"),
            "read sources before rejecting {options:?}: {stderr}"
        );
    }
}
