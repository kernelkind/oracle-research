"""Exercise the weighted discovery and strict-containment production paths."""

import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from hidef_experiment import (DEFAULTS, discover, load_inputs, note_projection,
                              persistent_groups, read_graph, resolution_schedule,
                              strict_containment, verify_weaver, weighted_partition)


class StrictContainmentTests(unittest.TestCase):
    def test_exact_memberships_multiple_parents_and_transitive_reduction(self):
        candidates = [
            {'vector_ids': [0, 1, 2], 'support_count': 7},
            {'vector_ids': [0, 1, 3], 'support_count': 6},
            {'vector_ids': [0, 1], 'support_count': 5},
            {'vector_ids': [0], 'support_count': 5},
            {'vector_ids': [0, 1], 'support_count': 8},
        ]
        before = copy.deepcopy(candidates)
        groups = strict_containment(candidates, [{'a'}, {'a'}, {'b'}, {'c'}, {'d'}])
        self.assertEqual(candidates, before)
        by_set = {tuple(g['vector_ids']): g for g in groups}
        self.assertEqual(len(groups), 5)
        self.assertEqual(groups[0]['id'], 5)
        child = by_set[(0, 1)]
        self.assertEqual(child['parents'], [by_set[(0, 1, 2)]['id'], by_set[(0, 1, 3)]['id']])
        self.assertEqual(by_set[(0,)]['parents'], [child['id']])
        self.assertEqual(child['note_ids'], ['a'])
        self.assertEqual(child['persistence']['support_count'], 8)
        self.assertNotIn(by_set[(0,)]['id'], groups[0]['children'])

    def test_note_containment_does_not_create_vector_edges(self):
        candidates = [{'vector_ids': [0, 2], 'support_count': 5},
                      {'vector_ids': [1], 'support_count': 5}]
        groups = strict_containment(candidates, [{'a'}, {'a'}, {'b'}])
        self.assertEqual([g['parents'] for g in groups[1:]], [[3], [3]])
        diagnostics = note_projection(groups)
        blocked = diagnostics['note_containment_without_vector_containment']
        self.assertEqual(len(blocked), 1)
        self.assertEqual(blocked[0]['blocking_vector_ids'], [1])
        self.assertEqual(blocked[0]['parent'], groups[1]['id'])
        self.assertEqual(blocked[0]['child'], groups[2]['id'])

    def test_full_corpus_candidate_is_recorded_at_nonsemantic_root(self):
        groups = strict_containment([{'vector_ids': [0, 1], 'support_count': 9}],
                                    [{'a'}, {'b'}])
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]['kind'], 'root')
        self.assertEqual(groups[0]['vector_ids'], [0, 1])
        self.assertEqual(groups[0]['parents'], [])
        self.assertEqual(groups[0]['persistence']['support_count'], 9)

    def test_actual_weaver_agrees_without_changing_overlapping_sets(self):
        groups = strict_containment([
            {'vector_ids': [0, 1, 2], 'support_count': 5},
            {'vector_ids': [0, 1, 3], 'support_count': 5},
            {'vector_ids': [0, 1], 'support_count': 5}], [{'a'}, {'a'}, {'b'}, {'c'}])
        before = copy.deepcopy(groups)
        self.assertEqual(verify_weaver(groups)['status'], 'verified')
        self.assertEqual(groups, before)


