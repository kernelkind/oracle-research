use std::fs::{self, File};
use std::io;
use std::io::Write;
use std::os::unix::fs::PermissionsExt;
use std::path::{Path, PathBuf};
use std::thread;
use std::time::{Duration, Instant};

use nostrdb::{Config, Filter, Ndb, NoteBuilder, Transaction};
use oracle_mvp::adaptive_learning_runner::AdaptiveLearningRunnerOutcome;
use oracle_mvp::candidate_order::CandidateOrderOracle;
use oracle_mvp::evaluator::{
    CompletionView, EvaluatorDecision, EvaluatorSubmission, EvaluatorUi, RatingOutcome, RatingView,
    RecoveryOutcome, RecoveryView, RestOutcome, RestView,
};
use oracle_mvp::fp32_oracle::{
    Fp32Candidate, SimilarNotesRequest, SimilarNotesResponse, SimilarNotesWaveMetrics,
    SimilarNotesWaveResponse, VectorsForNotesResponse,
};
use oracle_mvp::gte::TokenRole;
use oracle_mvp::ordered_gte_token_audit::{
    OrderedGteTokenAuditConfig, OrderedGteTokenCounter, audit_ordered_gte_tokens,
};
use oracle_mvp::phase3_binding::Phase3RunnerBinding;
use oracle_mvp::phase3_cost_preflight::immutable_tree_metadata_fingerprint;
use oracle_mvp::phase3_learning_launch::{
    HUMAN_LEARNING_PURPOSE, LearningWorkspaceState, bind_learning_launch,
    prepare_learning_workspace, read_learning_launch_config, read_learning_launch_receipt,
    run_prepared_learning,
};
use oracle_mvp::phase3_seed_selection::{
    Phase3SeedSelectionConfig, Phase3SeedSelectionOutcome, run_phase3_seed_selection,
};
use oracle_mvp::quota_resolution::PriorPresentation;
use oracle_mvp::representation::{
    RepresentationBuildConfig, RepresentationDescriptor, RepresentationEncoder,
    build_representation_shards,
};
use oracle_mvp::representation_batch_plan::{
    RepresentationBatchPlanConfig, create_representation_batch_plan,
};
use oracle_mvp::representation_geometry::derive_representation_geometry;
use oracle_mvp::snapshot::{Error, Result};
use sha2::{Digest, Sha256};

const ROWS: usize = 513;

#[test]
fn schema_two_learning_workspace_consumes_the_completed_seed_handoff() {
    let fixture = Fixture::new();
    let handoff_path = fixture.temp.path().join("seed-selection-handoff.json");
    let selection_config = Phase3SeedSelectionConfig {
        corpus_path: fixture.ndb_path.clone(),
        corpus_identity: format!("sha256:{}", hash_file(&fixture.ndb_path.join("data.mdb"))),
        session_path: fixture.temp.path().join("seed-selection-session.json"),
        handoff_path: handoff_path.clone(),
        representation_version: fixture.representation_version.clone(),
        candidate_event_ids: fixture.ids[..7].to_vec(),
    };
    let mut oracle = SeedSelectionOracle {
        version: fixture.representation_version.clone(),
        corpus_ids: fixture.ids.clone(),
    };
    let mut evaluator = SeedSelectionEvaluator {
        decisions: [
            EvaluatorDecision::Rating(1),
            EvaluatorDecision::WrongLanguage,
            EvaluatorDecision::Rating(5),
            EvaluatorDecision::Rating(6),
            EvaluatorDecision::Rating(7),
            EvaluatorDecision::Rating(5),
            EvaluatorDecision::Rating(6),
        ]
        .into_iter(),
    };
    let outcome = run_phase3_seed_selection(&selection_config, &mut oracle, &mut evaluator)
        .expect("complete fixture seed selection");
    assert!(matches!(outcome, Phase3SeedSelectionOutcome::Complete(_)));

    let config_path = fixture.write_handoff_config("handoff-learning", &handoff_path);
    let config = read_learning_launch_config(&config_path).expect("read handoff learning config");
    let prepared = prepare_learning_workspace(&config_path, &config)
        .expect("prepare workspace from seed handoff");
    let binding: Phase3RunnerBinding = serde_json::from_slice(
        &fs::read(prepared.runner_binding_path()).expect("read runner binding"),
    )
    .expect("decode runner binding");

    assert_eq!(binding.seeds().len(), 5);
    assert_eq!(
        binding.initial_presentations().expect("screening ledger"),
        std::collections::BTreeMap::from([
            (fixture.ids[0], PriorPresentation::EligibleUnrated),
            (fixture.ids[1], PriorPresentation::WrongLanguage),
        ])
    );
    assert_eq!(
        fs::read(prepared.seed_selection_handoff_path()).expect("frozen handoff"),
        fs::read(handoff_path).expect("source handoff")
    );

    bind_learning_launch(
        &prepared,
        &config,
        &format!("sha256:{}", "d".repeat(64)),
        68 * 1024_u64.pow(3),
    )
    .expect("bind handoff learning launch");
    let mut learning_evaluator = PausingEvaluator::default();
    let learning = run_prepared_learning(
        &prepared,
        &config,
        FixtureEncoder {
            descriptor: fixture_descriptor(&fixture.model_bundle.join("model-lock.json")),
        },
        &mut learning_evaluator,
    )
    .expect("enter learning from selector handoff");
    assert!(matches!(learning, AdaptiveLearningRunnerOutcome::Paused));
    assert_eq!(learning_evaluator.presented_notes.len(), 1);
    assert_ne!(learning_evaluator.presented_notes[0], "note-0");
    assert_ne!(learning_evaluator.presented_notes[0], "note-1");
    let session: serde_json::Value = serde_json::from_slice(
        &fs::read(prepared.session_path()).expect("read handoff learning session"),
    )
    .expect("decode handoff learning session");
    assert_eq!(session["binding"]["seed_evidence"]["event_count"], 5);
    assert_eq!(
        session["binding"]["fixed"]["initial_presentations"]
            .as_array()
            .expect("stored screening ledger")
            .len(),
        2
    );
}

