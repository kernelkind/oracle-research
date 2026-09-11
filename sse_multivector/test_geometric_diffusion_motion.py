import unittest
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import numpy as np

from geometric_diffusion import fit
from geometric_diffusion_motion import describe_snapshot


class MotionTests(unittest.TestCase):
    def test_cli_rejects_directional_motion_before_using_euclidean_accounting(self):
        actual = fit([[1., 0.], [0., 1.]], epsilon=.6, max_steps=1,
                     coordinate_constraint='unit_sphere')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path/'configuration.json').write_text(json.dumps({'run_id': 'unit-test'}))
            (path/'hierarchy.json').write_text(json.dumps(
                {'stats': actual['stats'], 'nodes': actual['nodes']}))
            (path/'evidence.json').write_text(json.dumps([
                {'row': i, 'aliases': [{'short_id': f'V{i + 1:03}',
                                       'note_short_id': f'N{i + 1:03}'}]}
                for i in range(2)]))
            np.savez(path/'coordinate-snapshots.npz',
                     **{'0': np.array([[1., 0.], [0., 1.]]),
                        '1': actual['final_coordinates']})
            result = subprocess.run([sys.executable,
                                     str(Path(__file__).with_name('geometric_diffusion_motion.py')),
                                     directory, '--targets', 'V001', '--groups', '0',
                                     '--output', str(path/'motion.json')],
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('requires unconstrained coordinate updates', result.stderr)
            self.assertFalse((path/'motion.json').exists())

    def test_motion_reconstructs_real_update_and_group_contributions(self):
        x = np.array([[0., 0.], [.4, 0.], [2., 1.]])
        actual = fit(x, epsilon=.6, max_steps=1, relaxation=.25)
        before = x.copy()
        result = describe_snapshot(x, [0], {'a': [0, 1], 'b': [2]},
                                   [{'A'}, {'A'}, {'B'}], epsilon=.6,
                                   beta=1, relaxation=.25,
                                   next_coordinates=actual['final_coordinates'])
        row = result['targets'][0]
        self.assertLess(result['next_coordinate_max_error'], 1e-14)
        self.assertAlmostEqual(sum(g['probability'] for g in row['groups'].values()), 1)
        self.assertAlmostEqual(sum(g['motion_projection'] for g in row['groups'].values()),
                               row['displacement'])
        self.assertGreater(row['same_note_probability'], row['self_probability'])
        np.testing.assert_array_equal(x, before)

    def test_density_normalization_can_reverse_individual_neighbor_weights(self):
        x = np.array([[0.]] + [[1.]] * 20 + [[-1.1]])
        result = describe_snapshot(x, [0], {}, [{str(i)} for i in range(22)],
                                   epsilon=4, beta=1, relaxation=1)
        weights = {v['row']: v for v in result['targets'][0]['neighbors']}
        self.assertLess(weights[21]['raw_affinity'], weights[1]['raw_affinity'])
        self.assertGreater(weights[21]['probability'], weights[1]['probability'])

    def test_groups_must_not_overlap_and_reconstruction_must_match(self):
        x = np.array([[0.], [1.]])
        with self.assertRaises(ValueError):
            describe_snapshot(x, [0], {'a': [0], 'b': [0]}, [{'A'}, {'B'}],
                              epsilon=1, beta=1, relaxation=1)
        with self.assertRaises(ValueError):
            describe_snapshot(x, [0], {}, [{'A'}, {'B'}], epsilon=1,
                              beta=1, relaxation=1, next_coordinates=x)


if __name__ == '__main__':
    unittest.main()
