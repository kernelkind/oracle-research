//! Exact, dense HDBSCAN* over normalized semantic vectors.
//!
//! This module implements the algorithm described by Campello, Moulavi, and
//! Sander, including the condensed hierarchy and excess-of-mass extraction:
//! <https://doi.org/10.1007/978-3-642-37456-2_14>. GLOSH scores follow the
//! expanded formulation of Campello, Moulavi, Zimek, and Sander:
//! <https://doi.org/10.1145/2733381>. Flat-cluster membership strengths and
//! leaf selection are explicitly identified below as reference-implementation
//! extensions rather than paper-defined HDBSCAN* outputs:
//! <https://github.com/scikit-learn-contrib/hdbscan>.
//!
//! Inputs are limited to [`CosineMatrix`], numeric configuration, and optional
//! caller-supplied core distances and excluded ordinal pairs. Cosines become
//! angular distance (`acos(cosine)`), which is a metric for unit vectors. No
//! note text, labels, author information, or semantic rules enter this numeric
//! implementation.
//!
//! Following Definition 3.1 of Campello et al. (2015),
//! [`hdbscan`] uses [`HdbscanConfig::min_samples`] counting the point itself.
//! A value of two therefore makes a point's core distance the distance to its
//! nearest other point. This is explicit because some software APIs use a
//! different convention. [`hdbscan_with_core_distances`] instead uses supplied
//! numeric core distances without changing the downstream algorithm.
//!
//! Input ordinals are part of the deterministic contract. They break exact
//! geometric ties in the MST and public ordering, so callers that require
//! reproducibility must provide the same canonically ordered vectors.

use std::collections::{BTreeMap, BTreeSet, VecDeque};

use serde::{Deserialize, Serialize};
use thiserror::Error;

use crate::fine_region_partition::CosineMatrix;

pub type Result<T> = std::result::Result<T, HdbscanError>;

