//! Command boundary for preparing and analyzing SSE subject vectors.

use std::env;
use std::process::ExitCode;

use oracle_mvp::sse_vector_diagnostic::{
    analyze_sse_vectors, prepare_sse_worker_input, verify_sse_vector_diagnostic,
};

const USAGE: &str = "usage: sse-vector-diagnostic <prepare PROPOSAL WORKER_INPUT | analyze PROPOSAL WORKER_RECEIPT RAW_VECTORS OUTPUT_DIR | verify PROPOSAL OUTPUT_DIR>";

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("SSE vector diagnostic failed: {error}");
            ExitCode::FAILURE
        }
    }
}

fn run() -> Result<(), Box<dyn std::error::Error>> {
    let arguments = env::args().skip(1).collect::<Vec<_>>();
    match arguments.as_slice() {
        [command, proposal, worker_input] if command == "prepare" => {
            prepare_sse_worker_input(proposal, worker_input)?;
            println!("prepared source-bound SSE worker input at {worker_input}");
        }
        [command, proposal, worker_receipt, raw_vectors, output] if command == "analyze" => {
            let report = analyze_sse_vectors(proposal, worker_receipt, raw_vectors, output)?;
            println!(
                "published SSE vector analysis: {} subjects, {} unordered pairs",
                report.subject_count, report.pair_counts.all
            );
        }
        [command, proposal, output] if command == "verify" => {
            let report = verify_sse_vector_diagnostic(proposal, output)?;
            println!(
                "verified SSE vector analysis: {} subjects, {} unordered pairs",
                report.subject_count, report.pair_counts.all
            );
        }
        _ => return Err(USAGE.into()),
    }
    Ok(())
}
