"""Provenance rejection through the real experiment command-line entry point."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class MergeRuleCommandTests(unittest.TestCase):
    def test_note_pair_cli_checks_real_alias_provenance(self):
        for case in ('valid', 'map_disagrees', 'multiple_sources'):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                multi = case == 'multiple_sources'
                aliases = [['a', 'b'], ['c']] if multi else [['a'], ['c']]
                sources = {'a': 'P', 'c': 'R'}
                if multi:
                    sources['b'] = 'Q'
                mapping = [{'vector_id': v, 'note_id': note} for v, note in sources.items()]
                if case == 'map_disagrees':
                    mapping[0]['note_id'] = 'wrong'
                baseline = {
                    'canonical_unique_ids': ['a', 'c'], 'alias_groups': aliases,
                    'algorithm_result': {
                        'vector_count': 2,
                        'mutual_reachability_distances': [0, 1, 1, 0],
                        'core_distances': [0 if multi else 1, 1],
                        'minimum_spanning_tree': [
                            {'left': 0, 'right': 1, 'mutual_reachability_distance': 1}],
                    },
                }
                inputs = {
                    'baseline': {'artifact': {'result': baseline}},
                    'request': {'source_note_ids': sources},
                    'vector-map': {'vectors': mapping},
                    'notes': {'notes': [{'note_id': note, 'text': note}
                                        for note in sorted(set(sources.values()))]},
                }
                command = [sys.executable, str(Path(__file__).with_name('merge_rule_experiment.py'))]
                for name, data in inputs.items():
                    path = root / (name + '.json')
                    path.write_text(json.dumps(data))
                    command.extend(['--' + name, str(path)])
                output = root / 'result.json'
                command.extend(['--rule', 'note_pair_mean', '--run-id', 'test',
                                '--output', str(output)])
                result = subprocess.run(command, capture_output=True, text=True, timeout=30)
                if case == 'valid':
                    self.assertEqual(result.returncode, 0, result.stderr)
                    saved = json.loads(output.read_text())
                    self.assertEqual(saved['alias_groups'], aliases)
                    self.assertEqual(saved['merges'][0]['merge_score'], 1)
                else:
                    self.assertNotEqual(result.returncode, 0)
                    expected = ('source notes changed between vector map and request'
                                if case == 'map_disagrees' else
                                'note-pair weighting requires one source note per canonical vector')
                    self.assertIn(expected, result.stderr)
                    self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
