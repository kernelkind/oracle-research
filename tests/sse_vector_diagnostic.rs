use std::fs;
use std::path::{Path, PathBuf};

use oracle_mvp::sse_vector_diagnostic::{
    analyze_sse_vectors, prepare_sse_worker_input, verify_sse_vector_diagnostic,
};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};

const SUBJECT_INSTRUCTION: &str = "Enumerate every atomic subject explicitly and substantively discussed in the provided text.\n\nAn atomic subject is the smallest coherent semantic idea that remains meaningful as a distinct focus.\n\n<RAW NOTE>\n\nReturn only a JSON array of subject strings.";
const MASK_INSTRUCTION: &str = "Mask only the narrowest portion or portions of the provided text that directly express the provided atomic subject.\n\nAtomic subject:\n<SUBJECT>\n\nText:\n<RAW NOTE>\n\nReturn only a JSON array of exact substrings copied from the text, in source order. If the subject is not expressed, return \"unsupported\".";

#[test]
fn production_path_prepares_an_unlabeled_packet_and_publishes_replayable_analysis() {
    let fixture = Fixture::new();

    prepare_sse_worker_input(&fixture.proposal_path, &fixture.worker_input_path)
        .expect("prepare worker input");
    let worker_input_bytes = fs::read(&fixture.worker_input_path).expect("read worker input");
    let worker_input: Value =
        serde_json::from_slice(&worker_input_bytes).expect("decode worker input");
    assert_eq!(worker_input["notes"].as_array().expect("notes").len(), 3);
    assert!(
        !String::from_utf8(worker_input_bytes.clone())
            .expect("utf-8 input")
            .contains("label"),
        "subject labels must not cross the encoder boundary"
    );
    assert_eq!(
        worker_input["notes"][0]["subjects"][0]["byte_spans"],
        json!([[0, 4]])
    );

    fixture.write_worker_result(&worker_input_bytes);
    analyze_sse_vectors(
        &fixture.proposal_path,
        &fixture.worker_receipt_path,
        &fixture.raw_vectors_path,
        &fixture.output_path,
    )
    .expect("analyze vectors");

    let analysis: Value = read_json(&fixture.output_path.join("analysis.json"));
    assert_eq!(analysis["subject_count"], 4);
    assert_eq!(analysis["pair_counts"]["all"], 6);
    assert_eq!(analysis["pair_counts"]["same_note"], 1);
    assert_eq!(analysis["pair_counts"]["cross_note"], 5);
    assert_eq!(analysis["pairs"].as_array().expect("pairs").len(), 6);
    assert_eq!(
        analysis["subjects"][0]["nearest_overall"]["subject_id"],
        subject_id(3)
    );
    assert_eq!(
        analysis["subjects"][0]["cross_note_ranking"][0]["subject_id"],
        subject_id(3)
    );
    assert_eq!(
        analysis["subjects"][0]["top_cross_note_neighbors"][0]["label"],
        "Rust ownership"
    );
    assert_eq!(
        analysis["subjects"][0]["top_cross_note_neighbors"][0]["fragments"][0]["text"],
        "Rust ownership"
    );
    assert_eq!(
        analysis["pairs"][0]["token_overlap"]["relationship"],
        "disjoint"
    );
    assert_eq!(
        fs::metadata(fixture.output_path.join("raw-vectors.f32le"))
            .expect("raw vectors")
            .len(),
        32
    );
    assert_eq!(
        fs::metadata(fixture.output_path.join("normalized-vectors.f32le"))
            .expect("normalized vectors")
            .len(),
        32
    );

    let before = snapshot_tree(&fixture.output_path);
    verify_sse_vector_diagnostic(&fixture.proposal_path, &fixture.output_path)
        .expect("verify published analysis");
    assert_eq!(
        snapshot_tree(&fixture.output_path),
        before,
        "verification must be read-only"
    );
}

