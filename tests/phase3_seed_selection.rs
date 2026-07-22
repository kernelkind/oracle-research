use std::collections::{BTreeMap, VecDeque};
use std::fs;
use std::io;
use std::os::unix::fs::PermissionsExt;
use std::path::Path;
use std::thread;
use std::time::{Duration, Instant};

use nostrdb::{Config, Filter, Ndb, NoteBuilder, Transaction};
use oracle_mvp::candidate_order::CandidateOrderOracle;
use oracle_mvp::evaluator::{
    CompletionView, EvaluatorDecision, EvaluatorSubmission, EvaluatorUi, RatingOutcome, RatingView,
    RecoveryOutcome, RecoveryView, RestOutcome, RestView,
};
use oracle_mvp::fp32_oracle::{
    Fp32Candidate, SimilarNotesRequest, SimilarNotesResponse, SimilarNotesWaveMetrics,
    SimilarNotesWaveResponse, VectorsForNotesResponse,
};
use oracle_mvp::phase3_seed_selection::{
    Phase3SeedSelectionConfig, Phase3SeedSelectionOutcome, ScreeningDecision,
    run_phase3_seed_selection,
};
use oracle_mvp::representation::EventId;

const VERSION: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const SECRET_KEY: [u8; 32] = [17; 32];

#[test]
fn selector_uses_maximum_marginal_coverage_and_only_positive_ratings_become_seeds() {
    let fixture = Fixture::new(9);
    let mut oracle = FakeOracle::new(&fixture.event_ids);
    oracle.set_neighbors(fixture.event_ids[4], range_ids(10_000, 1_024));
    oracle.set_neighbors(fixture.event_ids[5], range_ids(10_001, 1_024));
    oracle.set_neighbors(fixture.event_ids[6], range_ids(20_000, 1_024));
    let mut evaluator = ScriptedEvaluator::ratings([1, 2, 3, 4, 5, 6, 7, 5, 7]);

    let outcome = run_phase3_seed_selection(&fixture.config, &mut oracle, &mut evaluator)
        .expect("complete seed selection");
    let Phase3SeedSelectionOutcome::Complete(handoff) = outcome else {
        panic!("selection unexpectedly paused");
    };

    assert_eq!(evaluator.presented.len(), 9);
    assert_eq!(&evaluator.presented[..5], &fixture.event_ids[..5]);
    assert_eq!(
        evaluator.presented[5], fixture.event_ids[6],
        "the disjoint response must outrank the nearly duplicate response"
    );
    assert_eq!(handoff.seeds().len(), 5);
    assert_eq!(
        handoff
            .seeds()
            .iter()
            .map(|seed| seed.rating())
            .collect::<Vec<_>>(),
        vec![5, 6, 7, 5, 7]
    );
    assert!(
        handoff.presentations()[..4]
            .iter()
            .all(|presentation| matches!(
                presentation.decision(),
                ScreeningDecision::Rating(1..=4)
            ))
    );
    assert_eq!(
        handoff
            .initial_presentations()
            .expect("validated initial presentations")
            .len(),
        4
    );
}

#[test]
fn selector_has_no_twenty_presentation_cap_and_stops_at_the_fifth_positive() {
    let fixture = Fixture::new(27);
    let mut oracle = FakeOracle::new(&fixture.event_ids);
    let mut ratings = vec![1; 21];
    ratings.extend([5, 5, 5, 5, 5, 7]);
    let mut evaluator = ScriptedEvaluator::ratings(ratings);

    let outcome = run_phase3_seed_selection(&fixture.config, &mut oracle, &mut evaluator)
        .expect("complete seed selection");
    let Phase3SeedSelectionOutcome::Complete(handoff) = outcome else {
        panic!("selection unexpectedly paused");
    };

    assert_eq!(evaluator.presented.len(), 26);
    assert_eq!(
        evaluator.presented,
        fixture.event_ids[..26],
        "equal marginal coverage must preserve curated input order"
    );
    assert_eq!(evaluator.rests, vec![20]);
    assert_eq!(handoff.presentations().len(), 26);
    assert_eq!(handoff.seeds().len(), 5);
}

