//! Provisional titles over an unchanged saved note-navigation projection.

use std::collections::{BTreeMap, BTreeSet};
use std::error::Error;
use std::fs;
use std::path::Path;

use serde::Deserialize;
use sha2::{Digest, Sha256};

use crate::hdbscan_hierarchy::Hierarchy;
use crate::manual_note_hierarchy::{ManualCategory, ManualNote, ManualNoteHierarchy};

pub struct TitledMergeHierarchy {
    pub hierarchy: ManualNoteHierarchy,
    pub run_id: String,
    pub min_notes: usize,
    pub start_group_id: usize,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct TitleSpec {
    schema_version: u32,
    run_id: String,
    min_notes: usize,
    input_sha256: InputHashes,
    titles: Vec<Title>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct InputHashes {
    merge_history: String,
    vector_map: String,
    source_notes: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Title {
    group_id: usize,
    label: String,
    #[serde(default)]
    analysis: String,
}

#[derive(Deserialize)]
struct HistoryIdentity {
    run_id: String,
}

#[derive(Deserialize)]
struct VectorMap {
    vectors: Vec<NoteReference>,
}

#[derive(Deserialize)]
struct NoteReference {
    note_id: String,
    note_short_id: String,
}

impl TitledMergeHierarchy {
    pub fn load(
        history_path: &Path,
        vector_map_path: &Path,
        notes_path: &Path,
        titles_path: &Path,
        min_notes: usize,
    ) -> Result<Self, Box<dyn Error>> {
        let spec: TitleSpec = serde_json::from_slice(&fs::read(titles_path)?)?;
        if spec.schema_version != 1 || spec.run_id.trim().is_empty() {
            return Err("invalid titled merge hierarchy identity".into());
        }
        if spec.min_notes != min_notes {
            return Err("titles minimum note count does not match the requested projection".into());
        }
        for (name, path, expected) in [
            (
                "merge_history",
                history_path,
                &spec.input_sha256.merge_history,
            ),
            ("vector_map", vector_map_path, &spec.input_sha256.vector_map),
            ("source_notes", notes_path, &spec.input_sha256.source_notes),
        ] {
            if format!("{:x}", Sha256::digest(fs::read(path)?)) != *expected {
                return Err(format!("titled hierarchy {name} SHA-256 mismatch").into());
            }
        }
        let identity: HistoryIdentity = serde_json::from_slice(&fs::read(history_path)?)?;
        if identity.run_id != spec.run_id {
            return Err("titles run ID does not match the saved merge history".into());
        }
        let saved = Hierarchy::load_merge_history_with_min_notes(
            history_path,
            vector_map_path,
            notes_path,
            min_notes,
        )?;
        let mut titles = BTreeMap::new();
        for title in spec.titles {
            if title.label.trim().is_empty() || titles.insert(title.group_id, title).is_some() {
                return Err("titles must be nonempty and group IDs must be unique".into());
            }
        }
        let expected = saved.groups.keys().copied().collect::<BTreeSet<_>>();
        let actual = titles.keys().copied().collect::<BTreeSet<_>>();
        if expected != actual {
            return Err(format!(
                "titles must exactly cover displayed groups; missing {:?}; extra {:?}",
                expected.difference(&actual).collect::<Vec<_>>(),
                actual.difference(&expected).collect::<Vec<_>>()
            )
            .into());
        }

        let vectors: VectorMap = serde_json::from_slice(&fs::read(vector_map_path)?)?;
        let mut short_ids = BTreeMap::new();
        let mut source_ids = BTreeMap::new();
        for reference in vectors.vectors {
            if reference.note_id.trim().is_empty() || reference.note_short_id.trim().is_empty() {
                return Err("vector map requires nonempty source note IDs".into());
            }
            if short_ids
                .insert(reference.note_id.clone(), reference.note_short_id.clone())
                .is_some_and(|previous| previous != reference.note_short_id)
                || source_ids
                    .insert(reference.note_short_id, reference.note_id.clone())
                    .is_some_and(|previous| previous != reference.note_id)
            {
                return Err("vector map has conflicting source note short IDs".into());
            }
        }
        let mut notes = BTreeMap::new();
        for mask in saved.vectors.values().flatten() {
            let short = short_ids
                .get(&mask.note_id)
                .ok_or("source note short ID is missing")?;
            notes.entry(short.clone()).or_insert_with(|| ManualNote {
                note_id: mask.note_id.clone(),
                note_short_id: short.clone(),
                content: mask.text.clone(),
            });
        }
        let nodes = saved
            .groups
            .values()
            .map(|group| {
                let title = titles.remove(&group.id).expect("validated title coverage");
                let id = group.id.to_string();
                let note_ids = group
                    .vectors
                    .iter()
                    .flat_map(|point| &saved.vectors[point])
                    .map(|mask| short_ids[&mask.note_id].clone())
                    .collect::<BTreeSet<_>>()
                    .into_iter()
                    .collect();
                (
                    id.clone(),
                    ManualCategory {
                        node_id: id,
                        label: title.label,
                        children: group.children.iter().map(usize::to_string).collect(),
                        note_ids,
                        analysis: title.analysis,
                    },
                )
            })
            .collect();
        Ok(Self {
            hierarchy: ManualNoteHierarchy {
                hierarchy_id: spec.run_id.clone(),
                root_node_id: saved.root.to_string(),
                nodes,
                notes,
            },
            run_id: spec.run_id,
            min_notes,
            start_group_id: saved.root,
        })
    }

    /// Set the initial position while preserving the complete hierarchy and root.
    pub fn start_at(&mut self, group_id: usize) -> Result<(), Box<dyn Error>> {
        let id = group_id.to_string();
        if !self.hierarchy.nodes.contains_key(&id) {
            return Err(format!(
                "group {group_id} is not displayed at minimum {} notes",
                self.min_notes
            )
            .into());
        }
        self.start_group_id = group_id;
        Ok(())
    }

    pub fn check_summary(&self) -> String {
        let mut lines = vec![
            format!(
                "{} · provisional titles · minimum {} notes · read-only",
                self.run_id, self.min_notes
            ),
            format!(
                "{} categories · {} notes",
                self.hierarchy.nodes.len(),
                self.hierarchy.notes.len()
            ),
            format!("Start: {}/{}", self.run_id, self.start_group_id),
        ];
        for node in self.hierarchy.nodes.values() {
            lines.push(format!(
                "{}/{} · {} · {} notes",
                self.run_id,
                node.node_id,
                node.label,
                self.hierarchy.note_ids(&node.node_id).len()
            ));
        }
        lines.join("\n")
    }
}
