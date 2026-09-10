use std::collections::BTreeSet;
use std::fs;
use std::path::Path;

use oracle_mvp::hdbscan_hierarchy::Hierarchy;
use serde_json::{Value, json};

fn fixture() -> (Value, Value, Value) {
    let response = json!({"artifact": {"result": {
        "algorithm_result": {
            "vector_count": 8,
            "single_linkage_tree": [
                {"id":8,"left":0,"right":1,"size":2,"mutual_reachability_distance":0.1},
                {"id":9,"left":2,"right":8,"size":3,"mutual_reachability_distance":0.2},
                {"id":10,"left":3,"right":4,"size":2,"mutual_reachability_distance":0.2},
                {"id":11,"left":5,"right":10,"size":3,"mutual_reachability_distance":0.3},
                {"id":12,"left":9,"right":11,"size":6,"mutual_reachability_distance":0.4},
                {"id":13,"left":6,"right":12,"size":7,"mutual_reachability_distance":0.5},
                {"id":14,"left":7,"right":13,"size":8,"mutual_reachability_distance":0.6}
            ],
            "condensed_tree": "not used in the merge-tree comparison",
            "mutual_reachability_distances": "skip matrices without materializing them"
        },
        "canonical_unique_ids": ["v0","v1","v2","v3","v4","v5","v6","v7"],
        "alias_groups": [["v0"],["v1"],["v2","alias"],["v3"],["v4"],["v5"],["v6"],["v7"]]
    }}});
    let vectors = json!({"vectors": [
        {"vector_id":"v0","short_id":"V0","note_id":"a","byte_spans":[[0,5]],"fragments":["café"]},
        {"vector_id":"v1","short_id":"V1","note_id":"a","byte_spans":[[6,9],[10,13]],"fragments":["one","two"]},
        {"vector_id":"v2","short_id":"V2","note_id":"b","byte_spans":[[0,3]],"fragments":["tea"]},
        {"vector_id":"alias","short_id":"VA","note_id":"a","byte_spans":[[0,5]],"fragments":["café"]},
        {"vector_id":"v3","short_id":"V3","note_id":"a","byte_spans":[[6,9]],"fragments":["one"]},
        {"vector_id":"v4","short_id":"V4","note_id":"b","byte_spans":[[0,3]],"fragments":["tea"]},
        {"vector_id":"v5","short_id":"V5","note_id":"b","byte_spans":[[0,3]],"fragments":["tea"]},
        {"vector_id":"v6","short_id":"V6","note_id":"c","byte_spans":[[0,5]],"fragments":["stock"]},
        {"vector_id":"v7","short_id":"V7","note_id":"d","byte_spans":[[0,4]],"fragments":["last"]}
    ]});
    let notes = json!({"notes":[
        {"note_id":"a","text":"café one two"},
        {"note_id":"b","text":"tea"},
        {"note_id":"c","text":"stock"},
        {"note_id":"d","text":"last"}
    ]});
    (response, vectors, notes)
}

fn load_fixture(
    response: &Value,
    vectors: &Value,
    notes: &Value,
) -> Result<Hierarchy, Box<dyn std::error::Error>> {
    let directory = tempfile::tempdir()?;
    let paths = [
        directory.path().join("response.json"),
        directory.path().join("vectors.json"),
        directory.path().join("notes.json"),
    ];
    for (path, value) in paths.iter().zip([response, vectors, notes]) {
        fs::write(path, serde_json::to_vec(value)?)?;
    }
    let before = paths.iter().map(fs::read).collect::<Result<Vec<_>, _>>()?;
    let result = Hierarchy::load_note_navigation(&paths[0], &paths[1], &paths[2]);
    assert_eq!(
        before,
        paths.iter().map(fs::read).collect::<Result<Vec<_>, _>>()?
    );
    assert_eq!(fs::read_dir(directory.path())?.count(), 3);
    result
}

