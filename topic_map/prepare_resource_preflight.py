#!/usr/bin/env python3
"""Prepare a compute-only BatchTopK preflight entirely on tmpfs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import struct
import subprocess
import sys
from array import array
from pathlib import Path


def _require_tmpfs(path: Path) -> None:
    probe = path if path.exists() else path.parent
    filesystem = subprocess.check_output(
        ["findmnt", "-n", "-o", "FSTYPE", "-T", str(probe)],
        text=True,
    ).strip()
    if filesystem != "tmpfs":
        raise ValueError(f"resource preflight must be prepared on tmpfs: {path}")


def prepare_resource_preflight(
    root: Path,
    *,
    learning_rows: int = 4096,
    evaluation_rows: int = 512,
    dimensions: int = 768,
    dictionary_size: int = 3072,
    average_k: int = 32,
    batch_size: int = 1000,
    steps: int = 20,
    seed: int = 112233,
) -> Path:
    if sys.byteorder != "little":
        raise RuntimeError("the FP32 preflight format requires a little-endian host")
    values = {
        "learning_rows": learning_rows,
        "evaluation_rows": evaluation_rows,
        "dimensions": dimensions,
        "dictionary_size": dictionary_size,
        "average_k": average_k,
        "batch_size": batch_size,
        "steps": steps,
    }
    for name, value in values.items():
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(f"{name} must be a positive integer")
    if average_k > dictionary_size:
        raise ValueError("average_k cannot exceed dictionary_size")
    if root.exists():
        raise FileExistsError(f"preflight root already exists: {root}")
    _require_tmpfs(root)
    root.mkdir(parents=False)
    output_directory = root / "output"
    output_directory.mkdir()

    total_rows = learning_rows + evaluation_rows
    matrix_path = root / "vectors.f32le"
    generator = random.Random(seed)
    with matrix_path.open("xb") as matrix:
        remaining = total_rows * dimensions
        while remaining:
            count = min(remaining, 64 * 1024)
            chunk = array(
                "f", (generator.uniform(-1.0, 1.0) for _ in range(count))
            )
            chunk.tofile(matrix)
            remaining -= count

    note_ids_path = root / "note-ids.bin"
    with note_ids_path.open("xb") as note_ids:
        for row in range(total_rows):
            note_ids.write(
                hashlib.sha256(
                    b"crec-113-resource-preflight-row"
                    + struct.pack("<Q", row)
                ).digest()
            )

    source_read_bytes = matrix_path.stat().st_size + note_ids_path.stat().st_size
    config = {
        "schema_version": 1,
        "purpose": (
            "CREC-113 discarded resource-only preflight; no semantic or "
            "quality conclusions"
        ),
        "input": {
            "matrix_path": str(matrix_path),
            "note_ids_path": str(note_ids_path),
            "dimensions": dimensions,
            "start_row": 0,
            "learning_rows": learning_rows,
            "evaluation_rows": evaluation_rows,
        },
        "model": {
            "dictionary_size": dictionary_size,
            "average_k": average_k,
            "batch_size": batch_size,
            "steps": steps,
            "learning_rate": 0.001,
            "seed": seed,
            "warmup_steps": max(1, steps // 10),
            "dead_tokens": 10_000_000,
            "auxiliary_k": min(dictionary_size, max(1, dimensions // 2)),
            "auxiliary_penalty": 1.0 / 32.0,
            "gradient_clip": 1.0,
            "maximum_relation_entries": (
                total_rows * min(dictionary_size, average_k * 8)
            ),
            "device": "cpu",
        },
        "io_budget": {
            "max_source_read_bytes": source_read_bytes,
            "max_durable_write_bytes": 32 * 1024 * 1024,
        },
        "output_path": str(output_directory / "relation"),
    }
    config_path = root / "config.json"
    temporary = root / ".config.json.tmp"
    with temporary.open("x", encoding="utf-8") as output:
        json.dump(config, output, allow_nan=False, sort_keys=True, indent=2)
        output.write("\n")
    os.replace(temporary, config_path)
    return config_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    arguments = parser.parse_args()
    print(prepare_resource_preflight(arguments.root))


if __name__ == "__main__":
    main()
