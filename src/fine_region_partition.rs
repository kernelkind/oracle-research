//! Hard-partition baselines over normalized semantic vectors.

use std::cmp::Ordering;
use std::collections::{BTreeSet, BinaryHeap};

use rayon::prelude::*;
use serde::{Deserialize, Serialize};
use thiserror::Error;

const UNIT_NORM_TOLERANCE: f64 = 1.0e-5;
const CENTROID_NORM_TOLERANCE: f64 = 1.0e-12;
const MAX_DP_VMF_ITERATIONS: usize = 1_000;

pub type Result<T> = std::result::Result<T, FineRegionPartitionError>;

#[derive(Debug, Error)]
pub enum FineRegionPartitionError {
    #[error("fine-region partition invariant failed: {0}")]
    Invariant(String),
}

#[derive(Clone, Debug, PartialEq)]
pub struct CosineMatrix {
    count: usize,
    values: Vec<f64>,
}

impl CosineMatrix {
    pub fn from_normalized_vectors(vectors: &[Vec<f64>]) -> Result<Self> {
        let vectors = normalized_copy(vectors)?;

        let count = vectors.len();
        let mut values = vec![0.0; count * count];
        let results = values
            .par_chunks_mut(count)
            .enumerate()
            .map(|(left, row)| {
                row[left] = 1.0;
                for right in (left + 1)..count {
                    let cosine = vectors[left]
                        .iter()
                        .zip(vectors[right].iter())
                        .map(|(left, right)| left * right)
                        .sum::<f64>();
                    let cosine = normalize_cosine(cosine)?;
                    row[right] = cosine;
                }
                Ok(())
            })
            .collect::<Vec<Result<()>>>();
        for result in results {
            result?;
        }
        mirror_upper_triangle(&mut values, count);
        Ok(Self { count, values })
    }

    pub fn count(&self) -> usize {
        self.count
    }

    pub fn get(&self, left: usize, right: usize) -> Result<f64> {
        if left >= self.count || right >= self.count {
            return Err(invalid("cosine matrix index is out of bounds"));
        }
        Ok(self.values[left * self.count + right])
    }

    pub fn minimum_within(&self, members: &[usize]) -> Option<f64> {
        let mut minimum: Option<f64> = None;
        for (position, left) in members.iter().enumerate() {
            for right in &members[(position + 1)..] {
                if *left >= self.count || *right >= self.count {
                    return None;
                }
                let cosine = self.values[*left * self.count + *right];
                minimum = Some(minimum.map_or(cosine, |current| current.min(cosine)));
            }
        }
        minimum
    }
}

