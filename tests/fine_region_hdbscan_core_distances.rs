use oracle_mvp::fine_region_hdbscan::{
    ClusterSelectionMethod, HdbscanConfig, hdbscan, hdbscan_with_core_distances,
};
use oracle_mvp::fine_region_partition::CosineMatrix;

fn matrix(angles: &[f64]) -> CosineMatrix {
    let vectors = angles
        .iter()
        .map(|angle| vec![angle.cos(), angle.sin()])
        .collect::<Vec<_>>();
    CosineMatrix::from_normalized_vectors(&vectors).expect("valid unit vectors")
}

fn config() -> HdbscanConfig {
    HdbscanConfig {
        min_samples: 2,
        min_cluster_size: 2,
        selection_method: ClusterSelectionMethod::ExcessOfMass,
    }
}

fn angular_distance(cosines: &CosineMatrix, left: usize, right: usize) -> f64 {
    cosines.get(left, right).unwrap().acos()
}

#[test]
fn supplying_ordinary_core_distances_preserves_every_hdbscan_output() {
    let cosines = matrix(&[0.0, 0.002, 0.004, 0.08, 0.082, 0.084, 1.8, 1.802, 1.804]);

    for min_samples in [1, 2, 3] {
        for selection_method in [
            ClusterSelectionMethod::ExcessOfMass,
            ClusterSelectionMethod::Leaf,
        ] {
            let config = HdbscanConfig {
                min_samples,
                selection_method,
                ..config()
            };
            let ordinary = hdbscan(&cosines, config).expect("valid ordinary HDBSCAN input");
            let supplied = hdbscan_with_core_distances(&cosines, config, &ordinary.core_distances)
                .expect("ordinary core distances are valid supplied core distances");

            assert_eq!(supplied, ordinary);
        }
    }
}

#[test]
fn supplied_cross_note_core_distances_delay_same_note_tightness_without_removing_edges() {
    // Ordinals 0 and 1 share one source note; 2 comes from another. Ordinals
    // 3 and 4 share a third source note; 5 comes from a fourth. The caller
    // supplies each ordinal's nearest distance to a different source note.
    let cosines = matrix(&[0.0, 0.01, 0.3, 1.0, 1.01, 1.3]);
    let cores = [
        angular_distance(&cosines, 0, 2),
        angular_distance(&cosines, 1, 2),
        angular_distance(&cosines, 2, 1),
        angular_distance(&cosines, 3, 5),
        angular_distance(&cosines, 4, 5),
        angular_distance(&cosines, 5, 4),
    ];
    let ordinary = hdbscan(&cosines, config()).expect("valid ordinary HDBSCAN input");
    let supplied = hdbscan_with_core_distances(&cosines, config(), &cores)
        .expect("valid supplied core distances");

    assert_eq!(supplied.config, ordinary.config);
    assert_eq!(supplied.core_distances, cores);
    for (left, right) in [(0, 1), (3, 4)] {
        assert!(
            supplied.mutual_reachability(left, right).unwrap()
                > ordinary.mutual_reachability(left, right).unwrap()
        );
        assert_eq!(
            supplied.mutual_reachability(left, right).unwrap(),
            cores[left].max(cores[right])
        );
    }

    for (left, right) in [(0, 2), (1, 2), (3, 5), (4, 5), (2, 3)] {
        assert_eq!(
            supplied.mutual_reachability(left, right).unwrap(),
            angular_distance(&cosines, left, right),
            "raw angular distance remains unchanged when it dominates both cores"
        );
    }
    for left in 0..cosines.count() {
        for right in (left + 1)..cosines.count() {
            assert_eq!(
                supplied.mutual_reachability(left, right).unwrap(),
                angular_distance(&cosines, left, right)
                    .max(cores[left])
                    .max(cores[right]),
                "the full graph retains same-note and different-note edges"
            );
        }
    }
    assert_eq!(supplied.minimum_spanning_tree.len(), cosines.count() - 1);
    assert_eq!(supplied.single_linkage_tree.len(), cosines.count() - 1);
    assert_ne!(
        supplied.minimum_spanning_tree,
        ordinary.minimum_spanning_tree
    );
    assert_ne!(supplied.condensed_tree, ordinary.condensed_tree);
}

#[test]
fn zero_supplied_cores_are_valid_for_deduplicated_multi_source_aliases() {
    let cosines = matrix(&[0.0, 0.1, 1.0, 1.1]);
    let cores = [0.0; 4];
    let result = hdbscan_with_core_distances(&cosines, config(), &cores)
        .expect("zero cores are valid when distinct input directions are nonzero distance");

    assert_eq!(result.core_distances, cores);
    for left in 0..cosines.count() {
        assert_eq!(result.mutual_reachability(left, left).unwrap(), 0.0);
        for right in (left + 1)..cosines.count() {
            assert_eq!(
                result.mutual_reachability(left, right).unwrap(),
                angular_distance(&cosines, left, right)
            );
        }
    }
    assert!(
        result
            .condensed_tree
            .iter()
            .all(|edge| edge.lambda.is_finite())
    );
}

#[test]
fn supplied_cores_do_not_allow_identical_input_directions() {
    let cosines =
        CosineMatrix::from_normalized_vectors(&[vec![1.0, 0.0], vec![1.0, 0.0], vec![0.0, 1.0]])
            .expect("valid unit vectors");

    for cores in [[0.0; 3], [0.1; 3]] {
        let error = hdbscan_with_core_distances(&cosines, config(), &cores)
            .expect_err("exact aliases still belong in upstream deduplication");
        assert!(error.to_string().contains("identical vector directions"));
    }
}

#[test]
fn rejects_supplied_core_counts_that_do_not_match_the_vectors() {
    let cosines = matrix(&[0.0, 0.1, 0.4]);

    for cores in [vec![], vec![0.1; 2], vec![0.1; 4]] {
        let error = hdbscan_with_core_distances(&cosines, config(), &cores)
            .expect_err("each input ordinal must have exactly one supplied core distance");
        assert!(error.to_string().contains("core distances"));
        assert!(error.to_string().contains("count"));
    }
}

#[test]
fn rejects_negative_or_nonfinite_supplied_core_distances() {
    let cosines = matrix(&[0.0, 0.1, 0.4]);

    for invalid_core in [-0.1, f64::NAN, f64::INFINITY, f64::NEG_INFINITY] {
        let error = hdbscan_with_core_distances(&cosines, config(), &[0.1, invalid_core, 0.3])
            .expect_err("supplied core distances must be finite and nonnegative");
        assert!(error.to_string().contains("core distance"));
        assert!(
            error.to_string().contains("1"),
            "identify the invalid input ordinal"
        );
    }
}

#[test]
fn supplying_core_distances_preserves_configuration_validation() {
    let cosines = matrix(&[0.0, 0.1, 0.4]);

    for config in [
        HdbscanConfig {
            min_samples: 0,
            ..config()
        },
        HdbscanConfig {
            min_samples: 4,
            ..config()
        },
        HdbscanConfig {
            min_cluster_size: 1,
            ..config()
        },
        HdbscanConfig {
            min_cluster_size: 4,
            ..config()
        },
    ] {
        assert_eq!(
            hdbscan_with_core_distances(&cosines, config, &[0.1; 3]).unwrap_err(),
            hdbscan(&cosines, config).unwrap_err()
        );
    }
}
