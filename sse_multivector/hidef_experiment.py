#!/usr/bin/env python3
"""Weighted independent Leiden discovery, HiDeF persistence, exact containment.

The finder adapter preserves upstream resolution sampling, ClusterGraph and
consensus, but supplies weights/seeds, runs serially and keeps size-one groups.
Persistence aggregation precedes containment and is saved separately. No parent
expansion, generated labels, source edits or embedding calls are performed.
"""

from __future__ import annotations

import argparse
from collections import Counter, deque
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import resource
import shlex
import time

for variable in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS',
                 'NUMEXPR_NUM_THREADS'):
    os.environ[variable] = '1'

HIDEF_COMMIT = '3d016a375ac52feda0e0b2a3ace917c834f3a3a9'
METHOD = 'hidef_weighted_leiden_strict_containment'
DEFAULTS = dict(minres=.001, maxres=25., density=.1, neighbors=10,
                jaccard=.75, persistence=5, consensus_percent=75, seed=123,
                candidate_min_size=1, n_iterations=2, sample=1., workers=1)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def read_graph(path, canonical_ids):
    """Read the saved zero-based Pajek-like format without igraph reindexing."""
    import igraph

    lines = Path(path).read_text().splitlines()
    n = len(canonical_ids)
    if not lines or lines[0] != f'*Vertices {n}' or len(lines) < n + 2:
        raise ValueError('graph vertex count does not match the frozen canonical IDs')
    for i, canonical_id in enumerate(canonical_ids):
        if shlex.split(lines[i + 1]) != [str(i), canonical_id]:
            raise ValueError(f'graph vertex identity mismatch at node {i}')
    if lines[n + 1] != '*Edges':
        raise ValueError('graph must have an undirected *Edges section')
    edges, weights, seen = [], [], set()
    for line in lines[n + 2:]:
        fields = line.split()
        if len(fields) != 3:
            raise ValueError('each graph edge requires two IDs and a weight')
        a, b, weight = int(fields[0]), int(fields[1]), float(fields[2])
        if not 0 <= a < b < n or not math.isfinite(weight) or weight <= 0:
            raise ValueError('graph requires positive finite weights and ordered cross-node edges')
        if (a, b) in seen:
            raise ValueError('duplicate graph edge')
        seen.add((a, b))
        edges.append((a, b))
        weights.append(weight)
    graph = igraph.Graph(n=n, edges=edges, directed=False)
    graph.es['weight'] = weights
    if graph.get_edgelist() != edges or list(graph.es['weight']) != weights:
        raise ValueError('igraph changed graph identities or weights')
    return graph


def load_inputs(graph_directory, data_directory):
    graph_directory, data_directory = Path(graph_directory), Path(data_directory)
    reference_path = graph_directory / 'hierarchy.json'
    reference = json.loads(reference_path.read_text())
    config = json.loads((graph_directory / 'configuration.json').read_text())
    if reference.get('schema_version') != 'infomap-hierarchy-v1' or reference.get('run_id') != 'I03':
        raise ValueError('input must be the saved I03 hierarchy')
    graph_path = graph_directory / 'graph.net'
    if sha256(graph_path) != config['graph']['sha256']:
        raise ValueError('I03 graph checksum mismatch')
    if reference['sources'] != config['sources']:
        raise ValueError('I03 provenance disagrees between configuration and hierarchy')
    paths = {
        'baseline': data_directory / 'hdbv3-cross-note-edges-v1/response.json',
        'request': data_directory / 'hdbv3-cross-note-edges-v1/request.json',
        'vector_map': data_directory / 'vectors/vector-map.json',
        'notes': data_directory / 'reviewed-input.json',
    }
    for name, path in paths.items():
        if sha256(path) != reference['sources'][name]['sha256']:
            raise ValueError(f'I03 source checksum mismatch: {name}')
    aliases, canonical = reference['alias_groups'], reference['canonical_unique_ids']
    if len(aliases) != reference['vector_count'] or len(canonical) != len(aliases):
        raise ValueError('I03 vector identity counts disagree')
    records = json.loads(paths['vector_map'].read_text())['vectors']
    by_id = {row['vector_id']: row for row in records}
    if len(by_id) != len(records):
        raise ValueError('duplicate vector-map IDs')
    notes = json.loads(paths['notes'].read_text())['notes']
    note_ids = {row['note_id'] for row in notes}
    flattened = [alias for group in aliases for alias in group]
    if len(set(flattened)) != len(flattened) or set(flattened) != set(by_id):
        raise ValueError('aliases must preserve every vector-map record exactly once')
    for i, group in enumerate(aliases):
        if not group or canonical[i] != group[0]:
            raise ValueError('canonical ID must be the first saved alias')
    source_sets = [{by_id[alias]['note_id'] for alias in group} for group in aliases]
    if any(not sources or not sources <= note_ids for sources in source_sets):
        raise ValueError('vector aliases refer to absent source notes')
    graph = read_graph(graph_path, canonical)
    if graph.ecount() != config['graph']['undirected_edges']:
        raise ValueError('I03 edge count mismatch')
    return graph, reference, source_sets, graph_path


