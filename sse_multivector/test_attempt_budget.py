"""Cross-experiment attempt limits through the real shared runner CLI."""
import json
from concurrent.futures import ThreadPoolExecutor
import unittest

from sse_multivector import test_experiment as fixtures
from sse_multivector.extraction_pipeline import NewJobLimitReached, PersistentAttemptBudget


class AttemptBudgetTests(unittest.TestCase):
    setUp = fixtures.ExperimentTests.setUp
    write = fixtures.ExperimentTests.write
    cli = fixtures.ExperimentTests.cli
    prepare = fixtures.ExperimentTests.prepare
    show = fixtures.ExperimentTests.show
    calls = fixtures.ExperimentTests.calls

    def test_one_budget_counts_new_attempts_across_runs_but_not_reuse(self):
        self.write('budget.json', dict(schema_version=1, limit=2, used=0))
        self.prepare('first')
        self.cli('run', 'first', '--attempt-budget', 'budget.json')
        self.assertEqual(len(self.calls()), 2)
        self.assertEqual(json.loads((self.root / 'budget.json').read_text())['used'], 2)
        self.cli('prepare', 'cached', '--from', 'first')
        self.cli('run', 'cached', '--attempt-budget', 'budget.json')
        self.assertEqual(len(self.calls()), 2)
        self.cli('prepare', 'independent', '--from', 'first', '--repeat')
        self.cli('run', 'independent', '--attempt-budget', 'budget.json', ok=False)
        self.assertEqual(len(self.calls()), 2)
        self.assertEqual(self.show('independent')['summary']['unrun'], 2)

    def test_failed_model_attempt_is_not_refunded(self):
        self.write('budget.json', dict(schema_version=1, limit=1, used=0))
        self.prepare('first')
        self.cli('run', 'first', '--attempt-budget', 'budget.json', ok=False,
                 env={'FAKE_RUNNER_FAIL_STAGE': 'prompt'})
        self.assertEqual(json.loads((self.root / 'budget.json').read_text())['used'], 1)
        self.cli('prepare', 'second', '--from', 'first', '--repeat')
        self.cli('run', 'second', '--attempt-budget', 'budget.json', ok=False)
        self.assertEqual(json.loads((self.root / 'budget.json').read_text())['used'], 1)

    def test_concurrent_claims_cannot_exceed_one_shared_limit(self):
        self.write('budget.json', dict(schema_version=1, limit=7, used=0))

        def claim(index):
            try:
                PersistentAttemptBudget(self.root / 'budget.json').claim(str(index))
                return True
            except NewJobLimitReached:
                return False

        with ThreadPoolExecutor(max_workers=8) as pool:
            accepted = list(pool.map(claim, range(30)))
        self.assertEqual(sum(accepted), 7)
        self.assertEqual(json.loads((self.root / 'budget.json').read_text())['used'], 7)
        claims = [json.loads(line) for line in
                  (self.root / 'budget.json.claims.jsonl').read_text().splitlines()]
        self.assertEqual([c['ordinal'] for c in claims], list(range(1, 8)))


if __name__ == '__main__':
    unittest.main()