fn members(hierarchy: &Hierarchy, group: usize) -> BTreeSet<usize> {
    let mut result = BTreeSet::new();
    let mut pending = vec![group];
    while let Some(id) = pending.pop() {
        result.extend(&hierarchy.groups[&id].vectors);
        pending.extend(&hierarchy.groups[&id].children);
    }
    result
}

#[test]
fn six_member_raw_group_survives_without_stock_and_all_masks_remain_exact() {
    let (response, vectors, notes) = fixture();
    let hierarchy = load_fixture(&response, &vectors, &notes).unwrap();
    assert_eq!(hierarchy.root, 14);
    assert_eq!(
        hierarchy.groups.keys().copied().collect::<Vec<_>>(),
        [12, 13, 14]
    );
    assert_eq!(members(&hierarchy, 12), (0..6).collect());
    assert_eq!(members(&hierarchy, 13), (0..7).collect());
    assert_eq!(members(&hierarchy, 14), (0..8).collect());
    assert_eq!(hierarchy.groups[&12].parent, Some(13));
    assert_eq!(hierarchy.groups[&13].parent, Some(14));
    assert_eq!(hierarchy.groups[&14].children, [13]);
    assert_eq!(hierarchy.groups[&13].children, [12]);
    assert_eq!(hierarchy.groups[&13].vectors, [6]);
    assert_eq!(hierarchy.groups[&14].vectors, [7]);
    assert_eq!(
        (
            hierarchy.groups[&12].vector_count,
            hierarchy.groups[&12].note_count
        ),
        (6, 2)
    );
    assert_eq!(
        (
            hierarchy.groups[&13].vector_count,
            hierarchy.groups[&13].note_count
        ),
        (7, 3)
    );
    assert_eq!(
        (
            hierarchy.groups[&14].vector_count,
            hierarchy.groups[&14].note_count
        ),
        (8, 4)
    );
    assert!(hierarchy.groups.values().all(|group| group.note_count >= 2));
    assert!(
        hierarchy.groups.keys().all(|id| *id >= 8),
        "never turn alias-bearing points into group nodes"
    );
    assert_eq!(hierarchy.vectors.len(), 8);
    assert_eq!(hierarchy.vectors.values().map(Vec::len).sum::<usize>(), 9);
    for original in vectors["vectors"].as_array().unwrap() {
        let actual = hierarchy
            .vectors
            .values()
            .flatten()
            .find(|mask| mask.vector_id == original["vector_id"].as_str().unwrap())
            .unwrap();
        assert_eq!(actual.id, original["short_id"]);
        assert_eq!(actual.note_id, original["note_id"]);
        assert_eq!(
            serde_json::to_value(&actual.fragments).unwrap(),
            original["fragments"]
        );
        assert_eq!(
            serde_json::to_value(&actual.byte_spans).unwrap(),
            original["byte_spans"]
        );
        let source = notes["notes"]
            .as_array()
            .unwrap()
            .iter()
            .find(|note| note["note_id"] == original["note_id"])
            .unwrap();
        assert_eq!(actual.text, source["text"]);
    }
    assert_eq!(
        hierarchy.vectors[&2]
            .iter()
            .map(|mask| mask.vector_id.as_str())
            .collect::<Vec<_>>(),
        ["v2", "alias"]
    );
    let owners = hierarchy
        .groups
        .values()
        .flat_map(|group| group.vectors.iter().copied())
        .collect::<Vec<_>>();
    assert_eq!(owners.len(), 8);
    assert_eq!(
        owners.into_iter().collect::<BTreeSet<_>>(),
        (0..8).collect()
    );
}

#[test]
fn equal_note_set_child_is_removed_and_its_descendants_reach_the_upper_parent() {
    let (response, mut vectors, notes) = fixture();
    vectors["vectors"][8]["note_id"] = json!("c");
    vectors["vectors"][8]["byte_spans"] = json!([[0, 5]]);
    vectors["vectors"][8]["fragments"] = json!(["stock"]);
    let hierarchy = load_fixture(&response, &vectors, &notes).unwrap();
    assert_eq!(
        hierarchy.groups.keys().copied().collect::<Vec<_>>(),
        [12, 14]
    );
    assert_eq!(
        hierarchy.root, 14,
        "retain the upper raw parent, not its smaller child"
    );
    assert_eq!(hierarchy.groups[&12].parent, Some(14));
    assert_eq!(hierarchy.groups[&14].children, [12]);
    assert_eq!(hierarchy.groups[&14].vectors, [6, 7]);
    assert_eq!(members(&hierarchy, 12), (0..6).collect());
    assert_eq!(members(&hierarchy, 14), (0..8).collect());
}

