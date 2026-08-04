//! Deterministic average-linkage hierarchy over an accepted fine-segment partition.

use std::collections::BTreeSet;

use kodama::{Method, linkage};
use serde::{Deserialize, Serialize};
use thiserror::Error;

const UNIT_NORM_TOLERANCE: f64 = 1.0e-5;

pub type Result<T> = std::result::Result<T, FineRegionHierarchyError>;

#[derive(Debug, Error)]
pub enum FineRegionHierarchyError {
    #[error("fine-region hierarchy invariant failed: {0}")]
    Invariant(String),
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct FineSegment {
    pub segment_id: String,
    pub members: Vec<usize>,
}

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(tag = "kind", content = "id", rename_all = "snake_case")]
pub enum HierarchyNode {
    FineSegment(String),
    Merge(usize),
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct HierarchyMerge {
    pub merge_index: usize,
    pub children: [HierarchyNode; 2],
    pub similarity: f64,
    pub fine_segment_count: usize,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct FineRegionHierarchy {
    pub fine_segments: Vec<FineSegment>,
    pub merges: Vec<HierarchyMerge>,
    pub root: HierarchyNode,
}

pub fn average_linkage_hierarchy(
    normalized_vectors: &[Vec<f64>],
    fine_segments: &[FineSegment],
) -> Result<FineRegionHierarchy> {
    build_average_linkage_hierarchy(normalized_vectors, fine_segments, true)
}

pub fn average_linkage_hierarchy_over_selected_segments(
    normalized_vectors: &[Vec<f64>],
    fine_segments: &[FineSegment],
) -> Result<FineRegionHierarchy> {
    build_average_linkage_hierarchy(normalized_vectors, fine_segments, false)
}

fn build_average_linkage_hierarchy(
    normalized_vectors: &[Vec<f64>],
    fine_segments: &[FineSegment],
    require_complete_vector_partition: bool,
) -> Result<FineRegionHierarchy> {
    let vectors = normalized_copy(normalized_vectors)?;
    let fine_segments = validate_and_canonicalize(
        vectors.len(),
        fine_segments,
        require_complete_vector_partition,
    )?;
    let count = fine_segments.len();
    if count == 1 {
        return Ok(FineRegionHierarchy {
            root: HierarchyNode::FineSegment(fine_segments[0].segment_id.clone()),
            fine_segments,
            merges: Vec::new(),
        });
    }

    let means = fine_segments
        .iter()
        .map(|segment| raw_mean(&vectors, &segment.members))
        .collect::<Vec<_>>();
    let mut dissimilarities = Vec::with_capacity(count * (count - 1) / 2);
    for left in 0..(count - 1) {
        for right in (left + 1)..count {
            let similarity = dot(&means[left], &means[right]);
            dissimilarities.push(1.0 - similarity);
        }
    }

    let dendrogram = linkage(&mut dissimilarities, count, Method::Average);
    let mut nodes = fine_segments
        .iter()
        .map(|segment| {
            (
                HierarchyNode::FineSegment(segment.segment_id.clone()),
                vec![segment.segment_id.clone()],
            )
        })
        .collect::<Vec<_>>();
    let mut merges = Vec::with_capacity(count - 1);

    for (merge_index, step) in dendrogram.steps().iter().enumerate() {
        let left = nodes
            .get(step.cluster1)
            .ok_or_else(|| invalid("average-linkage output names an unknown left child"))?;
        let right = nodes
            .get(step.cluster2)
            .ok_or_else(|| invalid("average-linkage output names an unknown right child"))?;
        let children = if left.1 <= right.1 {
            [left.0.clone(), right.0.clone()]
        } else {
            [right.0.clone(), left.0.clone()]
        };
        let mut fine_segment_ids = left.1.clone();
        fine_segment_ids.extend(right.1.iter().cloned());
        fine_segment_ids.sort();

        merges.push(HierarchyMerge {
            merge_index,
            children,
            similarity: 1.0 - step.dissimilarity,
            fine_segment_count: step.size,
        });
        nodes.push((HierarchyNode::Merge(merge_index), fine_segment_ids));
    }

    let root = HierarchyNode::Merge(merges.len() - 1);

    Ok(FineRegionHierarchy {
        fine_segments,
        merges,
        root,
    })
}

pub(crate) fn validate_and_canonicalize(
    vector_count: usize,
    fine_segments: &[FineSegment],
    require_complete_vector_partition: bool,
) -> Result<Vec<FineSegment>> {
    if fine_segments.is_empty() {
        return Err(invalid("the fine-segment partition is empty"));
    }

    let mut segments = fine_segments.to_vec();
    for segment in &mut segments {
        if segment.segment_id.trim().is_empty() {
            return Err(invalid("a fine segment has an empty ID"));
        }
        if segment.members.is_empty() {
            return Err(invalid(format!(
                "fine segment {} is empty",
                segment.segment_id
            )));
        }
        if segment.members.iter().any(|member| *member >= vector_count) {
            return Err(invalid(format!(
                "fine segment {} contains an out of bounds vector",
                segment.segment_id
            )));
        }
        segment.members.sort_unstable();
    }
    segments.sort_by(|left, right| left.segment_id.cmp(&right.segment_id));

    if segments
        .windows(2)
        .any(|pair| pair[0].segment_id == pair[1].segment_id)
    {
        return Err(invalid("fine-segment IDs are not unique"));
    }

    let members = segments
        .iter()
        .flat_map(|segment| segment.members.iter().copied())
        .collect::<BTreeSet<_>>();
    let occurrence_count = segments
        .iter()
        .map(|segment| segment.members.len())
        .sum::<usize>();
    if occurrence_count != members.len() {
        return Err(invalid(
            "the selected fine segments do not contain each referenced vector exactly once",
        ));
    }
    if require_complete_vector_partition
        && (occurrence_count != vector_count || members != (0..vector_count).collect())
    {
        return Err(invalid(
            "the fine-segment partition does not contain every vector exactly once",
        ));
    }

    Ok(segments)
}

pub(crate) fn normalized_copy(vectors: &[Vec<f64>]) -> Result<Vec<Vec<f64>>> {
    if vectors.is_empty() || vectors[0].is_empty() {
        return Err(invalid("the normalized vector input is empty"));
    }
    let dimensions = vectors[0].len();
    vectors
        .iter()
        .map(|vector| {
            if vector.len() != dimensions || vector.iter().any(|coordinate| !coordinate.is_finite())
            {
                return Err(invalid(
                    "normalized vectors have inconsistent dimensions or non-finite coordinates",
                ));
            }
            let norm = vector.iter().map(|value| value * value).sum::<f64>().sqrt();
            if !norm.is_finite() || (norm - 1.0).abs() > UNIT_NORM_TOLERANCE {
                return Err(invalid("a hierarchy input vector is not unit normalized"));
            }
            Ok(vector.iter().map(|coordinate| coordinate / norm).collect())
        })
        .collect()
}

pub(crate) fn raw_mean(vectors: &[Vec<f64>], members: &[usize]) -> Vec<f64> {
    let mut mean = vec![0.0; vectors[0].len()];
    for member in members {
        for (sum, coordinate) in mean.iter_mut().zip(&vectors[*member]) {
            *sum += coordinate;
        }
    }
    for coordinate in &mut mean {
        *coordinate /= members.len() as f64;
    }
    mean
}

pub(crate) fn dot(left: &[f64], right: &[f64]) -> f64 {
    left.iter()
        .zip(right)
        .map(|(left, right)| left * right)
        .sum()
}

pub(crate) fn invalid(message: impl Into<String>) -> FineRegionHierarchyError {
    FineRegionHierarchyError::Invariant(message.into())
}
