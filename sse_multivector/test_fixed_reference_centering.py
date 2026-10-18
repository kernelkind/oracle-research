import unittest

import numpy as np

from sse_multivector.fixed_reference_centering import centered_cosines


class FixedReferenceCenteringTests(unittest.TestCase):
    def test_matches_direct_cosines_after_removing_accepted_reference_mean(self):
        bank = np.array([[1., 0, 0], [0, 1., 0], [0, 0, 1.]])
        queries = np.array([[1., 1, 0], [0, 1., 1]])
        references = bank[[0, 2]]
        mean = bank.mean(axis=0)
        q = queries / np.linalg.norm(queries, axis=1, keepdims=True) - mean
        r = references - mean
        expected = (q / np.linalg.norm(q, axis=1, keepdims=True)) @ (
            r / np.linalg.norm(r, axis=1, keepdims=True)).T
        actual = centered_cosines(queries, ['x', 'y'], references, bank, list('abc'))
        np.testing.assert_allclose(actual, expected, atol=1e-15)

    def test_excludes_all_entries_from_query_source_note_when_finding_mean(self):
        bank = np.array([[1., 0, 0], [.8, .6, 0], [0, 1., 0], [0, 0, 1.]])
        notes = list('aabc')
        query = np.array([[1., 1., 1.]])
        expected = centered_cosines(query, ['q'], bank, bank[2:], list('bc'))
        actual = centered_cosines(query, ['a'], bank, bank, notes)
        np.testing.assert_allclose(actual, expected, atol=1e-15)
        # Excluding just the matching vector would give a different result.
        wrong = centered_cosines(query, ['q'], bank, bank[1:], list('abc'))
        self.assertGreater(np.max(abs(wrong - actual)), .01)

    def test_queries_do_not_change_bank_or_influence_each_other(self):
        bank = np.array([[1., 0, 0], [0, 1., 0], [0, 0, 1.]])
        queries = np.array([[1., 1., 0], [0, 1., 1], [1., 0, 1]])
        original = bank.copy()
        expected = centered_cosines(queries, list('axc'), bank, bank, list('abc'))
        order = [2, 0, 0, 1]
        np.testing.assert_allclose(centered_cosines(
            queries[order], ['c', 'a', 'a', 'x'], bank, bank, list('abc')),
            expected[order], atol=1e-15)
        np.testing.assert_allclose(centered_cosines(
            queries * np.array([[2], [3], [4]]), list('axc'), bank * 7,
            bank[[2, 0, 1]] * np.array([[3], [4], [5]]), list('cab')),
            expected, atol=1e-15)
        for j, note in enumerate('axc'):
            np.testing.assert_allclose(centered_cosines(
                queries[j:j+1], [note], bank, bank, list('abc')),
                expected[j:j+1], atol=1e-15)
        np.testing.assert_array_equal(bank, original)

    def test_unavailable_or_degenerate_centering_is_rejected(self):
        for query, notes, refs, bank, bank_notes in [
                ([[1., 0]], ['a'], [[1., 0]], [[1., 0]], ['a']),
                ([[1., 0]], ['q'], [[0, 1.]], [[1., 0]], ['a']),
                ([[0, 1.]], ['q'], [[1., 0]], [[1., 0]], ['a']),
                ([[0, 0]], ['q'], [[0, 1.]], [[1., 0]], ['a']),
                ([[float('nan'), 0]], ['q'], [[0, 1.]], [[1., 0]], ['a']),
                ([[1., 0]], [], [[0, 1.]], [[1., 0]], ['a']),
                ([[1., 0]], ['q'], [[0, 1.]], [[1., 0]], []),
                ([[1., 0]], ['q'], [[0, 1., 0]], [[1., 0]], ['a']),
                ([[1., 0]], ['q'], [[0, 1.]], [], [])]:
            with self.subTest(query=query, notes=notes, bank_notes=bank_notes):
                with self.assertRaises(ValueError):
                    centered_cosines(query, notes, refs, bank, bank_notes)


if __name__ == '__main__':
    unittest.main()
