//! Compose existing manual-note and saved-merge explorers for read-only comparison.

use std::collections::BTreeMap;
use std::error::Error;
use std::fs;
use std::io;
use std::path::{Path, PathBuf};

use crossterm::event::{Event, KeyCode, KeyEventKind, KeyModifiers};
use ratatui::Frame;
use ratatui::layout::{Constraint, Layout, Rect};
use ratatui::widgets::{Block, Borders, List, ListItem, ListState, Paragraph, Wrap};
use serde::Deserialize;
use sha2::{Digest, Sha256};

use crate::hdbscan_hierarchy::Hierarchy;
use crate::hdbscan_hierarchy_tui::{HierarchyExplorer, HierarchyView};
use crate::manual_note_hierarchy::ManualNoteHierarchy;
use crate::manual_note_hierarchy_tui::ManualNoteExplorer;
use crate::reference_tui::{
    InteractiveReviewModel, ReferenceTerminal, accent_style, border_style, has_command_modifier,
    is_control_c_event, render_scrollable_panel, secondary_style, terminal_safe,
};

#[derive(Deserialize)]
struct ComparisonSpec {
    schema_version: u32,
    title: String,
    manual_hierarchy: PathBuf,
    source_notes: PathBuf,
    vector_map: PathBuf,
    merge_history: PathBuf,
    input_sha256: Option<BTreeMap<String, String>>,
    pages: Vec<PageSpec>,
}

#[derive(Deserialize)]
struct PageSpec {
    title: String,
    analysis: String,
    #[serde(flatten)]
    kind: PageKind,
}

#[derive(Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
enum PageKind {
    Manual { node_id: String },
    Merge { group_id: usize, min_notes: usize },
    Analysis,
}

fn load_note_short_ids(
    path: &Path,
    manual: &ManualNoteHierarchy,
) -> Result<BTreeMap<String, String>, Box<dyn Error>> {
    let notes = crate::hdbscan_hierarchy::load_note_short_ids(path)?;
    for note in manual.notes.values() {
        if notes
            .get(&note.note_id)
            .is_some_and(|short| short != &note.note_short_id)
        {
            return Err(format!(
                "manual and vector map short IDs disagree for {}",
                note.note_id
            )
            .into());
        }
    }
    Ok(notes)
}

enum Explorer {
    Manual(ManualNoteExplorer),
    Merge(HierarchyExplorer),
}

struct ComparisonPage {
    title: String,
    analysis: String,
    summary: String,
    analysis_scroll: u16,
    explorer: Option<Explorer>,
}

pub struct HierarchyComparison {
    title: String,
    pages: Vec<ComparisonPage>,
    selected: usize,
    opened: bool,
    half_page_lines: u16,
    pending_g: bool,
    interaction_enabled: bool,
}