#[test]
fn initialization_is_atomic_source_preserving_and_exactly_resumable() {
    let fixture = Fixture::new();
    let config_path = fixture.write_config("human-run", &fixture.ids[..5], &[5, 6, 7, 5, 6]);
    let config = read_learning_launch_config(&config_path).expect("read learning config");
    let representation_before = immutable_tree_metadata_fingerprint(&fixture.representation)
        .expect("fingerprint representation before");
    let model_before = immutable_tree_metadata_fingerprint(&fixture.model_bundle)
        .expect("fingerprint model before");
    let corpus_before = fs::read(fixture.ndb_path.join("data.mdb")).expect("read corpus before");
    let ordered_before = fs::read(&fixture.ordered_path).expect("read ordered IDs before");
    let geometry_before = snapshot_tree(&fixture.geometry);

    let prepared = prepare_learning_workspace(&config_path, &config)
        .expect("initialize the real learning workspace");

    assert!(prepared.created());
    assert_eq!(prepared.state(), LearningWorkspaceState::Initialized);
    assert_eq!(
        fs::metadata(prepared.workspace_path())
            .unwrap()
            .permissions()
            .mode()
            & 0o777,
        0o700
    );
    assert_eq!(
        fs::read(prepared.corpus_path().join("data.mdb")).unwrap(),
        corpus_before
    );
    assert_eq!(
        fs::read(prepared.ordered_event_ids_path()).unwrap(),
        ordered_before
    );
    assert!(
        prepared
            .representation_path()
            .join("verification.json")
            .is_file()
    );
    assert!(!prepared.session_path().exists());
    assert!(!prepared.oracle_cache_path().exists());
    let binding: Phase3RunnerBinding =
        serde_json::from_slice(&fs::read(prepared.runner_binding_path()).unwrap())
            .expect("decode runner binding");
    assert_eq!(binding.corpus_path(), prepared.corpus_path());
    assert_eq!(binding.session_path(), prepared.session_path());
    assert_eq!(binding.seeds().len(), 5);
    assert_eq!(
        immutable_tree_metadata_fingerprint(&fixture.representation).unwrap(),
        representation_before
    );
    assert_eq!(
        immutable_tree_metadata_fingerprint(&fixture.model_bundle).unwrap(),
        model_before
    );
    assert_eq!(
        fs::read(fixture.ndb_path.join("data.mdb")).unwrap(),
        corpus_before
    );
    assert_eq!(fs::read(&fixture.ordered_path).unwrap(), ordered_before);
    assert_eq!(snapshot_tree(&fixture.geometry), geometry_before);

    let image_id = format!("sha256:{}", "d".repeat(64));
    let launch = bind_learning_launch(&prepared, &config, &image_id, 68 * 1024_u64.pow(3))
        .expect("freeze the first guarded launch");
    assert_eq!(launch.controller_image_id(), image_id);
    assert_eq!(launch.memory_limit_bytes(), 68 * 1024_u64.pow(3));

    fs::write(prepared.session_path(), b"durable human ratings\n").expect("write session sentinel");
    fs::create_dir(prepared.oracle_cache_path()).expect("create cache sentinel");
    fs::write(
        prepared.oracle_cache_path().join("response.json"),
        b"cached\n",
    )
    .expect("write cache sentinel");
    fs::set_permissions(prepared.session_path(), fs::Permissions::from_mode(0o600))
        .expect("protect session sentinel");
    fs::set_permissions(
        prepared.oracle_cache_path(),
        fs::Permissions::from_mode(0o700),
    )
    .expect("protect cache sentinel");
    fs::set_permissions(
        prepared.oracle_cache_path().join("response.json"),
        fs::Permissions::from_mode(0o600),
    )
    .expect("protect cached response");
    let workspace_before = snapshot_tree(prepared.workspace_path());
    let resumed = prepare_learning_workspace(&config_path, &config)
        .expect("resume the exact initialized workspace");

    assert!(!resumed.created());
    assert_eq!(resumed.state(), LearningWorkspaceState::Initialized);
    assert_eq!(snapshot_tree(resumed.workspace_path()), workspace_before);

    let launch_before = fs::read(resumed.launch_receipt_path()).expect("read launch receipt");
    let error = bind_learning_launch(
        &resumed,
        &config,
        &format!("sha256:{}", "e".repeat(64)),
        68 * 1024_u64.pow(3),
    )
    .expect_err("refuse to replace the frozen controller image");
    assert!(error.to_string().contains("launch receipt"));
    assert_eq!(
        fs::read(resumed.launch_receipt_path()).expect("read unchanged launch receipt"),
        launch_before
    );
}

