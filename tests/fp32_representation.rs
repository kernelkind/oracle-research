use std::fs::{self, File, OpenOptions};
use std::io::Write;
use std::process::Command;
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::{Duration, Instant};

use nostrdb::{Config, Filter, Ndb, NoteBuilder, Transaction};
use oracle_mvp::fp32_oracle::{Fp32OfflineOracle, SimilarNotesRequest, vectors_for_notes};
use oracle_mvp::gte::TokenRole;
use oracle_mvp::ordered_gte_token_audit::{
    OrderedGteTokenAuditConfig, OrderedGteTokenCounter, audit_ordered_gte_tokens,
};
use oracle_mvp::representation::{
    RepresentationArtifactPhase, RepresentationBatchShape, RepresentationBuildConfig,
    RepresentationBuildObserver, RepresentationDescriptor, RepresentationEncoder,
    build_representation_shards, build_representation_shards_observed, complete_representation,
    open_representation, prepare_representation_index, verify_representation,
};
use oracle_mvp::representation_batch_plan::{
    RepresentationBatchPlanConfig, create_representation_batch_plan,
};
use oracle_mvp::snapshot::{Error, Result};

#[test]
fn publishes_nonadjacent_shards_and_resumes_without_reencoding() {
    let fixture = Fixture::new();
    let artifact = fixture.temp.path().join("representation");
    let calls = Arc::new(Mutex::new(Vec::new()));
    let mut encoder = FixtureEncoder::new(calls.clone());
    let config = fixture.build_config("resume-plan", 2, 1, vec![0, 2]);

    let first = build_representation_shards(
        &fixture.ndb_path,
        &fixture.ordered_path,
        &artifact,
        &config,
        &mut encoder,
    )
    .expect("build calibration shards");
    assert_eq!(first.encoded_rows, 4);
    assert_eq!(first.reused_rows, 0);
    assert_eq!(first.manifest.shards.len(), 2);
    assert!(!first.manifest.complete);
    assert_eq!(calls.lock().expect("call log").len(), 4);
    let first_bytes =
        fs::read(artifact.join("shards/000000/vectors.f32le")).expect("first shard bytes");

    let resumed = build_representation_shards(
        &fixture.ndb_path,
        &fixture.ordered_path,
        &artifact,
        &config,
        &mut encoder,
    )
    .expect("resume calibration shards");
    assert_eq!(resumed.encoded_rows, 0);
    assert_eq!(resumed.reused_rows, 4);
    assert_eq!(calls.lock().expect("call log").len(), 4);
    assert_eq!(
        fs::read(artifact.join("shards/000000/vectors.f32le")).expect("resumed first shard bytes"),
        first_bytes
    );

    let completed = build_representation_shards(
        &fixture.ndb_path,
        &fixture.ordered_path,
        &artifact,
        &fixture.build_config("resume-plan", 2, 1, vec![1]),
        &mut encoder,
    )
    .expect("complete representation");
    assert!(completed.manifest.complete);
    assert_eq!(completed.manifest.completed_rows, 6);
    assert_eq!(completed.manifest.shards.len(), 3);

    let opened = open_representation(&fixture.ordered_path, &artifact)
        .expect("open completed representation");
    assert_eq!(
        opened.representation_version(),
        completed.representation_version
    );

    let mut cuda_encoder = FixtureEncoder::new(Arc::new(Mutex::new(Vec::new())));
    cuda_encoder.descriptor.execution_device = "cuda".to_owned();
    build_representation_shards(
        &fixture.ndb_path,
        &fixture.ordered_path,
        &artifact,
        &fixture.build_config("resume-plan", 2, 1, vec![0]),
        &mut cuda_encoder,
    )
    .expect_err("CPU and CUDA shards must not share a representation identity");

    let vectors_path = artifact.join("shards/000002/vectors.f32le");
    let mut corrupted = fs::read(&vectors_path).expect("read vectors");
    corrupted[0] ^= 1;
    fs::write(&vectors_path, corrupted).expect("corrupt vectors");
    open_representation(&fixture.ordered_path, &artifact)
        .expect_err("corrupt immutable shard must be rejected");
}

