//! Durable execution record for the production-shaped oracle preflight.

use std::collections::BTreeSet;

use serde::{Deserialize, Serialize};

use crate::artifact::{hash_bytes, hash_file, is_safe_artifact_name};
use crate::embedding::EmbeddingEncoder;
use crate::event::EventId;
use crate::oracle::{OfflineOracle, OracleVersions};
use crate::runner::ExperimentRunner;
use crate::snapshot::{
    DamusSnapshot, Error, Result, create_directory, read_manifest, require_file, write_manifest,
};

const PREFLIGHT_CLAIM: &str = "codepath-exercise-only-no-recommendation-quality-claim";

/// Inputs for one immutable end-to-end preflight execution.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct PreflightConfig {
    /// Filesystem-safe record name.
    pub name: String,
    /// Exact selected corpus stage to exercise.
    pub stage_name: String,
    /// Exact embedding artifact to exercise.
    pub embedding_artifact: String,
    /// Required selected row count.
    pub expected_rows: u64,
    /// Arbitrary text used only to exercise topic bootstrap.
    pub topic: String,
    /// Candidate depth used for both logical oracle entrypoints.
    pub candidate_depth: usize,
}

/// Boolean correctness checks recorded by the preflight.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct PreflightChecks {
    /// Stage and embedding contain exactly the required row count.
    pub artifact_rows_match: bool,
    /// Repeated topic queries return identical source-specific evidence.
    pub text_query_deterministic: bool,
    /// Equivalent runner transitions serialize to identical state.
    pub runner_state_deterministic: bool,
    /// Repeated note-neighbor workflows produce the same local order and evidence.
    pub local_order_deterministic: bool,
    /// No onboarding event survives local filtering.
    pub onboarding_filtered: bool,
    /// The selected source event is absent from the local result.
    pub source_excluded: bool,
    /// At least one unseen neighbor survives the complete workflow.
    pub unseen_neighbor_returned: bool,
}

/// Immutable evidence that the production-shaped codepaths ran successfully.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct PreflightManifest {
    /// Manifest schema version.
    pub schema_version: u32,
    /// Immutable record name.
    pub name: String,
    /// Explicitly limits the interpretation of this record.
    pub claim: String,
    /// Selected corpus stage name.
    pub stage_name: String,
    /// SHA-256 of the selected corpus-stage manifest.
    pub stage_manifest_sha256: String,
    /// Exact canonical rows exercised.
    pub selected_rows: u64,
    /// Embedding artifact name.
    pub embedding_artifact: String,
    /// SHA-256 of the embedding manifest.
    pub embedding_manifest_sha256: String,
    /// Versions returned by both logical oracle entrypoints.
    pub oracle_versions: OracleVersions,
    /// Arbitrary text used to exercise topic bootstrap.
    pub topic: String,
    /// Candidate depth used per source.
    pub candidate_depth: u64,
    /// First bootstrap candidate selected mechanically as a codepath source.
    pub mechanical_source_event_id: EventId,
    /// Topic-bootstrap candidates returned.
    pub bootstrap_candidates: u64,
    /// Unseen local candidates returned after filtering.
    pub local_candidates: u64,
    /// SHA-256 of the deterministic serialized private state.
    pub runner_state_sha256: String,
    /// SHA-256 of the deterministic serialized local candidate evidence.
    pub local_candidates_sha256: String,
    /// Individual correctness results.
    pub checks: PreflightChecks,
    /// Failed correctness checks; empty means every recorded check passed.
    pub failures: Vec<String>,
}

