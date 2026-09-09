use std::collections::BTreeMap;

use oracle_mvp::fine_region_candidate::{
    FineRegionCandidateInput, HDBSCAN_CONTROLLED_SUITE_CONFIG_V1, run_hdbscan_cross_note_candidate,
    run_hdbscan_cross_note_edges_candidate,
};
use oracle_mvp::fine_region_candidate_artifact::{
    build_hdbscan_cross_note_candidate_artifact, build_hdbscan_cross_note_edges_candidate_artifact,
    verify_hdbscan_cross_note_candidate_artifact,
    verify_hdbscan_cross_note_edges_candidate_artifact,
};
use oracle_mvp::fine_region_hdbscan::{
    ClusterSelectionMethod, HdbscanConfig, hdbscan, hdbscan_with_core_distances_and_excluded_edges,
};
use oracle_mvp::fine_region_partition::CosineMatrix;
use sha2::{Digest, Sha256};

fn hash_bytes(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}

fn id(value: usize) -> String {
    format!("{value:064x}")
}

fn inputs() -> (Vec<FineRegionCandidateInput>, BTreeMap<String, String>) {
    let angles = [0.0_f64, 0.4, 0.6, 1.0, 2.0, 2.02];
    let notes = [10, 11, 11, 12, 13, 14];
    (
        angles
            .iter()
            .enumerate()
            .map(|(ordinal, angle)| FineRegionCandidateInput {
                opaque_id: id(ordinal + 1),
                normalized_vector: vec![angle.cos(), angle.sin()],
            })
            .collect(),
        notes
            .iter()
            .enumerate()
            .map(|(ordinal, note)| (id(ordinal + 1), id(*note)))
            .collect(),
    )
}

#[test]
fn multi_source_aliases_keep_edges_with_a_different_note_witness() {
    let (mut inputs, mut notes) = inputs();
    inputs.push(FineRegionCandidateInput {
        opaque_id: id(7),
        normalized_vector: inputs[1].normalized_vector.clone(),
    });
    notes.insert(id(7), id(10));
    let result =
        run_hdbscan_cross_note_edges_candidate(&inputs, &notes, HDBSCAN_CONTROLLED_SUITE_CONFIG_V1)
            .unwrap();
    let baseline =
        run_hdbscan_cross_note_candidate(&inputs, &notes, HDBSCAN_CONTROLLED_SUITE_CONFIG_V1)
            .unwrap();
    assert_eq!(result.alias_groups[1], vec![id(2), id(7)]);
    assert_eq!(result.algorithm_result.core_distances[1], 0.0);
    assert_eq!(
        result.algorithm_result.core_distances,
        baseline.algorithm_result.core_distances
    );
    assert_eq!(result.canonical_unique_ids.len(), 6);
    assert_eq!(result.algorithm_result.minimum_spanning_tree.len(), 5);
    assert!(
        result
            .algorithm_result
            .minimum_spanning_tree
            .iter()
            .any(|edge| edge.left == 1 && edge.right == 2),
        "the representative IDs share note 11, but alias 7 supplies note 10"
    );
    for edge in &result.algorithm_result.minimum_spanning_tree {
        assert!(result.alias_groups[edge.left].iter().any(|left| {
            result.alias_groups[edge.right]
                .iter()
                .any(|right| notes[left] != notes[right])
        }));
    }
    let mut actual_ids = result
        .fine_output
        .segments
        .iter()
        .flatten()
        .chain(result.fine_output.unassigned.iter())
        .cloned()
        .collect::<Vec<_>>();
    actual_ids.sort();
    assert_eq!(actual_ids, (1..=7).map(id).collect::<Vec<_>>());
    inputs.reverse();
    assert_eq!(result, run_hdbscan_cross_note_edges_candidate(
        &inputs, &notes, HDBSCAN_CONTROLLED_SUITE_CONFIG_V1,
    ).unwrap());
}

