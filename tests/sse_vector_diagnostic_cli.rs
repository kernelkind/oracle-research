use std::process::Command;

#[test]
fn cli_explains_the_three_diagnostic_operations() {
    let output = Command::new(env!("CARGO_BIN_EXE_sse-vector-diagnostic"))
        .output()
        .expect("run diagnostic CLI");

    assert!(!output.status.success());
    let stderr = String::from_utf8(output.stderr).expect("UTF-8 stderr");
    assert!(
        stderr.contains(
            "usage: sse-vector-diagnostic <prepare PROPOSAL WORKER_INPUT | \
             analyze PROPOSAL WORKER_RECEIPT RAW_VECTORS OUTPUT_DIR | \
             verify PROPOSAL OUTPUT_DIR>"
        ),
        "{stderr}"
    );
}
