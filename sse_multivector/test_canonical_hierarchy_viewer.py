"""Offline canonical viewer exports through the production experiment CLI."""
import hashlib
import json
import unittest

from sse_multivector import test_experiment as fixtures


class CanonicalHierarchyViewerTests(unittest.TestCase):
    setUp = fixtures.ExperimentTests.setUp
    write = fixtures.ExperimentTests.write
    cli = fixtures.ExperimentTests.cli

    def source(self):
        (self.root / 'trial').mkdir()
        corpus = self.write('notes.json', {'schema_version': 1, 'notes': [
            {'note_id': 'n1', 'text': 'First original\npost.', 'selection_rank': 1},
            {'note_id': 'unused', 'text': 'Unselected post.', 'selection_rank': 2},
            {'note_id': 'n3', 'text': 'Third original post. ', 'selection_rank': 3}]})
        nodes = [
            {'id': 'C001', 'subject': 'First heading', 'meaning': 'First fixed meaning',
             'parents': [], 'entries': [{'note_id': 'n1', 'number': '1'}]},
            {'id': 'C002', 'subject': 'Second heading', 'meaning': 'Second fixed meaning',
             'parents': [], 'entries': [{'note_id': 'n3', 'number': '1'}]},
            {'id': 'C003', 'subject': 'Shared heading', 'meaning': 'Shared fixed meaning',
             'parents': ['C001', 'C002'], 'entries': [
                 {'note_id': 'n1', 'number': '2'}, {'note_id': 'n1', 'number': '3'}]}]
        return self.write('trial/state.json', {'schema_version': 2, 'corpus': str(corpus),
            'roots': [{'note_id': 'n1', 'number': '1'}, {'note_id': 'n3', 'number': '1'}],
            'nodes': nodes, 'sources': {str(corpus): hashlib.sha256(corpus.read_bytes()).hexdigest()},
            'status': 'shaped_candidate', 'shape': {'roots': ['C002', 'C001'],
                'semantic_certified': False, 'group_task_coverage': 'unknown',
                'qualification': 'Retained meanings and supporting entries are unchanged.'}})

    def test_export_preserves_dag_memberships_meanings_and_original_text_without_inference(self):
        path = self.source()
        original = path.read_bytes()
        self.cli('export-canonical-viewer', 'trial', '--output', 'viewer')
        hierarchy = json.loads((self.root / 'viewer/hierarchy.json').read_text())
        notes_path = self.root / 'viewer/notes.json'
        notes = json.loads(notes_path.read_text())
        self.assertEqual(hierarchy['schema_version'], 2)
        self.assertEqual(hierarchy['hierarchy_id'], 'trial')
        self.assertEqual(hierarchy['source_sha256'], hashlib.sha256(notes_path.read_bytes()).hexdigest())
        self.assertEqual(hierarchy['notes'], [
            {'note_id': 'n1', 'note_short_id': 'N001'}, {'note_id': 'n3', 'note_short_id': 'N003'}])
        self.assertEqual(notes, {'notes': [
            {'note_id': 'n1', 'text': 'First original\npost.'},
            {'note_id': 'n3', 'text': 'Third original post. '}]})
        nodes = {node['node_id']: node for node in hierarchy['nodes']}
        self.assertEqual(set(nodes), {'VIEW_ROOT', 'C001', 'C002', 'C003'})
        self.assertEqual(nodes['VIEW_ROOT']['children'], ['C002', 'C001'])
        self.assertEqual(nodes['VIEW_ROOT']['note_ids'], [])
        self.assertIn('Display-only container', nodes['VIEW_ROOT']['analysis'])
        self.assertIn('shaped_candidate', nodes['VIEW_ROOT']['analysis'])
        self.assertIn('not human gold', nodes['VIEW_ROOT']['analysis'])
        self.assertEqual(nodes['C001']['children'], ['C003'])
        self.assertEqual(nodes['C002']['children'], ['C003'])
        self.assertEqual(nodes['C003']['note_ids'], ['N001'])
        self.assertEqual(nodes['C003']['label'], 'Shared heading (C003)')
        self.assertIn('Fixed meaning: Shared fixed meaning', nodes['C003']['analysis'])
        self.assertIn('Canonical parents: C001, C002', nodes['C003']['analysis'])
        self.assertEqual(path.read_bytes(), original)
        existing = {p.name: p.read_bytes() for p in (self.root / 'viewer').iterdir()}
        refused = self.cli('export-canonical-viewer', 'trial', '--output', 'viewer', ok=False)
        self.assertIn('viewer output must not exist', refused.stderr)
        self.assertEqual(existing, {p.name: p.read_bytes() for p in (self.root / 'viewer').iterdir()})
        (self.root / 'notes.json').write_text('Changed source')
        refused = self.cli('export-canonical-viewer', 'trial', '--output', 'changed', ok=False)
        self.assertIn('trial source changed', refused.stderr)
        self.assertFalse((self.root / 'changed').exists())
        self.assertEqual(fixtures.ExperimentTests.calls(self), [])

    def test_top_container_excludes_notes_outside_roots_and_preserves_node_notes(self):
        path = self.source()
        state = json.loads(path.read_text())
        state['direct_note_ids'] = ['unused', 'n1']
        path.write_text(json.dumps(state))
        original = path.read_bytes()

        self.cli('export-canonical-viewer', 'trial', '--output', 'viewer')

        view = json.loads((self.root / 'viewer/hierarchy.json').read_text())
        nodes = {node['node_id']: node for node in view['nodes']}
        self.assertEqual(nodes['VIEW_ROOT']['note_ids'], [])
        self.assertEqual(nodes['VIEW_ROOT']['children'], ['C002', 'C001'])
        self.assertEqual(nodes['C002']['note_ids'], ['N003'])
        self.assertEqual(nodes['C003']['note_ids'], ['N001'])
        self.assertEqual(view['notes'], [
            {'note_id': 'n1', 'note_short_id': 'N001'},
            {'note_id': 'n3', 'note_short_id': 'N003'}])
        self.assertEqual(json.loads((self.root / 'viewer/notes.json').read_text()), {
            'notes': [
                {'note_id': 'n1', 'text': 'First original\npost.'},
                {'note_id': 'n3', 'text': 'Third original post. '}]})
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual(fixtures.ExperimentTests.calls(self), [])

    def test_export_uses_the_finished_menu_and_preserves_the_raw_graph(self):
        from sse_multivector.canonical_hierarchy_shape import finish_nodes
        path = self.source()
        state = json.loads(path.read_text())
        state.pop('shape')
        state['note_ids'] = ['n1', 'n3']
        state['menu']={'nodes':finish_nodes(state['nodes'])}
        path.write_text(json.dumps(state))
        original = path.read_bytes()
        self.cli('export-canonical-viewer', 'trial', '--output', 'viewer')
        view = json.loads((self.root/'viewer/hierarchy.json').read_text())
        nodes = {n['node_id']: n for n in view['nodes']}
        self.assertEqual(set(nodes), {'VIEW_ROOT', 'C002', 'C003'})
        self.assertEqual(nodes['VIEW_ROOT']['children'], ['C002'])
        self.assertEqual(nodes['C003']['note_ids'], ['N001'])
        self.assertEqual(nodes['C003']['children'], [])
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual(fixtures.ExperimentTests.calls(self), [])

    def test_merged_collections_can_repeat_selection_ranks(self):
        path = self.source()
        state = json.loads(path.read_text())
        corpus = self.root / 'notes.json'
        value = json.loads(corpus.read_text())
        value['notes'][2]['selection_rank'] = 1
        corpus.write_text(json.dumps(value))
        state['sources'][str(corpus)] = hashlib.sha256(corpus.read_bytes()).hexdigest()
        path.write_text(json.dumps(state))
        before = path.read_bytes(), corpus.read_bytes()
        self.cli('export-canonical-viewer', 'trial', '--output', 'viewer')
        view = json.loads((self.root / 'viewer/hierarchy.json').read_text())
        self.assertEqual(view['notes'], [
            {'note_id': 'n1', 'note_short_id': 'N001'},
            {'note_id': 'n3', 'note_short_id': 'N003'}])
        self.assertEqual((path.read_bytes(), corpus.read_bytes()), before)
        self.assertEqual(fixtures.ExperimentTests.calls(self), [])

    def test_note_memberships_are_available_without_displaying_note_id_lists(self):
        path = self.source()
        original = path.read_bytes()
        self.cli('export-canonical-viewer', 'trial', '--output', 'viewer')
        view = json.loads((self.root / 'viewer/hierarchy.json').read_text())
        nodes = {node['node_id']: node for node in view['nodes']}
        self.assertEqual(nodes['C001']['label'], 'First heading (C001)')
        self.assertEqual(nodes['C003']['label'], 'Shared heading (C003)')
        for node in nodes.values():
            self.assertNotIn('N001', node['label'])
            self.assertNotIn('N003', node['label'])
            self.assertNotIn('Direct supporting notes:', node['analysis'])
        self.assertEqual(nodes['C001']['note_ids'], ['N001'])
        self.assertEqual(nodes['C003']['note_ids'], ['N001'])
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual(fixtures.ExperimentTests.calls(self), [])
