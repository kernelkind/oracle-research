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

    def test_legacy_audit_uses_root_selection_without_selecting_the_whole_corpus(self):
        path = self.source()
        state = json.loads(path.read_text())
        corpus_path = self.root/'notes.json'
        corpus = json.loads(corpus_path.read_text())
        for note in corpus['notes']:
            count = 3 if note['note_id'] == 'n1' else 1
            note['subjects'] = [dict(number=str(i)) for i in range(1, count+1)]
        corpus_path.write_text(json.dumps(corpus))
        state['sources'][str(corpus_path)] = hashlib.sha256(corpus_path.read_bytes()).hexdigest()
        path.write_text(json.dumps(state))
        original = path.read_bytes()
        self.cli('audit-canonical-trial', 'trial', '--output', 'legacy-audit.json')
        audited = json.loads((self.root/'legacy-audit.json').read_text())
        self.assertEqual(audited['note_coverage']['selected'], ['n1', 'n3'])
        self.assertEqual(audited['note_coverage']['selected_count'], 2)
        self.assertEqual(audited['note_coverage']['reachable_count'], 2)
        self.assertEqual(audited['note_coverage']['missing'], [])
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual(fixtures.ExperimentTests.calls(self), [])

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

    def admission_study(self):
        path=self.source()
        (self.root/'admissions').mkdir()
        state=json.loads(path.read_text())
        record=dict(id='L001',title='Additional heading',meaning='Additional fixed meaning.',
                    source_note_id='unused')
        state['originals']=[dict(id=record['id'],title=record['title'],meaning=record['meaning'],
                                local=dict(note_id='unused',number='1'))]
        path.write_text(json.dumps(state))
        plan=dict(as_version='ASv6.100',source_state=str(path),corpus=state['corpus'],
                  sources={str(path):hashlib.sha256(path.read_bytes()).hexdigest()},
                  records=[record],roots={'C001':{},'C002':{}})
        self.write('admissions/plan.json',plan)
        self.write('admissions/query-root-results.json',[
            dict(corpus='trial',root='trial:'+root,entry='L001',source_note_id='unused',
                 method=method,proposed=True,groups=['fused-001'])
            for root,method in [('C001','MM_note_bend'),('C002','MM_note_bend'),
                                ('C003','MM_coverage')]])
        self.seal_admission_study()
        return path

    def seal_admission_study(self):
        self.write('admissions/final-verification.json',dict(artifacts={
            f:hashlib.sha256((self.root/'admissions'/f).read_bytes()).hexdigest()
            for f in ['plan.json','query-root-results.json']}))

    def test_saved_admissions_preview_adds_only_root_notes_without_changing_sources(self):
        path=self.admission_study()
        original=path.read_bytes()
        self.cli('export-canonical-viewer','trial','--output','baseline')
        self.cli('export-canonical-viewer','trial','--output','preview',
                 '--root-admissions','admissions')
        baseline=json.loads((self.root/'baseline/hierarchy.json').read_text())
        view=json.loads((self.root/'preview/hierarchy.json').read_text())
        before={n['node_id']:n for n in baseline['nodes']}
        after={n['node_id']:n for n in view['nodes']}
        self.assertEqual(set(before),set(after))
        for key in before:
            self.assertEqual(before[key]['children'],after[key]['children'])
            if key!='VIEW_ROOT':self.assertEqual(before[key]['label'],after[key]['label'])
        self.assertEqual(after['VIEW_ROOT']['note_ids'],[])
        self.assertEqual(after['C001']['note_ids'],['N001','N002'])
        self.assertEqual(after['C002']['note_ids'],['N003','N002'])
        self.assertEqual(after['C003'],before['C003'])
        notes=json.loads((self.root/'preview/notes.json').read_text())['notes']
        self.assertEqual([r['note_id']for r in notes],['n1','unused','n3'])
        self.assertEqual(notes[1]['text'],'Unselected post.')
        self.assertEqual(view['source_sha256'],hashlib.sha256((self.root/'preview/notes.json').read_bytes()).hexdigest())
        proof=json.loads((self.root/'preview/root-admissions.json').read_text())
        self.assertEqual(proof['additional_notes'],1)
        self.assertEqual(proof['new_root_placements'],2)
        self.assertEqual(path.read_bytes(),original)
        self.assertEqual(fixtures.ExperimentTests.calls(self),[])

    def test_saved_admissions_preview_rejects_changed_results_before_writing(self):
        self.admission_study()
        (self.root/'admissions/query-root-results.json').write_text('[]')
        result=self.cli('export-canonical-viewer','trial','--output','preview',
                        '--root-admissions','admissions',ok=False)
        self.assertIn('admission source checksum mismatch',result.stderr)
        self.assertFalse((self.root/'preview').exists())
        self.assertEqual(fixtures.ExperimentTests.calls(self),[])

    def test_saved_admissions_preview_rejects_nonroot_or_changed_entry_evidence(self):
        self.admission_study()
        path=self.root/'admissions/query-root-results.json'
        original=path.read_bytes()
        for field,value,error in [('root','trial:C003','existing root'),
                                   ('source_note_id','n3','entry evidence')]:
            rows=json.loads(original)
            rows[0][field]=value
            path.write_text(json.dumps(rows));self.seal_admission_study()
            result=self.cli('export-canonical-viewer','trial','--output','preview',
                            '--root-admissions','admissions',ok=False)
            self.assertIn(error,result.stderr)
            self.assertFalse((self.root/'preview').exists())

    def verified_baseline(self):
        path=self.admission_study()
        history=self.root/'old-construction.txt';history.write_text('Frozen historical input')
        state=json.loads(path.read_text())
        state['sources'][str(history)]=hashlib.sha256(history.read_bytes()).hexdigest()
        path.write_text(json.dumps(state))
        plan=json.loads((self.root/'admissions/plan.json').read_text())
        plan['sources'][str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
        self.write('admissions/plan.json',plan);self.seal_admission_study()
        self.cli('export-canonical-viewer','trial','--output','baseline')
        self.write('baseline/provenance.json',dict(state=str(path),
            state_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),files={
                f:hashlib.sha256((self.root/'baseline'/f).read_bytes()).hexdigest()
                for f in ['hierarchy.json','notes.json']}))
        return path,history

    def test_preview_reuses_verified_snapshot_without_rechecking_old_construction(self):
        path,history=self.verified_baseline()
        history.write_text('Historical source no longer used by this preview')
        self.cli('export-canonical-viewer','trial','--output','preview',
                 '--root-admissions','admissions','--base-viewer','baseline')
        view=json.loads((self.root/'preview/hierarchy.json').read_text())
        self.assertEqual(len(view['notes']),3)
        self.assertEqual(fixtures.ExperimentTests.calls(self),[])
        refused=self.cli('export-canonical-viewer','trial','--output','full-export',ok=False)
        self.assertIn('trial source changed',refused.stderr)
        self.assertFalse((self.root/'full-export').exists())

    def test_verified_preview_rejects_changed_snapshot_or_corpus(self):
        self.verified_baseline()
        hierarchy=self.root/'baseline/hierarchy.json';original=hierarchy.read_bytes()
        hierarchy.write_text('{}')
        refused=self.cli('export-canonical-viewer','trial','--output','preview',
                         '--root-admissions','admissions','--base-viewer','baseline',ok=False)
        self.assertIn('verified viewer checksum mismatch',refused.stderr)
        self.assertFalse((self.root/'preview').exists())
        hierarchy.write_bytes(original)
        (self.root/'notes.json').write_text('{}')
        refused=self.cli('export-canonical-viewer','trial','--output','preview',
                         '--root-admissions','admissions','--base-viewer','baseline',ok=False)
        self.assertIn('verified viewer corpus changed',refused.stderr)
        self.assertFalse((self.root/'preview').exists())

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