#[test]
fn first_launch_rejects_preexisting_runner_state() {
    let fixture = Fixture::new();
    let config_path = fixture.write_config("orphaned-state", &fixture.ids[..5], &[5, 6, 7, 5, 6]);
    let config = read_learning_launch_config(&config_path).expect("read learning config");
    let prepared = prepare_learning_workspace(&config_path, &config).expect("prepare workspace");
    fs::write(prepared.session_path(), b"orphaned ratings\n").expect("write orphaned session");
    fs::set_permissions(prepared.session_path(), fs::Permissions::from_mode(0o600))
        .expect("protect orphaned session");

    let error = bind_learning_launch(
        &prepared,
        &config,
        &format!("sha256:{}", "d".repeat(64)),
        68 * 1024_u64.pow(3),
    )
    .expect_err("refuse to bind an orphaned runner session");

    assert!(error.to_string().contains("runner state"));
    assert!(!prepared.launch_receipt_path().exists());
}

#[test]
fn invalid_seed_fails_without_publishing_a_workspace() {
    let fixture = Fixture::new();
    let mut seeds = fixture.ids[..4].to_vec();
    seeds.push([0xff; 32]);
    let config_path = fixture.write_config("invalid-seed", &seeds, &[5, 6, 7, 5, 6]);
    let config = read_learning_launch_config(&config_path).expect("read learning config");

    let error = prepare_learning_workspace(&config_path, &config)
        .expect_err("reject a seed absent from the corpus and representation");

    assert!(error.to_string().contains("seed"));
    assert!(!fixture.temp.path().join("invalid-seed").exists());
}

