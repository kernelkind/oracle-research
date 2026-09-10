use std::fs;
use std::path::PathBuf;
use std::process::{Command, Output};

use oracle_mvp::hdbscan_hierarchy::Hierarchy;
use serde_json::{Value, json};

fn fixture() -> (Value, Value, Value) {
    let history = json!({
        "vector_count": 4,
        "canonical_unique_ids": ["v0", "v1", "v2", "v3"],
        "alias_groups": [["v0"], ["v1", "alias"], ["v2"], ["v3"]],
        "merges": [
            {"id":4,"left":0,"right":1,"size":2,"merge_score":0.8,"unsupported_left":0,"unsupported_right":0},
            {"id":5,"left":2,"right":4,"size":3,"merge_score":0.2,"unsupported_left":0,"unsupported_right":1},
            {"id":6,"left":3,"right":5,"size":4,"merge_score":0.7,"unsupported_left":0,"unsupported_right":0}
        ]
    });
    let vectors = json!({"vectors": [
        {"vector_id":"v0","short_id":"V0","note_id":"a","byte_spans":[[0,5]],"fragments":["café"]},
        {"vector_id":"v1","short_id":"V1","note_id":"a","byte_spans":[[6,9]],"fragments":["one"]},
        {"vector_id":"alias","short_id":"VA","note_id":"b","byte_spans":[[0,3]],"fragments":["tea"]},
        {"vector_id":"v2","short_id":"V2","note_id":"a","byte_spans":[[10,13]],"fragments":["two"]},
        {"vector_id":"v3","short_id":"V3","note_id":"c","byte_spans":[[0,5]],"fragments":["stock"]}
    ]});
    let notes = json!({"notes": [
        {"note_id":"a","text":"café one two"},
        {"note_id":"b","text":"tea"},
        {"note_id":"c","text":"stock"}
    ]});
    (history, vectors, notes)
}

fn saved_fixture(values: &(Value, Value, Value)) -> (tempfile::TempDir, [PathBuf; 3]) {
    let directory = tempfile::tempdir().unwrap();
    let paths = [
        directory.path().join("history.json"),
        directory.path().join("vectors.json"),
        directory.path().join("notes.json"),
    ];
    for (path, value) in paths.iter().zip([&values.0, &values.1, &values.2]) {
        fs::write(path, serde_json::to_vec(value).unwrap()).unwrap();
    }
    (directory, paths)
}

fn run_cli(paths: &[PathBuf; 3], options: &[&str]) -> Output {
    Command::new(env!("CARGO_BIN_EXE_hdbscan-hierarchy"))
        .args(paths)
        .args(options)
        .output()
        .unwrap()
}

#[test]
fn merge_history_cli_accepts_real_score_inversions_without_changing_sources() {
    let (directory, paths) = saved_fixture(&fixture());
    let before = paths
        .iter()
        .map(fs::read)
        .collect::<Result<Vec<_>, _>>()
        .unwrap();
    let output = run_cli(&paths, &["--merge-history", "--start-at", "5", "--check"]);
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let text = String::from_utf8_lossy(&output.stdout);
    for expected in [
        "Merge-tree note navigation",
        "2 groups",
        "4 unique vectors",
        "5 original IDs",
        "3 notes",
        "Starting branch 5",
    ] {
        assert!(text.contains(expected), "Missing {expected}: {text}");
    }
    assert_eq!(
        before,
        paths
            .iter()
            .map(fs::read)
            .collect::<Result<Vec<_>, _>>()
            .unwrap()
    );
    assert_eq!(fs::read_dir(directory.path()).unwrap().count(), 3);
}

#[test]
fn score_inversions_preserve_the_note_projection_aliases_and_exact_masks() {
    let values = fixture();
    let (_directory, paths) = saved_fixture(&values);
    let hierarchy = Hierarchy::load_merge_history(&paths[0], &paths[1], &paths[2]).unwrap();
    assert_eq!(hierarchy.root, 6);
    assert_eq!(hierarchy.groups.keys().copied().collect::<Vec<_>>(), [5, 6]);
    assert_eq!(hierarchy.groups[&5].parent, Some(6));
    assert_eq!(hierarchy.groups[&6].children, [5]);
    assert_eq!(hierarchy.groups[&5].vectors, [0, 1, 2]);
    assert_eq!(hierarchy.groups[&6].vectors, [3]);
    assert_eq!(hierarchy.groups[&5].vector_count, 3);
    assert_eq!(
        hierarchy.groups[&5].note_count, 2,
        "the alias supplies the second note"
    );
    assert_eq!(hierarchy.groups[&6].vector_count, 4);
    assert_eq!(hierarchy.groups[&6].note_count, 3);
    assert_eq!(hierarchy.vectors.len(), 4);
    assert_eq!(hierarchy.vectors.values().map(Vec::len).sum::<usize>(), 5);
    for original in values.1["vectors"].as_array().unwrap() {
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
        let source = values.2["notes"]
            .as_array()
            .unwrap()
            .iter()
            .find(|note| note["note_id"] == original["note_id"])
            .unwrap();
        assert_eq!(actual.text, source["text"]);
    }
}

