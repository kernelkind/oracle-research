use std::collections::BTreeMap;
use std::fs;
use std::process::{Command, Output};

use oracle_mvp::fine_region_candidate::{
    FineRegionCandidateInput, HDBSCAN_CONTROLLED_SUITE_CONFIG_V1, HdbscanCandidateRun,
    SNN_CONTROLLED_SUITE_CONFIG_V1, run_hdbscan_candidate, run_hdbscan_cross_note_candidate,
};
use oracle_mvp::fine_region_candidate_artifact::{
    HdbscanCrossNoteCandidateArtifact, build_hdbscan_candidate_artifact,
    build_hdbscan_cross_note_candidate_artifact, build_snn_candidate_artifact,
    verify_hdbscan_candidate_artifact, verify_hdbscan_cross_note_candidate_artifact,
};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};

fn id(value: u8) -> String {
    format!("{value:064x}")
}

fn hash_bytes(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}

fn inputs() -> Vec<FineRegionCandidateInput> {
    [0.0_f64, 0.01, 0.4, 1.0, 1.01, 1.4]
        .into_iter()
        .enumerate()
        .map(|(index, angle)| FineRegionCandidateInput {
            opaque_id: id(index as u8 + 1),
            normalized_vector: vec![angle.cos(), angle.sin()],
        })
        .collect()
}

fn source_notes() -> BTreeMap<String, String> {
    [10, 10, 20, 10, 20, 30]
        .into_iter()
        .enumerate()
        .map(|(index, note)| (id(index as u8 + 1), id(note)))
        .collect()
}

fn request() -> Value {
    json!({
        "schema_version": 1,
        "candidate": "hdbscan_cross_note",
        "source_vector_manifest_sha256": "a".repeat(64),
        "normalized_vector_sha256": "b".repeat(64),
        "inputs": inputs(),
        "source_note_ids": source_notes(),
    })
}

fn execute(request: &Value) -> Output {
    let directory = tempfile::tempdir_in("/dev/shm").unwrap();
    let path = directory.path().join("request.json");
    fs::write(&path, serde_json::to_vec(request).unwrap()).unwrap();
    Command::new(env!("CARGO_BIN_EXE_fine-segmentation-candidate"))
        .arg(path)
        .output()
        .expect("run fresh-process candidate")
}

