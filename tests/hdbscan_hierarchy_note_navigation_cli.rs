use std::path::PathBuf;
use std::process::Command;

fn paths() -> [PathBuf; 3] {
    let base = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("sse_multivector/real-note-fine-segmentation-v1");
    [
        base.join("hdbv3-cross-note-edges-v1/response.json"),
        base.join("vectors/vector-map.json"),
        base.join("reviewed-input.json"),
    ]
}

#[test]
fn note_navigation_validates_saved_merge_tree_without_writing_sources() {
    let paths = paths();
    let before: Vec<_> = paths
        .iter()
        .map(|path| std::fs::read(path).unwrap())
        .collect();
    let output = Command::new(env!("CARGO_BIN_EXE_hdbscan-hierarchy"))
        .args(&paths)
        .args(["--note-navigation", "--start-at", "1204", "--check"])
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let text = String::from_utf8_lossy(&output.stdout);
    for expected in [
        "Merge-tree note navigation",
        "246 groups",
        "916 unique vectors",
        "945 original IDs",
        "100 notes",
        "Starting branch 1204",
    ] {
        assert!(text.contains(expected), "Missing {expected}: {text}");
    }
    assert!(!text.contains("HDBv2"), "{text}");
    assert_eq!(
        paths
            .iter()
            .map(|path| std::fs::read(path).unwrap())
            .collect::<Vec<_>>(),
        before
    );
}

#[test]
fn note_navigation_rejects_manual_selection_and_collapsed_starting_groups() {
    let bin = env!("CARGO_BIN_EXE_hdbscan-hierarchy");
    let conflict = Command::new(bin)
        .args(paths())
        .args(["--note-navigation", "--selection", "unused.json", "--check"])
        .output()
        .unwrap();
    assert!(!conflict.status.success());
    assert!(String::from_utf8_lossy(&conflict.stderr).contains("cannot combine"));

    // The two-mask chocolate/tea group is collapsed into the six-mask group:
    // both contain exactly N016 and N073.
    let collapsed = Command::new(bin)
        .args(paths())
        .args(["--note-navigation", "--start-at", "1076", "--check"])
        .output()
        .unwrap();
    assert!(!collapsed.status.success());
    assert!(String::from_utf8_lossy(&collapsed.stderr).contains("unknown group 1076"));
}

#[test]
fn note_navigation_help_explains_that_ids_come_from_merge_history() {
    let output = Command::new(env!("CARGO_BIN_EXE_hdbscan-hierarchy"))
        .arg("--help")
        .output()
        .unwrap();
    assert!(output.status.success());
    let text = String::from_utf8_lossy(&output.stdout);
    assert!(text.contains("--note-navigation"));
    assert!(text.contains("merge-tree IDs"));
}
