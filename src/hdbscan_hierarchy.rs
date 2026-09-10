//! Read-only reconstruction of saved HDBSCAN trees and scored merge histories.

use std::collections::{BTreeMap, BTreeSet};
use std::error::Error;
use std::fs::File;
use std::io::{BufReader, Read};
use std::path::Path;

use serde::{Deserialize, de::DeserializeOwned};
use sha2::{Digest, Sha256};

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
    /// Load a note-navigation comparison from the saved binary merge tree.
    ///
    /// Retain a merge only when it contains at least two distinct source notes
    /// and its complete note set differs from its immediate raw parent's set.
    /// Exact-vector aliases all contribute notes. The root is always retained
    /// as a container, including for a one-note corpus; it is not evidence of
    /// a cross-note group in that case. Input points never become group nodes.
    ///
    /// IDs are the original single-linkage merge IDs, not condensed-tree IDs.
    /// Removing a group only promotes its retained descendants and transfers
    /// its direct points to the nearest retained ancestor. No distances are
    /// recomputed, no equal-distance transitions are additionally removed, and
    /// every retained group's complete membership and source masks stay intact.
    pub fn load_note_navigation(
        response_path: &Path,
        vector_map_path: &Path,
        notes_path: &Path,
    ) -> Result<Self, Box<dyn Error>> {
        Self::load_note_navigation_with_min_notes(response_path, vector_map_path, notes_path, 2)
    }

    /// Use a larger minimum distinct-note count for displayed group choices.
    /// Smaller groups' points remain at the nearest displayed ancestor. The
    /// root is always kept, even when the entire corpus is below the minimum.
    pub fn load_note_navigation_with_min_notes(
        response_path: &Path,
        vector_map_path: &Path,
        notes_path: &Path,
        min_notes: usize,
    ) -> Result<Self, Box<dyn Error>> {
        let response: SavedResponse<SavedLinkageAlgorithm> = read_json(response_path)?;
        let SavedResult {
            algorithm_result,
            alias_groups,
            canonical_unique_ids,
        } = response.artifact.result;
        let SavedLinkageAlgorithm {
            vector_count,
            single_linkage_tree,
        } = algorithm_result;
        let mut previous_distance = 0.0;
        for row in &single_linkage_tree {
            let distance = row.score.mutual_reachability_distance;
            if !distance.is_finite() || distance < previous_distance {
                return Err(
                    "single-linkage distances must be finite, nonnegative, and ordered".into(),
                );
            }
            previous_distance = distance;
        }
        Self::project_note_navigation(
            vector_count,
            &single_linkage_tree,
            alias_groups,
            canonical_unique_ids,
            vector_map_path,
            notes_path,
            min_notes,
        )
    }

    /// Apply the same distinct-note projection to a saved merge history.
    ///
    /// Genuine merge scores may decrease. They must be finite and nonnegative,
    /// but are never reordered or replaced with single-linkage distances.
    pub fn load_merge_history(
        history_path: &Path,
        vector_map_path: &Path,
        notes_path: &Path,
    ) -> Result<Self, Box<dyn Error>> {
        Self::load_merge_history_with_min_notes(history_path, vector_map_path, notes_path, 2)
    }

    /// Apply the optional display minimum without changing saved merges.
    pub fn load_merge_history_with_min_notes(
        history_path: &Path,
        vector_map_path: &Path,
        notes_path: &Path,
        min_notes: usize,
    ) -> Result<Self, Box<dyn Error>> {
        let history: SavedMergeHistory = read_json(history_path)?;
        for row in &history.merges {
            if !row.score.merge_score.is_finite() || row.score.merge_score < 0.0 {
                return Err("merge scores must be finite and nonnegative".into());
            }
        }
        Self::project_note_navigation(
            history.vector_count,
            &history.merges,
            history.alias_groups,
            history.canonical_unique_ids,
            vector_map_path,
            notes_path,
            min_notes,
        )
    }

    fn project_note_navigation<Score>(
        vector_count: usize,
        merges: &[SavedMergeNode<Score>],
        alias_groups: Vec<Vec<String>>,
        canonical_unique_ids: Vec<String>,
        vector_map_path: &Path,
        notes_path: &Path,
        min_notes: usize,
    ) -> Result<Self, Box<dyn Error>> {
        if min_notes < 2 {
            return Err("minimum group size must be at least 2 distinct notes".into());
        }
        if vector_count < 2 {
            return Err("saved merge history requires at least two points".into());
        }
        if merges.len() != vector_count - 1 {
            return Err("merge history must contain vector_count - 1 merges".into());
        }
        if alias_groups.len() != vector_count {
            return Err("alias group count does not match vector_count".into());
        }
        if canonical_unique_ids.len() != vector_count {
            return Err("canonical ID count does not match vector_count".into());
        }
        let total_nodes = vector_count
            .checked_add(vector_count - 1)
            .ok_or("merge-history node count overflows")?;
        let root = total_nodes - 1;
        let vectors = load_vectors(
            alias_groups,
            canonical_unique_ids,
            vector_map_path,
            notes_path,
        )?;

        let mut parents = vec![None; total_nodes];
        let mut point_counts = vec![0usize; total_nodes];
        let mut note_counts = vec![0usize; total_nodes];
        let mut pending_notes = BTreeMap::new();
        for (&point, aliases) in &vectors {
            let notes = aliases
                .iter()
                .map(|mask| mask.note_id.as_str())
                .collect::<BTreeSet<_>>();
            point_counts[point] = 1;
            note_counts[point] = notes.len();
            pending_notes.insert(point, notes);
        }
        let mut retained = BTreeSet::from([root]);
        for (offset, row) in merges.iter().enumerate() {
            if row.id != vector_count + offset {
                return Err("merge IDs must be consecutive and ordered".into());
            }
            if row.left == row.right || row.left >= row.id || row.right >= row.id {
                return Err(format!("merge {} must join distinct earlier nodes", row.id).into());
            }
            for child in [row.left, row.right] {
                if parents[child].replace(row.id).is_some() {
                    return Err(format!("raw node {child} has more than one parent").into());
                }
            }
            let count = point_counts[row.left] + point_counts[row.right];
            if row.size != count {
                return Err(format!(
                    "merge {} size {} does not match {count} descendant points",
                    row.id, row.size
                )
                .into());
            }
            point_counts[row.id] = count;

            // A node is evaluated against its immediate raw parent while both
            // complete note sets are available. Child sets are then consumed,
            // avoiding stored per-ancestor copies of all point memberships.
            let left_notes = pending_notes.remove(&row.left).expect("validated child");
            let right_notes = pending_notes.remove(&row.right).expect("validated child");
            let notes = left_notes
                .union(&right_notes)
                .copied()
                .collect::<BTreeSet<_>>();
            for (child, child_notes) in [(row.left, &left_notes), (row.right, &right_notes)] {
                if child >= vector_count && child_notes.len() >= min_notes && *child_notes != notes
                {
                    retained.insert(child);
                }
            }
            note_counts[row.id] = notes.len();
            pending_notes.insert(row.id, notes);
        }
        if point_counts[root] != vector_count
            || parents[..root].iter().any(Option::is_none)
            || parents[root].is_some()
        {
            return Err("merge-history root must contain every point exactly once".into());
        }

        // Parent IDs are larger than child IDs. Descending order therefore
        // resolves each node's nearest retained ancestor without recursion.
        let mut owners = vec![root; total_nodes];
        for id in (0..root).rev() {
            owners[id] = if retained.contains(&id) {
                id
            } else {
                owners[parents[id].expect("validated nonroot parent")]
            };
        }
        let mut groups = retained
            .iter()
            .map(|&id| {
                (
                    id,
                    Group {
                        id,
                        parent: parents[id].map(|parent| owners[parent]),
                        children: Vec::new(),
                        vectors: Vec::new(),
                        note_count: note_counts[id],
                        vector_count: point_counts[id],
                    },
                )
            })
            .collect::<BTreeMap<_, _>>();
        // Promotion preserves raw left-to-right order, rather than introducing
        // an ordering by merge ID. Direct points keep their canonical order.
        let mut pending = vec![root];
        while let Some(id) = pending.pop() {
            if id < vector_count {
                continue;
            }
            if let Some(parent) = groups.get(&id).and_then(|group| group.parent) {
                groups
                    .get_mut(&parent)
                    .expect("retained parent")
                    .children
                    .push(id);
            }
            let row = &merges[id - vector_count];
            pending.push(row.right);
            pending.push(row.left);
        }
        for (point, &owner) in owners.iter().take(vector_count).enumerate() {
            groups
                .get_mut(&owner)
                .expect("retained point owner")
                .vectors
                .push(point);
        }
        Ok(Self {
            root,
            groups,
            vectors,
        })
    }

    /// Load a saved display selection after verifying its sources and membership.
    /// The raw tree remains untouched; only existing ancestor edges are shortened.
    pub fn load_selection(
        response_path: &Path,
        vector_map_path: &Path,
        notes_path: &Path,
        selection_path: &Path,
    ) -> Result<Self, Box<dyn Error>> {
        let selection: SavedSelection = read_json(selection_path)?;
        for (name, path, source) in [
            ("response", response_path, &selection.sources.response),
            ("vectors", vector_map_path, &selection.sources.vectors),
            ("notes", notes_path, &selection.sources.notes),
        ] {
            if source.sha256 != file_sha256(path)? {
                return Err(format!("selection source checksum mismatch: {name}").into());
            }
        }
        let mut hierarchy = Self::load(response_path, vector_map_path, notes_path)?;
        let mut records = BTreeMap::new();
        for record in selection.retained_groups {
            let id = record.id;
            if !hierarchy.groups.contains_key(&id) {
                return Err(format!("selection contains unknown group {id}").into());
            }
            if records.insert(id, record).is_some() {
                return Err(format!("selection contains duplicate group {id}").into());
            }
        }
        if !records.contains_key(&hierarchy.root) {
            return Err("selection must retain the root".into());
        }
        let nearest_retained = |mut id: Option<usize>| {
            while let Some(group) = id {
                if records.contains_key(&group) {
                    return Some(group);
                }
                id = hierarchy.groups[&group].parent;
            }
            None
        };
        let mut selected = BTreeMap::new();
        for &id in records.keys() {
            let raw = &hierarchy.groups[&id];
            selected.insert(
                id,
                Group {
                    id,
                    parent: nearest_retained(raw.parent),
                    children: Vec::new(),
                    vectors: Vec::new(),
                    note_count: raw.note_count,
                    vector_count: raw.vector_count,
                },
            );
        }
        // Assign each raw group's direct points to its closest retained ancestor.
        // This preserves the complete point set of every retained group without
        // copying flattened memberships for every ancestor.
        for raw in hierarchy.groups.values() {
            let owner = nearest_retained(Some(raw.id)).expect("root retained");
            selected
                .get_mut(&owner)
                .expect("retained group")
                .vectors
                .extend(&raw.vectors);
        }
        for &id in records.keys() {
            if let Some(parent) = selected[&id].parent {
                selected
                    .get_mut(&parent)
                    .expect("retained parent")
                    .children
                    .push(id);
            }
        }
        for (&id, group) in &mut selected {
            group.vectors.sort_unstable();
            let record = &records[&id];
            let mut direct = record.direct_points.clone();
            direct.sort_unstable();
            if record.raw_parent != hierarchy.groups[&id].parent
                || record.display_parent != group.parent
                || record.display_children != group.children
            {
                return Err(format!("selection ancestry mismatch for group {id}").into());
            }
            if direct != group.vectors {
                return Err(
                    format!("selection direct-point membership mismatch for group {id}").into(),
                );
            }
            if record.distinct_notes != group.note_count
                || record.unique_vectors != group.vector_count
                || record.direct_unique_vectors != group.vectors.len()
            {
                return Err(format!("selection count mismatch for group {id}").into());
            }
        }
        hierarchy.groups = selected;
        Ok(hierarchy)
    }

    pub fn load(
        response_path: &Path,
        vector_map_path: &Path,
        notes_path: &Path,
    ) -> Result<Self, Box<dyn Error>> {
        let response: SavedResponse<SavedAlgorithm> = read_json(response_path)?;
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

fn file_sha256(path: &Path) -> Result<String, Box<dyn Error>> {
    let mut file = File::open(path)?;
    let mut digest = Sha256::new();
    let mut buffer = [0; 65536];
    loop {
        let count = file.read(&mut buffer)?;
        if count == 0 {
            break;
        }
        digest.update(&buffer[..count]);
    }
    Ok(format!("{:x}", digest.finalize()))
}

#[derive(Deserialize)]
struct SavedSelection {
    sources: SelectionSources,
    retained_groups: Vec<SelectedGroup>,
}

#[derive(Deserialize)]
struct SelectionSources {
    response: SelectionSource,
    vectors: SelectionSource,
    notes: SelectionSource,
}

#[derive(Deserialize)]
struct SelectionSource {
    sha256: String,
}

#[derive(Deserialize)]
struct SelectedGroup {
    id: usize,
    raw_parent: Option<usize>,
    display_parent: Option<usize>,
    display_children: Vec<usize>,
    direct_points: Vec<usize>,
    distinct_notes: usize,
    unique_vectors: usize,
    direct_unique_vectors: usize,
}

// These intentionally partial schemas skip saved matrices, labels, selected
// clusters, model output, and provenance without materializing them in memory.
#[derive(Deserialize)]
struct SavedResponse<Algorithm> {
    artifact: SavedArtifact<Algorithm>,
}

#[derive(Deserialize)]
struct SavedArtifact<Algorithm> {
    result: SavedResult<Algorithm>,
}

#[derive(Deserialize)]
struct SavedResult<Algorithm> {
    algorithm_result: Algorithm,
    alias_groups: Vec<Vec<String>>,
    canonical_unique_ids: Vec<String>,
}

#[derive(Deserialize)]
struct SavedAlgorithm {
    vector_count: usize,
    condensed_tree: Vec<SavedEdge>,
}

#[derive(Deserialize)]
struct SavedLinkageAlgorithm {
    vector_count: usize,
    single_linkage_tree: Vec<SavedMergeNode<SavedLinkageDistance>>,
}

#[derive(Deserialize)]
struct SavedMergeHistory {
    vector_count: usize,
    alias_groups: Vec<Vec<String>>,
    canonical_unique_ids: Vec<String>,
    merges: Vec<SavedMergeNode<SavedMergeScore>>,
}

#[derive(Deserialize)]
struct SavedMergeNode<Score> {
    id: usize,
    left: usize,
    right: usize,
    size: usize,
    #[serde(flatten)]
    score: Score,
}

#[derive(Deserialize)]
struct SavedLinkageDistance {
    mutual_reachability_distance: f64,
}

#[derive(Deserialize)]
struct SavedMergeScore {
    merge_score: f64,
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
