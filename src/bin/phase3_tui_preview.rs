//! Standalone integration preview of the production Phase 3 workflow and TUI.

use std::fs;
use std::path::PathBuf;
use std::process::ExitCode;

use oracle_mvp::adaptive_learning_runner::AdaptiveLearningRunnerOutcome;
use oracle_mvp::evaluator_tui::FullScreenEvaluator;
use oracle_mvp::phase3_preview::run_phase3_preview;

const PREVIEW_STATE_DIRECTORY: &str = "phase3-tui-preview-state-v2";

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("phase3 TUI preview failed: {error}");
            ExitCode::FAILURE
        }
    }
}

fn run() -> Result<(), Box<dyn std::error::Error>> {
    let workspace = preview_workspace();
    let mut evaluator = FullScreenEvaluator::new()?;
    let outcome = run_phase3_preview(&workspace, &mut evaluator)?;
    if matches!(outcome, AdaptiveLearningRunnerOutcome::Complete(_)) {
        fs::remove_dir_all(&workspace)?;
    }
    Ok(())
}

fn preview_workspace() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("target")
        .join(PREVIEW_STATE_DIRECTORY)
}
