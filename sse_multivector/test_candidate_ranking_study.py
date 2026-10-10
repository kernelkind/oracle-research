"""Ranking research uses fixed meanings and never treats heading ties as merges."""
import unittest
from pathlib import Path
import tempfile
import json

import numpy as np

from sse_multivector import candidate_ranking_study as study


class CandidateRankingStudy(unittest.TestCase):
    def test_root_order_stays_fixed_while_children_combine_two_orders(self):
        ids = [f'C{i:03}' for i in range(16)]
        scores = {key: np.arange(16, 0, -1, dtype=float) for key in (
            'heading', 'meaning', 'contextual_heading', 'contextual_meaning', 'meaning_descendants',
            'heading_descendants', 'contextual_descendants', 'definition_text', 'late_interaction',
            'density_contextual')}
        meaning_order = [13, 14, 0, 1, 2, 3, 4, 5, 15, 12, 6, 7, 8, 9, 10, 11]
        for rank, index in enumerate(meaning_order):
            scores['meaning'][index] = 16-rank
        frame = dict(ids=ids, scores=scores, pool=ids, step={'local': {'number': '2'}})
        self.assertEqual(study.orders(frame)['root_baseline_meaning_union'], ids)
        frame['step']['local']['number'] = '2.1'
        self.assertEqual(study.orders(frame)['root_baseline_meaning_union'], ids[:12]+[ids[13], ids[14]])

    def test_requested_profiles_do_not_run_unrelated_screens(self):
        self.assertEqual(study.screen_profiles(['baseline', 'meaning', 'learned'],
            ['meaning-12', 'baseline-16']), {'meaning-12': ('meaning', 12), 'baseline-16': ('baseline', 16)})
        self.assertEqual(len(study.screen_profiles(['baseline', 'meaning'])), 6)
        with self.assertRaisesRegex(ValueError, 'profile'):
            study.screen_profiles(['baseline'], ['meaning-12'])
        with self.assertRaisesRegex(ValueError, 'profile'):
            study.screen_profiles(['baseline'], ['baseline-12', 'baseline-12'])

    def test_heading_groups_keep_distinct_meanings_without_merging(self):
        rows = [dict(id='C1', subject='Meals'), dict(id='C2', subject='Morning'),
                dict(id='C3', subject='Meals'), dict(id='C4', subject='Bread')]
        selected = study.select_candidates(rows, ['C1', 'C2', 'C4', 'C3'],
                                           limit=2, heading_groups=True)
        self.assertEqual(selected, ['C1', 'C3', 'C2'])

    def test_mapped_parent_has_priority(self):
        rows = [dict(id='C1', subject='Food'), dict(id='C2', subject='Cooking')]
        self.assertEqual(study.select_candidates(rows, ['C1', 'C2'], limit=1,
                                                mapped_parent='C2'), ['C2'])

    def test_descendants_nominate_broader_candidates(self):
        scores = np.array([.1, .9, .5])
        inherited = study.descendant_scores(scores, [[0, 1], [1], [2]])
        np.testing.assert_allclose(inherited, [.9, .9, .5])
        self.assertEqual(study.score_order(['parent', 'child', 'other'], inherited),
                         ['child', 'parent', 'other'])

    def test_logistic_fit_does_not_change_inputs_and_separates_signal(self):
        x = np.array([[-2.], [-1.], [1.], [2.]])
        original = x.copy()
        model = study.fit_logistic(x, np.array([0., 0., 1., 1.]), penalty=.1)
        predictions = study.predict_logistic(model, x)
        np.testing.assert_array_equal(x, original)
        self.assertTrue(np.all(predictions[:2] < .5))
        self.assertTrue(np.all(predictions[2:] > .5))

    def test_note_split_is_stable_and_disjoint(self):
        notes = [str(i) for i in range(50)]
        split = study.note_split(notes)
        self.assertEqual(split, study.note_split(notes[::-1]))
        self.assertEqual(set(split['development']) & set(split['test']), set())
        self.assertEqual(len(split['test']), 10)

    def test_zero_vectors_fail_instead_of_becoming_matches(self):
        with self.assertRaisesRegex(ValueError, 'nonzero'):
            study.unit_rows(np.array([[0., 0.]]))

    def test_replay_history_retains_only_answers_actually_requested(self):
        step = dict(index=1, before=[], after=[], answers=[
            dict(id='C1', status='valid', receipt={'record_sha256': 'one'},
                 output={'relation': 'neither'}),
            dict(id='C2', status='valid', receipt={'record_sha256': 'two'},
                 output={'relation': 'canonical_contains_local'})])
        original = repr(step)
        replayed = study.history_step(step, {'C2'})
        self.assertEqual([a['id'] for a in replayed['answers']], ['C2'])
        self.assertEqual(replayed['answers'][0]['receipt']['record_sha256'], 'two')
        self.assertEqual(repr(step), original)

    def test_paper_inspired_coverage_score_uses_different_views(self):
        scores = study.late_interaction(np.array([[1., 0.], [0., 1.]]),
            np.array([[[1., 0.], [0., 1.]], [[1., 0.], [1., 0.]]]))
        np.testing.assert_allclose(scores, [1., .5])

    def test_density_correction_penalizes_a_crowded_candidate(self):
        vectors = np.array([[1., 0.], [1., 0.], [0., 1.]])
        scores = study.density_corrected(np.array([.8, .8, .8]), vectors, neighbors=1)
        np.testing.assert_allclose(scores, [.6, .6, 1.6])

    def test_vector_receipt_must_match_this_exact_preparation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'inputs.json').write_text('{}')
            (root / 'worker-request.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'binding'):
                study.verify_vector_binding(root, dict(proposal_sha256='wrong', request_sha256='wrong'))

    def test_online_training_excludes_unrequested_and_uncertain_answers(self):
        frame = dict(ids=['positive', 'future', 'uncertain'], features=np.array([[1., 2.], [3., 4.], [5., 6.]]),
            known={'positive': {'parsed': {'relation': 'canonical_contains_local'}},
                   'future': {'parsed': {'relation': 'neither'}},
                   'uncertain': {'parsed': {'relation': 'uncertain'}}})
        x, y = study.observed_training(frame, {'positive', 'uncertain'}, [1])
        self.assertEqual([v.tolist() for v in x], [[2.]])
        self.assertEqual(y, [True])


class CandidateRankingCosts(unittest.TestCase):
    def test_native_warmup_remains_outside_comparison_cost(self):
        from sse_multivector import test_experiment as fixtures
        from sse_multivector import experiment as workflow
        fixture = fixtures.ExperimentTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.runner.write_bytes((Path(workflow.__file__).parents[1] / 'tests/fixtures/fake-runner.py').read_bytes())
        fixture.prompt.write_text('GENERIC PROMPT' + ' word'*1100 + '\n{POST}')
        fixture.prepare('cached', '--model', 'gpt-6.1-sol', '--prompt-cache')
        fixture.cli('run', 'cached', env={'FAKE_RUNNER_RESULT_OVERRIDE': json.dumps({
            'usage': {'input': 11, 'cacheRead': 7, 'output': 5, 'cost': {'total': .1}}})})
        directory = fixture.root / 'cached'
        report = workflow.report(directory, only=['one'], generation_costs=True,
                                 include_request_preview=False)
        self.assertEqual(report['generation_usage']['original_calls'], 2)
        frame = dict(step={'index': 0}, known={c['id']: dict(c, experiment=str(directory))
                                              for c in report['cases']})
        usage = study.comparison_costs([frame], {0: {'one'}}, workflow)
        self.assertEqual(usage['actual_source_attempts'], 1)
        self.assertAlmostEqual(usage['known_catalog_cost_estimate_usd'], .1)
        self.assertEqual(len(fixture.calls()), 3)

    def test_native_reuse_prices_its_original_once_without_new_calls(self):
        from sse_multivector import test_experiment as fixtures
        from sse_multivector import experiment as workflow
        fixture = fixtures.ExperimentTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.prepare('E1')
        fixture.cli('run', 'E1', env={'FAKE_RUNNER_RESULT_OVERRIDE': json.dumps({
            'usage': {'input': 11, 'cacheRead': 7, 'output': 5, 'cost': {'total': .1}}})})
        fixture.cli('prepare', 'E2', '--from', 'E1')
        fixture.cli('run', 'E2')
        frames, selected = [], {}
        for index, name in enumerate(('E1', 'E2')):
            directory = fixture.root / name
            cases = workflow.report(directory, only=['one'], include_request_preview=False)['cases']
            frames.append(dict(step={'index': index},
                known={c['id']: dict(c, experiment=str(directory)) for c in cases}))
            selected[index] = {'one'}
        ledgers = [fixture.root / name / 'run/results.jsonl' for name in ('E1', 'E2')]
        before = [p.read_bytes() for p in ledgers]
        usage = study.comparison_costs(frames, selected, workflow)
        self.assertEqual(usage['actual_source_attempts'], 1)
        self.assertEqual(usage['input_tokens'], 11)
        self.assertEqual(usage['cached_input_tokens'], 7)
        self.assertEqual(usage['output_tokens'], 5)
        self.assertEqual(usage['attempts_without_cost_estimate'], 0)
        self.assertAlmostEqual(usage['known_catalog_cost_estimate_usd'], .1)
        self.assertEqual([p.read_bytes() for p in ledgers], before)
        self.assertEqual(len(fixture.calls()), 2)
        frames[0]['known']['one']['receipt']['record_sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'no longer valid'):
            study.comparison_costs(frames, selected, workflow)
        self.assertEqual(len(fixture.calls()), 2)


if __name__ == '__main__':
    unittest.main()
