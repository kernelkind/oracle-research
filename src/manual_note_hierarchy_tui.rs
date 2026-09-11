//! Read-only browsing of manual categories and their full original notes.

use std::io;

use crossterm::event::{Event, KeyCode, KeyEventKind, KeyModifiers};
use ratatui::Frame;
use ratatui::layout::{Constraint, Layout, Rect};
use ratatui::text::Line;
use ratatui::widgets::{Block, Borders, List, ListItem, ListState, Paragraph, Wrap};

use crate::manual_note_hierarchy::{CategoryNoteMasks, ManualCategory, ManualNoteHierarchy};
use crate::reference_tui::{
    InteractiveReviewModel, MIN_HEIGHT, MIN_WIDTH, ReferenceTerminal, accent_style, border_style,
    centered, has_command_modifier, is_control_c_event, render_scrollable_panel, secondary_style,
    terminal_safe,
};
use crate::sse_mask_review::highlighted_note;
use crate::titled_merge_hierarchy::TitledMergeHierarchy;

const CONTROLS: &str = "In categories, j/k or Up/Down chooses an item; Enter/l or Right opens it. h, Backspace or Escape returns to the parent. Child categories are separate from the actions for viewing all notes or notes outside children.\n\nIn original notes, h/l or Left/Right changes the note; j/k or Up/Down scrolls. Backspace or Escape returns to the category choices.\n\nCtrl-D/U scrolls half a page; Ctrl-F/B or PageDown/PageUp scrolls a full page. gg or Home goes to the top; G or End goes to the end. ? shows the current category's analysis and these controls. Q or Ctrl-C exits.\n\nThis manual proposal is read-only. Nothing is written or approved.";

const CATEGORY_CONTROLS: &str = "In categories, only immediate child categories are listed. j/k or Up/Down chooses a child; Enter/l or Right descends into it, including a category with no children. N opens all original notes at the CURRENT category, including descendants and deduplicating shared notes. h, Backspace or Escape returns to the parent.\n\nWhen masks are supplied, each note shows one combined ⟦highlight⟧ covering all its mask ranges in the current category, including descendants. Masks belonging only to other branches are excluded. h/l or Left/Right changes the note; j/k or Up/Down scrolls. Backspace or Escape returns to the same category menu and selection.\n\nPaths use Category > Child > Grandchild and wrap. If older ancestors cannot fit above the notes, an ellipsis marks them and the complete path appears in this analysis screen.\n\nCtrl-D/U scrolls half a page; Ctrl-F/B or PageDown/PageUp scrolls a full page. gg or Home goes to the top; G or End goes to the end. ? shows the current category's analysis and these controls. Q or Ctrl-C exits.\n\nThis category hierarchy is read-only. Nothing is written or approved.";

struct CategoryFrame {
    node_id: String,
    cursor: usize,
}

struct NoteBrowser {
    note_ids: Vec<String>,
    cursor: usize,
    scroll: u16,
    leave_category: bool,
    outside_children: bool,
}

pub struct ManualNoteExplorer {
    hierarchy: ManualNoteHierarchy,
    categories_only: bool,
    category_masks: Option<CategoryNoteMasks>,
    merge_origin: Option<(String, usize)>,
    categories: Vec<CategoryFrame>,
    notes: Option<NoteBrowser>,
    analysis_scroll: Option<u16>,
    half_page_lines: u16,
    pending_g: bool,
    interaction_enabled: bool,
}

impl ManualNoteExplorer {
    pub fn new(hierarchy: ManualNoteHierarchy) -> Self {
        Self::with_categories_only(hierarchy, false)
    }

    /// Browse immediate children, with original notes opened separately using N.
    pub fn categories(hierarchy: ManualNoteHierarchy) -> Self {
        Self::with_categories_only(hierarchy, true)
    }

    pub fn categories_with_masks(
        hierarchy: ManualNoteHierarchy,
        masks: Option<CategoryNoteMasks>,
    ) -> Self {
        let mut model = Self::categories(hierarchy);
        model.category_masks = masks;
        model
    }

