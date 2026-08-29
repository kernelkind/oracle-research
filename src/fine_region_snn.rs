//! Shared-nearest-neighbor fine segmentation.
//!
//! This implements the final published algorithm in sections 2 and 4.2 of
//! Ertöz, Steinbach, and Kumar, *Finding Clusters of Different Sizes, Shapes,
//! and Densities in Noisy, High Dimensional Data* (SDM 2003,
//! <https://doi.org/10.1137/1.9781611972733.5>; author PDF:
//! <https://www-users.cse.umn.edu/~kumar/papers/SIAM_snn.pdf>):
//!
//! 1. calculate an exact, ordered `k`-nearest-neighbor list for every point;
//! 2. link two points only when each occurs in the other's list;
//! 3. define their SNN similarity as the raw number of neighbors the two lists
//!    share;
//! 4. retain links meeting the shared-neighbor threshold;
//! 5. define point density as the number of retained incident links; and
//! 6. connect core points, then attach qualifying non-core border points.
//!
//! The paper explicitly makes the shared-neighbor threshold inclusive, but its
//! algorithm and worked example disagree on equality at the core-density
//! threshold. This implementation resolves core equality inclusively. The
//! paper also does not specify which cluster receives a border point linked to
//! multiple core components. As a deterministic extension, an ambiguous border
//! chooses the incident core with the greatest shared-neighbor count, then the
//! smallest direct angular distance, then the lowest input ordinal. Border
//! points never connect core components. Exact angular-distance ties in
//! nearest-neighbor lists also use the lowest input ordinal.

use std::collections::BTreeMap;

use serde::{Deserialize, Serialize};
use thiserror::Error;

use crate::fine_region_partition::{CosineMatrix, FineRegionPartitionError};

pub type Result<T> = std::result::Result<T, SnnError>;

