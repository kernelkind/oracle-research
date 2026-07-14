use std::fs::{self, File};
use std::io::Cursor;
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::{Duration, Instant};

use nostrdb::{Config, Filter, Ndb, NoteBuilder, Transaction};
use oracle_mvp::embedding::{EmbeddingEncoder, EncoderDescriptor};
use oracle_mvp::manual_workflow::{
    ManualDecisionKind, ManualSession, ManualSessionPhase, ManualWorkflowConfig,
    ManualWorkflowOutcome, run_manual_workflow,
};
use oracle_mvp::ordered_embedding::{OrderedEmbeddingBuildConfig, build_ordered_embeddings};

#[test]
fn guided_workflow_resumes_and_records_private_decisions_without_changing_sources() {
    let temp = tempfile::tempdir().expect("temporary directory");
    let ndb_path = temp.path().join("corpus.ndb");
    let ndb = open_ndb(&ndb_path);
    let contents = [
        "distributed systems design",
        "distributed databases",
        "consensus protocols",
        "network partitions",
        "ceramic glazing",
    ];
    let events = contents
        .iter()
        .enumerate()
        .map(|(index, content)| signed_event(content, index as u64))
        .collect::<Vec<_>>();
    for event in &events {
        ndb.process_event(event).expect("submit event");
    }
    wait_for_count(&ndb, events.len());
    drop(ndb);

    let ordered_ids = events
        .iter()
        .map(|event| event_id(event))
        .collect::<Vec<_>>();
    let ordered_path = temp.path().join("ordered-event-ids.bin");
    write_ids(&ordered_path, &ordered_ids);
    let artifact_path = temp.path().join("embeddings");
    build_ordered_embeddings(
        &ndb_path,
        &ordered_path,
        &artifact_path,
        &OrderedEmbeddingBuildConfig {
            rows: contents.len() as u64,
            batch_size: 2,
            shard_rows: contents.len() as u64,
        },
        &mut FixtureEncoder::new(),
    )
    .expect("build ordered embedding artifact");

    let session_path = temp.path().join("manual-session.json");
    let config = ManualWorkflowConfig {
        corpus_path: ndb_path,
        ordered_event_ids_path: ordered_path,
        embedding_artifact_path: artifact_path,
        session_path: session_path.clone(),
        onboarding_depth: 2,
        neighbor_depth: 4,
        recommendation_limit: 2,
    };

    let mut first_output = Vec::new();
    let first = run_manual_workflow(
        &config,
        FixtureEncoder::new(),
        Cursor::new(b"distributed systems\n1\nw\nq\n"),
        &mut first_output,
    )
    .expect("run first portion");
    assert_eq!(first, ManualWorkflowOutcome::Paused);
    let first_session = read_session(&session_path);
    assert_eq!(
        first_session.phase,
        ManualSessionPhase::JudgeRecommendations
    );
    assert_eq!(first_session.decisions.len(), 1);
    assert_eq!(
        first_session.decisions[0].judgment,
        ManualDecisionKind::WorthSeeing
    );
    assert_eq!(
        first_session
            .runner_state
            .interest(first_session.interest_id)
            .expect("interest")
            .positive_sources()
            .len(),
        1
    );

    let mut second_output = Vec::new();
    let second = run_manual_workflow(
        &config,
        FixtureEncoder::new(),
        Cursor::new(b"n\n"),
        &mut second_output,
    )
    .expect("resume workflow");
    assert_eq!(second, ManualWorkflowOutcome::Complete);
    let completed = read_session(&session_path);
    assert_eq!(completed.phase, ManualSessionPhase::Complete);
    assert_eq!(completed.topic, "distributed systems");
    assert_eq!(completed.bootstrap_response.candidates.len(), 5);
    assert_eq!(completed.onboarding_candidates.len(), 2);
    assert_eq!(completed.selected_source_ids.len(), 1);
    assert_eq!(completed.decisions.len(), 2);
    assert_eq!(
        completed.decisions[1].judgment,
        ManualDecisionKind::NotWorthSeeing
    );
    assert_eq!(
        completed
            .runner_state
            .interest(completed.interest_id)
            .expect("interest")
            .positive_sources()
            .len(),
        1,
        "worth seeing must not silently become show-more-like-this"
    );

    let transcript = String::from_utf8(first_output).expect("UTF-8 transcript");
    assert!(transcript.contains("Enter one interest"));
    assert!(transcript.contains("Choose worthwhile source notes"));
    assert!(transcript.contains("Worth seeing?"));
    assert!(!transcript.contains("cosine"));
    assert!(!transcript.contains("source rank"));
    let resumed = String::from_utf8(second_output).expect("UTF-8 resumed transcript");
    assert!(!resumed.contains("Enter one interest"));
    assert!(!resumed.contains("Choose worthwhile source notes"));
}

