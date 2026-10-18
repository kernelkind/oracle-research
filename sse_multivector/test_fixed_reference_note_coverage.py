import unittest

import numpy as np

from sse_multivector.fixed_reference_bend import mean_support
from sse_multivector.fixed_reference_members import derive_boundary
from sse_multivector.fixed_reference_note_coverage import derive_boundaries


class FixedReferenceNoteCoverageTests(unittest.TestCase):
    def test_another_group_can_preserve_a_note_without_its_weak_heading(self):
        affinity = np.full((5, 5), .2)
        np.fill_diagonal(affinity, 1.)
        affinity[0, 1] = affinity[1, 0] = .8
        affinity[0, 2] = affinity[2, 0] = .1
        affinity[1, 2] = affinity[2, 1] = .1
        affinity[3, 4] = affinity[4, 3] = .9
        notes = list('abccd')
        groups = {'g': [0, 1, 2], 'h': [3, 4]}
        original = {g: derive_boundary(affinity, notes, indices)
                    for g, indices in groups.items()}
        scores = {g: [r['score'] for r in model['member_scores']]
                  for g, model in original.items()}
        member_notes = {g: [notes[i] for i in indices] for g, indices in groups.items()}
        result = derive_boundaries(scores, member_notes)
        self.assertEqual(result['multiplier'], 1.)
        self.assertEqual(result['groups']['g']['threshold'], .45)
        self.assertEqual(result['groups']['h']['threshold'], .9)
        self.assertEqual(result['notes']['c']['best_groups'], ['h'])
        queries = np.array([[.2, .2, .2, .05, .05], [.7, .7, .4, .1, .1]])
        query_scores = mean_support(queries, ['x', 'y'], notes, groups['g'])
        np.testing.assert_array_equal(query_scores >= original['g']['threshold'], [True, True])
        np.testing.assert_array_equal(query_scores >= result['groups']['g']['threshold'], [False, True])

    def test_a_sole_weak_note_route_limits_tightening(self):
        result = derive_boundaries({'g': [.45, .45, .1], 'h': [.9, .9]},
                                   {'g': list('abc'), 'h': list('de')})
        self.assertEqual(result['groups']['g']['threshold'], .1)
        self.assertEqual(result['groups']['h']['threshold'], .9)
        self.assertEqual(result['limiting_notes'], ['c'])

    def test_each_note_supplies_its_best_heading_once(self):
        result = derive_boundaries({'g': [.6, .1, .5, .4]}, {'g': list('aabc')})
        self.assertEqual(result['groups']['g']['note_scores'], {'a': .6, 'b': .5, 'c': .4})
        self.assertEqual(result['groups']['g']['median'], .5)
        self.assertEqual(result['groups']['g']['minimum'], .1)
        self.assertEqual(result['groups']['g']['threshold'], .4)
        copied = derive_boundaries({'g': [.6, .1, .5, .4, .1, .6]},
                                   {'g': list('aabcaa')})
        self.assertEqual(result, copied)

    def test_permutation_preserves_results_and_inputs(self):
        scores = {'g': np.array([.45, .45, .1]), 'h': np.array([.9, .9])}
        notes = {'g': list('abc'), 'h': list('cd')}
        before = {g: a.copy() for g, a in scores.items()}
        expected = derive_boundaries(scores, notes)
        changed = derive_boundaries({'h': scores['h'][::-1], 'g': scores['g'][::-1]},
                                    {'h': notes['h'][::-1], 'g': notes['g'][::-1]})
        self.assertEqual(changed, expected)
        for g in scores:
            np.testing.assert_array_equal(scores[g], before[g])

    def test_thresholds_can_disable_a_group_while_preserving_all_note_routes(self):
        scores = {'a': [.5, .3, .3], 'b': [.3, .5, .3],
                  'c': [.3, .3, .5], 'd': [.8, .8, .8]}
        notes = {g: list('xyz') for g in scores}
        result = derive_boundaries(scores, notes)
        self.assertGreater(result['groups']['d']['threshold'], 1)
        for note in 'xyz':
            self.assertTrue(any(s >= result['groups'][g]['threshold']
                                for g in scores for s, n in zip(scores[g], notes[g])
                                if n == note))

    def test_exact_ratio_arithmetic_preserves_limiting_member_at_float_ties(self):
        scores = {'g': [.1, .7, .7], 'h': [.45, .45]}
        notes = {'g': list('abc'), 'h': list('de')}
        result = derive_boundaries(scores, notes)
        self.assertEqual(result['groups']['g']['threshold'], .1)
        for note in 'abcde':
            self.assertTrue(any(s >= result['groups'][g]['threshold']
                                for g in scores for s, n in zip(scores[g], notes[g])
                                if n == note))

    def test_unavailable_groups_and_zero_medians_do_not_invent_normalized_support(self):
        self.assertEqual(derive_boundaries({}, {})['status'], 'no_scaled_groups')
        result = derive_boundaries({'empty': [], 'same': [.5, .5], 'missing': [.4, None],
                                    'zero': [0., 0.], 'valid': [.6, .6]},
                                   {'empty': [], 'same': list('aa'), 'missing': list('ab'),
                                    'zero': list('cd'), 'valid': list('ef')})
        for g in ('empty', 'same', 'missing'):
            self.assertIsNone(result['groups'][g]['threshold'])
        self.assertEqual(result['groups']['zero']['threshold'], 0.)
        self.assertIsNone(result['groups']['zero']['median'])
        self.assertEqual(result['groups']['valid']['threshold'], .6)

    def test_invalid_groups_shapes_scores_and_notes_are_rejected(self):
        for scores, notes in [({'a': [.5]}, {}), ({'a': [.5]}, {'a': []}),
                               ({'a': [[.5]]}, {'a': ['x']}),
                               ({'a': [.5, float('inf')]}, {'a': ['x', 'y']}),
                               ({'a': [-.1, .5]}, {'a': ['x', 'y']}),
                               ({'a': [1.1, .5]}, {'a': ['x', 'y']}),
                               ({'a': [.5, .5]}, {'a': ['x', None]})]:
            with self.subTest(scores=scores, notes=notes):
                with self.assertRaises(ValueError):
                    derive_boundaries(scores, notes)


if __name__ == '__main__':
    unittest.main()
