"""Bounded automatic continuation through the native CLI and offline runner."""
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from sse_multivector import test_experiment as fixtures
from sse_multivector import test_canonical_trial as roots_fixtures
from sse_multivector import canonical_continuation as continuation
from sse_multivector import canonical_trial
from sse_multivector import extraction_pipeline as engine


class CanonicalContinuationTests(unittest.TestCase):
    setUp = fixtures.ExperimentTests.setUp
    write = fixtures.ExperimentTests.write
    cli = fixtures.ExperimentTests.cli
    calls = fixtures.ExperimentTests.calls
    setup_trial = roots_fixtures.CanonicalTrialTests.setup_trial
    state = roots_fixtures.CanonicalTrialTests.state
    answer = roots_fixtures.CanonicalTrialTests.answer
    advance = roots_fixtures.CanonicalTrialTests.advance

    def dynamic_runner(self):
        # Only the offline transport is replaced; CLI preparation, validation,
        # budget claims, receipts and every construction transition are real.
        self.runner.write_text(self.runner.read_text().replace(
            'elif stage == "takeaway":', '''    payload = json.loads(prompt.removeprefix("GENERIC PROMPT "))
    local = payload["local"]
    meaning = local.get("meaning", local["entry"]["subject"] + " fixed meaning")
    answer = {"meaning": meaning}
    if "canonical" in payload:
        relations = json.loads(os.environ.get("FIXTURE_RELATIONS", "{}"))
        relation = relations.get(local["entry"]["subject"], {}).get(
            payload["canonical"]["id"], os.environ.get("FIXTURE_RELATION", "neither"))
        answer.update(relation=relation, reason="Offline relation fixture")
        if os.environ.get("FIXTURE_CHANGED_MEANING"):
            answer["meaning"] += " changed"
    output_text = json.dumps(answer)
elif stage == "takeaway":'''))

    def shared(self, limit=100, used=0):
        self.write('shared.json', dict(schema_version=1, limit=limit, used=used))

    def continue_trial(self, nodes=3, attempts=3, directory='trial', **kwargs):
        return self.cli('continue-canonical-trial', directory, '--max-nodes', str(nodes),
                        '--max-new-attempts', str(attempts), '--attempt-budget', 'shared.json',
                        **kwargs)

    def test_native_continuation_completes_without_fictional_semantic_approval(self):
        self.setup_trial(same_note=True, schema_version=2, independent_meanings=True)
        self.write('shared.json', dict(schema_version=1, limit=100, used=0))
        result = json.loads(self.continue_trial(env={
            'FAKE_RUNNER_PROMPT_RESPONSE': '{"meaning":"Fixed source meaning"}'}).stdout)
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(result['semantic_review'], 'pending')
        self.assertEqual(self.state()['index'], 3)
        self.assertEqual(len(self.state()['nodes']), 3)
        self.assertTrue(all(step['reviewer'] == 'automatic' and
                            step['semantic_review'] == 'pending'
                            for step in self.state()['steps']))
        self.assertEqual(len(self.calls()), 3)
        self.assertEqual(json.loads((self.root / 'shared.json').read_text())['used'], 3)
        self.assertEqual(result['attempts']['used'], 3)

    def test_fixed_meanings_and_all_neither_relations_complete_through_native_path(self):
        self.dynamic_runner()
        self.setup_trial(schema_version=2, independent_meanings=True)
        self.shared()
        result = json.loads(self.continue_trial(attempts=6).stdout)
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(len(self.calls()), 6)
        state = self.state()
        self.assertEqual([n['meaning'] for n in state['nodes']],
                         ['Cooking fixed meaning', 'Food fixed meaning', 'Ingredients fixed meaning'])
        self.assertTrue(all(n['parents'] == [] for n in state['nodes']))
        for step in state['steps']:
            self.assertEqual(step['selected_meaning'], step['local_meaning_from']['meaning'])
            self.assertEqual(step['local_meaning_from']['semantic_review'], 'pending')
        plan = json.loads((self.root / 'trial/continuation/plan.json').read_text())['plan']
        self.assertEqual(plan['maximum_first_attempt_requests'], 6)

    def test_persistent_local_cap_stops_pending_comparison_and_cannot_reset_on_resume(self):
        self.dynamic_runner()
        self.setup_trial(schema_version=2, independent_meanings=True)
        self.shared()
        first = json.loads(self.continue_trial(attempts=2, ok=False).stdout)
        self.assertEqual(first['status'], 'attempt_limit')
        self.assertEqual((self.state()['index'], self.state()['phase']), (1, 'comparison'))
        self.assertEqual(len(self.state()['steps']), 1)
        before = self.state()
        # Another worker's launch changes the shared counter, not this cap.
        engine.PersistentAttemptBudget(self.root / 'shared.json').claim('other-worker')
        resumed = json.loads(self.continue_trial(attempts=2, ok=False).stdout)
        self.assertEqual(resumed['attempts']['used'], 2)
        self.assertEqual(self.state(), before)
        self.assertEqual(len(self.calls()), 2)
        self.assertEqual(json.loads((self.root / 'shared.json').read_text())['used'], 3)
        self.assertIn('cannot change', self.continue_trial(attempts=3, ok=False).stderr)
        self.assertIn('cannot change', self.continue_trial(nodes=2, attempts=2, ok=False).stderr)

    def test_global_cap_is_preserved_and_pending_meaning_not_held(self):
        self.dynamic_runner()
        self.setup_trial(schema_version=2, independent_meanings=True)
        self.shared(limit=1)
        result = json.loads(self.continue_trial(attempts=10, ok=False).stdout)
        self.assertEqual(result['status'], 'attempt_limit')
        self.assertEqual(self.state()['index'], 1)
        self.assertEqual(self.state()['phase'], 'meaning')
        self.assertEqual(self.state()['steps'][0]['status'], 'added')
        self.assertEqual(len(self.calls()), 1)
        self.assertEqual(result['shared_remaining'], 0)
        self.assertEqual(result['attempts']['used'], 1)

    def test_node_bound_does_not_start_next_meaning_or_descend_to_children(self):
        self.dynamic_runner()
        self.setup_trial(schema_version=2, independent_meanings=True)
        self.shared()
        result = json.loads(self.continue_trial(nodes=1, attempts=10).stdout)
        self.assertEqual(result['status'], 'node_limit')
        self.assertEqual(self.state()['index'], 1)
        self.assertEqual(len(self.calls()), 1)
        self.assertNotIn('children', self.state())
        self.continue_trial(nodes=1, attempts=10)
        self.assertEqual(len(self.calls()), 1)

    def test_receipt_reuse_can_finish_after_both_counters_exhausted(self):
        self.dynamic_runner()
        self.setup_trial(same_note=True, schema_version=2, independent_meanings=True)
        for number in ('2', '3'):
            config = json.loads((self.root / 'trial.json').read_text())
            config.pop('note_ids')
            config['roots'] = [{'note_id': 'n1', 'number': number}]
            self.write('cached-' + number + '.json', config)
            self.cli('prepare-canonical-trial', 'cached-' + number,
                     '--spec', 'cached-' + number + '.json')
            cached = json.loads((self.root / ('cached-' + number) / 'state.json').read_text())
            self.cli('run', cached['experiment'])
        self.shared(limit=1)
        result = json.loads(self.continue_trial(attempts=1).stdout)
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(len(self.calls()), 3)
        self.assertEqual(result['attempts']['used'], 1)
        self.assertEqual([s['answers'][0]['reused'] for s in self.state()['steps']], [False, True, True])

    def test_terminal_unknown_failures_hold_without_retry_or_fake_meaning(self):
        self.setup_trial(same_note=True, schema_version=2, independent_meanings=True)
        self.shared()
        result = json.loads(self.continue_trial(env={'FAKE_RUNNER_FAIL_STAGE': 'prompt'}).stdout)
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(len(self.calls()), 3)
        self.assertEqual(self.state()['nodes'], [])
        self.assertEqual(self.state()['local_meanings'], {})
        self.assertTrue(all(s['status'] == 'held' and s['selected_meaning'] is None
                            and s['answers'][0]['failure_kind'] == 'unknown'
                            for s in self.state()['steps']))
        self.continue_trial(env={'FAKE_RUNNER_FAIL_STAGE': 'prompt'})
        self.assertEqual(len(self.calls()), 3)

    def test_provider_fatal_stops_without_disposing_or_retrying_current_node(self):
        self.dynamic_runner()
        self.setup_trial(schema_version=2, independent_meanings=True)
        self.shared()
        env = {'FAKE_RUNNER_FAILURES': json.dumps({
            'GENERIC PROMPT': {'metadata': {'http_status': 403}, 'error': 'Forbidden'}})}
        result = json.loads(self.continue_trial(ok=False, env=env).stdout)
        self.assertEqual(result['status'], 'provider_fatal')
        self.assertEqual(self.state()['index'], 0)
        self.assertEqual(self.state()['steps'], [])
        self.continue_trial(ok=False, env=env)
        self.assertEqual(len(self.calls()), 1)

    def test_admission_limit_during_provider_retry_stays_pending_on_resume(self):
        self.dynamic_runner()
        self.setup_trial(schema_version=2, independent_meanings=True)
        self.shared()
        env = {'FAKE_RUNNER_FAILURES': json.dumps({
            'GENERIC PROMPT': {'metadata': {'http_status': 429}, 'error': 'Rate limited'}})}
        first = json.loads(self.continue_trial(nodes=1, attempts=1, ok=False, env=env).stdout)
        self.assertEqual(first['status'], 'attempt_limit')
        self.assertEqual(self.state()['index'], 0)
        resumed = json.loads(self.continue_trial(nodes=1, attempts=1, ok=False, env=env).stdout)
        self.assertEqual(resumed['status'], 'attempt_limit')
        self.assertEqual(self.state()['steps'], [])
        self.assertEqual(len(self.calls()), 1)

    def test_native_provider_retry_counts_once_in_each_persistent_budget(self):
        self.dynamic_runner()
        self.setup_trial(schema_version=2, independent_meanings=True)
        self.shared()
        env = {'FAKE_RUNNER_FAILURES': json.dumps({
            'GENERIC PROMPT': {'metadata': {'http_status': 429}, 'error': 'Rate limited', 'attempts': 1}})}
        result = json.loads(self.continue_trial(nodes=1, attempts=2, env=env).stdout)
        self.assertEqual(result['status'], 'node_limit')
        self.assertEqual(self.state()['steps'][0]['status'], 'added')
        self.assertEqual(result['attempts']['used'], 2)
        self.assertEqual(json.loads((self.root / 'shared.json').read_text())['used'], 2)
        self.assertEqual(len(self.calls()), 2)

    def test_two_failed_provider_attempts_are_terminal_and_never_retried_by_continuation(self):
        self.dynamic_runner()
        self.setup_trial(schema_version=2, independent_meanings=True)
        self.shared()
        env = {'FAKE_RUNNER_FAILURES': json.dumps({
            'GENERIC PROMPT': {'metadata': {'http_status': 429}, 'error': 'Rate limited'}})}
        self.continue_trial(nodes=1, attempts=2, env=env)
        self.assertEqual(self.state()['steps'][0]['status'], 'held')
        self.continue_trial(nodes=1, attempts=2, env=env)
        self.assertEqual(len(self.calls()), 2)

    def test_invalid_success_receipt_stops_before_any_transition(self):
        self.setup_trial(schema_version=2, independent_meanings=True)
        self.answer({'meaning': 'Saved meaning'})
        ledger = Path(self.state()['experiment']) / 'run/results.jsonl'
        record = json.loads(ledger.read_text())
        record['prompt_sha256'] = '0' * 64
        ledger.write_text(json.dumps(record) + '\n')
        self.shared()
        result = json.loads(self.continue_trial(ok=False).stdout)
        self.assertEqual(result['status'], 'invalid_receipt')
        self.assertEqual(self.state()['index'], 0)
        self.assertEqual(len(self.calls()), 1)

    def test_failed_receipt_with_wrong_request_cannot_be_automatically_held(self):
        self.setup_trial(schema_version=2, independent_meanings=True)
        self.cli('run', self.state()['experiment'], ok=False,
                 env={'FAKE_RUNNER_FAIL_STAGE': 'prompt'})
        ledger = Path(self.state()['experiment']) / 'run/results.jsonl'
        record = json.loads(ledger.read_text())
        record['request_sha256'] = '0' * 64
        ledger.write_text(json.dumps(record) + '\n')
        self.shared()
        result = json.loads(self.continue_trial(ok=False).stdout)
        self.assertEqual(result['status'], 'invalid_receipt')
        self.assertEqual(self.state()['steps'], [])
        self.assertEqual(len(self.calls()), 1)

    def test_null_meaning_is_held_by_existing_guard(self):
        self.setup_trial(same_note=True, schema_version=2, independent_meanings=True)
        self.shared()
        self.continue_trial(env={'FAKE_RUNNER_PROMPT_RESPONSE': '{"meaning":null}'})
        self.assertEqual(len(self.calls()), 3)
        self.assertEqual(self.state()['nodes'], [])
        self.assertTrue(all(s['reason'] == 'uncertain meaning or relationship'
                            for s in self.state()['steps']))

    def test_uncertainty_and_copy_mismatch_preserve_existing_graph(self):
        self.dynamic_runner()
        self.setup_trial(schema_version=2, independent_meanings=True)
        self.shared()
        self.continue_trial(attempts=6, env={'FIXTURE_RELATION': 'uncertain'})
        state = self.state()
        self.assertEqual(len(state['nodes']), 1)
        self.assertEqual([s['status'] for s in state['steps']], ['added', 'held', 'held'])
        self.assertTrue(all(s['after'] == s['before'] for s in state['steps'][1:]))

    def test_copy_mismatch_is_held_without_rewriting_frozen_meaning(self):
        self.dynamic_runner()
        self.setup_trial(schema_version=2, independent_meanings=True)
        self.shared()
        self.continue_trial(attempts=6, env={'FIXTURE_CHANGED_MEANING': '1'})
        self.assertEqual(len(self.state()['nodes']), 1)
        self.assertTrue(all('copy' in s['reason'] for s in self.state()['steps'][1:]))
        self.assertEqual(self.state()['local_meanings']['1']['meaning'], 'Food fixed meaning')

    def test_both_transitive_consequences_are_checked_by_existing_advance(self):
        self.dynamic_runner()
        self.setup_trial(schema_version=2, independent_meanings=True)
        self.shared()
        # C001 contains C002. The incoming C003 cannot contain C001 while
        # remaining unrelated to C002; it would acquire C002 as a descendant.
        relations = {'Food': {'C001': 'canonical_contains_local'},
                     'Ingredients': {'C001': 'local_contains_canonical', 'C002': 'neither'}}
        self.continue_trial(attempts=6, env={'FIXTURE_RELATIONS': json.dumps(relations)})
        step = self.state()['steps'][-1]
        self.assertEqual(step['status'], 'held')
        self.assertIn('contradiction at C002', step['reason'])
        self.assertEqual(step['before'], step['after'])

    def test_ancestor_consequence_is_checked_by_existing_advance(self):
        self.dynamic_runner()
        self.setup_trial(schema_version=2, independent_meanings=True)
        self.shared()
        relations = {'Food': {'C001': 'canonical_contains_local'},
                     'Ingredients': {'C001': 'neither', 'C002': 'canonical_contains_local'}}
        self.continue_trial(attempts=6, env={'FIXTURE_RELATIONS': json.dumps(relations)})
        step = self.state()['steps'][-1]
        self.assertEqual(step['status'], 'held')
        self.assertIn('contradiction at C001', step['reason'])
        self.assertEqual(step['before'], step['after'])

    def test_current_producer_rejection_holds(self):
        self.setup_trial(same_note=True, schema_version=2, independent_meanings=True)
        self.answer({'meaning': 'Reviewed meaning'})
        self.cli('review', self.state()['experiment'], '--case', 'bootstrap', '--role', 'agent',
                 '--verdict', 'reject', '--comment', 'Missing established source restriction')
        self.shared()
        self.continue_trial(env={'FAKE_RUNNER_PROMPT_RESPONSE': '{"meaning":"Other meaning"}'})
        self.assertEqual(self.state()['steps'][0]['status'], 'held')
        self.assertIn('producer review', self.state()['steps'][0]['reason'])
        self.assertEqual(len(self.state()['nodes']), 2)

    def test_stale_output_bound_review_does_not_hold_the_new_output(self):
        self.setup_trial(same_note=True, schema_version=2, independent_meanings=True)
        self.answer({'meaning': 'Reviewed meaning'})
        self.cli('review', self.state()['experiment'], '--case', 'bootstrap', '--role', 'agent',
                 '--verdict', 'reject', '--comment', 'Stale output assessment')
        path = Path(self.state()['experiment']) / 'reviews.jsonl'
        record = json.loads(path.read_text())
        record['output_sha256'] = '0' * 64
        path.write_text(json.dumps(record) + '\n')
        self.shared()
        self.continue_trial(env={'FAKE_RUNNER_PROMPT_RESPONSE': '{"meaning":"Other meaning"}'})
        self.assertEqual(self.state()['steps'][0]['status'], 'added')
        self.assertEqual(len(self.state()['nodes']), 3)

    def test_reused_meaning_keeps_exact_source_producer_rejection(self):
        self.dynamic_runner()
        self.setup_trial(same_note=True, schema_version=2, independent_meanings=True)
        config = json.loads((self.root / 'trial.json').read_text())
        config.pop('note_ids')
        config['roots'] = [{'note_id': 'n1', 'number': '2'}]
        self.write('producer.json', config)
        self.cli('prepare-canonical-trial', 'producer', '--spec', 'producer.json')
        producer = json.loads((self.root / 'producer/state.json').read_text())
        self.cli('run', producer['experiment'])
        self.cli('review', producer['experiment'], '--case', 'bootstrap', '--role', 'agent',
                 '--verdict', 'reject', '--comment', 'Known missing cooking-purpose limit')
        self.shared()
        self.continue_trial()
        step = self.state()['steps'][1]
        self.assertTrue(step['answers'][0]['reused'])
        self.assertEqual(step['status'], 'held')
        self.assertIn('Known missing cooking-purpose limit', step['reason'])
        self.assertEqual(len(self.state()['nodes']), 2)

    def test_mapped_parent_exception_is_compared_even_with_single_note_parent(self):
        self.dynamic_runner()
        self.setup_trial(schema_version=2, independent_meanings=True)
        self.shared()
        self.continue_trial(attempts=6)
        before = self.state()
        self.cli('prepare-canonical-child-trial', 'children', '--base-trial', 'trial')
        relations = {'EXCLUDED CHILD': {'C001': 'canonical_contains_local'}}
        result = json.loads(self.continue_trial(directory='children', nodes=1, attempts=4,
                                               env={'FIXTURE_RELATIONS': json.dumps(relations)}).stdout)
        self.assertEqual(result['status'], 'complete')
        state = json.loads((self.root / 'children/state.json').read_text())
        step = state['steps'][-1]
        self.assertEqual(step['mapped_parent'], 'C001')
        self.assertEqual([c['id'] for c in step['answers']], ['C001', 'C002', 'C003'])
        self.assertEqual(state['nodes'][-1]['parents'], ['C001'])
        self.assertEqual(self.state(), before)

    def test_mapped_parent_mismatch_holds_child_and_keeps_completed_base(self):
        self.dynamic_runner()
        self.setup_trial(schema_version=2, independent_meanings=True)
        self.shared()
        self.continue_trial(attempts=6)
        before = self.state()
        self.cli('prepare-canonical-child-trial', 'children', '--base-trial', 'trial')
        self.continue_trial(directory='children', nodes=1, attempts=4)
        state = json.loads((self.root / 'children/state.json').read_text())
        self.assertEqual(state['nodes'], before['nodes'])
        self.assertEqual(state['steps'][-1]['status'], 'held')
        self.assertIn('mapped canonical parent', state['steps'][-1]['reason'])

    def test_multiple_equivalents_require_hold_without_merging_existing_nodes(self):
        self.dynamic_runner()
        self.setup_trial(schema_version=2, independent_meanings=True)
        self.shared()
        relations = {'Ingredients': {'C001': 'equivalent', 'C002': 'equivalent'}}
        self.continue_trial(attempts=6, env={'FIXTURE_RELATIONS': json.dumps(relations)})
        step = self.state()['steps'][-1]
        self.assertEqual(step['status'], 'held')
        self.assertIn('multiple canonical equivalents', step['reason'])
        self.assertEqual(step['before'], step['after'])

    def test_cycle_is_held_without_changing_graph(self):
        self.dynamic_runner()
        self.setup_trial(schema_version=2, independent_meanings=True)
        self.shared()
        relations = {'Food': {'C001': 'canonical_contains_local'},
                     'Ingredients': {'C001': 'equivalent', 'C002': 'canonical_contains_local'}}
        self.continue_trial(attempts=6, env={'FIXTURE_RELATIONS': json.dumps(relations)})
        step = self.state()['steps'][-1]
        self.assertEqual(step['reason'], 'proposed placement creates a cycle')
        self.assertEqual(step['before'], step['after'])

    def test_equivalence_substitution_checks_a_settled_pair_in_both_orientations(self):
        self.dynamic_runner()
        self.setup_trial(schema_version=2, independent_meanings=True)
        self.shared()
        relations = {'Ingredients': {'C001': 'equivalent',
                                      'C002': 'canonical_contains_local'}}
        result = json.loads(self.continue_trial(attempts=6, env={
            'FIXTURE_RELATIONS': json.dumps(relations)}).stdout)
        state = self.state()
        self.assertEqual(result['status'], 'complete')
        step = state['steps'][-1]
        self.assertEqual(step['status'], 'held')
        self.assertEqual(step['before'], step['after'])
        witness = step['equivalence_contradiction']
        self.assertEqual(witness['equivalent_to'], 'C001')
        self.assertEqual(witness['other'], 'C002')
        self.assertEqual(witness['previous_answer']['id'], 'C001')
        self.assertEqual(witness['previous_relation'], 'neither')
        self.assertEqual(witness['current_relation'], 'canonical_contains_local')
        self.assertEqual(step['reviewer'], 'automatic')
        self.assertEqual(step['semantic_review'], 'pending')
        self.assertEqual(len(self.calls()), 6)
        self.assertEqual(result['attempts']['used'], 6)
        self.assertEqual(json.loads((self.root / 'shared.json').read_text())['used'], 6)

    def test_equivalence_preserves_compatible_history_despite_different_local_context(self):
        self.dynamic_runner()
        self.setup_trial(schema_version=2, independent_meanings=True)
        self.shared()
        relations = {'Ingredients': {'C001': 'equivalent', 'C002': 'neither'}}
        self.continue_trial(attempts=6, env={'FIXTURE_RELATIONS': json.dumps(relations)})
        state = self.state()
        step = state['steps'][-1]
        self.assertEqual(step['status'], 'equivalent')
        self.assertNotIn('equivalence_contradiction', step)
        self.assertEqual(state['nodes'][0]['meaning'], 'Cooking fixed meaning')
        self.assertEqual(state['nodes'][0]['entries'], [
            {'note_id': 'n1', 'number': '1'}, {'note_id': 'n3', 'number': '3'}])
        self.assertEqual(state['nodes'][0]['parents'], [])
        self.assertEqual(state['nodes'][1]['parents'], [])

    def test_equivalence_checks_old_pairs_excluded_from_the_current_comparisons(self):
        self.dynamic_runner()
        self.setup_trial(schema_version=2, independent_meanings=True, extra_root=True)
        corpus = json.loads((self.root / 'notes.json').read_text())
        corpus['notes'][0]['subjects'].append({
            'number': '4', 'subject': 'Extra branch', 'context': 'A narrower fixed topic'})
        self.write('notes.json', corpus)
        config = json.loads((self.root / 'trial.json').read_text())
        del config['note_ids']
        config['roots'] = [{'note_id': 'n1', 'number': '1'},
                           {'note_id': 'n2', 'number': '2'},
                           {'note_id': 'n1', 'number': '4'},
                           {'note_id': 'n2', 'number': '3'}]
        self.write('branches.json', config)
        self.cli('prepare-canonical-trial', 'branches', '--spec', 'branches.json')
        self.shared()
        # C001 and C002 are unrelated. C003 is placed beneath C002 without
        # comparing same-note C001. Equivalence with C001 now places it under
        # C003 and hence C002, which is excluded from this incoming comparison.
        relations = {'Extra branch': {'C002': 'canonical_contains_local'},
                     'Other root': {'C001': 'equivalent',
                                    'C003': 'canonical_contains_local'}}
        self.continue_trial(nodes=4, attempts=8, directory='branches', env={
            'FIXTURE_RELATIONS': json.dumps(relations)})
        state = json.loads((self.root / 'branches/state.json').read_text())
        step = state['steps'][-1]
        self.assertEqual([answer['id'] for answer in step['answers']], ['C001', 'C003'])
        self.assertEqual(step['status'], 'held')
        self.assertEqual(step['before'], step['after'])
        witness = step['equivalence_contradiction']
        self.assertEqual(witness['equivalent_to'], 'C001')
        self.assertEqual(witness['other'], 'C002')
        self.assertEqual(witness['previous_relation'], 'neither')
        self.assertEqual(witness['current_relation'], 'canonical_contains_local')
        self.assertEqual(len(self.calls()), 8)

    def test_held_pair_answers_do_not_constrain_a_later_equivalence(self):
        self.dynamic_runner()
        self.setup_trial(schema_version=2, independent_meanings=True, extra_root=True)
        self.shared()
        # The second local root is held for uncertainty. Its valid-looking
        # partial relationship never establishes a canonical pair constraint.
        relations = {'Food': {'C001': 'uncertain'},
                     'Other root': {'C001': 'neither'},
                     'Ingredients': {'C001': 'equivalent', 'C003': 'neither'}}
        self.continue_trial(nodes=4, attempts=10, env={
            'FIXTURE_RELATIONS': json.dumps(relations)})
        state = self.state()
        self.assertEqual([step['status'] for step in state['steps']],
                         ['added', 'held', 'added', 'equivalent'])
        self.assertNotIn('equivalence_contradiction', state['steps'][-1])
        self.assertEqual(state['nodes'][0]['meaning'], 'Cooking fixed meaning')
        self.assertEqual(len(state['nodes'][0]['entries']), 2)

    def test_terminal_validation_failures_are_not_retried(self):
        self.setup_trial(same_note=True, schema_version=2, independent_meanings=True)
        self.shared()
        self.continue_trial(env={'FAKE_RUNNER_PROMPT_RESPONSE': '{"wrong":"schema"}'})
        self.assertEqual(len(self.calls()), 3)
        self.assertEqual(self.state()['nodes'], [])
        self.assertTrue(all(s['answers'][0]['status'] == 'malformed' and s['answers'][0]['receipt']
                            for s in self.state()['steps']))

    def test_native_local_claim_ledger_rejects_counter_rollback(self):
        self.dynamic_runner()
        self.setup_trial(schema_version=2, independent_meanings=True)
        self.shared()
        self.continue_trial(attempts=1, ok=False)
        path = self.root / 'trial/continuation/attempt-budget.json'
        self.write(str(path), dict(schema_version=1, limit=1, used=0))
        self.assertIn('rollback', self.continue_trial(attempts=1, ok=False).stderr)
        self.assertEqual(len(self.calls()), 1)

    def test_missing_plan_cannot_restart_the_bounded_node_range(self):
        self.dynamic_runner()
        self.setup_trial(same_note=True, schema_version=2, independent_meanings=True)
        self.shared()
        self.continue_trial(nodes=1)
        (self.root / 'trial/continuation/plan.json').unlink()
        result = self.continue_trial(nodes=1, ok=False)
        self.assertIn('missing continuation plan', result.stderr)
        self.assertEqual(self.state()['index'], 1)
        self.assertEqual(len(self.calls()), 1)

    def test_missing_shared_budget_is_not_created(self):
        self.setup_trial(schema_version=2, independent_meanings=True)
        self.continue_trial(ok=False)
        self.assertFalse((self.root / 'shared.json').exists())
        self.assertFalse((self.root / 'trial/continuation/attempt-budget.json').exists())
        self.assertEqual(self.calls(), [])

    def test_interrupt_after_atomic_advance_resumes_without_reapplying(self):
        self.dynamic_runner()
        self.setup_trial(same_note=True, schema_version=2, independent_meanings=True)
        self.shared()
        prepare = canonical_trial._prepare
        def interrupted(directory, state):
            if state['index'] == 1:
                raise ValueError('Simulated preparation interruption')
            return prepare(directory, state)
        with patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.log)), patch.object(
                canonical_trial, '_prepare', side_effect=interrupted):
            with self.assertRaisesRegex(ValueError, 'preparation interruption'):
                continuation.continue_trial(self.root / 'trial', 3, 3, self.root / 'shared.json')
        self.assertEqual(self.state()['index'], 1)
        self.assertIsNone(self.state()['experiment'])
        self.continue_trial()
        self.assertEqual(len(self.calls()), 3)
        self.assertEqual(len(self.state()['steps']), 3)

    def test_stale_experiment_is_not_applied_after_intervening_manual_advance(self):
        self.dynamic_runner()
        self.setup_trial(same_note=True, schema_version=2, independent_meanings=True)
        self.shared()
        run = continuation.workflow.run
        def intervening(*args, **kwargs):
            result = run(*args, **kwargs)
            canonical_trial.advance_trial(self.root / 'trial', 'bootstrap', 'Actual intervening manual review')
            return result
        with patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.log)), patch.object(
                continuation.workflow, 'run', side_effect=intervening):
            with self.assertRaisesRegex(ValueError, 'experiment changed'):
                continuation.continue_trial(self.root / 'trial', 3, 3, self.root / 'shared.json')
        self.assertEqual(self.state()['index'], 1)
        self.assertEqual(self.state()['steps'][0]['reviewer'], 'agent')
        self.assertEqual(len(self.calls()), 1)
        self.assertIn('manual transition', self.continue_trial(ok=False).stderr)

    def test_invalid_bounds_missing_budget_and_nonindependent_trial_make_no_calls(self):
        self.setup_trial(schema_version=2)
        self.shared()
        self.assertIn('independently', self.continue_trial(ok=False).stderr)
        self.assertIn('positive', self.continue_trial(nodes=0, ok=False).stderr)
        self.assertIn('positive', self.continue_trial(attempts=0, ok=False).stderr)
        self.assertEqual(self.calls(), [])

    def test_source_change_stops_before_launch(self):
        self.dynamic_runner()
        self.setup_trial(schema_version=2, independent_meanings=True)
        self.shared()
        path = self.root / 'notes.json'
        path.write_text(path.read_text() + '\n')
        self.assertIn('source changed', self.continue_trial(ok=False).stderr)
        self.assertEqual(self.calls(), [])


if __name__ == '__main__':
    unittest.main()
