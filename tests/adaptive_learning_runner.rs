use std::collections::BTreeMap;
use std::io::{BufRead, Cursor, Read, Write};
use std::thread;
use std::time::{Duration, Instant};

use nostrdb::{Config, Filter, Ndb, NoteBuilder, Transaction};
use oracle_mvp::adaptive_learning_runner::{
    AdaptiveLearningRunnerConfig, AdaptiveLearningRunnerOutcome, AdaptiveLearningSeed,
    run_adaptive_learning,
};
use oracle_mvp::candidate_order::{B16Boundary, CandidateOrderOracle};
use oracle_mvp::fp32_oracle::{
    Fp32Candidate, SimilarNotesRequest, SimilarNotesResponse, SimilarNotesWaveMetrics,
    SimilarNotesWaveResponse, StoredNoteVector, VectorsForNotesResponse,
};
use oracle_mvp::personalizer_learning::{CompactLearningSettings, RbfLearningSettings, ScaleLevel};
use oracle_mvp::representation::EventId;
use oracle_mvp::snapshot::{Error as SnapshotError, Result as SnapshotResult};

const VERSION: &str = "runner-representation-v1";

const APPROVED_RATING_PROMPT: &str =
    "Considering the attention it required, how glad are you that you saw this note?";
const APPROVED_INPUT_PROMPT: &str = "Considering the attention it required, how glad are you that you saw this note? [1–7, `l` = wrong_language; append `q` to save and stop]: ";
const APPROVED_RATING_ANCHORS: [&str; 7] = [
    "1: Actively wish it had not been shown.",
    "2: Clearly not worth seeing.",
    "3: Little personal value.",
    "4: Indifferent.",
    "5: Mildly glad to have seen it.",
    "6: Clearly glad; personally valuable.",
    "7: Exceptionally valuable.",
];
const APPROVED_LANGUAGE_RULE: &str = "Use wrong_language only when the note is clearly primarily non-English. Mixed-language, code-heavy, and ambiguous notes remain eligible and must be rated.";

#[derive(Default)]
struct FailOnRawNoteOutput {
    bytes: Vec<u8>,
    fail_next_write: bool,
}

impl Write for FailOnRawNoteOutput {
    fn write(&mut self, bytes: &[u8]) -> std::io::Result<usize> {
        if self.fail_next_write {
            return Err(std::io::Error::new(
                std::io::ErrorKind::BrokenPipe,
                "injected terminal failure after a partial note",
            ));
        }
        if bytes
            .windows(b"raw runner fixture note".len())
            .any(|window| window == b"raw runner fixture note")
        {
            let partial = bytes.len().div_ceil(2);
            self.bytes.extend_from_slice(&bytes[..partial]);
            self.fail_next_write = true;
            return Ok(partial);
        }
        self.bytes.extend_from_slice(bytes);
        Ok(bytes.len())
    }

    fn flush(&mut self) -> std::io::Result<()> {
        Ok(())
    }
}

#[derive(Default)]
struct FailBeforeRawNoteOutput {
    bytes: Vec<u8>,
}

impl Write for FailBeforeRawNoteOutput {
    fn write(&mut self, bytes: &[u8]) -> std::io::Result<usize> {
        if bytes == b"\n" {
            return Err(std::io::Error::new(
                std::io::ErrorKind::BrokenPipe,
                "injected terminal failure before the raw note",
            ));
        }
        self.bytes.extend_from_slice(bytes);
        Ok(bytes.len())
    }

    fn flush(&mut self) -> std::io::Result<()> {
        Ok(())
    }
}

#[derive(Default)]
struct FailAfterRawNoteOutput {
    bytes: Vec<u8>,
}

impl Write for FailAfterRawNoteOutput {
    fn write(&mut self, bytes: &[u8]) -> std::io::Result<usize> {
        self.bytes.extend_from_slice(bytes);
        Ok(bytes.len())
    }

    fn flush(&mut self) -> std::io::Result<()> {
        Err(std::io::Error::new(
            std::io::ErrorKind::BrokenPipe,
            "injected terminal flush failure after the raw note",
        ))
    }
}

struct FailOnTerminalInput;

impl Read for FailOnTerminalInput {
    fn read(&mut self, _bytes: &mut [u8]) -> std::io::Result<usize> {
        Err(std::io::Error::new(
            std::io::ErrorKind::BrokenPipe,
            "injected terminal input failure",
        ))
    }
}

impl BufRead for FailOnTerminalInput {
    fn fill_buf(&mut self) -> std::io::Result<&[u8]> {
        Err(std::io::Error::new(
            std::io::ErrorKind::BrokenPipe,
            "injected terminal input failure",
        ))
    }

    fn consume(&mut self, _amount: usize) {}
}

#[test]
fn terminal_and_session_binding_use_the_exact_frozen_evaluator_protocol() {
    let fixture = RunnerFixture::new();
    let session_path = fixture.temp.path().join("evaluator-protocol-session.json");
    let config = fixture.config(session_path.clone());
    let mut oracle = FixtureOracle::new(fixture.event_ids.clone());
    let mut output = Vec::new();

    let outcome = run_adaptive_learning(&config, &mut oracle, Cursor::new(b""), &mut output)
        .expect("pause at the first evaluator prompt");
    assert!(matches!(outcome, AdaptiveLearningRunnerOutcome::Paused));
    let transcript = String::from_utf8(output).expect("UTF-8 transcript");
    assert!(transcript.contains(APPROVED_RATING_PROMPT));
    for anchor in APPROVED_RATING_ANCHORS {
        assert!(transcript.contains(anchor), "missing anchor `{anchor}`");
    }
    assert!(transcript.contains(APPROVED_LANGUAGE_RULE));
    assert!(!transcript.contains("extremely sorry you saw it"));

    let session = read_session(&session_path);
    assert_eq!(
        session["binding"]["fixed"]["rating_prompt"],
        APPROVED_INPUT_PROMPT
    );
    assert_eq!(
        session["binding"]["fixed"]["rating_instructions"],
        format!(
            "{}\n{}\n",
            APPROVED_RATING_ANCHORS.join("\n"),
            APPROVED_LANGUAGE_RULE
        )
    );
}

#[test]
fn resume_rejects_a_changed_evaluator_protocol_before_oracle_work() {
    let fixture = RunnerFixture::new();
    let session_path = fixture.temp.path().join("changed-protocol-session.json");
    let config = fixture.config(session_path.clone());
    let mut first_oracle = FixtureOracle::new(fixture.event_ids.clone());
    run_adaptive_learning(
        &config,
        &mut first_oracle,
        Cursor::new(b""),
        &mut Vec::new(),
    )
    .expect("create bound evaluator session");

    let mut changed = read_session(&session_path);
    changed["binding"]["fixed"]["rating_prompt"] =
        serde_json::json!("a different evaluator question");
    std::fs::write(
        &session_path,
        serde_json::to_vec_pretty(&changed).expect("encode changed session"),
    )
    .expect("write changed session");

    let mut resumed_oracle = FixtureOracle::new(fixture.event_ids.clone());
    let error = run_adaptive_learning(
        &config,
        &mut resumed_oracle,
        Cursor::new(b""),
        &mut Vec::new(),
    )
    .err()
    .expect("reject changed evaluator protocol");
    assert!(error.to_string().contains("immutable configuration"));
    assert_eq!(resumed_oracle.vector_lookups, 0);
    assert_eq!(resumed_oracle.matrix_passes, 0);
}

