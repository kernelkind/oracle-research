//! Command boundary for pressure-gated real-note sample materialization.

use std::env;
use std::process::ExitCode;

use oracle_mvp::topic_sample::materialize_topic_sample_from_config;

const USAGE: &str = "usage: topic-map-sample CONFIG.json";

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("topic-map sampling failed: {error}");
            ExitCode::FAILURE
        }
    }
}

fn run() -> Result<(), Box<dyn std::error::Error>> {
    let mut arguments = env::args_os().skip(1);
    let config = arguments.next().ok_or(USAGE)?;
    if arguments.next().is_some() {
        return Err(USAGE.into());
    }
    let manifest = materialize_topic_sample_from_config(config)?;
    serde_json::to_writer_pretty(std::io::stdout().lock(), &manifest)?;
    println!();
    Ok(())
}
