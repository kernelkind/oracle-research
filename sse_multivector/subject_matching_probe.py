"""SMv1: offline, reversible cross-post subject matching on saved SSE vectors.

Mask nearest neighbors select post pairs. Within each pair, mutual subject-text
best matches must pass independent subject/mask cutoffs. Passing chains merge;
all merged groups participating in a directed cycle are split back to subjects.
No inference, new placement, title generation, or baseline edits.
"""
import argparse
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import platform

from sse_multivector.ancestor_cosine_probe import cosine, load_vectors
from sse_multivector.subject_order_probe import read, reachable, save
from sse_multivector.worker import _sha256_file

TIE_TOLERANCE = 1e-12  # Numerical ties only; not a semantic acceptance margin.


def match_subjects(inputs, subject_vectors, mask_vectors, *, subject_cutoff=.90, mask_cutoff=.80):
    subjects, edges = inputs["subjects"], inputs["edges"]
    n = len(subjects)
    if not n or [s["index"] for s in subjects] != list(range(n)):
        raise ValueError("contiguous original subject indices required")
    if len(subject_vectors) != n or len(mask_vectors) != n:
        raise ValueError("one subject vector and optional mask vector per SP entry required")
    if any(not math.isfinite(v) or not -1 <= v <= 1 for v in (subject_cutoff, mask_cutoff)):
        raise ValueError("finite cosine cutoffs in [-1, 1] required")
    sv = [tuple(v) for v in subject_vectors]
    mv = [tuple(v) if v is not None else None for v in mask_vectors]
    for v in sv + [v for v in mv if v is not None]:
        cosine(sv[0], v)  # Validate dimensions, finiteness, and nonzero norms.
    original_paths = reachable(n, edges)
    if any(a == b for a, b in original_paths):
        raise ValueError("original SP graph contains a cycle")
    if any(subjects[a]["note_id"] != subjects[b]["note_id"] for a, b in edges):
        raise ValueError("original SP edges must stay within a post")

    @lru_cache(None)
    def similarity(a, b):
        return cosine(a, b)

    by_post = {}
    representatives, seen_masks = [], set()
    for i, s in enumerate(subjects):
        by_post.setdefault(s["note_id"], []).append(i)
        identity = s["note_id"], tuple(s["mask_vector_ids"])
        if mv[i] is not None and identity not in seen_masks:
            seen_masks.add(identity)
            representatives.append(i)
    nearest_masks, post_pairs = [], set()
    for i in representatives:
        others = [j for j in representatives if subjects[i]["note_id"] != subjects[j]["note_id"]]
        if not others:
            continue
        scores = {j: similarity(mv[i], mv[j]) for j in others}
        best = max(scores.values())
        winners = [j for j in others if abs(scores[j] - best) <= TIE_TOLERANCE]
        nearest_masks.append(dict(subject_index=i, matches=winners, mask_cosine=best))
        post_pairs.update(tuple(sorted((subjects[i]["note_id"], subjects[j]["note_id"]))) for j in winners)

    comparisons, accepted = [], []
    for post_a, post_b in sorted(post_pairs):
        left, right = by_post[post_a], by_post[post_b]
        scores = {(i, j): similarity(sv[i], sv[j]) for i in left for j in right}
        best_left = {i: max(scores[i, j] for j in right) for i in left}
        best_right = {j: max(scores[i, j] for i in left) for j in right}
        for i in left:
            for j in right:
                subject_score = scores[i, j]
                mask_score = similarity(mv[i], mv[j]) if mv[i] is not None and mv[j] is not None else None
                mutual = (abs(subject_score - best_left[i]) <= TIE_TOLERANCE
                          and abs(subject_score - best_right[j]) <= TIE_TOLERANCE)
                reason = ("not-mutual" if not mutual else
                          "subject-cutoff" if subject_score < subject_cutoff else
                          "empty-mask" if mask_score is None else
                          "mask-cutoff" if mask_score < mask_cutoff else "accepted")
                pair = sorted((i, j))
                best = {i: best_left[i], j: best_right[j]}
                comparisons.append(dict(pair=pair, subject_cosine=subject_score, mask_cosine=mask_score,
                                        best_subject_cosines=[best[k] for k in pair],
                                        mutual=mutual, reason=reason))
                if reason == "accepted":
                    accepted.append(pair)

    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for a, b in sorted(accepted):
        a, b = find(a), find(b)
        parent[max(a, b)] = min(a, b)
    components = {}
    for i in range(n):
        components.setdefault(find(i), []).append(i)
    groups = sorted(components.values())
    rollbacks = []
    while True:
        owner = {member: i for i, group in enumerate(groups) for member in group}
        mapped = sorted({(owner[a], owner[b]) for a, b in edges if owner[a] != owner[b]})
        paths = reachable(len(groups), mapped)
        cyclic = {a for a, b in paths if a == b}
        if not cyclic:
            break
        undo = {i for i in cyclic if len(groups[i]) > 1}
        if not undo:
            raise ValueError("cycle without any proposed merge to undo")
        rollbacks.append(dict(groups=[groups[i] for i in sorted(undo)],
                              cyclic_groups=[groups[i] for i in sorted(cyclic)],
                              edges=[list(e) for e in mapped]))
        groups = sorted([part for i, group in enumerate(groups)
                         for part in ([[m] for m in group] if i in undo else [group])])
    if any(owner[a] != owner[b] and (owner[a], owner[b]) not in paths for a, b in original_paths):
        raise ValueError("an original SP relationship was lost")
    return dict(experiment_id="SMv1", settings=dict(
        subject_cutoff=subject_cutoff, mask_cutoff=mask_cutoff, tie_tolerance=TIE_TOLERANCE,
        post_selection="cross-post nearest mask; all numerical ties",
        matching="mutual subject best within each post pair, before cutoff/mask checks",
        merging="connected passing pairs; no all-pairs requirement or iterative rematching",
        cycles="split every merged group in any cycle; repeat; retain original SP links"),
        nearest_masks=nearest_masks, candidate_post_pairs=[list(p) for p in sorted(post_pairs)],
        comparisons=sorted(comparisons, key=lambda r: r["pair"]), accepted_pairs=sorted(accepted),
        cycle_rollbacks=rollbacks, groups=groups, edges=[list(e) for e in mapped],
        member_to_group=[owner[i] for i in range(n)],
        rolled_back_pairs=[p for p in sorted(accepted) if owner[p[0]] != owner[p[1]]],
        collapsed_sp_edges=[list(e) for e in edges if owner[e[0]] == owner[e[1]]],
        original_ancestor_pairs=len(original_paths), sp_order_preserved=True)


