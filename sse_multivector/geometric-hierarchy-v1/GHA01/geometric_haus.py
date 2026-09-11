"""Direct-vector adaptation of HAUS's released recursive spectral core.

Reference: Rossetti & Pirri, NeurIPS 2024. Author implementation inspected at
deepplants/recursive-deep-spectral-clustering commit 37ee4d32a6698cc9d241ff0d77c97dbd9bdac608.
No overclustering, image coordinates, CRF, training, or semantic labels.
This baseline follows the *released code*: inherited affinities, first k
eigenvectors, binary threshold rounding, mean-cut stopping, and the Frobenius
perturbation check only for k>2. It is not the distinct appendix pseudocode.
Dense symmetric eigensolving replaces ARPACK; empty partitions are inadmissible.
"""
from __future__ import annotations

import numpy as np
from scipy.linalg import eigh
from sklearn.cluster import KMeans


def normalized_laplacian(a):
    degree = a.sum(axis=1)
    inv = 1 / np.sqrt(np.maximum(degree, 1e-12))
    return (np.diag(degree) - a) * inv[:, None] * inv[None, :]


def _cut_cost(a, labels):
    costs = []
    degree = a.sum(axis=1)
    for label in np.unique(labels):
        inside = labels == label
        costs.append(float(a[np.ix_(inside, ~inside)].sum() /
                           max(float(degree[inside].sum()), 1e-12)))
    return costs


def _partition(a, y, k, seed):
    if k > 2:
        z = y / np.maximum(np.linalg.norm(y, axis=1, keepdims=True), 1e-12)
        return KMeans(n_clusters=k, random_state=seed, n_init=10, tol=1e-6,
                      max_iter=600, algorithm='lloyd').fit_predict(z)
    f = y[:, 1]
    thresholds = np.r_[np.linspace(f.min(), f.max(), 10, endpoint=False), 0., f.mean()]
    best, score = None, np.inf
    for threshold in thresholds:
        labels = (f > threshold).astype(int)
        if len(np.unique(labels)) != 2:
            continue
        cost = np.mean(_cut_cost(a, labels))
        if cost < score:
            best, score = labels, cost
    return best


def fit_affinity(affinity, *, max_kways=10, max_depth=9, min_points=1,
                 mean_cut_threshold=.8, max_perturbation=80., seed=1234):
    a = np.asarray(affinity, dtype=np.float64)
    if (a.ndim != 2 or a.shape[0] != a.shape[1] or len(a) == 0 or
            not np.isfinite(a).all() or (a < 0).any() or
            not np.allclose(a, a.T, rtol=0, atol=1e-12)):
        raise ValueError('affinity must be a finite nonnegative symmetric square matrix')
    if max_kways < 3 or max_depth < 0 or min_points < 1:
        raise ValueError('max_kways>=3, max_depth>=0, min_points>=1 required')
    if not (0 < mean_cut_threshold <= 1) or max_perturbation < 0:
        raise ValueError('invalid cut or perturbation threshold')
    a = (a + a.T) / 2
    np.fill_diagonal(a, 0)
    nodes = []

    def visit(members, parent, depth):
        node_id = len(nodes)
        node = dict(id=node_id, parent=parent, children=[], members=members.tolist(),
                    depth=depth, diagnostic={})
        nodes.append(node)
        d = node['diagnostic']
        if len(members) <= min_points or depth >= max_depth:
            d['stop'] = 'minimum_points' if len(members) <= min_points else 'depth_limit'
            return node_id
        sub = a[np.ix_(members, members)]
        off = sub[np.triu_indices(len(sub), 1)]
        if len(sub) < 3 or np.ptp(off) <= 1e-12:
            # Uniform positive affinities provide no supported distinction.
            d['stop'] = 'uniform_affinity' if np.ptp(off) <= 1e-12 else 'two_points'
            return node_id
        lap = normalized_laplacian(sub)
        count = min(max_kways, len(sub) - 1)
        vals, vecs = eigh(lap, subset_by_index=[0, count - 1], check_finite=False)
        d['eigenvalues'] = vals.tolist()
        gaps = np.diff(vals)
        if len(gaps) < 2 or np.max(gaps[1:]) <= 1e-12:
            d['stop'] = 'no_nontrivial_eigengap'
            return node_id
        index = int(np.argmax(gaps[1:]) + 1)
        k = index + 1
        d.update(proposed_children=k, eigengap=float(gaps[index]))
        y = vecs[:, :k]
        labels = _partition(sub, y, k, seed)
        if labels is None or len(np.unique(labels)) != k:
            d['stop'] = 'degenerate_partition'
            return node_id
        if k > 2:
            ideal = (labels[:, None] == labels[None, :]).astype(float)
            np.fill_diagonal(ideal, 0)
            perturbation = float(np.linalg.norm(normalized_laplacian(ideal) - lap,
                                                ord='fro') / gaps[index])
            d['perturbation_ratio'] = perturbation
            if perturbation > max_perturbation:
                d['stop'] = 'perturbation_limit'
                return node_id
        attempts = []
        while True:
            costs = _cut_cost(sub, labels)
            score = float(np.mean(costs))
            attempts.append(dict(children=k, mean_cut=score))
            if score < mean_cut_threshold:
                break
            k -= 1
            if k < 2:
                d.update(stop='mean_cut_limit', attempts=attempts)
                return node_id
            # As in released code, fallback k-means retains original embedding.
            labels = _partition(sub, y, k, seed)
            if labels is None or len(np.unique(labels)) != k:
                d.update(stop='degenerate_partition', attempts=attempts)
                return node_id
        d.update(stop='split', accepted_children=k, attempts=attempts)
        groups = sorted((members[labels == label] for label in np.unique(labels)),
                        key=lambda rows: int(rows[0]))
        for group in groups:
            node['children'].append(visit(group, node_id, depth + 1))
        return node_id

    root = visit(np.arange(len(a)), None, 0)
    return dict(nodes=nodes, roots=[root], method='haus_released_core_direct_vectors',
                stats=dict(nodes=len(nodes), leaves=sum(not n['children'] for n in nodes),
                           max_depth=max(n['depth'] for n in nodes)))


def fit(x, **config):
    x = np.asarray(x, dtype=np.float64)
    if x.ndim != 2 or not len(x) or not np.isfinite(x).all():
        raise ValueError('vectors must be a nonempty finite matrix')
    norm = np.linalg.norm(x, axis=1, keepdims=True)
    if np.any(norm == 0):
        raise ValueError('zero vectors have undefined cosine')
    unit = x / norm
    distance = np.maximum(1 - unit @ unit.T, 0)
    np.fill_diagonal(distance, 0)
    maximum = float(distance.max())
    affinity = 1 - distance / maximum if maximum > 0 else np.ones_like(distance)
    np.fill_diagonal(affinity, 0)
    return fit_affinity(affinity, **config)
