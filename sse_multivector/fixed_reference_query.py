"""Experimental title/meaning query support against fixed accepted connections.

For query affinities t and m and a symmetric accepted graph C, return
sqrt(t C m.T / sum(C)). Self-connections are excluded. Thus both query views
must match accepted entries joined by a fixed connection. No query is inserted
into the graph; no accepted vector, group, edge or weight is updated.

This is a proposed query score, not published SNF/Nystrom inference or a proved
admission rule. With sparse query rows containing at most k entries and accepted
degree at most k, the sparse product has at most Q*k*k entries for Q queries.
Finding the query affinities and setting a decision cutoff are separate tasks.
"""
import numpy as np
from scipy import sparse


def query_support(title_affinities, meaning_affinities, accepted_connections):
    """Return one score per independent query; NaN means no reference edges.

    Callers exclude forbidden source-note references before supplying affinities
    and connections. Same-view controls pass the same affinity matrix twice.
    The function preserves all input arrays and sparse matrices.
    """
    t=sparse.csr_matrix(title_affinities,dtype=float,copy=True)
    m=sparse.csr_matrix(meaning_affinities,dtype=float,copy=True)
    c=sparse.csr_matrix(accepted_connections,dtype=float,copy=True)
    for a in [t,m,c]:
        a.sum_duplicates()
        if not np.all(np.isfinite(a.data)) or np.any(a.data<0):
            raise ValueError('query affinities and connections must be finite and nonnegative')
    if (t.shape!=m.shape or c.shape!=(t.shape[1],t.shape[1])
            or np.any(t.data>1) or np.any(m.data>1)):
        raise ValueError('query affinities must align with accepted connections and lie in [0,1]')
    if (c-c.T).nnz:
        raise ValueError('accepted connections must be symmetric')
    c.setdiag(0)
    c.eliminate_zeros()
    mass=float(c.sum())
    if mass==0:
        return np.full(t.shape[0],np.nan)
    weighted=np.asarray((t@c).multiply(m).sum(axis=1)).ravel()
    return np.sqrt(weighted/mass)
