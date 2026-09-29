"""AVv1: saved subject-vector ancestor voting; scores only, no placements.

Reuse SMv1 nodes without changing merges or links. Hide a query and its branch,
including repeated exact subject wording, before constructing voting evidence.
This is a small exhaustive diagnostic, not a production retrieval algorithm.
"""
import argparse
from collections import deque
import hashlib
import math
from pathlib import Path
import platform

from sse_multivector.ancestor_cosine_probe import cosine, load_vectors
from sse_multivector.subject_order_probe import read, reachable, save
from sse_multivector.worker import _sha256_file

TOLERANCE = 1e-12


def prepare_case(subjects, vectors, groups, edges, *, query):
    if (not groups or any(not g for g in groups)
            or sorted(i for g in groups for i in g) != list(range(len(subjects)))):
        raise ValueError("groups must partition original subjects")
    if len(vectors) != len(subjects) or not 0 <= query < len(groups):
        raise ValueError("invalid vector count or query")
    paths = reachable(len(groups), edges)
    if any(a == b for a, b in paths):
        raise ValueError("input graph contains a cycle")
    by_text = {}
    for s, v in zip(subjects, vectors, strict=True):
        cosine(vectors[0], v)
        if s["subject"] in by_text and tuple(v) != by_text[s["subject"]]:
            raise ValueError("identical subject text has different saved vectors")
        by_text[s["subject"]] = tuple(v)
    names = [set(subjects[i]["subject"] for i in g) for g in groups]
    excluded = {query}
    while True:
        old = set(excluded)
        excluded.update(b for a, b in paths if a in excluded)
        wording = set().union(*(names[g] for g in excluded))
        excluded.update(g for g, labels in enumerate(names) if labels & wording)
        if old == excluded:
            break
    active = sorted(set(range(len(groups))) - excluded)
    parents = {g: [] for g in active}
    for parent, child in sorted(set(map(tuple, edges))):
        if parent in parents and child in parents:
            parents[child].append(parent)

    def similarity(text):
        # No vector blending. Multi-name SMv1 nodes use the best constituent.
        return max(cosine(vectors[i], by_text[text]) for i in groups[query])

    direct = {g: max(similarity(text) for text in names[g]) for g in active}
    owners = {}
    for g in active:
        for text in sorted(names[g]):
            owners.setdefault(text, []).append(g)
    neighbors = []
    for text, nodes in sorted(owners.items()):
        distance = {}
        pending = deque((p, 1) for g in nodes for p in parents[g])
        while pending:
            node, hops = pending.popleft()
            if node in distance and distance[node] <= hops:
                continue
            distance[node] = hops
            pending.extend((p, hops + 1) for p in parents[node])
        neighbors.append(dict(subject=text, nodes=nodes, cosine=similarity(text),
                              ancestors=[dict(node=g, hops=h) for g, h in sorted(distance.items())]))
    return dict(query=query, known_parents=sorted({a for a, b in edges if b == query}),
                excluded_nodes=sorted(excluded), direct=[dict(node=g, cosine=v) for g, v in direct.items()],
                neighbors=sorted(neighbors, key=lambda r: (-r["cosine"], r["subject"])))


def score_case(case, *, k, decay):
    if not isinstance(k, int) or k < 1 or not math.isfinite(decay) or not 0 < decay <= 1:
        raise ValueError("positive integer k and finite decay in (0, 1] required")
    neighbors = [n for n in case["neighbors"] if n["cosine"] > 0]
    if len(neighbors) > k:
        cutoff = neighbors[k - 1]["cosine"]
        neighbors = [n for n in neighbors if n["cosine"] >= cutoff - TOLERANCE]
    evidence = {d["node"]: [] for d in case["direct"]}
    for neighbor in neighbors:
        for ancestor in neighbor["ancestors"]:
            evidence[ancestor["node"]].append(dict(
                subject=neighbor["subject"], source_nodes=neighbor["nodes"],
                cosine=neighbor["cosine"], hops=ancestor["hops"],
                contribution=neighbor["cosine"] * decay ** (ancestor["hops"] - 1)))
    ranking = [dict(node=d["node"], direct_cosine=d["cosine"],
                    vote_score=sum(e["contribution"] for e in evidence[d["node"]]),
                    evidence=evidence[d["node"]]) for d in case["direct"]]
    for row in ranking:
        row["direct_rank"] = 1 + sum(r["direct_cosine"] > row["direct_cosine"] + TOLERANCE for r in ranking)
        row["vote_rank"] = (1 + sum(r["vote_score"] > row["vote_score"] + TOLERANCE for r in ranking)
                            if row["vote_score"] > 0 else None)
    return dict(k=k, decay=decay, neighbors=neighbors,
                ranking=sorted(ranking, key=lambda r: (-r["vote_score"], r["node"])))


