use std::error::Error;
use std::io::{self, IsTerminal};
use std::path::PathBuf;

use oracle_mvp::hdbscan_hierarchy::Hierarchy;
use oracle_mvp::hdbscan_hierarchy_tui::{HierarchyView, run_hierarchy_explorer};

const USAGE: &str = "Read-only HDBSCAN hierarchy explorer

Usage: hdbscan-hierarchy INPUT.json VECTOR-MAP.json NOTES.json [--selection SELECTION.json | --note-navigation | --merge-history] [--min-notes N] [--start-at GROUP] [--check]

--selection FILE  Inspect a validated saved selection instead of the raw tree
--note-navigation  Simplify the saved merge tree by distinct note sets; uses merge-tree IDs, not condensed-tree IDs
--merge-history    Apply the same note-set projection to a saved merge history; merge scores may decrease
--min-notes N      Minimum distinct notes per displayed group (default: 2; root always kept); requires --note-navigation or --merge-history
--start-at GROUP  Initially display this saved group (default: root)
--check           Validate the inputs and print counts without opening the TUI
--help            Show this help

No inference, segmentation, source changes, or review decisions are performed.";

fn run() -> Result<(), Box<dyn Error>> {
    let mut paths = Vec::new();
    let mut start = None;
    let mut check = false;
    let mut selection = None;
    let mut note_navigation = false;
    let mut merge_history = false;
    let mut min_notes = None;
    let mut args = std::env::args_os().skip(1);
    while let Some(arg) = args.next() {
        match arg.to_str() {
            Some("--help" | "-h") => {
                println!("{USAGE}");
                return Ok(());
            }
            Some("--start-at") if start.is_none() => {
                let value = args.next().ok_or("--start-at requires a group ID")?;
                start = Some(value.to_str().ok_or("invalid group ID")?.parse::<usize>()?);
            }
            Some("--selection") if selection.is_none() => {
                selection = Some(PathBuf::from(
                    args.next().ok_or("--selection requires a file")?,
                ));
            }
            Some("--min-notes") if min_notes.is_none() => {
                let value = args.next().ok_or("--min-notes requires a count")?;
                let value = value
                    .to_str()
                    .ok_or("invalid minimum note count")?
                    .parse::<usize>()?;
                if value < 2 {
                    return Err("--min-notes must be at least 2 distinct notes".into());
                }
                min_notes = Some(value);
            }
            Some("--check") if !check => check = true,
            Some("--note-navigation") if !note_navigation => note_navigation = true,
            Some("--merge-history") if !merge_history => merge_history = true,
            Some(flag) if flag.starts_with('-') => {
                return Err(format!("unknown or repeated option: {flag}\n{USAGE}").into());
            }
            _ => paths.push(PathBuf::from(arg)),
        }
    }
    let [response, vector_map, notes] = paths.as_slice() else {
        return Err(USAGE.into());
    };
    if merge_history && (note_navigation || selection.is_some()) {
        return Err("cannot combine --merge-history with --note-navigation or --selection".into());
    }
    if note_navigation && selection.is_some() {
        return Err("cannot combine --note-navigation and --selection".into());
    }
    if min_notes.is_some() && !note_navigation && !merge_history {
        return Err("--min-notes requires --note-navigation or --merge-history".into());
    }
    let navigation_view = min_notes.map_or(
        HierarchyView::NoteNavigation,
        HierarchyView::NoteNavigationMinimum,
    );
    let (hierarchy, view) = if merge_history {
        (
            Hierarchy::load_merge_history_with_min_notes(
                response,
                vector_map,
                notes,
                min_notes.unwrap_or(2),
            )?,
            navigation_view,
        )
    } else if note_navigation {
        (
            Hierarchy::load_note_navigation_with_min_notes(
                response,
                vector_map,
                notes,
                min_notes.unwrap_or(2),
            )?,
            navigation_view,
        )
    } else if let Some(path) = &selection {
        (
            Hierarchy::load_selection(response, vector_map, notes, path)?,
            HierarchyView::Selection,
        )
    } else {
        (
            Hierarchy::load(response, vector_map, notes)?,
            HierarchyView::Condensed,
        )
    };
    let branch = start.unwrap_or(hierarchy.root);
    if !hierarchy.groups.contains_key(&branch) {
        if let Some(minimum) = min_notes {
            return Err(format!("group {branch} is not displayed with --min-notes {minimum}; omit --start-at to open the root").into());
        }
        return Err(format!("unknown group {branch}").into());
    }
    if check {
        if note_navigation || merge_history {
            println!("Merge-tree note navigation · comparison · read-only");
        }
        if let Some(minimum) = min_notes {
            println!("Minimum group size: {minimum} distinct notes (root always kept)");
        }
        if selection.is_some() {
            let root = &hierarchy.groups[&hierarchy.root];
            println!(
                "HDBv2 selection · proposal · read-only\n{} root choices · {} masks outside retained root children",
                root.children.len(),
                root.vectors.len()
            );
        }
        let originals: usize = hierarchy.vectors.values().map(Vec::len).sum();
        println!(
            "{} groups · {} unique vectors · {originals} original IDs · {} notes\nStarting branch {branch}",
            hierarchy.groups.len(),
            hierarchy.vectors.len(),
            hierarchy.groups[&hierarchy.root].note_count,
        );
        return Ok(());
    }
    if !io::stdin().is_terminal() || !io::stdout().is_terminal() {
        return Err("An interactive terminal is required; use --check for validation.".into());
    }
    run_hierarchy_explorer(hierarchy, Some(branch), view)?;
    Ok(())
}

fn main() {
    if let Err(error) = run() {
        eprintln!("{error}");
        std::process::exit(1);
    }
}