    fn with_categories_only(hierarchy: ManualNoteHierarchy, categories_only: bool) -> Self {
        let mut model = Self {
            categories: vec![CategoryFrame {
                node_id: hierarchy.root_node_id.clone(),
                cursor: 0,
            }],
            hierarchy,
            categories_only,
            category_masks: None,
            merge_origin: None,
            notes: None,
            analysis_scroll: None,
            half_page_lines: 1,
            pending_g: false,
            interaction_enabled: true,
        };
        if !categories_only && model.category().children.is_empty() {
            model.show_notes(false, false);
        }
        model
    }

    pub fn from_merge(hierarchy: TitledMergeHierarchy) -> Self {
        let mut path = vec![hierarchy.start_group_id.to_string()];
        let mut model = Self::new(hierarchy.hierarchy);
        model.merge_origin = Some((hierarchy.run_id, hierarchy.min_notes));
        while path.last().expect("starting group") != &model.hierarchy.root_node_id {
            let child = path.last().expect("starting group");
            let parent = model
                .hierarchy
                .nodes
                .values()
                .find(|node| node.children.contains(child))
                .expect("validated complete merge hierarchy");
            path.push(parent.node_id.clone());
        }
        path.reverse();
        model.categories = path
            .iter()
            .enumerate()
            .map(|(index, id)| CategoryFrame {
                node_id: id.clone(),
                cursor: path
                    .get(index + 1)
                    .and_then(|child| {
                        model.hierarchy.nodes[id]
                            .children
                            .iter()
                            .position(|id| id == child)
                    })
                    .unwrap_or(0),
            })
            .collect();
        model.notes = None;
        if model.category().children.is_empty() {
            model.show_notes(false, model.categories.len() > 1);
        }
        model
    }

    fn category_title(&self, id: &str) -> String {
        let label = terminal_safe(&self.hierarchy.nodes[id].label);
        match &self.merge_origin {
            Some((run, _)) => format!("{}/{id} · {label}", terminal_safe(run)),
            None => label,
        }
    }

    fn merge_notice(&self) -> Option<String> {
        self.merge_origin.as_ref().map(|(run, minimum)| {
            format!(
                "{} · provisional titles · minimum {minimum} notes · read-only",
                terminal_safe(run)
            )
        })
    }

    fn category(&self) -> &ManualCategory {
        &self.hierarchy.nodes[&self.categories.last().expect("root category").node_id]
    }

    fn breadcrumb(&self) -> String {
        if self.merge_origin.is_some() {
            let title = self.category_title(&self.category().node_id);
            // An immediate parent and current title remain legible even deep in the tree.
            return if self.categories.len() > 1 {
                let parent = &self.categories[self.categories.len() - 2].node_id;
                format!("Parent: {}\n{title}", self.category_title(parent))
            } else {
                title
            };
        }
        self.categories
            .iter()
            .map(|frame| terminal_safe(&self.hierarchy.nodes[&frame.node_id].label))
            .collect::<Vec<_>>()
            .join(" > ")
    }

    fn menu_items(&self) -> Vec<String> {
        let category = self.category();
        let mut items = category
            .children
            .iter()
            .map(|id| {
                format!(
                    "{} · {}",
                    self.category_title(id),
                    note_count(self.hierarchy.note_ids(id).len())
                )
            })
            .collect::<Vec<_>>();
        if self.categories_only {
            return items;
        }
        items.push(format!(
            "View all {}",
            note_count(self.hierarchy.note_ids(&category.node_id).len())
        ));
        let outside = self.hierarchy.outside_child_note_ids(&category.node_id);
        if !category.children.is_empty() && !outside.is_empty() {
            items.push(format!(
                "View {} outside children",
                note_count(outside.len())
            ));
        }
        items
    }

    fn show_notes(&mut self, outside_children: bool, leave_category: bool) {
        let id = &self.category().node_id;
        let note_ids = if outside_children {
            self.hierarchy.outside_child_note_ids(id)
        } else {
            self.hierarchy.note_ids(id)
        };
        if !note_ids.is_empty() {
            self.notes = Some(NoteBrowser {
                note_ids,
                cursor: 0,
                scroll: 0,
                leave_category,
                outside_children,
            });
        }
    }

