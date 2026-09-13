use std::process::{Command, Stdio};

#[test]
fn title_review_has_its_own_entrypoint_and_question() {
    for arguments in [
        vec!["review-titles", "titles.json", "session.json"],
        vec![
            "review-titles",
            "titles.json",
            "session.json",
            "--start-at",
            "S001",
        ],
    ] {
        let output = Command::new(env!("CARGO_BIN_EXE_sse-mask-review"))
            .args(arguments)
            .stdin(Stdio::null())
            .output()
            .expect("run title review CLI");
        assert!(!output.status.success());
        let error = String::from_utf8_lossy(&output.stderr);
        assert!(
            error.contains("title prompt review must be started from an interactive terminal"),
            "expected the separate title-review entrypoint, got: {error}"
        );
    }
}
