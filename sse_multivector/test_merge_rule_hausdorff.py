"""Worst finite nearest-partner evidence, retaining source-edge omissions."""

import math
import unittest

import numpy as np

from merge_rule_experiment import agglomerate, pair_score


RULE = 'hausdorff_finite'


def exhaustive_score(d, a, b):
    nearest = []
    for source, target in ((a, b), (b, a)):
        for i in source:
            permitted = [float(d[i, j]) for j in target if math.isfinite(d[i, j])]
            if permitted:
                nearest.append(min(permitted))
    return max(nearest) if nearest else math.inf


def angles(seed, n=9):
    x = np.random.default_rng(seed).normal(size=(n, 3))
    x /= np.linalg.norm(x, axis=1)[:, None]
    d = np.arccos(np.clip(x @ x.T, -1, 1))
    np.fill_diagonal(d, np.inf)
    return d


class FiniteHausdorffTests(unittest.TestCase):
    def test_uses_worst_nearest_partner_not_worst_cross_pair(self):
        x = np.array([0, 1.5, .1, 1.3])
        d = np.abs(x[:, None] - x[None, :])
        self.assertAlmostEqual(pair_score(d, [0, 1], [2, 3], RULE), .2)
        self.assertAlmostEqual(d[np.ix_([0, 1], [2, 3])].max(), 1.4)
        self.assertAlmostEqual(pair_score(d, [0], [2, 3], RULE), 1.3)

    def test_unsupported_endpoint_is_omitted_and_still_reported(self):
        d = np.array([[np.inf, .1, np.inf, np.inf], [.1, np.inf, .2, .8],
                      [np.inf, .2, np.inf, .3], [np.inf, .8, .3, np.inf]])
        self.assertAlmostEqual(pair_score(d, [0, 1], [2, 3], RULE), .8)
        self.assertAlmostEqual(pair_score(d, [0, 1], [2, 3]), .35)
        rows = agglomerate(d, RULE)
        self.assertEqual([(r['left'], r['right']) for r in rows], [(0, 1), (2, 4), (3, 5)])
        self.assertEqual((rows[1]['unsupported_left'], rows[1]['unsupported_right']), (0, 1))
        self.assertEqual((rows[2]['unsupported_left'], rows[2]['unsupported_right']), (0, 1))
        self.assertTrue(math.isinf(pair_score(d, [0], [2, 3], RULE)))

    def test_full_histories_match_independent_exhaustive_selection(self):
        for seed in range(8):
            d = angles(2400 + seed)
            rng = np.random.default_rng(seed)
            for i in range(len(d)):
                for j in range(i + 1, len(d)):
                    if i % 3 == j % 3 or (abs(i - j) > 1 and rng.random() < .15):
                        d[i, j] = d[j, i] = np.inf
            active = {i: [i] for i in range(len(d))}
            for row in agglomerate(d, RULE):
                score, a, b = min((exhaustive_score(d, av, bv), a, b)
                                 for a, av in active.items() for b, bv in active.items() if a < b)
                self.assertEqual((row['left'], row['right']), (a, b))
                self.assertAlmostEqual(row['merge_score'], score)
                self.assertAlmostEqual(pair_score(d, active[a], active[b], RULE), score)
                for side, other in (('left', 'right'), ('right', 'left')):
                    source, target = active[row[side]], active[row[other]]
                    self.assertEqual(row['unsupported_' + side], sum(
                        not any(math.isfinite(d[i, j]) for j in target) for i in source))
                active[row['id']] = active.pop(a) + active.pop(b)

    def test_actual_angular_reversal_is_not_flattened(self):
        rows = agglomerate(angles(3, 10), RULE)
        self.assertAlmostEqual(rows[-2]['merge_score'], 1.8536116146120896)
        self.assertAlmostEqual(rows[-1]['merge_score'], 1.73798099188955)
        self.assertLess(rows[-1]['merge_score'], rows[-2]['merge_score'])

    def test_strictly_increasing_transform_preserves_memberships(self):
        d = angles(29)
        d[0, 3] = d[3, 0] = np.inf
        original = agglomerate(d, RULE)
        changed = agglomerate(d * d, RULE)
        self.assertEqual([(r['left'], r['right']) for r in original],
                         [(r['left'], r['right']) for r in changed])
        for a, b in zip(original, changed):
            self.assertAlmostEqual(a['merge_score'] ** 2, b['merge_score'])

    def test_ties_and_disconnected_input(self):
        rows = agglomerate(np.ones((4, 4)), RULE)
        self.assertEqual([(r['left'], r['right']) for r in rows], [(0, 1), (2, 3), (4, 5)])
        with self.assertRaisesRegex(ValueError, 'connected'):
            agglomerate(np.array([[np.inf, .2, np.inf], [.2, np.inf, np.inf],
                                  [np.inf, np.inf, np.inf]]), RULE)


if __name__ == '__main__':
    unittest.main()
