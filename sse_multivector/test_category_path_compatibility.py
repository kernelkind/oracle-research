import copy
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import mask_description_hierarchy
from subject_pattern_candidates import compare_patterns
from category_path_compatibility import prepare_candidates, analyze_scores, main


def source():
    inputs = [dict(row=i, canonical_row=i, note=note, subject=text,
                   fragments=['unchanged', 'fragments'], alias_ids=['V' + str(i)],
                   text='original note ' + note)
              for i, (note, text) in enumerate([
                  ('a', 'Sea salt and sea salt.'), ('a', 'bread'),
                  ('b', 'Sea salt and bread.'), ('c', 'bread'),
                  ('d', 'other')])]
    return dict(compare_patterns(inputs), inputs=inputs, run_id='CAP04')


def scores(prepared):
    values = {'salt': [.5, .5, .8, .1, .1],
              'sea salt': [.2, .9, .8, .1, .1],
              'salt and': [.1, .1, .1, .1, .1],
              'bread': [.1, .1, .1, .5, .1],
              'and bread': [.1, .1, .1, .1, .1]}
    return [dict(row=r['row'], text=r['subject'], condition='single', labels=[c['label']],
                 scores=[dict(label=c['label'], score=values[c['label']][r['row']],
                              logit=math.log(values[c['label']][r['row']] /
                                             (1-values[c['label']][r['row']])),
                              accepted=values[c['label']][r['row']] >= .5)])
            for c in prepared['candidates'] for r in prepared['inputs']]


class CategoryPathCompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.source = source()
        self.prepared = prepare_candidates(self.source, ['bread', 'salt'])

    def test_preserves_inputs_patterns_and_all_occurrences(self):
        before = copy.deepcopy(self.source)
        result = prepare_candidates(self.source, ['bread', 'salt'])
        self.assertEqual(self.source, before)
        self.assertEqual(result['inputs'], self.source['inputs'])
        self.assertEqual(result['inputs'][0]['fragments'], ['unchanged', 'fragments'])
        expected = [p for p in self.source['adjacent']
                    if set(p['tokens']) & {'bread', 'salt'}]
        pairs = [c for c in result['candidates'] if c['family'] == 'adjacent']
        self.assertEqual(len(pairs), len(expected))
        for candidate, original in zip(pairs, expected):
            for key, value in original.items():
                self.assertEqual(candidate[key], value)
            self.assertEqual(candidate['features'], original['tokens'])
        salt = next(c for c in result['candidates'] if c['label'] == 'salt')
        self.assertEqual(salt['positions'], [[0, [[1], [4]]], [2, [[1]]]])
        self.assertEqual(salt['casefolded_character_occurrences'],
                         [[0, [[4, 8], [17, 21]]], [2, [[4, 8]]]])

    def test_rejects_nonliteral_join_and_broken_source_provenance(self):
        for change in ('punctuation', 'tokens', 'spans', 'positions', 'notes', 'rows'):
            broken = copy.deepcopy(self.source)
            if change == 'punctuation':
                broken['inputs'][0]['subject'] = 'Sea-salt and sea salt.'
            elif change == 'tokens':
                broken['tokens'][0][0] = 'different'
            elif change == 'spans':
                broken['casefolded_character_spans'][0][0] = [0, 2]
            else:
                pair = next(p for p in broken['adjacent'] if p['tokens'] == ['sea', 'salt'])
                pair[change] = []
            with self.subTest(change=change), self.assertRaises(ValueError):
                prepare_candidates(broken, ['salt'])

    def test_complete_native_matrix_and_note_max_retains_all_tied_rows(self):
        result = analyze_scores(self.prepared, scores(self.prepared), [.5, .8])
        salt = next(c for c in self.prepared['candidates'] if c['label'] == 'salt')
        entry = next(n for n in result['note_scores']
                     if n['candidate_id'] == salt['id'] and n['note'] == 'a')
        self.assertEqual(entry['score'], .5)
        self.assertEqual(entry['attaining_rows'], [0, 1])
        selected = next(c for c in result['thresholds'][0]['candidates'] if c['label'] == 'salt')
        self.assertEqual(selected['rows'], [0, 1, 2])
        self.assertEqual(selected['notes'], ['a', 'b'])
        higher = next(c for c in result['thresholds'][1]['candidates'] if c['label'] == 'salt')
        self.assertEqual(higher['notes'], ['b'])

    def test_rejects_missing_duplicate_extra_nonfinite_or_mismatched_scores(self):
        valid = scores(self.prepared)
        for kind in ('missing', 'duplicate', 'extra', 'text', 'condition', 'labels',
                     'label', 'score', 'logit', 'range', 'row'):
            broken = copy.deepcopy(valid)
            if kind == 'missing':
                broken.pop()
            elif kind == 'duplicate':
                broken[-1] = copy.deepcopy(broken[0])
            elif kind == 'extra':
                broken.append(copy.deepcopy(broken[0]))
            elif kind == 'text':
                broken[0]['text'] += ' changed'
            elif kind == 'condition':
                broken[0]['condition'] = 'joint'
            elif kind == 'labels':
                broken[0]['labels'].append('salt')
            elif kind == 'label':
                broken[0]['scores'][0]['label'] = 'unknown'
            elif kind in ('score', 'logit'):
                broken[0]['scores'][0][kind] = float('nan')
            elif kind == 'range':
                broken[0]['scores'][0]['score'] = 1.1
            else:
                broken[0]['row'] = True
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                analyze_scores(self.prepared, broken, [.5])

    def test_equality_empty_singletons_and_changes_are_not_filtered(self):
        result = analyze_scores(self.prepared, scores(self.prepared), [.5])
        threshold = result['thresholds'][0]
        ids = {c['label']: c['id'] for c in threshold['candidates']}
        self.assertEqual(len(threshold['candidates']), len(self.prepared['candidates']))
        self.assertIn(ids['salt and'], threshold['empty_candidates'])
        self.assertIn(ids['bread'], threshold['single_note_candidates'])
        self.assertIn(dict(notes=['a', 'b'], candidate_ids=sorted([ids['salt'], ids['sea salt']])),
                      threshold['equal_note_set_classes'])
        bread = next(c for c in threshold['candidates'] if c['label'] == 'bread')
        self.assertEqual(bread['removed_notes'], ['a', 'b'])
        self.assertEqual(bread['added_notes'], [])
        sea_salt = next(c for c in threshold['candidates'] if c['label'] == 'sea salt')
        self.assertIn(1, sea_salt['rows'])  # Nonliteral fragment in note a is retained.
        self.assertNotIn([ids['salt'], ids['sea salt']], threshold['relations']['note_subset']['all_edges'])

    def test_reuses_both_existing_relations_and_reports_edge_differences(self):
        relation = mask_description_hierarchy.description_relations
        with patch.object(mask_description_hierarchy, 'description_relations', wraps=relation) as reused:
            result = analyze_scores(self.prepared, scores(self.prepared), [.5, .8])
        self.assertEqual(reused.call_count, 3)
        self.assertEqual(result['literal']['relations'], relation(self.prepared['candidates']))
        for threshold in result['thresholds']:
            self.assertEqual(threshold['relations'], relation(threshold['candidates']))
            for rule in ('note_subset', 'descriptor_extension'):
                for field in ('all_edges', 'immediate_edges'):
                    old = {tuple(e) for e in result['literal']['relations'][rule][field]}
                    new = {tuple(e) for e in threshold['relations'][rule][field]}
                    self.assertEqual(threshold['edge_changes'][rule][field],
                                     dict(added=[list(e) for e in sorted(new-old)],
                                          removed=[list(e) for e in sorted(old-new)]))

    def test_rejects_invalid_anchors_and_cutoffs(self):
        for anchors in ([], ['salt', 'salt'], ['Sea salt'], ['Salt']):
            with self.subTest(anchors=anchors), self.assertRaises(ValueError):
                prepare_candidates(self.source, anchors)
        for cutoffs in ([], [.5, .5], [float('inf')], [-.1], [1.1]):
            with self.subTest(cutoffs=cutoffs), self.assertRaises(ValueError):
                analyze_scores(self.prepared, scores(self.prepared), cutoffs)

    def test_cli_copies_all_945_inputs_and_snapshots_with_hashes(self):
        inputs = copy.deepcopy(self.source['inputs'])
        for row in range(len(inputs), 945):
            inputs.append(dict(row=row, note='padding', subject='other', fragments=['preserved']))
        full = dict(compare_patterns(inputs), inputs=inputs, run_id='CAP04')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            patterns = root / 'CAP04.json'
            patterns.write_text(json.dumps(full))
            prepared_dir = root / 'prepared'
            main(['prepare', '--patterns', str(patterns), '--anchors', 'bread', 'salt',
                  '--output', str(prepared_dir)])
            self.assertEqual(json.loads((prepared_dir / 'inputs.json').read_text()), inputs)
            config = json.loads((prepared_dir / 'config.json').read_text())
            self.assertEqual(config['patterns_source']['sha256'],
                             hashlib.sha256(patterns.read_bytes()).hexdigest())
            self.assertEqual(config['inputs_sha256'],
                             hashlib.sha256((prepared_dir / 'inputs.json').read_bytes()).hexdigest())
            for filename, digest in config['code_sha256'].items():
                self.assertEqual(digest, hashlib.sha256((prepared_dir / 'source' / filename).read_bytes()).hexdigest())
            with self.assertRaises(FileExistsError):
                main(['prepare', '--patterns', str(patterns), '--anchors', 'salt',
                      '--output', str(prepared_dir)])
            candidates = json.loads((prepared_dir / 'candidates.json').read_text())
            native = []
            for candidate in candidates:
                for record in inputs:
                    native.append(dict(row=record['row'], text=record['subject'], condition='single',
                                       labels=[candidate['label']], scores=[dict(label=candidate['label'],
                                       score=.5, logit=0., accepted=True)]))
            native_path = root / 'scores.json'
            native_path.write_text(json.dumps(native))
            output = root / 'analysis'
            main(['analyze', '--prepared', str(prepared_dir), '--scores', str(native_path),
                  '--cutoffs', '.5', '.9481359422711596', '--output', str(output)])
            result = json.loads((output / 'result.json').read_text())
            self.assertEqual(len(result['thresholds'][1]['empty_candidates']), len(candidates))
            metadata = json.loads((output / 'config.json').read_text())
            self.assertEqual(metadata['scores_source']['sha256'],
                             hashlib.sha256(native_path.read_bytes()).hexdigest())
            self.assertEqual((output / 'inputs.json').read_bytes(), (prepared_dir / 'inputs.json').read_bytes())
            self.assertEqual((output / 'scores.json').read_bytes(), native_path.read_bytes())
            with self.assertRaises(FileExistsError):
                main(['analyze', '--prepared', str(prepared_dir), '--scores', str(native_path),
                      '--cutoffs', '.5', '--output', str(output)])


if __name__ == '__main__':
    unittest.main()
