//! Deterministic admission control for rented embedding stages.

use std::fs::File;
use std::io::{BufReader, Read, Seek, SeekFrom};
use std::path::{Component, Path};

use serde::{Deserialize, Serialize};

use crate::artifact::{hash_bytes, hash_file, is_safe_artifact_name};
use crate::benchmark::{
    BENCHMARK_SCHEMA_VERSION, EmbeddingBenchmark, HardwareIdentity, TokenBatchShapeCount,
    TokenBucketCount, TokenBucketScheme, verify_measurements,
};
use crate::embedding::{
    EmbeddingBuildConfig, EmbeddingEncoder, EmbeddingManifest, EncoderDescriptor, MATRIX_FORMAT,
};
use crate::snapshot::{
    DamusSnapshot, Error, Result, create_directory, io_error, read_manifest, require_file,
    write_manifest,
};
use crate::token_audit::TokenAuditManifest;

const NANOS_PER_HOUR: u128 = 3_600_000_000_000;
const ADMISSION_SCHEMA_VERSION: u32 = 1;
pub(crate) const REQUIRED_BENCHMARK_ROWS: u64 = 100_000;
const REQUIRED_CONTINGENCY: MicroUsd = MicroUsd::from_dollars(40);
const MVP_RAW_TOKEN_INPUT_RULE: &str =
    "raw-utf8-url-text-empty-as-eot-add-special-tokens-no-truncation-no-padding-v1";
const MVP_RAW_TOKEN_LENGTH_RULE: &str = "tokenizer-output-ids-before-model-truncation-v1";
const MVP_ENCODER_INPUT_RULE: &str =
    "raw-utf8-url-text-empty-as-eot-add-special-tokens-right-truncate-512-v1";

/// The cumulative oracle-MVP spending cap cannot be raised by a runtime request.
pub const MVP_HARD_BUDGET: MicroUsd = MicroUsd::from_dollars(1_000);

/// Integer millionths of one US dollar.
#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(transparent)]
pub struct MicroUsd(pub u64);

impl MicroUsd {
    /// Construct an exact whole-dollar amount.
    pub const fn from_dollars(dollars: u64) -> Self {
        Self(dollars * 1_000_000)
    }

    /// Construct an exact whole-cent amount.
    pub const fn from_cents(cents: u64) -> Self {
        Self(cents * 10_000)
    }

    pub(crate) fn try_from_u128(value: u128) -> Result<Self> {
        u64::try_from(value)
            .map(Self)
            .map_err(|_| Error::Budget("cost does not fit u64 micro-USD".to_owned()))
    }
}

/// Immutable file identity relative to a snapshot data root.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct ArtifactIdentity {
    pub path: String,
    pub sha256: String,
}

/// Exact next embedding work whose launch is being considered.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct ProposedEmbeddingStage {
    pub stage_name: String,
    pub stage_manifest: ArtifactIdentity,
    pub selected_rows_sha256: String,
    pub artifact_name: String,
    pub base_artifact_name: Option<String>,
    pub base_artifact_manifest_sha256: Option<String>,
    pub encoder: EncoderDescriptor,
    pub batch_size: u32,
    pub batching_rule: String,
    pub matrix_format: String,
    pub shard_rows: u64,
    pub proposed_new_rows: u64,
    pub length_audit: ArtifactIdentity,
    pub bucket_scheme: TokenBucketScheme,
    /// Must equal the counts derived from the audit's stable row lengths for
    /// exactly `base_rows..target_rows` under this build's batching settings.
    pub projected_buckets: Vec<TokenBucketCount>,
}

/// Complete deterministic input to one stage-budget decision.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct BudgetAdmissionRequest {
    pub completed_spend: MicroUsd,
    /// Identity of every managed commitment present when this admission was planned.
    pub managed_commitments_sha256: String,
    pub reserved_contingency: MicroUsd,
    pub projected_artifact_and_transfer: MicroUsd,
    pub benchmark_artifact: ArtifactIdentity,
    pub proposal: ProposedEmbeddingStage,
    pub benchmark: EmbeddingBenchmark,
}

/// Operator inputs for an admission; all hashes, bucket counts, build settings,
/// and completed managed spend are derived from verified local artifacts.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct BudgetAdmissionConfig {
    pub benchmark_name: String,
    pub stage_name: String,
    pub artifact_name: String,
    pub base_artifact_name: Option<String>,
    pub token_audit_name: String,
    pub projected_artifact_and_transfer: MicroUsd,
}

/// Exact rented offer on which an admitted stage will execute.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct AdmittedExecutionConfig {
    pub hardware: HardwareIdentity,
    pub rental_rate_per_hour: MicroUsd,
}

/// Immutable, reproducible decision allowing one exact build and no other.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct BudgetAdmission {
    pub schema_version: u32,
    pub hard_budget: MicroUsd,
    pub request: BudgetAdmissionRequest,
    pub projected_runtime_nanoseconds: u64,
    pub projected_compute: MicroUsd,
    pub projected_stage: MicroUsd,
    /// Completed spend, proposed stage, and fixed failure contingency.
    pub projected_cumulative: MicroUsd,
    pub remaining_after_contingency: MicroUsd,
    pub identity_sha256: String,
}

