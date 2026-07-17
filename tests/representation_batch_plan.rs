use std::fs::File;
use std::io::Write;
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::{Duration, Instant};

use nostrdb::{Config, Filter, Ndb, NoteBuilder, Transaction};
use oracle_mvp::gte::TokenRole;
use oracle_mvp::ordered_gte_token_audit::{
    OrderedGteTokenAuditConfig, OrderedGteTokenCounter, audit_ordered_gte_tokens,
};
use oracle_mvp::representation::RepresentationDescriptor;
use oracle_mvp::representation_batch_plan::{
    BATCHING_RULE, RepresentationBatchPlanConfig, create_representation_batch_plan,
    open_representation_batch_plan, tokenization_contract_sha256,
};
use oracle_mvp::snapshot::Result;

#[test]
fn immutable_plan_uses_verified_lengths_and_exact_shard_local_batch_shapes() {
    let fixture = Fixture::new();
    let audit_path = fixture.temp.path().join("token-audit");
    let plan_path = fixture.temp.path().join("batch-plan");
    let mut counter = LengthCounter::new();
    audit_ordered_gte_tokens(
        &fixture.ndb_path,
        &fixture.ordered_path,
        &audit_path,
        &OrderedGteTokenAuditConfig {
            batch_size: 2,
            shard_rows: 2,
        },
        &mut counter,
    )
    .expect("audit exact fixture lengths");

    let config = RepresentationBatchPlanConfig {
        shard_rows: 6,
        batch_rows: 2,
    };
    let first =
        create_representation_batch_plan(&fixture.ordered_path, &audit_path, &plan_path, &config)
            .expect("create immutable batch plan");
    assert_eq!(first.manifest().batching_rule, BATCHING_RULE);
    assert_eq!(first.manifest().total_rows, 6);
    assert_eq!(first.manifest().total_batches, 3);
    assert_eq!(
        first
            .manifest()
            .batch_shapes
            .iter()
            .map(|shape| (
                shape.rows_per_batch,
                shape.padded_tokens_per_row,
                shape.batches,
            ))
            .collect::<Vec<_>>(),
        vec![(2, 2, 1), (2, 4, 1), (2, 6, 1)]
    );

    let batches = first.shard_batches(0).expect("derive first shard schedule");
    assert_eq!(
        batches
            .iter()
            .map(|batch| {
                (
                    batch
                        .rows
                        .iter()
                        .map(|row| (row.row_offset, row.tokens))
                        .collect::<Vec<_>>(),
                    batch.padded_tokens_per_row,
                )
            })
            .collect::<Vec<_>>(),
        vec![
            (vec![(1, 1), (3, 2)], 2),
            (vec![(5, 3), (2, 4)], 4),
            (vec![(4, 5), (0, 6)], 6),
        ]
    );

    let reopened = open_representation_batch_plan(&fixture.ordered_path, &audit_path, &plan_path)
        .expect("reopen verified batch plan");
    assert_eq!(reopened.identity(), first.identity());

    let error = create_representation_batch_plan(
        &fixture.ordered_path,
        &audit_path,
        &plan_path,
        &RepresentationBatchPlanConfig {
            shard_rows: 6,
            batch_rows: 3,
        },
    )
    .expect_err("an existing plan cannot silently change its production batch rows");
    assert!(error.to_string().contains("different settings"), "{error}");
}

#[test]
fn token_lengths_are_not_invalidated_by_unrelated_container_binary_changes() {
    let original = fixture_descriptor();
    let mut rebuilt_container = original.clone();
    rebuilt_container.container_image = "rebuilt@sha256:".to_owned() + &"6".repeat(64);
    assert_eq!(
        tokenization_contract_sha256(&original).expect("hash original tokenizer contract"),
        tokenization_contract_sha256(&rebuilt_container)
            .expect("hash rebuilt-container tokenizer contract"),
        "the model, tokenizer, worker, dependencies, and input contract did not change"
    );

    rebuilt_container.worker_sha256 = "7".repeat(64);
    assert_ne!(
        tokenization_contract_sha256(&original).expect("hash original tokenizer contract"),
        tokenization_contract_sha256(&rebuilt_container)
            .expect("hash changed-worker tokenizer contract"),
        "a changed tokenizer worker must invalidate audited lengths"
    );
}

struct Fixture {
    temp: tempfile::TempDir,
    ndb_path: std::path::PathBuf,
    ordered_path: std::path::PathBuf,
}

