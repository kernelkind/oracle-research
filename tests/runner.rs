use std::collections::BTreeMap;

use oracle_mvp::event::EventId;
use oracle_mvp::oracle::{Oracle, OracleCandidate, OracleResponse, OracleVersions};
use oracle_mvp::runner::{ExperimentRunner, ExperimentState, WorthJudgment};
use oracle_mvp::snapshot::{Error, Result};

#[test]
fn private_state_keeps_feedback_controls_and_sources_separate() {
    let mut oracle = RecordingOracle::default()
        .with_text(
            "distributed systems",
            response(&[(id(1), 0.9), (id(2), 0.8)]),
        )
        .with_text("ceramics", response(&[(id(3), 0.7)]));
    let mut runner = ExperimentRunner::new();

    let systems = runner
        .bootstrap(&mut oracle, "distributed systems".to_owned(), 10)
        .expect("systems bootstrap")
        .interest_id;
    let ceramics = runner
        .bootstrap(&mut oracle, "ceramics".to_owned(), 10)
        .expect("ceramics bootstrap")
        .interest_id;
    assert_eq!(runner.state().current_interest(), Some(ceramics));
    assert!(runner.state().seen().contains(&id(1)));
    assert!(runner.state().seen().contains(&id(2)));
    assert!(runner.state().seen().contains(&id(3)));

    runner
        .select_positive_source(systems, id(1))
        .expect("select systems source");
    runner
        .select_positive_source(ceramics, id(3))
        .expect("select ceramics source");
    let error = runner
        .select_positive_source(systems, id(9))
        .expect_err("non-onboarding source is rejected");
    assert!(error.to_string().contains("onboarding"));

    runner.record_worth(id(4), WorthJudgment::WorthSeeing);
    runner
        .record_recommendation_control(ceramics, "temporarily prefer glazing".to_owned())
        .expect("record recommendation control");
    assert_eq!(
        runner.state().worth_judgment(id(4)),
        Some(WorthJudgment::WorthSeeing)
    );
    assert!(
        !runner
            .state()
            .interest(ceramics)
            .expect("ceramics interest")
            .positive_sources()
            .contains(&id(4))
    );
    assert_eq!(runner.state().recommendation_controls().len(), 1);
    assert_eq!(
        runner.state().recommendation_controls()[0].instruction(),
        "temporarily prefer glazing"
    );

    let json = serde_json::to_vec(runner.state()).expect("serialize private state");
    let state: ExperimentState = serde_json::from_slice(&json).expect("deserialize private state");
    let restored = ExperimentRunner::restore(state).expect("restore valid private state");
    assert_eq!(restored.state(), runner.state());
}

#[test]
fn runner_queries_each_source_filters_locally_and_orders_without_score_fusion() {
    let systems_sources = response(&[(id(10), 0.9), (id(11), 0.8)]);
    let ceramics_sources = response(&[(id(12), 0.7)]);
    let mut setup_oracle = RecordingOracle::default()
        .with_text("distributed systems", systems_sources)
        .with_text("ceramics", ceramics_sources)
        .with_note(
            id(10),
            response(&[
                (id(12), 0.99),
                (id(20), 0.90),
                (id(30), 0.80),
                (id(21), 0.70),
                (id(26), 0.60),
            ]),
        )
        .with_note(id(11), response(&[(id(22), 0.95), (id(23), 0.85)]))
        .with_note(
            id(12),
            response(&[
                (id(24), 0.96),
                (id(30), 0.81),
                (id(25), 0.71),
                (id(27), 0.61),
            ]),
        );
    let mut runner = ExperimentRunner::new();
    let systems = runner
        .bootstrap(&mut setup_oracle, "distributed systems".to_owned(), 10)
        .expect("systems bootstrap")
        .interest_id;
    let ceramics = runner
        .bootstrap(&mut setup_oracle, "ceramics".to_owned(), 10)
        .expect("ceramics bootstrap")
        .interest_id;
    runner
        .select_positive_source(systems, id(10))
        .expect("first systems source");
    runner
        .select_positive_source(systems, id(11))
        .expect("second systems source");
    runner
        .select_positive_source(ceramics, id(12))
        .expect("ceramics source");
    runner
        .set_current_interest(systems)
        .expect("set current systems interest");
    runner.record_worth(id(21), WorthJudgment::NotWorthSeeing);
    runner.mark_seen(id(25));
    runner.record_worth(id(99), WorthJudgment::WorthSeeing);

    let serialized = serde_json::to_vec(runner.state()).expect("serialize runner state");
    let restored_state = serde_json::from_slice(&serialized).expect("deserialize runner state");
    let restored = ExperimentRunner::restore(restored_state).expect("restore runner");
    let mut first_oracle = setup_oracle.for_recommendations();
    let mut second_oracle = setup_oracle.for_recommendations();
    let first = runner
        .recommend(&mut first_oracle, 10)
        .expect("first local recommendation order");
    let second = restored
        .recommend(&mut second_oracle, 10)
        .expect("reproduced local recommendation order");
    assert_eq!(first, second);
    assert_eq!(first_oracle.calls, second_oracle.calls);
    assert_eq!(
        first_oracle.calls,
        vec![
            Call::Note(id(10), 10),
            Call::Note(id(11), 10),
            Call::Note(id(12), 10)
        ]
    );

    assert_eq!(
        first
            .iter()
            .map(|candidate| candidate.event_id)
            .collect::<Vec<_>>(),
        vec![id(20), id(24), id(22), id(30), id(26), id(27), id(23)]
    );
    assert_eq!(
        first
            .iter()
            .map(|candidate| candidate.local_rank)
            .collect::<Vec<_>>(),
        vec![1, 2, 3, 4, 5, 6, 7]
    );
    assert!(first.iter().all(|candidate| candidate.event_id != id(12)));
    assert!(first.iter().all(|candidate| candidate.event_id != id(21)));
    assert!(first.iter().all(|candidate| candidate.event_id != id(25)));
    assert!(first.iter().any(|candidate| candidate.event_id == id(26)));

    let shared = first
        .iter()
        .find(|candidate| candidate.event_id == id(30))
        .expect("shared candidate");
    assert_eq!(shared.evidence.len(), 2);
    assert_eq!(shared.evidence[0].source_note_id, id(10));
    assert_eq!(shared.evidence[0].source_rank, 3);
    assert_eq!(shared.evidence[0].cosine_score, 0.80);
    assert_eq!(shared.evidence[1].source_note_id, id(12));
    assert_eq!(shared.evidence[1].source_rank, 2);
    assert_eq!(shared.evidence[1].cosine_score, 0.81);
    assert_eq!(shared.evidence[0].versions, versions());
}

