"""Experimental fixed-reference graph boundaries; not hierarchy admission.

Order accepted references by their unchanged cross-note mean meaning support.
Sweep complete score levels, measuring the fusion weight crossing each split.
The lowest-conductance split on the smaller-volume side must also be a local
minimum of the fraction of its own weight escaping. That second condition
avoids a false valley caused only by switching the conductance denominator at
half volume. A missing valley leaves the boundary unresolved.

This is a hypothesis, not a semantic certificate or a PageRank/Cheeger guarantee:
the ordering is supplied by meaning support, not a spectral method. References,
their memberships and their fusion weights never change. A boundary need not
recover every member; whole-note recovery is reported separately. Outsiders
cannot influence the graph, ordering or boundary.
"""
import numpy as np
from scipy import sparse

from sse_multivector.fixed_reference_bend import mean_support


def derive_boundary(reference_affinities, reference_notes, group_indices,
                    reference_connections, *, excluded_notes=()):
    """Map a fixed-graph split to an adjacent meaning-score midpoint.

    Exclude a source note from the graph and from all meaning means together.
    Equal-score entries enter together; no boundary splits a score tie. Select
    the lowest conductance among cuts touching the group with at most half of
    graph volume; ties favor the earlier, higher-score cut. Require a local
    valley, looking past the half-volume limit using cut / own volume. A zero
    cut is a resolved boundary. The whole reference set is never eligible.

    The graph volume is weighted degree, not distinct-note count. Self edges
    are ignored. Graph weights determine the split; they are never compared
    numerically with outsider meaning scores.
    """
    a = np.asarray(reference_affinities, dtype=float)
    n = len(reference_notes)
    if a.shape != (n, n) or not np.allclose(a, a.T, rtol=0, atol=1e-12):
        raise ValueError('reference affinities must be square, aligned and symmetric')
    g = sparse.csr_matrix(reference_connections, dtype=float, copy=True)
    if (g.shape != (n, n) or not np.all(np.isfinite(g.data))
            or np.any(g.data < 0) or (g - g.T).nnz):
        raise ValueError('reference connections must be aligned, finite, nonnegative and symmetric')
    group = list(group_indices)
    excluded = set(excluded_notes)
    scores = mean_support(a, reference_notes, reference_notes, group,
                          excluded_notes=excluded)
    group = [i for i in group if reference_notes[i] not in excluded]
    context = [i for i in range(n) if reference_notes[i] not in excluded and np.isfinite(scores[i])]
    result = dict(status='no_group_reference' if not group else 'no_resolved_minimum',
                  threshold=None, group_indices=group, context_indices=context,
                  selected_indices=[], curve=[], best_level=None)
    if not group or not context:
        return result
    g.setdiag(0)
    g.eliminate_zeros()
    g = g[context][:, context].tocsr()
    degree = np.asarray(g.sum(axis=1)).ravel()
    total = float(degree.sum())
    result['total_volume'] = total
    if total == 0:
        result['status'] = 'no_edges'
        return result
    levels = {}
    for j, i in enumerate(context):
        levels.setdefault(float(scores[i]), []).append(j)
    inside = np.zeros(len(context), dtype=bool)
    group_set = set(group)
    volume = cut = 0.
    group_count = 0
    for score, positions in sorted(levels.items(), reverse=True):
        for j in positions:
            start, end = g.indptr[j:j+2]
            cut += float(degree[j] - 2 * g.data[start:end][inside[g.indices[start:end]]].sum())
            volume += float(degree[j])
            inside[j] = True
            group_count += context[j] in group_set
        denominator = min(volume, total - volume)
        phi = max(0., cut) / denominator if denominator > 1e-12 * total else None
        escape = max(0., cut) / volume if volume > 1e-12 * total else None
        result['curve'].append(dict(score=score, indices=[context[j] for j in positions],
                                   size=int(inside.sum()), volume=volume, cut=max(0., cut),
                                   conductance=phi, escape_fraction=escape,
                                   group_members=group_count,
                                   eligible=bool(group_count and phi is not None
                                                 and volume <= total / 2 + 1e-12 * total)))
    curve = result['curve']
    eligible = [j for j, row in enumerate(curve) if row['eligible'] and j + 1 < len(curve)]
    if not eligible:
        return result
    best = eligible[0]
    for j in eligible[1:]:
        if curve[j]['conductance'] < curve[best]['conductance'] - 1e-12:
            best = j
    result['best_level'] = best
    row = curve[best]
    later = next((r for r in curve[best+1:] if r['escape_fraction'] is not None
                  and abs(r['escape_fraction'] - row['escape_fraction']) > 1e-12), None)
    previous = curve[best-1] if best else None
    valley = (row['escape_fraction'] <= 1e-12 or
              ((previous is None or previous['escape_fraction'] is None
                or row['escape_fraction'] <= previous['escape_fraction'] + 1e-12)
               and later is not None and later['escape_fraction'] > row['escape_fraction']))
    if not valley:
        return result
    result.update(status='boundary', threshold=(row['score'] + curve[best+1]['score']) / 2,
                  selected_indices=[i for level in curve[:best+1] for i in level['indices']])
    return result


def qualify_boundary(reference_affinities, reference_notes, group_indices,
                     reference_connections, *, excluded_notes=()):
    """Report whole-source-note recovery without changing the fixed group."""
    excluded = set(excluded_notes)
    group = [i for i in group_indices if reference_notes[i] not in excluded]
    base = derive_boundary(reference_affinities, reference_notes, group,
                           reference_connections, excluded_notes=excluded)
    folds = []
    for note in sorted({reference_notes[i] for i in group}):
        boundary = derive_boundary(reference_affinities, reference_notes, group,
                                   reference_connections, excluded_notes=excluded | {note})
        held = [i for i in group if reference_notes[i] == note]
        scores = mean_support(np.asarray(reference_affinities)[held], [note] * len(held),
                              reference_notes, group, excluded_notes=excluded | {note})
        threshold = boundary['threshold']
        failed = [i for i, score in zip(held, scores)
                  if threshold is None or not np.isfinite(score) or score < threshold]
        folds.append(dict(excluded_note=note, boundary=boundary, held_indices=held,
                          scores=[float(s) if np.isfinite(s) else None for s in scores],
                          failed_indices=failed))
    return dict(base=base, folds=folds,
                eligible=base['threshold'] is not None and bool(folds)
                and all(not fold['failed_indices'] for fold in folds))