#[test]
fn prepared_learning_enters_and_recovers_the_real_runner_boundary() {
    let fixture = Fixture::new();
    let config_path = fixture.write_config("runner", &fixture.ids[..5], &[5, 6, 7, 5, 6]);
    let config = read_learning_launch_config(&config_path).expect("read learning config");
    let prepared = prepare_learning_workspace(&config_path, &config).expect("prepare workspace");
    bind_learning_launch(
        &prepared,
        &config,
        &format!("sha256:{}", "d".repeat(64)),
        68 * 1024_u64.pow(3),
    )
    .expect("bind launch");
    let mut first = PausingEvaluator::default();
    let outcome = run_prepared_learning(
        &prepared,
        &config,
        FixtureEncoder {
            descriptor: fixture_descriptor(&fixture.model_bundle.join("model-lock.json")),
        },
        &mut first,
    )
    .expect("enter the production runner");
    assert!(matches!(outcome, AdaptiveLearningRunnerOutcome::Paused));
    assert_eq!(first.rating_presentations, vec![1]);
    assert!(prepared.session_path().is_file());
    assert!(prepared.oracle_cache_path().is_dir());
    let session_before = fs::read(prepared.session_path()).expect("read paused session");

    let resumed = prepare_learning_workspace(&config_path, &config).expect("verify exact resume");
    assert_eq!(fs::read(resumed.session_path()).unwrap(), session_before);
    let mut recovery = PausingEvaluator::default();
    let outcome = run_prepared_learning(
        &resumed,
        &config,
        FixtureEncoder {
            descriptor: fixture_descriptor(&fixture.model_bundle.join("model-lock.json")),
        },
        &mut recovery,
    )
    .expect("recover the pending production presentation");
    assert!(matches!(outcome, AdaptiveLearningRunnerOutcome::Paused));
    assert_eq!(recovery.recovery_presentations, vec![1]);
}

#[test]
fn resume_rejects_private_binding_drift_without_touching_the_session() {
    let fixture = Fixture::new();
    let config_path = fixture.write_config("binding-drift", &fixture.ids[..5], &[5, 6, 7, 5, 6]);
    let config = read_learning_launch_config(&config_path).expect("read learning config");
    let prepared = prepare_learning_workspace(&config_path, &config).expect("prepare workspace");
    fs::write(
        prepared.session_path(),
        b"private ratings remain untouched\n",
    )
    .expect("write session sentinel");
    fs::set_permissions(prepared.session_path(), fs::Permissions::from_mode(0o600))
        .expect("protect session sentinel");
    let session_before = fs::read(prepared.session_path()).unwrap();
    let mut binding = fs::read(prepared.runner_binding_path()).unwrap();
    binding.push(b' ');
    fs::write(prepared.runner_binding_path(), binding).expect("tamper binding");

    let error = prepare_learning_workspace(&config_path, &config)
        .expect_err("reject a changed runner binding");

    assert!(error.to_string().contains("runner binding"));
    assert_eq!(fs::read(prepared.session_path()).unwrap(), session_before);
}

#[test]
fn resume_rejects_a_session_that_is_not_owner_only() {
    let fixture = Fixture::new();
    let config_path = fixture.write_config("session-mode", &fixture.ids[..5], &[5, 6, 7, 5, 6]);
    let config = read_learning_launch_config(&config_path).expect("read learning config");
    let prepared = prepare_learning_workspace(&config_path, &config).expect("prepare workspace");
    fs::write(prepared.session_path(), b"permissive private state\n")
        .expect("write permissive session");
    fs::set_permissions(prepared.session_path(), fs::Permissions::from_mode(0o644))
        .expect("make session permissive");

    let error = prepare_learning_workspace(&config_path, &config)
        .expect_err("reject a permissive private session");

    assert!(error.to_string().contains("owner-only"));
}

#[test]
fn resume_rejects_source_model_drift() {
    let fixture = Fixture::new();
    let config_path = fixture.write_config("model-drift", &fixture.ids[..5], &[5, 6, 7, 5, 6]);
    let config = read_learning_launch_config(&config_path).expect("read learning config");
    prepare_learning_workspace(&config_path, &config).expect("prepare workspace");
    fs::write(
        fixture.model_bundle.join("model/weights.bin"),
        b"changed fixture weights\n",
    )
    .expect("change source model");

    let error = prepare_learning_workspace(&config_path, &config)
        .expect_err("reject changed source model metadata");

    assert!(error.to_string().contains("source artifact"));
}

