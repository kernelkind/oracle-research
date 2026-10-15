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
fn hdbscan_cli_preserves_exact_output_across_explicit_thread_counts() {
    let root = tempfile::tempdir_in("/dev/shm").unwrap();
    let request_path = root.path().join("request.json");
    let inputs = (0..256)
        .map(|i| {
            json!({
                "opaque_id": format!("{:064x}", i + 1),
                "normalized_vector": unit_vector(i as f64 * 0.019),
            })
        })
        .collect::<Vec<_>>();
    fs::write(
        &request_path,
        serde_json::to_vec(&json!({
            "schema_version": 1, "candidate": "hdbscan",
            "source_vector_manifest_sha256": "a".repeat(64),
            "normalized_vector_sha256": "b".repeat(64),
            "hdbscan_configuration": {"min_samples":3,"min_cluster_size":2,
                                      "selection_method":"excess_of_mass"},
            "inputs": inputs,
        }))
        .unwrap(),
    )
    .unwrap();
    let mut expected = None;
    for threads in [1, 4] {
        let output = Command::new(env!("CARGO_BIN_EXE_fine-segmentation-candidate"))
            .arg(&request_path)
            .arg("--threads")
            .arg(threads.to_string())
            .output()
            .unwrap();
        assert!(
            output.status.success(),
            "{}",
            String::from_utf8_lossy(&output.stderr)
        );
        assert!(output.stderr.is_empty());
        if let Some(expected) = &expected {
            assert_eq!(&output.stdout, expected);
        } else {
            expected = Some(output.stdout);
        }
    }
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

#[test]
fn candidate_cli_runs_explicit_hdbscan_configuration_without_changing_legacy_baseline() {
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
    let mut request = json!({
        "schema_version": 1,
        "candidate": "hdbscan",
        "source_vector_manifest_sha256": "a".repeat(64),
        "normalized_vector_sha256": "b".repeat(64),
        "inputs": inputs,
    });
    fs::write(&request_path, serde_json::to_vec(&request).unwrap()).unwrap();
    let baseline = Command::new(env!("CARGO_BIN_EXE_fine-segmentation-candidate"))
        .arg(&request_path)
        .output()
        .expect("baseline command");
    assert!(
        baseline.status.success(),
        "{}",
        String::from_utf8_lossy(&baseline.stderr)
    );
    let baseline: Value = serde_json::from_slice(&baseline.stdout).unwrap();
    assert_eq!(
        "hdbscan-controlled-suite-config-v1",
        baseline["candidate_identity"]
    );
    let baseline_config: Value = serde_json::from_str(
        baseline["artifact"]["canonical_configuration_json"]
            .as_str()
            .unwrap(),
    )
    .unwrap();
    assert_eq!(
        json!({"min_samples":2,"min_cluster_size":2,"selection_method":"excess_of_mass"}),
        baseline_config
    );

    let chosen = json!({"min_samples":3,"min_cluster_size":3,"selection_method":"leaf"});
    request["hdbscan_configuration"] = chosen.clone();
    fs::write(&request_path, serde_json::to_vec(&request).unwrap()).unwrap();
    let changed = Command::new(env!("CARGO_BIN_EXE_fine-segmentation-candidate"))
        .arg(&request_path)
        .output()
        .expect("configured command");
    assert!(
        changed.status.success(),
        "{}",
        String::from_utf8_lossy(&changed.stderr)
    );
    let changed: Value = serde_json::from_slice(&changed.stdout).unwrap();
    assert_eq!("hdbscan-explicit-config-v1", changed["candidate_identity"]);
    let actual: Value = serde_json::from_str(
        changed["artifact"]["canonical_configuration_json"]
            .as_str()
            .unwrap(),
    )
    .unwrap();
    assert_eq!(chosen, actual);
    assert_ne!(
        baseline["artifact"]["manifest"]["configuration_sha256"],
        changed["artifact"]["manifest"]["configuration_sha256"]
    );
}

#[test]
fn candidate_cli_does_not_silently_ignore_hdbscan_configuration_for_snn() {
    let root = tempfile::tempdir_in("/dev/shm").expect("temporary directory");
    let request_path = root.path().join("request.json");
    fs::write(&request_path, serde_json::to_vec(&json!({
        "schema_version": 1,
        "candidate": "snn",
        "source_vector_manifest_sha256": "a".repeat(64),
        "normalized_vector_sha256": "b".repeat(64),
        "inputs": [],
        "hdbscan_configuration": {"min_samples":2,"min_cluster_size":2,"selection_method":"leaf"},
    })).unwrap()).unwrap();
    let output = Command::new(env!("CARGO_BIN_EXE_fine-segmentation-candidate"))
        .arg(request_path)
        .output()
        .expect("run candidate");
    assert!(!output.status.success());
    assert!(
        String::from_utf8_lossy(&output.stderr)
            .contains("hdbscan_configuration requires candidate `hdbscan`")
    );
}
