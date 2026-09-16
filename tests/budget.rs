use oracle_mvp::benchmark::{
    EmbeddingBenchmark, HardwareIdentity, PhaseTimings, TokenBatchShapeCount,
    TokenBatchShapeMeasurement, TokenBucketMeasurement, TokenBucketScheme,
};
use oracle_mvp::budget::{
    ArtifactIdentity, BudgetAdmissionRequest, MVP_HARD_BUDGET, MicroUsd, ProposedEmbeddingStage,
    admit_stage,
};
use oracle_mvp::embedding::{EncoderDescriptor, MATRIX_FORMAT};

const TEST_BATCH_SIZE: u32 = 50_000;

#[test]
fn stage_admission_projects_each_length_bucket_and_all_non_model_work() {
    let request = make_request(
        vec![bucket_count(64, 100_000), bucket_count(512, 100_000)],
        MicroUsd::from_dollars(950),
        MicroUsd::from_dollars(2),
    );
    let admission = admit_stage(&request).expect("stage remains under the hard budget");

    // The measured 100K-row shard spent 1s on 50K short rows, 9s on 50K long
    // rows, and 6s in non-model work. This 200K-row proposal therefore takes 32s.
    assert_eq!(admission.projected_runtime_nanoseconds, 32_000_000_000);
    assert_eq!(admission.projected_compute, MicroUsd(32_000));
    assert_eq!(admission.projected_stage, MicroUsd(2_032_000));
    assert_eq!(admission.projected_cumulative, MicroUsd(992_032_000));
    assert_eq!(admission.remaining_after_contingency, MicroUsd(7_968_000));
    assert_eq!(admission.hard_budget, MVP_HARD_BUDGET);
    assert!(!admission.identity_sha256.is_empty());
    assert_eq!(admit_stage(&request).expect("repeat admission"), admission);
}

#[test]
fn long_inputs_are_not_projected_at_aggregate_token_throughput() {
    let request = make_request(
        vec![bucket_count(64, 0), bucket_count(512, 200_000)],
        MicroUsd::from_dollars(0),
        MicroUsd::from_dollars(0),
    );
    let admission = admit_stage(&request).expect("long-only stage remains affordable");

    // Four long-bucket equivalents cost 36s of model time plus 12s overhead.
    assert_eq!(admission.projected_runtime_nanoseconds, 48_000_000_000);
    assert_eq!(admission.projected_compute, MicroUsd(48_000));
}

#[test]
fn partial_shard_and_batch_are_charged_as_whole_production_units() {
    let request = make_request(
        vec![bucket_count(64, 0), bucket_count(512, 1)],
        MicroUsd(0),
        MicroUsd(0),
    );
    let admission = admit_stage(&request).expect("one-row delta remains affordable");

    // One long batch costs 9s even with one row, and one partial new shard pays
    // the complete measured 6s non-model checkpoint/artifact overhead.
    assert_eq!(admission.projected_runtime_nanoseconds, 15_000_000_000);
}

#[test]
fn admission_rejects_a_full_target_batch_measured_only_as_a_partial_batch() {
    let mut request = make_request(
        vec![bucket_count(64, 0), bucket_count(512, 60_000)],
        MicroUsd(0),
        MicroUsd(0),
    );
    request.proposal.batch_size = 60_000;
    request.proposal.projected_buckets[1].batches = 1;
    request.proposal.projected_buckets[1].batch_shapes = vec![TokenBatchShapeCount {
        rows_per_batch: 60_000,
        padded_tokens_per_row: 512,
        batches: 1,
    }];
    request.benchmark.batch_size = 60_000;
    request.benchmark.buckets[0].rows = 60_000;
    request.benchmark.buckets[0].effective_tokens = 1_920_000;
    request.benchmark.buckets[0].padded_tokens = 3_840_000;
    request.benchmark.buckets[0].worst_batch_rows = 60_000;
    request.benchmark.buckets[0].batch_shapes = vec![TokenBatchShapeMeasurement {
        rows_per_batch: 60_000,
        padded_tokens_per_row: 64,
        batches: 1,
        maximum_elapsed_nanoseconds: 1_000_000_000,
    }];
    request.benchmark.buckets[1].rows = 40_000;
    request.benchmark.buckets[1].effective_tokens = 16_000_000;
    request.benchmark.buckets[1].padded_tokens = 20_480_000;
    request.benchmark.buckets[1].worst_batch_rows = 40_000;
    request.benchmark.buckets[1].batch_shapes = vec![TokenBatchShapeMeasurement {
        rows_per_batch: 40_000,
        padded_tokens_per_row: 512,
        batches: 1,
        maximum_elapsed_nanoseconds: 9_000_000_000,
    }];

    let error = admit_stage(&request)
        .expect_err("a full target batch needs a full calibration batch at its bucket ceiling");
    assert!(error.to_string().contains("full production batch"));
}

