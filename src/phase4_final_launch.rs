//! Host-side safety planning for the real frozen Phase 4 evaluation.

use std::ffi::OsString;
use std::fs;
use std::fs::{File, OpenOptions};
use std::io::{self, BufReader, BufWriter, Write};
use std::os::unix::fs::{MetadataExt, OpenOptionsExt, PermissionsExt};
use std::path::{Component, Path, PathBuf};
use std::process::Command;
use std::time::{SystemTime, UNIX_EPOCH};

use serde::{Deserialize, Serialize};

use crate::adaptive_learning::CompletedAdaptiveLearning;
use crate::adaptive_learning_runner::replay_completed_adaptive_learning;
use crate::artifact::hash_file;
use crate::final_evaluation_runner::{
    FinalEvaluationRunnerConfig, FinalEvaluationRunnerOutcome, resume_final_evaluation_tui,
    run_final_evaluation_tui,
};
use crate::fp32_oracle::Fp32OfflineOracle;
use crate::phase3_binding::Phase3RunnerBinding;
use crate::phase3_cost_preflight::{
    create_private_preflight_directory, immutable_content_tree_identity,
    immutable_tree_metadata_fingerprint, prepare_disposable_representation_view,
    write_private_json_atomic,
};
use crate::phase3_learning_launch::{
    HOST_MEMORY_RESERVE_BYTES as PHASE3_HOST_MEMORY_RESERVE_BYTES, HUMAN_LEARNING_PURPOSE,
    HostMemorySnapshot, MINIMUM_LEARNING_MEMORY_BYTES, derive_learning_memory_limit,
    read_host_memory_snapshot, read_learning_launch_config, resolve_controller_image_id,
};
use crate::representation::{RepresentationEncoder, RepresentationManifest, verify_representation};
use crate::snapshot::{Error, Result};

const GIB: u64 = 1024 * 1024 * 1024;
const CONFIG_SCHEMA_VERSION: u32 = 1;
const INITIALIZATION_SCHEMA_VERSION: u32 = 1;
const LAUNCH_SCHEMA_VERSION: u32 = 1;
const INITIALIZATION_FILE: &str = "initialization.json";
const FROZEN_CONFIG_FILE: &str = "frozen-config.json";
const SESSION_FILE: &str = "phase4-session.json";
const ORDERS_FILE: &str = "frozen-orders.json";
const REPORT_FILE: &str = "final-report.json";
const LAUNCH_RECEIPT_FILE: &str = "launch.json";
const PHASE3_INITIALIZATION_FILE: &str = "initialization.json";
const PHASE3_FROZEN_CONFIG_FILE: &str = "frozen-config.json";
const PHASE3_RUNNER_BINDING_FILE: &str = "runner-binding.json";
const PHASE3_SESSION_FILE: &str = "phase3-session.json";
const PHASE3_LAUNCH_FILE: &str = "launch.json";
const PHASE3_CORPUS_DIRECTORY: &str = "corpus.ndb";
const PHASE3_ORDERED_EVENT_IDS_FILE: &str = "ordered-event-ids.bin";
const PHASE3_REPRESENTATION_DIRECTORY: &str = "representation";
const CORPUS_DIRECTORY: &str = "corpus.ndb";
const ORDERED_EVENT_IDS_FILE: &str = "ordered-event-ids.bin";
const REPRESENTATION_DIRECTORY: &str = "representation";

pub const FINAL_EVALUATION_PURPOSE: &str = "human-phase4-final-evaluation-v1";
pub const HOST_MEMORY_RESERVE_BYTES: u64 = 12 * GIB;

/// The already-proven full-matrix controller-and-worker envelope.
pub const MINIMUM_FINAL_EVALUATION_MEMORY_BYTES: u64 = 67 * GIB;

#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Phase4FinalLaunchConfig {
    schema_version: u32,
    purpose: String,
    workspace_path: PathBuf,
    source_phase3_workspace_path: PathBuf,
    source_representation_path: PathBuf,
    source_model_bundle_path: PathBuf,
    container_runtime: PathBuf,
    container_name: String,
    controller_image: String,
    /// SHA-256 of the completed Phase 3 session. The session manifests every
    /// cache response required to reconstruct the completed handoff, so this
    /// digest is also the Phase 3 handoff identity recorded in the final report.
    source_phase3_session_sha256: String,
    expected_representation_version: String,
    host_memory_reserve_bytes: u64,
}

impl Phase4FinalLaunchConfig {
    pub fn workspace_path(&self) -> &Path {
        &self.workspace_path
    }

    pub fn source_phase3_workspace_path(&self) -> &Path {
        &self.source_phase3_workspace_path
    }

    pub fn source_representation_path(&self) -> &Path {
        &self.source_representation_path
    }

    pub fn source_model_bundle_path(&self) -> &Path {
        &self.source_model_bundle_path
    }

    pub fn container_runtime(&self) -> &Path {
        &self.container_runtime
    }

    pub fn container_name(&self) -> &str {
        &self.container_name
    }

    pub fn controller_image(&self) -> &str {
        &self.controller_image
    }

    pub fn source_phase3_session_sha256(&self) -> &str {
        &self.source_phase3_session_sha256
    }

    pub fn expected_representation_version(&self) -> &str {
        &self.expected_representation_version
    }

    pub const fn host_memory_reserve_bytes(&self) -> u64 {
        self.host_memory_reserve_bytes
    }

