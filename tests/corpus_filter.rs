use std::collections::{BTreeMap, HashMap};
use std::fs;
use std::process::Command;
use std::thread;
use std::time::{Duration, Instant};

use nostrdb::{Config, Error as NdbError, Filter, Ndb, NoteBuilder, Transaction};
use oracle_mvp::corpus_filter::{
    CorpusFilterSummary, FrozenTokenizer, FrozenTokenizerLock, filter_corpus,
};
use sha2::{Digest, Sha256};
use tokenizers::Tokenizer;
use tokenizers::models::wordlevel::WordLevel;
use tokenizers::pre_tokenizers::whitespace::WhitespaceSplit;
use tokenizers::processors::template::TemplateProcessing;

#[test]
fn filters_both_tokenizers_across_complete_and_partial_ndb_batches() {
    let temp = tempfile::tempdir().expect("temporary directory");
    let source = open_ndb(&temp.path().join("corpus.ndb"), false);
    let filtered = open_ndb(&temp.path().join("filtered.ndb"), true);
    let pplx_dir = temp.path().join("pplx-tokenizer");
    let gte_dir = temp.path().join("gte-tokenizer");
    let mut pplx = fixture_tokenizer(&pplx_dir, "fixture/pplx", false);
    let mut gte = fixture_tokenizer(&gte_dir, "fixture/gte", true);

    let mut contents = (0..20_025)
        .map(|index| match index {
            0 | 1 => "same retained content".to_owned(),
            _ => format!("short-{index}"),
        })
        .collect::<Vec<_>>();
    contents.push(words(511));
    contents.push(words(512));
    contents.push(words(513));
    let events = contents
        .iter()
        .enumerate()
        .map(|(index, content)| signed_test_event(content, index))
        .collect::<Vec<_>>();
    for event in &events {
        submit(&source, event);
    }
    wait_for_count(&source, events.len());
    for event in events.iter().take(100) {
        submit(&filtered, event);
    }
    wait_for_count(&filtered, 100);

    let expected_summary = CorpusFilterSummary {
        scanned_events: 20_028,
        retained_events: 20_026,
        excluded_events: 2,
    };
    assert_eq!(
        filter_corpus(&source, &filtered, &mut pplx, &mut gte).expect("filter corpus"),
        expected_summary
    );
    let expected = events
        .iter()
        .filter_map(|event| {
            let value: serde_json::Value = serde_json::from_str(event).expect("fixture JSON");
            (value["content"]
                .as_str()
                .expect("fixture content")
                .split_whitespace()
                .count()
                <= 511)
                .then(|| (value["id"].as_str().expect("fixture ID").to_owned(), value))
        })
        .collect::<BTreeMap<_, _>>();
    assert_eq!(stored_events(&filtered), expected);
    assert_eq!(
        expected
            .values()
            .filter(|event| event["content"] == "same retained content")
            .count(),
        2,
        "token filtering must not perform exact-content canonicalization"
    );

    assert_eq!(
        filter_corpus(&source, &filtered, &mut pplx, &mut gte).expect("replay filter corpus"),
        expected_summary
    );
    thread::sleep(Duration::from_millis(100));
    assert_eq!(stored_events(&filtered), expected);
}

#[test]
fn frozen_tokenizer_rejects_a_changed_locked_file() {
    let temp = tempfile::tempdir().expect("tokenizer directory");
    let tokenizer_dir = temp.path().join("tokenizer");
    let lock = write_fixture_tokenizer(&tokenizer_dir, "fixture/tokenizer", false);
    fs::write(tokenizer_dir.join("tokenizer_config.json"), b"[]\n")
        .expect("tamper tokenizer config");

    let error = FrozenTokenizer::load(&tokenizer_dir, lock).expect_err("locked file mismatch");
    assert!(error.to_string().contains("checksum"));
}

#[test]
fn stage3_rejects_two_paths_resolving_to_the_same_ndb() {
    let temp = tempfile::tempdir().expect("temporary directory");
    let source_path = temp.path().join("corpus.ndb");
    drop(open_ndb(&source_path, false));
    let alias_path = temp.path().join(".").join("corpus.ndb");
    let output = Command::new(env!("CARGO_BIN_EXE_stage3_filter"))
        .arg(&source_path)
        .arg(&alias_path)
        .arg(temp.path().join("missing-pplx"))
        .arg(temp.path().join("missing-gte"))
        .output()
        .expect("run stage3_filter");

    assert!(!output.status.success());
    let stderr = String::from_utf8(output.stderr).expect("UTF-8 stderr");
    assert!(stderr.contains("must differ"), "unexpected error: {stderr}");
}

