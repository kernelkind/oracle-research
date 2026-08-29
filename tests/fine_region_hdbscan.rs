use std::f64::consts::PI;

use oracle_mvp::fine_region_hdbscan::{ClusterSelectionMethod, HdbscanConfig, hdbscan};
use oracle_mvp::fine_region_partition::CosineMatrix;

fn circle_vectors(angles: &[f64]) -> Vec<Vec<f64>> {
    angles
        .iter()
        .map(|angle| vec![angle.cos(), angle.sin()])
        .collect()
}

fn matrix(angles: &[f64]) -> CosineMatrix {
    CosineMatrix::from_normalized_vectors(&circle_vectors(angles)).expect("valid unit vectors")
}

fn assert_close(actual: f64, expected: f64) {
    assert!(
        (actual - expected).abs() <= 1.0e-12,
        "expected {expected:.16}, got {actual:.16}"
    );
}

#[test]
fn core_and_mutual_reachability_follow_the_published_definition() {
    let paper_mpts_one = hdbscan(
        &matrix(&[0.0, 0.1, 0.4]),
        HdbscanConfig {
            min_samples: 1,
            min_cluster_size: 2,
            selection_method: ClusterSelectionMethod::ExcessOfMass,
        },
    )
    .expect("mpts = 1 is defined by the paper");
    assert_eq!(paper_mpts_one.core_distances, vec![0.0; 3]);
    assert_close(paper_mpts_one.mutual_reachability(0, 2).unwrap(), 0.4);

    let result = hdbscan(
        &matrix(&[0.0, 0.1, 0.4]),
        HdbscanConfig {
            min_samples: 2,
            min_cluster_size: 2,
            selection_method: ClusterSelectionMethod::ExcessOfMass,
        },
    )
    .expect("valid HDBSCAN input");

    // The paper counts self, so min_samples = 2 means nearest-other distance.
    assert_close(result.core_distances[0], 0.1);
    assert_close(result.core_distances[1], 0.1);
    assert_close(result.core_distances[2], 0.3);

    // d_mreach(0, 2) = max(core(0), core(2), angular_distance(0, 2)).
    assert_close(result.mutual_reachability(0, 2).unwrap(), 0.4);
}

#[test]
fn extracts_two_density_clusters_and_leaves_the_bridge_point_as_noise() {
    let cosines = matrix(&[0.0, 0.01, 0.02, 1.0, 1.01, 1.02, 2.5]);
    let result = hdbscan(
        &cosines,
        HdbscanConfig {
            min_samples: 2,
            min_cluster_size: 2,
            selection_method: ClusterSelectionMethod::ExcessOfMass,
        },
    )
    .expect("valid HDBSCAN input");

    assert_eq!(result.clusters.len(), 2);
    assert_eq!(result.clusters[0].members, vec![0, 1, 2]);
    assert_eq!(result.clusters[1].members, vec![3, 4, 5]);
    assert_eq!(result.noise, vec![6]);
    assert_eq!(result.labels[6], None);
    assert_eq!(result.membership_strengths[6], 0.0);
    assert_eq!(
        result.labels,
        vec![Some(0), Some(0), Some(0), Some(1), Some(1), Some(1), None]
    );
    assert_eq!(
        result.membership_strengths,
        vec![1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0]
    );
    // GLOSH uses the maximum lambda at which the point's last cluster *or any
    // descendant* survives: 1 - (1 / 1.48) / 100.
    assert_close(result.outlier_scores[6], 0.993_243_243_243_243_2);

    assert_eq!(result.minimum_spanning_tree.len(), cosines.count() - 1);
    assert_eq!(result.single_linkage_tree.len(), cosines.count() - 1);
    assert_eq!(
        result
            .condensed_tree
            .iter()
            .filter(|edge| edge.child < cosines.count())
            .count(),
        cosines.count(),
        "every vector must leave exactly one condensed-tree cluster"
    );
}

