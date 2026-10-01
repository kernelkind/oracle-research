"""Apply saved bounded comparisons without discarding SP ancestry or evidence.

The caller validates model responses and receipts. This module makes no model
requests. Each proposal has an edge-inspection budget; unresolved proposals are
retained rather than forcing a merge, deleting an SP edge, or repairing a cycle.
"""

from collections import defaultdict, deque
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile

try:
    from .subject_hierarchy import browser_spec, reachable
    from .extraction_pipeline import _sha256_file, _canonical_json_bytes
    from .experiment import read, write
except ImportError:
    from subject_hierarchy import browser_spec, reachable
    from extraction_pipeline import _sha256_file, _canonical_json_bytes
    from experiment import read, write


EXPERIMENT_ID = "HG100-SOL01"
RELATIONS = {"equivalent", "a_parent_of_b", "b_parent_of_a", "neither", "uncertain"}


class _BudgetExceeded(Exception):
    pass


class _Work:
    def __init__(self, limit):
        self.limit, self.used = limit, 0

    def step(self, count=1):
        if self.used + count > self.limit:
            raise _BudgetExceeded
        self.used += count

    def require(self, count):
        # Sorting an entire wide adjacency before checking individual edges
        # would defeat the work budget, even if few neighbours are inspected.
        if self.used + count > self.limit:
            raise _BudgetExceeded


def _dag(count, edges):
    """Validate a complete snapshot in O(nodes + edges), not per proposal."""
    children = [set() for _ in range(count)]
    indegree = [0] * count
    for parent, child in edges:
        if not (0 <= parent < count and 0 <= child < count):
            raise ValueError("edge outside hierarchy")
        if child not in children[parent]:
            children[parent].add(child)
            indegree[child] += 1
    pending = deque(i for i, degree in enumerate(indegree) if not degree)
    visited = 0
    while pending:
        parent = pending.popleft()
        visited += 1
        for child in children[parent]:
            indegree[child] -= 1
            if not indegree[child]:
                pending.append(child)
    if visited != count:
        raise ValueError("hierarchy contains a cycle")


class _Graph:
    """Keep sparse original adjacency; canonicalize endpoints lazily."""
    def __init__(self, groups, edges):
        self.groups = groups
        self.owners = list(range(len(groups)))
        self.members = {i: {i} for i in range(len(groups))}
        self.outgoing = [set() for _ in groups]
        self.incoming = [set() for _ in groups]
        for a, b in edges:
            self.outgoing[a].add(b)
            self.incoming[b].add(a)

    def root(self, node):
        result = node
        while self.owners[result] != result:
            result = self.owners[result]
        while self.owners[node] != node:
            previous = node
            node = self.owners[node]
            self.owners[previous] = result
        return result

    def canonical(self, node, alias=None):
        node = self.root(node)
        return alias[0] if alias and node == alias[1] else node

    def children(self, node, work, alias=None, extra=None):
        node = self.canonical(node, alias)
        collections = [self.members[node]]
        if alias and node == alias[0]:
            collections.append(self.members[alias[1]])
        seen = set()
        for collection in collections:
            work.require(len(collection))
            for original in sorted(collection):
                work.step()
                work.require(len(self.outgoing[original]))
                for child in sorted(self.outgoing[original]):
                    work.step()
                    child = self.canonical(child, alias)
                    if child != node and child not in seen:
                        seen.add(child)
                        yield child
        if extra and node == self.canonical(extra[0], alias):
            work.step()
            child = self.canonical(extra[1], alias)
            if child != node and child not in seen:
                yield child

    def reaches(self, start, target, work, *, alias=None, extra=None, indirect=False):
        start, target = self.canonical(start, alias), self.canonical(target, alias)
        if start == target:
            return True
        pending, visited = deque([start]), {start}
        while pending:
            node = pending.popleft()
            work.step()
            for child in self.children(node, work, alias, extra):
                if child == target:
                    # A direct edge becomes an internal SP relationship after
                    # equivalence; a path through another node creates a cycle.
                    if not indirect or node != start:
                        return True
                    continue
                if child not in visited:
                    visited.add(child)
                    pending.append(child)
        return False

    def path(self, start, target, work):
        """Return one shortest ancestry witness within an explicit work budget."""
        start, target = self.root(start), self.root(target)
        previous = {start: None}
        pending = deque([start])
        while pending:
            node = pending.popleft()
            work.step()
            if node == target:
                result = []
                while node is not None:
                    result.append(node)
                    node = previous[node]
                return list(reversed(result))
            for child in self.children(node, work):
                if child not in previous:
                    previous[child] = node
                    pending.append(child)
        return None

    def parents(self, node, work):
        node = self.root(node)
        seen = set()
        work.require(len(self.members[node]))
        for original in sorted(self.members[node]):
            work.step()
            work.require(len(self.incoming[original]))
            for parent in sorted(self.incoming[original]):
                work.step()
                parent = self.root(parent)
                if parent != node and parent not in seen:
                    seen.add(parent)
                    yield parent

    def closure(self, start, work, *, reverse=False):
        """Bounded ancestor/descendant neighbourhood, including its start."""
        start = self.root(start)
        pending, visited = deque([start]), {start}
        while pending:
            node = pending.popleft()
            work.step()
            neighbors = self.parents(node, work) if reverse else self.children(node, work)
            for neighbor in neighbors:
                if neighbor not in visited:
                    visited.add(neighbor)
                    pending.append(neighbor)
        return visited

    def add_edge(self, parent, child):
        self.outgoing[parent].add(child)
        self.incoming[child].add(parent)

    def combine(self, a, b, work):
        work.step(len(self.members[b]))
        self.owners[b] = a
        self.members[a].update(self.members.pop(b))

    def snapshot(self):
        roots = sorted(self.members, key=lambda i: min(self.groups[j][0]
                                                     for j in self.members[i]))
        groups = [sorted(m for j in self.members[i] for m in self.groups[j]) for i in roots]
        indices = {root: i for i, root in enumerate(roots)}
        owners = [None] * sum(map(len, groups))
        for i, group in enumerate(groups):
            for member in group:
                owners[member] = i
        edges = {(indices[self.root(a)], indices[self.root(b)])
                 for a, children in enumerate(self.outgoing) for b in children
                 if self.root(a) != self.root(b)}
        return groups, owners, sorted(edges)


