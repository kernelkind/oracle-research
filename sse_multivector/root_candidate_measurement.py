"""Offline sizing of root-candidate supplements; never infer or place nodes.

This is a small-corpus measurement, not a changed hierarchy-build policy.
Original SP references, subject vectors and shared production packers are reused.
"""

from collections import Counter, defaultdict
import hashlib
import importlib.metadata
import math
from pathlib import Path
import re
import resource
import sys
import time

try:
    from .bounded_hierarchy_candidates import (
        _ancestor, _validate_graph, compact_entries, HNSWSubjectNeighbors,
        build_discovery, pack_discovery_requests,
    )
    from .subject_matching_probe import load_subject_vectors
    from . import experiment as workflow
    from .experiment_inputs import digest
except ImportError:
    from bounded_hierarchy_candidates import (
        _ancestor, _validate_graph, compact_entries, HNSWSubjectNeighbors,
        build_discovery, pack_discovery_requests,
    )
    from subject_matching_probe import load_subject_vectors
    import experiment as workflow
    from experiment_inputs import digest


class RootCandidateSearch:
    """Bounded ANN search of existing roots using at most two original wordings.

    Queries may be internal hierarchy nodes. Thirty-two candidate nodes are
    inspected; exclusions do not trigger an unbounded refill. Exact retrieval
    is available only for this explicitly bounded small-corpus measurement.
    """

    def __init__(self, inputs, hierarchy, vectors, *, backend="hnsw", inspection_limit=32):
        import numpy as np

        if len(inputs["subjects"]) > 5000:
            raise ValueError("root measurement is limited to 5000 SP entries")
        if backend not in ("exact", "hnsw"):
            raise ValueError("root search backend must be exact or hnsw")
        if type(inspection_limit) is not int or not 1 <= inspection_limit <= 32:
            raise ValueError("root inspection limit must be one through 32")
        self.np, self.backend, self.inspection_limit = np, backend, inspection_limit
        self.owner, self.groups, self.parents, _ = _validate_graph(inputs, hierarchy)
        self.references = {n: compact_entries(inputs, g) for n, g in self.groups.items()}
        self.wordings = {n: list(dict.fromkeys(e["subject"] for e in entries))
                         for n, entries in self.references.items()}
        self.roots = sorted(n for n, parents in self.parents.items() if not parents)
        self.normalized = {}
        for word in sorted({w for ws in self.wordings.values() for w in ws}):
            identity = hashlib.sha256(word.encode()).hexdigest()
            v = np.asarray(vectors[identity, identity[:16]], dtype=np.float64)
            norm = np.linalg.norm(v)
            if v.ndim != 1 or not np.isfinite(v).all() or not norm:
                raise ValueError("finite nonzero standalone subject vector required")
            self.normalized[word] = v / norm
        self.word_roots = defaultdict(list)
        for node in self.roots:
            for word in self.wordings[node]:
                self.word_roots[word].append(node)
        self.words = sorted(self.word_roots)
        self.matrix = np.asarray([self.normalized[w] for w in self.words])
        self.metadata = dict(backend=backend, roots=len(self.roots),
            indexed_wordings=len(self.words), dimensions=self.matrix.shape[1],
            normalized_subject_vector_bytes=sum(v.nbytes for v in self.normalized.values()),
            root_matrix_bytes=self.matrix.nbytes,
            original_wordings_per_node=2, inspection_limit=inspection_limit,
            vector_probes_per_query_wording=2 * inspection_limit,
            maximum_sp_entries=5000, exact_search_is_small_corpus_only=True)
        self.exclusions = Counter()
        if backend == "hnsw":
            import hnswlib
            self.index = hnswlib.Index(space="cosine", dim=self.matrix.shape[1])
            self.index.init_index(max_elements=len(self.words), M=16,
                ef_construction=200, random_seed=17)
            self.index.set_num_threads(1)
            self.index.add_items(self.matrix.astype(np.float32),
                np.arange(len(self.words)), num_threads=1)
            self.index.set_ef(128)
            self.metadata.update(library="hnswlib",
                library_version=importlib.metadata.version("hnswlib"),
                M=16, ef_construction=200, ef_search=128, seed=17, threads=1)

    def candidates(self, query, *, limit=5, judged_pairs=()):
        if type(limit) is not int or not 0 <= limit <= self.inspection_limit:
            raise ValueError("candidate quota must fit the bounded inspection limit")
        if query not in self.groups:
            raise ValueError("query must identify a current hierarchy node")
        scores = {}
        for word in self.wordings[query]:
            vector = self.normalized[word]
            if self.backend == "hnsw":
                labels, _ = self.index.knn_query(vector.astype(self.np.float32),
                    k=min(len(self.words), 2 * self.inspection_limit), num_threads=1)
                labels = labels[0]
            else:
                labels = range(len(self.words))
            values = self.matrix[list(labels)] @ vector
            for label, value in zip(labels, values):
                candidate_word = self.words[int(label)]
                # Duplicate wordings can map to multiple roots; expansion is bounded too.
                for node in self.word_roots[candidate_word][:self.inspection_limit]:
                    item = dict(id=node, cosine=max(-1., min(1., float(value))),
                                query_wording=word, candidate_wording=candidate_word)
                    old = scores.get(node)
                    if old is None or item["cosine"] > old["cosine"]:
                        scores[node] = item
        result = []
        for node in sorted(scores, key=lambda n: (-scores[n]["cosine"], n))[:self.inspection_limit]:
            if node == query:
                self.exclusions["self"] += 1
                continue
            if frozenset((query, node)) in judged_pairs:
                self.exclusions["already_judged"] += 1
                continue
            related = _ancestor(node, query, self.parents)
            if related is False:
                related = _ancestor(query, node, self.parents)
            if related is None:
                self.exclusions["reachability_work_budget"] += 1
            elif related:
                self.exclusions["existing_ancestry"] += 1
            else:
                result.append(scores[node])
        return result[:limit]


