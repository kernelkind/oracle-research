use std::fs;
use std::process::Command;

use serde_json::{Value, json};

fn opaque_id(value: u8) -> String {
    format!("{value:064x}")
}

fn unit_vector(angle: f64) -> Vec<f64> {
    vec![angle.cos(), angle.sin()]
}

#[test]
fn candidate_cli_runs_the_frozen_snn_boundary_in_a_fresh_process() {
    let root = tempfile::tempdir_in("/dev/shm").expect("temporary directory");
    let request_path = root.path().join("request.json");
    let inputs = [0.00_f64, 0.01, 0.02, 0.03, 1.00, 1.01, 1.02, 1.03]
        .into_iter()
        .enumerate()
        .map(|(ordinal, angle)| {
            json!({
                "opaque_id": opaque_id(ordinal as u8 + 1),
                "normalized_vector": unit_vector(angle),
            })
        })
        .collect::<Vec<_>>();
    fs::write(
        &request_path,
        serde_json::to_vec(&json!({
            "schema_version": 1,
            "candidate": "snn",
            "source_vector_manifest_sha256": "a".repeat(64),
            "normalized_vector_sha256": "b".repeat(64),
            "inputs": inputs,
        }))
        .expect("encode request"),
    )
    .expect("write request");

    let output = Command::new(env!("CARGO_BIN_EXE_fine-segmentation-candidate"))
        .arg(&request_path)
        .output()
        .expect("run candidate process");
    assert!(
        output.status.success(),
        "candidate failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert!(output.stderr.is_empty());

    let value: Value = serde_json::from_slice(&output.stdout).expect("decode candidate output");
    assert_eq!(1, value["schema_version"]);
    assert_eq!(
        "snn-controlled-suite-config-v1",
        value["candidate_identity"]
    );
    assert_eq!(
        "snn-sdm-2003-exact-angular-v1",
        value["artifact"]["manifest"]["algorithm_version"]
    );
    assert_eq!(8, value["artifact"]["manifest"]["vector_count"]);
    assert_eq!(
        "{\"neighbor_count\":5,\"minimum_shared_neighbor_count\":2,\"minimum_core_neighbor_count\":3}",
        value["artifact"]["canonical_configuration_json"]
    );
}

#[test]
fn candidate_cli_rejects_an_unrecognized_candidate_before_running() {
    let root = tempfile::tempdir_in("/dev/shm").expect("temporary directory");
    let request_path = root.path().join("request.json");
    fs::write(
        &request_path,
        serde_json::to_vec(&json!({
            "schema_version": 1,
            "candidate": "unknown",
            "source_vector_manifest_sha256": "a".repeat(64),
            "normalized_vector_sha256": "b".repeat(64),
            "inputs": [],
        }))
        .expect("encode request"),
    )
    .expect("write request");

    let output = Command::new(env!("CARGO_BIN_EXE_fine-segmentation-candidate"))
        .arg(&request_path)
        .output()
        .expect("run candidate process");
    assert!(!output.status.success());
    assert!(String::from_utf8_lossy(&output.stderr).contains("unsupported candidate `unknown`"));
}
