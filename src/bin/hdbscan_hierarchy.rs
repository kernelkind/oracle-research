use std::error::Error;
use std::io::{self, IsTerminal};
use std::path::PathBuf;

use oracle_mvp::hdbscan_hierarchy::Hierarchy;
use oracle_mvp::hdbscan_hierarchy_tui::{HierarchyView, run_hierarchy_explorer};

const USAGE: &str = "Read-only HDBSCAN hierarchy explorer

Usage: hdbscan-hierarchy RESPONSE.json VECTOR-MAP.json NOTES.json [--selection SELECTION.json | --note-navigation] [--start-at GROUP] [--check]

--selection FILE  Inspect a validated saved selection instead of the raw tree
--note-navigation  Simplify the saved merge tree by distinct note sets; uses merge-tree IDs, not condensed-tree IDs
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
            Some("--check") if !check => check = true,
            Some("--note-navigation") if !note_navigation => note_navigation = true,
            Some(flag) if flag.starts_with('-') => {
                return Err(format!("unknown or repeated option: {flag}\n{USAGE}").into());
            }
            _ => paths.push(PathBuf::from(arg)),
        }
    }
    let [response, vector_map, notes] = paths.as_slice() else {
        return Err(USAGE.into());
    };
    if note_navigation && selection.is_some() {
        return Err("cannot combine --note-navigation and --selection".into());
    }
    let (hierarchy, view) = if note_navigation {
        (
            Hierarchy::load_note_navigation(response, vector_map, notes)?,
            HierarchyView::NoteNavigation,
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
        return Err(format!("unknown group {branch}").into());
    }
    if check {
        if note_navigation {
            println!("Merge-tree note navigation · comparison · read-only");
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
