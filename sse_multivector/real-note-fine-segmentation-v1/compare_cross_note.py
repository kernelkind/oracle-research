#!/usr/bin/env python3
"""Preserve prior evidence, then compare the complete cross-note-density trial."""

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_json(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(
            value, stream, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False
        )
        stream.write("\n")


def snapshot(root, paths):
    return {
        str(path.relative_to(root)): {"sha256": sha(path), "bytes": path.stat().st_size}
        for path in sorted(paths)
    }


def verify_snapshot(root, saved):
    for name, identity in saved.items():
        path = root / name
        if (
            not path.is_file()
            or path.stat().st_size != identity["bytes"]
            or sha(path) != identity["sha256"]
        ):
            raise ValueError(f"previous evidence was not preserved: {name}")


def partition(packets, unassigned):
    by_segment, by_vector, evidence = {}, {}, {}
    for item in packets:
        key = item["packet"]
        if key in by_segment:
            raise ValueError("duplicate segment")
        by_segment[key] = item
        for instance in item["instances"]:
            member = instance["vector_id"]
            if member in by_vector:
                raise ValueError("duplicate vector membership")
            by_vector[member] = key
            evidence[member] = instance
    for member in unassigned:
        if member in by_vector:
            raise ValueError("duplicate unassigned membership")
        by_vector[member] = None
    return by_segment, by_vector, evidence


def multi_note(item):
    return len({row["note_id"] for row in item["instances"]}) > 1


def verify_partition(packets, unassigned, fine_output):
    actual = sorted(
        sorted(row["vector_id"] for row in item["instances"]) for item in packets
    )
    expected = sorted(sorted(members) for members in fine_output["segments"])
    if actual != expected or sorted(unassigned) != sorted(fine_output["unassigned"]):
        raise ValueError(
            "packaged memberships differ from the replayed candidate result"
        )


def compare(old_packets, old_unassigned, new_packets, new_unassigned):
    old, old_membership, old_evidence = partition(old_packets, old_unassigned)
    new, new_membership, new_evidence = partition(new_packets, new_unassigned)
    if old_membership.keys() != new_membership.keys():
        raise ValueError("vector universe differs")
    for member in old_evidence.keys() & new_evidence.keys():
        if old_evidence[member] != new_evidence[member]:
            raise ValueError("source evidence differs")
    unchanged = sorted(old.keys() & new.keys())
    if any(old[key] != new[key] for key in unchanged):
        raise ValueError("same segment identity has different evidence")

    def counts(groups, noise):
        return {
            "segments": len(groups),
            "multi_note_segments": sum(
                multi_note(packet) for packet in groups.values()
            ),
            "one_note_segments": sum(
                not multi_note(packet) for packet in groups.values()
            ),
            "assigned_vectors": sum(
                len(packet["instances"]) for packet in groups.values()
            ),
            "unassigned_vectors": len(noise),
            "vectors_in_multi_note_segments": sum(
                len(packet["instances"])
                for packet in groups.values()
                if multi_note(packet)
            ),
        }

    destinations = {}
    for key, item in old.items():
        members = [row["vector_id"] for row in item["instances"]]
        placed = sorted(
            {
                new_membership[member]
                for member in members
                if new_membership[member] is not None
            }
        )
        destinations[key] = {
            "segments": placed,
            "multi_note_segments": [key for key in placed if multi_note(new[key])],
            "unassigned_vectors": [
                member for member in members if new_membership[member] is None
            ],
            "all_members_together": len(placed) == 1
            and all(new_membership[member] is not None for member in members),
            "exactly_unchanged": key in unchanged,
        }
    new_review = [
        new[key] for key in sorted(new.keys() - old.keys()) if multi_note(new[key])
    ]
    return {
        "baseline": counts(old, old_unassigned),
        "trial": counts(new, new_unassigned),
        "exactly_unchanged_segments": unchanged,
        "new_segments": sorted(new.keys() - old.keys()),
        "baseline_segments_changed": sorted(old.keys() - new.keys()),
        "baseline_multi_note_segments_changed": sorted(
            key for key in old.keys() - new.keys() if multi_note(old[key])
        ),
        "newly_unassigned_vectors": sorted(set(new_unassigned) - set(old_unassigned)),
        "newly_assigned_vectors": sorted(set(old_unassigned) - set(new_unassigned)),
        "baseline_segment_destinations": destinations,
        "user_review_segments": [item["packet"] for item in new_review],
    }, new_review


def freeze():
    destination = ROOT / "cross-note-density-v1"
    destination.mkdir(exist_ok=False)
    paths = [ROOT / "reviewed-input.json", ROOT / "corpus-selection-v1/notes.json"]
    for name in (
        "vectors",
        "hdbscan-baseline",
        "hdbscan-leaf",
        "hdbscan-density",
        "review-handoff",
        "omission-audit-v1/report",
    ):
        paths.extend(path for path in (ROOT / name).rglob("*") if path.is_file())
    saved = snapshot(ROOT, paths)
    write_json(destination / "preserved-before.json", saved)
    print(
        json.dumps(
            {
                "preserved_files": len(saved),
                "bytes": sum(item["bytes"] for item in saved.values()),
            }
        )
    )


def analyze():
    destination = ROOT / "cross-note-density-v1"
    saved = read(destination / "preserved-before.json")
    verify_snapshot(ROOT, saved)
    baseline = ROOT / "hdbscan-baseline"
    trial = ROOT / "hdbscan-cross-note"
    proof = read(trial / "replay-proof.json")
    if not proof["full_parsed_response_equal"]:
        raise ValueError("trial full replay was not verified")
    for name, digest in proof["files"].items():
        if sha(trial / name) != digest:
            raise ValueError(f"trial replay evidence changed: {name}")
    original_request = read(ROOT / "vectors/candidate-request.json")
    changed_request = read(trial / "request.json")
    if changed_request.pop("candidate") != "hdbscan_cross_note":
        raise ValueError("incorrect trial candidate")
    note_map = changed_request.pop("source_note_ids")
    expected_map = {
        row["vector_id"]: row["note_id"]
        for row in read(ROOT / "vectors/vector-map.json")["vectors"]
    }
    if note_map != expected_map:
        raise ValueError("trial source-note map differs")
    changed_request["candidate"] = "hdbscan"
    if changed_request != original_request:
        raise ValueError("trial changed other request inputs")
    old_review = read(baseline / "review/review.json")
    new_review = read(trial / "review/review.json")
    old_noise = read(baseline / "review/unassigned.json")["instances"]
    new_noise = read(trial / "review/unassigned.json")["instances"]
    for run, review, noise in (
        (baseline, old_review, old_noise),
        (trial, new_review, new_noise),
    ):
        response = read(run / "response.json")
        verify_partition(
            review["packets"],
            [row["vector_id"] for row in noise],
            response["artifact"]["result"]["fine_output"],
        )
    old_all = {
        row["vector_id"]: row for p in old_review["packets"] for row in p["instances"]
    }
    new_all = {
        row["vector_id"]: row for p in new_review["packets"] for row in p["instances"]
    }
    old_all.update({row["vector_id"]: row for row in old_noise})
    new_all.update({row["vector_id"]: row for row in new_noise})
    if old_all != new_all:
        raise ValueError("complete source evidence changed")
    result, packets = compare(
        old_review["packets"],
        [row["vector_id"] for row in old_noise],
        new_review["packets"],
        [row["vector_id"] for row in new_noise],
    )
    _, old_membership, _ = partition(
        old_review["packets"], [row["vector_id"] for row in old_noise]
    )
    new_groups, new_membership, _ = partition(
        new_review["packets"], [row["vector_id"] for row in new_noise]
    )
    pair_root = ROOT / "omission-audit-v1/report/disagreements"
    judgments = {
        row["packet"]: row
        for row in read(pair_root / "user-response.json")["judgments"]
    }
    pair_results = []
    for pair in read(pair_root / "review.json")["packets"]:
        members = [row["vector_id"] for row in pair["instances"]]
        groups = [new_membership[member] for member in members]
        shared = groups[0] if groups[0] is not None and len(set(groups)) == 1 else None
        pair_results.append(
            {
                "pair": pair["packet"],
                "user_verdict": judgments[pair["packet"]]["verdict"],
                "vectors": [row["instance"] for row in pair["instances"]],
                "baseline_segments": [old_membership[member] for member in members],
                "trial_segments": groups,
                "together_in_trial": shared is not None,
                "trial_segment_vector_count": len(new_groups[shared]["instances"])
                if shared
                else None,
            }
        )
    result.update(
        {
            "schema_version": 1,
            "preserved_files": len(saved),
            "original_evidence_unchanged": True,
            "user_reviewed_pairs": pair_results,
            "vector_labels": {
                key: row["instance"] for key, row in sorted(old_all.items())
            },
            "source_files": {
                str(path.relative_to(ROOT)): sha(path)
                for path in (
                    trial / "replay-proof.json",
                    baseline / "review/review.json",
                    trial / "review/review.json",
                    pair_root / "review.json",
                    pair_root / "user-response.json",
                )
            },
        }
    )
    review_id = (
        "RN"
        + hashlib.sha256(
            json.dumps([p["packet"] for p in packets]).encode()
        ).hexdigest()[:12]
    )
    output_review = dict(new_review, review_set=review_id, packets=packets)
    output_review["response_contract"] = dict(
        new_review["response_contract"], review_set=review_id
    )
    write_json(destination / "comparison.json", result)
    write_json(destination / "review.json", output_review)
    write_json(
        destination / "preserved-after.json",
        {
            "unchanged": True,
            "files": len(saved),
            "before_sha256": sha(destination / "preserved-before.json"),
        },
    )
    print(
        json.dumps(
            {key: result[key] for key in ("baseline", "trial", "user_reviewed_pairs")},
            indent=2,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("freeze", "compare", "verify-preserved"))
    args = parser.parse_args()
    if args.action == "freeze":
        freeze()
    elif args.action == "compare":
        analyze()
    else:
        saved = read(ROOT / "cross-note-density-v1/preserved-before.json")
        verify_snapshot(ROOT, saved)
        print(f"All {len(saved)} preserved files are unchanged.")
