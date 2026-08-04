use std::fs;
use std::process::Command;

use oracle_mvp::fine_region_hierarchy::{FineSegment, average_linkage_hierarchy};
use oracle_mvp::fine_region_scc_preflight::{
    D_SQRT_2_SCHEDULE_ID, D2_SCHEDULE_ID, G200_SCHEDULE_ID, build_scc_preflight,
    frozen_scc_schedules,
};
use serde_json::json;
use sha2::{Digest, Sha256};
use tempfile::TempDir;

fn unit_vector(degrees: f64) -> Vec<f64> {
    let radians = degrees.to_radians();
    vec![radians.cos(), radians.sin()]
}

#[test]
fn preflight_command_binds_the_frozen_inputs_and_writes_all_variants() {
    let temp = TempDir::new().expect("temporary directory");
    let vectors = [
        [1.0_f32, 0.0_f32],
        [0.999_847_7_f32, 0.017_452_406_f32],
        [0.984_807_7_f32, 0.173_648_18_f32],
        [0.981_627_17_f32, 0.190_809_f32],
    ];
    let vector_bytes = vectors
        .iter()
        .flatten()
        .flat_map(|value| value.to_le_bytes())
        .collect::<Vec<_>>();
    let vector_path = temp.path().join("vectors.f32le");
    fs::write(&vector_path, &vector_bytes).expect("write vectors");
    let decoded = vectors
        .iter()
        .map(|row| row.iter().copied().map(f64::from).collect::<Vec<_>>())
        .collect::<Vec<_>>();
    let fine_segments = (0..4)
        .map(|index| FineSegment {
            segment_id: format!("F{index:06}"),
            members: vec![index],
        })
        .collect::<Vec<_>>();
    let hierarchy = average_linkage_hierarchy(&decoded, &fine_segments).expect("hierarchy");
    let hierarchy_path = temp.path().join("hierarchy.json");
    fs::write(
        &hierarchy_path,
        serde_json::to_vec_pretty(&json!({
            "vector_count": 4,
            "dimensions": 2,
            "normalized_vectors_sha256": format!("{:x}", Sha256::digest(&vector_bytes)),
            "hierarchy": hierarchy,
        }))
        .expect("encode hierarchy"),
    )
    .expect("write hierarchy");
    let output = temp.path().join("analysis.json");

    let result = Command::new(env!("CARGO_BIN_EXE_sse-fine-region-scc-preflight"))
        .args([&hierarchy_path, &vector_path, &output])
        .output()
        .expect("run preflight command");
    assert!(
        result.status.success(),
        "{}",
        String::from_utf8_lossy(&result.stderr)
    );
    let artifact: serde_json::Value =
        serde_json::from_slice(&fs::read(output).expect("read result")).expect("decode result");
    assert_eq!(artifact["schema_version"], 1);
    assert_eq!(artifact["report"]["variants"].as_array().unwrap().len(), 3);
    assert!(artifact["fine_region_hierarchy_source_sha256"].is_string());
    assert!(artifact["flake_nix_sha256"].is_string());
    assert!(artifact["flake_lock_sha256"].is_string());
    assert_eq!(
        artifact["normalized_vectors_sha256"],
        format!("{:x}", Sha256::digest(&vector_bytes))
    );

    let empty_vectors = temp.path().join("empty.f32le");
    fs::write(&empty_vectors, []).expect("write empty vectors");
    let mut invalid_hierarchy: serde_json::Value =
        serde_json::from_slice(&fs::read(&hierarchy_path).expect("read hierarchy fixture"))
            .expect("decode hierarchy fixture");
    invalid_hierarchy["dimensions"] = json!(0);
    invalid_hierarchy["normalized_vectors_sha256"] = json!(format!("{:x}", Sha256::digest([])));
    let invalid_hierarchy_path = temp.path().join("zero-dimension-hierarchy.json");
    fs::write(
        &invalid_hierarchy_path,
        serde_json::to_vec_pretty(&invalid_hierarchy).expect("encode invalid hierarchy"),
    )
    .expect("write invalid hierarchy");
    let invalid_output = temp.path().join("invalid-analysis.json");
    let invalid = Command::new(env!("CARGO_BIN_EXE_sse-fine-region-scc-preflight"))
        .args([&invalid_hierarchy_path, &empty_vectors, &invalid_output])
        .output()
        .expect("run invalid preflight command");
    assert!(!invalid.status.success());
    assert!(
        String::from_utf8_lossy(&invalid.stderr).contains("dimensions must be positive"),
        "{}",
        String::from_utf8_lossy(&invalid.stderr)
    );

    invalid_hierarchy["vector_count"] = json!(0);
    invalid_hierarchy["dimensions"] = json!(usize::MAX);
    let overflow_hierarchy_path = temp.path().join("overflow-hierarchy.json");
    fs::write(
        &overflow_hierarchy_path,
        serde_json::to_vec_pretty(&invalid_hierarchy).expect("encode overflow hierarchy"),
    )
    .expect("write overflow hierarchy");
    let overflow_output = temp.path().join("overflow-analysis.json");
    let overflow = Command::new(env!("CARGO_BIN_EXE_sse-fine-region-scc-preflight"))
        .args([&overflow_hierarchy_path, &empty_vectors, &overflow_output])
        .output()
        .expect("run overflow preflight command");
    assert!(!overflow.status.success());
    assert!(
        String::from_utf8_lossy(&overflow.stderr).contains("byte count overflowed"),
        "{}",
        String::from_utf8_lossy(&overflow.stderr)
    );
}

