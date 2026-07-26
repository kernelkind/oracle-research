use std::fs::{self, File};
use std::io::{BufRead, BufReader, Write};
use std::os::unix::fs::PermissionsExt;
use std::thread;
use std::time::{Duration, Instant};

use nostrdb::{Config, Filter, Ndb, NoteBuilder, Transaction};
use oracle_mvp::io_pressure::IoPressureController;
use oracle_mvp::topic_sample::{
    TopicSampleConfig, TopicSampleManifest, TopicSampleRecord,
    materialize_topic_sample_with_controller,
};
use sha2::{Digest, Sha256};

const AUTHOR_SPLIT_DOMAIN: &[u8] = b"oracle-mvp/topic-sample-author-split/v1\0";

#[test]
fn materializes_exact_author_disjoint_quotas_and_stops_without_reading_another_id() {
    let root = tempfile::tempdir_in("/dev/shm").expect("tmpfs test directory");
    let source_path = root.path().join("source.ndb");
    let ndb = open_ndb(&source_path);
    let seed = [42_u8; 32];
    let (learning, evaluation) = fixture_notes_for_both_splits(&seed);
    for note in [&learning, &evaluation] {
        ndb.process_event(&note.json).expect("submit fixture note");
    }
    wait_for_count(&ndb, 2);
    drop(ndb);
    let source_data_path = source_path.join("data.mdb");
    let mut source_permissions = fs::metadata(&source_data_path)
        .expect("source data metadata")
        .permissions();
    source_permissions.set_mode(0o444);
    fs::set_permissions(&source_data_path, source_permissions).expect("make source data read-only");

    let ordered_path = root.path().join("ordered-event-ids.bin");
    let mut ordered = File::create(&ordered_path).expect("create ordered IDs");
    ordered
        .write_all(&learning.event_id)
        .expect("write learning ID");
    ordered
        .write_all(&evaluation.event_id)
        .expect("write evaluation ID");
    ordered
        .write_all(&[0xff; 32])
        .expect("write unreachable invalid ID");
    drop(ordered);

    let semantic_manifest_path = root.path().join("semantic-manifest.json");
    fs::write(
        &semantic_manifest_path,
        serde_json::to_vec_pretty(&serde_json::json!({
            "schema_version": 1,
            "selection_rule": "preserve-source-order-exclude-raw-content-trim-empty-v1",
            "source_ndb_data_sha256": hash_file(&source_path.join("data.mdb")),
            "output_ordered_event_ids_sha256": hash_file(&ordered_path),
            "retained_events": 3
        }))
        .expect("encode semantic manifest"),
    )
    .expect("write semantic manifest");

    let data_before = hash_file(&source_data_path);
    let pressure_path = root.path().join("io.pressure");
    write_pressure(&pressure_path, 0);
    let controller =
        IoPressureController::start(&pressure_path).expect("start pressure controller");
    let output_path = root.path().join("sample");
    let manifest = materialize_topic_sample_with_controller(
        &TopicSampleConfig {
            source_corpus_path: source_path.clone(),
            ordered_event_ids_path: ordered_path,
            semantic_manifest_path,
            output_path: output_path.clone(),
            learning_rows: 1,
            evaluation_rows: 1,
            max_examined_rows: 3,
            max_sample_bytes: 1_048_576,
            author_split_seed_hex: hex(&seed),
        },
        &controller,
    )
    .expect("materialize bounded sample");
    controller.shutdown().expect("stop pressure controller");

    assert_eq!(1, manifest.learning_rows);
    assert_eq!(1, manifest.evaluation_rows);
    assert_eq!(2, manifest.examined_rows);
    assert_eq!(3, manifest.max_examined_rows);
    assert_eq!(1_048_576, manifest.max_sample_bytes);
    let mut sampled_prefix = Sha256::new();
    sampled_prefix.update(learning.event_id);
    sampled_prefix.update(evaluation.event_id);
    assert_eq!(
        format!("{:x}", sampled_prefix.finalize()),
        manifest.sampled_order_prefix_sha256
    );
    assert_eq!(
        fs::metadata(&source_data_path)
            .expect("source data metadata")
            .len(),
        manifest.source_ndb_data_bytes
    );
    assert_eq!(data_before, hash_file(&source_data_path));

    let records = BufReader::new(File::open(output_path.join("sample.jsonl")).expect("sample"))
        .lines()
        .map(|line| {
            serde_json::from_str::<TopicSampleRecord>(&line.expect("sample line"))
                .expect("sample record")
        })
        .collect::<Vec<_>>();
    assert_eq!(2, records.len());
    assert_eq!("learning", records[0].split);
    assert_eq!(hex(&learning.event_id), records[0].note_id);
    assert_eq!("evaluation", records[1].split);
    assert_eq!(hex(&evaluation.event_id), records[1].note_id);
    assert_ne!(records[0].pubkey, records[1].pubkey);

    let stored: TopicSampleManifest = serde_json::from_reader(
        File::open(output_path.join("manifest.json")).expect("stored manifest"),
    )
    .expect("decode stored manifest");
    assert_eq!(manifest, stored);
}

