import math
import unittest

import numpy as np

from sse_multivector.fixed_reference_member_distribution import derive_boundary


class FixedReferenceMemberDistributionTests(unittest.TestCase):
    def test_bend_separates_isolated_weak_member_without_changing_scores(self):
        scores = np.array([.60, .58, .56, .05])
        before = scores.copy()
        result = derive_boundary(scores, list('abcd'))
        self.assertEqual(result['selection'], 'member_bend')
        self.assertEqual(result['selected_level'], 2)
        self.assertAlmostEqual(result['threshold'], math.sqrt(.56 * .05))
        self.assertGreater(result['threshold'], .05)
        self.assertLess(result['threshold'], .56)
        np.testing.assert_array_equal(scores, before)

    def test_two_or_equal_levels_retain_existing_minimum(self):
        for scores, notes in [([.6, .6], list('ab')),
                              ([.8, .8, .4, .4], list('abcd')),
                              ([.5, .5, .5], list('abc'))]:
            with self.subTest(scores=scores):
                result = derive_boundary(scores, notes)
                self.assertEqual(result['selection'], 'minimum_insufficient_levels')
                self.assertEqual(result['threshold'], min(scores))

    def test_log_linear_scores_retain_minimum_without_spurious_bend(self):
        result = derive_boundary([.8, .6, .45], list('abc'))
        self.assertEqual(result['selection'], 'minimum_no_positive_bend')
        self.assertEqual(result['threshold'], .45)

    def test_numerically_equal_logs_cannot_create_a_bend(self):
        a = .001
        b = np.nextafter(a, 1.)
        c = np.nextafter(b, 1.)
        self.assertEqual(math.log(a), math.log(c))
        result = derive_boundary([a, b, c], list('abc'))
        self.assertEqual(result['selection'], 'minimum_no_positive_bend')
        self.assertEqual(result['threshold'], a)

    def test_source_notes_have_equal_mass_and_tied_scores_share_level(self):
        result = derive_boundary([.6, .6, .58, .05], list('aabc'))
        self.assertEqual([r['note_mass'] for r in result['curve']], [1., 1., 1.])
        self.assertEqual([r['cumulative_note_mass'] for r in result['curve']], [1., 2., 3.])
        duplicate = derive_boundary([.6, .58, .05], list('abc'))
        self.assertEqual(result['threshold'], duplicate['threshold'])

    def test_permutation_preserves_curve_and_boundary(self):
        scores = np.array([.60, .58, .56, .05])
        notes = np.array(list('abcd'))
        expected = derive_boundary(scores, notes)
        for order in [[3, 0, 2, 1], [1, 2, 3, 0]]:
            result = derive_boundary(scores[order], notes[order])
            self.assertEqual(result, expected)

    def test_empty_missing_or_zero_support_cannot_invent_boundary(self):
        for scores, notes, status in [([], [], 'no_group_reference'),
                                       ([.5, np.nan], list('ab'), 'no_cross_note_reference'),
                                       ([.5, 0.], list('ab'), 'nonpositive_member_support')]:
            with self.subTest(scores=scores):
                result = derive_boundary(scores, notes)
                self.assertEqual(result['status'], status)
                self.assertIsNone(result['threshold'])

    def test_invalid_or_unaligned_scores_are_rejected(self):
        for scores, notes in [([.5], list('ab')), ([[.5]], ['a']),
                              ([np.inf], ['a']), ([-.1], ['a']), ([1.1], ['a'])]:
            with self.subTest(scores=scores):
                with self.assertRaises(ValueError):
                    derive_boundary(scores, notes)


if __name__ == '__main__':
    unittest.main()
