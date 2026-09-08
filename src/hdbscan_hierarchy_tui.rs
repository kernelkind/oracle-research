//! Read-only exploration of the saved HDBSCAN condensed hierarchy.

use std::collections::{BTreeMap, BTreeSet};
use std::io;

use crossterm::event::{Event, KeyCode, KeyEventKind, KeyModifiers};
use ratatui::Frame;
use ratatui::layout::{Constraint, Layout};
use ratatui::style::{Color, Style};
use ratatui::text::Line;
use ratatui::widgets::{Block, Borders, Paragraph};
use unicode_width::UnicodeWidthStr;

use crate::hdbscan_hierarchy::{Hierarchy, MaskInstance};
use crate::reference_tui::{
    InteractiveReviewModel, ReferenceTerminal, accent_style, has_command_modifier,
    is_control_c_event, secondary_style, terminal_safe,
};

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum Selection {
    Group(usize),
    Mask(usize, usize),
}

#[derive(Clone, Copy)]
enum Detail {
    Note(usize, usize),
    Help,
}

struct Row {
    selection: Option<Selection>,
    prefix: String,
    content: String,
}

const HELP: &str = "This is a read-only view of the saved HDBSCAN hierarchy.\n\n\
Group numbers are the IDs in the saved tree, not generated subject titles.\n\
Counts are distinct source notes in the group, including all descendants. They are not additive: the same note can appear in several children.\n\n\
Masks outside its child groups belong to that parent in the saved tree. They have not been discarded or moved into a made-up child.\n\
V numbers identify the original mask/vector records. Identical masks from the same note sharing one vector are shown together, with every ID retained.\n\n\
Up/Down selects a group or mask. Right expands a group; when already expanded it moves into its contents. Left collapses a group or selects the containing group.\n\
U shows the parent of the displayed branch, preserving expansion and selection. F focuses the selected group as the displayed branch.\n\
PageUp/PageDown and Ctrl-U/Ctrl-D scroll. Home/End move to the beginning/end. Shift-Left/Right scroll horizontally in deep branches.\n\
Enter opens a mask's full original note with inline brackets, or toggles a selected group. Escape returns from the note or this help.\n\n\
No groups or members are filtered, judged, relabeled, or rearranged. Nothing is written to the source files or review sessions. Q or Ctrl-C exits.";

pub struct HierarchyExplorer {
    hierarchy: Hierarchy,
    branch: usize,
    expanded: BTreeSet<usize>,
    selected: Selection,
    point_parents: BTreeMap<usize, usize>,
    scroll: usize,
    horizontal: usize,
    height: usize,
    viewport: Option<(u16, u16)>,
    follow_selection: bool,
    detail: Option<Detail>,
    detail_scroll: usize,
}

