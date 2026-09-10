#!/usr/bin/env python3
"""Exact, isolated merge-rule experiments over frozen HDBv3 eligible distances.

The first rule is symmetric normalized Chamfer linkage (Ch_NS / 2), adapted
to the baseline's excluded edges by averaging only finite point minima.
Raw merge scores may decrease. They are not HDBSCAN distances or lifetimes.
Updates reuse the point-to-cluster recurrence in Gowda et al. (2026), §3:
https://arxiv.org/html/2602.10444v1 . No generated text enters clustering.
"""

from __future__ import annotations

import argparse
import hashlib
import heapq
import json
import math
import time
from pathlib import Path

import numpy as np


RULES = {
    'symmetric_mean': 'Half the sum of both directional means of finite per-point nearest eligible distances.',
    'symmetric_sum': 'Half the sum of both directional sums of finite per-point nearest eligible distances.',
    'min_sum': 'The smaller of both directional sums of finite per-point nearest eligible distances.',
    'average': 'The mean of every finite eligible cross-group pair distance, weighted by the number of such pairs.',
    'median': 'The ordinary median of all finite eligible cross-group pair distances; average the two middle values for even counts.',
}


def pair_score(distances, left, right, rule='symmetric_mean'):
    """Reference definition; points without an eligible partner contribute nothing."""
    if rule not in RULES:
        raise ValueError('unknown merge rule: ' + rule)
    cross = np.asarray(distances)[np.ix_(left, right)]
    if rule in ('average', 'median'):
        eligible = cross[np.isfinite(cross)]
        if not len(eligible):
            return math.inf
        return float(np.median(eligible) if rule == 'median' else eligible.mean())
    forward, reverse = cross.min(axis=1), cross.min(axis=0)
    forward, reverse = forward[np.isfinite(forward)], reverse[np.isfinite(reverse)]
    if not len(forward) or not len(reverse):
        return math.inf
    if rule == 'min_sum':
        return float(min(forward.sum(), reverse.sum()))
    if rule == 'symmetric_sum':
        return float((forward.sum() + reverse.sum()) / 2)
    return float((forward.mean() + reverse.mean()) / 2)


def agglomerate(distances, rule='symmetric_mean'):
    """Globally smallest active score, including decreases after previous merges.

    Heap ties use ordered cluster IDs. Cached directional sums and support
    counts preserve fixed edge exclusions. Space is O(n²). Mean/sum rules
    take O(n) arithmetic per merge plus heap updates. Median recomputes the
    changed cross-pair distributions exactly, with O(n³) worst-case work.
    """
    if rule not in RULES:
        raise ValueError('unknown merge rule: ' + rule)
    d = np.array(distances, dtype=np.float64, copy=True)
    if d.ndim != 2 or d.shape[0] != d.shape[1] or len(d) < 2:
        raise ValueError('distances must be a square matrix with at least two points')
    if np.isnan(d).any() or (d < 0).any():
        raise ValueError('distances must be nonnegative numbers or positive infinity')
    if not np.array_equal(d, d.T):
        raise ValueError('distances must be symmetric')
    n, total = len(d), 2 * len(d) - 1
    np.fill_diagonal(d, np.inf)
    nearest = np.full((total, n), np.inf)
    nearest[:n] = d
    sums = np.zeros((total, total))
    counts = np.zeros((total, total), dtype=np.int64)
    finite = np.isfinite(d)
    sums[:n, :n] = np.where(finite, d, 0)
    counts[:n, :n] = finite
    # All-pairs averaging needs pair counts, not endpoint-support counts.
    # Keep them separate so unsupported endpoint reporting remains identical.
    pair_sums = sums.copy() if rule == 'average' else None
    pair_counts = counts.copy() if rule == 'average' else None
    active = set(range(n))
    members = {i: np.array([i], dtype=np.int64) for i in range(n)}
    owner = np.arange(n)
    sizes = np.ones(total, dtype=np.int64)
    heap = [(float(d[i, j]), i, j) for i in range(n) for j in range(i + 1, n)
            if finite[i, j]]
    heapq.heapify(heap)
    rows = []
    for new in range(n, total):
        while heap:
            score, left, right = heapq.heappop(heap)
            if left in active and right in active:
                break
        else:
            raise ValueError('eligible distance graph must be connected')
        sizes[new] = sizes[left] + sizes[right]
        rows.append({
            'id': new, 'left': left, 'right': right,
            'size': int(sizes[new]), 'merge_score': score,
            'unsupported_left': int(sizes[left] - counts[left, right]),
            'unsupported_right': int(sizes[right] - counts[right, left]),
        })
        active.remove(left)
        active.remove(right)
        others = np.array(sorted(active), dtype=np.int64)
        members[new] = np.concatenate((members.pop(left), members.pop(right)))
        owner[members[new]] = new
        nearest[new] = np.minimum(nearest[left], nearest[right])
        sums[new, others] = sums[left, others] + sums[right, others]
        counts[new, others] = counts[left, others] + counts[right, others]
        available = np.isfinite(nearest[new])
        incoming = np.bincount(owner[available], weights=nearest[new, available], minlength=total)
        supported = np.bincount(owner[available], minlength=total)
        sums[others, new] = incoming[others]
        counts[others, new] = supported[others]
        valid = others[(counts[new, others] > 0) & (counts[others, new] > 0)]
        if rule == 'median':
            values = np.array([pair_score(d, members[new], members[other], rule)
                               for other in valid])
        elif rule == 'average':
            pair_sums[new, others] = pair_sums[left, others] + pair_sums[right, others]
            pair_counts[new, others] = pair_counts[left, others] + pair_counts[right, others]
            pair_sums[others, new] = pair_sums[new, others]
            pair_counts[others, new] = pair_counts[new, others]
            values = pair_sums[new, valid] / pair_counts[new, valid]
        elif rule == 'min_sum':
            values = np.minimum(sums[new, valid], sums[valid, new])
        elif rule == 'symmetric_sum':
            values = (sums[new, valid] + sums[valid, new]) / 2
        else:
            values = (sums[new, valid] / counts[new, valid]
                      + sums[valid, new] / counts[valid, new]) / 2
        for other, value in zip(valid.tolist(), values.tolist()):
            heapq.heappush(heap, (value, other, new))
        active.add(new)
    return rows


