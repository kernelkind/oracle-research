import math
import unittest

from sse_multivector.reference_view_agreement import summarize
from sse_multivector.reference_view_agreement_boundary import derive_boundary


class ReferenceViewAgreementBoundaryTests(unittest.TestCase):
    def test_production_vector_summaries_feed_the_same_boundary(self):
        gaps = {}
        for group, gap in [('a', .01), ('b', .02), ('c', .03), ('d', .8)]:
            cosine = 1-gap
            summary = summarize([[1, 0], [1, 0]],
                                [[1, 0], [cosine, math.sqrt(1-cosine*cosine)]],
                                ['note1', 'note2'])
            gaps[group] = summary['median_cosine_gap']
        result = derive_boundary(gaps)
        self.assertEqual(result['disabled_groups'], ['d'])
        self.assertAlmostEqual(result['threshold'], .415)

    def test_reference_disagreement_bend_disables_only_the_upper_tail(self):
        gaps = {'a': .01, 'b': .02, 'c': .03, 'd': .8, 'e': -.2}
        result = derive_boundary(gaps)
        self.assertEqual(result['status'], 'boundary')
        self.assertAlmostEqual(result['threshold'], .415)
        self.assertEqual(result['disabled_groups'], ['d'])
        self.assertEqual(gaps['d'], .8)

    def test_exact_ties_share_a_level_with_equal_mass_per_group(self):
        result = derive_boundary({'a': .1, 'b': .2, 'c': .2, 'd': .9})
        self.assertAlmostEqual(result['threshold'], .55)
        self.assertEqual(result['curve'][1]['groups'], ['b', 'c'])
        self.assertEqual(result['curve'][1]['cumulative_groups'], 3)
        self.assertEqual(result['disabled_groups'], ['d'])
        self.assertEqual(result, derive_boundary({'d': .9, 'c': .2, 'b': .2, 'a': .1}))

    def test_missing_nonpositive_small_and_linear_distributions_do_not_gate(self):
        for gaps in [{}, {'a': None}, {'a': -.5, 'b': 0.},
                     {'a': .1, 'b': .2}, {'a': .1, 'b': .1, 'c': .1},
                     {'a': .1, 'b': .2, 'c': .3}]:
            with self.subTest(gaps=gaps):
                result = derive_boundary(gaps)
                self.assertIsNone(result['threshold'])
                self.assertEqual(result['disabled_groups'], [])

    def test_uniform_positive_scaling_preserves_the_selected_groups(self):
        gaps = {'a': .01, 'b': .02, 'c': .03, 'd': .8}
        first = derive_boundary(gaps)
        scaled = derive_boundary({k: 2 * v for k, v in gaps.items()})
        self.assertEqual(first['disabled_groups'], scaled['disabled_groups'])
        self.assertAlmostEqual(2 * first['threshold'], scaled['threshold'])

    def test_invalid_group_ids_or_nonfinite_out_of_range_gaps_are_rejected(self):
        for gaps in [{1: .2}, {'': .2}, {'a': float('nan')},
                     {'a': float('inf')}, {'a': 2.01}, {'a': -2.01}]:
            with self.subTest(gaps=gaps):
                with self.assertRaises(ValueError):
                    derive_boundary(gaps)


if __name__ == '__main__':
    unittest.main()