#[test]
fn frozen_preflight_brackets_dense_and_coarse_scc_schedules() {
    let vectors = vec![
        unit_vector(0.0),
        unit_vector(1.0),
        unit_vector(10.0),
        unit_vector(11.0),
    ];
    let fine_segments = (0..4)
        .map(|index| FineSegment {
            segment_id: format!("F{index:06}"),
            members: vec![index],
        })
        .collect::<Vec<_>>();
    let average = average_linkage_hierarchy(&vectors, &fine_segments).expect("average linkage");

    let schedules = frozen_scc_schedules().expect("frozen schedules");
    assert_eq!(
        schedules
            .iter()
            .map(|schedule| schedule.schedule_id.as_str())
            .collect::<Vec<_>>(),
        vec![G200_SCHEDULE_ID, D2_SCHEDULE_ID, D_SQRT_2_SCHEDULE_ID]
    );
    assert_eq!(schedules[0].minimum_similarities.len(), 200);
    assert_eq!(schedules[1].minimum_similarities.len(), 11);
    assert_eq!(schedules[2].minimum_similarities.len(), 21);
    assert_eq!(schedules[0].minimum_similarities[0], 1.0);
    assert!((schedules[0].minimum_similarities[199] - 0.001).abs() < 1.0e-12);
    assert_eq!(schedules[1].minimum_similarities[10], 0.0);
    assert!((schedules[2].minimum_similarities[19] - (1.0 - 0.512_f64.sqrt())).abs() < 1.0e-12);
    assert_eq!(schedules[2].minimum_similarities[20], 0.0);

    let report =
        build_scc_preflight(&vectors, &fine_segments, &average, &schedules).expect("SCC preflight");
    assert_eq!(report.variants.len(), 3);
    for variant in &report.variants {
        assert_eq!(variant.fine_segment_count, 4);
        assert_eq!(variant.hierarchy.roots.len(), 1);
        assert_eq!(variant.hierarchy.merges.len(), 3);
        assert!(variant.max_child_count >= 2);
    }
    assert_eq!(report.variants[0].average_linkage_node_matches, 3);
    assert_eq!(report.variants[0].average_linkage_node_count, 3);
    assert_eq!(report.variants[0].node_comparisons.len(), 3);
    assert!(
        report.variants[0]
            .node_comparisons
            .iter()
            .all(|node| node.average_linkage_merge_index.is_some())
    );
}