#[test]
fn selector_bounds_oracle_work_to_forty_sources_per_wave() {
    let fixture = Fixture::new(85);
    let mut oracle = FakeOracle::new(&fixture.event_ids);
    let mut evaluator = ScriptedEvaluator::ratings([5, 5, 5, 5, 5]);

    let outcome = run_phase3_seed_selection(&fixture.config, &mut oracle, &mut evaluator)
        .expect("complete bounded-wave seed selection");

    assert!(matches!(outcome, Phase3SeedSelectionOutcome::Complete(_)));
    assert_eq!(oracle.wave_sizes, vec![40, 40, 5]);
}

#[test]
fn selector_resumes_pending_and_stored_decisions_without_repeating_a_source() {
    let fixture = Fixture::new(8);
    let mut first_oracle = FakeOracle::new(&fixture.event_ids);
    let mut first = ScriptedEvaluator::pause_on_first_presentation();
    let paused = run_phase3_seed_selection(&fixture.config, &mut first_oracle, &mut first)
        .expect("pause seed selection");
    assert!(matches!(paused, Phase3SeedSelectionOutcome::Paused));
    assert_eq!(first.presented, vec![fixture.event_ids[0]]);

    let mut resumed_oracle = FakeOracle::new(&fixture.event_ids);
    let mut resumed = ScriptedEvaluator::recover_then_rate(
        EvaluatorSubmission::new(EvaluatorDecision::Rating(5), false),
        [5, 5, 5, 5],
    );
    let resumed_outcome =
        run_phase3_seed_selection(&fixture.config, &mut resumed_oracle, &mut resumed)
            .expect("resume seed selection");
    assert!(matches!(
        resumed_outcome,
        Phase3SeedSelectionOutcome::Complete(_)
    ));
    assert_eq!(resumed.recoveries, 1);
    assert!(!resumed.presented.contains(&fixture.event_ids[0]));

    let fixture = Fixture::new(7);
    let mut oracle = FakeOracle::new(&fixture.event_ids);
    let mut pause_after = ScriptedEvaluator::submissions([
        EvaluatorSubmission::new(EvaluatorDecision::Rating(5), false),
        EvaluatorSubmission::new(EvaluatorDecision::Rating(1), true),
    ]);
    let paused = run_phase3_seed_selection(&fixture.config, &mut oracle, &mut pause_after)
        .expect("store then pause");
    assert!(matches!(paused, Phase3SeedSelectionOutcome::Paused));
    let already_presented = pause_after.presented.clone();

    let mut replay_oracle = FakeOracle::new(&fixture.event_ids).fail_on_query();
    let mut finish = ScriptedEvaluator::ratings([5, 5, 5, 5]);
    let completed = run_phase3_seed_selection(&fixture.config, &mut replay_oracle, &mut finish)
        .expect("resume entirely from durable response cache");
    assert!(matches!(completed, Phase3SeedSelectionOutcome::Complete(_)));
    assert!(
        finish
            .presented
            .iter()
            .all(|event_id| !already_presented.contains(event_id))
    );
}

#[test]
fn selector_fails_closed_when_the_curated_pool_is_exhausted() {
    let fixture = Fixture::new(6);
    let mut oracle = FakeOracle::new(&fixture.event_ids);
    let mut evaluator = ScriptedEvaluator::ratings([1, 2, 3, 4, 5, 1]);

    let error = run_phase3_seed_selection(&fixture.config, &mut oracle, &mut evaluator)
        .expect_err("an exhausted pool cannot produce a handoff");
    assert!(error.to_string().contains("exhausted"));
    assert!(!fixture.config.handoff_path.exists());

    let mut no_query = FakeOracle::new(&fixture.event_ids).fail_on_query();
    let mut no_ui = ScriptedEvaluator::fail_on_use();
    let replay_error = run_phase3_seed_selection(&fixture.config, &mut no_query, &mut no_ui)
        .expect_err("terminal exhaustion must replay without more work");
    assert_eq!(replay_error.to_string(), error.to_string());
}