def browser_spec(inputs, result, masks, source_hash):
    """Use the existing DAG browser, preserving SP sources even for empty masks."""
    subjects, groups = inputs["subjects"], result["groups"]
    ids = [f"S{g[0]:04d}" for g in groups]
    children = {i: [] for i in range(len(groups))}
    nonroots = set()
    for a, b in result["edges"]:
        children[a].append(b)
        nonroots.add(b)
    names = [" / ".join(dict.fromkeys(subjects[m]["subject"] for m in g)) for g in groups]
    nodes, own_notes, own_masks = [], {}, {}
    for i, group in enumerate(groups):
        own_notes[i], own_masks[i], origins = set(), {}, []
        for m in group:
            s = subjects[m]
            own_notes[i].add(s["note_short_id"])
            mask_ids = []
            for v in s["mask_vector_ids"]:
                mask = masks[v]
                identity = mask["note_short_id"], tuple(map(tuple, mask["byte_spans"]))
                own_masks[i].setdefault(identity, set()).add(mask["short_id"])
                mask_ids.append(mask["short_id"])
            origins.append(f'{s["note_short_id"]} SP {s["number"]}: {s["subject"]} '
                           f'({", ".join(mask_ids) or "empty mask"})')
        nodes.append(dict(node_id=ids[i], label=names[i],
                          children=[ids[j] for j in sorted(children[i], key=lambda j: (names[j], ids[j]))],
                          note_ids=sorted(own_notes[i]),
                          analysis="SMv1 experimental subject matching; original SP links only. "
                          "No title generation or new placements.\nOriginal subjects:\n" + "\n".join(origins)))
    paths = reachable(len(groups), result["edges"])
    nodes.insert(0, dict(node_id="root", label="All subjects", note_ids=[],
                         children=[ids[i] for i in sorted(set(children) - nonroots,
                                                         key=lambda j: (names[j], ids[j]))],
                         analysis="SMv1 navigation root, not an inferred subject. All SP subjects retained; "
                         "no display collapsing. Empty masks show original posts without highlights."))
    note_masks, instances = {}, {}
    for node in nodes:
        key = node["node_id"]
        if key == "root":
            included = range(len(groups))
        else:
            i = ids.index(key)
            included = [i] + [b for a, b in sorted(paths) if a == i]
        notes, combined = set(), {}
        for i in included:
            notes.update(own_notes[i])
            for identity, aliases in own_masks[i].items():
                combined.setdefault(identity, set()).update(aliases)
        individual = {p: [] for p in sorted(notes)}
        for (p, spans), aliases in sorted(combined.items()):
            individual[p].append(dict(ids=sorted(aliases), byte_spans=[list(s) for s in spans]))
        instances[key] = individual
        note_masks[key] = {p: [list(s) for s in sorted({tuple(s) for m in items for s in m["byte_spans"]})]
                           for p, items in individual.items()}
    return dict(schema_version=2, hierarchy_id="SMv1 · saved SP hierarchies · experimental matching",
                source_sha256=source_hash, root_node_id="root", nodes=nodes,
                notes=[dict(note_id=p["note_id"], note_short_id=p["note_short_id"])
                       for p in inputs["posts"]], note_masks=note_masks, mask_instances=instances)


