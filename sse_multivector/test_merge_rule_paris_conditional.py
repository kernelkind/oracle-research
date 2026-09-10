"""Conditional expected connections, with original affinities held fixed."""

import math
import unittest

import numpy as np

from merge_rule_experiment import agglomerate, pair_score


RULE = 'paris_conditional'


def original_graph(d):
    n = len(d)
    w = [[1 - float(d[i, j]) / math.pi
          if i != j and math.isfinite(d[i, j]) else 0
          for j in range(n)] for i in range(n)]
    s = [sum(row) for row in w]
    W = sum(s)
    Z = sum(s[i] * s[j] for i in range(n) for j in range(n) if w[i][j])
    return w, s, W, Z


def expected_score(graph, a, b):
    w, s, W, Z = graph
    cross = sum(w[i][j] for i in a for j in b)
    if not cross:
        return math.inf
    expected = sum(s[i] * s[j] for i in a for j in b if w[i][j])
    return W * expected / (Z * cross)


class ConditionalParisTests(unittest.TestCase):
    def test_omits_forbidden_expectations_but_keeps_original_strengths(self):
        w = np.array([[0, .8, 0, .2], [.8, 0, .7, .3],
                      [0, .7, 0, .9], [.2, .3, .9, 0]])
        d = np.where(w > 0, math.pi * (1 - w), np.inf)
        graph = original_graph(d)
        _, s, W, Z = graph
        self.assertAlmostEqual(Z, W * W - sum(x * x for x in s) - 2 * s[0] * s[2])
        actual = pair_score(d, [0, 1], [2, 3], RULE)
        self.assertAlmostEqual(actual, W * (s[0] * s[3] + s[1] * s[2] + s[1] * s[3]) / (Z * 1.2))
        full_product = pair_score(d, [0, 1], [2, 3], 'paris_linear') * W * W / Z
        self.assertLess(actual, full_product)
        self.assertTrue(math.isinf(pair_score(d, [0], [2], RULE)))

    def test_all_eligible_singleton_scores_share_one_rescaling(self):
        x = np.array([0, .2, 1.0, 1.3, 1.7])
        d = np.abs(x[:, None] - x[None, :])
        d[0, 2] = d[2, 0] = np.inf
        graph = original_graph(d)
        w, _, W, Z = graph
        old, new = [], []
        for i in range(len(d)):
            for j in range(i + 1, len(d)):
                if w[i][j]:
                    a = pair_score(d, [i], [j], 'paris_linear')
                    b = pair_score(d, [i], [j], RULE)
                    self.assertAlmostEqual(b / a, W * W / Z)
                    old.append((a, i, j))
                    new.append((b, i, j))
        self.assertEqual([p[1:] for p in sorted(old)], [p[1:] for p in sorted(new)])

    def test_conditioning_does_not_preserve_strength_marginals(self):
        source = ['P', 'P', 'P', 'Q', 'Q', 'R']
        d = np.array([[np.inf if a == b else 0.0 for b in source] for a in source])
        w, s, W, Z = original_graph(d)
        self.assertEqual((W, Z), (22, 314))
        marginal = sum(s[0] * s[j] / Z for j in range(6) if w[0][j])
        self.assertNotAlmostEqual(marginal, s[0] / W)
        self.assertAlmostEqual(pair_score(d, [0], [3], RULE), 22 * 12 / 314)
        self.assertAlmostEqual(pair_score(d, [3], [5], RULE), 22 * 20 / 314)

    def test_complete_histories_match_independent_exhaustive_scores(self):
        for seed in range(8):
            rng = np.random.default_rng(1900 + seed)
            x = rng.normal(size=(9, 6))
            x /= np.linalg.norm(x, axis=1)[:, None]
            d = np.arccos(np.clip(x @ x.T, -1, 1))
            for i in range(9):
                for j in range(i, 9):
                    if i % 3 == j % 3 or (abs(i - j) > 1 and rng.random() < .15):
                        d[i, j] = d[j, i] = np.inf
            graph = original_graph(d)
            active = {i: [i] for i in range(9)}
            previous = -math.inf
            for row in agglomerate(d, RULE):
                candidates = [(expected_score(graph, av, bv), a, b)
                              for a, av in active.items() for b, bv in active.items() if a < b]
                score, a, b = min(candidates)
                self.assertEqual((row['left'], row['right']), (a, b))
                self.assertAlmostEqual(row['merge_score'], score)
                self.assertAlmostEqual(pair_score(d, active[a], active[b], RULE), score)
                self.assertGreaterEqual(row['merge_score'] + 1e-12, previous)
                self.assertEqual(row['unsupported_left'], sum(
                    not any(math.isfinite(d[i, j]) for j in active[b]) for i in active[a]))
                self.assertEqual(row['unsupported_right'], sum(
                    not any(math.isfinite(d[i, j]) for i in active[a]) for j in active[b]))
                previous = row['merge_score']
                active[row['id']] = active.pop(a) + active.pop(b)

    def test_constant_complete_graph_keeps_exact_id_ties(self):
        d = np.zeros((4, 4))
        rows = agglomerate(d, RULE)
        self.assertEqual([(r['left'], r['right']) for r in rows], [(0, 1), (2, 3), (4, 5)])
        self.assertEqual([r['merge_score'] for r in rows], [1, 1, 1])

    def test_invalid_affinities_and_disconnection_remain_errors(self):
        for angle in (math.pi, math.pi + .1):
            d = np.array([[0, angle], [angle, 0]])
            with self.assertRaisesRegex(ValueError, 'eligible angles'):
                agglomerate(d, RULE)
        for d in (np.full((4, 4), np.inf),
                  np.array([[np.inf, 1, np.inf], [1, np.inf, np.inf], [np.inf] * 3])):
            with self.assertRaisesRegex(ValueError, 'connected'):
                agglomerate(d, RULE)


if __name__ == '__main__':
    unittest.main()
