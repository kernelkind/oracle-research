#!/usr/bin/env python3
"""Execute the frozen fine-segmentation SSE request in a hardened container."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Iterable

from sse_multivector.fine_segmentation_suite import (
    finalize_vector_artifact,
    verify_prepared_suite,
    verify_vector_artifact,
)
from sse_multivector.worker import canonical_tree_sha256


SCHEMA_VERSION = 1
SUITE_ID = "fine-segmentation-controlled-suite-v1"
EXPECTED_MODEL = {
    "base_model": "sentence-transformers/sentence-t5-base",
    "dimensions": 768,
    "maximum_tokens": 512,
    "pooling": "selected-contextual-token-mean-linear-relu-linear-v1",
}
HARDENED_PROFILE = "network-none-read-only-no-new-privileges-cap-drop-all-v1"


def _canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _file_record(path: Path) -> dict[str, int | str]:
    metadata = path.stat()
    return {
        "bytes": metadata.st_size,
        "sha256": _sha256_file(path),
    }


def _write_new(path: Path, value: bytes, *, mode: int = 0o644) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    try:
        with os.fdopen(descriptor, "wb") as destination:
            destination.write(value)
            destination.flush()
            os.fsync(destination.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def _write_json(path: Path, value: object, *, mode: int = 0o644) -> None:
    _write_new(path, _canonical_bytes(value), mode=mode)


def _metadata_tree_sha256(root: Path) -> str:
    """Hash mutation-relevant metadata while deliberately excluding access time."""

    digest = hashlib.sha256()
    entries = [
        root,
        *sorted(
            root.rglob("*"), key=lambda path: os.fsencode(str(path.relative_to(root)))
        ),
    ]
    for path in entries:
        metadata = path.lstat()
        relative = b"." if path == root else os.fsencode(path.relative_to(root))
        digest.update(relative + b"\0")
        digest.update(
            (
                f"{stat.S_IFMT(metadata.st_mode)}:{stat.S_IMODE(metadata.st_mode)}:"
                f"{metadata.st_dev}:{metadata.st_ino}:{metadata.st_size}:"
                f"{metadata.st_mtime_ns}:{metadata.st_ctime_ns}"
            ).encode("ascii")
        )
        digest.update(b"\0")
    return digest.hexdigest()


def _resolve_frozen_path(repo_root: Path, value: object, name: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError(f"technical freeze field {name} is missing")
    path = Path(value)
    return path.resolve() if path.is_absolute() else (repo_root / path).resolve()


def _resolve_executable(value: Path | str) -> Path:
    supplied = os.fspath(value)
    found = shutil.which(supplied)
    if found is None:
        raise ValueError(f"Docker executable is unavailable: {supplied}")
    executable = Path(found).resolve()
    if not executable.is_file() or not os.access(executable, os.X_OK):
        raise ValueError(f"Docker executable is not executable: {executable}")
    return executable


def _protected_snapshot(
    prepared: Path,
    freeze_path: Path,
    checkpoint: Path,
    worker: Path,
    model: Path,
) -> dict[str, object]:
    return {
        "prepared": {
            "tree_sha256": canonical_tree_sha256(prepared),
            "metadata_sha256": _metadata_tree_sha256(prepared),
        },
        "technical_freeze": _file_record(freeze_path),
        "checkpoint": _file_record(checkpoint),
        "worker": _file_record(worker),
        "base_model": {
            "tree_sha256": canonical_tree_sha256(model),
            "metadata_sha256": _metadata_tree_sha256(model),
        },
    }


def _load_frozen_context(
    repo_root: Path, prepared: Path, freeze_path: Path
) -> dict[str, object]:
    prepared_report = verify_prepared_suite(repo_root, prepared)
    prepared_tree_sha256 = canonical_tree_sha256(prepared)
    freeze = _read_json(freeze_path)
    if not isinstance(freeze, dict):
        raise ValueError("technical freeze must be a JSON object")
    if (
        freeze.get("schema_version") != SCHEMA_VERSION
        or freeze.get("suite_id") != SUITE_ID
    ):
        raise ValueError("technical freeze identifies a different suite")
    bindings = {
        "prepared_manifest_sha256": _sha256_file(prepared / "manifest.json"),
        "protocol_sha256": prepared_report["protocol_sha256"],
        "worker_request_sha256": prepared_report["worker_request_sha256"],
        "encoding_count": prepared_report["encoding_count"],
    }
    for field, expected in bindings.items():
        if freeze.get(field) != expected:
            raise ValueError(
                f"technical freeze field {field} differs from the prepared suite"
            )

    encoder = freeze.get("encoder")
    if not isinstance(encoder, dict):
        raise ValueError("technical freeze is missing its encoder identity")
    if encoder.get("request_sha256") != bindings["worker_request_sha256"]:
        raise ValueError("frozen encoder request differs from the prepared request")
    checkpoint = _resolve_frozen_path(
        repo_root, encoder.get("checkpoint_path"), "checkpoint_path"
    )
    worker = _resolve_frozen_path(repo_root, encoder.get("worker_path"), "worker_path")
    model = _resolve_frozen_path(
        repo_root, encoder.get("base_model_artifact_path"), "base_model_artifact_path"
    )
    checkpoint_record = _file_record(checkpoint) if checkpoint.is_file() else None
    worker_record = _file_record(worker) if worker.is_file() else None
    model_tree_sha256 = canonical_tree_sha256(model) if model.is_dir() else None
    if checkpoint_record is None or checkpoint_record["sha256"] != encoder.get(
        "checkpoint_sha256"
    ):
        raise ValueError("checkpoint differs from the frozen encoder identity")
    if worker_record is None or worker_record["sha256"] != encoder.get("worker_sha256"):
        raise ValueError("worker differs from the frozen encoder identity")
    if model_tree_sha256 is None or model_tree_sha256 != encoder.get(
        "base_model_artifact_tree_sha256"
    ):
        raise ValueError("base-model tree differs from the frozen encoder identity")
    if encoder.get("model") != EXPECTED_MODEL:
        raise ValueError(
            "frozen encoder model descriptor is not the approved SSE model"
        )
    if (
        encoder.get("dimensions") != 768
        or encoder.get("vector_format") != "row-major-f32le-v1"
    ):
        raise ValueError("frozen encoder vector contract is invalid")
    note_batch_size = encoder.get("note_batch_size")
    if (
        isinstance(note_batch_size, bool)
        or not isinstance(note_batch_size, int)
        or note_batch_size < 1
    ):
        raise ValueError("frozen encoder note batch size is invalid")
    image_reference = encoder.get("container_image")
    if not isinstance(image_reference, str):
        raise ValueError("frozen encoder container image is missing")
    match = re.fullmatch(r"(?:[^@]+@)?(sha256:[0-9a-f]{64})", image_reference)
    if match is None:
        raise ValueError(
            "frozen encoder container image must be an immutable SHA-256 identity"
        )
    validated_snapshot = {
        "prepared": {
            "tree_sha256": prepared_tree_sha256,
            "metadata_sha256": _metadata_tree_sha256(prepared),
        },
        "technical_freeze": _file_record(freeze_path),
        "checkpoint": checkpoint_record,
        "worker": worker_record,
        "base_model": {
            "tree_sha256": model_tree_sha256,
            "metadata_sha256": _metadata_tree_sha256(model),
        },
    }
    return {
        "freeze": freeze,
        "encoder": encoder,
        "checkpoint": checkpoint,
        "worker": worker,
        "model": model,
        "image_id": match.group(1),
        "image_reference": image_reference,
        "prepared_report": prepared_report,
        "validated_snapshot": validated_snapshot,
    }


def _worker_config(context: dict[str, object]) -> dict[str, object]:
    encoder = context["encoder"]
    assert isinstance(encoder, dict)
    return {
        "schema_version": SCHEMA_VERSION,
        "request_path": "/input/worker-request.json",
        "request_sha256": encoder["request_sha256"],
        "checkpoint_path": "/checkpoint/subencoder_st5_base.ckpt",
        "checkpoint_sha256": encoder["checkpoint_sha256"],
        "base_model_artifact_path": "/model",
        "base_model_artifact_tree_sha256": encoder["base_model_artifact_tree_sha256"],
        "model": encoder["model"],
        "device": "cpu",
        "container_image": encoder["container_image"],
        "note_batch_size": encoder["note_batch_size"],
        "output_path": "/output/worker-output",
    }


def _mount(source: Path, destination: str, *, readonly: bool) -> str:
    fields = ["type=bind", f"src={source}", f"dst={destination}"]
    if readonly:
        fields.append("readonly")
    return ",".join(fields)


def _inspect_command(executable: Path, image_id: str) -> list[str]:
    return [str(executable), "image", "inspect", image_id, "--format", "{{.Id}}"]


def _worker_command(
    executable: Path,
    image_id: str,
    request_path: Path,
    config_path: Path,
    checkpoint: Path,
    model: Path,
    worker: Path,
    runtime_output: Path,
) -> list[str]:
    return [
        str(executable),
        "run",
        "--rm",
        "--network",
        "none",
        "--read-only",
        "--security-opt",
        "no-new-privileges",
        "--cap-drop",
        "ALL",
        "--pids-limit",
        "256",
        "--shm-size",
        "1g",
        "--tmpfs",
        "/tmp:rw,noexec,nosuid,nodev,size=4g,mode=1777",
        "--user",
        f"{os.getuid()}:{os.getgid()}",
        "--env",
        "HOME=/tmp",
        "--env",
        "XDG_CACHE_HOME=/tmp/cache",
        "--env",
        "HF_HOME=/tmp/huggingface",
        "--mount",
        _mount(request_path, "/input/worker-request.json", readonly=True),
        "--mount",
        _mount(config_path, "/input/worker-config.json", readonly=True),
        "--mount",
        _mount(checkpoint, "/checkpoint/subencoder_st5_base.ckpt", readonly=True),
        "--mount",
        _mount(model, "/model", readonly=True),
        "--mount",
        _mount(worker, "/workspace/worker.py", readonly=True),
        "--mount",
        _mount(runtime_output, "/output", readonly=False),
        image_id,
        "python",
        "/workspace/worker.py",
        "/input/worker-config.json",
    ]


def _run(
    command: list[str], repo_root: Path
) -> tuple[subprocess.CompletedProcess[bytes], int]:
    started = time.monotonic_ns()
    result = subprocess.run(command, cwd=repo_root, capture_output=True, check=False)
    return result, time.monotonic_ns() - started


def _stream_record(path: Path) -> dict[str, int | str]:
    return _file_record(path)


def _build_manifest(output: Path) -> dict[str, object]:
    file_names = (
        "execution.json",
        "image-inspect.stderr",
        "image-inspect.stdout",
        "worker-config.json",
        "worker.stderr",
        "worker.stdout",
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "suite_id": SUITE_ID,
        "hardened_profile": HARDENED_PROFILE,
        "files": {name: _file_record(output / name) for name in file_names},
        "directories": {
            "worker-output": canonical_tree_sha256(output / "worker-output"),
            "vector-artifact": canonical_tree_sha256(output / "vector-artifact"),
        },
    }


def _verify_manifest(output: Path) -> dict[str, object]:
    manifest = _read_json(output / "manifest.json")
    if manifest != _build_manifest(output):
        raise ValueError("encoder-run manifest differs from replay")
    return manifest


def run_frozen_encoder(
    repo_root: Path | str,
    prepared_path: Path | str,
    technical_freeze_path: Path | str,
    output_path: Path | str,
    *,
    docker_executable: Path | str = "docker",
) -> dict[str, object]:
    """Run the single frozen SSE request and atomically publish all evidence."""

    repo_root = Path(repo_root).resolve()
    prepared = Path(prepared_path).resolve()
    freeze_path = Path(technical_freeze_path).resolve()
    output = Path(output_path).resolve()
    if output.exists():
        raise ValueError(f"encoder run already exists: {output}")
    context = _load_frozen_context(repo_root, prepared, freeze_path)
    executable = _resolve_executable(docker_executable)
    encoder_runner = Path(__file__).resolve()
    encoder_runner_before = _file_record(encoder_runner)
    checkpoint = context["checkpoint"]
    worker = context["worker"]
    model = context["model"]
    image_id = context["image_id"]
    assert isinstance(checkpoint, Path)
    assert isinstance(worker, Path)
    assert isinstance(model, Path)
    assert isinstance(image_id, str)
    protected_before = context["validated_snapshot"]

    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}.", dir=output.parent))
    try:
        config_directory = stage / "config"
        runtime_output = stage / "runtime-output"
        config_directory.mkdir()
        runtime_output.mkdir()
        config_path = config_directory / "worker-config.json"
        config_bytes = _canonical_bytes(_worker_config(context))
        _write_new(config_path, config_bytes, mode=0o444)

        inspect_command = _inspect_command(executable, image_id)
        inspect_result, inspect_duration = _run(inspect_command, repo_root)
        _write_new(stage / "image-inspect.stdout", inspect_result.stdout)
        _write_new(stage / "image-inspect.stderr", inspect_result.stderr)
        if inspect_result.returncode != 0:
            raise RuntimeError(
                "Docker could not inspect the frozen SSE image: "
                + inspect_result.stderr.decode("utf-8", errors="replace").strip()
            )
        inspected_id = inspect_result.stdout.decode("utf-8", errors="strict").strip()
        if inspected_id != image_id:
            raise ValueError(
                f"local SSE image identity differs: expected {image_id}, got {inspected_id}"
            )

        worker_command = _worker_command(
            executable,
            image_id,
            prepared / "worker-request.json",
            config_path,
            checkpoint,
            model,
            worker,
            runtime_output,
        )
        worker_result, worker_duration = _run(worker_command, repo_root)
        _write_new(stage / "worker.stdout", worker_result.stdout)
        _write_new(stage / "worker.stderr", worker_result.stderr)
        if worker_result.returncode != 0:
            raise RuntimeError(
                "frozen SSE worker failed: "
                + worker_result.stderr.decode("utf-8", errors="replace").strip()
            )
        if config_path.read_bytes() != config_bytes:
            raise ValueError("immutable worker config changed during execution")
        protected_after = _protected_snapshot(
            prepared, freeze_path, checkpoint, worker, model
        )
        if protected_after != protected_before:
            raise ValueError("a frozen encoder input changed during execution")
        if _file_record(encoder_runner) != encoder_runner_before:
            raise ValueError("encoder runner changed during execution")

        worker_output = runtime_output / "worker-output"
        if not worker_output.is_dir():
            raise ValueError("SSE worker did not produce its expected output directory")
        os.rename(worker_output, stage / "worker-output")
        runtime_output.rmdir()
        os.rename(config_path, stage / "worker-config.json")
        config_directory.rmdir()

        vector_report = finalize_vector_artifact(
            prepared,
            freeze_path,
            stage / "worker-output",
            stage / "vector-artifact",
        )
        execution = {
            "schema_version": SCHEMA_VERSION,
            "suite_id": SUITE_ID,
            "hardened_profile": HARDENED_PROFILE,
            "repo_root": str(repo_root),
            "prepared_path": str(prepared),
            "prepared_manifest_sha256": _sha256_file(prepared / "manifest.json"),
            "technical_freeze_path": str(freeze_path),
            "technical_freeze_sha256": _sha256_file(freeze_path),
            "worker_config_sha256": _sha256_bytes(config_bytes),
            "docker_executable": {
                "path": str(executable),
                **_file_record(executable),
            },
            "encoder_runner": {
                "path": str(encoder_runner),
                **encoder_runner_before,
            },
            "image": {
                "frozen_reference": context["image_reference"],
                "expected_id": image_id,
                "inspected_id": inspected_id,
            },
            "inspect": {
                "argv": inspect_command,
                "return_code": inspect_result.returncode,
                "duration_nanoseconds": inspect_duration,
                "stdout": _stream_record(stage / "image-inspect.stdout"),
                "stderr": _stream_record(stage / "image-inspect.stderr"),
            },
            "worker": {
                "argv": worker_command,
                "return_code": worker_result.returncode,
                "duration_nanoseconds": worker_duration,
                "stdout": _stream_record(stage / "worker.stdout"),
                "stderr": _stream_record(stage / "worker.stderr"),
            },
            "protected_inputs_before": protected_before,
            "protected_inputs_after": protected_after,
            "vector_artifact_manifest_sha256": vector_report["manifest_sha256"],
        }
        _write_json(stage / "execution.json", execution)
        _write_json(stage / "manifest.json", _build_manifest(stage))
        os.rename(stage, output)
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return verify_frozen_encoder_run(repo_root, prepared, freeze_path, output)


def verify_frozen_encoder_run(
    repo_root: Path | str,
    prepared_path: Path | str,
    technical_freeze_path: Path | str,
    output_path: Path | str,
) -> dict[str, object]:
    """Replay all deterministic checks without rerunning the neural encoder."""

    repo_root = Path(repo_root).resolve()
    prepared = Path(prepared_path).resolve()
    freeze_path = Path(technical_freeze_path).resolve()
    output = Path(output_path).resolve()
    context = _load_frozen_context(repo_root, prepared, freeze_path)
    expected_entries = {
        "execution.json",
        "image-inspect.stderr",
        "image-inspect.stdout",
        "manifest.json",
        "vector-artifact",
        "worker-config.json",
        "worker-output",
        "worker.stderr",
        "worker.stdout",
    }
    if (
        not output.is_dir()
        or {entry.name for entry in output.iterdir()} != expected_entries
    ):
        raise ValueError("encoder run contains unexpected entries")
    _verify_manifest(output)
    expected_config = _canonical_bytes(_worker_config(context))
    config_path = output / "worker-config.json"
    if config_path.read_bytes() != expected_config:
        raise ValueError("retained worker config differs from the frozen inputs")
    if stat.S_IMODE(config_path.stat().st_mode) & 0o222:
        raise ValueError("retained worker config is writable")

    execution = _read_json(output / "execution.json")
    if not isinstance(execution, dict):
        raise ValueError("encoder execution evidence is invalid")
    if execution.get("hardened_profile") != HARDENED_PROFILE:
        raise ValueError("encoder execution used a different hardening profile")
    encoder_runner = Path(__file__).resolve()
    if execution.get("encoder_runner") != {
        "path": str(encoder_runner),
        **_file_record(encoder_runner),
    }:
        raise ValueError("encoder runner differs from execution time")
    if execution.get("prepared_manifest_sha256") != _sha256_file(
        prepared / "manifest.json"
    ):
        raise ValueError("encoder execution is not bound to the prepared suite")
    if execution.get("technical_freeze_sha256") != _sha256_file(freeze_path):
        raise ValueError("encoder execution is not bound to the technical freeze")
    if execution.get("worker_config_sha256") != _sha256_bytes(expected_config):
        raise ValueError("encoder execution is not bound to the worker config")
    image = execution.get("image", {})
    if image != {
        "frozen_reference": context["image_reference"],
        "expected_id": context["image_id"],
        "inspected_id": context["image_id"],
    }:
        raise ValueError("encoder execution image evidence is invalid")
    for operation in ("inspect", "worker"):
        record = execution.get(operation, {})
        if record.get("return_code") != 0:
            raise ValueError(f"encoder {operation} evidence reports failure")
        for stream in ("stdout", "stderr"):
            path = (
                output
                / f"{'image-inspect' if operation == 'inspect' else 'worker'}.{stream}"
            )
            if record.get(stream) != _file_record(path):
                raise ValueError(f"encoder {operation} {stream} evidence differs")
    if (output / "image-inspect.stdout").read_text(encoding="utf-8").strip() != context[
        "image_id"
    ]:
        raise ValueError(
            "retained Docker inspection output differs from the frozen image"
        )
    if execution.get("protected_inputs_before") != execution.get(
        "protected_inputs_after"
    ):
        raise ValueError("execution evidence reports a frozen-input mutation")
    current_snapshot = context["validated_snapshot"]
    if execution.get("protected_inputs_after") != current_snapshot:
        raise ValueError("a frozen encoder input differs from execution time")

    vector_report = verify_vector_artifact(
        prepared,
        freeze_path,
        output / "worker-output",
        output / "vector-artifact",
    )
    if (
        execution.get("vector_artifact_manifest_sha256")
        != vector_report["manifest_sha256"]
    ):
        raise ValueError("execution evidence differs from the vector artifact")
    return {
        **vector_report,
        "encoder_run_manifest_sha256": _sha256_file(output / "manifest.json"),
        "output_path": str(output),
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("run", "verify"):
        command = subparsers.add_parser(name)
        command.add_argument("repo_root", type=Path)
        command.add_argument("prepared", type=Path)
        command.add_argument("technical_freeze", type=Path)
        command.add_argument("output", type=Path)
        if name == "run":
            command.add_argument("--docker-executable", default="docker")
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.command == "run":
        report = run_frozen_encoder(
            args.repo_root,
            args.prepared,
            args.technical_freeze,
            args.output,
            docker_executable=args.docker_executable,
        )
    else:
        report = verify_frozen_encoder_run(
            args.repo_root, args.prepared, args.technical_freeze, args.output
        )
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
