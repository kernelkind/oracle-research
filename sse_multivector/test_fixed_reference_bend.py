import unittest

import numpy as np

from sse_multivector.fixed_reference_bend import derive_boundary, mean_support, qualify_boundary


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


if __name__ == '__main__':
    unittest.main()