struct FixtureNote {
    json: String,
    event_id: [u8; 32],
    pubkey: [u8; 32],
}

fn fixture_notes_for_both_splits(seed: &[u8; 32]) -> (FixtureNote, FixtureNote) {
    let mut learning = None;
    let mut evaluation = None;
    for secret_byte in 1_u8..=64 {
        let content = format!("fixture note from author {secret_byte}");
        let json = NoteBuilder::new()
            .kind(1)
            .content(&content)
            .created_at(1_700_000_000 + u64::from(secret_byte))
            .sign(&[secret_byte; 32])
            .build()
            .expect("sign fixture note")
            .json()
            .expect("fixture JSON");
        let value: serde_json::Value = serde_json::from_str(&json).expect("fixture value");
        let note = FixtureNote {
            event_id: decode_hex_32(value["id"].as_str().expect("event ID")),
            pubkey: decode_hex_32(value["pubkey"].as_str().expect("pubkey")),
            json,
        };
        if is_evaluation_author(seed, &note.pubkey) {
            evaluation.get_or_insert(note);
        } else {
            learning.get_or_insert(note);
        }
        if learning.is_some() && evaluation.is_some() {
            break;
        }
    }
    (
        learning.expect("learning author"),
        evaluation.expect("evaluation author"),
    )
}

fn is_evaluation_author(seed: &[u8; 32], pubkey: &[u8; 32]) -> bool {
    let mut hasher = Sha256::new();
    hasher.update(AUTHOR_SPLIT_DOMAIN);
    hasher.update(seed);
    hasher.update(pubkey);
    let digest = hasher.finalize();
    u64::from_be_bytes(digest[..8].try_into().expect("digest prefix")) < (1_u64 << 63)
}

fn open_ndb(path: &std::path::Path) -> Ndb {
    Ndb::new(
        path.to_str().expect("UTF-8 NostrDB path"),
        &Config::new().set_mapsize(64 * 1_024 * 1_024),
    )
    .expect("open NostrDB")
}

fn wait_for_count(ndb: &Ndb, expected: usize) {
    let deadline = Instant::now() + Duration::from_secs(30);
    loop {
        let transaction = Transaction::new(ndb).expect("read transaction");
        let count = ndb
            .fold(
                &transaction,
                &[Filter::new().build()],
                0_usize,
                |count, _| count + 1,
            )
            .expect("count fixture notes");
        if count == expected {
            return;
        }
        assert!(Instant::now() < deadline, "NostrDB persistence timeout");
        thread::sleep(Duration::from_millis(10));
    }
}

fn hash_file(path: &std::path::Path) -> String {
    format!(
        "{:x}",
        Sha256::digest(fs::read(path).expect("read hash input"))
    )
}

fn decode_hex_32(encoded: &str) -> [u8; 32] {
    let mut output = [0_u8; 32];
    for (index, chunk) in encoded.as_bytes().chunks_exact(2).enumerate() {
        output[index] = (decode_nibble(chunk[0]) << 4) | decode_nibble(chunk[1]);
    }
    output
}

fn decode_nibble(value: u8) -> u8 {
    match value {
        b'0'..=b'9' => value - b'0',
        b'a'..=b'f' => value - b'a' + 10,
        _ => panic!("invalid hex"),
    }
}

fn hex(bytes: &[u8]) -> String {
    bytes.iter().map(|byte| format!("{byte:02x}")).collect()
}

fn write_pressure(path: &std::path::Path, some_total_microseconds: u64) {
    fs::write(
        path,
        format!(
            "some avg10=0.00 avg60=0.00 avg300=0.00 total={some_total_microseconds}\n\
             full avg10=0.00 avg60=0.00 avg300=0.00 total=0\n"
        ),
    )
    .expect("write pressure sample");
}
