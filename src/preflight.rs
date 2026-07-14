//! Durable, replayable execution evidence for the production-shaped oracle preflight.

use std::collections::BTreeSet;
use std::fs;
use std::path::Path;

use serde::{Deserialize, Serialize, de::DeserializeOwned};

use crate::artifact::hash_file;
use crate::embedding::EmbeddingEncoder;
use crate::event::EventId;
use crate::oracle::{
    OfflineOracle, Oracle, OracleProvenance, OracleResponse, OracleVersions,
    verified_oracle_provenance,
};
use crate::runner::{
    BootstrapResult, EXPERIMENT_RUNNER_VERSION, ExperimentRunner, ExperimentState, InterestId,
    LocalCandidate,
};
use crate::snapshot::{
    CorpusManifest, DamusSnapshot, Error, Result, SourceManifest, create_directory, io_error,
    read_manifest, require_file, write_manifest,
};

const PREFLIGHT_SCHEMA_VERSION: u32 = 3;
const PREFLIGHT_CLAIM: &str = "codepath-exercise-only-no-recommendation-quality-claim";
const PREFLIGHT_IMPLEMENTATION_VERSION: &str = "durable-replay-evidence-v3";
const MECHANICAL_SOURCE_LIMIT: usize = 2;

const BOOTSTRAP_RESPONSES_FILE: &str = "bootstrap-responses.json";
const RUNNER_STATES_FILE: &str = "runner-states.json";
const SIMILAR_NOTES_RESPONSES_FILE: &str = "similar-notes-responses.json";
const LOCAL_CANDIDATE_RESULTS_FILE: &str = "local-candidate-results.json";

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

/// One checksummed JSON evidence file within a preflight record.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct PreflightEvidenceArtifact {
    /// Fixed file name relative to the preflight record.
    pub file: String,
    /// Exact serialized byte length.
    pub bytes: u64,
    /// SHA-256 of the exact serialized bytes.
    pub sha256: String,
}

/// Boolean correctness checks derived from persisted evidence.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct PreflightChecks {
    /// Stage and embedding contain exactly the required row count.
    pub artifact_rows_match: bool,
    /// Repeated topic queries return identical source-specific evidence.
    pub text_query_deterministic: bool,
    /// Equivalent runner transitions serialize to identical state.
    pub runner_state_deterministic: bool,
    /// Repeated note queries return identical source responses.
    pub note_query_deterministic: bool,
    /// Repeated note-neighbor workflows produce the same local order and evidence.
    pub local_order_deterministic: bool,
    /// No onboarding event survives local filtering.
    pub onboarding_filtered: bool,
    /// Every direct note-neighbor response excludes its own source event.
    pub source_excluded: bool,
    /// At least one unseen neighbor survives the complete workflow.
    pub unseen_neighbor_returned: bool,
}

/// Immutable evidence that the production-shaped codepaths ran successfully.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct PreflightManifest {
    /// Manifest schema version.
    pub schema_version: u32,
    /// Versioned identity of the preflight execution and verification logic.
    pub preflight_implementation: String,
    /// Versioned identity of the runner workflow exercised by this record.
    pub runner_implementation: String,
    /// Immutable record name.
    pub name: String,
    /// Explicitly limits the interpretation of this record.
    pub claim: String,
    /// SHA-256 of the source-ingestion manifest for the exercised reservoir.
    pub source_manifest_sha256: String,
    /// SHA-256 of the exact compressed snapshot or snapshot extract ingested.
    pub source_snapshot_sha256: String,
    /// Raw JSONL records in that exact compressed input.
    pub source_snapshot_records: u64,
    /// Valid unique source events stored after ingestion, including embedded repost content.
    pub source_stored_events: u64,
    /// SHA-256 of the eligibility-derivation manifest.
    pub corpus_manifest_sha256: String,
    /// Eligible root, non-quote kind `1` events before exact-content canonicalization.
    pub eligible_events: u64,
    /// Selected corpus stage name.
    pub stage_name: String,
    /// SHA-256 of the selected corpus-stage manifest.
    pub stage_manifest_sha256: String,
    /// Row count required by the execution inputs.
    pub expected_rows: u64,
    /// Exact canonical rows exercised.
    pub selected_rows: u64,
    /// Canonical rows available in the exact backing reservoir.
    pub available_canonical_rows: u64,
    /// Deterministic rule that selected the exercised rows.
    pub stage_selection_rule: String,
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
    /// Up to two bootstrap candidates selected mechanically as codepath sources.
    pub mechanical_source_event_ids: Vec<EventId>,
    /// Topic-bootstrap candidates returned.
    pub bootstrap_candidates: u64,
    /// Unseen local candidates returned after filtering.
    pub local_candidates: u64,
    /// Both actual topic-bootstrap results.
    pub bootstrap_responses: PreflightEvidenceArtifact,
    /// Both actual serialized private runner states.
    pub runner_states: PreflightEvidenceArtifact,
    /// Direct note-neighbor responses for every mechanical source in both runs.
    pub similar_notes_responses: PreflightEvidenceArtifact,
    /// Both actual locally filtered and ordered candidate results.
    pub local_candidate_results: PreflightEvidenceArtifact,
    /// Individual correctness results, derived again when this record is opened.
    pub checks: PreflightChecks,
    /// Failed correctness checks; empty means every recorded check passed.
    pub failures: Vec<String>,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