#[test]
fn complete_representation_reuses_the_existing_middle_shard() {
    let fixture = Fixture::new();
    let artifact = fixture.temp.path().join("complete-from-middle");
    let calls = Arc::new(Mutex::new(Vec::new()));
    let mut encoder = FixtureEncoder::new(calls.clone());
    let config = fixture.build_config("complete-from-middle-plan", 2, 1, vec![1]);
    let partial = build_representation_shards(
        &fixture.ndb_path,
        &fixture.ordered_path,
        &artifact,
        &config,
        &mut encoder,
    )
    .expect("build reusable middle shard");
    assert_eq!(partial.encoded_rows, 2);
    assert!(!partial.manifest.complete);
    let middle_vectors =
        fs::read(artifact.join("shards/000001/vectors.f32le")).expect("read reusable vectors");

    let completed = complete_representation(
        &fixture.ndb_path,
        &fixture.ordered_path,
        &artifact,
        &config.token_audit_path,
        &config.batch_plan_path,
        &mut encoder,
    )
    .expect("complete every missing shard");
    assert!(completed.manifest.complete);
    assert_eq!(completed.encoded_rows, 4);
    assert_eq!(completed.reused_rows, 2);
    assert_eq!(calls.lock().expect("call log").len(), 6);
    assert_eq!(
        fs::read(artifact.join("shards/000001/vectors.f32le")).expect("read reused middle vectors"),
        middle_vectors,
    );
}

#[test]
fn oracle_uses_query_role_and_returns_exact_stored_vectors() {
    let fixture = Fixture::new();
    let artifact = fixture.temp.path().join("representation");
    let mut build_encoder = FixtureEncoder::new(Arc::new(Mutex::new(Vec::new())));
    let built = build_representation_shards(
        &fixture.ndb_path,
        &fixture.ordered_path,
        &artifact,
        &fixture.build_config("oracle-plan", 2, 2, vec![0, 1, 2]),
        &mut build_encoder,
    )
    .expect("build complete fixture representation");

    let query_calls = Arc::new(Mutex::new(Vec::new()));
    let query_encoder = FixtureEncoder::new(query_calls.clone());
    let mut oracle = Fp32OfflineOracle::open(
        &fixture.ndb_path,
        &fixture.ordered_path,
        &artifact,
        query_encoder,
    )
    .expect("open oracle");

    let response = oracle
        .similar_notes(fixture.ids[0], 3, &built.representation_version)
        .expect("query similar notes");
    assert_eq!(
        response.representation_version,
        built.representation_version
    );
    assert!(response.complete);
    assert_eq!(response.represented_rows, 6);
    assert_eq!(response.total_rows, 6);
    assert_eq!(response.candidates[0].event_id, fixture.ids[2]);
    assert_eq!(
        response
            .candidates
            .iter()
            .map(|candidate| candidate.rank)
            .collect::<Vec<_>>(),
        vec![1, 2, 3]
    );
    assert!(
        !response
            .candidates
            .iter()
            .any(|candidate| candidate.event_id == fixture.ids[0])
    );
    assert_eq!(
        *query_calls.lock().expect("query call log"),
        vec!["note-0".to_owned()]
    );

    let requested = [fixture.ids[4], fixture.ids[1]];
    let vectors = oracle
        .vectors_for_notes(&requested, &built.representation_version)
        .expect("batch vector lookup");
    assert_eq!(vectors.representation_version, built.representation_version);
    assert!(vectors.complete);
    assert_eq!(vectors.represented_rows, 6);
    assert_eq!(vectors.total_rows, 6);
    assert_eq!(vectors.vectors[0].event_id, fixture.ids[4]);
    assert_eq!(vectors.vectors[0].vector, document_vector("note-4"));
    assert_eq!(vectors.vectors[1].event_id, fixture.ids[1]);
    assert_eq!(vectors.vectors[1].vector, document_vector("note-1"));

    oracle
        .similar_notes(fixture.ids[0], 3, &"0".repeat(64))
        .expect_err("representation-version mismatch must be rejected");
    oracle
        .vectors_for_notes(&[[9_u8; 32]], &built.representation_version)
        .expect_err("event outside the corpus must be rejected");
}

