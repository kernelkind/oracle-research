import copy
import unittest

import numpy as np

from phrase_description_probe import pair_scores, prepare_inputs, nearest_notes


class PhraseDescriptionProbeTests(unittest.TestCase):
    def test_inputs_preserve_source_and_cache_only_identical_subjects(self):
        rows = [dict(row=i, note=n, subject=s, text='Full note.',
                     fragments=['Full'], alias_ids=[f'V{i}'])
                for i, (n, s) in enumerate([
                    ('N1', 'Bread.'), ('N2', 'Bread.'), ('N3', 'bread.')])]
        source = dict(inputs=rows)
        original = copy.deepcopy(source)
        inputs, unique, indices = prepare_inputs(source)
        self.assertEqual(inputs, rows)
        self.assertEqual(unique[:2], ['Bread.', 'bread.'])
        self.assertEqual(indices, [0, 0, 1])
        inputs[0]['fragments'].append('note')
        self.assertEqual(source, original)
        with self.assertRaises(ValueError):
            prepare_inputs(dict(inputs=[dict(rows[0], subject=' ')]))
        with self.assertRaises(ValueError):
            prepare_inputs(dict(inputs=[dict(rows[0], row=1)]))

    def test_unnormalized_distance_and_cosine_are_distinct(self):
        v = np.array([[1., 0.], [2., 0.], [1., 1.]])
        scores = pair_scores(v)
        np.testing.assert_allclose(scores['euclidean'],
                                   [[0, 1, 1], [1, 0, 2**.5], [1, 2**.5, 0]])
        self.assertEqual(scores['cosine'][0, 1], 1.)
        self.assertAlmostEqual(scores['cosine'][0, 2], 2**-.5)
        for bad in [np.array([[0., 0.]]), np.array([[np.nan, 0.]]), np.array([1., 2.])]:
            with self.assertRaises(ValueError):
                pair_scores(bad)

    def test_nearest_notes_excludes_own_note_and_keeps_best_witness(self):
        rows = [dict(row=i, note=n) for i, n in enumerate(['A', 'A', 'B', 'B', 'C'])]
        vector_scores = np.array([1., .99, .8, .9, .9])
        self.assertEqual(nearest_notes(rows, 0, vector_scores, 'cosine', 10),
                         [dict(row=3, note='B', score=.9), dict(row=4, note='C', score=.9)])
        self.assertEqual(nearest_notes(rows, 0, vector_scores, 'euclidean', 1),
                         [dict(row=2, note='B', score=.8)])
        with self.assertRaises(ValueError):
            nearest_notes(rows, 0, [1.], 'cosine', 1)
        with self.assertRaises(ValueError):
            nearest_notes(rows, 0, vector_scores, 'unknown', 1)


if __name__ == '__main__':
    unittest.main()
