//! Read-only categories over original notes: schema 1 trees and schema 2 DAGs.

use std::collections::{BTreeMap, BTreeSet};
use std::error::Error;
use std::fs;
use std::path::Path;

use serde::Deserialize;
use sha2::{Digest, Sha256};

#[derive(Clone, Debug)]
pub struct ManualNoteHierarchy {
    pub hierarchy_id: String,
    pub root_node_id: String,
    pub nodes: BTreeMap<String, ManualCategory>,
    pub notes: BTreeMap<String, ManualNote>,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ManualCategory {
    pub node_id: String,
    pub label: String,
    pub children: Vec<String>,
    /// Direct memberships, using the declared short note IDs.
    pub note_ids: Vec<String>,
    #[serde(default)]
    pub analysis: String,
}

/// Child choices for one route, without changing saved category memberships.
#[derive(Clone, Debug)]
pub struct CategoryNavigation {
    pub children: Vec<String>,
    pub collapsed: Vec<String>,
    pub outside_note_ids: Vec<String>,
}

#[derive(Clone, Debug)]
pub struct ManualNote {
    pub note_id: String,
    pub note_short_id: String,
    pub content: String,
}

type NoteMaskRanges = BTreeMap<String, BTreeMap<String, Vec<(usize, usize)>>>;
type CategoryMaskInstances = BTreeMap<String, BTreeMap<String, Vec<MaskInstance>>>;

/// One original mask; identical masks retain all their original vector IDs.
#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct MaskInstance {
    pub ids: Vec<String>,
    pub byte_spans: Vec<(usize, usize)>,
}

/// Source-validated category highlights and optional original masks with IDs.
#[derive(Clone, Debug)]
pub struct CategoryNoteMasks {
    ranges: NoteMaskRanges,
    instances: CategoryMaskInstances,
}

impl CategoryNoteMasks {
    pub fn spans(&self, category: &str, note: &str) -> &[(usize, usize)] {
        &self.ranges[category][note]
    }

