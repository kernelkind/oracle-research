"""Source-bound HDBSCAN groups and numerical cuts of their saved hierarchy."""

import hashlib
import json
import math
from pathlib import Path
import struct
import subprocess

from . import canonical_trial as trial
from . import experiment as workflow


CONFIG = dict(min_samples=3, min_cluster_size=2, selection_method="excess_of_mass")
CONFIG_V42 = dict(CONFIG, min_cluster_size=4)


def section_plan(response, request, mapping, max_siblings):
    """Keep selected groups as leaves; cut only their original ancestor tree."""
    groups = members(response, request, mapping)
    if not groups:
        return dict(roots=[], sections=[], cuts=[])
    result = response["artifact"]["result"]
    algorithm = result["algorithm_result"]
    count = algorithm["vector_count"]
    aliases = result["alias_groups"]
    unique = result["canonical_unique_ids"]
    if (type(count) is not int or count < 1 or len(aliases) != count
            or len(unique) != count or len(set(unique)) != count
            or any(not a or a[0] != u for a, u in zip(aliases, unique))
            or sorted(i for a in aliases for i in a) != sorted(mapping)
            or len(algorithm["clusters"]) != len(groups)):
        raise ValueError("invalid HDBSCAN tree input identities")
    selected = {}
    for cluster, group in zip(algorithm["clusters"], groups, strict=True):
        identifier = cluster["id"]
        if (type(identifier) is not int or identifier < count or identifier in selected
                or any(type(i) is not int or not 0 <= i < count for i in cluster["members"])
                or sorted(mapping[x] for i in cluster["members"] for x in aliases[i]) != sorted(group)):
            raise ValueError("HDBSCAN selected cluster differs from saved group")
        selected[identifier] = group
    positions = {node: i for i, node in enumerate(selected)}
    parents, children = {}, {}
    for edge in algorithm["condensed_tree"]:
        parent, child, value = edge["parent"], edge["child"], edge["lambda"]
        if (type(parent) is not int or parent < count or type(child) is not int
                or child < 0 or child == parent or child in parents
                or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0):
            raise ValueError("invalid HDBSCAN condensed tree")
        parents[child] = (parent, value)
        if child >= count:
            children.setdefault(parent, []).append(child)
    needed = set()
    for leaf in selected:
        node, path = leaf, set()
        while node not in needed:
            if node in path:
                raise ValueError("cyclic HDBSCAN condensed tree")
            path.add(node)
            if node == count:
                break
            if node not in parents:
                raise ValueError("disconnected HDBSCAN selected group")
            node = parents[node][0]
        needed.update(path)
    # Postorder without Python recursion, including long chain-shaped trees.
    order, stack = [], [count]
    while stack:
        node = stack.pop()
        order.append(node)
        stack.extend(c for c in children.get(node, []) if c in needed)
    projected, representative, sizes, first = {}, {}, {}, {}
    for node in reversed(order):
        below = [representative[c] for c in children.get(node, []) if c in needed]
        if node in selected:
            if below:
                raise ValueError("HDBSCAN selected groups are not independent leaves")
            representative[node] = node
            sizes[node], first[node] = 1, positions[node]
        elif len(below) == 1:
            representative[node] = below[0]
        elif len(below) >= 2:
            values = [parents[c][1] for c in children[node] if c in needed]
            if any(not math.isclose(v, values[0], rel_tol=1e-12) for v in values):
                raise ValueError("HDBSCAN branch split distances differ")
            distance = 1 / values[0]
            if any(c in projected and projected[c]["distance"] > distance for c in below):
                raise ValueError("HDBSCAN branch distances are not ordered")
            below.sort(key=first.__getitem__)
            projected[node] = dict(children=below, distance=distance)
            representative[node] = node
            sizes[node] = sum(sizes[c] for c in below)
            first[node] = min(first[c] for c in below)
        else:
            raise ValueError("empty HDBSCAN ancestor branch")

    def cut(node):
        if sizes[node] <= max_siblings:
            leaves, pending = [], [node]
            while pending:
                current = pending.pop()
                if current in selected:
                    leaves.append(current)
                else:
                    pending.extend(projected[current]["children"])
            return sorted(leaves, key=first.__getitem__), None
        frontier, upper = [node], None
        while True:
            distance = max(projected[c]["distance"] for c in frontier if c in projected)
            expanded, pending = [], list(frontier)
            while pending:
                current = pending.pop()
                if current in projected and projected[current]["distance"] == distance:
                    pending.extend(projected[current]["children"])
                else:
                    expanded.append(current)
            if len(expanded) > max_siblings:
                if len(frontier) == 1:
                    raise ValueError("HDBSCAN tied split exceeds the section limit")
                return sorted(frontier, key=first.__getitem__), dict(
                    lower=distance, upper=upper, epsilon=(distance + upper) / 2)
            frontier, upper = expanded, distance
            if all(c in selected for c in frontier):
                return sorted(frontier, key=first.__getitem__), None

    root = representative[count]
    roots, boundary = cut(root)
    cuts = [dict(cluster_id=root, children=roots, boundary=boundary)]
    records, pending = {}, list(roots)
    while pending:
        node = pending.pop()
        if node in records:
            continue
        below, boundary = ([], None) if node in selected else cut(node)
        if below:
            cuts.append(dict(cluster_id=node, children=below, boundary=boundary))
        records[node] = dict(cluster_id=node, children=below,
                             group=selected.get(node, []))
        pending.extend(below)
    order, pending = [], list(roots)
    while pending:
        node = pending.pop()
        order.append(node)
        pending.extend(records[node]["children"])
    sections = []
    original_ids = {}
    for node in reversed(order):
        record = records[node]
        original_ids[node] = sorted(record["group"] or [
            i for child in record["children"] for i in original_ids[child]])
        sections.append(dict(record, original_ids=original_ids[node]))
    cuts.sort(key=lambda c: c["cluster_id"])
    return dict(roots=roots, sections=sections, cuts=cuts)