/// Refuse a proposed stage unless every measured bucket fits under $1,000.
pub fn admit_stage(request: &BudgetAdmissionRequest) -> Result<BudgetAdmission> {
    validate_request(request)?;
    let benchmark = &request.benchmark;
    let model_nanoseconds = request
        .proposal
        .projected_buckets
        .iter()
        .try_fold(0_u128, |total, projected| {
            if projected.rows == 0 {
                return Ok(total);
            }
            let measured = benchmark
                .buckets
                .iter()
                .find(|bucket| bucket.upper_bound == projected.upper_bound)
                .ok_or_else(|| {
                    Error::Budget(format!(
                        "benchmark is missing token bucket {}",
                        projected.upper_bound
                    ))
                })?;
            if measured.rows == 0
                || measured.encode_elapsed_nanoseconds == 0
                || measured.worst_batch_rows == 0
                || measured.worst_batch_elapsed_nanoseconds == 0
            {
                return Err(Error::Budget(format!(
                    "benchmark has no conservative upper-bound production timing for token bucket {}",
                    projected.upper_bound
                )));
            }
            let full_ceiling_batch = measured.batch_shapes.iter().find(|shape| {
                shape.rows_per_batch == benchmark.batch_size
                    && shape.padded_tokens_per_row == measured.upper_bound
            });
            if full_ceiling_batch.is_none() {
                return Err(Error::Budget(format!(
                    "benchmark has no full production batch at the token bucket {} ceiling",
                    projected.upper_bound
                )));
            }
            let bucket_nanoseconds = u128::from(projected.batches)
                .checked_mul(u128::from(measured.maximum_batch_elapsed_nanoseconds))
                .ok_or_else(|| Error::Budget("bucket projection overflowed".to_owned()))?;
            total
                .checked_add(bucket_nanoseconds)
                .ok_or_else(|| Error::Budget("model projection overflowed".to_owned()))
        })?;
    let measured_model_nanoseconds =
        benchmark.buckets.iter().try_fold(0_u64, |total, bucket| {
            total
                .checked_add(bucket.encode_elapsed_nanoseconds)
                .ok_or_else(|| Error::Budget("benchmark model duration overflowed".to_owned()))
        })?;
    let measured_non_model_nanoseconds = benchmark
        .phases
        .end_to_end_nanoseconds
        .checked_sub(measured_model_nanoseconds)
        .ok_or_else(|| Error::Budget("benchmark phases exceed wall time".to_owned()))?;
    let proposed_shards = div_ceil(
        u128::from(request.proposal.proposed_new_rows),
        u128::from(benchmark.newly_encoded_rows),
    );
    let overhead_nanoseconds = proposed_shards
        .checked_mul(u128::from(measured_non_model_nanoseconds))
        .ok_or_else(|| Error::Budget("non-model projection overflowed".to_owned()))?;
    let projected_runtime = model_nanoseconds
        .checked_add(overhead_nanoseconds)
        .ok_or_else(|| Error::Budget("runtime projection overflowed".to_owned()))?;
    let projected_runtime_nanoseconds = u64::try_from(projected_runtime)
        .map_err(|_| Error::Budget("runtime projection does not fit u64".to_owned()))?;
    let projected_compute = MicroUsd::try_from_u128(div_ceil(
        projected_runtime
            .checked_mul(u128::from(benchmark.rental_rate_per_hour.0))
            .ok_or_else(|| Error::Budget("compute projection overflowed".to_owned()))?,
        NANOS_PER_HOUR,
    ))?;
    let projected_stage = checked_sum(
        projected_compute,
        request.projected_artifact_and_transfer,
        "projected stage cost",
    )?;
    let projected_cumulative = checked_sum(
        checked_sum(
            request.completed_spend,
            projected_stage,
            "projected cumulative spend",
        )?,
        REQUIRED_CONTINGENCY,
        "projected cumulative spend",
    )?;
    if projected_cumulative > MVP_HARD_BUDGET {
        return Err(Error::Budget(format!(
            "projected cumulative spend {} micro-USD exceeds the fixed $1,000 MVP hard budget",
            projected_cumulative.0
        )));
    }
    let remaining_after_contingency = MicroUsd(
        MVP_HARD_BUDGET
            .0
            .checked_sub(projected_cumulative.0)
            .expect("admitted cumulative spend is within hard budget"),
    );
    let unsigned = UnsignedAdmission {
        schema_version: ADMISSION_SCHEMA_VERSION,
        hard_budget: MVP_HARD_BUDGET,
        request,
        projected_runtime_nanoseconds,
        projected_compute,
        projected_stage,
        projected_cumulative,
        remaining_after_contingency,
    };
    let bytes = serde_json::to_vec(&unsigned).map_err(|source| {
        Error::Budget(format!(
            "failed to serialize deterministic budget admission: {source}"
        ))
    })?;
    Ok(BudgetAdmission {
        schema_version: unsigned.schema_version,
        hard_budget: unsigned.hard_budget,
        request: request.clone(),
        projected_runtime_nanoseconds,
        projected_compute,
        projected_stage,
        projected_cumulative,
        remaining_after_contingency,
        identity_sha256: hash_bytes(&bytes),
    })
}

#[derive(Serialize)]
struct UnsignedAdmission<'a> {
    schema_version: u32,
    hard_budget: MicroUsd,
    request: &'a BudgetAdmissionRequest,
    projected_runtime_nanoseconds: u64,
    projected_compute: MicroUsd,
    projected_stage: MicroUsd,
    projected_cumulative: MicroUsd,
    remaining_after_contingency: MicroUsd,
}

fn validate_request(request: &BudgetAdmissionRequest) -> Result<()> {
    let proposal = &request.proposal;
    let benchmark = &request.benchmark;
    if request.reserved_contingency != REQUIRED_CONTINGENCY {
        return Err(Error::Budget(
            "MVP admission requires the fixed $40 failure contingency".to_owned(),
        ));
    }
    if request.managed_commitments_sha256.len() != 64
        || !request
            .managed_commitments_sha256
            .bytes()
            .all(|byte| byte.is_ascii_hexdigit())
    {
        return Err(Error::Budget(
            "managed commitment identity must be a SHA-256 digest".to_owned(),
        ));
    }
    validate_identity(&request.benchmark_artifact)?;
    validate_identity(&proposal.stage_manifest)?;
    validate_identity(&proposal.length_audit)?;
    if !is_safe_artifact_name(&proposal.stage_name)
        || !is_safe_artifact_name(&proposal.artifact_name)
        || proposal
            .base_artifact_name
            .as_ref()
            .is_some_and(|name| !is_safe_artifact_name(name))
    {
        return Err(Error::Budget(
            "proposed stage or embedding artifact name is unsafe".to_owned(),
        ));
    }
    if proposal.base_artifact_name.is_some() != proposal.base_artifact_manifest_sha256.is_some() {
        return Err(Error::Budget(
            "base artifact name and manifest identity must be present together".to_owned(),
        ));
    }
    if proposal.batch_size == 0
        || proposal.shard_rows == 0
        || proposal.proposed_new_rows == 0
        || proposal.selected_rows_sha256.is_empty()
    {
        return Err(Error::Budget(
            "proposed build settings and row count must be positive".to_owned(),
        ));
    }
    if benchmark.schema_version != BENCHMARK_SCHEMA_VERSION
        || benchmark.newly_encoded_rows != REQUIRED_BENCHMARK_ROWS
        || benchmark.total_artifact_rows != REQUIRED_BENCHMARK_ROWS
        || benchmark.reused_rows != 0
        || benchmark.reused_shards != 0
        || benchmark.shard_rows != REQUIRED_BENCHMARK_ROWS
    {
        return Err(Error::Budget(
            "budget calibration requires a fresh representative 100,000-row production benchmark"
                .to_owned(),
        ));
    }
    if proposal.encoder != benchmark.encoder {
        return Err(Error::Budget(
            "benchmark encoder identity does not match the proposed encoder".to_owned(),
        ));
    }
    if proposal.encoder.execution_provider != "cuda" {
        return Err(Error::Budget(
            "rented embedding admission requires the CUDA provider".to_owned(),
        ));
    }
    if proposal.batch_size != benchmark.batch_size
        || proposal.batching_rule != benchmark.batching_rule
        || proposal.matrix_format != benchmark.matrix_format
        || proposal.matrix_format != MATRIX_FORMAT
        || proposal.shard_rows != benchmark.shard_rows
    {
        return Err(Error::Budget(
            "benchmark build settings do not match the proposed build".to_owned(),
        ));
    }
    if proposal.bucket_scheme != benchmark.bucket_scheme
        || proposal.projected_buckets.len() != proposal.bucket_scheme.upper_bounds.len()
        || proposal
            .projected_buckets
            .iter()
            .zip(&proposal.bucket_scheme.upper_bounds)
            .any(|(bucket, bound)| bucket.upper_bound != *bound)
    {
        return Err(Error::Budget(
            "audit projection and benchmark use incompatible token buckets".to_owned(),
        ));
    }
    let projected_rows = proposal
        .projected_buckets
        .iter()
        .try_fold(0_u64, |total, bucket| {
            total
                .checked_add(bucket.rows)
                .ok_or_else(|| Error::Budget("projected bucket rows overflowed".to_owned()))
        })?;
    if projected_rows != proposal.proposed_new_rows {
        return Err(Error::Budget(
            "projected token buckets do not cover exactly the proposed new rows".to_owned(),
        ));
    }
    for (index, bucket) in proposal.projected_buckets.iter().enumerate() {
        let previous_bound = index
            .checked_sub(1)
            .map_or(0, |previous| proposal.bucket_scheme.upper_bounds[previous]);
        validate_projected_bucket(bucket, previous_bound, proposal.batch_size)?;
    }
    verify_measurements(benchmark)?;
    Ok(())
}

