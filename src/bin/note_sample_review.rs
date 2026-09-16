use std::io::IsTerminal;
use std::process::ExitCode;

use oracle_mvp::note_sample_review::NoteSampleReview;

const USAGE: &str = "usage: note-sample-review SELECTION.json [--start-at NOTE_ID]";

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("Note viewer failed: {error}");
            ExitCode::FAILURE
        }
    }
}

fn run() -> Result<(), Box<dyn std::error::Error>> {
    let arguments = std::env::args().skip(1).collect::<Vec<_>>();
    if matches!(arguments.as_slice(), [argument] if argument == "--help" || argument == "-h") {
        println!(
            "{USAGE}\nView complete notes and selection reasons. No model calls or saved decisions.\nLeft/Right or h/l: previous/next. Up/Down or j/k: scroll. Tab: panel.\nPgUp/PgDown: page. Ctrl-U/D: half-page. g/G: top/bottom. q/Esc/Ctrl-C: exit."
        );
        return Ok(());
    }
    let (path, start_at) = match arguments.as_slice() {
        [path] if !path.starts_with('-') => (path, None),
        [path, flag, id] if !path.starts_with('-') && flag == "--start-at" => {
            (path, Some(id.as_str()))
        }
        _ => return Err(USAGE.into()),
    };
    let review = NoteSampleReview::load(path, start_at)?;
    if !std::io::stdin().is_terminal() || !std::io::stdout().is_terminal() {
        return Err("start the note viewer in an interactive terminal".into());
    }
    review.run()?;
    Ok(())
}
