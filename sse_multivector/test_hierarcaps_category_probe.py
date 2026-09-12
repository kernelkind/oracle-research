"""Category-description preparation and analysis tests; no model runtime required."""
import copy
import math
import unittest

from hierarcaps_category_probe import prepare_inputs, analyze_scores


def fixture():
    return dict(
        experiment_id='HRC03', model_id='malper/hierarcaps-clip-l',
        model_revision='e3aa199d94c438f98628c9697a0b64ef5760b03c',
        cases=[dict(id='case-1', domain='biology', rationale='A fixed comparison.',
                    wordings=[dict(broader='  Organisms\n', narrower='Élan and deer',
                                   alternative='Minerals'),
                              dict(broader='Living things', narrower='Hoofed mammals',
                                   alternative='Rocks')])])


class HierarCapsCategoryProbeTests(unittest.TestCase):
    def test_preparation_preserves_verbatim_text_and_case_metadata(self):
        frozen = fixture()
        frozen['cases'][0]['metadata'] = 'Never encode this metadata.'
        original = copy.deepcopy(frozen)
        rows = prepare_inputs(frozen)
        self.assertEqual(frozen, original)
        self.assertEqual(len(rows), 6)
        self.assertEqual(rows[0], dict(
            id='case-1-w1-broader', case='case-1', domain='biology', wording=1,
            role='broader', text='  Organisms\n', model_input='  Organisms\n'))
        self.assertEqual(rows[-1]['id'], 'case-1-w2-alternative')
        self.assertEqual(rows[1]['model_input'], 'Élan and deer')
        self.assertNotIn('metadata', rows[0])

    def test_requires_frozen_model_and_experiment(self):
        for field in ('model_id', 'model_revision', 'experiment_id'):
            frozen = fixture()
            frozen[field] = 'changed'
            with self.subTest(field=field), self.assertRaises(ValueError):
                prepare_inputs(frozen)

    def test_rejects_missing_empty_and_nonstring_descriptions(self):
        for text in ('', ' \n\t', None, 123, ['description']):
            frozen = fixture()
            frozen['cases'][0]['wordings'][0]['broader'] = text
            with self.subTest(text=text), self.assertRaises(ValueError):
                prepare_inputs(frozen)
        frozen = fixture()
        del frozen['cases'][0]['wordings'][1]['alternative']
        with self.assertRaises(ValueError):
            prepare_inputs(frozen)

    def test_requires_two_wordings_and_unique_nonempty_cases(self):
        for count in (0, 1, 3):
            frozen = fixture()
            frozen['cases'][0]['wordings'] = [frozen['cases'][0]['wordings'][0]] * count
            with self.subTest(count=count), self.assertRaises(ValueError):
                prepare_inputs(frozen)
        frozen = fixture()
        frozen['cases'].append(copy.deepcopy(frozen['cases'][0]))
        with self.assertRaises(ValueError):
            prepare_inputs(frozen)
        for field in ('id', 'domain', 'rationale'):
            frozen = fixture()
            frozen['cases'][0][field] = ''
            with self.subTest(field=field), self.assertRaises(ValueError):
                prepare_inputs(frozen)
        frozen = fixture()
        frozen['cases'] = []
        with self.assertRaises(ValueError):
            prepare_inputs(frozen)

    def test_analysis_keeps_all_pairs_and_both_comparisons(self):
        rows = prepare_inputs(fixture())
        root = [1., 0.]
        vectors = [[0., 1.], [-1., 0.], [0., -1.]] * 2
        result = analyze_scores(rows, root, vectors)
        self.assertEqual(len(result['pairs']), 36)
        self.assertEqual(len(result['direction']), 2)
        self.assertEqual(len(result['candidate_comparisons']), 2)
        first = result['direction'][0]
        self.assertEqual((first['case'], first['domain'], first['wording']),
                         ('case-1', 'biology', 1))
        self.assertAlmostEqual(first['forward_degrees'], 90.)
        self.assertAlmostEqual(first['reverse_degrees'], 135.)
        self.assertAlmostEqual(first['reverse_minus_forward'], 45.)
        self.assertAlmostEqual(first['forward_cosine'], 0.)
        self.assertAlmostEqual(first['reverse_cosine'], 0.)
        comparison = result['candidate_comparisons'][0]
        self.assertEqual(comparison['broader'], 'case-1-w1-broader')
        self.assertEqual(comparison['narrower'], 'case-1-w1-narrower')
        self.assertEqual(comparison['alternative'], 'case-1-w1-alternative')
        self.assertAlmostEqual(comparison['broader_degrees'], 90.)
        self.assertAlmostEqual(comparison['alternative_degrees'], 90.)
        self.assertAlmostEqual(comparison['alternative_minus_broader_degrees'], 0.)
        self.assertAlmostEqual(comparison['broader_cosine'], 0.)
        self.assertAlmostEqual(comparison['alternative_cosine'], 0.)
        self.assertAlmostEqual(comparison['broader_minus_alternative_cosine'], 0.)

    def test_comparison_differences_follow_angle_and_cosine_conventions(self):
        rows = prepare_inputs(fixture())
        result = analyze_scores(rows, [1., 0.],
                                [[-1., 0.], [0., 1.], [math.sqrt(.5), math.sqrt(.5)]] * 2)
        comparison = result['candidate_comparisons'][0]
        self.assertAlmostEqual(comparison['broader_degrees'], 135.)
        self.assertAlmostEqual(comparison['alternative_degrees'], 45.)
        self.assertAlmostEqual(comparison['alternative_minus_broader_degrees'], -90.)
        self.assertAlmostEqual(comparison['alternative_cosine'], math.sqrt(.5))
        self.assertAlmostEqual(comparison['broader_minus_alternative_cosine'], -math.sqrt(.5))

    def test_undefined_angles_remain_null(self):
        rows = prepare_inputs(fixture())
        result = analyze_scores(rows, [1., 0.], [[0., 1.]] * 6)
        self.assertTrue(all(pair['angle_degrees'] is None for pair in result['pairs']))
        self.assertIsNone(result['direction'][0]['reverse_minus_forward'])
        self.assertIsNone(result['candidate_comparisons'][0]['alternative_minus_broader_degrees'])
        self.assertEqual(result['candidate_comparisons'][0]['broader_minus_alternative_cosine'], 0.)

    def test_analysis_rejects_missing_or_invalid_embeddings(self):
        rows = prepare_inputs(fixture())
        for vectors in ([[0., 1.]] * 5, [[0., 2.]] * 6):
            with self.assertRaises(ValueError):
                analyze_scores(rows, [1., 0.], vectors)


if __name__ == '__main__':
    unittest.main()
