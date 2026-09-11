use std::process::Command;

#[test]
fn category_mode_checks_saved_categories_and_original_notes_without_a_terminal() {
    let output = Command::new(env!("CARGO_BIN_EXE_sse-subject-navigation"))
        .args([
            "--categories",
            "sse_multivector/manual-coffee-hierarchy-v1/hierarchy.json",
            "sse_multivector/real-note-fine-segmentation-v1/reviewed-input.json",
            "--check",
        ])
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let stdout = String::from_utf8_lossy(&output.stdout);
    for expected in ["Coffee", "Morning coffee", "Coffee preparation", "18 notes"] {
        assert!(stdout.contains(expected), "missing {expected}: {stdout}");
    }
}
