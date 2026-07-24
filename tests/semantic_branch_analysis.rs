use std::collections::BTreeMap;
use std::fs::{self, File};
use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::thread;
use std::time::{Duration, Instant};

use nostrdb::{Config, Filter, Ndb, NoteBuilder, Transaction};
use oracle_mvp::fp32_oracle::{Fp32Candidate, SimilarNotesResponse};
use oracle_mvp::gte::TokenRole;
use oracle_mvp::ordered_gte_token_audit::{
    OrderedGteTokenAuditConfig, OrderedGteTokenCounter, audit_ordered_gte_tokens,
};
use oracle_mvp::representation::{
    RepresentationBuildConfig, RepresentationDescriptor, RepresentationEncoder,
    build_representation_shards,
};
use oracle_mvp::representation_batch_plan::{
    RepresentationBatchPlanConfig, create_representation_batch_plan,
};
use oracle_mvp::semantic_branch_analysis::{
    SEMANTIC_BRANCH_REPORT_FILE, SemanticBranchAnalysisConfig, SemanticBranchAnalysisError,
    SemanticBranchAnalysisReport, analyze_semantic_branch_from_config,
    verify_semantic_branch_from_config,
};
use oracle_mvp::semantic_branch_artifact::{
    LABELER_A_LABELS_FILE, LABELER_A_PACKET_FILE, LABELER_B_LABELS_FILE, LABELER_B_PACKET_FILE,
    SemanticBranchLabelRecord, SemanticBranchPrepareConfig, select_semantic_branch_candidates,
};
use oracle_mvp::semantic_branch_geometry::{BranchLabel, SemanticBranchDecision};
use oracle_mvp::snapshot::{Error, Result};
use sha2::{Digest, Sha256};

const SECRET_KEY: [u8; 32] = [31; 32];

#[test]
fn analysis_refuses_unsealed_input_before_opening_vector_artifacts() {
    let temp = tempfile::tempdir().expect("temporary analysis workspace");
    let run_path = temp.path().join("prepared-but-unsealed");
    fs::create_dir(&run_path).expect("create unsealed run directory");
    let config_path = temp.path().join("analysis.json");
    write_json(
        &config_path,
        &SemanticBranchAnalysisConfig {
            run_path,
            ordered_event_ids_path: temp.path().join("missing-ordered-event-ids.bin"),
            expected_ordered_event_ids_sha256: "1".repeat(64),
            representation_path: temp.path().join("missing-representation"),
            representation_version: "2".repeat(64),
            represented_rows: 1_025,
        },
    );

    let error = analyze_semantic_branch_from_config(&config_path)
        .expect_err("unsealed input must fail before vector lookup");

    assert!(matches!(
        error,
        SemanticBranchAnalysisError::Artifact(
            oracle_mvp::semantic_branch_artifact::SemanticBranchArtifactError::MissingLabelSeal(_)
        )
    ));
}

