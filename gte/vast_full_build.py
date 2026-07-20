#!/usr/bin/env python3
"""Resumable operator for the frozen Vast full-build experiment."""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import getpass
import hashlib
import json
import os
import shlex
import shutil
import signal
import subprocess
import sys
import time
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_CEILING
from pathlib import Path
from typing import BinaryIO, Iterator, NoReturn

sys.dont_write_bytecode = True

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
        if document.get("artifact_kind") != "gte-vast-full-build-operation":
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
    package_config_path = (
        context.path("execution/package/run/full-build-config.json")
        if require_local_execution_package
        else context.path("transport/package-skeleton/run/full-build-config.json")
    )
    package_config = read_json(package_config_path)
    if not isinstance(package_config, dict):
        raise OperationError("frozen full-build config is invalid")
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
            "/usr/bin/rsync",
            context.image,
            "--version",
        ]
    )


def ensure_retrieval_destination(context: Context) -> None:
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
    matches = [
        row
        for row in search_offers(query, context.limit("disk_gb"))
        if str(row.get("id")) == identifier
    ]
    if len(matches) != 1:
        raise OperationError("the exact approved Vast offer is no longer available")
    try:
        selected = full_build_package.validate_full_build_offer(matches[0], identifier)
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
            frozen = full_build_package.validate_full_build_offer(
                recorded[0], identifier
            )
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
                recovered = calibration_package.recover_create_result(
                    rows,
                    offer,
                    context.image,
                    context.label,
                    context.limit("maximum_rental_rate_micro_usd_per_hour"),
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


def record_instance_ownership(
    context: Context,
    offer: dict[str, object],
    create_result: dict[str, object],
    candidate: dict[str, object],
) -> None:
    instance_path = context.path("launch/instance-ownership.json")
    validation_path = context.path("launch/instance-ownership-validation.json")
    try:
        validation = calibration_package.validate_instance_against_offer(
            offer,
            create_result,
            candidate,
            context.image,
            context.limit("maximum_rental_rate_micro_usd_per_hour"),
            expected_label=context.label,
            require_running=False,
        )
    except ValueError as error:
        raise OperationError(f"created Vast instance failed identity binding: {error}") from error
    if instance_path.exists():
        existing = read_json(instance_path)
        try:
            expected = calibration_package.validate_instance_against_offer(
                offer,
                create_result,
                existing,
                context.image,
                context.limit("maximum_rental_rate_micro_usd_per_hour"),
                expected_label=context.label,
                require_running=False,
            )
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
                candidate = calibration_package.freeze_instance_record(create_result, raw)
                record_instance_ownership(context, offer, create_result, candidate)
                if candidate.get("actual_status") == "running":
                    frozen = candidate
                    break
            except (OperationError, ValueError):
                pass
            if interval:
                time.sleep(interval)
        if frozen is None:
            raise OperationError("created Vast instance did not become running")
        atomic_json(instance_path, frozen)
    try:
        validation = calibration_package.validate_instance_against_offer(
            offer,
            create_result,
            frozen,
            context.image,
            context.limit("maximum_rental_rate_micro_usd_per_hour"),
            expected_label=context.label,
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


def rsync_ssh_transport(
    context: Context, private_key: Path, target: list[str]
) -> tuple[str, str]:
    if len(target) == 3:
        port_flag, port, host = target
        if port_flag != "-p":
            raise OperationError("Vast SSH target has no usable rsync port")
    elif len(target) == 1:
        try:
            parsed = urllib.parse.urlparse(target[0])
            hostname = parsed.hostname
            port = parsed.port
            username = parsed.username
        except ValueError as error:
            raise OperationError("Vast SSH target is invalid for rsync") from error
        if hostname is None or port is None or username != "root":
            raise OperationError("Vast SSH target is invalid for rsync")
        if ":" in hostname:
            hostname = f"[{hostname}]"
        host = f"{username}@{hostname}"
    else:
        raise OperationError("Vast SSH target is invalid for rsync")
    command = shlex.join([*ssh_options(context, private_key), "-p", str(port)])
    return command, host


def rsync_upload_directory(
    context: Context,
    private_key: Path,
    target: list[str],
    source: Path,
    remote_directory: str,
) -> None:
    if not source.is_dir() or not remote_directory.startswith("/"):
        raise OperationError("rsync upload directories are invalid")
    remote_shell, host = rsync_ssh_transport(context, private_key, target)
    completed_process(
        [
            *ssh_arguments(context, private_key, target),
            "mkdir",
            "-p",
            "--",
            remote_directory.rstrip("/"),
        ]
    )
    completed_process(
        [
            "rsync",
            "--archive",
            "--no-owner",
            "--no-group",
            "--partial",
            "--delete",
            "--timeout=60",
            "--rsync-path=/usr/bin/rsync",
            "--rsh",
            remote_shell,
            f"{source}/",
            f"{host}:{remote_directory.rstrip('/')}/",
        ]
    )


def rsync_download_directory(
    context: Context,
    private_key: Path,
    target: list[str],
    remote_directory: str,
    destination: Path,
) -> None:
    if not remote_directory.startswith("/"):
        raise OperationError("rsync download directory is invalid")
    destination.mkdir(parents=True, exist_ok=True, mode=0o700)
    remote_shell, host = rsync_ssh_transport(context, private_key, target)
    completed_process(
        [
            "rsync",
            "--archive",
            "--no-owner",
            "--no-group",
            "--partial",
            "--delete",
            "--timeout=60",
            "--rsync-path=/usr/bin/rsync",
            "--rsh",
            remote_shell,
            f"{host}:{remote_directory.rstrip('/')}/",
            f"{destination}/",
        ]
    )


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
            result = completed_process(["vastai", "ssh-url", instance_id])
            target = parse_vast_ssh_target(result.stdout)
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
        "/opt/gte-venv/bin/python",
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
        remote_arguments(context, private_key, target, operation, *arguments)
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
            rsync_download_directory(
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
                "/usr/bin/rsync",
                "--version",
            ]
        )
        verify_reviewed_artifacts(context)
        transfer: object = None
        for copy_attempt in range(2):
            try:
                rsync_upload_directory(
                    context,
                    private_key,
                    target,
                    context.path("transport"),
                    "/workspace/oracle-full-build/transport/",
                )
                rsync_upload_directory(
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
    instance_id: str, raw: object
) -> dict[str, object]:
    try:
        row = calibration_package.instance_from_document(raw)
        if str(row.get("id")) != instance_id:
            raise ValueError("instance ID changed")
        duration = Decimal(str(row["duration"]))
        rate = Decimal(str(row["dph_total"]))
        down = Decimal(str(row.get("inet_down_billed", 0))) * Decimal(
            str(row.get("inet_down_cost", 0))
        )
        up = Decimal(str(row.get("inet_up_billed", 0))) * Decimal(
            str(row.get("inet_up_cost", 0))
        )
        total = duration * rate / Decimal(3600) + (down + up) / Decimal(1_000_000)
        micro = int(
            (total * Decimal(1_000_000)).to_integral_value(rounding=ROUND_CEILING)
        )
    except (KeyError, ValueError, ArithmeticError) as error:
        raise OperationError(f"live provider cost record is invalid: {error}") from error
    return {
        "schema_version": 1,
        "instance_id": instance_id,
        "observed_at_utc": utc_text(),
        "duration_seconds": int(duration),
        "total_hourly_rate_usd": str(rate),
        "conservative_observed_total_micro_usd": micro,
    }


def live_cost_record(instance_id: str) -> dict[str, object]:
    return cost_record_from_instance(
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
    value = (existing[-1] + 1) if existing else 1
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
    cost = live_cost_record(instance_id)
    cost["attempt_id"] = attempt_id
    cost["reason"] = reason
    atomic_json(path, cost)
    observed = cost.get("conservative_observed_total_micro_usd")
    if isinstance(observed, bool) or not isinstance(observed, int):
        raise OperationError("pre-worker cost receipt is invalid")
    if observed > context.limit("setup_cost_micro_usd"):
        raise OperationError("worker start refused because setup exceeded its cost gate")
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
    try:
        response = remote_json(
            context,
            private_key,
            target,
            "_remote-worker",
            "--attempt",
            attempt_id,
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
    terminal = terminal_state(attempt)
    if terminal is not None:
        return {"state": "terminal", "attempt_id": attempt_id, **terminal}
    started = (attempt / "full-build.started").is_file()
    supervisor = read_pid(attempt / "full-build.pid")
    controller = read_pid(attempt / "controller.pid")
    supervisor_alive = process_alive(supervisor)
    controller_alive = process_alive(controller)
    if started and controller_alive:
        state = "running"
    elif supervisor_alive or controller_alive:
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
    }


def remote_status_report(context: Context, attempt_id: str) -> dict[str, object]:
    result = remote_attempt_status(context, attempt_id)
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
    usage = shutil.disk_usage(context.root)
    disk = {
        "total_bytes": usage.total,
        "used_bytes": usage.used,
        "available_bytes": usage.free,
    }
    try:
        observation = completed_process(
            [
                "nvidia-smi",
                "--query-gpu=utilization.gpu,memory.used,memory.total",
                "--format=csv,noheader,nounits",
            ]
        ).stdout.decode("utf-8", errors="strict").strip()
        rows = [line.strip() for line in observation.splitlines() if line.strip()]
        if len(rows) != 1:
            raise ValueError("expected exactly one GPU")
        values = [int(value.strip()) for value in rows[0].split(",")]
        if len(values) != 3 or any(value < 0 for value in values):
            raise ValueError("GPU metrics are invalid")
        gpu: dict[str, object] = {
            "utilization_percent": values[0],
            "memory_used_bytes": values[1] * 1024 * 1024,
            "memory_total_bytes": values[2] * 1024 * 1024,
        }
    except (OperationError, UnicodeDecodeError, ValueError) as error:
        gpu = {"error": f"GPU observation unavailable: {error}"}
    result.update({"progress": progress, "disk": disk, "gpu": gpu})
    return result


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
    try:
        os.execv(executable, arguments)
    except OSError as error:
        raise OperationError(f"could not exec the full-build controller: {error}") from error


def remote_worker(context: Context, attempt_id: str) -> dict[str, object]:
    attempt_id = parse_attempt_id(attempt_id)
    attempts = context.path("work/full-build-attempts")
    attempts.mkdir(parents=True, exist_ok=True, mode=0o700)
    attempt = attempts / attempt_id
    with file_lock(
        context.path("work/full-build-start.lock"), blocking=True
    ) as start_lock:
        if attempt.is_dir():
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
        for prior in sorted(attempts.iterdir()):
            if prior == attempt or not prior.is_dir():
                continue
            terminal = terminal_state(prior)
            if terminal is None:
                raise OperationError(f"prior worker attempt is unresolved: {prior.name}")
            if terminal.get("kind") != "start.exit":
                raise OperationError(
                    f"prior worker attempt consumed the full-build execution: {prior.name}"
                )
        with file_lock(context.path("work/full-build.lock"), blocking=False):
            pass
        attempt.mkdir(mode=0o700)
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


def remote_stop(context: Context, attempt_id: str) -> dict[str, object]:
    with file_lock(context.path("work/full-build-start.lock"), blocking=True):
        status = remote_attempt_status(context, attempt_id)
        if status["state"] == "terminal":
            return {"stop_requested": True, **status}
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
                status = remote_attempt_status(context, attempt_id)
                if status["state"] != "orphaned":
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
        if not isinstance(receipt, dict) or receipt.get("instance_id") != instance_id:
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
    rsync_download_directory(
        context,
        private_key,
        target,
        "/workspace/oracle-full-build/work/",
        destination / "work",
    )
    verified_work = validate_file_records(destination / "work", work_records)
    verified_preparation: list[dict[str, object]] = []
    if preparation_records is not None:
        preparation_destination = destination / "audit/preparation-attempts"
        rsync_download_directory(
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
    atomic_json(receipt_path, receipt)
    return receipt


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
    bindings = (
        (
            context.path("launch/instance.json"),
            context.path("launch/pre-transfer-instance-validation.json"),
        ),
        (
            context.path("launch/instance-ownership.json"),
            context.path("launch/instance-ownership-validation.json"),
        ),
    )
    for frozen_path, receipt_path in bindings:
        if not frozen_path.exists() and not receipt_path.exists():
            continue
        if not frozen_path.exists():
            raise OperationError("destroy ownership binding is incomplete")
        frozen = read_json(frozen_path)
        try:
            expected = calibration_package.validate_instance_against_offer(
                offer,
                create_result,
                frozen,
                context.image,
                context.limit("maximum_rental_rate_micro_usd_per_hour"),
                expected_label=context.label,
                require_running=False,
            )
        except ValueError as error:
            raise OperationError(
                f"recorded destroy ownership binding is invalid: {error}"
            ) from error
        if not receipt_path.exists():
            atomic_json(receipt_path, expected)
        elif read_json(receipt_path) != expected:
            raise OperationError(
                "destroy ownership receipt differs from the bound instance"
            )
        observed = True
    if live_instance is not None:
        if observed:
            try:
                live = calibration_package.instance_from_document(live_instance)
            except ValueError as error:
                raise OperationError(
                    f"live destroy target is not a provider instance: {error}"
                ) from error
            if str(live.get("id")) != instance_id or live.get("label") not in (
                context.label,
                None,
                "",
            ):
                raise OperationError(
                    "live destroy target differs from the durably bound instance"
                )
        else:
            try:
                frozen_live = calibration_package.freeze_instance_record(
                    create_result, live_instance
                )
            except ValueError as error:
                raise OperationError(
                    f"live destroy target is not the bound operation instance: {error}"
                ) from error
            record_instance_ownership(context, offer, create_result, frozen_live)
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
        "calibration_lifetime_cap_micro_usd": cents(
            "calibration_lifetime_cap_cents"
        ),
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


def cleanup_preworker_instance(context: Context, instance_id: str) -> dict[str, object]:
    failure = context.path("launch/preworker-instance-failure.log")
    if not failure.exists():
        atomic_bytes(
            failure,
            f"{utc_text()} pre-worker instance cleanup\n".encode("utf-8"),
        )
    destroy_instance(context, instance_id)
    charge = ensure_final_charge(context, instance_id)
    if charge is None:
        return invoice_pending_result(context, instance_id)
    return settle(context)


def ledger_reconciliation_state(
    context: Context, instance_id: str
) -> dict[str, object]:
    evidence = context.path("launch/result-loss-ledger-reconciliation.json")
    document = read_json(evidence)
    if not isinstance(document, dict) or document.get("instance_id") != instance_id:
        raise OperationError("result-loss reconciliation evidence is invalid")
    if not context.path("launch/destruction-confirmation.json").exists():
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
    context: Context, instance_id: str, attempt_id: str, reason: str
) -> dict[str, object]:
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
) -> dict[str, object]:
    del remote
    ensure_retrieved(context, instance_id, private_key, target, attempt_id)
    publish_verified_result(context, attempt_id)
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
        result["cost"] = cost_record_from_instance(instance_id, raw)
    except OperationError as error:
        result["cost_error"] = str(error)
        result["manual_stop_recommended"] = None
    if attempt_id is not None and context.path("launch/ssh/id_ed25519").is_file():
        private = context.path("launch/ssh/id_ed25519")
        ssh_url = completed_process(["vastai", "ssh-url", instance_id])
        target = parse_vast_ssh_target(ssh_url.stdout)
        remote = worker_status(context, private, target, attempt_id)
        result["remote"] = remote
        if remote["state"] in ("running", "starting"):
            result["state"] = "running"
        elif remote["state"] in ("terminal", "orphaned"):
            result["state"] = "terminal"
    cost = result.get("cost")
    if isinstance(cost, dict) and isinstance(
        cost.get("conservative_observed_total_micro_usd"), int
    ):
        result["manual_stop_recommended"] = (
            cost["conservative_observed_total_micro_usd"]
            >= context.limit("manual_stop_cost_micro_usd")
        )
    return result


def prepare(context: Context) -> dict[str, object]:
    with operation_lock(context.root):
        verify_reviewed_artifacts(context)
        verify_image(context)
        completed_process(["rsync", "--version"])
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
            return ledger_reconciliation_state(context, instance_id)
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
            destroy_instance(context, instance_id)
            charge = ensure_final_charge(context, instance_id)
            if charge is None:
                return invoice_pending_result(context, instance_id)
            return settle(context)
        if context.path("launch/preworker-instance-failure.log").exists():
            if instance_id is None:
                raise OperationError("pre-worker instance failure has no instance identity")
            return cleanup_preworker_instance(context, instance_id)
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
            return cleanup_preworker_instance(context, instance_id)
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
            return cleanup_preworker_instance(context, instance_id)
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
            )
        raise OperationError("acknowledged worker has no recoverable remote state")


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


