"""Tests exercise the same numerical functions used by the offline probe CLI."""
import unittest

import numpy as np
from scipy.cluster.hierarchy import linkage

from sse_multivector.cluster_resampling_probe import (
    branch_members,
    branch_recovery,
    chance_recovery,
    choose_sections,
    group_centroids,
    resample,
)


class ResamplingTests(unittest.TestCase):
    def test_missing_notes_do_not_count_as_changed_group_membership(self):
        original = branch_members(np.array([[0, 1, 1, 2], [2, 3, 2, 3.]]), [0, 1, 2], 3)
        smaller = branch_members(np.array([[0, 1, 2, 2.]]), [0, 2], 3)
        score, matched = branch_recovery(original, smaller, [0, 2])
        self.assertAlmostEqual(score[-1], 1.)
        self.assertTrue(np.isnan(score[3]))  # Only one surviving member: uninformative.
        self.assertEqual(matched[-1], 2)

    def test_changed_connection_lowers_recovery(self):
        base = branch_members(np.array([[0, 1, 1, 2], [2, 3, 1, 2], [4, 5, 3, 4.]]), range(4), 4)
        other = branch_members(np.array([[0, 2, 1, 2], [1, 3, 1, 2], [4, 5, 3, 4.]]), range(4), 4)
        score, _ = branch_recovery(base, other, range(4))
        self.assertAlmostEqual(score[4], .5)
        self.assertAlmostEqual(score[5], .5)
        self.assertAlmostEqual(score[6], 1.)

    def test_whole_tree_has_no_support_beyond_random_membership(self):
        tree = np.array([[0, 1, 1, 2], [2, 3, 1, 2], [4, 5, 3, 4.]])
        members = branch_members(tree, range(4), 4)
        score, null, adjusted = chance_recovery(members, members, list(range(4)),
                                                permutations=16, seed=21)
        self.assertEqual(score[-1], 1.)
        self.assertEqual(null[-1], 1.)
        self.assertEqual(adjusted[-1], 0.)
        self.assertGreater(adjusted[4], 0.)
        self.assertTrue(np.isnan(adjusted[0]))

    def test_shuffle_control_is_deterministic_and_does_not_mutate_tree(self):
        tree = np.array([[0, 1, 1, 2], [2, 3, 1, 2], [4, 5, 3, 4.]])
        members = branch_members(tree, range(4), 4)
        before = members.copy()
        first = chance_recovery(members, members, list(range(4)), permutations=8, seed=13)
        second = chance_recovery(members, members, list(range(4)), permutations=8, seed=13)
        for a, b in zip(first, second):
            np.testing.assert_equal(a, b)
        np.testing.assert_array_equal(members.toarray(), before.toarray())

    def test_sampling_removes_all_entries_of_a_note_together(self):
        vectors = np.array([[1., 0], [0, 1], [.8, .2], [.1, .9]])
        groups = np.array([0, 1, 0, 1])
        notes = np.array([0, 0, 1, 2])
        result = resample(vectors, groups, notes, repeats=8, fraction=2/3, seed=7)
        self.assertEqual(result['sampled_notes'].shape, (8, 2))
        for sampled, trace in zip(result['sampled_notes'], result['sampled_groups']):
            rows = np.isin(notes, sampled)
            gids, centroids = group_centroids(vectors, groups, rows)
            self.assertEqual(gids.tolist(), trace)
            self.assertEqual(centroids.shape[0], len(gids))
        again = resample(vectors, groups, notes, repeats=8, fraction=2/3, seed=7)
        np.testing.assert_equal(result['recoveries'], again['recoveries'])

    def test_full_note_control_recovers_every_nontrivial_branch(self):
        vectors = np.array([[1., 0], [.9, .1], [0, 1], [.1, .9]])
        result = resample(vectors, np.arange(4), np.arange(4), repeats=2, fraction=1, seed=2)
        np.testing.assert_allclose(result['recoveries'][:, 4:], 1.)

    def test_section_selection_counts_distinct_notes_and_preserves_disjoint_groups(self):
        tree = linkage([[0., 0], [.01, 0], [2, 0], [2.01, 0]], method='ward')
        members = branch_members(tree, range(4), 4)
        # Two groups share note 0; this must not count as two notes.
        note_sets = [{0}, {0}, {1}, {2}]
        result = choose_sections(members, note_sets, np.array([0., 0, 0, 0, .1, .1, 1]),
                                 count=2, minimum_notes=3, time_limit=10)
        self.assertEqual(result['coverage'], 3)
        self.assertEqual(len(result['selected']), 2)
        chosen = members[result['selected']].toarray()
        self.assertTrue(np.all(chosen.sum(axis=0) <= 1))

    def test_invalid_shapes_and_sampling_fail(self):
        with self.assertRaises(ValueError):
            resample(np.ones((3, 2)), np.arange(3), np.arange(2), repeats=2, fraction=.8, seed=0)
        with self.assertRaises(ValueError):
            resample(np.ones((3, 2)), np.arange(3), np.arange(3), repeats=2, fraction=0, seed=0)
        with self.assertRaises(ValueError):
            resample(np.ones((3, 2)), np.array([1, 2, 3]), np.arange(3),
                     repeats=2, fraction=1, seed=0)


if __name__ == '__main__':
    unittest.main()
