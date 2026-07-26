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

#[test]
fn skips_a_high_confidence_textual_copy_from_the_opposite_split() {
    let root = tempfile::tempdir_in("/dev/shm").expect("tmpfs test directory");
    let source_path = root.path().join("source.ndb");
    let ndb = open_ndb(&source_path);
    let seed = [73_u8; 32];
    let (learning_secret, evaluation_secret) = fixture_secrets_for_both_splits(&seed);
    let repeated = "Rust's ownership model prevents data races while retaining predictable native performance. \
        This release improves diagnostics for difficult lifetime errors and explains each suggested correction. \
        Read the complete release notes at https://example.com/releases/original and test the compiler with your existing projects.";
    let edited_copy = "RUST'S ownership model prevents data races while retaining predictable native performance. \
        This release improves diagnostics for difficult lifetime errors and explains each suggested correction. \
        Read the complete release notes at https://example.com/releases/revised and test the compiler with your existing projects.";
    let short_learning = "Café\tRUST";
    let short_normalized_copy = " cafe\u{301}   rust ";
    let short_distinct = "café rust!";
    let same_subject_but_distinct = "A practical way to learn Rust is to build a small command-line program, then replace owned strings \
        with borrowed references one boundary at a time. Compiler errors expose where the data must outlive each function call.";
    let learning = fixture_note(learning_secret, repeated, 1_700_100_001);
    let evaluation_copy = fixture_note(evaluation_secret, edited_copy, 1_700_100_002);
    let learning_short = fixture_note(learning_secret, short_learning, 1_700_100_003);
    let evaluation_short_copy =
        fixture_note(evaluation_secret, short_normalized_copy, 1_700_100_004);
    let evaluation_short_distinct = fixture_note(evaluation_secret, short_distinct, 1_700_100_005);
    let evaluation_distinct =
        fixture_note(evaluation_secret, same_subject_but_distinct, 1_700_100_006);
    for note in [
        &learning,
        &evaluation_copy,
        &learning_short,
        &evaluation_short_copy,
        &evaluation_short_distinct,
        &evaluation_distinct,
    ] {
        ndb.process_event(&note.json).expect("submit fixture note");
    }
    wait_for_count(&ndb, 6);
    drop(ndb);
    let source_data_path = source_path.join("data.mdb");
    let mut source_permissions = fs::metadata(&source_data_path)
        .expect("source data metadata")
        .permissions();
    source_permissions.set_mode(0o444);
    fs::set_permissions(&source_data_path, source_permissions).expect("make source data read-only");

    let ordered_path = root.path().join("ordered-event-ids.bin");
    let mut ordered = File::create(&ordered_path).expect("create ordered IDs");
    for note in [
        &learning,
        &evaluation_copy,
        &learning_short,
        &evaluation_short_copy,
        &evaluation_short_distinct,
        &evaluation_distinct,
    ] {
        ordered.write_all(&note.event_id).expect("write event ID");
    }
    drop(ordered);

    let semantic_manifest_path = root.path().join("semantic-manifest.json");
    fs::write(
        &semantic_manifest_path,
        serde_json::to_vec_pretty(&serde_json::json!({
            "schema_version": 1,
            "selection_rule": "preserve-source-order-exclude-raw-content-trim-empty-v1",
            "source_ndb_data_sha256": hash_file(&source_data_path),
            "output_ordered_event_ids_sha256": hash_file(&ordered_path),
            "retained_events": 6
        }))
        .expect("encode semantic manifest"),
    )
    .expect("write semantic manifest");

    let pressure_path = root.path().join("io.pressure");
    write_pressure(&pressure_path, 0);
    let controller =
        IoPressureController::start(&pressure_path).expect("start pressure controller");
    let output_path = root.path().join("sample");
    let manifest = materialize_topic_sample_with_controller(
        &TopicSampleConfig {
            source_corpus_path: source_path.clone(),
            ordered_event_ids_path: ordered_path,
            semantic_manifest_path: semantic_manifest_path.clone(),
            output_path: output_path.clone(),
            learning_rows: 2,
            evaluation_rows: 2,
            max_examined_rows: 6,
            max_sample_bytes: 1_048_576,
            author_split_seed_hex: hex(&seed),
        },
        &controller,
    )
    .expect("materialize copy-isolated sample");
    controller.shutdown().expect("stop pressure controller");

    assert_eq!(6, manifest.examined_rows);
    assert_eq!(2, manifest.skipped_cross_split_textual_copy_rows);
    assert_eq!(2, manifest.schema_version);
    assert_eq!(
        "semantic-order-prefix-author-hash-text-copy-disjoint-learning-first-v2",
        manifest.selection_rule
    );
    assert_eq!(
        "nfc-lower-nfc-trim-collapse-unicode-whitespace-exact-all-fuzzy-both-ge100-\
         codepoints-codepoint5-set-sha256-prefix128-codepoint-length-ge90-jaccard-ge90-v1",
        manifest.textual_copy_rule
    );
    let records = BufReader::new(File::open(output_path.join("sample.jsonl")).expect("sample"))
        .lines()
        .map(|line| {
            serde_json::from_str::<TopicSampleRecord>(&line.expect("sample line"))
                .expect("sample record")
        })
        .collect::<Vec<_>>();
    assert_eq!(4, records.len());
    assert_eq!(hex(&learning.event_id), records[0].note_id);
    assert_eq!(hex(&learning_short.event_id), records[1].note_id);
    assert_eq!(hex(&evaluation_short_distinct.event_id), records[2].note_id);
    assert_eq!(hex(&evaluation_distinct.event_id), records[3].note_id);

    let reverse_ordered_path = root.path().join("reverse-ordered-event-ids.bin");
    let mut reverse_ordered =
        File::create(&reverse_ordered_path).expect("create reverse ordered IDs");
    for note in [&evaluation_copy, &learning, &learning_short] {
        reverse_ordered
            .write_all(&note.event_id)
            .expect("write reverse event ID");
    }
    drop(reverse_ordered);
    let reverse_semantic_manifest_path = root.path().join("reverse-semantic-manifest.json");
    fs::write(
        &reverse_semantic_manifest_path,
        serde_json::to_vec_pretty(&serde_json::json!({
            "schema_version": 1,
            "selection_rule": "preserve-source-order-exclude-raw-content-trim-empty-v1",
            "source_ndb_data_sha256": hash_file(&source_data_path),
            "output_ordered_event_ids_sha256": hash_file(&reverse_ordered_path),
            "retained_events": 3
        }))
        .expect("encode reverse semantic manifest"),
    )
    .expect("write reverse semantic manifest");

    write_pressure(&pressure_path, 0);
    let reverse_controller =
        IoPressureController::start(&pressure_path).expect("start reverse pressure controller");
    let reverse_output_path = root.path().join("reverse-sample");
    let reverse_manifest = materialize_topic_sample_with_controller(
        &TopicSampleConfig {
            source_corpus_path: source_path,
            ordered_event_ids_path: reverse_ordered_path,
            semantic_manifest_path: reverse_semantic_manifest_path,
            output_path: reverse_output_path.clone(),
            learning_rows: 1,
            evaluation_rows: 1,
            max_examined_rows: 3,
            max_sample_bytes: 1_048_576,
            author_split_seed_hex: hex(&seed),
        },
        &reverse_controller,
    )
    .expect("materialize reverse copy-isolated sample");
    reverse_controller
        .shutdown()
        .expect("stop reverse pressure controller");

    assert_eq!(3, reverse_manifest.examined_rows);
    assert_eq!(1, reverse_manifest.skipped_cross_split_textual_copy_rows);
    let reverse_records =
        BufReader::new(File::open(reverse_output_path.join("sample.jsonl")).expect("sample"))
            .lines()
            .map(|line| {
                serde_json::from_str::<TopicSampleRecord>(&line.expect("sample line"))
                    .expect("sample record")
            })
            .collect::<Vec<_>>();
    assert_eq!(2, reverse_records.len());
    assert_eq!(hex(&learning_short.event_id), reverse_records[0].note_id);
    assert_eq!(hex(&evaluation_copy.event_id), reverse_records[1].note_id);
}

struct FixtureNote {
    json: String,
    event_id: [u8; 32],
    pubkey: [u8; 32],
}

fn fixture_secrets_for_both_splits(seed: &[u8; 32]) -> (u8, u8) {
    let mut learning = None;
    let mut evaluation = None;
    for secret_byte in 1_u8..=64 {
        let note = fixture_note(secret_byte, "split probe", 1_700_000_000);
        if is_evaluation_author(seed, &note.pubkey) {
            evaluation.get_or_insert(secret_byte);
        } else {
            learning.get_or_insert(secret_byte);
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

fn fixture_note(secret_byte: u8, content: &str, created_at: u64) -> FixtureNote {
    let json = NoteBuilder::new()
        .kind(1)
        .content(content)
        .created_at(created_at)
        .sign(&[secret_byte; 32])
        .build()
        .expect("sign fixture note")
        .json()
        .expect("fixture JSON");
    let value: serde_json::Value = serde_json::from_str(&json).expect("fixture value");
    FixtureNote {
        event_id: decode_hex_32(value["id"].as_str().expect("event ID")),
        pubkey: decode_hex_32(value["pubkey"].as_str().expect("pubkey")),
        json,
    }
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
