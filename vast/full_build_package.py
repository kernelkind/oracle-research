#!/usr/bin/env python3
"""Verify workload file manifests and exact provider invoice evidence."""

from __future__ import annotations

import hashlib
import json
import os
from decimal import Decimal, InvalidOperation
from pathlib import Path


SCHEMA_VERSION = 1
HASH_BUFFER_BYTES = 8 * 1024 * 1024


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
