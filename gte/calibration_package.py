#!/usr/bin/env python3
"""Freeze, verify, and bind the one-off GTE calibration package."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
from dataclasses import dataclass
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
from pathlib import Path


SCHEMA_VERSION = 1
ARTIFACT_KIND = "gte-calibration-package"
IDENTITY_SCHEMA_VERSION = 2
IDENTITY_KIND = "gte-calibration-execution-identity"
APPROVED_GPU_MODEL = "NVIDIA RTX PRO 6000 Blackwell Workstation Edition"
APPROVED_OFFER_GPU_MODEL = "RTX PRO 6000 WS"
MIN_DRIVER = (580, 95, 5)
MIN_RELIABILITY_MILLIONTHS = 995_000
MIN_HOST_MEMORY_BYTES = 128 * 1024**3
MIN_LOCAL_NVME_BYTES = 200_000_000_000
MIN_LOCAL_NVME_BANDWIDTH_BYTES_PER_SECOND = 1_000_000_000
REQUIRED_POWER_LIMIT_WATTS = 600
MIN_AVAILABLE_DURATION_SECONDS = 86_400
HASH_BUFFER_BYTES = 8 * 1024 * 1024
REQUIRED_FILES = (
    "bundle/model-lock.json",
    "corpus-root/ndb/data.mdb",
    "run/semantic-corpus/manifest.json",
    "run/semantic-corpus/ordered-event-ids.bin",
    "run/token-audit-semantic-v3/manifest.json",
    "run/batch-plan-semantic-v5/manifest.json",
    "run/representation/index/index-manifest.json",
    "run/representation/index/event-id-to-row.bin",
    "run/budget-ledger.json",
    "run/calibration-config.json",
    "run/vast-calibration-runbook.txt",
)


@dataclass(frozen=True)
class HostSnapshot:
    gpu_model: str
    gpu_device_uuid: str
    gpu_count: int
    gpu_power_limit_watts: int
    driver_version: str
    host_cpu: str
    host_memory_bytes: int
    local_nvme_bytes: int


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(HASH_BUFFER_BYTES):
            digest.update(chunk)
    return digest.hexdigest()


def package_files(root: Path, manifest_path: Path) -> list[Path]:
    root = root.resolve()
    try:
        manifest_relative = manifest_path.resolve().relative_to(root)
    except ValueError as error:
        raise ValueError("package manifest must be inside the package root") from error

    files = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"package contains a symbolic link: {path.relative_to(root)}")
        if path.is_dir():
            continue
        if not path.is_file():
            raise ValueError(f"package contains a non-regular file: {path.relative_to(root)}")
        relative = path.relative_to(root)
        if relative == manifest_relative:
            continue
        if relative.name == "lock.mdb":
            raise ValueError(f"package must not contain LMDB lock.mdb: {relative}")
        files.append(path)
    return files


def validate_required_files(root: Path, relative_paths: set[str]) -> None:
    missing = sorted(set(REQUIRED_FILES) - relative_paths)
    if missing:
        raise ValueError(f"package is missing required files: {missing}")
    if not any(path.startswith("bundle/model/") for path in relative_paths):
        raise ValueError("package contains no model files under bundle/model")


def atomic_write_json(path: Path, document: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    if temporary.exists():
        temporary.unlink()
    with temporary.open("x", encoding="utf-8") as output:
        json.dump(document, output, ensure_ascii=False, sort_keys=True, indent=2)
        output.write("\n")
        output.flush()
        os.fsync(output.fileno())
    temporary.replace(path)
    directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def write_package_manifest(root: Path, manifest_path: Path) -> dict[str, object]:
    root = root.resolve()
    files = package_files(root, manifest_path)
    records = []
    for path in files:
        relative = path.relative_to(root).as_posix()
        records.append(
            {
                "path": relative,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    validate_required_files(root, {record["path"] for record in records})
    document: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": ARTIFACT_KIND,
        "total_bytes": sum(record["bytes"] for record in records),
        "files": records,
    }
    atomic_write_json(manifest_path, document)
    return document


def read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"could not read JSON from {path}: {error}") from error


def verify_package(root: Path, manifest_path: Path) -> dict[str, object]:
    document = read_json(manifest_path)
    if (
        not isinstance(document, dict)
        or document.get("schema_version") != SCHEMA_VERSION
        or document.get("artifact_kind") != ARTIFACT_KIND
        or not isinstance(document.get("files"), list)
        or not document["files"]
    ):
        raise ValueError("package manifest has an incompatible identity")

    expected: dict[str, dict[str, object]] = {}
    for record in document["files"]:
        if (
            not isinstance(record, dict)
            or not isinstance(record.get("path"), str)
            or not record["path"]
            or Path(record["path"]).is_absolute()
            or ".." in Path(record["path"]).parts
            or not isinstance(record.get("bytes"), int)
            or record["bytes"] < 0
            or not isinstance(record.get("sha256"), str)
            or len(record["sha256"]) != 64
            or not all(character in "0123456789abcdef" for character in record["sha256"])
            or record["path"] in expected
        ):
            raise ValueError("package manifest contains an invalid file record")
        expected[record["path"]] = record

    root = root.resolve()
    actual_paths = {
        path.relative_to(root).as_posix() for path in package_files(root, manifest_path)
    }
    validate_required_files(root, actual_paths)
    if actual_paths != set(expected):
        raise ValueError(
            "package file set does not match its manifest: "
            f"missing={sorted(set(expected) - actual_paths)}, "
            f"extra={sorted(actual_paths - set(expected))}"
        )
    for relative, record in expected.items():
        path = root / relative
        if path.stat().st_size != record["bytes"] or sha256_file(path) != record["sha256"]:
            raise ValueError(f"package file {relative} does not match its manifest")
    if document.get("total_bytes") != sum(record["bytes"] for record in expected.values()):
        raise ValueError("package total byte count does not match its files")
    return document


def require_number(value: object, field: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"Vast offer field {field} is not numeric")
    number = Decimal(str(value))
    if not number.is_finite():
        raise ValueError(f"Vast offer field {field} is not finite")
    return number


def parse_driver(value: str) -> tuple[int, int, int]:
    try:
        parts = tuple(int(part) for part in value.split("."))
    except ValueError as error:
        raise ValueError(f"invalid driver version {value}") from error
    if len(parts) == 2:
        return (parts[0], parts[1], 0)
    if len(parts) != 3:
        raise ValueError(f"invalid driver version {value}")
    return parts


def created_instance_id(create_result: object) -> str:
    if not isinstance(create_result, dict) or create_result.get("success") is not True:
        raise ValueError("Vast create result is invalid")
    value = create_result.get("new_contract")
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, str))
        or not str(value).strip()
    ):
        raise ValueError("Vast create result has no instance ID")
    return str(value)


def freeze_create_result(raw_create_result: object) -> dict[str, object]:
    created_instance_id(raw_create_result)
    assert isinstance(raw_create_result, dict)
    return {
        "success": True,
        "new_contract": raw_create_result["new_contract"],
    }


def instance_from_document(document: object) -> dict[str, object]:
    if isinstance(document, dict) and "instances" in document:
        document = document.get("instances")
    if not isinstance(document, dict):
        raise ValueError("actual Vast instance must be one JSON object")
    return document


INSTANCE_RECORD_FIELDS = (
    "id",
    "machine_id",
    "bundle_id",
    "actual_status",
    "intended_status",
    "image_uuid",
    "gpu_name",
    "num_gpus",
    "disk_space",
    "dph_total",
    "is_bid",
    "verification",
)

TEMPLATE_RECORD_FIELDS = (
    "args_str",
    "env",
    "id",
    "hash_id",
    "name",
    "image",
    "onstart",
    "tag",
    "private",
    "recommended_disk_space",
    "runtype",
    "ssh_direct",
    "use_jupyter_lab",
    "use_ssh",
    "user",
)


def freeze_template_record(
    raw_templates: object, expected_hash: str, expected_image: str
) -> dict[str, object]:
    if (
        not expected_hash.strip()
        or not isinstance(raw_templates, list)
        or len(raw_templates) != 1
    ):
        raise ValueError("Vast template search must return exactly one template")
    template = raw_templates[0]
    if not isinstance(template, dict) or template.get("hash_id") != expected_hash:
        raise ValueError("Vast template does not match the selected template hash")
    effective_image = immutable_image_ref(template.get("image"))
    expected_image = immutable_image_ref(expected_image)
    if template.get("tag") not in (None, ""):
        raise ValueError("Vast template does not use the exact calibration image")
    if normalized_image_ref(effective_image) != normalized_image_ref(expected_image):
        raise ValueError("Vast template does not use the exact calibration image")
    if template.get("use_ssh") is not True or template.get("runtype") != "ssh":
        raise ValueError("Vast template must enable SSH")
    if template.get("private") is not True:
        raise ValueError("Vast template must remain private")
    if any(template.get(field) not in (None, "") for field in ("args_str", "env", "onstart", "user")):
        raise ValueError("Vast template must not contain startup overrides")
    if template.get("use_jupyter_lab") not in (None, False):
        raise ValueError("Vast template must not enable Jupyter")
    record = {field: template.get(field) for field in TEMPLATE_RECORD_FIELDS}
    record["effective_image"] = effective_image
    return record


def freeze_instance_record(create_result: object, raw_instance: object) -> dict[str, object]:
    expected_id = created_instance_id(create_result)
    instance = instance_from_document(raw_instance)
    if str(instance.get("id")) != expected_id:
        raise ValueError("actual instance does not match the Vast create result")
    return {field: instance.get(field) for field in INSTANCE_RECORD_FIELDS}


def normalized_image_ref(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("container image reference is invalid")
    normalized = value.strip()
    if normalized.startswith("docker.io/"):
        normalized = normalized[len("docker.io/") :]
    return normalized


def immutable_image_ref(value: object) -> str:
    normalized = normalized_image_ref(value)
    try:
        repository, digest = normalized.rsplit("@sha256:", 1)
    except ValueError as error:
        raise ValueError("container image must use an immutable digest") from error
    if (
        not repository
        or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
    ):
        raise ValueError("container image must use an immutable digest")
    return normalized


def build_execution_identity(
    descriptor_result: object,
    offer: object,
    create_result: object,
    instance: object,
    host: HostSnapshot,
) -> dict[str, object]:
    if not isinstance(descriptor_result, dict) or not isinstance(
        descriptor_result.get("descriptor"), dict
    ):
        raise ValueError("descriptor result is invalid")
    descriptor = descriptor_result["descriptor"]
    descriptor_json = descriptor_result.get("descriptor_json")
    descriptor_sha256 = descriptor_result.get("descriptor_sha256")
    try:
        parsed_descriptor = (
            json.loads(descriptor_json) if isinstance(descriptor_json, str) else None
        )
    except json.JSONDecodeError as error:
        raise ValueError("descriptor result does not contain valid exact JSON") from error
    descriptor_image = immutable_image_ref(descriptor.get("container_image"))
    if (
        not isinstance(descriptor_json, str)
        or not isinstance(descriptor_sha256, str)
        or hashlib.sha256(descriptor_json.encode("utf-8")).hexdigest()
        != descriptor_sha256
        or parsed_descriptor != descriptor
        or descriptor.get("execution_device") != "cuda"
    ):
        raise ValueError("descriptor result does not identify the exact CUDA representation")
    if not isinstance(offer, dict):
        raise ValueError("Vast offer must be one JSON object")
    instance = instance_from_document(instance)
    expected_instance_id = created_instance_id(create_result)

    offer_driver = offer.get("driver_version")
    offer_id = offer.get("id")
    offer_machine_id = offer.get("machine_id")
    offer_bundle_id = offer.get("bundle_id")
    instance_id = instance.get("id")
    instance_bundle_id = instance.get("bundle_id")
    reliability = int(
        (require_number(offer.get("reliability"), "reliability") * 1_000_000).to_integral_value(
            rounding=ROUND_FLOOR
        )
    )
    disk_bandwidth = int(
        (require_number(offer.get("disk_bw"), "disk_bw") * 1_000_000).to_integral_value(
            rounding=ROUND_FLOOR
        )
    )
    offer_duration = int(
        require_number(offer.get("duration"), "duration").to_integral_value(
            rounding=ROUND_FLOOR
        )
    )
    offer_rate = int(
        (require_number(offer.get("dph_total"), "dph_total") * 1_000_000).to_integral_value(
            rounding=ROUND_CEILING
        )
    )
    offer_power = require_number(offer.get("gpu_max_power"), "gpu_max_power")
    if (
        offer.get("gpu_name") != APPROVED_OFFER_GPU_MODEL
        or isinstance(offer_id, bool)
        or not isinstance(offer_id, (int, str))
        or not str(offer_id).strip()
        or isinstance(offer_machine_id, bool)
        or not isinstance(offer_machine_id, (int, str))
        or not str(offer_machine_id).strip()
        or isinstance(offer_bundle_id, bool)
        or not isinstance(offer_bundle_id, (int, str))
        or not str(offer_bundle_id).strip()
        or offer.get("num_gpus") != 1
        or offer_power != REQUIRED_POWER_LIMIT_WATTS
        or not isinstance(offer_driver, str)
        or parse_driver(offer_driver) < MIN_DRIVER
        or reliability < MIN_RELIABILITY_MILLIONTHS
        or disk_bandwidth < MIN_LOCAL_NVME_BANDWIDTH_BYTES_PER_SECOND
        or offer_duration < MIN_AVAILABLE_DURATION_SECONDS
        or offer_rate <= 0
        or offer.get("is_bid") is not False
        or offer.get("rentable") is not True
        or offer.get("verification") != "verified"
        or offer.get("vericode") != 1
    ):
        raise ValueError("Vast offer does not satisfy the approved calibration contract")

    instance_rate = int(
        (
            require_number(instance.get("dph_total"), "instance dph_total")
            * 1_000_000
        ).to_integral_value(rounding=ROUND_CEILING)
    )
    if (
        isinstance(instance_id, bool)
        or not isinstance(instance_id, (int, str))
        or not str(instance_id).strip()
        or str(instance_id) != expected_instance_id
        or instance.get("machine_id") != offer_machine_id
        or (
            instance_bundle_id is not None
            and instance_bundle_id != offer_bundle_id
        )
        or instance.get("actual_status") != "running"
        or instance.get("intended_status") != "running"
        or immutable_image_ref(instance.get("image_uuid")) != descriptor_image
        or instance.get("gpu_name") != APPROVED_OFFER_GPU_MODEL
        or instance.get("num_gpus") != 1
        or require_number(instance.get("disk_space"), "instance disk_space") < 200
        or instance_rate <= 0
        or instance.get("is_bid") is not False
        or instance.get("verification") != "verified"
    ):
        raise ValueError("actual Vast instance does not match the approved offer and image")
    if (
        host.gpu_model != APPROVED_GPU_MODEL
        or host.gpu_count != 1
        or host.gpu_power_limit_watts != REQUIRED_POWER_LIMIT_WATTS
        or parse_driver(host.driver_version) < MIN_DRIVER
        or not host.gpu_device_uuid.strip()
        or not host.host_cpu.strip()
        or host.host_memory_bytes < MIN_HOST_MEMORY_BYTES
        or host.local_nvme_bytes < MIN_LOCAL_NVME_BYTES
    ):
        raise ValueError("live host does not satisfy the approved calibration contract")

    return {
        "schema_version": IDENTITY_SCHEMA_VERSION,
        "artifact_kind": IDENTITY_KIND,
        "representation_descriptor_sha256": descriptor_sha256,
        "gpu_model": host.gpu_model,
        "gpu_device_uuid": host.gpu_device_uuid,
        "gpu_count": host.gpu_count,
        "gpu_power_limit_watts": host.gpu_power_limit_watts,
        "driver_version": host.driver_version,
        "machine_verified": True,
        "reliability_millionths": reliability,
        "host_cpu": host.host_cpu,
        "host_memory_bytes": host.host_memory_bytes,
        "local_nvme_bytes": host.local_nvme_bytes,
        "local_nvme_bandwidth_bytes_per_second": disk_bandwidth,
        "on_demand": True,
        "available_duration_seconds": offer_duration,
        "rental_provider": "vast.ai",
        "rental_offer_id": str(offer_id),
        "rental_instance_id": str(instance_id),
        "rental_rate_per_hour": instance_rate,
    }


def capture_host(nvidia_smi: Path, mount: Path) -> HostSnapshot:
    command = [
        str(nvidia_smi),
        "--query-gpu=name,uuid,power.limit,driver_version",
        "--format=csv,noheader,nounits",
    ]
    result = subprocess.run(command, check=True, text=True, capture_output=True)
    rows = list(csv.reader(line for line in result.stdout.splitlines() if line.strip()))
    if len(rows) != 1 or len(rows[0]) != 4:
        raise ValueError("nvidia-smi did not report exactly one complete GPU row")
    gpu_model, gpu_uuid, raw_power, driver = (value.strip() for value in rows[0])
    power = Decimal(raw_power)
    if power != power.to_integral_value():
        raise ValueError("GPU power limit is not a whole number of watts")

    cpu = ""
    for line in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines():
        if line.startswith("model name") and ":" in line:
            cpu = line.split(":", 1)[1].strip()
            break
    memory_bytes = 0
    for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
        if line.startswith("MemTotal:"):
            memory_bytes = int(line.split()[1]) * 1024
            break
    stat = os.statvfs(mount)
    return HostSnapshot(
        gpu_model=gpu_model,
        gpu_device_uuid=gpu_uuid,
        gpu_count=1,
        gpu_power_limit_watts=int(power),
        driver_version=driver,
        host_cpu=cpu,
        host_memory_bytes=memory_bytes,
        local_nvme_bytes=stat.f_blocks * stat.f_frsize,
    )


def load_one_offer(path: Path) -> object:
    document = read_json(path)
    if isinstance(document, list):
        if len(document) != 1:
            raise ValueError("offer file must contain exactly one Vast offer")
        return document[0]
    return document


def load_one_instance(path: Path) -> object:
    return instance_from_document(read_json(path))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="operation", required=True)

    manifest = subparsers.add_parser("manifest")
    manifest.add_argument("root", type=Path)
    manifest.add_argument("output", type=Path)

    verify = subparsers.add_parser("verify")
    verify.add_argument("root", type=Path)
    verify.add_argument("manifest", type=Path)

    freeze_instance = subparsers.add_parser("freeze-instance")
    freeze_instance.add_argument("create_result", type=Path)
    freeze_instance.add_argument("raw_instance", type=Path)
    freeze_instance.add_argument("output", type=Path)

    freeze_create = subparsers.add_parser("freeze-create")
    freeze_create.add_argument("raw_create_result", type=Path)
    freeze_create.add_argument("output", type=Path)

    freeze_template = subparsers.add_parser("freeze-template")
    freeze_template.add_argument("raw_templates", type=Path)
    freeze_template.add_argument("expected_hash")
    freeze_template.add_argument("expected_image")
    freeze_template.add_argument("output", type=Path)

    identity = subparsers.add_parser("capture-identity")
    identity.add_argument("descriptor", type=Path)
    identity.add_argument("offer", type=Path)
    identity.add_argument("create_result", type=Path)
    identity.add_argument("instance", type=Path)
    identity.add_argument("output", type=Path)
    identity.add_argument("--mount", type=Path, default=Path("/workspace"))
    identity.add_argument("--nvidia-smi", type=Path, default=Path("nvidia-smi"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.operation == "manifest":
        result = write_package_manifest(args.root, args.output)
    elif args.operation == "verify":
        result = verify_package(args.root, args.manifest)
    elif args.operation == "freeze-instance":
        result = freeze_instance_record(
            read_json(args.create_result), read_json(args.raw_instance)
        )
        atomic_write_json(args.output, result)
    elif args.operation == "freeze-create":
        result = freeze_create_result(read_json(args.raw_create_result))
        atomic_write_json(args.output, result)
    elif args.operation == "freeze-template":
        result = freeze_template_record(
            read_json(args.raw_templates), args.expected_hash, args.expected_image
        )
        atomic_write_json(args.output, result)
    else:
        host = capture_host(args.nvidia_smi, args.mount)
        result = build_execution_identity(
            read_json(args.descriptor),
            load_one_offer(args.offer),
            read_json(args.create_result),
            load_one_instance(args.instance),
            host,
        )
        atomic_write_json(args.output, result)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
