use nostrdb::{Config, Ndb, NoteBuilder, Transaction};
use oracle_mvp::corpus_post_sample::{CorpusPostSampleConfig, export_corpus_post_sample};
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::{fs, thread, time::Duration};

#[test]
fn exports_hash_ordered_original_events_and_rejects_address_replies_without_source_writes() {
    let dir = tempfile::tempdir_in("/dev/shm").unwrap();
    let source = dir.path().join("source");
    let ndb = Ndb::new(
        source.to_str().unwrap(),
        &Config::new().set_mapsize(64 << 20),
    )
    .unwrap();
    let a = NoteBuilder::new()
        .kind(1)
        .content("An original English post.")
        .created_at(1)
        .sign(&[1; 32])
        .build()
        .unwrap()
        .json()
        .unwrap();
    let b = NoteBuilder::new()
        .kind(1)
        .content("An address-based reply.")
        .created_at(2)
        .start_tag()
        .tag_str("a")
        .tag_str("30023:author:thread")
        .tag_str("")
        .tag_str("reply")
        .sign(&[2; 32])
        .build()
        .unwrap()
        .json()
        .unwrap();
    for event in [&a, &b] {
        ndb.process_event(event).unwrap();
    }
    for _ in 0..200 {
        let tx = Transaction::new(&ndb).unwrap();
        let id = serde_json::from_str::<Value>(&b).unwrap()["id"]
            .as_str()
            .unwrap()
            .to_owned();
        let raw = hex_id(&id);
        if ndb.get_note_by_id(&tx, &raw).is_ok() {
            break;
        }
        thread::sleep(Duration::from_millis(10));
    }
    drop(ndb);
    let before = fs::read(source.join("data.mdb")).unwrap();
    let lock_before = fs::read(source.join("lock.mdb")).unwrap();
    let mut ids = Vec::new();
    for event in [&a, &b] {
        ids.extend(hex_id(
            serde_json::from_str::<Value>(event).unwrap()["id"]
                .as_str()
                .unwrap(),
        ));
    }
    let order = dir.path().join("ids.bin");
    fs::write(&order, &ids).unwrap();
    let config = CorpusPostSampleConfig {
        source_corpus_path: source.clone(),
        ordered_event_ids_path: order,
        ordered_event_ids_sha256: format!("{:x}", Sha256::digest(&ids)),
        selection_domain: "sample-test\0".into(),
        candidate_rows: 2,
        language_model_path: None,
    };
    let out = dir.path().join("export");
    export_corpus_post_sample(&config, &out).unwrap();
    let records: Vec<Value> = fs::read_to_string(out.join("candidates.jsonl"))
        .unwrap()
        .lines()
        .map(|s| serde_json::from_str(s).unwrap())
        .collect();
    assert_eq!(records.len(), 2);
    assert!(
        records[0]["selection_order_sha256"].as_str().unwrap()
            < records[1]["selection_order_sha256"].as_str().unwrap()
    );
    assert!(
        records
            .iter()
            .find(|r| r["text"] == "An original English post.")
            .unwrap()["root_non_quote"]
            .as_bool()
            .unwrap()
    );
    assert!(
        !records
            .iter()
            .find(|r| r["text"] == "An address-based reply.")
            .unwrap()["root_non_quote"]
            .as_bool()
            .unwrap()
    );
    assert_eq!(before, fs::read(source.join("data.mdb")).unwrap());
    assert_eq!(lock_before, fs::read(source.join("lock.mdb")).unwrap());
    assert!(export_corpus_post_sample(&config, &out).is_err());
    let mut bad = config;
    bad.ordered_event_ids_sha256 = "0".repeat(64);
    assert!(export_corpus_post_sample(&bad, &dir.path().join("bad")).is_err());
    assert!(!dir.path().join("bad").exists());
}

fn hex_id(id: &str) -> [u8; 32] {
    std::array::from_fn(|i| u8::from_str_radix(&id[i * 2..i * 2 + 2], 16).unwrap())
}
