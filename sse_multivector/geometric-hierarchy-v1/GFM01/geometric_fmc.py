"""Experimental Goldschmidt et al. FMC, not covariance-based FMSC (2006).

Method: Fast Multilevel Clustering, sections 3.1--3.6, author-hosted text:
https://www.wisdom.weizmann.ac.il/~achi/LOP158.pdf
The 2005 report is listed at https://www.wisdom.weizmann.ac.il/~achi/trlist.html.
This is an independent dense research implementation, not the authors' code.

Conventions where the report is incomplete:
* Undirected coarse edges use both orientations, P.T @ W @ P, with zero
  diagonal. Literal one-orientation i<j sums would break symmetry.
* Equation 2 uses the current raw coupling W, not the previous normalized W.
  Its denominator includes all distinct fine-node pairs, including nonedges.
* Refinement updates existing interpolation support, clamps seed rows to
  identity, and retains a row if its neighbors offer no supported weight.
* Optional interpolation pruning is omitted; no low weights are discarded.
* The sparsity average is P.T @ rho / column_sum(P), exactly as printed,
  not weighted by the fine aggregate's accumulated original-point volume.
* Q=.5, alpha=1, xi=2, gamma1=gamma2=1, delta0=0, and the level cap are
  experimental settings, not reported paper defaults. The paper suggests
  k=10, six sparsity neighbors, and two refinement iterations in examples.
* Premature attachment control (section 3.4) is available but off by default:
  the report does not specify which 'few last' levels activate it.

Input coordinates are never normalized, projected, source-filtered, or moved.
Original integer row identity is retained. Duplicate coordinates are rejected
because inverse-distance weights are undefined; there is no hidden jitter.
Disconnected mutual-neighbor components remain a forest. There is no selected
semantic cut, saliency threshold, automatic root union, or taxonomy objective.

Native output is a fuzzy pyramid, NOT a hard membership tree. The separate
hard_projection explicitly commits each whole child to its largest transition
weight and reports disagreement with argmax of the composite fuzzy membership.
Dense matrices make this pilot O(n^2) memory with dense coarsening products;
it does not inherit the paper's sparse linear-time complexity claim.
"""

from __future__ import annotations

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial.distance import pdist, squareform


def _zero_diagonal(matrix):
    np.fill_diagonal(matrix, 0.)
    return matrix


def _aggregation(coupling, normalized, distance, sparsity, adaptive,
                 alpha, gamma1, gamma2):
    if not adaptive:
        return coupling.copy()
    total = sparsity[:, None] + sparsity[None, :]
    nonzero = coupling > 0
    result = np.zeros_like(coupling)
    difference = np.abs(sparsity[:, None] - sparsity[None, :])
    # Compute the positive-edge formula in log space; exact underflow to zero
    # is reported by fit rather than replacing weights by an arbitrary floor.
    with np.errstate(under='ignore'):
        result[nonzero] = np.exp(
            alpha * np.log(normalized[nonzero])
            - gamma1 * difference[nonzero] / total[nonzero]
            - gamma2 * distance[nonzero] / total[nonzero])
    return result


def _seeds(aggregation, normalized, sparsity, q, delta):
    eligible = aggregation * (normalized > delta)
    total = eligible.sum(axis=1)
    selected = []
    # Stable ties deliberately use the current node order (original row order
    # at the finest level); seed-order sensitivity is an experimental concern.
    for row in np.argsort(sparsity, kind='stable'):
        if total[row] == 0 or eligible[row, selected].sum() < q * total[row]:
            selected.append(int(row))
    return selected


def _interpolation(aggregation, seeds):
    p = aggregation[:, seeds].copy()
    p[seeds] = np.eye(len(seeds))
    totals = p.sum(axis=1)
    if np.any(totals <= 0):
        raise ArithmeticError('seed selection left an unsupported nonseed')
    return p / totals[:, None]


def _control_order(aggregation, seeds, p, tau, factor):
    """One section 3.4 pass; keep removed links removed after seed promotion."""
    is_seed = np.zeros(len(p), dtype=bool)
    is_seed[seeds] = True
    coarse_strength = aggregation[np.ix_(seeds, seeds)].max(axis=0)
    removed = ((p >= tau)
               & (coarse_strength[None, :] > factor * aggregation[:, seeds]))
    removed[is_seed] = False
    kept = p.copy()
    kept[removed] = 0
    promoted = np.flatnonzero(kept.sum(axis=1) == 0).tolist()
    new_seeds = seeds + promoted
    if promoted:
        kept = aggregation[:, new_seeds].copy()
        old_columns = kept[:, :len(seeds)]
        old_columns[removed] = 0
        kept[new_seeds] = np.eye(len(new_seeds))
    kept /= kept.sum(axis=1, keepdims=True)
    return new_seeds, kept, int(removed.sum()), promoted


def _refine(coupling, seeds, p, steps):
    support = p > 0
    for _ in range(steps):
        update = coupling @ p
        update[~support] = 0
        totals = update.sum(axis=1)
        supported = totals > 0
        update[supported] /= totals[supported, None]
        update[~supported] = p[~supported]
        update[seeds] = np.eye(len(seeds))
        p = update
    return p


