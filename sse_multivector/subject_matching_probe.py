"""SMv2: exact same-post combination and reversible cross-post subject matching.

Mask nearest neighbors select post pairs. Within each pair, mutual subject-text
best matches must pass independent subject/mask cutoffs. Passing chains merge;
cross-post merges in cycles are undone without splitting exact same-post groups.
If exact same-post combination alone creates a cycle, stop before any export.
No inference, new placement, title generation, or baseline edits.
"""
import argparse
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import platform
import sys

from sse_multivector.ancestor_cosine_probe import cosine, load_vectors
from sse_multivector.subject_order_probe import build_inputs, read, reachable, save
from sse_multivector.worker import _load_request, _sha256_file
from sse_multivector.subject_hierarchy import browser_spec

TIE_TOLERANCE = 1e-12  # Numerical ties only; not a semantic acceptance margin.


def load_subject_vectors(probe):
    """Read original worker batches, retaining their receipts instead of synthesizing one."""
    vectors, receipts, protected, visited, active = {}, [], {}, set(), set()

    def visit(folder):
        folder = Path(folder).resolve()
        if folder in active:
            raise ValueError('cyclic subject-vector reuse')
        if folder in visited:
            return
        active.add(folder)
        path = folder / 'inputs.json'
        data = read(path)
        protected[str(path)] = _sha256_file(path)
        for prior in data.get('reused_probes', []):
            visit(prior)
        if data.get('new_encodings', 1):
            batch, receipt = load_vectors(folder / 'worker-result')
            if receipt['proposal_sha256'] != protected[str(path)]:
                raise ValueError('subject vectors do not match the saved SP inputs')
            request = folder / 'worker-request.json'
            if request.exists() or 'new_encodings' in data:
                if receipt['request_sha256'] != _sha256_file(request):
                    raise ValueError('subject-vector request hash differs')
                proposal, notes = _load_request(request)
                if proposal != receipt['proposal_sha256']:
                    raise ValueError('subject-vector request proposal differs')
                expected = []
                for note in notes:
                    encoding = hashlib.sha256(note.text.encode()).hexdigest()
                    if (note.note_id != encoding or len(note.subjects) != 1
                            or note.subjects[0].subject_id != encoding[:16]
                            or tuple(note.subjects[0].byte_spans) != ((0, len(note.text.encode())),)):
                        raise ValueError('subject-vector request is not standalone full subject text')
                    expected.append((note.note_id, note.subjects[0].subject_id))
                if list(batch) != expected:
                    raise ValueError('subject-vector worker rows differ from request')
                protected[str(request)] = _sha256_file(request)
            for name in ('worker-receipt.json', 'raw-vectors.f32le'):
                path = folder / 'worker-result' / name
                protected[str(path)] = _sha256_file(path)
            if receipts:
                for key in ('checkpoint_sha256', 'base_model_artifact_tree_sha256', 'model',
                            'runtime', 'dimensions', 'device', 'note_batch_size'):
                    if receipt.get(key) != receipts[0].get(key):
                        raise ValueError(f'SSE identity mismatch between subject batches: {key}')
            receipts.append(receipt)
            for key, vector in batch.items():
                if key in vectors and vectors[key] != vector:
                    raise ValueError('conflicting saved vectors for the same subject')
                vectors[key] = vector
        active.remove(folder)
        visited.add(folder)

    visit(probe)
    if not receipts:
        raise ValueError('no saved subject-vector batches')
    return vectors, receipts[0], protected