#[test]
fn similar_note_wave_batches_uncached_sources_into_one_matrix_pass() {
    let fixture = Fixture::new();
    let artifact = fixture.temp.path().join("wave-representation");
    let mut build_encoder = FixtureEncoder::new(Arc::new(Mutex::new(Vec::new())));
    let built = build_representation_shards(
        &fixture.ndb_path,
        &fixture.ordered_path,
        &artifact,
        &fixture.build_config("wave-plan", 2, 2, vec![0, 1, 2]),
        &mut build_encoder,
    )
    .expect("build complete fixture representation");

    let query_batches = Arc::new(Mutex::new(Vec::new()));
    let query_encoder = WaveFixtureEncoder {
        descriptor: fixture_descriptor(),
        query_batches: query_batches.clone(),
    };
    let mut oracle = Fp32OfflineOracle::open(
        &fixture.ndb_path,
        &fixture.ordered_path,
        &artifact,
        query_encoder,
    )
    .expect("open wave oracle");
    let requests = [
        SimilarNotesRequest {
            note_id: fixture.ids[0],
            candidate_depth: 3,
        },
        SimilarNotesRequest {
            note_id: fixture.ids[4],
            candidate_depth: 2,
        },
    ];

    let first = oracle
        .similar_notes_wave(&requests, &built.representation_version)
        .expect("query one co-scheduled wave");
    assert_eq!(first.responses.len(), 2);
    assert_eq!(first.metrics.encoded_queries, 2);
    assert_eq!(first.metrics.cache_hits, 0);
    assert_eq!(first.metrics.matrix_passes, 1);
    assert_eq!(first.metrics.scanned_rows, 6);
    assert_eq!(first.metrics.scan_block_rows, 4_096);
    assert!(
        !first.responses[0]
            .candidates
            .iter()
            .any(|candidate| candidate.event_id == fixture.ids[0])
    );
    assert!(
        !first.responses[1]
            .candidates
            .iter()
            .any(|candidate| candidate.event_id == fixture.ids[4])
    );
    assert_eq!(
        *query_batches.lock().expect("query batches"),
        vec![vec!["note-0".to_owned(), "note-4".to_owned()]]
    );

    let second = oracle
        .similar_notes_wave(&requests, &built.representation_version)
        .expect("reuse exact per-request cache entries");
    assert_eq!(second.responses, first.responses);
    assert_eq!(second.metrics.encoded_queries, 0);
    assert_eq!(second.metrics.cache_hits, 2);
    assert_eq!(second.metrics.matrix_passes, 0);
    assert_eq!(second.metrics.scanned_rows, 0);
    assert_eq!(query_batches.lock().expect("query batches").len(), 1);
}

#[test]
fn same_contract_cpu_query_encoder_can_use_a_cuda_built_representation() {
    let fixture = Fixture::new();
    let artifact = fixture
        .temp
        .path()
        .join("cross-device-query-representation");
    let mut build_encoder = FixtureEncoder::new(Arc::new(Mutex::new(Vec::new())));
    build_encoder.descriptor.execution_device = "cuda".to_owned();
    let built = build_representation_shards(
        &fixture.ndb_path,
        &fixture.ordered_path,
        &artifact,
        &fixture.build_config("cross-device-query-plan", 2, 2, vec![0, 1, 2]),
        &mut build_encoder,
    )
    .expect("build CUDA-provenance representation");

    let cpu_query_encoder = FixtureEncoder::new(Arc::new(Mutex::new(Vec::new())));
    let mut oracle = Fp32OfflineOracle::open(
        &fixture.ndb_path,
        &fixture.ordered_path,
        &artifact,
        cpu_query_encoder,
    )
    .expect("same semantic contract may query locally on CPU");
    oracle
        .similar_notes(fixture.ids[0], 2, &built.representation_version)
        .expect("run local CPU query against CUDA-built public vectors");
}

#[test]
fn oracle_rejects_a_corpus_changed_after_verification_before_query_inference() {
    let fixture = Fixture::new();
    let artifact = fixture.temp.path().join("corpus-sealed-representation");
    let mut build_encoder = FixtureEncoder::new(Arc::new(Mutex::new(Vec::new())));
    build_representation_shards(
        &fixture.ndb_path,
        &fixture.ordered_path,
        &artifact,
        &fixture.build_config("corpus-sealed-plan", 2, 2, vec![0, 1, 2]),
        &mut build_encoder,
    )
    .expect("build and verify sealed representation");

    let corpus_data = fixture.ndb_path.join("data.mdb");
    let replacement = fixture.ndb_path.join("changed-data.mdb");
    fs::copy(&corpus_data, &replacement).expect("copy corpus data");
    fs::rename(&replacement, &corpus_data).expect("replace corpus data");

    let query_calls = Arc::new(Mutex::new(Vec::new()));
    let error = match Fp32OfflineOracle::open(
        &fixture.ndb_path,
        &fixture.ordered_path,
        &artifact,
        FixtureEncoder::new(query_calls.clone()),
    ) {
        Ok(_) => panic!("oracle must reject a corpus changed after verification"),
        Err(error) => error,
    };
    assert!(
        error.to_string().contains("changed after verification"),
        "{error}"
    );
    assert!(
        query_calls.lock().expect("query call log").is_empty(),
        "corpus identity must fail before query inference"
    );
}

