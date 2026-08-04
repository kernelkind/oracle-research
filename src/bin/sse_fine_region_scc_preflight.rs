//! Replays the frozen SCC schedules against an existing fine-segment hierarchy artifact.

use std::env;
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::Path;
use std::process::ExitCode;

use oracle_mvp::fine_region_hierarchy::FineRegionHierarchy;
use oracle_mvp::fine_region_scc_preflight::{build_scc_preflight, frozen_scc_schedules};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

const USAGE: &str =
    "usage: sse-fine-region-scc-preflight HIERARCHY_ANALYSIS NORMALIZED_VECTORS OUTPUT_JSON";
const FINE_REGION_HIERARCHY_SOURCE: &[u8] = include_bytes!("../fine_region_hierarchy.rs");
const SCC_SOURCE: &[u8] = include_bytes!("../fine_region_scc.rs");
const PREFLIGHT_SOURCE: &[u8] = include_bytes!("../fine_region_scc_preflight.rs");
const COMMAND_SOURCE: &[u8] = include_bytes!("sse_fine_region_scc_preflight.rs");
const CARGO_LOCK: &[u8] = include_bytes!("../../Cargo.lock");
const FLAKE_NIX: &[u8] = include_bytes!("../../flake.nix");
const FLAKE_LOCK: &[u8] = include_bytes!("../../flake.lock");

#[derive(Deserialize)]
struct HierarchyArtifact {
    vector_count: usize,
    dimensions: usize,
    normalized_vectors_sha256: String,
    hierarchy: FineRegionHierarchy,
}

#[derive(Serialize)]
struct Artifact {
    schema_version: u32,
    pilot_id: &'static str,
    hierarchy_analysis_sha256: String,
    normalized_vectors_sha256: String,
    fine_region_hierarchy_source_sha256: String,
    scc_source_sha256: String,
    preflight_source_sha256: String,
    command_source_sha256: String,
    cargo_lock_sha256: String,
    flake_nix_sha256: String,
    flake_lock_sha256: String,
    report: oracle_mvp::fine_region_scc_preflight::SccPreflightReport,
}

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("SCC preflight failed: {error}");
            ExitCode::FAILURE
        }
    }
}

fn run() -> Result<(), Box<dyn std::error::Error>> {
    let arguments = env::args().skip(1).collect::<Vec<_>>();
    let [hierarchy_path, vectors_path, output_path] = arguments.as_slice() else {
        return Err(USAGE.into());
    };
    let hierarchy_bytes = fs::read(hierarchy_path)?;
    let hierarchy: HierarchyArtifact = serde_json::from_slice(&hierarchy_bytes)?;
    let vector_bytes = fs::read(vectors_path)?;
    let vector_hash = hash(&vector_bytes);
    if vector_hash != hierarchy.normalized_vectors_sha256 {
        return Err(format!(
            "normalized-vector hash mismatch: expected {}, got {vector_hash}",
            hierarchy.normalized_vectors_sha256
        )
        .into());
    }
    let vectors = decode_vectors(&vector_bytes, hierarchy.vector_count, hierarchy.dimensions)?;
    let schedules = frozen_scc_schedules()?;
    let report = build_scc_preflight(
        &vectors,
        &hierarchy.hierarchy.fine_segments,
        &hierarchy.hierarchy,
        &schedules,
    )?;
    let artifact = Artifact {
        schema_version: 1,
        pilot_id: "scc-hierarchy-preflight-v1",
        hierarchy_analysis_sha256: hash(&hierarchy_bytes),
        normalized_vectors_sha256: vector_hash,
        fine_region_hierarchy_source_sha256: hash(FINE_REGION_HIERARCHY_SOURCE),
        scc_source_sha256: hash(SCC_SOURCE),
        preflight_source_sha256: hash(PREFLIGHT_SOURCE),
        command_source_sha256: hash(COMMAND_SOURCE),
        cargo_lock_sha256: hash(CARGO_LOCK),
        flake_nix_sha256: hash(FLAKE_NIX),
        flake_lock_sha256: hash(FLAKE_LOCK),
        report,
    };
    let mut output = serde_json::to_vec_pretty(&artifact)?;
    output.push(b'\n');
    let output_path = Path::new(output_path);
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(output_path)?;
    file.write_all(&output)?;
    file.sync_all()?;
    println!(
        "wrote SCC preflight with {} variants to {}",
        artifact.report.variants.len(),
        output_path.display()
    );
    Ok(())
}

fn decode_vectors(bytes: &[u8], count: usize, dimensions: usize) -> Result<Vec<Vec<f64>>, String> {
    if dimensions == 0 {
        return Err("normalized-vector dimensions must be positive".to_owned());
    }
    let row_bytes = dimensions
        .checked_mul(4)
        .ok_or_else(|| "normalized-vector byte count overflowed".to_owned())?;
    let expected = count
        .checked_mul(row_bytes)
        .ok_or_else(|| "normalized-vector byte count overflowed".to_owned())?;
    if bytes.len() != expected {
        return Err(format!(
            "normalized-vector file has {} bytes, expected {expected}",
            bytes.len()
        ));
    }
    bytes
        .chunks_exact(row_bytes)
        .map(|row| {
            row.chunks_exact(4)
                .map(|coordinate| {
                    let value = f32::from_le_bytes(coordinate.try_into().expect("four bytes"));
                    value
                        .is_finite()
                        .then_some(f64::from(value))
                        .ok_or_else(|| {
                            "normalized-vector file contains a non-finite value".to_owned()
                        })
                })
                .collect()
        })
        .collect()
}

fn hash(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}
