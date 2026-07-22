//! Guarded start and exact resume of the real full-corpus Phase 3 learning run.

use std::env;
use std::ffi::OsString;
use std::fs::{self, File};
use std::io::{BufReader, IsTerminal};
use std::path::{Path, PathBuf};
use std::process::{Command, ExitCode, Stdio};

use oracle_mvp::adaptive_learning_runner::AdaptiveLearningRunnerOutcome;
use oracle_mvp::gte::{GteProcessEncoder, GteWorkerConfig};
use oracle_mvp::phase3_capacity_stress::{
    require_combined_memory_limit, require_host_memory_admission, resolve_unified_cgroup_path,
};
use oracle_mvp::phase3_learning_launch::{
    LearningContainerState, bind_learning_launch, derive_learning_memory_limit,
    inspect_learning_container, learning_attach_arguments, learning_container_arguments,
    learning_launch_identity, prepare_learning_workspace, read_host_memory_snapshot,
    read_learning_launch_config, read_learning_launch_receipt, resolve_controller_image_id,
    run_prepared_learning_tui,
};
use oracle_mvp::representation::RepresentationManifest;

const CGROUP_MOUNT: &str = "/sys/fs/cgroup";

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("phase3 learning failed: {error}");
            ExitCode::FAILURE
        }
    }
}

fn run() -> Result<(), String> {
    let mut arguments = env::args_os().skip(1);
    let first = arguments.next().ok_or_else(usage)?;
    if first == "__run" {
        let config = arguments.next().ok_or_else(usage)?;
        require_no_more(arguments)?;
        return run_inside_guard(Path::new(&config));
    }
    require_no_more(arguments)?;
    run_from_host(Path::new(&first))
}

fn run_from_host(config_path: &Path) -> Result<(), String> {
    if !std::io::stdin().is_terminal() || !std::io::stdout().is_terminal() {
        return Err(
            "the real Phase 3 evaluator must be started from an interactive terminal".to_owned(),
        );
    }
    let config_path = fs::canonicalize(config_path).map_err(|error| {
        format!(
            "could not resolve Phase 3 config `{}`: {error}",
            config_path.display()
        )
    })?;
    let config = read_learning_launch_config(&config_path).map_err(|error| error.to_string())?;
    let prepared =
        prepare_learning_workspace(&config_path, &config).map_err(|error| error.to_string())?;
    let memory = read_host_memory_snapshot("/proc/meminfo").map_err(|error| error.to_string())?;
    let launch = match read_learning_launch_receipt(&prepared, &config)
        .map_err(|error| error.to_string())?
    {
        Some(receipt) => {
            let actual = resolve_controller_image_id(
                config.container_runtime(),
                receipt.controller_image_id(),
            )
            .map_err(|error| error.to_string())?;
            if actual != receipt.controller_image_id() {
                return Err("the frozen Phase 3 controller image is no longer exact".to_owned());
            }
            receipt
        }
        None => {
            let image_id =
                resolve_controller_image_id(config.container_runtime(), config.controller_image())
                    .map_err(|error| error.to_string())?;
            let memory_limit = derive_learning_memory_limit(
                memory.available_bytes(),
                memory.swap_used_bytes(),
                config.host_memory_reserve_bytes(),
            )
            .map_err(|error| error.to_string())?;
            bind_learning_launch(&prepared, &config, &image_id, memory_limit)
                .map_err(|error| error.to_string())?
        }
    };
    let launch_identity = learning_launch_identity(&prepared).map_err(|error| error.to_string())?;
    match inspect_learning_container(
        config.container_runtime(),
        launch.container_name(),
        &launch_identity,
        launch.controller_image_id(),
    )
    .map_err(|error| error.to_string())?
    {
        LearningContainerState::Running => run_runtime(
            config.container_runtime(),
            learning_attach_arguments(launch.container_name()),
        ),
        LearningContainerState::Stopped => Err(
            "the guarded Phase 3 container stopped without being removed; inspect it before retrying"
                .to_owned(),
        ),
        LearningContainerState::Absent => {
            require_host_memory_admission(
                memory.available_bytes(),
                memory.swap_used_bytes(),
                config.host_memory_reserve_bytes(),
                launch.memory_limit_bytes(),
            )
            .map_err(|error| error.to_string())?;
            let readonly_inputs = vec![
                config.source_representation_path().to_owned(),
                config.source_geometry_path().to_owned(),
                config.model_bundle_path().to_owned(),
            ];
            let arguments = learning_container_arguments(
                launch.container_name(),
                launch.controller_image_id(),
                &launch_identity,
                launch.memory_limit_bytes(),
                unsafe { libc::geteuid() },
                unsafe { libc::getegid() },
                &readonly_inputs,
                prepared.workspace_path(),
                prepared.frozen_config_path(),
            )
            .map_err(|error| error.to_string())?;
            run_runtime(config.container_runtime(), arguments)
        }
    }
}

