use std::process::Command;

#[test]
fn geometry_cli_requires_an_operation_and_three_paths() {
    let output = Command::new(env!("CARGO_BIN_EXE_representation-geometry"))
        .output()
        .expect("run representation geometry CLI");
    assert!(!output.status.success());
    let stderr = String::from_utf8(output.stderr).expect("UTF-8 stderr");
    assert!(
        stderr.contains(
            "representation-geometry <derive|verify> ORDERED_EVENT_IDS REPRESENTATION OUTPUT"
        ),
        "unexpected stderr: {stderr}"
    );
}
