//! Load a manually constructed hierarchy over the accepted SSE fine segments.

use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::path::{Path, PathBuf};

use serde::Deserialize;
use sha2::{Digest, Sha256};

use crate::snapshot::{Error, Result};
use crate::subject_navigation::{NavigationHierarchy, NavigationNode, NavigationNote};

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct ManualHierarchySpec {
    schema_version: u32,
    hierarchy_id: String,
    construction: Construction,
    inputs: Inputs,
    root_node_id: String,
    nodes: Vec<ManualNode>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct Construction {
    method: String,
    automated: bool,
    claim: String,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct Inputs {
    fine_region_hierarchy_analysis_sha256: String,
    fine_region_partition_analysis_sha256: String,
}

#[derive(Debug, Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
enum ManualNode {
    Internal {
        node_id: String,
        label: String,
        children: Vec<String>,
    },
    FineSegment {
        node_id: String,
        label: String,
        fine_segment_id: String,
    },
}

#[derive(Debug, Deserialize)]
struct HierarchyAnalysis {
    partition_analysis_sha256: String,
    hierarchy: SourceHierarchy,
}

#[derive(Debug, Deserialize)]
struct SourceHierarchy {
    fine_segments: Vec<FineSegment>,
}

#[derive(Debug, Deserialize)]
struct FineSegment {
    segment_id: String,
    members: Vec<usize>,
}

#[derive(Debug, Deserialize)]
struct PartitionAnalysis {
    vectors: Vec<SourceVector>,
}

#[derive(Debug, Deserialize)]
struct SourceVector {
    ordinal: usize,
    note_id: String,
    source_note: String,
}

pub fn load_sse_subject_hierarchy(
    spec_path: impl AsRef<Path>,
    hierarchy_analysis_path: impl AsRef<Path>,
    partition_analysis_path: impl AsRef<Path>,
) -> Result<NavigationHierarchy> {
    let spec_path = spec_path.as_ref();
    let hierarchy_analysis_path = hierarchy_analysis_path.as_ref();
    let partition_analysis_path = partition_analysis_path.as_ref();

    let spec_bytes = read(spec_path)?;
    let hierarchy_bytes = read(hierarchy_analysis_path)?;
    let partition_bytes = read(partition_analysis_path)?;
    let spec: ManualHierarchySpec = decode(spec_path, &spec_bytes)?;
    let source_hierarchy: HierarchyAnalysis = decode(hierarchy_analysis_path, &hierarchy_bytes)?;
    let partition: PartitionAnalysis = decode(partition_analysis_path, &partition_bytes)?;

    if spec.schema_version != 1
        || spec.hierarchy_id.trim().is_empty()
        || spec.construction.method != "manual_best_case_from_grounded_masks"
        || spec.construction.automated
        || spec.construction.claim.trim().is_empty()
    {
        return invalid("manual SSE hierarchy identity or construction metadata is invalid");
    }
    verify_hash(
        hierarchy_analysis_path,
        &hierarchy_bytes,
        &spec.inputs.fine_region_hierarchy_analysis_sha256,
    )?;
    verify_hash(
        partition_analysis_path,
        &partition_bytes,
        &spec.inputs.fine_region_partition_analysis_sha256,
    )?;
    let partition_sha256 = sha256(&partition_bytes);
    if source_hierarchy.partition_analysis_sha256 != partition_sha256 {
        return invalid(format!(
            "hierarchy analysis embedded partition SHA-256 {} does not match {}",
            source_hierarchy.partition_analysis_sha256, partition_sha256
        ));
    }

    for (index, vector) in partition.vectors.iter().enumerate() {
        if vector.ordinal != index
            || vector.note_id.trim().is_empty()
            || vector.source_note.trim().is_empty()
        {
            return invalid(format!(
                "partition vector at index {index} has invalid source metadata"
            ));
        }
    }

    let fine_segments = source_hierarchy
        .hierarchy
        .fine_segments
        .iter()
        .map(|segment| (segment.segment_id.as_str(), segment))
        .collect::<BTreeMap<_, _>>();
    if fine_segments.len() != source_hierarchy.hierarchy.fine_segments.len() {
        return invalid("fine-region source repeats a segment ID");
    }

    let mut notes = BTreeMap::<String, String>::new();
    let mut selected_segments = BTreeSet::new();
    let mut selected_ordinals = BTreeSet::new();
    let mut nodes = Vec::with_capacity(spec.nodes.len());
    for node in spec.nodes {
        match node {
            ManualNode::Internal {
                node_id,
                label,
                children,
            } => nodes.push(NavigationNode {
                node_id,
                label,
                children,
                note_ids: Vec::new(),
            }),
            ManualNode::FineSegment {
                node_id,
                label,
                fine_segment_id,
            } => {
                if !selected_segments.insert(fine_segment_id.clone()) {
                    return invalid(format!(
                        "manual hierarchy repeats fine segment {fine_segment_id}"
                    ));
                }
                let segment = fine_segments.get(fine_segment_id.as_str()).ok_or_else(|| {
                    Error::ExperimentState(format!(
                        "manual hierarchy names missing fine segment {fine_segment_id}"
                    ))
                })?;
                let mut leaf_note_ids = Vec::new();
                let mut leaf_seen = BTreeSet::new();
                for &ordinal in &segment.members {
                    if !selected_ordinals.insert(ordinal) {
                        return invalid(format!(
                            "fine-region source assigns vector {ordinal} to more than one selected segment"
                        ));
                    }
                    let vector = partition.vectors.get(ordinal).ok_or_else(|| {
                        Error::ExperimentState(format!(
                            "fine segment {fine_segment_id} names missing vector {ordinal}"
                        ))
                    })?;
                    match notes.get(&vector.note_id) {
                        Some(content) if content != &vector.source_note => {
                            return invalid(format!(
                                "note {} has conflicting source text",
                                vector.note_id
                            ));
                        }
                        Some(_) => {}
                        None => {
                            notes.insert(vector.note_id.clone(), vector.source_note.clone());
                        }
                    }
                    if leaf_seen.insert(vector.note_id.as_str()) {
                        leaf_note_ids.push(vector.note_id.clone());
                    }
                }
                nodes.push(NavigationNode {
                    node_id,
                    label,
                    children: Vec::new(),
                    note_ids: leaf_note_ids,
                });
            }
        }
    }

    let expected_segments = fine_segments
        .keys()
        .map(|segment| (*segment).to_owned())
        .collect::<BTreeSet<_>>();
    if selected_segments != expected_segments {
        return invalid("manual hierarchy must use every accepted fine segment exactly once");
    }

    let hierarchy = NavigationHierarchy {
        root_node_id: spec.root_node_id,
        notes: notes
            .into_iter()
            .map(|(note_id, content)| NavigationNote { note_id, content })
            .collect(),
        nodes,
    };
    hierarchy.validate()?;
    validate_discovery_transitions(&hierarchy)?;
    Ok(hierarchy)
}

fn validate_discovery_transitions(hierarchy: &NavigationHierarchy) -> Result<()> {
    let mut memo = BTreeMap::<String, BTreeSet<String>>::new();
    fn descendant_notes(
        hierarchy: &NavigationHierarchy,
        node_id: &str,
        memo: &mut BTreeMap<String, BTreeSet<String>>,
    ) -> Result<BTreeSet<String>> {
        if let Some(notes) = memo.get(node_id) {
            return Ok(notes.clone());
        }
        let node = hierarchy.node(node_id).ok_or_else(|| {
            Error::ExperimentState(format!("navigation node {node_id} is missing"))
        })?;
        let notes = if node.is_leaf() {
            node.note_ids.iter().cloned().collect()
        } else {
            let mut notes = BTreeSet::new();
            for child in &node.children {
                notes.extend(descendant_notes(hierarchy, child, memo)?);
            }
            notes
        };
        memo.insert(node_id.to_owned(), notes.clone());
        Ok(notes)
    }

    for node in hierarchy.nodes.iter().filter(|node| !node.is_leaf()) {
        let parent_notes = descendant_notes(hierarchy, &node.node_id, &mut memo)?;
        let mut sibling_sets = BTreeMap::<Vec<String>, &str>::new();
        for child in &node.children {
            let child_notes = descendant_notes(hierarchy, child, &mut memo)?;
            if child_notes == parent_notes {
                return invalid(format!(
                    "navigation edge {} -> {child} does not narrow the note set",
                    node.node_id
                ));
            }
            let signature = child_notes.into_iter().collect::<Vec<_>>();
            if let Some(previous) = sibling_sets.insert(signature, child.as_str()) {
                return invalid(format!(
                    "siblings {previous} and {child} expose the same note set"
                ));
            }
        }
    }
    Ok(())
}

fn read(path: &Path) -> Result<Vec<u8>> {
    fs::read(path).map_err(|source| Error::Io {
        operation: "read",
        path: path.to_path_buf(),
        source,
    })
}

fn decode<T: for<'de> Deserialize<'de>>(path: &Path, bytes: &[u8]) -> Result<T> {
    serde_json::from_slice(bytes).map_err(|source| Error::Manifest {
        operation: "decode",
        path: PathBuf::from(path),
        source,
    })
}

fn verify_hash(path: &Path, bytes: &[u8], expected: &str) -> Result<()> {
    let actual = sha256(bytes);
    if actual != expected {
        return invalid(format!(
            "source artifact {} changed: expected SHA-256 {expected}, found {actual}",
            path.display()
        ));
    }
    Ok(())
}

fn sha256(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}

fn invalid<T>(message: impl Into<String>) -> Result<T> {
    Err(Error::ExperimentState(message.into()))
}