#[test]
fn stored_vector_lookup_does_not_require_a_query_encoder_or_corpus() {
    let fixture = Fixture::new();
    let artifact = fixture.temp.path().join("representation");
    let mut build_encoder = FixtureEncoder::new(Arc::new(Mutex::new(Vec::new())));
    let built = build_representation_shards(
        &fixture.ndb_path,
        &fixture.ordered_path,
        &artifact,
        &fixture.build_config("lookup-plan", 2, 2, vec![0, 1, 2]),
        &mut build_encoder,
    )
    .expect("build complete fixture representation");
    fs::remove_dir_all(&fixture.ndb_path).expect("remove corpus after representation build");

    let requested = [fixture.ids[4], fixture.ids[1]];
    let vectors = vectors_for_notes(
        &fixture.ordered_path,
        &artifact,
        &requested,
        &built.representation_version,
    )
    .expect("read stored vectors without a corpus or encoder");
    assert_eq!(vectors.representation_version, built.representation_version);
    assert_eq!(vectors.vectors[0].event_id, fixture.ids[4]);
    assert_eq!(vectors.vectors[0].vector, document_vector("note-4"));
    assert_eq!(vectors.vectors[1].event_id, fixture.ids[1]);
    assert_eq!(vectors.vectors[1].vector, document_vector("note-1"));

    let config_path = fixture.temp.path().join("vectors-config.json");
    fs::write(
        &config_path,
        serde_json::to_vec_pretty(&serde_json::json!({
            "corpus_path": fixture.temp.path().join("missing-corpus"),
            "ordered_event_ids_path": fixture.ordered_path,
            "token_audit_path": fixture.token_audit_path,
            "batch_plan_path": fixture.temp.path().join("lookup-plan"),
            "representation_path": artifact,
            "model_bundle_root": fixture.temp.path().join("missing-model"),
            "model_lock_path": fixture.temp.path().join("missing-model-lock"),
            "model_bundle_script": fixture.temp.path().join("missing-verifier"),
            "model_bundle_python": fixture.temp.path().join("missing-python"),
            "worker_source_path": fixture.temp.path().join("missing-worker"),
            "dependency_lock_path": fixture.temp.path().join("missing-dependencies"),
            "container_image": "fixture-image",
            "torch_version": "fixture",
            "transformers_version": "fixture",
            "cuda_version": "fixture",
            "worker": {
                "program": fixture.temp.path().join("missing-worker-program"),
                "model_dir": fixture.temp.path().join("missing-model-directory"),
                "model_lock_path": fixture.temp.path().join("missing-worker-model-lock"),
                "dependency_lock_path": fixture.temp.path().join("missing-worker-dependencies"),
                "device": "cpu"
            },
            "batch_size": 2,
            "shard_rows": 2
        }))
        .expect("serialize vector command config"),
    )
    .expect("write vector command config");
    let ids = requested
        .iter()
        .map(|id| {
            id.iter()
                .map(|byte| format!("{byte:02x}"))
                .collect::<String>()
        })
        .collect::<Vec<_>>()
        .join(",");
    let output = Command::new(env!("CARGO_BIN_EXE_gte-oracle"))
        .arg("vectors-for-notes")
        .arg(&config_path)
        .arg(ids)
        .arg(&built.representation_version)
        .output()
        .expect("run stored-vector command");
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let output: serde_json::Value =
        serde_json::from_slice(&output.stdout).expect("decode stored-vector response");
    assert_eq!(
        output["vectors"][0]["vector"],
        serde_json::json!(document_vector("note-4"))
    );
}

#[test]
fn lookup_requires_explicit_verification_and_rejects_a_changed_unrequested_shard() {
    let fixture = Fixture::new();
    let artifact = fixture.temp.path().join("sealed-representation");
    let mut encoder = FixtureEncoder::new(Arc::new(Mutex::new(Vec::new())));
    let built = build_representation_shards(
        &fixture.ndb_path,
        &fixture.ordered_path,
        &artifact,
        &fixture.build_config("sealed-plan", 2, 2, vec![0, 1, 2]),
        &mut encoder,
    )
    .expect("build and verify sealed representation");
    let verification = artifact.join("verification.json");
    assert!(
        verification.is_file(),
        "build must publish a verification receipt"
    );

    fs::remove_file(&verification).expect("remove verification receipt");
    let error = vectors_for_notes(
        &fixture.ordered_path,
        &artifact,
        &[fixture.ids[0]],
        &built.representation_version,
    )
    .expect_err("lookup must never silently repeat deep verification");
    assert!(
        error.to_string().contains("verify representation"),
        "{error}"
    );
    assert!(
        !verification.exists(),
        "lookup must not recreate trust implicitly"
    );

    verify_representation(&fixture.ndb_path, &fixture.ordered_path, &artifact)
        .expect("explicitly verify and reseal representation");
    vectors_for_notes(
        &fixture.ordered_path,
        &artifact,
        &[fixture.ids[0]],
        &built.representation_version,
    )
    .expect("lookup after explicit verification");

    let unrequested = artifact.join("shards/000002/vectors.f32le");
    let mut corrupted = fs::read(&unrequested).expect("read unrequested shard");
    corrupted[0] ^= 1;
    fs::write(&unrequested, corrupted).expect("mutate unrequested shard in place");
    let error = vectors_for_notes(
        &fixture.ordered_path,
        &artifact,
        &[fixture.ids[0]],
        &built.representation_version,
    )
    .expect_err("sealed lookup must reject any changed shard");
    assert!(
        error.to_string().contains("changed after verification"),
        "{error}"
    );
    open_representation(&fixture.ordered_path, &artifact)
        .expect_err("deep verification must reject the changed shard checksum");
}

