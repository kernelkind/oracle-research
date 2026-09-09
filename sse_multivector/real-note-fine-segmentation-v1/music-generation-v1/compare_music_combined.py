#!/usr/bin/env python3
"""Compare saved music-only and food-first combined HDBv2 results by vector ID.

Print JSON to stdout; never invoke SSE or the candidate binary. Existing artifact
verification recreates finalizer/review outputs in disposable temporary folders,
but does not alter any saved input, result, review, or user decision.
"""

import argparse
import json
import sys
from pathlib import Path


sys.dont_write_bytecode = True
EXPERIMENT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXPERIMENT / "coverage-expansion-v1"))

from coverage_artifacts import (  # noqa: E402
    CANDIDATE_SHA256,
    _counts,
    _verified_run,
    _verify_composition,
    multi_note,
    partition,
    read,
    sha,
)


def stable_row(row):
    """Ignore only fields recomputed when a source note gets a new position."""
    positional = {"ordinal", "short_id", "note_short_id", "reviewed_note_index"}
    stable = {key: value for key, value in row.items() if key not in positional}
    if "reviewed_subjects" in stable:
        stable["reviewed_subjects"] = [
            {key: value for key, value in subject.items() if key not in positional}
            for subject in stable["reviewed_subjects"]
        ]
    return stable


