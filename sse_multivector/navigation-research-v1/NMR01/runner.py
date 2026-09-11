"""Test membership against frozen examples in original SSE coordinates.

This is a diagnostic assignment heuristic, not a semantic confidence model.
No proposed member becomes an example during the same pass.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from geometric_experiment import load_input, write_json


def score_group(similarities, note_ids, anchor_rows):
    similarities = np.asarray(similarities, dtype=float)
    note_ids = np.asarray(note_ids)
    rows = sorted(set(anchor_rows))
    if similarities.shape != (len(note_ids), len(note_ids)):
        raise ValueError('similarities must cover the same rows as note IDs')
    if not rows or min(rows) < 0 or max(rows) >= len(note_ids):
        raise ValueError('anchor rows must identify existing vectors')
    notes = sorted(set(note_ids[rows]))
    scores = np.full((len(note_ids), len(notes)), np.nan)
    witnesses = np.full(scores.shape, -1, dtype=int)
    for j, note in enumerate(notes):
        members = np.array([r for r in rows if note_ids[r] == note])
        chosen = members[np.argmax(similarities[:, members], axis=1)]
        eligible = note_ids != note
        scores[eligible, j] = similarities[np.arange(len(note_ids)), chosen][eligible]
        witnesses[eligible, j] = chosen[eligible]
    count = np.sum(np.isfinite(scores), axis=1)
    mean = np.divide(np.nansum(scores, axis=1), count,
                     out=np.full(len(note_ids), np.nan), where=count > 0)
    second = np.full(len(note_ids), np.nan)
    if len(notes) >= 2:
        ordered = np.sort(np.nan_to_num(scores, nan=-np.inf), axis=1)
        second[count >= 2] = ordered[count >= 2, -2]
    return dict(mean=mean, second=second, support_count=count,
                note_scores=scores, witness_rows=witnesses, anchor_notes=notes)


def propose_members(similarities, note_ids, anchor_rows):
    rows = sorted(set(anchor_rows))
    scores = score_group(similarities, note_ids, rows)
    if len(scores['anchor_notes']) < 2:
        raise ValueError('membership requires at least two distinct anchor notes')
    # Each existing note contributes its best cross-note-supported mask, not
    # its worst fragment or its number of overlapping masks.
    calibration = {note: max(float(scores['mean'][r]) for r in rows
                             if note_ids[r] == note)
                   for note in scores['anchor_notes']}
    threshold = min(calibration.values())
    anchors = set(rows)
    proposed = [r for r in range(len(note_ids)) if r not in anchors
                and scores['support_count'][r] >= 2
                and scores['mean'][r] >= threshold]
    return dict(anchor_rows=rows, threshold=threshold, calibration=calibration,
                proposed_rows=proposed, calibrated_probability=False, scores=scores)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--hierarchy', type=Path, required=True)
    parser.add_argument('--groups', type=int, nargs='+', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output exists; preserve previous results')
    x, records, sources = load_input(args.data)
    note_sets = [{a['note_short_id'] for a in r['aliases']} for r in records]
    if any(len(s) != 1 for s in note_sets):
        raise ValueError('this diagnostic requires one source note per canonical row')
    note_ids = [next(iter(s)) for s in note_sets]
    tree_bytes = args.hierarchy.read_bytes()
    groups = {n['id']: n for n in json.loads(tree_bytes)['nodes']}
    if set(args.groups) - groups.keys():
        parser.error('unknown group ID')
    similarities = np.clip(x @ x.T, -1., 1.)
    results = []
    reviews = []
    for group_id in args.groups:
        result = propose_members(similarities, note_ids, groups[group_id]['members'])
        scores = result.pop('scores')
        anchors = set(result['anchor_rows'])
        anchor_notes = set(scores['anchor_notes'])
        ordered = sorted((r for r in range(len(x)) if r not in anchors),
                         key=lambda r: (-scores['mean'][r], r))
        ranked = []
        for r in ordered:
            witnesses = sorted([(float(s), int(w)) for s, w in zip(
                scores['note_scores'][r], scores['witness_rows'][r]) if w >= 0], reverse=True)
            ranked.append(dict(row=r, vector_id=records[r]['aliases'][0]['short_id'],
                               note_id=note_ids[r], mean=float(scores['mean'][r]),
                               second=float(scores['second'][r]) if np.isfinite(scores['second'][r]) else None,
                               new_note=note_ids[r] not in anchor_notes,
                               witnesses=[dict(cosine=s, row=w) for s, w in witnesses]))
        new = [r for r in result['proposed_rows'] if note_ids[r] not in anchor_notes]
        result.update(group_id=group_id, anchor_notes=sorted(anchor_notes), ranked=ranked,
                      proposed_new_notes=sorted({note_ids[r] for r in new}))
        results.append(result)
        # Every proposal is inspectable, including extra masks from known notes.
        # Top-ranked non-proposals are also shown so omissions remain visible.
        review_rows = sorted(set(result['proposed_rows']) | set(ordered[:12]))
        reviews.append(dict(group_id=group_id,
                            anchors=[records[r] for r in result['anchor_rows']],
                            candidates=[dict(evidence=records[r], proposed=r in result['proposed_rows'])
                                        for r in review_rows]))
        print(json.dumps({k: result[k] for k in ('group_id', 'threshold', 'anchor_notes',
                                               'proposed_new_notes')}, ensure_ascii=False))
    args.output.mkdir(parents=True)
    write_json(args.output/'results.json', results)
    write_json(args.output/'review.json', reviews)
    write_json(args.output/'configuration.json', dict(
        method='note-balanced mean nearest-example cosine', groups=args.groups,
        threshold='minimum best-per-note leave-own-note-out score',
        minimum_support_notes=2, one_pass_frozen_examples=True,
        calibrated_probability=False, sources=sources,
        hierarchy=dict(path=str(args.hierarchy.resolve()), sha256=hashlib.sha256(tree_bytes).hexdigest()),
        code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))


if __name__ == '__main__':
    main()
