//! Interactive review entrypoint for generated SSE subjects and their masks.

use std::env;
use std::io::IsTerminal;
use std::path::Path;
use std::process::ExitCode;

use oracle_mvp::mask_prompt_review::{
    MaskPromptReviewOutcome, run_category_membership_review_from, run_mask_prompt_review_selected,
};
use oracle_mvp::reference_tui::ReferenceTerminal;
use oracle_mvp::sse_mask_review::{
    AtomicSubjectNoteReviewRunOutcome, ReviewStage, SelectedSubjectReviewRunOutcome,
    SubjectMaskReviewRunOutcome, load_verified_subject_mask_proposal,
    run_atomic_subject_note_review, run_claim_note_review, run_selected_atomic_subject_review,
    run_subject_mask_review,
};
use oracle_mvp::title_prompt_review::{
    TitlePromptReviewOutcome, run_title_prompt_review_with_comments,
};

const USAGE: &str = "usage: sse-mask-review \
    <subject-mask-proposal.json> <session.json> <approved-subject-masks.json>\n       \
    sse-mask-review iterate <generation-run-directory> <prompt-review-session.json> [--only <note:subject,...>]\n       \
    sse-mask-review review-subjects <experiment-directory>\n       \
    sse-mask-review review-claims <experiment-directory>\n       \
    sse-mask-review review-masks <mask-review.json> <mask-session.json> [--start-at <item-id>] [--only <item-id,...>]\n       \
    sse-mask-review review-titles <title-review.json> <title-session.json> [--start-at <item-id>] [--comments <comments.json>]\n       \
    sse-mask-review review-membership <membership-review.json> <membership-session.json> [--start-at <item-id>]";

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
    if let [command, batch, session, options @ ..] = arguments.as_slice()
        && command == "review-titles"
    {
        let mut start_at = None;
        let mut comments_path = None;
        let mut options = options.chunks_exact(2);
        for option in &mut options {
            match option[0].as_str() {
                "--start-at" if start_at.is_none() => start_at = Some(option[1].as_str()),
                "--comments" if comments_path.is_none() => {
                    comments_path = Some(Path::new(&option[1]));
                }
                _ => return Err(USAGE.into()),
            }
        }
        if !options.remainder().is_empty() {
            return Err(USAGE.into());
        }
        if !std::io::stdin().is_terminal() || !std::io::stdout().is_terminal() {
            return Err(
                "the title prompt review must be started from an interactive terminal".into(),
            );
        }
        let mut terminal = ReferenceTerminal::new()?;
        let outcome = run_title_prompt_review_with_comments(
            batch,
            session,
            start_at,
            comments_path,
            |screen, comment, assistant_comment| {
                if let Some(assistant_comment) = assistant_comment {
                    terminal.review_title_with_comment(
                        screen,
                        comment,
                        &assistant_comment.assessment_summary,
                        &assistant_comment.comment,
                    )
                } else {
                    terminal.review_title(screen, comment)
                }
            },
        )?;
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
    if let [command, batch, session, options @ ..] = arguments.as_slice()
        && (command == "review-masks" || command == "review-membership")
    {
        let membership = command == "review-membership";
        let mut start_at = None;
        let mut only = None;
        let mut options = options.chunks_exact(2);
        for option in &mut options {
            match option[0].as_str() {
                "--start-at" if start_at.is_none() => start_at = Some(option[1].as_str()),
                "--only" if !membership && only.is_none() => {
                    only = Some(option[1].split(',').collect::<Vec<_>>());
                }
                _ => return Err(USAGE.into()),
            }
        }
        if !options.remainder().is_empty() {
            return Err(USAGE.into());
        }
        if !std::io::stdin().is_terminal() || !std::io::stdout().is_terminal() {
            return Err(if membership {
                "the category membership review must be started from an interactive terminal"
            } else {
                "the mask prompt review must be started from an interactive terminal"
            }
            .into());
        }
        let mut terminal = ReferenceTerminal::new()?;
        let outcome = if membership {
            run_category_membership_review_from(batch, session, start_at, |screen, comment| {
                terminal.review_navigable_stacked(screen, comment)
            })?
        } else {
            run_mask_prompt_review_selected(
                batch,
                session,
                start_at,
                only.as_deref(),
                |screen, comment| terminal.review_navigable_stacked(screen, comment),
            )?
        };
        drop(terminal);
        let label = if membership { "Membership" } else { "Mask" };
        match outcome {
            MaskPromptReviewOutcome::Paused => println!("{label} review paused safely"),
            MaskPromptReviewOutcome::Completed {
                approved,
                rejected,
                skipped,
            } => {
                println!(
                    "{label} review complete: {approved} approved, {rejected} disapproved, {skipped} skipped"
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
