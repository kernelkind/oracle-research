#!/usr/bin/env python3
"""Validate the frozen HDFv2 artifacts and print structural comparisons as JSON.

Read-only, standard-library only: no graph optimization or semantic scoring.
All non-root groups, including one-note groups, participate in correspondence.
"""

import argparse
from collections import Counter, defaultdict
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path
import shlex


POLICIES = ('original', 'mutual_best_per_note', 'strongest_edges_matched')
SEEDS = (123, 124, 125)
ANCHORS = (1046, 951, 976, 1027, 1023, 965, 1037)
EXTRA_GROUPS = (1071, 1030, 1151, 1055, 1069, 994, 977, 995, 923, 938, 931, 939)
EXTRA_EDGES = ((965, 1071), (1005, 1030), (929, 1151), (997, 1055),
               (994, 1060), (923, 1134), (938, 975), (931, 950),
               (919, 939), (939, 983))
FILES = ('configuration.json', 'graph.net', 'hierarchy.json', 'raw-partitions.json',
         'candidates.json', 'persistent-groups.json', 'strict-dag.json',
         'note-projection.json', 'timings.json')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def read_run(directory):
    """Verify every manifested file and the saved graph's exact identities."""
    directory = Path(directory)
    manifest = json.loads((directory / 'manifest.json').read_text())['sha256']
    require(set(FILES) <= set(manifest), f'{directory}: incomplete manifest')
    for name, digest in manifest.items():
        require(Path(name).name == name and sha256(directory / name) == digest,
                f'{directory}: manifest mismatch for {name}')
    names = {'configuration': 'configuration.json', 'hierarchy': 'hierarchy.json',
             'raw': 'raw-partitions.json', 'candidates': 'candidates.json',
             'persistent': 'persistent-groups.json', 'dag': 'strict-dag.json'}
    run = {key: json.loads((directory / name).read_text()) for key, name in names.items()}
    run['directory'] = str(directory)
    graph = (directory / 'graph.net').read_bytes()
    config, hierarchy = run['configuration'], run['hierarchy']
    metadata = config.get('graph', config.get('input_graph'))
    require(hashlib.sha256(graph).hexdigest() == metadata['sha256'],
            f'{directory}: graph hash mismatch')
    n = hierarchy['vector_count']
    lines = graph.decode().splitlines()
    require(len(lines) >= n + 2 and lines[0] == f'*Vertices {n}'
            and lines[n + 1] == '*Edges', f'{directory}: graph header mismatch')
    require(len(hierarchy['canonical_unique_ids']) == n, 'canonical identity count mismatch')
    for i, identity in enumerate(hierarchy['canonical_unique_ids']):
        require(shlex.split(lines[i + 1]) == [str(i), identity], 'graph vertex identity mismatch')
    edges = []
    seen = set()
    for line in lines[n + 2:]:
        fields = line.split()
        require(len(fields) == 3, 'invalid graph edge')
        a, b, weight = int(fields[0]), int(fields[1]), float(fields[2])
        require(0 <= a < b < n and math.isfinite(weight) and weight > 0
                and (a, b) not in seen, 'invalid or duplicate graph edge')
        seen.add((a, b))
        edges.append((a, b, weight))
    require(metadata['vertices'] == n and metadata['edges'] == len(edges), 'graph count mismatch')
    require(math.isclose(metadata['weight_sum'], math.fsum(e[2] for e in edges),
                         rel_tol=1e-12, abs_tol=1e-12), 'graph weight sum mismatch')
    run.update(graph_bytes=graph, edges=edges)
    return run


