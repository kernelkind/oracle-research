use std::env;
use std::io::{self, Write};

use oracle_mvp::english_filter_pilot::score_pilot;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut args = env::args_os().skip(1);
    let pilot = args.next().ok_or_else(usage)?;
    if args.next().is_some() {
        return Err(usage().into());
    }
    let report = score_pilot(pilot)?;
    serde_json::to_writer_pretty(io::stdout().lock(), &report)?;
    writeln!(io::stdout().lock())?;
    Ok(())
}

fn usage() -> String {
    "usage: score_english_filter_pilot PILOT_DIRECTORY".to_owned()
}
