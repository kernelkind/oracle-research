//! Interactive review entrypoint for generated SSE subjects and their masks.

use std::env;
use std::io::IsTerminal;
use std::process::ExitCode;

use oracle_mvp::mask_prompt_review::{MaskPromptReviewOutcome, run_mask_prompt_review_from};
use oracle_mvp::reference_tui::ReferenceTerminal;
use oracle_mvp::sse_mask_review::{
    AtomicSubjectNoteReviewRunOutcome, ReviewStage, SelectedSubjectReviewRunOutcome,
    SubjectMaskReviewRunOutcome, load_verified_subject_mask_proposal,
    run_atomic_subject_note_review, run_claim_note_review, run_selected_atomic_subject_review,
    run_subject_mask_review,
};
use oracle_mvp::title_prompt_review::{TitlePromptReviewOutcome, run_title_prompt_review};

const USAGE: &str = "usage: sse-mask-review \
    <subject-mask-proposal.json> <session.json> <approved-subject-masks.json>\n       \
    sse-mask-review iterate <generation-run-directory> <prompt-review-session.json> [--only <note:subject,...>]\n       \
    sse-mask-review review-subjects <experiment-directory>\n       \
    sse-mask-review review-claims <experiment-directory>\n       \
    sse-mask-review review-masks <mask-review.json> <mask-session.json> [--start-at <item-id>]\n       \
    sse-mask-review review-titles <title-review.json> <title-session.json> [--start-at <item-id>]";

#[derive(Clone, Copy)]
enum PromptReviewMode {
    AtomicSubject,
    Claim,
}

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
    let title_review = match arguments.as_slice() {
        [command, batch, session] if command == "review-titles" => Some((batch, session, None)),
        [command, batch, session, flag, item]
            if command == "review-titles" && flag == "--start-at" =>
        {
            Some((batch, session, Some(item.as_str())))
        }
        _ => None,
    };
    if let Some((batch, session, start_at)) = title_review {
        if !std::io::stdin().is_terminal() || !std::io::stdout().is_terminal() {
            return Err(
                "the title prompt review must be started from an interactive terminal".into(),
            );
        }
        let mut terminal = ReferenceTerminal::new()?;
        let outcome = run_title_prompt_review(batch, session, start_at, |screen, comment| {
            if screen.title.is_some() {
                terminal.review_title(screen, comment)
            } else {
                terminal.review_navigable_prompt_iteration(screen, comment)
            }
        })?;
        drop(terminal);
        match outcome {
            TitlePromptReviewOutcome::Paused => println!("Title review paused safely"),
            TitlePromptReviewOutcome::Completed {
                approved,
                rejected,
                skipped,
            } => println!(
                "Title review complete: {approved} approved, {rejected} disapproved, {skipped} skipped"
            ),
        }
        return Ok(());
    }
    if let [command, generation_run, session, flag, selection] = arguments.as_slice()
        && command == "iterate"
        && flag == "--only"
    {
        if !std::io::stdin().is_terminal() || !std::io::stdout().is_terminal() {
            return Err(
                "the SSE prompt review must be started from an interactive terminal".into(),
            );
        }
        let mut terminal = ReferenceTerminal::new()?;
        let outcome = run_selected_atomic_subject_review(
            generation_run,
            session,
            selection,
            |screen, comment| terminal.review_navigable_prompt_iteration(screen, comment),
        )?;
        drop(terminal);
        match outcome {
            SelectedSubjectReviewRunOutcome::Paused => {
                println!("Selected subject review paused safely");
            }
            SelectedSubjectReviewRunOutcome::Completed {
                approved,
                rejected,
                undecided,
            } => {
                println!(
                    "Selected subject review: {approved} approved, {rejected} disapproved, {undecided} not reviewed. Other subjects are unchanged."
                );
            }
        }
        return Ok(());
    }
    let mask_review = match arguments.as_slice() {
        [command, batch, session] if command == "review-masks" => Some((batch, session, None)),
        [command, batch, session, flag, item]
            if command == "review-masks" && flag == "--start-at" =>
        {
            Some((batch, session, Some(item.as_str())))
        }
        _ => None,
    };
    if let Some((batch, session, start_at)) = mask_review {
        if !std::io::stdin().is_terminal() || !std::io::stdout().is_terminal() {
            return Err(
                "the mask prompt review must be started from an interactive terminal".into(),
            );
        }
        let mut terminal = ReferenceTerminal::new()?;
        let outcome = run_mask_prompt_review_from(batch, session, start_at, |screen, comment| {
            terminal.review_navigable_prompt_iteration(screen, comment)
        })?;
        drop(terminal);
        match outcome {
            MaskPromptReviewOutcome::Paused => println!("Mask review paused safely"),
            MaskPromptReviewOutcome::Completed {
                approved,
                rejected,
                skipped,
            } => {
                println!(
                    "Mask review complete: {approved} approved, {rejected} disapproved, {skipped} skipped"
                );
            }
        }
        return Ok(());
    }
    let prompt_review_paths = match arguments.as_slice() {
        [command, generation_run, session] if command == "iterate" => Some((
            PromptReviewMode::AtomicSubject,
            generation_run.into(),
            session.into(),
        )),
        [command, experiment] if command == "review-subjects" => {
            let experiment = std::path::PathBuf::from(experiment);
            Some((
                PromptReviewMode::AtomicSubject,
                experiment.join("run"),
                experiment.join("review-session.json"),
            ))
        }
        [command, experiment] if command == "review-claims" => {
            let experiment = std::path::PathBuf::from(experiment);
            Some((
                PromptReviewMode::Claim,
                experiment.join("run"),
                experiment.join("review-session.json"),
            ))
        }
        _ => None,
    };
    if let Some((mode, generation_run, session)) = prompt_review_paths {
        if !std::io::stdin().is_terminal() || !std::io::stdout().is_terminal() {
            return Err(
                "the SSE prompt review must be started from an interactive terminal".into(),
            );
        }
        let mut terminal = ReferenceTerminal::new()?;
        let outcome = match mode {
            PromptReviewMode::AtomicSubject => {
                run_atomic_subject_note_review(generation_run, session, &mut terminal)?
            }
            PromptReviewMode::Claim => {
                run_claim_note_review(generation_run, session, &mut terminal)?
            }
        };
        drop(terminal);
        match outcome {
            AtomicSubjectNoteReviewRunOutcome::Paused => {
                println!(
                    "SSE {} prompt review paused safely",
                    match mode {
                        PromptReviewMode::AtomicSubject => "atomic-subject",
                        PromptReviewMode::Claim => "claim",
                    }
                )
            }
            AtomicSubjectNoteReviewRunOutcome::Completed {
                subjects,
                notes_missing_subjects,
                notes_with_repeated_subjects,
            } => match mode {
                PromptReviewMode::AtomicSubject => println!(
                    "SSE atomic-subject prompt review complete: subjects {} approved, {} rejected; \
                     {notes_missing_subjects} notes missing subjects; \
                     {notes_with_repeated_subjects} notes with repeated subjects",
                    subjects.approved, subjects.rejected,
                ),
                PromptReviewMode::Claim => println!(
                    "SSE claim prompt review complete: claims {} approved, {} rejected; \
                     {notes_missing_subjects} notes missing claims; \
                     {notes_with_repeated_subjects} notes with repeated claims",
                    subjects.approved, subjects.rejected,
                ),
            },
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
