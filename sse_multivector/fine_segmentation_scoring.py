#!/usr/bin/env python3
"""Score controlled fine-segmentation outputs and prepare blinded review packets.

This module is intentionally separate from candidate execution.  It receives
immutable outputs, restores the approved fixture identities, applies the
predeclared rules, and creates review artifacts.  It never supplies a human
semantic judgment or chooses a candidate.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import math
import os
import shutil
import statistics
import struct
import tempfile
import argparse
import copy
from collections import Counter
from pathlib import Path
from typing import Iterable, Mapping, Sequence


SCHEMA_VERSION = 1
REVIEW_CAPACITY = 100
REVIEW_SEED_DOMAIN = b"fine-segmentation-exp2-review-seed-v1\0"
REVIEW_EXPERIMENT_DOMAIN = b"02-nearby-subject-resolution\0"
REVIEW_PACKET_DOMAIN = b"fine-segmentation-exp2-review-packet-v1\0"
REVIEW_MEMBER_DOMAIN = b"fine-segmentation-exp2-review-member-v1\0"


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _canonical_member_set(members: Iterable[str]) -> tuple[str, ...]:
    canonical = tuple(sorted(set(members)))
    if not canonical:
        raise ValueError("a segment must contain at least one member")
    return canonical


def load_verified_candidate_outputs(
    protocol: Mapping[str, object],
    candidate_run_path: Path | str,
    candidate: str,
) -> dict[str, dict[str, object]]:
    """Read one candidate from the replay-verified runner artifact.

    Callers must first run ``verify_candidate_suite_runs`` against the same
    directory and frozen inputs.  This parser then checks the runner's retained
    schema, binds every logical input to exactly two records, and restores the
    readable fixture IDs for semantic scoring.
    """

    root = Path(candidate_run_path).resolve()
    completion = json.loads((root / "completion.json").read_text(encoding="utf-8"))
    if (
        completion.get("complete") is not True
        or completion.get("repetitions_per_input") != 2
    ):
        raise ValueError("candidate-run artifact is not complete")
    specifications = protocol.get("inputs")
    if not isinstance(specifications, list):
        raise ValueError("compiled protocol is missing logical inputs")
    by_id = {str(item["input_id"]): item for item in specifications}
    if len(by_id) != len(specifications):
        raise ValueError("compiled protocol repeats a logical input ID")

    records: dict[str, list[tuple[dict[str, object], dict[str, object] | None]]] = {
        input_id: [] for input_id in by_id
    }
    identities = set()
    for directory in (root / "runs").iterdir():
        if not directory.is_dir():
            continue
        record = json.loads((directory / "record.json").read_text(encoding="utf-8"))
        if record.get("candidate") != candidate:
            continue
        input_id = record.get("input_id")
        if input_id not in records:
            raise ValueError(f"runner record names unknown input {input_id}")
        if directory.name != record.get("run_id"):
            raise ValueError("runner directory and record IDs differ")
        fine_output_path = directory / "fine-output.json"
        fine_output = (
            json.loads(fine_output_path.read_text(encoding="utf-8"))
            if fine_output_path.is_file()
            else None
        )
        records[str(input_id)].append((record, fine_output))
        identities.add(record.get("candidate_identity"))
    expected_count = len(specifications) * 2
    if completion.get("candidate_counts", {}).get(candidate) != expected_count:
        raise ValueError("runner completion count differs from the protocol")
    if len(identities) != 1 or None in identities:
        raise ValueError("runner records do not have one candidate identity")

    outputs: dict[str, dict[str, object]] = {}
    for input_id, pairs in records.items():
        if len(pairs) != 2 or {pair[0].get("repetition") for pair in pairs} != {1, 2}:
            raise ValueError(f"input {input_id} does not have exactly two repetitions")
        pairs.sort(key=lambda pair: int(pair[0]["repetition"]))
        invocation_summaries = [
            {
                "run_id": str(pair[0]["run_id"]),
                "repetition": pair[0].get("repetition"),
                "status": pair[0].get("status", "valid"),
                "integrity_error": pair[0].get("integrity_error"),
                "fine_output_sha256": pair[0].get("fine_output_sha256"),
                "execution_profile": pair[0].get("execution_profile"),
                "execution_profile_sha256": pair[0].get("execution_profile_sha256"),
                "actual_argv": pair[0].get("actual_argv"),
                "files": pair[0].get("files"),
                "return_code": pair[0].get("return_code"),
            }
            for pair in pairs
        ]
        invalid = [
            pair[0] for pair in pairs if pair[0].get("status", "valid") != "valid"
        ]
        if invalid:
            outputs[input_id] = {
                "eligible": False,
                "integrity_failure": "; ".join(
                    sorted(
                        {
                            str(
                                record.get("integrity_error")
                                or "unspecified integrity failure"
                            )
                            for record in invalid
                        }
                    )
                ),
                "segments": [],
                "unassigned": [],
                "canonical_output_sha256": None,
                "invocation_record_ids": [str(pair[0]["run_id"]) for pair in pairs],
                "invocations": invocation_summaries,
                "candidate_identity": next(iter(identities)),
                "experiment": by_id[input_id].get("experiment"),
                "input_member_order": list(by_id[input_id].get("readable_members", [])),
            }
            continue
        fine_outputs = []
        fine_hashes = []
        for record, fine in pairs:
            if fine is None or not isinstance(fine, dict):
                raise ValueError("valid runner record is missing fine-output.json")
            fine_outputs.append(fine)
            fine_hashes.append(record.get("fine_output_sha256"))
        if fine_outputs[0] != fine_outputs[1] or fine_hashes[0] != fine_hashes[1]:
            outputs[input_id] = {
                "eligible": False,
                "integrity_failure": "repeatability failure",
                "segments": [],
                "unassigned": [],
                "canonical_output_sha256": None,
                "invocation_record_ids": [str(pair[0]["run_id"]) for pair in pairs],
                "invocations": invocation_summaries,
                "candidate_identity": next(iter(identities)),
                "experiment": by_id[input_id].get("experiment"),
                "input_member_order": list(by_id[input_id].get("readable_members", [])),
            }
            continue

        specification = by_id[input_id]
        readable = specification.get("readable_members")
        opaque = specification.get("opaque_ids")
        if (
            not isinstance(readable, list)
            or not isinstance(opaque, list)
            or len(readable) != len(opaque)
            or len(set(opaque)) != len(opaque)
        ):
            raise ValueError(
                f"protocol input {input_id} has an invalid identity mapping"
            )
        reveal = dict(zip(opaque, readable, strict=True))
        try:
            segments = [
                [str(reveal[opaque_id]) for opaque_id in segment]
                for segment in fine_outputs[0]["segments"]
            ]
            unassigned = [
                str(reveal[opaque_id]) for opaque_id in fine_outputs[0]["unassigned"]
            ]
        except KeyError as error:
            raise ValueError(
                f"input {input_id} output contains an unknown opaque ID"
            ) from error
        outputs[input_id] = {
            "eligible": True,
            "integrity_failure": None,
            "segments": segments,
            "unassigned": unassigned,
            "canonical_output_sha256": fine_hashes[0],
            "invocation_record_ids": [str(pair[0]["run_id"]) for pair in pairs],
            "invocations": invocation_summaries,
            "candidate_identity": next(iter(identities)),
            "experiment": specification.get("experiment"),
            "input_member_order": list(readable),
        }
    return outputs


def score_experiment_01(
    segments: Iterable[Iterable[str]],
    cohorts: Mapping[str, set[str]],
) -> dict[str, object]:
    """Apply Experiment 1's exact recovery-and-purity rule."""

    canonical_segments = sorted(
        {_canonical_member_set(segment) for segment in segments}
    )
    expected = {name: tuple(sorted(members)) for name, members in cohorts.items()}
    expected_sets = [set(members) for members in expected.values()]
    recovered = {
        name: members in canonical_segments
        for name, members in sorted(expected.items())
    }
    mixed = [
        list(segment)
        for segment in canonical_segments
        if len(segment) >= 2
        and not any(set(segment).issubset(subject) for subject in expected_sets)
    ]
    passed = all(recovered.values()) and not mixed
    return {
        "verdict": "pass" if passed else "recovery_failure",
        "expected_cohort_recovery": recovered,
        "mixed_segments": mixed,
        "segments": [list(segment) for segment in canonical_segments],
    }


def review_seed_commitment(review_seed: bytes) -> str:
    if len(review_seed) != 32:
        raise ValueError("Experiment 2 review seed must contain exactly 32 bytes")
    return hashlib.sha256(
        REVIEW_SEED_DOMAIN + REVIEW_EXPERIMENT_DOMAIN + review_seed
    ).hexdigest()


def _mask_fragments(encoding: Mapping[str, object]) -> list[str]:
    text = encoding.get("text")
    spans = encoding.get("byte_spans")
    if not isinstance(text, str) or not isinstance(spans, list) or not spans:
        raise ValueError("review member is missing its frozen text or mask spans")
    encoded = text.encode("utf-8")
    fragments: list[str] = []
    previous_end = -1
    for span in spans:
        if (
            not isinstance(span, list)
            or len(span) != 2
            or not all(isinstance(value, int) for value in span)
        ):
            raise ValueError("review member contains an invalid byte span")
        start, end = span
        if start < 0 or start >= end or end > len(encoded) or start < previous_end:
            raise ValueError("review member contains an invalid byte-span range")
        try:
            fragment = encoded[start:end].decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError(
                "review mask does not align to UTF-8 boundaries"
            ) from error
        fragments.append(fragment)
        previous_end = end
    return fragments


def build_experiment_02_review(
    occurrences: Sequence[Mapping[str, object]],
    encodings: Mapping[str, Mapping[str, object]],
    *,
    review_seed: bytes,
) -> dict[str, object]:
    """Build the complete deduplicated Experiment 2 semantic-review pool.

    The reviewer-facing packets contain only complete masks under neutral
    labels.  The internal packet records retain the configuration and support
    provenance required by the coverage manifest.
    """

    commitment = review_seed_commitment(review_seed)
    grouped: dict[tuple[str, ...], list[Mapping[str, object]]] = {}
    readable_by_opaque_set: dict[tuple[str, ...], dict[str, str]] = {}
    for occurrence in occurrences:
        opaque = _canonical_member_set(occurrence.get("opaque_members", []))
        readable = occurrence.get("readable_members")
        if not isinstance(readable, list) or len(readable) != len(opaque):
            raise ValueError("review occurrence has inconsistent member identities")
        opaque_input = occurrence.get("opaque_members")
        if not isinstance(opaque_input, list):
            raise ValueError("review occurrence is missing opaque members")
        pair_map = dict(zip(opaque_input, readable, strict=True))
        if set(pair_map) != set(opaque):
            raise ValueError("review occurrence repeats an opaque member")
        normalized_map = {member: str(pair_map[member]) for member in opaque}
        existing = readable_by_opaque_set.setdefault(opaque, normalized_map)
        if existing != normalized_map:
            raise ValueError("one opaque member set maps to conflicting fixtures")
        grouped.setdefault(opaque, []).append(occurrence)

    ordered_groups = []
    for opaque_members, packet_occurrences in grouped.items():
        member_set_bytes = _canonical_json(list(opaque_members))
        packet_key = hmac.new(
            review_seed,
            REVIEW_PACKET_DOMAIN + REVIEW_EXPERIMENT_DOMAIN + member_set_bytes,
            hashlib.sha256,
        ).digest()
        ordered_groups.append(
            (packet_key, member_set_bytes, opaque_members, packet_occurrences)
        )
    ordered_groups.sort(key=lambda item: (item[0], item[1]))

    reviewer_packets: list[dict[str, object]] = []
    internal_packets: list[dict[str, object]] = []
    for ordinal, (_, member_set_bytes, opaque_members, packet_occurrences) in enumerate(
        ordered_groups, start=1
    ):
        packet_id = f"P{ordinal:03d}"
        readable_map = readable_by_opaque_set[opaque_members]
        member_rows = []
        for opaque_id in opaque_members:
            member_key = hmac.new(
                review_seed,
                REVIEW_MEMBER_DOMAIN
                + REVIEW_EXPERIMENT_DOMAIN
                + member_set_bytes
                + b"\0"
                + bytes.fromhex(opaque_id),
                hashlib.sha256,
            ).digest()
            member_rows.append((member_key, bytes.fromhex(opaque_id), opaque_id))
        member_rows.sort(key=lambda item: (item[0], item[1]))

        instances = []
        internal_members = []
        for member_ordinal, (_, _, opaque_id) in enumerate(member_rows, start=1):
            readable_id = readable_map[opaque_id]
            if readable_id not in encodings:
                raise ValueError(f"review member {readable_id} has no fixture encoding")
            fragments = _mask_fragments(encodings[readable_id])
            instances.append(
                {
                    "instance": f"I{member_ordinal:02d}",
                    "fragments": fragments,
                }
            )
            internal_members.append(
                {
                    "instance": f"I{member_ordinal:02d}",
                    "opaque_id": opaque_id,
                    "readable_id": readable_id,
                    "fragments": fragments,
                }
            )
        reviewer_packets.append(
            {
                "packet": packet_id,
                "question": (
                    "Are all instances recognizable as refinements of one fine subject?"
                ),
                "verdicts": ["valid", "invalid", "uncertain"],
                "instances": instances,
            }
        )
        internal_packets.append(
            {
                "packet": packet_id,
                "canonical_opaque_members": list(opaque_members),
                "members": internal_members,
                "occurrences": [
                    {
                        key: copy.deepcopy(value)
                        for key, value in item.items()
                        if key != "review"
                    }
                    for item in packet_occurrences
                ],
                "review_state": "pending",
            }
        )

    count = len(internal_packets)
    if count > REVIEW_CAPACITY:
        status = "review_capacity_failure"
        reviewer_packets = []
        for packet in internal_packets:
            packet["review_state"] = "unavailable"
        unavailable_reason = (
            f"complete pool contains {count} unique packets, exceeding the "
            f"frozen cap of {REVIEW_CAPACITY}; no subset was sampled"
        )
    else:
        status = "pending_review"
        unavailable_reason = None
    return {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "review_seed_commitment": commitment,
        "packet_cap": REVIEW_CAPACITY,
        "unique_packet_count": count,
        "unavailable_reason": unavailable_reason,
        "reviewer_packets": reviewer_packets,
        "internal_packets": internal_packets,
    }


def validate_semantic_review_response(
    review: Mapping[str, object],
    review_set: str,
    response: Mapping[str, object],
) -> dict[str, dict[str, object]]:
    """Validate one complete primary-review response without inventing judgments."""

    if review.get("status") != "pending_review":
        raise ValueError("semantic review is not available for this candidate")
    packets = review.get("internal_packets")
    if not isinstance(packets, list):
        raise ValueError("semantic review is missing its internal packets")
    return _validate_packet_judgments(packets, review_set, response)


def _validate_packet_judgments(
    packets: Sequence[Mapping[str, object]],
    review_set: str,
    response: Mapping[str, object],
) -> dict[str, dict[str, object]]:
    """Validate exactly one semantic judgment for every named packet."""

    if set(response) != {"schema_version", "review_set", "judgments"}:
        raise ValueError("semantic-review response has the wrong top-level schema")
    if response.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("semantic-review response has the wrong schema version")
    if response.get("review_set") != review_set:
        raise ValueError("semantic-review response names the wrong review set")
    judgments = response.get("judgments")
    if not isinstance(judgments, list):
        raise ValueError("semantic-review response is missing packets or judgments")
    expected = {str(packet.get("packet")) for packet in packets}
    if None in expected or "None" in expected or len(expected) != len(packets):
        raise ValueError("semantic-review packet identities are invalid")
    by_packet: dict[str, dict[str, object]] = {}
    for judgment in judgments:
        if not isinstance(judgment, dict):
            raise ValueError("semantic-review judgment is not an object")
        if set(judgment) != {"packet", "verdict", "fine_subject"}:
            raise ValueError("semantic-review judgment has unexpected fields")
        packet = judgment.get("packet")
        verdict = judgment.get("verdict")
        fine_subject = judgment.get("fine_subject")
        if not isinstance(packet, str) or packet in by_packet:
            raise ValueError("semantic-review response repeats a packet")
        if verdict not in {"valid", "invalid", "uncertain"}:
            raise ValueError("semantic-review verdict is invalid")
        if verdict == "valid":
            if not isinstance(fine_subject, str) or not fine_subject.strip():
                raise ValueError("a valid packet requires one fine subject")
        elif fine_subject is not None:
            raise ValueError("only a valid packet may record a fine subject")
        by_packet[packet] = dict(judgment)
    if set(by_packet) != expected:
        raise ValueError(
            "semantic-review response does not cover every packet exactly once"
        )
    return by_packet


