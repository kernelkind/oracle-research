use std::collections::BTreeMap;
use std::fs;
use std::process::Command;
use std::thread;
use std::time::{Duration, Instant};

use nostrdb::{Config, Error as NdbError, Filter, Ndb, NoteBuilder, Transaction};
use sha2::{Digest, Sha256};

const ROW_ORDER_DOMAIN: &[u8] = b"oracle-mvp/canonical-row-order/v1\0";

#[test]
fn builds_one_persisted_event_per_exact_content_in_stable_order() {
    let temp = tempfile::tempdir().expect("temporary directory");
    let filtered_path = temp.path().join("filtered.ndb");
    let filtered = open_ndb(&filtered_path, false);

    let mut events = (0..16_500)
        .map(|index| signed_test_event(&format!("unique-{index}"), index))
        .collect::<Vec<_>>();
    events.push(signed_test_event("same content", 20_001));
    events.push(signed_test_event("same content", 20_002));
    events.push(signed_test_event("nostr 日本語", 20_003));
    events.push(signed_test_event("read https://example.com", 20_004));
    for event in &events {
        submit(&filtered, event);
    }
    wait_for_count(&filtered, events.len());

    let expected = expected_representatives(&events);
    assert_eq!(expected.len(), events.len() - 1);
    let first_output = temp.path().join("first");
    let first_summary = run_stage(&filtered_path, &first_output);
    assert_eq!(first_summary["scanned_events"], events.len() as u64);
    assert_eq!(first_summary["retained_events"], expected.len() as u64);
    assert_eq!(first_summary["duplicate_events"], 1);

    let deduplicated = open_ndb(&first_output.join("ndb"), true);
    assert_eq!(stored_events(&deduplicated), expected);
    let ordered = read_ids(&first_output.join("ordered-event-ids.bin"));
    let mut expected_order = expected.keys().map(|id| decode_id(id)).collect::<Vec<_>>();
    expected_order.sort_unstable_by_key(row_order_key);
    assert_eq!(ordered, expected_order);
    assert_eq!(
        fs::read_to_string(first_output.join("ordered-event-ids.sha256")).expect("checksum file"),
        format!(
            "{}  ordered-event-ids.bin\n",
            sha256_file(&first_output.join("ordered-event-ids.bin"))
        )
    );
    assert!(!first_output.join("aliases.bin").exists());

    let second_output = temp.path().join("second");
    let second_summary = run_stage(&filtered_path, &second_output);
    assert_eq!(second_summary, first_summary);
    assert_eq!(
        fs::read(first_output.join("ordered-event-ids.bin")).expect("first ordered IDs"),
        fs::read(second_output.join("ordered-event-ids.bin")).expect("second ordered IDs")
    );
    assert_eq!(
        fs::read(first_output.join("ordered-event-ids.sha256")).expect("first checksum"),
        fs::read(second_output.join("ordered-event-ids.sha256")).expect("second checksum")
    );
}

#[test]
fn refuses_to_replace_an_existing_output_directory() {
    let temp = tempfile::tempdir().expect("temporary directory");
    let filtered_path = temp.path().join("filtered.ndb");
    drop(open_ndb(&filtered_path, false));
    let output_path = temp.path().join("deduplicated");
    fs::create_dir(&output_path).expect("existing output");
    fs::write(output_path.join("owned-by-user"), b"keep").expect("sentinel");

    let output = Command::new(env!("CARGO_BIN_EXE_stage4_deduplicate"))
        .arg(&filtered_path)
        .arg(&output_path)
        .output()
        .expect("run stage4_deduplicate");

    assert!(!output.status.success());
    assert_eq!(
        fs::read(output_path.join("owned-by-user")).expect("sentinel survives"),
        b"keep"
    );
}

