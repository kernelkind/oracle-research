//! Deterministic Sub-Cluster Component hierarchy over fixed fine-segment leaves.
//!
//! Linkage gives each fine segment equal weight. Similarity between two fine
//! segments is average cosine across their member vectors; similarity between
//! two later clusters is average similarity across their descendant fine
//! segments.

use std::collections::BTreeMap;

use serde::{Deserialize, Serialize};

use crate::fine_region_hierarchy::{
    FineRegionHierarchyError, FineSegment, HierarchyNode, dot, invalid, normalized_copy, raw_mean,
    validate_and_canonicalize,
};

pub type Result<T> = std::result::Result<T, FineRegionHierarchyError>;

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SccHierarchy {
    pub fine_segments: Vec<FineSegment>,
    pub minimum_similarities: Vec<f64>,
    pub rounds: Vec<SccRound>,
    pub merges: Vec<SccMerge>,
    pub roots: Vec<HierarchyNode>,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SccRound {
    pub round_index: usize,
    pub threshold_index: usize,
    pub minimum_similarity: f64,
    pub input_cluster_count: usize,
    pub resulting_cluster_count: usize,
    pub merge_indices: Vec<usize>,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SccMerge {
    pub merge_index: usize,
    pub round_index: usize,
    pub children: Vec<HierarchyNode>,
    pub nearest_neighbor_edges: Vec<SccNearestNeighborEdge>,
    pub fine_segment_count: usize,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SccNearestNeighborEdge {
    pub left: HierarchyNode,
    pub right: HierarchyNode,
    pub similarity: f64,
    pub left_selected_right: bool,
    pub right_selected_left: bool,
}

/// Builds SCC over a complete partition of the supplied vectors.
///
/// `minimum_similarities` must be strictly decreasing. At each value, SCC joins
/// every connected component of nearest-neighbor edges whose similarity is at
/// least that value. Exact ties resolve to the current cluster with the lowest
/// canonical fine-segment membership. SCC repeats one value until a pass makes
/// no merges, then advances to the next, lower value.
pub fn scc_hierarchy(
    normalized_vectors: &[Vec<f64>],
    fine_segments: &[FineSegment],
    minimum_similarities: &[f64],
) -> Result<SccHierarchy> {
    build_scc_hierarchy(
        normalized_vectors,
        fine_segments,
        minimum_similarities,
        true,
    )
}

/// Builds SCC over selected, disjoint fine segments without requiring them to
/// cover every supplied vector.
pub fn scc_hierarchy_over_selected_segments(
    normalized_vectors: &[Vec<f64>],
    fine_segments: &[FineSegment],
    minimum_similarities: &[f64],
) -> Result<SccHierarchy> {
    build_scc_hierarchy(
        normalized_vectors,
        fine_segments,
        minimum_similarities,
        false,
    )
}

fn build_scc_hierarchy(
    normalized_vectors: &[Vec<f64>],
    fine_segments: &[FineSegment],
    minimum_similarities: &[f64],
    require_complete_vector_partition: bool,
) -> Result<SccHierarchy> {
    validate_schedule(minimum_similarities)?;
    let vectors = normalized_copy(normalized_vectors)?;
    let fine_segments = validate_and_canonicalize(
        vectors.len(),
        fine_segments,
        require_complete_vector_partition,
    )?;
    let base_similarities = fine_segment_similarities(&vectors, &fine_segments);
    let mut clusters = fine_segments
        .iter()
        .enumerate()
        .map(|(index, segment)| Cluster {
            node: HierarchyNode::FineSegment(segment.segment_id.clone()),
            fine_segment_indices: vec![index],
        })
        .collect::<Vec<_>>();
    let mut rounds = Vec::new();
    let mut merges = Vec::new();
    let mut threshold_index = 0;

    while threshold_index < minimum_similarities.len() && clusters.len() > 1 {
        let minimum_similarity = minimum_similarities[threshold_index];
        let components =
            nearest_neighbor_components(&clusters, &base_similarities, minimum_similarity);
        if components
            .iter()
            .all(|component| component.members.len() == 1)
        {
            threshold_index += 1;
            continue;
        }

        let round_index = rounds.len();
        let input_cluster_count = clusters.len();
        let mut merge_indices = Vec::new();
        let mut next_clusters = Vec::with_capacity(components.len());
        for component in components {
            if component.members.len() == 1 {
                next_clusters.push(clusters[component.members[0]].clone());
                continue;
            }

            let mut children = component
                .members
                .iter()
                .map(|index| clusters[*index].clone())
                .collect::<Vec<_>>();
            children
                .sort_by(|left, right| left.fine_segment_indices.cmp(&right.fine_segment_indices));
            let mut fine_segment_indices = children
                .iter()
                .flat_map(|child| child.fine_segment_indices.iter().copied())
                .collect::<Vec<_>>();
            fine_segment_indices.sort_unstable();
            let merge_index = merges.len();
            let nearest_neighbor_edges = component
                .edges
                .iter()
                .map(|edge| SccNearestNeighborEdge {
                    left: clusters[edge.left].node.clone(),
                    right: clusters[edge.right].node.clone(),
                    similarity: edge.similarity,
                    left_selected_right: edge.left_selected_right,
                    right_selected_left: edge.right_selected_left,
                })
                .collect();
            merges.push(SccMerge {
                merge_index,
                round_index,
                children: children.iter().map(|child| child.node.clone()).collect(),
                nearest_neighbor_edges,
                fine_segment_count: fine_segment_indices.len(),
            });
            merge_indices.push(merge_index);
            next_clusters.push(Cluster {
                node: HierarchyNode::Merge(merge_index),
                fine_segment_indices,
            });
        }
        next_clusters
            .sort_by(|left, right| left.fine_segment_indices.cmp(&right.fine_segment_indices));
        rounds.push(SccRound {
            round_index,
            threshold_index,
            minimum_similarity,
            input_cluster_count,
            resulting_cluster_count: next_clusters.len(),
            merge_indices,
        });
        clusters = next_clusters;
    }

    Ok(SccHierarchy {
        fine_segments,
        minimum_similarities: minimum_similarities.to_vec(),
        rounds,
        merges,
        roots: clusters.into_iter().map(|cluster| cluster.node).collect(),
    })
}

#[derive(Clone, Debug)]
struct Cluster {
    node: HierarchyNode,
    fine_segment_indices: Vec<usize>,
}

fn validate_schedule(minimum_similarities: &[f64]) -> Result<()> {
    if minimum_similarities.is_empty() {
        return Err(invalid("the SCC minimum-similarity schedule is empty"));
    }
    if minimum_similarities
        .iter()
        .any(|similarity| !similarity.is_finite() || !(-1.0..=1.0).contains(similarity))
    {
        return Err(invalid(
            "SCC minimum similarities must be finite values between -1 and 1",
        ));
    }
    if minimum_similarities
        .windows(2)
        .any(|pair| pair[0] <= pair[1])
    {
        return Err(invalid(
            "the SCC minimum-similarity schedule is not strictly decreasing",
        ));
    }
    Ok(())
}

fn fine_segment_similarities(vectors: &[Vec<f64>], fine_segments: &[FineSegment]) -> Vec<Vec<f64>> {
    let means = fine_segments
        .iter()
        .map(|segment| raw_mean(vectors, &segment.members))
        .collect::<Vec<_>>();
    let mut similarities = vec![vec![1.0; means.len()]; means.len()];
    for left in 0..means.len() {
        for right in (left + 1)..means.len() {
            let similarity = dot(&means[left], &means[right]);
            similarities[left][right] = similarity;
            similarities[right][left] = similarity;
        }
    }
    similarities
}

fn nearest_neighbor_components(
    clusters: &[Cluster],
    base_similarities: &[Vec<f64>],
    minimum_similarity: f64,
) -> Vec<RoundComponent> {
    let similarities = current_cluster_similarities(clusters, base_similarities);
    let mut disjoint_set = DisjointSet::new(clusters.len());
    let mut selected = vec![vec![false; clusters.len()]; clusters.len()];
    for left in 0..clusters.len() {
        let right = (0..clusters.len())
            .filter(|right| *right != left)
            .max_by(|first, second| {
                similarities[left][*first]
                    .total_cmp(&similarities[left][*second])
                    .then_with(|| second.cmp(first))
            })
            .expect("more than one current cluster");
        if similarities[left][right] < minimum_similarity {
            continue;
        }
        selected[left][right] = true;
        disjoint_set.union(left, right);
    }

    let mut by_root = BTreeMap::<usize, Vec<usize>>::new();
    let mut root_by_index = Vec::with_capacity(clusters.len());
    for index in 0..clusters.len() {
        let root = disjoint_set.find(index);
        root_by_index.push(root);
        by_root.entry(root).or_default().push(index);
    }
    let mut edges_by_root = BTreeMap::<usize, Vec<RoundEdge>>::new();
    for left in 0..clusters.len() {
        for right in (left + 1)..clusters.len() {
            if !selected[left][right] && !selected[right][left] {
                continue;
            }
            let root = root_by_index[left];
            debug_assert_eq!(root, root_by_index[right]);
            edges_by_root.entry(root).or_default().push(RoundEdge {
                left,
                right,
                similarity: similarities[left][right],
                left_selected_right: selected[left][right],
                right_selected_left: selected[right][left],
            });
        }
    }
    let mut components = by_root
        .into_iter()
        .map(|(root, members)| RoundComponent {
            members,
            edges: edges_by_root.remove(&root).unwrap_or_default(),
        })
        .collect::<Vec<_>>();
    components.sort_by(|left, right| {
        clusters[left.members[0]]
            .fine_segment_indices
            .cmp(&clusters[right.members[0]].fine_segment_indices)
    });
    components
}

struct RoundComponent {
    members: Vec<usize>,
    edges: Vec<RoundEdge>,
}

struct RoundEdge {
    left: usize,
    right: usize,
    similarity: f64,
    left_selected_right: bool,
    right_selected_left: bool,
}

fn current_cluster_similarities(
    clusters: &[Cluster],
    base_similarities: &[Vec<f64>],
) -> Vec<Vec<f64>> {
    let mut similarities = vec![vec![1.0; clusters.len()]; clusters.len()];
    for left in 0..clusters.len() {
        for right in (left + 1)..clusters.len() {
            let mut sum = 0.0;
            for left_segment in &clusters[left].fine_segment_indices {
                for right_segment in &clusters[right].fine_segment_indices {
                    sum += base_similarities[*left_segment][*right_segment];
                }
            }
            let pair_count = clusters[left].fine_segment_indices.len()
                * clusters[right].fine_segment_indices.len();
            let similarity = sum / pair_count as f64;
            similarities[left][right] = similarity;
            similarities[right][left] = similarity;
        }
    }
    similarities
}

struct DisjointSet {
    parents: Vec<usize>,
}

impl DisjointSet {
    fn new(len: usize) -> Self {
        Self {
            parents: (0..len).collect(),
        }
    }

    fn find(&mut self, index: usize) -> usize {
        if self.parents[index] != index {
            self.parents[index] = self.find(self.parents[index]);
        }
        self.parents[index]
    }

    fn union(&mut self, left: usize, right: usize) {
        let left_root = self.find(left);
        let right_root = self.find(right);
        if left_root == right_root {
            return;
        }
        let (root, child) = if left_root < right_root {
            (left_root, right_root)
        } else {
            (right_root, left_root)
        };
        self.parents[child] = root;
    }
}
