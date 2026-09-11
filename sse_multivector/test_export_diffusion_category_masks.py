"""Category masks retain original byte spans from each full native group."""
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from export_diffusion_categories import export
from export_diffusion_hierarchy import export as export_viewer
from test_export_diffusion_hierarchy import digest, fixture


class DiffusionCategoryMaskExportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.run = self.root / 'run'
        self.run.mkdir()
        self.vector_map = self.root / 'vectors.json'
        self.notes = self.root / 'notes.json'
        self.titles = self.root / 'titles.json'
        self.output = self.root / 'categories.json'
        self.projection = self.root / 'projection.json'

    def save(self, values, titles):
        for name in ('hierarchy', 'configuration', 'evidence'):
            (self.run / f'{name}.json').write_text(json.dumps(values[name]))
        self.vector_map.write_text(json.dumps(values['vectors']))
        self.notes.write_text(json.dumps(values['notes']))
        self.titles.write_text(json.dumps(titles))
        export_viewer(self.run, self.vector_map, self.notes, self.run / 'viewer.json')

    def run_export(self):
        export(self.run, self.vector_map, self.notes, self.titles,
               self.output, self.projection)
        return json.loads(self.output.read_text())

    def test_masks_include_descendants_hidden_groups_and_highest_collapsed_group(self):
        self.save(fixture(), {'9': 'All notes', '8': 'Coffee and tea'})
        before = {path: path.read_bytes() for path in self.root.rglob('*.json')}
        categories = self.run_export()
        self.assertIn('note_masks', categories)
        self.assertEqual(categories['note_masks'], {
            '9': {'N001': [[0, 5], [6, 9], [10, 13]], 'N002': [[0, 3]],
                  'N003': [[0, 5]], 'N004': [[0, 5]]},
            '8': {'N001': [[0, 5], [6, 9], [10, 13]], 'N002': [[0, 3]]},
        })
        self.assertEqual(categories['nodes'], [
            dict(node_id='9', label='All notes', analysis='', children=['8'],
                 note_ids=['N003', 'N004']),
            dict(node_id='8', label='Coffee and tea', analysis='', children=[],
                 note_ids=['N001', 'N002']),
        ])
        self.assertEqual(categories['schema_version'], 1)
        self.assertEqual(categories['source_sha256'], hashlib.sha256(self.notes.read_bytes()).hexdigest())
        self.assertEqual(before, {path: path.read_bytes() for path in before})
        self.assertEqual(set(self.root.rglob('*.json')), set(before) | {self.output, self.projection})

    def test_masks_use_every_alias_original_utf8_spans_and_exclude_sibling_vectors(self):
        values = fixture()
        # Row 5 now contributes a different mask of note a in a sibling group.
        vector = values['vectors']['vectors'][5]
        vector.update(note_id='a', note_short_id='N001', byte_spans=[[14, 18]],
                      fragments=['tail'])
        values['evidence'][5]['aliases'] = [dict(vector, text='café one two tail')]
        nodes = {node['id']: node for node in values['hierarchy']['nodes']}
        nodes[5]['note_ids'] = ['N001']
        nodes[9].update(children=[10, 8], note_ids=['N001', 'N002', 'N003'])
        values['hierarchy']['nodes'].append(dict(
            id=10, children=[5, 4], members=[4, 5], note_ids=['N001', 'N003']))
        # This distinct canonical-row alias contributes an overlapping UTF-8
        # span and a duplicate span already supplied by a different member row.
        alias = dict(values['vectors']['vectors'][0], vector_id='accent-alias',
                     short_id='VAC', byte_spans=[[3, 5], [6, 9]], fragments=['é', 'one'])
        values['vectors']['vectors'].append(alias)
        values['evidence'][0]['aliases'].append(dict(alias, text='café one two tail'))
        values['configuration']['sources']['mapping']['sha256'] = digest(values['vectors'])
        self.save(values, {'9': 'All notes', '8': 'Coffee and tea', '10': 'Other masks'})

        categories = self.run_export()
        self.assertIn('note_masks', categories)
        self.assertEqual(categories['note_masks'], {
            '9': {'N001': [[0, 5], [3, 5], [6, 9], [10, 13], [14, 18]],
                  'N002': [[0, 3]], 'N003': [[0, 5]]},
            '10': {'N001': [[14, 18]], 'N003': [[0, 5]]},
            '8': {'N001': [[0, 5], [3, 5], [6, 9], [10, 13]], 'N002': [[0, 3]]},
        })
        nodes = {node['node_id']: node for node in categories['nodes']}

        def full_notes(node_id):
            node = nodes[node_id]
            return set(node['note_ids']).union(*(full_notes(child) for child in node['children']))

        self.assertEqual(set(categories['note_masks']), set(nodes))
        for node_id, masks in categories['note_masks'].items():
            with self.subTest(node_id=node_id):
                self.assertEqual(set(masks), full_notes(node_id))


if __name__ == '__main__':
    unittest.main()
