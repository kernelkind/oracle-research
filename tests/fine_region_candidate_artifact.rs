use oracle_mvp::fine_region_candidate::{
    CANDIDATE_INPUT_CONTRACT_VERSION, FineRegionCandidateInput,
    HDBSCAN_CONTROLLED_SUITE_CONFIG_JSON_V1, HDBSCAN_CONTROLLED_SUITE_CONFIG_V1,
    HDBSCAN_FINE_OUTPUT_SELECTOR_VERSION, SNN_CONTROLLED_SUITE_CONFIG_JSON_V1,
    SNN_CONTROLLED_SUITE_CONFIG_V1, SNN_FINE_OUTPUT_SELECTOR_VERSION,
};
use oracle_mvp::fine_region_candidate_artifact::{
    CANDIDATE_ARTIFACT_SCHEMA_VERSION, HDBSCAN_ALGORITHM_VERSION, HDBSCAN_TIE_RULE_VERSION,
    SNN_ALGORITHM_VERSION, SNN_TIE_RULE_VERSION, build_hdbscan_candidate_artifact,
    build_snn_candidate_artifact, verify_hdbscan_candidate_artifact, verify_snn_candidate_artifact,
};
use oracle_mvp::fine_region_hdbscan::{ClusterSelectionMethod, HdbscanConfig};
use oracle_mvp::fine_region_snn::SnnConfig;

fn opaque_id(value: u8) -> String {
    format!("{value:064x}")
}

fn input(value: u8, angle: f64) -> FineRegionCandidateInput {
    FineRegionCandidateInput {
        opaque_id: opaque_id(value),
        normalized_vector: vec![angle.cos(), angle.sin()],
    }
}

fn inputs() -> Vec<FineRegionCandidateInput> {
    [0.0_f64, 0.02, 0.04, 1.0, 1.02, 1.04]
        .into_iter()
        .enumerate()
        .map(|(ordinal, angle)| input(ordinal as u8 + 1, angle))
        .collect()
}

fn snn_config() -> SnnConfig {
    SNN_CONTROLLED_SUITE_CONFIG_V1.clone()
}

fn hdbscan_config() -> HdbscanConfig {
    HDBSCAN_CONTROLLED_SUITE_CONFIG_V1
}