#[cfg(unix)]
#[test]
fn phase3_session_and_oracle_artifacts_remain_owner_only() {
    use std::os::unix::fs::PermissionsExt as _;

    fn mode(path: &std::path::Path) -> u32 {
        std::fs::symlink_metadata(path)
            .expect("private artifact metadata")
            .permissions()
            .mode()
            & 0o777
    }

    let fixture = RunnerFixture::new();
    let session_path = fixture.temp.path().join("private-session.json");
    let config = fixture.config(session_path.clone());
    let lock_path = fixture.temp.path().join(".private-session.json.lock");
    let cache_dir = fixture
        .temp
        .path()
        .join(".private-session.json.oracle-responses");
    let session_temporary = fixture.temp.path().join(".private-session.json.tmp");
    let mut oracle = FixtureOracle::new(fixture.event_ids.clone());
    run_adaptive_learning(&config, &mut oracle, Cursor::new(b"7q\n"), &mut Vec::new())
        .expect("create private Phase 3 artifacts");

    assert_eq!(mode(&session_path), 0o600);
    assert_eq!(mode(&lock_path), 0o600);
    assert_eq!(mode(&cache_dir), 0o700);
    let cache_files = std::fs::read_dir(&cache_dir)
        .expect("read private cache")
        .map(|entry| entry.expect("cache entry").path())
        .collect::<Vec<_>>();
    assert!(!cache_files.is_empty());
    for path in &cache_files {
        assert_eq!(mode(path), 0o600, "cache artifact {}", path.display());
        std::fs::set_permissions(path, std::fs::Permissions::from_mode(0o644))
            .expect("make cache artifact permissive");
    }
    std::fs::set_permissions(&session_path, std::fs::Permissions::from_mode(0o644))
        .expect("make session permissive");
    std::fs::set_permissions(&lock_path, std::fs::Permissions::from_mode(0o644))
        .expect("make lock permissive");
    std::fs::set_permissions(&cache_dir, std::fs::Permissions::from_mode(0o755))
        .expect("make cache directory permissive");
    std::fs::write(&session_temporary, b"stale private temporary")
        .expect("create stale session temporary");
    std::fs::set_permissions(&session_temporary, std::fs::Permissions::from_mode(0o644))
        .expect("make temporary permissive");
    let orphaned_cache_temporary = cache_dir.join(".orphaned-response.tmp");
    std::fs::write(&orphaned_cache_temporary, b"stale cache temporary")
        .expect("create stale cache temporary");
    std::fs::set_permissions(
        &orphaned_cache_temporary,
        std::fs::Permissions::from_mode(0o644),
    )
    .expect("make cache temporary permissive");

    let mut resumed_oracle = FixtureOracle::new(fixture.event_ids.clone());
    let resumed = run_adaptive_learning(
        &config,
        &mut resumed_oracle,
        Cursor::new(b""),
        &mut Vec::new(),
    )
    .expect("repair and resume private Phase 3 artifacts");
    assert!(matches!(resumed, AdaptiveLearningRunnerOutcome::Paused));
    assert_eq!(mode(&session_path), 0o600);
    assert_eq!(mode(&lock_path), 0o600);
    assert_eq!(mode(&cache_dir), 0o700);
    assert_eq!(mode(&orphaned_cache_temporary), 0o600);
    assert!(!session_temporary.exists());
    for path in cache_files {
        assert_eq!(mode(&path), 0o600, "cache artifact {}", path.display());
    }
}

#[cfg(unix)]
#[test]
fn phase3_rejects_a_private_artifact_symlink_without_touching_its_target() {
    use std::os::unix::fs::symlink;

    let fixture = RunnerFixture::new();
    let session_path = fixture.temp.path().join("symlinked-session.json");
    let target_path = fixture.temp.path().join("unrelated-target.txt");
    let original = b"must remain unchanged";
    std::fs::write(&target_path, original).expect("write unrelated target");
    symlink(&target_path, &session_path).expect("create session symlink");
    let config = fixture.config(session_path);
    let mut oracle = FixtureOracle::new(fixture.event_ids.clone());

    let error = run_adaptive_learning(&config, &mut oracle, Cursor::new(b""), &mut Vec::new())
        .err()
        .expect("reject private artifact symlink");
    assert!(error.to_string().contains("not a regular file"));
    assert_eq!(std::fs::read(&target_path).expect("read target"), original);
    assert_eq!(oracle.vector_lookups, 0);
    assert_eq!(oracle.matrix_passes, 0);
}

#[test]
fn accepted_rating_is_staged_and_resume_continues_at_the_next_event() {
    let fixture = RunnerFixture::new();
    let session_path = fixture.temp.path().join("learning-session.json");
    let config = fixture.config(session_path.clone());
    let mut first_oracle = FixtureOracle::new(fixture.event_ids.clone());
    let mut first_output = Vec::new();

    let first = run_adaptive_learning(
        &config,
        &mut first_oracle,
        Cursor::new(b"7q\n"),
        &mut first_output,
    )
    .expect("run first portion");
    assert!(matches!(first, AdaptiveLearningRunnerOutcome::Paused));
    assert_eq!(first_oracle.matrix_passes, 1);
    assert_eq!(
        std::str::from_utf8(&first_output)
            .expect("UTF-8 transcript")
            .matches("raw runner fixture note")
            .count(),
        1,
        "normal quit must occur after the accepted rating and before another display"
    );

    let first_session = read_session(&session_path);
    let accepted_id =
        value_event_id(&first_session["rounds"][0]["waves"][0]["decisions"][0]["event_id"]);
    let accepted_content = fixture.content_for(accepted_id);

    let mut resumed_oracle = FixtureOracle::new(fixture.event_ids.clone());
    let mut resumed_output = Vec::new();
    let resumed = run_adaptive_learning(
        &config,
        &mut resumed_oracle,
        Cursor::new(b""),
        &mut resumed_output,
    )
    .expect("resume first round");
    assert!(matches!(resumed, AdaptiveLearningRunnerOutcome::Paused));
    assert_eq!(
        resumed_oracle.matrix_passes, 0,
        "resume must use durable Oracle responses instead of rescanning"
    );
    let resumed_transcript = String::from_utf8(resumed_output).expect("UTF-8 transcript");
    assert!(
        !resumed_transcript.contains(&accepted_content),
        "a durably rated note must not be displayed again"
    );

    let session = read_session(&session_path);
    assert_eq!(
        session["rounds"][0]["waves"][0]["decisions"]
            .as_array()
            .unwrap()
            .len(),
        1
    );
    assert_eq!(session["rounds"][0]["ratings_submitted"], false);
}

#[test]
fn a_displayed_unrated_note_is_not_redisplayed_after_resume() {
    let fixture = RunnerFixture::new();
    let session_path = fixture.temp.path().join("displayed-session.json");
    let config = fixture.config(session_path.clone());
    let mut first_oracle = FixtureOracle::new(fixture.event_ids.clone());
    let mut first_output = Vec::new();
    let first = run_adaptive_learning(
        &config,
        &mut first_oracle,
        Cursor::new(b""),
        &mut first_output,
    )
    .expect("pause after displaying the first note");
    assert!(matches!(first, AdaptiveLearningRunnerOutcome::Paused));
    let first_session = read_session(&session_path);
    assert!(!first_session["pending_presentation"].is_null());
    let pending_id = value_event_id(&first_session["pending_presentation"]["event_id"]);
    let content = fixture.content_for(pending_id);
    assert!(String::from_utf8(first_output).unwrap().contains(&content));

    let mut resumed_oracle = FixtureOracle::new(fixture.event_ids.clone());
    let mut resumed_output = Vec::new();
    let resumed = run_adaptive_learning(
        &config,
        &mut resumed_oracle,
        Cursor::new(b"7q\n"),
        &mut resumed_output,
    )
    .expect("rate the already displayed note");
    assert!(matches!(resumed, AdaptiveLearningRunnerOutcome::Paused));
    let resumed_transcript = String::from_utf8(resumed_output).expect("UTF-8 transcript");
    assert!(!resumed_transcript.contains(&content));
    assert!(
        resumed_transcript.contains("`lq`"),
        "recovery instructions must say how to save a wrong-language decision and stop"
    );
    let resumed_session = read_session(&session_path);
    assert!(resumed_session["pending_presentation"].is_null());
    assert_eq!(
        value_event_id(&resumed_session["rounds"][0]["waves"][0]["decisions"][0]["event_id"]),
        pending_id
    );
}

#[test]
fn uncertain_partial_display_and_transient_corpus_failure_resume_same_event() {
    let fixture = RunnerFixture::new();
    let session_path = fixture.temp.path().join("uncertain-session.json");
    let config = fixture.config(session_path.clone());
    let mut first_oracle = FixtureOracle::new(fixture.event_ids.clone());
    let mut failing_output = FailOnRawNoteOutput::default();
    let first = run_adaptive_learning(
        &config,
        &mut first_oracle,
        Cursor::new(b""),
        &mut failing_output,
    )
    .expect("terminal failure pauses an uncertain presentation");
    assert!(matches!(first, AdaptiveLearningRunnerOutcome::Paused));
    let first_session = read_session(&session_path);
    assert!(!first_session["pending_presentation"].is_null());
    assert_eq!(first_session["phase"], "learning");
    assert!(first_session["failure"].is_null());
    let pending_id = value_event_id(&first_session["pending_presentation"]["event_id"]);
    let content = fixture.content_for(pending_id);

    let unavailable = fixture.temp.path().join("temporarily-unavailable.ndb");
    std::fs::rename(&fixture.corpus_path, &unavailable).expect("hide display corpus");
    let mut missing_oracle = FixtureOracle::new(fixture.event_ids.clone());
    let mut missing_output = Vec::new();
    let missing = run_adaptive_learning(
        &config,
        &mut missing_oracle,
        Cursor::new(b"r\n"),
        &mut missing_output,
    )
    .expect("missing corpus pauses instead of failing the session");
    assert!(matches!(missing, AdaptiveLearningRunnerOutcome::Paused));
    let missing_session = read_session(&session_path);
    assert_eq!(
        missing_session["pending_presentation"]["event_id"],
        first_session["pending_presentation"]["event_id"]
    );
    assert_eq!(missing_session["phase"], "learning");
    assert!(missing_session["failure"].is_null());
    assert!(
        !fixture.corpus_path.exists(),
        "a transiently missing corpus must not be replaced with an empty database"
    );

    std::fs::rename(&unavailable, &fixture.corpus_path).expect("restore display corpus");
    let mut resumed_oracle = FixtureOracle::new(fixture.event_ids.clone());
    let mut resumed_output = Vec::new();
    let resumed = run_adaptive_learning(
        &config,
        &mut resumed_oracle,
        Cursor::new(b"r\n7q\n"),
        &mut resumed_output,
    )
    .expect("explicitly authorize redisplay and rate the same event");
    assert!(matches!(resumed, AdaptiveLearningRunnerOutcome::Paused));
    let transcript = String::from_utf8(resumed_output).expect("UTF-8 transcript");
    assert!(transcript.contains("may have been shown"));
    assert_eq!(transcript.matches(&content).count(), 1);
    let resumed_session = read_session(&session_path);
    assert!(resumed_session["pending_presentation"].is_null());
    assert_eq!(
        value_event_id(&resumed_session["rounds"][0]["waves"][0]["decisions"][0]["event_id"]),
        pending_id
    );
}