struct BootstrapEvidence {
    runs: [BootstrapResult; 2],
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
struct RunnerStateEvidence {
    runs: [ExperimentState; 2],
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
struct SimilarNotesEvidence {
    runs: [Vec<SourceResponse>; 2],
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
struct SourceResponse {
    source_event_id: EventId,
    response: OracleResponse,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
struct LocalCandidateEvidence {
    runs: [Vec<LocalCandidate>; 2],
}

#[derive(Clone, Debug, PartialEq)]
struct PreflightEvidence {
    bootstrap: BootstrapEvidence,
    runner_states: RunnerStateEvidence,
    similar_notes: SimilarNotesEvidence,
    local_candidates: LocalCandidateEvidence,
}

impl DamusSnapshot {
    /// Execute both oracle entrypoints twice and either publish or replay durable evidence.
    pub fn execute_preflight<E>(
        &self,
        config: &PreflightConfig,
        encoder: E,
    ) -> Result<PreflightManifest>
    where
        E: EmbeddingEncoder,
    {
        validate_config(config)?;
        let artifact = self.layout().preflight_dir(&config.name);
        let persisted = if artifact.exists() {
            let manifest = self.open_preflight(&config.name)?;
            validate_existing_inputs(&manifest, config)?;
            Some(manifest)
        } else {
            None
        };

        let stage = self.open_corpus_stage(&config.stage_name)?;
        let source: SourceManifest = read_manifest(&self.layout().source_manifest())?;
        let corpus: CorpusManifest = read_manifest(&self.layout().corpus_manifest())?;
        if source.schema_version != 1 || source.snapshot_sha256 != stage.source_snapshot_sha256 {
            return Err(Error::Preflight(
                "source manifest does not match the selected corpus stage".to_owned(),
            ));
        }
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
        let expected_provenance =
            verified_oracle_provenance(self, &embedding, config.candidate_depth)?;
        let mut oracle = OfflineOracle::open(self, &config.embedding_artifact, encoder)?;
        let evidence = execute_workflow(&mut oracle, config)?;
        validate_evidence_structure(
            &evidence,
            oracle.versions(),
            u64::try_from(config.candidate_depth)
                .map_err(|_| Error::InvalidQuery("candidate depth does not fit u64".to_owned()))?,
            &config.topic,
            &expected_provenance,
        )?;
        let checks = derive_checks(artifact_rows_match, &evidence);

        if let Some(manifest) = persisted {
            let recorded = read_evidence(self, &manifest)?;
            if evidence != recorded || checks != manifest.checks {
                return Err(Error::Preflight(format!(
                    "preflight `{}` re-execution differs from persisted evidence",
                    config.name
                )));
            }
            return Ok(manifest);
        }

        create_directory(&self.layout().preflight_root())?;
        let stage_path =
            self.prepare_stage(&artifact, &self.layout().preflight_work(&config.name))?;
        let bootstrap_responses =
            write_evidence(&stage_path, BOOTSTRAP_RESPONSES_FILE, &evidence.bootstrap)?;
        let runner_states =
            write_evidence(&stage_path, RUNNER_STATES_FILE, &evidence.runner_states)?;
        let similar_notes_responses = write_evidence(
            &stage_path,
            SIMILAR_NOTES_RESPONSES_FILE,
            &evidence.similar_notes,
        )?;
        let local_candidate_results = write_evidence(
            &stage_path,
            LOCAL_CANDIDATE_RESULTS_FILE,
            &evidence.local_candidates,
        )?;
        let first_bootstrap = &evidence.bootstrap.runs[0];
        let first_candidates = &evidence.local_candidates.runs[0];
        let mechanical_source_event_ids = mechanical_sources(first_bootstrap);
        let failures = failed_checks(&checks);
        let manifest = PreflightManifest {
            schema_version: PREFLIGHT_SCHEMA_VERSION,
            preflight_implementation: PREFLIGHT_IMPLEMENTATION_VERSION.to_owned(),
            runner_implementation: EXPERIMENT_RUNNER_VERSION.to_owned(),
            name: config.name.clone(),
            claim: PREFLIGHT_CLAIM.to_owned(),
            source_manifest_sha256: hash_file(&self.layout().source_manifest())?,
            source_snapshot_sha256: source.snapshot_sha256,
            source_snapshot_records: source.counts.snapshot_records,
            source_stored_events: source.counts.stored_events,
            corpus_manifest_sha256: hash_file(&self.layout().corpus_manifest())?,
            eligible_events: corpus.eligible_events,
            stage_name: config.stage_name.clone(),
            stage_manifest_sha256: hash_file(
                &self.layout().corpus_stage_manifest(&config.stage_name),
            )?,
            expected_rows: config.expected_rows,
            selected_rows: stage.selected_rows,
            available_canonical_rows: stage.available_canonical_rows,
            stage_selection_rule: stage.selection_rule,
            embedding_artifact: config.embedding_artifact.clone(),
            embedding_manifest_sha256: hash_file(
                &self.layout().embedding_manifest(&config.embedding_artifact),
            )?,
            oracle_versions: first_bootstrap.response.versions.clone(),
            topic: config.topic.clone(),
            candidate_depth: u64::try_from(config.candidate_depth)
                .map_err(|_| Error::InvalidQuery("candidate depth does not fit u64".to_owned()))?,
            mechanical_source_event_ids,
            bootstrap_candidates: u64::try_from(first_bootstrap.response.candidates.len())
                .map_err(|_| {
                    Error::Invariant("bootstrap candidate count does not fit u64".to_owned())
                })?,
            local_candidates: u64::try_from(first_candidates.len()).map_err(|_| {
                Error::Invariant("local candidate count does not fit u64".to_owned())
            })?,
            bootstrap_responses,
            runner_states,
            similar_notes_responses,
            local_candidate_results,
            checks,
            failures,
        };
        write_manifest(&stage_path.join("manifest.json"), &manifest)?;
        self.publish_stage(&stage_path, &artifact)?;
        Ok(manifest)
    }

