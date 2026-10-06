#!/usr/bin/env python3
"""Generalization of the successful GTE Vast controller.

The original controller remains unchanged in gte/vast_full_build.py. Without a
workload section this retains its GTE contract; with one, command/input/output
configuration replaces only GTE-specific workload preparation and accounting.
Command workloads preserve the instance until an explicit stop command.
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import getpass
import hashlib
import ipaddress
import json
import os
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_CEILING
from pathlib import Path
from typing import BinaryIO, Iterator, NoReturn

sys.dont_write_bytecode = True

if not Path(__file__).with_name("calibration_package.py").is_file():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gte"))

import calibration_package
import full_build_package


class OperationError(Exception):
    """A state or provider result that must stop the operation."""


class RemotePreparationFailed(OperationError):
    """The paid host published terminal preparation failure evidence."""


class RemoteAccessUnavailable(OperationError):
    """The bound paid host is temporarily unreachable."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> object:
    try:
        with path.open(encoding="utf-8") as source:
            return json.load(source)
    except (OSError, json.JSONDecodeError) as error:
        raise OperationError(f"cannot read JSON {path}: {error}") from error


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_text(moment: datetime | None = None) -> str:
    return (moment or utc_now()).strftime("%Y-%m-%dT%H:%M:%SZ")


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
        raise OperationError(f"document is not canonical JSON: {error}") from error


