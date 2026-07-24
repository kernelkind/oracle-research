use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::io::Write;
use std::path::Path;
use std::thread;
use std::time::{Duration, Instant};

use nostrdb::{Config, Filter, Ndb, NoteBuilder, Transaction};
use oracle_mvp::fp32_oracle::{Fp32Candidate, SimilarNotesResponse};
use oracle_mvp::semantic_branch_artifact::{
    LABELER_A_LABELS_FILE, LABELER_A_PACKET_FILE, LABELER_B_LABELS_FILE, LABELER_B_PACKET_FILE,
    PRIVATE_KEY_FILE, SemanticBranchLabelRecord, SemanticBranchPrepareConfig,
    open_sealed_semantic_branch_input, prepare_semantic_branch_artifact,
    read_cached_semantic_branch_response, seal_semantic_branch_labels,
    select_semantic_branch_candidates,
};
use oracle_mvp::semantic_branch_geometry::BranchLabel;
use sha2::{Digest, Sha256};

const VERSION: &str = "5365b29f5e41d361cfae4b3a1754501d5320728053887236449071d680302c50";
const SECRET_KEY: [u8; 32] = [29; 32];

#[test]
fn selection_takes_the_smallest_domain_hashes_from_each_rank_quartile() {
    let source = [0xff; 32];
    let response = complete_response();

    let selected = select_semantic_branch_candidates(&response, source).expect("select candidates");

    assert_eq!(selected.len(), 160);
    assert_eq!(
        selected
            .iter()
            .fold(BTreeMap::new(), |mut counts, candidate| {
                *counts.entry(candidate.rank_quartile).or_insert(0) += 1;
                counts
            }),
        BTreeMap::from([(0, 40), (1, 40), (2, 40), (3, 40)])
    );
    for quartile in 0_u8..=3 {
        let first_rank = usize::from(quartile) * 256 + 1;
        let mut expected = response.candidates[first_rank - 1..first_rank + 255]
            .iter()
            .map(|candidate| (sample_key(&candidate.event_id), candidate.event_id))
            .collect::<Vec<_>>();
        expected.sort_unstable();
        let expected = expected
            .into_iter()
            .take(40)
            .map(|(_, event_id)| event_id)
            .collect::<Vec<_>>();
        let actual = selected
            .iter()
            .filter(|candidate| candidate.rank_quartile == quartile)
            .map(|candidate| candidate.event_id)
            .collect::<Vec<_>>();
        assert_eq!(actual, expected);
    }
}

#[test]
fn cached_reader_rejects_changed_hash_key_and_incomplete_response() {
    let fixture = ArtifactFixture::new();

    let response = read_cached_semantic_branch_response(
        &fixture.config.cached_response_path,
        &fixture.config.expected_cached_response_sha256,
        fixture.config.source_event_id,
        VERSION,
        3_530_455,
    )
    .expect("read exact cached response");
    assert_eq!(response.candidates.len(), 1_024);

    let original = fs::read(&fixture.config.cached_response_path).expect("read response bytes");
    fs::write(
        &fixture.config.cached_response_path,
        [original.as_slice(), b"\n"].concat(),
    )
    .expect("change response bytes");
    let checksum_error = read_cached_semantic_branch_response(
        &fixture.config.cached_response_path,
        &fixture.config.expected_cached_response_sha256,
        fixture.config.source_event_id,
        VERSION,
        3_530_455,
    )
    .expect_err("changed cached bytes must be rejected");
    assert!(checksum_error.to_string().contains("hash"));
    fs::write(&fixture.config.cached_response_path, &original).expect("restore response bytes");

    let mut changed: serde_json::Value =
        serde_json::from_slice(&original).expect("decode response wrapper");
    changed["key"]["candidate_depth"] = 1_023.into();
    let changed_bytes = serde_json::to_vec(&changed).expect("encode changed key");
    fs::write(&fixture.config.cached_response_path, &changed_bytes).expect("write changed key");
    let key_error = read_cached_semantic_branch_response(
        &fixture.config.cached_response_path,
        &sha256_bytes(&changed_bytes),
        fixture.config.source_event_id,
        VERSION,
        3_530_455,
    )
    .expect_err("changed immutable key must be rejected");
    assert!(key_error.to_string().contains("key"));

    changed["key"]["candidate_depth"] = 1_024.into();
    changed["response"]["complete"] = false.into();
    let changed_bytes = serde_json::to_vec(&changed).expect("encode incomplete response");
    fs::write(&fixture.config.cached_response_path, &changed_bytes)
        .expect("write incomplete response");
    let incomplete_error = read_cached_semantic_branch_response(
        &fixture.config.cached_response_path,
        &sha256_bytes(&changed_bytes),
        fixture.config.source_event_id,
        VERSION,
        3_530_455,
    )
    .expect_err("incomplete response must be rejected");
    assert!(incomplete_error.to_string().contains("complete top-1024"));
}

