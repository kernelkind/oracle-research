"""Native construction omits unused previews, never execution reuse guards."""
from contextlib import redirect_stdout
from io import StringIO
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from sse_multivector import experiment as workflow
from sse_multivector import test_canonical_continuation as fixtures


class CanonicalReportPreviewTests(unittest.TestCase):
    setUp = fixtures.CanonicalContinuationTests.setUp
    write = fixtures.CanonicalContinuationTests.write
    cli = fixtures.CanonicalContinuationTests.cli
    calls = fixtures.CanonicalContinuationTests.calls
    setup_trial = fixtures.CanonicalContinuationTests.setup_trial
    dynamic_runner = fixtures.CanonicalContinuationTests.dynamic_runner
    shared = fixtures.CanonicalContinuationTests.shared

    def native(self, *arguments):
        with redirect_stdout(StringIO()), patch.dict(os.environ, {'FAKE_RUNNER_LOG': str(self.log)}):
            return workflow.main(list(arguments))

    def test_native_continuation_never_computes_unused_request_preview(self):
        self.dynamic_runner()
        self.setup_trial(schema_version=2, independent_meanings=True)
        self.shared()
        with patch.object(workflow, 'request_preview', side_effect=AssertionError('unused preview')):
            self.assertEqual(self.native('continue-canonical-trial', str(self.root / 'trial'),
                                        '--max-nodes', '3', '--max-new-attempts', '6',
                                        '--attempt-budget', str(self.root / 'shared.json')), 0)
        state = json.loads((self.root / 'trial/state.json').read_text())
        self.assertEqual(state['status'], 'complete')
        self.assertEqual(len(self.calls()), 6)
        self.assertEqual(json.loads((self.root / 'shared.json').read_text())['used'], 6)

    def test_native_canonical_prepare_skips_preview_but_explicit_prepare_and_show_retain_it(self):
        self.dynamic_runner()
        self.setup_trial(schema_version=2, independent_meanings=True)
        state = json.loads((self.root / 'trial/state.json').read_text())
        self.cli('run', state['experiment'])
        with patch.object(workflow, 'request_preview', side_effect=AssertionError('unused preview')):
            self.assertEqual(self.native('prepare-canonical-trial', str(self.root / 'second'),
                                        '--spec', str(self.root / 'trial.json')), 0)
        with patch.object(workflow, 'request_preview', wraps=workflow.request_preview) as preview:
            self.assertEqual(self.native('prepare', str(self.root / 'explicit'),
                                        '--from', state['experiment']), 0)
            self.assertGreater(preview.call_count, 0)
            result = workflow.report(self.root / 'explicit')
            self.assertEqual(result['requests']['reusable'], 1)
            before = preview.call_count
            self.assertEqual(self.native('show', str(self.root / 'explicit'), '--json'), 0)
            self.assertGreater(preview.call_count, before)

    def test_native_automatic_exact_reuse_still_validates_receipts_without_new_attempts(self):
        self.dynamic_runner()
        self.setup_trial(schema_version=2, independent_meanings=True)
        self.shared()
        args = ('--max-nodes', '3', '--max-new-attempts', '6',
                '--attempt-budget', str(self.root / 'shared.json'))
        self.assertEqual(self.native('continue-canonical-trial', str(self.root / 'trial'), *args), 0)
        calls = len(self.calls())
        used = json.loads((self.root / 'shared.json').read_text())['used']
        with patch.object(workflow, 'request_preview', side_effect=AssertionError('unused preview')):
            self.assertEqual(self.native('prepare-canonical-trial', str(self.root / 'cached'),
                                        '--spec', str(self.root / 'trial.json')), 0)
            self.assertEqual(self.native('continue-canonical-trial', str(self.root / 'cached'), *args), 0)
        self.assertEqual(len(self.calls()), calls)
        self.assertEqual(json.loads((self.root / 'shared.json').read_text())['used'], used)
        self.assertEqual(json.loads((self.root / 'cached/continuation/attempt-budget.json').read_text())['used'], 0)
        state = json.loads((self.root / 'cached/state.json').read_text())
        self.assertEqual(state['status'], 'complete')
        for step in state['steps']:
            shown = workflow.report(step['experiment'])
            self.assertTrue(all(c['status'] == 'valid' and c['reused'] for c in shown['cases']))

    def test_automatic_reuse_rejects_tampered_source_receipt_without_placement(self):
        self.dynamic_runner()
        self.setup_trial(schema_version=2, independent_meanings=True)
        self.shared()
        args = ('--max-nodes', '1', '--max-new-attempts', '2',
                '--attempt-budget', str(self.root / 'shared.json'))
        self.assertEqual(self.native('continue-canonical-trial', str(self.root / 'trial'), *args), 0)
        self.assertEqual(self.native('prepare-canonical-trial', str(self.root / 'cached'),
                                    '--spec', str(self.root / 'trial.json')), 0)
        state = json.loads((self.root / 'trial/state.json').read_text())
        receipt = state['local_meanings']['0']['receipt']['results_path']
        ledger = Path(receipt)
        lines = ledger.read_text().splitlines()
        record = json.loads(lines[0])
        record['final_output_raw'] = '{"meaning":"Forged meaning"}'
        lines[0] = json.dumps(record)
        ledger.write_text('\n'.join(lines) + '\n')
        before = len(self.calls())
        with patch.object(workflow, 'request_preview', side_effect=AssertionError('unused preview')):
            self.assertNotEqual(self.native('continue-canonical-trial', str(self.root / 'cached'), *args), 0)
        cached = json.loads((self.root / 'cached/state.json').read_text())
        self.assertEqual(cached['nodes'], [])
        self.assertEqual(cached['index'], 0)
        self.assertEqual(len(self.calls()), before)

    def test_manual_advance_run_next_skips_unused_preview(self):
        self.dynamic_runner()
        self.setup_trial(schema_version=2, independent_meanings=True)
        state = json.loads((self.root / 'trial/state.json').read_text())
        self.cli('run', state['experiment'])
        self.shared()
        with patch.object(workflow, 'request_preview', side_effect=AssertionError('unused preview')):
            self.assertEqual(self.native('advance-canonical-trial', str(self.root / 'trial'),
                                        '--meaning-case', 'bootstrap', '--comment', 'Offline review',
                                        '--run-next', '--max-new-attempts', '1',
                                        '--attempt-budget', str(self.root / 'shared.json')), 0)
        state = json.loads((self.root / 'trial/state.json').read_text())
        self.assertEqual((state['index'], state['phase']), (1, 'meaning'))
        self.assertEqual(workflow.report(state['experiment'])['summary']['valid'], 1)