#[test]
fn aliases_contribute_all_source_notes_but_never_create_point_only_groups() {
    let (mut response, vectors, notes) = fixture();
    let result = &mut response["artifact"]["result"];
    result["algorithm_result"]["vector_count"] = json!(3);
    result["algorithm_result"]["single_linkage_tree"] = json!([
        {"id":3,"left":0,"right":1,"size":2,"mutual_reachability_distance":0.1},
        {"id":4,"left":2,"right":3,"size":3,"mutual_reachability_distance":0.2}
    ]);
    result["canonical_unique_ids"] = json!(["v0", "v1", "v6"]);
    result["alias_groups"] = json!([["v0", "alias"], ["v1"], ["v6"]]);
    let mut vectors = json!({"vectors": [vectors["vectors"][0], vectors["vectors"][1], vectors["vectors"][3], vectors["vectors"][7]]});
    vectors["vectors"][2]["note_id"] = json!("b");
    vectors["vectors"][2]["byte_spans"] = json!([[0, 3]]);
    vectors["vectors"][2]["fragments"] = json!(["tea"]);
    let hierarchy = load_fixture(&response, &vectors, &notes).unwrap();
    assert_eq!(hierarchy.groups.keys().copied().collect::<Vec<_>>(), [3, 4]);
    assert_eq!(
        hierarchy.groups[&3].note_count, 2,
        "alias note b counts despite both representatives belonging to a"
    );
    assert_eq!(hierarchy.groups[&3].vectors, [0, 1]);
    assert_eq!(hierarchy.groups[&4].note_count, 3);
    assert_eq!(hierarchy.vectors[&0].len(), 2);
    assert!(!hierarchy.groups.contains_key(&0));
}

#[test]
fn one_note_corpus_keeps_only_a_root_container_without_losing_points() {
    let (response, mut vectors, notes) = fixture();
    for vector in vectors["vectors"].as_array_mut().unwrap() {
        vector["note_id"] = json!("a");
        vector["byte_spans"] = json!([[0, 5]]);
        vector["fragments"] = json!(["café"]);
    }
    let hierarchy = load_fixture(&response, &vectors, &notes).unwrap();
    assert_eq!(hierarchy.groups.keys().copied().collect::<Vec<_>>(), [14]);
    assert_eq!(hierarchy.groups[&14].note_count, 1);
    assert_eq!(hierarchy.groups[&14].vectors, (0..8).collect::<Vec<_>>());
    assert_eq!(hierarchy.vectors.values().map(Vec::len).sum::<usize>(), 9);
}

#[test]
fn equal_distance_parent_child_transitions_are_not_an_extra_pruning_rule() {
    let (mut response, vectors, notes) = fixture();
    response["artifact"]["result"]["algorithm_result"]["single_linkage_tree"][5]["mutual_reachability_distance"] =
        json!(0.6);
    let hierarchy = load_fixture(&response, &vectors, &notes).unwrap();
    assert_eq!(
        hierarchy.groups.keys().copied().collect::<Vec<_>>(),
        [12, 13, 14]
    );
    assert_eq!(hierarchy.groups[&13].parent, Some(14));
}

