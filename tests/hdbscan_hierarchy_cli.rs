use std::path::Path;
use std::process::Command;

#[test]
fn validates_real_artifact_without_a_terminal_or_source_writes() {
    let root = Path::new(env!("CARGO_MANIFEST_DIR"));
    let base = root.join("sse_multivector/real-note-fine-segmentation-v1");
    let paths = [
        base.join("hdbscan-cross-note/response.json"),
        base.join("vectors/vector-map.json"),
        base.join("reviewed-input.json"),
    ];
    let before = paths
        .iter()
        .map(std::fs::read)
        .collect::<Result<Vec<_>, _>>()
        .unwrap();
    let output = Command::new(env!("CARGO_BIN_EXE_hdbscan-hierarchy"))
        .args(&paths)
        .args(["--start-at", "1039", "--check"])
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains("130 groups"));
    assert!(stdout.contains("916 unique vectors"));
    assert!(stdout.contains("945 original IDs"));
    assert!(stdout.contains("100 notes"));
    assert!(stdout.contains("1039"));
    assert_eq!(
        paths
            .iter()
            .map(std::fs::read)
            .collect::<Result<Vec<_>, _>>()
            .unwrap(),
        before
    );
}

#[test]
fn help_is_available_and_nonterminal_interaction_is_rejected_clearly() {
    let bin = env!("CARGO_BIN_EXE_hdbscan-hierarchy");
    let help = Command::new(bin).arg("--help").output().unwrap();
    assert!(help.status.success());
    assert!(String::from_utf8_lossy(&help.stdout).contains("--start-at"));
    let base = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("sse_multivector/real-note-fine-segmentation-v1");
    let output = Command::new(bin)
        .args([
            base.join("hdbscan-cross-note/response.json"),
            base.join("vectors/vector-map.json"),
            base.join("reviewed-input.json"),
        ])
        .output()
        .unwrap();
    assert!(!output.status.success());
    assert!(String::from_utf8_lossy(&output.stderr).contains("interactive terminal"));
}