#[test]
fn candidate_artifacts_bind_and_recompute_both_production_algorithms() {
    let inputs = inputs();
    let source_manifest_sha256 = "a".repeat(64);
    let normalized_vector_sha256 = "b".repeat(64);

    let snn = build_snn_candidate_artifact(
        &inputs,
        &source_manifest_sha256,
        &normalized_vector_sha256,
        &snn_config(),
    )
    .expect("build SNN candidate artifact");
    assert_eq!(
        snn.manifest.schema_version,
        CANDIDATE_ARTIFACT_SCHEMA_VERSION
    );
    assert_eq!(snn.manifest.algorithm_version, SNN_ALGORITHM_VERSION);
    assert_eq!(snn.manifest.tie_rule_version, SNN_TIE_RULE_VERSION);
    assert_eq!(
        snn.manifest.input_contract_version,
        CANDIDATE_INPUT_CONTRACT_VERSION
    );
    assert_eq!(
        snn.manifest.fine_output_selector_version,
        SNN_FINE_OUTPUT_SELECTOR_VERSION
    );
    assert_eq!(snn.manifest.parameters, snn_config());
    assert_eq!(
        snn.canonical_configuration_json,
        SNN_CONTROLLED_SUITE_CONFIG_JSON_V1
    );
    assert_eq!(
        snn.manifest.configuration_sha256,
        "a7ddf6fb4125017551f7281d68e888121528e794882ed781bdc6b037eb1f4c4a"
    );
    assert_eq!(snn.manifest.vector_count, inputs.len());
    assert_eq!(snn.manifest.unique_vector_count, inputs.len());
    assert_eq!(
        snn.canonical_input_ids,
        (1..=6).map(opaque_id).collect::<Vec<_>>()
    );
    assert!(is_lower_sha256(
        &snn.manifest.adapter_implementation_source_sha256
    ));
    assert!(is_lower_sha256(
        &snn.manifest.algorithm_implementation_source_sha256
    ));
    assert!(is_lower_sha256(
        &snn.manifest.preprocessing_implementation_source_sha256
    ));
    assert!(is_lower_sha256(&snn.manifest.canonical_input_sha256));
    assert!(is_lower_sha256(&snn.manifest.result_sha256));
    assert!(is_lower_sha256(&snn.manifest.fine_output_sha256));
    assert_eq!(
        snn.canonical_fine_output_json,
        serde_json::to_string(&snn.result.fine_output).expect("serialize selected fine output")
    );
    verify_snn_candidate_artifact(
        &snn,
        &inputs,
        &source_manifest_sha256,
        &normalized_vector_sha256,
        &snn_config(),
    )
    .expect("verify SNN by deterministic recomputation");

    let hdbscan = build_hdbscan_candidate_artifact(
        &inputs,
        &source_manifest_sha256,
        &normalized_vector_sha256,
        &hdbscan_config(),
    )
    .expect("build HDBSCAN* candidate artifact");
    assert_eq!(
        hdbscan.manifest.algorithm_version,
        HDBSCAN_ALGORITHM_VERSION
    );
    assert_eq!(hdbscan.manifest.tie_rule_version, HDBSCAN_TIE_RULE_VERSION);
    assert_eq!(
        hdbscan.manifest.input_contract_version,
        CANDIDATE_INPUT_CONTRACT_VERSION
    );
    assert_eq!(
        hdbscan.manifest.fine_output_selector_version,
        HDBSCAN_FINE_OUTPUT_SELECTOR_VERSION
    );
    assert_eq!(hdbscan.manifest.parameters, hdbscan_config());
    assert_eq!(
        hdbscan.canonical_configuration_json,
        HDBSCAN_CONTROLLED_SUITE_CONFIG_JSON_V1
    );
    assert_eq!(
        hdbscan.manifest.configuration_sha256,
        "b762e2a82577496db94b670ff5076da387465719a151621a1643f7e8a15c6445"
    );
    assert_eq!(hdbscan.manifest.vector_count, inputs.len());
    assert!(is_lower_sha256(
        &hdbscan.manifest.adapter_implementation_source_sha256
    ));
    assert!(is_lower_sha256(
        &hdbscan.manifest.algorithm_implementation_source_sha256
    ));
    assert!(is_lower_sha256(
        &hdbscan.manifest.preprocessing_implementation_source_sha256
    ));
    assert!(is_lower_sha256(&hdbscan.manifest.canonical_input_sha256));
    assert!(is_lower_sha256(&hdbscan.manifest.result_sha256));
    assert!(is_lower_sha256(&hdbscan.manifest.fine_output_sha256));
    assert_eq!(
        hdbscan.canonical_fine_output_json,
        serde_json::to_string(&hdbscan.result.fine_output).expect("serialize selected fine output")
    );
    verify_hdbscan_candidate_artifact(
        &hdbscan,
        &inputs,
        &source_manifest_sha256,
        &normalized_vector_sha256,
        &hdbscan_config(),
    )
    .expect("verify HDBSCAN* by deterministic recomputation");

    let encoded = serde_json::to_vec(&hdbscan).expect("serialize artifact");
    let decoded = serde_json::from_slice(&encoded).expect("deserialize artifact");
    assert_eq!(hdbscan, decoded);
}

