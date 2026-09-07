#!/usr/bin/env python3
"""Run at most 12 commands once, in owned systemd units, with host guards.

Usage: python run_comparison.py jobs.json --output NEW_DIRECTORY
Each job supplies id, unit (prefix), absolute cwd, and command (argv with an
absolute executable). Limits apply to the owned units: commands that explicitly
launch work into other systemd units are not bounded by this driver's cgroups.
"""

import argparse
import json
import math
import os
import re
import signal
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path


GIB = 1024 ** 3
SAMPLE_SECONDS = 5
TIMEOUT_SECONDS = 900


def read_resources():
    meminfo = Path("/proc/meminfo").read_text()
    available = re.search(r"^MemAvailable:\s+(\d+) kB$", meminfo, re.MULTILINE)
    if available is None:
        raise ValueError("missing MemAvailable reading")
    result = {"mem_available_bytes": int(available.group(1)) * 1024}
    for name in ("memory", "io"):
        pressure = Path(f"/proc/pressure/{name}").read_text()
        some = next((line for line in pressure.splitlines() if line.startswith("some ")), None)
        if some is None:
            raise ValueError(f"missing {name} some pressure reading")
        fields = dict(field.split("=", 1) for field in some.split()[1:])
        value = float(fields["avg10"])
        if not math.isfinite(value) or not 0 <= value <= 100:
            raise ValueError(f"invalid {name} some avg10")
        result[f"{name}_some_avg10"] = value
    return result


class Monitor:
    def __init__(self, stream):
        self.stream = stream
        self.lock = threading.RLock()
        self.done = threading.Event()
        self.stop_reason = None
        self.started = time.monotonic()
        self.last_sample = None
        self.max_interval = 0.0
        self.sample_count = 0
        self.thread = threading.Thread(target=self.run, name="resource-monitor")

    def abort(self, reason):
        with self.lock:
            if self.stop_reason is None:
                self.stop_reason = reason

    def sample(self, reason):
        with self.lock:
            now = time.monotonic()
            sample = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "monotonic": now,
                "reason": reason,
            }
            try:
                sample.update(read_resources())
                if sample["mem_available_bytes"] < 8 * GIB:
                    self.abort("emergency: MemAvailable below 8 GiB")
                if sample["memory_some_avg10"] > 10:
                    self.abort("emergency: memory some avg10 above 10")
            except Exception as error:
                sample["error"] = f"{type(error).__name__}: {error}"
                self.abort(f"resource readings unavailable: {error}")
            if now - self.started >= TIMEOUT_SECONDS:
                self.abort("batch timeout after 900 seconds")
            if self.last_sample is not None:
                self.max_interval = max(self.max_interval, now - self.last_sample)
            self.last_sample = now
            self.sample_count += 1
            try:
                self.stream.write(json.dumps(sample) + "\n")
                self.stream.flush()
            except Exception as error:
                self.abort(f"resource log unavailable: {error}")
            return sample

    def run(self):
        next_sample = self.started
        while not self.done.is_set():
            self.sample("periodic")
            next_sample += SAMPLE_SECONDS
            self.done.wait(max(0, next_sample - time.monotonic()))


def load_jobs(path):
    value = json.loads(path.read_text())
    jobs = value.get("jobs") if isinstance(value, dict) else None
    if not isinstance(jobs, list) or not 1 <= len(jobs) <= 12:
        raise ValueError("jobs must contain between 1 and 12 jobs")
    identifiers = set()
    units = set()
    for job in jobs:
        if not isinstance(job, dict):
            raise ValueError("each job must be an object")
        for field in ("id", "unit"):
            if not isinstance(job.get(field), str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}", job[field]):
                raise ValueError(f"job {field} must be a safe, nonempty identifier")
        unit_prefix = job["unit"].removesuffix(".service")
        if job["id"] in identifiers or unit_prefix in units:
            raise ValueError("job ids and unit prefixes must be unique")
        identifiers.add(job["id"])
        units.add(unit_prefix)
        command = job.get("command")
        if not isinstance(command, list) or not command or not all(isinstance(arg, str) and "\0" not in arg for arg in command):
            raise ValueError("job command must be a nonempty argv list")
        if not os.path.isabs(command[0]):
            raise ValueError("job command executable must be absolute")
        cwd = job.get("cwd")
        if not isinstance(cwd, str) or not os.path.isabs(cwd) or not Path(cwd).is_dir():
            raise ValueError("job cwd must be an existing absolute directory")
    return jobs


def admitted(sample):
    return (
        "error" not in sample
        and sample["mem_available_bytes"] >= 16 * GIB
        and sample["memory_some_avg10"] <= 1
        and sample["io_some_avg10"] <= 10
    )


