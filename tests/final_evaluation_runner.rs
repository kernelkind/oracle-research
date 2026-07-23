use std::collections::BTreeMap;
use std::io;
use std::thread;
use std::time::{Duration, Instant};

use nostrdb::{Config, Filter, Ndb, NoteBuilder, Transaction};
use oracle_mvp::adaptive_learning::{AdaptiveLearningCoordinator, CompletedAdaptiveLearning};
use oracle_mvp::candidate_order::{B16Boundary, CandidateOrderOracle};
use oracle_mvp::evaluator::{
    CompletionView, EvaluatorDecision, EvaluatorSubmission, EvaluatorUi, RatingOutcome, RatingView,
    RecoveryOutcome, RecoveryView, RestOutcome, RestView,
};
use oracle_mvp::final_evaluation_runner::{
    FinalEvaluationRunnerConfig, FinalEvaluationRunnerOutcome, resume_final_evaluation,
    run_final_evaluation,
};
use oracle_mvp::fp32_oracle::{
    Fp32Candidate, SimilarNotesRequest, SimilarNotesResponse, SimilarNotesWaveMetrics,
    SimilarNotesWaveResponse, StoredNoteVector, VectorsForNotesResponse,
};
use oracle_mvp::personalizer_learning::{
    BatchRating, CompactLearningController, CompactLearningSettings, EvidenceNote,
    RbfLearningController, RbfLearningSettings, ScaleLevel,
};
use oracle_mvp::quota_resolution::{EventLanguageOutcome, LanguageEligibility};
use oracle_mvp::representation::EventId;
use oracle_mvp::snapshot::{Error as SnapshotError, Result as SnapshotResult};

const VERSION: &str = "final-runner-representation-v1";

#[test]
fn display_failure_leaves_the_exact_next_note_pending_before_any_decision() {
    let fixture = Fixture::new();
    let session_path = fixture.temp.path().join("phase4-session.json");
    let config = FinalEvaluationRunnerConfig {
        corpus_path: fixture.corpus_path.clone(),
        corpus_identity: format!("sha256:{}", "33".repeat(32)),
        session_path: session_path.clone(),
        frozen_orders_path: fixture.temp.path().join("phase4-orders.json"),
        report_path: fixture.temp.path().join("phase4-report.json"),
        oracle_cache_path: fixture.temp.path().join("phase4-oracle-cache"),
        phase3_handoff_identity_sha256: "11".repeat(32),
        guarded_launch_identity_sha256: "aa".repeat(32),
        geometry_version: "22".repeat(32),
    };
    let corpus_before =
        std::fs::read(fixture.corpus_path.join("data.mdb")).expect("read corpus before run");
    let (completed, mut oracle) = fixture.completed_learning();
    let mut evaluator = FailOnFirstDisplay::default();

    let outcome = run_final_evaluation(&config, completed, &mut oracle, &mut evaluator)
        .expect("display failure is a recoverable pause");

    assert!(matches!(outcome, FinalEvaluationRunnerOutcome::Paused));
    assert_eq!(evaluator.presented_notes.len(), 1);
    let session: serde_json::Value = serde_json::from_reader(
        std::fs::File::open(&session_path).expect("open durable Phase 4 session"),
    )
    .expect("decode durable Phase 4 session");
    let pending = session["pending_presentation"]
        .as_object()
        .expect("the displayed note was durably marked pending");
    let pending_id = value_event_id(&pending["event_id"]);
    assert_eq!(
        evaluator.presented_notes[0],
        fixture.content_for(pending_id)
    );
    assert_eq!(
        session["waves"][0]["decisions"]
            .as_array()
            .expect("decision prefix")
            .len(),
        0
    );
    assert_eq!(
        std::fs::read(fixture.corpus_path.join("data.mdb")).expect("read corpus after run"),
        corpus_before
    );

    assert_cache_mutation_fails_closed(&fixture, &config, "wave-", |cached| {
        cached["response"]["metrics"]["source_loading_ns"] = serde_json::json!(123_456);
    });

    let (completed, _) = fixture.completed_learning();
    let mut recovery = CommitDuringRecovery::default();
    let resumed = resume_final_evaluation(&config, completed, &mut recovery)
        .expect("resume reconstructs the frozen orders from the durable Phase 4 cache");
    assert!(matches!(resumed, FinalEvaluationRunnerOutcome::Paused));
    assert_eq!(recovery.recovery_requests, 1);

    let stored = serde_json::from_reader::<_, serde_json::Value>(
        std::fs::File::open(&session_path).expect("open committed recovery session"),
    )
    .expect("decode committed recovery session");
    assert!(stored["pending_presentation"].is_null());
    assert_eq!(
        stored["waves"][0]["decisions"]
            .as_array()
            .expect("committed decision prefix")
            .len(),
        1
    );

    let (completed, _) = fixture.completed_learning();
    let mut next = PauseOnNextDisplay::default();
    let resumed = resume_final_evaluation(&config, completed, &mut next)
        .expect("continue after the committed recovered decision");
    assert_eq!(resumed, FinalEvaluationRunnerOutcome::Paused);
    assert_eq!(next.presented_notes.len(), 1);
    assert_ne!(next.presented_notes, evaluator.presented_notes);
}

