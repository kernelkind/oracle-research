"""Saved diffusion export preserves native groups and original source masks."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from export_diffusion_hierarchy import export


def digest(value):
    return hashlib.sha256(json.dumps(value).encode()).hexdigest()


def fixture():
    notes = {'notes': [
        {'note_id': 'a', 'text': 'café one two tail'},
        {'note_id': 'b', 'text': 'tea original'},
        {'note_id': 'c', 'text': 'stock original'},
        {'note_id': 'd', 'text': 'other original'},
    ]}
    vectors = {'vectors': []}
    for i, (note, short, span, fragment) in enumerate([
        ('a', 'N001', [0, 5], 'café'), ('a', 'N001', [6, 9], 'one'),
        ('b', 'N002', [0, 3], 'tea'), ('a', 'N001', [10, 13], 'two'),
        ('c', 'N003', [0, 5], 'stock'), ('d', 'N004', [0, 5], 'other'),
    ]):
        vectors['vectors'].append(dict(vector_id=f'v{i}', short_id=f'V{i}',
                                       note_id=note, note_short_id=short,
                                       byte_spans=[span], fragments=[fragment]))
    alias = dict(vectors['vectors'][2], vector_id='alias', short_id='VA')
    vectors['vectors'].append(alias)
    by_note = {note['note_id']: note['text'] for note in notes['notes']}
    evidence = []
    for i, vector in enumerate(vectors['vectors'][:6]):
        aliases = [vector, alias] if i == 2 else [vector]
        evidence.append(dict(row=i, canonical_id=vector['vector_id'],
                             aliases=[dict(v, text=by_note[v['note_id']],
                                           subject='Never use this as a group title')
                                      for v in aliases]))
    nodes = [dict(id=i, children=[], members=[i],
                  note_ids=[vectors['vectors'][i]['note_short_id']]) for i in range(6)]
    nodes.extend([
        dict(id=6, children=[1, 0], members=[0, 1], note_ids=['N001']),
        dict(id=7, children=[6, 2], members=[0, 1, 2], note_ids=['N001', 'N002']),
        dict(id=8, children=[3, 7], members=[0, 1, 2, 3], note_ids=['N001', 'N002']),
        dict(id=9, children=[5, 8, 4], members=list(range(6)),
             note_ids=['N001', 'N002', 'N003', 'N004']),
    ])
    hierarchy = dict(nodes=list(reversed(nodes)), roots=[9])
    configuration = dict(run_id='GDC09', method='diffusion', vector_count=6,
                         canonical_order_sha256=hashlib.sha256(
                             '\n'.join(f'v{i}' for i in range(6)).encode()).hexdigest(),
                         sources=dict(mapping=dict(path='vectors.json', sha256=digest(vectors)),
                                      notes=dict(path='notes.json', sha256=digest(notes))))
    return dict(hierarchy=hierarchy, configuration=configuration, evidence=evidence,
                vectors=vectors, notes=notes)


class DiffusionExportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.run = self.root / 'run'
        self.run.mkdir()
        self.vector_map = self.root / 'vectors.json'
        self.notes = self.root / 'notes.json'
        self.output = self.run / 'viewer.json'

    def save(self, values):
        for name in ('hierarchy', 'configuration', 'evidence'):
            (self.run / f'{name}.json').write_text(json.dumps(values[name]))
        self.vector_map.write_text(json.dumps(values['vectors']))
        self.notes.write_text(json.dumps(values['notes']))

    def run_export(self):
        export(self.run, self.vector_map, self.notes, self.output)
        return json.loads(self.output.read_text())

    def test_native_ids_edges_masks_and_equal_note_nodes_survive_without_source_writes(self):
        values = fixture()
        self.save(values)
        before = {p: p.read_bytes() for p in self.root.rglob('*.json')}
        result = self.run_export()
        self.assertEqual(result['schema_version'], 'containment-hierarchy-v1')
        self.assertEqual((result['run_id'], result['root'], result['vector_count']),
                         ('GDC09', 9, 6))
        groups = {group['id']: group for group in result['groups']}
        self.assertEqual(set(groups), {6, 7, 8, 9})
        for node in values['hierarchy']['nodes']:
            if node['children']:
                group = groups[node['id']]
                self.assertEqual(group['children'], [i for i in node['children'] if i >= 6])
                self.assertEqual(group['vector_ids'], node['members'])
        self.assertEqual(groups[6]['note_ids'], ['a'])
        self.assertEqual(groups[7]['note_ids'], groups[8]['note_ids'])
        self.assertEqual(groups[7]['parents'], [8])
        self.assertEqual(groups[9]['parents'], [])
        self.assertEqual(result['alias_groups'][2], ['v2', 'alias'])
        self.assertEqual(result['canonical_unique_ids'], [f'v{i}' for i in range(6)])
        self.assertEqual(result['sources']['vector_map']['sha256'], digest(values['vectors']))
        self.assertNotIn('subject', json.dumps(result))
        self.assertEqual(before, {p: p.read_bytes() for p in before})
        self.assertEqual(set(self.root.rglob('*.json')), set(before) | {self.output})

    def test_export_is_exclusive_and_never_replaces_existing_output(self):
        self.save(fixture())
        self.output.write_text('preserve me')
        with self.assertRaises(FileExistsError):
            self.run_export()
        self.assertEqual(self.output.read_text(), 'preserve me')

    def test_nonascending_internal_children_keep_the_saved_order(self):
        values = fixture()
        values['hierarchy']['nodes'].append(dict(
            id=10, children=[5, 4], members=[4, 5], note_ids=['N003', 'N004']))
        values['hierarchy']['nodes'][0]['children'] = [10, 8]
        self.save(values)
        groups = {group['id']: group for group in self.run_export()['groups']}
        self.assertEqual(groups[9]['children'], [10, 8])
        self.assertEqual(groups[10]['parents'], [9])

    def test_cli_uses_explicit_paths_and_saved_run_identity(self):
        self.save(fixture())
        result = subprocess.run([
            sys.executable, str(Path(__file__).with_name('export_diffusion_hierarchy.py')),
            str(self.run), '--vector-map', str(self.vector_map), '--notes', str(self.notes),
            '--output', str(self.output),
        ], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(self.output.read_text())['run_id'], 'GDC09')

    def test_rejects_changed_sources_even_when_masks_still_match(self):
        for source in (self.vector_map, self.notes):
            with self.subTest(source=source.name):
                self.save(fixture())
                source.write_bytes(source.read_bytes() + b'\n')
                with self.assertRaisesRegex(ValueError, 'checksum'):
                    self.run_export()
                self.assertFalse(self.output.exists())

    def test_rejects_bad_aliases_evidence_and_canonical_order(self):
        mutations = [
            ('canonical hash', lambda v: v['configuration'].update(canonical_order_sha256='bad')),
            ('duplicate row', lambda v: v['evidence'][1].update(row=0)),
            ('wrong canonical', lambda v: v['evidence'][0].update(canonical_id='v1')),
            ('duplicate alias', lambda v: v['evidence'][1]['aliases'].append(
                copy.deepcopy(v['evidence'][0]['aliases'][0]))),
            ('missing alias', lambda v: v['evidence'][2]['aliases'].pop()),
            ('changed text', lambda v: v['evidence'][0]['aliases'][0].update(text='wrong')),
            ('changed fragment', lambda v: v['evidence'][0]['aliases'][0].update(fragments=['wrong'])),
            ('changed spans', lambda v: v['evidence'][0]['aliases'][0].update(byte_spans=[[0, 4]])),
            ('changed short ID', lambda v: v['evidence'][0]['aliases'][0].update(short_id='WRONG')),
        ]
        for label, mutate in mutations:
            with self.subTest(label=label):
                values = fixture()
                mutate(values)
                self.save(values)
                with self.assertRaises(ValueError):
                    self.run_export()
                self.assertFalse(self.output.exists())

    def test_rejects_invalid_original_utf8_spans_even_when_evidence_agrees(self):
        values = fixture()
        values['vectors']['vectors'][0]['byte_spans'] = [[0, 4]]
        values['evidence'][0]['aliases'][0]['byte_spans'] = [[0, 4]]
        values['configuration']['sources']['mapping']['sha256'] = digest(values['vectors'])
        self.save(values)
        with self.assertRaisesRegex(ValueError, 'UTF-8'):
            self.run_export()
        self.assertFalse(self.output.exists())

    def test_rejects_invalid_native_trees_without_creating_output(self):
        mutations = [
            ('forest', lambda v: v['hierarchy'].update(roots=[8, 4, 5])),
            ('wrong method', lambda v: v['configuration'].update(method='fmc')),
            ('duplicate child', lambda v: v['hierarchy']['nodes'][0].update(children=[5, 8, 8, 4])),
            ('wrong membership', lambda v: v['hierarchy']['nodes'][1].update(members=[0, 1, 2])),
            ('wrong note membership', lambda v: v['hierarchy']['nodes'][1].update(note_ids=['N001'])),
            ('missing child', lambda v: v['hierarchy']['nodes'][0].update(children=[8, 999])),
            ('shared child', lambda v: v['hierarchy']['nodes'][1].update(children=[7, 2])),
            ('cycle', lambda v: v['hierarchy']['nodes'][1].update(children=[9, 3])),
            ('duplicate node', lambda v: v['hierarchy']['nodes'].append(
                copy.deepcopy(v['hierarchy']['nodes'][0]))),
        ]
        for label, mutate in mutations:
            with self.subTest(label=label):
                values = fixture()
                mutate(values)
                self.save(values)
                with self.assertRaises(ValueError):
                    self.run_export()
                self.assertFalse(self.output.exists())


if __name__ == '__main__':
    unittest.main()
