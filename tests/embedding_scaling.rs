use std::collections::BTreeMap;
use std::fs::{self, File};
use std::io::{BufWriter, Write};
use std::sync::{Arc, Mutex};

use nostrdb::NoteBuilder;
use oracle_mvp::embedding::{EmbeddingBuildConfig, EmbeddingEncoder, EncoderDescriptor};
use oracle_mvp::snapshot::{CanonicalManifest, CorpusManifest, DamusSnapshot, Error, Result};
use oracle_mvp::stage::CorpusStageConfig;

#[test]
fn interrupted_embedding_resumes_after_verified_complete_shards() {
    let fixture = Fixture::new(&["one", "two two", "three three three", "four", "five"]);
    let config = EmbeddingBuildConfig {
        artifact_name: "resumable".to_owned(),
        batch_size: 2,
        shard_rows: 2,
    };
    let seen_before_failure = Arc::new(Mutex::new(Vec::new()));
    let mut failing = RecordingEncoder::new(4, seen_before_failure.clone()).fail_after_calls(1);
    let error = fixture
        .pipeline
        .embed_canonical_corpus(&config, &mut failing)
        .expect_err("second shard fails after the first shard is durable");
    assert!(error.to_string().contains("deliberate fixture failure"));
    assert_eq!(seen_before_failure.lock().expect("seen lock").len(), 2);

    let resumed_seen = Arc::new(Mutex::new(Vec::new()));
    let mut resumed = RecordingEncoder::new(4, resumed_seen.clone());
    let manifest = fixture
        .pipeline
        .embed_canonical_corpus(&config, &mut resumed)
        .expect("resume the matching incomplete artifact");
    assert_eq!(manifest.total_rows, 5);
    assert_eq!(manifest.shards.len(), 3);
    assert_eq!(resumed_seen.lock().expect("seen lock").len(), 3);
    assert_eq!(
        fixture
            .pipeline
            .open_embedding_artifact(&config.artifact_name)
            .expect("verify resumed artifact"),
        manifest
    );
}

#[test]
fn resume_rejects_malformed_noncheckpoint_entries() {
    let fixture = Fixture::new(&["one", "two", "three"]);
    let config = EmbeddingBuildConfig {
        artifact_name: "malformed-checkpoint".to_owned(),
        batch_size: 2,
        shard_rows: 2,
    };
    fixture
        .pipeline
        .embed_canonical_corpus(
            &config,
            &mut RecordingEncoder::new(4, Arc::new(Mutex::new(Vec::new()))).fail_after_calls(1),
        )
        .expect_err("leave one durable shard");
    let shard_root = fixture
        .pipeline
        .layout()
        .root()
        .join("work/embedding-malformed-checkpoint/shards");
    fs::create_dir(shard_root.join("00000")).expect("malformed lower lexical name");

    let error = fixture
        .pipeline
        .embed_canonical_corpus(
            &config,
            &mut RecordingEncoder::new(4, Arc::new(Mutex::new(Vec::new()))),
        )
        .expect_err("malformed checkpoint must not be ignored");
    assert!(error.to_string().contains("unexpected shard `00000`"));
}

#[test]
fn resume_rejects_a_corrupted_completed_checkpoint() {
    let fixture = Fixture::new(&["one", "two", "three", "four"]);
    let config = EmbeddingBuildConfig {
        artifact_name: "corrupted-resume".to_owned(),
        batch_size: 2,
        shard_rows: 2,
    };
    let mut failing =
        RecordingEncoder::new(4, Arc::new(Mutex::new(Vec::new()))).fail_after_calls(1);
    fixture
        .pipeline
        .embed_canonical_corpus(&config, &mut failing)
        .expect_err("leave one completed shard");

    let vectors = fixture
        .pipeline
        .layout()
        .root()
        .join("work/embedding-corrupted-resume/shards/000000/vectors.i8");
    let mut bytes = fs::read(&vectors).expect("completed checkpoint vectors");
    bytes[0] ^= 1;
    fs::write(&vectors, bytes).expect("corrupt completed checkpoint");

    let error = fixture
        .pipeline
        .embed_canonical_corpus(
            &config,
            &mut RecordingEncoder::new(4, Arc::new(Mutex::new(Vec::new()))),
        )
        .expect_err("resume must verify completed shards before trusting them");
    assert!(error.to_string().contains("metadata"));
}