#[test]
fn production_batches_follow_audited_lengths_and_preserve_ordered_vector_rows() {
    let fixture = Fixture::new();
    let artifact = fixture.temp.path().join("scheduled-representation");
    let calls = Arc::new(Mutex::new(Vec::new()));
    let mut encoder = FixtureEncoder::new(calls.clone());
    let mut observer = RecordingObserver::default();
    let config = fixture.build_config("scheduled-plan", 6, 2, vec![0]);

    let built = build_representation_shards_observed(
        &fixture.ndb_path,
        &fixture.ordered_path,
        &artifact,
        &config,
        &mut encoder,
        &mut observer,
    )
    .expect("build length-scheduled representation");

    assert_eq!(
        *calls.lock().expect("call log"),
        vec!["note-1", "note-3", "note-5", "note-2", "note-0", "note-4"]
    );
    let expected_shapes = vec![
        RepresentationBatchShape {
            rows: 2,
            padded_tokens_per_row: 2,
            effective_tokens: 3,
        },
        RepresentationBatchShape {
            rows: 2,
            padded_tokens_per_row: 4,
            effective_tokens: 7,
        },
        RepresentationBatchShape {
            rows: 2,
            padded_tokens_per_row: 6,
            effective_tokens: 11,
        },
    ];
    let expected_batches = expected_shapes
        .into_iter()
        .enumerate()
        .map(|(batch, shape)| (0, batch as u32, shape))
        .collect::<Vec<_>>();
    assert_eq!(observer.checked, expected_batches);
    assert_eq!(observer.completed_batches, expected_batches);
    assert_eq!(observer.completed_shards, vec![0]);
    assert!(
        observer
            .phases
            .contains(&RepresentationArtifactPhase::ShardSetup)
    );
    assert!(
        observer
            .phases
            .contains(&RepresentationArtifactPhase::Write)
    );
    assert!(
        observer
            .phases
            .contains(&RepresentationArtifactPhase::Checkpoint)
    );

    let response = vectors_for_notes(
        &fixture.ordered_path,
        &artifact,
        &fixture.ids,
        &built.representation_version,
    )
    .expect("read every vector in original row order");
    assert_eq!(
        response
            .vectors
            .iter()
            .map(|stored| stored.vector.clone())
            .collect::<Vec<_>>(),
        (0..6)
            .map(|index| document_vector(&format!("note-{index}")))
            .collect::<Vec<_>>()
    );
    assert_eq!(
        built.manifest.batch_plan.manifest_sha256,
        create_representation_batch_plan(
            &fixture.ordered_path,
            &fixture.token_audit_path,
            fixture.temp.path().join("scheduled-plan"),
            &RepresentationBatchPlanConfig {
                shard_rows: 6,
                batch_rows: 2,
            },
        )
        .expect("reopen plan")
        .identity()
        .manifest_sha256
    );
}

#[test]
fn production_observer_measures_checkpoint_publication_and_final_verification() {
    let fixture = Fixture::new();
    let artifact = fixture.temp.path().join("complete-pipeline-measurement");
    let calls = Arc::new(Mutex::new(Vec::new()));
    let mut encoder = FixtureEncoder::new(calls);
    let mut observer = RecordingObserver::default();
    let config = fixture.build_config("complete-pipeline-plan", 6, 2, vec![0]);

    build_representation_shards_observed(
        &fixture.ndb_path,
        &fixture.ordered_path,
        &artifact,
        &config,
        &mut encoder,
        &mut observer,
    )
    .expect("build through the measured production path");

    assert!(
        observer
            .phases
            .contains(&RepresentationArtifactPhase::Checkpoint)
    );
    assert!(
        observer
            .phases
            .contains(&RepresentationArtifactPhase::ManifestPublication)
    );
    assert!(
        observer
            .phases
            .contains(&RepresentationArtifactPhase::Verification)
    );
}

