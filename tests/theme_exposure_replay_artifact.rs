use std::fs;
use std::path::Path;

use oracle_mvp::theme_exposure_replay_artifact::{
    ThemeExposureReplayConfig, load_sealed_replay_input, validate_theme_exposure_replay_config,
};
use oracle_mvp::theme_geometry_diagnostic::Theme;
use serde_json::json;
use sha2::{Digest, Sha256};
use tempfile::TempDir;

#[test]
fn sealed_blind_input_reconstructs_exact_presentation_order() {
    let fixture = SealedFixture::new();

    let input = load_sealed_replay_input(
        &fixture.artifact,
        &fixture.report_sha256,
        &fixture.seal_sha256,
    )
    .expect("load sealed replay input");

    assert_eq!(
        input
            .identities_in_blind_order()
            .iter()
            .map(|identity| identity.record_id.as_str())
            .collect::<Vec<_>>(),
        vec!["T001", "T002", "T003"]
    );
    assert_eq!(
        input
            .chronological_identities()
            .iter()
            .map(|identity| (identity.presentation_ordinal, identity.record_id.as_str()))
            .collect::<Vec<_>>(),
        vec![(1, "T002"), (2, "T003"), (3, "T001")]
    );
    assert_eq!(
        input.label_sets()[0].labels()["T001"],
        [Theme::Cryptocurrency].into()
    );
}

#[test]
fn sealed_input_rejects_a_changed_label_file() {
    let fixture = SealedFixture::new();
    fs::write(
        fixture.artifact.join("labels-a.jsonl"),
        "{\"record_id\":\"T001\",\"themes\":[\"other\"]}\n",
    )
    .expect("change a sealed label file");

    let error = load_sealed_replay_input(
        &fixture.artifact,
        &fixture.report_sha256,
        &fixture.seal_sha256,
    )
    .expect_err("changed sealed source must be rejected");

    assert!(error.to_string().contains("hash mismatch"), "{error}");
}

#[test]
fn sealed_input_rejects_a_duplicate_event_identity() {
    let fixture =
        SealedFixture::with_event_ids(["11".repeat(32), "11".repeat(32), "33".repeat(32)]);

    let error = load_sealed_replay_input(
        &fixture.artifact,
        &fixture.report_sha256,
        &fixture.seal_sha256,
    )
    .expect_err("duplicate event identity must be rejected");

    assert!(error.to_string().contains("repeats an event ID"), "{error}");
}

#[test]
fn frozen_config_rejects_output_inside_an_immutable_input() {
    let temp = tempfile::tempdir().expect("create path-safety fixture");
    let source = temp.path().join("source");
    let representation = temp.path().join("representation");
    let semantic_corpus = temp.path().join("semantic-corpus");
    fs::create_dir(&source).expect("create source directory");
    fs::create_dir(&representation).expect("create representation directory");
    fs::create_dir(&semantic_corpus).expect("create semantic corpus directory");
    let config = ThemeExposureReplayConfig {
        source_artifact_path: source.clone(),
        expected_source_report_sha256:
            "5273e99c555ddc6f6e825b3a8810b1d65ea707a6f48c8fbb73ef186165606297".to_owned(),
        expected_label_seal_sha256:
            "d9d72b9e027c2f3d2277cec582da6bbad2d4ecf64c1f37d84a5970662bcf22a8".to_owned(),
        ordered_event_ids_path: semantic_corpus.join("ordered-event-ids.bin"),
        expected_ordered_event_ids_sha256:
            "5b161558645a66ac93418d47ac6fc77daff761940200f6fddc07b30587e78c39".to_owned(),
        representation_path: representation,
        representation_version: "5365b29f5e41d361cfae4b3a1754501d5320728053887236449071d680302c50"
            .to_owned(),
        expected_vector_set_sha256:
            "f8df0e9e607a578e3906eee9c9d072e4f1d8adec6a988dba6ec35c1c782dfeeb".to_owned(),
        output_path: source.join("crec-102-output"),
        minimum_family_notes: 8,
        primary_half_life: 20,
        sensitivity_half_lives: [10, 40],
        permutations: 10_000,
        permutation_seed: "crec-102-cumulative-theme-exposure-vector-permutations-v1".to_owned(),
    };

    let error = validate_theme_exposure_replay_config(&config)
        .expect_err("nested output must be rejected before execution");

    assert!(error.to_string().contains("protected input"), "{error}");

    let mut traversal = config;
    traversal.output_path = temp
        .path()
        .join("missing")
        .join("..")
        .join("source")
        .join("crec-102-output");
    let error = validate_theme_exposure_replay_config(&traversal)
        .expect_err("unresolved parent traversal must be rejected");
    assert!(error.to_string().contains("normalized"), "{error}");
}

