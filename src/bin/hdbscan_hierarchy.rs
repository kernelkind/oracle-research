use std::error::Error;
use std::io::{self, IsTerminal};
use std::path::PathBuf;

use oracle_mvp::hdbscan_hierarchy::Hierarchy;
use oracle_mvp::hdbscan_hierarchy_tui::run_hierarchy_explorer;

const USAGE: &str = "Read-only HDBSCAN hierarchy explorer

Usage: hdbscan-hierarchy RESPONSE.json VECTOR-MAP.json NOTES.json [--start-at GROUP] [--check]

--start-at GROUP  Initially display this saved group (default: root)
--check           Validate the inputs and print counts without opening the TUI
--help            Show this help

No inference, segmentation, source changes, or review decisions are performed.";

fn run() -> Result<(), Box<dyn Error>> {
    let mut paths = Vec::new();
    let mut start = None;
    let mut check = false;
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
            Some("--check") if !check => check = true,
            Some(flag) if flag.starts_with('-') => {
                return Err(format!("unknown or repeated option: {flag}\n{USAGE}").into());
            }
            _ => paths.push(PathBuf::from(arg)),
        }
    }
    let [response, vector_map, notes] = paths.as_slice() else {
        return Err(USAGE.into());
    };
    let hierarchy = Hierarchy::load(response, vector_map, notes)?;
    let branch = start.unwrap_or(hierarchy.root);
    if !hierarchy.groups.contains_key(&branch) {
        return Err(format!("unknown group {branch}").into());
    }
    if check {
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
    run_hierarchy_explorer(hierarchy, Some(branch))?;
    Ok(())
}

fn main() {
    if let Err(error) = run() {
        eprintln!("{error}");
        std::process::exit(1);
    }
}
