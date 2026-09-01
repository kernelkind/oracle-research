use oracle_mvp::fine_region_candidate::{
    CANDIDATE_INPUT_CONTRACT_VERSION, FineRegionCandidateInput,
    HDBSCAN_CONTROLLED_SUITE_CONFIG_JSON_V1, HDBSCAN_CONTROLLED_SUITE_CONFIG_V1,
    HDBSCAN_CONTROLLED_SUITE_CONFIG_VERSION, HDBSCAN_FINE_OUTPUT_SELECTOR_VERSION,
    SNN_CONTROLLED_SUITE_CONFIG_JSON_V1, SNN_CONTROLLED_SUITE_CONFIG_V1,
    SNN_CONTROLLED_SUITE_CONFIG_VERSION, SNN_FINE_OUTPUT_SELECTOR_VERSION, run_hdbscan_candidate,
    run_snn_candidate,
};
use oracle_mvp::fine_region_hdbscan::{ClusterSelectionMethod, HdbscanConfig};
use oracle_mvp::fine_region_snn::SnnConfig;

fn opaque_id(value: u8) -> String {
    format!("{value:064x}")
}

fn unit_vector(angle: f64) -> Vec<f64> {
    vec![angle.cos(), angle.sin()]
}

fn input(value: u8, angle: f64) -> FineRegionCandidateInput {
    FineRegionCandidateInput {
        opaque_id: opaque_id(value),
        normalized_vector: unit_vector(angle),
    }
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
fn snn_candidate_canonicalizes_input_order_and_returns_opaque_ids() {
    let inputs = vec![
        input(8, 1.03),
        input(2, 0.01),
        input(6, 1.01),
        input(4, 0.03),
        input(1, 0.00),
        input(7, 1.02),
        input(3, 0.02),
        input(5, 1.00),
    ];
    let mut reversed = inputs.clone();
    reversed.reverse();

    let first = run_snn_candidate(&inputs, &snn_config()).expect("run canonical SNN candidate");
    let second = run_snn_candidate(&reversed, &snn_config()).expect("run reversed SNN candidate");

    assert_eq!(first, second);
    assert_eq!(
        first.input_contract_version,
        CANDIDATE_INPUT_CONTRACT_VERSION
    );
    assert_eq!(
        first.fine_output_selector_version,
        SNN_FINE_OUTPUT_SELECTOR_VERSION
    );
    assert_eq!(
        first.canonical_unique_ids,
        (1..=8).map(opaque_id).collect::<Vec<_>>()
    );
    assert_eq!(
        first.fine_output.segments,
        vec![
            (1..=4).map(opaque_id).collect::<Vec<_>>(),
            (5..=8).map(opaque_id).collect::<Vec<_>>(),
        ]
    );
    assert!(first.fine_output.unassigned.is_empty());
}

#[test]
fn snn_candidate_collapses_exact_vectors_and_expands_their_aliases() {
    let base = vec![
        input(10, 0.00),
        input(20, 0.01),
        input(30, 0.02),
        input(40, 0.03),
        input(50, 1.00),
        input(60, 1.01),
        input(70, 1.02),
        input(80, 1.03),
    ];
    let mut with_alias = base.clone();
    with_alias.push(FineRegionCandidateInput {
        opaque_id: opaque_id(11),
        normalized_vector: base[0].normalized_vector.clone(),
    });

    let baseline = run_snn_candidate(&base, &snn_config()).expect("run baseline SNN candidate");
    let aliased = run_snn_candidate(&with_alias, &snn_config()).expect("run aliased SNN candidate");

    let original_ids = base
        .iter()
        .map(|item| item.opaque_id.as_str())
        .collect::<std::collections::BTreeSet<_>>();
    let projected = aliased
        .fine_output
        .segments
        .iter()
        .map(|segment| {
            segment
                .iter()
                .filter(|id| original_ids.contains(id.as_str()))
                .cloned()
                .collect::<Vec<_>>()
        })
        .collect::<Vec<_>>();

    assert_eq!(projected, baseline.fine_output.segments);
    assert_eq!(aliased.alias_groups[0], vec![opaque_id(10), opaque_id(11)]);
    assert!(
        aliased
            .fine_output
            .segments
            .iter()
            .any(|segment| segment.contains(&opaque_id(10)) && segment.contains(&opaque_id(11)))
    );
}

#[test]
fn hdbscan_candidate_accepts_exact_aliases_and_is_input_order_independent() {
    let mut inputs = vec![
        input(10, 0.00),
        input(20, 0.01),
        input(30, 0.02),
        input(40, 1.00),
        input(50, 1.01),
        input(60, 1.02),
        input(70, 2.50),
    ];
    inputs.push(FineRegionCandidateInput {
        opaque_id: opaque_id(11),
        normalized_vector: inputs[0].normalized_vector.clone(),
    });
    inputs.push(FineRegionCandidateInput {
        opaque_id: opaque_id(71),
        normalized_vector: inputs[6].normalized_vector.clone(),
    });
    let mut reversed = inputs.clone();
    reversed.reverse();

    let first =
        run_hdbscan_candidate(&inputs, hdbscan_config()).expect("run canonical HDBSCAN candidate");
    let second =
        run_hdbscan_candidate(&reversed, hdbscan_config()).expect("run reversed HDBSCAN candidate");

    assert_eq!(first, second);
    assert_eq!(
        first.input_contract_version,
        CANDIDATE_INPUT_CONTRACT_VERSION
    );
    assert_eq!(
        first.fine_output_selector_version,
        HDBSCAN_FINE_OUTPUT_SELECTOR_VERSION
    );
    assert_eq!(
        first.fine_output.segments,
        vec![
            vec![opaque_id(10), opaque_id(11), opaque_id(20), opaque_id(30)],
            vec![opaque_id(40), opaque_id(50), opaque_id(60)],
        ]
    );
    assert_eq!(
        first.fine_output.unassigned,
        vec![opaque_id(70), opaque_id(71)]
    );
    assert_eq!(
        first.alias_groups,
        vec![
            vec![opaque_id(10), opaque_id(11)],
            vec![opaque_id(20)],
            vec![opaque_id(30)],
            vec![opaque_id(40)],
            vec![opaque_id(50)],
            vec![opaque_id(60)],
            vec![opaque_id(70), opaque_id(71)],
        ]
    );
}

#[test]
fn candidate_rejects_invalid_or_repeated_opaque_ids() {
    let invalid = vec![FineRegionCandidateInput {
        opaque_id: "not-an-opaque-id".to_owned(),
        normalized_vector: unit_vector(0.0),
    }];
    let error =
        run_snn_candidate(&invalid, &snn_config()).expect_err("invalid opaque ID must be rejected");
    assert!(error.to_string().contains("64 lowercase hexadecimal"));

    let repeated = vec![input(1, 0.0), input(1, 1.0), input(2, 2.0), input(3, 3.0)];
    let error = run_snn_candidate(&repeated, &snn_config())
        .expect_err("repeated opaque ID must be rejected");
    assert!(error.to_string().contains("unique"));
}

#[test]
fn controlled_suite_candidate_configurations_have_frozen_canonical_bytes() {
    assert_eq!(
        SNN_CONTROLLED_SUITE_CONFIG_VERSION,
        "snn-controlled-suite-config-v1"
    );
    assert_eq!(
        serde_json::to_string(&SNN_CONTROLLED_SUITE_CONFIG_V1)
            .expect("serialize frozen SNN configuration"),
        SNN_CONTROLLED_SUITE_CONFIG_JSON_V1
    );
    assert_eq!(
        SNN_CONTROLLED_SUITE_CONFIG_JSON_V1,
        r#"{"neighbor_count":5,"minimum_shared_neighbor_count":2,"minimum_core_neighbor_count":3}"#
    );

    assert_eq!(
        HDBSCAN_CONTROLLED_SUITE_CONFIG_VERSION,
        "hdbscan-controlled-suite-config-v1"
    );
    assert_eq!(
        serde_json::to_string(&HDBSCAN_CONTROLLED_SUITE_CONFIG_V1)
            .expect("serialize frozen HDBSCAN configuration"),
        HDBSCAN_CONTROLLED_SUITE_CONFIG_JSON_V1
    );
    assert_eq!(
        HDBSCAN_CONTROLLED_SUITE_CONFIG_JSON_V1,
        r#"{"min_samples":2,"min_cluster_size":2,"selection_method":"excess_of_mass"}"#
    );
}