#[test]
fn complete_run_routes_overlap_replaces_wrong_language_and_publishes_exact_results() {
    let fixture = Fixture::new();
    let config = FinalEvaluationRunnerConfig {
        corpus_path: fixture.corpus_path.clone(),
        corpus_identity: format!("sha256:{}", "44".repeat(32)),
        session_path: fixture.temp.path().join("complete-session.json"),
        frozen_orders_path: fixture.temp.path().join("complete-orders.json"),
        report_path: fixture.temp.path().join("complete-report.json"),
        oracle_cache_path: fixture.temp.path().join("complete-oracle-cache"),
        phase3_handoff_identity_sha256: "55".repeat(32),
        guarded_launch_identity_sha256: "aa".repeat(32),
        geometry_version: "66".repeat(32),
    };
    let (completed, mut oracle) = fixture.completed_learning();
    let mut evaluator = CompleteEvaluator {
        frozen_orders_path: config.frozen_orders_path.clone(),
        report_path: config.report_path.clone(),
        ..CompleteEvaluator::default()
    };

    let outcome = run_final_evaluation(&config, completed, &mut oracle, &mut evaluator)
        .expect("complete frozen final evaluation");

    assert_eq!(outcome, FinalEvaluationRunnerOutcome::Complete);
    assert_eq!(evaluator.presented_notes.len(), 201);
    assert_eq!(
        evaluator
            .presented_notes
            .iter()
            .collect::<std::collections::BTreeSet<_>>()
            .len(),
        201,
        "no final note may be displayed twice"
    );
    assert_eq!(evaluator.rests, 10);
    assert_eq!(evaluator.completion_presentations, Some(201));
    let report: serde_json::Value = serde_json::from_reader(
        std::fs::File::open(&config.report_path).expect("open final report"),
    )
    .expect("decode final report");
    assert_eq!(report["language"]["wrong_language_presentations"], 1);
    assert_eq!(report["language"]["unique_presentations"], 201);
    assert_eq!(
        report["compact"]["ratings"]
            .as_array()
            .expect("compact ratings")
            .len(),
        200
    );
    assert_eq!(
        report["rbf"]["ratings"]
            .as_array()
            .expect("RBF ratings")
            .len(),
        200
    );
    assert_eq!(report["compact"]["rating_sum"], 1_000);
    assert_eq!(report["rbf"]["rating_sum"], 1_000);
    assert_eq!(report["compact"]["passed"], true);
    assert_eq!(report["rbf"]["passed"], true);
    assert_eq!(report["passed"], true);
    assert!(
        !report["quota_audit"]
            .as_array()
            .expect("retained quota audit")
            .is_empty()
    );
    assert_eq!(report["compact"]["ratings"], report["rbf"]["ratings"]);
    assert_eq!(
        report["provenance"]["guarded_launch_identity_sha256"],
        "aa".repeat(32),
        "the final report must bind the exact guarded launch"
    );
    assert!(
        report["provenance"]["evaluator_transcript_identity_sha256"]
            .as_str()
            .is_some_and(is_sha256),
        "the final report must bind the exact evaluator transcript"
    );
}