#[test]
fn prepared_packets_are_balanced_deterministic_and_blind() {
    let fixture = ArtifactFixture::new();
    let response_before = sha256_file(&fixture.config.cached_response_path);
    let corpus_before = sha256_file(&fixture.config.corpus_path.join("data.mdb"));

    prepare_semantic_branch_artifact(&fixture.config).expect("prepare first blind artifact");
    let mut second = fixture.config.clone();
    second.output_path = fixture._temp.path().join("second-artifact");
    prepare_semantic_branch_artifact(&second).expect("prepare second blind artifact");

    assert_eq!(
        fs::read(fixture.config.output_path.join(LABELER_A_PACKET_FILE))
            .expect("read first packet"),
        fs::read(second.output_path.join(LABELER_A_PACKET_FILE)).expect("read second packet")
    );
    assert_eq!(
        fs::read(fixture.config.output_path.join(LABELER_B_PACKET_FILE))
            .expect("read first packet"),
        fs::read(second.output_path.join(LABELER_B_PACKET_FILE)).expect("read second packet")
    );
    assert_eq!(
        fs::read(fixture.config.output_path.join(PRIVATE_KEY_FILE)).expect("read first key"),
        fs::read(second.output_path.join(PRIVATE_KEY_FILE)).expect("read second key")
    );

    let packet_a = read_json_lines(&fixture.config.output_path.join(LABELER_A_PACKET_FILE));
    let packet_b = read_json_lines(&fixture.config.output_path.join(LABELER_B_PACKET_FILE));
    assert_eq!(packet_a.len(), 160);
    assert_eq!(packet_b.len(), 160);
    for record in packet_a.iter().chain(&packet_b) {
        assert_eq!(
            record
                .as_object()
                .expect("blind record object")
                .keys()
                .cloned()
                .collect::<BTreeSet<_>>(),
            BTreeSet::from(["content".to_owned(), "record_id".to_owned()])
        );
        let encoded = serde_json::to_string(record).expect("encode blind record");
        assert!(!encoded.contains("event_id"));
        assert!(!encoded.contains("rank"));
        assert!(!encoded.contains("score"));
        assert!(!encoded.contains("vector"));
    }
    assert_ne!(
        packet_a
            .iter()
            .map(|record| record["content"].as_str().expect("packet content"))
            .collect::<Vec<_>>(),
        packet_b
            .iter()
            .map(|record| record["content"].as_str().expect("packet content"))
            .collect::<Vec<_>>(),
        "independent label packets must use independent deterministic orders"
    );

    let key = read_json_lines(&fixture.config.output_path.join(PRIVATE_KEY_FILE));
    assert_eq!(key.len(), 160);
    assert_eq!(
        key.iter().fold(BTreeMap::new(), |mut counts, record| {
            *counts
                .entry(record["rank_quartile"].as_u64().expect("rank quartile"))
                .or_insert(0) += 1;
            counts
        }),
        BTreeMap::from([(0, 40), (1, 40), (2, 40), (3, 40)])
    );
    assert_eq!(
        sha256_file(&fixture.config.cached_response_path),
        response_before,
        "preparation must not modify the cached response"
    );
    assert_eq!(
        sha256_file(&fixture.config.corpus_path.join("data.mdb")),
        corpus_before,
        "preparation must not modify copied corpus data"
    );
}