def _distribution(values):
    values = sorted(values)
    if not values:
        return dict(total=0, min=0, max=0, mean=0, p95=0)
    return dict(total=sum(values), min=values[0], max=values[-1],
                mean=sum(values) / len(values), p95=values[math.ceil(.95 * len(values)) - 1])


def _diagnostic_pairs(inputs, hierarchy, pairs):
    """Validate original SP references before retrieval or vector loading."""
    pairs = list(pairs)
    owners = {i: min(group) for group in hierarchy["groups"] for i in group} if pairs else {}
    for pair in pairs:
        if (not isinstance(pair, (tuple, list)) or len(pair) != 2 or
                any(not isinstance(n, str) or not re.fullmatch(r"S[0-9]{4}", n) for n in pair)):
            raise ValueError("diagnostic pairs require two original S#### IDs")
        indices = [int(n[1:]) for n in pair]
        if any(i >= len(inputs["subjects"]) or i not in owners for i in indices):
            raise ValueError("diagnostic ID is outside the original SP source hierarchy")
        if owners[indices[0]] == owners[indices[1]]:
            raise ValueError("diagnostic pair must identify two distinct current nodes")
    return pairs


def measure_variants(inputs, hierarchy, vectors, judgments, discovery_template,
                     comparison_template, *, quotas=(3, 5, 10), minimum_existing=(0, 30, 45, 55),
                     diagnostic_pairs=()):
    """Use real preparation/packing without model responses or graph mutation."""
    try:
        from .bounded_hierarchy_sizing import comparison_capacity_bound
    except ImportError:
        from bounded_hierarchy_sizing import comparison_capacity_bound

    diagnostic_pairs = _diagnostic_pairs(inputs, hierarchy, diagnostic_pairs)
    started = time.perf_counter()
    search = RootCandidateSearch(inputs, hierarchy, vectors)
    exact = RootCandidateSearch(inputs, hierarchy, vectors, backend="exact")
    judged = {frozenset((search.owner[int(c["A"][1:])], search.owner[int(c["B"][1:])]))
              for c in judgments}
    base = build_discovery(inputs, hierarchy, vectors, discovery_template,
        judged_pairs=judgments,
        nearest_neighbors=HNSWSubjectNeighbors(inputs, hierarchy, vectors))
    baseline_seconds = time.perf_counter() - started
    by_post, old_eligible = {}, {}
    for case in base["cases"]:
        e = case["evidence"]
        post = by_post.setdefault(e["source_post"], dict(queries=[], candidates=e["candidates"]))
        if post["candidates"] != e["candidates"]:
            raise ValueError("saved post catalogues disagree")
        post["queries"].extend(e["queries"])
        for query in e["queries"]:
            old_eligible[query] = set(e["candidates"]) - set(e["excluded_candidates"].get(query, []))
    retrieved = {q: search.candidates(q, limit=max(quotas), judged_pairs=judged)
                 for q in sorted(search.groups)}
    exact_retrieved = {q: exact.candidates(q, limit=max(quotas), judged_pairs=judged)
                       for q in sorted(search.groups)}
    differences = {k: sum([r["id"] for r in retrieved[q][:k]] !=
                         [r["id"] for r in exact_retrieved[q][:k]] for q in retrieved)
                   for k in quotas}
    profiles = []
    for quota in quotas:
        supplemental = {q: [r["id"] for r in rs[:quota]] for q, rs in retrieved.items()}
        modes = [("combined_catalogue", m, "all_nodes") for m in minimum_existing] + [
            ("root_only_followup", 0, scope) for scope in ("all_nodes", "roots")]
        for mode, minimum, scope in modes:
            start = time.perf_counter()
            cases = []
            profile = dict(root_quota=quota, minimum_existing_candidates=minimum,
                           catalogue_mode=mode, query_scope=scope,
                           existing_graph_and_answers_unchanged=True)
            try:
                for post, group in sorted(by_post.items()):
                    queries = [q for q in group["queries"] if scope == "all_nodes" or q in search.roots]
                    if not queries:
                        continue
                    existing = group["candidates"] if mode == "combined_catalogue" else []
                    base_eligibility = old_eligible if existing else {q: set() for q in queries}
                    cases.extend(pack_discovery_requests(post, queries,
                        search.references, existing, search.wordings,
                        base_eligibility, discovery_template,
                        supplemental_by_query={q: supplemental[q] for q in queries},
                        minimum_existing_candidates=minimum))
            except ValueError as error:
                profile.update(status="refused", reason=str(error))
                profiles.append(profile)
                continue
            eligible = {}
            for case in cases:
                e = case["evidence"]
                for q in e["queries"]:
                    eligible[q] = set(e["candidates"]) - set(e["excluded_candidates"].get(q, []))
                    if not set(supplemental[q]) <= eligible[q]:
                        raise AssertionError("packing dropped a mandatory root candidate")
            universe = {tuple(sorted((q, c))) for q, cs in eligible.items() for c in cs}
            capacity = comparison_capacity_bound(search.references, comparison_template, universe)
            if capacity["guaranteed_pairs_per_request"] < 1:
                raise ValueError("cannot certify verification requests within the token limit")
            nominations = sum(min(3, len(cs)) for cs in eligible.values())
            comparisons = math.ceil(min(nominations, len(universe)) / capacity["guaranteed_pairs_per_request"])
            targets = []
            for a, b in diagnostic_pairs:
                a, b = search.owner[int(a[1:])], search.owner[int(b[1:])]
                directions = []
                for q, c in [(a, b), (b, a)]:
                    root = next((r for r in retrieved[q] if r["id"] == c), None)
                    directions.append(dict(query=q, candidate=c, candidate_is_root=c in search.roots,
                        root_rank=next((i + 1 for i, r in enumerate(retrieved[q]) if r["id"] == c), None),
                        root_score=root, in_original=c in old_eligible[q], query_in_scope=q in eligible,
                        in_combined_request=c in eligible.get(q, ())))
                targets.append(dict(pair=[a, b], directions=directions))
            profile.update(status="measured", discovery_requests=len(cases), queried_nodes=len(eligible),
                rendered_input_tokens=_distribution([c["evidence"]["input_tokens"] for c in cases]),
                catalogue_sizes=_distribution([len(c["evidence"]["candidates"]) for c in cases]),
                queries_per_request=_distribution([len(c["evidence"]["queries"]) for c in cases]),
                old_candidates_available=sum(len(old_eligible[q]) for q in eligible),
                old_candidates_retained=sum(len(cs & old_eligible[q]) for q, cs in eligible.items()),
                old_candidates_not_reoffered=sum(len(old_eligible[q] - cs) for q, cs in eligible.items()),
                old_candidates_displaced=(sum(len(old_eligible[q] - cs) for q, cs in eligible.items())
                                          if mode == "combined_catalogue" else 0),
                supplemental_candidates_retained=sum(len(supplemental[q]) for q in eligible),
                comparison_pair_universe=len(universe), maximum_nominations=nominations,
                comparison_capacity=capacity, maximum_verification_requests=comparisons,
                maximum_first_attempt_requests=len(cases) + comparisons,
                maximum_attempts_with_one_retry=2 * (len(cases) + comparisons),
                maximum_rendered_input_tokens_first_attempt=(
                    sum(c["evidence"]["input_tokens"] for c in cases) + 4000 * comparisons),
                maximum_rendered_input_tokens_with_one_retry=2 * (
                    sum(c["evidence"]["input_tokens"] for c in cases) + 4000 * comparisons),
                diagnostic_pairs=targets, seconds=time.perf_counter() - start)
            profiles.append(profile)
    # Linux getrusage can retain a launcher's pre-exec high-water mark. VmHWM
    # measures this executable's actual peak instead of attributing that to ANN.
    if sys.platform == "linux":
        peak_rss = int(next(line.split()[1] for line in Path("/proc/self/status").read_text().splitlines()
                            if line.startswith("VmHWM:")))
        rss_source = "/proc/self/status VmHWM"
    else:
        peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (
            1024 if sys.platform == "darwin" else 1)
        rss_source = "getrusage RUSAGE_SELF"
    return dict(schema_version=1, measurement_id="RCMv1", inference_attempts=0,
        status="offline_measurement_not_a_build_policy", node_count=len(search.groups),
        root_search=search.metadata, ann_vs_exact_changed_queries=differences,
        root_search_exclusions=dict(search.exclusions),
        baseline=dict(discovery_requests=len(base["cases"]),
            rendered_input_tokens=_distribution([c["evidence"]["input_tokens"] for c in base["cases"]]),
            seconds=baseline_seconds), profiles=profiles,
        total_output_token_ceiling=None,
        output_ceiling_reason="saved subscription settings have no hard output-token cap",
        process_peak_rss_kib=peak_rss, process_peak_rss_source=rss_source,
        total_seconds=time.perf_counter() - started)


