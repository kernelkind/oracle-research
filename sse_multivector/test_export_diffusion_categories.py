"""Category projection preserves each saved group's complete note membership."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from export_diffusion_categories import export, project
from export_diffusion_hierarchy import export as export_viewer
from test_export_diffusion_hierarchy import fixture


class DiffusionCategoryExportTests(unittest.TestCase):
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
        self.save(fixture())
        self.titles.write_text(json.dumps({'9': 'All notes', '8': 'Coffee and tea'}))

    def save(self, values):
        for name in ('hierarchy', 'configuration', 'evidence'):
            (self.run / f'{name}.json').write_text(json.dumps(values[name]))
        self.vector_map.write_text(json.dumps(values['vectors']))
        self.notes.write_text(json.dumps(values['notes']))
        viewer = self.run / 'viewer.json'
        if viewer.exists():
            viewer.unlink()
        export_viewer(self.run, self.vector_map, self.notes, viewer)

    def run_export(self):
        export(self.run, self.vector_map, self.notes, self.titles,
               self.output, self.projection)
        return json.loads(self.output.read_text()), json.loads(self.projection.read_text())

    def test_equal_parent_child_sets_collapse_and_single_note_choices_disappear(self):
        before = {p: p.read_bytes() for p in self.root.rglob('*.json')}
        categories, provenance = self.run_export()
        self.assertEqual(categories['schema_version'], 1)
        self.assertEqual(categories['hierarchy_id'], 'GDC09-note-categories')
        self.assertEqual(categories['root_node_id'], '9')
        self.assertEqual(categories['source_sha256'], hashlib.sha256(self.notes.read_bytes()).hexdigest())
        nodes = {node['node_id']: node for node in categories['nodes']}
        self.assertEqual(set(nodes), {'8', '9'})
        self.assertEqual(nodes['9']['children'], ['8'])
        self.assertEqual(nodes['9']['note_ids'], ['N003', 'N004'])
        self.assertEqual(nodes['8']['children'], [])
        self.assertEqual(nodes['8']['note_ids'], ['N001', 'N002'])
        self.assertEqual(nodes['8']['label'], 'Coffee and tea')
        self.assertEqual(categories['notes'], [
            {'note_id': note, 'note_short_id': f'N00{i}'}
            for i, note in enumerate('abcd', 1)])
        self.assertEqual(provenance['native_to_retained'], {'6': '8', '7': '8', '8': '8', '9': '9'})
        retained = {node['node_id']: node for node in provenance['retained_groups']}
        self.assertEqual(retained['8']['native_node_ids'], [8, 7])
        self.assertEqual(retained['8']['note_ids'], ['N001', 'N002'])
        self.assertEqual(before, {p: p.read_bytes() for p in before})
        self.assertEqual(set(self.root.rglob('*.json')), set(before) | {self.output, self.projection})

    def test_child_order_is_preserved_when_equal_membership_children_are_spliced(self):
        viewer = dict(root=20, groups=[
            dict(id=20, children=[15, 19], note_ids=list('abcd')),
            dict(id=15, children=[14, 12], note_ids=list('abc')),
            dict(id=14, children=[13, 11], note_ids=list('abc')),
            dict(id=13, children=[], note_ids=list('bc')),
            dict(id=11, children=[], note_ids=list('ab')),
            dict(id=12, children=[], note_ids=['a']),
            dict(id=19, children=[], note_ids=list('cd')),
        ])
        result = project(viewer)
        groups = {group['node_id']: group for group in result['retained_groups']}
        self.assertEqual(groups['20']['children'], ['15', '19'])
        self.assertEqual(groups['15']['children'], ['13', '11'])
        self.assertEqual(groups['15']['native_node_ids'], [15, 14])
        self.assertEqual(groups['15']['direct_note_ids'], [])
        self.assertEqual(result['native_to_retained']['12'], '15')

    def test_same_note_sets_in_different_branches_are_not_merged(self):
        result = project(dict(root=9, groups=[
            dict(id=9, children=[7, 8], note_ids=list('abcd')),
            dict(id=7, children=[5], note_ids=list('abc')),
            dict(id=8, children=[6], note_ids=list('abd')),
            dict(id=5, children=[], note_ids=list('ab')),
            dict(id=6, children=[], note_ids=list('ab')),
        ]))
        groups = {group['node_id']: group for group in result['retained_groups']}
        self.assertEqual(groups['7']['children'], ['5'])
        self.assertEqual(groups['8']['children'], ['6'])
        self.assertEqual(groups['5']['note_ids'], groups['6']['note_ids'])
        self.assertNotEqual(result['native_to_retained']['5'], result['native_to_retained']['6'])

    def test_title_analysis_is_optional_and_never_taken_from_evidence_subjects(self):
        self.titles.write_text(json.dumps({
            '9': {'label': 'All notes', 'analysis': 'Saved coverage'},
            '8': {'label': 'Coffee and tea'},
        }))
        categories, provenance = self.run_export()
        nodes = {node['node_id']: node for node in categories['nodes']}
        self.assertEqual(nodes['9']['analysis'], 'Saved coverage')
        self.assertEqual(nodes['8']['analysis'], '')
        self.assertNotIn('Never use this', json.dumps(categories))
        self.assertEqual(provenance['categories_sha256'], hashlib.sha256(self.output.read_bytes()).hexdigest())
        self.assertEqual(provenance['sources']['titles']['sha256'], hashlib.sha256(self.titles.read_bytes()).hexdigest())

    def test_bad_titles_never_create_either_output(self):
        for titles in ({'9': 'Root'}, {'9': 'Root', '8': 'Child', '7': 'Extra'},
                       {'9': 'Root', '8': ''}, {'9': 'Root', '8': {'label': 'Child', 'analysis': 4}}):
            with self.subTest(titles=titles):
                self.titles.write_text(json.dumps(titles))
                with self.assertRaisesRegex(ValueError, 'title'):
                    self.run_export()
                self.assertFalse(self.output.exists())
                self.assertFalse(self.projection.exists())

    def test_exclusive_outputs_do_not_replace_or_leave_partial_files(self):
        for output in (self.output, self.projection):
            with self.subTest(output=output.name):
                output.write_text('preserve me')
                with self.assertRaises(FileExistsError):
                    self.run_export()
                self.assertEqual(output.read_text(), 'preserve me')
                self.assertFalse(({self.output, self.projection} - {output}).pop().exists())
                output.unlink()
        with self.assertRaisesRegex(ValueError, 'distinct'):
            export(self.run, self.vector_map, self.notes, self.titles, self.output, self.output)
        self.assertFalse(self.output.exists())

    def test_rejects_changed_sources_evidence_and_saved_viewer(self):
        for path, mutate in [
            (self.notes, lambda blob: blob + b'\n'),
            (self.vector_map, lambda blob: blob + b'\n'),
            (self.run / 'evidence.json', lambda blob: blob.replace(b'original', b'changed')),
            (self.run / 'hierarchy.json', lambda blob: blob.replace(b'"N004"', b'"WRONG"')),
            (self.run / 'viewer.json', lambda blob: blob.replace(b'"root": 9', b'"root": 8')),
        ]:
            with self.subTest(path=path.name):
                original = path.read_bytes()
                path.write_bytes(mutate(original))
                with self.assertRaises(ValueError):
                    self.run_export()
                self.assertFalse(self.output.exists())
                self.assertFalse(self.projection.exists())
                path.write_bytes(original)

    def test_complete_memberships_are_reconstructed_at_every_retained_node(self):
        categories, provenance = self.run_export()
        nodes = {node['node_id']: node for node in categories['nodes']}

        def membership(node_id):
            node = nodes[node_id]
            result = set(node['note_ids'])
            for child in node['children']:
                result.update(membership(child))
            self.assertEqual(len(node['note_ids']), len(set(node['note_ids'])))
            return result

        for group in provenance['retained_groups']:
            with self.subTest(node=group['node_id']):
                self.assertEqual(membership(group['node_id']), set(group['note_ids']))
                self.assertEqual(group['note_ids_sha256'], hashlib.sha256(
                    '\n'.join(group['note_ids']).encode()).hexdigest())
        self.assertEqual(membership(categories['root_node_id']), {'N001', 'N002', 'N003', 'N004'})

    def test_cli_exports_both_files_from_explicit_paths(self):
        result = subprocess.run([
            sys.executable, str(Path(__file__).with_name('export_diffusion_categories.py')),
            str(self.run), '--vector-map', str(self.vector_map), '--notes', str(self.notes),
            '--titles', str(self.titles), '--output', str(self.output),
            '--projection-output', str(self.projection),
        ], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(self.output.read_text())['root_node_id'], '9')
        self.assertTrue(self.projection.is_file())


if __name__ == '__main__':
    unittest.main()
