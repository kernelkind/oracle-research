"""Fork a stopped trial through native preparation and receipt reuse."""
import hashlib
import json
from pathlib import Path
import unittest

from sse_multivector import test_canonical_continuation as fixtures


class CanonicalTrialForkTests(unittest.TestCase):
    setUp = fixtures.CanonicalContinuationTests.setUp
    write = fixtures.CanonicalContinuationTests.write
    cli = fixtures.CanonicalContinuationTests.cli
    calls = fixtures.CanonicalContinuationTests.calls
    setup_trial = fixtures.CanonicalContinuationTests.setup_trial
    state = fixtures.CanonicalContinuationTests.state
    dynamic_runner = fixtures.CanonicalContinuationTests.dynamic_runner
    shared = fixtures.CanonicalContinuationTests.shared
    continue_trial = fixtures.CanonicalContinuationTests.continue_trial

    def stopped_trial(self):
        self.dynamic_runner()
        self.setup_trial(schema_version=2, independent_meanings=True)
        self.shared(limit=5)
        result = json.loads(self.continue_trial(attempts=5, ok=False).stdout)
        self.assertEqual(result['status'], 'attempt_limit')
        self.assertEqual((self.state()['index'], self.state()['phase']), (2, 'comparison'))

    def test_fork_preserves_original_and_resumes_only_missing_answers(self):
        self.stopped_trial()
        original = self.state()
        source_path = self.root / 'trial/state.json'
        original_bytes = source_path.read_bytes()
        saved = {path: path.read_bytes() for path in (self.root / 'trial').rglob('*')
                 if path.is_file()}
        shared_bytes = (self.root / 'shared.json').read_bytes()
        inputs = json.loads(self.cli('show', original['experiment'], '--inputs-only', '--json').stdout)
        calls = len(self.calls())

        self.cli('fork-canonical-trial', 'trial', '--output', 'fork')
        fork = json.loads((self.root / 'fork/state.json').read_text())
        for field in ('schema_version', 'index', 'phase', 'nodes', 'steps', 'roots',
                      'local_meanings', 'bootstrap_spec', 'comparison_spec'):
            self.assertEqual(fork[field], original[field], field)
        self.assertEqual(fork.get('queue'), original.get('queue'))
        self.assertEqual(fork['status'], 'awaiting_review')
        self.assertEqual(fork['sources'], original['sources'] | {
            str(source_path): hashlib.sha256(original_bytes).hexdigest()})
        self.assertEqual(Path(fork['experiment']), self.root / 'fork/step-002/experiment')
        self.assertFalse((self.root / 'fork/continuation').exists())
        self.assertEqual(json.loads(self.cli('show', fork['experiment'], '--inputs-only', '--json').stdout), inputs)
        self.assertEqual(len(self.calls()), calls)

        self.write('new-shared.json', dict(schema_version=1, limit=3, used=0))
        result = json.loads(self.cli('continue-canonical-trial', 'fork', '--max-nodes', '1',
                           '--max-new-attempts', '3', '--attempt-budget', 'new-shared.json').stdout)
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(result['attempts']['used'], 1)
        self.assertEqual(len(self.calls()), calls + 1)
        finished = json.loads((self.root / 'fork/state.json').read_text())
        self.assertEqual([answer['reused'] for answer in finished['steps'][-1]['answers']], [True, False])
        plan = json.loads((self.root / 'fork/continuation/plan.json').read_text())['plan']
        self.assertEqual((plan['start_index'], plan['end_index'], plan['max_new_attempts']), (2, 3, 3))
        self.assertEqual((self.root / 'shared.json').read_bytes(), shared_bytes)
        self.assertEqual({path: path.read_bytes() for path in saved}, saved)

    def test_fork_refuses_overwrite_and_changed_sources(self):
        self.stopped_trial()
        self.cli('fork-canonical-trial', 'trial', '--output', 'fork')
        before = (self.root / 'fork/state.json').read_bytes()
        result = self.cli('fork-canonical-trial', 'trial', '--output', 'fork', ok=False)
        self.assertIn('destination already exists', result.stderr)
        self.assertEqual((self.root / 'fork/state.json').read_bytes(), before)
        with (self.root / 'notes.json').open('a') as source:
            source.write('\n')
        result = self.cli('fork-canonical-trial', 'trial', '--output', 'changed', ok=False)
        self.assertIn('trial source changed', result.stderr)
        self.assertFalse((self.root / 'changed').exists())

    def test_fork_refuses_completed_shaped_and_inconsistent_history(self):
        self.stopped_trial()
        original = self.state()
        for field, value in (('status', 'complete'), ('shape', {}), ('index', 1)):
            with self.subTest(field=field):
                self.write('trial/state.json', original | {field: value})
                result = self.cli('fork-canonical-trial', 'trial', '--output', 'rejected', ok=False)
                self.assertIn('unfinished raw canonical trial', result.stderr)
                self.assertFalse((self.root / 'rejected').exists())

    def test_fork_keeps_native_growth_execution_queue(self):
        self.dynamic_runner()
        self.setup_trial(schema_version=2, independent_meanings=True, root_order=[
            {'note_id': 'n1', 'number': '1'}, {'note_id': 'n2', 'number': '2'}])
        self.shared()
        self.continue_trial(nodes=2, attempts=3)
        spec = json.loads((self.root / 'trial.json').read_text())
        spec['roots'] = [{'note_id': 'n3', 'number': '3'}]
        self.write('growth.json', spec)
        self.cli('prepare-canonical-trial', 'growth', '--spec', 'growth.json', '--base-trial', 'trial')
        before = json.loads((self.root / 'growth/state.json').read_text())
        self.cli('fork-canonical-trial', 'growth', '--output', 'fork')
        after = json.loads((self.root / 'fork/state.json').read_text())
        self.assertEqual(after['queue'], before['queue'])
        self.assertEqual(after['steps'], before['steps'])
        result = json.loads(self.continue_trial(directory='fork', nodes=1, attempts=3).stdout)
        self.assertEqual(result['status'], 'complete')
        finished = json.loads((self.root / 'fork/state.json').read_text())
        self.assertEqual(finished['steps'][-1]['local'], {'note_id': 'n3', 'number': '3'})
        self.assertEqual(finished['nodes'][-1]['id'], 'C003')


if __name__ == '__main__':
    unittest.main()