#[test]
fn runner_rejects_mixed_oracle_versions() {
    let mut setup = RecordingOracle::default()
        .with_text("first", response(&[(id(1), 0.9)]))
        .with_text("second", response(&[(id(2), 0.8)]));
    let mut runner = ExperimentRunner::new();
    let first = runner
        .bootstrap(&mut setup, "first".to_owned(), 5)
        .expect("first bootstrap")
        .interest_id;
    let second = runner
        .bootstrap(&mut setup, "second".to_owned(), 5)
        .expect("second bootstrap")
        .interest_id;
    runner
        .select_positive_source(first, id(1))
        .expect("first source");
    runner
        .select_positive_source(second, id(2))
        .expect("second source");

    let mut mismatched = response(&[(id(4), 0.7)]);
    mismatched.versions.corpus = "other-corpus".to_owned();
    let mut oracle = RecordingOracle::default()
        .with_note(id(1), response(&[(id(3), 0.8)]))
        .with_note(id(2), mismatched);
    let error = runner
        .recommend(&mut oracle, 5)
        .expect_err("mixed versions are rejected");
    assert!(error.to_string().contains("versions"));
}

#[derive(Clone, Debug, Eq, PartialEq)]
enum Call {
    Text(String, usize),
    Note(EventId, usize),
}

#[derive(Clone, Default)]
struct RecordingOracle {
    text: BTreeMap<String, OracleResponse>,
    notes: BTreeMap<EventId, OracleResponse>,
    calls: Vec<Call>,
}

impl RecordingOracle {
    fn with_text(mut self, text: &str, response: OracleResponse) -> Self {
        self.text.insert(text.to_owned(), response);
        self
    }

    fn with_note(mut self, note_id: EventId, response: OracleResponse) -> Self {
        self.notes.insert(note_id, response);
        self
    }

    fn for_recommendations(&self) -> Self {
        Self {
            text: BTreeMap::new(),
            notes: self.notes.clone(),
            calls: Vec::new(),
        }
    }
}

impl Oracle for RecordingOracle {
    fn search_text(&mut self, text: &str, candidate_depth: usize) -> Result<OracleResponse> {
        self.calls
            .push(Call::Text(text.to_owned(), candidate_depth));
        self.text
            .get(text)
            .cloned()
            .ok_or_else(|| Error::InvalidQuery(format!("no text fixture for `{text}`")))
    }

    fn similar_notes(
        &mut self,
        note_id: EventId,
        candidate_depth: usize,
    ) -> Result<OracleResponse> {
        self.calls.push(Call::Note(note_id, candidate_depth));
        self.notes
            .get(&note_id)
            .cloned()
            .ok_or_else(|| Error::EventNotFound(note_id.to_string()))
    }
}

fn response(candidates: &[(EventId, f32)]) -> OracleResponse {
    OracleResponse {
        versions: versions(),
        candidates: candidates
            .iter()
            .enumerate()
            .map(|(index, (event_id, cosine_score))| OracleCandidate {
                event_id: *event_id,
                rank: u64::try_from(index + 1).expect("fixture rank"),
                cosine_score: *cosine_score,
            })
            .collect(),
    }
}

fn versions() -> OracleVersions {
    OracleVersions {
        corpus: "fixture-corpus".to_owned(),
        retriever: "fixture-retriever".to_owned(),
    }
}

fn id(byte: u8) -> EventId {
    EventId::from([byte; 32])
}
