#!/usr/bin/env python3
"""Freeze and reconstruct the small transport for the complete GTE build."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path


SCHEMA_VERSION = 1
MODEL_PAYLOAD_KIND = "gte-stable-model-payload"
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
    else:
        result = reconstruct_corpus(
            args.compressed,
            args.destination,
            args.expected_bytes,
            args.expected_sha256,
            args.gzip,
        )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
