use std::fs;

use oracle_mvp::hdbscan_hierarchy::Hierarchy;
use serde_json::{Value, json};
use tempfile::tempdir;

fn fixture() -> (Value, Value, Value) {
    let response = json!({"artifact": {"result": {
        "algorithm_result": {
            "vector_count": 5,
            "condensed_tree": [
                {"parent":5,"child":0,"lambda":0.1,"child_size":1},
                {"parent":5,"child":6,"lambda":0.2,"child_size":3},
                {"parent":5,"child":7,"lambda":0.2,"child_size":1},
                {"parent":6,"child":1,"lambda":0.3,"child_size":1},
                {"parent":6,"child":8,"lambda":0.4,"child_size":2},
                {"parent":8,"child":2,"lambda":0.5,"child_size":1},
                {"parent":8,"child":3,"lambda":0.5,"child_size":1},
                {"parent":7,"child":4,"lambda":0.5,"child_size":1}
            ],
            "clusters": [{"id":8,"members":[2,3]}],
            "mutual_reachability_distances": "irrelevant: do not deserialize matrices"
        },
        "canonical_unique_ids": ["v0", "v1", "v2", "v3", "v4"],
        "alias_groups": [["v0"], ["v1"], ["v2", "alias"], ["v3"], ["v4"]]
    }}});
    let vectors = json!({"vectors": [
        {"vector_id":"v0","short_id":"V0","note_id":"a","byte_spans":[[0,5]],"fragments":["café"]},
        {"vector_id":"v1","short_id":"V1","note_id":"a","byte_spans":[[6,9],[10,13]],"fragments":["one","two"]},
        {"vector_id":"v2","short_id":"V2","note_id":"a","byte_spans":[[10,13]],"fragments":["two"]},
        {"vector_id":"alias","short_id":"VA","note_id":"b","byte_spans":[[0,5]],"fragments":["alias"]},
        {"vector_id":"v3","short_id":"V3","note_id":"a","byte_spans":[[0,5]],"fragments":["café"]},
        {"vector_id":"v4","short_id":"V4","note_id":"c","byte_spans":[[0,4]],"fragments":["solo"]}
    ]});
    let notes = json!({"notes": [
        {"note_id":"a","text":"café one two","subjects":"ignored"},
        {"note_id":"b","text":"alias"},
        {"note_id":"c","text":"solo"}
    ]});
    (response, vectors, notes)
}

fn load_fixture(
    response: &Value,
    vectors: &Value,
    notes: &Value,
) -> Result<Hierarchy, Box<dyn std::error::Error>> {
    let dir = tempdir()?;
    let response_path = dir.path().join("response.json");
    let vectors_path = dir.path().join("vector-map.json");
    let notes_path = dir.path().join("reviewed-input.json");
    for (path, value) in [
        (&response_path, response),
        (&vectors_path, vectors),
        (&notes_path, notes),
    ] {
        fs::write(path, serde_json::to_vec(value)?)?;
    }
    let before = [
        fs::read(&response_path)?,
        fs::read(&vectors_path)?,
        fs::read(&notes_path)?,
    ];
    let result = Hierarchy::load(&response_path, &vectors_path, &notes_path);
    assert_eq!(fs::read(&response_path)?, before[0]);
    assert_eq!(fs::read(&vectors_path)?, before[1]);
    assert_eq!(fs::read(&notes_path)?, before[2]);
    assert_eq!(fs::read_dir(dir.path())?.count(), 3);
    result
}

