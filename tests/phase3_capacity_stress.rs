use std::fs;
use std::process::Command;

use oracle_mvp::phase3_capacity_stress::{
    evict_file_cache, require_combined_memory_limit, require_host_memory_admission,
    resident_file_cache, resolve_unified_cgroup_path,
};

#[test]
fn combined_guard_requires_one_exact_hard_limit_and_zero_swap() {
    let temp = tempfile::tempdir().expect("temporary cgroup");
    fs::write(temp.path().join("memory.max"), b"68719476736\n").expect("write memory limit");
    fs::write(temp.path().join("memory.swap.max"), b"0\n").expect("write swap limit");

    let observation = require_combined_memory_limit(temp.path(), 68_719_476_736)
        .expect("accept the exact combined guard");
    assert_eq!(observation.memory_max_bytes(), 68_719_476_736);
    assert_eq!(observation.memory_swap_max_bytes(), 0);

    fs::write(temp.path().join("memory.swap.max"), b"1\n").expect("change swap limit");
    let error = require_combined_memory_limit(temp.path(), 68_719_476_736)
        .expect_err("reject usable swap outside the memory ceiling");
    assert!(error.to_string().contains("swap"));
}

#[test]
fn host_admission_preserves_swap_debt_and_the_approved_reserve() {
    let gib = 1024_u64.pow(3);
    let observation = require_host_memory_admission(95 * gib, 15 * gib, 12 * gib, 67 * gib)
        .expect("admit the exact safe host envelope");
    assert_eq!(observation.headroom_bytes(), gib);

    let error = require_host_memory_admission(93 * gib, 15 * gib, 12 * gib, 67 * gib)
        .expect_err("reject a run that would consume the host reserve");
    assert!(error.to_string().contains("host memory"));
}

#[test]
fn unified_cgroup_path_resolves_the_process_scope_below_the_mount() {
    let path = resolve_unified_cgroup_path(
        "/sys/fs/cgroup".as_ref(),
        "0::/user.slice/user-1000.slice/capacity.scope\n",
    )
    .expect("resolve cgroup v2 scope");

    assert_eq!(
        path,
        std::path::PathBuf::from("/sys/fs/cgroup/user.slice/user-1000.slice/capacity.scope")
    );
}

#[test]
fn cache_eviction_advises_only_the_explicit_regular_files() {
    let temp = tempfile::tempdir().expect("temporary inputs");
    let input = temp.path().join("vectors.f32le");
    fs::write(&input, vec![7_u8; 1024 * 1024]).expect("write input");
    let untouched = temp.path().join("untouched.bin");
    fs::write(&untouched, vec![9_u8; 1024]).expect("write untouched file");

    let observation = evict_file_cache(std::slice::from_ref(&input))
        .expect("advise the kernel to drop the explicit input");

    assert_eq!(observation.files(), 1);
    assert_eq!(observation.bytes(), 1024 * 1024);
    assert_eq!(fs::read(untouched).unwrap(), vec![9_u8; 1024]);
}

#[test]
fn cache_residency_is_measured_without_an_external_utility() {
    let temp = tempfile::tempdir().expect("temporary inputs");
    let input = temp.path().join("vectors.f32le");
    fs::write(&input, vec![7_u8; 1024 * 1024]).expect("write input");

    let observation = resident_file_cache(std::slice::from_ref(&input))
        .expect("measure resident file-backed pages");

    assert_eq!(observation.files(), 1);
    assert!(observation.bytes() <= 1024 * 1024);
}

#[test]
fn stress_image_keeps_the_exact_worker_runtime_and_adds_only_the_controller() {
    let dockerfile = fs::read_to_string("gte/phase3-capacity-stress.Dockerfile")
        .expect("read capacity Dockerfile");

    assert!(dockerfile.contains(
        "FROM docker.io/kernelkind/oracle-mvp@sha256:96a60fd4caf87afadf0546636af6eeefee72d327dc95dde1714f86ea14fb435a"
    ));
    assert!(dockerfile.contains("ENTRYPOINT [\"/usr/local/bin/phase3-capacity-stress\"]"));
}