#[derive(Clone, Debug, Error, PartialEq)]
pub enum HdbscanError {
    #[error("HDBSCAN* invariant failed: {0}")]
    Invariant(String),
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ClusterSelectionMethod {
    /// Select the non-overlapping set of clusters with maximum total
    /// stability (the paper's excess-of-mass objective).
    ExcessOfMass,
    /// Select every leaf of the condensed cluster tree, matching the optional
    /// `leaf` policy exposed by the official reference implementation. This is
    /// not the paper's excess-of-mass extraction.
    Leaf,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct HdbscanConfig {
    /// Neighborhood size `mpts`, including the point itself. This must be
    /// between one and the number of vectors.
    pub min_samples: usize,
    /// Smallest branch retained while condensing the single-linkage tree.
    pub min_cluster_size: usize,
    pub selection_method: ClusterSelectionMethod,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct MinimumSpanningTreeEdge {
    pub left: usize,
    pub right: usize,
    pub mutual_reachability_distance: f64,
}

/// One binary merge in the ordinary `n - 1`-edge mutual-reachability MST
/// diagnostic tree.
///
/// Leaves have IDs `0..vector_count`. Merge IDs are allocated consecutively
/// from `vector_count`, so the final row is the root. Equal-distance edges
/// necessarily receive a deterministic binary order here; condensation
/// coalesces each equal-distance tier before applying HDBSCAN* semantics.
#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SingleLinkageNode {
    pub id: usize,
    pub left: usize,
    pub right: usize,
    pub mutual_reachability_distance: f64,
    pub size: usize,
}

/// One edge in the HDBSCAN* condensed tree.
///
/// IDs below `vector_count` are input vectors and always have `child_size =
/// 1`; IDs at or above `vector_count` are condensed clusters. `lambda` is
/// reciprocal mutual-reachability distance at which `child` leaves `parent`.
#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CondensedTreeEdge {
    pub parent: usize,
    pub child: usize,
    pub lambda: f64,
    pub child_size: usize,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct HdbscanCluster {
    /// Condensed-tree cluster ID, not a user-facing ordinal.
    pub id: usize,
    pub members: Vec<usize>,
    /// Paper-defined cluster stability before EOM compares it with descendants.
    pub stability: f64,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct HdbscanResult {
    pub config: HdbscanConfig,
    pub core_distances: Vec<f64>,
    pub minimum_spanning_tree: Vec<MinimumSpanningTreeEdge>,
    pub single_linkage_tree: Vec<SingleLinkageNode>,
    pub condensed_tree: Vec<CondensedTreeEdge>,
    pub clusters: Vec<HdbscanCluster>,
    /// For each input vector, the ordinal in `clusters`, or `None` for noise.
    pub labels: Vec<Option<usize>>,
    pub noise: Vec<usize>,
    /// Flat-cluster membership strength relative to the selected cluster's
    /// maximum lambda, following the official reference implementation. This
    /// is an extension to the paper-defined flat extraction. Noise has
    /// strength zero.
    pub membership_strengths: Vec<f64>,
    /// GLOSH score for every vector; zero is least outlying and one most.
    pub outlier_scores: Vec<f64>,
    vector_count: usize,
    mutual_reachability_distances: Vec<f64>,
}

impl HdbscanResult {
    pub fn mutual_reachability(&self, left: usize, right: usize) -> Result<f64> {
        if left >= self.vector_count || right >= self.vector_count {
            return Err(invalid("mutual-reachability index is out of bounds"));
        }
        Ok(self.mutual_reachability_distances[left * self.vector_count + right])
    }
}

/// Runs exact dense HDBSCAN* over angular distances.
///
/// The implementation intentionally uses `O(n^2)` distance storage and an
/// exact `O(n^2)` Prim MST. That is simple and auditable for the intended
/// 500--1,000-vector pilot, and avoids changing results through approximate
/// nearest-neighbor search.
///
/// The all-data root is not eligible for EOM or leaf selection. This is the
/// conventional HDBSCAN* behavior: if no proper condensed branch survives,
/// every vector is reported as noise rather than manufacturing one cluster.
///
/// Algorithm 1 in Campello et al. constructs an extended MST containing
/// self-loops so that singleton core-distance transitions appear in the full
/// hierarchy. This API deliberately requires `min_cluster_size >= 2`, so
/// singleton transitions cannot survive condensation. It therefore stores the
/// ordinary `n - 1` MST and exposes its binary linkage only as a diagnostic;
/// equal tiers are coalesced while building the condensed tree.
///
/// Distinct input ordinals must also have nonzero angular distance. Exact
/// duplicate directions are rejected so the condensed hierarchy never needs
/// an invented convention for infinite lambda; deduplication belongs before
/// this vector-space algorithm.
pub fn hdbscan(cosines: &CosineMatrix, config: HdbscanConfig) -> Result<HdbscanResult> {
    validate(cosines.count(), config)?;

    let vector_count = cosines.count();
    let angular_distances = angular_distances(cosines)?;
    let core_distances = core_distances(&angular_distances, vector_count, config.min_samples);
    hdbscan_from_distances(&angular_distances, core_distances, config, &[])
}

/// Runs the same exact dense HDBSCAN* calculation with caller-supplied cores.
///
/// Supply one finite, nonnegative angular core distance per input ordinal.
/// Zero is allowed, including when upstream deduplication has combined exact
/// aliases from multiple source notes. Distinct input ordinals must still
/// have nonzero angular distance, as required by [`hdbscan`].
///
/// `config.min_samples` is validated and retained in the result, but does not
/// recompute or alter the supplied cores. All pairwise angular distances,
/// mutual-reachability edges, MST construction, condensation, selection, and
/// scores use the same implementation as [`hdbscan`].
pub fn hdbscan_with_core_distances(
    cosines: &CosineMatrix,
    config: HdbscanConfig,
    core_distances: &[f64],
) -> Result<HdbscanResult> {
    hdbscan_with_core_distances_and_excluded_edges(cosines, config, core_distances, &[])
}

/// Runs the supplied-core calculation after excluding numeric ordinal pairs
/// from the graph used to construct a new MST. Both pair orientations exclude
/// the same undirected edge. Self-pairs and out-of-bounds ordinals are rejected.
///
/// Angular and mutual-reachability distances stay finite and unchanged, even
/// for excluded pairs. The complete MST, linkage, condensation, selection, and
/// scores are then rebuilt through the ordinary production implementation.
/// A disconnected permitted graph is rejected instead of returning a forest.
pub fn hdbscan_with_core_distances_and_excluded_edges(
    cosines: &CosineMatrix,
    config: HdbscanConfig,
    core_distances: &[f64],
    excluded_edges: &[(usize, usize)],
) -> Result<HdbscanResult> {
    validate(cosines.count(), config)?;
    if core_distances.len() != cosines.count() {
        return Err(invalid(format!(
            "supplied core distances count {} does not match vector count {}",
            core_distances.len(),
            cosines.count()
        )));
    }
    for (ordinal, distance) in core_distances.iter().enumerate() {
        if !distance.is_finite() || *distance < 0.0 {
            return Err(invalid(format!(
                "supplied core distance at input ordinal {ordinal} must be finite and nonnegative"
            )));
        }
    }

    let angular_distances = angular_distances(cosines)?;
    hdbscan_from_distances(
        &angular_distances,
        core_distances.to_vec(),
        config,
        excluded_edges,
    )
}

fn hdbscan_from_distances(
    angular_distances: &[f64],
    core_distances: Vec<f64>,
    config: HdbscanConfig,
    excluded_edges: &[(usize, usize)],
) -> Result<HdbscanResult> {
    let vector_count = core_distances.len();
    let mutual_reachability_distances =
        mutual_reachability_distances(angular_distances, &core_distances, vector_count);
    let minimum_spanning_tree =
        exact_prim_mst(&mutual_reachability_distances, vector_count, excluded_edges)?;
    let single_linkage_tree = single_linkage_tree(&minimum_spanning_tree, vector_count)?;
    let condensed_tree =
        condense_tree(&single_linkage_tree, vector_count, config.min_cluster_size)?;

    let raw_stabilities = cluster_stabilities(&condensed_tree, vector_count)?;
    let selected = match config.selection_method {
        ClusterSelectionMethod::ExcessOfMass => {
            select_excess_of_mass(&condensed_tree, &raw_stabilities, vector_count)
        }
        ClusterSelectionMethod::Leaf => select_leaves(&condensed_tree, vector_count),
    };
    let assignments =
        assign_selected_clusters(&condensed_tree, &selected, &raw_stabilities, vector_count)?;
    let mut clusters = assignments.clusters;
    clusters.sort_by(|left, right| {
        left.members
            .cmp(&right.members)
            .then(left.id.cmp(&right.id))
    });

    // Sorting clusters for stable public output changes their ordinal labels.
    let ordinal_by_id = clusters
        .iter()
        .enumerate()
        .map(|(ordinal, cluster)| (cluster.id, ordinal))
        .collect::<BTreeMap<_, _>>();
    let labels = assignments
        .labels
        .into_iter()
        .map(|cluster_id| cluster_id.map(|id| ordinal_by_id[&id]))
        .collect::<Vec<_>>();
    let noise = labels
        .iter()
        .enumerate()
        .filter_map(|(point, label)| label.is_none().then_some(point))
        .collect();
    let outlier_scores = glosh_outlier_scores(&condensed_tree, vector_count)?;

    Ok(HdbscanResult {
        config,
        core_distances,
        minimum_spanning_tree,
        single_linkage_tree,
        condensed_tree,
        clusters,
        labels,
        noise,
        membership_strengths: assignments.membership_strengths,
        outlier_scores,
        vector_count,
        mutual_reachability_distances,
    })
}

fn validate(vector_count: usize, config: HdbscanConfig) -> Result<()> {
    if vector_count < 2 {
        return Err(invalid("at least two vectors are required"));
    }
    if config.min_samples == 0 || config.min_samples > vector_count {
        return Err(invalid(format!(
            "min_samples must count between 1 and {vector_count} vectors including self"
        )));
    }
    if config.min_cluster_size < 2 || config.min_cluster_size > vector_count {
        return Err(invalid(format!(
            "min_cluster_size must be between 2 and {vector_count}"
        )));
    }
    Ok(())
}

fn angular_distances(cosines: &CosineMatrix) -> Result<Vec<f64>> {
    let count = cosines.count();
    let mut distances = vec![0.0; count * count];
    for left in 0..count {
        for right in (left + 1)..count {
            let cosine = cosines
                .get(left, right)
                .map_err(|error| invalid(error.to_string()))?;
            let distance = cosine.acos();
            if !distance.is_finite() {
                return Err(invalid("angular distance is not finite"));
            }
            if distance == 0.0 {
                return Err(invalid(format!(
                    "identical vector directions at input ordinals {left} and {right}; deduplicate embeddings before HDBSCAN*"
                )));
            }
            distances[left * count + right] = distance;
            distances[right * count + left] = distance;
        }
    }
    Ok(distances)
}

fn core_distances(distances: &[f64], count: usize, min_samples: usize) -> Vec<f64> {
    (0..count)
        .map(|point| {
            let mut neighborhood = (0..count)
                .map(|other| distances[point * count + other])
                .collect::<Vec<_>>();
            neighborhood.sort_by(f64::total_cmp);
            neighborhood[min_samples - 1]
        })
        .collect()
}

fn mutual_reachability_distances(
    distances: &[f64],
    core_distances: &[f64],
    count: usize,
) -> Vec<f64> {
    let mut mutual = vec![0.0; count * count];
    for left in 0..count {
        for right in left..count {
            let value = distances[left * count + right]
                .max(core_distances[left])
                .max(core_distances[right]);
            mutual[left * count + right] = value;
            mutual[right * count + left] = value;
        }
    }
    mutual
}

fn exact_prim_mst(
    distances: &[f64],
    count: usize,
    excluded_edges: &[(usize, usize)],
) -> Result<Vec<MinimumSpanningTreeEdge>> {
    // Dense membership keeps Prim O(n^2), without allocating another matrix
    // for the original complete-graph calculation.
    let mut excluded = if excluded_edges.is_empty() {
        Vec::new()
    } else {
        vec![false; count * count]
    };
    for &(left, right) in excluded_edges {
        if left >= count || right >= count || left == right {
            return Err(invalid(
                "excluded edges must contain distinct in-bounds input ordinals",
            ));
        }
        excluded[left * count + right] = true;
        excluded[right * count + left] = true;
    }
    let mut in_tree = vec![false; count];
    let mut best_distance = vec![f64::INFINITY; count];
    let mut best_source = vec![usize::MAX; count];
    let mut current = 0;
    let mut edges = Vec::with_capacity(count - 1);

    for _ in 1..count {
        in_tree[current] = true;

        for target in 0..count {
            if in_tree[target]
                || excluded
                    .get(current * count + target)
                    .copied()
                    .unwrap_or(false)
            {
                continue;
            }
            let candidate = distances[current * count + target];
            if candidate.total_cmp(&best_distance[target]).is_lt()
                || (candidate.total_cmp(&best_distance[target]).is_eq()
                    && current < best_source[target])
            {
                best_distance[target] = candidate;
                best_source[target] = current;
            }
        }

        let next = (0..count)
            .filter(|target| !in_tree[*target])
            .min_by(|left, right| {
                best_distance[*left]
                    .total_cmp(&best_distance[*right])
                    .then(best_source[*left].cmp(&best_source[*right]))
                    .then(left.cmp(right))
            })
            .ok_or_else(|| invalid("minimum spanning tree is disconnected"))?;
        let source = best_source[next];
        if source == usize::MAX || !best_distance[next].is_finite() {
            return Err(invalid(
                "minimum spanning tree contains no finite connecting edge",
            ));
        }
        let (left, right) = canonical_pair(source, next);
        edges.push(MinimumSpanningTreeEdge {
            left,
            right,
            mutual_reachability_distance: best_distance[next],
        });
        current = next;
    }

    Ok(edges)
}

fn single_linkage_tree(
    minimum_spanning_tree: &[MinimumSpanningTreeEdge],
    count: usize,
) -> Result<Vec<SingleLinkageNode>> {
    let mut edges = minimum_spanning_tree.to_vec();
    edges.sort_by(|left, right| {
        left.mutual_reachability_distance
            .total_cmp(&right.mutual_reachability_distance)
            .then(left.left.cmp(&right.left))
            .then(left.right.cmp(&right.right))
    });

    let mut union_find = UnionFind::new(count);
    let mut node_for_root = (0..count).collect::<Vec<_>>();
    let mut sizes = vec![1usize; count.saturating_mul(2).saturating_sub(1)];
    let mut hierarchy = Vec::with_capacity(count - 1);

    for (offset, edge) in edges.iter().enumerate() {
        let left_root = union_find.find(edge.left);
        let right_root = union_find.find(edge.right);
        if left_root == right_root {
            return Err(invalid("minimum spanning tree edge forms a cycle"));
        }
        let (left, right) = canonical_pair(node_for_root[left_root], node_for_root[right_root]);
        let id = count + offset;
        let size = sizes[left] + sizes[right];
        sizes[id] = size;
        let root = union_find.union_roots(left_root, right_root);
        node_for_root[root] = id;
        hierarchy.push(SingleLinkageNode {
            id,
            left,
            right,
            mutual_reachability_distance: edge.mutual_reachability_distance,
            size,
        });
    }

    if hierarchy.last().map(|node| node.size) != Some(count) {
        return Err(invalid("single-linkage tree does not contain every vector"));
    }
    Ok(hierarchy)
}

fn condense_tree(
    hierarchy: &[SingleLinkageNode],
    count: usize,
    min_cluster_size: usize,
) -> Result<Vec<CondensedTreeEdge>> {
    let root = count.saturating_mul(2).saturating_sub(2);
    let mut queue = VecDeque::from([(root, count)]);
    let mut next_label = count + 1;
    let mut result = Vec::with_capacity(count.saturating_mul(2));

    while let Some((node, parent)) = queue.pop_front() {
        if node < count {
            return Err(invalid("a retained condensed cluster is a singleton"));
        }
        let row = hierarchy
            .get(node - count)
            .ok_or_else(|| invalid("single-linkage node ID is invalid"))?;
        let split_distance = row.mutual_reachability_distance;
        let lambda = reciprocal_distance(split_distance)?;

        // Definition 3.2 / Algorithm 1 removes all equal-weight edges at
        // once. A binary single-linkage encoding can contain an arbitrary
        // chain of merges at that same distance, so expose the entire
        // multifurcation before applying the minimum-cluster-size rule.
        let mut children = Vec::new();
        collect_children_below_tied_split(node, split_distance, hierarchy, count, &mut children)?;
        children.sort_by_key(|child| subtree_minimum_point(*child, hierarchy, count));

        let mut retained = Vec::new();
        for child in children {
            let child_size = hierarchy_size(child, hierarchy, count)?;
            if child_size >= min_cluster_size {
                retained.push((child, child_size));
            } else {
                for point in subtree_points(child, hierarchy, count)? {
                    result.push(CondensedTreeEdge {
                        parent,
                        child: point,
                        lambda,
                        child_size: 1,
                    });
                }
            }
        }

        if retained.len() == 1 {
            // One significant component means the parent only shrank; its
            // identity persists, as specified by hierarchy simplification.
            queue.push_back((retained[0].0, parent));
        } else {
            // Zero significant components means the parent disappeared.
            // Two or more are a true (possibly multiway) split.
            for (child, child_size) in retained {
                let child_label = next_label;
                next_label += 1;
                result.push(CondensedTreeEdge {
                    parent,
                    child: child_label,
                    lambda,
                    child_size,
                });
                queue.push_back((child, child_label));
            }
        }
    }

    let mut point_counts = vec![0usize; count];
    for edge in &result {
        if edge.child < count {
            point_counts[edge.child] += 1;
        }
    }
    if point_counts.iter().any(|occurrences| *occurrences != 1) {
        return Err(invalid(
            "every vector must leave exactly one condensed-tree cluster",
        ));
    }

    Ok(result)
}

fn collect_children_below_tied_split(
    node: usize,
    split_distance: f64,
    hierarchy: &[SingleLinkageNode],
    count: usize,
    result: &mut Vec<usize>,
) -> Result<()> {
    if node < count {
        result.push(node);
        return Ok(());
    }
    let row = hierarchy
        .get(node - count)
        .ok_or_else(|| invalid("single-linkage split contains an invalid merge"))?;
    if row
        .mutual_reachability_distance
        .total_cmp(&split_distance)
        .is_eq()
    {
        collect_children_below_tied_split(row.left, split_distance, hierarchy, count, result)?;
        collect_children_below_tied_split(row.right, split_distance, hierarchy, count, result)?;
    } else {
        result.push(node);
    }
    Ok(())
}

fn subtree_points(
    node: usize,
    hierarchy: &[SingleLinkageNode],
    count: usize,
) -> Result<Vec<usize>> {
    let mut stack = vec![node];
    let mut points = Vec::new();
    while let Some(current) = stack.pop() {
        if current < count {
            points.push(current);
        } else {
            let row = hierarchy
                .get(current - count)
                .ok_or_else(|| invalid("single-linkage subtree contains an invalid merge"))?;
            stack.push(row.right);
            stack.push(row.left);
        }
    }
    points.sort_unstable();
    Ok(points)
}

fn subtree_minimum_point(node: usize, hierarchy: &[SingleLinkageNode], count: usize) -> usize {
    if node < count {
        node
    } else {
        let row = &hierarchy[node - count];
        subtree_minimum_point(row.left, hierarchy, count)
            .min(subtree_minimum_point(row.right, hierarchy, count))
    }
}

fn hierarchy_size(node: usize, hierarchy: &[SingleLinkageNode], count: usize) -> Result<usize> {
    if node < count {
        Ok(1)
    } else {
        hierarchy
            .get(node - count)
            .map(|row| row.size)
            .ok_or_else(|| invalid("single-linkage child ID is invalid"))
    }
}

fn cluster_stabilities(
    condensed_tree: &[CondensedTreeEdge],
    count: usize,
) -> Result<BTreeMap<usize, f64>> {
    let mut births = BTreeMap::from([(count, 0.0)]);
    for edge in condensed_tree {
        if edge.child >= count && births.insert(edge.child, edge.lambda).is_some() {
            return Err(invalid("condensed cluster has multiple parents"));
        }
    }

    let mut stabilities = condensed_tree
        .iter()
        .map(|edge| edge.parent)
        .collect::<BTreeSet<_>>()
        .into_iter()
        .map(|cluster| (cluster, 0.0))
        .collect::<BTreeMap<_, _>>();
    for edge in condensed_tree {
        let birth = *births
            .get(&edge.parent)
            .ok_or_else(|| invalid("condensed cluster has no birth lambda"))?;
        let persistence = lambda_difference(edge.lambda, birth)?;
        let contribution = persistence * edge.child_size as f64;
        let stability = stabilities
            .get_mut(&edge.parent)
            .ok_or_else(|| invalid("condensed cluster has no stability entry"))?;
        *stability += contribution;
    }
    Ok(stabilities)
}

fn select_excess_of_mass(
    condensed_tree: &[CondensedTreeEdge],
    stabilities: &BTreeMap<usize, f64>,
    count: usize,
) -> BTreeSet<usize> {
    let children = cluster_children(condensed_tree, count);
    eom_subtree(count, count, &children, stabilities).1
}

fn eom_subtree(
    node: usize,
    root: usize,
    children: &BTreeMap<usize, Vec<usize>>,
    stabilities: &BTreeMap<usize, f64>,
) -> (f64, BTreeSet<usize>) {
    let mut child_total = 0.0;
    let mut child_selection = BTreeSet::new();
    for child in children.get(&node).into_iter().flatten() {
        let (stability, selected) = eom_subtree(*child, root, children, stabilities);
        child_total += stability;
        child_selection.extend(selected);
    }

    if node == root {
        return (child_total, child_selection);
    }

    let own = stabilities.get(&node).copied().unwrap_or(0.0);
    // Campello et al.'s dynamic program selects the parent on an exact tie.
    if own >= child_total {
        (own, BTreeSet::from([node]))
    } else {
        (child_total, child_selection)
    }
}

fn select_leaves(condensed_tree: &[CondensedTreeEdge], count: usize) -> BTreeSet<usize> {
    let children = cluster_children(condensed_tree, count);
    condensed_tree
        .iter()
        .map(|edge| edge.parent)
        .filter(|cluster| *cluster != count && !children.contains_key(cluster))
        .collect()
}

fn cluster_children(
    condensed_tree: &[CondensedTreeEdge],
    count: usize,
) -> BTreeMap<usize, Vec<usize>> {
    let mut children = BTreeMap::<usize, Vec<usize>>::new();
    for edge in condensed_tree {
        if edge.child >= count {
            children.entry(edge.parent).or_default().push(edge.child);
        }
    }
    for values in children.values_mut() {
        values.sort_unstable();
    }
    children
}

fn assign_selected_clusters(
    condensed_tree: &[CondensedTreeEdge],
    selected: &BTreeSet<usize>,
    stabilities: &BTreeMap<usize, f64>,
    count: usize,
) -> Result<FlatAssignments> {
    let mut cluster_parent = BTreeMap::new();
    let mut point_parent = vec![None; count];
    let mut point_lambda = vec![0.0; count];
    let mut cluster_death = BTreeMap::<usize, f64>::new();

    for edge in condensed_tree {
        cluster_death
            .entry(edge.parent)
            .and_modify(|value| *value = value.max(edge.lambda))
            .or_insert(edge.lambda);
        if edge.child < count {
            if point_parent[edge.child].replace(edge.parent).is_some() {
                return Err(invalid("vector has multiple condensed-tree parents"));
            }
            point_lambda[edge.child] = edge.lambda;
        } else if cluster_parent.insert(edge.child, edge.parent).is_some() {
            return Err(invalid("condensed cluster has multiple parents"));
        }
    }

    let mut labels = vec![None; count];
    let mut membership_strengths = vec![0.0; count];
    let mut members = selected
        .iter()
        .map(|cluster| (*cluster, Vec::new()))
        .collect::<BTreeMap<_, _>>();

    for point in 0..count {
        let mut cluster =
            point_parent[point].ok_or_else(|| invalid("vector has no condensed-tree parent"))?;
        let assigned = loop {
            if selected.contains(&cluster) {
                break Some(cluster);
            }
            if cluster == count {
                break None;
            }
            cluster = *cluster_parent
                .get(&cluster)
                .ok_or_else(|| invalid("condensed cluster has no parent"))?;
        };

        if let Some(cluster) = assigned {
            labels[point] = Some(cluster);
            members
                .get_mut(&cluster)
                .ok_or_else(|| invalid("selected cluster has no member list"))?
                .push(point);
            let maximum = cluster_death.get(&cluster).copied().unwrap_or(0.0);
            membership_strengths[point] = membership_strength(point_lambda[point], maximum)?;
        }
    }

    let clusters = members
        .into_iter()
        .map(|(id, members)| HdbscanCluster {
            id,
            members,
            stability: stabilities.get(&id).copied().unwrap_or(0.0),
        })
        .collect();
    Ok(FlatAssignments {
        labels,
        clusters,
        membership_strengths,
    })
}

struct FlatAssignments {
    labels: Vec<Option<usize>>,
    clusters: Vec<HdbscanCluster>,
    membership_strengths: Vec<f64>,
}

fn membership_strength(point_lambda: f64, cluster_maximum: f64) -> Result<f64> {
    if !point_lambda.is_finite() || !cluster_maximum.is_finite() {
        return Err(invalid("membership lambda is not finite"));
    }
    if cluster_maximum == 0.0 {
        Ok(1.0)
    } else {
        Ok((point_lambda.min(cluster_maximum) / cluster_maximum).clamp(0.0, 1.0))
    }
}

fn glosh_outlier_scores(condensed_tree: &[CondensedTreeEdge], count: usize) -> Result<Vec<f64>> {
    let mut maximum_descendant_lambda = BTreeMap::<usize, f64>::new();
    let mut point_parent = vec![None; count];
    let mut point_lambda = vec![0.0; count];

    for edge in condensed_tree {
        maximum_descendant_lambda
            .entry(edge.parent)
            .and_modify(|value| *value = value.max(edge.lambda))
            .or_insert(edge.lambda);
        if edge.child < count {
            point_parent[edge.child] = Some(edge.parent);
            point_lambda[edge.child] = edge.lambda;
        }
    }

    // Condensed cluster IDs are allocated after their parents. Reverse ID
    // order is therefore a postorder for propagating each descendant's peak.
    let mut cluster_edges = condensed_tree
        .iter()
        .filter(|edge| edge.child >= count)
        .collect::<Vec<_>>();
    cluster_edges.sort_by_key(|edge| std::cmp::Reverse(edge.child));
    for edge in cluster_edges {
        let child_maximum = maximum_descendant_lambda
            .get(&edge.child)
            .copied()
            .unwrap_or(edge.lambda);
        maximum_descendant_lambda
            .entry(edge.parent)
            .and_modify(|value| *value = value.max(child_maximum))
            .or_insert(child_maximum);
    }

    (0..count)
        .map(|point| {
            let parent = point_parent[point]
                .ok_or_else(|| invalid("vector has no condensed-tree parent for GLOSH"))?;
            let maximum = maximum_descendant_lambda
                .get(&parent)
                .copied()
                .unwrap_or(0.0);
            outlier_score(point_lambda[point], maximum)
        })
        .collect()
}

fn outlier_score(point_lambda: f64, maximum_lambda: f64) -> Result<f64> {
    if !point_lambda.is_finite() || !maximum_lambda.is_finite() {
        return Err(invalid("GLOSH lambda is not finite"));
    }
    if maximum_lambda == 0.0 {
        Ok(0.0)
    } else {
        Ok(((maximum_lambda - point_lambda) / maximum_lambda).clamp(0.0, 1.0))
    }
}

fn reciprocal_distance(distance: f64) -> Result<f64> {
    if !distance.is_finite() || distance <= 0.0 {
        Err(invalid(
            "condensed-tree split distance must be finite and positive",
        ))
    } else {
        Ok(1.0 / distance)
    }
}

fn lambda_difference(lambda: f64, birth: f64) -> Result<f64> {
    if !lambda.is_finite() || !birth.is_finite() {
        return Err(invalid("condensed-tree lambda is not finite"));
    }
    if lambda < birth {
        return Err(invalid(
            "condensed-tree lambda decreases below cluster birth",
        ));
    }
    Ok(lambda - birth)
}

fn canonical_pair(left: usize, right: usize) -> (usize, usize) {
    if left <= right {
        (left, right)
    } else {
        (right, left)
    }
}

#[derive(Debug)]
struct UnionFind {
    parent: Vec<usize>,
    rank: Vec<u8>,
}

impl UnionFind {
    fn new(count: usize) -> Self {
        Self {
            parent: (0..count).collect(),
            rank: vec![0; count],
        }
    }

    fn find(&mut self, point: usize) -> usize {
        if self.parent[point] != point {
            self.parent[point] = self.find(self.parent[point]);
        }
        self.parent[point]
    }

    fn union_roots(&mut self, left: usize, right: usize) -> usize {
        let (root, child) = match self.rank[left].cmp(&self.rank[right]) {
            std::cmp::Ordering::Less => (right, left),
            std::cmp::Ordering::Greater => (left, right),
            std::cmp::Ordering::Equal if left <= right => {
                self.rank[left] += 1;
                (left, right)
            }
            std::cmp::Ordering::Equal => {
                self.rank[right] += 1;
                (right, left)
            }
        };
        self.parent[child] = root;
        root
    }
}

fn invalid(message: impl Into<String>) -> HdbscanError {
    HdbscanError::Invariant(message.into())
}