def validate_graph_policy(run, original, notes):
    """Independently check the selected indices and byte-preserving restriction."""
    config = run['configuration']
    audit = config['graph_policy']
    edges = original['edges']
    require(config['input_graph']['sha256'] == hashlib.sha256(original['graph_bytes']).hexdigest(),
            'original graph hash mismatch')
    best = [{} for _ in notes]
    for a, b, weight in edges:
        require(notes[a] != notes[b], 'same-note edge in original graph')
        for i, j in ((a, b), (b, a)):
            rank = (-weight, j)
            if notes[j] not in best[i] or rank < best[i][notes[j]]:
                best[i][notes[j]] = rank
    mutual = [i for i, (a, b, _) in enumerate(edges)
              if best[a][notes[b]][1] == b and best[b][notes[a]][1] == a]
    policy = audit['policy']
    require(policy in POLICIES, 'unknown graph policy')
    expected = list(range(len(edges))) if policy == 'original' else mutual
    if policy == 'strongest_edges_matched':
        expected = sorted(sorted(range(len(edges)),
                                 key=lambda i: (-edges[i][2], edges[i][0], edges[i][1]))[:len(mutual)])
    require(audit['retained_original_edge_indices'] == expected, 'retained original edge indices mismatch')
    retained = set(expected)
    require(audit['removed_original_edge_indices'] == [i for i in range(len(edges)) if i not in retained],
            'removed original edge indices mismatch')
    start = len(notes) + 2
    lines = original['graph_bytes'].splitlines(keepends=True)
    expected_bytes = b''.join(lines[:start] + [lines[start + i] for i in expected])
    require(run['graph_bytes'] == expected_bytes, 'actual graph bytes disagree with original edge indices')


def validate_memberships(run, notes):
    """Check partition coverage, consensus lineage and the exact containment DAG."""
    config, hierarchy = run['configuration'], run['hierarchy']
    n = len(notes)

    def check_group(group):
        vectors = group['vector_ids']
        require(vectors == sorted(set(vectors)) and all(0 <= i < n for i in vectors),
                'invalid group vector membership')
        require(group['note_ids'] == sorted({notes[i] for i in vectors}), 'group note projection mismatch')

    candidates = run['candidates']['groups']
    by_candidate = {g['id']: g for g in candidates}
    require(len(by_candidate) == len(candidates), 'duplicate raw candidate ID')
    for group in candidates:
        check_group(group)
    partitions = run['raw']['partitions']
    require(len(partitions) == len(config['resolutions']), 'resolution count mismatch')
    require(run['raw']['reference_partition_index'] == config['single_resolution_reference_index'],
            'single-resolution reference mismatch')
    degrees = Counter(v for a, b, _ in run['edges'] for v in (a, b))
    isolates = [i for i in range(n) if not degrees[i]]
    seen_candidates = []
    for index, partition in enumerate(partitions):
        require(partition['sample_index'] == index and partition['resolution'] == config['resolutions'][index]
                and partition['seed'] == config['parameters']['seed'] + index, 'partition resolution/seed mismatch')
        membership = partition['membership']
        require(len(membership) == n and all(isinstance(x, int) and x >= 0 for x in membership),
                'partition does not cover every vector')
        communities = defaultdict(list)
        for vector, label in enumerate(membership):
            communities[label].append(vector)
        require(all(len(communities[membership[i]]) == 1 for i in isolates), 'isolate was not preserved as singleton')
        saved = [by_candidate[i] for i in partition['candidate_ids']]
        require(sorted(tuple(g['vector_ids']) for g in saved) == sorted(map(tuple, communities.values())),
                'raw candidate/partition coverage mismatch')
        require(all(g['sample_index'] == index and g['resolution'] == partition['resolution']
                    and g['seed'] == partition['seed'] for g in saved), 'candidate provenance mismatch')
        seen_candidates.extend(partition['candidate_ids'])
    require(sorted(seen_candidates) == sorted(by_candidate), 'raw candidates omitted or reused')
    for group in run['persistent']['groups']:
        check_group(group)
        family = [by_candidate[i] for i in group['candidate_ids']]
        require(len(family) == group['support_count'] and len(family) >= config['parameters']['persistence'],
                'persistent support mismatch')
        samples = sorted({g['sample_index'] for g in family})
        require(samples == group['sample_indices'] and len(samples) == group['distinct_resolution_count'],
                'distinct-resolution support mismatch')
        counts = Counter(v for g in family for v in g['vector_ids'])
        expected = sorted(v for v, count in counts.items()
                          if 100 * count > config['parameters']['consensus_percent'] * len(family))
        require(group['vector_ids'] == expected, 'persistent consensus membership mismatch')
    groups = hierarchy['groups']
    by_id = {g['id']: g for g in groups}
    require(len(by_id) == len(groups) and hierarchy['root'] == n
            and groups[0]['id'] == n and groups[0]['vector_ids'] == list(range(n)), 'invalid root/group IDs')
    for group in groups:
        check_group(group)
    sets = {g['id']: set(g['vector_ids']) for g in groups}
    require(len({tuple(g['vector_ids']) for g in groups}) == len(groups), 'duplicate DAG memberships')
    expected_sets = {tuple(g['vector_ids']) for g in run['persistent']['groups'] if g['vector_ids']}
    expected_sets.add(tuple(range(n)))
    require({tuple(g['vector_ids']) for g in groups} == expected_sets,
            'persistent memberships and DAG memberships differ')
    for group in groups:
        possible = sorted((g for g in groups if sets[group['id']] < sets[g['id']]),
                          key=lambda g: (len(g['vector_ids']), g['id']))
        parents = []
        for candidate in possible:
            if not any(sets[p] < sets[candidate['id']] for p in parents):
                parents.append(candidate['id'])
        require(group['parents'] == sorted(parents), 'DAG is not exact reduced strict containment')
        require(group['children'] == sorted(g['id'] for g in groups if group['id'] in g['parents']),
                'DAG parents/children disagree')
    dag = run['dag']
    require(dag['root'] == n and dag['groups'] == groups, 'hierarchy/strict DAG mismatch')
    require(dag['edges'] == [{'parent': g['id'], 'child': c} for g in groups for c in g['children']],
            'saved DAG edges mismatch')


