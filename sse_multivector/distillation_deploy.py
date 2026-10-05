"""Freeze distillation inputs and execute them as a shared Vast command workload."""
import argparse
from decimal import Decimal, InvalidOperation
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time

from gte.full_build_package import write_manifest, verify_manifest
from sse_multivector.distillation_run import (load_data, read_json, sha256, write_json,
    preparation_data, subject_stage_summary, subject_test_summary, verify_subject_run)


CODE_ROOT = Path(__file__).resolve().parents[1]
CODE_FILES = (
    "sse_multivector/distillation_deploy.py", "sse_multivector/distillation_run.py",
    "sse_multivector/distillation_data.py", "sse_multivector/extraction_pipeline.py",
    "sse_multivector/mask_positions.py", "sse_multivector/distillation/requirements.lock",
    "sse_multivector/distillation/requirements-gpu.lock",
    "sse_multivector/distillation_vast.py", "sse_multivector/distillation/vast-launch.json",
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
               number(limits["inet_up_cost"]) * number(settings["outbound_gb"]))
    if maximum > number(settings["approved_maximum_usd"]):
        raise ValueError("launch allowances exceed the approved maximum")
    return {"offer_id": offer["id"], "quoted_hourly_usd": str(offer["dph_total"]),
            "maximum_charge_usd": f"{maximum:.2f}", "spending_admitted": False,
            "image_repository": settings["image_repository"], "create_options": settings["create_options"],
            "label": settings["label"], "worker_timeout_seconds": settings["worker_timeout_seconds"]}


def code_hashes():
    return {name: sha256(CODE_ROOT / name) for name in CODE_FILES}


def prepare(config_paths, output, timeout_seconds=None, through="report", preparation_configs=None):
    """Copy only explicit inputs; no source code, credentials or host config."""
    if (timeout_seconds is not None and (type(timeout_seconds) is not int or timeout_seconds <= 0)
            or not config_paths or through not in ("preflight", "baseline", "train", "report", "preparation")):
        raise ValueError("runs and a positive timeout or no timeout are required")
    output = Path(output).resolve()
    configurations = list(map(read_json, config_paths))
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
                       != {k: v for k, v in pilot.items() if k != "training_milestones"}):
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
            load_data(data, prompt)
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
        write_json(staging / "job.json", job)
        write_manifest(staging, staging / "manifest.json", "distillation-inputs")
        staging.rename(output)
    except BaseException:
        shutil.rmtree(staging)
        raise
    return sha256(output / "manifest.json")


def verify_package(package):
    package = Path(package)
    verify_manifest(package, package / "manifest.json")
    job = read_json(package / "job.json")
    if job["code"] != code_hashes():
        raise ValueError("container code or dependencies differ from the prepared package")
    return job


class StopRequested(RuntimeError):
    """An explicit controller stop, checked by the shared operator first."""


def run_process(command, timeout, **kwargs):
    """Wait without an automatic kill when the frozen timeout is disabled."""
    with subprocess.Popen(command, start_new_session=True, **kwargs) as process:
        try:
            while True:
                try:
                    process.wait(timeout=timeout)
                    break
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
    write_json(output / "deployment.json", state)
    def stop(signum, frame):
        raise StopRequested("stopped by controller")
    previous = signal.signal(signal.SIGTERM, stop)
    try:
        def candidate(relative):
            name = Path(relative).stem
            config = read_json(package / relative)
            for key in ("data", "mask_prompt"):
                if key in config:
                    config[key] = str(package / config[key])
            if (package / config["model"]).is_dir():
                config["model"] = str(package / config["model"])
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
            state.update(stage=mode, candidate=name, preparation=preparing)
            write_json(output / "deployment.json", state)
            with (root / (name + ".log")).open("a") as log:
                result = run_process([sys.executable, "-m", "sse_multivector.distillation_run",
                    str(config_path), "--output", str(root / name), "--through", mode],
                    cwd=CODE_ROOT, stdout=log, stderr=subprocess.STDOUT,
                    env={**os.environ, "PYTHONPATH": str(CODE_ROOT)}, timeout=remaining)
            if result.returncode:
                raise RuntimeError(f"run {name} failed with exit code {result.returncode}; see {name}.log")
            return root / name, config

        for relative in job.get("preparation_runs", []):
            directory, config = invoke(relative, "preparation", preparing=True)
            verify_subject_run(directory, load_data(config["data"]), config, "preparation")

        pilots = [r for r in job["runs"] if "training_milestones" in read_json(package / r)
                  and "preparation" not in read_json(package / r)]
        if pilots and len(pilots) != len(job["runs"]):
            raise ValueError("subject pilot candidates cannot be mixed with legacy runs")
        if pilots and job["through"] in ("baseline", "train", "report"):
            baselines = {}
            for relative in pilots:
                directory, config = invoke(relative, "baseline")
                data = load_data(config["data"])
                baselines[directory.name] = subject_stage_summary(directory / "baseline", data)
                if "test" in data:
                    baselines[directory.name]["test"] = subject_test_summary(directory, data, config)
            write_json(output / "baselines-integrity.json", baselines)
        if job["through"] != "baseline" or not pilots:
            for relative in job["runs"]:
                directory, config = invoke(relative, job["through"])
                if "training_milestones" in config and job["through"] in ("report", "preparation"):
                    data = load_data(config["data"])
                    verify_subject_run(directory, data, config, job["through"])
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


def verify_results(package, output):
    """Recheck retrieved comparisons locally; no GPU, generation or provider calls."""
    package, output = Path(package), Path(output)
    job = verify_package(package)
    results = {}
    for relative in job["runs"]:
        config = read_json(package / relative)
        if "training_milestones" not in config or job["through"] != "report":
            raise ValueError("comparison verification requires subject pilot reports")
        name = Path(relative).stem
        data = load_data(package / config["data"])
        results[name] = verify_subject_run(output / name, data, config, "report")
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
    checked = verify_results(package, candidate / "work/results")
    write_json(operation / "launch/completion-integrity.json", checked)
    review = {"complete": True, "instance_id": instance_id,
        "operation_contract_sha256": sha256(context.config_path),
        "retrieval_verification_sha256": sha256(receipt_path),
        "integrity_sha256": sha256(operation / "launch/completion-integrity.json"),
        "checks": ["All required candidate baselines and checkpoint evaluations accounted for.",
                   "Reserved baseline/final test collections complete, source-bound and sealed for local review.",
                   "Raw/parsed subjects and batch receipts agree; model failures remain counted.",
                   "Every training note used once; all continuing checkpoints retained.",
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
    prepare_parser.add_argument("--output", type=Path, required=True)
    prepare_parser.add_argument("--timeout-seconds", type=int,
                                help="optional execution deadline; omitted means no automatic stop")
    prepare_parser.add_argument("--through", choices=("preflight", "baseline", "train", "report", "preparation"), default="report")
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
    elif args.operation == "prepare":
        result = {"package_sha256": prepare(args.config, args.output, args.timeout_seconds, args.through,
                                             args.preparation_config)}
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