def measure_build(build, destination, *, diagnostic_pairs=()):
    """Shared-runner offline entrypoint. Writes only a separate ignored measurement."""
    try:
        from .bounded_hierarchy_build import _budget
    except ImportError:
        from bounded_hierarchy_build import _budget

    build, destination = Path(build).resolve(), Path(destination).resolve()
    if destination.exists():
        raise FileExistsError(destination)
    envelope = workflow.read(build / "bounded-build.json")
    plan = envelope["plan"]
    if digest(plan) != envelope["sha256"]:
        raise ValueError("saved build manifest changed")
    budget = _budget(build, plan)
    snapshot = Path(plan["export"])
    manifest_path = snapshot / "manifest.json"
    manifest = workflow.read(manifest_path)
    protected = {str(manifest_path): hashlib.sha256(manifest_path.read_bytes()).hexdigest()}
    for name, expected in manifest["files"].items():
        path = snapshot / name
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"saved hierarchy export changed: {name}")
        protected[str(path)] = expected
    input_path = Path(plan["spec"]["inputs"])
    inputs = workflow.read(input_path)
    measured = hashlib.sha256(input_path.read_bytes()).hexdigest()
    if measured != plan["protected_sha256"][str(input_path)]:
        raise ValueError("saved original SP inputs changed")
    protected[str(input_path)] = measured
    if len(inputs["subjects"]) > 5000:
        raise ValueError("root measurement is limited to 5000 SP entries")
    hierarchy = workflow.read(snapshot / "results.json")
    diagnostic_pairs = _diagnostic_pairs(inputs, hierarchy, diagnostic_pairs)
    vectors, receipt, vector_sources = load_subject_vectors(Path(plan["spec"]["subject_probe"]))
    protected.update(vector_sources)
    templates = {}
    for phase in ("discovery", "comparison"):
        path = Path(plan["spec"]["prompts"][phase]["path"])
        measured = hashlib.sha256(path.read_bytes()).hexdigest()
        if measured != plan["protected_sha256"][str(path)]:
            raise ValueError("saved prompt changed")
        protected[str(path)] = measured
        templates[phase] = path.read_text()
    code_sha256 = {}
    for name in ("root_candidate_measurement.py", "bounded_hierarchy_candidates.py",
                 "bounded_hierarchy_sizing.py", "bounded_hierarchy_workflow.py", "experiment.py"):
        path = Path(__file__).with_name(name).resolve()
        code_sha256[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    protected.update(code_sha256)
    result = measure_variants(inputs, hierarchy, vectors,
        plan["comparisons"], templates["discovery"], templates["comparison"],
        diagnostic_pairs=diagnostic_pairs)
    result.update(source_build=str(build), source_snapshot=str(snapshot), protected_sha256=protected,
        source_build_plan_sha256=envelope["sha256"], code_sha256=code_sha256,
        source_prompt_ids={p: plan["spec"]["prompts"][p]["id"] for p in templates},
        source_runner=plan["spec"]["runner"], tokenizer="o200k_base",
        token_counts_are_rendered_proxy_not_provider_billing=True,
        existing_budget=budget,
        queries_at_existing_nomination_limit=sum(plan["quota"].get(n, 0) >=
            plan["spec"]["max_nominations_per_reference"] for n in
            {f'S{min(g):04d}' for g in hierarchy["groups"]}),
        source_build_finished=plan["status"] == "finished",
        requires_new_versioned_pass_authorization=True)
    for profile in result["profiles"]:
        if profile["status"] == "measured":
            profile["within_remaining_first_attempt_budget"] = (
                profile["maximum_first_attempt_requests"] <= budget["limit"] - budget["used"])
            profile["within_remaining_budget_with_one_retry_each"] = (
                profile["maximum_attempts_with_one_retry"] <= budget["limit"] - budget["used"])
    for path, expected in protected.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected:
            raise ValueError("source changed during measurement")
    destination.mkdir(parents=True)
    workflow.write(destination / "report.json", result)
    return result