#[test]
fn rejects_incomplete_or_invalid_binary_merge_trees() {
    for case in [
        "missing row",
        "extra row",
        "wrong id",
        "future child",
        "repeated child",
        "multiple parents",
        "wrong size",
        "negative distance",
        "decreasing distance",
        "invalid distance",
        "zero points",
        "wrong alias count",
        "wrong canonical count",
    ] {
        let (mut response, vectors, notes) = fixture();
        let result = &mut response["artifact"]["result"];
        match case {
            "zero points" => result["algorithm_result"]["vector_count"] = json!(0),
            "wrong alias count" => {
                result["alias_groups"].as_array_mut().unwrap().pop();
            }
            "wrong canonical count" => {
                result["canonical_unique_ids"].as_array_mut().unwrap().pop();
            }
            _ => {
                let rows = result["algorithm_result"]["single_linkage_tree"]
                    .as_array_mut()
                    .unwrap();
                match case {
                    "missing row" => {
                        rows.pop();
                    }
                    "extra row" => rows.push(rows[6].clone()),
                    "wrong id" => rows[0]["id"] = json!(9),
                    "future child" => rows[0]["left"] = json!(14),
                    "repeated child" => rows[0]["right"] = json!(0),
                    "multiple parents" => rows[6]["right"] = json!(12),
                    "wrong size" => rows[0]["size"] = json!(3),
                    "negative distance" => rows[0]["mutual_reachability_distance"] = json!(-0.1),
                    "decreasing distance" => rows[4]["mutual_reachability_distance"] = json!(0.15),
                    "invalid distance" => rows[0]["mutual_reachability_distance"] = json!("NaN"),
                    _ => unreachable!(),
                }
            }
        }
        assert!(
            load_fixture(&response, &vectors, &notes).is_err(),
            "accepted {case}"
        );
    }
}

#[test]
fn source_mask_integrity_checks_are_shared_with_the_original_loader() {
    for case in [
        "fragment",
        "span",
        "duplicate alias",
        "canonical",
        "missing note",
        "unmapped vector",
    ] {
        let (mut response, mut vectors, mut notes) = fixture();
        match case {
            "fragment" => vectors["vectors"][0]["fragments"] = json!(["cafe"]),
            "span" => vectors["vectors"][0]["byte_spans"] = json!([[0, 4]]),
            "duplicate alias" => {
                response["artifact"]["result"]["alias_groups"][1] = json!(["v1", "v0"])
            }
            "canonical" => response["artifact"]["result"]["canonical_unique_ids"][0] = json!("v1"),
            "missing note" => {
                notes["notes"].as_array_mut().unwrap().pop();
            }
            "unmapped vector" => {
                let mut extra = vectors["vectors"][0].clone();
                extra["vector_id"] = json!("extra");
                extra["short_id"] = json!("VX");
                vectors["vectors"].as_array_mut().unwrap().push(extra);
            }
            _ => unreachable!(),
        }
        assert!(
            load_fixture(&response, &vectors, &notes).is_err(),
            "accepted {case}"
        );
    }
}