    fn validate(&self) -> Result<()> {
        if self.schema_version != CONFIG_SCHEMA_VERSION {
            return Err(Error::ExperimentState(
                "Phase 4 final-evaluation config has the wrong schema".to_owned(),
            ));
        }
        if self.purpose != FINAL_EVALUATION_PURPOSE {
            return Err(Error::ExperimentState(
                "Phase 4 config is not a human final-evaluation config".to_owned(),
            ));
        }
        if self.host_memory_reserve_bytes != HOST_MEMORY_RESERVE_BYTES {
            return Err(Error::ExperimentState(
                "Phase 4 config must preserve the approved 12 GiB host reserve".to_owned(),
            ));
        }
        for (label, path) in [
            ("workspace", self.workspace_path.as_path()),
            (
                "source Phase 3 workspace",
                self.source_phase3_workspace_path.as_path(),
            ),
            (
                "source representation",
                self.source_representation_path.as_path(),
            ),
            (
                "source model bundle",
                self.source_model_bundle_path.as_path(),
            ),
            ("container runtime", self.container_runtime.as_path()),
        ] {
            require_absolute_normalized(path, label)?;
        }
        for source in [
            &self.source_phase3_workspace_path,
            &self.source_representation_path,
            &self.source_model_bundle_path,
        ] {
            if source.starts_with(&self.workspace_path) || self.workspace_path.starts_with(source) {
                return Err(Error::ExperimentState(format!(
                    "Phase 4 source `{}` overlaps private workspace `{}`",
                    source.display(),
                    self.workspace_path.display()
                )));
            }
        }
        validate_container_name(&self.container_name)?;
        require_image_id(&self.controller_image)?;
        require_sha256(
            &self.source_phase3_session_sha256,
            "source Phase 3 session SHA-256",
        )?;
        require_sha256(
            &self.expected_representation_version,
            "expected representation version",
        )
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum FinalEvaluationWorkspaceState {
    Fresh,
    Initialized,
}

#[derive(Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct FinalEvaluationInitializationReceipt {
    schema_version: u32,
    purpose: String,
    config_sha256: String,
    frozen_config_sha256: String,
    source_phase3_workspace_path: PathBuf,
    source_phase3_initialization_sha256: String,
    source_phase3_frozen_config_sha256: String,
    source_phase3_runner_binding_sha256: String,
    source_phase3_session_sha256: String,
    source_phase3_launch_sha256: String,
    source_phase3_oracle_cache_identity: String,
    representation_version: String,
    source_representation_metadata_sha256: String,
    source_model_metadata_sha256: String,
    created_unix_time_ns: u128,
}

/// Fully verified, private Phase 4 state and immutable Phase 3 inputs.
#[derive(Clone, Debug)]
pub struct PreparedFinalEvaluationWorkspace {
    workspace_path: PathBuf,
    source_phase3_runner_binding_path: PathBuf,
    corpus_path: PathBuf,
    ordered_event_ids_path: PathBuf,
    representation_path: PathBuf,
    frozen_config_path: PathBuf,
    session_path: PathBuf,
    orders_path: PathBuf,
    report_path: PathBuf,
    oracle_cache_path: PathBuf,
    launch_receipt_path: PathBuf,
    created: bool,
}

impl PreparedFinalEvaluationWorkspace {
    pub const fn state(&self) -> FinalEvaluationWorkspaceState {
        FinalEvaluationWorkspaceState::Initialized
    }

    pub const fn created(&self) -> bool {
        self.created
    }

    pub fn workspace_path(&self) -> &Path {
        &self.workspace_path
    }

    pub fn source_phase3_runner_binding_path(&self) -> &Path {
        &self.source_phase3_runner_binding_path
    }

    pub fn corpus_path(&self) -> &Path {
        &self.corpus_path
    }

    pub fn ordered_event_ids_path(&self) -> &Path {
        &self.ordered_event_ids_path
    }

    pub fn representation_path(&self) -> &Path {
        &self.representation_path
    }

    pub fn frozen_config_path(&self) -> &Path {
        &self.frozen_config_path
    }

    pub fn session_path(&self) -> &Path {
        &self.session_path
    }

    pub fn orders_path(&self) -> &Path {
        &self.orders_path
    }

    pub fn report_path(&self) -> &Path {
        &self.report_path
    }

    pub fn oracle_cache_path(&self) -> &Path {
        &self.oracle_cache_path
    }