fn validate_projected_bucket(
    bucket: &TokenBucketCount,
    previous_bound: u32,
    batch_size: u32,
) -> Result<()> {
    if bucket.rows == 0 {
        if bucket.effective_tokens != 0 || bucket.batches != 0 || !bucket.batch_shapes.is_empty() {
            return Err(Error::Budget(
                "empty projected bucket contains batch shapes".to_owned(),
            ));
        }
        return Ok(());
    }
    if bucket.effective_tokens < bucket.rows
        || bucket.batches == 0
        || bucket.batch_shapes.is_empty()
    {
        return Err(Error::Budget(
            "projected bucket batch shapes do not cover their rows".to_owned(),
        ));
    }
    let mut rows = 0_u64;
    let mut batches = 0_u64;
    let mut padded_tokens = 0_u64;
    let mut previous_shape = None;
    for shape in &bucket.batch_shapes {
        let key = (shape.rows_per_batch, shape.padded_tokens_per_row);
        if shape.rows_per_batch == 0
            || shape.rows_per_batch > batch_size
            || shape.padded_tokens_per_row <= previous_bound
            || shape.padded_tokens_per_row > bucket.upper_bound
            || shape.batches == 0
            || previous_shape.is_some_and(|previous| previous >= key)
        {
            return Err(Error::Budget(
                "projected bucket contains an invalid or duplicate batch shape".to_owned(),
            ));
        }
        previous_shape = Some(key);
        rows = rows
            .checked_add(
                u64::from(shape.rows_per_batch)
                    .checked_mul(shape.batches)
                    .ok_or_else(|| Error::Budget("projected shape rows overflowed".to_owned()))?,
            )
            .ok_or_else(|| Error::Budget("projected shape rows overflowed".to_owned()))?;
        batches = batches
            .checked_add(shape.batches)
            .ok_or_else(|| Error::Budget("projected shape count overflowed".to_owned()))?;
        padded_tokens = padded_tokens
            .checked_add(
                u64::from(shape.rows_per_batch)
                    .checked_mul(u64::from(shape.padded_tokens_per_row))
                    .and_then(|tokens| tokens.checked_mul(shape.batches))
                    .ok_or_else(|| Error::Budget("projected shape tokens overflowed".to_owned()))?,
            )
            .ok_or_else(|| Error::Budget("projected shape tokens overflowed".to_owned()))?;
    }
    if rows != bucket.rows || batches != bucket.batches || bucket.effective_tokens > padded_tokens {
        return Err(Error::Budget(
            "projected bucket aggregates do not match its exact batch shapes".to_owned(),
        ));
    }
    Ok(())
}

fn validate_identity(identity: &ArtifactIdentity) -> Result<()> {
    let path = Path::new(&identity.path);
    if identity.path.is_empty()
        || path.is_absolute()
        || path.components().any(|component| {
            matches!(
                component,
                Component::ParentDir | Component::RootDir | Component::Prefix(_)
            )
        })
        || identity.sha256.len() != 64
        || !identity.sha256.bytes().all(|byte| byte.is_ascii_hexdigit())
    {
        return Err(Error::Budget(
            "artifact identity must contain a safe relative path and SHA-256".to_owned(),
        ));
    }
    Ok(())
}

fn checked_sum(left: MicroUsd, right: MicroUsd, label: &str) -> Result<MicroUsd> {
    left.0
        .checked_add(right.0)
        .map(MicroUsd)
        .ok_or_else(|| Error::Budget(format!("{label} overflowed")))
}

fn div_ceil(numerator: u128, denominator: u128) -> u128 {
    numerator / denominator + u128::from(!numerator.is_multiple_of(denominator))
}

impl DamusSnapshot {
    /// Construct and publish an admission without caller-supplied provenance or
    /// completed-spend accounting.
    pub fn plan_and_publish_budget_admission(
        &self,
        name: &str,
        config: &BudgetAdmissionConfig,
    ) -> Result<BudgetAdmission> {
        validate_admission_name(name)?;
        for (value, label) in [
            (&config.benchmark_name, "benchmark"),
            (&config.stage_name, "stage"),
            (&config.artifact_name, "artifact"),
            (&config.token_audit_name, "token audit"),
        ] {
            if !is_safe_artifact_name(value) {
                return Err(Error::Budget(format!("{label} name is unsafe")));
            }
        }
        if config
            .base_artifact_name
            .as_ref()
            .is_some_and(|value| !is_safe_artifact_name(value))
        {
            return Err(Error::Budget("base artifact name is unsafe".to_owned()));
        }
        let benchmark = self.open_embedding_benchmark(&config.benchmark_name)?;
        let stage = self.open_corpus_stage(&config.stage_name)?;
        let base = match &config.base_artifact_name {
            Some(base_name) => Some((
                self.open_embedding_artifact(base_name)?,
                hash_file(&self.layout().embedding_manifest(base_name))?,
            )),
            None => None,
        };
        let base_rows = base.as_ref().map_or(0, |(manifest, _)| manifest.total_rows);
        let proposed_new_rows = stage
            .selected_rows
            .checked_sub(base_rows)
            .ok_or_else(|| Error::Budget("target stage is smaller than its base".to_owned()))?;
        let audit_path = self
            .layout()
            .root()
            .join("token-audits")
            .join(&config.token_audit_name)
            .join("manifest.json");
        require_file(&audit_path)?;
        let audit_identity = ArtifactIdentity {
            path: format!("token-audits/{}/manifest.json", config.token_audit_name),
            sha256: hash_file(&audit_path)?,
        };
        let unverified_audit: TokenAuditManifest = read_manifest(&audit_path)?;
        let audit =
            self.open_token_length_audit(&config.token_audit_name, &unverified_audit.tokenizer)?;
        let mut proposal = ProposedEmbeddingStage {
            stage_name: config.stage_name.clone(),
            stage_manifest: ArtifactIdentity {
                path: format!("stages/{}/manifest.json", config.stage_name),
                sha256: hash_file(&self.layout().corpus_stage_manifest(&config.stage_name))?,
            },
            selected_rows_sha256: stage.rows.sha256.clone(),
            artifact_name: config.artifact_name.clone(),
            base_artifact_name: config.base_artifact_name.clone(),
            base_artifact_manifest_sha256: base.as_ref().map(|(_, sha256)| sha256.clone()),
            encoder: benchmark.encoder.clone(),
            batch_size: benchmark.batch_size,
            batching_rule: benchmark.batching_rule.clone(),
            matrix_format: benchmark.matrix_format.clone(),
            shard_rows: benchmark.shard_rows,
            proposed_new_rows,
            length_audit: audit_identity,
            bucket_scheme: benchmark.bucket_scheme.clone(),
            projected_buckets: benchmark
                .bucket_scheme
                .upper_bounds
                .iter()
                .map(|upper_bound| TokenBucketCount {
                    upper_bound: *upper_bound,
                    rows: 0,
                    effective_tokens: 0,
                    batches: 0,
                    batch_shapes: Vec::new(),
                })
                .collect(),
        };
        proposal.projected_buckets = derive_projected_buckets(
            self.layout().root(),
            &config.token_audit_name,
            &audit,
            base_rows,
            stage.selected_rows,
            &proposal,
        )?;
        let managed = managed_commitment_state(self, None)?;
        let request = BudgetAdmissionRequest {
            completed_spend: managed.total,
            managed_commitments_sha256: managed.identity_sha256,
            reserved_contingency: REQUIRED_CONTINGENCY,
            projected_artifact_and_transfer: config.projected_artifact_and_transfer,
            benchmark_artifact: ArtifactIdentity {
                path: format!("benchmarks/{}/manifest.json", config.benchmark_name),
                sha256: hash_file(
                    &self
                        .layout()
                        .root()
                        .join("benchmarks")
                        .join(&config.benchmark_name)
                        .join("manifest.json"),
                )?,
            },
            proposal,
            benchmark,
        };
        self.publish_budget_admission(name, &request)
    }