    /// Open a preflight record and verify its artifact bindings and evidence bytes.
    pub fn open_preflight(&self, name: &str) -> Result<PreflightManifest> {
        validate_name(name)?;
        let path = self.layout().preflight_manifest(name);
        require_file(&path)?;
        let manifest: PreflightManifest = read_manifest(&path)?;
        if manifest.schema_version != PREFLIGHT_SCHEMA_VERSION
            || manifest.preflight_implementation != PREFLIGHT_IMPLEMENTATION_VERSION
            || manifest.runner_implementation != EXPERIMENT_RUNNER_VERSION
            || manifest.name != name
            || manifest.claim != PREFLIGHT_CLAIM
        {
            return Err(Error::Preflight(format!(
                "preflight record `{name}` has an incompatible identity"
            )));
        }
        if manifest.candidate_depth == 0 || manifest.mechanical_source_event_ids.is_empty() {
            return Err(Error::Preflight(format!(
                "preflight record `{name}` has invalid execution inputs"
            )));
        }

        let stage = self.open_corpus_stage(&manifest.stage_name)?;
        let source: SourceManifest = read_manifest(&self.layout().source_manifest())?;
        let corpus: CorpusManifest = read_manifest(&self.layout().corpus_manifest())?;
        let embedding = self.open_embedding_artifact(&manifest.embedding_artifact)?;
        let source_manifest_sha256 = hash_file(&self.layout().source_manifest())?;
        let corpus_manifest_sha256 = hash_file(&self.layout().corpus_manifest())?;
        let stage_manifest_sha256 =
            hash_file(&self.layout().corpus_stage_manifest(&manifest.stage_name))?;
        let embedding_manifest_sha256 = hash_file(
            &self
                .layout()
                .embedding_manifest(&manifest.embedding_artifact),
        )?;
        if source.schema_version != 1
            || source_manifest_sha256 != manifest.source_manifest_sha256
            || source.snapshot_sha256 != manifest.source_snapshot_sha256
            || source.counts.snapshot_records != manifest.source_snapshot_records
            || source.counts.stored_events != manifest.source_stored_events
            || corpus_manifest_sha256 != manifest.corpus_manifest_sha256
            || corpus.eligible_events != manifest.eligible_events
            || corpus.source_snapshot_sha256 != source.snapshot_sha256
            || source.snapshot_sha256 != stage.source_snapshot_sha256
            || stage.available_canonical_rows != manifest.available_canonical_rows
            || stage.selection_rule != manifest.stage_selection_rule
            || stage_manifest_sha256 != manifest.stage_manifest_sha256
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

        let evidence = read_evidence(self, &manifest)?;
        let candidate_depth = usize::try_from(manifest.candidate_depth)
            .map_err(|_| Error::Invariant("candidate depth does not fit usize".to_owned()))?;
        let expected_provenance = verified_oracle_provenance(self, &embedding, candidate_depth)?;
        validate_evidence_structure(
            &evidence,
            &expected_versions,
            manifest.candidate_depth,
            &manifest.topic,
            &expected_provenance,
        )?;
        let source_event_ids = mechanical_sources(&evidence.bootstrap.runs[0]);
        let bootstrap_candidates = evidence.bootstrap.runs[0].response.candidates.len();
        let local_candidates = evidence.local_candidates.runs[0].len();
        if source_event_ids != manifest.mechanical_source_event_ids
            || u64::try_from(bootstrap_candidates).ok() != Some(manifest.bootstrap_candidates)
            || u64::try_from(local_candidates).ok() != Some(manifest.local_candidates)
            || evidence.bootstrap.runs[0].response.versions != manifest.oracle_versions
        {
            return Err(Error::Preflight(format!(
                "preflight record `{name}` has counts or identities inconsistent with its evidence"
            )));
        }
        let checks = derive_checks(
            stage.selected_rows == manifest.expected_rows
                && embedding.total_rows == manifest.expected_rows,
            &evidence,
        );
        if checks != manifest.checks {
            return Err(Error::Preflight(format!(
                "preflight record `{name}` has checks inconsistent with its evidence"
            )));
        }
        Ok(manifest)
    }
}

fn execute_workflow(
    oracle: &mut impl Oracle,
    config: &PreflightConfig,
) -> Result<PreflightEvidence> {
    let mut first_runner = ExperimentRunner::new();
    let mut second_runner = ExperimentRunner::new();
    let first_bootstrap =
        first_runner.bootstrap(oracle, config.topic.clone(), config.candidate_depth)?;
    let second_bootstrap =
        second_runner.bootstrap(oracle, config.topic.clone(), config.candidate_depth)?;
    if first_bootstrap.response.candidates.is_empty()
        || second_bootstrap.response.candidates.is_empty()
    {
        return Err(Error::Preflight(
            "topic bootstrap returned no source candidates".to_owned(),
        ));
    }

    let first_sources = mechanical_sources(&first_bootstrap);
    let second_sources = mechanical_sources(&second_bootstrap);
    for source in &first_sources {
        first_runner.select_positive_source(first_bootstrap.interest_id, *source)?;
    }
    for source in &second_sources {
        second_runner.select_positive_source(second_bootstrap.interest_id, *source)?;
    }

    let first_state = first_runner.state().clone();
    let second_state = second_runner.state().clone();
    let (first_candidates, first_responses) =
        recommend_and_record(&first_runner, oracle, config.candidate_depth)?;
    let (second_candidates, second_responses) =
        recommend_and_record(&second_runner, oracle, config.candidate_depth)?;

    Ok(PreflightEvidence {
        bootstrap: BootstrapEvidence {
            runs: [first_bootstrap, second_bootstrap],
        },
        runner_states: RunnerStateEvidence {
            runs: [first_state, second_state],
        },
        similar_notes: SimilarNotesEvidence {
            runs: [first_responses, second_responses],
        },
        local_candidates: LocalCandidateEvidence {
            runs: [first_candidates, second_candidates],
        },
    })
}

fn recommend_and_record(
    runner: &ExperimentRunner,
    oracle: &mut impl Oracle,
    candidate_depth: usize,
) -> Result<(Vec<LocalCandidate>, Vec<SourceResponse>)> {
    let mut recording = RecordingOracle::new(oracle);
    let candidates = runner.recommend(&mut recording, candidate_depth)?;
    Ok((candidates, recording.into_responses()))
}

struct RecordingOracle<'a, O> {
    oracle: &'a mut O,
    responses: Vec<SourceResponse>,
}

impl<'a, O> RecordingOracle<'a, O> {
    fn new(oracle: &'a mut O) -> Self {
        Self {
            oracle,
            responses: Vec::new(),
        }
    }