def _reconstruct_experiment_02_machine_outcomes(
    configurations: Sequence[Mapping[str, object]],
    *,
    frozen_inputs: Sequence[Mapping[str, object]],
    frozen_encodings: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    """Rebuild every machine-derived Experiment 2 field from frozen inputs."""

    input_by_id = {str(item.get("input_id")): item for item in frozen_inputs}
    if len(input_by_id) != len(frozen_inputs) or "None" in input_by_id:
        raise ValueError("frozen Experiment 2 inputs repeat or omit an input ID")
    configuration_by_id = {
        str(item.get("configuration_id")): item for item in configurations
    }
    if len(configuration_by_id) != len(configurations) or "None" in configuration_by_id:
        raise ValueError("Experiment 2 configurations repeat or omit an input ID")
    if set(configuration_by_id) != set(input_by_id):
        raise ValueError("configuration coverage differs from the frozen schedule")

    outputs: dict[str, dict[str, object]] = {}
    for input_id, specification in input_by_id.items():
        readable = specification.get("readable_members")
        opaque = specification.get("opaque_ids")
        metadata = specification.get("metadata")
        if (
            not isinstance(readable, list)
            or not isinstance(opaque, list)
            or len(readable) != len(opaque)
            or len(set(readable)) != len(readable)
            or len(set(opaque)) != len(opaque)
            or not isinstance(metadata, dict)
            or not isinstance(metadata.get("subjects"), list)
        ):
            raise ValueError("frozen Experiment 2 input mapping is invalid")
        for member in readable:
            encoding = frozen_encodings.get(str(member))
            if not isinstance(encoding, Mapping) or not isinstance(
                encoding.get("metadata"), Mapping
            ):
                raise ValueError("frozen Experiment 2 encoding mapping is incomplete")
            if encoding["metadata"].get("subject_code") not in metadata["subjects"]:
                raise ValueError(
                    "frozen Experiment 2 encoding names an unknown subject"
                )

        configuration = configuration_by_id[input_id]
        invocations = configuration.get("invocations")
        invocation_ids = configuration.get("invocation_record_ids")
        if not isinstance(invocations, list) or len(invocations) != 2:
            raise ValueError(
                "each configuration must retain two complete invocation records"
            )
        if (
            not isinstance(invocation_ids, list)
            or len(invocation_ids) != 2
            or {row.get("run_id") for row in invocations} != set(invocation_ids)
            or {row.get("repetition") for row in invocations} != {1, 2}
        ):
            raise ValueError("configuration invocation bindings are inconsistent")
        for invocation in invocations:
            status = invocation.get("status")
            files = invocation.get("files")
            if (
                status not in {"valid", "integrity-failure"}
                or not isinstance(invocation.get("execution_profile"), dict)
                or not isinstance(invocation.get("execution_profile_sha256"), str)
                or not isinstance(invocation.get("actual_argv"), list)
                or not isinstance(invocation.get("return_code"), int)
                or not isinstance(files, dict)
                or not {"request.json", "stdout.bin", "stderr.bin"}.issubset(files)
            ):
                raise ValueError(
                    "configuration invocation lacks actual-profile or raw-output evidence"
                )
            if status == "valid" and not {
                "response.json",
                "fine-output.json",
            }.issubset(files):
                raise ValueError("valid invocation lacks canonical output evidence")

        invalid = [row for row in invocations if row.get("status") != "valid"]
        hashes = [row.get("fine_output_sha256") for row in invocations]
        if invalid:
            eligible = False
            integrity_failure = "; ".join(
                sorted(
                    {
                        str(
                            row.get("integrity_error")
                            or "unspecified integrity failure"
                        )
                        for row in invalid
                    }
                )
            )
            canonical_hash = None
        elif len(set(hashes)) != 1 or hashes[0] is None:
            eligible = False
            integrity_failure = "repeatability failure"
            canonical_hash = None
        else:
            eligible = True
            integrity_failure = None
            canonical_hash = hashes[0]
        if configuration.get("eligible") is not eligible:
            raise ValueError(
                "configuration eligibility differs from retained invocations"
            )
        if configuration.get("integrity_failure") != integrity_failure:
            raise ValueError(
                "configuration integrity failure differs from retained invocations"
            )
        if configuration.get("canonical_output_sha256") != canonical_hash:
            raise ValueError(
                "configuration output hash differs from retained invocations"
            )

        complete_output = configuration.get("complete_output")
        if eligible:
            if (
                not isinstance(complete_output, dict)
                or not isinstance(complete_output.get("segments"), list)
                or not isinstance(complete_output.get("unassigned"), list)
            ):
                raise ValueError("eligible configuration lacks its complete output")
            members = set(str(member) for member in readable)
            segments = complete_output["segments"]
            unassigned = complete_output["unassigned"]
            if any(
                not isinstance(segment, list)
                or not segment
                or len(segment) != len(set(segment))
                or not set(segment).issubset(members)
                for segment in segments
            ):
                raise ValueError("configuration output contains an invalid segment")
            if len(unassigned) != len(set(unassigned)) or not set(unassigned).issubset(
                members
            ):
                raise ValueError(
                    "configuration output contains invalid unassigned members"
                )
            assigned = set().union(*(set(segment) for segment in segments), set())
            if set(unassigned) != members - assigned:
                raise ValueError(
                    "configuration unassigned members are not the exact complement"
                )
            selected_segments = segments
            selected_unassigned = unassigned
        else:
            if complete_output is not None:
                raise ValueError(
                    "ineligible configuration must not claim a complete output"
                )
            selected_segments = []
            selected_unassigned = []
        outputs[input_id] = {
            "eligible": eligible,
            "integrity_failure": integrity_failure,
            "segments": selected_segments,
            "unassigned": selected_unassigned,
            "canonical_output_sha256": canonical_hash,
            "invocation_record_ids": list(invocation_ids),
            "invocations": list(invocations),
        }
    return characterize_experiment_02(frozen_inputs, outputs, frozen_encodings)


def validate_experiment_02_coverage(
    manifest: Mapping[str, object],
    *,
    frozen_inputs: Sequence[Mapping[str, object]],
    frozen_encodings: Mapping[str, Mapping[str, object]],
    expected_configuration_ids: Sequence[str],
    expected_unequal_configuration_ids: Sequence[str],
    mandatory_summaries: Mapping[str, object],
    exceptions: Mapping[str, object],
) -> dict[str, int]:
    """Verify exact configuration and matched-comparison coverage."""

    configurations = manifest.get("configurations")
    comparisons = manifest.get("comparisons")
    if not isinstance(configurations, list) or not isinstance(comparisons, list):
        raise ValueError("coverage manifest is missing configurations or comparisons")
    actual_configuration_ids = [item.get("configuration_id") for item in configurations]
    if len(actual_configuration_ids) != len(set(actual_configuration_ids)) or set(
        actual_configuration_ids
    ) != set(expected_configuration_ids):
        raise ValueError("configuration coverage differs from the frozen schedule")
    if {str(item.get("input_id")) for item in frozen_inputs} != set(
        expected_configuration_ids
    ):
        raise ValueError(
            "frozen Experiment 2 inputs differ from expected configuration IDs"
        )
    configuration_by_id = {
        str(item["configuration_id"]): item for item in configurations
    }
    reconstructed = _reconstruct_experiment_02_machine_outcomes(
        configurations,
        frozen_inputs=frozen_inputs,
        frozen_encodings=frozen_encodings,
    )
    reconstructed_configurations = reconstructed["configurations"]
    packet_members: dict[str, tuple[str, ...]] = {}
    member_set_review: dict[tuple[str, ...], tuple[str, str]] = {}
    for item in configurations:
        invocations = item.get("invocation_record_ids")
        if not isinstance(invocations, list) or len(invocations) != 2:
            raise ValueError(
                "each configuration must bind exactly two invocation records"
            )
        invocation_rows = item.get("invocations")
        if not isinstance(invocation_rows, list) or len(invocation_rows) != 2:
            raise ValueError(
                "each configuration must retain two complete invocation records"
            )
        if {row.get("run_id") for row in invocation_rows} != set(invocations) or {
            row.get("repetition") for row in invocation_rows
        } != {1, 2}:
            raise ValueError("configuration invocation bindings are inconsistent")
        for invocation in invocation_rows:
            status = invocation.get("status")
            files = invocation.get("files")
            if (
                status not in {"valid", "integrity-failure"}
                or not isinstance(invocation.get("execution_profile"), dict)
                or not isinstance(invocation.get("execution_profile_sha256"), str)
                or not isinstance(invocation.get("actual_argv"), list)
                or not isinstance(invocation.get("return_code"), int)
                or not isinstance(files, dict)
                or not {"request.json", "stdout.bin", "stderr.bin"}.issubset(files)
            ):
                raise ValueError(
                    "configuration invocation lacks actual-profile or raw-output evidence"
                )
            if status == "valid" and not {
                "response.json",
                "fine-output.json",
            }.issubset(files):
                raise ValueError("valid invocation lacks canonical output evidence")
        if item.get("eligible") is True:
            if any(row.get("status") != "valid" for row in invocation_rows):
                raise ValueError(
                    "eligible configuration contains an invalid invocation"
                )
            hashes = {row.get("fine_output_sha256") for row in invocation_rows}
            if (
                len(hashes) != 1
                or None in hashes
                or item.get("canonical_output_sha256") not in hashes
            ):
                raise ValueError(
                    "eligible configuration repeat hashes are inconsistent"
                )
        complete_output = item.get("complete_output")
        if item.get("eligible") is True and (
            not isinstance(complete_output, dict)
            or not isinstance(complete_output.get("segments"), list)
            or not isinstance(complete_output.get("unassigned"), list)
        ):
            raise ValueError("eligible configuration lacks its complete output")
        occurrences = item.get("cross_subject_occurrences", [])
        if not isinstance(occurrences, list):
            raise ValueError("configuration cross-subject occurrences are invalid")
        for occurrence in occurrences:
            members = occurrence.get("readable_members")
            opaque_members = occurrence.get("opaque_members")
            roles = occurrence.get("member_roles")
            review = occurrence.get("review")
            if (
                not isinstance(members, list)
                or not isinstance(roles, dict)
                or set(roles) != set(members)
                or not isinstance(review, dict)
                or not isinstance(review.get("packet"), str)
                or review.get("verdict")
                not in {"pending", "valid", "invalid", "uncertain", "unavailable"}
            ):
                raise ValueError(
                    "cross-subject occurrence is not bound to complete review evidence"
                )
            if occurrence.get("configuration_id") != item.get("configuration_id"):
                raise ValueError(
                    "cross-subject occurrence names the wrong configuration"
                )
            opaque_by_readable = item.get("opaque_id_by_readable")
            if (
                not isinstance(opaque_by_readable, dict)
                or set(opaque_by_readable)
                != {
                    member
                    for subject in item["subjects"].values()
                    for member in subject["members"]
                }
                or not isinstance(opaque_members, list)
                or set(opaque_members)
                != {opaque_by_readable[member] for member in members}
            ):
                raise ValueError(
                    "cross-subject occurrence has the wrong opaque member set"
                )
            canonical_members = tuple(sorted(str(member) for member in members))
            if canonical_members not in {
                tuple(sorted(str(member) for member in segment))
                for segment in complete_output["segments"]
            }:
                raise ValueError(
                    "cross-subject occurrence is absent from the complete output"
                )
            packet = str(review["packet"])
            verdict = str(review["verdict"])
            prior_members = packet_members.setdefault(packet, canonical_members)
            if prior_members != canonical_members:
                raise ValueError(
                    "one semantic-review packet is reused for different members"
                )
            prior_review = member_set_review.setdefault(
                canonical_members, (packet, verdict)
            )
            if prior_review != (packet, verdict):
                raise ValueError(
                    "one member set has inconsistent packet or verdict reuse"
                )
            for member in members:
                containing = [
                    (subject_name, subject)
                    for subject_name, subject in item["subjects"].items()
                    if member in subject["members"]
                ]
                if len(containing) != 1:
                    raise ValueError("cross-subject member lacks one declared subject")
                subject_name, subject = containing[0]
                expected_role = {
                    "subject": subject_name,
                    "support_count": len(subject["members"]),
                    "support_role": subject["support_role"],
                }
                if roles[member] != expected_role:
                    raise ValueError(
                        "cross-subject occurrence has an incorrect support role"
                    )
        expected_configuration = copy.deepcopy(
            reconstructed_configurations[str(item["configuration_id"])]
        )
        expected_occurrences = {
            tuple(occurrence["readable_members"]): occurrence
            for occurrence in expected_configuration["cross_subject_occurrences"]
        }
        actual_occurrences = {
            tuple(occurrence["readable_members"]): occurrence
            for occurrence in occurrences
        }
        if (
            len(expected_occurrences)
            != len(expected_configuration["cross_subject_occurrences"])
            or len(actual_occurrences) != len(occurrences)
            or set(actual_occurrences) != set(expected_occurrences)
        ):
            raise ValueError(
                "machine-derived cross-subject occurrence coverage is incomplete"
            )
        for members, expected_occurrence in expected_occurrences.items():
            expected_occurrence["review"] = copy.deepcopy(
                actual_occurrences[members]["review"]
            )
        _refresh_singleton_review_dispositions(expected_configuration)
        if item != expected_configuration:
            raise ValueError(
                "configuration machine-derived outcomes differ from complete output"
            )
    actual_comparisons = [item.get("unequal_configuration_id") for item in comparisons]
    if len(actual_comparisons) != len(set(actual_comparisons)) or set(
        actual_comparisons
    ) != set(expected_unequal_configuration_ids):
        raise ValueError("comparison coverage differs from the frozen schedule")
    for comparison in comparisons:
        unequal_id = comparison.get("unequal_configuration_id")
        balanced_id = comparison.get("balanced_configuration_id")
        if (
            unequal_id not in configuration_by_id
            or balanced_id not in configuration_by_id
        ):
            raise ValueError("comparison links to an unknown configuration")
        unequal = configuration_by_id[str(unequal_id)]
        balanced = configuration_by_id[str(balanced_id)]
        if (
            balanced.get("condition") != "balanced"
            or unequal.get("condition") == "balanced"
            or balanced.get("neighborhood") != unequal.get("neighborhood")
            or balanced.get("schedule") != unequal.get("schedule")
        ):
            raise ValueError(
                "comparison does not use its exact matched balanced baseline"
            )
        survival = comparison.get("subject_survival")
        if not isinstance(survival, list) or len(survival) != 3:
            raise ValueError("each unequal comparison must account for three subjects")
        if {row.get("subject") for row in survival} != set(unequal["subjects"]):
            raise ValueError("comparison survival rows do not cover its three subjects")
        expected_projection = (
            "available"
            if balanced.get("eligible") is True and unequal.get("eligible") is True
            else "unavailable"
        )
        if comparison.get("projection_state") != expected_projection:
            raise ValueError(
                "comparison projection availability contradicts its inputs"
            )
        expected_failures = [
            {
                "configuration_id": configuration["configuration_id"],
                "integrity_failure": configuration["integrity_failure"],
            }
            for configuration in (balanced, unequal)
            if configuration.get("eligible") is not True
        ]
        if comparison.get("projection_dependency_failures") != expected_failures:
            raise ValueError("comparison dependency failures are incomplete")
        expected_projection_value = (
            _experiment_02_projection(balanced, unequal)
            if expected_projection == "available"
            else None
        )
        if comparison.get("projection") != expected_projection_value:
            raise ValueError("comparison projection differs from its complete outputs")
        expected_survival = []
        for subject_name, unequal_subject in unequal["subjects"].items():
            support_count = unequal_subject.get("support_count")
            if support_count == 1:
                verdict = "not_applicable_singleton"
                reason = None
            elif expected_failures:
                verdict = "unavailable"
                reason = "; ".join(
                    f"{failure['configuration_id']}: {failure['integrity_failure']}"
                    for failure in expected_failures
                )
            elif not balanced["subjects"][subject_name]["reference_cohort_recovered"]:
                verdict = "unavailable"
                reason = "matched balanced baseline did not recover"
            else:
                verdict = (
                    "survived"
                    if unequal_subject["reference_cohort_recovered"]
                    else "did_not_survive"
                )
                reason = None
            expected_survival.append(
                {
                    "subject": subject_name,
                    "support_count": support_count,
                    "support_role": unequal_subject.get("support_role"),
                    "matched_baseline_recovered": balanced["subjects"][
                        subject_name
                    ].get("reference_cohort_recovered"),
                    "verdict": verdict,
                    "reason": reason,
                }
            )
        if survival != expected_survival:
            raise ValueError(
                "comparison survival verdicts differ from bound configuration outcomes"
            )
    if comparisons != reconstructed["comparisons"]:
        raise ValueError("comparison records differ from machine-derived outcomes")
    if manifest.get("support_role_by_wording_form") != reconstructed.get(
        "support_role_by_wording_form"
    ):
        raise ValueError(
            "support-role by wording-form evidence differs from the frozen fixtures"
        )

    role_counts: Counter[str] = Counter()
    appearance_counts: Counter[str] = Counter()
    condition_counts: Counter[str] = Counter()
    for configuration in configurations:
        condition_counts[str(configuration.get("condition"))] += 1
        subjects = configuration.get("subjects")
        if not isinstance(subjects, dict) or len(subjects) != 3:
            raise ValueError(
                "each configuration must account for three declared subjects"
            )
        for subject in subjects.values():
            role = subject.get("support_role")
            members = subject.get("members")
            if not isinstance(role, str) or not isinstance(members, list):
                raise ValueError("configuration subject coverage is incomplete")
            role_counts[role] += 1
            appearance_counts.update(str(member) for member in members)
    if not appearance_counts:
        minimum_appearances = maximum_appearances = 0
    else:
        minimum_appearances = min(appearance_counts.values())
        maximum_appearances = max(appearance_counts.values())
    if len(expected_configuration_ids) == 512:
        expected_conditions = {
            "balanced": 32,
            "imbalanced": 96,
            "singleton": 192,
            "dense-singleton": 192,
        }
        expected_roles = {
            "balanced-4": 96,
            "imbalanced-8": 96,
            "imbalanced-2": 192,
            "singleton-6": 192,
            "singleton-5": 192,
            "singleton-1": 192,
            "dense-singleton-8": 192,
            "dense-singleton-3": 192,
            "dense-singleton-1": 192,
        }
        if dict(condition_counts) != expected_conditions:
            raise ValueError(
                "condition coverage differs from the frozen 512-input schedule"
            )
        if dict(role_counts) != expected_roles:
            raise ValueError("support-role coverage differs from the frozen schedule")
        if len(appearance_counts) != 96 or set(appearance_counts.values()) != {64}:
            raise ValueError("vector appearances differ from the frozen schedule")
    characterization = {
        "configurations": configuration_by_id,
        "comparisons": comparisons,
    }
    if mandatory_summaries != build_experiment_02_summaries(characterization):
        raise ValueError(
            "mandatory Experiment 2 summary tables differ from the coverage manifest"
        )
    if exceptions != build_experiment_02_exceptions(characterization):
        raise ValueError("Experiment 2 exceptions differ from the coverage manifest")
    return {
        "configuration_count": len(configurations),
        "comparison_count": len(comparisons),
        "condition_counts": dict(sorted(condition_counts.items())),
        "support_role_counts": dict(sorted(role_counts.items())),
        "vector_count": len(appearance_counts),
        "minimum_vector_appearance_count": minimum_appearances,
        "maximum_vector_appearance_count": maximum_appearances,
    }


def canonical_projection(
    segments: Iterable[Iterable[str]],
    retained_ids: set[str],
    *,
    global_order: Sequence[str] | None = None,
) -> Counter[tuple[str, ...]]:
    """Project segments as the protocol-defined multiset."""

    rank = (
        {member: ordinal for ordinal, member in enumerate(global_order)}
        if global_order is not None
        else None
    )

    def ordered(members: set[str]) -> tuple[str, ...]:
        if rank is None:
            return tuple(sorted(members))
        if not members.issubset(rank):
            raise ValueError("projection member is absent from the frozen global order")
        return tuple(sorted(members, key=rank.__getitem__))

    projected: Counter[tuple[str, ...]] = Counter()
    for segment in segments:
        members = ordered(set(segment) & retained_ids)
        if members:
            projected[members] += 1
    return projected


def build_representation_diagnostics(
    protocol: Mapping[str, object],
    vectors_by_encoding: Mapping[str, Sequence[float]],
    vector_records: Mapping[str, Mapping[str, object]] | None = None,
) -> dict[str, object]:
    """Preserve raw-vector cosine diagnostics without using them as verdicts."""

    encodings = protocol.get("encodings")
    if not isinstance(encodings, list):
        raise ValueError("protocol is missing its encoding fixture")
    normalized: dict[str, tuple[float, ...]] = {}
    dimensions = None
    for encoding in encodings:
        encoding_id = str(encoding["encoding_id"])
        values = vectors_by_encoding.get(encoding_id)
        if values is None:
            raise ValueError(f"diagnostics are missing vector {encoding_id}")
        values = tuple(float(value) for value in values)
        if dimensions is None:
            dimensions = len(values)
        if (
            len(values) != dimensions
            or not values
            or not all(math.isfinite(value) for value in values)
        ):
            raise ValueError("diagnostic vectors have inconsistent dimensions")
        norm = math.sqrt(sum(value * value for value in values))
        if norm == 0.0 or not math.isfinite(norm):
            raise ValueError("diagnostic vector has an invalid norm")
        normalized[encoding_id] = tuple(value / norm for value in values)

    def cosine(left: str, right: str) -> float:
        return sum(
            first * second
            for first, second in zip(normalized[left], normalized[right], strict=True)
        )

    experiments = {}
    for experiment in (
        "experiment-01",
        "experiment-02",
        "experiment-03",
        "experiment-04",
    ):
        selected = [item for item in encodings if item["experiment"] == experiment]
        if not selected:
            continue
        ids = [str(item["encoding_id"]) for item in selected]
        matrix = [[cosine(left, right) for right in ids] for left in ids]
        nearest_neighbors = []
        for left in ids:
            ordered = sorted(
                (
                    (-cosine(left, right), right, cosine(left, right))
                    for right in ids
                    if right != left
                ),
                key=lambda row: (row[0], row[1]),
            )
            nearest_neighbors.append(
                {
                    "encoding_id": left,
                    "neighbors": [
                        {"encoding_id": right, "cosine": value, "rank": rank}
                        for rank, (_, right, value) in enumerate(ordered, start=1)
                    ],
                }
            )
        experiments[experiment] = {
            "encoding_ids": ids,
            "readable_ids": [str(item["readable_id"]) for item in selected],
            "cosine_matrix": matrix,
            "nearest_neighbor_orders": nearest_neighbors,
        }

    exp2 = [item for item in encodings if item["experiment"] == "experiment-02"]
    if exp2:
        by_neighborhood: dict[str, list[Mapping[str, object]]] = {}
        for item in exp2:
            by_neighborhood.setdefault(
                str(item["metadata"]["neighborhood"]), []
            ).append(item)
        distributions = {}
        nearest_rows = []
        for neighborhood, items in sorted(by_neighborhood.items()):
            same_values = []
            cross_values = []
            for left_index, left in enumerate(items):
                left_id = str(left["encoding_id"])
                left_subject = str(left["metadata"]["subject_code"])
                local_neighbors = []
                for right_index, right in enumerate(items):
                    right_id = str(right["encoding_id"])
                    if right_id == left_id:
                        continue
                    value = cosine(left_id, right_id)
                    local_neighbors.append(
                        (
                            -value,
                            str(right["readable_id"]),
                            str(right["metadata"]["subject_code"]),
                            value,
                        )
                    )
                    if left_index < right_index:
                        if left_subject == str(right["metadata"]["subject_code"]):
                            same_values.append(value)
                        else:
                            cross_values.append(value)
                local_neighbors.sort()
                local_nearest_same_rank = (
                    next(
                        rank
                        for rank, row in enumerate(local_neighbors, start=1)
                        if row[2] == left_subject
                    )
                    if any(row[2] == left_subject for row in local_neighbors)
                    else None
                )
                global_neighbors = sorted(
                    (
                        -cosine(left_id, str(right["encoding_id"])),
                        str(right["readable_id"]),
                        str(right["metadata"]["subject_code"]),
                        cosine(left_id, str(right["encoding_id"])),
                    )
                    for right in exp2
                    if str(right["encoding_id"]) != left_id
                )
                nearest_same_rank = next(
                    (
                        rank
                        for rank, row in enumerate(global_neighbors, start=1)
                        if row[2] == left_subject
                    ),
                    None,
                )
                nearest_same = (
                    global_neighbors[nearest_same_rank - 1]
                    if nearest_same_rank is not None
                    else None
                )
                highest_cross = max(
                    (row[3] for row in global_neighbors if row[2] != left_subject),
                    default=None,
                )
                nearest_rows.append(
                    {
                        "neighborhood": neighborhood,
                        "readable_id": str(left["readable_id"]),
                        "subject": left_subject,
                        "nearest_same_subject_rank": nearest_same_rank,
                        "local_nearest_same_subject_rank": local_nearest_same_rank,
                        "nearest_same_subject_cosine": (
                            nearest_same[3] if nearest_same else None
                        ),
                        "highest_cross_subject_cosine": highest_cross,
                        "nearest_same_subject_margin": (
                            nearest_same[3] - highest_cross
                            if nearest_same and highest_cross is not None
                            else None
                        ),
                    }
                )

            def distribution(values: list[float]) -> dict[str, object]:
                return {
                    "count": len(values),
                    "minimum": min(values) if values else None,
                    "maximum": max(values) if values else None,
                    "mean": statistics.fmean(values) if values else None,
                    "median": statistics.median(values) if values else None,
                }

            distributions[neighborhood] = {
                "same_subject": distribution(same_values),
                "cross_subject": distribution(cross_values),
            }
        experiments["experiment-02"].update(
            {
                "cosine_distributions_by_neighborhood": distributions,
                "nearest_same_subject": nearest_rows,
                "subject_by_wording_form": {
                    subject: dict(
                        sorted(
                            Counter(
                                str(item["metadata"]["form"])
                                for item in exp2
                                if str(item["metadata"]["subject_code"]) == subject
                            ).items()
                        )
                    )
                    for subject in sorted(
                        {str(item["metadata"]["subject_code"]) for item in exp2}
                    )
                },
            }
        )
    if vector_records is not None:
        tokenizer_records = {}
        for encoding in encodings:
            if encoding["experiment"] not in {"experiment-03", "experiment-04"}:
                continue
            encoding_id = str(encoding["encoding_id"])
            record = vector_records.get(encoding_id)
            if not isinstance(record, Mapping):
                raise ValueError(f"token diagnostics are missing {encoding_id}")
            positions = record.get("selected_token_indices")
            token_ids = record.get("selected_token_ids")
            token_count = record.get("token_count")
            if (
                not isinstance(positions, list)
                or not positions
                or not all(isinstance(value, int) and value >= 0 for value in positions)
                or not isinstance(token_ids, list)
                or len(token_ids) != len(positions)
                or not all(isinstance(value, int) and value >= 0 for value in token_ids)
                or not isinstance(token_count, int)
                or token_count <= max(positions)
            ):
                raise ValueError(f"token diagnostics are invalid for {encoding_id}")
            tokenizer_records[encoding_id] = {
                "selected_token_indices": positions,
                "selected_token_ids": token_ids,
                "selected_piece_count": len(positions),
                "token_count": token_count,
            }
        experiments["experiment-03"]["tokenizer_records"] = {
            key: value
            for key, value in tokenizer_records.items()
            if key.startswith("experiment-03/")
        }
        experiments["experiment-04"]["tokenizer_records"] = {
            key: value
            for key, value in tokenizer_records.items()
            if key.startswith("experiment-04/")
        }
        exp3_pairs = []
        exp3_by_readable: dict[str, dict[str, Mapping[str, object]]] = {}
        for encoding in encodings:
            if encoding["experiment"] == "experiment-03":
                exp3_by_readable.setdefault(str(encoding["readable_id"]), {})[
                    str(encoding["metadata"]["version"])
                ] = encoding
        for readable_id, versions in sorted(exp3_by_readable.items()):
            if set(versions) != {"B", "C"}:
                raise ValueError(f"Experiment 3 pair {readable_id} is incomplete")
            b_id = str(versions["B"]["encoding_id"])
            c_id = str(versions["C"]["encoding_id"])
            b_tokens = tokenizer_records[b_id]
            c_tokens = tokenizer_records[c_id]
            changed = [
                ordinal
                for ordinal, (left, right) in enumerate(
                    zip(
                        b_tokens["selected_token_ids"],
                        c_tokens["selected_token_ids"],
                        strict=False,
                    )
                )
                if left != right
            ]
            exp3_pairs.append(
                {
                    "readable_id": readable_id,
                    "baseline_encoding_id": b_id,
                    "changed_encoding_id": c_id,
                    "cosine": cosine(b_id, c_id),
                    "cosine_change_from_identity": cosine(b_id, c_id) - 1.0,
                    "selected_positions_equal": (
                        b_tokens["selected_token_indices"]
                        == c_tokens["selected_token_indices"]
                    ),
                    "selected_piece_counts_equal": (
                        b_tokens["selected_piece_count"]
                        == c_tokens["selected_piece_count"]
                    ),
                    "changed_selected_token_ordinals": changed,
                    "exactly_one_selected_token_changed": (
                        b_tokens["selected_piece_count"]
                        == c_tokens["selected_piece_count"]
                        and len(changed) == 1
                    ),
                    "selected_piece_count_in_frozen_range": (
                        21 <= b_tokens["selected_piece_count"] <= 34
                        and 21 <= c_tokens["selected_piece_count"] <= 34
                    ),
                }
            )
        failed_pairs = [
            row["readable_id"]
            for row in exp3_pairs
            if not (
                row["selected_positions_equal"]
                and row["selected_piece_counts_equal"]
                and row["exactly_one_selected_token_changed"]
                and row["selected_piece_count_in_frozen_range"]
            )
        ]
        if failed_pairs:
            raise ValueError(
                "Experiment 3 executable tokenizer qualification failed for "
                + ", ".join(failed_pairs)
            )
        experiments["experiment-03"]["matched_baseline_changed_pairs"] = exp3_pairs
        experiments["experiment-03"]["tokenizer_qualification"] = {
            "qualified": True,
            "pair_count": len(exp3_pairs),
            "required_pair_count": 24,
            "selected_piece_count_range": [21, 34],
        }
        if len(exp3_pairs) != 24:
            raise ValueError(
                "Experiment 3 executable tokenizer qualification has the wrong pair count"
            )
    return {
        "schema_version": SCHEMA_VERSION,
        "dimensions": dimensions,
        "verdict_use": "diagnostic_only",
        "experiments": experiments,
    }


def _segments(record: Mapping[str, object]) -> list[set[str]]:
    value = record.get("segments")
    if not isinstance(value, list):
        raise ValueError("scoring record is missing selected segments")
    return [set(segment) for segment in value]


def _unassigned(record: Mapping[str, object]) -> set[str]:
    value = record.get("unassigned")
    if not isinstance(value, list):
        raise ValueError("scoring record is missing unassigned IDs")
    return set(value)


def _eligible(record: Mapping[str, object] | None) -> bool:
    return bool(record is not None and record.get("eligible") is True)


def _integrity_reason(record: Mapping[str, object] | None) -> str:
    if record is None:
        return "missing immutable input record"
    reason = record.get("integrity_failure")
    return str(reason) if reason else "input was not eligible"


def _output_signature(
    record: Mapping[str, object],
) -> tuple[tuple[tuple[str, ...], ...], tuple[str, ...]]:
    segments = tuple(
        sorted(_canonical_member_set(segment) for segment in _segments(record))
    )
    return segments, tuple(sorted(_unassigned(record)))


def _output_difference(
    baseline: Mapping[str, object], changed: Mapping[str, object]
) -> dict[str, object]:
    baseline_segments, baseline_unassigned = _output_signature(baseline)
    changed_segments, changed_unassigned = _output_signature(changed)
    return {
        "segments_added": [
            list(segment)
            for segment in sorted(set(changed_segments) - set(baseline_segments))
        ],
        "segments_removed": [
            list(segment)
            for segment in sorted(set(baseline_segments) - set(changed_segments))
        ],
        "unassigned_added": sorted(set(changed_unassigned) - set(baseline_unassigned)),
        "unassigned_removed": sorted(
            set(baseline_unassigned) - set(changed_unassigned)
        ),
    }


def _qualify_cohorts(
    record: Mapping[str, object], cohorts: Sequence[set[str]]
) -> dict[str, object]:
    result = score_experiment_01(
        _segments(record),
        {str(index): cohort for index, cohort in enumerate(cohorts)},
    )
    return {
        "qualified": result["verdict"] == "pass",
        "details": result,
        "reference_output": {
            "segments": [sorted(segment) for segment in _segments(record)],
            "unassigned": sorted(_unassigned(record)),
        },
    }


def _project_output(
    record: Mapping[str, object], retained: set[str]
) -> dict[str, object]:
    frozen_order = record.get("input_member_order")
    rank = (
        {member: ordinal for ordinal, member in enumerate(frozen_order)}
        if isinstance(frozen_order, list) and frozen_order
        else None
    )

    def ordered(members: set[str]) -> tuple[str, ...]:
        if rank is None:
            return tuple(sorted(members))
        if not members.issubset(rank):
            raise ValueError("projected output is absent from its frozen input order")
        return tuple(sorted(members, key=rank.__getitem__))

    projected_segments = []
    provenance = []
    for ordinal, segment in enumerate(_segments(record), start=1):
        projected = ordered(segment & retained)
        if not projected:
            continue
        projected_segments.append(projected)
        provenance.append(
            {
                "source_segment_ordinal": ordinal,
                "source_segment": sorted(segment),
                "projected_members": list(projected),
                "source_invocation_record_ids": list(
                    record.get("invocation_record_ids", [])
                ),
            }
        )
    duplicates = sorted(
        [
            list(segment)
            for segment, count in Counter(projected_segments).items()
            if count > 1
        ]
    )
    return {
        "segments": [list(segment) for segment in sorted(projected_segments)],
        "unassigned": sorted(_unassigned(record) & retained),
        "duplicate_projected_segments": duplicates,
        "provenance": provenance,
    }


def score_experiment_06(
    outputs: Mapping[str, Mapping[str, object]],
    *,
    left_groups: Sequence[set[str]],
    right_groups: Sequence[set[str]],
    duplicate_aliases: Mapping[str, str],
    imported_experiment_01_passed: bool,
) -> dict[str, object]:
    """Score Experiment 6's three stability interventions."""

    left_record = outputs.get("L0")
    right_record = outputs.get("R0")

    def input_evidence(
        input_id: str,
        record: Mapping[str, object] | None,
        reference: Mapping[str, object] | None = None,
    ) -> dict[str, object]:
        eligible = _eligible(record)
        reference_eligible = _eligible(reference)
        return {
            "input_id": input_id,
            "eligible": eligible,
            "integrity_failure": None if eligible else _integrity_reason(record),
            "canonical_output_sha256": (
                record.get("canonical_output_sha256") if record else None
            ),
            "invocation_record_ids": (
                list(record.get("invocation_record_ids", [])) if record else []
            ),
            "invocations": list(record.get("invocations", [])) if record else [],
            "complete_output": (
                {
                    "segments": [sorted(segment) for segment in _segments(record)],
                    "unassigned": sorted(_unassigned(record)),
                }
                if eligible
                else None
            ),
            "complete_output_difference_from_reference": (
                _output_difference(reference, record)
                if eligible and reference_eligible
                else None
            ),
        }

    baselines: dict[str, dict[str, object]] = {}
    for name, record, cohorts in (
        ("L0", left_record, left_groups),
        ("R0", right_record, right_groups),
    ):
        if not _eligible(record):
            baselines[name] = {
                "qualified": False,
                "state": "integrity_failure",
                "reason": _integrity_reason(record),
                "input": input_evidence(f"experiment-06/{name}", record),
            }
        else:
            qualification = _qualify_cohorts(record, cohorts)
            qualification["state"] = (
                "qualified"
                if qualification["qualified"]
                else "local_prerequisite_failure"
            )
            qualification["input"] = input_evidence(f"experiment-06/{name}", record)
            baselines[name] = qualification

    conditions: dict[str, dict[str, object]] = {}
    duplicate_record = outputs.get("duplicates")
    duplicate_input = input_evidence(
        "experiment-06/exact-duplicates", duplicate_record, left_record
    )
    if not baselines["L0"]["qualified"]:
        conditions["duplicates"] = {
            "verdict": "no_verdict",
            "reason": "L0 baseline did not qualify",
            "input": duplicate_input,
        }
    elif not _eligible(duplicate_record):
        conditions["duplicates"] = {
            "verdict": "no_verdict",
            "reason": _integrity_reason(duplicate_record),
            "input": duplicate_input,
        }
    else:
        reverse_aliases: dict[str, list[str]] = {}
        for alias, source in duplicate_aliases.items():
            reverse_aliases.setdefault(source, []).append(alias)
        reference = left_record
        expected_segments = []
        for segment in _segments(reference):
            expanded = set(segment)
            for source in segment:
                expanded.update(reverse_aliases.get(source, ()))
            expected_segments.append(expanded)
        expected_unassigned = set(_unassigned(reference))
        for source in list(expected_unassigned):
            expected_unassigned.update(reverse_aliases.get(source, ()))
        expected = (
            tuple(
                sorted(_canonical_member_set(segment) for segment in expected_segments)
            ),
            tuple(sorted(expected_unassigned)),
        )
        actual = _output_signature(duplicate_record)
        conditions["duplicates"] = {
            "verdict": "pass" if actual == expected else "stability_failure",
            "expected": {
                "segments": [list(segment) for segment in expected[0]],
                "unassigned": list(expected[1]),
            },
            "actual": {
                "segments": [list(segment) for segment in actual[0]],
                "unassigned": list(actual[1]),
            },
            "input": duplicate_input,
        }

    unrelated_record = outputs.get("unrelated")
    unrelated_input = input_evidence(
        "experiment-06/unrelated-addition", unrelated_record, left_record
    )
    left_ids = set().union(*left_groups)
    right_first = set(right_groups[0])
    if not baselines["L0"]["qualified"]:
        conditions["unrelated_addition"] = {
            "verdict": "no_verdict",
            "reason": "L0 baseline did not qualify",
            "input": unrelated_input,
        }
    elif not _eligible(unrelated_record):
        conditions["unrelated_addition"] = {
            "verdict": "no_verdict",
            "reason": _integrity_reason(unrelated_record),
            "input": unrelated_input,
        }
    else:
        projection = _project_output(unrelated_record, left_ids)
        reference_signature = _output_signature(left_record)
        projected_signature = (
            tuple(sorted(tuple(sorted(segment)) for segment in projection["segments"])),
            tuple(sorted(projection["unassigned"])),
        )
        contaminated = [
            sorted(segment)
            for segment in _segments(unrelated_record)
            if segment & left_ids and segment & right_first
        ]
        added_subject_only = [
            sorted(segment)
            for segment in _segments(unrelated_record)
            if segment and segment.issubset(right_first)
        ]
        added_subject_unassigned = sorted(_unassigned(unrelated_record) & right_first)
        passed = (
            not projection["duplicate_projected_segments"]
            and projected_signature == reference_signature
            and not contaminated
        )
        conditions["unrelated_addition"] = {
            "verdict": "pass" if passed else "stability_failure",
            "projection": projection,
            "reference": {
                "segments": [list(segment) for segment in reference_signature[0]],
                "unassigned": list(reference_signature[1]),
            },
            "cross_subject_contamination": contaminated,
            "added_subject_only_segments": added_subject_only,
            "added_subject_unassigned": added_subject_unassigned,
            "input": unrelated_input,
        }

    combined_record = outputs.get("combined")
    combined_input = input_evidence(
        "experiment-01/default", combined_record, left_record
    )
    combined_sides = {}
    for side, baseline_name, baseline_record, groups in (
        ("L", "L0", left_record, left_groups),
        ("R", "R0", right_record, right_groups),
    ):
        if not imported_experiment_01_passed:
            combined_sides[side] = {
                "verdict": "no_verdict",
                "reason": "imported Experiment 1 artifact did not pass",
            }
        elif not baselines[baseline_name]["qualified"]:
            combined_sides[side] = {
                "verdict": "no_verdict",
                "reason": f"{baseline_name} baseline did not qualify",
            }
        elif not _eligible(combined_record):
            combined_sides[side] = {
                "verdict": "no_verdict",
                "reason": _integrity_reason(combined_record),
            }
        else:
            retained = set().union(*groups)
            projection = _project_output(combined_record, retained)
            reference_signature = _output_signature(baseline_record)
            projected_signature = (
                tuple(
                    sorted(tuple(sorted(segment)) for segment in projection["segments"])
                ),
                tuple(sorted(projection["unassigned"])),
            )
            passed = (
                not projection["duplicate_projected_segments"]
                and projected_signature == reference_signature
            )
            combined_sides[side] = {
                "verdict": "pass" if passed else "stability_failure",
                "projection": projection,
            }
    side_verdicts = [value["verdict"] for value in combined_sides.values()]
    if not imported_experiment_01_passed:
        combined_verdict = "no_verdict"
        combined_reason = "imported Experiment 1 artifact did not pass"
    elif "no_verdict" in side_verdicts:
        combined_verdict = "no_verdict"
        combined_reason = "one or both side prerequisites were unavailable"
    else:
        combined_verdict = (
            "pass" if side_verdicts == ["pass", "pass"] else "stability_failure"
        )
        combined_reason = None
    conditions["combined"] = {
        "verdict": combined_verdict,
        "reason": combined_reason,
        "sides": combined_sides,
        "input": combined_input,
    }

    owned = [
        conditions[name]["verdict"]
        for name in ("duplicates", "unrelated_addition", "combined")
    ]
    if any(value == "stability_failure" for value in owned):
        overall = "stability_failure"
    elif all(value == "pass" for value in owned) and all(
        baseline["qualified"] for baseline in baselines.values()
    ):
        overall = "pass"
    else:
        overall = "no_verdict"
    return {
        "baselines": baselines,
        "conditions": conditions,
        "overall_verdict": overall,
    }


def _subject_relationship_signature(
    segments: Sequence[set[str]],
    subject_by_member: Mapping[str, str],
    trap_subjects: set[str],
) -> dict[str, object]:
    groups = {
        subject: {
            member for member, value in subject_by_member.items() if value == subject
        }
        for subject in set(subject_by_member.values())
    }
    recovery = {
        subject: group in segments
        for subject, group in sorted(groups.items())
        if subject in trap_subjects
    }
    trap_members = set().union(*(groups[subject] for subject in trap_subjects))
    cross_pairs = set()
    for segment in segments:
        ordered = sorted(segment)
        for index, left in enumerate(ordered):
            for right in ordered[index + 1 :]:
                if subject_by_member[left] != subject_by_member[right] and (
                    left in trap_members or right in trap_members
                ):
                    cross_pairs.add((left, right))
    return {
        "recovery": recovery,
        "cross_subject_pairs": [list(pair) for pair in sorted(cross_pairs)],
    }


def score_experiment_03(
    outputs: Mapping[str, Mapping[str, object]],
    trap_groups: Mapping[str, Mapping[str, set[str]]],
) -> dict[str, object]:
    """Score the three Experiment 3 lexical traps independently."""

    subject_by_member = {
        member: subject
        for groups in trap_groups.values()
        for subject, members in groups.items()
        for member in members
    }
    baseline = outputs.get("experiment-03/BASELINE")
    baseline_eligible = _eligible(baseline)
    baseline_segments = _segments(baseline) if baseline_eligible else []
    all_subjects = set(subject_by_member.values())
    full_baseline_signature = (
        _subject_relationship_signature(
            baseline_segments, subject_by_member, all_subjects
        )
        if baseline_eligible
        else None
    )

    def arm_evidence(
        input_id: str,
        record: Mapping[str, object] | None,
        trap_subjects: set[str],
    ) -> dict[str, object]:
        if not _eligible(record):
            return {
                "input_id": input_id,
                "eligible": False,
                "reason": _integrity_reason(record),
                "relationships": None,
                "complete_relationships": None,
                "shape": "unavailable",
                "complete_output_difference": None,
                "complete_output": None,
            }
        segments = _segments(record)
        relationships = _subject_relationship_signature(
            segments, subject_by_member, trap_subjects
        )
        complete_relationships = _subject_relationship_signature(
            segments, subject_by_member, all_subjects
        )
        if baseline_eligible:
            shape = (
                "exactly_stable"
                if _output_signature(record) == _output_signature(baseline)
                else (
                    "shape_only_change"
                    if complete_relationships == full_baseline_signature
                    else "semantic_change"
                )
            )
            difference = _output_difference(baseline, record)
        else:
            shape = "baseline_unavailable"
            difference = None
        return {
            "input_id": input_id,
            "eligible": True,
            "reason": None,
            "relationships": relationships,
            "complete_relationships": complete_relationships,
            "shape": shape,
            "complete_output_difference": difference,
            "complete_output": {
                "segments": [sorted(segment) for segment in segments],
                "unassigned": sorted(_unassigned(record)),
            },
        }

    results: dict[str, object] = {}
    for trap, groups in sorted(trap_groups.items()):
        trap_subjects = set(groups)
        required = list(groups.values())
        trap_members = set().union(*required)
        baseline_signature = (
            _subject_relationship_signature(
                baseline_segments, subject_by_member, trap_subjects
            )
            if baseline_eligible
            else None
        )
        baseline_pure = bool(
            baseline_eligible
            and all(
                any(segment == cohort for segment in baseline_segments)
                for cohort in required
            )
            and all(
                len(segment) < 2
                or not (segment & trap_members)
                or any(segment.issubset(cohort) for cohort in required)
                for segment in baseline_segments
            )
        )
        suffixes = [subject.removeprefix(trap + "-") for subject in groups]
        control_ids = [f"experiment-03/{trap}-{suffix}-ONLY" for suffix in suffixes]
        control_rows = [
            arm_evidence(control_id, outputs.get(control_id), trap_subjects)
            for control_id in control_ids
        ]
        for row in control_rows:
            row["qualified"] = bool(
                baseline_pure
                and row["eligible"]
                and row["relationships"] == baseline_signature
            )
        both_id = f"experiment-03/{trap}-BOTH"
        both_row = arm_evidence(both_id, outputs.get(both_id), trap_subjects)
        both_row["focal_eligible"] = False

        if not baseline_eligible:
            verdict = "no_verdict"
            reason = _integrity_reason(baseline)
        elif not baseline_pure:
            verdict = "local_recovery_prerequisite_failure"
            reason = "trap baseline relationships did not qualify"
        elif any(not row["eligible"] for row in control_rows):
            verdict = "no_verdict"
            failed = next(row for row in control_rows if not row["eligible"])
            reason = f"{failed['input_id']}: {failed['reason']}"
        elif any(not row["qualified"] for row in control_rows):
            verdict = "one_sided_control_prerequisite_failure"
            failed = next(row for row in control_rows if not row["qualified"])
            reason = f"{failed['input_id']} changed local subject relationships"
        elif not both_row["eligible"]:
            verdict = "no_verdict"
            reason = str(both_row["reason"])
        else:
            both_row["focal_eligible"] = True
            verdict = (
                "pass"
                if both_row["relationships"] == baseline_signature
                else "lexical_collision_failure"
            )
            reason = None
        results[trap] = {
            "verdict": verdict,
            "reason": reason,
            "baseline_qualified": baseline_pure,
            "baseline_relationships": baseline_signature,
            "controls": control_rows,
            "both": both_row,
            "both_relationships": both_row["relationships"],
            "complete_relationships": both_row["complete_relationships"],
            "both_shape": both_row["shape"],
            "complete_output_difference": both_row["complete_output_difference"],
        }
    verdicts = [row["verdict"] for row in results.values()]
    overall = (
        "pass"
        if verdicts and all(value == "pass" for value in verdicts)
        else (
            "lexical_collision_failure"
            if "lexical_collision_failure" in verdicts
            else "no_verdict"
        )
    )
    return {"traps": results, "overall_verdict": overall}


def _reference_segments(
    segments: Sequence[set[str]],
    subject_members: Mapping[str, set[str]],
    declared_subject: Mapping[str, str],
) -> dict[str, list[set[str]]]:
    result = {subject: [] for subject in subject_members}
    for segment in segments:
        segment_subjects = {declared_subject[member] for member in segment}
        if len(segment_subjects) != 1:
            continue
        subject = next(iter(segment_subjects))
        anchors = segment & subject_members[subject]
        if len(anchors) >= 2:
            result[subject].append(segment)
    return result


def _connected_anchor_graph(anchors: set[str], references: Sequence[set[str]]) -> bool:
    if not anchors:
        return False
    adjacency = {anchor: set() for anchor in anchors}
    for segment in references:
        present = segment & anchors
        for left in present:
            adjacency[left].update(present - {left})
    seen = set()
    stack = [next(iter(anchors))]
    while stack:
        item = stack.pop()
        if item in seen:
            continue
        seen.add(item)
        stack.extend(adjacency[item] - seen)
    return seen == anchors


def _anchor_graph_record(
    anchors: set[str], references: Sequence[set[str]]
) -> dict[str, object]:
    edges = set()
    for segment in references:
        present = sorted(segment & anchors)
        for index, left in enumerate(present):
            for right in present[index + 1 :]:
                edges.add((left, right))
    return {
        "vertices": sorted(anchors),
        "edges": [list(edge) for edge in sorted(edges)],
        "reference_segments": [sorted(segment) for segment in references],
        "connected": _connected_anchor_graph(anchors, references),
    }


def _anchor_projection(
    segments: Sequence[set[str]], anchors: set[str]
) -> list[dict[str, object]]:
    rows = []
    for ordinal, segment in enumerate(segments, start=1):
        projection = sorted(segment & anchors)
        rows.append(
            {
                "source_segment_ordinal": ordinal,
                "source_segment": sorted(segment),
                "anchor_members": projection,
            }
        )
    return rows


def _unsupported_auxiliary_segments(
    segments: Sequence[set[str]],
    subject_members: Mapping[str, set[str]],
    scored_vectors: set[str],
) -> list[dict[str, object]]:
    """Record returned segments that no recovered subject can anchor."""

    rows = []
    for ordinal, segment in enumerate(segments, start=1):
        supported = [
            subject
            for subject, anchors in subject_members.items()
            if len(segment & anchors) >= 2
        ]
        if not supported and not (segment & scored_vectors):
            rows.append(
                {
                    "source_segment_ordinal": ordinal,
                    "members": sorted(segment),
                }
            )
    return rows


def _relationship_profile(
    vector: str,
    subjects: Sequence[str],
    segments: Sequence[set[str]],
    references: Mapping[str, Sequence[set[str]]],
    declared_subject: Mapping[str, str],
) -> list[bool]:
    profile = []
    own = declared_subject[vector]
    for subject in subjects:
        if own == subject:
            profile.append(any(vector in segment for segment in references[subject]))
        else:
            profile.append(
                any(
                    vector in segment
                    and any(
                        member != vector and declared_subject[member] == subject
                        for member in segment
                    )
                    for segment in segments
                )
            )
    return profile


def score_experiment_04(
    baseline: Mapping[str, object],
    treatments: Mapping[str, Mapping[str, object]],
    *,
    subject_members: Mapping[str, set[str]],
    controls: Mapping[str, str],
    treatment_targets: Mapping[str, str],
    treatment_contexts: Mapping[str, str],
    treatment_forms: Mapping[str, str],
) -> dict[str, object]:
    """Score Experiment 4's preserved-control relationship profiles."""

    subjects = list(subject_members)
    declared = {
        member: subject
        for subject, members in subject_members.items()
        for member in members
    }
    baseline_eligible = _eligible(baseline)
    baseline_segments = _segments(baseline) if baseline_eligible else []
    baseline_references = (
        _reference_segments(baseline_segments, subject_members, declared)
        if baseline_eligible
        else {subject: [] for subject in subjects}
    )
    reference_qualified = {
        subject: (
            _connected_anchor_graph(
                subject_members[subject], baseline_references[subject]
            )
            if baseline_eligible
            else False
        )
        for subject in subjects
    }
    baseline_graphs = {
        subject: _anchor_graph_record(
            subject_members[subject], baseline_references[subject]
        )
        for subject in subjects
    }
    baseline_profiles = {}
    control_qualified = {}
    for subject, control in controls.items():
        profile = (
            _relationship_profile(
                control, subjects, baseline_segments, baseline_references, declared
            )
            if baseline_eligible
            else None
        )
        expected = [item == subject for item in subjects]
        baseline_profiles[control] = profile
        control_qualified[control] = (
            baseline_eligible
            and all(reference_qualified.values())
            and profile == expected
        )

    treatment_results = {}
    for mixed, record in treatments.items():
        target = treatment_targets[mixed]
        context = treatment_contexts[mixed]
        outer_form = treatment_forms[mixed]
        control = controls[target]
        treatment_identity = {
            "target_subject": target,
            "context_subject": context,
            "outer_form": outer_form,
            "control": control,
            "treatment_integrity_reason": (
                None if _eligible(record) else _integrity_reason(record)
            ),
        }
        treatment_evidence: dict[str, object] = {}
        if _eligible(record):
            treatment_declared = {**declared, mixed: target}
            segments = _segments(record)
            references = _reference_segments(
                segments, subject_members, treatment_declared
            )
            treatment_reference_qualified = {
                subject: _connected_anchor_graph(
                    subject_members[subject], references[subject]
                )
                for subject in subjects
            }
            treatment_graphs = {
                subject: _anchor_graph_record(
                    subject_members[subject], references[subject]
                )
                for subject in subjects
            }
            all_anchors = set().union(*subject_members.values())
            treatment_evidence = {
                "reference_qualified": treatment_reference_qualified,
                "reference_graphs": treatment_graphs,
                "anchor_projection": _anchor_projection(segments, all_anchors),
                "complete_output": {
                    "segments": [sorted(segment) for segment in segments],
                    "unassigned": sorted(_unassigned(record)),
                },
                "unsupported_auxiliary_segments": _unsupported_auxiliary_segments(
                    segments, subject_members, {control, mixed}
                ),
            }
        if not baseline_eligible:
            treatment_results[mixed] = {
                "verdict": "no_verdict",
                "reason": "anchor-only baseline integrity failed",
                "baseline_integrity_reason": _integrity_reason(baseline),
                **treatment_identity,
                **treatment_evidence,
            }
            continue
        if not all(reference_qualified.values()):
            treatment_results[mixed] = {
                "verdict": "no_verdict",
                "reason": "local baseline reference prerequisite failed",
                **treatment_identity,
                **treatment_evidence,
            }
            continue
        if not control_qualified[control]:
            treatment_results[mixed] = {
                "verdict": "no_verdict",
                "reason": "local control profile prerequisite failed",
                **treatment_identity,
                **treatment_evidence,
            }
            continue
        if not _eligible(record):
            treatment_results[mixed] = {
                "verdict": "no_verdict",
                "reason": _integrity_reason(record),
                **treatment_identity,
            }
            continue
        if not all(treatment_reference_qualified.values()):
            treatment_results[mixed] = {
                "verdict": "no_verdict",
                "reason": "local treatment reference prerequisite failed",
                **treatment_identity,
                **treatment_evidence,
            }
            continue
        control_profile = _relationship_profile(
            control, subjects, segments, references, treatment_declared
        )
        if control_profile != baseline_profiles[control]:
            treatment_results[mixed] = {
                "verdict": "no_verdict",
                "reason": "local control displacement prerequisite failed",
                **treatment_identity,
                "control_profile": control_profile,
                "baseline_control_profile": baseline_profiles[control],
                **treatment_evidence,
            }
            continue
        mixed_profile = _relationship_profile(
            mixed, subjects, segments, references, treatment_declared
        )
        gained = [
            subject
            for subject, before, after in zip(
                subjects, baseline_profiles[control], mixed_profile, strict=True
            )
            if not before and after
        ]
        lost = [
            subject
            for subject, before, after in zip(
                subjects, baseline_profiles[control], mixed_profile, strict=True
            )
            if before and not after
        ]
        relationship_changes = []
        for direction, changed_subjects in (("gained", gained), ("lost", lost)):
            for subject in changed_subjects:
                relationship_changes.append(
                    {
                        "direction": direction,
                        "subject": subject,
                        "classification": (
                            "masked_subject"
                            if subject == target
                            else (
                                "matching_context"
                                if subject == context
                                else "other_subject"
                            )
                        ),
                    }
                )
        treatment_results[mixed] = {
            "verdict": (
                "pass"
                if mixed_profile == baseline_profiles[control]
                else "context_membership_change_failure"
            ),
            **treatment_identity,
            "baseline_control_profile": baseline_profiles[control],
            "control_profile": control_profile,
            "mixed_profile": mixed_profile,
            "gained": gained,
            "lost": lost,
            "relationship_changes": relationship_changes,
            **treatment_evidence,
            "mixed_supporting_segments": [
                sorted(segment) for segment in segments if mixed in segment
            ],
        }
    verdicts = [row["verdict"] for row in treatment_results.values()]
    if "context_membership_change_failure" in verdicts:
        overall = "context_membership_change_failure"
    elif verdicts and all(value == "pass" for value in verdicts):
        overall = "pass"
    else:
        overall = "no_verdict"

    def pattern(dimension: str) -> list[dict[str, object]]:
        values = sorted(
            {
                str(row.get(dimension))
                for row in treatment_results.values()
                if row.get(dimension) is not None
            }
        )
        result = []
        for value in values:
            rows = [
                row
                for row in treatment_results.values()
                if str(row.get(dimension)) == value
            ]
            changes = Counter(
                str(change["classification"])
                for row in rows
                for change in row.get("relationship_changes", [])
            )
            result.append(
                {
                    dimension: value,
                    "treatment_count": len(rows),
                    "verdict_counts": dict(
                        sorted(Counter(str(row["verdict"]) for row in rows).items())
                    ),
                    "relationship_change_counts": dict(sorted(changes.items())),
                }
            )
        return result

    return {
        "baseline": {
            "qualified": all(reference_qualified.values())
            and all(control_qualified.values()),
            "reference_qualified": reference_qualified,
            "reference_graphs": baseline_graphs,
            "control_profiles": baseline_profiles,
            "control_qualified": control_qualified,
            "anchor_projection": _anchor_projection(
                baseline_segments, set().union(*subject_members.values())
            ),
            "complete_output": {
                "segments": [sorted(segment) for segment in baseline_segments],
                "unassigned": sorted(_unassigned(baseline)),
            },
            "unsupported_auxiliary_segments": _unsupported_auxiliary_segments(
                baseline_segments, subject_members, set(controls.values())
            ),
            "integrity_reason": (
                None if baseline_eligible else _integrity_reason(baseline)
            ),
        },
        "treatments": treatment_results,
        "diagnostic_patterns": {
            "by_context_subject": pattern("context_subject"),
            "by_masked_subject": pattern("target_subject"),
            "by_outer_form": pattern("outer_form"),
        },
        "overall_verdict": overall,
    }


def _support_role(condition: str, count: int) -> str:
    if condition == "balanced":
        return "balanced-4"
    if condition == "dense-singleton":
        return f"dense-singleton-{count}"
    return f"{condition}-{count}"


def _experiment_02_projection(
    balanced: Mapping[str, object], unequal: Mapping[str, object]
) -> dict[str, object]:
    balanced_members = {
        member
        for subject in balanced["subjects"].values()
        for member in subject["members"]
    }
    unequal_members = {
        member
        for subject in unequal["subjects"].values()
        for member in subject["members"]
    }
    shared = balanced_members & unequal_members
    global_order = balanced.get("input_member_order")
    if not isinstance(global_order, list) or set(global_order) != balanced_members:
        raise ValueError("balanced configuration lacks its frozen global member order")
    shared_order = [member for member in global_order if member in shared]
    shared_rank = {member: ordinal for ordinal, member in enumerate(shared_order)}
    balanced_projection = canonical_projection(
        balanced["complete_output"]["segments"],
        shared,
        global_order=global_order,
    )
    unequal_projection = canonical_projection(
        unequal["complete_output"]["segments"],
        shared,
        global_order=global_order,
    )

    def provenance(configuration: Mapping[str, object]) -> list[dict[str, object]]:
        rows = []
        for ordinal, source_segment in enumerate(
            configuration["complete_output"]["segments"], start=1
        ):
            projected = sorted(
                set(source_segment) & shared,
                key=shared_rank.__getitem__,
            )
            if not projected:
                continue
            rows.append(
                {
                    "source_configuration_id": configuration["configuration_id"],
                    "source_segment_ordinal": ordinal,
                    "source_segment": list(source_segment),
                    "projected_members": projected,
                    "source_invocation_record_ids": list(
                        configuration["invocation_record_ids"]
                    ),
                }
            )
        return rows

    keys = sorted(set(balanced_projection) | set(unequal_projection))
    return {
        "shared_ids": shared_order,
        "balanced_multiset": [
            {"members": list(key), "count": balanced_projection[key]}
            for key in sorted(balanced_projection)
        ],
        "unequal_multiset": [
            {"members": list(key), "count": unequal_projection[key]}
            for key in sorted(unequal_projection)
        ],
        "signed_difference_unequal_minus_balanced": [
            {
                "members": list(key),
                "difference": unequal_projection[key] - balanced_projection[key],
            }
            for key in keys
        ],
        "balanced_provenance": provenance(balanced),
        "unequal_provenance": provenance(unequal),
    }


def characterize_experiment_02(
    inputs: Sequence[Mapping[str, object]],
    outputs: Mapping[str, Mapping[str, object]],
    encodings: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    """Produce machine-defined Experiment 2 outcomes and matched comparisons."""

    configuration_results: dict[str, dict[str, object]] = {}
    balanced_by_key: dict[tuple[str, int], str] = {}
    input_by_id = {str(item["input_id"]): item for item in inputs}
    for specification in inputs:
        input_id = str(specification["input_id"])
        metadata = specification["metadata"]
        neighborhood = str(metadata["neighborhood"])
        schedule = int(metadata["schedule"])
        condition = str(metadata["condition"])
        if condition == "balanced":
            balanced_by_key[(neighborhood, schedule)] = input_id
        members = [str(item) for item in specification["readable_members"]]
        subject_by_member = {
            member: str(encodings[member]["metadata"]["subject_code"])
            for member in members
        }
        form_by_member = {
            member: str(encodings[member]["metadata"].get("form", "unknown"))
            for member in members
        }
        support = Counter(subject_by_member.values())
        record = outputs.get(input_id)
        row: dict[str, object] = {
            "configuration_id": input_id,
            "neighborhood": neighborhood,
            "schedule": schedule,
            "condition": condition,
            "allocation": list(metadata["allocation"]),
            "eligible": _eligible(record),
            "integrity_failure": (
                None if _eligible(record) else _integrity_reason(record)
            ),
            "invocation_record_ids": (
                list(record.get("invocation_record_ids", [])) if record else []
            ),
            "invocations": list(record.get("invocations", [])) if record else [],
            "canonical_output_sha256": (
                record.get("canonical_output_sha256") if record else None
            ),
            "input_member_order": list(specification["readable_members"]),
            "opaque_id_by_readable": dict(
                zip(
                    specification["readable_members"],
                    specification["opaque_ids"],
                    strict=True,
                )
            ),
        }
        if not _eligible(record):
            unavailable_subjects = {}
            for subject in metadata["subjects"]:
                subject = str(subject)
                cohort = {
                    member for member in members if subject_by_member[member] == subject
                }
                unavailable_subjects[subject] = {
                    "support_count": len(cohort),
                    "support_role": _support_role(condition, len(cohort)),
                    "members": sorted(cohort),
                    "reference_cohort_recovered": "unavailable",
                    "partial_same_subject_segments": [],
                    "singleton_disposition": (
                        {
                            "member": next(iter(cohort)),
                            "singleton_segment_exists": "unavailable",
                            "has_no_membership": "unavailable",
                            "multi_member_segments": [],
                            "invalid_membership": "unavailable",
                        }
                        if len(cohort) == 1
                        else None
                    ),
                }
            row.update(
                {
                    "subjects": unavailable_subjects,
                    "omissions": [],
                    "same_subject_segments": [],
                    "cross_subject_occurrences": [],
                    "has_omission": "not_available",
                    "has_fragmentation": "not_available",
                }
            )
            configuration_results[input_id] = row
            continue
        segments = _segments(record)
        unassigned = _unassigned(record)
        segment_wording_diagnostics = []
        canonical_forms = {"A", "C", "E", "G"}
        equivalent_forms = {"B", "D", "F", "H"}
        for ordinal, segment in enumerate(segments, start=1):
            forms = [form_by_member[member] for member in sorted(segment)]
            strata = sorted(
                {
                    (
                        "canonical"
                        if form in canonical_forms
                        else (
                            "equivalent-paraphrase"
                            if form in equivalent_forms
                            else "unknown"
                        )
                    )
                    for form in forms
                }
            )
            form_counts = Counter(forms)
            segment_wording_diagnostics.append(
                {
                    "source_segment_ordinal": ordinal,
                    "members": sorted(segment),
                    "wording_forms": forms,
                    "wording_strata": strata,
                    "crosses_canonical_and_equivalent_paraphrase": (
                        "canonical" in strata and "equivalent-paraphrase" in strata
                    ),
                    "shared_wording_forms": sorted(
                        form for form, count in form_counts.items() if count > 1
                    ),
                }
            )
        subjects = {}
        same_subject_segments = []
        for subject in metadata["subjects"]:
            subject = str(subject)
            cohort = {
                member for member in members if subject_by_member[member] == subject
            }
            complete = cohort in segments if len(cohort) >= 2 else None
            partial = sorted(
                [
                    sorted(segment)
                    for segment in segments
                    if segment and segment.issubset(cohort) and segment != cohort
                ]
            )
            for segment in segments:
                if segment and segment.issubset(cohort):
                    same_subject_segments.append(
                        {
                            "subject": subject,
                            "members": sorted(segment),
                            "complete": segment == cohort,
                        }
                    )
            singleton = None
            if len(cohort) == 1:
                member = next(iter(cohort))
                joined = [
                    sorted(segment)
                    for segment in segments
                    if member in segment and len(segment) > 1
                ]
                singleton = {
                    "member": member,
                    "singleton_segment_exists": {member} in segments,
                    "has_no_membership": member in unassigned,
                    "multi_member_segments": joined,
                    "invalid_membership": (
                        "pending_semantic_review" if joined else False
                    ),
                }
            subjects[subject] = {
                "support_count": len(cohort),
                "support_role": _support_role(condition, len(cohort)),
                "members": sorted(cohort),
                "reference_cohort_recovered": complete,
                "partial_same_subject_segments": partial,
                "singleton_disposition": singleton,
            }
        cross_occurrences = []
        opaque_by_readable = dict(
            zip(
                specification["readable_members"],
                specification["opaque_ids"],
                strict=True,
            )
        )
        for segment in segments:
            segment_subjects = {subject_by_member[member] for member in segment}
            if len(segment_subjects) < 2:
                continue
            cross_occurrences.append(
                {
                    "configuration_id": input_id,
                    "readable_members": sorted(segment),
                    "opaque_members": [
                        opaque_by_readable[member] for member in sorted(segment)
                    ],
                    "member_roles": {
                        member: {
                            "subject": subject_by_member[member],
                            "support_count": support[subject_by_member[member]],
                            "support_role": _support_role(
                                condition, support[subject_by_member[member]]
                            ),
                        }
                        for member in sorted(segment)
                    },
                    "shared_wording_forms": next(
                        row["shared_wording_forms"]
                        for row in segment_wording_diagnostics
                        if row["members"] == sorted(segment)
                    ),
                    "review": "pending",
                }
            )
        row.update(
            {
                "subjects": subjects,
                "omissions": sorted(unassigned),
                "same_subject_segments": same_subject_segments,
                "cross_subject_occurrences": cross_occurrences,
                "segment_wording_diagnostics": segment_wording_diagnostics,
                "has_omission": bool(unassigned),
                "has_fragmentation": any(
                    value["partial_same_subject_segments"]
                    for value in subjects.values()
                ),
                "complete_output": {
                    "segments": [sorted(segment) for segment in segments],
                    "unassigned": sorted(unassigned),
                },
            }
        )
        configuration_results[input_id] = row

    comparisons = []
    for unequal_id, specification in input_by_id.items():
        metadata = specification["metadata"]
        if metadata["condition"] == "balanced":
            continue
        subject_survival = []
        balanced_id = balanced_by_key[
            (str(metadata["neighborhood"]), int(metadata["schedule"]))
        ]
        balanced = configuration_results[balanced_id]
        unequal = configuration_results[unequal_id]
        if not balanced["eligible"] or not unequal["eligible"]:
            projection = None
            projection_state = "unavailable"
            projection_dependency_failures = [
                {
                    "configuration_id": configuration["configuration_id"],
                    "integrity_failure": configuration["integrity_failure"],
                }
                for configuration in (balanced, unequal)
                if not configuration["eligible"]
            ]
        else:
            projection = _experiment_02_projection(balanced, unequal)
            projection_state = "available"
            projection_dependency_failures = []
        for subject in metadata["subjects"]:
            subject = str(subject)
            support_count = unequal["subjects"].get(subject, {}).get("support_count")
            if support_count == 1:
                verdict = "not_applicable_singleton"
                reason = None
            elif not balanced["eligible"] or not unequal["eligible"]:
                verdict = "unavailable"
                reason = "; ".join(
                    f"{failure['configuration_id']}: {failure['integrity_failure']}"
                    for failure in projection_dependency_failures
                )
            elif not balanced["subjects"][subject]["reference_cohort_recovered"]:
                verdict = "unavailable"
                reason = "matched balanced baseline did not recover"
            else:
                verdict = (
                    "survived"
                    if unequal["subjects"][subject]["reference_cohort_recovered"]
                    else "did_not_survive"
                )
                reason = None
            subject_survival.append(
                {
                    "subject": subject,
                    "support_count": support_count,
                    "support_role": unequal["subjects"]
                    .get(subject, {})
                    .get("support_role"),
                    "matched_baseline_recovered": (
                        balanced["subjects"]
                        .get(subject, {})
                        .get("reference_cohort_recovered")
                    ),
                    "verdict": verdict,
                    "reason": reason,
                }
            )
        comparisons.append(
            {
                "balanced_configuration_id": balanced_id,
                "unequal_configuration_id": unequal_id,
                "projection_state": projection_state,
                "projection": projection,
                "projection_dependency_failures": projection_dependency_failures,
                "subject_survival": subject_survival,
            }
        )
    role_form_counts: dict[str, Counter[str]] = {}
    for configuration in configuration_results.values():
        for subject in configuration["subjects"].values():
            role = str(subject["support_role"])
            counter = role_form_counts.setdefault(role, Counter())
            for member in subject["members"]:
                counter[str(encodings[member]["metadata"].get("form", "unknown"))] += 1
    return {
        "configurations": configuration_results,
        "comparisons": comparisons,
        "support_role_by_wording_form": {
            role: dict(sorted(counts.items()))
            for role, counts in sorted(role_form_counts.items())
        },
    }


def _review_class(review: object) -> str:
    if isinstance(review, dict):
        verdict = review.get("verdict")
        if verdict in {"valid", "invalid", "uncertain"}:
            return str(verdict)
    return "unavailable"


def _summary_metrics(
    configurations: Sequence[Mapping[str, object]],
    comparisons: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    eligible = [row for row in configurations if row["eligible"]]
    survival_rows = [
        row
        for comparison in comparisons
        for row in comparison["subject_survival"]
        if row["verdict"] != "not_applicable_singleton"
    ]
    occurrences = [
        occurrence
        for row in eligible
        for occurrence in row["cross_subject_occurrences"]
    ]
    classes = Counter(_review_class(item.get("review")) for item in occurrences)
    return {
        "total_configurations": len(configurations),
        "eligible_configurations": len(eligible),
        "total_projected_comparisons": (
            len(comparisons) if comparisons else "not_applicable"
        ),
        "eligible_projected_comparisons": (
            sum(row["projection_state"] == "available" for row in comparisons)
            if comparisons
            else "not_applicable"
        ),
        "unavailable_projected_comparisons": (
            sum(row["projection_state"] != "available" for row in comparisons)
            if comparisons
            else "not_applicable"
        ),
        "total_survival_comparisons": (
            len(survival_rows) if comparisons else "not_applicable"
        ),
        "matched_baselines_recovered": (
            sum(row["matched_baseline_recovered"] is True for row in survival_rows)
            if comparisons
            else "not_applicable"
        ),
        "survived": (
            sum(row["verdict"] == "survived" for row in survival_rows)
            if comparisons
            else "not_applicable"
        ),
        "did_not_survive": (
            sum(row["verdict"] == "did_not_survive" for row in survival_rows)
            if comparisons
            else "not_applicable"
        ),
        "unavailable_survival_comparisons": (
            sum(row["verdict"] == "unavailable" for row in survival_rows)
            if comparisons
            else "not_applicable"
        ),
        "eligible_configurations_with_omission": sum(
            row["has_omission"] is True for row in eligible
        ),
        "eligible_configurations_with_fragmentation": sum(
            row["has_fragmentation"] is True for row in eligible
        ),
        "eligible_cross_subject_occurrences": len(occurrences),
        "cross_subject_valid": classes["valid"],
        "cross_subject_invalid": classes["invalid"],
        "cross_subject_uncertain": classes["uncertain"],
        "cross_subject_unavailable": classes["unavailable"],
        "configuration_ids": sorted(
            str(row["configuration_id"]) for row in configurations
        ),
    }


def build_experiment_02_summaries(
    characterization: Mapping[str, object],
) -> dict[str, object]:
    """Build all three mandatory summary tables with explicit denominators."""

    configurations = list(characterization["configurations"].values())
    comparisons = list(characterization["comparisons"])
    by_unequal = {row["unequal_configuration_id"]: row for row in comparisons}

    neighborhood_condition = []
    neighborhood_conditions = sorted(
        {(row["neighborhood"], row["condition"]) for row in configurations}
    )
    for neighborhood, condition in neighborhood_conditions:
        rows = [
            row
            for row in configurations
            if row["neighborhood"] == neighborhood and row["condition"] == condition
        ]
        relevant = [
            by_unequal[row["configuration_id"]]
            for row in rows
            if row["configuration_id"] in by_unequal
        ]
        neighborhood_condition.append(
            {
                "neighborhood": neighborhood,
                "condition": condition,
                **_summary_metrics(rows, relevant),
            }
        )

    schedule = []
    for schedule_index in sorted({int(row["schedule"]) for row in configurations}):
        rows = [row for row in configurations if row["schedule"] == schedule_index]
        relevant = [
            by_unequal[row["configuration_id"]]
            for row in rows
            if row["configuration_id"] in by_unequal
        ]
        schedule.append(
            {"schedule": schedule_index, **_summary_metrics(rows, relevant)}
        )

    role_rows: dict[str, list[tuple[Mapping[str, object], Mapping[str, object]]]] = {}
    for configuration in configurations:
        for subject in configuration["subjects"].values():
            role_rows.setdefault(str(subject["support_role"]), []).append(
                (configuration, subject)
            )
    survival_by_key = {
        (comparison["unequal_configuration_id"], row["subject"]): row
        for comparison in comparisons
        for row in comparison["subject_survival"]
    }
    by_role = []
    for role, rows in sorted(role_rows.items()):
        comparison_rows = [
            survival_by_key[(configuration["configuration_id"], subject_name)]
            for configuration, subject in rows
            for subject_name, candidate_subject in configuration["subjects"].items()
            if candidate_subject is subject
            and (configuration["configuration_id"], subject_name) in survival_by_key
        ]
        applicable = [
            row
            for row in comparison_rows
            if row["verdict"] != "not_applicable_singleton"
        ]
        occurrence_ids = {
            (
                configuration["configuration_id"],
                tuple(occurrence["readable_members"]),
            )
            for configuration, subject in rows
            for occurrence in configuration["cross_subject_occurrences"]
            if any(
                occurrence["member_roles"][member]["support_role"] == role
                for member in occurrence["readable_members"]
            )
        }
        role_occurrences = {
            (
                configuration["configuration_id"],
                tuple(occurrence["readable_members"]),
            ): occurrence
            for configuration, _ in rows
            for occurrence in configuration["cross_subject_occurrences"]
            if any(
                occurrence["member_roles"][member]["support_role"] == role
                for member in occurrence["readable_members"]
            )
        }
        role_classes = Counter(
            _review_class(occurrence.get("review"))
            for occurrence in role_occurrences.values()
        )
        by_role.append(
            {
                "support_role": role,
                "total_subject_occurrences": len(rows),
                "eligible_subject_occurrences": sum(
                    configuration["eligible"] for configuration, _ in rows
                ),
                "total_projected_comparisons": "not_applicable",
                "eligible_projected_comparisons": "not_applicable",
                "unavailable_projected_comparisons": "not_applicable",
                "total_survival_comparisons": (
                    len(applicable) if applicable else "not_applicable"
                ),
                "matched_baselines_recovered": (
                    sum(row["matched_baseline_recovered"] is True for row in applicable)
                    if applicable
                    else "not_applicable"
                ),
                "survived": (
                    sum(row["verdict"] == "survived" for row in applicable)
                    if applicable
                    else "not_applicable"
                ),
                "did_not_survive": (
                    sum(row["verdict"] == "did_not_survive" for row in applicable)
                    if applicable
                    else "not_applicable"
                ),
                "unavailable_survival_comparisons": (
                    sum(row["verdict"] == "unavailable" for row in applicable)
                    if applicable
                    else "not_applicable"
                ),
                "eligible_configurations_with_omission": "not_applicable",
                "eligible_configurations_with_fragmentation": "not_applicable",
                "cross_subject_occurrence_role_incidences": len(occurrence_ids),
                "cross_subject_valid": role_classes["valid"],
                "cross_subject_invalid": role_classes["invalid"],
                "cross_subject_uncertain": role_classes["uncertain"],
                "cross_subject_unavailable": role_classes["unavailable"],
                "configuration_ids": sorted(
                    {
                        str(configuration["configuration_id"])
                        for configuration, _ in rows
                    }
                ),
            }
        )
    return {
        "by_neighborhood_and_condition": neighborhood_condition,
        "by_exact_support_role": by_role,
        "by_schedule": schedule,
    }


def bind_experiment_02_review(
    characterization: dict[str, object], review: Mapping[str, object]
) -> None:
    """Bind every eligible cross-subject occurrence to its reused packet."""

    packet_by_members = {
        tuple(packet["canonical_opaque_members"]): packet["packet"]
        for packet in review["internal_packets"]
    }
    for configuration in characterization["configurations"].values():
        for occurrence in configuration["cross_subject_occurrences"]:
            key = tuple(sorted(occurrence["opaque_members"]))
            packet = packet_by_members.get(key)
            if packet is None:
                raise ValueError(
                    "eligible cross-subject occurrence has no review packet"
                )
            if review["status"] == "review_capacity_failure":
                occurrence["review"] = {
                    "packet": packet,
                    "verdict": "unavailable",
                    "reason": "review_capacity_failure",
                }
            else:
                occurrence["review"] = {
                    "packet": packet,
                    "verdict": "pending",
                    "reason": "primary human review not yet supplied",
                }
        _refresh_singleton_review_dispositions(configuration)


def _refresh_singleton_review_dispositions(
    configuration: Mapping[str, object],
) -> None:
    review_by_members = {
        tuple(sorted(occurrence["readable_members"])): occurrence["review"]
        for occurrence in configuration["cross_subject_occurrences"]
    }
    for subject in configuration["subjects"].values():
        singleton = subject.get("singleton_disposition")
        if not isinstance(singleton, dict):
            continue
        joined = singleton.get("multi_member_segments")
        if not isinstance(joined, list) or not joined:
            singleton["invalid_membership"] = False
            continue
        states = []
        for members in joined:
            bound = review_by_members.get(tuple(sorted(members)))
            if bound is None:
                raise ValueError("singleton membership has no semantic-review binding")
            states.append(bound.get("verdict"))
        if "invalid" in states:
            singleton["invalid_membership"] = True
        elif "uncertain" in states:
            singleton["invalid_membership"] = "uncertain"
        elif "unavailable" in states:
            singleton["invalid_membership"] = "unavailable"
        elif "pending" in states:
            singleton["invalid_membership"] = "pending_semantic_review"
        elif states and all(state == "valid" for state in states):
            singleton["invalid_membership"] = False
        else:
            raise ValueError("singleton review binding has an invalid verdict")


def build_experiment_02_exceptions(
    characterization: Mapping[str, object],
) -> dict[str, list[dict[str, object]]]:
    """Enumerate every record the final reviewer must explicitly address."""

    exceptions: dict[str, list[dict[str, object]]] = {
        "integrity_failures": [],
        "omissions": [],
        "fragmentation": [],
        "did_not_survive": [],
        "unavailable_survival": [],
        "invalid_cross_subject": [],
        "uncertain_cross_subject": [],
        "unavailable_cross_subject": [],
    }
    for configuration in characterization["configurations"].values():
        configuration_id = configuration["configuration_id"]
        if not configuration["eligible"]:
            exceptions["integrity_failures"].append(
                {
                    "configuration_id": configuration_id,
                    "reason": configuration["integrity_failure"],
                }
            )
            continue
        if configuration["has_omission"]:
            exceptions["omissions"].append(
                {
                    "configuration_id": configuration_id,
                    "members": configuration["omissions"],
                }
            )
        if configuration["has_fragmentation"]:
            exceptions["fragmentation"].append(
                {
                    "configuration_id": configuration_id,
                    "same_subject_segments": configuration["same_subject_segments"],
                }
            )
        for occurrence in configuration["cross_subject_occurrences"]:
            review = occurrence["review"]
            row = {
                "configuration_id": configuration_id,
                "members": occurrence["readable_members"],
                "packet": review["packet"],
                "reason": review.get("reason"),
            }
            verdict = review["verdict"]
            if verdict == "invalid":
                exceptions["invalid_cross_subject"].append(row)
            elif verdict == "uncertain":
                exceptions["uncertain_cross_subject"].append(row)
            elif verdict in {"unavailable", "pending"}:
                exceptions["unavailable_cross_subject"].append(row)
    for comparison in characterization["comparisons"]:
        for survival in comparison["subject_survival"]:
            row = {
                "balanced_configuration_id": comparison["balanced_configuration_id"],
                "unequal_configuration_id": comparison["unequal_configuration_id"],
                "subject": survival["subject"],
                "support_role": survival["support_role"],
                "reason": survival["reason"],
            }
            if survival["verdict"] == "did_not_survive":
                exceptions["did_not_survive"].append(row)
            elif survival["verdict"] == "unavailable":
                exceptions["unavailable_survival"].append(row)
    ordinal = 1
    for category, rows in exceptions.items():
        rows.sort(key=_canonical_json)
        for row in rows:
            row["exception_id"] = f"E{ordinal:06d}"
            row["category"] = category
            ordinal += 1
    return exceptions


def apply_semantic_review_response(
    evidence: Mapping[str, object],
    review_set: str,
    response: Mapping[str, object],
) -> dict[str, object]:
    """Apply only the primary reviewer's supplied packet judgments."""

    reviewed = copy.deepcopy(evidence)
    experiment = reviewed.get("experiment_02")
    if not isinstance(experiment, dict):
        raise ValueError("candidate evidence has no Experiment 2 result")
    review = experiment.get("review")
    coverage = experiment.get("coverage_manifest")
    frozen_inputs = experiment.get("frozen_inputs")
    frozen_encodings = experiment.get("frozen_encodings")
    expected_configuration_ids = experiment.get("frozen_expected_configuration_ids")
    expected_unequal_configuration_ids = experiment.get(
        "frozen_expected_unequal_configuration_ids"
    )
    if (
        not isinstance(review, dict)
        or not isinstance(coverage, dict)
        or not isinstance(frozen_inputs, list)
        or not isinstance(frozen_encodings, dict)
        or not isinstance(expected_configuration_ids, list)
        or not all(isinstance(value, str) for value in expected_configuration_ids)
        or not isinstance(expected_unequal_configuration_ids, list)
        or not all(
            isinstance(value, str) for value in expected_unequal_configuration_ids
        )
    ):
        raise ValueError(
            "candidate evidence is missing frozen Experiment 2 coverage inputs"
        )
    judgments = validate_semantic_review_response(review, review_set, response)
    for packet in review["internal_packets"]:
        packet_id = str(packet["packet"])
        judgment = judgments[packet_id]
        packet["review_state"] = "completed"
        packet["verdict"] = judgment["verdict"]
        packet["fine_subject"] = judgment["fine_subject"]
    configurations = {
        str(configuration["configuration_id"]): configuration
        for configuration in coverage["configurations"]
    }
    for configuration in configurations.values():
        for occurrence in configuration["cross_subject_occurrences"]:
            packet_id = str(occurrence["review"]["packet"])
            judgment = judgments.get(packet_id)
            if judgment is None:
                raise ValueError(
                    "cross-subject occurrence references an unreviewed packet"
                )
            occurrence["review"] = {
                "packet": packet_id,
                "verdict": judgment["verdict"],
                "fine_subject": judgment["fine_subject"],
                "reason": None,
            }
        _refresh_singleton_review_dispositions(configuration)
    characterization = {
        "configurations": configurations,
        "comparisons": coverage["comparisons"],
    }
    summaries = build_experiment_02_summaries(characterization)
    exceptions = build_experiment_02_exceptions(characterization)
    validation = validate_experiment_02_coverage(
        coverage,
        frozen_inputs=frozen_inputs,
        frozen_encodings=frozen_encodings,
        expected_configuration_ids=expected_configuration_ids,
        expected_unequal_configuration_ids=expected_unequal_configuration_ids,
        mandatory_summaries=summaries,
        exceptions=exceptions,
    )
    review["status"] = "completed"
    review["semantic_review_response_sha256"] = hashlib.sha256(
        _canonical_json(response)
    ).hexdigest()
    experiment["mandatory_summaries"] = summaries
    experiment["exceptions"] = exceptions
    experiment["coverage_validation"] = validation
    required_exception_ids = [
        row["exception_id"] for rows in exceptions.values() for row in rows
    ]
    experiment["decision_response_contract"] = {
        "schema_version": SCHEMA_VERSION,
        "allowed_candidate_dispositions": ["proceed", "revise candidate", "stop"],
        "required_fields": [
            "schema_version",
            "candidate_disposition",
            "written_rationale",
            "exception_dispositions",
        ],
        "exception_disposition_fields": [
            "exception_id",
            "blocks_proceed",
            "rationale",
        ],
        "required_exception_ids": required_exception_ids,
        "proceed_rule": (
            "every required exception must have blocks_proceed=false; the final "
            "candidate choice remains reserved for the user"
        ),
    }
    experiment["report_completeness"] = {
        "coverage_structurally_complete": True,
        "semantic_review_complete": True,
        "exception_dispositions_complete": False,
        "written_rationale_complete": False,
        "proceed_eligible": False,
        "reason": "candidate disposition and required written rationales are pending",
    }
    reviewed["review_status"] = "completed"
    reviewed["user_disposition"] = "pending"
    reviewed["candidate_selection"] = "reserved_for_user"
    return reviewed


def finalize_candidate_disposition(
    reviewed_evidence: Mapping[str, object],
    response: Mapping[str, object],
) -> dict[str, object]:
    """Validate and record a user-supplied candidate disposition and rationales."""

    finalized = copy.deepcopy(reviewed_evidence)
    experiment = finalized.get("experiment_02")
    review_status = finalized.get("review_status")
    if not isinstance(experiment, dict) or review_status not in {
        "completed",
        "review_capacity_failure",
        "not_available",
    }:
        raise ValueError("candidate evidence is not ready for a disposition")
    coverage = experiment.get("coverage_manifest")
    summaries = experiment.get("mandatory_summaries")
    exceptions = experiment.get("exceptions")
    frozen_inputs = experiment.get("frozen_inputs")
    frozen_encodings = experiment.get("frozen_encodings")
    expected_configuration_ids = experiment.get("frozen_expected_configuration_ids")
    expected_unequal_configuration_ids = experiment.get(
        "frozen_expected_unequal_configuration_ids"
    )
    if review_status in {"completed", "review_capacity_failure"}:
        if (
            not all(
                isinstance(value, dict) for value in (coverage, summaries, exceptions)
            )
            or not isinstance(frozen_inputs, list)
            or not isinstance(frozen_encodings, dict)
            or not isinstance(expected_configuration_ids, list)
            or not all(isinstance(value, str) for value in expected_configuration_ids)
            or not isinstance(expected_unequal_configuration_ids, list)
            or not all(
                isinstance(value, str) for value in expected_unequal_configuration_ids
            )
        ):
            raise ValueError(
                "candidate result is missing coverage, summaries, or exceptions"
            )
        validate_experiment_02_coverage(
            coverage,
            frozen_inputs=frozen_inputs,
            frozen_encodings=frozen_encodings,
            expected_configuration_ids=expected_configuration_ids,
            expected_unequal_configuration_ids=expected_unequal_configuration_ids,
            mandatory_summaries=summaries,
            exceptions=exceptions,
        )
    elif not isinstance(summaries, dict) or not isinstance(exceptions, dict):
        raise ValueError("unavailable candidate lacks its retained exception evidence")
    contract = experiment.get("decision_response_contract")
    if not isinstance(contract, dict):
        raise ValueError("candidate evidence is missing its decision-response contract")
    required_fields = set(contract["required_fields"])
    if (
        set(response) != required_fields
        or response.get("schema_version") != SCHEMA_VERSION
    ):
        raise ValueError("candidate disposition response has the wrong schema")
    disposition = response.get("candidate_disposition")
    if disposition not in contract["allowed_candidate_dispositions"]:
        raise ValueError("candidate disposition is invalid")
    written_rationale = response.get("written_rationale")
    if not isinstance(written_rationale, str) or not written_rationale.strip():
        raise ValueError("candidate disposition requires a written rationale")
    rows = response.get("exception_dispositions")
    if not isinstance(rows, list):
        raise ValueError("candidate disposition lacks exception dispositions")
    by_id: dict[str, dict[str, object]] = {}
    expected_fields = set(contract["exception_disposition_fields"])
    for row in rows:
        if not isinstance(row, dict) or set(row) != expected_fields:
            raise ValueError("exception disposition has the wrong schema")
        exception_id = row.get("exception_id")
        rationale = row.get("rationale")
        if (
            not isinstance(exception_id, str)
            or exception_id in by_id
            or not isinstance(row.get("blocks_proceed"), bool)
            or not isinstance(rationale, str)
            or not rationale.strip()
        ):
            raise ValueError("exception disposition is incomplete")
        by_id[exception_id] = dict(row)
    if set(by_id) != set(contract["required_exception_ids"]):
        raise ValueError(
            "candidate disposition does not address every required exception"
        )
    if disposition == "proceed" and any(
        row["blocks_proceed"] for row in by_id.values()
    ):
        raise ValueError(
            "proceed is incompatible with a blocking exception disposition"
        )
    experiment["primary_reviewer_decision"] = copy.deepcopy(response)
    experiment["report_completeness"] = {
        "coverage_structurally_complete": review_status != "not_available",
        "semantic_review_complete": review_status == "completed",
        "exception_dispositions_complete": True,
        "written_rationale_complete": True,
        "proceed_eligible": review_status == "completed" and disposition == "proceed",
        "reason": (
            None
            if review_status == "completed"
            else experiment.get("review", {}).get("unavailable_reason")
            or "semantic review was unavailable"
        ),
    }
    finalized["user_disposition"] = disposition
    finalized["candidate_selection"] = "reserved_for_user"
    return finalized


def _experiment_01_cohorts(protocol: Mapping[str, object]) -> dict[str, set[str]]:
    cohorts: dict[str, set[str]] = {}
    for encoding in protocol["encodings"]:
        if encoding["experiment"] != "experiment-01":
            continue
        code = str(encoding["metadata"]["subject_code"])
        cohorts.setdefault(code, set()).add(str(encoding["readable_id"]))
    return cohorts


def _remap_record(
    record: Mapping[str, object], mapping: Mapping[str, str]
) -> dict[str, object]:
    return {
        **record,
        "segments": [
            [mapping.get(member, member) for member in segment]
            for segment in record["segments"]
        ],
        "unassigned": [mapping.get(member, member) for member in record["unassigned"]],
        "input_member_order": [
            mapping.get(member, member)
            for member in record.get("input_member_order", [])
        ],
    }


def build_candidate_evidence(
    protocol: Mapping[str, object],
    outputs: Mapping[str, Mapping[str, object]],
    *,
    candidate_identity: str,
    review_seed: bytes,
) -> dict[str, object]:
    """Score one complete candidate record and prepare its pending review."""

    default = outputs.get("experiment-01/default")
    alternate = outputs.get("candidate-conformance/alternate-order")

    def conformance_input(
        input_id: str, record: Mapping[str, object] | None
    ) -> dict[str, object]:
        eligible = _eligible(record)
        return {
            "input_id": input_id,
            "eligible": eligible,
            "integrity_failure": None if eligible else _integrity_reason(record),
            "canonical_output_sha256": (
                record.get("canonical_output_sha256") if record else None
            ),
            "invocation_record_ids": (
                list(record.get("invocation_record_ids", [])) if record else []
            ),
            "invocations": list(record.get("invocations", [])) if record else [],
            "complete_output": (
                {
                    "segments": [sorted(segment) for segment in _segments(record)],
                    "unassigned": sorted(_unassigned(record)),
                }
                if eligible
                else None
            ),
        }

    conformance_inputs = {
        "default": conformance_input("experiment-01/default", default),
        "alternate_order": conformance_input(
            "candidate-conformance/alternate-order", alternate
        ),
    }
    if not _eligible(default) or not _eligible(alternate):
        conformance = {
            "verdict": "no_verdict",
            "reason": "one or both conformance inputs were unavailable",
            "inputs": conformance_inputs,
        }
    elif _output_signature(default) != _output_signature(alternate):
        conformance = {
            "verdict": "candidate_integrity_failure",
            "inputs": conformance_inputs,
            "complete_output_difference": _output_difference(default, alternate),
        }
    else:
        conformance = {
            "verdict": "pass",
            "inputs": conformance_inputs,
            "complete_output_difference": _output_difference(default, alternate),
        }
    if conformance["verdict"] != "pass":
        unavailable_reason = str(conformance.get("reason") or conformance["verdict"])
        exception = {
            "exception_id": "E000001",
            "category": "candidate_conformance",
            "reason": unavailable_reason,
        }
        return {
            "schema_version": SCHEMA_VERSION,
            "candidate_identity": candidate_identity,
            "candidate_conformance": conformance,
            "semantic_scoring": "blocked_by_candidate_conformance",
            "experiment_02": {
                "review": {
                    "status": "not_available",
                    "unavailable_reason": unavailable_reason,
                },
                "mandatory_summaries": {},
                "exceptions": {"candidate_conformance": [exception]},
                "decision_response_contract": {
                    "schema_version": SCHEMA_VERSION,
                    "allowed_candidate_dispositions": ["revise candidate", "stop"],
                    "required_fields": [
                        "schema_version",
                        "candidate_disposition",
                        "written_rationale",
                        "exception_dispositions",
                    ],
                    "exception_disposition_fields": [
                        "exception_id",
                        "blocks_proceed",
                        "rationale",
                    ],
                    "required_exception_ids": ["E000001"],
                    "proceed_rule": (
                        "proceed is unavailable after candidate conformance failure"
                    ),
                },
                "report_completeness": {
                    "coverage_structurally_complete": False,
                    "semantic_review_complete": False,
                    "exception_dispositions_complete": False,
                    "written_rationale_complete": False,
                    "proceed_eligible": False,
                    "reason": unavailable_reason,
                },
            },
            "review_status": "not_available",
            "user_disposition": "pending",
            "candidate_selection": "reserved_for_user",
        }

    exp1_cohorts = _experiment_01_cohorts(protocol)
    exp1 = score_experiment_01(_segments(default), exp1_cohorts)

    code_by_letter = {
        "A": "ORIGAMI",
        "B": "BIKE-TUBE",
        "C": "ECLIPSE",
        "D": "STARTER",
        "E": "PIANO",
        "F": "TOMATO",
    }
    exp6_alias = {
        f"{code}-{ordinal}": f"{letter}{ordinal}"
        for letter, code in code_by_letter.items()
        for ordinal in range(1, 7)
    }
    exp6_outputs = {
        "L0": _remap_record(outputs["experiment-06/L0"], exp6_alias),
        "R0": _remap_record(outputs["experiment-06/R0"], exp6_alias),
        "duplicates": _remap_record(
            outputs["experiment-06/exact-duplicates"], exp6_alias
        ),
        "unrelated": _remap_record(
            outputs["experiment-06/unrelated-addition"], exp6_alias
        ),
        "combined": _remap_record(default, exp6_alias),
    }
    exp6 = score_experiment_06(
        exp6_outputs,
        left_groups=[{f"{letter}{index}" for index in range(1, 7)} for letter in "ABC"],
        right_groups=[
            {f"{letter}{index}" for index in range(1, 7)} for letter in "DEF"
        ],
        duplicate_aliases={f"A{index}'": f"A{index}" for index in range(1, 7)},
        imported_experiment_01_passed=exp1["verdict"] == "pass",
    )

    exp3_groups: dict[str, dict[str, set[str]]] = {}
    for encoding in protocol["encodings"]:
        if encoding["experiment"] != "experiment-03":
            continue
        trap = str(encoding["metadata"]["trap"])
        subject = str(encoding["subject"])
        exp3_groups.setdefault(trap, {}).setdefault(subject, set()).add(
            str(encoding["readable_id"])
        )
    exp3 = score_experiment_03(outputs, exp3_groups)

    input_by_id = {str(item["input_id"]): item for item in protocol["inputs"]}
    anchor_spec = input_by_id["experiment-04/anchor-only"]
    subject_order = [
        "COFFEE",
        "BICYCLE",
        "WATERCOLOR",
        "TELESCOPE",
        "SOURDOUGH",
        "PASSPORT",
    ]
    exp4_members = {
        subject: {
            member
            for member in anchor_spec["readable_members"]
            if str(member).startswith(subject + "-")
        }
        for subject in subject_order
    }
    controls = {subject: f"{subject}-CONTROL" for subject in subject_order[:3]}
    exp4_encoding = {
        str(item["readable_id"]): item
        for item in protocol["encodings"]
        if item["experiment"] == "experiment-04"
    }
    treatment_ids = [
        input_id
        for input_id in outputs
        if input_id.startswith("experiment-04/")
        and input_id != "experiment-04/anchor-only"
    ]
    treatments = {
        input_id.removeprefix("experiment-04/"): outputs[input_id]
        for input_id in treatment_ids
    }
    targets = {
        mixed: str(exp4_encoding[mixed]["metadata"]["target_subject"])
        for mixed in treatments
    }
    contexts = {
        mixed: str(exp4_encoding[mixed]["metadata"]["context_subject"])
        for mixed in treatments
    }
    forms = {
        mixed: str(exp4_encoding[mixed]["metadata"]["outer_form"])
        for mixed in treatments
    }
    exp4 = score_experiment_04(
        outputs["experiment-04/anchor-only"],
        treatments,
        subject_members=exp4_members,
        controls=controls,
        treatment_targets=targets,
        treatment_contexts=contexts,
        treatment_forms=forms,
    )

    exp2_inputs = [
        item for item in protocol["inputs"] if item["experiment"] == "experiment-02"
    ]
    exp2_encodings = {
        str(item["readable_id"]): item
        for item in protocol["encodings"]
        if item["experiment"] == "experiment-02"
    }
    exp2 = characterize_experiment_02(exp2_inputs, outputs, exp2_encodings)
    occurrences = [
        occurrence
        for configuration in exp2["configurations"].values()
        for occurrence in configuration["cross_subject_occurrences"]
    ]
    review = build_experiment_02_review(
        occurrences,
        exp2_encodings,
        review_seed=review_seed,
    )
    bind_experiment_02_review(exp2, review)
    summaries = build_experiment_02_summaries(exp2)
    exceptions = build_experiment_02_exceptions(exp2)
    coverage = {
        "schema_version": SCHEMA_VERSION,
        "candidate_identity": candidate_identity,
        "configurations": list(exp2["configurations"].values()),
        "comparisons": exp2["comparisons"],
        "support_role_by_wording_form": exp2["support_role_by_wording_form"],
    }
    expected_configuration_ids = [str(item["input_id"]) for item in exp2_inputs]
    expected_unequal_configuration_ids = [
        str(item["input_id"])
        for item in exp2_inputs
        if item["metadata"]["condition"] != "balanced"
    ]
    coverage_validation = validate_experiment_02_coverage(
        coverage,
        frozen_inputs=exp2_inputs,
        frozen_encodings=exp2_encodings,
        expected_configuration_ids=expected_configuration_ids,
        expected_unequal_configuration_ids=expected_unequal_configuration_ids,
        mandatory_summaries=summaries,
        exceptions=exceptions,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "candidate_identity": candidate_identity,
        "candidate_conformance": conformance,
        "experiment_01": exp1,
        "experiment_06": exp6,
        "experiment_03": exp3,
        "experiment_04": exp4,
        "experiment_02": {
            "review": review,
            "coverage_manifest": coverage,
            "coverage_validation": coverage_validation,
            "frozen_inputs": copy.deepcopy(exp2_inputs),
            "frozen_encodings": copy.deepcopy(exp2_encodings),
            "frozen_expected_configuration_ids": expected_configuration_ids,
            "frozen_expected_unequal_configuration_ids": expected_unequal_configuration_ids,
            "mandatory_summaries": summaries,
            "exceptions": exceptions,
            "decision_response_contract": (
                {
                    "schema_version": SCHEMA_VERSION,
                    "allowed_candidate_dispositions": ["revise candidate", "stop"],
                    "required_fields": [
                        "schema_version",
                        "candidate_disposition",
                        "written_rationale",
                        "exception_dispositions",
                    ],
                    "exception_disposition_fields": [
                        "exception_id",
                        "blocks_proceed",
                        "rationale",
                    ],
                    "required_exception_ids": [
                        row["exception_id"]
                        for rows in exceptions.values()
                        for row in rows
                    ],
                    "proceed_rule": "proceed is unavailable after review-capacity failure",
                }
                if review["status"] == "review_capacity_failure"
                else None
            ),
            "report_completeness": {
                "coverage_structurally_complete": True,
                "semantic_review_complete": False,
                "exception_dispositions_complete": False,
                "written_rationale_complete": False,
                "proceed_eligible": False,
                "reason": (
                    "review capacity exceeded; proceed is withheld"
                    if review["status"] == "review_capacity_failure"
                    else "primary human semantic review and disposition are pending"
                ),
            },
        },
        "review_status": review["status"],
        "user_disposition": "pending",
        "candidate_selection": "reserved_for_user",
    }


def _artifact_json(value: object) -> bytes:
    return _canonical_json(value) + b"\n"


def _write_new(path: Path, value: bytes) -> None:
    with path.open("xb") as destination:
        destination.write(value)
        destination.flush()
        os.fsync(destination.fileno())


def write_scoring_artifact(
    output_path: Path | str,
    evidence_by_candidate: Mapping[str, Mapping[str, object]],
    *,
    review_seed: bytes,
    source_bindings: Mapping[str, object],
    shared_diagnostics: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Write immutable internal evidence and candidate-blind review sets."""

    review_seed_commitment(review_seed)
    output = Path(output_path).resolve()
    if output.exists():
        raise ValueError(f"scoring artifact already exists: {output}")
    if not evidence_by_candidate:
        raise ValueError("scoring artifact requires at least one candidate record")
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}.", dir=output.parent))
    try:
        (stage / "internal").mkdir()
        (stage / "review").mkdir()
        review_mapping = []
        unavailable_reviews = []
        files: dict[str, dict[str, object]] = {}
        for candidate, evidence in sorted(evidence_by_candidate.items()):
            identity = evidence.get("candidate_identity")
            if not isinstance(identity, str) or not identity:
                raise ValueError("candidate evidence is missing its identity")
            internal_name = f"internal/{candidate}.json"
            internal_bytes = _artifact_json(evidence)
            _write_new(stage / internal_name, internal_bytes)
            files[internal_name] = {
                "bytes": len(internal_bytes),
                "sha256": hashlib.sha256(internal_bytes).hexdigest(),
            }

            review_status = evidence.get("review_status")
            if review_status != "pending_review":
                unavailable_reviews.append(
                    {
                        "candidate": candidate,
                        "candidate_identity": identity,
                        "review_status": review_status or "not_available",
                    }
                )
                continue
            review = evidence.get("experiment_02", {}).get("review", {})
            if not isinstance(review, dict):
                raise ValueError(
                    "candidate evidence is missing its Experiment 2 review"
                )
            set_digest = hmac.new(
                review_seed,
                b"fine-segmentation-exp2-review-set-v1\0" + identity.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
            review_set = f"R{set_digest[:12]}"
            reviewer_value = {
                "schema_version": SCHEMA_VERSION,
                "review_set": review_set,
                "status": review.get("status"),
                "review_seed_commitment": review.get("review_seed_commitment"),
                "unique_packet_count": review.get("unique_packet_count"),
                "instructions": {
                    "question": (
                        "For each packet, decide whether all instances are recognizable "
                        "as refinements of one fine subject."
                    ),
                    "valid": (
                        "Record one recognizable, non-disjunctive fine subject that covers "
                        "every instance."
                    ),
                    "invalid": (
                        "No one recognizable, non-disjunctive fine subject covers every instance."
                    ),
                    "uncertain": "The masks do not support a confident valid/invalid decision.",
                },
                "packets": review.get("reviewer_packets", []),
                "response_contract": {
                    "schema_version": SCHEMA_VERSION,
                    "review_set": review_set,
                    "judgments": "exactly one judgment for every packet",
                    "judgment_fields": ["packet", "verdict", "fine_subject"],
                    "allowed_verdicts": ["valid", "invalid", "uncertain"],
                    "fine_subject": (
                        "one nonempty subject for valid; null for invalid or uncertain"
                    ),
                },
            }
            reviewer_name = f"review/{review_set}.json"
            reviewer_bytes = _artifact_json(reviewer_value)
            _write_new(stage / reviewer_name, reviewer_bytes)
            files[reviewer_name] = {
                "bytes": len(reviewer_bytes),
                "sha256": hashlib.sha256(reviewer_bytes).hexdigest(),
            }
            review_mapping.append(
                {
                    "candidate": candidate,
                    "candidate_identity": identity,
                    "review_set": review_set,
                    "review_status": review.get("status"),
                    "packet_count": review.get("unique_packet_count"),
                }
            )

        mapping_value = {
            "schema_version": SCHEMA_VERSION,
            "review_seed_commitment": review_seed_commitment(review_seed),
            "sets": sorted(review_mapping, key=lambda item: item["review_set"]),
            "unavailable_candidates": sorted(
                unavailable_reviews, key=lambda item: item["candidate"]
            ),
            "user_disposition": "pending",
            "candidate_selection": "reserved_for_user",
        }
        mapping_bytes = _artifact_json(mapping_value)
        _write_new(stage / "internal/review-set-mapping.json", mapping_bytes)
        files["internal/review-set-mapping.json"] = {
            "bytes": len(mapping_bytes),
            "sha256": hashlib.sha256(mapping_bytes).hexdigest(),
        }
        if shared_diagnostics is not None:
            (stage / "shared").mkdir()
            diagnostics_bytes = _artifact_json(shared_diagnostics)
            _write_new(
                stage / "shared/representation-diagnostics.json", diagnostics_bytes
            )
            files["shared/representation-diagnostics.json"] = {
                "bytes": len(diagnostics_bytes),
                "sha256": hashlib.sha256(diagnostics_bytes).hexdigest(),
            }
        status_value = {
            "schema_version": SCHEMA_VERSION,
            "candidate_count": len(evidence_by_candidate),
            "review_set_count": len(review_mapping),
            "review_states": sorted(
                {
                    str(evidence.get("review_status") or "not_available")
                    for evidence in evidence_by_candidate.values()
                }
            ),
            "next_action": (
                "primary human semantic review"
                if review_mapping
                else "inspect candidate result records; semantic review is unavailable"
            ),
            "assistant_recommendation": "withheld_until_review",
            "candidate_selection": "reserved_for_user",
        }
        status_bytes = _artifact_json(status_value)
        _write_new(stage / "status.json", status_bytes)
        files["status.json"] = {
            "bytes": len(status_bytes),
            "sha256": hashlib.sha256(status_bytes).hexdigest(),
        }
        manifest_value = {
            "schema_version": SCHEMA_VERSION,
            "source_bindings": dict(source_bindings),
            "review_seed_commitment": review_seed_commitment(review_seed),
            "files": dict(sorted(files.items())),
        }
        _write_new(stage / "manifest.json", _artifact_json(manifest_value))
        os.rename(stage, output)
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return verify_scoring_artifact(output)


def verify_scoring_artifact(output_path: Path | str) -> dict[str, object]:
    """Verify retained scoring and reviewer-facing file identities."""

    output = Path(output_path).resolve()
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    files = manifest.get("files")
    if not isinstance(files, dict):
        raise ValueError("scoring manifest is missing file identities")
    actual_files = {
        str(path.relative_to(output))
        for path in output.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    }
    if actual_files != set(files):
        raise ValueError("scoring artifact contains unexpected or missing files")
    for relative, identity in files.items():
        value = (output / relative).read_bytes()
        if identity != {
            "bytes": len(value),
            "sha256": hashlib.sha256(value).hexdigest(),
        }:
            raise ValueError(
                f"scoring artifact file {relative} differs from its manifest"
            )
    status = json.loads((output / "status.json").read_text(encoding="utf-8"))
    return {
        "candidate_count": status["candidate_count"],
        "review_set_count": status["review_set_count"],
        "review_states": status["review_states"],
        "next_action": status["next_action"],
        "manifest_sha256": hashlib.sha256(
            (output / "manifest.json").read_bytes()
        ).hexdigest(),
        "output_path": str(output),
    }


def _verify_json_artifact(
    artifact_path: Path | str, *, artifact_type: str
) -> tuple[Path, dict[str, object], str]:
    """Verify an immutable JSON artifact directory and return its manifest."""

    root = Path(artifact_path).resolve()
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        raise ValueError(f"{artifact_type} artifact has no manifest")
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes.decode("utf-8"))
    if (
        manifest.get("schema_version") != SCHEMA_VERSION
        or manifest.get("artifact_type") != artifact_type
        or not isinstance(manifest.get("files"), dict)
    ):
        raise ValueError(f"{artifact_type} artifact manifest is invalid")
    files = manifest["files"]
    actual_files = {
        str(path.relative_to(root))
        for path in root.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    }
    if actual_files != set(files):
        raise ValueError(
            f"{artifact_type} artifact contains unexpected or missing files"
        )
    for relative, identity in files.items():
        value = (root / relative).read_bytes()
        if identity != {
            "bytes": len(value),
            "sha256": hashlib.sha256(value).hexdigest(),
        }:
            raise ValueError(
                f"{artifact_type} artifact file {relative} is not immutable"
            )
    return root, manifest, hashlib.sha256(manifest_bytes).hexdigest()


def _write_json_artifact(
    output_path: Path | str,
    *,
    artifact_type: str,
    source_bindings: Mapping[str, object],
    json_files: Mapping[str, object],
) -> None:
    """Write one new immutable directory containing canonical JSON files."""

    output = Path(output_path).resolve()
    if output.exists():
        raise ValueError(f"artifact already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}.", dir=output.parent))
    try:
        files: dict[str, dict[str, object]] = {}
        for relative, value in sorted(json_files.items()):
            path = stage / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            payload = _artifact_json(value)
            _write_new(path, payload)
            files[relative] = {
                "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "artifact_type": artifact_type,
            "source_bindings": copy.deepcopy(dict(source_bindings)),
            "files": files,
        }
        _write_new(stage / "manifest.json", _artifact_json(manifest))
        os.rename(stage, output)
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise


def _bound_scoring_candidate(
    scoring_path: Path | str, review_set: str
) -> dict[str, object]:
    """Resolve one opaque review set to its exact manifest-bound candidate."""

    scoring = Path(scoring_path).resolve()
    scoring_report = verify_scoring_artifact(scoring)
    mapping = json.loads(
        (scoring / "internal/review-set-mapping.json").read_text(encoding="utf-8")
    )
    rows = [
        row for row in mapping.get("sets", []) if row.get("review_set") == review_set
    ]
    if len(rows) != 1:
        raise ValueError("review set does not identify exactly one scored candidate")
    row = rows[0]
    candidate = row.get("candidate")
    if (
        not isinstance(candidate, str)
        or not candidate
        or "/" in candidate
        or candidate in {".", ".."}
    ):
        raise ValueError("review-set mapping contains an invalid candidate name")
    relative = f"internal/{candidate}.json"
    candidate_path = scoring / relative
    evidence = json.loads(candidate_path.read_text(encoding="utf-8"))
    if evidence.get("candidate_identity") != row.get("candidate_identity"):
        raise ValueError("review set and internal candidate identity differ")
    reviewer_path = scoring / "review" / f"{review_set}.json"
    reviewer = json.loads(reviewer_path.read_text(encoding="utf-8"))
    if reviewer.get("review_set") != review_set:
        raise ValueError("reviewer packet names the wrong review set")
    return {
        "scoring_path": scoring,
        "scoring_manifest_sha256": scoring_report["manifest_sha256"],
        "candidate": candidate,
        "candidate_identity": row["candidate_identity"],
        "review_set": review_set,
        "candidate_file": relative,
        "candidate_file_sha256": hashlib.sha256(
            candidate_path.read_bytes()
        ).hexdigest(),
        "review_file": f"review/{review_set}.json",
        "review_file_sha256": hashlib.sha256(reviewer_path.read_bytes()).hexdigest(),
        "evidence": evidence,
        "reviewer": reviewer,
    }


def _bound_unavailable_scoring_candidate(
    scoring_path: Path | str, candidate: str
) -> dict[str, object]:
    """Resolve one review-unavailable candidate from the scoring manifest."""

    scoring = Path(scoring_path).resolve()
    scoring_report = verify_scoring_artifact(scoring)
    mapping = json.loads(
        (scoring / "internal/review-set-mapping.json").read_text(encoding="utf-8")
    )
    rows = [
        row
        for row in mapping.get("unavailable_candidates", [])
        if row.get("candidate") == candidate
    ]
    if len(rows) != 1:
        raise ValueError(
            "candidate is not exactly one review-unavailable scored candidate"
        )
    row = rows[0]
    if not candidate or "/" in candidate or candidate in {".", ".."}:
        raise ValueError("unavailable-candidate mapping contains an invalid name")
    relative = f"internal/{candidate}.json"
    candidate_path = scoring / relative
    evidence = json.loads(candidate_path.read_text(encoding="utf-8"))
    if (
        evidence.get("candidate_identity") != row.get("candidate_identity")
        or evidence.get("review_status") != row.get("review_status")
        or evidence.get("review_status")
        not in {"review_capacity_failure", "not_available"}
    ):
        raise ValueError("unavailable candidate differs from its scoring mapping")
    return {
        "scoring_path": scoring,
        "scoring_manifest_sha256": scoring_report["manifest_sha256"],
        "candidate": candidate,
        "candidate_identity": row["candidate_identity"],
        "review_set": None,
        "review_status": row["review_status"],
        "candidate_file": relative,
        "candidate_file_sha256": hashlib.sha256(
            candidate_path.read_bytes()
        ).hexdigest(),
        "evidence": evidence,
    }


POST_HOC_REVIEW_ARTIFACT_TYPE = "fine-segmentation-post-hoc-review-v1"
POST_HOC_REVIEWED_ARTIFACT_TYPE = "fine-segmentation-post-hoc-reviewed-v1"
POST_HOC_PACKET_COUNT = 177
POST_HOC_OCCURRENCE_COUNT = 191


def _reject_post_hoc_output_overlap(
    output_path: Path | str,
    upstream_paths: Sequence[tuple[str, Path | str]],
) -> None:
    """Reject an output equal to, above, or below any immutable source."""

    output = Path(output_path).expanduser().resolve()
    for name, upstream_path in upstream_paths:
        upstream = Path(upstream_path).expanduser().resolve()
        if (
            output == upstream
            or output in upstream.parents
            or upstream in output.parents
        ):
            raise ValueError(f"post-hoc output and {name} artifact paths overlap")


def _validated_post_hoc_occurrences(
    evidence: Mapping[str, object],
    internal_packets: Sequence[Mapping[str, object]],
) -> list[tuple[str, dict[str, object]]]:
    """Bind retained packet occurrences to the formal coverage manifest."""

    experiment = evidence.get("experiment_02")
    coverage = (
        experiment.get("coverage_manifest") if isinstance(experiment, dict) else None
    )
    configurations = (
        coverage.get("configurations") if isinstance(coverage, dict) else None
    )
    if not isinstance(configurations, list):
        raise ValueError("HDBSCAN source has no formal Experiment 2 coverage")

    internal_rows: list[tuple[str, dict[str, object]]] = []
    internal_counter: Counter[tuple[str, bytes]] = Counter()
    for packet in internal_packets:
        packet_id = packet.get("packet")
        occurrences = packet.get("occurrences")
        if not isinstance(packet_id, str) or not isinstance(occurrences, list):
            raise ValueError("HDBSCAN source contains invalid packet occurrences")
        for occurrence in occurrences:
            if not isinstance(occurrence, dict):
                raise ValueError("HDBSCAN source contains an invalid occurrence")
            retained = copy.deepcopy(occurrence)
            internal_rows.append((packet_id, retained))
            internal_counter[(packet_id, _canonical_json(retained))] += 1

    coverage_counter: Counter[tuple[str, bytes]] = Counter()
    for configuration in configurations:
        if not isinstance(configuration, dict):
            raise ValueError("Experiment 2 coverage contains an invalid configuration")
        occurrences = configuration.get("cross_subject_occurrences")
        if not isinstance(occurrences, list):
            raise ValueError("Experiment 2 coverage omits cross-subject occurrences")
        for occurrence in occurrences:
            if not isinstance(occurrence, dict):
                raise ValueError("Experiment 2 coverage contains an invalid occurrence")
            review = occurrence.get("review")
            packet_id = review.get("packet") if isinstance(review, dict) else None
            if not isinstance(packet_id, str):
                raise ValueError("Experiment 2 occurrence has no packet binding")
            retained = {
                key: copy.deepcopy(value)
                for key, value in occurrence.items()
                if key != "review"
            }
            coverage_counter[(packet_id, _canonical_json(retained))] += 1
    if internal_counter != coverage_counter:
        raise ValueError(
            "retained review packet occurrences differ from formal Experiment 2 coverage"
        )
    return internal_rows


def _post_hoc_hdbscan_review_values(
    source: Mapping[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    """Project every retained HDBSCAN packet without exposing scoring provenance."""

    if (
        source.get("candidate") != "hdbscan"
        or source.get("candidate_identity") != "hdbscan-controlled-suite-config-v1"
        or source.get("review_status") != "review_capacity_failure"
    ):
        raise ValueError(
            "post-hoc review requires the frozen capacity-failed HDBSCAN candidate"
        )
    evidence = source.get("evidence")
    if not isinstance(evidence, dict):
        raise ValueError("post-hoc review source has no candidate evidence")
    experiment = evidence.get("experiment_02")
    review = experiment.get("review") if isinstance(experiment, dict) else None
    if (
        not isinstance(review, dict)
        or review.get("status") != "review_capacity_failure"
        or review.get("reviewer_packets") != []
    ):
        raise ValueError("HDBSCAN source did not retain its capacity-failure state")
    internal_packets = review.get("internal_packets")
    if not isinstance(internal_packets, list) or review.get(
        "unique_packet_count"
    ) != len(internal_packets):
        raise ValueError("HDBSCAN source has an invalid retained packet pool")
    if len(internal_packets) != POST_HOC_PACKET_COUNT:
        raise ValueError("post-hoc HDBSCAN review requires exactly 177 unique packets")

    packets: list[dict[str, object]] = []
    packet_ids: set[str] = set()
    for packet in internal_packets:
        if not isinstance(packet, dict):
            raise ValueError("HDBSCAN source contains an invalid packet")
        packet_id = packet.get("packet")
        members = packet.get("members")
        occurrences = packet.get("occurrences")
        if (
            not isinstance(packet_id, str)
            or not packet_id
            or packet_id in packet_ids
            or packet.get("review_state") != "unavailable"
            or not isinstance(members, list)
            or len(members) < 2
            or not isinstance(occurrences, list)
            or not occurrences
        ):
            raise ValueError("HDBSCAN source contains an invalid retained packet")
        packet_ids.add(packet_id)
        projected_instances = []
        seen_instances: set[str] = set()
        for member in members:
            if not isinstance(member, dict):
                raise ValueError("HDBSCAN packet contains an invalid member")
            instance = member.get("instance")
            fragments = member.get("fragments")
            if (
                not isinstance(instance, str)
                or not instance
                or instance in seen_instances
                or not isinstance(fragments, list)
                or not fragments
                or not all(
                    isinstance(fragment, str) and fragment for fragment in fragments
                )
            ):
                raise ValueError("HDBSCAN packet contains an invalid review instance")
            seen_instances.add(instance)
            projected_instances.append(
                {"instance": instance, "fragments": copy.deepcopy(fragments)}
            )
        packets.append(
            {
                "packet": packet_id,
                "question": (
                    "Are all instances recognizable as refinements of one fine subject?"
                ),
                "verdicts": ["valid", "invalid", "uncertain"],
                "instances": projected_instances,
            }
        )
    occurrence_count = len(_validated_post_hoc_occurrences(evidence, internal_packets))
    if occurrence_count != POST_HOC_OCCURRENCE_COUNT:
        raise ValueError("post-hoc HDBSCAN review requires exactly 191 occurrences")

    review_set_digest = hashlib.sha256(
        b"fine-segmentation-post-hoc-hdbscan-review-v1\0"
        + str(source["candidate_file_sha256"]).encode("ascii")
        + _canonical_json(packets)
    ).hexdigest()
    review_set = f"PH{review_set_digest[:12]}"
    reviewer = {
        "schema_version": SCHEMA_VERSION,
        "review_set": review_set,
        "instructions": {
            "question": (
                "For each packet, decide whether all instances are recognizable "
                "as refinements of one fine subject."
            ),
            "valid": (
                "Every instance is recognizable as a refinement of one fine subject."
            ),
            "invalid": (
                "No one recognizable, non-disjunctive fine subject covers every instance."
            ),
            "uncertain": (
                "The masks do not support a confident valid/invalid decision."
            ),
        },
        "packets": packets,
        "response_contract": {
            "schema_version": SCHEMA_VERSION,
            "review_set": review_set,
            "judgments": "exactly one judgment for every packet",
            "judgment_fields": ["packet", "verdict"],
            "allowed_verdicts": ["valid", "invalid", "uncertain"],
        },
    }
    status = {
        "schema_version": SCHEMA_VERSION,
        "status": "pending_review",
        "epistemic_status": "post_hoc_exploratory_after_capacity_failure",
        "source_review_status": "review_capacity_failure",
        "packet_count": len(packets),
        "occurrence_count": occurrence_count,
        "changes_frozen_protocol_result": False,
        "proceed_eligible": False,
        "candidate_selection": "reserved_for_user",
    }
    return reviewer, status


def _post_hoc_review_source_bindings(source: Mapping[str, object]) -> dict[str, object]:
    bindings = {
        key: copy.deepcopy(source[key])
        for key in (
            "scoring_manifest_sha256",
            "candidate",
            "candidate_identity",
            "candidate_file",
            "candidate_file_sha256",
        )
    }
    bindings["source_review_status"] = source["review_status"]
    return bindings


def write_post_hoc_hdbscan_review_artifact(
    scoring_path: Path | str, output_path: Path | str
) -> dict[str, object]:
    """Materialize all retained HDBSCAN packets as a separate post-hoc review."""

    _reject_post_hoc_output_overlap(output_path, (("scoring", scoring_path),))
    source = _bound_unavailable_scoring_candidate(scoring_path, "hdbscan")
    reviewer, status = _post_hoc_hdbscan_review_values(source)
    _write_json_artifact(
        output_path,
        artifact_type=POST_HOC_REVIEW_ARTIFACT_TYPE,
        source_bindings=_post_hoc_review_source_bindings(source),
        json_files={"review.json": reviewer, "status.json": status},
    )
    return verify_post_hoc_hdbscan_review_artifact(scoring_path, output_path)


def verify_post_hoc_hdbscan_review_artifact(
    scoring_path: Path | str, review_path: Path | str
) -> dict[str, object]:
    """Replay the safe reviewer projection from the immutable scoring source."""

    root, manifest, manifest_sha = _verify_json_artifact(
        review_path, artifact_type=POST_HOC_REVIEW_ARTIFACT_TYPE
    )
    source = _bound_unavailable_scoring_candidate(scoring_path, "hdbscan")
    if manifest.get("source_bindings") != _post_hoc_review_source_bindings(source):
        raise ValueError("post-hoc review source chain differs from frozen scoring")
    expected_review, expected_status = _post_hoc_hdbscan_review_values(source)
    retained_review = json.loads((root / "review.json").read_text(encoding="utf-8"))
    retained_status = json.loads((root / "status.json").read_text(encoding="utf-8"))
    if retained_review != expected_review or retained_status != expected_status:
        raise ValueError("post-hoc review differs from its replayed projection")
    return {
        "artifact_type": POST_HOC_REVIEW_ARTIFACT_TYPE,
        "manifest_sha256": manifest_sha,
        "output_path": str(root),
        "packet_count": expected_status["packet_count"],
        "occurrence_count": expected_status["occurrence_count"],
        "review": retained_review,
        "status": retained_status,
    }


def _validate_post_hoc_packet_judgments(
    packets: Sequence[Mapping[str, object]],
    review_set: str,
    response: Mapping[str, object],
) -> dict[str, dict[str, object]]:
    """Validate one verdict-only judgment for every post-hoc packet."""

    if set(response) != {"schema_version", "review_set", "judgments"}:
        raise ValueError("post-hoc review response has the wrong top-level schema")
    if response.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("post-hoc review response has the wrong schema version")
    if response.get("review_set") != review_set:
        raise ValueError("post-hoc review response names the wrong review set")
    judgments = response.get("judgments")
    if not isinstance(judgments, list):
        raise ValueError("post-hoc review response is missing judgments")
    expected = {str(packet.get("packet")) for packet in packets}
    if None in expected or "None" in expected or len(expected) != len(packets):
        raise ValueError("post-hoc review packet identities are invalid")
    by_packet: dict[str, dict[str, object]] = {}
    for judgment in judgments:
        if not isinstance(judgment, dict):
            raise ValueError("post-hoc review judgment is not an object")
        if set(judgment) != {"packet", "verdict"}:
            raise ValueError("post-hoc review judgment has unexpected fields")
        packet = judgment.get("packet")
        if not isinstance(packet, str) or packet in by_packet:
            raise ValueError("post-hoc review response repeats a packet")
        if judgment.get("verdict") not in {"valid", "invalid", "uncertain"}:
            raise ValueError("post-hoc review verdict is invalid")
        by_packet[packet] = dict(judgment)
    if set(by_packet) != expected:
        raise ValueError(
            "post-hoc review response does not cover every packet exactly once"
        )
    return by_packet


def _post_hoc_review_result(
    source: Mapping[str, object],
    reviewer: Mapping[str, object],
    response: Mapping[str, object],
) -> dict[str, object]:
    packets = reviewer.get("packets")
    review_set = reviewer.get("review_set")
    if not isinstance(packets, list) or not isinstance(review_set, str):
        raise ValueError("post-hoc reviewer artifact is invalid")
    judgments = _validate_post_hoc_packet_judgments(packets, review_set, response)
    evidence = source["evidence"]
    internal_packets = evidence["experiment_02"]["review"]["internal_packets"]
    bound_occurrences = _validated_post_hoc_occurrences(evidence, internal_packets)
    occurrence_rows = []
    for packet_id, occurrence in bound_occurrences:
        judgment = judgments[packet_id]
        occurrence_rows.append(
            {
                "packet": packet_id,
                "configuration_id": occurrence["configuration_id"],
                "verdict": judgment["verdict"],
            }
        )
    packet_verdict_counts = Counter(
        str(judgment["verdict"]) for judgment in judgments.values()
    )
    occurrence_verdict_counts = Counter(row["verdict"] for row in occurrence_rows)
    return {
        "schema_version": SCHEMA_VERSION,
        "candidate": source["candidate"],
        "candidate_identity": source["candidate_identity"],
        "source_review_status": "review_capacity_failure",
        "changes_frozen_protocol_result": False,
        "proceed_eligible": False,
        "candidate_selection": "reserved_for_user",
        "judgment_count": len(judgments),
        "occurrence_count": len(occurrence_rows),
        "packet_verdict_counts": {
            verdict: packet_verdict_counts.get(verdict, 0)
            for verdict in ("valid", "invalid", "uncertain")
        },
        "occurrence_verdict_counts": {
            verdict: occurrence_verdict_counts.get(verdict, 0)
            for verdict in ("valid", "invalid", "uncertain")
        },
        "judgments": [judgments[str(packet["packet"])] for packet in packets],
        "occurrences": occurrence_rows,
    }


def write_post_hoc_hdbscan_reviewed_artifact(
    scoring_path: Path | str,
    review_path: Path | str,
    response: Mapping[str, object],
    output_path: Path | str,
) -> dict[str, object]:
    """Retain a complete post-hoc response without overriding the frozen verdict."""

    _reject_post_hoc_output_overlap(
        output_path,
        (("scoring", scoring_path), ("review", review_path)),
    )
    review_report = verify_post_hoc_hdbscan_review_artifact(scoring_path, review_path)
    source = _bound_unavailable_scoring_candidate(scoring_path, "hdbscan")
    result = _post_hoc_review_result(source, review_report["review"], response)
    _write_json_artifact(
        output_path,
        artifact_type=POST_HOC_REVIEWED_ARTIFACT_TYPE,
        source_bindings={
            "post_hoc_review_manifest_sha256": review_report["manifest_sha256"],
            **_post_hoc_review_source_bindings(source),
        },
        json_files={
            "semantic-response.json": copy.deepcopy(response),
            "post-hoc-result.json": result,
        },
    )
    return verify_post_hoc_hdbscan_reviewed_artifact(
        scoring_path, review_path, output_path
    )


def verify_post_hoc_hdbscan_reviewed_artifact(
    scoring_path: Path | str,
    review_path: Path | str,
    reviewed_path: Path | str,
) -> dict[str, object]:
    """Replay a complete post-hoc response and its occurrence reuse."""

    review_report = verify_post_hoc_hdbscan_review_artifact(scoring_path, review_path)
    source = _bound_unavailable_scoring_candidate(scoring_path, "hdbscan")
    root, manifest, manifest_sha = _verify_json_artifact(
        reviewed_path, artifact_type=POST_HOC_REVIEWED_ARTIFACT_TYPE
    )
    expected_bindings = {
        "post_hoc_review_manifest_sha256": review_report["manifest_sha256"],
        **_post_hoc_review_source_bindings(source),
    }
    if manifest.get("source_bindings") != expected_bindings:
        raise ValueError("post-hoc reviewed source chain is incomplete")
    response = json.loads((root / "semantic-response.json").read_text(encoding="utf-8"))
    expected = _post_hoc_review_result(source, review_report["review"], response)
    retained = json.loads((root / "post-hoc-result.json").read_text(encoding="utf-8"))
    if retained != expected:
        raise ValueError("post-hoc reviewed result differs from replayed judgments")
    return {
        "artifact_type": POST_HOC_REVIEWED_ARTIFACT_TYPE,
        "manifest_sha256": manifest_sha,
        "output_path": str(root),
        **retained,
    }


def write_reviewed_scoring_artifact(
    scoring_path: Path | str,
    review_set: str,
    response: Mapping[str, object],
    output_path: Path | str,
) -> dict[str, object]:
    """Apply a semantic response only to its scoring-manifest-bound candidate."""

    source = _bound_scoring_candidate(scoring_path, review_set)
    reviewed = apply_semantic_review_response(source["evidence"], review_set, response)
    bindings = {
        key: source[key]
        for key in (
            "scoring_manifest_sha256",
            "candidate",
            "candidate_identity",
            "review_set",
            "candidate_file",
            "candidate_file_sha256",
            "review_file",
            "review_file_sha256",
        )
    }
    _write_json_artifact(
        output_path,
        artifact_type="fine-segmentation-reviewed-v1",
        source_bindings=bindings,
        json_files={
            "semantic-response.json": copy.deepcopy(response),
            "reviewed-evidence.json": reviewed,
        },
    )
    return verify_reviewed_scoring_artifact(scoring_path, output_path)


def verify_reviewed_scoring_artifact(
    scoring_path: Path | str, reviewed_path: Path | str
) -> dict[str, object]:
    """Replay a semantic response from the exact retained scoring evidence."""

    root, manifest, manifest_sha = _verify_json_artifact(
        reviewed_path, artifact_type="fine-segmentation-reviewed-v1"
    )
    bindings = manifest["source_bindings"]
    if not isinstance(bindings, dict) or not isinstance(
        bindings.get("review_set"), str
    ):
        raise ValueError("reviewed artifact lacks its review-set source binding")
    source = _bound_scoring_candidate(scoring_path, str(bindings["review_set"]))
    expected_bindings = {
        key: source[key]
        for key in (
            "scoring_manifest_sha256",
            "candidate",
            "candidate_identity",
            "review_set",
            "candidate_file",
            "candidate_file_sha256",
            "review_file",
            "review_file_sha256",
        )
    }
    if bindings != expected_bindings:
        raise ValueError(
            "reviewed artifact source chain differs from the scoring artifact"
        )
    response = json.loads((root / "semantic-response.json").read_text(encoding="utf-8"))
    replayed = apply_semantic_review_response(
        source["evidence"], str(bindings["review_set"]), response
    )
    retained = json.loads((root / "reviewed-evidence.json").read_text(encoding="utf-8"))
    if retained != replayed:
        raise ValueError("reviewed evidence differs from replayed semantic response")
    return {
        "artifact_type": "fine-segmentation-reviewed-v1",
        "manifest_sha256": manifest_sha,
        "output_path": str(root),
        "candidate": source["candidate"],
        "candidate_identity": source["candidate_identity"],
        "review_set": source["review_set"],
        "response": response,
        "evidence": retained,
    }


def write_finalized_scoring_artifact(
    scoring_path: Path | str,
    reviewed_path: Path | str,
    response: Mapping[str, object],
    output_path: Path | str,
) -> dict[str, object]:
    """Record one disposition while preserving a replayable review chain."""

    reviewed = verify_reviewed_scoring_artifact(scoring_path, reviewed_path)
    finalized = finalize_candidate_disposition(reviewed["evidence"], response)
    reviewed_root = Path(reviewed_path).resolve()
    reviewed_manifest = json.loads(
        (reviewed_root / "manifest.json").read_text(encoding="utf-8")
    )
    bindings = {
        "finalization_mode": "semantic-review",
        "scoring_manifest_sha256": _bound_scoring_candidate(
            scoring_path, str(reviewed["review_set"])
        )["scoring_manifest_sha256"],
        "reviewed_manifest_sha256": reviewed["manifest_sha256"],
        "candidate": reviewed["candidate"],
        "candidate_identity": reviewed["candidate_identity"],
        "review_set": reviewed["review_set"],
    }
    _write_json_artifact(
        output_path,
        artifact_type="fine-segmentation-finalized-v1",
        source_bindings=bindings,
        json_files={
            "source-reviewed-manifest.json": reviewed_manifest,
            "semantic-response.json": reviewed["response"],
            "reviewed-evidence.json": reviewed["evidence"],
            "decision-response.json": copy.deepcopy(response),
            "finalized-evidence.json": finalized,
        },
    )
    return verify_finalized_scoring_artifact(scoring_path, output_path)


def write_unavailable_finalized_scoring_artifact(
    scoring_path: Path | str,
    candidate: str,
    response: Mapping[str, object],
    output_path: Path | str,
) -> dict[str, object]:
    """Finalize a review-unavailable candidate without inventing packet review."""

    source = _bound_unavailable_scoring_candidate(scoring_path, candidate)
    finalized = finalize_candidate_disposition(source["evidence"], response)
    bindings = {
        key: source[key]
        for key in (
            "scoring_manifest_sha256",
            "candidate",
            "candidate_identity",
            "review_set",
            "review_status",
            "candidate_file",
            "candidate_file_sha256",
        )
    }
    bindings["finalization_mode"] = "review-unavailable"
    _write_json_artifact(
        output_path,
        artifact_type="fine-segmentation-finalized-v1",
        source_bindings=bindings,
        json_files={
            "decision-response.json": copy.deepcopy(response),
            "finalized-evidence.json": finalized,
        },
    )
    return verify_finalized_scoring_artifact(scoring_path, output_path)


def verify_finalized_scoring_artifact(
    scoring_path: Path | str, finalized_path: Path | str
) -> dict[str, object]:
    """Replay both human responses from the exact retained candidate evidence."""

    root, manifest, manifest_sha = _verify_json_artifact(
        finalized_path, artifact_type="fine-segmentation-finalized-v1"
    )
    bindings = manifest["source_bindings"]
    if not isinstance(bindings, dict):
        raise ValueError("finalized artifact lacks source bindings")
    mode = bindings.get("finalization_mode")
    semantic_response = None
    if mode == "semantic-review":
        if not isinstance(bindings.get("review_set"), str):
            raise ValueError("finalized artifact lacks its review-set source binding")
        source = _bound_scoring_candidate(scoring_path, str(bindings["review_set"]))
        if any(
            bindings.get(key) != source[key]
            for key in (
                "scoring_manifest_sha256",
                "candidate",
                "candidate_identity",
                "review_set",
            )
        ):
            raise ValueError(
                "finalized artifact source chain differs from scoring evidence"
            )
        reviewed_manifest_bytes = (root / "source-reviewed-manifest.json").read_bytes()
        reviewed_manifest_value = json.loads(reviewed_manifest_bytes.decode("utf-8"))
        if hashlib.sha256(reviewed_manifest_bytes).hexdigest() != bindings.get(
            "reviewed_manifest_sha256"
        ):
            raise ValueError("finalized artifact names the wrong reviewed manifest")
        expected_reviewed_bindings = {
            key: source[key]
            for key in (
                "scoring_manifest_sha256",
                "candidate",
                "candidate_identity",
                "review_set",
                "candidate_file",
                "candidate_file_sha256",
                "review_file",
                "review_file_sha256",
            )
        }
        if (
            reviewed_manifest_value.get("artifact_type")
            != "fine-segmentation-reviewed-v1"
            or reviewed_manifest_value.get("source_bindings")
            != expected_reviewed_bindings
        ):
            raise ValueError(
                "finalized artifact reviewed manifest names the wrong candidate"
            )
        semantic_response = json.loads(
            (root / "semantic-response.json").read_text(encoding="utf-8")
        )
        replayed_review = apply_semantic_review_response(
            source["evidence"], str(bindings["review_set"]), semantic_response
        )
        retained_review = json.loads(
            (root / "reviewed-evidence.json").read_text(encoding="utf-8")
        )
        if retained_review != replayed_review:
            raise ValueError("finalized artifact retained the wrong reviewed evidence")
    elif mode == "review-unavailable":
        candidate = bindings.get("candidate")
        if not isinstance(candidate, str):
            raise ValueError("unavailable finalization lacks its candidate binding")
        source = _bound_unavailable_scoring_candidate(scoring_path, candidate)
        expected_bindings = {
            key: source[key]
            for key in (
                "scoring_manifest_sha256",
                "candidate",
                "candidate_identity",
                "review_set",
                "review_status",
                "candidate_file",
                "candidate_file_sha256",
            )
        }
        expected_bindings["finalization_mode"] = "review-unavailable"
        if bindings != expected_bindings:
            raise ValueError(
                "unavailable finalization source chain differs from scoring evidence"
            )
        replayed_review = source["evidence"]
    else:
        raise ValueError("finalized artifact has an unknown finalization mode")
    decision_response = json.loads(
        (root / "decision-response.json").read_text(encoding="utf-8")
    )
    replayed_final = finalize_candidate_disposition(replayed_review, decision_response)
    retained_final = json.loads(
        (root / "finalized-evidence.json").read_text(encoding="utf-8")
    )
    if retained_final != replayed_final:
        raise ValueError("finalized evidence differs from replayed disposition")
    return {
        "artifact_type": "fine-segmentation-finalized-v1",
        "manifest_sha256": manifest_sha,
        "output_path": str(root),
        "candidate": source["candidate"],
        "candidate_identity": source["candidate_identity"],
        "review_set": source["review_set"],
        "semantic_response": semantic_response,
        "decision_response": decision_response,
        "evidence": retained_final,
    }


def _comparison_value(
    finalized_reports: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    candidates = []
    for report in sorted(finalized_reports, key=lambda item: str(item["candidate"])):
        evidence = report["evidence"]
        experiment = evidence["experiment_02"]
        candidates.append(
            {
                "candidate": report["candidate"],
                "candidate_identity": report["candidate_identity"],
                "review_set": report["review_set"],
                "finalized_manifest_sha256": report["manifest_sha256"],
                "candidate_conformance": evidence.get("candidate_conformance"),
                "experiment_01": evidence.get("experiment_01"),
                "experiment_03": evidence.get("experiment_03"),
                "experiment_04": evidence.get("experiment_04"),
                "experiment_06": evidence.get("experiment_06"),
                "experiment_02": {
                    "mandatory_summaries": experiment.get("mandatory_summaries"),
                    "exceptions": experiment.get("exceptions"),
                    "coverage_validation": experiment.get("coverage_validation"),
                    "primary_reviewer_decision": experiment.get(
                        "primary_reviewer_decision"
                    ),
                    "report_completeness": experiment["report_completeness"],
                },
                "user_disposition": evidence["user_disposition"],
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "candidates": candidates,
        "assistant_recommendation": {
            "status": "pending",
            "recommended_candidate": None,
            "rationale": None,
        },
        "candidate_selection": "reserved_for_user",
    }


def write_candidate_comparison_artifact(
    scoring_path: Path | str,
    finalized_paths: Sequence[Path | str],
    output_path: Path | str,
) -> dict[str, object]:
    """Freeze both finalized candidates side by side without selecting one."""

    if len(finalized_paths) != 2:
        raise ValueError(
            "candidate comparison requires exactly two finalized candidates"
        )
    reports = [
        verify_finalized_scoring_artifact(scoring_path, path)
        for path in finalized_paths
    ]
    if len({report["candidate"] for report in reports}) != 2:
        raise ValueError("candidate comparison repeats one finalized candidate")
    scoring_report = verify_scoring_artifact(scoring_path)
    mapping = json.loads(
        (Path(scoring_path).resolve() / "internal/review-set-mapping.json").read_text(
            encoding="utf-8"
        )
    )
    expected_candidates = {
        row["candidate"]
        for key in ("sets", "unavailable_candidates")
        for row in mapping.get(key, [])
    }
    if {report["candidate"] for report in reports} != expected_candidates:
        raise ValueError(
            "candidate comparison does not cover every reviewable candidate"
        )
    value = _comparison_value(reports)
    source_finalized = [
        {
            "candidate": report["candidate"],
            "review_set": report["review_set"],
            "manifest_sha256": report["manifest_sha256"],
        }
        for report in sorted(reports, key=lambda item: str(item["candidate"]))
    ]
    _write_json_artifact(
        output_path,
        artifact_type="fine-segmentation-comparison-v1",
        source_bindings={
            "scoring_manifest_sha256": scoring_report["manifest_sha256"],
            "finalized_artifacts": source_finalized,
        },
        json_files={"comparison.json": value},
    )
    return verify_candidate_comparison_artifact(
        scoring_path, finalized_paths, output_path
    )


def verify_candidate_comparison_artifact(
    scoring_path: Path | str,
    finalized_paths: Sequence[Path | str],
    comparison_path: Path | str,
) -> dict[str, object]:
    """Replay the complete two-candidate comparison artifact."""

    if len(finalized_paths) != 2:
        raise ValueError(
            "candidate comparison requires exactly two finalized candidates"
        )
    root, manifest, manifest_sha = _verify_json_artifact(
        comparison_path, artifact_type="fine-segmentation-comparison-v1"
    )
    reports = [
        verify_finalized_scoring_artifact(scoring_path, path)
        for path in finalized_paths
    ]
    if len({report["candidate"] for report in reports}) != 2:
        raise ValueError("candidate comparison repeats one finalized candidate")
    scoring_report = verify_scoring_artifact(scoring_path)
    mapping = json.loads(
        (Path(scoring_path).resolve() / "internal/review-set-mapping.json").read_text(
            encoding="utf-8"
        )
    )
    expected_candidates = {
        row["candidate"]
        for key in ("sets", "unavailable_candidates")
        for row in mapping.get(key, [])
    }
    if {report["candidate"] for report in reports} != expected_candidates:
        raise ValueError("candidate comparison does not cover every scored candidate")
    expected_bindings = {
        "scoring_manifest_sha256": scoring_report["manifest_sha256"],
        "finalized_artifacts": [
            {
                "candidate": report["candidate"],
                "review_set": report["review_set"],
                "manifest_sha256": report["manifest_sha256"],
            }
            for report in sorted(reports, key=lambda item: str(item["candidate"]))
        ],
    }
    if manifest["source_bindings"] != expected_bindings:
        raise ValueError("candidate comparison source chain is incomplete")
    retained = json.loads((root / "comparison.json").read_text(encoding="utf-8"))
    expected = _comparison_value(reports)
    if retained != expected:
        raise ValueError("candidate comparison differs from finalized evidence")
    return {
        **retained,
        "artifact_type": "fine-segmentation-comparison-v1",
        "manifest_sha256": manifest_sha,
        "output_path": str(root),
    }


def _load_manifest_verified_raw_vectors(
    vector_artifact_path: Path | str,
    vector_map: Mapping[str, object],
) -> dict[str, tuple[float, ...]]:
    """Load diagnostic f32 rows only after checking their retained identity."""

    vectors = Path(vector_artifact_path).resolve()
    manifest = json.loads((vectors / "manifest.json").read_text(encoding="utf-8"))
    raw = (vectors / "raw-vectors.f32le").read_bytes()
    identity = manifest.get("files", {}).get("raw-vectors.f32le")
    actual_identity = {
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }
    if identity != actual_identity:
        raise ValueError("raw vector bytes differ from the vector manifest")
    dimensions = vector_map.get("dimensions")
    rows = vector_map.get("vectors")
    count = vector_map.get("vector_count")
    if (
        not isinstance(dimensions, int)
        or dimensions <= 0
        or not isinstance(rows, list)
        or count != len(rows)
        or manifest.get("dimensions") != dimensions
        or manifest.get("vector_count") != count
        or len(raw) != len(rows) * dimensions * 4
    ):
        raise ValueError("raw vector shape differs from its manifest and vector map")
    by_encoding: dict[str, tuple[float, ...]] = {}
    ordinals = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("vector map row is invalid")
        ordinal = row.get("ordinal")
        encoding_id = row.get("encoding_id")
        if (
            not isinstance(ordinal, int)
            or ordinal < 0
            or ordinal >= len(rows)
            or ordinal in ordinals
            or not isinstance(encoding_id, str)
            or encoding_id in by_encoding
        ):
            raise ValueError("vector map row identity is invalid")
        values = struct.unpack_from(f"<{dimensions}f", raw, ordinal * dimensions * 4)
        if not all(math.isfinite(value) for value in values):
            raise ValueError("raw vector contains a non-finite value")
        ordinals.add(ordinal)
        by_encoding[encoding_id] = values
    if ordinals != set(range(len(rows))):
        raise ValueError("vector map ordinals are incomplete")
    return by_encoding


def prepare_scoring_artifact(
    repo_root: Path | str,
    prepared_path: Path | str,
    vector_artifact_path: Path | str,
    technical_freeze_path: Path | str,
    candidate_run_path: Path | str,
    output_path: Path | str,
) -> dict[str, object]:
    """Verify the complete run, reveal identities, score, and prepare review."""

    from sse_multivector.fine_segmentation_candidate_runs import (
        verify_candidate_suite_runs,
    )
    from sse_multivector.fine_segmentation_suite import verify_prepared_suite

    root = Path(repo_root).resolve()
    prepared = Path(prepared_path).resolve()
    vectors = Path(vector_artifact_path).resolve()
    freeze_path = Path(technical_freeze_path).resolve()
    runs = Path(candidate_run_path).resolve()
    prepared_report = verify_prepared_suite(root, prepared)
    run_report = verify_candidate_suite_runs(prepared, vectors, freeze_path, runs)
    if run_report.get("complete") is not True:
        raise ValueError("candidate run is not complete")
    protocol = json.loads((prepared / "protocol.json").read_text(encoding="utf-8"))
    private = json.loads(
        (prepared / "blinding-private.json").read_text(encoding="utf-8")
    )
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    review_private = private.get("experiment_02_review")
    if not isinstance(review_private, dict):
        raise ValueError("prepared suite is missing its frozen review seed")
    try:
        review_seed = bytes.fromhex(str(review_private["seed_hex"]))
    except (KeyError, ValueError) as error:
        raise ValueError("prepared Experiment 2 review seed is invalid") from error
    commitment = review_seed_commitment(review_seed)
    if (
        review_private.get("commitment") != commitment
        or prepared_report.get("experiment_02_review_commitment") != commitment
        or freeze.get("experiment_02_review_commitment") != commitment
    ):
        raise ValueError("Experiment 2 review seed differs from the technical freeze")

    evidence = {}
    for candidate in ("hdbscan", "snn"):
        outputs = load_verified_candidate_outputs(protocol, runs, candidate)
        identities = {record["candidate_identity"] for record in outputs.values()}
        if len(identities) != 1:
            raise ValueError(f"{candidate} runner outputs have conflicting identities")
        evidence[candidate] = build_candidate_evidence(
            protocol,
            outputs,
            candidate_identity=next(iter(identities)),
            review_seed=review_seed,
        )
    vector_map = json.loads((vectors / "vector-map.json").read_text(encoding="utf-8"))
    vectors_by_encoding = _load_manifest_verified_raw_vectors(vectors, vector_map)
    shared_diagnostics = build_representation_diagnostics(
        protocol,
        vectors_by_encoding,
        {str(row["encoding_id"]): row for row in vector_map["vectors"]},
    )
    source_bindings = {
        "prepared_manifest_sha256": hashlib.sha256(
            (prepared / "manifest.json").read_bytes()
        ).hexdigest(),
        "protocol_sha256": hashlib.sha256(
            (prepared / "protocol.json").read_bytes()
        ).hexdigest(),
        "vector_manifest_sha256": hashlib.sha256(
            (vectors / "manifest.json").read_bytes()
        ).hexdigest(),
        "technical_freeze_sha256": hashlib.sha256(freeze_path.read_bytes()).hexdigest(),
        "candidate_run_manifest_sha256": hashlib.sha256(
            (runs / "manifest.json").read_bytes()
        ).hexdigest(),
        "candidate_run_completion_sha256": hashlib.sha256(
            (runs / "completion.json").read_bytes()
        ).hexdigest(),
        "candidate_run_record_set_sha256": run_report["run_record_set_sha256"],
    }
    return write_scoring_artifact(
        output_path,
        evidence,
        review_seed=review_seed,
        source_bindings=source_bindings,
        shared_diagnostics=shared_diagnostics,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare = subparsers.add_parser("prepare-review")
    prepare.add_argument("repo_root", type=Path)
    prepare.add_argument("prepared", type=Path)
    prepare.add_argument("vectors", type=Path)
    prepare.add_argument("technical_freeze", type=Path)
    prepare.add_argument("candidate_runs", type=Path)
    prepare.add_argument("output", type=Path)
    verify = subparsers.add_parser("verify")
    verify.add_argument("output", type=Path)
    apply_review = subparsers.add_parser("apply-review")
    apply_review.add_argument("scoring", type=Path)
    apply_review.add_argument("review_set")
    apply_review.add_argument("response", type=Path)
    apply_review.add_argument("output", type=Path)
    verify_reviewed = subparsers.add_parser("verify-reviewed")
    verify_reviewed.add_argument("scoring", type=Path)
    verify_reviewed.add_argument("reviewed", type=Path)
    finalize = subparsers.add_parser("finalize-decision")
    finalize.add_argument("scoring", type=Path)
    finalize.add_argument("reviewed", type=Path)
    finalize.add_argument("response", type=Path)
    finalize.add_argument("output", type=Path)
    finalize_unavailable = subparsers.add_parser("finalize-unavailable")
    finalize_unavailable.add_argument("scoring", type=Path)
    finalize_unavailable.add_argument("candidate")
    finalize_unavailable.add_argument("response", type=Path)
    finalize_unavailable.add_argument("output", type=Path)
    verify_finalized = subparsers.add_parser("verify-finalized")
    verify_finalized.add_argument("scoring", type=Path)
    verify_finalized.add_argument("finalized", type=Path)
    compare = subparsers.add_parser("prepare-comparison")
    compare.add_argument("scoring", type=Path)
    compare.add_argument("finalized", type=Path, nargs=2)
    compare.add_argument("output", type=Path)
    verify_comparison = subparsers.add_parser("verify-comparison")
    verify_comparison.add_argument("scoring", type=Path)
    verify_comparison.add_argument("finalized", type=Path, nargs=2)
    verify_comparison.add_argument("comparison", type=Path)
    prepare_post_hoc = subparsers.add_parser("prepare-post-hoc-review")
    prepare_post_hoc.add_argument("scoring", type=Path)
    prepare_post_hoc.add_argument("output", type=Path)
    verify_post_hoc = subparsers.add_parser("verify-post-hoc-review")
    verify_post_hoc.add_argument("scoring", type=Path)
    verify_post_hoc.add_argument("review", type=Path)
    apply_post_hoc = subparsers.add_parser("apply-post-hoc-review")
    apply_post_hoc.add_argument("scoring", type=Path)
    apply_post_hoc.add_argument("review", type=Path)
    apply_post_hoc.add_argument("response", type=Path)
    apply_post_hoc.add_argument("output", type=Path)
    verify_post_hoc_reviewed = subparsers.add_parser("verify-post-hoc-reviewed")
    verify_post_hoc_reviewed.add_argument("scoring", type=Path)
    verify_post_hoc_reviewed.add_argument("review", type=Path)
    verify_post_hoc_reviewed.add_argument("reviewed", type=Path)
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.command == "prepare-review":
        report = prepare_scoring_artifact(
            args.repo_root,
            args.prepared,
            args.vectors,
            args.technical_freeze,
            args.candidate_runs,
            args.output,
        )
    elif args.command == "verify":
        report = verify_scoring_artifact(args.output)
    elif args.command == "apply-review":
        response = json.loads(args.response.read_text(encoding="utf-8"))
        result = write_reviewed_scoring_artifact(
            args.scoring, args.review_set, response, args.output
        )
        report = {
            key: result[key]
            for key in (
                "artifact_type",
                "manifest_sha256",
                "output_path",
                "review_set",
            )
        }
        report["review_status"] = result["evidence"]["review_status"]
        report["next_action"] = "candidate disposition and written rationale"
    elif args.command == "verify-reviewed":
        result = verify_reviewed_scoring_artifact(args.scoring, args.reviewed)
        report = {
            key: result[key]
            for key in (
                "artifact_type",
                "manifest_sha256",
                "output_path",
                "review_set",
            )
        }
        report.update(
            {
                "review_status": result["evidence"]["review_status"],
                "next_action": "candidate disposition and written rationale",
            }
        )
    elif args.command == "finalize-decision":
        response = json.loads(args.response.read_text(encoding="utf-8"))
        result = write_finalized_scoring_artifact(
            args.scoring, args.reviewed, response, args.output
        )
        report = {
            key: result[key]
            for key in (
                "artifact_type",
                "manifest_sha256",
                "output_path",
                "review_set",
            )
        }
        report.update(
            {
                "user_disposition": result["evidence"]["user_disposition"],
                "candidate_selection": result["evidence"]["candidate_selection"],
            }
        )
    elif args.command == "finalize-unavailable":
        response = json.loads(args.response.read_text(encoding="utf-8"))
        result = write_unavailable_finalized_scoring_artifact(
            args.scoring, args.candidate, response, args.output
        )
        report = {
            key: result[key]
            for key in (
                "artifact_type",
                "manifest_sha256",
                "output_path",
            )
        }
        report.update(
            {
                "candidate": result["candidate"],
                "user_disposition": result["evidence"]["user_disposition"],
                "candidate_selection": result["evidence"]["candidate_selection"],
            }
        )
    elif args.command == "verify-finalized":
        result = verify_finalized_scoring_artifact(args.scoring, args.finalized)
        report = {
            key: result[key]
            for key in (
                "artifact_type",
                "manifest_sha256",
                "output_path",
                "review_set",
            )
        }
        report.update(
            {
                "user_disposition": result["evidence"]["user_disposition"],
                "candidate_selection": result["evidence"]["candidate_selection"],
            }
        )
    elif args.command == "prepare-comparison":
        result = write_candidate_comparison_artifact(
            args.scoring, args.finalized, args.output
        )
        report = {
            "artifact_type": result["artifact_type"],
            "manifest_sha256": result["manifest_sha256"],
            "output_path": result["output_path"],
            "assistant_recommendation": result["assistant_recommendation"],
            "candidate_selection": result["candidate_selection"],
        }
    elif args.command == "verify-comparison":
        result = verify_candidate_comparison_artifact(
            args.scoring, args.finalized, args.comparison
        )
        report = {
            "artifact_type": result["artifact_type"],
            "manifest_sha256": result["manifest_sha256"],
            "output_path": result["output_path"],
            "assistant_recommendation": result["assistant_recommendation"],
            "candidate_selection": result["candidate_selection"],
        }
    elif args.command == "prepare-post-hoc-review":
        result = write_post_hoc_hdbscan_review_artifact(args.scoring, args.output)
        report = {
            key: result[key]
            for key in (
                "artifact_type",
                "manifest_sha256",
                "output_path",
                "packet_count",
                "occurrence_count",
            )
        }
    elif args.command == "verify-post-hoc-review":
        result = verify_post_hoc_hdbscan_review_artifact(args.scoring, args.review)
        report = {
            key: result[key]
            for key in (
                "artifact_type",
                "manifest_sha256",
                "output_path",
                "packet_count",
                "occurrence_count",
            )
        }
    elif args.command == "apply-post-hoc-review":
        response = json.loads(args.response.read_text(encoding="utf-8"))
        result = write_post_hoc_hdbscan_reviewed_artifact(
            args.scoring, args.review, response, args.output
        )
        report = {
            key: result[key]
            for key in (
                "artifact_type",
                "manifest_sha256",
                "output_path",
                "judgment_count",
                "occurrence_count",
                "source_review_status",
                "proceed_eligible",
            )
        }
    elif args.command == "verify-post-hoc-reviewed":
        result = verify_post_hoc_hdbscan_reviewed_artifact(
            args.scoring, args.review, args.reviewed
        )
        report = {
            key: result[key]
            for key in (
                "artifact_type",
                "manifest_sha256",
                "output_path",
                "judgment_count",
                "occurrence_count",
                "source_review_status",
                "proceed_eligible",
            )
        }
    else:
        raise AssertionError(f"unhandled command {args.command}")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
