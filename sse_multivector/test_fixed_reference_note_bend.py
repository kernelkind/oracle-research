import copy
import math
import unittest

from sse_multivector.fixed_reference_note_bend import derive_boundaries
from sse_multivector.fixed_reference_note_coverage import derive_boundaries as preserve


class FixedReferenceNoteBendTests(unittest.TestCase):
    def test_weak_note_no_longer_forces_all_notes_to_pass(self):
        scores = {'g': [.60, .58, .56, .05]}
        notes = {'g': list('abcd')}
        original = copy.deepcopy((scores, notes))
        old = preserve(scores, notes)
        result = derive_boundaries(scores, notes)
        self.assertEqual(old['groups']['g']['threshold'], .05)
        self.assertEqual(result['selection'], 'note_bend')
        self.assertAlmostEqual(result['groups']['g']['threshold'], math.sqrt(.56 * .05))
        self.assertGreater(result['groups']['g']['threshold'], .05)
        self.assertLess(result['groups']['g']['threshold'], .56)
        self.assertIn('d', result['notes'])
        self.assertEqual(result['groups']['g']['note_scores'], old['groups']['g']['note_scores'])
        self.assertEqual((scores, notes), original)

    def test_each_note_contributes_its_best_route_once(self):
        result = derive_boundaries({'g': [.60, .58, .56, .05]}, {'g': list('abcd')})
        repeated = derive_boundaries({'g': [.60, .60, .58, .56, .05]},
                                     {'g': list('aabcd')})
        self.assertEqual(result['note_curve'], repeated['note_curve'])
        self.assertEqual(result['multiplier_ratio'], repeated['multiplier_ratio'])
        self.assertEqual(result['groups'], repeated['groups'])

    def test_no_bend_preserves_exact_original_boundary_and_limiting_notes(self):
        for scores, notes in [({'g': [.6, .4]}, {'g': list('ab')}),
                              ({'g': [.5, .5, .5]}, {'g': list('abc')}),
                              ({'g': [.8, .6, .45]}, {'g': list('abc')})]:
            with self.subTest(scores=scores):
                old = preserve(scores, notes)
                result = derive_boundaries(scores, notes)
                self.assertEqual(result['selection'], 'minimum_no_note_bend')
                for key in ['groups', 'notes', 'multiplier_ratio', 'limiting_notes']:
                    self.assertEqual(result[key], old[key])

    def test_permutation_and_group_order_preserve_result(self):
        scores = {'b': [.6, .58, .56, .05], 'a': [.5, .48, .46, .02]}
        notes = {'b': list('abcd'), 'a': list('abce')}
        expected = derive_boundaries(scores, notes)
        actual = derive_boundaries({'a': [.02, .46, .5, .48],
                                    'b': [.05, .56, .6, .58]},
                                   {'a': list('ecab'), 'b': list('dcab')})
        self.assertEqual(actual, expected)

    def test_unavailable_or_zero_support_cannot_invent_log_boundary(self):
        for scores, notes in [({}, {}), ({'g': [.5]}, {'g': ['a']}),
                              ({'g': [0., 0.]}, {'g': list('ab')}),
                              ({'g': [float('nan'), .5]}, {'g': list('ab')}),
                              ({'g': [.5, .4, 0.]}, {'g': list('abc')})]:
            with self.subTest(scores=scores):
                old = preserve(scores, notes)
                result = derive_boundaries(scores, notes)
                self.assertNotEqual(result['selection'], 'note_bend')
                self.assertEqual(result['groups'], old['groups'])


if __name__ == '__main__':
    unittest.main()