#[test]
fn twenty_second_wrong_language_stops_before_any_more_notes_are_shown() {
    let fixture = Fixture::new();
    let config = FinalEvaluationRunnerConfig {
        corpus_path: fixture.corpus_path.clone(),
        corpus_identity: format!("sha256:{}", "77".repeat(32)),
        session_path: fixture.temp.path().join("language-failure-session.json"),
        frozen_orders_path: fixture.temp.path().join("language-failure-orders.json"),
        report_path: fixture.temp.path().join("language-failure-report.json"),
        oracle_cache_path: fixture.temp.path().join("language-failure-oracle-cache"),
        phase3_handoff_identity_sha256: "88".repeat(32),
        guarded_launch_identity_sha256: "aa".repeat(32),
        geometry_version: "99".repeat(32),
    };
    let (completed, mut oracle) = fixture.completed_learning();
    let mut evaluator = AllWrongLanguage::default();

    let error = run_final_evaluation(&config, completed, &mut oracle, &mut evaluator)
        .expect_err("the irreversible twenty-second language failure stops the run");

    assert!(error.to_string().contains("exceeded 21"));
    assert_eq!(evaluator.presentations, 22);
    assert!(!config.report_path.exists());
    let mut session: serde_json::Value = serde_json::from_reader(
        std::fs::File::open(&config.session_path).expect("open failed session"),
    )
    .expect("decode failed session");
    assert_eq!(session["phase"], "failed");
    session["failure"]["after_presentations"] = serde_json::json!(21);
    write_json(&config.session_path, &session);
    let (completed, _) = fixture.completed_learning();
    let mut evaluator = CompleteEvaluator::default();
    let error = resume_final_evaluation(&config, completed, &mut evaluator)
        .expect_err("a corrupted terminal failure record must fail closed");
    assert!(
        error.to_string().contains("failure record"),
        "unexpected corrupted-failure error: {error}"
    );
}

#[test]
fn completed_resume_rejects_mutated_transcript_completion_and_checkpoints() {
    let fixture = Fixture::new();
    let config = FinalEvaluationRunnerConfig {
        corpus_path: fixture.corpus_path.clone(),
        corpus_identity: format!("sha256:{}", "ab".repeat(32)),
        session_path: fixture.temp.path().join("sealed-session.json"),
        frozen_orders_path: fixture.temp.path().join("sealed-orders.json"),
        report_path: fixture.temp.path().join("sealed-report.json"),
        oracle_cache_path: fixture.temp.path().join("sealed-oracle-cache"),
        phase3_handoff_identity_sha256: "bc".repeat(32),
        guarded_launch_identity_sha256: "aa".repeat(32),
        geometry_version: "cd".repeat(32),
    };
    let (completed, mut oracle) = fixture.completed_learning();
    let mut evaluator = CompleteEvaluator {
        frozen_orders_path: config.frozen_orders_path.clone(),
        report_path: config.report_path.clone(),
        ..CompleteEvaluator::default()
    };
    assert_eq!(
        run_final_evaluation(&config, completed, &mut oracle, &mut evaluator)
            .expect("complete the sealed fixture"),
        FinalEvaluationRunnerOutcome::Complete
    );
    let original = std::fs::read(&config.session_path).expect("read completed session");

    let mut mutated: serde_json::Value =
        serde_json::from_slice(&original).expect("decode completed session");
    let rating = mutated["waves"]
        .as_array_mut()
        .expect("waves")
        .iter_mut()
        .flat_map(|wave| {
            wave["decisions"]
                .as_array_mut()
                .expect("decisions")
                .iter_mut()
        })
        .find(|decision| decision["outcome"] == "rated")
        .expect("rated decision");
    rating["rating"] = serde_json::json!(1);
    write_json(&config.session_path, &mutated);
    assert_completed_resume_fails(&fixture, &config, "decision checksum");

    let mut mutated: serde_json::Value =
        serde_json::from_slice(&original).expect("decode completed session");
    mutated["completion"]["compact_ratings"] = serde_json::json!(199);
    write_json(&config.session_path, &mutated);
    assert_completed_resume_fails(&fixture, &config, "completion");

    let mut mutated: serde_json::Value =
        serde_json::from_slice(&original).expect("decode completed session");
    mutated["rest_checkpoints"]
        .as_array_mut()
        .expect("rest checkpoints")
        .push(serde_json::json!({
            "after_presentations": 202,
            "continued": true
        }));
    write_json(&config.session_path, &mutated);
    assert_completed_resume_fails(&fixture, &config, "rest checkpoint");
}

