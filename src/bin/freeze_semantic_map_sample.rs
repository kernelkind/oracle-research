//! Command boundary for the frozen scaled semantic-map sample.

use std::env;
use std::fs::File;
use std::process::ExitCode;

use oracle_mvp::semantic_map_sample::{SemanticMapSampleConfig, freeze_semantic_map_sample};

const USAGE: &str = "usage: freeze-semantic-map-sample CONFIG.json";

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("semantic-map sample failed: {error}");
            ExitCode::FAILURE
        }
    }
}

fn run() -> Result<(), Box<dyn std::error::Error>> {
    let mut arguments = env::args_os().skip(1);
    let config_path = arguments.next().ok_or(USAGE)?;
    if arguments.next().is_some() {
        return Err(USAGE.into());
    }
    let config: SemanticMapSampleConfig = serde_json::from_reader(File::open(config_path)?)?;
    let manifest = freeze_semantic_map_sample(&config)?;
    serde_json::to_writer_pretty(std::io::stdout().lock(), &manifest)?;
    println!();
    Ok(())
}
