use std::fs;
use std::os::unix::fs::PermissionsExt;

use oracle_mvp::phase3_cost_preflight::{
    create_private_preflight_directory, gte_container_prefix_arguments,
    immutable_content_tree_identity, immutable_tree_metadata_fingerprint,
    prepare_disposable_representation_view, resolve_output_outside_tree, write_private_json_atomic,
};

#[test]
fn container_worker_overrides_the_image_entrypoint_with_python() {
    let arguments = gte_container_prefix_arguments(
        "phase3-worker",
        "/bundle/source:/bundle:ro",
        "oracle@example",
    );
    let arguments = arguments
        .iter()
        .map(|argument| argument.to_string_lossy().into_owned())
        .collect::<Vec<_>>();

    assert_eq!(
        &arguments[arguments.len() - 3..],
        ["--entrypoint", "/opt/gte-venv/bin/python", "oracle@example"]
    );
}

#[test]
fn disposable_representation_view_copies_identity_and_only_links_large_data() {
    let temp = tempfile::tempdir().expect("temporary directory");
    let source = temp.path().join("rental-representation");
    fs::create_dir_all(source.join("index")).expect("create source index");
    fs::create_dir_all(source.join("shards/000000")).expect("create source shard");
    fs::write(source.join("manifest.json"), b"manifest").expect("write source manifest");
    fs::write(source.join("build-identity.json"), b"identity")
        .expect("write source build identity");
    fs::write(source.join("verification.json"), b"rental seal")
        .expect("write source verification seal");
    fs::write(source.join("index/event-id-to-row.bin"), b"index").expect("write source index");
    fs::write(source.join("shards/000000/vectors.f32le"), b"vectors")
        .expect("write source vectors");
    let before = immutable_tree_metadata_fingerprint(&source).expect("fingerprint source before");
    let view = temp.path().join("disposable-representation");

    let observation = prepare_disposable_representation_view(&source, &view)
        .expect("prepare disposable representation view");

    assert_eq!(observation.source_metadata_before(), before);
    assert_eq!(observation.source_metadata_after(), before);
    assert_eq!(fs::read(view.join("manifest.json")).unwrap(), b"manifest");
    assert_eq!(
        fs::read(view.join("build-identity.json")).unwrap(),
        b"identity"
    );
    assert!(!view.join("verification.json").exists());
    assert!(
        fs::symlink_metadata(view.join("index"))
            .unwrap()
            .file_type()
            .is_symlink()
    );
    assert!(
        fs::symlink_metadata(view.join("shards"))
            .unwrap()
            .file_type()
            .is_symlink()
    );
    assert_eq!(
        fs::canonicalize(view.join("index")).unwrap(),
        fs::canonicalize(source.join("index")).unwrap()
    );
    assert_eq!(
        fs::canonicalize(view.join("shards")).unwrap(),
        fs::canonicalize(source.join("shards")).unwrap()
    );
}

#[test]
fn disposable_representation_view_rejects_an_output_inside_source_without_creating_parents() {
    let temp = tempfile::tempdir().expect("temporary directory");
    let source = temp.path().join("rental-representation");
    fs::create_dir_all(source.join("index")).expect("create source index");
    fs::create_dir_all(source.join("shards")).expect("create source shards");
    fs::write(source.join("manifest.json"), b"manifest").expect("write source manifest");
    fs::write(source.join("build-identity.json"), b"identity")
        .expect("write source build identity");
    let forbidden_parent = source.join("generated");

    assert!(
        prepare_disposable_representation_view(&source, forbidden_parent.join("view")).is_err()
    );
    assert!(!forbidden_parent.exists());
}

#[test]
fn content_tree_identity_ignores_permission_refreshes_but_covers_file_bytes() {
    let temp = tempfile::tempdir().expect("temporary directory");
    let cache = temp.path().join("cache");
    fs::create_dir(&cache).expect("create cache");
    let response = cache.join("vectors.json");
    fs::write(&response, b"cached vectors").expect("write cached response");
    let before = immutable_content_tree_identity(&cache).expect("content identity before chmod");

    fs::set_permissions(&cache, fs::Permissions::from_mode(0o700)).expect("refresh cache mode");
    fs::set_permissions(&response, fs::Permissions::from_mode(0o600))
        .expect("refresh response mode");

    assert_eq!(
        immutable_content_tree_identity(&cache).expect("content identity after chmod"),
        before
    );
    fs::write(&response, b"changed cached vectors").expect("change cached response");
    assert_ne!(
        immutable_content_tree_identity(&cache).expect("content identity after byte change"),
        before
    );
}

#[test]
fn output_resolution_rejects_direct_and_symlinked_paths_inside_immutable_tree() {
    let temp = tempfile::tempdir().expect("temporary directory");
    let immutable = temp.path().join("rental");
    let output_root = temp.path().join("outputs");
    fs::create_dir(&immutable).expect("create immutable tree");
    fs::create_dir(&output_root).expect("create output root");

    assert!(resolve_output_outside_tree(&immutable, immutable.join("work")).is_err());
    std::os::unix::fs::symlink(&immutable, output_root.join("rental-link"))
        .expect("link output parent to immutable tree");
    assert!(
        resolve_output_outside_tree(&immutable, output_root.join("rental-link/report.json"))
            .is_err()
    );
    assert_eq!(
        resolve_output_outside_tree(&immutable, output_root.join("safe.json"))
            .expect("resolve safe output"),
        output_root.join("safe.json")
    );
    assert!(!immutable.join("work").exists());
}

#[test]
fn preflight_owned_directories_and_json_are_owner_only() {
    let temp = tempfile::tempdir().expect("temporary directory");
    let workspace = temp.path().join("workspace");
    create_private_preflight_directory(&workspace).expect("create private workspace");
    assert_eq!(
        fs::metadata(&workspace).unwrap().permissions().mode() & 0o777,
        0o700
    );

    let binding = workspace.join("binding.json");
    write_private_json_atomic(&binding, &serde_json::json!({"seed": "private"}))
        .expect("write private binding");
    assert_eq!(
        fs::metadata(binding).unwrap().permissions().mode() & 0o777,
        0o600
    );
}