impl HierarchyExplorer {
    pub fn new(hierarchy: Hierarchy, start: Option<usize>) -> Result<Self, String> {
        let branch = start.unwrap_or(hierarchy.root);
        if !hierarchy.groups.contains_key(&branch) {
            return Err(format!("unknown group {branch}"));
        }
        let point_parents = hierarchy
            .groups
            .values()
            .flat_map(|group| group.vectors.iter().map(move |point| (*point, group.id)))
            .collect();
        Ok(Self {
            hierarchy,
            branch,
            expanded: BTreeSet::from([branch]),
            selected: Selection::Group(branch),
            point_parents,
            scroll: 0,
            horizontal: 0,
            height: 12,
            viewport: None,
            follow_selection: true,
            detail: None,
            detail_scroll: 0,
        })
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
        if key.modifiers == KeyModifiers::CONTROL {
            match key.code {
                KeyCode::Char('d') => self.scroll_by((self.height / 2).max(1) as isize),
                KeyCode::Char('u') => self.scroll_by(-((self.height / 2).max(1) as isize)),
                _ => {}
            }
            return false;
        }
        if has_command_modifier(key.modifiers) {
            return false;
        }
        if matches!(key.code, KeyCode::Char('q' | 'Q')) {
            return true;
        }
        if self.detail.is_some() {
            match key.code {
                KeyCode::Esc => {
                    self.detail = None;
                    self.follow_selection = true;
                }
                KeyCode::Up => self.scroll_by(-1),
                KeyCode::Down => self.scroll_by(1),
                KeyCode::PageUp => self.scroll_by(-(self.height as isize)),
                KeyCode::PageDown => self.scroll_by(self.height as isize),
                KeyCode::Home => self.detail_scroll = 0,
                KeyCode::End => self.detail_scroll = usize::MAX,
                _ => {}
            }
            return false;
        }
        if key.modifiers.contains(KeyModifiers::SHIFT) {
            match key.code {
                KeyCode::Left => {
                    self.horizontal = self.horizontal.saturating_sub(8);
                    self.follow_selection = false;
                    return false;
                }
                KeyCode::Right => {
                    self.horizontal = self.horizontal.saturating_add(8);
                    self.follow_selection = false;
                    return false;
                }
                _ => {}
            }
        }
        match key.code {
            KeyCode::Char('?') => {
                self.detail = Some(Detail::Help);
                self.detail_scroll = 0;
            }
            KeyCode::Up => self.move_selection(-1),
            KeyCode::Down => self.move_selection(1),
            KeyCode::Right => {
                if let Selection::Group(id) = self.selected {
                    if !self.expanded.insert(id) {
                        self.move_selection(1);
                    }
                    self.follow_selection = true;
                }
            }
            KeyCode::Left => self.collapse_or_parent(),
            KeyCode::Enter => match self.selected {
                Selection::Group(id) => {
                    if !self.expanded.remove(&id) {
                        self.expanded.insert(id);
                    }
                    self.follow_selection = true;
                }
                Selection::Mask(point, alias) => {
                    self.detail = Some(Detail::Note(point, alias));
                    self.detail_scroll = 0;
                }
            },
            KeyCode::Char('u' | 'U') => self.show_parent(),
            KeyCode::Char('f' | 'F') => {
                if let Selection::Group(id) = self.selected {
                    self.branch = id;
                    self.expanded.insert(id);
                    self.scroll = 0;
                    self.horizontal = 0;
                    self.follow_selection = true;
                }
            }
            KeyCode::PageUp => self.scroll_by(-(self.height as isize)),
            KeyCode::PageDown => self.scroll_by(self.height as isize),
            KeyCode::Home => {
                self.selected = Selection::Group(self.branch);
                self.scroll = 0;
                self.follow_selection = true;
            }
            KeyCode::End => {
                self.scroll = usize::MAX;
                self.follow_selection = false;
            }
            _ => {}
        }
        false
    }

    fn scroll_by(&mut self, delta: isize) {
        let scroll = if self.detail.is_some() {
            &mut self.detail_scroll
        } else {
            &mut self.scroll
        };
        *scroll = scroll.saturating_add_signed(delta);
        self.follow_selection = false;
    }

    fn move_selection(&mut self, delta: isize) {
        let selections = self
            .rows()
            .into_iter()
            .filter_map(|row| row.selection)
            .collect::<Vec<_>>();
        let index = selections
            .iter()
            .position(|item| *item == self.selected)
            .unwrap_or(0);
        self.selected = selections[index.saturating_add_signed(delta).min(selections.len() - 1)];
        self.follow_selection = true;
    }

    fn show_parent(&mut self) {
        if let Some(parent) = self.hierarchy.groups[&self.branch].parent {
            self.expanded.insert(parent);
            self.branch = parent;
            self.follow_selection = true;
        }
    }

    fn collapse_or_parent(&mut self) {
        match self.selected {
            Selection::Group(id) if self.expanded.remove(&id) => {}
            Selection::Group(id) => {
                if id == self.branch {
                    self.show_parent();
                } else if let Some(parent) = self.hierarchy.groups[&id].parent {
                    self.selected = Selection::Group(parent);
                }
            }
            Selection::Mask(point, _) => {
                self.selected = Selection::Group(self.point_parents[&point])
            }
        }
        self.follow_selection = true;
    }

    fn rows(&self) -> Vec<Row> {
        let mut rows = Vec::new();
        // Explicit stack preserves the saved tree even for deeply nested input.
        let mut stack = vec![(self.branch, String::new(), String::new())];
        while let Some((id, prefix, continuation)) = stack.pop() {
            let group = &self.hierarchy.groups[&id];
            let expanded = self.expanded.contains(&id);
            rows.push(Row {
                selection: Some(Selection::Group(id)),
                prefix,
                content: format!(
                    "{} {id} · {} {}",
                    if expanded { "▾" } else { "▸" },
                    group.note_count,
                    if group.note_count == 1 {
                        "note"
                    } else {
                        "notes"
                    }
                ),
            });
            if !expanded {
                continue;
            }
            let point_prefix = format!(
                "{continuation}{}  ",
                if group.children.is_empty() {
                    " "
                } else {
                    "│"
                }
            );
            if !group.children.is_empty() && !group.vectors.is_empty() {
                rows.push(Row {
                    selection: None,
                    prefix: point_prefix.clone(),
                    content: "Masks outside its child groups:".to_owned(),
                });
            }
            for point in &group.vectors {
                let aliases = &self.hierarchy.vectors[point];
                let mut seen = BTreeSet::new();
                for (index, mask) in aliases.iter().enumerate() {
                    if !seen.insert((&mask.note_id, &mask.byte_spans)) {
                        continue;
                    }
                    let ids = matching_ids(aliases, mask);
                    rows.push(Row {
                        selection: Some(Selection::Mask(*point, index)),
                        prefix: point_prefix.clone(),
                        content: format!(
                            "{ids}  {}",
                            mask.fragments
                                .iter()
                                .map(|text| format!("⟦{}⟧", terminal_safe(text)))
                                .collect::<Vec<_>>()
                                .join(" ")
                        ),
                    });
                }
            }
            for (index, child) in group.children.iter().enumerate().rev() {
                let last = index == group.children.len() - 1;
                stack.push((
                    *child,
                    format!("{continuation}{} ", if last { "└─" } else { "├─" }),
                    format!("{continuation}{}", if last { "   " } else { "│  " }),
                ));
            }
        }
        rows
    }