    fn open(&mut self) {
        let cursor = self.categories.last().expect("root category").cursor;
        if let Some(child) = self.category().children.get(cursor).cloned() {
            self.categories.push(CategoryFrame {
                node_id: child,
                cursor: 0,
            });
            if !self.categories_only && self.category().children.is_empty() {
                self.show_notes(false, true);
            }
        } else if !self.categories_only {
            self.show_notes(cursor > self.category().children.len(), false);
        }
    }

    fn back(&mut self) {
        if self.analysis_scroll.take().is_some() {
            return;
        }
        if let Some(notes) = self.notes.take() {
            if notes.leave_category && self.categories.len() > 1 {
                self.categories.pop();
            }
        } else if self.categories.len() > 1 {
            self.categories.pop();
        }
    }

    fn move_by(&mut self, delta: isize) {
        if let Some(scroll) = self.analysis_scroll.as_mut() {
            *scroll = usize::from(*scroll)
                .saturating_add_signed(delta)
                .min(u16::MAX as usize) as u16;
        } else if let Some(notes) = self.notes.as_mut() {
            notes.scroll = usize::from(notes.scroll)
                .saturating_add_signed(delta)
                .min(u16::MAX as usize) as u16;
        } else {
            let maximum = self.menu_items().len().saturating_sub(1);
            let frame = self.categories.last_mut().expect("root category");
            frame.cursor = frame.cursor.saturating_add_signed(delta).min(maximum);
        }
    }

    fn jump(&mut self, end: bool) {
        if let Some(scroll) = self.analysis_scroll.as_mut() {
            *scroll = if end { u16::MAX } else { 0 };
        } else if let Some(notes) = self.notes.as_mut() {
            notes.scroll = if end { u16::MAX } else { 0 };
        } else {
            let cursor = if end {
                self.menu_items().len().saturating_sub(1)
            } else {
                0
            };
            self.categories.last_mut().expect("root category").cursor = cursor;
        }
    }

    pub fn handle_event(&mut self, event: Event) -> bool {
        if is_control_c_event(&event) {
            return true;
        }
        let Event::Key(key) = event else {
            return false;
        };
        if key.kind == KeyEventKind::Release {
            return false;
        }
        let previous_g = std::mem::take(&mut self.pending_g);
        if !has_command_modifier(key.modifiers) && matches!(key.code, KeyCode::Char('q' | 'Q')) {
            return true;
        }
        if !self.interaction_enabled {
            return false;
        }
        if key.modifiers == KeyModifiers::CONTROL {
            let half = self.half_page_lines as isize;
            match key.code {
                KeyCode::Char('d') => self.move_by(half),
                KeyCode::Char('u') => self.move_by(-half),
                KeyCode::Char('f') => self.move_by(half * 2),
                KeyCode::Char('b') => self.move_by(-half * 2),
                _ => {}
            }
            return false;
        }
        if has_command_modifier(key.modifiers) {
            return false;
        }
        let code = match key.code {
            KeyCode::Char('h') => KeyCode::Left,
            KeyCode::Char('j') => KeyCode::Down,
            KeyCode::Char('k') => KeyCode::Up,
            KeyCode::Char('l') => KeyCode::Right,
            KeyCode::Char('G') => KeyCode::End,
            KeyCode::Char('g') if previous_g => KeyCode::Home,
            KeyCode::Char('g') => {
                self.pending_g = true;
                return false;
            }
            other => other,
        };
        match code {
            KeyCode::Esc | KeyCode::Backspace => self.back(),
            KeyCode::Char('?') => {
                self.analysis_scroll = if self.analysis_scroll.is_some() {
                    None
                } else {
                    Some(0)
                };
            }
            KeyCode::Down => self.move_by(1),
            KeyCode::Up => self.move_by(-1),
            KeyCode::PageDown => self.move_by(self.half_page_lines as isize * 2),
            KeyCode::PageUp => self.move_by(-(self.half_page_lines as isize) * 2),
            KeyCode::Home => self.jump(false),
            KeyCode::End => self.jump(true),
            _ if self.analysis_scroll.is_some() => {}
            KeyCode::Char('n' | 'N') if self.categories_only && self.notes.is_none() => {
                self.show_notes(false, false);
            }
            KeyCode::Left | KeyCode::Right if self.notes.is_some() => {
                let notes = self.notes.as_mut().expect("note browser");
                notes.cursor = if code == KeyCode::Left {
                    notes.cursor.saturating_sub(1)
                } else {
                    (notes.cursor + 1).min(notes.note_ids.len() - 1)
                };
                notes.scroll = 0;
            }
            KeyCode::Left => self.back(),
            KeyCode::Enter | KeyCode::Right if self.notes.is_none() => self.open(),
            _ => {}
        }
        false
    }