#[test]
fn same_source_aliases_do_not_enable_excluded_edges() {
    let (mut inputs, mut notes) = inputs();
    let original =
        run_hdbscan_cross_note_edges_candidate(&inputs, &notes, HDBSCAN_CONTROLLED_SUITE_CONFIG_V1)
            .unwrap();
    inputs.push(FineRegionCandidateInput {
        opaque_id: id(7),
        normalized_vector: inputs[1].normalized_vector.clone(),
    });
    notes.insert(id(7), id(11));
    let with_alias =
        run_hdbscan_cross_note_edges_candidate(&inputs, &notes, HDBSCAN_CONTROLLED_SUITE_CONFIG_V1)
            .unwrap();
    assert_eq!(with_alias.algorithm_result, original.algorithm_result);
    assert!(
        !with_alias
            .algorithm_result
            .minimum_spanning_tree
            .iter()
            .any(|edge| edge.left == 1 && edge.right == 2)
    );
}

#[test]
fn artifact_verification_binds_the_edge_policy_and_recomputes_the_complete_result() {
    let (inputs, notes) = inputs();
    let source_hash = "a".repeat(64);
    let vector_hash = "b".repeat(64);
    let config = HDBSCAN_CONTROLLED_SUITE_CONFIG_V1;
    let artifact = build_hdbscan_cross_note_edges_candidate_artifact(
        &inputs,
        &notes,
        &source_hash,
        &vector_hash,
        &config,
    )
    .unwrap();
    verify_hdbscan_cross_note_edges_candidate_artifact(
        &artifact,
        &inputs,
        &notes,
        &source_hash,
        &vector_hash,
        &config,
    )
    .unwrap();
    assert!(
        verify_hdbscan_cross_note_candidate_artifact(
            &artifact,
            &inputs,
            &notes,
            &source_hash,
            &vector_hash,
            &config,
        )
        .is_err()
    );
    let baseline = build_hdbscan_cross_note_candidate_artifact(
        &inputs,
        &notes,
        &source_hash,
        &vector_hash,
        &config,
    )
    .unwrap();
    verify_hdbscan_cross_note_candidate_artifact(
        &baseline,
        &inputs,
        &notes,
        &source_hash,
        &vector_hash,
        &config,
    )
    .unwrap();
    assert!(
        verify_hdbscan_cross_note_edges_candidate_artifact(
            &baseline,
            &inputs,
            &notes,
            &source_hash,
            &vector_hash,
            &config,
        )
        .is_err()
    );

    for wrong_rule in [None, Some("unrecognized-edge-rule".to_owned())] {
        let mut altered = artifact.clone();
        altered
            .manifest
            .cross_note
            .as_mut()
            .unwrap()
            .edge_rule_version = wrong_rule;
        assert!(
            verify_hdbscan_cross_note_edges_candidate_artifact(
                &altered,
                &inputs,
                &notes,
                &source_hash,
                &vector_hash,
                &config,
            )
            .is_err()
        );
    }

    // Rehashing a retained complete-graph result must not turn it into the
    // edge-excluding result. All ordinary integrity checks pass; replay must fail.
    let mut altered = artifact.clone();
    altered.result = baseline.result;
    altered.manifest.result_sha256 = hash_bytes(&serde_json::to_vec(&altered.result).unwrap());
    altered.canonical_fine_output_json =
        serde_json::to_string(&altered.result.fine_output).unwrap();
    altered.manifest.fine_output_sha256 = hash_bytes(altered.canonical_fine_output_json.as_bytes());
    let error = verify_hdbscan_cross_note_edges_candidate_artifact(
        &altered,
        &inputs,
        &notes,
        &source_hash,
        &vector_hash,
        &config,
    )
    .unwrap_err();
    assert!(error.to_string().contains(
        "retained artifact does not match deterministic recomputation from the supplied inputs"
    ));

    // Renaming a sole note changes no geometry or allowed edges, but still
    // changes the external evidence bound by the artifact.
    let mut renamed = notes.clone();
    renamed.insert(id(6), id(15));
    assert_eq!(
        artifact.result,
        run_hdbscan_cross_note_edges_candidate(&inputs, &renamed, config,).unwrap()
    );
    assert!(
        verify_hdbscan_cross_note_edges_candidate_artifact(
            &artifact,
            &inputs,
            &renamed,
            &source_hash,
            &vector_hash,
            &config,
        )
        .is_err()
    );
    let mut reordered = inputs.clone();
    reordered.reverse();
    assert_eq!(
        artifact,
        build_hdbscan_cross_note_edges_candidate_artifact(
            &reordered,
            &notes,
            &source_hash,
            &vector_hash,
            &config,
        )
        .unwrap()
    );
}

