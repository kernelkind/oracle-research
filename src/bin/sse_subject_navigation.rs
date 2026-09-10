//! Browse saved fine-segment hierarchies or manual categories over original notes.

use std::env;
use std::io::IsTerminal;
use std::process::ExitCode;

use oracle_mvp::manual_note_hierarchy::ManualNoteHierarchy;
use oracle_mvp::manual_note_hierarchy_tui::run_manual_note_explorer;
use oracle_mvp::reference_tui::ReferenceTerminal;
use oracle_mvp::sse_subject_navigation::load_sse_subject_hierarchy;

const USAGE: &str = "usage: sse-subject-navigation <manual-hierarchy.json> <fine-region-hierarchy-analysis.json> <fine-region-partition-analysis.json>
       sse-subject-navigation --notes <manual-note-hierarchy.json> <source-notes.json> [--check]

--notes  Inspect manually constructed categories over original notes; no vector or clustering input
--check  Validate the manual-note proposal without opening a terminal";

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
    if arguments == ["--help"] || arguments == ["-h"] {
        println!("{USAGE}");
        return Ok(());
    }
    if arguments.first().is_some_and(|arg| arg == "--notes") {
        return run_notes(&arguments[1..]);
    }
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

fn run_notes(arguments: &[String]) -> Result<(), Box<dyn std::error::Error>> {
    let (spec, source, check) = match arguments {
        [spec, source] => (spec, source, false),
        [spec, source, flag] if flag == "--check" => (spec, source, true),
        _ => return Err(USAGE.into()),
    };
    let hierarchy = ManualNoteHierarchy::load(spec.as_ref(), source.as_ref())?;
    if check {
        println!("{} · manual proposal · read-only", hierarchy.hierarchy_id);
        println!(
            "{} categories · {} notes",
            hierarchy.nodes.len(),
            hierarchy.notes.len()
        );
        for node in hierarchy.nodes.values() {
            println!(
                "{} · {} notes",
                node.label,
                hierarchy.note_ids(&node.node_id).len()
            );
            if !node.children.is_empty() {
                println!("  Children: {}", node.children.join(", "));
                println!(
                    "  Notes outside children: {}",
                    hierarchy.outside_child_note_ids(&node.node_id).join(" ")
                );
            }
        }
        return Ok(());
    }
    if !std::io::stdin().is_terminal() || !std::io::stdout().is_terminal() {
        return Err("manual note navigation must be started from an interactive terminal".into());
    }
    run_manual_note_explorer(hierarchy)?;
    Ok(())
}