#[test]
fn resume_rejects_drift_in_every_frozen_input_without_touching_the_session() {
    let fixture = Fixture::new();
    let config_path = fixture.write_config("frozen-drift", &fixture.ids[..5], &[5, 6, 7, 5, 6]);
    let config = read_learning_launch_config(&config_path).expect("read learning config");
    let prepared = prepare_learning_workspace(&config_path, &config).expect("prepare workspace");
    bind_learning_launch(
        &prepared,
        &config,
        &format!("sha256:{}", "d".repeat(64)),
        68 * 1024_u64.pow(3),
    )
    .expect("bind launch");
    fs::write(
        prepared.session_path(),
        b"private ratings remain untouched\n",
    )
    .expect("write session sentinel");
    fs::set_permissions(prepared.session_path(), fs::Permissions::from_mode(0o600))
        .expect("protect session sentinel");
    let session_before = fs::read(prepared.session_path()).unwrap();

    let cases = [
        ("invocation config", config_path.clone(), false),
        (
            "frozen config",
            prepared.frozen_config_path().to_owned(),
            false,
        ),
        (
            "prepared corpus",
            prepared.corpus_path().join("data.mdb"),
            false,
        ),
        (
            "ordered event IDs",
            prepared.ordered_event_ids_path().to_owned(),
            false,
        ),
        (
            "prepared representation",
            prepared.representation_path().join("manifest.json"),
            false,
        ),
        (
            "source geometry",
            fixture.geometry.join("manifest.json"),
            false,
        ),
        (
            "launch receipt",
            prepared.launch_receipt_path().to_owned(),
            true,
        ),
    ];
    for (label, path, launch_receipt) in cases {
        let original = fs::read(&path).unwrap_or_else(|error| panic!("read {label}: {error}"));
        let mut changed = original.clone();
        changed.push(b' ');
        fs::write(&path, changed).unwrap_or_else(|error| panic!("change {label}: {error}"));

        let rejected = if launch_receipt {
            read_learning_launch_receipt(&prepared, &config).is_err()
        } else {
            prepare_learning_workspace(&config_path, &config).is_err()
        };
        fs::write(&path, original).unwrap_or_else(|error| panic!("restore {label}: {error}"));

        assert!(rejected, "resume accepted drift in {label}");
        assert_eq!(
            fs::read(prepared.session_path()).unwrap(),
            session_before,
            "resume touched the private session after {label} drift"
        );
    }
}

#[derive(Default)]
struct PausingEvaluator {
    rating_presentations: Vec<usize>,
    recovery_presentations: Vec<usize>,
    presented_notes: Vec<String>,
}

struct SeedSelectionEvaluator {
    decisions: std::array::IntoIter<EvaluatorDecision, 7>,
}

impl EvaluatorUi for SeedSelectionEvaluator {
    fn rate(&mut self, _view: RatingView<'_>) -> io::Result<RatingOutcome> {
        Ok(RatingOutcome::Submitted(EvaluatorSubmission::new(
            self.decisions.next().expect("fixture seed decision"),
            false,
        )))
    }

    fn recover(&mut self, _view: RecoveryView) -> io::Result<RecoveryOutcome> {
        Ok(RecoveryOutcome::Paused)
    }

    fn rest(&mut self, _view: RestView) -> io::Result<RestOutcome> {
        Ok(RestOutcome::Continue)
    }

    fn preparing(&mut self) -> io::Result<()> {
        Ok(())
    }

    fn complete(&mut self, _view: CompletionView) -> io::Result<()> {
        Ok(())
    }
}

struct SeedSelectionOracle {
    version: String,
    corpus_ids: Vec<[u8; 32]>,
}

impl CandidateOrderOracle for SeedSelectionOracle {
    fn representation_version(&self) -> &str {
        &self.version
    }

    fn similar_notes_wave(
        &mut self,
        requests: &[SimilarNotesRequest],
        _representation_version: &str,
    ) -> Result<SimilarNotesWaveResponse> {
        Ok(SimilarNotesWaveResponse {
            responses: requests
                .iter()
                .map(|request| SimilarNotesResponse {
                    representation_version: self.version.clone(),
                    represented_rows: ROWS as u64,
                    total_rows: ROWS as u64,
                    complete: true,
                    candidates: self
                        .corpus_ids
                        .iter()
                        .copied()
                        .filter(|event_id| *event_id != request.note_id)
                        .enumerate()
                        .map(|(index, event_id)| Fp32Candidate {
                            event_id,
                            rank: index + 1,
                            cosine_score: 1.0 - index as f32 / ROWS as f32,
                        })
                        .collect(),
                })
                .collect(),
            metrics: SimilarNotesWaveMetrics {
                source_loading_ns: 0,
                query_encoding_ns: 0,
                matrix_scan_ns: 0,
                result_merge_ns: 0,
                encoded_queries: requests.len() as u64,
                cache_hits: 0,
                matrix_passes: 1,
                scanned_rows: ROWS as u64,
                scan_block_rows: ROWS as u64,
            },
        })
    }

