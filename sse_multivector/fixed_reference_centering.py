"""Experimental centered cosine scores using an accepted-only reference bank.

One bank shared across roots supplies the mean, rather than each root removing
its own topic. Query vectors never enter the bank. Whole-source-note exclusion
also applies when calibrating existing members; directed scores are possible.
No memberships, semantic labels or admission thresholds enter this operation.
"""
import numpy as np


def _unit_rows(values):
    a = np.asarray(values, dtype=float)
    if a.ndim != 2 or not a.shape[1] or not np.isfinite(a).all():
        raise ValueError('vectors must be a finite two-dimensional matrix')
    norms = np.linalg.norm(a, axis=1, keepdims=True)
    if not np.isfinite(norms).all() or np.any(norms == 0):
        raise ValueError('vectors must have finite, nonzero norms')
    return a / norms


def centered_cosines(query_vectors, query_notes, reference_vectors,
                     centering_vectors, centering_notes):
    """Normalize, subtract the accepted-bank mean, renormalize and compare.

    For each query, exclude every bank entry from its source note before finding
    the mean. Subtract that same mean from both the query and its references.
    Group scoring must separately exclude same-note references. Empty banks or
    zero residual vectors are errors, with no fallback or numerical floor.

    Work is O(queries * references * dimensions), with an output score matrix
    and one centered reference matrix at a time, never a 3-D pair tensor.
    """
    queries = _unit_rows(query_vectors)
    references = _unit_rows(reference_vectors)
    bank = _unit_rows(centering_vectors)
    qnotes, bnotes = list(query_notes), list(centering_notes)
    if (len(qnotes) != len(queries) or len(bnotes) != len(bank)
            or any(not isinstance(n, str) for n in qnotes + bnotes)
            or not len(bank) or not len(references)
            or queries.shape[1] != references.shape[1]
            or queries.shape[1] != bank.shape[1]):
        raise ValueError('vectors and source notes must align with a nonempty bank')
    by_note = {}
    for i, note in enumerate(qnotes):
        by_note.setdefault(note, []).append(i)
    total = bank.sum(axis=0)
    bank_indices = {}
    for i, note in enumerate(bnotes):
        bank_indices.setdefault(note, []).append(i)
    scores = np.empty((len(queries), len(references)))
    for note, positions in by_note.items():
        excluded = bank_indices.get(note, [])
        count = len(bank) - len(excluded)
        if not count:
            raise ValueError('no accepted bank entries remain outside query note')
        mean = (total - bank[excluded].sum(axis=0)) / count
        q = _unit_rows(queries[positions] - mean)
        r = _unit_rows(references - mean)
        scores[positions] = np.clip(q @ r.T, -1., 1.)
    return scores