    fn into_responses(self) -> Vec<SourceResponse> {
        self.responses
    }
}

impl<O> Oracle for RecordingOracle<'_, O>
where
    O: Oracle,
{
    fn search_text(&mut self, text: &str, candidate_depth: usize) -> Result<OracleResponse> {
        self.oracle.search_text(text, candidate_depth)
    }

    fn similar_notes(
        &mut self,
        note_id: EventId,
        candidate_depth: usize,
    ) -> Result<OracleResponse> {
        let response = self.oracle.similar_notes(note_id, candidate_depth)?;
        self.responses.push(SourceResponse {
            source_event_id: note_id,
            response: response.clone(),
        });
        Ok(response)
    }
}

fn mechanical_sources(bootstrap: &BootstrapResult) -> Vec<EventId> {
    bootstrap
        .response
        .candidates
        .iter()
        .take(MECHANICAL_SOURCE_LIMIT)
        .map(|candidate| candidate.event_id)
        .collect()
}

fn validate_evidence_structure(
    evidence: &PreflightEvidence,
    expected_versions: &OracleVersions,
    candidate_depth: u64,
    topic: &str,
    expected_provenance: &OracleProvenance,
) -> Result<()> {
    if expected_provenance.candidate_depth != candidate_depth {
        return Err(Error::Preflight(
            "bootstrap evidence has an incompatible candidate depth".to_owned(),
        ));
    }
    for run in 0..2 {
        let bootstrap = &evidence.bootstrap.runs[run];
        if bootstrap.response.versions != *expected_versions
            || bootstrap.response.provenance != *expected_provenance
        {
            return Err(Error::Preflight(format!(
                "bootstrap evidence run {run} has incompatible oracle versions"
            )));
        }
        validate_oracle_response(&bootstrap.response)?;
        let expected_sources = mechanical_sources(bootstrap);
        let expected_query_order = expected_sources
            .iter()
            .copied()
            .collect::<BTreeSet<_>>()
            .into_iter()
            .collect::<Vec<_>>();
        let actual_sources = evidence.similar_notes.runs[run]
            .iter()
            .map(|source| source.source_event_id)
            .collect::<Vec<_>>();
        if actual_sources != expected_query_order {
            return Err(Error::Preflight(format!(
                "similar-notes evidence run {run} does not match its mechanical sources"
            )));
        }
        for source in &evidence.similar_notes.runs[run] {
            if source.response.versions != *expected_versions
                || source.response.provenance != *expected_provenance
            {
                return Err(Error::Preflight(format!(
                    "similar-notes evidence run {run} has incompatible oracle versions"
                )));
            }
            validate_oracle_response(&source.response)?;
        }

        let expected_state = replay_bootstrap_state(
            bootstrap,
            &expected_sources,
            topic,
            usize::try_from(candidate_depth)
                .map_err(|_| Error::Invariant("candidate depth does not fit usize".to_owned()))?,
        )?;
        if evidence.runner_states.runs[run] != expected_state {
            return Err(Error::Preflight(format!(
                "runner-state evidence run {run} is not the exact bootstrap transition result"
            )));
        }
        let restored = ExperimentRunner::restore(evidence.runner_states.runs[run].clone())?;
        let interest = restored
            .state()
            .interest(bootstrap.interest_id)
            .ok_or_else(|| {
                Error::Preflight(format!(
                    "runner-state evidence run {run} lacks its bootstrap interest"
                ))
            })?;
        let onboarding = bootstrap
            .response
            .candidates
            .iter()
            .map(|candidate| candidate.event_id)
            .collect::<BTreeSet<_>>();
        let positive_sources = expected_sources.iter().copied().collect::<BTreeSet<_>>();
        if interest.onboarding_ids() != &onboarding
            || interest.positive_sources() != &positive_sources
        {
            return Err(Error::Preflight(format!(
                "runner-state evidence run {run} does not match bootstrap selections"
            )));
        }
        let mut replay = ReplayOracle::new(&evidence.similar_notes.runs[run]);
        let replayed_candidates = restored.recommend(
            &mut replay,
            usize::try_from(candidate_depth)
                .map_err(|_| Error::Invariant("candidate depth does not fit usize".to_owned()))?,
        )?;
        replay.finish()?;
        if replayed_candidates != evidence.local_candidates.runs[run] {
            return Err(Error::Preflight(format!(
                "local-candidate evidence run {run} is not the exact runner output from its persisted source responses"
            )));
        }
        validate_local_candidates(
            &evidence.local_candidates.runs[run],
            bootstrap.interest_id,
            &positive_sources,
            &evidence.similar_notes.runs[run],
            expected_versions,
        )?;
    }
    Ok(())
}

fn replay_bootstrap_state(
    expected: &BootstrapResult,
    sources: &[EventId],
    topic: &str,
    candidate_depth: usize,
) -> Result<ExperimentState> {
    let mut oracle = BootstrapReplayOracle {
        expected_text: topic,
        expected_depth: candidate_depth,
        response: Some(expected.response.clone()),
    };
    let mut runner = ExperimentRunner::new();
    let actual = runner.bootstrap(&mut oracle, topic.to_owned(), candidate_depth)?;
    if &actual != expected || oracle.response.is_some() {
        return Err(Error::Preflight(
            "bootstrap evidence is not the exact runner transition result".to_owned(),
        ));
    }
    for source in sources {
        runner.select_positive_source(actual.interest_id, *source)?;
    }
    Ok(runner.into_state())
}

struct BootstrapReplayOracle<'a> {
    expected_text: &'a str,
    expected_depth: usize,
    response: Option<OracleResponse>,
}

impl Oracle for BootstrapReplayOracle<'_> {
    fn search_text(&mut self, text: &str, candidate_depth: usize) -> Result<OracleResponse> {
        if text != self.expected_text || candidate_depth != self.expected_depth {
            return Err(Error::Preflight(
                "runner bootstrap replay used different query inputs".to_owned(),
            ));
        }
        self.response.take().ok_or_else(|| {
            Error::Preflight("runner bootstrap replay made a duplicate text query".to_owned())
        })
    }

