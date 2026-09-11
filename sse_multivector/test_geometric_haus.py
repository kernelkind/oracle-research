"""Small known-geometry checks for the actual recursive HAUS kernel."""
import unittest
import numpy as np

from geometric_haus import fit, fit_affinity, normalized_laplacian


class HausTests(unittest.TestCase):
    def test_binary_fallback_retains_initial_row_normalization(self):
        raw = np.random.default_rng(10).lognormal(0, 1, size=(8, 8))
        a = (raw + raw.T) / 2
        np.fill_diagonal(a, 0)
        result = fit_affinity(a, max_depth=1, mean_cut_threshold=.55)
        nodes = {n['id']: n for n in result['nodes']}
        root = nodes[result['roots'][0]]
        self.assertEqual(root['diagnostic']['proposed_children'], 5)
        self.assertEqual([a['children'] for a in root['diagnostic']['attempts']],
                         [5, 4, 3, 2])
        self.assertEqual({tuple(nodes[c]['members']) for c in root['children']},
                         {(0, 1, 2, 5, 6, 7), (3, 4)})

    def test_disconnected_components_are_preserved_before_finer_splits(self):
        a = np.zeros((12, 12))
        for start in (0, 4, 8):
            a[start:start + 4, start:start + 4] = 1
        np.fill_diagonal(a, 0)
        r = fit_affinity(a, max_kways=10, max_depth=9)
        nodes = {n['id']: n for n in r['nodes']}
        children = nodes[r['roots'][0]]['children']
        self.assertEqual({tuple(nodes[c]['members']) for c in children},
                         {tuple(range(i, i + 4)) for i in (0, 4, 8)})

    def test_uniform_affinity_stops_without_inventing_a_partition(self):
        a = np.ones((8, 8)) - np.eye(8)
        r = fit_affinity(a)
        self.assertEqual(len(r['nodes']), 1)
        self.assertEqual(r['nodes'][0]['members'], list(range(8)))

    def test_every_split_is_an_exact_disjoint_cover(self):
        rng = np.random.default_rng(14)
        x = np.vstack([rng.normal(c, .02, (10, 3)) for c in
                       ([1, 0, 0], [0, 1, 0], [0, 0, 1])])
        r = fit(x)
        nodes = {n['id']: n for n in r['nodes']}
        self.assertGreater(len(nodes), 1)
        for n in nodes.values():
            if n['children']:
                members = [i for c in n['children'] for i in nodes[c]['members']]
                self.assertEqual(sorted(members), n['members'])
                self.assertEqual(len(members), len(set(members)))

    def test_repeat_is_deterministic_and_does_not_modify_input(self):
        x = np.random.default_rng(1).normal(size=(25, 6))
        before = x.copy()
        self.assertEqual(fit(x), fit(x))
        np.testing.assert_array_equal(x, before)

    def test_normalized_laplacian_uses_zero_for_isolated_vertex(self):
        np.testing.assert_array_equal(normalized_laplacian(np.zeros((2, 2))),
                                      np.zeros((2, 2)))

    def test_invalid_vectors_and_asymmetric_affinities_are_rejected(self):
        for x in (np.zeros((3, 2)), np.array([[1, np.nan], [2, 3]])):
            with self.assertRaises(ValueError):
                fit(x)
        with self.assertRaises(ValueError):
            fit_affinity(np.array([[0, 1], [0, 0]]))

    def test_gaussian_affinity_is_explicit_and_uses_original_unit_distances(self):
        x = np.random.default_rng(10).normal(size=(20, 4))
        x /= np.linalg.norm(x, axis=1, keepdims=True)
        expected = np.exp(-np.maximum(2 - 2 * (x @ x.T), 0) / .2)
        np.fill_diagonal(expected, 0)
        direct = fit(x, affinity='gaussian', epsilon=.2)
        reference = fit_affinity(expected)
        self.assertEqual([n['members'] for n in direct['nodes']],
                         [n['members'] for n in reference['nodes']])
        with self.assertRaises(ValueError):
            fit(x, affinity='gaussian')


if __name__ == '__main__':
    unittest.main()