#[test]
fn output_failure_before_note_bytes_leaves_a_recoverable_pending_event() {
    let fixture = RunnerFixture::new();
    let session_path = fixture.temp.path().join("before-output-session.json");
    let config = fixture.config(session_path.clone());
    let mut oracle = FixtureOracle::new(fixture.event_ids.clone());
    let mut output = FailBeforeRawNoteOutput::default();
    let outcome = run_adaptive_learning(&config, &mut oracle, Cursor::new(b""), &mut output)
        .expect("terminal failure before note bytes pauses the presentation");
    assert!(matches!(outcome, AdaptiveLearningRunnerOutcome::Paused));

    let session = read_session(&session_path);
    let pending_id = value_event_id(&session["pending_presentation"]["event_id"]);
    assert_eq!(session["phase"], "learning");
    assert!(session["failure"].is_null());
    assert!(
        !String::from_utf8(output.bytes)
            .unwrap()
            .contains(&fixture.content_for(pending_id))
    );
}

#[test]
fn flush_failure_after_note_bytes_leaves_a_recoverable_pending_event() {
    let fixture = RunnerFixture::new();
    let session_path = fixture.temp.path().join("flush-output-session.json");
    let config = fixture.config(session_path.clone());
    let mut oracle = FixtureOracle::new(fixture.event_ids.clone());
    let mut output = FailAfterRawNoteOutput::default();
    let outcome = run_adaptive_learning(&config, &mut oracle, Cursor::new(b""), &mut output)
        .expect("terminal flush failure pauses the presentation");
    assert!(matches!(outcome, AdaptiveLearningRunnerOutcome::Paused));

    let session = read_session(&session_path);
    let pending_id = value_event_id(&session["pending_presentation"]["event_id"]);
    assert_eq!(session["phase"], "learning");
    assert!(session["failure"].is_null());
    assert!(
        String::from_utf8(output.bytes)
            .unwrap()
            .contains(&fixture.content_for(pending_id))
    );
}

#[test]
fn terminal_input_failure_after_display_leaves_a_recoverable_pending_event() {
    let fixture = RunnerFixture::new();
    let session_path = fixture.temp.path().join("input-failure-session.json");
    let config = fixture.config(session_path.clone());
    let mut oracle = FixtureOracle::new(fixture.event_ids.clone());
    let mut output = Vec::new();
    let outcome = run_adaptive_learning(&config, &mut oracle, FailOnTerminalInput, &mut output)
        .expect("terminal input failure pauses the presentation");
    assert!(matches!(outcome, AdaptiveLearningRunnerOutcome::Paused));

    let session = read_session(&session_path);
    let pending_id = value_event_id(&session["pending_presentation"]["event_id"]);
    assert_eq!(session["phase"], "learning");
    assert!(session["failure"].is_null());
    assert!(
        String::from_utf8(output)
            .unwrap()
            .contains(&fixture.content_for(pending_id))
    );
}

#[test]
fn a_corrupt_pending_presentation_is_rejected_before_output_or_oracle_work() {
    let fixture = RunnerFixture::new();
    let session_path = fixture
        .temp
        .path()
        .join("corrupt-presentation-session.json");
    let config = fixture.config(session_path.clone());
    let mut first_oracle = FixtureOracle::new(fixture.event_ids.clone());
    run_adaptive_learning(
        &config,
        &mut first_oracle,
        Cursor::new(b""),
        &mut Vec::new(),
    )
    .expect("create pending presentation");
    let mut corrupt = read_session(&session_path);
    corrupt["pending_presentation"]["event_id"] =
        serde_json::to_value(fixture.event_ids[0]).expect("encode wrong event ID");
    std::fs::write(
        &session_path,
        serde_json::to_vec_pretty(&corrupt).expect("encode corrupt session"),
    )
    .expect("write corrupt session");

    let mut resumed_oracle = FixtureOracle::new(fixture.event_ids.clone());
    let mut output = Vec::new();
    let error = run_adaptive_learning(
        &config,
        &mut resumed_oracle,
        Cursor::new(b"7q\n"),
        &mut output,
    )
    .err()
    .expect("reject corrupt pending presentation");
    assert!(error.to_string().contains("final frozen wave"));
    assert!(output.is_empty());
    assert_eq!(resumed_oracle.vector_lookups, 0);
    assert_eq!(resumed_oracle.matrix_passes, 0);
}

#[test]
fn h256_fallback_is_durably_replayed_without_new_oracle_work() {
    let fixture = DivergentFixture::new();
    let session_path = fixture.temp.path().join("fallback-session.json");
    let mut config = fixture.config(session_path.clone());
    config.compact_settings =
        CompactLearningSettings::new(VERSION, 0.005, 0.01, 2.0, ScaleLevel::Mass64)
            .expect("fallback Compact settings");

    let mut first_oracle = DivergentOracle::new(&fixture);
    let first = run_adaptive_learning(
        &config,
        &mut first_oracle,
        Cursor::new(b"7q\n"),
        &mut Vec::new(),
    )
    .expect("start fallback round");
    assert!(matches!(first, AdaptiveLearningRunnerOutcome::Paused));
    assert_eq!(first_oracle.matrix_passes, 1);
    assert_eq!(first_oracle.logical_wave_calls, 1);

    let session = read_session(&session_path);
    assert_eq!(session["oracle_calls"].as_array().unwrap().len(), 4);

    let mut resumed_oracle = DivergentOracle::new(&fixture);
    let resumed = run_adaptive_learning(
        &config,
        &mut resumed_oracle,
        Cursor::new(b""),
        &mut Vec::new(),
    )
    .expect("replay fallback round");
    assert!(matches!(resumed, AdaptiveLearningRunnerOutcome::Paused));
    assert_eq!(resumed_oracle.matrix_passes, 0);
    assert_eq!(resumed_oracle.logical_wave_calls, 0);
}

