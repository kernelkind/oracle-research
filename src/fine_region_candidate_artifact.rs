//! Reproducible in-memory artifacts for fine-segmentation candidates.
//!
//! [`crate::fine_region_candidate`] is the only algorithm-execution boundary.
//! This module binds that adapter's canonical input, complete production run,
//! implementation sources, exact parameters, and deterministic contracts into
//! a verifiable artifact. Verification reconstructs the artifact by rerunning
//! the adapter; it does not trust hashes stored in the retained artifact.

use std::collections::BTreeMap;

use serde::{Deserialize, Serialize};
use thiserror::Error;

use crate::artifact::hash_bytes;
use crate::fine_region_candidate::{
    CANDIDATE_INPUT_CONTRACT_VERSION, FineRegionCandidateError, FineRegionCandidateInput,
    FineRegionCandidateOutput, FineRegionCandidateRun,
    HDBSCAN_CROSS_NOTE_CORE_DISTANCE_RULE_VERSION, HDBSCAN_CROSS_NOTE_EDGE_RULE_VERSION,
    HDBSCAN_FINE_OUTPUT_SELECTOR_VERSION, HdbscanCandidateRun, SNN_FINE_OUTPUT_SELECTOR_VERSION,
    SnnCandidateRun, run_hdbscan_candidate, run_hdbscan_cross_note_candidate,
    run_hdbscan_cross_note_edges_candidate, run_snn_candidate,
};
use crate::fine_region_hdbscan::{CondensedTreeEdge, HdbscanCluster, HdbscanConfig};
use crate::fine_region_snn::SnnConfig;

const CANDIDATE_ADAPTER_SOURCE: &[u8] = include_bytes!("fine_region_candidate.rs");
const PREPROCESSING_SOURCE: &[u8] = include_bytes!("fine_region_partition.rs");
const SNN_SOURCE: &[u8] = include_bytes!("fine_region_snn.rs");
const HDBSCAN_SOURCE: &[u8] = include_bytes!("fine_region_hdbscan.rs");

pub const CANDIDATE_ARTIFACT_SCHEMA_VERSION: u32 = 4;
pub const SNN_ALGORITHM_VERSION: &str = "snn-sdm-2003-exact-angular-v1";
pub const HDBSCAN_ALGORITHM_VERSION: &str = "hdbscan-star-exact-angular-v1";
pub const HDBSCAN_CROSS_NOTE_ALGORITHM_VERSION: &str = "hdbscan-star-cross-note-exact-angular-v1";
pub const HDBSCAN_CROSS_NOTE_EDGES_ALGORITHM_VERSION: &str =
    "hdbscan-star-cross-note-edges-exact-angular-v1";

/// SNN ties use lower canonical input ordinals in exact angular-neighbor
/// ordering. An ambiguous border point chooses the qualifying core link with
/// the greatest shared-neighbor count, then the smallest angular distance,
/// then the lowest canonical ordinal. Border points never connect core
/// components.
pub const SNN_TIE_RULE_VERSION: &str = "snn-angular-ordinal-border-v1";

/// HDBSCAN* MST ties use source then target canonical ordinal, all
/// equal-distance splits are condensed simultaneously, EOM selects the parent
/// on equal stability, and public clusters use member ordinals then cluster ID.
pub const HDBSCAN_TIE_RULE_VERSION: &str = "hdbscan-angular-ordinal-equal-tier-v1";

#[derive(Clone, Copy)]
struct AlgorithmContract {
    version: &'static str,
    tie_rule_version: &'static str,
    fine_output_selector_version: &'static str,
    implementation_source: &'static [u8],
    cross_note_core_distance_rule_version: Option<&'static str>,
    cross_note_edge_rule_version: Option<&'static str>,
}

const SNN_CONTRACT: AlgorithmContract = AlgorithmContract {
    version: SNN_ALGORITHM_VERSION,
    tie_rule_version: SNN_TIE_RULE_VERSION,
    fine_output_selector_version: SNN_FINE_OUTPUT_SELECTOR_VERSION,
    implementation_source: SNN_SOURCE,
    cross_note_core_distance_rule_version: None,
    cross_note_edge_rule_version: None,
};

