"""Source-bound HDBSCAN rounds for the native root-only hierarchy experiment."""

import hashlib
import json
import math
from pathlib import Path
import struct
import subprocess

from . import canonical_trial as trial
from . import experiment as workflow


CONFIG = dict(min_samples=3, min_cluster_size=2, selection_method="excess_of_mass")


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
        hdbscan_configuration=CONFIG,
    ), mapping


def members(response, request, mapping):
    if (response.get("schema_version") != 1
            or response.get("candidate_identity") != "hdbscan-explicit-config-v1"):
        raise ValueError("unexpected HDBSCAN response identity")
    artifact = response["artifact"]
    manifest = artifact["manifest"]
    if (json.loads(artifact["canonical_configuration_json"]) != CONFIG
            or manifest.get("parameters") != CONFIG
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
        if (not isinstance(group, list) or len(group) < 2
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