    /// Verify all referenced artifacts, derive the exact delta buckets, and
    /// publish an immutable admission decision.
    pub fn publish_budget_admission(
        &self,
        name: &str,
        request: &BudgetAdmissionRequest,
    ) -> Result<BudgetAdmission> {
        validate_admission_name(name)?;
        self.validate_admission_artifacts(request)?;
        let admission = admit_stage(request)?;
        let root = self.layout().root().join("budget-admissions");
        create_directory(&root)?;
        let directory = root.join(name);
        let path = directory.join("manifest.json");
        if path.exists() {
            let existing: BudgetAdmission = read_manifest(&path)?;
            if existing != admission {
                return Err(Error::Budget(format!(
                    "budget admission `{name}` already names a different decision"
                )));
            }
            return Ok(existing);
        }
        if directory.exists() {
            return Err(Error::IncompleteStage(directory));
        }
        std::fs::create_dir(&directory).map_err(|source| io_error("create", &directory, source))?;
        write_manifest(&path, &admission)?;
        Ok(admission)
    }

    /// Reopen an admission and revalidate every artifact it authorizes.
    pub fn open_budget_admission(&self, name: &str) -> Result<BudgetAdmission> {
        validate_admission_name(name)?;
        let path = self
            .layout()
            .root()
            .join("budget-admissions")
            .join(name)
            .join("manifest.json");
        require_file(&path)?;
        let admission: BudgetAdmission = read_manifest(&path)?;
        if admission.schema_version != ADMISSION_SCHEMA_VERSION
            || admission.hard_budget != MVP_HARD_BUDGET
        {
            return Err(Error::Budget(
                "budget admission schema or fixed hard budget is invalid".to_owned(),
            ));
        }
        self.validate_admission_artifacts(&admission.request)?;
        let expected = admit_stage(&admission.request)?;
        if admission != expected {
            return Err(Error::Budget(
                "budget admission contents or identity are not reproducible".to_owned(),
            ));
        }
        Ok(admission)
    }

    /// Execute only the exact CUDA stage recorded by a verified admission.
    pub fn execute_budget_admission(
        &self,
        name: &str,
        execution: &AdmittedExecutionConfig,
        encoder: &mut dyn EmbeddingEncoder,
    ) -> Result<crate::embedding::EmbeddingManifest> {
        let admission = self.open_budget_admission(name)?;
        let proposal = &admission.request.proposal;
        if encoder.descriptor() != &proposal.encoder {
            return Err(Error::Budget(
                "runtime encoder does not match the admitted encoder identity".to_owned(),
            ));
        }
        if execution.hardware != admission.request.benchmark.hardware
            || execution.rental_rate_per_hour != admission.request.benchmark.rental_rate_per_hour
        {
            return Err(Error::Budget(
                "launch hardware, rented offer, or total hourly rate differs from the calibration benchmark"
                .to_owned(),
            ));
        }
        let config = EmbeddingBuildConfig {
            artifact_name: proposal.artifact_name.clone(),
            batch_size: usize::try_from(proposal.batch_size)
                .map_err(|_| Error::Budget("admitted batch size does not fit usize".to_owned()))?,
            shard_rows: proposal.shard_rows,
        };
        if self
            .layout()
            .embedding_dir(&proposal.artifact_name)
            .exists()
        {
            let manifest = execute_admitted_embedding(self, proposal, &config, encoder)?;
            verify_admitted_embedding(proposal, &manifest)?;
            return Ok(manifest);
        }

        let attempts = load_execution_attempts(self, &proposal.artifact_name)?;
        if attempts.iter().any(|attempt| {
            attempt.admission_name != name
                || attempt.admission_identity_sha256 != admission.identity_sha256
        }) {
            return Err(Error::Budget(
                "incomplete embedding artifact belongs to a different admitted execution"
                    .to_owned(),
            ));
        }
        let prior_attempt_cost = attempts.iter().try_fold(MicroUsd(0), |total, attempt| {
            checked_sum(total, attempt.projected_stage_cost, "prior attempt spend")
        })?;
        let unrelated = managed_commitment_state(self, Some(&proposal.artifact_name))?;
        if unrelated.total != admission.request.completed_spend
            || unrelated.identity_sha256 != admission.request.managed_commitments_sha256
        {
            return Err(Error::Budget(
                "managed commitments changed after this stage was admitted; create a new admission"
                    .to_owned(),
            ));
        }
        let charged = checked_sum(
            unrelated.total,
            prior_attempt_cost,
            "charged execution attempts",
        )?;
        let after_attempt = checked_sum(charged, admission.projected_stage, "charged attempt")?;
        let protected = checked_sum(
            after_attempt,
            REQUIRED_CONTINGENCY,
            "charged attempt and contingency",
        )?;
        if protected > MVP_HARD_BUDGET {
            return Err(Error::Budget(
                "another charged execution attempt plus contingency would exceed the fixed $1,000 MVP hard budget"
                    .to_owned(),
            ));
        }
        let ordinal = u32::try_from(attempts.len())
            .map_err(|_| Error::Budget("execution attempt ordinal does not fit u32".to_owned()))?;
        let attempt = ChargedExecutionAttempt {
            schema_version: 1,
            ordinal,
            admission_name: name.to_owned(),
            admission_identity_sha256: admission.identity_sha256.clone(),
            artifact_name: proposal.artifact_name.clone(),
            projected_stage_cost: admission.projected_stage,
            hardware: execution.hardware.clone(),
            rental_rate_per_hour: execution.rental_rate_per_hour,
        };
        persist_execution_attempt(self.layout().root(), &attempt)?;
        let manifest = execute_admitted_embedding(self, proposal, &config, encoder)?;
        verify_admitted_embedding(proposal, &manifest)?;
        Ok(manifest)
    }

