"""Node-note ordering from direct title fit and child transfer. No inference.

A note directly in a node scores by how well it belongs in that node judged
from the node's title: the inverse-combined estimate per mask — prominence
times rescaled mask/title cosine plus missing meaning times rescaled
complement/title cosine — the maximum across the note's masks there. A note
arriving through a child node carries its recursively computed score through
the child-to-parent edge; shared descendants contribute through every route,
and the maximum route score is kept. Orderings list each note in the node's
complete subtree either by score alone or with direct members first, against
the plain prominence-times-mask-cosine product as baseline. The transfer
shapes, relevance sources and listing rules are candidates being compared,
not adopted rules.
"""

import math

try:
    from .prominence_ranking import ranking_scores
except ImportError:
    from prominence_ranking import ranking_scores


SHAPES = ('identity', 'multiply', 'cap')
LISTINGS = ('score', 'direct-first')
BASELINE = 'Product'


def note_scores(rows):
    """Aggregate validated mask rows to per-node note scores.

    Each row needs node_id, note_id, prominence, cosine and the saved inverse
    comparison (inverse_cosine and full_post_cosine). Returns
    {(node_id, note_id): {'prominence': int, 'score': float, 'product': float}}
    holding the maxima over the note's masks in that node: its inverse-combined
    score, its plain product baseline and its mask prominence.
    """
    result = {}
    for row in rows:
        for key in ('node_id', 'note_id'):
            if not isinstance(row.get(key), str) or not row[key]:
                raise ValueError(f'missing {key}')
        values = ranking_scores(row)
        if 'inverse_product' not in values:
            raise ValueError('inverse comparison required')
        prominence = row['prominence']
        entry = result.setdefault((row['node_id'], row['note_id']),
                                  {'prominence': prominence,
                                   'score': values['inverse_product'],
                                   'product': values['linear_product']})
        entry['prominence'] = max(entry['prominence'], prominence)
        entry['score'] = max(entry['score'], values['inverse_product'])
        entry['product'] = max(entry['product'], values['linear_product'])
    return result


def transfer(direct, relevance, shape):
    """Map a child's direct score (0..100) to the parent with relevance 0..1."""
    if shape not in SHAPES:
        raise ValueError('unknown transfer shape')
    if type(direct) not in (int, float) or not math.isfinite(direct) or not 0 <= direct <= 100:
        raise ValueError('invalid direct score')
    if shape == 'identity':
        return float(direct)
    if type(relevance) not in (int, float) or not math.isfinite(relevance) or not 0 <= relevance <= 1:
        raise ValueError('invalid relevance')
    if shape == 'multiply':
        return relevance * direct
    return min(float(direct), 100 * relevance)


def variant_scores(scores, parent, children, relevance, shape):
    """Per-note scores at the parent, including every descendant.

    `children` maps each hierarchy node to its direct children. `relevance`
    maps each parent-child edge to its relevance. A note's score is the
    maximum over its direct score and every transferred descendant route.
    """
    if shape not in SHAPES:
        raise ValueError('unknown transfer shape')
    children, _ = _validated(scores, parent, children, relevance)
    direct = {}
    for (node, note), entry in scores.items():
        direct.setdefault(node, {})[note] = float(entry['score'])
    memo = {}

    def scores_at(node):
        if node in memo:
            return memo[node]
        result = dict(direct.get(node, {}))
        for child in children[node]:
            edge_relevance = relevance[(node, child)]
            for note, child_score in scores_at(child).items():
                score = transfer(child_score, edge_relevance, shape)
                result[note] = max(result.get(note, score), score)
        memo[node] = result
        return result

    return scores_at(parent)


def orderings(scores, parent, children, relevance):
    """Named orderings of the parent's complete notes.

    `children` maps hierarchy nodes to their direct children. Returns
    {name: [note_id, ...]} for the subtree's notes: the plain-product baseline
    and each transfer shape under both listing rules. Scores tie-break by note
    ID only to make browsing deterministic; ties are genuine.
    """
    children, nodes = _validated(scores, parent, children, relevance)
    notes = _notes(scores, nodes)
    direct = {note for (node, note) in scores if node == parent}

    result = {BASELINE: sorted(
        notes, key=lambda note: (-_product(scores, note, nodes), note))}
    for shape in SHAPES:
        values = variant_scores(scores, parent, children, relevance, shape)
        for listing in LISTINGS:
            if listing == 'direct-first':
                key = lambda note: (0 if note in direct else 1, -values[note], note)
            else:
                key = lambda note: (-values[note], note)
            result[f'{shape} · {listing}'] = sorted(notes, key=key)
    return result


def _product(scores, note, nodes):
    """The note's baseline value: maximum product in the parent's subtree."""
    values = [entry['product'] for (node, entry_note), entry in scores.items()
              if node in nodes and entry_note == note]
    if not values:
        raise ValueError('note without scores')
    return max(values)


def _validated(scores, parent, children, relevance):
    if not isinstance(scores, dict) or not scores:
        raise ValueError('missing scores')
    if not isinstance(parent, str) or not parent:
        raise ValueError('missing parent')
    if not isinstance(children, dict) or not children:
        raise ValueError('missing hierarchy')
    graph = {}
    edges = set()
    for node, direct_children in children.items():
        if not isinstance(node, str) or not node:
            raise ValueError('invalid hierarchy node')
        if not isinstance(direct_children, (list, tuple)):
            raise ValueError('invalid children')
        if any(not isinstance(child, str) or not child for child in direct_children):
            raise ValueError('invalid child')
        if len(set(direct_children)) != len(direct_children) or node in direct_children:
            raise ValueError('invalid children')
        graph[node] = list(direct_children)
        edges.update((node, child) for child in direct_children)
    if parent not in graph:
        raise ValueError('unknown parent')
    if any(child not in graph for _, child in edges):
        raise ValueError('unknown child')

    for identity in scores:
        if (not isinstance(identity, tuple) or len(identity) != 2
                or any(not isinstance(value, str) or not value for value in identity)):
            raise ValueError('invalid score identity')
    unknown = {node for node, _ in scores} - set(graph)
    if unknown:
        raise ValueError(f'unknown node in scores: {sorted(unknown)}')
    if not isinstance(relevance, dict) or set(relevance) != edges:
        raise ValueError('relevance must cover exactly the hierarchy edges')
    for value in relevance.values():
        if (type(value) not in (int, float) or not math.isfinite(value)
                or not 0 <= value <= 1):
            raise ValueError('invalid relevance')

    state = {}

    def check_acyclic(node):
        if state.get(node) == 1:
            raise ValueError('hierarchy contains a cycle')
        if state.get(node) == 2:
            return
        state[node] = 1
        for child in graph[node]:
            check_acyclic(child)
        state[node] = 2

    for node in graph:
        check_acyclic(node)

    nodes = set()

    def collect(node):
        if node in nodes:
            return
        nodes.add(node)
        for child in graph[node]:
            collect(child)

    collect(parent)
    return graph, nodes


def _notes(scores, nodes):
    notes = {note for node, note in scores if node in nodes}
    if not notes:
        raise ValueError('no notes to order')
    return notes
