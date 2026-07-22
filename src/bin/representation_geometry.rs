//! Command boundary for the one-time representation geometry diagnostic.

use std::env;
use std::path::PathBuf;
use std::process::ExitCode;

use oracle_mvp::representation_geometry::{
    derive_representation_geometry, verify_representation_geometry,
};

const USAGE: &str =
    "usage: representation-geometry <derive|verify> ORDERED_EVENT_IDS REPRESENTATION OUTPUT";

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("{error}");
            ExitCode::FAILURE
        }
    }
}

fn run() -> Result<(), String> {
    let mut arguments = env::args_os().skip(1);
    let operation = arguments.next().ok_or_else(usage)?;
    let ordered_event_ids = PathBuf::from(arguments.next().ok_or_else(usage)?);
    let representation = PathBuf::from(arguments.next().ok_or_else(usage)?);
    let output = PathBuf::from(arguments.next().ok_or_else(usage)?);
    if arguments.next().is_some() {
        return Err(usage());
    }
    let operation = operation
        .to_str()
        .ok_or_else(|| "operation is not UTF-8".to_owned())?;
    let artifact = match operation {
        "derive" => derive_representation_geometry(&ordered_event_ids, &representation, &output),
        "verify" => verify_representation_geometry(&ordered_event_ids, &representation, &output),
        _ => return Err(usage()),
    }
    .map_err(|error| error.to_string())?;
    serde_json::to_writer_pretty(std::io::stdout().lock(), artifact.manifest())
        .map_err(|error| format!("failed to encode geometry manifest: {error}"))?;
    println!();
    Ok(())
}

fn usage() -> String {
    USAGE.to_owned()
}
