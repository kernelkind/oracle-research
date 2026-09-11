"""Read-only checks of frozen GDC09/GDC02S trajectories; no fitting or labels.

Run with the same Python/NumPy/SciPy environment as geometric_experiment.py.
Sparse saved times can disprove permanence, not establish every-step permanence.
Output is derived evidence, not another candidate or a semantic quality score.
"""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from scipy.sparse.csgraph import connected_components

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
from geometric_diffusion import _squared_distances
from geometric_experiment import write_json


def read(run, file):
    return json.loads((ROOT / run / file).read_text())


old = read('GDC06', 'hierarchy.json')
new = read('GDC09', 'hierarchy.json')
cache = np.load(ROOT / 'GDC09/coordinate-snapshots.npz')
assert new['nodes'][:len(old['nodes'])] == old['nodes']
assert new['stats']['history'][:2000] == old['stats']['history']
assert np.array_equal(cache['2000'], np.load(ROOT / 'GDC06/final-coordinates.npy'))
evidence = read('GDC09', 'evidence.json')
ids = {a['short_id']: r['row'] for r in evidence for a in r['aliases']}
baseline_nodes = {n['id']: n for n in read('GDC02', 'hierarchy.json')['nodes']}
reference_sets = {str(i): baseline_nodes[i]['members'] for i in [1334, 1354, 1406]}
reference_sets['remaining'] = sorted(set(range(len(evidence))) -
                                   set(sum(reference_sets.values(), [])))
assert sum(map(len, reference_sets.values())) == len(evidence)
observations = []

for run in ['GDC02S', 'GDC09']:
    tree = read(run, 'hierarchy.json')
    snapshots = np.load(ROOT / run / 'coordinate-snapshots.npz')
    stats = tree['stats']
    histories = {h['iteration']: h for h in stats['history']}
    parents = {c: n['id'] for n in tree['nodes'] for c in n['children']}
    nodes = {n['id']: n for n in tree['nodes']}
    tolerance = stats['merge_tolerance']
    for t in sorted(map(int, snapshots.files)):
        x = snapshots[str(t)]
        d2 = _squared_distances(x)
        # Verify the distance helper against direct subtraction on selected pairs.
        for left, right in [(111, 526), (524, 526), (444, 526)]:
            assert abs(d2[left, right] - np.sum((x[left] - x[right]) ** 2)) < 2e-14
        disconnected = []
        worst = None
        for node in tree['nodes']:
            if not node['children'] or node['iteration'] > t:
                continue
            members = node['members']
            sub = d2[np.ix_(members, members)]
            diameter = float(np.sqrt(sub.max()))
            if worst is None or diameter > worst['diameter']:
                worst = dict(node=node['id'], diameter=diameter)
            if diameter <= tolerance:
                continue
            count, labels = connected_components(sub < tolerance ** 2, directed=False)
            if count > 1:
                active = (node['id'] not in parents or
                          nodes[parents[node['id']]]['iteration'] > t)
                disconnected.append(dict(node=node['id'], active=active,
                                         born=node['iteration'], diameter=diameter,
                                         components=[sorted(members[k] for k in
                                                            np.flatnonzero(labels == j))
                                                     for j in range(count)]))
        targets = []
        epsilon = histories[min(t + 1, len(histories))]['epsilon']
        raw = np.exp(-d2 / epsilon)
        q = raw.sum(axis=1)
        p = raw / q[None, :] ** stats['density_normalization']
        p /= p.sum(axis=1, keepdims=True)
        for v in ['V356', 'V494', 'V503', 'V855']:
            i = ids[v]
            u = x / np.linalg.norm(x, axis=1, keepdims=True)
            nearest = [j for j in np.argsort(d2[i], kind='stable') if j != i][:8]
            targets.append(dict(vector=v, row=i, norm=float(np.linalg.norm(x[i])),
                                reference_weights={k: float(p[i, rows].sum())
                                                   for k, rows in reference_sets.items()},
                                to_coffee_V503=dict(
                                    distance=float(np.sqrt(d2[i, ids['V503']])),
                                    cosine=float(np.dot(u[i], u[ids['V503']])),
                                    affinity=float(raw[i, ids['V503']])),
                                nearest=[dict(row=int(j), distance=float(np.sqrt(d2[i,j])),
                                              probability=float(p[i,j])) for j in nearest]))
        observations.append(dict(run=run, iteration=t, worst_recorded_diameter=worst,
                                 disconnected_recorded_groups=disconnected, targets=targets))

output = dict(
    diagnostic_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    prefix_validation=dict(nodes_exact=True, first2000_history_exact=True,
                           coordinates_at2000_bitwise_equal=True),
    references=reference_sets,
    snapshot_sha256={run: hashlib.sha256(
        (ROOT/run/'coordinate-snapshots.npz').read_bytes()).hexdigest()
        for run in ['GDC02S', 'GDC09']},
    warning='Reference sets are retrospective accounting only. Sparse snapshots cannot prove all-step permanence. Raw probabilities are not signed motion contributions, especially after sphere projection.',
    observations=observations)
write_json(ROOT/'GDC09/continuation-analysis.json', output)
print(json.dumps(dict(prefix_validation=output['prefix_validation'],
                      observations=len(observations),
                      times_with_disconnected_groups=[
                          [o['run'], o['iteration'], len(o['disconnected_recorded_groups'])]
                          for o in observations if o['disconnected_recorded_groups']]), indent=2))
