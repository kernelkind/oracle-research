import json
import unittest

import numpy as np
from scipy import sparse

from sse_multivector.fixed_reference_bend import derive_boundary, mean_support, qualify_boundary, separation_bounds


def reference(pair=.96):
    a = np.full((9, 9), .1)
    np.fill_diagonal(a, 1)
    a[0, 1] = a[1, 0] = pair
    for j, value in enumerate([.95, .94, .93, .3, .28, .27, .26], 2):
        a[j, :2] = a[:2, j] = value
    return a, list('abcdefghi')


class FixedReferenceBendTests(unittest.TestCase):
    def test_reference_plateau_defines_boundary_without_outsiders(self):
        a, notes = reference()
        r = derive_boundary(a, notes, [0, 1])
        self.assertEqual(r['status'], 'boundary')
        self.assertAlmostEqual(r['threshold'], (.93 + .3) / 2)

    def test_whole_note_exclusion_removes_context_and_group_references(self):
        a, notes = reference()
        r = derive_boundary(a, notes, [0, 1], excluded_notes={'a'})
        self.assertNotIn(0, r['context_indices'])
        self.assertEqual(r['group_indices'], [1])
        unavailable = derive_boundary(a, notes, [0, 1], excluded_notes={'a', 'b'})
        self.assertIsNone(unavailable['threshold'])
        self.assertEqual(unavailable['status'], 'no_group_reference')

    def test_duplicating_an_entry_within_its_note_does_not_move_boundary(self):
        a, notes = reference()
        baseline = derive_boundary(a, notes, [0, 1])
        positions = list(range(9)) + [3]
        duplicated = derive_boundary(a[np.ix_(positions, positions)], notes + [notes[3]], [0, 1])
        self.assertEqual(baseline['threshold'], duplicated['threshold'])
        np.testing.assert_allclose([r['note_mass'] for r in baseline['curve']],
                                   [r['note_mass'] for r in duplicated['curve']])

    def test_straight_curve_does_not_manufacture_bend(self):
        a = np.full((8, 8), .1)
        np.fill_diagonal(a, 1)
        a[0, 1:] = a[1:, 0] = np.linspace(.9, .3, 7)
        r = derive_boundary(a, list('abcdefgh'), [0])
        self.assertIsNone(r['threshold'])
        self.assertEqual(r['status'], 'no_positive_bend')

    def test_insufficient_reference_structure_is_unresolved(self):
        a = np.full((3, 3), .1)
        np.fill_diagonal(a, 1)
        r = derive_boundary(a, ['a', 'b', 'c'], [0, 1])
        self.assertIsNone(r['threshold'])

    def test_group_must_recover_its_members_without_their_source_notes(self):
        a, notes = reference()
        good = qualify_boundary(a, notes, [0, 1])
        self.assertTrue(good['eligible'])
        self.assertEqual(len(good['folds']), 2)
        a, notes = reference(pair=.1)
        bad = qualify_boundary(a, notes, [0, 1])
        self.assertFalse(bad['eligible'])
        self.assertTrue(any(r['failed_indices'] for r in bad['folds']))

    def test_independent_queries_and_inputs_are_unchanged(self):
        a, notes = reference()
        threshold = qualify_boundary(a, notes, [0, 1])['base']['threshold']
        q = np.array([[.8, .8] + [.1] * 7, [.2, .2] + [.1] * 7])
        before = a.copy(), q.copy()
        together = mean_support(q, ['x', 'y'], notes, [0, 1])
        apart = np.array([mean_support(q[j:j+1], [['x'], ['y']][j], notes, [0, 1])[0]
                          for j in range(2)])
        np.testing.assert_array_equal(together, apart)
        np.testing.assert_array_equal(together >= threshold, [True, False])
        changed = mean_support(q[[1, 0, 0]], ['y', 'x', 'x'], notes, [0, 1])
        np.testing.assert_array_equal(changed, together[[1, 0, 0]])
        np.testing.assert_array_equal(a, before[0])
        np.testing.assert_array_equal(q, before[1])
        self.assertTrue(np.isnan(mean_support(q[:1], ['a'], ['a'] * 9, [0, 1])[0]))

    def test_rejects_invalid_reference_affinities(self):
        for a in [np.array([[1., -.1], [-.1, 1.]]), np.array([[1., np.nan], [np.nan, 1.]])]:
            with self.assertRaises(ValueError):
                derive_boundary(a, ['a', 'b'], [0, 1])

    def test_member_anchor_keeps_weakest_member_as_curve_start(self):
        a = np.full((10, 10), .1)
        np.fill_diagonal(a, 1)
        for i, j, score in [(0, 1, .9), (0, 2, .7), (1, 2, .5)]:
            a[i, j] = a[j, i] = score
        for j, score in enumerate([.99, .55, .5, .2, .18, .16, .14], 3):
            a[j, :3] = a[:3, j] = score
        r = derive_boundary(a, list('abcdefghij'), [0, 1, 2], anchor='members')
        self.assertAlmostEqual(r['anchor_score'], .6)
        self.assertEqual(r['fit_start_level'], r['anchor_level'])
        self.assertAlmostEqual(r['curve'][r['fit_start_level']]['score'], .6)
        self.assertAlmostEqual(r['threshold'], (.5 + .2)/2)

    def test_member_anchor_cannot_use_same_note_support(self):
        a, notes = reference()
        notes[1] = notes[0]
        r = derive_boundary(a, notes, [0, 1], anchor='members')
        self.assertEqual(r['status'], 'no_member_anchor')
        self.assertIsNone(r['threshold'])

    def test_member_anchor_is_reestablished_after_whole_note_exclusion(self):
        a, notes = reference()
        r = qualify_boundary(a, notes, [0, 1], anchor='members')
        self.assertIsNotNone(r['base']['threshold'])
        self.assertFalse(r['eligible'])
        self.assertTrue(all(f['boundary']['status']=='no_member_anchor' for f in r['folds']))

    def test_unknown_anchor_is_rejected(self):
        a, notes = reference()
        with self.assertRaises(ValueError):
            derive_boundary(a, notes, [0, 1], anchor='unknown')

    def test_fusion_context_uses_members_and_direct_neighbors_only(self):
        a, notes = reference()
        c = np.eye(9)
        for i, j in [(0, 2), (1, 3), (3, 4)]:
            c[i, j] = c[j, i] = .2
        r = derive_boundary(a, notes, [0, 1], context_connections=sparse.csr_matrix(c))
        self.assertEqual(r['context_indices'], [0, 1, 2, 3])
        self.assertNotIn(4, r['context_indices'])
        json.dumps(r, allow_nan=False)

    def test_exclusion_recomputes_neighbors_from_remaining_members(self):
        a, notes = reference()
        c = np.eye(9)
        for i, j in [(0, 2), (1, 3)]:
            c[i, j] = c[j, i] = .2
        r = derive_boundary(a, notes, [0, 1], excluded_notes={'a'},
                            context_connections=sparse.csr_matrix(c))
        self.assertEqual(r['group_indices'], [1])
        self.assertEqual(r['context_indices'], [3])

    def test_whole_note_folds_use_the_same_fixed_connections(self):
        a, notes = reference()
        c = np.eye(9)
        for i, j in [(0, 2), (1, 3)]:
            c[i, j] = c[j, i] = .2
        r = qualify_boundary(a, notes, [0, 1], context_connections=sparse.csr_matrix(c))
        self.assertEqual(r['base']['context_indices'], [0, 1, 2, 3])
        self.assertEqual(r['folds'][0]['boundary']['context_indices'], [3])
        self.assertEqual(r['folds'][1]['boundary']['context_indices'], [2])

    def test_context_weight_units_do_not_change_support_or_mutate_graph(self):
        a, notes = reference()
        c = sparse.csr_matrix(np.ones((9, 9)))
        before = c.data.copy(), c.indices.copy(), c.indptr.copy(), a.copy()
        baseline = derive_boundary(a, notes, [0, 1])
        local = derive_boundary(a, notes, [0, 1], context_connections=c)
        scaled = derive_boundary(a, notes, [0, 1], context_connections=c*1000)
        self.assertEqual(baseline, local)
        self.assertEqual(local, scaled)
        for actual, expected in zip([c.data, c.indices, c.indptr, a], before):
            np.testing.assert_array_equal(actual, expected)

    def test_invalid_context_connections_are_rejected(self):
        a, notes = reference()
        for c in [np.eye(8), np.full((9, 9), np.nan), -np.eye(9), np.triu(np.ones((9, 9)))]:
            with self.assertRaises(ValueError):
                derive_boundary(a, notes, [0, 1], context_connections=sparse.csr_matrix(c))


