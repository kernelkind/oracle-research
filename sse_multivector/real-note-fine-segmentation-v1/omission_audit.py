#!/usr/bin/env python3
"""Freeze omission proposals and a blinded, vector-weighted pair sample.

No inference, new encoding, clustering, or semantic decisions are performed.
The eligible universe is stored as little-endian uint32 index pairs rather
than repeated JSON objects. Its index order is the sorted short vector IDs.
"""

from __future__ import annotations

import argparse
from array import array
import itertools
import json
import os
from pathlib import Path
import random
import struct
import sys

# Apply before the lazy NumPy import; the standalone CLI uses one BLAS thread.
for _name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "BLIS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[_name] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sse_multivector.real_note_segmentation import (  # noqa: E402
    REVIEW_INSTRUCTIONS,
    REVIEW_QUESTION,
    REVIEW_VERDICTS,
    _canonical,
    _identity,
    _new_output,
    _review_evidence,
    _sha,
    _write_output,
)


SEED = 20260908
SAMPLE_SIZE = 64
ACCOUNTING = {"total": 945, "baseline_multi_note": 150,
              "baseline_one_note": 633, "baseline_noise": 162, "excluded": 795}
PAIR_RULE = "cross-note unordered vector pairs with at least one vector outside baseline multi-note segments"


def _load(path):
    return json.loads(Path(path).read_bytes())


def _eligible(pair, instances, excluded):
    a, b = pair
    return (a != b and a in instances and b in instances
            and instances[a]["note_id"] != instances[b]["note_id"]
            and (a in excluded or b in excluded))


def _pair_id(pair, instances):
    return "S" + _sha(_canonical(sorted(instances[v]["vector_id"] for v in pair)))[:10]


def _record(pair, instances, routes):
    return {"pair": list(pair), "pair_id": _pair_id(pair, instances), "routes": routes}


def _write_package(output, files, manifest, manifest_name="manifest.json"):
    manifest["files"] = {name: _identity(raw) for name, raw in sorted(files.items())}
    _write_output(Path(output), {**files, manifest_name: _canonical(manifest)})
    return manifest


def _partition(root, name, instances, sources):
    declaration = _load(root / f"hdbscan-{name}/review/manifest.json")
    if declaration.get("schema_version") != 1:
        raise ValueError(f"unsupported {name} review manifest")
    documents = []
    for filename in ("review.json", "unassigned.json"):
        relative = f"hdbscan-{name}/review/{filename}"
        raw = (root / relative).read_bytes()
        if declaration.get("files", {}).get(filename) != _identity(raw):
            raise ValueError(f"{name} review manifest hash mismatch: {filename}")
        sources[relative] = _identity(raw)
        documents.append(json.loads(raw))
    review, noise = documents
    if review.get("schema_version") != 3 or noise.get("kind") != "unassigned":
        raise ValueError(f"unsupported {name} review schema")
    seen, segment_ids, groups = set(), set(), []
    for segment in review["packets"]:
        if not segment["instances"] or segment["packet"] in segment_ids:
            raise ValueError(f"invalid {name} segment membership")
        segment_ids.add(segment["packet"])
        groups.append((segment["packet"], segment["instances"]))
    for _, members in [*groups, (None, noise["instances"])]:
        for instance in members:
            v = instance["instance"]
            if v in seen or v not in instances or instance != instances[v]:
                raise ValueError(f"{name} partition has duplicate or changed source evidence: {v}")
            seen.add(v)
    if seen != set(instances):
        raise ValueError(f"{name} partition does not account for every vector")
    return groups, {i["instance"] for i in noise["instances"]}


