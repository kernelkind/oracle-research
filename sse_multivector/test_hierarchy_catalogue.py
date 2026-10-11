"""Exercise saved hierarchy discovery through the production shared launcher."""
import hashlib
import json
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
            self.assertIn('historical-model', (root / 'catalogue/index.html').read_text())

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


if __name__ == '__main__':
    unittest.main()
