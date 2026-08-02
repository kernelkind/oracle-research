use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::io::Write as _;
use std::path::{Path, PathBuf};

use oracle_mvp::sse_context_counterfactual::{
    analyze_sse_context_counterfactual, prepare_sse_context_counterfactual,
    verify_sse_context_counterfactual,
};
use oracle_mvp::sse_vector_diagnostic::{
    SseFileIdentity, SseWorkerInput, SseWorkerModel, SseWorkerReceipt, SseWorkerReceiptRow,
};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use tempfile::TempDir;

const DIMENSIONS: usize = 768;
const TARGET_COUNT: usize = 24;
const REFERENCE_COUNT: usize = 57;
const ROW_COUNT: usize = TARGET_COUNT + REFERENCE_COUNT;

#[test]
fn prepare_compiles_the_approved_fixture_into_one_label_free_worker_request() {
    let temporary = TempDir::new().expect("temporary directory");
    let first = temporary.path().join("first");
    let second = temporary.path().join("second");

    let manifest = prepare_sse_context_counterfactual(fixture_path(), &first)
        .expect("approved fixture should compile");
    let replay = prepare_sse_context_counterfactual(fixture_path(), &second)
        .expect("approved fixture should compile deterministically");

    assert_eq!(manifest, replay);
    assert_eq!(manifest.note_count, 74);
    assert_eq!(manifest.target_count, TARGET_COUNT);
    assert_eq!(manifest.reference_count, REFERENCE_COUNT);
    assert_eq!(manifest.rows.len(), ROW_COUNT);
    let fixture_value: Value =
        serde_json::from_slice(&fs::read(fixture_path()).expect("fixture")).expect("fixture JSON");
    assert_eq!(
        fixture_value["source_artifacts"],
        json!([{
            "path": "sse_multivector/context-counterfactual-source-notes-v1.json",
            "path_base": "repository root",
            "sha256": "080cc4b7ea8934e7361ac17bda3d73c53d75f0338a1f0884fddb6acefe0f7cc8",
            "provides": "the complete text of every real source note named by the frozen fixture"
        }]),
        "the committed fixture must not depend on ignored target artifacts"
    );
    let source_evidence: Value = serde_json::from_slice(
        &fs::read(
            Path::new(env!("CARGO_MANIFEST_DIR"))
                .join("sse_multivector/context-counterfactual-source-notes-v1.json"),
        )
        .expect("committed source evidence"),
    )
    .expect("source evidence JSON");
    let declared_source_ids = fixture_value["source_notes"]
        .as_array()
        .expect("declared source notes")
        .iter()
        .map(|note| note["note_id"].as_str().expect("declared source ID"))
        .collect::<BTreeSet<_>>();
    let evidenced_source_ids = source_evidence["notes"]
        .as_array()
        .expect("evidenced source notes")
        .iter()
        .map(|note| {
            assert!(!note["text"].as_str().expect("source text").is_empty());
            note["note_id"].as_str().expect("evidenced source ID")
        })
        .collect::<BTreeSet<_>>();
    assert_eq!(evidenced_source_ids, declared_source_ids);
    assert_eq!(
        manifest.fixture_sha256,
        "3a791d395234b5ab4b9304c2c399480b94bf7244febf05f73390c95bf6cc8c48"
    );
    assert_eq!(
        manifest.worker_sha256,
        "fe4dc92d834c5aa6e2c15072cd2cb57db3c03ea0062cde32bcb84b4a466f9421"
    );
    assert_eq!(
        manifest.execution.checkpoint_sha256,
        "ef9d34ca38f04fc30b2879fa365d07cd8264dc2cd3f5c24084533fe18535ad1d"
    );
    assert_eq!(
        manifest.execution.base_model_artifact_tree_sha256,
        "bba50abbbb7de6165ee3828c4e4abb0c88a6386bd4754374469246cde5017e5d"
    );
    assert_eq!(manifest.execution.dimensions, DIMENSIONS as u32);
    assert_eq!(manifest.execution.maximum_tokens, 512);
    assert_eq!(manifest.execution.note_batch_size, 8);
    assert_eq!(manifest.execution.device, "cpu");
    assert_eq!(
        manifest.execution.container_image,
        "local/oracle-mvp-sse@sha256:a6c9674dca720e1f094b7feeb1397b6e6b0a97e10f13e0a6555deebf4b70ddaa"
    );

    for name in [
        "worker-input.json",
        "worker-config.json",
        "compile-manifest.json",
    ] {
        assert_eq!(
            fs::read(first.join(name)).expect("first prepared file"),
            fs::read(second.join(name)).expect("second prepared file"),
            "{name} must be deterministic"
        );
    }
    let first_request = fs::read(first.join("worker-input.json")).expect("worker input");
    let request: SseWorkerInput =
        serde_json::from_slice(&first_request).expect("valid worker request");
    let expected = expected_compilation();
    assert_eq!(request.notes.len(), expected.notes.len());
    assert_eq!(manifest.rows.len(), expected.rows.len());
    assert_eq!(request.proposal_sha256, manifest.fixture_sha256);
    for (actual, expected) in request.notes.iter().zip(&expected.notes) {
        assert_eq!(actual.note_id, expected.note_id);
        assert_eq!(actual.text, expected.text);
        assert_eq!(actual.subjects.len(), expected.subjects.len());
        for (actual, expected) in actual.subjects.iter().zip(&expected.subjects) {
            assert_eq!(actual.subject_id, expected.subject_id);
            assert_eq!(actual.byte_spans, expected.byte_spans);
        }
    }
    assert_eq!(
        request.notes[0].note_id,
        "179aa6aa7fbd6d85b54588751e7ea3f25331539c1e3e5d4ef3cbe375026b6a16"
    );
    assert_eq!(request.notes[0].subjects[0].subject_id, "a4c6866fd80f5271");
    assert_eq!(
        request.notes[15].note_id,
        "edeccb039e8fe17952dfb9f2d4f92f760fe7137d7dbf9c434892f1b0d321094a"
    );
    assert_eq!(request.notes[15].subjects[4].byte_spans, vec![[353, 497]]);
    assert_eq!(
        request.notes[17].note_id,
        "2f56023ba0236dd5411221a0ab74f4f3fd9030327bb718f6a8c862e51344ee41"
    );
    assert_eq!(request.notes[17].subjects[0].subject_id, "1b8387e8f9565053");
    for (actual, expected) in manifest.rows.iter().zip(&expected.rows) {
        assert_eq!(actual.ordinal, expected.ordinal);
        assert_eq!(actual.note_id, expected.note_id);
        assert_eq!(actual.subject_id, expected.subject_id);
        assert_eq!(actual.target_id, expected.target_id);
        assert_eq!(actual.preferred_group_id, expected.preferred_group_id);
        assert_eq!(actual.alternative_group_ids, expected.alternative_group_ids);
        assert_eq!(actual.reference_group_id, expected.reference_group_id);
        assert_eq!(actual.reference_index, expected.reference_index);
    }

    let note_ids = request
        .notes
        .iter()
        .map(|note| note.note_id.as_str())
        .collect::<BTreeSet<_>>();
    let subject_ids = request
        .notes
        .iter()
        .flat_map(|note| {
            note.subjects
                .iter()
                .map(|subject| subject.subject_id.as_str())
        })
        .collect::<BTreeSet<_>>();
    assert_eq!(note_ids.len(), 74);
    assert_eq!(subject_ids.len(), ROW_COUNT);
    assert!(
        note_ids
            .iter()
            .all(|identifier| is_lower_hex(identifier, 64))
    );
    assert!(
        subject_ids
            .iter()
            .all(|identifier| is_lower_hex(identifier, 16))
    );

    let request_value: Value = serde_json::from_slice(&first_request).expect("worker request JSON");
    assert_no_keys(
        &request_value,
        &[
            "label",
            "preferred_group_id",
            "alternative_group_ids",
            "reference_group_id",
            "target_id",
            "verdicts",
        ],
    );

    let before_no_replace = directory_hashes(&first);
    prepare_sse_context_counterfactual(fixture_path(), &first)
        .expect_err("prepare must never replace an existing artifact");
    assert_eq!(directory_hashes(&first), before_no_replace);

    let unauthorized_fixture = temporary.path().join("unauthorized.json");
    let mut unauthorized: Value =
        serde_json::from_slice(&fs::read(fixture_path()).expect("approved fixture"))
            .expect("fixture JSON");
    unauthorized["review_status"] = Value::String("proposed".to_owned());
    unauthorized["inference_authorized"] = Value::Bool(false);
    fs::write(
        &unauthorized_fixture,
        serde_json::to_vec_pretty(&unauthorized).expect("unauthorized fixture"),
    )
    .expect("write unauthorized fixture");
    let unauthorized_output = temporary.path().join("unauthorized-output");
    prepare_sse_context_counterfactual(&unauthorized_fixture, &unauthorized_output)
        .expect_err("unapproved fixture must not compile");
    assert!(!unauthorized_output.exists());

    let fixture_directory = fixture_path().parent().unwrap().to_owned();
    let mut changed_fixture =
        tempfile::NamedTempFile::new_in(fixture_directory).expect("changed fixture file");
    let mut changed: Value =
        serde_json::from_slice(&fs::read(fixture_path()).expect("approved fixture"))
            .expect("fixture JSON");
    changed["question"] = Value::String("Unapproved changed scientific question".to_owned());
    changed_fixture
        .write_all(&serde_json::to_vec_pretty(&changed).expect("changed fixture JSON"))
        .expect("write changed fixture");
    changed_fixture.flush().expect("flush changed fixture");
    let changed_output = temporary.path().join("changed-approved-output");
    prepare_sse_context_counterfactual(changed_fixture.path(), &changed_output)
        .expect_err("self-declared approval must not authorize a changed fixture");
    assert!(!changed_output.exists());
}

