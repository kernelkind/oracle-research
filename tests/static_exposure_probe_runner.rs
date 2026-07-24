use std::collections::BTreeSet;
use std::io;
use std::thread;
use std::time::{Duration, Instant};

use nostrdb::{Config, Filter, Ndb, NoteBuilder, Transaction};
use oracle_mvp::evaluator::{
    CompletionView, EvaluatorDecision, EvaluatorSubmission, EvaluatorUi, RatingOutcome, RatingView,
    RecoveryOutcome, RecoveryView, RepetitionAnswer, RepetitionOutcome, RepetitionUi,
    RepetitionView, RestOutcome, RestView,
};
use oracle_mvp::representation::EventId;
use oracle_mvp::static_exposure_probe_runner::{
    FullPoolExposureGateProtocol, FullPoolExposureSeed, StaticExposureProbeCandidate,
    StaticExposureProbeInput, StaticExposureProbeRunnerConfig, StaticExposureProbeRunnerOutcome,
    StaticExposureProbeSourceProvenance, StaticExposureProbeVerification,
    replay_completed_static_exposure_probe, run_full_pool_exposure_probe,
    run_static_exposure_probe, verify_full_pool_exposure_probe, verify_static_exposure_probe,
};
use sha2::{Digest, Sha256};

#[test]
fn complete_probe_records_forty_unique_ratings_and_separate_repetition_answers() {
    let fixture = Fixture::new();
    let config = fixture.config("complete");
    let input = fixture.input();
    let corpus_before =
        std::fs::read(fixture.corpus_path.join("data.mdb")).expect("read corpus before probe");
    let mut evaluator = CompleteEvaluator::default();

    let outcome = run_static_exposure_probe(&config, &input, &mut evaluator)
        .expect("complete the static exposure probe");

    assert_eq!(outcome, StaticExposureProbeRunnerOutcome::Complete);
    assert_eq!(evaluator.presented.len(), 40);
    assert_eq!(
        evaluator.presented.iter().collect::<BTreeSet<_>>().len(),
        40,
        "the probe must never present one event twice"
    );
    assert_eq!(evaluator.repetition_prompts, 40);
    assert_eq!(evaluator.rests, 3);
    assert_eq!(evaluator.completed, Some(40));
    assert_eq!(
        std::fs::read(fixture.corpus_path.join("data.mdb")).expect("read corpus after probe"),
        corpus_before,
        "displaying notes must not mutate the prepared corpus data"
    );

    let report: serde_json::Value = serde_json::from_reader(
        std::fs::File::open(&config.report_path).expect("open complete probe report"),
    )
    .expect("decode complete probe report");
    assert_eq!(report["valid_ratings"], 40);
    assert_eq!(report["presentations"], 40);
    assert_eq!(report["ratings"]["5"], 40);
    assert_eq!(report["repetition_answers"]["yes"], 20);
    assert_eq!(report["repetition_answers"]["no"], 20);
    assert_eq!(report["selection"]["tranche_size"], 64);
    assert_eq!(report["selection"]["half_life"], 20);
    assert_eq!(
        report["selection"]["typical_pair_cosine"],
        serde_json::json!(0.42087467246166055_f64)
    );
    assert_eq!(
        report["presentation_audit"][0]["vector_identity_sha256"]
            .as_str()
            .expect("chosen vector identity")
            .len(),
        64
    );
    assert_eq!(
        verify_static_exposure_probe(&config, &input)
            .expect("verify completed probe without evaluator input"),
        StaticExposureProbeVerification::Complete {
            presentations: 40,
            valid_ratings: 40,
        }
    );
}

#[test]
fn full_pool_gate_reuses_the_durable_runner_with_twenty_ratings_and_one_rest() {
    let fixture = Fixture::new();
    let config = fixture.config("full-pool-complete");
    let input = fixture.full_pool_input(false);
    let mut evaluator = CompleteEvaluator::default();

    let outcome = run_full_pool_exposure_probe(&config, &input, &mut evaluator)
        .expect("complete the full-pool exposure-gated probe");

    assert_eq!(outcome, StaticExposureProbeRunnerOutcome::Complete);
    assert_eq!(evaluator.presented.len(), 20);
    assert_eq!(
        evaluator.presented.iter().collect::<BTreeSet<_>>().len(),
        20
    );
    assert_eq!(evaluator.repetition_prompts, 20);
    assert_eq!(evaluator.rests, 1);
    assert_eq!(evaluator.completed, Some(20));

    let report: serde_json::Value = serde_json::from_reader(
        std::fs::File::open(&config.report_path).expect("open full-pool report"),
    )
    .expect("decode full-pool report");
    assert_eq!(report["valid_ratings"], 20);
    assert_eq!(
        report["selection"]["policy"],
        "highest-frozen-support-below-full-pool-exposure-ceiling-v1"
    );
    assert_eq!(
        report["selection"]["exposure_ceiling"],
        serde_json::json!(0.32686638460886658_f64)
    );
    assert_eq!(report["termination"], "valid_rating_quota_reached");
}

