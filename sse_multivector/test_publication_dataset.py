"""Exercise shared publication preparation through the supported project CLI."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class PublicationDatasetTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'exports'
        self.output = self.root / 'dataset'
        self.mapping = self.root / 'roots.json'
        self.mapping.write_text(json.dumps({'fixture': str(self.root / 'originals')}))
        self.selection = self.root / 'selection.json'
        self.decisions = []

    def publication(self, name, status, *, reused=None):
        directory = self.source / 'prompts' / name
        directory.mkdir(parents=True)
        payloads = {
            'inputs.jsonl': [{'input_sha256': 'input', 'inputs': {'POST': 'Tea ' * 300}}],
            'results.jsonl': [{'case_id': name, 'input_sha256': 'input', 'status': status,
                               'output': None if status == 'unrun' else 'Saved answer ' * 40,
                               'reused': reused, 'reviews': []}],
        }
        files = {}
        for filename, rows in payloads.items():
            raw = b''.join(json.dumps(row, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode() + b'\n' for row in rows)
            (directory / filename).write_bytes(raw)
            files[filename] = {'sha256': hashlib.sha256(raw).hexdigest(),
                               'bytes': len(raw), 'records': len(rows)}
        native = self.root / 'originals' / name
        run = native / 'run'
        run.mkdir(parents=True)
        native_files = {'experiment': native / 'experiment.json', 'report': native / 'report.json',
                        'runner_config': native / 'runner-config.json', 'manifest': run / 'manifest.json'}
        for key, file in native_files.items():
            file.write_text(json.dumps({'fixture': name, 'file': key}) + '\n')
        evidence = {key: {'exists': True, 'sha256': hashlib.sha256(file.read_bytes()).hexdigest()}
                    for key, file in native_files.items()}
        evidence.update({key: {'exists': False} for key in
                         ('results_ledger', 'execution-settings.jsonl', 'code-upgrades.jsonl')})
        metadata = {'schema_version': 1, 'format': 'prompt-publication-v1',
                    'source_id': name, 'outcome': {'cases': 1, status: 1}, 'files': files,
                    'snapshot': {'experiment_sha256': evidence['experiment']['sha256'],
                                 'report_sha256': evidence['report']['sha256']}}
        (directory / 'experiment.json').write_text(json.dumps(metadata, sort_keys=True, indent=2) + '\n')
        if status == 'unrun':
            self.decisions.append({'publication': 'prompts/' + name, 'plan_sha256': name,
                'decision': 'exclude_unexecuted_preparation', 'exported_outcome': metadata['outcome'],
                'source_snapshot_unchanged': True, 'source': 'fixture:' + name + '/experiment.json',
                'resolved_run_directory': str(run), 'run_entries': ['manifest.json'], 'evidence': evidence})
            self.selection.write_text(json.dumps({'source_mapping': str(self.mapping), 'publications': self.decisions}))
        return directory

    def cli(self, *arguments):
        project = Path(__file__).resolve().parents[1]
        environment = dict(os.environ, EXPERIMENT_RUNNER_ROOT=str(project.parent / 'experiment-runner'),
                           PYTHONDONTWRITEBYTECODE='1')
        return subprocess.run([sys.executable, str(project / 'sse_multivector/experiment.py'),
                               *map(str, arguments)], cwd=project, env=environment,
                              text=True, capture_output=True)

    def test_preparation_shares_content_and_omits_only_unexecuted_snapshots(self):
        self.publication('completed', 'valid')
        self.publication('failed', 'failed')
        self.publication('prepared', 'unrun')
        before = {str(p.relative_to(self.source)): p.read_bytes()
                  for p in self.source.rglob('*') if p.is_file()}
        result = self.cli('prepare-publication-dataset', self.source, '--output', self.output,
                          '--selection', self.selection)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.output / 'prompts/completed/results.jsonl').is_file())
        self.assertTrue((self.output / 'prompts/failed/results.jsonl').is_file())
        self.assertFalse((self.output / 'prompts/prepared').exists())
        self.assertIn('"$ref"', (self.output / 'prompts/completed/inputs.jsonl').read_text())
        verified = self.cli('verify-publication-dataset', self.output)
        self.assertEqual(verified.returncode, 0, verified.stderr)
        restored = self.root / 'restored'
        result = self.cli('restore-publication-dataset', self.output, '--output', restored)
        self.assertEqual(result.returncode, 0, result.stderr)
        for relative, raw in before.items():
            self.assertEqual((self.source / relative).read_bytes(), raw)
            if not relative.startswith('prompts/prepared/'):
                self.assertEqual((restored / relative).read_bytes(), raw)

    def test_reused_answer_cannot_be_excluded_as_an_unrun_preparation(self):
        self.publication('reused', 'unrun', reused=True)
        result = self.cli('prepare-publication-dataset', self.source, '--output', self.output)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.output / 'prompts/reused/results.jsonl').is_file())

    def test_old_unrun_snapshot_requires_bound_execution_evidence(self):
        directory = self.publication('historical', 'unrun')
        path = directory / 'experiment.json'
        metadata = json.loads(path.read_bytes())
        metadata['snapshot'] = {'experiment_sha256': 'old-plan', 'report_sha256': 'old-report'}
        path.write_text(json.dumps(metadata, sort_keys=True, indent=2) + '\n')
        result = self.cli('prepare-publication-dataset', self.source, '--output', self.output)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('requires execution evidence', result.stderr)
        self.assertFalse(self.output.exists())
        evidence = self.root / 'selection.json'
        row = {'publication': 'prompts/historical', 'plan_sha256': 'historical',
               'decision': 'keep_unknown', 'exported_outcome': metadata['outcome'],
               'evidence': {'experiment': {'sha256': 'old-plan'}, 'report': {'sha256': 'old-report'}},
               'source_snapshot_unchanged': True}
        evidence.write_text(json.dumps({'source_mapping': str(self.mapping), 'publications': [row]}))
        result = self.cli('prepare-publication-dataset', self.source, '--output', self.output,
                          '--selection', evidence)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.output / 'prompts/historical/results.jsonl').is_file())

    def test_execution_evidence_cannot_exclude_another_snapshot(self):
        directory = self.publication('historical', 'unrun')
        path = directory / 'experiment.json'
        metadata = json.loads(path.read_bytes())
        metadata['snapshot'] = {'experiment_sha256': 'old-plan', 'report_sha256': 'old-report'}
        path.write_text(json.dumps(metadata, sort_keys=True, indent=2) + '\n')
        evidence = self.root / 'selection.json'
        evidence.write_text(json.dumps({'source_mapping': str(self.mapping), 'publications': [{'publication': 'prompts/historical',
            'plan_sha256': 'different-plan', 'decision': 'exclude_unexecuted_preparation',
            'exported_outcome': metadata['outcome'], 'evidence': {
                'experiment': {'sha256': 'old-plan'}, 'report': {'sha256': 'old-report'}}}]}))
        result = self.cli('prepare-publication-dataset', self.source, '--output', self.output,
                          '--selection', evidence)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('does not bind', result.stderr)
        self.assertFalse(self.output.exists())

    def test_new_execution_after_audit_prevents_omission(self):
        self.publication('prepared', 'unrun')
        (self.root / 'originals/prepared/run/results.jsonl').write_text('{"status":"failed"}\n')
        result = self.cli('prepare-publication-dataset', self.source, '--output', self.output,
                          '--selection', self.selection)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('execution evidence is stale', result.stderr)
        self.assertFalse(self.output.exists())


if __name__ == '__main__':
    unittest.main()
