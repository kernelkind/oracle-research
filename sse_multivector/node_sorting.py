"""Node-note ordering from direct title fit and child transfer. No inference.

A note directly in a node scores by how well it belongs in that node judged
from the node's title: prominence times rescaled title cosine per mask, the
maximum across the note's masks there. A note arriving through a child node
carries its direct score there through a transfer with the child's relevance to
the current node; the note's score at the parent is the maximum over all its
routes. Orderings list the parent's complete notes either by score alone or
with direct members first. The transfer shapes, relevance sources and listing
rules are candidates being compared, not adopted rules.
"""

import math

try:
    from .prominence_ranking import cosine_weight
except ImportError:
    from prominence_ranking import cosine_weight


SHAPES = ('identity', 'multiply', 'cap')
LISTINGS = ('score', 'direct-first')


def note_scores(rows):
    """Aggregate validated mask rows to per-node note scores.

    Each row needs node_id, note_id, prominence and cosine. Returns
    {(node_id, note_id): {'prominence': int, 'score': float}} holding the
    maximum mask prominence and maximum mask score for that note in that node.
    """
    result = {}
    for row in rows:
        for key in ('node_id', 'note_id'):
            if not isinstance(row.get(key), str) or not row[key]:
                raise ValueError(f'missing {key}')
        prominence = row.get('prominence')
        if type(prominence) is not int or not 0 <= prominence <= 100:
            raise ValueError('invalid prominence')
        score = prominence * cosine_weight(row.get('cosine'))
        entry = result.setdefault((row['node_id'], row['note_id']),
                                  {'prominence': prominence, 'score': score})
        entry['prominence'] = max(entry['prominence'], prominence)
        entry['score'] = max(entry['score'], score)
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
    """Per-note scores at the parent under one transfer shape.

    `scores` comes from note_scores and must cover the parent and every child.
    A note's score is the maximum over its direct score at the parent (when it
    is a direct member) and its transferred score through each child.
    """
    if shape not in SHAPES:
        raise ValueError('unknown transfer shape')
    children = _validated(scores, parent, children, relevance)
    result = {}
    for note in _notes(scores, parent, children):
        values = []
        entry = scores.get((parent, note))
        if entry is not None:
            values.append(float(entry['score']))
        for child in children:
            child_entry = scores.get((child, note))
            if child_entry is not None:
                values.append(transfer(child_entry['score'], relevance[child], shape))
        if not values:
            raise ValueError('note without scores')
        result[note] = max(values)
    return result


def orderings(scores, parent, children, relevance):
    """Named orderings of the parent's complete notes.

    Returns {name: [note_id, ...]}: the maximum own-node-prominence baseline
    and each transfer shape under both listing rules. Scores tie-break by note
    ID only to make browsing deterministic; ties are genuine.
    """
    children = _validated(scores, parent, children, relevance)
    notes = _notes(scores, parent, children)
    direct = {note for (node, note) in scores if node == parent}

    def baseline(note):
        return max(entry['prominence'] for (node, entry_note), entry in scores.items()
                   if entry_note == note)

    result = {'Prominence': sorted(notes, key=lambda note: (-baseline(note), note))}
    for shape in SHAPES:
        values = variant_scores(scores, parent, children, relevance, shape)
        for listing in LISTINGS:
            if listing == 'direct-first':
                key = lambda note: (0 if note in direct else 1, -values[note], note)
            else:
                key = lambda note: (-values[note], note)
            result[f'{shape} · {listing}'] = sorted(notes, key=key)
    return result


def _validated(scores, parent, children, relevance):
    if not isinstance(scores, dict) or not scores:
        raise ValueError('missing scores')
    if not isinstance(parent, str) or not parent:
        raise ValueError('missing parent')
    children = list(children)
    if len(set(children)) != len(children) or parent in children:
        raise ValueError('invalid children')
    for node, note in scores:
        if not isinstance(node, str) or not node or not isinstance(note, str) or not note:
            raise ValueError('invalid score identity')
    unknown = {node for node, _ in scores} - {parent, *children}
    if unknown:
        raise ValueError(f'unknown node in scores: {sorted(unknown)}')
    if not isinstance(relevance, dict) or set(relevance) != set(children):
        raise ValueError('relevance must cover exactly the children')
    return children


def _notes(scores, parent, children):
    notes = {note for node, note in scores if node == parent or node in set(children)}
    if not notes:
        raise ValueError('no notes to order')
    return notes