    fn vectors_for_notes(
        &mut self,
        _note_ids: &[[u8; 32]],
        _representation_version: &str,
    ) -> Result<VectorsForNotesResponse> {
        panic!("seed selector must not request document vectors")
    }
}

impl EvaluatorUi for PausingEvaluator {
    fn rate(&mut self, view: RatingView<'_>) -> io::Result<RatingOutcome> {
        self.rating_presentations.push(view.presentation_number());
        self.presented_notes.push(view.note().to_owned());
        Ok(RatingOutcome::Paused)
    }

    fn recover(&mut self, view: RecoveryView) -> io::Result<RecoveryOutcome> {
        self.recovery_presentations.push(view.presentation_number());
        Ok(RecoveryOutcome::Paused)
    }

    fn rest(&mut self, _view: RestView) -> io::Result<RestOutcome> {
        Ok(RestOutcome::Paused)
    }

    fn preparing(&mut self) -> io::Result<()> {
        Ok(())
    }

    fn complete(&mut self, _view: CompletionView) -> io::Result<()> {
        Ok(())
    }
}

struct Fixture {
    temp: tempfile::TempDir,
    ndb_path: PathBuf,
    ordered_path: PathBuf,
    representation: PathBuf,
    geometry: PathBuf,
    model_bundle: PathBuf,
    runtime: PathBuf,
    ids: Vec<[u8; 32]>,
    representation_version: String,
    geometry_version: String,
}

impl Fixture {
    fn new() -> Self {
        let temp = tempfile::tempdir().expect("temporary directory");
        let ndb_path = temp.path().join("source-corpus.ndb");
        let ndb = Ndb::new(
            ndb_path.to_str().expect("UTF-8 NDB path"),
            &Config::new().set_mapsize(512 * 1024 * 1024),
        )
        .expect("open fixture NDB");
        let events = (0..ROWS)
            .map(|index| signed_event(&format!("note-{index}"), index as u64))
            .collect::<Vec<_>>();
        for event in &events {
            ndb.process_event(event).expect("submit fixture event");
        }
        wait_for_count(&ndb, events.len());
        drop(ndb);
        let ids = events
            .iter()
            .map(|event| event_id(event))
            .collect::<Vec<_>>();
        let ordered_path = temp.path().join("ordered-event-ids.bin");
        write_ids(&ordered_path, &ids);

        let model_bundle = temp.path().join("model-bundle");
        fs::create_dir_all(model_bundle.join("model")).expect("create model bundle");
        fs::write(
            model_bundle.join("model-lock.json"),
            b"fixture model lock\n",
        )
        .expect("write model lock");
        fs::write(model_bundle.join("model/weights.bin"), b"fixture weights\n")
            .expect("write model weights");
        let descriptor = fixture_descriptor(&model_bundle.join("model-lock.json"));
        let token_audit = temp.path().join("token-audit");
        let mut counter = FixtureLengthCounter {
            descriptor: descriptor.clone(),
        };
        audit_ordered_gte_tokens(
            &ndb_path,
            &ordered_path,
            &token_audit,
            &OrderedGteTokenAuditConfig {
                batch_size: 64,
                shard_rows: ROWS as u64,
            },
            &mut counter,
        )
        .expect("audit fixture token lengths");
        let batch_plan = temp.path().join("batch-plan");
        create_representation_batch_plan(
            &ordered_path,
            &token_audit,
            &batch_plan,
            &RepresentationBatchPlanConfig {
                shard_rows: ROWS as u64,
                batch_rows: 64,
            },
        )
        .expect("create fixture batch plan");
        let representation = temp.path().join("representation");
        let mut encoder = FixtureEncoder { descriptor };
        let built = build_representation_shards(
            &ndb_path,
            &ordered_path,
            &representation,
            &RepresentationBuildConfig {
                token_audit_path: token_audit,
                batch_plan_path: batch_plan,
                shard_ordinals: vec![0],
            },
            &mut encoder,
        )
        .expect("build fixture representation");
        let geometry = temp.path().join("geometry");
        derive_representation_geometry(&ordered_path, &representation, &geometry)
            .expect("derive fixture geometry");
        let geometry_version = hash_file(&geometry.join("manifest.json"));
        let runtime = temp.path().join("docker");
        fs::write(&runtime, b"#!/bin/sh\n").expect("write runtime stub");

        Self {
            temp,
            ndb_path,
            ordered_path,
            representation,
            geometry,
            model_bundle,
            runtime,
            ids,
            representation_version: built.representation_version,
            geometry_version,
        }
    }

