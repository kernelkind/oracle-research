"""Bounded, source-bound comparison selection; no semantic judgments or inference."""

from collections import Counter, defaultdict, deque
from graphlib import CycleError, TopologicalSorter
from heapq import nsmallest
import hashlib
import importlib.metadata
import json
import math
import re


def _node_id(members):
    return f"S{min(members):04d}"


def compact_entries(inputs, members):
    """Retain the first SP entry, then the first differing wording or context."""
    subjects = inputs["subjects"]
    members = list(members)
    if not members or any(type(i) is not int or not 0 <= i < len(subjects)
                          for i in members):
        raise ValueError("nonempty original SP member indices required")
    members = sorted(set(members))
    first = members[0]
    second = next((i for i in members
                   if subjects[i]["subject"] != subjects[first]["subject"]), None)
    if second is None:
        second = next((i for i in members
                       if subjects[i]["context"] != subjects[first]["context"]), None)
    selected = [first] + ([second] if second is not None else [])
    entries = []
    for i in selected:
        subject = subjects[i]
        if (subject.get("index") != i or not isinstance(subject.get("subject"), str)
                or not subject["subject"] or not isinstance(subject.get("context"), str)):
            raise ValueError("original SP index, subject wording and context required")
        entries.append(dict(index=i, subject=subject["subject"], context=subject["context"]))
    return entries


class _SubjectVectors:
    """Shared source-vector identity, normalization and wording-to-node index."""

    def __init__(self, inputs, hierarchy, subject_vectors, *, max_wordings=None):
        try:
            import numpy as np
        except ImportError as error:
            raise RuntimeError("subject retrieval requires numpy") from error
        self.np = np
        word_nodes = defaultdict(set)
        for members in hierarchy["groups"]:
            node = _node_id(members)
            for i in members:
                word_nodes[inputs["subjects"][i]["subject"]].add(node)
        self.words = sorted(word_nodes)
        if max_wordings is not None and len(self.words) > max_wordings:
            raise ValueError(f"exact reference is limited to {max_wordings} distinct "
                             "wordings; supply an explicit ANN provider")
        self.word_nodes = {word: sorted(nodes) for word, nodes in word_nodes.items()}
        rows = []
        for word in self.words:
            digest = hashlib.sha256(word.encode()).hexdigest()
            try:
                rows.append(subject_vectors[digest, digest[:16]])
            except KeyError as error:
                raise ValueError(f"missing original subject vector: {word}") from error
        try:
            self.vectors = np.asarray(rows, dtype=np.float64)
        except (TypeError, ValueError) as error:
            raise ValueError("consistent finite subject vectors required") from error
        if (self.vectors.ndim != 2 or not self.vectors.shape[1]
                or not np.isfinite(self.vectors).all()):
            raise ValueError("consistent finite subject vectors required")
        norms = np.linalg.norm(self.vectors, axis=1)
        if not np.isfinite(norms).all() or (norms == 0).any():
            raise ValueError("nonzero finite subject-vector norms required")
        self.vectors /= norms[:, None]
        self.word_index = {word: i for i, word in enumerate(self.words)}

    def best_eligible(self, labels, scores, excluded_node_ids):
        best = None
        for label, score in zip(labels, scores, strict=True):
            node = next((n for n in self.word_nodes[self.words[int(label)]]
                         if n not in excluded_node_ids), None)
            if node is None:
                continue
            score = max(-1.0, min(1.0, float(score)))
            if (best is None or score > best[1] + 1e-12
                    or abs(score - best[1]) <= 1e-12 and node < best[0]):
                best = node, score
        return best


class ExactSubjectNeighbors:
    """Small-corpus exact reference behind an ANN-compatible nearest-node seam.

    Only normalized wording vectors are retained. A query scans bounded blocks;
    no node-by-node or wording-by-wording similarity table is materialized.
    ``nearest(wording, excluded_node_ids)`` returns ``(node_id, cosine)`` or None.
    """

    def __init__(self, inputs, hierarchy, subject_vectors, *, block_size=256):
        if type(block_size) is not int or block_size < 1:
            raise ValueError("positive exact-search block size required")
        self._block_size = block_size
        self._data = _SubjectVectors(inputs, hierarchy, subject_vectors, max_wordings=5000)
        self.metadata = dict(backend="exact-reference", block_size=block_size,
                             maximum_distinct_wordings=5000, dtype="float64")

    def nearest(self, wording, excluded_node_ids):
        data = self._data
        if wording not in data.word_index:
            raise ValueError("nearest-node query must be an original SP wording")
        query = data.vectors[data.word_index[wording]]
        best = None
        for start in range(0, len(data.words), self._block_size):
            stop = min(len(data.words), start + self._block_size)
            scores = data.vectors[start:stop] @ query
            match = data.best_eligible(range(start, stop), scores, excluded_node_ids)
            if match is not None and (best is None or match[1] > best[1] + 1e-12
                    or abs(match[1] - best[1]) <= 1e-12 and match[0] < best[0]):
                best = match
        return best


