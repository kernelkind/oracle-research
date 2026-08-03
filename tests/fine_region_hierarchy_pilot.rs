use std::fs;
use std::path::Path;

use oracle_mvp::fine_region_hierarchy::HierarchyNode;
use oracle_mvp::fine_region_hierarchy_pilot::{
    ensure_fine_region_hierarchy_pilot, run_fine_region_hierarchy_pilot,
    verify_fine_region_hierarchy_pilot,
};
use serde_json::json;
use sha2::{Digest, Sha256};
use tempfile::TempDir;

fn unit_vector(degrees: f64) -> [f32; 2] {
    let radians = degrees.to_radians();
    [radians.cos() as f32, radians.sin() as f32]
}

fn sha256(path: &Path) -> String {
    let bytes = fs::read(path).expect("read fixture");
    format!("{:x}", Sha256::digest(bytes))
}

fn write_json(path: &Path, value: &serde_json::Value) {
    fs::write(
        path,
        serde_json::to_vec_pretty(value).expect("encode fixture"),
    )
    .expect("write fixture");
}

struct Fixture {
    _temp: TempDir,
    config: std::path::PathBuf,
    baseline: std::path::PathBuf,
    partition_analysis: std::path::PathBuf,
    review_decisions: std::path::PathBuf,
    output: std::path::PathBuf,
}

fn fixture() -> Fixture {
    let temp = TempDir::new().expect("temporary fixture");
    let baseline = temp.path().join("baseline");
    fs::create_dir(&baseline).expect("baseline directory");
    let vector_path = baseline.join("normalized-vectors.f32le");
    let vectors = [
        unit_vector(0.0),
        unit_vector(5.0),
        unit_vector(90.0),
        unit_vector(95.0),
    ];
    let bytes = vectors
        .iter()
        .flatten()
        .flat_map(|value| value.to_le_bytes())
        .collect::<Vec<_>>();
    fs::write(&vector_path, bytes).expect("vector fixture");

    let partition_analysis = temp.path().join("partition-analysis.json");
    write_json(
        &partition_analysis,
        &json!({
            "schema_version": 1,
            "pilot_id": "fixture-partition",
            "baseline_archive_sha256": "a".repeat(64),
            "analysis_manifest_sha256": "b".repeat(64),
            "note_count": 3,
            "vector_count": 4,
            "dimensions": 2,
            "vectors": [
                {"ordinal": 0, "note_id": "same-note"},
                {"ordinal": 1, "note_id": "same-note"},
                {"ordinal": 2, "note_id": "cross-note-a"},
                {"ordinal": 3, "note_id": "cross-note-b"}
            ]
        }),
    );

    let review_decisions = temp.path().join("review-decisions.json");
    write_json(
        &review_decisions,
        &json!({
            "schema_version": 1,
            "criterion": "expected members",
            "decision_owner": "user",
            "decisions": [
                {
                    "segment_id": "accepted",
                    "minimum_cosine": 0.99,
                    "title_reviewed": "accepted",
                    "decision": "pass"
                },
                {
                    "segment_id": "rejected",
                    "minimum_cosine": 0.5,
                    "title_reviewed": "rejected",
                    "decision": "fail"
                }
            ]
        }),
    );

    let config = temp.path().join("config.json");
    write_json(
        &config,
        &json!({
            "schema_version": 1,
            "pilot_id": "fixture-hierarchy",
            "baseline_archive_sha256": "a".repeat(64),
            "analysis_manifest_sha256": "b".repeat(64),
            "normalized_vectors": {
                "path": "normalized-vectors.f32le",
                "sha256": sha256(&vector_path)
            },
            "partition_analysis_sha256": sha256(&partition_analysis),
            "review_decisions_sha256": sha256(&review_decisions),
            "vector_count": 4,
            "dimensions": 2
        }),
    );

    let output = temp.path().join("result");
    Fixture {
        _temp: temp,
        config,
        baseline,
        partition_analysis,
        review_decisions,
        output,
    }
}

