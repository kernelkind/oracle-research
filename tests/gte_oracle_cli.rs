use std::process::Command;

use serde_json::json;

#[test]
fn phase2_cli_refuses_to_guess_an_operation() {
    let output = Command::new(env!("CARGO_BIN_EXE_gte-oracle"))
        .output()
        .expect("run gte-oracle");
    assert!(!output.status.success());
    let stderr = String::from_utf8(output.stderr).expect("UTF-8 stderr");
    assert!(stderr.contains("usage: gte-oracle"), "{stderr}");
}

#[test]
fn phase2_cli_refuses_unadmitted_cuda_before_touching_model_or_corpus() {
    let temporary = tempfile::tempdir().expect("temporary directory");
    let config_path = temporary.path().join("cuda.json");
    std::fs::write(
        &config_path,
        serde_json::to_vec_pretty(&json!({
            "corpus_path": temporary.path().join("missing-corpus"),
            "ordered_event_ids_path": temporary.path().join("missing-order"),
            "token_audit_path": temporary.path().join("missing-audit"),
            "batch_plan_path": temporary.path().join("missing-batch-plan"),
            "representation_path": temporary.path().join("missing-representation"),
            "model_bundle_root": temporary.path().join("missing-bundle"),
            "model_lock_path": temporary.path().join("missing-model-lock"),
            "model_bundle_script": temporary.path().join("missing-verifier"),
            "model_bundle_python": temporary.path().join("missing-python"),
            "worker_source_path": temporary.path().join("missing-worker"),
            "dependency_lock_path": temporary.path().join("missing-dependencies"),
            "container_image": "missing@example.invalid/worker@sha256:deadbeef",
            "torch_version": "2.12.1",
            "transformers_version": "4.41.2",
            "cuda_version": "13.0.2",
            "worker": {
                "program": temporary.path().join("missing-program"),
                "model_dir": temporary.path().join("missing-model"),
                "model_lock_path": temporary.path().join("missing-worker-model-lock"),
                "dependency_lock_path": temporary.path().join("missing-worker-dependencies"),
                "device": "cuda"
            },
            "batch_size": 32,
            "shard_rows": 100000
        }))
        .expect("serialize config"),
    )
    .expect("write config");

    let output = Command::new(env!("CARGO_BIN_EXE_gte-oracle"))
        .arg("embed-shards")
        .arg(&config_path)
        .arg("0")
        .output()
        .expect("run gte-oracle");
    assert!(!output.status.success());
    let stderr = String::from_utf8(output.stderr).expect("UTF-8 stderr");
    assert!(stderr.contains("refuses unadmitted CUDA"), "{stderr}");
    assert!(!stderr.contains("model-bundle verification"), "{stderr}");
}

#[test]
fn phase2_cli_has_one_separate_ledger_bound_cuda_calibration_entrypoint() {
    let temporary = tempfile::tempdir().expect("temporary directory");
    let config_path = temporary.path().join("cuda-calibration.json");
    std::fs::write(
        &config_path,
        serde_json::to_vec_pretty(&json!({
            "corpus_path": temporary.path().join("missing-corpus"),
            "ordered_event_ids_path": temporary.path().join("missing-order"),
            "token_audit_path": temporary.path().join("missing-audit"),
            "batch_plan_path": temporary.path().join("missing-batch-plan"),
            "representation_path": temporary.path().join("missing-representation"),
            "model_lock_path": temporary.path().join("missing-model-lock"),
            "worker_source_path": temporary.path().join("missing-worker"),
            "dependency_lock_path": temporary.path().join("missing-dependencies"),
            "container_image": "missing@example.invalid/worker@sha256:deadbeef",
            "torch_version": "2.12.1",
            "transformers_version": "4.41.2",
            "cuda_version": "13.0.2",
            "worker": {
                "program": temporary.path().join("missing-program"),
                "model_dir": temporary.path().join("missing-model"),
                "model_lock_path": temporary.path().join("missing-worker-model-lock"),
                "dependency_lock_path": temporary.path().join("missing-worker-dependencies"),
                "device": "cuda"
            },
            "batch_size": 32,
            "shard_rows": 100000
        }))
        .expect("serialize config"),
    )
    .expect("write config");

    let output = Command::new(env!("CARGO_BIN_EXE_gte-oracle"))
        .arg("calibrate-shards")
        .arg(&config_path)
        .arg("0")
        .output()
        .expect("run gte-oracle");
    assert!(!output.status.success());
    let stderr = String::from_utf8(output.stderr).expect("UTF-8 stderr");
    assert!(stderr.contains("requires calibration"), "{stderr}");
    assert!(!stderr.contains("refuses unadmitted CUDA"), "{stderr}");
}

