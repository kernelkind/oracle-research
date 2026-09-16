use std::fs::{self, File, OpenOptions};
use std::io::{BufReader, BufWriter, Read, Write};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::Duration;

use nostrdb::NoteBuilder;
use oracle_mvp::benchmark::{BenchmarkStageConfig, HardwareIdentity, TokenBucketScheme};
use oracle_mvp::budget::{AdmittedExecutionConfig, BudgetAdmissionConfig, MicroUsd};
use oracle_mvp::embedding::{EmbeddingBuildConfig, EmbeddingEncoder, EncoderDescriptor};
use oracle_mvp::snapshot::{CanonicalManifest, CorpusManifest, DamusSnapshot, Error, Result};
use oracle_mvp::stage::CorpusStageConfig;
use oracle_mvp::token_audit::{TokenAuditConfig, TokenLengthCounter, TokenizerDescriptor};
use sha2::{Digest, Sha256};

const CALIBRATION_ROWS: u64 = 100_000;
const RAW_INPUT_RULE: &str =
    "raw-utf8-url-text-empty-as-eot-add-special-tokens-no-truncation-no-padding-v1";
const RAW_LENGTH_RULE: &str = "tokenizer-output-ids-before-model-truncation-v1";
const ENCODER_INPUT_RULE: &str =
    "raw-utf8-url-text-empty-as-eot-add-special-tokens-right-truncate-512-v1";