#[test]
fn full_pool_gate_seals_candidate_exhaustion_without_relaxing_the_ceiling() {
    let fixture = Fixture::new();
    let config = fixture.config("full-pool-exhausted");
    let input = fixture.full_pool_input(true);
    let mut evaluator = CompletionOnlyEvaluator::default();

    let outcome = run_full_pool_exposure_probe(&config, &input, &mut evaluator)
        .expect("seal the exhausted full-pool probe");

    assert_eq!(outcome, StaticExposureProbeRunnerOutcome::Complete);
    assert_eq!(evaluator.completed, Some(0));
    let report: serde_json::Value = serde_json::from_reader(
        std::fs::File::open(&config.report_path).expect("open exhausted report"),
    )
    .expect("decode exhausted report");
    assert_eq!(report["termination"], "candidate_supply_exhausted");
    assert_eq!(report["valid_ratings"], 0);
    assert_eq!(
        verify_full_pool_exposure_probe(&config, &input).expect("verify deterministic exhaustion"),
        StaticExposureProbeVerification::Complete {
            presentations: 0,
            valid_ratings: 0,
        }
    );
}

#[test]
fn full_pool_gate_seals_the_second_wrong_language_without_corrupting_resume() {
    let fixture = Fixture::new();
    let config = fixture.config("full-pool-language-reserve");
    let input = fixture.full_pool_input(false);
    let mut evaluator = WrongLanguageUntilComplete::default();

    let outcome = run_full_pool_exposure_probe(&config, &input, &mut evaluator)
        .expect("seal the exhausted language reserve");

    assert_eq!(outcome, StaticExposureProbeRunnerOutcome::Complete);
    assert_eq!(evaluator.presented, 2);
    assert_eq!(evaluator.completed, Some(2));
    let report: serde_json::Value = serde_json::from_reader(
        std::fs::File::open(&config.report_path).expect("open language-reserve report"),
    )
    .expect("decode language-reserve report");
    assert_eq!(report["termination"], "wrong_language_reserve_exhausted");
    assert_eq!(report["wrong_language_presentations"], 2);
    assert_eq!(
        verify_full_pool_exposure_probe(&config, &input)
            .expect("verify durable language-reserve termination"),
        StaticExposureProbeVerification::Complete {
            presentations: 2,
            valid_ratings: 0,
        }
    );
}

#[test]
fn completed_full_pool_probe_cannot_claim_language_reserve_exhaustion_after_one_rejection() {
    let fixture = Fixture::new();
    let config = fixture.config("forged-language-reserve");
    let input = fixture.full_pool_input(false);
    run_full_pool_exposure_probe(&config, &input, &mut WrongLanguageUntilComplete::default())
        .expect("create a legitimate exhausted language-reserve artifact");
    forge_one_rejection_language_reserve_completion(&config);

    let error = verify_full_pool_exposure_probe(&config, &input)
        .expect_err("one wrong-language rejection must not exhaust a reserve of one");

    assert!(error.to_string().contains("wrong-language"));
}

#[test]
fn source_provenance_is_retained_in_the_frozen_probe_input() {
    let fixture = Fixture::new();
    let provenance = StaticExposureProbeSourceProvenance::new(
        "31".repeat(32),
        "32".repeat(32),
        "33".repeat(32),
        "34".repeat(32),
        "35".repeat(32),
        "36".repeat(32),
    )
    .expect("valid source provenance");

    let input = fixture.input().with_source_provenance(provenance.clone());

    assert_eq!(input.source_provenance(), Some(&provenance));
}

#[test]
fn full_pool_protocol_rejects_a_different_source_input_identity() {
    let fixture = Fixture::new();
    let input = fixture.input();
    let protocol = full_pool_protocol(&input, "ff".repeat(32));

    let error = input
        .with_full_pool_exposure_gate(protocol)
        .expect_err("source input identity must be enforced");

    assert!(error.to_string().contains("different source probe input"));
}

#[test]
fn completed_source_replay_returns_the_verified_ordered_presentations() {
    let fixture = Fixture::new();
    let config = fixture.config("completed-replay");
    let input = fixture.input();
    run_static_exposure_probe(&config, &input, &mut CompleteEvaluator::default())
        .expect("complete source probe");

    let replay =
        replay_completed_static_exposure_probe(&config, &input).expect("replay completed source");

    assert_eq!(replay.presentations().len(), 40);
    assert_eq!(
        replay
            .presentations()
            .iter()
            .map(|presentation| presentation.event_id())
            .collect::<BTreeSet<_>>()
            .len(),
        40
    );
    assert!(
        replay
            .presentations()
            .iter()
            .all(|presentation| presentation.source_exposure().is_finite())
    );
}

