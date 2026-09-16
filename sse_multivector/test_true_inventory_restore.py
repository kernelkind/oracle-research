import copy
import json
from pathlib import Path
import tempfile
import unittest

from true_inventory_restore import (restore, retain_membership_additions, prepare,
                                    identity, REFERENCE, REFERENCE_SOURCE, SHARED)

CODE = Path(__file__).resolve().parent
RESEARCH = CODE / 'navigation-research-v1'


def read(path):
    return json.loads(path.read_text())


class RestorationTests(unittest.TestCase):
    def test_reference_identity_uses_existing_frozen_scoring_files(self):
        reference = identity(REFERENCE, REFERENCE_SOURCE)
        self.assertEqual(set(reference['source_sha256']), set(SHARED))
        self.assertEqual(reference['source_sha256'], identity(REFERENCE, CODE)['source_sha256'])

    def test_restores_inventory_without_changing_existing_data(self):
        old = read(RESEARCH / 'TRUE10/derived/canonical.json')
        titles = read(CODE / 'hdbv2-node-titles-v21-astra-low/titles.json')
        before = copy.deepcopy(old)
        result, missing = restore(old, titles)
        self.assertEqual(old, before)
        self.assertEqual(result['titles']['groups'][:-1], old['titles']['groups'])
        self.assertEqual(result['scores'], old['scores'])
        self.assertEqual(result['source_packets'], old['source_packets'])
        self.assertEqual(result['consolidations'], old['consolidations'])
        restored = result['titles']['groups'][-1]
        source = next(g for g in titles['groups'] if g['group'] == 'Sf5a4b23523')
        self.assertEqual(restored['instances'], source['instances'])
        self.assertEqual(restored['title'], '#coffeechain')
        self.assertEqual(restored['title_override']['previous_title'], source['title'])
        self.assertEqual(len(result['titles']['groups']), 59)
        self.assertEqual(len(missing), 116)
        self.assertTrue(all('Sf5a4b23523' in (r['a_id'], r['b_id']) for r in missing))
        self.assertEqual(len({r['model_input'] for r in missing}), 116)

    def test_another_missing_group_is_not_silently_ignored(self):
        old = read(RESEARCH / 'TRUE10/derived/canonical.json')
        old['titles']['groups'].pop(0)
        with self.assertRaisesRegex(ValueError, 'inventory mismatch'):
            restore(old, read(CODE / 'hdbv2-node-titles-v21-astra-low/titles.json'))

    def test_prepare_preserves_previous_run(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'TRUE13'
            prepare(output)
            self.assertEqual(len(read(output / 'missing-inputs.json')), 116)
            with self.assertRaises(FileExistsError):
                prepare(output)

    def test_membership_additions_keep_unrelated_categories_and_reach_ancestors(self):
        old = {'source_sha256': 'same', 'root_node_id': 'root',
               'notes': [{'note_id': 'full1', 'note_short_id': 'N1'}],
               'nodes': [{'node_id': 'root', 'children': ['a', 'b'], 'note_ids': []},
                         {'node_id': 'a', 'children': ['c'], 'note_ids': []},
                         {'node_id': 'b', 'children': [], 'note_ids': ['N1']},
                         {'node_id': 'c', 'children': [], 'note_ids': ['N1']}],
               'note_masks': {k: {'N1': [[0, 2]]} for k in ['root', 'a', 'b', 'c']}}
        baseline = {'source_sha256': 'same', 'root_node_id': 'root',
                    'nodes': [copy.deepcopy(old['nodes'][0]), copy.deepcopy(old['nodes'][3])],
                    'note_masks': {'root': {}, 'c': {'N1': [[0, 2]]}}}
        expanded = copy.deepcopy(baseline)
        expanded['nodes'][1]['note_ids'].append('N2')
        expanded['note_masks']['c']['N2'] = [[3, 5]]
        expanded['notes'] = old['notes'] + [{'note_id': 'full2', 'note_short_id': 'N2'}]
        result = retain_membership_additions(old, baseline, expanded)
        self.assertEqual(result['nodes'], old['nodes'][:-1] + [expanded['nodes'][1]])
        self.assertEqual(result['note_masks']['b'], old['note_masks']['b'])
        for node in ['root', 'a', 'c']:
            self.assertEqual(result['note_masks'][node]['N2'], [[3, 5]])


if __name__ == '__main__':
    unittest.main()
