#!/usr/bin/env python3
"""Encode one frozen learning-first topic sample into a bound FP32 matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import stat
import struct
import sys
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Protocol


EMBEDDING_FORMAT = "learning-first-note-embedding-matrix-v1"
CANONICAL_TREE_HASH_RULE = (
    "sorted-relative-path-type-size-content-sha256-v1"
)
SAMPLE_SELECTION_RULE = (
    "semantic-order-prefix-author-hash-text-copy-disjoint-learning-first-v2"
)


def _plain_int(value: object, name: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"`{name}` must be an integer >= {minimum}")
    return value


def _mapping(value: object, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"`{name}` must be an object")
    return value


def _nonempty_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"`{name}` must be a nonempty string")
    return value


def _sha256_string(value: object, name: str) -> str:
    encoded = _nonempty_string(value, name)
    if (
        len(encoded) != 64
        or encoded != encoded.lower()
        or any(character not in "0123456789abcdef" for character in encoded)
    ):
        raise ValueError(f"`{name}` must be a lowercase SHA-256 hex digest")
    return encoded


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_tree_sha256(root: Path) -> str:
    """Hash one directory tree by relative names, types, sizes, and contents."""

    root_stat = root.lstat()
    if not stat.S_ISDIR(root_stat.st_mode):
        raise ValueError(f"canonical tree root is not a directory: {root}")
    digest = hashlib.sha256()
    digest.update(CANONICAL_TREE_HASH_RULE.encode("ascii") + b"\0")

    def visit(directory: Path, prefix: tuple[bytes, ...]) -> None:
        with os.scandir(directory) as iterator:
            entries = sorted(iterator, key=lambda entry: os.fsencode(entry.name))
        for entry in entries:
            name = os.fsencode(entry.name)
            relative_parts = (*prefix, name)
            relative = b"/".join(relative_parts)
            metadata = entry.stat(follow_symlinks=False)
            if stat.S_ISDIR(metadata.st_mode):
                digest.update(b"D")
                digest.update(struct.pack("<Q", len(relative)))
                digest.update(relative)
                visit(Path(entry.path), relative_parts)
                continue
            if not stat.S_ISREG(metadata.st_mode):
                raise ValueError(
                    "canonical trees may contain only directories and regular "
                    f"files: {Path(entry.path)}"
                )
            file_digest = hashlib.sha256()
            bytes_read = 0
            with open(entry.path, "rb") as source:
                while chunk := source.read(1024 * 1024):
                    bytes_read += len(chunk)
                    file_digest.update(chunk)
            if bytes_read != metadata.st_size:
                raise ValueError(
                    f"file changed while hashing canonical tree: {entry.path}"
                )
            digest.update(b"F")
            digest.update(struct.pack("<Q", len(relative)))
            digest.update(relative)
            digest.update(struct.pack("<Q", bytes_read))
            digest.update(file_digest.digest())

    visit(root, ())
    return digest.hexdigest()


@dataclass(frozen=True)
class EncoderDescriptor:
    model_id: str
    model_revision: str
    dimensions: int
    pooling: str
    maximum_tokens: int
    numeric_type: str

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "EncoderDescriptor":
        descriptor = cls(
            model_id=_nonempty_string(raw.get("model_id"), "encoder.model_id"),
            model_revision=_nonempty_string(
                raw.get("model_revision"), "encoder.model_revision"
            ),
            dimensions=_plain_int(
                raw.get("dimensions"), "encoder.dimensions", minimum=1
            ),
            pooling=_nonempty_string(raw.get("pooling"), "encoder.pooling"),
            maximum_tokens=_plain_int(
                raw.get("maximum_tokens"),
                "encoder.maximum_tokens",
                minimum=1,
            ),
            numeric_type=_nonempty_string(
                raw.get("numeric_type"), "encoder.numeric_type"
            ),
        )
        if descriptor.numeric_type != "float32":
            raise ValueError("only float32 output is supported")
        if descriptor.pooling != "cls-token-no-normalization-v1":
            raise ValueError("unsupported encoder pooling rule")
        return descriptor

    def to_dict(self) -> dict[str, str | int]:
        return asdict(self)


@dataclass(frozen=True)
class RuntimeDescriptor:
    canonical_tree_hash_rule: str
    model_tree_sha256: str
    dependencies_tree_sha256: str
    encoder_implementation_sha256: str
    container_image: str

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "RuntimeDescriptor":
        descriptor = cls(
            canonical_tree_hash_rule=_nonempty_string(
                raw.get("canonical_tree_hash_rule"),
                "runtime.canonical_tree_hash_rule",
            ),
            model_tree_sha256=_sha256_string(
                raw.get("model_tree_sha256"),
                "runtime.model_tree_sha256",
            ),
            dependencies_tree_sha256=_sha256_string(
                raw.get("dependencies_tree_sha256"),
                "runtime.dependencies_tree_sha256",
            ),
            encoder_implementation_sha256=_sha256_string(
                raw.get("encoder_implementation_sha256"),
                "runtime.encoder_implementation_sha256",
            ),
            container_image=_nonempty_string(
                raw.get("container_image"), "runtime.container_image"
            ),
        )
        if descriptor.canonical_tree_hash_rule != CANONICAL_TREE_HASH_RULE:
            raise ValueError("unsupported canonical tree hash rule")
        image_digest = descriptor.container_image.rpartition("@sha256:")[2]
        _sha256_string(image_digest, "runtime.container_image digest")
        return descriptor

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class SampleEmbeddingConfig:
    schema_version: int
    purpose: str
    sample_manifest_path: Path
    model_path: Path
    dependencies_path: Path
    encoder: EncoderDescriptor
    runtime: RuntimeDescriptor
    batch_size: int
    io_maximum_sample_artifact_bytes: int
    io_maximum_output_bytes: int
    output_path: Path

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "SampleEmbeddingConfig":
        schema_version = _plain_int(
            raw.get("schema_version"), "schema_version", minimum=1
        )
        if schema_version != 1:
            raise ValueError(f"unsupported schema version {schema_version}")
        io_budget = _mapping(raw.get("io_budget"), "io_budget")
        return cls(
            schema_version=schema_version,
            purpose=_nonempty_string(raw.get("purpose"), "purpose"),
            sample_manifest_path=Path(
                _nonempty_string(
                    raw.get("sample_manifest_path"), "sample_manifest_path"
                )
            ),
            model_path=Path(
                _nonempty_string(raw.get("model_path"), "model_path")
            ),
            dependencies_path=Path(
                _nonempty_string(
                    raw.get("dependencies_path"), "dependencies_path"
                )
            ),
            encoder=EncoderDescriptor.from_dict(
                _mapping(raw.get("encoder"), "encoder")
            ),
            runtime=RuntimeDescriptor.from_dict(
                _mapping(raw.get("runtime"), "runtime")
            ),
            batch_size=_plain_int(
                raw.get("batch_size"), "batch_size", minimum=1
            ),
            io_maximum_sample_artifact_bytes=_plain_int(
                io_budget.get("maximum_sample_artifact_bytes"),
                "io_budget.maximum_sample_artifact_bytes",
            ),
            io_maximum_output_bytes=_plain_int(
                io_budget.get("maximum_output_bytes"),
                "io_budget.maximum_output_bytes",
            ),
            output_path=Path(
                _nonempty_string(raw.get("output_path"), "output_path")
            ),
        )


@dataclass(frozen=True)
class SampleEncodingReport:
    total_rows: int
    learning_rows: int
    evaluation_rows: int
    sample_artifact_bytes_read: int
    output_bytes_written: int
    elapsed_seconds: float

    def to_dict(self) -> dict[str, int | float]:
        return asdict(self)


class BatchEncoder(Protocol):
    descriptor: EncoderDescriptor

    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        """Return one fixed-dimensional row for every input text."""


class TransformersClsEncoder:
    """Pinned local Transformers model with SentenceTransformers CLS pooling."""

    def __init__(self, model_path: Path, descriptor: EncoderDescriptor) -> None:
        try:
            import torch
            from transformers import AutoModel, AutoTokenizer
        except ImportError as error:
            raise RuntimeError(
                "transformers and torch are required for real sample encoding"
            ) from error

        self._torch = torch
        self.descriptor = descriptor
        self._tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            local_files_only=True,
            trust_remote_code=False,
        )
        self._model = AutoModel.from_pretrained(
            model_path,
            local_files_only=True,
            trust_remote_code=False,
            torch_dtype=torch.float32,
            attn_implementation="eager",
        )
        hidden_size = int(self._model.config.hidden_size)
        if hidden_size != descriptor.dimensions:
            raise ValueError(
                "model hidden size does not match frozen encoder dimensions: "
                f"{hidden_size} != {descriptor.dimensions}"
            )
        model_maximum = int(self._model.config.max_position_embeddings)
        if descriptor.maximum_tokens > model_maximum:
            raise ValueError(
                "frozen token limit exceeds model capacity: "
                f"{descriptor.maximum_tokens} > {model_maximum}"
            )
        self._model.eval()

    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        tokens = self._tokenizer(
            texts,
            add_special_tokens=True,
            padding=True,
            truncation=False,
            return_tensors="pt",
        )
        token_count = int(tokens["attention_mask"].sum(dim=1).max())
        if token_count > self.descriptor.maximum_tokens:
            raise ValueError(
                "sample note exceeds the frozen encoder token limit: "
                f"{token_count} > {self.descriptor.maximum_tokens}"
            )
        with self._torch.inference_mode():
            hidden = self._model(**tokens).last_hidden_state[:, 0, :]
        return hidden.to(dtype=self._torch.float32, device="cpu").tolist()


def _validated_sample(
    config: SampleEmbeddingConfig,
) -> tuple[dict[str, Any], Path, int, str]:
    manifest_bytes = config.sample_manifest_path.read_bytes()
    manifest_size = len(manifest_bytes)
    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
    manifest = json.loads(manifest_bytes)
    if manifest.get("schema_version") not in {2, 3}:
        raise ValueError("sample manifest schema is not supported")
    if manifest.get("selection_rule") != SAMPLE_SELECTION_RULE:
        raise ValueError("sample selection rule does not match the frozen rule")
    sample = _mapping(manifest.get("sample"), "sample_manifest.sample")
    sample_name = _nonempty_string(
        sample.get("file"), "sample_manifest.sample.file"
    )
    if Path(sample_name).name != sample_name:
        raise ValueError("sample filename must not contain a path")
    sample_path = config.sample_manifest_path.parent / sample_name
    sample_size = sample_path.stat().st_size
    expected_size = _plain_int(
        sample.get("bytes"), "sample_manifest.sample.bytes"
    )
    if sample_size != expected_size:
        raise ValueError("sample byte length differs from its manifest")
    sample_artifact_bytes = manifest_size + sample_size
    if sample_artifact_bytes > config.io_maximum_sample_artifact_bytes:
        raise ValueError(
            "sample artifact-read budget exceeded before encoding: "
            f"{sample_artifact_bytes} > "
            f"{config.io_maximum_sample_artifact_bytes}"
        )
    expected_matrix_bytes = (
        _plain_int(sample.get("records"), "sample_manifest.sample.records")
        * config.encoder.dimensions
        * 4
    )
    expected_note_id_bytes = (
        _plain_int(sample.get("records"), "sample_manifest.sample.records") * 32
    )
    if (
        expected_matrix_bytes + expected_note_id_bytes
        > config.io_maximum_output_bytes
    ):
        raise ValueError(
            "embedding output budget exceeded before encoding: "
            f"{expected_matrix_bytes + expected_note_id_bytes} > "
            f"{config.io_maximum_output_bytes}"
        )
    return manifest, sample_path, sample_artifact_bytes, manifest_sha256


@dataclass
class _ConsumedSampleIdentity:
    bytes_read: int = 0
    digest: Any = field(
        default_factory=hashlib.sha256, init=False, repr=False
    )

    def update(self, raw: bytes) -> None:
        self.bytes_read += len(raw)
        self.digest.update(raw)

    def hexdigest(self) -> str:
        return self.digest.hexdigest()


def _record_batches(
    sample_path: Path,
    *,
    learning_rows: int,
    evaluation_rows: int,
    batch_size: int,
    consumed_identity: _ConsumedSampleIdentity,
):
    expected_total = learning_rows + evaluation_rows
    seen_ids: set[bytes] = set()
    batch: list[tuple[bytes, str]] = []
    row = 0
    with sample_path.open("rb") as source:
        for line_number, raw_line in enumerate(source, start=1):
            consumed_identity.update(raw_line)
            try:
                line = raw_line.decode("utf-8")
                record = json.loads(line)
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise ValueError(
                    f"sample line {line_number} is not valid UTF-8 JSON"
                ) from error
            if row >= expected_total:
                raise ValueError("sample contains more rows than its split quotas")
            expected_split = "learning" if row < learning_rows else "evaluation"
            if record.get("split") != expected_split:
                raise ValueError(
                    "sample is not in frozen learning-first split order at "
                    f"row {row}"
                )
            note_id_hex = _nonempty_string(
                record.get("note_id"), f"sample[{row}].note_id"
            )
            try:
                note_id = bytes.fromhex(note_id_hex)
            except ValueError as error:
                raise ValueError(f"sample[{row}].note_id is not hex") from error
            if len(note_id) != 32:
                raise ValueError(f"sample[{row}].note_id is not 32 bytes")
            if note_id in seen_ids:
                raise ValueError("sample NoteIds are not unique")
            seen_ids.add(note_id)
            content = record.get("content")
            if not isinstance(content, str) or not content.strip():
                raise ValueError(f"sample[{row}].content is empty")
            batch.append((note_id, content))
            row += 1
            if len(batch) == batch_size:
                yield batch
                batch = []
    if batch:
        yield batch
    if row != expected_total:
        raise ValueError(
            f"sample row count differs from split quotas: {row} != "
            f"{expected_total}"
        )


def _write_batch(
    vectors,
    note_records: list[tuple[bytes, str]],
    *,
    dimensions: int,
    matrix_output,
    note_id_output,
    matrix_digest,
    note_id_digest,
) -> int:
    if len(vectors) != len(note_records):
        raise ValueError("encoder returned the wrong number of rows")
    written = 0
    for vector, (note_id, _) in zip(vectors, note_records, strict=True):
        if len(vector) != dimensions:
            raise ValueError(
                "encoder returned the wrong dimensions: "
                f"{len(vector)} != {dimensions}"
            )
        values = [float(value) for value in vector]
        if not all(math.isfinite(value) for value in values):
            raise ValueError("encoder returned a non-finite value")
        encoded = struct.pack(f"<{dimensions}f", *values)
        matrix_output.write(encoded)
        note_id_output.write(note_id)
        matrix_digest.update(encoded)
        note_id_digest.update(note_id)
        written += len(encoded) + len(note_id)
    return written


def _actual_runtime_descriptor(
    config: SampleEmbeddingConfig,
) -> RuntimeDescriptor:
    return RuntimeDescriptor(
        canonical_tree_hash_rule=CANONICAL_TREE_HASH_RULE,
        model_tree_sha256=_canonical_tree_sha256(config.model_path),
        dependencies_tree_sha256=_canonical_tree_sha256(
            config.dependencies_path
        ),
        encoder_implementation_sha256=_hash_file(Path(__file__)),
        container_image=config.runtime.container_image,
    )


def _verified_runtime_before_encoding(
    config: SampleEmbeddingConfig,
) -> RuntimeDescriptor:
    actual = _actual_runtime_descriptor(config)
    for field_name, label in (
        ("model_tree_sha256", "model tree"),
        ("dependencies_tree_sha256", "dependencies tree"),
        ("encoder_implementation_sha256", "encoder implementation"),
    ):
        if getattr(actual, field_name) != getattr(config.runtime, field_name):
            raise ValueError(
                f"{label} hash differs from frozen config before encoding"
            )
    return actual


def _verify_runtime_after_encoding(
    config: SampleEmbeddingConfig,
    before: RuntimeDescriptor,
) -> None:
    after = _actual_runtime_descriptor(config)
    for field_name, label in (
        ("model_tree_sha256", "model tree"),
        ("dependencies_tree_sha256", "dependencies tree"),
        ("encoder_implementation_sha256", "encoder implementation"),
    ):
        if getattr(after, field_name) != getattr(before, field_name):
            raise ValueError(f"{label} changed during encoding")


def encode_sample(
    config: SampleEmbeddingConfig,
    *,
    encoder: BatchEncoder | None = None,
) -> SampleEncodingReport:
    """Encode a frozen sample once and atomically publish its bound matrix."""

    started = time.monotonic()
    (
        manifest,
        sample_path,
        sample_artifact_bytes,
        sample_manifest_sha256,
    ) = _validated_sample(config)
    if config.output_path.exists():
        raise FileExistsError(f"output path already exists: {config.output_path}")
    runtime = _verified_runtime_before_encoding(config)
    if encoder is None:
        encoder = TransformersClsEncoder(config.model_path, config.encoder)
    if encoder.descriptor != config.encoder:
        raise ValueError("runtime encoder identity differs from frozen config")

    learning_rows = _plain_int(
        manifest.get("learning_rows"), "sample_manifest.learning_rows", minimum=1
    )
    evaluation_rows = _plain_int(
        manifest.get("evaluation_rows"),
        "sample_manifest.evaluation_rows",
        minimum=1,
    )
    sample_spec = _mapping(manifest.get("sample"), "sample_manifest.sample")
    expected_rows = _plain_int(
        sample_spec.get("records"), "sample_manifest.sample.records", minimum=2
    )
    if learning_rows + evaluation_rows != expected_rows:
        raise ValueError("sample split quotas do not equal its record count")
    consumed_sample = _ConsumedSampleIdentity()

    config.output_path.parent.mkdir(parents=True, exist_ok=True)
    staging: Path | None = Path(
        tempfile.mkdtemp(
            prefix=f".{config.output_path.name}.",
            dir=config.output_path.parent,
        )
    )
    matrix_digest = hashlib.sha256()
    note_id_digest = hashlib.sha256()
    output_bytes = 0
    try:
        assert staging is not None
        matrix_path = staging / "vectors.f32le"
        note_ids_path = staging / "note-ids.bin"
        with matrix_path.open("xb") as matrix_output, note_ids_path.open(
            "xb"
        ) as note_id_output:
            for batch in _record_batches(
                sample_path,
                learning_rows=learning_rows,
                evaluation_rows=evaluation_rows,
                batch_size=config.batch_size,
                consumed_identity=consumed_sample,
            ):
                output_bytes += _write_batch(
                    encoder.encode_batch([content for _, content in batch]),
                    batch,
                    dimensions=config.encoder.dimensions,
                    matrix_output=matrix_output,
                    note_id_output=note_id_output,
                    matrix_digest=matrix_digest,
                    note_id_digest=note_id_digest,
                )
                if output_bytes > config.io_maximum_output_bytes:
                    raise ValueError(
                        "embedding output budget exceeded during encoding"
                    )
            matrix_output.flush()
            os.fsync(matrix_output.fileno())
            note_id_output.flush()
            os.fsync(note_id_output.fileno())

        expected_sample_bytes = _plain_int(
            sample_spec.get("bytes"), "sample_manifest.sample.bytes"
        )
        if consumed_sample.bytes_read != expected_sample_bytes:
            raise ValueError(
                "sample bytes consumed differ in length from its manifest"
            )
        sample_sha256 = consumed_sample.hexdigest()
        if sample_sha256 != sample_spec.get("sha256"):
            raise ValueError(
                "sample bytes consumed differ from its manifest hash"
            )
        _verify_runtime_after_encoding(config, runtime)

        embedding_manifest = {
            "schema_version": 1,
            "embedding_format": EMBEDDING_FORMAT,
            "purpose": config.purpose,
            "sample_manifest_sha256": sample_manifest_sha256,
            "sample_sha256": sample_sha256,
            "sample_selection_rule": manifest["selection_rule"],
            "learning_rows": learning_rows,
            "evaluation_rows": evaluation_rows,
            "total_rows": expected_rows,
            "encoder": config.encoder.to_dict(),
            "runtime": runtime.to_dict(),
            "runtime_verification": "verified-before-and-after-encoding-v1",
            "batch_size": config.batch_size,
            "files": {
                "vectors.f32le": {
                    "bytes": matrix_path.stat().st_size,
                    "sha256": matrix_digest.hexdigest(),
                },
                "note-ids.bin": {
                    "bytes": note_ids_path.stat().st_size,
                    "sha256": note_id_digest.hexdigest(),
                },
            },
        }
        manifest_bytes = (
            json.dumps(
                embedding_manifest,
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                indent=2,
            )
            + "\n"
        ).encode()
        if output_bytes + len(manifest_bytes) > config.io_maximum_output_bytes:
            raise ValueError(
                "embedding output budget exceeded before manifest publication"
            )
        with (staging / "manifest.json").open("xb") as output:
            output.write(manifest_bytes)
            output.flush()
            os.fsync(output.fileno())
        output_bytes += len(manifest_bytes)
        os.replace(staging, config.output_path)
        parent_descriptor = os.open(config.output_path.parent, os.O_RDONLY)
        try:
            os.fsync(parent_descriptor)
        finally:
            os.close(parent_descriptor)
        staging = None
    finally:
        if staging is not None and staging.exists():
            shutil.rmtree(staging)

    return SampleEncodingReport(
        total_rows=expected_rows,
        learning_rows=learning_rows,
        evaluation_rows=evaluation_rows,
        sample_artifact_bytes_read=sample_artifact_bytes,
        output_bytes_written=output_bytes,
        elapsed_seconds=time.monotonic() - started,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    arguments = parser.parse_args()
    config = SampleEmbeddingConfig.from_dict(
        json.loads(arguments.config.read_text(encoding="utf-8"))
    )
    report = encode_sample(config)
    print(
        json.dumps(
            report.to_dict(),
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
