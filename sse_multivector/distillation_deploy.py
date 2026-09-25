"""Freeze experiment inputs and operate a distillation container over SSH.

Follows the existing GTE Vast deployment: immutable image, verified input
package, detached worker, reconnect, verified retrieval. The remote machine
runs the image directly; Docker is required only when preparing it locally.
Instance creation and budget admission precede this operator.
"""
import argparse
import contextlib
import fcntl
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tarfile
import time
import traceback

from gte.full_build_package import write_manifest, verify_manifest
from sse_multivector.distillation_run import load_data, read_json, sha256, write_json


CODE_ROOT = Path(__file__).resolve().parents[1]
CODE_FILES = (
    "sse_multivector/distillation_deploy.py", "sse_multivector/distillation_run.py",
    "sse_multivector/distillation_data.py", "sse_multivector/extraction_pipeline.py",
    "sse_multivector/mask_positions.py", "sse_multivector/distillation/requirements.lock",
    "sse_multivector/distillation/Dockerfile",
    "gte/full_build_package.py",
)
REMOTE_BASE = "/workspace/distillation"
REMOTE_PYTHON = "/opt/distillation-venv/bin/python"


def code_hashes():
    return {name: sha256(CODE_ROOT / name) for name in CODE_FILES}


def prepare(config_paths, output, timeout_seconds):
    """Copy only explicit inputs; no source code, credentials or host config."""
    if timeout_seconds <= 0 or not config_paths:
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
            data, prompt = Path(config["data"]), Path(config["mask_prompt"])
            load_data(data, prompt)
            data_relative = "data/" + sha256(data / "manifest.json")
            prompt_relative = "prompts/" + sha256(prompt) + ".txt"
            (staging / data_relative).mkdir(parents=True, exist_ok=True)
            for filename in ("manifest.json", "train.jsonl", "evaluation.jsonl", "references.jsonl"):
                shutil.copyfile(data / filename, staging / data_relative / filename)
            (staging / prompt_relative).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(prompt, staging / prompt_relative)
            config.update(data="package/" + data_relative, mask_prompt="package/" + prompt_relative)
            model = Path(config["model"])
            if model.is_dir():
                model_relative = "models/" + name
                shutil.copytree(model, staging / model_relative)
                config["model"] = "package/" + model_relative
            elif not re.fullmatch(r"[a-f0-9]{40}", config.get("revision") or ""):
                raise ValueError("remote models require an immutable revision")
            relative = "configs/" + name + ".json"
            write_json(staging / relative, config)
            runs.append(relative)
        write_json(staging / "job.json", {"runs": runs, "timeout_seconds": timeout_seconds,
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


@contextlib.contextmanager
def locked(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield lock


def worker_running(root):
    try:
        with locked(root / ".worker.lock"):
            return False
    except BlockingIOError:
        return True


def remote_status(root):
    if not (root / "package").exists():
        return {"state": "missing", "code": code_hashes()}
    if sha256(root / "package/manifest.json") != root.name:
        raise ValueError("remote package identity differs")
    if not (root / "state.json").exists():
        return {"state": "ready", "code": code_hashes()}
    state = read_json(root / "state.json")
    if worker_running(root):
        return {**state, "state": "running"}
    if state["state"] == "running":
        state = {**state, "state": "interrupted"}
    return state


def remote_receive(root):
    with locked(root / ".transfer.lock"):
        if (root / "package").exists():
            raise FileExistsError("remote package already exists")
        staging = root / "package.partial"
        if staging.exists():
            shutil.rmtree(staging)
        staging.mkdir()
        with tarfile.open(fileobj=sys.stdin.buffer, mode="r|") as archive:
            archive.extractall(staging, filter="data")
        verify_package(staging)
        if sha256(staging / "manifest.json") != root.name:
            raise ValueError("uploaded package identity differs")
        staging.rename(root / "package")
    return {"state": "ready"}


def remote_start(root):
    # The child inherits this flock, eliminating a gap between acknowledgement
    # and worker startup. Reconnecting never creates a concurrent worker.
    with locked(root / ".start.lock"):
        state = remote_status(root)
        if state["state"] in ("running", "complete", "failed"):
            return state
        if state["state"] not in ("ready", "interrupted"):
            raise ValueError("remote package has not been installed")
        with locked(root / ".worker.lock") as lock:
            job = verify_package(root / "package")
            state = {"state": "running", "starts": state.get("starts", 0) + 1,
                     "deadline": state.get("deadline", time.time() + job["timeout_seconds"]),
                     "package_sha256": root.name}
            write_json(root / "state.json", state)
            results = root / "results"
            results.mkdir(exist_ok=True)
            with (results / "worker.log").open("a") as log:
                child = subprocess.Popen(
                    [sys.executable, "-m", "sse_multivector.distillation_deploy", "_worker",
                     "--root", str(root), "--lock-fd", str(lock.fileno())],
                    cwd=CODE_ROOT, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                    start_new_session=True, pass_fds=(lock.fileno(),))
            state["pid"] = child.pid
            write_json(root / "state.json", state)
        return state


def remote_worker(root, lock_fd):
    # Parent may still be publishing the PID while this process starts.
    with locked_wait(root / ".start.lock"):
        state = read_json(root / "state.json")
    try:
        os.fstat(lock_fd)
        job = verify_package(root / "package")
        environment = {**os.environ, "PYTHONPATH": str(CODE_ROOT), "PYTHONUNBUFFERED": "1"}
        for config in job["runs"]:
            remaining = state["deadline"] - time.time()
            if remaining <= 0:
                raise TimeoutError("experiment exceeded its frozen runtime limit")
            name = Path(config).stem
            with (root / "results" / (name + ".log")).open("a") as log:
                result = subprocess.run(
                    [sys.executable, "-m", "sse_multivector.distillation_run",
                     "package/" + config, "--output", "results/" + name], cwd=root,
                    stdout=log, stderr=subprocess.STDOUT, env=environment, timeout=remaining)
            if result.returncode:
                raise RuntimeError(f"run {name} failed with exit code {result.returncode}; see {name}.log")
        state.update(state="complete")
    except BaseException as error:
        traceback.print_exc()
        state.update(state="failed", error=str(error))
    finally:
        state["finished"] = time.time()
        write_json(root / "state.json", state)
        os.close(lock_fd)


@contextlib.contextmanager
def locked_wait(path):
    with path.open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def remote_export(root):
    with locked(root / ".start.lock"):
        state = remote_status(root)
        if state["state"] not in ("complete", "failed", "interrupted"):
            raise ValueError("results are not ready for retrieval")
        with locked(root / ".worker.lock"):
            results = root / "results"
            write_json(results / "deployment.json", state)
            write_manifest(results, results / "manifest.json", "distillation-results")
            # No live writer remains while results are streamed.
            subprocess.run(["tar", "-C", str(results), "-cf", "-", "."], check=True)


def ssh_command(target, output, operation, root):
    host, port, identity = target["host"], target["port"], target["identity"]
    if not re.fullmatch(r"[a-zA-Z0-9_.@:-]+", host) or host.startswith("-") or not 0 < port < 65536:
        raise ValueError("invalid SSH endpoint")
    remote = "cd /work && " + shlex.join(
        [REMOTE_PYTHON, "-m", "sse_multivector.distillation_deploy", operation, "--root", root])
    return ["ssh", "-F", "/dev/null", "-i", identity, "-p", str(port),
            "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
            "-o", "ServerAliveInterval=5", "-o", "ServerAliveCountMax=3",
            "-o", "StrictHostKeyChecking=accept-new",
            "-o", "UserKnownHostsFile=" + str(output / "known_hosts"), host, remote]


def remote_json(target, output, operation, root):
    result = subprocess.run(ssh_command(target, output, operation, root),
                            capture_output=True, text=True, timeout=120)
    if result.returncode:
        raise RuntimeError(f"SSH {operation} failed: {result.stderr.strip()}")
    return json.loads(result.stdout)


def upload(package, target, output, root):
    with subprocess.Popen(["tar", "-C", str(package), "-cf", "-", "."], stdout=subprocess.PIPE) as source:
        try:
            result = subprocess.run(ssh_command(target, output, "_receive", root),
                                    stdin=source.stdout, capture_output=True, timeout=3600)
        finally:
            source.stdout.close()
            if source.poll() is None:
                source.terminate()
        status = source.wait()
    if result.returncode or status:
        raise RuntimeError("package upload failed: " + result.stderr.decode(errors="replace"))


def retrieve(target, output, root):
    staging = output / "result.partial"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir()
    # Save the stream first so both transfer failure and extraction are explicit.
    archive_path = output / "result.tar.partial"
    with archive_path.open("wb") as archive:
        result = subprocess.run(ssh_command(target, output, "_export", root),
                                stdout=archive, stderr=subprocess.PIPE, timeout=3600)
    if result.returncode:
        raise RuntimeError("result retrieval failed: " + result.stderr.decode(errors="replace"))
    with tarfile.open(archive_path) as archive:
        archive.extractall(staging, filter="data")
    verify_manifest(staging, staging / "manifest.json")
    state = read_json(staging / "deployment.json")
    if state["package_sha256"] != Path(root).name:
        raise ValueError("retrieved result belongs to another package")
    staging.rename(output / "result")
    archive_path.unlink()
    return state


def operate(package, output, target, start_only=False):
    package, output = Path(package).resolve(), Path(output).resolve()
    verify_package(package)
    digest = sha256(package / "manifest.json")
    root = REMOTE_BASE + "/" + digest
    output.mkdir(parents=True, exist_ok=True)
    with locked(output / ".lock"):
        contract = {"package_sha256": digest, "target": target, "remote_root": root}
        identity = output / "deployment.json"
        if identity.exists() and read_json(identity) != contract:
            raise ValueError("deployment settings differ; use a new output directory")
        write_json(identity, contract)
        if (output / "result").exists():
            verify_manifest(output / "result", output / "result/manifest.json")
            state = read_json(output / "result/deployment.json")
            if state["package_sha256"] != digest:
                raise ValueError("saved result belongs to another package")
            if state["state"] != "interrupted":
                return state
            # Keep retrieved evidence while an explicit repeat resumes the job.
            (output / "result").rename(output / f"interrupted-{state['starts']}")
        state = remote_json(target, output, "_status", root)
        if state["state"] == "missing":
            if state["code"] != code_hashes():
                raise ValueError("remote container differs from the prepared code")
            upload(package, target, output, root)
        state = remote_json(target, output, "_start", root)
        if start_only:
            return state
        while state["state"] == "running":
            time.sleep(2)
            state = remote_json(target, output, "_status", root)
        return retrieve(target, output, root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="operation", required=True)
    prepare_parser = commands.add_parser("prepare")
    prepare_parser.add_argument("--config", type=Path, action="append", required=True)
    prepare_parser.add_argument("--output", type=Path, required=True)
    prepare_parser.add_argument("--timeout-seconds", type=int, required=True)
    run_parser = commands.add_parser("run")
    run_parser.add_argument("--package", type=Path, required=True)
    run_parser.add_argument("--output", type=Path, required=True)
    run_parser.add_argument("--host", required=True)
    run_parser.add_argument("--port", type=int, default=22)
    run_parser.add_argument("--identity", type=Path, required=True)
    run_parser.add_argument("--start-only", action="store_true")
    for name in ("_receive", "_start", "_status", "_worker", "_export"):
        remote = commands.add_parser(name, help=argparse.SUPPRESS)
        remote.add_argument("--root", type=Path, required=True)
        if name == "_worker":
            remote.add_argument("--lock-fd", type=int, required=True)
    args = parser.parse_args()
    if args.operation == "prepare":
        result = {"package_sha256": prepare(args.config, args.output, args.timeout_seconds)}
    elif args.operation == "run":
        result = operate(args.package, args.output,
            {"host": args.host, "port": args.port, "identity": str(args.identity.resolve())}, args.start_only)
    else:
        if args.root.parent != Path(REMOTE_BASE) or not re.fullmatch(r"[a-f0-9]{64}", args.root.name):
            raise ValueError("invalid remote experiment directory")
        if args.operation == "_export":
            remote_export(args.root)
            return
        if args.operation == "_worker":
            remote_worker(args.root, args.lock_fd)
            return
        result = {"_receive": remote_receive, "_start": remote_start, "_status": remote_status}[args.operation](args.root)
    print(json.dumps(result))
    if args.operation == "run" and result.get("state") in ("failed", "interrupted"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
