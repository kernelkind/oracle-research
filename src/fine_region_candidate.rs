//! Shared production boundary for fine-segmentation candidates.
//!
//! The adapter canonicalizes opaque-ID/vector inputs before either clustering
//! core observes an ordinal, collapses bitwise-identical vectors into alias
//! groups, and expands those aliases after selecting the core's fine output.
//! This keeps exact duplicate evidence from changing neighborhood geometry and
//! makes ordinal tie rules independent of arrival order.

use std::collections::{BTreeMap, BTreeSet};

use serde::{Deserialize, Serialize};
use thiserror::Error;

use crate::fine_region_hdbscan::{
    ClusterSelectionMethod, HdbscanConfig, HdbscanError, HdbscanResult, hdbscan,
};
use crate::fine_region_partition::{CosineMatrix, FineRegionPartitionError};
use crate::fine_region_snn::{SnnConfig, SnnError, SnnSegmentation, snn_segmentation};

pub const CANDIDATE_INPUT_CONTRACT_VERSION: &str = "opaque-id-order-bitwise-vector-alias-v1";
pub const SNN_FINE_OUTPUT_SELECTOR_VERSION: &str = "snn-segments-members-v1";
pub const HDBSCAN_FINE_OUTPUT_SELECTOR_VERSION: &str = "hdbscan-clusters-members-v1";

pub const SNN_CONTROLLED_SUITE_CONFIG_VERSION: &str = "snn-controlled-suite-config-v1";
pub const SNN_CONTROLLED_SUITE_CONFIG_JSON_V1: &str =
    r#"{"neighbor_count":5,"minimum_shared_neighbor_count":2,"minimum_core_neighbor_count":3}"#;
pub const SNN_CONTROLLED_SUITE_CONFIG_V1: SnnConfig = SnnConfig {
    neighbor_count: 5,
    minimum_shared_neighbor_count: 2,
    minimum_core_neighbor_count: 3,
};

pub const HDBSCAN_CONTROLLED_SUITE_CONFIG_VERSION: &str = "hdbscan-controlled-suite-config-v1";
pub const HDBSCAN_CONTROLLED_SUITE_CONFIG_JSON_V1: &str =
    r#"{"min_samples":2,"min_cluster_size":2,"selection_method":"excess_of_mass"}"#;
pub const HDBSCAN_CONTROLLED_SUITE_CONFIG_V1: HdbscanConfig = HdbscanConfig {
    min_samples: 2,
    min_cluster_size: 2,
    selection_method: ClusterSelectionMethod::ExcessOfMass,
};

pub type Result<T> = std::result::Result<T, FineRegionCandidateError>;

