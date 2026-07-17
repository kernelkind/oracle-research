use std::fs::{self, File};
use std::io::Write;
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::{Duration, Instant};

use nostrdb::{Config, Filter, Ndb, NoteBuilder, Transaction};
use oracle_mvp::gte::TokenRole;
use oracle_mvp::ordered_gte_token_audit::{
    OrderedGteTokenAuditConfig, OrderedGteTokenCounter, audit_ordered_gte_tokens,
    open_ordered_gte_token_audit,
};
use oracle_mvp::representation::RepresentationDescriptor;
use oracle_mvp::snapshot::Result;

#[test]
fn audits_both_roles_in_order_and_reuses_completed_shards() {
    let fixture = Fixture::new();
    let output = fixture.temp.path().join("token-audit");
    let calls = Arc::new(Mutex::new(Vec::new()));
    let mut counter = FixtureCounter::new(calls.clone(), 100);
    let config = OrderedGteTokenAuditConfig {
        batch_size: 2,
        shard_rows: 2,
    };

    let first = audit_ordered_gte_tokens(
        &fixture.ndb_path,
        &fixture.ordered_path,
        &output,
        &config,
        &mut counter,
    )
    .expect("complete ordered token audit");
    assert_eq!(first.audited_rows, 4);
    assert_eq!(first.reused_rows, 0);
    assert_eq!(first.manifest.total_rows, 4);
    assert_eq!(first.manifest.document_total_tokens, 24);
    assert_eq!(first.manifest.query_total_tokens, 32);
    assert_eq!(first.manifest.document_maximum_tokens, 6);
    assert_eq!(first.manifest.query_maximum_tokens, 8);
    assert_eq!(calls.lock().expect("call log").len(), 4);

    calls.lock().expect("call log").clear();
    let second = audit_ordered_gte_tokens(
        &fixture.ndb_path,
        &fixture.ordered_path,
        &output,
        &config,
        &mut counter,
    )
    .expect("resume completed audit");
    assert_eq!(second.audited_rows, 0);
    assert_eq!(second.reused_rows, 4);
    assert!(calls.lock().expect("call log").is_empty());
    assert_eq!(
        open_ordered_gte_token_audit(&fixture.ordered_path, &output).expect("reopen audit"),
        second.manifest
    );
}

#[test]
fn resumes_completed_shards_after_interrupted_manifest_publication() {
    let fixture = Fixture::new();
    let output = fixture.temp.path().join("interrupted-manifest-audit");
    let calls = Arc::new(Mutex::new(Vec::new()));
    let mut counter = FixtureCounter::new(calls.clone(), 100);
    let config = OrderedGteTokenAuditConfig {
        batch_size: 2,
        shard_rows: 2,
    };

    audit_ordered_gte_tokens(
        &fixture.ndb_path,
        &fixture.ordered_path,
        &output,
        &config,
        &mut counter,
    )
    .expect("complete initial ordered token audit");
    fs::remove_file(output.join("manifest.json")).expect("remove final manifest");
    let temporary = output.join(".manifest.json.tmp");
    fs::write(&temporary, b"{\"interrupted\":").expect("leave interrupted manifest publication");
    calls.lock().expect("call log").clear();

    let resumed = audit_ordered_gte_tokens(
        &fixture.ndb_path,
        &fixture.ordered_path,
        &output,
        &config,
        &mut counter,
    )
    .expect("resume from completed token-audit shards");
    assert_eq!(resumed.audited_rows, 0);
    assert_eq!(resumed.reused_rows, 4);
    assert!(calls.lock().expect("call log").is_empty());
    assert!(
        !temporary.exists(),
        "stale publication file must not survive a successful resume"
    );
    assert_eq!(
        open_ordered_gte_token_audit(&fixture.ordered_path, &output)
            .expect("open atomically published manifest"),
        resumed.manifest
    );
}

#[test]
fn refuses_interrupted_shards_from_a_different_ordered_corpus() {
    let fixture = Fixture::new();
    let output = fixture.temp.path().join("changed-order-audit");
    let calls = Arc::new(Mutex::new(Vec::new()));
    let mut counter = FixtureCounter::new(calls.clone(), 100);
    let config = OrderedGteTokenAuditConfig {
        batch_size: 2,
        shard_rows: 2,
    };

    audit_ordered_gte_tokens(
        &fixture.ndb_path,
        &fixture.ordered_path,
        &output,
        &config,
        &mut counter,
    )
    .expect("complete initial ordered token audit");
    fs::remove_file(output.join("manifest.json")).expect("simulate interrupted publication");
    let mut changed_order = fs::read(&fixture.ordered_path).expect("read ordered IDs");
    let first = changed_order[..32].to_vec();
    let second = changed_order[32..64].to_vec();
    changed_order[..32].copy_from_slice(&second);
    changed_order[32..64].copy_from_slice(&first);
    fs::write(&fixture.ordered_path, changed_order).expect("replace ordered IDs");
    calls.lock().expect("call log").clear();

    let error = audit_ordered_gte_tokens(
        &fixture.ndb_path,
        &fixture.ordered_path,
        &output,
        &config,
        &mut counter,
    )
    .expect_err("completed shards from another order must never be reused");
    assert!(error.to_string().contains("ordered"), "{error}");
    assert!(
        calls.lock().expect("call log").is_empty(),
        "input identity must fail before tokenization"
    );
}

#[test]
fn refuses_any_note_that_would_require_truncation() {
    let fixture = Fixture::new();
    let output = fixture.temp.path().join("over-limit-audit");
    let mut counter = FixtureCounter::new(Arc::new(Mutex::new(Vec::new())), 5);
    let error = audit_ordered_gte_tokens(
        &fixture.ndb_path,
        &fixture.ordered_path,
        &output,
        &OrderedGteTokenAuditConfig {
            batch_size: 2,
            shard_rows: 2,
        },
        &mut counter,
    )
    .expect_err("over-limit note must stop the audit");
    assert!(error.to_string().contains("would require truncation"));
    assert!(!output.join("manifest.json").exists());
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
        let events = (0..4)
            .map(|index| signed_event(&format!("note-{index}"), index))
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

type TokenCalls = Arc<Mutex<Vec<(TokenRole, Vec<String>)>>>;

struct FixtureCounter {
    descriptor: RepresentationDescriptor,
    calls: TokenCalls,
}

impl FixtureCounter {
    fn new(calls: TokenCalls, ceiling: u32) -> Self {
        Self {
            descriptor: RepresentationDescriptor {
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
                model_token_ceiling: ceiling,
                document_input: "raw-note-content".to_owned(),
                query_instruction: "fixture-query-instruction".to_owned(),
                pooling: "last-token".to_owned(),
                normalization: "l2".to_owned(),
                numeric_format: "f32le".to_owned(),
            },
            calls,
        }
    }
}

impl OrderedGteTokenCounter for FixtureCounter {
    fn descriptor(&self) -> &RepresentationDescriptor {
        &self.descriptor
    }

    fn token_lengths(&mut self, role: TokenRole, texts: &[&str]) -> Result<Vec<u32>> {
        self.calls
            .lock()
            .expect("call log")
            .push((role, texts.iter().map(|text| (*text).to_owned()).collect()));
        let extra = if role == TokenRole::Query { 2 } else { 0 };
        Ok(texts
            .iter()
            .map(|text| u32::try_from(text.len() + extra).expect("fixture length"))
            .collect())
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
