"""Experimental boundaries from fixed group members, without curve fitting.

Use the weakest cross-note member mean as the group threshold. This is an
empirical positive-reference rule, not an accuracy or coverage guarantee.
Outsiders and nonmember references cannot determine the boundary. Not wired
into hierarchy admission.
"""
import numpy as np

from sse_multivector.fixed_reference_bend import mean_support


def derive_boundary(reference_affinities, reference_notes, group_indices, *, excluded_notes=()):
    """Return the minimum member support, excluding each member's whole note.

    All original memberships remain fixed. Excluded notes are removed from both
    scored members and their references. A group without cross-note support
    supplies no boundary. Record tied weakest members; no interpolation, trim,
    numerical margin, outsider score or neighboring group selects the cutoff.
    """
    a = np.asarray(reference_affinities, dtype=float)
    n = len(reference_notes)
    if a.shape != (n, n) or not np.allclose(a, a.T, rtol=0, atol=1e-12):
        raise ValueError('reference affinities must be square, aligned and symmetric')
    group = list(group_indices)
    excluded = set(excluded_notes)
    scores = mean_support(a, reference_notes, reference_notes, group, excluded_notes=excluded)
    group = [i for i in group if reference_notes[i] not in excluded]
    result = dict(status='no_group_reference' if not group else 'no_cross_note_reference',
                  threshold=None, group_indices=group, weakest_indices=[],
                  member_scores=[dict(index=i, score=float(scores[i]) if np.isfinite(scores[i]) else None)
                                 for i in group])
    if group and all(np.isfinite(scores[i]) for i in group):
        threshold = float(min(scores[i] for i in group))
        result.update(status='boundary', threshold=threshold,
                      weakest_indices=[i for i in group if scores[i] == threshold])
    return result