const HDBSCAN_CONTRACT: AlgorithmContract = AlgorithmContract {
    version: HDBSCAN_ALGORITHM_VERSION,
    tie_rule_version: HDBSCAN_TIE_RULE_VERSION,
    fine_output_selector_version: HDBSCAN_FINE_OUTPUT_SELECTOR_VERSION,
    implementation_source: HDBSCAN_SOURCE,
    cross_note_core_distance_rule_version: None,
    cross_note_edge_rule_version: None,
};

const HDBSCAN_CROSS_NOTE_CONTRACT: AlgorithmContract = AlgorithmContract {
    version: HDBSCAN_CROSS_NOTE_ALGORITHM_VERSION,
    cross_note_core_distance_rule_version: Some(HDBSCAN_CROSS_NOTE_CORE_DISTANCE_RULE_VERSION),
    ..HDBSCAN_CONTRACT
};

const HDBSCAN_CROSS_NOTE_EDGES_CONTRACT: AlgorithmContract = AlgorithmContract {
    version: HDBSCAN_CROSS_NOTE_EDGES_ALGORITHM_VERSION,
    cross_note_edge_rule_version: Some(HDBSCAN_CROSS_NOTE_EDGE_RULE_VERSION),
    ..HDBSCAN_CROSS_NOTE_CONTRACT
};

pub type Result<T> = std::result::Result<T, CandidateArtifactError>;

#[derive(Debug, Error)]
pub enum CandidateArtifactError {
    #[error("fine-region candidate artifact invariant failed: {0}")]
    Invariant(String),
    #[error(transparent)]
    Candidate(#[from] FineRegionCandidateError),
    #[error("fine-region candidate artifact serialization failed: {0}")]
    Serialization(#[from] serde_json::Error),
}

/// Extra binding required only for source-note-aware core distances. The map
/// remains external evidence, like the normalized vectors, and verification
/// requires its complete contents instead of trusting this retained digest.
#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CrossNoteCandidateMetadata {
    pub core_distance_rule_version: String,
    /// SHA-256 of compact JSON encoding of the opaque-ID-sorted source map.
    pub source_note_ids_sha256: String,
    /// Omitted for the original complete-graph cross-note-core candidate.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub edge_rule_version: Option<String>,
}

/// Integrity and reproducibility metadata shared by the candidate algorithms.
#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CandidateArtifactManifest<Parameters> {
    pub schema_version: u32,
    pub algorithm_version: String,
    pub input_contract_version: String,
    pub fine_output_selector_version: String,
    /// SHA-256 of the exact shared adapter module compiled into this build.
    pub adapter_implementation_source_sha256: String,
    /// SHA-256 of the exact algorithm core compiled into this build.
    pub algorithm_implementation_source_sha256: String,
    /// SHA-256 of the exact normalization and cosine implementation compiled
    /// into this build.
    pub preprocessing_implementation_source_sha256: String,
    pub source_vector_manifest_sha256: String,
    pub normalized_vector_sha256: String,
    /// SHA-256 over canonical opaque IDs and each coordinate's IEEE-754 bits.
    pub canonical_input_sha256: String,
    pub vector_count: usize,
    pub unique_vector_count: usize,
    pub parameters: Parameters,
    /// SHA-256 of the exact canonical configuration JSON bytes.
    pub configuration_sha256: String,
    pub tie_rule_version: String,
    /// SHA-256 of the compact JSON encoding of the complete adapter run.
    pub result_sha256: String,
    /// SHA-256 of the exact canonical selected-output JSON bytes.
    pub fine_output_sha256: String,
    /// Omitted entirely for standard SNN and HDBSCAN* artifacts.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub cross_note: Option<CrossNoteCandidateMetadata>,
}

