use oracle_mvp::fine_region_hierarchy::{FineSegment, HierarchyNode};
use oracle_mvp::fine_region_scc::{scc_hierarchy, scc_hierarchy_over_selected_segments};

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
fn scc_merges_a_nearest_neighbor_component_as_one_nonbinary_parent() {
    let vectors = vec![
        vec![1.0, 0.0, 0.0],
        vec![
            std::f64::consts::FRAC_1_SQRT_2,
            std::f64::consts::FRAC_1_SQRT_2,
            0.0,
        ],
        vec![0.0, 1.0, 0.0],
        vec![0.0, 0.0, 1.0],
    ];
    let segments = vec![
        segment("A", &[0]),
        segment("B", &[1]),
        segment("C", &[2]),
        segment("D", &[3]),
    ];

    let hierarchy =
        scc_hierarchy_over_selected_segments(&vectors, &segments, &[0.70]).expect("SCC hierarchy");

    assert_eq!(hierarchy.rounds.len(), 1);
    assert_eq!(hierarchy.merges.len(), 1);
    assert_eq!(
        hierarchy.merges[0].children,
        vec![
            HierarchyNode::FineSegment("A".to_owned()),
            HierarchyNode::FineSegment("B".to_owned()),
            HierarchyNode::FineSegment("C".to_owned()),
        ]
    );
    assert_eq!(hierarchy.merges[0].fine_segment_count, 3);
    assert_eq!(hierarchy.merges[0].nearest_neighbor_edges.len(), 2);
    assert_eq!(
        (
            &hierarchy.merges[0].nearest_neighbor_edges[0].left,
            &hierarchy.merges[0].nearest_neighbor_edges[0].right,
        ),
        (
            &HierarchyNode::FineSegment("A".to_owned()),
            &HierarchyNode::FineSegment("B".to_owned()),
        )
    );
    assert!(hierarchy.merges[0].nearest_neighbor_edges[0].left_selected_right);
    assert!(hierarchy.merges[0].nearest_neighbor_edges[0].right_selected_left);
    assert_eq!(
        (
            &hierarchy.merges[0].nearest_neighbor_edges[1].left,
            &hierarchy.merges[0].nearest_neighbor_edges[1].right,
        ),
        (
            &HierarchyNode::FineSegment("B".to_owned()),
            &HierarchyNode::FineSegment("C".to_owned()),
        )
    );
    assert!(!hierarchy.merges[0].nearest_neighbor_edges[1].left_selected_right);
    assert!(hierarchy.merges[0].nearest_neighbor_edges[1].right_selected_left);
    assert_eq!(
        hierarchy.roots,
        vec![
            HierarchyNode::Merge(0),
            HierarchyNode::FineSegment("D".to_owned()),
        ]
    );
}

#[test]
fn scc_repeats_one_threshold_until_no_further_merge_is_possible() {
    let vectors = vec![
        unit_vector(0.0),
        unit_vector(1.0),
        unit_vector(10.0),
        unit_vector(11.0),
    ];
    let segments = vec![
        segment("A", &[0]),
        segment("B", &[1]),
        segment("C", &[2]),
        segment("D", &[3]),
    ];

    let hierarchy =
        scc_hierarchy_over_selected_segments(&vectors, &segments, &[0.98]).expect("SCC hierarchy");

    assert_eq!(hierarchy.rounds.len(), 2);
    assert_eq!(hierarchy.rounds[0].threshold_index, 0);
    assert_eq!(hierarchy.rounds[1].threshold_index, 0);
    assert_eq!(hierarchy.rounds[0].merge_indices, vec![0, 1]);
    assert_eq!(hierarchy.rounds[1].merge_indices, vec![2]);
    assert_eq!(
        hierarchy.merges[2].children,
        vec![HierarchyNode::Merge(0), HierarchyNode::Merge(1)]
    );
    assert_eq!(hierarchy.roots, vec![HierarchyNode::Merge(2)]);
}

#[test]
fn scc_finishes_every_successful_pass_before_relaxing_to_the_next_threshold() {
    let vectors = vec![
        unit_vector(0.0),
        unit_vector(1.0),
        unit_vector(10.0),
        unit_vector(11.0),
        unit_vector(90.0),
    ];
    let segments = vec![
        segment("A", &[0]),
        segment("B", &[1]),
        segment("C", &[2]),
        segment("D", &[3]),
        segment("E", &[4]),
    ];

    let hierarchy = scc_hierarchy_over_selected_segments(&vectors, &segments, &[0.98, 0.0])
        .expect("SCC hierarchy");

    assert_eq!(
        hierarchy
            .rounds
            .iter()
            .map(|round| round.threshold_index)
            .collect::<Vec<_>>(),
        vec![0, 0, 1]
    );
    assert_eq!(hierarchy.roots, vec![HierarchyNode::Merge(3)]);
}