    fn similar_notes(
        &mut self,
        _note_id: EventId,
        _candidate_depth: usize,
    ) -> Result<OracleResponse> {
        Err(Error::Preflight(
            "runner bootstrap replay made an unexpected note query".to_owned(),
        ))
    }
}

struct ReplayOracle<'a> {
    responses: &'a [SourceResponse],
    offset: usize,
}

impl<'a> ReplayOracle<'a> {
    const fn new(responses: &'a [SourceResponse]) -> Self {
        Self {
            responses,
            offset: 0,
        }
    }

    fn finish(self) -> Result<()> {
        if self.offset == self.responses.len() {
            Ok(())
        } else {
            Err(Error::Preflight(
                "persisted source responses contain calls the runner did not make".to_owned(),
            ))
        }
    }
}

impl Oracle for ReplayOracle<'_> {
    fn search_text(&mut self, _text: &str, _candidate_depth: usize) -> Result<OracleResponse> {
        Err(Error::Preflight(
            "runner replay made an unexpected text query".to_owned(),
        ))
    }

    fn similar_notes(
        &mut self,
        note_id: EventId,
        _candidate_depth: usize,
    ) -> Result<OracleResponse> {
        let response = self.responses.get(self.offset).ok_or_else(|| {
            Error::Preflight(format!(
                "runner replay made an unrecorded note query for `{note_id}`"
            ))
        })?;
        if response.source_event_id != note_id {
            return Err(Error::Preflight(format!(
                "runner replay queried `{note_id}` but persisted source `{}` was next",
                response.source_event_id
            )));
        }
        self.offset += 1;
        Ok(response.response.clone())
    }
}

