//! Host-side safety planning for the real full-corpus Phase 3 learning run.

use std::ffi::OsString;
use std::fs;
use std::fs::{File, OpenOptions};
use std::io::{self, BufReader, BufWriter, Write};
use std::os::unix::fs::{MetadataExt, OpenOptionsExt, PermissionsExt};
use std::path::{Component, Path, PathBuf};
use std::process::Command;
use std::time::{SystemTime, UNIX_EPOCH};

use nostrdb::Transaction;
use serde::{Deserialize, Serialize};

use crate::adaptive_learning_runner::{
    AdaptiveLearningRunnerOutcome, run_adaptive_learning_tui_with_initial_presentations,
    run_adaptive_learning_with_initial_presentations,
};
use crate::artifact::hash_file;
use crate::evaluator::EvaluatorUi;
use crate::fp32_oracle::Fp32OfflineOracle;
use crate::phase3_binding::{
    Phase3InitialPresentationBinding, Phase3RunnerBinding, Phase3SeedBinding,
};
use crate::phase3_cost_preflight::{
    create_private_preflight_directory, immutable_content_tree_identity,
    immutable_tree_metadata_fingerprint, prepare_disposable_representation_view,
    write_private_json_atomic,
};
use crate::phase3_seed_selection::{
    Phase3SeedSelectionHandoff, read_phase3_seed_selection_handoff,
};
use crate::representation::{RepresentationEncoder, verify_representation};
use crate::representation_geometry::open_representation_geometry;
use crate::snapshot::{Error, Result, Validation, ndb_error, open_existing_ndb};

const GIB: u64 = 1024 * 1024 * 1024;
const LEGACY_CONFIG_SCHEMA_VERSION: u32 = 1;
const CONFIG_SCHEMA_VERSION: u32 = 2;
const INITIALIZATION_SCHEMA_VERSION: u32 = 1;
const INITIALIZATION_FILE: &str = "initialization.json";
const FROZEN_CONFIG_FILE: &str = "frozen-config.json";
const RUNNER_BINDING_FILE: &str = "runner-binding.json";
const CORPUS_DIRECTORY: &str = "corpus.ndb";
const ORDERED_EVENT_IDS_FILE: &str = "ordered-event-ids.bin";
const REPRESENTATION_DIRECTORY: &str = "representation";
const SESSION_FILE: &str = "phase3-session.json";
const LAUNCH_RECEIPT_FILE: &str = "launch.json";
const SEED_SELECTION_HANDOFF_FILE: &str = "seed-selection-handoff.json";
const LAUNCH_SCHEMA_VERSION: u32 = 1;

pub const HUMAN_LEARNING_PURPOSE: &str = "human-phase3-learning-v1";
pub const HOST_MEMORY_RESERVE_BYTES: u64 = 12 * GIB;

/// The smallest combined controller-and-worker envelope proven by CREC-90.
pub const MINIMUM_LEARNING_MEMORY_BYTES: u64 = 67 * GIB;

#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Phase3LearningLaunchConfig {
    schema_version: u32,
    purpose: String,
    workspace_path: PathBuf,
    source_corpus_data_path: PathBuf,
    source_ordered_event_ids_path: PathBuf,
    source_representation_path: PathBuf,
    source_geometry_path: PathBuf,
    model_bundle_path: PathBuf,
    container_runtime: PathBuf,
    container_name: String,
    controller_image: String,
    expected_representation_version: String,
    expected_geometry_version: String,
    host_memory_reserve_bytes: u64,
    #[serde(default)]
    seeds: Vec<Phase3SeedBinding>,
    #[serde(default)]
    seed_selection_handoff_path: Option<PathBuf>,
}

impl Phase3LearningLaunchConfig {
    pub fn workspace_path(&self) -> &Path {
        &self.workspace_path
    }

    pub fn source_corpus_data_path(&self) -> &Path {
        &self.source_corpus_data_path
    }

    pub fn source_ordered_event_ids_path(&self) -> &Path {
        &self.source_ordered_event_ids_path
    }

    pub fn source_representation_path(&self) -> &Path {
        &self.source_representation_path
    }

    pub fn source_geometry_path(&self) -> &Path {
        &self.source_geometry_path
    }

