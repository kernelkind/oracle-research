use std::fs::{self, File, OpenOptions};
use std::io::{BufReader, BufWriter, Read, Write};
use std::thread;
use std::time::Duration;

use nostrdb::NoteBuilder;
use oracle_mvp::benchmark::{
    BenchmarkStageConfig, EmbeddingBenchmark, HardwareIdentity, TokenBucketScheme,
};
use oracle_mvp::budget::MicroUsd;
use oracle_mvp::embedding::{EmbeddingBuildConfig, EmbeddingEncoder, EncoderDescriptor};
use oracle_mvp::snapshot::{CanonicalManifest, CorpusManifest, DamusSnapshot, Error, Result};
use oracle_mvp::stage::CorpusStageConfig;
use sha2::{Digest, Sha256};

const CALIBRATION_ROWS: u64 = 100_000;

#[test]
fn benchmark_rejects_a_non_calibration_stage_before_reserving_or_encoding() {
    let fixture = Fixture::new(&["one", "two"]);
    fixture
        .pipeline
        .materialize_corpus_stage(&CorpusStageConfig {
            name: "too-small".to_owned(),
            rows: 2,
        })
        .expect("small stage");
    let mut config = benchmark_config("unusable-stage", "unusable-artifact");
    config.stage_name = "too-small".to_owned();
    let mut encoder = DelayedEncoder::new();

    let error = fixture
        .pipeline
        .benchmark_corpus_stage(&config, &mut encoder)
        .expect_err("rented benchmark requires an exact 100K stage");
    assert!(error.to_string().contains("100,000-row"));
    assert_eq!(encoder.encode_calls, 0);
    assert!(
        !fixture
            .pipeline
            .layout()
            .root()
            .join("budget-reservations/benchmark-unusable-stage.json")
            .exists()
    );
}