def prepare(source, output, *, posts=None, reuse_probe=None, protected=()):
    """Prepare all SP entries, requesting only standalone subject vectors not already saved."""
    source, output = Path(source).resolve(), Path(output).resolve()
    if output.exists():
        raise FileExistsError(output)
    mappings = read(source / 'vector-map.json')
    corpus = read(source / 'masked-posts.json')
    if posts is None:
        if {p['note_id'] for p in corpus['notes']} != {v['note_id'] for v in mappings['vectors']}:
            raise ValueError('cannot identify every corpus post from the saved vector map')
        posts = sorted({v['note_short_id'] for v in mappings['vectors']})
    inputs, request = build_inputs(corpus, mappings, posts)
    hashes = {str(path.resolve()): _sha256_file(path) for path in [
        source / 'masked-posts.json', source / 'vector-map.json', source / 'worker-config.json',
        source / 'worker-result/worker-receipt.json', source / 'worker-result/raw-vectors.f32le',
        *map(Path, protected)]}
    reused, reusable = [], {}
    if reuse_probe is not None:
        reusable, receipt, prior_hashes = load_subject_vectors(reuse_probe)
        original = read(source / 'worker-result/worker-receipt.json')
        for key in ('checkpoint_sha256', 'base_model_artifact_tree_sha256', 'model', 'runtime'):
            if receipt[key] != original[key]:
                raise ValueError(f'SSE identity mismatch: {key}')
        hashes.update(prior_hashes)
        reused.append(str(Path(reuse_probe).resolve()))
    total = len(request['notes'])
    request['notes'] = [p for p in request['notes']
                        if (p['note_id'], p['subjects'][0]['subject_id']) not in reusable]
    new_count = len(request['notes'])
    inputs.update(experiment_id='SMv2', protected_sha256=hashes, reused_probes=reused,
                  new_encodings=new_count, encoding='standalone-subject-full-text')
    output.mkdir(parents=True, exist_ok=False)
    save(output / 'inputs.json', inputs)
    if new_count:
        request.update(schema_version=1, proposal_sha256=_sha256_file(output / 'inputs.json'))
        save(output / 'worker-request.json', request)
        _load_request(output / 'worker-request.json')
        config = read(source / 'worker-config.json')
        config.update(request_path=str(output / 'worker-request.json'),
                      request_sha256=_sha256_file(output / 'worker-request.json'),
                      output_path=str(output / 'worker-result'))
        save(output / 'worker-config.json', config)
    return dict(posts=len(inputs['posts']), subjects=len(inputs['subjects']), unique_encodings=total,
                reused_encodings=total - new_count, new_encodings=new_count,
                empty_masks=sum(not s['byte_spans'] for s in inputs['subjects']))


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

    def mapped_graph(groups):
        owner = {member: i for i, group in enumerate(groups) for member in group}
        mapped = sorted({(owner[a], owner[b]) for a, b in edges if owner[a] != owner[b]})
        return owner, mapped, reachable(len(groups), mapped)

    # HD11: identity comes from exact source positions, not vector IDs or cosine.
    same_post = {}
    for i, s in enumerate(subjects):
        spans = tuple(map(tuple, s["byte_spans"]))
        identity = (s["note_id"], s["subject"], spans) if spans else (i,)
        same_post.setdefault(identity, []).append(i)
    base_groups = sorted(same_post.values())
    base_owner, _, base_paths = mapped_graph(base_groups)
    base_cyclic = {a for a, b in base_paths if a == b}
    if base_cyclic:
        members = sorted(m for i in base_cyclic for m in base_groups[i])
        refs = "; ".join(f'{subjects[m]["note_short_id"]} SP {subjects[m]["number"]}: '
                         f'{subjects[m]["subject"]}' for m in members)
        raise ValueError(f"exact same-post combination creates a cycle: {refs}")

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
    for group in base_groups:
        for m in group:
            parent[m] = group[0]

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
        owner, mapped, paths = mapped_graph(groups)
        cyclic = {a for a, b in paths if a == b}
        if not cyclic:
            break
        undo = {i for i in cyclic if len({base_owner[m] for m in groups[i]}) > 1}
        if not undo:
            raise ValueError("cycle without any cross-post merge to undo")
        rollbacks.append(dict(groups=[groups[i] for i in sorted(undo)],
                              cyclic_groups=[groups[i] for i in sorted(cyclic)],
                              edges=[list(e) for e in mapped]))
        groups = sorted(part for i, group in enumerate(groups)
                        for part in ([base_groups[j] for j in sorted({base_owner[m] for m in group})]
                                     if i in undo else [group]))
    if any(owner[a] != owner[b] and (owner[a], owner[b]) not in paths for a, b in original_paths):
        raise ValueError("an original SP relationship was lost")
    return dict(experiment_id="SMv2", settings=dict(
        subject_cutoff=subject_cutoff, mask_cutoff=mask_cutoff, tie_tolerance=TIE_TOLERANCE,
        same_post_combination="HD11: exact post, subject wording and nonempty source positions",
        post_selection="cross-post nearest mask; all numerical ties",
        matching="mutual subject best within each post pair, before cutoff/mask checks",
        merging="connected passing pairs; no all-pairs requirement or iterative rematching",
        cycles="HD15: stop on exact-combination cycle; undo every cross-post merge in any cycle; "
        "repeat; retain exact same-post groups and original SP links"),
        same_post_groups=[g for g in base_groups if len(g) > 1],
        nearest_masks=nearest_masks, candidate_post_pairs=[list(p) for p in sorted(post_pairs)],
        comparisons=sorted(comparisons, key=lambda r: r["pair"]), accepted_pairs=sorted(accepted),
        cycle_rollbacks=rollbacks, groups=groups, edges=[list(e) for e in mapped],
        member_to_group=[owner[i] for i in range(n)],
        rolled_back_pairs=[p for p in sorted(accepted) if owner[p[0]] != owner[p[1]]],
        collapsed_sp_edges=[list(e) for e in edges if owner[e[0]] == owner[e[1]]],
        original_ancestor_pairs=len(original_paths), sp_order_preserved=True)


