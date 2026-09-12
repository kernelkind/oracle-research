import copy
import unittest

from dependency_description_probe import dependency_paths


def word(i, lemma, pos, head, relation):
    return dict(id=i, text=lemma, lemma=lemma, upos=pos, head=head, deprel=relation)


class DependencyDescriptionProbeTests(unittest.TestCase):
    def test_paths_retain_connections_direction_and_prepositions(self):
        words = [word(1, 'rosemary', 'NOUN', 0, 'root'),
                 word(2, 'in', 'ADP', 3, 'case'),
                 word(3, 'bread', 'NOUN', 1, 'nmod')]
        original = copy.deepcopy(words)
        paths = dependency_paths([words])
        path = next(p for p in paths if p['word_ids'] == [1, 3])
        self.assertEqual(path['nodes'], [['rosemary', 'NOUN'], ['bread', 'NOUN']])
        self.assertEqual(path['edges'], [['down', 'nmod']])
        self.assertEqual(path['case_dependents'], [[], [['in', 'ADP']]])
        self.assertEqual(words, original)
        changed = copy.deepcopy(words)
        changed[1]['lemma'] = 'without'
        self.assertNotEqual(path['case_dependents'],
                            next(p for p in dependency_paths([changed])
                                 if p['word_ids'] == [1, 3])['case_dependents'])

    def test_all_occurrences_and_sentences_remain_separate(self):
        words = [word(1, 'coffee', 'NOUN', 2, 'obj'),
                 word(2, 'drink', 'VERB', 0, 'root'),
                 word(3, 'coffee', 'NOUN', 2, 'obl')]
        paths = dependency_paths([words, words])
        self.assertEqual(len(paths), 6)
        p = paths[0]
        self.assertEqual(p['word_ids'], [1, 2])
        self.assertEqual(p['edges'], [['up', 'obj']])
        self.assertEqual({p['sentence'] for p in paths}, {0, 1})
        full = next(p for p in paths if p['sentence'] == 0 and p['word_ids'] == [1, 2, 3])
        self.assertEqual(full['edges'], [['up', 'obj'], ['down', 'obl']])

    def test_bad_trees_are_rejected(self):
        for words in [[], [word(1, 'x', 'NOUN', 2, 'obj')],
                      [word(1, 'x', 'NOUN', 0, 'root'), word(2, 'y', 'NOUN', 0, 'root')],
                      [word(1, 'x', 'NOUN', 0, 'root'), word(2, 'y', 'NOUN', 3, 'obj'),
                       word(3, 'z', 'NOUN', 2, 'obj')]]:
            with self.assertRaises(ValueError):
                dependency_paths([words])


if __name__ == '__main__':
    unittest.main()
