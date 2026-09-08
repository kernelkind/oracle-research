#!/usr/bin/env python3
"""Prepare the saved SSE command, then optionally execute it with cgroup diagnostics.

prepare never starts Docker. run requires a separate explicit invocation and
refuses an existing run directory. Sampling is diagnostic only: it neither
admits additional work nor pauses the worker or changes its encoding behavior.
"""

import argparse
import hashlib
import json
import subprocess
import sys
import time
from collections import deque
from pathlib import Path


EXPERIMENT = Path(__file__).resolve().parents[1]
ROOT = EXPERIMENT.parents[1]
sys.path.insert(0, str(ROOT))

from sse_multivector.real_note_segmentation import (  # noqa: E402
    _canonical,
    _new_output,
    _prepared_files,
    _write_output,
)


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _plan_files(prepared, plan_directory, output):
    files, request, mapping, encoder = _prepared_files(prepared)
    if encoder != read(EXPERIMENT / "vectors/encoder.json"):
        raise ValueError("prepared encoder differs from the frozen original encoder")
    if sha(ROOT / encoder["worker_path"]) != encoder["worker_sha256"]:
        raise ValueError("worker differs from its frozen SHA-256")
    for name in ("subject-package.json", "mask-package.json"):
        if files[name] != (EXPERIMENT / "vectors" / name).read_bytes():
            raise ValueError(
                f"prepared package differs from the frozen original: {name}"
            )
    baseline_path = EXPERIMENT / "encoder-run/execution-plan.json"
    config_path = EXPERIMENT / "encoder-run/worker-config.json"
    baseline, config = read(baseline_path), read(config_path)
    limits = {"cpus": 4, "memory_bytes": 8589934592, "swap_bytes": 0}
    required = {
        "--cpus": "4",
        "--memory": "8g",
        "--memory-swap": "8g",
        "--network": "none",
        "--security-opt": "no-new-privileges",
        "--cap-drop": "ALL",
    }
    argv = baseline["argv"][:]
    if (
        baseline["resource_limits"] != limits
        or any(
            argv.count(flag) != 1 or argv[argv.index(flag) + 1] != value
            for flag, value in required.items()
        )
        or any(
            argv.count(flag) != 1
            for flag in ("--pull=never", "--read-only", encoder["container_image"])
        )
    ):
        raise ValueError(
            "saved Docker command differs from frozen resource limits/profile/image"
        )
    for field in (
        "checkpoint_sha256",
        "base_model_artifact_tree_sha256",
        "container_image",
        "model",
        "note_batch_size",
    ):
        if config[field] != encoder[field]:
            raise ValueError(
                f"saved worker config differs from frozen encoder: {field}"
            )
    if config["device"] != "cpu":
        raise ValueError("saved worker config differs from frozen CPU device")
    config["request_sha256"] = hashlib.sha256(files["worker-request.json"]).hexdigest()
    config_raw = _canonical(config)
    name = (
        "oracle-coverage-sse-" + hashlib.sha256(str(output).encode()).hexdigest()[:12]
    )
    argv[argv.index("--name") + 1] = name
    replacements = {
        str(EXPERIMENT / "encoder-input/worker-request.json"): str(
            prepared / "worker-request.json"
        ),
        str(EXPERIMENT / "encoder-run/worker-config.json"): str(
            plan_directory / "worker-config.json"
        ),
        str(EXPERIMENT / "encoder-run"): str(output),
    }
    for index, argument in enumerate(argv):
        for original, replacement in replacements.items():
            argument = argument.replace(original, replacement)
        argv[index] = argument
    plan = {
        "schema_version": 1,
        "helper_sha256": sha(Path(__file__)),
        "prepared": str(prepared),
        "prepared_manifest_sha256": sha(prepared / "manifest.json"),
        "baseline_execution_plan_sha256": sha(baseline_path),
        "baseline_worker_config_sha256": sha(config_path),
        "worker_config_sha256": hashlib.sha256(config_raw).hexdigest(),
        "output_directory": str(output),
        "container_name": name,
        "cwd": baseline["cwd"],
        "argv": argv,
        "resource_limits": baseline["resource_limits"],
        "note_count": len(mapping["notes"]),
        "encoded_note_count": len(request["notes"]),
        "vector_count": mapping["vector_count"],
        "admission": "One capped SSE invocation only, after generation and mask review finish. No other work is admitted during encoding.",
        "diagnostics": "Actual Docker cgroup sampled every 250 ms; rolling two-second io.pressure some-total diagnostic only. No SIGSTOP or runtime encoding changes.",
    }
    return {
        "worker-config.json": config_raw,
        "execution-plan.json": _canonical(plan),
    }, plan


