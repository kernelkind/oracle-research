//! Reproducible in-memory artifacts for fine-segmentation candidates.
//!
//! The wrapper retains the algorithm's complete production result and binds it
//! to the ordered vector identities, upstream vector artifacts, exact
//! parameters, implementation source, and deterministic tie rules. Verification
//! reruns the production algorithm and reconstructs the entire expected
//! artifact; it does not trust hashes stored in the artifact being checked.

use std::collections::BTreeSet;

use serde::{Deserialize, Serialize};
use thiserror::Error;

use crate::artifact::hash_bytes;
use crate::fine_region_hdbscan::{HdbscanConfig, HdbscanError, HdbscanResult, hdbscan};
use crate::fine_region_partition::CosineMatrix;
use crate::fine_region_snn::{SnnConfig, SnnError, SnnSegmentation, snn_segmentation};

const SNN_SOURCE: &[u8] = include_bytes!("fine_region_snn.rs");
const HDBSCAN_SOURCE: &[u8] = include_bytes!("fine_region_hdbscan.rs");

pub const CANDIDATE_ARTIFACT_SCHEMA_VERSION: u32 = 1;
pub const SNN_ALGORITHM_VERSION: &str = "snn-sdm-2003-exact-angular-v1";
pub const HDBSCAN_ALGORITHM_VERSION: &str = "hdbscan-star-exact-angular-v1";

/// SNN ties use lower input ordinals in exact angular-neighbor ordering. An
/// ambiguous border point chooses the qualifying core link with the greatest
/// shared-neighbor count, then the smallest angular distance, then the lowest
/// core ordinal. Border points never connect core components.
pub const SNN_TIE_RULE_VERSION: &str = "snn-angular-ordinal-border-v1";

/// HDBSCAN* MST ties use source then target input ordinal, all equal-distance
/// splits are condensed simultaneously, EOM selects the parent on equal
/// stability, and public clusters use member ordinals then cluster ID.
pub const HDBSCAN_TIE_RULE_VERSION: &str = "hdbscan-angular-ordinal-equal-tier-v1";

#[derive(Clone, Copy)]
struct AlgorithmContract {
    version: &'static str,
    tie_rule_version: &'static str,
    implementation_source: &'static [u8],
}

const SNN_CONTRACT: AlgorithmContract = AlgorithmContract {
    version: SNN_ALGORITHM_VERSION,
    tie_rule_version: SNN_TIE_RULE_VERSION,
    implementation_source: SNN_SOURCE,
};

const HDBSCAN_CONTRACT: AlgorithmContract = AlgorithmContract {
    version: HDBSCAN_ALGORITHM_VERSION,
    tie_rule_version: HDBSCAN_TIE_RULE_VERSION,
    implementation_source: HDBSCAN_SOURCE,
};

pub type Result<T> = std::result::Result<T, CandidateArtifactError>;