#[test]
fn analyze_uses_all_reference_scores_strict_medians_and_declared_verdict_dependencies() {
    let temporary = TempDir::new().expect("temporary directory");
    let prepared = temporary.path().join("prepared");
    prepare_sse_context_counterfactual(fixture_path(), &prepared)
        .expect("approved fixture should compile");
    let expected = expected_compilation();

    let passing_worker = temporary.path().join("passing-worker");
    write_synthetic_worker_output(&prepared, &passing_worker, &expected, None);
    let passing_output = temporary.path().join("passing-analysis");
    let passing = analyze_sse_context_counterfactual(
        fixture_path(),
        &prepared,
        &passing_worker,
        &passing_output,
    )
    .expect("controlled preferred vectors should pass");

    assert_eq!(passing.target_reference_cosine_count, 1_368);
    assert_eq!(passing.group_median_count, 456);
    assert_eq!(passing.predictions.len(), TARGET_COUNT);
    assert!(
        passing
            .predictions
            .iter()
            .all(|prediction| prediction.passed)
    );
    assert!(passing.verdicts.values().all(|verdict| verdict.passed));
    assert!(passing.verdicts["overall"].passed);
    assert_eq!(
        passing
            .verdicts
            .keys()
            .map(String::as_str)
            .collect::<BTreeSet<_>>(),
        BTreeSet::from([
            "context_grounded",
            "mixed_note_separation",
            "not_blended",
            "overall",
            "self_contained_baseline",
            "unrelated_context_resistance",
        ])
    );
    let expected_target_ids = expected
        .rows
        .iter()
        .filter_map(|row| row.target_id.clone())
        .collect::<Vec<_>>();
    assert_eq!(
        passing
            .predictions
            .iter()
            .map(|prediction| prediction.target_id.clone())
            .collect::<Vec<_>>(),
        expected_target_ids
    );
    assert_eq!(
        passing
            .predictions
            .iter()
            .map(|prediction| prediction.comparisons.len())
            .sum::<usize>(),
        56
    );
    assert_eq!(passing.predictions[0].reference_cosines.len(), 19);
    assert_eq!(passing.predictions[0].group_medians.len(), 19);
    assert_eq!(passing.predictions[0].comparisons.len(), 2);
    let preferred_scores = &passing.predictions[0].reference_cosines["self-directed-authenticity"];
    assert_eq!(preferred_scores.len(), 3);
    for (score, expected_reference) in preferred_scores.iter().zip(
        expected
            .rows
            .iter()
            .filter(|row| row.reference_group_id.as_deref() == Some("self-directed-authenticity")),
    ) {
        assert_eq!(
            score.reference_index,
            expected_reference.reference_index.unwrap()
        );
        assert_eq!(score.reference_note_id, expected_reference.note_id);
        assert_eq!(score.reference_subject_id, expected_reference.subject_id);
    }
    let expected_scores =
        [0.3_f32, 0.1_f32, 0.2_f32].map(|context| 1.0 / (1.0 + f64::from(context).powi(2)).sqrt());
    for (actual, expected) in preferred_scores.iter().zip(expected_scores) {
        assert_eq!(actual.cosine, expected);
    }
    assert_eq!(passing.predictions[0].preferred_median, expected_scores[2]);
    assert_eq!(
        passing.predictions[0].group_medians["coffee-with-raw-cream-and-yolk"],
        0.0
    );
    assert_eq!(
        passing
            .predictions
            .iter()
            .flat_map(|prediction| prediction.reference_cosines.values())
            .map(Vec::len)
            .sum::<usize>(),
        1_368
    );
    assert_eq!(
        verify_sse_context_counterfactual(fixture_path(), &passing_output)
            .expect("published result should replay"),
        passing
    );
    let analysis_path = passing_output.join("analysis.json");
    let mut corrupted_analysis = fs::read(&analysis_path).expect("analysis JSON");
    corrupted_analysis.push(b' ');
    fs::write(&analysis_path, corrupted_analysis).expect("tamper analysis");
    let before_failed_verify = directory_hashes(&passing_output);
    verify_sse_context_counterfactual(fixture_path(), &passing_output)
        .expect_err("verification must detect a changed analysis");
    assert_eq!(
        directory_hashes(&passing_output),
        before_failed_verify,
        "verification must remain read-only"
    );

    let tied_worker = temporary.path().join("tied-worker");
    write_synthetic_worker_output(
        &prepared,
        &tied_worker,
        &expected,
        Some(("autonomy-alone", "coffee-with-raw-cream-and-yolk")),
    );
    let tied_output = temporary.path().join("tied-analysis");
    let tied =
        analyze_sse_context_counterfactual(fixture_path(), &prepared, &tied_worker, &tied_output)
            .expect("a semantic failure should still publish complete evidence");
    let prediction = tied
        .predictions
        .iter()
        .find(|prediction| prediction.target_id == "autonomy-alone")
        .expect("controlled target");
    assert!(
        !prediction.passed,
        "equal medians must fail strict comparison"
    );
    assert_eq!(
        prediction.preferred_median,
        prediction.group_medians["coffee-with-raw-cream-and-yolk"]
    );
    assert!(!tied.verdicts["self_contained_baseline"].passed);
    assert!(!tied.verdicts["unrelated_context_resistance"].passed);
    assert!(!tied.verdicts["not_blended"].passed);
    assert!(!tied.verdicts["overall"].passed);
    assert_eq!(
        verify_sse_context_counterfactual(fixture_path(), &tied_output)
            .expect("semantic failure evidence should replay"),
        tied
    );

    assert_dependency_failure(
        temporary.path(),
        &prepared,
        &expected,
        "retirement-greenhouse-context",
        "minimalism-enabled-retirement",
        &["context_grounded", "overall"],
        &[
            "self_contained_baseline",
            "unrelated_context_resistance",
            "mixed_note_separation",
            "not_blended",
        ],
    );
    assert_dependency_failure(
        temporary.path(),
        &prepared,
        &expected,
        "mixed-public-private-agreement",
        "persistent-wren-chirping",
        &["mixed_note_separation", "not_blended", "overall"],
        &[
            "self_contained_baseline",
            "unrelated_context_resistance",
            "context_grounded",
        ],
    );
}

