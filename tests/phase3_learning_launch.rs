use std::fs;

use oracle_mvp::phase3_learning_launch::{
    HUMAN_LEARNING_PURPOSE, LearningContainerState, LearningWorkspaceState,
    MINIMUM_LEARNING_MEMORY_BYTES, derive_learning_memory_limit, inspect_learning_container,
    inspect_learning_workspace, learning_attach_arguments, learning_container_arguments,
    read_host_memory_snapshot, read_learning_launch_config, resolve_controller_image_id,
};

#[test]
fn safe_learning_memory_ceiling_preserves_swap_debt_and_host_reserve() {
    let gib = 1024_u64.pow(3);

    assert_eq!(
        derive_learning_memory_limit(95 * gib, 15 * gib, 12 * gib)
            .expect("derive the safe learning ceiling"),
        68 * gib
    );
    assert_eq!(MINIMUM_LEARNING_MEMORY_BYTES, 67 * gib);

    let error = derive_learning_memory_limit(93 * gib, 15 * gib, 12 * gib)
        .expect_err("reject a ceiling below the proven envelope");
    assert!(error.to_string().contains("67 GiB"));
}

#[test]
fn learning_container_keeps_controller_and_worker_under_one_zero_swap_guard() {
    let temp = tempfile::tempdir().expect("temporary launch paths");
    let representation = temp.path().join("representation");
    let model = temp.path().join("model-bundle");
    let workspace = temp.path().join("private-run");
    fs::create_dir(&representation).expect("create representation");
    fs::create_dir(&model).expect("create model bundle");
    fs::create_dir(&workspace).expect("create workspace");
    let config = workspace.join("frozen-config.json");
    fs::write(&config, b"{}\n").expect("write frozen config");
    let limit = 68 * 1024_u64.pow(3);

    let arguments = learning_container_arguments(
        "phase3-real-learning",
        &format!("sha256:{}", "d".repeat(64)),
        &"e".repeat(64),
        limit,
        1000,
        1000,
        &[representation.clone(), model.clone()],
        &workspace,
        &config,
    )
    .expect("build the guarded container launch");
    let arguments = arguments
        .iter()
        .map(|argument| argument.to_string_lossy().into_owned())
        .collect::<Vec<_>>();
    let joined = arguments.join(" ");

    assert!(joined.contains("--interactive --tty"));
    assert!(joined.contains("--network=none"));
    assert!(joined.contains("--read-only"));
    assert!(joined.contains(&format!("--memory={limit}")));
    assert!(joined.contains(&format!("--memory-swap={limit}")));
    assert!(!joined.contains("--memory-swappiness"));
    assert!(joined.contains(
        "--tmpfs=/runtime-tmp:rw,noexec,nosuid,nodev,size=1g,uid=1000,gid=1000,mode=0700"
    ));
    assert!(
        joined
            .contains("--tmpfs=/runtime-home:rw,nosuid,nodev,size=2g,uid=1000,gid=1000,mode=0700")
    );
    assert!(joined.contains("--detach-keys=ctrl-]"));
    assert!(joined.contains(&format!(
        "--label=io.notedeck.phase3.launch={}",
        "e".repeat(64)
    )));
    assert!(joined.contains("--user=1000:1000"));
    assert!(joined.contains(&format!(
        "type=bind,src={},dst={},readonly",
        representation.display(),
        representation.display()
    )));
    assert!(joined.contains(&format!(
        "type=bind,src={},dst={},readonly",
        model.display(),
        model.display()
    )));
    assert!(joined.contains(&format!(
        "type=bind,src={},dst={}",
        workspace.display(),
        workspace.display()
    )));
    assert_eq!(
        arguments[arguments.len() - 3],
        format!("sha256:{}", "d".repeat(64))
    );
    assert_eq!(arguments[arguments.len() - 2], "__run");
    assert_eq!(arguments.last().unwrap(), config.to_str().unwrap());
}

#[test]
fn exact_controller_image_id_is_verified_by_the_runtime() {
    use std::os::unix::fs::PermissionsExt;

    let temp = tempfile::tempdir().expect("temporary runtime");
    let runtime = temp.path().join("docker");
    let image_id = format!("sha256:{}", "a".repeat(64));
    fs::write(
        &runtime,
        format!(
            "#!/bin/sh\n[ \"$1 $2 $3 $4\" = \"image inspect --format={{{{.Id}}}} {image_id}\" ] || exit 9\nprintf '%s\\n' '{image_id}'\n"
        ),
    )
    .expect("write runtime");
    fs::set_permissions(&runtime, fs::Permissions::from_mode(0o700))
        .expect("make runtime executable");

    assert_eq!(
        resolve_controller_image_id(&runtime, &image_id).expect("verify image ID"),
        image_id
    );
}

#[test]
fn human_config_requires_an_exact_controller_image_id() {
    let temp = tempfile::tempdir().expect("temporary config");
    let config_path = temp.path().join("config.json");
    let mut config = learning_config(temp.path());
    config["controller_image"] = serde_json::json!("oracle-mvp-phase3-learning:mutable");
    fs::write(
        &config_path,
        serde_json::to_vec_pretty(&config).expect("encode config"),
    )
    .expect("write config");

    let error = read_learning_launch_config(&config_path)
        .expect_err("reject a mutable controller image reference");
    assert!(error.to_string().contains("exact image ID"));
}