fn matrix() -> CosineMatrix {
    CosineMatrix::from_normalized_vectors(
        &inputs()
            .0
            .into_iter()
            .map(|input| input.normalized_vector)
            .collect::<Vec<_>>(),
    )
    .unwrap()
}

#[test]
fn an_empty_exclusion_preserves_all_numeric_production_outputs() {
    let matrix = matrix();
    for min_samples in [1, 2, 3] {
        for selection_method in [
            ClusterSelectionMethod::ExcessOfMass,
            ClusterSelectionMethod::Leaf,
        ] {
            let config = HdbscanConfig {
                min_samples,
                selection_method,
                ..HDBSCAN_CONTROLLED_SUITE_CONFIG_V1
            };
            let original = hdbscan(&matrix, config).unwrap();
            let supplied = hdbscan_with_core_distances_and_excluded_edges(
                &matrix,
                config,
                &original.core_distances,
                &[],
            )
            .unwrap();
            assert_eq!(supplied, original);
        }
    }
}

#[test]
fn numeric_exclusions_are_undirected_and_leave_all_distances_finite() {
    let matrix = matrix();
    let config = HDBSCAN_CONTROLLED_SUITE_CONFIG_V1;
    let original = hdbscan(&matrix, config).unwrap();
    let forward = hdbscan_with_core_distances_and_excluded_edges(
        &matrix,
        config,
        &original.core_distances,
        &[(1, 2)],
    )
    .unwrap();
    let reverse = hdbscan_with_core_distances_and_excluded_edges(
        &matrix,
        config,
        &original.core_distances,
        &[(2, 1), (1, 2)],
    )
    .unwrap();
    assert_eq!(forward, reverse);
    assert!(
        !forward
            .minimum_spanning_tree
            .iter()
            .any(|edge| edge.left == 1 && edge.right == 2)
    );
    assert_eq!(forward.core_distances, original.core_distances);
    for left in 0..matrix.count() {
        for right in 0..matrix.count() {
            assert_eq!(
                forward.mutual_reachability(left, right).unwrap(),
                original.mutual_reachability(left, right).unwrap()
            );
            assert!(
                forward
                    .mutual_reachability(left, right)
                    .unwrap()
                    .is_finite()
            );
        }
    }
}

#[test]
fn numeric_exclusions_reject_invalid_edges_and_disconnected_graphs() {
    let matrix = matrix();
    let config = HDBSCAN_CONTROLLED_SUITE_CONFIG_V1;
    let original = hdbscan(&matrix, config).unwrap();
    for excluded in [[(0, 0)], [(0, 6)], [(usize::MAX, 1)]] {
        let error = hdbscan_with_core_distances_and_excluded_edges(
            &matrix,
            config,
            &original.core_distances,
            &excluded,
        )
        .unwrap_err();
        assert!(
            error
                .to_string()
                .contains("distinct in-bounds input ordinals")
        );
    }
    let excluded = (1..matrix.count())
        .map(|right| (0, right))
        .collect::<Vec<_>>();
    let error = hdbscan_with_core_distances_and_excluded_edges(
        &matrix,
        config,
        &original.core_distances,
        &excluded,
    )
    .unwrap_err();
    assert!(error.to_string().contains("no finite connecting edge"));
}
