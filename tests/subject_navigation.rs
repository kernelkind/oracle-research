use std::fs::{self, File};
use std::io::BufReader;
use std::path::{Path, PathBuf};

use oracle_mvp::reference_map::ApprovedHierarchy;
use oracle_mvp::sse_subject_navigation::load_sse_subject_hierarchy;
use oracle_mvp::subject_navigation::{NavigationHierarchy, SubjectNavigation};
use sha2::{Digest, Sha256};

fn project_path(path: &str) -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR")).join(path)
}

fn manual_hierarchy() -> NavigationHierarchy {
    load_sse_subject_hierarchy(
        project_path("sse_multivector/manual-subject-hierarchy-v1/hierarchy.json"),
        project_path("sse_multivector/fine-region-hierarchy-result-v2/analysis.json"),
        project_path("sse_multivector/fine-region-partition-result-v1/analysis.json"),
    )
    .expect("load the source-bound manual hierarchy")
}

#[test]
fn manual_hierarchy_resolves_every_selected_fine_segment_and_note_edge() {
    let hierarchy = manual_hierarchy();

    assert_eq!(hierarchy.notes.len(), 36);
    assert_eq!(
        hierarchy
            .nodes
            .iter()
            .filter(|node| node.children.is_empty())
            .count(),
        22
    );
    assert_eq!(
        hierarchy
            .nodes
            .iter()
            .map(|node| node.note_ids.len())
            .sum::<usize>(),
        48
    );
    assert_eq!(
        hierarchy
            .node("root")
            .expect("hidden root")
            .children
            .iter()
            .map(String::as_str)
            .collect::<Vec<_>>(),
        [
            "food-and-drink",
            "solar-energy",
            "equipment",
            "digital-sovereignty",
            "integrity-under-pressure",
            "book-recommendations-reviews",
            "gradual-realization",
            "nature-plant-life",
        ]
    );
    assert_eq!(
        hierarchy.node("home-bitcoin-mining").unwrap().label,
        "Home Bitcoin mining"
    );
    assert_eq!(
        hierarchy.node("equipment-supply-chores").unwrap().label,
        "Equipment chores"
    );
    assert_eq!(
        hierarchy.node("openness-without-imposition").unwrap().label,
        "Open technology choice"
    );
    assert_eq!(
        hierarchy.node("programmable-money-control").unwrap().label,
        "Monetary sovereignty"
    );
    assert_eq!(
        hierarchy.node("integrity-under-pressure").unwrap().label,
        "Integrity under pressure to conform"
    );
    assert_eq!(hierarchy.node("nature-plant-life").unwrap().label, "Nature");
}

#[test]
fn manual_hierarchy_navigates_from_a_broad_subject_to_grounded_notes() {
    let hierarchy = manual_hierarchy();
    let mut navigation = SubjectNavigation::new(&hierarchy).expect("open hierarchy");

    navigation.move_next(&hierarchy);
    navigation.move_next(&hierarchy);
    navigation.enter(&hierarchy).expect("enter equipment");
    assert_eq!(navigation.current_node_id(), "equipment");

    navigation.enter(&hierarchy).expect("enter Bitcoin mining");
    assert_eq!(navigation.current_node_id(), "bitcoin-mining");

    navigation
        .enter(&hierarchy)
        .expect("enter home Bitcoin mining");
    assert_eq!(navigation.current_node_id(), "home-bitcoin-mining");
    assert!(
        navigation
            .selected_note(&hierarchy)
            .expect("resolve selected note")
            .expect("leaf contains a note")
            .content
            .contains("miner")
    );

    navigation.back();
    assert_eq!(navigation.current_node_id(), "bitcoin-mining");
    navigation.back();
    assert_eq!(navigation.current_node_id(), "equipment");
}

#[test]
fn approved_reference_hierarchy_converts_without_losing_leaf_order() {
    let path = project_path("reference_map/crec-116-approved-hierarchy-v1.json");
    let approved: ApprovedHierarchy =
        serde_json::from_reader(BufReader::new(File::open(path).expect("open hierarchy")))
            .expect("decode hierarchy");
    approved.validate().expect("validate approved hierarchy");

    let navigation = NavigationHierarchy::try_from(&approved).expect("convert hierarchy");
    assert_eq!(navigation.notes.len(), approved.notes.len());
    assert_eq!(navigation.root_node_id, approved.root_node_id);

    for leaf in approved
        .nodes
        .iter()
        .filter(|node| node.children.is_empty())
    {
        let expected = approved
            .leaf_notes(&leaf.node_id)
            .expect("resolve approved leaf")
            .into_iter()
            .map(|note| note.note_id.as_str())
            .collect::<Vec<_>>();
        let actual = navigation
            .node(&leaf.node_id)
            .expect("converted leaf")
            .note_ids
            .iter()
            .map(String::as_str)
            .collect::<Vec<_>>();
        assert_eq!(actual, expected, "leaf {} changed order", leaf.node_id);
    }
}

#[test]
fn manual_hierarchy_rejects_a_partition_not_bound_by_its_hierarchy_analysis() {
    let temporary = tempfile::tempdir().expect("create temporary directory");
    let source_spec = project_path("sse_multivector/manual-subject-hierarchy-v1/hierarchy.json");
    let source_hierarchy =
        project_path("sse_multivector/fine-region-hierarchy-result-v2/analysis.json");
    let source_partition =
        project_path("sse_multivector/fine-region-partition-result-v1/analysis.json");

    let mut hierarchy: serde_json::Value = serde_json::from_reader(BufReader::new(
        File::open(&source_hierarchy).expect("open hierarchy analysis"),
    ))
    .expect("decode hierarchy analysis");
    hierarchy["partition_analysis_sha256"] = serde_json::Value::String("0".repeat(64));
    let hierarchy_bytes = serde_json::to_vec(&hierarchy).expect("encode hierarchy analysis");
    let hierarchy_path = temporary.path().join("hierarchy-analysis.json");
    fs::write(&hierarchy_path, &hierarchy_bytes).expect("write hierarchy analysis");

    let mut spec: serde_json::Value = serde_json::from_reader(BufReader::new(
        File::open(source_spec).expect("open manual hierarchy"),
    ))
    .expect("decode manual hierarchy");
    spec["inputs"]["fine_region_hierarchy_analysis_sha256"] =
        serde_json::Value::String(format!("{:x}", Sha256::digest(&hierarchy_bytes)));
    let spec_path = temporary.path().join("manual-hierarchy.json");
    fs::write(
        &spec_path,
        serde_json::to_vec(&spec).expect("encode manual hierarchy"),
    )
    .expect("write manual hierarchy");

    let error = load_sse_subject_hierarchy(spec_path, hierarchy_path, source_partition)
        .expect_err("hierarchy analysis must bind its partition analysis");
    assert!(
        error.to_string().contains("embedded partition SHA-256"),
        "{error}"
    );
}