#[test]
fn malformed_worker_rows_and_vectors_are_rejected_before_publication() {
    let out_of_order = Fixture::new();
    prepare_sse_worker_input(&out_of_order.proposal_path, &out_of_order.worker_input_path)
        .expect("prepare worker input");
    let request = fs::read(&out_of_order.worker_input_path).expect("read request");
    out_of_order.write_worker_result(&request);
    let mut receipt = read_json(&out_of_order.worker_receipt_path);
    receipt["rows"]
        .as_array_mut()
        .expect("receipt rows")
        .swap(0, 1);
    write_json(&out_of_order.worker_receipt_path, &receipt);
    let error = analyze_sse_vectors(
        &out_of_order.proposal_path,
        &out_of_order.worker_receipt_path,
        &out_of_order.raw_vectors_path,
        &out_of_order.output_path,
    )
    .expect_err("out-of-order rows must fail");
    assert!(error.to_string().contains("wrong identity"), "{error}");
    assert!(!out_of_order.output_path.exists());

    let bad_token = Fixture::new();
    prepare_sse_worker_input(&bad_token.proposal_path, &bad_token.worker_input_path)
        .expect("prepare worker input");
    let request = fs::read(&bad_token.worker_input_path).expect("read request");
    bad_token.write_worker_result(&request);
    let mut receipt = read_json(&bad_token.worker_receipt_path);
    receipt["rows"][0]["selected_token_indices"] = json!([5]);
    write_json(&bad_token.worker_receipt_path, &receipt);
    let error = analyze_sse_vectors(
        &bad_token.proposal_path,
        &bad_token.worker_receipt_path,
        &bad_token.raw_vectors_path,
        &bad_token.output_path,
    )
    .expect_err("out-of-range token index must fail");
    assert!(
        error.to_string().contains("selected token indices"),
        "{error}"
    );
    assert!(!bad_token.output_path.exists());

    for first_row in [[f32::NAN, 0.0], [0.0, 0.0]] {
        let fixture = Fixture::new();
        prepare_sse_worker_input(&fixture.proposal_path, &fixture.worker_input_path)
            .expect("prepare worker input");
        let request = fs::read(&fixture.worker_input_path).expect("read request");
        fixture.write_worker_result(&request);
        let mut raw = fs::read(&fixture.raw_vectors_path).expect("read raw vectors");
        raw[..4].copy_from_slice(&first_row[0].to_le_bytes());
        raw[4..8].copy_from_slice(&first_row[1].to_le_bytes());
        fs::write(&fixture.raw_vectors_path, &raw).expect("rewrite raw vectors");
        let mut receipt = read_json(&fixture.worker_receipt_path);
        receipt["files"]["raw-vectors.f32le"]["sha256"] = json!(sha256(&raw));
        write_json(&fixture.worker_receipt_path, &receipt);
        let error = analyze_sse_vectors(
            &fixture.proposal_path,
            &fixture.worker_receipt_path,
            &fixture.raw_vectors_path,
            &fixture.output_path,
        )
        .expect_err("invalid vector must fail");
        assert!(
            error.to_string().contains("non-finite") || error.to_string().contains("zero-norm"),
            "{error}"
        );
        assert!(!fixture.output_path.exists());
    }
}

struct Fixture {
    _temporary: tempfile::TempDir,
    proposal_path: PathBuf,
    worker_input_path: PathBuf,
    worker_receipt_path: PathBuf,
    raw_vectors_path: PathBuf,
    output_path: PathBuf,
}

impl Fixture {
    fn new() -> Self {
        let temporary = tempfile::tempdir().expect("create fixture directory");
        let sample_path = temporary.path().join("sample.jsonl");
        let note_set_path = temporary.path().join("note-set.json");
        let proposal_path = temporary.path().join("proposal.json");
        let worker_input_path = temporary.path().join("worker-input.json");
        let worker_receipt_path = temporary.path().join("worker-receipt.json");
        let raw_vectors_path = temporary.path().join("raw-vectors.f32le");
        let output_path = temporary.path().join("analysis");
        let rows = [
            json!({
                "split": "learning",
                "note_id": note_id(1),
                "pubkey": note_id(101),
                "content": "Rust and beach."
            }),
            json!({
                "split": "learning",
                "note_id": note_id(2),
                "pubkey": note_id(102),
                "content": "Rust ownership."
            }),
            json!({
                "split": "learning",
                "note_id": note_id(3),
                "pubkey": note_id(103),
                "content": "Coffee at the beach."
            }),
        ];
        let mut sample = rows
            .iter()
            .map(Value::to_string)
            .collect::<Vec<_>>()
            .join("\n");
        sample.push('\n');
        fs::write(&sample_path, sample.as_bytes()).expect("write sample");
        write_json(
            &note_set_path,
            &json!({
                "schema_version": 2,
                "status": "approved",
                "source": {
                    "path": "sample.jsonl",
                    "sha256": sha256(sample.as_bytes())
                },
                "note_ids": [note_id(1), note_id(2), note_id(3)],
                "invariants": {
                    "note_count": 3,
                    "unique_note_count": 3,
                    "unique_author_count": 3,
                    "required_split": "learning"
                }
            }),
        );
        write_json(
            &proposal_path,
            &json!({
                "schema_version": 2,
                "proposal_id": "diagnostic-test",
                "note_set": {
                    "path": "note-set.json",
                    "sha256": sha256(&fs::read(&note_set_path).expect("read note set"))
                },
                "subject_instruction": SUBJECT_INSTRUCTION,
                "mask_instruction": MASK_INSTRUCTION,
                "notes": [
                    {
                        "note_id": note_id(1),
                        "subjects": [
                            {
                                "subject_id": subject_id(1),
                                "label": "Rust programming",
                                "status": "masked",
                                "fragments": [{"text": "Rust", "occurrence": 1}]
                            },
                            {
                                "subject_id": subject_id(2),
                                "label": "Beaches",
                                "status": "masked",
                                "fragments": [{"text": "beach", "occurrence": 1}]
                            }
                        ]
                    },
                    {
                        "note_id": note_id(2),
                        "subjects": [{
                            "subject_id": subject_id(3),
                            "label": "Rust ownership",
                            "status": "masked",
                            "fragments": [{"text": "Rust ownership", "occurrence": 1}]
                        }]
                    },
                    {
                        "note_id": note_id(3),
                        "subjects": [{
                            "subject_id": subject_id(4),
                            "label": "Visiting a beach",
                            "status": "masked",
                            "fragments": [{"text": "the beach", "occurrence": 1}]
                        }]
                    }
                ]
            }),
        );
        Self {
            _temporary: temporary,
            proposal_path,
            worker_input_path,
            worker_receipt_path,
            raw_vectors_path,
            output_path,
        }
    }