def fit(X, *, n_neighbors=10, density_neighbors=6, adaptive=True, alpha=1.,
        xi=2., gamma1=1., gamma2=1., q=.5, refinement_steps=2,
        delta0=0., delta_decay=2., delta_until_level=0,
        order_control_start_level=None, attachment_tau=.5,
        attachment_factor=10., max_levels=32):
    """Return native levels, fuzzy transitions, settings, and stop diagnostics.

    ``levels[s]['membership'][i, k]`` is original row i's composite fuzzy
    membership in aggregate k. ``transitions[s]['interpolation']`` maps level
    s rows to level s+1 aggregates. Every membership/interpolation row sums to
    one. Matrix-valued results are NumPy arrays and should be stored separately
    from JSON summaries. ``max_levels`` caps the number of transitions.

    ``adaptive=False`` uses a=W as a controlled mechanism ablation, while still
    calculating the other coarse measurements. Positive delta only restricts
    seed selection, not interpolation. If it causes an identity transition,
    the declared schedule is allowed to advance until delta becomes zero.
    """
    config = dict(n_neighbors=n_neighbors, density_neighbors=density_neighbors,
                  adaptive=adaptive, alpha=alpha, xi=xi, gamma1=gamma1,
                  gamma2=gamma2, q=q, refinement_steps=refinement_steps,
                  delta0=delta0, delta_decay=delta_decay,
                  delta_until_level=delta_until_level,
                  order_control_start_level=order_control_start_level,
                  attachment_tau=attachment_tau, attachment_factor=attachment_factor,
                  max_levels=max_levels)
    for name in ('n_neighbors', 'density_neighbors', 'max_levels'):
        value = config[name]
        if not isinstance(value, (int, np.integer)) or isinstance(value, bool) or value < 1:
            raise ValueError(name + ' must be a positive integer')
    for name in ('refinement_steps', 'delta_until_level'):
        value = config[name]
        if not isinstance(value, (int, np.integer)) or isinstance(value, bool) or value < 0:
            raise ValueError(name + ' must be a nonnegative integer')
    if (order_control_start_level is not None
            and (not isinstance(order_control_start_level, (int, np.integer))
                 or isinstance(order_control_start_level, bool)
                 or order_control_start_level < 0)):
        raise ValueError('order_control_start_level must be None or a nonnegative integer')
    for name in ('alpha', 'xi', 'gamma1', 'gamma2', 'q', 'delta0',
                 'delta_decay', 'attachment_tau', 'attachment_factor'):
        if not np.isfinite(config[name]):
            raise ValueError(name + ' must be finite')
    if alpha <= 0 or xi <= 0 or not 0 < q <= 1:
        raise ValueError('alpha and xi must be positive; q must lie in (0, 1]')
    if gamma1 < 0 or gamma2 < 0 or delta0 < 0 or delta_decay <= 1:
        raise ValueError('gamma1, gamma2 and delta0 must be nonnegative; delta_decay > 1')
    if not 0 < attachment_tau <= 1 or attachment_factor <= 1:
        raise ValueError('attachment_tau must lie in (0, 1]; attachment_factor > 1')
    x = np.asarray(X, dtype=np.float64)
    if x.ndim != 2 or min(x.shape) < 1 or not np.isfinite(x).all():
        raise ValueError('X must be a nonempty finite two-dimensional matrix')
    n = len(x)
    distances = squareform(pdist(x, metric='euclidean'))
    if n > 1 and np.any(distances[np.triu_indices(n, 1)] == 0):
        raise ValueError('duplicate coordinates have undefined inverse-distance coupling')
    if not np.isfinite(distances).all():
        raise ValueError('coordinate distances overflowed')
    np.fill_diagonal(distances, np.inf)
    nearest = np.argsort(distances, axis=1, kind='stable')
    directed = np.zeros((n, n), dtype=bool)
    directed[np.arange(n)[:, None], nearest[:, :min(n_neighbors, n - 1)]] = True
    edges = directed & directed.T
    w = np.zeros((n, n))
    with np.errstate(over='raise', invalid='raise', divide='raise'):
        w[edges] = distances[edges] ** -alpha
    border = edges.astype(np.float64)
    sparsity = (np.take_along_axis(distances, nearest[:, :min(density_neighbors, n - 1)],
                                  axis=1).mean(axis=1) if n > 1 else np.zeros(1))
    normalized = w.copy()
    distance = np.zeros_like(w)
    distance[edges] = 1 / w[edges]
    volume, membership = np.ones(n), np.eye(n)
    levels, transitions = [], []
    initial_components = int(connected_components(csr_matrix(edges), directed=False,
                                                 return_labels=False))
    stop_reason = 'max_levels'
    for scale in range(max_levels + 1):
        a = _aggregation(w, normalized, distance, sparsity, adaptive,
                         alpha, gamma1, gamma2)
        if not all(np.isfinite(value).all() for value in
                   (w, border, normalized, distance, sparsity, volume, membership, a)):
            raise ArithmeticError('FMC coarse measures overflowed; revise the declared parameters')
        levels.append(dict(level=scale, coupling=w, border=border,
                           normalized_coupling=normalized, distance=distance,
                           sparsity=sparsity, volume=volume, membership=membership,
                           aggregation=a, aggregation_underflow_edges=int(
                               np.count_nonzero((w > 0) & (a == 0)) // 2)))
        if len(w) == 1:
            stop_reason = 'single_aggregate'
            break
        if scale == max_levels:
            break
        delta = delta0 / delta_decay ** scale if scale <= delta_until_level else 0.
        seeds = _seeds(a, normalized, sparsity, q, delta)
        p = _interpolation(a, seeds)
        removed, promoted = 0, []
        if order_control_start_level is not None and scale >= order_control_start_level:
            seeds, p, removed, promoted = _control_order(
                a, seeds, p, attachment_tau, attachment_factor)
        if len(seeds) == len(w) and delta == 0:
            stop_reason = 'no_coarsening'
            break
        before = p.copy()
        p = _refine(w, seeds, p, refinement_steps)
        transitions.append(dict(level=scale, seeds=seeds, interpolation=p,
                                interpolation_before_refinement=before,
                                refinement_l1_change=float(np.abs(p - before).sum()),
                                removed_attachments=removed, promoted_seeds=promoted,
                                delta=delta))
        col_sum = p.sum(axis=0)
        next_w = _zero_diagonal(p.T @ w @ p)
        next_border = _zero_diagonal(p.T @ border @ p)
        # This is the explicit symmetric version of Eq. 2, including nonedges
        # in the interpolation-only denominator but not in its numerator.
        with np.errstate(over='raise', invalid='raise', divide='raise'):
            numerator = _zero_diagonal(p.T @ (w ** xi) @ p)
            denominator = np.outer(col_sum, col_sum) - p.T @ p
            next_normalized = np.zeros_like(next_w)
            next_distance = np.zeros_like(next_w)
            connected = next_w > 0
            next_normalized[connected] = (numerator[connected]
                                          / denominator[connected]) ** (1 / xi)
            next_distance[connected] = (next_border[connected]
                                        / numerator[connected]) ** (1 / xi)
        sparsity = p.T @ sparsity / col_sum
        volume, membership = p.T @ volume, membership @ p
        w, border = next_w, next_border
        normalized, distance = next_normalized, next_distance
    return dict(method='fmc2005_experimental_fuzzy', config=config, levels=levels,
                transitions=transitions, stop_reason=stop_reason,
                diagnostics=dict(n_rows=n, dimension=x.shape[1],
                                 initial_components=initial_components,
                                 initial_edges=int(edges.sum() // 2),
                                 initial_isolated_rows=np.flatnonzero(
                                     edges.sum(axis=1) == 0).tolist(),
                                 adaptive_underflow_edges=sum(
                                     level['aggregation_underflow_edges'] for level in levels),
                                 final_aggregates=len(levels[-1]['volume'])))


def hard_projection(result):
    """Nested whole-child argmax projection, not the native fuzzy hierarchy.

    This changes FMC's output: a child cannot follow two coarse parents, and a
    later composite-membership preference cannot move an individual row across
    an earlier hard boundary. Ties choose the lowest coarse column. The native
    result is not modified. Unary steps reuse node IDs, and disconnected roots
    are not combined into an unsupported synthetic group.
    """
    n = result['diagnostics']['n_rows']
    assignment = np.arange(n)
    node_ids = list(range(n))
    nodes = [dict(id=i, children=[], members=[i], stats=dict(level=0)) for i in range(n)]
    levels = []
    for scale, native in enumerate(result['levels']):
        parents = None
        if scale:
            parents = np.argmax(result['transitions'][scale - 1]['interpolation'], axis=1)
            assignment = parents[assignment]
        groups = [np.flatnonzero(assignment == column).tolist()
                  for column in range(native['membership'].shape[1])]
        if scale:
            next_ids = []
            for column, members in enumerate(groups):
                children = [node_ids[row] for row in np.flatnonzero(parents == column)]
                if len(children) == 1:
                    next_ids.append(children[0])
                else:
                    node_id = len(nodes)
                    next_ids.append(node_id)
                    nodes.append(dict(id=node_id, children=children, members=members,
                                      stats=dict(level=scale,
                                                 fuzzy_volume=float(native['volume'][column]),
                                                 mean_fuzzy_membership=float(
                                                     native['membership'][members, column].mean()))))
            node_ids = next_ids
        composite_argmax = np.argmax(native['membership'], axis=1)
        levels.append(dict(level=scale, groups=groups, assignment=assignment.copy(),
                           parents=None if parents is None else parents.tolist(),
                           node_ids=list(node_ids), composite_argmax_disagreements=int(
                               np.count_nonzero(composite_argmax != assignment)),
                           mean_selected_fuzzy_membership=float(np.mean(
                               native['membership'][np.arange(n), assignment]))))
    return dict(method='per-transition whole-child argmax; not the native fuzzy hierarchy',
                levels=levels, nodes=nodes, roots=node_ids,
                stats=dict(n_rows=n, projection_disagreements_by_level=[
                    level['composite_argmax_disagreements'] for level in levels]))