def prepare(root, output):
    """Verify frozen artifacts and export all eligible proposal routes."""
    root, output = Path(root), Path(output)
    _new_output(output)
    manifest_raw, vector_manifest, evidence, vector_inputs = _review_evidence(root / "vectors")
    instances = {i["instance"]: i for i in evidence.values()}
    if len(instances) != len(evidence):
        raise ValueError("duplicate short vector IDs")
    ids = sorted(instances)
    sources = {"vectors/manifest.json": _identity(manifest_raw)}
    for name, identity in vector_manifest["files"].items():
        sources[f"vectors/{name}"] = identity
    partitions = {name: _partition(root, name, instances, sources) for name in ("baseline", "leaf", "density")}
    covered, one_note = set(), set()
    for _, members in partitions["baseline"][0]:
        target = covered if len({i["note_id"] for i in members}) > 1 else one_note
        target.update(i["instance"] for i in members)
    excluded = set(ids) - covered
    accounting = {"total": len(ids), "baseline_multi_note": len(covered),
                  "baseline_one_note": len(one_note), "baseline_noise": len(partitions["baseline"][1]),
                  "excluded": len(excluded)}
    if accounting != ACCOUNTING:
        raise ValueError(f"frozen baseline accounting mismatch: {accounting}")

    aliases = {}
    for v in ids:
        i = instances[v]
        key = (i["note_id"], tuple(tuple(span) for span in i["byte_spans"]))
        aliases.setdefault(key, []).append(v)
    excluded_keys = {key for key, vs in aliases.items() if set(vs) & excluded}
    source_masks = {
        "distinct_total": len(aliases), "distinct_excluded": len(excluded_keys),
        "vector_alias_count": len(ids) - len(aliases),
        "excluded_vector_alias_count": len(excluded) - len(excluded_keys),
        "excluded_aliases_of_covered_source_masks": sum(len(set(vs) & excluded) for vs in aliases.values() if set(vs) & covered),
        "alias_groups": [{"note_id": key[0], "byte_spans": [list(s) for s in key[1]], "vector_ids": vs}
                         for key, vs in sorted(aliases.items()) if len(vs) > 1],
    }
    universe = array("I")
    for a, b in itertools.combinations(range(len(ids)), 2):
        if _eligible((ids[a], ids[b]), instances, excluded):
            universe.extend((a, b))
    if universe.itemsize != 4:
        raise ValueError("uint32 pair storage unavailable")
    if sys.byteorder != "little":
        universe.byteswap()

    routes = {}
    for name in ("leaf", "density"):
        for segment, members in partitions[name][0]:
            if len({i["note_id"] for i in members}) < 2:
                continue
            for pair in itertools.combinations(sorted(i["instance"] for i in members), 2):
                if _eligible(pair, instances, excluded):
                    routes.setdefault(pair, []).append({"kind": f"{name}_comembership", "segment": segment})

    import numpy as np

    matrix = np.asarray([i["normalized_vector"] for i in vector_inputs], dtype=np.float64)
    cosines = matrix @ matrix.T  # 945 x 945 float64: 7,144,200 bytes.
    rows = {i["opaque_id"]: row for row, i in enumerate(vector_inputs)}
    for source in sorted(excluded):
        source_i = instances[source]
        best = {}
        for partner in ids:
            i = instances[partner]
            if i["note_id"] == source_i["note_id"]:
                continue
            cosine = float(cosines[rows[source_i["vector_id"]], rows[i["vector_id"]]])
            candidate = (-cosine, i["vector_id"], partner)
            note = i["note_id"]
            if note not in best or candidate < best[note]:
                best[note] = candidate
        ranked = sorted((value[0], note, value[1], value[2]) for note, value in best.items())[:3]
        if len(ranked) != 3:
            raise ValueError("excluded vector has fewer than three other notes")
        for rank, (negative_cosine, note, _, partner) in enumerate(ranked, 1):
            pair = tuple(sorted((source, partner)))
            routes.setdefault(pair, []).append({"kind": "cosine_top3", "source": source,
                                                "partner": partner, "partner_note_id": note,
                                                "rank": rank, "cosine": -negative_cosine})
    candidates = [_record(pair, instances, sorted(rs, key=_canonical)) for pair, rs in sorted(routes.items())]
    if len({p["pair_id"] for p in candidates}) != len(candidates):
        raise ValueError("stable pair ID collision")
    catalog = [{"id": v, "note_id": instances[v]["note_id"],
                "fragments": [instances[v]["text"].encode("utf-8")[a:b].decode("utf-8") for a, b in instances[v]["byte_spans"]]}
               for v in ids]
    files = {"instances.json": _canonical([instances[v] for v in ids]),
             "mask-catalog.json": _canonical(catalog), "excluded-ids.json": _canonical(sorted(excluded)),
             "candidates.json": _canonical(candidates), "universe.u32le": universe.tobytes()}
    return _write_package(output, files, {
        "schema_version": 1, "kind": "omission-audit-prepared", "sources": sources,
        "accounting": accounting, "source_mask_accounting": source_masks,
        "unit": "vector-weighted eligible vector pairs; not source-mask prevalence",
        "pair_eligibility": PAIR_RULE,
        "universe": {"format": "row-major-u32le-index-pairs-v1", "index_order": ids,
                     "pair_count": len(universe) // 2},
        "candidate_count": len(candidates), "cosine_matrix_bytes": int(cosines.nbytes),
        "top3_rule": "highest cosine per distinct other note, ties by full vector ID; rank notes by descending cosine, full note ID, full vector ID",
        "blas_threads": 1, "conclusions": None,
    })


def sample(audit, text_proposals, output):
    """Freeze the union and sample 64 pairs from it and 64 from its complement."""
    audit, output = Path(audit), Path(output)
    _new_output(output)
    manifest_raw = (audit / "manifest.json").read_bytes()
    manifest = json.loads(manifest_raw)
    if manifest.get("kind") != "omission-audit-prepared" or manifest.get("schema_version") != 1:
        raise ValueError("unsupported prepared omission audit")
    files = {}
    for name, identity in manifest["files"].items():
        if Path(name).name != name:
            raise ValueError("invalid audit filename")
        raw = (audit / name).read_bytes()
        if _identity(raw) != identity:
            raise ValueError(f"audit hash mismatch: {name}")
        files[name] = raw
    instances = {i["instance"]: i for i in json.loads(files["instances.json"])}
    ids = manifest["universe"]["index_order"]
    excluded = set(json.loads(files["excluded-ids.json"]))
    if ids != sorted(instances) or len(files["universe.u32le"]) != 8 * manifest["universe"]["pair_count"]:
        raise ValueError("audit universe shape mismatch")
    routes = {tuple(p["pair"]): list(p["routes"]) for p in json.loads(files["candidates.json"])}
    proposal_raw = Path(text_proposals).read_bytes()
    proposals = json.loads(proposal_raw)
    if not isinstance(proposals, list):
        raise ValueError("text proposals must be a list of two-ID pairs")
    for raw_pair in proposals:
        if not isinstance(raw_pair, list) or len(raw_pair) != 2 or not all(isinstance(v, str) for v in raw_pair):
            raise ValueError("invalid text-proposal pair")
        pair = tuple(sorted(raw_pair))
        if not _eligible(pair, instances, excluded):
            raise ValueError(f"ineligible text-proposal pair: {pair}")
        if {"kind": "text_proposal"} not in routes.setdefault(pair, []):
            routes[pair].append({"kind": "text_proposal"})
    if any(not _eligible(pair, instances, excluded) for pair in routes):
        raise ValueError("ineligible prepared candidate")
    pool = [_record(pair, instances, sorted(rs, key=_canonical)) for pair, rs in sorted(routes.items())]
    populations = {"proposed": len(pool), "nonproposed": manifest["universe"]["pair_count"] - len(pool)}
    if min(populations.values()) < SAMPLE_SIZE:
        raise ValueError(f"each sampling stratum requires at least {SAMPLE_SIZE} pairs: {populations}")
    rng = random.Random(SEED)
    chosen = [(tuple(p["pair"]), "proposed") for p in rng.sample(pool, SAMPLE_SIZE)]
    residual_ranks = set(rng.sample(range(populations["nonproposed"]), SAMPLE_SIZE))
    residual_count = 0
    for a, b in struct.iter_unpack("<II", files["universe.u32le"]):
        pair = (ids[a], ids[b])
        if pair in routes:
            continue
        if residual_count in residual_ranks:
            chosen.append((pair, "nonproposed"))
        residual_count += 1
    if residual_count != populations["nonproposed"] or len(chosen) != SAMPLE_SIZE * 2:
        raise ValueError("candidate pool does not match the frozen universe")
    rng.shuffle(chosen)
    packets, selected = [], []
    for pair, stratum in chosen:
        stable_id = _pair_id(pair, instances)
        packets.append({"packet": stable_id, "question": REVIEW_QUESTION, "verdicts": REVIEW_VERDICTS,
                        "instances": sorted((instances[v] for v in pair), key=lambda i: i["vector_id"])})
        selected.append({"pair": list(pair), "pair_id": stable_id, "stratum": stratum,
                         "selection_probability": SAMPLE_SIZE / populations[stratum],
                         "routes": sorted(routes.get(pair, []), key=_canonical)})
    if len({p["pair_id"] for p in pool}) != len(pool) or len({p["packet"] for p in packets}) != len(packets):
        raise ValueError("stable pair ID collision")
    review_set = "RN" + _sha(b"omission-pair-review-v3\0" + _canonical(packets))[:12]
    review = {"schema_version": 3, "review_set": review_set, "instructions": REVIEW_INSTRUCTIONS,
              "packets": packets, "response_contract": {"schema_version": 3, "review_set": review_set,
              "judgments": "zero or one judgment for every packet", "judgment_fields": ["packet", "verdict", "comment"],
              "allowed_verdicts": REVIEW_VERDICTS}}
    return _write_package(output, {"review.json": _canonical(review), "pool.json": _canonical(pool),
                                  "text-proposals.json": proposal_raw}, {
        "schema_version": 1, "kind": "omission-audit-sampled-pairs", "seed": SEED,
        "randomization": {"implementation": "Python random.Random MT19937; sample sorted proposed pairs, sample complement ranks, shuffle mixed sample",
                          "python_version": sys.version, "pair_order": "lexicographic short vector IDs; complement follows frozen universe order"},
        "unit": manifest["unit"], "not_a_partition": True,
        "audit_manifest": _identity(manifest_raw), "source_mask_accounting": manifest["source_mask_accounting"],
        "universe_population": manifest["universe"]["pair_count"], "pair_eligibility": PAIR_RULE,
        "strata": {s: {"population": n, "n": SAMPLE_SIZE, "selection_probability": SAMPLE_SIZE / n} for s, n in populations.items()},
        "selected": selected, "review_set": review_set,
    }, "sampling-manifest.json")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("prepare")
    p.add_argument("--root", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    s = commands.add_parser("sample")
    s.add_argument("--audit", required=True, type=Path)
    s.add_argument("--text-proposals", required=True, type=Path)
    s.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = prepare(args.root, args.output) if args.command == "prepare" else sample(args.audit, args.text_proposals, args.output)
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(1, f"omission audit: {error}\n")
    print(json.dumps({"output": str(args.output), "kind": result["kind"]}))


if __name__ == "__main__":
    main()