def validate_replay(reference, replay):
    """Require exact saved discovery/consensus/DAG data, except elapsed timings."""
    def raw_without_times(run):
        return {**run['raw'], 'partitions': [
            {key: value for key, value in partition.items() if key != 'seconds'}
            for partition in run['raw']['partitions']]}
    require(raw_without_times(reference) == raw_without_times(replay), 'original replay raw partitions differ')
    for key in ('candidates', 'persistent'):
        require(reference[key] == replay[key], f'original replay {key} differ')
    for key in ('root', 'groups', 'edges'):
        require(reference['dag'][key] == replay['dag'][key], f'original replay DAG {key} differ')
    require(reference['hierarchy']['groups'] == replay['hierarchy']['groups'], 'original replay hierarchy differs')
    return True


def summarize_run(run, notes):
    hierarchy = run['hierarchy']
    groups = [g for g in hierarchy['groups'] if g['id'] != hierarchy['root']]
    displayed = [g for g in groups if len(g['note_ids']) >= 2]
    by_id = {g['id']: g for g in displayed}
    display_edges = [(g, by_id[c]) for g in displayed for c in g['children'] if c in by_id]
    adjacency = [set() for _ in notes]
    for a, b, _ in run['edges']:
        adjacency[a].add(b)
        adjacency[b].add(a)
    unseen, components = set(range(len(notes))), []
    while unseen:
        pending = [min(unseen)]
        unseen.remove(pending[0])
        size = 0
        while pending:
            vector = pending.pop()
            size += 1
            neighbors = adjacency[vector] & unseen
            unseen.difference_update(neighbors)
            pending.extend(neighbors)
        components.append(size)
    isolates = [i for i, neighbors in enumerate(adjacency) if not neighbors]

    def coverage(selected):
        covered = {note for group in selected for note in group['note_ids']}
        return {'note_count': len(covered), 'missing_note_ids': sorted(set(notes) - covered)}

    def sizes(selected):
        return {key: dict(sorted(Counter(len(g[key]) for g in selected).items()))
                for key in ('vector_ids', 'note_ids')}

    return {
        'run_id': hierarchy['run_id'], 'directory': run['directory'],
        'groups_including_root': len(groups) + 1, 'nonroot_groups': len(groups),
        'displayed_nonroot_groups': len(displayed),
        'root_children': len(hierarchy['groups'][0]['children']),
        'displayed_root_children': sum(c in by_id for c in hierarchy['groups'][0]['children']),
        'nonroot_note_coverage': coverage(groups), 'displayed_note_coverage': coverage(displayed),
        'nonroot_size_distribution': sizes(groups), 'displayed_size_distribution': sizes(displayed),
        'displayed_nonroot_edges': len(display_edges),
        'displayed_edges_fewer_notes': sum(len(c['note_ids']) < len(p['note_ids']) for p, c in display_edges),
        'displayed_edges_same_note_set': sum(p['note_ids'] == c['note_ids'] for p, c in display_edges),
        'graph_edges': len(run['edges']), 'isolated_vector_ids': isolates,
        'isolated_vector_count': len(isolates),
        'nonisolated_note_count': len({notes[i] for i, neighbors in enumerate(adjacency) if neighbors}),
        'component_count': len(components), 'component_sizes': sorted(components, reverse=True),
    }


