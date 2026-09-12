"""Tests exercise TRUE01's actual input construction and decision calculation."""
import copy
import json
import math
from pathlib import Path
import unittest

from true_category_probe import make_pairs, model_input, score_logits, summarize, render_decisions, score_generation


class TRUECategoryProbeTests(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads((Path(__file__).parent /
            'navigation-research-v1/hrc03-fixture.json').read_text())

    def test_frozen_subset_is_balanced_by_domain_and_preserves_exact_strings(self):
        pairs = make_pairs(self.fixture)
        self.assertEqual(len(pairs), 90)
        self.assertEqual(len({p['id'] for p in pairs}), 90)
        self.assertEqual(sum(p['expected'] for p in pairs), 30)
        domains = {p['domain'] for p in pairs}
        self.assertEqual(len(domains), 5)
        self.assertTrue(all(sum(p['domain'] == d for p in pairs) == 18 for d in domains))
        original = {text for c in self.fixture['cases'] for w in c['wordings']
                    for text in w.values()}
        self.assertTrue(all(p['a'] in original and p['b'] in original for p in pairs))

    def test_subsumption_direction_and_native_input_format(self):
        pair = next(p for p in make_pairs(self.fixture) if p['id'] == 'S03-w1-forward')
        self.assertEqual(pair['a'], 'Open-source software')
        self.assertEqual(pair['b'], 'Programs released under the GNU General Public License')
        self.assertTrue(pair['expected'])
        self.assertEqual(model_input(pair, 'bare'),
            'premise: Programs released under the GNU General Public License hypothesis: Open-source software')
        self.assertEqual(model_input(pair, 'topic'),
            'premise: This text is about Programs released under the GNU General Public License. '
            'hypothesis: This text is about Open-source software.')

    def test_reversals_are_independent_decisions_and_equivalence_is_bidirectional(self):
        pairs = {p['id']: p for p in make_pairs(self.fixture)}
        self.assertFalse(pairs['S03-w1-reverse']['expected'])
        self.assertEqual(pairs['S03-w1-reverse']['b'], pairs['S03-w1-forward']['a'])
        eq = [p for p in pairs.values() if p['kind'] == 'equivalent']
        self.assertEqual(len(eq), 10)
        self.assertTrue(all(p['expected'] for p in eq))
        self.assertTrue(all(any(q['a'] == p['b'] and q['b'] == p['a'] for q in eq) for p in eq))

    def test_missing_cases_and_duplicate_ids_are_rejected(self):
        changed = copy.deepcopy(self.fixture)
        changed['cases'] = [c for c in changed['cases'] if c['id'] != 'S03']
        with self.assertRaises(ValueError):
            make_pairs(changed)
        changed['cases'].append(changed['cases'][0])
        with self.assertRaises(ValueError):
            make_pairs(changed)

    def test_score_uses_released_label_ids_and_preserves_out_of_label_predictions(self):
        result = score_logits([1000., 1001., 1002.], zero_id=0, one_id=1)
        self.assertAlmostEqual(result['entailment_score'], 1 / (1 + math.exp(-1)))
        self.assertEqual(result['binary_label'], 1)
        self.assertEqual(result['argmax_token_id'], 2)
        self.assertIsNone(result['predicted'])
        self.assertLess(result['label_probability_mass'], 1)
        ordinary = score_logits([4., -5., 2.], zero_id=1, one_id=0)
        self.assertTrue(ordinary['predicted'])

    def test_nonfinite_and_invalid_label_ids_rejected(self):
        for values, zero, one in (([math.nan, 1.], 0, 1), ([1., 2.], 0, 0),
                                   ([1., 2.], 0, 2)):
            with self.assertRaises(ValueError):
                score_logits(values, zero, one)

    def test_duplicate_case_rejected_even_when_all_selected_cases_present(self):
        changed = copy.deepcopy(self.fixture)
        changed['cases'].append(changed['cases'][0])
        with self.assertRaisesRegex(ValueError, 'duplicate case ID'):
            make_pairs(changed)

    def test_summary_counts_abstentions_as_unresolved_not_correct_negatives(self):
        rows = [dict(format='topic', domain='software', kind='forward', expected=True, predicted=True),
                dict(format='topic', domain='software', kind='reverse', expected=False, predicted=None)]
        result = summarize(rows)['topic']['overall']
        self.assertEqual(result['correct'], 1)
        self.assertEqual(result['unresolved'], 1)
        self.assertEqual(result['false_positive'], 0)

    def test_report_shows_both_complete_categories_and_separates_input_formats(self):
        rows = [dict(id='X', a='Broad category', b='Specific category', expected=True,
                     format=form, predicted=prediction, entailment_score=score)
                for form, prediction, score in (('topic', True, .9), ('bare', False, .1))]
        report = render_decisions(rows)
        self.assertIn('A contains B', report)
        self.assertIn('Broad category', report)
        self.assertIn('Specific category', report)
        self.assertIn('Yes (0.900000)', report)
        self.assertIn('No (0.100000)', report)

    def test_complete_multitoken_zero_is_decoded_not_assumed_from_its_first_token(self):
        values = [0., 0., 0., 5., 1.]
        labels = {'0': [3, 2], '1': [4]}
        result = score_generation(values, '0', [0, 3, 2, 1], labels)
        self.assertFalse(result['predicted'])
        self.assertEqual(result['generated_token_ids'], [0, 3, 2, 1])
        self.assertAlmostEqual(result['entailment_score'], math.exp(1) / (3 + math.exp(5) + math.exp(1)))
        other = score_generation(values, 'some other output', [0, 3, 2, 1], labels)
        self.assertIsNone(other['predicted'])

    def test_generation_must_agree_with_raw_first_token_argmax(self):
        with self.assertRaisesRegex(ValueError, 'argmax'):
            score_generation([5., 1., 0.], '1', [0, 1, 2], {'0': [0, 2], '1': [1]})

    def test_unterminated_label_is_unresolved(self):
        result = score_generation([0., 0., 5.], '1', [0, 2], {'0': [0, 2], '1': [2]})
        self.assertIsNone(result['predicted'])


if __name__ == '__main__':
    unittest.main()