#[test]
fn canonical_embedding_rejects_incompatible_canonical_rules_before_encoding() {
    let fixture = Fixture::new(&["one", "two"]);
    let path = fixture.pipeline.layout().canonical_manifest();
    let mut manifest: CanonicalManifest =
        serde_json::from_slice(&fs::read(&path).expect("canonical manifest"))
            .expect("canonical manifest JSON");
    manifest.content_rule = "forged-content-rule".to_owned();
    fs::write(
        &path,
        serde_json::to_vec_pretty(&manifest).expect("serialize forged canonical manifest"),
    )
    .expect("write forged canonical manifest");

    let seen = Arc::new(Mutex::new(Vec::new()));
    let error = fixture
        .pipeline
        .embed_canonical_corpus(
            &EmbeddingBuildConfig {
                artifact_name: "invalid-canonical-rules".to_owned(),
                batch_size: 2,
                shard_rows: 2,
            },
            &mut RecordingEncoder::new(4, seen.clone()),
        )
        .expect_err("embedding must verify canonical rules");
    assert!(error.to_string().contains("canonical manifest"));
    assert!(seen.lock().expect("seen lock").is_empty());
}

#[test]
fn canonical_embedding_rejects_a_different_corpus_contract_before_encoding() {
    let fixture = Fixture::new(&["one", "two"]);
    let path = fixture.pipeline.layout().corpus_manifest();
    let mut manifest: CorpusManifest =
        serde_json::from_slice(&fs::read(&path).expect("corpus manifest"))
            .expect("corpus manifest JSON");
    manifest.source_snapshot_sha256 = "forged-snapshot".to_owned();
    fs::write(
        &path,
        serde_json::to_vec_pretty(&manifest).expect("serialize forged corpus manifest"),
    )
    .expect("write forged corpus manifest");

    let seen = Arc::new(Mutex::new(Vec::new()));
    let error = fixture
        .pipeline
        .embed_canonical_corpus(
            &EmbeddingBuildConfig {
                artifact_name: "invalid-corpus-contract".to_owned(),
                batch_size: 2,
                shard_rows: 2,
            },
            &mut RecordingEncoder::new(4, seen.clone()),
        )
        .expect_err("embedding must verify the backing corpus contract");
    assert!(error.to_string().contains("different corpus contract"));
    assert!(seen.lock().expect("seen lock").is_empty());
}

