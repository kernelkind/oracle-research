"""Deterministic edge-only policies for the saved weighted cross-note graph."""

import math
from numbers import Real


POLICIES = {
    'original': 'Retain every existing edge and weight in its original order.',
    'mutual_best_per_note': (
        'Retain an existing edge only when each endpoint is the other endpoint\'s '
        'highest-weight existing neighbor from that source note. Do not refill.'),
    'strongest_edges_matched': (
        'Retain the globally highest-weight existing edges, with their count equal '
        'to mutual_best_per_note on the same original graph. Do not refill.'),
}


def apply_graph_policy(graph, source_sets, policy):
    """Return a new igraph graph and JSON-safe audit without changing vertex IDs.

    Each vertex must have exactly one source note. Edge indices in the audit
    refer to the input graph; retained edges keep their original order and
    attributes. All vertices, including isolates, are preserved.
    """
    if policy not in POLICIES:
        raise ValueError(f'unknown graph policy: {policy}')
    if graph.is_directed() or not graph.is_simple():
        raise ValueError('graph policies require a simple undirected graph')
    if len(source_sets) != graph.vcount():
        raise ValueError('source-set count must match the graph vertex count')
    notes = []
    for sources in source_sets:
        if isinstance(sources, str) or len(sources) != 1:
            raise ValueError('each vertex must have exactly one source note')
        note = next(iter(sources))
        if not isinstance(note, str) or not note:
            raise ValueError('source note IDs must be nonempty strings')
        notes.append(note)
    if 'weight' not in graph.es.attributes():
        raise ValueError('graph edges require explicit weights')
    edges, weights = graph.get_edgelist(), list(graph.es['weight'])
    best = [{} for _ in notes]
    for (a, b), weight in zip(edges, weights):
        if (not isinstance(weight, Real) or isinstance(weight, bool)
                or not math.isfinite(weight) or weight <= 0):
            raise ValueError('graph edges require positive finite numeric weights')
        if notes[a] == notes[b]:
            raise ValueError('graph policies require cross-note edges')
        for vertex, neighbor in ((a, b), (b, a)):
            source = notes[neighbor]
            rank = (-weight, neighbor)
            if source not in best[vertex] or rank < best[vertex][source]:
                best[vertex][source] = rank
    mutual = [i for i, (a, b) in enumerate(edges)
              if best[a][notes[b]][1] == b and best[b][notes[a]][1] == a]
    if policy == 'original':
        retained = list(range(len(edges)))
    elif policy == 'mutual_best_per_note':
        retained = mutual
    else:
        ranked = sorted(range(len(edges)),
                        key=lambda i: (-weights[i], *sorted(edges[i])))
        retained = sorted(ranked[:len(mutual)])
    retained_set = set(retained)
    removed = [i for i in range(len(edges)) if i not in retained_set]
    result = graph.copy()
    result.delete_edges(removed)
    degrees = result.degree()
    isolated = [i for i, degree in enumerate(degrees) if degree == 0]
    nonisolated_notes = sorted({notes[i] for i, degree in enumerate(degrees) if degree})
    audit = {
        'policy': policy,
        'definition': POLICIES[policy],
        'tie_break': {
            'mutual_best_per_note': 'Equal weight: lower canonical neighbor vertex index.',
            'strongest_edges_matched': 'Equal weight: lower ordered endpoint pair (a, b).',
            'output_edge_order': 'Original edge index; vertices are never renumbered.',
        },
        'vertex_count': graph.vcount(),
        'original_edge_count': len(edges),
        'retained_edge_count': len(retained),
        'removed_edge_count': len(removed),
        'mutual_best_edge_count': len(mutual),
        'isolated_vector_ids': isolated,
        'isolated_vector_count': len(isolated),
        'nonisolated_vector_count': graph.vcount() - len(isolated),
        'distinct_note_count': len(set(notes)),
        'nonisolated_note_ids': nonisolated_notes,
        'nonisolated_note_count': len(nonisolated_notes),
        'retained_original_edge_indices': retained,
        'removed_original_edge_indices': removed,
    }
    return result, audit
