//! Browse saved fine-segment hierarchies or manual categories over original notes.

use std::collections::BTreeSet;
use std::env;
use std::io::IsTerminal;
use std::process::ExitCode;

use oracle_mvp::hierarchy_comparison_tui::{HierarchyComparison, run_hierarchy_comparison};
use oracle_mvp::manual_note_hierarchy::ManualNoteHierarchy;
use oracle_mvp::manual_note_hierarchy_tui::{
    run_category_note_explorer, run_manual_note_explorer, run_titled_merge_note_explorer,
};
use oracle_mvp::reference_tui::ReferenceTerminal;
use oracle_mvp::sse_subject_navigation::load_sse_subject_hierarchy;
use oracle_mvp::titled_merge_hierarchy::TitledMergeHierarchy;

const USAGE: &str = "usage: sse-subject-navigation <manual-hierarchy.json> <fine-region-hierarchy-analysis.json> <fine-region-partition-analysis.json>
       sse-subject-navigation --notes <manual-note-hierarchy.json> <source-notes.json> [--check]
       sse-subject-navigation --categories <note-hierarchy.json> <source-notes.json> [--collapse-equal-note-steps | --absorb-single-children] [--min-notes N] [--check]
       sse-subject-navigation --compare <comparison.json> [--check]
       sse-subject-navigation --merge-notes <merge-history.json> <vector-map.json> <source-notes.json> <titles.json> [--min-notes 5] [--start-at GROUP] [--check]