#[test]
fn guided_workflow_overretrieves_and_filters_non_english_before_presentation() {
    let temp = tempfile::tempdir().expect("temporary directory");
    let ndb_path = temp.path().join("corpus.ndb");
    let ndb = open_ndb(&ndb_path);
    let contents = [
        "Dieser ausführliche Beitrag erklärt sichere Rust-Programmierung mit praktischen Beispielen für verteilte Computersysteme.",
        "Este artículo detallado explica programación segura con Rust y ejemplos prácticos para sistemas distribuidos.",
        "This practical guide explains safe Rust programming for distributed computer systems.",
        "A detailed tutorial about writing reliable concurrent services in the Rust programming language.",
        "Ce guide présente la programmation concurrente en Rust pour construire des services distribués fiables.",
        "Ownership patterns for reliable concurrent Rust services.",
        "Testing distributed Rust applications under network partitions.",
        "Ceramic glazing techniques for a small pottery studio.",
    ];
    let events = contents
        .iter()
        .enumerate()
        .map(|(index, content)| signed_event(content, index as u64))
        .collect::<Vec<_>>();
    for event in &events {
        ndb.process_event(event).expect("submit event");
    }
    wait_for_count(&ndb, events.len());
    drop(ndb);

    let ordered_ids = events
        .iter()
        .map(|event| event_id(event))
        .collect::<Vec<_>>();
    let ordered_path = temp.path().join("ordered-event-ids.bin");
    write_ids(&ordered_path, &ordered_ids);
    let artifact_path = temp.path().join("embeddings");
    build_ordered_embeddings(
        &ndb_path,
        &ordered_path,
        &artifact_path,
        &OrderedEmbeddingBuildConfig {
            rows: contents.len() as u64,
            batch_size: 2,
            shard_rows: contents.len() as u64,
        },
        &mut FixtureEncoder::new(),
    )
    .expect("build ordered embedding artifact");

    let session_path = temp.path().join("manual-session.json");
    let config = ManualWorkflowConfig {
        corpus_path: ndb_path,
        ordered_event_ids_path: ordered_path,
        embedding_artifact_path: artifact_path,
        session_path: session_path.clone(),
        onboarding_depth: 2,
        neighbor_depth: 8,
        recommendation_limit: 2,
    };
    let mut output = Vec::new();
    let outcome = run_manual_workflow(
        &config,
        FixtureEncoder::new(),
        Cursor::new(b"rust coding\n1\nw\n\nn\n"),
        &mut output,
    )
    .expect("run language-filtered workflow");
    assert_eq!(outcome, ManualWorkflowOutcome::Complete);

    let session = read_session(&session_path);
    assert_eq!(session.bootstrap_response.candidates.len(), contents.len());
    assert_eq!(session.bootstrap_retrieval_depth, 20);
    assert_eq!(
        session.bootstrap_response.provenance.candidate_depth,
        session.bootstrap_retrieval_depth as u64
    );
    assert_eq!(
        session.language_filter_policy,
        "whatlang-0.18.0:exclude-reliable-non-english-v1"
    );
    assert_eq!(session.onboarding_candidates.len(), 2);
    assert_eq!(
        session
            .onboarding_candidates
            .iter()
            .map(|candidate| candidate.event_id)
            .collect::<Vec<_>>(),
        vec![ordered_ids[2].into(), ordered_ids[3].into()]
    );
    assert!(!session.runner_state.seen().contains(&ordered_ids[0].into()));
    assert!(!session.runner_state.seen().contains(&ordered_ids[1].into()));
    assert!(!session.runner_state.seen().contains(&ordered_ids[4].into()));
    assert!(
        session.unfiltered_recommendation_candidates.len()
            > session.recommendation_candidates.len()
    );
    assert_eq!(
        session
            .recommendation_candidates
            .iter()
            .take(2)
            .map(|candidate| candidate.event_id)
            .collect::<Vec<_>>(),
        vec![ordered_ids[5].into(), ordered_ids[6].into()]
    );

    let transcript = String::from_utf8(output).expect("UTF-8 transcript");
    assert!(transcript.contains(contents[2]));
    assert!(transcript.contains(contents[3]));
    assert!(transcript.contains(contents[5]));
    assert!(transcript.contains(contents[6]));
    assert!(!transcript.contains(contents[0]));
    assert!(!transcript.contains(contents[1]));
    assert!(!transcript.contains(contents[4]));
}

