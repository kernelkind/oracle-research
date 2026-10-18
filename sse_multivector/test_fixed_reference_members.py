import unittest

import numpy as np

from sse_multivector.fixed_reference_members import derive_boundary


class FixedReferenceMemberTests(unittest.TestCase):
    def setUp(self):
        self.affinities = np.array([[1, .8, .4, .2], [.8, 1, .5, .3],
                                    [.4, .5, 1, .1], [.2, .3, .1, 1]])

    def test_uses_exact_weakest_cross_note_mean_without_fitting(self):
        result = derive_boundary(self.affinities, list('abcd'), [0, 1, 2])
        self.assertEqual(result['status'], 'boundary')
        self.assertEqual(result['threshold'], (.4 + .5) / 2)
        self.assertEqual(result['weakest_indices'], [2])
        self.assertEqual(result['member_scores'], [dict(index=0, score=(.8 + .4) / 2),
                                                   dict(index=1, score=(.8 + .5) / 2),
                                                   dict(index=2, score=(.4 + .5) / 2)])

    def test_excludes_entire_source_note_not_only_self(self):
        result = derive_boundary(self.affinities, list('aabc'), [0, 1, 2])
        self.assertEqual(result['threshold'], .4)
        self.assertEqual(result['member_scores'], [dict(index=0, score=.4),
                                                   dict(index=1, score=.5),
                                                   dict(index=2, score=(.4 + .5) / 2)])
        excluded = derive_boundary(self.affinities, list('aabc'), [0, 1, 2, 3], excluded_notes={'a'})
        self.assertEqual(excluded['group_indices'], [2, 3])
        self.assertEqual(excluded['threshold'], .1)
        self.assertEqual(excluded['weakest_indices'], [2, 3])

    def test_nonmembers_cannot_change_threshold_or_inputs(self):
        original = self.affinities.copy()
        a = derive_boundary(self.affinities, list('abcd'), [0, 1, 2])
        changed = original.copy()
        changed[3, :3] = changed[:3, 3] = 1
        b = derive_boundary(changed, list('abcd'), [0, 1, 2])
        self.assertEqual(a, b)
        np.testing.assert_array_equal(self.affinities, original)

    def test_no_cross_note_members_leaves_boundary_unavailable(self):
        for group, notes, excluded, status in [([0, 1], list('aabc'), (), 'no_cross_note_reference'),
                                               ([0], list('abcd'), (), 'no_cross_note_reference'),
                                               ([0, 1], list('abcd'), {'a', 'b'}, 'no_group_reference'),
                                               ([], list('abcd'), (), 'no_group_reference')]:
            with self.subTest(group=group, excluded=excluded):
                result = derive_boundary(self.affinities, notes, group, excluded_notes=excluded)
                self.assertEqual(result['status'], status)
                self.assertIsNone(result['threshold'])

    def test_directed_scores_preserve_query_to_reference_orientation(self):
        # Rows represent incoming meanings; columns represent reference titles.
        # Two entries share note a, so neither can provide evidence for the other.
        affinities = np.array([[1, .9, .2], [.8, 1, .4], [.7, .5, 1]])
        result = derive_boundary(affinities, list('aab'), [0, 1, 2])
        self.assertEqual(result['member_scores'], [dict(index=0, score=.2),
                                                   dict(index=1, score=.4),
                                                   dict(index=2, score=.6)])
        self.assertEqual(result['threshold'], .2)
        transposed = derive_boundary(affinities.T, list('aab'), [0, 1, 2])
        self.assertAlmostEqual(transposed['threshold'], .3)
        np.testing.assert_array_equal(affinities,
                                      [[1, .9, .2], [.8, 1, .4], [.7, .5, 1]])

    def test_rejects_unaligned_invalid_or_duplicate_inputs(self):
        for a, notes, group in [(self.affinities, list('abc'), [0, 1]),
                                (self.affinities[:3], list('abcd'), [0, 1]),
                                (self.affinities, list('abcd'), [0, 0]),
                                (self.affinities * 2, list('abcd'), [0, 1])]:
            with self.subTest(group=group, notes=notes):
                with self.assertRaises(ValueError):
                    derive_boundary(a, notes, group)


if __name__ == '__main__':
    unittest.main()
