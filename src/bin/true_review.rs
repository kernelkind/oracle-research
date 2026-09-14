//! Read-only terminal viewer for the existing TRUE04 review packet.

use std::io::IsTerminal;
use std::process::ExitCode;

use oracle_mvp::containment_review::ContainmentReview;

const USAGE: &str = "usage: true-review PAIRS.json [--start-at I01|A01]";

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("TRUE04 viewer failed: {error}");
            ExitCode::FAILURE
        }
    }
}

fn run() -> Result<(), Box<dyn std::error::Error>> {
    let arguments = std::env::args().skip(1).collect::<Vec<_>>();
    if matches!(arguments.as_slice(), [argument] if argument == "--help" || argument == "-h") {
        println!("{USAGE}\nRead-only: no decisions or session files are saved.");
        return Ok(());
    }
    let (path, start_at) = match arguments.as_slice() {
        [path] => (path, None),
        [path, flag, id] if flag == "--start-at" => (path, Some(id.as_str())),
        _ => return Err(USAGE.into()),
    };
    let review = ContainmentReview::load(path, start_at)?;
    if !std::io::stdin().is_terminal() || !std::io::stdout().is_terminal() {
        return Err("start the TRUE04 viewer from an interactive terminal (stdin and stdout must be terminals)".into());
    }
    review.run()?;
    Ok(())
}
