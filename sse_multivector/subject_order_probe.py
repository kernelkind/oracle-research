"""Isolated subject-SSE/OPHAC diagnostic; never edits source hierarchies.

Prepare a source-bound worker request, run the existing SSE worker separately,
then compare complete-linkage merge sequences with and without SP constraints.
No semantic merges, final cut, titles, or browsing hierarchy are approved here.
"""

import argparse
import hashlib
import inspect
import json
import platform
from pathlib import Path

from sse_multivector.worker import _load_request, _sha256_file
from sse_multivector.subject_hierarchy import reachable


def read(path):
    return json.loads(Path(path).read_bytes())


def save(path, value):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")


def post_ids(vector_map):
    """Identify posts independently of whether any MP mask has a vector."""
    result = {v["note_short_id"]: v["note_id"] for v in vector_map["vectors"]}
    for note in vector_map.get("notes", []):
        label = note.get("note_short_id", note.get("short_id"))
        if not isinstance(label, str) or not label:
            raise ValueError("saved post mapping requires a short ID")
        if label in result and result[label] != note["note_id"]:
            raise ValueError("saved post mapping conflicts with mask vectors")
        result[label] = note["note_id"]
    if len(set(result.values())) != len(result):
        raise ValueError("saved post mapping repeats a post under different short IDs")
    return result


def build_inputs(posts, vector_map, labels):
    if len(set(labels)) != len(labels):
        raise ValueError("duplicate post selection")
    note_ids = post_ids(vector_map)
    by_id = {p["note_id"]: p for p in posts["notes"]}
    mask_ids = {}
    for v in vector_map["vectors"]:
        key = (v["note_id"], tuple(map(tuple, v["byte_spans"])))
        mask_ids.setdefault(key, []).append(v["vector_id"])
    entries, edges, selected_posts, encodings = [], [], [], {}
    for label in labels:
        if label not in note_ids or note_ids[label] not in by_id:
            raise ValueError(f"missing post {label}")
        post = by_id[note_ids[label]]
        selected_posts.append(dict(note_short_id=label, note_id=post["note_id"], text=post["text"]))
        numbers = {}
        for subject in sorted(post["subjects"], key=lambda s: tuple(map(int, s["number"].split(".")))):
            number, text = subject["number"], subject["subject"]
            if number in numbers or not text.strip():
                raise ValueError("duplicate subject number or empty subject")
            numbers[number] = len(entries)
            encoding = hashlib.sha256(text.encode()).hexdigest()
            encodings.setdefault(text, dict(note_id=encoding, text=text, subjects=[
                dict(subject_id=encoding[:16], byte_spans=[[0, len(text.encode())]])]))
            key = (post["note_id"], tuple(map(tuple, subject["byte_spans"])))
            vector_ids = mask_ids.get(key, []) if subject["byte_spans"] else []
            if subject["byte_spans"] and not vector_ids:
                raise ValueError(f"nonempty mask lacks saved vector: {label}/{number}")
            raw = post["text"].encode()
            if [raw[a:b].decode() for a, b in subject["byte_spans"]] != subject["fragments"]:
                raise ValueError(f"mask/source mismatch: {label}/{number}")
            entries.append(dict(subject, index=len(entries), note_id=post["note_id"],
                                note_short_id=label, encoding_id=encoding[:16], mask_vector_ids=vector_ids))
        for number, index in numbers.items():
            if "." in number:
                parent = number.rsplit(".", 1)[0]
                if parent not in numbers:
                    raise ValueError(f"missing SP parent {label}/{parent}")
                edges.append([numbers[parent], index])
    if len(entries) < 2:
        raise ValueError("at least two subject entries required")
    return dict(posts=selected_posts, subjects=entries, edges=edges), dict(notes=list(encodings.values()))


def cosine_distances(vectors):
    import numpy as np
    vectors = np.asarray(vectors, dtype=np.float64)
    if vectors.ndim != 2 or not np.isfinite(vectors).all():
        raise ValueError("invalid vectors")
    norms = np.linalg.norm(vectors, axis=1)
    if np.any(norms == 0):
        raise ValueError("zero vector")
    unit = vectors / norms[:, None]
    distances = np.clip(1 - unit @ unit.T, 0, 2)
    distances[distances < 1e-12] = 0  # Floating-point roundoff, not a semantic threshold.
    np.fill_diagonal(distances, 0)
    return distances