#[test]
fn pause_after_final_decision_completes_to_a_stably_verifiable_report() {
    let fixture = Fixture::new();
    let config = FinalEvaluationRunnerConfig {
        corpus_path: fixture.corpus_path.clone(),
        corpus_identity: format!("sha256:{}", "de".repeat(32)),
        session_path: fixture.temp.path().join("final-pause-session.json"),
        frozen_orders_path: fixture.temp.path().join("final-pause-orders.json"),
        report_path: fixture.temp.path().join("final-pause-report.json"),
        oracle_cache_path: fixture.temp.path().join("final-pause-oracle-cache"),
        phase3_handoff_identity_sha256: "ef".repeat(32),
        guarded_launch_identity_sha256: "aa".repeat(32),
        geometry_version: "fa".repeat(32),
    };
    let (completed, mut oracle) = fixture.completed_learning();
    let mut evaluator = PauseAfterFinalDecision::default();
    assert_eq!(
        run_final_evaluation(&config, completed, &mut oracle, &mut evaluator)
            .expect("pause after the final accepted decision"),
        FinalEvaluationRunnerOutcome::Paused
    );
    assert_eq!(evaluator.presentations, 200);

    let (completed, _) = fixture.completed_learning();
    let mut completing = CompleteEvaluator::default();
    assert_eq!(
        resume_final_evaluation(&config, completed, &mut completing)
            .expect("seal the already-rated final wave"),
        FinalEvaluationRunnerOutcome::Complete
    );

    let (completed, _) = fixture.completed_learning();
    let mut verifying = CompleteEvaluator::default();
    assert_eq!(
        resume_final_evaluation(&config, completed, &mut verifying)
            .expect("the sealed report must verify on its next exact resume"),
        FinalEvaluationRunnerOutcome::Complete
    );
}

#[derive(Default)]
struct FailOnFirstDisplay {
    presented_notes: Vec<String>,
}

impl EvaluatorUi for FailOnFirstDisplay {
    fn rate(&mut self, view: RatingView<'_>) -> io::Result<RatingOutcome> {
        self.presented_notes.push(view.note().to_owned());
        Err(io::Error::other("injected display failure"))
    }

    fn recover(&mut self, _view: RecoveryView) -> io::Result<RecoveryOutcome> {
        panic!("a new session must not enter recovery")
    }

    fn rest(&mut self, _view: RestView) -> io::Result<RestOutcome> {
        panic!("the first presentation is not a rest boundary")
    }

    fn preparing(&mut self) -> io::Result<()> {
        Ok(())
    }

    fn complete(&mut self, _view: CompletionView) -> io::Result<()> {
        panic!("a paused session is not complete")
    }
}

#[derive(Default)]
struct CompleteEvaluator {
    frozen_orders_path: std::path::PathBuf,
    report_path: std::path::PathBuf,
    presented_notes: Vec<String>,
    wrong_language_used: bool,
    rests: usize,
    completion_presentations: Option<usize>,
}

impl EvaluatorUi for CompleteEvaluator {
    fn rate(&mut self, view: RatingView<'_>) -> io::Result<RatingOutcome> {
        assert!(
            self.frozen_orders_path.exists(),
            "orders must be sealed before evaluator input"
        );
        assert!(
            !self.report_path.exists(),
            "the report must not exist before judgments finish"
        );
        self.presented_notes.push(view.note().to_owned());
        let decision = if self.wrong_language_used {
            EvaluatorDecision::Rating(5)
        } else {
            self.wrong_language_used = true;
            EvaluatorDecision::WrongLanguage
        };
        Ok(RatingOutcome::Submitted(EvaluatorSubmission::new(
            decision, false,
        )))
    }

    fn recover(&mut self, _view: RecoveryView) -> io::Result<RecoveryOutcome> {
        panic!("an uninterrupted run must not recover a pending note")
    }

    fn rest(&mut self, _view: RestView) -> io::Result<RestOutcome> {
        self.rests += 1;
        Ok(RestOutcome::Continue)
    }

    fn preparing(&mut self) -> io::Result<()> {
        Ok(())
    }

    fn complete(&mut self, view: CompletionView) -> io::Result<()> {
        self.completion_presentations = Some(view.presentations_stored());
        Ok(())
    }
}

#[derive(Default)]
struct AllWrongLanguage {
    presentations: usize,
}

#[derive(Default)]
struct PauseAfterFinalDecision {
    presentations: usize,
}

impl EvaluatorUi for PauseAfterFinalDecision {
    fn rate(&mut self, _view: RatingView<'_>) -> io::Result<RatingOutcome> {
        self.presentations += 1;
        Ok(RatingOutcome::Submitted(EvaluatorSubmission::new(
            EvaluatorDecision::Rating(5),
            self.presentations == 200,
        )))
    }

