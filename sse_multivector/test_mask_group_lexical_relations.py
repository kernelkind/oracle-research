import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from mask_group_lexical_relations import prepare_groups, lexical_relations


def group(name, phrase, row):
    return dict(id=name, features=phrase.lower().split(), seed_rows=[row],
                rows=[row], notes=['N' + str(row)])


def record(row, phrase):
    return dict(row=row, aliases=[dict(short_id='V' + str(row),
                note_short_id='N' + str(row), fragments=[phrase], text=phrase)])


def lexicon():
    return dict(queries={'bread': ['bread.n.1'], 'sourdough_bread': ['sourdough.n.1'],
                         'loaf': ['bread.n.1'], 'coffee': ['coffee.n.1']},
                senses={
                    'bread.n.1': dict(definition='bread', hypernyms=['food.n.1']),
                    'sourdough.n.1': dict(definition='sourdough', hypernyms=['bread.n.1']),
                    'coffee.n.1': dict(definition='coffee', hypernyms=['food.n.1']),
                    'food.n.1': dict(definition='food', hypernyms=[]),
                })


class LexicalRelationsTests(unittest.TestCase):
    def test_seeds_preserve_word_order_and_all_group_evidence(self):
        ds = [dict(id='a', features=['bread', 'sourdough'], seed_rows=[0],
                   rows=[0, 1], notes=['N0', 'N1'])]
        evidence = [record(0, 'sourdough bread'), record(1, 'I bake sourdough bread')]
        groups = prepare_groups(ds, evidence)
        self.assertEqual(groups[0]['queries'], ['sourdough_bread'])
        self.assertEqual(groups[0]['evidence'], evidence)
        self.assertEqual(groups[0]['source_group'], ds[0])

    def test_subsumption_is_directed_and_shared_ancestor_is_not_subsumption(self):
        ds = [group('bread', 'bread', 0), group('sourdough', 'sourdough bread', 1),
              group('coffee', 'coffee', 2)]
        gs = prepare_groups(ds, [record(i, s) for i, s in enumerate(
            ['bread', 'sourdough bread', 'coffee'])])
        result = lexical_relations(gs, lexicon())
        self.assertEqual([(p['parent'], p['child']) for p in result['broader_candidates']],
                         [('bread', 'sourdough')])
        self.assertEqual(result['broader_candidates'][0]['witnesses'][0]['path'],
                         ['sourdough.n.1', 'bread.n.1'])

    def test_equivalence_is_separate_and_missing_words_stay_unknown(self):
        ds = [group('bread', 'bread', 0), group('loaf', 'loaf', 1),
              group('unknown', 'newword', 2)]
        gs = prepare_groups(ds, [record(i, s) for i, s in enumerate(['bread', 'loaf', 'newword'])])
        result = lexical_relations(gs, lexicon())
        self.assertEqual(result['broader_candidates'], [])
        self.assertEqual(result['equivalent_candidates'][0]['groups'], ['bread', 'loaf'])
        self.assertEqual(result['unknown_groups'], ['unknown'])
        self.assertEqual(len(result['pairs']), 6)

    def test_all_senses_are_retained_not_silently_disambiguated(self):
        data = lexicon()
        data['queries']['bread'].append('money.n.1')
        data['senses']['money.n.1'] = dict(definition='money', hypernyms=[])
        data['queries']['cash'] = ['money.n.1']
        gs = prepare_groups([group('bread', 'bread', 0), group('cash', 'cash', 1)],
                            [record(0, 'bread'), record(1, 'cash')])
        result = lexical_relations(gs, data)
        self.assertEqual(result['group_senses']['bread'], ['bread.n.1', 'money.n.1'])
        self.assertEqual(result['equivalent_candidates'][0]['sense_ids'], ['money.n.1'])

    def test_cli_snapshots_inputs_and_refuses_overwrite(self):
        script = Path(__file__).with_name('mask_group_lexical_relations.py')
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            inputs = {'groups': [group('bread', 'bread', 0), group('sourdough', 'sourdough bread', 1)],
                      'evidence': [record(0, 'bread'), record(1, 'sourdough bread')],
                      'lexicon': lexicon()}
            command = [sys.executable, str(script), '--output', str(root / 'out'), '--run-id', 'test']
            for name, data in inputs.items():
                path = root / (name + '.json')
                path.write_text(json.dumps(data))
                command += ['--' + name, str(path)]
            subprocess.run(command, capture_output=True, text=True, check=True)
            result = json.loads((root / 'out' / 'relations.json').read_text())
            self.assertEqual(len(result['broader_candidates']), 1)
            saved = {p.name: p.read_bytes() for p in (root / 'out').iterdir() if p.is_file()}
            again = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(again.returncode, 0)
            self.assertIn('preserve', again.stderr)
            self.assertEqual(saved, {p.name: p.read_bytes() for p in (root / 'out').iterdir() if p.is_file()})


if __name__ == '__main__':
    unittest.main()
