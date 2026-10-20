"""Freeze distillation inputs and execute them as a shared Vast command workload."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal, InvalidOperation
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time

from gte.full_build_package import write_manifest, verify_manifest
from sse_multivector.distillation_run import (load_data, read_json, sha256, write_json,
    preparation_data, shared_code_files, subject_parent, subject_stage_summary, subject_test_summary, verify_subject_run)


CODE_ROOT = Path(__file__).resolve().parents[1]
CODE_FILES = (
    "sse_multivector/distillation_deploy.py", "sse_multivector/distillation_run.py",
    "sse_multivector/evaluation_publication.py",
    "sse_multivector/distillation_cache.py",
    "sse_multivector/distillation_data.py", "sse_multivector/extraction_pipeline.py",
    "sse_multivector/_runner_bootstrap.py",
    "sse_multivector/mask_positions.py", "sse_multivector/distillation/requirements.lock",
    "sse_multivector/distillation/requirements-gpu.lock",
    "sse_multivector/distillation_vast.py", "sse_multivector/distillation/vast-launch.json",
    "sse_multivector/distillation/qwen-continuation-v1.vast.json",
    "sse_multivector/distillation/Dockerfile",
    "vast/runner.py", "vast/package.py",
    "gte/full_build_package.py",
    "gte/calibration_package.py", "gte/vast_private_create.py",
)
REMOTE_PYTHON = "/opt/distillation-venv/bin/python"


def check_offer(settings, offer):
    """Check a saved quote; this neither admits spending nor creates an instance."""
    def number(value):
        try:
            result = Decimal(str(value))
        except InvalidOperation as error:
            raise ValueError("invalid numeric quote") from error
        if not result.is_finite() or result < 0:
            raise ValueError("invalid numeric quote")
        return result

    excluded = settings.get("excluded_machine_ids", [])
    if (not isinstance(excluded, list) or any(type(n) is not int or n <= 0 for n in excluded)
            or offer.get("machine_id") in excluded):
        raise ValueError("offer uses an excluded machine or invalid exclusion list")
    for key, value in settings["offer_equals"].items():
        if offer.get(key) != value:
            raise ValueError(f"offer differs: {key}")
    for key, value in settings["offer_minimums"].items():
        if number(offer.get(key)) < number(value):
            raise ValueError(f"offer below minimum: {key}")
    for key, value in settings["offer_maximums"].items():
        if number(offer.get(key)) > number(value):
            raise ValueError(f"offer above maximum: {key}")
    driver = tuple(int(part) for part in offer.get("driver_version", "").split("."))
    if driver < tuple(settings["minimum_driver"]):
        raise ValueError("driver too old for the pinned CUDA image")
    # Vast's search ceiling can be applied before --storage is added. Check
    # the actual returned total and prove the requested disk is included.
    storage = number(offer.get("storage_total_cost"))
    expected = number(offer.get("storage_cost")) * number(settings["disk_gb"]) / 720
    if (storage + Decimal("0.000001") < expected or
            number(offer.get("dph_base")) + storage > number(offer["dph_total"]) + Decimal("0.000001")):
        raise ValueError("quote does not include requested storage")
    limits = settings["offer_maximums"]
    maximum = (number(limits["dph_total"]) * number(settings["rental_hours"]) +
               number(limits["inet_down_cost"]) * number(settings["inbound_gb"]) +
               number(limits["inet_up_cost"]) * number(settings["outbound_gb"]) +
               number(settings.get("local_volume_maximum_usd", 0)))
    if maximum > number(settings["approved_maximum_usd"]):
        raise ValueError("launch allowances exceed the approved maximum")
    return {"offer_id": offer["id"], "quoted_hourly_usd": str(offer["dph_total"]),
            "maximum_charge_usd": f"{maximum:.2f}", "spending_admitted": False,
            "image_repository": settings["image_repository"], "create_options": settings["create_options"],
            "label": settings["label"], "worker_timeout_seconds": settings["worker_timeout_seconds"]}


def code_hashes():
    return ({name: sha256(CODE_ROOT / name) for name in CODE_FILES}
            | {name: sha256(path) for name, path in shared_code_files().items()})


def validate_gpu_assignments(assignments, names):
    if (not isinstance(assignments, dict) or set(assignments) != set(names)
            or any(type(gpu) is not int or gpu < 0 for gpu in assignments.values())
            or set(assignments.values()) != set(range(len(set(assignments.values()))))
            or not assignments):
        raise ValueError("GPU assignments must cover every candidate with consecutive indices starting at zero")


def prepare(config_paths, output, timeout_seconds=None, through="report", preparation_configs=None,
            gpu_assignments=None, cache_manifest=None, download_cache=False):
    """Copy only explicit inputs; no source code, credentials or host config."""
    if (timeout_seconds is not None and (type(timeout_seconds) is not int or timeout_seconds <= 0)
            or not config_paths or through not in ("preflight", "baseline", "train", "report", "preparation")):
        raise ValueError("runs and a positive timeout or no timeout are required")
    output = Path(output).resolve()
    if type(download_cache) is not bool or download_cache and cache_manifest is None:
        raise ValueError("cache download requires a cache manifest")
    if gpu_assignments is not None:
        validate_gpu_assignments(gpu_assignments, [Path(path).stem for path in config_paths])
    configurations = list(map(read_json, config_paths))
    if cache_manifest is not None:
        from sse_multivector.distillation_cache import bind
        bind(read_json(cache_manifest), configurations)
    pilots = [c for c in configurations if "training_milestones" in c and "preparation" not in c]
    if pilots:
        shared = [{k: v for k, v in c.items() if k not in
                   ("model", "revision", "lora_target_modules", "subject_batching")} for c in pilots]
        if len(pilots) != len(configurations) or any(c != shared[0] for c in shared[1:]):
            raise ValueError("shared pilot inputs or recipe differ between candidates")
    if through in ("report", "train") and not preparation_configs:
        if any(c.get("device") == "cuda" and c.get("fused_linear_cross_entropy")
               and "training_milestones" in c and "preparation" not in c
               for c in configurations):
            raise ValueError("CUDA subject pilot requires matched GPU preparation")
    if preparation_configs:
        if through != "report" or len(preparation_configs) != len(config_paths):
            raise ValueError("paired preparation requires one config per complete pilot run")
        for pilot_path, prep_path in zip(config_paths, preparation_configs):
            pilot, prep = read_json(pilot_path), read_json(prep_path)
            if (Path(pilot_path).stem != Path(prep_path).stem or "preparation" in pilot
                    or "preparation" not in prep or "training_milestones" not in pilot
                    or {k: v for k, v in prep.items() if k not in ("preparation", "training_milestones")}
                       != {k: v for k, v in pilot.items() if k not in ("training_milestones", "continuation")}):
                raise ValueError("preparation recipe differs from the pilot")
            preparation_data(load_data(prep["data"], prep.get("mask_prompt")), prep)
    if output.exists():
        raise FileExistsError(output)
    staging = output.with_name(output.name + ".partial")
    staging.mkdir(parents=True)
    try:
        names = set()
        runs = []
        all_paths = [(path, "configs") for path in config_paths]
        all_paths += [(path, "preparation-configs") for path in preparation_configs or []]
        for path, folder in all_paths:
            path = Path(path)
            name = path.stem
            if not re.fullmatch(r"[a-z][a-z0-9_-]*", name) or (folder, name) in names:
                raise ValueError("config filenames must be distinct lowercase run names")
            names.add((folder, name))
            config = read_json(path)
            data = Path(config["data"])
            prompt = Path(config["mask_prompt"]) if "mask_prompt" in config else None
            loaded = load_data(data, prompt)
            if "continuation" in config:
                parent, checkpoint, _, _ = subject_parent(loaded, config)
                subject_stage_summary(parent / "baseline", loaded)
                if "test" in loaded:
                    subject_test_summary(parent, loaded, config)
                parent_relative = "parents/" + sha256(parent / "manifest.json")
                destination = staging / parent_relative
                if not destination.exists():
                    destination.mkdir(parents=True)
                    for filename in ("manifest.json", "training-plan.json"):
                        shutil.copyfile(parent / filename, destination / filename)
                    for directory in (Path("baseline"), checkpoint.relative_to(parent),
                                      *([Path("test/baseline")] if "test" in loaded else [])):
                        shutil.copytree(parent / directory, destination / directory)
                config["continuation"] = {**config["continuation"], "parent_run": parent_relative}
            data_relative = "data/" + sha256(data / "manifest.json")
            (staging / data_relative).mkdir(parents=True, exist_ok=True)
            for filename in ("manifest.json", *read_json(data / "manifest.json")["outputs"]):
                shutil.copyfile(data / filename, staging / data_relative / filename)
            config["data"] = data_relative
            if prompt is not None:
                prompt_relative = "prompts/" + sha256(prompt) + ".txt"
                (staging / prompt_relative).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(prompt, staging / prompt_relative)
                config["mask_prompt"] = prompt_relative
            model = Path(config["model"])
            if model.is_dir():
                model_relative = "models/" + name
                if not (staging / model_relative).exists():
                    shutil.copytree(model, staging / model_relative)
                config["model"] = model_relative
            elif not re.fullmatch(r"[a-f0-9]{40}", config.get("revision") or ""):
                raise ValueError("remote models require an immutable revision")
            relative = folder + "/" + name + ".json"
            write_json(staging / relative, config)
            runs.append(relative)
        job = {"runs": runs[:len(config_paths)], "timeout_seconds": timeout_seconds, "through": through,
               "code": code_hashes()}
        if preparation_configs:
            job["preparation_runs"] = runs[len(config_paths):]
        if gpu_assignments is not None:
            job["gpu_assignments"] = gpu_assignments
        if cache_manifest is not None:
            shutil.copyfile(cache_manifest, staging / "model-cache.json")
            job["cache_manifest"] = "model-cache.json"
        if download_cache:
            job["download_cache"] = True
        write_json(staging / "job.json", job)
        write_manifest(staging, staging / "manifest.json", "distillation-inputs")
        staging.rename(output)
    except BaseException:
        shutil.rmtree(staging)
        raise
    return sha256(output / "manifest.json")


def prepare_continuation(parent_run, data, preparation_config, output, *, name, additional_passes=2,
                         cache_manifest=None):
    """Derive a single-model package from sealed training state, without inference."""
    if type(additional_passes) is not int or additional_passes < 1:
        raise ValueError("additional passes must be positive")
    if not re.fullmatch(r"[a-z][a-z0-9_-]*", name):
        raise ValueError("invalid continuation run name")
    parent_run = Path(parent_run).resolve()
    original = read_json(parent_run / "manifest.json")["config"]
    cache = None
    if not Path(original['model']).is_dir():
        if cache_manifest is None:
            raise ValueError('remote continuation requires a pinned model cache manifest')
        from sse_multivector.distillation_cache import validate
        cache = validate(read_json(cache_manifest))
        cache['models'] = [model for model in cache['models']
                          if (model['model'], model['revision']) == (original['model'], original['revision'])]
        validate(cache)
    if "continuation" in original or "preparation" in original:
        raise ValueError("continuation requires an original subject pilot")
    count = original["training_milestones"][-1]
    checkpoint = parent_run / "checkpoints" / f"checkpoint-{count}"
    config = {**original, "data": str(Path(data).resolve()),
        "training_milestones": [count * (i + 2) for i in range(additional_passes)],
        "continuation": {"parent_run": str(parent_run),
            "manifest_sha256": sha256(parent_run / "manifest.json"),
            "plan_sha256": sha256(parent_run / "training-plan.json"),
            "checkpoint_sha256": sha256(checkpoint / "complete.json")}}
    preparation = {**read_json(preparation_config), "data": config["data"]}
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        pilot_path, prep_path = root / "configs" / (name + ".json"), root / "preparation" / (name + ".json")
        write_json(pilot_path, config)
        write_json(prep_path, preparation)
        selected_cache = root / 'model-cache.json' if cache is not None else None
        if selected_cache is not None:
            write_json(selected_cache, cache)
        return prepare([pilot_path], output, preparation_configs=[prep_path], gpu_assignments={name: 0},
                       cache_manifest=selected_cache, download_cache=selected_cache is not None)


def verify_package(package):
    package = Path(package)
    verify_manifest(package, package / "manifest.json")
    job = read_json(package / "job.json")
    if job["code"] != code_hashes():
        raise ValueError("container code or dependencies differ from the prepared package")
    if "gpu_assignments" in job:
        validate_gpu_assignments(job["gpu_assignments"], [Path(path).stem for path in job["runs"]])
    if 'download_cache' in job and (job['download_cache'] is not True or 'cache_manifest' not in job):
        raise ValueError('cache download requires a cache manifest')
    for path in job['runs']:
        config = read_json(package / path)
        if ('continuation' in config and not (package / config['model']).is_dir()
                and not job.get('download_cache')):
            raise ValueError('remote continuation requires its pinned cache download')
    if "cache_manifest" in job:
        from sse_multivector.distillation_cache import bind
        if job["cache_manifest"] != "model-cache.json":
            raise ValueError("invalid cache manifest path")
        bind(read_json(package / job["cache_manifest"]),
             [read_json(package / r) for r in job["runs"] + job.get("preparation_runs", [])])
    return job


class StopRequested(RuntimeError):
    """An explicit controller stop, checked by the shared operator first."""


def run_process(command, timeout, *, stop_event=None, **kwargs):
    """Wait without an automatic kill when the frozen timeout is disabled."""
    worker_fd = os.environ.get("ORACLE_RUN_WORKER_LOCK_FD")
    if worker_fd is not None:
        descriptor = int(worker_fd)
        if descriptor < 3:
            raise ValueError("invalid inherited worker lock descriptor")
        os.fstat(descriptor)
        kwargs["pass_fds"] = tuple(set(kwargs.get("pass_fds", ())) | {descriptor})
    with subprocess.Popen(command, start_new_session=True, **kwargs) as process:
        deadline = time.monotonic() + timeout if timeout is not None else None
        try:
            while True:
                try:
                    if stop_event is not None and stop_event.is_set():
                        raise StopRequested("stopped by controller")
                    remaining = max(0, deadline - time.monotonic()) if deadline is not None else None
                    interval = min(remaining, .2) if remaining is not None else .2
                    process.wait(timeout=interval if stop_event is not None else remaining)
                    break
                except subprocess.TimeoutExpired:
                    if deadline is not None and time.monotonic() >= deadline:
                        raise
                except KeyboardInterrupt:
                    if timeout is not None:
                        raise
                    print("operator interrupted; unbounded job continues", file=sys.stderr, flush=True)
        except BaseException as error:
            if timeout is not None or isinstance(error, StopRequested):
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            raise
        return process


def execute(package, output):
    """Run each frozen candidate once; shared runner owns SSH and result sealing."""
    from datetime import datetime
    package, output = Path(package).resolve(), Path(output).resolve()
    job = verify_package(package)
    output.mkdir(parents=True, exist_ok=True)
    deadline = time.time() + job["timeout_seconds"] if job["timeout_seconds"] is not None else None
    if deadline is not None and os.environ.get("ORACLE_RUN_DEADLINE_UTC"):
        deadline = min(deadline, datetime.fromisoformat(os.environ["ORACLE_RUN_DEADLINE_UTC"].replace("Z", "+00:00")).timestamp())
    state = {"state": "running", "package_sha256": sha256(package / "manifest.json"), "deadline": deadline}
    assignments = job.get("gpu_assignments", {})
    visible = os.environ.get("CUDA_VISIBLE_DEVICES")
    lock, stop_event = threading.Lock(), threading.Event()
    state.update(gpu_assignments=assignments, active_runs={})
    write_json(output / "deployment.json", state)
    def stop(signum, frame):
        stop_event.set()
        raise StopRequested("stopped by controller")
    def interrupt(signum, frame):
        print("operator interrupted; unbounded job continues", file=sys.stderr, flush=True)
    previous = signal.signal(signal.SIGTERM, stop)
    previous_interrupt = signal.signal(signal.SIGINT, interrupt) if deadline is None else None
    try:
        if "cache_manifest" in job:
            from sse_multivector.distillation_cache import download, verify
            if job.get('download_cache'):
                state.update(stage='download', preparation=False)
                write_json(output / 'deployment.json', state)
                receipt = download(package / job['cache_manifest'], output / 'model-cache')
                write_json(output / 'cache-verification.json', receipt)
            else:
                verify(package / job["cache_manifest"], output / "cache-verification.json")
        if assignments and visible is not None and (len(visible.split(",")) <= max(assignments.values())
                or any(not value.strip() for value in visible.split(","))):
            raise ValueError("GPU assignments exceed the inherited CUDA_VISIBLE_DEVICES")
        bindings = {gpu: visible.split(",")[gpu].strip() if visible is not None else str(gpu)
                    for gpu in set(assignments.values())}
        if assignments and job["through"] != "preflight" and any(
                read_json(package / r).get("device") == "cuda" for r in job["runs"]):
            import torch
            if torch.cuda.device_count() <= max(assignments.values()):
                raise ValueError("GPU assignments exceed the visible CUDA devices")

        def candidate(relative):
            name = Path(relative).stem
            config = read_json(package / relative)
            for key in ("data", "mask_prompt"):
                if key in config:
                    config[key] = str(package / config[key])
            if (package / config["model"]).is_dir():
                config["model"] = str(package / config["model"])
            if "continuation" in config:
                config["continuation"] = {**config["continuation"],
                    "parent_run": str(package / config["continuation"]["parent_run"])}
            return name, config

        def invoke(relative, mode, preparing=False):
            remaining = deadline - time.time() if deadline is not None else None
            if remaining is not None and remaining <= 0:
                raise TimeoutError("experiment exceeded its frozen runtime limit")
            name, config = candidate(relative)
            root = output / "preparation" if preparing else output
            root.mkdir(parents=True, exist_ok=True)
            config_path = root / "configs" / (name + ".json")
            write_json(config_path, config)
            env = {**os.environ, "PYTHONPATH": str(CODE_ROOT)}
            if "cache_manifest" in job:
                env.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                           HF_HUB_DISABLE_IMPLICIT_TOKEN="1")
            gpu = assignments.get(name)
            if gpu is not None:
                env["CUDA_VISIBLE_DEVICES"] = bindings[gpu]
            with lock:
                state.update(stage=mode, preparation=preparing)
                if not assignments:
                    state["candidate"] = name
                state["active_runs"][name] = {"stage": mode, "preparation": preparing, "gpu": gpu,
                                              "cuda_visible_devices": env.get("CUDA_VISIBLE_DEVICES")}
                write_json(output / "deployment.json", state)
            try:
                with (root / (name + ".log")).open("a") as log:
                    result = run_process([sys.executable, "-m", "sse_multivector.distillation_run",
                        str(config_path), "--output", str(root / name), "--through", mode],
                        cwd=CODE_ROOT, stdout=log, stderr=subprocess.STDOUT, env=env, timeout=remaining,
                        stop_event=stop_event if assignments else None)
                if result.returncode:
                    raise RuntimeError(f"run {name} failed with exit code {result.returncode}; see {name}.log")
                return root / name, config
            finally:
                with lock:
                    state["active_runs"].pop(name)
                    write_json(output / "deployment.json", state)

        def run_stage(relatives, mode, preparing=False, verify=None):
            def complete(relative):
                directory, config = invoke(relative, mode, preparing)
                if verify is not None:
                    verify(directory, config)
            if not assignments:
                for relative in relatives:
                    complete(relative)
                return
            lanes, failed = {}, threading.Event()
            for relative in relatives:
                lanes.setdefault(assignments[Path(relative).stem], []).append(relative)
            def lane(runs):
                for relative in runs:
                    if failed.is_set() or stop_event.is_set():
                        return
                    try:
                        complete(relative)
                    except BaseException as error:
                        failed.set()
                        with lock:
                            state.setdefault("failures", {})[Path(relative).stem] = str(error)
                            write_json(output / "deployment.json", state)
                        raise
            if lanes:
                errors = []
                with ThreadPoolExecutor(max_workers=len(lanes)) as pool:
                    futures = [pool.submit(lane, runs) for runs in lanes.values()]
                    for future in as_completed(futures):
                        try:
                            future.result()
                        except BaseException as error:
                            errors.append(error)
                if errors:
                    raise errors[0]

        run_stage(job.get("preparation_runs", []), "preparation", preparing=True,
                  verify=lambda directory, config: verify_subject_run(
                      directory, load_data(config["data"]), config, "preparation"))

        pilots = [r for r in job["runs"] if "training_milestones" in read_json(package / r)
                  and "preparation" not in read_json(package / r)]
        if pilots and len(pilots) != len(job["runs"]):
            raise ValueError("subject pilot candidates cannot be mixed with legacy runs")
        if pilots and job["through"] in ("baseline", "train", "report"):
            baselines = {}
            def verify_baseline(directory, config):
                data = load_data(config["data"])
                name = directory.name
                if "continuation" in config:
                    directory = subject_parent(data, config)[0]
                summary = subject_stage_summary(directory / "baseline", data)
                if "test" in data:
                    summary["test"] = subject_test_summary(directory, data, config)
                with lock:
                    baselines[name] = summary
            continuing = [r for r in pilots if "continuation" in read_json(package / r)]
            for relative in continuing:
                name, config = candidate(relative)
                verify_baseline(output / name, config)
            run_stage([r for r in pilots if r not in continuing], "baseline", verify=verify_baseline)
            write_json(output / "baselines-integrity.json", baselines)
        if job["through"] != "baseline" or not pilots:
            def verify_run(directory, config):
                if "training_milestones" in config and job["through"] in ("report", "preparation"):
                    data = load_data(config["data"])
                    verify_subject_run(directory, data, config, job["through"])
            run_stage(job["runs"], job["through"], verify=verify_run)
        if pilots and job["through"] == "report":
            write_json(output / "integrity.json", verify_results(package, output))
        state["state"] = "complete"
        return state
    except BaseException as error:
        state.update(state="failed", error=str(error))
        raise
    finally:
        state["finished"] = time.time()
        write_json(output / "deployment.json", state)
        signal.signal(signal.SIGTERM, previous)
        if previous_interrupt is not None:
            signal.signal(signal.SIGINT, previous_interrupt)


def status(output):
    """Read mechanical progress, keeping reserved-test results out of review."""
    output = Path(output)
    path = output / "deployment.json"
    result = {"deployment": read_json(path) if path.exists() else {}, "candidates": {}, "preparation": {}}
    for root, group in ((output, "candidates"), (output / "preparation", "preparation")):
        for config in sorted((root / "configs").glob("*.json")):
            directory = root / config.stem
            path = directory / "preflight.json"
            counts = read_json(path) if path.exists() else {}
            candidate = {"evaluations": {}, "tests": {}, "checkpoints": []}
            ages = []
            for prefix, target in (("baseline", "evaluations"), ("evaluations", "evaluations"), ("test", "tests")):
                stages = [directory / prefix] if prefix == "baseline" else sorted((directory / prefix).glob("*"))
                for stage in stages:
                    notes = sorted(stage.glob("note-*/complete.json"))
                    if not notes:
                        continue
                    ages.extend(p.stat().st_mtime for p in notes)
                    summary = {"notes": len(notes), "expected_notes": counts.get(
                        "test_notes" if target == "tests" else "evaluation_notes")}
                    if target != "tests":
                        summary["subject_failures"] = sum(bool(read_json(p.parent / "subjects-result.json")["errors"])
                                                          for p in notes)
                    candidate[target][stage.name] = summary
            for checkpoint in sorted((directory / "checkpoints").glob("checkpoint-*/complete.json")):
                metadata = read_json(checkpoint.parent / "training.json")
                candidate["checkpoints"].append({key: metadata[key] for key in ("cursor", "updates")})
                ages.append(checkpoint.stat().st_mtime)
            updates = directory / "subject-training-updates.jsonl"
            if updates.exists():
                with updates.open("rb") as source:
                    source.seek(max(0, updates.stat().st_size - 65536))
                    tail = source.read()
                lines = tail.splitlines() if tail.endswith(b"\n") else tail.splitlines()[:-1]
                if lines:
                    last = json.loads(lines[-1])
                    candidate["training"] = {key: last[key] for key in (
                        "cursor", "update", "updates", "loss", "gradient_norm", "seconds", "cuda_allocated_bytes",
                        "cuda_reserved_bytes", "attempt_id") if key in last}
                    ages.append(updates.stat().st_mtime)
            candidate["last_progress_age_seconds"] = max(0, time.time() - max(ages)) if ages else None
            result[group][config.stem] = candidate
    return result


def verify_results(package, output, *, expected_volume=None):
    """Recheck retrieved comparisons locally; no GPU, generation or provider calls."""
    package, output = Path(package), Path(output)
    job = verify_package(package)
    if job.get('download_cache'):
        from sse_multivector.distillation_cache import verify_results as verify_cache_results
        verify_cache_results(package / job['cache_manifest'], output / 'model-cache', expected_volume)
    results = {}
    for relative in job["runs"]:
        config = read_json(package / relative)
        if "training_milestones" not in config or job["through"] != "report":
            raise ValueError("comparison verification requires subject pilot reports")
        name = Path(relative).stem
        data = load_data(package / config["data"])
        results[name] = verify_subject_run(output / name, data, config, "report", package=package)
    for relative in job.get("preparation_runs", []):
        config = read_json(package / relative)
        data = load_data(package / config["data"])
        verify_subject_run(output / "preparation" / Path(relative).stem, data, config, "preparation")
    return {"status": "complete", "candidates": results,
            "semantic_review": "Pending local review; compute completeness does not establish a winner."}


def review_completion(package, operation):
    """Write the shared deletion prerequisite only after local work verification."""
    from vast import runner
    operation = Path(operation).resolve()
    receipt_path = operation / "launch/retrieval-verification.json"
    receipt = read_json(receipt_path)
    context = runner.Context.load(argparse.Namespace(root=operation,
        config=operation / "operation-contract.json", operation="status"))
    instance_id = runner.recorded_instance_id(context)
    if instance_id is None or receipt["instance_id"] != instance_id:
        raise ValueError("retrieval belongs to another instance")
    if sha256(Path(package) / "manifest.json") != sha256(context.path("transport/workload/inputs/manifest.json")):
        raise ValueError("comparison package differs from the frozen operation")
    candidate = context.path("result") if context.path("result").is_dir() else context.path("result.next")
    # Check transfer integrity first, then account for every baseline/checkpoint/
    # evaluation. Neither a worker's exit code nor its own report is sufficient.
    runner.verify_command_results(context, candidate)
    checked = verify_results(package, candidate / "work/results", expected_volume=context.config.get('local_volume'))
    write_json(operation / "launch/completion-integrity.json", checked)
    review = {"complete": True, "instance_id": instance_id,
        "operation_contract_sha256": sha256(context.config_path),
        "retrieval_verification_sha256": sha256(receipt_path),
        "integrity_sha256": sha256(operation / "launch/completion-integrity.json"),
        "checks": ["All required candidate baselines and checkpoint evaluations accounted for.",
                   "All required reserved test collections complete, source-bound and sealed for local review.",
                   "Raw/parsed subjects and batch receipts agree; model failures remain counted.",
                   "Every planned training-note use and update verified; all continuing checkpoints retained.",
                   "Matched preparation and local transfer verification complete."]}
    write_json(operation / "launch/completion-review.json", review)
    runner.verify_completion_review(context, instance_id, None)
    return review


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="operation", required=True)
    prepare_parser = commands.add_parser("prepare")
    prepare_parser.add_argument("--config", type=Path, action="append", required=True)
    prepare_parser.add_argument("--preparation-config", type=Path, action="append",
                                help="paired prep recipe; verified prep continues into fresh pilot runs")
    prepare_parser.add_argument("--gpu-assignments", type=Path,
                                help="JSON mapping each candidate name to its exclusive GPU index")
    prepare_parser.add_argument("--cache-manifest", type=Path,
                                help="required model files, verified offline before any GPU work")
    prepare_parser.add_argument("--output", type=Path, required=True)
    prepare_parser.add_argument("--timeout-seconds", type=int,
                                help="optional execution deadline; omitted means no automatic stop")
    prepare_parser.add_argument("--through", choices=("preflight", "baseline", "train", "report", "preparation"), default="report")
    continuation_parser = commands.add_parser("prepare-continuation", help="freeze a single-model continuation; no inference or rental")
    continuation_parser.add_argument("--parent-run", type=Path, required=True)
    continuation_parser.add_argument("--data", type=Path, required=True)
    continuation_parser.add_argument("--preparation-config", type=Path, required=True)
    continuation_parser.add_argument("--name", required=True)
    continuation_parser.add_argument("--additional-passes", type=int, default=2)
    continuation_parser.add_argument("--cache-manifest", type=Path,
        help="pinned model files; the selected model downloads and verifies on the same rental")
    continuation_parser.add_argument("--output", type=Path, required=True)
    offer_parser = commands.add_parser("check-offer", help="validate a saved quote without renting")
    offer_parser.add_argument("--settings", type=Path, required=True)
    offer_parser.add_argument("--offers", type=Path, required=True)
    offer_parser.add_argument("--offer-id", type=int, required=True)
    execute_parser = commands.add_parser("execute")
    execute_parser.add_argument("--package", type=Path, required=True)
    execute_parser.add_argument("--output", type=Path, default=Path("results"))
    status_parser = commands.add_parser("status", help="read progress without exposing test answers")
    status_parser.add_argument("--output", type=Path, required=True)
    verify_parser = commands.add_parser("verify-results", help="check retrieved subject pilot completeness offline")
    verify_parser.add_argument("--package", type=Path, required=True)
    verify_parser.add_argument("--output", type=Path, required=True)
    verify_parser.add_argument("--operation-root", type=Path,
                               help="also verify the retrieved operation and record its completion review")
    args = parser.parse_args()
    if args.operation == "status":
        result = status(args.output)
    elif args.operation == "prepare-continuation":
        result = {"package_sha256": prepare_continuation(args.parent_run, args.data,
            args.preparation_config, args.output, name=args.name, additional_passes=args.additional_passes,
            cache_manifest=args.cache_manifest)}
    elif args.operation == "prepare":
        result = {"package_sha256": prepare(args.config, args.output, args.timeout_seconds, args.through,
                                             args.preparation_config,
                                             read_json(args.gpu_assignments) if args.gpu_assignments else None,
                                             args.cache_manifest)}
    elif args.operation == "check-offer":
        offers = read_json(args.offers)
        if isinstance(offers, dict):
            offers = offers["offers"]
        matches = [o for o in offers if o["id"] == args.offer_id]
        if len(matches) != 1:
            raise ValueError("expected exactly one matching offer")
        result = check_offer(read_json(args.settings), matches[0])
    elif args.operation == "verify-results":
        result = verify_results(args.package, args.output)
        if args.operation_root:
            result["completion_review"] = review_completion(args.package, args.operation_root)
    else:
        result = execute(args.package, args.output)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