#[derive(Debug, Error)]
pub enum SnnError {
    #[error("SNN fine-segmentation invariant failed: {0}")]
    Invariant(String),
    #[error(transparent)]
    CosineMatrix(#[from] FineRegionPartitionError),
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SnnConfig {
    /// Number of exact angular-nearest neighbors retained for every point.
    pub neighbor_count: usize,
    /// Inclusive shared-neighbor count required for a reciprocal link.
    pub minimum_shared_neighbor_count: usize,
    /// Inclusive qualifying-neighbor count required for a core point.
    pub minimum_core_neighbor_count: usize,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum SnnPointRole {
    Core,
    Border,
    Noise,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SnnNeighborEvidence {
    pub ordinal: usize,
    /// One-based position in the owning point's nearest-neighbor list.
    pub rank: usize,
    pub angular_distance_radians: f64,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SnnLinkEvidence {
    pub left: usize,
    pub right: usize,
    pub angular_distance_radians: f64,
    /// Canonically ordered intersection of the two nearest-neighbor lists.
    pub shared_neighbors: Vec<usize>,
    pub shared_neighbor_count: usize,
    pub qualifies: bool,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SnnPointEvidence {
    pub ordinal: usize,
    pub nearest_neighbors: Vec<SnnNeighborEvidence>,
    /// Number of qualifying reciprocal SNN links incident to this point.
    pub density: usize,
    pub role: SnnPointRole,
    /// The core selected by the deterministic border-assignment extension.
    pub border_core_ordinal: Option<usize>,
    pub segment_index: Option<usize>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SnnSegment {
    pub segment_index: usize,
    pub members: Vec<usize>,
    pub core_members: Vec<usize>,
    pub border_members: Vec<usize>,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SnnSegmentation {
    pub config: SnnConfig,
    pub points: Vec<SnnPointEvidence>,
    /// Every reciprocal-neighbor link, including non-qualifying links.
    pub links: Vec<SnnLinkEvidence>,
    pub segments: Vec<SnnSegment>,
    pub noise: Vec<usize>,
}

/// Runs the final published shared-nearest-neighbor clustering contract.
pub fn snn_segmentation(cosines: &CosineMatrix, config: &SnnConfig) -> Result<SnnSegmentation> {
    validate_config(cosines.count(), config)?;

    let nearest_neighbors = exact_nearest_neighbors(cosines, config.neighbor_count)?;
    let ranks = neighbor_ranks(cosines.count(), &nearest_neighbors);
    let mut density = vec![0_usize; cosines.count()];
    let mut links = Vec::new();

    for left in 0..cosines.count() {
        for right in (left + 1)..cosines.count() {
            if ranks[left][right] == 0 || ranks[right][left] == 0 {
                continue;
            }

            let mut shared_neighbors = nearest_neighbors[left]
                .iter()
                .filter_map(|neighbor| {
                    (ranks[right][neighbor.ordinal] != 0).then_some(neighbor.ordinal)
                })
                .collect::<Vec<_>>();
            shared_neighbors.sort_unstable();
            let shared_neighbor_count = shared_neighbors.len();
            let qualifies = shared_neighbor_count >= config.minimum_shared_neighbor_count;
            if qualifies {
                density[left] += 1;
                density[right] += 1;
            }
            let angular_distance_radians = angular_distance(cosines.get(left, right)?);
            links.push(SnnLinkEvidence {
                left,
                right,
                angular_distance_radians,
                shared_neighbors,
                shared_neighbor_count,
                qualifies,
            });
        }
    }

    let is_core = density
        .iter()
        .map(|neighbor_count| *neighbor_count >= config.minimum_core_neighbor_count)
        .collect::<Vec<_>>();

    let mut components = DisjointSet::new(cosines.count());
    for link in &links {
        if link.qualifies && is_core[link.left] && is_core[link.right] {
            components.union(link.left, link.right);
        }
    }

    let mut cores_by_root = BTreeMap::<usize, Vec<usize>>::new();
    for (ordinal, core) in is_core.iter().copied().enumerate() {
        if core {
            let root = components.find(ordinal);
            cores_by_root.entry(root).or_default().push(ordinal);
        }
    }
    let mut core_groups = cores_by_root.into_values().collect::<Vec<_>>();
    core_groups.sort_by_key(|cores| cores[0]);
    let mut segments = core_groups
        .into_iter()
        .enumerate()
        .map(|(segment_index, core_members)| SnnSegment {
            segment_index,
            members: core_members.clone(),
            core_members,
            border_members: Vec::new(),
        })
        .collect::<Vec<_>>();
    let mut core_segment = vec![None; cosines.count()];
    for segment in &segments {
        for core in &segment.core_members {
            core_segment[*core] = Some(segment.segment_index);
        }
    }

    let mut roles = vec![SnnPointRole::Noise; cosines.count()];
    let mut border_core = vec![None; cosines.count()];
    let mut segment_by_point = vec![None; cosines.count()];
    for (ordinal, core) in is_core.iter().copied().enumerate() {
        if core {
            roles[ordinal] = SnnPointRole::Core;
            segment_by_point[ordinal] = core_segment[ordinal];
            continue;
        }

        let best_core = links
            .iter()
            .filter(|link| link.qualifies && (link.left == ordinal || link.right == ordinal))
            .filter_map(|link| {
                let other = if link.left == ordinal {
                    link.right
                } else {
                    link.left
                };
                is_core[other].then_some((
                    link.shared_neighbor_count,
                    link.angular_distance_radians,
                    other,
                ))
            })
            .max_by(|left, right| {
                left.0
                    .cmp(&right.0)
                    .then_with(|| right.1.total_cmp(&left.1))
                    .then_with(|| right.2.cmp(&left.2))
            });
        let Some((_, _, core_ordinal)) = best_core else {
            continue;
        };
        let segment_index = core_segment[core_ordinal].expect("every core has a segment");
        roles[ordinal] = SnnPointRole::Border;
        border_core[ordinal] = Some(core_ordinal);
        segment_by_point[ordinal] = Some(segment_index);
        segments[segment_index].members.push(ordinal);
        segments[segment_index].border_members.push(ordinal);
    }

    for segment in &mut segments {
        segment.members.sort_unstable();
        segment.border_members.sort_unstable();
    }
    let noise = roles
        .iter()
        .enumerate()
        .filter_map(|(ordinal, role)| (*role == SnnPointRole::Noise).then_some(ordinal))
        .collect::<Vec<_>>();
    let points = (0..cosines.count())
        .map(|ordinal| SnnPointEvidence {
            ordinal,
            nearest_neighbors: nearest_neighbors[ordinal].clone(),
            density: density[ordinal],
            role: roles[ordinal],
            border_core_ordinal: border_core[ordinal],
            segment_index: segment_by_point[ordinal],
        })
        .collect();

    Ok(SnnSegmentation {
        config: config.clone(),
        points,
        links,
        segments,
        noise,
    })
}

fn exact_nearest_neighbors(
    cosines: &CosineMatrix,
    neighbor_count: usize,
) -> Result<Vec<Vec<SnnNeighborEvidence>>> {
    (0..cosines.count())
        .map(|left| {
            let mut neighbors = (0..cosines.count())
                .filter(|right| *right != left)
                .map(|right| {
                    let angular_distance_radians = angular_distance(cosines.get(left, right)?);
                    Ok(SnnNeighborEvidence {
                        ordinal: right,
                        rank: 0,
                        angular_distance_radians,
                    })
                })
                .collect::<Result<Vec<_>>>()?;
            neighbors.sort_by(|left, right| {
                left.angular_distance_radians
                    .total_cmp(&right.angular_distance_radians)
                    .then_with(|| left.ordinal.cmp(&right.ordinal))
            });
            neighbors.truncate(neighbor_count);
            for (index, neighbor) in neighbors.iter_mut().enumerate() {
                neighbor.rank = index + 1;
            }
            Ok(neighbors)
        })
        .collect()
}

fn angular_distance(cosine: f64) -> f64 {
    let distance = cosine.acos();
    if distance == 0.0 { 0.0 } else { distance }
}

fn neighbor_ranks(count: usize, nearest_neighbors: &[Vec<SnnNeighborEvidence>]) -> Vec<Vec<usize>> {
    let mut ranks = vec![vec![0; count]; count];
    for (ordinal, neighbors) in nearest_neighbors.iter().enumerate() {
        for neighbor in neighbors {
            ranks[ordinal][neighbor.ordinal] = neighbor.rank;
        }
    }
    ranks
}

fn validate_config(count: usize, config: &SnnConfig) -> Result<()> {
    if config.neighbor_count < 2 {
        return Err(invalid("the SNN neighbor count must be at least 2"));
    }
    if config.neighbor_count >= count {
        return Err(invalid(
            "the SNN neighbor count must be smaller than the vector count",
        ));
    }
    if config.minimum_shared_neighbor_count == 0 {
        return Err(invalid(
            "the SNN minimum shared-neighbor count must be positive",
        ));
    }
    if config.minimum_shared_neighbor_count >= config.neighbor_count {
        return Err(invalid(
            "the SNN minimum shared-neighbor count must be at most k - 1",
        ));
    }
    if config.minimum_core_neighbor_count == 0 {
        return Err(invalid(
            "the SNN minimum core-neighbor count must be positive",
        ));
    }
    if config.minimum_core_neighbor_count > config.neighbor_count {
        return Err(invalid(
            "the SNN minimum core-neighbor count must be at most k",
        ));
    }
    Ok(())
}

fn invalid(message: impl Into<String>) -> SnnError {
    SnnError::Invariant(message.into())
}

struct DisjointSet {
    parents: Vec<usize>,
}

impl DisjointSet {
    fn new(count: usize) -> Self {
        Self {
            parents: (0..count).collect(),
        }
    }

    fn find(&mut self, ordinal: usize) -> usize {
        if self.parents[ordinal] != ordinal {
            self.parents[ordinal] = self.find(self.parents[ordinal]);
        }
        self.parents[ordinal]
    }

    fn union(&mut self, left: usize, right: usize) {
        let left_root = self.find(left);
        let right_root = self.find(right);
        if left_root == right_root {
            return;
        }
        let (keep, replace) = if left_root < right_root {
            (left_root, right_root)
        } else {
            (right_root, left_root)
        };
        self.parents[replace] = keep;
    }
}
