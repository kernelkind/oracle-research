"""Input alignment and semantic-evidence packaging, independent of clustering."""
import unittest
from unittest.mock import patch
from tempfile import TemporaryDirectory
from pathlib import Path
import json
import numpy as np
from geometric_experiment import canonical_rows, validate_tree, overlay, detach_arrays, main


class GeometryArtifactTests(unittest.TestCase):
    def test_canonical_order_is_not_source_row_order(self):
        x = np.array([[1., 0.], [0., 1.], [1., 0.]])
        mapping = [{'vector_id': name, 'ordinal': i}
                   for i, name in enumerate(('a', 'b', 'c'))]
        out = canonical_rows(x, mapping, [['b'], ['a', 'c']])
        np.testing.assert_array_equal(out, [[0, 1], [1, 0]])

    def test_alias_must_have_exactly_same_saved_coordinates(self):
        with self.assertRaises(ValueError):
            canonical_rows(np.eye(2), [{'vector_id': 'a', 'ordinal': 0},
                           {'vector_id': 'b', 'ordinal': 1}], [['a', 'b']])

    def test_tree_must_cover_each_input_once_and_children_must_partition(self):
        nodes = [{'id': 2, 'children': [0, 1], 'members': [0, 1]},
                 {'id': 0, 'children': [], 'members': [0]},
                 {'id': 1, 'children': [], 'members': [1]}]
        validate_tree(nodes, [2], 2)
        nodes[2]['members'] = [0]
        with self.assertRaises(ValueError):
            validate_tree(nodes, [2], 2)

    def test_inline_overlay_uses_utf8_byte_positions(self):
        self.assertEqual(overlay('☕ coffee now', [[4, 10]]), '☕ ⟦coffee⟧ now')

    def test_native_fuzzy_arrays_are_preserved_without_mutating_result(self):
        matrix = np.array([[.2, .8], [1., 0.]])
        native = {'levels': [{'membership': matrix}], 'config': {'q': .5}}
        encoded, arrays = detach_arrays(native)
        key = encoded['levels'][0]['membership']['array']
        np.testing.assert_array_equal(arrays[key], matrix)
        self.assertIs(native['levels'][0]['membership'], matrix)
        self.assertEqual(encoded['config'], {'q': .5})

    def test_cli_preserves_requested_coordinate_snapshots_separately(self):
        x = np.eye(3)
        records = [{'canonical_id': str(i), 'aliases': [{'note_short_id': str(i)}]}
                   for i in range(3)]
        with TemporaryDirectory() as temporary:
            output = Path(temporary)/'run'
            args = ['experiment', 'run', '--data', temporary, '--method', 'diffusion',
                    '--config', json.dumps({'epsilon': .2, 'max_steps': 2,
                                            'snapshot_iterations': [0, 1, 2]}),
                    '--run-id', 'test', '--output', str(output)]
            with patch('sys.argv', args), patch('geometric_experiment.load_input',
                                               return_value=(x, records, {})), patch('builtins.print'):
                main()
            with np.load(output/'coordinate-snapshots.npz') as saved:
                np.testing.assert_array_equal(saved['0'], x)
                np.testing.assert_array_equal(saved['2'], np.load(output/'final-coordinates.npy'))
            result = json.loads((output/'hierarchy.json').read_text())
            self.assertEqual(result['snapshot_iterations'], [0, 1, 2])
            self.assertNotIn('snapshots', result)


if __name__ == '__main__':
    unittest.main()
