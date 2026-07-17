#!/usr/bin/env python3
"""Download once and checksum-lock the exact GTE model snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path


MODEL_ID = "Alibaba-NLP/gte-Qwen2-7B-instruct"
MODEL_REVISION = "a8d08b36ada9cacfe34c4d6f80957772a025daf2"
SCHEMA_VERSION = 1
BUFFER_BYTES = 8 * 1024 * 1024


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(BUFFER_BYTES):
            digest.update(chunk)
    return digest.hexdigest()


def model_files(model_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in model_dir.rglob("*")
        if path.is_file() and ".cache" not in path.relative_to(model_dir).parts
    )


def write_lock(model_dir: Path, lock_path: Path) -> dict[str, object]:
    if not model_dir.is_dir():
        raise ValueError(f"model directory does not exist: {model_dir}")
    files = model_files(model_dir)
    if not files:
        raise ValueError("model directory contains no lockable files")
    document: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "files": [
            {
                "path": path.relative_to(model_dir).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in files
        ],
    }
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = lock_path.with_name(f".{lock_path.name}.tmp")
    if temporary.exists():
        temporary.unlink()
    with temporary.open("x", encoding="utf-8") as output:
        json.dump(document, output, ensure_ascii=False, sort_keys=True, indent=2)
        output.write("\n")
        output.flush()
        os.fsync(output.fileno())
    temporary.replace(lock_path)
    directory = os.open(lock_path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)
    return document


def verify_bundle(model_dir: Path, lock_path: Path) -> dict[str, object]:
    try:
        document = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"could not read model lock: {error}") from error
    if (
        not isinstance(document, dict)
        or document.get("schema_version") != SCHEMA_VERSION
        or document.get("model_id") != MODEL_ID
        or document.get("model_revision") != MODEL_REVISION
        or not isinstance(document.get("files"), list)
        or not document["files"]
    ):
        raise ValueError("model lock has an incompatible identity")

    expected_paths: set[str] = set()
    for record in document["files"]:
        if not isinstance(record, dict):
            raise ValueError("model lock contains a non-object file record")
        relative = record.get("path")
        size = record.get("bytes")
        checksum = record.get("sha256")
        if (
            not isinstance(relative, str)
            or not relative
            or Path(relative).is_absolute()
            or ".." in Path(relative).parts
            or not isinstance(size, int)
            or size < 0
            or not isinstance(checksum, str)
            or len(checksum) != 64
        ):
            raise ValueError("model lock contains an invalid file record")
        if relative in expected_paths:
            raise ValueError(f"model lock repeats file {relative}")
        expected_paths.add(relative)
        path = model_dir / relative
        if (
            not path.is_file()
            or path.stat().st_size != size
            or sha256_file(path) != checksum
        ):
            raise ValueError(f"model file {relative} does not match its lock")

    actual_paths = {
        path.relative_to(model_dir).as_posix() for path in model_files(model_dir)
    }
    if actual_paths != expected_paths:
        missing = sorted(expected_paths - actual_paths)
        extra = sorted(actual_paths - expected_paths)
        raise ValueError(f"model file set does not match its lock: missing={missing}, extra={extra}")
    return document


def prepare(bundle_root: Path) -> dict[str, object]:
    from huggingface_hub import snapshot_download

    model_dir = bundle_root / "model"
    model_dir.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id=MODEL_ID,
        revision=MODEL_REVISION,
        local_dir=model_dir,
        local_dir_use_symlinks=False,
        resume_download=True,
    )
    lock_path = bundle_root / "model-lock.json"
    write_lock(model_dir, lock_path)
    return verify_bundle(model_dir, lock_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("prepare", "verify"))
    parser.add_argument("bundle_root", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.operation == "prepare":
        result = prepare(args.bundle_root)
    else:
        result = verify_bundle(
            args.bundle_root / "model", args.bundle_root / "model-lock.json"
        )
    print(
        json.dumps(
            {
                "model_id": result["model_id"],
                "model_revision": result["model_revision"],
                "files": len(result["files"]),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