#[test]
fn benchmark_times_the_real_resumable_artifact_builder() {
    let fixture = Fixture::new(&[
        "one",
        "two-two",
        "a considerably longer note",
        "four",
        "another considerably longer note",
        "six",
    ]);
    fixture.inflate_canonical_rows(CALIBRATION_ROWS);
    fixture
        .pipeline
        .materialize_corpus_stage(&CorpusStageConfig {
            name: "calibration".to_owned(),
            rows: CALIBRATION_ROWS,
        })
        .expect("calibration stage");
    let error = fixture
        .pipeline
        .embed_corpus_stage(
            "calibration",
            &EmbeddingBuildConfig {
                artifact_name: "unadmitted-cuda".to_owned(),
                batch_size: 2,
                shard_rows: 2,
            },
            &mut DelayedEncoder::new(),
        )
        .expect_err("ordinary library API must reject CUDA");
    assert!(error.to_string().contains("refuse CUDA"));

    let mut wrong_shard = benchmark_config("wrong-shard", "wrong-shard-artifact");
    wrong_shard.embedding.shard_rows = CALIBRATION_ROWS / 2;
    let mut encoder = DelayedEncoder::new();
    let error = fixture
        .pipeline
        .benchmark_corpus_stage(&wrong_shard, &mut encoder)
        .expect_err("calibration must use the production 100K shard size");
    assert!(error.to_string().contains("shard_rows=100,000"));
    assert_eq!(encoder.encode_calls, 0);
    assert!(
        !fixture
            .pipeline
            .layout()
            .root()
            .join("budget-reservations/benchmark-wrong-shard.json")
            .exists()
    );

    let stale = benchmark_config("stale-work", "stale-work-artifact");
    let stale_work = fixture
        .pipeline
        .layout()
        .root()
        .join("work/embedding-stale-work-artifact");
    fs::create_dir_all(&stale_work).expect("stale embedding work");
    let mut encoder = DelayedEncoder::new();
    let error = fixture
        .pipeline
        .benchmark_corpus_stage(&stale, &mut encoder)
        .expect_err("benchmark must not reserve money for resumable work");
    assert!(error.to_string().contains("fresh embedding artifact"));
    assert_eq!(encoder.encode_calls, 0);
    assert!(
        !fixture
            .pipeline
            .layout()
            .root()
            .join("budget-reservations/benchmark-stale-work.json")
            .exists()
    );
    fs::remove_dir_all(stale_work).expect("remove stale work fixture");

    let config = benchmark_config("resume-benchmark", "bench-artifact");

    let error = fixture
        .pipeline
        .benchmark_corpus_stage(
            &config,
            &mut DelayedEncoder::new().fail_after_encode_calls(1),
        )
        .expect_err("fixture interrupts within the one calibration shard");
    assert!(error.to_string().contains("deliberate fixture failure"));

    let error = fixture
        .pipeline
        .benchmark_corpus_stage(&config, &mut DelayedEncoder::new())
        .expect_err("failed benchmark reservation is one-shot");
    assert!(error.to_string().contains("one-shot"));
    assert!(
        !fixture
            .pipeline
            .layout()
            .root()
            .join("benchmarks/resume-benchmark/manifest.json")
            .exists()
    );

    let fresh_config = benchmark_config("fresh-benchmark", "fresh-bench-artifact");
    let benchmark = fixture
        .pipeline
        .benchmark_corpus_stage(&fresh_config, &mut DelayedEncoder::new())
        .expect("fresh production-path benchmark");

    assert_eq!(benchmark.total_artifact_rows, CALIBRATION_ROWS);
    assert_eq!(benchmark.reused_rows, 0);
    assert_eq!(benchmark.newly_encoded_rows, CALIBRATION_ROWS);
    assert_eq!(benchmark.reused_shards, 0);
    assert_eq!(benchmark.newly_completed_shards, 1);
    assert_eq!(
        benchmark
            .buckets
            .iter()
            .map(|bucket| bucket.rows)
            .sum::<u64>(),
        CALIBRATION_ROWS
    );
    assert!(
        benchmark
            .buckets
            .iter()
            .filter(|bucket| bucket.rows > 0)
            .all(|bucket| bucket.encode_elapsed_nanoseconds > 0)
    );
    assert!(benchmark.phases.effective_length_nanoseconds > 0);
    assert!(benchmark.phases.artifact_write_nanoseconds > 0);
    assert!(benchmark.phases.checkpoint_nanoseconds > 0);
    assert!(benchmark.phases.end_to_end_nanoseconds > 0);
    assert_eq!(
        benchmark
            .buckets
            .iter()
            .map(|bucket| bucket.encode_elapsed_nanoseconds)
            .sum::<u64>()
            + benchmark.phases.effective_length_nanoseconds
            + benchmark.phases.artifact_write_nanoseconds
            + benchmark.phases.checkpoint_nanoseconds
            + benchmark.phases.other_nanoseconds,
        benchmark.phases.end_to_end_nanoseconds
    );

    let artifact_manifest = fixture
        .pipeline
        .layout()
        .embedding_manifest("fresh-bench-artifact");
    assert_eq!(
        benchmark.artifact_manifest_sha256,
        hash_file(&artifact_manifest)
    );
    fixture
        .pipeline
        .open_embedding_artifact("fresh-bench-artifact")
        .expect("benchmark artifact is independently verifiable");

    let persisted_path = fixture
        .pipeline
        .layout()
        .root()
        .join("benchmarks/fresh-benchmark/manifest.json");
    let persisted: EmbeddingBenchmark =
        serde_json::from_reader(File::open(persisted_path).expect("benchmark manifest"))
            .expect("decode benchmark manifest");
    assert_eq!(persisted, benchmark);

    let mut over_phase_cap = benchmark_config("over-phase-cap", "over-phase-artifact");
    over_phase_cap.maximum_rental_cost = MicroUsd::from_dollars(40);
    let error = fixture
        .pipeline
        .benchmark_corpus_stage(&over_phase_cap, &mut DelayedEncoder::new())
        .expect_err("active failure reservation counts toward the cumulative phase cap");
    assert!(error.to_string().contains("cumulative $40"));
}

