use oracle_mvp::fine_region_candidate::{
    CANDIDATE_INPUT_CONTRACT_VERSION, FineRegionCandidateInput, SNN_FINE_OUTPUT_SELECTOR_VERSION,
};
use oracle_mvp::fine_region_candidate_artifact::build_snn_candidate_artifact;
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

#[test]
fn candidate_artifact_uses_the_canonical_alias_aware_adapter() {
    let mut inputs = vec![
        input(10, 0.00),
        input(20, 0.01),
        input(30, 0.02),
        input(40, 0.03),
        input(50, 1.00),
        input(60, 1.01),
        input(70, 1.02),
        input(80, 1.03),
    ];
    inputs.push(FineRegionCandidateInput {
        opaque_id: opaque_id(11),
        normalized_vector: inputs[0].normalized_vector.clone(),
    });
    let mut reversed = inputs.clone();
    reversed.reverse();
    let config = SnnConfig {
        neighbor_count: 3,
        minimum_shared_neighbor_count: 1,
        minimum_core_neighbor_count: 2,
    };

    let first = build_snn_candidate_artifact(&inputs, &"a".repeat(64), &"b".repeat(64), &config)
        .expect("build canonical candidate artifact");
    let second = build_snn_candidate_artifact(&reversed, &"a".repeat(64), &"b".repeat(64), &config)
        .expect("build reversed candidate artifact");

    assert_eq!(first, second);
    assert_eq!(
        first.manifest.input_contract_version,
        CANDIDATE_INPUT_CONTRACT_VERSION
    );
    assert_eq!(
        first.manifest.fine_output_selector_version,
        SNN_FINE_OUTPUT_SELECTOR_VERSION
    );
    assert_eq!(
        first.result.alias_groups[0],
        vec![opaque_id(10), opaque_id(11)]
    );
    assert_eq!(first.manifest.vector_count, 9);
    assert_eq!(first.manifest.unique_vector_count, 8);
}
