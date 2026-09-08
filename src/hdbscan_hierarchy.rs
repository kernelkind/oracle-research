//! Read-only reconstruction of a saved HDBSCAN condensed tree.

use std::collections::{BTreeMap, BTreeSet};
use std::error::Error;
use std::fs::File;
use std::io::BufReader;
use std::path::Path;

use serde::{Deserialize, de::DeserializeOwned};

#[derive(Clone, Debug)]
pub struct Hierarchy {
    pub root: usize,
    pub groups: BTreeMap<usize, Group>,
    pub vectors: BTreeMap<usize, Vec<MaskInstance>>,
}

#[derive(Clone, Debug)]
pub struct Group {
    pub id: usize,
    pub parent: Option<usize>,
    pub children: Vec<usize>,
    /// Points departing directly from this group, excluding its descendants.
    pub vectors: Vec<usize>,
    /// Distinct source notes across direct points, descendants, and all aliases.
    pub note_count: usize,
    /// Canonical points across direct points and descendant groups.
    pub vector_count: usize,
}

#[derive(Clone, Debug)]
pub struct MaskInstance {
    pub id: String,
    pub vector_id: String,
    pub note_id: String,
    pub text: String,
    pub byte_spans: Vec<(usize, usize)>,
    pub fragments: Vec<String>,
}

impl Hierarchy {
    pub fn load(
        response_path: &Path,
        vector_map_path: &Path,
        notes_path: &Path,
    ) -> Result<Self, Box<dyn Error>> {
        let response: SavedResponse = read_json(response_path)?;
        let SavedResult {
            algorithm_result,
            alias_groups,
            canonical_unique_ids,
        } = response.artifact.result;
        let SavedAlgorithm {
            vector_count,
            condensed_tree,
        } = algorithm_result;
        if vector_count == 0 {
            return Err("saved condensed tree has no points".into());
        }
        if alias_groups.len() != vector_count {
            return Err("alias group count does not match vector_count".into());
        }
        if canonical_unique_ids.len() != vector_count {
            return Err("canonical ID count does not match vector_count".into());
        }
        let vectors = load_vectors(
            alias_groups,
            canonical_unique_ids,
            vector_map_path,
            notes_path,
        )?;

        let root = vector_count;
        let mut groups = BTreeMap::from([(root, Group::new(root))]);
        let mut parents = BTreeMap::new();
        let mut point_count = 0;
        for edge in &condensed_tree {
            if edge.parent < vector_count {
                return Err(format!("point {} cannot be a group parent", edge.parent).into());
            }
            if edge.child == root {
                return Err(format!("root group {root} cannot have a parent").into());
            }
            if parents.insert(edge.child, edge.parent).is_some() {
                return Err(format!("child {} has more than one parent edge", edge.child).into());
            }
            if edge.child_size == 0 || !edge.lambda.is_finite() || edge.lambda < 0.0 {
                return Err(
                    format!("invalid child_size or lambda for child {}", edge.child).into(),
                );
            }
            let parent = groups
                .entry(edge.parent)
                .or_insert_with(|| Group::new(edge.parent));
            // A one-point group remains a group: IDs, not child_size, distinguish it.
            if edge.child < vector_count {
                if edge.child_size != 1 {
                    return Err(format!("point {} must have child_size 1", edge.child).into());
                }
                parent.vectors.push(edge.child);
                point_count += 1;
            } else {
                parent.children.push(edge.child);
                groups
                    .entry(edge.child)
                    .or_insert_with(|| Group::new(edge.child))
                    .parent = Some(edge.parent);
            }
        }
        if point_count != vector_count {
            return Err(format!(
                "each point must appear exactly once: found {point_count} of {vector_count}"
            )
            .into());
        }
        for group in groups.values() {
            if group.id != root && group.parent.is_none() {
                return Err(
                    format!("group {} has no parent; only root {root} may", group.id).into(),
                );
            }
        }

        // Iterative traversal avoids consuming the call stack on deeply nested trees.
        let mut order = vec![root];
        let mut visited = BTreeSet::from([root]);
        let mut next = 0;
        while next < order.len() {
            for &child in &groups[&order[next]].children {
                if !visited.insert(child) {
                    return Err(format!("cycle at group {child}").into());
                }
                order.push(child);
            }
            next += 1;
        }
        if order.len() != groups.len() {
            return Err("condensed tree contains a cycle or an unreachable group".into());
        }

        // Consume children's temporary note sets as each parent is counted. No
        // flattened point memberships or per-ancestor copies are retained.
        let mut descendant_notes: BTreeMap<usize, BTreeSet<&str>> = BTreeMap::new();
        for id in order.into_iter().rev() {
            let group = &groups[&id];
            let mut count = group.vectors.len();
            let mut note_ids = BTreeSet::new();
            for point in &group.vectors {
                note_ids.extend(vectors[point].iter().map(|mask| mask.note_id.as_str()));
            }
            for child in &group.children {
                count += groups[child].vector_count;
                note_ids.extend(descendant_notes.remove(child).expect("child visited first"));
            }
            let group = groups.get_mut(&id).expect("visited group");
            group.vector_count = count;
            group.note_count = note_ids.len();
            descendant_notes.insert(id, note_ids);
        }
        for edge in &condensed_tree {
            if edge.child >= vector_count && groups[&edge.child].vector_count != edge.child_size {
                return Err(format!(
                    "group {} child_size {} does not match {} descendant points",
                    edge.child, edge.child_size, groups[&edge.child].vector_count
                )
                .into());
            }
        }
        Ok(Self {
            root,
            groups,
            vectors,
        })
    }
}

