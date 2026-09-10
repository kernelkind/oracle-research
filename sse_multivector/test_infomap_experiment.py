"""Production graph construction and native Infomap output checks."""

import math
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np

from infomap_experiment import build_graph, run_infomap, summarize_paths


class InfomapExperimentTests(unittest.TestCase):
    def test_dense_graph_preserves_exact_m07_weights_and_exclusions(self):
        d = np.array([[np.inf, .2, np.inf], [.2, np.inf, .7], [np.inf, .7, np.inf]])
        before = d.copy()
        graph = build_graph(d)
        np.testing.assert_array_equal(d, before)
        np.testing.assert_array_equal(graph, [[0, 1-.2/math.pi, 0],
                                             [1-.2/math.pi, 0, 1-.7/math.pi],
                                             [0, 1-.7/math.pi, 0]])

    def test_sparse_graph_is_union_not_mutual_and_never_restores_excluded_edges(self):
        d = np.array([[np.inf, .1, .2, np.inf], [.1, np.inf, .3, .4],
                      [.2, .3, np.inf, .5], [np.inf, .4, .5, np.inf]])
        graph = build_graph(d, neighbors=1)
        self.assertEqual(set(zip(*np.where(np.triu(graph) > 0))), {(0, 1), (0, 2), (1, 3)})
        np.testing.assert_array_equal(graph, graph.T)
        dense = build_graph(d)
        np.testing.assert_array_equal(graph[graph > 0], dense[graph > 0])
        np.testing.assert_array_equal(build_graph(d, neighbors=99), dense)

    def test_equal_distance_neighbors_use_canonical_node_id(self):
        d = np.ones((4, 4))
        np.fill_diagonal(d, np.inf)
        graph = build_graph(d, neighbors=1)
        self.assertEqual(set(zip(*np.where(np.triu(graph) > 0))), {(0, 1), (0, 2), (0, 3)})

    def test_invalid_graphs_are_rejected_before_inference(self):
        for d in (np.array([[np.inf, .1], [.2, np.inf]]),
                  np.array([[np.inf, -1.], [-1., np.inf]]),
                  np.array([[np.inf, math.pi], [math.pi, np.inf]]),
                  np.array([[np.inf, np.nan], [np.nan, np.inf]])):
            with self.subTest(d=d), self.assertRaises(ValueError):
                build_graph(d)
        with self.assertRaises(ValueError):
            build_graph(np.array([[np.inf, .1], [.1, np.inf]]), neighbors=0)

    def test_native_infomap_preserves_every_node_including_isolated_nodes(self):
        graph = np.zeros((7, 7))
        for a, b in [(0, 1), (1, 2), (0, 2), (3, 4), (4, 5), (3, 5)]:
            graph[a, b] = graph[b, a] = 1.
        result, paths = run_infomap(graph, seed=123, trials=2)
        self.assertEqual(sorted(p['node_id'] for p in paths), list(range(7)))
        native = {node.node_id: list(node.path) for node in result.nodes()}
        for p in paths:
            self.assertEqual(p['module_path'], native[p['node_id']][:-1])
        self.assertEqual(len(result.codelengths), 2)

    def test_summary_keeps_native_multiway_nesting_and_alias_notes(self):
        paths = [{'node_id': 0, 'module_path': [1, 1]},
                 {'node_id': 1, 'module_path': [1, 2]},
                 {'node_id': 2, 'module_path': [1, 3]},
                 {'node_id': 3, 'module_path': [2]}]
        groups = summarize_paths(paths, [{'a'}, {'a', 'b'}, {'c'}, {'d'}])
        by_path = {tuple(g['module_path']): g for g in groups}
        self.assertEqual(by_path[()]['id'], 4)
        self.assertEqual(by_path[(1,)]['children'], [6, 7, 8])
        self.assertEqual(by_path[(1,)]['note_ids'], ['a', 'b', 'c'])
        self.assertEqual(by_path[(1,)]['direct_vectors'], [])
        self.assertEqual(by_path[(1, 2)]['direct_vectors'], [1])
        self.assertEqual(by_path[()]['vector_ids'], [0, 1, 2, 3])

    def test_cli_saves_native_output_binds_sources_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            ids = ['a0', 'b0', 'c0']
            result = {'canonical_unique_ids': ids, 'alias_groups': [[v] for v in ids],
                      'algorithm_result': {'vector_count': 3,
                          'mutual_reachability_distances': [0., .3, .5, .3, 0., .4, .5, .4, 0.],
                          'core_distances': [.3, .3, .4],
                          'minimum_spanning_tree': [
                              {'left': 0, 'right': 1, 'mutual_reachability_distance': .3},
                              {'left': 1, 'right': 2, 'mutual_reachability_distance': .4}]}}
            values = {'baseline': {'artifact': {'result': result}},
                      'request': {'source_note_ids': dict(zip(ids, ['a', 'b', 'c']))},
                      'vector_map': {'vectors': [
                          {'vector_id': v, 'note_id': note, 'short_id': f'V{i}',
                           'byte_spans': [[0, 1]], 'fragments': [note]}
                          for i, (v, note) in enumerate(zip(ids, ['a', 'b', 'c']))]},
                      'notes': {'notes': [{'note_id': v, 'text': v} for v in ['a', 'b', 'c']]}}
            sources = {}
            for name, value in values.items():
                path = root / f'{name}.json'
                path.write_text(json.dumps(value))
                sources[name] = {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
            reference = {'method': 'paris_linear_eligible_graph', 'sources': sources,
                         'canonical_unique_ids': ids, 'alias_groups': result['alias_groups']}
            (root / 'M07.json').write_text(json.dumps(reference))
            command = [sys.executable, str(Path(__file__).with_name('infomap_experiment.py')),
                       '--reference', str(root / 'M07.json'), '--output', str(root / 'out'),
                       '--run-id', 'test', '--trials', '2']
            for name, source in sources.items():
                command += ['--' + name.replace('_', '-'), source['path']]
            completed = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            saved = json.loads((root / 'out/hierarchy.json').read_text())
            self.assertEqual(saved['sources'], sources)
            self.assertEqual(saved['canonical_unique_ids'], ids)
            self.assertEqual(saved['alias_groups'], result['alias_groups'])
            self.assertEqual([p['node_id'] for p in saved['paths']], [0, 1, 2])
            config = json.loads((root / 'out/configuration.json').read_text())
            self.assertFalse(config['infomap']['two_level'])
            self.assertEqual(config['graph']['sha256'], hashlib.sha256((root / 'out/graph.net').read_bytes()).hexdigest())
            for filename in ['native.tree', 'native.json']:
                self.assertGreater((root / 'out' / filename).stat().st_size, 0)
            before = {path.name: path.read_bytes() for path in (root / 'out').iterdir()}
            repeated = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(repeated.returncode, 0)
            self.assertIn('output already exists', repeated.stderr)
            self.assertEqual(before, {path.name: path.read_bytes() for path in (root / 'out').iterdir()})
            for source in sources.values():
                self.assertEqual(source['sha256'], hashlib.sha256(Path(source['path']).read_bytes()).hexdigest())
            # A source edit cannot be silently substituted for frozen M07 input.
            (root / 'notes.json').write_text(json.dumps(values['notes']) + '\n')
            command[command.index('--output') + 1] = str(root / 'changed')
            changed = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(changed.returncode, 0)
            self.assertIn('notes changed from the frozen M07 source', changed.stderr)
            self.assertFalse((root / 'changed').exists())


if __name__ == '__main__':
    unittest.main()