#[test]
fn nested_stage_extension_embeds_only_new_rows() {
    let fixture = Fixture::new(&["one", "two", "three", "four", "five", "six"]);
    fixture
        .pipeline
        .materialize_corpus_stage(&CorpusStageConfig {
            name: "four".to_owned(),
            rows: 4,
        })
        .expect("four-row stage");
    fixture
        .pipeline
        .materialize_corpus_stage(&CorpusStageConfig {
            name: "six".to_owned(),
            rows: 6,
        })
        .expect("six-row stage");

    let base_config = EmbeddingBuildConfig {
        artifact_name: "base-four".to_owned(),
        batch_size: 2,
        shard_rows: 2,
    };
    let base_seen = Arc::new(Mutex::new(Vec::new()));
    fixture
        .pipeline
        .embed_corpus_stage(
            "four",
            &base_config,
            &mut RecordingEncoder::new(4, base_seen.clone()),
        )
        .expect("base embedding");
    assert_eq!(base_seen.lock().expect("seen lock").len(), 4);
    let base_vectors = fs::read(
        fixture
            .pipeline
            .layout()
            .embedding_dir("base-four")
            .join("shards/000000/vectors.i8"),
    )
    .expect("base vectors");

    let extension_config = EmbeddingBuildConfig {
        artifact_name: "extended-six".to_owned(),
        batch_size: 2,
        shard_rows: 2,
    };
    let extension_seen = Arc::new(Mutex::new(Vec::new()));
    let manifest = fixture
        .pipeline
        .extend_corpus_stage(
            "base-four",
            "six",
            &extension_config,
            &mut RecordingEncoder::new(4, extension_seen.clone()),
        )
        .expect("extend embedding");
    assert_eq!(manifest.total_rows, 6);
    assert_eq!(extension_seen.lock().expect("seen lock").len(), 2);
    assert_eq!(
        fs::read(
            fixture
                .pipeline
                .layout()
                .embedding_dir("base-four")
                .join("shards/000000/vectors.i8"),
        )
        .expect("unchanged base vectors"),
        base_vectors
    );
    assert_eq!(
        fs::read(
            fixture
                .pipeline
                .layout()
                .embedding_dir("extended-six")
                .join("shards/000000/vectors.i8"),
        )
        .expect("reused vectors"),
        base_vectors
    );
    fs::remove_dir_all(fixture.pipeline.layout().embedding_dir("base-four"))
        .expect("remove external base after self-contained extension");
    fixture
        .pipeline
        .open_embedding_artifact("extended-six")
        .expect("extended artifact remains portable without its external base");
}

#[test]
fn extension_resume_repairs_an_interrupted_base_seed_without_reencoding_it() {
    let fixture = Fixture::new(&["one", "two", "three", "four", "five", "six"]);
    for (name, rows) in [("four", 4), ("six", 6)] {
        fixture
            .pipeline
            .materialize_corpus_stage(&CorpusStageConfig {
                name: name.to_owned(),
                rows,
            })
            .expect("corpus stage");
    }
    fixture
        .pipeline
        .embed_corpus_stage(
            "four",
            &EmbeddingBuildConfig {
                artifact_name: "seed-base".to_owned(),
                batch_size: 2,
                shard_rows: 2,
            },
            &mut RecordingEncoder::new(4, Arc::new(Mutex::new(Vec::new()))),
        )
        .expect("base artifact");
    let extension = EmbeddingBuildConfig {
        artifact_name: "repair-seed".to_owned(),
        batch_size: 2,
        shard_rows: 2,
    };
    fixture
        .pipeline
        .extend_corpus_stage(
            "seed-base",
            "six",
            &extension,
            &mut RecordingEncoder::new(4, Arc::new(Mutex::new(Vec::new()))).fail_after_calls(0),
        )
        .expect_err("interrupt after base shards are seeded");
    let work = fixture
        .pipeline
        .layout()
        .root()
        .join("work/embedding-repair-seed");
    fs::remove_dir_all(work.join("shards/000001")).expect("simulate partial base seeding");

    let seen = Arc::new(Mutex::new(Vec::new()));
    let manifest = fixture
        .pipeline
        .extend_corpus_stage(
            "seed-base",
            "six",
            &extension,
            &mut RecordingEncoder::new(4, seen.clone()),
        )
        .expect("resume repairs missing seeded shard");
    assert_eq!(seen.lock().expect("seen lock").len(), 2);
    let base = manifest.base_artifact.expect("incremental provenance");
    assert_eq!(base.name, "seed-base");
    assert_eq!(base.rows, 4);
    assert!(!base.manifest_sha256.is_empty());
}

