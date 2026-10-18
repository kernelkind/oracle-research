"""Experimental independent-query support from distinct accepted source notes.

Fixed reference memberships and affinities are supplied by the caller. Each
source note contributes its strongest match once. No outsiders change the
references, and no semantic labels or admission thresholds enter this score.
"""
import numpy as np


def note_support(affinities, query_notes, reference_notes, group_indices, *,
                 neighbors=None, excluded_notes=()):
    """Average best affinities per other note, optionally using the closest notes.

    Exclude the query's entire source note and all explicitly excluded notes.
    `neighbors=None` uses every available note; a positive integer requires
    exactly that many distinct notes. Insufficient support is NaN, never zero
    or an implicit fallback. Calibration and incoming queries must use the same
    setting. Input arrays and group memberships remain unchanged.
    """
    a = np.asarray(affinities, dtype=float)
    if a.ndim != 2 or a.shape != (len(query_notes), len(reference_notes)):
        raise ValueError('affinities must align with query and reference notes')
    if not np.all(np.isfinite(a)) or np.any(a < 0) or np.any(a > 1):
        raise ValueError('affinities must be finite and lie in [0,1]')
    if neighbors is not None and (type(neighbors) is not int or neighbors < 1):
        raise ValueError('neighbors must be a positive integer or None')
    group = list(group_indices)
    if len(set(group)) != len(group) or any(i < 0 or i >= a.shape[1] for i in group):
        raise ValueError('group indices must be distinct reference positions')
    excluded = set(excluded_notes)
    group = [i for i in group if reference_notes[i] not in excluded]
    scores = np.full(len(query_notes), np.nan)
    for j, note in enumerate(query_notes):
        by_note = {}
        for i in group:
            other = reference_notes[i]
            if other != note:
                by_note[other] = max(by_note.get(other, 0.), float(a[j, i]))
        nearest = sorted(by_note.values(), reverse=True)
        if nearest and (neighbors is None or len(nearest) >= neighbors):
            scores[j] = float(np.mean(nearest[:neighbors]))
    return scores