impl Fixture {
    fn new() -> Self {
        let temp = tempfile::tempdir().expect("temporary directory");
        let ndb_path = temp.path().join("english.ndb");
        let ndb = Ndb::new(
            ndb_path.to_str().expect("UTF-8 NDB path"),
            &Config::new().set_mapsize(512 * 1024 * 1024),
        )
        .expect("open NDB");
        let contents = ["aaaaaa", "a", "aaaa", "aa", "aaaaa", "aaa"];
        let events = contents
            .iter()
            .enumerate()
            .map(|(index, content)| signed_event(content, index as u64))
            .collect::<Vec<_>>();
        for event in &events {
            ndb.process_event(event).expect("submit event");
        }
        wait_for_count(&ndb, events.len());
        drop(ndb);
        let ordered_path = temp.path().join("ordered-event-ids.bin");
        let mut ordered = File::create(&ordered_path).expect("ordered IDs");
        for event in &events {
            ordered
                .write_all(&event_id(event))
                .expect("write ordered ID");
        }
        ordered.sync_all().expect("sync ordered IDs");
        Self {
            temp,
            ndb_path,
            ordered_path,
        }
    }
}

struct LengthCounter {
    descriptor: RepresentationDescriptor,
    _calls: Arc<Mutex<usize>>,
}

impl LengthCounter {
    fn new() -> Self {
        Self {
            descriptor: fixture_descriptor(),
            _calls: Arc::new(Mutex::new(0)),
        }
    }
}

impl OrderedGteTokenCounter for LengthCounter {
    fn descriptor(&self) -> &RepresentationDescriptor {
        &self.descriptor
    }

    fn token_lengths(&mut self, role: TokenRole, texts: &[&str]) -> Result<Vec<u32>> {
        let extra = if role == TokenRole::Query { 2 } else { 0 };
        Ok(texts
            .iter()
            .map(|text| u32::try_from(text.len() + extra).expect("fixture length"))
            .collect())
    }
}

fn fixture_descriptor() -> RepresentationDescriptor {
    RepresentationDescriptor {
        model_id: "fixture/gte".to_owned(),
        model_revision: "1".repeat(40),
        model_lock_sha256: "2".repeat(64),
        worker_sha256: "3".repeat(64),
        dependency_lock_sha256: "4".repeat(64),
        container_image: "fixture@sha256:".to_owned() + &"5".repeat(64),
        torch_version: "2.12.1".to_owned(),
        transformers_version: "4.41.2".to_owned(),
        cuda_version: "13.0.2".to_owned(),
        execution_device: "cpu".to_owned(),
        dimensions: 3,
        model_token_ceiling: 100,
        document_input: "raw-note-content".to_owned(),
        query_instruction: "fixture-query-instruction".to_owned(),
        pooling: "last-token".to_owned(),
        normalization: "l2".to_owned(),
        numeric_format: "f32le".to_owned(),
    }
}

fn signed_event(content: &str, offset: u64) -> String {
    NoteBuilder::new()
        .kind(1)
        .content(content)
        .created_at(1_700_000_000 + offset)
        .sign(&[7_u8; 32])
        .build()
        .expect("sign event")
        .json()
        .expect("event JSON")
}

fn wait_for_count(ndb: &Ndb, expected: usize) {
    let deadline = Instant::now() + Duration::from_secs(30);
    loop {
        let txn = Transaction::new(ndb).expect("read transaction");
        let all = Filter::new().build();
        let count = ndb
            .fold(&txn, &[all], 0_usize, |count, _| count + 1)
            .expect("count events");
        if count == expected {
            return;
        }
        assert!(Instant::now() < deadline, "NDB persistence timeout");
        thread::sleep(Duration::from_millis(10));
    }
}

fn event_id(event: &str) -> [u8; 32] {
    let value: serde_json::Value = serde_json::from_str(event).expect("event value");
    let value = value["id"].as_str().expect("event ID");
    let mut output = [0_u8; 32];
    for (index, chunk) in value.as_bytes().chunks_exact(2).enumerate() {
        output[index] = (hex(chunk[0]) << 4) | hex(chunk[1]);
    }
    output
}

fn hex(value: u8) -> u8 {
    match value {
        b'0'..=b'9' => value - b'0',
        b'a'..=b'f' => value - b'a' + 10,
        _ => panic!("invalid hex"),
    }
}
