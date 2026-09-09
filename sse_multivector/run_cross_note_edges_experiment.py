#!/usr/bin/env python3
"""Replay HDBv2, change only edge eligibility, and compare the complete HDBv3 tree."""

import argparse
import hashlib
import json
import subprocess
import tempfile
from functools import cache
from pathlib import Path


def sha(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def save(path, value):
    with path.open("x", encoding="utf-8") as out:
        json.dump(value, out, ensure_ascii=False, sort_keys=True, allow_nan=False)
        out.write("\n")


def tree(result, source_notes):
    algorithm = result["algorithm_result"]
    count = algorithm["vector_count"]
    groups = {count: {"children": [], "direct_points": [], "parent": None}}
    for edge in algorithm["condensed_tree"]:
        parent, child = edge["parent"], edge["child"]
        if edge["child_size"] > 1:
            groups[parent]["children"].append(child)
            groups[child] = {"children": [], "direct_points": [], "parent": parent}
        else:
            groups[parent]["direct_points"].append(child)

    @cache
    def members(group):
        item = groups[group]
        return frozenset(item["direct_points"]).union(
            *(members(child) for child in item["children"]))

    @cache
    def depth(group):
        parent = groups[group]["parent"]
        return 0 if parent is None else depth(parent) + 1

    for group, item in groups.items():
        item["points"] = members(group)
        item["notes"] = set().union(*(source_notes[p] for p in item["points"]))
        item["depth"] = depth(group)
    return groups


def compare(before, after, request, mapping):
    sources = [set(request["source_note_ids"][v] for v in aliases)
               for aliases in before["alias_groups"]]
    evidence = {v["vector_id"]: v for v in mapping["vectors"]}

    def point_evidence(point):
        return [{"vector": evidence[v]["short_id"],
                 "note": evidence[v]["note_short_id"],
                 "fragments": evidence[v]["fragments"]}
                for v in before["alias_groups"][point]]

    def excluded(edge):
        left, right = sources[edge["left"]], sources[edge["right"]]
        return len(left) == len(right) == 1 and left == right

    def edge_record(edge):
        return {**edge, "same_note_only": excluded(edge),
                "left_masks": point_evidence(edge["left"]),
                "right_masks": point_evidence(edge["right"])}

    old_tree, new_tree = tree(before, sources), tree(after, sources)
    old_algorithm, new_algorithm = before["algorithm_result"], after["algorithm_result"]
    old_edges, new_edges = (a["minimum_spanning_tree"] for a in (old_algorithm, new_algorithm))
    if any(excluded(edge) for edge in new_edges):
        raise ValueError("HDBv3 contains an excluded same-note MST edge")

    def summary(algorithm, groups):
        edges = algorithm["minimum_spanning_tree"]
        leaves = [g for g in groups.values() if not g["children"]]
        return {
            "groups": len(groups), "leaf_groups": len(leaves),
            "maximum_depth": max(g["depth"] for g in groups.values()),
            "parent_child_equal_note_sets": sum(
                groups[c]["notes"] == g["notes"]
                for g in groups.values() for c in g["children"]),
            "selected_clusters": len(algorithm["clusters"]),
            "assigned_canonical_vectors": algorithm["vector_count"] - len(algorithm["noise"]),
            "assigned_original_vectors": sum(len(before["alias_groups"][p])
                for p, label in enumerate(algorithm["labels"]) if label is not None),
            "mst_edges": len(edges), "same_note_mst_edges": sum(map(excluded, edges)),
        }

    def record(group, item):
        return {"group": group, "parent": item["parent"], "children": item["children"],
                "depth": item["depth"], "canonical_vector_count": len(item["points"]),
                "note_count": len(item["notes"]),
                "direct_masks": [point_evidence(p) for p in item["direct_points"]],
                "vectors": sorted(evidence[v]["short_id"] for p in item["points"]
                                  for v in before["alias_groups"][p]),
                "notes": sorted({evidence[v]["note_short_id"] for p in item["points"]
                                  for v in before["alias_groups"][p]})}

    def crossing(points, edges):
        crossing_edges = [e for e in edges if (e["left"] in points) != (e["right"] in points)]
        if not crossing_edges:
            return []
        distance = min(e["mutual_reachability_distance"] for e in crossing_edges)
        return [edge_record(e) for e in crossing_edges
                if e["mutual_reachability_distance"] == distance]

    matches = []
    for old_id, old in old_tree.items():
        points = old["points"]
        containing = [(len(g["points"]), gid) for gid, g in new_tree.items()
                      if points <= g["points"]]
        best = sorted(new_tree, key=lambda gid: (
            -len(points & new_tree[gid]["points"]) / len(points | new_tree[gid]["points"]), gid))[:3]
        matches.append({
            "HDBv2_group": old_id,
            "identical_HDBv3_groups": [gid for gid, g in new_tree.items() if g["points"] == points],
            "smallest_HDBv3_group_containing_all_members": min(containing)[1],
            "closest_HDBv3_memberships": [{"group": gid,
                "shared_vectors": len(points & new_tree[gid]["points"]),
                "lost_vectors": len(points - new_tree[gid]["points"]),
                "added_vectors": len(new_tree[gid]["points"] - points)} for gid in best],
            "HDBv2_lowest_distance_crossing_edges": crossing(points, old_edges),
            "HDBv3_lowest_distance_crossing_edges": crossing(points, new_edges),
        })
    old_sets = {frozenset(c["members"]) for c in old_algorithm["clusters"]}
    new_sets = {frozenset(c["members"]) for c in new_algorithm["clusters"]}
    return {
        "schema_version": 1, "HDBv2": summary(old_algorithm, old_tree),
        "HDBv3": summary(new_algorithm, new_tree),
        "identical_selected_clusters": len(old_sets & new_sets),
        "removed_same_note_mst_edges": [edge_record(e) for e in old_edges if excluded(e)],
        "group_matches": matches,
        "HDBv2_groups": [record(gid, g) for gid, g in old_tree.items()],
        "HDBv3_groups": [record(gid, g) for gid, g in new_tree.items()],
    }


def run(baseline, mapping_path, notes_path, binary, pinned_sha, output):
    if output.exists() or output.is_symlink():
        raise ValueError(f"output already exists: {output}")
    baseline, mapping_path, notes_path, binary, output = (
        p.resolve() for p in (baseline, mapping_path, notes_path, binary, output))
    if sha(binary) != pinned_sha:
        raise ValueError("binary SHA-256 differs from pin")
    paths = [baseline / "request.json", baseline / "response.json", mapping_path, notes_path, binary]
    protected = {str(p): sha(p) for p in paths}
    request = read(paths[0])
    if request.get("candidate") != "hdbscan_cross_note":
        raise ValueError("expected frozen HDBv2 hdbscan_cross_note request")
    mapping = read(mapping_path)
    mapped_sources = {v["vector_id"]: v["note_id"] for v in mapping["vectors"]}
    if mapped_sources != request["source_note_ids"]:
        raise ValueError("vector-map note assignments differ from request")
    if not set(mapped_sources.values()) <= {n["note_id"] for n in read(notes_path)["notes"]}:
        raise ValueError("missing original notes")
    frozen = read(paths[1])
    output.mkdir(parents=True, exist_ok=False)
    invocations = []

    def unchanged():
        for path, digest in protected.items():
            if sha(Path(path)) != digest:
                raise ValueError(f"frozen file changed: {path}")

    def invoke(request_path, response_path):
        unchanged()
        stderr_path = output / f"{response_path.stem}.stderr"
        with response_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
            command = [str(binary), str(request_path)]
            process = subprocess.run(command, stdin=subprocess.DEVNULL,
                stdout=stdout, stderr=stderr, timeout=300, check=False)
        invocations.append({"argv": command, "returncode": process.returncode,
                            "request_sha256": sha(request_path),
                            "response_sha256": sha(response_path)})
        unchanged()
        if process.returncode:
            raise ValueError(f"candidate failed; see {stderr_path}")
        return read(response_path)

    try:
        # Temporary replay outputs avoid keeping three copies of the distance matrix.
        with tempfile.TemporaryDirectory(prefix="hdbv3-replay-", dir="/dev/shm") as temp:
            temp = Path(temp)
            baseline_replay = invoke(paths[0], temp / "baseline-replay.json")
            before = frozen["artifact"]["result"]
            if before != baseline_replay["artifact"]["result"]:
                raise ValueError("baseline result differs with the new binary")
            request["candidate"] = "hdbscan_cross_note_edges"
            save(output / "request.json", request)
            changed = invoke(output / "request.json", output / "response.json")
            after = changed["artifact"]["result"]
            for key in ["alias_groups", "canonical_unique_ids", "input_contract_version"]:
                if before[key] != after[key]:
                    raise ValueError(f"frozen {key} differs")
            for key in ["config", "vector_count", "core_distances", "mutual_reachability_distances"]:
                if before["algorithm_result"][key] != after["algorithm_result"][key]:
                    raise ValueError(f"frozen numeric input differs: {key}")
            manifest = changed["artifact"]["manifest"]
            if manifest["algorithm_version"] != "hdbscan-star-cross-note-edges-exact-angular-v1":
                raise ValueError("wrong candidate algorithm")
            if manifest["cross_note"].get("edge_rule_version") != "different-source-note-witness-angular-v1":
                raise ValueError("missing edge policy")
            replay = invoke(output / "request.json", temp / "variant-replay.json")
            if changed != replay:
                raise ValueError("fresh variant replay differs")
            comparison = compare(before, after, request, mapping)
            save(output / "comparison.json", comparison)
            unchanged()
            save(output / "proof.json", {
                "schema_version": 1, "run_id": "HDBv3", "baseline_run_id": "HDBv2",
                "runner_sha256": sha(Path(__file__)), "protected_files": protected,
                "candidate_binary_sha256": pinned_sha, "invocations": invocations,
                "baseline_result_identical": True, "fresh_replay_identical": True,
                "frozen_numeric_inputs_identical": True,
                "files": {p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file()},
            })
            return {"output": str(output), "HDBv2": comparison["HDBv2"], "HDBv3": comparison["HDBv3"]}
    except Exception as error:
        save(output / "failure.json", {"error": str(error), "invocations": invocations})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("vector_map", type=Path)
    parser.add_argument("notes", type=Path)
    parser.add_argument("binary", type=Path)
    parser.add_argument("binary_sha256")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        result = run(args.baseline, args.vector_map, args.notes, args.binary, args.binary_sha256, args.output)
    except Exception as error:
        parser.exit(1, f"HDBv3 experiment failed: {error}\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
