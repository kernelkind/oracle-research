use std::env;

use oracle_mvp::theme_exposure_replay_artifact::{
    run_theme_exposure_replay_from_config, verify_theme_exposure_replay_from_config,
};

fn main() {
    if let Err(error) = run() {
        eprintln!("theme exposure replay failed: {error}");
        std::process::exit(1);
    }
}

fn run() -> Result<(), Box<dyn std::error::Error>> {
    let arguments = env::args().skip(1).collect::<Vec<_>>();
    match arguments.as_slice() {
        [command, config] if command == "run" => {
            let report = run_theme_exposure_replay_from_config(config)?;
            println!(
                "theme exposure replay decision: {:?} ({} presentations)",
                report.replay.decision, report.replay.note_count
            );
        }
        [command, config] if command == "verify" => {
            let report = verify_theme_exposure_replay_from_config(config)?;
            println!(
                "verified theme exposure replay: {:?} ({} presentations)",
                report.replay.decision, report.replay.note_count
            );
        }
        _ => {
            return Err("usage: theme_exposure_replay <run|verify> CONFIG.json".into());
        }
    }
    Ok(())
}