def resolution_schedule(config):
    """Upstream run() sampling separated from its unseeded multiprocessing call."""
    import networkx as nx
    import numpy as np
    from hidef import hidef_finder as finder

    low, high = config['minres'], config['maxres']
    if not all(math.isfinite(x) for x in (low, high, config['density'])):
        raise ValueError('resolution configuration must be finite')
    if not .001 <= low < high or config['density'] <= 0 or config['neighbors'] < 1:
        raise ValueError('require .001 <= minres < maxres, positive density and neighbors')
    graph = nx.Graph()
    for value in (low, high):
        finder.update_resolution_graph(graph, value, config['density'], config['neighbors'])
    queue, resolutions = deque([(low, high)]), [low, high]
    while queue:
        a, b = queue.popleft()
        if round(b - a, 4) <= .001:
            continue
        if graph.nodes[f'{a:.4f}']['padded'] and graph.nodes[f'{b:.4f}']['padded']:
            continue
        middle = float(np.round(np.sqrt(a * b), 4))
        if f'{middle:.4f}' in graph:
            raise ValueError('resolution rounding collision')
        resolutions.append(middle)
        if len(resolutions) > 4096:
            raise ValueError('resolution schedule exceeds the bounded 4096-sample limit')
        queue.extend([(a, middle), (middle, b)])
        finder.update_resolution_graph(graph, middle, config['density'], config['neighbors'])
    return resolutions, graph


def weighted_partition(graph, resolution, seed, n_iterations=2):
    import leidenalg

    return leidenalg.find_partition(
        graph, leidenalg.RBConfigurationVertexPartition,
        weights=graph.es['weight'], resolution_parameter=resolution,
        seed=seed, n_iterations=n_iterations)


def discover(graph, source_sets, config):
    from hidef import hidef_finder as finder

    resolutions, resolution_graph = resolution_schedule(config)
    cluster_graph = finder.ClusterGraph()
    cluster_graph.graph.update(sim_threshold=config['jaccard'], num_leaves=graph.vcount())
    partitions, candidates = [], []
    for index, resolution in enumerate(resolutions):
        started = time.monotonic()
        seed = config['seed'] + index
        partition = weighted_partition(graph, resolution, seed, config['n_iterations'])
        # Explicitly override upstream minsize=4; every raw community survives.
        matrix = finder.partition_to_membership_matrix(partition, minsize=1)
        key = f'{resolution:.4f}'
        resolution_graph.nodes[key]['matrix'] = matrix
        cluster_graph.add_clusters(resolution_graph, resolution)
        candidate_ids = [int(v) for v in resolution_graph.nodes[key]['node_indices']]
        for candidate_id in candidate_ids:
            members = [int(v) for v in cluster_graph.nodes[candidate_id]['data'].members]
            candidates.append({'id': candidate_id, 'sample_index': index,
                               'resolution': resolution, 'seed': seed,
                               'vector_ids': members,
                               'note_ids': sorted({note for v in members for note in source_sets[v]})})
        partitions.append({'sample_index': index, 'resolution': resolution, 'seed': seed,
                           'membership': list(partition.membership), 'candidate_ids': candidate_ids,
                           'quality': float(partition.quality()),
                           'seconds': time.monotonic() - started})
    return cluster_graph, candidates, partitions, resolution_graph