#[test]
fn vectors_cannot_be_requested_until_exact_labels_are_sealed() {
    let fixture = ArtifactFixture::new();
    prepare_semantic_branch_artifact(&fixture.config).expect("prepare blind artifact");

    let unsealed = open_sealed_semantic_branch_input(&fixture.config.output_path)
        .expect_err("geometry input must remain unavailable before sealing");
    assert!(unsealed.to_string().contains("label seal"));

    write_neutral_labels(
        &fixture.config.output_path.join(LABELER_A_PACKET_FILE),
        &fixture.config.output_path.join(LABELER_A_LABELS_FILE),
    );
    write_neutral_labels(
        &fixture.config.output_path.join(LABELER_B_PACKET_FILE),
        &fixture.config.output_path.join(LABELER_B_LABELS_FILE),
    );
    seal_semantic_branch_labels(&fixture.config.output_path).expect("seal exact labels");

    let sealed = open_sealed_semantic_branch_input(&fixture.config.output_path)
        .expect("open sealed geometry input");
    assert_eq!(sealed.records().len(), 160);
    assert_eq!(sealed.label_sets()[0].labels().len(), 160);
    assert_eq!(sealed.label_sets()[1].labels().len(), 160);
    assert_eq!(
        sealed
            .records()
            .iter()
            .fold(BTreeMap::new(), |mut counts, record| {
                *counts.entry(record.rank_quartile()).or_insert(0) += 1;
                counts
            }),
        BTreeMap::from([(0, 40), (1, 40), (2, 40), (3, 40)])
    );

    let original = fs::read(&fixture.config.cached_response_path).expect("read source response");
    fs::write(
        &fixture.config.cached_response_path,
        [original.as_slice(), b"\n"].concat(),
    )
    .expect("change source response");
    let changed_response = open_sealed_semantic_branch_input(&fixture.config.output_path)
        .expect_err("changed response source must be rejected");
    assert!(changed_response.to_string().contains("hash"));
    fs::write(&fixture.config.cached_response_path, original).expect("restore source response");

    fs::OpenOptions::new()
        .append(true)
        .open(fixture.config.corpus_path.join("data.mdb"))
        .expect("open copied corpus data")
        .write_all(b"x")
        .expect("change copied corpus data");
    let changed_corpus = open_sealed_semantic_branch_input(&fixture.config.output_path)
        .expect_err("changed copied corpus must be rejected");
    assert!(changed_corpus.to_string().contains("hash"));
}

fn complete_response() -> SimilarNotesResponse {
    SimilarNotesResponse {
        representation_version: VERSION.to_owned(),
        represented_rows: 3_530_455,
        total_rows: 3_530_455,
        complete: true,
        candidates: (1..=1_024)
            .map(|rank| Fp32Candidate {
                event_id: event_id(rank as u64),
                rank,
                cosine_score: 1.0 - rank as f32 / 2_048.0,
            })
            .collect(),
    }
}

fn event_id(value: u64) -> [u8; 32] {
    let mut id = [0_u8; 32];
    id[..8].copy_from_slice(&value.to_le_bytes());
    id
}

fn sample_key(event_id: &[u8; 32]) -> [u8; 32] {
    let mut digest = Sha256::new();
    digest.update(b"oracle-mvp-semantic-branch-quartile-sample-v1\0");
    digest.update(event_id);
    digest.finalize().into()
}

struct ArtifactFixture {
    _temp: tempfile::TempDir,
    config: SemanticBranchPrepareConfig,
}

