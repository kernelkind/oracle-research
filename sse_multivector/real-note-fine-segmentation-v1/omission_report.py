#!/usr/bin/env python3
"""Package saved omission judgments without estimating prevalence or regrouping."""

from __future__ import annotations

import argparse
from collections import Counter
import copy
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from sse_multivector.real_note_segmentation import _canonical, _identity, _new_output, _sha


VERDICTS = ("valid", "invalid", "uncertain")


def _counts(rows):
    return {
        "reviewed": len(rows),
        "verdicts": {who: {v: sum(r[who]["verdict"] == v for r in rows) for v in VERDICTS}
                     for who in ("A", "B", "primary")},
        "all_three_valid": sum(r["all_three_valid"] for r in rows),
        "any_valid_not_all_valid": sum(r["any_valid_not_all_valid"] for r in rows),
        "no_valid": sum(not r["any_valid"] for r in rows),
    }


def _groups(rows, instances, excluded, noise):
    result = {}
    for name, selected in {
        "all_reviewed": rows,
        "agreements": [r for r in rows if r["all_three_valid"]],
        "disagreements": [r for r in rows if r["any_valid_not_all_valid"]],
        "any_valid": [r for r in rows if r["any_valid"]],
        "primary_valid": [r for r in rows if r["primary"]["verdict"] == "valid"],
    }.items():
        all_ids = {v for r in selected for v in r["instances"]}
        affected = all_ids & excluded
        source_masks = {}
        for v in sorted(affected):
            i = instances[v]
            key = (i["note_id"], tuple(tuple(s) for s in i["byte_spans"]))
            source_masks.setdefault(key, []).append(v)
        note_ids = sorted({instances[v]["note_id"] for v in affected})
        result[name] = {
            "packet_count": len(selected), "packets": [r["packet"] for r in selected],
            "excluded_vector_ids": sorted(affected), "excluded_vector_count": len(affected),
            "distinct_source_mask_count": len(source_masks),
            "source_masks": [{"note_id": k[0], "byte_spans": [list(s) for s in k[1]], "instances": vs}
                             for k, vs in sorted(source_masks.items())],
            "excluded_note_ids": note_ids, "excluded_note_count": len(note_ids),
            "all_pair_note_count": len({instances[v]["note_id"] for v in all_ids}),
            "baseline_noise_ids": sorted(affected & noise), "baseline_noise_count": len(affected & noise),
            "baseline_one_note_ids": sorted(affected - noise), "baseline_one_note_count": len(affected - noise),
        }
    return result


