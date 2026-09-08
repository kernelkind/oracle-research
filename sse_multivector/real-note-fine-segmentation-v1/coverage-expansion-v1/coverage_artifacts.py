#!/usr/bin/env python3
"""Compose frozen old/new vector rows and compare expanded HDBv2 partitions.

No encoding or candidate execution occurs here. The unchanged run_candidate.py
must execute each request twice before comparison admits its saved review.
"""

import argparse
import hashlib
import json
import math
import struct
import sys
import tempfile
from pathlib import Path


EXPERIMENT = Path(__file__).resolve().parents[1]
ROOT = EXPERIMENT.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(EXPERIMENT))

from compare_cross_note import multi_note, partition, verify_partition  # noqa: E402
from sse_multivector.real_note_segmentation import (  # noqa: E402
    NORMALIZATION,
    _canonical,
    _compile_inputs,
    _identity,
    _new_output,
    _review_evidence,
    _write_output,
    finalize_vectors,
    package_review,
)


CANDIDATE_SHA256 = "d2c0cf7266ad46a09882c395c20e393c08eff1ab27780538219184d96df4a7d9"
CANDIDATE_IDENTITY = "hdbscan-cross-note-controlled-suite-config-v1"
PARAMETERS = {
    "min_samples": 2,
    "min_cluster_size": 2,
    "selection_method": "excess_of_mass",
}
COMPOSITION = "old-prefix-and-selected-new-note-rows-v1"


