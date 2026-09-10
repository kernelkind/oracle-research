#!/usr/bin/env python3
"""Native hierarchical Infomap on the exact M07 graph or its union-kNN subgraph.

Only saved cross-note angular distances are used. No SSE inference, new labels,
binary merge conversion, or note-based module pruning occurs here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import resource
import time

for variable in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[variable] = '1'

import infomap
import numpy as np

from merge_rule_experiment import load_baseline, _paris_weights


def build_graph(distances, neighbors=None):
    """Preserve M07 weights; optionally retain either endpoint's k nearest edges."""
    d = np.asarray(distances, dtype=np.float64)
    if (d.ndim != 2 or d.shape[0] != d.shape[1] or len(d) < 2
            or np.isnan(d).any() or not np.array_equal(d, d.T)):
        raise ValueError('distances must be a symmetric square matrix without NaN')
    if neighbors is not None and (not isinstance(neighbors, int) or neighbors < 1):
        raise ValueError('neighbors must be a positive integer')
    weights = _paris_weights(d)
    if neighbors is None:
        return weights
    keep = np.zeros(d.shape, dtype=bool)
    for i in range(len(d)):
        eligible = np.flatnonzero(weights[i] > 0)
        # eligible IDs begin sorted; stable sorting breaks equal angles by ID.
        closest = eligible[np.argsort(d[i, eligible], kind='stable')[:neighbors]]
        keep[i, closest] = True
    weights[~(keep | keep.T)] = 0
    return weights


def run_infomap(weights, seed=123, trials=10):
    network = infomap.Network()
    network.add_nodes(range(len(weights)))
    for a, b in zip(*np.where(np.triu(weights, 1) > 0)):
        network.add_link(int(a), int(b), float(weights[a, b]))
    result = infomap.run(network, options=infomap.Options(
        silent=True, seed=seed, num_trials=trials, flow_model='undirected',
        two_level=False, inner_parallelization=False))
    paths = sorted(({'node_id': int(node.node_id),
                     'module_path': list(node.path[:-1]),
                     'native_path': list(node.path), 'flow': float(node.flow)}
                    for node in result.nodes()), key=lambda row: row['node_id'])
    if [p['node_id'] for p in paths] != list(range(len(weights))):
        raise ValueError('Infomap output must contain every input node exactly once')
    return result, paths


def summarize_paths(paths, source_sets):
    """Expose native module prefixes and their complete memberships, not labels."""
    n = len(source_sets)
    if sorted(p['node_id'] for p in paths) != list(range(n)):
        raise ValueError('paths must cover every canonical node exactly once')
    prefixes = {()}
    for row in paths:
        path = tuple(row['module_path'])
        if any(type(part) is not int or part < 1 for part in path):
            raise ValueError('module paths require positive integer components')
        prefixes.update(path[:length] for length in range(1, len(path) + 1))
    ordered = sorted(prefixes)
    ids = {path: n + i for i, path in enumerate(ordered)}
    groups = {path: {'id': ids[path], 'module_path': list(path),
                     'parent': ids[path[:-1]] if path else None,
                     'children': [], 'direct_vectors': [], 'vector_ids': [], 'note_ids': []}
              for path in ordered}
    for path in ordered[1:]:
        groups[path[:-1]]['children'].append(ids[path])
    for row in paths:
        path, node = tuple(row['module_path']), row['node_id']
        groups[path]['direct_vectors'].append(node)
        for length in range(len(path) + 1):
            groups[path[:length]]['vector_ids'].append(node)
    for group in groups.values():
        group['direct_vectors'].sort()
        group['vector_ids'].sort()
        group['note_ids'] = sorted({note for i in group['vector_ids'] for note in source_sets[i]})
    return [groups[path] for path in ordered]


def graph_summary(weights):
    remaining = set(range(len(weights)))
    components = []
    while remaining:
        pending, component = [min(remaining)], set()
        while pending:
            node = pending.pop()
            if node in component:
                continue
            component.add(node)
            pending.extend(int(j) for j in np.flatnonzero(weights[node]) if j not in component)
        remaining -= component
        components.append(len(component))
    positive = weights[np.triu(weights > 0, 1)]
    degrees = np.count_nonzero(weights, axis=1)
    return {'undirected_edges': len(positive), 'component_sizes': sorted(components, reverse=True),
            'isolated_nodes': int((degrees == 0).sum()),
            'degree_min': int(degrees.min()), 'degree_max': int(degrees.max()),
            'degree_median': float(np.median(degrees)),
            'weight_min': float(positive.min()) if len(positive) else None,
            'weight_max': float(positive.max()) if len(positive) else None}


