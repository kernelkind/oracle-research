//! Interactive approval and navigation entrypoints for the reference map.

use std::env;
use std::fs::File;
use std::io::{BufReader, IsTerminal};
use std::path::Path;
use std::process::ExitCode;

use oracle_mvp::reference_map::ApprovedHierarchy;
use oracle_mvp::reference_review::{
    load_verified_note_proposal, prepare_note_proposal, run_hierarchy_review, run_note_review,
    ReviewRunOutcome,
};
use oracle_mvp::reference_tui::ReferenceTerminal;

const NOTES_USAGE: &str =
    "usage: reference-map notes <proposal.json> <session.json> <approved-notes.json>";
const HIERARCHY_USAGE: &str = "usage: reference-map hierarchy <approved-notes.json> <draft.json> <session.json> <approved-hierarchy.json>";
const NAVIGATE_USAGE: &str = "usage: reference-map navigate <approved-hierarchy.json>";
const PREPARE_NOTES_USAGE: &str =
    "usage: reference-map prepare-notes <selection-plan.json> <proposal.json>";
const USAGE: &str = "usage:\n  reference-map prepare-notes <selection-plan.json> <proposal.json>\n  reference-map notes <proposal.json> <session.json> <approved-notes.json>\n  reference-map hierarchy <approved-notes.json> <draft.json> <session.json> <approved-hierarchy.json>\n  reference-map navigate <approved-hierarchy.json>";

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("reference map failed: {error}");
            ExitCode::FAILURE
        }
    }
}

fn run() -> Result<(), Box<dyn std::error::Error>> {
    let arguments = env::args().skip(1).collect::<Vec<_>>();
    match arguments.as_slice() {
        [mode] if mode == "notes" => return Err(NOTES_USAGE.into()),
        [mode] if mode == "hierarchy" => return Err(HIERARCHY_USAGE.into()),
        [mode] if mode == "navigate" => return Err(NAVIGATE_USAGE.into()),
        [mode] if mode == "prepare-notes" => return Err(PREPARE_NOTES_USAGE.into()),
        [mode, plan, proposal] if mode == "prepare-notes" => {
            prepare_note_proposal(plan, proposal)?;
            println!("prepared source-bound note proposal at {proposal}");
        }
        [mode, proposal, session, approved] if mode == "notes" => {
            load_verified_note_proposal(proposal)?;
            require_terminal()?;
            let mut terminal = ReferenceTerminal::new()?;
            let outcome = run_note_review(proposal, session, approved, &mut terminal)?;
            drop(terminal);
            print_review_outcome("note selection", outcome);
        }
        [mode, approved_notes, draft, session, approved_hierarchy] if mode == "hierarchy" => {
            require_terminal()?;
            let mut terminal = ReferenceTerminal::new()?;
            let outcome = run_hierarchy_review(
                approved_notes,
                draft,
                session,
                approved_hierarchy,
                &mut terminal,
            )?;
            drop(terminal);
            print_review_outcome("hierarchy", outcome);
        }
        [mode, approved_hierarchy] if mode == "navigate" => {
            require_terminal()?;
            let hierarchy = read_approved_hierarchy(Path::new(approved_hierarchy))?;
            let mut terminal = ReferenceTerminal::new()?;
            terminal.navigate(hierarchy)?;
        }
        [mode, ..]
            if !matches!(
                mode.as_str(),
                "prepare-notes" | "notes" | "hierarchy" | "navigate"
            ) =>
        {
            return Err(format!("unknown mode `{mode}`\n\n{USAGE}").into());
        }
        _ => return Err(USAGE.into()),
    }
    Ok(())
}

fn require_terminal() -> Result<(), Box<dyn std::error::Error>> {
    if !std::io::stdin().is_terminal() || !std::io::stdout().is_terminal() {
        return Err("the reference map must be started from an interactive terminal".into());
    }
    Ok(())
}

fn read_approved_hierarchy(path: &Path) -> Result<ApprovedHierarchy, Box<dyn std::error::Error>> {
    let hierarchy: ApprovedHierarchy = serde_json::from_reader(BufReader::new(File::open(path)?))?;
    hierarchy.validate()?;
    Ok(hierarchy)
}

fn print_review_outcome(name: &str, outcome: ReviewRunOutcome) {
    match outcome {
        ReviewRunOutcome::Paused => println!("{name} review paused safely"),
        ReviewRunOutcome::NeedsRevision { approved, rejected } => {
            println!("{name} review needs revision: {approved} approved, {rejected} rejected")
        }
        ReviewRunOutcome::Approved => println!("{name} review approved and sealed"),
    }
}
