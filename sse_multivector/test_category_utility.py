import unittest

from category_utility import utility_scores, note_weights


class CategoryUtilityTests(unittest.TestCase):
    def test_published_probability_formula(self):
        result = utility_scores([{'a'}, {'a'}, {'b'}], [1/3]*3,
                                {'all': [0, 1, 2], 'a': [0, 1], 'b': [2]})
        self.assertAlmostEqual(result['all']['utility'], 0)
        self.assertAlmostEqual(result['a']['utility'], 8/27)
        self.assertAlmostEqual(result['b']['utility'], 4/27)

    def test_each_note_has_equal_total_weight(self):
        evidence = [dict(aliases=[dict(note_short_id=n)]) for n in ['a', 'a', 'b']]
        self.assertEqual(note_weights(evidence), [0.25, 0.25, 0.5])

    def test_single_object_word_can_raise_score_without_shared_evidence(self):
        original = [{'a'}, {'b'}, {'c'}]
        changed = [{'a', 'unique'}, {'b'}, {'c'}]
        before = utility_scores(original, [1/3]*3, {'group': [0, 1]})
        after = utility_scores(changed, [1/3]*3, {'group': [0, 1]})
        self.assertAlmostEqual(after['group']['utility']-before['group']['utility'], 5/54)


if __name__ == '__main__':
    unittest.main()
