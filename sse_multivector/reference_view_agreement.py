"""Describe agreement inside fixed accepted groups; no admission decisions.

The primary diagnostic is median title cosine minus median meaning cosine.
Only pairs from different source notes contribute. A large positive gap means
the title vectors agree more strongly than the complete-meaning vectors; it
does not establish that a group is semantically wrong or should be disabled.
"""
import numpy as np


def summarize(title_vectors, meaning_vectors, note_ids):
    """Normalize aligned views and summarize cross-note pairs of one group."""
    title = np.asarray(title_vectors, dtype=float)
    meaning = np.asarray(meaning_vectors, dtype=float)
    notes = list(note_ids)
    if (title.ndim != 2 or title.shape != meaning.shape or title.shape[1] < 1
            or len(title) != len(notes) or any(not isinstance(n, str) for n in notes)
            or not np.isfinite(title).all() or not np.isfinite(meaning).all()):
        raise ValueError('aligned finite title/meaning vectors and source notes are required')
    title_norm = np.linalg.norm(title, axis=1, keepdims=True)
    meaning_norm = np.linalg.norm(meaning, axis=1, keepdims=True)
    if np.any(title_norm == 0) or np.any(meaning_norm == 0):
        raise ValueError('title/meaning vectors must be nonzero')
    left, right = np.triu_indices(len(notes), 1)
    cross_note = np.asarray([notes[a] != notes[b] for a, b in zip(left, right)], dtype=bool)
    left, right = left[cross_note], right[cross_note]
    result = dict(entries=len(notes), notes=len(set(notes)), cross_note_pairs=len(left),
                  title_median_cosine=None, meaning_median_cosine=None, median_cosine_gap=None)
    if len(left):
        title, meaning = title / title_norm, meaning / meaning_norm
        tc = np.clip((title @ title.T)[left, right], -1., 1.)
        mc = np.clip((meaning @ meaning.T)[left, right], -1., 1.)
        tm, mm = float(np.median(tc)), float(np.median(mc))
        result.update(title_median_cosine=tm, meaning_median_cosine=mm, median_cosine_gap=tm-mm)
    return result
