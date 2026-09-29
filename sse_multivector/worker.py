#!/usr/bin/env python3
"""Run one source-bound Sub-Sentence Encoder inference job."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import os
import platform
import shutil
import stat
import struct
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence


SCHEMA_VERSION = 1
VECTOR_FORMAT = "row-major-f32le-v1"
POOLING_RULE = "selected-contextual-token-mean-linear-relu-linear-v1"
BYTE_SPAN_RULE = "complete-token-contained-in-utf8-byte-span-union-v2"
TREE_HASH_RULE = "sorted-relative-path-type-size-content-sha256-v1"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _file_identity(path: Path) -> tuple[int, int, int, int, int]:
    metadata = path.stat()
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def canonical_tree_sha256(root: Path) -> str:
    """Hash a regular-file directory tree with the repository's frozen rule."""

    metadata = root.lstat()
    if not stat.S_ISDIR(metadata.st_mode):
        raise ValueError(f"canonical tree root is not a directory: {root}")
    digest = hashlib.sha256()
    digest.update(TREE_HASH_RULE.encode("ascii") + b"\0")

    def visit(directory: Path, prefix: tuple[bytes, ...]) -> None:
        with os.scandir(directory) as iterator:
            entries = sorted(iterator, key=lambda entry: os.fsencode(entry.name))
        for entry in entries:
            name = os.fsencode(entry.name)
            relative_parts = (*prefix, name)
            relative = b"/".join(relative_parts)
            entry_metadata = entry.stat(follow_symlinks=False)
            if stat.S_ISDIR(entry_metadata.st_mode):
                digest.update(b"D")
                digest.update(struct.pack("<Q", len(relative)))
                digest.update(relative)
                visit(Path(entry.path), relative_parts)
                continue
            if not stat.S_ISREG(entry_metadata.st_mode):
                raise ValueError(
                    "canonical trees may contain only directories and regular "
                    f"files: {Path(entry.path)}"
                )
            file_digest = hashlib.sha256()
            size = 0
            with open(entry.path, "rb") as source:
                while chunk := source.read(1024 * 1024):
                    size += len(chunk)
                    file_digest.update(chunk)
            if size != entry_metadata.st_size:
                raise ValueError(
                    f"file changed while hashing canonical tree: {entry.path}"
                )
            digest.update(b"F")
            digest.update(struct.pack("<Q", len(relative)))
            digest.update(relative)
            digest.update(struct.pack("<Q", size))
            digest.update(file_digest.digest())

    visit(root, ())
    return digest.hexdigest()


def _expect_object(value: object, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"`{name}` must be an object")
    return value


def _expect_fields(
    value: dict[str, Any],
    name: str,
    expected: set[str],
) -> None:
    unexpected = sorted(set(value) - expected)
    missing = sorted(expected - set(value))
    if unexpected:
        raise ValueError(f"`{name}` contains unexpected field `{unexpected[0]}`")
    if missing:
        raise ValueError(f"`{name}` is missing field `{missing[0]}`")


def _expect_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"`{name}` must be a nonempty string")
    return value


def _expect_int(value: object, name: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"`{name}` must be an integer >= {minimum}")
    return value


def _expect_sha256(value: object, name: str) -> str:
    digest = _expect_string(value, name)
    if (
        len(digest) != 64
        or digest != digest.lower()
        or any(character not in "0123456789abcdef" for character in digest)
    ):
        raise ValueError(f"`{name}` must be a lowercase SHA-256 digest")
    return digest


def _expect_lower_hex(value: object, name: str, length: int) -> str:
    encoded = _expect_string(value, name)
    if (
        len(encoded) != length
        or encoded != encoded.lower()
        or any(character not in "0123456789abcdef" for character in encoded)
    ):
        raise ValueError(
            f"`{name}` must contain exactly {length} lowercase hexadecimal digits"
        )
    return encoded


@dataclass(frozen=True)
class SubjectInput:
    subject_id: str
    byte_spans: tuple[tuple[int, int], ...]


@dataclass(frozen=True)
class NoteInput:
    note_id: str
    text: str
    subjects: tuple[SubjectInput, ...]


