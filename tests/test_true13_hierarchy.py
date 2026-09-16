"""Verify the complete restored graph through the production browser format."""
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT / 'sse_multivector'
RESEARCH = CODE / 'navigation-research-v1'
RUN = RESEARCH / 'TRUE13'
RESTORED = 'Sf5a4b23523'


def read(path):
    return json.loads(path.read_text())


class TRUE13HierarchyTests(unittest.TestCase):
    def test_launcher_runs_from_another_directory(self):
        result = subprocess.run(['bash', str(CODE / 'run-true13-hierarchy.sh'), '--check'],
                                cwd='/', capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_every_source_group_accounted_for_in_view(self):
        source = read(CODE / 'hdbv2-node-titles-v21-astra-low/titles.json')
        canonical = read(RUN / 'canonical.json')
        view = read(RUN / 'categories.json')
        represented = {g['group']: g['group'] for g in source['groups']}
        for item in canonical['consolidations']:
            represented.update({g: item['canonical'] for g in item['source_group_ids']})
        self.assertEqual(set(represented.values()), {n['node_id'] for n in view['nodes']} - {'root'})
        self.assertEqual(len(view['nodes']), 60)
        self.assertEqual(len(view['notes']), 79)

    def test_existing_titles_scores_masks_and_raw_edges_unchanged(self):
        old = read(RESEARCH / 'TRUE10/derived/canonical.json')
        new = read(RUN / 'canonical.json')
        self.assertEqual(new['titles']['groups'][:-1], old['titles']['groups'])
        self.assertEqual(new['scores'][:3306], old['scores'])
        self.assertEqual(len(new['scores']), 3422)
        self.assertEqual(new['source_packets'], old['source_packets'])
        old_edges = read(RESEARCH / 'TRUE11/native-graph.json')['raw_edges']
        new_edges = read(RUN / 'native-graph.json')['raw_edges']
        self.assertEqual([e for e in new_edges if RESTORED not in (e['a_id'], e['b_id'])], old_edges)

    def test_restored_group_keeps_all_original_masks(self):
        node = next(n for n in read(RUN / 'native-notes.json')['nodes'] if n['group'] == RESTORED)
        source = next(p for p in read(CODE / 'hdbv2-node-titles-v20-astra-low/source-packets.json')['packets']
                      if p['packet'] == RESTORED)
        actual = {i['instance']: i for i in node['matched_instances']}
        self.assertEqual(set(actual), {i['instance'] for i in source['instances']})
        for original in source['instances']:
            for field in ('note_id', 'text', 'byte_spans'):
                self.assertEqual(actual[original['instance']][field], original[field])
        self.assertEqual(node['own_note_count'], 7)

    def test_original_categories_and_additional_memberships_visible(self):
        view = read(RUN / 'categories.json')
        nodes = {n['node_id']: n for n in view['nodes']}
        expanded = read(RESEARCH / 'TRUE12/hierarchy/categories.json')
        original = read(RESEARCH / 'TRUE11/categories.json')
        for spec in (expanded, original):
            for node in spec['nodes']:
                key = node['node_id']
                if key == 'root':
                    continue
                self.assertTrue(set(node['note_ids']) <= set(nodes[key]['note_ids']))
                for note, spans in spec['note_masks'][key].items():
                    self.assertTrue(set(map(tuple, spans)) <= set(map(tuple, view['note_masks'][key][note])))
        self.assertIn('S8ea08f1aff', nodes, 'Music at Coffee Shops remains visible')
        self.assertEqual(nodes[RESTORED]['label'], '#coffeechain')

    def test_root_reaches_every_category_and_masks_match_recursive_notes(self):
        view = read(RUN / 'categories.json')
        nodes = {n['node_id']: n for n in view['nodes']}
        reached = set()

        def walk(key, path):
            self.assertNotIn(key, path, 'cyclic category relationship')
            reached.add(key)
            notes = set(nodes[key]['note_ids'])
            for child in nodes[key]['children']:
                notes.update(walk(child, path | {key}))
                for note, spans in view['note_masks'][child].items():
                    self.assertTrue(set(map(tuple, spans)) <= set(map(tuple, view['note_masks'][key][note])))
            self.assertEqual(notes, set(view['note_masks'][key]))
            return notes

        walk('root', set())
        self.assertEqual(reached, set(nodes))


if __name__ == '__main__':
    unittest.main()