def run(source, probe, output, *, subject_cutoff=.90, mask_cutoff=.80):
    source, probe, output = map(lambda p: Path(p).resolve(), (source, probe, output))
    if output.exists():
        raise FileExistsError(output)
    inputs = read(probe / "inputs.json")
    mask_vectors, mask_receipt = load_vectors(source / "worker-result")
    subject_vectors, subject_receipt, subject_hashes = load_subject_vectors(probe)
    for key in ("checkpoint_sha256", "base_model_artifact_tree_sha256", "model", "runtime"):
        if mask_receipt[key] != subject_receipt[key]:
            raise ValueError(f"SSE identity mismatch: {key}")
    protected = dict(inputs["protected_sha256"])
    for path, expected in subject_hashes.items():
        if path in protected and protected[path] != expected:
            raise ValueError(f'protected input changed: {path}')
        protected[path] = expected
    for folder in (source,):
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
    summary = dict(experiment_id=result["experiment_id"], posts=len(inputs["posts"]), subjects=len(sv),
                   empty_masks=sum(v is None for v in mv), mask_vectors=len(selected_masks),
                   same_post_groups=len(result["same_post_groups"]),
                   same_post_reduction=sum(len(g) - 1 for g in result["same_post_groups"]),
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
                      implementation_sha256={str(p.resolve()): _sha256_file(p) for p in
                                             (Path(__file__), Path(__file__).with_name("subject_hierarchy.py"))},
                      source_path=str(source), probe_path=str(probe), subjects=inputs["subjects"],
                      original_edges=inputs["edges"], masks=list(selected_masks.values()))
    output.mkdir(parents=True, exist_ok=False)
    for name, value in (("results", result), ("categories", view), ("provenance", provenance), ("summary", summary)):
        save(output / f"{name}.json", value)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    if len(sys.argv) > 1 and sys.argv[1] == 'prepare':
        parser.add_argument('--source', type=Path, required=True)
        parser.add_argument('--output', type=Path, required=True)
        parser.add_argument('--posts', nargs='+')
        parser.add_argument('--reuse-probe', type=Path)
        parser.add_argument('--protect', type=Path, nargs='*', default=[])
        args = parser.parse_args(sys.argv[2:])
        print(json.dumps(prepare(args.source, args.output, posts=args.posts,
                                 reuse_probe=args.reuse_probe, protected=args.protect), indent=2))
        return
    for name in ("source", "probe", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--subject-cutoff", type=float, default=.90)
    parser.add_argument("--mask-cutoff", type=float, default=.80)
    args = parser.parse_args()
    print(json.dumps(run(args.source, args.probe, args.output,
                         subject_cutoff=args.subject_cutoff, mask_cutoff=args.mask_cutoff), indent=2))


if __name__ == "__main__":
    main()