def _normalized(judgment, owners):
    if not isinstance(judgment, dict):
        raise ValueError("judgment must be an object")
    relation = judgment.get("answer", {}).get("relation")
    if relation not in RELATIONS:
        raise ValueError("unsupported comparison relation")
    nodes = []
    for key in ("A", "B"):
        identifier = judgment.get(key)
        if (not isinstance(identifier, str) or not identifier.startswith("S")
                or not identifier[1:].isdigit()):
            raise ValueError("unknown hierarchy node")
        member = int(identifier[1:])
        if not 0 <= member < len(owners):
            raise ValueError(f"unknown hierarchy node: {identifier}")
        nodes.append(owners[member])
    a, b = nodes
    if a > b:
        a, b = b, a
        relation = {"a_parent_of_b": "b_parent_of_a",
                    "b_parent_of_a": "a_parent_of_b"}.get(relation, relation)
    return a, b, relation


def apply_relations(inputs, hierarchy, judgments, *, work_budget=20000,
                    freeze_membership=False, cross_pair_neither="binding"):
    """Return a lossless hierarchy plus applied/deferred saved judgments.

    ``judgments`` includes previously accepted comparisons as well as fresh
    comparisons: historical neither constraints must not be omitted. S IDs
    refer to original SP indices, so IDs survive earlier accepted merges.
    The fixed meaning reference is always the smallest original member index.
    """
    if not isinstance(work_budget, int) or isinstance(work_budget, bool) or work_budget < 0:
        raise ValueError("work_budget must be a nonnegative integer")
    if not isinstance(freeze_membership, bool):
        raise ValueError("freeze_membership must be boolean")
    if cross_pair_neither not in {"binding", "diagnostic"}:
        raise ValueError("unknown cross-pair neither policy")
    if cross_pair_neither == "diagnostic" and not freeze_membership:
        raise ValueError("diagnostic neither policy requires fixed membership")
    size = len(inputs["subjects"])
    groups = [sorted(group) for group in hierarchy["groups"]]
    flattened = [m for group in groups for m in group]
    if (any(not group for group in groups) or len(flattened) != size
            or sorted(flattened) != list(range(size))):
        raise ValueError("hierarchy must preserve every SP subject exactly once")
    owners = [None] * size
    for i, group in enumerate(groups):
        for member in group:
            owners[member] = i
    if owners != hierarchy["member_to_group"]:
        raise ValueError("hierarchy member mapping does not match groups")
    edges = {tuple(edge) for edge in hierarchy["edges"]}
    sp_edges = set()
    for a, b in inputs["edges"]:
        if not (0 <= a < size and 0 <= b < size):
            raise ValueError("SP edge outside subjects")
        if owners[a] != owners[b]:
            sp_edges.add((owners[a], owners[b]))
    edges.update(sp_edges)
    _dag(len(groups), edges)
    graph = _Graph(groups, edges)
    records = []
    meanings = defaultdict(set)
    for judgment in judgments:
        a, b, relation = _normalized(judgment, owners)
        records.append((a, b, relation, deepcopy(judgment)))
        if relation != "uncertain":
            meanings[a, b].add(relation)
    records.sort(key=lambda item: (item[0], item[1], item[2],
                                   json.dumps(item[3], sort_keys=True)))
    conflicts = {pair for pair, values in meanings.items() if len(values) > 1}
    applied, deferred = [], []
    constraints = defaultdict(set)
    distinct = defaultdict(set)
    for a, b, relation, _ in records:
        if (a, b) not in conflicts and relation in {"a_parent_of_b", "b_parent_of_a"}:
            # Teacher parent answers assert strictly different scope, unlike
            # original SP ancestry, which must survive as ancestor-or-equal.
            distinct[a].add(b)
            distinct[b].add(a)
    inspections = 0

    def record(judgment, reason, work, *, accepted=False):
        nonlocal inspections
        inspections += work.used
        destination = applied if accepted else deferred
        destination.append(dict(judgment=judgment, reason=reason, inspected=work.used))

    def compatible(ancestors, descendants, work):
        # Only these endpoint pairs can gain new ancestry. The index is on
        # original group IDs; lazy unions preserve every indexed constraint.
        work.require(len(ancestors))
        for ancestor in sorted(ancestors):
            work.step()
            work.require(len(graph.members[ancestor]))
            for original in sorted(graph.members[ancestor]):
                work.step()
                work.require(len(constraints[original]))
                for other in sorted(constraints[original]):
                    work.step()
                    if graph.root(other) in descendants:
                        return False
        return True

    def permits(work, *, merge=None, edge=None):
        if not constraints:
            return True
        a, b = merge or edge
        ancestors_a = graph.closure(a, work, reverse=True)
        descendants_b = graph.closure(b, work)
        if not compatible(ancestors_a, descendants_b, work):
            return False
        if merge:
            return compatible(graph.closure(b, work, reverse=True),
                              graph.closure(a, work), work)
        return True

    def constrain(a, b):
        constraints[a].add(b)
        constraints[b].add(a)

    def distinct_meanings(a, b, work):
        work.require(len(graph.members[a]))
        for original in sorted(graph.members[a]):
            work.step()
            work.require(len(distinct[original]))
            for other in sorted(distinct[original]):
                work.step()
                if graph.root(other) == b:
                    return False
        return True

    # Record negative constraints before considering changes; disagreements
    # on the same pair defer every answer rather than picking a winner.
    for a, b, relation, judgment in records:
        if (a, b) in conflicts:
            record(judgment, "judgment_conflict", _Work(work_budget))
        elif relation == "uncertain":
            record(judgment, "uncertain", _Work(work_budget))
        elif relation == "neither":
            work = _Work(work_budget)
            try:
                work.step()
                if a == b:
                    record(judgment, "equivalent_conflict", work)
                elif graph.reaches(a, b, work) or graph.reaches(b, a, work):
                    record(judgment, "neither_conflict", work)
                else:
                    constrain(a, b)
                    record(judgment, "recorded", work, accepted=True)
            except _BudgetExceeded:
                constrain(a, b)
                record(judgment, "work_budget", work)

    for stage in ("equivalent", "ancestor"):
        for original_a, original_b, relation, judgment in records:
            if ((original_a, original_b) in conflicts or relation in {"neither", "uncertain"}
                    or (relation == "equivalent") != (stage == "equivalent")):
                continue
            work = _Work(work_budget)
            a, b = graph.root(original_a), graph.root(original_b)
            try:
                work.step()
                if relation == "equivalent":
                    if a == b:
                        record(judgment, "already_equivalent", work, accepted=True)
                        continue
                    if freeze_membership:
                        record(judgment, "fixed_membership", work)
                        continue
                    if min(groups[a]) > min(groups[b]):
                        a, b = b, a
                    if (graph.reaches(a, b, work, indirect=True)
                            or graph.reaches(b, a, work, indirect=True)):
                        record(judgment, "cycle", work)
                    elif not distinct_meanings(a, b, work):
                        record(judgment, "ancestor_conflict", work)
                    elif not permits(work, merge=(a, b)):
                        record(judgment, "neither_conflict", work)
                    else:
                        graph.combine(a, b, work)
                        record(judgment, "equivalent", work, accepted=True)
                else:
                    parent, child = (a, b) if relation == "a_parent_of_b" else (b, a)
                    if parent == child:
                        record(judgment, "equivalent_conflict", work)
                    elif graph.reaches(child, parent, work):
                        record(judgment, "cycle", work)
                    else:
                        permitted = permits(work, edge=(parent, child))
                        if not permitted and cross_pair_neither == "binding":
                            record(judgment, "neither_conflict", work)
                        else:
                            graph.add_edge(parent, child)
                            reason = "ancestor" if permitted else "ancestor_with_neither_conflict"
                            record(judgment, reason, work, accepted=True)
            except _BudgetExceeded:
                record(judgment, "work_budget", work)

    combined, member_to_group, final_edges = graph.snapshot()
    _dag(len(combined), final_edges)
    mapped_sp = sorted({(member_to_group[a], member_to_group[b]) for a, b in inputs["edges"]
                        if member_to_group[a] != member_to_group[b]})
    if not set(mapped_sp) <= set(final_edges):
        raise ValueError("combined hierarchy loses SP ancestry")
    result = deepcopy(hierarchy)
    result.update(experiment_id=EXPERIMENT_ID, groups=combined,
                  member_to_group=member_to_group,
                  edges=[list(edge) for edge in final_edges],
                  sp_edges=[list(edge) for edge in mapped_sp],
                  analysis="Bounded saved-comparison build. Fixed original SP meaning references; "
                           "all original subjects, masks and SP relationships retained. "
                           "Unresolved relationships are deferred, not repaired.")
    result.pop("browsing_edges", None)
    result.pop("ancestor_proposals", None)
    if freeze_membership:
        result["parent_replay_policy"] = dict(membership="fixed", cross_pair_neither=cross_pair_neither)
        result["analysis"] = ("Fixed-membership saved-parent replay. Original SP ancestry retained; "
                              f"cross-pair neither policy: {cross_pair_neither}. No new model calls.")
    identifiers = [f"S{group[0]:04d}" for group in combined]
    mapping = {f"S{member:04d}": identifiers[owner]
               for member, owner in enumerate(member_to_group)}
    nonroots = {b for _, b in final_edges}
    stats = dict(posts=len(inputs["posts"]), subjects=size, nodes=len(combined),
                 roots=len(combined) - len(nonroots),
                 nodes_combined=len(groups) - len(combined),
                 applied=len(applied), deferred=len(deferred),
                 edge_inspections=inspections, work_budget_per_proposal=work_budget,
                 sp_order_preserved=True, dag=True, inference_calls=0)
    return dict(results=result, mapping=mapping, applied=applied, deferred=deferred, stats=stats)


