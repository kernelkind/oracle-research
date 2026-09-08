#!/usr/bin/env python3
"""Reproduce the unnamed review handoff from the three saved candidate runs.

This is artifact packaging, not a combined partition or a new clustering method.
It copies exact packets, orders multi-note groups first, and avoids presenting
baseline-identical groups again in the two comparison review sets.
"""

import hashlib
import json
from pathlib import Path

from generation import write as write_json


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root = Path(__file__).resolve().parent
    destination = root / "review-handoff"
    if destination.exists():
        raise ValueError("review-handoff already exists; do not replace user evidence")
    runs = {
        name: read(root / f"hdbscan-{name}/review/review.json")
        for name in ("baseline", "leaf", "density")
    }
    baseline = {packet["packet"]: packet for packet in runs["baseline"]["packets"]}
    mapping = {"schema_version": 1, "sets": {}, "segments": {}, "user_decisions": "initially absent"}
    for name, source in runs.items():
        proof = read(root / f"hdbscan-{name}/replay-proof.json")
        if not proof["full_parsed_response_equal"]:
            raise ValueError("candidate replay was not verified")
        included, reused = [], []
        for packet in source["packets"]:
            key = packet["packet"]
            if key in baseline and packet != baseline[key]:
                raise ValueError("same segment ID has different evidence")
            mapping["segments"].setdefault(key, {"runs": []})["runs"].append(name)
            if name != "baseline" and key in baseline:
                reused.append(key)
            else:
                included.append(packet)
        included.sort(key=lambda packet: (
            len({item["note_id"] for item in packet["instances"]}) == 1,
            packet["packet"],
        ))
        output = dict(source)
        output["packets"] = included
        ordered_ids = [packet["packet"] for packet in included]
        identity = "RN" + hashlib.sha256(json.dumps(ordered_ids).encode()).hexdigest()[:12]
        output["review_set"] = identity
        output["response_contract"] = dict(output["response_contract"], review_set=identity)
        path = destination / name / "review.json"
        path.parent.mkdir(parents=True, exist_ok=False)
        write_json(path, output)
        mapping["sets"][name] = {
            "path": str(path.relative_to(destination)),
            "sha256": sha(path),
            "source_review": f"../hdbscan-{name}/review/review.json",
            "source_review_sha256": sha(root / f"hdbscan-{name}/review/review.json"),
            "configuration": proof["hdbscan_configuration"],
            "included_segments": ordered_ids,
            "identical_segments_reviewed_in_baseline": sorted(reused),
            "ungrouped_evidence": f"../hdbscan-{name}/review/unassigned.txt",
        }
        for key in ordered_ids:
            prior = mapping["segments"][key].get("review_set")
            if prior is not None:
                raise ValueError("a segment would be reviewed twice")
            mapping["segments"][key]["review_set"] = name
    write_json(destination / "manifest.json", mapping)
    print(json.dumps({name: len(value["included_segments"]) for name, value in mapping["sets"].items()}))


if __name__ == "__main__":
    main()