    fn write_worker_result(&self, worker_input_bytes: &[u8]) {
        let raw = [3.0_f32, 0.0, 0.0, 4.0, 1.0, 0.0, 0.0, 2.0]
            .into_iter()
            .flat_map(f32::to_le_bytes)
            .collect::<Vec<_>>();
        fs::write(&self.raw_vectors_path, &raw).expect("write raw vectors");
        write_json(
            &self.worker_receipt_path,
            &json!({
                "schema_version": 1,
                "proposal_sha256": sha256(
                    &fs::read(&self.proposal_path).expect("read proposal")
                ),
                "request_sha256": sha256(worker_input_bytes),
                "checkpoint_sha256": "1".repeat(64),
                "base_model_artifact_tree_sha256": "2".repeat(64),
                "tree_hash_rule": "sorted-relative-path-type-size-content-sha256-v1",
                "model": {
                    "base_model": "fixture/base",
                    "dimensions": 2,
                    "maximum_tokens": 512,
                    "pooling": "selected-contextual-token-mean-linear-relu-linear-v1"
                },
                "runtime": {"python": "fixture"},
                "device": "cpu",
                "container_image": "fixture/sse@sha256:".to_owned() + &"ef".repeat(32),
                "note_batch_size": 3,
                "vector_format": "row-major-f32le-v1",
                "dimensions": 2,
                "row_count": 4,
                "rows": [
                    {
                        "ordinal": 0,
                        "note_id": note_id(1),
                        "subject_id": subject_id(1),
                        "token_count": 5,
                        "selected_token_indices": [1]
                    },
                    {
                        "ordinal": 1,
                        "note_id": note_id(1),
                        "subject_id": subject_id(2),
                        "token_count": 5,
                        "selected_token_indices": [3]
                    },
                    {
                        "ordinal": 2,
                        "note_id": note_id(2),
                        "subject_id": subject_id(3),
                        "token_count": 4,
                        "selected_token_indices": [1, 2]
                    },
                    {
                        "ordinal": 3,
                        "note_id": note_id(3),
                        "subject_id": subject_id(4),
                        "token_count": 5,
                        "selected_token_indices": [4]
                    }
                ],
                "files": {
                    "raw-vectors.f32le": {
                        "bytes": raw.len(),
                        "sha256": sha256(&raw)
                    }
                }
            }),
        );
    }
}

fn note_id(value: u64) -> String {
    format!("{value:064x}")
}

fn subject_id(value: u64) -> String {
    format!("{value:016x}")
}

fn write_json(path: &Path, value: &Value) {
    let mut bytes = serde_json::to_vec_pretty(value).expect("encode JSON");
    bytes.push(b'\n');
    fs::write(path, bytes).expect("write JSON");
}

fn read_json(path: &Path) -> Value {
    serde_json::from_slice(&fs::read(path).expect("read JSON")).expect("decode JSON")
}

fn sha256(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}

fn snapshot_tree(root: &Path) -> Vec<(PathBuf, Vec<u8>)> {
    let mut files = Vec::new();
    let mut pending = vec![root.to_owned()];
    while let Some(path) = pending.pop() {
        let mut entries = fs::read_dir(&path)
            .expect("read artifact directory")
            .map(|entry| entry.expect("directory entry").path())
            .collect::<Vec<_>>();
        entries.sort();
        for entry in entries {
            if entry.is_dir() {
                pending.push(entry);
            } else {
                files.push((
                    entry.strip_prefix(root).expect("relative path").to_owned(),
                    fs::read(entry).expect("read artifact file"),
                ));
            }
        }
    }
    files.sort_by(|left, right| left.0.cmp(&right.0));
    files
}