#[test]
fn selector_recovers_interrupted_create_once_writes() {
    let fixture = Fixture::new(6);
    let cache_dir = fixture
        .config
        .session_path
        .parent()
        .expect("session parent")
        .join(".selection-session.json.oracle-responses");
    fs::create_dir(&cache_dir).expect("create response cache directory");
    let response_name = format!("response-{}.json", hex(fixture.event_ids[0]));
    let response_temporary = cache_dir.join(format!(".{response_name}.tmp"));
    fs::write(&response_temporary, b"interrupted response write")
        .expect("leave interrupted response write");
    let handoff_temporary = fixture
        .config
        .handoff_path
        .with_file_name(".selection-handoff.json.tmp");
    fs::write(&handoff_temporary, b"interrupted handoff write")
        .expect("leave interrupted handoff write");

    let mut oracle = FakeOracle::new(&fixture.event_ids);
    let mut evaluator = ScriptedEvaluator::ratings([5, 5, 5, 5, 5]);
    let outcome = run_phase3_seed_selection(&fixture.config, &mut oracle, &mut evaluator)
        .expect("recover interrupted writes and complete");

    assert!(matches!(outcome, Phase3SeedSelectionOutcome::Complete(_)));
    assert!(!response_temporary.exists());
    assert!(!handoff_temporary.exists());
    assert_eq!(
        fs::metadata(&fixture.config.session_path)
            .expect("session metadata")
            .permissions()
            .mode()
            & 0o777,
        0o600
    );
    assert_eq!(
        fs::metadata(&fixture.config.handoff_path)
            .expect("handoff metadata")
            .permissions()
            .mode()
            & 0o777,
        0o600
    );
    assert_eq!(
        fs::metadata(&cache_dir)
            .expect("cache metadata")
            .permissions()
            .mode()
            & 0o777,
        0o700
    );
    for entry in fs::read_dir(&cache_dir).expect("read response cache") {
        assert_eq!(
            entry
                .expect("cache entry")
                .metadata()
                .expect("cache entry metadata")
                .permissions()
                .mode()
                & 0o777,
            0o600
        );
    }

    let mut no_query = FakeOracle::new(&fixture.event_ids).fail_on_query();
    let mut completion_only = ScriptedEvaluator::ratings([]);
    let replay = run_phase3_seed_selection(&fixture.config, &mut no_query, &mut completion_only)
        .expect("replay completed seed selection without more work");
    assert!(matches!(replay, Phase3SeedSelectionOutcome::Complete(_)));
    assert!(completion_only.presented.is_empty());
}

struct Fixture {
    _temp: tempfile::TempDir,
    event_ids: Vec<EventId>,
    config: Phase3SeedSelectionConfig,
}

impl Fixture {
    fn new(note_count: usize) -> Self {
        let temp = tempfile::tempdir().expect("temporary selector workspace");
        let corpus_path = temp.path().join("corpus.ndb");
        let event_ids = build_corpus(&corpus_path, note_count);
        let config = Phase3SeedSelectionConfig {
            corpus_path,
            corpus_identity: "sha256:fixture-corpus".to_owned(),
            session_path: temp.path().join("selection-session.json"),
            handoff_path: temp.path().join("selection-handoff.json"),
            representation_version: VERSION.to_owned(),
            candidate_event_ids: event_ids.clone(),
        };
        Self {
            _temp: temp,
            event_ids,
            config,
        }
    }
}

