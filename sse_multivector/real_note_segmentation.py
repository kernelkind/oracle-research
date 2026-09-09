#!/usr/bin/env python3
"""Adapt explicitly reviewed real-note masks to the existing SSE worker."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
from pathlib import Path

from sse_multivector.fine_segmentation_candidate_runs import _canonical_input_sha256
from sse_multivector.worker import (
    ModelDescriptor,
    TREE_HASH_RULE,
    VECTOR_FORMAT,
    _byte_span_to_character_span,
    _expect_int,
    _expect_lower_hex,
    _expect_object,
    _expect_string,
)


NORMALIZATION = "row-major-f32le-to-exact-f64-l2-normalized-f64le-v1"
REVIEW_QUESTION = "Are all instances recognizable as refinements of one fine subject?"
REVIEW_INSTRUCTIONS = {
    "question": "For each packet, decide whether all instances are recognizable as refinements of one fine subject.",
    "valid": "Every instance is recognizable as a refinement of one fine subject.",
    "invalid": "No one recognizable, non-disjunctive fine subject covers every instance.",
    "uncertain": "The masks do not support a confident valid/invalid decision.",
}
REVIEW_VERDICTS = ["valid", "invalid", "uncertain"]


def _canonical(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _identity(raw: bytes) -> dict:
    return {"bytes": len(raw), "sha256": _sha(raw)}


def _array(value: object, name: str, *, nonempty: bool = True) -> list:
    if not isinstance(value, list) or (nonempty and not value):
        raise ValueError(f"{name} must be a {'nonempty ' if nonempty else ''}array")
    return value


def _new_output(path: Path) -> None:
    if path.exists() or path.is_symlink():
        raise ValueError(f"output already exists: {path}")


def _write_output(path: Path, files: dict[str, bytes]) -> None:
    _new_output(path)
    path.mkdir(parents=True, exist_ok=False)
    for name, raw in files.items():
        with (path / name).open("xb") as destination:
            destination.write(raw)


def _validate_encoder(value: object) -> dict:
    encoder = _expect_object(value, "encoder descriptor")
    if type(encoder.get("schema_version")) is not int or encoder["schema_version"] != 1:
        raise ValueError("encoder descriptor must use schema_version 1")
    for name in (
        "checkpoint_sha256",
        "base_model_artifact_tree_sha256",
        "worker_sha256",
    ):
        _expect_lower_hex(encoder.get(name), f"encoder.{name}", 64)
    for name in ("checkpoint_path", "base_model_artifact_path", "worker_path"):
        _expect_string(encoder.get(name), f"encoder.{name}")
    image = _expect_string(encoder.get("container_image"), "encoder.container_image")
    if not (image.startswith("sha256:") or "@sha256:" in image):
        raise ValueError("encoder.container_image must name an immutable SHA-256 image")
    _expect_lower_hex(image.rsplit("sha256:", 1)[1], "container image digest", 64)
    _expect_int(encoder.get("note_batch_size"), "encoder.note_batch_size", minimum=1)
    ModelDescriptor.from_json(encoder.get("model"))
    return encoder


def _compile_inputs(reviewed: object, reviewed_sha256: str) -> tuple[dict, dict]:
    document = _expect_object(reviewed, "reviewed input")
    if (
        type(document.get("schema_version")) is not int
        or document["schema_version"] != 1
    ):
        raise ValueError("reviewed input must use schema_version 1")
    request_notes, mapped_notes, vectors, excluded = [], [], [], []
    note_ids, worker_ids, vector_ids = set(), set(), set()
    for note_index, raw_note in enumerate(_array(document.get("notes"), "notes")):
        note = _expect_object(raw_note, f"notes[{note_index}]")
        note_id = _expect_lower_hex(note.get("note_id"), "note_id", 64)
        if note_id in note_ids:
            raise ValueError(f"duplicate note ID: {note_id}")
        note_ids.add(note_id)
        text = _expect_string(note.get("text"), "note.text")
        encoded = text.encode("utf-8")
        deduplicate = note.get("deduplicate_identical_masks", False)
        if type(deduplicate) is not bool:
            raise ValueError("note.deduplicate_identical_masks must be a boolean")
        distinct_masks = {}
        note_short_id = f"N{note_index + 1:03d}"
        mapped_notes.append(
            {
                "note_id": note_id,
                "short_id": note_short_id,
                "reviewed_note_index": note_index,
                "text_sha256": _sha(encoded),
            }
        )
        subject_ids, worker_subjects = set(), []
        for subject_index, raw_subject in enumerate(
            _array(note.get("subjects"), "note.subjects", nonempty=False)
        ):
            subject = _expect_object(raw_subject, "reviewed subject")
            reviewed_id = _expect_string(subject.get("id"), "subject.id")
            if reviewed_id in subject_ids:
                raise ValueError(
                    f"duplicate reviewed subject ID in note {note_id}: {reviewed_id}"
                )
            subject_ids.add(reviewed_id)
            subject_text = _expect_string(subject.get("subject"), "subject.subject")
            judgment = subject.get("judgment")
            if judgment not in ("accepted", "rejected", "unresolved"):
                raise ValueError(f"subject {reviewed_id} has an unknown judgment")
            mapping = {
                "note_id": note_id,
                "note_short_id": note_short_id,
                "reviewed_subject_id": reviewed_id,
                "reviewed_note_index": note_index,
                "reviewed_subject_index": subject_index,
                "subject": subject_text,
                "judgment": judgment,
                "reviewed_subject": subject,
            }
            if judgment != "accepted":
                excluded.append(mapping)
                continue
            fragments = _array(subject.get("fragments"), "subject.fragments")
            spans = _array(subject.get("byte_spans"), "subject.byte_spans")
            if len(fragments) != len(spans):
                raise ValueError("fragments and byte_spans must have equal length")
            previous_end = 0
            for fragment, span in zip(fragments, spans, strict=True):
                _expect_string(fragment, "mask fragment")
                if not isinstance(span, list) or len(span) != 2:
                    raise ValueError("byte_spans must contain [start, end] pairs")
                start = _expect_int(span[0], "span start")
                end = _expect_int(span[1], "span end")
                if start < previous_end:
                    raise ValueError("mask spans overlap or are out of source order")
                _byte_span_to_character_span(text, (start, end))
                if encoded[start:end] != fragment.encode("utf-8"):
                    raise ValueError(
                        "mask fragment is not exact text at its explicit byte span"
                    )
                previous_end = end
            identity = _canonical(
                [note_id, _sha(encoded), reviewed_id, subject_text, fragments, spans]
            )
            worker_id = _sha(b"real-note-worker-subject-v1\0" + identity)[:16]
            vector_id = _sha(b"real-note-vector-v1\0" + identity)
            if worker_id in worker_ids or vector_id in vector_ids:
                raise ValueError("derived subject or vector ID collision")
            worker_ids.add(worker_id)
            vector_ids.add(vector_id)
            if deduplicate:
                source_subject = {
                    **mapping,
                    "vector_id": vector_id,
                    "worker_subject_id": worker_id,
                }
                mask_key = tuple(tuple(span) for span in spans)
                if mask_key in distinct_masks:
                    distinct_masks[mask_key]["reviewed_subjects"].append(source_subject)
                    continue
            worker_subjects.append({"subject_id": worker_id, "byte_spans": spans})
            vectors.append(
                {
                    **mapping,
                    "ordinal": len(vectors),
                    "vector_id": vector_id,
                    "short_id": f"V{len(vectors) + 1:03d}",
                    "worker_subject_id": worker_id,
                    "fragments": fragments,
                    "byte_spans": spans,
                }
            )
            if deduplicate:
                vectors[-1]["reviewed_subjects"] = [source_subject]
                distinct_masks[mask_key] = vectors[-1]
        if worker_subjects:
            request_notes.append(
                {"note_id": note_id, "text": text, "subjects": worker_subjects}
            )
    if not vectors:
        raise ValueError("reviewed input contains no accepted masks")
    request = {
        "schema_version": 1,
        "proposal_sha256": reviewed_sha256,
        "notes": request_notes,
    }
    mapping = {
        "schema_version": 1,
        "notes": mapped_notes,
        "vector_count": len(vectors),
        "vectors": vectors,
        "excluded": excluded,
    }
    return request, mapping


def prepare_reviewed_inputs(
    reviewed_path: Path | str,
    encoder_path: Path | str,
    subject_package_path: Path | str,
    mask_package_path: Path | str,
    output_path: Path | str,
) -> dict:
    """Freeze reviewed inputs and compile accepted explicit masks; never infer positions."""
    output = Path(output_path)
    _new_output(output)
    paths = {
        "reviewed-input.json": Path(reviewed_path).resolve(),
        "encoder.json": Path(encoder_path).resolve(),
        "subject-package.json": Path(subject_package_path).resolve(),
        "mask-package.json": Path(mask_package_path).resolve(),
    }
    files = {name: path.read_bytes() for name, path in paths.items()}
    values = {name: json.loads(raw) for name, raw in files.items()}
    _validate_encoder(values["encoder.json"])
    for name, version in (
        ("subject-package.json", "ASv6.23"),
        ("mask-package.json", "MPv3.5"),
    ):
        package = _expect_object(values[name], name)
        if package.get("status") != "frozen" or package.get("version") != version:
            raise ValueError(f"{name} must be frozen {version}")
    request, mapping = _compile_inputs(
        values["reviewed-input.json"], _sha(files["reviewed-input.json"])
    )
    files["worker-request.json"] = _canonical(request)
    files["vector-map.json"] = _canonical(mapping)
    manifest = {
        "schema_version": 1,
        "note_count": len(mapping["notes"]),
        "encoded_note_count": len(request["notes"]),
        "vector_count": len(mapping["vectors"]),
        "excluded_subject_count": len(mapping["excluded"]),
        "sources": {
            name: {"path": str(path), **_identity(files[name])}
            for name, path in paths.items()
        },
        "adapter_sha256": _sha(Path(__file__).read_bytes()),
        "files": {name: _identity(raw) for name, raw in files.items()},
    }
    files["manifest.json"] = _canonical(manifest)
    _write_output(output, files)
    return manifest


def _prepared_files(prepared: Path) -> tuple[dict[str, bytes], dict, dict, dict]:
    manifest_raw = (prepared / "manifest.json").read_bytes()
    manifest = _expect_object(json.loads(manifest_raw), "prepared manifest")
    names = {
        "reviewed-input.json",
        "encoder.json",
        "subject-package.json",
        "mask-package.json",
        "worker-request.json",
        "vector-map.json",
    }
    if manifest.get("schema_version") != 1 or set(manifest.get("files", {})) != names:
        raise ValueError("prepared manifest has invalid files or schema")
    files = {name: (prepared / name).read_bytes() for name in names}
    for name, raw in files.items():
        if manifest["files"][name] != _identity(raw):
            raise ValueError(f"prepared file hash differs from manifest: {name}")
    source_names = names - {"worker-request.json", "vector-map.json"}
    if set(manifest.get("sources", {})) != source_names:
        raise ValueError("prepared manifest has incomplete source identities")
    for name in source_names:
        source = manifest["sources"][name]
        if source.get("sha256") != _sha(files[name]) or source.get("bytes") != len(
            files[name]
        ):
            raise ValueError(f"prepared source hash differs from saved bytes: {name}")
        if _identity(Path(source["path"]).read_bytes()) != _identity(files[name]):
            raise ValueError(f"prepared source file hash has changed: {name}")
    request, mapping = _compile_inputs(
        json.loads(files["reviewed-input.json"]), _sha(files["reviewed-input.json"])
    )
    if files["worker-request.json"] != _canonical(request) or files[
        "vector-map.json"
    ] != _canonical(mapping):
        raise ValueError(
            "prepared request or vector map differs from reviewed source replay"
        )
    encoder = _validate_encoder(json.loads(files["encoder.json"]))
    files["prepared-manifest.json"] = manifest_raw
    return files, request, mapping, encoder


def _validate_tokens(row: dict, maximum_tokens: int, ordinal: int) -> None:
    indices = row.get("selected_token_indices")
    token_ids = row.get("selected_token_ids")
    count = row.get("token_count")
    if (
        not isinstance(indices, list)
        or not indices
        or any(type(index) is not int for index in indices)
        or indices != sorted(set(indices))
        or not isinstance(token_ids, list)
        or len(token_ids) != len(indices)
        or any(type(token_id) is not int or token_id < 0 for token_id in token_ids)
        or type(count) is not int
        or not 1 <= count <= maximum_tokens
        or any(index < 0 or index >= count for index in indices)
    ):
        raise ValueError(f"worker row {ordinal} has invalid selected-token evidence")


def finalize_vectors(
    prepared_path: Path | str,
    worker_output_path: Path | str,
    output_path: Path | str,
) -> dict:
    """Validate saved worker output and normalize exact decoded f32 values in f64."""
    output = Path(output_path)
    _new_output(output)
    files, request, mapping, encoder = _prepared_files(Path(prepared_path))
    worker = Path(worker_output_path)
    raw = (worker / "raw-vectors.f32le").read_bytes()
    receipt_raw = (worker / "worker-receipt.json").read_bytes()
    receipt = _expect_object(json.loads(receipt_raw), "worker receipt")
    expected = {
        "schema_version": 1,
        "proposal_sha256": request["proposal_sha256"],
        "request_sha256": _sha(files["worker-request.json"]),
        "checkpoint_sha256": encoder["checkpoint_sha256"],
        "base_model_artifact_tree_sha256": encoder["base_model_artifact_tree_sha256"],
        "tree_hash_rule": TREE_HASH_RULE,
        "model": encoder["model"],
        "container_image": encoder["container_image"],
        "device": "cpu",
        "note_batch_size": encoder["note_batch_size"],
        "vector_format": VECTOR_FORMAT,
        "dimensions": encoder["model"]["dimensions"],
        "row_count": mapping["vector_count"],
    }
    for name, value in expected.items():
        if receipt.get(name) != value or type(receipt.get(name)) is not type(value):
            raise ValueError(f"worker receipt differs from frozen {name}")
    runtime = _expect_object(receipt.get("runtime"), "worker runtime")
    if runtime.get("worker_sha256") != encoder["worker_sha256"]:
        raise ValueError("worker receipt differs from frozen worker_sha256")
    dimensions = expected["dimensions"]
    rows = _array(receipt.get("rows"), "worker rows")
    if len(rows) != mapping["vector_count"]:
        raise ValueError("worker row count differs from vector map")
    if len(raw) != len(rows) * dimensions * 4:
        raise ValueError("worker raw vector byte count is inconsistent")
    if receipt.get("files", {}).get("raw-vectors.f32le") != _identity(raw):
        raise ValueError("worker raw vector file hash or size differs from receipt")
    normalized, candidate_inputs, norms = bytearray(), [], []
    for ordinal, (mapped, raw_row) in enumerate(
        zip(mapping["vectors"], rows, strict=True)
    ):
        row = _expect_object(raw_row, "worker row")
        if (
            type(row.get("ordinal")) is not int
            or row["ordinal"] != ordinal
            or row.get("note_id") != mapped["note_id"]
            or row.get("subject_id") != mapped["worker_subject_id"]
        ):
            raise ValueError(
                f"worker row order differs from vector map at row {ordinal}"
            )
        _validate_tokens(row, encoder["model"]["maximum_tokens"], ordinal)
        values = struct.unpack_from(f"<{dimensions}f", raw, ordinal * dimensions * 4)
        if not all(math.isfinite(value) for value in values):
            raise ValueError(f"worker row {ordinal} contains non-finite coordinates")
        norm = math.sqrt(sum(float(value) * float(value) for value in values))
        if not math.isfinite(norm) or norm == 0:
            raise ValueError(f"worker row {ordinal} has an invalid norm")
        values = [float(value) / norm for value in values]
        normalized.extend(struct.pack(f"<{dimensions}d", *values))
        norms.append(math.sqrt(sum(value * value for value in values)))
        candidate_inputs.append(
            {"opaque_id": mapped["vector_id"], "normalized_vector": values}
        )
        mapped.update(
            {
                key: row[key]
                for key in (
                    "selected_token_indices",
                    "selected_token_ids",
                    "token_count",
                )
            }
        )
    mapping["dimensions"] = dimensions
    files.update(
        {
            "vector-map.json": _canonical(mapping),
            "raw-vectors.f32le": raw,
            "normalized-vectors.f64le": bytes(normalized),
            "worker-receipt.json": receipt_raw,
        }
    )
    manifest = {
        "schema_version": 1,
        "vector_count": len(rows),
        "dimensions": dimensions,
        "raw_decode_and_normalization_contract": NORMALIZATION,
        "minimum_normalized_norm": min(norms),
        "maximum_normalized_norm": max(norms),
        "sources": {
            "prepared_manifest_sha256": _sha(files["prepared-manifest.json"]),
            "worker_receipt_sha256": _sha(receipt_raw),
        },
        "files": {name: _identity(value) for name, value in files.items()},
    }
    files["manifest.json"] = _canonical(manifest)
    files["candidate-request.json"] = _canonical(
        {
            "schema_version": 1,
            "candidate": "hdbscan",
            "source_vector_manifest_sha256": _sha(files["manifest.json"]),
            "normalized_vector_sha256": _sha(bytes(normalized)),
            "inputs": candidate_inputs,
        }
    )
    _write_output(output, files)
    return manifest


def _review_evidence(vector_artifact: Path) -> tuple[bytes, dict, dict, list]:
    manifest_raw = (vector_artifact / "manifest.json").read_bytes()
    manifest = _expect_object(json.loads(manifest_raw), "vector manifest")
    if (
        manifest.get("schema_version") != 1
        or manifest.get("raw_decode_and_normalization_contract") != NORMALIZATION
    ):
        raise ValueError("unsupported vector artifact schema or normalization")
    declared_files = _expect_object(manifest.get("files"), "vector manifest files")
    required_files = {"vector-map.json", "reviewed-input.json", "normalized-vectors.f64le"}
    if not required_files <= declared_files.keys():
        raise ValueError("vector manifest omits required evidence files")
    files = {}
    for name, identity in declared_files.items():
        if not name or Path(name).name != name or name in (".", ".."):
            raise ValueError(f"vector manifest has an invalid artifact filename: {name}")
        try:
            raw = (vector_artifact / name).read_bytes()
        except OSError as error:
            raise ValueError(f"cannot read declared vector artifact file: {name}") from error
        if identity != _identity(raw):
            raise ValueError(f"vector artifact file hash differs from manifest: {name}")
        if name in required_files:
            files[name] = raw
    reviewed = json.loads(files["reviewed-input.json"])
    _, expected_map = _compile_inputs(reviewed, _sha(files["reviewed-input.json"]))
    mapping = _expect_object(json.loads(files["vector-map.json"]), "vector map")
    vectors = _array(mapping.get("vectors"), "mapped vectors")
    dimensions = _expect_int(manifest.get("dimensions"), "dimensions", minimum=1)
    raw = files["normalized-vectors.f64le"]
    if (
        len(vectors) != len(expected_map["vectors"])
        or len(vectors) != manifest.get("vector_count")
        or mapping.get("vector_count") != len(vectors)
        or mapping.get("dimensions") != dimensions
        or len(raw) != len(vectors) * dimensions * 8
    ):
        raise ValueError("vector artifact shape differs from reviewed input")
    evidence, candidate_inputs = {}, []
    for ordinal, (mapped, expected) in enumerate(
        zip(vectors, expected_map["vectors"], strict=True)
    ):
        if any(mapped.get(key) != value for key, value in expected.items()):
            raise ValueError("vector map differs from reviewed source evidence")
        note = reviewed["notes"][mapped["reviewed_note_index"]]
        evidence[mapped["vector_id"]] = {
            "instance": mapped["short_id"],
            "note_id": mapped["note_id"],
            "vector_id": mapped["vector_id"],
            "text": note["text"],
            "byte_spans": mapped["byte_spans"],
        }
        values = list(
            struct.unpack_from(f"<{dimensions}d", raw, ordinal * dimensions * 8)
        )
        if not all(math.isfinite(value) for value in values) or not math.isclose(
            math.sqrt(sum(value * value for value in values)),
            1.0,
            rel_tol=0,
            abs_tol=1e-12,
        ):
            raise ValueError(
                "vector artifact has non-finite or non-unit normalized vectors"
            )
        candidate_inputs.append(
            {"opaque_id": mapped["vector_id"], "normalized_vector": values}
        )
    return manifest_raw, manifest, evidence, candidate_inputs


def package_review(
    vector_artifact: Path | str,
    candidate_result_json: Path | str,
    output_path: Path | str,
) -> dict:
    """Package every selected segment for unlabeled review; retain noise separately."""
    output = Path(output_path)
    _new_output(output)
    vector_manifest_raw, vector_manifest, evidence, inputs = _review_evidence(
        Path(vector_artifact)
    )
    candidate_raw = Path(candidate_result_json).read_bytes()
    response = _expect_object(json.loads(candidate_raw), "candidate response")
    if response.get("schema_version") != 1:
        raise ValueError("unsupported candidate response schema")
    candidate_identity = _expect_string(
        response.get("candidate_identity"), "candidate identity"
    )
    artifact = _expect_object(response.get("artifact"), "candidate artifact")
    manifest = _expect_object(artifact.get("manifest"), "candidate manifest")
    algorithm = manifest.get("algorithm_version")
    if (
        manifest.get("schema_version") != 4
        or algorithm not in (
            "hdbscan-star-exact-angular-v1",
            "hdbscan-star-cross-note-exact-angular-v1",
        )
        or manifest.get("fine_output_selector_version") != "hdbscan-clusters-members-v1"
    ):
        raise ValueError(
            "review packaging requires the HDBSCAN selected-output artifact"
        )
    cross_note = None
    cross_note_identities = {
        "hdbscan-cross-note-controlled-suite-config-v1",
        "hdbscan-cross-note-explicit-config-v1",
    }
    if algorithm == "hdbscan-star-cross-note-exact-angular-v1":
        if candidate_identity not in cross_note_identities:
            raise ValueError("cross-note candidate identity differs from algorithm")
        source_note_ids = {member: item["note_id"] for member, item in evidence.items()}
        cross_note = {
            "core_distance_rule_version": "nearest-different-source-note-angular-v1",
            "source_note_ids_sha256": _sha(
                json.dumps(
                    source_note_ids, sort_keys=True, separators=(",", ":")
                ).encode("utf-8")
            ),
        }
        if manifest.get("cross_note") != cross_note:
            raise ValueError(
                "cross-note rule or source note map hash differs from verified vector evidence"
            )
    elif "cross_note" in manifest or candidate_identity in cross_note_identities:
        raise ValueError(
            "cross-note metadata or identity requires the cross-note algorithm"
        )
    expected_hashes = {
        "source_vector_manifest_sha256": _sha(vector_manifest_raw),
        "normalized_vector_sha256": vector_manifest["files"][
            "normalized-vectors.f64le"
        ]["sha256"],
        "canonical_input_sha256": _canonical_input_sha256(inputs),
    }
    for name, value in expected_hashes.items():
        if manifest.get(name) != value:
            raise ValueError(
                f"candidate source hash is not bound to vector artifact: {name}"
            )
    if manifest.get("vector_count") != len(evidence) or artifact.get(
        "canonical_input_ids"
    ) != sorted(evidence):
        raise ValueError("candidate input members differ from vector map")
    configuration = _expect_string(
        artifact.get("canonical_configuration_json"), "canonical configuration"
    )
    if _sha(configuration.encode("utf-8")) != manifest.get(
        "configuration_sha256"
    ) or json.loads(configuration) != manifest.get("parameters"):
        raise ValueError("candidate configuration hash or parameters are inconsistent")
    result = _expect_object(artifact.get("result"), "candidate result")
    # result_sha256 covers Rust typed-struct serialization. The CLI emits the
    # result through serde_json::Value (sorted object keys), and Python also
    # formats some floats differently. Do not pretend a Python JSON hash checks
    # that digest: the experiment must replay with its pinned candidate binary
    # and compare the complete parsed response before packaging.
    fine = _expect_object(result.get("fine_output"), "candidate fine output")
    canonical_fine = _expect_string(
        artifact.get("canonical_fine_output_json"), "canonical fine output"
    )
    if json.loads(canonical_fine) != fine or _sha(
        canonical_fine.encode("utf-8")
    ) != manifest.get("fine_output_sha256"):
        raise ValueError("candidate fine output hash is inconsistent")
    if set(fine) != {"segments", "unassigned"}:
        raise ValueError("candidate fine output has invalid partition fields")
    segments = _array(fine["segments"], "segments", nonempty=False)
    unassigned = _array(fine["unassigned"], "unassigned", nonempty=False)
    accounted = set()
    for members in [*segments, unassigned]:
        _array(members, "partition members", nonempty=False)
        for member in members:
            _expect_lower_hex(member, "partition member", 64)
            if member not in evidence or member in accounted:
                raise ValueError("candidate partition has unknown or duplicate members")
            accounted.add(member)
    if accounted != set(evidence) or any(not members for members in segments):
        raise ValueError(
            "candidate partition omits members or contains an empty segment"
        )
    packets, metadata_segments, packet_ids = [], [], set()
    for members in segments:
        members = sorted(members)
        membership_sha = _sha(_canonical(members))
        packet_id = "S" + membership_sha[:10]
        if packet_id in packet_ids:
            raise ValueError("stable segment ID collision")
        packet_ids.add(packet_id)
        instances = [evidence[member] for member in members]
        packets.append(
            {
                "packet": packet_id,
                "question": REVIEW_QUESTION,
                "verdicts": REVIEW_VERDICTS,
                "instances": instances,
            }
        )
        metadata_segments.append(
            {
                "packet": packet_id,
                "membership_sha256": membership_sha,
                "evidence_sha256": _sha(_canonical(instances)),
                "vector_ids": members,
                "member_count": len(members),
                "distinct_note_count": len({item["note_id"] for item in instances}),
            }
        )
    packets.sort(key=lambda packet: packet["packet"])
    metadata_segments.sort(key=lambda packet: packet["packet"])
    review_set = (
        "RN"
        + _sha(
            b"real-note-review-v3\0"
            + _sha(vector_manifest_raw).encode("ascii")
            + _canonical(packets)
        )[:12]
    )
    reviewer = {
        "schema_version": 3,
        "review_set": review_set,
        "instructions": REVIEW_INSTRUCTIONS,
        "packets": packets,
        "response_contract": {
            "schema_version": 3,
            "review_set": review_set,
            "judgments": "zero or one judgment for every packet",
            "judgment_fields": ["packet", "verdict", "comment"],
            "allowed_verdicts": REVIEW_VERDICTS,
        },
    }
    noise = {
        "schema_version": 1,
        "kind": "unassigned",
        "instances": [evidence[member] for member in sorted(unassigned)],
    }
    noise_lines = ["Unassigned instances (not segments)", ""]
    for item in noise["instances"]:
        raw = item["text"].encode("utf-8")
        highlighted, start = [], 0
        for left, right in item["byte_spans"]:
            highlighted.extend(
                [
                    raw[start:left].decode("utf-8"),
                    "⟦",
                    raw[left:right].decode("utf-8"),
                    "⟧",
                ]
            )
            start = right
        highlighted.append(raw[start:].decode("utf-8"))
        noise_lines.extend([item["instance"], "".join(highlighted), ""])
    metadata = {
        "schema_version": 1,
        "review_set": review_set,
        "candidate_identity": candidate_identity,
        "configuration_sha256": manifest["configuration_sha256"],
        "parameters": manifest["parameters"],
        "candidate_result_sha256": _sha(candidate_raw),
        "candidate_result_verification": {
            "result_sha256_checked": False,
            "required_external_check": (
                "Freshly replay the saved request with the pinned unchanged candidate "
                "binary and compare the full parsed response before packaging."
            ),
        },
        **expected_hashes,
        "vector_count": len(evidence),
        "segment_count": len(packets),
        "assigned_count": len(evidence) - len(unassigned),
        "unassigned_count": len(unassigned),
        "segments": metadata_segments,
        "unassigned_vector_ids": sorted(unassigned),
    }
    if cross_note is not None:
        metadata["cross_note"] = cross_note
    files = {
        "review.json": _canonical(reviewer),
        "unassigned.json": _canonical(noise),
        "unassigned.txt": ("\n".join(noise_lines) + "\n").encode("utf-8"),
        "metadata.json": _canonical(metadata),
        "candidate-response.json": candidate_raw,
    }
    files["manifest.json"] = _canonical(
        {
            "schema_version": 1,
            "review_set": review_set,
            "files": {name: _identity(raw) for name, raw in files.items()},
        }
    )
    _write_output(output, files)
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare")
    for name in ("reviewed", "encoder", "subject_package", "mask_package", "output"):
        prepare.add_argument(name, type=Path)
    finalize = commands.add_parser("finalize")
    for name in ("prepared", "worker_output", "output"):
        finalize.add_argument(name, type=Path)
    package = commands.add_parser("package-review")
    for name in ("vectors", "candidate_result", "output"):
        package.add_argument(name, type=Path)
    args = parser.parse_args()
    if args.command == "prepare":
        report = prepare_reviewed_inputs(
            args.reviewed,
            args.encoder,
            args.subject_package,
            args.mask_package,
            args.output,
        )
    elif args.command == "finalize":
        report = finalize_vectors(args.prepared, args.worker_output, args.output)
    else:
        report = package_review(args.vectors, args.candidate_result, args.output)
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