#[test]
fn production_observer_can_stop_before_publishing_a_checkpoint() {
    let fixture = Fixture::new();
    let artifact = fixture.temp.path().join("checkpoint-stop");
    let calls = Arc::new(Mutex::new(Vec::new()));
    let mut encoder = FixtureEncoder::new(calls);
    let mut observer = StopBeforeCheckpoint;
    let config = fixture.build_config("checkpoint-stop-plan", 6, 2, vec![0]);

    let error = build_representation_shards_observed(
        &fixture.ndb_path,
        &fixture.ordered_path,
        &artifact,
        &config,
        &mut encoder,
        &mut observer,
    )
    .expect_err("observer stops before checkpoint publication");

    assert!(error.to_string().contains("checkpoint stop"), "{error}");
    assert!(!artifact.join("shards/000000").exists());
}

#[test]
fn local_index_preparation_rejects_an_orphan_or_different_order() {
    let fixture = Fixture::new();
    let artifact = fixture.temp.path().join("prepared-index");
    let prepared =
        prepare_representation_index(&fixture.ndb_path, &fixture.ordered_path, &artifact)
            .expect("prepare the complete event-ID index without an encoder");
    assert_eq!(prepared.total_rows, 6);
    assert_eq!(
        prepare_representation_index(&fixture.ndb_path, &fixture.ordered_path, &artifact)
            .expect("reuse the verified local index"),
        prepared
    );

    let mut reversed = fixture.ids.clone();
    reversed.reverse();
    let reversed_path = fixture.temp.path().join("reversed-event-ids.bin");
    write_ids(&reversed_path, &reversed);
    let error = prepare_representation_index(&fixture.ndb_path, &reversed_path, &artifact)
        .expect_err("same-size ordered IDs cannot reuse a different index");
    assert!(
        error.to_string().contains("different corpus or order"),
        "{error}"
    );

    let orphan = fixture.temp.path().join("orphan-index");
    fs::create_dir_all(orphan.join("index")).expect("create orphan index directory");
    fs::write(orphan.join("index/event-id-to-row.bin"), b"orphan").expect("write orphan index");
    let error = prepare_representation_index(&fixture.ndb_path, &fixture.ordered_path, &orphan)
        .expect_err("an index without its immutable identity must not be reused");
    assert!(error.to_string().contains("unpublished index"), "{error}");

    let legacy = fixture.temp.path().join("legacy-index");
    fs::create_dir_all(&legacy).expect("create legacy representation directory");
    fs::write(legacy.join("event-id-to-row.bin"), b"unbound").expect("write unbound legacy index");
    let error = prepare_representation_index(&fixture.ndb_path, &fixture.ordered_path, &legacy)
        .expect_err("an old index without corpus/order identity must not be ignored or reused");
    assert!(error.to_string().contains("unpublished index"), "{error}");
}

#[test]
fn representation_build_rejects_orphan_shards_without_a_build_identity() {
    let fixture = Fixture::new();
    let artifact = fixture.temp.path().join("orphan-shard");
    fs::create_dir_all(artifact.join("shards/000000")).expect("create orphan shard");
    fs::write(artifact.join("shards/000000/vectors.f32le"), b"unbound")
        .expect("write orphan shard data");
    let mut encoder = FixtureEncoder::new(Arc::new(Mutex::new(Vec::new())));

    let error = build_representation_shards(
        &fixture.ndb_path,
        &fixture.ordered_path,
        &artifact,
        &fixture.build_config("orphan-shard-plan", 6, 2, vec![0]),
        &mut encoder,
    )
    .expect_err("a shard without a corpus/order/build identity must not be reused");
    assert!(error.to_string().contains("orphan shards"), "{error}");
}

#[test]
fn representation_rejects_a_corpus_changed_after_the_token_audit() {
    let fixture = Fixture::new();
    let config = fixture.build_config("changed-corpus-plan", 6, 2, vec![0]);
    let mut corpus = OpenOptions::new()
        .append(true)
        .open(fixture.ndb_path.join("data.mdb"))
        .expect("open corpus data");
    corpus.write_all(b"changed").expect("change corpus bytes");
    corpus.sync_all().expect("sync changed corpus");
    let calls = Arc::new(Mutex::new(Vec::new()));
    let mut encoder = FixtureEncoder::new(calls.clone());

    let error = build_representation_shards(
        &fixture.ndb_path,
        &fixture.ordered_path,
        fixture.temp.path().join("changed-corpus-representation"),
        &config,
        &mut encoder,
    )
    .expect_err("stale audited lengths must not be used for a changed corpus");
    assert!(error.to_string().contains("token audit"), "{error}");
    assert!(
        calls.lock().expect("encoder calls").is_empty(),
        "corpus identity must fail before model inference"
    );
}