class DiscoveryTests(unittest.TestCase):
    @staticmethod
    def graph():
        import igraph
        graph = igraph.Graph(n=5, edges=[(0, 1), (2, 3), (0, 2), (1, 3)])
        graph.es['weight'] = [10., 10., .1, .1]
        return graph

    def test_production_leiden_uses_exact_weights_and_seed(self):
        import leidenalg
        graph = self.graph()
        original = list(graph.es['weight'])
        partition = weighted_partition(graph, 1., 123)
        expected = leidenalg.find_partition(graph, leidenalg.RBConfigurationVertexPartition,
            weights=original, resolution_parameter=1., seed=123, n_iterations=2)
        unweighted = leidenalg.find_partition(graph, leidenalg.RBConfigurationVertexPartition,
            resolution_parameter=1., seed=123, n_iterations=2)
        self.assertEqual(partition.membership, expected.membership)
        self.assertEqual(partition.quality(), expected.quality())
        self.assertNotAlmostEqual(partition.quality(), unweighted.quality())
        self.assertEqual(graph.es['weight'], original)

    def test_discovery_is_repeatable_and_preserves_singletons_and_isolated_node(self):
        config = {**DEFAULTS, 'minres': .1, 'maxres': 2., 'density': .4,
                  'neighbors': 2, 'persistence': 2}
        sources = [{'a'}, {'b'}, {'c'}, {'d'}, {'e'}]
        first, candidates, partitions, _ = discover(self.graph(), sources, config)
        second, candidates2, partitions2, _ = discover(self.graph(), sources, config)
        self.assertEqual(candidates, candidates2)
        self.assertEqual([p['membership'] for p in partitions], [p['membership'] for p in partitions2])
        self.assertEqual([p['seed'] for p in partitions], list(range(123, 123 + len(partitions))))
        for partition in partitions:
            groups = [g for g in candidates if g['sample_index'] == partition['sample_index']]
            self.assertEqual(sorted(v for g in groups for v in g['vector_ids']), list(range(5)))
            self.assertIn([4], [g['vector_ids'] for g in groups])
        a = persistent_groups(first, candidates, sources, config)
        b = persistent_groups(second, candidates2, sources, config)
        self.assertEqual(a, b)
        self.assertTrue(a)
        self.assertTrue(all(g['support_count'] >= g['distinct_resolution_count'] for g in a))

    def test_consensus_strict_percent_and_native_lineage(self):
        import networkx as nx
        import numpy as np
        from scipy.sparse import csr_matrix
        from hidef import hidef_finder as finder
        config = {**DEFAULTS, 'persistence': 2}
        graph = finder.ClusterGraph()
        graph.graph.update(sim_threshold=.75, num_leaves=5)
        candidates = []
        # Vector 4 occurs in exactly 75% and must be removed, unlike 80%.
        for i, members in enumerate(([0, 1, 2, 3, 4],) * 3 + ([0, 1, 2, 3],)):
            binary = np.zeros((1, 5), dtype=int)
            binary[0, members] = 1
            graph.add_node(i, data=finder.Cluster(csr_matrix(binary), .1 + i))
            candidates.append({'id': i, 'sample_index': i, 'vector_ids': members})
        graph.add_edges_from(nx.complete_graph(4).edges)
        groups = persistent_groups(graph, candidates, [{'a'}] * 5, config)
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]['vector_ids'], [0, 1, 2, 3])
        self.assertEqual(groups[0]['support_count'], 4)