/// A complete adapter result plus the canonical input identities and manifest
/// that bind it.
#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CandidateArtifact<Parameters, CandidateRun> {
    pub manifest: CandidateArtifactManifest<Parameters>,
    pub canonical_input_ids: Vec<String>,
    /// Exact compact UTF-8 JSON for the algorithm configuration, with no
    /// trailing newline.
    pub canonical_configuration_json: String,
    /// Exact compact UTF-8 JSON selected for semantic scoring, with no
    /// trailing newline.
    pub canonical_fine_output_json: String,
    pub result: CandidateRun,
}

pub type SnnCandidateArtifact = CandidateArtifact<SnnConfig, SnnCandidateRun>;
pub type HdbscanCandidateArtifact = CandidateArtifact<HdbscanConfig, HdbscanCandidateRun>;
pub type HdbscanCrossNoteCandidateArtifact = CandidateArtifact<HdbscanConfig, HdbscanCandidateRun>;

/// Numerical fields consumed by recursive hierarchy construction. Dense distance
/// tables remain working memory rather than part of the serialized result.
#[derive(Debug, Serialize)]
pub struct HdbscanHierarchyResult {
    pub vector_count: usize,
    pub clusters: Vec<HdbscanCluster>,
    pub condensed_tree: Vec<CondensedTreeEdge>,
}

pub fn build_hdbscan_hierarchy_artifact(
    inputs: &[FineRegionCandidateInput],
    source_vector_manifest_sha256: &str,
    normalized_vector_sha256: &str,
    config: &HdbscanConfig,
) -> Result<CandidateArtifact<HdbscanConfig, FineRegionCandidateRun<HdbscanHierarchyResult>>> {
    validate_source_hashes(source_vector_manifest_sha256, normalized_vector_sha256)?;
    let run = run_hdbscan_candidate(inputs, *config)?;
    let result = FineRegionCandidateRun {
        algorithm_result: HdbscanHierarchyResult {
            vector_count: run.canonical_unique_ids.len(),
            clusters: run.algorithm_result.clusters,
            condensed_tree: run.algorithm_result.condensed_tree,
        },
        input_contract_version: run.input_contract_version,
        fine_output_selector_version: run.fine_output_selector_version,
        canonical_unique_ids: run.canonical_unique_ids,
        alias_groups: run.alias_groups,
        fine_output: run.fine_output,
    };
    assemble_artifact(
        inputs,
        source_vector_manifest_sha256,
        normalized_vector_sha256,
        *config,
        result,
        HDBSCAN_CONTRACT,
    )
}

pub fn build_snn_candidate_artifact(
    inputs: &[FineRegionCandidateInput],
    source_vector_manifest_sha256: &str,
    normalized_vector_sha256: &str,
    config: &SnnConfig,
) -> Result<SnnCandidateArtifact> {
    validate_source_hashes(source_vector_manifest_sha256, normalized_vector_sha256)?;
    let result = run_snn_candidate(inputs, config)?;
    assemble_artifact(
        inputs,
        source_vector_manifest_sha256,
        normalized_vector_sha256,
        config.clone(),
        result,
        SNN_CONTRACT,
    )
}

pub fn verify_snn_candidate_artifact(
    artifact: &SnnCandidateArtifact,
    inputs: &[FineRegionCandidateInput],
    source_vector_manifest_sha256: &str,
    normalized_vector_sha256: &str,
    config: &SnnConfig,
) -> Result<()> {
    validate_retained_artifact(artifact, SNN_CONTRACT)?;
    if artifact.manifest.parameters != artifact.result.algorithm_result.config {
        return Err(invalid(
            "SNN manifest parameters differ from the retained production result",
        ));
    }
    let expected = build_snn_candidate_artifact(
        inputs,
        source_vector_manifest_sha256,
        normalized_vector_sha256,
        config,
    )?;
    require_recomputed_match(artifact, &expected)
}

pub fn build_hdbscan_candidate_artifact(
    inputs: &[FineRegionCandidateInput],
    source_vector_manifest_sha256: &str,
    normalized_vector_sha256: &str,
    config: &HdbscanConfig,
) -> Result<HdbscanCandidateArtifact> {
    validate_source_hashes(source_vector_manifest_sha256, normalized_vector_sha256)?;
    let result = run_hdbscan_candidate(inputs, *config)?;
    assemble_artifact(
        inputs,
        source_vector_manifest_sha256,
        normalized_vector_sha256,
        *config,
        result,
        HDBSCAN_CONTRACT,
    )
}

