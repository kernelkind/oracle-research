use std::fs;
use std::path::Path;

use oracle_mvp::scaled_fine_segments::{ensure_scaled_fine_segments, verify_scaled_fine_segments};
use serde_json::json;
use sha2::{Digest, Sha256};

#[test]
fn selects_only_maximal_complete_link_segments_spanning_multiple_notes() {
    let root = tempfile::tempdir_in("/dev/shm").expect("temporary directory");
    let vectors = root.path().join("vectors");
    fs::create_dir(&vectors).expect("vector directory");
    let directions = [0.0_f64, 5.0, 7.0, 90.0, 92.0, 180.0];
    let mut normalized = Vec::new();
    for degrees in directions {
        normalized.extend_from_slice(&(degrees.to_radians().cos() as f32).to_le_bytes());
        normalized.extend_from_slice(&(degrees.to_radians().sin() as f32).to_le_bytes());
    }
    fs::write(vectors.join("normalized-vectors.f32le"), &normalized).expect("normalized vectors");

    let note_ids = ["a", "a", "b", "c", "c", "d"];
    let mapped = note_ids
        .iter()
        .enumerate()
        .map(|(ordinal, prefix)| {
            json!({
                "ordinal": ordinal,
                "subject_id": format!("{ordinal:016x}"),
                "note_id": prefix.repeat(64),
                "takeaway_index": ordinal,
                "takeaway": format!("meaning {ordinal}"),
                "prominence": 70 + ordinal,
                "fragments": [format!("fragment {ordinal}")],
                "byte_spans": [[0, 1]]
            })
        })
        .collect::<Vec<_>>();
    write_json(
        &vectors.join("vector-map.json"),
        &json!({
            "schema_version": 1,
            "artifact_id": "fixture-vectors",
            "note_count": 4,
            "vector_count": mapped.len(),
            "generation_output_sha256": "1".repeat(64),
            "vectors": mapped
        }),
    );
    let normalized_sha = sha256(&vectors.join("normalized-vectors.f32le"));
    write_json(
        &vectors.join("manifest.json"),
        &json!({
            "schema_version": 1,
            "artifact_id": "fixture-vectors",
            "note_count": 4,
            "vector_count": 6,
            "dimensions": 2,
            "files": {
                "normalized-vectors.f32le": {
                    "bytes": normalized.len(),
                    "sha256": normalized_sha
                },
                "vector-map.json": {
                    "bytes": fs::metadata(vectors.join("vector-map.json")).unwrap().len(),
                    "sha256": sha256(&vectors.join("vector-map.json"))
                }
            }
        }),
    );

    let output = root.path().join("segments");
    let config = root.path().join("config.json");
    write_json(
        &config,
        &json!({
            "schema_version": 1,
            "artifact_id": "fixture-segments",
            "vector_artifact_path": vectors,
            "pairwise_min_cosine": 0.98,
            "output_path": output
        }),
    );

    let report = ensure_scaled_fine_segments(&config).expect("build segments");

    assert_eq!(1, report.segment_count);
    assert_eq!(3, report.represented_vector_count);
    assert_eq!(2, report.represented_note_count);
    assert_eq!(
        report,
        verify_scaled_fine_segments(&config).expect("verify replay")
    );
    let analysis: serde_json::Value =
        serde_json::from_slice(&fs::read(output.join("segments.json")).expect("segments output"))
            .expect("decode segments");
    assert_eq!(json!([0, 1, 2]), analysis["segments"][0]["vector_ordinals"]);
    assert!(
        analysis["segments"][0]["minimum_within_cosine"]
            .as_f64()
            .unwrap()
            >= 0.98
    );
    assert_eq!(2, analysis["excluded_partition_regions"]);
}

fn write_json(path: &Path, value: &serde_json::Value) {
    fs::write(path, serde_json::to_vec(value).expect("encode JSON")).expect("write JSON");
}

fn sha256(path: &Path) -> String {
    format!("{:x}", Sha256::digest(fs::read(path).expect("hash input")))
}