    fn write_config(&self, workspace_name: &str, seeds: &[[u8; 32]], ratings: &[u8]) -> PathBuf {
        let config_path = self.temp.path().join(format!("{workspace_name}.json"));
        let config = serde_json::json!({
            "schema_version": 1,
            "purpose": HUMAN_LEARNING_PURPOSE,
            "workspace_path": self.temp.path().join(workspace_name),
            "source_corpus_data_path": self.ndb_path.join("data.mdb"),
            "source_ordered_event_ids_path": self.ordered_path,
            "source_representation_path": self.representation,
            "source_geometry_path": self.geometry,
            "model_bundle_path": self.model_bundle,
            "container_runtime": self.runtime,
            "container_name": format!("phase3-{workspace_name}"),
            "controller_image": format!("sha256:{}", "d".repeat(64)),
            "expected_representation_version": self.representation_version,
            "expected_geometry_version": self.geometry_version,
            "host_memory_reserve_bytes": 12 * 1024_u64.pow(3),
            "seeds": seeds.iter().zip(ratings).map(|(event_id, rating)| serde_json::json!({
                "event_id": hex(event_id),
                "rating": rating,
            })).collect::<Vec<_>>(),
        });
        fs::write(&config_path, serde_json::to_vec_pretty(&config).unwrap())
            .expect("write learning config");
        config_path
    }

    fn write_handoff_config(&self, workspace_name: &str, handoff_path: &Path) -> PathBuf {
        let config_path = self.temp.path().join(format!("{workspace_name}.json"));
        let config = serde_json::json!({
            "schema_version": 2,
            "purpose": HUMAN_LEARNING_PURPOSE,
            "workspace_path": self.temp.path().join(workspace_name),
            "source_corpus_data_path": self.ndb_path.join("data.mdb"),
            "source_ordered_event_ids_path": self.ordered_path,
            "source_representation_path": self.representation,
            "source_geometry_path": self.geometry,
            "model_bundle_path": self.model_bundle,
            "container_runtime": self.runtime,
            "container_name": format!("phase3-{workspace_name}"),
            "controller_image": format!("sha256:{}", "d".repeat(64)),
            "expected_representation_version": self.representation_version,
            "expected_geometry_version": self.geometry_version,
            "host_memory_reserve_bytes": 12 * 1024_u64.pow(3),
            "seed_selection_handoff_path": handoff_path,
        });
        fs::write(&config_path, serde_json::to_vec_pretty(&config).unwrap())
            .expect("write handoff learning config");
        config_path
    }
}

struct FixtureLengthCounter {
    descriptor: RepresentationDescriptor,
}

impl OrderedGteTokenCounter for FixtureLengthCounter {
    fn descriptor(&self) -> &RepresentationDescriptor {
        &self.descriptor
    }

    fn token_lengths(&mut self, _role: TokenRole, texts: &[&str]) -> Result<Vec<u32>> {
        Ok(vec![1; texts.len()])
    }
}

struct FixtureEncoder {
    descriptor: RepresentationDescriptor,
}

impl RepresentationEncoder for FixtureEncoder {
    fn descriptor(&self) -> &RepresentationDescriptor {
        &self.descriptor
    }

    fn encode_documents(&mut self, texts: &[&str]) -> Result<Vec<f32>> {
        let mut vectors = Vec::with_capacity(texts.len() * 2);
        for text in texts {
            let index = text
                .strip_prefix("note-")
                .and_then(|value| value.parse::<usize>().ok())
                .ok_or_else(|| Error::Invariant("unexpected fixture note".to_owned()))?;
            let angle = std::f64::consts::TAU * index as f64 / ROWS as f64;
            vectors.extend([angle.cos() as f32, angle.sin() as f32]);
        }
        Ok(vectors)
    }

