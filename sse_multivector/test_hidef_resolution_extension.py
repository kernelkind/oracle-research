"""Range extension reuses frozen discovery evidence through production paths."""

import contextlib
import copy
import io
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import hidef_experiment as experiment
from test_hidef_experiment import CliTests, DiscoveryTests


class ResolutionExtensionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        graph, data, _ = CliTests().fixture(self.root)
        self.source = self.root / 'source'
        self.output = self.root / 'extended'
        self.arguments = ['--graph-directory', str(graph), '--data-directory', str(data),
                          '--minres', '.1', '--density', '.4', '--neighbors', '2',
                          '--persistence', '2']
        with contextlib.redirect_stdout(io.StringIO()):
            experiment.main(self.arguments + ['--maxres', '2', '--output', str(self.source)])

    def extend(self, *extra):
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            experiment.main(self.arguments + ['--maxres', '5', '--extend-from', str(self.source),
                            '--output', str(self.output), *extra])
        return stdout.getvalue()

    def read(self, directory, name):
        return json.loads((directory / name).read_text())

    def rewrite_source(self, name, value):
        (self.source / name).write_text(json.dumps(value))
        manifest = self.read(self.source, 'manifest.json')
        manifest['sha256'][name] = experiment.sha256(self.source / name)
        (self.source / 'manifest.json').write_text(json.dumps(manifest))

    def test_extension_replays_every_frozen_row_and_only_optimizes_new_resolutions(self):
        source_bytes = {path.name: path.read_bytes() for path in self.source.iterdir()}
        old = self.read(self.source, 'raw-partitions.json')
        old_candidates = self.read(self.source, 'candidates.json')
        old_config = self.read(self.source, 'configuration.json')
        with mock.patch.object(experiment, 'weighted_partition', wraps=experiment.weighted_partition) as optimizer:
            self.extend()
        actual = self.read(self.output, 'raw-partitions.json')
        candidates = self.read(self.output, 'candidates.json')
        config = self.read(self.output, 'configuration.json')
        count = len(old['partitions'])
        added = actual['partitions'][count:]
        self.assertTrue(added)
        self.assertEqual(actual['partitions'][:count], old['partitions'])
        self.assertEqual(candidates['groups'][:len(old_candidates['groups'])], old_candidates['groups'])
        expected, _ = experiment.resolution_schedule({**old_config['parameters'], 'minres': 2., 'maxres': 5.})
        self.assertEqual([row['resolution'] for row in added], [value for value in expected if value > 2.])
        self.assertEqual([call.args[1] for call in optimizer.call_args_list], [row['resolution'] for row in added])
        self.assertEqual([row['seed'] for row in added], list(range(123 + count, 123 + count + len(added))))
        old_edges = {tuple(edge) for edge in old['resolution_edges']}
        old_keys = {f"{row['resolution']:.4f}" for row in old['partitions']}
        new_edges = {tuple(edge) for edge in actual['resolution_edges']}
        self.assertEqual({edge for edge in new_edges if set(edge) <= old_keys}, old_edges)
        self.assertTrue(any((a in old_keys) != (b in old_keys) for a, b in new_edges))
        self.assertEqual(config['resolutions'][:count], old_config['resolutions'])
        self.assertEqual(config['extension']['source_manifest_sha256'], experiment.sha256(self.source / 'manifest.json'))
        self.assertEqual(config['extension']['source_artifact_sha256'], self.read(self.source, 'manifest.json')['sha256'])
        self.assertTrue(config['extension']['endpoint_exceeds_singleton_bound'])
        self.assertEqual(source_bytes, {path.name: path.read_bytes() for path in self.source.iterdir()})
        self.assertEqual((self.output / 'graph.net').read_bytes(), (self.source / 'graph.net').read_bytes())
        for name, digest in self.read(self.output, 'manifest.json')['sha256'].items():
            self.assertEqual(experiment.sha256(self.output / name), digest)

    def test_plan_records_graph_bound_without_discovery_or_output(self):
        with mock.patch.object(experiment, 'weighted_partition', side_effect=AssertionError('optimizer called')):
            planned = json.loads(self.extend('--plan'))
        self.assertFalse(self.output.exists())
        self.assertAlmostEqual(planned['extension']['singleton_resolution_bound'], 40.4 * 10 / 10.1**2)
        self.assertLessEqual(planned['extension']['boundary_log10_gap'], planned['parameters']['density'])

    def test_incompatible_parameters_or_graph_policy_are_rejected_before_output(self):
        for arguments, field in [(['--seed', '124'], 'seed'), (['--density', '.5'], 'density'),
                                 (['--maxres', '2'], 'maxres'),
                                 (['--graph-policy', 'mutual_best_per_note'], 'graph')]:
            with self.subTest(arguments=arguments), self.assertRaisesRegex(ValueError, field):
                self.extend(*arguments)
            self.assertFalse(self.output.exists())

    def test_manifest_corruption_is_rejected_before_output(self):
        (self.source / 'raw-partitions.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'checksum.*raw-partitions.json'):
            self.extend()
        self.assertFalse(self.output.exists())

    def test_internally_inconsistent_frozen_membership_is_rejected_before_output(self):
        original = self.read(self.source, 'raw-partitions.json')
        for field, value in [('seed', 900), ('membership', [0] * 5), ('quality', math.inf)]:
            broken = copy.deepcopy(original)
            broken['partitions'][-1][field] = value
            self.rewrite_source('raw-partitions.json', broken)
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'partition|candidate'):
                self.extend()
            self.assertFalse(self.output.exists())

    def test_partial_extension_records_that_endpoint_does_not_exceed_bound(self):
        planned = json.loads(self.extend('--maxres', '3', '--plan'))
        self.assertFalse(planned['extension']['endpoint_exceeds_singleton_bound'])


class SingletonResolutionBoundTests(unittest.TestCase):
    def test_graph_bound_handles_isolates_and_weight_scaling(self):
        graph = DiscoveryTests.graph()
        expected = 40.4 * 10 / 10.1**2
        self.assertAlmostEqual(experiment.singleton_resolution_bound(graph), expected)
        graph.es['weight'] = [7 * weight for weight in graph.es['weight']]
        self.assertAlmostEqual(experiment.singleton_resolution_bound(graph), expected)


if __name__ == '__main__':
    unittest.main()
