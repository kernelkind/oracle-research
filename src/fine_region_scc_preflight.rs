//! Frozen SCC schedules and mechanical comparison with the existing hierarchy.

use std::collections::{BTreeMap, BTreeSet};

use serde::{Deserialize, Serialize};

use crate::fine_region_hierarchy::{
    FineRegionHierarchy, FineRegionHierarchyError, FineSegment, HierarchyNode, invalid,
};
use crate::fine_region_scc::{SccHierarchy, scc_hierarchy_over_selected_segments};

pub const G200_SCHEDULE_ID: &str = "g200";
pub const D2_SCHEDULE_ID: &str = "d2";
pub const D_SQRT_2_SCHEDULE_ID: &str = "d_sqrt_2";

pub type Result<T> = std::result::Result<T, FineRegionHierarchyError>;

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct FrozenSccSchedule {
    pub schedule_id: String,
    pub source: String,
    pub minimum_similarities: Vec<f64>,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SccPreflightReport {
    pub fine_segment_count: usize,
    pub average_linkage_node_count: usize,
    pub variants: Vec<SccPreflightVariant>,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SccPreflightVariant {
    pub schedule_id: String,
    pub schedule_source: String,
    pub fine_segment_count: usize,
    pub internal_node_count: usize,
    pub binary_node_count: usize,
    pub max_child_count: usize,
    pub average_linkage_node_matches: usize,
    pub average_linkage_node_count: usize,
    pub node_comparisons: Vec<SccNodeComparison>,
    pub hierarchy: SccHierarchy,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SccNodeComparison {
    pub scc_merge_index: usize,
    pub descendant_fine_segment_ids: Vec<String>,
    pub average_linkage_merge_index: Option<usize>,
}

/// Returns the three schedules frozen before semantic inspection of the pilot.
pub fn frozen_scc_schedules() -> Result<Vec<FrozenSccSchedule>> {
    let g200 = (0..200)
        .map(|index| 10.0_f64.powf(-3.0 * index as f64 / 199.0))
        .collect::<Vec<_>>();
    let d2_distances: [f64; 11] = [
        0.001, 0.002, 0.004, 0.008, 0.016, 0.032, 0.064, 0.128, 0.256, 0.512, 1.0,
    ];
    let d2 = d2_distances
        .iter()
        .copied()
        .map(|distance| 1.0 - distance)
        .collect::<Vec<_>>();
    let mut d_sqrt_2_distances = vec![d2_distances[0]];
    for pair in d2_distances.windows(2) {
        d_sqrt_2_distances.push((pair[0] * pair[1]).sqrt());
        d_sqrt_2_distances.push(pair[1]);
    }
    let d_sqrt_2 = d_sqrt_2_distances
        .into_iter()
        .map(|distance| 1.0 - distance)
        .collect::<Vec<_>>();

    let schedules = vec![
        FrozenSccSchedule {
            schedule_id: G200_SCHEDULE_ID.to_owned(),
            source: "published SCC cosine schedule: 200 geometrically spaced similarities from 1.0 through 0.001".to_owned(),
            minimum_similarities: g200,
        },
        FrozenSccSchedule {
            schedule_id: D2_SCHEDULE_ID.to_owned(),
            source: "theorem-inspired schedule: cosine-distance thresholds double from 0.001 through 0.512, then 1.0".to_owned(),
            minimum_similarities: d2,
        },
        FrozenSccSchedule {
            schedule_id: D_SQRT_2_SCHEDULE_ID.to_owned(),
            source: "sensitivity schedule: one geometric midpoint between each doubling threshold".to_owned(),
            minimum_similarities: d_sqrt_2,
        },
    ];
    for schedule in &schedules {
        validate_schedule(schedule)?;
    }
    Ok(schedules)
}

pub fn build_scc_preflight(
    normalized_vectors: &[Vec<f64>],
    fine_segments: &[FineSegment],
    average_linkage: &FineRegionHierarchy,
    schedules: &[FrozenSccSchedule],
) -> Result<SccPreflightReport> {
    if schedules.is_empty() {
        return Err(invalid("the SCC preflight has no schedules"));
    }
    let mut schedule_ids = BTreeSet::new();
    for schedule in schedules {
        validate_schedule(schedule)?;
        if !schedule_ids.insert(schedule.schedule_id.as_str()) {
            return Err(invalid("the SCC preflight schedule IDs are not unique"));
        }
    }
    if fine_segments != average_linkage.fine_segments {
        return Err(invalid(
            "the SCC leaves differ from the average-linkage comparison leaves",
        ));
    }

    let average_sets = average_descendant_sets(average_linkage)?;
    let variants = schedules
        .iter()
        .map(|schedule| {
            let hierarchy = scc_hierarchy_over_selected_segments(
                normalized_vectors,
                fine_segments,
                &schedule.minimum_similarities,
            )?;
            let scc_sets = scc_descendant_sets(&hierarchy)?;
            let node_comparisons = scc_sets
                .iter()
                .enumerate()
                .map(
                    |(merge_index, descendant_fine_segment_ids)| SccNodeComparison {
                        scc_merge_index: merge_index,
                        average_linkage_merge_index: average_sets
                            .get(descendant_fine_segment_ids)
                            .copied(),
                        descendant_fine_segment_ids: descendant_fine_segment_ids.clone(),
                    },
                )
                .collect::<Vec<_>>();
            let average_linkage_node_matches = node_comparisons
                .iter()
                .filter(|node| node.average_linkage_merge_index.is_some())
                .count();
            let binary_node_count = hierarchy
                .merges
                .iter()
                .filter(|merge| merge.children.len() == 2)
                .count();
            let max_child_count = hierarchy
                .merges
                .iter()
                .map(|merge| merge.children.len())
                .max()
                .unwrap_or(0);
            Ok(SccPreflightVariant {
                schedule_id: schedule.schedule_id.clone(),
                schedule_source: schedule.source.clone(),
                fine_segment_count: hierarchy.fine_segments.len(),
                internal_node_count: hierarchy.merges.len(),
                binary_node_count,
                max_child_count,
                average_linkage_node_matches,
                average_linkage_node_count: average_sets.len(),
                node_comparisons,
                hierarchy,
            })
        })
        .collect::<Result<Vec<_>>>()?;

    Ok(SccPreflightReport {
        fine_segment_count: fine_segments.len(),
        average_linkage_node_count: average_sets.len(),
        variants,
    })
}

fn validate_schedule(schedule: &FrozenSccSchedule) -> Result<()> {
    if schedule.schedule_id.trim().is_empty()
        || schedule.source.trim().is_empty()
        || schedule.minimum_similarities.is_empty()
        || schedule
            .minimum_similarities
            .iter()
            .any(|value| !value.is_finite() || !(-1.0..=1.0).contains(value))
        || schedule
            .minimum_similarities
            .windows(2)
            .any(|pair| pair[0] <= pair[1])
    {
        return Err(invalid("an SCC preflight schedule is invalid"));
    }
    Ok(())
}

fn average_descendant_sets(
    hierarchy: &FineRegionHierarchy,
) -> Result<BTreeMap<Vec<String>, usize>> {
    let mut nodes = hierarchy
        .fine_segments
        .iter()
        .map(|segment| {
            (
                HierarchyNode::FineSegment(segment.segment_id.clone()),
                vec![segment.segment_id.clone()],
            )
        })
        .collect::<BTreeMap<_, _>>();
    let mut sets = BTreeMap::new();
    for merge in &hierarchy.merges {
        let descendants = descendants_for_children(&nodes, &merge.children)?;
        let node = HierarchyNode::Merge(merge.merge_index);
        if nodes.insert(node, descendants.clone()).is_some()
            || sets.insert(descendants, merge.merge_index).is_some()
        {
            return Err(invalid(
                "the average-linkage hierarchy contains duplicate internal nodes",
            ));
        }
    }
    Ok(sets)
}

fn scc_descendant_sets(hierarchy: &SccHierarchy) -> Result<Vec<Vec<String>>> {
    let mut nodes = hierarchy
        .fine_segments
        .iter()
        .map(|segment| {
            (
                HierarchyNode::FineSegment(segment.segment_id.clone()),
                vec![segment.segment_id.clone()],
            )
        })
        .collect::<BTreeMap<_, _>>();
    let mut sets = BTreeSet::new();
    let mut ordered = Vec::with_capacity(hierarchy.merges.len());
    for merge in &hierarchy.merges {
        let descendants = descendants_for_children(&nodes, &merge.children)?;
        let node = HierarchyNode::Merge(merge.merge_index);
        if nodes.insert(node, descendants.clone()).is_some() || !sets.insert(descendants.clone()) {
            return Err(invalid(
                "an SCC hierarchy contains duplicate internal nodes",
            ));
        }
        ordered.push(descendants);
    }
    Ok(ordered)
}

fn descendants_for_children(
    nodes: &BTreeMap<HierarchyNode, Vec<String>>,
    children: &[HierarchyNode],
) -> Result<Vec<String>> {
    let mut descendants = children
        .iter()
        .map(|child| {
            nodes
                .get(child)
                .cloned()
                .ok_or_else(|| invalid("a hierarchy child appears before it is defined"))
        })
        .collect::<Result<Vec<_>>>()?
        .into_iter()
        .flatten()
        .collect::<Vec<_>>();
    descendants.sort();
    if descendants.windows(2).any(|pair| pair[0] == pair[1]) {
        return Err(invalid("a hierarchy node repeats a fine-segment leaf"));
    }
    Ok(descendants)
}