#[derive(Debug, Error)]
pub enum FineRegionCandidateError {
    #[error("fine-region candidate invariant failed: {0}")]
    Invariant(String),
    #[error(transparent)]
    CosineMatrix(#[from] FineRegionPartitionError),
    #[error(transparent)]
    Snn(#[from] SnnError),
    #[error(transparent)]
    Hdbscan(#[from] HdbscanError),
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct FineRegionCandidateInput {
    pub opaque_id: String,
    pub normalized_vector: Vec<f64>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct FineRegionCandidateOutput {
    /// Canonically ordered opaque-ID member sets selected as fine segments.
    pub segments: Vec<Vec<String>>,
    /// Canonically ordered opaque IDs not selected into any fine segment.
    pub unassigned: Vec<String>,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct FineRegionCandidateRun<AlgorithmResult> {
    pub input_contract_version: String,
    pub fine_output_selector_version: String,
    /// One representative ID per bitwise-distinct input vector, in the order
    /// supplied to the algorithm core.
    pub canonical_unique_ids: Vec<String>,
    /// Alias group at each corresponding canonical unique-vector ordinal.
    pub alias_groups: Vec<Vec<String>>,
    /// Complete production result over the unique-vector collection.
    pub algorithm_result: AlgorithmResult,
    pub fine_output: FineRegionCandidateOutput,
}

pub type SnnCandidateRun = FineRegionCandidateRun<SnnSegmentation>;
pub type HdbscanCandidateRun = FineRegionCandidateRun<HdbscanResult>;

pub fn run_snn_candidate(
    inputs: &[FineRegionCandidateInput],
    config: &SnnConfig,
) -> Result<SnnCandidateRun> {
    let canonical = canonicalize(inputs)?;
    let algorithm_result = snn_segmentation(&canonical.cosines, config)?;
    let selected_segments = algorithm_result
        .segments
        .iter()
        .map(|segment| segment.members.clone())
        .collect::<Vec<_>>();
    let fine_output = expand_output(
        &canonical.alias_groups,
        &selected_segments,
        &algorithm_result.noise,
    )?;

    Ok(FineRegionCandidateRun {
        input_contract_version: CANDIDATE_INPUT_CONTRACT_VERSION.to_owned(),
        fine_output_selector_version: SNN_FINE_OUTPUT_SELECTOR_VERSION.to_owned(),
        canonical_unique_ids: canonical.canonical_unique_ids,
        alias_groups: canonical.alias_groups,
        algorithm_result,
        fine_output,
    })
}

pub fn run_hdbscan_candidate(
    inputs: &[FineRegionCandidateInput],
    config: HdbscanConfig,
) -> Result<HdbscanCandidateRun> {
    let canonical = canonicalize(inputs)?;
    let algorithm_result = hdbscan(&canonical.cosines, config)?;
    let selected_segments = algorithm_result
        .clusters
        .iter()
        .map(|cluster| cluster.members.clone())
        .collect::<Vec<_>>();
    let fine_output = expand_output(
        &canonical.alias_groups,
        &selected_segments,
        &algorithm_result.noise,
    )?;

    Ok(FineRegionCandidateRun {
        input_contract_version: CANDIDATE_INPUT_CONTRACT_VERSION.to_owned(),
        fine_output_selector_version: HDBSCAN_FINE_OUTPUT_SELECTOR_VERSION.to_owned(),
        canonical_unique_ids: canonical.canonical_unique_ids,
        alias_groups: canonical.alias_groups,
        algorithm_result,
        fine_output,
    })
}

struct CanonicalInput {
    canonical_unique_ids: Vec<String>,
    alias_groups: Vec<Vec<String>>,
    cosines: CosineMatrix,
}

fn canonicalize(inputs: &[FineRegionCandidateInput]) -> Result<CanonicalInput> {
    let mut ordered = inputs.iter().collect::<Vec<_>>();
    for input in &ordered {
        validate_opaque_id(&input.opaque_id)?;
    }
    ordered.sort_by(|left, right| left.opaque_id.cmp(&right.opaque_id));
    if ordered
        .windows(2)
        .any(|pair| pair[0].opaque_id == pair[1].opaque_id)
    {
        return Err(invalid("opaque IDs must be unique"));
    }

    let mut group_by_vector = BTreeMap::<Vec<u64>, usize>::new();
    let mut canonical_unique_ids = Vec::new();
    let mut alias_groups = Vec::<Vec<String>>::new();
    let mut unique_vectors = Vec::new();
    for input in ordered {
        let vector_bits = input
            .normalized_vector
            .iter()
            .map(|coordinate| coordinate.to_bits())
            .collect::<Vec<_>>();
        if let Some(group) = group_by_vector.get(&vector_bits).copied() {
            alias_groups[group].push(input.opaque_id.clone());
            continue;
        }

        let group = unique_vectors.len();
        group_by_vector.insert(vector_bits, group);
        canonical_unique_ids.push(input.opaque_id.clone());
        alias_groups.push(vec![input.opaque_id.clone()]);
        unique_vectors.push(input.normalized_vector.clone());
    }
    let cosines = CosineMatrix::from_normalized_vectors(&unique_vectors)?;

    Ok(CanonicalInput {
        canonical_unique_ids,
        alias_groups,
        cosines,
    })
}

fn expand_output(
    alias_groups: &[Vec<String>],
    selected_segments: &[Vec<usize>],
    unassigned_ordinals: &[usize],
) -> Result<FineRegionCandidateOutput> {
    if selected_segments.iter().any(Vec::is_empty) {
        return Err(invalid(
            "the selected fine output contains an empty segment",
        ));
    }
    let mut segments = selected_segments
        .iter()
        .map(|segment| expand_ordinals(alias_groups, segment, "fine segment"))
        .collect::<Result<Vec<_>>>()?;
    segments.sort();
    if segments.windows(2).any(|pair| pair[0] == pair[1]) {
        return Err(invalid(
            "the selected fine output contains duplicate member sets",
        ));
    }

    let unassigned = expand_ordinals(alias_groups, unassigned_ordinals, "unassigned output")?;
    let assigned = segments.iter().flatten().collect::<BTreeSet<_>>();
    if unassigned.iter().any(|id| assigned.contains(id)) {
        return Err(invalid(
            "the selected fine output assigns an opaque ID and reports it as unassigned",
        ));
    }
    let all_ids = alias_groups.iter().flatten().collect::<BTreeSet<_>>();
    let covered_ids = assigned
        .into_iter()
        .chain(unassigned.iter())
        .collect::<BTreeSet<_>>();
    if covered_ids != all_ids {
        return Err(invalid(
            "the selected fine output does not account for every opaque ID",
        ));
    }
    Ok(FineRegionCandidateOutput {
        segments,
        unassigned,
    })
}

fn expand_ordinals(
    alias_groups: &[Vec<String>],
    ordinals: &[usize],
    name: &str,
) -> Result<Vec<String>> {
    let unique = ordinals.iter().copied().collect::<BTreeSet<_>>();
    if unique.len() != ordinals.len() {
        return Err(invalid(format!("{name} repeats a unique-vector ordinal")));
    }

    let mut expanded = Vec::new();
    for ordinal in ordinals {
        let aliases = alias_groups
            .get(*ordinal)
            .ok_or_else(|| invalid(format!("{name} contains an out-of-range ordinal")))?;
        expanded.extend(aliases.iter().cloned());
    }
    expanded.sort();
    Ok(expanded)
}

fn validate_opaque_id(value: &str) -> Result<()> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err(invalid(
            "opaque IDs must contain exactly 64 lowercase hexadecimal characters",
        ));
    }
    Ok(())
}

fn invalid(message: impl Into<String>) -> FineRegionCandidateError {
    FineRegionCandidateError::Invariant(message.into())
}
