//! End-to-end measurements from the resumable production embedding builder.

use std::collections::BTreeMap;
use std::fs;
use std::path::Path;
use std::time::{Duration, Instant};

use serde::{Deserialize, Serialize};

use crate::artifact::{hash_file, is_safe_artifact_name};
use crate::budget::{
    MicroUsd, REQUIRED_BENCHMARK_ROWS, release_benchmark_budget, reserve_benchmark_budget,
};
use crate::embedding::{
    EmbeddingArtifactPhase, EmbeddingBuildConfig, EmbeddingBuildObserver, EmbeddingEncoder,
    EmbeddingManifest, EmbeddingShardManifest, EncoderDescriptor, validate_config,
};
use crate::snapshot::{
    DamusSnapshot, Error, Result, create_directory, io_error, read_manifest, require_file,
    write_manifest,
};

pub(crate) const BENCHMARK_SCHEMA_VERSION: u32 = 2;
const NANOS_PER_HOUR: u128 = 3_600_000_000_000;

/// Ordered upper bounds shared by an audit, benchmark, and budget projection.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct TokenBucketScheme {
    pub upper_bounds: Vec<u32>,
}

/// Audited row and effective-token count assigned to one production bucket.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct TokenBucketCount {
    pub upper_bound: u32,
    pub rows: u64,
    pub effective_tokens: u64,
    /// Exact production batches produced by shard-local sorting.
    pub batches: u64,
    /// Exact batch shapes produced by shard-local sorting.
    pub batch_shapes: Vec<TokenBatchShapeCount>,
}

/// Count of projected production batches with one exact row and padding shape.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct TokenBatchShapeCount {
    pub rows_per_batch: u32,
    pub padded_tokens_per_row: u32,
    pub batches: u64,
}

/// Measured production encoding time for batches assigned to one bucket.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct TokenBucketMeasurement {
    pub upper_bound: u32,
    pub rows: u64,
    pub effective_tokens: u64,
    pub padded_tokens: u64,
    pub encode_elapsed_nanoseconds: u64,
    pub batches: u64,
    /// Largest padded sequence length actually measured in this bucket.
    pub maximum_padded_tokens_per_row: u32,
    /// Rows in the slowest observed production batch on a per-row basis.
    pub worst_batch_rows: u32,
    /// Wall time of that slowest observed production batch.
    pub worst_batch_elapsed_nanoseconds: u64,
    /// Slowest whole production batch observed in this bucket.
    pub maximum_batch_elapsed_nanoseconds: u64,
    /// Exact observed batch shapes and the slowest timing for each shape.
    pub batch_shapes: Vec<TokenBatchShapeMeasurement>,
}

/// Observed production batches with one exact row and padding shape.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct TokenBatchShapeMeasurement {
    pub rows_per_batch: u32,
    pub padded_tokens_per_row: u32,
    pub batches: u64,
    pub maximum_elapsed_nanoseconds: u64,
}

/// Directly timed non-model phases plus complete wall time.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct PhaseTimings {
    pub effective_length_nanoseconds: u64,
    pub artifact_write_nanoseconds: u64,
    pub checkpoint_nanoseconds: u64,
    /// All measured wall time not enclosed by the three explicit phase timers
    /// or by model-encoding timers, including corpus reads and scheduling.
    pub other_nanoseconds: u64,
    pub end_to_end_nanoseconds: u64,
}

/// Exact rented host and device identity attached to one measurement.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct HardwareIdentity {
    pub gpu_model: String,
    pub gpu_device_uuid: String,
    pub gpu_count: u32,
    pub driver_version: String,
    pub cuda_version: String,
    pub host_cpu: String,
    pub host_memory_bytes: u64,
    pub rental_provider: String,
    pub rental_offer_id: String,
}

/// Inputs for one fresh benchmark artifact build.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct BenchmarkStageConfig {
    pub name: String,
    pub stage_name: String,
    pub embedding: EmbeddingBuildConfig,
    pub bucket_scheme: TokenBucketScheme,
    pub hardware: HardwareIdentity,
    /// Total hourly price for the complete rented instance, not GPU-only price.
    pub rental_rate_per_hour: MicroUsd,
    /// Predeclared maximum cost of this calibration run itself.
    pub maximum_rental_cost: MicroUsd,
}

/// Immutable result of timing the actual artifact/checkpoint production path.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct EmbeddingBenchmark {
    pub schema_version: u32,
    pub name: String,
    pub artifact_name: String,
    pub artifact_manifest_sha256: String,
    pub stage_name: String,
    pub stage_manifest_sha256: String,
    pub selected_rows_sha256: String,
    pub encoder: EncoderDescriptor,
    pub batch_size: u32,
    pub batching_rule: String,
    pub matrix_format: String,
    pub shard_rows: u64,
    pub total_artifact_rows: u64,
    pub newly_encoded_rows: u64,
    pub reused_rows: u64,
    pub newly_completed_shards: u32,
    pub reused_shards: u32,
    pub artifact_bytes: u64,
    pub hardware: HardwareIdentity,
    pub rental_rate_per_hour: MicroUsd,
    pub maximum_rental_cost: MicroUsd,
    pub bucket_scheme: TokenBucketScheme,
    pub buckets: Vec<TokenBucketMeasurement>,
    pub phases: PhaseTimings,
    pub measured_rental_cost: MicroUsd,
}