#[test]
fn learning_image_reuses_the_proven_worker_runtime() {
    let dockerfile =
        fs::read_to_string("gte/phase3-learning.Dockerfile").expect("read learning Dockerfile");

    assert!(dockerfile.contains(
        "FROM docker.io/kernelkind/oracle-mvp@sha256:96a60fd4caf87afadf0546636af6eeefee72d327dc95dde1714f86ea14fb435a"
    ));
    assert!(dockerfile.contains("cargo build --locked --release --bin phase3-learning"));
    assert!(dockerfile.contains("ENTRYPOINT [\"/usr/local/bin/phase3-learning\"]"));
}

#[test]
fn host_snapshot_and_running_container_resume_are_explicit() {
    use std::os::unix::fs::PermissionsExt;

    let temp = tempfile::tempdir().expect("temporary host state");
    let meminfo = temp.path().join("meminfo");
    fs::write(
        &meminfo,
        "MemAvailable: 100000 kB\nSwapTotal: 20000 kB\nSwapFree: 5000 kB\n",
    )
    .expect("write meminfo");
    let memory = read_host_memory_snapshot(&meminfo).expect("read host memory");
    assert_eq!(memory.available_bytes(), 100000 * 1024);
    assert_eq!(memory.swap_used_bytes(), 15000 * 1024);

    let runtime = temp.path().join("docker");
    let launch = "b".repeat(64);
    let image = format!("sha256:{}", "c".repeat(64));
    fs::write(
        &runtime,
        format!(
            "#!/bin/sh\nif [ \"$1 $2\" = \"container inspect\" ]; then\n  printf 'true\\n{}\\n{}\\n'\n  exit 0\nfi\nexit 8\n",
            launch, image
        ),
    )
    .expect("write runtime");
    fs::set_permissions(&runtime, fs::Permissions::from_mode(0o700))
        .expect("make runtime executable");

    assert_eq!(
        inspect_learning_container(&runtime, "phase3-real-learning", &launch, &image)
            .expect("inspect matching running container"),
        LearningContainerState::Running
    );
    assert_eq!(
        learning_attach_arguments("phase3-real-learning")
            .into_iter()
            .map(|value| value.to_string_lossy().into_owned())
            .collect::<Vec<_>>(),
        ["attach", "--detach-keys=ctrl-]", "phase3-real-learning"]
    );
}

#[test]
fn human_config_rejects_synthetic_purpose_and_nonpositive_seeds() {
    let temp = tempfile::tempdir().expect("temporary config");
    let config_path = temp.path().join("config.json");
    let mut config = learning_config(temp.path());
    config["purpose"] = serde_json::json!("synthetic-capacity-stress");
    fs::write(
        &config_path,
        serde_json::to_vec_pretty(&config).expect("encode config"),
    )
    .expect("write config");

    let error =
        read_learning_launch_config(&config_path).expect_err("reject a non-human launch purpose");
    assert!(error.to_string().contains("human"));

    config["purpose"] = serde_json::json!(HUMAN_LEARNING_PURPOSE);
    config["seeds"][0]["rating"] = serde_json::json!(4);
    fs::write(
        &config_path,
        serde_json::to_vec_pretty(&config).expect("encode config"),
    )
    .expect("write config");
    let error = read_learning_launch_config(&config_path).expect_err("reject a nonpositive seed");
    assert!(error.to_string().contains("positive"));
}

#[test]
fn existing_private_state_without_human_initialization_receipt_fails_closed() {
    let temp = tempfile::tempdir().expect("temporary workspace parent");
    let workspace = temp.path().join("real-learning");
    let config_sha256 = "a".repeat(64);

    assert_eq!(
        inspect_learning_workspace(&workspace, &config_sha256)
            .expect("accept an absent fresh workspace"),
        LearningWorkspaceState::Fresh
    );

    fs::create_dir(&workspace).expect("create untrusted workspace");
    let synthetic_session = workspace.join("phase3-capacity-session.json");
    fs::write(&synthetic_session, b"synthetic\n").expect("write synthetic state");
    let before = fs::read(&synthetic_session).expect("read state before rejection");

    let error = inspect_learning_workspace(&workspace, &config_sha256)
        .expect_err("reject private state without a human initialization receipt");
    assert!(error.to_string().contains("initialization receipt"));
    assert_eq!(
        fs::read(&synthetic_session).expect("read state after rejection"),
        before
    );
}

fn learning_config(root: &std::path::Path) -> serde_json::Value {
    serde_json::json!({
        "schema_version": 1,
        "purpose": HUMAN_LEARNING_PURPOSE,
        "workspace_path": root.join("real-learning"),
        "source_corpus_data_path": root.join("source-corpus/data.mdb"),
        "source_ordered_event_ids_path": root.join("ordered-event-ids.bin"),
        "source_representation_path": root.join("representation"),
        "source_geometry_path": root.join("geometry"),
        "model_bundle_path": root.join("model-bundle"),
        "container_runtime": root.join("docker"),
        "container_name": "phase3-real-learning",
        "controller_image": format!("sha256:{}", "d".repeat(64)),
        "expected_representation_version": "b".repeat(64),
        "expected_geometry_version": "c".repeat(64),
        "host_memory_reserve_bytes": 12 * 1024_u64.pow(3),
        "seeds": (1_u8..=5).map(|value| serde_json::json!({
            "event_id": format!("{value:02x}").repeat(32),
            "rating": 7
        })).collect::<Vec<_>>()
    })
}