class CliTests(unittest.TestCase):
    def fixture(self, root):
        graph_dir, data_dir = root / 'graph', root / 'data'
        graph_dir.mkdir()
        values = {
            'baseline': ('hdbv3-cross-note-edges-v1/response.json', {}),
            'request': ('hdbv3-cross-note-edges-v1/request.json', {}),
            'vector_map': ('vectors/vector-map.json', {'vectors': [
                {'vector_id': f'v{i}', 'note_id': f'n{i}', 'short_id': f'V{i}'} for i in range(5)]}),
            'notes': ('reviewed-input.json', {'notes': [{'note_id': f'n{i}', 'text': f'note {i}'} for i in range(5)]}),
        }
        sources = {}
        for name, (filename, value) in values.items():
            path = data_dir / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(value))
            sources[name] = {'path': '/historical/' + filename,
                             'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        graph_path = graph_dir / 'graph.net'
        graph_path.write_text('*Vertices 5\n' + ''.join(f'{i} "v{i}"\n' for i in range(5))
                              + '*Edges\n0 1 10\n0 2 0.1\n1 3 0.1\n2 3 10\n')
        hierarchy = {'schema_version': 'infomap-hierarchy-v1', 'run_id': 'I03', 'sources': sources,
                     'vector_count': 5, 'canonical_unique_ids': [f'v{i}' for i in range(5)],
                     'alias_groups': [[f'v{i}'] for i in range(5)]}
        (graph_dir / 'hierarchy.json').write_text(json.dumps(hierarchy))
        (graph_dir / 'configuration.json').write_text(json.dumps({'sources': sources,
            'graph': {'sha256': hashlib.sha256(graph_path.read_bytes()).hexdigest(), 'undirected_edges': 4}}))
        return graph_dir, data_dir, hierarchy

    def test_zero_based_graph_weights_and_source_hash_rejection(self):
        with tempfile.TemporaryDirectory() as temporary:
            graph_dir, data_dir, reference = self.fixture(Path(temporary))
            graph, loaded, sources, _ = load_inputs(graph_dir, data_dir)
            self.assertEqual(graph.vcount(), 5)
            self.assertEqual(graph.es['weight'], [10., .1, .1, 10.])
            self.assertEqual(loaded, reference)
            self.assertEqual(sources, [{f'n{i}'} for i in range(5)])
            (data_dir / 'reviewed-input.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'source checksum mismatch: notes'):
                load_inputs(graph_dir, data_dir)

    def test_graph_parser_rejects_identity_changes_and_invalid_edges(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'graph.net'
            for body, message in [
                ('*Vertices 2\n1 "v0"\n2 "v1"\n*Edges\n0 1 1\n', 'identity mismatch'),
                ('*Vertices 2\n0 "v0"\n1 "v1"\n*Edges\n0 1 nan\n', 'positive finite'),
                ('*Vertices 2\n0 "v0"\n1 "v1"\n*Edges\n0 1 1\n0 1 2\n', 'duplicate graph edge')]:
                path.write_text(body)
                with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                    read_graph(path, ['v0', 'v1'])

    def test_cli_writes_all_stages_refuses_overwrite_and_repeats_memberships(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            graph_dir, data_dir, reference = self.fixture(root)
            command = [sys.executable, str(Path(__file__).with_name('hidef_experiment.py')),
                       '--graph-directory', str(graph_dir), '--data-directory', str(data_dir),
                       '--minres', '.1', '--maxres', '2', '--density', '.4', '--neighbors', '2',
                       '--persistence', '2', '--output', str(root / 'out')]
            planned = subprocess.run(command + ['--plan'], capture_output=True, text=True)
            self.assertEqual(planned.returncode, 0, planned.stderr)
            self.assertFalse((root / 'out').exists())
            run = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            output = root / 'out'
            expected = {'configuration.json', 'graph.net', 'raw-partitions.json', 'candidates.json',
                        'persistent-groups.json', 'strict-dag.json', 'note-projection.json',
                        'hierarchy.json', 'timings.json', 'manifest.json'}
            self.assertEqual({p.name for p in output.iterdir()}, expected)
            hierarchy = json.loads((output / 'hierarchy.json').read_text())
            for key in ('sources', 'canonical_unique_ids', 'alias_groups'):
                self.assertEqual(hierarchy[key], reference[key])
            before = {p.name: p.read_bytes() for p in output.iterdir()}
            repeated = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(repeated.returncode, 0)
            self.assertIn('output already exists', repeated.stderr)
            self.assertEqual(before, {p.name: p.read_bytes() for p in output.iterdir()})
            command[-1] = str(root / 'repeat')
            repeated = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(repeated.returncode, 0, repeated.stderr)
            self.assertEqual(hierarchy, json.loads((root / 'repeat/hierarchy.json').read_text()))


class LauncherTests(unittest.TestCase):
    def test_launcher_freezes_settings_and_separate_seed_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            script = root / 'sse_multivector/run-hidef-experiment.sh'
            script.parent.mkdir()
            shutil.copy2(Path(__file__).with_name(script.name), script)
            binary = root / 'bin/nix'
            binary.parent.mkdir()
            binary.write_text('#!/usr/bin/env bash\nprintf "%s\\n" "$@"\n')
            binary.chmod(0o755)
            env = {**os.environ, 'PATH': str(binary.parent) + os.pathsep + os.environ['PATH']}
            for seed in (123, 124, 125):
                command = [str(script), str(seed), str(root / f'seed{seed}'), '--plan']
                result = subprocess.run(command, env=env, cwd='/', capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                args = result.stdout.splitlines()
                self.assertIn('HDFv1-seed' + str(seed), args)
                self.assertIn(str(root / 'sse_multivector/hidef-requirements.lock'), args)
                self.assertEqual(args[-13:], ['--minres', '.001', '--maxres', '25', '--density', '.1',
                    '--neighbors', '10', '--persistence', '5', '--consensus-percent', '75', '--plan'])
            rejected = subprocess.run([str(script), '126', str(root / 'unknown')], env=env,
                                      capture_output=True, text=True)
            self.assertEqual(rejected.returncode, 2)


if __name__ == '__main__':
    unittest.main()
