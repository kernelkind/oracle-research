#!/usr/bin/env python3
"""Compile, freeze, execute, and analyze the controlled segmentation suite."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import itertools
import json
import math
import os
import platform
import re
import resource
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = 1
SUITE_ID = "fine-segmentation-controlled-suite-v1"
PROTOCOL_DIRECTORY = Path("docs/experiments/fine-segmentation")
PROTOCOL_FILES = (
    "README.md",
    "01-repeated-subject-recovery.md",
    "02-nearby-subject-resolution.md",
    "03-lexical-coincidence.md",
    "04-unmasked-context.md",
    "06-irrelevant-change-stability.md",
)
BLINDING_NAMESPACE_BY_INTERNAL = {
    "experiment-01": "01-repeated-subject-recovery",
    "experiment-02": "02-nearby-subject-resolution",
    "experiment-03": "03-lexical-coincidence",
    "experiment-04": "04-unmasked-context",
    "experiment-06-duplicates": "06-irrelevant-change-stability",
}


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


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _marked_text(marked: str) -> tuple[str, list[list[int]]]:
    """Remove mask delimiters and return UTF-8 byte spans in the resulting text."""

    output: list[str] = []
    spans: list[list[int]] = []
    selected_start: int | None = None
    byte_offset = 0
    for character in marked:
        if character == "⟦":
            if selected_start is not None:
                raise ValueError("nested mask delimiter")
            selected_start = byte_offset
            continue
        if character == "⟧":
            if selected_start is None or selected_start == byte_offset:
                raise ValueError("unmatched or empty mask delimiter")
            spans.append([selected_start, byte_offset])
            selected_start = None
            continue
        output.append(character)
        byte_offset += len(character.encode("utf-8"))
    if selected_start is not None or not spans:
        raise ValueError("fixture must contain a complete nonempty mask")
    return "".join(output), spans


def _encoding(
    *,
    experiment: str,
    readable_id: str,
    encoding_id: str,
    subject: str,
    marked_text: str,
    metadata: dict[str, object] | None = None,
) -> dict[str, object]:
    text, byte_spans = _marked_text(marked_text)
    return {
        "encoding_id": encoding_id,
        "experiment": experiment,
        "readable_id": readable_id,
        "subject": subject,
        "text": text,
        "byte_spans": byte_spans,
        "worker_note_id": hashlib.sha256(
            b"fine-segmentation-worker-note-v1\0" + encoding_id.encode("utf-8")
        ).hexdigest(),
        "worker_subject_id": hashlib.sha256(
            b"fine-segmentation-worker-subject-v1\0" + encoding_id.encode("utf-8")
        ).hexdigest()[:16],
        "metadata": metadata or {},
    }


def _parse_table_experiment(
    path: Path,
    *,
    experiment: str,
    heading_level: int,
) -> list[dict[str, object]]:
    encodings: list[dict[str, object]] = []
    subject_code: str | None = None
    subject_text: str | None = None
    heading = re.compile(rf"^{'#' * heading_level} `([^`]+)`: (.+)$")
    row = re.compile(r"^\| `([^`]+)` \| (⟦.*⟧) \|$")
    for line in path.read_text(encoding="utf-8").splitlines():
        if match := heading.match(line):
            subject_code, subject_text = match.groups()
            continue
        if match := row.match(line):
            if subject_code is None or subject_text is None:
                raise ValueError(f"fixture row appears before a subject in {path}")
            readable_id, marked = match.groups()
            if not readable_id.startswith(subject_code):
                raise ValueError(
                    f"fixture ID {readable_id} does not match {subject_code}"
                )
            metadata: dict[str, object] = {"subject_code": subject_code}
            if experiment == "experiment-02":
                neighborhood, subject_position, form = _experiment_02_metadata(
                    subject_code, readable_id
                )
                metadata.update(
                    {
                        "neighborhood": neighborhood,
                        "subject_position": subject_position,
                        "form": form,
                        "formulation_index": int(
                            re.search(r"(\d+)$", readable_id).group(1)
                        ),
                    }
                )
            encodings.append(
                _encoding(
                    experiment=experiment,
                    readable_id=readable_id,
                    encoding_id=f"{experiment}/{readable_id}",
                    subject=subject_text,
                    marked_text=marked,
                    metadata=metadata,
                )
            )
    return encodings


EXPERIMENT_02_NEIGHBORHOODS = {
    "coffee": ("COFFEE-R", "COFFEE-G", "COFFEE-E"),
    "photograph": ("PHOTO-C", "PHOTO-A", "PHOTO-S"),
    "rose-bush": ("ROSE-P", "ROSE-W", "ROSE-F"),
    "software": ("SOFTWARE-C", "SOFTWARE-T", "SOFTWARE-D"),
}
EXPERIMENT_02_FORMS = {
    "coffee": tuple("ABCDEFGH"),
    "photograph": tuple("CDEFGHAB"),
    "rose-bush": tuple("EFGHABCD"),
    "software": tuple("GHABCDEF"),
}


def _experiment_02_metadata(
    subject_code: str, readable_id: str
) -> tuple[str, int, str]:
    for neighborhood, subjects in EXPERIMENT_02_NEIGHBORHOODS.items():
        if subject_code in subjects:
            index = int(re.search(r"(\d+)$", readable_id).group(1))
            return (
                neighborhood,
                subjects.index(subject_code) + 1,
                EXPERIMENT_02_FORMS[neighborhood][index - 1],
            )
    raise ValueError(f"unknown Experiment 2 subject {subject_code}")


def _parse_experiment_03(path: Path) -> list[dict[str, object]]:
    encodings: list[dict[str, object]] = []
    subject: str | None = None
    position: str | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if match := re.match(r"^### `([^`]+)`$", line):
            subject = match.group(1)
            continue
        if match := re.match(r"^`([^`]+)`$", line):
            position = match.group(1)
            continue
        if match := re.match(r"^- `([BC])` (⟦.*⟧)$", line):
            if subject is None or position is None or not position.startswith(subject):
                raise ValueError(f"invalid Experiment 3 fixture position near {line}")
            version, marked = match.groups()
            trap, side = subject.split("-", 1)
            encodings.append(
                _encoding(
                    experiment="experiment-03",
                    readable_id=position,
                    encoding_id=f"experiment-03/{position}/{version}",
                    subject=subject,
                    marked_text=marked,
                    metadata={"trap": trap, "side": side, "version": version},
                )
            )
    return encodings


EXPERIMENT_04_SUBJECTS = {
    "COFFEE": "roasting green coffee beans",
    "BICYCLE": "repairing a bicycle drivetrain",
    "WATERCOLOR": "painting a watercolor landscape",
    "TELESCOPE": "aligning an equatorial telescope mount",
    "SOURDOUGH": "feeding a sourdough starter",
    "PASSPORT": "submitting passport-renewal paperwork",
}


def _parse_experiment_04(path: Path) -> list[dict[str, object]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    encodings: list[dict[str, object]] = []
    index = 0
    while index < len(lines):
        match = re.match(r"^\*\*([^*]+)\*\*$", lines[index])
        if match is None:
            index += 1
            continue
        label = match.group(1)
        readable_id, separator, form = label.partition(" · form ")
        cursor = index + 1
        while cursor < len(lines) and not lines[cursor].startswith("> "):
            if lines[cursor].startswith("**") or lines[cursor].startswith("##"):
                break
            cursor += 1
        if cursor >= len(lines) or not lines[cursor].startswith("> "):
            index += 1
            continue
        quote_lines = []
        while cursor < len(lines) and lines[cursor].startswith("> "):
            quote_lines.append(lines[cursor][2:])
            cursor += 1
        marked = " ".join(quote_lines)
        target_code = readable_id.split("-", 1)[0]
        if target_code not in EXPERIMENT_04_SUBJECTS:
            raise ValueError(f"unknown Experiment 4 target {target_code}")
        metadata: dict[str, object] = {"target_subject": target_code}
        if separator:
            context_code = readable_id.rsplit("-", 1)[1]
            if context_code not in {"TELESCOPE", "SOURDOUGH", "PASSPORT"}:
                raise ValueError(f"unknown Experiment 4 context {context_code}")
            metadata.update({"context_subject": context_code, "outer_form": form})
        else:
            metadata["anchor"] = True
        encodings.append(
            _encoding(
                experiment="experiment-04",
                readable_id=readable_id,
                encoding_id=f"experiment-04/{readable_id}",
                subject=EXPERIMENT_04_SUBJECTS[target_code],
                marked_text=marked,
                metadata=metadata,
            )
        )
        index = cursor
    return encodings


def _hmac(seed: bytes, *parts: str) -> bytes:
    message = b"\0".join(part.encode("utf-8") for part in parts)
    return hmac.new(seed, message, hashlib.sha256).digest()


def _opaque_mapping(
    encodings: list[dict[str, object]], namespace_seeds: dict[str, bytes]
) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    position_keys: dict[str, set[str]] = {
        "experiment-01": {
            str(item["readable_id"])
            for item in encodings
            if item["experiment"] == "experiment-01"
        },
        "experiment-02": {
            str(item["readable_id"])
            for item in encodings
            if item["experiment"] == "experiment-02"
        },
        "experiment-03": {
            str(item["readable_id"])
            for item in encodings
            if item["experiment"] == "experiment-03"
        },
        "experiment-04": {
            str(item["readable_id"])
            for item in encodings
            if item["experiment"] == "experiment-04"
        },
    }
    mapping: dict[str, dict[str, str]] = {}
    orders: dict[str, dict[str, str]] = {}
    for namespace, keys in sorted(position_keys.items()):
        protocol_namespace = BLINDING_NAMESPACE_BY_INTERNAL[namespace]
        seed = namespace_seeds[protocol_namespace]
        mapping[namespace] = {}
        orders[namespace] = {}
        for key in sorted(keys):
            mapping[namespace][key] = _hmac(
                seed, "fine-segmentation-id-v1", protocol_namespace, key
            ).hex()
            orders[namespace][key] = _hmac(
                seed, "fine-segmentation-order-v1", protocol_namespace, key
            ).hex()
    mapping["experiment-06-duplicates"] = {}
    orders["experiment-06-duplicates"] = {}
    protocol_namespace = BLINDING_NAMESPACE_BY_INTERNAL["experiment-06-duplicates"]
    seed = namespace_seeds[protocol_namespace]
    for ordinal in range(1, 7):
        key = f"A{ordinal}'"
        mapping["experiment-06-duplicates"][key] = _hmac(
            seed, "fine-segmentation-id-v1", protocol_namespace, key
        ).hex()
        orders["experiment-06-duplicates"][key] = _hmac(
            seed, "fine-segmentation-order-v1", protocol_namespace, key
        ).hex()
    return mapping, orders


def _ordered(
    namespace: str,
    members: Iterable[str],
    mapping: dict[str, dict[str, str]],
    orders: dict[str, dict[str, str]],
) -> tuple[list[str], list[str]]:
    values = sorted(
        set(members), key=lambda member: (orders[namespace][member], member)
    )
    return values, [mapping[namespace][member] for member in values]


def _experiment_02_members(subject_code: str, support: int, schedule: int) -> list[str]:
    for subjects in EXPERIMENT_02_NEIGHBORHOODS.values():
        if subject_code in subjects:
            phase = (0, 3, 6)[subjects.index(subject_code)]
            return [
                f"{subject_code}{((schedule - 1 + phase + offset) % 8) + 1}"
                for offset in range(support)
            ]
    raise ValueError(f"unknown Experiment 2 subject {subject_code}")


def _build_inputs(
    encodings: list[dict[str, object]],
    mapping: dict[str, dict[str, str]],
    orders: dict[str, dict[str, str]],
) -> tuple[list[dict[str, object]], dict[str, int]]:
    inputs: list[dict[str, object]] = []

    def add(
        input_id: str,
        experiment: str,
        namespace: str,
        readable_members: Iterable[str],
        encoding_ids: Iterable[str],
        metadata: dict[str, object],
    ) -> None:
        readable, opaque = _ordered(namespace, readable_members, mapping, orders)
        by_readable = dict(zip(readable_members, encoding_ids, strict=True))
        inputs.append(
            {
                "input_id": input_id,
                "experiment": experiment,
                "readable_members": readable,
                "encoding_ids": [by_readable[item] for item in readable],
                "opaque_ids": opaque,
                "metadata": metadata,
            }
        )

    experiment_01_ids = sorted(mapping["experiment-01"])
    default_members, default_opaque = _ordered(
        "experiment-01", experiment_01_ids, mapping, orders
    )
    inputs.append(
        {
            "input_id": "experiment-01/default",
            "experiment": "experiment-01",
            "readable_members": default_members,
            "encoding_ids": [f"experiment-01/{item}" for item in default_members],
            "opaque_ids": default_opaque,
            "metadata": {"order": "default"},
        }
    )
    inputs.append(
        {
            "input_id": "candidate-conformance/alternate-order",
            "experiment": "candidate-conformance",
            "readable_members": list(reversed(default_members)),
            "encoding_ids": [
                f"experiment-01/{item}" for item in reversed(default_members)
            ],
            "opaque_ids": list(reversed(default_opaque)),
            "metadata": {"order": "reverse-of-default"},
        }
    )

    exp1_subjects = {
        "A": "ORIGAMI",
        "B": "BIKE-TUBE",
        "C": "ECLIPSE",
        "D": "STARTER",
        "E": "PIANO",
        "F": "TOMATO",
    }
    aliases = {
        f"{letter}{ordinal}": f"{code}-{ordinal}"
        for letter, code in exp1_subjects.items()
        for ordinal in range(1, 7)
    }
    for input_id, selected in (
        ("experiment-06/L0", [f"{letter}{i}" for letter in "ABC" for i in range(1, 7)]),
        ("experiment-06/R0", [f"{letter}{i}" for letter in "DEF" for i in range(1, 7)]),
        (
            "experiment-06/unrelated-addition",
            [f"{letter}{i}" for letter in "ABCD" for i in range(1, 7)],
        ),
    ):
        members = [aliases[item] for item in selected]
        add(
            input_id,
            "experiment-06",
            "experiment-01",
            members,
            [f"experiment-01/{item}" for item in members],
            {"aliases": selected},
        )

    duplicate_members = [
        aliases[f"{letter}{i}"] for letter in "ABC" for i in range(1, 7)
    ]
    duplicate_pairs = [(f"A{i}'", aliases[f"A{i}"]) for i in range(1, 7)]
    combined_order = [
        (orders["experiment-01"][member], member, "experiment-01")
        for member in duplicate_members
    ] + [
        (orders["experiment-06-duplicates"][alias], alias, "experiment-06-duplicates")
        for alias, _ in duplicate_pairs
    ]
    combined_order.sort()
    readable_members = [item[1] for item in combined_order]
    opaque_ids = [mapping[item[2]][item[1]] for item in combined_order]
    duplicate_source = dict(duplicate_pairs)
    encoding_ids = [
        f"experiment-01/{duplicate_source.get(item, item)}" for item in readable_members
    ]
    inputs.append(
        {
            "input_id": "experiment-06/exact-duplicates",
            "experiment": "experiment-06",
            "readable_members": readable_members,
            "encoding_ids": encoding_ids,
            "opaque_ids": opaque_ids,
            "metadata": {"duplicate_sources": duplicate_source},
        }
    )

    exp3_positions = sorted(mapping["experiment-03"])
    exp3_traps = {
        "COACH": ("COACH-SPORTS", "COACH-VEHICLE"),
        "PITCHER": ("PITCHER-BALLGAME", "PITCHER-CONTAINER"),
        "BANK": ("BANK-FINANCIAL", "BANK-RIVER"),
    }

    def exp3_input(
        input_id: str, changed_subjects: set[str], metadata: dict[str, object]
    ) -> None:
        versions = {
            position: (
                "C"
                if any(position.startswith(subject) for subject in changed_subjects)
                else "B"
            )
            for position in exp3_positions
        }
        add(
            input_id,
            "experiment-03",
            "experiment-03",
            exp3_positions,
            [
                f"experiment-03/{position}/{versions[position]}"
                for position in exp3_positions
            ],
            {**metadata, "versions": versions},
        )

    exp3_input("experiment-03/BASELINE", set(), {"condition": "baseline"})
    for trap, (first, second) in exp3_traps.items():
        exp3_input(
            f"experiment-03/{trap}-{first.removeprefix(trap + '-')}-ONLY",
            {first},
            {"condition": "one-sided", "trap": trap, "changed_subjects": [first]},
        )
        exp3_input(
            f"experiment-03/{trap}-{second.removeprefix(trap + '-')}-ONLY",
            {second},
            {"condition": "one-sided", "trap": trap, "changed_subjects": [second]},
        )
        exp3_input(
            f"experiment-03/{trap}-BOTH",
            {first, second},
            {"condition": "both", "trap": trap, "changed_subjects": [first, second]},
        )

    exp4_ids = sorted(mapping["experiment-04"])
    exp4_anchors = [
        item for item in exp4_ids if item.endswith("CONTROL") or "-ANCHOR-" in item
    ]
    add(
        "experiment-04/anchor-only",
        "experiment-04",
        "experiment-04",
        exp4_anchors,
        [f"experiment-04/{item}" for item in exp4_anchors],
        {"condition": "anchor-only"},
    )
    for target in [item for item in exp4_ids if item not in exp4_anchors]:
        members = [*exp4_anchors, target]
        add(
            f"experiment-04/{target}",
            "experiment-04",
            "experiment-04",
            members,
            [f"experiment-04/{item}" for item in members],
            {"condition": "treatment", "mixed_target": target},
        )

    appearances = {item: 0 for item in mapping["experiment-02"]}
    condition_specs = (
        ("balanced", ((4, 4, 4),)),
        ("imbalanced", ((8, 2, 2), (2, 8, 2), (2, 2, 8))),
        (
            "singleton",
            tuple(itertools.permutations((6, 5, 1))),
        ),
        (
            "dense-singleton",
            tuple(itertools.permutations((8, 3, 1))),
        ),
    )
    for neighborhood, subjects in EXPERIMENT_02_NEIGHBORHOODS.items():
        for schedule in range(1, 9):
            for condition, allocations in condition_specs:
                for allocation_index, allocation in enumerate(allocations, start=1):
                    members = [
                        member
                        for subject, support in zip(subjects, allocation, strict=True)
                        for member in _experiment_02_members(subject, support, schedule)
                    ]
                    for member in members:
                        appearances[member] += 1
                    add(
                        (
                            f"experiment-02/{neighborhood}/s{schedule}/"
                            f"{condition}-{allocation_index}"
                        ),
                        "experiment-02",
                        "experiment-02",
                        members,
                        [f"experiment-02/{item}" for item in members],
                        {
                            "neighborhood": neighborhood,
                            "schedule": schedule,
                            "condition": condition,
                            "allocation": list(allocation),
                            "subjects": list(subjects),
                        },
                    )

    return inputs, appearances


def compile_approved_protocol(repo_root: Path | str) -> dict[str, object]:
    root = Path(repo_root).resolve()
    directory = root / PROTOCOL_DIRECTORY
    encodings = [
        *_parse_table_experiment(
            directory / "01-repeated-subject-recovery.md",
            experiment="experiment-01",
            heading_level=3,
        ),
        *_parse_table_experiment(
            directory / "02-nearby-subject-resolution.md",
            experiment="experiment-02",
            heading_level=4,
        ),
        *_parse_experiment_03(directory / "03-lexical-coincidence.md"),
        *_parse_experiment_04(directory / "04-unmasked-context.md"),
    ]
    expected_counts = {
        "experiment-01": 36,
        "experiment-02": 96,
        "experiment-03": 48,
        "experiment-04": 27,
    }
    actual_counts = {
        experiment: sum(item["experiment"] == experiment for item in encodings)
        for experiment in expected_counts
    }
    if actual_counts != expected_counts or len(encodings) != 207:
        raise ValueError(f"compiled fixture counts differ: {actual_counts}")
    encoding_ids = [str(item["encoding_id"]) for item in encodings]
    if len(set(encoding_ids)) != len(encoding_ids):
        raise ValueError("compiled fixture repeats an encoding ID")

    # The zero seed is a structural placeholder. prepare_suite replaces the
    # resulting mapping and inputs with the committed run seed.
    mapping, orders = _opaque_mapping(
        encodings,
        {namespace: bytes(32) for namespace in BLINDING_NAMESPACE_BY_INTERNAL.values()},
    )
    inputs, appearances = _build_inputs(encodings, mapping, orders)
    logical_counts = {
        name: sum(item["experiment"] == name for item in inputs)
        for name in (
            "candidate-conformance",
            "experiment-01",
            "experiment-02",
            "experiment-03",
            "experiment-04",
            "experiment-06",
        )
    }
    if len(inputs) != 538 or set(appearances.values()) != {64}:
        raise ValueError("compiled input schedule violates its frozen cardinalities")
    return {
        "schema_version": SCHEMA_VERSION,
        "suite_id": SUITE_ID,
        "encodings": encodings,
        "inputs": inputs,
        "encoding_counts": actual_counts,
        "logical_input_counts": logical_counts,
        "experiment_02_vector_appearance_counts": appearances,
    }


def _protocol_with_seed(
    repo_root: Path, namespace_seeds: dict[str, bytes], review_seed: bytes
) -> tuple[dict[str, object], dict[str, object]]:
    expected_namespaces = set(BLINDING_NAMESPACE_BY_INTERNAL.values())
    if (
        set(namespace_seeds) != expected_namespaces
        or any(len(seed) != 32 for seed in namespace_seeds.values())
        or len(review_seed) != 32
    ):
        raise ValueError("suite seeds must contain exactly 32 bytes")
    protocol = compile_approved_protocol(repo_root)
    encodings = protocol["encodings"]
    mapping, orders = _opaque_mapping(encodings, namespace_seeds)
    inputs, appearances = _build_inputs(encodings, mapping, orders)
    protocol["inputs"] = inputs
    protocol["experiment_02_vector_appearance_counts"] = appearances
    review_commitment = _sha256_bytes(
        b"fine-segmentation-exp2-review-seed-v1\0"
        b"02-nearby-subject-resolution\0" + review_seed
    )
    private = {
        "schema_version": SCHEMA_VERSION,
        "suite_id": SUITE_ID,
        "namespace_seeds": {
            namespace: seed.hex() for namespace, seed in sorted(namespace_seeds.items())
        },
        "namespace_commitments": {
            namespace: _sha256_bytes(
                b"fine-segmentation-blinding-commit-v1\0"
                + namespace.encode("utf-8")
                + b"\0"
                + seed
            )
            for namespace, seed in sorted(namespace_seeds.items())
        },
        "opaque_mapping": mapping,
        "order_keys": orders,
        "experiment_02_review": {
            "seed_hex": review_seed.hex(),
            "commitment": review_commitment,
            "packet_key_rule": "fine-segmentation-exp2-review-packet-v1",
            "member_key_rule": "fine-segmentation-exp2-review-member-v1",
            "packet_cap_per_candidate": 100,
        },
    }
    return protocol, private


def prepare_suite(
    repo_root: Path | str,
    output_path: Path | str,
    *,
    namespace_seeds: dict[str, bytes] | None = None,
    review_seed: bytes | None = None,
) -> dict[str, object]:
    root = Path(repo_root).resolve()
    output = Path(output_path).resolve()
    if output.exists():
        raise ValueError(f"prepared suite already exists: {output}")
    namespace_seeds = (
        {
            namespace: os.urandom(32)
            for namespace in BLINDING_NAMESPACE_BY_INTERNAL.values()
        }
        if namespace_seeds is None
        else namespace_seeds
    )
    review_seed = os.urandom(32) if review_seed is None else review_seed
    protocol, private = _protocol_with_seed(root, namespace_seeds, review_seed)
    protocol_bytes = _canonical_bytes(protocol)
    private_bytes = _canonical_bytes(private)
    request = {
        "schema_version": 1,
        "proposal_sha256": _sha256_bytes(protocol_bytes),
        "notes": [
            {
                "note_id": item["worker_note_id"],
                "text": item["text"],
                "subjects": [
                    {
                        "subject_id": item["worker_subject_id"],
                        "byte_spans": item["byte_spans"],
                    }
                ],
            }
            for item in protocol["encodings"]
        ],
    }
    request_bytes = _canonical_bytes(request)
    protocol_hashes = {
        name: _sha256_file(root / PROTOCOL_DIRECTORY / name) for name in PROTOCOL_FILES
    }
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "suite_id": SUITE_ID,
        "approval_date": "2026-08-31",
        "encoding_count": len(protocol["encodings"]),
        "logical_input_count": len(protocol["inputs"]),
        "fresh_invocations_per_candidate": 1076,
        "fresh_invocations_total": 2152,
        "protocol_document_sha256": protocol_hashes,
        "protocol_sha256": _sha256_bytes(protocol_bytes),
        "worker_request_sha256": _sha256_bytes(request_bytes),
        "blinding_commitments": private["namespace_commitments"],
        "experiment_02_review_commitment": private["experiment_02_review"][
            "commitment"
        ],
        "files": {
            "protocol.json": _sha256_bytes(protocol_bytes),
            "worker-request.json": _sha256_bytes(request_bytes),
        },
    }
    manifest_bytes = _canonical_bytes(manifest)

    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}.", dir=output.parent))
    try:
        _write(stage / "protocol.json", protocol_bytes)
        _write(stage / "worker-request.json", request_bytes)
        _write(stage / "blinding-private.json", private_bytes)
        _write(stage / "manifest.json", manifest_bytes)
        os.rename(stage, output)
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return verify_prepared_suite(root, output)


def verify_prepared_suite(
    repo_root: Path | str, output_path: Path | str
) -> dict[str, object]:
    root = Path(repo_root).resolve()
    output = Path(output_path).resolve()
    expected_entries = {
        "blinding-private.json",
        "manifest.json",
        "protocol.json",
        "worker-request.json",
    }
    if {item.name for item in output.iterdir()} != expected_entries:
        raise ValueError("prepared suite has unexpected entries")
    private = _read_json(output / "blinding-private.json")
    namespace_seeds = {
        namespace: bytes.fromhex(seed_hex)
        for namespace, seed_hex in private["namespace_seeds"].items()
    }
    review_seed = bytes.fromhex(private["experiment_02_review"]["seed_hex"])
    protocol, expected_private = _protocol_with_seed(root, namespace_seeds, review_seed)
    if private != expected_private:
        raise ValueError("prepared blinding data differs from replay")
    protocol_bytes = _canonical_bytes(protocol)
    if (output / "protocol.json").read_bytes() != protocol_bytes:
        raise ValueError("prepared protocol differs from replay")
    request = {
        "schema_version": 1,
        "proposal_sha256": _sha256_bytes(protocol_bytes),
        "notes": [
            {
                "note_id": item["worker_note_id"],
                "text": item["text"],
                "subjects": [
                    {
                        "subject_id": item["worker_subject_id"],
                        "byte_spans": item["byte_spans"],
                    }
                ],
            }
            for item in protocol["encodings"]
        ],
    }
    request_bytes = _canonical_bytes(request)
    if (output / "worker-request.json").read_bytes() != request_bytes:
        raise ValueError("prepared worker request differs from replay")
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "suite_id": SUITE_ID,
        "approval_date": "2026-08-31",
        "encoding_count": len(protocol["encodings"]),
        "logical_input_count": len(protocol["inputs"]),
        "fresh_invocations_per_candidate": 1076,
        "fresh_invocations_total": 2152,
        "protocol_document_sha256": {
            name: _sha256_file(root / PROTOCOL_DIRECTORY / name)
            for name in PROTOCOL_FILES
        },
        "protocol_sha256": _sha256_bytes(protocol_bytes),
        "worker_request_sha256": _sha256_bytes(request_bytes),
        "blinding_commitments": private["namespace_commitments"],
        "experiment_02_review_commitment": private["experiment_02_review"][
            "commitment"
        ],
        "files": {
            "protocol.json": _sha256_bytes(protocol_bytes),
            "worker-request.json": _sha256_bytes(request_bytes),
        },
    }
    if _read_json(output / "manifest.json") != manifest:
        raise ValueError("prepared manifest differs from replay")
    return {
        "encoding_count": len(protocol["encodings"]),
        "logical_input_count": len(protocol["inputs"]),
        "protocol_sha256": manifest["protocol_sha256"],
        "worker_request_sha256": manifest["worker_request_sha256"],
        "blinding_commitments": manifest["blinding_commitments"],
        "experiment_02_review_commitment": manifest["experiment_02_review_commitment"],
        "output_path": str(output),
    }


def _candidate_build_inputs(repo_root: Path) -> dict[str, object]:
    paths = [repo_root / "Cargo.toml", repo_root / "Cargo.lock"]
    paths.extend(
        sorted(
            (path for path in (repo_root / "src").rglob("*") if path.is_file()),
            key=lambda path: path.relative_to(repo_root).as_posix(),
        )
    )
    files = {
        path.relative_to(repo_root).as_posix(): _sha256_file(path) for path in paths
    }
    return {
        "hash_rule": "canonical-json-relative-path-to-file-sha256-v1",
        "files": files,
        "aggregate_sha256": _sha256_bytes(_canonical_bytes(files)),
    }


def _suite_implementation(repo_root: Path) -> dict[str, object]:
    relative_paths = (
        "sse_multivector/fine_segmentation_suite.py",
        "sse_multivector/fine_segmentation_encoder.py",
        "sse_multivector/fine_segmentation_candidate_runs.py",
        "sse_multivector/fine_segmentation_scoring.py",
        "sse_multivector/fine-segmentation-suite-encoder-v1.json",
    )
    files = {
        relative: _sha256_file(repo_root / relative) for relative in relative_paths
    }
    return {
        "hash_rule": "canonical-json-relative-path-to-file-sha256-v1",
        "files": files,
        "aggregate_sha256": _sha256_bytes(_canonical_bytes(files)),
    }


def _candidate_probe(candidate_executable: Path, candidate: str) -> dict[str, object]:
    inputs = []
    for ordinal, angle in enumerate((0.00, 0.01, 0.02, 0.03, 1.00, 1.01, 1.02, 1.03)):
        inputs.append(
            {
                "opaque_id": f"{ordinal + 1:064x}",
                "normalized_vector": [math.cos(angle), math.sin(angle)],
            }
        )
    request = {
        "schema_version": 1,
        "candidate": candidate,
        "source_vector_manifest_sha256": "a" * 64,
        "normalized_vector_sha256": "b" * 64,
        "inputs": inputs,
    }
    with tempfile.TemporaryDirectory(dir="/dev/shm") as directory:
        request_path = Path(directory) / "request.json"
        request_path.write_bytes(_canonical_bytes(request))
        completed = subprocess.run(
            [str(candidate_executable), str(request_path)],
            cwd=candidate_executable.parent,
            env=os.environ.copy(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    if completed.returncode != 0:
        raise ValueError(
            f"candidate probe {candidate} failed with {completed.returncode}: "
            + completed.stderr.decode("utf-8", errors="replace")
        )
    if completed.stderr:
        raise ValueError(f"candidate probe {candidate} wrote to stderr")
    try:
        response = json.loads(completed.stdout)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(
            f"candidate probe {candidate} returned invalid JSON"
        ) from error
    artifact = response.get("artifact")
    manifest = artifact.get("manifest") if isinstance(artifact, dict) else None
    configuration = (
        artifact.get("canonical_configuration_json")
        if isinstance(artifact, dict)
        else None
    )
    if (
        response.get("schema_version") != 1
        or not isinstance(response.get("candidate_identity"), str)
        or not isinstance(manifest, dict)
        or not isinstance(configuration, str)
    ):
        raise ValueError(f"candidate probe {candidate} omitted its frozen contract")
    required_manifest_fields = (
        "algorithm_version",
        "input_contract_version",
        "fine_output_selector_version",
        "adapter_implementation_source_sha256",
        "algorithm_implementation_source_sha256",
        "preprocessing_implementation_source_sha256",
        "configuration_sha256",
        "tie_rule_version",
    )
    if any(
        not isinstance(manifest.get(field), str) for field in required_manifest_fields
    ):
        raise ValueError(f"candidate probe {candidate} has an incomplete manifest")
    if manifest["configuration_sha256"] != _sha256_bytes(configuration.encode("utf-8")):
        raise ValueError(f"candidate probe {candidate} configuration hash is invalid")
    return {
        "candidate_identity": response["candidate_identity"],
        "canonical_configuration_json": configuration,
        "artifact_contract": {
            field: manifest[field] for field in required_manifest_fields
        },
    }


def _candidate_host_profile() -> dict[str, object]:
    cpu_model = ""
    cpu_features: list[str] = []
    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.exists():
        for line in cpuinfo.read_text(encoding="utf-8", errors="replace").splitlines():
            key, separator, value = line.partition(":")
            if not separator:
                continue
            if key.strip().lower() == "model name" and not cpu_model:
                cpu_model = value.strip()
            if key.strip().lower() in {"flags", "features"} and not cpu_features:
                cpu_features = sorted(value.split())
    return {
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "cpu_model": cpu_model,
        "cpu_features": cpu_features,
    }


def _candidate_resource_limits() -> dict[str, list[int]]:
    names = {
        "address_space_bytes": resource.RLIMIT_AS,
        "cpu_seconds": resource.RLIMIT_CPU,
        "file_size_bytes": resource.RLIMIT_FSIZE,
        "open_files": resource.RLIMIT_NOFILE,
        "processes": resource.RLIMIT_NPROC,
        "stack_bytes": resource.RLIMIT_STACK,
    }
    return {name: list(resource.getrlimit(limit)) for name, limit in names.items()}


def _build_technical_freeze(
    repo_root: Path,
    prepared_path: Path,
    encoder_config_path: Path,
    candidate_executable: Path,
) -> dict[str, object]:
    from sse_multivector.worker import BYTE_SPAN_RULE, TREE_HASH_RULE, canonical_tree_sha256

    prepared_report = verify_prepared_suite(repo_root, prepared_path)
    encoder_config = _read_json(encoder_config_path)
    required_encoder_fields = {
        "schema_version",
        "checkpoint_path",
        "checkpoint_sha256",
        "worker_path",
        "worker_sha256",
        "base_model_artifact_path",
        "base_model_artifact_tree_sha256",
        "container_image",
        "note_batch_size",
        "model",
    }
    if (
        not isinstance(encoder_config, dict)
        or set(encoder_config) != required_encoder_fields
    ):
        raise ValueError(
            "encoder config fields differ from the technical-freeze contract"
        )

    def resolve_config_path(value: str) -> Path:
        path = Path(value)
        return path.resolve() if path.is_absolute() else (repo_root / path).resolve()

    checkpoint_path = resolve_config_path(encoder_config["checkpoint_path"])
    worker_path = resolve_config_path(encoder_config["worker_path"])
    model_path = resolve_config_path(encoder_config["base_model_artifact_path"])
    if _sha256_file(checkpoint_path) != encoder_config["checkpoint_sha256"]:
        raise ValueError("encoder checkpoint differs from its declared hash")
    if _sha256_file(worker_path) != encoder_config["worker_sha256"]:
        raise ValueError("encoder worker differs from its declared hash")
    if (
        canonical_tree_sha256(model_path)
        != encoder_config["base_model_artifact_tree_sha256"]
    ):
        raise ValueError("encoder model tree differs from its declared hash")
    if not re.fullmatch(
        r"(?:[^@]+@)?sha256:[0-9a-f]{64}", encoder_config["container_image"]
    ):
        raise ValueError("encoder container image is not an immutable SHA-256 identity")
    model = encoder_config["model"]
    expected_model = {
        "base_model": "sentence-transformers/sentence-t5-base",
        "dimensions": 768,
        "maximum_tokens": 512,
        "pooling": "selected-contextual-token-mean-linear-relu-linear-v1",
    }
    if model != expected_model:
        raise ValueError(
            "encoder model descriptor differs from the approved SSE boundary"
        )

    executable = candidate_executable.resolve()
    if not executable.is_file() or not os.access(executable, os.X_OK):
        raise ValueError("candidate executable is missing or not executable")
    candidates = {
        candidate: _candidate_probe(executable, candidate)
        for candidate in ("hdbscan", "snn")
    }
    expected_identities = {
        "hdbscan": "hdbscan-controlled-suite-config-v1",
        "snn": "snn-controlled-suite-config-v1",
    }
    if {
        name: value["candidate_identity"] for name, value in candidates.items()
    } != expected_identities:
        raise ValueError(
            "candidate executable returned an unexpected candidate identity"
        )

    prepared_manifest = _read_json(prepared_path / "manifest.json")
    return {
        "schema_version": SCHEMA_VERSION,
        "suite_id": SUITE_ID,
        "prepared_manifest_sha256": _sha256_file(prepared_path / "manifest.json"),
        "protocol_sha256": prepared_report["protocol_sha256"],
        "worker_request_sha256": prepared_report["worker_request_sha256"],
        "encoding_count": prepared_report["encoding_count"],
        "logical_input_count": prepared_report["logical_input_count"],
        "invocations_per_candidate": prepared_manifest[
            "fresh_invocations_per_candidate"
        ],
        "blinding_commitments": prepared_report["blinding_commitments"],
        "experiment_02_review_commitment": prepared_report[
            "experiment_02_review_commitment"
        ],
        "encoder": {
            "request_sha256": prepared_report["worker_request_sha256"],
            "checkpoint_path": str(checkpoint_path),
            "checkpoint_sha256": encoder_config["checkpoint_sha256"],
            "worker_path": str(worker_path),
            "worker_sha256": encoder_config["worker_sha256"],
            "base_model_artifact_path": str(model_path),
            "base_model_artifact_tree_sha256": encoder_config[
                "base_model_artifact_tree_sha256"
            ],
            "tree_hash_rule": TREE_HASH_RULE,
            "container_image": encoder_config["container_image"],
            "note_batch_size": encoder_config["note_batch_size"],
            "model": model,
            "dimensions": 768,
            "vector_format": "row-major-f32le-v1",
            "byte_span_rule": BYTE_SPAN_RULE,
        },
        "candidate_execution": {
            "executable_path": str(executable),
            "executable_sha256": _sha256_file(executable),
            "working_directory": str(repo_root),
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
            "isolation": ("fresh-process-empty-environment-no-shared-mutable-state-v1"),
            "resource_limits": _candidate_resource_limits(),
            "host": _candidate_host_profile(),
        },
        "candidate_build_inputs": _candidate_build_inputs(repo_root),
        "suite_implementation": _suite_implementation(repo_root),
        "candidates": candidates,
    }


def freeze_suite(
    repo_root: Path | str,
    prepared_path: Path | str,
    encoder_config_path: Path | str,
    candidate_executable: Path | str,
    output_path: Path | str,
) -> dict[str, object]:
    root = Path(repo_root).resolve()
    prepared = Path(prepared_path).resolve()
    encoder_config = Path(encoder_config_path).resolve()
    executable = Path(candidate_executable).resolve()
    output = Path(output_path).resolve()
    if output.exists():
        raise ValueError(f"technical freeze already exists: {output}")
    freeze = _build_technical_freeze(root, prepared, encoder_config, executable)
    output.parent.mkdir(parents=True, exist_ok=True)
    _write_json(output, freeze)
    return verify_technical_freeze(root, prepared, output)


def verify_technical_freeze(
    repo_root: Path | str,
    prepared_path: Path | str,
    output_path: Path | str,
) -> dict[str, object]:
    root = Path(repo_root).resolve()
    prepared = Path(prepared_path).resolve()
    output = Path(output_path).resolve()
    frozen = _read_json(output)
    encoder = frozen.get("encoder", {})
    config = {
        "schema_version": 1,
        "checkpoint_path": encoder.get("checkpoint_path"),
        "checkpoint_sha256": encoder.get("checkpoint_sha256"),
        "worker_path": encoder.get("worker_path"),
        "worker_sha256": encoder.get("worker_sha256"),
        "base_model_artifact_path": encoder.get("base_model_artifact_path"),
        "base_model_artifact_tree_sha256": encoder.get(
            "base_model_artifact_tree_sha256"
        ),
        "container_image": encoder.get("container_image"),
        "note_batch_size": encoder.get("note_batch_size"),
        "model": encoder.get("model"),
    }
    with tempfile.TemporaryDirectory(dir="/dev/shm") as directory:
        config_path = Path(directory) / "encoder.json"
        config_path.write_bytes(_canonical_bytes(config))
        expected = _build_technical_freeze(
            root,
            prepared,
            config_path,
            Path(frozen.get("candidate_execution", {}).get("executable_path", "")),
        )
    if frozen != expected:
        raise ValueError("technical freeze differs from replay")
    return {
        "encoding_count": frozen["encoding_count"],
        "logical_input_count": frozen["logical_input_count"],
        "candidate_count": len(frozen["candidates"]),
        "invocations_per_candidate": frozen["invocations_per_candidate"],
        "technical_freeze_sha256": _sha256_file(output),
        "output_path": str(output),
    }


def _build_vector_artifact(
    prepared_path: Path, technical_freeze_path: Path, worker_output_path: Path
) -> tuple[dict[str, object], bytes, bytes, bytes, bytes]:
    protocol = _read_json(prepared_path / "protocol.json")
    request = _read_json(prepared_path / "worker-request.json")
    freeze = _read_json(technical_freeze_path)
    receipt_path = worker_output_path / "worker-receipt.json"
    raw_path = worker_output_path / "raw-vectors.f32le"
    receipt = _read_json(receipt_path)
    raw = raw_path.read_bytes()
    encoder = freeze.get("encoder")
    if not isinstance(encoder, dict):
        raise ValueError("technical freeze is missing its encoder identity")
    required_identity = {
        "request_sha256": _sha256_file(prepared_path / "worker-request.json"),
        "checkpoint_sha256": receipt.get("checkpoint_sha256"),
        "base_model_artifact_tree_sha256": receipt.get(
            "base_model_artifact_tree_sha256"
        ),
        "worker_sha256": receipt.get("runtime", {}).get("worker_sha256"),
        "container_image": receipt.get("container_image"),
        "dimensions": receipt.get("dimensions"),
        "vector_format": receipt.get("vector_format"),
    }
    for name, actual in required_identity.items():
        if encoder.get(name) != actual:
            raise ValueError(f"worker receipt differs from frozen encoder field {name}")
    if receipt.get("request_sha256") != encoder["request_sha256"]:
        raise ValueError("worker receipt is not bound to the frozen request")
    if receipt.get("proposal_sha256") != request.get("proposal_sha256"):
        raise ValueError("worker receipt is not bound to the compiled protocol")
    encodings = protocol.get("encodings")
    rows = receipt.get("rows")
    dimensions = encoder.get("dimensions")
    if (
        not isinstance(encodings, list)
        or not isinstance(rows, list)
        or len(encodings) != 207
        or len(rows) != len(encodings)
        or receipt.get("row_count") != len(encodings)
        or dimensions != 768
    ):
        raise ValueError(
            "worker output violates the frozen 207-row, 768-dimension shape"
        )
    if len(raw) != len(encodings) * dimensions * 4:
        raise ValueError("worker raw vector byte count is inconsistent")
    file_identity = receipt.get("files", {}).get("raw-vectors.f32le", {})
    if file_identity != {"bytes": len(raw), "sha256": _sha256_bytes(raw)}:
        raise ValueError("worker raw vector identity is invalid")

    normalized = bytearray()
    vector_map = []
    norms = []
    for ordinal, (encoding, row) in enumerate(zip(encodings, rows, strict=True)):
        if (
            row.get("ordinal") != ordinal
            or row.get("note_id") != encoding.get("worker_note_id")
            or row.get("subject_id") != encoding.get("worker_subject_id")
        ):
            raise ValueError(f"worker row {ordinal} differs from the compiled fixture")
        selected_token_indices = row.get("selected_token_indices")
        selected_token_ids = row.get("selected_token_ids")
        token_count = row.get("token_count")
        if (
            not isinstance(selected_token_indices, list)
            or not selected_token_indices
            or any(type(index) is not int for index in selected_token_indices)
            or selected_token_indices != sorted(set(selected_token_indices))
            or not isinstance(selected_token_ids, list)
            or len(selected_token_ids) != len(selected_token_indices)
            or any(
                type(token_id) is not int or token_id < 0
                for token_id in selected_token_ids
            )
            or type(token_count) is not int
            or token_count < 1
            or any(
                index < 0 or index >= token_count for index in selected_token_indices
            )
        ):
            raise ValueError(
                f"worker row {ordinal} has invalid selected-token evidence"
            )
        values = struct.unpack_from(f"<{dimensions}f", raw, ordinal * dimensions * 4)
        norm = math.sqrt(sum(float(value) * float(value) for value in values))
        if not math.isfinite(norm) or norm == 0.0:
            raise ValueError(f"worker row {ordinal} has an invalid norm")
        normalized_values = tuple(float(value) / norm for value in values)
        normalized.extend(struct.pack(f"<{dimensions}d", *normalized_values))
        normalized_norm = math.sqrt(sum(value * value for value in normalized_values))
        norms.append(normalized_norm)
        vector_map.append(
            {
                "ordinal": ordinal,
                "encoding_id": encoding["encoding_id"],
                "experiment": encoding["experiment"],
                "readable_id": encoding["readable_id"],
                "subject": encoding["subject"],
                "worker_note_id": encoding["worker_note_id"],
                "worker_subject_id": encoding["worker_subject_id"],
                "byte_spans": encoding["byte_spans"],
                "selected_token_indices": selected_token_indices,
                "selected_token_ids": selected_token_ids,
                "token_count": token_count,
                "metadata": encoding["metadata"],
            }
        )
    vector_map_value = {
        "schema_version": SCHEMA_VERSION,
        "suite_id": SUITE_ID,
        "vector_count": len(encodings),
        "dimensions": dimensions,
        "vectors": vector_map,
    }
    vector_map_bytes = _canonical_bytes(vector_map_value)
    receipt_bytes = (worker_output_path / "worker-receipt.json").read_bytes()
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "suite_id": SUITE_ID,
        "vector_count": len(encodings),
        "dimensions": dimensions,
        "raw_decode_and_normalization_contract": (
            "row-major-f32le-to-exact-f64-l2-normalized-f64le-v1"
        ),
        "minimum_normalized_norm": min(norms),
        "maximum_normalized_norm": max(norms),
        "sources": {
            "prepared_manifest_sha256": _sha256_file(prepared_path / "manifest.json"),
            "technical_freeze_sha256": _sha256_file(technical_freeze_path),
            "worker_receipt_sha256": _sha256_bytes(receipt_bytes),
        },
        "files": {
            "raw-vectors.f32le": {
                "bytes": len(raw),
                "sha256": _sha256_bytes(raw),
            },
            "normalized-vectors.f64le": {
                "bytes": len(normalized),
                "sha256": _sha256_bytes(normalized),
            },
            "vector-map.json": {
                "bytes": len(vector_map_bytes),
                "sha256": _sha256_bytes(vector_map_bytes),
            },
            "worker-receipt.json": {
                "bytes": len(receipt_bytes),
                "sha256": _sha256_bytes(receipt_bytes),
            },
        },
    }
    return manifest, raw, bytes(normalized), vector_map_bytes, receipt_bytes


def finalize_vector_artifact(
    prepared_path: Path | str,
    technical_freeze_path: Path | str,
    worker_output_path: Path | str,
    output_path: Path | str,
) -> dict[str, object]:
    prepared = Path(prepared_path).resolve()
    freeze = Path(technical_freeze_path).resolve()
    worker = Path(worker_output_path).resolve()
    output = Path(output_path).resolve()
    if output.exists():
        raise ValueError(f"vector artifact already exists: {output}")
    manifest, raw, normalized, vector_map, receipt = _build_vector_artifact(
        prepared, freeze, worker
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}.", dir=output.parent))
    try:
        _write(stage / "raw-vectors.f32le", raw)
        _write(stage / "normalized-vectors.f64le", normalized)
        _write(stage / "vector-map.json", vector_map)
        _write(stage / "worker-receipt.json", receipt)
        _write_json(stage / "manifest.json", manifest)
        os.rename(stage, output)
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return verify_vector_artifact(prepared, freeze, worker, output)


def verify_vector_artifact(
    prepared_path: Path | str,
    technical_freeze_path: Path | str,
    worker_output_path: Path | str,
    output_path: Path | str,
) -> dict[str, object]:
    prepared = Path(prepared_path).resolve()
    freeze = Path(technical_freeze_path).resolve()
    worker = Path(worker_output_path).resolve()
    output = Path(output_path).resolve()
    expected_files = {
        "manifest.json",
        "normalized-vectors.f64le",
        "raw-vectors.f32le",
        "vector-map.json",
        "worker-receipt.json",
    }
    if {entry.name for entry in output.iterdir()} != expected_files:
        raise ValueError("vector artifact has unexpected entries")
    manifest, raw, normalized, vector_map, receipt = _build_vector_artifact(
        prepared, freeze, worker
    )
    expected = {
        "manifest.json": _canonical_bytes(manifest),
        "raw-vectors.f32le": raw,
        "normalized-vectors.f64le": normalized,
        "vector-map.json": vector_map,
        "worker-receipt.json": receipt,
    }
    for name, value in expected.items():
        if (output / name).read_bytes() != value:
            raise ValueError(f"vector artifact file {name} differs from replay")
    return {
        "vector_count": manifest["vector_count"],
        "dimensions": manifest["dimensions"],
        "raw_vector_bytes": len(raw),
        "minimum_normalized_norm": manifest["minimum_normalized_norm"],
        "maximum_normalized_norm": manifest["maximum_normalized_norm"],
        "manifest_sha256": _sha256_file(output / "manifest.json"),
        "normalized_vector_sha256": manifest["files"]["normalized-vectors.f64le"][
            "sha256"
        ],
        "output_path": str(output),
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare = subparsers.add_parser("prepare")
    prepare.add_argument("repo_root", type=Path)
    prepare.add_argument("output", type=Path)
    verify = subparsers.add_parser("verify-prepared")
    verify.add_argument("repo_root", type=Path)
    verify.add_argument("output", type=Path)
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.command == "prepare":
        report = prepare_suite(args.repo_root, args.output)
    else:
        report = verify_prepared_suite(args.repo_root, args.output)
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
