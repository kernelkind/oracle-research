//! Read-only exploration of saved HDBSCAN hierarchies and optional display views.

use std::collections::{BTreeMap, BTreeSet};
use std::io;

use crossterm::event::{Event, KeyCode, KeyEventKind, KeyModifiers};
use ratatui::Frame;
use ratatui::layout::{Constraint, Layout, Rect};
use ratatui::style::{Color, Style};
use ratatui::text::Line;
use ratatui::widgets::{Block, Borders, Paragraph};
use unicode_width::UnicodeWidthStr;

use crate::hdbscan_hierarchy::{Hierarchy, MaskInstance};
use crate::reference_tui::{
    InteractiveReviewModel, ReferenceTerminal, accent_style, has_command_modifier,
    is_control_c_event, secondary_style, terminal_safe,
};

#[derive(Clone, Debug, PartialEq, Eq)]
enum Selection {
    Group(Vec<usize>),
    Mask(Vec<usize>, usize, usize),
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

const HELP_COUNTS: &str = "Group numbers are the IDs in the saved tree, not generated subject titles.\n\
Counts are distinct source notes in the group, including all descendants. They are not additive: the same note can appear in several children.";

const HELP_CONTROLS: &str = "V numbers identify the original mask/vector records. Identical masks from the same note sharing one vector are shown together, with every ID retained.\n\n\
h/j/k/l match Left/Down/Up/Right. Up/Down selects a group or mask. Right expands a group; when already expanded it moves into its contents. Left collapses a group or selects the containing group. In notes and help, j/k scroll.\n\
U shows the parent of the displayed branch, preserving expansion and selection. F focuses the selected group as the displayed branch.\n\
Ctrl-F/B or PageDown/PageUp scroll a page; Ctrl-U/D scroll half a page up/down. gg or Home moves to the beginning; G or End moves to the end. Shift-Left/Right scroll horizontally in deep branches.\n\
Enter opens a mask's full original note with inline brackets, or toggles a selected group. Escape returns from the note or this help.";

#[derive(Clone, Copy, PartialEq, Eq)]
pub enum HierarchyView {
    Condensed,
    Selection,
    NoteNavigation,
    NoteNavigationMinimum(usize),
    Infomap,
    Containment,
}

pub struct HierarchyExplorer {
    hierarchy: Hierarchy,
    run_id: Option<String>,
    note_short_ids: BTreeMap<String, String>,
    show_parent_masks: Option<bool>,
    view: HierarchyView,
    branch: Vec<usize>,
    expanded: BTreeSet<Vec<usize>>,
    child_order: BTreeMap<Vec<usize>, Vec<usize>>,
    selected: Selection,
    hidden_parent_masks: BTreeSet<(usize, usize, usize)>,
    scroll: usize,
    horizontal: usize,
    height: usize,
    viewport: Option<(u16, u16)>,
    follow_selection: bool,
    detail: Option<Detail>,
    detail_scroll: usize,
    pending_g: bool,
}

impl HierarchyExplorer {
    pub fn new(hierarchy: Hierarchy, start: Option<usize>) -> Result<Self, String> {
        Self::with_view(hierarchy, start, HierarchyView::Condensed)
    }

    /// Display an already-projected saved selection without changing its members.
    pub fn new_selection(hierarchy: Hierarchy, start: Option<usize>) -> Result<Self, String> {
        Self::with_view(hierarchy, start, HierarchyView::Selection)
    }

    /// Display the note-based projection of a saved complete merge tree.
    pub fn new_note_navigation(hierarchy: Hierarchy, start: Option<usize>) -> Result<Self, String> {
        Self::with_view(hierarchy, start, HierarchyView::NoteNavigation)
    }

    /// Display native Infomap modules with their original source note IDs.
    pub fn new_infomap(
        hierarchy: Hierarchy,
        start: Option<usize>,
        note_short_ids: BTreeMap<String, String>,
    ) -> Result<Self, String> {
        Ok(Self::with_view(hierarchy, start, HierarchyView::Infomap)?
            .with_note_short_ids(note_short_ids)
            .with_parent_mask_toggle())
    }