#[test]
fn malformed_worker_output_is_rejected_without_publishing_any_analysis() {
    let temporary = TempDir::new().expect("temporary directory");
    let prepared = temporary.path().join("prepared");
    prepare_sse_context_counterfactual(fixture_path(), &prepared)
        .expect("approved fixture should compile");
    let expected = expected_compilation();
    let worker = temporary.path().join("worker");
    write_synthetic_worker_output(&prepared, &worker, &expected, None);

    let receipt_path = worker.join("worker-receipt.json");
    let mut receipt: Value =
        serde_json::from_slice(&fs::read(&receipt_path).expect("receipt")).expect("receipt JSON");
    receipt["request_sha256"] = Value::String("0".repeat(64));
    fs::write(
        &receipt_path,
        serde_json::to_vec_pretty(&receipt).expect("encode malformed receipt"),
    )
    .expect("write malformed receipt");

    let output = temporary.path().join("analysis");
    let error = analyze_sse_context_counterfactual(fixture_path(), &prepared, &worker, &output)
        .expect_err("unbound worker receipt must fail");
    assert!(error.to_string().contains("worker"));
    assert!(!output.exists(), "invalid inputs must publish nothing");

    let wrong_pin_worker = temporary.path().join("wrong-pin-worker");
    write_synthetic_worker_output(&prepared, &wrong_pin_worker, &expected, None);
    let wrong_pin_receipt_path = wrong_pin_worker.join("worker-receipt.json");
    let mut wrong_pin_receipt: SseWorkerReceipt =
        serde_json::from_slice(&fs::read(&wrong_pin_receipt_path).expect("wrong-pin receipt"))
            .expect("wrong-pin receipt JSON");
    wrong_pin_receipt.checkpoint_sha256 = "1".repeat(64);
    let mut wrong_pin_bytes =
        serde_json::to_vec_pretty(&wrong_pin_receipt).expect("wrong-pin receipt encoding");
    wrong_pin_bytes.push(b'\n');
    fs::write(&wrong_pin_receipt_path, wrong_pin_bytes).expect("write wrong pin");
    let wrong_pin_output = temporary.path().join("wrong-pin-analysis");
    analyze_sse_context_counterfactual(
        fixture_path(),
        &prepared,
        &wrong_pin_worker,
        &wrong_pin_output,
    )
    .expect_err("a syntactically valid but unpinned checkpoint must fail");
    assert!(!wrong_pin_output.exists());

    let missing_worker_pin = temporary.path().join("missing-worker-pin");
    write_synthetic_worker_output(&prepared, &missing_worker_pin, &expected, None);
    let missing_worker_receipt_path = missing_worker_pin.join("worker-receipt.json");
    let mut missing_worker_receipt: SseWorkerReceipt = serde_json::from_slice(
        &fs::read(&missing_worker_receipt_path).expect("missing-worker receipt"),
    )
    .expect("missing-worker receipt JSON");
    missing_worker_receipt
        .runtime
        .as_object_mut()
        .expect("runtime object")
        .remove("worker_sha256");
    let mut missing_worker_bytes =
        serde_json::to_vec_pretty(&missing_worker_receipt).expect("missing-worker encoding");
    missing_worker_bytes.push(b'\n');
    fs::write(&missing_worker_receipt_path, missing_worker_bytes)
        .expect("write missing worker pin");
    let missing_worker_output = temporary.path().join("missing-worker-analysis");
    analyze_sse_context_counterfactual(
        fixture_path(),
        &prepared,
        &missing_worker_pin,
        &missing_worker_output,
    )
    .expect_err("worker output must bind the exact worker source");
    assert!(!missing_worker_output.exists());

    let zero_worker = temporary.path().join("zero-worker");
    write_synthetic_worker_output(&prepared, &zero_worker, &expected, None);
    zero_first_vector(&zero_worker);
    let zero_output = temporary.path().join("zero-analysis");
    analyze_sse_context_counterfactual(fixture_path(), &prepared, &zero_worker, &zero_output)
        .expect_err("zero-norm vector must fail");
    assert!(
        !zero_output.exists(),
        "invalid vectors must publish nothing"
    );

    let nonfinite_worker = temporary.path().join("nonfinite-worker");
    write_synthetic_worker_output(&prepared, &nonfinite_worker, &expected, None);
    set_first_coordinate(&nonfinite_worker, f32::NAN);
    let nonfinite_output = temporary.path().join("nonfinite-analysis");
    analyze_sse_context_counterfactual(
        fixture_path(),
        &prepared,
        &nonfinite_worker,
        &nonfinite_output,
    )
    .expect_err("non-finite vector must fail");
    assert!(!nonfinite_output.exists());
}