def run(probe, matching, output, *, holdouts, inspections, ks, decays):
    probe, matching, output = map(lambda p: Path(p).resolve(), (probe, matching, output))
    if output.exists():
        raise FileExistsError(output)
    inputs, matched = read(probe / "inputs.json"), read(matching / "results.json")
    provenance = read(matching / "provenance.json")
    protected = dict(provenance["protected_sha256"])
    if protected.get(str(probe / "inputs.json")) != _sha256_file(probe / "inputs.json"):
        raise ValueError("matching experiment does not reference these SP inputs")
    for path in (matching / "results.json", matching / "provenance.json", Path(__file__).resolve()):
        protected[str(path)] = _sha256_file(path)

    def verify():
        for path, expected in protected.items():
            if _sha256_file(Path(path)) != expected:
                raise ValueError(f"protected input changed: {path}")

    verify()
    saved, receipt = load_vectors(probe / "worker-result")
    if receipt["proposal_sha256"] != _sha256_file(probe / "inputs.json"):
        raise ValueError("subject vectors do not match saved SP inputs")
    subjects, groups, edges = inputs["subjects"], matched["groups"], matched["edges"]
    owner = {i: g for g, members in enumerate(groups) for i in members}
    mapped = sorted({(owner[a], owner[b]) for a, b in inputs["edges"] if owner[a] != owner[b]})
    if mapped != sorted(map(tuple, edges)):
        raise ValueError("matching graph is not the mapped original SP relationships")
    vectors = [saved[hashlib.sha256(s["subject"].encode()).hexdigest(), s["encoding_id"]] for s in subjects]
    references = {f'{s["note_short_id"]}:{s["number"]}': owner[i] for i, s in enumerate(subjects)}
    specifications = [(ref, "hidden-link") for ref in holdouts] + [(ref, "missing-link") for ref in inspections]
    if not specifications or len({ref for ref, _ in specifications}) != len(specifications):
        raise ValueError("nonempty, unique case references required")
    cases = []
    for ref, kind in specifications:
        case = prepare_case(subjects, vectors, groups, edges, query=references[ref])
        if kind == "hidden-link" and not case["known_parents"]:
            raise ValueError(f"hidden-link case has no known parent: {ref}")
        if kind == "missing-link" and case["known_parents"]:
            raise ValueError(f"missing-link case is not a current root: {ref}")
        runs = [score_case(case, k=k, decay=d) for k in ks for d in decays]
        if runs != [score_case(case, k=k, decay=d) for k in ks for d in decays]:
            raise ValueError("scoring did not reproduce deterministically")
        cases.append(dict(reference=ref, kind=kind, **case, runs=runs))
    nodes = [dict(node=g, subjects=sorted({subjects[i]["subject"] for i in members}),
                  origins=[subjects[i] for i in members]) for g, members in enumerate(groups)]
    measurements = []
    for k in ks:
        for decay in decays:
            rows = []
            for case in cases:
                if case["kind"] != "hidden-link":
                    continue
                result = next(r for r in case["runs"] if r["k"] == k and r["decay"] == decay)
                indexed = {r["node"]: r for r in result["ranking"]}
                for parent in case["known_parents"]:
                    row = indexed.get(parent, {})
                    rows.append(dict(reference=case["reference"], parent=parent,
                                     direct_rank=row.get("direct_rank"), vote_rank=row.get("vote_rank")))
            measurements.append(dict(k=k, decay=decay, hidden_links=len(rows),
                direct_top1=sum(r["direct_rank"] == 1 for r in rows),
                vote_top1=sum(r["vote_rank"] == 1 for r in rows),
                direct_top3=sum(r["direct_rank"] is not None and r["direct_rank"] <= 3 for r in rows),
                vote_top3=sum(r["vote_rank"] is not None and r["vote_rank"] <= 3 for r in rows),
                supported=sum(r["vote_rank"] is not None for r in rows), cases=rows))
    summary = dict(experiment_id="AVv1", posts=len(inputs["posts"]), nodes=len(groups),
                   hidden_link_cases=len(holdouts), missing_link_cases=len(inspections), measurements=measurements,
                   inference_calls=0, placements=0, protected_inputs_unchanged=True,
                   deterministic_rerun_matches=True)
    report = dict(experiment_id="AVv1", nodes=nodes, original_edges=edges, cases=cases,
        settings=dict(ks=ks, decays=decays, vector_type="standalone subject-text SSE only",
            node_cosine="maximum over constituent subject texts; no vector blending",
            neighbors="k distinct exact texts with positive cosine; include ties at kth score",
            voting="one vote per retrieved exact text per ancestor; shortest remaining path",
            weight="cosine(query subject, neighbor subject) * decay ** (hops - 1)",
            exclusion="query, descendants, identical-wording nodes, their descendants; repeat to closure",
            acceptance="none; ranks are not valid-placement decisions",
            metric="recovery of saved direct SP parents, not semantic accuracy; ties share rank"),
        protected_sha256=protected, python=platform.python_version())
    verify()
    output.mkdir(parents=True, exist_ok=False)
    save(output / "results.json", report)
    save(output / "summary.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("probe", "matching", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--holdout", action="append", default=[], help="POST:SP_NUMBER")
    parser.add_argument("--inspect", action="append", default=[], help="Current root POST:SP_NUMBER")
    parser.add_argument("--k", type=int, nargs="+", default=[3, 5, 10])
    parser.add_argument("--decay", type=float, nargs="+", default=[.5, 1.])
    args = parser.parse_args()
    result = run(args.probe, args.matching, args.output, holdouts=args.holdout,
                 inspections=args.inspect, ks=args.k, decays=args.decay)
    for m in result["measurements"]:
        print(f'k={m["k"]} decay={m["decay"]}: voting top1={m["vote_top1"]}/{m["hidden_links"]}, '
              f'top3={m["vote_top3"]}; cosine top1={m["direct_top1"]}, top3={m["direct_top3"]}')


if __name__ == "__main__":
    main()