def persistent_groups(cluster_graph, candidates, source_sets, config):
    """Call upstream consensus; trace its families separately and assert agreement.

    The upstream API omits family IDs. This companion repeats only its family
    enumeration for audit lineage; no independent persistence variant is used.
    """
    import networkx as nx
    import numpy as np
    from scipy.sparse import csr_matrix
    from hidef import hidef_finder as finder
    from hidef.utils import jaccard_matrix

    k, percent = config['persistence'], config['consensus_percent']
    native = finder.consensus(cluster_graph, k=k, f=1., p=percent)
    families = []
    for component in nx.connected_components(cluster_graph):
        if len(component) < k:
            continue
        component = sorted(int(v) for v in component)
        matrix = csr_matrix(np.stack([cluster_graph.nodes[v]['data'].binary for v in component]))
        rows, columns = jaccard_matrix(matrix, matrix)  # upstream fixed strict > .75
        clique_graph = nx.Graph()
        clique_graph.add_edges_from((int(a), int(b)) for a, b in zip(rows, columns) if a != b)
        for family in nx.algorithms.community.k_clique_communities(clique_graph, k):
            families.append(sorted(component[i] for i in family))
    families.sort(key=lambda ids: (-len(ids), ids))
    collapsed = finder.collapse_cluster_graph(cluster_graph, families, p=percent)
    native_signature = Counter((tuple(int(v) for v in np.flatnonzero(members)), int(support))
                               for members, support in native)
    traced_signature = Counter((tuple(int(v) for v in np.flatnonzero(members)), len(family))
                               for members, family in zip(collapsed, families))
    if native_signature != traced_signature:
        raise ValueError('consensus lineage does not match the actual pinned HiDeF consensus')
    by_id = {row['id']: row for row in candidates}
    result = []
    for index, (members, family) in enumerate(zip(collapsed, families)):
        vector_ids = [int(v) for v in np.flatnonzero(members)]
        sample_indices = sorted({by_id[v]['sample_index'] for v in family})
        result.append({'family_id': index, 'candidate_ids': family,
                       'support_count': len(family), 'distinct_resolution_count': len(sample_indices),
                       'sample_indices': sample_indices, 'vector_ids': vector_ids,
                       'note_ids': sorted({note for v in vector_ids for note in source_sets[v]}),
                       'empty_after_consensus': not vector_ids})
    return result


def strict_containment(persistent, source_sets):
    """Deduplicate complete sets, retaining every exact minimal-superset parent."""
    n = len(source_sets)
    if n == 0:
        raise ValueError('containment requires at least one vector')
    all_vectors = tuple(range(n))
    evidence = {all_vectors: []}
    for candidate in persistent:
        members = candidate['vector_ids']
        if members != sorted(set(members)) or any(type(v) is not int or not 0 <= v < n for v in members):
            raise ValueError('persistent vector IDs must be sorted, unique and in range')
        if members:
            evidence.setdefault(tuple(members), []).append(candidate)
    ordered = sorted(evidence, key=lambda members: (-len(members), members))
    groups = []
    for offset, members in enumerate(ordered):
        rows = evidence[members]
        groups.append({'id': n + offset, 'kind': 'root' if offset == 0 else 'persistent',
                       'vector_ids': list(members),
                       'note_ids': sorted({note for v in members for note in source_sets[v]}),
                       'parents': [], 'children': [],
                       'persistence': {
                           'support_count': max((r['support_count'] for r in rows), default=0),
                           'family_ids': sorted(r['family_id'] for r in rows if 'family_id' in r),
                           'distinct_resolution_count': max((r.get('distinct_resolution_count', 0)
                                                             for r in rows), default=0)}})
    sets = [set(g['vector_ids']) for g in groups]
    for child in range(1, len(groups)):
        supersets = [parent for parent in range(child) if sets[child] < sets[parent]]
        direct = [parent for parent in supersets
                  if not any(sets[child] < sets[other] < sets[parent] for other in supersets)]
        for parent in direct:
            groups[child]['parents'].append(groups[parent]['id'])
            groups[parent]['children'].append(groups[child]['id'])
    return groups


def verify_weaver(groups):
    """Cross-check the pinned exact-containment API and forbid upward expansion."""
    import numpy as np
    from hidef.weaver import Weaver

    if len(groups) == 1:
        # The upstream one-input case fails while locating its root. No edges
        # exist in this case; avoid manufacturing a duplicate input to appease it.
        return {'status': 'root_only', 'membership_changes': 0, 'edge_agreement': True}
    n = len(groups[0]['vector_ids'])
    assignment = np.zeros((len(groups), n), dtype=bool)
    for i, group in enumerate(groups):
        assignment[i, group['vector_ids']] = True
    weaver = Weaver()
    tree = weaver.weave(assignment.copy(), terminals=list(range(n)), boolean=True,
                        levels=False, merge=False, cutoff=1., top=100)
    if not np.array_equal(weaver.assignment, assignment):
        raise ValueError('strict Weaver changed a preserved group membership')
    edges = {(groups[tree.nodes[a]['index']]['id'], groups[tree.nodes[b]['index']]['id'])
             for a, b in tree.edges if isinstance(a, tuple) and isinstance(b, tuple)}
    expected = {(group['id'], child) for group in groups for child in group['children']}
    if edges != expected:
        raise ValueError('strict Weaver edges disagree with exact-set transitive reduction')
    return {'status': 'verified', 'membership_changes': 0, 'edge_agreement': True}