#[test]
fn reconstructs_saved_groups_without_flattening_or_filtering() {
    let (response, vectors, notes) = fixture();
    let hierarchy = load_fixture(&response, &vectors, &notes).expect("valid saved hierarchy");

    assert_eq!(hierarchy.root, 5);
    assert_eq!(
        hierarchy.groups.keys().copied().collect::<Vec<_>>(),
        [5, 6, 7, 8]
    );
    let root = &hierarchy.groups[&5];
    assert_eq!(root.parent, None);
    assert_eq!(root.children, [6, 7]);
    assert_eq!(root.vectors, [0]);
    assert_eq!((root.vector_count, root.note_count), (5, 3));
    let intermediate = &hierarchy.groups[&6];
    assert_eq!(intermediate.parent, Some(5));
    assert_eq!(intermediate.children, [8]);
    assert_eq!(intermediate.vectors, [1]);
    assert_eq!((intermediate.vector_count, intermediate.note_count), (3, 2));
    let leaf = &hierarchy.groups[&8];
    assert_eq!(leaf.parent, Some(6));
    assert!(leaf.children.is_empty());
    assert_eq!(leaf.vectors, [2, 3]);
    assert_eq!((leaf.vector_count, leaf.note_count), (2, 2));
    let single_note = &hierarchy.groups[&7];
    assert_eq!(single_note.vectors, [4]);
    assert_eq!((single_note.vector_count, single_note.note_count), (1, 1));
}

#[test]
fn preserves_every_alias_id_note_text_fragment_and_utf8_byte_span() {
    let (response, vectors, notes) = fixture();
    let hierarchy = load_fixture(&response, &vectors, &notes).expect("valid saved hierarchy");

    assert_eq!(hierarchy.vectors.len(), 5);
    assert_eq!(hierarchy.vectors.values().map(Vec::len).sum::<usize>(), 6);
    let aliases = &hierarchy.vectors[&2];
    assert_eq!(
        aliases
            .iter()
            .map(|item| item.id.as_str())
            .collect::<Vec<_>>(),
        ["V2", "VA"]
    );
    assert_eq!(
        aliases
            .iter()
            .map(|item| item.vector_id.as_str())
            .collect::<Vec<_>>(),
        ["v2", "alias"]
    );
    assert_eq!(
        aliases
            .iter()
            .map(|item| item.note_id.as_str())
            .collect::<Vec<_>>(),
        ["a", "b"]
    );
    assert_eq!(aliases[0].text, "café one two");
    assert_eq!(aliases[1].text, "alias");
    assert_eq!(hierarchy.vectors[&0][0].byte_spans, [(0, 5)]);
    assert_eq!(hierarchy.vectors[&0][0].fragments, ["café"]);
    assert_eq!(hierarchy.vectors[&1][0].byte_spans, [(6, 9), (10, 13)]);
    assert_eq!(hierarchy.vectors[&1][0].fragments, ["one", "two"]);
}

#[test]
fn rejects_invalid_utf8_ranges_and_fragments() {
    for (spans, fragments, expected) in [
        (json!([[0, 4]]), json!(["café"]), "byte span"),
        (json!([[0, 99]]), json!(["café"]), "byte span"),
        (json!([[5, 0]]), json!(["café"]), "byte span"),
        (json!([[0, 5]]), json!(["cafe"]), "fragment"),
        (json!([[0, 5]]), json!([]), "fragment"),
    ] {
        let (response, mut vectors, notes) = fixture();
        vectors["vectors"][0]["byte_spans"] = spans;
        vectors["vectors"][0]["fragments"] = fragments;
        let error = load_fixture(&response, &vectors, &notes).expect_err("invalid mask");
        assert!(error.to_string().contains(expected), "{error}");
    }
}

#[test]
fn rejects_overlapping_and_out_of_order_source_ranges() {
    for (spans, fragments) in [
        (json!([[0, 5], [0, 5]]), json!(["café", "café"])),
        (json!([[10, 13], [0, 5]]), json!(["two", "café"])),
    ] {
        let (response, mut vectors, notes) = fixture();
        vectors["vectors"][0]["fragments"] = fragments;
        vectors["vectors"][0]["byte_spans"] = spans;
        let error = load_fixture(&response, &vectors, &notes).expect_err("invalid source order");
        assert!(error.to_string().contains("byte span"), "{error}");
    }
}