#[test]
fn pause_after_rating_resumes_at_the_unanswered_repetition_prompt_without_redisplay() {
    let fixture = Fixture::new();
    let config = fixture.config("resume");
    let input = fixture.input();
    let mut pausing = PauseAfterFirstRating::default();

    let outcome = run_static_exposure_probe(&config, &input, &mut pausing)
        .expect("pause after the first durable rating");

    assert_eq!(outcome, StaticExposureProbeRunnerOutcome::Paused);
    assert_eq!(pausing.presented, 1);
    assert_eq!(pausing.repetition_prompts, 0);

    let mut resuming = ResumeAtRepetition::default();
    let outcome = run_static_exposure_probe(&config, &input, &mut resuming)
        .expect("resume the exact incomplete decision");

    assert_eq!(outcome, StaticExposureProbeRunnerOutcome::Paused);
    assert_eq!(resuming.repetition_prompts, 1);
    assert_eq!(
        resuming.repetition_notes,
        vec!["static exposure candidate 3"]
    );
    assert_eq!(
        resuming.rating_prompts, 1,
        "after completing the stored diagnostic, only the next note may be rated"
    );
    let session: serde_json::Value = serde_json::from_reader(
        std::fs::File::open(&config.session_path).expect("open resumed probe session"),
    )
    .expect("decode resumed probe session");
    let presentations = session["presentations"]
        .as_array()
        .expect("probe presentations");
    assert_eq!(presentations.len(), 1);
    assert_eq!(presentations[0]["rating"], 5);
    assert_eq!(presentations[0]["repetition"], "no");
    assert!(
        session["pending_presentation"].is_object(),
        "the next displayed note remains durably pending"
    );
}

#[test]
fn full_pool_pause_after_rating_resumes_the_same_repetition_prompt() {
    let fixture = Fixture::new();
    let config = fixture.config("full-pool-resume");
    let input = fixture.full_pool_input(false);
    let mut pausing = PauseAfterFirstRating::default();

    assert_eq!(
        run_full_pool_exposure_probe(&config, &input, &mut pausing)
            .expect("pause after durable full-pool rating"),
        StaticExposureProbeRunnerOutcome::Paused
    );
    let mut resuming = ResumeAtRepetition::default();
    assert_eq!(
        run_full_pool_exposure_probe(&config, &input, &mut resuming)
            .expect("resume full-pool repetition"),
        StaticExposureProbeRunnerOutcome::Paused
    );

    assert_eq!(resuming.repetition_prompts, 1);
    assert_eq!(resuming.rating_prompts, 1);
    let session: serde_json::Value = serde_json::from_reader(
        std::fs::File::open(&config.session_path).expect("open resumed full-pool session"),
    )
    .expect("decode resumed full-pool session");
    assert_eq!(session["presentations"].as_array().unwrap().len(), 1);
    assert_eq!(session["presentations"][0]["rating"], 5);
    assert_eq!(session["presentations"][0]["repetition"], "no");
}

#[test]
fn full_pool_unrated_pending_note_recovers_without_changing_selection() {
    let fixture = Fixture::new();
    let config = fixture.config("full-pool-unrated-recovery");
    let input = fixture.full_pool_input(false);

    assert_eq!(
        run_full_pool_exposure_probe(&config, &input, &mut PauseBeforeRating)
            .expect("pause with a durable unrated selection"),
        StaticExposureProbeRunnerOutcome::Paused
    );
    let pending_before: serde_json::Value = serde_json::from_reader(
        std::fs::File::open(&config.session_path).expect("open paused session"),
    )
    .expect("decode paused session");
    let selected_before = pending_before["pending_presentation"]["selection"]["event_id"].clone();

    let mut resuming = RecoverRatingThenPauseNext::default();
    assert_eq!(
        run_full_pool_exposure_probe(&config, &input, &mut resuming)
            .expect("recover the durable selection"),
        StaticExposureProbeRunnerOutcome::Paused
    );
    let resumed: serde_json::Value = serde_json::from_reader(
        std::fs::File::open(&config.session_path).expect("open recovered session"),
    )
    .expect("decode recovered session");
    assert_eq!(resumed["presentations"][0]["event_id"], selected_before);
    assert_eq!(resuming.recoveries, 1);
    assert_eq!(resuming.repetitions, 1);
    assert_eq!(resuming.next_rating_prompts, 1);
}

