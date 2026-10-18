import unittest

from sse_multivector.reference_view_agreement import summarize


class ReferenceViewAgreementTests(unittest.TestCase):
    def test_title_agreement_can_hide_meaning_disagreement_across_notes(self):
        result = summarize([[2, 0], [3, 0], [4, 0]],
                           [[1, 0], [0, 2], [3, 0]], ['a', 'b', 'a'])
        self.assertEqual(result['entries'], 3)
        self.assertEqual(result['notes'], 2)
        self.assertEqual(result['cross_note_pairs'], 2)
        self.assertEqual(result['title_median_cosine'], 1.)
        self.assertEqual(result['meaning_median_cosine'], 0.)
        self.assertEqual(result['median_cosine_gap'], 1.)

    def test_coherent_views_have_no_gap_and_permutation_preserves_summary(self):
        result = summarize([[1, 0], [1, 0], [0, 1]],
                           [[0, 2], [0, 4], [5, 0]], ['a', 'b', 'c'])
        self.assertEqual(result['median_cosine_gap'], 0.)
        self.assertEqual(result, summarize([[0, 7], [3, 0], [4, 0]],
                                           [[2, 0], [0, 8], [0, 9]], ['c', 'a', 'b']))

    def test_one_source_note_cannot_establish_cross_note_agreement(self):
        result = summarize([[1, 0], [1, 0]], [[1, 0], [0, 1]], ['a', 'a'])
        self.assertEqual(result['cross_note_pairs'], 0)
        for field in ['title_median_cosine', 'meaning_median_cosine', 'median_cosine_gap']:
            self.assertIsNone(result[field])

    def test_misaligned_or_invalid_vectors_are_rejected(self):
        for title, meaning, notes in [([[1]], [[1], [1]], ['a']),
                                       ([[0, 0]], [[1, 0]], ['a']),
                                       ([[1, 0]], [[float('nan'), 0]], ['a']),
                                       ([[1]], [[1]], []),
                                       ([[1]], [[1]], [None])]:
            with self.subTest(title=title, meaning=meaning, notes=notes):
                with self.assertRaises(ValueError):
                    summarize(title, meaning, notes)


if __name__ == '__main__':
    unittest.main()