    fn encode_queries(&mut self, _texts: &[&str]) -> Result<Vec<f32>> {
        self.encode_documents(_texts)
    }
}

fn fixture_descriptor(model_lock: &Path) -> RepresentationDescriptor {
    RepresentationDescriptor {
        model_id: "fixture/geometry".to_owned(),
        model_revision: "1".repeat(40),
        model_lock_sha256: hash_file(model_lock),
        worker_sha256: "3".repeat(64),
        dependency_lock_sha256: "4".repeat(64),
        container_image: "fixture@sha256:".to_owned() + &"5".repeat(64),
        torch_version: "fixture".to_owned(),
        transformers_version: "fixture".to_owned(),
        cuda_version: "fixture".to_owned(),
        execution_device: "cpu".to_owned(),
        dimensions: 2,
        model_token_ceiling: 32_768,
        document_input: "raw-note-content".to_owned(),
        query_instruction: "fixture-query-instruction".to_owned(),
        pooling: "last-token".to_owned(),
        normalization: "l2".to_owned(),
        numeric_format: "f32le".to_owned(),
    }
}

fn signed_event(content: &str, offset: u64) -> String {
    NoteBuilder::new()
        .kind(1)
        .content(content)
        .created_at(1_700_000_000 + offset)
        .sign(&[7_u8; 32])
        .build()
        .expect("sign fixture event")
        .json()
        .expect("fixture event JSON")
}

fn wait_for_count(ndb: &Ndb, expected: usize) {
    let deadline = Instant::now() + Duration::from_secs(30);
    loop {
        let transaction = Transaction::new(ndb).expect("read fixture transaction");
        let count = ndb
            .fold(
                &transaction,
                &[Filter::new().build()],
                0_usize,
                |count, _| count + 1,
            )
            .expect("count fixture events");
        if count == expected {
            return;
        }
        assert!(Instant::now() < deadline, "NDB persistence timeout");
        thread::sleep(Duration::from_millis(10));
    }
}

fn event_id(event: &str) -> [u8; 32] {
    let value: serde_json::Value = serde_json::from_str(event).expect("fixture event value");
    let encoded = value["id"].as_str().expect("fixture event ID");
    let mut output = [0_u8; 32];
    for (index, chunk) in encoded.as_bytes().chunks_exact(2).enumerate() {
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

fn write_ids(path: &Path, ids: &[[u8; 32]]) {
    let mut file = File::create(path).expect("create ordered ID file");
    for id in ids {
        file.write_all(id).expect("write ordered event ID");
    }
    file.sync_all().expect("sync ordered event IDs");
}

fn hash_file(path: &Path) -> String {
    let bytes = fs::read(path).expect("read hash input");
    format!("{:x}", Sha256::digest(bytes))
}

fn hex(bytes: &[u8]) -> String {
    bytes.iter().map(|byte| format!("{byte:02x}")).collect()
}

fn snapshot_tree(root: &Path) -> Vec<(PathBuf, Vec<u8>)> {
    let mut output = Vec::new();
    let mut pending = vec![root.to_owned()];
    while let Some(path) = pending.pop() {
        let mut entries = fs::read_dir(&path)
            .expect("read snapshot directory")
            .map(|entry| entry.expect("read snapshot entry").path())
            .collect::<Vec<_>>();
        entries.sort();
        for entry in entries.into_iter().rev() {
            let relative = entry.strip_prefix(root).unwrap().to_owned();
            let metadata = fs::symlink_metadata(&entry).expect("read snapshot metadata");
            if metadata.is_dir() {
                pending.push(entry);
            } else if metadata.file_type().is_symlink() {
                output.push((
                    relative,
                    fs::read_link(entry)
                        .unwrap()
                        .as_os_str()
                        .as_encoded_bytes()
                        .to_vec(),
                ));
            } else {
                output.push((relative, fs::read(entry).expect("read snapshot file")));
            }
        }
    }
    output.sort_by(|left, right| left.0.cmp(&right.0));
    output
}