#[test]
fn scc_records_the_one_way_nearest_neighbor_edge_that_connects_a_chain() {
    let vectors = vec![unit_vector(0.0), unit_vector(10.0), unit_vector(30.0)];
    let segments = vec![segment("A", &[0]), segment("B", &[1]), segment("C", &[2])];

    let hierarchy =
        scc_hierarchy_over_selected_segments(&vectors, &segments, &[0.90]).expect("SCC hierarchy");

    let edges = &hierarchy.merges[0].nearest_neighbor_edges;
    assert_eq!(edges.len(), 2);
    assert!(edges[0].left_selected_right);
    assert!(edges[0].right_selected_left);
    assert_eq!(
        (&edges[1].left, &edges[1].right),
        (
            &HierarchyNode::FineSegment("B".to_owned()),
            &HierarchyNode::FineSegment("C".to_owned()),
        )
    );
    assert!(!edges[1].left_selected_right);
    assert!(edges[1].right_selected_left);
}

#[test]
fn scc_relaxes_the_threshold_only_after_the_current_threshold_stabilizes() {
    let vectors = vec![unit_vector(0.0), unit_vector(5.0), unit_vector(30.0)];
    let segments = vec![segment("A", &[0]), segment("B", &[1]), segment("C", &[2])];

    let hierarchy = scc_hierarchy_over_selected_segments(&vectors, &segments, &[0.99, 0.88])
        .expect("SCC hierarchy");

    assert_eq!(hierarchy.rounds.len(), 2);
    assert_eq!(hierarchy.rounds[0].threshold_index, 0);
    assert_eq!(hierarchy.rounds[0].minimum_similarity, 0.99);
    assert_eq!(hierarchy.rounds[1].threshold_index, 1);
    assert_eq!(hierarchy.rounds[1].minimum_similarity, 0.88);
    assert_eq!(hierarchy.roots, vec![HierarchyNode::Merge(1)]);
}

#[test]
fn scc_average_linkage_weights_each_fine_segment_equally() {
    let mut vectors = vec![unit_vector(0.0); 10];
    vectors.extend([unit_vector(40.0), unit_vector(100.0), unit_vector(100.0)]);
    let segments = vec![
        segment("A", &(0..10).collect::<Vec<_>>()),
        segment("B", &[10]),
        segment("C", &[11]),
        segment("D", &[12]),
    ];

    let hierarchy = scc_hierarchy_over_selected_segments(&vectors, &segments, &[0.99, 0.70, 0.0])
        .expect("SCC hierarchy");

    assert_eq!(
        hierarchy
            .rounds
            .iter()
            .map(|round| round.threshold_index)
            .collect::<Vec<_>>(),
        vec![0, 1, 2]
    );
    assert_eq!(
        hierarchy.merges[2].children,
        vec![HierarchyNode::Merge(1), HierarchyNode::Merge(0)]
    );
    assert_eq!(hierarchy.roots, vec![HierarchyNode::Merge(2)]);
}

#[test]
fn scc_is_stable_across_input_order_and_breaks_exact_nearest_ties_canonically() {
    let vectors = vec![
        vec![1.0, 0.0],
        vec![0.0, 1.0],
        vec![-1.0, 0.0],
        vec![0.0, -1.0],
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

    let expected =
        scc_hierarchy_over_selected_segments(&vectors, &canonical, &[-0.01]).expect("canonical");
    let actual =
        scc_hierarchy_over_selected_segments(&vectors, &permuted, &[-0.01]).expect("permuted");

    assert_eq!(actual, expected);
    assert_eq!(actual.merges.len(), 1);
    assert_eq!(actual.merges[0].children.len(), 4);
    assert_eq!(actual.merges[0].nearest_neighbor_edges.len(), 3);
}

#[test]
fn scc_uses_inclusive_minimum_similarity_thresholds() {
    let vectors = vec![unit_vector(0.0), unit_vector(60.0)];
    let segments = vec![segment("A", &[0]), segment("B", &[1])];
    let exact_similarity = vectors[0][0] * vectors[1][0] + vectors[0][1] * vectors[1][1];

    let hierarchy = scc_hierarchy_over_selected_segments(&vectors, &segments, &[exact_similarity])
        .expect("inclusive threshold");

    assert_eq!(hierarchy.merges.len(), 1);
}

#[test]
fn scc_rejects_invalid_threshold_schedules() {
    let vectors = vec![unit_vector(0.0), unit_vector(30.0)];
    let segments = vec![segment("A", &[0]), segment("B", &[1])];
    for (name, schedule, expected) in [
        ("empty", vec![], "empty"),
        ("duplicate", vec![0.9, 0.9], "strictly decreasing"),
        ("increasing", vec![0.8, 0.9], "strictly decreasing"),
        ("non-finite", vec![f64::NAN], "finite"),
        ("out of range", vec![1.1], "between -1 and 1"),
    ] {
        let error =
            scc_hierarchy_over_selected_segments(&vectors, &segments, &schedule).expect_err(name);
        assert!(error.to_string().contains(expected), "{name}: {error}");
    }
}

#[test]
fn complete_scc_requires_every_vector_while_selected_scc_does_not() {
    let vectors = vec![unit_vector(0.0), unit_vector(30.0), unit_vector(60.0)];
    let segments = vec![segment("A", &[0]), segment("B", &[2])];

    let error = scc_hierarchy(&vectors, &segments, &[0.0]).expect_err("incomplete partition");
    assert!(error.to_string().contains("every vector"), "{error}");
    scc_hierarchy_over_selected_segments(&vectors, &segments, &[0.0])
        .expect("selected fine segments");
}