def prepare(prepared_path, plan_path, output_path):
    _new_output(Path(plan_path))
    _new_output(Path(output_path))
    prepared, plan_directory, output = (
        Path(path).resolve() for path in (prepared_path, plan_path, output_path)
    )
    files, plan = _plan_files(prepared, plan_directory, output)
    _write_output(plan_directory, files)
    return plan


def _cgroup(docker, container_name):
    result = subprocess.run(
        [docker, "inspect", "--format", "{{.State.Pid}}", container_name],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=2,
        check=False,
    )
    if (
        result.returncode
        or not result.stdout.strip().isdigit()
        or int(result.stdout.strip()) <= 0
    ):
        return None
    for line in (
        Path(f"/proc/{int(result.stdout.strip())}/cgroup").read_text().splitlines()
    ):
        if line.startswith("0::"):
            return Path("/sys/fs/cgroup") / line[3:].lstrip("/")
    raise ValueError("Docker process has no unified cgroup")


def _sample(cgroup):
    for attempt in range(3):
        try:
            memory = int((cgroup / "memory.current").read_text())
            events = (cgroup / "memory.events").read_text()
            pressure = (cgroup / "io.pressure").read_text()
            some = next(
                line for line in pressure.splitlines() if line.startswith("some ")
            )
            total = int(
                dict(field.split("=", 1) for field in some.split()[1:])["total"]
            )
            if memory < 0 or total < 0:
                raise ValueError("negative cgroup memory or pressure counter")
            return {
                "memory_current": memory,
                "memory_events": events,
                "io_pressure": pressure,
                "io_some_total_microseconds": total,
            }
        except (OSError, ValueError, KeyError, StopIteration):
            if attempt == 2:
                raise
            time.sleep(0.01)


def _pressure(window, elapsed, total):
    if window and total < window[-1][1]:
        window.clear()
    window.append((elapsed, total))
    while len(window) > 1 and elapsed - window[1][0] >= 2:
        window.popleft()
    duration = elapsed - window[0][0]
    return (
        100 * (total - window[0][1]) / (duration * 1_000_000) if duration >= 2 else None
    )