pub fn verify_hdbscan_candidate_artifact(
    artifact: &HdbscanCandidateArtifact,
    inputs: &[FineRegionCandidateInput],
    source_vector_manifest_sha256: &str,
    normalized_vector_sha256: &str,
    config: &HdbscanConfig,
) -> Result<()> {
    validate_retained_artifact(artifact, HDBSCAN_CONTRACT)?;
    if artifact.manifest.parameters != artifact.result.algorithm_result.config {
        return Err(invalid(
            "HDBSCAN* manifest parameters differ from the retained production result",
        ));
    }
    let expected = build_hdbscan_candidate_artifact(
        inputs,
        source_vector_manifest_sha256,
        normalized_vector_sha256,
        config,
    )?;
    require_recomputed_match(artifact, &expected)
}

pub fn build_hdbscan_cross_note_candidate_artifact(
    inputs: &[FineRegionCandidateInput],
    source_note_ids: &BTreeMap<String, String>,
    source_vector_manifest_sha256: &str,
    normalized_vector_sha256: &str,
    config: &HdbscanConfig,
) -> Result<HdbscanCrossNoteCandidateArtifact> {
    build_cross_note_artifact(
        inputs,
        source_note_ids,
        source_vector_manifest_sha256,
        normalized_vector_sha256,
        config,
        HDBSCAN_CROSS_NOTE_CONTRACT,
    )
}

pub fn build_hdbscan_cross_note_edges_candidate_artifact(
    inputs: &[FineRegionCandidateInput],
    source_note_ids: &BTreeMap<String, String>,
    source_vector_manifest_sha256: &str,
    normalized_vector_sha256: &str,
    config: &HdbscanConfig,
) -> Result<HdbscanCrossNoteCandidateArtifact> {
    build_cross_note_artifact(
        inputs,
        source_note_ids,
        source_vector_manifest_sha256,
        normalized_vector_sha256,
        config,
        HDBSCAN_CROSS_NOTE_EDGES_CONTRACT,
    )
}

fn build_cross_note_artifact(
    inputs: &[FineRegionCandidateInput],
    source_note_ids: &BTreeMap<String, String>,
    source_vector_manifest_sha256: &str,
    normalized_vector_sha256: &str,
    config: &HdbscanConfig,
    contract: AlgorithmContract,
) -> Result<HdbscanCrossNoteCandidateArtifact> {
    validate_source_hashes(source_vector_manifest_sha256, normalized_vector_sha256)?;
    let result = if contract.cross_note_edge_rule_version.is_some() {
        run_hdbscan_cross_note_edges_candidate(inputs, source_note_ids, *config)?
    } else {
        run_hdbscan_cross_note_candidate(inputs, source_note_ids, *config)?
    };
    let mut artifact = assemble_artifact(
        inputs,
        source_vector_manifest_sha256,
        normalized_vector_sha256,
        *config,
        result,
        contract,
    )?;
    artifact.manifest.cross_note = Some(CrossNoteCandidateMetadata {
        core_distance_rule_version: HDBSCAN_CROSS_NOTE_CORE_DISTANCE_RULE_VERSION.to_owned(),
        source_note_ids_sha256: hash_serialized(source_note_ids)?,
        edge_rule_version: contract.cross_note_edge_rule_version.map(str::to_owned),
    });
    Ok(artifact)
}

pub fn verify_hdbscan_cross_note_candidate_artifact(
    artifact: &HdbscanCrossNoteCandidateArtifact,
    inputs: &[FineRegionCandidateInput],
    source_note_ids: &BTreeMap<String, String>,
    source_vector_manifest_sha256: &str,
    normalized_vector_sha256: &str,
    config: &HdbscanConfig,
) -> Result<()> {
    verify_cross_note_artifact(
        artifact,
        inputs,
        source_note_ids,
        source_vector_manifest_sha256,
        normalized_vector_sha256,
        config,
        HDBSCAN_CROSS_NOTE_CONTRACT,
    )
}

