use std::collections::BTreeMap;
use std::thread;
use std::time::{Duration, Instant};

use nostrdb::{Config, Error, Filter, Ndb, NoteBuilder, Transaction};
use oracle_mvp::corpus_derivation::derive_corpus;

#[test]
fn streams_only_root_non_quote_kind_one_notes_into_corpus() {
    let temp = tempfile::tempdir().expect("temporary directory");
    let source_path = temp.path().join("source.ndb");
    let corpus_path = temp.path().join("corpus.ndb");
    let source = open_ndb(&source_path);
    let corpus = open_ndb(&corpus_path);

    let event_id = "11".repeat(32);
    let plain_root = signed_test_event(1, "plain root", &[]);
    let url_root = signed_test_event(1, "root with URL https://example.com", &[]);
    let events = [
        plain_root.clone(),
        url_root.clone(),
        signed_test_event(1, "marked reply", &[["e", &event_id, "", "reply"]]),
        signed_test_event(1, "reply to root", &[["e", &event_id, "", "root"]]),
        signed_test_event(1, "legacy reply", &[["e", &event_id, "", ""]]),
        signed_test_event(1, "NIP-18 quote", &[["q", &event_id, "", ""]]),
        signed_test_event(1, "legacy quote", &[["e", &event_id, "", "mention"]]),
        signed_test_event(0, "profile metadata", &[]),
    ];

    for event in &events {
        submit(&source, event);
    }
    wait_for_count(&source, events.len());

    derive_corpus(&source, &corpus).expect("derive corpus");
    wait_for_count(&corpus, 2);
    derive_corpus(&source, &corpus).expect("replay corpus derivation");
    wait_for_count(&corpus, 2);

    let txn = Transaction::new(&corpus).expect("corpus transaction");
    let all = Filter::new().build();
    let events = corpus
        .fold(&txn, &[all], BTreeMap::new(), |mut events, note| {
            let event: serde_json::Value =
                serde_json::from_str(&note.json().expect("stored event JSON"))
                    .expect("stored event value");
            events.insert(
                event["id"].as_str().expect("stored event ID").to_owned(),
                event,
            );
            events
        })
        .expect("query corpus");

    let expected = [plain_root, url_root]
        .into_iter()
        .map(|event| {
            let event: serde_json::Value = serde_json::from_str(&event).expect("fixture event");
            (
                event["id"].as_str().expect("fixture event ID").to_owned(),
                event,
            )
        })
        .collect();
    assert_eq!(events, expected);
}

fn open_ndb(path: &std::path::Path) -> Ndb {
    Ndb::new(
        path.to_str().expect("UTF-8 NostrDB path"),
        &Config::new().set_mapsize(512 * 1024 * 1024),
    )
    .expect("open NostrDB")
}

fn submit(ndb: &Ndb, event: &str) {
    loop {
        match ndb.process_event(event) {
            Ok(()) => return,
            Err(Error::NoteProcessFailed) => thread::sleep(Duration::from_millis(10)),
            Err(error) => panic!("submit event: {error}"),
        }
    }
}

fn wait_for_count(ndb: &Ndb, expected: usize) {
    let deadline = Instant::now() + Duration::from_secs(5);
    loop {
        let txn = Transaction::new(ndb).expect("count transaction");
        let all = Filter::new().build();
        let count = ndb
            .fold(&txn, &[all], 0_usize, |count, _| count + 1)
            .expect("count notes");
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

// Test infrastructure only: NostrDB rejects fixtures whose event ID or signature is invalid.
// The production corpus-derivation path never creates or signs events.
fn signed_test_event(kind: u32, content: &str, tags: &[[&str; 4]]) -> String {
    let secret = [7_u8; 32];
    let mut builder = NoteBuilder::new()
        .kind(kind)
        .content(content)
        .created_at(1_700_000_000 + u64::from(kind));
    for tag in tags {
        builder = builder
            .start_tag()
            .tag_str(tag[0])
            .tag_str(tag[1])
            .tag_str(tag[2])
            .tag_str(tag[3]);
    }
    builder
        .sign(&secret)
        .build()
        .expect("signed note")
        .json()
        .expect("note JSON")
}
