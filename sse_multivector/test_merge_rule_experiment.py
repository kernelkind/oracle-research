"""Tests exercise the same numeric runner used for the saved experiments."""

import math
import unittest

import numpy as np

from merge_rule_experiment import agglomerate, pair_score


class MergeRuleTests(unittest.TestCase):
    def test_score_uses_each_endpoint_not_only_the_closest_pair(self):
        d = np.array([[0, .1, .2, .8], [.1, 0, .7, .6],
                      [.2, .7, 0, .1], [.8, .6, .1, 0]])
        self.assertAlmostEqual(pair_score(d, [0, 1], [2, 3]), .4)

    def test_excluded_edges_supply_no_evidence(self):
        d = np.array([[0, np.inf, .2], [np.inf, 0, .4], [.2, .4, 0]])
        self.assertAlmostEqual(pair_score(d, [0, 2], [1]), .4)
        rows = agglomerate(d)
        self.assertEqual((rows[0]['left'], rows[0]['right']), (0, 2))
        self.assertEqual(rows[-1]['size'], 3)
        self.assertEqual(rows[-1]['unsupported_right'], 1)

    def test_actual_angular_score_inversion_is_preserved(self):
        x = np.array([[-2, -1, -2], [1, 2, 0], [2, -1, -1], [-2, 2, 1]], dtype=float)
        x /= np.linalg.norm(x, axis=1)[:, None]
        d = np.arccos(np.clip(x @ x.T, -1, 1))
        rows = agglomerate(d)
        self.assertEqual((rows[0]['left'], rows[0]['right']), (1, 3))
        self.assertEqual((rows[1]['left'], rows[1]['right']), (0, 2))
        self.assertAlmostEqual(rows[2]['merge_score'], math.pi / 2)
        self.assertLess(rows[2]['merge_score'], rows[1]['merge_score'])

    def test_updates_match_exhaustive_global_selection(self):
        for seed in range(8):
            rng = np.random.default_rng(seed)
            x = rng.normal(size=(9, 5))
            x /= np.linalg.norm(x, axis=1)[:, None]
            d = np.arccos(np.clip(x @ x.T, -1, 1))
            for i in range(9):
                for j in range(9):
                    if i // 3 == j // 3:
                        d[i, j] = np.inf
            active = {i: [i] for i in range(9)}
            for row in agglomerate(d):
                candidates = []
                for a, av in active.items():
                    for b, bv in active.items():
                        if a >= b:
                            continue
                        ab = [min(d[i, j] for j in bv) for i in av]
                        ba = [min(d[j, i] for i in av) for j in bv]
                        ab = [v for v in ab if math.isfinite(v)]
                        ba = [v for v in ba if math.isfinite(v)]
                        if ab and ba:
                            candidates.append(((sum(ab)/len(ab) + sum(ba)/len(ba))/2, a, b))
                score, a, b = min(candidates)
                self.assertEqual((row['left'], row['right']), (a, b))
                self.assertAlmostEqual(row['merge_score'], score)
                active[row['id']] = active.pop(a) + active.pop(b)
            self.assertEqual(len(active), 1)

    def test_disconnected_or_invalid_matrix_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'connected'):
            agglomerate(np.array([[0, np.inf], [np.inf, 0]]))
        with self.assertRaisesRegex(ValueError, 'symmetric'):
            agglomerate(np.array([[0, .2], [.3, 0]]))
        with self.assertRaisesRegex(ValueError, 'nonnegative'):
            agglomerate(np.array([[0, -.2], [-.2, 0]]))

    def test_symmetric_sum_changes_only_directional_normalization(self):
        d = np.array([[0, .1, .2, .8], [.1, 0, .7, .6],
                      [.2, .7, 0, .1], [.8, .6, .1, 0]])
        self.assertAlmostEqual(pair_score(d, [0, 1], [2, 3], rule='symmetric_sum'), .8)
        self.assertAlmostEqual(pair_score(d, [0], [2], rule='symmetric_sum'), .2)

    def test_symmetric_sum_updates_match_exhaustive_selection(self):
        rng = np.random.default_rng(21)
        x = rng.normal(size=(13, 5))
        x /= np.linalg.norm(x, axis=1)[:, None]
        d = np.arccos(np.clip(x @ x.T, -1, 1))
        for i in range(13):
            for j in range(13):
                if i // 3 == j // 3:
                    d[i, j] = np.inf
        active = {i: [i] for i in range(13)}
        for row in agglomerate(d, rule='symmetric_sum'):
            candidates = []
            for a, av in active.items():
                for b, bv in active.items():
                    if a >= b:
                        continue
                    values = [min(d[i, j] for j in bv) for i in av]
                    values += [min(d[j, i] for i in av) for j in bv]
                    finite = [v for v in values if math.isfinite(v)]
                    if finite:
                        candidates.append((sum(finite)/2, a, b))
            score, a, b = min(candidates)
            self.assertEqual((row['left'], row['right']), (a, b))
            self.assertAlmostEqual(row['merge_score'], score)
            active[row['id']] = active.pop(a) + active.pop(b)

    def test_min_sum_singleton_uses_nearest_eligible_member(self):
        d = np.array([[0, .2, .6], [.2, 0, np.inf], [.6, np.inf, 0]])
        self.assertAlmostEqual(pair_score(d, [0], [1, 2], rule='min_sum'), .2)
        self.assertAlmostEqual(pair_score(d, [1, 2], [0], rule='min_sum'), .2)

    def test_min_sum_updates_match_exhaustive_selection_with_excluded_edges(self):
        for seed in range(6):
            rng = np.random.default_rng(30 + seed)
            x = rng.normal(size=(11, 5))
            x /= np.linalg.norm(x, axis=1)[:, None]
            d = np.arccos(np.clip(x @ x.T, -1, 1))
            for i in range(11):
                for j in range(11):
                    if i // 3 == j // 3:
                        d[i, j] = np.inf
            active = {i: [i] for i in range(11)}
            for row in agglomerate(d, rule='min_sum'):
                candidates = []
                for a, av in active.items():
                    for b, bv in active.items():
                        if a >= b:
                            continue
                        ab = [min(d[i, j] for j in bv) for i in av]
                        ba = [min(d[j, i] for i in av) for j in bv]
                        ab = [v for v in ab if math.isfinite(v)]
                        ba = [v for v in ba if math.isfinite(v)]
                        if ab and ba:
                            candidates.append((min(sum(ab), sum(ba)), a, b))
                score, a, b = min(candidates)
                self.assertEqual((row['left'], row['right']), (a, b))
                self.assertAlmostEqual(row['merge_score'], score)
                active[row['id']] = active.pop(a) + active.pop(b)


if __name__ == '__main__':
    unittest.main()
