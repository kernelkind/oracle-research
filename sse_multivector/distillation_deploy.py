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
from sse_multivector.distillation_run import load_data, read_json, sha256, write_json


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


def prepare(config_paths, output, timeout_seconds, through="report"):
    """Copy only explicit inputs; no source code, credentials or host config."""
    if timeout_seconds <= 0 or not config_paths or through not in ("preflight", "baseline", "train", "report"):
        raise ValueError("runs and a positive timeout are required")
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError(output)
    staging = output.with_name(output.name + ".partial")
    staging.mkdir(parents=True)
    try:
        names = set()
        runs = []
        for path in config_paths:
            path = Path(path)
            name = path.stem
            if not re.fullmatch(r"[a-z][a-z0-9_-]*", name) or name in names:
                raise ValueError("config filenames must be distinct lowercase run names")
            names.add(name)
            config = read_json(path)
            data = Path(config["data"])
            prompt = Path(config["mask_prompt"]) if "mask_prompt" in config else None
            load_data(data, prompt)
            data_relative = "data/" + sha256(data / "manifest.json")
            (staging / data_relative).mkdir(parents=True, exist_ok=True)
            for filename in ("manifest.json", "train.jsonl", "evaluation.jsonl", "references.jsonl"):
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
                shutil.copytree(model, staging / model_relative)
                config["model"] = model_relative
            elif not re.fullmatch(r"[a-f0-9]{40}", config.get("revision") or ""):
                raise ValueError("remote models require an immutable revision")
            relative = "configs/" + name + ".json"
            write_json(staging / relative, config)
            runs.append(relative)
        write_json(staging / "job.json", {"runs": runs, "timeout_seconds": timeout_seconds, "through": through,
                                          "code": code_hashes()})
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


def run_process(command, timeout, **kwargs):
    """Bound the whole process group, including download/training children."""
    with subprocess.Popen(command, start_new_session=True, **kwargs) as process:
        try:
            process.wait(timeout=timeout)
        except BaseException:
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
    deadline = time.time() + job["timeout_seconds"]
    if os.environ.get("ORACLE_RUN_DEADLINE_UTC"):
        deadline = min(deadline, datetime.fromisoformat(os.environ["ORACLE_RUN_DEADLINE_UTC"].replace("Z", "+00:00")).timestamp())
    state = {"state": "running", "package_sha256": sha256(package / "manifest.json"), "deadline": deadline}
    write_json(output / "deployment.json", state)
    def stop(signum, frame):
        raise RuntimeError("stopped by controller")
    previous = signal.signal(signal.SIGTERM, stop)
    try:
        for relative in job["runs"]:
            remaining = deadline - time.time()
            if remaining <= 0:
                raise TimeoutError("experiment exceeded its frozen runtime limit")
            name = Path(relative).stem
            config = read_json(package / relative)
            for key in ("data", "mask_prompt"):
                if key in config:
                    config[key] = str(package / config[key])
            if (package / config["model"]).is_dir():
                config["model"] = str(package / config["model"])
            config_path = output / "configs" / (name + ".json")
            write_json(config_path, config)
            with (output / (name + ".log")).open("a") as log:
                result = run_process([sys.executable, "-m", "sse_multivector.distillation_run",
                    str(config_path), "--output", str(output / name), "--through", job["through"]],
                    cwd=CODE_ROOT, stdout=log, stderr=subprocess.STDOUT,
                    env={**os.environ, "PYTHONPATH": str(CODE_ROOT)}, timeout=remaining)
            if result.returncode:
                raise RuntimeError(f"run {name} failed with exit code {result.returncode}; see {name}.log")
        state["state"] = "complete"
        return state
    except BaseException as error:
        state.update(state="failed", error=str(error))
        raise
    finally:
        state["finished"] = time.time()
        write_json(output / "deployment.json", state)
        signal.signal(signal.SIGTERM, previous)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="operation", required=True)
    prepare_parser = commands.add_parser("prepare")
    prepare_parser.add_argument("--config", type=Path, action="append", required=True)
    prepare_parser.add_argument("--output", type=Path, required=True)
    prepare_parser.add_argument("--timeout-seconds", type=int, required=True)
    prepare_parser.add_argument("--through", choices=("preflight", "baseline", "train", "report"), default="report")
    offer_parser = commands.add_parser("check-offer", help="validate a saved quote without renting")
    offer_parser.add_argument("--settings", type=Path, required=True)
    offer_parser.add_argument("--offers", type=Path, required=True)
    offer_parser.add_argument("--offer-id", type=int, required=True)
    execute_parser = commands.add_parser("execute")
    execute_parser.add_argument("--package", type=Path, required=True)
    execute_parser.add_argument("--output", type=Path, default=Path("results"))
    args = parser.parse_args()
    if args.operation == "prepare":
        result = {"package_sha256": prepare(args.config, args.output, args.timeout_seconds, args.through)}
    elif args.operation == "check-offer":
        offers = read_json(args.offers)
        if isinstance(offers, dict):
            offers = offers["offers"]
        matches = [o for o in offers if o["id"] == args.offer_id]
        if len(matches) != 1:
            raise ValueError("expected exactly one matching offer")
        result = check_offer(read_json(args.settings), matches[0])
    else:
        result = execute(args.package, args.output)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
