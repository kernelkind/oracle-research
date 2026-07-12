use std::fs::{self, File};
use std::io::{BufWriter, Write};
use std::process::Command;

use nostrdb::{Config, Filter, Ndb, NoteBuilder, Transaction};
use oracle_mvp::snapshot::{CorpusManifest, DamusSnapshot, SourceManifest};

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
fn build_command_publishes_both_database_artifacts() {
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
    assert!(pipeline.layout().source_db().is_dir());
    assert!(pipeline.layout().corpus_db().is_dir());
}

fn signed_note(kind: u32, content: &str, tags: &[[&str; 4]]) -> String {
    let secret = [7; 32];
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
