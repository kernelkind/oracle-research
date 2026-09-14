//! TRUE04 evidence viewer with optional separate saved containment decisions.

use std::io::IsTerminal;
use std::process::ExitCode;

use oracle_mvp::containment_review::{ContainmentDecisionReviewOutcome, ContainmentReview};
use oracle_mvp::reference_tui::ReferenceTerminal;

const USAGE: &str = "usage: true-review PAIRS.json [--session SESSION.json] [--titles TITLES.json] [--start-at ITEM]";

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
        println!(
            "{USAGE}\nRead-only by default: no decisions or session files are saved.\nWith --session: A Yes (A contains B), R No, S Skip, C optional comment.\nAdd --titles with --session to show all source masks beneath each category title.\nLeft/right visits all cards; Tab chooses a scroll panel; j/k scrolls.\nCtrl-C saves/exits. Resume with the same command; --start-at reopens a card."
        );
        return Ok(());
    }
    let Some(path) = arguments.first().filter(|path| !path.starts_with('-')) else {
        return Err(USAGE.into());
    };
    let mut start_at = None;
    let mut session = None;
    let mut titles = None;
    let mut flags = arguments[1..].chunks_exact(2);
    for pair in &mut flags {
        match pair[0].as_str() {
            "--start-at" if start_at.is_none() => start_at = Some(pair[1].as_str()),
            "--session" if session.is_none() => session = Some(pair[1].as_str()),
            "--titles" if titles.is_none() => titles = Some(pair[1].as_str()),
            _ => return Err(USAGE.into()),
        }
    }
    if !flags.remainder().is_empty() || (titles.is_some() && session.is_none()) {
        return Err(USAGE.into());
    }
    let mut review = ContainmentReview::load(path, start_at)?;
    if let Some(titles) = titles {
        review = review.with_titles(titles)?;
    }
    if !std::io::stdin().is_terminal() || !std::io::stdout().is_terminal() {
        // Preserve packet/start-card validation precedence without creating a
        // session or lock when stdin or stdout has been redirected.
        return Err("start the TRUE04 viewer from an interactive terminal (stdin and stdout must be terminals)".into());
    }
    if let Some(session) = session {
        let mut terminal = None;
        let outcome = review.run_decisions(session, start_at, |screen, comment| {
            if terminal.is_none() {
                terminal = Some(ReferenceTerminal::new()?);
            }
            let terminal = terminal.as_mut().unwrap();
            if titles.is_some() {
                terminal.review_navigable_stacked(screen, comment)
            } else {
                terminal.review_navigable_prompt_iteration(screen, comment)
            }
        })?;
        drop(terminal);
        match outcome {
            ContainmentDecisionReviewOutcome::Paused => {
                println!("Containment review saved; run the same command to resume.")
            }
            ContainmentDecisionReviewOutcome::Completed { yes, no, skipped } => println!(
                "Containment review complete: {yes} Yes, {no} No, {skipped} skipped. Saved to {session}."
            ),
        }
    } else {
        review.run()?;
    }
    Ok(())
}