impl DamusSnapshot {
    /// Exercise both oracle entrypoints through equivalent private runners twice.
    pub fn execute_preflight<E>(
        &self,
        config: &PreflightConfig,
        encoder: E,
    ) -> Result<PreflightManifest>
    where
        E: EmbeddingEncoder,
    {
        validate_name(&config.name)?;
        if config.expected_rows == 0 {
            return Err(Error::Preflight(
                "expected row count must be positive".to_owned(),
            ));
        }
        if config.candidate_depth == 0 {
            return Err(Error::InvalidQuery(
                "candidate depth must be positive".to_owned(),
            ));
        }
        let artifact = self.layout().preflight_dir(&config.name);
        if artifact.exists() {
            let manifest = self.open_preflight(&config.name)?;
            let candidate_depth = usize::try_from(manifest.candidate_depth).map_err(|_| {
                Error::Invariant("recorded candidate depth does not fit usize".to_owned())
            })?;
            if manifest.stage_name != config.stage_name
                || manifest.embedding_artifact != config.embedding_artifact
                || manifest.selected_rows != config.expected_rows
                || manifest.topic != config.topic
                || candidate_depth != config.candidate_depth
            {
                return Err(Error::Preflight(format!(
                    "existing preflight `{}` has different inputs",
                    config.name
                )));
            }
            return Ok(manifest);
        }

        let stage = self.open_corpus_stage(&config.stage_name)?;
        let embedding = self.open_embedding_artifact(&config.embedding_artifact)?;
        let embedding_stage = embedding.corpus_stage.as_ref().ok_or_else(|| {
            Error::Preflight("embedding artifact does not represent a corpus stage".to_owned())
        })?;
        if embedding_stage.name != config.stage_name {
            return Err(Error::Preflight(format!(
                "embedding represents stage `{}` instead of `{}`",
                embedding_stage.name, config.stage_name
            )));
        }
        let artifact_rows_match = stage.selected_rows == config.expected_rows
            && embedding.total_rows == config.expected_rows;

        let mut oracle = OfflineOracle::open(self, &config.embedding_artifact, encoder)?;
        let mut first_runner = ExperimentRunner::new();
        let mut second_runner = ExperimentRunner::new();
        let first_bootstrap =
            first_runner.bootstrap(&mut oracle, config.topic.clone(), config.candidate_depth)?;
        let second_bootstrap =
            second_runner.bootstrap(&mut oracle, config.topic.clone(), config.candidate_depth)?;
        let first_source = first_bootstrap
            .response
            .candidates
            .first()
            .map(|candidate| candidate.event_id)
            .ok_or_else(|| {
                Error::Preflight("topic bootstrap returned no source candidates".to_owned())
            })?;
        let second_source = second_bootstrap
            .response
            .candidates
            .first()
            .map(|candidate| candidate.event_id)
            .ok_or_else(|| {
                Error::Preflight("repeated topic bootstrap returned no candidates".to_owned())
            })?;
        first_runner.select_positive_source(first_bootstrap.interest_id, first_source)?;
        second_runner.select_positive_source(second_bootstrap.interest_id, second_source)?;
        let first_state = serde_json::to_vec(first_runner.state()).map_err(|source| {
            Error::Preflight(format!("failed to serialize first runner state: {source}"))
        })?;
        let second_state = serde_json::to_vec(second_runner.state()).map_err(|source| {
            Error::Preflight(format!("failed to serialize second runner state: {source}"))
        })?;
        let first_candidates = first_runner.recommend(&mut oracle, config.candidate_depth)?;
        let second_candidates = second_runner.recommend(&mut oracle, config.candidate_depth)?;
        let candidate_bytes = serde_json::to_vec(&first_candidates).map_err(|source| {
            Error::Preflight(format!("failed to serialize local candidates: {source}"))
        })?;
        let onboarding = first_bootstrap
            .response
            .candidates
            .iter()
            .map(|candidate| candidate.event_id)
            .collect::<BTreeSet<_>>();
        let checks = PreflightChecks {
            artifact_rows_match,
            text_query_deterministic: first_bootstrap.response == second_bootstrap.response
                && first_source == second_source,
            runner_state_deterministic: first_state == second_state,
            local_order_deterministic: first_candidates == second_candidates,
            onboarding_filtered: first_candidates
                .iter()
                .all(|candidate| !onboarding.contains(&candidate.event_id)),
            source_excluded: first_candidates
                .iter()
                .all(|candidate| candidate.event_id != first_source),
            unseen_neighbor_returned: !first_candidates.is_empty(),
        };
        let failures = failed_checks(&checks);
        let manifest = PreflightManifest {
            schema_version: 1,
            name: config.name.clone(),
            claim: PREFLIGHT_CLAIM.to_owned(),
            stage_name: config.stage_name.clone(),
            stage_manifest_sha256: hash_file(
                &self.layout().corpus_stage_manifest(&config.stage_name),
            )?,
            selected_rows: stage.selected_rows,
            embedding_artifact: config.embedding_artifact.clone(),
            embedding_manifest_sha256: hash_file(
                &self.layout().embedding_manifest(&config.embedding_artifact),
            )?,
            oracle_versions: first_bootstrap.response.versions,
            topic: config.topic.clone(),
            candidate_depth: u64::try_from(config.candidate_depth)
                .map_err(|_| Error::InvalidQuery("candidate depth does not fit u64".to_owned()))?,
            mechanical_source_event_id: first_source,
            bootstrap_candidates: u64::try_from(onboarding.len()).map_err(|_| {
                Error::Invariant("bootstrap candidate count does not fit u64".to_owned())
            })?,
            local_candidates: u64::try_from(first_candidates.len()).map_err(|_| {
                Error::Invariant("local candidate count does not fit u64".to_owned())
            })?,
            runner_state_sha256: hash_bytes(&first_state),
            local_candidates_sha256: hash_bytes(&candidate_bytes),
            checks,
            failures,
        };

        create_directory(&self.layout().preflight_root())?;
        let stage_path =
            self.prepare_stage(&artifact, &self.layout().preflight_work(&config.name))?;
        write_manifest(&stage_path.join("manifest.json"), &manifest)?;
        self.publish_stage(&stage_path, &artifact)?;
        Ok(manifest)
    }