#[test]
fn condensation_keeps_one_surviving_child_and_drops_zero_surviving_children() {
    let cosines = matrix(&[0.0, 0.01, 0.02, 1.0, 1.01, 1.02, 2.5]);
    let result = hdbscan(
        &cosines,
        HdbscanConfig {
            min_samples: 2,
            min_cluster_size: 2,
            selection_method: ClusterSelectionMethod::ExcessOfMass,
        },
    )
    .expect("valid HDBSCAN input");

    let root = cosines.count();
    let bridge_exit = result
        .condensed_tree
        .iter()
        .find(|edge| edge.parent == root && edge.child == 6)
        .expect("the bridge point leaves the root first");
    let root_children = result
        .condensed_tree
        .iter()
        .filter(|edge| edge.parent == root && edge.child >= cosines.count())
        .collect::<Vec<_>>();
    assert_eq!(root_children.len(), 2);
    assert!(
        root_children
            .iter()
            .all(|edge| edge.lambda > bridge_exit.lambda),
        "after one valid child survives, the root ID must persist until its later true split"
    );

    for child in root_children {
        let departures = result
            .condensed_tree
            .iter()
            .filter(|edge| edge.parent == child.child)
            .collect::<Vec<_>>();
        assert_eq!(departures.len(), 3);
        assert!(
            departures.iter().all(|edge| edge.child < cosines.count()),
            "when no valid child survives, the cluster must disappear into points"
        );
    }
}

#[test]
fn eom_and_leaf_selection_are_both_deterministic_production_paths() {
    let cosines = matrix(&[0.0, 0.002, 0.004, 0.08, 0.082, 0.084, 1.8, 1.802, 1.804]);

    for selection_method in [
        ClusterSelectionMethod::ExcessOfMass,
        ClusterSelectionMethod::Leaf,
    ] {
        let config = HdbscanConfig {
            min_samples: 2,
            min_cluster_size: 2,
            selection_method,
        };
        let first = hdbscan(&cosines, config).expect("valid HDBSCAN input");
        let second = hdbscan(&cosines, config).expect("valid HDBSCAN input");

        assert_eq!(first, second);
        assert!(
            first
                .clusters
                .iter()
                .all(|cluster| cluster.id >= cosines.count())
        );
        assert!(
            first
                .membership_strengths
                .iter()
                .all(|value| (0.0..=1.0).contains(value))
        );
        assert!(
            first
                .outlier_scores
                .iter()
                .all(|value| (0.0..=1.0).contains(value))
        );
    }
}

#[test]
fn eom_selects_a_stabler_parent_over_its_descendants() {
    let cosines = matrix(&[0.0, 0.04, 0.08, 0.13, 0.17, 0.21, 2.0, 2.04, 2.08]);
    let config = |selection_method| HdbscanConfig {
        min_samples: 2,
        min_cluster_size: 3,
        selection_method,
    };

    let eom =
        hdbscan(&cosines, config(ClusterSelectionMethod::ExcessOfMass)).expect("valid EOM input");
    let leaf = hdbscan(&cosines, config(ClusterSelectionMethod::Leaf))
        .expect("valid leaf-selection input");

    assert_eq!(
        eom.clusters
            .iter()
            .map(|cluster| cluster.members.clone())
            .collect::<Vec<_>>(),
        vec![vec![0, 1, 2, 3, 4, 5], vec![6, 7, 8]]
    );
    assert_eq!(
        leaf.clusters
            .iter()
            .map(|cluster| cluster.members.clone())
            .collect::<Vec<_>>(),
        vec![vec![0, 1, 2], vec![3, 4, 5], vec![6, 7, 8]]
    );

    let parent_stability = eom.clusters[0].stability;
    let descendant_stability = leaf.clusters[0].stability + leaf.clusters[1].stability;
    assert!(parent_stability > descendant_stability);
}