fn read_session(path: &std::path::Path) -> ManualSession {
    serde_json::from_reader(File::open(path).expect("open session")).expect("decode session")
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
        .sign(&[7_u8; 32])
        .build()
        .expect("sign fixture event")
        .json()
        .expect("event JSON")
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
    let mut bytes = Vec::with_capacity(ids.len() * 32);
    for id in ids {
        bytes.extend_from_slice(id);
    }
    fs::write(path, bytes).expect("write ordered IDs");
}

struct FixtureEncoder {
    descriptor: EncoderDescriptor,
    queries: Arc<Mutex<Vec<String>>>,
}

impl FixtureEncoder {
    fn new() -> Self {
        Self {
            descriptor: EncoderDescriptor {
                model_id: "fixture-encoder".to_owned(),
                model_revision: "fixture-revision".to_owned(),
                model_lock_sha256: "fixture-lock".to_owned(),
                runtime: "fixture-runtime".to_owned(),
                runtime_version: "fixture-runtime-version".to_owned(),
                runtime_sha256: "fixture-runtime-sha".to_owned(),
                execution_provider: "cpu".to_owned(),
                output_name: "fixture-output".to_owned(),
                dimensions: 4,
                max_tokens: 512,
                input_rule: "fixture-input".to_owned(),
                pooling: "fixture-pooling".to_owned(),
                quantization: "native-int8".to_owned(),
                instruction: None,
            },
            queries: Arc::new(Mutex::new(Vec::new())),
        }
    }

    fn vector(text: &str) -> [i8; 4] {
        match text {
            "distributed systems" => [100, 0, 0, 0],
            "distributed systems design" => [100, 0, 0, 0],
            "distributed databases" => [95, 5, 0, 0],
            "consensus protocols" => [80, 20, 0, 0],
            "network partitions" => [65, 35, 0, 0],
            "ceramic glazing" => [0, 100, 0, 0],
            "rust coding" => [100, 0, 0, 0],
            "Dieser ausführliche Beitrag erklärt sichere Rust-Programmierung mit praktischen Beispielen für verteilte Computersysteme." => {
                [100, 0, 0, 0]
            }
            "Este artículo detallado explica programación segura con Rust y ejemplos prácticos para sistemas distribuidos." => {
                [99, 1, 0, 0]
            }
            "This practical guide explains safe Rust programming for distributed computer systems." => {
                [98, 2, 0, 0]
            }
            "A detailed tutorial about writing reliable concurrent services in the Rust programming language." => {
                [97, 3, 0, 0]
            }
            "Ce guide présente la programmation concurrente en Rust pour construire des services distribués fiables." => {
                [96, 4, 0, 0]
            }
            "Ownership patterns for reliable concurrent Rust services." => [90, 10, 0, 0],
            "Testing distributed Rust applications under network partitions." => [85, 15, 0, 0],
            "Ceramic glazing techniques for a small pottery studio." => [0, 100, 0, 0],
            other => panic!("unexpected fixture input: {other}"),
        }
    }
}

impl EmbeddingEncoder for FixtureEncoder {
    fn descriptor(&self) -> &EncoderDescriptor {
        &self.descriptor
    }

    fn effective_token_lengths(
        &mut self,
        texts: &[&str],
    ) -> oracle_mvp::snapshot::Result<Vec<u32>> {
        Ok(texts.iter().map(|text| text.len() as u32).collect())
    }

    fn encode(&mut self, texts: &[&str]) -> oracle_mvp::snapshot::Result<Vec<i8>> {
        self.queries
            .lock()
            .expect("query lock")
            .extend(texts.iter().map(|text| (*text).to_owned()));
        Ok(texts.iter().flat_map(|text| Self::vector(text)).collect())
    }
}