pub fn verify_hdbscan_cross_note_edges_candidate_artifact(
    artifact: &HdbscanCrossNoteCandidateArtifact,
    inputs: &[FineRegionCandidateInput],
    source_note_ids: &BTreeMap<String, String>,
    source_vector_manifest_sha256: &str,
    normalized_vector_sha256: &str,
    config: &HdbscanConfig,
) -> Result<()> {
    verify_cross_note_artifact(
        artifact,
        inputs,
        source_note_ids,
        source_vector_manifest_sha256,
        normalized_vector_sha256,
        config,
        HDBSCAN_CROSS_NOTE_EDGES_CONTRACT,
    )
}

fn verify_cross_note_artifact(
    artifact: &HdbscanCrossNoteCandidateArtifact,
    inputs: &[FineRegionCandidateInput],
    source_note_ids: &BTreeMap<String, String>,
    source_vector_manifest_sha256: &str,
    normalized_vector_sha256: &str,
    config: &HdbscanConfig,
    contract: AlgorithmContract,
) -> Result<()> {
    validate_retained_artifact(artifact, contract)?;
    if artifact.manifest.parameters != artifact.result.algorithm_result.config {
        return Err(invalid(
            "HDBSCAN* manifest parameters differ from the retained production result",
        ));
    }
    let expected = build_cross_note_artifact(
        inputs,
        source_note_ids,
        source_vector_manifest_sha256,
        normalized_vector_sha256,
        config,
        contract,
    )?;
    require_recomputed_match(artifact, &expected)
}

fn assemble_artifact<Parameters, CandidateRun>(
    inputs: &[FineRegionCandidateInput],
    source_vector_manifest_sha256: &str,
    normalized_vector_sha256: &str,
    parameters: Parameters,
    result: CandidateRun,
    contract: AlgorithmContract,
) -> Result<CandidateArtifact<Parameters, CandidateRun>>
where
    Parameters: Serialize,
    CandidateRun: CandidateRunContract + Serialize,
{
    let mut canonical_inputs = inputs.iter().collect::<Vec<_>>();
    canonical_inputs.sort_by(|left, right| left.opaque_id.cmp(&right.opaque_id));
    let canonical_input_ids = canonical_inputs
        .iter()
        .map(|input| input.opaque_id.clone())
        .collect::<Vec<_>>();
    let canonical_configuration_json = serde_json::to_string(&parameters)?;
    let canonical_fine_output_json =
        serde_json::to_string(result.fine_output()).map_err(CandidateArtifactError::from)?;
    let manifest = CandidateArtifactManifest {
        schema_version: CANDIDATE_ARTIFACT_SCHEMA_VERSION,
        algorithm_version: contract.version.to_owned(),
        input_contract_version: CANDIDATE_INPUT_CONTRACT_VERSION.to_owned(),
        fine_output_selector_version: contract.fine_output_selector_version.to_owned(),
        adapter_implementation_source_sha256: hash_bytes(CANDIDATE_ADAPTER_SOURCE),
        algorithm_implementation_source_sha256: hash_bytes(contract.implementation_source),
        preprocessing_implementation_source_sha256: hash_bytes(PREPROCESSING_SOURCE),
        source_vector_manifest_sha256: source_vector_manifest_sha256.to_owned(),
        normalized_vector_sha256: normalized_vector_sha256.to_owned(),
        canonical_input_sha256: hash_canonical_inputs(&canonical_inputs),
        vector_count: inputs.len(),
        unique_vector_count: result.unique_vector_count(),
        parameters,
        configuration_sha256: hash_bytes(canonical_configuration_json.as_bytes()),
        tie_rule_version: contract.tie_rule_version.to_owned(),
        result_sha256: hash_serialized(&result)?,
        fine_output_sha256: hash_bytes(canonical_fine_output_json.as_bytes()),
        cross_note: None,
    };
    Ok(CandidateArtifact {
        manifest,
        canonical_input_ids,
        canonical_configuration_json,
        canonical_fine_output_json,
        result,
    })
}