def stop(context: Context) -> dict[str, object]:
    with operation_lock(context.root):
        if context.path("result/settlement/settlement-result.json").exists():
            return settle(context)
        instance_id = recorded_instance_id(context)
        if context.path("launch/result-loss-ledger-reconciliation.json").exists():
            if instance_id is None:
                raise OperationError("result-loss evidence has no instance identity")
            return ledger_reconciliation_state(context, instance_id)
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
                return cleanup_preworker_instance(context, instance_id)
            destroy_instance(context, instance_id)
            charge = ensure_final_charge(context, instance_id)
            if charge is None:
                return invoice_pending_result(context, instance_id)
            return settle(context)
        attempt_id = last_attempt_id(context)
        if attempt_id is None:
            return cleanup_preworker_instance(context, instance_id)
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
                context, instance_id, attempt_id, str(error)
            )
        if remote["state"] not in ("terminal", "orphaned"):
            return destroy_without_remote_retrieval(
                context,
                instance_id,
                attempt_id,
                "worker could not be reconciled to a terminal remote state",
            )
        try:
            return cleanup_terminal(
                context,
                instance_id,
                private_key,
                target,
                attempt_id,
                remote,
            )
        except OperationError as error:
            if context.path("launch/retrieval-verification.json").exists():
                raise
            return destroy_without_remote_retrieval(
                context, instance_id, attempt_id, str(error)
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    subparsers = parser.add_subparsers(dest="operation", required=True)
    subparsers.add_parser("prepare")
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--approve")
    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--watch", action="store_true")
    subparsers.add_parser("stop")
    subparsers.add_parser("_remote-verify-transfer", help=argparse.SUPPRESS)
    subparsers.add_parser("_remote-prepare", help=argparse.SUPPRESS)
    prepare_worker = subparsers.add_parser(
        "_remote-prepare-worker", help=argparse.SUPPRESS
    )
    prepare_worker.add_argument("--start-lock-fd", required=True, type=int)
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
    supervise = subparsers.add_parser("_remote-supervise", help=argparse.SUPPRESS)
    supervise.add_argument("--attempt", required=True)
    supervise.add_argument("--start-lock-fd", required=True, type=int)
    args = parser.parse_args()
    return args


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
            result = run(context, args.approve)
        elif args.operation == "status":
            result = status(context, args.watch)
        elif args.operation == "stop":
            result = stop(context)
        elif args.operation == "_remote-verify-transfer":
            result = remote_verify_transfer(context)
        elif args.operation == "_remote-prepare":
            result = remote_prepare(context)
        elif args.operation == "_remote-prepare-worker":
            result = remote_prepare_worker(context, args.start_lock_fd)
        elif args.operation == "_remote-worker":
            result = remote_worker(context, args.attempt)
        elif args.operation == "_remote-supervise":
            result = remote_supervise(context, args.attempt, args.start_lock_fd)
        elif args.operation == "_remote-controller":
            remote_controller(context, args.attempt)
        elif args.operation == "_remote-status":
            result = remote_status_report(context, args.attempt)
        elif args.operation == "_remote-stop":
            result = remote_stop(context, args.attempt)
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