#[test]
fn candidate_order_failure_persists_complete_attempts_and_replays_from_cache() {
    let fixture = RunnerFixture::with_note_count(45);
    let session_path = fixture.temp.path().join("candidate-failure-session.json");
    let config = fixture.config(session_path.clone());
    let mut first_oracle = FixtureOracle::new(fixture.event_ids.clone());
    let error = run_adaptive_learning(
        &config,
        &mut first_oracle,
        Cursor::new(b""),
        &mut Vec::new(),
    )
    .err()
    .expect("forty non-seed notes cannot satisfy the 41-note order");
    assert!(
        error.to_string().contains("CompactGeometryMismatch"),
        "unexpected failure: {error}"
    );

    let failed = read_session(&session_path);
    assert_eq!(failed["phase"], "failed");
    assert_eq!(failed["failure"]["transition"]["kind"], "start_round");
    assert_eq!(failed["failure"]["transition"]["round"], 1);
    let attempts = failed["failure"]["candidate_order_attempts"]
        .as_array()
        .expect("failed candidate-order attempts must be structured");
    assert_eq!(attempts.len(), 2);
    assert_eq!(
        attempts[0]["record"]["accepted"].as_array().unwrap().len(),
        40
    );
    assert_eq!(
        attempts[1]["record"]["accepted"].as_array().unwrap().len(),
        40
    );
    assert_eq!(
        attempts[0]["record"]["active_parameters"]["kind"],
        "compact"
    );
    assert_eq!(
        attempts[0]["record"]["active_parameters"]["parameter_tuple"]["scale_level"],
        "mass64"
    );
    assert_eq!(
        attempts[1]["record"]["active_parameters"]["parameter_tuple"]["scale_level"],
        "mass256"
    );
    for attempt in attempts {
        assert_eq!(attempt["sha256"].as_str().unwrap().len(), 64);
        assert!(
            !attempt["record"]["source_responses"]
                .as_array()
                .unwrap()
                .is_empty()
        );
        assert!(
            !attempt["record"]["candidates"]
                .as_array()
                .unwrap()
                .is_empty()
        );
        assert!(attempt["record"]["accepted"][0]["vector"].is_array());
    }

    let mut replay_oracle = FixtureOracle::new(fixture.event_ids.clone());
    let mut replay_output = Vec::new();
    let replay_error = run_adaptive_learning(
        &config,
        &mut replay_oracle,
        Cursor::new(b""),
        &mut replay_output,
    )
    .err()
    .expect("reproduce the stopped transition from cached artifacts");
    assert_eq!(replay_error.to_string(), error.to_string());
    assert_eq!(replay_oracle.matrix_passes, 0);
    assert_eq!(replay_oracle.vector_lookups, 0);
    assert!(
        String::from_utf8(replay_output)
            .unwrap()
            .contains("Phase 3 learning is stopped")
    );

    let mut corrupt = failed.clone();
    let score =
        corrupt["failure"]["candidate_order_attempts"][0]["record"]["accepted"][0]["raw_score"]
            .as_f64()
            .expect("stored raw score");
    corrupt["failure"]["candidate_order_attempts"][0]["record"]["accepted"][0]["raw_score"] =
        serde_json::json!(score + 0.25);
    std::fs::write(
        &session_path,
        serde_json::to_vec_pretty(&corrupt).expect("encode corrupt failure diagnostic"),
    )
    .expect("write corrupt failure diagnostic");
    let mut rejecting_oracle = FixtureOracle::new(fixture.event_ids.clone());
    let mut rejecting_output = Vec::new();
    let corrupt_error = run_adaptive_learning(
        &config,
        &mut rejecting_oracle,
        Cursor::new(b""),
        &mut rejecting_output,
    )
    .err()
    .expect("reject a corrupted failed-attempt diagnostic");
    assert!(corrupt_error.to_string().contains("failed its checksum"));
    assert_eq!(rejecting_oracle.matrix_passes, 0);
    assert_eq!(rejecting_oracle.vector_lookups, 0);
    assert!(rejecting_output.is_empty());

    std::fs::write(
        &session_path,
        serde_json::to_vec_pretty(&failed).expect("restore failed session"),
    )
    .expect("restore failed session");
    let mut transition_corrupt = failed;
    transition_corrupt["failure"]["transition"]["kind"] = serde_json::json!("submit_ratings");
    std::fs::write(
        &session_path,
        serde_json::to_vec_pretty(&transition_corrupt).expect("encode corrupt failure transition"),
    )
    .expect("write corrupt failure transition");
    let mut transition_rejecting_oracle = FixtureOracle::new(fixture.event_ids.clone());
    let transition_error = run_adaptive_learning(
        &config,
        &mut transition_rejecting_oracle,
        Cursor::new(b""),
        &mut Vec::new(),
    )
    .err()
    .expect("reject a corrupted failure transition");
    assert!(
        transition_error
            .to_string()
            .contains("failure failed its checksum"),
        "unexpected transition-tamper error: {transition_error}"
    );
    assert_eq!(transition_rejecting_oracle.matrix_passes, 0);
    assert_eq!(transition_rejecting_oracle.vector_lookups, 0);
}

#[test]
fn language_limit_failure_replays_prior_rounds_and_the_failed_transition() {
    let fixture = RunnerFixture::new();
    let session_path = fixture.temp.path().join("language-limit-failure.json");
    let config = fixture.config(session_path.clone());
    let mut input = "7\n".repeat(20);
    input.push_str(&"l\n".repeat(22));
    input.push_str(&"7\n".repeat(18));

    let mut first_oracle = FixtureOracle::new(fixture.event_ids.clone());
    let first_error = run_adaptive_learning(
        &config,
        &mut first_oracle,
        Cursor::new(input.into_bytes()),
        &mut Vec::new(),
    )
    .err()
    .expect("the twenty-second wrong-language result stops learning");
    assert!(first_error.to_string().contains("WrongLanguageLimit"));

    let failed = read_session(&session_path);
    assert_eq!(failed["phase"], "failed");
    assert_eq!(failed["rounds"][0]["ratings_submitted"], true);
    assert_eq!(failed["rounds"][1]["ratings_submitted"], false);
    assert_eq!(failed["failure"]["transition"]["kind"], "submit_language");

    let mut replay_oracle = FixtureOracle::new(fixture.event_ids.clone());
    let replay_error = run_adaptive_learning(
        &config,
        &mut replay_oracle,
        Cursor::new(b""),
        &mut Vec::new(),
    )
    .err()
    .expect("replay the failed language transition");
    assert_eq!(replay_error.to_string(), first_error.to_string());
    assert_eq!(replay_oracle.matrix_passes, 0);
    assert_eq!(replay_oracle.vector_lookups, 0);

    let mut judgment_corrupt = failed.clone();
    let decisions = judgment_corrupt["rounds"][1]["waves"][1]["decisions"]
        .as_array_mut()
        .expect("failed-wave decisions");
    let wrong_index = decisions
        .iter()
        .position(|decision| decision["outcome"] == "wrong_language")
        .expect("wrong-language decision");
    let rated_index = decisions
        .iter()
        .position(|decision| decision["outcome"] == "rated")
        .expect("rated decision");
    let wrong_event_id = decisions[wrong_index]["event_id"].clone();
    let rated_event_id = decisions[rated_index]["event_id"].clone();
    let rating = decisions[rated_index]["rating"].clone();
    decisions[wrong_index] = serde_json::json!({
        "outcome": "rated",
        "event_id": wrong_event_id,
        "rating": rating,
    });
    decisions[rated_index] = serde_json::json!({
        "outcome": "wrong_language",
        "event_id": rated_event_id,
    });
    std::fs::write(
        &session_path,
        serde_json::to_vec_pretty(&judgment_corrupt).expect("encode swapped failed-wave judgments"),
    )
    .expect("write swapped failed-wave judgments");
    let mut judgment_rejecting_oracle = FixtureOracle::new(fixture.event_ids.clone());
    let judgment_error = run_adaptive_learning(
        &config,
        &mut judgment_rejecting_oracle,
        Cursor::new(b""),
        &mut Vec::new(),
    )
    .err()
    .expect("reject changed judgments with unchanged failure counts");
    assert!(
        judgment_error
            .to_string()
            .contains("failed transition input")
    );
    assert_eq!(judgment_rejecting_oracle.matrix_passes, 0);
    assert_eq!(judgment_rejecting_oracle.vector_lookups, 0);

    let mut corrupt = failed;
    corrupt["rounds"][0]["diagnostic_seal"]["errors_sha256"] = serde_json::json!("0".repeat(64));
    std::fs::write(
        &session_path,
        serde_json::to_vec_pretty(&corrupt).expect("encode corrupt prior round seal"),
    )
    .expect("write corrupt prior round seal");
    let mut rejecting_oracle = FixtureOracle::new(fixture.event_ids.clone());
    let error = run_adaptive_learning(
        &config,
        &mut rejecting_oracle,
        Cursor::new(b""),
        &mut Vec::new(),
    )
    .err()
    .expect("reject prior-round drift before accepting the failed session");
    assert!(error.to_string().contains("completed round diagnostic"));
    assert_eq!(rejecting_oracle.matrix_passes, 0);
    assert_eq!(rejecting_oracle.vector_lookups, 0);
}

#[test]
fn transient_oracle_error_keeps_the_learning_session_retryable() {
    let fixture = RunnerFixture::new();
    let session_path = fixture.temp.path().join("transient-oracle-error.json");
    let config = fixture.config(session_path.clone());
    let mut oracle = FailOnceOracle::new(fixture.event_ids.clone());

    let error = run_adaptive_learning(&config, &mut oracle, Cursor::new(b""), &mut Vec::new())
        .err()
        .expect("surface the injected transient Oracle error");
    assert!(
        error
            .to_string()
            .contains("injected transient Oracle failure")
    );
    let retryable = read_session(&session_path);
    assert_eq!(retryable["phase"], "learning");
    assert!(retryable["failure"].is_null());
    assert!(!retryable["pause_reason"].is_null());

    let resumed =
        run_adaptive_learning(&config, &mut oracle, Cursor::new(b"7q\n"), &mut Vec::new())
            .expect("retry the same transition after the Oracle recovers");
    assert!(matches!(resumed, AdaptiveLearningRunnerOutcome::Paused));
    let recovered = read_session(&session_path);
    assert_eq!(recovered["phase"], "learning");
    assert!(recovered["failure"].is_null());
}

