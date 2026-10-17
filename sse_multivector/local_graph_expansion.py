"""Experimental seeded graph expansion; not wired into hierarchy admission.

Personalized PageRank orders a fixed weighted graph. A conductance sweep keeps
the supplied seed set and selects a boundary from the graph, without a semantic
score cutoff. This seed-preserving sweep is an adaptation, not a claim to inherit
the guarantees of the single-seed ACL algorithm. References:
https://cs.stanford.edu/people/jure/pubs/mappr-kdd17.pdf

Storage is sparse O(vertices + edges). Each PageRank iteration and sweep is
O(vertices + edges); sorting costs O(vertices log vertices). Neighbor retrieval
and graph construction are deliberately separate from this calculation.
"""
import numpy as np
from scipy import sparse


def expand(graph, seeds, *, continuation=.85, tolerance=1e-12):
    """Return the seed-preserving minimum-conductance sweep and its evidence.

    ``seeds`` maps vertex IDs to nonnegative starting weights. The input graph
    and seeds are never mutated. Self edges are ignored. Only boundaries with
    at most half the total graph volume are eligible, as in a local sweep. A
    minimum caused solely by that search limit, without a local valley, remains
    unresolved and proposes no additions. A disconnected zero-cut set is valid.
    The complete curve and an earliest-local-minimum control are retained.
    """
    g = sparse.csr_matrix(graph, dtype=float, copy=True)
    n = g.shape[0]
    if (g.shape != (n, n) or not n or not seeds
            or np.any(g.data < 0) or not np.all(np.isfinite(g.data))
            or (g - g.T).nnz or not 0 < continuation < 1
            or not 0 < tolerance < 1
            or any(type(i) is not int or not 0 <= i < n
                   or not np.isfinite(w) or w <= 0 for i, w in seeds.items())):
        raise ValueError('finite symmetric nonnegative graph and positive seeds required')
    g.setdiag(0)
    g.eliminate_zeros()
    g.sort_indices()
    degree = np.asarray(g.sum(axis=1)).ravel()
    total = float(degree.sum())
    seed_ids = sorted(seeds)
    start = np.zeros(n)
    start[seed_ids] = [seeds[i] for i in seed_ids]
    start /= start.sum()
    p = start.copy()
    inverse = np.divide(1., degree, out=np.zeros(n), where=degree > 0)
    for iterations in range(1, 10001):
        following = ((1 - continuation) * start + continuation *
                     (g.T @ (p * inverse) + p[degree == 0].sum() * start))
        residual = float(np.abs(following - p).sum())
        p = following
        if residual <= tolerance:
            break
    else:
        raise ArithmeticError('PageRank did not converge')
    scores = p * inverse
    seed_set = set(seed_ids)
    order = [int(i) for i in np.lexsort((np.arange(n), -scores))
             if scores[i] > 0 and i not in seed_set]
    inside = np.zeros(n, dtype=bool)
    inside[seed_ids] = True
    volume = float(degree[seed_ids].sum())
    cut = volume - float(g[seed_ids, :][:, seed_ids].sum())
    curve = []

    def record(added):
        denominator = min(volume, total - volume)
        phi = max(0., cut) / denominator if denominator > tolerance * max(total, 1) else None
        curve.append(dict(added=added, size=len(seed_ids) + added,
                          volume=volume, cut=max(0., cut), conductance=phi,
                          eligible=bool(phi is not None and volume <= total / 2 + tolerance * max(total, 1))))

    record(0)
    for added, i in enumerate(order, 1):
        a, z = g.indptr[i:i+2]
        cut += float(degree[i] - 2 * g.data[a:z][inside[g.indices[a:z]]].sum())
        volume += float(degree[i])
        inside[i] = True
        record(added)
    eligible = [r for r in curve if r['eligible']]
    later_different = [None] * len(curve)
    next_valid = None
    for i in range(len(curve) - 1, -1, -1):
        if curve[i]['conductance'] is None:
            continue
        if next_valid is not None:
            later_different[i] = (next_valid if abs(curve[next_valid]['conductance'] - curve[i]['conductance']) > tolerance
                                  else later_different[next_valid])
        next_valid = i

    def is_valley(row):
        following_index = later_different[row['added']]
        later = curve[following_index] if following_index is not None else None
        previous = curve[row['added'] - 1] if row['added'] else None
        return (row['conductance'] <= tolerance or
                ((previous is None or previous['conductance'] is None
                  or row['conductance'] <= previous['conductance'] + tolerance)
                 and later is not None and later['conductance'] > row['conductance']))

    best = None
    for row in eligible:
        if best is None or row['conductance'] < best['conductance'] - tolerance:
            best = row
    first = next((r for r in eligible if is_valley(r)), None)
    if best is None:
        status, selected = 'no_edges', seed_ids
    elif not best['added']:
        status, selected = 'seed_only', seed_ids
    elif not is_valley(best):
        status, selected = 'no_resolved_minimum', seed_ids
    else:
        status, selected = 'selected', seed_ids + order[:best['added']]
    return dict(status=status, selected=selected, best=best,
                first_local=first, first_local_selected=seed_ids + order[:first['added']] if first else seed_ids,
                order=order, curve=curve, pagerank=p.tolist(),
                iterations=iterations, residual=residual)