#[derive(Debug, Error)]
pub enum CandidateArtifactError {
    #[error("fine-region candidate artifact invariant failed: {0}")]
    Invariant(String),
    #[error(transparent)]
    Snn(#[from] SnnError),
    #[error(transparent)]
    Hdbscan(#[from] HdbscanError),
    #[error("fine-region candidate artifact serialization failed: {0}")]
    Serialization(#[from] serde_json::Error),
}

/// Integrity and reproducibility metadata shared by both candidate algorithms.
#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CandidateArtifactManifest<Parameters> {
    pub schema_version: u32,
    pub algorithm_version: String,
    /// SHA-256 of the exact Rust algorithm module compiled into this build.
    pub implementation_source_sha256: String,
    pub source_vector_manifest_sha256: String,
    pub normalized_vector_sha256: String,
    /// SHA-256 of the compact JSON array of opaque IDs in supplied order.
    pub ordered_vector_ids_sha256: String,
    pub vector_count: usize,
    pub parameters: Parameters,
    pub tie_rule_version: String,
    /// SHA-256 of the compact JSON encoding of the complete production result.
    pub result_sha256: String,
}

/// A complete candidate result plus the identities and manifest that bind it.
#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CandidateArtifact<Parameters, AlgorithmResult> {
    pub manifest: CandidateArtifactManifest<Parameters>,
    pub ordered_vector_ids: Vec<String>,
    pub result: AlgorithmResult,
}

pub type SnnCandidateArtifact = CandidateArtifact<SnnConfig, SnnSegmentation>;
pub type HdbscanCandidateArtifact = CandidateArtifact<HdbscanConfig, HdbscanResult>;

pub fn build_snn_candidate_artifact(
    cosines: &CosineMatrix,
    ordered_vector_ids: &[String],
    source_vector_manifest_sha256: &str,
    normalized_vector_sha256: &str,
    config: &SnnConfig,
) -> Result<SnnCandidateArtifact> {
    validate_inputs(
        cosines,
        ordered_vector_ids,
        source_vector_manifest_sha256,
        normalized_vector_sha256,
    )?;
    let result = snn_segmentation(cosines, config)?;
    assemble_artifact(
        ordered_vector_ids,
        source_vector_manifest_sha256,
        normalized_vector_sha256,
        config.clone(),
        result,
        SNN_CONTRACT,
    )
}

pub fn verify_snn_candidate_artifact(
    artifact: &SnnCandidateArtifact,
    cosines: &CosineMatrix,
    ordered_vector_ids: &[String],
    source_vector_manifest_sha256: &str,
    normalized_vector_sha256: &str,
    config: &SnnConfig,
) -> Result<()> {
    validate_retained_artifact(artifact, cosines.count(), SNN_CONTRACT)?;
    if artifact.manifest.parameters != artifact.result.config {
        return Err(invalid(
            "SNN manifest parameters differ from the retained production result",
        ));
    }
    let expected = build_snn_candidate_artifact(
        cosines,
        ordered_vector_ids,
        source_vector_manifest_sha256,
        normalized_vector_sha256,
        config,
    )?;
    require_recomputed_match(artifact, &expected)
}

pub fn build_hdbscan_candidate_artifact(
    cosines: &CosineMatrix,
    ordered_vector_ids: &[String],
    source_vector_manifest_sha256: &str,
    normalized_vector_sha256: &str,
    config: &HdbscanConfig,
) -> Result<HdbscanCandidateArtifact> {
    validate_inputs(
        cosines,
        ordered_vector_ids,
        source_vector_manifest_sha256,
        normalized_vector_sha256,
    )?;
    let result = hdbscan(cosines, *config)?;
    assemble_artifact(
        ordered_vector_ids,
        source_vector_manifest_sha256,
        normalized_vector_sha256,
        *config,
        result,
        HDBSCAN_CONTRACT,
    )
}

pub fn verify_hdbscan_candidate_artifact(
    artifact: &HdbscanCandidateArtifact,
    cosines: &CosineMatrix,
    ordered_vector_ids: &[String],
    source_vector_manifest_sha256: &str,
    normalized_vector_sha256: &str,
    config: &HdbscanConfig,
) -> Result<()> {
    validate_retained_artifact(artifact, cosines.count(), HDBSCAN_CONTRACT)?;
    if artifact.manifest.parameters != artifact.result.config {
        return Err(invalid(
            "HDBSCAN* manifest parameters differ from the retained production result",
        ));
    }
    let expected = build_hdbscan_candidate_artifact(
        cosines,
        ordered_vector_ids,
        source_vector_manifest_sha256,
        normalized_vector_sha256,
        config,
    )?;
    require_recomputed_match(artifact, &expected)
}

fn assemble_artifact<Parameters, AlgorithmResult>(
    ordered_vector_ids: &[String],
    source_vector_manifest_sha256: &str,
    normalized_vector_sha256: &str,
    parameters: Parameters,
    result: AlgorithmResult,
    contract: AlgorithmContract,
) -> Result<CandidateArtifact<Parameters, AlgorithmResult>>
where
    Parameters: Serialize,
    AlgorithmResult: Serialize,
{
    let manifest = CandidateArtifactManifest {
        schema_version: CANDIDATE_ARTIFACT_SCHEMA_VERSION,
        algorithm_version: contract.version.to_owned(),
        implementation_source_sha256: hash_bytes(contract.implementation_source),
        source_vector_manifest_sha256: source_vector_manifest_sha256.to_owned(),
        normalized_vector_sha256: normalized_vector_sha256.to_owned(),
        ordered_vector_ids_sha256: hash_serialized(&ordered_vector_ids)?,
        vector_count: ordered_vector_ids.len(),
        parameters,
        tie_rule_version: contract.tie_rule_version.to_owned(),
        result_sha256: hash_serialized(&result)?,
    };
    Ok(CandidateArtifact {
        manifest,
        ordered_vector_ids: ordered_vector_ids.to_vec(),
        result,
    })
}

fn validate_inputs(
    cosines: &CosineMatrix,
    ordered_vector_ids: &[String],
    source_vector_manifest_sha256: &str,
    normalized_vector_sha256: &str,
) -> Result<()> {
    validate_ordered_ids(ordered_vector_ids, cosines.count())?;
    validate_sha256(
        "source vector-manifest SHA-256",
        source_vector_manifest_sha256,
    )?;
    validate_sha256("normalized-vector SHA-256", normalized_vector_sha256)
}

fn validate_ordered_ids(ordered_vector_ids: &[String], expected_count: usize) -> Result<()> {
    if ordered_vector_ids.len() != expected_count {
        return Err(invalid(format!(
            "ordered vector-ID count {} does not match cosine-matrix count {expected_count}",
            ordered_vector_ids.len()
        )));
    }
    if ordered_vector_ids.iter().any(String::is_empty) {
        return Err(invalid("ordered vector IDs must each be nonempty"));
    }
    let unique = ordered_vector_ids.iter().collect::<BTreeSet<_>>();
    if unique.len() != ordered_vector_ids.len() {
        return Err(invalid("ordered vector IDs must be unique"));
    }
    Ok(())
}

fn validate_retained_artifact<Parameters, AlgorithmResult>(
    artifact: &CandidateArtifact<Parameters, AlgorithmResult>,
    expected_count: usize,
    contract: AlgorithmContract,
) -> Result<()>
where
    Parameters: Serialize,
    AlgorithmResult: Serialize,
{
    validate_ordered_ids(&artifact.ordered_vector_ids, expected_count)?;
    for (name, value) in [
        (
            "implementation-source SHA-256",
            artifact.manifest.implementation_source_sha256.as_str(),
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
            "ordered-vector-ID SHA-256",
            artifact.manifest.ordered_vector_ids_sha256.as_str(),
        ),
        ("result SHA-256", artifact.manifest.result_sha256.as_str()),
    ] {
        validate_sha256(name, value)?;
    }
    if artifact.manifest.schema_version != CANDIDATE_ARTIFACT_SCHEMA_VERSION
        || artifact.manifest.algorithm_version != contract.version
        || artifact.manifest.tie_rule_version != contract.tie_rule_version
        || artifact.manifest.vector_count != expected_count
        || artifact.manifest.implementation_source_sha256
            != hash_bytes(contract.implementation_source)
        || artifact.manifest.ordered_vector_ids_sha256
            != hash_serialized(&artifact.ordered_vector_ids)?
        || artifact.manifest.result_sha256 != hash_serialized(&artifact.result)?
    {
        return Err(invalid(
            "retained artifact metadata does not match deterministic recomputation",
        ));
    }
    Ok(())
}

fn require_recomputed_match<Parameters, AlgorithmResult>(
    artifact: &CandidateArtifact<Parameters, AlgorithmResult>,
    expected: &CandidateArtifact<Parameters, AlgorithmResult>,
) -> Result<()>
where
    Parameters: PartialEq,
    AlgorithmResult: PartialEq,
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