pub(crate) fn mirror_upper_triangle(values: &mut [f64], count: usize) {
    for left in 0..count {
        for right in left + 1..count {
            values[right * count + left] = values[left * count + right];
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RegionPartition {
    regions: Vec<Vec<usize>>,
}

impl RegionPartition {
    fn new(count: usize, mut regions: Vec<Vec<usize>>) -> Result<Self> {
        for region in &mut regions {
            region.sort_unstable();
            if region.is_empty() {
                return Err(invalid("a partition contains an empty region"));
            }
        }
        regions.sort();

        let mut members = regions.iter().flatten().copied().collect::<Vec<_>>();
        members.sort_unstable();
        if members != (0..count).collect::<Vec<_>>() {
            return Err(invalid(
                "a partition does not contain every vector exactly once",
            ));
        }
        Ok(Self { regions })
    }

    pub fn regions(&self) -> &[Vec<usize>] {
        &self.regions
    }
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ResolutionLevel {
    pub percentile: u8,
    pub pairwise_min_cosine: f64,
    pub pairwise_max_angle_degrees: f64,
    pub centroid_min_cosine: f64,
    pub centroid_max_angle_degrees: f64,
}

pub fn resolution_levels(
    cosines: &CosineMatrix,
    note_ids: &[String],
    percentiles: &[u8],
) -> Result<Vec<ResolutionLevel>> {
    if note_ids.len() != cosines.count {
        return Err(invalid(
            "the note-ID count does not match the cosine matrix",
        ));
    }
    if percentiles.is_empty()
        || percentiles
            .iter()
            .any(|percentile| *percentile == 0 || *percentile >= 100)
        || percentiles.windows(2).any(|pair| pair[0] >= pair[1])
    {
        return Err(invalid(
            "resolution percentiles must be unique, increasing, and between 1 and 99",
        ));
    }

    let mut cross_note_nearest = Vec::with_capacity(cosines.count);
    for left in 0..cosines.count {
        let nearest = (0..cosines.count)
            .filter(|right| note_ids[*right] != note_ids[left])
            .map(|right| cosines.values[left * cosines.count + right])
            .max_by(f64::total_cmp)
            .ok_or_else(|| invalid("a vector has no vector from another note"))?;
        cross_note_nearest.push(nearest);
    }
    cross_note_nearest.sort_by(f64::total_cmp);

    percentiles
        .iter()
        .map(|percentile| {
            let pairwise_min_cosine =
                linear_percentile(&cross_note_nearest, f64::from(*percentile) / 100.0);
            let pairwise_max_angle = pairwise_min_cosine.acos();
            Ok(ResolutionLevel {
                percentile: *percentile,
                pairwise_min_cosine,
                pairwise_max_angle_degrees: pairwise_max_angle.to_degrees(),
                centroid_min_cosine: pairwise_min_cosine,
                centroid_max_angle_degrees: pairwise_max_angle.to_degrees(),
            })
        })
        .collect()
}

pub fn complete_linkage_partition(
    cosines: &CosineMatrix,
    pairwise_min_cosine: f64,
) -> Result<RegionPartition> {
    validate_threshold(pairwise_min_cosine)?;
    let count = cosines.count;
    let mut similarities = Vec::with_capacity(count.saturating_mul(2).saturating_sub(1));
    let mut candidates = BinaryHeap::new();
    for right in 0..count {
        let mut row = Vec::with_capacity(right);
        for left in 0..right {
            let similarity = cosines.values[right * count + left];
            row.push(similarity);
            if similarity >= pairwise_min_cosine {
                candidates.push(LinkCandidate::new(similarity, left, right, left, right));
            }
        }
        similarities.push(row);
    }

    let mut members = (0..count).map(|ordinal| vec![ordinal]).collect::<Vec<_>>();
    let mut active = vec![true; count];
    while let Some(candidate) = candidates.pop() {
        if !active[candidate.left] || !active[candidate.right] {
            continue;
        }
        let left = candidate.left;
        let right = candidate.right;
        active[left] = false;
        active[right] = false;

        let mut merged = Vec::with_capacity(members[left].len() + members[right].len());
        merged.extend_from_slice(&members[left]);
        merged.extend_from_slice(&members[right]);
        merged.sort_unstable();
        let merged_id = members.len();
        let merged_first = merged[0];
        members.push(merged);
        active.push(true);

        let mut row = vec![f64::NAN; merged_id];
        for other in 0..merged_id {
            if !active[other] {
                continue;
            }
            let similarity = triangular_get(&similarities, left, other).min(triangular_get(
                &similarities,
                right,
                other,
            ));
            row[other] = similarity;
            if similarity >= pairwise_min_cosine {
                candidates.push(LinkCandidate::new(
                    similarity,
                    merged_id,
                    other,
                    merged_first,
                    members[other][0],
                ));
            }
        }
        similarities.push(row);
    }

    RegionPartition::new(
        count,
        active
            .iter()
            .enumerate()
            .filter(|(_, active)| **active)
            .map(|(id, _)| members[id].clone())
            .collect(),
    )
}

#[derive(Clone, Copy, Debug)]
struct LinkCandidate {
    similarity: f64,
    left: usize,
    right: usize,
    left_first: usize,
    right_first: usize,
}

impl LinkCandidate {
    fn new(
        similarity: f64,
        first_id: usize,
        second_id: usize,
        first_member: usize,
        second_member: usize,
    ) -> Self {
        if first_member < second_member {
            Self {
                similarity,
                left: first_id,
                right: second_id,
                left_first: first_member,
                right_first: second_member,
            }
        } else {
            Self {
                similarity,
                left: second_id,
                right: first_id,
                left_first: second_member,
                right_first: first_member,
            }
        }
    }
}

impl Eq for LinkCandidate {}

impl PartialEq for LinkCandidate {
    fn eq(&self, other: &Self) -> bool {
        self.cmp(other) == Ordering::Equal
    }
}

impl Ord for LinkCandidate {
    fn cmp(&self, other: &Self) -> Ordering {
        self.similarity
            .total_cmp(&other.similarity)
            .then_with(|| other.left_first.cmp(&self.left_first))
            .then_with(|| other.right_first.cmp(&self.right_first))
    }
}

impl PartialOrd for LinkCandidate {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

fn triangular_get(similarities: &[Vec<f64>], left: usize, right: usize) -> f64 {
    if left > right {
        similarities[left][right]
    } else {
        similarities[right][left]
    }
}

pub fn dp_vmf_partition(
    vectors: &[Vec<f64>],
    centroid_min_cosine: f64,
    order: &[usize],
) -> Result<RegionPartition> {
    validate_threshold(centroid_min_cosine)?;
    let vectors = normalized_copy(vectors)?;
    validate_order(vectors.len(), order)?;

    let mut labels = vec![usize::MAX; vectors.len()];
    let mut centroids = Vec::<Vec<f64>>::new();
    for ordinal in order {
        labels[*ordinal] =
            best_or_new_region(&vectors[*ordinal], &mut centroids, centroid_min_cosine);
    }
    canonicalize_labels(&mut labels);

    let mut seen = BTreeSet::new();
    seen.insert(labels.clone());
    for _ in 0..MAX_DP_VMF_ITERATIONS {
        centroids = normalized_centroids(&vectors, &labels)?;
        let mut next = labels.clone();
        let mut counts = label_counts(&next);
        let mut active = vec![true; centroids.len()];

        for ordinal in order {
            let old = next[*ordinal];
            if counts[old] == 1 {
                active[old] = false;
            }

            let mut best: Option<(f64, usize)> = None;
            for (region, centroid) in centroids.iter().enumerate() {
                if !active[region] {
                    continue;
                }
                let similarity = dot(&vectors[*ordinal], centroid);
                if best.is_none_or(|(current, current_region)| {
                    similarity > current || (similarity == current && region < current_region)
                }) {
                    best = Some((similarity, region));
                }
            }

            let assigned = match best {
                Some((similarity, region)) if similarity >= centroid_min_cosine => region,
                _ => {
                    centroids.push(vectors[*ordinal].clone());
                    active.push(true);
                    counts.push(0);
                    centroids.len() - 1
                }
            };

            if counts[old] == 1 {
                counts[old] = 0;
            } else {
                counts[old] -= 1;
            }
            next[*ordinal] = assigned;
            counts[assigned] += 1;
            active[assigned] = true;
        }

        canonicalize_labels(&mut next);
        if next == labels {
            return labels_to_partition(next);
        }
        if !seen.insert(next.clone()) {
            return Err(invalid("DP-vMF assignments entered a cycle"));
        }
        labels = next;
    }
    Err(invalid("DP-vMF did not converge"))
}

fn best_or_new_region(vector: &[f64], centroids: &mut Vec<Vec<f64>>, threshold: f64) -> usize {
    let best = centroids
        .iter()
        .enumerate()
        .map(|(region, centroid)| (dot(vector, centroid), region))
        .max_by(|left, right| {
            left.0
                .total_cmp(&right.0)
                .then_with(|| right.1.cmp(&left.1))
        });
    match best {
        Some((similarity, region)) if similarity >= threshold => region,
        _ => {
            centroids.push(vector.to_vec());
            centroids.len() - 1
        }
    }
}

fn normalized_centroids(vectors: &[Vec<f64>], labels: &[usize]) -> Result<Vec<Vec<f64>>> {
    let region_count = labels
        .iter()
        .copied()
        .max()
        .map_or(0, |maximum| maximum + 1);
    let dimensions = vectors[0].len();
    let mut sums = vec![vec![0.0; dimensions]; region_count];
    for (vector, label) in vectors.iter().zip(labels.iter()) {
        for (sum, coordinate) in sums[*label].iter_mut().zip(vector.iter()) {
            *sum += coordinate;
        }
    }
    for (region, sum) in sums.iter_mut().enumerate() {
        let norm = sum.iter().map(|value| value * value).sum::<f64>().sqrt();
        if !norm.is_finite() || norm <= CENTROID_NORM_TOLERANCE {
            return Err(invalid(format!(
                "DP-vMF region {region} has an invalid centroid"
            )));
        }
        for coordinate in sum {
            *coordinate /= norm;
        }
    }
    Ok(sums)
}

fn label_counts(labels: &[usize]) -> Vec<usize> {
    let mut counts = vec![
        0;
        labels
            .iter()
            .copied()
            .max()
            .map_or(0, |maximum| maximum + 1)
    ];
    for label in labels {
        counts[*label] += 1;
    }
    counts
}

fn canonicalize_labels(labels: &mut [usize]) {
    let mut regions = Vec::<Vec<usize>>::new();
    for (ordinal, label) in labels.iter().copied().enumerate() {
        if label >= regions.len() {
            regions.resize_with(label + 1, Vec::new);
        }
        regions[label].push(ordinal);
    }
    regions.retain(|region| !region.is_empty());
    regions.sort();
    for (label, region) in regions.iter().enumerate() {
        for ordinal in region {
            labels[*ordinal] = label;
        }
    }
}

fn labels_to_partition(labels: Vec<usize>) -> Result<RegionPartition> {
    let mut regions = vec![Vec::new(); labels.iter().copied().max().map_or(0, |value| value + 1)];
    for (ordinal, label) in labels.iter().enumerate() {
        regions[*label].push(ordinal);
    }
    RegionPartition::new(labels.len(), regions)
}

fn validate_order(count: usize, order: &[usize]) -> Result<()> {
    let mut sorted = order.to_vec();
    sorted.sort_unstable();
    if sorted != (0..count).collect::<Vec<_>>() {
        return Err(invalid(
            "DP-vMF order must contain every vector exactly once",
        ));
    }
    Ok(())
}

fn normalized_copy(vectors: &[Vec<f64>]) -> Result<Vec<Vec<f64>>> {
    let dimensions = vectors
        .first()
        .map(Vec::len)
        .ok_or_else(|| invalid("the vector collection is empty"))?;
    if dimensions == 0 {
        return Err(invalid("vectors have zero dimensions"));
    }
    let mut normalized = Vec::with_capacity(vectors.len());
    for (ordinal, vector) in vectors.iter().enumerate() {
        if vector.len() != dimensions || vector.iter().any(|value| !value.is_finite()) {
            return Err(invalid(format!(
                "vector {ordinal} has invalid dimensions or a non-finite coordinate"
            )));
        }
        let norm = vector.iter().map(|value| value * value).sum::<f64>().sqrt();
        if (norm - 1.0).abs() > UNIT_NORM_TOLERANCE {
            return Err(invalid(format!(
                "vector {ordinal} is not unit normalized: norm {norm}"
            )));
        }
        normalized.push(vector.iter().map(|coordinate| coordinate / norm).collect());
    }
    Ok(normalized)
}

fn validate_threshold(value: f64) -> Result<()> {
    if !value.is_finite() || !(-1.0..=1.0).contains(&value) {
        return Err(invalid("a cosine threshold is not between -1 and 1"));
    }
    Ok(())
}

fn linear_percentile(sorted: &[f64], quantile: f64) -> f64 {
    let position = (sorted.len() - 1) as f64 * quantile;
    let lower = position.floor() as usize;
    let upper = position.ceil() as usize;
    sorted[lower] + (sorted[upper] - sorted[lower]) * (position - lower as f64)
}

fn dot(left: &[f64], right: &[f64]) -> f64 {
    left.iter()
        .zip(right.iter())
        .map(|(left, right)| left * right)
        .sum()
}

fn normalize_cosine(value: f64) -> Result<f64> {
    if !value.is_finite()
        || !(-1.0 - UNIT_NORM_TOLERANCE..=1.0 + UNIT_NORM_TOLERANCE).contains(&value)
    {
        return Err(invalid("a vector pair produced an invalid cosine"));
    }
    Ok(value.clamp(-1.0, 1.0))
}

fn invalid(message: impl Into<String>) -> FineRegionPartitionError {
    FineRegionPartitionError::Invariant(message.into())
}
