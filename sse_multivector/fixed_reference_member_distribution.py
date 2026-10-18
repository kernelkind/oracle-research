"""Experimental admission boundary from accepted members' support distribution.

The input scores already exclude each member's source note. Query scores and
group membership are unchanged. A strongest-first bend on log support separates
the stronger members from a weak tail; unavailable bends retain the minimum.
This hypothesis is not wired into hierarchy admission or a semantic guarantee.
"""
from collections import Counter
import math

import numpy as np


def derive_boundary(member_scores, member_notes):
    """Find the largest positive x-y bend, with equal total mass per note.

    No outsider, labels, trimming, mixture fit or global similarity threshold
    determines the result. Distinct score levels merge exact ties. The gap
    midpoint is geometric because the curve uses log support. The 1e-12
    tolerance suppresses numerical bends on straight curves, as in the existing
    reference-bend implementation. Missing or zero scores cannot supply a log.
    """
    scores = np.asarray(member_scores, dtype=float)
    if (scores.ndim != 1 or len(scores) != len(member_notes)
            or np.any(np.isinf(scores)) or np.any(scores < 0) or np.any(scores > 1)):
        raise ValueError('member scores must align with notes and lie in [0,1] or be missing')
    result = dict(status='no_group_reference', threshold=None, minimum=None,
                  selection=None, selected_level=None, curve=[])
    if not len(scores):
        return result
    counts = Counter(member_notes)
    if not np.isfinite(scores).all() or len(counts) < 2:
        result['status'] = 'no_cross_note_reference'
        return result
    if np.any(scores <= 0):
        result['status'] = 'nonpositive_member_support'
        return result
    result.update(status='boundary', threshold=float(scores.min()),
                  minimum=float(scores.min()), selection='minimum_insufficient_levels')
    levels = {}
    for score, note in zip(scores, member_notes):
        levels[float(score)] = levels.get(float(score), 0.) + 1 / counts[note]
    cumulative = 0.
    for score, mass in sorted(levels.items(), reverse=True):
        cumulative += mass
        result['curve'].append(dict(score=score, note_mass=mass,
                                    cumulative_note_mass=cumulative))
    curve = result['curve']
    if len(curve) < 3:
        return result
    first, last = curve[0], curve[-1]
    mass_span = last['cumulative_note_mass'] - first['cumulative_note_mass']
    log_first, log_last = math.log(first['score']), math.log(last['score'])
    if log_first == log_last:
        result['selection'] = 'minimum_no_positive_bend'
        return result
    for level in curve:
        x = (level['cumulative_note_mass'] - first['cumulative_note_mass']) / mass_span
        y = (log_first - math.log(level['score'])) / (log_first - log_last)
        level.update(x=x, y=y, deviation=x-y)
    selected = max(range(1, len(curve)-1), key=lambda i: curve[i]['deviation'])
    if curve[selected]['deviation'] <= 1e-12:
        result['selection'] = 'minimum_no_positive_bend'
        return result
    threshold = math.exp((math.log(curve[selected]['score'])
                          + math.log(curve[selected+1]['score'])) / 2)
    result.update(selection='member_bend', selected_level=selected,
                  threshold=threshold)
    return result
