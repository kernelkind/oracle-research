//! Guarded start and exact resume of the real Phase 4 final evaluation.

use std::env;
use std::ffi::OsString;
use std::fs::{self, File};
use std::io::{BufReader, IsTerminal};
use std::path::{Path, PathBuf};
use std::process::{Command, ExitCode, Stdio};

use oracle_mvp::final_evaluation_runner::FinalEvaluationRunnerOutcome;
use oracle_mvp::gte::{GteProcessEncoder, GteWorkerConfig};
use oracle_mvp::phase3_capacity_stress::{
    require_combined_memory_limit, require_host_memory_admission, resolve_unified_cgroup_path,
};
use oracle_mvp::phase4_final_launch::{
    FinalEvaluationContainerState, bind_final_evaluation_launch,
    derive_final_evaluation_memory_limit, final_evaluation_attach_arguments,
    final_evaluation_container_arguments, final_evaluation_launch_identity,
    inspect_final_evaluation_container, prepare_final_evaluation_workspace,
    read_final_evaluation_host_memory_snapshot, read_final_evaluation_launch_config,
    read_final_evaluation_launch_receipt, resolve_final_evaluation_controller_image_id,
    resume_prepared_final_evaluation_tui, run_prepared_final_evaluation_tui,
};
use oracle_mvp::representation::RepresentationManifest;

const CGROUP_MOUNT: &str = "/sys/fs/cgroup";

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("Phase 4 final evaluation failed: {error}");
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
            "the real Phase 4 evaluator must be started from an interactive terminal".to_owned(),
        );
    }
    let config_path = fs::canonicalize(config_path).map_err(|error| {
        format!(
            "could not resolve Phase 4 config `{}`: {error}",
            config_path.display()
        )
    })?;
    let config =
        read_final_evaluation_launch_config(&config_path).map_err(|error| error.to_string())?;
    let prepared = prepare_final_evaluation_workspace(&config_path, &config)
        .map_err(|error| error.to_string())?;
    let memory = read_final_evaluation_host_memory_snapshot("/proc/meminfo")
        .map_err(|error| error.to_string())?;
    let launch = match read_final_evaluation_launch_receipt(&prepared, &config)
        .map_err(|error| error.to_string())?
    {
        Some(receipt) => {
            let actual = resolve_final_evaluation_controller_image_id(
                config.container_runtime(),
                receipt.controller_image_id(),
            )
            .map_err(|error| error.to_string())?;
            if actual != receipt.controller_image_id() {
                return Err("the frozen Phase 4 controller image is no longer exact".to_owned());
            }
            receipt
        }
        None => {
            let image_id = resolve_final_evaluation_controller_image_id(
                config.container_runtime(),
                config.controller_image(),
            )
            .map_err(|error| error.to_string())?;
            let memory_limit = derive_final_evaluation_memory_limit(
                memory.available_bytes(),
                memory.swap_used_bytes(),
                config.host_memory_reserve_bytes(),
            )
            .map_err(|error| error.to_string())?;
            bind_final_evaluation_launch(&prepared, &config, &image_id, memory_limit)
                .map_err(|error| error.to_string())?
        }
    };
    let launch_identity =
        final_evaluation_launch_identity(&prepared).map_err(|error| error.to_string())?;
    match inspect_final_evaluation_container(
        config.container_runtime(),
        launch.container_name(),
        &launch_identity,
        launch.controller_image_id(),
    )
    .map_err(|error| error.to_string())?
    {
        FinalEvaluationContainerState::Running => run_runtime(
            config.container_runtime(),
            final_evaluation_attach_arguments(launch.container_name()),
        ),
        FinalEvaluationContainerState::Stopped => Err(
            "the guarded Phase 4 container stopped without being removed; inspect it before retrying"
                .to_owned(),
        ),
        FinalEvaluationContainerState::Absent => {
            require_host_memory_admission(
                memory.available_bytes(),
                memory.swap_used_bytes(),
                config.host_memory_reserve_bytes(),
                launch.memory_limit_bytes(),
            )
            .map_err(|error| error.to_string())?;
            let readonly_inputs = vec![
                config.source_phase3_workspace_path().to_owned(),
                config.source_representation_path().to_owned(),
                config.source_model_bundle_path().to_owned(),
            ];
            let arguments = final_evaluation_container_arguments(
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
            "could not resolve frozen Phase 4 config `{}`: {error}",
            config_path.display()
        )
    })?;
    let config =
        read_final_evaluation_launch_config(&config_path).map_err(|error| error.to_string())?;
    let prepared = prepare_final_evaluation_workspace(&config_path, &config)
        .map_err(|error| error.to_string())?;
    let launch = read_final_evaluation_launch_receipt(&prepared, &config)
        .map_err(|error| error.to_string())?
        .ok_or_else(|| "guarded Phase 4 workspace has no launch receipt".to_owned())?;
    let cgroup = current_cgroup_root()?;
    require_combined_memory_limit(&cgroup, launch.memory_limit_bytes())
        .map_err(|error| error.to_string())?;
    let frozen = prepared.session_path().exists() || prepared.orders_path().exists();
    let outcome = if frozen {
        resume_prepared_final_evaluation_tui(&prepared, &config)
            .map_err(|error| error.to_string())?
    } else {
        let manifest: RepresentationManifest =
            read_json(&prepared.representation_path().join("manifest.json"))?;
        let descriptor = &manifest.descriptor;
        let encoder = GteProcessEncoder::start(GteWorkerConfig {
            program: "/opt/gte-venv/bin/python".into(),
            prefix_arguments: Vec::new(),
            worker_path: Some("/opt/oracle-mvp/gte/worker.py".into()),
            model_dir: config.source_model_bundle_path().join("model"),
            model_lock_path: config.source_model_bundle_path().join("model-lock.json"),
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
        run_prepared_final_evaluation_tui(&prepared, &config, encoder)
            .map_err(|error| error.to_string())?
    };
    match outcome {
        FinalEvaluationRunnerOutcome::Paused => {
            eprintln!("Phase 4 final evaluation paused safely. Run the same command to resume.");
        }
        FinalEvaluationRunnerOutcome::Complete => {
            eprintln!("Phase 4 final evaluation is complete.");
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
        Err(format!("guarded Phase 4 container exited with {status}"))
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
    "usage: phase4-final-evaluation CONFIG.json".to_owned()
}