@dataclass(frozen=True)
class EncodedSubject:
    note_id: str
    subject_id: str
    vector: tuple[float, ...]
    selected_token_indices: tuple[int, ...]
    selected_token_ids: tuple[int, ...]
    token_count: int


@dataclass(frozen=True)
class ModelDescriptor:
    base_model: str
    dimensions: int
    maximum_tokens: int
    pooling: str

    @classmethod
    def from_json(cls, raw: object) -> "ModelDescriptor":
        value = _expect_object(raw, "model")
        _expect_fields(
            value,
            "model",
            {
                "base_model",
                "dimensions",
                "maximum_tokens",
                "pooling",
            },
        )
        descriptor = cls(
            base_model=_expect_string(value["base_model"], "model.base_model"),
            dimensions=_expect_int(value["dimensions"], "model.dimensions", minimum=1),
            maximum_tokens=_expect_int(
                value["maximum_tokens"],
                "model.maximum_tokens",
                minimum=1,
            ),
            pooling=_expect_string(value["pooling"], "model.pooling"),
        )
        if descriptor.pooling != POOLING_RULE:
            raise ValueError(f"unsupported pooling rule `{descriptor.pooling}`")
        return descriptor

    def to_json(self) -> dict[str, str | int]:
        return {
            "base_model": self.base_model,
            "dimensions": self.dimensions,
            "maximum_tokens": self.maximum_tokens,
            "pooling": self.pooling,
        }


@dataclass(frozen=True)
class WorkerConfig:
    request_path: Path
    request_sha256: str
    checkpoint_path: Path
    checkpoint_sha256: str
    base_model_artifact_path: Path
    base_model_artifact_tree_sha256: str
    model: ModelDescriptor
    device: str
    container_image: str
    note_batch_size: int
    output_path: Path

    @classmethod
    def load(cls, path: Path) -> "WorkerConfig":
        raw = json.loads(path.read_text(encoding="utf-8"))
        value = _expect_object(raw, "config")
        _expect_fields(
            value,
            "config",
            {
                "schema_version",
                "request_path",
                "request_sha256",
                "checkpoint_path",
                "checkpoint_sha256",
                "base_model_artifact_path",
                "base_model_artifact_tree_sha256",
                "model",
                "device",
                "container_image",
                "note_batch_size",
                "output_path",
            },
        )
        if _expect_int(value["schema_version"], "schema_version") != SCHEMA_VERSION:
            raise ValueError("unsupported worker config schema version")
        device = _expect_string(value["device"], "device")
        if device != "cpu":
            raise ValueError("the diagnostic worker currently supports only `cpu`")
        container_image = _expect_string(value["container_image"], "container_image")
        if container_image.startswith("sha256:"):
            image_digest = container_image.removeprefix("sha256:")
        else:
            _, separator, image_digest = container_image.rpartition("@sha256:")
            if not separator:
                raise ValueError(
                    "`container_image` must be an immutable sha256 image identity"
                )
        _expect_sha256(image_digest, "container_image digest")
        return cls(
            request_path=Path(_expect_string(value["request_path"], "request_path")),
            request_sha256=_expect_sha256(value["request_sha256"], "request_sha256"),
            checkpoint_path=Path(
                _expect_string(value["checkpoint_path"], "checkpoint_path")
            ),
            checkpoint_sha256=_expect_sha256(
                value["checkpoint_sha256"], "checkpoint_sha256"
            ),
            base_model_artifact_path=Path(
                _expect_string(
                    value["base_model_artifact_path"],
                    "base_model_artifact_path",
                )
            ),
            base_model_artifact_tree_sha256=_expect_sha256(
                value["base_model_artifact_tree_sha256"],
                "base_model_artifact_tree_sha256",
            ),
            model=ModelDescriptor.from_json(value["model"]),
            device=device,
            container_image=container_image,
            note_batch_size=_expect_int(
                value["note_batch_size"], "note_batch_size", minimum=1
            ),
            output_path=Path(_expect_string(value["output_path"], "output_path")),
        )


@dataclass(frozen=True)
class WorkerReport:
    row_count: int
    dimensions: int
    output_path: Path