trait CandidateRunContract {
    fn input_contract_version(&self) -> &str;
    fn fine_output_selector_version(&self) -> &str;
    fn canonical_unique_ids(&self) -> &[String];
    fn alias_groups(&self) -> &[Vec<String>];
    fn fine_output(&self) -> &FineRegionCandidateOutput;

    fn unique_vector_count(&self) -> usize {
        self.canonical_unique_ids().len()
    }
}

impl<AlgorithmResult> CandidateRunContract for FineRegionCandidateRun<AlgorithmResult> {
    fn input_contract_version(&self) -> &str {
        &self.input_contract_version
    }

    fn fine_output_selector_version(&self) -> &str {
        &self.fine_output_selector_version
    }

    fn canonical_unique_ids(&self) -> &[String] {
        &self.canonical_unique_ids
    }

    fn alias_groups(&self) -> &[Vec<String>] {
        &self.alias_groups
    }

    fn fine_output(&self) -> &FineRegionCandidateOutput {
        &self.fine_output
    }
}

fn validate_retained_artifact<Parameters, CandidateRun>(
    artifact: &CandidateArtifact<Parameters, CandidateRun>,
    contract: AlgorithmContract,
) -> Result<()>
where
    Parameters: Serialize,
    CandidateRun: CandidateRunContract + Serialize,
{
    validate_canonical_ids(&artifact.canonical_input_ids)?;
    match (
        &artifact.manifest.cross_note,
        contract.cross_note_core_distance_rule_version,
    ) {
        (None, None) => {}
        (Some(metadata), Some(rule))
            if metadata.core_distance_rule_version == rule
                && metadata.edge_rule_version.as_deref()
                    == contract.cross_note_edge_rule_version =>
        {
            validate_sha256("source-note-IDs SHA-256", &metadata.source_note_ids_sha256)?;
        }
        _ => {
            return Err(invalid(
                "retained cross-note metadata does not match the candidate algorithm",
            ));
        }
    }
    for (name, value) in [
        (
            "adapter-implementation-source SHA-256",
            artifact
                .manifest
                .adapter_implementation_source_sha256
                .as_str(),
        ),
        (
            "algorithm-implementation-source SHA-256",
            artifact
                .manifest
                .algorithm_implementation_source_sha256
                .as_str(),
        ),
        (
            "preprocessing-implementation-source SHA-256",
            artifact
                .manifest
                .preprocessing_implementation_source_sha256
                .as_str(),
        ),
        (
            "source vector-manifest SHA-256",
            artifact.manifest.source_vector_manifest_sha256.as_str(),
        ),
        (
            "normalized-vector SHA-256",
            artifact.manifest.normalized_vector_sha256.as_str(),
        ),
        (
            "canonical-input SHA-256",
            artifact.manifest.canonical_input_sha256.as_str(),
        ),
        (
            "configuration SHA-256",
            artifact.manifest.configuration_sha256.as_str(),
        ),
        ("result SHA-256", artifact.manifest.result_sha256.as_str()),
        (
            "fine-output SHA-256",
            artifact.manifest.fine_output_sha256.as_str(),
        ),
    ] {
        validate_sha256(name, value)?;
    }

    let mut result_ids = artifact
        .result
        .alias_groups()
        .iter()
        .flatten()
        .cloned()
        .collect::<Vec<_>>();
    result_ids.sort();
    if result_ids != artifact.canonical_input_ids
        || artifact.result.alias_groups().len() != artifact.result.canonical_unique_ids().len()
        || artifact
            .result
            .alias_groups()
            .iter()
            .zip(artifact.result.canonical_unique_ids())
            .any(|(aliases, representative)| aliases.first() != Some(representative))
    {
        return Err(invalid(
            "retained alias groups do not match the canonical input identities",
        ));
    }

    if artifact.manifest.schema_version != CANDIDATE_ARTIFACT_SCHEMA_VERSION
        || artifact.manifest.algorithm_version != contract.version
        || artifact.manifest.input_contract_version != CANDIDATE_INPUT_CONTRACT_VERSION
        || artifact.manifest.fine_output_selector_version != contract.fine_output_selector_version
        || artifact.result.input_contract_version() != CANDIDATE_INPUT_CONTRACT_VERSION
        || artifact.result.fine_output_selector_version() != contract.fine_output_selector_version
        || artifact.manifest.tie_rule_version != contract.tie_rule_version
        || artifact.manifest.vector_count != artifact.canonical_input_ids.len()
        || artifact.manifest.unique_vector_count != artifact.result.unique_vector_count()
        || artifact.canonical_configuration_json
            != serde_json::to_string(&artifact.manifest.parameters)?
        || artifact.manifest.configuration_sha256
            != hash_bytes(artifact.canonical_configuration_json.as_bytes())
        || artifact.manifest.adapter_implementation_source_sha256
            != hash_bytes(CANDIDATE_ADAPTER_SOURCE)
        || artifact.manifest.algorithm_implementation_source_sha256
            != hash_bytes(contract.implementation_source)
        || artifact.manifest.preprocessing_implementation_source_sha256
            != hash_bytes(PREPROCESSING_SOURCE)
        || artifact.manifest.result_sha256 != hash_serialized(&artifact.result)?
        || artifact.canonical_fine_output_json
            != serde_json::to_string(artifact.result.fine_output())?
        || artifact.manifest.fine_output_sha256
            != hash_bytes(artifact.canonical_fine_output_json.as_bytes())
    {
        return Err(invalid(
            "retained artifact metadata does not match deterministic recomputation",
        ));
    }
    Ok(())
}