def plan_for(state, round_, vectors):
    request, mapping = request_for(state, round_["current"], vectors)
    return section_plan(workflow.read(round_["hdbscan"]["result"]), request,
                        mapping, state["max_siblings"])


def request_for(state, ids, vectors):
    inputs, mapping, raw = [], {}, bytearray()
    for identifier, vector in zip(ids, vectors, strict=True):
        norm = math.sqrt(sum(v * v for v in vector))
        if not math.isfinite(norm) or norm == 0:
            raise ValueError("invalid HDBSCAN input vector")
        normalized = [v / norm for v in vector]
        opaque = workflow.inputs.digest([identifier, state["items"][identifier]["vector_key"]])
        mapping[opaque] = identifier
        inputs.append(dict(opaque_id=opaque, normalized_vector=normalized))
        raw.extend(struct.pack("<" + "d" * len(normalized), *normalized))
    return dict(
        schema_version=1, candidate="hdbscan", inputs=inputs,
        source_vector_manifest_sha256=workflow.inputs.digest([
            [identifier, state["items"][identifier]["vector_key"]] for identifier in ids
        ]),
        normalized_vector_sha256=hashlib.sha256(raw).hexdigest(),
        hdbscan_configuration=(CONFIG_V42 if state.get("generation_policy") ==
                               "hierarchy-generation-v4.2" else CONFIG),
    ), mapping


def members(response, request, mapping):
    if (response.get("schema_version") != 1
            or response.get("candidate_identity") != "hdbscan-explicit-config-v1"):
        raise ValueError("unexpected HDBSCAN response identity")
    artifact = response["artifact"]
    manifest = artifact["manifest"]
    configuration = request["hdbscan_configuration"]
    if (configuration not in (CONFIG, CONFIG_V42)
            or json.loads(artifact["canonical_configuration_json"]) != configuration
            or manifest.get("parameters") != configuration
            or manifest.get("algorithm_version") != "hdbscan-star-exact-angular-v1"
            or manifest.get("fine_output_selector_version") != "hdbscan-clusters-members-v1"
            or any(manifest.get(k) != request[k] for k in (
                "source_vector_manifest_sha256", "normalized_vector_sha256"))
            or artifact.get("canonical_input_ids") != sorted(mapping)):
        raise ValueError("HDBSCAN controls or input identities changed")
    segments = artifact["result"]["fine_output"]["segments"]
    if not isinstance(segments, list):
        raise ValueError("HDBSCAN groups must be an array")
    assigned = []
    for group in segments:
        if (not isinstance(group, list) or len(group) < configuration["min_cluster_size"]
                or any(not isinstance(i, str) or i not in mapping for i in group)):
            raise ValueError("invalid HDBSCAN group membership")
        assigned.extend(group)
    if len(set(assigned)) != len(assigned):
        raise ValueError("HDBSCAN groups overlap or repeat members")
    return [[mapping[i] for i in group] for group in segments]


def round_for(directory, state, family, vectors):
    ids = list(family["current"])
    request, mapping = request_for(state, ids, vectors)
    destination = directory / f"hdbscan-{len(family['rounds']):05d}"
    destination.mkdir(exist_ok=True)
    request_path, result_path = destination / "request.json", destination / "result.json"
    trial._save_once(request_path, request)
    if not result_path.exists():
        result = subprocess.run([state["hdbscan_binary"], str(request_path)],
                                capture_output=True, check=False)
        (destination / "stderr.txt").write_bytes(result.stderr)
        if result.returncode:
            raise ValueError("HDBSCAN command failed: " + result.stderr.decode(errors="replace"))
        decoded = json.loads(result.stdout)
        members(decoded, request, mapping)
        trial._save_once(result_path, decoded)
    groups = members(workflow.read(result_path), request, mapping)
    assigned = {i for group in groups for i in group}
    return dict(
        current=ids, groups=groups,
        cases={f"{family['id']}-G{i:05d}": group for i, group in enumerate(groups)},
        unassigned=[i for i in ids if i not in assigned], unpaired=[],
        hdbscan=dict(request=str(request_path), request_sha256=trial._hash(request_path),
                     result=str(result_path), result_sha256=trial._hash(result_path)),
    )


def check_round(state, family, round_, vectors):
    request, mapping = request_for(state, round_["current"], vectors)
    evidence = round_["hdbscan"]
    if (trial._hash(evidence["request"]) != evidence["request_sha256"]
            or trial._hash(evidence["result"]) != evidence["result_sha256"]
            or workflow.read(evidence["request"]) != request):
        raise ValueError("saved HDBSCAN evidence changed")
    groups = members(workflow.read(evidence["result"]), request, mapping)
    assigned = {i for group in groups for i in group}
    if (round_["groups"] != groups
            or round_["cases"] != {
                f"{family['id']}-G{i:05d}": group for i, group in enumerate(groups)}
            or round_["unassigned"] != [i for i in round_["current"] if i not in assigned]
            or round_["unpaired"]):
        raise ValueError("saved HDBSCAN membership changed")
