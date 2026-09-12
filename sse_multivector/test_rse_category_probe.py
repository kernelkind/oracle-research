"""Tests for the released RSE transfer experiment's actual scoring path."""
import math
import unittest

import torch

from rse_category_probe import pair_scores, analyze_scores, project_cls
from hierarcaps_category_probe import prepare_inputs
from test_hierarcaps_category_probe import fixture


class RSECategoryProbeTests(unittest.TestCase):
    def test_relation_is_added_to_raw_first_vector_before_cosine(self):
        result = pair_scores([2., 0.], [0., 3.], [0., 2.])
        self.assertAlmostEqual(result['entailment'], math.sqrt(.5))
        self.assertAlmostEqual(result['cosine'], 0.)
        self.assertNotAlmostEqual(result['entailment'], 2 / math.sqrt(5))
        self.assertAlmostEqual(pair_scores([0., 3.], [2., 0.], [0., 2.])['entailment'], 0.)

    def test_cosine_is_symmetric_but_entailment_is_not(self):
        a, b, relation = [3., 1.], [1., 4.], [2., -1.]
        forward = pair_scores(a, b, relation)
        reverse = pair_scores(b, a, relation)
        self.assertAlmostEqual(forward['cosine'], reverse['cosine'])
        self.assertNotAlmostEqual(forward['entailment'], reverse['entailment'])

    def test_rejects_wrong_dimensions_nonfinite_and_zero_vectors(self):
        for a, b, relation in (([1.], [1., 0.], [0.]),
                               ([math.nan, 1.], [1., 0.], [0., 0.]),
                               ([0., 0.], [1., 0.], [0., 1.]),
                               ([1., 0.], [1., 0.], [-1., 0.])):
            with self.subTest(a=a, b=b, relation=relation), self.assertRaises(ValueError):
                pair_scores(a, b, relation)

    def test_projection_uses_first_token_and_trained_linear_then_tanh(self):
        hidden = torch.tensor([[[2., 3.], [90., 80.]]])
        weight = torch.tensor([[1., 2.], [-1., 0.]])
        bias = torch.tensor([1., 2.])
        actual = project_cls(hidden, weight, bias)
        torch.testing.assert_close(actual, torch.tensor([[9., 0.]]).tanh())

    def test_analysis_checks_child_to_parent_not_reverse(self):
        rows = prepare_inputs(fixture())
        # Child + relation equals parent. Reversing fails this relationship.
        vectors = [[1., 1.], [1., 0.], [1., -1.]] * 2
        result = analyze_scores(rows, vectors, [0., 1.])
        self.assertEqual(len(result['pairs']), 36)
        self.assertEqual(len(result['candidate_comparisons']), 2)
        self.assertEqual(len(result['cross_wording_comparisons']), 8)
        comparison = result['candidate_comparisons'][0]
        self.assertAlmostEqual(comparison['broader_entailment'], 1.)
        self.assertAlmostEqual(comparison['alternative_entailment'], 0.)
        self.assertGreater(comparison['forward_minus_reverse'], 0.)
        self.assertAlmostEqual(comparison['broader_minus_alternative_cosine'], 0.)

    def test_analysis_rejects_missing_vectors(self):
        with self.assertRaises(ValueError):
            analyze_scores(prepare_inputs(fixture()), [[1., 0.]] * 5, [0., 1.])


if __name__ == '__main__':
    unittest.main()