def load_baseline(baseline, request, vector_map, notes):
    paths = dict(baseline=baseline, request=request, vector_map=vector_map, notes=notes)
    loaded, sources = {}, {}
    for name, path in paths.items():
        data = path.read_bytes()
        loaded[name] = json.loads(data)
        sources[name] = {'path': str(path.resolve()), 'sha256': hashlib.sha256(data).hexdigest()}
    result = loaded['baseline']['artifact']['result']
    algorithm = result['algorithm_result']
    n = algorithm['vector_count']
    aliases, ids = result['alias_groups'], result['canonical_unique_ids']
    if len(aliases) != n or ids != [a[0] for a in aliases]:
        raise ValueError('canonical IDs and alias groups do not agree')
    mapping = {v['vector_id']: v for v in loaded['vector_map']['vectors']}
    source_ids = loaded['request']['source_note_ids']
    if set(source_ids) != {v for group in aliases for v in group}:
        raise ValueError('baseline aliases must match the frozen request')
    source_sets = []
    for group in aliases:
        if any(mapping[v]['note_id'] != source_ids[v] for v in group):
            raise ValueError('source notes changed between vector map and request')
        source_sets.append(frozenset(source_ids[v] for v in group))
    # Code audit: on permitted HDBv3 edges, both cross-note cores are bounded
    # by the pair's angle. Thus these saved values equal the original angles.
    # Excluded same-note values need not equal angles and are never consumed.
    d = np.array(algorithm['mutual_reachability_distances']).reshape(n, n)
    excluded = 0
    for i in range(n):
        d[i, i] = np.inf
        for j in range(i + 1, n):
            if len(source_sets[i]) == 1 and source_sets[i] == source_sets[j]:
                d[i, j] = d[j, i] = np.inf
                excluded += 1
    cores = np.array(algorithm['core_distances'])
    for i, source_set in enumerate(source_sets):
        expected = 0 if len(source_set) > 1 else np.min(d[i])
        if not math.isclose(float(cores[i]), float(expected), rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError('saved cores do not follow HDBv3 nearest-cross-note policy')
    for edge in algorithm['minimum_spanning_tree']:
        distance = d[edge['left'], edge['right']]
        if not math.isfinite(distance) or distance != edge['mutual_reachability_distance']:
            raise ValueError('baseline MST contains an excluded or changed edge')
    return d, result, source_sets, sources, excluded


def tree_summary(rows, source_sets):
    n = len(source_sets)
    memberships = [set(s) for s in source_sets]
    depths = [0] * n
    costs = [0.0] * n
    inversions = []
    for row in rows:
        a, b = row['left'], row['right']
        memberships.append(memberships[a] | memberships[b])
        depths.append(1 + max(depths[a], depths[b]))
        costs.append(row['merge_score'])
        if row['merge_score'] + 1e-12 < max(costs[a], costs[b]):
            inversions.append(row['id'])
    return {'unique_vectors': n, 'notes': len(memberships[-1]),
            'merges': len(rows), 'raw_max_depth': depths[-1],
            'parent_score_inversions': inversions,
            'merges_with_unsupported_endpoints': sum(
                bool(r['unsupported_left'] or r['unsupported_right']) for r in rows)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('baseline', 'request', 'vector-map', 'notes', 'output'):
        parser.add_argument('--' + name, required=True, type=Path)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--rule', choices=RULES, default='symmetric_mean')
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output already exists; preserve previous experiments')
    start = time.monotonic()
    d, baseline, source_sets, sources, excluded = load_baseline(
        args.baseline, args.request, args.vector_map, args.notes)
    rows = agglomerate(d, rule=args.rule)
    summary = tree_summary(rows, source_sets)
    result = {
        'schema_version': 'merge-rule-experiment-v1', 'run_id': args.run_id,
        'method': (args.rule + '_eligible_pairs' if args.rule in ('average', 'median')
                   else 'chamfer_' + args.rule + '_finite'), 'sources': sources,
        'source_code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'definition': RULES[args.rule],
        'missing_partner_policy': (
            'Omit excluded pairs from the median sample; record endpoints with no eligible partner. A pair of groups with no eligible edges cannot merge.'
            if args.rule == 'median' else
            'Omit excluded pairs from the mean and denominator; record endpoints with no eligible partner. A pair of groups with no eligible edges cannot merge.'
            if args.rule == 'average' else
            'Omit endpoints with no eligible partner from that directional aggregation; record their counts. A pair with no eligible edges cannot merge.'),
        'tie_rule': 'merge_score, then smaller cluster ID, then larger cluster ID',
        'distance': 'Frozen HDBv3 angular distances on permitted cross-note edges; no distance recomputation.',
        'excluded_undirected_edges': excluded,
        'canonical_unique_ids': baseline['canonical_unique_ids'],
        'alias_groups': baseline['alias_groups'], 'vector_count': len(d),
        'merges': rows, 'summary': summary, 'elapsed_seconds': time.monotonic() - start,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as output:
        json.dump(result, output, indent=2, allow_nan=False)
        output.write('\n')
    print(json.dumps(dict(summary, output=str(args.output), elapsed_seconds=result['elapsed_seconds']), indent=2))


if __name__ == '__main__':
    main()
