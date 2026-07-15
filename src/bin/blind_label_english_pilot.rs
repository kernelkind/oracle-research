use std::env;
use std::io::{self, BufReader};

use oracle_mvp::english_filter_pilot::label_pilot;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut args = env::args_os().skip(1);
    let pilot = args.next().ok_or_else(usage)?;
    let page_size = match args.next() {
        Some(value) => value
            .to_str()
            .ok_or_else(usage)?
            .parse::<usize>()
            .map_err(|_| usage())?,
        None => 20,
    };
    if args.next().is_some() {
        return Err(usage().into());
    }
    let stdin = io::stdin();
    let mut input = BufReader::new(stdin.lock());
    let stdout = io::stdout();
    let mut output = stdout.lock();
    label_pilot(pilot, &mut input, &mut output, page_size)?;
    Ok(())
}

fn usage() -> String {
    "usage: blind_label_english_pilot PILOT_DIRECTORY [PAGE_SIZE]".to_owned()
}
