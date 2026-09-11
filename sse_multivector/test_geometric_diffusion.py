"""Direct-coordinate diffusion condensation, exercised through its real fit path."""

import unittest

import numpy as np

from geometric_diffusion import fit


class GeometricDiffusionTests(unittest.TestCase):
    def test_one_step_is_density_normalized_coordinate_diffusion(self):
        coordinates = np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 2.0]])
        original = coordinates.copy()
        affinity = np.array([
            [np.exp(-np.dot(a - b, a - b)) for b in coordinates]
            for a in coordinates
        ])
        degree = affinity.sum(axis=1)
        kernel = affinity / (degree[:, None] * degree[None, :])
        expected = (kernel / kernel.sum(axis=1)[:, None]) @ coordinates

        result = fit(coordinates, epsilon=1.0, max_steps=1)

        np.testing.assert_allclose(result["final_coordinates"], expected)
        np.testing.assert_array_equal(coordinates, original)

    def test_affinities_are_recomputed_after_each_coordinate_update(self):
        coordinates = np.array([[0.0], [0.4], [2.0]])
        expected = coordinates.copy()
        first_operator = None
        for _ in range(2):
            distances = np.array([[float(np.dot(a - b, a - b)) for b in expected]
                                  for a in expected])
            kernel = np.exp(-distances / 0.6)
            degree = kernel.sum(axis=1)
            kernel /= degree[:, None] * degree[None, :]
            operator = kernel / kernel.sum(axis=1)[:, None]
            if first_operator is None:
                first_operator = operator
            expected = operator @ expected

        result = fit(coordinates, epsilon=0.6, max_steps=2, bandwidth_growth=1)

        np.testing.assert_allclose(result["final_coordinates"], expected)
        self.assertFalse(np.allclose(expected, first_operator @ first_operator @ coordinates))
        self.assertEqual(result["stats"]["steps"], 2)

    def test_diffusion_power_uses_the_same_operator_within_one_step(self):
        coordinates = np.array([[0.0], [0.4], [2.0]])
        kernel = np.exp(-((coordinates - coordinates.T) ** 2) / 0.6)
        degree = kernel.sum(axis=1)
        kernel /= degree[:, None] * degree[None, :]
        operator = kernel / kernel.sum(axis=1)[:, None]

        result = fit(coordinates, epsilon=0.6, max_steps=1, diffusion_steps=3)

        np.testing.assert_allclose(result["final_coordinates"],
                                   operator @ operator @ operator @ coordinates)

    def test_cumulative_memberships_do_not_split_when_trajectories_separate(self):
        coordinates = np.array([[-1.0], [-1.0], [-0.2], [0.2], [1.0], [1.0]])
        result = fit(coordinates, epsilon=0.5, density_normalization=0,
                     merge_tolerance=0.402, max_steps=1)

        self.assertGreater(float(result["final_coordinates"][3, 0]
                                 - result["final_coordinates"][2, 0]), 0.402)
        root_members = [result["nodes"][root]["members"] for root in result["roots"]]
        self.assertIn([2, 3], root_members)
        self.assertEqual(result["final_coordinates"].shape, coordinates.shape)

    def test_simultaneous_connected_merges_are_one_native_multiway_union(self):
        result = fit([[0.0], [0.09], [0.18]], epsilon=1.0,
                     merge_tolerance=0.1, max_steps=0)

        self.assertEqual(len(result["nodes"]), 4)
        root = result["nodes"][result["roots"][0]]
        self.assertEqual(root["children"], [0, 1, 2])
        self.assertEqual(root["members"], [0, 1, 2])
        self.assertEqual(root["iteration"], 0)
        self.assertEqual(result["stats"]["stop_reason"], "single_group")
        self.assertFalse(result["stats"]["all_within_tolerance"])

    def test_two_pairs_form_before_a_complete_nested_parent(self):
        result = fit([[0.0], [0.01], [10.0], [10.01]], epsilon=1e-4,
                     merge_tolerance=1e-5, max_steps=200)
        groups = {tuple(node["members"]) for node in result["nodes"]}
        self.assertIn((0, 1), groups)
        self.assertIn((2, 3), groups)
        self.assertEqual(len(result["roots"]), 1)
        self.assertEqual(result["nodes"][result["roots"][0]]["members"], [0, 1, 2, 3])
        for node in result["nodes"]:
            if not node["children"]:
                continue
            children = [result["nodes"][child] for child in node["children"]]
            flattened = [member for child in children for member in child["members"]]
            self.assertEqual(sorted(flattened), node["members"])
            self.assertEqual(len(flattened), len(set(flattened)))
            for child in children:
                self.assertLess(len(child["members"]), len(node["members"]))
                self.assertLessEqual(child["iteration"], node["iteration"])

    def test_numeric_merging_does_not_compress_or_reweight_original_rows(self):
        coordinates = np.array([[0.0], [0.05], [2.0]])
        fine = fit(coordinates, epsilon=0.2, max_steps=1, merge_tolerance=1e-8)
        coarse = fit(coordinates, epsilon=0.2, max_steps=1, merge_tolerance=0.1)

        np.testing.assert_array_equal(fine["final_coordinates"], coarse["final_coordinates"])
        self.assertEqual(coarse["final_coordinates"].shape, coordinates.shape)
        self.assertFalse(coarse["stats"]["representative_compression"])

    def test_bandwidth_growth_resets_same_bandwidth_density_comparison(self):
        result = fit([[0.0], [100.0]], epsilon=1e-6, max_steps=5)
        history = result["stats"]["history"]

        self.assertEqual([step["epsilon"] for step in history],
                         [1e-6, 1e-6, 2e-6, 2e-6, 4e-6])
        self.assertEqual([step["density_change"] for step in history],
                         [None, 0.0, None, 0.0, None])
        self.assertEqual(result["stats"]["stop_reason"], "max_steps")
        self.assertEqual(result["roots"], [0, 1])

    def test_singleton_does_not_invent_merges_or_run_diffusion(self):
        result = fit([[3.0, 4.0]], epsilon=0.5)

        self.assertEqual(result["roots"], [0])
        self.assertEqual(result["nodes"][0]["children"], [])
        self.assertEqual(result["stats"]["steps"], 0)
        np.testing.assert_array_equal(result["final_coordinates"], [[3.0, 4.0]])

    def test_constant_input_coordinates_are_not_unit_renormalized(self):
        result = fit([[1.0, 0.0], [0.0, 1.0]], epsilon=1.0, max_steps=1)

        self.assertTrue(np.all(np.linalg.norm(result["final_coordinates"], axis=1) < 1))

    def test_unit_sphere_constraint_normalizes_each_move_before_rebuilding_kernel(self):
        x = np.array([[1., 0.], [.6, .8], [0., 1.]])
        original = x.copy()
        expected = x.copy()
        for _ in range(2):
            distances = np.array([[np.dot(a - b, a - b) for b in expected]
                                  for a in expected])
            affinity = np.exp(-distances / .6)
            degree = affinity.sum(axis=1)
            kernel = affinity / (degree[:, None] * degree[None, :])
            operator = kernel / kernel.sum(axis=1)[:, None]
            expected = .75 * expected + .25 * (operator @ expected)
            expected /= np.linalg.norm(expected, axis=1)[:, None]

        result = fit(x, epsilon=.6, relaxation=.25, max_steps=2,
                     coordinate_constraint='unit_sphere', snapshot_iterations=(1, 2))

        np.testing.assert_allclose(result['final_coordinates'], expected, atol=1e-14)
        for snapshot in result['snapshots'].values():
            np.testing.assert_allclose(np.linalg.norm(snapshot, axis=1), 1., atol=1e-14)
        np.testing.assert_array_equal(x, original)
        self.assertEqual(result['stats']['coordinate_constraint'], 'unit_sphere')
        plain = fit(x, epsilon=.6, relaxation=.25, max_steps=2)
        normalized_at_end = plain['final_coordinates']
        normalized_at_end /= np.linalg.norm(normalized_at_end, axis=1)[:, None]
        self.assertFalse(np.allclose(expected, normalized_at_end))

    def test_no_coordinate_constraint_preserves_original_dynamics(self):
        x = np.array([[0.], [.4], [2.]])
        original = fit(x, epsilon=.6, max_steps=3)
        explicit = fit(x, epsilon=.6, max_steps=3, coordinate_constraint='none')
        np.testing.assert_array_equal(original['final_coordinates'], explicit['final_coordinates'])
        self.assertEqual(original['nodes'], explicit['nodes'])

    def test_unit_sphere_constraint_rejects_nonunit_input_and_undefined_direction(self):
        for x in ([[0., 0.], [1., 0.]], [[2., 0.], [0., 1.]]):
            with self.subTest(x=x), self.assertRaisesRegex(ValueError, 'unit vectors'):
                fit(x, epsilon=.6, coordinate_constraint='unit_sphere')
        with self.assertRaisesRegex(ValueError, 'undefined direction'):
            fit([[1., 0.], [-1., 0.]], epsilon=1e300, max_steps=1,
                coordinate_constraint='unit_sphere')
        with self.assertRaisesRegex(ValueError, 'coordinate_constraint'):
            fit([[1., 0.]], epsilon=.6, coordinate_constraint='sphere')

    def test_requested_snapshots_are_read_only_observations_of_same_trajectory(self):
        x = np.array([[0.], [.4], [2.]])
        plain = fit(x, epsilon=.6, max_steps=3, bandwidth_growth=1)
        observed = fit(x, epsilon=.6, max_steps=3, bandwidth_growth=1,
                       snapshot_iterations=(0, 1, 3))
        self.assertEqual(set(observed['snapshots']), {0, 1, 3})
        np.testing.assert_array_equal(observed['snapshots'][0], x)
        first = fit(x, epsilon=.6, max_steps=1, bandwidth_growth=1)
        np.testing.assert_array_equal(observed['snapshots'][1], first['final_coordinates'])
        np.testing.assert_array_equal(observed['snapshots'][3], plain['final_coordinates'])
        self.assertEqual(observed['nodes'], plain['nodes'])
        observed['snapshots'][1][0, 0] = 999
        self.assertNotEqual(observed['final_coordinates'][0, 0], 999)

    def test_underrelaxation_moves_only_the_requested_fraction(self):
        x = np.array([[0.], [.4], [2.]])
        full = fit(x, epsilon=.6, max_steps=1)
        slow = fit(x, epsilon=.6, max_steps=1, relaxation=.25)
        expected = .75 * x + .25 * full['final_coordinates']
        np.testing.assert_allclose(slow['final_coordinates'], expected, atol=1e-15)
        self.assertEqual(slow['stats']['relaxation'], .25)
        first_then_second = fit(expected, epsilon=.6, max_steps=1, relaxation=.25)
        two = fit(x, epsilon=.6, max_steps=2, relaxation=.25)
        np.testing.assert_allclose(two['final_coordinates'], first_then_second['final_coordinates'], atol=1e-15)

    def test_full_relaxation_preserves_existing_numerical_update(self):
        x = np.array([[0.], [.4], [2.]])
        plain = fit(x, epsilon=.6, max_steps=3)
        explicit = fit(x, epsilon=.6, max_steps=3, relaxation=1)
        np.testing.assert_array_equal(plain['final_coordinates'], explicit['final_coordinates'])
        self.assertEqual(plain['nodes'], explicit['nodes'])

    def test_relaxation_must_be_a_finite_convex_step(self):
        for value in (0, -.1, 1.1, np.nan, np.inf):
            with self.subTest(value=value), self.assertRaises(ValueError):
                fit([[0.], [1.]], epsilon=.6, relaxation=value)

    def test_invalid_inputs_and_parameters_are_rejected(self):
        for coordinates in ([], [[]], [1, 2], [[np.nan]], [[np.inf]], [[1j]]):
            with self.subTest(coordinates=coordinates), self.assertRaises(ValueError):
                fit(coordinates, epsilon=1.0)
        for config in ({"epsilon": 0}, {"epsilon": np.inf}, {"merge_tolerance": 0},
                       {"density_tolerance": -1}, {"density_normalization": 2},
                       {"bandwidth_growth": 0.5}, {"diffusion_steps": 0},
                       {"diffusion_steps": True}, {"max_steps": -1}, {"max_steps": 1.5}):
            with self.subTest(config=config), self.assertRaises(ValueError):
                fit([[0.0], [1.0]], **({"epsilon": 1.0} | config))


if __name__ == "__main__":
    unittest.main()
