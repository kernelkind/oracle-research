//! Read-only manual categories over original notes, independent of vector groups.

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

#[derive(Clone, Debug)]
pub struct ManualNote {
    pub note_id: String,
    pub note_short_id: String,
    pub content: String,
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
        let spec: Spec = serde_json::from_slice(&fs::read(spec_path)?)?;
        let bytes = fs::read(source_path)?;
        if spec.schema_version != 1 || spec.hierarchy_id.trim().is_empty() {
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
            let expected = usize::from(node != &spec.root_node_id);
            if parents.get(node).copied().unwrap_or(0) != expected {
                return Err(format!("category {node} has an invalid parent count").into());
            }
        }
        let mut seen = BTreeSet::new();
        let mut pending = vec![spec.root_node_id.clone()];
        while let Some(node) = pending.pop() {
            if !seen.insert(node.clone()) {
                return Err("manual hierarchy contains a cycle".into());
            }
            pending.extend(nodes[&node].children.iter().cloned());
        }
        if seen.len() != nodes.len() || used_notes != notes.keys().cloned().collect() {
            return Err("every declared category and note must be reachable".into());
        }
        Ok(Self {
            hierarchy_id: spec.hierarchy_id,
            root_node_id: spec.root_node_id,
            nodes,
            notes,
        })
    }

    /// Full membership of a category, deduplicated across its descendants.
    pub fn note_ids(&self, node_id: &str) -> Vec<String> {
        let mut notes = BTreeSet::new();
        let mut pending = vec![node_id];
        while let Some(id) = pending.pop() {
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
}