fn fixture_tokenizer(root: &std::path::Path, id: &str, add_special: bool) -> FrozenTokenizer {
    let lock = write_fixture_tokenizer(root, id, add_special);
    FrozenTokenizer::load(root, lock).expect("frozen tokenizer")
}

fn write_fixture_tokenizer(
    root: &std::path::Path,
    id: &str,
    add_special: bool,
) -> FrozenTokenizerLock {
    fs::create_dir(root).expect("create tokenizer directory");
    write_word_tokenizer(root, add_special);
    fs::write(root.join("tokenizer_config.json"), b"{}\n").expect("tokenizer config");
    FrozenTokenizerLock::from_json(&fixture_lock_json(root, id)).expect("frozen lock")
}

fn open_ndb(path: &std::path::Path, trusted_source: bool) -> Ndb {
    Ndb::new(
        path.to_str().expect("UTF-8 NostrDB path"),
        &Config::new()
            .set_mapsize(512 * 1_024 * 1_024)
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
    let deadline = Instant::now() + Duration::from_secs(10);
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
        let event: serde_json::Value =
            serde_json::from_str(&note.json().expect("stored event JSON"))
                .expect("stored event value");
        events.insert(
            event["id"].as_str().expect("stored event ID").to_owned(),
            event,
        );
        events
    })
    .expect("query NostrDB")
}

// Test infrastructure only: the production filter never creates or signs events.
fn signed_test_event(content: &str, index: usize) -> String {
    NoteBuilder::new()
        .kind(1)
        .content(content)
        .created_at(1_700_000_000 + u64::try_from(index).expect("timestamp index"))
        .sign(&[7_u8; 32])
        .build()
        .expect("signed note")
        .json()
        .expect("note JSON")
}

fn write_word_tokenizer(root: &std::path::Path, add_special: bool) {
    let vocabulary = [
        ("<unk>".to_owned(), 0),
        ("word".to_owned(), 1),
        ("<special>".to_owned(), 2),
    ]
    .into_iter()
    .collect::<HashMap<_, _>>();
    let model = WordLevel::builder()
        .vocab(vocabulary.into_iter().collect())
        .unk_token("<unk>".to_owned())
        .build()
        .expect("word-level model");
    let mut tokenizer = Tokenizer::new(model);
    tokenizer.with_pre_tokenizer(Some(WhitespaceSplit));
    if add_special {
        tokenizer.with_post_processor(Some(
            TemplateProcessing::builder()
                .try_single("$A <special>")
                .expect("single template")
                .special_tokens(vec![("<special>", 2)])
                .build()
                .expect("template processor"),
        ));
    }
    tokenizer
        .save(root.join("tokenizer.json"), false)
        .expect("save tokenizer");
}

fn fixture_lock_json(root: &std::path::Path, id: &str) -> String {
    let tokenizer = root.join("tokenizer.json");
    let config = root.join("tokenizer_config.json");
    serde_json::to_string_pretty(&serde_json::json!({
        "schema_version": 1,
        "tokenizer_id": id,
        "models": [],
        "configured_input_tokens": 512,
        "input_rule": "raw-utf8-empty-unchanged-add-special-tokens-no-truncation-no-padding-v1",
        "token_length_rule": "tokenizer-output-ids-before-model-truncation-v1",
        "empty_input": { "strategy": "unchanged" },
        "files": [
            {
                "path": "tokenizer.json",
                "bytes": fs::metadata(&tokenizer).expect("tokenizer metadata").len(),
                "sha256": sha256_file(&tokenizer),
            },
            {
                "path": "tokenizer_config.json",
                "bytes": fs::metadata(&config).expect("config metadata").len(),
                "sha256": sha256_file(&config),
            },
        ],
    }))
    .expect("lock JSON")
}

fn sha256_file(path: &std::path::Path) -> String {
    format!("{:x}", Sha256::digest(fs::read(path).expect("hash input")))
}

fn words(count: usize) -> String {
    std::iter::repeat_n("word", count)
        .collect::<Vec<_>>()
        .join(" ")
}
