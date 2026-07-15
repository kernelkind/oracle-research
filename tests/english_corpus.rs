use std::collections::BTreeMap;
use std::fs;
use std::path::Path;
use std::thread;
use std::time::{Duration, Instant};

use fasttext::{FastText, args::Args};
use nostrdb::{Config, Error as NdbError, Filter, Ndb, NoteBuilder, Transaction};
use oracle_mvp::english_corpus::{
    EnglishCorpusManifest, EnglishModelLock, FrozenEnglishClassifier, build_english_corpus,
};
use oracle_mvp::english_filter::ClassifierDecision;
use sha2::{Digest, Sha256};

#[test]
fn builds_the_ordered_english_eligible_corpus_without_changing_source_events() {
    let temp = tempfile::tempdir().expect("temporary directory");
    let source_directory = temp.path().join("deduplicated");
    let source_path = source_directory.join("ndb");
    fs::create_dir(&source_directory).expect("source directory");
    let source = open_ndb(&source_path, false);

    let english = signed_test_event("english rust code https://example.com", 1);
    let neutral_empty = signed_test_event("https://example.com/path?q=1", 2);
    let neutral_label = signed_test_event("terminal command code bytes", 3);
    let non_english = signed_test_event("hola mundo espanol", 4);
    let events = [english, neutral_empty, neutral_label, non_english];
    for event in &events {
        submit(&source, event);
    }
    wait_for_count(&source, events.len());
    drop(source);

    let ids = events
        .iter()
        .map(|event| event_id(event))
        .collect::<Vec<_>>();
    let source_order = [ids[3], ids[1], ids[0], ids[2]];
    let ordered_path = source_directory.join("ordered-event-ids.bin");
    fs::write(
        &ordered_path,
        source_order.iter().flatten().copied().collect::<Vec<_>>(),
    )
    .expect("ordered source IDs");
    write_ordered_checksum(&ordered_path);

    let (model_path, lock) = fixture_model(temp.path());
    let classifier = FrozenEnglishClassifier::load(&model_path, lock).expect("frozen classifier");
    assert_eq!(
        classifier.classify_content("english rust code https://example.com"),
        ClassifierDecision::KeepEnglish
    );
    assert_eq!(
        classifier.classify_content("https://example.com/path?q=1"),
        ClassifierDecision::KeepLanguageNeutral
    );
    assert_eq!(
        classifier.classify_content("terminal command code bytes"),
        ClassifierDecision::KeepLanguageNeutral
    );
    assert_eq!(
        classifier.classify_content("hola mundo espanol"),
        ClassifierDecision::Exclude
    );

    let output = temp.path().join("english-eligible");
    let manifest =
        build_english_corpus(&source_directory, &output, &classifier).expect("English corpus");

    assert_eq!(manifest.input_events, 4);
    assert_eq!(manifest.retained_events, 3);
    assert_eq!(manifest.excluded_events, 1);
    assert_eq!(
        manifest.source_ordered_event_ids_sha256,
        sha256_file(&ordered_path)
    );
    assert_eq!(
        manifest.output_ordered_event_ids_sha256,
        sha256_file(&output.join("ordered-event-ids.bin"))
    );
    assert_eq!(
        serde_json::from_slice::<EnglishCorpusManifest>(
            &fs::read(output.join("manifest.json")).expect("manifest")
        )
        .expect("manifest JSON"),
        manifest
    );
    assert_eq!(
        read_ids(&output.join("ordered-event-ids.bin")),
        [ids[1], ids[0], ids[2]]
    );

    let expected = events[..3]
        .iter()
        .map(|event| event_value(event))
        .map(|event| (event["id"].as_str().expect("event ID").to_owned(), event))
        .collect::<BTreeMap<_, _>>();
    assert_eq!(
        stored_events(&open_ndb(&output.join("ndb"), true)),
        expected
    );
    assert_eq!(
        stored_events(&open_ndb(&source_path, true)),
        events
            .iter()
            .map(|event| event_value(event))
            .map(|event| (event["id"].as_str().expect("event ID").to_owned(), event))
            .collect(),
        "the source NostrDB must remain unchanged"
    );
}