#[test]
fn accepts_adjacent_source_order_ranges() {
    let (response, mut vectors, notes) = fixture();
    vectors["vectors"][0]["byte_spans"] = json!([[0, 3], [3, 5]]);
    vectors["vectors"][0]["fragments"] = json!(["caf", "é"]);
    let hierarchy = load_fixture(&response, &vectors, &notes).expect("adjacent valid UTF-8 spans");
    assert_eq!(hierarchy.vectors[&0][0].byte_spans, [(0, 3), (3, 5)]);
}

#[test]
fn requires_the_canonical_vector_to_be_the_first_alias() {
    let (mut response, vectors, notes) = fixture();
    response["artifact"]["result"]["alias_groups"][2] = json!(["alias", "v2"]);
    let error = load_fixture(&response, &vectors, &notes).expect_err("noncanonical alias order");
    assert!(error.to_string().contains("canonical"), "{error}");
}

#[test]
fn rejects_cycles_duplicate_parents_missing_points_and_incorrect_child_sizes() {
    for (case, expected) in [
        ("cycle", "cycle"),
        ("duplicate parent", "parent"),
        ("missing point", "point"),
        ("incorrect child size", "child_size"),
        ("point parent", "parent"),
        ("root parent", "root"),
    ] {
        let (mut response, vectors, notes) = fixture();
        let edges = response["artifact"]["result"]["algorithm_result"]["condensed_tree"]
            .as_array_mut()
            .unwrap();
        match case {
            "cycle" => edges[1]["parent"] = json!(8),
            "duplicate parent" => {
                edges.push(json!({"parent":7,"child":2,"lambda":0.5,"child_size":1}))
            }
            "missing point" => {
                edges.remove(0);
            }
            "incorrect child size" => edges[1]["child_size"] = json!(2),
            "point parent" => edges[0]["parent"] = json!(4),
            "root parent" => edges.push(json!({"parent":8,"child":5,"lambda":0.5,"child_size":5})),
            _ => unreachable!(),
        }
        let error = load_fixture(&response, &vectors, &notes).expect_err(case);
        assert!(error.to_string().contains(expected), "{case}: {error}");
    }
}

#[test]
fn rejects_missing_or_ambiguous_original_vector_and_note_mappings() {
    for (case, expected) in [
        ("missing vector", "missing vector"),
        ("unmapped vector", "unmapped vector"),
        ("duplicate vector", "duplicate vector"),
        ("duplicate short id", "duplicate short_id"),
        ("duplicate note", "duplicate note"),
        ("missing note", "missing note"),
        ("duplicate alias", "alias"),
        ("missing aliases", "alias"),
        ("wrong canonical id", "canonical"),
    ] {
        let (mut response, mut vectors, mut notes) = fixture();
        match case {
            "missing vector" => {
                vectors["vectors"].as_array_mut().unwrap().remove(0);
            }
            "unmapped vector" => {
                let mut extra = vectors["vectors"][0].clone();
                extra["vector_id"] = json!("extra");
                extra["short_id"] = json!("VX");
                vectors["vectors"].as_array_mut().unwrap().push(extra);
            }
            "duplicate vector" => {
                let duplicate = vectors["vectors"][0].clone();
                vectors["vectors"].as_array_mut().unwrap().push(duplicate);
            }
            "duplicate short id" => vectors["vectors"][1]["short_id"] = json!("V0"),
            "duplicate note" => {
                let duplicate = notes["notes"][0].clone();
                notes["notes"].as_array_mut().unwrap().push(duplicate);
            }
            "missing note" => {
                notes["notes"].as_array_mut().unwrap().remove(0);
            }
            "duplicate alias" => {
                response["artifact"]["result"]["alias_groups"][1] = json!(["v1", "v0"])
            }
            "missing aliases" => response["artifact"]["result"]["alias_groups"][0] = json!([]),
            "wrong canonical id" => {
                response["artifact"]["result"]["canonical_unique_ids"][0] = json!("v4")
            }
            _ => unreachable!(),
        }
        let error = load_fixture(&response, &vectors, &notes).expect_err(case);
        assert!(error.to_string().contains(expected), "{case}: {error}");
    }
}