impl Group {
    fn new(id: usize) -> Self {
        Self {
            id,
            parent: None,
            children: Vec::new(),
            vectors: Vec::new(),
            note_count: 0,
            vector_count: 0,
        }
    }
}

fn load_vectors(
    alias_groups: Vec<Vec<String>>,
    canonical_unique_ids: Vec<String>,
    vector_map_path: &Path,
    notes_path: &Path,
) -> Result<BTreeMap<usize, Vec<MaskInstance>>, Box<dyn Error>> {
    let saved_notes: SavedNotes = read_json(notes_path)?;
    let mut notes = BTreeMap::new();
    for note in saved_notes.notes {
        if notes.contains_key(&note.note_id) {
            return Err(format!("duplicate note ID {}", note.note_id).into());
        }
        notes.insert(note.note_id, note.text);
    }
    let saved_vectors: SavedVectors = read_json(vector_map_path)?;
    let mut originals = BTreeMap::new();
    let mut short_ids = BTreeSet::new();
    for vector in saved_vectors.vectors {
        if originals.contains_key(&vector.vector_id) {
            return Err(format!("duplicate vector ID {}", vector.vector_id).into());
        }
        if !short_ids.insert(vector.short_id.clone()) {
            return Err(format!("duplicate short_id {}", vector.short_id).into());
        }
        let text = notes.get(&vector.note_id).ok_or_else(|| {
            format!(
                "missing note {} for vector {}",
                vector.note_id, vector.vector_id
            )
        })?;
        if vector.byte_spans.len() != vector.fragments.len() {
            return Err(
                format!("fragment/byte span count mismatch for {}", vector.vector_id).into(),
            );
        }
        if vector.byte_spans.is_empty() {
            return Err(format!("no byte spans for vector {}", vector.vector_id).into());
        }
        let mut previous_end = 0;
        for (&(start, end), fragment) in vector.byte_spans.iter().zip(&vector.fragments) {
            let source = text
                .get(start..end)
                .filter(|_| start >= previous_end && start < end)
                .ok_or_else(|| {
                    format!(
                        "invalid, overlapping, or out-of-order UTF-8 byte span {start}..{end} for vector {}",
                        vector.vector_id
                    )
                })?;
            if source != fragment {
                return Err(format!(
                    "fragment does not match note byte span {start}..{end} for vector {}",
                    vector.vector_id
                )
                .into());
            }
            previous_end = end;
        }
        originals.insert(
            vector.vector_id.clone(),
            MaskInstance {
                id: vector.short_id,
                vector_id: vector.vector_id,
                note_id: vector.note_id,
                text: text.clone(),
                byte_spans: vector.byte_spans,
                fragments: vector.fragments,
            },
        );
    }

    let mut vectors = BTreeMap::new();
    let mut seen_aliases = BTreeSet::new();
    let mut seen_canonical = BTreeSet::new();
    for (ordinal, (aliases, canonical)) in alias_groups
        .into_iter()
        .zip(canonical_unique_ids)
        .enumerate()
    {
        if aliases.is_empty() {
            return Err(format!("empty alias group for point {ordinal}").into());
        }
        if aliases.first() != Some(&canonical) || !seen_canonical.insert(canonical) {
            return Err(format!("invalid or duplicate canonical ID for point {ordinal}").into());
        }
        let mut instances = Vec::with_capacity(aliases.len());
        for alias in aliases {
            if !seen_aliases.insert(alias.clone()) {
                return Err(format!("duplicate alias {alias}").into());
            }
            instances.push(
                originals
                    .remove(&alias)
                    .ok_or_else(|| format!("missing vector for alias {alias}"))?,
            );
        }
        vectors.insert(ordinal, instances);
    }
    if let Some(id) = originals.keys().next() {
        return Err(format!("unmapped vector {id} is absent from alias groups").into());
    }
    Ok(vectors)
}

fn read_json<T: DeserializeOwned>(path: &Path) -> Result<T, Box<dyn Error>> {
    let file = File::open(path).map_err(|error| format!("{}: {error}", path.display()))?;
    serde_json::from_reader(BufReader::new(file))
        .map_err(|error| format!("{}: {error}", path.display()).into())
}

// These intentionally partial schemas skip saved matrices, labels, selected
// clusters, model output, and provenance without materializing them in memory.
#[derive(Deserialize)]
struct SavedResponse {
    artifact: SavedArtifact,
}

#[derive(Deserialize)]
struct SavedArtifact {
    result: SavedResult,
}

#[derive(Deserialize)]
struct SavedResult {
    algorithm_result: SavedAlgorithm,
    alias_groups: Vec<Vec<String>>,
    canonical_unique_ids: Vec<String>,
}

#[derive(Deserialize)]
struct SavedAlgorithm {
    vector_count: usize,
    condensed_tree: Vec<SavedEdge>,
}

#[derive(Deserialize)]
struct SavedEdge {
    parent: usize,
    child: usize,
    lambda: f64,
    child_size: usize,
}

#[derive(Deserialize)]
struct SavedVectors {
    vectors: Vec<SavedVector>,
}

#[derive(Deserialize)]
struct SavedVector {
    vector_id: String,
    short_id: String,
    note_id: String,
    byte_spans: Vec<(usize, usize)>,
    fragments: Vec<String>,
}

#[derive(Deserialize)]
struct SavedNotes {
    notes: Vec<SavedNote>,
}

#[derive(Deserialize)]
struct SavedNote {
    note_id: String,
    text: String,
}
