//! Start or exactly resume the CREC-108 static exposure probe.

use std::env;
use std::io::IsTerminal;
use std::path::Path;
use std::process::ExitCode;

use oracle_mvp::static_exposure_probe_launch::{
    prepare_static_exposure_probe, read_static_exposure_probe_launch_config,
    run_static_exposure_probe_tui,
};
use oracle_mvp::static_exposure_probe_runner::{
    StaticExposureProbeRunnerOutcome, StaticExposureProbeVerification,
};

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("static exposure probe failed: {error}");
            ExitCode::FAILURE
        }
    }
}

fn run() -> Result<(), String> {
    let mut arguments = env::args_os().skip(1);
    let first = arguments.next().ok_or_else(usage)?;
    let (verify_only, config_path) = if first == "--verify" {
        (true, arguments.next().ok_or_else(usage)?)
    } else {
        (false, first)
    };
    if arguments.next().is_some() {
        return Err(usage());
    }
    if !verify_only && (!std::io::stdin().is_terminal() || !std::io::stdout().is_terminal()) {
        return Err("the static exposure probe requires an interactive terminal".to_owned());
    }
    let config = read_static_exposure_probe_launch_config(Path::new(&config_path))
        .map_err(|error| error.to_string())?;
    if verify_only {
        eprintln!("Verifying frozen probe inputs; this can take about two minutes...");
        let prepared = prepare_static_exposure_probe(&config).map_err(|error| error.to_string())?;
        println!(
            "verified {} candidates, {} historical presentations, representation {}",
            prepared.candidate_count(),
            prepared.historical_presentation_count(),
            prepared.representation_version()
        );
        match prepared
            .verification_state()
            .map_err(|error| error.to_string())?
        {
            StaticExposureProbeVerification::Ready => {
                println!("probe state: ready; no evaluator transcript exists");
            }
            StaticExposureProbeVerification::Active {
                presentations,
                valid_ratings,
                pending_presentation,
            } => {
                println!(
                    "probe state: active; {presentations} presentations, {valid_ratings} valid ratings, pending={pending_presentation}"
                );
            }
            StaticExposureProbeVerification::Complete {
                presentations,
                valid_ratings,
            } => {
                println!(
                    "probe state: complete and report verified; {presentations} presentations, {valid_ratings} valid ratings"
                );
            }
        }
        return Ok(());
    }
    match run_static_exposure_probe_tui(&config).map_err(|error| error.to_string())? {
        StaticExposureProbeRunnerOutcome::Paused => {
            eprintln!("Static exposure probe paused safely. Run the same command to resume.");
        }
        StaticExposureProbeRunnerOutcome::Complete => {
            eprintln!("Static exposure probe is complete.");
        }
    }
    Ok(())
}

fn usage() -> String {
    "usage: static-exposure-probe [--verify] CONFIG.json".to_owned()
}
