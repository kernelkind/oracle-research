"""Offline hierarchy foundation checks through the shared production CLI."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import unittest

from sse_multivector import test_experiment as fixtures


PROJECT = Path(__file__).resolve().parents[1]
LAUNCHER = PROJECT.parent / 'experiment-runner/bin/experiment-runner'


class CanonicalFoundationIntegrationTests(unittest.TestCase):
    setUp = fixtures.ExperimentTests.setUp
    write = fixtures.ExperimentTests.write
    calls = fixtures.ExperimentTests.calls

    def cli(self, *args, ok=True):
        result = subprocess.run(
            [str(LAUNCHER), '--project-root', str(PROJECT), *map(str, args)],
            cwd=self.root, env={**os.environ, 'FAKE_RUNNER_LOG': str(self.log)},
            text=True, capture_output=True, timeout=30)
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout)
        return result

    def test_canonical_preparation_command_checks_source_without_inference(self):
        result = self.cli('prepare-canonical-traversal', 'trial',
                          '--spec', 'missing-trial.json', ok=False)
        self.assertNotIn('invalid choice', result.stderr)
        self.assertIn('missing-trial.json', result.stderr)
        self.assertFalse((self.root / 'trial').exists())
        self.assertEqual(self.calls(), [])

    def test_local_meaning_adapter_preserves_full_selected_tree_and_code_binding(self):
        entries = [
            dict(number='1', subject='Feedback', context='Participant responses.'),
            dict(number='1.1', subject='Written feedback', context='Comment slips.'),
            dict(number='2', subject='Equipment', context='Packed components.')]
        self.write('subjects.json', dict(schema_version=1, notes=[dict(
            note_id='note', text='Participants left comment slips. Components are packed.',
            origin=dict(prompt_version='ASv6.100'), subjects=entries)]))
        self.write('nodes.json', dict(schema_version=4, corpus='subjects.json', nodes=[dict(
            id='selected', local=dict(note_id='note', number='1.1'), review={})]))
        self.prompt.write_text('Define the selected topic. {INPUT_JSON}')
        spec = json.loads(self.spec.read_text())
        spec['dataset'] = dict(adapter='hierarchy_local_nodes', path='nodes.json')
        self.write('spec.json', spec)
        self.cli('prepare', 'prepared', '--spec', self.spec)
        shown = json.loads(self.cli('show', 'prepared', '--case', 'selected', '--json').stdout)
        self.assertEqual(json.loads(shown['inputs']['INPUT_JSON']), dict(local=dict(
            post='Participants left comment slips. Components are packed.',
            hierarchy=dict(selected='1.1', entries=entries[:2]))))
        plan = json.loads((self.root / 'prepared/experiment.json').read_text())['plan']
        for name in ('canonical_trial.py', 'canonical_receipts.py', 'hierarchy_node_pairs.py'):
            path = PROJECT / 'sse_multivector' / name
            self.assertEqual(plan['code'][name], hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(self.calls(), [])


if __name__ == '__main__':
    unittest.main()