impl DamusSnapshot {
    /// Build and time one fresh embedding artifact through the production path.
    ///
    /// Interrupted or pre-existing shards are observed but invalidate the
    /// benchmark: timings from separate processes are never silently combined.
    pub fn benchmark_corpus_stage(
        &self,
        config: &BenchmarkStageConfig,
        encoder: &mut dyn EmbeddingEncoder,
    ) -> Result<EmbeddingBenchmark> {
        validate_benchmark_config(config, encoder.descriptor())?;
        let benchmark_root = self.layout().root().join("benchmarks").join(&config.name);
        let benchmark_path = benchmark_root.join("manifest.json");
        if benchmark_path.exists() {
            let benchmark: EmbeddingBenchmark = read_manifest(&benchmark_path)?;
            verify_benchmark(self, &benchmark, Some(config), Some(encoder.descriptor()))?;
            return Ok(benchmark);
        }
        if benchmark_root.exists() {
            return Err(Error::Invariant(format!(
                "incomplete benchmark artifact exists at `{}`",
                benchmark_root.display()
            )));
        }
        let reservation_path = self
            .layout()
            .root()
            .join("budget-reservations")
            .join(format!("benchmark-{}.json", config.name));
        if reservation_path.exists() {
            reserve_benchmark_budget(self, &config.name, config.maximum_rental_cost)?;
            return Err(Error::Invariant(
                "existing benchmark reservation was unexpectedly reusable".to_owned(),
            ));
        }
        validate_fresh_calibration_input(self, config)?;
        reserve_benchmark_budget(self, &config.name, config.maximum_rental_cost)?;

        let maximum_runtime_nanoseconds =
            maximum_runtime(config.maximum_rental_cost, config.rental_rate_per_hour)?;
        let batch_size = u32::try_from(config.embedding.batch_size)
            .map_err(|_| Error::Budget("benchmark batch size does not fit u32".to_owned()))?;
        let mut recorder = BenchmarkRecorder::new(
            config.bucket_scheme.clone(),
            batch_size,
            maximum_runtime_nanoseconds,
        )?;
        let started = Instant::now();
        let artifact = self.embed_corpus_stage_observed(
            &config.stage_name,
            &config.embedding,
            encoder,
            &mut recorder,
        )?;
        let end_to_end = duration_nanoseconds(started.elapsed())?;
        let observations = recorder.finish(end_to_end)?;
        if observations.reused_rows != 0
            || observations.reused_shards != 0
            || observations.newly_encoded_rows != artifact.total_rows
        {
            return Err(Error::Budget(
                "benchmark must start from a fresh artifact; interrupted or existing shards cannot supply a complete timing record"
                    .to_owned(),
            ));
        }
        let corpus_stage = artifact.corpus_stage.as_ref().ok_or_else(|| {
            Error::Invariant("benchmark artifact does not represent a corpus stage".to_owned())
        })?;
        let manifest_path = self
            .layout()
            .embedding_manifest(&config.embedding.artifact_name);
        let artifact_manifest_sha256 = hash_file(&manifest_path)?;
        let artifact_bytes =
            directory_bytes(&self.layout().embedding_dir(&config.embedding.artifact_name))?;
        let measured_rental_cost = cost_for_duration(
            observations.phases.end_to_end_nanoseconds,
            config.rental_rate_per_hour,
        )?;
        let benchmark = EmbeddingBenchmark {
            schema_version: BENCHMARK_SCHEMA_VERSION,
            name: config.name.clone(),
            artifact_name: config.embedding.artifact_name.clone(),
            artifact_manifest_sha256,
            stage_name: corpus_stage.name.clone(),
            stage_manifest_sha256: corpus_stage.manifest_sha256.clone(),
            selected_rows_sha256: corpus_stage.rows_sha256.clone(),
            encoder: artifact.encoder.clone(),
            batch_size: artifact.batch_size,
            batching_rule: artifact.batching_rule.clone(),
            matrix_format: artifact.matrix_format.clone(),
            shard_rows: artifact.shard_rows,
            total_artifact_rows: artifact.total_rows,
            newly_encoded_rows: observations.newly_encoded_rows,
            reused_rows: observations.reused_rows,
            newly_completed_shards: observations.newly_completed_shards,
            reused_shards: observations.reused_shards,
            artifact_bytes,
            hardware: config.hardware.clone(),
            rental_rate_per_hour: config.rental_rate_per_hour,
            maximum_rental_cost: config.maximum_rental_cost,
            bucket_scheme: config.bucket_scheme.clone(),
            buckets: observations.buckets,
            phases: observations.phases,
            measured_rental_cost,
        };
        verify_benchmark(self, &benchmark, Some(config), Some(encoder.descriptor()))?;
        publish_benchmark(self.layout().root(), &benchmark)?;
        release_benchmark_budget(self, &config.name)?;
        Ok(benchmark)
    }

