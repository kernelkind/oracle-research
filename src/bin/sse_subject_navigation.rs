//! Navigate the manually constructed hierarchy over accepted SSE fine segments.

use std::env;
use std::io::IsTerminal;
use std::process::ExitCode;

use oracle_mvp::reference_tui::ReferenceTerminal;
use oracle_mvp::sse_subject_navigation::load_sse_subject_hierarchy;

const USAGE: &str = "usage: sse-subject-navigation <manual-hierarchy.json> <fine-region-hierarchy-analysis.json> <fine-region-partition-analysis.json>";

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("SSE subject navigation failed: {error}");
            ExitCode::FAILURE
        }
    }
}

fn run() -> Result<(), Box<dyn std::error::Error>> {
    let arguments = env::args().skip(1).collect::<Vec<_>>();
    let [hierarchy, hierarchy_analysis, partition_analysis] = arguments.as_slice() else {
        return Err(USAGE.into());
    };
    let hierarchy = load_sse_subject_hierarchy(hierarchy, hierarchy_analysis, partition_analysis)?;
    if !std::io::stdin().is_terminal() || !std::io::stdout().is_terminal() {
        return Err("SSE subject navigation must be started from an interactive terminal".into());
    }
    let mut terminal = ReferenceTerminal::new()?;
    terminal.navigate_subjects(hierarchy)?;
    Ok(())
}
