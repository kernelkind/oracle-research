#!/usr/bin/env python3
"""Read-only HDFv3 preservation checks and evidence for resolution extension.

Uses saved memberships only; never clusters, creates labels, or scores meaning.
The primary-seed review sample is fixed independently of the new memberships.
"""

import argparse
from collections import Counter, defaultdict
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path

from compare_hidef_graph_policies import (
    match_groups, read_run, require, sha256, summarize_run, validate_memberships,
)


SEEDS = (123, 124, 125)
ANCHORS = (1046, 951, 976, 1027, 1023, 965, 1037)
EXTRA_GROUPS = (977, 994, 1060, 919, 939, 983)
FROZEN_EDGES = ((965, 1037), (994, 1060), (919, 939), (939, 983))
SATOSHI_PAIR = (187, 691)
SAMPLE_PREFIX = 'HDFv3-resolution-extension-review-v1'
SOURCE_PATHS = {
    'baseline': 'hdbv3-cross-note-edges-v1/response.json',
    'request': 'hdbv3-cross-note-edges-v1/request.json',
    'vector_map': 'vectors/vector-map.json', 'notes': 'reviewed-input.json',
}


def singleton_resolution_bound(edges, vector_count):
    degrees = [0.] * vector_count
    for a, b, weight in edges:
        degrees[a] += weight
        degrees[b] += weight
    total = math.fsum(weight for _, _, weight in edges)
    return max((2 * total * weight / (degrees[a] * degrees[b])
                for a, b, weight in edges), default=0.)


def validate_extension(baseline, extended):
    """Old records, including elapsed times, are immutable; only append samples."""
    old, new = baseline['configuration'], extended['configuration']
    require(extended['graph_bytes'] == baseline['graph_bytes'], 'original graph bytes changed')
    require(new['parameters'] == {**old['parameters'], 'maxres': new['parameters']['maxres']},
            'parameters changed beyond maxres')
    require(new['parameters']['maxres'] > old['parameters']['maxres'], 'maxres was not extended')
    for key in ('method', 'sources', 'input_hierarchy_sha256', 'seed_policy',
                'single_resolution_reference_index', 'consensus_similarity',
                'consensus_membership', 'containment', 'dependencies', 'python',
                'dependency_lock_sha256', 'graph_policy_source_sha256',
                'input_graph', 'graph', 'graph_policy'):
        require(new[key] == old[key], f'configuration changed: {key}')
    for key in ('sources', 'canonical_unique_ids', 'alias_groups', 'vector_count', 'root', 'method'):
        require(extended['hierarchy'][key] == baseline['hierarchy'][key],
                f'source identities changed: {key}')
    count = len(old['resolutions'])
    added = new['resolutions'][count:]
    require(new['resolutions'][:count] == old['resolutions'], 'old resolutions changed')
    require(added and len(set(new['resolutions'])) == len(new['resolutions'])
            and all(math.isfinite(r) and old['parameters']['maxres'] < r <= new['parameters']['maxres']
                    for r in added) and max(added) == new['parameters']['maxres'],
            'invalid added resolutions')
    require(extended['raw']['partitions'][:count] == baseline['raw']['partitions'],
            'old raw partitions changed (including seconds)')
    candidate_count = len(baseline['candidates']['groups'])
    require(extended['candidates']['groups'][:candidate_count] == baseline['candidates']['groups'],
            'old candidates changed')
    require(extended['raw']['reference_partition_index'] == baseline['raw']['reference_partition_index'],
            'old reference partition index changed')
    require(len(extended['raw']['partitions']) == len(new['resolutions']), 'partition count mismatch')
    for index, partition in enumerate(extended['raw']['partitions'][count:], count):
        require(partition['sample_index'] == index and partition['seed'] == old['parameters']['seed'] + index
                and partition['resolution'] == new['resolutions'][index], 'invalid new partition provenance')

    def check_edges(section, key, old_nodes, all_nodes):
        def normalize(edges):
            normalized = set()
            for edge in edges:
                require(len(edge) == 2 and edge[0] != edge[1]
                        and set(edge) <= all_nodes, f'invalid {key}')
                pair = tuple(sorted(edge))
                require(pair not in normalized, f'duplicate {key}')
                normalized.add(pair)
            return normalized
        before = normalize(baseline[section][key])
        after = normalize(extended[section][key])
        require({edge for edge in after if set(edge) <= old_nodes} == before,
                f'old {key} changed')
        return len(after - before)

    resolution_edges = check_edges('raw', 'resolution_edges',
        {f'{r:.4f}' for r in old['resolutions']}, {f'{r:.4f}' for r in new['resolutions']})
    cluster_edges = check_edges('candidates', 'cluster_graph_edges',
        {g['id'] for g in baseline['candidates']['groups']},
        {g['id'] for g in extended['candidates']['groups']})
    ordered = sorted([old['parameters']['maxres']] + added)
    return {'preserved_partition_count': count, 'added_partition_count': len(added),
            'preserved_candidate_count': candidate_count,
            'added_candidate_count': len(extended['candidates']['groups']) - candidate_count,
            'added_resolution_edge_count': resolution_edges, 'added_cluster_edge_count': cluster_edges,
            'boundary_log10_gap': math.log10(ordered[1] / ordered[0]),
            'maximum_added_log10_gap': max(math.log10(b / a) for a, b in zip(ordered, ordered[1:])),
            'old_partition_records_exact_including_seconds': True,
            'old_candidate_records_exact': True, 'old_old_edges_exact': True}