    /// Open and verify a benchmark record and the artifact it identifies.
    pub fn open_embedding_benchmark(&self, name: &str) -> Result<EmbeddingBenchmark> {
        validate_name(name, "benchmark")?;
        let path = self
            .layout()
            .root()
            .join("benchmarks")
            .join(name)
            .join("manifest.json");
        require_file(&path)?;
        let benchmark: EmbeddingBenchmark = read_manifest(&path)?;
        verify_benchmark(self, &benchmark, None, None)?;
        Ok(benchmark)
    }
}

struct BenchmarkRecorder {
    scheme: TokenBucketScheme,
    batch_size: u32,
    buckets: BTreeMap<u32, MutableBucket>,
    length_rows: u64,
    length_effective_tokens: u64,
    effective_length_nanoseconds: u128,
    artifact_write_nanoseconds: u128,
    checkpoint_nanoseconds: u128,
    reused_rows: u64,
    reused_shards: u32,
    newly_completed_shards: u32,
    invalid_length: Option<u32>,
    invalid_batch_rows: Option<u32>,
    started: Instant,
    maximum_runtime_nanoseconds: u64,
}

#[derive(Default)]
struct MutableBucket {
    rows: u64,
    effective_tokens: u64,
    padded_tokens: u64,
    encode_elapsed_nanoseconds: u128,
    batches: u64,
    maximum_padded_tokens_per_row: u32,
    worst_batch_rows: u32,
    worst_batch_elapsed_nanoseconds: u64,
    maximum_batch_elapsed_nanoseconds: u64,
    batch_shapes: BTreeMap<(u32, u32), MutableBatchShape>,
}

#[derive(Default)]
struct MutableBatchShape {
    batches: u64,
    maximum_elapsed_nanoseconds: u64,
}

struct FinishedObservation {
    newly_encoded_rows: u64,
    reused_rows: u64,
    newly_completed_shards: u32,
    reused_shards: u32,
    buckets: Vec<TokenBucketMeasurement>,
    phases: PhaseTimings,
}

impl BenchmarkRecorder {
    fn new(
        scheme: TokenBucketScheme,
        batch_size: u32,
        maximum_runtime_nanoseconds: u64,
    ) -> Result<Self> {
        validate_bucket_scheme(&scheme, None)?;
        if batch_size == 0 {
            return Err(Error::Budget(
                "benchmark batch size must be positive".to_owned(),
            ));
        }
        let buckets = scheme
            .upper_bounds
            .iter()
            .map(|upper_bound| (*upper_bound, MutableBucket::default()))
            .collect();
        Ok(Self {
            scheme,
            batch_size,
            buckets,
            length_rows: 0,
            length_effective_tokens: 0,
            effective_length_nanoseconds: 0,
            artifact_write_nanoseconds: 0,
            checkpoint_nanoseconds: 0,
            reused_rows: 0,
            reused_shards: 0,
            newly_completed_shards: 0,
            invalid_length: None,
            invalid_batch_rows: None,
            started: Instant::now(),
            maximum_runtime_nanoseconds,
        })
    }