#[test]
fn concealed_order_is_deterministic_and_displays_only_raw_note_content() {
    let first_fixture = RunnerFixture::new();
    let first_session_path = first_fixture.temp.path().join("first-session.json");
    let first_config = first_fixture.config(first_session_path.clone());
    let mut first_oracle = FixtureOracle::new(first_fixture.event_ids.clone());
    let mut first_output = Vec::new();
    let first = run_adaptive_learning(
        &first_config,
        &mut first_oracle,
        Cursor::new(b"4q\n"),
        &mut first_output,
    )
    .expect("start first session");
    assert!(matches!(first, AdaptiveLearningRunnerOutcome::Paused));

    let second_fixture = RunnerFixture::new();
    let second_session_path = second_fixture.temp.path().join("second-session.json");
    let second_config = second_fixture.config(second_session_path.clone());
    let mut second_oracle = FixtureOracle::new(second_fixture.event_ids.clone());
    let mut second_output = Vec::new();
    let second = run_adaptive_learning(
        &second_config,
        &mut second_oracle,
        Cursor::new(b"4q\n"),
        &mut second_output,
    )
    .expect("start second session");
    assert!(matches!(second, AdaptiveLearningRunnerOutcome::Paused));

    let first_session = read_session(&first_session_path);
    let second_session = read_session(&second_session_path);
    assert_eq!(
        first_session["rounds"][0]["waves"][0]["presentation_order"],
        second_session["rounds"][0]["waves"][0]["presentation_order"]
    );
    let coordinator_ids = first_session["rounds"][0]["waves"][0]["coordinator_event_ids"]
        .as_array()
        .unwrap();
    let presentation_ids = first_session["rounds"][0]["waves"][0]["presentation_order"]
        .as_array()
        .unwrap();
    assert_eq!(coordinator_ids.len(), presentation_ids.len());
    assert_ne!(
        coordinator_ids, presentation_ids,
        "the fixture must exercise shuffling"
    );

    let transcript = std::str::from_utf8(&first_output).expect("UTF-8 transcript");
    assert!(transcript.contains("https://example.com/runner"));
    assert!(transcript.contains("nostr:note1runnerfixture"));
    for forbidden in ["Compact", "RBF", "cosine", "rank", "score"] {
        assert!(!transcript.contains(forbidden), "leaked `{forbidden}`");
    }
    assert_eq!(first_output, second_output);
}

#[test]
fn a_small_corpus_uses_every_available_neighbor_below_candidate_depth() {
    let fixture = RunnerFixture::with_note_count(100);
    let session_path = fixture.temp.path().join("small-corpus-session.json");
    let config = fixture.config(session_path);
    let mut oracle = FixtureOracle::new(fixture.event_ids.clone());

    let outcome =
        run_adaptive_learning(&config, &mut oracle, Cursor::new(b"4q\n"), &mut Vec::new())
            .expect("run with fewer rows than the Oracle candidate depth");

    assert!(matches!(outcome, AdaptiveLearningRunnerOutcome::Paused));
    assert_eq!(oracle.matrix_passes, 1);
}

#[test]
fn an_active_session_lock_rejects_a_second_runner_before_oracle_work() {
    let fixture = RunnerFixture::new();
    let session_path = fixture.temp.path().join("locked-session.json");
    let lock_path = fixture.temp.path().join(".locked-session.json.lock");
    let lock = std::fs::OpenOptions::new()
        .create(true)
        .read(true)
        .write(true)
        .truncate(false)
        .open(&lock_path)
        .expect("open session lock");
    lock.try_lock().expect("hold session lock");
    let config = fixture.config(session_path.clone());
    let mut oracle = FixtureOracle::new(fixture.event_ids.clone());

    let error = run_adaptive_learning(&config, &mut oracle, Cursor::new(b"4q\n"), &mut Vec::new())
        .err()
        .expect("reject concurrent session");

    assert!(error.to_string().contains("already active"));
    assert_eq!(oracle.vector_lookups, 0);
    assert_eq!(oracle.matrix_passes, 0);
    assert!(!session_path.exists());
}

#[test]
fn malformed_input_reprompts_without_advancing_or_persisting_it() {
    let fixture = RunnerFixture::new();
    let session_path = fixture.temp.path().join("malformed-session.json");
    let config = fixture.config(session_path.clone());
    let mut oracle = FixtureOracle::new(fixture.event_ids.clone());
    let mut output = Vec::new();

    let outcome = run_adaptive_learning(
        &config,
        &mut oracle,
        Cursor::new(b"garbage\n0\n8\n6q\n"),
        &mut output,
    )
    .expect("retry malformed input");
    assert!(matches!(outcome, AdaptiveLearningRunnerOutcome::Paused));
    let session = read_session(&session_path);
    let decisions = session["rounds"][0]["waves"][0]["decisions"]
        .as_array()
        .unwrap();
    assert_eq!(decisions.len(), 1);
    assert_eq!(decisions[0]["rating"], 6);
    assert_eq!(session["rounds"][0]["waves"][0]["submitted"], false);
    assert_eq!(session["rounds"][0]["ratings_submitted"], false);
    let transcript = String::from_utf8(output).expect("UTF-8 transcript");
    assert_eq!(
        transcript
            .matches("Enter 1 to 7 or `l`; append `q` to save that decision and stop.")
            .count(),
        3
    );
}

#[test]
fn wrong_language_uses_a_frozen_replacement_without_losing_staged_ratings() {
    let fixture = RunnerFixture::new();
    let session_path = fixture.temp.path().join("language-session.json");
    let config = fixture.config(session_path.clone());
    let mut oracle = FixtureOracle::new(fixture.event_ids.clone());
    let mut input = String::from("l\n");
    input.push_str(&"7\n".repeat(19));
    input.push_str("7q\n");

    let paused = run_adaptive_learning(
        &config,
        &mut oracle,
        Cursor::new(input.into_bytes()),
        &mut Vec::new(),
    )
    .expect("save the complete replacement wave");
    assert!(matches!(paused, AdaptiveLearningRunnerOutcome::Paused));
    let outcome = run_adaptive_learning(&config, &mut oracle, Cursor::new(b""), &mut Vec::new())
        .expect("submit the replacement round");
    assert!(matches!(outcome, AdaptiveLearningRunnerOutcome::Paused));
    let session = read_session(&session_path);
    let round = &session["rounds"][0];
    assert_eq!(round["waves"].as_array().unwrap().len(), 2);
    assert_eq!(round["waves"][0]["decisions"].as_array().unwrap().len(), 20);
    assert_eq!(round["waves"][1]["decisions"].as_array().unwrap().len(), 1);
    assert_eq!(round["waves"][0]["submitted"], true);
    assert_eq!(round["waves"][1]["submitted"], true);
    assert_eq!(round["ratings_submitted"], true);
    let decisions = round["waves"]
        .as_array()
        .unwrap()
        .iter()
        .flat_map(|wave| wave["decisions"].as_array().unwrap())
        .collect::<Vec<_>>();
    assert_eq!(
        decisions
            .iter()
            .filter(|decision| decision["outcome"] == "wrong_language")
            .count(),
        1
    );
    assert_eq!(
        decisions
            .iter()
            .filter(|decision| decision["outcome"] == "rated")
            .count(),
        20
    );
    let unique = decisions
        .iter()
        .map(|decision| value_event_id(&decision["event_id"]))
        .collect::<std::collections::BTreeSet<_>>();
    assert_eq!(unique.len(), 21, "no presented note may repeat");
}

#[test]
fn resume_recovers_the_boundary_between_a_submitted_wave_and_its_replacement() {
    let fixture = RunnerFixture::new();
    let session_path = fixture.temp.path().join("replacement-boundary.json");
    let config = fixture.config(session_path.clone());
    let mut oracle = FixtureOracle::new(fixture.event_ids.clone());
    let mut input = String::from("l\n");
    input.push_str(&"7\n".repeat(19));
    input.push_str("7q\n");
    run_adaptive_learning(
        &config,
        &mut oracle,
        Cursor::new(input.into_bytes()),
        &mut Vec::new(),
    )
    .expect("reach the replacement wave");

    // Model the last valid session file if publication stopped after recording
    // the complete first-wave transition but before recording its derived wave.
    let mut boundary = read_session(&session_path);
    boundary["rounds"][0]["waves"]
        .as_array_mut()
        .expect("waves")
        .truncate(1);
    std::fs::write(
        &session_path,
        serde_json::to_vec_pretty(&boundary).expect("encode boundary"),
    )
    .expect("write boundary");

    let mut resumed_oracle = FixtureOracle::new(fixture.event_ids.clone());
    let outcome = run_adaptive_learning(
        &config,
        &mut resumed_oracle,
        Cursor::new(b""),
        &mut Vec::new(),
    )
    .expect("recover replacement boundary");
    assert!(matches!(outcome, AdaptiveLearningRunnerOutcome::Paused));
    let recovered = read_session(&session_path);
    assert_eq!(recovered["rounds"][0]["waves"].as_array().unwrap().len(), 2);
    assert_eq!(
        recovered["rounds"][0]["waves"][1]["decisions"],
        serde_json::json!([])
    );
}