fn fixture_path() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR")).join("sse_multivector/context-counterfactual-v1.json")
}

#[derive(Debug)]
struct ExpectedCompilation {
    notes: Vec<ExpectedNote>,
    rows: Vec<ExpectedRow>,
}

#[derive(Debug)]
struct ExpectedNote {
    note_id: String,
    text: String,
    subjects: Vec<ExpectedSubject>,
}

#[derive(Debug)]
struct ExpectedSubject {
    subject_id: String,
    byte_spans: Vec<[usize; 2]>,
}

#[derive(Debug)]
struct ExpectedRow {
    ordinal: usize,
    note_id: String,
    subject_id: String,
    target_id: Option<String>,
    preferred_group_id: String,
    alternative_group_ids: Vec<String>,
    reference_group_id: Option<String>,
    reference_index: Option<usize>,
}

fn expected_compilation() -> ExpectedCompilation {
    let fixture_bytes = fs::read(fixture_path()).expect("fixture");
    let fixture: Value = serde_json::from_slice(&fixture_bytes).expect("fixture JSON");
    let fixture_id = fixture["fixture_id"].as_str().expect("fixture ID");
    let mut notes = Vec::new();
    let mut rows = Vec::new();

    for case in fixture["self_contained_cases"]
        .as_array()
        .expect("self-contained cases")
    {
        let preferred = case["target_group_id"].as_str().expect("target group");
        let alternatives = strings(&case["alternative_group_ids"]);
        for variant in case["variants"].as_array().expect("variants") {
            push_expected_target_note(
                fixture_id,
                variant,
                variant["fixture_note_id"].as_str().expect("target ID"),
                preferred,
                alternatives.clone(),
                &mut notes,
                &mut rows,
            );
        }
    }
    for case in fixture["context_resolution_cases"]
        .as_array()
        .expect("context cases")
    {
        for variant in case["variants"].as_array().expect("variants") {
            push_expected_target_note(
                fixture_id,
                variant,
                variant["fixture_note_id"].as_str().expect("target ID"),
                variant["preferred_group_id"]
                    .as_str()
                    .expect("preferred group"),
                strings(&variant["alternative_group_ids"]),
                &mut notes,
                &mut rows,
            );
        }
    }
    for case in fixture["mixed_note_cases"].as_array().expect("mixed cases") {
        let fixture_note_id = case["fixture_note_id"].as_str().expect("fixture note ID");
        let text = case["text"].as_str().expect("mixed text").to_owned();
        let note_id = stable_id(
            "oracle-mvp-sse-context-counterfactual-note-id-v1\0",
            &[fixture_id, "target", fixture_note_id],
            32,
        );
        let mut subjects = Vec::new();
        for meaning in case["meanings"].as_array().expect("meanings") {
            let target_id = meaning["meaning_id"].as_str().expect("meaning ID");
            let subject_id = stable_id(
                "oracle-mvp-sse-context-counterfactual-subject-id-v1\0",
                &[fixture_id, "target", target_id],
                8,
            );
            subjects.push(ExpectedSubject {
                subject_id: subject_id.clone(),
                byte_spans: expected_spans(&text, &meaning["mask"]),
            });
            rows.push(ExpectedRow {
                ordinal: rows.len(),
                note_id: note_id.clone(),
                subject_id,
                target_id: Some(target_id.to_owned()),
                preferred_group_id: meaning["preferred_group_id"]
                    .as_str()
                    .expect("preferred group")
                    .to_owned(),
                alternative_group_ids: strings(&meaning["alternative_group_ids"]),
                reference_group_id: None,
                reference_index: None,
            });
        }
        notes.push(ExpectedNote {
            note_id,
            text,
            subjects,
        });
    }

    for group in fixture["reference_groups"]
        .as_array()
        .expect("reference groups")
    {
        let group_id = group["group_id"].as_str().expect("group ID");
        for (zero_index, reference) in group["references"]
            .as_array()
            .expect("references")
            .iter()
            .enumerate()
        {
            let reference_index = zero_index + 1;
            let index = reference_index.to_string();
            let fields = [fixture_id, "reference", group_id, index.as_str()];
            let note_id = stable_id(
                "oracle-mvp-sse-context-counterfactual-note-id-v1\0",
                &fields,
                32,
            );
            let subject_id = stable_id(
                "oracle-mvp-sse-context-counterfactual-subject-id-v1\0",
                &fields,
                8,
            );
            let text = reference.as_str().expect("reference text").to_owned();
            notes.push(ExpectedNote {
                note_id: note_id.clone(),
                text: text.clone(),
                subjects: vec![ExpectedSubject {
                    subject_id: subject_id.clone(),
                    byte_spans: vec![[0, text.len()]],
                }],
            });
            rows.push(ExpectedRow {
                ordinal: rows.len(),
                note_id,
                subject_id,
                target_id: None,
                preferred_group_id: String::new(),
                alternative_group_ids: Vec::new(),
                reference_group_id: Some(group_id.to_owned()),
                reference_index: Some(reference_index),
            });
        }
    }
    ExpectedCompilation { notes, rows }
}