    /// Display every retained containment edge, including shared groups.
    pub fn new_containment(
        hierarchy: Hierarchy,
        start: Option<usize>,
        note_short_ids: BTreeMap<String, String>,
    ) -> Result<Self, String> {
        Ok(
            Self::with_view(hierarchy, start, HierarchyView::Containment)?
                .with_note_short_ids(note_short_ids)
                .with_parent_mask_toggle(),
        )
    }

    pub(crate) fn with_view(
        hierarchy: Hierarchy,
        start: Option<usize>,
        view: HierarchyView,
    ) -> Result<Self, String> {
        let start = start.unwrap_or(hierarchy.root);
        if !hierarchy.groups.contains_key(&start) {
            return Err(format!("unknown group {start}"));
        }
        let (branch, expanded) = initial_paths(&hierarchy, start);
        let hidden_parent_masks = if view == HierarchyView::Selection {
            BTreeSet::new()
        } else {
            repeated_parent_masks(&hierarchy)
        };
        Ok(Self {
            hierarchy,
            run_id: None,
            note_short_ids: BTreeMap::new(),
            show_parent_masks: None,
            view,
            branch: branch.clone(),
            expanded,
            child_order: BTreeMap::new(),
            selected: Selection::Group(branch),
            hidden_parent_masks,
            scroll: 0,
            horizontal: 0,
            height: 12,
            viewport: None,
            follow_selection: true,
            detail: None,
            detail_scroll: 0,
            pending_g: false,
        })
    }

    pub(crate) fn with_note_short_ids(mut self, note_short_ids: BTreeMap<String, String>) -> Self {
        self.note_short_ids = note_short_ids;
        self
    }

    /// Identify the saved experiment without changing any hierarchy membership.
    pub fn with_run_id(mut self, run_id: Option<String>) -> Self {
        self.run_id = run_id;
        self
    }

    fn run_suffix(&self) -> String {
        self.run_id
            .as_ref()
            .map(|id| format!(" · {}", id.escape_debug()))
            .unwrap_or_default()
    }

    pub(crate) fn with_parent_mask_toggle(mut self) -> Self {
        self.show_parent_masks = Some(false);
        self
    }

