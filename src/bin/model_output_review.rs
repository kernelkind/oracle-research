use std::io::IsTerminal;
use std::process::ExitCode;

use oracle_mvp::model_output_review::ModelOutputReview;

const USAGE: &str = "usage: model-output-review REVIEW.json [--start-at ID] [--check]";

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("Model-output viewer failed: {error}");
            ExitCode::FAILURE
        }
    }
}

fn run() -> Result<(), Box<dyn std::error::Error>> {
    let arguments = std::env::args().skip(1).collect::<Vec<_>>();
    if matches!(arguments.as_slice(), [argument] if argument == "--help" || argument == "-h") {
        println!(
            "{USAGE}\nCompare complete notes, saved model outputs, and separate comments.\nNo model calls or saved decisions. --check validates without opening a terminal.\n1–4 or [ / ]: model (number keys 1–9 supported). Left/Right or h/l n/p: note.\ns: next saved ordering, keeping position (when orderings are supplied).\nTab/Shift-Tab: pane. Up/Down or j/k: scroll. PgUp/PgDown: page.\nCtrl-U/D: half-page. g/G: top/bottom. i: original/model input if different.\nq/Esc/Ctrl-C: exit."
        );
        return Ok(());
    }
    let mut arguments = arguments.iter();
    let path = arguments
        .next()
        .filter(|path| !path.starts_with('-'))
        .ok_or(USAGE)?;
    let mut start_at = None;
    let mut check = false;
    while let Some(option) = arguments.next() {
        match option.as_str() {
            "--start-at" if start_at.is_none() => {
                start_at = Some(arguments.next().ok_or(USAGE)?.as_str());
            }
            "--check" if !check => check = true,
            _ => return Err(USAGE.into()),
        }
    }
    let review = ModelOutputReview::load(path, start_at)?;
    if check {
        println!("{}", review.check_summary());
        return Ok(());
    }
    if !std::io::stdin().is_terminal() || !std::io::stdout().is_terminal() {
        return Err("start the model-output viewer in an interactive terminal".into());
    }
    review.run()?;
    Ok(())
}