    fn finish(self, end_to_end_nanoseconds: u64) -> Result<FinishedObservation> {
        if let Some(length) = self.invalid_length {
            return Err(Error::Budget(format!(
                "effective token length {length} is outside the benchmark bucket scheme"
            )));
        }
        if let Some(rows) = self.invalid_batch_rows {
            return Err(Error::Budget(format!(
                "encoder submitted {rows} rows in a benchmark batch configured for at most {}",
                self.batch_size
            )));
        }
        let mut encoded_rows = 0_u64;
        let mut encoded_effective_tokens = 0_u64;
        let mut encode_nanoseconds = 0_u128;
        let mut buckets = Vec::with_capacity(self.buckets.len());
        for upper_bound in &self.scheme.upper_bounds {
            let bucket = self
                .buckets
                .get(upper_bound)
                .expect("scheme initialized map");
            encoded_rows = encoded_rows
                .checked_add(bucket.rows)
                .ok_or_else(|| Error::Budget("benchmark row count overflowed".to_owned()))?;
            encoded_effective_tokens = encoded_effective_tokens
                .checked_add(bucket.effective_tokens)
                .ok_or_else(|| Error::Budget("benchmark token count overflowed".to_owned()))?;
            encode_nanoseconds = encode_nanoseconds
                .checked_add(bucket.encode_elapsed_nanoseconds)
                .ok_or_else(|| Error::Budget("benchmark duration overflowed".to_owned()))?;
            buckets.push(TokenBucketMeasurement {
                upper_bound: *upper_bound,
                rows: bucket.rows,
                effective_tokens: bucket.effective_tokens,
                padded_tokens: bucket.padded_tokens,
                encode_elapsed_nanoseconds: u64::try_from(bucket.encode_elapsed_nanoseconds)
                    .map_err(|_| Error::Budget("benchmark duration does not fit u64".to_owned()))?,
                batches: bucket.batches,
                maximum_padded_tokens_per_row: bucket.maximum_padded_tokens_per_row,
                worst_batch_rows: bucket.worst_batch_rows,
                worst_batch_elapsed_nanoseconds: bucket.worst_batch_elapsed_nanoseconds,
                maximum_batch_elapsed_nanoseconds: bucket.maximum_batch_elapsed_nanoseconds,
                batch_shapes: bucket
                    .batch_shapes
                    .iter()
                    .map(|((rows_per_batch, padded_tokens_per_row), measurement)| {
                        TokenBatchShapeMeasurement {
                            rows_per_batch: *rows_per_batch,
                            padded_tokens_per_row: *padded_tokens_per_row,
                            batches: measurement.batches,
                            maximum_elapsed_nanoseconds: measurement.maximum_elapsed_nanoseconds,
                        }
                    })
                    .collect(),
            });
        }
        if encoded_rows != self.length_rows
            || encoded_effective_tokens != self.length_effective_tokens
        {
            return Err(Error::Budget(
                "length measurement and successful encoding covered different rows or tokens"
                    .to_owned(),
            ));
        }
        let explicit = encode_nanoseconds
            .checked_add(self.effective_length_nanoseconds)
            .and_then(|value| value.checked_add(self.artifact_write_nanoseconds))
            .and_then(|value| value.checked_add(self.checkpoint_nanoseconds))
            .ok_or_else(|| Error::Budget("benchmark phase duration overflowed".to_owned()))?;
        let end_to_end = u128::from(end_to_end_nanoseconds);
        let other = end_to_end.checked_sub(explicit).ok_or_else(|| {
            Error::Budget("benchmark phase timers exceed end-to-end wall time".to_owned())
        })?;
        Ok(FinishedObservation {
            newly_encoded_rows: encoded_rows,
            reused_rows: self.reused_rows,
            newly_completed_shards: self.newly_completed_shards,
            reused_shards: self.reused_shards,
            buckets,
            phases: PhaseTimings {
                effective_length_nanoseconds: u64::try_from(self.effective_length_nanoseconds)
                    .map_err(|_| Error::Budget("benchmark duration does not fit u64".to_owned()))?,
                artifact_write_nanoseconds: u64::try_from(self.artifact_write_nanoseconds)
                    .map_err(|_| Error::Budget("benchmark duration does not fit u64".to_owned()))?,
                checkpoint_nanoseconds: u64::try_from(self.checkpoint_nanoseconds)
                    .map_err(|_| Error::Budget("benchmark duration does not fit u64".to_owned()))?,
                other_nanoseconds: u64::try_from(other)
                    .map_err(|_| Error::Budget("benchmark duration does not fit u64".to_owned()))?,
                end_to_end_nanoseconds,
            },
        })
    }

    fn bucket_for(&self, length: u32) -> Option<u32> {
        self.scheme
            .upper_bounds
            .iter()
            .copied()
            .find(|upper_bound| length <= *upper_bound)
    }
}

impl EmbeddingBuildObserver for BenchmarkRecorder {
    fn check_continue(&mut self) -> Result<()> {
        if duration_nanoseconds(self.started.elapsed())? > self.maximum_runtime_nanoseconds {
            return Err(Error::Budget(
                "benchmark exceeded its predeclared rental-cost cap".to_owned(),
            ));
        }
        Ok(())
    }

    fn reused_shard(&mut self, shard: &EmbeddingShardManifest) {
        self.reused_rows = self.reused_rows.saturating_add(shard.rows);
        self.reused_shards = self.reused_shards.saturating_add(1);
    }

    fn measured_effective_lengths(&mut self, lengths: &[u32], elapsed: Duration) {
        self.effective_length_nanoseconds = self
            .effective_length_nanoseconds
            .saturating_add(elapsed.as_nanos());
        self.length_rows = self
            .length_rows
            .saturating_add(u64::try_from(lengths.len()).unwrap_or(u64::MAX));
        self.length_effective_tokens = lengths
            .iter()
            .fold(self.length_effective_tokens, |tokens, length| {
                tokens.saturating_add(u64::from(*length))
            });
        if self.invalid_length.is_none() {
            self.invalid_length = lengths
                .iter()
                .copied()
                .find(|length| self.bucket_for(*length).is_none());
        }
    }

