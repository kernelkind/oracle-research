use std::fs;

use oracle_mvp::phase4_final_launch::{
    FINAL_EVALUATION_PURPOSE, FinalEvaluationContainerState, FinalEvaluationWorkspaceState,
    MINIMUM_FINAL_EVALUATION_MEMORY_BYTES, final_evaluation_attach_arguments,
    final_evaluation_container_arguments, inspect_final_evaluation_container,
    inspect_final_evaluation_workspace, read_final_evaluation_launch_config,
};

#[test]
fn final_evaluation_container_separates_immutable_phase3_inputs_from_phase4_state() {
    let temp = tempfile::tempdir().expect("temporary launch paths");
    let phase3 = temp.path().join("phase3");
    let representation = temp.path().join("representation");
    let model = temp.path().join("model-bundle");
    let workspace = temp.path().join("phase4");
    for path in [&phase3, &representation, &model, &workspace] {
        fs::create_dir(path).expect("create launch path");
    }
    let config = workspace.join("frozen-config.json");
    fs::write(&config, b"{}\n").expect("write frozen config");
    let limit = 68 * 1024_u64.pow(3);

    let arguments = final_evaluation_container_arguments(
        "phase4-real-final",
        &format!("sha256:{}", "d".repeat(64)),
        &"e".repeat(64),
        limit,
        1000,
        1000,
        &[phase3.clone(), representation.clone(), model.clone()],
        &workspace,
        &config,
    )
    .expect("build guarded final-evaluation launch");
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
        "--label=io.notedeck.phase4.launch={}",
        "e".repeat(64)
    )));
    assert!(joined.contains("--user=1000:1000"));
    for input in [phase3, representation, model] {
        assert!(joined.contains(&format!(
            "type=bind,src={},dst={},readonly",
            input.display(),
            input.display()
        )));
    }
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
    assert_eq!(MINIMUM_FINAL_EVALUATION_MEMORY_BYTES, 67 * 1024_u64.pow(3));
}

#[test]
fn final_evaluation_config_pins_exact_phase3_session_representation_and_image() {
    let temp = tempfile::tempdir().expect("temporary config");
    let config_path = temp.path().join("config.json");
    let config = final_evaluation_config(temp.path());
    fs::write(
        &config_path,
        serde_json::to_vec_pretty(&config).expect("encode config"),
    )
    .expect("write config");

    let parsed =
        read_final_evaluation_launch_config(&config_path).expect("read exact Phase 4 config");
    assert_eq!(
        parsed.source_phase3_session_sha256(),
        "a".repeat(64).as_str()
    );
    assert_eq!(
        parsed.expected_representation_version(),
        "b".repeat(64).as_str()
    );
    assert_eq!(
        parsed.controller_image(),
        format!("sha256:{}", "d".repeat(64))
    );

    let mut mutable_image = config.clone();
    mutable_image["controller_image"] = serde_json::json!("oracle-mvp-phase4:mutable");
    fs::write(
        &config_path,
        serde_json::to_vec_pretty(&mutable_image).expect("encode mutable config"),
    )
    .expect("write mutable config");
    let error = read_final_evaluation_launch_config(&config_path)
        .expect_err("reject mutable controller image");
    assert!(error.to_string().contains("exact image ID"));

    let mut overlapping = config;
    overlapping["workspace_path"] = overlapping["source_phase3_workspace_path"].clone();
    fs::write(
        &config_path,
        serde_json::to_vec_pretty(&overlapping).expect("encode overlapping config"),
    )
    .expect("write overlapping config");
    let error =
        read_final_evaluation_launch_config(&config_path).expect_err("reject source-state overlap");
    assert!(error.to_string().contains("overlaps"));
}

#[test]
fn existing_phase4_state_without_initialization_receipt_fails_closed() {
    let temp = tempfile::tempdir().expect("temporary workspace parent");
    let workspace = temp.path().join("final-evaluation");
    let config_sha256 = "a".repeat(64);

    assert_eq!(
        inspect_final_evaluation_workspace(&workspace, &config_sha256)
            .expect("accept an absent fresh workspace"),
        FinalEvaluationWorkspaceState::Fresh
    );

    fs::create_dir(&workspace).expect("create untrusted workspace");
    let untrusted_session = workspace.join("phase4-session.json");
    fs::write(&untrusted_session, b"untrusted\n").expect("write untrusted state");
    let before = fs::read(&untrusted_session).expect("read state before rejection");

    let error = inspect_final_evaluation_workspace(&workspace, &config_sha256)
        .expect_err("reject state without initialization receipt");
    assert!(error.to_string().contains("initialization receipt"));
    assert_eq!(
        fs::read(&untrusted_session).expect("read state after rejection"),
        before
    );
}

#[test]
fn running_phase4_container_resume_requires_the_frozen_identity() {
    use std::os::unix::fs::PermissionsExt;

    let temp = tempfile::tempdir().expect("temporary runtime");
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
        inspect_final_evaluation_container(&runtime, "phase4-real-final", &launch, &image)
            .expect("inspect matching running container"),
        FinalEvaluationContainerState::Running
    );
    assert_eq!(
        final_evaluation_attach_arguments("phase4-real-final")
            .into_iter()
            .map(|value| value.to_string_lossy().into_owned())
            .collect::<Vec<_>>(),
        ["attach", "--detach-keys=ctrl-]", "phase4-real-final"]
    );
}

#[test]
fn final_evaluation_image_reuses_the_proven_worker_runtime() {
    let dockerfile = fs::read_to_string("gte/phase4-final-evaluation.Dockerfile")
        .expect("read final-evaluation Dockerfile");

    assert!(dockerfile.contains(
        "FROM docker.io/kernelkind/oracle-mvp@sha256:96a60fd4caf87afadf0546636af6eeefee72d327dc95dde1714f86ea14fb435a"
    ));
    assert!(dockerfile.contains("cargo build --locked --release --bin phase4-final-evaluation"));
    assert!(dockerfile.contains("ENTRYPOINT [\"/usr/local/bin/phase4-final-evaluation\"]"));
}

fn final_evaluation_config(root: &std::path::Path) -> serde_json::Value {
    serde_json::json!({
        "schema_version": 1,
        "purpose": FINAL_EVALUATION_PURPOSE,
        "workspace_path": root.join("phase4"),
        "source_phase3_workspace_path": root.join("phase3"),
        "source_representation_path": root.join("representation"),
        "source_model_bundle_path": root.join("model-bundle"),
        "container_runtime": root.join("docker"),
        "container_name": "phase4-real-final",
        "controller_image": format!("sha256:{}", "d".repeat(64)),
        "source_phase3_session_sha256": "a".repeat(64),
        "expected_representation_version": "b".repeat(64),
        "host_memory_reserve_bytes": 12 * 1024_u64.pow(3)
    })
}