#[test]
fn full_pool_selection_order_is_independent_of_ratings_and_repetition_answers() {
    let fixture = Fixture::new();
    let input = fixture.full_pool_input(false);
    let low_config = fixture.config("full-pool-low-outcomes");
    let high_config = fixture.config("full-pool-high-outcomes");

    run_full_pool_exposure_probe(
        &low_config,
        &input,
        &mut FixedCompleteEvaluator::new(1, RepetitionAnswer::Yes),
    )
    .expect("complete low-outcome probe");
    run_full_pool_exposure_probe(
        &high_config,
        &input,
        &mut FixedCompleteEvaluator::new(7, RepetitionAnswer::No),
    )
    .expect("complete high-outcome probe");

    let low: serde_json::Value = serde_json::from_reader(
        std::fs::File::open(&low_config.report_path).expect("open low report"),
    )
    .expect("decode low report");
    let high: serde_json::Value = serde_json::from_reader(
        std::fs::File::open(&high_config.report_path).expect("open high report"),
    )
    .expect("decode high report");
    let event_order = |report: &serde_json::Value| {
        report["presentation_audit"]
            .as_array()
            .unwrap()
            .iter()
            .map(|presentation| presentation["event_id"].clone())
            .collect::<Vec<_>>()
    };
    assert_eq!(event_order(&low), event_order(&high));
    assert_ne!(low["ratings"], high["ratings"]);
    assert_ne!(low["repetition_answers"], high["repetition_answers"]);
}

#[test]
fn changed_rating_is_rejected_before_any_more_evaluator_input() {
    let fixture = Fixture::new();
    let config = fixture.config("tampered");
    let input = fixture.input();
    run_static_exposure_probe(&config, &input, &mut PauseAfterFirstRating::default())
        .expect("store the first rating");
    run_static_exposure_probe(&config, &input, &mut ResumeAtRepetition::default())
        .expect("commit the first presentation and pause on the second");

    let mut session: serde_json::Value = serde_json::from_reader(
        std::fs::File::open(&config.session_path).expect("open probe session"),
    )
    .expect("decode probe session");
    session["presentations"][0]["rating"] = serde_json::json!(1);
    write_json(&config.session_path, &session);

    let error = run_static_exposure_probe(&config, &input, &mut NeverCalled)
        .expect_err("a changed durable rating must fail closed");

    assert!(error.to_string().contains("checksum"));
}

#[test]
fn third_wrong_language_presentation_stops_the_bounded_probe() {
    let fixture = Fixture::new();
    let config = fixture.config("language-ceiling");
    let input = fixture.input();
    let mut evaluator = AllWrongLanguage::default();

    let error = run_static_exposure_probe(&config, &input, &mut evaluator)
        .expect_err("the third wrong-language presentation must stop the probe");

    assert_eq!(evaluator.presented, 3);
    assert!(error.to_string().contains("wrong-language"));
}

#[test]
fn stale_report_without_a_session_is_rejected_before_evaluator_input() {
    let fixture = Fixture::new();
    let config = fixture.config("stale-report");
    let input = fixture.input();
    std::fs::write(&config.report_path, b"stale\n").expect("create stale report");

    let error = run_static_exposure_probe(&config, &input, &mut NeverCalled)
        .expect_err("a report without its session must fail immediately");

    assert!(error.to_string().contains("report"));
    assert!(!config.session_path.exists());
}

struct Fixture {
    temp: tempfile::TempDir,
    corpus_path: std::path::PathBuf,
    event_ids: Vec<EventId>,
}

impl Fixture {
    fn new() -> Self {
        let temp = tempfile::tempdir().expect("create probe fixture");
        let corpus_path = temp.path().join("corpus.ndb");
        std::fs::create_dir(&corpus_path).expect("create corpus directory");
        let ndb = open_ndb(&corpus_path);
        let mut event_ids = Vec::new();
        for index in 0..80_u64 {
            let event = signed_event(&format!("static exposure candidate {index}"), index);
            event_ids.push(event_id(&event));
            ndb.process_event(&event).expect("submit fixture event");
        }
        wait_for_count(&ndb, event_ids.len());
        drop(ndb);
        Self {
            temp,
            corpus_path,
            event_ids,
        }
    }

    fn config(&self, name: &str) -> StaticExposureProbeRunnerConfig {
        StaticExposureProbeRunnerConfig {
            corpus_path: self.corpus_path.clone(),
            corpus_identity: format!("sha256:{}", "11".repeat(32)),
            session_path: self.temp.path().join(format!("{name}-session.json")),
            report_path: self.temp.path().join(format!("{name}-report.json")),
        }
    }