struct Fixture {
    temp: tempfile::TempDir,
    ndb_path: std::path::PathBuf,
    ordered_path: std::path::PathBuf,
    token_audit_path: std::path::PathBuf,
    ids: Vec<[u8; 32]>,
}

impl Fixture {
    fn new() -> Self {
        let temp = tempfile::tempdir().expect("temporary directory");
        let ndb_path = temp.path().join("english.ndb");
        let ndb = Ndb::new(
            ndb_path.to_str().expect("UTF-8 NDB path"),
            &Config::new().set_mapsize(512 * 1024 * 1024),
        )
        .expect("open NDB");
        let events = (0..6)
            .map(|index| signed_event(&format!("note-{index}"), index))
            .collect::<Vec<_>>();
        for event in &events {
            ndb.process_event(event).expect("submit event");
        }
        wait_for_count(&ndb, events.len());
        drop(ndb);
        let ids = events
            .iter()
            .map(|event| event_id(event))
            .collect::<Vec<_>>();
        let ordered_path = temp.path().join("ordered-event-ids.bin");
        write_ids(&ordered_path, &ids);
        let token_audit_path = temp.path().join("token-audit");
        let mut counter = FixtureLengthCounter {
            descriptor: fixture_descriptor(),
        };
        audit_ordered_gte_tokens(
            &ndb_path,
            &ordered_path,
            &token_audit_path,
            &OrderedGteTokenAuditConfig {
                batch_size: 2,
                shard_rows: 2,
            },
            &mut counter,
        )
        .expect("audit fixture token lengths");
        Self {
            temp,
            ndb_path,
            ordered_path,
            token_audit_path,
            ids,
        }
    }

    fn build_config(
        &self,
        plan_name: &str,
        shard_rows: u64,
        batch_rows: usize,
        shard_ordinals: Vec<u32>,
    ) -> RepresentationBuildConfig {
        let batch_plan_path = self.temp.path().join(plan_name);
        create_representation_batch_plan(
            &self.ordered_path,
            &self.token_audit_path,
            &batch_plan_path,
            &RepresentationBatchPlanConfig {
                shard_rows,
                batch_rows,
            },
        )
        .expect("create fixture production batch plan");
        RepresentationBuildConfig {
            token_audit_path: self.token_audit_path.clone(),
            batch_plan_path,
            shard_ordinals,
        }
    }
}

struct FixtureLengthCounter {
    descriptor: RepresentationDescriptor,
}

impl OrderedGteTokenCounter for FixtureLengthCounter {
    fn descriptor(&self) -> &RepresentationDescriptor {
        &self.descriptor
    }

    fn token_lengths(&mut self, role: TokenRole, texts: &[&str]) -> Result<Vec<u32>> {
        let query_extra = if role == TokenRole::Query { 10 } else { 0 };
        texts
            .iter()
            .map(|text| {
                let index = text
                    .strip_prefix("note-")
                    .and_then(|index| index.parse::<usize>().ok())
                    .ok_or_else(|| Error::Invariant("unexpected fixture note".to_owned()))?;
                let document = [5_u32, 1, 4, 2, 6, 3][index];
                Ok(document + query_extra)
            })
            .collect()
    }
}

#[derive(Default)]
struct RecordingObserver {
    checked: Vec<(u32, u32, RepresentationBatchShape)>,
    completed_batches: Vec<(u32, u32, RepresentationBatchShape)>,
    phases: Vec<RepresentationArtifactPhase>,
    completed_shards: Vec<u32>,
}

struct StopBeforeCheckpoint;

impl RepresentationBuildObserver for StopBeforeCheckpoint {
    fn check_artifact_phase(
        &mut self,
        phase: RepresentationArtifactPhase,
        _shard_ordinal: Option<u32>,
    ) -> Result<()> {
        if phase == RepresentationArtifactPhase::Checkpoint {
            return Err(Error::Budget("checkpoint stop".to_owned()));
        }
        Ok(())
    }
}

impl RepresentationBuildObserver for RecordingObserver {
    fn check_continue(
        &mut self,
        shard_ordinal: u32,
        batch_ordinal: u32,
        next: &RepresentationBatchShape,
    ) -> Result<()> {
        self.checked
            .push((shard_ordinal, batch_ordinal, next.clone()));
        Ok(())
    }

