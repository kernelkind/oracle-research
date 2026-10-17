"""Experimental admission boundaries derived only from accepted references.

Fusion supplies fixed groups; these functions neither construct nor change them.
Callers supply meaning-kernel affinities, not fusion weights. A source note gets
equal total mass in each reference curve. Outsiders never determine a curve.
The primary bend is x-y (a high-support plateau before a fall). The opposite
orientation is an explicit diagnostic, not an automatic fallback.

Recovering held-out group members is a self-consistency check, not a semantic
accuracy guarantee. Missing bends and failed checks leave expansion unavailable.
"""
from collections import Counter
import math

import numpy as np


def mean_support(affinities, query_notes, reference_notes, group_indices, *, excluded_notes=()):
    """Mean group affinity per independent query, excluding its whole source note.

    NaN denotes no available reference. No input is changed. Arrays contain
    finite affinities in [0,1]; their construction is the caller's responsibility.
    """
    a = np.asarray(affinities, dtype=float)
    if a.ndim != 2 or a.shape != (len(query_notes), len(reference_notes)):
        raise ValueError('affinities must align with query and reference notes')
    if not np.all(np.isfinite(a)) or np.any(a < 0) or np.any(a > 1):
        raise ValueError('affinities must be finite and lie in [0,1]')
    group = list(group_indices)
    if len(set(group)) != len(group) or any(i < 0 or i >= a.shape[1] for i in group):
        raise ValueError('group indices must be distinct reference positions')
    excluded = set(excluded_notes)
    group = [i for i in group if reference_notes[i] not in excluded]
    scores = np.full(len(query_notes), np.nan)
    for j, note in enumerate(query_notes):
        available = [i for i in group if reference_notes[i] != note]
        if available:
            scores[j] = float(np.mean(a[j, available]))
    return scores


def derive_boundary(reference_affinities, reference_notes, group_indices, *,
                    excluded_notes=(), orientation='x_minus_y', anchor=None):
    """Fit the strongest central-80% bend in a reference-only support curve.

    Equal scores share a level; trim ceil(10% of distinct levels) from each end.
    Normalize cumulative note mass and support drop over the retained endpoints.
    The boundary is midway between the selected score and the next lower score.
    The 1e-12 tolerance only suppresses floating-point bends on straight curves.

    With anchor='members', replace the upper trim by the weakest available
    member's cross-note support. Keep that point as the fitted upper endpoint;
    retain the original lower trim. Recompute the anchor after note exclusions.
    A member without cross-note support makes this anchored fit unavailable.
    """
    a = np.asarray(reference_affinities, dtype=float)
    if a.shape != (len(reference_notes), len(reference_notes)):
        raise ValueError('reference affinities must be square and align with notes')
    if not np.allclose(a, a.T, rtol=0, atol=1e-12):
        raise ValueError('reference affinities must be symmetric')
    if orientation not in ('x_minus_y', 'y_minus_x'):
        raise ValueError('unknown bend orientation')
    if anchor not in (None, 'members'):
        raise ValueError('unknown reference anchor')
    excluded = set(excluded_notes)
    scores = mean_support(a, reference_notes, reference_notes, group_indices,
                          excluded_notes=excluded)
    group = [i for i in group_indices if reference_notes[i] not in excluded]
    context = [i for i, note in enumerate(reference_notes)
               if note not in excluded and np.isfinite(scores[i])]
    result = dict(status='no_group_reference' if not group else 'insufficient_levels',
                  threshold=None, group_indices=group, context_indices=context,
                  orientation=orientation, curve=[])
    if not group or not context:
        return result
    counts = Counter(reference_notes[i] for i in context)
    levels = {}
    for i in context:
        level = levels.setdefault(float(scores[i]), dict(note_mass=0., indices=[]))
        level['note_mass'] += 1 / counts[reference_notes[i]]
        level['indices'].append(i)
    cumulative = 0.
    for score, level in sorted(levels.items(), reverse=True):
        cumulative += level['note_mass']
        result['curve'].append(dict(score=score, cumulative_note_mass=cumulative, **level))
    curve = result['curve']
    trim = math.ceil(.10 * len(curve))
    result['trim_levels_per_end'] = trim
    fit_start = trim
    if anchor == 'members':
        if not all(np.isfinite(scores[i]) for i in group):
            result['status'] = 'no_member_anchor'
            return result
        anchor_score = float(min(scores[i] for i in group))
        fit_start = next(i for i, level in enumerate(curve) if level['score']==anchor_score)
        result.update(anchor=anchor, anchor_score=anchor_score, anchor_level=fit_start,
                      fit_start_level=fit_start)
    retained = curve[fit_start:len(curve)-trim]
    if len(retained) < 3:
        return result
    first, last = retained[0], retained[-1]
    for level in retained:
        x = ((level['cumulative_note_mass'] - first['cumulative_note_mass']) /
             (last['cumulative_note_mass'] - first['cumulative_note_mass']))
        y = (first['score'] - level['score']) / (first['score'] - last['score'])
        deviation = x-y if orientation == 'x_minus_y' else y-x
        level.update(x=x, y=y, deviation=deviation)
    best = max(retained, key=lambda level: level['deviation'])
    if best['deviation'] <= 1e-12:
        result['status'] = 'no_positive_bend'
        return result
    selected = next(i for i, level in enumerate(curve) if level is best)
    result.update(status='boundary', threshold=(best['score'] + curve[selected+1]['score'])/2,
                  selected_level=selected, deviation=best['deviation'])
    return result


def qualify_boundary(reference_affinities, reference_notes, group_indices, *,
                     excluded_notes=(), orientation='x_minus_y', anchor=None):
    """Check fixed group members with their entire source note withheld.

    Each fold excludes the note from both reference context and group members;
    it keeps the originally selected fusion membership of all other entries.
    """
    excluded = set(excluded_notes)
    group = [i for i in group_indices if reference_notes[i] not in excluded]
    base = derive_boundary(reference_affinities, reference_notes, group,
                           excluded_notes=excluded, orientation=orientation, anchor=anchor)
    folds = []
    for note in sorted({reference_notes[i] for i in group}):
        boundary = derive_boundary(reference_affinities, reference_notes, group,
                                   excluded_notes=excluded | {note}, orientation=orientation,
                                   anchor=anchor)
        held = [i for i in group if reference_notes[i] == note]
        scores = mean_support(np.asarray(reference_affinities)[held], [note]*len(held),
                              reference_notes, group, excluded_notes=excluded | {note})
        threshold = boundary['threshold']
        failed = [i for i, score in zip(held, scores)
                  if threshold is None or not np.isfinite(score) or score < threshold]
        folds.append(dict(excluded_note=note, boundary=boundary, held_indices=held,
                          scores=[float(s) if np.isfinite(s) else None for s in scores],
                          failed_indices=failed))
    return dict(base=base, folds=folds,
                eligible=base['threshold'] is not None and bool(folds)
                and all(not fold['failed_indices'] for fold in folds))