fn validate_oracle_response(response: &OracleResponse) -> Result<()> {
    let mut event_ids = BTreeSet::new();
    for (offset, candidate) in response.candidates.iter().enumerate() {
        let expected_rank = u64::try_from(offset)
            .ok()
            .and_then(|rank| rank.checked_add(1))
            .ok_or_else(|| Error::Invariant("oracle candidate rank overflowed u64".to_owned()))?;
        if candidate.rank != expected_rank
            || !candidate.cosine_score.is_finite()
            || !event_ids.insert(candidate.event_id)
        {
            return Err(Error::Preflight(
                "persisted oracle response violates the response contract".to_owned(),
            ));
        }
    }
    Ok(())
}

fn validate_local_candidates(
    candidates: &[LocalCandidate],
    interest_id: InterestId,
    sources: &BTreeSet<EventId>,
    direct_responses: &[SourceResponse],
    expected_versions: &OracleVersions,
) -> Result<()> {
    let mut event_ids = BTreeSet::new();
    for (offset, candidate) in candidates.iter().enumerate() {
        let expected_rank = u64::try_from(offset)
            .ok()
            .and_then(|rank| rank.checked_add(1))
            .ok_or_else(|| Error::Invariant("local candidate rank overflowed u64".to_owned()))?;
        let mut evidence_sources = BTreeSet::new();
        let invalid_evidence = candidate.evidence.iter().any(|source| {
            let direct_response = direct_responses
                .iter()
                .find(|response| response.source_event_id == source.source_note_id);
            let direct_candidate = direct_response.and_then(|response| {
                response
                    .response
                    .candidates
                    .iter()
                    .find(|direct| direct.event_id == candidate.event_id)
            });
            source.interest_id != interest_id
                || !sources.contains(&source.source_note_id)
                || source.versions != *expected_versions
                || direct_response
                    .is_none_or(|response| source.provenance != response.response.provenance)
                || !evidence_sources.insert(source.source_note_id)
                || direct_candidate.is_none_or(|direct| {
                    direct.rank != source.source_rank || direct.cosine_score != source.cosine_score
                })
        });
        if candidate.local_rank != expected_rank
            || candidate.evidence.is_empty()
            || !event_ids.insert(candidate.event_id)
            || invalid_evidence
        {
            return Err(Error::Preflight(
                "persisted local candidates violate the runner evidence contract".to_owned(),
            ));
        }
    }
    Ok(())
}

