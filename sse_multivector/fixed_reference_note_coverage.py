"""Experimental boundaries preserving reference-note routes across fixed groups.

Scores and memberships are unchanged. Each note needs one retained member
route, rather than every heading setting its group's admission standard. This
is reference self-consistency, not held-out accuracy or a hierarchy policy.
"""
from collections.abc import Mapping
from fractions import Fraction

import numpy as np


def derive_boundaries(member_scores, member_notes):
    """Tighten group minima using a common reference-only relative requirement.

    Within each group, take the best member score per source note and their
    median. Each note's best score/median ratio over its original groups defines
    a route; the least such ratio is the largest common requirement preserving
    all those notes. Multiply each group's median by that requirement and never
    lower its original minimum. Outsiders and semantic labels are not inputs.

    Scores must already exclude each member's entire source note. Unavailable
    groups stay unavailable; zero medians retain their original boundary without
    entering ratios. Exact rational comparisons and multiplication preserve
    limiting member ties without an epsilon or relaxed comparison. A threshold
    above one is retained, not clamped or used to remove a canonical group.
    """
    if (not isinstance(member_scores, Mapping) or not isinstance(member_notes, Mapping)
            or set(member_scores) != set(member_notes)
            or any(not isinstance(g, str) for g in member_scores)):
        raise ValueError('member score and note mappings must have matching group IDs')
    groups, best, best_groups = {}, {}, {}
    for group in sorted(member_scores):
        scores = np.asarray(member_scores[group], dtype=float)
        notes = list(member_notes[group])
        if (scores.ndim != 1 or len(scores) != len(notes)
                or np.any(np.isinf(scores)) or np.any(scores < 0) or np.any(scores > 1)
                or any(not isinstance(n, str) for n in notes)):
            raise ValueError('group scores must align with notes and lie in [0,1] or be missing')
        result = dict(status='no_group_reference', minimum=None, threshold=None,
                      median=None, note_scores={})
        groups[group] = result
        if not len(scores):
            continue
        if not np.isfinite(scores).all() or len(set(notes)) < 2:
            result['status'] = 'no_cross_note_reference'
            continue
        minimum = float(scores.min())
        by_note = {}
        for score, note in zip(scores, notes):
            by_note[note] = max(by_note.get(note, 0.), float(score))
        by_note = dict(sorted(by_note.items()))
        median = float(np.median(list(by_note.values())))
        result.update(status='nonpositive_median', minimum=minimum,
                      threshold=minimum, note_scores=by_note)
        if median <= 0:
            continue
        result.update(status='boundary', median=median)
        for note, score in by_note.items():
            ratio = Fraction(score) / Fraction(median)
            if note not in best or ratio > best[note]:
                best[note], best_groups[note] = ratio, [group]
            elif ratio == best[note]:
                best_groups[note].append(group)
    result = dict(status='no_scaled_groups', multiplier=None, multiplier_ratio=None,
                  limiting_notes=[], groups=groups, notes={})
    if not best:
        return result
    multiplier = min(best.values())
    try:
        result.update(status='boundary', multiplier=float(multiplier),
                      multiplier_ratio=[multiplier.numerator, multiplier.denominator],
                      limiting_notes=sorted(n for n, ratio in best.items() if ratio == multiplier))
        result['notes'] = {
            note: dict(relative_score=float(ratio), ratio=[ratio.numerator, ratio.denominator],
                       best_groups=best_groups[note]) for note, ratio in sorted(best.items())}
        for group in groups.values():
            if group['median'] is not None:
                group['threshold'] = float(max(Fraction(group['minimum']),
                                               multiplier * Fraction(group['median'])))
    except OverflowError as error:
        raise ValueError('derived relative score or threshold is not representable') from error
    return result