#[test]
fn configuration_mismatch_is_rejected_before_oracle_work_and_keeps_session_bytes() {
    let fixture = RunnerFixture::new();
    let session_path = fixture.temp.path().join("bound-session.json");
    let config = fixture.config(session_path.clone());
    let mut first_oracle = FixtureOracle::new(fixture.event_ids.clone());
    run_adaptive_learning(
        &config,
        &mut first_oracle,
        Cursor::new(b"4q\n"),
        &mut Vec::new(),
    )
    .expect("create bound session");
    let before = std::fs::read(&session_path).expect("read original session");

    let mut changed = config.clone();
    changed.b16 = B16Boundary::new(VERSION, 0.25).expect("changed B16");
    let mut resumed_oracle = FixtureOracle::new(fixture.event_ids.clone());
    let error = run_adaptive_learning(
        &changed,
        &mut resumed_oracle,
        Cursor::new(b"7\n"),
        &mut Vec::new(),
    )
    .err()
    .expect("configuration mismatch");
    assert!(error.to_string().contains("immutable configuration"));
    assert_eq!(resumed_oracle.vector_lookups, 0);
    assert_eq!(resumed_oracle.matrix_passes, 0);
    assert_eq!(
        std::fs::read(&session_path).expect("read unchanged session"),
        before
    );
}

#[test]
fn an_orphaned_completed_oracle_call_preserves_responses_metrics_and_matrix_work() {
    let fixture = RunnerFixture::new();
    let session_path = fixture.temp.path().join("orphan-recovery-session.json");
    let config = fixture.config(session_path.clone());
    let mut first_oracle = FixtureOracle::new(fixture.event_ids.clone());
    run_adaptive_learning(
        &config,
        &mut first_oracle,
        Cursor::new(b"4q\n"),
        &mut Vec::new(),
    )
    .expect("create cached first round");
    assert_eq!(first_oracle.matrix_passes, 1);

    // Model a crash after one atomic logical-call record reached disk but before
    // its derived per-source response files or following session publication.
    let cache_dir = fixture
        .temp
        .path()
        .join(".orphan-recovery-session.json.oracle-responses");
    for entry in std::fs::read_dir(&cache_dir).expect("read Oracle cache") {
        let entry = entry.expect("cache entry");
        let name = entry.file_name();
        let name = name.to_str().expect("UTF-8 cache name");
        if !name.starts_with("call-") && !name.starts_with("vectors-") {
            std::fs::remove_file(entry.path()).expect("remove derived response");
        }
    }
    let mut before_publication = read_session(&session_path);
    before_publication["rounds"] = serde_json::json!([]);
    before_publication["oracle_calls"] = serde_json::json!([]);
    before_publication["oracle_responses"] = serde_json::json!([]);
    std::fs::write(
        &session_path,
        serde_json::to_vec_pretty(&before_publication).expect("encode crash state"),
    )
    .expect("write crash state");

    let mut resumed_oracle = FixtureOracle::new(fixture.event_ids.clone());
    let outcome = run_adaptive_learning(
        &config,
        &mut resumed_oracle,
        Cursor::new(b"4q\n"),
        &mut Vec::new(),
    )
    .expect("recover orphaned Oracle response");
    assert!(matches!(outcome, AdaptiveLearningRunnerOutcome::Paused));
    assert_eq!(
        resumed_oracle.matrix_passes, 0,
        "a completed immutable response must survive the session-publication crash window"
    );
    let recovered = read_session(&session_path);
    assert_eq!(
        recovered["oracle_calls"][0]["metrics"]["matrix_passes"], 1,
        "recovery must retain the original operational audit, not invent a cache-only call"
    );
}

#[test]
fn resumed_and_uninterrupted_ten_round_runs_freeze_the_same_handoff() {
    let uninterrupted_fixture = RunnerFixture::new();
    let uninterrupted_path = uninterrupted_fixture
        .temp
        .path()
        .join("uninterrupted-session.json");
    let uninterrupted_config = uninterrupted_fixture.config(uninterrupted_path.clone());
    let mut uninterrupted_oracle = FixtureOracle::new(uninterrupted_fixture.event_ids.clone());
    let uninterrupted = run_adaptive_learning(
        &uninterrupted_config,
        &mut uninterrupted_oracle,
        Cursor::new("7\n".repeat(200).into_bytes()),
        &mut Vec::new(),
    )
    .expect("complete uninterrupted learning");
    let uninterrupted_handoff = completed(uninterrupted);
    let sealed = read_session(&uninterrupted_path);
    assert!(sealed["completion"]["compact_active_tuple"].is_object());
    assert!(sealed["completion"]["rbf_active_tuple"].is_object());
    let sealed_rounds = sealed["completion"]["ordered_rounds"]
        .as_array()
        .expect("sealed completed rounds");
    assert_eq!(sealed_rounds.len(), 10);
    for round in sealed_rounds {
        for field in [
            "round_record_sha256",
            "frozen_predictions_sha256",
            "errors_sha256",
            "next_tuples_sha256",
            "candidate_order_audit_sha256",
            "shared_round_audit_sha256",
        ] {
            assert_eq!(
                round[field].as_str().map(str::len),
                Some(64),
                "round diagnostic `{field}` must be cryptographically sealed"
            );
        }
    }

    let resumed_fixture = RunnerFixture::new();
    let resumed_path = resumed_fixture.temp.path().join("resumed-session.json");
    let resumed_config = resumed_fixture.config(resumed_path.clone());
    for ratings in [37, 63] {
        let mut oracle = FixtureOracle::new(resumed_fixture.event_ids.clone());
        let outcome = run_adaptive_learning(
            &resumed_config,
            &mut oracle,
            Cursor::new(ratings_then_quit(ratings, 7)),
            &mut Vec::new(),
        )
        .expect("pause resumed learning");
        assert!(matches!(outcome, AdaptiveLearningRunnerOutcome::Paused));
    }
    let mut final_oracle = FixtureOracle::new(resumed_fixture.event_ids.clone());
    let resumed = run_adaptive_learning(
        &resumed_config,
        &mut final_oracle,
        Cursor::new("7\n".repeat(100).into_bytes()),
        &mut Vec::new(),
    )
    .expect("complete resumed learning");
    let resumed_handoff = completed(resumed);

    assert_eq!(
        uninterrupted_handoff
            .compact_controller()
            .evidence_identity(),
        resumed_handoff.compact_controller().evidence_identity()
    );
    assert_eq!(
        uninterrupted_handoff.rbf_controller().evidence_identity(),
        resumed_handoff.rbf_controller().evidence_identity()
    );
    assert_eq!(
        uninterrupted_handoff.compact_controller().history(),
        resumed_handoff.compact_controller().history()
    );
    assert_eq!(
        uninterrupted_handoff.rbf_controller().history(),
        resumed_handoff.rbf_controller().history()
    );
    assert_eq!(
        uninterrupted_handoff.presentation_ledger(),
        resumed_handoff.presentation_ledger()
    );
    assert_eq!(uninterrupted_handoff.ratings(), resumed_handoff.ratings());
    assert_eq!(
        uninterrupted_handoff.language_totals(),
        resumed_handoff.language_totals()
    );
    assert_eq!(
        uninterrupted_handoff.round_records(),
        resumed_handoff.round_records()
    );
    assert_eq!(
        uninterrupted_handoff.source_wave_records(),
        resumed_handoff.source_wave_records()
    );

    let uninterrupted_session = read_session(&uninterrupted_path);
    let resumed_session = read_session(&resumed_path);
    assert_eq!(uninterrupted_session["phase"], "complete");
    assert_eq!(uninterrupted_session["rounds"], resumed_session["rounds"]);
    assert_eq!(
        uninterrupted_session["oracle_calls"],
        resumed_session["oracle_calls"]
    );
    assert_eq!(
        uninterrupted_session["completion"],
        resumed_session["completion"]
    );

    let before_reopen = std::fs::read(&resumed_path).expect("read completed session");
    let mut before_handoff_publication = read_session(&resumed_path);
    before_handoff_publication["phase"] = serde_json::json!("learning");
    before_handoff_publication["completion"] = serde_json::Value::Null;
    let mut crash_bytes =
        serde_json::to_vec_pretty(&before_handoff_publication).expect("encode crash boundary");
    crash_bytes.push(b'\n');
    std::fs::write(&resumed_path, crash_bytes).expect("write pre-handoff crash boundary");
    std::fs::rename(
        &resumed_fixture.corpus_path,
        resumed_fixture
            .temp
            .path()
            .join("completed-corpus-unavailable.ndb"),
    )
    .expect("make display-only corpus unavailable after learning");
    let mut reopened_oracle = FixtureOracle::new(resumed_fixture.event_ids.clone());
    let mut reopened_output = Vec::new();
    let reopened = run_adaptive_learning(
        &resumed_config,
        &mut reopened_oracle,
        Cursor::new(b"1\n"),
        &mut reopened_output,
    )
    .expect("recover the completed handoff without the display corpus");
    assert!(matches!(
        reopened,
        AdaptiveLearningRunnerOutcome::Complete(_)
    ));
    assert_eq!(reopened_oracle.matrix_passes, 0);
    assert_eq!(
        reopened_oracle.vector_lookups, 0,
        "the persisted handoff must reconstruct both learned controllers without reading external vectors"
    );
    assert_eq!(
        std::fs::read(&resumed_path).expect("reread completed session"),
        before_reopen
    );
    let transcript = String::from_utf8(reopened_output).expect("UTF-8 summary");
    assert!(transcript.contains("Phase 3 learning complete"));
    assert!(!transcript.contains("raw runner fixture note"));

    let mut tuple_corrupted = read_session(&resumed_path);
    tuple_corrupted["completion"]["compact_active_tuple"]["parameters"]["maximum_distance"] =
        serde_json::json!(0.0);
    std::fs::write(
        &resumed_path,
        serde_json::to_vec_pretty(&tuple_corrupted).expect("encode corrupted final tuple"),
    )
    .expect("write corrupted final tuple");
    let mut tuple_rejecting_oracle = FixtureOracle::new(resumed_fixture.event_ids.clone());
    let tuple_error = run_adaptive_learning(
        &resumed_config,
        &mut tuple_rejecting_oracle,
        Cursor::new(b""),
        &mut Vec::new(),
    )
    .err()
    .expect("reject a corrupted final active tuple");
    assert!(
        tuple_error
            .to_string()
            .contains("does not match deterministic replay")
    );
    assert_eq!(tuple_rejecting_oracle.matrix_passes, 0);
    assert_eq!(tuple_rejecting_oracle.vector_lookups, 0);
    std::fs::write(&resumed_path, &before_reopen).expect("restore completed session");

    let mut diagnostic_corrupted = read_session(&resumed_path);
    diagnostic_corrupted["completion"]["ordered_rounds"][0]["candidate_order_audit_sha256"] =
        serde_json::json!("0".repeat(64));
    std::fs::write(
        &resumed_path,
        serde_json::to_vec_pretty(&diagnostic_corrupted)
            .expect("encode corrupted round diagnostic"),
    )
    .expect("write corrupted round diagnostic");
    let mut diagnostic_rejecting_oracle = FixtureOracle::new(resumed_fixture.event_ids.clone());
    let diagnostic_error = run_adaptive_learning(
        &resumed_config,
        &mut diagnostic_rejecting_oracle,
        Cursor::new(b""),
        &mut Vec::new(),
    )
    .err()
    .expect("reject a corrupted round diagnostic seal");
    assert!(
        diagnostic_error
            .to_string()
            .contains("does not match deterministic replay")
    );
    assert_eq!(diagnostic_rejecting_oracle.matrix_passes, 0);
    assert_eq!(diagnostic_rejecting_oracle.vector_lookups, 0);
    std::fs::write(&resumed_path, &before_reopen).expect("restore completed session");

    let mut corrupted = read_session(&resumed_path);
    corrupted["completion"]["eligible_presentations"] = serde_json::json!(999);
    std::fs::write(
        &resumed_path,
        serde_json::to_vec_pretty(&corrupted).expect("encode corrupted handoff"),
    )
    .expect("write corrupted handoff");
    let mut rejecting_oracle = FixtureOracle::new(resumed_fixture.event_ids.clone());
    let error = run_adaptive_learning(
        &resumed_config,
        &mut rejecting_oracle,
        Cursor::new(b""),
        &mut Vec::new(),
    )
    .err()
    .expect("reject corrupted completion seal");
    assert!(
        error
            .to_string()
            .contains("does not match deterministic replay")
    );
    assert_eq!(rejecting_oracle.matrix_passes, 0);
}

