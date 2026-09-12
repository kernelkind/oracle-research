import json
from pathlib import Path
import subprocess
import sys
import unittest

from mask_description_hierarchy import descriptions_from_masks, description_relations
from shared_mask_descriptions import shared_descriptions


def evidence(pairs):
    return [dict(row=i, aliases=[dict(note_short_id=n, fragments=f)])
            for i, (n, f) in enumerate(pairs)]


class SharedDescriptionsTests(unittest.TestCase):
    def test_shared_subset_without_complete_mask_becomes_candidate(self):
        records = evidence([
            ('a', ['fresh chicken stock']), ('b', ['make chicken stock']),
            ('c', ['chicken dinner']), ('d', ['bread']), ('e', ['bread']),
        ])
        baseline = descriptions_from_masks(records, keep_symbols=True)
        result = shared_descriptions(records)
        by_words = {tuple(d['features']): d for d in result['descriptions']}
        self.assertEqual(set(by_words), {('bread',), ('chicken',), ('chicken', 'stock')})
        self.assertEqual(by_words[('chicken', 'stock')]['rows'], [0, 1])
        self.assertEqual(by_words[('chicken', 'stock')]['notes'], ['a', 'b'])
        self.assertEqual(by_words[('bread',)], baseline[0])
        self.assertEqual(result['shared_seeds'][by_words[('chicken', 'stock')]['id']], ['stock'])
        relation = description_relations(result['descriptions'])['descriptor_extension']
        self.assertEqual(relation['immediate_edges'], [[by_words[('chicken',)]['id'], by_words[('chicken', 'stock')]['id']]])

    def test_equal_closures_do_not_duplicate_candidates(self):
        records = evidence([('a', ['fresh chicken stock']), ('b', ['make chicken stock'])])
        result = shared_descriptions(records)
        self.assertEqual(len(result['descriptions']), 1)
        d = result['descriptions'][0]
        self.assertEqual(d['features'], ['chicken', 'stock'])
        self.assertEqual(result['shared_seeds'][d['id']], ['chicken', 'stock'])

    def test_same_note_repetition_does_not_supply_recurrence(self):
        self.assertEqual(shared_descriptions(evidence([('a', ['bread']), ('a', ['bread'])]))['descriptions'], [])

    def test_seed_bound_can_miss_an_intersection(self):
        records = evidence([('a', ['fresh coffee milk']), ('b', ['warm coffee milk']),
                            ('c', ['black coffee']), ('d', ['cold milk'])])
        result = shared_descriptions(records)
        self.assertEqual({tuple(d['features']) for d in result['descriptions']}, {('coffee',), ('milk',)})

    def test_cli_reproduces_frozen_baseline_without_changing_files(self):
        root = Path(__file__).resolve().parent
        baseline = root / 'navigation-research-v1/MDH02/descriptions.json'
        source = root / 'geometric-hierarchy-v1/GDC09/evidence.json'
        before = source.read_bytes(), baseline.read_bytes()
        run = subprocess.run([sys.executable, str(root / 'shared_mask_descriptions.py'),
                              '--evidence', str(source), '--baseline', str(baseline)],
                             capture_output=True, text=True, check=True)
        result = json.loads(run.stdout)
        self.assertTrue(result['baseline_reproduced'])
        indexed = {d['id']: d for d in result['descriptions']}
        for original in json.loads(before[1]):
            self.assertEqual(indexed[original['id']], original)
        self.assertLessEqual(len(indexed), result['recurring_features'] + len(json.loads(before[1])))
        self.assertEqual((source.read_bytes(), baseline.read_bytes()), before)


if __name__ == '__main__':
    unittest.main()
