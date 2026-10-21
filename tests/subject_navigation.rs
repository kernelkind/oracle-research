use std::fs::File;
use std::io::BufReader;
use std::path::{Path, PathBuf};

use oracle_mvp::reference_map::ApprovedHierarchy;
use oracle_mvp::subject_navigation::{NavigationHierarchy};

fn project_path(path: &str) -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR")).join(path)
}

#[test]
fn approved_reference_hierarchy_converts_without_losing_leaf_order() {
    let path = project_path("tests/fixtures/reference-map/crec-116-approved-hierarchy-v1.json");
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
