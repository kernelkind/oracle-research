//! Command boundary for the scaled fixed-floor SSE fine segments.

use std::env;
use std::process::ExitCode;

use oracle_mvp::scaled_fine_segments::{
    ensure_scaled_fine_segments, run_scaled_fine_segments, verify_scaled_fine_segments,
};

const USAGE: &str = "usage: scaled-fine-segments <ensure|run|verify> CONFIG.json";

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("scaled fine segments failed: {error}");
            ExitCode::FAILURE
        }
    }
}

fn run() -> Result<(), Box<dyn std::error::Error>> {
    let arguments = env::args().skip(1).collect::<Vec<_>>();
    let report = match arguments.as_slice() {
        [command, config] if command == "ensure" => ensure_scaled_fine_segments(config)?,
        [command, config] if command == "run" => run_scaled_fine_segments(config)?,
        [command, config] if command == "verify" => verify_scaled_fine_segments(config)?,
        _ => return Err(USAGE.into()),
    };
    println!(
        "{} fine segments represent {} vectors from {} notes",
        report.segment_count, report.represented_vector_count, report.represented_note_count
    );
    Ok(())
}
