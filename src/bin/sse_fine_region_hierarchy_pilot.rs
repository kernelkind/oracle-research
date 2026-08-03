//! Command boundary for the frozen SSE fine-region hierarchy pilot.

use std::env;
use std::process::ExitCode;

use oracle_mvp::fine_region_hierarchy_pilot::{
    ensure_fine_region_hierarchy_pilot, run_fine_region_hierarchy_pilot,
    verify_fine_region_hierarchy_pilot,
};

const USAGE: &str = "usage: sse-fine-region-hierarchy-pilot <ensure|run|verify> CONFIG BASELINE_ROOT PARTITION_ANALYSIS REVIEW_DECISIONS OUTPUT_DIR";

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("SSE fine-region hierarchy pilot failed: {error}");
            ExitCode::FAILURE
        }
    }
}

fn run() -> Result<(), Box<dyn std::error::Error>> {
    let arguments = env::args().skip(1).collect::<Vec<_>>();
    match arguments.as_slice() {
        [command, config, baseline, partition, review, output] if command == "ensure" => {
            let report =
                ensure_fine_region_hierarchy_pilot(config, baseline, partition, review, output)?;
            println!(
                "ensured SSE fine-region hierarchy pilot: {} fine segments, {} higher merges",
                report.hierarchy.fine_segments.len(),
                report.hierarchy.merges.len()
            );
        }
        [command, config, baseline, partition, review, output] if command == "run" => {
            let report =
                run_fine_region_hierarchy_pilot(config, baseline, partition, review, output)?;
            println!(
                "published SSE fine-region hierarchy pilot: {} fine segments, {} higher merges",
                report.hierarchy.fine_segments.len(),
                report.hierarchy.merges.len()
            );
        }
        [command, config, baseline, partition, review, output] if command == "verify" => {
            let report =
                verify_fine_region_hierarchy_pilot(config, baseline, partition, review, output)?;
            println!(
                "verified SSE fine-region hierarchy pilot: {} fine segments, {} higher merges",
                report.hierarchy.fine_segments.len(),
                report.hierarchy.merges.len()
            );
        }
        _ => return Err(USAGE.into()),
    }
    Ok(())
}