    fn input(&self) -> StaticExposureProbeInput {
        let candidates = self
            .event_ids
            .iter()
            .copied()
            .enumerate()
            .map(|(index, event_id)| {
                let angle = index as f32 * std::f32::consts::TAU / self.event_ids.len() as f32;
                StaticExposureProbeCandidate::new(
                    event_id,
                    vec![angle.cos(), angle.sin()],
                    1.0 - index as f64 / 100.0,
                )
                .expect("valid frozen candidate")
            })
            .collect();
        StaticExposureProbeInput::new(
            "static-probe-representation-v1",
            "22".repeat(32),
            candidates,
            self.event_ids[..3].iter().copied().collect(),
        )
        .expect("valid frozen probe input")
    }

    fn full_pool_input(&self, exhaust_remaining: bool) -> StaticExposureProbeInput {
        let candidates = self
            .event_ids
            .iter()
            .copied()
            .enumerate()
            .map(|(index, event_id)| {
                let mut vector = vec![0.0; self.event_ids.len()];
                if index < 43 || exhaust_remaining {
                    vector[0] = 1.0;
                } else {
                    vector[index - 42] = 1.0;
                }
                StaticExposureProbeCandidate::new(event_id, vector, 1.0 - index as f64 / 100.0)
                    .expect("valid full-pool candidate")
            })
            .collect();
        let input = StaticExposureProbeInput::new(
            "static-probe-representation-v1",
            "22".repeat(32),
            candidates,
            self.event_ids[..3].iter().copied().collect(),
        )
        .expect("valid base full-pool input");
        let source_input_identity = input
            .identity_sha256()
            .expect("identify source full-pool input");
        let protocol = full_pool_protocol(&input, source_input_identity);
        input
            .with_full_pool_exposure_gate(protocol)
            .expect("bind full-pool protocol")
    }
}

fn full_pool_protocol(
    input: &StaticExposureProbeInput,
    source_input_identity: String,
) -> FullPoolExposureGateProtocol {
    let seeded_history = input.candidates()[3..43]
        .iter()
        .map(|candidate| {
            FullPoolExposureSeed::new(candidate.event_id(), 0.0, RepetitionAnswer::No)
                .expect("valid seeded presentation")
        })
        .collect();
    FullPoolExposureGateProtocol::new(
        seeded_history,
        "40".repeat(32),
        "41".repeat(32),
        "42".repeat(32),
        source_input_identity,
    )
    .expect("valid full-pool protocol")
}

#[derive(Default)]
struct CompleteEvaluator {
    presented: Vec<String>,
    repetition_prompts: usize,
    rests: usize,
    completed: Option<usize>,
}

impl EvaluatorUi for CompleteEvaluator {
    fn rate(&mut self, view: RatingView<'_>) -> io::Result<RatingOutcome> {
        self.presented.push(view.note().to_owned());
        Ok(RatingOutcome::Submitted(EvaluatorSubmission::new(
            EvaluatorDecision::Rating(5),
            false,
        )))
    }

    fn recover(&mut self, _view: RecoveryView) -> io::Result<RecoveryOutcome> {
        panic!("the uninterrupted complete run must not recover")
    }

    fn rest(&mut self, _view: RestView) -> io::Result<RestOutcome> {
        self.rests += 1;
        Ok(RestOutcome::Continue)
    }

    fn preparing(&mut self) -> io::Result<()> {
        Ok(())
    }

    fn complete(&mut self, view: CompletionView) -> io::Result<()> {
        self.completed = Some(view.presentations_stored());
        Ok(())
    }
}

impl RepetitionUi for CompleteEvaluator {
    fn repetition(&mut self, view: RepetitionView) -> io::Result<RepetitionOutcome> {
        self.repetition_prompts += 1;
        let answer = if view.presentation_number().is_multiple_of(2) {
            RepetitionAnswer::Yes
        } else {
            RepetitionAnswer::No
        };
        Ok(RepetitionOutcome::Answered(answer))
    }
}

struct FixedCompleteEvaluator {
    rating: u8,
    repetition: RepetitionAnswer,
}

impl FixedCompleteEvaluator {
    const fn new(rating: u8, repetition: RepetitionAnswer) -> Self {
        Self { rating, repetition }
    }
}

impl EvaluatorUi for FixedCompleteEvaluator {
    fn rate(&mut self, _view: RatingView<'_>) -> io::Result<RatingOutcome> {
        Ok(RatingOutcome::Submitted(EvaluatorSubmission::new(
            EvaluatorDecision::Rating(self.rating),
            false,
        )))
    }