    fn recover(&mut self, _view: RecoveryView) -> io::Result<RecoveryOutcome> {
        panic!("an uninterrupted final-decision pause does not recover")
    }

    fn rest(&mut self, _view: RestView) -> io::Result<RestOutcome> {
        Ok(RestOutcome::Continue)
    }

    fn preparing(&mut self) -> io::Result<()> {
        Ok(())
    }

    fn complete(&mut self, _view: CompletionView) -> io::Result<()> {
        panic!("the invocation that pauses after its final decision does not seal the report")
    }
}

impl EvaluatorUi for AllWrongLanguage {
    fn rate(&mut self, _view: RatingView<'_>) -> io::Result<RatingOutcome> {
        self.presentations += 1;
        Ok(RatingOutcome::Submitted(EvaluatorSubmission::new(
            EvaluatorDecision::WrongLanguage,
            false,
        )))
    }

    fn recover(&mut self, _view: RecoveryView) -> io::Result<RecoveryOutcome> {
        panic!("uninterrupted language failure must not recover")
    }

    fn rest(&mut self, _view: RestView) -> io::Result<RestOutcome> {
        Ok(RestOutcome::Continue)
    }

    fn preparing(&mut self) -> io::Result<()> {
        Ok(())
    }

    fn complete(&mut self, _view: CompletionView) -> io::Result<()> {
        panic!("invalid language phase has no quality completion")
    }
}

#[derive(Default)]
struct CommitDuringRecovery {
    recovery_requests: usize,
}

impl EvaluatorUi for CommitDuringRecovery {
    fn rate(&mut self, _view: RatingView<'_>) -> io::Result<RatingOutcome> {
        panic!("a pending presentation must recover before redisplay")
    }

    fn recover(&mut self, _view: RecoveryView) -> io::Result<RecoveryOutcome> {
        self.recovery_requests += 1;
        Ok(RecoveryOutcome::Submitted(EvaluatorSubmission::new(
            EvaluatorDecision::Rating(6),
            true,
        )))
    }

    fn rest(&mut self, _view: RestView) -> io::Result<RestOutcome> {
        panic!("recovery is not a rest boundary")
    }

    fn preparing(&mut self) -> io::Result<()> {
        Ok(())
    }

    fn complete(&mut self, _view: CompletionView) -> io::Result<()> {
        panic!("recovery is not complete")
    }
}

#[derive(Default)]
struct PauseOnNextDisplay {
    presented_notes: Vec<String>,
}

impl EvaluatorUi for PauseOnNextDisplay {
    fn rate(&mut self, view: RatingView<'_>) -> io::Result<RatingOutcome> {
        self.presented_notes.push(view.note().to_owned());
        Ok(RatingOutcome::Paused)
    }

    fn recover(&mut self, _view: RecoveryView) -> io::Result<RecoveryOutcome> {
        panic!("the committed recovered note must not be recovered twice")
    }

    fn rest(&mut self, _view: RestView) -> io::Result<RestOutcome> {
        panic!("one committed presentation is not a rest boundary")
    }

    fn preparing(&mut self) -> io::Result<()> {
        Ok(())
    }

    fn complete(&mut self, _view: CompletionView) -> io::Result<()> {
        panic!("the resumed session is not complete")
    }
}

struct Fixture {
    temp: tempfile::TempDir,
    corpus_path: std::path::PathBuf,
    event_ids: Vec<EventId>,
    contents: Vec<String>,
}

impl Fixture {
    fn new() -> Self {
        let temp = tempfile::tempdir().expect("temporary directory");
        let corpus_path = temp.path().join("corpus.ndb");
        let ndb = open_ndb(&corpus_path);
        let contents = (0..500)
            .map(|index| format!("raw final evaluation fixture note {index}"))
            .collect::<Vec<_>>();
        let events = contents
            .iter()
            .enumerate()
            .map(|(index, content)| signed_event(content, index as u64))
            .collect::<Vec<_>>();
        for event in &events {
            ndb.process_event(event).expect("submit fixture event");
        }
        wait_for_count(&ndb, events.len());
        drop(ndb);
        Self {
            temp,
            corpus_path,
            event_ids: events.iter().map(|event| event_id(event)).collect(),
            contents,
        }
    }

