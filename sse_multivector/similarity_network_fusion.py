"""Experimental bounded-neighbor adaptation of Similarity Network Fusion.

This does not change hierarchy generation. The SNFtool exchange/normalization
equations are retained when no edge is pruned. Sparse local initialization and
mutual top-k pruning before/after each sandwich product are explicit adaptations,
not the published dense algorithm. Source: SNFtool R/SNF.R and affinityMatrix.R,
https://github.com/maxconway/SNFtool (Wang et al., Nature Methods, 2014).

Stored transition/state graphs have at most k off-diagonal entries per row and
column. Each of the two sparse products has at most n*(k+1)^2 entries before
pruning. No dense fusion-state matrix is allocated. Neighbor search here is exact
and chunked; it does not qualify approximate search for a production corpus.

The separate precomputed-distance HDBSCAN adapter is dense, as is the existing
small-reference native control. It is deliberately not a corpus-scale constructor.
"""
import warnings

import numpy as np
from scipy import sparse
from sklearn import config_context
from sklearn.neighbors import NearestNeighbors


def _top_rows(graph, neighbors):
    """Keep the strongest k non-self entries in each row, with stable ID ties."""
    graph = sparse.csr_matrix(graph, dtype=float)
    graph.sum_duplicates()
    graph.sort_indices()
    rows, columns, values = [], [], []
    for i in range(graph.shape[0]):
        a, z = graph.indptr[i:i+2]
        jj, vv = graph.indices[a:z], graph.data[a:z]
        off = jj != i
        order = np.lexsort((jj[off], -vv[off]))[:neighbors]
        selected = [(int(j), float(v)) for j, v in zip(jj[off][order], vv[off][order]) if v > 0]
        selected.extend((int(j), float(v)) for j, v in zip(jj[~off], vv[~off]) if v > 0)
        rows.extend([i] * len(selected))
        columns.extend(j for j, _ in selected)
        values.extend(v for _, v in selected)
    out = sparse.csr_matrix((values, (rows, columns)), shape=graph.shape)
    out.sort_indices()
    return out


def _mutual(graph, neighbors):
    graph = sparse.csr_matrix((graph + graph.T) * .5)
    selected = _top_rows(graph, neighbors)
    support = selected.copy()
    support.data[:] = 1
    out = graph.multiply(support.multiply(support.T)).tocsr()
    out.eliminate_zeros()
    out.sort_indices()
    return out


def _row_normalize(graph):
    sums = np.asarray(graph.sum(axis=1)).ravel()
    if np.any(sums <= 0):
        raise ValueError('every fusion row needs positive mass')
    return (sparse.diags(1 / sums) @ graph).tocsr()


def local_graph(vectors, *, neighbors=20, sigma=.5):
    """Locally scaled angular affinities, restricted to mutual nearest neighbors."""
    x = np.asarray(vectors, dtype=float)
    if (x.ndim != 2 or len(x) < 2 or x.shape[1] < 1 or not np.all(np.isfinite(x))
            or np.any(np.linalg.norm(x, axis=1) == 0)
            or type(neighbors) is not int or neighbors < 1
            or not np.isfinite(sigma) or sigma <= 0):
        raise ValueError('invalid vectors or neighborhood controls')
    x = x / np.linalg.norm(x, axis=1, keepdims=True)
    k = min(neighbors, len(x)-1)
    with config_context(working_memory=128):
        distances, indices = NearestNeighbors(n_neighbors=k+1, algorithm='brute',
                                              metric='euclidean', n_jobs=1).fit(x).kneighbors(x)
    rows, columns, angular = [], [], []
    rho = np.empty(len(x))
    for i, (dd, jj) in enumerate(zip(distances, indices)):
        other = jj != i
        jj, dd = jj[other][:k], dd[other][:k]
        aa = 2 * np.arcsin(np.clip(dd / 2, 0, 1))
        rho[i] = max(float(aa.mean()), np.finfo(float).eps)
        rows.extend([i] * len(jj))
        columns.extend(jj)
        angular.extend(aa)
    rows, columns, angular = np.asarray(rows), np.asarray(columns), np.asarray(angular)
    scale = sigma * np.maximum((rho[rows] + rho[columns] + angular) / 3, np.finfo(float).eps)
    values = np.exp(-.5 * (angular / scale)**2) / scale
    graph = sparse.csr_matrix((values, (rows, columns)), shape=(len(x), len(x)))
    support = graph.copy()
    support.data[:] = 1
    graph = ((graph + graph.T) * .5).multiply(support.multiply(support.T)).tocsr()
    diagonal_scale = sigma * np.maximum(2 * rho / 3, np.finfo(float).eps)
    graph.setdiag(1 / diagonal_scale)
    graph.sort_indices()
    return graph


