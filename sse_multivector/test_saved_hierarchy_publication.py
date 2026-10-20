"""Saved hierarchy evidence uses the existing historical export entry point."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import os
import subprocess
import sys


class SavedHierarchyPublicationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / 'source'
        self.output = self.root / 'publication'

    def write(self, name, value):
        path = self.source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = (json.dumps(value, ensure_ascii=False) + '\n').encode()
        path.write_bytes(raw)
        return {'path': name, 'sha256': hashlib.sha256(raw).hexdigest()}

    def fixture(self):
        posts = self.write('posts.json', {'notes': [
            {'note_id': 'post-a', 'text': 'Tea.'}, {'note_id': 'post-b', 'text': 'Sun.'}]})
        value = {'schema_version': 1, 'hierarchy_id': 'saved',
                 'source_sha256': posts['sha256'], 'root_node_id': 'root',
                 'notes': [{'note_id': 'post-a', 'note_short_id': 'N1'},
                           {'note_id': 'post-b', 'note_short_id': 'N2'}],
                 'nodes': [
                     {'node_id': 'root', 'label': 'Topics', 'analysis': '',
                      'children': ['b', 'a'], 'note_ids': ['N1', 'N2']},
                     {'node_id': 'a', 'label': 'Tea', 'analysis': 'Saved analysis.',
                      'children': [], 'note_ids': ['N1']},
                     {'node_id': 'b', 'label': 'Sun', 'analysis': '',
                      'children': [], 'note_ids': ['N2']}],
                 'note_masks': {'root': {'N1': [[0, 3]]}}}
        return {'profile': 'saved-hierarchy', 'kind': 'categories',
                'hierarchy': self.write('categories.json', value),
                'posts': posts,
                'reused_inputs': {'publication': 'historical-studies/known-inputs',
                                  'notes': 2}}

    def export(self, selection):
        from .historical_study_publication import export_results
        spec = self.root / 'selection.json'
        spec.write_text(json.dumps({'schema_version': 1, 'studies': {'saved': selection}}))
        return export_results(self.source, spec, 'saved', self.output)

    def rows(self, name):
        return [json.loads(line) for line in (self.output / name).read_text().splitlines()]

    def replace_hierarchy(self, selection, change):
        path = self.source / selection['hierarchy']['path']
        value = json.loads(path.read_text())
        change(value)
        selection['hierarchy'] = self.write(selection['hierarchy']['path'], value)

    def test_native_order_analysis_and_memberships_survive_unsigned_conversion(self):
        self.export(self.fixture())
        from .canonical_hierarchy_nostr import UNSIGNED_NAMESPACE
        import uuid
        local = lambda name: str(uuid.uuid5(UNSIGNED_NAMESPACE, name))
        rows = self.rows('results.jsonl')
        self.assertTrue(all(set(row) == {'kind', 'tags', 'content'} for row in rows))
        root = next(row for row in rows if ['d', local('root')] in row['tags'])
        self.assertEqual([tag[1] for tag in root['tags'] if tag[0] == 'child'],
                         [local('b'), local('a')])
        self.assertEqual(root['content'], '')
        tea = next(row for row in rows if ['d', local('a')] in row['tags'])
        self.assertEqual(tea['content'], 'Saved analysis.')
        original = next(row for row in self.rows('inputs.jsonl')
                        if row.get('source_node_id') == 'root')
        self.assertEqual(original['native_note_ids'], ['N1', 'N2'])
        self.assertEqual(self.rows('answers.jsonl'), [])
        self.assertEqual(self.rows('judgments.jsonl'), [])
        metadata = json.loads((self.output / 'experiment.json').read_text())
        self.assertIsNone(metadata['counts']['original_mask_ids'])

    def test_bad_edges_notes_and_mask_spans_fail_before_destination_changes(self):
        mutations = [
            (lambda value: value['nodes'][1]['children'].append('root'), 'navigation root|cycle'),
            (lambda value: value['nodes'][1]['children'].append('absent'), 'unknown child'),
            (lambda value: value['nodes'][1]['note_ids'].append('absent'), 'unknown source note'),
            (lambda value: value['note_masks']['root']['N1'].append([99, 100]), 'byte span')]
        for mutate, message in mutations:
            with self.subTest(message=message):
                selection = self.fixture()
                self.replace_hierarchy(selection, mutate)
                with self.assertRaisesRegex(ValueError, message):
                    self.export(selection)
                self.assertFalse(self.output.exists())

    def test_source_snapshot_refresh_and_selected_parameters(self):
        selection = self.fixture()
        parameter = self.write('preparation.json', {'policy': {'k': 5, 'passes': 1},
            'cache': {'large': 'NOT-A-FINAL-RESULT'}, 'api_key': 'PRIVATE-KEY',
            'path': '/home/private/account/auth.json'})
        selection['parameters'] = [dict(parameter, fields=['policy'])]
        originals = {p: (p.read_bytes(), p.stat().st_mtime_ns)
                     for p in self.source.iterdir()}
        self.export(selection)
        metadata = json.loads((self.output / 'experiment.json').read_text())
        self.assertEqual(metadata['parameters']['preparation.json'], {'policy': {'k': 5, 'passes': 1}})
        snapshot = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.output.iterdir()}
        self.export(selection)
        self.assertEqual(snapshot, {p: (p.read_bytes(), p.stat().st_mtime_ns)
                                    for p in self.output.iterdir()})
        self.assertEqual(originals, {p: (p.read_bytes(), p.stat().st_mtime_ns)
                                     for p in self.source.iterdir()})

    def infomap_fixture(self):
        mapping = self.write('vectors.json', {'vectors': [
            {'vector_id': 'a', 'note_id': 'post-a'},
            {'vector_id': 'b', 'note_id': 'post-b'},
            {'vector_id': 'b-alias', 'note_id': 'post-b'}]})
        sources = {'vector_map': {'path': '/home/private/old/vector-map.json', 'sha256': mapping['sha256']}}
        value = {'schema_version': 'infomap-hierarchy-v1', 'run_id': 'I-test',
                 'sources': sources, 'vector_count': 2, 'canonical_unique_ids': ['a', 'b'],
                 'alias_groups': [['a'], ['b', 'b-alias']], 'root': 2,
                 'paths': [{'node_id': i, 'module_path': [1], 'native_path': [1, i + 1],
                            'flow': 0 if i == 0 else .5} for i in range(2)],
                 'modules': [
                     {'id': 2, 'module_path': [], 'parent': None, 'children': [3],
                      'direct_vectors': [], 'vector_ids': [0, 1], 'note_ids': ['post-a', 'post-b']},
                     {'id': 3, 'module_path': [1], 'parent': 2, 'children': [],
                      'direct_vectors': [0, 1], 'vector_ids': [0, 1], 'note_ids': ['post-a', 'post-b']}],
                 'summary': {'notes': 2, 'codelength': 0, 'trial_codelengths': [0, .4]},
                 'excluded_same_note_edges': 1}
        return {'profile': 'saved-hierarchy', 'kind': 'infomap',
                'hierarchy': self.write('infomap.json', value),
                'vector_map': mapping,
                'configuration': self.write('configuration.json', {'run_id': 'I-test',
                    'sources': sources, 'infomap': {'seed': 123, 'num_trials': 10},
                    'environment': {'python': 'saved-version', 'threads': 1}, 'api_key': 'PRIVATE-KEY'})}

    def test_native_infomap_values_aliases_and_runtime_without_invented_titles(self):
        self.export(self.infomap_fixture())
        row = self.rows('results.jsonl')[0]
        self.assertEqual(row['data']['paths'][0]['flow'], 0)
        self.assertEqual(row['data']['summary']['trial_codelengths'], [0, .4])
        self.assertEqual(row['data']['alias_groups'], [['a'], ['b', 'b-alias']])
        self.assertNotIn('label', row['data']['modules'][0])
        metadata = json.loads((self.output / 'experiment.json').read_text())
        self.assertEqual(metadata['parameters']['environment']['threads'], 1)
        self.assertIsNone(metadata['subject_provenance']['generated_subjects_deprecated'])
        public = ''.join(p.read_text() for p in self.output.iterdir())
        self.assertNotIn('PRIVATE-KEY', public)
        self.assertNotIn('/home/private/', public)

    def test_infomap_note_and_native_path_joins_fail_closed(self):
        for mutate, message in [
            (lambda value: value['modules'][1]['note_ids'].remove('post-a'), 'note membership'),
            (lambda value: value['paths'][0].update(native_path=[9, 1]), 'native/module path')]:
            selection = self.infomap_fixture()
            self.replace_hierarchy(selection, mutate)
            with self.assertRaisesRegex(ValueError, message):
                self.export(selection)
            self.assertFalse(self.output.exists())

    def test_infomap_source_hash_and_alias_partition_are_verified(self):
        for mutate, message in [
            (lambda value: value['sources']['vector_map'].update(sha256='0' * 64), 'selected vector source'),
            (lambda value: value['alias_groups'][0].append('b'), 'alias partition')]:
            selection = self.infomap_fixture()
            self.replace_hierarchy(selection, mutate)
            if message == 'selected vector source':
                configuration = json.loads((self.source / 'configuration.json').read_text())
                configuration['sources']['vector_map']['sha256'] = '0' * 64
                selection['configuration'] = self.write('configuration.json', configuration)
            with self.assertRaisesRegex(ValueError, message):
                self.export(selection)
            self.assertFalse(self.output.exists())

    def test_reference_fixture_is_exact_input_and_has_no_algorithm_results(self):
        fixture = {'schema_version': 1, 'hierarchy_id': 'manual', 'root_node_id': 'root',
                   'construction': {'automated': False, 'claim': 'A reference, not an algorithm.'},
                   'nodes': [{'node_id': 'root', 'children': [], 'label': 'Reference'}]}
        self.export({'profile': 'saved-hierarchy', 'kind': 'reference',
                     'hierarchy': self.write('reference.json', fixture)})
        self.assertEqual(self.rows('inputs.jsonl'), [{'type': 'reference_fixture', 'data': fixture}])
        self.assertEqual(self.rows('results.jsonl'), [])
        metadata = json.loads((self.output / 'experiment.json').read_text())
        self.assertEqual(metadata['scientific_role'], 'reference input')
        self.assertIsNone(metadata['counts']['notes'])

    def test_cyclic_true_graph_is_retained_without_unsigned_dag_conversion(self):
        selection = self.true_fixture()
        self.export(selection)
        self.assertEqual(self.rows('answers.jsonl'), [])
        graphs = [row for row in self.rows('results.jsonl') if row['type'].endswith('true_graph')]
        self.assertEqual(len(graphs), 2)
        self.assertEqual(graphs[0]['data']['cycle_components'], [['A', 'B']])
        self.assertEqual(graphs[0]['data']['roots'], [])
        self.assertEqual(graphs[0]['data']['transitive_reduced_edges'], None)
        self.assertEqual(graphs[0]['data']['raw_edges'][1]['score_origin']['reused'], True)
        self.assertEqual(graphs[0]['data']['raw_edges'][0]['score_ref']['publication'], 'numerical/prior')
        self.assertEqual(json.loads((self.output / 'experiment.json').read_text())['counts']['raw_directions'], 2)
        data = ''.join(path.read_text() for path in self.output.iterdir())
        self.assertNotIn('EXPANDED-REQUEST', data)
        self.assertNotIn('PRIVATE-KEY', data)
        self.assertNotIn('"token_ids"', data)

    def true_fixture(self):
        science = {'generated_text': '1', 'generated_token_ids': [0, 209, 1],
            'eos_terminated': True, 'predicted': True, 'entailment_score': .7,
            'threshold_predicted': True, 'logit_0_first_token': 0,
            'logit_1_first_token': 1, 'probability_0_first_token': .2,
            'first_token_binary_score': .8, 'first_token_binary_label': 1,
            'label_prefix_probability_mass': .9, 'argmax_token_id': 209}
        rows = [dict(science, id=a+'-'+b, a_id=a, b_id=b, a=a, b=b,
            model_input='EXPANDED-REQUEST', token_ids=[100, 200],
            score_origin={'source': 'prior/scores.jsonl', 'row_index': i,
                          'row_id': a+'-'+b, 'reused': bool(i)})
            for i, (a, b) in enumerate([('A', 'B'), ('B', 'A')])]
        payload = self.write('published.jsonl', rows[0])
        path = self.source / 'published.jsonl'
        path.write_text(''.join(json.dumps({k: v for k, v in row.items()
                                           if k not in ('score_origin', 'model_input', 'token_ids')})+'\n'
                                for row in rows))
        payload['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        graph = {'threshold': .142, 'nodes': [{'group': 'A', 'title': 'A'}, {'group': 'B', 'title': 'B'}],
                 'raw_edges': rows, 'roots': [], 'cycle_components': [['A', 'B']],
                 'transitive_reduced_edges': None, 'stats': {'nodes': 2, 'raw_edges': 2,
                     'cycle_components': 1, 'scored_ordered_pairs': 2}}
        raw = self.write('raw-graph.json', graph)
        derived = self.write('graph.json', graph)
        score_table = self.write('scores.json', rows)
        code = self.write('source.py', 'Frozen source bytes.')
        canonical = self.write('canonical.json', {'titles': {'groups': graph['nodes'], 'status': 'saved'},
            'scores': rows, 'consolidations': [], 'source_packets': {'packets': [
                {'packet': 'A', 'instances': [{'note_id': 'post-a', 'text': 'éTea',
                    'byte_spans': [[2, 5]], 'instance': 'V1', 'fragments': ['Tea']}]}]}})
        memberships = self.write('notes.json', {'nodes': [{'group': 'A', 'own_note_ids': ['post-a']}],
            'stats': {'nodes': 1, 'unique_note_count': 1}})
        raw_completion = self.write('raw-completion.json', {
            'scores_sha256': score_table['sha256'], 'graph_sha256': raw['sha256'],
            'graph_code_sha256': code['sha256'], 'stats': graph['stats']})
        final = self.write('completion.json', {'files': {binding['path']: binding['sha256']
            for binding in (derived, memberships, canonical)}, 'raw_stats': graph['stats'],
            'canonical_stats': graph['stats'], 'note_stats': {'nodes': 1, 'unique_note_count': 1}})
        config = {'model_id': 'saved/TRUE', 'revision': 'saved-revision', 'threshold': .142,
                  'seed': 0, 'api_key': 'PRIVATE-KEY'}
        return {'profile': 'saved-hierarchy', 'kind': 'true-graph', 'hierarchy': raw,
            'score_table': score_table, 'derived_graph': derived, 'canonical': canonical,
            'memberships': memberships, 'raw_completion': raw_completion,
            'derived_completion': final, 'configuration': self.write('config.json', config),
            'plan': self.write('plan.json', config), 'graph_code': code,
            'published_scores': [{'source': 'prior/scores.jsonl', 'publication': 'numerical/prior',
                                  'payload': payload}]}

    def test_true_score_and_completion_bindings_fail_before_writing(self):
        for field, filename, mutate, message in [
            ('raw_completion', 'raw-completion.json', lambda value: value.update(graph_sha256='0'*64),
             'raw completion'),
            ('score_table', 'scores.json', lambda value: value[0].update(entailment_score=.8),
             'published scientific output')]:
            selection = self.true_fixture()
            value = json.loads((self.source / filename).read_text())
            mutate(value)
            selection[field] = self.write(filename, value)
            with self.assertRaisesRegex(ValueError, message):
                self.export(selection)
            self.assertFalse(self.output.exists())

    def test_existing_project_cli_exports_selected_saved_hierarchy(self):
        selection = self.fixture()
        spec = self.root / 'selection.json'
        spec.write_text(json.dumps({'schema_version': 1, 'studies': {'saved': selection}}))
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
        result = subprocess.run([sys.executable, 'sse_multivector/experiment.py',
            'export-evaluation-results', str(self.source), '--kind', 'prompt-study',
            '--spec', str(spec), '--study', 'saved', '--output', str(self.output)],
            cwd=Path(__file__).resolve().parents[1], env=environment,
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(self.rows('results.jsonl')), 4)


if __name__ == '__main__':
    unittest.main()