def sync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_bytes(path: Path, content: bytes, *, replace: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.exists() and not replace:
        if path.read_bytes() == content:
            return
        raise OperationError(f"authoritative receipt already differs: {path}")
    temporary = path.with_name(f".{path.name}.next-{os.getpid()}")
    try:
        descriptor = os.open(
            temporary,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )
        try:
            written = 0
            while written < len(content):
                count = os.write(descriptor, content[written:])
                if count <= 0:
                    raise OperationError(f"could not finish writing receipt: {path}")
                written += count
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        if not replace and path.exists():
            if path.read_bytes() != content:
                raise OperationError(f"authoritative receipt raced: {path}")
            temporary.unlink()
            return
        os.replace(temporary, path)
        sync_directory(path.parent)
    finally:
        with contextlib.suppress(FileNotFoundError):
            temporary.unlink()


def atomic_json(path: Path, document: object, *, replace: bool = False) -> None:
    atomic_bytes(path, canonical_json(document), replace=replace)


def atomic_copy(source: Path, destination: Path) -> None:
    if destination.exists():
        if sha256_file(source) != sha256_file(destination):
            raise OperationError(f"authoritative copy differs: {destination}")
        return
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = destination.with_name(f".{destination.name}.next-{os.getpid()}")
    try:
        with source.open("rb") as input_file, temporary.open("xb") as output_file:
            os.chmod(temporary, 0o600)
            shutil.copyfileobj(input_file, output_file, 1024 * 1024)
            output_file.flush()
            os.fsync(output_file.fileno())
        os.replace(temporary, destination)
        sync_directory(destination.parent)
    finally:
        with contextlib.suppress(FileNotFoundError):
            temporary.unlink()


def required_object(document: dict[str, object], field: str) -> dict[str, object]:
    value = document.get(field)
    if not isinstance(value, dict):
        raise OperationError(f"operation config `{field}` must be an object")
    return value


def required_string(document: dict[str, object], field: str) -> str:
    value = document.get(field)
    if not isinstance(value, str) or not value:
        raise OperationError(f"operation config `{field}` must be a nonempty string")
    return value


def required_positive_int(document: dict[str, object], field: str) -> int:
    value = document.get(field)
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise OperationError(f"operation config `{field}` must be a positive integer")
    return value


def required_nonnegative_int(document: dict[str, object], field: str) -> int:
    value = document.get(field)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise OperationError(
            f"operation config `{field}` must be a nonnegative integer"
        )
    return value


def require_sha256(value: str, field: str) -> str:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise OperationError(f"operation config `{field}` must be a SHA-256")
    return value


def completed_process(
    arguments: list[str],
    *,
    input_bytes: bytes | None = None,
    environment: dict[str, str] | None = None,
    redact: bool = False,
) -> subprocess.CompletedProcess[bytes]:
    try:
        result = subprocess.run(
            arguments,
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env=environment,
        )
    except OSError as error:
        raise OperationError(f"could not execute {arguments[0]}: {error}") from error
    if result.returncode != 0:
        command = arguments[0] if redact else " ".join(arguments)
        detail = ""
        if not redact:
            detail = result.stderr.decode("utf-8", errors="replace").strip()
        suffix = f": {detail}" if detail else ""
        raise OperationError(
            f"command failed with status {result.returncode}: {command}{suffix}"
        )
    return result


def command_json(
    arguments: list[str],
    *,
    input_bytes: bytes | None = None,
    environment: dict[str, str] | None = None,
    redact: bool = False,
) -> object:
    result = completed_process(
        arguments,
        input_bytes=input_bytes,
        environment=environment,
        redact=redact,
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise OperationError(f"{arguments[0]} did not return JSON") from error


@contextlib.contextmanager
def operation_lock(root: Path) -> Iterator[None]:
    launch = root / "launch"
    launch.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = launch / ".operation.lock"
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise OperationError("another full-build operation is active") from error
        yield
    finally:
        os.close(descriptor)


@dataclass(frozen=True)
class Context:
    root: Path
    config_path: Path
    ledger: Path
    config: dict[str, object]

    @classmethod
    def load(cls, args: argparse.Namespace) -> "Context":
        root = args.root.resolve()
        config_path = args.config.resolve()
        document = read_json(config_path)
        if not isinstance(document, dict):
            raise OperationError("operation config must be a JSON object")
        if document.get("schema_version") != 1:
            raise OperationError("operation config schema_version must be 1")
        if document.get("artifact_kind") not in ("gte-vast-full-build-operation", "vast-command-operation"):
            raise OperationError("operation config artifact_kind is invalid")
        if args.operation.startswith("_remote"):
            ledger = root / "budget-ledger.json"
        else:
            canonical_ledger = Path(
                required_string(document, "canonical_ledger_path")
            )
            if not canonical_ledger.is_absolute():
                raise OperationError("canonical_ledger_path must be absolute")
            ledger = canonical_ledger.resolve()
        context = cls(root=root, config_path=config_path, ledger=ledger, config=document)
        context.validate()
        return context

    def validate(self) -> None:
        # New approvals must explicitly budget transfers; an old or missing
        # allowance is not evidence that transfers are free. Frozen runs keep
        # their original controller and contract.
        transfer = required_nonnegative_int(self.limits, "transfer_allowance_micro_usd")
        if transfer > self.limit("reservation_ceiling_micro_usd"):
            raise OperationError("transfer allowance exceeds the reservation ceiling")
        if self.command_workload:
            validate_command_context(self)
            return
        self.label
        self.image
        canonical_ledger = Path(
            required_string(self.config, "canonical_ledger_path")
        )
        if not canonical_ledger.is_absolute():
            raise OperationError("canonical_ledger_path must be absolute")
        for field in (
            "operator_sha256",
            "controller_sha256",
            "control_sha256s_sha256",
            "transport_manifest_sha256",
            "execution_package_manifest_sha256",
            "descriptor_sha256",
        ):
            self.pin(field)
        for field in ("controller_source_commit", "image_source_commit"):
            required_string(self.pins, field)
        for field in (
            "disk_gb",
            "maximum_rental_rate_micro_usd_per_hour",
            "reservation_ceiling_micro_usd",
            "lifetime_budget_micro_usd",
            "artifact_storage_and_transfer_micro_usd",
            "one_cold_restart_micro_usd",
            "one_lost_shard_micro_usd",
            "setup_cost_micro_usd",
            "manual_stop_cost_micro_usd",
        ):
            self.limit(field)
        if self.limit("reservation_ceiling_micro_usd") > self.limit(
            "lifetime_budget_micro_usd"
        ):
            raise OperationError("reservation ceiling exceeds the lifetime budget")
        if self.limit("setup_cost_micro_usd") >= self.limit(
            "manual_stop_cost_micro_usd"
        ):
            raise OperationError("setup cost gate must precede the manual stop warning")
        queries = required_object(self.config, "offer_queries")
        required_string(queries, "us")
        required_string(queries, "global")
        for field in (
            "represented_rows",
            "total_rows",
            "completed_shards",
            "final_vector_bytes",
        ):
            required_positive_int(self.expected, field)
        if required_positive_int(self.expected, "represented_rows") >= required_positive_int(
            self.expected, "total_rows"
        ):
            raise OperationError("checkpoint rows must be smaller than total rows")
        require_sha256(
            required_string(self.expected, "build_identity_sha256"),
            "expected.build_identity_sha256",
        )
        if "checkpoint_shard_ordinal" in self.expected:
            required_nonnegative_int(self.expected, "checkpoint_shard_ordinal")
            require_sha256(
                required_string(self.expected, "checkpoint_vector_sha256"),
                "expected.checkpoint_vector_sha256",
            )
        corpus = required_object(self.config, "corpus")
        required_positive_int(corpus, "bytes")
        require_sha256(required_string(corpus, "sha256"), "corpus.sha256")
        for field in (
            "provider_attempts",
            "preparation_attempts",
            "destroy_attempts",
            "invoice_retry_attempts",
        ):
            required_positive_int(self.timing, field)
        if required_positive_int(self.timing, "destroy_attempts") < 2:
            raise OperationError("destroy confirmation requires at least two attempts")
        for field in (
            "provider_poll_seconds",
            "preparation_poll_seconds",
            "destroy_poll_seconds",
            "invoice_retry_seconds",
            "invoice_confirmation_seconds",
            "invoice_not_before_seconds",
            "status_watch_seconds",
        ):
            required_nonnegative_int(self.timing, field)

    @property
    def command_workload(self) -> bool:
        return self.config.get("artifact_kind") == "vast-command-operation"

    @property
    def remote_python(self) -> str:
        if self.command_workload:
            return required_string(required_object(self.config, "workload"), "python")
        return "/opt/gte-venv/bin/python"

    @property
    def label(self) -> str:
        return required_string(self.config, "label")

    @property
    def image(self) -> str:
        image = required_string(self.config, "image")
        try:
            calibration_package.immutable_image_ref(image)
        except ValueError as error:
            raise OperationError(str(error)) from error
        return image

    @property
    def pins(self) -> dict[str, object]:
        return required_object(self.config, "pins")

    @property
    def limits(self) -> dict[str, object]:
        return required_object(self.config, "limits")

    @property
    def expected(self) -> dict[str, object]:
        return required_object(self.config, "expected")

    @property
    def timing(self) -> dict[str, object]:
        return required_object(self.config, "timing")

    def pin(self, field: str) -> str:
        return require_sha256(required_string(self.pins, field), f"pins.{field}")

    def limit(self, field: str) -> int:
        return required_positive_int(self.limits, field)

    def timing_value(self, field: str) -> int:
        if field.endswith("_seconds"):
            return required_nonnegative_int(self.timing, field)
        return required_positive_int(self.timing, field)

    def path(self, relative: str) -> Path:
        candidate = (self.root / relative).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError as error:
            raise OperationError(f"path escapes operation root: {relative}") from error
        return candidate

    @property
    def operator_path(self) -> Path:
        return self.path("transport/control/vast_full_build.py")

    @property
    def approval_dir(self) -> Path:
        return self.path("launch/plans")

    def controller(self, layout: str, arguments: list[str]) -> object:
        result = completed_process(self.controller_arguments(layout, arguments))
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as error:
            raise OperationError("gte-oracle did not return JSON") from error

    def controller_arguments(self, layout: str, arguments: list[str]) -> list[str]:
        return [
            "docker",
            "run",
            "--rm",
            "--pull",
            "never",
            "--network",
            "none",
            "--user",
            f"{os.getuid()}:{os.getgid()}",
            "-v",
            f"{self.root}:/workspace/oracle-full-build",
            "-w",
            f"/workspace/oracle-full-build/{layout}",
            "--entrypoint",
            "/workspace/oracle-full-build/transport/control/gte-oracle",
            self.image,
            *arguments,
        ]


def verify_sha(path: Path, expected: str, field: str) -> None:
    if not path.is_file() or sha256_file(path) != expected:
        raise OperationError(f"{field} does not match the frozen operation contract")


def verify_control_sums(context: Context) -> None:
    sums = context.path("transport/control/SHA256SUMS")
    verify_sha(sums, context.pin("control_sha256s_sha256"), "control SHA256SUMS")
    for line in sums.read_text(encoding="utf-8").splitlines():
        try:
            digest, relative = line.split("  ", 1)
        except ValueError as error:
            raise OperationError("control SHA256SUMS contains an invalid line") from error
        verify_sha(context.path(relative), require_sha256(digest, relative), relative)


def verify_reviewed_artifacts(
    context: Context, *, require_local_execution_package: bool = True
) -> None:
    if context.command_workload:
        verify_command_artifacts(context)
        return
    verify_control_sums(context)
    verify_sha(
        context.path("transport/control/gte-oracle"),
        context.pin("controller_sha256"),
        "controller",
    )
    source_commit = context.path(
        "transport/control/gte-oracle-source-commit.txt"
    ).read_text(encoding="utf-8").strip()
    if source_commit != required_string(context.pins, "controller_source_commit"):
        raise OperationError("controller source commit does not match the contract")
    verify_sha(
        context.path("transport/transport-manifest.json"),
        context.pin("transport_manifest_sha256"),
        "transport manifest",
    )
    execution_manifest = (
        context.path("execution/package/package-manifest.json")
        if require_local_execution_package
        else context.path("transport/package-skeleton/package-manifest.json")
    )
    verify_sha(
        execution_manifest,
        context.pin("execution_package_manifest_sha256"),
        "execution package manifest",
    )
    try:
        full_build_package.verify_manifest(
            context.path("transport"),
            context.path("transport/transport-manifest.json"),
        )
        if require_local_execution_package:
            full_build_package.verify_manifest(
                context.path("execution/package"), execution_manifest
            )
    except (OSError, ValueError) as error:
        raise OperationError(f"reviewed artifact verification failed: {error}") from error
    verify_sha(context.operator_path, context.pin("operator_sha256"), "operator")
    verify_sha(Path(__file__).resolve(), context.pin("operator_sha256"), "invoked operator")
    if Path(__file__).resolve() != context.operator_path:
        raise OperationError(
            "reviewed workflow must be invoked through the transported operator"
        )
    if context.operator_path.read_bytes() != Path(__file__).resolve().read_bytes():
        raise OperationError("invoked operator differs from transported operator")
    package_config_paths = [
        context.path("transport/package-skeleton/run/full-build-config.json")
    ]
    if require_local_execution_package:
        package_config_paths.insert(
            0, context.path("execution/package/run/full-build-config.json")
        )
    try:
        launch_image = calibration_package.immutable_image_ref(context.image)
    except ValueError as error:
        raise OperationError(f"frozen launch container image is invalid: {error}") from error
    for package_config_path in package_config_paths:
        package_config = read_json(package_config_path)
        if not isinstance(package_config, dict):
            raise OperationError("frozen full-build config is invalid")
        try:
            package_image = calibration_package.immutable_image_ref(
                package_config.get("container_image")
            )
        except ValueError as error:
            raise OperationError(
                f"frozen full-build container image is invalid: {error}"
            ) from error
        if package_image != launch_image:
            raise OperationError(
                "operation contract and frozen full-build config differ on container image"
            )
        full_build = package_config.get("full_build")
        if not isinstance(full_build, dict):
            raise OperationError("frozen full-build config has no full_build settings")
        for field in (
            "artifact_storage_and_transfer_micro_usd",
            "one_cold_restart_micro_usd",
            "one_lost_shard_micro_usd",
        ):
            if full_build.get(field) != context.limit(field):
                raise OperationError(
                    f"operation contract and frozen full-build config differ on {field}"
                )


def vast_json(arguments: list[str]) -> object:
    return command_json(["vastai", *arguments])


def sanitized_live_instances() -> list[dict[str, object]]:
    try:
        return calibration_package.sanitize_instance_list(
            vast_json(["show", "instances", "--raw"])
        )
    except ValueError as error:
        raise OperationError(f"Vast instance inventory is invalid: {error}") from error


def search_offers(query: str, disk_gb: int) -> list[dict[str, object]]:
    document = vast_json(
        [
            "search",
            "offers",
            query,
            "--type",
            "on-demand",
            "--storage",
            str(disk_gb),
            "--order",
            "dph_total",
            "--limit",
            "20",
            "--raw",
        ]
    )
    if not isinstance(document, list):
        raise OperationError("Vast offer search did not return an array")
    return [row for row in document if isinstance(row, dict)]


def select_offer(context: Context) -> tuple[str, dict[str, object]]:
    if context.command_workload:
        offer = required_object(context.config, "selected_offer")
        query = f"machine_id={offer['machine_id']} num_gpus={offer['num_gpus']} rentable=true rented=false"
        return query, validate_offer(context, offer, str(offer["id"]))
    queries = required_object(context.config, "offer_queries")
    for name in ("us", "global"):
        query = required_string(queries, name)
        valid: list[dict[str, object]] = []
        for row in search_offers(query, context.limit("disk_gb")):
            identifier = row.get("id")
            if isinstance(identifier, bool):
                continue
            try:
                valid.append(
                    full_build_package.validate_full_build_offer(row, str(identifier))
                )
            except ValueError:
                continue
        if valid:
            valid.sort(
                key=lambda row: (
                    full_build_package.decimal_field(row, "dph_total"),
                    int(str(row["id"])),
                )
            )
            selected = valid[0]
            rate = int(
                (
                    full_build_package.decimal_field(selected, "dph_total")
                    * Decimal(1_000_000)
                ).to_integral_value(rounding=ROUND_CEILING)
            )
            if rate > context.limit("maximum_rental_rate_micro_usd_per_hour"):
                continue
            return query, selected
    raise OperationError("no Vast offer satisfies the frozen full-build contract")


def verify_image(context: Context) -> None:
    if context.command_workload:
        completed_process(["docker", "image", "inspect", context.image])
        completed_process(["docker", "run", "--rm", "--network", "none", "--entrypoint",
                           "/usr/bin/tar", context.image, "--version"])
        return
    result = completed_process(
        [
            "docker",
            "image",
            "inspect",
            context.image,
            "--format",
            '{{ index .Config.Labels "org.opencontainers.image.revision" }}',
        ]
    )
    revision = result.stdout.decode("utf-8", errors="strict").strip()
    if revision != required_string(context.pins, "image_source_commit"):
        raise OperationError("local image does not match its frozen source commit")
    completed_process(
        [
            "docker",
            "run",
            "--rm",
            "--network",
            "none",
            "--entrypoint",
            "/usr/bin/tar",
            context.image,
            "--version",
        ]
    )


def ensure_retrieval_destination(context: Context) -> None:
    if context.command_workload:
        for relative in ("result.next/work", "result.next/audit"):
            context.path(relative).mkdir(parents=True, exist_ok=True, mode=0o700)
        return
    destination = context.path("result.next")
    if context.path("result").exists():
        return
    if not destination.exists():
        staging = context.path(".result.next.prepare")
        if staging.exists():
            shutil.rmtree(staging)
        staging.mkdir(mode=0o700)
        try:
            completed_process(
                [
                    "cp",
                    "-a",
                    "--reflink=auto",
                    str(context.path("execution/package")),
                    str(staging / "package"),
                ]
            )
            completed_process(
                [
                    "cp",
                    "-a",
                    str(context.path("transport/control")),
                    str(staging / "control"),
                ]
            )
            (staging / "work").mkdir(mode=0o700)
            (staging / "audit").mkdir(mode=0o700)
            sync_directory(staging)
            os.replace(staging, destination)
            sync_directory(destination.parent)
        finally:
            if staging.exists():
                shutil.rmtree(staging)
    for relative in ("package", "control", "work", "audit"):
        if not (destination / relative).is_dir():
            raise OperationError("result.next is not a complete retrieval destination")


def verify_baseline_ledgers(context: Context) -> str:
    paths = [
        context.ledger,
        context.path("execution/work/budget-ledger.json"),
        context.path("transport/work-seed/budget-ledger.json"),
    ]
    hashes = []
    for path in paths:
        if not path.is_file():
            raise OperationError(f"baseline ledger is missing: {path}")
        read_json(path)
        hashes.append(sha256_file(path))
    if len(set(hashes)) != 1:
        raise OperationError("canonical, execution, and transport ledgers differ")
    return hashes[0]


def plan_document(
    context: Context,
    query: str,
    offer: dict[str, object],
    projection: object,
    ledger_sha256: str,
) -> dict[str, object]:
    if not isinstance(projection, dict):
        raise OperationError("full-build projection is not an object")
    projected = projection.get("projected_lifetime_total_micro_usd")
    if isinstance(projected, bool) or not isinstance(projected, int):
        raise OperationError("full-build projection has no lifetime total")
    if projected > context.limit("lifetime_budget_micro_usd"):
        raise OperationError("full-build projection exceeds the lifetime budget")
    total = projection.get("total_micro_usd")
    if isinstance(total, bool) or not isinstance(total, int):
        raise OperationError("full-build projection has no reservation total")
    if total > context.limit("reservation_ceiling_micro_usd"):
        raise OperationError("full-build projection exceeds the reservation ceiling")
    return {
        "schema_version": 1,
        "artifact_kind": "gte-vast-full-build-approval-plan",
        "created_at_utc": utc_text(),
        "operation_config_sha256": sha256_file(context.config_path),
        "operator_sha256": context.pin("operator_sha256"),
        "image": context.image,
        "label": context.label,
        "transport_manifest_sha256": context.pin("transport_manifest_sha256"),
        "execution_package_manifest_sha256": context.pin(
            "execution_package_manifest_sha256"
        ),
        "canonical_ledger_path": str(context.ledger),
        "canonical_ledger_sha256": ledger_sha256,
        "offer_query": query,
        "offer": offer,
        "projection": projection,
        "maximum_rental_rate_micro_usd_per_hour": context.limit(
            "maximum_rental_rate_micro_usd_per_hour"
        ),
        "reservation_ceiling_micro_usd": context.limit(
            "reservation_ceiling_micro_usd"
        ),
    }


def load_approval_plan(context: Context, digest: str) -> dict[str, object]:
    require_sha256(digest, "approval")
    path = context.approval_dir / f"{digest}.json"
    if not path.is_file() or sha256_file(path) != digest:
        raise OperationError("approved plan does not exist or does not match its SHA-256")
    document = read_json(path)
    if not isinstance(document, dict) or document.get("artifact_kind") != (
        "gte-vast-full-build-approval-plan"
    ):
        raise OperationError("approved plan is invalid")
    checks = {
        "operation_config_sha256": sha256_file(context.config_path),
        "operator_sha256": context.pin("operator_sha256"),
        "image": context.image,
        "label": context.label,
        "transport_manifest_sha256": context.pin("transport_manifest_sha256"),
        "execution_package_manifest_sha256": context.pin(
            "execution_package_manifest_sha256"
        ),
        "canonical_ledger_path": str(context.ledger),
        "reservation_ceiling_micro_usd": context.limit(
            "reservation_ceiling_micro_usd"
        ),
    }
    for field, expected in checks.items():
        if document.get(field) != expected:
            raise OperationError(f"approved plan no longer matches `{field}`")
    if not isinstance(document.get("offer"), dict):
        raise OperationError("approved plan has no exact offer")
    if not isinstance(document.get("projection"), dict):
        raise OperationError("approved plan has no exact projection")
    return document


def approval_receipt(context: Context, supplied: str | None) -> dict[str, object]:
    path = context.path("launch/approval.json")
    if path.exists():
        document = read_json(path)
        if not isinstance(document, dict):
            raise OperationError("approval receipt is invalid")
        digest = document.get("approval_sha256")
        if not isinstance(digest, str):
            raise OperationError("approval receipt has no plan SHA-256")
        if supplied is not None and supplied != digest:
            raise OperationError("supplied approval differs from the recorded approval")
        load_approval_plan(context, digest)
        return document
    if supplied is None:
        raise OperationError("run requires --approve with the exact prepared plan SHA-256")
    plan = load_approval_plan(context, supplied)
    refresh_approved_offer(context, plan)
    if any(row.get("label") == context.label for row in sanitized_live_instances()):
        raise OperationError("a live instance already uses the full-build label")
    receipt = {
        "schema_version": 1,
        "artifact_kind": "gte-vast-full-build-approval",
        "approval_sha256": supplied,
        "approved_at_utc": utc_text(),
        "operation_config_sha256": sha256_file(context.config_path),
        "operator_sha256": context.pin("operator_sha256"),
        "canonical_ledger_path": str(context.ledger),
        "offer_id": str(plan["offer"]["id"]),
        "reservation_ceiling_micro_usd": context.limit(
            "reservation_ceiling_micro_usd"
        ),
    }
    atomic_json(path, receipt)
    return receipt


def refresh_approved_offer(
    context: Context, plan: dict[str, object]
) -> dict[str, object]:
    query = plan.get("offer_query")
    approved = plan.get("offer")
    if not isinstance(query, str) or not isinstance(approved, dict):
        raise OperationError("approved offer record is invalid")
    identifier = str(approved.get("id"))
    if context.command_workload:
        # The caller supplies the exact offer. A second search can return a
        # different GPU pair from the same host; it is not an availability proof.
        matches = [required_object(context.config, "selected_offer")]
    else:
        matches = [
            row
            for row in search_offers(query, context.limit("disk_gb"))
            if str(row.get("id")) == identifier
        ]
    if len(matches) != 1:
        raise OperationError("the exact approved Vast offer is no longer available")
    try:
        selected = validate_offer(context, matches[0], identifier)
        for field in ("id", "machine_id", "bundle_id"):
            if selected.get(field) != approved.get(field):
                raise ValueError(f"refreshed offer changed {field}")
        for field in ("dph_total", "inet_down_cost", "inet_up_cost"):
            if full_build_package.decimal_field(
                selected, field
            ) > full_build_package.decimal_field(approved, field):
                raise ValueError(f"refreshed offer worsened {field}")
    except ValueError as error:
        raise OperationError(f"refreshed offer is not the approved offer: {error}") from error
    path = context.path("launch/offer.json")
    if path.exists():
        recorded = read_json(path)
        if not isinstance(recorded, list) or len(recorded) != 1:
            raise OperationError("recorded offer receipt is invalid")
        try:
            frozen = validate_offer(context, recorded[0], identifier)
        except ValueError as error:
            raise OperationError(f"recorded offer receipt is invalid: {error}") from error
        for field in ("id", "machine_id", "bundle_id"):
            if selected.get(field) != frozen.get(field):
                raise OperationError(f"live offer changed recorded {field}")
        for field in ("dph_total", "inet_down_cost", "inet_up_cost"):
            if full_build_package.decimal_field(
                selected, field
            ) > full_build_package.decimal_field(frozen, field):
                raise OperationError(f"live offer worsened recorded {field}")
        return frozen
    atomic_json(path, [selected])
    return selected


def replace_from_expected(
    source: Path,
    destination: Path,
    *,
    allowed_existing_sha256: set[str],
) -> None:
    existing = sha256_file(destination) if destination.is_file() else None
    source_digest = sha256_file(source)
    if existing == source_digest:
        return
    if existing not in allowed_existing_sha256:
        raise OperationError(f"refusing to replace unexpected authoritative file: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = destination.with_name(f".{destination.name}.next-{os.getpid()}")
    try:
        shutil.copyfile(source, temporary)
        os.chmod(temporary, 0o600)
        with temporary.open("rb") as copied:
            os.fsync(copied.fileno())
        os.replace(temporary, destination)
        sync_directory(destination.parent)
    finally:
        with contextlib.suppress(FileNotFoundError):
            temporary.unlink()


def ensure_reservation(
    context: Context, plan: dict[str, object]
) -> dict[str, object]:
    if context.command_workload:
        return reserve_command_workload(context, plan)
    baseline = context.path("launch/pre-reservation-budget-ledger.json")
    reservation_path = context.path("launch/full-build-reservation.json")
    execution_ledger = context.path("execution/work/budget-ledger.json")
    rejected_path = context.path("launch/rejected-reservation.json")
    invoice_start = context.path("launch/invoice-start-date.txt")
    if not invoice_start.exists():
        atomic_bytes(invoice_start, f"{utc_now().date().isoformat()}\n".encode("utf-8"))
    if not baseline.exists():
        expected = plan.get("canonical_ledger_sha256")
        if not isinstance(expected, str) or sha256_file(context.ledger) != expected:
            raise OperationError("canonical ledger changed after approval planning")
        if sha256_file(execution_ledger) != expected:
            raise OperationError("execution ledger changed before reservation")
        atomic_copy(context.ledger, baseline)
    baseline_digest = sha256_file(baseline)

    def finish_rejected_result(document: object) -> NoReturn:
        if not isinstance(document, dict) or not isinstance(
            document.get("controller_result"), dict
        ):
            raise OperationError("rejected reservation receipt is invalid")
        result_digest = document.get("mutated_execution_ledger_sha256")
        if not isinstance(result_digest, str):
            raise OperationError("rejected reservation has no ledger identity")
        require_sha256(result_digest, "rejected reservation ledger")
        current = sha256_file(execution_ledger)
        if current != baseline_digest:
            replace_from_expected(
                baseline,
                execution_ledger,
                allowed_existing_sha256={result_digest},
            )
        if sha256_file(context.ledger) != baseline_digest:
            raise OperationError(
                "canonical ledger changed during rejected reservation recovery"
            )
        reason = document.get("reason")
        raise OperationError(
            reason
            if isinstance(reason, str) and reason
            else "a controller reservation result was rejected before publication"
        )

    if rejected_path.exists():
        finish_rejected_result(read_json(rejected_path))
    created_receipt = False
    if reservation_path.exists():
        reservation = read_json(reservation_path)
    else:
        reservation = context.controller(
            "execution",
            [
                "reserve-full-build",
                "package/run/full-build-config.json",
                utc_text(),
            ],
        )
        if not isinstance(reservation, dict):
            raise OperationError("reservation result is invalid")
        created_receipt = True
    if not isinstance(reservation, dict):
        raise OperationError("reservation receipt is invalid")
    previous = reservation.get("previous_ledger_sha256")
    reserved = reservation.get("ledger_sha256")
    def reject_new_result(reason: str) -> NoReturn:
        if not created_receipt:
            raise OperationError(reason)
        mutated_digest = sha256_file(execution_ledger)
        atomic_json(
            rejected_path,
            {
                "schema_version": 1,
                "reason": reason,
                "controller_result": reservation,
                "mutated_execution_ledger_sha256": mutated_digest,
                "rejected_at_utc": utc_text(),
            },
        )
        finish_rejected_result(read_json(rejected_path))

    if previous != baseline_digest or not isinstance(reserved, str):
        reject_new_result("reservation does not follow the approved ledger")
    try:
        require_sha256(reserved, "reservation ledger")
    except OperationError:
        reject_new_result("reservation ledger identity is invalid")
    projection = plan.get("projection")
    if not isinstance(projection, dict):
        raise OperationError("approved plan has no reservation projection")
    projection_fields = (
        "remaining_compute_micro_usd",
        "artifact_storage_and_transfer_micro_usd",
        "paid_lazy_inference_micro_usd",
        "one_cold_restart_micro_usd",
        "one_lost_shard_micro_usd",
        "total_micro_usd",
        "projected_lifetime_total_micro_usd",
        "remaining_lifetime_budget_micro_usd",
    )
    for field in projection_fields:
        if reservation.get(field) != projection.get(field):
            reject_new_result(
                f"reservation projection differs from the approved plan on {field}"
            )
    total = reservation.get("total_micro_usd")
    if isinstance(total, bool) or not isinstance(total, int):
        reject_new_result("reservation total is invalid")
    if total > context.limit("reservation_ceiling_micro_usd"):
        reject_new_result("reservation exceeds the approved reservation ceiling")
    lifetime_total = reservation.get("projected_lifetime_total_micro_usd")
    if isinstance(lifetime_total, bool) or not isinstance(lifetime_total, int):
        reject_new_result("reservation lifetime projection is invalid")
    if lifetime_total > context.limit("lifetime_budget_micro_usd"):
        reject_new_result("reservation exceeds the lifetime budget")
    if sha256_file(execution_ledger) != reserved:
        reject_new_result("execution ledger does not match its reservation receipt")
    if created_receipt:
        atomic_json(reservation_path, reservation)
    replace_from_expected(
        execution_ledger,
        context.ledger,
        allowed_existing_sha256={baseline_digest},
    )
    reserved_copy = context.path("launch/reserved-budget-ledger.json")
    atomic_copy(execution_ledger, reserved_copy)
    if sha256_file(reserved_copy) != reserved:
        raise OperationError("reserved transfer ledger is invalid")
    return reservation


def write_preclaim_failure(context: Context, reason: str) -> None:
    failure = context.path("launch/preclaim-failure.log")
    if not failure.exists():
        atomic_bytes(
            failure,
            f"{utc_text()} pre-worker failure: {reason}\n".encode("utf-8"),
        )
    charge = context.path("launch/provider-final-charge.json")
    if not charge.exists():
        atomic_json(
            charge,
            {
                "schema_version": 1,
                "actual_charge_micro_usd": 0,
                "reason": reason,
            },
        )


def docker_pat_from_tty() -> str:
    try:
        descriptor = os.open("/dev/tty", os.O_RDWR | os.O_NOCTTY)
    except OSError as error:
        raise OperationError("Docker PAT requires an interactive terminal") from error
    else:
        os.close(descriptor)
    try:
        value = getpass.getpass("Docker read-only PAT: ")
    except (EOFError, OSError) as error:
        raise OperationError("Docker PAT requires an interactive terminal") from error
    if not value or any(character.isspace() for character in value):
        raise OperationError("Docker PAT must be one nonempty token")
    return value


def invoke_private_create(
    context: Context, offer: dict[str, object], docker_pat: str
) -> None:
    marker = context.path("launch/create-request-attempted.txt")
    outcome = context.path("launch/create-api-outcome.json")
    if marker.exists():
        raise OperationError("create request was already attempted")
    environment = os.environ.copy()
    environment.pop("DOCKER_PULL_PAT", None)
    environment["VASTAI_NO_UPDATE_CHECK"] = "1"
    if not environment.get("VAST_API_KEY"):
        secret_path = Path("/run/secrets/vast-api-key")
        if not secret_path.is_file():
            raise OperationError("Vast API key is unavailable")
        environment["VAST_API_KEY"] = secret_path.read_text(encoding="utf-8").strip()
    arguments = [
        "uvx",
        "--offline",
        "--from",
        "vastai==1.4.1",
        "python3",
        str(context.path("transport/control/vast_private_create.py")),
        str(offer["id"]),
        context.image,
        context.label,
        str(marker),
        str(outcome),
    ]
    if context.command_workload:
        arguments += ["--disk-gb", str(context.limit("disk_gb"))]
        if context.config.get("onstart"):
            arguments += ["--onstart-cmd", context.config["onstart"]]
        if "local_volume" in context.config:
            volume = context.config["local_volume"]
            arguments += ["--local-volume-id", str(volume["id"])]
    try:
        subprocess.run(
            arguments,
            input=docker_pat.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            env=environment,
        )
    except OSError as error:
        raise OperationError(f"could not execute secret-safe Vast create: {error}") from error
    finally:
        del docker_pat
        environment.pop("VAST_API_KEY", None)


def recover_or_freeze_create(
    context: Context, offer: dict[str, object]
) -> dict[str, object] | None:
    result_path = context.path("launch/create-result.json")
    if result_path.exists():
        result = read_json(result_path)
        if not isinstance(result, dict):
            raise OperationError("create result is invalid")
        calibration_package.created_instance_id(result)
        return result
    marker = context.path("launch/create-request-attempted.txt")
    outcome_path = context.path("launch/create-api-outcome.json")
    if not marker.exists():
        return None
    outcome = read_json(outcome_path) if outcome_path.exists() else None
    if isinstance(outcome, dict) and outcome.get("outcome") == "success":
        try:
            frozen = calibration_package.freeze_create_result(outcome)
        except ValueError as error:
            raise OperationError(f"create outcome is invalid: {error}") from error
        atomic_json(result_path, frozen)
        return frozen
    attempts = context.timing_value("provider_attempts")
    interval = context.timing_value("provider_poll_seconds")
    last_complete_inventory_had_no_match = False
    for _ in range(attempts):
        try:
            rows = sanitized_live_instances()
        except OperationError:
            if interval:
                time.sleep(interval)
            continue
        matches = [row for row in rows if row.get("label") == context.label]
        if len(matches) > 1:
            raise OperationError("create recovery found duplicate live label matches")
        last_complete_inventory_had_no_match = not matches
        if matches:
            try:
                recovered = recover_create_result(
                    rows,
                    offer,
                    context.image,
                    context.label,
                    context.limit("maximum_rental_rate_micro_usd_per_hour"),
                    minimum_disk_gb=context.limit("disk_gb"),
                )
            except ValueError as error:
                raise OperationError(
                    f"live create-recovery match failed identity validation: {error}"
                ) from error
            atomic_json(result_path, recovered)
            return recovered
        if interval:
            time.sleep(interval)
    if (
        isinstance(outcome, dict)
        and outcome.get("outcome") == "definitive_rejection"
        and last_complete_inventory_had_no_match
    ):
        write_preclaim_failure(context, "provider definitively rejected create")
        return None
    raise OperationError(
        "create state is unresolved; rerun to reconcile the unique label, never create again"
    )


def ensure_create(
    context: Context, offer: dict[str, object]
) -> dict[str, object] | None:
    result = recover_or_freeze_create(context, offer)
    if result is not None or context.path("launch/preclaim-failure.log").exists():
        return result
    matches = [
        row for row in sanitized_live_instances() if row.get("label") == context.label
    ]
    if matches:
        raise OperationError(
            "live instance already uses the full-build label immediately before create"
        )
    docker_pat = docker_pat_from_tty()
    invoke_private_create(context, offer, docker_pat)
    return recover_or_freeze_create(context, offer)


def validate_instance_ownership(
    create_result: object, instance: object, expected_label: str
) -> dict[str, object]:
    """Identify our created instance without deciding whether it can run the work."""
    expected_id = calibration_package.created_instance_id(create_result)
    instance = calibration_package.instance_from_document(instance)
    if isinstance(instance.get("id"), bool) or str(instance.get("id")) != expected_id:
        raise ValueError("instance ID differs from the recorded create result")
    if not expected_label.strip() or instance.get("label") not in (expected_label, None, ""):
        raise ValueError("instance label conflicts with the recorded operation")
    return {"instance_id": expected_id, "label": instance.get("label")}


def record_instance_ownership(
    context: Context,
    create_result: dict[str, object],
    candidate: dict[str, object],
) -> None:
    instance_path = context.path("launch/instance-ownership.json")
    validation_path = context.path("launch/instance-ownership-validation.json")
    try:
        validation = validate_instance_ownership(create_result, candidate, context.label)
    except ValueError as error:
        raise OperationError(f"created Vast instance failed identity binding: {error}") from error
    if instance_path.exists():
        existing = read_json(instance_path)
        try:
            expected = validate_instance_ownership(create_result, existing, context.label)
        except ValueError as error:
            raise OperationError(
                f"recorded Vast instance ownership is invalid: {error}"
            ) from error
        if not validation_path.exists():
            atomic_json(validation_path, expected)
        elif read_json(validation_path) != expected:
            raise OperationError("recorded Vast instance ownership receipt differs")
        return
    atomic_json(instance_path, candidate)
    atomic_json(validation_path, validation)


def freeze_running_instance(
    context: Context,
    offer: dict[str, object],
    create_result: dict[str, object],
) -> dict[str, object]:
    instance_path = context.path("launch/instance.json")
    validation_path = context.path("launch/pre-transfer-instance-validation.json")
    if instance_path.exists():
        frozen = read_json(instance_path)
        if not isinstance(frozen, dict):
            raise OperationError("frozen instance is invalid")
    else:
        identifier = calibration_package.created_instance_id(create_result)
        attempts = context.timing_value("provider_attempts")
        interval = context.timing_value("provider_poll_seconds")
        frozen = None
        for _ in range(attempts):
            try:
                raw = vast_json(["show", "instance", identifier, "--raw"])
            except OperationError:
                # Keep the successful controller's bounded provider retry.
                if interval:
                    time.sleep(interval)
                continue
            if raw is None or (isinstance(raw, dict) and "instances" in raw and raw["instances"] is None):
                if interval:
                    time.sleep(interval)
                continue
            try:
                candidate = calibration_package.freeze_instance_record(create_result, raw)
            except ValueError as error:
                raise OperationError(f"created Vast instance identity is invalid: {error}") from error
            # Validation failures must reach run's cleanup path, not disappear
            # into the readiness wait. Loading/created states still get time.
            record_instance_ownership(context, create_result, candidate)
            if candidate.get("actual_status") == "running":
                frozen = candidate
                break
            if interval:
                time.sleep(interval)
        if frozen is None:
            raise OperationError("created Vast instance did not become running")
        atomic_json(instance_path, frozen)
    try:
        validation = validate_instance_against_offer(
            offer,
            create_result,
            frozen,
            context.image,
            context.limit("maximum_rental_rate_micro_usd_per_hour"),
            expected_label=context.label,
            minimum_disk_gb=context.limit("disk_gb"),
        )
    except ValueError as error:
        raise OperationError(f"created Vast instance failed identity binding: {error}") from error
    if validation_path.exists():
        if read_json(validation_path) != validation:
            raise OperationError("frozen instance validation receipt differs")
    else:
        atomic_json(validation_path, validation)
    return frozen


def parse_vast_ssh_target(output: bytes) -> list[str]:
    try:
        target = shlex.split(output.decode("utf-8", errors="strict").strip())
    except (UnicodeDecodeError, ValueError) as error:
        raise OperationError("Vast SSH URL is invalid") from error
    if not target or any("\n" in value or "\r" in value for value in target):
        raise OperationError("Vast SSH URL is invalid")
    if len(target) == 3:
        host, option, port = target
        if option != "-p" or not port.isdecimal() or not host.startswith("root@"):
            raise OperationError("Vast SSH URL is invalid")
        return ["-p", port, host]
    if len(target) == 1:
        try:
            parsed = urllib.parse.urlparse(target[0])
            valid = (
                parsed.scheme == "ssh"
                and parsed.username == "root"
                and bool(parsed.hostname)
                and parsed.port is not None
                and parsed.path in ("", "/")
            )
        except ValueError:
            valid = False
        if valid:
            return target
    raise OperationError("Vast SSH URL is invalid")


def resolve_ssh_target(
    context: Context, instance_id: str, raw_instance: object | None = None,
) -> list[str]:
    if not context.command_workload or not context.config.get("ssh_direct", False):
        return parse_vast_ssh_target(completed_process(["vastai", "ssh-url", instance_id]).stdout)
    if raw_instance is None:
        raw_instance = vast_json(["show", "instance", instance_id, "--raw"])
    try:
        instance = calibration_package.instance_from_document(raw_instance)
        calibration_package.freeze_instance_record(
            {"success": True, "new_contract": instance_id}, instance)
        host = instance.get("public_ipaddr")
        if not isinstance(host, str):
            raise ValueError("public_ipaddr is missing")
        address = ipaddress.ip_address(host)
        if address.is_unspecified or address.is_multicast:
            raise ValueError("public_ipaddr is not a unicast address")
        ports = instance.get("ports")
        bindings = ports.get("22/tcp") if isinstance(ports, dict) else None
        if not isinstance(bindings, list) or not bindings:
            raise ValueError("TCP port 22 has no published mapping yet")
        mapped = set()
        for binding in bindings:
            if not isinstance(binding, dict):
                raise ValueError("invalid TCP port 22 mapping")
            bind_host = binding.get("HostIp")
            if bind_host:
                bind_address = ipaddress.ip_address(bind_host)
                if bind_address.version != address.version:
                    continue
            port = binding.get("HostPort")
            if (isinstance(port, bool) or not isinstance(port, (str, int))
                    or not str(port).isdecimal() or not 1 <= int(port) <= 65535):
                raise ValueError("invalid TCP port 22 host port")
            mapped.add(int(port))
        if len(mapped) != 1:
            raise ValueError("TCP port 22 needs one unambiguous host port")
    except ValueError as error:
        raise OperationError(f"Vast direct SSH endpoint is invalid: {error}") from error
    return ["-p", str(mapped.pop()), f"root@{address}"]


def ssh_arguments(
    context: Context, private_key: Path, target: list[str]
) -> list[str]:
    return [
        *ssh_options(context, private_key),
        *target,
    ]


def ssh_options(context: Context, private_key: Path) -> list[str]:
    return [
        "ssh",
        "-F",
        "/dev/null",
        "-i",
        str(private_key),
        "-o",
        "BatchMode=yes",
        "-o",
        "IdentitiesOnly=yes",
        "-o",
        "ConnectTimeout=15",
        "-o",
        "ConnectionAttempts=2",
        "-o",
        "ServerAliveInterval=15",
        "-o",
        "ServerAliveCountMax=3",
        "-o",
        "StrictHostKeyChecking=accept-new",
        "-o",
        f"UserKnownHostsFile={context.path('launch/ssh/known_hosts')}",
    ]


def verify_local_ssh(context: Context) -> None:
    # -G parses the same options used for access/transfers without connecting.
    # The key is created after rental; this checks configuration, not authentication.
    private_key = context.path("launch/ssh/id_ed25519")
    try:
        completed_process(ssh_arguments(context, private_key, ["-G", "root@127.0.0.1"]))
    except OperationError as error:
        raise OperationError(f"local SSH configuration check failed: {error}") from error


def stream_processes(
    producer_arguments: list[str],
    consumer_arguments: list[str],
    description: str,
    timeout_seconds: int,
) -> None:
    if timeout_seconds <= 0:
        raise OperationError("stream timeout must be positive")
    producer: subprocess.Popen[bytes] | None = None
    consumer: subprocess.Popen[bytes] | None = None
    previous_handlers: dict[signal.Signals, object] = {}
    completed = False

    def interrupted(signum: int, _frame: object) -> NoReturn:
        raise InterruptedError(f"signal {signum}")

    def terminate(process: subprocess.Popen[bytes] | None) -> None:
        if process is None or process.poll() is not None:
            return
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=5)
            return
        except subprocess.TimeoutExpired:
            pass
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
        with contextlib.suppress(subprocess.TimeoutExpired):
            process.wait(timeout=5)

    with (
        tempfile.TemporaryFile() as producer_error,
        tempfile.TemporaryFile() as consumer_output,
        tempfile.TemporaryFile() as consumer_error,
    ):
        try:
            for handled_signal in (signal.SIGINT, signal.SIGTERM):
                previous_handlers[handled_signal] = signal.getsignal(handled_signal)
                signal.signal(handled_signal, interrupted)
            producer = subprocess.Popen(
                producer_arguments,
                stdout=subprocess.PIPE,
                stderr=producer_error,
                start_new_session=True,
            )
            assert producer.stdout is not None
            consumer = subprocess.Popen(
                consumer_arguments,
                stdin=producer.stdout,
                stdout=consumer_output,
                stderr=consumer_error,
                start_new_session=True,
            )
            producer.stdout.close()
            deadline = time.monotonic() + timeout_seconds
            consumer_status = consumer.wait(
                timeout=max(0.001, deadline - time.monotonic())
            )
            producer_status = producer.wait(
                timeout=max(0.001, deadline - time.monotonic())
            )
            completed = True
        except InterruptedError as error:
            raise OperationError(f"{description} was interrupted") from error
        except OSError as error:
            command = (
                producer_arguments[0]
                if producer is None
                else consumer_arguments[0]
            )
            raise OperationError(f"could not execute {command}: {error}") from error
        except subprocess.TimeoutExpired as error:
            raise OperationError(
                f"{description} exceeded its {timeout_seconds}-second limit"
            ) from error
        finally:
            if not completed:
                terminate(consumer)
                terminate(producer)
            for handled_signal, previous in previous_handlers.items():
                signal.signal(handled_signal, previous)
        if producer_status == 0 and consumer_status == 0:
            return
        producer_error.seek(0)
        consumer_error.seek(0)
        details = b"\n".join(
            value.strip()
            for value in (producer_error.read(), consumer_error.read())
            if value.strip()
        ).decode("utf-8", errors="replace")
        suffix = f": {details}" if details else ""
        raise OperationError(
            f"{description} failed with producer status {producer_status} "
            f"and consumer status {consumer_status}{suffix}"
        )


def validated_remote_directory(remote_directory: str) -> str:
    directory = remote_directory.rstrip("/")
    if (
        not directory.startswith("/workspace/oracle-full-build/")
        or any(character.isspace() for character in directory)
        or any(part in ("", ".", "..") for part in directory.split("/")[1:])
    ):
        raise OperationError("remote transfer directory is invalid")
    return directory


def tar_upload_directory(
    context: Context,
    private_key: Path,
    target: list[str],
    source: Path,
    remote_directory: str,
) -> None:
    if not source.is_dir():
        raise OperationError("tar upload source is not a directory")
    remote_directory = validated_remote_directory(remote_directory)
    completed_process(
        [
            *ssh_arguments(context, private_key, target),
            "rm",
            "-rf",
            "--",
            remote_directory,
        ]
    )
    completed_process(
        [
            *ssh_arguments(context, private_key, target),
            "mkdir",
            "-p",
            "--",
            remote_directory,
        ]
    )
    stream_processes(
        ["tar", "-C", str(source), "-cf", "-", "."],
        [
            *ssh_arguments(context, private_key, target),
            "/usr/bin/tar",
            "-C",
            remote_directory,
            "--no-same-owner",
            "-xf",
            "-",
        ],
        "tar upload",
        3_600,
    )


def tar_download_directory(
    context: Context,
    private_key: Path,
    target: list[str],
    remote_directory: str,
    destination: Path,
) -> None:
    remote_directory = validated_remote_directory(remote_directory)
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if destination.exists():
        if not destination.is_dir() or destination.is_symlink():
            raise OperationError("tar download destination is not a directory")
    else:
        destination.mkdir(mode=0o700)
    staging = destination.with_name(f".{destination.name}.tar-download")
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(mode=0o700)
    try:
        stream_processes(
            [
                *ssh_arguments(context, private_key, target),
                "/usr/bin/tar",
                "-C",
                remote_directory,
                "-cf",
                "-",
                ".",
            ],
            [
                "tar",
                "-C",
                str(staging),
                "--no-same-owner",
                "-xf",
                "-",
            ],
            "tar download",
            21_600,
        )
        try:
            for child in destination.iterdir():
                if child.is_dir() and not child.is_symlink():
                    shutil.rmtree(child)
                else:
                    child.unlink()
            for child in staging.iterdir():
                os.replace(child, destination / child.name)
            sync_directory(destination)
            sync_directory(destination.parent)
        except OSError as error:
            raise OperationError(f"could not publish tar download: {error}") from error
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def ensure_ssh(context: Context, instance_id: str) -> tuple[Path, list[str]]:
    directory = context.path("launch/ssh")
    private = directory / "id_ed25519"
    public = directory / "id_ed25519.pub"
    attached = context.path("launch/ssh-attached.json")
    delivered = context.path("launch/ssh-attach-delivered.json")
    if not private.exists():
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        completed_process(
            [
                "ssh-keygen",
                "-q",
                "-t",
                "ed25519",
                "-N",
                "",
                "-C",
                f"crec-72-{instance_id}",
                "-f",
                str(private),
            ]
        )
    if not private.is_file() or not public.is_file():
        raise OperationError("operation SSH keypair is incomplete")
    os.chmod(private, 0o600)
    key_sha256 = sha256_file(public)
    expected_receipt = {
        "schema_version": 1,
        "instance_id": instance_id,
        "public_key_sha256": key_sha256,
    }
    if attached.exists():
        receipt = read_json(attached)
        if not isinstance(receipt, dict) or receipt.get("instance_id") != instance_id:
            raise OperationError("SSH attachment receipt is bound to another instance")
        if receipt.get("public_key_sha256") != key_sha256:
            raise OperationError("SSH attachment receipt is bound to another key")
    if delivered.exists():
        receipt = read_json(delivered)
        if not isinstance(receipt, dict) or any(
            receipt.get(field) != value
            for field, value in expected_receipt.items()
        ):
            raise OperationError("SSH attach delivery receipt differs")
    elif not attached.exists():
        attempts = context.timing_value("provider_attempts")
        interval = context.timing_value("provider_poll_seconds")
        for attempt in range(attempts):
            try:
                result = completed_process(
                    [
                        "vastai",
                        "attach",
                        "ssh",
                        instance_id,
                        str(public),
                        "--raw",
                    ]
                )
                break
            except OperationError as error:
                if attempt + 1 == attempts:
                    raise RemoteAccessUnavailable(
                        f"could not attach the operation SSH key: {error}"
                    ) from error
                if interval:
                    time.sleep(interval)
        atomic_json(
            delivered,
            {
                **expected_receipt,
                "command_exit_status": 0,
                "stdout_bytes": len(result.stdout),
                "stdout_sha256": hashlib.sha256(result.stdout).hexdigest(),
                "delivered_at_utc": utc_text(),
            },
        )
    attempts = context.timing_value("provider_attempts")
    interval = context.timing_value("provider_poll_seconds")
    for attempt in range(attempts):
        try:
            target = resolve_ssh_target(context, instance_id)
            if not attached.exists():
                completed_process([*ssh_arguments(context, private, target), "true"])
                atomic_json(
                    attached,
                    {
                        **expected_receipt,
                        "attached_at_utc": utc_text(),
                    },
                )
            return private, target
        except OperationError as error:
            if attempt + 1 == attempts:
                raise RemoteAccessUnavailable(
                    f"could not resolve the operation SSH endpoint: {error}"
                ) from error
            if interval:
                time.sleep(interval)
    raise AssertionError("provider retry loop did not return")


def remote_arguments(
    context: Context,
    private_key: Path,
    target: list[str],
    operation: str,
    *arguments: str,
) -> list[str]:
    return [
        *ssh_arguments(context, private_key, target),
        context.remote_python,
        "/workspace/oracle-full-build/transport/control/vast_full_build.py",
        "--root",
        "/workspace/oracle-full-build",
        "--config",
        "/workspace/oracle-full-build/launch/operation-contract.json",
        operation,
        *arguments,
    ]


def remote_json(
    context: Context,
    private_key: Path,
    target: list[str],
    operation: str,
    *arguments: str,
) -> object:
    return command_json(
        remote_arguments(context, private_key, target, operation, *(shlex.quote(value) for value in arguments))
    )


def ensure_remote_receipts(
    context: Context,
    plan: dict[str, object],
    reservation: dict[str, object],
    create_result: dict[str, object],
    instance: dict[str, object],
) -> Path:
    remote = context.path("launch/remote")
    remote.mkdir(parents=True, exist_ok=True, mode=0o700)
    documents = {
        "approval-plan.json": plan,
        "approval.json": read_json(context.path("launch/approval.json")),
        "offer.json": read_json(context.path("launch/offer.json")),
        "full-build-reservation.json": reservation,
        "create-result.json": create_result,
        "instance.json": instance,
        "pre-transfer-instance-validation.json": read_json(
            context.path("launch/pre-transfer-instance-validation.json")
        ),
    }
    for name, document in documents.items():
        atomic_json(remote / name, document)
    atomic_copy(context.config_path, remote / "operation-contract.json")
    atomic_copy(
        context.path("launch/reserved-budget-ledger.json"),
        remote / "reserved-budget-ledger.json",
    )
    return remote


def retrieve_preparation_failure(
    context: Context,
    instance_id: str,
    private_key: Path,
    target: list[str],
    response: dict[str, object],
) -> None:
    receipt = context.path("launch/preparation-failure-retrieval.json")
    if receipt.is_file():
        return
    destination = context.path("launch/preparation-failure")
    errors: list[str] = []
    attempts = min(3, context.timing_value("preparation_attempts"))
    for attempt_number in range(1, attempts + 1):
        staging = context.path(
            f"launch/preparation-failure.next-{attempt_number:03d}"
        )
        with contextlib.suppress(FileNotFoundError):
            shutil.rmtree(staging)
        staging.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            tar_download_directory(
                context,
                private_key,
                target,
                "/workspace/oracle-full-build/preparation-attempts/",
                staging,
            )
            records = response.get("evidence_files")
            if records is not None:
                verified = validate_file_records(staging, records)
            else:
                logs = list(staging.rglob("preparation.log"))
                exits = list(staging.rglob("preparation.exit"))
                if not logs or not exits:
                    raise OperationError(
                        "retrieved preparation failure lacks its log or terminal receipt"
                    )
                verified = tree_file_records(staging, set())
            if destination.exists():
                shutil.rmtree(destination)
            os.replace(staging, destination)
            sync_directory(destination.parent)
            atomic_json(
                receipt,
                {
                    "schema_version": 1,
                    "instance_id": instance_id,
                    "attempts": attempt_number,
                    "files": verified,
                    "retrieved_at_utc": utc_text(),
                },
            )
            return
        except OperationError as error:
            errors.append(str(error))
            with contextlib.suppress(FileNotFoundError):
                shutil.rmtree(staging)
            if attempt_number < attempts:
                interval = context.timing_value("provider_poll_seconds")
                if interval:
                    time.sleep(interval)
    irretrievable = context.path(
        "launch/preparation-failure-irretrievable.json"
    )
    if not irretrievable.exists():
        atomic_json(
            irretrievable,
            {
                "schema_version": 1,
                "instance_id": instance_id,
                "attempts": attempts,
                "errors": errors,
                "remote_evidence_files": response.get("evidence_files"),
                "recorded_at_utc": utc_text(),
            },
        )


def ensure_remote_volume(context: Context, private_key: Path, target: list[str],
                         remote_receipts: Path, instance_id: str) -> None:
    receipt = context.path("launch/volume-prepared.json")
    digest = sha256_file(context.config_path)
    if receipt.exists():
        saved = read_json(receipt)
        if saved.get("instance_id") != instance_id or saved.get("contract_sha256") != digest:
            raise OperationError("volume receipt differs from this instance or contract")
        return
    root = "/workspace/oracle-full-build"
    completed_process([*ssh_arguments(context, private_key, target), "mountpoint", "-q", "/workspace"])
    staging = root + "/replacements/" + digest
    tar_upload_directory(context, private_key, target, context.path("transport"), staging + "/transport/")
    tar_upload_directory(context, private_key, target, remote_receipts, staging + "/launch/")
    result = command_json([*ssh_arguments(context, private_key, target), context.remote_python,
        staging + "/transport/control/vast_full_build.py", "--root", staging,
        "--config", staging + "/launch/operation-contract.json", "_remote-volume-prepare"])
    if not isinstance(result, dict) or result.get("prepared") is not True:
        raise OperationError("persistent volume preparation was not acknowledged")
    atomic_json(receipt, {"instance_id": instance_id, "contract_sha256": digest, "remote_receipt": result})


def remote_volume_prepare(context: Context, volume_root: Path) -> dict[str, object]:
    """Keep saved work at its original paths; retire only prior control receipts."""
    if "local_volume" not in context.config:
        raise OperationError("volume preparation requires a frozen local volume")
    completed_process(["mountpoint", "-q", str(volume_root.parent)])
    verify_reviewed_artifacts(context, require_local_execution_package=False)
    identity = volume_root / "volume-identity.json"
    if identity.exists():
        if read_json(identity) != context.config["local_volume"]:
            raise OperationError("mounted volume identity differs from the frozen volume")
    else:
        atomic_json(identity, context.config["local_volume"])
    digest = sha256_file(context.config_path)
    receipt = volume_root / "volume-receipts" / (digest + ".json")
    with file_lock(volume_root / "volume.lock", blocking=False):
        if receipt.exists():
            return read_json(receipt)
        prior_path = volume_root / "launch/operation-contract.json"
        recovery = context.config.get("volume_recovery")
        if recovery is None:
            if prior_path.exists() or (volume_root / "work").exists():
                raise OperationError("existing volume work requires an explicit verified replacement")
            result = {"prepared": True, "recovered": False, "contract_sha256": digest}
        else:
            archive = volume_root / "recoveries" / recovery["previous_contract_sha256"]
            intent = archive / "replacement-intent.json"
            reuse_work = recovery.get("reuse_work", True)
            work = volume_root / "work"
            if not work.exists() and not reuse_work:
                work = archive / "work"
            with file_lock(work / "full-build-start.lock", blocking=False), \
                    file_lock(work / "full-build.lock", blocking=False):
                if intent.exists():
                    if read_json(intent) != {"contract_sha256": digest, "recovery": recovery}:
                        raise OperationError("volume replacement intent differs from this contract")
                    # Delivery can resume after interruption between directory renames.
                    validate_file_records(work, recovery["work_files"])
                else:
                    verify_sha(prior_path, recovery["previous_contract_sha256"], "previous volume contract")
                    validate_file_records(work, recovery["work_files"])
                    atomic_json(intent, {"contract_sha256": digest, "recovery": recovery})
                for relative in ("launch", "transport", "package", "preparation-attempts",
                                 "work/retrieval-manifest.json" if reuse_work else "work"):
                    source = volume_root / relative
                    destination = archive / Path(relative).name
                    if source.exists():
                        if destination.exists():
                            raise OperationError("volume recovery archive already contains " + relative)
                        os.rename(source, destination)
                        sync_directory(destination.parent)
                result = {"prepared": True, "recovered": True, "contract_sha256": digest,
                          "reused_work": reuse_work,
                          "previous_instance_id": recovery["previous_instance_id"],
                          "archive": str(archive.relative_to(volume_root))}
        atomic_json(receipt, result)
        return result


def ensure_remote_prepared(
    context: Context,
    instance_id: str,
    private_key: Path,
    target: list[str],
    remote_receipts: Path,
) -> bool:
    local_receipt = context.path("launch/remote-prepared.json")
    if local_receipt.exists():
        return True
    if "local_volume" in context.config:
        ensure_remote_volume(context, private_key, target, remote_receipts, instance_id)
    transfer_receipt = context.path("launch/remote-transfer-verified.json")
    if transfer_receipt.exists():
        transfer = read_json(transfer_receipt)
        if (
            not isinstance(transfer, dict)
            or transfer.get("instance_id") != instance_id
            or transfer.get("transport_manifest_sha256")
            != context.pin("transport_manifest_sha256")
            or transfer.get("operation_config_sha256")
            != sha256_file(context.config_path)
        ):
            raise OperationError("remote transfer receipt is invalid")
    else:
        completed_process(
            [
                *ssh_arguments(context, private_key, target),
                "/usr/bin/tar",
                "--version",
            ]
        )
        verify_reviewed_artifacts(context)
        transfer: object = None
        for copy_attempt in range(2):
            try:
                tar_upload_directory(
                    context,
                    private_key,
                    target,
                    context.path("transport"),
                    "/workspace/oracle-full-build/transport/",
                )
                tar_upload_directory(
                    context,
                    private_key,
                    target,
                    remote_receipts,
                    "/workspace/oracle-full-build/launch/",
                )
                transfer = remote_json(
                    context, private_key, target, "_remote-verify-transfer"
                )
                if not isinstance(transfer, dict) or transfer.get("verified") is not True:
                    raise OperationError("remote transfer verification was not acknowledged")
                break
            except OperationError:
                if copy_attempt == 1:
                    return False
                interval = context.timing_value("provider_poll_seconds")
                if interval:
                    time.sleep(interval)
        assert isinstance(transfer, dict)
        atomic_json(
            transfer_receipt,
            {
                "schema_version": 1,
                "instance_id": instance_id,
                "transport_manifest_sha256": context.pin(
                    "transport_manifest_sha256"
                ),
                "operation_config_sha256": sha256_file(context.config_path),
                "remote_receipt": transfer,
                "verified_by_remote_at_utc": utc_text(),
            },
        )
    attempts = context.timing_value("preparation_attempts")
    interval = context.timing_value("preparation_poll_seconds")
    response: object = None
    for _ in range(attempts):
        try:
            response = remote_json(context, private_key, target, "_remote-prepare")
        except OperationError:
            return False
        if isinstance(response, dict) and response.get("prepared") is True:
            break
        if isinstance(response, dict) and response.get("state") == "failed":
            retrieve_preparation_failure(
                context, instance_id, private_key, target, response
            )
            raise RemotePreparationFailed("remote preparation failed")
        if interval:
            time.sleep(interval)
    else:
        return False
    atomic_json(
        local_receipt,
        {
            "schema_version": 1,
            "instance_id": instance_id,
            "remote_receipt": response,
            "recorded_at_utc": utc_text(),
        },
    )
    return True


def cost_record_from_instance(
    context: Context, instance_id: str, raw: object
) -> dict[str, object]:
    """Estimate spending from approved allowances, not unverified live counters.

    Vast's duration is elapsed time, including setup. Charging all of it at the
    approved maximum hourly rate and adding the entire transfer allowance is a
    budget estimate, not an observed bill or an enforced traffic/charge cap.
    Posted charges remain the responsibility of ensure_final_charge.
    """
    try:
        row = calibration_package.instance_from_document(raw)
        if str(row.get("id")) != instance_id:
            raise ValueError("instance ID changed")
        duration = calibration_package.require_number(row.get("duration"), "instance.duration")
        rate = calibration_package.require_number(row.get("dph_total"), "instance.dph_total")
        maximum_rate = context.limit("maximum_rental_rate_micro_usd_per_hour")
        if duration < 0:
            raise ValueError("instance.duration is negative")
        if rate <= 0 or rate * 1_000_000 > maximum_rate:
            raise ValueError("instance.dph_total is nonpositive or exceeds the approved rate")
        rental_micro = int(
            (duration * maximum_rate / Decimal(3600)).to_integral_value(rounding=ROUND_CEILING)
        )
    except (KeyError, ValueError, ArithmeticError) as error:
        raise OperationError(f"live provider cost estimate input is invalid: {error}") from error
    transfer_micro = required_nonnegative_int(context.limits, "transfer_allowance_micro_usd")
    return {
        "schema_version": 2,
        "instance_id": instance_id,
        "observed_at_utc": utc_text(),
        "duration_seconds": int(duration),
        "maximum_hourly_rate_micro_usd": maximum_rate,
        "estimated_rental_micro_usd": rental_micro,
        "transfer_allowance_micro_usd": transfer_micro,
        "estimated_total_micro_usd": rental_micro + transfer_micro,
        "provider_reported_total_micro_usd": None,
    }


def live_cost_record(context: Context, instance_id: str) -> dict[str, object]:
    return cost_record_from_instance(
        context,
        instance_id,
        vast_json(["show", "instance", instance_id, "--raw"]),
    )


def next_attempt_id(context: Context) -> str:
    directory = context.path("launch/worker-invocations")
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    existing = sorted(
        int(path.stem)
        for path in directory.glob("[0-9][0-9][0-9].json")
        if path.stem.isdecimal()
    )
    recovery = context.config.get("volume_recovery", {})
    previous = int(recovery.get("previous_attempt", "000")) if recovery.get("reuse_work", True) else 0
    value = (existing[-1] if existing else previous) + 1
    if value > 999:
        raise OperationError("worker attempt namespace is exhausted")
    return f"{value:03d}"


def last_attempt_id(context: Context) -> str | None:
    directory = context.path("launch/worker-invocations")
    if not directory.is_dir():
        return None
    values = sorted(path.stem for path in directory.glob("[0-9][0-9][0-9].json"))
    return values[-1] if values else None


def record_pre_worker_cost(
    context: Context, instance_id: str, attempt_id: str, reason: str
) -> dict[str, object]:
    directory = context.path("launch/pre-worker-cost-observations")
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    existing = sorted(directory.glob(f"{attempt_id}-*.json"))
    path = directory / f"{attempt_id}-{len(existing) + 1:03d}.json"
    cost = live_cost_record(context, instance_id)
    cost["attempt_id"] = attempt_id
    cost["reason"] = reason
    atomic_json(path, cost)
    estimated = cost.get("estimated_total_micro_usd")
    if isinstance(estimated, bool) or not isinstance(estimated, int):
        raise OperationError("pre-worker cost receipt is invalid")
    if estimated > context.limit("setup_cost_micro_usd"):
        raise OperationError("worker start refused because the setup cost estimate exceeded its gate")
    return cost


def publish_worker_acknowledgement(
    context: Context,
    instance_id: str,
    attempt_id: str,
    response: dict[str, object],
) -> None:
    atomic_json(
        context.path("launch/worker-started.json"),
        {
            "schema_version": 1,
            "attempt_id": attempt_id,
            "instance_id": instance_id,
            "remote_receipt": response,
            "recorded_at_utc": utc_text(),
        },
    )


def ensure_worker_started(
    context: Context,
    instance_id: str,
    private_key: Path,
    target: list[str],
) -> str:
    acknowledged = context.path("launch/worker-started.json")
    if acknowledged.exists():
        document = read_json(acknowledged)
        if not isinstance(document, dict) or not isinstance(
            document.get("attempt_id"), str
        ):
            raise OperationError("worker-start receipt is invalid")
        return document["attempt_id"]
    invocation_dir = context.path("launch/worker-invocations")
    invocation_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    unresolved = [
        path.stem
        for path in sorted(invocation_dir.glob("[0-9][0-9][0-9].json"))
        if not context.path(f"launch/worker-invocations/{path.stem}.terminal.json").exists()
    ]
    if len(unresolved) > 1:
        raise OperationError("more than one worker invocation is unresolved")
    if unresolved:
        attempt_id = unresolved[0]
        status = worker_status(context, private_key, target, attempt_id)
        if (
            status.get("execution_committed") is True
            and status["state"] in ("running", "starting", "orphaned")
        ) or (
            status["state"] == "terminal" and status.get("kind") != "start.exit"
        ):
            publish_worker_acknowledgement(
                context, instance_id, attempt_id, status
            )
            return attempt_id
        if (
            status["state"] == "orphaned"
            and status.get("execution_committed") is not True
        ):
            response = remote_json(
                context,
                private_key,
                target,
                "_remote-abort-unstarted",
                "--attempt",
                attempt_id,
            )
            if not isinstance(response, dict) or response.get("kind") != "start.exit":
                raise OperationError("unstarted orphan could not be terminalized")
            atomic_json(
                context.path(
                    f"launch/worker-invocations/{attempt_id}.terminal.json"
                ),
                response,
            )
            raise OperationError(
                f"worker attempt {attempt_id} ended before execution; rerun for a fresh attempt"
            )
        if status["state"] == "terminal":
            atomic_json(
                context.path(
                    f"launch/worker-invocations/{attempt_id}.terminal.json"
                ),
                status,
            )
            raise OperationError(
                f"worker attempt {attempt_id} ended before execution; rerun for a fresh attempt"
            )
        if status["state"] != "absent":
            raise OperationError("unresolved worker invocation has an invalid remote state")
        pending = read_json(context.path(f"launch/worker-invocations/{attempt_id}.json"))
        if "resume_from" not in pending:
            record_pre_worker_cost(
                context, instance_id, attempt_id, "redeliver-unstarted-invocation"
            )
    else:
        attempt_id = next_attempt_id(context)
        record_pre_worker_cost(context, instance_id, attempt_id, "initial-invocation")
    invocation = context.path(f"launch/worker-invocations/{attempt_id}.json")
    if invocation.exists():
        existing = read_json(invocation)
        if not isinstance(existing, dict) or existing.get("instance_id") != instance_id:
            raise OperationError("worker invocation receipt is invalid")
    else:
        atomic_json(
            invocation,
            {
                "schema_version": 1,
                "attempt_id": attempt_id,
                "instance_id": instance_id,
                "invoked_at_utc": utc_text(),
            },
        )
    continuation_args = []
    saved_invocation = read_json(invocation)
    recovery = context.config.get("volume_recovery")
    if recovery is not None and not recovery.get("reuse_work", True):
        recovery = None
    if recovery is not None and "resume_from" not in saved_invocation:
        saved_invocation.update(resume_from=recovery["previous_attempt"],
            reason="Continue the identical workload after verified volume-backed instance replacement")
        atomic_json(invocation, saved_invocation, replace=True)
    if recovery is not None and saved_invocation.get("resume_from") == recovery["previous_attempt"]:
        prepared = context.path(f"launch/worker-invocations/{attempt_id}.prepared.json")
        if not prepared.exists():
            volume = read_json(context.path("launch/volume-prepared.json"))
            if volume.get("instance_id") != instance_id or not volume.get("remote_receipt", {}).get("recovered"):
                raise OperationError("volume continuation has not verified its saved work")
            atomic_json(prepared, {"volume_receipt_sha256": sha256_file(context.path("launch/volume-prepared.json"))})
    if "resume_from" in saved_invocation:
        if not context.path(f"launch/worker-invocations/{attempt_id}.prepared.json").is_file():
            raise OperationError("continuation retrieval archive is not prepared; rerun resume")
        continuation_args = ["--resume-from", saved_invocation["resume_from"],
                             "--reason", saved_invocation["reason"]]
    try:
        response = remote_json(
            context,
            private_key,
            target,
            "_remote-worker",
            "--attempt",
            attempt_id,
            *continuation_args,
        )
    except OperationError as error:
        raise OperationError(
            f"worker start delivery is unresolved for attempt {attempt_id}; "
            "rerun to reconcile the same attempt"
        ) from error
    if not isinstance(response, dict):
        raise OperationError("remote worker start was not acknowledged")
    if response.get("state") == "terminal" and response.get("kind") != "start.exit":
        publish_worker_acknowledgement(context, instance_id, attempt_id, response)
        return attempt_id
    if response.get("acknowledged") is not True:
        if response.get("state") in ("not_started", "terminal"):
            atomic_json(
                context.path(
                    f"launch/worker-invocations/{attempt_id}.terminal.json"
                ),
                response,
            )
        raise OperationError("remote worker start was not acknowledged")
    publish_worker_acknowledgement(context, instance_id, attempt_id, response)
    return attempt_id


def parse_attempt_id(value: str) -> str:
    if len(value) != 3 or not value.isdecimal():
        raise OperationError("worker attempt must be exactly three digits")
    return value


def read_exit_status(path: Path, *, allow_zero: bool = True) -> int:
    try:
        value = int(path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError) as error:
        raise OperationError(f"terminal receipt is invalid: {path}") from error
    if value < 0 or value > 255 or (not allow_zero and value == 0):
        raise OperationError(f"terminal receipt is invalid: {path}")
    return value


def read_pid(path: Path) -> int | None:
    if not path.is_file():
        return None
    try:
        value = int(path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError) as error:
        raise OperationError(f"PID receipt is invalid: {path}") from error
    if value <= 1:
        raise OperationError(f"PID receipt is invalid: {path}")
    return value


def process_alive(identifier: int | None) -> bool:
    if identifier is None:
        return False
    try:
        os.kill(identifier, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


@contextlib.contextmanager
def file_lock(path: Path, *, blocking: bool) -> Iterator[BinaryIO]:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor = path.open("a+b")
    flags = fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB)
    try:
        try:
            fcntl.flock(descriptor.fileno(), flags)
        except BlockingIOError as error:
            raise OperationError(f"lock is held: {path}") from error
        yield descriptor
    finally:
        descriptor.close()


def terminal_state(attempt: Path) -> dict[str, object] | None:
    records: list[dict[str, object]] = []
    full_exit = attempt / "full-build.exit"
    start_exit = attempt / "start.exit"
    orphaned = attempt / "full-build.orphaned"
    if full_exit.is_file():
        records.append({"kind": "full-build.exit", "exit_status": read_exit_status(full_exit)})
    if start_exit.is_file():
        if (attempt / "full-build.started").is_file() or (
            attempt / "controller.pid"
        ).is_file():
            raise OperationError(
                "worker attempt records a safe-start failure after execution commitment"
            )
        records.append(
            {
                "kind": "start.exit",
                "exit_status": read_exit_status(start_exit, allow_zero=False),
            }
        )
    if orphaned.is_file():
        if not orphaned.read_text(encoding="utf-8").strip():
            raise OperationError("orphan terminal receipt is empty")
        records.append({"kind": "full-build.orphaned"})
    if len(records) > 1:
        raise OperationError("worker attempt has conflicting terminal receipts")
    return records[0] if records else None


def attempt_execution_committed(attempt: Path) -> bool:
    return (attempt / "full-build.started").is_file() or (
        attempt / "controller.pid"
    ).is_file()


def remote_attempt_status(context: Context, attempt_id: str) -> dict[str, object]:
    attempt_id = parse_attempt_id(attempt_id)
    attempt = context.path(f"work/full-build-attempts/{attempt_id}")
    if not attempt.is_dir():
        return {"state": "absent", "attempt_id": attempt_id}
    # Controller exit is not proof that its independently running children
    # stopped writing. They inherit this lock until their own process exits.
    worker_lock = context.path("work/full-build.lock")
    worker_lock_held = False
    if worker_lock.exists():
        with worker_lock.open("rb") as descriptor:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                worker_lock_held = True
            else:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
    terminal = terminal_state(attempt)
    if terminal is not None and not worker_lock_held:
        return {"state": "terminal", "attempt_id": attempt_id, **terminal}
    started = (attempt / "full-build.started").is_file()
    supervisor = read_pid(attempt / "full-build.pid")
    controller = read_pid(attempt / "controller.pid")
    supervisor_alive = process_alive(supervisor)
    controller_alive = process_alive(controller)
    if started and (controller_alive or worker_lock_held):
        state = "running"
    elif supervisor_alive or controller_alive or worker_lock_held:
        state = "starting"
    else:
        state = "orphaned"
    return {
        "state": state,
        "attempt_id": attempt_id,
        "started": started,
        "execution_committed": attempt_execution_committed(attempt),
        "supervisor_pid": supervisor,
        "supervisor_alive": supervisor_alive,
        "controller_pid": controller,
        "controller_alive": controller_alive,
        "worker_lock_held": worker_lock_held,
    }


def remote_status_report(context: Context, attempt_id: str) -> dict[str, object]:
    result = remote_attempt_status(context, attempt_id)
    result.update(hardware_status(context))
    if context.command_workload:
        command = context.config["workload"].get("status_command")
        if command:
            try:
                work = context.path("work")
                result["progress"] = json.loads(subprocess.run(command, cwd=work if work.exists() else context.root,
                    env={**os.environ, **context.config["workload"].get("environment", {})},
                    capture_output=True, check=True, timeout=30).stdout)
            except (subprocess.SubprocessError, OSError, ValueError) as error:
                result["progress"] = {"error": str(error)}
        return result
    representation = context.path("work/representation")
    progress: dict[str, object] = {
        "completed_rows": 0,
        "total_rows": required_positive_int(context.expected, "total_rows"),
        "completed_shards": 0,
        "total_shards": required_positive_int(context.expected, "completed_shards"),
        "reused_checkpoint_rows": 0,
        "completed_new_rows": 0,
        "completed_new_shards": 0,
        "newest_new_shard_age_seconds": None,
    }
    shard_files = sorted(
        path
        for path in representation.glob("shards/[0-9][0-9][0-9][0-9][0-9][0-9]/manifest.json")
        if path.is_file()
    )
    if shard_files:
        build_config = read_json(
            context.path("package/run/full-build-config.json")
        )
        if not isinstance(build_config, dict):
            raise OperationError("full-build config is invalid while reading progress")
        shard_rows = required_positive_int(build_config, "shard_rows")
        total_rows = required_positive_int(context.expected, "total_rows")
        total_shards = required_positive_int(context.expected, "completed_shards")
        record_bytes, remainder = divmod(
            required_positive_int(context.expected, "final_vector_bytes"),
            total_rows,
        )
        if remainder or record_bytes <= 0:
            raise OperationError("expected vector size is not an exact row width")
        completed_rows = 0
        ordinals: set[int] = set()
        rows_by_ordinal: dict[int, int] = {}
        manifest_by_ordinal: dict[int, Path] = {}
        for manifest_path in shard_files:
            manifest = read_json(manifest_path)
            if not isinstance(manifest, dict):
                raise OperationError("remote representation shard manifest is invalid")
            ordinal = manifest.get("ordinal")
            start_row = manifest.get("start_row")
            rows = manifest.get("rows")
            if (
                isinstance(ordinal, bool)
                or not isinstance(ordinal, int)
                or ordinal < 0
                or ordinal >= total_shards
                or manifest_path.parent.name != f"{ordinal:06d}"
                or ordinal in ordinals
                or isinstance(start_row, bool)
                or not isinstance(start_row, int)
                or start_row != ordinal * shard_rows
                or isinstance(rows, bool)
                or not isinstance(rows, int)
                or rows != min(shard_rows, total_rows - start_row)
                or manifest.get("descriptor_sha256")
                != context.pin("descriptor_sha256")
                or manifest.get("build_identity_sha256")
                != required_string(
                    context.expected, "build_identity_sha256"
                )
            ):
                raise OperationError("remote representation shard identity is invalid")
            vectors = manifest.get("vectors")
            expected_vector_path = (
                f"shards/{manifest_path.parent.name}/vectors.f32le"
            )
            expected_bytes = rows * record_bytes
            vector_path = manifest_path.parent / "vectors.f32le"
            if (
                not isinstance(vectors, dict)
                or vectors.get("file") != expected_vector_path
                or vectors.get("records") != rows
                or vectors.get("bytes") != expected_bytes
                or not vector_path.is_file()
                or vector_path.stat().st_size != expected_bytes
            ):
                raise OperationError("remote representation shard vectors are invalid")
            ordinals.add(ordinal)
            rows_by_ordinal[ordinal] = rows
            manifest_by_ordinal[ordinal] = manifest_path
            completed_rows += rows
        checkpoint_ordinal = context.expected.get("checkpoint_shard_ordinal")
        reused_rows = (
            rows_by_ordinal.get(checkpoint_ordinal, 0)
            if isinstance(checkpoint_ordinal, int)
            and not isinstance(checkpoint_ordinal, bool)
            else 0
        )
        new_ordinals = [
            ordinal
            for ordinal in ordinals
            if ordinal != checkpoint_ordinal
        ]
        progress.update(
            {
                "completed_rows": completed_rows,
                "completed_shards": len(ordinals),
                "reused_checkpoint_rows": reused_rows,
                "completed_new_rows": completed_rows - reused_rows,
                "completed_new_shards": len(new_ordinals),
            }
        )
        if new_ordinals:
            newest = max(
                manifest_by_ordinal[ordinal].stat().st_mtime
                for ordinal in new_ordinals
            )
            progress["newest_new_shard_age_seconds"] = max(
                0, int(time.time() - newest)
            )
    result["progress"] = progress
    return result


def hardware_status(context: Context) -> dict[str, object]:
    usage = shutil.disk_usage(context.root)
    disk = {
        "total_bytes": usage.total,
        "used_bytes": usage.used,
        "available_bytes": usage.free,
    }
    try:
        fields = "utilization.gpu,memory.used,memory.total"
        if context.command_workload:
            fields = "index,uuid," + fields
        observation = completed_process(
            [
                "nvidia-smi",
                "--query-gpu=" + fields,
                "--format=csv,noheader,nounits",
            ]
        ).stdout.decode("utf-8", errors="strict").strip()
        rows = [line.strip() for line in observation.splitlines() if line.strip()]
        if not rows or not context.command_workload and len(rows) != 1:
            raise ValueError("expected exactly one GPU")
        devices = []
        for row in rows:
            parts = [value.strip() for value in row.split(",")]
            identity = {}
            if context.command_workload:
                if len(parts) != 5 or not parts[1].startswith("GPU-"):
                    raise ValueError("GPU identity is invalid")
                identity = {"index": int(parts[0]), "uuid": parts[1]}
                parts = parts[2:]
            values = [int(value) for value in parts]
            if len(values) != 3 or any(value < 0 for value in values):
                raise ValueError("GPU metrics are invalid")
            devices.append({**identity, "utilization_percent": values[0],
                "memory_used_bytes": values[1] * 1024 * 1024,
                "memory_total_bytes": values[2] * 1024 * 1024})
        if context.command_workload and (len({d["index"] for d in devices}) != len(devices)
                or len({d["uuid"] for d in devices}) != len(devices) or any(d["index"] < 0 for d in devices)):
            raise ValueError("GPU identities are not distinct")
        gpu: dict[str, object] = devices[0] if len(devices) == 1 else {"devices": devices}
    except (OperationError, UnicodeDecodeError, ValueError) as error:
        gpu = {"error": f"GPU observation unavailable: {error}"}
    return {"disk": disk, "gpu": gpu}


def spawn_remote_child(
    context: Context,
    operation: str,
    arguments: list[str],
    log_path: Path,
    *,
    inherited_fds: tuple[int, ...] = (),
) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    log = log_path.open("ab", buffering=0)
    try:
        child = subprocess.Popen(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "--root",
                str(context.root),
                "--config",
                str(context.config_path),
                operation,
                *arguments,
            ],
            cwd=context.root,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            close_fds=True,
            pass_fds=inherited_fds,
        )
    except OSError as error:
        raise OperationError(f"could not start {operation}: {error}") from error
    finally:
        log.close()
    return child.pid


def validate_representation(
    context: Context, response: object, *, complete: bool
) -> dict[str, object]:
    if not isinstance(response, dict) or not isinstance(response.get("manifest"), dict):
        raise OperationError("representation verification response is invalid")
    manifest = response["manifest"]
    expected = context.expected
    total_rows = required_positive_int(expected, "total_rows")
    build_identity = require_sha256(
        required_string(expected, "build_identity_sha256"),
        "expected.build_identity_sha256",
    )
    if manifest.get("complete") is not complete:
        raise OperationError("representation completeness differs from the contract")
    if manifest.get("total_rows") != total_rows:
        raise OperationError("representation total rows differ from the contract")
    if manifest.get("build_identity_sha256") != build_identity:
        raise OperationError("representation build identity differs from the contract")
    shards = manifest.get("shards")
    if not isinstance(shards, list):
        raise OperationError("representation shard list is invalid")
    if complete:
        if manifest.get("completed_rows") != total_rows:
            raise OperationError("complete representation does not contain every row")
        if len(shards) != required_positive_int(expected, "completed_shards"):
            raise OperationError("complete representation shard count differs")
        vector_bytes = 0
        for shard in shards:
            if not isinstance(shard, dict) or not isinstance(shard.get("vectors"), dict):
                raise OperationError("complete representation shard is invalid")
            value = shard["vectors"].get("bytes")
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise OperationError("complete representation vector size is invalid")
            vector_bytes += value
        if vector_bytes != required_positive_int(expected, "final_vector_bytes"):
            raise OperationError("complete representation byte count differs")
    else:
        if manifest.get("completed_rows") != required_positive_int(
            expected, "represented_rows"
        ):
            raise OperationError("checkpoint represented rows differ from the contract")
        checkpoint_ordinal = expected.get("checkpoint_shard_ordinal")
        checkpoint_sha256 = expected.get("checkpoint_vector_sha256")
        if checkpoint_ordinal is not None or checkpoint_sha256 is not None:
            if (
                isinstance(checkpoint_ordinal, bool)
                or not isinstance(checkpoint_ordinal, int)
                or checkpoint_ordinal < 0
                or not isinstance(checkpoint_sha256, str)
                or len(shards) != 1
                or not isinstance(shards[0], dict)
                or shards[0].get("ordinal") != checkpoint_ordinal
                or not isinstance(shards[0].get("vectors"), dict)
                or shards[0]["vectors"].get("sha256")
                != require_sha256(
                    checkpoint_sha256, "expected.checkpoint_vector_sha256"
                )
            ):
                raise OperationError("checkpoint shard differs from the contract")
    return response


def transfer_receipt_values(context: Context) -> dict[str, object]:
    return {
        "schema_version": 1,
        "transport_manifest_sha256": context.pin("transport_manifest_sha256"),
        "operation_config_sha256": sha256_file(context.config_path),
        "reserved_budget_ledger_sha256": sha256_file(
            context.path("launch/reserved-budget-ledger.json")
        ),
    }


def remote_verify_transfer(context: Context) -> dict[str, object]:
    receipt_path = context.path("launch/transfer-verification.json")
    expected = transfer_receipt_values(context)
    if receipt_path.is_file():
        receipt = read_json(receipt_path)
        if not isinstance(receipt, dict) or any(
            receipt.get(field) != value for field, value in expected.items()
        ):
            raise OperationError("remote transfer receipt differs from this operation")
        return {"verified": True, "receipt": receipt}
    verify_reviewed_artifacts(context, require_local_execution_package=False)
    reservation = read_json(context.path("launch/full-build-reservation.json"))
    if not isinstance(reservation, dict) or reservation.get(
        "ledger_sha256"
    ) != expected["reserved_budget_ledger_sha256"]:
        raise OperationError("remote reserved ledger differs from its reservation")
    for relative in (
        "approval-plan.json",
        "approval.json",
        "offer.json",
        "create-result.json",
        "instance.json",
        "pre-transfer-instance-validation.json",
    ):
        read_json(context.path(f"launch/{relative}"))
    receipt = {**expected, "verified_at_utc": utc_text()}
    atomic_json(receipt_path, receipt)
    return {"verified": True, "receipt": receipt}


def require_remote_transfer_receipt(context: Context) -> None:
    receipt = read_json(context.path("launch/transfer-verification.json"))
    expected = transfer_receipt_values(context)
    if not isinstance(receipt, dict) or any(
        receipt.get(field) != value for field, value in expected.items()
    ):
        raise OperationError("remote preparation lacks a valid transfer receipt")


def remote_prepare_worker(
    context: Context, start_lock_fd: int
) -> dict[str, object]:
    attempt = context.path("preparation-attempts/001")
    attempt.mkdir(parents=True, exist_ok=True, mode=0o700)
    started = attempt / "preparation.started"
    exit_path = attempt / "preparation.exit"
    status = 1
    inherited_start_lock = start_lock_fd
    terminal_lock_fd = -1
    owns_preparation = False
    try:
        with file_lock(
            context.path("preparation-attempts/preparation.lock"), blocking=False
        ) as preparation_lock:
            owns_preparation = True
            terminal_lock_fd = os.dup(preparation_lock.fileno())
            atomic_bytes(started, f"{utc_text()}\n".encode("utf-8"))
            os.close(inherited_start_lock)
            inherited_start_lock = -1
            require_remote_transfer_receipt(context)
            if context.command_workload:
                prepare_remote_command(context)
                status = 0
                return {"prepared": True, "state": "complete"}
            work = context.path("work")
            if not work.exists():
                staging = context.path("work.next")
                if staging.exists():
                    shutil.rmtree(staging)
                shutil.copytree(context.path("transport/work-seed"), staging)
                reservation = read_json(
                    context.path("launch/full-build-reservation.json")
                )
                if not isinstance(reservation, dict) or not isinstance(
                    reservation.get("ledger_sha256"), str
                ):
                    raise OperationError("remote reservation receipt is invalid")
                reserved = context.path("launch/reserved-budget-ledger.json")
                verify_sha(reserved, reservation["ledger_sha256"], "reserved ledger")
                shutil.copyfile(reserved, staging / "budget-ledger.json")
                os.chmod(staging / "budget-ledger.json", 0o600)
                os.replace(staging, work)
                sync_directory(context.root)
            package = context.path("package")
            if not package.exists():
                staging = context.path("package.next")
                if staging.exists():
                    shutil.rmtree(staging)
                shutil.copytree(context.path("transport/package-skeleton"), staging)
                download = context.path("scratch/downloaded-bundle")
                download.mkdir(parents=True, exist_ok=True)
                environment = os.environ.copy()
                environment.update({"HF_HUB_OFFLINE": "0", "TRANSFORMERS_OFFLINE": "0"})
                completed_process(
                    [
                        "/opt/gte-venv/bin/python",
                        "/opt/oracle-mvp/gte/model_bundle.py",
                        "prepare",
                        str(download),
                    ],
                    environment=environment,
                )
                (staging / "bundle").mkdir(parents=True, exist_ok=True)
                os.replace(download / "model", staging / "bundle/model")
                with contextlib.suppress(FileNotFoundError):
                    (download / "model-lock.json").unlink()
                try:
                    full_build_package.verify_model_payload(
                        staging / "bundle/model",
                        staging / "bundle/model-lock.json",
                        context.path("transport/model-payload-identity.json"),
                    )
                    full_build_package.restore_model_metadata(
                        staging / "bundle/model",
                        context.path("transport/legacy-huggingface"),
                    )
                except (OSError, ValueError) as error:
                    raise OperationError(f"remote model verification failed: {error}") from error
                completed_process(
                    [
                        "/opt/gte-venv/bin/python",
                        "/opt/oracle-mvp/gte/model_bundle.py",
                        "verify",
                        str(staging / "bundle"),
                    ]
                )
                corpus = required_object(context.config, "corpus")
                try:
                    full_build_package.reconstruct_corpus(
                        context.path("transport/corpus/data.mdb.gz"),
                        staging / "corpus-root/ndb/data.mdb",
                        required_positive_int(corpus, "bytes"),
                        require_sha256(
                            required_string(corpus, "sha256"), "corpus.sha256"
                        ),
                        Path("/usr/bin/gzip"),
                    )
                    full_build_package.verify_manifest(
                        staging, staging / "package-manifest.json"
                    )
                except (OSError, ValueError) as error:
                    raise OperationError(f"remote package verification failed: {error}") from error
                os.replace(staging, package)
                sync_directory(context.root)
            descriptor = command_json(
            [
                str(context.path("transport/control/gte-oracle")),
                "describe-representation",
                str(context.path("package/run/full-build-config.json")),
            ]
        )
            atomic_json(context.path("work/offline-descriptor.json"), descriptor)
            try:
                host = calibration_package.capture_host(Path("nvidia-smi"), context.root)
                identity = calibration_package.build_execution_identity(
                    descriptor,
                    recorded_offer(context),
                    read_json(context.path("launch/create-result.json")),
                    read_json(context.path("launch/instance.json")),
                    host,
                )
            except (OSError, ValueError) as error:
                raise OperationError(f"remote execution identity failed: {error}") from error
            atomic_json(context.path("work/execution-identity.json"), identity)
            verification = command_json(
            [
                str(context.path("transport/control/gte-oracle")),
                "verify-representation",
                str(context.path("package/run/full-build-config.json")),
            ]
        )
            validate_representation(context, verification, complete=False)
            atomic_json(context.path("work/preparation-verification.json"), verification)
            status = 0
            return {"prepared": True, "state": "complete"}
    finally:
        if inherited_start_lock >= 0:
            with contextlib.suppress(OSError):
                os.close(inherited_start_lock)
        if owns_preparation:
            atomic_bytes(exit_path, f"{status}\n".encode("utf-8"))
        if terminal_lock_fd >= 0:
            with contextlib.suppress(OSError):
                os.close(terminal_lock_fd)


def remote_prepare(context: Context) -> dict[str, object]:
    attempt = context.path("preparation-attempts/001")
    exit_path = attempt / "preparation.exit"

    def terminal_response() -> dict[str, object]:
        status = read_exit_status(exit_path)
        return {
            "prepared": status == 0,
            "state": "complete" if status == 0 else "failed",
            "exit_status": status,
            "evidence_files": tree_file_records(
                context.path("preparation-attempts"), {"retrieval-manifest.json"}
            ),
        }

    if exit_path.is_file():
        return terminal_response()
    pid_path = attempt / "preparation.pid"
    with file_lock(
        context.path("preparation-attempts/preparation-start.lock"), blocking=True
    ) as start_lock:
        if exit_path.is_file():
            return terminal_response()
        pid = read_pid(pid_path)
        if pid is None and not (attempt / "preparation.started").exists():
            require_remote_transfer_receipt(context)
            attempt.mkdir(parents=True, exist_ok=True, mode=0o700)
            pid = spawn_remote_child(
                context,
                "_remote-prepare-worker",
                ["--start-lock-fd", str(start_lock.fileno())],
                attempt / "preparation.log",
                inherited_fds=(start_lock.fileno(),),
            )
            atomic_bytes(pid_path, f"{pid}\n".encode("utf-8"))
    with file_lock(
        context.path("preparation-attempts/preparation-start.lock"), blocking=True
    ):
        pass
    if exit_path.is_file():
        return terminal_response()
    try:
        with file_lock(
            context.path("preparation-attempts/preparation.lock"), blocking=False
        ):
            if exit_path.is_file():
                return terminal_response()
            attempt.mkdir(parents=True, exist_ok=True, mode=0o700)
            atomic_bytes(
                attempt / "preparation.orphaned",
                b"preparation owner exited without a terminal receipt\n",
            )
            atomic_bytes(exit_path, b"76\n")
    except OperationError:
        return {
            "prepared": False,
            "state": "running",
            "pid": read_pid(pid_path),
        }
    return terminal_response()


def remote_supervise(
    context: Context, attempt_id: str, start_lock_fd: int
) -> dict[str, object]:
    attempt_id = parse_attempt_id(attempt_id)
    attempt = context.path(f"work/full-build-attempts/{attempt_id}")
    attempt.mkdir(parents=True, exist_ok=True, mode=0o700)
    inherited_start_lock = start_lock_fd
    try:
        with file_lock(context.path("work/full-build.lock"), blocking=False) as worker_lock:
            preparation = context.path("preparation-attempts/001/preparation.exit")
            if not preparation.is_file() or read_exit_status(preparation) != 0:
                raise OperationError("remote preparation is not complete")
            log = (attempt / "full-build.log").open("ab", buffering=0)
            try:
                worker = subprocess.Popen(
                    [
                        sys.executable,
                        str(Path(__file__).resolve()),
                        "--root",
                        str(context.root),
                        "--config",
                        str(context.config_path),
                        "_remote-controller",
                        "--attempt",
                        attempt_id,
                    ],
                    cwd=context.root,
                    stdin=subprocess.DEVNULL,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                    close_fds=True,
                    pass_fds=(worker_lock.fileno(),),
                    env={**os.environ, "ORACLE_RUN_WORKER_LOCK_FD": str(worker_lock.fileno())},
                )
            finally:
                log.close()
            controller_pid = attempt / "controller.pid"
            started = attempt / "full-build.started"
            for _ in range(100):
                if controller_pid.is_file() and started.is_file():
                    break
                if worker.poll() is not None:
                    break
                time.sleep(0.1)
            if not controller_pid.is_file() or not started.is_file():
                if not command_requires_completion(context):
                    with contextlib.suppress(ProcessLookupError):
                        os.killpg(worker.pid, signal.SIGTERM)
                    with contextlib.suppress(subprocess.TimeoutExpired):
                        worker.wait(timeout=10)
                raise OperationError(
                    "remote controller did not publish its durable start before exiting"
                )
            os.close(inherited_start_lock)
            inherited_start_lock = -1
            raw_status = worker.wait()
            status = raw_status if raw_status >= 0 else 128 - raw_status
            atomic_bytes(
                attempt / "full-build.exit", f"{status}\n".encode("utf-8")
            )
            return {"state": "terminal", "exit_status": status}
    except (OperationError, OSError) as error:
        if not terminal_state(attempt):
            if (attempt / "full-build.started").is_file():
                pass
            elif (attempt / "controller.pid").is_file():
                atomic_bytes(
                    attempt / "full-build.orphaned",
                    b"controller committed before durable start acknowledgement\n",
                )
            else:
                atomic_bytes(attempt / "start.exit", b"75\n")
        if isinstance(error, OperationError):
            raise
        raise OperationError(f"remote worker supervisor failed: {error}") from error
    finally:
        if inherited_start_lock >= 0:
            with contextlib.suppress(OSError):
                os.close(inherited_start_lock)


def remote_controller(context: Context, attempt_id: str) -> NoReturn:
    attempt_id = parse_attempt_id(attempt_id)
    attempt = context.path(f"work/full-build-attempts/{attempt_id}")
    atomic_bytes(
        attempt / "controller.pid", f"{os.getpid()}\n".encode("utf-8")
    )
    atomic_bytes(
        attempt / "full-build.started", f"{utc_text()}\n".encode("utf-8")
    )
    executable = str(context.path("transport/control/gte-oracle"))
    arguments = [
        executable,
        "run-full-build",
        str(context.path("package/run/full-build-config.json")),
    ]
    if context.command_workload:
        workload = required_object(context.config, "workload")
        arguments = workload["command"]
        executable = arguments[0]
        os.chdir(context.path("work"))
        os.environ.update(workload.get("environment", {}))
        os.environ["ORACLE_RUN_ATTEMPT_ID"] = attempt_id
        for key in ("ORACLE_RUN_PREVIOUS_ATTEMPT_ID", "ORACLE_RUN_CONTINUATION_REASON"):
            os.environ.pop(key, None)
        resume = attempt / "resume.json"
        if resume.exists():
            document = read_json(resume)
            os.environ["ORACLE_RUN_PREVIOUS_ATTEMPT_ID"] = document["previous_attempt"]
            os.environ["ORACLE_RUN_CONTINUATION_REASON"] = document["reason"]
        if workload["work_seconds"] is None:
            os.environ.pop("ORACLE_RUN_DEADLINE_UTC", None)
        else:
            os.environ["ORACLE_RUN_DEADLINE_UTC"] = utc_text(utc_now() + timedelta(seconds=workload["work_seconds"]))
    try:
        os.execv(executable, arguments)
    except OSError as error:
        raise OperationError(f"could not exec the full-build controller: {error}") from error


def remote_worker(context: Context, attempt_id: str, resume_from: str | None = None,
                  reason: str | None = None) -> dict[str, object]:
    attempt_id = parse_attempt_id(attempt_id)
    attempts = context.path("work/full-build-attempts")
    attempts.mkdir(parents=True, exist_ok=True, mode=0o700)
    attempt = attempts / attempt_id
    resume = None
    if resume_from is not None:
        resume_from = parse_attempt_id(resume_from)
        if (not context.command_workload or context.config["workload"].get("resumable") is not True
                or not isinstance(reason, str) or not reason.strip() or resume_from >= attempt_id):
            raise OperationError("continuation requires an explicitly resumable workload and a reason")
        verify_reviewed_artifacts(context)
        try:
            full_build_package.verify_manifest(context.path("package"), context.path("package/package-manifest.json"))
        except (OSError, ValueError) as error:
            raise OperationError(f"continuation package verification failed: {error}") from error
        resume = {"previous_attempt": resume_from, "reason": reason,
                  "operation_contract_sha256": sha256_file(context.config_path)}
    with file_lock(
        context.path("work/full-build-start.lock"), blocking=True
    ) as start_lock:
        if attempt.is_dir():
            if resume is not None and read_json(attempt / "resume.json") != resume:
                raise OperationError("continuation delivery differs from the saved intent")
            status = remote_attempt_status(context, attempt_id)
            if status["state"] in ("running", "starting", "terminal"):
                acknowledged = (
                    status.get("execution_committed") is True
                    and status["state"] in ("running", "starting")
                ) or (
                    status["state"] == "terminal"
                    and status.get("kind") != "start.exit"
                )
                return {
                    "acknowledged": acknowledged,
                    **status,
                }
            if status["state"] == "orphaned":
                with file_lock(context.path("work/full-build.lock"), blocking=False):
                    if attempt_execution_committed(attempt):
                        atomic_bytes(
                            attempt / "full-build.orphaned",
                            b"supervisor and controller are dead; worker lock is free\n",
                        )
                    else:
                        atomic_bytes(attempt / "start.exit", b"75\n")
                return {"acknowledged": False, **remote_attempt_status(context, attempt_id)}
        committed = []
        for prior in sorted(attempts.iterdir()):
            if prior == attempt or not prior.is_dir():
                continue
            terminal = terminal_state(prior)
            if terminal is None:
                raise OperationError(f"prior worker attempt is unresolved: {prior.name}")
            if terminal.get("kind") != "start.exit":
                committed.append(prior.name)
        if committed and (resume is None or committed[-1] != resume_from):
            raise OperationError(f"prior worker attempt consumed the full-build execution: {committed[-1]}")
        if resume is not None and (not committed or committed[-1] != resume_from):
            raise OperationError("continuation does not follow the latest terminal execution")
        with file_lock(context.path("work/full-build.lock"), blocking=False):
            pass
        if resume is not None:
            for source, name in ((context.path("work/retrieval-manifest.json"), "retrieval-work-manifest.json"),
                                 (context.path("preparation-attempts/retrieval-manifest.json"), "retrieval-preparation-manifest.json")):
                saved = attempts / resume_from / name
                if source.exists():
                    if saved.exists():
                        raise OperationError("previous retrieval manifest archive already exists")
                    os.replace(source, saved)
                    sync_directory(saved.parent)
        attempt.mkdir(mode=0o700)
        if resume is not None:
            atomic_json(attempt / "resume.json", resume)
        pid = spawn_remote_child(
            context,
            "_remote-supervise",
            [
                "--attempt",
                attempt_id,
                "--start-lock-fd",
                str(start_lock.fileno()),
            ],
            attempt / "nohup.log",
            inherited_fds=(start_lock.fileno(),),
        )
        atomic_bytes(attempt / "full-build.pid", f"{pid}\n".encode("utf-8"))
        for _ in range(100):
            status = remote_attempt_status(context, attempt_id)
            if status["state"] in ("running", "terminal"):
                acknowledged = status["state"] == "running" or (
                    status["state"] == "terminal"
                    and status.get("kind") != "start.exit"
                )
                return {"acknowledged": acknowledged, **status}
            if not process_alive(pid):
                break
            time.sleep(0.1)
        raise OperationError("remote worker did not acknowledge its start")


def remote_stop(context: Context, attempt_id: str, incomplete_stop_approval: str | None = None) -> dict[str, object]:
    with file_lock(context.path("work/full-build-start.lock"), blocking=True):
        status = remote_attempt_status(context, attempt_id)
        if status["state"] == "terminal":
            return {"stop_requested": True, **status}
        if command_requires_completion(context):
            if not isinstance(incomplete_stop_approval, str) or not incomplete_stop_approval.strip():
                raise OperationError("incomplete work requires explicit user stop approval")
            atomic_json(context.path(f"work/full-build-attempts/{attempt_id}/user-approved-stop.json"),
                        {"reason": incomplete_stop_approval, "recorded_at_utc": utc_text(),
                         "operation_contract_sha256": sha256_file(context.config_path)})
        controller = status.get("controller_pid")
        if not isinstance(controller, int) or not process_alive(controller):
            raise OperationError("remote worker has no live controller to stop")
        try:
            os.killpg(controller, signal.SIGTERM)
        except ProcessLookupError:
            pass
        return {"stop_requested": True, "attempt_id": attempt_id}


def remote_abort_unstarted(context: Context, attempt_id: str) -> dict[str, object]:
    attempt_id = parse_attempt_id(attempt_id)
    attempt = context.path(f"work/full-build-attempts/{attempt_id}")
    with file_lock(context.path("work/full-build-start.lock"), blocking=True):
        status = remote_attempt_status(context, attempt_id)
        if status["state"] not in ("absent", "orphaned") or (
            attempt.is_dir() and attempt_execution_committed(attempt)
        ):
            raise OperationError("worker attempt is not safely unstarted")
        with file_lock(context.path("work/full-build.lock"), blocking=False):
            attempt.mkdir(parents=True, exist_ok=True, mode=0o700)
            atomic_bytes(
                attempt / "start-preconditions.log",
                b"operator stop proved the worker was never started\n",
            )
            atomic_bytes(attempt / "start.exit", b"74\n")
    return {"aborted_unstarted": True, **remote_attempt_status(context, attempt_id)}


def tree_file_records(root: Path, excluded: set[str]) -> list[dict[str, object]]:
    records = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise OperationError(f"retrieval tree contains a symbolic link: {path}")
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if relative in excluded:
            continue
        records.append(
            {"path": relative, "bytes": path.stat().st_size, "sha256": sha256_file(path)}
        )
    if not records:
        raise OperationError(f"retrieval tree contains no files: {root}")
    return records


def remote_seal(context: Context, attempt_id: str) -> dict[str, object]:
    attempt_id = parse_attempt_id(attempt_id)
    attempt = context.path(f"work/full-build-attempts/{attempt_id}")
    with file_lock(context.path("work/full-build-start.lock"), blocking=False):
        with file_lock(context.path("work/full-build.lock"), blocking=False):
            terminal = terminal_state(attempt)
            if terminal is None:
                if any(process_alive(read_pid(attempt / name))
                       for name in ("full-build.pid", "controller.pid")):
                    raise OperationError("worker is not terminal and cannot be sealed")
                if attempt_execution_committed(attempt):
                    atomic_bytes(
                        attempt / "full-build.orphaned",
                        b"supervisor and controller are dead; both worker locks are free\n",
                    )
                else:
                    atomic_bytes(attempt / "start.exit", b"75\n")
                terminal = terminal_state(attempt)
            work_records = tree_file_records(
                context.path("work"), {"retrieval-manifest.json"}
            )
            preparation_records = tree_file_records(
                context.path("preparation-attempts"), {"retrieval-manifest.json"}
            )
            work_manifest = {
                "schema_version": 1,
                "artifact_kind": "gte-full-build-retrieval-work",
                "files": work_records,
            }
            preparation_manifest = {
                "schema_version": 1,
                "artifact_kind": "gte-full-build-retrieval-preparation",
                "files": preparation_records,
            }
            atomic_json(context.path("work/retrieval-manifest.json"), work_manifest)
            atomic_json(
                context.path("preparation-attempts/retrieval-manifest.json"),
                preparation_manifest,
            )
            return {
                "terminal": True,
                "attempt_id": attempt_id,
                "terminal_record": terminal,
                "work_files": work_records,
                "preparation_files": preparation_records,
            }


def progressive_policy(context: Context) -> dict[str, int] | None:
    if not context.command_workload:
        return None
    policy = context.config["workload"].get("progressive_copy")
    if policy is None:
        return None
    fields = {"poll_seconds", "bytes_per_second", "timeout_seconds"}
    if not isinstance(policy, dict) or set(policy) != fields:
        raise OperationError("invalid progressive copy policy")
    for field in fields:
        required_positive_int(policy, field)
    return policy


def copy_records(records: object) -> list[dict[str, object]]:
    if not isinstance(records, list):
        raise OperationError("copy records must be a list")
    seen = set()
    for record in records:
        if not isinstance(record, dict):
            raise OperationError("invalid copy record")
        path = command_relative_path(record.get("path"))
        if path.as_posix() != record["path"] or path.parts[0] not in ("work", "preparation-attempts") or len(path.parts) < 2:
            raise OperationError("invalid copy path")
        if record["path"] in seen:
            raise OperationError("duplicate copy path")
        seen.add(record["path"])
        size = required_nonnegative_int(record, "bytes")
        offset = record.get("offset", 0)
        if type(offset) is not int or not 0 <= offset <= size:
            raise OperationError("invalid copy offset")
        length = record.get("length", size - offset)
        if type(length) is not int or not 0 <= length <= size - offset or (length == 0 and offset < size):
            raise OperationError("invalid copy length")
        require_sha256(required_string(record, "sha256"), "copy SHA256")
        if "completion_files" in record:
            members = record["completion_files"]
            if not isinstance(members, list) or not members or any(not isinstance(n, str) for n in members):
                raise OperationError("invalid completion file list")
            if len(set(members)) != len(members) or record["path"] in members:
                raise OperationError("duplicate completion file")
            for member in members:
                member_path = command_relative_path(member)
                if member_path.as_posix() != member or not member_path.is_relative_to(path.parent):
                    raise OperationError("completion file is outside its sealed directory")
    return records


def copy_source(context: Context, relative: str) -> Path:
    path = context.path(relative)
    if path.resolve() != path.absolute() or not path.is_file():
        raise OperationError(f"copy source is missing or contains a symbolic link: {relative}")
    return path


def copy_priority() -> None:
    os.nice(19)
    completed_process(["ionice", "-c", "3", "-p", str(os.getpid())])


def remote_progress(context: Context) -> dict[str, object]:
    """Discover completion records without rereading large saved tensors."""
    if progressive_policy(context) is None:
        raise OperationError("progressive copying is not configured")
    copy_priority()
    records = {}
    for relative in context.config["workload"]["outputs"]:
        root = context.path("work") / relative
        for seal in sorted({*root.rglob("complete.json"), *root.rglob("*.complete.json")}):
            if any(".partial" in part or part.startswith(".") for part in seal.relative_to(root).parts):
                continue
            contents = read_json(copy_source(context, str(seal.relative_to(context.root))))
            if not isinstance(contents, dict) or not contents:
                raise OperationError("invalid progressive completion record")
            files = dict(contents)
            files[seal.name] = sha256_file(seal)
            for name, digest in files.items():
                path = seal.parent / command_relative_path(name)
                record = {"path": str(path.relative_to(context.root)),
                          "bytes": copy_source(context, str(path.relative_to(context.root))).stat().st_size,
                          "sha256": digest}
                if name == seal.name and seal.name != "complete.json":
                    record["completion_files"] = [str((seal.parent / command_relative_path(n)).relative_to(context.root))
                                                  for n in contents]
                copy_records([record])
                existing = records.get(record["path"], {})
                if any(key in existing and existing[key] != value for key, value in record.items()):
                    raise OperationError("published progressive files disagree")
                records[record["path"]] = {**existing, **record}
    return {"files": list(records.values())}


def remote_copy(context: Context, records: object) -> None:
    policy = progressive_policy(context)
    if policy is None:
        raise OperationError("progressive copying is not configured")
    copy_priority()
    started, sent = time.monotonic(), 0
    for record in copy_records(records):
        path = copy_source(context, record["path"])
        if path.stat().st_size != record["bytes"]:
            raise OperationError("copy source size changed")
        with path.open("rb") as source:
            source.seek(record.get("offset", 0))
            remaining = record.get("length", record["bytes"] - source.tell())
            while remaining:
                chunk = source.read(min(65536, remaining))
                if not chunk:
                    raise OperationError("copy source ended early")
                sys.stdout.buffer.write(chunk)
                sys.stdout.buffer.flush()
                sent += len(chunk)
                remaining -= len(chunk)
                delay = started + sent / policy["bytes_per_second"] - time.monotonic()
                if delay > 0:
                    time.sleep(delay)


def copy_destination(context: Context, record: dict[str, object]) -> Path:
    relative = Path(record["path"])
    if relative.parts[0] == "preparation-attempts":
        relative = Path("audit") / relative
    path = context.path("result.next") / relative
    if path.resolve() != path.absolute():
        raise OperationError("copy destination contains a symbolic link")
    return path


def receive_copy(context: Context, request: Path) -> None:
    """Publish each file only after its complete contents match the saved hash."""
    for record in copy_records(read_json(request)):
        target = copy_destination(context, record)
        partial = context.path("progressive/partial") / record["path"]
        partial.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        offset = record.get("offset", 0)
        if (partial.stat().st_size if partial.exists() else 0) != offset:
            raise OperationError("partial copy offset changed")
        with partial.open("a+b") as output:
            remaining = record.get("length", record["bytes"] - offset)
            while remaining:
                chunk = sys.stdin.buffer.read(min(65536, remaining))
                if not chunk:
                    raise OperationError("copy stream ended early; partial files retained")
                output.write(chunk)
                remaining -= len(chunk)
            output.flush()
            os.fsync(output.fileno())
        if partial.stat().st_size < record["bytes"]:
            continue
        # Hash once at completion, including bytes retained across chunks or
        # interrupted streams. Incomplete files never acquire a verified receipt.
        if partial.stat().st_size != record["bytes"] or sha256_file(partial) != record["sha256"]:
            raise OperationError("copy hash mismatch; evidence retained")
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if target.exists():
            raise OperationError("copy destination already exists")
        os.replace(partial, target)
        sync_directory(target.parent)
        atomic_json(context.path("progressive/verified") / (record["path"] + ".json"), {
            **{key: record[key] for key in ("path", "bytes", "sha256")},
            "local_mtime_ns": target.stat().st_mtime_ns, "verified_at_utc": utc_text()})
    if sys.stdin.buffer.read(1):
        raise OperationError("copy stream has extra bytes")


def copy_files(context: Context, private_key: Path, target: list[str], records: object,
               *, terminal: bool = False, one_group: bool = False) -> dict[str, int]:
    policy = progressive_policy(context)
    if policy is None:
        raise OperationError("progressive copying is not configured")
    totals = {"copied_files": 0, "copied_bytes": 0, "reused_files": 0, "reused_bytes": 0}
    records = copy_records(records)
    sizes = {Path(record["path"]).parent: 0 for record in records
             if Path(record["path"]).name == "complete.json"}
    for record in records:
        for parent in Path(record["path"]).parents:
            if parent in sizes:
                sizes[parent] += record["bytes"]

    def priority(record):
        path = Path(record["path"])
        if path in subsets:
            size, group, marker = subsets[path]
            return (size, group, marker, record["bytes"], record["path"])
        directory = next((parent for parent in path.parents if parent in sizes), None)
        return (sizes[directory] if directory is not None else record["bytes"],
                str(directory if directory is not None else path),
                path.name == "complete.json", record["bytes"], record["path"])

    subsets = {}
    by_path = {record["path"]: record for record in records}
    for marker in records:
        if "completion_files" not in marker:
            continue
        names = [*marker["completion_files"], marker["path"]]
        if any(n not in by_path for n in names):
            raise OperationError("completion marker has a missing copy dependency")
        size = sum(by_path[n]["bytes"] for n in names)
        for name in names:
            group = (size, marker["path"], name == marker["path"])
            if Path(name) not in subsets or group < subsets[Path(name)]:
                subsets[Path(name)] = group
    # Prioritize small sealed subsets/directories, with their markers last.
    # Descendant directories are smaller than ancestors, so enclosing markers
    # also follow the files they certify. Unsealed files use their own size.
    records = sorted(records, key=priority)
    # Bound each stream so the watcher can
    # discover newly sealed responses between checkpoint chunks. At the
    # distillation default of 8 MiB/s, 64 MiB takes eight seconds of payload,
    # amortizing SSH setup without holding the copier for an entire checkpoint.
    stream_bytes = 64 * 1024 * 1024
    position = 0
    while position < len(records):
        with file_lock(context.path("progressive/copy.lock"), blocking=True):
            if not terminal and context.path("progressive/terminal.json").exists():
                break
            pending, size = [], 0
            while position < len(records) and len(pending) < 32 and size < stream_bytes:
                record = records[position]
                destination = copy_destination(context, record)
                receipt = context.path("progressive/verified") / (record["path"] + ".json")
                if destination.exists():
                    saved = read_json(receipt) if receipt.exists() else None
                    if saved is not None:
                        if (any(saved.get(key) != record[key] for key in ("path", "bytes", "sha256"))
                                or destination.stat().st_size != record["bytes"]
                                or destination.stat().st_mtime_ns != saved["local_mtime_ns"]):
                            raise OperationError("previously verified copy changed; evidence retained")
                    elif destination.stat().st_size != record["bytes"] or sha256_file(destination) != record["sha256"]:
                        raise OperationError("existing copy hash mismatch; evidence retained")
                    if saved is None:
                        atomic_json(receipt, {
                            **{key: record[key] for key in ("path", "bytes", "sha256")},
                            "local_mtime_ns": destination.stat().st_mtime_ns, "verified_at_utc": utc_text()})
                    totals["reused_files"] += 1
                    totals["reused_bytes"] += record["bytes"]
                    position += 1
                    continue
                partial = context.path("progressive/partial") / record["path"]
                offset = partial.stat().st_size if partial.exists() else 0
                if offset > record["bytes"]:
                    raise OperationError("partial copy exceeds expected size")
                length = min(record["bytes"] - offset, stream_bytes - size)
                pending.append({**record, "offset": offset, "length": length})
                size += length
                if offset + length == record["bytes"]:
                    position += 1
            if not pending:
                continue
            request = context.path("progressive/request.json")
            atomic_json(request, pending, replace=True)
            encoded = shlex.quote(json.dumps(pending, separators=(",", ":")))
            stream_processes(
                remote_arguments(context, private_key, target, "_remote-copy", "--files", encoded),
                [sys.executable, str(context.operator_path), "--root", str(context.root),
                 "--config", str(context.config_path), "_receive-copy", "--request", str(request)],
                "progressive copy", policy["timeout_seconds"])
            totals["copied_files"] += sum(record["offset"] + record["length"] == record["bytes"] for record in pending)
            totals["copied_bytes"] += size
            if one_group:
                break
    return totals


def progressive_copy(context: Context, watch: bool) -> dict[str, object]:
    verify_reviewed_artifacts(context)
    policy = progressive_policy(context)
    if policy is None:
        raise OperationError("progressive copying is not configured")
    with file_lock(context.path("progressive/watch.lock"), blocking=False):
        endpoint = read_json(context.path("progressive/endpoint.json"))
        while True:
            if (context.path("progressive/terminal.json").exists()
                    or context.path("launch/retrieval-verification.json").exists()
                    or context.path("launch/destruction-confirmation.json").exists()):
                state = {"state": "stopped", "observed_at_utc": utc_text()}
                atomic_json(context.path("progressive/status.json"), state, replace=True)
                return state
            try:
                inventory = remote_json(context, Path(endpoint["identity"]), endpoint["target"], "_remote-progress")
                totals = copy_files(context, Path(endpoint["identity"]), endpoint["target"], inventory["files"],
                                    one_group=watch)
                state = {"state": "watching" if watch else "copied", **totals, "observed_at_utc": utc_text()}
                atomic_json(context.path("progressive/status.json"), state, replace=True)
            except (OperationError, OSError) as error:
                atomic_json(context.path("progressive/status.json"), {
                    "state": "failed", "error": str(error), "observed_at_utc": utc_text()}, replace=True)
                raise
            if not watch:
                return state
            if not (totals["copied_bytes"] or totals["copied_files"]):
                time.sleep(policy["poll_seconds"])


def start_progressive_copy(context: Context, private_key: Path, target: list[str]) -> subprocess.Popen[bytes]:
    atomic_json(context.path("progressive/endpoint.json"), {
        "identity": str(private_key), "target": target}, replace=True)
    with context.path("progressive/copier.log").open("ab") as log:
        return subprocess.Popen([sys.executable, str(context.operator_path), "--root", str(context.root),
            "--config", str(context.config_path), "copy", "--watch"], stdout=log, stderr=log)


def validate_file_records(root: Path, records: object) -> list[dict[str, object]]:
    if not isinstance(records, list) or not records:
        raise OperationError("retrieval manifest contains no files")
    expected: dict[str, dict[str, object]] = {}
    for record in records:
        if not isinstance(record, dict):
            raise OperationError("retrieval manifest contains an invalid record")
        relative = record.get("path")
        byte_count = record.get("bytes")
        digest = record.get("sha256")
        if (
            not isinstance(relative, str)
            or not relative
            or Path(relative).is_absolute()
            or ".." in Path(relative).parts
            or relative in expected
            or isinstance(byte_count, bool)
            or not isinstance(byte_count, int)
            or byte_count < 0
            or not isinstance(digest, str)
        ):
            raise OperationError("retrieval manifest contains an invalid record")
        require_sha256(digest, f"retrieval file {relative}")
        expected[relative] = record
    actual: set[str] = set()
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise OperationError(f"retrieved tree contains a symbolic link: {path}")
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if relative == "retrieval-manifest.json":
            continue
        actual.add(relative)
    if actual != set(expected):
        raise OperationError("retrieved file set does not match the sealed manifest")
    for relative, record in expected.items():
        path = root / relative
        if path.stat().st_size != record["bytes"] or sha256_file(path) != record["sha256"]:
            raise OperationError(f"retrieved file failed integrity verification: {relative}")
    return list(expected.values())


def ensure_retrieved(
    context: Context,
    instance_id: str,
    private_key: Path,
    target: list[str],
    attempt_id: str,
) -> dict[str, object]:
    receipt_path = context.path("launch/retrieval-verification.json")
    if receipt_path.exists():
        receipt = read_json(receipt_path)
        if (not isinstance(receipt, dict) or receipt.get("instance_id") != instance_id
                or receipt.get("attempt_id") != attempt_id):
            raise OperationError("retrieval verification receipt is invalid")
        return receipt
    response = remote_json(
        context, private_key, target, "_remote-seal", "--attempt", attempt_id
    )
    if not isinstance(response, dict) or response.get("terminal") is not True:
        raise OperationError("remote state was not sealed as terminal")
    work_records = response.get("work_files", response.get("files"))
    preparation_records = response.get("preparation_files")
    destination = context.path("result.next")
    if not destination.is_dir():
        raise OperationError("result.next is missing before retrieval")
    progressive = progressive_policy(context) is not None
    if progressive:
        atomic_json(context.path("progressive/terminal.json"), {"attempt_id": attempt_id})
        records = [{**record, "path": "work/" + record["path"]} for record in work_records]
        by_path = {record["path"]: record for record in records}
        inventory = remote_json(context, private_key, target, "_remote-progress")
        for published in copy_records(inventory["files"]):
            sealed = by_path.get(published["path"])
            if sealed is None or any(sealed[key] != published[key] for key in ("bytes", "sha256")):
                raise OperationError("progressive publication differs from terminal retrieval seal")
            if "completion_files" in published:
                sealed["completion_files"] = published["completion_files"]
        # The terminal manifest itself is excluded from its file list. Copy it
        # using its small authoritative bytes from the sealed response.
        copied = copy_files(context, private_key, target, records, terminal=True)
        atomic_json(destination / "work/retrieval-manifest.json", {
            "schema_version": 1, "artifact_kind": "gte-full-build-retrieval-work", "files": work_records})
    else:
        tar_download_directory(
            context, private_key, target, "/workspace/oracle-full-build/work/", destination / "work")
    verified_work = validate_file_records(destination / "work", work_records)
    verified_preparation: list[dict[str, object]] = []
    if preparation_records is not None:
        preparation_destination = destination / "audit/preparation-attempts"
        tar_download_directory(
            context,
            private_key,
            target,
            "/workspace/oracle-full-build/preparation-attempts/",
            preparation_destination,
        )
        verified_preparation = validate_file_records(
            preparation_destination, preparation_records
        )
    receipt = {
        "schema_version": 1,
        "instance_id": instance_id,
        "attempt_id": attempt_id,
        "sealed_terminal": response.get("terminal_record"),
        "work_files": verified_work,
        "preparation_files": verified_preparation,
        "verified_at_utc": utc_text(),
    }
    if progressive:
        receipt["progressive_copy"] = copied
    atomic_json(receipt_path, receipt)
    return receipt


def resume(context: Context, reason: str) -> dict[str, object]:
    """Explicitly continue an opted-in frozen job on its existing instance."""
    verify_reviewed_artifacts(context)
    if not context.command_workload or context.config["workload"].get("resumable") is not True:
        raise OperationError("the frozen workload does not permit continuation")
    if not isinstance(reason, str) or not reason.strip():
        raise OperationError("continuation requires a recorded reason")
    with file_lock(context.path("watch.lock"), blocking=False), \
            file_lock(context.path("progressive/watch.lock"), blocking=False), operation_lock(context.root):
        if any(context.path(name).exists() for name in (
                "launch/destruction-confirmation.json", "launch/provider-final-charge.json",
                "result/settlement/settlement-result.json")):
            raise OperationError("cannot continue a destroyed or settled instance")
        instance_id = recorded_instance_id(context)
        previous = last_attempt_id(context)
        if instance_id is None or previous is None:
            raise OperationError("continuation requires an existing instance and worker attempt")
        private, target = ensure_ssh(context, instance_id)
        invocation = read_json(context.path(f"launch/worker-invocations/{previous}.json"))
        if invocation.get("resume_from") and invocation.get("reason") == reason:
            attempt_id = previous
            previous = parse_attempt_id(invocation["resume_from"])
        else:
            state = worker_status(context, private, target, previous)
            if state["state"] not in ("terminal", "orphaned"):
                raise OperationError("continuation requires a terminal worker; running work is preserved")
            receipt = ensure_retrieved(context, instance_id, private, target, previous)
            tree = context.path("result") if context.path("result").is_dir() else context.path("result.next")
            validate_file_records(tree / "work", receipt["work_files"])
            attempt_id = next_attempt_id(context)
            invocation = {
                "schema_version": 1, "attempt_id": attempt_id, "instance_id": instance_id,
                "resume_from": previous, "reason": reason, "invoked_at_utc": utc_text(),
                "operation_contract_sha256": sha256_file(context.config_path),
                "previous_retrieval_sha256": sha256_file(context.path("launch/retrieval-verification.json")),
            }
            atomic_json(context.path(f"launch/worker-invocations/{attempt_id}.json"), invocation)
            atomic_json(context.path(f"launch/worker-invocations/{previous}.terminal.json"), state)
        if invocation.get("instance_id") != instance_id or invocation.get("operation_contract_sha256") != sha256_file(context.config_path):
            raise OperationError("continuation invocation belongs to another instance or contract")
        prepared = context.path(f"launch/worker-invocations/{attempt_id}.prepared.json")
        archive = context.path(f"retrieval-attempts/{previous}")
        if not prepared.exists():
            archive.mkdir(parents=True, exist_ok=True, mode=0o700)
            prior_terminal = context.path(f"launch/worker-invocations/{previous}.terminal.json")
            if not prior_terminal.exists():
                atomic_json(prior_terminal, worker_status(context, private, target, previous))
            if not (archive / "result").exists():
                tree = context.path("result") if context.path("result").is_dir() else context.path("result.next")
                os.replace(tree, archive / "result")
                sync_directory(archive)
            # Each move is idempotent, so delivery can be reconciled after a
            # controller interruption without deleting earlier evidence.
            for source, destination in (
                    ("launch/retrieval-verification.json", "retrieval-verification.json"),
                    ("launch/worker-started.json", "worker-started.json"),
                    ("launch/completion-review.json", "completion-review.json"),
                    ("launch/user-approved-incomplete-stop.json", "user-approved-incomplete-stop.json"),
                    *(("progressive/" + n, "progressive/" + n) for n in
                      ("terminal.json", "status.json", "verified", "partial", "failures"))):
                path, saved = context.path(source), archive / destination
                if path.exists():
                    if saved.exists():
                        raise OperationError("continuation archive destination already exists")
                    saved.parent.mkdir(parents=True, exist_ok=True)
                    os.replace(path, saved)
                    sync_directory(saved.parent)
            old_receipt = archive / "retrieval-verification.json"
            if sha256_file(old_receipt) != invocation["previous_retrieval_sha256"]:
                raise OperationError("previous retrieval receipt changed during continuation")
            receipt = read_json(old_receipt)
            validate_file_records(archive / "result/work", receipt["work_files"])
            context.path("result.next").mkdir(exist_ok=True)
            if progressive_policy(context) is not None:
                inventory = remote_json(context, private, target, "_remote-progress")
                for record in copy_records(inventory["files"]):
                    source = archive / "result" / record["path"]
                    destination = copy_destination(context, record)
                    if not source.is_file() or source.stat().st_size != record["bytes"] or sha256_file(source) != record["sha256"]:
                        raise OperationError("published continuation input differs from retrieved evidence")
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    if destination.exists():
                        if sha256_file(destination) != record["sha256"]:
                            raise OperationError("continuation copy differs from saved evidence")
                    else:
                        os.link(source, destination)
            atomic_json(prepared, {"previous_attempt": previous, "archive": str(archive.relative_to(context.root))})
        started = ensure_worker_started(context, instance_id, private, target)
        return {"state": "running", "instance_id": instance_id, "attempt_id": started,
                "remote": worker_status(context, private, target, started)}


def publish_verified_result(context: Context, attempt_id: str) -> bool:
    result = context.path("result")
    if result.is_dir():
        return (result / "audit/local-verification.json").is_file()
    candidate = context.path("result.next")
    attempt = candidate / f"work/full-build-attempts/{attempt_id}"
    terminal = terminal_state(attempt)
    if terminal is None:
        raise OperationError("retrieved worker attempt has no terminal evidence")
    if terminal.get("kind") != "full-build.exit" or terminal.get("exit_status") != 0:
        return False
    verification_path = candidate / "audit/local-verification.json"
    if not verification_path.exists():
        try:
            if context.command_workload:
                response = verify_command_results(context, candidate)
            else:
                response = context.controller(
                    "result.next",
                    ["verify-representation", "package/run/full-build-config.json"],
                )
                validate_representation(context, response, complete=True)
            atomic_json(verification_path, response)
        except OperationError as error:
            atomic_bytes(
                candidate / "audit/local-verification-failure.log",
                f"{error}\n".encode("utf-8"),
            )
            return False
    os.replace(candidate, result)
    sync_directory(result.parent)
    return True


def create_authorized_destroy(
    context: Context,
    instance_id: str,
    offer: dict[str, object],
    create_result: dict[str, object],
) -> None:
    path = context.path("launch/create-authorized-destroy.json")
    checks = {
        "schema_version": 1,
        "artifact_kind": "gte-create-authorized-vast-destroy",
        "instance_id": instance_id,
        "offer_id": str(offer.get("id")),
        "image": context.image,
        "label": context.label,
        "create_result_sha256": sha256_file(
            context.path("launch/create-result.json")
        ),
        "offer_sha256": sha256_file(context.path("launch/offer.json")),
    }
    if path.exists():
        document = read_json(path)
        if not isinstance(document, dict) or any(
            document.get(field) != value for field, value in checks.items()
        ):
            raise OperationError("create-authorized destroy receipt differs")
        return
    try:
        if calibration_package.created_instance_id(create_result) != instance_id:
            raise ValueError("create result instance ID changed")
    except ValueError as error:
        raise OperationError(f"create-authorized destroy is invalid: {error}") from error
    atomic_json(path, {**checks, "recorded_at_utc": utc_text()})


def verify_destroy_ownership(
    context: Context, instance_id: str, live_instance: dict[str, object] | None
) -> bool:
    create_result = read_json(context.path("launch/create-result.json"))
    try:
        if calibration_package.created_instance_id(create_result) != instance_id:
            raise OperationError("destroy target differs from the recorded create result")
    except ValueError as error:
        raise OperationError(f"create result is invalid during destroy: {error}") from error
    offer = recorded_offer(context)
    create_authorized_destroy(context, instance_id, offer, create_result)
    observed = False
    # A failed offer/hardware check cannot revoke ownership established by
    # create. Retain ID/label and receipt-integrity checks for recorded data.
    for relative in ("launch/instance-ownership.json", "launch/instance.json"):
        frozen_path = context.path(relative)
        if frozen_path.exists():
            record_instance_ownership(context, create_result, read_json(frozen_path))
            observed = True
    if live_instance is not None:
        try:
            frozen_live = calibration_package.freeze_instance_record(create_result, live_instance)
        except ValueError as error:
            raise OperationError(f"live destroy target is not the bound operation instance: {error}") from error
        record_instance_ownership(context, create_result, frozen_live)
        observed = True
    return observed


def invoke_destroy_request(
    context: Context, instance_id: str, *, force: bool = False
) -> bool:
    attempted_path = context.path("launch/destroy-request-attempted.json")
    attempted = {
        "schema_version": 1,
        "instance_id": instance_id,
        "create_authorization_sha256": sha256_file(
            context.path("launch/create-authorized-destroy.json")
        ),
    }
    if attempted_path.exists():
        document = read_json(attempted_path)
        if not isinstance(document, dict) or any(
            document.get(field) != value for field, value in attempted.items()
        ):
            raise OperationError("destroy-request attempt receipt differs")
    else:
        atomic_json(
            attempted_path,
            {**attempted, "attempted_at_utc": utc_text()},
        )
    response_path = context.path("launch/destroy-response.json")
    prior_exit_zero = False
    if response_path.exists():
        response = read_json(response_path)
        if (
            not isinstance(response, dict)
            or response.get("instance_id") != instance_id
            or response.get("command_exit_status") != 0
        ):
            raise OperationError("recorded Vast destroy response is invalid")
        prior_exit_zero = True
        if not force:
            return True
    try:
        result = completed_process(
            ["vastai", "destroy", "instance", instance_id, "-y", "--raw"]
        )
    except OperationError as error:
        errors = context.path("launch/destroy-request-errors")
        errors.mkdir(parents=True, exist_ok=True, mode=0o700)
        sequence = len(list(errors.glob("[0-9][0-9][0-9].log"))) + 1
        atomic_bytes(
            errors / f"{sequence:03d}.log",
            f"{utc_text()} {error}\n".encode("utf-8"),
        )
        return prior_exit_zero
    response = {
        "schema_version": 1,
        "instance_id": instance_id,
        "command_exit_status": 0,
        "stdout_bytes": len(result.stdout),
        "stdout_sha256": hashlib.sha256(result.stdout).hexdigest(),
        "acknowledged_at_utc": utc_text(),
    }
    attempts = context.path("launch/destroy-request-attempts")
    attempts.mkdir(parents=True, exist_ok=True, mode=0o700)
    sequence = len(list(attempts.glob("[0-9][0-9][0-9].json"))) + 1
    atomic_json(attempts / f"{sequence:03d}.json", response)
    if not response_path.exists():
        atomic_json(response_path, response)
    return True


def destroy_instance(context: Context, instance_id: str) -> dict[str, object]:
    proof_path = context.path("launch/destruction-confirmation.json")
    if proof_path.exists():
        proof = read_json(proof_path)
        if not isinstance(proof, dict) or proof.get("instance_id") != instance_id:
            raise OperationError("destruction proof is invalid")
        return proof
    if command_requires_completion(context):
        verify_completion_review(context, instance_id, None)
    live = sanitized_live_instances()
    matches = [row for row in live if str(row.get("id")) == instance_id]
    label_matches = [row for row in live if row.get("label") == context.label]
    if len(matches) > 1:
        raise OperationError("provider inventory repeats the instance being destroyed")
    if len(label_matches) > 1 or (
        label_matches and str(label_matches[0].get("id")) != instance_id
    ):
        raise OperationError("destroy ownership label resolves to another live instance")
    observed = verify_destroy_ownership(
        context, instance_id, matches[0] if matches else None
    )
    request_exit_zero = context.path("launch/destroy-response.json").exists()
    if (
        matches
        or not observed
        or context.path("launch/destroy-request-attempted.json").exists()
        or context.path("launch/destroy-response.json").exists()
    ):
        request_exit_zero = invoke_destroy_request(context, instance_id)
    attempts = context.timing_value("destroy_attempts")
    interval = context.timing_value("destroy_poll_seconds")
    last_inventory: list[dict[str, object]] | None = None
    consecutive_absences = 0
    for attempt in range(attempts):
        try:
            last_inventory = sanitized_live_instances()
        except OperationError:
            last_inventory = None
        current_matches = [] if last_inventory is None else [
            row for row in last_inventory if str(row.get("id")) == instance_id
        ]
        if last_inventory is not None and not current_matches:
            consecutive_absences += 1
            required_absences = (
                min(2, attempts) if request_exit_zero or observed else attempts
            )
            if consecutive_absences >= required_absences:
                destroyed_path = context.path("launch/destroyed-at.txt")
                if destroyed_path.exists():
                    destroyed_at = destroyed_path.read_text(encoding="utf-8").strip()
                    parse_utc(destroyed_at, "destroyed time")
                else:
                    destroyed_at = utc_text()
                    atomic_bytes(
                        destroyed_path,
                        f"{destroyed_at}\n".encode("utf-8"),
                    )
                proof = {
                    "schema_version": 1,
                    "instance_id": instance_id,
                    "absent_from_complete_inventory": True,
                    "absence_observations": consecutive_absences,
                    "destroy_request_attempted": context.path(
                        "launch/destroy-request-attempted.json"
                    ).exists(),
                    "destroy_request_exit_zero": request_exit_zero,
                    "instance_previously_observed": observed,
                    "inventory": last_inventory,
                    "destroyed_at_utc": destroyed_at,
                }
                atomic_json(proof_path, proof)
                return proof
        elif current_matches:
            consecutive_absences = 0
        if current_matches and attempt + 1 < attempts:
            verify_destroy_ownership(context, instance_id, current_matches[0])
            request_exit_zero = invoke_destroy_request(
                context, instance_id, force=True
            ) or request_exit_zero
        if interval:
            time.sleep(interval)
    raise OperationError("instance destruction is unresolved; it may still be billing")


def parse_utc(value: str, field: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
    except (TypeError, ValueError) as error:
        raise OperationError(f"{field} is not an exact UTC timestamp") from error


def active_invoice_cycle(context: Context) -> tuple[str, Path]:
    pointer = context.path("launch/current-invoice-cycle.json")
    if pointer.exists():
        document = read_json(pointer)
        if not isinstance(document, dict) or not isinstance(
            document.get("cycle_id"), str
        ):
            raise OperationError("current invoice-cycle receipt is invalid")
        cycle_id = document["cycle_id"]
        cycle = context.path(f"launch/invoice-cycles/{cycle_id}")
        if cycle.is_dir() and not (cycle / "rejected.json").exists():
            return cycle_id, cycle
    directory = context.path("launch/invoice-cycles")
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    existing = [
        int(path.name)
        for path in directory.iterdir()
        if path.is_dir() and path.name.isdecimal()
    ]
    cycle_id = f"{(max(existing) + 1) if existing else 1:03d}"
    cycle = directory / cycle_id
    cycle.mkdir(mode=0o700)
    atomic_json(
        pointer,
        {"schema_version": 1, "cycle_id": cycle_id, "started_at_utc": utc_text()},
        replace=pointer.exists(),
    )
    return cycle_id, cycle


def reject_invoice_cycle(cycle: Path, reason: str) -> None:
    atomic_json(
        cycle / "rejected.json",
        {"schema_version": 1, "reason": reason, "rejected_at_utc": utc_text()},
    )


def fetch_invoice_snapshot(
    context: Context, cycle: Path, name: str, instance_id: str
) -> tuple[Path, str] | None:
    snapshot = cycle / name
    snapshot.mkdir(parents=True, exist_ok=True, mode=0o700)
    merged = snapshot / "invoice.json"
    observed = snapshot / "observed-at.txt"
    if merged.exists() and observed.exists():
        try:
            full_build_package.exact_instance_invoice_rows(
                merged, instance_id, context.label
            )
        except ValueError as error:
            if "not available yet" in str(error):
                reject_invoice_cycle(cycle, str(error))
                return None
            raise OperationError(f"recorded invoice snapshot is invalid: {error}") from error
        return merged, observed.read_text(encoding="utf-8").strip()
    pages_dir = snapshot / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    start_date = context.path("launch/invoice-start-date.txt").read_text(
        encoding="utf-8"
    ).strip()
    end_date = (utc_now().date() + timedelta(days=1)).isoformat()
    pages: list[Path] = []
    next_token: str | None = None
    for index in range(1, 1001):
        page = pages_dir / f"{index:06d}.json"
        arguments = [
            "show",
            "invoices-v1",
            "--charges",
            "--charge-type",
            "instance",
            "--start-date",
            start_date,
            "--end-date",
            end_date,
            "--limit",
            "100",
            "--latest-first",
            "--raw",
        ]
        if next_token is not None:
            arguments.extend(["--next-token", next_token])
        if page.exists():
            document = read_json(page)
        else:
            attempts = context.timing_value("invoice_retry_attempts")
            interval = context.timing_value("invoice_retry_seconds")
            document = None
            for retry in range(attempts):
                try:
                    document = vast_json(arguments)
                    break
                except OperationError:
                    if retry + 1 == attempts:
                        raise
                    if interval:
                        time.sleep(interval)
            assert document is not None
            temporary = page.with_name(f".{page.name}.fetched")
            atomic_json(temporary, document)
            try:
                full_build_package.validate_provider_invoice_page(temporary)
            except ValueError as error:
                temporary.unlink(missing_ok=True)
                raise OperationError(f"provider invoice page is invalid: {error}") from error
            os.replace(temporary, page)
            sync_directory(page.parent)
        try:
            validated = full_build_package.validate_provider_invoice_page(page)
        except ValueError as error:
            raise OperationError(f"provider invoice page is invalid: {error}") from error
        pages.append(page)
        value = validated.get("next_token")
        if value is None:
            break
        if not isinstance(value, str) or not value:
            raise OperationError("provider invoice continuation token is invalid")
        next_token = value
    else:
        raise OperationError("provider invoice pagination did not terminate")
    try:
        full_build_package.merge_provider_invoice_pages(pages, merged)
        full_build_package.exact_instance_invoice_rows(
            merged, instance_id, context.label
        )
    except ValueError as error:
        if "not available yet" in str(error):
            reject_invoice_cycle(cycle, str(error))
            return None
        raise OperationError(f"provider invoice is not complete: {error}") from error
    observed_at = utc_text()
    atomic_bytes(observed, f"{observed_at}\n".encode("utf-8"))
    return merged, observed_at


def ensure_final_charge(
    context: Context, instance_id: str
) -> dict[str, object] | None:
    output = context.path("launch/provider-final-charge.json")
    if output.exists():
        document = read_json(output)
        if not isinstance(document, dict) or not isinstance(
            document.get("actual_charge_micro_usd"), int
        ):
            raise OperationError("provider final charge receipt is invalid")
        return document
    destroyed = context.path("launch/destroyed-at.txt").read_text(
        encoding="utf-8"
    ).strip()
    not_before = parse_utc(destroyed, "destroyed time") + timedelta(
        seconds=context.timing_value("invoice_not_before_seconds")
    )
    atomic_bytes(
        context.path("launch/invoice-not-before-utc.txt"),
        f"{utc_text(not_before)}\n".encode("utf-8"),
    )
    if utc_now() < not_before:
        return None
    _cycle_id, cycle = active_invoice_cycle(context)
    first_result = fetch_invoice_snapshot(context, cycle, "first", instance_id)
    if first_result is None:
        return None
    first, first_observed = first_result
    first_time = parse_utc(first_observed, "first invoice observation")
    confirmation_delay = context.timing_value("invoice_confirmation_seconds")
    if utc_now() < first_time + timedelta(seconds=confirmation_delay):
        return None
    confirmation_result = fetch_invoice_snapshot(
        context, cycle, "confirmation", instance_id
    )
    if confirmation_result is None:
        return None
    confirmation, confirmation_observed = confirmation_result
    try:
        rows, amount, rows_sha = full_build_package.exact_instance_invoice_rows(
            first, instance_id, context.label
        )
        _, confirmation_amount, confirmation_rows_sha = (
            full_build_package.exact_instance_invoice_rows(
                confirmation, instance_id, context.label
            )
        )
    except ValueError as error:
        raise OperationError(f"provider invoice is not final: {error}") from error
    if amount != confirmation_amount or rows_sha != confirmation_rows_sha:
        reject_invoice_cycle(
            cycle, "provider invoice changed between its two observations"
        )
        return None
    micro = amount * Decimal(1_000_000)
    if micro != micro.to_integral_value():
        raise OperationError("provider invoice charge is not exact to micro-USD")
    result = {
        "schema_version": 1,
        "instance_id": instance_id,
        "label": context.label,
        "actual_charge_micro_usd": int(micro),
        "invoice_rows": len(rows),
        "exact_instance_rows_sha256": rows_sha,
        "invoice_not_before_utc": utc_text(not_before),
        "invoice_observed_at_utc": first_observed,
        "confirmation_observed_at_utc": confirmation_observed,
        "invoice_snapshot_sha256": sha256_file(first),
        "confirmation_invoice_snapshot_sha256": sha256_file(confirmation),
        "invoice_cycle": cycle.name,
    }
    atomic_copy(first, context.path("launch/provider-final-invoice-first.json"))
    atomic_copy(
        confirmation,
        context.path("launch/provider-final-invoice-confirmation.json"),
    )
    atomic_copy(
        cycle / "first/observed-at.txt",
        context.path("launch/provider-final-invoice-first-observed-at.txt"),
    )
    atomic_copy(
        cycle / "confirmation/observed-at.txt",
        context.path("launch/provider-final-invoice-confirmation-observed-at.txt"),
    )
    atomic_json(output, result)
    return result


def invoice_pending_fields(context: Context) -> dict[str, object]:
    not_before_path = context.path("launch/invoice-not-before-utc.txt")
    if not not_before_path.is_file():
        raise OperationError("invoice wait state has no eligibility time")
    next_eligible = parse_utc(
        not_before_path.read_text(encoding="utf-8").strip(),
        "invoice eligibility time",
    )
    cycles = context.path("launch/invoice-cycles")
    first_observations = sorted(cycles.glob("*/first/observed-at.txt")) if cycles.exists() else []
    if first_observations:
        first = parse_utc(
            first_observations[-1].read_text(encoding="utf-8").strip(),
            "first invoice observation",
        )
        next_eligible = max(
            next_eligible,
            first
            + timedelta(
                seconds=context.timing_value("invoice_confirmation_seconds")
            ),
        )
    if next_eligible <= utc_now():
        next_eligible = utc_now() + timedelta(
            seconds=context.timing_value("invoice_retry_seconds")
        )
    return {"next_eligible_observation_utc": utc_text(next_eligible)}


def invoice_pending_result(
    context: Context, instance_id: str
) -> dict[str, object]:
    return {
        "state": "invoice_pending",
        "instance_id": instance_id,
        **invoice_pending_fields(context),
    }


def rewrite_settlement_config(source: Path, destination: Path, stage: str) -> None:
    document = read_json(source)
    if not isinstance(document, dict):
        raise OperationError("full-build config is invalid")
    for section in ("calibration", "full_build"):
        value = document.get(section)
        if isinstance(value, dict) and "ledger_path" in value:
            value["ledger_path"] = f"{stage}/budget-ledger.json"
    atomic_json(destination, document)


def settlement_layout(context: Context) -> tuple[str, bool]:
    if context.path("result").is_dir():
        return "result", (context.path("result/audit/local-verification.json").is_file())
    invocation = context.path("launch/worker-invocations")
    if invocation.is_dir() and any(invocation.glob("[0-9][0-9][0-9].json")):
        if not context.path("launch/retrieval-verification.json").is_file():
            raise OperationError(
                "claimed remote ledger is not retrieved; settlement cannot continue"
            )
        return "result.next", False
    if not (
        context.path("launch/preclaim-failure.log").is_file()
        or context.path("launch/preworker-instance-failure.log").is_file()
    ):
        raise OperationError("failure settlement has no durable failure evidence")
    return "execution", False


def failure_evidence(context: Context, layout: str) -> str:
    if layout == "execution":
        if context.path("launch/preworker-instance-failure.log").is_file():
            return "../launch/preworker-instance-failure.log"
        return "../launch/preclaim-failure.log"
    attempt_id = last_attempt_id(context)
    if attempt_id is None:
        raise OperationError("worker failure has no attempt identity")
    attempt = context.path(f"{layout}/work/full-build-attempts/{attempt_id}")
    terminal = terminal_state(attempt)
    if terminal is None:
        raise OperationError("worker failure has no terminal evidence")
    if terminal["kind"] == "full-build.exit" and terminal.get("exit_status") == 0:
        path = context.path(f"{layout}/audit/local-verification-failure.log")
        if not path.is_file():
            raise OperationError("zero-exit worker failure lacks local verification evidence")
        return "audit/local-verification-failure.log"
    return f"work/full-build-attempts/{attempt_id}/{terminal['kind']}"


def existing_settlement(context: Context) -> str | None:
    layouts = [
        layout
        for layout in ("result", "result.next", "execution")
        if context.path(f"{layout}/settlement").is_dir()
    ]
    if len(layouts) > 1:
        raise OperationError("more than one published settlement exists")
    return layouts[0] if layouts else None


def finish_settlement(context: Context, layout: str) -> dict[str, object]:
    published = context.path(f"{layout}/settlement")
    try:
        full_build_package.verify_manifest(
            published, published / "settlement-manifest.json"
        )
    except (OSError, ValueError) as error:
        raise OperationError(f"published settlement is invalid: {error}") from error
    result = read_json(published / "settlement-result.json")
    if not isinstance(result, dict) or not isinstance(result.get("ledger_sha256"), str):
        raise OperationError("published settlement result is invalid")
    require_sha256(result["ledger_sha256"], "settlement ledger")
    settled_ledger = published / "budget-ledger.json"
    if sha256_file(settled_ledger) != result["ledger_sha256"]:
        raise OperationError("published settlement ledger differs from its receipt")
    atomic_json(context.path("launch/settlement-result.json"), result)
    if layout == "execution":
        destination = context.path("result.next/settlement")
        if destination.exists():
            raise OperationError("result.next already contains another settlement")
        os.replace(published, destination)
        sync_directory(destination.parent)
        layout = "result.next"
    if layout == "result.next":
        if context.path("result").exists():
            raise OperationError("cannot publish result.next over an existing result")
        os.replace(context.path("result.next"), context.path("result"))
        sync_directory(context.root)
    published = context.path("result/settlement")
    settled_ledger = published / "budget-ledger.json"
    reservation = read_json(context.path("launch/full-build-reservation.json"))
    if not isinstance(reservation, dict) or not isinstance(
        reservation.get("ledger_sha256"), str
    ):
        raise OperationError("reservation receipt is invalid at ledger publication")
    require_sha256(reservation["ledger_sha256"], "reservation ledger")
    replace_from_expected(
        settled_ledger,
        context.ledger,
        allowed_existing_sha256={reservation["ledger_sha256"]},
    )
    if sha256_file(context.ledger) != result["ledger_sha256"]:
        raise OperationError("canonical ledger publication failed")
    try:
        full_build_package.verify_manifest(
            published, published / "settlement-manifest.json"
        )
    except (OSError, ValueError) as error:
        raise OperationError(f"final settlement verification failed: {error}") from error
    shutil.rmtree(context.path("launch/ssh"), ignore_errors=True)
    return {"state": "settled", "settlement": result}


def settlement_summary_from_ledger(
    context: Context,
    stage: Path,
    operation: str,
    actual_charge_micro_usd: int,
    recorded_at_utc: str,
) -> dict[str, object]:
    ledger_path = stage / "budget-ledger.json"
    before_path = stage / "pre-settlement-budget-ledger.json"
    document = read_json(ledger_path)
    config = read_json(stage / "full-build-config.json")
    if not isinstance(document, dict) or not isinstance(config, dict):
        raise OperationError("interrupted settlement state is invalid")
    full_build = config.get("full_build")
    if not isinstance(full_build, dict) or not isinstance(
        full_build.get("reservation_id"), str
    ):
        raise OperationError("settlement config has no reservation identity")
    reservation_id = full_build["reservation_id"]
    kind = (
        "full_build_settlement"
        if operation == "settle-full-build"
        else "failed_full_build_settlement"
    )
    entries = document.get("entries")
    if not isinstance(entries, list):
        raise OperationError("settled ledger has no entry list")
    matches = [
        entry
        for entry in entries
        if isinstance(entry, dict)
        and entry.get("kind") == kind
        and entry.get("reservation_id") == reservation_id
    ]
    if len(matches) != 1:
        raise OperationError("interrupted settlement ledger is not uniquely settled")
    entry = matches[0]
    if (
        entry.get("previous_ledger_sha256") != sha256_file(before_path)
        or entry.get("actual_charge_micro_usd") != actual_charge_micro_usd
        or entry.get("recorded_at_utc") != recorded_at_utc
    ):
        raise OperationError("interrupted settlement entry differs from its invocation")

    def cents(field: str) -> int:
        value = document.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise OperationError(f"settled ledger field is invalid: {field}")
        return value * 10_000

    return {
        "ledger_sha256": sha256_file(ledger_path),
        "lifetime_cap_micro_usd": cents("lifetime_cap_cents"),
        "actual_spend_micro_usd": cents("actual_spend_cents"),
        "outstanding_commitments_micro_usd": cents(
            "outstanding_commitments_cents"
        ),
        "calibration_actual_spend_micro_usd": cents(
            "calibration_actual_spend_cents"
        ),
        "calibration_outstanding_commitments_micro_usd": cents(
            "calibration_outstanding_commitments_cents"
        ),
    }


def run_settlement_controller(
    context: Context,
    layout: str,
    stage: Path,
    operation: str,
    arguments: list[str],
    actual_charge_micro_usd: int,
) -> dict[str, object]:
    result_path = stage / "settlement-result.json"
    if result_path.exists():
        result = read_json(result_path)
        if not isinstance(result, dict):
            raise OperationError("staged settlement result is invalid")
        return result
    recorded_path = stage / "settled-at.txt"
    if recorded_path.exists():
        recorded_at_utc = recorded_path.read_text(encoding="utf-8").strip()
        parse_utc(recorded_at_utc, "settlement time")
    else:
        recorded_at_utc = utc_text()
        atomic_bytes(recorded_path, f"{recorded_at_utc}\n".encode("utf-8"))
    arguments = [*arguments, str(actual_charge_micro_usd), recorded_at_utc]
    before = stage / "pre-settlement-budget-ledger.json"
    ledger = stage / "budget-ledger.json"
    output = stage / "settlement-result.json.next"
    lock_path = stage / "controller.lock"
    with file_lock(lock_path, blocking=False) as lock:
        if output.is_file():
            try:
                candidate = read_json(output)
            except OperationError:
                candidate = None
            if isinstance(candidate, dict) and candidate.get("ledger_sha256") == sha256_file(
                ledger
            ):
                os.replace(output, result_path)
                sync_directory(stage)
                return candidate
            output.unlink()
        if sha256_file(ledger) != sha256_file(before):
            result = settlement_summary_from_ledger(
                context,
                stage,
                operation,
                actual_charge_micro_usd,
                recorded_at_utc,
            )
            atomic_json(result_path, result)
            return result
        atomic_json(
            stage / "controller-invocation.json",
            {
                "schema_version": 1,
                "operation": operation,
                "arguments": arguments,
                "recorded_at_utc": recorded_at_utc,
            },
        )
        stderr = (stage / "controller.stderr").open("ab", buffering=0)
        stdout = output.open("xb", buffering=0)
        try:
            child = subprocess.Popen(
                context.controller_arguments(layout, [operation, *arguments]),
                stdin=subprocess.DEVNULL,
                stdout=stdout,
                stderr=stderr,
                start_new_session=True,
                close_fds=True,
                pass_fds=(lock.fileno(),),
            )
        except OSError as error:
            raise OperationError(f"could not start settlement controller: {error}") from error
        finally:
            stdout.close()
            stderr.close()
        atomic_bytes(stage / "controller.pid", f"{child.pid}\n".encode("utf-8"))
        status = child.wait()
        atomic_bytes(stage / "controller.exit", f"{status}\n".encode("utf-8"))
        if status != 0:
            if sha256_file(ledger) != sha256_file(before):
                result = settlement_summary_from_ledger(
                    context,
                    stage,
                    operation,
                    actual_charge_micro_usd,
                    recorded_at_utc,
                )
                atomic_json(result_path, result)
                return result
            raise OperationError("settlement controller failed before changing its ledger")
        candidate = read_json(output)
        if not isinstance(candidate, dict):
            raise OperationError("settlement controller returned an invalid result")
        os.replace(output, result_path)
        sync_directory(stage)
        return candidate


def recoverable_settlement_stage(root: Path) -> Path | None:
    attempts = root / "settlement-attempts"
    if not attempts.is_dir():
        return None
    recoverable = []
    for stage in sorted(path for path in attempts.iterdir() if path.is_dir()):
        required = (
            stage / "budget-ledger.json",
            stage / "pre-settlement-budget-ledger.json",
            stage / "full-build-config.json",
        )
        if all(path.is_file() for path in required):
            recoverable.append(stage)
    if len(recoverable) > 1:
        raise OperationError("more than one initialized settlement attempt exists")
    return recoverable[0] if recoverable else None


def finish_settlement_stage(context: Context, root: Path, stage: Path) -> None:
    attempt_id = stage.name
    for relative in (
        "launch/provider-final-charge.json",
        "launch/provider-final-invoice-first.json",
        "launch/provider-final-invoice-confirmation.json",
        "launch/invoice-not-before-utc.txt",
        "launch/provider-final-invoice-first-observed-at.txt",
        "launch/provider-final-invoice-confirmation-observed-at.txt",
        "launch/destruction-confirmation.json",
        "launch/destroyed-at.txt",
    ):
        source = context.path(relative)
        if source.is_file():
            atomic_copy(source, stage / source.name)
    try:
        full_build_package.write_manifest(
            stage,
            stage / "settlement-manifest.json",
            "gte-full-build-settlement",
        )
        full_build_package.verify_manifest(stage, stage / "settlement-manifest.json")
    except (OSError, ValueError) as error:
        raise OperationError(f"settlement package verification failed: {error}") from error
    os.replace(stage, root / "settlement")
    sync_directory(root)
    audit = root / "settlement-attempts" / attempt_id
    audit.mkdir(mode=0o700)
    atomic_json(
        audit / "published.json",
        {
            "schema_version": 1,
            "published_as": "settlement",
            "settlement_manifest_sha256": sha256_file(
                root / "settlement/settlement-manifest.json"
            ),
        },
    )


def settle(context: Context) -> dict[str, object]:
    if context.command_workload:
        charge = read_json(context.path("launch/provider-final-charge.json"))
        return {"state": "ledger_reconciliation_required", "billing_possible": False,
                "instance_id": recorded_instance_id(context), "provider_final_charge": charge,
                "canonical_ledger_path": str(context.ledger)}
    existing = existing_settlement(context)
    if existing is not None:
        return finish_settlement(context, existing)
    charge = read_json(context.path("launch/provider-final-charge.json"))
    if not isinstance(charge, dict) or not isinstance(
        charge.get("actual_charge_micro_usd"), int
    ):
        raise OperationError("provider final charge is invalid")
    layout, success = settlement_layout(context)
    root = context.path(layout)
    published = root / "settlement"
    if not published.exists():
        stage = recoverable_settlement_stage(root)
        if stage is None:
            attempt_id = f"{utc_now().strftime('%Y%m%dT%H%M%S')}-{time.time_ns()}"
            stage_relative = f"settlement-attempts/{attempt_id}"
            stage = root / stage_relative
            stage.mkdir(parents=True, mode=0o700)
            source_ledger = root / "work/budget-ledger.json"
            if not source_ledger.is_file():
                raise OperationError("settlement source ledger is missing")
            atomic_copy(source_ledger, stage / "pre-settlement-budget-ledger.json")
            atomic_copy(source_ledger, stage / "budget-ledger.json")
            rewrite_settlement_config(
                root / "package/run/full-build-config.json",
                stage / "full-build-config.json",
                stage_relative,
            )
        else:
            stage_relative = stage.relative_to(root).as_posix()
        arguments = [stage_relative + "/full-build-config.json"]
        operation = "settle-full-build"
        if not success:
            operation = "settle-failed-full-build"
            arguments.append(failure_evidence(context, layout))
        result = run_settlement_controller(
            context,
            layout,
            stage,
            operation,
            arguments,
            charge["actual_charge_micro_usd"],
        )
        if not isinstance(result, dict) or not isinstance(result.get("ledger_sha256"), str):
            raise OperationError("controller settlement result is invalid")
        require_sha256(result["ledger_sha256"], "settlement ledger")
        if sha256_file(stage / "budget-ledger.json") != result["ledger_sha256"]:
            raise OperationError("settlement ledger does not match the controller receipt")
        if not (stage / "settlement-result.json").exists():
            atomic_json(stage / "settlement-result.json", result)
        finish_settlement_stage(context, root, stage)
    return finish_settlement(context, layout)


def settle_preclaim_failure(context: Context) -> dict[str, object]:
    if not context.path("launch/provider-final-charge.json").exists():
        write_preclaim_failure(context, "provider rejected the instance before creation")
    return settle(context)


def preserved_instance_result(context: Context, instance_id: str) -> dict[str, object]:
    return {
        "state": "retrieved" if context.path("launch/retrieval-verification.json").exists() else "manual_stop_required",
        "instance_id": instance_id,
        "instance_preserved": True,
        "billing_possible": True,
        "manual_stop_recommended": True,
    }


def cleanup_preworker_instance(
    context: Context, instance_id: str, *, delete: bool = True,
) -> dict[str, object]:
    failure = context.path("launch/preworker-instance-failure.log")
    if not failure.exists():
        atomic_bytes(
            failure,
            f"{utc_text()} pre-worker instance cleanup\n".encode("utf-8"),
        )
    if not delete:
        return preserved_instance_result(context, instance_id)
    destroy_instance(context, instance_id)
    charge = ensure_final_charge(context, instance_id)
    if charge is None:
        return invoice_pending_result(context, instance_id)
    return settle(context)


def ledger_reconciliation_state(
    context: Context, instance_id: str, *, delete: bool = True,
) -> dict[str, object]:
    evidence = context.path("launch/result-loss-ledger-reconciliation.json")
    document = read_json(evidence)
    if not isinstance(document, dict) or document.get("instance_id") != instance_id:
        raise OperationError("result-loss reconciliation evidence is invalid")
    if not context.path("launch/destruction-confirmation.json").exists():
        if not delete:
            return preserved_instance_result(context, instance_id)
        destroy_instance(context, instance_id)
    charge = ensure_final_charge(context, instance_id)
    if charge is None:
        return {
            "state": "invoice_pending",
            "instance_id": instance_id,
            "ledger_reconciliation_required": True,
            **invoice_pending_fields(context),
        }
    return {
        "state": "ledger_reconciliation_required",
        "instance_id": instance_id,
        "actual_charge_micro_usd": charge["actual_charge_micro_usd"],
        "evidence": str(evidence),
    }


def destroy_without_remote_retrieval(
    context: Context, instance_id: str, attempt_id: str, reason: str, *, delete: bool = True,
) -> dict[str, object]:
    if not delete:
        return {**preserved_instance_result(context, instance_id), "retrieval_error": reason}
    evidence = context.path("launch/result-loss-ledger-reconciliation.json")
    if not evidence.exists():
        atomic_json(
            evidence,
            {
                "schema_version": 1,
                "instance_id": instance_id,
                "attempt_id": attempt_id,
                "result_lost": True,
                "claimed_remote_ledger_irretrievable": True,
                "reason": reason,
                "recorded_at_utc": utc_text(),
            },
        )
    return ledger_reconciliation_state(context, instance_id)


def cleanup_terminal(
    context: Context,
    instance_id: str,
    private_key: Path,
    target: list[str],
    attempt_id: str,
    remote: dict[str, object],
    *, delete: bool = True,
) -> dict[str, object]:
    del remote
    ensure_retrieved(context, instance_id, private_key, target, attempt_id)
    publish_verified_result(context, attempt_id)
    if not delete:
        return preserved_instance_result(context, instance_id)
    destroy_instance(context, instance_id)
    charge = ensure_final_charge(context, instance_id)
    if charge is None:
        return invoice_pending_result(context, instance_id)
    return settle(context)


def recorded_offer(context: Context) -> dict[str, object]:
    document = read_json(context.path("launch/offer.json"))
    if not isinstance(document, list) or len(document) != 1 or not isinstance(
        document[0], dict
    ):
        raise OperationError("recorded approved offer is invalid")
    return document[0]


def recorded_instance_id(context: Context) -> str | None:
    path = context.path("launch/create-result.json")
    if not path.exists():
        return None
    try:
        return calibration_package.created_instance_id(read_json(path))
    except ValueError as error:
        raise OperationError(f"create result is invalid: {error}") from error


def worker_status(
    context: Context,
    private_key: Path,
    target: list[str],
    attempt_id: str,
) -> dict[str, object]:
    response = remote_json(
        context,
        private_key,
        target,
        "_remote-status",
        "--attempt",
        attempt_id,
    )
    if not isinstance(response, dict):
        raise OperationError("remote worker status is invalid")
    state = response.get("state", response.get("remote_status"))
    if state not in ("absent", "starting", "running", "terminal", "orphaned"):
        raise OperationError("remote worker status has an unknown state")
    normalized = dict(response)
    normalized["state"] = state
    if context.command_workload:
        atomic_json(context.path(f"observations/{time.time_ns()}-{attempt_id}.json"),
                    {"observed_at_utc": utc_text(), "attempt_id": attempt_id, "remote": normalized})
    return normalized


def current_state(context: Context) -> str:
    if context.path("result/settlement/settlement-result.json").is_file():
        settlement = read_json(
            context.path("result/settlement/settlement-result.json")
        )
        if not isinstance(settlement, dict) or not isinstance(
            settlement.get("ledger_sha256"), str
        ):
            raise OperationError("published settlement receipt is invalid")
        expected = require_sha256(
            settlement["ledger_sha256"], "published settlement ledger"
        )
        if not context.ledger.is_file() or sha256_file(context.ledger) != expected:
            raise OperationError(
                "published settlement ledger differs from the canonical ledger"
            )
        return "settled"
    if context.path("launch/result-loss-ledger-reconciliation.json").is_file():
        return (
            "ledger_reconciliation_required"
            if context.path("launch/provider-final-charge.json").is_file()
            else "invoice_pending"
        )
    if context.path("launch/provider-final-charge.json").is_file():
        return "invoice_final"
    if context.path("launch/destruction-confirmation.json").is_file():
        return "invoice_pending"
    if context.path("launch/retrieval-verification.json").is_file():
        return "retrieved"
    if context.path("launch/worker-started.json").is_file():
        return "worker_started"
    if context.path("launch/remote-prepared.json").is_file():
        return "remote_prepared"
    if context.path("launch/instance.json").is_file():
        return "instance_verified"
    if context.path("launch/create-request-attempted.txt").is_file():
        return "create_requested"
    if context.path("launch/full-build-reservation.json").is_file():
        return "reserved"
    if context.path("launch/approval.json").is_file():
        return "approved"
    if context.approval_dir.is_dir() and any(context.approval_dir.glob("*.json")):
        return "awaiting_approval"
    return "unprepared"


def status_once(context: Context) -> dict[str, object]:
    state = current_state(context)
    instance_id = recorded_instance_id(context)
    definitive_preclaim_rejection = False
    if (
        instance_id is None
        and context.path("launch/preclaim-failure.log").is_file()
        and context.path("launch/provider-final-charge.json").is_file()
    ):
        charge = read_json(context.path("launch/provider-final-charge.json"))
        if not isinstance(charge, dict) or charge.get(
            "actual_charge_micro_usd"
        ) != 0:
            raise OperationError("preclaim provider charge evidence is invalid")
        definitive_preclaim_rejection = True
    billing_possible = (
        context.path("launch/create-request-attempted.txt").exists()
        and not context.path("launch/destruction-confirmation.json").exists()
        and not definitive_preclaim_rejection
    )
    result: dict[str, object] = {
        "state": state,
        "billing_possible": billing_possible,
    }
    if context.path("progressive/status.json").exists():
        result["progressive_copy"] = read_json(context.path("progressive/status.json"))
    if context.path("launch/result-loss-ledger-reconciliation.json").is_file():
        result["ledger_reconciliation_required"] = True
    attempt_id = last_attempt_id(context)
    if instance_id is None or context.path("launch/destruction-confirmation.json").exists():
        if state == "invoice_pending" and context.path(
            "launch/invoice-not-before-utc.txt"
        ).is_file():
            result.update(invoice_pending_fields(context))
        return result
    raw = vast_json(["show", "instance", instance_id, "--raw"])
    try:
        provider = calibration_package.freeze_instance_record(
            read_json(context.path("launch/create-result.json")), raw
        )
    except ValueError as error:
        raise OperationError(f"live instance status is invalid: {error}") from error
    result["instance"] = provider
    try:
        result["cost"] = cost_record_from_instance(context, instance_id, raw)
    except OperationError as error:
        result["cost_error"] = str(error)
        result["manual_stop_recommended"] = None
    if attempt_id is not None and context.path("launch/ssh/id_ed25519").is_file():
        private = context.path("launch/ssh/id_ed25519")
        target = resolve_ssh_target(context, instance_id, raw)
        remote = worker_status(context, private, target, attempt_id)
        result["remote"] = remote
        if remote["state"] in ("running", "starting"):
            result["state"] = "running"
        elif remote["state"] in ("terminal", "orphaned"):
            result["state"] = "terminal"
    cost = result.get("cost")
    if isinstance(cost, dict) and isinstance(
        cost.get("estimated_total_micro_usd"), int
    ):
        result["manual_stop_recommended"] = (
            cost["estimated_total_micro_usd"]
            >= context.limit("manual_stop_cost_micro_usd")
        )
    return result


def prepare(context: Context) -> dict[str, object]:
    if context.command_workload:
        return prepare_command_plan(context)
    with operation_lock(context.root):
        verify_reviewed_artifacts(context)
        verify_local_ssh(context)
        verify_image(context)
        completed_process(["tar", "--version"])
        ledger_sha256 = verify_baseline_ledgers(context)
        descriptor = context.controller(
            "execution",
            ["describe-representation", "package/run/full-build-config.json"],
        )
        if not isinstance(descriptor, dict) or descriptor.get(
            "descriptor_sha256"
        ) != context.pin("descriptor_sha256"):
            raise OperationError("offline descriptor differs from the frozen representation")
        query, offer = select_offer(context)
        if any(row.get("label") == context.label for row in sanitized_live_instances()):
            raise OperationError("a live instance already uses the full-build label")
        non_compute = {
            "artifact_storage_and_transfer_micro_usd": context.limit(
                "artifact_storage_and_transfer_micro_usd"
            ),
            "one_cold_restart_micro_usd": context.limit(
                "one_cold_restart_micro_usd"
            ),
            "one_lost_shard_micro_usd": context.limit("one_lost_shard_micro_usd"),
        }
        non_compute_path = context.path("launch/full-build-non-compute-costs.json")
        atomic_json(non_compute_path, non_compute)
        projection = context.controller(
            "execution",
            [
                "project-full-build",
                "package/run/full-build-config.json",
                "../launch/full-build-non-compute-costs.json",
            ],
        )
        ensure_retrieval_destination(context)
        plan = plan_document(context, query, offer, projection, ledger_sha256)
        encoded = canonical_json(plan)
        digest = hashlib.sha256(encoded).hexdigest()
        plan_path = context.approval_dir / f"{digest}.json"
        atomic_bytes(plan_path, encoded)
        return {
            "state": "awaiting_approval",
            "paid_action_performed": False,
            "approval_sha256": digest,
            "plan": str(plan_path),
            "offer_id": str(offer["id"]),
            "hourly_rate_usd": str(offer["dph_total"]),
            "projected_lifetime_total_micro_usd": projection[
                "projected_lifetime_total_micro_usd"
            ],
            "reservation_ceiling_micro_usd": context.limit(
                "reservation_ceiling_micro_usd"
            ),
        }


def run(context: Context, approval: str | None) -> dict[str, object]:
    with operation_lock(context.root):
        verify_reviewed_artifacts(context)
        if context.path("result/settlement/settlement-result.json").exists():
            return settle(context)
        receipt = approval_receipt(context, approval)
        digest = receipt.get("approval_sha256")
        if not isinstance(digest, str):
            raise OperationError("approval receipt is invalid")
        plan = load_approval_plan(context, digest)
        instance_id = recorded_instance_id(context)
        if context.path("launch/result-loss-ledger-reconciliation.json").exists():
            if instance_id is None:
                raise OperationError("result-loss evidence has no instance identity")
            return ledger_reconciliation_state(context, instance_id, delete=not context.command_workload)
        if context.path("launch/provider-final-charge.json").exists():
            return settle(context)
        if context.path("launch/destruction-confirmation.json").exists():
            if instance_id is None:
                raise OperationError("destroyed instance has no create-result identity")
            charge = ensure_final_charge(context, instance_id)
            if charge is None:
                return invoice_pending_result(context, instance_id)
            return settle(context)
        if context.path("launch/retrieval-verification.json").exists():
            if instance_id is None:
                raise OperationError("retrieved instance has no create-result identity")
            attempt_id = last_attempt_id(context)
            if attempt_id is None:
                raise OperationError("retrieved worker has no attempt identity")
            publish_verified_result(context, attempt_id)
            if context.command_workload:
                return preserved_instance_result(context, instance_id)
            destroy_instance(context, instance_id)
            charge = ensure_final_charge(context, instance_id)
            if charge is None:
                return invoice_pending_result(context, instance_id)
            return settle(context)
        if context.path("launch/preworker-instance-failure.log").exists():
            if instance_id is None:
                raise OperationError("pre-worker instance failure has no instance identity")
            return cleanup_preworker_instance(context, instance_id, delete=not context.command_workload)
        if (
            instance_id is None
            and not context.path("launch/create-request-attempted.txt").exists()
            and not context.path("launch/preclaim-failure.log").exists()
        ):
            verify_local_ssh(context)
        reservation = ensure_reservation(context, plan)
        if (
            context.path("launch/preclaim-failure.log").exists()
            and instance_id is None
        ):
            return settle_preclaim_failure(context)
        if context.path("launch/create-request-attempted.txt").exists():
            offer = recorded_offer(context)
        else:
            offer = refresh_approved_offer(context, plan)
        create_result = ensure_create(context, offer)
        if create_result is None:
            if context.path("launch/preclaim-failure.log").exists():
                return settle_preclaim_failure(context)
            raise OperationError("create did not produce an instance or terminal failure")
        instance_id = calibration_package.created_instance_id(create_result)
        try:
            instance = freeze_running_instance(context, offer, create_result)
        except OperationError as error:
            if not context.path("launch/preworker-instance-failure.log").exists():
                atomic_bytes(
                    context.path("launch/preworker-instance-failure.log"),
                    f"{utc_text()} instance startup failure: {error}\n".encode(
                        "utf-8"
                    ),
                )
            return cleanup_preworker_instance(context, instance_id, delete=not context.command_workload)
        try:
            private_key, target = ensure_ssh(context, instance_id)
        except RemoteAccessUnavailable:
            return {
                "state": "remote_access_pending",
                "instance_id": instance_id,
                "billing_possible": True,
            }
        try:
            remote_receipts = ensure_remote_receipts(
                context,
                plan,
                reservation,
                create_result,
                instance,
            )
            if not ensure_remote_prepared(
                context,
                instance_id,
                private_key,
                target,
                remote_receipts,
            ):
                return {
                    "state": "preparing",
                    "instance_id": instance_id,
                    "billing_possible": True,
                }
            attempt_id = ensure_worker_started(
                context, instance_id, private_key, target
            )
        except RemoteAccessUnavailable:
            return {
                "state": "remote_access_pending",
                "instance_id": instance_id,
                "billing_possible": True,
            }
        except OperationError as error:
            invocations = context.path("launch/worker-invocations")
            if invocations.is_dir() and any(
                invocations.glob("[0-9][0-9][0-9].json")
            ):
                raise
            if not context.path("launch/preworker-instance-failure.log").exists():
                atomic_bytes(
                    context.path("launch/preworker-instance-failure.log"),
                    f"{utc_text()} pre-worker failure: {error}\n".encode("utf-8"),
                )
            return cleanup_preworker_instance(context, instance_id, delete=not context.command_workload)
        remote = worker_status(context, private_key, target, attempt_id)
        if remote["state"] in ("running", "starting"):
            return {
                "state": "running",
                "instance_id": instance_id,
                "attempt_id": attempt_id,
                "remote": remote,
            }
        if remote["state"] in ("terminal", "orphaned"):
            return cleanup_terminal(
                context,
                instance_id,
                private_key,
                target,
                attempt_id,
                remote,
                delete=not context.command_workload,
            )
        raise OperationError("acknowledged worker has no recoverable remote state")


def command_requires_completion(context: Context) -> bool:
    return context.command_workload and context.config["workload"]["work_seconds"] is None


def verify_completion_review(context: Context, instance_id: str | None, incomplete_stop_approval: str | None) -> None:
    """File-transfer verification cannot establish that all required work exists."""
    approval_path = context.path("launch/user-approved-incomplete-stop.json")
    if approval_path.exists():
        approval = read_json(approval_path)
        if (not isinstance(approval, dict) or approval.get("instance_id") != instance_id
                or approval.get("operation_contract_sha256") != sha256_file(context.config_path)
                or not isinstance(approval.get("reason"), str) or not approval["reason"].strip()):
            raise OperationError("recorded incomplete stop approval belongs to another operation")
        return
    if incomplete_stop_approval is not None:
        if not isinstance(incomplete_stop_approval, str) or not incomplete_stop_approval.strip():
            raise OperationError("incomplete stop approval must record the user's reason")
        atomic_json(approval_path,
                    {"instance_id": instance_id, "reason": incomplete_stop_approval,
                     "operation_contract_sha256": sha256_file(context.config_path), "recorded_at_utc": utc_text()})
        return
    review_path = context.path("launch/completion-review.json")
    receipt_path = context.path("launch/retrieval-verification.json")
    if not review_path.is_file() or not receipt_path.is_file():
        raise OperationError("complete locally verified data and a completion review are required before stop")
    review = read_json(review_path)
    receipt = read_json(receipt_path)
    checks = review.get("checks") if isinstance(review, dict) else None
    latest = last_attempt_id(context)
    if (not isinstance(review, dict) or review.get("complete") is not True
            or review.get("instance_id") != instance_id or receipt.get("instance_id") != instance_id
            or latest is not None and receipt.get("attempt_id") != latest
            or review.get("operation_contract_sha256") != sha256_file(context.config_path)
            or review.get("retrieval_verification_sha256") != sha256_file(receipt_path)
            or not isinstance(checks, list) or not checks
            or any(not isinstance(check, str) or not check.strip() for check in checks)):
        raise OperationError("complete data review is missing, stale or belongs to another operation")
    candidate = context.path("result") if context.path("result").is_dir() else context.path("result.next")
    terminal = terminal_state(candidate / f"work/full-build-attempts/{parse_attempt_id(receipt['attempt_id'])}")
    if terminal is None or terminal.get("kind") != "full-build.exit" or terminal.get("exit_status") != 0:
        raise OperationError("complete data review requires a successful retrieved worker")
    verify_command_results(context, candidate)


def run_watch(context: Context, approval: str | None) -> dict[str, object]:
    """Supervise the existing resumable run; no separate provider lifecycle."""
    if not context.command_workload:
        raise OperationError("run --watch requires a command workload")
    verify_reviewed_artifacts(context)
    # A second watcher must fail before it can stop the active operation.
    with file_lock(context.path("watch.lock"), blocking=False):
        path = context.path("launch/watch-deadline.json")
        with operation_lock(context.root):
            if not path.exists():
                seconds = required_positive_int(context.config, "session_seconds") - context.config.get("cleanup_seconds", 0)
                atomic_json(path, {"deadline_utc": utc_text(utc_now() + timedelta(seconds=seconds))})
            deadline = parse_utc(read_json(path)["deadline_utc"], "watch deadline")
        copier = None
        failures = len(list(context.path("progressive/failures").glob("*.json")))
        try:
            while True:
                if utc_now() >= deadline:
                    if context.path("launch/create-request-attempted.txt").exists():
                        if not command_requires_completion(context):
                            return stop(context, delete=False)
                        warning = context.path("launch/watch-limit-warning.json")
                        if not warning.exists():
                            atomic_json(warning, {"deadline_utc": utc_text(deadline), "observed_at_utc": utc_text(),
                                                 "work_continues": True, "approval_review_required": True})
                            print("session estimate exceeded; job continues and requires review", file=sys.stderr, flush=True)
                    else:
                        raise OperationError("watch deadline expired before creation; prepare a new operation")
                result = run(context, approval)
                approval = None
                if progressive_policy(context) is not None:
                    try:
                        if copier is None and failures <= 3 and result.get("state") == "running":
                            private = context.path("launch/ssh/id_ed25519")
                            target = resolve_ssh_target(context, result["instance_id"])
                            copier = start_progressive_copy(context, private, target)
                        if copier is not None and copier.poll() not in (None, 0):
                            raise OperationError(f"background copy exited with status {copier.returncode}; see progressive/copier.log")
                        if context.path("progressive/status.json").exists():
                            result["progressive_copy"] = read_json(context.path("progressive/status.json"))
                    except (OperationError, OSError) as error:
                        if copier is None or copier.poll() is not None:
                            failures += 1
                            copier = None
                            atomic_json(context.path(f"progressive/failures/{failures:03}.json"),
                                        {"error": str(error), "observed_at_utc": utc_text()})
                        state = {"state": "failed", "error": str(error), "observed_at_utc": utc_text(),
                                 "will_retry": failures <= 3}
                        result["progressive_copy"] = state
                        with contextlib.suppress(OperationError, OSError):
                            atomic_json(context.path("progressive/status.json"), state, replace=True)
                        print(f"background copy failed: {error}", file=sys.stderr, flush=True)
                if result.get("state") not in ("running", "preparing", "remote_access_pending"):
                    return result
                print("watch status: " + json.dumps(result, sort_keys=True), file=sys.stderr, flush=True)
                time.sleep(30 if command_requires_completion(context) else
                           min(30, max(0, (deadline - utc_now()).total_seconds())))
        except (Exception, KeyboardInterrupt):
            if (context.path("launch/create-request-attempted.txt").exists()
                    and not command_requires_completion(context)):
                stop(context, delete=False)
            raise
        finally:
            if copier is not None and copier.poll() is None:
                copier.terminate()
                try:
                    copier.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    copier.kill()
                    copier.wait(timeout=5)


def status(context: Context, watch: bool) -> dict[str, object]:
    if not watch:
        return status_once(context)
    interval = context.timing_value("status_watch_seconds")
    while True:
        result = status_once(context)
        print(json.dumps(result, sort_keys=True), flush=True)
        if result.get("billing_possible") is not True or result.get("state") in (
            "terminal",
            "retrieved",
        ):
            return result
        time.sleep(interval)


def stop(context: Context, *, delete: bool = True, incomplete_stop_approval: str | None = None) -> dict[str, object]:
    """Stop and retrieve; automatic command supervision passes delete=False."""
    with operation_lock(context.root):
        if context.path("result/settlement/settlement-result.json").exists():
            return settle(context)
        instance_id = recorded_instance_id(context)
        if (command_requires_completion(context)
                and not context.path("launch/destruction-confirmation.json").exists()
                and (instance_id is not None or context.path("launch/create-request-attempted.txt").exists())):
            verify_completion_review(context, instance_id, incomplete_stop_approval)
        if context.path("launch/result-loss-ledger-reconciliation.json").exists():
            if instance_id is None:
                raise OperationError("result-loss evidence has no instance identity")
            return ledger_reconciliation_state(context, instance_id, delete=delete)
        if context.path("launch/provider-final-charge.json").exists():
            return settle(context)
        if context.path("launch/destruction-confirmation.json").exists():
            if instance_id is None:
                raise OperationError("destroyed instance has no create-result identity")
            charge = ensure_final_charge(context, instance_id)
            return (
                settle(context)
                if charge is not None
                else invoice_pending_result(context, instance_id)
            )
        if instance_id is None and context.path(
            "launch/create-request-attempted.txt"
        ).exists():
            instance = recover_or_freeze_create(context, recorded_offer(context))
            if instance is not None:
                instance_id = calibration_package.created_instance_id(instance)
        if instance_id is None:
            if not context.path("launch/full-build-reservation.json").exists():
                raise OperationError("there is no paid full-build operation to stop")
            if not context.path("launch/preclaim-failure.log").exists():
                atomic_bytes(
                    context.path("launch/preclaim-failure.log"),
                    f"{utc_text()} stopped before instance creation\n".encode("utf-8"),
                )
            write_preclaim_failure(context, "stopped before instance creation")
            return settle(context)
        if context.path("launch/retrieval-verification.json").exists():
            attempt = last_attempt_id(context)
            if attempt is not None:
                publish_verified_result(context, attempt)
            if attempt is None:
                return cleanup_preworker_instance(context, instance_id, delete=delete)
            if not delete:
                return preserved_instance_result(context, instance_id)
            destroy_instance(context, instance_id)
            charge = ensure_final_charge(context, instance_id)
            if charge is None:
                return invoice_pending_result(context, instance_id)
            return settle(context)
        attempt_id = last_attempt_id(context)
        if attempt_id is None:
            return cleanup_preworker_instance(context, instance_id, delete=delete)
        try:
            private_key, target = ensure_ssh(context, instance_id)
            remote = worker_status(context, private_key, target, attempt_id)
            if remote["state"] == "absent" or (
                remote["state"] == "orphaned"
                and remote.get("execution_committed") is not True
            ):
                response = remote_json(
                    context,
                    private_key,
                    target,
                    "_remote-abort-unstarted",
                    "--attempt",
                    attempt_id,
                )
                if (
                    not isinstance(response, dict)
                    or response.get("aborted_unstarted") is not True
                    or response.get("state") != "terminal"
                    or response.get("kind") != "start.exit"
                ):
                    raise OperationError(
                        "remote worker did not publish an unstarted terminal receipt"
                    )
                atomic_json(
                    context.path(
                        f"launch/worker-invocations/{attempt_id}.terminal.json"
                    ),
                    response,
                )
                remote = response
            if remote["state"] in ("running", "starting"):
                response = remote_json(
                    context,
                    private_key,
                    target,
                    "_remote-stop",
                    "--attempt",
                    attempt_id,
                    *(["--incomplete-stop-approval", incomplete_stop_approval] if incomplete_stop_approval else []),
                )
                if (
                    not isinstance(response, dict)
                    or response.get("stop_requested") is not True
                ):
                    raise OperationError(
                        "remote worker did not acknowledge the stop request"
                    )
                attempts = context.timing_value("provider_attempts")
                interval = context.timing_value("provider_poll_seconds")
                for _ in range(attempts):
                    remote = worker_status(
                        context, private_key, target, attempt_id
                    )
                    if remote["state"] in ("terminal", "orphaned"):
                        break
                    if interval:
                        time.sleep(interval)
                else:
                    raise OperationError(
                        "worker stop did not reach a terminal record"
                    )
        except OperationError as error:
            return destroy_without_remote_retrieval(
                context, instance_id, attempt_id, str(error), delete=delete
            )
        if remote["state"] not in ("terminal", "orphaned"):
            return destroy_without_remote_retrieval(
                context,
                instance_id,
                attempt_id,
                "worker could not be reconciled to a terminal remote state",
                delete=delete,
            )
        try:
            return cleanup_terminal(
                context,
                instance_id,
                private_key,
                target,
                attempt_id,
                remote,
                delete=delete,
            )
        except OperationError as error:
            if context.path("launch/retrieval-verification.json").exists():
                raise
            return destroy_without_remote_retrieval(
                context, instance_id, attempt_id, str(error), delete=delete
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    subparsers = parser.add_subparsers(dest="operation", required=True)
    subparsers.add_parser("prepare")
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--approve")
    run_parser.add_argument("--watch", action="store_true")
    resume_parser = subparsers.add_parser("resume", help="explicitly continue a terminal resumable command job")
    resume_parser.add_argument("--reason", required=True)
    resume_parser.add_argument("--watch", action="store_true")
    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--watch", action="store_true")
    copy_parser = subparsers.add_parser("copy", help="copy completed files without stopping the worker")
    copy_parser.add_argument("--watch", action="store_true")
    subparsers.add_parser("_remote-progress", help=argparse.SUPPRESS)
    copy_remote = subparsers.add_parser("_remote-copy", help=argparse.SUPPRESS)
    copy_remote.add_argument("--files", required=True)
    copy_receive = subparsers.add_parser("_receive-copy", help=argparse.SUPPRESS)
    copy_receive.add_argument("--request", required=True, type=Path)
    stop_parser = subparsers.add_parser("stop", help="stop the workload, retrieve results and delete the instance")
    stop_parser.add_argument("--incomplete-stop-approval",
                             help="record explicit user approval to stop before complete verified retrieval")
    subparsers.add_parser("_remote-verify-transfer", help=argparse.SUPPRESS)
    subparsers.add_parser("_remote-prepare", help=argparse.SUPPRESS)
    prepare_worker = subparsers.add_parser(
        "_remote-prepare-worker", help=argparse.SUPPRESS
    )
    prepare_worker.add_argument("--start-lock-fd", required=True, type=int)
    subparsers.add_parser("_remote-volume-prepare", help=argparse.SUPPRESS)
    for operation in (
        "_remote-worker",
        "_remote-controller",
        "_remote-status",
        "_remote-stop",
        "_remote-abort-unstarted",
        "_remote-seal",
    ):
        hidden = subparsers.add_parser(operation, help=argparse.SUPPRESS)
        hidden.add_argument("--attempt", required=True)
        if operation == "_remote-worker":
            hidden.add_argument("--resume-from", help=argparse.SUPPRESS)
            hidden.add_argument("--reason", help=argparse.SUPPRESS)
        if operation == "_remote-stop":
            hidden.add_argument("--incomplete-stop-approval", help=argparse.SUPPRESS)
    supervise = subparsers.add_parser("_remote-supervise", help=argparse.SUPPRESS)
    supervise.add_argument("--attempt", required=True)
    supervise.add_argument("--start-lock-fd", required=True, type=int)
    args = parser.parse_args()
    return args


def validate_instance_against_offer(
    offer: object,
    create_result: object,
    instance: object,
    expected_image: str,
    maximum_rate_micro_usd: int,
    *,
    expected_label: str | None = None,
    require_running: bool = True,
    minimum_disk_gb: int = 200,
) -> dict[str, object]:
    """Check the created instance's approved terms, not equality of bundle IDs."""
    if not isinstance(offer, dict):
        raise ValueError("approved Vast offer must be one object")
    if maximum_rate_micro_usd <= 0:
        raise ValueError("maximum Vast instance rate must be positive")
    instance = calibration_package.instance_from_document(instance)
    expected_instance_id = calibration_package.created_instance_id(create_result)
    offer_id = offer.get("id")
    offer_machine_id = offer.get("machine_id")
    offer_bundle_id = offer.get("bundle_id")
    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, str))
        or not str(value).isdecimal()
        or int(value) <= 0
        for value in (offer_id, offer_machine_id, offer_bundle_id)
    ):
        raise ValueError("approved Vast offer identifiers must be positive integers")
    offer_rate = int(
        (calibration_package.require_number(offer.get("dph_total"), "dph_total") * 1_000_000)
        .to_integral_value(rounding=ROUND_CEILING)
    )
    instance_rate = int(
        (
            calibration_package.require_number(instance.get("dph_total"), "instance dph_total")
            * 1_000_000
        ).to_integral_value(rounding=ROUND_CEILING)
    )
    instance_id = instance.get("id")
    instance_bundle_id = instance.get("bundle_id")
    if isinstance(instance_id, bool) or not isinstance(instance_id, (int, str)) or str(instance_id) != expected_instance_id:
        raise ValueError("actual Vast instance ID differs from the recorded create result")
    for field in ("machine_id", "gpu_name", "num_gpus"):
        if instance.get(field) != offer.get(field):
            raise ValueError(f"actual Vast instance {field} does not match the approved offer")
    if require_running:
        for field in ("actual_status", "intended_status"):
            if instance.get(field) != "running":
                raise ValueError(f"actual Vast instance {field} is not running")
    if calibration_package.immutable_image_ref(instance.get("image_uuid")) != calibration_package.immutable_image_ref(expected_image):
        raise ValueError("actual Vast instance image_uuid does not match the approved image")
    if calibration_package.require_number(instance.get("disk_space"), "instance disk_space") < minimum_disk_gb:
        raise ValueError("actual Vast instance disk_space is below the approved allocation")
    if instance_rate <= 0 or instance_rate > offer_rate or instance_rate > maximum_rate_micro_usd:
        raise ValueError("actual Vast instance dph_total is invalid or exceeds the approved rate")
    if instance.get("is_bid") is not False:
        raise ValueError("actual Vast instance is_bid is not false")
    if instance.get("verification") != "verified":
        raise ValueError("actual Vast instance verification is not verified")
    if expected_label is not None and (not expected_label.strip() or instance.get("label") != expected_label):
        raise ValueError("actual Vast instance label does not match the approved operation")
    return {
        "schema_version": 1,
        "artifact_kind": "gte-approved-vast-instance",
        "offer_id": str(offer_id),
        "instance_id": str(instance_id),
        "machine_id": str(offer_machine_id),
        "offer_bundle_id": str(offer_bundle_id),
        "bundle_id": None if instance_bundle_id is None else str(instance_bundle_id),
        "image": calibration_package.immutable_image_ref(expected_image),
        "rate_micro_usd_per_hour": instance_rate,
        "maximum_rate_micro_usd_per_hour": maximum_rate_micro_usd,
        "on_demand": True,
        "label": instance.get("label"),
    }