    fn completed_learning(&self) -> (Box<CompletedAdaptiveLearning>, FixtureOracle) {
        let evidence = || {
            self.event_ids[..5]
                .iter()
                .copied()
                .map(|event_id| {
                    EvidenceNote::new(event_id, vec![1.0, 0.0], 7).expect("positive seed")
                })
                .collect()
        };
        let compact = CompactLearningController::new(
            CompactLearningSettings::new(VERSION, 0.5, 1.0, 2.0, ScaleLevel::Mass64)
                .expect("compact settings"),
            evidence(),
        )
        .expect("compact controller");
        let rbf = RbfLearningController::new(
            RbfLearningSettings::new(VERSION, 0.5, 1.0, 2.0).expect("RBF settings"),
            evidence(),
        )
        .expect("RBF controller");
        let mut oracle = FixtureOracle::new(self.event_ids.clone());
        let mut coordinator = AdaptiveLearningCoordinator::new(
            &oracle,
            compact,
            rbf,
            B16Boundary::new(VERSION, 0.0).expect("B16"),
        )
        .expect("adaptive-learning coordinator");
        for _ in 0..10 {
            coordinator
                .start_next_round(&mut oracle)
                .expect("start learning round");
            while let Some(wave) = coordinator.pending_language_wave().cloned() {
                coordinator
                    .submit_language_outcomes(
                        wave.wave_id(),
                        wave.event_ids()
                            .iter()
                            .copied()
                            .map(|event_id| {
                                EventLanguageOutcome::new(event_id, LanguageEligibility::Eligible)
                            })
                            .collect(),
                    )
                    .expect("accept language wave");
            }
            let ratings = coordinator
                .pending_rating_event_ids()
                .expect("pending ratings")
                .iter()
                .copied()
                .map(|event_id| BatchRating::new(event_id, 7).expect("valid rating"))
                .collect();
            coordinator
                .submit_ratings(ratings)
                .expect("complete learning round");
        }
        let completed = coordinator
            .into_completed()
            .unwrap_or_else(|_| panic!("ten rounds completed"));
        (Box::new(completed), oracle)
    }

    fn content_for(&self, event_id: EventId) -> String {
        let index = self
            .event_ids
            .iter()
            .position(|candidate| *candidate == event_id)
            .expect("fixture event ID");
        self.contents[index].clone()
    }
}

struct FixtureOracle {
    event_ids: Vec<EventId>,
    responses: BTreeMap<EventId, SimilarNotesResponse>,
}

impl FixtureOracle {
    fn new(event_ids: Vec<EventId>) -> Self {
        Self {
            event_ids,
            responses: BTreeMap::new(),
        }
    }

    fn response(&self, source: EventId) -> SimilarNotesResponse {
        SimilarNotesResponse {
            representation_version: VERSION.to_owned(),
            represented_rows: self.event_ids.len() as u64,
            total_rows: self.event_ids.len() as u64,
            complete: true,
            candidates: self
                .event_ids
                .iter()
                .copied()
                .filter(|event_id| *event_id != source)
                .enumerate()
                .map(|(index, event_id)| Fp32Candidate {
                    event_id,
                    rank: index + 1,
                    cosine_score: 1.0 - index as f32 / 10_000.0,
                })
                .collect(),
        }
    }
}

impl CandidateOrderOracle for FixtureOracle {
    fn representation_version(&self) -> &str {
        VERSION
    }

    fn similar_notes_wave(
        &mut self,
        requests: &[SimilarNotesRequest],
        representation_version: &str,
    ) -> SnapshotResult<SimilarNotesWaveResponse> {
        if representation_version != VERSION || requests.is_empty() {
            return Err(SnapshotError::InvalidQuery(
                "unexpected fixture query".to_owned(),
            ));
        }
        let missing = requests
            .iter()
            .filter(|request| !self.responses.contains_key(&request.note_id))
            .map(|request| request.note_id)
            .collect::<Vec<_>>();
        for event_id in missing.iter().copied() {
            self.responses.insert(event_id, self.response(event_id));
        }
        Ok(SimilarNotesWaveResponse {
            responses: requests
                .iter()
                .map(|request| self.responses[&request.note_id].clone())
                .collect(),
            metrics: SimilarNotesWaveMetrics {
                source_loading_ns: 0,
                query_encoding_ns: 0,
                matrix_scan_ns: 0,
                result_merge_ns: 0,
                encoded_queries: missing.len() as u64,
                cache_hits: (requests.len() - missing.len()) as u64,
                matrix_passes: u64::from(!missing.is_empty()),
                scanned_rows: if missing.is_empty() {
                    0
                } else {
                    self.event_ids.len() as u64
                },
                scan_block_rows: 4_096,
            },
        })
    }