#[test]
fn equal_weight_splits_are_condensed_simultaneously() {
    let cosine = (3.0_f64 / 4.0).sqrt();
    let sine = 0.5;
    let vectors = vec![
        vec![cosine, sine, 0.0, 0.0, 0.0, 0.0],
        vec![cosine, -sine, 0.0, 0.0, 0.0, 0.0],
        vec![0.0, 0.0, cosine, sine, 0.0, 0.0],
        vec![0.0, 0.0, cosine, -sine, 0.0, 0.0],
        vec![0.0, 0.0, 0.0, 0.0, cosine, sine],
        vec![0.0, 0.0, 0.0, 0.0, cosine, -sine],
    ];
    let cosines = CosineMatrix::from_normalized_vectors(&vectors).expect("valid unit vectors");
    let result = hdbscan(
        &cosines,
        HdbscanConfig {
            min_samples: 1,
            min_cluster_size: 2,
            selection_method: ClusterSelectionMethod::Leaf,
        },
    )
    .expect("valid HDBSCAN input");

    let root_cluster_children = result
        .condensed_tree
        .iter()
        .filter(|edge| edge.parent == cosines.count() && edge.child >= cosines.count())
        .collect::<Vec<_>>();
    assert_eq!(
        root_cluster_children.len(),
        3,
        "removing the two equal-weight bridge edges simultaneously exposes three groups"
    );
    assert_eq!(
        result
            .clusters
            .iter()
            .map(|cluster| cluster.members.clone())
            .collect::<Vec<_>>(),
        vec![vec![0, 1], vec![2, 3], vec![4, 5]]
    );
}

#[test]
fn rejects_identical_vector_directions_for_upstream_deduplication() {
    let cosines =
        CosineMatrix::from_normalized_vectors(&[vec![1.0, 0.0], vec![1.0, 0.0], vec![0.0, 1.0]])
            .expect("valid unit vectors");
    let error = hdbscan(
        &cosines,
        HdbscanConfig {
            min_samples: 2,
            min_cluster_size: 2,
            selection_method: ClusterSelectionMethod::ExcessOfMass,
        },
    )
    .expect_err("identical embedding directions must be removed before HDBSCAN*");

    assert!(error.to_string().contains("identical vector directions"));
}

#[test]
fn rejects_parameters_that_do_not_define_core_distance_or_clusters() {
    let cosines = matrix(&[0.0, PI / 4.0, PI / 2.0]);

    let no_other_neighbor = hdbscan(
        &cosines,
        HdbscanConfig {
            min_samples: 4,
            min_cluster_size: 2,
            selection_method: ClusterSelectionMethod::ExcessOfMass,
        },
    )
    .expect_err("min_samples cannot exceed the complete three-vector neighborhood");
    assert!(no_other_neighbor.to_string().contains("min_samples"));

    let singleton_cluster = hdbscan(
        &cosines,
        HdbscanConfig {
            min_samples: 2,
            min_cluster_size: 1,
            selection_method: ClusterSelectionMethod::ExcessOfMass,
        },
    )
    .expect_err("HDBSCAN* clusters contain at least two vectors");
    assert!(singleton_cluster.to_string().contains("min_cluster_size"));
}

#[test]
fn membership_strength_is_partial_when_a_point_leaves_its_selected_cluster_early() {
    let cosines = matrix(&[0.0, 0.01, 0.02, 0.20, 1.0, 1.01, 1.02]);
    let result = hdbscan(
        &cosines,
        HdbscanConfig {
            min_samples: 2,
            min_cluster_size: 3,
            selection_method: ClusterSelectionMethod::ExcessOfMass,
        },
    )
    .expect("valid HDBSCAN input");

    assert_eq!(result.clusters[0].members, vec![0, 1, 2, 3]);
    assert_close(result.membership_strengths[3], 1.0 / 18.0);
    assert_eq!(result.membership_strengths[0..3], [1.0, 1.0, 1.0]);
}
