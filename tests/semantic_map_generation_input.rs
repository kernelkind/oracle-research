use std::collections::BTreeMap;
use std::fs;
use std::os::unix::fs::PermissionsExt;
use std::os::unix::fs::symlink;
use std::path::Path;
use std::thread;
use std::time::{Duration, Instant};

use nostrdb::{Config, Error as NdbError, Filter, Ndb, NoteBuilder, Transaction};
use oracle_mvp::english_filter::{
    CLASSIFICATION_POLICY, GLOTLID_V3_REPOSITORY_COMMIT, GLOTLID_V3_SHA256, NORMALIZATION_POLICY,
};
use oracle_mvp::semantic_map_sample::{
    SAMPLE_ROWS, SemanticMapGenerationInputConfig, SemanticMapSampleConfig,
    freeze_semantic_map_sample, materialize_semantic_map_generation_input,
};
use sha2::{Digest, Sha256};

#[test]
fn materializes_the_requested_frozen_prefix_without_mutating_the_source() {
    let root = tempfile::tempdir_in("/dev/shm").expect("tmpfs test directory");
    let source_path = root.path().join("source.ndb");
    let source = open_ndb(&source_path);
    let events = (0..SAMPLE_ROWS)
        .map(|index| {
            signed_test_event(
                &format!("Exact canonical content for semantic-map note {index}."),
                index as u64,
            )
        })
        .collect::<Vec<_>>();
    let mut content_by_id = BTreeMap::new();
    for event in &events {
        submit(&source, event);
        let value: serde_json::Value = serde_json::from_str(event).expect("event JSON");
        content_by_id.insert(
            value["id"].as_str().expect("event ID").to_owned(),
            value["content"].as_str().expect("event content").to_owned(),
        );
    }
    wait_for_count(&source, events.len());
    drop(source);

    let source_data = source_path.join("data.mdb");
    let source_lock = source_path.join("lock.mdb");
    let source_data_hash = sha256_file(&source_data);
    let source_lock_hash = sha256_file(&source_lock);
    let mut permissions = fs::metadata(&source_data)
        .expect("data metadata")
        .permissions();
    permissions.set_mode(0o444);
    fs::set_permissions(&source_data, permissions).expect("make source data read-only");

    let ordered_path = root.path().join("source-order.bin");
    let source_ids = events
        .iter()
        .map(|event| event_id(event))
        .collect::<Vec<_>>();
    write_ids(&ordered_path, &source_ids);
    let source_manifest_path = root.path().join("source-manifest.json");
    write_source_manifest(
        &source_manifest_path,
        &ordered_path,
        &source_data_hash,
        source_ids.len(),
    );
    let sample_path = root.path().join("sample");
    freeze_semantic_map_sample(&SemanticMapSampleConfig {
        source_corpus_path: source_path.clone(),
        source_ordered_event_ids_path: ordered_path,
        source_manifest_path,
        output_path: sample_path.clone(),
    })
    .expect("freeze sample");

    let output_path = root.path().join("generation-input");
    let config = SemanticMapGenerationInputConfig {
        source_corpus_path: source_path.clone(),
        sample_path: sample_path.clone(),
        rows: 3,
        excluded_note_ids: Vec::new(),
        output_path: output_path.clone(),
    };
    let manifest =
        materialize_semantic_map_generation_input(&config).expect("materialize generation input");

    assert_eq!(3, manifest.rows);
    let sample_ids = read_ids(&sample_path.join("ordered-event-ids.bin"));
    let input: serde_json::Value = serde_json::from_slice(
        &fs::read(output_path.join("notes.json")).expect("read notes input"),
    )
    .expect("decode notes input");
    let notes = input["notes"].as_array().expect("notes array");
    assert_eq!(3, notes.len());
    for (note, expected_id) in notes.iter().zip(&sample_ids[..3]) {
        let expected_hex = hex(expected_id);
        assert_eq!(Some(expected_hex.as_str()), note["note_id"].as_str());
        assert_eq!(
            content_by_id.get(&expected_hex).map(String::as_str),
            note["text"].as_str(),
        );
    }
    assert_eq!(source_data_hash, sha256_file(&source_data));
    assert_eq!(source_lock_hash, sha256_file(&source_lock));

    assert_eq!(
        manifest,
        materialize_semantic_map_generation_input(&config).expect("verify replay")
    );

    let excluded_output_path = root.path().join("generation-input-with-exclusions");
    let excluded_ids = vec![hex(&sample_ids[0]), hex(&sample_ids[2])];
    let excluded_config: SemanticMapGenerationInputConfig =
        serde_json::from_value(serde_json::json!({
            "source_corpus_path": source_path,
            "sample_path": sample_path,
            "rows": 3,
            "excluded_note_ids": excluded_ids,
            "output_path": excluded_output_path,
        }))
        .expect("generation input config accepts explicit exclusions");
    let excluded_manifest = materialize_semantic_map_generation_input(&excluded_config)
        .expect("materialize generation input with exclusions");
    let excluded_manifest_value =
        serde_json::to_value(&excluded_manifest).expect("encode exclusion manifest");
    assert_eq!(
        "first-retained-rows-after-explicit-event-id-exclusions-from-frozen-semantic-map-sample-v1",
        excluded_manifest_value["selection_rule"]
    );
    assert_eq!(
        serde_json::json!([hex(&sample_ids[0]), hex(&sample_ids[2])]),
        excluded_manifest_value["excluded_note_ids"]
    );
    assert_eq!(5, excluded_manifest_value["scanned_sample_rows"]);
    let excluded_input: serde_json::Value = serde_json::from_slice(
        &fs::read(excluded_output_path.join("notes.json")).expect("read excluded notes input"),
    )
    .expect("decode excluded notes input");
    assert_eq!(
        vec![
            hex(&sample_ids[1]),
            hex(&sample_ids[3]),
            hex(&sample_ids[4])
        ],
        excluded_input["notes"]
            .as_array()
            .expect("excluded notes array")
            .iter()
            .map(|note| note["note_id"].as_str().expect("note ID").to_owned())
            .collect::<Vec<_>>()
    );
    assert_eq!(
        excluded_manifest,
        materialize_semantic_map_generation_input(&excluded_config)
            .expect("verify exclusion replay")
    );

    let unused_exclusion_error =
        materialize_semantic_map_generation_input(&SemanticMapGenerationInputConfig {
            excluded_note_ids: vec![hex(&sample_ids[10])],
            output_path: root.path().join("generation-input-with-unused-exclusion"),
            ..excluded_config
        })
        .expect_err("an exclusion that does not affect the retained rows is invalid");
    assert!(
        unused_exclusion_error
            .to_string()
            .contains("was not encountered"),
        "{unused_exclusion_error}"
    );

    let alias_path = root.path().join("generation-input-alias");
    symlink(&output_path, &alias_path).expect("create output alias");
    let alias_error =
        materialize_semantic_map_generation_input(&SemanticMapGenerationInputConfig {
            output_path: alias_path,
            ..config.clone()
        })
        .expect_err("a symlink cannot stand in for a sealed output artifact");
    assert!(alias_error.to_string().contains("symlink"), "{alias_error}");

    let overlap_error =
        materialize_semantic_map_generation_input(&SemanticMapGenerationInputConfig {
            output_path: root.path().to_path_buf(),
            ..config
        })
        .expect_err("output cannot contain its source artifacts");
    assert!(
        overlap_error.to_string().contains("overlaps"),
        "{overlap_error}"
    );
}