    pub fn launch_receipt_path(&self) -> &Path {
        &self.launch_receipt_path
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct FinalEvaluationLaunchReceipt {
    schema_version: u32,
    purpose: String,
    config_sha256: String,
    initialization_sha256: String,
    controller_image_id: String,
    container_name: String,
    session_path: PathBuf,
    orders_path: PathBuf,
    report_path: PathBuf,
    memory_limit_bytes: u64,
    host_memory_reserve_bytes: u64,
}

impl FinalEvaluationLaunchReceipt {
    pub fn controller_image_id(&self) -> &str {
        &self.controller_image_id
    }

    pub fn container_name(&self) -> &str {
        &self.container_name
    }

    pub const fn memory_limit_bytes(&self) -> u64 {
        self.memory_limit_bytes
    }
}

pub fn read_final_evaluation_launch_config(
    path: impl AsRef<Path>,
) -> Result<Phase4FinalLaunchConfig> {
    let path = path.as_ref();
    require_absolute_normalized(path, "Phase 4 config")?;
    let input = File::open(path).map_err(|source| Error::Io {
        operation: "open",
        path: path.to_owned(),
        source,
    })?;
    let config: Phase4FinalLaunchConfig =
        serde_json::from_reader(BufReader::new(input)).map_err(|source| Error::Manifest {
            operation: "decode",
            path: path.to_owned(),
            source,
        })?;
    config.validate()?;
    Ok(config)
}

pub fn inspect_final_evaluation_workspace(
    workspace: impl AsRef<Path>,
    config_sha256: &str,
) -> Result<FinalEvaluationWorkspaceState> {
    let workspace = workspace.as_ref();
    require_absolute_normalized(workspace, "Phase 4 workspace")?;
    require_sha256(config_sha256, "Phase 4 config SHA-256")?;
    let metadata = match fs::symlink_metadata(workspace) {
        Ok(metadata) => metadata,
        Err(error) if error.kind() == io::ErrorKind::NotFound => {
            return Ok(FinalEvaluationWorkspaceState::Fresh);
        }
        Err(source) => return Err(io_error("inspect", workspace, source)),
    };
    if metadata.file_type().is_symlink() || !metadata.is_dir() {
        return Err(Error::ExperimentState(
            "Phase 4 workspace must be a real private directory".to_owned(),
        ));
    }
    let receipt_path = workspace.join(INITIALIZATION_FILE);
    let receipt: FinalEvaluationInitializationReceipt =
        read_json(&receipt_path).map_err(|error| {
            if matches!(
                &error,
                Error::Io { source, .. } if source.kind() == io::ErrorKind::NotFound
            ) {
                Error::ExperimentState(
                    "existing Phase 4 workspace has no valid initialization receipt".to_owned(),
                )
            } else {
                error
            }
        })?;
    if receipt.schema_version != INITIALIZATION_SCHEMA_VERSION
        || receipt.purpose != FINAL_EVALUATION_PURPOSE
        || receipt.config_sha256 != config_sha256
    {
        return Err(Error::ExperimentState(
            "existing Phase 4 workspace initialization receipt does not match this evaluation"
                .to_owned(),
        ));
    }
    Ok(FinalEvaluationWorkspaceState::Initialized)
}

pub fn prepare_final_evaluation_workspace(
    config_path: impl AsRef<Path>,
    config: &Phase4FinalLaunchConfig,
) -> Result<PreparedFinalEvaluationWorkspace> {
    config.validate()?;
    let config_path = canonical_exact(config_path.as_ref(), "Phase 4 config")?;
    let config_sha256 = hash_file(&config_path)?;
    let workspace = resolve_workspace_path(&config.workspace_path)?;
    match inspect_final_evaluation_workspace(&workspace, &config_sha256)? {
        FinalEvaluationWorkspaceState::Initialized => {
            verify_initialized_workspace(&workspace, &config_path, config, &config_sha256)?;
            Ok(prepared_layout(
                workspace,
                canonical_exact(
                    &config.source_phase3_workspace_path,
                    "source Phase 3 workspace",
                )?,
                false,
            ))
        }
        FinalEvaluationWorkspaceState::Fresh => {
            initialize_workspace(&workspace, &config_path, config, &config_sha256)?;
            verify_initialized_workspace(&workspace, &config_path, config, &config_sha256)?;
            Ok(prepared_layout(
                workspace,
                canonical_exact(
                    &config.source_phase3_workspace_path,
                    "source Phase 3 workspace",
                )?,
                true,
            ))
        }
    }
}

fn initialize_workspace(
    workspace: &Path,
    config_path: &Path,
    config: &Phase4FinalLaunchConfig,
    config_sha256: &str,
) -> Result<()> {
    let source = source_identity(config)?;
    let parent = workspace
        .parent()
        .ok_or_else(|| Error::Invariant("Phase 4 workspace has no parent".to_owned()))?;
    let name = workspace
        .file_name()
        .ok_or_else(|| Error::Invariant("Phase 4 workspace has no file name".to_owned()))?;
    let stage = parent.join(format!(".{}.initialize", name.to_string_lossy()));
    match fs::symlink_metadata(&stage) {
        Ok(_) => return Err(Error::IncompleteStage(stage)),
        Err(error) if error.kind() == io::ErrorKind::NotFound => {}
        Err(source) => return Err(io_error("inspect", &stage, source)),
    }
    create_private_preflight_directory(&stage)?;
    let staged = prepared_layout(stage.clone(), source.workspace_path.clone(), true);
    let result = (|| {
        create_owner_only_directory(&staged.corpus_path)?;
        copy_private_file(
            &source
                .workspace_path
                .join(PHASE3_CORPUS_DIRECTORY)
                .join("data.mdb"),
            &staged.corpus_path.join("data.mdb"),
        )?;
        copy_private_file(
            &source.workspace_path.join(PHASE3_ORDERED_EVENT_IDS_FILE),
            &staged.ordered_event_ids_path,
        )?;
        prepare_disposable_representation_view(
            &config.source_representation_path,
            &staged.representation_path,
        )?;
        let representation = verify_representation(
            &staged.corpus_path,
            &staged.ordered_event_ids_path,
            &staged.representation_path,
        )?;
        if representation.representation_version() != config.expected_representation_version {
            return Err(Error::ExperimentState(
                "prepared Phase 4 representation has the wrong version".to_owned(),
            ));
        }
        copy_private_file(config_path, &staged.frozen_config_path)?;
        let after = source_identity(config)?;
        if source != after {
            return Err(Error::Invariant(
                "a Phase 3 source artifact changed during Phase 4 initialization".to_owned(),
            ));
        }
        let receipt = FinalEvaluationInitializationReceipt {
            schema_version: INITIALIZATION_SCHEMA_VERSION,
            purpose: FINAL_EVALUATION_PURPOSE.to_owned(),
            config_sha256: config_sha256.to_owned(),
            frozen_config_sha256: hash_file(&staged.frozen_config_path)?,
            source_phase3_workspace_path: source.workspace_path,
            source_phase3_initialization_sha256: source.initialization_sha256,
            source_phase3_frozen_config_sha256: source.frozen_config_sha256,
            source_phase3_runner_binding_sha256: source.runner_binding_sha256,
            source_phase3_session_sha256: source.session_sha256,
            source_phase3_launch_sha256: source.launch_sha256,
            source_phase3_oracle_cache_identity: source.oracle_cache_identity,
            representation_version: source.representation_version,
            source_representation_metadata_sha256: source.representation_metadata_sha256,
            source_model_metadata_sha256: source.model_metadata_sha256,
            created_unix_time_ns: unix_time_ns()?,
        };
        write_private_json_atomic(stage.join(INITIALIZATION_FILE), &receipt)?;
        File::open(&stage)
            .and_then(|directory| directory.sync_all())
            .map_err(|source| io_error("sync", &stage, source))?;
        fs::rename(&stage, workspace).map_err(|source| io_error("publish", workspace, source))?;
        File::open(parent)
            .and_then(|directory| directory.sync_all())
            .map_err(|source| io_error("sync", parent, source))
    })();
    if result.is_err() && stage.exists() {
        let _ = fs::remove_dir_all(&stage);
    }
    result
}

fn verify_initialized_workspace(
    workspace: &Path,
    config_path: &Path,
    config: &Phase4FinalLaunchConfig,
    config_sha256: &str,
) -> Result<()> {
    require_private_directory(workspace, "Phase 4 workspace")?;
    let source = source_identity(config)?;
    let layout = prepared_layout(workspace.to_owned(), source.workspace_path.clone(), false);
    require_private_file(&layout.frozen_config_path, "Phase 4 frozen config")?;
    require_optional_private_file(&layout.session_path, "Phase 4 session")?;
    require_optional_private_file(&layout.orders_path, "Phase 4 frozen orders")?;
    require_optional_private_file(&layout.report_path, "Phase 4 final report")?;
    require_optional_private_directory(&layout.oracle_cache_path, "Phase 4 Oracle cache")?;
    let representation = verify_representation(
        &layout.corpus_path,
        &layout.ordered_event_ids_path,
        &layout.representation_path,
    )?;
    if representation.representation_version() != config.expected_representation_version {
        return Err(Error::ExperimentState(
            "prepared Phase 4 representation has the wrong version".to_owned(),
        ));
    }
    let receipt: FinalEvaluationInitializationReceipt =
        read_json(workspace.join(INITIALIZATION_FILE))?;
    let expected = FinalEvaluationInitializationReceipt {
        schema_version: INITIALIZATION_SCHEMA_VERSION,
        purpose: FINAL_EVALUATION_PURPOSE.to_owned(),
        config_sha256: config_sha256.to_owned(),
        frozen_config_sha256: hash_file(&layout.frozen_config_path)?,
        source_phase3_workspace_path: source.workspace_path,
        source_phase3_initialization_sha256: source.initialization_sha256,
        source_phase3_frozen_config_sha256: source.frozen_config_sha256,
        source_phase3_runner_binding_sha256: source.runner_binding_sha256,
        source_phase3_session_sha256: source.session_sha256,
        source_phase3_launch_sha256: source.launch_sha256,
        source_phase3_oracle_cache_identity: source.oracle_cache_identity,
        representation_version: source.representation_version,
        source_representation_metadata_sha256: source.representation_metadata_sha256,
        source_model_metadata_sha256: source.model_metadata_sha256,
        created_unix_time_ns: receipt.created_unix_time_ns,
    };
    if receipt != expected
        || hash_file(config_path)? != config_sha256
        || fs::read(config_path).map_err(|source| io_error("read", config_path, source))?
            != fs::read(&layout.frozen_config_path)
                .map_err(|source| io_error("read", &layout.frozen_config_path, source))?
    {
        return Err(Error::ExperimentState(
            "Phase 4 initialized workspace or immutable Phase 3 source changed".to_owned(),
        ));
    }
    Ok(())
}

#[derive(Eq, PartialEq)]
struct SourceIdentity {
    workspace_path: PathBuf,
    initialization_sha256: String,
    frozen_config_sha256: String,
    runner_binding_sha256: String,
    session_sha256: String,
    launch_sha256: String,
    oracle_cache_identity: String,
    representation_version: String,
    representation_metadata_sha256: String,
    model_metadata_sha256: String,
}

#[derive(Deserialize)]
struct SourcePhase3InitializationReceipt {
    schema_version: u32,
    purpose: String,
    config_sha256: String,
    frozen_config_sha256: String,
    runner_binding_sha256: String,
    corpus_data_sha256: String,
    ordered_event_ids_sha256: String,
    representation_version: String,
    geometry_version: String,
    represented_rows: u64,
    dimensions: u32,
    source_representation_metadata_sha256: String,
    source_model_metadata_sha256: String,
}

#[derive(Deserialize)]
struct SourcePhase3LaunchReceipt {
    schema_version: u32,
    purpose: String,
    config_sha256: String,
    initialization_sha256: String,
    runner_binding_sha256: String,
    controller_image_id: String,
    container_name: String,
    session_path: PathBuf,
    memory_limit_bytes: u64,
    host_memory_reserve_bytes: u64,
}

fn source_identity(config: &Phase4FinalLaunchConfig) -> Result<SourceIdentity> {
    let workspace = canonical_exact(
        &config.source_phase3_workspace_path,
        "source Phase 3 workspace",
    )?;
    require_real_directory(&workspace, "source Phase 3 workspace")?;
    let initialization = workspace.join(PHASE3_INITIALIZATION_FILE);
    let frozen_config = workspace.join(PHASE3_FROZEN_CONFIG_FILE);
    let runner_binding_path = workspace.join(PHASE3_RUNNER_BINDING_FILE);
    let session = workspace.join(PHASE3_SESSION_FILE);
    let launch = workspace.join(PHASE3_LAUNCH_FILE);
    let oracle_cache = workspace.join(format!(".{PHASE3_SESSION_FILE}.oracle-responses"));
    for (path, label) in [
        (&initialization, "source Phase 3 initialization"),
        (&frozen_config, "source Phase 3 frozen config"),
        (&runner_binding_path, "source Phase 3 runner binding"),
        (&session, "source Phase 3 session"),
        (&launch, "source Phase 3 launch"),
    ] {
        require_real_file(path, label)?;
    }
    require_real_directory(&oracle_cache, "source Phase 3 Oracle cache")?;

    let binding: Phase3RunnerBinding = read_json(&runner_binding_path)?;
    binding.runner_config().map_err(Error::ExperimentState)?;
    binding
        .initial_presentations()
        .map_err(Error::ExperimentState)?;
    if binding.session_path() != session
        || binding.corpus_path() != workspace.join(PHASE3_CORPUS_DIRECTORY)
    {
        return Err(Error::ExperimentState(
            "source Phase 3 binding does not point into the selected workspace".to_owned(),
        ));
    }
    if binding.representation_version() != config.expected_representation_version {
        return Err(Error::ExperimentState(
            "source Phase 3 binding has the wrong representation version".to_owned(),
        ));
    }
    let session_sha256 = hash_file(&session)?;
    if session_sha256 != config.source_phase3_session_sha256 {
        return Err(Error::ExperimentState(
            "source Phase 3 session does not match the exact completed session SHA-256".to_owned(),
        ));
    }

    let representation_source =
        canonical_exact(&config.source_representation_path, "source representation")?;
    let model_source = canonical_exact(&config.source_model_bundle_path, "source model bundle")?;
    let representation_metadata_sha256 =
        immutable_tree_metadata_fingerprint(&representation_source)?;
    let model_metadata_sha256 = immutable_tree_metadata_fingerprint(&model_source)?;
    let representation_view = workspace.join(PHASE3_REPRESENTATION_DIRECTORY);
    require_real_file(
        &representation_view.join("manifest.json"),
        "Phase 3 representation manifest",
    )?;
    require_real_file(
        &representation_view.join("verification.json"),
        "Phase 3 representation verification",
    )?;
    let shards = canonical_exact(
        &representation_view.join("shards"),
        "Phase 3 representation shards",
    )?;
    let index = canonical_exact(
        &representation_view.join("index"),
        "Phase 3 representation index",
    )?;
    if shards != representation_source.join("shards")
        || index != representation_source.join("index")
    {
        return Err(Error::ExperimentState(
            "source representation does not own the Phase 3 representation view".to_owned(),
        ));
    }
    require_real_file(
        &workspace.join(PHASE3_ORDERED_EVENT_IDS_FILE),
        "source Phase 3 ordered event IDs",
    )?;
    require_real_file(
        &workspace.join(PHASE3_CORPUS_DIRECTORY).join("data.mdb"),
        "source Phase 3 corpus",
    )?;
    let manifest_path = representation_view.join("manifest.json");
    let manifest: RepresentationManifest = read_json(&manifest_path)?;
    let representation_version = hash_file(&manifest_path)?;
    if representation_version != config.expected_representation_version
        || manifest.descriptor.model_lock_sha256
            != hash_file(&model_source.join("model-lock.json"))?
    {
        return Err(Error::ExperimentState(
            "source representation or model does not match the Phase 4 config".to_owned(),
        ));
    }
    let initialization_sha256 = hash_file(&initialization)?;
    let frozen_config_sha256 = hash_file(&frozen_config)?;
    let runner_binding_sha256 = hash_file(&runner_binding_path)?;
    let launch_sha256 = hash_file(&launch)?;
    let phase3_config = read_learning_launch_config(&frozen_config)?;
    let phase3_initialization: SourcePhase3InitializationReceipt = read_json(&initialization)?;
    let phase3_launch: SourcePhase3LaunchReceipt = read_json(&launch)?;
    if phase3_initialization.schema_version != 1
        || phase3_initialization.purpose != HUMAN_LEARNING_PURPOSE
        || phase3_initialization.config_sha256 != frozen_config_sha256
        || phase3_initialization.frozen_config_sha256 != frozen_config_sha256
        || phase3_initialization.runner_binding_sha256 != runner_binding_sha256
        || phase3_initialization.corpus_data_sha256 != manifest.corpus_data_sha256
        || phase3_initialization.ordered_event_ids_sha256 != manifest.ordered_event_ids_sha256
        || phase3_initialization.representation_version != representation_version
        || phase3_initialization.geometry_version != binding.geometry_version()
        || phase3_initialization.represented_rows != manifest.completed_rows
        || phase3_initialization.dimensions != manifest.descriptor.dimensions
        || phase3_initialization.source_representation_metadata_sha256
            != representation_metadata_sha256
        || phase3_initialization.source_model_metadata_sha256 != model_metadata_sha256
        || binding.corpus_identity()
            != format!("sha256:{}", phase3_initialization.corpus_data_sha256)
        || canonical_exact(
            phase3_config.workspace_path(),
            "Phase 3 configured workspace",
        )? != workspace
        || canonical_exact(
            phase3_config.source_representation_path(),
            "Phase 3 configured representation",
        )? != representation_source
        || canonical_exact(
            phase3_config.model_bundle_path(),
            "Phase 3 configured model bundle",
        )? != model_source
        || phase3_config.expected_representation_version() != representation_version
        || phase3_config.expected_geometry_version() != binding.geometry_version()
    {
        return Err(Error::ExperimentState(
            "source Phase 3 initialization does not bind its selected artifacts".to_owned(),
        ));
    }
    if phase3_launch.schema_version != 1
        || phase3_launch.purpose != HUMAN_LEARNING_PURPOSE
        || phase3_launch.config_sha256 != frozen_config_sha256
        || phase3_launch.initialization_sha256 != initialization_sha256
        || phase3_launch.runner_binding_sha256 != runner_binding_sha256
        || phase3_launch.controller_image_id != phase3_config.controller_image()
        || phase3_launch.container_name != phase3_config.container_name()
        || phase3_launch.session_path != session
        || phase3_launch.memory_limit_bytes < MINIMUM_LEARNING_MEMORY_BYTES
        || !phase3_launch.memory_limit_bytes.is_multiple_of(GIB)
        || phase3_launch.host_memory_reserve_bytes != PHASE3_HOST_MEMORY_RESERVE_BYTES
    {
        return Err(Error::ExperimentState(
            "source Phase 3 launch does not bind its completed session".to_owned(),
        ));
    }

    Ok(SourceIdentity {
        workspace_path: workspace,
        initialization_sha256,
        frozen_config_sha256,
        runner_binding_sha256,
        session_sha256,
        launch_sha256,
        oracle_cache_identity: immutable_content_tree_identity(oracle_cache)?,
        representation_version,
        representation_metadata_sha256,
        model_metadata_sha256,
    })
}

fn prepared_layout(
    workspace_path: PathBuf,
    source_phase3_workspace_path: PathBuf,
    created: bool,
) -> PreparedFinalEvaluationWorkspace {
    let source_phase3_runner_binding_path =
        source_phase3_workspace_path.join(PHASE3_RUNNER_BINDING_FILE);
    let corpus_path = workspace_path.join(CORPUS_DIRECTORY);
    let ordered_event_ids_path = workspace_path.join(ORDERED_EVENT_IDS_FILE);
    let representation_path = workspace_path.join(REPRESENTATION_DIRECTORY);
    let frozen_config_path = workspace_path.join(FROZEN_CONFIG_FILE);
    let session_path = workspace_path.join(SESSION_FILE);
    let orders_path = workspace_path.join(ORDERS_FILE);
    let report_path = workspace_path.join(REPORT_FILE);
    let oracle_cache_path = workspace_path.join(format!(".{SESSION_FILE}.oracle-responses"));
    let launch_receipt_path = workspace_path.join(LAUNCH_RECEIPT_FILE);
    PreparedFinalEvaluationWorkspace {
        workspace_path,
        source_phase3_runner_binding_path,
        corpus_path,
        ordered_event_ids_path,
        representation_path,
        frozen_config_path,
        session_path,
        orders_path,
        report_path,
        oracle_cache_path,
        launch_receipt_path,
        created,
    }
}

pub fn bind_final_evaluation_launch(
    prepared: &PreparedFinalEvaluationWorkspace,
    config: &Phase4FinalLaunchConfig,
    controller_image_id: &str,
    memory_limit_bytes: u64,
) -> Result<FinalEvaluationLaunchReceipt> {
    config.validate()?;
    require_image_id(controller_image_id)?;
    if memory_limit_bytes < MINIMUM_FINAL_EVALUATION_MEMORY_BYTES
        || !memory_limit_bytes.is_multiple_of(GIB)
    {
        return Err(Error::ExperimentState(
            "Phase 4 launch memory ceiling must be a whole-GiB proven envelope".to_owned(),
        ));
    }
    let initialization_path = prepared.workspace_path.join(INITIALIZATION_FILE);
    require_private_file(&initialization_path, "Phase 4 initialization receipt")?;
    let initialization: FinalEvaluationInitializationReceipt = read_json(&initialization_path)?;
    let expected = FinalEvaluationLaunchReceipt {
        schema_version: LAUNCH_SCHEMA_VERSION,
        purpose: FINAL_EVALUATION_PURPOSE.to_owned(),
        config_sha256: initialization.config_sha256,
        initialization_sha256: hash_file(&initialization_path)?,
        controller_image_id: controller_image_id.to_owned(),
        container_name: config.container_name.clone(),
        session_path: prepared.session_path.clone(),
        orders_path: prepared.orders_path.clone(),
        report_path: prepared.report_path.clone(),
        memory_limit_bytes,
        host_memory_reserve_bytes: config.host_memory_reserve_bytes,
    };
    match fs::symlink_metadata(&prepared.launch_receipt_path) {
        Ok(_) => {
            let actual =
                read_final_evaluation_launch_receipt(prepared, config)?.ok_or_else(|| {
                    Error::Invariant("existing Phase 4 launch receipt disappeared".to_owned())
                })?;
            if actual != expected {
                return Err(Error::ExperimentState(
                    "existing Phase 4 launch receipt binds a different guarded run".to_owned(),
                ));
            }
            Ok(actual)
        }
        Err(error) if error.kind() == io::ErrorKind::NotFound => {
            if controller_image_id != config.controller_image {
                return Err(Error::ExperimentState(
                    "resolved Phase 4 controller image differs from the exact configured image ID"
                        .to_owned(),
                ));
            }
            require_pristine_first_launch(prepared)?;
            write_private_json_atomic(&prepared.launch_receipt_path, &expected)?;
            Ok(expected)
        }
        Err(source) => Err(io_error("inspect", &prepared.launch_receipt_path, source)),
    }
}

pub fn read_final_evaluation_launch_receipt(
    prepared: &PreparedFinalEvaluationWorkspace,
    config: &Phase4FinalLaunchConfig,
) -> Result<Option<FinalEvaluationLaunchReceipt>> {
    match fs::symlink_metadata(&prepared.launch_receipt_path) {
        Err(error) if error.kind() == io::ErrorKind::NotFound => return Ok(None),
        Err(source) => return Err(io_error("inspect", &prepared.launch_receipt_path, source)),
        Ok(_) => {}
    }
    require_private_file(&prepared.launch_receipt_path, "Phase 4 launch receipt")?;
    let receipt_bytes = fs::read(&prepared.launch_receipt_path)
        .map_err(|source| io_error("read", &prepared.launch_receipt_path, source))?;
    let receipt: FinalEvaluationLaunchReceipt =
        serde_json::from_slice(&receipt_bytes).map_err(|source| Error::Manifest {
            operation: "decode",
            path: prepared.launch_receipt_path.clone(),
            source,
        })?;
    let mut canonical = serde_json::to_vec_pretty(&receipt).map_err(|source| Error::Manifest {
        operation: "encode",
        path: prepared.launch_receipt_path.clone(),
        source,
    })?;
    canonical.push(b'\n');
    let initialization_path = prepared.workspace_path.join(INITIALIZATION_FILE);
    let initialization: FinalEvaluationInitializationReceipt = read_json(&initialization_path)?;
    if receipt_bytes != canonical
        || receipt.schema_version != LAUNCH_SCHEMA_VERSION
        || receipt.purpose != FINAL_EVALUATION_PURPOSE
        || receipt.config_sha256 != initialization.config_sha256
        || receipt.initialization_sha256 != hash_file(&initialization_path)?
        || receipt.controller_image_id != config.controller_image
        || receipt.container_name != config.container_name
        || receipt.session_path != prepared.session_path
        || receipt.orders_path != prepared.orders_path
        || receipt.report_path != prepared.report_path
        || receipt.host_memory_reserve_bytes != HOST_MEMORY_RESERVE_BYTES
        || receipt.memory_limit_bytes < MINIMUM_FINAL_EVALUATION_MEMORY_BYTES
        || !receipt.memory_limit_bytes.is_multiple_of(GIB)
    {
        return Err(Error::ExperimentState(
            "Phase 4 launch receipt does not match the initialized final evaluation".to_owned(),
        ));
    }
    Ok(Some(receipt))
}

pub fn final_evaluation_launch_identity(
    prepared: &PreparedFinalEvaluationWorkspace,
) -> Result<String> {
    require_private_file(&prepared.launch_receipt_path, "Phase 4 launch receipt")?;
    hash_file(&prepared.launch_receipt_path)
}

/// Replay the immutable completed Phase 3 handoff and run the guarded Phase 4
/// evaluator over the disposable Phase 4 corpus.
pub fn run_prepared_final_evaluation_tui<E>(
    prepared: &PreparedFinalEvaluationWorkspace,
    config: &Phase4FinalLaunchConfig,
    encoder: E,
) -> Result<FinalEvaluationRunnerOutcome>
where
    E: RepresentationEncoder,
{
    let (completed, runner_config) = prepared_final_evaluation_inputs(prepared, config)?;
    let mut oracle = Fp32OfflineOracle::open(
        &prepared.corpus_path,
        &prepared.ordered_event_ids_path,
        &prepared.representation_path,
        encoder,
    )?;
    run_final_evaluation_tui(&runner_config, completed, &mut oracle)
}

/// Resume Phase 4 solely from the frozen order/cache and completed Phase 3
/// handoff. This deliberately does not construct an embedding encoder or open
/// the full FP32 matrix.
pub fn resume_prepared_final_evaluation_tui(
    prepared: &PreparedFinalEvaluationWorkspace,
    config: &Phase4FinalLaunchConfig,
) -> Result<FinalEvaluationRunnerOutcome> {
    let (completed, runner_config) = prepared_final_evaluation_inputs(prepared, config)?;
    resume_final_evaluation_tui(&runner_config, completed)
}

fn prepared_final_evaluation_inputs(
    prepared: &PreparedFinalEvaluationWorkspace,
    config: &Phase4FinalLaunchConfig,
) -> Result<(Box<CompletedAdaptiveLearning>, FinalEvaluationRunnerConfig)> {
    require_bound_final_evaluation_run(prepared, config)?;
    let guarded_launch_identity_sha256 = final_evaluation_launch_identity(prepared)?;
    let binding: Phase3RunnerBinding = read_json(&prepared.source_phase3_runner_binding_path)?;
    let replay_config = binding.runner_config().map_err(Error::ExperimentState)?;
    let initial_presentations = binding
        .initial_presentations()
        .map_err(Error::ExperimentState)?;
    let completed = replay_completed_adaptive_learning(&replay_config, &initial_presentations)?;
    let runner_config = FinalEvaluationRunnerConfig {
        corpus_path: prepared.corpus_path.clone(),
        corpus_identity: binding.corpus_identity().to_owned(),
        session_path: prepared.session_path.clone(),
        frozen_orders_path: prepared.orders_path.clone(),
        report_path: prepared.report_path.clone(),
        oracle_cache_path: prepared.oracle_cache_path.clone(),
        phase3_handoff_identity_sha256: config.source_phase3_session_sha256.clone(),
        guarded_launch_identity_sha256,
        geometry_version: binding.geometry_version().to_owned(),
    };
    Ok((completed, runner_config))
}

fn require_bound_final_evaluation_run(
    prepared: &PreparedFinalEvaluationWorkspace,
    config: &Phase4FinalLaunchConfig,
) -> Result<FinalEvaluationLaunchReceipt> {
    read_final_evaluation_launch_receipt(prepared, config)?.ok_or_else(|| {
        Error::ExperimentState("Phase 4 workspace has no frozen guarded launch receipt".to_owned())
    })
}

pub fn derive_final_evaluation_memory_limit(
    available_bytes: u64,
    swap_used_bytes: u64,
    reserve_bytes: u64,
) -> Result<u64> {
    derive_learning_memory_limit(available_bytes, swap_used_bytes, reserve_bytes)
}

pub fn read_final_evaluation_host_memory_snapshot(
    path: impl AsRef<Path>,
) -> Result<HostMemorySnapshot> {
    read_host_memory_snapshot(path)
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum FinalEvaluationContainerState {
    Absent,
    Running,
    Stopped,
}

pub fn inspect_final_evaluation_container(
    container_runtime: impl AsRef<Path>,
    container_name: &str,
    launch_identity_sha256: &str,
    controller_image_id: &str,
) -> Result<FinalEvaluationContainerState> {
    validate_container_name(container_name)?;
    require_sha256(launch_identity_sha256, "Phase 4 launch identity")?;
    require_image_id(controller_image_id)?;
    let runtime = canonical_exact(container_runtime.as_ref(), "container runtime")?;
    let format =
        "{{.State.Running}}\n{{index .Config.Labels \"io.notedeck.phase4.launch\"}}\n{{.Image}}";
    let inspection = Command::new(&runtime)
        .args(["container", "inspect", "--format", format, container_name])
        .output()
        .map_err(|source| io_error("execute", &runtime, source))?;
    if inspection.status.success() {
        let output = String::from_utf8(inspection.stdout).map_err(|_| {
            Error::ExperimentState("container runtime returned non-UTF-8 Phase 4 state".to_owned())
        })?;
        let lines = output.lines().collect::<Vec<_>>();
        if lines.len() != 3 || lines[1] != launch_identity_sha256 || lines[2] != controller_image_id
        {
            return Err(Error::ExperimentState(
                "same-name container does not match the frozen Phase 4 launch".to_owned(),
            ));
        }
        return match lines[0] {
            "true" => Ok(FinalEvaluationContainerState::Running),
            "false" => Ok(FinalEvaluationContainerState::Stopped),
            _ => Err(Error::ExperimentState(
                "container runtime returned an invalid Phase 4 running state".to_owned(),
            )),
        };
    }
    let exact_name = format!("name=^/{container_name}$");
    let listing = Command::new(&runtime)
        .args([
            "container",
            "ls",
            "--all",
            "--quiet",
            "--filter",
            &exact_name,
        ])
        .output()
        .map_err(|source| io_error("execute", &runtime, source))?;
    if !listing.status.success() {
        return Err(Error::ExperimentState(format!(
            "container runtime could not inspect Phase 4 controller: {}",
            String::from_utf8_lossy(&listing.stderr).trim()
        )));
    }
    if listing.stdout.iter().all(u8::is_ascii_whitespace) {
        Ok(FinalEvaluationContainerState::Absent)
    } else {
        Err(Error::ExperimentState(
            "container runtime found the Phase 4 name but could not verify its identity".to_owned(),
        ))
    }
}

pub fn final_evaluation_attach_arguments(container_name: &str) -> Vec<OsString> {
    [
        "attach".into(),
        "--detach-keys=ctrl-]".into(),
        container_name.into(),
    ]
    .into_iter()
    .collect()
}

#[allow(clippy::too_many_arguments)]
pub fn final_evaluation_container_arguments(
    container_name: &str,
    controller_image: &str,
    launch_identity_sha256: &str,
    memory_limit_bytes: u64,
    user_id: u32,
    group_id: u32,
    readonly_inputs: &[PathBuf],
    workspace: &Path,
    frozen_config: &Path,
) -> Result<Vec<OsString>> {
    validate_container_name(container_name)?;
    require_image_id(controller_image)?;
    require_sha256(launch_identity_sha256, "Phase 4 launch identity")?;
    if memory_limit_bytes < MINIMUM_FINAL_EVALUATION_MEMORY_BYTES {
        return Err(Error::ExperimentState(
            "Phase 4 container limit is below the proven 67 GiB envelope".to_owned(),
        ));
    }
    if readonly_inputs.is_empty() {
        return Err(Error::ExperimentState(
            "Phase 4 has no immutable input mounts".to_owned(),
        ));
    }
    let workspace = canonical_exact(workspace, "Phase 4 workspace")?;
    if !workspace.is_dir() {
        return Err(Error::ExperimentState(format!(
            "Phase 4 workspace is not a directory: `{}`",
            workspace.display()
        )));
    }
    let frozen_config = canonical_exact(frozen_config, "Phase 4 frozen config")?;
    if !frozen_config.is_file() || !frozen_config.starts_with(&workspace) {
        return Err(Error::ExperimentState(
            "Phase 4 frozen config must be a file inside its private workspace".to_owned(),
        ));
    }
    let mut readonly = Vec::with_capacity(readonly_inputs.len());
    for input in readonly_inputs {
        let input = canonical_exact(input, "Phase 4 immutable input")?;
        if input.starts_with(&workspace) || workspace.starts_with(&input) {
            return Err(Error::ExperimentState(format!(
                "Phase 4 immutable input `{}` overlaps private workspace `{}`",
                input.display(),
                workspace.display()
            )));
        }
        readonly.push(input);
    }
    let mut arguments = vec![
        "run".into(),
        "--rm".into(),
        "--name".into(),
        container_name.into(),
        format!("--label=io.notedeck.phase4.launch={launch_identity_sha256}").into(),
        "--pull=never".into(),
        "--interactive".into(),
        "--tty".into(),
        "--detach-keys=ctrl-]".into(),
        "--network=none".into(),
        "--read-only".into(),
        format!("--memory={memory_limit_bytes}").into(),
        format!("--memory-swap={memory_limit_bytes}").into(),
        "--pids-limit=4096".into(),
        "--shm-size=1g".into(),
        format!(
            "--tmpfs=/runtime-tmp:rw,noexec,nosuid,nodev,size=1g,uid={user_id},gid={group_id},mode=0700"
        )
        .into(),
        format!(
            "--tmpfs=/runtime-home:rw,nosuid,nodev,size=2g,uid={user_id},gid={group_id},mode=0700"
        )
        .into(),
        format!("--user={user_id}:{group_id}").into(),
        "--env=HOME=/runtime-home".into(),
        "--env=TMPDIR=/runtime-tmp".into(),
        "--env=PYTHONDONTWRITEBYTECODE=1".into(),
        "--env=HF_HUB_OFFLINE=1".into(),
        "--env=TRANSFORMERS_OFFLINE=1".into(),
        "--env=TOKENIZERS_PARALLELISM=false".into(),
    ];
    for input in readonly {
        arguments.push("--mount".into());
        arguments.push(readonly_mount(&input).into());
    }
    arguments.push("--mount".into());
    arguments.push(writable_mount(&workspace).into());
    arguments.push(controller_image.into());
    arguments.push("__run".into());
    arguments.push(frozen_config.into_os_string());
    Ok(arguments)
}

pub fn resolve_final_evaluation_controller_image_id(
    container_runtime: impl AsRef<Path>,
    controller_image_reference: &str,
) -> Result<String> {
    resolve_controller_image_id(container_runtime, controller_image_reference)
}

fn require_pristine_first_launch(prepared: &PreparedFinalEvaluationWorkspace) -> Result<()> {
    for path in [
        &prepared.session_path,
        &prepared.orders_path,
        &prepared.report_path,
        &prepared.oracle_cache_path,
    ] {
        match fs::symlink_metadata(path) {
            Err(error) if error.kind() == io::ErrorKind::NotFound => {}
            Err(source) => return Err(io_error("inspect", path, source)),
            Ok(_) => {
                return Err(Error::ExperimentState(format!(
                    "Phase 4 launch receipt is missing but prior evaluator state exists at `{}`",
                    path.display()
                )));
            }
        }
    }
    Ok(())
}

fn resolve_workspace_path(path: &Path) -> Result<PathBuf> {
    require_absolute_normalized(path, "Phase 4 workspace")?;
    let parent = path
        .parent()
        .ok_or_else(|| Error::Invariant("Phase 4 workspace has no parent".to_owned()))?;
    let parent = canonical_exact(parent, "Phase 4 workspace parent")?;
    let name = path
        .file_name()
        .ok_or_else(|| Error::Invariant("Phase 4 workspace has no file name".to_owned()))?;
    reject_unsafe_mount_path(&parent.join(name), "Phase 4 workspace")
}

fn canonical_exact(path: &Path, label: &str) -> Result<PathBuf> {
    let canonical = fs::canonicalize(path).map_err(|source| io_error("resolve", path, source))?;
    reject_unsafe_mount_path(&canonical, label)
}

fn reject_unsafe_mount_path(path: &Path, label: &str) -> Result<PathBuf> {
    require_absolute_normalized(path, label)?;
    if path == Path::new("/") {
        return Err(Error::ExperimentState(format!(
            "{label} cannot be the filesystem root"
        )));
    }
    Ok(path.to_owned())
}

fn create_owner_only_directory(path: &Path) -> Result<()> {
    fs::create_dir(path).map_err(|source| io_error("create", path, source))?;
    fs::set_permissions(path, fs::Permissions::from_mode(0o700))
        .map_err(|source| io_error("set permissions on", path, source))
}

fn copy_private_file(source: &Path, destination: &Path) -> Result<()> {
    let mut input = File::open(source).map_err(|error| io_error("open", source, error))?;
    let mut output = OpenOptions::new()
        .write(true)
        .create_new(true)
        .mode(0o600)
        .open(destination)
        .map_err(|error| io_error("create", destination, error))?;
    {
        let mut writer = BufWriter::new(&mut output);
        io::copy(&mut input, &mut writer).map_err(|error| io_error("copy", destination, error))?;
        writer
            .flush()
            .map_err(|error| io_error("flush", destination, error))?;
    }
    output
        .sync_all()
        .map_err(|error| io_error("sync", destination, error))
}

fn require_private_directory(path: &Path, label: &str) -> Result<()> {
    let metadata =
        fs::symlink_metadata(path).map_err(|source| io_error("inspect", path, source))?;
    if metadata.file_type().is_symlink()
        || !metadata.is_dir()
        || metadata.uid() != unsafe { libc::geteuid() }
        || metadata.mode() & 0o077 != 0
    {
        return Err(Error::ExperimentState(format!(
            "{label} must be a real owner-only directory"
        )));
    }
    Ok(())
}

fn require_private_file(path: &Path, label: &str) -> Result<()> {
    let metadata =
        fs::symlink_metadata(path).map_err(|source| io_error("inspect", path, source))?;
    if metadata.file_type().is_symlink()
        || !metadata.is_file()
        || metadata.uid() != unsafe { libc::geteuid() }
        || metadata.mode() & 0o077 != 0
    {
        return Err(Error::ExperimentState(format!(
            "{label} must be a real owner-only file"
        )));
    }
    Ok(())
}

fn require_optional_private_file(path: &Path, label: &str) -> Result<()> {
    match fs::symlink_metadata(path) {
        Err(error) if error.kind() == io::ErrorKind::NotFound => Ok(()),
        Err(source) => Err(io_error("inspect", path, source)),
        Ok(_) => require_private_file(path, label),
    }
}

fn require_optional_private_directory(path: &Path, label: &str) -> Result<()> {
    match fs::symlink_metadata(path) {
        Err(error) if error.kind() == io::ErrorKind::NotFound => Ok(()),
        Err(source) => Err(io_error("inspect", path, source)),
        Ok(_) => require_private_directory(path, label),
    }
}

fn require_real_file(path: &Path, label: &str) -> Result<()> {
    let metadata =
        fs::symlink_metadata(path).map_err(|source| io_error("inspect", path, source))?;
    if metadata.file_type().is_symlink() || !metadata.is_file() {
        return Err(Error::ExperimentState(format!(
            "{label} must be a real file"
        )));
    }
    Ok(())
}

fn require_real_directory(path: &Path, label: &str) -> Result<()> {
    let metadata =
        fs::symlink_metadata(path).map_err(|source| io_error("inspect", path, source))?;
    if metadata.file_type().is_symlink() || !metadata.is_dir() {
        return Err(Error::ExperimentState(format!(
            "{label} must be a real directory"
        )));
    }
    Ok(())
}

fn read_json<T: for<'de> Deserialize<'de>>(path: impl AsRef<Path>) -> Result<T> {
    let path = path.as_ref();
    let input = File::open(path).map_err(|source| io_error("open", path, source))?;
    serde_json::from_reader(BufReader::new(input)).map_err(|source| Error::Manifest {
        operation: "decode",
        path: path.to_owned(),
        source,
    })
}

fn unix_time_ns() -> Result<u128> {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|duration| duration.as_nanos())
        .map_err(|error| Error::Invariant(format!("system clock is before UNIX epoch: {error}")))
}

fn io_error(operation: &'static str, path: impl AsRef<Path>, source: io::Error) -> Error {
    Error::Io {
        operation,
        path: path.as_ref().to_owned(),
        source,
    }
}

fn validate_container_name(name: &str) -> Result<()> {
    if name.is_empty()
        || name.len() > 128
        || !name
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'_' | b'.'))
    {
        return Err(Error::ExperimentState(
            "Phase 4 container name is invalid".to_owned(),
        ));
    }
    Ok(())
}

fn require_absolute_normalized(path: &Path, label: &str) -> Result<()> {
    if !path.is_absolute()
        || path
            .components()
            .any(|component| !matches!(component, Component::RootDir | Component::Normal(_)))
    {
        return Err(Error::ExperimentState(format!(
            "{label} must be an absolute normalized path"
        )));
    }
    Ok(())
}

fn require_sha256(value: &str, label: &str) -> Result<()> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err(Error::ExperimentState(format!(
            "{label} must be a lowercase SHA-256"
        )));
    }
    Ok(())
}

fn require_image_id(value: &str) -> Result<()> {
    let Some(digest) = value.strip_prefix("sha256:") else {
        return Err(Error::ExperimentState(
            "Phase 4 controller image must be an exact image ID".to_owned(),
        ));
    };
    require_sha256(digest, "Phase 4 controller image")
}

fn readonly_mount(path: &Path) -> String {
    format!(
        "type=bind,src={},dst={},readonly",
        path.display(),
        path.display()
    )
}

fn writable_mount(path: &Path) -> String {
    format!("type=bind,src={},dst={}", path.display(), path.display())
}
