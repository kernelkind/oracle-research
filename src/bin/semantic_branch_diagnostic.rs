//! Command boundary for the CREC-110 semantic-branch diagnostic.

use std::env;
use std::path::Path;
use std::process::ExitCode;

use oracle_mvp::semantic_branch_analysis::{
    analyze_semantic_branch_from_config, read_semantic_branch_prepare_config,
    verify_semantic_branch_from_config,
};
use oracle_mvp::semantic_branch_artifact::{
    prepare_semantic_branch_artifact, seal_semantic_branch_labels,
};

const USAGE: &str = "usage: semantic-branch-diagnostic <prepare CONFIG.json | seal-labels RUN_PATH | analyze CONFIG.json | verify CONFIG.json>";

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("semantic-branch diagnostic failed: {error}");
            ExitCode::FAILURE
        }
    }
}

fn run() -> Result<(), Box<dyn std::error::Error>> {
    let arguments = env::args().skip(1).collect::<Vec<_>>();
    match arguments.as_slice() {
        [command, config] if command == "prepare" => {
            let config = read_semantic_branch_prepare_config(config)?;
            let output = prepare_semantic_branch_artifact(&config)?;
            println!(
                "prepared blind semantic-branch artifact at {}",
                output.display()
            );
        }
        [command, run_path] if command == "seal-labels" => {
            let output = seal_semantic_branch_labels(Path::new(run_path))?;
            println!(
                "sealed independent semantic-branch labels at {}",
                output.display()
            );
        }
        [command, config] if command == "analyze" => {
            let report = analyze_semantic_branch_from_config(config)?;
            println!(
                "semantic-branch decision: {:?} ({} candidates)",
                report.decision, report.candidate_count
            );
        }
        [command, config] if command == "verify" => {
            let report = verify_semantic_branch_from_config(config)?;
            println!(
                "verified semantic-branch decision: {:?} ({} candidates)",
                report.decision, report.candidate_count
            );
        }
        _ => return Err(USAGE.into()),
    }
    Ok(())
}
