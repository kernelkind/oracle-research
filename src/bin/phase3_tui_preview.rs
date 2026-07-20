//! Standalone preview of the production Phase 3 evaluator interaction.

use std::process::ExitCode;

use oracle_mvp::evaluator::{
    CompletionView, EvaluatorUi, RatingOutcome, RatingView, RestOutcome, RestView,
};
use oracle_mvp::evaluator_tui::FullScreenEvaluator;

const OVERFLOWING_NOTE: &str = "A deliberately long note demonstrates the real scrolling behavior at the minimum supported 72 × 24 terminal size.\n\nRust ownership makes resource lifetimes explicit.\nSmall interfaces are easier to reason about.\nDeterministic artifacts make experiments auditable.\nLocal judgments remain separate from public retrieval.\nPositive examples provide nearby support.\nNegative examples provide nearby conflict.\nNeutral examples pull nearby predictions toward neutral.\nDistant evidence contributes nothing.\nRepeated agreement strengthens a region.\nConflicting evidence preserves uncertainty.\nCandidate orders remain frozen while they are judged.\nEvery presented event ID remains in one no-repeat ledger.\nThe question and all seven anchors stay fixed below this pane.\nUse arrows, J/K, Page Up, Page Down, or Home to inspect the whole note.";

const NOTES: [&str; 6] = [
    OVERFLOWING_NOTE,
    "I finally replaced a proprietary tool with a tiny open-source program that does exactly one thing well. The best feature is the code I no longer have to maintain.",
    "A short note with a link that is shown as text only:\nhttps://example.com/an-article\n\nThe evaluator does not open it or infer what is behind it.",
    "Code-heavy notes remain readable and rateable:\n\nfn distance(left: &[f32], right: &[f32]) -> f32 {\n    left.iter().zip(right).map(|(a, b)| (a - b) * (a - b)).sum()\n}",
    "A note can mix several ideas at once: debugging a distributed system, drinking coffee outside, and wondering whether simple protocols outlive clever platforms.",
    "Rust's ownership model is not merely a memory-safety feature. It is a way to make resource lifetimes explicit without requiring a garbage collector.",
];

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("phase3 TUI preview failed: {error}");
            ExitCode::FAILURE
        }
    }
}

fn run() -> std::io::Result<()> {
    let mut evaluator = FullScreenEvaluator::new()?;
    evaluator.preparing()?;

    for index in 0..21 {
        let presentation_number = index + 1;
        let break_in = 20 - (index % 20);
        let note = NOTES[index % NOTES.len()];
        match evaluator.rate(RatingView::new(note, presentation_number, break_in))? {
            RatingOutcome::Submitted(submission) if submission.pause_after() => return Ok(()),
            RatingOutcome::Submitted(_) => {}
            RatingOutcome::Paused => return Ok(()),
        }
        if presentation_number == 20
            && evaluator.rest(RestView::new(presentation_number))? == RestOutcome::Paused
        {
            return Ok(());
        }
    }

    evaluator.complete(CompletionView::new(21))
}