#[allow(clippy::too_many_arguments)]
fn push_expected_target_note(
    fixture_id: &str,
    variant: &Value,
    target_id: &str,
    preferred_group_id: &str,
    alternative_group_ids: Vec<String>,
    notes: &mut Vec<ExpectedNote>,
    rows: &mut Vec<ExpectedRow>,
) {
    let fixture_note_id = variant["fixture_note_id"]
        .as_str()
        .expect("fixture note ID");
    let text = variant["text"].as_str().expect("target text").to_owned();
    let note_id = stable_id(
        "oracle-mvp-sse-context-counterfactual-note-id-v1\0",
        &[fixture_id, "target", fixture_note_id],
        32,
    );
    let subject_id = stable_id(
        "oracle-mvp-sse-context-counterfactual-subject-id-v1\0",
        &[fixture_id, "target", target_id],
        8,
    );
    notes.push(ExpectedNote {
        note_id: note_id.clone(),
        text: text.clone(),
        subjects: vec![ExpectedSubject {
            subject_id: subject_id.clone(),
            byte_spans: expected_spans(&text, &variant["mask"]),
        }],
    });
    rows.push(ExpectedRow {
        ordinal: rows.len(),
        note_id,
        subject_id,
        target_id: Some(target_id.to_owned()),
        preferred_group_id: preferred_group_id.to_owned(),
        alternative_group_ids,
        reference_group_id: None,
        reference_index: None,
    });
}