fn build_corpus(path: &Path, note_count: usize) -> Vec<EventId> {
    let ndb = Ndb::new(
        path.to_str().expect("UTF-8 fixture path"),
        &Config::new().set_mapsize(2 * 1_024 * 1_024 * 1_024),
    )
    .expect("open fixture NostrDB");
    let mut event_ids = Vec::new();
    for index in 0..note_count {
        let note = NoteBuilder::new()
            .kind(1)
            .content(&format!("seed candidate {index}"))
            .created_at(1_720_000_000 + index as u64)
            .sign(&SECRET_KEY)
            .build()
            .expect("build candidate note");
        let event = note.json().expect("encode candidate note");
        event_ids.push(*note.id());
        ndb.process_event(&event).expect("ingest candidate note");
    }
    let deadline = Instant::now() + Duration::from_secs(10);
    loop {
        let transaction = Transaction::new(&ndb).expect("open fixture transaction");
        let count = ndb
            .fold(
                &transaction,
                &[Filter::new().build()],
                0_usize,
                |count, _| count + 1,
            )
            .expect("count candidate notes");
        if count == note_count {
            break;
        }
        assert!(Instant::now() < deadline, "candidate ingestion timed out");
        thread::sleep(Duration::from_millis(10));
    }
    event_ids
}

struct FakeOracle {
    event_ids: Vec<EventId>,
    neighbors: BTreeMap<EventId, Vec<EventId>>,
    fail_on_query: bool,
    wave_sizes: Vec<usize>,
}

impl FakeOracle {
    fn new(event_ids: &[EventId]) -> Self {
        Self {
            event_ids: event_ids.to_vec(),
            neighbors: BTreeMap::new(),
            fail_on_query: false,
            wave_sizes: Vec::new(),
        }
    }

    fn set_neighbors(&mut self, event_id: EventId, neighbors: Vec<EventId>) {
        self.neighbors.insert(event_id, neighbors);
    }

    fn fail_on_query(mut self) -> Self {
        self.fail_on_query = true;
        self
    }

    fn response(&self, request: SimilarNotesRequest) -> SimilarNotesResponse {
        let fallback_index = self
            .event_ids
            .iter()
            .position(|event_id| *event_id == request.note_id)
            .expect("known source");
        let candidates = self
            .neighbors
            .get(&request.note_id)
            .cloned()
            .unwrap_or_else(|| range_ids(100_000 + fallback_index as u64 * 2_000, 1_024));
        SimilarNotesResponse {
            representation_version: VERSION.to_owned(),
            represented_rows: 10_000,
            total_rows: 10_000,
            complete: true,
            candidates: candidates
                .into_iter()
                .enumerate()
                .map(|(index, event_id)| Fp32Candidate {
                    event_id,
                    rank: index + 1,
                    cosine_score: 1.0 - index as f32 / 2_048.0,
                })
                .collect(),
        }
    }
}

impl CandidateOrderOracle for FakeOracle {
    fn representation_version(&self) -> &str {
        VERSION
    }

    fn similar_notes_wave(
        &mut self,
        requests: &[SimilarNotesRequest],
        _representation_version: &str,
    ) -> oracle_mvp::snapshot::Result<SimilarNotesWaveResponse> {
        assert!(!self.fail_on_query, "unexpected Oracle query after resume");
        self.wave_sizes.push(requests.len());
        Ok(SimilarNotesWaveResponse {
            responses: requests
                .iter()
                .copied()
                .map(|request| self.response(request))
                .collect(),
            metrics: SimilarNotesWaveMetrics {
                source_loading_ns: 1,
                query_encoding_ns: 1,
                matrix_scan_ns: 1,
                result_merge_ns: 1,
                encoded_queries: requests.len() as u64,
                cache_hits: 0,
                matrix_passes: 1,
                scanned_rows: 10_000,
                scan_block_rows: 1_024,
            },
        })
    }

    fn vectors_for_notes(
        &mut self,
        _note_ids: &[EventId],
        _representation_version: &str,
    ) -> oracle_mvp::snapshot::Result<VectorsForNotesResponse> {
        panic!("seed selection must not request document vectors")
    }
}

