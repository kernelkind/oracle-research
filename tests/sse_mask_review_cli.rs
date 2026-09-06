use std::process::Command;

#[test]
fn sse_mask_review_cli_explains_its_required_artifacts() {
    let output = Command::new(env!("CARGO_BIN_EXE_sse-mask-review"))
        .output()
        .expect("run mask review CLI");

    assert!(!output.status.success());
    let stderr = String::from_utf8(output.stderr).expect("utf-8 stderr");
    assert!(
        stderr.contains(
            "usage: sse-mask-review <subject-mask-proposal.json> <session.json> \
             <approved-subject-masks.json>"
        ),
        "{stderr}"
    );
    assert!(
        stderr.contains(
            "sse-mask-review iterate <generation-run-directory> <prompt-review-session.json>"
        ),
        "{stderr}"
    );
    assert!(
        stderr.contains("sse-mask-review review-claims <experiment-directory>"),
        "{stderr}"
    );
}

#[test]
fn subject_review_cli_accepts_an_explicit_subject_filter() {
    let output = Command::new(env!("CARGO_BIN_EXE_sse-mask-review"))
        .args([
            "iterate",
            "generation-run",
            "review-session.json",
            "--only",
            "18:3,3:2",
        ])
        .output()
        .expect("run filtered subject review CLI");
    assert!(!output.status.success());
    let stderr = String::from_utf8(output.stderr).expect("utf-8 stderr");
    assert!(
        stderr.contains("the SSE prompt review must be started from an interactive terminal"),
        "expected the filter to reach subject review, got: {stderr}"
    );
}
