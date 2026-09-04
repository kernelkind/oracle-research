use std::process::{Command, Stdio};

#[test]
fn mask_review_has_a_separate_entrypoint_without_subject_approval() {
    let output = Command::new(env!("CARGO_BIN_EXE_sse-mask-review"))
        .args(["review-masks", "mask-review.json", "mask-session.json"])
        .stdin(Stdio::null())
        .output()
        .expect("run mask review CLI");
    assert!(!output.status.success());
    let error = String::from_utf8_lossy(&output.stderr);
    assert!(
        error.contains("mask prompt review must be started from an interactive terminal"),
        "expected the mask-only entrypoint, got: {error}"
    );
}