    pub fn model_bundle_path(&self) -> &Path {
        &self.model_bundle_path
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

    pub fn expected_representation_version(&self) -> &str {
        &self.expected_representation_version
    }

    pub fn expected_geometry_version(&self) -> &str {
        &self.expected_geometry_version
    }

    pub const fn host_memory_reserve_bytes(&self) -> u64 {
        self.host_memory_reserve_bytes
    }

    pub fn seeds(&self) -> &[Phase3SeedBinding] {
        &self.seeds
    }

    pub fn seed_selection_handoff_path(&self) -> Option<&Path> {
        self.seed_selection_handoff_path.as_deref()
    }

    fn validate(&self) -> Result<()> {
        if !matches!(
            self.schema_version,
            LEGACY_CONFIG_SCHEMA_VERSION | CONFIG_SCHEMA_VERSION
        ) {
            return Err(Error::ExperimentState(
                "Phase 3 learning config has the wrong schema".to_owned(),
            ));
        }
        if self.purpose != HUMAN_LEARNING_PURPOSE {
            return Err(Error::ExperimentState(
                "Phase 3 learning config is not a human evaluation config".to_owned(),
            ));
        }
        if self.host_memory_reserve_bytes != HOST_MEMORY_RESERVE_BYTES {
            return Err(Error::ExperimentState(
                "Phase 3 learning config must preserve the approved 12 GiB host reserve".to_owned(),
            ));
        }
        for (label, path) in [
            ("workspace", self.workspace_path.as_path()),
            ("source corpus", self.source_corpus_data_path.as_path()),
            (
                "source ordered event IDs",
                self.source_ordered_event_ids_path.as_path(),
            ),
            (
                "source representation",
                self.source_representation_path.as_path(),
            ),
            ("source geometry", self.source_geometry_path.as_path()),
            ("model bundle", self.model_bundle_path.as_path()),
            ("container runtime", self.container_runtime.as_path()),
        ] {
            require_absolute_normalized(path, label)?;
        }
        if let Some(path) = &self.seed_selection_handoff_path {
            require_absolute_normalized(path, "seed-selection handoff")?;
        }
        for source in [
            &self.source_corpus_data_path,
            &self.source_ordered_event_ids_path,
            &self.source_representation_path,
            &self.source_geometry_path,
            &self.model_bundle_path,
        ] {
            if source.starts_with(&self.workspace_path) || self.workspace_path.starts_with(source) {
                return Err(Error::ExperimentState(format!(
                    "Phase 3 source `{}` overlaps private workspace `{}`",
                    source.display(),
                    self.workspace_path.display()
                )));
            }
        }
        if let Some(source) = &self.seed_selection_handoff_path
            && (source.starts_with(&self.workspace_path) || self.workspace_path.starts_with(source))
        {
            return Err(Error::ExperimentState(format!(
                "Phase 3 seed-selection handoff `{}` overlaps private workspace `{}`",
                source.display(),
                self.workspace_path.display()
            )));
        }
        validate_container_name(&self.container_name)?;
        require_image_id(&self.controller_image)?;
        require_sha256(
            &self.expected_representation_version,
            "expected representation version",
        )?;
        require_sha256(&self.expected_geometry_version, "expected geometry version")?;
        if self.schema_version == LEGACY_CONFIG_SCHEMA_VERSION
            && self.seed_selection_handoff_path.is_some()
        {
            return Err(Error::ExperimentState(
                "legacy Phase 3 configs cannot reference a seed-selection handoff".to_owned(),
            ));
        }
        if self.schema_version == CONFIG_SCHEMA_VERSION
            && (self.seed_selection_handoff_path.is_none() || !self.seeds.is_empty())
        {
            return Err(Error::ExperimentState(
                "Phase 3 schema 2 requires one seed-selection handoff and no duplicated inline seeds"
                    .to_owned(),
            ));
        }
        if self.schema_version == LEGACY_CONFIG_SCHEMA_VERSION && self.seeds.len() != 5 {
            return Err(Error::ExperimentState(
                "Phase 3 requires exactly five positive seeds".to_owned(),
            ));
        }
        if self.schema_version == LEGACY_CONFIG_SCHEMA_VERSION {
            let mut event_ids = self
                .seeds
                .iter()
                .map(Phase3SeedBinding::event_id)
                .collect::<std::result::Result<Vec<_>, _>>()
                .map_err(Error::ExperimentState)?;
            event_ids.sort_unstable();
            event_ids.dedup();
            if event_ids.len() != 5
                || self
                    .seeds
                    .iter()
                    .any(|seed| !(5..=7).contains(&seed.rating()))
            {
                return Err(Error::ExperimentState(
                    "Phase 3 seeds must be five distinct positive notes rated 5 through 7"
                        .to_owned(),
                ));
            }
        }
        Ok(())
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum LearningWorkspaceState {
    Fresh,
    Initialized,
}

#[derive(Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct LearningInitializationReceipt {
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
    source_geometry_content_sha256: String,
    source_model_metadata_sha256: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    seed_selection_handoff_sha256: Option<String>,
    created_unix_time_ns: u128,
}

/// Fully verified private inputs for one real human learning session.
#[derive(Clone, Debug)]
pub struct PreparedLearningWorkspace {
    workspace_path: PathBuf,
    corpus_path: PathBuf,
    ordered_event_ids_path: PathBuf,
    representation_path: PathBuf,
    runner_binding_path: PathBuf,
    frozen_config_path: PathBuf,
    session_path: PathBuf,
    oracle_cache_path: PathBuf,
    launch_receipt_path: PathBuf,
    seed_selection_handoff_path: PathBuf,
    created: bool,
}

impl PreparedLearningWorkspace {
    pub const fn state(&self) -> LearningWorkspaceState {
        LearningWorkspaceState::Initialized
    }

    pub const fn created(&self) -> bool {
        self.created
    }

    pub fn workspace_path(&self) -> &Path {
        &self.workspace_path
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

    pub fn runner_binding_path(&self) -> &Path {
        &self.runner_binding_path
    }

    pub fn frozen_config_path(&self) -> &Path {
        &self.frozen_config_path
    }

    pub fn session_path(&self) -> &Path {
        &self.session_path
    }

    pub fn oracle_cache_path(&self) -> &Path {
        &self.oracle_cache_path
    }

    pub fn launch_receipt_path(&self) -> &Path {
        &self.launch_receipt_path
    }

    pub fn seed_selection_handoff_path(&self) -> &Path {
        &self.seed_selection_handoff_path
    }
}

/// First-launch identity that every resume must reuse exactly.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct LearningLaunchReceipt {
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

impl LearningLaunchReceipt {
    pub fn controller_image_id(&self) -> &str {
        &self.controller_image_id
    }

    pub fn container_name(&self) -> &str {
        &self.container_name
    }

    pub const fn memory_limit_bytes(&self) -> u64 {
        self.memory_limit_bytes
    }

    pub fn config_sha256(&self) -> &str {
        &self.config_sha256
    }
}

/// Atomically freeze the resolved image and safe memory ceiling on first
/// launch. A later invocation can only reuse the identical values.
pub fn bind_learning_launch(
    prepared: &PreparedLearningWorkspace,
    config: &Phase3LearningLaunchConfig,
    controller_image_id: &str,
    memory_limit_bytes: u64,
) -> Result<LearningLaunchReceipt> {
    config.validate()?;
    require_image_id(controller_image_id)?;
    if memory_limit_bytes < MINIMUM_LEARNING_MEMORY_BYTES || !memory_limit_bytes.is_multiple_of(GIB)
    {
        return Err(Error::ExperimentState(
            "Phase 3 launch memory ceiling must be a whole-GiB proven envelope".to_owned(),
        ));
    }
    let initialization_path = prepared.workspace_path.join(INITIALIZATION_FILE);
    require_private_file(&initialization_path, "Phase 3 initialization receipt")?;
    require_private_file(&prepared.runner_binding_path, "Phase 3 runner binding")?;
    let initialization: LearningInitializationReceipt = read_json(&initialization_path)?;
    let expected = LearningLaunchReceipt {
        schema_version: LAUNCH_SCHEMA_VERSION,
        purpose: HUMAN_LEARNING_PURPOSE.to_owned(),
        config_sha256: initialization.config_sha256,
        initialization_sha256: hash_file(&initialization_path)?,
        runner_binding_sha256: hash_file(&prepared.runner_binding_path)?,
        controller_image_id: controller_image_id.to_owned(),
        container_name: config.container_name.clone(),
        session_path: prepared.session_path.clone(),
        memory_limit_bytes,
        host_memory_reserve_bytes: config.host_memory_reserve_bytes,
    };
    match fs::symlink_metadata(&prepared.launch_receipt_path) {
        Ok(_) => {
            let actual = read_learning_launch_receipt(prepared, config)?.ok_or_else(|| {
                Error::Invariant("existing Phase 3 launch receipt disappeared".to_owned())
            })?;
            if !same_launch_identity(&actual, &expected) {
                return Err(Error::ExperimentState(
                    "existing Phase 3 launch receipt binds a different guarded run".to_owned(),
                ));
            }
            Ok(actual)
        }
        Err(error) if error.kind() == io::ErrorKind::NotFound => {
            if controller_image_id != config.controller_image {
                return Err(Error::ExperimentState(
                    "resolved Phase 3 controller image differs from the exact configured image ID"
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

/// Load and validate a previously frozen launch, or report that the human
/// workspace has never been launched.
pub fn read_learning_launch_receipt(
    prepared: &PreparedLearningWorkspace,
    config: &Phase3LearningLaunchConfig,
) -> Result<Option<LearningLaunchReceipt>> {
    match fs::symlink_metadata(&prepared.launch_receipt_path) {
        Err(error) if error.kind() == io::ErrorKind::NotFound => return Ok(None),
        Err(source) => {
            return Err(io_error("inspect", &prepared.launch_receipt_path, source));
        }
        Ok(_) => {}
    }
    require_private_file(&prepared.launch_receipt_path, "Phase 3 launch receipt")?;
    let receipt_bytes = fs::read(&prepared.launch_receipt_path)
        .map_err(|source| io_error("read", &prepared.launch_receipt_path, source))?;
    let receipt: LearningLaunchReceipt =
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
    if receipt_bytes != canonical {
        return Err(Error::ExperimentState(
            "Phase 3 launch receipt bytes changed after first launch".to_owned(),
        ));
    }
    require_image_id(&receipt.controller_image_id)?;
    let initialization_path = prepared.workspace_path.join(INITIALIZATION_FILE);
    let initialization: LearningInitializationReceipt = read_json(&initialization_path)?;
    if receipt.schema_version != LAUNCH_SCHEMA_VERSION
        || receipt.purpose != HUMAN_LEARNING_PURPOSE
        || receipt.config_sha256 != initialization.config_sha256
        || receipt.initialization_sha256 != hash_file(&initialization_path)?
        || receipt.runner_binding_sha256 != hash_file(&prepared.runner_binding_path)?
        || receipt.controller_image_id != config.controller_image
        || receipt.container_name != config.container_name
        || receipt.session_path != prepared.session_path
        || receipt.host_memory_reserve_bytes != HOST_MEMORY_RESERVE_BYTES
        || receipt.memory_limit_bytes < MINIMUM_LEARNING_MEMORY_BYTES
        || !receipt.memory_limit_bytes.is_multiple_of(GIB)
    {
        return Err(Error::ExperimentState(
            "Phase 3 launch receipt does not match the initialized human run".to_owned(),
        ));
    }
    Ok(Some(receipt))
}

pub fn learning_launch_identity(prepared: &PreparedLearningWorkspace) -> Result<String> {
    require_private_file(&prepared.launch_receipt_path, "Phase 3 launch receipt")?;
    hash_file(&prepared.launch_receipt_path)
}

/// Run the verified workspace through the production FP32 Oracle and adaptive
/// learner with a supplied production evaluator implementation.
pub fn run_prepared_learning<E, U>(
    prepared: &PreparedLearningWorkspace,
    config: &Phase3LearningLaunchConfig,
    encoder: E,
    evaluator: &mut U,
) -> Result<AdaptiveLearningRunnerOutcome>
where
    E: RepresentationEncoder,
    U: EvaluatorUi,
{
    require_bound_learning_run(prepared, config)?;
    let binding: Phase3RunnerBinding = read_json(&prepared.runner_binding_path)?;
    let runner_config = binding.runner_config().map_err(Error::ExperimentState)?;
    let initial_presentations = binding
        .initial_presentations()
        .map_err(Error::ExperimentState)?;
    let mut oracle = Fp32OfflineOracle::open(
        &prepared.corpus_path,
        &prepared.ordered_event_ids_path,
        &prepared.representation_path,
        encoder,
    )?;
    run_adaptive_learning_with_initial_presentations(
        &runner_config,
        &initial_presentations,
        &mut oracle,
        evaluator,
    )
}

/// Real full-screen entrypoint over the same verified production path.
pub fn run_prepared_learning_tui<E>(
    prepared: &PreparedLearningWorkspace,
    config: &Phase3LearningLaunchConfig,
    encoder: E,
) -> Result<AdaptiveLearningRunnerOutcome>
where
    E: RepresentationEncoder,
{
    require_bound_learning_run(prepared, config)?;
    let binding: Phase3RunnerBinding = read_json(&prepared.runner_binding_path)?;
    let runner_config = binding.runner_config().map_err(Error::ExperimentState)?;
    let initial_presentations = binding
        .initial_presentations()
        .map_err(Error::ExperimentState)?;
    let mut oracle = Fp32OfflineOracle::open(
        &prepared.corpus_path,
        &prepared.ordered_event_ids_path,
        &prepared.representation_path,
        encoder,
    )?;
    run_adaptive_learning_tui_with_initial_presentations(
        &runner_config,
        &initial_presentations,
        &mut oracle,
    )
}

fn require_bound_learning_run(
    prepared: &PreparedLearningWorkspace,
    config: &Phase3LearningLaunchConfig,
) -> Result<LearningLaunchReceipt> {
    read_learning_launch_receipt(prepared, config)?.ok_or_else(|| {
        Error::ExperimentState("Phase 3 workspace has no frozen guarded launch receipt".to_owned())
    })
}

fn same_launch_identity(left: &LearningLaunchReceipt, right: &LearningLaunchReceipt) -> bool {
    left.schema_version == right.schema_version
        && left.purpose == right.purpose
        && left.config_sha256 == right.config_sha256
        && left.initialization_sha256 == right.initialization_sha256
        && left.runner_binding_sha256 == right.runner_binding_sha256
        && left.controller_image_id == right.controller_image_id
        && left.container_name == right.container_name
        && left.session_path == right.session_path
        && left.memory_limit_bytes == right.memory_limit_bytes
        && left.host_memory_reserve_bytes == right.host_memory_reserve_bytes
}

/// Prepare a fresh human workspace atomically, or prove that an existing one
/// is the exact workspace previously initialized from this config.
pub fn prepare_learning_workspace(
    config_path: impl AsRef<Path>,
    config: &Phase3LearningLaunchConfig,
) -> Result<PreparedLearningWorkspace> {
    config.validate()?;
    let config_path = canonical_exact(config_path.as_ref(), "Phase 3 config")?;
    let config_sha256 = hash_file(&config_path)?;
    let workspace = resolve_workspace_path(&config.workspace_path)?;
    match inspect_learning_workspace(&workspace, &config_sha256)? {
        LearningWorkspaceState::Initialized => {
            verify_initialized_workspace(&workspace, &config_path, config, &config_sha256)?;
            Ok(prepared_layout(workspace, false))
        }
        LearningWorkspaceState::Fresh => {
            initialize_learning_workspace(&workspace, &config_path, config, &config_sha256)?;
            verify_initialized_workspace(&workspace, &config_path, config, &config_sha256)?;
            Ok(prepared_layout(workspace, true))
        }
    }
}

fn initialize_learning_workspace(
    workspace: &Path,
    config_path: &Path,
    config: &Phase3LearningLaunchConfig,
    config_sha256: &str,
) -> Result<()> {
    let source_corpus = canonical_exact(&config.source_corpus_data_path, "source corpus")?;
    let source_ordered = canonical_exact(
        &config.source_ordered_event_ids_path,
        "source ordered event IDs",
    )?;
    let source_representation =
        canonical_exact(&config.source_representation_path, "source representation")?;
    let source_geometry = canonical_exact(&config.source_geometry_path, "source geometry")?;
    let model_bundle = canonical_exact(&config.model_bundle_path, "model bundle")?;
    let source_seed_handoff = config
        .seed_selection_handoff_path
        .as_deref()
        .map(|path| canonical_exact(path, "seed-selection handoff"))
        .transpose()?;
    let source_seed_handoff_before = source_seed_handoff.as_deref().map(hash_file).transpose()?;
    let source_representation_before = immutable_tree_metadata_fingerprint(&source_representation)?;
    let source_geometry_before = immutable_content_tree_identity(&source_geometry)?;
    let source_model_before = immutable_tree_metadata_fingerprint(&model_bundle)?;
    let parent = workspace
        .parent()
        .ok_or_else(|| Error::Invariant("Phase 3 workspace has no parent".to_owned()))?;
    let name = workspace
        .file_name()
        .ok_or_else(|| Error::Invariant("Phase 3 workspace has no file name".to_owned()))?;
    let stage = parent.join(format!(".{}.initialize", name.to_string_lossy()));
    match fs::symlink_metadata(&stage) {
        Ok(_) => return Err(Error::IncompleteStage(stage)),
        Err(error) if error.kind() == io::ErrorKind::NotFound => {}
        Err(source) => return Err(io_error("inspect", &stage, source)),
    }
    create_private_preflight_directory(&stage)?;
    let staged = prepared_layout(stage.clone(), true);
    let final_layout = prepared_layout(workspace.to_owned(), true);
    let result = (|| {
        create_owner_only_directory(&staged.corpus_path)?;
        copy_private_file(&source_corpus, &staged.corpus_path.join("data.mdb"))?;
        copy_private_file(&source_ordered, &staged.ordered_event_ids_path)?;
        if let Some(source) = &source_seed_handoff {
            copy_private_file(source, &staged.seed_selection_handoff_path)?;
        }
        prepare_disposable_representation_view(
            &source_representation,
            &staged.representation_path,
        )?;
        let verified = verify_representation(
            &staged.corpus_path,
            &staged.ordered_event_ids_path,
            &staged.representation_path,
        )?;
        if verified.representation_version() != config.expected_representation_version {
            return Err(Error::ExperimentState(
                "prepared representation has the wrong version".to_owned(),
            ));
        }
        let store = crate::representation::open_verified_representation(
            &staged.ordered_event_ids_path,
            &staged.representation_path,
        )?;
        let geometry = open_representation_geometry(
            &staged.ordered_event_ids_path,
            &staged.representation_path,
            &source_geometry,
        )?;
        if geometry.geometry_version() != config.expected_geometry_version {
            return Err(Error::ExperimentState(
                "prepared geometry has the wrong version".to_owned(),
            ));
        }
        let (seeds, initial_presentations) = seed_material(config, &staged, &store)?;
        require_seed_membership(&seeds, &staged, &store)?;
        let model_lock = model_bundle.join("model-lock.json");
        if hash_file(&model_lock)? != store.manifest().descriptor.model_lock_sha256 {
            return Err(Error::ExperimentState(
                "model bundle does not match the prepared representation".to_owned(),
            ));
        }
        let binding = Phase3RunnerBinding::from_geometry_with_initial_presentations(
            &geometry,
            final_layout.corpus_path.clone(),
            final_layout.session_path.clone(),
            seeds,
            initial_presentations,
        );
        write_private_json_atomic(&staged.runner_binding_path, &binding)?;
        copy_private_file(config_path, &staged.frozen_config_path)?;
        let source_representation_after =
            immutable_tree_metadata_fingerprint(&source_representation)?;
        let source_geometry_after = immutable_content_tree_identity(&source_geometry)?;
        let source_model_after = immutable_tree_metadata_fingerprint(&model_bundle)?;
        let source_seed_handoff_after =
            source_seed_handoff.as_deref().map(hash_file).transpose()?;
        if source_representation_after != source_representation_before
            || source_geometry_after != source_geometry_before
            || source_model_after != source_model_before
            || source_seed_handoff_after != source_seed_handoff_before
        {
            return Err(Error::Invariant(
                "a Phase 3 source artifact changed during initialization".to_owned(),
            ));
        }
        if staged.session_path.exists() || staged.oracle_cache_path.exists() {
            return Err(Error::ExperimentState(
                "fresh Phase 3 initialization contains pre-existing ratings or cache state"
                    .to_owned(),
            ));
        }
        let receipt = LearningInitializationReceipt {
            schema_version: INITIALIZATION_SCHEMA_VERSION,
            purpose: HUMAN_LEARNING_PURPOSE.to_owned(),
            config_sha256: config_sha256.to_owned(),
            frozen_config_sha256: hash_file(&staged.frozen_config_path)?,
            runner_binding_sha256: hash_file(&staged.runner_binding_path)?,
            corpus_data_sha256: store.manifest().corpus_data_sha256.clone(),
            ordered_event_ids_sha256: store.manifest().ordered_event_ids_sha256.clone(),
            representation_version: store.representation_version().to_owned(),
            geometry_version: geometry.geometry_version().to_owned(),
            represented_rows: store.manifest().completed_rows,
            dimensions: store.manifest().descriptor.dimensions,
            source_representation_metadata_sha256: source_representation_before,
            source_geometry_content_sha256: source_geometry_before,
            source_model_metadata_sha256: source_model_before,
            seed_selection_handoff_sha256: source_seed_handoff_before,
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
    config: &Phase3LearningLaunchConfig,
    config_sha256: &str,
) -> Result<()> {
    require_private_directory(workspace, "Phase 3 workspace")?;
    let layout = prepared_layout(workspace.to_owned(), false);
    require_optional_private_file(&layout.session_path, "Phase 3 session")?;
    require_optional_private_file(
        &session_lock_path(&layout.session_path)?,
        "Phase 3 session lock",
    )?;
    require_optional_private_file(
        &session_temporary_path(&layout.session_path)?,
        "Phase 3 session temporary",
    )?;
    require_optional_private_cache(&layout.oracle_cache_path)?;
    let receipt_path = workspace.join(INITIALIZATION_FILE);
    require_private_file(&receipt_path, "Phase 3 initialization receipt")?;
    let receipt: LearningInitializationReceipt = read_json(&receipt_path)?;
    if receipt.schema_version != INITIALIZATION_SCHEMA_VERSION
        || receipt.purpose != HUMAN_LEARNING_PURPOSE
        || receipt.config_sha256 != config_sha256
    {
        return Err(Error::ExperimentState(
            "existing Phase 3 workspace initialization receipt does not match this human run"
                .to_owned(),
        ));
    }
    for (path, expected, label) in [
        (
            config_path,
            receipt.config_sha256.as_str(),
            "invocation config",
        ),
        (
            layout.frozen_config_path.as_path(),
            receipt.frozen_config_sha256.as_str(),
            "frozen config",
        ),
        (
            layout.runner_binding_path.as_path(),
            receipt.runner_binding_sha256.as_str(),
            "runner binding",
        ),
        (
            layout.corpus_path.join("data.mdb").as_path(),
            receipt.corpus_data_sha256.as_str(),
            "prepared corpus",
        ),
        (
            layout.ordered_event_ids_path.as_path(),
            receipt.ordered_event_ids_sha256.as_str(),
            "prepared ordered event IDs",
        ),
    ] {
        if hash_file(path)? != expected {
            return Err(Error::ExperimentState(format!(
                "Phase 3 {label} does not match its initialization receipt"
            )));
        }
    }
    match &receipt.seed_selection_handoff_sha256 {
        Some(expected) => {
            require_private_file(
                &layout.seed_selection_handoff_path,
                "Phase 3 seed-selection handoff",
            )?;
            if hash_file(&layout.seed_selection_handoff_path)? != *expected {
                return Err(Error::ExperimentState(
                    "Phase 3 seed-selection handoff does not match its initialization receipt"
                        .to_owned(),
                ));
            }
        }
        None if layout.seed_selection_handoff_path.exists() => {
            return Err(Error::ExperimentState(
                "legacy Phase 3 workspace contains an unexpected seed-selection handoff".to_owned(),
            ));
        }
        None => {}
    }
    require_private_file(&layout.frozen_config_path, "Phase 3 frozen config")?;
    require_private_file(&layout.runner_binding_path, "Phase 3 runner binding")?;
    let frozen: Phase3LearningLaunchConfig = read_json(&layout.frozen_config_path)?;
    frozen.validate()?;
    if hash_file(config_path)? != hash_file(&layout.frozen_config_path)? {
        return Err(Error::ExperimentState(
            "Phase 3 invocation config differs from its frozen config".to_owned(),
        ));
    }
    let store = crate::representation::open_verified_representation(
        &layout.ordered_event_ids_path,
        &layout.representation_path,
    )?;
    store.require_verified_corpus(&layout.corpus_path.join("data.mdb"))?;
    if store.representation_version() != receipt.representation_version
        || store.representation_version() != config.expected_representation_version
        || store.manifest().completed_rows != receipt.represented_rows
        || store.manifest().descriptor.dimensions != receipt.dimensions
        || !store.manifest().complete
    {
        return Err(Error::ExperimentState(
            "prepared representation does not match its initialization receipt".to_owned(),
        ));
    }
    let source_geometry = canonical_exact(&config.source_geometry_path, "source geometry")?;
    let geometry = open_representation_geometry(
        &layout.ordered_event_ids_path,
        &layout.representation_path,
        &source_geometry,
    )?;
    if geometry.geometry_version() != receipt.geometry_version
        || geometry.geometry_version() != config.expected_geometry_version
    {
        return Err(Error::ExperimentState(
            "Phase 3 geometry does not match its initialization receipt".to_owned(),
        ));
    }
    let binding: Phase3RunnerBinding = read_json(&layout.runner_binding_path)?;
    let (seeds, initial_presentations) = seed_material(config, &layout, &store)?;
    let expected_initial = initial_presentations
        .iter()
        .map(|presentation| {
            Ok((
                presentation.event_id().map_err(Error::ExperimentState)?,
                presentation.state().clone(),
            ))
        })
        .collect::<Result<std::collections::BTreeMap<_, _>>>()?;
    if binding.corpus_path() != layout.corpus_path
        || binding.session_path() != layout.session_path
        || binding.representation_version() != receipt.representation_version
        || binding.geometry_version() != receipt.geometry_version
        || binding.seeds() != seeds
        || binding
            .initial_presentations()
            .map_err(Error::ExperimentState)?
            != expected_initial
    {
        return Err(Error::ExperimentState(
            "Phase 3 runner binding does not match the initialized human run".to_owned(),
        ));
    }
    binding.runner_config().map_err(Error::ExperimentState)?;
    if immutable_tree_metadata_fingerprint(canonical_exact(
        &config.source_representation_path,
        "source representation",
    )?)? != receipt.source_representation_metadata_sha256
        || immutable_content_tree_identity(&source_geometry)?
            != receipt.source_geometry_content_sha256
        || immutable_tree_metadata_fingerprint(canonical_exact(
            &config.model_bundle_path,
            "model bundle",
        )?)? != receipt.source_model_metadata_sha256
    {
        return Err(Error::ExperimentState(
            "a Phase 3 source artifact changed after initialization".to_owned(),
        ));
    }
    if hash_file(
        &canonical_exact(&config.model_bundle_path, "model bundle")?.join("model-lock.json"),
    )? != store.manifest().descriptor.model_lock_sha256
    {
        return Err(Error::ExperimentState(
            "model bundle does not match the prepared representation".to_owned(),
        ));
    }
    require_seed_membership(&seeds, &layout, &store)
}

fn require_seed_membership(
    seeds: &[Phase3SeedBinding],
    layout: &PreparedLearningWorkspace,
    store: &crate::representation::RepresentationStore,
) -> Result<()> {
    let corpus = open_existing_ndb(&layout.corpus_path, Validation::TrustedSource)?;
    let transaction = Transaction::new(&corpus)
        .map_err(|source| ndb_error("open transaction on", &layout.corpus_path, source))?;
    for seed in seeds {
        let event_id = seed.event_id().map_err(Error::ExperimentState)?;
        if store.row_for_event(event_id)?.is_none() {
            return Err(Error::ExperimentState(format!(
                "Phase 3 seed `{}` is absent from the representation",
                seed.event_id_hex()
            )));
        }
        corpus
            .get_note_by_id(&transaction, &event_id)
            .map_err(|_| {
                Error::ExperimentState(format!(
                    "Phase 3 seed `{}` is absent from the corpus",
                    seed.event_id_hex()
                ))
            })?;
    }
    Ok(())
}

fn seed_material(
    config: &Phase3LearningLaunchConfig,
    layout: &PreparedLearningWorkspace,
    store: &crate::representation::RepresentationStore,
) -> Result<(
    Vec<Phase3SeedBinding>,
    Vec<Phase3InitialPresentationBinding>,
)> {
    if config.schema_version == LEGACY_CONFIG_SCHEMA_VERSION {
        return Ok((config.seeds.clone(), Vec::new()));
    }
    let handoff: Phase3SeedSelectionHandoff =
        read_phase3_seed_selection_handoff(&layout.seed_selection_handoff_path)?;
    let expected_corpus_identity = format!("sha256:{}", store.manifest().corpus_data_sha256);
    if handoff.corpus_identity() != expected_corpus_identity
        || handoff.representation_version() != store.representation_version()
        || handoff.candidate_depth() != crate::candidate_order::CANDIDATE_DEPTH
    {
        return Err(Error::ExperimentState(
            "seed-selection handoff does not match the prepared Phase 3 corpus and representation"
                .to_owned(),
        ));
    }
    let initial_presentations = handoff
        .initial_presentations()
        .map_err(Error::ExperimentState)?
        .into_iter()
        .map(|(event_id, state)| {
            Phase3InitialPresentationBinding::new(event_id_hex(event_id), state)
                .map_err(Error::ExperimentState)
        })
        .collect::<Result<Vec<_>>>()?;
    Ok((handoff.seeds().to_vec(), initial_presentations))
}

fn prepared_layout(workspace_path: PathBuf, created: bool) -> PreparedLearningWorkspace {
    let corpus_path = workspace_path.join(CORPUS_DIRECTORY);
    let ordered_event_ids_path = workspace_path.join(ORDERED_EVENT_IDS_FILE);
    let representation_path = workspace_path.join(REPRESENTATION_DIRECTORY);
    let runner_binding_path = workspace_path.join(RUNNER_BINDING_FILE);
    let frozen_config_path = workspace_path.join(FROZEN_CONFIG_FILE);
    let session_path = workspace_path.join(SESSION_FILE);
    let oracle_cache_path = workspace_path.join(format!(".{SESSION_FILE}.oracle-responses"));
    let launch_receipt_path = workspace_path.join(LAUNCH_RECEIPT_FILE);
    let seed_selection_handoff_path = workspace_path.join(SEED_SELECTION_HANDOFF_FILE);
    PreparedLearningWorkspace {
        workspace_path,
        corpus_path,
        ordered_event_ids_path,
        representation_path,
        runner_binding_path,
        frozen_config_path,
        session_path,
        oracle_cache_path,
        launch_receipt_path,
        seed_selection_handoff_path,
        created,
    }
}

fn event_id_hex(event_id: crate::representation::EventId) -> String {
    event_id.iter().map(|byte| format!("{byte:02x}")).collect()
}

pub fn read_learning_launch_config(path: impl AsRef<Path>) -> Result<Phase3LearningLaunchConfig> {
    let path = path.as_ref();
    require_absolute_normalized(path, "Phase 3 config")?;
    let input = File::open(path).map_err(|source| Error::Io {
        operation: "open",
        path: path.to_owned(),
        source,
    })?;
    let config: Phase3LearningLaunchConfig = serde_json::from_reader(BufReader::new(input))
        .map_err(|source| Error::Manifest {
            operation: "decode",
            path: path.to_owned(),
            source,
        })?;
    config.validate()?;
    Ok(config)
}

pub fn inspect_learning_workspace(
    workspace: impl AsRef<Path>,
    config_sha256: &str,
) -> Result<LearningWorkspaceState> {
    let workspace = workspace.as_ref();
    require_absolute_normalized(workspace, "Phase 3 workspace")?;
    require_sha256(config_sha256, "Phase 3 config SHA-256")?;
    let metadata = match fs::symlink_metadata(workspace) {
        Ok(metadata) => metadata,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
            return Ok(LearningWorkspaceState::Fresh);
        }
        Err(source) => {
            return Err(Error::Io {
                operation: "inspect",
                path: workspace.to_owned(),
                source,
            });
        }
    };
    if metadata.file_type().is_symlink() || !metadata.is_dir() {
        return Err(Error::ExperimentState(
            "Phase 3 workspace must be a real private directory".to_owned(),
        ));
    }
    let receipt_path = workspace.join(INITIALIZATION_FILE);
    let input = File::open(&receipt_path).map_err(|source| {
        if source.kind() == std::io::ErrorKind::NotFound {
            Error::ExperimentState(
                "existing Phase 3 workspace has no valid human initialization receipt".to_owned(),
            )
        } else {
            Error::Io {
                operation: "open",
                path: receipt_path.clone(),
                source,
            }
        }
    })?;
    let receipt: LearningInitializationReceipt = serde_json::from_reader(BufReader::new(input))
        .map_err(|source| Error::Manifest {
            operation: "decode",
            path: receipt_path,
            source,
        })?;
    if receipt.schema_version != INITIALIZATION_SCHEMA_VERSION
        || receipt.purpose != HUMAN_LEARNING_PURPOSE
        || receipt.config_sha256 != config_sha256
    {
        return Err(Error::ExperimentState(
            "existing Phase 3 workspace initialization receipt does not match this human run"
                .to_owned(),
        ));
    }
    Ok(LearningWorkspaceState::Initialized)
}

/// Derive a whole-GiB hard limit while preserving existing host swap debt and
/// the supplied host reserve.
pub fn derive_learning_memory_limit(
    available_bytes: u64,
    swap_used_bytes: u64,
    reserve_bytes: u64,
) -> Result<u64> {
    let unavailable = swap_used_bytes
        .checked_add(reserve_bytes)
        .ok_or_else(|| Error::Invariant("Phase 3 host reservation overflowed".to_owned()))?;
    let safe_bytes = available_bytes.checked_sub(unavailable).ok_or_else(|| {
        Error::ExperimentState(
            "Phase 3 cannot preserve the existing swap debt and host reserve".to_owned(),
        )
    })?;
    let limit = safe_bytes / GIB * GIB;
    if limit < MINIMUM_LEARNING_MEMORY_BYTES {
        return Err(Error::ExperimentState(format!(
            "Phase 3 has only {} GiB of safe memory; at least 67 GiB is required",
            limit / GIB
        )));
    }
    Ok(limit)
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct HostMemorySnapshot {
    available_bytes: u64,
    swap_used_bytes: u64,
}

impl HostMemorySnapshot {
    pub const fn available_bytes(self) -> u64 {
        self.available_bytes
    }

    pub const fn swap_used_bytes(self) -> u64 {
        self.swap_used_bytes
    }
}

/// Read the exact host values used for first-launch sizing and every resume
/// admission check.
pub fn read_host_memory_snapshot(path: impl AsRef<Path>) -> Result<HostMemorySnapshot> {
    let path = path.as_ref();
    let contents = fs::read_to_string(path).map_err(|source| io_error("read", path, source))?;
    let mut available = None;
    let mut swap_total = None;
    let mut swap_free = None;
    for line in contents.lines() {
        let mut fields = line.split_whitespace();
        let Some(key) = fields.next() else {
            continue;
        };
        let key = key.trim_end_matches(':');
        if !matches!(key, "MemAvailable" | "SwapTotal" | "SwapFree") {
            continue;
        }
        let kibibytes = fields
            .next()
            .ok_or_else(|| Error::ExperimentState(format!("{path:?} has no value for {key}")))?
            .parse::<u64>()
            .map_err(|source| {
                Error::ExperimentState(format!("{path:?} has an invalid {key}: {source}"))
            })?;
        if fields.next() != Some("kB") {
            return Err(Error::ExperimentState(format!(
                "{path:?} does not express {key} in kB"
            )));
        }
        let bytes = kibibytes
            .checked_mul(1024)
            .ok_or_else(|| Error::Invariant(format!("host {key} byte count overflowed")))?;
        match key {
            "MemAvailable" => available = Some(bytes),
            "SwapTotal" => swap_total = Some(bytes),
            "SwapFree" => swap_free = Some(bytes),
            _ => unreachable!(),
        }
    }
    let available_bytes = available.ok_or_else(|| {
        Error::ExperimentState("host memory input has no MemAvailable value".to_owned())
    })?;
    let swap_total = swap_total.ok_or_else(|| {
        Error::ExperimentState("host memory input has no SwapTotal value".to_owned())
    })?;
    let swap_free = swap_free.ok_or_else(|| {
        Error::ExperimentState("host memory input has no SwapFree value".to_owned())
    })?;
    if swap_free > swap_total {
        return Err(Error::ExperimentState(
            "host SwapFree exceeds SwapTotal".to_owned(),
        ));
    }
    Ok(HostMemorySnapshot {
        available_bytes,
        swap_used_bytes: swap_total - swap_free,
    })
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum LearningContainerState {
    Absent,
    Running,
    Stopped,
}

/// Distinguish a resumable attached controller from an absent or unexpectedly
/// stopped container, and reject any same-name container with another identity.
pub fn inspect_learning_container(
    container_runtime: impl AsRef<Path>,
    container_name: &str,
    launch_identity_sha256: &str,
    controller_image_id: &str,
) -> Result<LearningContainerState> {
    validate_container_name(container_name)?;
    require_sha256(launch_identity_sha256, "Phase 3 launch identity")?;
    require_image_id(controller_image_id)?;
    let runtime = canonical_exact(container_runtime.as_ref(), "container runtime")?;
    let format =
        "{{.State.Running}}\n{{index .Config.Labels \"io.notedeck.phase3.launch\"}}\n{{.Image}}";
    let inspection = Command::new(&runtime)
        .args(["container", "inspect", "--format", format, container_name])
        .output()
        .map_err(|source| io_error("execute", &runtime, source))?;
    if inspection.status.success() {
        let output = String::from_utf8(inspection.stdout).map_err(|_| {
            Error::ExperimentState("container runtime returned non-UTF-8 Phase 3 state".to_owned())
        })?;
        let lines = output.lines().collect::<Vec<_>>();
        if lines.len() != 3 || lines[1] != launch_identity_sha256 || lines[2] != controller_image_id
        {
            return Err(Error::ExperimentState(
                "same-name container does not match the frozen Phase 3 launch".to_owned(),
            ));
        }
        return match lines[0] {
            "true" => Ok(LearningContainerState::Running),
            "false" => Ok(LearningContainerState::Stopped),
            _ => Err(Error::ExperimentState(
                "container runtime returned an invalid Phase 3 running state".to_owned(),
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
            "container runtime could not inspect Phase 3 controller: {}",
            String::from_utf8_lossy(&listing.stderr).trim()
        )));
    }
    if listing.stdout.iter().all(u8::is_ascii_whitespace) {
        Ok(LearningContainerState::Absent)
    } else {
        Err(Error::ExperimentState(
            "container runtime found the Phase 3 name but could not verify its identity".to_owned(),
        ))
    }
}

pub fn learning_attach_arguments(container_name: &str) -> Vec<OsString> {
    [
        "attach".into(),
        "--detach-keys=ctrl-]".into(),
        container_name.into(),
    ]
    .into_iter()
    .collect()
}

/// Build the one-container launch that places the Rust controller and its
/// direct Python query worker under the same hard memory and swap guard.
#[allow(clippy::too_many_arguments)]
pub fn learning_container_arguments(
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
    require_sha256(launch_identity_sha256, "Phase 3 launch identity")?;
    if memory_limit_bytes < MINIMUM_LEARNING_MEMORY_BYTES {
        return Err(Error::ExperimentState(
            "Phase 3 container limit is below the proven 67 GiB envelope".to_owned(),
        ));
    }
    if readonly_inputs.is_empty() {
        return Err(Error::ExperimentState(
            "Phase 3 has no immutable input mounts".to_owned(),
        ));
    }

    let workspace = canonical_exact(workspace, "Phase 3 workspace")?;
    if !workspace.is_dir() {
        return Err(Error::ExperimentState(format!(
            "Phase 3 workspace is not a directory: `{}`",
            workspace.display()
        )));
    }
    let frozen_config = canonical_exact(frozen_config, "Phase 3 frozen config")?;
    if !frozen_config.is_file() || !frozen_config.starts_with(&workspace) {
        return Err(Error::ExperimentState(
            "Phase 3 frozen config must be a file inside its private workspace".to_owned(),
        ));
    }
    let mut readonly = Vec::with_capacity(readonly_inputs.len());
    for input in readonly_inputs {
        let input = canonical_exact(input, "Phase 3 immutable input")?;
        if input.starts_with(&workspace) || workspace.starts_with(&input) {
            return Err(Error::ExperimentState(format!(
                "Phase 3 immutable input `{}` overlaps private workspace `{}`",
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
        format!("--label=io.notedeck.phase3.launch={launch_identity_sha256}").into(),
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

/// Prove that the configured immutable image ID exists unchanged in the local
/// container runtime.
pub fn resolve_controller_image_id(
    container_runtime: impl AsRef<Path>,
    controller_image_reference: &str,
) -> Result<String> {
    require_image_id(controller_image_reference)?;
    let runtime = canonical_exact(container_runtime.as_ref(), "container runtime")?;
    let output = Command::new(&runtime)
        .args([
            "image",
            "inspect",
            "--format={{.Id}}",
            controller_image_reference,
        ])
        .output()
        .map_err(|source| io_error("execute", &runtime, source))?;
    if !output.status.success() {
        return Err(Error::ExperimentState(format!(
            "container runtime could not resolve Phase 3 image `{controller_image_reference}`: {}",
            String::from_utf8_lossy(&output.stderr).trim()
        )));
    }
    let image_id = String::from_utf8(output.stdout)
        .map_err(|_| {
            Error::ExperimentState(
                "container runtime returned a non-UTF-8 Phase 3 image ID".to_owned(),
            )
        })?
        .trim()
        .to_owned();
    require_image_id(&image_id)?;
    if image_id != controller_image_reference {
        return Err(Error::ExperimentState(
            "container runtime resolved a different Phase 3 image than the exact configured ID"
                .to_owned(),
        ));
    }
    Ok(image_id)
}

fn resolve_workspace_path(path: &Path) -> Result<PathBuf> {
    require_absolute_normalized(path, "Phase 3 workspace")?;
    let parent = path
        .parent()
        .ok_or_else(|| Error::Invariant("Phase 3 workspace has no parent".to_owned()))?;
    let parent = canonical_exact(parent, "Phase 3 workspace parent")?;
    let name = path
        .file_name()
        .ok_or_else(|| Error::Invariant("Phase 3 workspace has no file name".to_owned()))?;
    let resolved = parent.join(name);
    match fs::symlink_metadata(&resolved) {
        Ok(metadata) => {
            if metadata.file_type().is_symlink() || !metadata.is_dir() {
                return Err(Error::ExperimentState(
                    "Phase 3 workspace must be a real private directory".to_owned(),
                ));
            }
            canonical_exact(&resolved, "Phase 3 workspace")
        }
        Err(error) if error.kind() == io::ErrorKind::NotFound => Ok(resolved),
        Err(source) => Err(io_error("inspect", &resolved, source)),
    }
}

fn canonical_exact(path: &Path, label: &str) -> Result<PathBuf> {
    require_absolute_normalized(path, label)?;
    let canonical = fs::canonicalize(path).map_err(|source| io_error("resolve", path, source))?;
    if canonical != path {
        return Err(Error::ExperimentState(format!(
            "{label} path must use its canonical spelling: `{}`",
            canonical.display()
        )));
    }
    reject_unsafe_mount_path(&canonical, label)?;
    Ok(canonical)
}

fn reject_unsafe_mount_path(path: &Path, label: &str) -> Result<()> {
    let encoded = path.as_os_str().as_encoded_bytes();
    if encoded.contains(&b',') || path.to_str().is_none() {
        return Err(Error::ExperimentState(format!(
            "{label} path cannot be represented safely as a container mount: `{}`",
            path.display()
        )));
    }
    Ok(())
}

fn create_owner_only_directory(path: &Path) -> Result<()> {
    create_private_preflight_directory(path)
}

fn copy_private_file(source: &Path, destination: &Path) -> Result<()> {
    if !source.is_file() {
        return Err(Error::ArtifactMissing(source.to_owned()));
    }
    match fs::symlink_metadata(destination) {
        Ok(_) => return Err(Error::ArtifactExists(destination.to_owned())),
        Err(error) if error.kind() == io::ErrorKind::NotFound => {}
        Err(source) => return Err(io_error("inspect", destination, source)),
    }
    let mut options = OpenOptions::new();
    options.create_new(true).write(true).mode(0o600);
    let output = options
        .open(destination)
        .map_err(|source| io_error("create", destination, source))?;
    output
        .set_permissions(fs::Permissions::from_mode(0o600))
        .map_err(|source| io_error("set permissions on", destination, source))?;
    let mut input = File::open(source).map_err(|error| io_error("open", source, error))?;
    let mut output = BufWriter::new(output);
    let copied = io::copy(&mut input, &mut output)
        .and_then(|_| output.flush())
        .map_err(|source| io_error("copy", destination, source));
    if let Err(error) = copied {
        let _ = fs::remove_file(destination);
        return Err(error);
    }
    output
        .get_ref()
        .sync_all()
        .map_err(|source| io_error("sync", destination, source))
}

fn require_private_directory(path: &Path, label: &str) -> Result<()> {
    let metadata =
        fs::symlink_metadata(path).map_err(|source| io_error("inspect", path, source))?;
    if metadata.file_type().is_symlink()
        || !metadata.is_dir()
        || metadata.uid() != unsafe { libc::geteuid() }
        || metadata.permissions().mode() & 0o777 != 0o700
    {
        return Err(Error::ExperimentState(format!(
            "{label} must be an owner-only real directory"
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
        || metadata.permissions().mode() & 0o777 != 0o600
    {
        return Err(Error::ExperimentState(format!(
            "{label} must be an owner-only regular file"
        )));
    }
    Ok(())
}

fn require_optional_private_file(path: &Path, label: &str) -> Result<()> {
    match fs::symlink_metadata(path) {
        Ok(_) => require_private_file(path, label),
        Err(source) if source.kind() == io::ErrorKind::NotFound => Ok(()),
        Err(source) => Err(io_error("inspect", path, source)),
    }
}

fn require_optional_private_cache(path: &Path) -> Result<()> {
    match fs::symlink_metadata(path) {
        Err(source) if source.kind() == io::ErrorKind::NotFound => return Ok(()),
        Err(source) => return Err(io_error("inspect", path, source)),
        Ok(_) => {}
    }
    require_private_directory(path, "Phase 3 Oracle cache")?;
    for entry in fs::read_dir(path).map_err(|source| io_error("read", path, source))? {
        let entry = entry.map_err(|source| io_error("read", path, source))?;
        require_private_file(&entry.path(), "Phase 3 Oracle cache entry")?;
    }
    Ok(())
}

fn session_lock_path(session_path: &Path) -> Result<PathBuf> {
    let name = session_path
        .file_name()
        .and_then(|name| name.to_str())
        .ok_or_else(|| Error::NonUtf8Path(session_path.to_owned()))?;
    Ok(session_path.with_file_name(format!(".{name}.lock")))
}

fn session_temporary_path(session_path: &Path) -> Result<PathBuf> {
    let name = session_path
        .file_name()
        .and_then(|name| name.to_str())
        .ok_or_else(|| Error::NonUtf8Path(session_path.to_owned()))?;
    Ok(session_path.with_file_name(format!(".{name}.tmp")))
}

fn require_pristine_first_launch(prepared: &PreparedLearningWorkspace) -> Result<()> {
    for path in [
        prepared.session_path.clone(),
        prepared.oracle_cache_path.clone(),
        session_lock_path(&prepared.session_path)?,
        session_temporary_path(&prepared.session_path)?,
    ] {
        match fs::symlink_metadata(&path) {
            Err(source) if source.kind() == io::ErrorKind::NotFound => {}
            Err(source) => return Err(io_error("inspect", &path, source)),
            Ok(_) => {
                return Err(Error::ExperimentState(format!(
                    "Phase 3 launch receipt is missing but prior runner state exists at `{}`",
                    path.display()
                )));
            }
        }
    }
    Ok(())
}

fn read_json<T: for<'de> Deserialize<'de>>(path: &Path) -> Result<T> {
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
        .map_err(|source| Error::Invariant(format!("system clock is before Unix epoch: {source}")))
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
        || !name
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'.' | b'_' | b'-'))
    {
        return Err(Error::ExperimentState(
            "Phase 3 container name is invalid".to_owned(),
        ));
    }
    Ok(())
}

fn require_absolute_normalized(path: &Path, label: &str) -> Result<()> {
    if !path.is_absolute()
        || path
            .components()
            .any(|component| matches!(component, Component::CurDir | Component::ParentDir))
    {
        return Err(Error::ExperimentState(format!(
            "{label} path must be absolute and normalized: `{}`",
            path.display()
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
            "{label} must contain 64 lowercase hexadecimal digits"
        )));
    }
    Ok(())
}

fn require_image_id(value: &str) -> Result<()> {
    let Some(digest) = value.strip_prefix("sha256:") else {
        return Err(Error::ExperimentState(
            "Phase 3 controller image must be an exact image ID (`sha256:...`)".to_owned(),
        ));
    };
    require_sha256(digest, "Phase 3 controller image ID")
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
