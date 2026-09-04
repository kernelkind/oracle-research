use std::process::{Command, Stdio};

#[test]
fn mask_review_can_open_a_requested_item_without_clearing_decisions() {
    let output = Command::new(env!("CARGO_BIN_EXE_sse-mask-review"))
        .args([
            "review-masks",
            "mask-review.json",
            "mask-session.json",
            "--start-at",
            "M08",
        ])
        .stdin(Stdio::null())
        .output()
        .expect("run mask review CLI");
    assert!(!output.status.success());
    let error = String::from_utf8_lossy(&output.stderr);
    assert!(
        error.contains("mask prompt review must be started from an interactive terminal"),
        "expected --start-at to reach the mask review entrypoint, got: {error}"
    );
}