#[test]
fn an_all_stored_cross_personalizer_round_completes_without_input_or_redisplay() {
    let fixture = DivergentFixture::new();
    let session_path = fixture.temp.path().join("stored-reuse-session.json");
    let config = fixture.config(session_path.clone());
    let mut oracle = DivergentOracle::new(&fixture);
    let input = ratings_then_quit(40, 7);

    let paused = run_adaptive_learning(&config, &mut oracle, Cursor::new(input), &mut Vec::new())
        .expect("save the first round ratings");
    assert!(matches!(paused, AdaptiveLearningRunnerOutcome::Paused));
    let outcome = run_adaptive_learning(&config, &mut oracle, Cursor::new(b""), &mut Vec::new())
        .expect("advance through stored-rating reuse");
    assert!(matches!(outcome, AdaptiveLearningRunnerOutcome::Paused));
    let session = read_session(&session_path);
    assert_eq!(
        session["rounds"][0]["waves"][0]["decisions"]
            .as_array()
            .unwrap()
            .len(),
        40
    );
    assert_eq!(session["rounds"][0]["ratings_submitted"], true);
    assert_eq!(session["rounds"][1]["round"], 2);
    assert_eq!(session["rounds"][1]["waves"], serde_json::json!([]));
    assert_eq!(session["rounds"][1]["ratings_submitted"], true);
    assert_eq!(session["rounds"][2]["round"], 3);
    assert_eq!(
        session["rounds"][2]["waves"][0]["decisions"],
        serde_json::json!([]),
        "the next evaluator input belongs to round three, not stored-reuse round two"
    );
}

#[test]
fn completed_learning_round_seal_rejects_drift_before_next_input() {
    let fixture = DivergentFixture::new();
    let session_path = fixture.temp.path().join("completed-round-seal.json");
    let config = fixture.config(session_path.clone());
    let mut oracle = DivergentOracle::new(&fixture);

    run_adaptive_learning(
        &config,
        &mut oracle,
        Cursor::new(ratings_then_quit(40, 7)),
        &mut Vec::new(),
    )
    .expect("save first-round ratings");
    run_adaptive_learning(&config, &mut oracle, Cursor::new(b""), &mut Vec::new())
        .expect("complete stored rounds and pause before more input");

    let mut session = read_session(&session_path);
    assert_eq!(session["phase"], "learning");
    assert_eq!(session["rounds"][0]["ratings_submitted"], true);
    assert_eq!(
        session["rounds"][0]["diagnostic_seal"]["candidate_order_audit_sha256"]
            .as_str()
            .map(str::len),
        Some(64),
        "every completed learning round must be sealed before the next round starts"
    );
    assert_eq!(
        session["rounds"][0]["diagnostic_seal"]["round_record_sha256"]
            .as_str()
            .map(str::len),
        Some(64),
        "the complete round record must have one authoritative seal"
    );
    assert_eq!(
        session["rounds"][0]["diagnostic_seal"]["presentation_ledger"][0]["state"]["kind"], "rated",
        "presentation state must use stable structured data rather than Debug text"
    );
    session["rounds"][0]["diagnostic_seal"]["candidate_order_audit_sha256"] =
        serde_json::json!("0".repeat(64));
    std::fs::write(
        &session_path,
        serde_json::to_vec_pretty(&session).expect("encode corrupted round seal"),
    )
    .expect("write corrupted round seal");

    let mut rejecting_oracle = DivergentOracle::new(&fixture);
    let error = run_adaptive_learning(
        &config,
        &mut rejecting_oracle,
        Cursor::new(b""),
        &mut Vec::new(),
    )
    .err()
    .expect("reject completed-round drift before requesting more input");
    assert!(error.to_string().contains("completed round diagnostic"));
    assert_eq!(rejecting_oracle.matrix_passes, 0);
    assert_eq!(rejecting_oracle.logical_wave_calls, 0);
}

fn completed(
    outcome: AdaptiveLearningRunnerOutcome,
) -> Box<oracle_mvp::adaptive_learning::CompletedAdaptiveLearning> {
    match outcome {
        AdaptiveLearningRunnerOutcome::Complete(completed) => completed,
        AdaptiveLearningRunnerOutcome::Paused => panic!("expected completed learning"),
    }
}

fn ratings_then_quit(count: usize, rating: u8) -> Vec<u8> {
    assert!(count > 0);
    let mut input = format!("{rating}\n").repeat(count - 1);
    input.push_str(&format!("{rating}q\n"));
    input.into_bytes()
}

struct RunnerFixture {
    temp: tempfile::TempDir,
    corpus_path: std::path::PathBuf,
    event_ids: Vec<EventId>,
    contents: Vec<String>,
}

struct DivergentFixture {
    temp: tempfile::TempDir,
    corpus_path: std::path::PathBuf,
    event_ids: Vec<EventId>,
    candidates: Vec<EventId>,
    vectors: BTreeMap<EventId, Vec<f32>>,
}

impl DivergentFixture {
    fn new() -> Self {
        let temp = tempfile::tempdir().expect("temporary directory");
        let corpus_path = temp.path().join("corpus.ndb");
        let ndb = open_ndb(&corpus_path);
        let contents = (0..1_050)
            .map(|index| format!("stored reuse fixture note {index:04}"))
            .collect::<Vec<_>>();
        let events = contents
            .iter()
            .enumerate()
            .map(|(index, content)| signed_event(content, 10_000 + index as u64))
            .collect::<Vec<_>>();
        for event in &events {
            ndb.process_event(event).expect("submit divergent event");
        }
        wait_for_count(&ndb, events.len());
        drop(ndb);
        let event_ids = events
            .iter()
            .map(|event| event_id(event))
            .collect::<Vec<_>>();
        let candidates = event_ids[5..].to_vec();
        let mut vectors = BTreeMap::new();
        for (event_id, vector) in event_ids[..5].iter().copied().zip(divergent_seed_vectors()) {
            vectors.insert(event_id, vector);
        }
        for event_id in event_ids[5..25].iter().copied() {
            vectors.insert(event_id, unit_vector(122.0));
        }
        for event_id in event_ids[25..45].iter().copied() {
            vectors.insert(event_id, unit_vector(70.0));
        }
        for event_id in event_ids[45..].iter().copied() {
            vectors.insert(event_id, unit_vector(214.0));
        }
        Self {
            temp,
            corpus_path,
            event_ids,
            candidates,
            vectors,
        }
    }