    pub fn render(&mut self, frame: &mut Frame<'_>) {
        let area = frame.area();
        let dimensions = (area.width, area.height);
        if self.viewport != Some(dimensions) {
            self.viewport = Some(dimensions);
            self.follow_selection = true;
        }
        if area.width < 60 || area.height < 12 {
            frame.render_widget(Paragraph::new("Resize to at least 60 × 12. Q exits."), area);
            return;
        }
        let areas = Layout::vertical([
            Constraint::Length(2),
            Constraint::Min(4),
            Constraint::Length(3),
        ])
        .split(area);
        let block = Block::default().borders(Borders::ALL);
        let inner = block.inner(areas[1]);
        self.height = usize::from(inner.height).max(1);
        if let Some(detail) = self.detail {
            let (title, content) = match detail {
                Detail::Help => ("Hierarchy help".to_owned(), HELP.to_owned()),
                Detail::Note(point, alias) => {
                    let aliases = &self.hierarchy.vectors[&point];
                    let mask = &aliases[alias];
                    (
                        format!("Original note · {}", matching_ids(aliases, mask)),
                        inline_note(mask),
                    )
                }
            };
            frame.render_widget(Paragraph::new(title).style(accent_style()), areas[0]);
            let lines = wrap_text(&content, usize::from(inner.width));
            self.detail_scroll = self
                .detail_scroll
                .min(lines.len().saturating_sub(self.height));
            frame.render_widget(
                Paragraph::new(
                    lines
                        .into_iter()
                        .skip(self.detail_scroll)
                        .take(self.height)
                        .map(Line::raw)
                        .collect::<Vec<_>>(),
                )
                .block(block),
                areas[1],
            );
            frame.render_widget(Paragraph::new("↑/↓ Scroll  PgUp/PgDn Page  Home/End Beginning/end\nEsc Return to hierarchy  Q Quit").style(secondary_style()), areas[2]);
            return;
        }
        let rows = self.rows();
        let selected_prefix = rows
            .iter()
            .find(|row| row.selection == Some(self.selected))
            .map(|row| row.prefix.width())
            .unwrap_or(0);
        if self.follow_selection {
            self.horizontal = selected_prefix.saturating_sub(usize::from(inner.width) / 3);
        }
        let max_indent = rows.iter().map(|row| row.prefix.width()).max().unwrap_or(0);
        self.horizontal = self.horizontal.min(max_indent);
        let mut physical = Vec::<(Option<Selection>, String)>::new();
        let width = usize::from(inner.width).saturating_sub(2);
        for row in rows {
            let prefix_width = row.prefix.width();
            let body_width = (width + self.horizontal)
                .saturating_sub(prefix_width)
                .max(16);
            for text in wrap_text(&row.content, body_width) {
                let text = format!("{}{text}", row.prefix);
                physical.push((row.selection, clip_left(&text, self.horizontal)));
            }
        }
        if let Some(first) = physical
            .iter()
            .position(|(id, _)| *id == Some(self.selected))
        {
            let last = physical
                .iter()
                .rposition(|(id, _)| *id == Some(self.selected))
                .unwrap();
            if self.follow_selection {
                if first < self.scroll {
                    self.scroll = first;
                } else if first >= self.scroll + self.height {
                    self.scroll = first.saturating_sub(self.height - 1);
                }
            } else if last < self.scroll || first >= self.scroll.saturating_add(self.height) {
                // Keep keyboard selection attached to visible content after scrolling.
                let top = self.scroll.min(physical.len().saturating_sub(self.height));
                if let Some(id) = physical
                    .iter()
                    .skip(top)
                    .take(self.height)
                    .find_map(|(id, _)| *id)
                {
                    self.selected = id;
                }
            }
        }
        self.scroll = self.scroll.min(physical.len().saturating_sub(self.height));
        self.follow_selection = false;
        let title = format!(
            "HDBv2 hierarchy · read-only\nShowing branch {} · {} {}",
            self.branch,
            self.hierarchy.groups[&self.branch].note_count,
            if self.hierarchy.groups[&self.branch].note_count == 1 {
                "note"
            } else {
                "notes"
            },
        );
        frame.render_widget(Paragraph::new(title).style(accent_style()), areas[0]);
        let mut marked = false;
        let lines = physical
            .iter()
            .skip(self.scroll)
            .take(self.height)
            .map(|(id, text)| {
                let selected = *id == Some(self.selected);
                let marker = if selected && !marked {
                    marked = true;
                    "▶ "
                } else {
                    "  "
                };
                let style = if selected {
                    Style::default().bg(Color::DarkGray).fg(Color::White)
                } else if matches!(id, Some(Selection::Group(_))) {
                    accent_style()
                } else if id.is_none() {
                    secondary_style()
                } else {
                    Style::default()
                };
                Line::styled(format!("{marker}{text}"), style)
            })
            .collect::<Vec<_>>();
        let position = format!(
            "Hierarchy · lines {}–{} of {}",
            self.scroll + 1,
            (self.scroll + self.height).min(physical.len()),
            physical.len()
        );
        frame.render_widget(Paragraph::new(lines).block(block.title(position)), areas[1]);
        let enter = if matches!(self.selected, Selection::Mask(_, _)) {
            "Enter Full note"
        } else {
            "Enter Toggle group"
        };
        frame.render_widget(Paragraph::new(format!("↑/↓ Select  ←/→ Collapse/expand  PgUp/PgDn Scroll\nU Show parent  F Focus group  {enter}\n? Help  Shift-←/→ Horizontal  Q Quit")).style(secondary_style()), areas[2]);
    }
}

