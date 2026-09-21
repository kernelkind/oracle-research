import unittest

import numpy as np

from hierarchy_encoder_probe import prepare_pairs, geometry, dominates


class HierarchyEncoderProbeTests(unittest.TestCase):
    def test_preserves_fixed_inputs_and_all_native_orders(self):
        first = [dict(condition='subject', first='A.', second='B.', child_group='a', parent_group='b'),
                 dict(condition='native', first='ignore', second='this')]
        later = [dict(first='Meaning A', second='Meaning B', child_group='a', parent_group='b')]
        pairs = prepare_pairs(first, later, later)
        self.assertEqual(len(pairs), 15)
        self.assertEqual(pairs[0]['first'], 'A.')
        self.assertEqual(pairs[1]['condition'], 'definitions')
        self.assertEqual(pairs[2]['condition'], 'combined')
        self.assertEqual(len({(p['first'],p['second']) for p in pairs if p['condition']=='native'}),12)

    def test_geometry_and_direction_use_raw_not_normalized_vectors(self):
        vectors = np.array([[0.,0.],[.2,0.],[.4,0.]],dtype=np.float64)
        distances, radii = geometry(vectors)
        self.assertTrue(np.allclose(distances, distances.T))
        self.assertTrue(np.allclose(np.diag(distances), 0))
        self.assertTrue(np.allclose(distances[0], radii))
        expected = 2 / np.sqrt(.5) * np.arctanh(np.sqrt(.5) * .4)
        self.assertAlmostEqual(radii[2], expected, places=6)
        self.assertGreater(radii[2], radii[1])
        with self.assertRaises(ValueError):geometry(np.array([[2.,0.]]))
        with self.assertRaises(ValueError):geometry(np.array([[float('nan'),0.]]))

    def test_dominance_requires_both_strict_advantages(self):
        self.assertTrue(dominates(distance=1., radius=2., reference_distance=2., reference_radius=3.))
        self.assertFalse(dominates(distance=1., radius=4., reference_distance=2., reference_radius=3.))
        self.assertFalse(dominates(distance=2., radius=2., reference_distance=2., reference_radius=3.))


if __name__ == '__main__':
    unittest.main()
