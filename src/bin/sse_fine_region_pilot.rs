//! Command boundary for the frozen SSE fine-region partition pilot.

use std::env;
use std::process::ExitCode;

use oracle_mvp::fine_region_pilot::{run_fine_region_pilot, verify_fine_region_pilot};

const USAGE: &str = "usage: sse-fine-region-pilot <run|verify> CONFIG BASELINE_ROOT OUTPUT_DIR";

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("SSE fine-region pilot failed: {error}");
            ExitCode::FAILURE
        }
    }
}

fn run() -> Result<(), Box<dyn std::error::Error>> {
    let arguments = env::args().skip(1).collect::<Vec<_>>();
    match arguments.as_slice() {
        [command, config, baseline, output] if command == "run" => {
            let report = run_fine_region_pilot(config, baseline, output)?;
            println!(
                "published SSE fine-region pilot: {} vectors, {} resolutions",
                report.vector_count,
                report.resolutions.len()
            );
        }
        [command, config, baseline, output] if command == "verify" => {
            let report = verify_fine_region_pilot(config, baseline, output)?;
            println!(
                "verified SSE fine-region pilot: {} vectors, {} resolutions",
                report.vector_count,
                report.resolutions.len()
            );
        }
        _ => return Err(USAGE.into()),
    }
    Ok(())
}