#[test]
fn admission_refuses_a_projection_over_the_fixed_mvp_budget() {
    let request = make_request(
        vec![bucket_count(64, 0), bucket_count(512, 5_000_000_000)],
        MicroUsd::from_dollars(450),
        MicroUsd::from_dollars(2),
    );
    let error = admit_stage(&request).expect_err("stage exceeds the fixed hard budget");
    assert!(error.to_string().contains("$1,000"));
}

#[test]
fn admission_rejects_missing_bucket_coverage_or_changed_build_identity() {
    let mut request = make_request(
        vec![bucket_count(64, 100_000), bucket_count(512, 100_000)],
        MicroUsd::from_dollars(0),
        MicroUsd::from_dollars(0),
    );
    request.benchmark.buckets[1].rows = 0;
    let error = admit_stage(&request).expect_err("projected bucket lacks a measurement");
    assert!(error.to_string().contains("bucket"));

    let mut request = make_request(
        vec![bucket_count(64, 100_000), bucket_count(512, 100_000)],
        MicroUsd::from_dollars(0),
        MicroUsd::from_dollars(0),
    );
    request.proposal.batch_size += 1;
    let error = admit_stage(&request).expect_err("benchmark must match proposed batching");
    assert!(error.to_string().contains("build"));

    let mut request = make_request(
        vec![bucket_count(64, 100_000), bucket_count(512, 100_000)],
        MicroUsd::from_dollars(0),
        MicroUsd::from_dollars(0),
    );
    request.proposal.encoder.input_rule = "changed".to_owned();
    let error = admit_stage(&request).expect_err("input rule is part of model identity");
    assert!(error.to_string().contains("encoder"));
}

