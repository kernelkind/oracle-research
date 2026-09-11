"""Read-only motion accounting from saved diffusion coordinate snapshots.

Reference groups are fixed sets from the saved result, used only to account
for an observed move. They never feed back into fitting. Probability measures
averaging weight; motion_projection is its signed contribution along the
actual displacement. These are different quantities, neither a subject label.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from geometric_diffusion import _squared_distances
from geometric_experiment import write_json


def describe_snapshot(coordinates, targets, groups, note_ids, *, epsilon,
                      beta, relaxation, next_coordinates=None):
    x = np.asarray(coordinates, dtype=float)
    grouped = [i for members in groups.values() for i in members]
    if len(grouped) != len(set(grouped)):
        raise ValueError('reference groups must not overlap')
    groups = dict(groups)
    groups['remaining'] = sorted(set(range(len(x))) - set(grouped))
    distances = _squared_distances(x)
    affinity = np.exp(-distances / epsilon)
    degree = affinity.sum(axis=1)
    # q_i cancels on row normalization; q_j still changes relative weights.
    operator = affinity / degree[None, :] ** beta
    operator /= operator.sum(axis=1, keepdims=True)
    predicted = (1 - relaxation) * x + relaxation * (operator @ x)
    error = None
    if next_coordinates is not None:
        error = float(np.max(np.abs(predicted - next_coordinates)))
        if error > 1e-12:
            raise ValueError('reconstructed update differs from saved trajectory')
    rows = []
    for i in targets:
        delta = predicted[i] - x[i]
        displacement = float(np.linalg.norm(delta))
        direction = delta / displacement if displacement else np.zeros(x.shape[1])
        projections = relaxation * operator[i] * ((x - x[i]) @ direction)
        same_note = [bool(note_ids[i] & ids) for ids in note_ids]
        def neighbor(j):
            return dict(row=int(j), distance=float(np.sqrt(distances[i, j])),
                        raw_affinity=float(affinity[i, j]), degree=float(degree[j]),
                        probability=float(operator[i, j]),
                        motion_projection=float(projections[j]))
        by_probability = np.argsort(-operator[i], kind='stable')
        by_projection = np.argsort(-projections, kind='stable')
        details = {}
        for name, members in groups.items():
            other = [j for j in members if j != i]
            nearest = min(other, key=lambda j: distances[i, j]) if other else None
            details[name] = dict(probability=float(operator[i, members].sum()),
                                 motion_projection=float(projections[members].sum()),
                                 nearest=None if nearest is None else neighbor(nearest),
                                 mean_distance=None if not other else
                                 float(np.sqrt(distances[i, other]).mean()))
        rows.append(dict(row=i, displacement=displacement, degree=float(degree[i]),
                         coordinate_norm=float(np.linalg.norm(x[i])),
                         self_probability=float(operator[i, i]),
                         same_note_probability=float(operator[i, same_note].sum()),
                         effective_neighbors=float(1 / np.dot(operator[i], operator[i])),
                         groups=details,
                         neighbors=[neighbor(j) for j in by_probability if j != i][:12],
                         positive_drivers=[neighbor(j) for j in by_projection
                                           if j != i and projections[j] > 0][:8],
                         opposing_drivers=[neighbor(j) for j in by_projection[::-1]
                                           if j != i and projections[j] < 0][:8]))
    return dict(diameter=float(np.sqrt(distances.max())),
                next_coordinate_max_error=error, targets=rows)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('run', type=Path)
    p.add_argument('--targets', nargs='+', required=True)
    p.add_argument('--groups', type=int, nargs='+', required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    config = json.loads((args.run/'configuration.json').read_text())
    tree = json.loads((args.run/'hierarchy.json').read_text())
    evidence = json.loads((args.run/'evidence.json').read_text())
    stats = tree['stats']
    if stats['diffusion_steps'] != 1:
        p.error('motion accounting currently requires one diffusion step per update')
    ids = {a['short_id']: r['row'] for r in evidence for a in r['aliases']}
    targets = [ids[v] for v in args.targets]
    nodes = {n['id']: n for n in tree['nodes']}
    groups = {str(i): nodes[i]['members'] for i in args.groups}
    notes = [{a['note_short_id'] for a in r['aliases']} for r in evidence]
    cache = args.run/'coordinate-snapshots.npz'
    history = {step['iteration']: step for step in stats['history']}
    snapshots = np.load(cache)
    summaries = []
    for t in sorted(map(int, snapshots.files)):
        if t + 1 not in history:
            continue
        summary = describe_snapshot(snapshots[str(t)], targets, groups, notes,
                                    epsilon=history[t + 1]['epsilon'],
                                    beta=stats['density_normalization'],
                                    relaxation=stats['relaxation'],
                                    next_coordinates=(snapshots[str(t + 1)]
                                                      if str(t + 1) in snapshots else None))
        summaries.append(dict(iteration=t, epsilon=history[t + 1]['epsilon'], **summary))
    write_json(args.output, dict(run=config['run_id'],
                                source_configuration=config,
                                diagnostic_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                                snapshot_sha256=hashlib.sha256(cache.read_bytes()).hexdigest(),
                                targets={v: ids[v] for v in args.targets},
                                reference_nodes={str(i): nodes[i] for i in args.groups},
                                snapshots=summaries))
    print(f'Saved {len(summaries)} motion observations to {args.output}')


if __name__ == '__main__':
    main()
