"""Experimental cosine clustering with a distinct-note minimum per section.

This partitions original entries directly, without a tree or a fitted encoder.
For fixed centers, assignment is a sparse minimum-cost-flow LP: each entry has
one unit of supply; note/section witness edges have capacity one; every section
requires a minimum witness flow. Entries from one note can support several
sections, but repeated entries cannot inflate that note's count in one section.
The LP uses O(k * (entries + notes)) variables/nonzeros, not an all-pairs matrix.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np
from scipy import sparse
from scipy.optimize import linprog


def note_counts(labels, notes, sections):
    return [len(set(notes[labels == k].tolist())) for k in range(sections)]


def assign(costs, note_ids, *, minimum_notes, time_limit=30):
    """Minimum-cost integral assignment, counting distinct note witnesses."""
    costs, notes = np.asarray(costs, dtype=float), np.asarray(note_ids)
    if (costs.ndim != 2 or not costs.size or notes.ndim != 1
            or len(notes) != len(costs) or not np.all(np.isfinite(costs))
            or type(minimum_notes) is not int or minimum_notes < 0
            or not np.isfinite(time_limit) or time_limit <= 0):
        raise ValueError('Finite costs, aligned notes and a nonnegative note minimum required')
    n, k = costs.shape
    unique, inverse = np.unique(notes, return_inverse=True)
    m = len(unique)
    if m < minimum_notes or n < k * minimum_notes:
        raise ValueError('Not enough distinct notes or entry witnesses for the section minimum')
    labels = costs.argmin(axis=1)
    started = time.monotonic()
    status = 'nearest assignments already satisfy note minimum'
    if min(note_counts(labels, notes, k)) < minimum_notes:
        nx, nw = n * k, m * k
        entry_columns = np.arange(nx)
        witness_rows = (inverse[:, None] * k + np.arange(k)).ravel()
        wr = np.arange(nw)
        ub = sparse.coo_matrix((
            np.r_[-np.ones(nx), np.ones(nw), -np.ones(nw)],
            (np.r_[witness_rows, wr, nw + np.tile(np.arange(k), m)],
             np.r_[entry_columns, nx + wr, nx + wr])),
            shape=(nw + k, nx + nw)).tocsr()
        eq = sparse.coo_matrix((np.ones(nx),
            (np.repeat(np.arange(n), k), entry_columns)), shape=(n, nx + nw)).tocsr()
        result = linprog(np.r_[costs.ravel(), np.zeros(nw)], A_ub=ub,
                         b_ub=np.r_[np.zeros(nw), np.full(k, -minimum_notes)],
                         A_eq=eq, b_eq=np.ones(n), bounds=(0, 1), method='highs-ds',
                         options={'time_limit': time_limit})
        if not result.success:
            raise ValueError('No optimal note-constrained assignment: ' + result.message)
        x = result.x[:nx].reshape(n, k)
        if np.max(np.abs(x - np.rint(x))) > 1e-6:
            raise ValueError('Flow LP returned fractional entry assignments')
        labels = x.argmax(axis=1)
        actual_cost = costs[np.arange(n), labels].sum()
        if not np.isclose(actual_cost, result.fun, rtol=1e-8, atol=1e-8):
            raise ValueError('Rounded assignment disagrees with optimal flow cost')
        status = result.message
    counts = note_counts(labels, notes, k)
    if min(counts) < minimum_notes:
        raise ValueError('Assignment failed independent distinct-note validation')
    return dict(labels=labels.tolist(), section_notes=counts,
                objective=float(costs[np.arange(n), labels].sum()),
                elapsed_seconds=time.monotonic() - started, status=status)


def _initial_centers(vectors, count, seed):
    rng = np.random.default_rng(seed)
    indices = [int(rng.integers(len(vectors)))]
    nearest = np.ones(len(vectors)) * 2
    while len(indices) < count:
        nearest = np.minimum(nearest, np.clip(1 - vectors @ vectors[indices[-1]], 0, 2))
        nearest[indices] = 0
        if nearest.sum() <= 1e-14:
            selected = next(i for i in range(len(vectors)) if i not in indices)
        else:
            selected = int(rng.choice(len(vectors), p=nearest / nearest.sum()))
        indices.append(selected)
    return vectors[indices].copy(), indices


def partition(vectors, note_ids, *, sections, minimum_notes, seed,
              max_iterations=50, time_limit=30):
    """Alternate exact constrained assignments and normalized center updates.

    Center initialization samples proportional to nearest-center cosine distance.
    Each step minimizes the same sum of entry-to-center cosine dissimilarities.
    Convergence is local; neither the seeds nor objective establish useful topics.
    """
    vectors, notes = np.asarray(vectors, dtype=float), np.asarray(note_ids)
    if (vectors.ndim != 2 or not vectors.size or not np.all(np.isfinite(vectors))
            or notes.ndim != 1 or len(notes) != len(vectors)
            or type(sections) is not int or not 1 <= sections <= len(vectors)
            or type(max_iterations) is not int or max_iterations < 1
            or np.any(np.linalg.norm(vectors, axis=1) <= 0)):
        raise ValueError('Finite nonzero vectors, aligned notes and valid section/iteration counts required')
    vectors = vectors / np.linalg.norm(vectors, axis=1)[:, None]
    centers, initial = _initial_centers(vectors, sections, seed)
    previous, trace = None, []
    started = time.monotonic()
    converged = False
    for iteration in range(max_iterations):
        costs = np.clip(1 - vectors @ centers.T, 0, 2)
        assignment = assign(costs, notes, minimum_notes=minimum_notes, time_limit=time_limit)
        labels = np.asarray(assignment['labels'])
        updated = centers.copy()
        for k in range(sections):
            total = vectors[labels == k].sum(axis=0)
            length = np.linalg.norm(total)
            if length > 1e-14:
                updated[k] = total / length
        objective = float(np.clip(1 - (vectors * updated[labels]).sum(axis=1), 0, 2).sum())
        if trace and objective > trace[-1]['objective'] + 1e-7:
            raise ValueError('Clustering objective increased during constrained update')
        trace.append(dict(iteration=iteration + 1, objective=objective,
                          fixed_center_objective=assignment['objective'],
                          assignment_seconds=assignment['elapsed_seconds'],
                          section_notes=assignment['section_notes']))
        centers = updated
        if previous is not None and np.array_equal(labels, previous):
            converged = True
            break
        previous = labels.copy()
    final_costs = np.clip(1 - vectors @ centers.T, 0, 2)
    nearest = final_costs.argmin(axis=1)
    displaced = np.flatnonzero(labels != nearest)
    return dict(seed=int(seed), initial_indices=initial, labels=labels.tolist(),
                section_notes=note_counts(labels, notes, sections),
                objective=objective, converged=converged, iterations=len(trace),
                centers=centers.tolist(), trace=trace,
                displaced_indices=displaced.tolist(),
                displacement_cost=float((final_costs[np.arange(len(labels)), labels]
                                         - final_costs.min(axis=1)).sum()),
                elapsed_seconds=time.monotonic() - started)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path, help='NPZ: vectors and aligned note IDs')
    parser.add_argument('output', type=Path)
    parser.add_argument('--sections', type=int, default=6)
    parser.add_argument('--minimum-notes', type=int, required=True)
    parser.add_argument('--minimum-total-notes', type=int, required=True)
    parser.add_argument('--starts', type=int, default=8)
    parser.add_argument('--seed', type=int, default=20261018)
    args = parser.parse_args()
    if args.starts < 1:
        parser.error('starts must be positive')
    packet = np.load(args.input, allow_pickle=False)
    vectors, notes = packet['vectors'], packet['notes']
    if len(np.unique(notes)) < args.minimum_total_notes:
        parser.error('input cannot meet the original-corpus retention requirement')
    args.output.mkdir(parents=True, exist_ok=False)
    plan = dict(status='Frozen before numerical clustering; not a HiGen policy',
                input=str(args.input.resolve()),
                input_sha256=hashlib.sha256(args.input.read_bytes()).hexdigest(),
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                sections=args.sections, minimum_notes=args.minimum_notes,
                minimum_total_notes=args.minimum_total_notes, starts=args.starts,
                seeds=list(range(args.seed, args.seed + args.starts)),
                max_iterations=50, assignment_time_limit_seconds=30,
                objective='Sum of entry-to-center cosine dissimilarities; equal original-entry weights',
                controls='Unconstrained spherical clustering uses identical initial centers/seeds',
                coverage='All supplied original entries assigned once; distinct notes may span sections')
    (args.output / 'plan.json').write_text(json.dumps(plan, indent=2) + '\n')
    runs = {}
    for mode, minimum in [('constrained', args.minimum_notes), ('unconstrained', 0)]:
        trials = [partition(vectors, notes, sections=args.sections, minimum_notes=minimum,
                            seed=seed) for seed in plan['seeds']]
        best = min(trials, key=lambda r: (r['objective'], r['seed']))
        runs[mode] = dict(best=best, trials=trials, covered_notes=len(np.unique(notes)))
        (args.output / (mode + '.json')).write_text(json.dumps(runs[mode], indent=2) + '\n')
        print(mode, 'notes', len(np.unique(notes)), 'per-section', best['section_notes'],
              'objective', best['objective'], 'displaced', len(best['displaced_indices']), flush=True)


if __name__ == '__main__':
    main()