    fn vectors_for_notes(
        &mut self,
        note_ids: &[EventId],
        representation_version: &str,
    ) -> SnapshotResult<VectorsForNotesResponse> {
        if representation_version != VERSION {
            return Err(SnapshotError::InvalidQuery(
                "unexpected fixture representation".to_owned(),
            ));
        }
        Ok(VectorsForNotesResponse {
            representation_version: VERSION.to_owned(),
            represented_rows: self.event_ids.len() as u64,
            total_rows: self.event_ids.len() as u64,
            complete: true,
            lookup_elapsed_ns: 0,
            vectors: note_ids
                .iter()
                .copied()
                .map(|event_id| StoredNoteVector {
                    event_id,
                    vector: vec![1.0, 0.0],
                })
                .collect(),
        })
    }
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
        let transaction = Transaction::new(ndb).expect("read transaction");
        let count = ndb
            .fold(
                &transaction,
                &[Filter::new().build()],
                0_usize,
                |count, _| count + 1,
            )
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
        .sign(&[8_u8; 32])
        .build()
        .expect("sign fixture event")
        .json()
        .expect("event JSON")
}

fn event_id(event: &str) -> EventId {
    let value: serde_json::Value = serde_json::from_str(event).expect("event value");
    let encoded = value["id"].as_str().expect("event ID");
    let mut output = [0_u8; 32];
    for (index, chunk) in encoded.as_bytes().chunks_exact(2).enumerate() {
        output[index] = (decode_hex(chunk[0]) << 4) | decode_hex(chunk[1]);
    }
    output
}

fn value_event_id(value: &serde_json::Value) -> EventId {
    let bytes = value.as_array().expect("event ID byte array");
    let mut event_id = [0_u8; 32];
    for (output, value) in event_id.iter_mut().zip(bytes) {
        *output = value.as_u64().expect("event ID byte") as u8;
    }
    event_id
}

fn assert_completed_resume_fails(
    fixture: &Fixture,
    config: &FinalEvaluationRunnerConfig,
    expected: &str,
) {
    let (completed, _) = fixture.completed_learning();
    let mut evaluator = CompleteEvaluator::default();
    let error = resume_final_evaluation(config, completed, &mut evaluator)
        .expect_err("a mutated completed session must fail closed");
    assert!(
        error.to_string().contains(expected),
        "unexpected completed-session error: {error}"
    );
}

fn assert_cache_mutation_fails_closed(
    fixture: &Fixture,
    config: &FinalEvaluationRunnerConfig,
    prefix: &str,
    mutate: impl FnOnce(&mut serde_json::Value),
) {
    let path = std::fs::read_dir(&config.oracle_cache_path)
        .expect("read Phase 4 Oracle cache")
        .map(|entry| entry.expect("cache entry").path())
        .find(|path| {
            path.file_name()
                .and_then(|name| name.to_str())
                .is_some_and(|name| name.starts_with(prefix))
        })
        .expect("expected Phase 4 cache entry");
    let original = std::fs::read(&path).expect("read cached response");
    let mut cached: serde_json::Value =
        serde_json::from_slice(&original).expect("decode cached response");
    mutate(&mut cached);
    write_json(&path, &cached);

    let (completed, _) = fixture.completed_learning();
    let mut evaluator = CompleteEvaluator::default();
    let error = resume_final_evaluation(config, completed, &mut evaluator)
        .expect_err("a mutated cached response must fail closed");
    assert!(
        error.to_string().contains("checksum"),
        "unexpected cached-response error: {error}"
    );
    std::fs::write(path, original).expect("restore cached response");
}

fn write_json(path: &std::path::Path, value: &serde_json::Value) {
    let mut bytes = serde_json::to_vec_pretty(value).expect("encode mutated session");
    bytes.push(b'\n');
    std::fs::write(path, bytes).expect("write mutated session");
}

fn is_sha256(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

fn decode_hex(value: u8) -> u8 {
    match value {
        b'0'..=b'9' => value - b'0',
        b'a'..=b'f' => value - b'a' + 10,
        _ => panic!("invalid hex"),
    }
}