fn validate_source_hashes(
    source_vector_manifest_sha256: &str,
    normalized_vector_sha256: &str,
) -> Result<()> {
    validate_sha256(
        "source vector-manifest SHA-256",
        source_vector_manifest_sha256,
    )?;
    validate_sha256("normalized-vector SHA-256", normalized_vector_sha256)
}

fn validate_canonical_ids(ids: &[String]) -> Result<()> {
    if ids.iter().any(|id| {
        id.len() != 64
            || !id
                .bytes()
                .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    }) {
        return Err(invalid(
            "canonical input IDs must contain exactly 64 lowercase hexadecimal characters",
        ));
    }
    if ids.windows(2).any(|pair| pair[0] >= pair[1]) {
        return Err(invalid(
            "canonical input IDs must be unique and strictly increasing",
        ));
    }
    Ok(())
}

fn hash_canonical_inputs(canonical_inputs: &[&FineRegionCandidateInput]) -> String {
    let coordinate_count = canonical_inputs
        .iter()
        .map(|input| input.normalized_vector.len())
        .sum::<usize>();
    let mut bytes =
        Vec::with_capacity(35 + canonical_inputs.len() * 72 + coordinate_count.saturating_mul(8));
    bytes.extend_from_slice(b"fine-region-candidate-input-v1\0");
    for input in canonical_inputs {
        bytes.extend_from_slice(input.opaque_id.as_bytes());
        bytes.extend_from_slice(&(input.normalized_vector.len() as u64).to_be_bytes());
        for coordinate in &input.normalized_vector {
            bytes.extend_from_slice(&coordinate.to_bits().to_be_bytes());
        }
    }
    hash_bytes(&bytes)
}

fn require_recomputed_match<Parameters, CandidateRun>(
    artifact: &CandidateArtifact<Parameters, CandidateRun>,
    expected: &CandidateArtifact<Parameters, CandidateRun>,
) -> Result<()>
where
    Parameters: PartialEq,
    CandidateRun: PartialEq,
{
    if artifact != expected {
        return Err(invalid(
            "retained artifact does not match deterministic recomputation from the supplied inputs",
        ));
    }
    Ok(())
}

fn hash_serialized(value: &impl Serialize) -> Result<String> {
    Ok(hash_bytes(&serde_json::to_vec(value)?))
}

fn validate_sha256(name: &str, value: &str) -> Result<()> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err(invalid(format!(
            "{name} must contain exactly 64 lowercase hexadecimal characters"
        )));
    }
    Ok(())
}

fn invalid(message: impl Into<String>) -> CandidateArtifactError {
    CandidateArtifactError::Invariant(message.into())
}