def read(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    with Path(path).open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def _source(path):
    """Replay the existing finalizer against saved receipts, without running SSE."""
    path = Path(path).resolve()
    manifest_raw, manifest, evidence, inputs = _review_evidence(path)
    files = {name: (path / name).read_bytes() for name in manifest["files"]}
    prepared_names = {
        "reviewed-input.json",
        "encoder.json",
        "subject-package.json",
        "mask-package.json",
        "worker-request.json",
        "vector-map.json",
    }
    required = prepared_names | {
        "prepared-manifest.json",
        "worker-receipt.json",
        "raw-vectors.f32le",
        "normalized-vectors.f64le",
    }
    if set(files) != required:
        raise ValueError("source must be an unchanged finalized SSE artifact")
    reviewed = json.loads(files["reviewed-input.json"])
    _, prepared_map = _compile_inputs(
        reviewed, _identity(files["reviewed-input.json"])["sha256"]
    )
    with tempfile.TemporaryDirectory(
        prefix="coverage-source-verification-"
    ) as directory:
        temporary = Path(directory)
        prepared = {name: files[name] for name in prepared_names}
        prepared["manifest.json"] = files["prepared-manifest.json"]
        prepared["vector-map.json"] = _canonical(prepared_map)
        _write_output(temporary / "prepared", prepared)
        _write_output(
            temporary / "worker",
            {
                name: files[name]
                for name in ("raw-vectors.f32le", "worker-receipt.json")
            },
        )
        finalize_vectors(
            temporary / "prepared", temporary / "worker", temporary / "replay"
        )
        for replayed in (temporary / "replay").iterdir():
            if replayed.read_bytes() != (path / replayed.name).read_bytes():
                raise ValueError(
                    f"source replay differs from saved bytes: {replayed.name}"
                )
    return {
        "path": path,
        "manifest_raw": manifest_raw,
        "manifest": manifest,
        "files": files,
        "reviewed": reviewed,
        "mapping": json.loads(files["vector-map.json"]),
        "evidence": evidence,
        "inputs": inputs,
    }


def _source_identity(source):
    return {
        "path": str(source["path"]),
        "manifest_sha256": _identity(source["manifest_raw"])["sha256"],
        "candidate_request_sha256": sha(source["path"] / "candidate-request.json"),
    }


def _composition_files(old_path, added_path, selected_note_ids):
    if not isinstance(selected_note_ids, list) or not selected_note_ids:
        raise ValueError("selected_note_ids must be a nonempty list")
    if any(not isinstance(note, str) for note in selected_note_ids) or len(
        set(selected_note_ids)
    ) != len(selected_note_ids):
        raise ValueError("selected_note_ids contains invalid or duplicate note IDs")
    old, added = _source(old_path), _source(added_path)
    old_notes = old["reviewed"]["notes"]
    new_notes = {note["note_id"]: note for note in added["reviewed"]["notes"]}
    if {note["note_id"] for note in old_notes} & new_notes.keys():
        raise ValueError("old and added source note IDs overlap")
    if set(selected_note_ids) - new_notes.keys():
        raise ValueError("selected_note_ids contains an unknown new note")
    for name in ("encoder.json", "subject-package.json", "mask-package.json"):
        if old["files"][name] != added["files"][name]:
            raise ValueError(f"source frozen descriptor differs: {name}")
    dimensions = old["manifest"]["dimensions"]
    if added["manifest"]["dimensions"] != dimensions:
        raise ValueError("source vector dimensions differ")
    composition = {
        "schema_version": 1,
        "composition": COMPOSITION,
        "adapter_sha256": sha(__file__),
        "sources": {"old": _source_identity(old), "added": _source_identity(added)},
        "selected_note_ids": selected_note_ids,
        "old_note_count": len(old_notes),
        "old_vector_count": old["manifest"]["vector_count"],
        "new_note_count": len(selected_note_ids),
    }
    reviewed = {
        "schema_version": 1,
        "notes": old_notes + [new_notes[note_id] for note_id in selected_note_ids],
        "provenance": {
            "composition": COMPOSITION,
            "source_reviewed_input_sha256": {
                name: _identity(source["files"]["reviewed-input.json"])["sha256"]
                for name, source in (("old", old), ("added", added))
            },
        },
    }
    reviewed_raw = _canonical(reviewed)
    _, mapping = _compile_inputs(reviewed, _identity(reviewed_raw)["sha256"])
    source_rows = {
        row["vector_id"]: (source, row)
        for source in (old, added)
        for row in source["mapping"]["vectors"]
    }
    raw, normalized, inputs, norms = bytearray(), bytearray(), [], []
    for mapped in mapping["vectors"]:
        source, original = source_rows[mapped["vector_id"]]
        ordinal = original["ordinal"]
        raw.extend(
            source["files"]["raw-vectors.f32le"][
                ordinal * dimensions * 4 : (ordinal + 1) * dimensions * 4
            ]
        )
        row_bytes = source["files"]["normalized-vectors.f64le"][
            ordinal * dimensions * 8 : (ordinal + 1) * dimensions * 8
        ]
        normalized.extend(row_bytes)
        values = list(struct.unpack(f"<{dimensions}d", row_bytes))
        inputs.append({"opaque_id": mapped["vector_id"], "normalized_vector": values})
        norms.append(math.sqrt(sum(value * value for value in values)))
        mapped.update(
            {
                key: original[key]
                for key in (
                    "selected_token_indices",
                    "selected_token_ids",
                    "token_count",
                )
            }
        )
    old_count = composition["old_vector_count"]
    if mapping["vectors"][:old_count] != old["mapping"]["vectors"]:
        raise ValueError("composition changed original vector IDs or evidence")
    for filename, value in (
        ("raw-vectors.f32le", raw),
        ("normalized-vectors.f64le", normalized),
    ):
        original = old["files"][filename]
        if bytes(value[: len(original)]) != original:
            raise ValueError(
                f"composition changed the original byte prefix: {filename}"
            )
    mapping["dimensions"] = dimensions
    composition["new_vector_count"] = mapping["vector_count"] - old_count
    files = {
        "reviewed-input.json": reviewed_raw,
        "vector-map.json": _canonical(mapping),
        "raw-vectors.f32le": bytes(raw),
        "normalized-vectors.f64le": bytes(normalized),
        "composition.json": _canonical(composition),
        **{
            name: old["files"][name]
            for name in ("encoder.json", "subject-package.json", "mask-package.json")
        },
    }
    for name, source in (("old", old), ("added", added)):
        files[f"source-{name}-manifest.json"] = source["manifest_raw"]
        files[f"source-{name}-worker-receipt.json"] = source["files"][
            "worker-receipt.json"
        ]
    manifest = {
        "schema_version": 1,
        "vector_count": mapping["vector_count"],
        "dimensions": dimensions,
        "raw_decode_and_normalization_contract": NORMALIZATION,
        "minimum_normalized_norm": min(norms),
        "maximum_normalized_norm": max(norms),
        "sources": composition["sources"],
        "files": {name: _identity(value) for name, value in files.items()},
    }
    files["manifest.json"] = _canonical(manifest)
    files["candidate-request.json"] = _canonical(
        {
            "schema_version": 1,
            "candidate": "hdbscan",
            "source_vector_manifest_sha256": _identity(files["manifest.json"])[
                "sha256"
            ],
            "normalized_vector_sha256": _identity(bytes(normalized))["sha256"],
            "inputs": inputs,
        }
    )
    return files, composition


def compose(old_path, added_path, selected_note_ids, output_path):
    """Append only selected new rows; retain every original row byte and ID."""
    output = Path(output_path)
    _new_output(output)
    files, composition = _composition_files(old_path, added_path, selected_note_ids)
    _write_output(output, files)
    return composition


def _verify_composition(path, old_path):
    composition = read(path / "composition.json")
    if (
        composition.get("schema_version") != 1
        or composition.get("composition") != COMPOSITION
    ):
        raise ValueError("unsupported composition artifact")
    sources = composition["sources"]
    if Path(sources["old"]["path"]).resolve() != old_path:
        raise ValueError("composition uses a different old vector artifact")
    files, expected = _composition_files(
        old_path, sources["added"]["path"], composition["selected_note_ids"]
    )
    for name, raw in files.items():
        if (path / name).read_bytes() != raw:
            raise ValueError(f"composition replay differs from saved bytes: {name}")
    return expected


def _verified_run(vectors, run):
    manifest_raw, manifest, evidence, inputs = _review_evidence(vectors)
    proof = read(run / "replay-proof.json")
    expected = {
        "schema_version": 1,
        "runner_sha256": sha(EXPERIMENT / "run_candidate.py"),
        "candidate_binary_sha256": CANDIDATE_SHA256,
        "source_vector_artifact": str(vectors),
        "source_request_sha256": sha(vectors / "candidate-request.json"),
        "candidate_identity": CANDIDATE_IDENTITY,
        "hdbscan_configuration": PARAMETERS,
        "configuration_file": None,
        "full_parsed_response_equal": True,
    }
    for name, value in expected.items():
        if proof.get(name) != value or type(proof.get(name)) is not type(value):
            raise ValueError(f"candidate replay proof differs from frozen {name}")
    binary = Path(proof["candidate_binary"]).resolve()
    if sha(binary) != CANDIDATE_SHA256:
        raise ValueError("candidate replay binary differs from its frozen pin")
    required = {
        "request.json",
        "response.json",
        "response.stderr",
        "replay.json",
        "replay.stderr",
    }
    if set(proof.get("files", {})) != required:
        raise ValueError("candidate replay proof omits required files")
    for name, digest in proof["files"].items():
        if sha(run / name) != digest:
            raise ValueError(f"candidate replay file changed: {name}")
    request = {
        "schema_version": 1,
        "candidate": "hdbscan_cross_note",
        "source_vector_manifest_sha256": _identity(manifest_raw)["sha256"],
        "normalized_vector_sha256": manifest["files"]["normalized-vectors.f64le"][
            "sha256"
        ],
        "inputs": inputs,
        "source_note_ids": {member: row["note_id"] for member, row in evidence.items()},
    }
    if read(run / "request.json") != request:
        raise ValueError(
            "candidate replay request differs from the verified HDBv2 inputs"
        )
    invocations = proof.get("invocations")
    if not isinstance(invocations, list) or len(invocations) != 2:
        raise ValueError("candidate replay requires two complete invocations")
    for invocation in invocations:
        expected_invocation = {
            "argv": [str(binary), str(run / "request.json")],
            "working_directory": str(ROOT),
            "timeout_seconds": 300,
            "return_code": 0,
            "binary_sha256_before": CANDIDATE_SHA256,
            "binary_sha256_after": CANDIDATE_SHA256,
            "request_sha256_before": sha(run / "request.json"),
            "request_sha256_after": sha(run / "request.json"),
        }
        if any(
            invocation.get(name) != value
            or type(invocation.get(name)) is not type(value)
            for name, value in expected_invocation.items()
        ):
            raise ValueError(
                "candidate replay invocation differs from frozen execution"
            )
        start, finish = (
            invocation.get("started_unix_ns"),
            invocation.get("finished_unix_ns"),
        )
        if type(start) is not int or type(finish) is not int or not 0 < start <= finish:
            raise ValueError("candidate replay invocation has invalid timestamps")
    response = read(run / "response.json")
    if (
        response != read(run / "replay.json")
        or response.get("candidate_identity") != CANDIDATE_IDENTITY
    ):
        raise ValueError("complete candidate replay responses or identities differ")
    artifact = response["artifact"]
    if (
        artifact["manifest"]["parameters"] != PARAMETERS
        or json.loads(artifact["canonical_configuration_json"]) != PARAMETERS
    ):
        raise ValueError(
            "candidate response parameters differ from frozen configuration"
        )
    with tempfile.TemporaryDirectory(
        prefix="coverage-review-verification-"
    ) as directory:
        replay = Path(directory) / "review"
        package_review(vectors, run / "response.json", replay)
        for path in replay.iterdir():
            if path.read_bytes() != (run / "review" / path.name).read_bytes():
                raise ValueError(
                    f"packaged review differs from replayed candidate membership/evidence: {path.name}"
                )
    review = read(run / "review/review.json")
    noise = read(run / "review/unassigned.json")["instances"]
    unassigned = [row["vector_id"] for row in noise]
    verify_partition(
        review["packets"], unassigned, response["artifact"]["result"]["fine_output"]
    )
    return review, unassigned, evidence


def _counts(groups, unassigned):
    return {
        "segments": len(groups),
        "multi_note_segments": sum(multi_note(packet) for packet in groups.values()),
        "one_note_segments": sum(not multi_note(packet) for packet in groups.values()),
        "assigned_vectors": sum(len(packet["instances"]) for packet in groups.values()),
        "unassigned_vectors": len(unassigned),
    }


def compare(old_vectors, old_run, combined_vectors, combined_run, output_path):
    """Verify both complete saved partitions, then separate old transitions/additions."""
    output = Path(output_path)
    _new_output(output)
    old_vectors, old_run, combined_vectors, combined_run = (
        Path(path).resolve()
        for path in (old_vectors, old_run, combined_vectors, combined_run)
    )
    composition = _verify_composition(combined_vectors, old_vectors)
    old_review, old_noise, old_evidence = _verified_run(old_vectors, old_run)
    new_review, new_noise, new_evidence = _verified_run(combined_vectors, combined_run)
    old, old_membership, _ = partition(old_review["packets"], old_noise)
    new, new_membership, _ = partition(new_review["packets"], new_noise)
    if not old_membership.keys() <= new_membership.keys():
        raise ValueError("expanded partition omits old vectors")
    if any(new_evidence[member] != item for member, item in old_evidence.items()):
        raise ValueError("expanded partition changed old source evidence")
    unchanged = sorted(old.keys() & new.keys())
    if any(old[key] != new[key] for key in unchanged):
        raise ValueError("unchanged segment identity has different evidence")
    added = sorted(new_membership.keys() - old_membership.keys())
    if len(added) != composition["new_vector_count"]:
        raise ValueError("expanded partition additions differ from composition")
    destinations = {}
    for key, packet in old.items():
        members = [row["vector_id"] for row in packet["instances"]]
        placed = sorted(
            {
                new_membership[member]
                for member in members
                if new_membership[member] is not None
            }
        )
        destinations[key] = {
            "vector_ids": members,
            "segments": placed,
            "unassigned_vectors": [
                member for member in members if new_membership[member] is None
            ],
            "all_members_together": len(placed) == 1
            and all(new_membership[member] is not None for member in members),
            "exactly_unchanged": key in unchanged,
            "added_vectors": sorted(
                member for member in added if new_membership[member] in placed
            ),
        }
    packets = [
        new[key] for key in sorted(new.keys() - old.keys()) if multi_note(new[key])
    ]
    report = {
        "schema_version": 1,
        "baseline": _counts(old, old_noise),
        "trial": _counts(new, new_noise),
        "exactly_unchanged_segments": unchanged,
        "new_segments": sorted(new.keys() - old.keys()),
        "baseline_segments_changed": sorted(old.keys() - new.keys()),
        "baseline_segment_destinations": destinations,
        "old_vector_transitions": [
            {
                "vector_id": member,
                "instance": old_evidence[member]["instance"],
                "before_segment": old_membership[member],
                "after_segment": new_membership[member],
            }
            for member in sorted(old_membership)
        ],
        "newly_assigned_old_vectors": sorted(
            member
            for member in old_membership
            if old_membership[member] is None and new_membership[member] is not None
        ),
        "newly_unassigned_old_vectors": sorted(
            member
            for member in old_membership
            if old_membership[member] is not None and new_membership[member] is None
        ),
        "additions": {
            "note_ids": composition["selected_note_ids"],
            "vector_count": len(added),
            "assigned_vectors": [
                member for member in added if new_membership[member] is not None
            ],
            "unassigned_vectors": [
                member for member in added if new_membership[member] is None
            ],
            "memberships": [
                {"vector_id": member, "segment": new_membership[member]}
                for member in added
            ],
        },
        "user_review_segments": [packet["packet"] for packet in packets],
        "sources": {
            str(path): sha(path)
            for path in (
                old_vectors / "manifest.json",
                combined_vectors / "manifest.json",
                combined_vectors / "composition.json",
                old_run / "replay-proof.json",
                combined_run / "replay-proof.json",
                old_run / "review/review.json",
                combined_run / "review/review.json",
            )
        },
    }
    review_id = (
        "RN" + _identity(_canonical([new_review["review_set"], packets]))["sha256"][:12]
    )
    review = dict(new_review, review_set=review_id, packets=packets)
    review["response_contract"] = dict(
        new_review["response_contract"], review_set=review_id
    )
    files = {"comparison.json": _canonical(report), "review.json": _canonical(review)}
    files["manifest.json"] = _canonical(
        {
            "schema_version": 1,
            "adapter_sha256": sha(__file__),
            "review_set": review_id,
            "files": {name: _identity(raw) for name, raw in files.items()},
        }
    )
    _write_output(output, files)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    command = commands.add_parser("compose")
    for name in ("old_vectors", "new_vectors", "selection", "output"):
        command.add_argument(name, type=Path)
    command = commands.add_parser("compare")
    for name in (
        "old_vectors",
        "old_run",
        "combined_vectors",
        "combined_run",
        "output",
    ):
        command.add_argument(name, type=Path)
    args = parser.parse_args()
    try:
        if args.command == "compose":
            selection = read(args.selection)
            if (
                not isinstance(selection, dict)
                or selection.get("schema_version") != 1
                or set(selection) != {"schema_version", "note_ids"}
            ):
                raise ValueError(
                    "selection requires schema_version 1 and note_ids only"
                )
            report = compose(
                args.old_vectors, args.new_vectors, selection["note_ids"], args.output
            )
        else:
            report = compare(
                args.old_vectors,
                args.old_run,
                args.combined_vectors,
                args.combined_run,
                args.output,
            )
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(1, f"coverage artifact failed: {error}\n")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