def build_report(audit, output):
    audit, output = Path(audit), Path(output)
    _new_output(output)
    paths = ("sample/review.json", "sample/sampling-manifest.json", "judgments.json", "primary-review.json",
             "inventory/manifest.json", "inventory/excluded-ids.json", "../hdbscan-baseline/review/unassigned.json")
    raw = {p: (audit / p).read_bytes() for p in paths}
    documents = {p: json.loads(v) for p, v in raw.items()}
    review, sampling = documents[paths[0]], documents[paths[1]]
    models, primary = documents[paths[2]], documents[paths[3]]
    inventory = documents[paths[4]]
    checks = [
        (sampling["files"]["review.json"], _identity(raw[paths[0]])),
        (sampling["audit_manifest"], _identity(raw[paths[4]])),
        (inventory["files"]["excluded-ids.json"], _identity(raw[paths[5]])),
        (inventory["sources"]["hdbscan-baseline/review/unassigned.json"], _identity(raw[paths[6]])),
        (models.get("source_review_sha256"), _sha(raw[paths[0]])),
        (primary.get("source_review_sha256"), _sha(raw[paths[0]])),
    ]
    if any(expected != actual for expected, actual in checks):
        raise ValueError("source hash binding mismatch")
    if review.get("schema_version") != 3 or review["response_contract"]["review_set"] != review["review_set"]:
        raise ValueError("invalid v3 review contract")
    packets = review["packets"]
    ids = [p["packet"] for p in packets]
    if len(ids) != 128 or len(set(ids)) != 128:
        raise ValueError("review coverage must be 128 distinct pairs")
    selected = sampling["selected"]
    if sampling["review_set"] != review["review_set"] or [r["pair_id"] for r in selected] != ids:
        raise ValueError("sampling coverage or mixed order mismatch")
    if Counter(r["stratum"] for r in selected) != {"proposed": 64, "nonproposed": 64}:
        raise ValueError("sampling stratum coverage mismatch")
    excluded_values = documents[paths[5]]
    excluded = set(excluded_values)
    if len(excluded) != len(excluded_values):
        raise ValueError("duplicate excluded IDs")
    noise = {i["instance"] for i in documents[paths[6]]["instances"]}
    if not noise <= excluded:
        raise ValueError("baseline noise lies outside excluded IDs")
    instances, fragments = {}, {}
    for p, membership in zip(packets, selected):
        if len(p["instances"]) != 2 or len({i["note_id"] for i in p["instances"]}) != 2:
            raise ValueError("review must contain cross-note pairs")
        vectors = [i["vector_id"] for i in p["instances"]]
        if p["packet"] != "S" + _sha(_canonical(sorted(vectors)))[:10]:
            raise ValueError("stable pair identity mismatch")
        if sorted(i["instance"] for i in p["instances"]) != membership["pair"]:
            raise ValueError("sampling pair evidence mismatch")
        if not excluded.intersection(membership["pair"]):
            raise ValueError("pair lacks an excluded vector")
        for i in p["instances"]:
            v = i["instance"]
            if v in instances and instances[v] != i:
                raise ValueError("inconsistent repeated vector evidence")
            encoded, previous, values = i["text"].encode("utf-8"), 0, []
            for left, right in i["byte_spans"]:
                if not 0 <= previous <= left < right <= len(encoded):
                    raise ValueError("invalid source mask spans")
                values.append(encoded[left:right].decode("utf-8"))
                previous = right
            if not values:
                raise ValueError("empty source mask")
            instances[v], fragments[v] = i, values
    rounds = {}
    for round_ in models["rounds"]:
        name = round_["round"]
        if name in rounds or name not in ("A", "B"):
            raise ValueError("duplicate or unknown judgment round")
        judgments = round_["judgments"]
        indexed = {j["packet"]: j for j in judgments}
        if len(indexed) != len(judgments) or set(indexed) != set(ids):
            raise ValueError(f"round {name} judgment coverage mismatch")
        if any(j["verdict"] not in VERDICTS or not isinstance(j.get("comment"), str) for j in judgments):
            raise ValueError("invalid model judgment")
        rounds[name] = indexed
    if set(rounds) != {"A", "B"}:
        raise ValueError("missing model round coverage")
    recording = primary.get("recording", "")
    if "every other packet" not in recording.lower() or "explicitly judged invalid" not in recording.lower():
        raise ValueError("primary recording does not explicitly cover remaining invalid judgments")
    valid, uncertain = primary["valid"], primary["uncertain"]
    if len(set(valid)) != len(valid) or len(set(uncertain)) != len(uncertain) or set(valid) & set(uncertain) or not set(valid + uncertain) <= set(ids):
        raise ValueError("primary judgment coverage mismatch")
    rows = []
    for p, membership in zip(packets, selected):
        sid = p["packet"]
        verdict = "valid" if sid in valid else "uncertain" if sid in uncertain else "invalid"
        votes = [rounds[who][sid]["verdict"] for who in ("A", "B")] + [verdict]
        all_valid, any_valid = all(v == "valid" for v in votes), "valid" in votes
        rows.append({"packet": sid, "instances": [i["instance"] for i in p["instances"]],
                     "stratum": membership["stratum"], "A": rounds["A"][sid], "B": rounds["B"][sid],
                     "primary": {"verdict": verdict}, "all_three_valid": all_valid,
                     "any_valid": any_valid, "any_valid_not_all_valid": any_valid and not all_valid})
    files = {}
    for name, keep in (("agreements", {r["packet"] for r in rows if r["all_three_valid"]}),
                       ("disagreements", {r["packet"] for r in rows if r["any_valid_not_all_valid"]})):
        subset = copy.deepcopy(review)
        subset["packets"] = [p for p in packets if p["packet"] in keep]
        subset["review_set"] = "RN" + _sha(b"omission-report-review-v3\0" + _canonical(subset["packets"]))[:12]
        subset["response_contract"]["review_set"] = subset["review_set"]
        files[f"{name}/review.json"] = _canonical(subset)
    all_link = Path(os.path.relpath(audit / "sample/review.json", output)).as_posix()
    lines = ["# Saved omission-pair assessments", "",
             f"[All 128 pairs]({all_link}) · [All three valid](agreements/review.json) · [Some valid, not all](disagreements/review.json)", "",
             "V identifies a vector and its mask. S identifies a proposed two-mask segment, not a partition or a subject name. ⟦…⟧ encloses each exact selected fragment; separate fragments remain separate. Source text and byte ranges remain intact in the v3 review files.", "",
             "Primary recording: " + recording, "", "Primary notes: " + primary.get("judgment_notes", ""), ""]
    for row in rows:
        lines.extend(["## " + row["packet"], ""])
        for v in row["instances"]:
            mask = " ".join("⟦" + f + "⟧" for f in fragments[v])
            lines.extend([v, "", *("> " + line for line in mask.split("\n")), ""])
        for who in ("A", "B"):
            lines.extend([f"{who}: {row[who]['verdict']}. {row[who]['comment']}", ""])
        lines.extend(["Primary: " + row["primary"]["verdict"] + ".", "", "Sampling stratum: " + row["stratum"] + ".", ""])
    files["assessments.md"] = "\n".join(lines).encode("utf-8")
    summary = {
        "schema_version": 1, "source_review_set": review["review_set"],
        "scope": "Descriptive counts of the 128 saved, vector-weighted sampled pairs only. No prevalence estimate, transitive merging, source-mask prevalence claim, or subject naming.",
        "sources": {p: _identity(raw[p]) for p in paths},
        "primary_record": primary,
        "model_provenance": {"prepared_manifest_sha256": models.get("prepared_manifest_sha256"),
            "calls": [{k: call[k] for k in ("call_id", "config_sha256", "prompt_sha256", "thread_id", "run_manifest", "run_manifest_sha256", "results", "results_sha256") if k in call} for call in models.get("calls", [])]},
        "counts": _counts(rows), "groups": _groups(rows, instances, excluded, noise),
        "by_stratum": {s: {"counts": _counts([r for r in rows if r["stratum"] == s]),
                           "groups": _groups([r for r in rows if r["stratum"] == s], instances, excluded, noise)}
                       for s in ("proposed", "nonproposed")},
        "assessments": rows, "files": {name: _identity(value) for name, value in files.items()},
        "user_decisions_prefilled": False,
    }
    files["summary.json"] = _canonical(summary)
    output.mkdir(parents=True, exist_ok=False)
    for name, value in files.items():
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as destination:
            destination.write(value)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = build_report(args.audit, args.output)
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(1, f"omission report: {error}\n")
    print(json.dumps({"output": str(args.output), "counts": result["counts"]}))


if __name__ == "__main__":
    main()