def merge_sequence(distances, edges, *, constrained):
    import numpy as np
    from ophac.dtypes import DistMatrix, Quivers
    from ophac.hac_approx import HACUntied_python
    d = np.asarray(distances, dtype=np.float64)
    n = len(d)
    if (d.shape != (n, n) or not np.isfinite(d).all() or np.any(d < 0)
            or not np.allclose(d, d.T, atol=1e-12, rtol=0) or np.any(np.diag(d) != 0)):
        raise ValueError("invalid distance matrix")
    original = reachable(n, edges)
    if any(a == b for a, b in original):
        raise ValueError("SP graph contains a cycle")
    order = Quivers(n=n, relation=edges if constrained else [])
    condensed = d[np.triu_indices(n, 1)].tolist()
    # Explicit Python backend: first minimum in stable index order resolves ties.
    # This does not explore all tied histories or optimize the paper's global loss.
    ac = HACUntied_python("complete").generate(DistMatrix(condensed), order)
    groups, steps = [[i] for i in range(n)], []
    for step, ((a, b), distance) in enumerate(zip(ac.joins, ac.dists, strict=True), 1):
        left, right = groups[a], groups[b]
        groups[a] = sorted(left + right)
        del groups[b]
        owner = {entry: i for i, group in enumerate(groups) for entry in group}
        mapped = sorted({(owner[a], owner[b]) for a, b in edges if owner[a] != owner[b]})
        paths = reachable(len(groups), mapped)
        acyclic = all(a != b for a, b in paths)
        collapsed = sum(owner[a] == owner[b] for a, b in original)
        preserved = sum(owner[a] != owner[b] and (owner[a], owner[b]) in paths for a, b in original)
        if constrained and (not acyclic or collapsed or preserved != len(original)):
            raise ValueError("OPHAC violated a supplied ancestor relationship")
        implied = {(a, b) for i, j in paths for a in groups[i] for b in groups[j] if a != b}
        steps.append(dict(step=step, distance=float(distance), left=left, right=right,
                          merged=groups[a], groups=[list(g) for g in groups],
                          edges=[[groups[i][0], groups[j][0]] for i, j in mapped],
                          acyclic=acyclic, parent_collapses=collapsed,
                          preserved_ancestor_pairs=preserved,
                          new_reachable_pairs=[list(p) for p in sorted(implied - original)]))
    return dict(constrained=constrained, initial_groups=n, original_ancestor_pairs=len(original), steps=steps)


def prepare(source, labels, output, protected):
    source, output = source.resolve(), output.resolve()
    paths = [source / name for name in ("masked-posts.json", "vector-map.json", "worker-config.json",
                                       "worker-result/worker-receipt.json", "subjects.json")]
    paths += [Path(__file__).resolve(), Path(inspect.getfile(_load_request)).resolve(),
              Path(inspect.getfile(reachable)).resolve()]
    paths += [path.resolve() for path in protected]
    hashes = {str(path): _sha256_file(path) for path in paths}
    inputs, request = build_inputs(read(paths[0]), read(paths[1]), labels)
    inputs.update(experiment_id="SOv1", protected_sha256=hashes, settings=dict(
        linkage="complete", distance="1-cosine", backend="HACUntied_python",
        tie_break="first-minimum-in-stable-input-index-order", constraints="strict-SP-ancestry",
        final_cut=None, encoding="standalone-subject-full-text", semantic_deduplication=False))
    output.mkdir(parents=True, exist_ok=False)
    save(output / "inputs.json", inputs)
    request.update(schema_version=1, proposal_sha256=_sha256_file(output / "inputs.json"))
    save(output / "worker-request.json", request)
    _load_request(output / "worker-request.json")
    config = read(source / "worker-config.json")
    config.update(request_path=str(output / "worker-request.json"),
                  request_sha256=_sha256_file(output / "worker-request.json"), output_path=str(output / "worker-result"))
    save(output / "worker-config.json", config)
    return dict(subjects=len(inputs["subjects"]), unique_encodings=len(request["notes"]),
                empty_masks=sum(not s["byte_spans"] for s in inputs["subjects"]), edges=len(inputs["edges"]))