fn maximal_cross_note_fixture() -> Fixture {
    let temp = TempDir::new().expect("temporary fixture");
    let baseline = temp.path().join("baseline");
    fs::create_dir(&baseline).expect("baseline directory");
    let vector_path = baseline.join("normalized-vectors.f32le");
    let vectors = [
        unit_vector(0.0),
        unit_vector(1.0),
        unit_vector(2.0),
        unit_vector(90.0),
        unit_vector(91.0),
        unit_vector(180.0),
        unit_vector(181.0),
    ];
    let bytes = vectors
        .iter()
        .flatten()
        .flat_map(|value| value.to_le_bytes())
        .collect::<Vec<_>>();
    fs::write(&vector_path, bytes).expect("vector fixture");

    let partition_analysis = temp.path().join("partition-analysis.json");
    write_json(
        &partition_analysis,
        &json!({
            "schema_version": 1,
            "pilot_id": "fixture-partition",
            "baseline_archive_sha256": "a".repeat(64),
            "analysis_manifest_sha256": "b".repeat(64),
            "note_count": 5,
            "vector_count": 7,
            "dimensions": 2,
            "vectors": [
                {"ordinal": 0, "note_id": "note-a"},
                {"ordinal": 1, "note_id": "note-b"},
                {"ordinal": 2, "note_id": "note-c"},
                {"ordinal": 3, "note_id": "note-a"},
                {"ordinal": 4, "note_id": "note-b"},
                {"ordinal": 5, "note_id": "note-d"},
                {"ordinal": 6, "note_id": "note-e"}
            ]
        }),
    );

    let review_decisions = temp.path().join("review-decisions.json");
    write_json(
        &review_decisions,
        &json!({
            "schema_version": 1,
            "criterion": "expected members",
            "decision_owner": "user",
            "decisions": [
                {
                    "segment_id": "accepted",
                    "minimum_cosine": 0.9995,
                    "title_reviewed": "accepted",
                    "decision": "pass"
                },
                {
                    "segment_id": "rejected",
                    "minimum_cosine": 0.9,
                    "title_reviewed": "rejected",
                    "decision": "fail"
                }
            ]
        }),
    );

    let config = temp.path().join("config.json");
    write_json(
        &config,
        &json!({
            "schema_version": 2,
            "pilot_id": "fixture-hierarchy-maximal-cross-note",
            "fine_segment_selection": "maximal_cross_note_sets",
            "baseline_archive_sha256": "a".repeat(64),
            "analysis_manifest_sha256": "b".repeat(64),
            "normalized_vectors": {
                "path": "normalized-vectors.f32le",
                "sha256": sha256(&vector_path)
            },
            "partition_analysis_sha256": sha256(&partition_analysis),
            "review_decisions_sha256": sha256(&review_decisions),
            "vector_count": 7,
            "dimensions": 2
        }),
    );

    let output = temp.path().join("result");
    Fixture {
        _temp: temp,
        config,
        baseline,
        partition_analysis,
        review_decisions,
        output,
    }
}

#[test]
fn pilot_publishes_and_replays_the_review_bounded_complete_hierarchy() {
    let fixture = fixture();

    let report = run_fine_region_hierarchy_pilot(
        &fixture.config,
        &fixture.baseline,
        &fixture.partition_analysis,
        &fixture.review_decisions,
        &fixture.output,
    )
    .expect("run hierarchy pilot");

    assert_eq!(report.vector_count, 4);
    assert_eq!(report.schema_version, 2);
    assert_eq!(report.accepted_minimum_cosine, 0.99);
    assert_eq!(report.first_rejected_minimum_cosine, 0.5);
    assert!(report.partition_cutoff_cosine < report.accepted_minimum_cosine);
    assert!(report.partition_cutoff_cosine > report.first_rejected_minimum_cosine);
    assert_eq!(
        report
            .hierarchy
            .fine_segments
            .iter()
            .map(|segment| segment.members.as_slice())
            .collect::<Vec<_>>(),
        vec![&[0][..], &[1][..], &[2, 3][..]]
    );
    assert_eq!(report.hierarchy.merges.len(), 2);
    assert_eq!(report.hierarchy.root, HierarchyNode::Merge(1));
    assert!(fixture.output.join("analysis.json").is_file());
    assert!(fixture.output.join("audit.md").is_file());
    assert!(fixture.output.join("manifest.json").is_file());
    let manifest: serde_json::Value =
        serde_json::from_slice(&fs::read(fixture.output.join("manifest.json")).unwrap()).unwrap();
    assert!(manifest["partition_source_sha256"].is_string());
    assert!(manifest["cargo_lock_sha256"].is_string());

    let replayed = verify_fine_region_hierarchy_pilot(
        &fixture.config,
        &fixture.baseline,
        &fixture.partition_analysis,
        &fixture.review_decisions,
        &fixture.output,
    )
    .expect("verify hierarchy pilot");
    assert_eq!(replayed, report);
}