#[test]
fn resume_reuses_an_identical_final_manifest_before_publish() {
    let fixture = Fixture::new(&["one", "two", "three"]);
    let config = EmbeddingBuildConfig {
        artifact_name: "republish".to_owned(),
        batch_size: 2,
        shard_rows: 2,
    };
    let manifest = fixture
        .pipeline
        .embed_canonical_corpus(
            &config,
            &mut RecordingEncoder::new(4, Arc::new(Mutex::new(Vec::new()))),
        )
        .expect("initial artifact");
    let artifact = fixture.pipeline.layout().embedding_dir("republish");
    let work = fixture
        .pipeline
        .layout()
        .root()
        .join("work/embedding-republish");
    fs::create_dir_all(work.parent().expect("work parent")).expect("work root");
    fs::rename(&artifact, &work).expect("simulate crash before final publish rename");

    let seen = Arc::new(Mutex::new(Vec::new()));
    let resumed = fixture
        .pipeline
        .embed_canonical_corpus(&config, &mut RecordingEncoder::new(4, seen.clone()))
        .expect("retry final publish");
    assert_eq!(resumed, manifest);
    assert!(seen.lock().expect("seen lock").is_empty());
    assert!(artifact.is_dir());
}

#[test]
fn production_embedding_batches_by_effective_length_but_preserves_row_mapping() {
    let fixture = Fixture::new(&[
        "xxxxxxxxxxxxxxxxxxxxxxxx",
        "x",
        "xxxxxxxxxxxx",
        "xxx",
        "xxxxxxxxxxxxxxxxxx",
        "xxxxxx",
    ]);
    let seen = Arc::new(Mutex::new(Vec::new()));
    let mut encoder = RecordingEncoder::new(4, seen.clone());
    let manifest = fixture
        .pipeline
        .embed_canonical_corpus(
            &EmbeddingBuildConfig {
                artifact_name: "bucketed".to_owned(),
                batch_size: 2,
                shard_rows: 100,
            },
            &mut encoder,
        )
        .expect("bucketed embedding build");

    let encoded_lengths = seen
        .lock()
        .expect("seen lock")
        .iter()
        .map(String::len)
        .collect::<Vec<_>>();
    assert!(
        encoded_lengths.windows(2).all(|pair| pair[0] <= pair[1]),
        "encoder batches must follow effective token length: {encoded_lengths:?}"
    );
    assert_eq!(manifest.total_rows, 6);
    fixture
        .pipeline
        .open_embedding_artifact("bucketed")
        .expect("row IDs remain in canonical order after bucketed execution");
    let root = fixture.pipeline.layout().embedding_dir("bucketed");
    for shard in &manifest.shards {
        let ids = fs::read(root.join(&shard.row_ids.file)).expect("row IDs");
        let vectors = fs::read(root.join(&shard.vectors.file)).expect("vectors");
        for (id, vector) in ids.chunks_exact(32).zip(vectors.chunks_exact(4)) {
            let content = fixture
                .contents_by_id
                .get(id)
                .expect("canonical ID belongs to the fixture");
            let seed = content.bytes().fold(1_u8, u8::wrapping_add).max(1);
            let expected = (0..4)
                .map(|offset| seed.wrapping_add(offset).min(127))
                .collect::<Vec<_>>();
            assert_eq!(
                vector, expected,
                "vector must remain paired with its row ID"
            );
        }
    }
}

struct Fixture {
    _temp: tempfile::TempDir,
    pipeline: DamusSnapshot,
    contents_by_id: BTreeMap<Vec<u8>, String>,
}

impl Fixture {
    fn new(contents: &[&str]) -> Self {
        let temp = tempfile::tempdir().expect("temporary directory");
        let root = temp.path().join("damus_snapshot");
        let pipeline = DamusSnapshot::new(&root);
        fs::create_dir_all(pipeline.layout().snapshot().parent().expect("input parent"))
            .expect("create input directory");
        let notes = contents
            .iter()
            .enumerate()
            .map(|(index, content)| signed_note(content, index as u64, index as u8 + 1))
            .collect::<Vec<_>>();
        let contents_by_id = notes
            .iter()
            .zip(contents)
            .map(|(note, content)| {
                let value: serde_json::Value =
                    serde_json::from_str(note).expect("fixture note JSON");
                let id = value["id"].as_str().expect("fixture event ID");
                let bytes = (0..id.len())
                    .step_by(2)
                    .map(|offset| u8::from_str_radix(&id[offset..offset + 2], 16).expect("hex ID"))
                    .collect::<Vec<_>>();
                (bytes, (*content).to_owned())
            })
            .collect();
        write_snapshot(
            pipeline.layout().snapshot(),
            &notes.iter().map(String::as_str).collect::<Vec<_>>(),
        );
        pipeline.import_source().expect("source import");
        pipeline.derive_corpus().expect("corpus derivation");
        pipeline
            .canonicalize_corpus()
            .expect("corpus canonicalization");
        Self {
            _temp: temp,
            pipeline,
            contents_by_id,
        }
    }
}