#[test]
fn phase2_cli_exposes_local_batch_plan_and_index_preparation_without_starting_the_model() {
    let temporary = tempfile::tempdir().expect("temporary directory");
    let config_path = temporary.path().join("local.json");
    std::fs::write(
        &config_path,
        serde_json::to_vec_pretty(&json!({
            "corpus_path": temporary.path().join("missing-corpus"),
            "ordered_event_ids_path": temporary.path().join("missing-order"),
            "token_audit_path": temporary.path().join("missing-audit"),
            "batch_plan_path": temporary.path().join("missing-batch-plan"),
            "representation_path": temporary.path().join("missing-representation"),
            "model_bundle_root": temporary.path().join("missing-bundle"),
            "model_lock_path": temporary.path().join("missing-model-lock"),
            "model_bundle_script": temporary.path().join("missing-verifier"),
            "model_bundle_python": temporary.path().join("missing-python"),
            "worker_source_path": temporary.path().join("missing-worker"),
            "dependency_lock_path": temporary.path().join("missing-dependencies"),
            "container_image": "missing@example.invalid/worker@sha256:deadbeef",
            "torch_version": "2.12.1",
            "transformers_version": "4.41.2",
            "cuda_version": "13.0.2",
            "worker": {
                "program": temporary.path().join("missing-program"),
                "model_dir": temporary.path().join("missing-model"),
                "model_lock_path": temporary.path().join("missing-worker-model-lock"),
                "dependency_lock_path": temporary.path().join("missing-worker-dependencies"),
                "device": "cpu"
            },
            "batch_size": 32,
            "shard_rows": 100000
        }))
        .expect("serialize config"),
    )
    .expect("write config");

    for (operation, missing_input) in [
        ("plan-batches", "missing-audit"),
        ("prepare-representation", "missing-order"),
        ("verify-representation", "missing-corpus"),
    ] {
        let output = Command::new(env!("CARGO_BIN_EXE_gte-oracle"))
            .arg(operation)
            .arg(&config_path)
            .output()
            .expect("run gte-oracle");
        assert!(!output.status.success());
        let stderr = String::from_utf8(output.stderr).expect("UTF-8 stderr");
        assert!(stderr.contains(missing_input), "{operation}: {stderr}");
        assert!(!stderr.contains("model-bundle"), "{operation}: {stderr}");
        assert!(
            !stderr.contains("usage: gte-oracle"),
            "{operation}: {stderr}"
        );
    }
}

#[test]
fn calibration_selection_has_a_model_free_local_preflight_command() {
    let temporary = tempfile::tempdir().expect("temporary directory");
    let config_path = temporary.path().join("selection-preflight.json");
    std::fs::write(
        &config_path,
        serde_json::to_vec_pretty(&json!({
            "corpus_path": temporary.path().join("missing-corpus"),
            "ordered_event_ids_path": temporary.path().join("missing-order"),
            "token_audit_path": temporary.path().join("missing-audit"),
            "batch_plan_path": temporary.path().join("missing-batch-plan"),
            "representation_path": temporary.path().join("missing-representation"),
            "model_lock_path": temporary.path().join("missing-model-lock"),
            "worker_source_path": temporary.path().join("missing-worker"),
            "dependency_lock_path": temporary.path().join("missing-dependencies"),
            "container_image": "missing@example.invalid/worker@sha256:deadbeef",
            "torch_version": "2.12.1",
            "transformers_version": "4.41.2",
            "cuda_version": "13.0.2",
            "worker": {
                "program": temporary.path().join("missing-program"),
                "model_dir": temporary.path().join("missing-model"),
                "model_lock_path": temporary.path().join("missing-worker-model-lock"),
                "dependency_lock_path": temporary.path().join("missing-worker-dependencies"),
                "device": "cuda"
            },
            "batch_size": 32,
            "shard_rows": 16384
        }))
        .expect("serialize config"),
    )
    .expect("write config");

    let output = Command::new(env!("CARGO_BIN_EXE_gte-oracle"))
        .arg("validate-calibration-selection")
        .arg(&config_path)
        .arg("157")
        .arg("16,20,25,32,40,50,64,80,100,128,160,202,259,325,433,513")
        .output()
        .expect("run local selection preflight");
    assert!(!output.status.success());
    let stderr = String::from_utf8(output.stderr).expect("UTF-8 stderr");
    assert!(stderr.contains("missing-batch-plan"), "{stderr}");
    assert!(!stderr.contains("refuses unadmitted CUDA"), "{stderr}");
    assert!(!stderr.contains("missing-model"), "{stderr}");
}

#[test]
fn model_operations_rely_on_the_worker_verified_bundle_without_a_second_host_verifier() {
    let temporary = tempfile::tempdir().expect("temporary directory");
    let config_path = temporary.path().join("single-verifier.json");
    std::fs::write(
        &config_path,
        serde_json::to_vec_pretty(&json!({
            "corpus_path": temporary.path().join("missing-corpus"),
            "ordered_event_ids_path": temporary.path().join("missing-order"),
            "token_audit_path": temporary.path().join("missing-audit"),
            "batch_plan_path": temporary.path().join("missing-batch-plan"),
            "representation_path": temporary.path().join("missing-representation"),
            "model_lock_path": temporary.path().join("missing-model-lock"),
            "worker_source_path": temporary.path().join("missing-worker"),
            "dependency_lock_path": temporary.path().join("missing-dependencies"),
            "container_image": "missing@example.invalid/worker@sha256:deadbeef",
            "torch_version": "2.12.1",
            "transformers_version": "4.41.2",
            "cuda_version": "13.0.2",
            "worker": {
                "program": temporary.path().join("missing-program"),
                "model_dir": temporary.path().join("missing-model"),
                "model_lock_path": temporary.path().join("missing-worker-model-lock"),
                "dependency_lock_path": temporary.path().join("missing-worker-dependencies"),
                "device": "cpu"
            },
            "batch_size": 32,
            "shard_rows": 100000
        }))
        .expect("serialize config"),
    )
    .expect("write config");

    let output = Command::new(env!("CARGO_BIN_EXE_gte-oracle"))
        .arg("model-smoke")
        .arg(&config_path)
        .output()
        .expect("run gte-oracle");
    assert!(!output.status.success());
    let stderr = String::from_utf8(output.stderr).expect("UTF-8 stderr");
    assert!(stderr.contains("missing-model-lock"), "{stderr}");
    assert!(!stderr.contains("missing field"), "{stderr}");
    assert!(!stderr.contains("model-bundle verifier"), "{stderr}");
}
