use oracle_mvp::fine_region_partition::CosineMatrix;
use oracle_mvp::fine_region_snn::{SnnConfig, SnnPointRole, snn_segmentation};

fn unit_vector(degrees: f64) -> Vec<f64> {
    let radians = degrees.to_radians();
    vec![radians.cos(), radians.sin()]
}

fn example_vectors() -> Vec<Vec<f64>> {
    [0.0, 1.0, 2.2, 3.7, 5.8, 90.0]
        .into_iter()
        .map(unit_vector)
        .collect()
}

fn example_config() -> SnnConfig {
    SnnConfig {
        neighbor_count: 3,
        minimum_shared_neighbor_count: 1,
        minimum_core_neighbor_count: 2,
    }
}

#[test]
fn snn_uses_reciprocal_neighbors_and_raw_shared_neighbor_count() {
    let cosines = CosineMatrix::from_normalized_vectors(&example_vectors()).expect("cosine matrix");

    let result = snn_segmentation(&cosines, &example_config()).expect("SNN segmentation");

    assert_eq!(
        result.points[0]
            .nearest_neighbors
            .iter()
            .map(|neighbor| neighbor.ordinal)
            .collect::<Vec<_>>(),
        vec![1, 2, 3]
    );
    assert!(
        (result.points[0].nearest_neighbors[0].angular_distance_radians - 1.0_f64.to_radians())
            .abs()
            < 1.0e-12
    );

    let link = result
        .links
        .iter()
        .find(|link| (link.left, link.right) == (0, 2))
        .expect("reciprocal link 0-2");
    assert_eq!(link.shared_neighbors, vec![1, 3]);
    assert_eq!(link.shared_neighbor_count, 2);
    assert!(link.qualifies);

    assert!(
        result
            .links
            .iter()
            .all(|link| (link.left, link.right) != (2, 4)),
        "2 and 4 share neighbors, but 4 is not in 2's k-nearest-neighbor list"
    );
}

#[test]
fn snn_builds_core_components_attaches_borders_and_leaves_noise_unassigned() {
    let cosines = CosineMatrix::from_normalized_vectors(&example_vectors()).expect("cosine matrix");

    let result = snn_segmentation(&cosines, &example_config()).expect("SNN segmentation");

    assert_eq!(result.segments.len(), 1);
    assert_eq!(result.segments[0].members, vec![0, 1, 2, 3, 4]);
    assert_eq!(result.segments[0].core_members, vec![0, 1, 2, 3]);
    assert_eq!(result.segments[0].border_members, vec![4]);
    assert_eq!(result.noise, vec![5]);
    assert_eq!(result.points[4].density, 1);
    assert_eq!(result.points[4].role, SnnPointRole::Border);
    assert_eq!(result.points[4].border_core_ordinal, Some(3));
    assert_eq!(result.points[4].segment_index, Some(0));
    assert_eq!(result.points[5].density, 0);
    assert_eq!(result.points[5].role, SnnPointRole::Noise);
    assert_eq!(result.points[5].border_core_ordinal, None);
    assert_eq!(result.points[5].segment_index, None);
}

#[test]
fn a_border_uses_smallest_angle_to_break_a_shared_count_tie_without_joining_cores() {
    let vectors = vec![
        vec![0.977_980_309_028, -0.121_252_154_742, -0.169_860_030_978],
        vec![0.982_765_923_376, 0.140_885_635_651, 0.119_676_135_959],
        vec![0.423_762_922_950, -0.697_624_563_673, -0.577_706_632_550],
        vec![-0.471_016_559_434, 0.866_887_656_395, -0.163_245_802_180],
        vec![-0.500_753_495_391, 0.328_592_378_819, 0.800_795_220_662],
        vec![-0.508_324_643_145, 0.662_662_605_545, -0.549_985_752_892],
        vec![0.494_592_302_297, 0.848_843_930_671, -0.186_661_286_482],
    ];
    let cosines = CosineMatrix::from_normalized_vectors(&vectors).expect("cosine matrix");
    let config = SnnConfig {
        neighbor_count: 4,
        minimum_shared_neighbor_count: 2,
        minimum_core_neighbor_count: 3,
    };

    let result = snn_segmentation(&cosines, &config).expect("SNN segmentation");

    assert_eq!(result.segments.len(), 2);
    assert_eq!(result.segments[0].core_members, vec![0]);
    assert_eq!(result.segments[1].core_members, vec![3]);
    let border = &result.points[6];
    assert_eq!(border.role, SnnPointRole::Border);
    assert_eq!(border.border_core_ordinal, Some(3));
    assert_eq!(border.segment_index, result.points[3].segment_index);
    assert_ne!(border.segment_index, result.points[0].segment_index);

    let left_link = result
        .links
        .iter()
        .find(|link| (link.left, link.right) == (0, 6))
        .expect("left core link");
    let right_link = result
        .links
        .iter()
        .find(|link| (link.left, link.right) == (3, 6))
        .expect("right core link");
    assert_eq!(left_link.shared_neighbor_count, 2);
    assert_eq!(right_link.shared_neighbor_count, 2);
    assert!(right_link.angular_distance_radians < left_link.angular_distance_radians);
}