def recover_create_result(
    raw_instances: object,
    offer: object,
    expected_image: str,
    expected_label: str,
    maximum_rate_micro_usd: int,
    *, minimum_disk_gb: int = 200,
) -> dict[str, object]:
    """Recover one ambiguous create only from one validated live label match."""
    if not expected_label.strip():
        raise ValueError("recovery label must be nonempty")
    if isinstance(raw_instances, dict) and isinstance(raw_instances.get("instances"), list):
        raw_instances = raw_instances["instances"]
    if not isinstance(raw_instances, list):
        raise ValueError("Vast instance recovery requires an instance list")
    matches = [
        row
        for row in raw_instances
        if isinstance(row, dict) and row.get("label") == expected_label
    ]
    if len(matches) != 1:
        raise ValueError("instance recovery requires exactly one matching live label")
    create_result = {"success": True, "new_contract": matches[0].get("id")}
    validate_instance_against_offer(
        offer,
        create_result,
        matches[0],
        expected_image,
        maximum_rate_micro_usd,
        expected_label=expected_label,
        require_running=False,
        minimum_disk_gb=minimum_disk_gb,
    )
    return create_result


def validate_command_context(context: Context) -> None:
    if "local_volume" in context.config:
        volume = required_object(context.config, "local_volume")
        if (set(volume) != {"id", "machine_id"}
                or any(type(v) is not int or v <= 0 for v in volume.values())
                or volume["machine_id"] != context.config["selected_offer"]["machine_id"]):
            raise OperationError("local volume must belong to the selected physical machine")
    if "volume_recovery" in context.config:
        recovery = required_object(context.config, "volume_recovery")
        if "local_volume" not in context.config:
            raise OperationError("replacement requires a local volume")
        require_sha256(required_string(recovery, "previous_contract_sha256"), "previous volume contract")
        parse_attempt_id(required_string(recovery, "previous_attempt"))
        required_string(recovery, "previous_instance_id")
        if not recovery.get("work_files"):
            raise OperationError("replacement requires sealed work records")
        if context.config["workload"].get("resumable") is not True:
            raise OperationError("volume replacement requires a resumable workload")
        if type(recovery.get("reuse_work", True)) is not bool:
            raise OperationError("volume reuse_work must be a boolean")
        if not recovery.get("reuse_work", True):
            required_string(recovery, "reason")
    if "cleanup_seconds" in context.config:
        cleanup = required_nonnegative_int(context.config, "cleanup_seconds")
        if cleanup >= required_positive_int(context.config, "session_seconds"):
            raise OperationError("cleanup_seconds must leave time for the session")
    context.label
    context.image
    onstart = context.config.get("onstart", "")
    if not isinstance(onstart, str) or "\0" in onstart:
        raise OperationError("onstart must be a string without NUL characters")
    if not isinstance(context.config.get("ssh_direct", False), bool):
        raise OperationError("ssh_direct must be a boolean")
    if not Path(required_string(context.config, "canonical_ledger_path")).is_absolute():
        raise OperationError("canonical_ledger_path must be absolute")
    for field in ("operator_sha256", "control_sha256s_sha256", "transport_manifest_sha256",
                  "execution_package_manifest_sha256"):
        context.pin(field)
    for field in ("disk_gb", "maximum_rental_rate_micro_usd_per_hour", "reservation_ceiling_micro_usd",
                  "lifetime_budget_micro_usd", "setup_cost_micro_usd", "manual_stop_cost_micro_usd"):
        context.limit(field)
    if context.limit("lifetime_budget_micro_usd") != 1_000_000_000:
        raise OperationError("the command workload must use the $1,000 lifetime budget")
    if not (context.limit("setup_cost_micro_usd") < context.limit("manual_stop_cost_micro_usd")
            <= context.limit("reservation_ceiling_micro_usd") <= context.limit("lifetime_budget_micro_usd")):
        raise OperationError("invalid workload spending limits")
    for field in ("provider_attempts", "preparation_attempts", "destroy_attempts", "invoice_retry_attempts"):
        context.timing_value(field)
    if context.timing_value("destroy_attempts") < 2:
        raise OperationError("destroy confirmation requires at least two attempts")
    for field in ("provider_poll_seconds", "preparation_poll_seconds", "destroy_poll_seconds",
                  "invoice_retry_seconds", "invoice_confirmation_seconds", "invoice_not_before_seconds",
                  "status_watch_seconds"):
        context.timing_value(field)
    workload = required_object(context.config, "workload")
    command = workload.get("command")
    if not isinstance(command, list) or not command or any(not isinstance(v, str) or not v for v in command):
        raise OperationError("workload.command must be a nonempty argument array")
    if not Path(command[0]).is_absolute() or not Path(context.remote_python).is_absolute():
        raise OperationError("workload executable and Python paths must be absolute")
    environment = workload.get("environment", {})
    if not isinstance(environment, dict) or any(not isinstance(k, str) or not k or "=" in k
            or not isinstance(v, str) or "\0" in k + v for k, v in environment.items()):
        raise OperationError("workload.environment must contain string environment variables")
    if "ORACLE_RUN_WORKER_LOCK_FD" in environment:
        raise OperationError("worker lock descriptor is reserved for the supervisor")
    if ("local_volume" in context.config
            and environment.get("HF_HOME") != "/workspace/oracle-full-build/model-cache"):
        raise OperationError("local volume requires the persistent model cache")
    if 'work_seconds' not in workload or workload['work_seconds'] is not None:
        required_positive_int(workload, "work_seconds")
    if not isinstance(workload.get("resumable", False), bool):
        raise OperationError("workload.resumable must be a boolean")
    if "status_command" in workload:
        status_command = workload["status_command"]
        if (not isinstance(status_command, list) or not status_command
                or any(not isinstance(v, str) or not v for v in status_command)
                or not Path(status_command[0]).is_absolute()):
            raise OperationError("workload.status_command must be an absolute executable argument array")
    outputs = workload.get("outputs")
    if not isinstance(outputs, list) or not outputs:
        raise OperationError("workload.outputs must list relative result paths")
    for relative in outputs:
        command_relative_path(relative)
    progressive_policy(context)