def note_projection(groups):
    """Report note-only containment, never silently turn it into vector ancestry."""
    blocked, unchanged = [], []
    by_id = {g['id']: g for g in groups}
    for parent in groups:
        for child_id in parent['children']:
            child = by_id[child_id]
            if parent['note_ids'] == child['note_ids']:
                unchanged.append({'parent': parent['id'], 'child': child_id})
    for parent in groups[1:]:
        parent_notes, parent_vectors = set(parent['note_ids']), set(parent['vector_ids'])
        for child in groups[1:]:
            if child['id'] == parent['id']:
                continue
            child_vectors = set(child['vector_ids'])
            if set(child['note_ids']) <= parent_notes and not child_vectors <= parent_vectors:
                blocked.append({'parent': parent['id'], 'child': child['id'],
                                'equal_note_sets': child['note_ids'] == parent['note_ids'],
                                'blocking_vector_ids': sorted(child_vectors - parent_vectors)})
    return {'unchanged_note_parent_edges': unchanged,
            'note_containment_without_vector_containment': blocked,
            'fewer_than_two_note_groups': [g['id'] for g in groups[1:] if len(g['note_ids']) < 2],
            'policy': 'diagnostics only; no vector memberships or containment edges are changed'}


def dependency_provenance():
    import hidef
    from hidef import hidef_finder, weaver, utils

    dist = importlib.metadata.distribution('hidef')
    direct_url = json.loads(dist.read_text('direct_url.json') or '{}')
    if direct_url.get('vcs_info', {}).get('commit_id') != HIDEF_COMMIT:
        raise ValueError('HiDeF must be installed from the pinned source commit')
    pins = {'igraph': '0.11.9', 'leidenalg': '0.10.2', 'louvain': '0.8.2',
            'numpy': '1.26.4', 'scipy': '1.12.0', 'networkx': '3.2.1',
            'pandas': '2.3.3', 'scikit-learn': '1.7.2'}
    for name, version in pins.items():
        if importlib.metadata.version(name) != version:
            raise ValueError(f'use pinned {name}=={version}')
    return {'hidef_version': hidef.__version__, 'hidef_commit': HIDEF_COMMIT,
            'versions': {d.metadata['Name']: d.version for d in importlib.metadata.distributions()},
            'source_sha256': {Path(module.__file__).name: sha256(module.__file__)
                              for module in (hidef_finder, weaver, utils)}}


