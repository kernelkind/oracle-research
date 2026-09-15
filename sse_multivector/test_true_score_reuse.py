import unittest

from true_category_probe import model_input
from true_score_reuse import plan_reuse, assemble_scores, validate_cache_identity


def pair(a_id, a, b_id, b):
    row = dict(id=f'{a_id}-contains-{b_id}', a_id=a_id, b_id=b_id,
               a=a, b=b, domain='generated-titles', format='topic')
    return dict(row, model_input=model_input(row, 'topic'))


def result(row, value=0.6):
    return dict(row, entailment_score=value, threshold_predicted=value > 0.142,
                predicted=True, generated_text='1', generated_token_ids=[0, 209, 1],
                eos_terminated=True, token_ids=[11, 22, 1])


class ScoreReuseTests(unittest.TestCase):
    def test_cache_identity_ignores_only_run_name_and_load_time(self):
        ref = dict(config=dict(dtype='float32', threshold=0.142, experiment='new', load_seconds=1),
                   model_files_sha256='weights', source_sha256={'scorer.py': 'code'})
        same = dict(ref, config=dict(ref['config'], experiment='old', load_seconds=99))
        validate_cache_identity(same, ref)
        for changed in [dict(config=dict(ref['config'], dtype='float16')),
                        dict(model_files_sha256='other'),
                        dict(source_sha256={'scorer.py': 'other'})]:
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                validate_cache_identity(dict(ref, **changed), ref)

    def test_exact_strings_reuse_across_ids_without_merging_nodes(self):
        old = result(pair('old-a', 'Food', 'old-b', 'Steak'))
        rows = [pair('a', 'Food', 'b', 'Steak'), pair('c', 'Food', 'b', 'Steak')]
        plan = plan_reuse(rows, [('old/scores.jsonl', [old])])
        self.assertEqual(plan['missing_inputs'], [])
        assembled = assemble_scores(rows, plan, [], 'fresh/scores.jsonl')
        self.assertEqual([r['a_id'] for r in assembled], ['a', 'c'])
        self.assertEqual([r['entailment_score'] for r in assembled], [0.6, 0.6])
        self.assertEqual(assembled[0]['score_origin']['row_index'], 0)

    def test_same_ids_changed_title_are_not_reused(self):
        old = result(pair('a', 'Food Ingredients', 'b', 'Steak'))
        rows = [pair('a', 'Foods featuring meat or seafood', 'b', 'Steak')]
        plan = plan_reuse(rows, [('old/scores.jsonl', [old])])
        self.assertEqual(plan['missing_inputs'], rows)
        with self.assertRaisesRegex(ValueError, 'missing'):
            assemble_scores(rows, plan, [], 'fresh/scores.jsonl')

    def test_conflicting_saved_decisions_require_fresh_inference(self):
        row = pair('a', 'Food', 'b', 'Steak')
        first, second = result(row, 0.141), result(row, 0.143)
        plan = plan_reuse([row], [('first', [first]), ('second', [second])])
        self.assertEqual(plan['missing_inputs'], [row])
        self.assertEqual(len(plan['conflicts']), 1)

    def test_unscored_duplicate_inputs_are_encoded_once(self):
        rows = [pair('a', 'Food', 'b', 'Steak'), pair('c', 'Food', 'b', 'Steak')]
        plan = plan_reuse(rows, [])
        self.assertEqual(plan['missing_inputs'], rows[:1])
        assembled = assemble_scores(rows, plan, [result(rows[0])], 'fresh')
        self.assertEqual(len(assembled), 2)

    def test_bad_cached_cutoff_or_framing_is_rejected(self):
        row = pair('a', 'Food', 'b', 'Steak')
        for changed in [dict(threshold_predicted=False), dict(model_input='wrong')]:
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                plan_reuse([row], [('old', [dict(result(row), **changed)])])

    def test_unexpected_or_duplicate_fresh_results_are_rejected(self):
        row = pair('a', 'Food', 'b', 'Steak')
        plan = plan_reuse([row], [])
        for fresh in [[result(row), result(row)], [result(pair('x', 'Coffee', 'y', 'Food'))]]:
            with self.subTest(fresh=fresh), self.assertRaises(ValueError):
                assemble_scores([row], plan, fresh, 'fresh')

    def test_expected_labels_do_not_leak_into_assembled_scores(self):
        row = pair('a', 'Food', 'b', 'Steak')
        plan = plan_reuse([row], [('old', [dict(result(row), expected=True)])])
        assembled = assemble_scores([row], plan, [], 'fresh')
        self.assertNotIn('expected', assembled[0])


if __name__ == '__main__':
    unittest.main()