    pub fn render(&mut self, frame: &mut Frame<'_>) {
        self.render_with_minimum(frame, frame.area(), MIN_HEIGHT);
    }

    pub(crate) fn render_in_area(&mut self, frame: &mut Frame<'_>, area: Rect) {
        // A comparison reserves one terminal row for its return shortcut.
        self.render_with_minimum(frame, area, MIN_HEIGHT - 1);
    }

    fn render_with_minimum(&mut self, frame: &mut Frame<'_>, area: Rect, minimum_height: u16) {
        self.interaction_enabled = area.width >= MIN_WIDTH && area.height >= minimum_height;
        if !self.interaction_enabled {
            frame.render_widget(
                Paragraph::new(format!(
                    "Resize to at least {MIN_WIDTH} × {minimum_height}. Q or Ctrl-C exits."
                ))
                .wrap(Wrap { trim: false }),
                area,
            );
            return;
        }
        let area = centered(area);
        let breadcrumb = self.breadcrumb();
        let mut heading = if self.analysis_scroll.is_some() {
            format!("{breadcrumb}\nCategory analysis · read-only")
        } else if let Some(notes) = &self.notes {
            let note = &self.hierarchy.notes[&notes.note_ids[notes.cursor]];
            format!(
                "{breadcrumb}{}\n{} · Note {} of {}",
                if notes.outside_children {
                    " · Notes outside children"
                } else {
                    ""
                },
                terminal_safe(&note.note_short_id),
                notes.cursor + 1,
                notes.note_ids.len(),
            )
        } else {
            format!(
                "{breadcrumb} · {}{}",
                note_count(self.hierarchy.note_ids(&self.category().node_id).len()),
                if !self.categories_only && self.merge_origin.is_none() {
                    "\nManual hierarchy · read-only"
                } else {
                    ""
                }
            )
        };
        if self.categories_only {
            heading.push_str(&format!(
                "\n{} · category hierarchy · read-only",
                terminal_safe(&self.hierarchy.hierarchy_id)
            ));
        }
        if let Some(notice) = self.merge_notice() {
            heading.push('\n');
            heading.push_str(&notice);
        }
        let heading_budget = if self.categories_only {
            (area.height / 4).max(3)
        } else {
            area.height.saturating_sub(9)
        };
        let suffix = heading[breadcrumb.len()..].to_owned();
        let mut shortened_path = false;
        if self.categories_only {
            for first in 1..self.categories.len() {
                if Paragraph::new(heading.as_str())
                    .wrap(Wrap { trim: false })
                    .line_count(area.width)
                    <= usize::from(heading_budget)
                {
                    break;
                }
                let path = self.categories[first..]
                    .iter()
                    .map(|category| self.category_title(&category.node_id))
                    .collect::<Vec<_>>()
                    .join(" > ");
                heading = format!("… > {path}{suffix}");
                shortened_path = true;
            }
        }
        let heading = Paragraph::new(heading).wrap(Wrap { trim: false });
        let heading_height = u16::try_from(heading.line_count(area.width))
            .unwrap_or(u16::MAX)
            .clamp(2, heading_budget);
        let rows = Layout::vertical([
            Constraint::Length(heading_height),
            Constraint::Min(5),
            Constraint::Length(3),
        ])
        .split(area);
        frame.render_widget(heading.style(accent_style()), rows[0]);
        if self.analysis_scroll.is_some() {
            let controls = if self.categories_only {
                CATEGORY_CONTROLS.to_owned()
            } else if self.merge_origin.is_some() {
                CONTROLS.replace("This manual proposal", "This saved hierarchy")
            } else {
                CONTROLS.to_owned()
            };
            let content = format!(
                "{}{}\n\n{controls}",
                if shortened_path {
                    format!("{breadcrumb}\n\n")
                } else {
                    String::new()
                },
                terminal_safe(&self.category().analysis)
            );
            render_scrollable_panel(
                frame,
                rows[1],
                "Analysis and controls",
                &content,
                self.analysis_scroll.as_mut().expect("analysis screen"),
                &mut self.half_page_lines,
                false,
            );
        } else if let Some(notes) = &mut self.notes {
            let note = &self.hierarchy.notes[&notes.note_ids[notes.cursor]];
            let (content, title) = if let Some(masks) = &self.category_masks {
                let category = &self.categories.last().expect("root category").node_id;
                (
                    highlighted_note(&note.content, masks.spans(category, &note.note_short_id)),
                    "Note · combined category mask",
                )
            } else {
                (note.content.clone(), "Note")
            };
            let content = terminal_safe(&content);
            render_scrollable_panel(
                frame,
                rows[1],
                title,
                &content,
                &mut notes.scroll,
                &mut self.half_page_lines,
                false,
            );
        } else {
            self.render_menu(frame, rows[1]);
        }
        let controls = if self.analysis_scroll.is_some() {
            "j/k ↑/↓ Scroll  Ctrl-D/U Half page  gg/G Top/end\nBackspace/Esc Back  Q Quit"
        } else if self.notes.is_some() {
            "h/l ←/→ Previous/next note  j/k ↑/↓ Scroll\nCtrl-D/U Half page  gg/G Top/end  ? Analysis\nBackspace/Esc Back  Q Quit"
        } else if self.categories_only {
            "j/k ↑/↓ Choose  Enter/l Descend  N Notes at current category\nh/Backspace/Esc Parent  gg/G Top/end  ? Analysis  Q Quit"
        } else {
            "j/k ↑/↓ Choose  Enter/l Open  h/l ←/→ Back/open\nBackspace/Esc Back  gg/G Top/end  ? Analysis  Q Quit"
        };
        frame.render_widget(Paragraph::new(controls).style(secondary_style()), rows[2]);
    }

