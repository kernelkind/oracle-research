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
    StaticExposureProbeCandidate, StaticExposureProbeInput, StaticExposureProbeRunnerConfig,
    StaticExposureProbeRunnerOutcome, StaticExposureProbeSourceProvenance,
    StaticExposureProbeVerification, run_static_exposure_probe, verify_static_exposure_probe,
};

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