def _byte_span_to_character_span(
    text: str,
    span: tuple[int, int],
) -> tuple[int, int]:
    encoded = text.encode("utf-8")
    start, end = span
    if start < 0 or end <= start or end > len(encoded):
        raise ValueError(f"invalid UTF-8 byte span [{start}, {end})")
    try:
        character_start = len(encoded[:start].decode("utf-8"))
        character_end = len(encoded[:end].decode("utf-8"))
    except UnicodeDecodeError as error:
        raise ValueError(
            f"UTF-8 byte span [{start}, {end}) is not on character boundaries"
        ) from error
    return character_start, character_end


def select_token_indices(
    text: str,
    byte_spans: Sequence[tuple[int, int]],
    token_offsets: Sequence[tuple[int, int]],
) -> tuple[int, ...]:
    """Select complete tokens contained in the union of exact UTF-8 byte spans."""

    if not byte_spans:
        raise ValueError("a subject mask must contain at least one byte span")
    spans = sorted(
        _byte_span_to_character_span(text, span) for span in byte_spans
    )
    character_spans = []
    for start, end in spans:
        if character_spans and start <= character_spans[-1][1]:
            previous_start, previous_end = character_spans[-1]
            character_spans[-1] = (previous_start, max(previous_end, end))
        else:
            character_spans.append((start, end))
    selected = []
    for index, (token_start, token_end) in enumerate(token_offsets):
        if token_start == token_end == 0:
            continue
        if token_start < 0 or token_end <= token_start or token_end > len(text):
            raise ValueError(f"token offset [{token_start}, {token_end}) is invalid")
        if any(
            span_start <= token_start and token_end <= span_end
            for span_start, span_end in character_spans
        ):
            selected.append(index)
    if not selected:
        raise ValueError(
            "subject span selects no complete tokenizer token under the "
            "upstream containment rule"
        )
    return tuple(selected)


def validate_token_lengths(
    note_lengths: Sequence[tuple[str, int]],
    *,
    maximum_tokens: int,
) -> None:
    for note_id, length in note_lengths:
        if length > maximum_tokens:
            raise ValueError(
                f"note {note_id} tokenizes to {length} tokens, exceeding "
                f"{maximum_tokens}; truncation is forbidden"
            )


