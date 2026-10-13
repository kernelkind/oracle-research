"""Exercise official hierarchy selection through the production shared launcher."""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import unittest


class HierarchyCatalogue(unittest.TestCase):
    def official_selection(self, source, artifact, version='HR03', name='Official test run'):
        spec = json.loads(source.read_text())
        spec['official_runs'] = [{'version_id': version, 'name': name,
                                 'root': str(artifact.parents[2]),
                                 'artifact_path': str(artifact.relative_to(artifact.parents[2])),
                                 'sha256': hashlib.sha256(artifact.read_bytes()).hexdigest()}]
        source.write_text(json.dumps(spec))

    def test_only_explicit_official_run_is_catalogued(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact, _, source = self.fixture(root)
            self.official_selection(source, artifact)
            diagnostic = artifact.parent.parent / 'diagnostic-checkpoint/state.json'
            diagnostic.parent.mkdir()
            diagnostic.write_bytes(artifact.read_bytes())
            rows = self.run_catalogue(root, source)['hierarchies']
            self.assertEqual([r['version_id'] for r in rows], ['HR03'])
            row, = rows
            self.assertEqual(row['version_id'], 'HR03')
            self.assertEqual(row['name'], 'Official test run')
            self.assertEqual(diagnostic.read_bytes(), artifact.read_bytes())

    def test_official_subject_prompt_refreshes_unknown_version_without_rebinding(self):
        for saved_only in (False, True):
            with self.subTest(saved_only=saved_only), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                artifact, _, source = self.fixture(root)
                original = artifact.read_bytes()
                before, = self.run_catalogue(root, source)['hierarchies']
                self.assertEqual(before['subject_versions'], [])
                self.assertEqual(before['source_status'], 'subject version unknown')
                registry = (root / 'versions.json').read_bytes()
                snapshot = root / 'catalogue' / before['output']
                snapshot_modified = snapshot.stat().st_mtime_ns

                spec = json.loads(source.read_text())
                spec['official_runs'][0]['experimental_parameters'] = {
                    'dataset': {'subject_prompt': 'ASv6.100'}}
                source.write_text(json.dumps(spec))
                row, = self.run_catalogue(root, source, ['--saved-only'] if saved_only else ())['hierarchies']

                self.assertEqual(row['subject_versions'], ['ASv6.100'])
                self.assertEqual(row['source_status'], 'source recorded: ASv6.100')
                for field in ('version_id', 'identity', 'artifact_path', 'sha256', 'output'):
                    self.assertEqual(row[field], before[field])
                self.assertEqual((root / 'versions.json').read_bytes(), registry)
                self.assertEqual(artifact.read_bytes(), original)
                self.assertEqual(snapshot.read_bytes(), original)
                self.assertEqual(snapshot.stat().st_mtime_ns, snapshot_modified)

                del spec['official_runs'][0]['experimental_parameters']
                source.write_text(json.dumps(spec))
                row, = self.run_catalogue(root, source, ['--saved-only'] if saved_only else ())['hierarchies']
                self.assertEqual(row['subject_versions'], [])
                self.assertEqual(row['source_status'], 'subject version unknown')
                self.assertEqual((root / 'versions.json').read_bytes(), registry)
                self.assertEqual(snapshot.read_bytes(), original)
                self.assertEqual(snapshot.stat().st_mtime_ns, snapshot_modified)

    def test_official_subject_prompt_preserves_artifact_and_evidence_versions(self):
        for saved_only in (False, True):
            with self.subTest(saved_only=saved_only), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                artifact, payload, source = self.fixture(root)
                payload['subject_prompt'] = 'ASv6.72'
                configuration = artifact.with_name('configuration.json')
                configuration.write_text(json.dumps({'subject_prompt': 'ASv6.48'}))
                payload['sources'] = {str(configuration): hashlib.sha256(configuration.read_bytes()).hexdigest()}
                artifact.write_text(json.dumps(payload))
                self.official_selection(source, artifact, 'H0001')
                before, = self.run_catalogue(root, source)['hierarchies']
                self.assertEqual(before['subject_versions'], ['ASv6.48', 'ASv6.72'])
                registry = (root / 'versions.json').read_bytes()

                spec = json.loads(source.read_text())
                spec['official_runs'][0]['experimental_parameters'] = {
                    'dataset': {'subject_prompt': 'ASv6.100'},
                    'historical_reference': 'Unrelated ASv1.1 mention'}
                source.write_text(json.dumps(spec))
                row, = self.run_catalogue(root, source, ['--saved-only'] if saved_only else ())['hierarchies']

                self.assertEqual(row['subject_versions'], ['ASv6.100', 'ASv6.48', 'ASv6.72'])
                self.assertEqual(row['source_status'], 'historical/deprecated')
                self.assertEqual((root / 'versions.json').read_bytes(), registry)
                self.assertEqual(row['identity'], before['identity'])
                self.assertEqual(row['sha256'], before['sha256'])

    def test_source_without_explicit_official_selection_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _, _, source = self.fixture(root)
            spec = json.loads(source.read_text())
            del spec['official_runs']
            source.write_text(json.dumps(spec))
            result = self.catalogue_result(root, source)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('must explicitly list official_runs', result.stderr)
            self.assertFalse((root / 'versions.json').exists())
            self.assertFalse((root / 'catalogue').exists())

    def test_missing_pinned_official_output_is_rejected_without_changing_archive(self):
        for saved_only in (False, True):
            with self.subTest(saved_only=saved_only), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                artifact, _, source = self.fixture(root)
                row, = self.run_catalogue(root, source)['hierarchies']
                registry = (root / 'versions.json').read_bytes()
                snapshot = root / 'catalogue' / row['output']
                retained = snapshot.read_bytes()
                artifact.unlink()
                result = self.catalogue_result(root, source, ['--saved-only'] if saved_only else ())
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('missing official output', result.stderr)
                self.assertEqual((root / 'versions.json').read_bytes(), registry)
                self.assertEqual(snapshot.read_bytes(), retained)

    def test_unselected_registry_rows_are_dropped_even_when_rebuilding_saved_inventory(self):
        for saved_only in (False, True):
            with self.subTest(saved_only=saved_only), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                artifact, _, source = self.fixture(root)
                self.official_selection(source, artifact)
                row, = self.run_catalogue(root, source)['hierarchies']
                legacy = {**row, 'version_id': 'H0042', 'identity': 'f' * 64,
                          'name': 'Diagnostic checkpoint', 'artifact_path': 'target/diagnostic/state.json'}
                (root / 'catalogue/records/H0042.json').write_text(json.dumps(legacy))
                registry = root / 'versions.json'
                saved = json.loads(registry.read_text())
                saved['versions'].append({k: legacy[k] for k in ('version_id', 'identity', 'artifact_path', 'sha256', 'family')})
                registry.write_text(json.dumps(saved))
                rows = self.run_catalogue(root, source, ['--saved-only'] if saved_only else ())['hierarchies']
                self.assertEqual([r['version_id'] for r in rows], ['HR03'])
                self.assertEqual([r['version_id'] for r in json.loads(registry.read_text())['versions']], ['HR03'])
                self.assertTrue((root / 'catalogue/records/H0042.json').exists())

    def test_related_menu_parameters_and_source_code_stay_under_official_run(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact, _, source = self.fixture(root)
            menu = artifact.parent / 'browsing-menu/categories.json'
            menu.parent.mkdir()
            menu.write_text(json.dumps({'nodes': [{'id': 'C001'}], 'root_node_id': 'C001',
                                        'menu_policy': {'max_choices': 6}}))
            code = menu.with_name('menu_generator.py')
            code.write_text('def menu(): return "saved menu policy"\n')
            configuration = menu.with_name('configuration.json')
            configuration.write_text(json.dumps({'seed': 91, 'code': {
                str(code): hashlib.sha256(code.read_bytes()).hexdigest()}}))
            spec = json.loads(source.read_text())
            entry = spec['official_runs'][0]
            entry['related_outputs'] = [{'label': 'Browsing menu',
                                         'path': str(menu.relative_to(root / 'original')),
                                         'sha256': hashlib.sha256(menu.read_bytes()).hexdigest()}]
            entry['experimental_parameters'] = {'concurrency': 32, 'api_key': 'omit-secret'}
            entry['code_provenance'] = {'git_commit': 'a' * 40, 'basis': 'Preserved source; generation commit unknown'}
            source.write_text(json.dumps(spec))
            data = self.run_catalogue(root, source)
            row, = data['hierarchies']
            self.assertEqual(row['experimental_parameters'], {'concurrency': 32})
            self.assertEqual(row['code_provenance'], entry['code_provenance'])
            self.assertEqual(row['generator_code']['commit_status'], 'unknown: not recorded')
            related, = row['related_outputs']
            self.assertEqual(related['parameters']['menu_policy']['max_choices'], 6)
            self.assertEqual((root / 'catalogue' / related['output']).read_bytes(), menu.read_bytes())
            self.assertTrue(any(data['parameter_evidence'][e['sha256']].get('seed') == 91 for e in related['evidence']))
            self.assertEqual(len(json.loads((root / 'versions.json').read_text())['versions']), 1)
            generator, = row['generator_code']['files']
            self.assertEqual((root / 'catalogue' / generator['snapshot']).read_bytes(), code.read_bytes())

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
        self.official_selection(source, artifact, 'H0001', artifact.parent.name)
        return artifact, payload, source

    def catalogue_result(self, root, source, extra=()):
        project = Path(__file__).resolve().parent.parent
        launcher = project.parent / 'experiment-runner' / 'bin' / 'experiment-runner'
        result = subprocess.run([str(launcher), '--project-root', str(project),
                                 'catalogue-hierarchies', '--source', str(source),
                                 '--registry', str(root / 'versions.json'),
                                 '--output', str(root / 'catalogue'), *extra], capture_output=True, text=True)
        return result

    def run_catalogue(self, root, source, extra=()):
        result = self.catalogue_result(root, source, extra)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads((root / 'catalogue/catalogue.json').read_text())
        self.assertEqual(data['discovery_errors'], [])
        return data

    def test_cli_preserves_selected_version_and_original_output(self):
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
            self.assertEqual(row['locations'], [str(artifact)])
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
            self.official_selection(source, artifact, 'H0001', artifact.parent.name)
            data = self.run_catalogue(root, source)
            row, = data['hierarchies']
            self.assertEqual(row['name'], 'saved-run')
            self.assertEqual(row['generation_time']['basis'], 'saved execution start')
            self.assertEqual(row['generation_time']['timestamp'], '2026-10-08T04:00:00+00:00')
            self.assertNotIn('before', row['parameters']['steps'][0])
            saved = [data['parameter_evidence'][e['sha256']] for e in row['evidence']]
            self.assertTrue(any(d.get('model') == 'step-model' for d in saved))
            self.assertTrue(any(d.get('execution_settings', [{}])[0].get('concurrency') == 4 for d in saved))

    def test_cutoff_labels_mtime_and_rejects_selected_output_before_cutoff(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact, payload, source = self.fixture(root)
            spec = json.loads(source.read_text())
            spec['generated_since'] = '2026-10-08T00:00:00-04:00'
            source.write_text(json.dumps(spec))
            artifact.write_text(json.dumps({**payload, 'generated_at': '2026-10-07T20:00:00-04:00'}))
            self.official_selection(source, artifact, 'H0001', artifact.parent.name)
            result = self.catalogue_result(root, source)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('predates generated_since', result.stderr)
            artifact.write_text(json.dumps(payload))
            self.official_selection(source, artifact, 'H0001', artifact.parent.name)
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
            self.official_selection(source, artifact, 'H0001', artifact.parent.name)
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
            self.official_selection(source, artifact, 'H0001', artifact.parent.name)
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

    def test_empty_official_selection_removes_old_rows_without_deleting_archives(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact, _, source = self.fixture(root)
            self.run_catalogue(root, source)
            spec = json.loads(source.read_text())
            spec['official_runs'] = []
            source.write_text(json.dumps(spec))
            self.assertEqual(self.run_catalogue(root, source)['hierarchies'], [])
            self.assertEqual(self.run_catalogue(root, source, ['--saved-only'])['hierarchies'], [])
            self.assertTrue((root / 'catalogue/records/H0001.json').exists())
            self.assertTrue((root / 'catalogue/outputs/H0001.json').exists())

    def test_changed_output_is_rejected_without_rebinding_official_id(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact, payload, source = self.fixture(root)
            original = artifact.read_bytes()
            self.run_catalogue(root, source)
            registry = (root / 'versions.json').read_bytes()
            payload['nodes'][0]['meaning'] = 'Revised meaning'
            artifact.write_text(json.dumps(payload))
            for extra in ((), ['--saved-only']):
                result = self.catalogue_result(root, source, extra)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('changed pinned official output', result.stderr)
            self.assertEqual((root / 'versions.json').read_bytes(), registry)
            self.assertEqual((root / 'catalogue/outputs/H0001.json').read_bytes(), original)
            self.official_selection(source, artifact, 'H0001', 'Changed official run')
            result = self.catalogue_result(root, source)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('already bound to another immutable output', result.stderr)

    def test_saved_settings_and_changed_frozen_sources_are_visible_in_one_catalogue(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact, payload, source = self.fixture(root)
            config = artifact.parent / 'configuration.json'
            config.write_text(json.dumps({'runner': {'model': 'historical-model', 'concurrency': 4},
                                          'seed': 123, 'api_key': 'must-not-appear'}))
            payload['sources'] = {str(config): '0' * 64, '/missing/configuration.json': '1' * 64}
            artifact.write_text(json.dumps(payload))
            self.official_selection(source, artifact, 'H0001', artifact.parent.name)
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
                frozen = database.with_name('frozen.sqlite')
                with sqlite3.connect(frozen) as target:
                    connection.backup(target)
                spec = json.loads(source.read_text())
                spec['official_runs'][0].update(artifact_path=str(database.relative_to(root / 'original')),
                                               sha256=hashlib.sha256(frozen.read_bytes()).hexdigest())
                source.write_text(json.dumps(spec))
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
            self.official_selection(source, artifact, 'H0001', artifact.parent.name)
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
            self.official_selection(source, artifact, 'H0001', artifact.parent.name)
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
            self.official_selection(source, artifact, 'H0001', artifact.parent.name)
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
                self.official_selection(source, artifact, 'H0001', artifact.parent.name)
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
            self.official_selection(source, artifact, 'H0001', artifact.parent.name)
            data = self.run_catalogue(root, source)
            row, = data['hierarchies']
            self.assertEqual(row['generator_code']['files'], [])
            self.assertEqual(row['generator_code']['commit_status'], 'unknown: not recorded')
            page = (root / 'catalogue/index.html').read_text()
            self.assertNotIn('later-model', page)


if __name__ == '__main__':
    unittest.main()