    fn encoded_batch(&mut self, lengths: &[u32], elapsed: Duration) {
        let Some(maximum) = lengths.iter().copied().max() else {
            return;
        };
        let Some(upper_bound) = self.bucket_for(maximum) else {
            self.invalid_length.get_or_insert(maximum);
            return;
        };
        let bucket = self.buckets.get_mut(&upper_bound).expect("known bucket");
        let rows = u64::try_from(lengths.len()).unwrap_or(u64::MAX);
        bucket.rows = bucket.rows.saturating_add(rows);
        bucket.batches = bucket.batches.saturating_add(1);
        bucket.effective_tokens = lengths
            .iter()
            .fold(bucket.effective_tokens, |tokens, length| {
                tokens.saturating_add(u64::from(*length))
            });
        bucket.padded_tokens = bucket
            .padded_tokens
            .saturating_add(rows.saturating_mul(u64::from(maximum)));
        let elapsed_nanoseconds = u64::try_from(elapsed.as_nanos()).unwrap_or(u64::MAX);
        bucket.encode_elapsed_nanoseconds = bucket
            .encode_elapsed_nanoseconds
            .saturating_add(elapsed.as_nanos());
        bucket.maximum_padded_tokens_per_row = bucket.maximum_padded_tokens_per_row.max(maximum);
        let batch_rows = u32::try_from(rows).unwrap_or(u32::MAX);
        if batch_rows > self.batch_size {
            self.invalid_batch_rows.get_or_insert(batch_rows);
        }
        let shape = bucket
            .batch_shapes
            .entry((batch_rows, maximum))
            .or_default();
        shape.batches = shape.batches.saturating_add(1);
        shape.maximum_elapsed_nanoseconds =
            shape.maximum_elapsed_nanoseconds.max(elapsed_nanoseconds);
        let replace_worst = bucket.worst_batch_rows == 0
            || u128::from(elapsed_nanoseconds) * u128::from(bucket.worst_batch_rows)
                > u128::from(bucket.worst_batch_elapsed_nanoseconds) * u128::from(batch_rows);
        if replace_worst {
            bucket.worst_batch_rows = batch_rows;
            bucket.worst_batch_elapsed_nanoseconds = elapsed_nanoseconds;
        }
        bucket.maximum_batch_elapsed_nanoseconds = bucket
            .maximum_batch_elapsed_nanoseconds
            .max(elapsed_nanoseconds);
    }

    fn artifact_phase(&mut self, phase: EmbeddingArtifactPhase, elapsed: Duration) {
        match phase {
            EmbeddingArtifactPhase::Write => {
                self.artifact_write_nanoseconds = self
                    .artifact_write_nanoseconds
                    .saturating_add(elapsed.as_nanos());
            }
            EmbeddingArtifactPhase::Checkpoint => {
                self.checkpoint_nanoseconds = self
                    .checkpoint_nanoseconds
                    .saturating_add(elapsed.as_nanos());
            }
        }
    }

    fn completed_shard(&mut self, _shard: &EmbeddingShardManifest) {
        self.newly_completed_shards = self.newly_completed_shards.saturating_add(1);
    }
}

fn validate_benchmark_config(
    config: &BenchmarkStageConfig,
    descriptor: &EncoderDescriptor,
) -> Result<()> {
    validate_config(&config.embedding, descriptor)?;
    validate_name(&config.name, "benchmark")?;
    validate_name(&config.stage_name, "corpus stage")?;
    validate_name(&config.embedding.artifact_name, "embedding artifact")?;
    validate_bucket_scheme(&config.bucket_scheme, Some(descriptor.max_tokens))?;
    if descriptor.execution_provider != "cuda" {
        return Err(Error::Budget(
            "rented-hardware benchmark requires the CUDA production provider".to_owned(),
        ));
    }
    if config.rental_rate_per_hour.0 == 0
        || config.maximum_rental_cost.0 == 0
        || config.maximum_rental_cost > MicroUsd::from_dollars(40)
    {
        return Err(Error::Budget(
            "benchmark rental rate and predeclared cost cap must be positive, with the cap at most $40"
                .to_owned(),
        ));
    }
    validate_hardware(&config.hardware)
}

fn validate_fresh_calibration_input(
    pipeline: &DamusSnapshot,
    config: &BenchmarkStageConfig,
) -> Result<()> {
    let stage = pipeline.open_corpus_stage(&config.stage_name)?;
    if stage.selected_rows != REQUIRED_BENCHMARK_ROWS {
        return Err(Error::Budget(
            "rented calibration requires an exact 100,000-row corpus stage".to_owned(),
        ));
    }
    if config.embedding.shard_rows != REQUIRED_BENCHMARK_ROWS {
        return Err(Error::Budget(
            "rented calibration requires embedding shard_rows=100,000".to_owned(),
        ));
    }
    let layout = pipeline.layout();
    if layout
        .embedding_dir(&config.embedding.artifact_name)
        .exists()
        || layout
            .embedding_stage(&config.embedding.artifact_name)
            .exists()
    {
        return Err(Error::Budget(
            "rented calibration requires a fresh embedding artifact with no resumable work"
                .to_owned(),
        ));
    }
    Ok(())
}

fn validate_bucket_scheme(scheme: &TokenBucketScheme, maximum: Option<u32>) -> Result<()> {
    if scheme.upper_bounds.is_empty()
        || scheme.upper_bounds.contains(&0)
        || scheme
            .upper_bounds
            .windows(2)
            .any(|pair| pair[0] >= pair[1])
    {
        return Err(Error::Budget(
            "token bucket upper bounds must be nonempty, positive, and strictly increasing"
                .to_owned(),
        ));
    }
    if let Some(maximum) = maximum
        && scheme.upper_bounds.last().copied() != Some(maximum)
    {
        return Err(Error::Budget(format!(
            "last token bucket must equal encoder ceiling {maximum}"
        )));
    }
    Ok(())
}