impl HierarchyComparison {
    pub fn load(path: &Path) -> Result<Self, Box<dyn Error>> {
        let spec: ComparisonSpec = serde_json::from_slice(&fs::read(path)?)?;
        if spec.schema_version != 1 || spec.title.trim().is_empty() || spec.pages.is_empty() {
            return Err("comparison requires schema version 1, a title, and pages".into());
        }
        let parent = path.parent().unwrap_or_else(|| Path::new("."));
        let inputs = BTreeMap::from([
            ("manual_hierarchy", parent.join(spec.manual_hierarchy)),
            ("source_notes", parent.join(spec.source_notes)),
            ("vector_map", parent.join(spec.vector_map)),
            ("merge_history", parent.join(spec.merge_history)),
        ]);
        if let Some(hashes) = spec.input_sha256 {
            if hashes.len() != inputs.len()
                || hashes.keys().any(|key| !inputs.contains_key(key.as_str()))
            {
                return Err("comparison input_sha256 must identify all four inputs".into());
            }
            for (name, path) in &inputs {
                if format!("{:x}", Sha256::digest(fs::read(path)?)) != hashes[*name] {
                    return Err(format!("comparison {name} SHA-256 mismatch").into());
                }
            }
        }
        let manual =
            ManualNoteHierarchy::load(&inputs["manual_hierarchy"], &inputs["source_notes"])?;
        let note_short_ids = load_note_short_ids(&inputs["vector_map"], &manual)?;
        let mut merges = BTreeMap::<usize, Hierarchy>::new();
        let mut pages = Vec::with_capacity(spec.pages.len());
        for page in spec.pages {
            if page.title.trim().is_empty() {
                return Err("every comparison page requires a title".into());
            }
            let (explorer, summary) = match page.kind {
                PageKind::Manual { node_id } => {
                    if !manual.nodes.contains_key(&node_id) {
                        return Err(format!("unknown manual category {node_id}").into());
                    }
                    let count = manual.note_ids(&node_id).len();
                    // Scope the owned browser copy, leaving the source hierarchy intact.
                    let mut scoped = manual.clone();
                    scoped.root_node_id = node_id.clone();
                    (
                        Some(Explorer::Manual(ManualNoteExplorer::new(scoped))),
                        format!("manual category {node_id} · {count} notes"),
                    )
                }
                PageKind::Merge {
                    group_id,
                    min_notes,
                } => {
                    if let std::collections::btree_map::Entry::Vacant(entry) =
                        merges.entry(min_notes)
                    {
                        entry.insert(Hierarchy::load_merge_history_with_min_notes(
                            &inputs["merge_history"],
                            &inputs["vector_map"],
                            &inputs["source_notes"],
                            min_notes,
                        )?);
                    }
                    let hierarchy = &merges[&min_notes];
                    let group = hierarchy.groups.get(&group_id).ok_or_else(|| {
                        format!("unknown group {group_id} at minimum {min_notes} notes")
                    })?;
                    let summary = format!(
                        "merge group {group_id} · {} notes · minimum {min_notes}",
                        group.note_count
                    );
                    (
                        Some(Explorer::Merge(
                            HierarchyExplorer::with_view(
                                hierarchy.clone(),
                                Some(group_id),
                                HierarchyView::NoteNavigationMinimum(min_notes),
                            )?
                            .with_note_short_ids(note_short_ids.clone())
                            .with_parent_mask_toggle(),
                        )),
                        summary,
                    )
                }
                PageKind::Analysis => (None, "analysis only".to_owned()),
            };
            pages.push(ComparisonPage {
                title: terminal_safe(&page.title),
                analysis: terminal_safe(&page.analysis),
                summary,
                analysis_scroll: 0,
                explorer,
            });
        }
        Ok(Self {
            title: terminal_safe(&spec.title),
            pages,
            selected: 0,
            opened: false,
            half_page_lines: 1,
            pending_g: false,
            interaction_enabled: true,
        })
    }

    pub fn check_summary(&self) -> String {
        let mut lines = vec![format!("{} · read-only comparison", self.title)];
        lines.extend(
            self.pages
                .iter()
                .map(|page| format!("{}: {}", page.title, page.summary)),
        );
        lines.join("\n")
    }

    fn scroll_analysis(&mut self, delta: isize) {
        let scroll = &mut self.pages[self.selected].analysis_scroll;
        *scroll = usize::from(*scroll)
            .saturating_add_signed(delta)
            .min(u16::MAX as usize) as u16;
    }

    pub fn handle_event(&mut self, event: Event) -> bool {
        if is_control_c_event(&event) {
            return true;
        }
        if let Event::Key(key) = &event {
            if key.kind == KeyEventKind::Release {
                return false;
            }
            if key.code == KeyCode::F(2) && !has_command_modifier(key.modifiers) {
                self.opened = false;
                self.pending_g = false;
                return false;
            }
            if !has_command_modifier(key.modifiers) && matches!(key.code, KeyCode::Char('q' | 'Q'))
            {
                return true;
            }
        }
        if !self.interaction_enabled {
            return false;
        }
        if self.opened {
            return match self.pages[self.selected]
                .explorer
                .as_mut()
                .expect("opened explorer")
            {
                Explorer::Manual(model) => model.handle_event(event),
                Explorer::Merge(model) => model.handle_event(event),
            };
        }
        let Event::Key(key) = event else {
            return false;
        };
        let previous_g = std::mem::take(&mut self.pending_g);
        if key.modifiers == KeyModifiers::CONTROL {
            let half = self.half_page_lines as isize;
            match key.code {
                KeyCode::Char('d') => self.scroll_analysis(half),
                KeyCode::Char('u') => self.scroll_analysis(-half),
                KeyCode::Char('f') => self.scroll_analysis(half * 2),
                KeyCode::Char('b') => self.scroll_analysis(-half * 2),
                _ => {}
            }
            return false;
        }
        if has_command_modifier(key.modifiers) {
            return false;
        }
        match key.code {
            KeyCode::Down | KeyCode::Char('j') => {
                self.selected = (self.selected + 1).min(self.pages.len() - 1)
            }
            KeyCode::Up | KeyCode::Char('k') => self.selected = self.selected.saturating_sub(1),
            KeyCode::Enter | KeyCode::Right | KeyCode::Char('l') => {
                self.opened = self.pages[self.selected].explorer.is_some()
            }
            KeyCode::Char('J') => self.scroll_analysis(1),
            KeyCode::Char('K') => self.scroll_analysis(-1),
            KeyCode::PageDown => self.scroll_analysis(self.half_page_lines as isize * 2),
            KeyCode::PageUp => self.scroll_analysis(-(self.half_page_lines as isize) * 2),
            KeyCode::Home => self.pages[self.selected].analysis_scroll = 0,
            KeyCode::End | KeyCode::Char('G') => {
                self.pages[self.selected].analysis_scroll = u16::MAX
            }
            KeyCode::Char('g') if previous_g => self.pages[self.selected].analysis_scroll = 0,
            KeyCode::Char('g') => self.pending_g = true,
            _ => {}
        }
        false
    }