    pub fn instances(&self, category: &str, note: &str) -> &[MaskInstance] {
        self.instances
            .get(category)
            .and_then(|notes| notes.get(note))
            .map_or(&[], Vec::as_slice)
    }
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Spec {
    schema_version: u32,
    hierarchy_id: String,
    source_sha256: String,
    root_node_id: String,
    notes: Vec<NoteReference>,
    nodes: Vec<ManualCategory>,
    #[serde(default)]
    note_masks: Option<NoteMaskRanges>,
    #[serde(default)]
    mask_instances: Option<CategoryMaskInstances>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct NoteReference {
    note_id: String,
    note_short_id: String,
}

#[derive(Deserialize)]
struct Source {
    notes: Vec<SourceNote>,
}

#[derive(Deserialize)]
struct SourceNote {
    note_id: String,
    text: String,
}

impl ManualNoteHierarchy {
    pub fn load(spec_path: &Path, source_path: &Path) -> Result<Self, Box<dyn Error>> {
        Self::load_with_masks(spec_path, source_path).map(|(hierarchy, _)| hierarchy)
    }

    pub fn load_with_masks(
        spec_path: &Path,
        source_path: &Path,
    ) -> Result<(Self, Option<CategoryNoteMasks>), Box<dyn Error>> {
        let spec: Spec = serde_json::from_slice(&fs::read(spec_path)?)?;
        let bytes = fs::read(source_path)?;
        if !matches!(spec.schema_version, 1 | 2) || spec.hierarchy_id.trim().is_empty() {
            return Err("invalid manual note hierarchy identity".into());
        }
        if format!("{:x}", Sha256::digest(&bytes)) != spec.source_sha256 {
            return Err("manual note hierarchy source SHA-256 mismatch".into());
        }
        let source: Source = serde_json::from_slice(&bytes)?;
        let mut originals = BTreeMap::new();
        for note in source.notes {
            if originals.insert(note.note_id, note.text).is_some() {
                return Err("source repeats a note ID".into());
            }
        }
        let mut notes = BTreeMap::new();
        let mut source_ids = BTreeSet::new();
        for reference in spec.notes {
            let content = originals
                .get(&reference.note_id)
                .ok_or_else(|| format!("source note {} is missing", reference.note_id))?;
            let short = reference.note_short_id;
            if short.trim().is_empty()
                || content.trim().is_empty()
                || !source_ids.insert(reference.note_id.clone())
                || notes.contains_key(&short)
            {
                return Err("manual hierarchy note references must be unique and nonempty".into());
            }
            notes.insert(
                short.clone(),
                ManualNote {
                    note_id: reference.note_id,
                    note_short_id: short,
                    content: content.clone(),
                },
            );
        }
        let mut nodes = BTreeMap::new();
        for node in spec.nodes {
            if node.node_id.trim().is_empty()
                || node.label.trim().is_empty()
                || (node.children.is_empty() && node.note_ids.is_empty())
                || nodes.insert(node.node_id.clone(), node).is_some()
            {
                return Err("manual categories must be unique, named, and nonempty".into());
            }
        }
        if !nodes.contains_key(&spec.root_node_id) {
            return Err("manual hierarchy root is missing".into());
        }
        let mut parents = BTreeMap::<String, usize>::new();
        let mut used_notes = BTreeSet::new();
        for node in nodes.values() {
            let mut children = BTreeSet::new();
            for child in &node.children {
                if !nodes.contains_key(child) || !children.insert(child) {
                    return Err(format!(
                        "category {} has a missing or repeated child",
                        node.node_id
                    )
                    .into());
                }
                *parents.entry(child.clone()).or_default() += 1;
            }
            let mut local_notes = BTreeSet::new();
            for note in &node.note_ids {
                if !notes.contains_key(note) || !local_notes.insert(note.clone()) {
                    return Err(format!(
                        "category {} has a missing or repeated note",
                        node.node_id
                    )
                    .into());
                }
            }
            used_notes.extend(local_notes);
        }
        for node in nodes.keys() {
            let count = parents.get(node).copied().unwrap_or(0);
            let valid = if node == &spec.root_node_id {
                count == 0
            } else if spec.schema_version == 1 {
                count == 1
            } else {
                count >= 1
            };
            if !valid {
                return Err(format!("category {node} has an invalid parent count").into());
            }
        }
        // Visit each child after all of its parents, not once per path to it.
        let mut reached = 0;
        let mut pending = vec![spec.root_node_id.clone()];
        while let Some(node) = pending.pop() {
            reached += 1;
            for child in &nodes[&node].children {
                let remaining = parents
                    .get_mut(child)
                    .expect("validated child parent count");
                *remaining -= 1;
                if *remaining == 0 {
                    pending.push(child.clone());
                }
            }
        }
        if reached != nodes.len() {
            return Err("manual hierarchy contains a cycle or unreachable category".into());
        }
        if used_notes != notes.keys().cloned().collect() {
            return Err("every declared category and note must be reachable".into());
        }
        let hierarchy = Self {
            hierarchy_id: spec.hierarchy_id,
            root_node_id: spec.root_node_id,
            nodes,
            notes,
        };
        let mut masks = spec
            .note_masks
            .map(|ranges| hierarchy.validate_masks(ranges))
            .transpose()?;
        if let Some(instances) = spec.mask_instances {
            let masks = masks
                .as_mut()
                .ok_or("individual masks require note masks")?;
            hierarchy.validate_instances(&instances, masks)?;
            masks.instances = instances;
        }
        Ok((hierarchy, masks))
    }

    fn validate_instances(
        &self,
        instances: &CategoryMaskInstances,
        masks: &CategoryNoteMasks,
    ) -> Result<(), Box<dyn Error>> {
        if instances.keys().ne(masks.ranges.keys()) {
            return Err("individual masks must cover exactly the declared categories".into());
        }
        let mut identities = BTreeMap::new();
        let mut combined = BTreeMap::new();
        for (category, notes) in instances {
            if notes.keys().ne(masks.ranges[category].keys()) {
                return Err("individual masks must cover exactly the category's notes".into());
            }
            let mut combined_notes = BTreeMap::new();
            for (note, records) in notes {
                let text = &self.notes[note].content;
                let mut seen_ids = BTreeSet::new();
                let mut seen_spans = BTreeSet::new();
                let mut spans = Vec::new();
                for record in records {
                    if record.ids.is_empty()
                        || record
                            .ids
                            .iter()
                            .any(|id| id.trim().is_empty() || !seen_ids.insert(id))
                        || record.byte_spans.is_empty()
                        || !seen_spans.insert(&record.byte_spans)
                        || record.byte_spans.iter().any(|&(a, b)| {
                            a >= b
                                || b > text.len()
                                || !text.is_char_boundary(a)
                                || !text.is_char_boundary(b)
                        })
                        || record
                            .byte_spans
                            .windows(2)
                            .any(|pair| pair[0].1 > pair[1].0)
                    {
                        return Err(format!("invalid individual mask for {category}/{note}").into());
                    }
                    for id in &record.ids {
                        let identity = (note, &record.byte_spans);
                        if identities
                            .insert(id, identity)
                            .is_some_and(|old| old != identity)
                        {
                            return Err(
                                format!("mask ID {id} has conflicting source ranges").into()
                            );
                        }
                    }
                    spans.extend(record.byte_spans.iter().copied());
                }
                combined_notes.insert(note.clone(), spans);
            }
            combined.insert(category.clone(), combined_notes);
        }
        if self.validate_masks(combined)?.ranges != masks.ranges {
            return Err("individual masks do not reproduce the saved combined masks".into());
        }
        Ok(())
    }

    fn validate_masks(
        &self,
        mut ranges: NoteMaskRanges,
    ) -> Result<CategoryNoteMasks, Box<dyn Error>> {
        if ranges.keys().ne(self.nodes.keys()) {
            return Err("note masks must cover exactly the declared categories".into());
        }
        for (category, notes) in &mut ranges {
            if notes.keys().ne(self.note_ids(category).iter()) {
                return Err(
                    format!("category {category} masks must cover exactly its notes").into(),
                );
            }
            for (note, spans) in notes {
                let text = &self.notes[note].content;
                // An explicit empty selection keeps an SP subject's source post
                // inspectable without inventing a highlighted fragment.
                if spans.iter().any(|&(start, end)| {
                    start >= end
                        || end > text.len()
                        || !text.is_char_boundary(start)
                        || !text.is_char_boundary(end)
                }) {
                    return Err(format!("invalid UTF-8 mask ranges for {category}/{note}").into());
                }
                spans.sort_unstable();
                let mut union: Vec<(usize, usize)> = Vec::new();
                for &(start, end) in spans.iter() {
                    if let Some(last) = union.last_mut().filter(|last| start <= last.1) {
                        last.1 = last.1.max(end);
                    } else {
                        union.push((start, end));
                    }
                }
                *spans = union;
            }
        }
        for (parent, node) in &self.nodes {
            for child in &node.children {
                for (note, spans) in &ranges[child] {
                    let parent_spans = &ranges[parent][note];
                    if spans.iter().any(|&(start, end)| {
                        !parent_spans.iter().any(|&(a, b)| a <= start && end <= b)
                    }) {
                        return Err(
                            format!("category {parent} mask omits child {child}/{note}").into()
                        );
                    }
                }
            }
        }
        Ok(CategoryNoteMasks {
            ranges,
            instances: BTreeMap::new(),
        })
    }

    /// Whether any category is referenced by more than one parent.
    pub fn has_shared_categories(&self) -> bool {
        let mut children = BTreeSet::new();
        self.nodes
            .values()
            .flat_map(|node| &node.children)
            .any(|child| !children.insert(child))
    }

    /// Absorb one-child steps, retaining each parent's identity and full membership.
    /// Existing category mask lookups stay valid because retained memberships do not change.
    /// Shared categories disable absorption: return zero without changing any category.
    pub fn absorb_single_children(&mut self) -> usize {
        if self.has_shared_categories() {
            return 0;
        }
        let before = self.nodes.len();
        let mut pending = vec![self.root_node_id.clone()];
        while let Some(id) = pending.pop() {
            while self.nodes[&id].children.len() == 1 {
                let child_id = self.nodes[&id].children[0].clone();
                let child = self
                    .nodes
                    .remove(&child_id)
                    .expect("validated child category");
                let parent = self.nodes.get_mut(&id).expect("retained parent category");
                parent.note_ids.extend(child.note_ids);
                parent.note_ids.sort();
                parent.note_ids.dedup();
                parent.children = child.children;
            }
            pending.extend(self.nodes[&id].children.iter().cloned());
        }
        before - self.nodes.len()
    }

    /// Full membership of a category, deduplicated across its descendants.
    pub fn note_ids(&self, node_id: &str) -> Vec<String> {
        let mut notes = BTreeSet::new();
        let mut seen = BTreeSet::new();
        let mut pending = vec![node_id];
        while let Some(id) = pending.pop() {
            if !seen.insert(id) {
                continue;
            }
            let node = &self.nodes[id];
            notes.extend(node.note_ids.iter().cloned());
            pending.extend(node.children.iter().map(String::as_str));
        }
        notes.into_iter().collect()
    }

    pub fn outside_child_note_ids(&self, node_id: &str) -> Vec<String> {
        let node = &self.nodes[node_id];
        let descendants: BTreeSet<_> = node
            .children
            .iter()
            .flat_map(|child| self.note_ids(child))
            .collect();
        node.note_ids
            .iter()
            .filter(|id| !descendants.contains(*id))
            .cloned()
            .collect::<BTreeSet<_>>()
            .into_iter()
            .collect()
    }

    /// Build the displayed choices from a validated, unchanged hierarchy.
    /// Equal-note steps are skipped locally; shared children remain on other routes.
    pub fn category_navigation(
        &self,
        node_id: &str,
        collapse_equal_notes: bool,
    ) -> CategoryNavigation {
        let notes = self.note_ids(node_id);
        let mut children = Vec::new();
        let mut collapsed = Vec::new();
        let mut child_notes = BTreeSet::new();
        let mut seen = BTreeSet::new();
        let mut pending = self.nodes[node_id]
            .children
            .iter()
            .rev()
            .collect::<Vec<_>>();
        while let Some(child) = pending.pop() {
            if !seen.insert(child) {
                continue;
            }
            let membership = self.note_ids(child);
            if collapse_equal_notes && membership == notes {
                collapsed.push(child.clone());
                pending.extend(self.nodes[child].children.iter().rev());
            } else {
                children.push(child.clone());
                child_notes.extend(membership);
            }
        }
        CategoryNavigation {
            children,
            collapsed,
            outside_note_ids: notes
                .into_iter()
                .filter(|note| !child_notes.contains(note))
                .collect(),
        }
    }
}