def write_json(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('baseline', 'request', 'vector-map', 'notes', 'reference', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--neighbors', type=int)
    parser.add_argument('--seed', type=int, default=123)
    parser.add_argument('--trials', type=int, default=10)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output already exists; previous results must remain unchanged')
    if args.seed < 1 or args.trials < 1:
        parser.error('seed and trials must be positive')
    if infomap.__version__ != '2.15.1' or np.__version__ != '2.3.4':
        parser.error('use the pinned Infomap 2.15.1 / NumPy 2.3.4 environment')
    started = time.monotonic()
    d, baseline, source_sets, sources, excluded = load_baseline(
        args.baseline, args.request, args.vector_map, args.notes)
    reference_data = args.reference.read_bytes()
    reference = json.loads(reference_data)
    for name, source in sources.items():
        if source['sha256'] != reference['sources'][name]['sha256']:
            raise ValueError(f'{name} changed from the frozen M07 source')
    if (reference['method'] != 'paris_linear_eligible_graph'
            or reference['canonical_unique_ids'] != baseline['canonical_unique_ids']
            or reference['alias_groups'] != baseline['alias_groups']):
        raise ValueError('reference must be M07 with the same ordered canonical nodes')
    weights = build_graph(d, args.neighbors)
    graph = graph_summary(weights)
    args.output.mkdir(parents=True, exist_ok=False)
    graph_path = args.output / 'graph.net'
    with graph_path.open('x') as stream:
        stream.write(f'*Vertices {len(weights)}\n')
        for i, aliases in enumerate(baseline['alias_groups']):
            stream.write(f'{i} "{aliases[0]}"\n')
        stream.write('*Edges\n')
        for a, b in zip(*np.where(np.triu(weights, 1) > 0)):
            stream.write(f'{a} {b} {weights[a,b]:.17g}\n')
    configuration = {
        'schema_version': 'infomap-configuration-v1', 'run_id': args.run_id,
        'sources': sources,
        'reference': {'path': str(args.reference.resolve()),
                      'sha256': hashlib.sha256(reference_data).hexdigest()},
        'source_code': {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                        for path in [Path(__file__), Path(__file__).with_name('merge_rule_experiment.py')]},
        'graph': {'neighbors': args.neighbors, 'selection': 'all_eligible' if args.neighbors is None
                  else 'symmetric_union_nearest_neighbors',
                  'tie_break': 'ascending canonical node ID',
                  'weight': '1 - saved eligible angular distance / pi',
                  'same_note_policy': 'exclude pairs whose alias source sets are the same singleton',
                  'sha256': hashlib.sha256(graph_path.read_bytes()).hexdigest(), **graph},
        'infomap': {'version': infomap.__version__, 'flow_model': 'undirected',
                    'two_level': False, 'seed': args.seed, 'num_trials': args.trials,
                    'inner_parallelization': False, 'other_settings': 'Infomap 2.15.1 defaults'},
        'environment': {'python': platform.python_version(), 'numpy': np.__version__,
                        'platform': platform.platform(), 'threads': 1},
    }
    write_json(args.output / 'configuration.json', configuration)
    inference_start = time.monotonic()
    result, paths = run_infomap(weights, args.seed, args.trials)
    elapsed_inference = time.monotonic() - inference_start
    result.write_tree(str(args.output / 'native.tree'))
    result.write_json(str(args.output / 'native.json'))
    groups = summarize_paths(paths, source_sets)
    summary = {'notes': len(groups[0]['note_ids']), 'unique_vectors': len(weights),
               'original_ids': sum(map(len, baseline['alias_groups'])),
               'groups_including_root': len(groups),
               'top_groups': len(groups[0]['children']),
               'leaf_groups': sum(not g['children'] for g in groups),
               'maximum_module_depth': max(len(g['module_path']) for g in groups),
               'one_note_groups_excluding_root': sum(len(g['note_ids']) == 1 for g in groups[1:]),
               'unchanged_note_parent_edges': sum(
                   g['parent'] is not None and g['note_ids'] == groups[g['parent']-len(weights)]['note_ids']
                   for g in groups),
               'codelength': result.codelength, 'one_level_codelength': result.one_level_codelength,
               'trial_codelengths': list(result.codelengths),
               'infomap_seconds': elapsed_inference,
               'elapsed_seconds': time.monotonic() - started,
               'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    hierarchy = {'schema_version': 'infomap-hierarchy-v1', 'run_id': args.run_id,
                 'sources': sources, 'vector_count': len(weights),
                 'canonical_unique_ids': baseline['canonical_unique_ids'],
                 'alias_groups': baseline['alias_groups'], 'paths': paths,
                 'root': len(weights), 'modules': groups, 'summary': summary,
                 'excluded_same_note_edges': excluded}
    write_json(args.output / 'hierarchy.json', hierarchy)
    print(json.dumps({'run_id': args.run_id, 'graph': graph, 'summary': summary}, indent=2))


if __name__ == '__main__':
    main()