    fn validate_admission_artifacts(&self, request: &BudgetAdmissionRequest) -> Result<()> {
        validate_request(request)?;
        verify_identity(self.layout().root(), &request.benchmark_artifact)?;
        verify_identity(self.layout().root(), &request.proposal.stage_manifest)?;
        verify_identity(self.layout().root(), &request.proposal.length_audit)?;

        let benchmark_name =
            exact_named_manifest(&request.benchmark_artifact.path, "benchmarks", "benchmark")?;
        let benchmark = self.open_embedding_benchmark(benchmark_name)?;
        if benchmark != request.benchmark {
            return Err(Error::Budget(
                "admission benchmark does not match its referenced manifest".to_owned(),
            ));
        }

        let proposal = &request.proposal;
        let expected_stage_path = format!("stages/{}/manifest.json", proposal.stage_name);
        if proposal.stage_manifest.path != expected_stage_path {
            return Err(Error::Budget(
                "proposed stage manifest path does not match its stage name".to_owned(),
            ));
        }
        let stage = self.open_corpus_stage(&proposal.stage_name)?;
        if stage.rows.sha256 != proposal.selected_rows_sha256
            || hash_file(&self.layout().corpus_stage_manifest(&proposal.stage_name))?
                != proposal.stage_manifest.sha256
        {
            return Err(Error::Budget(
                "proposed stage does not match its verified corpus artifact".to_owned(),
            ));
        }

        let base_rows = match (
            &proposal.base_artifact_name,
            &proposal.base_artifact_manifest_sha256,
        ) {
            (Some(name), Some(expected_sha256)) => {
                let base = self.open_embedding_artifact(name)?;
                let actual_sha256 = hash_file(&self.layout().embedding_manifest(name))?;
                if &actual_sha256 != expected_sha256
                    || base.encoder != proposal.encoder
                    || base.batch_size != proposal.batch_size
                    || base.batching_rule != proposal.batching_rule
                    || base.matrix_format != proposal.matrix_format
                    || base.shard_rows != proposal.shard_rows
                    || base.canonical_manifest_sha256 != stage.canonical_manifest_sha256
                    || base.canonical_rows_sha256 != stage.canonical_rows_sha256
                    || base.total_rows >= stage.selected_rows
                    || !base.total_rows.is_multiple_of(proposal.shard_rows)
                {
                    return Err(Error::Budget(
                        "base embedding artifact is not an aligned prefix of the proposed stage"
                            .to_owned(),
                    ));
                }
                base.total_rows
            }
            (None, None) => 0,
            _ => unreachable!("validated paired base identity"),
        };
        let new_rows = stage
            .selected_rows
            .checked_sub(base_rows)
            .ok_or_else(|| Error::Budget("proposed stage is smaller than its base".to_owned()))?;
        if new_rows != proposal.proposed_new_rows {
            return Err(Error::Budget(format!(
                "proposed new-row count {} does not match exact stage delta {new_rows}",
                proposal.proposed_new_rows
            )));
        }

        let audit_name =
            exact_named_manifest(&proposal.length_audit.path, "token-audits", "token audit")?;
        let audit_path = self
            .layout()
            .root()
            .join("token-audits")
            .join(audit_name)
            .join("manifest.json");
        let unverified_audit: TokenAuditManifest = read_manifest(&audit_path)?;
        let audit = self.open_token_length_audit(audit_name, &unverified_audit.tokenizer)?;
        if audit.tokenizer.model_id != proposal.encoder.model_id
            || audit.tokenizer.model_revision != proposal.encoder.model_revision
            || audit.tokenizer.model_lock_sha256 != proposal.encoder.model_lock_sha256
            || audit.tokenizer.model_token_ceiling != proposal.encoder.max_tokens
            || audit.tokenizer.input_rule != MVP_RAW_TOKEN_INPUT_RULE
            || audit.tokenizer.token_length_rule != MVP_RAW_TOKEN_LENGTH_RULE
            || proposal.encoder.input_rule != MVP_ENCODER_INPUT_RULE
            || audit.canonical_manifest_sha256 != stage.canonical_manifest_sha256
            || audit.canonical_rows_sha256 != stage.canonical_rows_sha256
            || audit.total_rows < stage.selected_rows
        {
            return Err(Error::Budget(
                "token audit does not cover the proposed stage with the admitted tokenizer"
                    .to_owned(),
            ));
        }
        let derived = derive_projected_buckets(
            self.layout().root(),
            audit_name,
            &audit,
            base_rows,
            stage.selected_rows,
            proposal,
        )?;
        if derived != proposal.projected_buckets {
            return Err(Error::Budget(
                "projected buckets were not derived from the exact audited stage delta".to_owned(),
            ));
        }
        Ok(())
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
struct ChargedExecutionAttempt {
    schema_version: u32,
    ordinal: u32,
    admission_name: String,
    admission_identity_sha256: String,
    artifact_name: String,
    projected_stage_cost: MicroUsd,
    hardware: HardwareIdentity,
    rental_rate_per_hour: MicroUsd,
}

fn persist_execution_attempt(root: &Path, attempt: &ChargedExecutionAttempt) -> Result<()> {
    let directory = execution_attempt_directory(root, &attempt.artifact_name);
    create_directory(&directory)?;
    let path = directory.join(format!("{:06}.json", attempt.ordinal));
    if path.exists() {
        return Err(Error::Budget(
            "charged execution attempt is immutable and already exists".to_owned(),
        ));
    }
    write_manifest(&path, attempt)
}

fn execution_attempt_directory(root: &Path, artifact_name: &str) -> std::path::PathBuf {
    root.join("admitted-attempts").join(artifact_name)
}

fn load_execution_attempts(
    pipeline: &DamusSnapshot,
    artifact_name: &str,
) -> Result<Vec<ChargedExecutionAttempt>> {
    if !is_safe_artifact_name(artifact_name) {
        return Err(Error::Budget(
            "execution attempt artifact name is unsafe".to_owned(),
        ));
    }
    let directory = execution_attempt_directory(pipeline.layout().root(), artifact_name);
    if !directory.exists() {
        return Ok(Vec::new());
    }
    let mut attempts = std::collections::BTreeMap::new();
    for entry in
        std::fs::read_dir(&directory).map_err(|source| io_error("read", &directory, source))?
    {
        let entry = entry.map_err(|source| io_error("read", &directory, source))?;
        let name = entry.file_name().into_string().map_err(|_| {
            Error::Budget("execution attempt ledger contains a non-UTF-8 name".to_owned())
        })?;
        let ordinal = name
            .strip_suffix(".json")
            .filter(|digits| digits.len() == 6 && digits.bytes().all(|byte| byte.is_ascii_digit()))
            .and_then(|digits| digits.parse::<u32>().ok())
            .ok_or_else(|| {
                Error::Budget(format!(
                    "execution attempt ledger contains unexpected entry `{name}`"
                ))
            })?;
        if !entry.path().is_file() {
            return Err(Error::Budget(format!(
                "execution attempt `{name}` is not a regular file"
            )));
        }
        let attempt: ChargedExecutionAttempt = read_manifest(&entry.path())?;
        if attempt.schema_version != 1
            || attempt.ordinal != ordinal
            || attempt.artifact_name != artifact_name
            || attempt.projected_stage_cost.0 == 0
            || attempt.rental_rate_per_hour.0 == 0
        {
            return Err(Error::Budget(format!(
                "execution attempt `{name}` has invalid accounting identity"
            )));
        }
        let admission = pipeline.open_budget_admission(&attempt.admission_name)?;
        if attempt.admission_identity_sha256 != admission.identity_sha256
            || attempt.artifact_name != admission.request.proposal.artifact_name
            || attempt.projected_stage_cost != admission.projected_stage
            || attempt.hardware != admission.request.benchmark.hardware
            || attempt.rental_rate_per_hour != admission.request.benchmark.rental_rate_per_hour
        {
            return Err(Error::Budget(format!(
                "execution attempt `{name}` does not match its verified admission"
            )));
        }
        if attempts.insert(ordinal, attempt).is_some() {
            return Err(Error::Budget(
                "execution attempt ledger contains a duplicate ordinal".to_owned(),
            ));
        }
    }
    let mut ordered = Vec::with_capacity(attempts.len());
    for (expected, (ordinal, attempt)) in (0_u32..).zip(attempts) {
        if ordinal != expected {
            return Err(Error::Budget(
                "execution attempt ledger ordinals are not contiguous".to_owned(),
            ));
        }
        ordered.push(attempt);
    }
    Ok(ordered)
}

fn execute_admitted_embedding(
    pipeline: &DamusSnapshot,
    proposal: &ProposedEmbeddingStage,
    config: &EmbeddingBuildConfig,
    encoder: &mut dyn EmbeddingEncoder,
) -> Result<EmbeddingManifest> {
    match &proposal.base_artifact_name {
        Some(base) => {
            pipeline.extend_corpus_stage_admitted(base, &proposal.stage_name, config, encoder)
        }
        None => pipeline.embed_corpus_stage_admitted(&proposal.stage_name, config, encoder),
    }
}

fn verify_admitted_embedding(
    proposal: &ProposedEmbeddingStage,
    manifest: &EmbeddingManifest,
) -> Result<()> {
    if manifest.encoder != proposal.encoder
        || manifest.batch_size != proposal.batch_size
        || manifest.batching_rule != proposal.batching_rule
        || manifest.matrix_format != proposal.matrix_format
        || manifest.shard_rows != proposal.shard_rows
        || manifest.corpus_stage.as_ref().is_none_or(|stage| {
            stage.name != proposal.stage_name
                || stage.manifest_sha256 != proposal.stage_manifest.sha256
                || stage.rows_sha256 != proposal.selected_rows_sha256
        })
    {
        return Err(Error::Budget(
            "completed embedding artifact does not match its admitted configuration".to_owned(),
        ));
    }
    Ok(())
}

fn verify_identity(root: &Path, identity: &ArtifactIdentity) -> Result<()> {
    validate_identity(identity)?;
    let path = root.join(&identity.path);
    require_file(&path)?;
    if hash_file(&path)? != identity.sha256 {
        return Err(Error::Budget(format!(
            "artifact identity for `{}` does not match the file",
            identity.path
        )));
    }
    Ok(())
}

fn exact_named_manifest<'a>(path: &'a str, parent: &str, label: &str) -> Result<&'a str> {
    let components = Path::new(path).components().collect::<Vec<_>>();
    if components.len() != 3
        || components[0].as_os_str() != parent
        || components[2].as_os_str() != "manifest.json"
    {
        return Err(Error::Budget(format!(
            "{label} identity must name `{parent}/NAME/manifest.json`"
        )));
    }
    components[1]
        .as_os_str()
        .to_str()
        .filter(|name| is_safe_artifact_name(name))
        .ok_or_else(|| Error::Budget(format!("{label} name is invalid UTF-8 or unsafe")))
}