def command_relative_path(value: object) -> Path:
    if not isinstance(value, str) or not value or Path(value).is_absolute() or ".." in Path(value).parts or value == ".":
        raise OperationError("workload paths must be nonempty relative paths without '..'")
    return Path(value)


def validate_offer(context: Context, offer: object, identifier: str) -> dict[str, object]:
    if not context.command_workload:
        return full_build_package.validate_full_build_offer(offer, identifier)
    if not isinstance(offer, dict) or str(offer.get("id")) != identifier:
        raise ValueError("offer differs from the personally selected offer")
    for field in ("id", "machine_id", "bundle_id", "num_gpus"):
        value = offer.get(field)
        if isinstance(value, bool) or not str(value).isdecimal() or int(value) <= 0:
            raise ValueError(f"invalid offer {field}")
    if (offer.get("rentable") is not True or offer.get("rented") is not False
            or offer.get("is_bid") is not False or offer.get("verification") != "verified"):
        raise ValueError("offer must be available, on-demand and verified")
    rate = full_build_package.decimal_field(offer, "dph_total")
    if rate <= 0 or rate * 1_000_000 > context.limit("maximum_rental_rate_micro_usd_per_hour"):
        raise ValueError("offer exceeds the approved hourly rate")
    for field in ("inet_down_cost", "inet_up_cost"):
        if full_build_package.decimal_field(offer, field) < 0:
            raise ValueError("negative transfer price")
    if full_build_package.decimal_field(offer, "disk_space") < context.limit("disk_gb"):
        raise ValueError("offer does not have the requested disk allocation")
    return offer