def match_groups(source, targets):
    """Top two vector matches plus top note match; all non-root sets are eligible."""
    source_vectors, source_notes = set(source['vector_ids']), set(source['note_ids'])
    matches = []
    for target in targets:
        vectors, notes = set(target['vector_ids']), set(target['note_ids'])
        matches.append({
            'group_id': target['id'], 'vector_count': len(vectors), 'note_count': len(notes),
            'displayed': len(notes) >= 2,
            'vector_jaccard': len(vectors & source_vectors) / len(vectors | source_vectors),
            'note_jaccard': len(notes & source_notes) / len(notes | source_notes),
            'exact_vector_set': vectors == source_vectors, 'exact_note_set': notes == source_notes,
            'added_vector_ids': sorted(vectors - source_vectors),
            'removed_vector_ids': sorted(source_vectors - vectors),
            'added_note_ids': sorted(notes - source_notes), 'removed_note_ids': sorted(source_notes - notes),
            'selected_by': [],
        })
    selected = {}
    for key, count, prefix in (('vector_jaccard', 2, 'vector'), ('note_jaccard', 1, 'note')):
        for rank, match in enumerate(sorted(matches, key=lambda m: (-m[key], m['group_id']))[:count], 1):
            selected.setdefault(match['group_id'], match)['selected_by'].append(f'{prefix}_rank_{rank}')
    return list(selected.values())


