use std::fs::{self, File};
use std::io::{BufWriter, Write};
use std::process::Command;

use nostrdb::{Config, Filter, Ndb, NoteBuilder, Transaction};
use oracle_mvp::snapshot::{CanonicalManifest, CorpusManifest, DamusSnapshot, SourceManifest};
use sha2::{Digest, Sha256};

#[test]
fn imports_validated_source_and_derives_eligible_corpus() {
    let temp = tempfile::tempdir().expect("temporary directory");
    let root = temp.path().join("damus_snapshot");
    let pipeline = DamusSnapshot::new(&root);
    fs::create_dir_all(pipeline.layout().snapshot().parent().expect("input parent"))
        .expect("create input directory");

    let eligible_url = signed_note(1, "read https://example.com", &[]);
    let eligible_plain = signed_note(1, "plain root note", &[]);
    let reply = signed_note(1, "reply", &[["e", &"11".repeat(32), "", "reply"]]);
    let quote = signed_note(1, "quote", &[["q", &"22".repeat(32), "", ""]]);
    let legacy_quote = signed_note(1, "legacy quote", &[["e", &"33".repeat(32), "", "mention"]]);
    let metadata = signed_note(0, "{}", &[]);
    let embedded_root = signed_note(1, "root recovered from repost content", &[]);
    let repost = signed_note(6, &embedded_root, &[]);
    let tampered = eligible_plain.replace("plain root note", "invalid signature");

    write_snapshot(
        pipeline.layout().snapshot(),
        &[
            &eligible_url,
            &eligible_plain,
            &reply,
            &quote,
            &legacy_quote,
            &metadata,
            &repost,
            &eligible_url,
            &tampered,
        ],
    );

    let source = pipeline.import_source().expect("source import");
    assert_eq!(
        source.counts,
        oracle_mvp::snapshot::SourceCounts {
            snapshot_records: 9,
            stored_events: 8,
        }
    );
    assert_manifest::<SourceManifest>(pipeline.layout().source_manifest(), &source);

    let corpus = pipeline.derive_corpus().expect("corpus derivation");
    assert_eq!(
        corpus,
        CorpusManifest {
            schema_version: 1,
            source_snapshot_sha256: source.snapshot_sha256,
            rejections: oracle_mvp::snapshot::EligibilityRejections {
                non_kind_1: 2,
                replies: 1,
                quotes: 2,
            },
            eligible_events: 3,
        }
    );
    assert_manifest::<CorpusManifest>(pipeline.layout().corpus_manifest(), &corpus);

    let ndb = open_ndb(pipeline.layout().corpus_db());
    let txn = Transaction::new(&ndb).expect("corpus transaction");
    let kind_one = Filter::new().kinds([1]).build();
    let contents = ndb
        .fold(&txn, &[kind_one], Vec::new(), |mut contents, note| {
            contents.push(note.content().to_owned());
            contents
        })
        .expect("query corpus");
    assert_eq!(contents.len(), 3);
    assert!(contents.iter().any(|content| content == "plain root note"));
    assert!(
        contents
            .iter()
            .any(|content| content == "read https://example.com")
    );
    assert!(
        contents
            .iter()
            .any(|content| content == "root recovered from repost content")
    );
}