#[test]
fn admission_derives_audited_buckets_and_executes_only_the_exact_cuda_stage() {
    let fixture = Fixture::new();
    fixture.inflate_canonical_rows(CALIBRATION_ROWS);
    fixture
        .pipeline
        .materialize_corpus_stage(&CorpusStageConfig {
            name: "stage-100k".to_owned(),
            rows: CALIBRATION_ROWS,
        })
        .expect("representative stage");
    fixture
        .pipeline
        .audit_corpus_stage_token_lengths(
            "stage-100k",
            &TokenAuditConfig {
                artifact_name: "audit-100k".to_owned(),
                shard_rows: CALIBRATION_ROWS,
            },
            &mut FixedLengthCounter::new(),
        )
        .expect("exact stage token audit");

    let benchmark = fixture
        .pipeline
        .benchmark_corpus_stage(
            &BenchmarkStageConfig {
                name: "benchmark-100k".to_owned(),
                stage_name: "stage-100k".to_owned(),
                embedding: EmbeddingBuildConfig {
                    artifact_name: "benchmark-matrix".to_owned(),
                    batch_size: 100_000,
                    shard_rows: CALIBRATION_ROWS,
                },
                bucket_scheme: TokenBucketScheme {
                    upper_bounds: vec![512],
                },
                hardware: hardware(),
                rental_rate_per_hour: MicroUsd::from_dollars(1),
                maximum_rental_cost: MicroUsd::from_dollars(1),
            },
            &mut FixedEncoder::new(),
        )
        .expect("fresh 100K production benchmark");
    assert_eq!(benchmark.newly_encoded_rows, CALIBRATION_ROWS);
    assert_eq!(benchmark.buckets[0].maximum_padded_tokens_per_row, 512);

    let admission = fixture
        .pipeline
        .plan_and_publish_budget_admission("stage-admission", &admission_config("admitted-matrix"))
        .expect("derive identities and counts from local artifacts");
    assert_eq!(
        admission.request.proposal.projected_buckets[0].rows,
        CALIBRATION_ROWS
    );
    assert_eq!(
        admission.request.proposal.projected_buckets[0].effective_tokens,
        CALIBRATION_ROWS * 512
    );
    let stale_admission = fixture
        .pipeline
        .plan_and_publish_budget_admission(
            "stale-stage-admission",
            &admission_config("stale-admitted-matrix"),
        )
        .expect("second admission reflects the same pre-launch commitments");
    assert_eq!(
        stale_admission.request.completed_spend,
        admission.request.completed_spend
    );

    let mut forged = admission.request.clone();
    forged.proposal.projected_buckets[0].effective_tokens -= 1;
    let error = fixture
        .pipeline
        .publish_budget_admission("forged-admission", &forged)
        .expect_err("caller-supplied bucket counts cannot override the audit");
    assert!(error.to_string().contains("exact audited stage delta"));

    let mut wrong_execution = execution();
    wrong_execution.hardware.rental_offer_id = "different-offer".to_owned();
    let error = fixture
        .pipeline
        .execute_budget_admission(
            "stage-admission",
            &wrong_execution,
            &mut FixedEncoder::new(),
        )
        .expect_err("launch offer must match calibration");
    assert!(error.to_string().contains("differs from the calibration"));

    let encoded = Arc::new(Mutex::new(0_u64));
    let error = fixture
        .pipeline
        .execute_budget_admission(
            "stage-admission",
            &execution(),
            &mut FixedEncoder::new().fail_after_calls(0),
        )
        .expect_err("first charged attempt fails before completing a shard");
    assert!(error.to_string().contains("deliberate fixture failure"));
    assert!(
        fixture
            .pipeline
            .layout()
            .root()
            .join("admitted-attempts/admitted-matrix/000000.json")
            .is_file()
    );

    let manifest = fixture
        .pipeline
        .execute_budget_admission(
            "stage-admission",
            &execution(),
            &mut FixedEncoder::recording(encoded.clone()),
        )
        .expect("execute exact admitted CUDA build");
    assert_eq!(manifest.total_rows, CALIBRATION_ROWS);
    assert_eq!(*encoded.lock().expect("encoded rows"), CALIBRATION_ROWS);
    assert!(
        fixture
            .pipeline
            .layout()
            .root()
            .join("admitted-attempts/admitted-matrix/000001.json")
            .is_file()
    );

    let error = fixture
        .pipeline
        .execute_budget_admission(
            "stale-stage-admission",
            &execution(),
            &mut FixedEncoder::new(),
        )
        .expect_err("a pre-existing admission cannot ignore the first launch commitment");
    assert!(error.to_string().contains("managed commitments changed"));
    assert!(
        !fixture
            .pipeline
            .layout()
            .root()
            .join("admitted-attempts/stale-admitted-matrix")
            .exists()
    );

    let fresh_admission = fixture
        .pipeline
        .plan_and_publish_budget_admission(
            "fresh-stage-admission",
            &admission_config("fresh-admitted-matrix"),
        )
        .expect("planner includes the first launch commitment");
    assert_eq!(
        fresh_admission.request.completed_spend.0,
        admission.request.completed_spend.0 + 2 * admission.projected_stage.0
    );

    let error = fixture
        .pipeline
        .execute_budget_admission(
            "fresh-stage-admission",
            &execution(),
            &mut FixedEncoder::new().fail_after_calls(0),
        )
        .expect_err("the fresh stage's first charged attempt fails");
    assert!(error.to_string().contains("deliberate fixture failure"));
    assert!(
        fixture
            .pipeline
            .layout()
            .root()
            .join("admitted-attempts/fresh-admitted-matrix/000000.json")
            .is_file()
    );

    let retry_encoded = Arc::new(Mutex::new(0_u64));
    let error = fixture
        .pipeline
        .execute_budget_admission(
            "fresh-stage-admission",
            &execution(),
            &mut FixedEncoder::recording(retry_encoded.clone()),
        )
        .expect_err("another full charged attempt would exceed the hard budget");
    assert!(error.to_string().contains("$1,000"));
    assert_eq!(*retry_encoded.lock().expect("retry encoded rows"), 0);
    assert!(
        !fixture
            .pipeline
            .layout()
            .root()
            .join("admitted-attempts/fresh-admitted-matrix/000001.json")
            .exists()
    );

    let resumed = fixture
        .pipeline
        .execute_budget_admission("stage-admission", &execution(), &mut FixedEncoder::new())
        .expect("reopening the exact complete artifact is not another charged attempt");
    assert_eq!(resumed, manifest);
    assert!(
        !fixture
            .pipeline
            .layout()
            .root()
            .join("admitted-attempts/admitted-matrix/000002.json")
            .exists()
    );
}