fn derive_checks(artifact_rows_match: bool, evidence: &PreflightEvidence) -> PreflightChecks {
    let onboarding = evidence.bootstrap.runs[0]
        .response
        .candidates
        .iter()
        .map(|candidate| candidate.event_id)
        .collect::<BTreeSet<_>>();
    let first_candidates = &evidence.local_candidates.runs[0];
    PreflightChecks {
        artifact_rows_match,
        text_query_deterministic: evidence.bootstrap.runs[0] == evidence.bootstrap.runs[1],
        runner_state_deterministic: evidence.runner_states.runs[0]
            == evidence.runner_states.runs[1],
        note_query_deterministic: evidence.similar_notes.runs[0] == evidence.similar_notes.runs[1],
        local_order_deterministic: evidence.local_candidates.runs[0]
            == evidence.local_candidates.runs[1],
        onboarding_filtered: first_candidates
            .iter()
            .all(|candidate| !onboarding.contains(&candidate.event_id)),
        source_excluded: evidence.similar_notes.runs.iter().flatten().all(|source| {
            source
                .response
                .candidates
                .iter()
                .all(|candidate| candidate.event_id != source.source_event_id)
        }),
        unseen_neighbor_returned: !first_candidates.is_empty(),
    }
}

fn read_evidence(
    pipeline: &DamusSnapshot,
    manifest: &PreflightManifest,
) -> Result<PreflightEvidence> {
    let root = pipeline.layout().preflight_dir(&manifest.name);
    Ok(PreflightEvidence {
        bootstrap: read_evidence_file(
            &root,
            &manifest.bootstrap_responses,
            BOOTSTRAP_RESPONSES_FILE,
        )?,
        runner_states: read_evidence_file(&root, &manifest.runner_states, RUNNER_STATES_FILE)?,
        similar_notes: read_evidence_file(
            &root,
            &manifest.similar_notes_responses,
            SIMILAR_NOTES_RESPONSES_FILE,
        )?,
        local_candidates: read_evidence_file(
            &root,
            &manifest.local_candidate_results,
            LOCAL_CANDIDATE_RESULTS_FILE,
        )?,
    })
}