#[test]
fn build_command_publishes_all_pipeline_artifacts() {
    let temp = tempfile::tempdir().expect("temporary directory");
    let root = temp.path().join("damus_snapshot");
    let pipeline = DamusSnapshot::new(&root);
    fs::create_dir_all(pipeline.layout().snapshot().parent().expect("input parent"))
        .expect("create input directory");
    let eligible = signed_note(1, "one eligible event", &[]);
    write_snapshot(pipeline.layout().snapshot(), &[&eligible]);

    let output = Command::new(env!("CARGO_BIN_EXE_oracle-mvp"))
        .arg("build")
        .arg(&root)
        .output()
        .expect("run oracle-mvp");

    assert!(
        output.status.success(),
        "stderr: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let result: serde_json::Value =
        serde_json::from_slice(&output.stdout).expect("command result JSON");
    assert_eq!(result["source"]["counts"]["stored_events"], 1);
    assert_eq!(result["corpus"]["eligible_events"], 1);
    assert_eq!(result["canonical"]["counts"]["canonical_rows"], 1);
    assert!(pipeline.layout().source_db().is_dir());
    assert!(pipeline.layout().corpus_db().is_dir());
    assert!(pipeline.layout().canonical_rows().is_file());
    assert!(pipeline.layout().canonical_aliases().is_file());
}

#[test]
fn canonicalizes_exact_content_and_orders_rows_independently_of_ingestion_order() {
    let duplicate_a = signed_note_at(1, "same content", &[], 1_700_000_101, 1);
    let duplicate_b = signed_note_at(1, "same content", &[], 1_700_000_102, 2);
    let unique_a = signed_note_at(1, "unique alpha", &[], 1_700_000_103, 3);
    let unique_b = signed_note_at(1, "unique beta", &[], 1_700_000_104, 4);
    let events = [&duplicate_a, &duplicate_b, &unique_a, &unique_b];

    let first = canonicalize_fixture(&events);
    let reversed = canonicalize_fixture(&events.into_iter().rev().collect::<Vec<_>>());

    assert_ne!(
        first.manifest.source_snapshot_sha256,
        reversed.manifest.source_snapshot_sha256
    );
    assert_eq!(first.manifest.counts, reversed.manifest.counts);
    assert_eq!(first.manifest.rows, reversed.manifest.rows);
    assert_eq!(first.manifest.aliases, reversed.manifest.aliases);
    assert_eq!(first.rows, reversed.rows);
    assert_eq!(first.aliases, reversed.aliases);
    assert_eq!(
        first.manifest,
        CanonicalManifest {
            schema_version: 1,
            source_snapshot_sha256: first.manifest.source_snapshot_sha256.clone(),
            content_rule: "byte-identical-utf8-v1".to_owned(),
            canonical_event_rule: "lowest-event-id-v1".to_owned(),
            row_order_rule: "sha256-domain-separated-event-id-v1".to_owned(),
            counts: oracle_mvp::snapshot::CanonicalCounts {
                eligible_events: 4,
                canonical_rows: 3,
                duplicate_events: 1,
            },
            rows: first.manifest.rows.clone(),
            aliases: first.manifest.aliases.clone(),
        }
    );
    assert_eq!(first.manifest.rows.record_bytes, 32);
    assert_eq!(first.manifest.rows.records, 3);
    assert_eq!(first.manifest.rows.bytes, 96);
    assert_eq!(first.manifest.aliases.record_bytes, 64);
    assert_eq!(first.manifest.aliases.records, 4);
    assert_eq!(first.manifest.aliases.bytes, 256);

    let duplicate_ids = [event_id(&duplicate_a), event_id(&duplicate_b)];
    let canonical_duplicate = *duplicate_ids.iter().min().expect("duplicate ID");
    let mut expected_aliases = vec![
        (duplicate_ids[0], canonical_duplicate),
        (duplicate_ids[1], canonical_duplicate),
        (event_id(&unique_a), event_id(&unique_a)),
        (event_id(&unique_b), event_id(&unique_b)),
    ];
    expected_aliases.sort_unstable();
    assert_eq!(decode_aliases(&first.aliases), expected_aliases);

    let mut expected_rows = vec![
        canonical_duplicate,
        event_id(&unique_a),
        event_id(&unique_b),
    ];
    expected_rows.sort_unstable_by_key(row_order_key);
    assert_eq!(decode_rows(&first.rows), expected_rows);
}

struct CanonicalFixture {
    manifest: CanonicalManifest,
    rows: Vec<u8>,
    aliases: Vec<u8>,
}

fn canonicalize_fixture(events: &[&String]) -> CanonicalFixture {
    let temp = tempfile::tempdir().expect("temporary directory");
    let root = temp.path().join("damus_snapshot");
    let pipeline = DamusSnapshot::new(&root);
    fs::create_dir_all(pipeline.layout().snapshot().parent().expect("input parent"))
        .expect("create input directory");
    write_snapshot(
        pipeline.layout().snapshot(),
        &events
            .iter()
            .map(|event| event.as_str())
            .collect::<Vec<_>>(),
    );
    pipeline.import_source().expect("source import");
    pipeline.derive_corpus().expect("corpus derivation");
    let manifest = pipeline
        .canonicalize_corpus()
        .expect("corpus canonicalization");
    assert_manifest::<CanonicalManifest>(pipeline.layout().canonical_manifest(), &manifest);
    CanonicalFixture {
        rows: fs::read(pipeline.layout().canonical_rows()).expect("canonical rows"),
        aliases: fs::read(pipeline.layout().canonical_aliases()).expect("canonical aliases"),
        manifest,
    }
}

fn signed_note(kind: u32, content: &str, tags: &[[&str; 4]]) -> String {
    signed_note_at(kind, content, tags, 1_700_000_000 + u64::from(kind), 7)
}

fn signed_note_at(
    kind: u32,
    content: &str,
    tags: &[[&str; 4]],
    created_at: u64,
    secret_byte: u8,
) -> String {
    let secret = [secret_byte; 32];
    let mut builder = NoteBuilder::new()
        .kind(kind)
        .content(content)
        .created_at(created_at);
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

fn event_id(event: &str) -> [u8; 32] {
    let value: serde_json::Value = serde_json::from_str(event).expect("event JSON");
    let hex = value["id"].as_str().expect("event ID");
    let mut id = [0_u8; 32];
    for (index, byte) in id.iter_mut().enumerate() {
        *byte = u8::from_str_radix(&hex[index * 2..index * 2 + 2], 16).expect("hex event ID");
    }
    id
}

fn row_order_key(id: &[u8; 32]) -> [u8; 32] {
    let mut hasher = Sha256::new();
    hasher.update(b"oracle-mvp/canonical-row-order/v1\0");
    hasher.update(id);
    hasher.finalize().into()
}

fn decode_rows(bytes: &[u8]) -> Vec<[u8; 32]> {
    bytes
        .chunks_exact(32)
        .map(|record| record.try_into().expect("row record"))
        .collect()
}

fn decode_aliases(bytes: &[u8]) -> Vec<([u8; 32], [u8; 32])> {
    bytes
        .chunks_exact(64)
        .map(|record| {
            (
                record[..32].try_into().expect("alias ID"),
                record[32..].try_into().expect("canonical ID"),
            )
        })
        .collect()
}

fn write_snapshot(path: impl AsRef<std::path::Path>, events: &[&str]) {
    let file = File::create(path).expect("snapshot file");
    let encoder =
        zstd::stream::write::Encoder::new(BufWriter::new(file), 1).expect("zstd snapshot encoder");
    let mut writer = encoder.auto_finish();
    for event in events {
        writeln!(writer, "{event}").expect("write snapshot event");
    }
    writer.flush().expect("flush snapshot");
}

fn assert_manifest<T>(path: impl AsRef<std::path::Path>, expected: &T)
where
    T: serde::de::DeserializeOwned + PartialEq + std::fmt::Debug,
{
    let manifest = fs::read(path).expect("manifest file");
    let actual = serde_json::from_slice::<T>(&manifest).expect("manifest JSON");
    assert_eq!(&actual, expected);
}

fn open_ndb(path: impl AsRef<std::path::Path>) -> Ndb {
    Ndb::new(
        path.as_ref().to_str().expect("UTF-8 NostrDB path"),
        &Config::new().set_mapsize(512 * 1024 * 1024),
    )
    .expect("open NostrDB")
}
