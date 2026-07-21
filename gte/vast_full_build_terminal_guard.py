#!/usr/bin/env python3
"""Fail-closed manual review gate for a frozen Vast full-build result."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import json
import math
import os
import select
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Iterator, NoReturn


REMOTE_ROOT = "/workspace/oracle-full-build"
REMOTE_CONTROLLER = f"{REMOTE_ROOT}/transport/control/gte-oracle"
CONFIG_RELATIVE = "package/run/full-build-config.json"
LOCAL_VERIFICATION_REPLACEMENT = "representation/verification.json"
TTY_CONFIRMATION_TIMEOUT_SECONDS = 300
PAYLOAD_EXCLUDED_TOP_LEVEL_PATHS = ("settlement", "settlement-attempts")


class GuardError(RuntimeError):
    """The terminal gate is not safe to advance."""


@dataclass(frozen=True)
class Runtime:
    operator: ModuleType
    context: object
    instance_id: str
    attempt_id: str
    private_key: Path
    target: list[str]
    remote: dict[str, object]


def utc_text() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_json(document: object) -> bytes:
    try:
        return (
            json.dumps(
                document,
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                indent=2,
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise GuardError(f"terminal evidence is not canonical JSON: {error}") from error


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as source:
            while chunk := source.read(8 * 1024 * 1024):
                digest.update(chunk)
    except OSError as error:
        raise GuardError(f"could not hash {path}: {error}") from error
    return digest.hexdigest()


def require_sha256(value: object, field: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise GuardError(f"{field} is not a SHA-256")
    return value


def read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise GuardError(f"could not read JSON from {path}: {error}") from error


def sync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.exists():
        if path.read_bytes() == content:
            return
        raise GuardError(f"immutable terminal evidence differs: {path}")
    temporary = path.with_name(f".{path.name}.next-{os.getpid()}")
    try:
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            written = 0
            while written < len(content):
                count = os.write(descriptor, content[written:])
                if count <= 0:
                    raise GuardError(f"could not finish writing {path}")
                written += count
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.replace(temporary, path)
        sync_directory(path.parent)
    finally:
        with contextlib.suppress(FileNotFoundError):
            temporary.unlink()


def atomic_json(path: Path, document: object) -> None:
    atomic_bytes(path, canonical_json(document))


def load_frozen_operator(root: Path) -> ModuleType:
    source = root / "transport/control/vast_full_build.py"
    if not source.is_file():
        raise GuardError(f"frozen operator is missing: {source}")
    control = str(source.parent)
    if control not in sys.path:
        sys.path.insert(0, control)
    module_name = f"frozen_vast_full_build_{sha256_file(source)[:16]}"
    if module_name in sys.modules:
        module = sys.modules[module_name]
        if not isinstance(module, ModuleType):
            raise GuardError("frozen operator module cache is invalid")
        return module
    spec = importlib.util.spec_from_file_location(module_name, source)
    if spec is None or spec.loader is None:
        raise GuardError(f"could not load frozen operator: {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    previous_dont_write_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous_dont_write_bytecode
    return module


def load_runtime(root: Path, config: Path) -> Runtime:
    root = root.resolve()
    operator = load_frozen_operator(root)
    arguments = argparse.Namespace(root=root, config=config.resolve(), operation="run")
    context = operator.Context.load(arguments)
    operator.verify_reviewed_artifacts(context)
    instance_id = operator.recorded_instance_id(context)
    attempt_id = operator.last_attempt_id(context)
    if instance_id is None or attempt_id is None:
        raise GuardError("the paid run has no bound instance or worker attempt")
    private_key, target = operator.ensure_ssh(context, instance_id)
    remote = operator.worker_status(context, private_key, target, attempt_id)
    if (
        remote.get("state") != "terminal"
        or remote.get("kind") != "full-build.exit"
        or remote.get("exit_status") != 0
    ):
        raise GuardError("the remote full build has not completed successfully")
    return Runtime(
        operator=operator,
        context=context,
        instance_id=instance_id,
        attempt_id=attempt_id,
        private_key=private_key,
        target=target,
        remote=remote,
    )


def load_recovery_runtime(root: Path, config: Path) -> Runtime:
    root = root.resolve()
    operator = load_frozen_operator(root)
    arguments = argparse.Namespace(root=root, config=config.resolve(), operation="run")
    context = operator.Context.load(arguments)
    operator.verify_reviewed_artifacts(context)
    instance_id = operator.recorded_instance_id(context)
    attempt_id = operator.last_attempt_id(context)
    if instance_id is None or attempt_id is None:
        raise GuardError("authorized destruction has no bound instance or attempt")
    return Runtime(
        operator=operator,
        context=context,
        instance_id=instance_id,
        attempt_id=attempt_id,
        private_key=Path(),
        target=[],
        remote={},
    )


@contextlib.contextmanager
def destruction_disabled(runtime: Runtime) -> Iterator[object]:
    original = runtime.operator.destroy_instance

    def forbidden(*_args: object, **_kwargs: object) -> NoReturn:
        raise GuardError("destruction is disabled before manual approval")

    runtime.operator.destroy_instance = forbidden
    try:
        yield original
    finally:
        runtime.operator.destroy_instance = original


@contextlib.contextmanager
def operation_lock(runtime: Runtime) -> Iterator[None]:
    lock = getattr(runtime.operator, "operation_lock", None)
    if lock is None:
        yield
        return
    with lock(runtime.context.root):
        yield


def sample_event_ids(runtime: Runtime) -> list[str]:
    result = runtime.context.path("result")
    layout = "result" if result.is_dir() else "result.next"
    path = runtime.context.path(
        f"{layout}/package/run/semantic-corpus/ordered-event-ids.bin"
    )
    total_rows = runtime.context.expected["total_rows"]
    if isinstance(total_rows, bool) or not isinstance(total_rows, int) or total_rows <= 0:
        raise GuardError("expected total row count is invalid")
    expected_bytes = total_rows * 32
    if not path.is_file() or path.stat().st_size != expected_bytes:
        raise GuardError("ordered event IDs do not match the expected row count")
    rows = (0, total_rows // 2, total_rows - 1)
    identifiers: list[str] = []
    with path.open("rb") as source:
        for row in rows:
            source.seek(row * 32)
            value = source.read(32)
            if len(value) != 32:
                raise GuardError("could not read a terminal smoke-test event ID")
            identifiers.append(value.hex())
    return identifiers


def cpu_query_config(runtime: Runtime) -> tuple[bytes, str, str]:
    result = runtime.context.path("result")
    layout = "result" if result.is_dir() else "result.next"
    source = runtime.context.path(f"{layout}/{CONFIG_RELATIVE}")
    document = read_json(source)
    if not isinstance(document, dict) or not isinstance(document.get("worker"), dict):
        raise GuardError("full-build query config is invalid")
    worker = document["worker"]
    if worker.get("device") != "cuda":
        raise GuardError("frozen full-build query config is not the expected CUDA config")
    worker["device"] = "cpu"
    content = canonical_json(document)
    digest = sha256_bytes(content)
    return content, digest, f"/tmp/gte-terminal-query-{digest}.json"


def upload_cpu_query_config(runtime: Runtime) -> tuple[str, str]:
    content, digest, remote_path = cpu_query_config(runtime)
    base = runtime.operator.ssh_arguments(
        runtime.context, runtime.private_key, runtime.target
    )
    written = runtime.operator.completed_process(
        [*base, "/usr/bin/tee", remote_path], input_bytes=content
    )
    if written.stdout != content:
        raise GuardError("remote CPU query config transfer was not exact")
    runtime.operator.completed_process([*base, "/usr/bin/chmod", "0600", remote_path])
    verified = runtime.operator.completed_process(
        [*base, "/usr/bin/sha256sum", remote_path]
    ).stdout.decode("utf-8", errors="strict").strip()
    if verified != f"{digest}  {remote_path}":
        raise GuardError("remote CPU query config hash differs")
    return remote_path, digest


def remote_controller(runtime: Runtime, arguments: list[str]) -> object:
    command = [
        *runtime.operator.ssh_arguments(
            runtime.context, runtime.private_key, runtime.target
        ),
        "/usr/bin/env",
        "-C",
        REMOTE_ROOT,
        REMOTE_CONTROLLER,
        *arguments,
    ]
    result = runtime.operator.completed_process(command)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise GuardError("remote controller did not return JSON") from error


def validate_similar_notes(
    runtime: Runtime,
    response: object,
    representation_version: str,
    source_event_id: str,
) -> dict[str, object]:
    if not isinstance(response, dict):
        raise GuardError("remote similar-notes response is invalid")
    responses = response.get("responses")
    metrics = response.get("metrics")
    total_rows = runtime.context.expected["total_rows"]
    if (
        not isinstance(responses, list)
        or len(responses) != 1
        or not isinstance(responses[0], dict)
        or not isinstance(metrics, dict)
    ):
        raise GuardError("remote similar-notes response is incomplete")
    result = responses[0]
    candidates = result.get("candidates")
    if (
        result.get("source_event_id") != source_event_id
        or result.get("representation_version") != representation_version
        or result.get("represented_rows") != total_rows
        or result.get("total_rows") != total_rows
        or result.get("complete") is not True
        or not isinstance(candidates, list)
        or len(candidates) != 10
        or metrics.get("encoded_queries") != 1
        or metrics.get("matrix_passes") != 1
        or metrics.get("scanned_rows") != total_rows
    ):
        raise GuardError("remote similar-notes did not scan the complete representation")
    summarized = []
    for index, candidate in enumerate(candidates, start=1):
        if not isinstance(candidate, dict):
            raise GuardError("remote similar-notes candidate is invalid")
        score = candidate.get("cosine_score")
        if (
            candidate.get("rank") != index
            or not isinstance(candidate.get("event_id"), str)
            or isinstance(score, bool)
            or not isinstance(score, (int, float))
            or not math.isfinite(float(score))
        ):
            raise GuardError("remote similar-notes candidate is invalid")
        summarized.append(candidate)
    stable_metrics = {
        field: metrics.get(field)
        for field in (
            "encoded_queries",
            "cache_hits",
            "matrix_passes",
            "scanned_rows",
            "scan_block_rows",
        )
    }
    return {
        "metrics": stable_metrics,
        "responses": [{**result, "candidates": summarized}],
    }


def validate_vectors(
    runtime: Runtime,
    response: object,
    representation_version: str,
    expected_ids: list[str],
) -> dict[str, object]:
    if not isinstance(response, dict):
        raise GuardError("vector response is invalid")
    total_rows = runtime.context.expected["total_rows"]
    vector_bytes = runtime.context.expected["final_vector_bytes"]
    if (
        isinstance(vector_bytes, bool)
        or not isinstance(vector_bytes, int)
        or vector_bytes % (total_rows * 4) != 0
    ):
        raise GuardError("expected vector dimensions are invalid")
    dimensions = vector_bytes // (total_rows * 4)
    vectors = response.get("vectors")
    if (
        response.get("representation_version") != representation_version
        or response.get("represented_rows") != total_rows
        or response.get("total_rows") != total_rows
        or response.get("complete") is not True
        or not isinstance(vectors, list)
        or len(vectors) != len(expected_ids)
    ):
        raise GuardError("vector response does not cover the requested complete representation")
    summarized = []
    for expected_id, vector in zip(expected_ids, vectors, strict=True):
        if not isinstance(vector, dict):
            raise GuardError("stored vector is invalid")
        values = vector.get("vector")
        if (
            vector.get("event_id") != expected_id
            or vector.get("dimensions") != dimensions
            or not isinstance(values, list)
            or len(values) != dimensions
            or any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(float(value))
                for value in values
            )
        ):
            raise GuardError("stored vector is invalid")
        digest = require_sha256(vector.get("vector_sha256"), "stored vector hash")
        summarized.append(
            {
                "event_id": expected_id,
                "dimensions": dimensions,
                "vector_sha256": digest,
            }
        )
    return {
        "representation_version": representation_version,
        "represented_rows": total_rows,
        "total_rows": total_rows,
        "complete": True,
        "vectors": summarized,
    }


def run_remote_read_only_checks(runtime: Runtime) -> dict[str, object]:
    verification = remote_controller(
        runtime, ["verify-representation", CONFIG_RELATIVE]
    )
    runtime.operator.validate_representation(
        runtime.context, verification, complete=True
    )
    if not isinstance(verification, dict):
        raise GuardError("remote representation verification is invalid")
    version = require_sha256(
        verification.get("representation_version"), "remote representation version"
    )
    identifiers = sample_event_ids(runtime)
    query_config, query_config_sha256 = upload_cpu_query_config(runtime)
    similar = remote_controller(
        runtime,
        ["similar-notes", query_config, identifiers[0], "10", version],
    )
    remote_vectors = remote_controller(
        runtime,
        ["vectors-for-notes", CONFIG_RELATIVE, ",".join(identifiers), version],
    )
    return {
        "representation_version": version,
        "query_config_sha256": query_config_sha256,
        "verification": verification,
        "similar_notes": validate_similar_notes(
            runtime, similar, version, identifiers[0]
        ),
        "vectors": validate_vectors(runtime, remote_vectors, version, identifiers),
        "sample_event_ids": identifiers,
    }


def verify_package(runtime: Runtime) -> dict[str, object]:
    root = runtime.context.path("result/package")
    manifest_path = root / "package-manifest.json"
    try:
        manifest = runtime.operator.full_build_package.verify_manifest(
            root, manifest_path
        )
    except (OSError, ValueError) as error:
        raise GuardError(f"published package verification failed: {error}") from error
    return {
        "manifest_sha256": sha256_file(manifest_path),
        "file_count": len(manifest["files"]),
        "total_bytes": manifest["total_bytes"],
    }


def verify_control(runtime: Runtime) -> dict[str, object]:
    root = runtime.context.path("result/control")
    sums = root / "SHA256SUMS"
    expected_sums = runtime.context.pin("control_sha256s_sha256")
    if not sums.is_file() or sha256_file(sums) != expected_sums:
        raise GuardError("published control SHA256SUMS differs from the contract")
    expected: dict[str, str] = {}
    for line in sums.read_text(encoding="utf-8").splitlines():
        try:
            digest, relative = line.split("  ", 1)
        except ValueError as error:
            raise GuardError("published control SHA256SUMS is invalid") from error
        path = Path(relative)
        if path.parts[:2] != ("transport", "control") or len(path.parts) != 3:
            raise GuardError("published control SHA256SUMS path is invalid")
        expected[path.name] = require_sha256(digest, f"control {path.name}")
    actual: set[str] = set()
    for path in root.iterdir():
        if path.is_symlink() or not path.is_file():
            raise GuardError(f"published control contains a non-regular file: {path}")
        actual.add(path.name)
    if actual != {*expected, "SHA256SUMS"}:
        raise GuardError("published control file set differs from SHA256SUMS")
    for name, digest in expected.items():
        if sha256_file(root / name) != digest:
            raise GuardError(f"published control file failed verification: {name}")
    return {
        "sha256s_sha256": expected_sums,
        "file_count": len(expected) + 1,
    }


def verify_sealed_local_files(runtime: Runtime) -> dict[str, object]:
    receipt_path = runtime.context.path("launch/retrieval-verification.json")
    receipt = read_json(receipt_path)
    if not isinstance(receipt, dict) or receipt.get("instance_id") != runtime.instance_id:
        raise GuardError("retrieval verification receipt is invalid")
    records = receipt.get("work_files")
    if not isinstance(records, list) or not records:
        raise GuardError("retrieval receipt has no sealed work files")
    root = runtime.context.path("result/work")
    expected: dict[str, dict[str, object]] = {}
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("path"), str):
            raise GuardError("retrieval receipt contains an invalid work record")
        expected[record["path"]] = record
    actual = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path.name != "retrieval-manifest.json"
    }
    for path in root.rglob("*"):
        if path.is_symlink() or (not path.is_dir() and not path.is_file()):
            raise GuardError(f"published work contains a non-regular entry: {path}")
    if actual != set(expected):
        raise GuardError("published work file set differs from the remote seal")
    replaced: dict[str, object] | None = None
    for relative, record in expected.items():
        path = root / relative
        if relative == LOCAL_VERIFICATION_REPLACEMENT:
            replaced = {
                "path": relative,
                "remote_sha256": record.get("sha256"),
                "local_sha256": sha256_file(path),
                "local_bytes": path.stat().st_size,
            }
            continue
        if (
            path.stat().st_size != record.get("bytes")
            or sha256_file(path) != record.get("sha256")
        ):
            raise GuardError(f"published work differs from the remote seal: {relative}")
    if replaced is None:
        raise GuardError("remote seal has no representation verification receipt")
    preparation = receipt.get("preparation_files")
    runtime.operator.validate_file_records(
        runtime.context.path("result/audit/preparation-attempts"), preparation
    )
    return {
        "retrieval_receipt_sha256": sha256_file(receipt_path),
        "work_file_count": len(expected),
        "preparation_file_count": len(preparation) if isinstance(preparation, list) else 0,
        "local_verification_replacement": replaced,
    }


def run_local_release_checks(
    runtime: Runtime,
    representation_version: str,
    remote_checks: dict[str, object] | None = None,
) -> dict[str, object]:
    package = verify_package(runtime)
    control = verify_control(runtime)
    sealed = verify_sealed_local_files(runtime)
    verification = runtime.context.controller(
        "result", ["verify-representation", CONFIG_RELATIVE]
    )
    runtime.operator.validate_representation(
        runtime.context, verification, complete=True
    )
    if (
        not isinstance(verification, dict)
        or verification.get("representation_version") != representation_version
    ):
        raise GuardError("local representation version differs from the remote version")
    identifiers = sample_event_ids(runtime)
    vector_response = runtime.context.controller(
        "result",
        ["vectors-for-notes", CONFIG_RELATIVE, ",".join(identifiers), representation_version],
    )
    vectors = validate_vectors(
        runtime, vector_response, representation_version, identifiers
    )
    if remote_checks is not None and vectors != remote_checks.get("vectors"):
        raise GuardError("remote and local stored vector hashes differ")
    return {
        "representation_version": representation_version,
        "verification": verification,
        "package": package,
        "control": control,
        "sealed_files": sealed,
        "vectors": vectors,
    }


def sync_result(runtime: Runtime) -> None:
    result = runtime.context.path("result")
    if not result.is_dir():
        raise GuardError("published result is missing before sync")
    completed = subprocess.run(
        ["sync", "--file-system", str(result)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise GuardError(f"result filesystem sync failed: {detail}")


def payload_manifest(result: Path) -> dict[str, object]:
    if not result.is_dir() or result.is_symlink():
        raise GuardError("published result is not a regular directory")
    files = []
    for path in sorted(result.rglob("*")):
        if path.is_symlink() or (not path.is_dir() and not path.is_file()):
            raise GuardError(f"published result contains a non-regular entry: {path}")
        if path.is_dir():
            continue
        relative_path = path.relative_to(result)
        if relative_path.parts[0] in PAYLOAD_EXCLUDED_TOP_LEVEL_PATHS:
            continue
        relative = relative_path.as_posix()
        files.append(
            {
                "path": relative,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    if not files:
        raise GuardError("published result contains no files")
    return {
        "schema_version": 1,
        "artifact_kind": "gte-full-build-final-local-payload",
        "excluded_top_level_paths": list(PAYLOAD_EXCLUDED_TOP_LEVEL_PATHS),
        "file_count": len(files),
        "total_bytes": sum(record["bytes"] for record in files),
        "files": files,
    }


def store_content_addressed(directory: Path, prefix: str, document: object) -> tuple[Path, str]:
    content = canonical_json(document)
    digest = sha256_bytes(content)
    path = directory / f"{prefix}-{digest}.json"
    atomic_bytes(path, content)
    return path, digest


def optional_receipt_hashes(runtime: Runtime) -> dict[str, str]:
    values: dict[str, str] = {}
    for relative in (
        "launch/create-result.json",
        "launch/offer.json",
        "launch/instance.json",
        "launch/instance-ownership.json",
        "launch/pre-transfer-instance-validation.json",
        "launch/instance-ownership-validation.json",
    ):
        path = runtime.context.path(relative)
        if path.is_file():
            values[relative] = sha256_file(path)
    return values


def write_review_report(
    runtime: Runtime,
    remote_checks: dict[str, object],
    local_checks: dict[str, object],
    retrieval: dict[str, object],
) -> dict[str, object]:
    reviews = runtime.context.path("launch/terminal-reviews")
    reviews.mkdir(parents=True, exist_ok=True, mode=0o700)
    manifest = payload_manifest(runtime.context.path("result"))
    manifest_path, manifest_sha = store_content_addressed(
        reviews, "payload", manifest
    )
    report = {
        "schema_version": 1,
        "artifact_kind": "gte-full-build-manual-terminal-review",
        "created_at_utc": utc_text(),
        "guard_sha256": sha256_file(Path(__file__).resolve()),
        "operation_config_sha256": sha256_file(runtime.context.config_path),
        "frozen_operator_sha256": sha256_file(runtime.context.operator_path),
        "instance_id": runtime.instance_id,
        "attempt_id": runtime.attempt_id,
        "label": runtime.context.label,
        "image": runtime.context.image,
        "remote_terminal": runtime.remote,
        "bound_receipts": optional_receipt_hashes(runtime),
        "retrieval_receipt_sha256": sha256_file(
            runtime.context.path("launch/retrieval-verification.json")
        ),
        "retrieval": retrieval,
        "representation_version": remote_checks["representation_version"],
        "remote_checks": remote_checks,
        "local_checks": local_checks,
        "payload_manifest": {
            "path": str(manifest_path),
            "sha256": manifest_sha,
            "file_count": manifest["file_count"],
            "total_bytes": manifest["total_bytes"],
        },
        "syncfs_completed": True,
        "warnings": [],
    }
    report_path, report_sha = store_content_addressed(reviews, "review", report)
    return {
        "state": "awaiting_manual_destroy_approval",
        "instance_id": runtime.instance_id,
        "representation_version": remote_checks["representation_version"],
        "review_sha256": report_sha,
        "report_path": str(report_path),
    }


def run_review(root: Path, config: Path) -> dict[str, object]:
    runtime = load_runtime(root.resolve(), config.resolve())
    with operation_lock(runtime), destruction_disabled(runtime):
        remote_checks = run_remote_read_only_checks(runtime)
        retrieval = runtime.operator.ensure_retrieved(
            runtime.context,
            runtime.instance_id,
            runtime.private_key,
            runtime.target,
            runtime.attempt_id,
        )
        if runtime.operator.publish_verified_result(
            runtime.context, runtime.attempt_id
        ) is not True:
            raise GuardError("local publication did not succeed; instance retained")
        local_checks = run_local_release_checks(
            runtime,
            require_sha256(
                remote_checks.get("representation_version"),
                "remote representation version",
            ),
            remote_checks,
        )
        sync_result(runtime)
        review = write_review_report(
            runtime, remote_checks, local_checks, retrieval
        )
        sync_result(runtime)
        return review


def load_review(runtime: Runtime, review_sha256: str) -> tuple[Path, dict[str, object]]:
    digest = require_sha256(review_sha256, "approved review")
    path = runtime.context.path(f"launch/terminal-reviews/review-{digest}.json")
    if not path.is_file() or sha256_file(path) != digest:
        raise GuardError("approved review does not exist or its hash differs")
    report = read_json(path)
    if not isinstance(report, dict):
        raise GuardError("approved review is invalid")
    checks = {
        "guard_sha256": sha256_file(Path(__file__).resolve()),
        "operation_config_sha256": sha256_file(runtime.context.config_path),
        "frozen_operator_sha256": sha256_file(runtime.context.operator_path),
        "instance_id": runtime.instance_id,
        "attempt_id": runtime.attempt_id,
        "label": runtime.context.label,
        "image": runtime.context.image,
    }
    if any(report.get(field) != value for field, value in checks.items()):
        raise GuardError("approved review no longer matches the live operation")
    if report.get("warnings") != [] or report.get("syncfs_completed") is not True:
        raise GuardError("approved review is not release-ready")
    return path, report


def verify_payload_manifest(report: dict[str, object]) -> dict[str, object]:
    reference = report.get("payload_manifest")
    if not isinstance(reference, dict):
        raise GuardError("review has no payload manifest")
    path_value = reference.get("path")
    if not isinstance(path_value, str):
        raise GuardError("review payload manifest path is invalid")
    path = Path(path_value)
    expected_sha = require_sha256(reference.get("sha256"), "payload manifest")
    if not path.is_file() or sha256_file(path) != expected_sha:
        raise GuardError("review payload manifest differs")
    expected = read_json(path)
    if not isinstance(expected, dict):
        raise GuardError("review payload manifest is invalid")
    result = path.parents[2] / "result"
    actual = payload_manifest(result)
    if actual != expected:
        raise GuardError("published result changed after manual review")
    return actual


def fresh_remote_seal(runtime: Runtime) -> dict[str, object]:
    response = runtime.operator.remote_json(
        runtime.context,
        runtime.private_key,
        runtime.target,
        "_remote-seal",
        "--attempt",
        runtime.attempt_id,
    )
    if not isinstance(response, dict) or response.get("terminal") is not True:
        raise GuardError("fresh remote seal is invalid")
    receipt = read_json(runtime.context.path("launch/retrieval-verification.json"))
    if not isinstance(receipt, dict):
        raise GuardError("retrieval receipt is invalid during final review")
    if (
        response.get("work_files", response.get("files")) != receipt.get("work_files")
        or response.get("preparation_files") != receipt.get("preparation_files")
        or response.get("terminal_record") != receipt.get("sealed_terminal")
    ):
        raise GuardError("fresh remote seal differs from the retrieved terminal state")
    return {
        "work_files_sha256": sha256_bytes(
            canonical_json(receipt.get("work_files"))
        ),
        "preparation_files_sha256": sha256_bytes(
            canonical_json(receipt.get("preparation_files"))
        ),
        "terminal_record": response.get("terminal_record"),
    }


def revalidate_before_destroy(
    runtime: Runtime, report: dict[str, object]
) -> dict[str, object]:
    seal = fresh_remote_seal(runtime)
    remote = run_remote_read_only_checks(runtime)
    if remote != report.get("remote_checks"):
        raise GuardError("fresh remote functional checks differ from the review")
    version = require_sha256(
        report.get("representation_version"), "review representation version"
    )
    local = run_local_release_checks(runtime, version, remote)
    if local != report.get("local_checks"):
        raise GuardError("fresh local checks differ from the review")
    sync_result(runtime)
    manifest = verify_payload_manifest(report)
    live = runtime.operator.sanitized_live_instances()
    matches = [row for row in live if str(row.get("id")) == runtime.instance_id]
    if len(matches) != 1:
        raise GuardError("the reviewed instance is not uniquely live before destruction")
    if not runtime.operator.verify_destroy_ownership(
        runtime.context, runtime.instance_id, matches[0]
    ):
        raise GuardError("the reviewed live instance is not durably bound")
    return {
        "remote_seal": seal,
        "payload_file_count": manifest["file_count"],
        "payload_total_bytes": manifest["total_bytes"],
        "live_instance": matches[0],
        "revalidated_at_utc": utc_text(),
    }


def confirmation_challenge(report: dict[str, object], review_sha256: str) -> str:
    return f"DESTROY {report['instance_id']} {report['representation_version']} {review_sha256}"


def manual_summary(report: dict[str, object]) -> dict[str, object]:
    remote = report.get("remote_checks")
    local = report.get("local_checks")
    remote = remote if isinstance(remote, dict) else {}
    local = local if isinstance(local, dict) else {}
    return {
        "review_sha256": report.get("review_sha256"),
        "guard_sha256": report.get("guard_sha256"),
        "operation_config_sha256": report.get("operation_config_sha256"),
        "frozen_operator_sha256": report.get("frozen_operator_sha256"),
        "instance_id": report.get("instance_id"),
        "image": report.get("image"),
        "representation_version": report.get("representation_version"),
        "payload_manifest": report.get("payload_manifest"),
        "remote_terminal": report.get("remote_terminal"),
        "bound_receipts": report.get("bound_receipts"),
        "retrieval_receipt_sha256": report.get("retrieval_receipt_sha256"),
        "retrieval": report.get("retrieval"),
        "query_config_sha256": remote.get("query_config_sha256"),
        "sample_event_ids": remote.get("sample_event_ids"),
        "remote_verification": remote.get("verification"),
        "remote_similar_notes": remote.get("similar_notes"),
        "remote_vectors": remote.get("vectors"),
        "local_verification": local.get("verification"),
        "local_package": local.get("package"),
        "local_control": local.get("control"),
        "local_sealed_files": local.get("sealed_files"),
        "local_vectors": local.get("vectors"),
        "syncfs_completed": report.get("syncfs_completed"),
        "final_revalidation": report.get("final_revalidation"),
        "warnings": report.get("warnings"),
    }


def write_all(descriptor: int, content: bytes) -> None:
    written = 0
    while written < len(content):
        count = os.write(descriptor, content[written:])
        if count <= 0:
            raise GuardError("could not finish displaying manual review evidence")
        written += count


def read_tty_confirmation(report: dict[str, object], challenge: str) -> str:
    descriptor = os.open("/dev/tty", os.O_RDWR | os.O_NOCTTY)
    try:
        summary = canonical_json(manual_summary(report))
        write_all(descriptor, summary)
        write_all(
            descriptor,
            f"\nType this exact line within five minutes:\n{challenge}\n> ".encode(),
        )
        readable, _, _ = select.select(
            [descriptor], [], [], TTY_CONFIRMATION_TIMEOUT_SECONDS
        )
        if not readable:
            raise GuardError("manual destroy confirmation timed out; instance retained")
        response = os.read(descriptor, 16 * 1024).decode("utf-8", errors="strict")
        return response.strip()
    except (OSError, UnicodeDecodeError) as error:
        raise GuardError(f"manual destroy confirmation failed: {error}") from error
    finally:
        os.close(descriptor)


def finish_after_destroy(runtime: Runtime) -> dict[str, object]:
    charge = runtime.operator.ensure_final_charge(
        runtime.context, runtime.instance_id
    )
    if charge is None:
        return runtime.operator.invoice_pending_result(
            runtime.context, runtime.instance_id
        )
    return runtime.operator.settle(runtime.context)


def validate_manual_authorization(
    runtime: Runtime, report: dict[str, object], review_sha256: str
) -> dict[str, object]:
    path = runtime.context.path("launch/manual-destroy-approval.json")
    authorization = read_json(path)
    if not isinstance(authorization, dict):
        raise GuardError("manual destroy authorization is invalid")
    expected = {
        "schema_version": 1,
        "artifact_kind": "gte-full-build-manual-destroy-authorization",
        "review_sha256": review_sha256,
        "instance_id": runtime.instance_id,
        "representation_version": report.get("representation_version"),
        "guard_sha256": sha256_file(Path(__file__).resolve()),
    }
    if any(authorization.get(field) != value for field, value in expected.items()):
        raise GuardError("manual destroy authorization differs from the reviewed result")
    challenge = confirmation_challenge(report, review_sha256)
    if authorization.get("challenge_sha256") != sha256_bytes(
        challenge.encode("utf-8")
    ):
        raise GuardError("manual destroy authorization has the wrong challenge")
    if not isinstance(authorization.get("revalidation"), dict):
        raise GuardError("manual destroy authorization lacks revalidation evidence")
    return authorization


def run_destroy(root: Path, config: Path, review_sha256: str) -> dict[str, object]:
    root = root.resolve()
    config = config.resolve()
    approval_exists = (root / "launch/manual-destroy-approval.json").is_file()
    provider_request_started = any(
        (root / relative).is_file()
        for relative in (
            "launch/destroy-request-attempted.json",
            "launch/destroy-response.json",
            "launch/destruction-confirmation.json",
        )
    )
    runtime = (
        load_recovery_runtime(root, config)
        if approval_exists and provider_request_started
        else load_runtime(root, config)
    )
    with operation_lock(runtime), destruction_disabled(runtime) as destroy:
        _report_path, report = load_review(runtime, review_sha256)
        approval_path = runtime.context.path("launch/manual-destroy-approval.json")
        if approval_path.is_file() and provider_request_started:
            validate_manual_authorization(runtime, report, review_sha256)
            verify_payload_manifest(report)
            sync_result(runtime)
            destroy(runtime.context, runtime.instance_id)
            return finish_after_destroy(runtime)
        revalidation = revalidate_before_destroy(runtime, report)
        challenge = confirmation_challenge(report, review_sha256)
        presented_report = {
            **report,
            "review_sha256": review_sha256,
            "final_revalidation": revalidation,
        }
        if read_tty_confirmation(presented_report, challenge) != challenge:
            raise GuardError("manual destroy confirmation differed; instance retained")
        authorization = {
            "schema_version": 1,
            "artifact_kind": "gte-full-build-manual-destroy-authorization",
            "authorized_at_utc": utc_text(),
            "review_sha256": review_sha256,
            "instance_id": runtime.instance_id,
            "representation_version": report["representation_version"],
            "guard_sha256": sha256_file(Path(__file__).resolve()),
            "challenge_sha256": sha256_bytes(challenge.encode("utf-8")),
            "revalidation": revalidation,
        }
        if approval_path.is_file():
            validate_manual_authorization(runtime, report, review_sha256)
        else:
            atomic_json(approval_path, authorization)
        sync_result(runtime)
        destroy(runtime.context, runtime.instance_id)
        return finish_after_destroy(runtime)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    subparsers = parser.add_subparsers(dest="operation", required=True)
    subparsers.add_parser("review")
    destroy = subparsers.add_parser("destroy")
    destroy.add_argument("--review-sha256", required=True)
    return parser.parse_args()


def main() -> int:
    arguments = parse_args()
    try:
        if arguments.operation == "review":
            result = run_review(arguments.root, arguments.config)
        else:
            result = run_destroy(
                arguments.root, arguments.config, arguments.review_sha256
            )
    except (GuardError, OSError, ValueError) as error:
        print(f"vast-full-build-terminal-guard: {error}", file=sys.stderr)
        return 1
    print(canonical_json(result).decode("utf-8"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