#[test]
fn prepare_rejects_a_runner_binding_outside_the_approved_workload() {
    let temp = tempfile::tempdir().expect("temporary capacity inputs");
    let corpus = temp.path().join("source-corpus.mdb");
    let ordered = temp.path().join("source-ordered.bin");
    let representation = temp.path().join("source-representation");
    let binding = temp.path().join("runner-binding.json");
    let model = temp.path().join("model-bundle");
    fs::write(&corpus, b"corpus").expect("write corpus");
    fs::write(&ordered, b"ordered").expect("write ordering");
    fs::create_dir(&representation).expect("create representation");
    fs::write(&binding, b"{}\n").expect("write binding");
    fs::create_dir(&model).expect("create model bundle");
    let workspace = temp.path().join("work");
    let config = temp.path().join("config.json");
    fs::write(
        &config,
        serde_json::to_vec_pretty(&serde_json::json!({
            "schema_version": 1,
            "workspace_path": workspace,
            "report_path": temp.path().join("work/report.json"),
            "memory_samples_path": temp.path().join("work/memory-samples.jsonl"),
            "cache_eviction_report_path": temp.path().join("work/cache-eviction.jsonl"),
            "source_corpus_data_path": corpus,
            "source_ordered_event_ids_path": ordered,
            "source_representation_path": representation,
            "source_runner_binding_path": binding,
            "model_bundle_path": model,
            "expected_representation_version": "0".repeat(64),
            "expected_geometry_version": "0".repeat(64),
            "expected_runner_binding_sha256": "1".repeat(64),
            "expected_memory_max_bytes": 1024,
            "host_memory_reserve_bytes": 1024
        }))
        .expect("encode config"),
    )
    .expect("write config");

    let output = Command::new(env!("CARGO_BIN_EXE_phase3-capacity-stress"))
        .args(["prepare", config.to_str().expect("UTF-8 config path")])
        .output()
        .expect("run capacity preparation");

    assert!(!output.status.success());
    assert!(
        String::from_utf8_lossy(&output.stderr).contains("runner binding"),
        "unexpected error: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert!(!workspace.exists());
}

#[test]
fn config_rejects_parent_components_before_resolving_output_paths() {
    let temp = tempfile::tempdir().expect("temporary capacity inputs");
    let corpus = temp.path().join("source-corpus.mdb");
    let ordered = temp.path().join("source-ordered.bin");
    let representation = temp.path().join("source-representation");
    let binding = temp.path().join("runner-binding.json");
    let model = temp.path().join("model-bundle");
    fs::write(&corpus, b"corpus").expect("write corpus");
    fs::write(&ordered, b"ordered").expect("write ordering");
    fs::create_dir(&representation).expect("create representation");
    fs::write(&binding, b"{}\n").expect("write binding");
    fs::create_dir(&model).expect("create model bundle");
    fs::create_dir(temp.path().join("work")).expect("create lexical parent");
    let workspace = temp
        .path()
        .join("work/../source-representation/accidental-output");
    let config = temp.path().join("config.json");
    fs::write(
        &config,
        serde_json::to_vec_pretty(&serde_json::json!({
            "schema_version": 1,
            "workspace_path": workspace,
            "report_path": workspace.join("report.json"),
            "memory_samples_path": workspace.join("memory-samples.jsonl"),
            "cache_eviction_report_path": workspace.join("cache-eviction.jsonl"),
            "source_corpus_data_path": corpus,
            "source_ordered_event_ids_path": ordered,
            "source_representation_path": representation,
            "source_runner_binding_path": binding,
            "model_bundle_path": model,
            "expected_representation_version": "0".repeat(64),
            "expected_geometry_version": "0".repeat(64),
            "expected_runner_binding_sha256": "0".repeat(64),
            "expected_memory_max_bytes": 1024,
            "host_memory_reserve_bytes": 1024
        }))
        .expect("encode config"),
    )
    .expect("write config");

    let output = Command::new(env!("CARGO_BIN_EXE_phase3-capacity-stress"))
        .args(["prepare", config.to_str().expect("UTF-8 config path")])
        .output()
        .expect("run capacity preparation");

    assert!(!output.status.success());
    assert!(
        String::from_utf8_lossy(&output.stderr).contains("normalized"),
        "unexpected error: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert!(!representation.join("accidental-output").exists());
}

#[test]
fn cache_eviction_records_each_retry_instead_of_trusting_stale_state() {
    let temp = tempfile::tempdir().expect("temporary capacity workspace");
    let workspace = temp.path().join("work");
    let corpus = workspace.join("corpus.ndb");
    let representation = workspace.join("representation");
    let model = temp.path().join("model-bundle");
    let prepared_model = workspace.join("model-bundle");
    fs::create_dir_all(&corpus).expect("create prepared corpus");
    fs::create_dir_all(&representation).expect("create prepared representation");
    fs::create_dir(&model).expect("create model bundle");
    fs::create_dir_all(prepared_model.join("model")).expect("create prepared model bundle");
    fs::write(workspace.join("preparation.json"), b"{}\n").expect("write preparation");
    fs::write(corpus.join("data.mdb"), b"corpus").expect("write corpus");
    fs::write(workspace.join("ordered-event-ids.bin"), b"ordered").expect("write ordering");
    fs::write(representation.join("manifest.json"), b"manifest").expect("write manifest");
    fs::write(representation.join("verification.json"), b"verification")
        .expect("write verification");
    fs::write(model.join("weights"), b"weights").expect("write model");
    fs::write(prepared_model.join("model-lock.json"), b"lock").expect("write model lock");
    fs::write(prepared_model.join("model/weights"), b"weights").expect("write prepared model");

    let source_corpus = temp.path().join("source-corpus.mdb");
    let source_ordered = temp.path().join("source-ordered.bin");
    let source_representation = temp.path().join("source-representation");
    let binding = temp.path().join("runner-binding.json");
    fs::write(&source_corpus, b"source corpus").expect("write source corpus");
    fs::write(&source_ordered, b"source ordering").expect("write source ordering");
    fs::create_dir(&source_representation).expect("create source representation");
    fs::write(&binding, b"{}\n").expect("write source binding");

    let config = temp.path().join("config.json");
    let receipt = workspace.join("cache-eviction.jsonl");
    fs::write(
        &config,
        serde_json::to_vec_pretty(&serde_json::json!({
            "schema_version": 1,
            "workspace_path": workspace,
            "report_path": temp.path().join("work/report.json"),
            "memory_samples_path": temp.path().join("work/memory-samples.jsonl"),
            "cache_eviction_report_path": receipt,
            "source_corpus_data_path": source_corpus,
            "source_ordered_event_ids_path": source_ordered,
            "source_representation_path": source_representation,
            "source_runner_binding_path": binding,
            "model_bundle_path": model,
            "expected_representation_version": "0".repeat(64),
            "expected_geometry_version": "0".repeat(64),
            "expected_runner_binding_sha256": "0".repeat(64),
            "expected_memory_max_bytes": 1024,
            "host_memory_reserve_bytes": 1024
        }))
        .expect("encode config"),
    )
    .expect("write config");

    for _ in 0..2 {
        let output = Command::new(env!("CARGO_BIN_EXE_phase3-capacity-stress"))
            .args(["evict-cache", config.to_str().expect("UTF-8 config path")])
            .output()
            .expect("run cache eviction");
        assert!(
            output.status.success(),
            "cache eviction failed: {}",
            String::from_utf8_lossy(&output.stderr)
        );
    }

    let receipts =
        fs::read_to_string(workspace.join("cache-eviction.jsonl")).expect("read eviction ledger");
    assert_eq!(receipts.lines().count(), 2);
    for receipt in receipts.lines() {
        let receipt: serde_json::Value =
            serde_json::from_str(receipt).expect("decode eviction receipt");
        assert_eq!(receipt["schema_version"], 2);
    }
}
