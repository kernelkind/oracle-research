use oracle_mvp::fine_region_hierarchy::{FineSegment, HierarchyNode, average_linkage_hierarchy};
use oracle_mvp::fine_region_partition::CosineMatrix;

fn unit_vector(degrees: f64) -> Vec<f64> {
    let radians = degrees.to_radians();
    vec![radians.cos(), radians.sin()]
}

fn segment(id: &str, members: &[usize]) -> FineSegment {
    FineSegment {
        segment_id: id.to_owned(),
        members: members.to_vec(),
    }
}

#[test]
fn average_linkage_weights_each_fine_segment_equally_and_preserves_every_merge() {
    let vectors = vec![
        unit_vector(0.0),
        unit_vector(0.0),
        unit_vector(5.0),
        unit_vector(15.0),
        unit_vector(60.0),
    ];
    let cosines = CosineMatrix::from_normalized_vectors(&vectors).expect("valid unit vectors");
    let segments = vec![
        segment("A", &[0, 1]),
        segment("B", &[2]),
        segment("C", &[3]),
        segment("D", &[4]),
    ];

    let hierarchy = average_linkage_hierarchy(&vectors, &segments).expect("valid hierarchy");

    assert_eq!(hierarchy.fine_segments, segments);
    assert_eq!(hierarchy.merges.len(), 3);
    assert_eq!(
        hierarchy.merges[0].children,
        [
            HierarchyNode::FineSegment("A".to_owned()),
            HierarchyNode::FineSegment("B".to_owned()),
        ]
    );
    assert_eq!(hierarchy.merges[0].fine_segment_count, 2);
    assert_eq!(hierarchy.merges[1].fine_segment_count, 3);
    assert_eq!(hierarchy.merges[2].fine_segment_count, 4);
    assert_eq!(hierarchy.root, HierarchyNode::Merge(2));

    let a_d = (cosines.get(0, 4).unwrap() + cosines.get(1, 4).unwrap()) / 2.0;
    let b_d = cosines.get(2, 4).unwrap();
    let c_d = cosines.get(3, 4).unwrap();
    let expected_root = (a_d + b_d + c_d) / 3.0;
    assert!((hierarchy.merges[2].similarity - expected_root).abs() < 1.0e-12);

    assert!(
        hierarchy
            .merges
            .windows(2)
            .all(|pair| pair[0].similarity >= pair[1].similarity)
    );
}

#[test]
fn average_linkage_is_stable_across_input_order_and_exact_ties() {
    let vectors = vec![
        unit_vector(0.0),
        unit_vector(90.0),
        unit_vector(180.0),
        unit_vector(270.0),
    ];
    let canonical = vec![
        segment("A", &[0]),
        segment("B", &[1]),
        segment("C", &[2]),
        segment("D", &[3]),
    ];
    let permuted = vec![
        segment("D", &[3]),
        segment("B", &[1]),
        segment("A", &[0]),
        segment("C", &[2]),
    ];

    let expected = average_linkage_hierarchy(&vectors, &canonical).expect("canonical hierarchy");
    let actual = average_linkage_hierarchy(&vectors, &permuted).expect("permuted hierarchy");

    assert_eq!(actual, expected);
    assert_eq!(
        actual.merges[0].children,
        [
            HierarchyNode::FineSegment("A".to_owned()),
            HierarchyNode::FineSegment("B".to_owned()),
        ]
    );
}

#[test]
fn average_linkage_rejects_invalid_fine_segment_partitions() {
    let vectors = vec![unit_vector(0.0), unit_vector(30.0), unit_vector(60.0)];
    for (name, segments, expected) in [
        (
            "empty segment",
            vec![segment("A", &[0]), segment("B", &[]), segment("C", &[1, 2])],
            "empty",
        ),
        (
            "overlap",
            vec![segment("A", &[0, 1]), segment("B", &[1, 2])],
            "exactly once",
        ),
        (
            "missing vector",
            vec![segment("A", &[0]), segment("B", &[2])],
            "exactly once",
        ),
        (
            "out of range",
            vec![segment("A", &[0, 1]), segment("B", &[2, 3])],
            "out of bounds",
        ),
    ] {
        let error = average_linkage_hierarchy(&vectors, &segments).expect_err(name);
        assert!(error.to_string().contains(expected), "{name}: {error}");
    }
}