def run_batch(jobs, output):
    output.mkdir(parents=True, exist_ok=False)
    run_id = uuid.uuid4().hex[:16]
    results = [
        {
            **job,
            "unit": f"{job['unit'].removesuffix('.service')}-{run_id}.service",
            "status": "not_launched",
            "exit_code": None,
        }
        for job in jobs
    ]
    active = {}
    owned_units = []
    interrupted = [None]
    old_handlers = {}
    stop_errors = []

    def handle_signal(signum, _frame):
        interrupted[0] = signum

    for signum in (signal.SIGINT, signal.SIGTERM):
        old_handlers[signum] = signal.signal(signum, handle_signal)

    with (output / "resources.jsonl").open("x", buffering=1) as resources:
        monitor = Monitor(resources)
        monitor.thread.start()
        try:
            pending = list(results)
            while pending or active:
                if interrupted[0] is not None:
                    monitor.abort(f"received {signal.Signals(interrupted[0]).name}")
                if time.monotonic() - monitor.started >= TIMEOUT_SECONDS:
                    monitor.abort("batch timeout after 900 seconds")
                if monitor.stop_reason is not None:
                    break
                if not monitor.thread.is_alive():
                    monitor.abort("resource monitor exited unexpectedly")
                    break
                for unit, (process, result) in list(active.items()):
                    code = process.poll()
                    if code is not None:
                        result.update(
                            status="succeeded" if code == 0 else "failed",
                            exit_code=code,
                            finished_monotonic=time.monotonic(),
                        )
                        del active[unit]
                if pending:
                    sample = monitor.sample("before_launch")
                    if monitor.stop_reason is not None or interrupted[0] is not None:
                        continue
                    if admitted(sample):
                        result = pending.pop(0)
                        unit = result["unit"]
                        command = [
                            "systemd-run", "--user", "--wait", "--pipe", "--quiet", "--collect",
                            "--unit", unit,
                            "--property", "MemoryMax=2G",
                            "--property", "MemorySwapMax=0",
                            "--property", "RuntimeMaxSec=900",
                            "--working-directory", result["cwd"],
                            "--", *result["command"],
                        ]
                        with (output / f"{result['id']}.stdout").open("xb") as stdout, (output / f"{result['id']}.stderr").open("xb") as stderr:
                            process = subprocess.Popen(
                                command, cwd=result["cwd"], stdin=subprocess.DEVNULL,
                                stdout=stdout, stderr=stderr,
                            )
                        result.update(status="running", started_monotonic=time.monotonic())
                        owned_units.append(unit)
                        active[unit] = (process, result)
                        continue
                if pending or active:
                    time.sleep(0.1)
        except Exception as error:
            monitor.abort(f"driver error: {type(error).__name__}: {error}")
        finally:
            if active:
                with (output / "systemctl.stdout").open("xb") as stdout, (output / "systemctl.stderr").open("xb") as stderr:
                    try:
                        stopped = subprocess.run(
                            ["systemctl", "--user", "stop", *active],
                            stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, timeout=15,
                        )
                        if stopped.returncode:
                            stop_errors.append(f"systemctl stop exited {stopped.returncode}")
                    except Exception as error:
                        stop_errors.append(f"systemctl stop failed: {error}")
                for process, result in active.values():
                    try:
                        code = process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        process.terminate()
                        try:
                            code = process.wait(timeout=2)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            code = process.wait(timeout=2)
                    result.update(
                        status="timed_out" if monitor.stop_reason == "batch timeout after 900 seconds" else "cancelled",
                        exit_code=code,
                        finished_monotonic=time.monotonic(),
                    )
            monitor.done.set()
            monitor.thread.join(timeout=6)
            if monitor.thread.is_alive():
                monitor.abort("resource monitor did not terminate")
            monitor.sample("after_last_completion")
            for result in results:
                if result["status"] == "not_launched":
                    result["reason"] = monitor.stop_reason
            report = {
                "run_id": run_id,
                "jobs": results,
                "owned_units": owned_units,
                "stop_reason": monitor.stop_reason,
                "stop_errors": stop_errors,
                "resource_sample_count": monitor.sample_count,
                "max_sample_interval_seconds": monitor.max_interval,
                "limits_scope": "Owned systemd units only; work launched into other units is outside these cgroups.",
            }
            (output / "results.json").write_text(json.dumps(report, indent=2) + "\n")
            for signum, handler in old_handlers.items():
                signal.signal(signum, handler)
    return 0 if monitor.stop_reason is None and not stop_errors and all(result["status"] == "succeeded" for result in results) else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jobs", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args(argv)
    try:
        jobs = load_jobs(arguments.jobs)
        return run_batch(jobs, arguments.output)
    except (OSError, ValueError) as error:
        print(f"comparison driver: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