    /// Open a preflight record and verify every artifact identity it names.
    pub fn open_preflight(&self, name: &str) -> Result<PreflightManifest> {
        validate_name(name)?;
        let path = self.layout().preflight_manifest(name);
        require_file(&path)?;
        let manifest: PreflightManifest = read_manifest(&path)?;
        if manifest.schema_version != 1
            || manifest.name != name
            || manifest.claim != PREFLIGHT_CLAIM
        {
            return Err(Error::Preflight(format!(
                "preflight record `{name}` has an incompatible identity"
            )));
        }
        let stage = self.open_corpus_stage(&manifest.stage_name)?;
        let embedding = self.open_embedding_artifact(&manifest.embedding_artifact)?;
        let stage_manifest_sha256 =
            hash_file(&self.layout().corpus_stage_manifest(&manifest.stage_name))?;
        let embedding_manifest_sha256 = hash_file(
            &self
                .layout()
                .embedding_manifest(&manifest.embedding_artifact),
        )?;
        if stage_manifest_sha256 != manifest.stage_manifest_sha256
            || embedding_manifest_sha256 != manifest.embedding_manifest_sha256
            || stage.selected_rows != manifest.selected_rows
            || embedding.total_rows != manifest.selected_rows
        {
            return Err(Error::Preflight(format!(
                "preflight record `{name}` no longer matches its artifacts"
            )));
        }
        let embedding_stage = embedding.corpus_stage.as_ref().ok_or_else(|| {
            Error::Preflight(format!(
                "preflight record `{name}` names an embedding without a corpus stage"
            ))
        })?;
        if embedding_stage.name != stage.name
            || embedding_stage.manifest_sha256 != stage_manifest_sha256
            || embedding_stage.rows_sha256 != stage.rows.sha256
            || embedding_stage.selection_rule != stage.selection_rule
        {
            return Err(Error::Preflight(format!(
                "preflight record `{name}` names an embedding for a different corpus stage"
            )));
        }
        let expected_versions =
            OracleVersions::from_embedding(&embedding, &embedding_manifest_sha256);
        if manifest.oracle_versions != expected_versions {
            return Err(Error::Preflight(format!(
                "preflight record `{name}` has oracle versions unrelated to its artifacts"
            )));
        }
        if manifest.failures != failed_checks(&manifest.checks) {
            return Err(Error::Preflight(format!(
                "preflight record `{name}` has failures inconsistent with its checks"
            )));
        }
        Ok(manifest)
    }
}

fn failed_checks(checks: &PreflightChecks) -> Vec<String> {
    let mut failures = Vec::new();
    if !checks.artifact_rows_match {
        failures.push("artifact row counts differ".to_owned());
    }
    if !checks.text_query_deterministic {
        failures.push("repeated text query differs".to_owned());
    }
    if !checks.runner_state_deterministic {
        failures.push("repeated runner state differs".to_owned());
    }
    if !checks.local_order_deterministic {
        failures.push("repeated local order differs".to_owned());
    }
    if !checks.onboarding_filtered {
        failures.push("onboarding event survived local filtering".to_owned());
    }
    if !checks.source_excluded {
        failures.push("source event survived local filtering".to_owned());
    }
    if !checks.unseen_neighbor_returned {
        failures.push("no unseen neighbor survived local filtering".to_owned());
    }
    failures
}

fn validate_name(name: &str) -> Result<()> {
    if !is_safe_artifact_name(name) {
        return Err(Error::Preflight(format!(
            "preflight name `{name}` is not filesystem-safe"
        )));
    }
    Ok(())
}