fn derive_projected_buckets(
    root: &Path,
    audit_name: &str,
    audit: &TokenAuditManifest,
    start_row: u64,
    end_row: u64,
    proposal: &ProposedEmbeddingStage,
) -> Result<Vec<TokenBucketCount>> {
    let mut totals = proposal
        .bucket_scheme
        .upper_bounds
        .iter()
        .map(|bound| (*bound, ProjectedBucketTotals::default()))
        .collect::<std::collections::BTreeMap<_, _>>();
    let batch_size = usize::try_from(proposal.batch_size)
        .map_err(|_| Error::Budget("batch size does not fit usize".to_owned()))?;
    let mut shard_start = start_row;
    while shard_start < end_row {
        let shard_end = shard_start
            .checked_add(proposal.shard_rows)
            .map_or(end_row, |end| end.min(end_row));
        let mut lengths = read_audit_lengths(root, audit_name, audit, shard_start, shard_end)?;
        for length in &mut lengths {
            *length = (*length).min(proposal.encoder.max_tokens);
            if *length == 0 {
                return Err(Error::Budget(
                    "token audit contains a zero-length model input".to_owned(),
                ));
            }
        }
        lengths.sort_unstable();
        for batch in lengths.chunks(batch_size) {
            let maximum = *batch.last().expect("delta shard is nonempty");
            let upper_bound = proposal
                .bucket_scheme
                .upper_bounds
                .iter()
                .copied()
                .find(|bound| maximum <= *bound)
                .ok_or_else(|| {
                    Error::Budget(format!(
                        "effective length {maximum} is outside the admitted bucket scheme"
                    ))
                })?;
            let rows = u64::try_from(batch.len())
                .map_err(|_| Error::Budget("batch row count does not fit u64".to_owned()))?;
            let tokens = batch.iter().try_fold(0_u64, |sum, length| {
                sum.checked_add(u64::from(*length))
                    .ok_or_else(|| Error::Budget("bucket token count overflowed".to_owned()))
            })?;
            let total = totals.get_mut(&upper_bound).expect("known bucket");
            total.rows = total
                .rows
                .checked_add(rows)
                .ok_or_else(|| Error::Budget("bucket row count overflowed".to_owned()))?;
            total.effective_tokens = total
                .effective_tokens
                .checked_add(tokens)
                .ok_or_else(|| Error::Budget("bucket token count overflowed".to_owned()))?;
            total.batches = total
                .batches
                .checked_add(1)
                .ok_or_else(|| Error::Budget("bucket batch count overflowed".to_owned()))?;
            let rows_per_batch = u32::try_from(batch.len())
                .map_err(|_| Error::Budget("batch row count does not fit u32".to_owned()))?;
            let shape_batches = total
                .batch_shapes
                .entry((rows_per_batch, maximum))
                .or_default();
            *shape_batches = shape_batches
                .checked_add(1)
                .ok_or_else(|| Error::Budget("batch-shape count overflowed".to_owned()))?;
        }
        shard_start = shard_end;
    }
    Ok(proposal
        .bucket_scheme
        .upper_bounds
        .iter()
        .map(|upper_bound| {
            let total = &totals[upper_bound];
            TokenBucketCount {
                upper_bound: *upper_bound,
                rows: total.rows,
                effective_tokens: total.effective_tokens,
                batches: total.batches,
                batch_shapes: total
                    .batch_shapes
                    .iter()
                    .map(|((rows_per_batch, padded_tokens_per_row), batches)| {
                        TokenBatchShapeCount {
                            rows_per_batch: *rows_per_batch,
                            padded_tokens_per_row: *padded_tokens_per_row,
                            batches: *batches,
                        }
                    })
                    .collect(),
            }
        })
        .collect())
}