def validate_objectives(run):
    """Independently recompute weighted RBConfiguration quality from the graph."""
    n = run['hierarchy']['vector_count']
    degrees = [0.] * n
    for a, b, weight in run['edges']:
        degrees[a] += weight
        degrees[b] += weight
    total = math.fsum(weight for _, _, weight in run['edges'])
    for partition in run['raw']['partitions']:
        membership = partition['membership']
        group_degrees = defaultdict(float)
        for vector, label in enumerate(membership):
            group_degrees[label] += degrees[vector]
        within = math.fsum(weight for a, b, weight in run['edges'] if membership[a] == membership[b])
        expected = 2 * within - partition['resolution'] * math.fsum(
            degree * degree for degree in group_degrees.values()) / (2 * total)
        require(math.isclose(partition['quality'], expected, rel_tol=1e-10, abs_tol=1e-8),
                f'weighted objective mismatch at sample {partition["sample_index"]}')


def group_record(group):
    return {key: group[key] for key in ('id', 'vector_ids', 'note_ids')}


def compare_group_sets(source, target):
    before = {tuple(g['vector_ids']): g for g in source}
    after = {tuple(g['vector_ids']): g for g in target}
    return {
        'retained': [{'baseline_group_id': before[key]['id'], 'extended_group_id': after[key]['id'],
                      'vector_ids': list(key), 'note_ids': after[key]['note_ids']}
                     for key in sorted(before.keys() & after.keys())],
        'lost': [group_record(before[key]) for key in sorted(before.keys() - after.keys())],
        'added': [group_record(after[key]) for key in sorted(after.keys() - before.keys())],
    }


def raw_stage_summary(candidates, preserved_count):
    before = {tuple(g['vector_ids']) for g in candidates if g['sample_index'] < preserved_count}
    added = [g for g in candidates if g['sample_index'] >= preserved_count]
    new = {tuple(g['vector_ids']): g for g in added if tuple(g['vector_ids']) not in before}
    return {'added_candidate_count': len(added),
            'added_singleton_candidate_count': sum(len(g['vector_ids']) == 1 for g in added),
            'added_multinote_candidate_count': sum(len(g['note_ids']) >= 2 for g in added),
            'new_unique_vector_set_count': len(new),
            'new_unique_multinote_vector_set_count': sum(len(g['note_ids']) >= 2 for g in new.values()),
            'added_candidate_vector_size_counts': dict(sorted(Counter(len(g['vector_ids']) for g in added).items()))}


def ancestor_subgraph(by_id, group_ids):
    found, pending = set(), list(group_ids)
    while pending:
        group_id = pending.pop()
        if group_id in found:
            continue
        found.add(group_id)
        pending.extend(by_id[group_id]['parents'])
    return {'groups': [{'id': i, 'vector_count': len(by_id[i]['vector_ids']),
                        'note_count': len(by_id[i]['note_ids']), 'parents': by_id[i]['parents']}
                       for i in sorted(found)],
            'edges': sorted([p, i] for i in found for p in by_id[i]['parents'])}


