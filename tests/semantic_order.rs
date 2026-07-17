use std::fs;
use std::path::Path;
use std::thread;
use std::time::{Duration, Instant};

use nostrdb::{Config, Error as NdbError, Filter, Ndb, NoteBuilder, Transaction};
use oracle_mvp::semantic_order::{
    SEMANTIC_ORDER_SELECTION_RULE, SemanticOrderManifest, derive_semantic_order,
};
use sha2::{Digest, Sha256};

#[test]
fn atomically_derives_the_semantic_order_from_raw_trimmed_content() {
    let temp = tempfile::tempdir().expect("temporary directory");
    let source_ndb = temp.path().join("english-eligible.ndb");
    let source = open_ndb(&source_ndb);
    let events = [
        signed_test_event("retained first", 1),
        signed_test_event(" \n\t", 2),
        signed_test_event("https://example.com", 3),
        signed_test_event("\u{2003}\u{a0}", 4),
        signed_test_event("retained last ", 5),
    ];
    for event in &events {
        submit(&source, event);
    }
    wait_for_count(&source, events.len());
    drop(source);

    let ids = events
        .iter()
        .map(|event| event_id(event))
        .collect::<Vec<_>>();
    let source_order = [ids[3], ids[0], ids[2], ids[1], ids[4]];
    let source_order_path = temp.path().join("source-order.bin");
    write_ids(&source_order_path, &source_order);

    let output = temp.path().join("semantic-corpus");
    let manifest =
        derive_semantic_order(&source_ndb, &source_order_path, &output).expect("semantic order");

    assert_eq!(manifest.schema_version, 1);
    assert_eq!(manifest.selection_rule, SEMANTIC_ORDER_SELECTION_RULE);
    assert_eq!(
        manifest.source_ndb_data_sha256,
        sha256_file(&source_ndb.join("data.mdb"))
    );
    assert_eq!(
        manifest.source_ordered_event_ids_sha256,
        sha256_file(&source_order_path)
    );
    assert_eq!(
        manifest.output_ordered_event_ids_sha256,
        sha256_file(&output.join("ordered-event-ids.bin"))
    );
    assert_eq!(manifest.input_events, 5);
    assert_eq!(manifest.retained_events, 3);
    assert_eq!(manifest.excluded_events, 2);
    assert_eq!(
        read_ids(&output.join("ordered-event-ids.bin")),
        [ids[0], ids[2], ids[4]]
    );
    assert_eq!(
        manifest.excluded,
        [
            oracle_mvp::semantic_order::ExcludedSemanticOrderEvent {
                original_row: 0,
                event_id: hex_id(&ids[3]),
                content_bytes: "\u{2003}\u{a0}".len() as u64,
            },
            oracle_mvp::semantic_order::ExcludedSemanticOrderEvent {
                original_row: 3,
                event_id: hex_id(&ids[1]),
                content_bytes: 3,
            },
        ]
    );
    assert_eq!(
        serde_json::from_slice::<SemanticOrderManifest>(
            &fs::read(output.join("manifest.json")).expect("semantic manifest")
        )
        .expect("manifest JSON"),
        manifest
    );
    assert!(!temp.path().join(".semantic-corpus.partial").exists());

    assert_eq!(
        derive_semantic_order(&source_ndb, &source_order_path, &output)
            .expect("deeply verified reuse"),
        manifest
    );
}

#[test]
fn rejects_reuse_when_the_output_or_source_identity_changed() {
    let temp = tempfile::tempdir().expect("temporary directory");
    let source_ndb = temp.path().join("source.ndb");
    let source = open_ndb(&source_ndb);
    let events = [signed_test_event("one", 1), signed_test_event("two", 2)];
    for event in &events {
        submit(&source, event);
    }
    wait_for_count(&source, events.len());
    drop(source);
    let ids = events
        .iter()
        .map(|event| event_id(event))
        .collect::<Vec<_>>();
    let source_order_path = temp.path().join("source-order.bin");
    write_ids(&source_order_path, &ids);

    let output = temp.path().join("semantic-corpus");
    derive_semantic_order(&source_ndb, &source_order_path, &output).expect("initial derivation");

    let output_order = output.join("ordered-event-ids.bin");
    let mut changed = fs::read(&output_order).expect("output order");
    changed[0] ^= 1;
    fs::write(&output_order, changed).expect("corrupt output order");
    let error = derive_semantic_order(&source_ndb, &source_order_path, &output)
        .expect_err("changed output must not be reused");
    assert!(error.to_string().contains("output ordered-ID SHA-256"));

    let manifest_path = output.join("manifest.json");
    let mut forged: SemanticOrderManifest =
        serde_json::from_slice(&fs::read(&manifest_path).expect("semantic manifest"))
            .expect("manifest JSON");
    forged.output_ordered_event_ids_sha256 = sha256_file(&output_order);
    fs::write(
        &manifest_path,
        serde_json::to_vec_pretty(&forged).expect("encode forged manifest"),
    )
    .expect("forge matching output checksum");
    let error = derive_semantic_order(&source_ndb, &source_order_path, &output)
        .expect_err("a matching checksum must not replace semantic verification");
    assert!(error.to_string().contains("retained output row 0"));

    fs::remove_dir_all(&output).expect("remove corrupt output");
    derive_semantic_order(&source_ndb, &source_order_path, &output).expect("second derivation");
    write_ids(&source_order_path, &[ids[1], ids[0]]);
    let error = derive_semantic_order(&source_ndb, &source_order_path, &output)
        .expect_err("changed source order must not reuse the artifact");
    assert!(error.to_string().contains("source ordered-ID SHA-256"));
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
    let deadline = Instant::now() + Duration::from_secs(10);
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

// Test infrastructure only: production code reads existing signed events.
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

fn hex_id(id: &[u8; 32]) -> String {
    id.iter().map(|byte| format!("{byte:02x}")).collect()
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

fn sha256_file(path: &Path) -> String {
    format!("{:x}", Sha256::digest(fs::read(path).expect("hash input")))
}