def fuse(graphs, *, neighbors=20, iterations=20, exchange=True):
    """Fuse two sparse affinity networks; exchange=False is self-diffusion control."""
    if (len(graphs) != 2 or type(neighbors) is not int or neighbors < 1
            or type(iterations) is not int or iterations < 0):
        raise ValueError('fusion requires two graphs and valid controls')
    shape = graphs[0].shape
    if len(shape) != 2 or shape[0] != shape[1] or any(g.shape != shape for g in graphs):
        raise ValueError('fusion inputs must be aligned square matrices')
    states = []
    for graph in graphs:
        graph = sparse.csr_matrix(graph, dtype=float)
        if np.any(graph.data < 0) or not np.all(np.isfinite(graph.data)):
            raise ValueError('fusion requires finite nonnegative affinities')
        graph = _mutual(graph, neighbors)
        graph = _row_normalize(graph)
        states.append(((graph + graph.T) * .5).tocsr())
    transitions = [_row_normalize(g) for g in states]
    trace = [{'iteration': 0, 'state_nnz': [g.nnz for g in states],
              'largest_product_nnz': 0}]
    identity = sparse.eye(shape[0], format='csr')
    for step in range(iterations):
        following, products = [], []
        for j, transition in enumerate(transitions):
            other = states[1-j if exchange else j]
            left = (transition @ other).tocsr()
            products.append(left.nnz)
            left = _top_rows(left, neighbors)
            result = (left @ transition.T).tocsr()
            products.append(result.nnz)
            result = _mutual(result + identity, neighbors)
            following.append(result)
        states = following
        trace.append({'iteration': step+1, 'state_nnz': [g.nnz for g in states],
                      'largest_product_nnz': max(products)})
    result = _row_normalize((states[0] + states[1]) * .5)
    result = (result + result.T + identity) * .5
    result = _mutual(result, neighbors)
    return result, trace


def cluster(affinity, *, min_samples=3, min_cluster_size=2):
    """EOM over reciprocal fused-edge weights; absent edges remain infinite.

    min_samples follows this repository's convention including the point itself.
    Dense conversion is confined to this small-reference clustering adapter.
    Warnings about disconnected/insufficient-neighbor distances are retained.
    """
    from sklearn.cluster import HDBSCAN
    graph = sparse.coo_matrix(affinity)
    n = graph.shape[0]
    if (graph.shape != (n, n) or min_samples < 2 or min_cluster_size < 2
            or np.any(graph.data <= 0) or not np.all(np.isfinite(graph.data))):
        raise ValueError('invalid clustering affinities or controls')
    if (graph.tocsr()-graph.T.tocsr()).nnz:
        raise ValueError('clustering affinities must be symmetric')
    distances = np.full((n, n), np.inf, dtype=float)
    distances[graph.row, graph.col] = 1 / graph.data
    np.fill_diagonal(distances, 0)
    if n < min_samples or not np.any(np.isfinite(distances[~np.eye(n, dtype=bool)])):
        return [], list(range(n)), []
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        labels = HDBSCAN(metric='precomputed', algorithm='brute', copy=True,
                         min_samples=min_samples,
                         min_cluster_size=min_cluster_size,
                         cluster_selection_method='eom',
                         allow_single_cluster=False).fit_predict(distances)
    groups = sorted([sorted(np.flatnonzero(labels == label).tolist()) for label in set(labels) if label >= 0])
    return groups, np.flatnonzero(labels < 0).tolist(), [str(w.message) for w in caught]
