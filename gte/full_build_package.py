#!/usr/bin/env python3
"""Freeze and reconstruct the small transport for the complete GTE build."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_CEILING
from pathlib import Path


SCHEMA_VERSION = 1
MODEL_PAYLOAD_KIND = "gte-stable-model-payload"
HASH_BUFFER_BYTES = 8 * 1024 * 1024
MAXIMUM_FULL_BUILD_RATE_MICRO_USD = 1_359_260


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(HASH_BUFFER_BYTES):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"could not read JSON from {path}: {error}") from error


def atomic_write_json(path: Path, document: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.next")
    temporary.unlink(missing_ok=True)
    with temporary.open("x", encoding="utf-8") as output:
        json.dump(document, output, ensure_ascii=False, sort_keys=True, indent=2)
        output.write("\n")
        output.flush()
        os.fsync(output.fileno())
    temporary.replace(path)
    sync_directory(path.parent)


def sync_directory(path: Path) -> None:
    directory = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def package_files(root: Path, manifest_path: Path) -> list[Path]:
    root = root.resolve()
    try:
        manifest_relative = manifest_path.resolve().relative_to(root)
    except ValueError as error:
        raise ValueError("manifest must be inside its package root") from error
    files = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"package contains a symbolic link: {path.relative_to(root)}")
        if path.is_dir():
            continue
        if not path.is_file():
            raise ValueError(
                f"package contains a non-regular file: {path.relative_to(root)}"
            )
        relative = path.relative_to(root)
        if relative == manifest_relative:
            continue
        if relative.name == "lock.mdb":
            raise ValueError(f"package must not contain LMDB lock.mdb: {relative}")
        files.append(path)
    return files


def write_manifest(root: Path, manifest_path: Path, artifact_kind: str) -> dict[str, object]:
    if not artifact_kind.strip():
        raise ValueError("artifact kind must be nonempty")
    root = root.resolve()
    manifest_path.with_name(f".{manifest_path.name}.next").unlink(missing_ok=True)
    records = []
    for path in package_files(root, manifest_path):
        relative = path.relative_to(root).as_posix()
        records.append(
            {
                "path": relative,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    if not records:
        raise ValueError("package contains no files")
    document: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": artifact_kind,
        "total_bytes": sum(record["bytes"] for record in records),
        "files": records,
    }
    atomic_write_json(manifest_path, document)
    return document


def verify_manifest(root: Path, manifest_path: Path) -> dict[str, object]:
    document = read_json(manifest_path)
    if (
        not isinstance(document, dict)
        or document.get("schema_version") != SCHEMA_VERSION
        or not isinstance(document.get("artifact_kind"), str)
        or not document["artifact_kind"]
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
            or not is_sha256(record["sha256"])
            or record["path"] in expected
        ):
            raise ValueError("package manifest contains an invalid file record")
        expected[record["path"]] = record
    root = root.resolve()
    actual_paths = {
        path.relative_to(root).as_posix() for path in package_files(root, manifest_path)
    }
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


def is_runtime_payload(relative: str) -> bool:
    return not any(part in {".huggingface", ".cache"} for part in Path(relative).parts)


def model_payload_identity(model_lock_path: Path) -> dict[str, object]:
    lock = read_json(model_lock_path)
    if (
        not isinstance(lock, dict)
        or lock.get("schema_version") != 1
        or not isinstance(lock.get("model_id"), str)
        or not isinstance(lock.get("model_revision"), str)
        or not isinstance(lock.get("files"), list)
    ):
        raise ValueError("model lock has an incompatible identity")
    files = []
    seen = set()
    for record in lock["files"]:
        if (
            not isinstance(record, dict)
            or not isinstance(record.get("path"), str)
            or not record["path"]
            or Path(record["path"]).is_absolute()
            or ".." in Path(record["path"]).parts
            or not isinstance(record.get("bytes"), int)
            or record["bytes"] < 0
            or not isinstance(record.get("sha256"), str)
            or not is_sha256(record["sha256"])
            or record["path"] in seen
        ):
            raise ValueError("model lock contains an invalid file record")
        seen.add(record["path"])
        if is_runtime_payload(record["path"]):
            files.append(
                {
                    "path": record["path"],
                    "bytes": record["bytes"],
                    "sha256": record["sha256"],
                }
            )
    if not files:
        raise ValueError("model lock contains no runtime payload files")
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": MODEL_PAYLOAD_KIND,
        "model_id": lock["model_id"],
        "model_revision": lock["model_revision"],
        "files": files,
    }


def write_model_payload_identity(
    model_lock_path: Path, output_path: Path
) -> dict[str, object]:
    identity = model_payload_identity(model_lock_path)
    atomic_write_json(output_path, identity)
    return identity


def verify_model_payload(
    model_dir: Path, model_lock_path: Path, identity_path: Path
) -> dict[str, object]:
    expected = model_payload_identity(model_lock_path)
    if read_json(identity_path) != expected:
        raise ValueError("stable model-payload identity does not match the legacy model lock")
    actual_paths = set()
    for path in sorted(model_dir.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"model payload contains a symbolic link: {path}")
        if not path.is_file():
            continue
        relative = path.relative_to(model_dir).as_posix()
        if is_runtime_payload(relative):
            actual_paths.add(relative)
    expected_records = {record["path"]: record for record in expected["files"]}
    if actual_paths != set(expected_records):
        raise ValueError(
            "model payload file set does not match: "
            f"missing={sorted(set(expected_records) - actual_paths)}, "
            f"extra={sorted(actual_paths - set(expected_records))}"
        )
    for relative, record in expected_records.items():
        path = model_dir / relative
        if path.stat().st_size != record["bytes"] or sha256_file(path) != record["sha256"]:
            raise ValueError(f"model payload file {relative} does not match")
    return expected


def restore_model_metadata(model_dir: Path, metadata_dir: Path) -> None:
    if not model_dir.is_dir() or not metadata_dir.is_dir():
        raise ValueError("model and transported metadata directories must exist")
    for path in metadata_dir.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"transported model metadata contains a symbolic link: {path}")
    target = model_dir / ".huggingface"
    temporary = model_dir / ".huggingface.next"
    if temporary.exists():
        shutil.rmtree(temporary)
    shutil.copytree(metadata_dir, temporary)
    if target.exists():
        shutil.rmtree(target)
    temporary.replace(target)
    sync_directory(model_dir)


def reconstruct_corpus(
    compressed_path: Path,
    destination_path: Path,
    expected_bytes: int,
    expected_sha256: str,
    gzip_path: Path,
) -> dict[str, object]:
    if expected_bytes <= 0 or not is_sha256(expected_sha256):
        raise ValueError("corpus identity is invalid")
    if destination_path.exists():
        if (
            destination_path.is_file()
            and destination_path.stat().st_size == expected_bytes
            and sha256_file(destination_path) == expected_sha256
        ):
            return {
                "bytes": expected_bytes,
                "sha256": expected_sha256,
                "path": str(destination_path),
            }
        raise ValueError(
            f"existing corpus destination does not match its exact identity: {destination_path}"
        )
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination_path.with_name(f"{destination_path.name}.next")
    temporary.unlink(missing_ok=True)
    try:
        with temporary.open("xb") as output:
            subprocess.run(
                [str(gzip_path), "--decompress", "--quiet", "--stdout", str(compressed_path)],
                check=True,
                stdout=output,
            )
            output.flush()
            os.fsync(output.fileno())
        if temporary.stat().st_size != expected_bytes or sha256_file(temporary) != expected_sha256:
            raise ValueError("decompressed corpus does not match its exact identity")
        temporary.replace(destination_path)
        sync_directory(destination_path.parent)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return {
        "bytes": expected_bytes,
        "sha256": expected_sha256,
        "path": str(destination_path),
    }


def is_sha256(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def decimal_field(document: dict[str, object], field: str) -> Decimal:
    value = document.get(field)
    if isinstance(value, bool):
        raise ValueError(f"Vast offer {field} is not numeric")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise ValueError(f"Vast offer {field} is not numeric") from error
    if not result.is_finite():
        raise ValueError(f"Vast offer {field} is not finite")
    return result


def positive_integer_field(document: dict[str, object], field: str) -> int:
    value = decimal_field(document, field)
    if value <= 0 or value != value.to_integral_value():
        raise ValueError(f"Vast offer {field} must be a positive integer")
    return int(value)


def driver_version(value: object) -> tuple[int, ...]:
    if not isinstance(value, str) or not value:
        raise ValueError("Vast offer driver_version is invalid")
    try:
        parts = tuple(int(part) for part in value.split("."))
    except ValueError as error:
        raise ValueError("Vast offer driver_version is invalid") from error
    if not parts or any(part < 0 for part in parts):
        raise ValueError("Vast offer driver_version is invalid")
    return parts + (0,) * (3 - len(parts))


def validate_full_build_offer(offer: object, offer_id: str) -> dict[str, object]:
    if not isinstance(offer_id, str) or not offer_id.isdecimal() or int(offer_id) <= 0:
        raise ValueError("selected Vast offer ID must be a positive integer")
    if not isinstance(offer, dict):
        raise ValueError("selected Vast offer is not an object")
    identifier = offer.get("id")
    if isinstance(identifier, bool) or str(identifier) != offer_id:
        raise ValueError("selected Vast offer does not match its ID")

    exact = {
        "gpu_name": "RTX PRO 6000 WS",
        "num_gpus": 1,
        "cpu_arch": "amd64",
        "rentable": True,
        "rented": False,
        "is_bid": False,
        "verification": "verified",
        "vericode": 1,
    }
    for field, expected in exact.items():
        if offer.get(field) != expected:
            raise ValueError(f"Vast offer {field} does not satisfy the full-build gate")
    for field in ("machine_id", "bundle_id"):
        positive_integer_field(offer, field)
    if decimal_field(offer, "gpu_max_power") != Decimal("600"):
        raise ValueError("Vast offer gpu_max_power does not satisfy the full-build gate")

    minimums = {
        "reliability": Decimal("0.995"),
        "cpu_ram": Decimal("137439"),
        "disk_space": Decimal("200"),
        "disk_bw": Decimal("1000"),
        "inet_down": Decimal("500"),
        "inet_up": Decimal("100"),
        "direct_port_count": Decimal("1"),
        "duration": Decimal("172800"),
    }
    for field, minimum in minimums.items():
        if decimal_field(offer, field) < minimum:
            raise ValueError(f"Vast offer {field} is below the full-build gate")

    for field in ("inet_down_cost", "inet_up_cost"):
        cost = decimal_field(offer, field)
        if cost < 0 or cost > Decimal("0.02"):
            raise ValueError(f"Vast offer {field} exceeds the full-build gate")

    if driver_version(offer.get("driver_version")) < (580, 95, 5):
        raise ValueError("Vast offer driver_version is below the full-build gate")
    rate = decimal_field(offer, "dph_total")
    if rate <= 0:
        raise ValueError("Vast offer dph_total must be positive")
    rate_micro_usd = int(
        (rate * Decimal(1_000_000)).to_integral_value(rounding=ROUND_CEILING)
    )
    if rate_micro_usd > MAXIMUM_FULL_BUILD_RATE_MICRO_USD:
        raise ValueError("Vast offer dph_total exceeds the full-build gate")
    return offer


def freeze_full_build_offer(
    source_path: Path,
    offer_id: str,
    output_path: Path,
    approved_offer_path: Path | None = None,
) -> list[dict[str, object]]:
    approved = None
    if approved_offer_path is not None:
        approved_document = read_json(approved_offer_path)
        if not isinstance(approved_document, list) or len(approved_document) != 1:
            raise ValueError("approved offer record must contain exactly one offer")
        approved = validate_full_build_offer(approved_document[0], offer_id)

    document = read_json(source_path)
    if not isinstance(document, list):
        raise ValueError("Vast offer search must return a JSON array")
    matches = [
        offer
        for offer in document
        if isinstance(offer, dict)
        and not isinstance(offer.get("id"), bool)
        and str(offer.get("id")) == offer_id
    ]
    if len(matches) != 1:
        raise ValueError("selected Vast offer must occur exactly once")
    selected = validate_full_build_offer(matches[0], offer_id)

    if approved is not None:
        for field in ("id", "machine_id", "bundle_id"):
            if selected.get(field) != approved.get(field):
                raise ValueError(f"refreshed offer does not match approved offer {field}")
        for field in ("dph_total", "inet_down_cost", "inet_up_cost"):
            if decimal_field(selected, field) > decimal_field(approved, field):
                raise ValueError(f"refreshed offer is worse than approved offer {field}")

    frozen = [selected]
    atomic_write_json(output_path, frozen)
    return frozen


def parse_utc_timestamp(value: str, field: str) -> datetime:
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field} must be an exact UTC timestamp") from error
    return parsed.replace(tzinfo=timezone.utc)


def exact_instance_invoice_rows(
    source_path: Path, instance_id: str, label: str
) -> tuple[list[dict[str, object]], Decimal, str]:
    document = read_json(source_path)
    if not isinstance(document, dict) or not isinstance(document.get("results"), list):
        raise ValueError("finalized provider invoice is not a complete result set")
    results = document["results"]
    count = document.get("count")
    total = document.get("total")
    if (
        document.get("success") is not True
        or "next_token" not in document
        or document["next_token"] is not None
        or isinstance(count, bool)
        or not isinstance(count, int)
        or isinstance(total, bool)
        or not isinstance(total, int)
        or count != len(results)
        or total != len(results)
    ):
        raise ValueError("finalized provider invoice is not a complete result set")
    expected_source = f"instance-{instance_id}"
    matches = [
        row
        for row in results
        if isinstance(row, dict) and row.get("source") == expected_source
    ]
    if not matches:
        raise ValueError("finalized provider invoice is not available yet")
    amount = Decimal(0)
    encoded_rows = []
    for row in matches:
        metadata = row.get("metadata")
        invoice_label = metadata.get("label") if isinstance(metadata, dict) else None
        if row.get("type") != "instance" or invoice_label not in (None, "", label):
            raise ValueError("finalized provider invoice has an invalid exact-instance row")
        value = row.get("amount")
        if isinstance(value, bool):
            raise ValueError("finalized provider invoice amount is invalid")
        try:
            charge = Decimal(str(value))
        except (InvalidOperation, ValueError) as error:
            raise ValueError("finalized provider invoice amount is invalid") from error
        if not charge.is_finite() or charge < 0:
            raise ValueError("finalized provider invoice amount is invalid")
        amount += charge
        try:
            encoded_rows.append(
                json.dumps(
                    row,
                    ensure_ascii=False,
                    allow_nan=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
            )
        except (TypeError, ValueError) as error:
            raise ValueError("finalized provider invoice row is not canonical JSON") from error
    micro_usd = amount * Decimal(1_000_000)
    if micro_usd != micro_usd.to_integral_value():
        raise ValueError("finalized provider invoice is not exact to micro-USD")
    encoded_rows.sort()
    rows_sha256 = hashlib.sha256("\n".join(encoded_rows).encode("utf-8")).hexdigest()
    return matches, amount, rows_sha256


def finalize_provider_invoice(
    source_path: Path,
    confirmation_path: Path,
    instance_id: str,
    label: str,
    not_before_utc: str,
    observed_at_utc: str,
    confirmation_observed_at_utc: str,
    output_path: Path,
) -> dict[str, object]:
    """Freeze a charge only after two stable post-billing-boundary observations."""
    if not instance_id.isdecimal() or int(instance_id) <= 0 or not label.strip():
        raise ValueError("finalized provider invoice identity is invalid")
    not_before = parse_utc_timestamp(not_before_utc, "invoice not-before")
    observed_at = parse_utc_timestamp(observed_at_utc, "first invoice observation")
    confirmation_observed_at = parse_utc_timestamp(
        confirmation_observed_at_utc, "confirmation invoice observation"
    )
    if observed_at < not_before:
        raise ValueError("first invoice observation precedes the not-before time")
    if confirmation_observed_at - observed_at < timedelta(minutes=5):
        raise ValueError("invoice observations must be at least five minutes apart")

    matches, amount, rows_sha256 = exact_instance_invoice_rows(
        source_path, instance_id, label
    )
    _confirmation_matches, confirmation_amount, confirmation_rows_sha256 = (
        exact_instance_invoice_rows(confirmation_path, instance_id, label)
    )
    if rows_sha256 != confirmation_rows_sha256 or amount != confirmation_amount:
        raise ValueError("finalized provider invoice is not stable across observations")
    micro_usd = amount * Decimal(1_000_000)
    expected_source = f"instance-{instance_id}"
    result = {
        "schema_version": SCHEMA_VERSION,
        "instance_id": instance_id,
        "source": expected_source,
        "label": label,
        "amount_usd": format(amount, "f"),
        "actual_charge_micro_usd": int(micro_usd),
        "invoice_rows": len(matches),
        "invoice_not_before_utc": not_before_utc,
        "invoice_observed_at_utc": observed_at_utc,
        "confirmation_observed_at_utc": confirmation_observed_at_utc,
        "invoice_snapshot_sha256": sha256_file(source_path),
        "confirmation_invoice_snapshot_sha256": sha256_file(confirmation_path),
        "exact_instance_rows_sha256": rows_sha256,
    }
    atomic_write_json(output_path, result)
    return result


def merge_provider_invoice_pages(
    page_paths: list[Path], output_path: Path
) -> dict[str, object]:
    """Merge one complete, ordered Vast invoice pagination sequence."""
    if not page_paths:
        raise ValueError("provider invoice requires at least one page")
    results: list[object] = []
    expected_total: int | None = None
    seen_rows: set[str] = set()
    for index, page_path in enumerate(page_paths):
        page = read_json(page_path)
        if not isinstance(page, dict) or not isinstance(page.get("results"), list):
            raise ValueError("provider invoice page is invalid")
        count = page.get("count")
        total = page.get("total")
        next_token = page.get("next_token")
        if (
            page.get("success") is not True
            or "next_token" not in page
            or isinstance(count, bool)
            or not isinstance(count, int)
            or count != len(page["results"])
            or isinstance(total, bool)
            or not isinstance(total, int)
            or total < 0
            or (index + 1 < len(page_paths) and not isinstance(next_token, str))
            or (isinstance(next_token, str) and not next_token)
            or (index + 1 == len(page_paths) and next_token is not None)
        ):
            raise ValueError("provider invoice page sequence is not terminal and complete")
        if expected_total is None:
            expected_total = total
        elif total != expected_total:
            raise ValueError("provider invoice pages disagree about the total")
        for row in page["results"]:
            encoded = json.dumps(
                row,
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
            if digest in seen_rows:
                raise ValueError("provider invoice pagination repeated a row")
            seen_rows.add(digest)
            results.append(row)
    assert expected_total is not None
    if len(results) != expected_total:
        raise ValueError("provider invoice pages do not cover the reported total")
    merged = {
        "success": True,
        "count": len(results),
        "total": expected_total,
        "next_token": None,
        "results": results,
    }
    atomic_write_json(output_path, merged)
    return merged


def validate_provider_invoice_page(page_path: Path) -> dict[str, object]:
    """Reject empty or error output before one fetched invoice page is published."""
    try:
        page = read_json(page_path)
    except ValueError as error:
        raise ValueError(f"provider invoice page is invalid: {error}") from error
    if not isinstance(page, dict) or not isinstance(page.get("results"), list):
        raise ValueError("provider invoice page is invalid")
    count = page.get("count")
    total = page.get("total")
    next_token = page.get("next_token")
    if (
        page.get("success") is not True
        or "next_token" not in page
        or isinstance(count, bool)
        or not isinstance(count, int)
        or count != len(page["results"])
        or isinstance(total, bool)
        or not isinstance(total, int)
        or total < count
        or (next_token is not None and not isinstance(next_token, str))
        or isinstance(next_token, str)
        and not next_token
    ):
        raise ValueError("provider invoice page is invalid")
    return page


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="operation", required=True)

    manifest = subparsers.add_parser("manifest")
    manifest.add_argument("root", type=Path)
    manifest.add_argument("output", type=Path)
    manifest.add_argument("artifact_kind")

    verify = subparsers.add_parser("verify")
    verify.add_argument("root", type=Path)
    verify.add_argument("manifest", type=Path)

    model_identity = subparsers.add_parser("model-payload-identity")
    model_identity.add_argument("model_lock", type=Path)
    model_identity.add_argument("output", type=Path)

    verify_model = subparsers.add_parser("verify-model-payload")
    verify_model.add_argument("model_dir", type=Path)
    verify_model.add_argument("model_lock", type=Path)
    verify_model.add_argument("identity", type=Path)

    restore_metadata = subparsers.add_parser("restore-model-metadata")
    restore_metadata.add_argument("model_dir", type=Path)
    restore_metadata.add_argument("metadata_dir", type=Path)

    corpus = subparsers.add_parser("reconstruct-corpus")
    corpus.add_argument("compressed", type=Path)
    corpus.add_argument("destination", type=Path)
    corpus.add_argument("expected_bytes", type=int)
    corpus.add_argument("expected_sha256")
    corpus.add_argument("--gzip", type=Path, default=Path("/usr/bin/gzip"))

    offer = subparsers.add_parser("freeze-offer")
    offer.add_argument("source", type=Path)
    offer.add_argument("offer_id")
    offer.add_argument("output", type=Path)
    offer.add_argument("--approved", type=Path)

    invoice = subparsers.add_parser("finalize-provider-invoice")
    invoice.add_argument("source", type=Path)
    invoice.add_argument("confirmation", type=Path)
    invoice.add_argument("instance_id")
    invoice.add_argument("label")
    invoice.add_argument("not_before_utc")
    invoice.add_argument("observed_at_utc")
    invoice.add_argument("confirmation_observed_at_utc")
    invoice.add_argument("output", type=Path)

    merge_invoices = subparsers.add_parser("merge-provider-invoice-pages")
    merge_invoices.add_argument("output", type=Path)
    merge_invoices.add_argument("pages", nargs="+", type=Path)

    validate_invoice_page = subparsers.add_parser("validate-provider-invoice-page")
    validate_invoice_page.add_argument("page", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.operation == "manifest":
        result = write_manifest(args.root, args.output, args.artifact_kind)
    elif args.operation == "verify":
        result = verify_manifest(args.root, args.manifest)
    elif args.operation == "model-payload-identity":
        result = write_model_payload_identity(args.model_lock, args.output)
    elif args.operation == "verify-model-payload":
        result = verify_model_payload(args.model_dir, args.model_lock, args.identity)
    elif args.operation == "restore-model-metadata":
        restore_model_metadata(args.model_dir, args.metadata_dir)
        result = {"model_dir": str(args.model_dir), "metadata": "restored"}
    elif args.operation == "reconstruct-corpus":
        result = reconstruct_corpus(
            args.compressed,
            args.destination,
            args.expected_bytes,
            args.expected_sha256,
            args.gzip,
        )
    elif args.operation == "freeze-offer":
        result = freeze_full_build_offer(
            args.source, args.offer_id, args.output, args.approved
        )
    elif args.operation == "finalize-provider-invoice":
        result = finalize_provider_invoice(
            args.source,
            args.confirmation,
            args.instance_id,
            args.label,
            args.not_before_utc,
            args.observed_at_utc,
            args.confirmation_observed_at_utc,
            args.output,
        )
    elif args.operation == "merge-provider-invoice-pages":
        result = merge_provider_invoice_pages(args.pages, args.output)
    else:
        result = validate_provider_invoice_page(args.page)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
