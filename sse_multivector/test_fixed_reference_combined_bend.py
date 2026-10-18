import copy
import math
import unittest

from sse_multivector.fixed_reference_combined_bend import derive_boundaries
from sse_multivector.fixed_reference_note_bend import derive_boundaries as note_bend


class FixedReferenceCombinedBendTests(unittest.TestCase):
    def test_group_bend_tightens_a_boundary_limited_by_other_groups(self):
        scores = {'a': [.8, .7, .6, .3, .29, .28], 'b': [.8, .79, .78, .01]}
        notes = {'a': list('abcdef'), 'b': list('ghij')}
        original = copy.deepcopy((scores, notes))
        old = note_bend(scores, notes)
        combined = derive_boundaries(scores, notes)
        self.assertGreater(combined['groups']['a']['threshold'], old['groups']['a']['threshold'])
        self.assertAlmostEqual(combined['groups']['a']['threshold'], math.sqrt(.6 * .3))
        for group in scores:
            self.assertGreaterEqual(combined['groups'][group]['threshold'], old['groups'][group]['threshold'])
            for field in ['minimum', 'median', 'note_scores']:
                self.assertEqual(combined['groups'][group][field], old['groups'][group][field])
        self.assertEqual(combined['notes'], old['notes'])
        self.assertEqual((scores, notes), original)

    def test_missing_or_nonpositive_group_bend_preserves_the_current_boundary(self):
        for scores, notes in [({}, {}), ({'a': [.6, .4]}, {'a': ['n1', 'n2']}),
                              ({'a': [.5, .5]}, {'a': ['n1', 'n1']}),
                              ({'a': [0., .5]}, {'a': ['n1', 'n2']}),
                              ({'a': [float('nan'), .5]}, {'a': ['n1', 'n2']})]:
            with self.subTest(scores=scores):
                old = note_bend(scores, notes)
                self.assertEqual(derive_boundaries(scores, notes)['groups'], old['groups'])

    def test_group_and_member_order_do_not_change_thresholds(self):
        scores = {'a': [.8, .7, .6, .3, .29, .28], 'b': [.8, .79, .78, .01]}
        notes = {'a': list('abcdef'), 'b': list('ghij')}
        expected = derive_boundaries(scores, notes)
        actual = derive_boundaries({'b': scores['b'][::-1], 'a': scores['a'][::-1]},
                                   {'b': notes['b'][::-1], 'a': notes['a'][::-1]})
        self.assertEqual(expected['groups'], actual['groups'])


if __name__ == '__main__':
    unittest.main()
