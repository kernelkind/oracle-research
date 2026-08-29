use oracle_mvp::fine_region_candidate_artifact::{
    CANDIDATE_ARTIFACT_SCHEMA_VERSION, HDBSCAN_ALGORITHM_VERSION, HDBSCAN_TIE_RULE_VERSION,
    SNN_ALGORITHM_VERSION, SNN_TIE_RULE_VERSION, build_hdbscan_candidate_artifact,
    build_snn_candidate_artifact, verify_hdbscan_candidate_artifact, verify_snn_candidate_artifact,
};
use oracle_mvp::fine_region_hdbscan::{ClusterSelectionMethod, HdbscanConfig};
use oracle_mvp::fine_region_partition::CosineMatrix;
use oracle_mvp::fine_region_snn::SnnConfig;

fn matrix() -> CosineMatrix {
    let vectors = [0.0_f64, 0.02, 0.04, 1.0, 1.02, 1.04]
        .into_iter()
        .map(|angle| vec![angle.cos(), angle.sin()])
        .collect::<Vec<_>>();
    CosineMatrix::from_normalized_vectors(&vectors).expect("valid normalized vectors")
}

fn ordered_ids() -> Vec<String> {
    (0..6).map(|ordinal| format!("opaque-{ordinal}")).collect()
}

fn snn_config() -> SnnConfig {
    SnnConfig {
        neighbor_count: 3,
        minimum_shared_neighbor_count: 1,
        minimum_core_neighbor_count: 2,
    }
}

fn hdbscan_config() -> HdbscanConfig {
    HdbscanConfig {
        min_samples: 2,
        min_cluster_size: 2,
        selection_method: ClusterSelectionMethod::ExcessOfMass,
    }
}

#[test]
fn candidate_artifacts_bind_and_recompute_both_production_algorithms() {
    let cosines = matrix();
    let ids = ordered_ids();
    let source_manifest_sha256 = "a".repeat(64);
    let normalized_vector_sha256 = "b".repeat(64);

    let snn = build_snn_candidate_artifact(
        &cosines,
        &ids,
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
    assert_eq!(snn.manifest.parameters, snn_config());
    assert_eq!(snn.manifest.vector_count, ids.len());
    assert_eq!(snn.ordered_vector_ids, ids);
    assert!(is_lower_sha256(&snn.manifest.implementation_source_sha256));
    assert!(is_lower_sha256(&snn.manifest.ordered_vector_ids_sha256));
    assert!(is_lower_sha256(&snn.manifest.result_sha256));
    verify_snn_candidate_artifact(
        &snn,
        &cosines,
        &ordered_ids(),
        &source_manifest_sha256,
        &normalized_vector_sha256,
        &snn_config(),
    )
    .expect("verify SNN by deterministic recomputation");

    let hdbscan = build_hdbscan_candidate_artifact(
        &cosines,
        &ordered_ids(),
        &source_manifest_sha256,
        &normalized_vector_sha256,
        &hdbscan_config(),
    )
    .expect("build HDBSCAN* candidate artifact");
    assert_eq!(
        hdbscan.manifest.schema_version,
        CANDIDATE_ARTIFACT_SCHEMA_VERSION
    );
    assert_eq!(
        hdbscan.manifest.algorithm_version,
        HDBSCAN_ALGORITHM_VERSION
    );
    assert_eq!(hdbscan.manifest.tie_rule_version, HDBSCAN_TIE_RULE_VERSION);
    assert_eq!(hdbscan.manifest.parameters, hdbscan_config());
    assert_eq!(hdbscan.manifest.vector_count, ordered_ids().len());
    assert!(is_lower_sha256(
        &hdbscan.manifest.implementation_source_sha256
    ));
    assert!(is_lower_sha256(&hdbscan.manifest.ordered_vector_ids_sha256));
    assert!(is_lower_sha256(&hdbscan.manifest.result_sha256));
    verify_hdbscan_candidate_artifact(
        &hdbscan,
        &cosines,
        &ordered_ids(),
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
fn verification_rejects_changed_results_and_inputs() {
    let cosines = matrix();
    let ids = ordered_ids();
    let source_manifest_sha256 = "a".repeat(64);
    let normalized_vector_sha256 = "b".repeat(64);
    let mut artifact = build_snn_candidate_artifact(
        &cosines,
        &ids,
        &source_manifest_sha256,
        &normalized_vector_sha256,
        &snn_config(),
    )
    .expect("build SNN candidate artifact");

    artifact.manifest.result_sha256 = "0".repeat(64);
    let error = verify_snn_candidate_artifact(
        &artifact,
        &cosines,
        &ids,
        &source_manifest_sha256,
        &normalized_vector_sha256,
        &snn_config(),
    )
    .expect_err("changed result hash must fail verification");
    assert!(error.to_string().contains("deterministic recomputation"));

    let mut reordered = ids.clone();
    reordered.swap(0, 1);
    let error = verify_snn_candidate_artifact(
        &build_snn_candidate_artifact(
            &cosines,
            &ids,
            &source_manifest_sha256,
            &normalized_vector_sha256,
            &snn_config(),
        )
        .unwrap(),
        &cosines,
        &reordered,
        &source_manifest_sha256,
        &normalized_vector_sha256,
        &snn_config(),
    )
    .expect_err("changed ordered IDs must fail verification");
    assert!(error.to_string().contains("deterministic recomputation"));
}

#[test]
fn construction_rejects_invalid_identity_inputs() {
    let cosines = matrix();
    let source_manifest_sha256 = "a".repeat(64);
    let normalized_vector_sha256 = "b".repeat(64);

    let mut duplicate_ids = ordered_ids();
    duplicate_ids[1] = duplicate_ids[0].clone();
    assert!(
        build_snn_candidate_artifact(
            &cosines,
            &duplicate_ids,
            &source_manifest_sha256,
            &normalized_vector_sha256,
            &snn_config(),
        )
        .expect_err("duplicate IDs must fail")
        .to_string()
        .contains("unique")
    );

    let mut empty_id = ordered_ids();
    empty_id[2].clear();
    assert!(
        build_snn_candidate_artifact(
            &cosines,
            &empty_id,
            &source_manifest_sha256,
            &normalized_vector_sha256,
            &snn_config(),
        )
        .expect_err("empty ID must fail")
        .to_string()
        .contains("nonempty")
    );

    assert!(
        build_snn_candidate_artifact(
            &cosines,
            &ordered_ids()[..5],
            &source_manifest_sha256,
            &normalized_vector_sha256,
            &snn_config(),
        )
        .expect_err("ID count mismatch must fail")
        .to_string()
        .contains("count")
    );

    assert!(
        build_snn_candidate_artifact(
            &cosines,
            &ordered_ids(),
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