#[test]
fn cli_prepares_seals_publishes_and_verifies_one_auditable_report() {
    let fixture = AnalysisFixture::new();

    let prepare = Command::new(env!("CARGO_BIN_EXE_semantic-branch-diagnostic"))
        .args([
            "prepare",
            fixture.prepare_config_path.to_str().expect("UTF-8 path"),
        ])
        .output()
        .expect("run prepare command");
    assert!(
        prepare.status.success(),
        "prepare failed: {}",
        String::from_utf8_lossy(&prepare.stderr)
    );
    fixture.write_neutral_labels();

    let seal = Command::new(env!("CARGO_BIN_EXE_semantic-branch-diagnostic"))
        .args([
            "seal-labels",
            fixture.run_path.to_str().expect("UTF-8 path"),
        ])
        .output()
        .expect("run seal-labels command");
    assert!(
        seal.status.success(),
        "seal failed: {}",
        String::from_utf8_lossy(&seal.stderr)
    );

    let analyze = Command::new(env!("CARGO_BIN_EXE_semantic-branch-diagnostic"))
        .args([
            "analyze",
            fixture.analysis_config_path.to_str().expect("UTF-8 path"),
        ])
        .output()
        .expect("run analyze command");
    assert!(
        analyze.status.success(),
        "analyze failed: {}",
        String::from_utf8_lossy(&analyze.stderr)
    );

    let report_path = fixture.run_path.join(SEMANTIC_BRANCH_REPORT_FILE);
    let report: SemanticBranchAnalysisReport =
        serde_json::from_slice(&fs::read(&report_path).expect("read report"))
            .expect("decode report");
    assert_eq!(report.candidate_count, 160);
    assert_eq!(report.vector_dimension, 3);
    assert_eq!(
        report.representation_version,
        fixture.representation_version
    );
    assert_eq!(report.represented_rows, 1_025);
    assert_eq!(report.geometry.permutations, 10_000);
    assert_eq!(report.geometry.minimum_exclusive_notes, 8);
    assert_eq!(report.decision, SemanticBranchDecision::Underdetermined);
    assert_eq!(
        report.ordered_event_ids_sha256,
        sha256_file(&fixture.ordered_event_ids_path)
    );
    assert_eq!(report.run_input_sha256.len(), 5);

    let report_before = fs::read(&report_path).expect("read create-once report");
    let files_before_verify = snapshot_tree(fixture._temp.path());
    let verify = Command::new(env!("CARGO_BIN_EXE_semantic-branch-diagnostic"))
        .args([
            "verify",
            fixture.analysis_config_path.to_str().expect("UTF-8 path"),
        ])
        .output()
        .expect("run verify command");
    assert!(
        verify.status.success(),
        "verify failed: {}",
        String::from_utf8_lossy(&verify.stderr)
    );
    assert_eq!(
        snapshot_tree(fixture._temp.path()),
        files_before_verify,
        "verification must not write or change any diagnostic source/report byte"
    );

    let second = analyze_semantic_branch_from_config(&fixture.analysis_config_path)
        .expect_err("published report must not be overwritten");
    assert!(matches!(
        second,
        SemanticBranchAnalysisError::ArtifactExists(path) if path == report_path
    ));
    assert_eq!(
        fs::read(&report_path).expect("reread report"),
        report_before
    );

    let mut tampered: serde_json::Value =
        serde_json::from_slice(&report_before).expect("decode report for tampering");
    tampered["decision"] = serde_json::Value::String("no_recoverable_branches".to_owned());
    write_json(&report_path, &tampered);
    let tampered_files = snapshot_tree(fixture._temp.path());

    let error = verify_semantic_branch_from_config(&fixture.analysis_config_path)
        .expect_err("tampered decision must fail exact report verification");
    assert!(matches!(
        error,
        SemanticBranchAnalysisError::ReportMismatch(path) if path == report_path
    ));
    assert_eq!(
        snapshot_tree(fixture._temp.path()),
        tampered_files,
        "failed verification must not repair or otherwise mutate any artifact"
    );
}

struct AnalysisFixture {
    _temp: tempfile::TempDir,
    run_path: PathBuf,
    prepare_config_path: PathBuf,
    analysis_config_path: PathBuf,
    ordered_event_ids_path: PathBuf,
    representation_version: String,
}

