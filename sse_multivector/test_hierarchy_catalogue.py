"""Exercise saved hierarchy discovery through the production shared launcher."""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import unittest


class HierarchyCatalogue(unittest.TestCase):
    def fixture(self, root):
        checkout = root / 'original'
        artifact = checkout / 'target' / 'saved-run' / 'state.json'
        artifact.parent.mkdir(parents=True)
        payload = {
            'schema_version': 2, 'corpus': '/saved/subjects.json',
            'roots': [{'note_id': 'N001', 'number': '1'}],
            'index': 1, 'status': 'complete', 'steps': [],
            'nodes': [{'id': 'C001', 'meaning': 'Original meaning',
                       'parents': [], 'entries': [{'note_id': 'N001', 'number': '1'}]}],
            'sources': {}, 'independent_meanings': True,
            'bootstrap_spec': {'prompt': {'id': 'Bootstrap-v104', 'path': '/saved/B104.md'},
                               'runner': {'model': 'saved-model', 'reasoning_effort': 'medium'}},
        }
        artifact.write_text(json.dumps(payload))
        source = root / 'source.json'
        source.write_text(json.dumps({'schema_version': 1, 'roots': [str(checkout), str(root / 'clone')]}))
        return artifact, payload, source

    def run_catalogue(self, root, source, extra=()):
        project = Path(__file__).resolve().parent.parent
        launcher = project.parent / 'experiment-runner' / 'bin' / 'experiment-runner'
        result = subprocess.run([str(launcher), '--project-root', str(project),
                                 'catalogue-hierarchies', '--source', str(source),
                                 '--registry', str(root / 'versions.json'),
                                 '--output', str(root / 'catalogue'), *extra], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads((root / 'catalogue/catalogue.json').read_text())
        self.assertEqual(data['discovery_errors'], [])
        return data

    def test_cli_assigns_stable_versions_and_preserves_source_outputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact, _, source = self.fixture(root)
            original = artifact.read_bytes()
            clone = root / 'clone/target/saved-run/state.json'
            clone.parent.mkdir(parents=True)
            clone.write_bytes(original)
            row, = self.run_catalogue(root, source)['hierarchies']
            self.assertEqual(row['version_id'], 'H0001')
            self.assertEqual(row['sha256'], hashlib.sha256(original).hexdigest())
            self.assertEqual(len(row['locations']), 2)
            self.assertEqual(row['parameters']['bootstrap_spec']['runner']['model'], 'saved-model')
            self.assertTrue(row['unknown'])
            updated, = self.run_catalogue(root, source)['hierarchies']
            self.assertEqual(updated['version_id'], 'H0001')
            self.assertEqual(artifact.read_bytes(), original)
            self.assertIn('H0001', (root / 'catalogue/index.html').read_text())
            rebuilt, = self.run_catalogue(root, source, ['--saved-only'])['hierarchies']
            self.assertEqual(rebuilt['version_id'], 'H0001')
            self.assertEqual(rebuilt['locations'], updated['locations'])

    def test_cutoff_uses_owned_execution_time_and_collects_step_settings(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact, payload, source = self.fixture(root)
            spec = json.loads(source.read_text())
            spec.update(generated_since='2026-10-08T00:00:00-04:00', areas=['target'],
                        exclude=['**/sse_multivector/**'])
            source.write_text(json.dumps(spec))
            for name, started in [('saved-run', '2026-10-08T04:00:00+00:00'),
                                  ('old-run', '2026-10-08T03:59:59+00:00')]:
                state = artifact.parent.parent / name / 'state.json'
                experiment = state.parent / 'step-000/experiment'
                experiment.mkdir(parents=True)
                settings = {'started_at_utc': started, 'concurrency': 4,
                            'prepared_concurrency': 4, 'warm_cache': True}
                (experiment / 'execution-settings.jsonl').write_text(json.dumps(settings) + '\n')
                (experiment / 'report.json').write_text(json.dumps({'execution_settings': [settings]}))
                (experiment / 'runner-config.json').write_text(json.dumps({'model': 'step-model'}))
                state.write_text(json.dumps({**payload, 'steps': [
                    {'index': 0, 'experiment': str(experiment), 'status': 'added',
                     'before': [{'meaning': 'large saved graph body'}]}]}))
            # A recently copied source snapshot is not a new hierarchy.
            copied = artifact.parent.parent / 'source-snapshot/sse_multivector/state.json'
            copied.parent.mkdir(parents=True)
            copied.write_bytes(artifact.read_bytes())
            data = self.run_catalogue(root, source)
            row, = data['hierarchies']
            self.assertEqual(row['name'], 'saved-run')
            self.assertEqual(row['generation_time']['basis'], 'saved execution start')
            self.assertEqual(row['generation_time']['timestamp'], '2026-10-08T04:00:00+00:00')
            self.assertNotIn('before', row['parameters']['steps'][0])
            saved = [data['parameter_evidence'][e['sha256']] for e in row['evidence']]
            self.assertTrue(any(d.get('model') == 'step-model' for d in saved))
            self.assertTrue(any(d.get('execution_settings', [{}])[0].get('concurrency') == 4 for d in saved))

    def test_cutoff_labels_mechanical_output_mtime_and_honors_saved_timestamp(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact, payload, source = self.fixture(root)
            spec = json.loads(source.read_text())
            spec['generated_since'] = '2026-10-08T00:00:00-04:00'
            source.write_text(json.dumps(spec))
            artifact.write_text(json.dumps({**payload, 'generated_at': '2026-10-07T20:00:00-04:00'}))
            self.assertEqual(self.run_catalogue(root, source)['hierarchies'], [])
            artifact.write_text(json.dumps(payload))
            os.utime(artifact, (1791475200, 1791475200))
            row, = self.run_catalogue(root, source)['hierarchies']
            self.assertEqual(row['generation_time']['basis'], 'file modification time (unverified)')

    def test_graph_search_phase_settings_remain_bound_to_the_checkpoint(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact, payload, source = self.fixture(root)
            experiment = artifact.parent / 'step-001/graph-search-000/experiment'
            experiment.mkdir(parents=True)
            started = '2026-10-09T12:00:00+00:00'
            (experiment / 'execution-settings.jsonl').write_text(json.dumps({'started_at_utc': started}) + '\n')
            (experiment / 'runner-config.json').write_text(json.dumps({'model': 'graph-search-model'}))
            receipt = {'results_path': str(experiment / 'results.jsonl'), 'record_sha256': 'a' * 64}
            payload['graph_search_steps'] = {'1': {
                'binding': {'meaning': {'experiment': str(experiment), 'case': 'C001', 'receipt': receipt}},
                'phases': [{'experiment': str(experiment), 'answers': ['discard response body']}],
            }}
            artifact.write_text(json.dumps(payload))
            data = self.run_catalogue(root, source)
            row, = data['hierarchies']
            self.assertEqual(row['generation_time']['timestamp'], started)
            self.assertEqual(row['parameters']['graph_search_steps']['1']['binding']['meaning']['receipt'], receipt)
            self.assertTrue(any(data['parameter_evidence'][e['sha256']].get('model') == 'graph-search-model'
                                for e in row['evidence']))

    def test_selection_ranking_bodies_are_not_experimental_parameters(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact, payload, source = self.fixture(root)
            selection = artifact.with_name('selection.json')
            selection.write_text(json.dumps({'candidate_selection': {'top_k': 16, 'method': 'saved-method'},
                                              'ranking': [{'method': 'saved-ranking', 'scores': {'N001': 0.9},
                                                           'text_scores': {'N001': 0.8}, 'sse_scores': {'N001': 0.7},
                                                           'subject_vectors': {'dimensions': 768, 'note_batch_size': 8},
                                                           'ancestor_query_policy': {'top_k': 16}}],
                                              'row_count': 1, 'rows': [{'selected_token_ids': [1, 2, 3]}],
                                              'selected': {'note_id': 'N001', 'number': '1'}}))
            payload['selection_report'] = str(selection)
            artifact.write_text(json.dumps(payload))
            data = self.run_catalogue(root, source)
            row, = data['hierarchies']
            document = data['parameter_evidence'][row['evidence'][0]['sha256']]
            self.assertEqual(document['ranking'], [{'method': 'saved-ranking',
                             'subject_vectors': {'dimensions': 768, 'note_batch_size': 8},
                             'ancestor_query_policy': {'top_k': 16}}])
            self.assertNotIn('rows', document)
            self.assertEqual(document['row_count'], 1)
            self.assertEqual(document['candidate_selection']['top_k'], 16)
            self.assertEqual(document['selected'], {'note_id': 'N001', 'number': '1'})

    def test_independent_saved_runs_are_distinct_and_empty_preparation_is_excluded(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact, payload, source = self.fixture(root)
            other = artifact.parent.parent / 'independent-run/state.json'
            other.parent.mkdir()
            other.write_bytes(artifact.read_bytes())
            prepared = artifact.parent.parent / 'only-prepared/state.json'
            prepared.parent.mkdir()
            prepared.write_text(json.dumps({**payload, 'nodes': [], 'status': 'prepared'}))
            rows = self.run_catalogue(root, source)['hierarchies']
            self.assertEqual(len(rows), 2)
            self.assertEqual(len({r['version_id'] for r in rows}), 2)
            self.assertEqual(rows[0]['same_output_versions'], [rows[1]['version_id']])

    def test_changed_output_gets_new_id_and_old_output_is_retained(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact, payload, source = self.fixture(root)
            original = artifact.read_bytes()
            self.run_catalogue(root, source)
            payload['nodes'][0]['meaning'] = 'Revised meaning'
            artifact.write_text(json.dumps(payload))
            old, new = self.run_catalogue(root, source)['hierarchies']
            self.assertEqual([old['version_id'], new['version_id']], ['H0001', 'H0002'])
            self.assertFalse(old['currently_discovered'])
            self.assertEqual((root / 'catalogue' / old['output']).read_bytes(), original)
            self.assertTrue(new['currently_discovered'])

    def test_saved_settings_and_changed_frozen_sources_are_visible_in_one_catalogue(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact, payload, source = self.fixture(root)
            config = artifact.parent / 'configuration.json'
            config.write_text(json.dumps({'runner': {'model': 'historical-model', 'concurrency': 4},
                                          'seed': 123, 'api_key': 'must-not-appear'}))
            payload['sources'] = {str(config): '0' * 64, '/missing/configuration.json': '1' * 64}
            artifact.write_text(json.dumps(payload))
            data = self.run_catalogue(root, source)
            row, = data['hierarchies']
            evidence = data['parameter_evidence'][row['evidence'][0]['sha256']]
            self.assertEqual(evidence['runner']['concurrency'], 4)
            self.assertEqual(evidence['seed'], 123)
            self.assertEqual(row['bindings'][str(config)]['status'], 'changed')
            self.assertEqual(row['bindings']['/missing/configuration.json']['status'], 'missing')
            self.assertNotIn('must-not-appear', (root / 'catalogue/index.html').read_text())
            self.assertNotIn('historical-model', (root / 'catalogue/index.html').read_text())
            self.assertEqual(evidence['runner']['model'], 'historical-model')

    def test_sqlite_snapshot_includes_committed_wal_rows(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact, _, source = self.fixture(root)
            artifact.unlink()
            database = artifact.with_name('graph.sqlite')
            with sqlite3.connect(database) as connection:
                connection.execute('PRAGMA journal_mode=WAL')
                connection.execute('CREATE TABLE entries(id INTEGER,payload TEXT)')
                connection.execute('CREATE TABLE owners(id INTEGER,parent INTEGER)')
                connection.execute('CREATE TABLE edges(a INTEGER,b INTEGER)')
                connection.execute("INSERT INTO entries VALUES(1,'{}')")
                connection.execute('INSERT INTO owners VALUES(1,1)')
                connection.commit()
                self.assertTrue(database.with_name('graph.sqlite-wal').stat().st_size)
                row, = self.run_catalogue(root, source)['hierarchies']
                self.assertEqual(row['parameters']['sqlite_counts']['entries'], 1)
                snapshot = root / 'catalogue' / row['output']
                with sqlite3.connect(snapshot) as saved:
                    self.assertEqual(saved.execute('SELECT COUNT(*) FROM entries').fetchone()[0], 1)
                repeated, = self.run_catalogue(root, source)['hierarchies']
                self.assertEqual(row['version_id'], repeated['version_id'])

    def test_defaults_come_from_verified_archived_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact, _, source = self.fixture(root)
            archived = artifact.with_name('geometric_haus.py')
            archived.write_text('def fit_affinity(x, seed=1234, max_depth=9):\n'
                                '    return KMeans(n_init=10, random_state=seed)\n')
            config = artifact.with_name('configuration.json')
            config.write_text(json.dumps({'method': 'haus', 'config': {'seed': 42},
                                         'code': {'geometric_haus.py': hashlib.sha256(archived.read_bytes()).hexdigest()}}))
            row, = self.run_catalogue(root, source)['hierarchies']
            defaults = row['parameters']['archived_method_defaults']
            self.assertEqual(defaults['signature_defaults']['seed'], 1234)
            self.assertEqual(defaults['overrides']['seed'], 42)
            self.assertEqual(defaults['fixed_calls'][0]['settings']['n_init'], 10)
            archived.write_text(archived.read_text().replace('1234', '9999'))
            row, = self.run_catalogue(root, source)['hierarchies']
            self.assertEqual(row['parameters']['archived_method_defaults']['signature_defaults']['seed'], 1234)

    def test_frozen_parameter_evidence_survives_later_source_edits(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact, payload, source = self.fixture(root)
            config = root / 'old-experiment/runner-config.json'
            config.parent.mkdir()
            config.write_text(json.dumps({'model': 'original-model'}))
            payload['sources'] = {str(config): hashlib.sha256(config.read_bytes()).hexdigest()}
            artifact.write_text(json.dumps(payload))
            row, = self.run_catalogue(root, source)['hierarchies']
            original_sha = row['evidence'][0]['sha256']
            config.write_text(json.dumps({'model': 'later-edit'}))
            data = self.run_catalogue(root, source)
            row, = data['hierarchies']
            self.assertEqual(row['version_id'], 'H0001')
            self.assertEqual(row['evidence'][0]['sha256'], original_sha)
            self.assertEqual(data['parameter_evidence'][original_sha]['model'], 'original-model')
            self.assertEqual(row['bindings'][str(config)]['status'], 'changed')

    def test_exact_generator_code_is_preserved_separately_from_current_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact, payload, source = self.fixture(root)
            code = root / 'old-experiment/generator.py'
            code.parent.mkdir()
            original = b'def generate():\n    return "original policy"\n'
            code.write_bytes(original)
            payload['sources'] = {str(code): hashlib.sha256(original).hexdigest()}
            artifact.write_text(json.dumps(payload))
            row, = self.run_catalogue(root, source)['hierarchies']
            generator, = row['generator_code']['files']
            self.assertEqual((root / 'catalogue' / generator['snapshot']).read_bytes(), original)
            self.assertEqual(row['generator_code']['commit_status'], 'unknown: not recorded')
            code.write_text('def generate():\n    return "new policy"\n')
            row, = self.run_catalogue(root, source)['hierarchies']
            generator, = row['generator_code']['files']
            self.assertEqual(generator['status'], 'preserved')
            self.assertEqual((root / 'catalogue' / generator['snapshot']).read_bytes(), original)

    def test_generator_code_can_be_recovered_from_git_without_inventing_a_run_commit(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact, payload, source = self.fixture(root)
            checkout = root / 'original'
            code = checkout / 'generator.py'
            original = b'def generate():\n    return "saved policy"\n'
            code.write_bytes(original)
            subprocess.run(['git', 'init', '-q', str(checkout)], check=True)
            subprocess.run(['git', '-C', str(checkout), 'add', 'generator.py'], check=True)
            message = root / 'commit-message.txt'
            message.write_text('Save original generator\n')
            subprocess.run(['git', '-C', str(checkout), '-c', 'user.name=Catalogue test',
                            '-c', 'user.email=catalogue@example.invalid', 'commit', '-q', '-F', str(message)], check=True)
            code.write_text('def generate():\n    return "later policy"\n')
            payload['sources'] = {str(code): hashlib.sha256(original).hexdigest()}
            artifact.write_text(json.dumps(payload))
            row, = self.run_catalogue(root, source)['hierarchies']
            generator, = row['generator_code']['files']
            self.assertIn('git_blob', generator['recovered_from'])
            self.assertEqual((root / 'catalogue' / generator['snapshot']).read_bytes(), original)
            self.assertEqual(row['generator_code']['commit_status'], 'unknown: not recorded')


    def test_basename_code_hash_recovers_project_and_shared_runner_git_sources(self):
        for source_directory in ('sse_multivector', 'experiment_runner'):
            with self.subTest(source_directory=source_directory), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                artifact, payload, source = self.fixture(root)
                repository = root / ('original' if source_directory == 'sse_multivector' else 'experiment-runner')
                code = repository / source_directory / 'saved_generator.py'
                code.parent.mkdir(parents=True)
                original = b'def generate():\n    return "original hierarchy"\n'
                code.write_bytes(original)
                subprocess.run(['git', 'init', '-q', str(repository)], check=True)
                subprocess.run(['git', '-C', str(repository), 'add', str(code.relative_to(repository))], check=True)
                message = root / 'commit-message.txt'
                message.write_text('Save original generator\n')
                subprocess.run(['git', '-C', str(repository), '-c', 'user.name=Catalogue test',
                                '-c', 'user.email=catalogue@example.invalid', 'commit', '-q', '-F', str(message)], check=True)
                code.write_text('def generate():\n    return "later hierarchy"\n')
                payload['code'] = {code.name: hashlib.sha256(original).hexdigest()}
                artifact.write_text(json.dumps(payload))
                row, = self.run_catalogue(root, source)['hierarchies']
                generator, = row['generator_code']['files']
                self.assertEqual(generator['status'], 'preserved')
                self.assertEqual((root / 'catalogue' / generator['snapshot']).read_bytes(), original)
                self.assertEqual(generator['recovered_from']['repository'], str(repository))
                self.assertIn('git_blob', generator['recovered_from'])
                self.assertEqual(row['generator_code']['commit_status'], 'unknown: not recorded')


    def test_page_loads_complete_parameters_from_local_assets_without_embedding_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact, _, source = self.fixture(root)
            complete_value = 'FULL_PARAMETER_VALUE_' + 'x' * 250000 + '</script>&'
            config = artifact.with_name('configuration.json')
            config.write_text(json.dumps({'model': 'large-evidence-model', 'seed': 731,
                                         'calibration_detail': complete_value}))
            data = self.run_catalogue(root, source)
            row, = data['hierarchies']
            index = root / 'catalogue/index.html'
            self.assertLess(index.stat().st_size, 30000)
            page = index.read_text()
            self.assertNotIn('FULL_PARAMETER_VALUE_', page)
            self.assertIn('large-evidence-model', page)
            self.assertIn('731', page)
            record_asset = root / 'catalogue/records' / (row['version_id'] + '.js')
            evidence_asset = root / 'catalogue/evidence' / (row['evidence'][0]['sha256'] + '.js')
            for asset, identifier, expected in (
                    (record_asset, row['version_id'], row),
                    (evidence_asset, row['evidence'][0]['sha256'],
                     data['parameter_evidence'][row['evidence'][0]['sha256']])):
                script = asset.read_text()
                arguments = json.loads('[' + script.split('(', 1)[1].rsplit(')', 1)[0] + ']')
                self.assertEqual(arguments, [identifier, expected])
                self.assertNotIn('</script>', script)
            self.assertEqual(json.loads(evidence_asset.with_suffix('.json').read_text())['calibration_detail'], complete_value)

    def test_changed_source_metadata_does_not_establish_generator_code(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact, payload, source = self.fixture(root)
            code = root / 'later-generator.py'
            code.write_text('def generate(): return "later edit"\n')
            changed = root / 'source-spec.json'
            changed.write_text(json.dumps({'model': 'later-model', 'git_commit': 'c' * 40,
                                           'code': {str(code): hashlib.sha256(code.read_bytes()).hexdigest()}}))
            payload['sources'] = {str(changed): '0' * 64}
            artifact.write_text(json.dumps(payload))
            data = self.run_catalogue(root, source)
            row, = data['hierarchies']
            self.assertEqual(row['generator_code']['files'], [])
            self.assertEqual(row['generator_code']['commit_status'], 'unknown: not recorded')
            page = (root / 'catalogue/index.html').read_text()
            self.assertNotIn('later-model', page)


if __name__ == '__main__':
    unittest.main()
