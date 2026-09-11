import copy
import unittest

from nli_subject_rendering import prepare_controls, summarize_controls


class SubjectRenderingTests(unittest.TestCase):
    def setUp(self):
        self.pairs = [dict(measurement='coverage', kind='subject', candidate='C1',
                           vector='V1', premise='This text is about They drink coffee..',
                           hypothesis='This text is about Coffee..', score=.2,
                           logits=[1, 0], token_count=12),
                      dict(measurement='relation', kind='phrase', score=.9)]

    def test_source_is_unchanged_and_only_subjects_are_scored(self):
        before = copy.deepcopy(self.pairs)
        rows = prepare_controls(self.pairs)
        self.assertEqual(self.pairs, before)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['premise'], 'This text is about They drink coffee.')
        self.assertEqual(rows[1]['premise'], 'They drink coffee.')
        self.assertTrue(all(p['hypothesis'] == 'This text is about Coffee.' for p in rows))
        self.assertTrue(all(p['baseline_score'] == .2 and p['source_pair'] == 0 for p in rows))
        self.assertTrue(all('logits' not in p and 'score' not in p for p in rows))

    def test_renderer_preserves_original_punctuation(self):
        self.pairs[0]['premise'] = 'This text is about Why coffee?.'
        rows = prepare_controls(self.pairs)
        self.assertEqual(rows[0]['premise'], 'This text is about Why coffee?')
        self.assertEqual(rows[1]['premise'], 'Why coffee?')

    def test_unknown_or_empty_source_fails_instead_of_guessing(self):
        with self.assertRaises(ValueError):
            prepare_controls([])
        self.pairs[0]['premise'] = 'Some other input'
        with self.assertRaises(ValueError):
            prepare_controls(self.pairs)

    def test_decision_changes_are_not_named_correctness(self):
        rows = prepare_controls(self.pairs)
        for row in rows:
            row['score'] = .8
        summary = summarize_controls(rows)
        self.assertEqual(len(summary), 2)
        self.assertTrue(all(s['became_positive'] == 1 for s in summary))
        self.assertTrue(all(s['became_negative'] == 0 for s in summary))


if __name__ == '__main__':
    unittest.main()