#[derive(Default)]
struct ProjectedBucketTotals {
    rows: u64,
    effective_tokens: u64,
    batches: u64,
    batch_shapes: std::collections::BTreeMap<(u32, u32), u64>,
}

fn read_audit_lengths(
    root: &Path,
    audit_name: &str,
    audit: &TokenAuditManifest,
    start_row: u64,
    end_row: u64,
) -> Result<Vec<u32>> {
    let count = end_row
        .checked_sub(start_row)
        .ok_or_else(|| Error::Budget("invalid audit row range".to_owned()))?;
    let mut lengths = Vec::with_capacity(
        usize::try_from(count)
            .map_err(|_| Error::Budget("audit row range does not fit memory".to_owned()))?,
    );
    let audit_root = root.join("token-audits").join(audit_name);
    for shard in &audit.shards {
        let shard_end = shard
            .start_row
            .checked_add(shard.rows)
            .ok_or_else(|| Error::Budget("audit shard range overflowed".to_owned()))?;
        let overlap_start = start_row.max(shard.start_row);
        let overlap_end = end_row.min(shard_end);
        if overlap_start >= overlap_end {
            continue;
        }
        let path = audit_root.join(&shard.row_lengths.file);
        let mut reader =
            BufReader::new(File::open(&path).map_err(|source| io_error("open", &path, source))?);
        let byte_offset = overlap_start
            .checked_sub(shard.start_row)
            .and_then(|rows| rows.checked_mul(4))
            .ok_or_else(|| Error::Budget("audit length offset overflowed".to_owned()))?;
        reader
            .seek(SeekFrom::Start(byte_offset))
            .map_err(|source| io_error("seek", &path, source))?;
        for _ in overlap_start..overlap_end {
            let mut bytes = [0_u8; 4];
            reader
                .read_exact(&mut bytes)
                .map_err(|source| io_error("read", &path, source))?;
            lengths.push(u32::from_le_bytes(bytes));
        }
    }
    if lengths.len()
        != usize::try_from(count)
            .map_err(|_| Error::Budget("audit row range does not fit usize".to_owned()))?
    {
        return Err(Error::Budget(
            "token audit shards do not cover the exact proposed row range".to_owned(),
        ));
    }
    Ok(lengths)
}

fn validate_admission_name(name: &str) -> Result<()> {
    if !is_safe_artifact_name(name) {
        return Err(Error::Budget(format!(
            "budget admission name `{name}` is not filesystem-safe"
        )));
    }
    Ok(())
}

fn managed_budget_commitments(pipeline: &DamusSnapshot) -> Result<MicroUsd> {
    Ok(managed_commitment_state(pipeline, None)?.total)
}

struct ManagedCommitmentState {
    total: MicroUsd,
    identity_sha256: String,
}

#[derive(Serialize)]
struct ManagedCommitmentRecord {
    cost: MicroUsd,
    artifact_sha256: String,
}