fn successful_response(request: &Value) -> Value {
    let output = execute(request);
    assert!(
        output.status.success(),
        "candidate failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert!(output.stderr.is_empty());
    serde_json::from_slice(&output.stdout).unwrap()
}

fn run_from(response: &Value) -> HdbscanCandidateRun {
    serde_json::from_value(response["artifact"]["result"].clone()).unwrap()
}

#[test]
fn cross_note_cli_uses_nearest_different_source_note_without_changing_vectors() {
    let response = successful_response(&request());
    let run = run_from(&response);
    let standard = run_hdbscan_candidate(&inputs(), HDBSCAN_CONTROLLED_SUITE_CONFIG_V1).unwrap();
    assert_eq!(run.canonical_unique_ids, standard.canonical_unique_ids);
    assert_eq!(run.alias_groups, standard.alias_groups);
    assert_eq!(
        run.algorithm_result.config,
        HDBSCAN_CONTROLLED_SUITE_CONFIG_V1
    );
    for (actual, expected) in run
        .algorithm_result
        .core_distances
        .iter()
        .zip([0.4, 0.39, 0.39, 0.01, 0.01, 0.39])
    {
        assert!(
            (actual - expected).abs() < 1.0e-12,
            "{actual} != {expected}"
        );
    }
    assert!(standard.algorithm_result.core_distances[0] < 0.02);
    assert!(run.algorithm_result.core_distances[0] > 0.39);
    assert_eq!(
        response["candidate_identity"],
        "hdbscan-cross-note-controlled-suite-config-v1"
    );
    let manifest = &response["artifact"]["manifest"];
    assert_eq!(
        manifest["algorithm_version"],
        "hdbscan-star-cross-note-exact-angular-v1"
    );
    assert_eq!(
        manifest["cross_note"]["core_distance_rule_version"],
        "nearest-different-source-note-angular-v1"
    );
    assert_eq!(
        manifest["cross_note"]["source_note_ids_sha256"],
        hash_bytes(&serde_json::to_vec(&source_notes()).unwrap())
    );
    let baseline = build_hdbscan_candidate_artifact(
        &inputs(),
        &"a".repeat(64),
        &"b".repeat(64),
        &HDBSCAN_CONTROLLED_SUITE_CONFIG_V1,
    )
    .unwrap();
    assert_eq!(
        manifest["canonical_input_sha256"],
        baseline.manifest.canonical_input_sha256
    );
    assert_eq!(
        manifest["normalized_vector_sha256"],
        baseline.manifest.normalized_vector_sha256
    );
}

#[test]
fn cross_note_cli_gathers_every_alias_source_before_computing_unique_vector_cores() {
    let mut request = request();
    let alias = json!({"opaque_id": id(7), "normalized_vector": inputs()[0].normalized_vector});
    request["inputs"].as_array_mut().unwrap().push(alias);
    // The representative belongs to note 10, while its exact alias belongs
    // to note 20. Both sources remain evidence after vector canonicalization.
    request["source_note_ids"][id(7)] = json!(id(20));
    let response = successful_response(&request);
    let run = run_from(&response);
    assert_eq!(run.alias_groups[0], vec![id(1), id(7)]);
    assert_eq!(run.algorithm_result.core_distances.len(), 6);
    assert_eq!(run.algorithm_result.core_distances[0], 0.0);
    // Point 2 belongs to note 10 and can use the alias group's note 20,
    // despite that group also containing note 10 (sets need not be disjoint).
    assert!((run.algorithm_result.core_distances[1] - 0.01).abs() < 1.0e-12);
    let output_groups = run
        .fine_output
        .segments
        .iter()
        .chain(std::iter::once(&run.fine_output.unassigned));
    assert!(
        output_groups
            .into_iter()
            .any(|group| group.contains(&id(1)) && group.contains(&id(7)))
    );
    request["inputs"].as_array_mut().unwrap().reverse();
    assert_eq!(response, successful_response(&request));
    // Repeated vectors from the same note do not create a cross-note witness
    // or add an ordinal to cluster sizes and EOM stability weighting.
    request["source_note_ids"][id(7)] = json!(id(10));
    let same_source = run_from(&successful_response(&request));
    let no_alias = run_from(&successful_response(&self::request()));
    assert_eq!(same_source.algorithm_result, no_alias.algorithm_result);
}

#[test]
fn cross_note_cli_binds_note_identity_even_when_geometry_and_output_are_unchanged() {
    let mut request = request();
    let first = successful_response(&request);
    for note in request["source_note_ids"]
        .as_object_mut()
        .unwrap()
        .values_mut()
    {
        if note == &json!(id(10)) {
            *note = json!(id(40));
        }
    }
    let second = successful_response(&request);
    assert_eq!(first["artifact"]["result"], second["artifact"]["result"]);
    assert_eq!(
        first["artifact"]["manifest"]["canonical_input_sha256"],
        second["artifact"]["manifest"]["canonical_input_sha256"]
    );
    assert_ne!(
        first["artifact"]["manifest"]["cross_note"]["source_note_ids_sha256"],
        second["artifact"]["manifest"]["cross_note"]["source_note_ids_sha256"]
    );
}

#[test]
fn cross_note_cli_rejects_missing_extra_invalid_and_single_note_sources() {
    let mut cases = Vec::new();
    let mut missing_map = request();
    missing_map
        .as_object_mut()
        .unwrap()
        .remove("source_note_ids");
    cases.push((missing_map, "source_note_ids is required"));
    let mut missing_entry = request();
    missing_entry["source_note_ids"]
        .as_object_mut()
        .unwrap()
        .remove(&id(1));
    cases.push((missing_entry, "exactly match the input opaque IDs"));
    let mut extra_entry = request();
    extra_entry["source_note_ids"][id(7)] = json!(id(10));
    cases.push((extra_entry, "exactly match the input opaque IDs"));
    let mut invalid_note = request();
    invalid_note["source_note_ids"][id(1)] = json!("short-note-id");
    cases.push((
        invalid_note,
        "source note IDs must contain exactly 64 lowercase hexadecimal",
    ));
    let mut uppercase_note = request();
    uppercase_note["source_note_ids"][id(1)] = json!("A".repeat(64));
    cases.push((
        uppercase_note,
        "source note IDs must contain exactly 64 lowercase hexadecimal",
    ));
    let mut invalid_opaque = request();
    invalid_opaque["inputs"][0]["opaque_id"] = json!("invalid");
    cases.push((
        invalid_opaque,
        "opaque IDs must contain exactly 64 lowercase hexadecimal",
    ));
    let mut single_note = request();
    for note in single_note["source_note_ids"]
        .as_object_mut()
        .unwrap()
        .values_mut()
    {
        *note = json!(id(10));
    }
    cases.push((single_note, "at least two distinct source notes"));
    let mut unsupported_samples = request();
    unsupported_samples["hdbscan_configuration"] =
        json!({"min_samples":3,"min_cluster_size":2,"selection_method":"excess_of_mass"});
    cases.push((
        unsupported_samples,
        "cross-note core distances require min_samples=2",
    ));
    for (request, expected) in cases {
        let output = execute(&request);
        assert!(
            !output.status.success(),
            "accepted invalid request: {request}"
        );
        assert!(output.stdout.is_empty());
        let error = String::from_utf8_lossy(&output.stderr);
        assert!(
            error.contains(expected),
            "expected {expected:?}, got {error}"
        );
    }
}

#[test]
fn cross_note_cli_supports_explicit_configuration_without_relabeling_baseline() {
    let mut request = request();
    request["hdbscan_configuration"] =
        json!({"min_samples":2,"min_cluster_size":3,"selection_method":"leaf"});
    let response = successful_response(&request);
    assert_eq!(
        response["candidate_identity"],
        "hdbscan-cross-note-explicit-config-v1"
    );
    assert_eq!(
        response["artifact"]["manifest"]["parameters"],
        request["hdbscan_configuration"]
    );
}

#[test]
fn standard_candidates_keep_their_artifact_shape_and_reject_unused_source_maps() {
    let mut request = request();
    request.as_object_mut().unwrap().remove("source_note_ids");
    for (name, expected) in [
        (
            "hdbscan",
            serde_json::to_value(
                build_hdbscan_candidate_artifact(
                    &inputs(),
                    &"a".repeat(64),
                    &"b".repeat(64),
                    &HDBSCAN_CONTROLLED_SUITE_CONFIG_V1,
                )
                .unwrap(),
            )
            .unwrap(),
        ),
        (
            "snn",
            serde_json::to_value(
                build_snn_candidate_artifact(
                    &inputs(),
                    &"a".repeat(64),
                    &"b".repeat(64),
                    &SNN_CONTROLLED_SUITE_CONFIG_V1,
                )
                .unwrap(),
            )
            .unwrap(),
        ),
    ] {
        request["candidate"] = json!(name);
        let response = successful_response(&request);
        assert_eq!(response["artifact"], expected);
        assert!(
            !response["artifact"]["manifest"]
                .as_object()
                .unwrap()
                .contains_key("cross_note")
        );
        request["source_note_ids"] = json!(source_notes());
        let output = execute(&request);
        assert!(!output.status.success());
        assert!(
            String::from_utf8_lossy(&output.stderr)
                .contains("source_note_ids requires candidate `hdbscan_cross_note`")
        );
        request.as_object_mut().unwrap().remove("source_note_ids");
    }
}

#[test]
fn cross_note_adapter_and_verifier_bind_complete_note_mapping_and_recompute_result() {
    let inputs = inputs();
    let notes = source_notes();
    let source_hash = "a".repeat(64);
    let vector_hash = "b".repeat(64);
    let config = HDBSCAN_CONTROLLED_SUITE_CONFIG_V1;
    let artifact = build_hdbscan_cross_note_candidate_artifact(
        &inputs,
        &notes,
        &source_hash,
        &vector_hash,
        &config,
    )
    .unwrap();
    let run = run_hdbscan_cross_note_candidate(&inputs, &notes, config).unwrap();
    assert_eq!(artifact.result, run);
    assert_eq!(
        serde_json::to_value(&artifact).unwrap(),
        successful_response(&request())["artifact"]
    );
    let verify = |retained: &HdbscanCrossNoteCandidateArtifact,
                  supplied_notes: &BTreeMap<String, String>| {
        verify_hdbscan_cross_note_candidate_artifact(
            retained,
            &inputs,
            supplied_notes,
            &source_hash,
            &vector_hash,
            &config,
        )
    };
    verify(&artifact, &notes).unwrap();

    let mut renamed_notes = notes.clone();
    for note in renamed_notes.values_mut() {
        if *note == id(10) {
            *note = id(40);
        }
    }
    assert_eq!(
        run,
        run_hdbscan_cross_note_candidate(&inputs, &renamed_notes, config).unwrap()
    );
    assert!(
        verify(&artifact, &renamed_notes).is_err(),
        "note identities must bind even if all core distances agree"
    );
    let mut missing_notes = notes.clone();
    missing_notes.remove(&id(1));
    assert!(verify(&artifact, &missing_notes).is_err());
    assert!(run_hdbscan_cross_note_candidate(&inputs, &missing_notes, config).is_err());
    let mut extra_notes = notes.clone();
    extra_notes.insert(id(7), id(10));
    assert!(verify(&artifact, &extra_notes).is_err());

    let mut forged = artifact.clone();
    forged.result.algorithm_result.core_distances[0] += 0.1;
    forged.manifest.result_sha256 = hash_bytes(&serde_json::to_vec(&forged.result).unwrap());
    assert!(
        verify(&forged, &notes).is_err(),
        "rehashing a forged core must not replace recomputation"
    );
    let mut wrong_hash = artifact.clone();
    wrong_hash
        .manifest
        .cross_note
        .as_mut()
        .unwrap()
        .source_note_ids_sha256 = "0".repeat(64);
    assert!(verify(&wrong_hash, &notes).is_err());
    let mut wrong_rule = artifact.clone();
    wrong_rule
        .manifest
        .cross_note
        .as_mut()
        .unwrap()
        .core_distance_rule_version = "different-rule".to_owned();
    assert!(verify(&wrong_rule, &notes).is_err());
    let mut absent_metadata = artifact.clone();
    absent_metadata.manifest.cross_note = None;
    assert!(verify(&absent_metadata, &notes).is_err());

    assert!(
        verify_hdbscan_candidate_artifact(&artifact, &inputs, &source_hash, &vector_hash, &config)
            .is_err()
    );
    let baseline =
        build_hdbscan_candidate_artifact(&inputs, &source_hash, &vector_hash, &config).unwrap();
    verify_hdbscan_candidate_artifact(&baseline, &inputs, &source_hash, &vector_hash, &config)
        .unwrap();
    assert!(
        verify(&baseline, &notes).is_err(),
        "standard artifacts must not masquerade as cross-note artifacts"
    );
}