def main(argv=None):
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--graph-directory', type=Path, default=root / 'infomap-experiment-v1/I03')
    parser.add_argument('--data-directory', type=Path, default=root / 'real-note-fine-segmentation-v1')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--run-id', default='HDFv1')
    parser.add_argument('--plan', action='store_true', help='validate inputs and print frozen configuration without discovery')
    for key in ('minres', 'maxres', 'density', 'neighbors', 'persistence', 'consensus_percent', 'seed'):
        parser.add_argument('--' + key.replace('_', '-'), type=type(DEFAULTS[key]), default=DEFAULTS[key])
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error('output already exists; previous results must remain unchanged')
    if not args.run_id.strip() or not 1 <= args.seed < 2**31 - 4096:
        parser.error('require nonempty run ID and positive bounded seed')
    if args.persistence < 2 or not 0 <= args.consensus_percent < 100:
        parser.error('require persistence >=2 and 0 <= consensus percent <100')
    started = time.monotonic()
    config = {**DEFAULTS, **{key: getattr(args, key) for key in DEFAULTS if hasattr(args, key)}}
    dependencies = dependency_provenance()
    graph, reference, source_sets, graph_path = load_inputs(args.graph_directory, args.data_directory)
    resolutions, resolution_graph = resolution_schedule(config)
    configuration = {
        'schema_version': 'hidef-configuration-v1', 'run_id': args.run_id, 'method': METHOD,
        'sources': reference['sources'],
        'input_graph': {'path': str(graph_path.resolve()), 'sha256': sha256(graph_path),
                        'vertices': graph.vcount(), 'edges': graph.ecount(),
                        'weight_sum': math.fsum(graph.es['weight'])},
        'input_hierarchy_sha256': sha256(args.graph_directory / 'hierarchy.json'),
        'parameters': config, 'resolutions': resolutions,
        'seed_policy': 'base seed + zero-based sample index; independent fresh partitions',
        'single_resolution_reference_index': min(range(len(resolutions)), key=lambda i: abs(math.log(resolutions[i]))),
        'consensus_similarity': 'strict Jaccard > 0.75 for cluster edges and clique percolation',
        'consensus_membership': 'strict participation > consensus_percent; before containment only',
        'containment': {'cutoff': 1., 'strict_subset': True, 'parent_expansion': False,
                        'transitive_reduction': True, 'multiple_parents': True},
        'dependencies': dependencies, 'python': platform.python_version(),
        'source_code_sha256': sha256(__file__),
        'dependency_lock_sha256': sha256(root / 'hidef-requirements.lock'),
    }
    if args.plan:
        print(json.dumps(configuration, indent=2, allow_nan=False))
        return
    args.output.mkdir(parents=True, exist_ok=False)
    write_json(args.output / 'configuration.json', configuration)
    with (args.output / 'graph.net').open('xb') as stream:
        stream.write(graph_path.read_bytes())
    stage = time.monotonic()
    cluster_graph, candidates, partitions, resolution_graph = discover(graph, source_sets, config)
    discovery_seconds = time.monotonic() - stage
    write_json(args.output / 'raw-partitions.json', {
        'partitions': partitions, 'reference_partition_index': configuration['single_resolution_reference_index'],
        'resolution_edges': sorted([sorted(edge) for edge in resolution_graph.edges])})
    write_json(args.output / 'candidates.json', {'groups': candidates,
        'cluster_graph_edges': sorted([sorted(map(int, edge)) for edge in cluster_graph.edges])})
    stage = time.monotonic()
    persistent = persistent_groups(cluster_graph, candidates, source_sets, config)
    persistence_seconds = time.monotonic() - stage
    write_json(args.output / 'persistent-groups.json', {'groups': persistent,
        'lineage_matches_upstream_consensus': True,
        'empty_group_policy': 'retain here as evidence; cannot form a containment category'})
    stage = time.monotonic()
    groups = strict_containment(persistent, source_sets)
    weaver_check = verify_weaver(groups)
    containment_seconds = time.monotonic() - stage
    write_json(args.output / 'strict-dag.json', {'root': graph.vcount(), 'weaver': weaver_check,
        'edges': [{'parent': group['id'], 'child': child} for group in groups for child in group['children']],
        'groups': groups})
    stage = time.monotonic()
    projection = note_projection(groups)
    write_json(args.output / 'note-projection.json', projection)
    projection_seconds = time.monotonic() - stage
    summary = {'vectors': graph.vcount(), 'notes': len(groups[0]['note_ids']),
               'raw_partitions': len(partitions), 'raw_candidates': len(candidates),
               'raw_total_memberships': sum(len(g['vector_ids']) for g in candidates),
               'persistent_families': len(persistent), 'groups_including_root': len(groups),
               'nonroot_edges': sum(len(g['children']) for g in groups[1:]),
               'multiple_parent_groups': sum(len(g['parents']) > 1 for g in groups),
               'unchanged_note_parent_edges': len(projection['unchanged_note_parent_edges']),
               'note_containment_blocked_pairs': len(projection['note_containment_without_vector_containment'])}
    write_json(args.output / 'hierarchy.json', {
        'schema_version': 'containment-hierarchy-v1', 'run_id': args.run_id, 'method': METHOD,
        'sources': reference['sources'], 'canonical_unique_ids': reference['canonical_unique_ids'],
        'alias_groups': reference['alias_groups'], 'vector_count': graph.vcount(),
        'root': graph.vcount(), 'groups': groups, 'summary': summary})
    write_json(args.output / 'timings.json', {'discovery_seconds': discovery_seconds,
        'persistence_seconds': persistence_seconds, 'containment_seconds': containment_seconds,
        'note_projection_seconds': projection_seconds, 'elapsed_seconds': time.monotonic() - started,
        'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})
    write_json(args.output / 'manifest.json', {
        'sha256': {path.name: sha256(path) for path in sorted(args.output.iterdir())}})
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