def verify_command_artifacts(context: Context) -> None:
    verify_control_sums(context)
    verify_sha(context.operator_path, context.pin("operator_sha256"), "operator")
    verify_sha(Path(__file__).resolve(), context.pin("operator_sha256"), "invoked operator")
    if Path(__file__).resolve() != context.operator_path:
        raise OperationError("reviewed workflow must be invoked through the transported operator")
    for relative, pin in (("transport/transport-manifest.json", "transport_manifest_sha256"),
                          ("transport/workload/package-manifest.json", "execution_package_manifest_sha256")):
        manifest = context.path(relative)
        verify_sha(manifest, context.pin(pin), relative)
        try:
            full_build_package.verify_manifest(manifest.parent, manifest)
        except (OSError, ValueError) as error:
            raise OperationError(f"workload package verification failed: {error}") from error


def command_budget(context: Context) -> dict[str, object]:
    ledger = read_json(context.ledger)
    if not isinstance(ledger, dict) or ledger.get("lifetime_cap_cents") != 100000:
        raise OperationError("invalid lifetime budget ledger")
    for field in ("actual_spend_cents", "outstanding_commitments_cents", "reserved_remaining_work_cents"):
        required_nonnegative_int(ledger, field)
    if sum(ledger[k] for k in ("actual_spend_cents", "outstanding_commitments_cents", "reserved_remaining_work_cents")) > 100000:
        raise OperationError("lifetime budget is exceeded")
    return ledger


