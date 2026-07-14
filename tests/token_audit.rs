use std::fs::{self, File};
use std::io::{BufWriter, Write};
use std::process::Command;

use nostrdb::NoteBuilder;
use oracle_mvp::snapshot::DamusSnapshot;
use oracle_mvp::stage::CorpusStageConfig;
use oracle_mvp::token_audit::{TokenAuditConfig, TokenLengthCounter, TokenizerDescriptor};

#[test]
fn audits_every_canonical_row_before_model_truncation_and_reopens_verifiably() {
    let fixture = AuditFixture::new(&[
        "one",
        "one two three",
        "one two three four five",
        "one two three four five six seven",
    ]);
    let config = TokenAuditConfig {
        artifact_name: "complete-canonical-audit".to_owned(),
        shard_rows: 2,
    };
    let mut counter = WordCounter::new();

    let manifest = fixture
        .pipeline
        .audit_canonical_token_lengths(&config, &mut counter)
        .expect("complete canonical token audit");

    assert_eq!(manifest.schema_version, 1);
    assert_eq!(manifest.total_rows, 4);
    assert_eq!(manifest.total_tokens, 16);
    assert_eq!(manifest.minimum_tokens, 1);
    assert_eq!(manifest.maximum_tokens, 7);
    assert_eq!(manifest.rows_over_model_ceiling, 2);
    assert_eq!(manifest.tokenizer, counter.descriptor);
    assert!(manifest.corpus_stage.is_none());
    assert_eq!(counter.seen.len(), 4);
    for content in [
        "one",
        "one two three",
        "one two three four five",
        "one two three four five six seven",
    ] {
        assert!(counter.seen.iter().any(|seen| seen == content));
    }

    let root = fixture
        .pipeline
        .layout()
        .root()
        .join("token-audits")
        .join(&config.artifact_name);
    let lengths = manifest
        .shards
        .iter()
        .flat_map(|shard| {
            decode_u32_records(
                &fs::read(root.join(&shard.row_lengths.file)).expect("shard row lengths"),
            )
        })
        .collect::<Vec<_>>();
    assert_eq!(lengths.len(), 4);
    assert_eq!(
        decode_buckets(&fs::read(root.join("length_buckets.bin")).expect("length buckets")),
        vec![(1, 1), (3, 1), (5, 1), (7, 1)]
    );
    assert_eq!(
        fixture
            .pipeline
            .open_token_length_audit(&config.artifact_name, &counter.descriptor)
            .expect("verified reopen"),
        manifest
    );
}

#[test]
fn stage_audit_records_exact_selection_and_rejects_corruption_or_tokenizer_mismatch() {
    let fixture = AuditFixture::new(&["one", "one two", "one two three", "one two three four"]);
    let stage = fixture
        .pipeline
        .materialize_corpus_stage(&CorpusStageConfig {
            name: "two-row-stage".to_owned(),
            rows: 2,
        })
        .expect("corpus stage");
    let config = TokenAuditConfig {
        artifact_name: "two-row-audit".to_owned(),
        shard_rows: 2,
    };
    let mut counter = WordCounter::new();
    let manifest = fixture
        .pipeline
        .audit_corpus_stage_token_lengths("two-row-stage", &config, &mut counter)
        .expect("stage token audit");

    let audited_stage = manifest.corpus_stage.as_ref().expect("stage provenance");
    assert_eq!(audited_stage.name, stage.name);
    assert_eq!(audited_stage.selected_rows, stage.selected_rows);
    assert_eq!(audited_stage.selection_rule, stage.selection_rule);
    assert_eq!(manifest.total_rows, 2);
    assert_eq!(counter.seen.len(), 2);

    let mut wrong_descriptor = counter.descriptor.clone();
    wrong_descriptor.model_revision = "different-revision".to_owned();
    let error = fixture
        .pipeline
        .open_token_length_audit(&config.artifact_name, &wrong_descriptor)
        .expect_err("tokenizer mismatch must be rejected");
    assert!(error.to_string().contains("tokenizer identity"));

    let lengths = fixture
        .pipeline
        .layout()
        .root()
        .join("token-audits")
        .join(&config.artifact_name)
        .join(&manifest.shards[0].row_lengths.file);
    let mut bytes = fs::read(&lengths).expect("row lengths");
    bytes[0] ^= 1;
    fs::write(&lengths, bytes).expect("corrupt row lengths");
    let error = fixture
        .pipeline
        .open_token_length_audit(&config.artifact_name, &counter.descriptor)
        .expect_err("artifact corruption must be rejected");
    assert!(error.to_string().contains("metadata"));
}

#[test]
fn resumes_after_verified_complete_shards_without_retokenizing_them() {
    let fixture = AuditFixture::new(&[
        "one",
        "one two",
        "one two three",
        "one two three four",
        "one two three four five",
    ]);
    let config = TokenAuditConfig {
        artifact_name: "resumable-audit".to_owned(),
        shard_rows: 2,
    };
    let mut interrupted = InterruptingCounter::new(2);
    let error = fixture
        .pipeline
        .audit_canonical_token_lengths(&config, &mut interrupted)
        .expect_err("second shard is interrupted");
    assert!(error.to_string().contains("fixture interruption"));

    let completed_shard = fixture
        .pipeline
        .layout()
        .root()
        .join("work/token-audit-resumable-audit/shards/000000/manifest.json");
    assert!(completed_shard.is_file());

    let mut resumed = WordCounter::new();
    let manifest = fixture
        .pipeline
        .audit_canonical_token_lengths(&config, &mut resumed)
        .expect("resume complete audit");
    assert_eq!(manifest.total_rows, 5);
    assert_eq!(manifest.shards.len(), 3);
    assert_eq!(
        resumed.seen.len(),
        3,
        "two rows in the verified first shard must not be tokenized again"
    );
}