struct Fixture {
    _temp: tempfile::TempDir,
    pipeline: DamusSnapshot,
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
        }
    }

    fn inflate_canonical_rows(&self, rows: u64) {
        let rows_path = self.pipeline.layout().canonical_rows();
        let original = fs::read(&rows_path).expect("canonical rows");
        let original_rows = original.len() / 32;
        let file = OpenOptions::new()
            .write(true)
            .truncate(true)
            .open(&rows_path)
            .expect("replace canonical rows");
        let mut writer = BufWriter::new(file);
        for row in 0..rows {
            let source = usize::try_from(row % original_rows as u64).expect("source row");
            writer
                .write_all(&original[source * 32..(source + 1) * 32])
                .expect("repeat canonical ID");
        }
        writer.flush().expect("flush repeated rows");

        let canonical_path = self.pipeline.layout().canonical_manifest();
        let mut canonical: CanonicalManifest = serde_json::from_reader(BufReader::new(
            File::open(&canonical_path).expect("canonical manifest"),
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
        let mut corpus: CorpusManifest = serde_json::from_reader(BufReader::new(
            File::open(&corpus_path).expect("corpus manifest"),
        ))
        .expect("corpus manifest JSON");
        corpus.eligible_events = rows;
        write_json_replacing(&corpus_path, &corpus);
    }
}

struct DelayedEncoder {
    descriptor: EncoderDescriptor,
    encode_calls: usize,
    fail_after_encode_calls: Option<usize>,
}

impl DelayedEncoder {
    fn new() -> Self {
        Self {
            descriptor: EncoderDescriptor {
                model_id: "test/delayed".to_owned(),
                model_revision: "fixture-v1".to_owned(),
                model_lock_sha256: "fixture-lock".to_owned(),
                runtime: "test".to_owned(),
                runtime_version: "1".to_owned(),
                runtime_sha256: "fixture-runtime".to_owned(),
                execution_provider: "cuda".to_owned(),
                output_name: "native_int8".to_owned(),
                dimensions: 4,
                max_tokens: 512,
                input_rule: "fixture-length-v1".to_owned(),
                pooling: "fixture".to_owned(),
                quantization: "native-int8".to_owned(),
                instruction: None,
            },
            encode_calls: 0,
            fail_after_encode_calls: None,
        }
    }

    fn fail_after_encode_calls(mut self, calls: usize) -> Self {
        self.fail_after_encode_calls = Some(calls);
        self
    }
}

impl EmbeddingEncoder for DelayedEncoder {
    fn descriptor(&self) -> &EncoderDescriptor {
        &self.descriptor
    }

    fn effective_token_lengths(&mut self, texts: &[&str]) -> Result<Vec<u32>> {
        thread::sleep(Duration::from_millis(1));
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
        if self.fail_after_encode_calls == Some(self.encode_calls) {
            return Err(Error::Encoder {
                operation: "running fixture encoder",
                message: "deliberate fixture failure".to_owned(),
            });
        }
        self.encode_calls += 1;
        let maximum = texts.iter().map(|text| text.len()).max().unwrap_or(1);
        thread::sleep(Duration::from_millis(if maximum <= 8 { 1 } else { 3 }));
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

fn benchmark_config(name: &str, artifact_name: &str) -> BenchmarkStageConfig {
    BenchmarkStageConfig {
        name: name.to_owned(),
        stage_name: "calibration".to_owned(),
        embedding: EmbeddingBuildConfig {
            artifact_name: artifact_name.to_owned(),
            batch_size: 50_000,
            shard_rows: CALIBRATION_ROWS,
        },
        bucket_scheme: TokenBucketScheme {
            upper_bounds: vec![8, 512],
        },
        hardware: HardwareIdentity {
            gpu_model: "fixture-gpu".to_owned(),
            gpu_device_uuid: "GPU-fixture".to_owned(),
            gpu_count: 1,
            driver_version: "fixture-driver".to_owned(),
            cuda_version: "fixture-cuda".to_owned(),
            host_cpu: "fixture-cpu".to_owned(),
            host_memory_bytes: 64 * 1024 * 1024,
            rental_provider: "fixture-provider".to_owned(),
            rental_offer_id: "fixture-offer".to_owned(),
        },
        rental_rate_per_hour: MicroUsd(3_600_000),
        maximum_rental_cost: MicroUsd::from_dollars(1),
    }
}

fn write_json_replacing(path: &std::path::Path, value: &impl serde::Serialize) {
    let file = OpenOptions::new()
        .write(true)
        .truncate(true)
        .open(path)
        .expect("replace manifest");
    serde_json::to_writer_pretty(file, value).expect("write manifest");
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

fn hash_file(path: &std::path::Path) -> String {
    let mut file = File::open(path).expect("hash input");
    let mut bytes = Vec::new();
    file.read_to_end(&mut bytes).expect("read hash input");
    format!("{:x}", Sha256::digest(bytes))
}
