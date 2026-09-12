import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import mask_description_hierarchy
from category_path_compatibility import main as prepare_main, prepare_candidates
from subject_pattern_candidates import compare_patterns
from category_morphology_control import compare_memberships, main


def fixture():
    inputs = [dict(row=i, canonical_row=i, note=note, subject=subject,
                   fragments=['original', 'fragments'], alias_ids=['V' + str(i)])
              for i, (note, subject) in enumerate([
                  ('a', 'Birds birds'), ('b', 'bird'),
                  ('c', 'make bird'), ('d', 'make bird'),
                  ('e', 'making bird'), ('f', 'making bird'),
                  ('g', 'making birds'), ('h', 'bird making'),
                  ('i', 'make bright birds'), ('j', 'untouched'),
                  ('k', 'make'), ('k', 'birds')])]
    patterns = dict(compare_patterns(inputs), inputs=inputs, run_id='CAP04')
    candidates = prepare_candidates(patterns, ['bird', 'make', 'making', 'ghost'])['candidates']
    return patterns, candidates


class CategoryMorphologyControlTests(unittest.TestCase):
    def setUp(self):
        self.patterns, self.candidates = fixture()

    def test_recovers_forms_only_in_contiguous_tokens_and_keeps_all_positions(self):
        result = compare_memberships(self.patterns, self.candidates)
        by_label = {c['label']: c for c in result['stemmed']['candidates']}
        bird = by_label['bird']
        self.assertEqual(bird['positions'][0], [0, [[0], [1]]])
        self.assertEqual(bird['casefolded_character_occurrences'][0], [0, [[0, 5], [6, 11]]])
        self.assertIn('a', bird['added_notes'])
        pair = by_label['make bird']
        self.assertEqual(pair['notes'], ['c', 'd', 'e', 'f', 'g'])
        self.assertEqual(pair['added_notes'], ['e', 'f', 'g'])
        self.assertEqual(pair['removed_notes'], [])
        self.assertEqual(pair['added_rows'], [4, 5, 6])
        self.assertEqual(pair['removed_rows'], [])
        match = next(m for m in pair['matches'] if m['row'] == 6)
        self.assertEqual(match, dict(row=6, note='g', token_positions=[0, 1],
                                    casefolded_character_span=[0, 12],
                                    casefolded_text='making birds', raw_tokens=['making', 'birds'],
                                    stemmed_tokens=['make', 'bird']))
        self.assertNotIn('h', pair['notes'])  # Reversed order is not contiguous matching.
        self.assertNotIn('i', pair['notes'])  # No gap across another token.
        self.assertNotIn('k', pair['notes'])  # Never join separate input records.

    def test_preserves_raw_candidates_inputs_empty_and_equal_groups(self):
        before = copy.deepcopy((self.patterns, self.candidates))
        result = compare_memberships(self.patterns, self.candidates)
        self.assertEqual((self.patterns, self.candidates), before)
        self.assertEqual(result['literal']['candidates'], self.candidates)
        self.assertEqual(len(result['stemmed']['candidates']), len(self.candidates))
        by_label = {c['label']: c for c in result['stemmed']['candidates']}
        for original in self.candidates:
            for field in ('id', 'tokens', 'label', 'features'):
                self.assertEqual(by_label[original['label']][field], original[field])
        self.assertEqual(by_label['making']['stemmed_tokens'], ['make'])
        self.assertIn(by_label['ghost']['id'], result['stemmed']['empty_candidates'])
        equal = sorted([by_label['make bird']['id'], by_label['making bird']['id']])
        self.assertIn(dict(notes=['c', 'd', 'e', 'f', 'g'], candidate_ids=equal),
                      result['stemmed']['equal_note_set_classes'])

    def test_uses_existing_relations_on_raw_features_and_reports_all_edge_changes(self):
        relations = mask_description_hierarchy.description_relations
        with patch.object(mask_description_hierarchy, 'description_relations', wraps=relations) as reused:
            result = compare_memberships(self.patterns, self.candidates)
        self.assertEqual(reused.call_count, 2)
        self.assertEqual(result['literal']['relations'], relations(self.candidates))
        self.assertEqual(result['stemmed']['relations'], relations(result['stemmed']['candidates']))
        ids = {c['label']: c['id'] for c in self.candidates}
        self.assertIn([ids['make'], ids['make bird']],
                      result['stemmed']['relations']['descriptor_extension']['all_edges'])
        self.assertNotIn([ids['make'], ids['making bird']],
                         result['stemmed']['relations']['descriptor_extension']['all_edges'])
        for rule in ('note_subset', 'descriptor_extension'):
            for field in ('all_edges', 'immediate_edges'):
                old = {tuple(e) for e in result['literal']['relations'][rule][field]}
                new = {tuple(e) for e in result['stemmed']['relations'][rule][field]}
                self.assertEqual(result['edge_changes'][rule][field],
                                 dict(added=[list(e) for e in sorted(new-old)],
                                      removed=[list(e) for e in sorted(old-new)]))

    def test_rejects_changed_source_tokens_or_frozen_candidate_fields(self):
        for field in ('tokens', 'features', 'notes', 'positions', 'id', 'label'):
            candidates = copy.deepcopy(self.candidates)
            candidates[0][field] = 'changed' if field in ('id', 'label') else []
            with self.subTest(field=field), self.assertRaises(ValueError):
                compare_memberships(self.patterns, candidates)
        changed = copy.deepcopy(self.patterns)
        changed['tokens'][0][0] = 'wrong'
        with self.assertRaises(ValueError):
            compare_memberships(changed, self.candidates)

    def test_cli_offline_replay_preserves_frozen_files_and_source_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            patterns = root / 'patterns.json'
            patterns.write_text(json.dumps(self.patterns))
            prepared = root / 'prepared'
            prepare_main(['prepare', '--patterns', str(patterns), '--anchors',
                          'bird', 'make', 'making', 'ghost', '--output', str(prepared)])
            before = {str(p): p.read_bytes() for p in root.rglob('*') if p.is_file()}
            outputs = [root / 'control', root / 'replay']
            for output in outputs:
                main(['--patterns', str(patterns), '--prepared', str(prepared), '--output', str(output)])
                config = json.loads((output / 'config.json').read_text())
                self.assertEqual(config['packages']['nltk'], '3.9.2')
                self.assertEqual(config['normalizer'], 'nltk.stem.snowball.EnglishStemmer')
                self.assertFalse(config['ignore_stopwords'])
                self.assertEqual(config['input_count'], 12)
                self.assertEqual(config['note_count'], 11)
                self.assertEqual(config['patterns_source']['sha256'], hashlib.sha256(patterns.read_bytes()).hexdigest())
                self.assertEqual((output / 'inputs.json').read_bytes(), (prepared / 'inputs.json').read_bytes())
                self.assertEqual((output / 'candidates.json').read_bytes(), (prepared / 'candidates.json').read_bytes())
                for filename, digest in config['code_sha256'].items():
                    self.assertEqual(digest, hashlib.sha256((output / 'source' / filename).read_bytes()).hexdigest())
                self.assertIn('stem/snowball.py', config['nltk_source_sha256'])
                for filename, digest in config['nltk_source_sha256'].items():
                    self.assertEqual(digest, hashlib.sha256((output / 'source' / 'nltk' / filename).read_bytes()).hexdigest())
            self.assertEqual((outputs[0] / 'result.json').read_bytes(), (outputs[1] / 'result.json').read_bytes())
            self.assertEqual(before, {name: Path(name).read_bytes() for name in before})
            with self.assertRaises(FileExistsError):
                main(['--patterns', str(patterns), '--prepared', str(prepared), '--output', str(outputs[0])])
            changed_inputs = json.loads((prepared / 'inputs.json').read_text())
            changed_inputs[0]['subject'] = 'modified'
            (prepared / 'inputs.json').write_text(json.dumps(changed_inputs))
            with self.assertRaises(ValueError):
                main(['--patterns', str(patterns), '--prepared', str(prepared), '--output', str(root / 'bad')])
            self.assertFalse((root / 'bad').exists())


if __name__ == '__main__':
    unittest.main()
