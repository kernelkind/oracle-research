use std::env;
use std::path::Path;

use oracle_mvp::theme_geometry_artifact::{
    analyze_theme_geometry_from_config, prepare_blind_artifact, read_prepare_config,
    seal_theme_labels,
};

fn main() {
    if let Err(error) = run() {
        eprintln!("theme geometry diagnostic failed: {error}");
        std::process::exit(1);
    }
}

fn run() -> Result<(), Box<dyn std::error::Error>> {
    let arguments = env::args().skip(1).collect::<Vec<_>>();
    match arguments.as_slice() {
        [command, config] if command == "prepare" => {
            let config = read_prepare_config(config)?;
            let output = prepare_blind_artifact(&config)?;
            println!("prepared blind artifact at {}", output.display());
        }
        [command, run_path] if command == "seal-labels" => {
            let output = seal_theme_labels(Path::new(run_path))?;
            println!("sealed independent labels at {}", output.display());
        }
        [command, config] if command == "analyze" => {
            let report = analyze_theme_geometry_from_config(config)?;
            println!(
                "theme geometry decision: {:?} ({} notes)",
                report.decision, report.source_prefix_notes
            );
        }
        _ => {
            return Err(
                "usage: theme_geometry_diagnostic <prepare CONFIG.json | seal-labels RUN_PATH | analyze CONFIG.json>"
                    .into(),
            );
        }
    }
    Ok(())
}
