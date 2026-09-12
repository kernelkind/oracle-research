import tempfile
import unittest
import zipfile
from pathlib import Path

import numpy as np
from nltk.corpus import wordnet as wn

from lmms_occurrence_probe import (
    candidate_keys, pool_layers, prepare_inputs, rank_conditions, read_inventory,
    tokenize_words,
)


class OccurrenceProbeTests(unittest.TestCase):
    def test_surface_control_recovers_inflection_without_synonym_expansion(self):
        surface = candidate_keys('tomatoes', 'tomatoe', 'NOUN', 'surface', wn)
        self.assertTrue(surface)
        self.assertEqual({key.split('%')[0] for key in surface}, {'tomato'})
        self.assertFalse(candidate_keys('tomatoes', 'tomatoe', 'NOUN', 'saved', wn))
        beet = candidate_keys('beet', 'boot', 'NOUN', 'surface', wn)
        self.assertEqual({wn.lemma_from_key(k).synset().name() for k in beet},
                         {'beet.n.01', 'beet.n.02'})
        self.assertNotIn('beet', {k.split('%')[0] for k in
                                 candidate_keys('beet', 'boot', 'NOUN', 'saved', wn)})

    def test_surface_uses_all_parts_and_saved_keeps_literal_lemma(self):
        keys = candidate_keys('canning', 'canning', 'NOUN', 'surface', wn)
        self.assertTrue(any('%2:' in key for key in keys))
        self.assertFalse(candidate_keys('canning', 'canning', 'NOUN', 'saved', wn))
        self.assertFalse(candidate_keys('Tomatoes', 'Tomato', 'NOUN', 'saved', wn))
        self.assertEqual(candidate_keys('chef', 'chef', 'PROPN', 'saved', wn),
                         candidate_keys('chef', 'chef', 'NOUN', 'saved', wn))

    def test_fixed_layers_use_last_first_skip_embedding_and_twenty_fifth_weight(self):
        states = [np.full((1, 5, 2), i, dtype=np.float32) for i in range(25)]
        states[24][0, 1] = [10, 20]
        states[24][0, 2] = [30, 40]
        weights = [1., 2.] + [0.] * 22 + [999.]
        result = pool_layers(states, [[1, 3], [3, 4]], weights)
        np.testing.assert_allclose(result, [[66, 76], [70, 70]])
        with self.assertRaises(ValueError):
            pool_layers(states[:24], [[1, 2]], weights)
        with self.assertRaises(ValueError):
            pool_layers(states, [[0, 0]], weights)

    def test_ranking_uses_one_score_vector_and_preserves_empty_candidates(self):
        labels = ['cat%1:05:00::', 'dog%1:05:00::', 'cat%1:18:00::']
        scores = np.array([.2, .9, .4])
        ranked = rank_conditions(labels, scores, {'saved': {labels[0], labels[2]},
                                                 'surface': set(), 'unrestricted': None})
        self.assertEqual(ranked['saved'], [(labels[2], .4), (labels[0], .2)])
        self.assertEqual(ranked['surface'], [])
        self.assertEqual(ranked['unrestricted'][0], (labels[1], .9))

    def test_input_preserves_all_context_and_requires_exact_offsets(self):
        words = [dict(text='A', start_char=0, end_char=1, lemma='a', upos='DET'),
                 dict(text='cat', start_char=2, end_char=5, lemma='cat', upos='NOUN')]
        inputs = [dict(row=1, note='N01', subject='A cat')]
        parses = [dict(row=1, subject='A cat', sentences=[words])]
        prepared = prepare_inputs(inputs, parses)
        self.assertEqual(prepared[0]['words'], words)
        self.assertEqual(prepared[0]['targets'], [1])
        self.assertEqual(inputs, [dict(row=1, note='N01', subject='A cat')])
        words[1]['end_char'] = 4
        with self.assertRaises(ValueError):
            prepare_inputs(inputs, parses)

    def test_real_bert_tokenizer_keeps_wordpiece_ranges_and_rejects_overlength(self):
        from transformers import BertTokenizer
        with tempfile.TemporaryDirectory() as directory:
            vocab = Path(directory) / 'vocab.txt'
            vocab.write_text('[PAD]\n[UNK]\n[CLS]\n[SEP]\n[MASK]\ntomato\n##es\n.\n')
            tokenizer = BertTokenizer(vocab_file=str(vocab), do_lower_case=False)
            ids, spans = tokenize_words(['tomatoes', '.'], tokenizer, 8)
            self.assertEqual(ids, [2, 5, 6, 7, 3])
            self.assertEqual(spans, [[1, 3], [3, 4]])
            with self.assertRaises(ValueError):
                tokenize_words(['tomatoes', '.'], tokenizer, 4)

    def test_inventory_read_normalizes_and_rejects_invalid_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'vectors.zip'
            with zipfile.ZipFile(path, 'w') as archive:
                archive.writestr('vectors.txt', 'cat%1:05:00:: 3 4\ndog%1:05:00:: 0 2\n')
            labels, matrix, info = read_inventory(path, dimension=2, max_bytes=10000)
            self.assertEqual(labels, ['cat%1:05:00::', 'dog%1:05:00::'])
            np.testing.assert_allclose(matrix, [[.6, .8], [0, 1]])
            self.assertEqual(info['rows'], 2)
            with self.assertRaises(ValueError):
                read_inventory(path, dimension=2, max_bytes=1)
            with zipfile.ZipFile(path, 'w') as archive:
                archive.writestr('vectors.txt', 'cat%1:05:00:: 0 0\n')
            with self.assertRaises(ValueError):
                read_inventory(path, dimension=2, max_bytes=10000)


if __name__ == '__main__':
    unittest.main()