#[test]
fn cli_exposes_the_tokenizer_only_complete_audit() {
    let output = Command::new(env!("CARGO_BIN_EXE_oracle-mvp"))
        .arg("--help")
        .output()
        .expect("run CLI help");
    assert!(output.status.success());
    let stdout = String::from_utf8(output.stdout).expect("UTF-8 help");
    assert!(stdout.contains("audit-token-lengths DATA_ROOT AUDIT_NAME MODEL_DIR [SHARD_ROWS]"));
}

struct WordCounter {
    descriptor: TokenizerDescriptor,
    seen: Vec<String>,
}

impl WordCounter {
    fn new() -> Self {
        Self {
            descriptor: TokenizerDescriptor {
                model_id: "test/word-counter".to_owned(),
                model_revision: "fixture-v1".to_owned(),
                model_lock_sha256: "11".repeat(32),
                tokenizer_file_sha256: "22".repeat(32),
                tokenizer_runtime: "fixture-tokenizer-1".to_owned(),
                model_token_ceiling: 4,
                input_rule: "raw-text-add-specials-no-truncation-v1".to_owned(),
                token_length_rule: "fixture-whitespace-words-v1".to_owned(),
            },
            seen: Vec::new(),
        }
    }
}

impl TokenLengthCounter for WordCounter {
    fn descriptor(&self) -> &TokenizerDescriptor {
        &self.descriptor
    }

    fn raw_token_lengths(&mut self, texts: &[&str]) -> oracle_mvp::snapshot::Result<Vec<u32>> {
        self.seen
            .extend(texts.iter().map(|text| (*text).to_owned()));
        Ok(texts
            .iter()
            .map(|text| u32::try_from(text.split_whitespace().count().max(1)).expect("u32 length"))
            .collect())
    }
}

struct InterruptingCounter {
    inner: WordCounter,
    fail_on_call: usize,
    calls: usize,
}

impl InterruptingCounter {
    fn new(fail_on_call: usize) -> Self {
        Self {
            inner: WordCounter::new(),
            fail_on_call,
            calls: 0,
        }
    }
}

impl TokenLengthCounter for InterruptingCounter {
    fn descriptor(&self) -> &TokenizerDescriptor {
        self.inner.descriptor()
    }

    fn raw_token_lengths(&mut self, texts: &[&str]) -> oracle_mvp::snapshot::Result<Vec<u32>> {
        self.calls += 1;
        if self.calls == self.fail_on_call {
            return Err(oracle_mvp::snapshot::Error::Encoder {
                operation: "fixture tokenization",
                message: "fixture interruption".to_owned(),
            });
        }
        self.inner.raw_token_lengths(texts)
    }
}

struct AuditFixture {
    _temp: tempfile::TempDir,
    pipeline: DamusSnapshot,
}

impl AuditFixture {
    fn new(contents: &[&str]) -> Self {
        let temp = tempfile::tempdir().expect("temporary directory");
        let pipeline = DamusSnapshot::new(temp.path().join("damus_snapshot"));
        fs::create_dir_all(pipeline.layout().snapshot().parent().expect("input parent"))
            .expect("create input directory");
        let events = contents
            .iter()
            .enumerate()
            .map(|(index, content)| signed_note(content, index))
            .collect::<Vec<_>>();
        write_snapshot(
            pipeline.layout().snapshot(),
            &events.iter().map(String::as_str).collect::<Vec<_>>(),
        );
        pipeline.import_source().expect("source import");
        pipeline.derive_corpus().expect("corpus derivation");
        pipeline.canonicalize_corpus().expect("canonicalize corpus");
        Self {
            _temp: temp,
            pipeline,
        }
    }
}

fn signed_note(content: &str, index: usize) -> String {
    NoteBuilder::new()
        .kind(1)
        .content(content)
        .created_at(1_700_000_000 + u64::try_from(index).expect("timestamp index"))
        .sign(&[u8::try_from(index + 1).expect("secret byte"); 32])
        .build()
        .expect("signed note")
        .json()
        .expect("note JSON")
}

fn write_snapshot(path: std::path::PathBuf, events: &[&str]) {
    let file = File::create(&path).expect("snapshot file");
    let encoder = zstd::stream::write::Encoder::new(file, 1).expect("zstd encoder");
    let mut writer = BufWriter::new(encoder);
    for event in events {
        writeln!(writer, "{event}").expect("write event");
    }
    let encoder = match writer.into_inner() {
        Ok(encoder) => encoder,
        Err(_) => panic!("finish buffered writer"),
    };
    encoder.finish().expect("finish zstd stream");
}

fn decode_u32_records(bytes: &[u8]) -> Vec<u32> {
    bytes
        .chunks_exact(4)
        .map(|record| u32::from_le_bytes(record.try_into().expect("u32 record")))
        .collect()
}

fn decode_buckets(bytes: &[u8]) -> Vec<(u32, u64)> {
    bytes
        .chunks_exact(12)
        .map(|record| {
            (
                u32::from_le_bytes(record[..4].try_into().expect("bucket length")),
                u64::from_le_bytes(record[4..].try_into().expect("bucket rows")),
            )
        })
        .collect()
}
