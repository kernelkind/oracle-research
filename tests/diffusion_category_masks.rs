use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::path::Path;

use oracle_mvp::manual_note_hierarchy::ManualNoteHierarchy;
use serde_json::Value;

const RUN: &str = "sse_multivector/geometric-hierarchy-v1/GDC09";
const SOURCE: &str = "sse_multivector/real-note-fine-segmentation-v1/reviewed-input.json";

fn read(path: impl AsRef<Path>) -> Value {
    serde_json::from_slice(&fs::read(path).unwrap()).unwrap()
}

fn spans(value: &Value) -> Vec<(usize, usize)> {
    value
        .as_array()
        .unwrap()
        .iter()
        .map(|span| {
            assert_eq!(span.as_array().unwrap().len(), 2);
            (
                usize::try_from(span[0].as_u64().unwrap()).unwrap(),
                usize::try_from(span[1].as_u64().unwrap()).unwrap(),
            )
        })
        .collect()
}

fn covered_bytes(spans: &[(usize, usize)]) -> BTreeSet<usize> {
    spans.iter().flat_map(|&(start, end)| start..end).collect()
}

#[test]
fn every_category_note_highlights_exactly_all_original_member_masks() {
    let (hierarchy, masks) = ManualNoteHierarchy::load_with_masks(
        &Path::new(RUN).join("categories.json"),
        Path::new(SOURCE),
    )
    .unwrap();
    let masks = masks.expect("saved diffusion categories must include original note masks");
    assert_eq!(hierarchy.nodes.len(), 219);
    assert_eq!(hierarchy.notes.len(), 100);

    let native = read(Path::new(RUN).join("hierarchy.json"));
    let native: BTreeMap<_, _> = native["nodes"]
        .as_array()
        .unwrap()
        .iter()
        .map(|node| (node["id"].as_u64().unwrap().to_string(), node))
        .collect();
    let evidence = read(Path::new(RUN).join("evidence.json"));
    let evidence = evidence.as_array().unwrap();
    assert_eq!(evidence.len(), 916);
    let source = read(SOURCE);
    let originals: BTreeMap<_, _> = source["notes"]
        .as_array()
        .unwrap()
        .iter()
        .map(|note| (note["note_id"].as_str().unwrap(), note))
        .collect();
    assert_eq!(originals.len(), 100);

    // Validate byte positions against original notes without locating fragments
    // by string search: repeated fragments must keep their saved occurrence.
    let mut vector_ids = BTreeSet::new();
    for (row, record) in evidence.iter().enumerate() {
        assert_eq!(record["row"].as_u64().unwrap(), row as u64);
        let aliases = record["aliases"].as_array().unwrap();
        assert!(!aliases.is_empty());
        for alias in aliases {
            assert!(vector_ids.insert(alias["vector_id"].as_str().unwrap()));
            let short = alias["note_short_id"].as_str().unwrap();
            let note_id = alias["note_id"].as_str().unwrap();
            let original = originals[note_id];
            let text = original["text"].as_str().unwrap();
            assert_eq!(hierarchy.notes[short].note_id, note_id);
            assert_eq!(hierarchy.notes[short].content, text);
            assert_eq!(alias["text"].as_str().unwrap(), text);
            let positions = spans(&alias["byte_spans"]);
            assert!(!positions.is_empty());
            let fragments = alias["fragments"].as_array().unwrap();
            assert_eq!(positions.len(), fragments.len());
            for (&(start, end), fragment) in positions.iter().zip(fragments) {
                assert!(start < end && end <= text.len());
                assert!(text.is_char_boundary(start) && text.is_char_boundary(end));
                assert_eq!(&text[start..end], fragment.as_str().unwrap());
            }
            assert!(
                original["subjects"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .any(|subject| {
                        subject["judgment"] == "accepted"
                            && subject["byte_spans"] == alias["byte_spans"]
                    })
            );
        }
    }
    assert_eq!(vector_ids.len(), 945);

    let mut saw_descendant_notes = false;
    let mut saw_other_branch_bytes = false;
    for (category, node) in &hierarchy.nodes {
        let mut expected = BTreeMap::<String, BTreeSet<usize>>::new();
        // Native members include every descendant, collapsed group, and
        // hidden one-note group, but exclude rows from other branches.
        for row in native[category]["members"].as_array().unwrap() {
            let row = usize::try_from(row.as_u64().unwrap()).unwrap();
            for alias in evidence[row]["aliases"].as_array().unwrap() {
                expected
                    .entry(alias["note_short_id"].as_str().unwrap().to_owned())
                    .or_default()
                    .extend(covered_bytes(&spans(&alias["byte_spans"])));
            }
        }
        let note_ids = hierarchy.note_ids(category);
        assert_eq!(expected.keys().cloned().collect::<Vec<_>>(), note_ids);
        saw_descendant_notes |= note_ids.iter().any(|note| !node.note_ids.contains(note));
        for note in note_ids {
            let actual = masks.spans(category, &note);
            assert!(actual.windows(2).all(|pair| pair[0].1 < pair[1].0));
            // Compare individual covered bytes, independently of the
            // production range-merging algorithm.
            assert_eq!(
                covered_bytes(actual),
                expected[&note],
                "incorrect original mask union for {category}/{note}"
            );
            let all_note_bytes = covered_bytes(masks.spans(&hierarchy.root_node_id, &note));
            saw_other_branch_bytes |= !all_note_bytes.is_subset(&expected[&note]);
        }
    }
    assert!(
        saw_descendant_notes,
        "fixture must exercise descendant notes"
    );
    assert!(
        saw_other_branch_bytes,
        "fixture must exercise same-note masks excluded from narrower categories"
    );
}
