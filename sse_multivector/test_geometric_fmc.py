"""Equation-level checks through the experimental FMC production path."""

import unittest

import numpy as np

from geometric_fmc import fit, hard_projection


class GeometricFmcTests(unittest.TestCase):
    def test_mutual_neighbors_do_not_silently_connect_isolated_rows(self):
        result = fit([[0.], [1.], [10.]], n_neighbors=1,
                     density_neighbors=1, adaptive=False, refinement_steps=0)
        initial = result['levels'][0]
        np.testing.assert_array_equal(initial['coupling'],
                                      [[0., 1., 0.], [1., 0., 0.], [0., 0., 0.]])
        self.assertEqual(result['diagnostics']['initial_components'], 2)
        projected = hard_projection(result)
        self.assertEqual(projected['levels'][-1]['groups'], [[0, 1], [2]])
        self.assertEqual(result['stop_reason'], 'no_coarsening')

    def test_seed_interpolation_and_coarse_measures_match_equations(self):
        result = fit([[0.], [1.], [3.], [4.]], n_neighbors=3,
                     density_neighbors=1, adaptive=False, refinement_steps=0,
                     max_levels=1, xi=2.)
        fine, coarse = result['levels']
        transition = result['transitions'][0]
        self.assertEqual(transition['seeds'], [0, 2])
        p = np.array([[1., 0.], [2 / 3, 1 / 3], [0., 1.], [.2, .8]])
        np.testing.assert_allclose(transition['interpolation'], p)
        np.testing.assert_allclose(coarse['membership'], p)
        for name in ('coupling', 'border'):
            expected = p.T @ fine[name] @ p
            np.fill_diagonal(expected, 0.)
            np.testing.assert_allclose(coarse[name], expected)
            np.testing.assert_allclose(coarse[name], coarse[name].T)
        numerator = p.T @ (fine['coupling'] ** 2) @ p
        denominator = np.outer(p.sum(0), p.sum(0)) - p.T @ p
        self.assertAlmostEqual(coarse['normalized_coupling'][0, 1],
                               np.sqrt(numerator[0, 1] / denominator[0, 1]))
        self.assertAlmostEqual(coarse['distance'][0, 1],
                               np.sqrt(coarse['border'][0, 1] / numerator[0, 1]))
        np.testing.assert_allclose(coarse['volume'], p.T @ np.ones(4))
        np.testing.assert_allclose(coarse['sparsity'], np.ones(2))

    def test_adaptive_weights_use_distinct_density_and_distance_factors(self):
        result = fit([[0.], [1.], [3.], [8.]], n_neighbors=3,
                     density_neighbors=1, max_levels=1, refinement_steps=0,
                     alpha=1., gamma1=2., gamma2=3.)
        level = result['levels'][0]
        rho = level['sparsity']
        i, j = 0, 3
        expected = (level['normalized_coupling'][i, j]
                    * np.exp(-2 * abs(rho[i] - rho[j]) / (rho[i] + rho[j]))
                    * np.exp(-3 * level['distance'][i, j] / (rho[i] + rho[j])))
        self.assertAlmostEqual(level['aggregation'][i, j], expected)
        np.testing.assert_array_equal(rho, [1., 1., 2., 5.])

    def test_sparse_border_and_all_pair_normalizations_are_not_conflated(self):
        result = fit([[0.], [1.], [2.5], [4.], [5.]], n_neighbors=2,
                     density_neighbors=1, adaptive=False, refinement_steps=0,
                     max_levels=1, xi=2.)
        fine, coarse = result['levels']
        p = result['transitions'][0]['interpolation']
        numerator = p.T @ (fine['coupling'] ** 2) @ p
        denominator = np.outer(p.sum(0), p.sum(0)) - p.T @ p
        self.assertGreater(denominator[0, 1], coarse['border'][0, 1])
        self.assertAlmostEqual(coarse['normalized_coupling'][0, 1],
                               np.sqrt(numerator[0, 1] / denominator[0, 1]))
        self.assertAlmostEqual(coarse['distance'][0, 1],
                               np.sqrt(coarse['border'][0, 1] / numerator[0, 1]))

    def test_declared_threshold_schedule_advances_past_identity_transition(self):
        result = fit([[0.], [1.], [3.], [4.]], n_neighbors=3,
                     density_neighbors=1, adaptive=False, refinement_steps=0,
                     delta0=2., delta_until_level=0)
        first = result['transitions'][0]
        np.testing.assert_array_equal(first['interpolation'], np.eye(4))
        self.assertEqual(first['delta'], 2.)
        self.assertLess(result['levels'][2]['membership'].shape[1], 4)
        self.assertEqual(result['transitions'][1]['delta'], 0.)

    def test_attachment_control_promotes_a_row_when_all_links_are_removed(self):
        result = fit([[0.], [1.], [2.], [100.]], n_neighbors=3,
                     density_neighbors=1, adaptive=False, refinement_steps=0,
                     order_control_start_level=0, attachment_tau=.49,
                     attachment_factor=10., max_levels=1)
        transition = result['transitions'][0]
        self.assertEqual(transition['promoted_seeds'], [3])
        self.assertEqual(transition['removed_attachments'], 2)
        self.assertEqual(transition['seeds'], [0, 1, 3])
        np.testing.assert_array_equal(transition['interpolation'][3], [0., 0., 1.])
        np.testing.assert_allclose(transition['interpolation'].sum(axis=1), np.ones(4))

    def test_refinement_uses_coupled_neighbors_with_fixed_seeds_and_support(self):
        options = dict(n_neighbors=3, density_neighbors=1, adaptive=False,
                       max_levels=1)
        unrefined = fit([[0.], [1.], [3.], [4.]], refinement_steps=0, **options)
        refined = fit([[0.], [1.], [3.], [4.]], refinement_steps=1, **options)
        transition = refined['transitions'][0]
        p = unrefined['transitions'][0]['interpolation']
        expected = unrefined['levels'][0]['coupling'] @ p
        expected[p == 0] = 0
        expected /= expected.sum(axis=1, keepdims=True)
        expected[transition['seeds']] = np.eye(len(transition['seeds']))
        np.testing.assert_allclose(transition['interpolation'], expected)
        np.testing.assert_allclose(transition['interpolation_before_refinement'], p)
        self.assertGreater(transition['refinement_l1_change'], 0.)

    def test_fuzzy_levels_keep_all_original_rows_and_projection_is_nested(self):
        x = np.array([[0.], [.3], [1.1], [2.], [5.], [5.2], [6.], [9.]])
        result = fit(x, n_neighbors=7, density_neighbors=2,
                     adaptive=False, refinement_steps=2)
        projected = hard_projection(result)
        product = np.eye(len(x))
        for index, level in enumerate(result['levels']):
            if index:
                product = product @ result['transitions'][index - 1]['interpolation']
            np.testing.assert_allclose(level['membership'], product)
            np.testing.assert_allclose(product.sum(axis=1), np.ones(len(x)))
            np.testing.assert_allclose(level['volume'], product.sum(axis=0))
            hard = projected['levels'][index]
            self.assertEqual(sorted(row for group in hard['groups'] for row in group),
                             list(range(len(x))))
            if index:
                parents = hard['parents']
                previous = projected['levels'][index - 1]
                for child, parent in enumerate(parents):
                    self.assertTrue(set(previous['groups'][child]) <= set(hard['groups'][parent]))
            native = np.argmax(product, axis=1)
            self.assertEqual(hard['composite_argmax_disagreements'],
                             int(np.count_nonzero(native != hard['assignment'])))
        self.assertIn('not the native fuzzy hierarchy', projected['method'])

    def test_exact_duplicate_coordinates_are_rejected_without_hidden_jitter(self):
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            fit([[1., 0.], [1., 0.]])

    def test_singleton_and_invalid_inputs(self):
        result = fit([[2., 3.]])
        self.assertEqual(result['stop_reason'], 'single_aggregate')
        self.assertEqual(hard_projection(result)['levels'][0]['groups'], [[0]])
        for x in ([], [1., 2.], [[float('nan')], [0.]], [[float('inf')], [0.]]):
            with self.subTest(x=x), self.assertRaises(ValueError):
                fit(x)
        for options in ({'n_neighbors': 0}, {'q': 0.}, {'q': 1.1},
                        {'xi': 0.}, {'gamma1': -1.}, {'max_levels': 0},
                        {'refinement_steps': -1}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                fit([[0.], [1.]], **options)


if __name__ == '__main__':
    unittest.main()