fn expected_spans(text: &str, masks: &Value) -> Vec<[usize; 2]> {
    masks
        .as_array()
        .expect("mask array")
        .iter()
        .map(|mask| {
            let fragment = mask["text"].as_str().expect("mask text");
            let occurrence = mask["occurrence"].as_u64().expect("occurrence") as usize;
            let start = text
                .match_indices(fragment)
                .nth(occurrence - 1)
                .expect("declared occurrence")
                .0;
            [start, start + fragment.len()]
        })
        .collect()
}

fn strings(value: &Value) -> Vec<String> {
    value
        .as_array()
        .expect("string array")
        .iter()
        .map(|value| value.as_str().expect("string").to_owned())
        .collect()
}

fn stable_id(domain: &str, fields: &[&str], digest_bytes: usize) -> String {
    let mut digest = Sha256::new();
    digest.update(domain.as_bytes());
    for field in fields {
        digest.update((field.len() as u64).to_be_bytes());
        digest.update(field.as_bytes());
    }
    let encoded = format!("{:x}", digest.finalize());
    encoded[..digest_bytes * 2].to_owned()
}

fn write_synthetic_worker_output(
    prepared: &Path,
    output: &Path,
    expected: &ExpectedCompilation,
    tie: Option<(&str, &str)>,
) {
    fs::create_dir(output).expect("worker output directory");
    let request_bytes = fs::read(prepared.join("worker-input.json")).expect("worker input");
    let request: SseWorkerInput =
        serde_json::from_slice(&request_bytes).expect("worker input JSON");
    let reference_group_indices = expected
        .rows
        .iter()
        .filter_map(|row| row.reference_group_id.as_deref())
        .collect::<BTreeSet<_>>()
        .into_iter()
        .enumerate()
        .map(|(index, group)| (group.to_owned(), index))
        .collect::<BTreeMap<_, _>>();

    let mut values = Vec::with_capacity(ROW_COUNT * DIMENSIONS);
    for row in &expected.rows {
        let mut vector = vec![0.0_f32; DIMENSIONS];
        if let Some(target_id) = &row.target_id {
            let preferred = reference_group_indices[&row.preferred_group_id];
            vector[preferred] = 1.0;
            if let Some((controlled_target, alternative_group)) = tie
                && target_id == controlled_target
            {
                vector[reference_group_indices[alternative_group]] = 1.0;
            }
        } else {
            vector[reference_group_indices[row.reference_group_id.as_ref().unwrap()]] = 1.0;
            let reference_index = row.reference_index.expect("reference index");
            vector[DIMENSIONS - 1] = [0.3, 0.1, 0.2][reference_index - 1];
        }
        values.extend(vector);
    }
    let raw_bytes = values
        .iter()
        .flat_map(|value| value.to_le_bytes())
        .collect::<Vec<_>>();
    fs::write(output.join("raw-vectors.f32le"), &raw_bytes).expect("raw vectors");

    let rows = request
        .notes
        .iter()
        .flat_map(|note| {
            note.subjects
                .iter()
                .map(|subject| (note.note_id.clone(), subject.subject_id.clone()))
        })
        .enumerate()
        .map(|(ordinal, (note_id, subject_id))| SseWorkerReceiptRow {
            ordinal,
            note_id,
            subject_id,
            token_count: 1,
            selected_token_indices: vec![0],
        })
        .collect::<Vec<_>>();
    let receipt = SseWorkerReceipt {
        schema_version: 1,
        proposal_sha256: request.proposal_sha256,
        request_sha256: sha256(&request_bytes),
        checkpoint_sha256: "ef9d34ca38f04fc30b2879fa365d07cd8264dc2cd3f5c24084533fe18535ad1d"
            .to_owned(),
        base_model_artifact_tree_sha256:
            "bba50abbbb7de6165ee3828c4e4abb0c88a6386bd4754374469246cde5017e5d"
                .to_owned(),
        tree_hash_rule: "sorted-relative-path-type-size-content-sha256-v1".to_owned(),
        model: SseWorkerModel {
            base_model: "sentence-transformers/sentence-t5-base".to_owned(),
            dimensions: DIMENSIONS as u32,
            maximum_tokens: 512,
            pooling: "selected-contextual-token-mean-linear-relu-linear-v1".to_owned(),
        },
        runtime: json!({
            "test_fixture": "controlled-orthogonal-v1",
            "worker_sha256": "fe4dc92d834c5aa6e2c15072cd2cb57db3c03ea0062cde32bcb84b4a466f9421"
        }),
        device: "cpu".to_owned(),
        container_image: "local/oracle-mvp-sse@sha256:a6c9674dca720e1f094b7feeb1397b6e6b0a97e10f13e0a6555deebf4b70ddaa".to_owned(),
        note_batch_size: 8,
        vector_format: "row-major-f32le-v1".to_owned(),
        dimensions: DIMENSIONS as u32,
        row_count: ROW_COUNT,
        rows,
        files: BTreeMap::from([(
            "raw-vectors.f32le".to_owned(),
            SseFileIdentity {
                bytes: raw_bytes.len() as u64,
                sha256: sha256(&raw_bytes),
            },
        )]),
    };
    let mut receipt_bytes = serde_json::to_vec_pretty(&receipt).expect("encode receipt");
    receipt_bytes.push(b'\n');
    fs::write(output.join("worker-receipt.json"), receipt_bytes).expect("worker receipt");
}