def prepare_command_plan(context: Context) -> dict[str, object]:
    with operation_lock(context.root):
        verify_reviewed_artifacts(context)
        verify_local_ssh(context)
        verify_image(context)
        completed_process(["tar", "--version"])
        ledger = command_budget(context)
        query, offer = select_offer(context)
        if any(row.get("label") == context.label for row in sanitized_live_instances()):
            raise OperationError("a live instance already uses the operation label")
        maximum = context.limit("reservation_ceiling_micro_usd")
        projection = {"total_micro_usd": maximum, "projected_lifetime_total_micro_usd": maximum + 10000 * sum(
            ledger[k] for k in ("actual_spend_cents", "outstanding_commitments_cents", "reserved_remaining_work_cents"))}
        ensure_retrieval_destination(context)
        plan = plan_document(context, query, offer, projection, sha256_file(context.ledger))
        digest = hashlib.sha256(canonical_json(plan)).hexdigest()
        path = context.approval_dir / f"{digest}.json"
        atomic_json(path, plan)
        return {"state": "awaiting_approval", "paid_action_performed": False, "approval_sha256": digest,
                "plan": str(path), "offer_id": str(offer["id"]), "reservation_ceiling_micro_usd": maximum,
                "reservation": {"kind": "vast_run_reservation", "plan_sha256": digest,
                    "evidence_path": str(context.root), "maximum_charge_cents": (maximum + 9999) // 10000}}


def reserve_command_workload(context: Context, plan: dict[str, object]) -> dict[str, object]:
    receipt_path = context.path("launch/full-build-reservation.json")
    if receipt_path.exists():
        receipt = read_json(receipt_path)
        verify_sha(context.path("launch/reserved-budget-ledger.json"), receipt["ledger_sha256"], "reserved ledger")
        return receipt
    ledger = command_budget(context)
    committed = completed_process(["git", "-C", str(context.ledger.parent), "show", "HEAD:" + context.ledger.name]).stdout
    if committed != context.ledger.read_bytes():
        raise OperationError("budget ledger must be committed before the paid commitment")
    digest = hashlib.sha256(canonical_json(plan)).hexdigest()
    maximum = (context.limit("reservation_ceiling_micro_usd") + 9999) // 10000
    rows = [row for row in ledger.get("entries", []) if row.get("kind") == "vast_run_reservation"
            and row.get("plan_sha256") == digest and row.get("evidence_path") == str(context.root)
            and row.get("maximum_charge_cents") == maximum and row.get("status") == "reserved"]
    if len(rows) != 1 or ledger["outstanding_commitments_cents"] < maximum:
        raise OperationError("one matching outstanding committed reservation is required")
    if not context.path("launch/invoice-start-date.txt").exists():
        atomic_bytes(context.path("launch/invoice-start-date.txt"), f"{utc_now().date().isoformat()}\n".encode())
    atomic_copy(context.ledger, context.path("launch/reserved-budget-ledger.json"))
    receipt = {"ledger_sha256": sha256_file(context.ledger), "reservation_id": rows[0].get("reservation_id"),
               "plan_sha256": digest, "total_micro_usd": maximum * 10000}
    atomic_json(receipt_path, receipt)
    return receipt


def prepare_remote_command(context: Context) -> None:
    package = context.path("package")
    if not package.exists():
        staging = context.path("package.next")
        if staging.exists():
            shutil.rmtree(staging)
        shutil.copytree(context.path("transport/workload"), staging)
        os.replace(staging, package)
        sync_directory(context.root)
    work = context.path("work")
    if work.exists():
        return
    staging = context.path("work.next")
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir()
    shutil.copyfile(context.path("launch/reserved-budget-ledger.json"), staging / "budget-ledger.json")
    os.replace(staging, work)
    sync_directory(context.root)


def verify_command_results(context: Context, candidate: Path) -> dict[str, object]:
    receipt = read_json(context.path("launch/retrieval-verification.json"))
    validate_file_records(candidate / "work", receipt["work_files"])
    for relative in required_object(context.config, "workload")["outputs"]:
        if not (candidate / "work" / command_relative_path(relative)).exists():
            raise OperationError(f"required workload output is missing: {relative}")
    return {"verified": True, "outputs": context.config["workload"]["outputs"], "verified_at_utc": utc_text()}


def fail(message: str) -> NoReturn:
    print(f"vast-full-build: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    args = parse_args()
    context: Context | None = None
    try:
        context = Context.load(args)
        if args.operation == "prepare":
            result = prepare(context)
        elif args.operation == "run":
            result = run_watch(context, args.approve) if args.watch else run(context, args.approve)
        elif args.operation == "resume":
            result = resume(context, args.reason)
            if args.watch:
                result = run_watch(context, None)
        elif args.operation == "status":
            result = status(context, args.watch)
        elif args.operation == "copy":
            result = progressive_copy(context, args.watch)
        elif args.operation == "_remote-progress":
            result = remote_progress(context)
        elif args.operation == "_remote-copy":
            remote_copy(context, json.loads(args.files))
            return 0
        elif args.operation == "_receive-copy":
            receive_copy(context, args.request)
            return 0
        elif args.operation == "stop":
            result = stop(context, incomplete_stop_approval=args.incomplete_stop_approval)
        elif args.operation == "_remote-verify-transfer":
            result = remote_verify_transfer(context)
        elif args.operation == "_remote-volume-prepare":
            if context.root.parent != Path('/workspace/oracle-full-build/replacements'):
                raise OperationError("volume staging root is invalid")
            result = remote_volume_prepare(context, Path('/workspace/oracle-full-build'))
        elif args.operation == "_remote-prepare":
            result = remote_prepare(context)
        elif args.operation == "_remote-prepare-worker":
            result = remote_prepare_worker(context, args.start_lock_fd)
        elif args.operation == "_remote-worker":
            result = remote_worker(context, args.attempt, args.resume_from, args.reason)
        elif args.operation == "_remote-supervise":
            result = remote_supervise(context, args.attempt, args.start_lock_fd)
        elif args.operation == "_remote-controller":
            remote_controller(context, args.attempt)
        elif args.operation == "_remote-status":
            result = remote_status_report(context, args.attempt)
        elif args.operation == "_remote-stop":
            result = remote_stop(context, args.attempt, args.incomplete_stop_approval)
        elif args.operation == "_remote-abort-unstarted":
            result = remote_abort_unstarted(context, args.attempt)
        else:
            result = remote_seal(context, args.attempt)
    except OperationError as error:
        message = str(error)
        if (
            context is not None
            and context.path("launch/create-request-attempted.txt").exists()
            and not context.path("launch/destruction-confirmation.json").exists()
        ):
            message += "; the recorded Vast instance may still be billing"
        fail(message)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