impl AnalysisFixture {
    fn new() -> Self {
        let temp = tempfile::tempdir().expect("temporary semantic-branch workspace");
        let corpus_path = temp.path().join("corpus.ndb");
        let ndb = Ndb::new(
            corpus_path.to_str().expect("UTF-8 corpus path"),
            &Config::new().set_mapsize(2 * 1_024 * 1_024 * 1_024),
        )
        .expect("open fixture NostrDB");
        let events = (0_u64..1_025)
            .map(|index| {
                NoteBuilder::new()
                    .kind(1)
                    .content(&format!("note-{index}"))
                    .created_at(1_720_000_000 + index)
                    .sign(&SECRET_KEY)
                    .build()
                    .expect("build fixture note")
            })
            .collect::<Vec<_>>();
        for event in &events {
            ndb.process_event(&event.json().expect("encode fixture note"))
                .expect("ingest fixture note");
        }
        wait_for_count(&ndb, events.len());
        drop(ndb);
        let event_ids = events.iter().map(|event| *event.id()).collect::<Vec<_>>();
        let ordered_event_ids_path = temp.path().join("ordered-event-ids.bin");
        write_event_ids(&ordered_event_ids_path, &event_ids);

        let token_audit_path = temp.path().join("token-audit");
        let mut counter = FixtureTokenCounter {
            descriptor: fixture_descriptor(),
        };
        audit_ordered_gte_tokens(
            &corpus_path,
            &ordered_event_ids_path,
            &token_audit_path,
            &OrderedGteTokenAuditConfig {
                batch_size: 1_025,
                shard_rows: 1_025,
            },
            &mut counter,
        )
        .expect("audit fixture tokens");
        let batch_plan_path = temp.path().join("batch-plan");
        create_representation_batch_plan(
            &ordered_event_ids_path,
            &token_audit_path,
            &batch_plan_path,
            &RepresentationBatchPlanConfig {
                shard_rows: 1_025,
                batch_rows: 1_025,
            },
        )
        .expect("create fixture batch plan");
        let representation_path = temp.path().join("representation");
        let mut encoder = FixtureEncoder {
            descriptor: fixture_descriptor(),
        };
        let built = build_representation_shards(
            &corpus_path,
            &ordered_event_ids_path,
            &representation_path,
            &RepresentationBuildConfig {
                token_audit_path,
                batch_plan_path,
                shard_ordinals: vec![0],
            },
            &mut encoder,
        )
        .expect("build complete fixture representation");
        assert!(built.manifest.complete);

        let source_event_id = event_ids[0];
        let response = SimilarNotesResponse {
            representation_version: built.representation_version.clone(),
            represented_rows: 1_025,
            total_rows: 1_025,
            complete: true,
            candidates: event_ids[1..]
                .iter()
                .enumerate()
                .map(|(index, event_id)| Fp32Candidate {
                    event_id: *event_id,
                    rank: index + 1,
                    cosine_score: cached_cosine(index + 1),
                })
                .collect(),
        };
        assert_eq!(
            select_semantic_branch_candidates(&response, source_event_id)
                .expect("select fixture branch candidates")
                .len(),
            160
        );
        let response_path = temp.path().join("cached-response.json");
        let response_bytes = serde_json::to_vec_pretty(&serde_json::json!({
            "key": {
                "representation_version": built.representation_version,
                "source_event_id": source_event_id,
                "candidate_depth": 1_024
            },
            "response": response
        }))
        .expect("encode cached response");
        fs::write(&response_path, &response_bytes).expect("write cached response");

        let run_path = temp.path().join("semantic-branch-run");
        let prepare_config = SemanticBranchPrepareConfig {
            cached_response_path: response_path,
            expected_cached_response_sha256: sha256_bytes(&response_bytes),
            corpus_path: corpus_path.clone(),
            expected_corpus_data_sha256: sha256_file(&corpus_path.join("data.mdb")),
            output_path: run_path.clone(),
            source_event_id,
            representation_version: built.representation_version.clone(),
            represented_rows: 1_025,
        };
        let prepare_config_path = temp.path().join("prepare.json");
        write_json(&prepare_config_path, &prepare_config);

        let analysis_config = SemanticBranchAnalysisConfig {
            run_path: run_path.clone(),
            ordered_event_ids_path: ordered_event_ids_path.clone(),
            expected_ordered_event_ids_sha256: sha256_file(&ordered_event_ids_path),
            representation_path,
            representation_version: built.representation_version.clone(),
            represented_rows: 1_025,
        };
        let analysis_config_path = temp.path().join("analysis.json");
        write_json(&analysis_config_path, &analysis_config);

        Self {
            _temp: temp,
            run_path,
            prepare_config_path,
            analysis_config_path,
            ordered_event_ids_path,
            representation_version: built.representation_version,
        }
    }

    fn write_neutral_labels(&self) {
        write_neutral_labels(
            &self.run_path.join(LABELER_A_PACKET_FILE),
            &self.run_path.join(LABELER_A_LABELS_FILE),
        );
        write_neutral_labels(
            &self.run_path.join(LABELER_B_PACKET_FILE),
            &self.run_path.join(LABELER_B_LABELS_FILE),
        );
    }
}

struct FixtureTokenCounter {
    descriptor: RepresentationDescriptor,
}

impl OrderedGteTokenCounter for FixtureTokenCounter {
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
        Ok(texts
            .iter()
            .flat_map(|text| document_vector(text))
            .collect())
    }

    fn encode_queries(&mut self, _texts: &[&str]) -> Result<Vec<f32>> {
        Err(Error::Encoder {
            operation: "encode queries",
            message: "semantic-branch fixture is document-only".to_owned(),
        })
    }
}