struct Fixture {
    _temp: tempfile::TempDir,
    pipeline: DamusSnapshot,
}

impl Fixture {
    fn new() -> Self {
        let temp = tempfile::tempdir().expect("temporary directory");
        let root = temp.path().join("damus_snapshot");
        let pipeline = DamusSnapshot::new(&root);
        fs::create_dir_all(pipeline.layout().snapshot().parent().expect("input parent"))
            .expect("input directory");
        let note = NoteBuilder::new()
            .kind(1)
            .content("one reusable fixture note")
            .created_at(1_700_100_000)
            .sign(&[7_u8; 32])
            .build()
            .expect("signed note")
            .json()
            .expect("note JSON");
        write_snapshot(pipeline.layout().snapshot(), &[&note]);
        pipeline.import_source().expect("source import");
        pipeline.derive_corpus().expect("corpus derivation");
        pipeline.canonicalize_corpus().expect("canonical corpus");
        Self {
            _temp: temp,
            pipeline,
        }
    }

    fn inflate_canonical_rows(&self, rows: u64) {
        let rows_path = self.pipeline.layout().canonical_rows();
        let mut original = [0_u8; 32];
        File::open(&rows_path)
            .expect("canonical rows")
            .read_exact(&mut original)
            .expect("canonical ID");
        let file = OpenOptions::new()
            .write(true)
            .truncate(true)
            .open(&rows_path)
            .expect("replace canonical rows");
        let mut writer = BufWriter::new(file);
        for _ in 0..rows {
            writer.write_all(&original).expect("repeated canonical ID");
        }
        writer.flush().expect("flush repeated rows");

        let canonical_path = self.pipeline.layout().canonical_manifest();
        let mut canonical: CanonicalManifest = serde_json::from_reader(BufReader::new(
            File::open(&canonical_path).expect("manifest"),
        ))
        .expect("canonical manifest JSON");
        canonical.counts.eligible_events = rows;
        canonical.counts.canonical_rows = rows;
        canonical.counts.duplicate_events = 0;
        canonical.rows.records = rows;
        canonical.rows.bytes = rows * 32;
        canonical.rows.sha256 = hash_file(&rows_path);
        write_json_replacing(&canonical_path, &canonical);

        let corpus_path = self.pipeline.layout().corpus_manifest();
        let mut corpus: CorpusManifest =
            serde_json::from_reader(BufReader::new(File::open(&corpus_path).expect("manifest")))
                .expect("corpus manifest JSON");
        corpus.eligible_events = rows;
        write_json_replacing(&corpus_path, &corpus);
    }
}

struct FixedLengthCounter {
    descriptor: TokenizerDescriptor,
}

impl FixedLengthCounter {
    fn new() -> Self {
        Self {
            descriptor: TokenizerDescriptor {
                model_id: "fixture/pplx".to_owned(),
                model_revision: "fixture-revision".to_owned(),
                model_lock_sha256: "ab".repeat(32),
                tokenizer_file_sha256: "cd".repeat(32),
                tokenizer_runtime: "fixture-runtime".to_owned(),
                model_token_ceiling: 512,
                input_rule: RAW_INPUT_RULE.to_owned(),
                token_length_rule: RAW_LENGTH_RULE.to_owned(),
            },
        }
    }
}

impl TokenLengthCounter for FixedLengthCounter {
    fn descriptor(&self) -> &TokenizerDescriptor {
        &self.descriptor
    }

    fn raw_token_lengths(&mut self, texts: &[&str]) -> Result<Vec<u32>> {
        Ok(vec![600; texts.len()])
    }
}

struct FixedEncoder {
    descriptor: EncoderDescriptor,
    encoded: Option<Arc<Mutex<u64>>>,
    calls: usize,
    fail_after_calls: Option<usize>,
}

impl FixedEncoder {
    fn new() -> Self {
        Self::with_recording(None)
    }

