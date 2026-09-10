use std::path::{Path, PathBuf};
use std::process::Command;

fn manifest() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("sse_multivector/manual-coffee-hierarchy-v1/m06-comparison.json")
}

#[test]
fn comparison_check_loads_manual_notes_and_every_saved_merge_page() {
    let output = Command::new(env!("CARGO_BIN_EXE_sse-subject-navigation"))
        .arg("--compare")
        .arg(manifest())
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
        "Coffee preparation",
        "5 notes",
        "1605",
        "19 notes",
        "951",
        "1096",
        "1343",
        "1654",
    ] {
        assert!(text.contains(expected), "Missing {expected}: {text}");
    }
}