fn matching_ids(aliases: &[MaskInstance], mask: &MaskInstance) -> String {
    aliases
        .iter()
        .filter(|other| other.note_id == mask.note_id && other.byte_spans == mask.byte_spans)
        .map(|other| terminal_safe(&other.id))
        .collect::<Vec<_>>()
        .join(", ")
}

fn inline_note(mask: &MaskInstance) -> String {
    let mut text = String::new();
    let mut previous = 0;
    for &(start, end) in &mask.byte_spans {
        text.push_str(&terminal_safe(&mask.text[previous..start]));
        text.push('⟦');
        text.push_str(&terminal_safe(&mask.text[start..end]));
        text.push('⟧');
        previous = end;
    }
    text.push_str(&terminal_safe(&mask.text[previous..]));
    text
}

fn wrap_text(text: &str, width: usize) -> Vec<String> {
    let width = width.max(1);
    let mut lines = Vec::new();
    for paragraph in text.split('\n') {
        let mut line = String::new();
        let mut cells = 0;
        for word in paragraph.split_inclusive(char::is_whitespace) {
            let word_width = word.width();
            if cells > 0 && cells + word_width > width {
                lines.push(line.trim_end().to_owned());
                line.clear();
                cells = 0;
            }
            for grapheme in Line::raw(word).styled_graphemes(Style::default()) {
                let size = grapheme.symbol.width();
                if cells + size > width && !line.is_empty() {
                    lines.push(std::mem::take(&mut line));
                    cells = 0;
                }
                line.push_str(grapheme.symbol);
                cells += size;
            }
        }
        lines.push(line.trim_end().to_owned());
    }
    lines
}

fn clip_left(text: &str, width: usize) -> String {
    let mut cells = 0;
    let mut output = String::new();
    for grapheme in Line::raw(text).styled_graphemes(Style::default()) {
        let size = grapheme.symbol.width();
        if cells >= width {
            output.push_str(grapheme.symbol);
        } else if cells + size > width {
            output.push_str(&" ".repeat(cells + size - width));
        }
        cells += size;
    }
    output
}

impl InteractiveReviewModel for HierarchyExplorer {
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

pub fn run_hierarchy_explorer(hierarchy: Hierarchy, start: Option<usize>) -> io::Result<()> {
    let mut model = HierarchyExplorer::new(hierarchy, start).map_err(io::Error::other)?;
    let mut terminal = ReferenceTerminal::new()?;
    terminal.run_review_model_stateful(&mut model, false)?;
    Ok(())
}
