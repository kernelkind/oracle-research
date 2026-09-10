"""Audit the four frozen artifacts and replay the graphs through native Infomap."""

import hashlib
import json
from pathlib import Path
import unittest

import infomap_experiment  # Applies the experiment's one-thread environment.
import infomap


ROOT = Path(__file__).resolve().parent


class SavedInfomapTests(unittest.TestCase):
    def test_all_sources_paths_and_native_memberships_are_preserved(self):
        sources = {
            'baseline': ROOT / 'real-note-fine-segmentation-v1/hdbv3-cross-note-edges-v1/response.json',
            'request': ROOT / 'real-note-fine-segmentation-v1/hdbv3-cross-note-edges-v1/request.json',
            'vector_map': ROOT / 'real-note-fine-segmentation-v1/vectors/vector-map.json',
            'notes': ROOT / 'real-note-fine-segmentation-v1/reviewed-input.json',
        }
        reference = json.loads((ROOT / 'merge-rule-exploration-v1/M07.json').read_text())
        for run in ['I01', 'I02', 'I03', 'I04']:
            with self.subTest(run=run):
                directory = ROOT / 'infomap-experiment-v1' / run
                h = json.loads((directory / 'hierarchy.json').read_text())
                native = json.loads((directory / 'native.json').read_text())
                config = json.loads((directory / 'configuration.json').read_text())
                for name, path in sources.items():
                    actual = hashlib.sha256(path.read_bytes()).hexdigest()
                    self.assertEqual(actual, h['sources'][name]['sha256'])
                    self.assertEqual(actual, reference['sources'][name]['sha256'])
                self.assertEqual(h['canonical_unique_ids'], reference['canonical_unique_ids'])
                self.assertEqual(h['alias_groups'], reference['alias_groups'])
                self.assertEqual(len(h['paths']), 916)
                native_paths = {p['id']: p['path'] for p in native['nodes']}
                self.assertEqual(native_paths, {p['node_id']: p['native_path'] for p in h['paths']})
                self.assertEqual(sorted(native_paths), list(range(916)))
                for p in h['paths']:
                    self.assertEqual(p['module_path'], p['native_path'][:-1])
                self.assertEqual(len(h['modules'][0]['note_ids']), 100)
                self.assertEqual(h['modules'][0]['vector_ids'], list(range(916)))
                self.assertEqual(config['graph']['sha256'], hashlib.sha256((directory / 'graph.net').read_bytes()).hexdigest())
                self.assertFalse(config['infomap']['two_level'])

    def test_saved_graphs_replay_same_native_paths_with_same_configuration(self):
        for run in ['I01', 'I02', 'I03', 'I04']:
            with self.subTest(run=run):
                directory = ROOT / 'infomap-experiment-v1' / run
                h = json.loads((directory / 'hierarchy.json').read_text())
                before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.iterdir()}
                result = infomap.run(str(directory / 'graph.net'), options=infomap.Options(
                    silent=True, flow_model='undirected', seed=123, num_trials=10,
                    two_level=False, inner_parallelization=False))
                self.assertEqual({n.node_id: list(n.path) for n in result.nodes()},
                                 {p['node_id']: p['native_path'] for p in h['paths']})
                self.assertAlmostEqual(result.codelength, h['summary']['codelength'], places=10)
                self.assertEqual(before, {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.iterdir()})


if __name__ == '__main__':
    unittest.main()