#[test]
fn pilot_verification_rejects_changed_output_or_input() {
    let fixture = fixture();
    run_fine_region_hierarchy_pilot(
        &fixture.config,
        &fixture.baseline,
        &fixture.partition_analysis,
        &fixture.review_decisions,
        &fixture.output,
    )
    .expect("run hierarchy pilot");

    fs::write(fixture.output.join("audit.md"), "changed").expect("tamper output");
    let output_error = verify_fine_region_hierarchy_pilot(
        &fixture.config,
        &fixture.baseline,
        &fixture.partition_analysis,
        &fixture.review_decisions,
        &fixture.output,
    )
    .expect_err("changed output must fail");
    assert!(
        output_error.to_string().contains("identity"),
        "{output_error}"
    );

    write_json(
        &fixture.review_decisions,
        &json!({"schema_version": 1, "changed": true}),
    );
    let input_error = verify_fine_region_hierarchy_pilot(
        &fixture.config,
        &fixture.baseline,
        &fixture.partition_analysis,
        &fixture.review_decisions,
        &fixture.output,
    )
    .expect_err("changed input must fail");
    assert!(
        input_error.to_string().contains("hash mismatch"),
        "{input_error}"
    );
}

#[test]
fn ensure_publishes_once_then_verifies_the_existing_artifact() {
    let fixture = fixture();
    let published = ensure_fine_region_hierarchy_pilot(
        &fixture.config,
        &fixture.baseline,
        &fixture.partition_analysis,
        &fixture.review_decisions,
        &fixture.output,
    )
    .expect("publish missing artifact");
    let verified = ensure_fine_region_hierarchy_pilot(
        &fixture.config,
        &fixture.baseline,
        &fixture.partition_analysis,
        &fixture.review_decisions,
        &fixture.output,
    )
    .expect("verify existing artifact");

    assert_eq!(verified, published);
}

#[test]
fn maximal_cross_note_selection_excludes_singletons_and_strict_subsets() {
    let fixture = maximal_cross_note_fixture();

    let report = run_fine_region_hierarchy_pilot(
        &fixture.config,
        &fixture.baseline,
        &fixture.partition_analysis,
        &fixture.review_decisions,
        &fixture.output,
    )
    .expect("run maximal cross-note hierarchy pilot");

    assert_eq!(
        report
            .hierarchy
            .fine_segments
            .iter()
            .map(|segment| segment.members.as_slice())
            .collect::<Vec<_>>(),
        vec![&[0, 1, 2][..], &[5, 6][..]]
    );
    assert_eq!(report.hierarchy.merges.len(), 1);
    assert_eq!(report.hierarchy.root, HierarchyNode::Merge(0));
    assert_eq!(report.cross_note_candidate_segment_count, 3);
    assert_eq!(report.cross_note_fine_segment_count, 2);
    assert_eq!(report.excluded_strict_subset_segment_count, 1);
    assert_eq!(report.singleton_fine_segment_count, 0);
    assert_eq!(report.hierarchy_vector_count, 5);
    assert_eq!(report.hierarchy_note_count, 5);
    assert!(report.partition_cutoff_cosine < report.accepted_minimum_cosine);
    assert!(report.partition_cutoff_cosine > report.first_rejected_minimum_cosine);
}