def compare_runs(directory, reference_directory, data_directory):
    directory, reference_directory, data_directory = map(Path, (directory, reference_directory, data_directory))
    paths = [directory / policy / f'seed{seed}' for policy in POLICIES for seed in SEEDS]
    for path in paths + [reference_directory / f'seed{seed}' for seed in SEEDS]:
        require((path / 'manifest.json').is_file(), f'incomplete run: {path}')
    primary = read_run(reference_directory / 'seed123')
    reference = primary['hierarchy']
    source_paths = {
        'baseline': 'hdbv3-cross-note-edges-v1/response.json',
        'request': 'hdbv3-cross-note-edges-v1/request.json',
        'vector_map': 'vectors/vector-map.json', 'notes': 'reviewed-input.json',
    }
    for key, relative in source_paths.items():
        require(sha256(data_directory / relative) == reference['sources'][key]['sha256'],
                f'original source hash mismatch: {key}')
    vectors = json.loads((data_directory / source_paths['vector_map']).read_text())['vectors']
    by_vector = {v['vector_id']: v['note_id'] for v in vectors}
    aliases = reference['alias_groups']
    require(len(by_vector) == len(vectors) and sorted(v for group in aliases for v in group) == sorted(by_vector),
            'alias/source vector identity mismatch')
    notes = []
    for i, aliases_for_vector in enumerate(aliases):
        require(aliases_for_vector[0] == reference['canonical_unique_ids'][i], 'canonical alias mismatch')
        sources = {by_vector[v] for v in aliases_for_vector}
        require(len(sources) == 1, 'canonical vector must have exactly one source note')
        notes.append(next(iter(sources)))
    base = primary['configuration']
    invariant_config = ('method', 'sources', 'input_hierarchy_sha256', 'resolutions',
                        'seed_policy', 'single_resolution_reference_index', 'consensus_similarity',
                        'consensus_membership', 'containment', 'dependencies', 'python', 'dependency_lock_sha256')
    summaries, saved_groups, replay_checks = [], {}, {}
    code_hashes = None
    for seed in SEEDS:
        original = primary if seed == 123 else read_run(reference_directory / f'seed{seed}')
        for policy in (None,) + POLICIES:
            run = original if policy is None else read_run(directory / policy / f'seed{seed}')
            config, hierarchy = run['configuration'], run['hierarchy']
            for key in ('sources', 'canonical_unique_ids', 'alias_groups', 'vector_count', 'root', 'method'):
                require(hierarchy[key] == reference[key], f'{run["directory"]}: source/identity mismatch: {key}')
            require(config['parameters'] == {**base['parameters'], 'seed': seed}, 'parameters changed beyond seed')
            for key in invariant_config:
                require(config[key] == base[key], f'configuration mismatch: {key}')
            require(run['raw']['resolution_edges'] == primary['raw']['resolution_edges'],
                    'resolution-neighbor graph changed')
            expected_id = f'HDFv1-seed{seed}' if policy is None else f'HDFv2-{policy}-seed{seed}'
            require(hierarchy['run_id'] == config['run_id'] == expected_id, 'run identity mismatch')
            validate_memberships(run, notes)
            if policy is None:
                require(run['graph_bytes'] == primary['graph_bytes'], 'reference graphs differ')
                continue
            hashes = (config['source_code_sha256'], config['graph_policy_source_sha256'])
            code_hashes = hashes if code_hashes is None else code_hashes
            require(hashes == code_hashes, 'HDFv2 code changed between runs')
            require(config['graph_policy']['policy'] == policy, 'policy/directory mismatch')
            validate_graph_policy(run, original, notes)
            if policy == 'original':
                replay_checks[str(seed)] = validate_replay(original, run)
            summary = summarize_run(run, notes)
            summary.update(policy=policy, seed=seed)
            summaries.append(summary)
            saved_groups[(policy, seed)] = [g for g in hierarchy['groups'] if g['id'] != hierarchy['root']]
    source_groups = {g['id']: g for g in reference['groups']}
    selected_ids = sorted(set(ANCHORS) | set(EXTRA_GROUPS) | {v for edge in EXTRA_EDGES for v in edge})
    correspondence = []
    for group_id in selected_ids:
        source = source_groups[group_id]
        correspondence.append({
            'reference_group_id': group_id, 'reference_vector_ids': source['vector_ids'],
            'reference_note_ids': source['note_ids'],
            'matches_by_run': {f'HDFv2-{policy}-seed{seed}': match_groups(source, saved_groups[(policy, seed)])
                               for policy in POLICIES for seed in SEEDS}})
    repeat = {}
    for policy in POLICIES:
        repeat[policy] = {}
        for key in ('vector_ids', 'note_ids'):
            sets = {seed: {tuple(g[key]) for g in saved_groups[(policy, seed)]} for seed in SEEDS}
            repeat[policy][key] = {
                'unique_set_counts': {str(seed): len(sets[seed]) for seed in SEEDS},
                'pairwise_intersection_counts': {f'{a}-{b}': len(sets[a] & sets[b]) for a, b in combinations(SEEDS, 2)},
                'three_seed_intersection_count': len(set.intersection(*sets.values())),
            }
    return {
        'schema_version': 'hidef-graph-policy-comparison-v1',
        'validation': {'all_manifests_and_sources_verified': True,
                       'all_partition_and_consensus_memberships_verified': True,
                       'all_strict_dags_verified': True, 'original_policy_replay_exact': replay_checks},
        'parameters_except_seed': {k: v for k, v in base['parameters'].items() if k != 'seed'},
        'resolution_count': len(base['resolutions']),
        'reference_resolution': base['resolutions'][base['single_resolution_reference_index']],
        'sample': {'anchors': ANCHORS, 'extra_groups': EXTRA_GROUPS, 'extra_edges': EXTRA_EDGES,
                   'counterpart_pool': 'all saved non-root groups, including one-note groups'},
        'runs': summaries, 'correspondence': correspondence, 'repeat_seed_exact_sets': repeat,
        'validation_scope': 'Checks saved partitions and lineage memberships; does not rerun Leiden or construct persistence families.',
        'interpretation': 'Set correspondences and structural counts are not semantic quality scores.',
    }


def main(argv=None):
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=root / 'hidef-experiment-v1/HDFv2')
    parser.add_argument('--reference-directory', type=Path, default=root / 'hidef-experiment-v1/HDFv1')
    parser.add_argument('--data-directory', type=Path, default=root / 'real-note-fine-segmentation-v1')
    args = parser.parse_args(argv)
    try:
        result = compare_runs(args.directory, args.reference_directory, args.data_directory)
    except (ValueError, KeyError, OSError) as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
