import unittest
from copy import deepcopy
from pathlib import Path

import numpy as np
from nltk.corpus import wordnet as wn

from lmms_occurrence_probe import candidate_keys, rank_conditions
from lmms_pos_control import score_saved, validate_sources


class PosControlTests(unittest.TestCase):
    def test_source_validation_binds_labels_offsets_and_loaded_dictionary(self):
        inputs = [dict(row=1, note='N01', subject='Bread.', text='Bread.',
                       fragments=['Bread'])]
        word = dict(text='Bread', lemma='bread', upos='NOUN', start_char=0, end_char=5)
        encoded = [dict(**inputs[0], words=[word], targets=[0])]
        targets = [dict(row=1, note='N01', subject='Bread.', word_index=0, word=word)]
        archive = Path(wn.root.zipfile.filename)
        validate_sources(inputs, encoded, targets, wn, archive)
        changed = deepcopy(targets)
        changed[0]['note'] = 'N02'
        with self.assertRaises(ValueError):
            validate_sources(inputs, encoded, changed, wn, archive)
        changed = deepcopy(encoded)
        changed[0]['words'][0]['end_char'] = 4
        with self.assertRaises(ValueError):
            validate_sources(inputs, changed, targets, wn, archive)
        with self.assertRaises(ValueError):
            validate_sources(inputs, encoded, targets, wn, archive.with_name('other.zip'))

    def source(self):
        labels = ['bread%1:13:00::', 'bread%2:35:00::']
        matrix = np.array([[1., 0.], [0., 1.]])
        vectors = np.array([[.6, .8]])
        word = dict(text='Bread', lemma='bread', upos='NOUN')
        candidates = {c: candidate_keys('Bread', 'bread', 'NOUN', c, wn)
                      for c in ('saved', 'surface', 'unrestricted')}
        matched = rank_conditions(labels, matrix @ vectors[0], candidates)
        targets = [dict(row=1, note='N01', subject='Bread preparation.', word_index=0,
                        word=word, matches={c:[dict(key=k,cosine=s) for k,s in rows]
                                          for c,rows in matched.items()})]
        return targets, vectors, labels, matrix

    def test_replays_existing_conditions_before_scoring_new_pos_condition(self):
        targets, vectors, labels, matrix = self.source()
        results, replay = score_saved(targets, vectors, labels, matrix, wn)
        self.assertEqual(replay['comparisons'], 3)
        self.assertEqual(replay['maximum_cosine_difference'], 0.)
        self.assertEqual(results[0]['matches'][0]['key'], labels[0])
        self.assertEqual(results[0]['matches'][0]['synset'], 'bread.n.01')
        self.assertNotIn('surface_pos', targets[0]['matches'])

    def test_drift_or_vector_shape_mismatch_is_rejected(self):
        targets, vectors, labels, matrix = self.source()
        with self.assertRaises(ValueError):
            score_saved(targets, vectors[:0], labels, matrix, wn)
        targets[0]['matches']['surface'][0]['cosine'] = .123
        with self.assertRaises(ValueError):
            score_saved(targets, vectors, labels, matrix, wn)


if __name__ == '__main__':
    unittest.main()
