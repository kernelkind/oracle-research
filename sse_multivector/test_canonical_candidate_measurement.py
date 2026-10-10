"""Offline candidate measurements through the production CLI and receipts."""
import hashlib
import json
from pathlib import Path
import unittest

from sse_multivector import test_canonical_continuation as fixtures


class CanonicalCandidateMeasurementTests(unittest.TestCase):
    setUp = fixtures.CanonicalContinuationTests.setUp
    write = fixtures.CanonicalContinuationTests.write
    cli = fixtures.CanonicalContinuationTests.cli
    calls = fixtures.CanonicalContinuationTests.calls
    setup_trial = fixtures.CanonicalContinuationTests.setup_trial
    state = fixtures.CanonicalContinuationTests.state
    dynamic_runner = fixtures.CanonicalContinuationTests.dynamic_runner
    shared = fixtures.CanonicalContinuationTests.shared
    continue_trial = fixtures.CanonicalContinuationTests.continue_trial
    answer = fixtures.CanonicalContinuationTests.answer
    advance = fixtures.CanonicalContinuationTests.advance

    def completed_trial(self):
        self.dynamic_runner()
        self.setup_trial(schema_version=2, independent_meanings=True)
        self.shared()
        self.continue_trial(attempts=6)
        self.write('measurement.json', {'schema_version': 1, 'trial': 'trial',
                   'candidate_limits': [1, 2]})

    def measure(self, output='report.json', **kwargs):
        return self.cli('measure-canonical-candidates', '--source', 'measurement.json',
                        '--output', output, **kwargs)

    def test_native_measurement_is_deterministic_and_never_executes_teacher(self):
        self.completed_trial()
        original = {path: path.read_bytes() for path in (self.root / 'trial').rglob('*')
                    if path.is_file()}
        calls = len(self.calls())
        summary = json.loads(self.measure(env={'FAKE_RUNNER_FAIL_STAGE': 'prompt'}).stdout)
        self.assertEqual(summary['output'], str(self.root / 'report.json'))
        self.assertTrue(all('steps' not in profile for profile in summary['profiles']))
        report = json.loads((self.root / 'report.json').read_text())
        self.assertEqual(report['inference_calls'], 0)
        self.assertEqual(report['baseline']['totals']['cases'], 3)
        self.assertGreater(report['baseline']['totals']['prompt_bytes_queried'], 0)
        for profile in report['profiles']:
            self.assertLessEqual(profile['totals']['prompt_bytes_queried'],
                                 report['baseline']['totals']['prompt_bytes_queried'])
        self.assertEqual([step['index'] for step in report['baseline']['steps']], [1, 2])
        self.assertEqual(len(report['profiles']), 5)
        self.assertTrue(all('totals' in profile and 'steps' in profile for profile in report['profiles']))
        source = self.root / 'measurement.json'
        state = self.root / 'trial/state.json'
        for path in (source, state):
            self.assertEqual(report['sources'][str(path)], hashlib.sha256(path.read_bytes()).hexdigest())
        for name in ('canonical_candidate_measurement.py', 'canonical_candidate_selection.py', 'canonical_trial.py'):
            path = Path(__file__).with_name(name).resolve()
            self.assertEqual(report['sources'][str(path)], hashlib.sha256(path.read_bytes()).hexdigest())
        self.measure('repeat.json')
        self.assertEqual((self.root / 'report.json').read_bytes(), (self.root / 'repeat.json').read_bytes())
        self.assertEqual(len(self.calls()), calls)
        self.assertEqual({path: path.read_bytes() for path in original}, original)

    def test_overwrite_changed_sources_and_graph_snapshots_are_rejected(self):
        self.completed_trial()
        self.measure()
        original_report = (self.root / 'report.json').read_bytes()
        result = self.measure(ok=False)
        self.assertIn('output already exists', result.stderr)
        self.assertEqual((self.root / 'report.json').read_bytes(), original_report)
        state = self.state()
        state['steps'][1]['before'][0]['meaning'] = 'Changed snapshot'
        self.write('trial/state.json', state)
        result = self.measure('changed-snapshot.json', ok=False)
        self.assertIn('graph snapshots differ', result.stderr)
        self.assertFalse((self.root / 'changed-snapshot.json').exists())
        with (self.root / 'notes.json').open('a') as source:
            source.write('\n')
        result = self.measure('changed-source.json', ok=False)
        self.assertIn('trial source changed', result.stderr)
        self.assertFalse((self.root / 'changed-source.json').exists())

    def test_changed_saved_answer_and_selected_meaning_are_rejected(self):
        self.completed_trial()
        original = self.state()
        state = json.loads(json.dumps(original))
        state['steps'][1]['answers'][0]['output']['relation'] = 'equivalent'
        self.write('trial/state.json', state)
        result = self.measure('changed-answer.json', ok=False)
        self.assertIn('differs from validated native receipt', result.stderr)
        self.assertFalse((self.root / 'changed-answer.json').exists())
        state = json.loads(json.dumps(original))
        state['steps'][1]['selected_meaning'] = 'Changed fixed meaning'
        self.write('trial/state.json', state)
        result = self.measure('changed-meaning.json', ok=False)
        self.assertIn('fixed meaning differs', result.stderr)
        self.assertFalse((self.root / 'changed-meaning.json').exists())

    def test_changed_reused_receipt_is_rejected(self):
        self.completed_trial()
        calls = len(self.calls())
        self.cli('prepare-canonical-trial', 'reuse', '--spec', 'trial.json')
        self.continue_trial(directory='reuse', attempts=6)
        self.assertEqual(len(self.calls()), calls)
        state = json.loads((self.root / 'reuse/state.json').read_text())
        answer = state['steps'][0]['answers'][0]
        self.assertTrue(answer['reused'])
        ledger = Path(answer['receipt']['results_path'])
        record = json.loads(ledger.read_text().splitlines()[0])
        origin = Path(record['reused_from']['results_path'])
        records = [json.loads(line) for line in origin.read_text().splitlines()]
        records[0]['final_output_raw'] = '{"meaning":"Altered reused source"}'
        origin.write_text(''.join(json.dumps(row) + '\n' for row in records))
        self.write('measurement.json', {'schema_version': 1, 'trial': 'reuse',
                   'candidate_limits': [1, 2]})
        result = self.measure('changed-reuse.json', ok=False)
        self.assertIn('differs from validated native receipt', result.stderr)
        self.assertFalse((self.root / 'changed-reuse.json').exists())

    def test_source_contract_rejects_invalid_limits_and_incomplete_trial(self):
        self.completed_trial()
        for limits in ([], [0], [True], [513], [1, 1], 'all'):
            with self.subTest(limits=limits):
                self.write('measurement.json', {'schema_version': 1, 'trial': 'trial',
                           'candidate_limits': limits})
                result = self.measure('invalid.json', ok=False)
                self.assertIn('invalid canonical candidate measurement source', result.stderr)
                self.assertFalse((self.root / 'invalid.json').exists())
        self.write('measurement.json', {'schema_version': 1, 'trial': 'trial', 'candidate_limits': [1]})
        state = self.state()
        state['status'] = 'awaiting_review'
        self.write('trial/state.json', state)
        result = self.measure('incomplete.json', ok=False)
        self.assertIn('requires a completed raw canonical trial', result.stderr)
        self.assertFalse((self.root / 'incomplete.json').exists())

    def test_comparison_generated_meanings_are_not_treated_as_fixed_local_meanings(self):
        self.completed_trial()
        state = self.state()
        state['independent_meanings'] = False
        self.write('trial/state.json', state)
        result = self.measure('unfixed.json', ok=False)
        self.assertIn('independently established local meanings', result.stderr)
        self.assertFalse((self.root / 'unfixed.json').exists())

    def test_menu_is_bound_to_the_exact_raw_trial_and_preserves_node_meanings(self):
        self.completed_trial()
        self.write('shape.json', {'schema_version': 1, 'trial': 'trial',
                   'roots': ['C001', 'C002', 'C003'], 'children': {}})
        self.cli('shape-canonical-trial', '--source', 'shape.json', '--output', 'menu')
        self.write('measurement.json', {'schema_version': 1, 'trial': 'trial',
                   'candidate_limits': [1, 2], 'menu': 'menu'})
        self.measure()
        report = json.loads((self.root / 'report.json').read_text())
        menu_path = self.root / 'menu/state.json'
        self.assertEqual(report['sources'][str(menu_path)], hashlib.sha256(menu_path.read_bytes()).hexdigest())
        menu = json.loads(menu_path.read_text())
        menu['nodes'][0]['meaning'] = 'Changed retained meaning'
        self.write('menu/state.json', menu)
        result = self.measure('changed-menu.json', ok=False)
        self.assertIn('menu must preserve nodes', result.stderr)
        self.assertFalse((self.root / 'changed-menu.json').exists())

    def test_terminal_failed_comparison_is_preserved_and_its_receipt_verified(self):
        self.dynamic_runner()
        self.setup_trial(schema_version=2, independent_meanings=True)
        self.answer({'meaning': 'Cooking fixed meaning'})
        self.advance('bootstrap')
        self.answer({'meaning': 'Food fixed meaning'})
        self.advance('bootstrap')
        self.cli('run', self.state()['experiment'], ok=False, env={'FAKE_RUNNER_FAIL_STAGE': 'prompt'})
        self.shared()
        self.continue_trial(attempts=6)
        self.write('measurement.json', {'schema_version': 1, 'trial': 'trial', 'candidate_limits': [1]})
        self.measure()
        report = json.loads((self.root / 'report.json').read_text())
        self.assertEqual(report['baseline']['totals']['held_pair_steps'], 1)
        self.assertIn('terminal answer failure', report['baseline']['steps'][0]['observed_hold_reason'])
        failed = self.state()['steps'][1]['answers'][0]
        self.assertEqual(failed['status'], 'failed')
        ledger = Path(failed['receipt']['results_path'])
        record = json.loads(ledger.read_text().splitlines()[0])
        record['stdout_sha256'] = 'changed'
        ledger.write_text(json.dumps(record) + '\n')
        result = self.measure('invalid-failure.json', ok=False)
        self.assertIn('validated native failure receipt', result.stderr)
        self.assertFalse((self.root / 'invalid-failure.json').exists())

    def test_terminal_failed_standalone_meaning_does_not_prevent_measurement(self):
        self.dynamic_runner()
        self.setup_trial(schema_version=2, independent_meanings=True)
        self.cli('run', self.state()['experiment'], ok=False, env={'FAKE_RUNNER_FAIL_STAGE': 'prompt'})
        self.shared()
        self.continue_trial(attempts=6)
        self.assertIsNone(self.state()['steps'][0]['selected_meaning'])
        self.write('measurement.json', {'schema_version': 1, 'trial': 'trial', 'candidate_limits': [1]})
        self.measure()
        report = json.loads((self.root / 'report.json').read_text())
        self.assertEqual([step['index'] for step in report['baseline']['steps']], [2])

    def test_oversized_reference_is_rejected_before_native_receipt_loading(self):
        self.completed_trial()
        state_path = self.root / 'trial/state.json'
        original = state_path.read_bytes()
        # A sparse file exercises the actual file-size gate without a huge fixture.
        with state_path.open('r+b') as state_file:
            state_file.truncate(64 * 1024 * 1024 + 1)
        self.runner.unlink()
        result = self.measure('too-large.json', ok=False)
        self.assertIn('exceeds 64 MiB limit', result.stderr)
        self.assertFalse((self.root / 'too-large.json').exists())
        state_path.write_bytes(original)
        state = json.loads(original)
        state['steps'][1]['before'] *= 513
        self.write('trial/state.json', state)
        result = self.measure('too-many-nodes.json', ok=False)
        self.assertIn('exceeds 512 nodes per snapshot', result.stderr)
        self.assertFalse((self.root / 'too-many-nodes.json').exists())
        state = json.loads(original)
        state['steps'][1]['answers'] *= 50001
        self.write('trial/state.json', state)
        result = self.measure('too-many-cases.json', ok=False)
        self.assertIn('exceeds 50000 pair cases', result.stderr)
        self.assertFalse((self.root / 'too-many-cases.json').exists())


if __name__ == '__main__':
    unittest.main()
