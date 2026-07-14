use std::collections::BTreeMap;

use oracle_mvp::event::EventId;
use oracle_mvp::oracle::{
    Oracle, OracleCandidate, OracleProvenance, OracleResponse, OracleVersions,
};
use oracle_mvp::runner::{ExperimentRunner, ExperimentState, RecommendationControl, WorthJudgment};
use oracle_mvp::snapshot::{EligibilityRules, Error, Result};

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
        .apply_recommendation_control(ceramics, RecommendationControl::DisableInterest)
        .expect("disable ceramics recommendations");
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
        runner.state().recommendation_controls()[0].control(),
        RecommendationControl::DisableInterest
    );
    assert!(!runner.state().interest_is_enabled(ceramics).unwrap());
    assert!(runner.state().interest_is_enabled(systems).unwrap());

    let mut disabled_oracle = setup_recommendation_oracle();
    let disabled = runner
        .recommend(&mut disabled_oracle, 10)
        .expect("recommend with ceramics disabled");
    assert_eq!(disabled_oracle.calls, vec![Call::Note(id(1), 10)]);
    assert_eq!(
        disabled
            .iter()
            .map(|candidate| candidate.event_id)
            .collect::<Vec<_>>(),
        vec![id(10)]
    );

    runner
        .apply_recommendation_control(ceramics, RecommendationControl::EnableInterest)
        .expect("enable ceramics recommendations");
    assert!(runner.state().interest_is_enabled(ceramics).unwrap());
    assert_eq!(runner.state().recommendation_controls().len(), 2);

    let json = serde_json::to_vec(runner.state()).expect("serialize private state");
    let state: ExperimentState = serde_json::from_slice(&json).expect("deserialize private state");
    let restored = ExperimentRunner::restore(state).expect("restore valid private state");
    assert_eq!(restored.state(), runner.state());
}

#[test]
fn runner_ranks_within_each_interest_then_preserves_opportunity_across_interests() {
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
                (id(31), 0.70),
                (id(21), 0.60),
            ]),
        )
        .with_note(
            id(11),
            response(&[(id(31), 0.95), (id(22), 0.85), (id(23), 0.75)]),
        )
        .with_note(
            id(12),
            response(&[(id(30), 0.99), (id(24), 0.96), (id(25), 0.71)]),
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
        vec![id(31), id(30), id(20), id(24), id(22), id(23)]
    );
    assert_eq!(
        first
            .iter()
            .map(|candidate| candidate.local_rank)
            .collect::<Vec<_>>(),
        vec![1, 2, 3, 4, 5, 6]
    );
    assert!(first.iter().all(|candidate| candidate.event_id != id(12)));
    assert!(first.iter().all(|candidate| candidate.event_id != id(21)));
    assert!(first.iter().all(|candidate| candidate.event_id != id(25)));
    assert!(first.iter().any(|candidate| candidate.event_id == id(23)));

    let supported_within_systems = first
        .iter()
        .find(|candidate| candidate.event_id == id(31))
        .expect("candidate supported by two systems sources");
    assert_eq!(supported_within_systems.evidence.len(), 2);
    assert!(
        supported_within_systems
            .evidence
            .iter()
            .all(|evidence| evidence.interest_id == systems)
    );

    let shared = first
        .iter()
        .find(|candidate| candidate.event_id == id(30))
        .expect("shared candidate");
    assert_eq!(shared.evidence.len(), 2);
    assert_eq!(shared.evidence[0].source_note_id, id(10));
    assert_eq!(shared.evidence[0].source_rank, 3);
    assert_eq!(shared.evidence[0].cosine_score, 0.80);
    assert_eq!(shared.evidence[1].source_note_id, id(12));
    assert_eq!(shared.evidence[1].source_rank, 1);
    assert_eq!(shared.evidence[1].cosine_score, 0.99);
    assert_eq!(shared.evidence[0].versions, versions());
    assert_eq!(shared.evidence[0].provenance.candidate_depth, 10);
    assert_eq!(shared.evidence[0].provenance, shared.evidence[1].provenance);
}