    fn recover(&mut self, _view: RecoveryView) -> io::Result<RecoveryOutcome> {
        panic!("uninterrupted fixed-outcome run must not recover")
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

impl RepetitionUi for FixedCompleteEvaluator {
    fn repetition(&mut self, _view: RepetitionView) -> io::Result<RepetitionOutcome> {
        Ok(RepetitionOutcome::Answered(self.repetition))
    }
}

#[derive(Default)]
struct PauseAfterFirstRating {
    presented: usize,
    repetition_prompts: usize,
}

impl EvaluatorUi for PauseAfterFirstRating {
    fn rate(&mut self, _view: RatingView<'_>) -> io::Result<RatingOutcome> {
        self.presented += 1;
        Ok(RatingOutcome::Submitted(EvaluatorSubmission::new(
            EvaluatorDecision::Rating(5),
            true,
        )))
    }

    fn recover(&mut self, _view: RecoveryView) -> io::Result<RecoveryOutcome> {
        panic!("the first invocation must not recover")
    }

    fn rest(&mut self, _view: RestView) -> io::Result<RestOutcome> {
        panic!("the first rating is not a rest boundary")
    }

    fn preparing(&mut self) -> io::Result<()> {
        Ok(())
    }

    fn complete(&mut self, _view: CompletionView) -> io::Result<()> {
        panic!("the first invocation pauses")
    }
}

impl RepetitionUi for PauseAfterFirstRating {
    fn repetition(&mut self, _view: RepetitionView) -> io::Result<RepetitionOutcome> {
        self.repetition_prompts += 1;
        panic!("pause-after-rating must occur before the diagnostic")
    }
}

#[derive(Default)]
struct ResumeAtRepetition {
    repetition_prompts: usize,
    repetition_notes: Vec<String>,
    rating_prompts: usize,
}

impl EvaluatorUi for ResumeAtRepetition {
    fn rate(&mut self, _view: RatingView<'_>) -> io::Result<RatingOutcome> {
        self.rating_prompts += 1;
        Ok(RatingOutcome::Paused)
    }

    fn recover(&mut self, _view: RecoveryView) -> io::Result<RecoveryOutcome> {
        panic!("the stored rating removes display uncertainty")
    }

    fn rest(&mut self, _view: RestView) -> io::Result<RestOutcome> {
        panic!("the resumed first presentation is not a rest boundary")
    }

    fn preparing(&mut self) -> io::Result<()> {
        Ok(())
    }

    fn complete(&mut self, _view: CompletionView) -> io::Result<()> {
        panic!("the resumed invocation pauses on the next note")
    }
}

impl RepetitionUi for ResumeAtRepetition {
    fn repetition(&mut self, view: RepetitionView<'_>) -> io::Result<RepetitionOutcome> {
        self.repetition_prompts += 1;
        self.repetition_notes.push(view.note().to_owned());
        Ok(RepetitionOutcome::Answered(RepetitionAnswer::No))
    }
}

#[derive(Default)]
struct AllWrongLanguage {
    presented: usize,
}

impl EvaluatorUi for AllWrongLanguage {
    fn rate(&mut self, _view: RatingView<'_>) -> io::Result<RatingOutcome> {
        self.presented += 1;
        Ok(RatingOutcome::Submitted(EvaluatorSubmission::new(
            EvaluatorDecision::WrongLanguage,
            false,
        )))
    }

    fn recover(&mut self, _view: RecoveryView) -> io::Result<RecoveryOutcome> {
        panic!("the uninterrupted language run must not recover")
    }

    fn rest(&mut self, _view: RestView) -> io::Result<RestOutcome> {
        panic!("wrong-language presentations do not reach a valid-rating rest")
    }

    fn preparing(&mut self) -> io::Result<()> {
        Ok(())
    }

    fn complete(&mut self, _view: CompletionView) -> io::Result<()> {
        panic!("the language ceiling is not a completed probe")
    }
}

impl RepetitionUi for AllWrongLanguage {
    fn repetition(&mut self, _view: RepetitionView<'_>) -> io::Result<RepetitionOutcome> {
        panic!("wrong-language presentations do not receive repetition questions")
    }
}

struct NeverCalled;

impl EvaluatorUi for NeverCalled {
    fn rate(&mut self, _view: RatingView<'_>) -> io::Result<RatingOutcome> {
        panic!("invalid state must fail before rating")
    }

    fn recover(&mut self, _view: RecoveryView) -> io::Result<RecoveryOutcome> {
        panic!("invalid state must fail before recovery")
    }

    fn rest(&mut self, _view: RestView) -> io::Result<RestOutcome> {
        panic!("invalid state must fail before rest")
    }

    fn preparing(&mut self) -> io::Result<()> {
        panic!("invalid state must fail before preparation")
    }

    fn complete(&mut self, _view: CompletionView) -> io::Result<()> {
        panic!("invalid state must fail before completion")
    }
}

impl RepetitionUi for NeverCalled {
    fn repetition(&mut self, _view: RepetitionView<'_>) -> io::Result<RepetitionOutcome> {
        panic!("invalid state must fail before repetition")
    }
}

#[derive(Default)]
struct CompletionOnlyEvaluator {
    completed: Option<usize>,
}

impl EvaluatorUi for CompletionOnlyEvaluator {
    fn rate(&mut self, _view: RatingView<'_>) -> io::Result<RatingOutcome> {
        panic!("an exhausted selector must not request a rating")
    }

    fn recover(&mut self, _view: RecoveryView) -> io::Result<RecoveryOutcome> {
        panic!("an exhausted selector must not recover a presentation")
    }

    fn rest(&mut self, _view: RestView) -> io::Result<RestOutcome> {
        panic!("an exhausted selector must not request a rest")
    }

    fn preparing(&mut self) -> io::Result<()> {
        Ok(())
    }

    fn complete(&mut self, view: CompletionView) -> io::Result<()> {
        self.completed = Some(view.presentations_stored());
        Ok(())
    }
}

impl RepetitionUi for CompletionOnlyEvaluator {
    fn repetition(&mut self, _view: RepetitionView) -> io::Result<RepetitionOutcome> {
        panic!("an exhausted selector must not request repetition feedback")
    }
}

#[derive(Default)]
struct WrongLanguageUntilComplete {
    presented: usize,
    completed: Option<usize>,
}

impl EvaluatorUi for WrongLanguageUntilComplete {
    fn rate(&mut self, _view: RatingView<'_>) -> io::Result<RatingOutcome> {
        self.presented += 1;
        Ok(RatingOutcome::Submitted(EvaluatorSubmission::new(
            EvaluatorDecision::WrongLanguage,
            false,
        )))
    }

    fn recover(&mut self, _view: RecoveryView) -> io::Result<RecoveryOutcome> {
        panic!("uninterrupted language-reserve run must not recover")
    }

    fn rest(&mut self, _view: RestView) -> io::Result<RestOutcome> {
        panic!("wrong-language presentations do not reach a rest")
    }

    fn preparing(&mut self) -> io::Result<()> {
        Ok(())
    }

    fn complete(&mut self, view: CompletionView) -> io::Result<()> {
        self.completed = Some(view.presentations_stored());
        Ok(())
    }
}

impl RepetitionUi for WrongLanguageUntilComplete {
    fn repetition(&mut self, _view: RepetitionView) -> io::Result<RepetitionOutcome> {
        panic!("wrong-language presentations do not receive repetition feedback")
    }
}

struct PauseBeforeRating;

impl EvaluatorUi for PauseBeforeRating {
    fn rate(&mut self, _view: RatingView<'_>) -> io::Result<RatingOutcome> {
        Ok(RatingOutcome::Paused)
    }

    fn recover(&mut self, _view: RecoveryView) -> io::Result<RecoveryOutcome> {
        panic!("the first run creates the uncertain presentation")
    }

    fn rest(&mut self, _view: RestView) -> io::Result<RestOutcome> {
        panic!("the first run has no rating")
    }

    fn preparing(&mut self) -> io::Result<()> {
        Ok(())
    }

    fn complete(&mut self, _view: CompletionView) -> io::Result<()> {
        panic!("the first run pauses")
    }
}

impl RepetitionUi for PauseBeforeRating {
    fn repetition(&mut self, _view: RepetitionView) -> io::Result<RepetitionOutcome> {
        panic!("an unrated note has no repetition prompt")
    }
}

#[derive(Default)]
struct RecoverRatingThenPauseNext {
    recoveries: usize,
    repetitions: usize,
    next_rating_prompts: usize,
}

impl EvaluatorUi for RecoverRatingThenPauseNext {
    fn rate(&mut self, _view: RatingView<'_>) -> io::Result<RatingOutcome> {
        self.next_rating_prompts += 1;
        Ok(RatingOutcome::Paused)
    }

    fn recover(&mut self, _view: RecoveryView) -> io::Result<RecoveryOutcome> {
        self.recoveries += 1;
        Ok(RecoveryOutcome::Submitted(EvaluatorSubmission::new(
            EvaluatorDecision::Rating(5),
            false,
        )))
    }

    fn rest(&mut self, _view: RestView) -> io::Result<RestOutcome> {
        panic!("one recovered rating is not a rest boundary")
    }

    fn preparing(&mut self) -> io::Result<()> {
        Ok(())
    }

    fn complete(&mut self, _view: CompletionView) -> io::Result<()> {
        panic!("the resumed run pauses on the next note")
    }
}

impl RepetitionUi for RecoverRatingThenPauseNext {
    fn repetition(&mut self, _view: RepetitionView) -> io::Result<RepetitionOutcome> {
        self.repetitions += 1;
        Ok(RepetitionOutcome::Answered(RepetitionAnswer::No))
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
        .sign(&[7_u8; 32])
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

fn decode_hex(value: u8) -> u8 {
    match value {
        b'0'..=b'9' => value - b'0',
        b'a'..=b'f' => value - b'a' + 10,
        _ => panic!("invalid hex"),
    }
}

fn write_json(path: &std::path::Path, value: &serde_json::Value) {
    let mut bytes = serde_json::to_vec_pretty(value).expect("encode changed session");
    bytes.push(b'\n');
    std::fs::write(path, bytes).expect("write changed session");
}

fn forge_one_rejection_language_reserve_completion(config: &StaticExposureProbeRunnerConfig) {
    let mut report = std::fs::read_to_string(&config.report_path).expect("read sealed report");
    remove_second_array_object(&mut report, "\"presentation_audit\": [");
    replace_once(
        &mut report,
        "\"presentations\": 2,",
        "\"presentations\": 1,",
    );
    replace_once(
        &mut report,
        "\"wrong_language_presentations\": 2,",
        "\"wrong_language_presentations\": 1,",
    );
    std::fs::write(&config.report_path, report.as_bytes()).expect("write forged report");
    let report_sha256 = hex_sha256(report.as_bytes());

    let mut session = std::fs::read_to_string(&config.session_path).expect("read sealed session");
    remove_second_array_object(&mut session, "\"presentations\": [");
    replace_once(
        &mut session,
        "\"presentations\": 2,",
        "\"presentations\": 1,",
    );
    let old_report_sha256 = serde_json::from_str::<serde_json::Value>(&session)
        .expect("decode sealed session")["completion"]["report_sha256"]
        .as_str()
        .expect("sealed report identity")
        .to_owned();
    replace_once(&mut session, &old_report_sha256, &report_sha256);

    let old_checksum = serde_json::from_str::<serde_json::Value>(&session)
        .expect("decode forged session")["transcript_checksum_sha256"]
        .as_str()
        .expect("sealed transcript identity")
        .to_owned();
    let checksum_field = format!(",\n  \"transcript_checksum_sha256\": \"{old_checksum}\"");
    let transcript = session
        .strip_suffix("\n}\n")
        .expect("pretty session ends with a root object and newline")
        .strip_suffix(&checksum_field)
        .expect("transcript checksum is the final session field");
    let compact_transcript = minify_json_preserving_order(&format!("{transcript}}}"));
    let new_checksum = hex_sha256(compact_transcript.as_bytes());
    replace_once(&mut session, &old_checksum, &new_checksum);
    std::fs::write(&config.session_path, session.as_bytes()).expect("write forged session");
}

fn remove_second_array_object(document: &mut String, marker: &str) {
    let marker_start = document.find(marker).expect("array marker exists");
    let array_start = marker_start + marker.len() - 1;
    let bytes = document.as_bytes();
    let mut in_string = false;
    let mut escaped = false;
    let mut object_depth = 0_usize;
    let mut object_starts = Vec::new();
    let mut object_ends = Vec::new();
    for index in array_start + 1..bytes.len() {
        let byte = bytes[index];
        if in_string {
            if escaped {
                escaped = false;
            } else if byte == b'\\' {
                escaped = true;
            } else if byte == b'"' {
                in_string = false;
            }
            continue;
        }
        match byte {
            b'"' => in_string = true,
            b'{' => {
                if object_depth == 0 {
                    object_starts.push(index);
                }
                object_depth += 1;
            }
            b'}' => {
                object_depth = object_depth.checked_sub(1).expect("balanced object");
                if object_depth == 0 {
                    object_ends.push(index + 1);
                    if object_ends.len() == 2 {
                        break;
                    }
                }
            }
            b']' if object_depth == 0 => break,
            _ => {}
        }
    }
    let second_start = *object_starts.get(1).expect("array has a second object");
    let second_end = *object_ends.get(1).expect("second object is complete");
    let mut removal_start = second_start;
    while document.as_bytes()[removal_start - 1].is_ascii_whitespace() {
        removal_start -= 1;
    }
    assert_eq!(document.as_bytes()[removal_start - 1], b',');
    document.replace_range(removal_start - 1..second_end, "");
}

fn replace_once(document: &mut String, old: &str, new: &str) {
    assert_eq!(
        document.match_indices(old).count(),
        1,
        "expected one exact replacement for {old:?}"
    );
    *document = document.replacen(old, new, 1);
}

fn minify_json_preserving_order(document: &str) -> String {
    let mut output = String::with_capacity(document.len());
    let mut in_string = false;
    let mut escaped = false;
    for character in document.chars() {
        if in_string {
            output.push(character);
            if escaped {
                escaped = false;
            } else if character == '\\' {
                escaped = true;
            } else if character == '"' {
                in_string = false;
            }
        } else if character == '"' {
            in_string = true;
            output.push(character);
        } else if !character.is_whitespace() {
            output.push(character);
        }
    }
    output
}

fn hex_sha256(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}
