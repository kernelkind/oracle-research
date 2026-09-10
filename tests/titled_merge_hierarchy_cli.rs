use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;

use oracle_mvp::hdbscan_hierarchy::Hierarchy;
use serde_json::json;
use sha2::{Digest, Sha256};

fn inputs() -> [PathBuf; 3] {
    let base = Path::new(env!("CARGO_MANIFEST_DIR")).join("sse_multivector");
    [
        base.join("merge-rule-exploration-v1/M06.json"),
        base.join("real-note-fine-segmentation-v1/vectors/vector-map.json"),
        base.join("real-note-fine-segmentation-v1/reviewed-input.json"),
    ]
}

#[test]
fn saved_merge_notes_check_preserves_groups_and_identifies_provisional_titles() {
    let paths = inputs();
    let h =
        Hierarchy::load_merge_history_with_min_notes(&paths[0], &paths[1], &paths[2], 5).unwrap();
    let hashes = ["merge_history", "vector_map", "source_notes"]
        .into_iter()
        .zip(&paths)
        .map(|(key, path)| {
            (
                key,
                format!("{:x}", Sha256::digest(fs::read(path).unwrap())),
            )
        })
        .collect::<std::collections::BTreeMap<_, _>>();
    let directory = tempfile::tempdir().unwrap();
    let titles = directory.path().join("titles.json");
    fs::write(
        &titles,
        serde_json::to_vec(&json!({
            "schema_version": 1,
            "run_id": "M06",
            "min_notes": 5,
            "input_sha256": hashes,
            "titles": h.groups.keys().map(|id| json!({
                "group_id": id,
                "label": if *id == 1605 { "Coffee" } else { "Mixed subjects" }
            })).collect::<Vec<_>>()
        }))
        .unwrap(),
    )
    .unwrap();
    let output = Command::new(env!("CARGO_BIN_EXE_sse-subject-navigation"))
        .arg("--merge-notes")
        .args(&paths)
        .arg(titles)
        .arg("--check")
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let text = String::from_utf8_lossy(&output.stdout);
    for expected in [
        "M06 · provisional titles",
        "minimum 5 notes",
        "150 categories · 100 notes",
        "M06/1605 · Coffee · 19 notes",
    ] {
        assert!(text.contains(expected), "Missing {expected}: {text}");
    }
    assert!(!text.contains("manual"), "{text}");
}
