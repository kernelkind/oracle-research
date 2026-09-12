import copy
import unittest

from subject_pattern_candidates import compare_patterns


def records(*subjects):
    return [dict(row=i, note=note, subject=subject) for i, (note, subject) in enumerate(subjects)]


def lookup(result, family, pair):
    return next((p for p in result[family] if p['tokens'] == list(pair)), None)


class SubjectPatternCandidateTests(unittest.TestCase):
    def test_order_and_adjacency_have_separate_effects(self):
        inputs = records(('a', 'red birds'), ('b', 'birds are red'),
                         ('c', 'red singing birds'), ('d', 'red birds'))
        before = copy.deepcopy(inputs)
        result = compare_patterns(inputs)
        self.assertEqual(inputs, before)
        self.assertEqual(lookup(result, 'unordered', ('birds', 'red'))['rows'], [0, 1, 2, 3])
        self.assertEqual(lookup(result, 'ordered', ('red', 'birds'))['rows'], [0, 2, 3])
        self.assertEqual(lookup(result, 'adjacent', ('red', 'birds'))['rows'], [0, 3])
        self.assertEqual(lookup(result, 'adjacent', ('red', 'birds'))['positions'],
                         [[0, [[0, 1]]], [3, [[0, 1]]]])

    def test_alternatives_do_not_create_support_or_cross_record_patterns(self):
        inputs = records(('a', 'red birds'), ('a', 'red birds'),
                         ('b', 'red'), ('b', 'birds'))
        result = compare_patterns(inputs)
        for family in ('unordered', 'ordered', 'adjacent'):
            self.assertEqual(result[family], [])

    def test_casefold_hyphens_symbols_and_multiple_occurrences(self):
        result = compare_patterns(records(('a', 'Good-morning ☀ morning'),
                                          ('b', 'good morning ☀')))
        self.assertEqual(result['tokens'][0], ['good', 'morning', '☀', 'morning'])
        self.assertEqual(lookup(result, 'adjacent', ('good', 'morning'))['notes'], ['a', 'b'])
        self.assertEqual(lookup(result, 'ordered', ('good', 'morning'))['positions'][0],
                         [0, [[0, 1], [0, 3]]])
        self.assertIsNotNone(lookup(result, 'adjacent', ('morning', '☀')))


if __name__ == '__main__':
    unittest.main()