struct SealedFixture {
    _temp: TempDir,
    artifact: std::path::PathBuf,
    report_sha256: String,
    seal_sha256: String,
}

impl SealedFixture {
    fn new() -> Self {
        Self::with_event_ids(["11".repeat(32), "22".repeat(32), "33".repeat(32)])
    }

    fn with_event_ids(event_ids: [String; 3]) -> Self {
        let temp = tempfile::tempdir().expect("create sealed fixture");
        let artifact = temp.path().join("artifact");
        fs::create_dir(&artifact).expect("create artifact directory");
        write(
            &artifact.join("blind-theme-notes.jsonl"),
            concat!(
                "{\"record_id\":\"T001\",\"content\":\"first\"}\n",
                "{\"record_id\":\"T002\",\"content\":\"second\"}\n",
                "{\"record_id\":\"T003\",\"content\":\"third\"}\n",
            ),
        );
        write(
            &artifact.join("blind-key.jsonl"),
            &format!(
                concat!(
                    "{{\"record_id\":\"T001\",\"presentation_ordinal\":3,\"event_id\":\"{}\"}}\n",
                    "{{\"record_id\":\"T002\",\"presentation_ordinal\":1,\"event_id\":\"{}\"}}\n",
                    "{{\"record_id\":\"T003\",\"presentation_ordinal\":2,\"event_id\":\"{}\"}}\n",
                ),
                event_ids[0], event_ids[1], event_ids[2],
            ),
        );
        write(&artifact.join("theme-rubric.json"), "{}\n");
        let labels = concat!(
            "{\"record_id\":\"T001\",\"themes\":[\"bitcoin\"]}\n",
            "{\"record_id\":\"T002\",\"themes\":[\"nostr\"]}\n",
            "{\"record_id\":\"T003\",\"themes\":[\"llm_ai\"]}\n",
        );
        write(&artifact.join("labels-a.jsonl"), labels);
        write(&artifact.join("labels-b.jsonl"), labels);

        let blind_sha = hash(&artifact.join("blind-theme-notes.jsonl"));
        let key_sha = hash(&artifact.join("blind-key.jsonl"));
        let rubric_sha = hash(&artifact.join("theme-rubric.json"));
        let labels_a_sha = hash(&artifact.join("labels-a.jsonl"));
        let labels_b_sha = hash(&artifact.join("labels-b.jsonl"));
        write_json(
            &artifact.join("prepare-manifest.json"),
            &json!({
                "schema_version": 1,
                "diagnostic_id": "crec-101-theme-vector-separation-v1",
                "prefix_notes": 3,
                "blind_file": "blind-theme-notes.jsonl",
                "blind_sha256": blind_sha,
                "key_file": "blind-key.jsonl",
                "key_sha256": key_sha,
                "rubric_file": "theme-rubric.json",
                "rubric_sha256": rubric_sha,
            }),
        );
        let manifest_sha = hash(&artifact.join("prepare-manifest.json"));
        write_json(
            &artifact.join("label-seal.json"),
            &json!({
                "schema_version": 1,
                "diagnostic_id": "crec-101-theme-vector-separation-v1",
                "prepare_manifest_sha256": manifest_sha,
                "blind_sha256": blind_sha,
                "key_sha256": key_sha,
                "rubric_sha256": rubric_sha,
                "labels_a_sha256": labels_a_sha,
                "labels_b_sha256": labels_b_sha,
                "record_count": 3,
            }),
        );
        let seal_sha256 = hash(&artifact.join("label-seal.json"));
        write_json(
            &artifact.join("geometry-report.json"),
            &json!({
                "diagnostic_id": "crec-101-theme-vector-separation-v1",
                "source_prefix_notes": 3,
                "ordered_event_ids_sha256": "ordered",
                "representation_version": "representation",
                "represented_rows": 3,
                "vector_dimension": 3,
                "vector_set_sha256": "vectors",
                "label_seal_sha256": seal_sha256,
                "decision": "proceed_to_exposure_replay",
            }),
        );
        let report_sha256 = hash(&artifact.join("geometry-report.json"));
        Self {
            _temp: temp,
            artifact,
            report_sha256,
            seal_sha256,
        }
    }
}

fn write(path: &Path, value: &str) {
    fs::write(path, value).expect("write fixture file");
}

fn write_json(path: &Path, value: &serde_json::Value) {
    let mut encoded = serde_json::to_vec_pretty(value).expect("encode fixture JSON");
    encoded.push(b'\n');
    fs::write(path, encoded).expect("write fixture JSON");
}

fn hash(path: &Path) -> String {
    let bytes = fs::read(path).expect("read fixture file");
    let digest = Sha256::digest(bytes);
    digest.iter().map(|byte| format!("{byte:02x}")).collect()
}
