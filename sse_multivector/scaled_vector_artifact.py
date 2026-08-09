#!/usr/bin/env python3
"""Build and verify the scaled communicated-meaning SSE vector artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import struct
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

try:
    from worker import POOLING_RULE, canonical_tree_sha256
except ImportError:
    from sse_multivector.worker import POOLING_RULE, canonical_tree_sha256


SCHEMA_VERSION = 1
EXPECTED_STAGES = {
    "takeaway": ("TPv3.82", "gpt-5.6-sol", "max"),
    "prominence": ("PPv2", "gpt-5.6-sol", "max"),
    "mask": ("MPv3.4", "gpt-5.6-sol", "max"),
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _write(path: Path, payload: bytes) -> None:
    with path.open("xb") as destination:
        destination.write(payload)
        destination.flush()
        os.fsync(destination.fileno())


def _write_json(path: Path, value: object) -> None:
    _write(path, _canonical_bytes(value))


def _load_json(path: Path, name: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"could not read {name} at {path}: {error}") from error


def _object(value: object, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return value


def _string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a nonempty string")
    return value


def _integer(value: object, name: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{name} must be an integer at least {minimum}")
    return value


def _sha(value: object, name: str) -> str:
    digest = _string(value, name)
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    return digest


def _resolve(value: object, name: str, parent: Path) -> Path:
    path = Path(_string(value, name)).expanduser()
    return (parent / path).resolve() if not path.is_absolute() else path.resolve()


@dataclass(frozen=True)
class ArtifactConfig:
    config_path: Path
    artifact_id: str
    note_count: int
    input_path: Path
    generation_run_directory: Path
    checkpoint_path: Path
    checkpoint_sha256: str
    worker_path: Path
    worker_sha256: str
    base_model_artifact_path: Path
    base_model_artifact_tree_sha256: str
    model: dict[str, object]
    container_image: str
    note_batch_size: int
    prepared_path: Path
    worker_output_path: Path
    vector_output_path: Path

    @classmethod
    def load(cls, path: Path | str) -> "ArtifactConfig":
        config_path = Path(path).resolve()
        value = _object(_load_json(config_path, "scaled vector config"), "config")
        expected = {
            "schema_version",
            "artifact_id",
            "note_count",
            "input_path",
            "generation_run_directory",
            "checkpoint_path",
            "checkpoint_sha256",
            "worker_path",
            "worker_sha256",
            "base_model_artifact_path",
            "base_model_artifact_tree_sha256",
            "model",
            "container_image",
            "note_batch_size",
            "prepared_path",
            "worker_output_path",
            "vector_output_path",
        }
        if set(value) != expected or value.get("schema_version") != SCHEMA_VERSION:
            raise ValueError("scaled vector config violates schema version 1")
        parent = config_path.parent
        model = _object(value["model"], "config.model")
        if set(model) != {"base_model", "dimensions", "maximum_tokens", "pooling"}:
            raise ValueError("config.model has invalid fields")
        _string(model["base_model"], "config.model.base_model")
        _integer(model["dimensions"], "config.model.dimensions", minimum=1)
        _integer(model["maximum_tokens"], "config.model.maximum_tokens", minimum=1)
        if model["pooling"] != POOLING_RULE:
            raise ValueError("config.model uses an unsupported pooling rule")
        return cls(
            config_path=config_path,
            artifact_id=_string(value["artifact_id"], "config.artifact_id"),
            note_count=_integer(value["note_count"], "config.note_count", minimum=1),
            input_path=_resolve(value["input_path"], "config.input_path", parent),
            generation_run_directory=_resolve(
                value["generation_run_directory"],
                "config.generation_run_directory",
                parent,
            ),
            checkpoint_path=_resolve(
                value["checkpoint_path"], "config.checkpoint_path", parent
            ),
            checkpoint_sha256=_sha(
                value["checkpoint_sha256"], "config.checkpoint_sha256"
            ),
            worker_path=_resolve(value["worker_path"], "config.worker_path", parent),
            worker_sha256=_sha(value["worker_sha256"], "config.worker_sha256"),
            base_model_artifact_path=_resolve(
                value["base_model_artifact_path"],
                "config.base_model_artifact_path",
                parent,
            ),
            base_model_artifact_tree_sha256=_sha(
                value["base_model_artifact_tree_sha256"],
                "config.base_model_artifact_tree_sha256",
            ),
            model=model,
            container_image=_string(
                value["container_image"], "config.container_image"
            ),
            note_batch_size=_integer(
                value["note_batch_size"], "config.note_batch_size", minimum=1
            ),
            prepared_path=_resolve(
                value["prepared_path"], "config.prepared_path", parent
            ),
            worker_output_path=_resolve(
                value["worker_output_path"], "config.worker_output_path", parent
            ),
            vector_output_path=_resolve(
                value["vector_output_path"], "config.vector_output_path", parent
            ),
        )


@dataclass(frozen=True)
class PreparedReport:
    note_count: int
    vector_count: int
    output_path: Path


@dataclass(frozen=True)
class VectorArtifactReport:
    note_count: int
    vector_count: int
    dimensions: int
    output_path: Path


def _publish_directory(path: Path, files: dict[str, bytes]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{path.name}.", dir=path.parent))
    try:
        for name, payload in files.items():
            _write(stage / name, payload)
        os.rename(stage, path)
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise


def _load_notes(config: ArtifactConfig) -> list[dict[str, str]]:
    value = _object(_load_json(config.input_path, "generation input"), "input")
    if set(value) != {"schema_version", "notes"} or value["schema_version"] != 1:
        raise ValueError("generation input violates schema version 1")
    raw_notes = value["notes"]
    if not isinstance(raw_notes, list) or len(raw_notes) != config.note_count:
        raise ValueError(f"generation input must contain exactly {config.note_count} notes")
    notes: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, raw in enumerate(raw_notes):
        note = _object(raw, f"input.notes[{index}]")
        if set(note) != {"note_id", "text"}:
            raise ValueError(f"input note {index} has invalid fields")
        note_id = _string(note["note_id"], f"input.notes[{index}].note_id")
        if len(note_id) != 64 or any(character not in "0123456789abcdef" for character in note_id):
            raise ValueError(f"input note {index} has an invalid note ID")
        if note_id in seen:
            raise ValueError(f"generation input repeats note ID {note_id}")
        seen.add(note_id)
        notes.append({"note_id": note_id, "text": _string(note["text"], f"input.notes[{index}].text")})
    return notes


def _validate_generation_manifest(config: ArtifactConfig) -> tuple[dict[str, Any], str]:
    path = config.generation_run_directory / "manifest.json"
    manifest = _object(_load_json(path, "generation manifest"), "generation manifest")
    if manifest.get("schema_version") != 2 or manifest.get("input_sha256") != _sha256(config.input_path):
        raise ValueError("generation manifest is not bound to the configured input")
    for stage_name, expected in EXPECTED_STAGES.items():
        stage = _object(manifest.get(stage_name), f"generation manifest.{stage_name}")
        actual = (stage.get("prompt_version"), stage.get("model"), stage.get("reasoning_effort"))
        if actual != expected:
            raise ValueError(f"generation manifest has the wrong {stage_name} contract")
    return manifest, _sha256(path)


@dataclass(frozen=True)
class GenerationLedger:
    latest: dict[str, dict[str, Any]]
    superseded_jobs: frozenset[str]


def _runner_boundaries(
    run_directory: Path,
    manifest: dict[str, Any],
    manifest_sha256: str,
    result_bytes: bytes,
) -> tuple[str, list[tuple[int, str]]]:
    initial_wrapper = _sha(
        manifest.get("wrapper_sha256"), "generation manifest.wrapper_sha256"
    )
    path = run_directory / "runner-upgrades.jsonl"
    if not path.exists():
        return initial_wrapper, []
    boundaries: list[tuple[int, str]] = []
    current_wrapper = initial_wrapper
    previous_first_line = 0
    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, 1):
            try:
                record = _object(
                    json.loads(line), f"runner upgrade line {line_number}"
                )
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"runner upgrade line {line_number} is invalid JSON"
                ) from error
            expected_fields = {
                "schema_version",
                "manifest_sha256",
                "from_wrapper_sha256",
                "to_wrapper_sha256",
                "first_result_line",
                "results_prefix_bytes",
                "results_prefix_sha256",
                "reason",
            }
            if set(record) != expected_fields or record["schema_version"] != 2:
                raise ValueError(f"runner upgrade line {line_number} has invalid fields")
            if record["manifest_sha256"] != manifest_sha256:
                raise ValueError(
                    f"runner upgrade line {line_number} belongs to another manifest"
                )
            from_wrapper = _sha(
                record["from_wrapper_sha256"],
                f"runner upgrade line {line_number}.from_wrapper_sha256",
            )
            to_wrapper = _sha(
                record["to_wrapper_sha256"],
                f"runner upgrade line {line_number}.to_wrapper_sha256",
            )
            if from_wrapper != current_wrapper or to_wrapper == from_wrapper:
                raise ValueError(
                    f"runner upgrade line {line_number} does not continue its chain"
                )
            first_line = _integer(
                record["first_result_line"],
                f"runner upgrade line {line_number}.first_result_line",
                minimum=1,
            )
            if (
                first_line < previous_first_line
                or first_line > len(result_bytes.splitlines()) + 1
            ):
                raise ValueError(
                    f"runner upgrade line {line_number} has invalid first_result_line"
                )
            prefix_bytes = _integer(
                record["results_prefix_bytes"],
                f"runner upgrade line {line_number}.results_prefix_bytes",
            )
            if prefix_bytes > len(result_bytes):
                raise ValueError(
                    f"runner upgrade line {line_number} has invalid results_prefix_bytes"
                )
            prefix = result_bytes[:prefix_bytes]
            if (
                _sha(
                    record["results_prefix_sha256"],
                    f"runner upgrade line {line_number}.results_prefix_sha256",
                )
                != hashlib.sha256(prefix).hexdigest()
                or len(prefix.splitlines()) != first_line - 1
                or (prefix and not prefix.endswith(b"\n"))
            ):
                raise ValueError(
                    f"runner upgrade line {line_number} does not match its results prefix"
                )
            _string(record["reason"], f"runner upgrade line {line_number}.reason")
            boundaries.append((first_line, to_wrapper))
            current_wrapper = to_wrapper
            previous_first_line = first_line
    return initial_wrapper, boundaries


def _load_latest_results(
    path: Path,
    manifest_sha256: str,
    initial_wrapper: str,
    runner_boundaries: list[tuple[int, str]],
) -> GenerationLedger:
    latest: dict[str, dict[str, Any]] = {}
    history: dict[str, list[tuple[int, dict[str, Any]]]] = {}
    active_wrapper = initial_wrapper
    boundary_index = 0
    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, 1):
            while (
                boundary_index < len(runner_boundaries)
                and runner_boundaries[boundary_index][0] <= line_number
            ):
                active_wrapper = runner_boundaries[boundary_index][1]
                boundary_index += 1
            try:
                record = _object(json.loads(line), f"generation result line {line_number}")
            except json.JSONDecodeError as error:
                raise ValueError(f"generation result line {line_number} is invalid JSON") from error
            if record.get("manifest_sha256") != manifest_sha256:
                raise ValueError(f"generation result line {line_number} belongs to another manifest")
            recorded_wrapper = record.get("wrapper_sha256")
            if recorded_wrapper is None:
                if active_wrapper != initial_wrapper:
                    raise ValueError(
                        f"generation result line {line_number} has invalid wrapper provenance"
                    )
            elif _sha(
                recorded_wrapper,
                f"generation result line {line_number}.wrapper_sha256",
            ) != active_wrapper:
                raise ValueError(
                    f"generation result line {line_number} has invalid wrapper provenance"
                )
            job_key = _string(record.get("job_key"), f"generation result line {line_number}.job_key")
            attempt = _integer(record.get("attempt"), f"generation result {job_key}.attempt", minimum=1)
            previous = latest.get(job_key)
            if previous is not None and attempt != previous["attempt"] + 1:
                raise ValueError(f"generation result {job_key} has nonconsecutive attempts")
            usage = _object(record.get("usage"), f"generation result {job_key}.usage")
            if not usage or any(isinstance(item, bool) or not isinstance(item, int) or item < 0 for item in usage.values()):
                raise ValueError(f"generation result {job_key} has invalid token usage")
            latest[job_key] = record
            history.setdefault(job_key, []).append((line_number, record))

    superseded_jobs: set[str] = set()
    for job_key, attempts in history.items():
        current_line, current = attempts[-1]
        if (
            current.get("stage") != "takeaway"
            or current.get("status") != "succeeded"
            or not isinstance(current.get("response"), list)
        ):
            continue
        note_id = current.get("note_id")
        if not isinstance(note_id, str) or job_key != f"takeaway:{note_id}":
            continue
        current_count = len(current["response"])
        prior_counts = [
            len(record["response"])
            for _, record in attempts[:-1]
            if record.get("status") == "succeeded"
            and isinstance(record.get("response"), list)
        ]
        if not prior_counts:
            continue
        for index in range(current_count, max(prior_counts)):
            for stage in ("prominence", "mask"):
                child_key = f"{stage}:{note_id}:{index}"
                child_attempts = history.get(child_key)
                if child_attempts and child_attempts[-1][0] < current_line:
                    superseded_jobs.add(child_key)
    return GenerationLedger(latest=latest, superseded_jobs=frozenset(superseded_jobs))


def _byte_spans(text: str, fragments: object, name: str) -> tuple[list[str], list[list[int]]]:
    if not isinstance(fragments, list) or not fragments:
        raise ValueError(f"{name} must contain at least one source fragment")
    result: list[str] = []
    spans: list[list[int]] = []
    cursor = 0
    for index, raw_fragment in enumerate(fragments):
        fragment = _string(raw_fragment, f"{name}[{index}]")
        start = text.find(fragment, cursor)
        if start < 0:
            raise ValueError(f"{name}[{index}] is absent or out of source order")
        end = start + len(fragment)
        spans.append([len(text[:start].encode("utf-8")), len(text[:end].encode("utf-8"))])
        result.append(fragment)
        cursor = end
    return result, spans


def _subject_id(note_id: str, index: int, takeaway: str) -> str:
    return hashlib.sha256(f"{note_id}\0{index}\0{takeaway}".encode("utf-8")).hexdigest()[:16]


def _prepared_values(config: ArtifactConfig) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    notes = _load_notes(config)
    manifest, manifest_sha256 = _validate_generation_manifest(config)
    output_path = config.generation_run_directory / "output.json"
    output = _object(_load_json(output_path, "generation output"), "generation output")
    if set(output) != {"schema_version", "manifest_sha256", "notes"} or output.get("schema_version") != 2 or output.get("manifest_sha256") != manifest_sha256:
        raise ValueError("generation output is not bound to its manifest")
    raw_generated = output["notes"]
    if not isinstance(raw_generated, list) or [item.get("note_id") if isinstance(item, dict) else None for item in raw_generated] != [note["note_id"] for note in notes]:
        raise ValueError("generation output does not contain every input note in order")
    results_path = config.generation_run_directory / "results.jsonl"
    result_bytes = results_path.read_bytes()
    initial_wrapper, runner_boundaries = _runner_boundaries(
        config.generation_run_directory,
        manifest,
        manifest_sha256,
        result_bytes,
    )
    ledger = _load_latest_results(
        results_path,
        manifest_sha256,
        initial_wrapper,
        runner_boundaries,
    )
    latest = ledger.latest
    expected_jobs: set[str] = set()
    request_notes = []
    vectors = []
    seen_subject_ids: set[str] = set()
    for note, raw_generated_note in zip(notes, raw_generated, strict=True):
        generated_note = _object(raw_generated_note, f"generated note {note['note_id']}")
        if set(generated_note) != {"note_id", "takeaways"}:
            raise ValueError(f"generated note {note['note_id']} has invalid fields")
        raw_takeaways = generated_note["takeaways"]
        if not isinstance(raw_takeaways, list):
            raise ValueError(f"generated note {note['note_id']} has invalid takeaways")
        takeaway_key = f"takeaway:{note['note_id']}"
        expected_jobs.add(takeaway_key)
        takeaway_record = latest.get(takeaway_key)
        texts = [item.get("text") if isinstance(item, dict) else None for item in raw_takeaways]
        if takeaway_record is None or takeaway_record.get("status") != "succeeded" or takeaway_record.get("stage") != "takeaway" or takeaway_record.get("response") != texts:
            raise ValueError(f"generation ledger does not support {takeaway_key}")
        subjects = []
        for index, raw_takeaway in enumerate(raw_takeaways):
            takeaway = _object(raw_takeaway, f"takeaway {note['note_id']}:{index}")
            if set(takeaway) != {"text", "fragments", "prominence"}:
                raise ValueError(f"takeaway {note['note_id']}:{index} has invalid fields")
            text = _string(takeaway["text"], f"takeaway {note['note_id']}:{index}.text")
            prominence = _integer(takeaway["prominence"], f"takeaway {note['note_id']}:{index}.prominence")
            if prominence > 100:
                raise ValueError(f"takeaway {note['note_id']}:{index} prominence exceeds 100")
            fragments, spans = _byte_spans(note["text"], takeaway["fragments"], f"takeaway {note['note_id']}:{index}.fragments")
            for stage, response in (("prominence", prominence), ("mask", fragments)):
                job_key = f"{stage}:{note['note_id']}:{index}"
                expected_jobs.add(job_key)
                record = latest.get(job_key)
                if record is None or record.get("status") != "succeeded" or record.get("stage") != stage or record.get("response") != response:
                    raise ValueError(f"generation ledger does not support {job_key}")
            subject_id = _subject_id(note["note_id"], index, text)
            if subject_id in seen_subject_ids:
                raise ValueError(f"derived duplicate subject ID {subject_id}")
            seen_subject_ids.add(subject_id)
            ordinal = len(vectors)
            subjects.append({"subject_id": subject_id, "byte_spans": spans})
            vectors.append(
                {
                    "ordinal": ordinal,
                    "subject_id": subject_id,
                    "note_id": note["note_id"],
                    "takeaway_index": index,
                    "takeaway": text,
                    "prominence": prominence,
                    "fragments": fragments,
                    "byte_spans": spans,
                }
            )
        if subjects:
            request_notes.append({"note_id": note["note_id"], "text": note["text"], "subjects": subjects})
    extras = set(latest) - expected_jobs
    missing = expected_jobs - set(latest)
    invalid_extras = extras - ledger.superseded_jobs
    if missing or invalid_extras:
        raise ValueError(
            "generation ledger job set differs; "
            f"extra={sorted(invalid_extras)[:1]} missing={sorted(missing)[:1]}"
        )
    if not vectors:
        raise ValueError("generation produced no masks to encode")
    generation_sha256 = _sha256(output_path)
    request = {"schema_version": 1, "proposal_sha256": generation_sha256, "notes": request_notes}
    vector_map = {
        "schema_version": SCHEMA_VERSION,
        "artifact_id": config.artifact_id,
        "note_count": len(notes),
        "vector_count": len(vectors),
        "generation_output_sha256": generation_sha256,
        "vectors": vectors,
    }
    request_sha256 = hashlib.sha256(_canonical_bytes(request)).hexdigest()
    worker_config = {
        "schema_version": 1,
        "request_path": "/input/worker-input.json",
        "request_sha256": request_sha256,
        "checkpoint_path": "/checkpoint/subencoder_st5_base.ckpt",
        "checkpoint_sha256": config.checkpoint_sha256,
        "base_model_artifact_path": "/model",
        "base_model_artifact_tree_sha256": config.base_model_artifact_tree_sha256,
        "model": config.model,
        "device": "cpu",
        "container_image": config.container_image,
        "note_batch_size": config.note_batch_size,
        "output_path": str(Path("/output") / config.worker_output_path.name),
    }
    return request, vector_map, worker_config


def _verify_model_sources(config: ArtifactConfig) -> None:
    if _sha256(config.checkpoint_path) != config.checkpoint_sha256:
        raise ValueError("configured SSE checkpoint hash differs")
    if _sha256(config.worker_path) != config.worker_sha256:
        raise ValueError("configured SSE worker hash differs")
    if canonical_tree_sha256(config.base_model_artifact_path) != config.base_model_artifact_tree_sha256:
        raise ValueError("configured SSE base-model tree hash differs")


def prepare_vector_artifact(config_path: Path | str) -> PreparedReport:
    config = ArtifactConfig.load(config_path)
    _verify_model_sources(config)
    request, vector_map, worker_config = _prepared_values(config)
    payloads = {
        "worker-input.json": _canonical_bytes(request),
        "vector-map.json": _canonical_bytes(vector_map),
        "worker-config.json": _canonical_bytes(worker_config),
    }
    runner_upgrades_path = (
        config.generation_run_directory / "runner-upgrades.jsonl"
    )
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "artifact_id": config.artifact_id,
        "config_sha256": _sha256(config.config_path),
        "input_sha256": _sha256(config.input_path),
        "generation_manifest_sha256": _sha256(config.generation_run_directory / "manifest.json"),
        "generation_results_sha256": _sha256(config.generation_run_directory / "results.jsonl"),
        "generation_runner_upgrades_sha256": (
            _sha256(runner_upgrades_path) if runner_upgrades_path.exists() else None
        ),
        "generation_output_sha256": _sha256(config.generation_run_directory / "output.json"),
        "note_count": vector_map["note_count"],
        "vector_count": vector_map["vector_count"],
        "files": {name: {"bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()} for name, payload in payloads.items()},
    }
    payloads["manifest.json"] = _canonical_bytes(manifest)
    if config.prepared_path.exists():
        expected_names = set(payloads)
        if not config.prepared_path.is_dir() or {item.name for item in config.prepared_path.iterdir()} != expected_names or any((config.prepared_path / name).read_bytes() != payload for name, payload in payloads.items()):
            raise ValueError("existing prepared vector artifact differs from its sources")
    else:
        _publish_directory(config.prepared_path, payloads)
    return PreparedReport(config.note_count, int(vector_map["vector_count"]), config.prepared_path)


def _load_prepared(config: ArtifactConfig) -> tuple[dict[str, Any], dict[str, Any]]:
    prepare_vector_artifact(config.config_path)
    request = _object(_load_json(config.prepared_path / "worker-input.json", "worker input"), "worker input")
    mapping = _object(_load_json(config.prepared_path / "vector-map.json", "vector map"), "vector map")
    return request, mapping


def _validate_worker_output(config: ArtifactConfig, request: dict[str, Any], mapping: dict[str, Any]) -> tuple[dict[str, Any], bytes]:
    receipt_path = config.worker_output_path / "worker-receipt.json"
    raw_path = config.worker_output_path / "raw-vectors.f32le"
    receipt = _object(_load_json(receipt_path, "worker receipt"), "worker receipt")
    vector_count = _integer(mapping.get("vector_count"), "vector map.vector_count", minimum=1)
    dimensions = _integer(config.model["dimensions"], "config.model.dimensions", minimum=1)
    runtime = _object(receipt.get("runtime"), "worker receipt.runtime")
    if receipt.get("schema_version") != 1 or receipt.get("proposal_sha256") != request.get("proposal_sha256") or receipt.get("request_sha256") != _sha256(config.prepared_path / "worker-input.json") or receipt.get("checkpoint_sha256") != config.checkpoint_sha256 or receipt.get("base_model_artifact_tree_sha256") != config.base_model_artifact_tree_sha256 or runtime.get("worker_sha256") != config.worker_sha256 or receipt.get("model") != config.model or receipt.get("dimensions") != dimensions or receipt.get("row_count") != vector_count:
        raise ValueError("worker receipt differs from the prepared SSE request")
    raw = raw_path.read_bytes()
    expected_bytes = vector_count * dimensions * 4
    file_entry = _object(_object(receipt.get("files"), "worker receipt.files").get("raw-vectors.f32le"), "worker receipt raw vector file")
    if len(raw) != expected_bytes or file_entry.get("bytes") != expected_bytes or file_entry.get("sha256") != hashlib.sha256(raw).hexdigest():
        raise ValueError("worker raw-vector bytes differ from its receipt")
    rows = receipt.get("rows")
    vectors = mapping.get("vectors")
    if not isinstance(rows, list) or not isinstance(vectors, list) or len(rows) != vector_count:
        raise ValueError("worker receipt rows are invalid")
    for expected, row in zip(vectors, rows, strict=True):
        row = _object(row, "worker receipt row")
        if (row.get("ordinal"), row.get("note_id"), row.get("subject_id")) != (expected.get("ordinal"), expected.get("note_id"), expected.get("subject_id")):
            raise ValueError("worker receipt row order differs from the vector map")
    return receipt, raw


def _normalize(raw: bytes, rows: int, dimensions: int) -> bytes:
    normalized = bytearray()
    row_format = struct.Struct(f"<{dimensions}f")
    for ordinal in range(rows):
        values = row_format.unpack_from(raw, ordinal * row_format.size)
        if any(not math.isfinite(value) for value in values):
            raise ValueError(f"SSE vector {ordinal} contains non-finite data")
        norm = math.sqrt(sum(value * value for value in values))
        if not math.isfinite(norm) or norm == 0.0:
            raise ValueError(f"SSE vector {ordinal} has no finite direction")
        normalized.extend(row_format.pack(*(value / norm for value in values)))
    return bytes(normalized)


def finalize_vector_artifact(config_path: Path | str) -> VectorArtifactReport:
    config = ArtifactConfig.load(config_path)
    _verify_model_sources(config)
    request, mapping = _load_prepared(config)
    receipt, raw = _validate_worker_output(config, request, mapping)
    vector_count = int(mapping["vector_count"])
    dimensions = int(config.model["dimensions"])
    normalized = _normalize(raw, vector_count, dimensions)
    payloads = {
        "vector-map.json": (config.prepared_path / "vector-map.json").read_bytes(),
        "worker-receipt.json": (config.worker_output_path / "worker-receipt.json").read_bytes(),
        "raw-vectors.f32le": raw,
        "normalized-vectors.f32le": normalized,
    }
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "artifact_id": config.artifact_id,
        "config_sha256": _sha256(config.config_path),
        "prepared_manifest_sha256": _sha256(config.prepared_path / "manifest.json"),
        "generation_output_sha256": mapping["generation_output_sha256"],
        "checkpoint_sha256": receipt["checkpoint_sha256"],
        "worker_sha256": config.worker_sha256,
        "base_model_artifact_tree_sha256": receipt["base_model_artifact_tree_sha256"],
        "note_count": mapping["note_count"],
        "vector_count": vector_count,
        "dimensions": dimensions,
        "normalization": "per-row-l2-f32le-v1",
        "files": {name: {"bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()} for name, payload in payloads.items()},
    }
    payloads["manifest.json"] = _canonical_bytes(manifest)
    if config.vector_output_path.exists():
        expected_names = set(payloads)
        if not config.vector_output_path.is_dir() or {item.name for item in config.vector_output_path.iterdir()} != expected_names or any((config.vector_output_path / name).read_bytes() != payload for name, payload in payloads.items()):
            raise ValueError("existing vector artifact differs from the verified worker output")
    else:
        _publish_directory(config.vector_output_path, payloads)
    return verify_vector_artifact(config.config_path)


def verify_vector_artifact(config_path: Path | str) -> VectorArtifactReport:
    config = ArtifactConfig.load(config_path)
    _verify_model_sources(config)
    request, mapping = _load_prepared(config)
    _, raw = _validate_worker_output(config, request, mapping)
    path = config.vector_output_path
    expected_names = {"manifest.json", "vector-map.json", "worker-receipt.json", "raw-vectors.f32le", "normalized-vectors.f32le"}
    if not path.is_dir() or {item.name for item in path.iterdir()} != expected_names:
        raise ValueError("vector artifact has unexpected entries")
    manifest = _object(_load_json(path / "manifest.json", "vector manifest"), "vector manifest")
    files = _object(manifest.get("files"), "vector manifest.files")
    for name in expected_names - {"manifest.json"}:
        entry = _object(files.get(name), f"vector manifest.files.{name}")
        file_path = path / name
        if entry.get("bytes") != file_path.stat().st_size or entry.get("sha256") != _sha256(file_path):
            raise ValueError(f"vector artifact file {name} differs from its manifest")
    if (path / "raw-vectors.f32le").read_bytes() != raw or (path / "vector-map.json").read_bytes() != (config.prepared_path / "vector-map.json").read_bytes():
        raise ValueError("vector artifact differs from its bound inputs")
    rows = _integer(manifest.get("vector_count"), "vector manifest.vector_count", minimum=1)
    dimensions = _integer(manifest.get("dimensions"), "vector manifest.dimensions", minimum=1)
    normalized = (path / "normalized-vectors.f32le").read_bytes()
    if normalized != _normalize(raw, rows, dimensions):
        raise ValueError("normalized vectors are not the canonical normalization")
    return VectorArtifactReport(
        note_count=_integer(manifest.get("note_count"), "vector manifest.note_count", minimum=1),
        vector_count=rows,
        dimensions=dimensions,
        output_path=path,
    )


def main(arguments: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "finalize", "verify"))
    parser.add_argument("config", type=Path)
    parsed = parser.parse_args(arguments)
    try:
        if parsed.command == "prepare":
            report = prepare_vector_artifact(parsed.config)
        elif parsed.command == "finalize":
            report = finalize_vector_artifact(parsed.config)
        else:
            report = verify_vector_artifact(parsed.config)
        print(json.dumps(report.__dict__, default=str, sort_keys=True))
        return 0
    except (OSError, ValueError) as error:
        print(f"scaled SSE vector artifact failed: {error}", file=os.sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