fn fixture_descriptor() -> RepresentationDescriptor {
    RepresentationDescriptor {
        model_id: "fixture/semantic-branch".to_owned(),
        model_revision: "1".repeat(40),
        model_lock_sha256: "2".repeat(64),
        worker_sha256: "3".repeat(64),
        dependency_lock_sha256: "4".repeat(64),
        container_image: "fixture@sha256:".to_owned() + &"5".repeat(64),
        torch_version: "fixture".to_owned(),
        transformers_version: "fixture".to_owned(),
        cuda_version: "fixture".to_owned(),
        execution_device: "cpu".to_owned(),
        dimensions: 3,
        model_token_ceiling: 512,
        document_input: "raw-note-content".to_owned(),
        query_instruction: "fixture".to_owned(),
        pooling: "last-token".to_owned(),
        normalization: "l2".to_owned(),
        numeric_format: "f32le".to_owned(),
    }
}

fn document_vector(content: &str) -> Vec<f32> {
    let index = content
        .strip_prefix("note-")
        .and_then(|value| value.parse::<usize>().ok())
        .expect("fixture note index");
    if index == 0 {
        return vec![1.0, 0.0, 0.0];
    }
    let cosine = cached_cosine(index);
    vec![cosine, (1.0 - cosine * cosine).sqrt(), 0.0]
}

fn cached_cosine(rank: usize) -> f32 {
    0.8 - rank as f32 / 4_096.0
}

fn write_neutral_labels(packet_path: &Path, labels_path: &Path) {
    let records = fs::read_to_string(packet_path)
        .expect("read blind packet")
        .lines()
        .map(|line| {
            let value: serde_json::Value = serde_json::from_str(line).expect("decode blind record");
            SemanticBranchLabelRecord {
                record_id: value["record_id"]
                    .as_str()
                    .expect("blind record ID")
                    .to_owned(),
                label: BranchLabel::themes([]),
            }
        })
        .collect::<Vec<_>>();
    let mut encoded = records
        .iter()
        .map(|record| serde_json::to_string(record).expect("encode neutral label"))
        .collect::<Vec<_>>()
        .join("\n");
    encoded.push('\n');
    fs::write(labels_path, encoded).expect("write neutral labels");
}

fn wait_for_count(ndb: &Ndb, expected: usize) {
    let deadline = Instant::now() + Duration::from_secs(30);
    loop {
        let transaction = Transaction::new(ndb).expect("open count transaction");
        let count = ndb
            .fold(
                &transaction,
                &[Filter::new().build()],
                0_usize,
                |count, _| count + 1,
            )
            .expect("count fixture notes");
        if count == expected {
            return;
        }
        assert!(Instant::now() < deadline, "fixture ingestion timed out");
        thread::sleep(Duration::from_millis(10));
    }
}

fn write_event_ids(path: &Path, event_ids: &[[u8; 32]]) {
    let mut file = File::create(path).expect("create ordered event IDs");
    for event_id in event_ids {
        file.write_all(event_id).expect("write ordered event ID");
    }
    file.sync_all().expect("sync ordered event IDs");
}

fn write_json(path: &Path, value: &impl serde::Serialize) {
    let mut bytes = serde_json::to_vec_pretty(value).expect("encode JSON");
    bytes.push(b'\n');
    fs::write(path, bytes).expect("write JSON");
}

fn sha256_file(path: &Path) -> String {
    sha256_bytes(&fs::read(path).expect("read hash input"))
}

fn sha256_bytes(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}

fn snapshot_tree(root: &Path) -> BTreeMap<PathBuf, Vec<u8>> {
    fn walk(root: &Path, directory: &Path, snapshot: &mut BTreeMap<PathBuf, Vec<u8>>) {
        let mut entries = fs::read_dir(directory)
            .expect("read snapshot directory")
            .collect::<std::result::Result<Vec<_>, _>>()
            .expect("enumerate snapshot directory");
        entries.sort_by_key(|entry| entry.file_name());
        for entry in entries {
            let path = entry.path();
            let relative = path
                .strip_prefix(root)
                .expect("snapshot path under root")
                .to_owned();
            let file_type = entry.file_type().expect("read snapshot file type");
            if file_type.is_dir() {
                snapshot.insert(relative, vec![1]);
                walk(root, &path, snapshot);
            } else if file_type.is_file() {
                let mut bytes = vec![0];
                bytes.extend(fs::read(&path).expect("read snapshot file"));
                snapshot.insert(relative, bytes);
            } else {
                panic!("unexpected filesystem entry in fixture: {}", path.display());
            }
        }
    }

    let mut snapshot = BTreeMap::new();
    walk(root, root, &mut snapshot);
    snapshot
}
