"""Replay numerical merge tolerances without recomputing diffusion dynamics."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.sparse.csgraph import connected_components
from geometric_diffusion import _squared_distances
from geometric_experiment import write_json


def replay(snapshots, tolerance):
    if not np.isfinite(tolerance) or tolerance <= 0:
        raise ValueError('tolerance must be positive and finite')
    times = sorted(snapshots)
    if not times or times != list(range(times[-1] + 1)):
        raise ValueError('replay requires every coordinate snapshot from iteration zero')
    n = len(snapshots[0])
    cumulative = np.eye(n, dtype=bool)
    history = []
    for iteration in times:
        coordinates = snapshots[iteration]
        if coordinates.shape != snapshots[0].shape:
            raise ValueError('snapshot shapes differ')
        cumulative |= _squared_distances(coordinates) < tolerance * tolerance
        count, labels = connected_components(cumulative, directed=False)
        groups = [np.flatnonzero(labels == label).tolist() for label in range(count)]
        history.append(dict(iteration=iteration, groups=groups))
    return history


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--tolerances', type=float, nargs='+', required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output exists; preserve previous results')
    path = args.run/'coordinate-snapshots.npz'
    with np.load(path) as saved:
        snapshots = {int(k): saved[k] for k in saved.files}
    records = json.loads((args.run/'evidence.json').read_text())
    results = {}
    for tolerance in args.tolerances:
        history = replay(snapshots, tolerance)
        for step in history:
            step['note_sets'] = [sorted({entry['note_short_id'] for i in group
                                         for entry in records[i]['aliases']})
                                 for group in step['groups']]
        results[str(tolerance)] = history
    write_json(args.output, dict(source=str(path.resolve()),
                                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                                histories=results))
    for tolerance, history in results.items():
        print(tolerance, [(step['iteration'], len(step['groups']),
                           max(map(len, step['note_sets']))) for step in history])


if __name__ == '__main__':
    main()
