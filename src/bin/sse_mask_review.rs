//! Interactive review entrypoint for generated SSE subjects and their masks.

use std::env;
use std::io::IsTerminal;
use std::process::ExitCode;

use oracle_mvp::reference_tui::ReferenceTerminal;
use oracle_mvp::sse_mask_review::{
    PromptReviewRunOutcome, ReviewStage, SubjectMaskReviewRunOutcome,
    load_verified_subject_mask_proposal, run_subject_mask_prompt_review, run_subject_mask_review,
};

const USAGE: &str = "usage: sse-mask-review \
    <subject-mask-proposal.json> <session.json> <approved-subject-masks.json>\n       \
    sse-mask-review iterate <generation-run-directory> <prompt-review-session.json>";

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("SSE subject-mask review failed: {error}");
            ExitCode::FAILURE
        }
    }
}

fn run() -> Result<(), Box<dyn std::error::Error>> {
    let arguments = env::args().skip(1).collect::<Vec<_>>();
    if let [command, generation_run, session] = arguments.as_slice()
        && command == "iterate"
    {
        if !std::io::stdin().is_terminal() || !std::io::stdout().is_terminal() {
            return Err(
                "the SSE prompt review must be started from an interactive terminal".into(),
            );
        }
        let mut terminal = ReferenceTerminal::new()?;
        let outcome = run_subject_mask_prompt_review(generation_run, session, &mut terminal)?;
        drop(terminal);
        match outcome {
            PromptReviewRunOutcome::Paused => println!("SSE prompt review paused safely"),
            PromptReviewRunOutcome::Completed {
                pairs,
                subject_lists,
            } => println!(
                "SSE prompt review complete: pairs {} approved, {} rejected, {} skipped; \
                 subject lists {} approved, {} rejected, {} skipped",
                pairs.approved,
                pairs.rejected,
                pairs.skipped,
                subject_lists.approved,
                subject_lists.rejected,
                subject_lists.skipped,
            ),
        }
        return Ok(());
    }
    let [proposal, session, approved] = arguments.as_slice() else {
        return Err(USAGE.into());
    };
    load_verified_subject_mask_proposal(proposal)?;
    if !std::io::stdin().is_terminal() || !std::io::stdout().is_terminal() {
        return Err(
            "the SSE subject-mask review must be started from an interactive terminal".into(),
        );
    }
    let mut terminal = ReferenceTerminal::new()?;
    let outcome = run_subject_mask_review(proposal, session, approved, &mut terminal)?;
    drop(terminal);
    match outcome {
        SubjectMaskReviewRunOutcome::Paused => println!("SSE subject-mask review paused safely"),
        SubjectMaskReviewRunOutcome::NeedsRevision {
            stage,
            approved,
            rejected,
            missing_subject_notes,
        } => match stage {
            ReviewStage::Subjects => println!(
                "SSE subject generation needs revision: {approved} subjects approved, \
                     {rejected} subjects rejected, {missing_subject_notes} notes missing subjects"
            ),
            ReviewStage::Masks => println!(
                "SSE mask generation needs revision: {approved} masks approved, \
                     {rejected} masks rejected"
            ),
        },
        SubjectMaskReviewRunOutcome::Approved => {
            println!("SSE subjects and masks approved and sealed")
        }
    }
    Ok(())
}