    pub fn render(&mut self, frame: &mut Frame<'_>) {
        let areas =
            Layout::vertical([Constraint::Min(0), Constraint::Length(1)]).split(frame.area());
        let (minimum_width, minimum_height) = if self.opened {
            match self.pages[self.selected]
                .explorer
                .as_ref()
                .expect("opened explorer")
            {
                Explorer::Manual(_) => (72, 24),
                Explorer::Merge(_) => (60, 13),
            }
        } else {
            (60, 17)
        };
        self.interaction_enabled =
            frame.area().width >= minimum_width && frame.area().height >= minimum_height;
        if !self.interaction_enabled {
            frame.render_widget(
                Paragraph::new(format!(
                    "Resize to at least {minimum_width} × {minimum_height}. Q exits."
                ))
                .wrap(Wrap { trim: false }),
                areas[0],
            );
        } else if self.opened {
            match self.pages[self.selected]
                .explorer
                .as_mut()
                .expect("opened explorer")
            {
                Explorer::Manual(model) => model.render_in_area(frame, areas[0]),
                Explorer::Merge(model) => model.render_in_area(frame, areas[0]),
            }
        } else {
            self.render_menu(frame, areas[0]);
        }
        frame.render_widget(
            Paragraph::new("F2 Comparison menu  ·  Q Quit").style(accent_style()),
            areas[1],
        );
    }

    fn render_menu(&mut self, frame: &mut Frame<'_>, area: Rect) {
        let list_height = (self.pages.len().min(8) + 2) as u16;
        let rows = Layout::vertical([
            Constraint::Length(2),
            Constraint::Length(list_height),
            Constraint::Min(5),
            Constraint::Length(2),
        ])
        .split(area);
        frame.render_widget(
            Paragraph::new(format!("{}\nRead-only comparison", self.title))
                .style(accent_style())
                .wrap(Wrap { trim: false }),
            rows[0],
        );
        let items = self
            .pages
            .iter()
            .map(|page| ListItem::new(page.title.as_str()))
            .collect::<Vec<_>>();
        frame.render_stateful_widget(
            List::new(items)
                .highlight_symbol("▶ ")
                .highlight_style(accent_style())
                .block(
                    Block::default()
                        .borders(Borders::ALL)
                        .border_style(border_style())
                        .title("Comparison pages"),
                ),
            rows[1],
            &mut ListState::default().with_selected(Some(self.selected)),
        );
        let page = &mut self.pages[self.selected];
        render_scrollable_panel(
            frame,
            rows[2],
            "Analysis",
            &page.analysis,
            &mut page.analysis_scroll,
            &mut self.half_page_lines,
            false,
        );
        let open = if page.explorer.is_some() {
            "Enter/l Open view"
        } else {
            "Analysis-only page"
        };
        frame.render_widget(
            Paragraph::new(format!(
                "j/k Choose page  {open}\nJ/K Scroll analysis  Ctrl-D/U Half page  gg/G Top/end"
            ))
            .style(secondary_style()),
            rows[3],
        );
    }
}

impl InteractiveReviewModel for HierarchyComparison {
    type Action = bool;
    fn none_action() -> bool {
        false
    }
    fn pause_action() -> bool {
        true
    }
    fn handle_terminal_event(&mut self, event: Event) -> bool {
        self.handle_event(event)
    }
    fn render_terminal(&mut self, frame: &mut Frame<'_>) {
        self.render(frame);
    }
}

pub fn run_hierarchy_comparison(mut model: HierarchyComparison) -> io::Result<()> {
    let mut terminal = ReferenceTerminal::new()?;
    terminal.run_review_model_stateful(&mut model, false)?;
    Ok(())
}
