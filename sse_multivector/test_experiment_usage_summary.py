"""Cross-experiment summaries use the stable shared CLI and offline fixtures."""

import json
import os
from pathlib import Path
import subprocess
import unittest

from sse_multivector import extraction_pipeline as engine
from sse_multivector import test_experiment as fixtures


SHARED_CLI = Path(engine.__file__).resolve().parents[1] / 'bin/experiment-runner'
PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ExperimentUsageSummaryTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.ExperimentTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        self.fixture.runner.write_bytes(
            (SHARED_CLI.parent.parent / 'tests/fixtures/fake-runner.py').read_bytes())
        self.fixture.cli = self.cli

    def cli(self, *args, ok=True, env=None):
        result = subprocess.run(
            [str(SHARED_CLI), '--project-root', str(PROJECT_ROOT), *map(str, args)],
            cwd=self.root,
            env={**os.environ, 'FAKE_RUNNER_LOG': str(self.fixture.log), **(env or {})},
            text=True, capture_output=True, timeout=30)
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout)
        return result

    def source(self, groups, budget=None):
        value = dict(schema_version=1, groups=groups)
        if budget is not None:
            value['attempt_budget'] = budget
        return self.fixture.write('usage-source.json', value)

    def summarize(self, source, output='summary.json', **kwargs):
        return self.cli('summarize-experiments', '--spec', source, '--output', output, **kwargs)

    def test_summary_counts_valid_native_attempts_without_new_calls(self):
        f = self.fixture
        f.prepare('known')
        f.cli('run', 'known')
        before = len(f.calls())
        self.summarize(self.source(dict(generation=['known'])))
        saved = json.loads((self.root / 'summary.json').read_text())
        self.assertEqual(saved['totals']['attempts'], 2)
        self.assertEqual(saved['generation_usage']['original_calls'], 2)
        self.assertEqual(len(f.calls()), before)

    def test_summary_preserves_automatic_warmup_classification(self):
        f = self.fixture
        f.prompt.write_text('GENERIC PROMPT' + ' word' * 1100 + '\n{POST}')
        f.prepare('cached', '--model', 'gpt-6.1-sol', '--prompt-cache')
        f.cli('run', 'cached', env={'FAKE_RUNNER_RESULT_OVERRIDE': json.dumps({
            'usage': {'input': 100, 'output': 20, 'cost': {'total': 0.25}}})})
        shown = f.show('cached', '--generation-costs')
        self.assertEqual(shown['summary']['attempts'], 3)
        self.assertEqual(shown['cache_warmup']['attempts'], 1)
        expected = shown['generation_usage']['cost_statistics']
        self.assertEqual(expected['warmup_requests'], 1)
        self.assertEqual(expected['comparison_requests'], 2)
        before = len(f.calls())
        self.summarize(self.source(dict(generation=['cached'])))
        saved = json.loads((self.root / 'summary.json').read_text())
        usage = saved['generation_usage']
        self.assertEqual(usage['original_calls'], 3)
        self.assertEqual(usage['catalog_cost_estimate_usd'], 0.75)
        self.assertEqual(usage['cost_statistics']['warmup_requests'], 1)
        self.assertEqual(usage['cost_statistics'], expected)
        self.assertEqual(len(f.calls()), before)

    def test_reused_warmup_is_classified_and_counted_once_across_cohorts(self):
        f = self.fixture
        f.prompt.write_text('GENERIC PROMPT' + ' word' * 1100 + '\n{POST}')
        f.prepare('cached', '--model', 'gpt-6.1-sol', '--prompt-cache')
        f.cli('run', 'cached', env={'FAKE_RUNNER_RESULT_OVERRIDE': json.dumps({
            'usage': {'input': 100, 'output': 20, 'cost': {'total': 0.25}}})})
        expected = f.show('cached', '--generation-costs')['generation_usage']
        for name in ('reuse_one', 'reuse_two'):
            f.cli('prepare', name, '--from', 'cached')
            f.cli('run', name)
        before = len(f.calls())
        self.summarize(self.source(dict(construction=['reuse_one', 'reuse_two'])))
        saved = json.loads((self.root / 'summary.json').read_text())
        usage = saved['generation_usage']
        self.assertEqual(saved['totals']['attempts'], 0)
        self.assertEqual(saved['totals']['reused'], 4)
        self.assertEqual(usage['original_calls'], 3)
        self.assertEqual(usage['source_calls_added'], 3)
        self.assertEqual(usage['cost_statistics'], expected['cost_statistics'])
        self.assertEqual(usage['catalog_cost_estimate_usd'], 0.75)
        self.assertEqual(len(f.calls()), before)

    def test_failed_warmup_unknown_usage_preserves_classification_and_incomplete_cost(self):
        f = self.fixture
        f.prompt.write_text('GENERIC PROMPT' + ' word' * 1100 + '\n{POST}')
        f.prepare('cached', '--model', 'gpt-6.1-sol', '--prompt-cache')
        f.cli('run', 'cached', env={'FAKE_RUNNER_FAIL_STAGE': 'prompt'}, ok=False)
        before = len(f.calls())
        self.summarize(self.source(dict(generation=['cached'])))
        saved = json.loads((self.root / 'summary.json').read_text())
        self.assertFalse(saved['complete'])
        for usage in (saved['totals'], saved['generation_usage']):
            self.assertEqual(usage['attempts_without_usage'], 1)
            self.assertEqual(usage['attempts_without_cost_estimate'], 1)
            self.assertEqual(usage['known_catalog_cost_estimate_usd'], 0)
            self.assertIsNone(usage['catalog_cost_estimate_usd'])
        usage = saved['generation_usage']
        self.assertEqual(usage['original_calls'], 1)
        self.assertEqual(usage['failed_calls'], 1)
        self.assertEqual(usage['cost_statistics']['warmup_requests'], 1)
        self.assertEqual(usage['cost_statistics']['comparison_requests'], 0)
        self.assertIsNone(usage['cost_statistics']['total_cost_usd'])
        self.assertEqual(len(f.calls()), before)

    def test_instructions_only_experiment_counts_as_warmup_not_comparison(self):
        f = self.fixture
        f.prompt.write_text('GENERIC PROMPT' + ' word' * 1100 + '\n{POST}')
        f.prepare('cached', '--model', 'gpt-6.1-sol', '--prompt-cache')
        f.cli('prepare', 'warm', '--from', 'cached', '--cache-warmup')
        f.cli('run', 'warm', '--max-new-attempts', '1')
        expected = f.show('warm', '--generation-costs')['generation_usage']
        before = len(f.calls())
        self.summarize(self.source(dict(warming=['warm'])))
        saved = json.loads((self.root / 'summary.json').read_text())
        self.assertEqual(saved['totals']['attempts'], 1)
        self.assertEqual(saved['generation_usage']['original_calls'], 1)
        self.assertEqual(saved['generation_usage']['cost_statistics']['warmup_requests'], 1)
        self.assertEqual(saved['generation_usage']['cost_statistics']['comparison_requests'], 0)
        self.assertEqual(saved['generation_usage']['cost_statistics'], expected['cost_statistics'])
        self.assertEqual(len(f.calls()), before)

    def test_recovered_warmup_and_comparison_retries_retain_both_classifications(self):
        f = self.fixture
        f.prompt.write_text('GENERIC PROMPT' + ' word' * 1100 + '\n{POST}')
        f.prepare('cached', '--model', 'gpt-6.1-sol', '--prompt-cache')
        f.cli('run', 'cached', env={
            'FAKE_RUNNER_RESULT_OVERRIDE': json.dumps({
                'usage': {'input': 100, 'output': 20, 'cost': {'total': 0.25}}}),
            'FAKE_RUNNER_FAILURES': json.dumps({'GENERIC PROMPT': dict(
                attempts=1, metadata=dict(http_status=200,
                    error=dict(code=504, message='Upstream idle timeout exceeded')))})})
        expected = f.show('cached', '--generation-costs')['generation_usage']
        before = len(f.calls())
        self.summarize(self.source(dict(generation=['cached'])))
        saved = json.loads((self.root / 'summary.json').read_text())
        self.assertEqual(saved['totals']['attempts'], 6)
        self.assertEqual(saved['totals']['failed_attempts'], 3)
        self.assertEqual(saved['totals']['recovered_failed_attempts'], 3)
        self.assertEqual(saved['totals']['retry_attempts'], 3)
        self.assertEqual(saved['generation_usage']['original_calls'], 6)
        self.assertEqual(saved['generation_usage']['cost_statistics']['warmup_requests'], 2)
        self.assertEqual(saved['generation_usage']['cost_statistics']['comparison_requests'], 4)
        self.assertEqual(saved['generation_usage']['cost_statistics'], expected['cost_statistics'])
        self.assertEqual(saved['generation_usage']['catalog_cost_estimate_usd'], 1.5)
        self.assertEqual(len(f.calls()), before)

    def test_cli_costs_deduplicate_generation_across_two_reuse_cohorts(self):
        f = self.fixture
        f.prepare('generation')
        f.cli('run', 'generation', env={'FAKE_RUNNER_RESULT_OVERRIDE': json.dumps({
            'usage': {'input': 100, 'output': 20, 'cost': {'total': 0.25}}})})
        for name in ('reuse_one', 'reuse_two'):
            f.cli('prepare', name, '--from', 'generation')
            f.cli('run', name)
        source = self.source(dict(construction=['reuse_one', 'reuse_two'],
                                  generation=['generation']))
        before = len(f.calls())
        shown = json.loads(self.summarize(source).stdout)
        saved = json.loads((self.root / 'summary.json').read_text())
        self.assertEqual(saved['totals']['attempts'], 2)
        self.assertEqual(saved['totals']['reused'], 4)
        self.assertEqual(saved['totals']['catalog_cost_estimate_usd'], 0.5)
        self.assertEqual(saved['groups']['construction']['totals']['catalog_cost_estimate_usd'], 0)
        self.assertEqual(saved['generation_usage']['original_calls'], 2)
        self.assertEqual(saved['generation_usage']['source_calls_added'], 0)
        self.assertEqual(saved['generation_usage']['catalog_cost_estimate_usd'], 0.5)
        self.assertEqual(shown['generation_usage'],
                         {k: v for k, v in saved['generation_usage'].items() if k != 'sources'})
        self.assertEqual(len(f.calls()), before)
        # A construction-only summary still traces both cohorts to the same originals.
        source = self.source(dict(construction=['reuse_one', 'reuse_two']))
        self.summarize(source, output='reuse-summary.json')
        reuse = json.loads((self.root / 'reuse-summary.json').read_text())
        self.assertEqual(reuse['totals']['catalog_cost_estimate_usd'], 0)
        self.assertEqual(reuse['generation_usage']['catalog_cost_estimate_usd'], 0.5)
        self.assertEqual(reuse['generation_usage']['source_calls_added'], 2)

    def test_cli_costs_keep_unknown_failed_usage_and_known_subtotal(self):
        f = self.fixture
        f.prepare('known')
        f.cli('run', 'known', env={'FAKE_RUNNER_RESULT_OVERRIDE': json.dumps({
            'usage': {'input': 100, 'output': 20, 'cost': {'total': 0.25}}})})
        f.prepare('unknown', '--repeat')
        f.cli('run', 'unknown', env={'FAKE_RUNNER_FAIL_STAGE': 'prompt'}, ok=False)
        self.summarize(self.source(dict(stage=['known', 'unknown'])))
        saved = json.loads((self.root / 'summary.json').read_text())
        for usage in (saved['totals'], saved['generation_usage']):
            self.assertIsNone(usage['catalog_cost_estimate_usd'])
            self.assertEqual(usage['known_catalog_cost_estimate_usd'], 0.5)
            self.assertEqual(usage['attempts_without_cost_estimate'], 2)
            self.assertEqual(usage['attempts_without_usage'], 2)
        self.assertFalse(saved['generation_usage']['usage_complete'])

    def test_cli_totals_local_native_usage_and_reuses_without_double_counting(self):
        f = self.fixture
        f.prepare('generation')
        f.cli('run', 'generation')
        f.cli('prepare', 'reuse', '--from', 'generation')
        f.cli('run', 'reuse')
        f.prepare('unfinished', '--repeat')
        f.cli('run', 'unfinished', '--max-new-attempts', '1', ok=False)
        calls = len(f.calls())
        source = self.source(dict(generation=['generation'], construction=['reuse'], diagnostics=['unfinished']))
        result = self.summarize(source)
        shown = json.loads(result.stdout)
        saved = json.loads((self.root / 'summary.json').read_text())
        self.assertEqual(saved['totals']['attempts'], 3)
        self.assertEqual(saved['totals']['reused'], 2)
        self.assertEqual(saved['totals']['known_input_tokens'], 300)
        self.assertEqual(saved['totals']['known_output_tokens'], 60)
        self.assertEqual(saved['totals']['known_reasoning_tokens'], 15)
        self.assertTrue(saved['reasoning_included_in_output'])
        self.assertEqual(saved['groups']['diagnostics']['totals']['unrun'], 1)
        self.assertEqual(shown['totals'], saved['totals'])
        self.assertNotIn('cases', saved['groups']['generation']['experiments'][0])
        self.assertFalse(saved['complete'])
        self.assertEqual(len(f.calls()), calls)
        self.summarize(source, ok=False)

    def test_recovered_retry_keeps_failed_attempt_and_unknown_usage(self):
        f = self.fixture
        f.prepare()
        f.cli('run', 'E1', env={'FAKE_RUNNER_FAILURES': json.dumps({'Tea':
            dict(attempts=1, metadata=dict(http_status=200,
                error=dict(code=504, message='Upstream idle timeout exceeded')))})})
        f.prepare('unknown', '--repeat')
        f.cli('run', 'unknown', env={'FAKE_RUNNER_FAIL_STAGE': 'prompt'}, ok=False)
        source = self.source(dict(arbitrary_stage=['E1', 'unknown']))
        self.summarize(source)
        saved = json.loads((self.root / 'summary.json').read_text())
        self.assertEqual(saved['totals']['attempts'], 5)
        self.assertEqual(saved['totals']['failed_attempts'], 3)
        self.assertEqual(saved['totals']['recovered_failed_attempts'], 1)
        self.assertEqual(saved['totals']['retry_attempts'], 1)
        self.assertEqual(saved['totals']['attempts_without_usage'], 2)
        self.assertFalse(saved['usage_complete'])
        self.assertEqual(saved['totals']['known_output_tokens'], 60)

    def test_budget_snapshot_uses_explicit_groups_and_never_refunds_delta(self):
        f = self.fixture
        f.prepare('generation')
        f.cli('run', 'generation')
        budget = f.write('budget.json', dict(schema_version=1, limit=10, used=0))
        f.prepare('charged', '--repeat')
        f.cli('run', 'charged', '--attempt-budget', budget)
        source = self.source(dict(generation=['generation'], charged=['charged']),
            dict(path='budget.json', groups=['charged']))
        before = budget.read_bytes()
        self.summarize(source)
        saved = json.loads((self.root / 'summary.json').read_text())
        self.assertEqual(saved['attempt_budget']['counted_attempts'], 2)
        self.assertEqual(saved['attempt_budget']['used'], 2)
        self.assertEqual(saved['attempt_budget']['status'], 'reconciled')
        self.assertEqual(budget.read_bytes(), before)
        value = json.loads(before)
        value['used'] = 4
        budget.write_text(json.dumps(value))
        before = budget.read_bytes()
        self.summarize(source, output='delta.json')
        saved = json.loads((self.root / 'delta.json').read_text())
        self.assertEqual(saved['attempt_budget']['delta'], 2)
        self.assertEqual(saved['attempt_budget']['status'], 'unreconciled')
        self.assertIn('omitted experiments', saved['attempt_budget']['explanation'])
        self.assertEqual(budget.read_bytes(), before)

    def test_duplicate_canonical_experiment_is_rejected_across_groups(self):
        self.fixture.prepare()
        (self.root / 'alias').symlink_to(self.root / 'E1', target_is_directory=True)
        source = self.source(dict(one=['E1'], two=['alias']))
        result = self.summarize(source, ok=False)
        self.assertIn('duplicate canonical experiment', result.stderr)
        self.assertFalse((self.root / 'summary.json').exists())

    def test_imported_historical_usage_is_flagged_and_excluded_from_new_totals(self):
        f = self.fixture
        f.prepare('original')
        f.cli('run', 'original')
        f.prepare('imported', '--import-config', 'original/runner-config.json')
        source = self.source(dict(history=['imported']))
        self.summarize(source)
        saved = json.loads((self.root / 'summary.json').read_text())
        historical = saved['groups']['history']['experiments'][0]
        self.assertTrue(historical['imported'])
        self.assertEqual(historical['historical_totals']['attempts'], 2)
        self.assertEqual(saved['totals']['attempts'], 0)
        self.assertEqual(saved['totals']['known_input_tokens'], 0)
        self.assertEqual(saved['totals']['catalog_cost_estimate_usd'], 0)
        self.assertEqual(saved['generation_usage']['original_calls'], 0)
        self.assertFalse(saved['complete'])
        self.assertEqual(len(f.calls()), 2)

    def test_same_native_run_alias_is_rejected_even_with_distinct_experiment_manifests(self):
        f = self.fixture
        f.prepare('original')
        f.cli('run', 'original')
        f.prepare('imported', '--import-config', 'original/runner-config.json')
        source = self.source(dict(first=['original'], alias=['imported']))
        result = self.summarize(source, ok=False)
        self.assertIn('duplicate native run-directory alias', result.stderr)
        self.assertFalse((self.root / 'summary.json').exists())

    def test_model_settings_breakdown_and_counter_negative_delta_remain_explicit(self):
        f = self.fixture
        f.prepare('first')
        f.cli('run', 'first')
        f.cli('prepare', 'second', '--from', 'first', '--model', 'fixture/other', '--reasoning', 'medium')
        f.cli('run', 'second')
        f.write('budget.json', dict(schema_version=1, limit=10, used=1))
        source = self.source(dict(all_calls=['first', 'second']), dict(path='budget.json', groups=['all_calls']))
        self.summarize(source)
        saved = json.loads((self.root / 'summary.json').read_text())
        models = {row['settings']['model']: row for row in saved['models']}
        self.assertEqual(set(models), {'fixture/model', 'fixture/other'})
        self.assertEqual(models['fixture/other']['settings']['reasoning_effort'], 'medium')
        self.assertEqual(models['fixture/other']['totals']['attempts'], 2)
        self.assertNotIn('auth_file', models['fixture/other']['settings'])
        self.assertEqual(saved['attempt_budget']['delta'], -3)
        self.assertEqual(saved['attempt_budget']['status'], 'unreconciled')
        self.assertEqual(json.loads((self.root / 'budget.json').read_text())['used'], 1)

    def test_tampered_native_receipt_fails_before_writing_summary(self):
        f = self.fixture
        f.prepare()
        f.cli('run', 'E1')
        ledger = self.root / 'E1' / 'run' / 'results.jsonl'
        records = [json.loads(line) for line in ledger.read_text().splitlines()]
        records[0]['usage']['input_tokens'] += 1
        ledger.write_text(''.join(json.dumps(record) + '\n' for record in records))
        source = self.source(dict(native=['E1']))
        self.summarize(source, ok=False)
        self.assertFalse((self.root / 'summary.json').exists())
        self.assertEqual(len(f.calls()), 2)

    def test_invalid_budget_and_unknown_budget_groups_fail_closed(self):
        f = self.fixture
        f.prepare()
        f.write('budget.json', dict(schema_version=1, limit=3, used=4))
        source = self.source(dict(native=['E1']), dict(path='budget.json', groups=['native']))
        self.summarize(source, ok=False)
        self.assertFalse((self.root / 'summary.json').exists())
        source = self.source(dict(native=['E1']), dict(path='budget.json', groups=['missing']))
        result = self.summarize(source, ok=False)
        self.assertIn('distinct existing summary groups', result.stderr)
        self.assertEqual(f.calls(), [])

    def test_sdk_zero_failed_usage_remains_unknown_not_known_zero(self):
        f = self.fixture
        f.prepare()
        f.cli('run', 'E1', ok=False, env={
            'FAKE_RUNNER_RESULT_OVERRIDE': json.dumps(dict(usage=dict(input=0, output=0, cacheRead=0))),
            'FAKE_RUNNER_FAILURES': json.dumps({'GENERIC PROMPT':
                dict(metadata=dict(http_status=200), error='terminated')})})
        source = self.source(dict(failed=['E1']))
        self.summarize(source)
        saved = json.loads((self.root / 'summary.json').read_text())
        self.assertEqual(saved['totals']['attempts'], 2)
        self.assertEqual(saved['totals']['attempts_without_usage'], 2)
        self.assertEqual(saved['totals']['known_input_tokens'], 0)
        self.assertFalse(saved['usage_complete'])
        self.assertTrue(saved['warnings'])