#[allow(clippy::too_many_arguments)]
fn assert_dependency_failure(
    root: &Path,
    prepared: &Path,
    expected: &ExpectedCompilation,
    target: &str,
    alternative: &str,
    failed_verdicts: &[&str],
    passing_verdicts: &[&str],
) {
    let worker = root.join(format!("{target}-worker"));
    write_synthetic_worker_output(prepared, &worker, expected, Some((target, alternative)));
    let output = root.join(format!("{target}-analysis"));
    let report = analyze_sse_context_counterfactual(fixture_path(), prepared, &worker, &output)
        .expect("semantic failure should publish evidence");
    for verdict in failed_verdicts {
        assert!(!report.verdicts[*verdict].passed, "{verdict} should fail");
    }
    for verdict in passing_verdicts {
        assert!(report.verdicts[*verdict].passed, "{verdict} should pass");
    }
}

fn zero_first_vector(worker: &Path) {
    let raw_path = worker.join("raw-vectors.f32le");
    let mut raw = fs::read(&raw_path).expect("raw vectors");
    raw[..DIMENSIONS * size_of::<f32>()].fill(0);
    fs::write(&raw_path, &raw).expect("zero vector");
    let receipt_path = worker.join("worker-receipt.json");
    let mut receipt: SseWorkerReceipt =
        serde_json::from_slice(&fs::read(&receipt_path).expect("receipt")).expect("worker receipt");
    receipt.files.insert(
        "raw-vectors.f32le".to_owned(),
        SseFileIdentity {
            bytes: raw.len() as u64,
            sha256: sha256(&raw),
        },
    );
    let mut receipt_bytes = serde_json::to_vec_pretty(&receipt).expect("encode receipt");
    receipt_bytes.push(b'\n');
    fs::write(receipt_path, receipt_bytes).expect("updated receipt");
}