fn validate_hardware(hardware: &HardwareIdentity) -> Result<()> {
    if hardware.gpu_count == 0
        || hardware.host_memory_bytes == 0
        || [
            &hardware.gpu_model,
            &hardware.gpu_device_uuid,
            &hardware.driver_version,
            &hardware.cuda_version,
            &hardware.host_cpu,
            &hardware.rental_provider,
            &hardware.rental_offer_id,
        ]
        .iter()
        .any(|value| value.is_empty())
    {
        return Err(Error::Budget(
            "benchmark hardware and rental identity must be complete".to_owned(),
        ));
    }
    Ok(())
}

fn verify_benchmark(
    pipeline: &DamusSnapshot,
    benchmark: &EmbeddingBenchmark,
    config: Option<&BenchmarkStageConfig>,
    descriptor: Option<&EncoderDescriptor>,
) -> Result<()> {
    if benchmark.schema_version != BENCHMARK_SCHEMA_VERSION {
        return Err(Error::Budget(format!(
            "benchmark schema {} is unsupported",
            benchmark.schema_version
        )));
    }
    validate_name(&benchmark.name, "benchmark")?;
    validate_name(&benchmark.artifact_name, "embedding artifact")?;
    validate_bucket_scheme(&benchmark.bucket_scheme, Some(benchmark.encoder.max_tokens))?;
    validate_hardware(&benchmark.hardware)?;
    let artifact: EmbeddingManifest = pipeline.open_embedding_artifact(&benchmark.artifact_name)?;
    if hash_file(
        &pipeline
            .layout()
            .embedding_manifest(&benchmark.artifact_name),
    )? != benchmark.artifact_manifest_sha256
        || artifact.encoder != benchmark.encoder
        || artifact.batch_size != benchmark.batch_size
        || artifact.batching_rule != benchmark.batching_rule
        || artifact.matrix_format != benchmark.matrix_format
        || artifact.shard_rows != benchmark.shard_rows
        || artifact.total_rows != benchmark.total_artifact_rows
    {
        return Err(Error::Budget(
            "benchmark does not match its embedding artifact".to_owned(),
        ));
    }
    let stage = artifact.corpus_stage.as_ref().ok_or_else(|| {
        Error::Budget("benchmark artifact does not represent a corpus stage".to_owned())
    })?;
    if stage.name != benchmark.stage_name
        || stage.manifest_sha256 != benchmark.stage_manifest_sha256
        || stage.rows_sha256 != benchmark.selected_rows_sha256
    {
        return Err(Error::Budget(
            "benchmark does not match its selected corpus stage".to_owned(),
        ));
    }
    if benchmark.reused_rows != 0
        || benchmark.reused_shards != 0
        || benchmark.total_artifact_rows != REQUIRED_BENCHMARK_ROWS
        || benchmark.newly_encoded_rows != benchmark.total_artifact_rows
        || benchmark.shard_rows != REQUIRED_BENCHMARK_ROWS
        || benchmark.newly_completed_shards != 1
        || benchmark.rental_rate_per_hour.0 == 0
        || benchmark.maximum_rental_cost.0 == 0
        || benchmark.maximum_rental_cost > MicroUsd::from_dollars(40)
        || benchmark.measured_rental_cost > benchmark.maximum_rental_cost
    {
        return Err(Error::Budget(
            "benchmark must measure a complete fresh 100,000-row calibration artifact build"
                .to_owned(),
        ));
    }
    verify_measurements(benchmark)?;
    let actual_bytes = directory_bytes(&pipeline.layout().embedding_dir(&benchmark.artifact_name))?;
    if actual_bytes != benchmark.artifact_bytes {
        return Err(Error::Budget(
            "benchmark artifact byte count has changed".to_owned(),
        ));
    }
    if let Some(config) = config
        && (benchmark.name != config.name
            || benchmark.artifact_name != config.embedding.artifact_name
            || benchmark.stage_name != config.stage_name
            || benchmark.batch_size
                != u32::try_from(config.embedding.batch_size).unwrap_or(u32::MAX)
            || benchmark.shard_rows != config.embedding.shard_rows
            || benchmark.bucket_scheme != config.bucket_scheme
            || benchmark.hardware != config.hardware
            || benchmark.rental_rate_per_hour != config.rental_rate_per_hour
            || benchmark.maximum_rental_cost != config.maximum_rental_cost)
    {
        return Err(Error::Budget(
            "existing benchmark was built with different requested settings".to_owned(),
        ));
    }
    if let Some(descriptor) = descriptor
        && benchmark.encoder != *descriptor
    {
        return Err(Error::Budget(
            "existing benchmark was built with a different encoder".to_owned(),
        ));
    }
    Ok(())
}

