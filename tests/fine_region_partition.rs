use oracle_mvp::fine_region_partition::{
    CosineMatrix, complete_linkage_partition, dp_vmf_partition, resolution_levels,
};

fn unit_vector(degrees: f64) -> Vec<f64> {
    let radians = degrees.to_radians();
    vec![radians.cos(), radians.sin()]
}

#[test]
fn complete_linkage_does_not_join_distant_endpoints_through_a_chain() {
    let vectors = vec![
        unit_vector(0.0),
        unit_vector(6.0),
        unit_vector(14.0),
        unit_vector(180.0),
    ];
    let cosines = CosineMatrix::from_normalized_vectors(&vectors).expect("valid unit vectors");

    let partition = complete_linkage_partition(&cosines, 10.0_f64.to_radians().cos())
        .expect("complete-link partition");

    assert_eq!(partition.regions(), &[vec![0, 1], vec![2], vec![3]]);
    assert!(
        partition
            .regions()
            .iter()
            .all(|region| cosines.minimum_within(region).unwrap_or(1.0)
                >= 10.0_f64.to_radians().cos())
    );
}

#[test]
fn complete_linkage_does_not_admit_a_pair_just_below_its_threshold() {
    let threshold = 0.5_f64;
    let vectors = vec![
        unit_vector(0.0),
        unit_vector((threshold - 5.0e-13).acos().to_degrees()),
    ];
    let cosines = CosineMatrix::from_normalized_vectors(&vectors).expect("valid unit vectors");

    let partition = complete_linkage_partition(&cosines, threshold).expect("strict cut");

    assert_eq!(partition.regions(), &[vec![0], vec![1]]);
}

#[test]
fn resolution_levels_ignore_same_note_nearest_neighbors() {
    let vectors = vec![
        unit_vector(0.0),
        unit_vector(0.0),
        unit_vector(60.0),
        unit_vector(120.0),
    ];
    let note_ids = vec![
        "a".to_owned(),
        "a".to_owned(),
        "b".to_owned(),
        "c".to_owned(),
    ];
    let cosines = CosineMatrix::from_normalized_vectors(&vectors).expect("valid unit vectors");

    let levels = resolution_levels(&cosines, &note_ids, &[50]).expect("one resolution level");

    assert_eq!(levels.len(), 1);
    assert!((levels[0].pairwise_min_cosine - 0.5).abs() < 1.0e-12);
    assert!(
        (levels[0].centroid_min_cosine - 0.5).abs() < 1.0e-12,
        "DP-vMF must sweep its native centroid threshold on the observed cosine scale"
    );
    assert!((levels[0].centroid_max_angle_degrees - 60.0).abs() < 1.0e-12);
}

#[test]
fn accepted_norm_roundoff_cannot_change_directional_similarity() {
    let vectors = vec![vec![1.0, 0.0], vec![0.999_995, 0.0]];
    let cosines = CosineMatrix::from_normalized_vectors(&vectors).expect("accepted roundoff");

    assert_eq!(cosines.get(0, 1).expect("cosine"), 1.0);
    let partition = dp_vmf_partition(&vectors, 0.999_999, &[0, 1])
        .expect("directional partition ignores magnitude roundoff");
    assert_eq!(partition.regions(), &[vec![0, 1]]);
}

#[test]
fn dp_vmf_opens_singletons_instead_of_forcing_distant_vectors_together() {
    let vectors = vec![
        unit_vector(0.0),
        unit_vector(8.0),
        unit_vector(100.0),
        unit_vector(108.0),
        unit_vector(220.0),
    ];
    let threshold = 12.0_f64.to_radians().cos();

    let partition =
        dp_vmf_partition(&vectors, threshold, &[0, 1, 2, 3, 4]).expect("DP-vMF partition");

    assert_eq!(partition.regions(), &[vec![0, 1], vec![2, 3], vec![4]]);
    assert!(partition.regions().iter().all(|region| !region.is_empty()));
}

#[test]
fn dp_vmf_partition_is_canonical_across_equivalent_orders() {
    let vectors = vec![
        unit_vector(0.0),
        unit_vector(5.0),
        unit_vector(90.0),
        unit_vector(95.0),
    ];
    let threshold = 10.0_f64.to_radians().cos();

    let forward = dp_vmf_partition(&vectors, threshold, &[0, 1, 2, 3]).expect("forward partition");
    let reverse = dp_vmf_partition(&vectors, threshold, &[3, 2, 1, 0]).expect("reverse partition");

    assert_eq!(forward, reverse);
    assert_eq!(forward.regions(), &[vec![0, 1], vec![2, 3]]);
}

#[test]
fn dp_vmf_does_not_admit_a_vector_just_below_its_threshold() {
    let threshold = 0.5_f64;
    let vectors = vec![
        unit_vector(0.0),
        unit_vector((threshold - 5.0e-13).acos().to_degrees()),
    ];

    let partition = dp_vmf_partition(&vectors, threshold, &[0, 1]).expect("strict threshold");

    assert_eq!(partition.regions(), &[vec![0], vec![1]]);
}

#[test]
fn dp_vmf_exposes_real_order_dependence() {
    let vectors = vec![unit_vector(0.0), unit_vector(20.0), unit_vector(40.0)];

    let forward = dp_vmf_partition(&vectors, 0.9, &[0, 1, 2]).expect("forward partition");
    let reverse = dp_vmf_partition(&vectors, 0.9, &[2, 1, 0]).expect("reverse partition");

    assert_eq!(forward.regions(), &[vec![0, 1], vec![2]]);
    assert_eq!(reverse.regions(), &[vec![0], vec![1, 2]]);
}

#[test]
fn dp_vmf_rejects_a_numerically_directionless_centroid() {
    let vectors = vec![unit_vector(0.0), unit_vector(180.0 - 1.0e-12)];

    let error = dp_vmf_partition(&vectors, -1.0, &[0, 1])
        .expect_err("a nearly cancelling centroid has no stable direction");

    assert!(error.to_string().contains("centroid"), "{error}");
}

#[test]
fn every_dp_vmf_member_meets_the_final_centroid_threshold() {
    let vectors = vec![
        unit_vector(0.0),
        unit_vector(20.0),
        unit_vector(45.0),
        unit_vector(100.0),
        unit_vector(125.0),
        unit_vector(240.0),
    ];
    let threshold = 0.9;
    let partition = dp_vmf_partition(&vectors, threshold, &[0, 1, 2, 3, 4, 5])
        .expect("converged DP-vMF partition");

    for region in partition.regions() {
        let mut centroid = vec![0.0; vectors[0].len()];
        for ordinal in region {
            for (sum, coordinate) in centroid.iter_mut().zip(&vectors[*ordinal]) {
                *sum += coordinate;
            }
        }
        let norm = centroid
            .iter()
            .map(|value| value * value)
            .sum::<f64>()
            .sqrt();
        for coordinate in &mut centroid {
            *coordinate /= norm;
        }
        for ordinal in region {
            let cosine = vectors[*ordinal]
                .iter()
                .zip(&centroid)
                .map(|(left, right)| left * right)
                .sum::<f64>();
            assert!(cosine >= threshold, "member {ordinal}: {cosine}");
        }
    }
}