#[test]
fn shared_neighbor_and_core_density_thresholds_are_inclusive() {
    let cosines = CosineMatrix::from_normalized_vectors(&example_vectors()).expect("cosine matrix");
    let config = SnnConfig {
        neighbor_count: 3,
        minimum_shared_neighbor_count: 2,
        minimum_core_neighbor_count: 2,
    };

    let result = snn_segmentation(&cosines, &config).expect("SNN segmentation");

    let exact_link = result
        .links
        .iter()
        .find(|link| (link.left, link.right) == (0, 1))
        .expect("link exactly at the shared-neighbor threshold");
    assert_eq!(exact_link.shared_neighbor_count, 2);
    assert!(exact_link.qualifies);
    assert_eq!(result.points[0].density, 2);
    assert_eq!(result.points[0].role, SnnPointRole::Core);
    assert_eq!(result.points[3].density, 1);
    assert_eq!(result.points[3].role, SnnPointRole::Noise);
}

#[test]
fn exact_angular_distance_ties_use_the_lower_ordinal_first() {
    let vectors = vec![
        vec![1.0, 0.0],
        vec![0.0, 1.0],
        vec![0.0, -1.0],
        vec![-1.0, 0.0],
    ];
    let cosines = CosineMatrix::from_normalized_vectors(&vectors).expect("cosine matrix");
    let config = SnnConfig {
        neighbor_count: 2,
        minimum_shared_neighbor_count: 1,
        minimum_core_neighbor_count: 1,
    };

    let result = snn_segmentation(&cosines, &config).expect("SNN segmentation");

    assert_eq!(
        result.points[0]
            .nearest_neighbors
            .iter()
            .map(|neighbor| neighbor.ordinal)
            .collect::<Vec<_>>(),
        vec![1, 2]
    );
}

#[test]
fn snn_rejects_invalid_configs() {
    let vectors = [0.0, 1.0, 2.0, 3.0]
        .into_iter()
        .map(unit_vector)
        .collect::<Vec<_>>();
    let cosines = CosineMatrix::from_normalized_vectors(&vectors).expect("cosine matrix");

    for (name, config, expected) in [
        (
            "too few neighbors",
            SnnConfig {
                neighbor_count: 1,
                ..example_config()
            },
            "at least 2",
        ),
        (
            "too many neighbors",
            SnnConfig {
                neighbor_count: 4,
                ..example_config()
            },
            "smaller than the vector count",
        ),
        (
            "zero shared neighbors",
            SnnConfig {
                minimum_shared_neighbor_count: 0,
                ..example_config()
            },
            "positive",
        ),
        (
            "impossible shared neighbors",
            SnnConfig {
                minimum_shared_neighbor_count: 3,
                ..example_config()
            },
            "at most k - 1",
        ),
        (
            "zero core density",
            SnnConfig {
                minimum_core_neighbor_count: 0,
                ..example_config()
            },
            "positive",
        ),
        (
            "impossible core density",
            SnnConfig {
                minimum_core_neighbor_count: 4,
                ..example_config()
            },
            "at most k",
        ),
    ] {
        let error = snn_segmentation(&cosines, &config).expect_err(name);
        assert!(error.to_string().contains(expected), "{name}: {error}");
    }
}