def _load_request(path: Path) -> tuple[str, tuple[NoteInput, ...]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    value = _expect_object(raw, "request")
    _expect_fields(
        value,
        "request",
        {"schema_version", "proposal_sha256", "notes"},
    )
    if _expect_int(value["schema_version"], "request.schema_version") != 1:
        raise ValueError("unsupported worker request schema version")
    proposal_sha256 = _expect_sha256(
        value["proposal_sha256"], "request.proposal_sha256"
    )
    raw_notes = value["notes"]
    if not isinstance(raw_notes, list) or not raw_notes:
        raise ValueError("`request.notes` must be a nonempty array")
    notes = []
    note_ids = set()
    subject_ids = set()
    for note_index, raw_note in enumerate(raw_notes):
        note_name = f"request.notes[{note_index}]"
        note = _expect_object(raw_note, note_name)
        _expect_fields(note, note_name, {"note_id", "text", "subjects"})
        note_id = _expect_lower_hex(note["note_id"], f"{note_name}.note_id", 64)
        if note_id in note_ids:
            raise ValueError(f"request repeats note ID {note_id}")
        note_ids.add(note_id)
        text = _expect_string(note["text"], f"{note_name}.text")
        raw_subjects = note["subjects"]
        if not isinstance(raw_subjects, list) or not raw_subjects:
            raise ValueError(f"`{note_name}.subjects` must be a nonempty array")
        subjects = []
        previous_span_start = -1
        for subject_index, raw_subject in enumerate(raw_subjects):
            subject_name = f"{note_name}.subjects[{subject_index}]"
            subject = _expect_object(raw_subject, subject_name)
            _expect_fields(
                subject,
                subject_name,
                {"subject_id", "byte_spans"},
            )
            subject_id = _expect_lower_hex(
                subject["subject_id"], f"{subject_name}.subject_id", 16
            )
            if subject_id in subject_ids:
                raise ValueError(f"request repeats subject ID {subject_id}")
            subject_ids.add(subject_id)
            raw_spans = subject["byte_spans"]
            if not isinstance(raw_spans, list) or not raw_spans:
                raise ValueError(
                    f"`{subject_name}.byte_spans` must be a nonempty array"
                )
            spans = []
            previous_span_start = -1
            for span_index, raw_span in enumerate(raw_spans):
                span_name = f"{subject_name}.byte_spans[{span_index}]"
                if not isinstance(raw_span, list) or len(raw_span) != 2:
                    raise ValueError(f"`{span_name}` must be [start, end]")
                start = _expect_int(raw_span[0], f"{span_name}[0]")
                end = _expect_int(raw_span[1], f"{span_name}[1]")
                if end <= start or start < previous_span_start:
                    raise ValueError(f"`{span_name}` is empty or out of source order")
                _byte_span_to_character_span(text, (start, end))
                spans.append((start, end))
                previous_span_start = start
            subjects.append(
                SubjectInput(
                    subject_id=subject_id,
                    byte_spans=tuple(spans),
                )
            )
        notes.append(
            NoteInput(
                note_id=note_id,
                text=text,
                subjects=tuple(subjects),
            )
        )
    return proposal_sha256, tuple(notes)


class OfficialSseEncoder:
    """Clean inference implementation for the official Lightning checkpoint."""

    def __init__(self, config: WorkerConfig) -> None:
        try:
            import torch
            from transformers import AutoConfig, AutoTokenizer, T5EncoderModel
        except ImportError as error:
            raise RuntimeError(
                "torch and transformers are required for SSE inference"
            ) from error

        self._torch = torch
        self._maximum_tokens = config.model.maximum_tokens
        self._dimensions = config.model.dimensions
        self._batch_size = config.note_batch_size
        self._tokenizer = AutoTokenizer.from_pretrained(
            config.base_model_artifact_path,
            local_files_only=True,
            trust_remote_code=False,
            use_fast=True,
        )
        if not self._tokenizer.is_fast:
            raise ValueError("SSE requires a fast tokenizer with offset mappings")

        encoder_config = AutoConfig.from_pretrained(
            config.base_model_artifact_path,
            local_files_only=True,
            trust_remote_code=False,
        )
        if getattr(encoder_config, "model_type", None) != "t5":
            raise ValueError("the pinned SSE backbone must use T5")
        self._encoder = T5EncoderModel(encoder_config)

        with torch.serialization.safe_globals([argparse.Namespace]):
            checkpoint = torch.load(
                config.checkpoint_path,
                map_location="cpu",
                mmap=True,
                weights_only=True,
            )
        if not isinstance(checkpoint, dict) or not isinstance(
            checkpoint.get("state_dict"), dict
        ):
            raise ValueError("checkpoint does not contain a Lightning state_dict")
        hyperparameters = checkpoint.get("hyper_parameters")
        params = (
            hyperparameters.get("params") if isinstance(hyperparameters, dict) else None
        )
        if params is not None:
            checkpoint_model_name = getattr(params, "model_name", None)
            checkpoint_dimensions = getattr(params, "final_output_dim", None)
            if checkpoint_model_name != config.model.base_model:
                raise ValueError(
                    "checkpoint backbone does not match the pinned base model"
                )
            expected_dimensions = (
                int(checkpoint_dimensions)
                if checkpoint_dimensions is not None
                else int(encoder_config.hidden_size)
            )
            if expected_dimensions != config.model.dimensions:
                raise ValueError(
                    "checkpoint output dimension does not match the config"
                )

        state = checkpoint["state_dict"]
        encoder_state = {
            key.removeprefix("encoder."): value
            for key, value in state.items()
            if key.startswith("encoder.")
        }
        self._encoder.load_state_dict(encoder_state, strict=True)
        linear1_weight = state.get("mlp.linear1.weight")
        linear1_bias = state.get("mlp.linear1.bias")
        linear2_weight = state.get("mlp.linear2.weight")
        linear2_bias = state.get("mlp.linear2.bias")
        if any(
            value is None
            for value in (
                linear1_weight,
                linear1_bias,
                linear2_weight,
                linear2_bias,
            )
        ):
            raise ValueError("checkpoint is missing the SSE projection MLP")
        input_dimensions = int(linear1_weight.shape[1])
        hidden_dimensions = int(linear1_weight.shape[0])
        output_dimensions = int(linear2_weight.shape[0])
        if (
            input_dimensions != int(encoder_config.hidden_size)
            or int(linear2_weight.shape[1]) != hidden_dimensions
            or output_dimensions != config.model.dimensions
        ):
            raise ValueError("checkpoint projection dimensions are inconsistent")
        self._linear1 = torch.nn.Linear(input_dimensions, hidden_dimensions)
        self._linear2 = torch.nn.Linear(hidden_dimensions, output_dimensions)
        self._linear1.load_state_dict(
            {"weight": linear1_weight, "bias": linear1_bias}, strict=True
        )
        self._linear2.load_state_dict(
            {"weight": linear2_weight, "bias": linear2_bias}, strict=True
        )
        self._encoder.float().eval()
        self._linear1.float().eval()
        self._linear2.float().eval()
        del checkpoint
        del state

    def encode(self, notes: Sequence[NoteInput]) -> Sequence[EncodedSubject]:
        torch = self._torch
        rows = []
        with torch.inference_mode():
            for start in range(0, len(notes), self._batch_size):
                batch = notes[start : start + self._batch_size]
                tokens = self._tokenizer(
                    [note.text for note in batch],
                    add_special_tokens=True,
                    padding=True,
                    truncation=False,
                    return_attention_mask=True,
                    return_offsets_mapping=True,
                    return_tensors="pt",
                )
                offsets = tokens.pop("offset_mapping")
                attention = tokens["attention_mask"]
                input_ids = tokens["input_ids"]
                lengths = attention.sum(dim=1).tolist()
                validate_token_lengths(
                    tuple(
                        (note.note_id, int(length))
                        for note, length in zip(batch, lengths, strict=True)
                    ),
                    maximum_tokens=self._maximum_tokens,
                )
                hidden = self._encoder(**tokens).last_hidden_state
                for batch_index, note in enumerate(batch):
                    note_offsets = [
                        (int(pair[0]), int(pair[1]))
                        for pair in offsets[batch_index].tolist()
                    ]
                    for subject in note.subjects:
                        selected = select_token_indices(
                            note.text,
                            subject.byte_spans,
                            note_offsets,
                        )
                        selected_tensor = torch.tensor(selected, dtype=torch.long)
                        pooled = (
                            hidden[batch_index]
                            .index_select(0, selected_tensor)
                            .mean(dim=0)
                        )
                        projected = self._linear2(torch.relu(self._linear1(pooled)))
                        vector = tuple(
                            float(value) for value in projected.float().cpu().tolist()
                        )
                        rows.append(
                            EncodedSubject(
                                note_id=note.note_id,
                                subject_id=subject.subject_id,
                                vector=vector,
                                selected_token_indices=selected,
                                selected_token_ids=tuple(
                                    int(input_ids[batch_index, index].item())
                                    for index in selected
                                ),
                                token_count=int(lengths[batch_index]),
                            )
                        )
        return rows


def _runtime_metadata(encoder: object, worker_sha256: str) -> dict[str, Any]:
    packages = {}
    for name in ("torch", "transformers", "tokenizers"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = "not-installed"
    return {
        "python": platform.python_version(),
        "packages": packages,
        "encoder_class": f"{type(encoder).__module__}.{type(encoder).__qualname__}",
        "worker_sha256": worker_sha256,
    }


def _flatten_expected_rows(
    notes: Sequence[NoteInput],
) -> tuple[tuple[str, str], ...]:
    return tuple(
        (note.note_id, subject.subject_id)
        for note in notes
        for subject in note.subjects
    )


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )


def run_worker(
    config_path: Path | str,
) -> WorkerReport:
    config_path = Path(config_path)
    config = WorkerConfig.load(config_path)
    if config.output_path.exists():
        raise ValueError(f"worker output already exists: {config.output_path}")
    if _sha256_file(config.request_path) != config.request_sha256:
        raise ValueError("worker request does not match its configured SHA-256")
    checkpoint_identity = _file_identity(config.checkpoint_path)
    if _sha256_file(config.checkpoint_path) != config.checkpoint_sha256:
        raise ValueError("checkpoint does not match its configured SHA-256")
    if (
        canonical_tree_sha256(config.base_model_artifact_path)
        != config.base_model_artifact_tree_sha256
    ):
        raise ValueError(
            "base-model artifact tree does not match its configured SHA-256"
        )

    worker_sha256 = _sha256_file(Path(__file__))
    proposal_sha256, notes = _load_request(config.request_path)
    active_encoder = OfficialSseEncoder(config)
    encoded = tuple(active_encoder.encode(notes))
    expected = _flatten_expected_rows(notes)
    actual = tuple((row.note_id, row.subject_id) for row in encoded)
    if actual != expected:
        raise ValueError(
            "encoder output note/subject order differs from the worker request"
        )

    raw = bytearray()
    receipt_rows = []
    for ordinal, row in enumerate(encoded):
        if len(row.vector) != config.model.dimensions:
            raise ValueError(
                f"encoder row {ordinal} has {len(row.vector)} dimensions, "
                f"expected {config.model.dimensions}"
            )
        rounded = []
        for value in row.vector:
            packed = struct.pack("<f", float(value))
            rounded_value = struct.unpack("<f", packed)[0]
            if not math.isfinite(rounded_value):
                raise ValueError(f"encoder row {ordinal} contains non-finite data")
            raw.extend(packed)
            rounded.append(rounded_value)
        if not any(value != 0.0 for value in rounded):
            raise ValueError(f"encoder row {ordinal} has a zero norm")
        indices = row.selected_token_indices
        token_ids = row.selected_token_ids
        if (
            not indices
            or tuple(sorted(set(indices))) != indices
            or any(index < 0 for index in indices)
            or len(token_ids) != len(indices)
            or any(
                not isinstance(token_id, int) or token_id < 0 for token_id in token_ids
            )
            or row.token_count < 1
            or any(index >= row.token_count for index in indices)
        ):
            raise ValueError(
                f"encoder row {ordinal} has invalid selected token indices"
            )
        receipt_rows.append(
            {
                "ordinal": ordinal,
                "note_id": row.note_id,
                "subject_id": row.subject_id,
                "selected_token_indices": list(indices),
                "selected_token_ids": list(token_ids),
                "token_count": row.token_count,
            }
        )

    stage = Path(
        tempfile.mkdtemp(
            prefix=f".{config.output_path.name}.",
            dir=config.output_path.parent,
        )
    )
    try:
        raw_path = stage / "raw-vectors.f32le"
        raw_path.write_bytes(raw)
        receipt = {
            "schema_version": SCHEMA_VERSION,
            "proposal_sha256": proposal_sha256,
            "request_sha256": config.request_sha256,
            "checkpoint_sha256": config.checkpoint_sha256,
            "base_model_artifact_tree_sha256": (config.base_model_artifact_tree_sha256),
            "tree_hash_rule": TREE_HASH_RULE,
            "model": config.model.to_json(),
            "runtime": _runtime_metadata(active_encoder, worker_sha256),
            "device": config.device,
            "container_image": config.container_image,
            "note_batch_size": config.note_batch_size,
            "vector_format": VECTOR_FORMAT,
            "dimensions": config.model.dimensions,
            "row_count": len(encoded),
            "rows": receipt_rows,
            "files": {
                "raw-vectors.f32le": {
                    "bytes": len(raw),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                }
            },
        }
        _write_json(stage / "worker-receipt.json", receipt)

        if _sha256_file(config.request_path) != config.request_sha256:
            raise ValueError("worker request changed during inference")
        if _file_identity(config.checkpoint_path) != checkpoint_identity:
            raise ValueError("checkpoint changed during inference")
        if (
            canonical_tree_sha256(config.base_model_artifact_path)
            != config.base_model_artifact_tree_sha256
        ):
            raise ValueError("base-model artifact tree changed during inference")
        if _sha256_file(Path(__file__)) != worker_sha256:
            raise ValueError("worker implementation changed during inference")
        os.rename(stage, config.output_path)
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise

    return WorkerReport(
        row_count=len(encoded),
        dimensions=config.model.dimensions,
        output_path=config.output_path,
    )


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run one pinned Sub-Sentence Encoder diagnostic job."
    )
    parser.add_argument("config", type=Path)
    args = parser.parse_args(list(argv) if argv is not None else None)
    report = run_worker(args.config)
    print(
        json.dumps(
            {
                "row_count": report.row_count,
                "dimensions": report.dimensions,
                "output_path": str(report.output_path),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