fn set_first_coordinate(worker: &Path, value: f32) {
    let raw_path = worker.join("raw-vectors.f32le");
    let mut raw = fs::read(&raw_path).expect("raw vectors");
    raw[..size_of::<f32>()].copy_from_slice(&value.to_le_bytes());
    fs::write(&raw_path, &raw).expect("changed vector");
    let receipt_path = worker.join("worker-receipt.json");
    let mut receipt: SseWorkerReceipt =
        serde_json::from_slice(&fs::read(&receipt_path).expect("receipt")).expect("worker receipt");
    receipt.files.insert(
        "raw-vectors.f32le".to_owned(),
        SseFileIdentity {
            bytes: raw.len() as u64,
            sha256: sha256(&raw),
        },
    );
    let mut receipt_bytes = serde_json::to_vec_pretty(&receipt).expect("encode receipt");
    receipt_bytes.push(b'\n');
    fs::write(receipt_path, receipt_bytes).expect("updated receipt");
}

fn directory_hashes(root: &Path) -> BTreeMap<String, String> {
    let mut files = fs::read_dir(root)
        .expect("artifact directory")
        .map(|entry| entry.expect("artifact entry").path())
        .collect::<Vec<_>>();
    files.sort();
    files
        .into_iter()
        .map(|path| {
            (
                path.file_name().unwrap().to_string_lossy().into_owned(),
                sha256(&fs::read(&path).expect("artifact file")),
            )
        })
        .collect()
}

fn sha256(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}

fn is_lower_hex(value: &str, length: usize) -> bool {
    value.len() == length
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

fn assert_no_keys(value: &Value, forbidden: &[&str]) {
    match value {
        Value::Object(object) => {
            for (key, value) in object {
                assert!(
                    !forbidden.contains(&key.as_str()),
                    "worker request leaked `{key}`"
                );
                assert_no_keys(value, forbidden);
            }
        }
        Value::Array(values) => {
            for value in values {
                assert_no_keys(value, forbidden);
            }
        }
        _ => {}
    }
}