--notes  Inspect manually constructed categories over original notes; no vector or clustering input
--categories  Browse immediate children; N opens current-category notes with combined masks when supplied
--collapse-equal-note-steps  Skip equal-note child steps per route; preserve raw categories, N/D memberships and masks; O uses displayed children (--categories only)
--absorb-single-children  Each parent absorbs its only child; keeps parent IDs, titles and notes (--categories only; unavailable with shared categories)
--min-notes  Hide categories with fewer distinct notes, including raw descendants, without changing saved categories (--categories default: 1; --merge-notes default: 5)
--compare  Compare manual notes with saved merge groups; F2 returns to the comparison menu
--merge-notes  Browse unchanged saved merge groups as original notes with provisional titles
--check  Validate and describe every requested page without opening a terminal";

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
        return run_notes(&arguments[1..], false);
    }
    if arguments.first().is_some_and(|arg| arg == "--categories") {
        return run_notes(&arguments[1..], true);
    }
    if arguments.first().is_some_and(|arg| arg == "--compare") {
        return run_comparison(&arguments[1..]);
    }
    if arguments.first().is_some_and(|arg| arg == "--merge-notes") {
        return run_merge_notes(&arguments[1..]);
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

fn run_merge_notes(arguments: &[String]) -> Result<(), Box<dyn std::error::Error>> {
    let [history, vectors, notes, titles, options @ ..] = arguments else {
        return Err(USAGE.into());
    };
    let mut minimum = None;
    let mut start = None;
    let mut check = false;
    let mut options = options.iter();
    while let Some(option) = options.next() {
        match option.as_str() {
            "--check" if !check => check = true,
            "--min-notes" if minimum.is_none() => {
                minimum = Some(options.next().ok_or(USAGE)?.parse::<usize>()?);
            }
            "--start-at" if start.is_none() => {
                start = Some(options.next().ok_or(USAGE)?.parse::<usize>()?);
            }
            _ => return Err(USAGE.into()),
        }
    }
    let mut hierarchy = TitledMergeHierarchy::load(
        history.as_ref(),
        vectors.as_ref(),
        notes.as_ref(),
        titles.as_ref(),
        minimum.unwrap_or(5),
    )?;
    if let Some(group) = start {
        hierarchy.start_at(group)?;
    }
    if check {
        println!("{}", hierarchy.check_summary());
        return Ok(());
    }
    if !std::io::stdin().is_terminal() || !std::io::stdout().is_terminal() {
        return Err(
            "titled merge note navigation must be started from an interactive terminal".into(),
        );
    }
    run_titled_merge_note_explorer(hierarchy)?;
    Ok(())
}

fn run_comparison(arguments: &[String]) -> Result<(), Box<dyn std::error::Error>> {
    let (manifest, check) = match arguments {
        [manifest] => (manifest, false),
        [manifest, flag] if flag == "--check" => (manifest, true),
        _ => return Err(USAGE.into()),
    };
    let model = HierarchyComparison::load(manifest.as_ref())?;
    if check {
        println!("{}", model.check_summary());
        return Ok(());
    }
    if !std::io::stdin().is_terminal() || !std::io::stdout().is_terminal() {
        return Err("hierarchy comparison must be started from an interactive terminal".into());
    }
    run_hierarchy_comparison(model)?;
    Ok(())
}

fn run_notes(
    arguments: &[String],
    categories_only: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    let [spec, source, options @ ..] = arguments else {
        return Err(USAGE.into());
    };
    let mut check = false;
    let mut absorb = false;
    let mut collapse_equal_notes = false;
    let mut minimum = None;
    let mut options = options.iter();
    while let Some(option) = options.next() {
        match option.as_str() {
            "--check" if !check => check = true,
            "--absorb-single-children" if categories_only && !absorb => absorb = true,
            "--collapse-equal-note-steps" if categories_only && !collapse_equal_notes => {
                collapse_equal_notes = true;
            }
            "--min-notes" if categories_only && minimum.is_none() => {
                let value = options
                    .next()
                    .ok_or("--min-notes requires a positive integer")?;
                let value = value
                    .parse::<usize>()
                    .map_err(|_| "--min-notes requires a positive integer")?;
                if value == 0 {
                    return Err("--min-notes requires a positive integer".into());
                }
                minimum = Some(value);
            }
            _ => return Err(USAGE.into()),
        }
    }
    let min_notes = minimum.unwrap_or(1);
    if absorb && collapse_equal_notes {
        return Err("choose either --collapse-equal-note-steps or --absorb-single-children".into());
    }
    let (mut hierarchy, masks) =
        ManualNoteHierarchy::load_with_masks(spec.as_ref(), source.as_ref())?;
    if absorb && hierarchy.has_shared_categories() {
        return Err("--absorb-single-children is unavailable with shared categories".into());
    }
    let absorbed = if absorb {
        let count = hierarchy.absorb_single_children();
        hierarchy
            .hierarchy_id
            .push_str(" · single-child absorption");
        count
    } else {
        0
    };
    if check {
        println!(
            "{} · {} · read-only",
            hierarchy.hierarchy_id,
            if categories_only {
                "category hierarchy"
            } else {
                "manual proposal"
            }
        );
        println!(
            "{} categories · {} notes",
            hierarchy.nodes.len(),
            hierarchy.notes.len()
        );
        if absorb {
            println!("Absorbed {absorbed} single-child categories");
        }
        if collapse_equal_notes {
            println!(
                "Equal-note navigation collapse enabled; raw categories and memberships unchanged."
            );
        }
        let displayed = if categories_only && min_notes > 1 {
            let root = hierarchy.category_navigation_with_min_notes(
                &hierarchy.root_node_id,
                collapse_equal_notes,
                min_notes,
            );
            println!("Minimum notes per displayed category: {min_notes}");
            println!("Displayed root children: {}", root.children.len());
            let mut displayed = BTreeSet::new();
            let mut pending = vec![hierarchy.root_node_id.clone()];
            while let Some(node_id) = pending.pop() {
                if displayed.insert(node_id.clone()) {
                    pending.extend(
                        hierarchy
                            .category_navigation_with_min_notes(
                                &node_id,
                                collapse_equal_notes,
                                min_notes,
                            )
                            .children,
                    );
                }
            }
            Some(displayed)
        } else {
            None
        };
        for node in hierarchy.nodes.values() {
            if displayed
                .as_ref()
                .is_some_and(|ids| !ids.contains(&node.node_id))
            {
                continue;
            }
            let navigation = hierarchy.category_navigation_with_min_notes(
                &node.node_id,
                collapse_equal_notes,
                min_notes,
            );
            println!(
                "{} · {} notes",
                node.label,
                hierarchy.note_ids(&node.node_id).len()
            );
            if collapse_equal_notes || !navigation.children.is_empty() {
                println!("  Children: {}", navigation.children.join(", "));
                if !navigation.collapsed.is_empty() {
                    println!("  Collapsed here: {}", navigation.collapsed.join(", "));
                }
                println!(
                    "  Notes outside children: {}",
                    navigation.outside_note_ids.join(" ")
                );
            }
        }
        return Ok(());
    }
    if !std::io::stdin().is_terminal() || !std::io::stdout().is_terminal() {
        return Err("manual note navigation must be started from an interactive terminal".into());
    }
    if categories_only {
        run_category_note_explorer(hierarchy, masks, collapse_equal_notes, min_notes)?;
    } else {
        run_manual_note_explorer(hierarchy)?;
    }
    Ok(())
}