class HNSWSubjectNeighbors:
    """Deterministic HNSW retrieval; inspect at most 256 wording neighbors.

    Approximate retrieval only selects comparisons. It never authorizes semantic
    merging or placement, and does not fall back to an exhaustive large-corpus scan.
    """

    def __init__(self, inputs, hierarchy, subject_vectors):
        try:
            import hnswlib
        except ImportError as error:
            raise RuntimeError("HNSW subject retrieval requires hnswlib") from error
        data = self._data = _SubjectVectors(inputs, hierarchy, subject_vectors)
        self._index = hnswlib.Index(space="cosine", dim=data.vectors.shape[1])
        self._index.init_index(max_elements=len(data.words), M=16, ef_construction=200,
                               random_seed=17)
        self._index.set_num_threads(1)
        self._index.add_items(data.vectors.astype(data.np.float32),
                              data.np.arange(len(data.words)), num_threads=1)
        self._index.set_ef(128)
        self.metadata = dict(backend="hnsw", library="hnswlib",
            library_version=importlib.metadata.version("hnswlib"), space="cosine",
            sorted_unique_wording_insertion=True, random_seed=17, threads=1,
            M=16, ef_construction=200, ef_search=128, inspection_limit=256,
            index_dtype="float32", rerank_dtype="float64")

    def nearest(self, wording, excluded_node_ids):
        data = self._data
        if wording not in data.word_index:
            raise ValueError("nearest-node query must be an original SP wording")
        query = data.vectors[data.word_index[wording]]
        labels, _ = self._index.knn_query(query.astype(data.np.float32),
            k=min(256, len(data.words)), num_threads=1)
        labels = labels[0]
        scores = data.vectors[labels] @ query
        return data.best_eligible(labels, scores, excluded_node_ids)


def _validate_graph(inputs, hierarchy):
    subjects, groups = inputs["subjects"], hierarchy["groups"]
    if not subjects or not groups:
        raise ValueError("nonempty SP inputs and hierarchy required")
    for i, subject in enumerate(subjects):
        compact_entries(inputs, [i])
        if (not isinstance(subject.get("note_id"), str) or not subject["note_id"]
                or not isinstance(subject.get("note_short_id"), str)
                or not re.fullmatch(r"[A-Za-z0-9_-]+", subject["note_short_id"])):
            raise ValueError("original source-post identities required")
    members = [i for group in groups for i in group]
    if (any(not group for group in groups)
            or any(type(i) is not int for i in members)
            or len(members) != len(subjects) or set(members) != set(range(len(subjects)))):
        raise ValueError("hierarchy groups must partition every original SP entry")
    owner = {i: _node_id(group) for group in groups for i in group}
    by_id = {_node_id(group): sorted(group) for group in groups}
    node_ids = [_node_id(group) for group in groups]
    parents = {node: set() for node in node_ids}
    for edge in hierarchy.get("edges", []):
        if (len(edge) != 2 or any(type(i) is not int or not 0 <= i < len(groups)
                                  for i in edge)):
            raise ValueError("valid current hierarchy edges required")
        a, b = (node_ids[i] for i in edge)
        parents[b].add(a)
    try:
        list(TopologicalSorter(parents).static_order())
    except CycleError as error:
        raise ValueError("current hierarchy contains a cycle") from error
    sp_parents = {node: set() for node in node_ids}
    original_parents = {i: set() for i in range(len(subjects))}
    for edge in inputs.get("edges", []):
        if (len(edge) != 2 or any(type(i) is not int or not 0 <= i < len(subjects)
                                  for i in edge)):
            raise ValueError("valid original SP edges required")
        a, b = edge
        if subjects[a]["note_id"] != subjects[b]["note_id"]:
            raise ValueError("original SP relationships must stay within their source post")
        original_parents[b].add(a)
        if owner[a] != owner[b]:
            sp_parents[owner[b]].add(owner[a])
    try:
        list(TopologicalSorter(original_parents).static_order())
    except CycleError as error:
        raise ValueError("original SP relationships contain a cycle") from error
    for child, ancestors in sp_parents.items():
        for ancestor in ancestors:
            if ancestor in parents[child]:
                continue
            preserved = _ancestor(ancestor, child, parents, max_operations=20000)
            if preserved is None:
                raise ValueError("original SP ancestry validation exceeds its work budget")
            if not preserved:
                raise ValueError("current hierarchy does not preserve original SP ancestry")
    return owner, by_id, parents, sp_parents