#[test]
fn rejects_a_changed_source_order_before_publishing_output() {
    let temp = tempfile::tempdir().expect("temporary directory");
    let source_directory = temp.path().join("deduplicated");
    let source_path = source_directory.join("ndb");
    fs::create_dir(&source_directory).expect("source directory");
    let source = open_ndb(&source_path, false);
    let event = signed_test_event("english rust code", 1);
    submit(&source, &event);
    wait_for_count(&source, 1);
    drop(source);

    fs::write(
        source_directory.join("ordered-event-ids.bin"),
        event_id(&event),
    )
    .expect("ordered source ID");
    fs::write(
        source_directory.join("ordered-event-ids.sha256"),
        format!("{}  ordered-event-ids.bin\n", "0".repeat(64)),
    )
    .expect("wrong source checksum");

    let (model_path, lock) = fixture_model(temp.path());
    let classifier = FrozenEnglishClassifier::load(&model_path, lock).expect("frozen classifier");
    let output = temp.path().join("english-eligible");
    let error = build_english_corpus(&source_directory, &output, &classifier)
        .expect_err("changed source order must be rejected");

    assert!(error.to_string().contains("checksum"));
    assert!(!output.exists(), "invalid input must not be published");
    assert!(
        !temp.path().join(".english-eligible.partial").exists(),
        "invalid input must not leave a partial build"
    );
}

fn fixture_model(root: &Path) -> (std::path::PathBuf, EnglishModelLock) {
    let training_path = root.join("language-training.txt");
    let mut training = String::new();
    for _ in 0..100 {
        training.push_str("__label__eng_Latn english rust code\n");
        training.push_str("__label__zxx_Latn terminal command code bytes\n");
        training.push_str("__label__spa_Latn hola mundo espanol\n");
    }
    fs::write(&training_path, training).expect("training data");

    let mut args = Args {
        input: training_path,
        output: Path::new("/dev/null").to_owned(),
        ..Args::default()
    };
    args.apply_supervised_defaults();
    args.dim = 16;
    args.epoch = 100;
    args.bucket = 0;
    args.thread = 1;
    args.verbose = 0;
    args.seed = 42;
    let model = FastText::train(args).expect("train fixture classifier");
    let model_path = root.join("fixture-language-model.bin");
    model.save_model(&model_path).expect("save fixture model");
    let lock = EnglishModelLock::new(sha256_file(&model_path), "fixture-revision")
        .expect("fixture model lock");
    (model_path, lock)
}

fn open_ndb(path: &Path, trusted_source: bool) -> Ndb {
    Ndb::new(
        path.to_str().expect("UTF-8 NostrDB path"),
        &Config::new()
            .set_flags((1 << 2) | (1 << 3) | (1 << 4))
            .set_mapsize(512 * 1_024 * 1_024)
            .skip_validation(trusted_source)
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
        if stored_events(ndb).len() == expected {
            return;
        }
        assert!(Instant::now() < deadline, "timed out waiting for notes");
        thread::sleep(Duration::from_millis(10));
    }
}

fn stored_events(ndb: &Ndb) -> BTreeMap<String, serde_json::Value> {
    let txn = Transaction::new(ndb).expect("read transaction");
    let all = Filter::new().build();
    ndb.fold(&txn, &[all], BTreeMap::new(), |mut events, note| {
        let event: serde_json::Value =
            serde_json::from_str(&note.json().expect("event JSON")).expect("event value");
        events.insert(event["id"].as_str().expect("event ID").to_owned(), event);
        events
    })
    .expect("scan NostrDB")
}

fn event_value(event: &str) -> serde_json::Value {
    serde_json::from_str(event).expect("signed event JSON")
}

fn event_id(event: &str) -> [u8; 32] {
    let value = event_value(event);
    let hex = value["id"].as_str().expect("event ID");
    let mut id = [0_u8; 32];
    for (index, bytes) in hex.as_bytes().chunks_exact(2).enumerate() {
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

fn read_ids(path: &Path) -> Vec<[u8; 32]> {
    let bytes = fs::read(path).expect("ordered event IDs");
    let mut records = bytes.chunks_exact(32);
    let ids = records
        .by_ref()
        .map(|record| record.try_into().expect("event ID width"))
        .collect();
    assert!(records.remainder().is_empty(), "partial event ID");
    ids
}

fn sha256_file(path: &Path) -> String {
    format!("{:x}", Sha256::digest(fs::read(path).expect("hash input")))
}

fn write_ordered_checksum(path: &Path) {
    fs::write(
        path.with_file_name("ordered-event-ids.sha256"),
        format!("{}  ordered-event-ids.bin\n", sha256_file(path)),
    )
    .expect("ordered source checksum");
}

// Test infrastructure only: production code only copies existing signed events.
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
