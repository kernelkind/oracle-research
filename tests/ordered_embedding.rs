use std::fs::{self, File};
use std::io::Write;
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::{Duration, Instant};

use nostrdb::{Config, Filter, Ndb, NoteBuilder, Transaction};
use oracle_mvp::embedding::{EmbeddingEncoder, EncoderDescriptor};
use oracle_mvp::ordered_embedding::{
    OrderedEmbeddingBuildConfig, build_ordered_embeddings, extend_ordered_embeddings,
    open_ordered_embedding_artifact,
};

#[test]
fn embeds_an_exact_ordered_prefix_and_extends_without_reencoding_it() {
    let temp = tempfile::tempdir().expect("temporary directory");
    let ndb_path = temp.path().join("deduplicated.ndb");
    let ndb = open_ndb(&ndb_path);
    let events = (0..6)
        .map(|index| signed_event(&format!("note-{index}"), index))
        .collect::<Vec<_>>();
    for event in &events {
        ndb.process_event(event).expect("submit event");
    }
    wait_for_count(&ndb, events.len());
    drop(ndb);

    let mut ordered = events
        .iter()
        .map(|event| event_id(event))
        .collect::<Vec<_>>();
    ordered.reverse();
    let ordered_path = temp.path().join("ordered-event-ids.bin");
    write_ids(&ordered_path, &ordered);

    let first_artifact = temp.path().join("first-four");
    let first_seen = Arc::new(Mutex::new(Vec::new()));
    let first = build_ordered_embeddings(
        &ndb_path,
        &ordered_path,
        &first_artifact,
        &OrderedEmbeddingBuildConfig {
            rows: 4,
            batch_size: 2,
            shard_rows: 2,
        },
        &mut RecordingEncoder::new(first_seen.clone()),
    )
    .expect("build first prefix");
    assert_eq!(first.manifest.total_rows, 4);
    assert_eq!(first.encoded_rows, 4);
    assert_eq!(
        read_artifact_ids(&first_artifact, &first.manifest),
        ordered[..4]
    );
    assert_eq!(
        *first_seen.lock().expect("first seen lock"),
        vec!["note-5", "note-4", "note-3", "note-2"]
    );
    assert_eq!(
        open_ordered_embedding_artifact(&ndb_path, &ordered_path, &first_artifact)
            .expect("reopen first artifact"),
        first.manifest
    );
    let first_vectors =
        fs::read(first_artifact.join("shards/000000/vectors.i8")).expect("first vectors");

    let extended_artifact = temp.path().join("all-six");
    let extension_seen = Arc::new(Mutex::new(Vec::new()));
    let extended = extend_ordered_embeddings(
        &ndb_path,
        &ordered_path,
        &first_artifact,
        &extended_artifact,
        &OrderedEmbeddingBuildConfig {
            rows: 6,
            batch_size: 2,
            shard_rows: 2,
        },
        &mut RecordingEncoder::new(extension_seen.clone()),
    )
    .expect("extend prefix");
    assert_eq!(extended.manifest.total_rows, 6);
    assert_eq!(extended.encoded_rows, 2);
    assert_eq!(
        read_artifact_ids(&extended_artifact, &extended.manifest),
        ordered
    );
    assert_eq!(
        *extension_seen.lock().expect("extension seen lock"),
        vec!["note-1", "note-0"]
    );
    assert_eq!(
        fs::read(extended_artifact.join("shards/000000/vectors.i8"))
            .expect("extended first vectors"),
        first_vectors
    );
    fs::remove_dir_all(&first_artifact).expect("remove base artifact");
    open_ordered_embedding_artifact(&ndb_path, &ordered_path, &extended_artifact)
        .expect("extended artifact is self-contained");

    let mut corrupt_manifest = extended.manifest;
    corrupt_manifest.shards[0].effective_tokens = 0;
    fs::write(
        extended_artifact.join("manifest.json"),
        serde_json::to_vec_pretty(&corrupt_manifest).expect("encode corrupt manifest"),
    )
    .expect("write corrupt manifest");
    open_ordered_embedding_artifact(&ndb_path, &ordered_path, &extended_artifact)
        .expect_err("invalid effective-token metadata must be rejected");
}

fn open_ndb(path: &std::path::Path) -> Ndb {
    Ndb::new(
        path.to_str().expect("UTF-8 NostrDB path"),
        &Config::new().set_mapsize(2 * 1_024 * 1_024 * 1_024),
    )
    .expect("open NostrDB")
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
        assert!(Instant::now() < deadline, "NostrDB persistence timeout");
        thread::sleep(Duration::from_millis(10));
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

fn event_id(event: &str) -> [u8; 32] {
    let value: serde_json::Value = serde_json::from_str(event).expect("event value");
    decode_id(value["id"].as_str().expect("event ID"))
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

fn write_ids(path: &std::path::Path, ids: &[[u8; 32]]) {
    let mut file = File::create(path).expect("ordered ID file");
    for id in ids {
        file.write_all(id).expect("ordered ID");
    }
    file.sync_all().expect("sync ordered IDs");
}

fn read_artifact_ids(
    artifact: &std::path::Path,
    manifest: &oracle_mvp::ordered_embedding::OrderedEmbeddingManifest,
) -> Vec<[u8; 32]> {
    manifest
        .shards
        .iter()
        .flat_map(|shard| {
            fs::read(artifact.join(&shard.row_ids.file))
                .expect("row IDs")
                .chunks_exact(32)
                .map(|bytes| bytes.try_into().expect("event ID width"))
                .collect::<Vec<_>>()
        })
        .collect()
}

struct RecordingEncoder {
    descriptor: EncoderDescriptor,
    seen: Arc<Mutex<Vec<String>>>,
}

impl RecordingEncoder {
    fn new(seen: Arc<Mutex<Vec<String>>>) -> Self {
        Self {
            descriptor: EncoderDescriptor {
                model_id: "fixture-encoder".to_owned(),
                model_revision: "fixture-revision".to_owned(),
                model_lock_sha256: "fixture-lock".to_owned(),
                runtime: "fixture-runtime".to_owned(),
                runtime_version: "fixture-runtime-version".to_owned(),
                runtime_sha256: "fixture-runtime-sha".to_owned(),
                execution_provider: "cpu".to_owned(),
                output_name: "fixture-output".to_owned(),
                dimensions: 4,
                max_tokens: 512,
                input_rule: "fixture-input".to_owned(),
                pooling: "fixture-pooling".to_owned(),
                quantization: "native-int8".to_owned(),
                instruction: None,
            },
            seen,
        }
    }
}

impl EmbeddingEncoder for RecordingEncoder {
    fn descriptor(&self) -> &EncoderDescriptor {
        &self.descriptor
    }

    fn effective_token_lengths(
        &mut self,
        texts: &[&str],
    ) -> oracle_mvp::snapshot::Result<Vec<u32>> {
        Ok(texts
            .iter()
            .map(|text| u32::try_from(text.len()).expect("fixture length"))
            .collect())
    }

    fn encode(&mut self, texts: &[&str]) -> oracle_mvp::snapshot::Result<Vec<i8>> {
        self.seen
            .lock()
            .expect("seen lock")
            .extend(texts.iter().map(|text| (*text).to_owned()));
        Ok(texts
            .iter()
            .flat_map(|text| {
                let value = i8::try_from(text.as_bytes()[5] - b'0' + 1).expect("fixture vector");
                [value, value, value, value]
            })
            .collect())
    }
}