#[test]
fn saved_hdbv3_keeps_the_requested_raw_refinements_and_complete_memberships() {
    let root = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("sse_multivector/real-note-fine-segmentation-v1");
    let hierarchy = Hierarchy::load_note_navigation(
        &root.join("hdbv3-cross-note-edges-v1/response.json"),
        &root.join("vectors/vector-map.json"),
        &root.join("reviewed-input.json"),
    )
    .unwrap();
    assert_eq!(hierarchy.root, 1830);
    assert_eq!(hierarchy.groups.len(), 246);
    assert_eq!(hierarchy.groups[&1830].children.len(), 10);
    assert_eq!(
        (
            hierarchy.groups[&1830].vector_count,
            hierarchy.groups[&1830].note_count
        ),
        (916, 100)
    );
    let mut pending = vec![(hierarchy.root, 0)];
    let mut maximum_depth = 0;
    while let Some((id, depth)) = pending.pop() {
        maximum_depth = maximum_depth.max(depth);
        let group = &hierarchy.groups[&id];
        let points = members(&hierarchy, id);
        let notes = points
            .iter()
            .flat_map(|p| {
                hierarchy.vectors[p]
                    .iter()
                    .map(|mask| mask.note_id.as_str())
            })
            .collect::<BTreeSet<_>>();
        assert_eq!(group.vector_count, points.len());
        assert_eq!(group.note_count, notes.len());
        if let Some(parent) = group.parent {
            assert!(group.note_count >= 2);
            assert!(group.note_count < hierarchy.groups[&parent].note_count);
        }
        pending.extend(group.children.iter().map(|child| (*child, depth + 1)));
    }
    assert_eq!(maximum_depth, 54);
    let mask_ids = |group| {
        members(&hierarchy, group)
            .into_iter()
            .flat_map(|point| hierarchy.vectors[&point].iter().map(|mask| mask.id.clone()))
            .collect::<BTreeSet<_>>()
    };
    assert_eq!(
        mask_ids(1204),
        ["V113", "V114", "V115", "V672", "V673", "V674"]
            .into_iter()
            .map(str::to_owned)
            .collect()
    );
    assert_eq!(hierarchy.groups[&1204].parent, Some(1254));
    assert_eq!(
        (
            hierarchy.groups[&1254].vector_count,
            hierarchy.groups[&1254].note_count
        ),
        (7, 3)
    );
    assert!(mask_ids(1254).contains("V098"));
    let coffee = mask_ids(1090);
    assert!(coffee.contains("V494") && coffee.contains("V503"));
    assert_eq!(
        (
            hierarchy.groups[&1090].vector_count,
            hierarchy.groups[&1090].note_count
        ),
        (41, 19)
    );
    assert!(!members(&hierarchy, 1090).iter().any(|point| {
        hierarchy.vectors[point]
            .iter()
            .any(|mask| mask.id == "V733")
    }));
    for group in [1023, 1063] {
        assert_eq!(
            (
                hierarchy.groups[&group].vector_count,
                hierarchy.groups[&group].note_count
            ),
            (2, 2)
        );
    }
    let owners = hierarchy
        .groups
        .values()
        .flat_map(|group| group.vectors.iter().copied())
        .collect::<Vec<_>>();
    assert_eq!(owners.len(), 916);
    assert_eq!(
        owners.into_iter().collect::<BTreeSet<_>>(),
        (0..916).collect()
    );
}

#[test]
fn promoted_children_preserve_raw_left_to_right_traversal_order() {
    let (mut response, mut vectors, notes) = fixture();
    response["artifact"]["result"]["algorithm_result"]["single_linkage_tree"] = json!([
        {"id":8,"left":0,"right":1,"size":2,"mutual_reachability_distance":0.1},
        {"id":9,"left":2,"right":3,"size":2,"mutual_reachability_distance":0.2},
        {"id":10,"left":4,"right":5,"size":2,"mutual_reachability_distance":0.3},
        {"id":11,"left":6,"right":7,"size":2,"mutual_reachability_distance":0.4},
        {"id":12,"left":8,"right":9,"size":4,"mutual_reachability_distance":0.5},
        {"id":13,"left":11,"right":12,"size":6,"mutual_reachability_distance":0.6},
        {"id":14,"left":10,"right":13,"size":8,"mutual_reachability_distance":0.7}
    ]);
    let point_notes = ["a", "c", "b", "b", "a", "b", "a", "b"];
    for vector in vectors["vectors"].as_array_mut().unwrap() {
        let id = vector["vector_id"].as_str().unwrap();
        let point = if id == "alias" {
            2
        } else {
            id.strip_prefix('v').unwrap().parse::<usize>().unwrap()
        };
        let note = point_notes[point];
        let fragment = match note {
            "a" => "café",
            "b" => "tea",
            "c" => "stock",
            _ => unreachable!(),
        };
        vector["note_id"] = json!(note);
        vector["byte_spans"] = json!([[0, fragment.len()]]);
        vector["fragments"] = json!([fragment]);
    }
    let hierarchy = load_fixture(&response, &vectors, &notes).unwrap();
    // Raw root 14 visits left child 10 before right child 13. Removing 13
    // and its equal-note-set child 12 promotes 11, then 8, from that right
    // subtree. Sorting retained IDs would incorrectly put 8 before 10.
    assert_eq!(hierarchy.groups[&14].children, [10, 11, 8]);
}