    fn mask_ids(&self, aliases: &[MaskInstance], mask: &MaskInstance) -> String {
        let ids = matching_ids(aliases, mask);
        match self.note_short_ids.get(&mask.note_id) {
            Some(short_id) => format!("{ids} · {}", terminal_safe(short_id)),
            None => ids,
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
        if key.modifiers == KeyModifiers::CONTROL {
            match key.code {
                KeyCode::Char('d') => self.scroll_by((self.height / 2).max(1) as isize),
                KeyCode::Char('u') => self.scroll_by(-((self.height / 2).max(1) as isize)),
                KeyCode::Char('f') => self.scroll_by(self.height as isize),
                KeyCode::Char('b') => self.scroll_by(-(self.height as isize)),
                _ => {}
            }
            return false;
        }
        if has_command_modifier(key.modifiers) {
            return false;
        }
        // Route aliases through the same actions in every view.
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
        if matches!(code, KeyCode::Char('q' | 'Q')) {
            return true;
        }
        if self.detail.is_some() {
            match code {
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
            match code {
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
        match code {
            KeyCode::Char('a') if self.show_parent_masks.is_some() => {
                let show = !self.show_parent_masks.unwrap();
                self.show_parent_masks = Some(show);
                if !show {
                    if let Selection::Mask(path, point, alias) = &self.selected {
                        if self.hidden_parent_masks.contains(&(
                            *path.last().unwrap(),
                            *point,
                            *alias,
                        )) {
                            self.selected = Selection::Group(path.clone());
                        }
                    }
                }
                self.follow_selection = true;
            }
            KeyCode::Char('?') => {
                self.detail = Some(Detail::Help);
                self.detail_scroll = 0;
            }
            KeyCode::Up => self.move_selection(-1),
            KeyCode::Down => self.move_selection(1),
            KeyCode::Right => {
                if let Selection::Group(path) = &self.selected {
                    if !self.expanded.insert(path.clone()) {
                        self.move_selection(1);
                    }
                    self.follow_selection = true;
                }
            }
            KeyCode::Left => self.collapse_or_parent(),
            KeyCode::Enter => match &self.selected {
                Selection::Group(path) => {
                    if !self.expanded.remove(path) {
                        self.expanded.insert(path.clone());
                    }
                    self.follow_selection = true;
                }
                Selection::Mask(_, point, alias) => {
                    self.detail = Some(Detail::Note(*point, *alias));
                    self.detail_scroll = 0;
                }
            },
            KeyCode::Char('u' | 'U') => self.show_parent(),
            KeyCode::Char('f' | 'F') => {
                if let Selection::Group(path) = &self.selected {
                    self.branch = path.clone();
                    self.expanded.insert(path.clone());
                    self.scroll = 0;
                    self.horizontal = 0;
                    self.follow_selection = true;
                }
            }
            KeyCode::PageUp => self.scroll_by(-(self.height as isize)),
            KeyCode::PageDown => self.scroll_by(self.height as isize),
            KeyCode::Home => {
                self.selected = Selection::Group(self.branch.clone());
                self.scroll = 0;
                self.follow_selection = true;
            }
            KeyCode::End => {
                if let Some(last) = self.rows().into_iter().rev().find_map(|row| row.selection) {
                    self.selected = last;
                }
                self.scroll = usize::MAX;
                self.follow_selection = true;
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
        self.selected =
            selections[index.saturating_add_signed(delta).min(selections.len() - 1)].clone();
        self.follow_selection = true;
    }

    fn show_parent(&mut self) {
        if self.branch.len() > 1 {
            let parent_path = self.branch[..self.branch.len() - 1].to_vec();
            let parent = *parent_path.last().unwrap();
            if self.view != HierarchyView::Selection {
                let children = self
                    .child_order
                    .entry(parent_path.clone())
                    .or_insert_with(|| self.hierarchy.groups[&parent].children.clone());
                // Reorder only on upward navigation, so opening a child does not
                // move it. Stable sorting also preserves order on return visits.
                children.sort_by_key(|child| {
                    let mut path = parent_path.clone();
                    path.push(*child);
                    self.expanded.contains(&path)
                });
            }
            self.expanded.insert(parent_path.clone());
            self.branch = parent_path;
            self.follow_selection = true;
        }
    }

    fn collapse_or_parent(&mut self) {
        match self.selected.clone() {
            Selection::Group(path) if self.expanded.remove(&path) => {}
            Selection::Group(mut path) => {
                if path == self.branch {
                    self.show_parent();
                } else if path.len() > 1 {
                    path.pop();
                    self.selected = Selection::Group(path);
                }
            }
            Selection::Mask(path, _, _) => self.selected = Selection::Group(path),
        }
        self.follow_selection = true;
    }

    fn rows(&self) -> Vec<Row> {
        enum PendingRows {
            Group(Vec<usize>, String, String),
            Masks(Vec<usize>, String),
        }

        let mut rows = Vec::new();
        // Explicit stack preserves the saved tree even for deeply nested input.
        let mut stack = vec![PendingRows::Group(
            self.branch.clone(),
            String::new(),
            String::new(),
        )];
        while let Some(pending) = stack.pop() {
            let (path, prefix, continuation) = match pending {
                PendingRows::Group(path, prefix, continuation) => (path, prefix, continuation),
                PendingRows::Masks(path, continuation) => {
                    self.append_masks(&mut rows, &path, &continuation);
                    continue;
                }
            };
            let id = *path.last().unwrap();
            let group = &self.hierarchy.groups[&id];
            let expanded = self.expanded.contains(&path);
            let same_notes = self.view == HierarchyView::Containment
                && path.len() > 1
                && self.hierarchy.groups[&path[path.len() - 2]].note_count == group.note_count;
            rows.push(Row {
                selection: Some(Selection::Group(path.clone())),
                prefix,
                content: format!(
                    "{} {id} · {} {}{}{}",
                    if expanded { "▾" } else { "▸" },
                    group.note_count,
                    if group.note_count == 1 {
                        "note"
                    } else {
                        "notes"
                    },
                    if same_notes { " · same notes" } else { "" },
                    if self.view == HierarchyView::Containment
                        && id != self.hierarchy.root
                        && group.parent.is_none()
                    {
                        " · shared"
                    } else {
                        ""
                    }
                ),
            });
            if !expanded {
                continue;
            }
            // LIFO ordering lets selection children stay reachable before long
            // direct-member lists, while raw parent masks stay before children.
            if self.view == HierarchyView::Selection {
                stack.push(PendingRows::Masks(path.clone(), continuation.clone()));
            }
            let children = self.child_order.get(&path).unwrap_or(&group.children);
            for (index, child) in children.iter().enumerate().rev() {
                let last = index == children.len() - 1
                    && (self.view != HierarchyView::Selection || group.vectors.is_empty());
                let mut child_path = path.clone();
                child_path.push(*child);
                stack.push(PendingRows::Group(
                    child_path,
                    format!("{continuation}{} ", if last { "└─" } else { "├─" }),
                    format!("{continuation}{}", if last { "   " } else { "│  " }),
                ));
            }
            if self.view != HierarchyView::Selection {
                stack.push(PendingRows::Masks(path, continuation));
            }
        }
        rows
    }

    fn append_masks(&self, rows: &mut Vec<Row>, path: &[usize], continuation: &str) {
        let id = *path.last().unwrap();
        let group = &self.hierarchy.groups[&id];
        let point_prefix = format!(
            "{continuation}{}  ",
            if group.children.is_empty() || self.view == HierarchyView::Selection {
                " "
            } else {
                "│"
            }
        );
        let mut needs_header = !group.children.is_empty();
        for point in &group.vectors {
            let aliases = &self.hierarchy.vectors[point];
            let mut seen = BTreeSet::new();
            for (index, mask) in aliases.iter().enumerate() {
                if (self.show_parent_masks != Some(true)
                    && self.hidden_parent_masks.contains(&(id, *point, index)))
                    || !seen.insert((&mask.note_id, &mask.byte_spans))
                {
                    continue;
                }
                if needs_header {
                    rows.push(Row {
                        selection: None,
                        prefix: if self.view == HierarchyView::Selection {
                            format!("{continuation}└─ ")
                        } else {
                            point_prefix.clone()
                        },
                        content: if self.view == HierarchyView::Selection {
                            "Masks outside retained child groups:"
                        } else {
                            "Masks outside its child groups:"
                        }
                        .to_owned(),
                    });
                    needs_header = false;
                }
                let ids = self.mask_ids(aliases, mask);
                rows.push(Row {
                    selection: Some(Selection::Mask(path.to_vec(), *point, index)),
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
    }

    fn help(&self) -> String {
        let minimum = match self.view {
            HierarchyView::NoteNavigation => {
                "Each group choice contains at least two distinct notes. ".to_owned()
            }
            HierarchyView::NoteNavigationMinimum(count) => format!(
                "Each group choice contains at least {count} distinct notes. Smaller groups are hidden; their masks remain at the nearest displayed ancestor. "
            ),
            _ => String::new(),
        };
        let (intro, masks, decisions) = if matches!(
            self.view,
            HierarchyView::NoteNavigation | HierarchyView::NoteNavigationMinimum(_)
        ) {
            (
                "This comparison uses the saved complete merge history. Group numbers are merge-tree IDs, not condensed-tree IDs.",
                "A child returning the same notes as its parent is collapsed. The parent keeps its complete membership; the remaining descendants are promoted. The root remains the full-corpus container, even below the minimum.\nAll masks remain at their nearest retained ancestor. A parent mask is hidden when its note occurs recursively in a child, including collapsed children.",
                "Going up places unopened children above expanded ones, preserving nesting. No new clustering, semantic judgments or subject titles are generated. These display rules do not establish semantic quality.",
            )
        } else if self.view == HierarchyView::Containment {
            (
                "This is a read-only view of the saved exact-containment DAG. Groups with fewer than two distinct notes are hidden; their masks remain at the nearest displayed ancestors. The full-corpus root is always retained.",
                "A shared group appears under every saved parent with the same ID and complete membership. Each route expands independently. Counts use distinct source notes, never sums of overlapping children. Equal-note transitions remain and are marked same notes; these do not narrow note discovery. A parent mask starts hidden when its note occurs recursively in any child, including collapsed children; a reveals every parent mask.",
                "U follows the route used to reach the displayed branch, placing unopened children above opened ones. A shared --start-at, including shared ancestry, starts at the root with all routes to that group open. No memberships are expanded, no parent is chosen for shared groups, and no semantic judgments or subject titles are generated.",
            )
        } else if self.view == HierarchyView::Infomap {
            (
                "This is a read-only view of the saved Infomap native module hierarchy.",
                "Every module path prefix remains a group, including one-note and one-vector modules. Direct masks stay in their saved module. A parent mask starts hidden when its note occurs recursively in a child, including collapsed children; a reveals every parent mask.",
                "No modules are removed or converted to binary merges. No merge distances, semantic judgments, or subject titles are generated. Going up preserves nesting and puts unopened children above expanded ones.",
            )
        } else if self.view == HierarchyView::Selection {
            (
                "This is a read-only view of the saved selection proposal.",
                "Groups skipped in this view remain in the raw tree. Every mask remains; masks outside retained children are shown at their displayed ancestor.",
                "Children are shown before direct masks. No groups are judged or given generated titles; no acceptance decisions are made.",
            )
        } else {
            (
                "This is a read-only view of the saved HDBSCAN hierarchy.",
                "Masks outside its child groups remain in the saved tree. A parent mask is hidden here when its source note occurs anywhere in a child subtree, including collapsed children. Counts and saved memberships are unchanged.",
                "Going up places unopened child groups above expanded ones. Opening or collapsing them afterward keeps that order. The saved tree is unchanged; no groups are removed, judged, or relabeled.",
            )
        };
        let comparison = if self.show_parent_masks.is_some() {
            "\n\nIn this comparison, a shows or hides repeated parent masks without changing any saved memberships. They start hidden. N numbers identify source notes from the vector map; V numbers remain the original mask IDs."
        } else {
            ""
        };
        let counts = if matches!(
            self.view,
            HierarchyView::Infomap | HierarchyView::Containment
        ) {
            "Group numbers identify groups within this run. The same number in another run can have different contents.\nCounts are distinct source notes including all descendants and aliases. They are not additive: a note can appear in several children."
        } else {
            HELP_COUNTS
        };
        format!(
            "{intro}\n\n{counts}\n\n{minimum}{masks}\n{HELP_CONTROLS}\n\n{decisions}{comparison} Nothing is written to the source files or review sessions. Q or Ctrl-C exits."
        )
    }

    pub fn render(&mut self, frame: &mut Frame<'_>) {
        self.render_in_area(frame, frame.area());
    }

    pub(crate) fn render_in_area(&mut self, frame: &mut Frame<'_>, area: Rect) {
        let dimensions = (area.width, area.height);
        if self.viewport != Some(dimensions) {
            self.viewport = Some(dimensions);
            self.follow_selection = true;
        }
        if area.width < 60 || area.height < 12 {
            frame.render_widget(Paragraph::new("Resize to at least 60 × 12. Q exits."), area);
            return;
        }
        let detail = self.detail.map(|detail| {
            let (mut title, content) = match detail {
                Detail::Help => (
                    if self.view == HierarchyView::Selection {
                        "HDBv2 selection help · proposal · read-only".to_owned()
                    } else if self.view == HierarchyView::Infomap {
                        format!("Infomap hierarchy help{}", self.run_suffix())
                    } else if self.view == HierarchyView::Containment {
                        format!("Containment hierarchy help{}", self.run_suffix())
                    } else {
                        "Hierarchy help".to_owned()
                    },
                    self.help(),
                ),
                Detail::Note(point, alias) => {
                    let aliases = &self.hierarchy.vectors[&point];
                    let mask = &aliases[alias];
                    let title = if matches!(
                        self.view,
                        HierarchyView::Infomap | HierarchyView::Containment
                    ) {
                        format!(
                            "Original note{} · {}\nSource note ID: {}",
                            self.run_suffix(),
                            self.mask_ids(aliases, mask),
                            terminal_safe(&mask.note_id)
                        )
                    } else {
                        format!("Original note · {}", self.mask_ids(aliases, mask))
                    };
                    (title, inline_note(mask))
                }
            };
            if self.show_parent_masks == Some(true) {
                title.push_str("\nAll parent masks shown in hierarchy");
            }
            let title = if matches!(
                self.view,
                HierarchyView::Infomap | HierarchyView::Containment
            ) {
                wrap_text(&title, usize::from(area.width)).join("\n")
            } else {
                title
            };
            (title, content)
        });
        let title_height = if matches!(
            self.view,
            HierarchyView::Infomap | HierarchyView::Containment
        ) {
            detail.as_ref().map_or(2, |(title, _)| {
                title
                    .lines()
                    .count()
                    .max(2)
                    .min(usize::from(area.height.saturating_sub(7))) as u16
            })
        } else {
            2
        };
        let areas = Layout::vertical([
            Constraint::Length(title_height),
            Constraint::Min(4),
            Constraint::Length(3),
        ])
        .split(area);
        let block = Block::default().borders(Borders::ALL);
        let inner = block.inner(areas[1]);
        self.height = usize::from(inner.height).max(1);
        if let Some((title, content)) = detail {
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
            frame.render_widget(
                Paragraph::new(
                    "j/k ↑/↓ Scroll  Ctrl-F/B Page  gg/G Top/end\nEsc Return to hierarchy  Q Quit",
                )
                .style(secondary_style()),
                areas[2],
            );
            return;
        }
        let rows = self.rows();
        let selected_prefix = rows
            .iter()
            .find(|row| row.selection.as_ref() == Some(&self.selected))
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
                physical.push((row.selection.clone(), clip_left(&text, self.horizontal)));
            }
        }
        self.scroll = self.scroll.min(physical.len().saturating_sub(self.height));
        if let Some(first) = physical
            .iter()
            .position(|(id, _)| id.as_ref() == Some(&self.selected))
        {
            let last = physical
                .iter()
                .rposition(|(id, _)| id.as_ref() == Some(&self.selected))
                .unwrap();
            if self.follow_selection {
                if first < self.scroll {
                    self.scroll = first;
                } else if first >= self.scroll + self.height {
                    self.scroll = first.saturating_sub(self.height - 1);
                }
            } else if last < self.scroll || first >= self.scroll.saturating_add(self.height) {
                // Keep keyboard selection attached to visible content after scrolling.
                if let Some(id) = physical
                    .iter()
                    .skip(self.scroll)
                    .take(self.height)
                    .find_map(|(id, _)| id.clone())
                {
                    self.selected = id;
                }
            }
        }
        self.follow_selection = false;
        let branch = self.branch.last().unwrap();
        let mut title = format!(
            "{}\nShowing branch {} · {} {}",
            match self.view {
                HierarchyView::Selection => "HDBv2 selection · proposal · read-only".to_owned(),
                HierarchyView::Condensed => "HDBv2 hierarchy · read-only".to_owned(),
                HierarchyView::NoteNavigation =>
                    "Merge-tree note navigation · comparison · read-only".to_owned(),
                HierarchyView::NoteNavigationMinimum(count) =>
                    format!("Merge-tree note navigation · minimum {count} notes · read-only"),
                HierarchyView::Infomap => format!(
                    "Infomap hierarchy{} · native modules · read-only",
                    self.run_suffix()
                ),
                HierarchyView::Containment => format!(
                    "Containment hierarchy{} · exact membership · read-only",
                    self.run_suffix()
                ),
            },
            branch,
            self.hierarchy.groups[branch].note_count,
            if self.hierarchy.groups[branch].note_count == 1 {
                "note"
            } else {
                "notes"
            },
        );
        if self.show_parent_masks == Some(true) {
            title.push_str(" · All parent masks");
        }
        frame.render_widget(Paragraph::new(title).style(accent_style()), areas[0]);
        let mut marked = false;
        let lines = physical
            .iter()
            .skip(self.scroll)
            .take(self.height)
            .map(|(id, text)| {
                let selected = id.as_ref() == Some(&self.selected);
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
        let enter = if matches!(self.selected, Selection::Mask(_, _, _)) {
            "Enter Full note"
        } else {
            "Enter Toggle group"
        };
        let parent_masks = match self.show_parent_masks {
            Some(true) => "  a Hide parent masks",
            Some(false) => "  a Show parent masks",
            None => "",
        };
        frame.render_widget(Paragraph::new(format!("j/k ↑/↓ Select  h/l ←/→ Collapse/expand  PgUp/PgDn Scroll\nU Show parent  F Focus group  {enter}\ngg/G Top/end  ? Help  Q Quit{parent_masks}")).style(secondary_style()), areas[2]);
    }
}

/// Ordinary loading records only one route. A requested shared group explicitly
/// opens all ancestor routes, rather than choosing a parent or inventing IDs.
fn initial_paths(hierarchy: &Hierarchy, start: usize) -> (Vec<usize>, BTreeSet<Vec<usize>>) {
    let mut parents = BTreeMap::<usize, Vec<usize>>::new();
    for group in hierarchy.groups.values() {
        for child in &group.children {
            parents.entry(*child).or_default().push(group.id);
        }
    }
    let mut route = vec![start];
    while let Some(ancestors) = parents.get(route.last().unwrap()) {
        if ancestors.len() != 1 {
            let mut relevant = BTreeSet::new();
            let mut pending = vec![start];
            while let Some(id) = pending.pop() {
                if relevant.insert(id) {
                    pending.extend(parents.get(&id).into_iter().flatten().copied());
                }
            }
            let branch = vec![hierarchy.root];
            let mut expanded = BTreeSet::new();
            let mut pending = vec![branch.clone()];
            while let Some(path) = pending.pop() {
                for child in &hierarchy.groups[path.last().unwrap()].children {
                    if relevant.contains(child) {
                        let mut child_path = path.clone();
                        child_path.push(*child);
                        pending.push(child_path);
                    }
                }
                expanded.insert(path);
            }
            return (branch, expanded);
        }
        route.push(ancestors[0]);
    }
    route.reverse();
    (route.clone(), BTreeSet::from([route]))
}

/// Compare direct masks with all original child memberships, not visible rows.
fn repeated_parent_masks(hierarchy: &Hierarchy) -> BTreeSet<(usize, usize, usize)> {
    let mut order = Vec::with_capacity(hierarchy.groups.len());
    let mut visited = BTreeSet::new();
    let mut pending = vec![(hierarchy.root, false)];
    while let Some((id, finished)) = pending.pop() {
        if finished {
            order.push(id);
        } else if visited.insert(id) {
            pending.push((id, true));
            pending.extend(
                hierarchy.groups[&id]
                    .children
                    .iter()
                    .map(|child| (*child, false)),
            );
        }
    }

    let mut subtree_notes: BTreeMap<usize, BTreeSet<&str>> = BTreeMap::new();
    let mut hidden = BTreeSet::new();
    // Visit each saved group once, retaining child sets until all parents use them.
    let mut remaining_parents = BTreeMap::<usize, usize>::new();
    for group in hierarchy.groups.values() {
        for child in &group.children {
            *remaining_parents.entry(*child).or_default() += 1;
        }
    }
    for id in order {
        let group = &hierarchy.groups[&id];
        let mut notes = BTreeSet::new();
        for child in &group.children {
            let remaining = remaining_parents.get_mut(child).unwrap();
            *remaining -= 1;
            if *remaining == 0 {
                notes.append(&mut subtree_notes.remove(child).expect("child already visited"));
            } else {
                notes.extend(&subtree_notes[child]);
            }
        }
        for point in &group.vectors {
            for (index, mask) in hierarchy.vectors[point].iter().enumerate() {
                if notes.contains(mask.note_id.as_str()) {
                    hidden.insert((id, *point, index));
                }
            }
        }
        // Add direct membership only after filtering: another mask at this same
        // group is not a child. Hidden masks still belong to the saved subtree.
        for point in &group.vectors {
            notes.extend(
                hierarchy.vectors[point]
                    .iter()
                    .map(|mask| mask.note_id.as_str()),
            );
        }
        subtree_notes.insert(id, notes);
    }
    hidden
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

pub fn run_hierarchy_explorer(
    hierarchy: Hierarchy,
    start: Option<usize>,
    view: HierarchyView,
    note_short_ids: BTreeMap<String, String>,
    run_id: Option<String>,
) -> io::Result<()> {
    let mut model = match view {
        HierarchyView::Condensed => HierarchyExplorer::new(hierarchy, start),
        HierarchyView::Selection => HierarchyExplorer::new_selection(hierarchy, start),
        HierarchyView::NoteNavigation => HierarchyExplorer::new_note_navigation(hierarchy, start),
        HierarchyView::NoteNavigationMinimum(_) => {
            HierarchyExplorer::with_view(hierarchy, start, view)
        }
        HierarchyView::Infomap => HierarchyExplorer::new_infomap(hierarchy, start, note_short_ids),
        HierarchyView::Containment => {
            HierarchyExplorer::new_containment(hierarchy, start, note_short_ids)
        }
    }
    .map_err(io::Error::other)?
    .with_run_id(run_id);
    let mut terminal = ReferenceTerminal::new()?;
    terminal.run_review_model_stateful(&mut model, false)?;
    Ok(())
}
