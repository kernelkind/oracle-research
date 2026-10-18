"""Experimental local angular affinities for fixed-reference admission.

Uses the local Gaussian form from similarity_network_fusion, with distinct
source-note neighbors and self-weight normalization into [0,1]. It is not the
unchanged fusion algorithm. No outsider changes a reference scale or graph.
These functions do not choose thresholds or activate a hierarchy policy.
"""
import math
import numpy as np


def _angles(cosines):
    values = np.asarray(cosines, dtype=float)
    if (values.ndim != 2 or not np.all(np.isfinite(values))
            or np.any(values < -1) or np.any(values > 1)):
        raise ValueError('cosines must be a finite matrix in [-1,1]')
    return np.arccos(values)


def neighbor_scales(cosines, query_notes, reference_notes, *, neighbors=20):
    """Mean angular distance to nearest distinct other source notes.

    Each note contributes its closest entry only. Queries see fixed references,
    never one another. NaN means no other-note reference; an exactly zero mean
    uses the existing fusion machine-epsilon floor, not a semantic distance.
    """
    angles = _angles(cosines)
    if (angles.shape != (len(query_notes), len(reference_notes))
            or type(neighbors) is not int or neighbors < 1
            or any(not isinstance(n, str) for n in (*query_notes, *reference_notes))):
        raise ValueError('notes must align with cosines and neighbors must be positive')
    result = np.full(len(query_notes), np.nan)
    for i, note in enumerate(query_notes):
        by_note = {}
        for distance, reference_note in zip(angles[i], reference_notes):
            if reference_note != note:
                by_note[reference_note] = min(by_note.get(reference_note, math.inf), float(distance))
        nearest = sorted(by_note.values())[:neighbors]
        if nearest:
            result[i] = max(float(np.mean(nearest)), np.finfo(float).eps)
    return result


def affinities(cosines, query_scales, reference_scales, *, sigma=.5):
    """Self-normalized local Gaussian, preserving the existing [0,1] contract.

    For d=acos(cosine), s=sigma*(rho_q+rho_r+d)/3 and
    a=2*sqrt(rho_q*rho_r)/(rho_q+rho_r+d)*exp(-0.5*(d/s)^2).
    This divides the existing Gaussian weights by their geometric self weights.
    Both scales must be available; do not turn absent references into matches.
    """
    angles = _angles(cosines)
    q, r = np.asarray(query_scales, dtype=float), np.asarray(reference_scales, dtype=float)
    if (q.shape != (angles.shape[0],) or r.shape != (angles.shape[1],)
            or not np.all(np.isfinite(q)) or not np.all(np.isfinite(r))
            or np.any(q <= 0) or np.any(r <= 0) or np.any(q > math.pi) or np.any(r > math.pi)
            or not np.isfinite(sigma) or sigma <= 0):
        raise ValueError('need aligned positive angular scales and positive sigma')
    total = q[:, None] + r[None, :] + angles
    scale = sigma * total / 3
    if not np.all(np.isfinite(scale)) or np.any(scale <= 0):
        raise ValueError('local Gaussian scale is not representable')
    normalization = 2 * np.sqrt(q[:, None] * r[None, :]) / total
    with np.errstate(over='ignore', under='ignore'):
        result = normalization * np.exp(-.5 * (angles / scale)**2)
    return np.clip(result, 0, 1)
