"""PARIS score checks over unchanged angular inputs and excluded edges."""

import math
import unittest

import numpy as np

from merge_rule_experiment import agglomerate, pair_score


class ParisMergeTests(unittest.TestCase):
    def test_outside_connections_change_scores_for_equal_pair_angles(self):
        positions = np.array([0, .15, 1.5, 1.65, 1.7])
        d = np.arccos(np.clip(np.cos(positions[:, None] - positions[None, :]), -1, 1))
        a = pair_score(d, [0], [1], 'paris_linear')
        b = pair_score(d, [2], [3], 'paris_linear')
        self.assertAlmostEqual(d[0, 1], d[2, 3])
        self.assertLess(a, b)
        w = [[0 if i == j else 1 - float(d[i, j]) / math.pi
              for j in range(5)] for i in range(5)]
        degree = [sum(row) for row in w]
        self.assertAlmostEqual(a, degree[0] * degree[1] / (sum(degree) * w[0][1]))
        self.assertNotAlmostEqual(a, pair_score(d[:4, :4], [0], [1], 'paris_linear'))

    def test_merged_mass_keeps_connections_that_became_internal(self):
        w = np.array([[0, .9, .1, .2], [.9, 0, .1, .2],
                      [.1, .1, 0, .8], [.2, .2, .8, 0]])
        d = math.pi * (1 - w)
        np.fill_diagonal(d, np.inf)
        rows = agglomerate(d, 'paris_linear')
        self.assertEqual([(r['left'], r['right']) for r in rows], [(2, 3), (0, 1), (4, 5)])
        self.assertAlmostEqual(rows[-1]['merge_score'], 2.2 * 2.4 / (4.6 * .6))

    def test_constant_edge_control_exposes_source_size_degree_effect(self):
        sources = ['P', 'P', 'P', 'Q', 'Q', 'R']
        d = np.ones((6, 6))
        for i in range(6):
            for j in range(6):
                if sources[i] == sources[j]:
                    d[i, j] = np.inf
        self.assertAlmostEqual(pair_score(d, [0], [3], 'paris_linear'), 12 / 22)
        self.assertAlmostEqual(pair_score(d, [3], [5], 'paris_linear'), 20 / 22)
        self.assertTrue(math.isinf(pair_score(d, [0], [1], 'paris_linear')))

    def test_history_matches_independent_exhaustive_graph_calculation(self):
        for seed in range(8):
            rng = np.random.default_rng(500 + seed)
            x = rng.normal(size=(9, 5))
            x /= np.linalg.norm(x, axis=1)[:, None]
            d = np.arccos(np.clip(x @ x.T, -1, 1))
            for i in range(9):
                for j in range(i, 9):
                    if i % 3 == j % 3 or (abs(i - j) > 1 and rng.random() < .2):
                        d[i, j] = d[j, i] = np.inf
            w = [[0 if not math.isfinite(d[i, j]) else 1 - d[i, j] / math.pi
                  for j in range(9)] for i in range(9)]
            degree = [sum(row) for row in w]
            total = sum(degree)
            active = {i: [i] for i in range(9)}
            previous = -math.inf
            for row in agglomerate(d, 'paris_linear'):
                candidates = []
                for a, av in active.items():
                    for b, bv in active.items():
                        if a >= b:
                            continue
                        cross = sum(w[i][j] for i in av for j in bv)
                        if cross:
                            score = sum(degree[i] for i in av) * sum(degree[j] for j in bv)
                            candidates.append((score / (total * cross), a, b))
                expected, a, b = min(candidates)
                self.assertEqual((row['left'], row['right']), (a, b))
                self.assertAlmostEqual(row['merge_score'], expected)
                self.assertGreaterEqual(row['merge_score'] + 1e-12, previous)
                self.assertEqual(row['unsupported_left'], sum(
                    not any(math.isfinite(d[i, j]) for j in active[b]) for i in active[a]))
                self.assertEqual(row['unsupported_right'], sum(
                    not any(math.isfinite(d[i, j]) for i in active[a]) for j in active[b]))
                previous = row['merge_score']
                active[row['id']] = active.pop(a) + active.pop(b)

    def test_exact_ties_use_existing_cluster_id_order(self):
        d = np.ones((4, 4))
        rows = agglomerate(d, 'paris_linear')
        self.assertEqual([(r['left'], r['right']) for r in rows], [(0, 1), (2, 3), (4, 5)])

    def test_rejects_nonpositive_eligible_affinities_and_disconnection(self):
        for angle in (math.pi, math.pi + .1):
            d = np.array([[0, angle], [angle, 0]])
            with self.assertRaisesRegex(ValueError, 'eligible angles'):
                agglomerate(d, 'paris_linear')
            with self.assertRaisesRegex(ValueError, 'eligible angles'):
                pair_score(d, [0], [1], 'paris_linear')
        d = np.full((4, 4), np.inf)
        d[0, 1] = d[1, 0] = d[2, 3] = d[3, 2] = 1
        with self.assertRaisesRegex(ValueError, 'connected'):
            agglomerate(d, 'paris_linear')


if __name__ == '__main__':
    unittest.main()