    fn config(&self, session_path: std::path::PathBuf) -> AdaptiveLearningRunnerConfig {
        AdaptiveLearningRunnerConfig {
            corpus_path: self.corpus_path.clone(),
            corpus_identity: "divergent-corpus-v1".to_owned(),
            session_path,
            compact_settings: CompactLearningSettings::new(
                VERSION,
                0.5,
                1.0,
                2.0,
                ScaleLevel::Mass64,
            )
            .expect("compact settings"),
            rbf_settings: RbfLearningSettings::new(VERSION, 0.5, 1.0, 2.0).expect("RBF settings"),
            b16: B16Boundary::new(VERSION, 0.0).expect("B16"),
            seeds: self.event_ids[..5]
                .iter()
                .copied()
                .map(|event_id| AdaptiveLearningSeed::new(event_id, 7).expect("positive seed"))
                .collect(),
        }
    }
}

fn divergent_seed_vectors() -> [Vec<f32>; 5] {
    [
        unit_vector(0.0),
        unit_vector(180.0),
        unit_vector(90.0),
        unit_vector(270.0),
        unit_vector(45.0),
    ]
}

fn unit_vector(degrees: f32) -> Vec<f32> {
    let radians = degrees.to_radians();
    vec![radians.cos(), radians.sin()]
}

struct DivergentOracle {
    candidates: Vec<EventId>,
    vectors: BTreeMap<EventId, Vec<f32>>,
    responses: BTreeMap<EventId, SimilarNotesResponse>,
    rows: u64,
    matrix_passes: usize,
    logical_wave_calls: usize,
}

impl DivergentOracle {
    fn new(fixture: &DivergentFixture) -> Self {
        Self {
            candidates: fixture.candidates.clone(),
            vectors: fixture.vectors.clone(),
            responses: BTreeMap::new(),
            rows: fixture.event_ids.len() as u64,
            matrix_passes: 0,
            logical_wave_calls: 0,
        }
    }

    fn response(&self, source: EventId) -> SimilarNotesResponse {
        SimilarNotesResponse {
            representation_version: VERSION.to_owned(),
            represented_rows: self.rows,
            total_rows: self.rows,
            complete: true,
            candidates: self
                .candidates
                .iter()
                .copied()
                .filter(|event_id| *event_id != source)
                .take(1_024)
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

impl CandidateOrderOracle for DivergentOracle {
    fn representation_version(&self) -> &str {
        VERSION
    }

    fn similar_notes_wave(
        &mut self,
        requests: &[SimilarNotesRequest],
        representation_version: &str,
    ) -> SnapshotResult<SimilarNotesWaveResponse> {
        self.logical_wave_calls += 1;
        if representation_version != VERSION || requests.is_empty() {
            return Err(SnapshotError::InvalidQuery(
                "unexpected divergent query".to_owned(),
            ));
        }
        let missing = requests
            .iter()
            .filter(|request| !self.responses.contains_key(&request.note_id))
            .map(|request| request.note_id)
            .collect::<Vec<_>>();
        if !missing.is_empty() {
            self.matrix_passes += 1;
        }
        for event_id in missing.iter().copied() {
            let response = self.response(event_id);
            self.responses.insert(event_id, response);
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
                scanned_rows: if missing.is_empty() { 0 } else { self.rows },
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
                "unexpected divergent representation".to_owned(),
            ));
        }
        Ok(VectorsForNotesResponse {
            representation_version: VERSION.to_owned(),
            represented_rows: self.rows,
            total_rows: self.rows,
            complete: true,
            lookup_elapsed_ns: 0,
            vectors: note_ids
                .iter()
                .map(|event_id| {
                    self.vectors
                        .get(event_id)
                        .cloned()
                        .map(|vector| StoredNoteVector {
                            event_id: *event_id,
                            vector,
                        })
                        .ok_or_else(|| SnapshotError::EventNotFound(format!("{event_id:?}")))
                })
                .collect::<SnapshotResult<Vec<_>>>()?,
        })
    }
}

impl RunnerFixture {
    fn new() -> Self {
        Self::with_note_count(1_030)
    }

    fn with_note_count(note_count: usize) -> Self {
        let temp = tempfile::tempdir().expect("temporary directory");
        let corpus_path = temp.path().join("corpus.ndb");
        let ndb = open_ndb(&corpus_path);
        let contents = (0..note_count)
            .map(|index| {
                format!(
                    "raw runner fixture note {index} https://example.com/runner nostr:note1runnerfixture"
                )
            })
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
        let event_ids = events.iter().map(|event| event_id(event)).collect();
        Self {
            temp,
            corpus_path,
            event_ids,
            contents,
        }
    }

    fn config(&self, session_path: std::path::PathBuf) -> AdaptiveLearningRunnerConfig {
        AdaptiveLearningRunnerConfig {
            corpus_path: self.corpus_path.clone(),
            corpus_identity: "fixture-corpus-v1".to_owned(),
            session_path,
            compact_settings: CompactLearningSettings::new(
                VERSION,
                0.5,
                1.0,
                2.0,
                ScaleLevel::Mass64,
            )
            .expect("compact settings"),
            rbf_settings: RbfLearningSettings::new(VERSION, 0.5, 1.0, 2.0).expect("RBF settings"),
            b16: B16Boundary::new(VERSION, 0.0).expect("B16"),
            seeds: self.event_ids[..5]
                .iter()
                .copied()
                .map(|event_id| AdaptiveLearningSeed::new(event_id, 7).expect("positive seed"))
                .collect(),
        }
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
    matrix_passes: usize,
    vector_lookups: usize,
}

struct FailOnceOracle {
    inner: FixtureOracle,
    fail_next_wave: bool,
}

impl FailOnceOracle {
    fn new(event_ids: Vec<EventId>) -> Self {
        Self {
            inner: FixtureOracle::new(event_ids),
            fail_next_wave: true,
        }
    }
}

impl CandidateOrderOracle for FailOnceOracle {
    fn representation_version(&self) -> &str {
        self.inner.representation_version()
    }

    fn similar_notes_wave(
        &mut self,
        requests: &[SimilarNotesRequest],
        representation_version: &str,
    ) -> SnapshotResult<SimilarNotesWaveResponse> {
        if self.fail_next_wave {
            self.fail_next_wave = false;
            return Err(SnapshotError::Invariant(
                "injected transient Oracle failure".to_owned(),
            ));
        }
        self.inner
            .similar_notes_wave(requests, representation_version)
    }

    fn vectors_for_notes(
        &mut self,
        note_ids: &[EventId],
        representation_version: &str,
    ) -> SnapshotResult<VectorsForNotesResponse> {
        self.inner
            .vectors_for_notes(note_ids, representation_version)
    }
}

impl FixtureOracle {
    fn new(event_ids: Vec<EventId>) -> Self {
        Self {
            event_ids,
            responses: BTreeMap::new(),
            matrix_passes: 0,
            vector_lookups: 0,
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
                .take(1_024)
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
        if !missing.is_empty() {
            self.matrix_passes += 1;
            for event_id in missing.iter().copied() {
                let response = self.response(event_id);
                self.responses.insert(event_id, response);
            }
        }
        Ok(SimilarNotesWaveResponse {
            responses: requests
                .iter()
                .map(|request| self.responses[&request.note_id].clone())
                .collect(),
            metrics: SimilarNotesWaveMetrics {
                source_loading_ns: 11,
                query_encoding_ns: 12,
                matrix_scan_ns: 13,
                result_merge_ns: 14,
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
        self.vector_lookups += 1;
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

fn read_session(path: &std::path::Path) -> serde_json::Value {
    serde_json::from_reader(std::fs::File::open(path).expect("open durable session"))
        .expect("decode durable session")
}

fn value_event_id(value: &serde_json::Value) -> EventId {
    let bytes = value.as_array().expect("event ID byte array");
    let mut event_id = [0_u8; 32];
    for (output, value) in event_id.iter_mut().zip(bytes) {
        *output = value.as_u64().expect("event ID byte") as u8;
    }
    event_id
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
        let txn = Transaction::new(ndb).expect("read transaction");
        let all = Filter::new().build();
        let count = ndb
            .fold(&txn, &[all], 0_usize, |count, _| count + 1)
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
        .sign(&[9_u8; 32])
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