fn run_inside_guard(config_path: &Path) -> Result<(), String> {
    let config_path = fs::canonicalize(config_path).map_err(|error| {
        format!(
            "could not resolve frozen Phase 3 config `{}`: {error}",
            config_path.display()
        )
    })?;
    let config = read_learning_launch_config(&config_path).map_err(|error| error.to_string())?;
    let prepared =
        prepare_learning_workspace(&config_path, &config).map_err(|error| error.to_string())?;
    let launch = read_learning_launch_receipt(&prepared, &config)
        .map_err(|error| error.to_string())?
        .ok_or_else(|| "guarded Phase 3 workspace has no launch receipt".to_owned())?;
    let cgroup = current_cgroup_root()?;
    require_combined_memory_limit(&cgroup, launch.memory_limit_bytes())
        .map_err(|error| error.to_string())?;
    let manifest: RepresentationManifest =
        read_json(&prepared.representation_path().join("manifest.json"))?;
    let descriptor = &manifest.descriptor;
    let encoder = GteProcessEncoder::start(GteWorkerConfig {
        program: "/opt/gte-venv/bin/python".into(),
        prefix_arguments: Vec::new(),
        worker_path: Some("/opt/oracle-mvp/gte/worker.py".into()),
        model_dir: config.model_bundle_path().join("model"),
        model_lock_path: config.model_bundle_path().join("model-lock.json"),
        dependency_lock_path: "/tmp/gte-locks/requirements.lock".into(),
        device: "cpu".to_owned(),
        model_lock_sha256: descriptor.model_lock_sha256.clone(),
        worker_sha256: descriptor.worker_sha256.clone(),
        dependency_lock_sha256: descriptor.dependency_lock_sha256.clone(),
        container_image: descriptor.container_image.clone(),
        torch_version: descriptor.torch_version.clone(),
        transformers_version: descriptor.transformers_version.clone(),
        cuda_version: descriptor.cuda_version.clone(),
    })
    .map_err(|error| error.to_string())?;
    match run_prepared_learning_tui(&prepared, &config, encoder)
        .map_err(|error| error.to_string())?
    {
        AdaptiveLearningRunnerOutcome::Paused => {
            eprintln!("Phase 3 learning paused safely. Run the same command to resume.");
        }
        AdaptiveLearningRunnerOutcome::Complete(_) => {
            eprintln!("Phase 3 adaptive learning is complete.");
        }
    }
    Ok(())
}

fn current_cgroup_root() -> Result<PathBuf, String> {
    let process_cgroup = fs::read_to_string("/proc/self/cgroup")
        .map_err(|error| format!("could not read /proc/self/cgroup: {error}"))?;
    resolve_unified_cgroup_path(Path::new(CGROUP_MOUNT), &process_cgroup)
        .map_err(|error| error.to_string())
}

fn run_runtime(runtime: &Path, arguments: Vec<OsString>) -> Result<(), String> {
    let status = Command::new(runtime)
        .args(arguments)
        .stdin(Stdio::inherit())
        .stdout(Stdio::inherit())
        .stderr(Stdio::inherit())
        .status()
        .map_err(|error| format!("could not start container runtime: {error}"))?;
    if status.success() {
        Ok(())
    } else {
        Err(format!("guarded Phase 3 container exited with {status}"))
    }
}

fn read_json<T: for<'de> serde::Deserialize<'de>>(path: &Path) -> Result<T, String> {
    let file = File::open(path)
        .map_err(|error| format!("could not open `{}`: {error}", path.display()))?;
    serde_json::from_reader(BufReader::new(file))
        .map_err(|error| format!("could not decode `{}`: {error}", path.display()))
}

fn require_no_more(mut arguments: impl Iterator<Item = OsString>) -> Result<(), String> {
    if arguments.next().is_some() {
        Err(usage())
    } else {
        Ok(())
    }
}

fn usage() -> String {
    "usage: phase3-learning CONFIG.json".to_owned()
}
