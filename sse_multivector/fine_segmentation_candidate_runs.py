#!/usr/bin/env python3
"""Execute and replay-verify frozen fine-segmentation candidate runs."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import math
import os
import platform
import resource
import shutil
import struct
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = 1
RUN_ORDER_VERSION = "hmac-sha256-blinding-seed-candidate-input-repeat-v1"
RUN_ID_VERSION = "sha256-candidate-input-repeat-v1"
REQUIRED_CANDIDATES = ("hdbscan", "snn")


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


def _compact_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _canonical_compact_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _write(path: Path, value: bytes) -> None:
    with path.open("xb") as destination:
        destination.write(value)
        destination.flush()
        os.fsync(destination.fileno())


def _write_json(path: Path, value: object) -> None:
    _write(path, _canonical_bytes(value))


def _cpu_model() -> str:
    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.exists():
        for line in cpuinfo.read_text(encoding="utf-8").splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    return "unknown"


def _actual_host() -> dict[str, object]:
    uname = platform.uname()
    cpu_features: list[str] = []
    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.exists():
        for line in cpuinfo.read_text(encoding="utf-8", errors="replace").splitlines():
            key, separator, value = line.partition(":")
            if separator and key.strip().lower() in {"flags", "features"}:
                cpu_features = sorted(value.split())
                break
    return {
        "system": uname.system,
        "release": uname.release,
        "machine": uname.machine,
        "cpu_model": _cpu_model(),
        "cpu_features": cpu_features,
    }


def _actual_resource_limits() -> dict[str, list[int]]:
    names = {
        "address_space_bytes": resource.RLIMIT_AS,
        "cpu_seconds": resource.RLIMIT_CPU,
        "file_size_bytes": resource.RLIMIT_FSIZE,
        "open_files": resource.RLIMIT_NOFILE,
        "processes": resource.RLIMIT_NPROC,
        "stack_bytes": resource.RLIMIT_STACK,
    }
    return {name: list(resource.getrlimit(limit)) for name, limit in names.items()}


def _require_sha256(name: str, value: object) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{name} is not a lowercase SHA-256")
    return value


def _require_exact_keys(name: str, value: object, keys: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{name} does not contain the frozen fields")
    return value


def _load_bound_inputs(
    prepared: Path,
    vectors: Path,
    freeze_path: Path,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, list[float]],
]:
    protocol_path = prepared / "protocol.json"
    prepared_manifest_path = prepared / "manifest.json"
    vector_manifest_path = vectors / "manifest.json"
    vector_map_path = vectors / "vector-map.json"
    normalized_path = vectors / "normalized-vectors.f64le"
    for path in (
        protocol_path,
        prepared_manifest_path,
        vector_manifest_path,
        vector_map_path,
        normalized_path,
        freeze_path,
    ):
        if not path.is_file():
            raise ValueError(f"required frozen input is missing: {path}")

    protocol = _read_json(protocol_path)
    prepared_manifest = _read_json(prepared_manifest_path)
    vector_manifest = _read_json(vector_manifest_path)
    vector_map = _read_json(vector_map_path)
    freeze = _read_json(freeze_path)
    suite_id = freeze.get("suite_id")
    if (
        freeze.get("schema_version") != SCHEMA_VERSION
        or not isinstance(suite_id, str)
        or protocol.get("suite_id") != suite_id
        or prepared_manifest.get("suite_id") != suite_id
        or vector_manifest.get("suite_id") != suite_id
        or vector_map.get("suite_id") != suite_id
    ):
        raise ValueError("suite identities do not agree")
    if freeze.get("prepared_manifest_sha256") != _sha256_file(prepared_manifest_path):
        raise ValueError("prepared manifest differs from the technical freeze")
    if freeze.get("protocol_sha256") != _sha256_file(protocol_path):
        raise ValueError("protocol differs from the technical freeze")
    if prepared_manifest.get("protocol_sha256") != _sha256_file(protocol_path):
        raise ValueError("prepared manifest does not bind the protocol")

    protocol_inputs = protocol.get("inputs")
    protocol_encodings = protocol.get("encodings")
    if not isinstance(protocol_inputs, list) or not isinstance(
        protocol_encodings, list
    ):
        raise ValueError("protocol does not contain encodings and logical inputs")
    logical_count = len(protocol_inputs)
    encoding_count = len(protocol_encodings)
    if (
        freeze.get("logical_input_count") != logical_count
        or freeze.get("encoding_count") != encoding_count
        or prepared_manifest.get("logical_input_count") != logical_count
    ):
        raise ValueError("frozen suite cardinalities do not match the protocol")

    execution = _validate_execution_freeze(freeze, freeze_path)
    repetitions = execution["repetitions_per_input"]
    expected_per_candidate = logical_count * repetitions
    if (
        freeze.get("invocations_per_candidate") != expected_per_candidate
        or prepared_manifest.get("fresh_invocations_per_candidate")
        != expected_per_candidate
    ):
        raise ValueError("frozen invocation count does not match the protocol")
    candidates = freeze.get("candidates")
    if (
        not isinstance(candidates, dict)
        or tuple(sorted(candidates)) != REQUIRED_CANDIDATES
    ):
        raise ValueError("technical freeze must contain exactly HDBSCAN and SNN")

    sources = vector_manifest.get("sources", {})
    if sources.get("prepared_manifest_sha256") != _sha256_file(prepared_manifest_path):
        raise ValueError("vector artifact is not bound to the prepared suite")
    if sources.get("technical_freeze_sha256") != _sha256_file(freeze_path):
        raise ValueError("vector artifact is not bound to the technical freeze")
    files = vector_manifest.get("files", {})
    normalized_identity = files.get("normalized-vectors.f64le")
    vector_map_identity = files.get("vector-map.json")
    if not isinstance(normalized_identity, dict) or not isinstance(
        vector_map_identity, dict
    ):
        raise ValueError("vector artifact manifest is incomplete")
    normalized = normalized_path.read_bytes()
    if normalized_identity != {
        "bytes": len(normalized),
        "sha256": _sha256_bytes(normalized),
    }:
        raise ValueError("normalized vector file differs from its manifest")
    if vector_map_identity != {
        "bytes": vector_map_path.stat().st_size,
        "sha256": _sha256_file(vector_map_path),
    }:
        raise ValueError("vector map differs from its manifest")

    dimensions = vector_manifest.get("dimensions")
    mapped_vectors = vector_map.get("vectors")
    if (
        not isinstance(dimensions, int)
        or dimensions <= 0
        or freeze.get("encoder", {}).get("dimensions") != dimensions
        or vector_manifest.get("vector_count") != encoding_count
        or vector_map.get("vector_count") != encoding_count
        or vector_map.get("dimensions") != dimensions
        or not isinstance(mapped_vectors, list)
        or len(mapped_vectors) != encoding_count
        or len(normalized) != encoding_count * dimensions * 8
    ):
        raise ValueError("vector artifact shape differs from the frozen protocol")

    encoding_ids = [item.get("encoding_id") for item in protocol_encodings]
    if any(not isinstance(item, str) for item in encoding_ids) or len(
        set(encoding_ids)
    ) != len(encoding_ids):
        raise ValueError("protocol encoding IDs are invalid")
    vector_by_encoding: dict[str, list[float]] = {}
    for ordinal, (encoding_id, mapped) in enumerate(
        zip(encoding_ids, mapped_vectors, strict=True)
    ):
        if mapped.get("ordinal") != ordinal or mapped.get("encoding_id") != encoding_id:
            raise ValueError(
                "vector map order differs from the protocol encoding order"
            )
        values = list(
            struct.unpack_from(f"<{dimensions}d", normalized, ordinal * dimensions * 8)
        )
        if not all(math.isfinite(value) for value in values):
            raise ValueError(
                f"normalized vector {ordinal} contains a non-finite coordinate"
            )
        norm = math.sqrt(sum(value * value for value in values))
        if not math.isclose(norm, 1.0, rel_tol=0.0, abs_tol=1e-12):
            raise ValueError(f"normalized vector {ordinal} does not have unit length")
        vector_by_encoding[encoding_id] = values

    seen_input_ids: set[str] = set()
    for logical_input in protocol_inputs:
        input_id = logical_input.get("input_id")
        opaque_ids = logical_input.get("opaque_ids")
        selected_encodings = logical_input.get("encoding_ids")
        if (
            not isinstance(input_id, str)
            or input_id in seen_input_ids
            or not isinstance(opaque_ids, list)
            or not isinstance(selected_encodings, list)
            or len(opaque_ids) != len(selected_encodings)
            or not opaque_ids
        ):
            raise ValueError("protocol contains an invalid logical input")
        seen_input_ids.add(input_id)
        if len(set(opaque_ids)) != len(opaque_ids):
            raise ValueError(f"logical input {input_id} repeats an opaque ID")
        for opaque_id, encoding_id in zip(opaque_ids, selected_encodings, strict=True):
            _require_sha256("opaque ID", opaque_id)
            if encoding_id not in vector_by_encoding:
                raise ValueError(f"logical input {input_id} names an unknown encoding")

    return freeze, protocol, vector_manifest, vector_by_encoding


def _validate_execution_freeze(
    freeze: dict[str, Any], freeze_path: Path
) -> dict[str, Any]:
    execution = _require_exact_keys(
        "candidate execution profile",
        freeze.get("candidate_execution"),
        {
            "executable_path",
            "executable_sha256",
            "working_directory",
            "argv_template",
            "environment",
            "fresh_process_per_invocation",
            "repetitions_per_input",
            "random_seed",
            "numeric_type",
            "normalized_vector_contract",
            "launcher",
            "device",
            "accelerator",
            "numerical_backend",
            "determinism",
            "thread_count",
            "process_count",
            "isolation",
            "resource_limits",
            "host",
        },
    )
    executable = Path(execution["executable_path"])
    working_directory = Path(execution["working_directory"])
    if (
        not executable.is_absolute()
        or executable.resolve() != executable
        or not executable.is_file()
        or not os.access(executable, os.X_OK)
        or _sha256_file(executable)
        != _require_sha256(
            "candidate executable SHA-256", execution["executable_sha256"]
        )
    ):
        raise ValueError("candidate executable differs from the technical freeze")
    if (
        not working_directory.is_absolute()
        or working_directory.resolve() != working_directory
        or not working_directory.is_dir()
    ):
        raise ValueError(
            "candidate working directory differs from the technical freeze"
        )
    required_profile = {
        "argv_template": ["{executable}", "{request_path}"],
        "environment": {},
        "fresh_process_per_invocation": True,
        "repetitions_per_input": 2,
        "random_seed": None,
        "numeric_type": "f64",
        "normalized_vector_contract": "row-major-f64le-v1",
        "launcher": "direct-executable-v1",
        "device": "cpu",
        "accelerator": None,
        "numerical_backend": "rust-standard-library-f64-v1",
        "determinism": "no-randomness-canonical-input-and-ties-v1",
        "thread_count": 1,
        "process_count": 1,
        "isolation": "fresh-process-empty-environment-no-shared-mutable-state-v1",
        "resource_limits": _actual_resource_limits(),
        "host": _actual_host(),
    }
    for field, expected in required_profile.items():
        if execution.get(field) != expected:
            raise ValueError(f"candidate execution field {field} differs from this run")
    return execution


def _schedule(
    freeze: dict[str, Any], protocol: dict[str, Any], private: dict[str, Any]
) -> list[dict[str, Any]]:
    seed_hex = private.get("seed_hex")
    if seed_hex is None:
        # The production suite has independent namespace seeds. Their complete,
        # frozen private artifact supplies one deterministic ordering key without
        # reusing any individual namespace seed for a new purpose.
        seed = hashlib.sha256(
            b"fine-segmentation-candidate-run-order-seed-v1\0"
            + _canonical_bytes(private)
        ).digest()
    else:
        try:
            seed = bytes.fromhex(seed_hex)
        except (TypeError, ValueError) as error:
            raise ValueError("prepared blinding seed is invalid") from error
        if len(seed) != 32:
            raise ValueError("prepared blinding seed must contain 32 bytes")
    suite_id = freeze["suite_id"]
    entries = []
    for candidate in REQUIRED_CANDIDATES:
        for input_ordinal, logical_input in enumerate(protocol["inputs"]):
            for repetition in range(1, 3):
                input_id = logical_input["input_id"]
                message = b"\0".join(
                    (
                        suite_id.encode(),
                        RUN_ORDER_VERSION.encode(),
                        candidate.encode(),
                        input_id.encode(),
                        str(repetition).encode(),
                    )
                )
                order_key = hmac.new(seed, message, hashlib.sha256).hexdigest()
                run_id = _sha256_bytes(
                    b"\0".join(
                        (
                            RUN_ID_VERSION.encode(),
                            suite_id.encode(),
                            candidate.encode(),
                            input_id.encode(),
                            str(repetition).encode(),
                        )
                    )
                )
                entries.append(
                    {
                        "run_id": run_id,
                        "candidate": candidate,
                        "input_ordinal": input_ordinal,
                        "input_id": input_id,
                        "experiment": logical_input.get("experiment"),
                        "repetition": repetition,
                        "order_key": order_key,
                    }
                )
    entries.sort(key=lambda item: (item["order_key"], item["run_id"]))
    return entries


def _request(
    entry: dict[str, Any],
    protocol: dict[str, Any],
    vector_by_encoding: dict[str, list[float]],
    vector_manifest_sha256: str,
    normalized_vector_sha256: str,
) -> dict[str, Any]:
    logical_input = protocol["inputs"][entry["input_ordinal"]]
    if logical_input["input_id"] != entry["input_id"]:
        raise ValueError("run schedule no longer points to its logical input")
    candidate_inputs = [
        {
            "opaque_id": opaque_id,
            "normalized_vector": vector_by_encoding[encoding_id],
        }
        for opaque_id, encoding_id in zip(
            logical_input["opaque_ids"], logical_input["encoding_ids"], strict=True
        )
    ]
    request = {
        "schema_version": SCHEMA_VERSION,
        "candidate": entry["candidate"],
        "source_vector_manifest_sha256": vector_manifest_sha256,
        "normalized_vector_sha256": normalized_vector_sha256,
        "inputs": candidate_inputs,
    }
    # JSON must round-trip every coordinate back to the exact frozen f64 bits.
    decoded = json.loads(_canonical_bytes(request))
    for original, replay in zip(candidate_inputs, decoded["inputs"], strict=True):
        for left, right in zip(
            original["normalized_vector"], replay["normalized_vector"], strict=True
        ):
            if struct.pack(">d", left) != struct.pack(">d", right):
                raise ValueError(
                    "candidate request does not preserve exact f64 coordinates"
                )
    return request


def _canonical_input_sha256(inputs: list[dict[str, Any]]) -> str:
    buffer = bytearray(b"fine-region-candidate-input-v1\0")
    for item in sorted(inputs, key=lambda value: value["opaque_id"]):
        buffer.extend(item["opaque_id"].encode("ascii"))
        vector = item["normalized_vector"]
        buffer.extend(len(vector).to_bytes(8, "big"))
        for coordinate in vector:
            buffer.extend(struct.pack(">d", coordinate))
    return _sha256_bytes(buffer)


def _validate_response(
    response: object,
    request: dict[str, Any],
    frozen_candidate: dict[str, Any],
) -> dict[str, Any]:
    response = _require_exact_keys(
        "candidate response",
        response,
        {"schema_version", "candidate_identity", "artifact"},
    )
    if response["schema_version"] != SCHEMA_VERSION or response[
        "candidate_identity"
    ] != frozen_candidate.get("candidate_identity"):
        raise ValueError(
            "candidate response identity differs from the technical freeze"
        )
    artifact = _require_exact_keys(
        "candidate artifact",
        response["artifact"],
        {
            "manifest",
            "canonical_input_ids",
            "canonical_configuration_json",
            "canonical_fine_output_json",
            "result",
        },
    )
    manifest = artifact["manifest"]
    if not isinstance(manifest, dict):
        raise ValueError("candidate artifact manifest is invalid")
    contract = frozen_candidate.get("artifact_contract")
    if not isinstance(contract, dict) or any(
        manifest.get(key) != value for key, value in contract.items()
    ):
        raise ValueError(
            "candidate artifact contract differs from the technical freeze"
        )
    configuration = frozen_candidate.get("canonical_configuration_json")
    if artifact["canonical_configuration_json"] != configuration:
        raise ValueError("candidate configuration differs from the technical freeze")
    configuration_sha = _sha256_bytes(configuration.encode("utf-8"))
    if (
        manifest.get("configuration_sha256") != configuration_sha
        or frozen_candidate.get("canonical_configuration_sha256", configuration_sha)
        != configuration_sha
    ):
        raise ValueError("candidate configuration hash is invalid")
    if (
        manifest.get("source_vector_manifest_sha256")
        != request["source_vector_manifest_sha256"]
        or manifest.get("normalized_vector_sha256")
        != request["normalized_vector_sha256"]
        or manifest.get("vector_count") != len(request["inputs"])
        or manifest.get("canonical_input_sha256")
        != _canonical_input_sha256(request["inputs"])
    ):
        raise ValueError("candidate artifact is not bound to its exact request")
    expected_ids = sorted(item["opaque_id"] for item in request["inputs"])
    if artifact["canonical_input_ids"] != expected_ids:
        raise ValueError("candidate artifact input IDs differ from its exact request")
    unique_count = manifest.get("unique_vector_count")
    if not isinstance(unique_count, int) or not 1 <= unique_count <= len(expected_ids):
        raise ValueError("candidate artifact unique-vector count is invalid")

    result = artifact["result"]
    if not isinstance(result, dict) or not isinstance(result.get("fine_output"), dict):
        raise ValueError("candidate artifact result has no selected fine output")
    fine_output = result["fine_output"]
    fine_bytes = _compact_bytes(fine_output)
    try:
        retained_fine = json.loads(artifact["canonical_fine_output_json"])
        parameters = json.loads(configuration)
    except (TypeError, json.JSONDecodeError) as error:
        raise ValueError(
            "candidate artifact contains invalid canonical JSON"
        ) from error
    if (
        retained_fine != fine_output
        or artifact["canonical_fine_output_json"].encode("utf-8") != fine_bytes
        or manifest.get("fine_output_sha256") != _sha256_bytes(fine_bytes)
        or manifest.get("parameters") != parameters
    ):
        raise ValueError("candidate artifact hashes or canonical output are invalid")
    # The complete result contains floating-point values. Python and serde_json
    # can spell equivalent exponents differently, so parsing and re-encoding it
    # is not a byte-faithful recomputation of the Rust artifact hash.
    _require_sha256("candidate result SHA-256", manifest.get("result_sha256"))
    output = _require_exact_keys(
        "selected fine output", fine_output, {"segments", "unassigned"}
    )
    segments = output["segments"]
    unassigned = output["unassigned"]
    if not isinstance(segments, list) or not isinstance(unassigned, list):
        raise ValueError("candidate fine output is invalid")
    segment_sets: set[tuple[str, ...]] = set()
    segment_sort_keys: list[bytes] = []
    assigned: set[str] = set()
    for segment in segments:
        if (
            not isinstance(segment, list)
            or not segment
            or segment != sorted(set(segment))
            or any(member not in expected_ids for member in segment)
        ):
            raise ValueError("candidate fine output contains an invalid segment")
        member_set = tuple(segment)
        if member_set in segment_sets:
            raise ValueError("candidate fine output repeats a segment")
        segment_sets.add(member_set)
        segment_sort_keys.append(_compact_bytes(segment))
        assigned.update(segment)
    if (
        segment_sort_keys != sorted(segment_sort_keys)
        or unassigned != sorted(set(unassigned))
        or any(member not in expected_ids for member in unassigned)
        or assigned.intersection(unassigned)
        or assigned.union(unassigned) != set(expected_ids)
    ):
        raise ValueError(
            "candidate unassigned IDs are not the complement of its segments"
        )
    return response


def _manifest(
    prepared: Path,
    vectors: Path,
    freeze_path: Path,
    freeze: dict[str, Any],
    schedule: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "suite_id": freeze["suite_id"],
        "prepared_manifest_sha256": _sha256_file(prepared / "manifest.json"),
        "protocol_sha256": _sha256_file(prepared / "protocol.json"),
        "technical_freeze_sha256": _sha256_file(freeze_path),
        "vector_manifest_sha256": _sha256_file(vectors / "manifest.json"),
        "normalized_vector_sha256": _sha256_file(vectors / "normalized-vectors.f64le"),
        "candidate_executable_sha256": freeze["candidate_execution"][
            "executable_sha256"
        ],
        "candidate_execution_profile_sha256": _sha256_bytes(
            _canonical_compact_bytes(freeze["candidate_execution"])
        ),
        "runner_source_sha256": _sha256_file(Path(__file__).resolve()),
        "logical_input_count": freeze["logical_input_count"],
        "repetitions_per_input": 2,
        "candidate_count": len(REQUIRED_CANDIDATES),
        "expected_invocation_count": len(schedule),
        "run_order_version": RUN_ORDER_VERSION,
        "run_id_version": RUN_ID_VERSION,
        "schedule_sha256": _sha256_bytes(_canonical_bytes(schedule)),
    }


def _initialize_output(output: Path, manifest: dict[str, Any]) -> None:
    if output.exists():
        if not output.is_dir() or not (output / "manifest.json").is_file():
            raise ValueError("candidate-run output is not a resumable artifact")
        if (output / "manifest.json").read_bytes() != _canonical_bytes(manifest):
            raise ValueError("candidate-run manifest differs from the frozen inputs")
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}.", dir=output.parent))
    try:
        (stage / "runs").mkdir()
        _write_json(stage / "manifest.json", manifest)
        os.rename(stage, output)
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise


def _execute_one(
    output: Path,
    entry: dict[str, Any],
    request: dict[str, Any],
    freeze: dict[str, Any],
) -> None:
    execution = freeze["candidate_execution"]
    executable = Path(execution["executable_path"])
    actual_profile = {
        **execution,
        "executable_sha256": _sha256_file(executable),
        "host": _actual_host(),
        "resource_limits": _actual_resource_limits(),
    }
    if actual_profile != execution:
        raise ValueError("actual candidate execution profile differs from the freeze")
    runs = output / "runs"
    stage = Path(tempfile.mkdtemp(prefix=".invocation-", dir=runs))
    request_path = stage / "request.json"
    try:
        _write_json(request_path, request)
        started_ns = time.time_ns()
        process = subprocess.Popen(
            [str(executable), str(request_path)],
            cwd=execution["working_directory"],
            env=execution["environment"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = process.communicate()
        finished_ns = time.time_ns()
        _write(stage / "stdout.bin", stdout)
        _write(stage / "stderr.bin", stderr)
        status, integrity_error, response = _classify_candidate_output(
            process.returncode,
            stdout,
            request,
            freeze["candidates"][entry["candidate"]],
        )
        record: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "suite_id": freeze["suite_id"],
            "run_id": entry["run_id"],
            "candidate": entry["candidate"],
            "candidate_identity": freeze["candidates"][entry["candidate"]][
                "candidate_identity"
            ],
            "input_ordinal": entry["input_ordinal"],
            "input_id": entry["input_id"],
            "experiment": entry["experiment"],
            "repetition": entry["repetition"],
            "order_key": entry["order_key"],
            "process_id": process.pid,
            "started_unix_ns": started_ns,
            "finished_unix_ns": finished_ns,
            "return_code": process.returncode,
            "status": status,
            "integrity_error": integrity_error,
            "execution_profile": actual_profile,
            "execution_profile_sha256": _sha256_bytes(
                _canonical_compact_bytes(actual_profile)
            ),
            "actual_argv": [str(executable), str(request_path)],
            "files": {
                "request.json": _sha256_file(request_path),
                "stdout.bin": _sha256_bytes(stdout),
                "stderr.bin": _sha256_bytes(stderr),
            },
        }
        if response is not None:
            response_bytes = _canonical_bytes(response)
            fine_output_bytes = response["artifact"][
                "canonical_fine_output_json"
            ].encode("utf-8")
            _write(stage / "response.json", response_bytes)
            _write(stage / "fine-output.json", fine_output_bytes)
            record["files"]["response.json"] = _sha256_bytes(response_bytes)
            record["files"]["fine-output.json"] = _sha256_bytes(fine_output_bytes)
            record["fine_output_sha256"] = response["artifact"]["manifest"][
                "fine_output_sha256"
            ]
        else:
            record["fine_output_sha256"] = None
        _write_json(stage / "record.json", record)
        os.rename(stage, runs / entry["run_id"])
    except BaseException:
        if stage.exists():
            shutil.rmtree(stage, ignore_errors=True)
        raise
    if _sha256_file(executable) != execution["executable_sha256"]:
        raise ValueError("candidate executable changed after invocation")


def _classify_candidate_output(
    return_code: int,
    stdout: bytes,
    request: dict[str, Any],
    frozen_candidate: dict[str, Any],
) -> tuple[str, str | None, dict[str, Any] | None]:
    if return_code != 0:
        return (
            "integrity-failure",
            f"candidate exited with status {return_code}",
            None,
        )
    try:
        response = json.loads(stdout.decode("utf-8"))
        response = _validate_response(response, request, frozen_candidate)
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        ValueError,
        TypeError,
        KeyError,
        AttributeError,
    ) as error:
        return "integrity-failure", f"invalid candidate response: {error}", None
    return "valid", None, response


def _verify_one(
    directory: Path,
    entry: dict[str, Any],
    expected_request: dict[str, Any],
    freeze: dict[str, Any],
) -> tuple[dict[str, Any], bytes | None]:
    record = _read_json(directory / "record.json")
    expected_files = {"record.json", "request.json", "stderr.bin", "stdout.bin"}
    if record.get("status") == "valid":
        expected_files.update(("response.json", "fine-output.json"))
    if {item.name for item in directory.iterdir()} != expected_files:
        raise ValueError(f"run {entry['run_id']} has unexpected files")
    for field in (
        "run_id",
        "candidate",
        "input_ordinal",
        "input_id",
        "experiment",
        "repetition",
        "order_key",
    ):
        if record.get(field) != entry[field]:
            raise ValueError(f"run {entry['run_id']} record field {field} is invalid")
    if (
        record.get("schema_version") != SCHEMA_VERSION
        or record.get("suite_id") != freeze["suite_id"]
        or record.get("candidate_identity")
        != freeze["candidates"][entry["candidate"]]["candidate_identity"]
        or record.get("status") not in {"valid", "integrity-failure"}
    ):
        raise ValueError(f"run {entry['run_id']} has an invalid integrity status")
    execution = freeze["candidate_execution"]
    if record.get("execution_profile") != execution:
        raise ValueError(f"run {entry['run_id']} execution profile is invalid")
    if record.get("execution_profile_sha256") != _sha256_bytes(
        _canonical_compact_bytes(execution)
    ):
        raise ValueError(f"run {entry['run_id']} execution profile hash is invalid")
    actual_argv = record.get("actual_argv")
    substituted_argv = None
    if isinstance(actual_argv, list) and len(actual_argv) == 2:
        substituted_argv = [
            value.replace("{executable}", execution["executable_path"]).replace(
                "{request_path}", actual_argv[1]
            )
            for value in execution["argv_template"]
        ]
    if (
        not isinstance(actual_argv, list)
        or len(actual_argv) != 2
        or actual_argv != substituted_argv
        or Path(actual_argv[1]).name != "request.json"
        or not Path(actual_argv[1]).parent.name.startswith(".invocation-")
        or Path(actual_argv[1]).parent.parent != directory.parent
    ):
        raise ValueError(f"run {entry['run_id']} actual argv is invalid")
    if (
        not isinstance(record.get("process_id"), int)
        or not isinstance(record.get("started_unix_ns"), int)
        or not isinstance(record.get("finished_unix_ns"), int)
        or record["finished_unix_ns"] < record["started_unix_ns"]
        or not isinstance(record.get("return_code"), int)
    ):
        raise ValueError(f"run {entry['run_id']} process evidence is invalid")
    request_bytes = _canonical_bytes(expected_request)
    if (directory / "request.json").read_bytes() != request_bytes:
        raise ValueError(f"run {entry['run_id']} request differs from replay")
    files = record.get("files")
    if not isinstance(files, dict):
        raise ValueError(f"run {entry['run_id']} file identities are missing")
    if set(files) != expected_files - {"record.json"}:
        raise ValueError(f"run {entry['run_id']} file identity set is invalid")
    for name in expected_files - {"record.json"}:
        actual = _sha256_file(directory / name)
        if files.get(name) != actual:
            label = "stdout" if name == "stdout.bin" else name
            raise ValueError(f"run {entry['run_id']} {label} differs from its record")
    stdout = (directory / "stdout.bin").read_bytes()
    status, integrity_error, response = _classify_candidate_output(
        record.get("return_code"),
        stdout,
        expected_request,
        freeze["candidates"][entry["candidate"]],
    )
    if (
        record.get("status") != status
        or record.get("integrity_error") != integrity_error
    ):
        raise ValueError(f"run {entry['run_id']} integrity classification is invalid")
    if response is None:
        if record.get("fine_output_sha256") is not None:
            raise ValueError(
                f"run {entry['run_id']} failed output has a fine-output hash"
            )
        return record, None
    response_bytes = _canonical_bytes(response)
    if (directory / "response.json").read_bytes() != response_bytes:
        raise ValueError(
            f"run {entry['run_id']} response differs from validated stdout"
        )
    if (
        record.get("fine_output_sha256")
        != response["artifact"]["manifest"]["fine_output_sha256"]
    ):
        raise ValueError(f"run {entry['run_id']} fine output identity is invalid")
    fine_output_bytes = response["artifact"]["canonical_fine_output_json"].encode(
        "utf-8"
    )
    if (directory / "fine-output.json").read_bytes() != fine_output_bytes:
        raise ValueError(f"run {entry['run_id']} canonical fine output is invalid")
    return record, fine_output_bytes


def _completion(
    freeze: dict[str, Any],
    schedule: list[dict[str, Any]],
    records: list[dict[str, Any]],
    repeatability_counts: dict[str, int],
) -> dict[str, Any]:
    candidate_counts = {
        candidate: sum(record["candidate"] == candidate for record in records)
        for candidate in REQUIRED_CANDIDATES
    }
    valid_candidate_counts = {
        candidate: sum(
            record["candidate"] == candidate and record["status"] == "valid"
            for record in records
        )
        for candidate in REQUIRED_CANDIDATES
    }
    record_identities = [
        {
            "run_id": record["run_id"],
            "request_sha256": record["files"]["request.json"],
            "stdout_sha256": record["files"]["stdout.bin"],
            "stderr_sha256": record["files"]["stderr.bin"],
            "response_sha256": record["files"].get("response.json"),
            "fine_output_file_sha256": record["files"].get("fine-output.json"),
            "fine_output_sha256": record["fine_output_sha256"],
            "status": record["status"],
            "integrity_error": record["integrity_error"],
        }
        for record in sorted(records, key=lambda value: value["run_id"])
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "suite_id": freeze["suite_id"],
        "complete": len(records) == len(schedule),
        "logical_input_count": freeze["logical_input_count"],
        "repetitions_per_input": 2,
        "completed_invocation_count": len(records),
        "candidate_counts": candidate_counts,
        "valid_candidate_counts": valid_candidate_counts,
        "integrity_failure_count": sum(
            record["status"] == "integrity-failure" for record in records
        ),
        "repeatability_counts": repeatability_counts,
        "all_valid_repeat_pairs_identical": repeatability_counts["different"] == 0,
        "run_record_set_sha256": _sha256_bytes(_canonical_bytes(record_identities)),
    }


def _load_context(
    prepared_path: Path | str,
    vector_artifact_path: Path | str,
    technical_freeze_path: Path | str,
) -> tuple[
    Path,
    Path,
    Path,
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, list[float]],
    list[dict[str, Any]],
]:
    prepared = Path(prepared_path).resolve()
    vectors = Path(vector_artifact_path).resolve()
    freeze_path = Path(technical_freeze_path).resolve()
    freeze, protocol, vector_manifest, vector_by_encoding = _load_bound_inputs(
        prepared, vectors, freeze_path
    )
    private = _read_json(prepared / "blinding-private.json")
    schedule = _schedule(freeze, protocol, private)
    if len(schedule) != freeze["invocations_per_candidate"] * len(REQUIRED_CANDIDATES):
        raise ValueError("candidate run schedule violates the technical freeze")
    return (
        prepared,
        vectors,
        freeze_path,
        freeze,
        protocol,
        vector_manifest,
        vector_by_encoding,
        schedule,
    )


def run_candidate_suite(
    prepared_path: Path | str,
    vector_artifact_path: Path | str,
    technical_freeze_path: Path | str,
    output_path: Path | str,
) -> dict[str, Any]:
    """Run every frozen candidate/input/repetition, resuming completed invocations."""

    (
        prepared,
        vectors,
        freeze_path,
        freeze,
        protocol,
        vector_manifest,
        vector_by_encoding,
        schedule,
    ) = _load_context(prepared_path, vector_artifact_path, technical_freeze_path)
    output = Path(output_path).resolve()
    manifest = _manifest(prepared, vectors, freeze_path, freeze, schedule)
    _initialize_output(output, manifest)
    runs = output / "runs"
    for stage in runs.glob(".invocation-*"):
        if stage.is_dir():
            shutil.rmtree(stage)

    vector_manifest_sha = _sha256_file(vectors / "manifest.json")
    normalized_sha = vector_manifest["files"]["normalized-vectors.f64le"]["sha256"]
    for entry in schedule:
        request = _request(
            entry,
            protocol,
            vector_by_encoding,
            vector_manifest_sha,
            normalized_sha,
        )
        destination = runs / entry["run_id"]
        if destination.exists():
            _verify_one(destination, entry, request, freeze)
            continue
        _execute_one(output, entry, request, freeze)

    report = _verify_candidate_suite_runs(
        prepared, vectors, freeze_path, output, require_completion=False
    )
    completion = {key: value for key, value in report.items() if key != "output_path"}
    temporary = output / ".completion.json.tmp"
    if temporary.exists():
        temporary.unlink()
    _write(temporary, _canonical_bytes(completion))
    os.replace(temporary, output / "completion.json")
    return verify_candidate_suite_runs(prepared, vectors, freeze_path, output)


def verify_candidate_suite_runs(
    prepared_path: Path | str,
    vector_artifact_path: Path | str,
    technical_freeze_path: Path | str,
    output_path: Path | str,
) -> dict[str, Any]:
    """Replay the frozen schedule and verify every retained process artifact."""

    return _verify_candidate_suite_runs(
        prepared_path,
        vector_artifact_path,
        technical_freeze_path,
        output_path,
        require_completion=True,
    )


def _verify_candidate_suite_runs(
    prepared_path: Path | str,
    vector_artifact_path: Path | str,
    technical_freeze_path: Path | str,
    output_path: Path | str,
    *,
    require_completion: bool,
) -> dict[str, Any]:

    (
        prepared,
        vectors,
        freeze_path,
        freeze,
        protocol,
        vector_manifest,
        vector_by_encoding,
        schedule,
    ) = _load_context(prepared_path, vector_artifact_path, technical_freeze_path)
    output = Path(output_path).resolve()
    expected_manifest = _manifest(prepared, vectors, freeze_path, freeze, schedule)
    allowed = {"manifest.json", "runs", "completion.json"}
    if not output.is_dir() or {item.name for item in output.iterdir()} - allowed:
        raise ValueError("candidate-run output has unexpected entries")
    if (output / "manifest.json").read_bytes() != _canonical_bytes(expected_manifest):
        raise ValueError("candidate-run manifest differs from replay")
    runs = output / "runs"
    expected_ids = {entry["run_id"] for entry in schedule}
    actual_ids = {item.name for item in runs.iterdir() if item.is_dir()}
    if actual_ids != expected_ids:
        raise ValueError("candidate-run coverage differs from the frozen schedule")

    vector_manifest_sha = _sha256_file(vectors / "manifest.json")
    normalized_sha = vector_manifest["files"]["normalized-vectors.f64le"]["sha256"]
    records = []
    fine_outputs: dict[tuple[str, str], list[tuple[int, bytes | None]]] = {}
    for entry in schedule:
        request = _request(
            entry,
            protocol,
            vector_by_encoding,
            vector_manifest_sha,
            normalized_sha,
        )
        record, fine_output = _verify_one(
            runs / entry["run_id"], entry, request, freeze
        )
        records.append(record)
        fine_outputs.setdefault((entry["candidate"], entry["input_id"]), []).append(
            (entry["repetition"], fine_output)
        )
    repeatability_counts = {"identical": 0, "different": 0, "unavailable": 0}
    for repeats in fine_outputs.values():
        repeats.sort(key=lambda item: item[0])
        outputs = [item[1] for item in repeats]
        if len(outputs) != 2 or any(output is None for output in outputs):
            repeatability_counts["unavailable"] += 1
        elif outputs[0] == outputs[1]:
            repeatability_counts["identical"] += 1
        else:
            repeatability_counts["different"] += 1
    completion = _completion(freeze, schedule, records, repeatability_counts)
    completion_path = output / "completion.json"
    completion_bytes = _canonical_bytes(completion)
    if completion_path.exists():
        if completion_path.read_bytes() != completion_bytes:
            raise ValueError("candidate-run completion record differs from replay")
    elif require_completion:
        raise ValueError("candidate-run completion record is missing")
    return {**completion, "output_path": str(output)}


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("run", "verify"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("prepared", type=Path)
        subparser.add_argument("vectors", type=Path)
        subparser.add_argument("technical_freeze", type=Path)
        subparser.add_argument("output", type=Path)
    args = parser.parse_args(list(argv) if argv is not None else None)
    operation = (
        run_candidate_suite if args.command == "run" else verify_candidate_suite_runs
    )
    report = operation(args.prepared, args.vectors, args.technical_freeze, args.output)
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
