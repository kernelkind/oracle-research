"""Offline experimental Ward-tree recovery under note-level subsampling.

No inference, encoding, fitted model or HiGen integration. NPZ input contains
saved entry vectors and integer `groups`/`notes` aligned with vector rows.
Original fine-group identities remain fixed; only broad connections are rebuilt.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np
from scipy import sparse
from scipy.cluster.hierarchy import linkage
from scipy.optimize import Bounds, LinearConstraint, milp


def group_centroids(vectors, groups, keep):
    ids = np.unique(groups[keep])
    means = np.array([vectors[keep & (groups == g)].mean(axis=0) for g in ids])
    lengths = np.linalg.norm(means, axis=1)
    if np.any(lengths <= 0) or not np.all(np.isfinite(means)):
        raise ValueError('Group centroids must be finite and nonzero')
    return ids, means / lengths[:, None]


def branch_members(tree, group_ids, group_count):
    """Map every leaf/internal node to its global original-group membership."""
    group_ids = list(group_ids)
    members = [[int(g)] for g in group_ids]
    for left, right, _, _ in tree:
        members.append(members[int(left)] + members[int(right)])
    rows, cols = [], []
    for i, values in enumerate(members):
        rows.extend([i] * len(values))
        cols.extend(values)
    return sparse.csr_matrix((np.ones(len(rows)), (rows, cols)),
                             shape=(len(members), group_count))


def branch_recovery(original, sampled, surviving_groups):
    """Best branch Jaccard after projecting BOTH trees onto surviving groups.

    Fewer than two surviving groups are uninformative, rather than evidence of
    perfect recovery or failure. The whole surviving tree trivially scores one.
    """
    restricted = original[:, list(surviving_groups)]
    size_a = np.asarray(restricted.sum(axis=1)).ravel()
    size_b = np.asarray(sampled.sum(axis=1)).ravel()
    intersection = (restricted @ sampled[:, list(surviving_groups)].T).toarray()
    union = size_a[:, None] + size_b[None, :] - intersection
    jaccard = np.divide(intersection, union, out=np.zeros_like(intersection), where=union > 0)
    best = jaccard.argmax(axis=1)
    score = jaccard[np.arange(original.shape[0]), best]
    score[size_a < 2] = np.nan
    return score, best


def chance_recovery(original, sampled, surviving_groups, *, permutations, seed):
    """Compare observed recovery with the same tree under shuffled group IDs.

    The null preserves branch sizes/tree shape and repeats the best-match search,
    rather than comparing an observed best match against a single random match.
    Whole-tree recovery is guaranteed even under shuffling, hence adds no evidence.
    """
    if permutations < 1:
        raise ValueError('At least one permutation is required')
    observed, _ = branch_recovery(original, sampled, surviving_groups)
    original = original[:, list(surviving_groups)]
    sampled = sampled[:, list(surviving_groups)]
    rng = np.random.default_rng(seed)
    null = np.zeros_like(observed)
    for _ in range(permutations):
        shuffled = sampled[:, rng.permutation(sampled.shape[1])]
        score, _ = branch_recovery(original, shuffled, range(sampled.shape[1]))
        null += np.nan_to_num(score, nan=0.) / permutations
    null[~np.isfinite(observed)] = np.nan
    adjusted = np.divide(observed-null, 1-null, out=np.zeros_like(observed),
                         where=np.isfinite(null) & (1-null > 1e-12))
    adjusted[~np.isfinite(observed)] = np.nan
    return observed, null, adjusted


def resample(vectors, groups, notes, *, repeats, fraction, seed, permutations=0):
    vectors = np.asarray(vectors, dtype=float)
    groups, notes = np.asarray(groups), np.asarray(notes)
    if (vectors.ndim != 2 or len(vectors) != len(groups) or len(groups) != len(notes)
            or not np.all(np.isfinite(vectors)) or repeats < 1 or not 0 < fraction <= 1
            or groups.ndim != 1 or notes.ndim != 1 or permutations < 0
            or not np.issubdtype(groups.dtype, np.integer)
            or not np.array_equal(np.unique(groups), np.arange(len(np.unique(groups))))):
        raise ValueError('Invalid aligned vectors/groups/notes or resampling controls')
    note_ids = np.unique(notes)
    size = int(np.ceil(len(note_ids) * fraction))
    if size < 2:
        raise ValueError('At least two notes are needed in each subsample')
    group_ids, centroids = group_centroids(vectors, groups, np.ones(len(groups), dtype=bool))
    if len(group_ids) < 2:
        raise ValueError('At least two original groups are needed')
    tree = linkage(centroids, method='ward')
    original = branch_members(tree, group_ids, int(groups.max()) + 1)
    rng = np.random.default_rng(seed)
    scores, matches, sampled_notes, sampled_groups = [], [], [], []
    nulls, adjusted_scores = [], []
    for repeat in range(repeats):
        chosen = np.sort(rng.choice(note_ids, size=size, replace=False))
        gids, means = group_centroids(vectors, groups, np.isin(notes, chosen))
        if len(gids) < 2:
            raise ValueError('Subsample has fewer than two surviving groups')
        sampled = branch_members(linkage(means, method='ward'), gids, original.shape[1])
        score, match = branch_recovery(original, sampled, gids)
        if permutations:
            observed, null, adjusted = chance_recovery(original, sampled, gids,
                                                      permutations=permutations,
                                                      seed=seed+1000000+repeat)
            if not np.allclose(observed, score, equal_nan=True):
                raise ValueError('Shuffle control changed the observed branch recovery')
            nulls.append(null)
            adjusted_scores.append(adjusted)
        scores.append(score)
        matches.append(match)
        sampled_notes.append(chosen)
        sampled_groups.append(gids.tolist())
    return dict(tree=tree, centroids=centroids, group_ids=group_ids, members=original,
                recoveries=np.asarray(scores), matches=np.asarray(matches),
                sampled_notes=np.asarray(sampled_notes), sampled_groups=sampled_groups,
                chance_baselines=np.asarray(nulls), adjusted_recoveries=np.asarray(adjusted_scores))


def choose_sections(members, group_notes, costs, *, count, minimum_notes, time_limit=120):
    """Choose disjoint branches; note coverage is a union, not summed sizes."""
    note_ids = sorted(set().union(*group_notes))
    note_index = {note: i for i, note in enumerate(note_ids)}
    rows, cols = [], []
    for g, values in enumerate(group_notes):
        rows.extend([g] * len(values))
        cols.extend(note_index[n] for n in values)
    group_note = sparse.csr_matrix((np.ones(len(rows)), (rows, cols)),
                                  shape=(members.shape[1], len(note_ids)))
    node_note = (members @ group_note).astype(bool).astype(float)
    n, m = node_note.shape
    if len(costs) != n or not np.all(np.isfinite(costs)):
        raise ValueError('Every branch needs a finite cost')
    constraints = sparse.vstack([
        sparse.hstack([sparse.csr_matrix(np.ones((1, n))), sparse.csr_matrix((1, m))]),
        sparse.hstack([members.T, sparse.csr_matrix((members.shape[1], m))]),
        sparse.hstack([-node_note.T, sparse.eye(m)]),
        sparse.hstack([sparse.csr_matrix((1, n)), sparse.csr_matrix(np.ones((1, m)))])
    ], format='csc')
    lower = np.r_[count, np.full(members.shape[1] + m, -np.inf), minimum_notes]
    upper = np.r_[count, np.ones(members.shape[1]), np.zeros(m), np.inf]
    started = time.monotonic()
    result = milp(np.r_[costs, np.zeros(m)], integrality=np.r_[np.ones(n), np.zeros(m)],
                  bounds=Bounds(np.zeros(n+m), np.ones(n+m)),
                  constraints=LinearConstraint(constraints, lower, upper),
                  options={'time_limit': time_limit, 'mip_rel_gap': .01})
    if result.x is None:
        raise ValueError(f'No feasible section selection: {result.message}')
    selected = np.flatnonzero(result.x[:n] > .5)
    actual = np.asarray(node_note[selected].sum(axis=0)).ravel() > 0
    if (len(selected) != count or actual.sum() < minimum_notes
            or np.any(np.asarray(members[selected].sum(axis=0)).ravel() > 1)):
        raise ValueError('Returned selection violates independent membership checks')
    return dict(selected=selected.tolist(), coverage=int(actual.sum()),
                note_ids=[note_ids[i] for i in np.flatnonzero(actual)],
                objective=float(result.fun), status=int(result.status), message=result.message,
                gap=float(result.mip_gap), elapsed_seconds=time.monotonic()-started)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--repeats', type=int, default=64)
    parser.add_argument('--fraction', type=float, default=.8)
    parser.add_argument('--seed', type=int, default=20261019)
    parser.add_argument('--permutations', type=int, default=0,
                        help='Optional shuffled-group-ID control per subsample')
    parser.add_argument('--sections', type=int, default=6)
    parser.add_argument('--minimum-notes', required=True, type=int)
    args = parser.parse_args()
    if args.repeats < 4 or args.repeats % 2:
        parser.error('Use an even number of repeats >=4 for discovery/holdout halves')
    args.output.mkdir(parents=True, exist_ok=False)
    plan = dict(input=str(args.input.resolve()), input_sha256=hashlib.sha256(args.input.read_bytes()).hexdigest(),
                repeats=args.repeats, fraction=args.fraction, seed=args.seed,
                permutations=args.permutations,
                sections=args.sections, minimum_notes=args.minimum_notes,
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                rule='Fixed fine groups; unit mean of surviving members; Ward Euclidean. '
                     'Branch recovery is best Jaccard on surviving group identities. '
                     'First half chooses branches minimizing group_count*(1-mean_recovery); '
                     'second half is held-out recovery, not used for selection. '
                     'Singleton branches have no nontrivial connection and zero instability cost. '
                     'Variance control uses identical tree, inputs and note-union constraint.',
                shuffle_control='When enabled: independently permute surviving group IDs within each '
                                'sampled tree; retain its sizes and shape; repeat the same best-Jaccard '
                                'search. Adjusted recovery=(observed-mean_null)/(1-mean_null). '
                                'A guaranteed match under the null gives zero evidence. '
                                'First/second halves remain discovery/holdout.',
                qualification='Whole-tree recovery is trivially one; stable membership is not semantic correctness.')
    (args.output/'plan.json').write_text(json.dumps(plan, indent=2)+'\n')
    data = np.load(args.input)
    started = time.monotonic()
    result = resample(data['vectors'], data['groups'], data['notes'],
                      repeats=args.repeats, fraction=args.fraction, seed=args.seed,
                      permutations=args.permutations)
    n_groups = len(result['group_ids'])
    sizes = np.asarray(result['members'].sum(axis=1)).ravel()
    discovery = result['recoveries'][:args.repeats//2]
    holdout = result['recoveries'][args.repeats//2:]
    def means(values):
        number = np.sum(np.isfinite(values), axis=0)
        return np.divide(np.nansum(values, axis=0), number,
                         out=np.ones(values.shape[1]), where=number > 0)
    stability, repeat_stability = means(discovery), means(holdout)
    instability = sizes * (1-stability)
    sums = result['members'] @ result['centroids']
    variance = np.maximum(0, sizes - (sums*sums).sum(axis=1)/sizes)
    group_notes = [set(data['notes'][data['groups'] == g].tolist())
                   for g in range(result['members'].shape[1])]
    selected = {}
    objectives = [('variance', variance), ('recovery', instability)]
    if args.permutations:
        adjusted = means(result['adjusted_recoveries'][:args.repeats//2])
        adjusted_holdout = means(result['adjusted_recoveries'][args.repeats//2:])
        objectives.append(('chance_adjusted_recovery', sizes*(1-adjusted)))
    for name, costs in objectives:
        choice = choose_sections(result['members'], group_notes, costs, count=args.sections,
                                 minimum_notes=args.minimum_notes)
        choice['branches'] = [dict(node=i, groups=int(sizes[i]),
                                    discovery_recovery=float(stability[i]),
                                    holdout_recovery=float(repeat_stability[i]),
                                    chance_adjusted_recovery=float(adjusted[i]) if args.permutations else None,
                                    chance_adjusted_holdout=float(adjusted_holdout[i]) if args.permutations else None,
                                    group_ids=result['members'][i].indices.tolist())
                              for i in choice['selected']]
        selected[name] = choice
    np.savez_compressed(args.output/'arrays.npz', tree=result['tree'],
                        centroids=result['centroids'], group_ids=result['group_ids'],
                        recoveries=result['recoveries'], matches=result['matches'],
                        chance_baselines=result['chance_baselines'],
                        adjusted_recoveries=result['adjusted_recoveries'],
                        sampled_notes=result['sampled_notes'], stability=stability,
                        holdout_stability=repeat_stability, sizes=sizes, variance=variance)
    summary = dict(groups=n_groups, entries=len(data['groups']), notes=len(np.unique(data['notes'])),
                   elapsed_seconds=time.monotonic()-started, selections=selected,
                   informative_counts=np.sum(np.isfinite(result['recoveries']), axis=0).tolist(),
                   sampled_groups=result['sampled_groups'])
    (args.output/'result.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(dict(output=str(args.output), elapsed_seconds=summary['elapsed_seconds'],
                          selections={k: {'coverage':v['coverage'], 'groups':[b['groups'] for b in v['branches']]}
                                      for k,v in selected.items()})), flush=True)


if __name__ == '__main__':
    main()