    fn completed_batch(
        &mut self,
        shard_ordinal: u32,
        batch_ordinal: u32,
        shape: &RepresentationBatchShape,
        _elapsed: Duration,
    ) -> Result<()> {
        self.completed_batches
            .push((shard_ordinal, batch_ordinal, shape.clone()));
        Ok(())
    }

    fn artifact_phase(
        &mut self,
        phase: RepresentationArtifactPhase,
        _shard_ordinal: Option<u32>,
        _elapsed: Duration,
    ) -> Result<()> {
        self.phases.push(phase);
        Ok(())
    }

    fn completed_shard(&mut self, shard: &oracle_mvp::representation::RepresentationShard) {
        self.completed_shards.push(shard.ordinal);
    }
}

struct FixtureEncoder {
    descriptor: RepresentationDescriptor,
    calls: Arc<Mutex<Vec<String>>>,
}

struct WaveFixtureEncoder {
    descriptor: RepresentationDescriptor,
    query_batches: Arc<Mutex<Vec<Vec<String>>>>,
}

impl RepresentationEncoder for WaveFixtureEncoder {
    fn descriptor(&self) -> &RepresentationDescriptor {
        &self.descriptor
    }

    fn encode_documents(&mut self, _texts: &[&str]) -> Result<Vec<f32>> {
        Err(Error::Encoder {
            operation: "encode documents",
            message: "wave fixture is query-only".to_owned(),
        })
    }

    fn encode_queries(&mut self, texts: &[&str]) -> Result<Vec<f32>> {
        self.query_batches
            .lock()
            .expect("query batches")
            .push(texts.iter().map(|text| (*text).to_owned()).collect());
        Ok(texts
            .iter()
            .flat_map(|text| match *text {
                "note-0" => vec![0.0, 1.0, 0.0],
                other => document_vector(other),
            })
            .collect())
    }
}

impl FixtureEncoder {
    fn new(calls: Arc<Mutex<Vec<String>>>) -> Self {
        Self {
            descriptor: fixture_descriptor(),
            calls,
        }
    }
}

impl RepresentationEncoder for FixtureEncoder {
    fn descriptor(&self) -> &RepresentationDescriptor {
        &self.descriptor
    }

    fn encode_documents(&mut self, texts: &[&str]) -> Result<Vec<f32>> {
        let mut output = Vec::with_capacity(texts.len() * 3);
        for text in texts {
            self.calls
                .lock()
                .expect("call log")
                .push((*text).to_owned());
            output.extend(document_vector(text));
        }
        Ok(output)
    }

    fn encode_queries(&mut self, texts: &[&str]) -> Result<Vec<f32>> {
        if texts.len() != 1 {
            return Err(Error::Encoder {
                operation: "encode query",
                message: "fixture expects one query".to_owned(),
            });
        }
        self.calls
            .lock()
            .expect("call log")
            .push(texts[0].to_owned());
        Ok(match texts[0] {
            "note-0" => vec![0.0, 1.0, 0.0],
            other => document_vector(other),
        })
    }
}

fn fixture_descriptor() -> RepresentationDescriptor {
    RepresentationDescriptor {
        model_id: "fixture/gte".to_owned(),
        model_revision: "1".repeat(40),
        model_lock_sha256: "2".repeat(64),
        worker_sha256: "3".repeat(64),
        dependency_lock_sha256: "4".repeat(64),
        container_image: "fixture@sha256:5".to_owned() + &"5".repeat(63),
        torch_version: "2.12.1".to_owned(),
        transformers_version: "4.41.2".to_owned(),
        cuda_version: "13.0.2".to_owned(),
        execution_device: "cpu".to_owned(),
        dimensions: 3,
        model_token_ceiling: 32_768,
        document_input: "raw-note-content".to_owned(),
        query_instruction: "fixture-query-instruction".to_owned(),
        pooling: "last-token".to_owned(),
        normalization: "l2".to_owned(),
        numeric_format: "f32le".to_owned(),
    }
}

fn document_vector(content: &str) -> Vec<f32> {
    let raw = match content {
        "note-0" => [1.0, 0.0, 0.0],
        "note-1" => [0.9, 0.1, 0.0],
        "note-2" => [0.0, 1.0, 0.0],
        "note-3" => [0.0, 0.9, 0.1],
        "note-4" => [0.0, 0.0, 1.0],
        "note-5" => [-1.0, 0.0, 0.0],
        _ => panic!("unexpected fixture content"),
    };
    let norm = raw.iter().map(|value| value * value).sum::<f32>().sqrt();
    raw.into_iter().map(|value| value / norm).collect()
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
        assert!(Instant::now() < deadline, "NDB persistence timeout");
        thread::sleep(Duration::from_millis(10));
    }
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
