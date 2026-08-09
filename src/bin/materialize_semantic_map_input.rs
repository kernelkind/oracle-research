//! Command boundary for materializing the initial scaled semantic-map input.

use std::env;
use std::fs::File;
use std::process::ExitCode;

use oracle_mvp::semantic_map_sample::{
    SemanticMapGenerationInputConfig, materialize_semantic_map_generation_input,
};

const USAGE: &str = "usage: materialize-semantic-map-input CONFIG.json";

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("semantic-map generation input failed: {error}");
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
    let config: SemanticMapGenerationInputConfig =
        serde_json::from_reader(File::open(config_path)?)?;
    let manifest = materialize_semantic_map_generation_input(&config)?;
    serde_json::to_writer_pretty(std::io::stdout().lock(), &manifest)?;
    println!();
    Ok(())
}
