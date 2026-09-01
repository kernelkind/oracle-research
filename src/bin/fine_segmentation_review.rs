//! Interactive entrypoint for the post-hoc HDBSCAN* semantic review.

use std::env;
use std::io::IsTerminal;
use std::process::ExitCode;

use oracle_mvp::fine_segmentation_review::{
    FineSegmentationReviewRunOutcome, run_fine_segmentation_review,
};
use oracle_mvp::reference_tui::ReferenceTerminal;

const USAGE: &str = "usage: fine-segmentation-review \
    REVIEWER.json SESSION.json RESPONSE.json";

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("fine-segmentation review failed: {error}");
            ExitCode::FAILURE
        }
    }
}

fn run() -> Result<(), Box<dyn std::error::Error>> {
    let arguments = env::args().skip(1).collect::<Vec<_>>();
    let [reviewer, session, response] = arguments.as_slice() else {
        return Err(USAGE.into());
    };
    if !std::io::stdin().is_terminal() || !std::io::stdout().is_terminal() {
        return Err(
            "the fine-segmentation review must be started from an interactive terminal".into(),
        );
    }

    let mut terminal = ReferenceTerminal::new()?;
    let outcome = run_fine_segmentation_review(reviewer, session, response, &mut terminal)?;
    drop(terminal);
    match outcome {
        FineSegmentationReviewRunOutcome::Paused => {
            println!("fine-segmentation review paused safely")
        }
        FineSegmentationReviewRunOutcome::Completed {
            valid,
            invalid,
            uncertain,
        } => println!(
            "fine-segmentation review complete: {valid} valid, {invalid} invalid, \
             {uncertain} uncertain"
        ),
    }
    Ok(())
}
