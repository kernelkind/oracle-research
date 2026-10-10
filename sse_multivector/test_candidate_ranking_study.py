"""Ranking research uses fixed meanings and never treats heading ties as merges."""
import unittest
from pathlib import Path
import tempfile

import numpy as np

from sse_multivector import candidate_ranking_study as study


class CandidateRankingStudy(unittest.TestCase):
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


if __name__ == '__main__':
    unittest.main()