fn run_stage(filtered: &std::path::Path, output: &std::path::Path) -> serde_json::Value {
    let result = Command::new(env!("CARGO_BIN_EXE_stage4_deduplicate"))
        .arg(filtered)
        .arg(output)
        .output()
        .expect("run stage4_deduplicate");
    assert!(
        result.status.success(),
        "stage failed: {}",
        String::from_utf8_lossy(&result.stderr)
    );
    serde_json::from_slice(&result.stdout).expect("summary JSON")
}

fn expected_representatives(events: &[String]) -> BTreeMap<String, serde_json::Value> {
    let mut by_content = BTreeMap::<String, Vec<serde_json::Value>>::new();
    for event in events {
        let value: serde_json::Value = serde_json::from_str(event).expect("event JSON");
        by_content
            .entry(value["content"].as_str().expect("content").to_owned())
            .or_default()
            .push(value);
    }
    by_content
        .into_values()
        .map(|events| {
            let event = events
                .into_iter()
                .min_by(|left, right| left["id"].as_str().cmp(&right["id"].as_str()))
                .expect("content group");
            (event["id"].as_str().expect("event ID").to_owned(), event)
        })
        .collect()
}

fn open_ndb(path: &std::path::Path, trusted_source: bool) -> Ndb {
    Ndb::new(
        path.to_str().expect("UTF-8 NostrDB path"),
        &Config::new()
            .set_mapsize(2 * 1_024 * 1_024 * 1_024)
            .skip_validation(trusted_source),
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
    let deadline = Instant::now() + Duration::from_secs(30);
    loop {
        let count = stored_events(ndb).len();
        if count >= expected {
            return;
        }
        assert!(
            Instant::now() < deadline,
            "timed out waiting for {expected} notes; found {count}"
        );
        thread::sleep(Duration::from_millis(10));
    }
}

fn stored_events(ndb: &Ndb) -> BTreeMap<String, serde_json::Value> {
    let txn = Transaction::new(ndb).expect("read transaction");
    let all = Filter::new().build();
    ndb.fold(&txn, &[all], BTreeMap::new(), |mut events, note| {
        let value: serde_json::Value =
            serde_json::from_str(&note.json().expect("stored event JSON"))
                .expect("stored event value");
        events.insert(value["id"].as_str().expect("event ID").to_owned(), value);
        events
    })
    .expect("scan NostrDB")
}

fn read_ids(path: &std::path::Path) -> Vec<[u8; 32]> {
    let bytes = fs::read(path).expect("ordered IDs");
    let mut records = bytes.chunks_exact(32);
    let ids = records
        .by_ref()
        .map(|chunk| chunk.try_into().expect("event ID width"))
        .collect();
    assert!(records.remainder().is_empty(), "partial event ID");
    ids
}

fn row_order_key(event_id: &[u8; 32]) -> [u8; 32] {
    let mut hasher = Sha256::new();
    hasher.update(ROW_ORDER_DOMAIN);
    hasher.update(event_id);
    hasher.finalize().into()
}

fn sha256_file(path: &std::path::Path) -> String {
    format!("{:x}", Sha256::digest(fs::read(path).expect("hash input")))
}

fn decode_id(value: &str) -> [u8; 32] {
    let mut output = [0_u8; 32];
    for (index, chunk) in value.as_bytes().chunks_exact(2).enumerate() {
        output[index] = (decode_hex(chunk[0]) << 4) | decode_hex(chunk[1]);
    }
    output
}

fn decode_hex(value: u8) -> u8 {
    match value {
        b'0'..=b'9' => value - b'0',
        b'a'..=b'f' => value - b'a' + 10,
        _ => panic!("invalid hex"),
    }
}

fn signed_test_event(content: &str, seed: usize) -> String {
    NoteBuilder::new()
        .kind(1)
        .content(content)
        .created_at(1_700_000_000 + seed as u64)
        .sign(&[7_u8; 32])
        .build()
        .expect("sign test event")
        .json()
        .expect("serialize test event")
}