struct RecordingEncoder {
    descriptor: EncoderDescriptor,
    seen: Arc<Mutex<Vec<String>>>,
    calls: usize,
    fail_after_calls: Option<usize>,
}

impl RecordingEncoder {
    fn new(dimensions: u32, seen: Arc<Mutex<Vec<String>>>) -> Self {
        Self {
            descriptor: EncoderDescriptor {
                model_id: "test/length-aware".to_owned(),
                model_revision: "fixture-v1".to_owned(),
                model_lock_sha256: "fixture-lock".to_owned(),
                runtime: "test".to_owned(),
                runtime_version: "1".to_owned(),
                runtime_sha256: "fixture-runtime".to_owned(),
                execution_provider: "test".to_owned(),
                output_name: "native_int8".to_owned(),
                dimensions,
                max_tokens: 512,
                input_rule: "fixture-length-aware-v1".to_owned(),
                pooling: "fixture".to_owned(),
                quantization: "native-int8".to_owned(),
                instruction: None,
            },
            seen,
            calls: 0,
            fail_after_calls: None,
        }
    }

    fn fail_after_calls(mut self, calls: usize) -> Self {
        self.fail_after_calls = Some(calls);
        self
    }
}

impl EmbeddingEncoder for RecordingEncoder {
    fn descriptor(&self) -> &EncoderDescriptor {
        &self.descriptor
    }

    fn effective_token_lengths(&mut self, texts: &[&str]) -> Result<Vec<u32>> {
        texts
            .iter()
            .map(|text| {
                u32::try_from(text.len()).map_err(|_| {
                    Error::Invariant("fixture text length does not fit u32".to_owned())
                })
            })
            .collect()
    }

    fn encode(&mut self, texts: &[&str]) -> Result<Vec<i8>> {
        if self.fail_after_calls == Some(self.calls) {
            return Err(Error::Encoder {
                operation: "running fixture encoder",
                message: "deliberate fixture failure".to_owned(),
            });
        }
        self.calls += 1;
        self.seen
            .lock()
            .expect("seen lock")
            .extend(texts.iter().map(|text| (*text).to_owned()));
        let dimensions = usize::try_from(self.descriptor.dimensions).expect("dimensions");
        let mut output = Vec::with_capacity(texts.len() * dimensions);
        for text in texts {
            let seed = text.bytes().fold(1_u8, u8::wrapping_add).max(1);
            for offset in 0..dimensions {
                output.push(seed.wrapping_add(offset as u8).min(127) as i8);
            }
        }
        Ok(output)
    }
}

fn signed_note(content: &str, offset: u64, secret_byte: u8) -> String {
    NoteBuilder::new()
        .kind(1)
        .content(content)
        .created_at(1_700_100_000 + offset)
        .sign(&[secret_byte; 32])
        .build()
        .expect("sign note")
        .json()
        .expect("note JSON")
}

fn write_snapshot(path: impl AsRef<std::path::Path>, events: &[&str]) {
    let file = File::create(path).expect("snapshot file");
    let writer = BufWriter::new(file);
    let mut encoder = zstd::stream::write::Encoder::new(writer, 1).expect("zstd encoder");
    for event in events {
        writeln!(encoder, "{event}").expect("snapshot event");
    }
    encoder.finish().expect("finish snapshot");
}