def run(source, probe, output, *, subject_cutoff=.90, mask_cutoff=.80):
    source, probe, output = map(lambda p: Path(p).resolve(), (source, probe, output))
    if output.exists():
        raise FileExistsError(output)
    inputs = read(probe / "inputs.json")
    mask_vectors, mask_receipt = load_vectors(source / "worker-result")
    subject_vectors, subject_receipt = load_vectors(probe / "worker-result")
    for key in ("checkpoint_sha256", "base_model_artifact_tree_sha256", "model", "runtime"):
        if mask_receipt[key] != subject_receipt[key]:
            raise ValueError(f"SSE identity mismatch: {key}")
    if subject_receipt["proposal_sha256"] != _sha256_file(probe / "inputs.json"):
        raise ValueError("subject vectors do not match the saved SP inputs")
    protected = dict(inputs["protected_sha256"])
    for folder in (source, probe):
        for name in ("worker-receipt.json", "raw-vectors.f32le"):
            path = folder / "worker-result" / name
            expected = _sha256_file(path)
            if str(path) in protected and protected[str(path)] != expected:
                raise ValueError(f"protected input changed: {path}")
            protected[str(path)] = expected
    for path in (probe / "inputs.json", source / "vector-map.json", source / "masked-posts.json"):
        expected = _sha256_file(path)
        if str(path) in protected and protected[str(path)] != expected:
            raise ValueError(f"protected input changed: {path}")
        protected[str(path)] = expected
    for path, expected in protected.items():
        if _sha256_file(Path(path)) != expected:
            raise ValueError(f"protected input changed: {path}")
    mappings = read(source / "vector-map.json")["vectors"]
    masks = {v["vector_id"]: v for v in mappings}
    originals = {p["note_id"]: p["text"] for p in read(source / "masked-posts.json")["notes"]}
    for p in inputs["posts"]:
        if originals[p["note_id"]] != p["text"]:
            raise ValueError("saved SP post differs from original source")
    sv, mv = [], []
    selected_masks = {}
    for s in inputs["subjects"]:
        key = hashlib.sha256(s["subject"].encode()).hexdigest(), s["encoding_id"]
        sv.append(subject_vectors[key])
        vectors = s["mask_vector_ids"]
        if not vectors:
            if s["byte_spans"] or s["fragments"]:
                raise ValueError("nonempty subject mask has no vector")
            mv.append(None)
            continue
        if len(vectors) != 1:
            raise ValueError("one canonical mask vector per subject required")
        m = masks[vectors[0]]
        if any(s[k] != m[k] for k in ("note_id", "note_short_id", "byte_spans", "fragments")):
            raise ValueError("mask provenance mismatch")
        raw = originals[s["note_id"]].encode()
        if [raw[a:b].decode() for a, b in m["byte_spans"]] != m["fragments"]:
            raise ValueError("mask differs from original post")
        mv.append(mask_vectors[m["note_id"], m["worker_subject_id"]])
        selected_masks[vectors[0]] = m
    result = match_subjects(inputs, sv, mv, subject_cutoff=subject_cutoff, mask_cutoff=mask_cutoff)
    if result != match_subjects(inputs, sv, mv, subject_cutoff=subject_cutoff, mask_cutoff=mask_cutoff):
        raise ValueError("matching did not reproduce deterministically")
    view = browser_spec(inputs, result, selected_masks, protected[str(source / "masked-posts.json")])
    summary = dict(experiment_id="SMv1", posts=len(inputs["posts"]), subjects=len(sv),
                   empty_masks=sum(v is None for v in mv), mask_vectors=len(selected_masks),
                   candidate_post_pairs=len(result["candidate_post_pairs"]),
                   subject_pairs_compared=len(result["comparisons"]), accepted_pairs=len(result["accepted_pairs"]),
                   merged_groups=sum(len(g) > 1 for g in result["groups"]), nodes=len(result["groups"]),
                   roots=len(view["nodes"][0]["children"]), edges=len(result["edges"]),
                   rolled_back_pairs=len(result["rolled_back_pairs"]), cycle_rollback_rounds=len(result["cycle_rollbacks"]),
                   sp_order_preserved=True, protected_inputs_unchanged=True, deterministic_rerun_matches=True,
                   inference_calls=0)
    for path, expected in protected.items():
        if _sha256_file(Path(path)) != expected:
            raise ValueError(f"protected input changed during run: {path}")
    provenance = dict(protected_sha256=protected, python=platform.python_version(),
                      implementation_sha256={str(Path(__file__).resolve()): _sha256_file(Path(__file__))},
                      source_path=str(source), probe_path=str(probe), subjects=inputs["subjects"],
                      original_edges=inputs["edges"], masks=list(selected_masks.values()))
    output.mkdir(parents=True, exist_ok=False)
    for name, value in (("results", result), ("categories", view), ("provenance", provenance), ("summary", summary)):
        save(output / f"{name}.json", value)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "probe", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--subject-cutoff", type=float, default=.90)
    parser.add_argument("--mask-cutoff", type=float, default=.80)
    args = parser.parse_args()
    print(json.dumps(run(args.source, args.probe, args.output,
                         subject_cutoff=args.subject_cutoff, mask_cutoff=args.mask_cutoff), indent=2))


if __name__ == "__main__":
    main()