def group_evidence(run, group, preserved_count):
    vectors = group['vector_ids']
    raw = [g for g in run['candidates']['groups'] if g['vector_ids'] == vectors]
    families = [g for g in run['persistent']['groups'] if g['vector_ids'] == vectors]
    return {**group_record(group), 'parents': group['parents'], 'children': group['children'],
            'raw_exact_occurrences': [{key: g[key] for key in ('id', 'sample_index', 'resolution', 'seed')}
                                      for g in raw],
            'raw_exact_added_count': sum(g['sample_index'] >= preserved_count for g in raw),
            'persistent_families': [{key: g[key] for key in
                ('family_id', 'support_count', 'sample_indices', 'distinct_resolution_count')}
                for g in families],
            'ancestry': ancestor_subgraph({g['id']: g for g in run['hierarchy']['groups']}, [group['id']])}


def pair_evidence(run, preserved_count):
    pair = set(SATOSHI_PAIR)
    raw = [g for g in run['candidates']['groups'] if pair <= set(g['vector_ids'])]
    persistent = [g for g in run['hierarchy']['groups'] if pair <= set(g['vector_ids'])]
    selected = sorted(persistent, key=lambda g: (len(g['vector_ids']), g['id']))
    smallest = [g for g in selected if len(g['vector_ids']) == len(selected[0]['vector_ids'])]

    def minimum(groups):
        if not groups:
            return None
        g = min(groups, key=lambda g: (len(g['vector_ids']), g['sample_index'], g['id']))
        return {key: g[key] for key in ('id', 'sample_index', 'resolution', 'seed', 'vector_ids', 'note_ids')}

    exact = [g for g in raw if set(g['vector_ids']) == pair]
    return {'canonical_vector_ids': list(SATOSHI_PAIR),
            'exact_raw_occurrences': [{key: g[key] for key in ('id', 'sample_index', 'resolution', 'seed')}
                                      for g in exact],
            'exact_raw_old_count': sum(g['sample_index'] < preserved_count for g in exact),
            'exact_raw_added_count': sum(g['sample_index'] >= preserved_count for g in exact),
            'smallest_raw_shared': minimum(raw),
            'smallest_added_raw_shared': minimum([g for g in raw if g['sample_index'] >= preserved_count]),
            'shared_nonroot_group_count': sum(g['id'] != run['hierarchy']['root'] for g in persistent),
            'smallest_shared_groups': [group_evidence(run, g, preserved_count) for g in smallest]}


def select_added_sample(added):
    result = []
    for low, high in ((2, 4), (5, 14), (15, math.inf)):
        eligible = [g for g in added if low <= len(g['note_ids']) <= high]
        def rank(group):
            identity = ','.join(map(str, group['vector_ids']))
            return hashlib.sha256(f'{SAMPLE_PREFIX}|{identity}'.encode()).hexdigest()
        result.extend({'group_id': g['id'], 'note_count_stratum': f'{low}-{high}', 'selection_sha256': rank(g)}
                      for g in sorted(eligible, key=rank)[:2])
    return result


def validate_provenance(baseline, extended):
    source = Path(baseline['directory'])
    manifest = json.loads((source / 'manifest.json').read_text())['sha256']
    saved = extended['configuration']['extension']
    require(Path(saved['source_directory']).resolve() == source.resolve(), 'extension source directory mismatch')
    require(saved['source_run_id'] == baseline['hierarchy']['run_id'], 'extension source run mismatch')
    require(saved['source_manifest_sha256'] == sha256(source / 'manifest.json')
            and saved['source_artifact_sha256'] == manifest, 'extension source artifact hashes mismatch')
    require(saved['preserved_partition_count'] == len(baseline['raw']['partitions'])
            and saved['preserved_candidate_count'] == len(baseline['candidates']['groups']),
            'extension preserved record counts mismatch')
    old, new = baseline['configuration'], extended['configuration']
    require(saved['previous_maxres'] == old['parameters']['maxres']
            and saved['added_resolutions'] == new['resolutions'][len(old['resolutions']):],
            'extension resolution provenance mismatch')
    bound = singleton_resolution_bound(extended['edges'], extended['hierarchy']['vector_count'])
    require(math.isclose(saved['singleton_resolution_bound'], bound, rel_tol=1e-12),
            'singleton resolution bound mismatch')
    require(saved['endpoint_exceeds_singleton_bound'] is True and new['parameters']['maxres'] > bound,
            'endpoint does not exceed singleton bound')
    return {'source_manifest_sha256': saved['source_manifest_sha256'],
            'source_artifact_sha256': manifest, 'singleton_resolution_bound': bound}


