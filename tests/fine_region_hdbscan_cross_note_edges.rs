use std::fs;
use std::process::{Command, Output};

use serde_json::{Value, json};

fn opaque_id(value: usize) -> String {
    format!("{value:064x}")
}

fn request(candidate: &str) -> Value {
    let angles = [0.0_f64, 0.4, 0.6, 1.0, 2.0, 2.02];
    let notes = [10, 11, 11, 12, 13, 14];
    json!({
        "schema_version": 1,
        "candidate": candidate,
        "source_vector_manifest_sha256": "a".repeat(64),
        "normalized_vector_sha256": "b".repeat(64),
        "inputs": angles.iter().enumerate().map(|(ordinal, angle)| json!({
            "opaque_id": opaque_id(ordinal + 1),
            "normalized_vector": [angle.cos(), angle.sin()],
        })).collect::<Vec<_>>(),
        "source_note_ids": notes.iter().enumerate().map(|(ordinal, note)|
            (opaque_id(ordinal + 1), Value::String(opaque_id(*note)))
        ).collect::<serde_json::Map<_, _>>(),
    })
}

fn run_cli(request: &Value) -> Output {
    let root = tempfile::tempdir_in("/dev/shm").expect("temporary directory");
    let path = root.path().join("request.json");
    fs::write(&path, serde_json::to_vec(request).unwrap()).unwrap();
    Command::new(env!("CARGO_BIN_EXE_fine-segmentation-candidate"))
        .arg(path)
        .output()
        .expect("run the production candidate CLI")
}

fn run_success(request: &Value) -> Value {
    let output = run_cli(request);
    assert!(
        output.status.success(),
        "candidate failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    serde_json::from_slice(&output.stdout).expect("decode candidate artifact")
}

#[test]
fn cross_note_edges_cli_requires_the_source_note_map() {
    let mut request = request("hdbscan_cross_note_edges");
    request.as_object_mut().unwrap().remove("source_note_ids");
    let output = run_cli(&request);
    assert!(!output.status.success());
    let error = String::from_utf8_lossy(&output.stderr);
    assert!(
        error.contains("source_note_ids is required for candidate `hdbscan_cross_note_edges`"),
        "unexpected candidate error: {error}"
    );
}

#[test]
fn cross_note_edges_cli_rebuilds_the_tree_without_changing_numeric_distances() {
    let baseline_request = request("hdbscan_cross_note");
    let baseline = run_success(&baseline_request);
    let changed_request = request("hdbscan_cross_note_edges");
    let changed = run_success(&changed_request);
    assert_eq!(
        changed["candidate_identity"],
        "hdbscan-cross-note-edges-controlled-suite-config-v1"
    );
    let baseline_run = &baseline["artifact"]["result"];
    let changed_run = &changed["artifact"]["result"];
    assert_eq!(baseline_run["alias_groups"], changed_run["alias_groups"]);
    assert_eq!(
        baseline_run["canonical_unique_ids"],
        changed_run["canonical_unique_ids"]
    );
    let before = &baseline_run["algorithm_result"];
    let after = &changed_run["algorithm_result"];
    for key in ["core_distances", "mutual_reachability_distances", "config"] {
        assert_eq!(before[key], after[key], "unchanged {key}");
    }
    assert_ne!(
        before["minimum_spanning_tree"],
        after["minimum_spanning_tree"]
    );
    assert_ne!(before["single_linkage_tree"], after["single_linkage_tree"]);
    assert_ne!(before["condensed_tree"], after["condensed_tree"]);
    let edges = after["minimum_spanning_tree"].as_array().unwrap();
    assert_eq!(edges.len(), 5, "a full rebuilt MST, not a cut old tree");
    for edge in edges {
        let ids = changed_run["canonical_unique_ids"].as_array().unwrap();
        let left = ids[edge["left"].as_u64().unwrap() as usize]
            .as_str()
            .unwrap();
        let right = ids[edge["right"].as_u64().unwrap() as usize]
            .as_str()
            .unwrap();
        assert_ne!(
            changed_request["source_note_ids"][left],
            changed_request["source_note_ids"][right]
        );
        assert!(
            edge["mutual_reachability_distance"]
                .as_f64()
                .unwrap()
                .is_finite()
        );
    }
    let manifest = &changed["artifact"]["manifest"];
    assert_eq!(
        manifest["algorithm_version"],
        "hdbscan-star-cross-note-edges-exact-angular-v1"
    );
    assert_eq!(
        manifest["cross_note"]["edge_rule_version"],
        "different-source-note-witness-angular-v1"
    );
    assert_eq!(
        manifest["cross_note"]["core_distance_rule_version"],
        baseline["artifact"]["manifest"]["cross_note"]["core_distance_rule_version"]
    );
    assert!(
        baseline["artifact"]["manifest"]["cross_note"]
            .get("edge_rule_version")
            .is_none()
    );
}

#[test]
fn cross_note_edges_cli_keeps_explicit_parameters_and_recomputes_flat_output_deterministically() {
    let mut request = request("hdbscan_cross_note_edges");
    let controlled = run_success(&request);
    request["hdbscan_configuration"] = json!({
        "min_samples": 2,
        "min_cluster_size": 2,
        "selection_method": "excess_of_mass",
    });
    let explicit = run_success(&request);
    assert_eq!(
        explicit["candidate_identity"],
        "hdbscan-cross-note-edges-explicit-config-v1"
    );
    assert_eq!(explicit["artifact"], controlled["artifact"]);
    request["inputs"].as_array_mut().unwrap().reverse();
    assert_eq!(explicit, run_success(&request));

    request["candidate"] = json!("hdbscan_cross_note");
    let baseline = run_success(&request);
    let before = &baseline["artifact"]["result"];
    let after = &explicit["artifact"]["result"];
    assert_eq!(
        before["fine_output"]["segments"].as_array().unwrap().len(),
        2
    );
    assert_eq!(
        after["fine_output"]["segments"].as_array().unwrap().len(),
        3
    );
    assert_ne!(
        before["algorithm_result"]["labels"],
        after["algorithm_result"]["labels"]
    );
    assert_ne!(
        before["algorithm_result"]["clusters"],
        after["algorithm_result"]["clusters"]
    );
}