#[test]
fn verification_rejects_configuration_bytes_hash_and_caller_drift() {
    let inputs = inputs();
    let source_manifest_sha256 = "a".repeat(64);
    let normalized_vector_sha256 = "b".repeat(64);

    let mut changed_bytes = build_snn_candidate_artifact(
        &inputs,
        &source_manifest_sha256,
        &normalized_vector_sha256,
        &snn_config(),
    )
    .expect("build SNN candidate artifact");
    changed_bytes.canonical_configuration_json.push(' ');
    let error = verify_snn_candidate_artifact(
        &changed_bytes,
        &inputs,
        &source_manifest_sha256,
        &normalized_vector_sha256,
        &snn_config(),
    )
    .expect_err("changed configuration bytes must fail verification");
    assert!(error.to_string().contains("deterministic recomputation"));

    let mut changed_hash = build_snn_candidate_artifact(
        &inputs,
        &source_manifest_sha256,
        &normalized_vector_sha256,
        &snn_config(),
    )
    .expect("build SNN candidate artifact");
    changed_hash.manifest.configuration_sha256 = "0".repeat(64);
    let error = verify_snn_candidate_artifact(
        &changed_hash,
        &inputs,
        &source_manifest_sha256,
        &normalized_vector_sha256,
        &snn_config(),
    )
    .expect_err("changed configuration hash must fail verification");
    assert!(error.to_string().contains("deterministic recomputation"));

    let snn = build_snn_candidate_artifact(
        &inputs,
        &source_manifest_sha256,
        &normalized_vector_sha256,
        &snn_config(),
    )
    .expect("build SNN candidate artifact");
    let different_snn_config = SnnConfig {
        neighbor_count: 4,
        ..snn_config()
    };
    let error = verify_snn_candidate_artifact(
        &snn,
        &inputs,
        &source_manifest_sha256,
        &normalized_vector_sha256,
        &different_snn_config,
    )
    .expect_err("changed caller SNN configuration must fail verification");
    assert!(error.to_string().contains("deterministic recomputation"));

    let hdbscan = build_hdbscan_candidate_artifact(
        &inputs,
        &source_manifest_sha256,
        &normalized_vector_sha256,
        &hdbscan_config(),
    )
    .expect("build HDBSCAN* candidate artifact");
    let different_hdbscan_config = HdbscanConfig {
        selection_method: ClusterSelectionMethod::Leaf,
        ..hdbscan_config()
    };
    let error = verify_hdbscan_candidate_artifact(
        &hdbscan,
        &inputs,
        &source_manifest_sha256,
        &normalized_vector_sha256,
        &different_hdbscan_config,
    )
    .expect_err("changed caller HDBSCAN* configuration must fail verification");
    assert!(error.to_string().contains("deterministic recomputation"));
}

#[test]
fn verification_rejects_changed_results_and_inputs_but_not_arrival_order() {
    let inputs = inputs();
    let source_manifest_sha256 = "a".repeat(64);
    let normalized_vector_sha256 = "b".repeat(64);
    let mut artifact = build_snn_candidate_artifact(
        &inputs,
        &source_manifest_sha256,
        &normalized_vector_sha256,
        &snn_config(),
    )
    .expect("build SNN candidate artifact");

    artifact.manifest.result_sha256 = "0".repeat(64);
    let error = verify_snn_candidate_artifact(
        &artifact,
        &inputs,
        &source_manifest_sha256,
        &normalized_vector_sha256,
        &snn_config(),
    )
    .expect_err("changed result hash must fail verification");
    assert!(error.to_string().contains("deterministic recomputation"));

    let artifact = build_snn_candidate_artifact(
        &inputs,
        &source_manifest_sha256,
        &normalized_vector_sha256,
        &snn_config(),
    )
    .unwrap();
    let mut reordered = inputs.clone();
    reordered.reverse();
    verify_snn_candidate_artifact(
        &artifact,
        &reordered,
        &source_manifest_sha256,
        &normalized_vector_sha256,
        &snn_config(),
    )
    .expect("arrival-order changes must preserve the artifact");

    let mut changed = inputs;
    changed[0].normalized_vector = vec![0.5_f64.cos(), 0.5_f64.sin()];
    let error = verify_snn_candidate_artifact(
        &artifact,
        &changed,
        &source_manifest_sha256,
        &normalized_vector_sha256,
        &snn_config(),
    )
    .expect_err("changed vector input must fail verification");
    assert!(error.to_string().contains("deterministic recomputation"));
}

#[test]
fn construction_rejects_invalid_identity_inputs() {
    let source_manifest_sha256 = "a".repeat(64);
    let normalized_vector_sha256 = "b".repeat(64);

    let mut duplicate_ids = inputs();
    duplicate_ids[1].opaque_id = duplicate_ids[0].opaque_id.clone();
    assert!(
        build_snn_candidate_artifact(
            &duplicate_ids,
            &source_manifest_sha256,
            &normalized_vector_sha256,
            &snn_config(),
        )
        .expect_err("duplicate IDs must fail")
        .to_string()
        .contains("unique")
    );

    let mut invalid_id = inputs();
    invalid_id[2].opaque_id = "opaque-2".to_owned();
    assert!(
        build_snn_candidate_artifact(
            &invalid_id,
            &source_manifest_sha256,
            &normalized_vector_sha256,
            &snn_config(),
        )
        .expect_err("invalid opaque ID must fail")
        .to_string()
        .contains("64 lowercase hexadecimal")
    );

    assert!(
        build_snn_candidate_artifact(
            &inputs(),
            &"A".repeat(64),
            &normalized_vector_sha256,
            &snn_config(),
        )
        .expect_err("uppercase hash must fail")
        .to_string()
        .contains("lowercase")
    );
}

fn is_lower_sha256(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}