#[test]
fn worth_judgments_do_not_change_interest_controls() {
    let mut oracle = RecordingOracle::default().with_text("systems", response(&[(id(1), 0.9)]));
    let mut runner = ExperimentRunner::new();
    let systems = runner
        .bootstrap(&mut oracle, "systems".to_owned(), 10)
        .expect("bootstrap systems")
        .interest_id;

    runner.record_worth(id(40), WorthJudgment::NotWorthSeeing);
    runner.record_worth(id(41), WorthJudgment::WorthSeeing);

    assert!(runner.state().interest_is_enabled(systems).unwrap());
    assert!(runner.state().recommendation_controls().is_empty());
}

#[test]
fn restore_rejects_zero_as_the_next_interest_id() {
    let runner = ExperimentRunner::new();
    let mut value = serde_json::to_value(runner.state()).expect("serialize state");
    value["next_interest_id"] = serde_json::json!(0);
    let state = serde_json::from_value(value).expect("deserialize state");

    let error = match ExperimentRunner::restore(state) {
        Ok(_) => panic!("interest ID zero must remain reserved"),
        Err(error) => error,
    };
    assert!(error.to_string().contains("zero"));
}

#[test]
fn restore_rejects_an_invalid_oracle_rebind_target() {
    let mut oracle = RecordingOracle::default().with_text("systems", response(&[(id(1), 0.9)]));
    let mut runner = ExperimentRunner::new();
    runner
        .bootstrap(&mut oracle, "systems".to_owned(), 5)
        .expect("bootstrap systems");
    let mut value = serde_json::to_value(runner.state()).expect("serialize state");
    let interest = value["interests"]["1"].clone();
    let from_versions = interest["current_versions"].clone();
    let from_provenance = interest["current_provenance"].clone();
    let mut invalid_versions = from_versions.clone();
    invalid_versions["corpus"] = serde_json::json!("");
    let mut invalid_provenance = from_provenance.clone();
    invalid_provenance["candidate_depth"] = serde_json::json!(0);
    value["interests"]["1"]["current_versions"] = invalid_versions.clone();
    value["interests"]["1"]["current_provenance"] = invalid_provenance.clone();
    value["oracle_rebindings"] = serde_json::json!([{
        "interest_id": 1,
        "from_versions": from_versions,
        "from_provenance": from_provenance,
        "to_versions": invalid_versions,
        "to_provenance": invalid_provenance
    }]);
    let state = serde_json::from_value(value).expect("deserialize structurally valid state");

    let error = match ExperimentRunner::restore(state) {
        Ok(_) => panic!("invalid rebind target must be rejected"),
        Err(error) => error,
    };
    assert!(error.to_string().contains("invalid target identity"));
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

#[test]
fn runner_rejects_mixed_oracle_provenance() {
    let mut setup =
        RecordingOracle::default().with_text("systems", response(&[(id(1), 0.9), (id(2), 0.8)]));
    let mut runner = ExperimentRunner::new();
    let systems = runner
        .bootstrap(&mut setup, "systems".to_owned(), 5)
        .expect("bootstrap systems")
        .interest_id;
    runner
        .select_positive_source(systems, id(1))
        .expect("first source");
    runner
        .select_positive_source(systems, id(2))
        .expect("second source");

    let mut different_model = response(&[(id(4), 0.7)]);
    different_model.provenance.model_revision = "other-revision".to_owned();
    let mut oracle = RecordingOracle::default()
        .with_note(id(1), response(&[(id(3), 0.8)]))
        .with_note(id(2), different_model);

    let error = runner
        .recommend(&mut oracle, 5)
        .expect_err("mixed provenance is rejected");
    assert!(error.to_string().contains("provenance"));
}

#[test]
fn runner_rejects_oracle_identity_drift_from_bootstrap() {
    let mut setup = RecordingOracle::default().with_text("systems", response(&[(id(1), 0.9)]));
    let mut runner = ExperimentRunner::new();
    let systems = runner
        .bootstrap(&mut setup, "systems".to_owned(), 5)
        .expect("bootstrap systems")
        .interest_id;
    runner
        .select_positive_source(systems, id(1))
        .expect("positive source");

    let mut changed_versions = response(&[(id(3), 0.8)]);
    changed_versions.versions.corpus = "different-corpus".to_owned();
    let error = runner
        .recommend(
            &mut RecordingOracle::default().with_note(id(1), changed_versions),
            5,
        )
        .expect_err("recommendation cannot silently change corpus artifacts");
    assert!(error.to_string().contains("versions"));

    let mut changed_model = response(&[(id(3), 0.8)]);
    changed_model.provenance.model_revision = "different-model".to_owned();
    let error = runner
        .recommend(
            &mut RecordingOracle::default().with_note(id(1), changed_model),
            5,
        )
        .expect_err("recommendation cannot silently change model provenance");
    assert!(error.to_string().contains("authorized provenance"));
}

#[test]
fn later_bootstrap_rejects_identity_drift_without_mutating_state() {
    let mut setup = RecordingOracle::default().with_text("systems", response(&[(id(1), 0.9)]));
    let mut runner = ExperimentRunner::new();
    runner
        .bootstrap(&mut setup, "systems".to_owned(), 5)
        .expect("bootstrap systems");
    let before = runner.state().clone();

    let mut changed = response(&[(id(2), 0.8)]);
    changed.versions.corpus = "different-corpus".to_owned();
    let error = runner
        .bootstrap(
            &mut RecordingOracle::default().with_text("ceramics", changed),
            "ceramics".to_owned(),
            5,
        )
        .expect_err("later bootstrap cannot silently change oracle identity");
    assert!(matches!(error, Error::OracleVersionMismatch));
    assert_eq!(runner.state(), &before);
}

#[test]
fn explicit_oracle_rebind_preserves_local_state_and_allows_a_larger_stage() {
    let mut setup = RecordingOracle::default()
        .with_text("systems", response(&[(id(1), 0.9)]))
        .with_text("ceramics", response(&[(id(2), 0.9)]));
    let mut runner = ExperimentRunner::new();
    let systems = runner
        .bootstrap(&mut setup, "systems".to_owned(), 5)
        .expect("bootstrap systems")
        .interest_id;
    let ceramics = runner
        .bootstrap(&mut setup, "ceramics".to_owned(), 5)
        .expect("bootstrap ceramics")
        .interest_id;
    runner
        .select_positive_source(systems, id(1))
        .expect("positive source");
    runner
        .select_positive_source(ceramics, id(2))
        .expect("positive source");
    runner.record_worth(id(90), WorthJudgment::WorthSeeing);

    let expanded_systems = expanded_response(&[(id(3), 0.8)]);
    let expanded_ceramics = expanded_response(&[(id(4), 0.8)]);
    runner
        .rebind_oracle(
            &mut RecordingOracle::default()
                .with_note(id(1), expanded_systems.clone())
                .with_note(id(2), expanded_ceramics.clone()),
            5,
        )
        .expect("explicitly rebind to expanded corpus");

    assert_eq!(runner.state().oracle_rebindings().len(), 2);
    assert_eq!(
        runner.state().worth_judgment(id(90)),
        Some(WorthJudgment::WorthSeeing)
    );
    assert!(
        runner
            .state()
            .interest(systems)
            .expect("systems interest")
            .positive_sources()
            .contains(&id(1))
    );
    let candidates = runner
        .recommend(
            &mut RecordingOracle::default()
                .with_note(id(1), expanded_systems)
                .with_note(id(2), expanded_ceramics),
            5,
        )
        .expect("recommend after explicit rebind");
    assert_eq!(
        candidates
            .iter()
            .map(|candidate| candidate.event_id)
            .collect::<Vec<_>>(),
        vec![id(4), id(3)]
    );
}

#[test]
fn oracle_rebind_is_atomic_across_interests() {
    let mut setup = RecordingOracle::default()
        .with_text("systems", response(&[(id(1), 0.9)]))
        .with_text("ceramics", response(&[(id(2), 0.9)]));
    let mut runner = ExperimentRunner::new();
    let systems = runner
        .bootstrap(&mut setup, "systems".to_owned(), 5)
        .expect("bootstrap systems")
        .interest_id;
    let ceramics = runner
        .bootstrap(&mut setup, "ceramics".to_owned(), 5)
        .expect("bootstrap ceramics")
        .interest_id;
    runner
        .select_positive_source(systems, id(1))
        .expect("systems source");
    runner
        .select_positive_source(ceramics, id(2))
        .expect("ceramics source");
    let before = runner.state().clone();

    let error = runner
        .rebind_oracle(
            &mut RecordingOracle::default().with_note(id(1), expanded_response(&[(id(3), 0.8)])),
            5,
        )
        .expect_err("second interest cannot be verified");
    assert!(matches!(error, Error::EventNotFound(_)));
    assert_eq!(runner.state(), &before);
}

#[test]
fn local_order_uses_event_id_as_the_final_deterministic_tie_breaker() {
    let mut setup =
        RecordingOracle::default().with_text("systems", response(&[(id(1), 0.9), (id(2), 0.8)]));
    let mut runner = ExperimentRunner::new();
    let systems = runner
        .bootstrap(&mut setup, "systems".to_owned(), 5)
        .expect("bootstrap systems")
        .interest_id;
    runner
        .select_positive_source(systems, id(1))
        .expect("first source");
    runner
        .select_positive_source(systems, id(2))
        .expect("second source");

    let mut oracle = RecordingOracle::default()
        .with_note(id(1), response(&[(id(41), 0.8)]))
        .with_note(id(2), response(&[(id(40), 0.8)]));
    let candidates = runner.recommend(&mut oracle, 5).expect("recommendations");

    assert_eq!(
        candidates
            .iter()
            .map(|candidate| candidate.event_id)
            .collect::<Vec<_>>(),
        vec![id(40), id(41)]
    );
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
            .map(|mut response| {
                response.provenance.candidate_depth = candidate_depth as u64;
                response
            })
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
            .map(|mut response| {
                response.provenance.candidate_depth = candidate_depth as u64;
                response
            })
            .ok_or_else(|| Error::EventNotFound(note_id.to_string()))
    }
}