def audit_neither(application, judgments, *, work_budget=20000):
    """Retain every negative claim and report bounded final-graph witnesses.

    Repeated historical aliases share a graph check, not a new model judgment.
    An exhausted search is unresolved, never evidence of compatibility.
    """
    if not isinstance(work_budget, int) or isinstance(work_budget, bool) or work_budget < 0:
        raise ValueError("work_budget must be a nonnegative integer")
    result = application["results"]
    groups, owners = result["groups"], result["member_to_group"]
    graph = _Graph(groups, result["edges"])
    negatives = defaultdict(list)
    for index, judgment in enumerate(judgments):
        a, b, relation = _normalized(judgment, owners)
        if relation == "neither":
            negatives[a, b].append(index)
    contradictions, unresolved, compatible = [], [], 0
    identifiers = [f"S{group[0]:04d}" for group in groups]
    inspections = 0
    for (a, b), indices in sorted(negatives.items()):
        work = _Work(work_budget)
        row = dict(nodes=[identifiers[a], identifiers[b]], judgment_indices=indices)
        try:
            witness = graph.path(a, b, work)
            if witness is None:
                witness = graph.path(b, a, work)
            if witness is None:
                compatible += 1
            else:
                contradictions.append(dict(row, path=[identifiers[node] for node in witness],
                                           inspected=work.used))
        except _BudgetExceeded:
            unresolved.append(dict(row, reason="work_budget", inspected=work.used))
        inspections += work.used
    return dict(contradictions=contradictions, unresolved=unresolved,
                compatible_pairs=compatible, unique_negative_pairs=len(negatives),
                edge_inspections=inspections, work_budget_per_pair=work_budget)