pub(crate) fn verify_measurements(benchmark: &EmbeddingBenchmark) -> Result<()> {
    if benchmark.buckets.len() != benchmark.bucket_scheme.upper_bounds.len()
        || benchmark
            .buckets
            .iter()
            .zip(&benchmark.bucket_scheme.upper_bounds)
            .any(|(bucket, bound)| bucket.upper_bound != *bound)
    {
        return Err(Error::Budget(
            "benchmark buckets do not match its bucket scheme".to_owned(),
        ));
    }
    let rows = checked_sum(
        benchmark.buckets.iter().map(|bucket| bucket.rows),
        "bucket rows",
    )?;
    let encode = checked_sum(
        benchmark
            .buckets
            .iter()
            .map(|bucket| bucket.encode_elapsed_nanoseconds),
        "bucket duration",
    )?;
    let batches = checked_sum(
        benchmark.buckets.iter().map(|bucket| bucket.batches),
        "bucket batches",
    )?;
    let expected_batches = benchmark
        .newly_encoded_rows
        .div_ceil(u64::from(benchmark.batch_size));
    let mut previous_bound = 0;
    for bucket in &benchmark.buckets {
        verify_bucket_measurement(bucket, previous_bound, benchmark.batch_size)?;
        previous_bound = bucket.upper_bound;
    }
    if rows != benchmark.newly_encoded_rows || batches != expected_batches {
        return Err(Error::Budget(
            "benchmark bucket coverage is incomplete".to_owned(),
        ));
    }
    let explicit = checked_sum(
        [
            encode,
            benchmark.phases.effective_length_nanoseconds,
            benchmark.phases.artifact_write_nanoseconds,
            benchmark.phases.checkpoint_nanoseconds,
            benchmark.phases.other_nanoseconds,
        ]
        .into_iter(),
        "phase duration",
    )?;
    if explicit != benchmark.phases.end_to_end_nanoseconds
        || benchmark.phases.end_to_end_nanoseconds == 0
        || cost_for_duration(
            benchmark.phases.end_to_end_nanoseconds,
            benchmark.rental_rate_per_hour,
        )? != benchmark.measured_rental_cost
    {
        return Err(Error::Budget(
            "benchmark phase or rental-cost accounting is inconsistent".to_owned(),
        ));
    }
    Ok(())
}

fn verify_bucket_measurement(
    bucket: &TokenBucketMeasurement,
    previous_bound: u32,
    batch_size: u32,
) -> Result<()> {
    if bucket.rows == 0 {
        if bucket.effective_tokens != 0
            || bucket.padded_tokens != 0
            || bucket.encode_elapsed_nanoseconds != 0
            || bucket.batches != 0
            || bucket.maximum_padded_tokens_per_row != 0
            || bucket.worst_batch_rows != 0
            || bucket.worst_batch_elapsed_nanoseconds != 0
            || bucket.maximum_batch_elapsed_nanoseconds != 0
            || !bucket.batch_shapes.is_empty()
        {
            return Err(Error::Budget(
                "empty benchmark bucket contains batch measurements".to_owned(),
            ));
        }
        return Ok(());
    }
    if bucket.effective_tokens < bucket.rows
        || bucket.effective_tokens > bucket.padded_tokens
        || bucket.encode_elapsed_nanoseconds == 0
        || bucket.batches == 0
        || bucket.maximum_padded_tokens_per_row == 0
        || bucket.worst_batch_rows == 0
        || bucket.worst_batch_rows > batch_size
        || bucket.worst_batch_elapsed_nanoseconds == 0
        || bucket.maximum_batch_elapsed_nanoseconds == 0
        || bucket.batch_shapes.is_empty()
    {
        return Err(Error::Budget(
            "benchmark bucket coverage is incomplete".to_owned(),
        ));
    }
    let mut rows = 0_u64;
    let mut batches = 0_u64;
    let mut padded_tokens = 0_u64;
    let mut maximum_padded = 0_u32;
    let mut maximum_elapsed = 0_u64;
    let mut shape_maxima_sum = 0_u64;
    let mut previous_shape = None;
    for shape in &bucket.batch_shapes {
        let key = (shape.rows_per_batch, shape.padded_tokens_per_row);
        if shape.rows_per_batch == 0
            || shape.rows_per_batch > batch_size
            || shape.padded_tokens_per_row <= previous_bound
            || shape.padded_tokens_per_row > bucket.upper_bound
            || shape.batches == 0
            || shape.maximum_elapsed_nanoseconds == 0
            || previous_shape.is_some_and(|previous| previous >= key)
        {
            return Err(Error::Budget(
                "benchmark bucket contains an invalid or duplicate batch shape".to_owned(),
            ));
        }
        previous_shape = Some(key);
        rows = rows
            .checked_add(
                u64::from(shape.rows_per_batch)
                    .checked_mul(shape.batches)
                    .ok_or_else(|| Error::Budget("batch-shape rows overflowed".to_owned()))?,
            )
            .ok_or_else(|| Error::Budget("batch-shape rows overflowed".to_owned()))?;
        batches = batches
            .checked_add(shape.batches)
            .ok_or_else(|| Error::Budget("batch-shape count overflowed".to_owned()))?;
        padded_tokens = padded_tokens
            .checked_add(
                u64::from(shape.rows_per_batch)
                    .checked_mul(u64::from(shape.padded_tokens_per_row))
                    .and_then(|tokens| tokens.checked_mul(shape.batches))
                    .ok_or_else(|| Error::Budget("batch-shape tokens overflowed".to_owned()))?,
            )
            .ok_or_else(|| Error::Budget("batch-shape tokens overflowed".to_owned()))?;
        maximum_padded = maximum_padded.max(shape.padded_tokens_per_row);
        maximum_elapsed = maximum_elapsed.max(shape.maximum_elapsed_nanoseconds);
        shape_maxima_sum = shape_maxima_sum
            .checked_add(shape.maximum_elapsed_nanoseconds)
            .ok_or_else(|| Error::Budget("batch-shape duration overflowed".to_owned()))?;
    }
    if rows != bucket.rows
        || batches != bucket.batches
        || padded_tokens != bucket.padded_tokens
        || maximum_padded != bucket.maximum_padded_tokens_per_row
        || maximum_elapsed != bucket.maximum_batch_elapsed_nanoseconds
        || shape_maxima_sum > bucket.encode_elapsed_nanoseconds
        || !bucket.batch_shapes.iter().any(|shape| {
            shape.rows_per_batch == bucket.worst_batch_rows
                && shape.maximum_elapsed_nanoseconds >= bucket.worst_batch_elapsed_nanoseconds
        })
    {
        return Err(Error::Budget(
            "benchmark bucket aggregates do not match its exact batch shapes".to_owned(),
        ));
    }
    Ok(())
}