class ScoreSeparationTests(unittest.TestCase):
    def test_group_specific_boundaries_can_succeed_when_one_root_boundary_cannot(self):
        r = separation_bounds([[.8, .05], [.1, .12]], [[.6, .1]])
        np.testing.assert_array_equal(r['recoverable'], [True, True])
        np.testing.assert_array_equal(r['common_boundary_recoverable'], [True, False])
        np.testing.assert_array_equal(r['recoverable_by_group'], [[True, False], [False, True]])

    def test_different_rejections_can_block_different_groups(self):
        r = separation_bounds([[.5, .5]], [[.6, .1], [.1, .6]])
        np.testing.assert_array_equal(r['recoverable'], [False])
        np.testing.assert_array_equal(r['blocking_rejection_indices'], [0, 1])

    def test_a_score_tie_cannot_be_separated(self):
        r = separation_bounds([[.5]], [[.5]])
        self.assertFalse(r['recoverable'][0])
        self.assertEqual(r['margins'][0, 0], 0)

    def test_bounds_are_necessary_and_sufficient_on_the_supplied_finite_scores(self):
        positive = np.array([[.8, .05], [.1, .12], [.4, .09]])
        negative = np.array([[.6, .1], [.3, .08]])
        r = separation_bounds(positive, negative)
        diagnostic_boundaries = np.nextafter(r['rejection_maxima'], np.inf)
        np.testing.assert_array_equal(np.any(positive >= diagnostic_boundaries, axis=1), r['recoverable'])
        self.assertFalse(np.any(negative >= diagnostic_boundaries))

    def test_missing_support_is_not_an_automatic_rejection_or_a_match(self):
        r = separation_bounds([[np.nan, .4], [np.nan, np.nan]], [[.9, np.nan]])
        np.testing.assert_array_equal(r['recoverable'], [True, False])
        self.assertTrue(np.isnan(r['rejection_maxima'][1]))
        self.assertEqual(r['blocking_rejection_indices'][1], -1)

    def test_reordering_and_duplicating_useful_entries_does_not_change_bounds(self):
        positive = np.array([[.8, .05], [.1, .12]])
        negative = np.array([[.6, .1], [.3, .08]])
        before = positive.copy(), negative.copy()
        original = separation_bounds(positive, negative)
        changed = separation_bounds(positive[[1, 0, 0]], negative[::-1])
        np.testing.assert_array_equal(changed['rejection_maxima'], original['rejection_maxima'])
        np.testing.assert_array_equal(changed['recoverable'], original['recoverable'][[1, 0, 0]])
        np.testing.assert_array_equal(positive, before[0])
        np.testing.assert_array_equal(negative, before[1])

    def test_requires_rejection_controls_and_aligned_valid_score_matrices(self):
        for positive, negative in [([[.5]], np.empty((0, 1))), ([[.5]], [[.3, .2]]),
                                   ([[np.inf]], [[.3]]), ([[.5]], [[-.1]]),
                                   ([[1.1]], [[.2]]), (np.empty((1, 0)), np.empty((1, 0)))]:
            with self.assertRaises(ValueError):
                separation_bounds(positive, negative)


if __name__ == '__main__':
    unittest.main()
