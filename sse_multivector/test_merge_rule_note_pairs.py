"""Source-note weighting checks against the actual merge runner."""

import math
import unittest

import numpy as np

from merge_rule_experiment import agglomerate, pair_score


class NotePairMergeTests(unittest.TestCase):
    def test_unequal_orientation_counts_are_pooled_per_unordered_note_pair(self):
        d = np.full((6, 6), np.inf)
        for i, j, value in [(0, 3, .2), (1, 3, .2), (2, 4, 1.0),
                            (0, 5, .8), (1, 5, .8), (2, 5, .7)]:
            d[i, j] = d[j, i] = value
        sources = ['P', 'P', 'Q', 'Q', 'P', 'R']
        expected = ((.2 + .2 + 1.0) / 3 + .8 + .7) / 3
        for left, right in [([0, 1, 2], [3, 4, 5]), ([3, 4, 5], [0, 1, 2])]:
            self.assertAlmostEqual(pair_score(d, left, right, rule='note_pair_mean',
                                              source_note_ids=sources), expected)
        self.assertNotAlmostEqual(expected, pair_score(d, [0, 1, 2], [3, 4, 5], 'average'))

    def test_singletons_and_absent_note_pairs(self):
        d = np.array([[np.inf, np.inf, .2, .8], [np.inf, np.inf, .2, .8],
                      [.2, .2, np.inf, .7], [.8, .8, .7, np.inf]])
        sources = ['P', 'P', 'Q', 'R']
        self.assertAlmostEqual(pair_score(d, [0], [2], 'note_pair_mean', sources), .2)
        self.assertAlmostEqual(pair_score(d, [3], [0, 1, 2], 'note_pair_mean', sources), .75)
        self.assertTrue(math.isinf(pair_score(d, [0], [1], 'note_pair_mean', sources)))
        unique = d[np.ix_([0, 2, 3], [0, 2, 3])]
        self.assertEqual(agglomerate(unique, 'note_pair_mean', ['P', 'Q', 'R']),
                         agglomerate(unique, 'average'))

    def test_real_angular_inversion_is_retained(self):
        x = np.array([[.540302305868140, .841470984807897, 0], [1, 0, 0],
                      [.267498828624587, .561287153046015, .783199277649037],
                      [.531860721374355, -.611509699255782, .585815722540163]])
        x /= np.linalg.norm(x, axis=1)[:, None]
        d = np.arccos(np.clip(x @ x.T, -1, 1))
        d[0, 2] = d[2, 0] = np.inf
        rows = agglomerate(d, 'note_pair_mean', ['P', 'Q', 'P', 'R'])
        self.assertEqual([(r['left'], r['right']) for r in rows], [(0, 1), (2, 4), (3, 5)])
        for row, expected in zip(rows, [1.0, 1.30, 1.2825]):
            self.assertAlmostEqual(row['merge_score'], expected)
        self.assertLess(rows[-1]['merge_score'], rows[-2]['merge_score'])

    def test_every_merge_matches_independent_exhaustive_note_pair_means(self):
        for seed in range(8):
            rng = np.random.default_rng(80 + seed)
            x = rng.normal(size=(12, 5))
            x /= np.linalg.norm(x, axis=1)[:, None]
            d = np.arccos(np.clip(x @ x.T, -1, 1))
            sources = [str(i // 3) for i in range(12)]
            for i in range(12):
                for j in range(12):
                    if sources[i] == sources[j]:
                        d[i, j] = np.inf
            active = {i: [i] for i in range(12)}
            for row in agglomerate(d, 'note_pair_mean', sources):
                candidates = []
                for a, av in active.items():
                    for b, bv in active.items():
                        if a >= b:
                            continue
                        pairs = {}
                        for i in av:
                            for j in bv:
                                if math.isfinite(d[i, j]):
                                    key = tuple(sorted((sources[i], sources[j])))
                                    pairs.setdefault(key, []).append(d[i, j])
                        if pairs:
                            means = [sum(values) / len(values) for values in pairs.values()]
                            candidates.append((sum(means) / len(means), a, b))
                score, a, b = min(candidates)
                self.assertEqual((row['left'], row['right']), (a, b))
                self.assertAlmostEqual(row['merge_score'], score)
                self.assertEqual(row['unsupported_left'], sum(
                    not any(math.isfinite(d[i, j]) for j in active[b]) for i in active[a]))
                self.assertEqual(row['unsupported_right'], sum(
                    not any(math.isfinite(d[i, j]) for i in active[a]) for j in active[b]))
                active[row['id']] = active.pop(a) + active.pop(b)
            self.assertEqual(sorted(next(iter(active.values()))), list(range(12)))

    def test_source_provenance_must_match_the_frozen_edge_policy(self):
        d = np.array([[0, .2], [.2, 0]])
        for invalid in [None, ['P'], ['P', ''], [frozenset({'P', 'Q'}), 'R']]:
            with self.assertRaisesRegex(ValueError, 'source note'):
                agglomerate(d, 'note_pair_mean', invalid)
        with self.assertRaisesRegex(ValueError, 'same-note'):
            agglomerate(d, 'note_pair_mean', ['P', 'P'])


if __name__ == '__main__':
    unittest.main()