fn range_ids(start: u64, count: usize) -> Vec<EventId> {
    (0..count)
        .map(|offset| event_id(start + offset as u64))
        .collect()
}

fn event_id(value: u64) -> EventId {
    let mut event_id = [0_u8; 32];
    event_id[24..].copy_from_slice(&value.to_be_bytes());
    event_id
}

fn hex(event_id: EventId) -> String {
    event_id.iter().map(|byte| format!("{byte:02x}")).collect()
}

struct ScriptedEvaluator {
    outcomes: VecDeque<RatingOutcome>,
    recovery: Option<RecoveryOutcome>,
    presented: Vec<EventId>,
    recoveries: usize,
    rests: Vec<usize>,
    fail_on_use: bool,
}

impl ScriptedEvaluator {
    fn ratings(ratings: impl IntoIterator<Item = u8>) -> Self {
        Self::submissions(
            ratings
                .into_iter()
                .map(|rating| EvaluatorSubmission::new(EvaluatorDecision::Rating(rating), false)),
        )
    }

    fn submissions(submissions: impl IntoIterator<Item = EvaluatorSubmission>) -> Self {
        Self {
            outcomes: submissions
                .into_iter()
                .map(RatingOutcome::Submitted)
                .collect(),
            recovery: None,
            presented: Vec::new(),
            recoveries: 0,
            rests: Vec::new(),
            fail_on_use: false,
        }
    }

    fn pause_on_first_presentation() -> Self {
        Self {
            outcomes: VecDeque::from([RatingOutcome::Paused]),
            recovery: None,
            presented: Vec::new(),
            recoveries: 0,
            rests: Vec::new(),
            fail_on_use: false,
        }
    }

    fn recover_then_rate(
        recovery: EvaluatorSubmission,
        ratings: impl IntoIterator<Item = u8>,
    ) -> Self {
        let mut evaluator = Self::ratings(ratings);
        evaluator.recovery = Some(RecoveryOutcome::Submitted(recovery));
        evaluator
    }

    fn fail_on_use() -> Self {
        let mut evaluator = Self::ratings([]);
        evaluator.fail_on_use = true;
        evaluator
    }
}

impl EvaluatorUi for ScriptedEvaluator {
    fn rate(&mut self, view: RatingView<'_>) -> io::Result<RatingOutcome> {
        assert!(!self.fail_on_use, "unexpected evaluator use");
        let index = view
            .note()
            .strip_prefix("seed candidate ")
            .expect("candidate content")
            .parse::<usize>()
            .expect("candidate index");
        self.presented.push(event_id_from_candidate_index(index));
        Ok(self.outcomes.pop_front().expect("scripted rating outcome"))
    }

    fn recover(&mut self, _view: RecoveryView) -> io::Result<RecoveryOutcome> {
        assert!(!self.fail_on_use, "unexpected evaluator use");
        self.recoveries += 1;
        Ok(self.recovery.take().expect("scripted recovery outcome"))
    }

    fn rest(&mut self, view: RestView) -> io::Result<RestOutcome> {
        assert!(!self.fail_on_use, "unexpected evaluator use");
        self.rests.push(view.presentations_stored());
        Ok(RestOutcome::Continue)
    }

    fn preparing(&mut self) -> io::Result<()> {
        assert!(!self.fail_on_use, "unexpected evaluator use");
        Ok(())
    }

    fn complete(&mut self, _view: CompletionView) -> io::Result<()> {
        assert!(!self.fail_on_use, "unexpected evaluator use");
        Ok(())
    }
}

fn event_id_from_candidate_index(index: usize) -> EventId {
    let note = NoteBuilder::new()
        .kind(1)
        .content(&format!("seed candidate {index}"))
        .created_at(1_720_000_000 + index as u64)
        .sign(&SECRET_KEY)
        .build()
        .expect("rebuild candidate note");
    *note.id()
}