    fn recording(encoded: Arc<Mutex<u64>>) -> Self {
        Self::with_recording(Some(encoded))
    }

    fn fail_after_calls(mut self, calls: usize) -> Self {
        self.fail_after_calls = Some(calls);
        self
    }

    fn with_recording(encoded: Option<Arc<Mutex<u64>>>) -> Self {
        Self {
            descriptor: EncoderDescriptor {
                model_id: "fixture/pplx".to_owned(),
                model_revision: "fixture-revision".to_owned(),
                model_lock_sha256: "ab".repeat(32),
                runtime: "onnxruntime".to_owned(),
                runtime_version: "fixture-runtime".to_owned(),
                runtime_sha256: "ef".repeat(32),
                execution_provider: "cuda".to_owned(),
                output_name: "pooler_output_int8".to_owned(),
                dimensions: 1,
                max_tokens: 512,
                input_rule: ENCODER_INPUT_RULE.to_owned(),
                pooling: "model-native-mean".to_owned(),
                quantization: "native-int8".to_owned(),
                instruction: None,
            },
            encoded,
            calls: 0,
            fail_after_calls: None,
        }
    }
}

impl EmbeddingEncoder for FixedEncoder {
    fn descriptor(&self) -> &EncoderDescriptor {
        &self.descriptor
    }

    fn effective_token_lengths(&mut self, texts: &[&str]) -> Result<Vec<u32>> {
        Ok(vec![512; texts.len()])
    }

    fn encode(&mut self, texts: &[&str]) -> Result<Vec<i8>> {
        if self.fail_after_calls == Some(self.calls) {
            return Err(Error::Encoder {
                operation: "running fixture encoder",
                message: "deliberate fixture failure".to_owned(),
            });
        }
        self.calls += 1;
        thread::sleep(Duration::from_millis(1));
        if let Some(encoded) = &self.encoded {
            let mut total = encoded.lock().expect("encoded rows");
            *total = total
                .checked_add(u64::try_from(texts.len()).map_err(|_| {
                    Error::Invariant("fixture batch length does not fit u64".to_owned())
                })?)
                .ok_or_else(|| Error::Invariant("fixture row count overflowed".to_owned()))?;
        }
        Ok(vec![1; texts.len()])
    }
}

fn hardware() -> HardwareIdentity {
    HardwareIdentity {
        gpu_model: "fixture-gpu".to_owned(),
        gpu_device_uuid: "GPU-fixture".to_owned(),
        gpu_count: 1,
        driver_version: "fixture-driver".to_owned(),
        cuda_version: "fixture-cuda".to_owned(),
        host_cpu: "fixture-cpu".to_owned(),
        host_memory_bytes: 64 * 1024 * 1024,
        rental_provider: "fixture-provider".to_owned(),
        rental_offer_id: "fixture-offer".to_owned(),
    }
}

fn execution() -> AdmittedExecutionConfig {
    AdmittedExecutionConfig {
        hardware: hardware(),
        rental_rate_per_hour: MicroUsd::from_dollars(1),
    }
}

fn admission_config(artifact_name: &str) -> BudgetAdmissionConfig {
    BudgetAdmissionConfig {
        benchmark_name: "benchmark-100k".to_owned(),
        stage_name: "stage-100k".to_owned(),
        artifact_name: artifact_name.to_owned(),
        base_artifact_name: None,
        token_audit_name: "audit-100k".to_owned(),
        projected_artifact_and_transfer: MicroUsd::from_dollars(280),
    }
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

fn write_json_replacing(path: &std::path::Path, value: &impl serde::Serialize) {
    let file = OpenOptions::new()
        .write(true)
        .truncate(true)
        .open(path)
        .expect("replace manifest");
    serde_json::to_writer_pretty(file, value).expect("write manifest");
}

fn hash_file(path: &std::path::Path) -> String {
    let mut file = File::open(path).expect("hash input");
    let mut bytes = Vec::new();
    file.read_to_end(&mut bytes).expect("read hash input");
    format!("{:x}", Sha256::digest(bytes))
}