#[test]
fn hdbscan_still_rejects_decreasing_distances_and_shares_the_same_projection() {
    let (history, vectors, notes) = fixture();
    let mut rows = history["merges"].clone();
    for row in rows.as_array_mut().unwrap() {
        row["mutual_reachability_distance"] =
            row.as_object_mut().unwrap().remove("merge_score").unwrap();
    }
    let response = json!({"artifact": {"result": {
        "alias_groups": history["alias_groups"],
        "canonical_unique_ids": history["canonical_unique_ids"],
        "algorithm_result": {"vector_count": 4, "single_linkage_tree": rows}
    }}});
    let (mut response, vectors, notes) = (response, vectors, notes);
    let (_directory, paths) = saved_fixture(&(response.clone(), vectors.clone(), notes.clone()));
    let error = Hierarchy::load_note_navigation(&paths[0], &paths[1], &paths[2]).unwrap_err();
    assert!(
        error
            .to_string()
            .contains("distances must be finite, nonnegative, and ordered")
    );
    for (index, row) in response["artifact"]["result"]["algorithm_result"]["single_linkage_tree"]
        .as_array_mut()
        .unwrap()
        .iter_mut()
        .enumerate()
    {
        row["mutual_reachability_distance"] = json!((index + 1) as f64 / 10.0);
    }
    let (_ordered_directory, ordered_paths) = saved_fixture(&(response, vectors, notes));
    let ordered =
        Hierarchy::load_note_navigation(&ordered_paths[0], &ordered_paths[1], &ordered_paths[2])
            .unwrap();
    let (_generic_directory, generic_paths) = saved_fixture(&fixture());
    let generic =
        Hierarchy::load_merge_history(&generic_paths[0], &generic_paths[1], &generic_paths[2])
            .unwrap();
    assert_eq!(ordered.root, generic.root);
    assert_eq!(
        ordered.groups.keys().collect::<Vec<_>>(),
        generic.groups.keys().collect::<Vec<_>>()
    );
    for (id, group) in &ordered.groups {
        let other = &generic.groups[id];
        assert_eq!(
            (
                group.parent,
                &group.children,
                &group.vectors,
                group.note_count,
                group.vector_count
            ),
            (
                other.parent,
                &other.children,
                &other.vectors,
                other.note_count,
                other.vector_count
            )
        );
    }
}

#[test]
fn merge_history_rejects_invalid_structure_scores_and_source_masks() {
    for case in [
        "missing row",
        "extra row",
        "wrong id",
        "future child",
        "repeated child",
        "multiple parents",
        "wrong size",
        "zero points",
        "wrong alias count",
        "wrong canonical count",
        "negative score",
        "null score",
        "nonnumeric score",
        "missing score",
        "wrong score field",
        "wrong fragment",
        "invalid byte span",
        "unmapped alias",
    ] {
        let (mut history, mut vectors, notes) = fixture();
        match case {
            "missing row" => {
                history["merges"].as_array_mut().unwrap().pop();
            }
            "extra row" => {
                let row = history["merges"][2].clone();
                history["merges"].as_array_mut().unwrap().push(row);
            }
            "wrong id" => history["merges"][0]["id"] = json!(5),
            "future child" => history["merges"][0]["left"] = json!(6),
            "repeated child" => history["merges"][0]["right"] = json!(0),
            "multiple parents" => history["merges"][2]["left"] = json!(0),
            "wrong size" => history["merges"][1]["size"] = json!(2),
            "zero points" => history["vector_count"] = json!(0),
            "wrong alias count" => {
                history["alias_groups"].as_array_mut().unwrap().pop();
            }
            "wrong canonical count" => {
                history["canonical_unique_ids"]
                    .as_array_mut()
                    .unwrap()
                    .pop();
            }
            "negative score" => history["merges"][0]["merge_score"] = json!(-0.1),
            "null score" => history["merges"][0]["merge_score"] = Value::Null,
            "nonnumeric score" => history["merges"][0]["merge_score"] = json!("NaN"),
            "missing score" | "wrong score field" => {
                history["merges"][0]
                    .as_object_mut()
                    .unwrap()
                    .remove("merge_score");
                if case == "wrong score field" {
                    history["merges"][0]["mutual_reachability_distance"] = json!(0.8);
                }
            }
            "wrong fragment" => vectors["vectors"][0]["fragments"] = json!(["cafe"]),
            "invalid byte span" => vectors["vectors"][0]["byte_spans"] = json!([[0, 4]]),
            "unmapped alias" => history["alias_groups"][1][1] = json!("missing"),
            _ => unreachable!(),
        }
        let (_directory, paths) = saved_fixture(&(history, vectors, notes));
        assert!(
            Hierarchy::load_merge_history(&paths[0], &paths[1], &paths[2]).is_err(),
            "accepted {case}"
        );
    }
}

#[test]
fn merge_history_cli_rejects_conflicting_modes_and_collapsed_starting_groups() {
    let (_directory, paths) = saved_fixture(&fixture());
    for options in [
        vec!["--merge-history", "--note-navigation", "--check"],
        vec!["--note-navigation", "--merge-history", "--check"],
        vec!["--merge-history", "--selection", "unused.json", "--check"],
        vec!["--selection", "unused.json", "--merge-history", "--check"],
    ] {
        let output = run_cli(&paths, &options);
        assert!(!output.status.success());
        assert!(String::from_utf8_lossy(&output.stderr).contains("cannot combine"));
    }
    let repeated = run_cli(&paths, &["--merge-history", "--merge-history", "--check"]);
    assert!(!repeated.status.success());
    assert!(String::from_utf8_lossy(&repeated.stderr).contains("unknown or repeated option"));
    let collapsed = run_cli(&paths, &["--merge-history", "--start-at", "4", "--check"]);
    assert!(!collapsed.status.success());
    assert!(String::from_utf8_lossy(&collapsed.stderr).contains("unknown group 4"));
    let default = run_cli(&paths, &["--merge-history", "--check"]);
    assert!(default.status.success());
    assert!(String::from_utf8_lossy(&default.stdout).contains("Starting branch 6"));
    let help = run_cli(&paths, &["--help"]);
    assert!(help.status.success());
    assert!(String::from_utf8_lossy(&help.stdout).contains("--merge-history"));
}
