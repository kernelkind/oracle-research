"""Original-coordinate membership scoring, independent of tree ancestry."""
import unittest

import numpy as np

from category_membership import score_group, propose_members, local_members


class MembershipTests(unittest.TestCase):
    def test_each_note_counts_once_and_own_note_cannot_support_itself(self):
        similarities = np.array([[1., .9, .6, .4], [.9, 1., .5, .3],
                                 [.6, .5, 1., .2], [.4, .3, .2, 1.]])
        scores = score_group(similarities, ['a', 'a', 'b', 'c'], [0, 1, 2])
        self.assertAlmostEqual(scores['mean'][3], .3)
        self.assertAlmostEqual(scores['second'][3], .2)
        self.assertEqual(scores['support_count'][3], 2)
        self.assertAlmostEqual(scores['mean'][0], .6)
        self.assertEqual(scores['support_count'][0], 1)
        self.assertTrue(np.isnan(scores['second'][0]))
        repeated = score_group(similarities, ['a', 'a', 'b', 'c'], [0, 0, 1, 2])
        np.testing.assert_equal(scores['mean'], repeated['mean'])

    def test_threshold_comes_from_other_notes_not_self_similarity(self):
        similarities = np.array([[1., .8, .9, .4], [.8, 1., .85, .5],
                                 [.9, .85, 1., .95], [.4, .5, .95, 1.]])
        result = propose_members(similarities, ['a', 'b', 'c', 'd'], [0, 1])
        self.assertAlmostEqual(result['threshold'], .8)
        self.assertEqual(result['proposed_rows'], [2])
        self.assertNotIn(3, result['proposed_rows'])
        self.assertEqual(result['anchor_rows'], [0, 1])
        self.assertFalse(result['calibrated_probability'])

    def test_one_note_group_cannot_propose_members(self):
        with self.assertRaisesRegex(ValueError, 'two distinct'):
            propose_members(np.eye(3), ['a', 'a', 'b'], [0, 1])

    def test_duplicate_masks_do_not_reduce_the_note_threshold(self):
        similarities = np.array([[1., .8, .1, .85], [.8, 1., .1, .85],
                                 [.1, .1, 1., .1], [.85, .85, .1, 1.]])
        result = propose_members(similarities, ['a', 'b', 'a', 'c'], [0, 1, 2])
        self.assertAlmostEqual(result['threshold'], .8)
        self.assertEqual(result['proposed_rows'], [3])

    def test_local_support_requires_two_independent_notes_and_their_actual_masks(self):
        similarities = np.array([[1., .8, .9, .2, .2], [.8, 1., .7, .2, .2],
                                 [.9, .7, 1., .95, .96], [.2, .2, .95, 1., .2],
                                 [.2, .2, .96, .2, 1.]])
        notes = ['a', 'b', 'c', 'a', 'c']
        # The best mask from note a is row 3, outside this group. Row 0's
        # membership must not confer membership on every mask of note a.
        result = local_members(similarities, notes, [0, 1])
        self.assertNotIn(2, result['proposed_rows'])
        self.assertEqual(result['neighbors'][2], [3, 1])
        # Admitting the actual supporting mask changes this decision.
        result = local_members(similarities, notes, [0, 1, 3])
        self.assertIn(2, result['proposed_rows'])

    def test_local_support_has_no_same_note_votes_or_recursive_recruitment(self):
        similarities = np.array([[1., .6, .8, .2], [.6, 1., .7, .3],
                                 [.8, .7, 1., .9], [.2, .3, .9, 1.]])
        result = local_members(similarities, ['a', 'b', 'c', 'c'], [0, 1])
        self.assertIn(2, result['proposed_rows'])
        self.assertEqual(result['neighbors'][3], [1, 0])
        result = local_members(similarities, ['a', 'b', 'c', 'd'], [0, 1])
        self.assertNotIn(3, result['proposed_rows'])


if __name__ == '__main__':
    unittest.main()