def run(plan_path):
    plan_directory = Path(plan_path).resolve()
    plan = read(plan_directory / "execution-plan.json")
    output = Path(plan["output_directory"])
    _new_output(output)
    expected, _ = _plan_files(Path(plan["prepared"]), plan_directory, output)
    for name, raw in expected.items():
        if (plan_directory / name).read_bytes() != raw:
            raise ValueError(f"saved execution plan/config changed: {name}")
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    process, cgroup, error = None, None, None
    count, sampled, failures, peak, maximum, oom = 0, 0, 0, 0, None, False
    window, cleanup = deque(), None
    try:
        with (
            (output / "worker.stdout").open("xb") as stdout,
            (output / "worker.stderr").open("xb") as stderr,
            (output / "resources.jsonl").open("xb") as resources,
        ):
            process = subprocess.Popen(
                plan["argv"],
                cwd=plan["cwd"],
                stdin=subprocess.DEVNULL,
                stdout=stdout,
                stderr=stderr,
            )
            while process.poll() is None:
                sample = {"elapsed_seconds": time.monotonic() - started}
                try:
                    if cgroup is None:
                        cgroup = _cgroup(plan["argv"][0], plan["container_name"])
                    if cgroup is not None:
                        sample.update(_sample(cgroup))
                        sampled += 1
                        peak = max(peak, sample["memory_current"])
                        events = dict(
                            line.split()
                            for line in sample["memory_events"].splitlines()
                        )
                        oom = oom or any(
                            int(events.get(key, 0)) > 0 for key in ("oom", "oom_kill")
                        )
                        pressure = _pressure(
                            window,
                            sample["elapsed_seconds"],
                            sample["io_some_total_microseconds"],
                        )
                        if pressure is not None:
                            sample["rolling_two_second_io_pressure_percent"] = pressure
                            maximum = (
                                pressure if maximum is None else max(maximum, pressure)
                            )
                except (
                    OSError,
                    ValueError,
                    KeyError,
                    StopIteration,
                    subprocess.SubprocessError,
                ) as problem:
                    sample["sampling_error"] = f"{type(problem).__name__}: {problem}"
                    failures += 1
                resources.write(_canonical(sample))
                resources.flush()
                count += 1
                time.sleep(0.25)
            process.wait()
    except BaseException as problem:
        error = f"{type(problem).__name__}: {problem}"
        raise
    finally:
        if process is not None and process.poll() is None:
            # Cancellation stops only this owned container; never freeze it.
            command = [plan["argv"][0], "stop", "--time", "10", plan["container_name"]]
            try:
                stopped = subprocess.run(
                    command,
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    timeout=15,
                    check=False,
                )
                cleanup = {
                    "argv": command,
                    "return_code": stopped.returncode,
                    "stderr": stopped.stderr.decode(errors="replace"),
                }
                process.wait(timeout=20)
            except (OSError, subprocess.SubprocessError) as problem:
                cleanup = {
                    "argv": command,
                    "error": str(problem),
                    "container_cleanup_unconfirmed": True,
                }
        summary = {
            "schema_version": 1,
            "exit_code": process.returncode if process is not None else None,
            "elapsed_seconds": time.monotonic() - started,
            "sample_count": count,
            "cgroup_sample_count": sampled,
            "sampling_error_count": failures,
            "peak_memory_bytes": peak if sampled else None,
            "maximum_rolling_two_second_io_pressure_percent": maximum,
            "oom_events_seen": oom,
            "workload_io_pause_threshold_reached": maximum is not None
            and maximum >= 20,
            "additional_work_admitted_during_encoding": False,
            "diagnostics_only": True,
            "error": error,
        }
        execution = {
            **summary,
            "argv": plan["argv"],
            "cwd": plan["cwd"],
            "execution_plan_sha256": sha(plan_directory / "execution-plan.json"),
            "resource_limits": plan["resource_limits"],
            "cgroup_path": str(cgroup) if cgroup is not None else None,
            "sample_interval_seconds": 0.25,
            "resources_file": "resources.jsonl",
            "cleanup": cleanup,
            "files": {
                name: sha(output / name)
                for name in ("worker.stdout", "worker.stderr", "resources.jsonl")
                if (output / name).is_file()
            },
        }
        for name, value in (
            ("execution.json", execution),
            ("resource-summary.json", summary),
        ):
            with (output / name).open("xb") as destination:
                destination.write(_canonical(value))
    return execution


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    command = commands.add_parser("prepare")
    for name in ("prepared", "plan", "output"):
        command.add_argument(name, type=Path)
    command = commands.add_parser("run")
    command.add_argument("plan", type=Path)
    args = parser.parse_args()
    if args.command == "prepare":
        result = prepare(args.prepared, args.plan, args.output)
    else:
        result = run(args.plan)
    print(json.dumps(result, sort_keys=True))
    if args.command == "run" and result["exit_code"] != 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
