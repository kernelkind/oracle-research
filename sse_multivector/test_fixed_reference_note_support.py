import unittest

import numpy as np

from sse_multivector.fixed_reference_note_support import note_support


class FixedReferenceNoteSupportTests(unittest.TestCase):
    def test_each_reference_note_contributes_its_best_match_once(self):
        values = np.array([[.9, .2, .7, .1]])
        self.assertAlmostEqual(note_support(values, ['q'], list('aabc'), range(4))[0],
                               (.9 + .7 + .1) / 3)
        self.assertAlmostEqual(note_support(values, ['q'], list('aabc'), range(4),
                                            neighbors=2)[0], .8)

    def test_excludes_whole_source_note_and_reports_insufficient_support(self):
        values = np.array([[1, .9, .4, .2], [.8, 1, .3, .1],
                           [.7, .6, 1, .5], [.4, .2, .8, 1]])
        np.testing.assert_allclose(note_support(values, list('aabc'), list('aabc'),
                                                range(4), neighbors=2),
                                   [.3, .2, .6, .6])
        result = note_support(values, list('aabc'), list('aabc'), range(4),
                              neighbors=2, excluded_notes={'a'})
        np.testing.assert_allclose(result[:2], [.3, .2])
        self.assertTrue(np.isnan(result[2:]).all())
        self.assertTrue(np.isnan(note_support(values, list('aabc'), list('aabc'),
                                              [], neighbors=1)).all())

    def test_duplicates_nonmembers_and_other_queries_cannot_change_support(self):
        values = np.array([[.9, .2, .7, .1], [.1, .8, .3, .4]])
        original = values.copy()
        expected = note_support(values, ['x', 'y'], list('aabc'), [0, 1, 2],
                                neighbors=2)
        repeated = np.column_stack([values, values[:, 0], values[:, 0] / 2])
        actual = note_support(repeated, ['x', 'y'], list('aabcaa'), [0, 1, 2, 4, 5],
                              neighbors=2)
        np.testing.assert_array_equal(actual, expected)
        values[:, 3] = 1
        np.testing.assert_array_equal(note_support(values, ['x', 'y'], list('aabc'),
                                                   [0, 1, 2], neighbors=2), expected)
        np.testing.assert_array_equal(note_support(original[[1, 0, 0]], ['y', 'x', 'x'],
                                                   list('aabc'), [2, 1, 0], neighbors=2),
                                      expected[[1, 0, 0]])
        for j, note in enumerate(['x', 'y']):
            self.assertEqual(note_support(original[j:j+1], [note], list('aabc'),
                                          [0, 1, 2], neighbors=2)[0], expected[j])

    def test_invalid_inputs_are_rejected(self):
        for values, queries, notes, group, options in [
                ([[.5]], ['x', 'y'], ['a'], [0], {}),
                ([[float('nan')]], ['x'], ['a'], [0], {}),
                ([[1.1]], ['x'], ['a'], [0], {}),
                ([[.5]], ['x'], ['a'], [0, 0], {}),
                ([[.5]], ['x'], ['a'], [-1], {}),
                ([[.5]], ['x'], ['a'], [1], {}),
                ([[.5]], ['x'], ['a'], [0], {'neighbors': 0}),
                ([[.5]], ['x'], ['a'], [0], {'neighbors': True}),
                ([[.5]], ['x'], ['a'], [0], {'neighbors': 1.5})]:
            with self.subTest(values=values, options=options):
                with self.assertRaises(ValueError):
                    note_support(values, queries, notes, group, **options)


if __name__ == '__main__':
    unittest.main()