def compare(music_vectors, music_run, combined_vectors, combined_run):
    music_vectors, music_run, combined_vectors, combined_run = (
        Path(path).resolve()
        for path in (music_vectors, music_run, combined_vectors, combined_run)
    )
    composition = read(combined_vectors / "composition.json")
    if Path(composition["sources"]["added"]["path"]).resolve() != music_vectors:
        raise ValueError("combined artifact does not use this music source")
    food_vectors = Path(composition["sources"]["old"]["path"]).resolve()
    composition = _verify_composition(combined_vectors, food_vectors)
    before_review, before_noise, before_evidence = _verified_run(
        music_vectors, music_run
    )
    after_review, after_noise, after_evidence = _verified_run(
        combined_vectors, combined_run
    )
    music_map = read(music_vectors / "vector-map.json")
    food_map = read(food_vectors / "vector-map.json")
    combined_map = read(combined_vectors / "vector-map.json")
    music_rows = {row["vector_id"]: row for row in music_map["vectors"]}
    combined_rows = {row["vector_id"]: row for row in combined_map["vectors"]}
    music_ids = set(music_rows)
    food_ids = {row["vector_id"] for row in food_map["vectors"]}
    music_notes = {row["note_id"] for row in music_map["notes"]}
    if (
        music_ids & food_ids
        or music_ids | food_ids != set(combined_rows)
        or music_ids != set(before_evidence)
        or set(combined_rows) != set(after_evidence)
        or music_notes != set(composition["selected_note_ids"])
        or len(music_ids) != composition["new_vector_count"]
    ):
        raise ValueError("composition must contain all music rows and all food rows")
    if music_map["dimensions"] != combined_map["dimensions"]:
        raise ValueError("music and combined dimensions differ")
    for member, row in music_rows.items():
        if stable_row(row) != stable_row(combined_rows[member]):
            raise ValueError(f"composition changed music vector evidence: {member}")
        for key in ("vector_id", "note_id", "text", "byte_spans"):
            if before_evidence[member][key] != after_evidence[member][key]:
                raise ValueError(f"composition changed music review {key}: {member}")
    for name, width in (("raw-vectors.f32le", 4), ("normalized-vectors.f64le", 8)):
        before_raw = (music_vectors / name).read_bytes()
        after_raw = (combined_vectors / name).read_bytes()
        stride = music_map["dimensions"] * width
        if (
            len(before_raw) != len(music_rows) * stride
            or len(after_raw) != len(combined_rows) * stride
        ):
            raise ValueError(f"unexpected vector file length: {name}")
        for member, row in music_rows.items():
            left = row["ordinal"] * stride
            right = combined_rows[member]["ordinal"] * stride
            if before_raw[left : left + stride] != after_raw[right : right + stride]:
                raise ValueError(f"composition changed music {name} row: {member}")

    before, before_membership, _ = partition(before_review["packets"], before_noise)
    after, after_membership, _ = partition(after_review["packets"], after_noise)
    before_sets = {
        key: {row["vector_id"] for row in packet["instances"]}
        for key, packet in before.items()
    }
    after_sets = {
        key: {row["vector_id"] for row in packet["instances"]}
        for key, packet in after.items()
    }
    for key in before.keys() & after.keys():
        if before_sets[key] != after_sets[key]:
            raise ValueError("same packet ID represents different vector memberships")
    unchanged = sorted(before.keys() & after.keys())
    destinations = {}
    for key, members in before_sets.items():
        placed = sorted(
            {after_membership[member] for member in members}
            - {None}
        )
        unassigned = sorted(member for member in members if after_membership[member] is None)
        destinations[key] = {
            "vector_ids": sorted(members),
            "segments": placed,
            "unassigned_vectors": unassigned,
            "all_members_together": len(placed) == 1 and not unassigned,
            "exactly_unchanged": key in unchanged,
            "destination_additions": {
                destination: sorted(after_sets[destination] - members)
                for destination in placed
            },
        }

    def multi_note_members(groups):
        return {
            row["vector_id"]
            for packet in groups.values()
            if multi_note(packet)
            for row in packet["instances"]
        } & music_ids

    before_multi, after_multi = multi_note_members(before), multi_note_members(after)
    before_notes = {before_evidence[member]["note_id"] for member in before_multi}
    after_notes = {after_evidence[member]["note_id"] for member in after_multi}
    sources = [
        Path(__file__).resolve(),
        music_vectors / "manifest.json",
        food_vectors / "manifest.json",
        combined_vectors / "manifest.json",
        combined_vectors / "composition.json",
        *(
            run / name
            for run in (music_run, combined_run)
            for name in ("replay-proof.json", "response.json", "review/review.json")
        ),
    ]
    return {
        "schema_version": 1,
        "candidate_binary_sha256": CANDIDATE_SHA256,
        "music_note_count": len(music_notes),
        "music_vector_count": len(music_ids),
        "food_vector_count": len(food_ids),
        "music_rows_and_evidence_unchanged": True,
        "music_standalone": _counts(before, before_noise),
        "combined_complete": _counts(after, after_noise),
        "exactly_unchanged_music_segments": unchanged,
        "music_segment_destinations": destinations,
        "music_vector_transitions": [
            {
                "vector_id": member,
                "note_id": before_evidence[member]["note_id"],
                "before_instance": before_evidence[member]["instance"],
                "after_instance": after_evidence[member]["instance"],
                "before_segment": before_membership[member],
                "after_segment": after_membership[member],
            }
            for member in sorted(music_ids)
        ],
        "newly_assigned_music_vectors": sorted(
            member for member in music_ids
            if before_membership[member] is None and after_membership[member] is not None
        ),
        "newly_unassigned_music_vectors": sorted(
            member for member in music_ids
            if before_membership[member] is not None and after_membership[member] is None
        ),
        "music_vectors_in_multi_note_segments": {
            "before": sorted(before_multi),
            "after": sorted(after_multi),
            "gained": sorted(after_multi - before_multi),
            "lost": sorted(before_multi - after_multi),
        },
        "music_notes_in_multi_note_segments": {
            "before": sorted(before_notes),
            "after": sorted(after_notes),
            "gained": sorted(after_notes - before_notes),
            "lost": sorted(before_notes - after_notes),
        },
        "combined_segments": {
            key: {
                "vector_ids": sorted(members),
                "music_vector_ids": sorted(members & music_ids),
                "food_vector_ids": sorted(members & food_ids),
                "note_ids": sorted({after_evidence[member]["note_id"] for member in members}),
            }
            for key, members in sorted(after_sets.items())
        },
        "combined_unassigned_vector_ids": sorted(after_noise),
        "sources": {str(path): sha(path) for path in sources},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("music_vectors", "music_run", "combined_vectors", "combined_run"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    try:
        report = compare(
            args.music_vectors, args.music_run, args.combined_vectors, args.combined_run
        )
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(1, f"music comparison failed: {error}\n")
    print(json.dumps(report, sort_keys=True, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