    fn render_menu(&mut self, frame: &mut Frame<'_>, area: Rect) {
        self.half_page_lines = (area.height.saturating_sub(2) / 2).max(1);
        let child_count = self.category().children.len();
        let block = Block::default()
            .borders(Borders::ALL)
            .border_style(border_style())
            .title(if self.categories_only {
                "Categories"
            } else {
                "Categories and note actions"
            });
        if self.categories_only && child_count == 0 {
            frame.render_widget(
                Paragraph::new("No child categories. N opens notes at this category.")
                    .style(secondary_style())
                    .wrap(Wrap { trim: false })
                    .block(block),
                area,
            );
            return;
        }
        let items = self
            .menu_items()
            .into_iter()
            .enumerate()
            .map(|(index, text)| {
                let style = if index < child_count {
                    accent_style()
                } else {
                    secondary_style()
                };
                ListItem::new(Line::styled(text, style))
            })
            .collect::<Vec<_>>();
        let cursor = self.categories.last().expect("root category").cursor;
        frame.render_stateful_widget(
            List::new(items)
                .highlight_symbol("▶ ")
                .highlight_style(accent_style())
                .block(block),
            area,
            &mut ListState::default().with_selected(Some(cursor)),
        );
    }
}

fn note_count(count: usize) -> String {
    format!("{count} {}", if count == 1 { "note" } else { "notes" })
}

impl InteractiveReviewModel for ManualNoteExplorer {
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

pub fn run_manual_note_explorer(hierarchy: ManualNoteHierarchy) -> io::Result<()> {
    run_note_explorer(ManualNoteExplorer::new(hierarchy))
}

pub fn run_category_note_explorer(
    hierarchy: ManualNoteHierarchy,
    masks: Option<CategoryNoteMasks>,
) -> io::Result<()> {
    run_note_explorer(ManualNoteExplorer::categories_with_masks(hierarchy, masks))
}

pub fn run_titled_merge_note_explorer(hierarchy: TitledMergeHierarchy) -> io::Result<()> {
    run_note_explorer(ManualNoteExplorer::from_merge(hierarchy))
}

fn run_note_explorer(mut model: ManualNoteExplorer) -> io::Result<()> {
    let mut terminal = ReferenceTerminal::new()?;
    terminal.run_review_model_stateful(&mut model, false)?;
    Ok(())
}