fn publish_benchmark(root: &Path, benchmark: &EmbeddingBenchmark) -> Result<()> {
    let parent = root.join("benchmarks");
    create_directory(&parent)?;
    let target = parent.join(&benchmark.name);
    if target.exists() {
        return Err(Error::ArtifactExists(target));
    }
    let temporary = parent.join(format!(".{}.tmp", benchmark.name));
    if temporary.exists() {
        fs::remove_dir_all(&temporary).map_err(|source| io_error("remove", &temporary, source))?;
    }
    fs::create_dir(&temporary).map_err(|source| io_error("create", &temporary, source))?;
    write_manifest(&temporary.join("manifest.json"), benchmark)?;
    fs::rename(&temporary, &target).map_err(|source| io_error("publish", &target, source))
}

fn directory_bytes(path: &Path) -> Result<u64> {
    let mut total = 0_u64;
    let mut pending = vec![path.to_owned()];
    while let Some(directory) = pending.pop() {
        for entry in
            fs::read_dir(&directory).map_err(|source| io_error("read", &directory, source))?
        {
            let entry = entry.map_err(|source| io_error("read", &directory, source))?;
            let metadata = entry
                .metadata()
                .map_err(|source| io_error("read metadata for", entry.path(), source))?;
            if metadata.is_dir() {
                pending.push(entry.path());
            } else if metadata.is_file() {
                total = total.checked_add(metadata.len()).ok_or_else(|| {
                    Error::Budget("benchmark artifact byte count overflowed".to_owned())
                })?;
            }
        }
    }
    Ok(total)
}

fn duration_nanoseconds(duration: Duration) -> Result<u64> {
    u64::try_from(duration.as_nanos())
        .map_err(|_| Error::Budget("benchmark duration does not fit u64".to_owned()))
}

fn cost_for_duration(nanoseconds: u64, hourly_rate: MicroUsd) -> Result<MicroUsd> {
    let numerator = u128::from(nanoseconds)
        .checked_mul(u128::from(hourly_rate.0))
        .ok_or_else(|| Error::Budget("rental cost overflowed".to_owned()))?;
    MicroUsd::try_from_u128(div_ceil(numerator, NANOS_PER_HOUR))
}

fn maximum_runtime(cost_cap: MicroUsd, hourly_rate: MicroUsd) -> Result<u64> {
    let numerator = u128::from(cost_cap.0)
        .checked_mul(NANOS_PER_HOUR)
        .ok_or_else(|| Error::Budget("benchmark runtime cap overflowed".to_owned()))?;
    u64::try_from(numerator / u128::from(hourly_rate.0))
        .map_err(|_| Error::Budget("benchmark runtime cap does not fit u64".to_owned()))
}

fn checked_sum(mut values: impl Iterator<Item = u64>, label: &str) -> Result<u64> {
    values.try_fold(0_u64, |sum, value| {
        sum.checked_add(value)
            .ok_or_else(|| Error::Budget(format!("{label} overflowed")))
    })
}

fn div_ceil(numerator: u128, denominator: u128) -> u128 {
    numerator / denominator + u128::from(!numerator.is_multiple_of(denominator))
}

fn validate_name(name: &str, label: &str) -> Result<()> {
    if !is_safe_artifact_name(name) {
        return Err(Error::Budget(format!(
            "{label} name `{name}` is not filesystem-safe"
        )));
    }
    Ok(())
}