def collect(output):
    import numpy as np
    import ophac.hac_approx
    from ophac import dtypes
    output = output.resolve()
    inputs, config = read(output / "inputs.json"), read(output / "worker-config.json")
    for path, expected in inputs["protected_sha256"].items():
        if _sha256_file(Path(path)) != expected:
            raise ValueError(f"protected input changed: {path}")
    receipt = read(output / "worker-result/worker-receipt.json")
    _, notes = _load_request(output / "worker-request.json")
    expected_rows = [(n.note_id, s.subject_id) for n in notes for s in n.subjects]
    if expected_rows != [(r["note_id"], r["subject_id"]) for r in receipt["rows"]]:
        raise ValueError("worker row identities differ")
    if receipt["request_sha256"] != _sha256_file(output / "worker-request.json"):
        raise ValueError("worker request hash differs")
    if receipt["proposal_sha256"] != _sha256_file(output / "inputs.json"):
        raise ValueError("worker proposal hash differs")
    prior_path = next(p for p in inputs["protected_sha256"] if p.endswith("worker-result/worker-receipt.json"))
    prior = read(prior_path)
    for key in ("checkpoint_sha256", "base_model_artifact_tree_sha256", "model", "device", "note_batch_size"):
        if receipt[key] != config[key] or receipt[key] != prior[key]:
            raise ValueError(f"SSE identity mismatch: {key}")
    if receipt["runtime"] != prior["runtime"]:
        raise ValueError("SSE runtime differs from saved HR02 worker")
    path = output / "worker-result/raw-vectors.f32le"
    if _sha256_file(path) != receipt["files"][path.name]["sha256"]:
        raise ValueError("vector file hash differs")
    matrix = np.fromfile(path, dtype="<f4").reshape(receipt["row_count"], receipt["dimensions"])
    rows = {r["subject_id"]: matrix[i] for i, r in enumerate(receipt["rows"])}
    vectors = np.array([rows[s["encoding_id"]] for s in inputs["subjects"]])
    distances = cosine_distances(vectors)
    outputs = {name: merge_sequence(distances, inputs["edges"], constrained=flag)
               for name, flag in (("constrained", True), ("unconstrained", False))}
    for name, flag in (("constrained", True), ("unconstrained", False)):
        if outputs[name] != merge_sequence(distances, inputs["edges"], constrained=flag):
            raise ValueError(f"non-reproducible sequence: {name}")
    result = dict(experiment_id=inputs["experiment_id"], settings=inputs["settings"],
                  inputs_sha256=_sha256_file(output / "inputs.json"),
                  receipt_sha256=_sha256_file(output / "worker-result/worker-receipt.json"),
                  runtime=dict(python=platform.python_version(), numpy=np.__version__,
                               ophac_source_sha256={m.__name__: _sha256_file(Path(inspect.getfile(m)))
                                                   for m in (ophac.hac_approx, dtypes)}),
                  deterministic_rerun_matches=True, distances=distances.tolist(), **outputs)
    save(output / "results.json", result)
    summary = dict(experiment_id=inputs["experiment_id"], subjects=len(vectors),
                   unique_encodings=len(rows), empty_masks=sum(not s["byte_spans"] for s in inputs["subjects"]),
                   direct_SP_edges=len(inputs["edges"]), ancestor_pairs=outputs["constrained"]["original_ancestor_pairs"],
                   protected_inputs_unchanged=True, deterministic_rerun_matches=True, cuts=[])
    # These are observations at fixed distances, not accepted thresholds.
    for threshold in (0, .05, .10, .15, .20, .25, .30, .40, .50, 1, 2):
        cut = dict(maximum_distance=threshold)
        for name, sequence in outputs.items():
            selected = [s for s in sequence["steps"] if s["distance"] <= threshold]
            last = selected[-1] if selected else None
            cut[name] = dict(step=last["step"] if last else 0,
                             groups=len(last["groups"]) if last else len(vectors),
                             parent_collapses=last["parent_collapses"] if last else 0,
                             acyclic=last["acyclic"] if last else True,
                             new_reachable_pairs=len(last["new_reachable_pairs"]) if last else 0)
        summary["cuts"].append(cut)
    save(output / "summary.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prep = commands.add_parser("prepare")
    prep.add_argument("--source", type=Path, required=True)
    prep.add_argument("--posts", nargs="+", required=True)
    prep.add_argument("--output", type=Path, required=True)
    prep.add_argument("--protect", type=Path, nargs="*", default=[])
    analysis = commands.add_parser("collect")
    analysis.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    value = prepare(args.source, args.posts, args.output, args.protect) if args.command == "prepare" else collect(args.output)
    print(json.dumps(value, indent=2))


if __name__ == "__main__":
    main()