fn response(candidates: &[(EventId, f32)]) -> OracleResponse {
    OracleResponse {
        versions: versions(),
        provenance: provenance(),
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

fn expanded_response(candidates: &[(EventId, f32)]) -> OracleResponse {
    let mut response = response(candidates);
    response.versions.corpus = "expanded-corpus".to_owned();
    response.versions.retriever = "expanded-retriever".to_owned();
    response.provenance.corpus_stage_name = Some("expanded-stage".to_owned());
    response.provenance.corpus_stage_event_count = 100_000;
    response
}

fn provenance() -> OracleProvenance {
    OracleProvenance {
        source_snapshot_sha256: "fixture-snapshot".to_owned(),
        corpus_stage_name: Some("fixture-stage".to_owned()),
        corpus_stage_event_count: 10_000,
        corpus_stage_selection_rule: "fixture-selection".to_owned(),
        eligibility: EligibilityRules::mvp(),
        content_preprocessing_rule: "fixture-preprocessing".to_owned(),
        content_length_limit_tokens: 512,
        model_id: "fixture-model".to_owned(),
        model_revision: "fixture-revision".to_owned(),
        embedding_dimensions: 1_024,
        matrix_format: "fixture-matrix".to_owned(),
        candidate_depth: 0,
        exact_search_implementation: "fixture-exact-search".to_owned(),
    }
}

fn versions() -> OracleVersions {
    OracleVersions {
        corpus: "fixture-corpus".to_owned(),
        retriever: "fixture-retriever".to_owned(),
    }
}

fn setup_recommendation_oracle() -> RecordingOracle {
    RecordingOracle::default()
        .with_note(id(1), response(&[(id(10), 0.9)]))
        .with_note(id(3), response(&[(id(30), 0.9)]))
}

fn id(byte: u8) -> EventId {
    EventId::from([byte; 32])
}