fn open_ndb(path: &Path) -> Ndb {
    Ndb::new(
        path.to_str().expect("UTF-8 NostrDB path"),
        &Config::new()
            .set_flags((1 << 2) | (1 << 3) | (1 << 4))
            .set_mapsize(512 * 1_024 * 1_024)
            .set_ingester_threads(1),
    )
    .expect("open NostrDB")
}

fn submit(ndb: &Ndb, event: &str) {
    loop {
        match ndb.process_event(event) {
            Ok(()) => return,
            Err(NdbError::NoteProcessFailed) => thread::sleep(Duration::from_millis(10)),
            Err(error) => panic!("submit event: {error}"),
        }
    }
}

fn wait_for_count(ndb: &Ndb, expected: usize) {
    let deadline = Instant::now() + Duration::from_secs(20);
    loop {
        let transaction = Transaction::new(ndb).expect("transaction");
        let count = ndb
            .count(&transaction, &[Filter::new().build()])
            .expect("count events");
        if count == expected {
            return;
        }
        assert!(Instant::now() < deadline, "timed out waiting for notes");
        thread::sleep(Duration::from_millis(10));
    }
}

fn signed_test_event(content: &str, seed: u64) -> String {
    NoteBuilder::new()
        .kind(1)
        .content(content)
        .created_at(1_700_000_000 + seed)
        .sign(&[7_u8; 32])
        .build()
        .expect("sign test event")
        .json()
        .expect("serialize test event")
}

fn event_id(event: &str) -> [u8; 32] {
    let value: serde_json::Value = serde_json::from_str(event).expect("event JSON");
    let encoded = value["id"].as_str().expect("event ID").as_bytes();
    let mut id = [0_u8; 32];
    for (index, bytes) in encoded.chunks_exact(2).enumerate() {
        id[index] = decode_hex(bytes[0]) << 4 | decode_hex(bytes[1]);
    }
    id
}

fn decode_hex(value: u8) -> u8 {
    match value {
        b'0'..=b'9' => value - b'0',
        b'a'..=b'f' => value - b'a' + 10,
        _ => panic!("invalid hexadecimal event ID"),
    }
}

fn write_ids(path: &Path, ids: &[[u8; 32]]) {
    fs::write(path, ids.iter().flatten().copied().collect::<Vec<_>>()).expect("write ordered IDs");
}

fn read_ids(path: &Path) -> Vec<[u8; 32]> {
    let bytes = fs::read(path).expect("read ordered IDs");
    let mut records = bytes.chunks_exact(32);
    let ids = records
        .by_ref()
        .map(|record| record.try_into().expect("event ID width"))
        .collect();
    assert!(records.remainder().is_empty());
    ids
}

fn write_source_manifest(path: &Path, ordered_path: &Path, data_sha256: &str, rows: usize) {
    fs::write(
        path,
        serde_json::to_vec_pretty(&serde_json::json!({
            "schema_version": 2,
            "source_ordered_event_ids_sha256": "1".repeat(64),
            "source_ndb_data_sha256": data_sha256,
            "source_derivation_ledger_sha256": "2".repeat(64),
            "source_dedup_manifest_sha256": "3".repeat(64),
            "model_sha256": GLOTLID_V3_SHA256,
            "model_repository_commit": GLOTLID_V3_REPOSITORY_COMMIT,
            "normalization_policy": NORMALIZATION_POLICY,
            "classification_policy": CLASSIFICATION_POLICY,
            "input_events": rows,
            "retained_events": rows,
            "excluded_events": 0,
            "output_ordered_event_ids_sha256": sha256_file(ordered_path)
        }))
        .expect("encode source manifest"),
    )
    .expect("write source manifest");
}

fn sha256_file(path: &Path) -> String {
    let bytes = fs::read(path).expect("hash input");
    format!("{:x}", Sha256::digest(bytes))
}

fn hex(bytes: &[u8]) -> String {
    bytes.iter().map(|byte| format!("{byte:02x}")).collect()
}