def compare_runs(directory, baseline_directory, data_directory):
    directory, baseline_directory, data_directory = map(Path, (directory, baseline_directory, data_directory))
    primary = read_run(baseline_directory / 'seed123')
    reference = primary['hierarchy']
    for key, relative in SOURCE_PATHS.items():
        require(sha256(data_directory / relative) == reference['sources'][key]['sha256'],
                f'frozen source hash mismatch: {key}')
    vectors = json.loads((data_directory / SOURCE_PATHS['vector_map']).read_text())['vectors']
    by_vector = {v['vector_id']: v for v in vectors}
    require(len(by_vector) == len(vectors)
            and sorted(v for aliases in reference['alias_groups'] for v in aliases) == sorted(by_vector),
            'alias/source vector identity mismatch')
    notes, masks = [], []
    for i, aliases in enumerate(reference['alias_groups']):
        require(aliases[0] == reference['canonical_unique_ids'][i], 'canonical alias mismatch')
        note_ids = {by_vector[v]['note_id'] for v in aliases}
        require(len(note_ids) == 1, 'canonical vector must have one source note')
        notes.append(next(iter(note_ids)))
        masks.append({'canonical_vector_id': i, 'aliases': [
            {key: by_vector[v][key] for key in ('vector_id', 'short_id', 'note_id', 'note_short_id',
                                               'fragments', 'byte_spans')}
            for v in aliases]})
    source_groups = {g['id']: g for g in reference['groups']}
    selected_ids = sorted(set(ANCHORS) | set(EXTRA_GROUPS))
    result = {'schema_version': 'hidef-resolution-extension-comparison-v1',
              'comparison_source_sha256': sha256(__file__),
              'sample': {'anchors': ANCHORS, 'extra_groups': EXTRA_GROUPS, 'edges': FROZEN_EDGES,
                         'satoshi_canonical_vector_ids': SATOSHI_PAIR,
                         'added_selection': f'two lowest SHA256({SAMPLE_PREFIX}|comma-separated canonical vector IDs) per 2-4/5-14/15+ note stratum',
                         'counterpart_pool': 'all saved non-root groups, including one-note groups'},
              'sources': reference['sources'], 'baseline_primary_evidence': [], 'runs': [],
              'interpretation': 'Set correspondences, repeatability, and counts do not score semantic quality. Broad coherent subjects and unexpected logical directions remain valid.',
              'validation_scope': 'Checks saved provenance, graph, partitions, objective, consensus membership and strict containment; does not rerun Leiden or reconstruct persistence families.'}
    used_masks = set(SATOSHI_PAIR)
    repeat = {}
    for group_id in selected_ids:
        evidence = group_evidence(primary, source_groups[group_id], len(primary['raw']['partitions']))
        result['baseline_primary_evidence'].append(evidence)
        used_masks.update(evidence['vector_ids'])
    for seed in SEEDS:
        baseline = primary if seed == 123 else read_run(baseline_directory / f'seed{seed}')
        extended = read_run(directory / f'seed{seed}')
        require(baseline['hierarchy']['run_id'] == f'HDFv2-original-seed{seed}'
                and extended['hierarchy']['run_id'] == f'HDFv3-seed{seed}', 'run identity mismatch')
        require(baseline['configuration']['parameters']['seed'] == seed, 'baseline seed mismatch')
        require(baseline['configuration']['parameters'] == {
            **primary['configuration']['parameters'], 'seed': seed}, 'repeat baseline parameters changed')
        require(extended['configuration']['parameters']['maxres'] == 190., 'HDFv3 endpoint changed')
        audit = validate_extension(baseline, extended)
        audit.update(validate_provenance(baseline, extended))
        for run in (baseline, extended):
            require(run['hierarchy']['canonical_unique_ids'] == reference['canonical_unique_ids']
                    and run['hierarchy']['sources'] == reference['sources'], 'repeat source mismatch')
            validate_memberships(run, notes)
            validate_objectives(run)
        old_groups = [g for g in baseline['hierarchy']['groups'] if g['id'] != reference['root']]
        new_groups = [g for g in extended['hierarchy']['groups'] if g['id'] != reference['root']]
        repeat[seed] = {tuple(g['vector_ids']) for g in new_groups if len(g['note_ids']) >= 2}
        changes = compare_group_sets(old_groups, new_groups)
        by_id = {g['id']: g for g in extended['hierarchy']['groups']}
        matches = []
        selected = set()
        for group_id in selected_ids:
            correspondence = match_groups(source_groups[group_id], new_groups)
            matches.append({'baseline_primary_group_id': group_id, 'matches': correspondence})
            selected.update(m['group_id'] for m in correspondence)
        new_sample = select_added_sample(changes['added']) if seed == 123 else []
        selected.update(row['group_id'] for row in new_sample)
        evidence = [group_evidence(extended, by_id[i], audit['preserved_partition_count']) for i in sorted(selected)]
        for group in evidence:
            used_masks.update(group['vector_ids'])
        pair = pair_evidence(extended, audit['preserved_partition_count'])
        for group in pair['smallest_shared_groups']:
            if group['id'] != reference['root']:
                used_masks.update(group['vector_ids'])
        endpoint = max(extended['raw']['partitions'], key=lambda p: p['resolution'])
        endpoint_sizes = Counter(Counter(endpoint['membership']).values())
        require(endpoint_sizes == {1: reference['vector_count']}, 'endpoint partition is not all singletons')
        result['runs'].append({'seed': seed, 'validation': audit,
            'baseline_summary': summarize_run(baseline, notes), 'extended_summary': summarize_run(extended, notes),
            'raw_added_summary': raw_stage_summary(extended['candidates']['groups'], audit['preserved_partition_count']),
            'persistent_set_changes': changes, 'correspondence': matches, 'selected_evidence': evidence,
            'new_primary_sample': new_sample, 'baseline_satoshi_pair': pair_evidence(baseline, audit['preserved_partition_count']),
            'extended_satoshi_pair': pair,
            'endpoint': {'resolution': endpoint['resolution'], 'seed': endpoint['seed'],
                         'quality': endpoint['quality'], 'group_size_counts': dict(endpoint_sizes)}})
        del extended
    result['repeat_seed_multinote_exact_sets'] = {
        'unique_set_counts': {str(seed): len(repeat[seed]) for seed in SEEDS},
        'pairwise_intersection_counts': {f'{a}-{b}': len(repeat[a] & repeat[b]) for a, b in combinations(SEEDS, 2)},
        'three_seed_intersection_count': len(set.intersection(*repeat.values())),
        'interpretation': 'Excludes single-note groups and the artificial root; repeatability is not semantic quality.'}
    result['mask_evidence'] = [masks[i] for i in sorted(used_masks)]
    result['validation'] = {'all_manifests_sources_graphs_verified': True,
        'old_raw_and_candidate_records_preserved_exactly': True,
        'all_partition_objectives_consensus_memberships_and_strict_dags_verified': True,
        'all_endpoints_all_singletons': True}
    return result


def main(argv=None):
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=root / 'hidef-experiment-v1/HDFv3')
    parser.add_argument('--baseline-directory', type=Path, default=root / 'hidef-experiment-v1/HDFv2/original')
    parser.add_argument('--data-directory', type=Path, default=root / 'real-note-fine-segmentation-v1')
    parser.add_argument('--output', type=Path, help='save JSON to a new file; refuse overwrite (default: stdout)')
    args = parser.parse_args(argv)
    try:
        if args.output is not None:
            require(not args.output.exists(), f'output already exists: {args.output}')
        result = compare_runs(args.directory, args.baseline_directory, args.data_directory)
        serialized = json.dumps(result, indent=2, allow_nan=False) + '\n'
        if args.output is not None:
            with args.output.open('x') as stream:
                stream.write(serialized)
        else:
            print(serialized, end='')
    except (ValueError, KeyError, OSError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    main()