fn make_request(
    projected_buckets: Vec<oracle_mvp::benchmark::TokenBucketCount>,
    completed_spend: MicroUsd,
    artifact_cost: MicroUsd,
) -> BudgetAdmissionRequest {
    let encoder = encoder();
    BudgetAdmissionRequest {
        completed_spend,
        managed_commitments_sha256: "02".repeat(32),
        reserved_contingency: MicroUsd::from_dollars(40),
        projected_artifact_and_transfer: artifact_cost,
        benchmark_artifact: ArtifactIdentity {
            path: "benchmarks/gpu-a/manifest.json".to_owned(),
            sha256: "ab".repeat(32),
        },
        proposal: ProposedEmbeddingStage {
            stage_name: "stage-2m".to_owned(),
            stage_manifest: ArtifactIdentity {
                path: "stages/stage-2m/manifest.json".to_owned(),
                sha256: "cd".repeat(32),
            },
            selected_rows_sha256: "rows".repeat(16),
            artifact_name: "pplx-stage-2m".to_owned(),
            base_artifact_name: Some("pplx-stage-1m".to_owned()),
            base_artifact_manifest_sha256: Some("ef".repeat(32)),
            encoder: encoder.clone(),
            batch_size: TEST_BATCH_SIZE,
            batching_rule: "effective-token-length-ascending-within-shard-v1".to_owned(),
            matrix_format: MATRIX_FORMAT.to_owned(),
            shard_rows: 100_000,
            proposed_new_rows: projected_buckets.iter().map(|bucket| bucket.rows).sum(),
            length_audit: ArtifactIdentity {
                path: "audits/stage-2m/manifest.json".to_owned(),
                sha256: "01".repeat(32),
            },
            bucket_scheme: TokenBucketScheme {
                upper_bounds: vec![64, 512],
            },
            projected_buckets,
        },
        benchmark: EmbeddingBenchmark {
            schema_version: 2,
            name: "gpu-a".to_owned(),
            artifact_name: "benchmark-artifact".to_owned(),
            artifact_manifest_sha256: "artifact".repeat(8),
            stage_name: "representative-100k".to_owned(),
            stage_manifest_sha256: "representative-stage".repeat(3),
            selected_rows_sha256: "representative-rows".repeat(3),
            encoder,
            batch_size: TEST_BATCH_SIZE,
            batching_rule: "effective-token-length-ascending-within-shard-v1".to_owned(),
            matrix_format: MATRIX_FORMAT.to_owned(),
            shard_rows: 100_000,
            total_artifact_rows: 100_000,
            newly_encoded_rows: 100_000,
            reused_rows: 0,
            newly_completed_shards: 1,
            reused_shards: 0,
            artifact_bytes: 102_400_000,
            hardware: HardwareIdentity {
                gpu_model: "fixture-gpu".to_owned(),
                gpu_device_uuid: "GPU-fixture".to_owned(),
                gpu_count: 1,
                driver_version: "fixture-driver".to_owned(),
                cuda_version: "fixture-cuda".to_owned(),
                host_cpu: "fixture-cpu".to_owned(),
                host_memory_bytes: 64 * 1024 * 1024 * 1024,
                rental_provider: "fixture-provider".to_owned(),
                rental_offer_id: "fixture-offer".to_owned(),
            },
            rental_rate_per_hour: MicroUsd(3_600_000),
            maximum_rental_cost: MicroUsd::from_dollars(1),
            bucket_scheme: TokenBucketScheme {
                upper_bounds: vec![64, 512],
            },
            buckets: vec![
                TokenBucketMeasurement {
                    upper_bound: 64,
                    rows: 50_000,
                    effective_tokens: 1_600_000,
                    padded_tokens: 3_200_000,
                    encode_elapsed_nanoseconds: 1_000_000_000,
                    batches: 1,
                    maximum_padded_tokens_per_row: 64,
                    worst_batch_rows: 50_000,
                    worst_batch_elapsed_nanoseconds: 1_000_000_000,
                    maximum_batch_elapsed_nanoseconds: 1_000_000_000,
                    batch_shapes: vec![TokenBatchShapeMeasurement {
                        rows_per_batch: TEST_BATCH_SIZE,
                        padded_tokens_per_row: 64,
                        batches: 1,
                        maximum_elapsed_nanoseconds: 1_000_000_000,
                    }],
                },
                TokenBucketMeasurement {
                    upper_bound: 512,
                    rows: 50_000,
                    effective_tokens: 20_000_000,
                    padded_tokens: 25_600_000,
                    encode_elapsed_nanoseconds: 9_000_000_000,
                    batches: 1,
                    maximum_padded_tokens_per_row: 512,
                    worst_batch_rows: 50_000,
                    worst_batch_elapsed_nanoseconds: 9_000_000_000,
                    maximum_batch_elapsed_nanoseconds: 9_000_000_000,
                    batch_shapes: vec![TokenBatchShapeMeasurement {
                        rows_per_batch: TEST_BATCH_SIZE,
                        padded_tokens_per_row: 512,
                        batches: 1,
                        maximum_elapsed_nanoseconds: 9_000_000_000,
                    }],
                },
            ],
            phases: PhaseTimings {
                effective_length_nanoseconds: 2_000_000_000,
                artifact_write_nanoseconds: 2_000_000_000,
                checkpoint_nanoseconds: 2_000_000_000,
                other_nanoseconds: 0,
                end_to_end_nanoseconds: 16_000_000_000,
            },
            measured_rental_cost: MicroUsd(16_000),
        },
    }
}

fn bucket_count(upper_bound: u32, rows: u64) -> oracle_mvp::benchmark::TokenBucketCount {
    let full_batches = rows / u64::from(TEST_BATCH_SIZE);
    let partial_rows = u32::try_from(rows % u64::from(TEST_BATCH_SIZE)).expect("partial rows");
    let mut batch_shapes = Vec::new();
    if partial_rows > 0 {
        batch_shapes.push(TokenBatchShapeCount {
            rows_per_batch: partial_rows,
            padded_tokens_per_row: upper_bound,
            batches: 1,
        });
    }
    if full_batches > 0 {
        batch_shapes.push(TokenBatchShapeCount {
            rows_per_batch: TEST_BATCH_SIZE,
            padded_tokens_per_row: upper_bound,
            batches: full_batches,
        });
    }
    oracle_mvp::benchmark::TokenBucketCount {
        upper_bound,
        rows,
        effective_tokens: rows.saturating_mul(u64::from(upper_bound)),
        batches: rows.div_ceil(u64::from(TEST_BATCH_SIZE)),
        batch_shapes,
    }
}

fn encoder() -> EncoderDescriptor {
    EncoderDescriptor {
        model_id: "perplexity-ai/pplx-embed-v1-0.6b".to_owned(),
        model_revision: "revision".to_owned(),
        model_lock_sha256: "model-lock".to_owned(),
        runtime: "onnxruntime".to_owned(),
        runtime_version: "fixture-runtime".to_owned(),
        runtime_sha256: "runtime".to_owned(),
        execution_provider: "cuda".to_owned(),
        output_name: "pooler_output_int8".to_owned(),
        dimensions: 1_024,
        max_tokens: 512,
        input_rule: "fixed-input-rule".to_owned(),
        pooling: "model-native-mean".to_owned(),
        quantization: "native-int8".to_owned(),
        instruction: None,
    }
}