fn write_evidence<T>(
    root: &Path,
    file: &'static str,
    evidence: &T,
) -> Result<PreflightEvidenceArtifact>
where
    T: Serialize,
{
    let path = root.join(file);
    write_manifest(&path, evidence)?;
    let bytes = fs::metadata(&path)
        .map_err(|source| io_error("read evidence metadata for", &path, source))?
        .len();
    Ok(PreflightEvidenceArtifact {
        file: file.to_owned(),
        bytes,
        sha256: hash_file(&path)?,
    })
}

fn read_evidence_file<T>(
    root: &Path,
    artifact: &PreflightEvidenceArtifact,
    expected_file: &'static str,
) -> Result<T>
where
    T: DeserializeOwned,
{
    if artifact.file != expected_file {
        return Err(Error::Preflight(format!(
            "preflight evidence file `{}` does not match `{expected_file}`",
            artifact.file
        )));
    }
    let path = root.join(expected_file);
    require_file(&path)?;
    let bytes = fs::metadata(&path)
        .map_err(|source| io_error("read evidence metadata for", &path, source))?
        .len();
    let sha256 = hash_file(&path)?;
    if bytes != artifact.bytes || sha256 != artifact.sha256 {
        return Err(Error::Preflight(format!(
            "preflight evidence `{expected_file}` does not match its checksum"
        )));
    }
    read_manifest(&path)
}

fn validate_config(config: &PreflightConfig) -> Result<()> {
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
    Ok(())
}

fn validate_existing_inputs(manifest: &PreflightManifest, config: &PreflightConfig) -> Result<()> {
    let candidate_depth = usize::try_from(manifest.candidate_depth)
        .map_err(|_| Error::Invariant("recorded candidate depth does not fit usize".to_owned()))?;
    if manifest.stage_name != config.stage_name
        || manifest.embedding_artifact != config.embedding_artifact
        || manifest.expected_rows != config.expected_rows
        || manifest.topic != config.topic
        || candidate_depth != config.candidate_depth
    {
        return Err(Error::Preflight(format!(
            "existing preflight `{}` has different inputs",
            config.name
        )));
    }
    Ok(())
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
    if !checks.note_query_deterministic {
        failures.push("repeated note query differs".to_owned());
    }
    if !checks.local_order_deterministic {
        failures.push("repeated local order differs".to_owned());
    }
    if !checks.onboarding_filtered {
        failures.push("onboarding event survived local filtering".to_owned());
    }
    if !checks.source_excluded {
        failures.push("source event survived direct oracle exclusion".to_owned());
    }
    if !checks.unseen_neighbor_returned {
        failures.push("no unseen neighbor survived local filtering".to_owned());
    }
    failures
}

fn validate_name(name: &str) -> Result<()> {
    if !crate::artifact::is_safe_artifact_name(name) {
        return Err(Error::Preflight(format!(
            "preflight name `{name}` is not filesystem-safe"
        )));
    }
    Ok(())
}