def export_hierarchy(output, inputs, application, *, source, provenance=None):
    """Export through the existing browser schema with all original evidence.

    Full reachability and browsing reduction happen only at this export
    snapshot; they are not charged to per-proposal bounded graph searches.
    ``provenance`` retains caller-supplied baseline/model settings and receipts
    verbatim, without attributing historical teachers to the new model.
    """
    output, source = Path(output).resolve(), Path(source).resolve()
    if output.exists():
        raise ValueError("export output already exists")
    paths = [source / "masked-posts.json", source / "vector-map.json"]
    protected = {str(path): _sha256_file(path) for path in paths}
    posts = read(paths[0])
    vectors = read(paths[1])["vectors"]
    originals = {p["note_id"]: p["text"] for p in posts["notes"]}
    masks = {mask["vector_id"]: mask for mask in vectors}
    if len(originals) != len(posts["notes"]) or len(masks) != len(vectors):
        raise ValueError("duplicate source identity")
    if any(originals.get(p["note_id"]) != p["text"] for p in inputs["posts"]):
        raise ValueError("saved SP post differs from original source")
    selected = {}
    for subject in inputs["subjects"]:
        if not subject["mask_vector_ids"] and (subject["byte_spans"] or subject["fragments"]):
            raise ValueError("nonempty mask has no mask vector")
        for identifier in subject["mask_vector_ids"]:
            if identifier not in masks:
                raise ValueError("missing original mask")
            mask = masks[identifier]
            if any(subject[key] != mask[key] for key in
                   ("note_id", "note_short_id", "byte_spans", "fragments")):
                raise ValueError("mask provenance mismatch")
            raw = originals[subject["note_id"]].encode()
            if [raw[a:b].decode() for a, b in mask["byte_spans"]] != mask["fragments"]:
                raise ValueError("mask differs from original post")
            selected[identifier] = mask
    result = deepcopy(application["results"])
    groups, edges = result["groups"], result["edges"]
    _dag(len(groups), edges)
    closure = reachable(len(groups), edges)
    children = defaultdict(set)
    for a, b in edges:
        children[a].add(b)
    browsing = [edge for edge in edges
                if not any(c != edge[1] and (c, edge[1]) in closure for c in children[edge[0]])]
    if reachable(len(groups), browsing) != closure:
        raise ValueError("browsing reduction loses ancestry")
    result["browsing_edges"] = browsing
    categories = browser_spec(inputs, result, selected, protected[str(paths[0])])
    categories["hierarchy_id"] = EXPERIMENT_ID + " · bounded saved-comparison build"
    if "parent_replay_policy" in result:
        categories["hierarchy_id"] = (EXPERIMENT_ID + " · fixed-membership parent replay · "
                                      + result["parent_replay_policy"]["cross_pair_neither"])
    references = {f"S{group[0]:04d}": inputs["subjects"][group[0]]["subject"] for group in groups}
    for node in categories["nodes"]:
        if node["node_id"] in references:
            node["label"] = references[node["node_id"]]
    summary = dict(application["stats"], masks=len(selected),
                   comparisons=len(application["applied"]) + len(application["deferred"]),
                   underlying_links=len(edges), browsing_links=len(browsing),
                   browsing_links_omitted=len(edges) - len(browsing),
                   browsing_ancestry_preserved=True)
    evidence = dict(baseline=deepcopy(provenance), posts=deepcopy(inputs["posts"]),
                    subjects=deepcopy(inputs["subjects"]), original_edges=deepcopy(inputs["edges"]),
                    masks=list(selected.values()), protected_sha256=protected,
                    applied=deepcopy(application["applied"]), deferred=deepcopy(application["deferred"]),
                    mapping=deepcopy(application["mapping"]),
                    meaning_references={f"S{group[0]:04d}": group[0] for group in groups},
                    implementation_sha256={str(Path(__file__).resolve()): _sha256_file(Path(__file__))},
                    export=dict(source=str(source), output=str(output), inference_calls=0))
    for path, expected in protected.items():
        if _sha256_file(Path(path)) != expected:
            raise ValueError("source changed during export")
    bundle = dict(results=result, categories=categories, provenance=evidence, summary=summary)
    # A crash must never expose an incomplete final snapshot. Interrupted
    # staging directories remain inspectable, while the final name is atomic.
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.parent))
    for name, value in bundle.items():
        write(staging / f"{name}.json", value)
    binding = hashlib.sha256(_canonical_json_bytes(dict(application=application,
                                                        provenance=provenance))).hexdigest()
    write(staging / "manifest.json", dict(schema_version=1, snapshot_binding=binding,
          files={f"{name}.json": _sha256_file(staging / f"{name}.json") for name in bundle}))
    staging.rename(output)
    return bundle
