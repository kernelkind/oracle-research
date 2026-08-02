//! Command boundary for the frozen SSE context counterfactual.

use std::env;
use std::process::ExitCode;

use oracle_mvp::sse_context_counterfactual::{
    analyze_sse_context_counterfactual, prepare_sse_context_counterfactual,
    verify_sse_context_counterfactual,
};

const USAGE: &str = "usage: sse-context-counterfactual <prepare FIXTURE PREPARED_DIR | analyze FIXTURE PREPARED_DIR WORKER_OUTPUT_DIR ANALYSIS_DIR | verify FIXTURE ANALYSIS_DIR>";

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("SSE context counterfactual failed: {error}");
            ExitCode::FAILURE
        }
    }
}

fn run() -> Result<(), Box<dyn std::error::Error>> {
    let arguments = env::args().skip(1).collect::<Vec<_>>();
    match arguments.as_slice() {
        [command, fixture, prepared] if command == "prepare" => {
            let manifest = prepare_sse_context_counterfactual(fixture, prepared)?;
            println!(
                "prepared SSE context counterfactual: {} notes, {} vectors",
                manifest.note_count,
                manifest.rows.len()
            );
        }
        [command, fixture, prepared, worker_output, analysis] if command == "analyze" => {
            let report =
                analyze_sse_context_counterfactual(fixture, prepared, worker_output, analysis)?;
            println!(
                "published SSE context counterfactual: overall {} ({} targets)",
                if report.verdicts["overall"].passed {
                    "PASS"
                } else {
                    "FAIL"
                },
                report.predictions.len()
            );
        }
        [command, fixture, analysis] if command == "verify" => {
            let report = verify_sse_context_counterfactual(fixture, analysis)?;
            println!(
                "verified SSE context counterfactual: overall {} ({} targets)",
                if report.verdicts["overall"].passed {
                    "PASS"
                } else {
                    "FAIL"
                },
                report.predictions.len()
            );
        }
        _ => return Err(USAGE.into()),
    }
    Ok(())
}
