use std::env;
use std::io::{self, Write};

use oracle_mvp::english_filter_pilot::build_pilot;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut args = env::args_os().skip(1);
    let deduplicated = args.next().ok_or_else(usage)?;
    let output = args.next().ok_or_else(usage)?;
    let model = args.next().ok_or_else(usage)?;
    if args.next().is_some() {
        return Err(usage().into());
    }

    let manifest = build_pilot(deduplicated, output, model)?;
    serde_json::to_writer_pretty(io::stdout().lock(), &manifest)?;
    writeln!(io::stdout().lock())?;
    Ok(())
}

fn usage() -> String {
    "usage: english_filter_pilot DEDUPLICATED_DIRECTORY OUTPUT_DIRECTORY GLOTLID_V3_MODEL"
        .to_owned()
}
