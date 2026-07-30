//! Interactive review entrypoint for the frozen SSE subject masks.

use std::env;
use std::io::IsTerminal;
use std::process::ExitCode;

use oracle_mvp::reference_tui::ReferenceTerminal;
use oracle_mvp::sse_mask_review::{
    MaskReviewRunOutcome, load_verified_mask_proposal, run_mask_review,
};

const USAGE: &str =
    "usage: sse-mask-review <mask-proposal.json> <session.json> <approved-masks.json>";

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("SSE mask review failed: {error}");
            ExitCode::FAILURE
        }
    }
}

fn run() -> Result<(), Box<dyn std::error::Error>> {
    let arguments = env::args().skip(1).collect::<Vec<_>>();
    let [proposal, session, approved] = arguments.as_slice() else {
        return Err(USAGE.into());
    };
    load_verified_mask_proposal(proposal)?;
    if !std::io::stdin().is_terminal() || !std::io::stdout().is_terminal() {
        return Err("the SSE mask review must be started from an interactive terminal".into());
    }
    let mut terminal = ReferenceTerminal::new()?;
    let outcome = run_mask_review(proposal, session, approved, &mut terminal)?;
    drop(terminal);
    match outcome {
        MaskReviewRunOutcome::Paused => println!("SSE mask review paused safely"),
        MaskReviewRunOutcome::NeedsRevision { approved, rejected } => {
            println!("SSE mask review needs revision: {approved} approved, {rejected} rejected")
        }
        MaskReviewRunOutcome::Approved => println!("SSE masks approved and sealed"),
    }
    Ok(())
}