fn managed_commitment_state(
    pipeline: &DamusSnapshot,
    excluded_attempt_artifact: Option<&str>,
) -> Result<ManagedCommitmentState> {
    let mut completed = MicroUsd(0);
    let mut active = MicroUsd(0);
    let mut records = std::collections::BTreeMap::new();
    let benchmark_root = pipeline.layout().root().join("benchmarks");
    if benchmark_root.exists() {
        for entry in std::fs::read_dir(&benchmark_root)
            .map_err(|source| io_error("read", &benchmark_root, source))?
        {
            let entry = entry.map_err(|source| io_error("read", &benchmark_root, source))?;
            if entry.file_name().to_string_lossy().starts_with('.') {
                continue;
            }
            if !entry
                .file_type()
                .map_err(|source| io_error("read metadata for", entry.path(), source))?
                .is_dir()
            {
                return Err(Error::Budget(
                    "benchmark ledger contains a non-directory entry".to_owned(),
                ));
            }
            let name = entry.file_name().into_string().map_err(|_| {
                Error::Budget("benchmark ledger contains a non-UTF-8 name".to_owned())
            })?;
            validate_admission_name(&name)?;
            let benchmark = pipeline.open_embedding_benchmark(&name)?;
            completed = checked_sum(
                completed,
                benchmark.measured_rental_cost,
                "managed completed spend",
            )?;
            records.insert(
                format!("benchmark/{name}"),
                ManagedCommitmentRecord {
                    cost: benchmark.measured_rental_cost,
                    artifact_sha256: hash_file(&entry.path().join("manifest.json"))?,
                },
            );
        }
    }
    let attempt_root = pipeline.layout().root().join("admitted-attempts");
    if attempt_root.exists() {
        for entry in std::fs::read_dir(&attempt_root)
            .map_err(|source| io_error("read", &attempt_root, source))?
        {
            let entry = entry.map_err(|source| io_error("read", &attempt_root, source))?;
            if !entry
                .file_type()
                .map_err(|source| io_error("read metadata for", entry.path(), source))?
                .is_dir()
            {
                return Err(Error::Budget(
                    "execution attempt ledger contains a non-directory artifact".to_owned(),
                ));
            }
            let artifact_name = entry.file_name().into_string().map_err(|_| {
                Error::Budget("execution attempt ledger contains a non-UTF-8 artifact".to_owned())
            })?;
            if !is_safe_artifact_name(&artifact_name) {
                return Err(Error::Budget(
                    "execution attempt ledger contains an unsafe artifact name".to_owned(),
                ));
            }
            let attempts = load_execution_attempts(pipeline, &artifact_name)?;
            if excluded_attempt_artifact == Some(artifact_name.as_str()) {
                continue;
            }
            for attempt in attempts {
                completed = checked_sum(
                    completed,
                    attempt.projected_stage_cost,
                    "managed completed spend",
                )?;
                let path = execution_attempt_directory(pipeline.layout().root(), &artifact_name)
                    .join(format!("{:06}.json", attempt.ordinal));
                records.insert(
                    format!("attempt/{artifact_name}/{:06}", attempt.ordinal),
                    ManagedCommitmentRecord {
                        cost: attempt.projected_stage_cost,
                        artifact_sha256: hash_file(&path)?,
                    },
                );
            }
        }
    }
    let reservation_root = pipeline.layout().root().join("budget-reservations");
    if reservation_root.exists() {
        for entry in std::fs::read_dir(&reservation_root)
            .map_err(|source| io_error("read", &reservation_root, source))?
        {
            let entry = entry.map_err(|source| io_error("read", &reservation_root, source))?;
            if !entry
                .file_type()
                .map_err(|source| io_error("read metadata for", entry.path(), source))?
                .is_file()
            {
                return Err(Error::Budget(
                    "benchmark reservation ledger contains a non-file entry".to_owned(),
                ));
            }
            let reservation: BenchmarkReservation = read_manifest(&entry.path())?;
            let expected_name = format!("benchmark-{}.json", reservation.benchmark_name);
            if reservation.schema_version != 1
                || reservation.maximum_rental_cost.0 == 0
                || !is_safe_artifact_name(&reservation.benchmark_name)
                || entry.file_name().to_string_lossy() != expected_name
            {
                return Err(Error::Budget(
                    "benchmark reservation has invalid accounting identity".to_owned(),
                ));
            }
            let completed_benchmark = pipeline
                .layout()
                .root()
                .join("benchmarks")
                .join(&reservation.benchmark_name)
                .join("manifest.json");
            if completed_benchmark.exists() {
                continue;
            }
            active = checked_sum(
                active,
                reservation.maximum_rental_cost,
                "active benchmark reservations",
            )?;
            records.insert(
                format!("reservation/{}", reservation.benchmark_name),
                ManagedCommitmentRecord {
                    cost: reservation.maximum_rental_cost,
                    artifact_sha256: hash_file(&entry.path())?,
                },
            );
        }
    }
    let total = checked_sum(completed, active, "managed budget commitments")?;
    let encoded = serde_json::to_vec(&records).map_err(|source| {
        Error::Budget(format!(
            "failed to serialize managed commitment identity: {source}"
        ))
    })?;
    Ok(ManagedCommitmentState {
        total,
        identity_sha256: hash_bytes(&encoded),
    })
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
struct BenchmarkReservation {
    schema_version: u32,
    benchmark_name: String,
    maximum_rental_cost: MicroUsd,
}

pub(crate) fn reserve_benchmark_budget(
    pipeline: &DamusSnapshot,
    name: &str,
    maximum_rental_cost: MicroUsd,
) -> Result<()> {
    validate_admission_name(name)?;
    let directory = pipeline.layout().root().join("budget-reservations");
    create_directory(&directory)?;
    let path = directory.join(format!("benchmark-{name}.json"));
    let reservation = BenchmarkReservation {
        schema_version: 1,
        benchmark_name: name.to_owned(),
        maximum_rental_cost,
    };
    if path.exists() {
        let existing: BenchmarkReservation = read_manifest(&path)?;
        if existing != reservation {
            return Err(Error::Budget(
                "benchmark already has a different budget reservation".to_owned(),
            ));
        }
        return Err(Error::Budget(
            "unfinished benchmark reservation is one-shot; use a new benchmark name after inspecting the failed run"
                .to_owned(),
        ));
    }
    let active = active_benchmark_reservations(pipeline)?;
    let completed_benchmarks = completed_benchmark_spend(pipeline)?;
    let phase_with_new = checked_sum(
        checked_sum(completed_benchmarks, active, "benchmark phase spend")?,
        maximum_rental_cost,
        "benchmark phase spend",
    )?;
    if phase_with_new > MicroUsd::from_dollars(40) {
        return Err(Error::Budget(
            "benchmark reservation would exceed the cumulative $40 benchmark-phase cap".to_owned(),
        ));
    }
    let committed = managed_budget_commitments(pipeline)?;
    let with_new = checked_sum(committed, maximum_rental_cost, "reserved spend")?;
    let with_contingency = checked_sum(with_new, REQUIRED_CONTINGENCY, "reserved spend")?;
    if with_contingency > MVP_HARD_BUDGET {
        return Err(Error::Budget(
            "benchmark reservation would exceed the fixed $1,000 MVP hard budget".to_owned(),
        ));
    }
    write_manifest(&path, &reservation)
}

pub(crate) fn release_benchmark_budget(pipeline: &DamusSnapshot, name: &str) -> Result<()> {
    let path = pipeline
        .layout()
        .root()
        .join("budget-reservations")
        .join(format!("benchmark-{name}.json"));
    if path.exists() {
        std::fs::remove_file(&path).map_err(|source| io_error("remove", &path, source))?;
    }
    Ok(())
}

fn active_benchmark_reservations(pipeline: &DamusSnapshot) -> Result<MicroUsd> {
    let root = pipeline.layout().root().join("budget-reservations");
    if !root.exists() {
        return Ok(MicroUsd(0));
    }
    let mut total = MicroUsd(0);
    for entry in std::fs::read_dir(&root).map_err(|source| io_error("read", &root, source))? {
        let entry = entry.map_err(|source| io_error("read", &root, source))?;
        if !entry.path().is_file() {
            continue;
        }
        let reservation: BenchmarkReservation = read_manifest(&entry.path())?;
        let completed = pipeline
            .layout()
            .root()
            .join("benchmarks")
            .join(&reservation.benchmark_name)
            .join("manifest.json");
        if !completed.exists() {
            total = checked_sum(
                total,
                reservation.maximum_rental_cost,
                "benchmark reservations",
            )?;
        }
    }
    Ok(total)
}

fn completed_benchmark_spend(pipeline: &DamusSnapshot) -> Result<MicroUsd> {
    let root = pipeline.layout().root().join("benchmarks");
    if !root.exists() {
        return Ok(MicroUsd(0));
    }
    let mut total = MicroUsd(0);
    for entry in std::fs::read_dir(&root).map_err(|source| io_error("read", &root, source))? {
        let entry = entry.map_err(|source| io_error("read", &root, source))?;
        if !entry.path().is_dir() || entry.file_name().to_string_lossy().starts_with('.') {
            continue;
        }
        let name = entry
            .file_name()
            .into_string()
            .map_err(|_| Error::Budget("benchmark ledger contains a non-UTF-8 name".to_owned()))?;
        let benchmark = pipeline.open_embedding_benchmark(&name)?;
        total = checked_sum(
            total,
            benchmark.measured_rental_cost,
            "benchmark phase spend",
        )?;
    }
    Ok(total)
}
