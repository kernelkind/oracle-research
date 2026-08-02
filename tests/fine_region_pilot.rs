use std::fs;
use std::path::Path;

use oracle_mvp::fine_region_pilot::{run_fine_region_pilot, verify_fine_region_pilot};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use tempfile::TempDir;

#[test]
fn pilot_runs_the_frozen_partition_path_and_verifies_its_artifact() {
    let fixture = Fixture::new();
    let output = fixture.temporary.path().join("result");

    let report = run_fine_region_pilot(&fixture.config, &fixture.baseline, &output)
        .expect("run fine-region pilot");

    assert_eq!(report.note_count, 4);
    assert_eq!(report.vector_count, 4);
    assert_eq!(report.dimensions, 2);
    assert_eq!(report.partition_source_sha256.len(), 64);
    assert_eq!(report.pilot_source_sha256.len(), 64);
    assert_eq!(report.resolutions.len(), 9);
    let median = report
        .resolutions
        .iter()
        .find(|resolution| resolution.level.percentile == 50)
        .expect("median resolution");
    assert_eq!(median.complete_linkage.regions.len(), 2);
    assert_eq!(median.complete_linkage.regions[0].members, vec![0, 1]);
    assert_eq!(median.complete_linkage.regions[1].members, vec![2, 3]);
    assert_eq!(median.dp_vmf.order_count, 4);

    let verified = verify_fine_region_pilot(&fixture.config, &fixture.baseline, &output)
        .expect("verify fine-region artifact");
    assert_eq!(verified, report);

    let audit = fs::read_to_string(output.join("audit.md")).expect("audit Markdown");
    assert!(audit.contains("Takeaway: Alpha near zero"));
    assert!(audit.contains("Selected source: `alpha` (occurrence 2)"));
    assert!(!audit.contains("Generated region label"));
}

struct Fixture {
    temporary: TempDir,
    baseline: std::path::PathBuf,
    config: std::path::PathBuf,
}

impl Fixture {
    fn new() -> Self {
        let temporary = tempfile::tempdir().expect("temporary directory");
        let baseline = temporary.path().join("baseline");
        fs::create_dir_all(baseline.join("analysis")).expect("baseline directories");

        let notes = [
            ("note-a", "alpha alpha"),
            ("note-b", "beta"),
            ("note-c", "gamma"),
            ("note-d", "delta"),
        ];
        let input = json!({
            "schema_version": 1,
            "notes": notes.iter().map(|(note_id, text)| json!({
                "note_id": note_id,
                "text": text,
            })).collect::<Vec<_>>()
        });
        write_json(&baseline.join("input.json"), &input);

        let labels = [
            "Alpha near zero",
            "Beta near zero",
            "Gamma near ninety",
            "Delta near ninety",
        ];
        let proposal = json!({
            "schema_version": 2,
            "proposal_id": "fixture",
            "note_set": {"path": "unused", "sha256": "0".repeat(64)},
            "subject_instruction": "fixture",
            "mask_instruction": "fixture",
            "notes": notes.iter().zip(labels.iter()).enumerate().map(|(index, ((note_id, text), label))| json!({
                "note_id": note_id,
                "subjects": [{
                    "subject_id": format!("{index:016x}"),
                    "label": label,
                    "status": "masked",
                    "fragments": [{
                        "text": if index == 0 { "alpha" } else { text },
                        "occurrence": if index == 0 { 2 } else { 1 }
                    }]
                }]
            })).collect::<Vec<_>>()
        });
        write_json(&baseline.join("proposal.json"), &proposal);

        let generation_manifest = json!({
            "schema_version": 1,
            "experiment": "fixture",
            "files": {
                "input.json": identity(&baseline.join("input.json")),
                "proposal.json": identity(&baseline.join("proposal.json"))
            }
        });
        write_json(
            &baseline.join("generation-manifest.json"),
            &generation_manifest,
        );

        let vectors = [
            unit_vector(0.0),
            unit_vector(5.0),
            unit_vector(90.0),
            unit_vector(95.0),
        ];
        let mut vector_bytes = Vec::new();
        for vector in vectors {
            for coordinate in vector {
                vector_bytes.extend_from_slice(&(coordinate as f32).to_le_bytes());
            }
        }
        fs::write(
            baseline.join("analysis/normalized-vectors.f32le"),
            vector_bytes,
        )
        .expect("vectors");
        let worker_receipt = json!({
            "schema_version": 1,
            "dimensions": 2,
            "row_count": 4,
            "rows": notes.iter().enumerate().map(|(ordinal, (note_id, _))| json!({
                "ordinal": ordinal,
                "note_id": note_id,
                "subject_id": format!("{ordinal:016x}")
            })).collect::<Vec<_>>()
        });
        write_json(
            &baseline.join("analysis/worker-receipt.json"),
            &worker_receipt,
        );
        let analysis_manifest = json!({
            "schema_version": 1,
            "note_count": 4,
            "subject_count": 4,
            "dimensions": 2,
            "files": {
                "normalized-vectors.f32le": identity(&baseline.join("analysis/normalized-vectors.f32le")),
                "worker-receipt.json": identity(&baseline.join("analysis/worker-receipt.json"))
            }
        });
        write_json(&baseline.join("analysis/manifest.json"), &analysis_manifest);

        let config = temporary.path().join("config.json");
        write_json(
            &config,
            &json!({
                "schema_version": 1,
                "pilot_id": "fixture-fine-region-pilot",
                "baseline_archive_sha256": "a".repeat(64),
                "generation_manifest": {
                    "path": "generation-manifest.json",
                    "sha256": sha256(&baseline.join("generation-manifest.json"))
                },
                "analysis_manifest": {
                    "path": "analysis/manifest.json",
                    "sha256": sha256(&baseline.join("analysis/manifest.json"))
                },
                "resolution_percentiles": [10,20,30,40,50,60,70,80,90],
                "audit_percentiles": [40,50,60],
                "dp_vmf_order_count": 4,
                "shuffle_seed": 7
            }),
        );

        Self {
            temporary,
            baseline,
            config,
        }
    }
}

fn unit_vector(degrees: f64) -> [f64; 2] {
    let radians = degrees.to_radians();
    [radians.cos(), radians.sin()]
}

fn identity(path: &Path) -> Value {
    json!({
        "bytes": fs::metadata(path).expect("metadata").len(),
        "sha256": sha256(path),
    })
}

fn write_json(path: &Path, value: &Value) {
    let mut bytes = serde_json::to_vec_pretty(value).expect("JSON");
    bytes.push(b'\n');
    fs::write(path, bytes).expect("write JSON");
}

fn sha256(path: &Path) -> String {
    let bytes = fs::read(path).expect("hash input");
    format!("{:x}", Sha256::digest(bytes))
}