def _ancestor(ancestor, node, parents, *, max_operations=2048):
    """Return reachability, or None if bounded node/adjacency work is exhausted."""
    seen, pending, operations = set(), [node], 0
    while pending:
        if operations == max_operations:
            return None
        operations += 1
        current = pending.pop()
        if current == ancestor:
            return True
        if current in seen:
            continue
        seen.add(current)
        adjacency = parents[current]
        if operations + len(adjacency) > max_operations:
            return None
        # Check width before sorting; the remaining work allowance bounds this
        # allocation as well as the actual inspected parent references.
        operations += len(adjacency)
        pending.extend(parent for parent in sorted(adjacency, reverse=True)
                       if parent not in seen)
    return False


def build_discovery(inputs, hierarchy, subject_vectors, template, *, query_nodes=None,
                    judged_pairs=(), max_candidates=60, max_queries=16,
                    max_input_tokens=4000, nearest_neighbors=None):
    """Prepare bounded PCPv2 requests from existing SP data and subject vectors.

    Every selected current node is queried once, owned by its earliest SP entry's
    source post. Candidates carry at most two original wordings, not contexts.
    Exact retrieval is a small-corpus reference; callers can supply an ANN provider
    with the same nearest-node contract. No result here authorizes a graph change.
    """
    try:
        from .experiment_inputs import render
    except ImportError:
        from experiment_inputs import render
    try:
        import tiktoken
    except ImportError as error:
        raise RuntimeError("bounded discovery requires tiktoken o200k_base") from error
    for value, name in [(max_candidates, "candidate"), (max_queries, "query"),
                        (max_input_tokens, "input-token")]:
        if type(value) is not int or value < 1:
            raise ValueError(f"positive {name} limit required")
    owner, by_id, parents, _ = _validate_graph(inputs, hierarchy)
    selected = sorted(by_id) if query_nodes is None else list(query_nodes)
    if len(set(selected)) != len(selected) or set(selected) - by_id.keys():
        raise ValueError("distinct current query node IDs required")
    judged = set()
    for pair in judged_pairs:
        a, b = (pair["A"], pair["B"]) if isinstance(pair, dict) else pair
        mapped = []
        for node in (a, b):
            if not isinstance(node, str) or not re.fullmatch(r"S[0-9]+", node):
                raise ValueError("original SP-based judged node IDs required")
            index = int(node[1:])
            if index not in owner:
                raise ValueError("judged node reference is outside original SP inputs")
            mapped.append(owner[index])
        judged.add(frozenset(mapped))
    subjects = inputs["subjects"]
    by_post = defaultdict(list)
    for i, subject in enumerate(subjects):
        by_post[subject["note_short_id"]].append(i)
    post_queries = defaultdict(list)
    for node in selected:
        post_queries[subjects[by_id[node][0]]["note_short_id"]].append(node)
    provider = nearest_neighbors
    if provider is None and selected:
        provider = ExactSubjectNeighbors(inputs, hierarchy, subject_vectors)
    encoding = tiktoken.get_encoding("o200k_base")
    references = {node: compact_entries(inputs, members) for node, members in by_id.items()}
    wordings = {node: list(dict.fromkeys(entry["subject"] for entry in entries))
                for node, entries in references.items()}
    parent_fronts = {node: nsmallest(3, adjacency) for node, adjacency in parents.items()}
    cases, retrieval_evidence, pool_counts, reachability_deferred = [], {}, [], []
    rendered_tokens = []
    for post, queries in sorted(post_queries.items()):
        queries.sort()
        local = {owner[i] for i in by_post[post]}
        anchors = sorted({subjects[i]["subject"] for i in by_post[post]})
        support, distances, searched = Counter(), {}, []
        for wording in anchors:
            nearest = provider.nearest(wording, local)
            if nearest is None:
                continue
            seed, score = nearest
            if (seed not in by_id or seed in local or not math.isfinite(score)
                    or not -1 <= score <= 1):
                raise ValueError("nearest-node provider returned an invalid eligible match")
            visited, pending, steps = {seed}, deque([(seed, 0)]), []
            while pending:
                node, distance = pending.popleft()
                support[node] += 1
                distances[node] = min(distances.get(node, 999), distance)
                steps.append(dict(node_id=node, ancestor_distance=distance))
                if distance == 2:
                    continue
                for parent in parent_fronts[node]:
                    if parent not in visited and len(visited) < 8:
                        visited.add(parent)
                        pending.append((parent, distance + 1))
            searched.append(dict(subject=wording, nearest_node=seed,
                                 subject_cosine=float(score), visited=steps))
        retrieval_evidence[post] = searched
        eligible_by_query = {}
        pool = local | set(support)
        capped = sorted(pool, key=lambda node: (
            -support[node], 0 if support[node] else 999,
            distances.get(node, 999), node))[:max_candidates]
        for query in queries:
            eligible = set()
            for node in capped:
                if node == query or frozenset((query, node)) in judged:
                    continue
                related = _ancestor(query, node, parents)
                if related is False:
                    related = _ancestor(node, query, parents)
                if related is None:
                    reachability_deferred.append(dict(query=query, candidate=node,
                        reason="reachability_work_budget", max_operations=2048))
                elif not related:
                    eligible.add(node)
            eligible_by_query[query] = eligible
        eligible = set().union(*eligible_by_query.values())
        candidates = [node for node in capped if node in eligible]
        pool_counts.append(len(candidates))

        def prepare(page_queries, page):
            excluded = {query: [node for node in candidates
                               if node not in eligible_by_query[query]]
                        for query in page_queries}
            excluded = {query: nodes for query, nodes in excluded.items() if nodes}
            payload = dict(queries=[dict(id=q, entries=references[q]) for q in page_queries],
                candidates=[dict(id=c, subjects=wordings[c]) for c in candidates],
                excluded_candidates=excluded)
            variables = {"INPUT_JSON": json.dumps(payload, ensure_ascii=False,
                                                   separators=(",", ":"))}
            tokens = len(encoding.encode(render(template, variables)))
            case = dict(id=f"PCPv2-{post}-{page:03d}", inputs=variables,
                evidence=dict(source_post=post, queries=list(page_queries),
                    candidates=list(candidates),
                    query_entries={q: references[q] for q in page_queries},
                    candidate_wordings={c: wordings[c] for c in candidates},
                    excluded_candidates=excluded, input_tokens=tokens))
            return case, tokens

        page, pending_queries = 1, []
        for query in queries:
            trial, tokens = prepare(pending_queries + [query], page)
            if pending_queries and (len(pending_queries) == max_queries
                                    or tokens > max_input_tokens):
                case, tokens = prepare(pending_queries, page)
                cases.append(case)
                rendered_tokens.append(tokens)
                page += 1
                pending_queries = []
                trial, tokens = prepare([query], page)
            if tokens > max_input_tokens:
                raise ValueError(f"query {query} and fixed candidate catalogue exceed "
                                 f"{max_input_tokens} rendered input tokens")
            pending_queries.append(query)
        if pending_queries:
            case, tokens = prepare(pending_queries, page)
            cases.append(case)
            rendered_tokens.append(tokens)
    settings = dict(neighbors_per_wording=1, ancestor_hops=2,
        parents_per_node=3, visited_nodes=8, candidate_limit=max_candidates,
        query_limit=max_queries, input_token_limit=max_input_tokens,
        eligibility_operations_per_walk=2048, sp_validation_operations_per_walk=20000,
        candidate_cap_before_eligibility=True,
        input_token_encoding="o200k_base", parent_order="stable-node-id",
        reference_policy="earliest SP; earliest differing wording, else context",
        candidate_order="distinct-anchor support, retrieval rank, ancestor distance, stable ID",
        ancestor_source="current hierarchy edges; original SP ancestry validated")
    return dict(cases=cases,
        source=dict(subject_count=len(subjects), node_count=len(by_id), node_ids=sorted(by_id)),
        provenance=dict(settings=settings,
            nearest_neighbors=getattr(provider, "metadata", dict(backend="external")),
            retrieval=retrieval_evidence,
            reachability_deferred=reachability_deferred,
            original_reference_indices={node: [entry["index"] for entry in references[node]]
                                        for node in selected}),
        stats=dict(queries=len(selected), source_posts=len(post_queries), cases=len(cases),
            candidate_nodes=sum(pool_counts), max_candidates=max(pool_counts, default=0),
            reachability_deferred=len(reachability_deferred),
            rendered_input_tokens=sum(rendered_tokens),
            max_rendered_input_tokens=max(rendered_tokens, default=0)))