impl ArtifactFixture {
    fn new() -> Self {
        let temp = tempfile::tempdir().expect("temporary artifact workspace");
        let source_note = NoteBuilder::new()
            .kind(1)
            .content("Exercise, study, and prayer can each strengthen a person.")
            .created_at(1_720_000_000)
            .sign(&SECRET_KEY)
            .build()
            .expect("build source note");
        let source_event_id = *source_note.id();
        let mut events = Vec::with_capacity(1_024);
        let mut candidates = Vec::with_capacity(1_024);
        for rank in 1_usize..=1_024 {
            let note = NoteBuilder::new()
                .kind(1)
                .content(&format!(
                    "candidate text token {}",
                    sha256_bytes(&rank.to_le_bytes())[..16].to_owned()
                ))
                .created_at(1_720_000_000 + rank as u64)
                .sign(&SECRET_KEY)
                .build()
                .expect("build candidate note");
            candidates.push(Fp32Candidate {
                event_id: *note.id(),
                rank,
                cosine_score: 0.8 - rank as f32 / 4_096.0,
            });
            events.push(note.json().expect("encode candidate note"));
        }
        let response = SimilarNotesResponse {
            representation_version: VERSION.to_owned(),
            represented_rows: 3_530_455,
            total_rows: 3_530_455,
            complete: true,
            candidates,
        };
        let selected = select_semantic_branch_candidates(&response, source_event_id)
            .expect("select fixture candidates")
            .into_iter()
            .map(|candidate| candidate.event_id)
            .collect::<BTreeSet<_>>();
        let corpus_path = temp.path().join("copied-corpus.ndb");
        let ndb = Ndb::new(
            corpus_path.to_str().expect("UTF-8 corpus path"),
            &Config::new().set_mapsize(2 * 1_024 * 1_024 * 1_024),
        )
        .expect("open fixture NostrDB");
        for event in events {
            let event_id = event_id_from_json(&event);
            if selected.contains(&event_id) {
                ndb.process_event(&event).expect("ingest selected note");
            }
        }
        wait_for_count(&ndb, selected.len());
        drop(ndb);

        let response_path = temp.path().join("cached-response.json");
        let wrapper = serde_json::json!({
            "key": {
                "representation_version": VERSION,
                "source_event_id": source_event_id,
                "candidate_depth": 1_024
            },
            "response": response
        });
        let response_bytes = serde_json::to_vec_pretty(&wrapper).expect("encode response wrapper");
        fs::write(&response_path, &response_bytes).expect("write response wrapper");
        let config = SemanticBranchPrepareConfig {
            cached_response_path: response_path,
            expected_cached_response_sha256: sha256_bytes(&response_bytes),
            corpus_path: corpus_path.clone(),
            expected_corpus_data_sha256: sha256_file(&corpus_path.join("data.mdb")),
            output_path: temp.path().join("branch-artifact"),
            source_event_id,
            representation_version: VERSION.to_owned(),
            represented_rows: 3_530_455,
        };
        Self {
            _temp: temp,
            config,
        }
    }
}

fn wait_for_count(ndb: &Ndb, expected: usize) {
    let deadline = Instant::now() + Duration::from_secs(10);
    loop {
        let transaction = Transaction::new(ndb).expect("open count transaction");
        let count = ndb
            .fold(
                &transaction,
                &[Filter::new().build()],
                0_usize,
                |count, _| count + 1,
            )
            .expect("count notes");
        if count == expected {
            return;
        }
        assert!(Instant::now() < deadline, "candidate ingestion timed out");
        thread::sleep(Duration::from_millis(10));
    }
}

fn event_id_from_json(event: &str) -> [u8; 32] {
    let value: serde_json::Value = serde_json::from_str(event).expect("decode event JSON");
    let hex = value["id"].as_str().expect("event id hex");
    let mut event_id = [0_u8; 32];
    for (index, byte) in event_id.iter_mut().enumerate() {
        *byte = u8::from_str_radix(&hex[index * 2..index * 2 + 2], 16).expect("event ID byte");
    }
    event_id
}

fn write_neutral_labels(packet_path: &Path, labels_path: &Path) {
    let records = read_json_lines(packet_path)
        .into_iter()
        .map(|record| SemanticBranchLabelRecord {
            record_id: record["record_id"]
                .as_str()
                .expect("packet record ID")
                .to_owned(),
            label: BranchLabel::themes([]),
        })
        .collect::<Vec<_>>();
    let encoded = records
        .iter()
        .map(|record| serde_json::to_string(record).expect("encode label"))
        .collect::<Vec<_>>()
        .join("\n")
        + "\n";
    fs::write(labels_path, encoded).expect("write labels");
}

fn read_json_lines(path: &Path) -> Vec<serde_json::Value> {
    fs::read_to_string(path)
        .expect("read JSON lines")
        .lines()
        .map(|line| serde_json::from_str(line).expect("decode JSON line"))
        .collect()
}

fn sha256_file(path: &Path) -> String {
    sha256_bytes(&fs::read(path).expect("read hash input"))
}

fn sha256_bytes(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}
