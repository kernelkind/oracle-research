"""Exercise roots-only construction through the production experiment CLI."""
import json
from pathlib import Path
import unittest

from sse_multivector import test_experiment as fixtures


class CanonicalTrialTests(unittest.TestCase):
    setUp = fixtures.ExperimentTests.setUp
    write = fixtures.ExperimentTests.write
    cli = fixtures.ExperimentTests.cli

    def setup_trial(self, same_note=False, extra_root=False, schema_version=1, root_order=None, independent_meanings=False, local_schema_version=None):
        self.prompt.write_text('GENERIC PROMPT {INPUT_JSON}')
        self.write('notes.json', {'schema_version': 1, 'notes': [
            {'note_id': 'n1', 'text': 'Original post', 'subjects': [
                {'number': '1', 'subject': 'Cooking', 'context': 'Using heat'},
                {'number': '1.1', 'subject': 'EXCLUDED CHILD', 'context': 'Child'},
                {'number': '2', 'subject': 'Food', 'context': 'Intended for cooking'},
                {'number': '3', 'subject': 'Ingredients', 'context': 'Cooking role'}]}]})
        base = json.loads(self.spec.read_text())
        schemas = Path(__file__).with_name('shr_single_pair')
        for name, schema in [('bootstrap', 'Hierarchy-bootstrap-v1.output.schema.json'),
                             ('comparison', 'Hierarchy-compare-v4.output.schema.json')]:
            spec = {**base, 'runner': {**base['runner'],
                    'output_schema': json.loads((schemas / schema).read_text())}}
            self.write(name + '.json', spec)
        self.write('trial.json', {'schema_version': schema_version, 'corpus': 'notes.json',
                   'note_ids': ['n1'], 'bootstrap_spec': 'bootstrap.json',
                   'comparison_spec': 'comparison.json'})
        if not same_note:
            corpus = json.loads((self.root / 'notes.json').read_text())
            subjects = corpus['notes'][0]['subjects']
            corpus['notes'] = [
                {'note_id': 'n1', 'text': 'First post', 'subjects': subjects[:2]},
                {'note_id': 'n2', 'text': 'Second post', 'subjects': [subjects[2]]},
                {'note_id': 'n3', 'text': 'Third post', 'subjects': [subjects[3]]}]
            if extra_root:
                corpus['notes'][1]['subjects'].append({'number': '3', 'subject': 'Other root', 'context': 'Independent topic'})
            self.write('notes.json', corpus)
            cfg = json.loads((self.root / 'trial.json').read_text())
            cfg['note_ids'] = ['n1', 'n2', 'n3']
            self.write('trial.json', cfg)
        if root_order is not None:
            cfg = json.loads((self.root / 'trial.json').read_text())
            del cfg['note_ids']
            cfg['roots'] = root_order
            self.write('trial.json', cfg)
        if independent_meanings:
            cfg = json.loads((self.root / 'trial.json').read_text())
            cfg['independent_meanings'] = True
            self.write('trial.json', cfg)
        if local_schema_version is not None:
            cfg = json.loads((self.root / 'trial.json').read_text())
            cfg['local_schema_version'] = local_schema_version
            self.write('trial.json', cfg)
        self.cli('prepare-canonical-trial', 'trial', '--spec', 'trial.json')

    def state(self):
        return json.loads((self.root / 'trial/state.json').read_text())

    def answer(self, value):
        self.cli('run', self.state()['experiment'],
                 env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(value)})

    def advance(self, case, **kwargs):
        return self.cli('advance-canonical-trial', 'trial', '--meaning-case', case,
                        '--comment', 'Reviewed saved meanings', **kwargs)

    def test_full_tree_meaning_input_is_preserved_for_root_and_child_construction(self):
        self.setup_trial(schema_version=2, independent_meanings=True, local_schema_version=4)
        shown = json.loads(self.cli('show', self.state()['experiment'], '--json').stdout)
        payload = json.loads(shown['cases'][0]['inputs']['INPUT_JSON'])
        self.assertEqual(payload['local'], {'post': 'First post', 'hierarchy': {
            'selected': '1', 'entries': [
                {'number': '1', 'subject': 'Cooking', 'context': 'Using heat'},
                {'number': '1.1', 'subject': 'EXCLUDED CHILD', 'context': 'Child'}]}})
        self.answer({'meaning': 'Fixed cooking meaning'})
        self.advance('bootstrap')
        self.answer({'meaning': 'Fixed food meaning'})
        self.advance('bootstrap')
        shown = json.loads(self.cli('show', self.state()['experiment'], '--case', 'C001', '--json').stdout)
        comparison = json.loads(shown['inputs']['INPUT_JSON'])
        self.assertEqual(comparison['local']['meaning'], 'Fixed food meaning')
        self.assertEqual(set(comparison['local']), {'entry', 'post', 'meaning'})
        self.answer({'meaning': 'Fixed food meaning', 'relation': 'neither', 'reason': 'Separate'})
        self.advance('C001')
        self.answer({'meaning': 'Fixed ingredients meaning'})
        self.advance('bootstrap')
        self.answer({'meaning': 'Fixed ingredients meaning', 'relation': 'neither', 'reason': 'Separate'})
        self.advance('C001')
        self.assertEqual(self.state()['status'], 'complete')
        self.cli('prepare-canonical-child-trial', 'children', '--base-trial', 'trial')
        child = json.loads((self.root / 'children/state.json').read_text())
        shown = json.loads(self.cli('show', child['experiment'], '--json').stdout)
        local = json.loads(shown['cases'][0]['inputs']['INPUT_JSON'])['local']
        self.assertEqual(local['hierarchy']['selected'], '1.1')
        self.assertEqual(local['hierarchy']['entries'], payload['local']['hierarchy']['entries'])
        self.assertEqual(local['post'], 'First post')
        self.assertNotIn('entry', local)

    def test_independent_meaning_is_established_before_comparisons_without_placement(self):
        self.setup_trial(schema_version=2, independent_meanings=True)
        self.assertEqual(self.state()['phase'], 'meaning')
        self.answer({'meaning': 'Fixed cooking meaning'})
        self.advance('bootstrap')
        self.assertEqual(self.state()['index'], 1)
        self.assertEqual(self.state()['phase'], 'meaning')
        self.answer({'meaning': 'Fixed food meaning'})
        meaning_experiment = self.state()['experiment']
        self.advance('bootstrap')
        state = self.state()
        self.assertEqual(state['index'], 1)
        self.assertEqual(len(state['nodes']), 1)
        self.assertEqual(state['phase'], 'comparison')
        source = json.loads((Path(state['experiment']).parent / 'source.json').read_text())
        self.assertEqual(source['pairs'][0]['local_meaning_from'],
                         {'experiment': meaning_experiment, 'case': 'bootstrap'})
        shown = json.loads(self.cli('show', state['experiment'], '--case', 'C001', '--json').stdout)
        payload = json.loads(shown['inputs']['INPUT_JSON'])
        self.assertEqual(payload['local']['meaning'], 'Fixed food meaning')
        self.answer({'meaning': 'Fixed food meaning', 'relation': 'canonical_contains_local',
                     'reason': 'Contained fixture'})
        self.advance('C001')
        self.assertEqual(self.state()['nodes'][1]['meaning'], 'Fixed food meaning')
        self.assertEqual(self.state()['nodes'][1]['parents'], ['C001'])
        self.assertEqual(len(fixtures.ExperimentTests.calls(self)), 3)

    def test_invalid_local_schema_cannot_prepare_a_trial(self):
        self.setup_trial(schema_version=2, independent_meanings=True)
        cfg = json.loads((self.root / 'trial.json').read_text())
        for value in (True, 2, 5, '4'):
            with self.subTest(local_schema_version=value):
                self.write('invalid.json', {**cfg, 'local_schema_version': value})
                result = self.cli('prepare-canonical-trial', 'invalid', '--spec', 'invalid.json', ok=False)
                self.assertIn('supported local schema', result.stderr)
                self.assertFalse((self.root / 'invalid').exists())
        self.write('invalid.json', {**cfg, 'local_schema_version': 4, 'independent_meanings': False})
        result = self.cli('prepare-canonical-trial', 'invalid', '--spec', 'invalid.json', ok=False)
        self.assertIn('independent meanings', result.stderr)

    def test_comparison_copy_mismatch_holds_incoming_graph_and_fixed_meaning(self):
        self.setup_trial(schema_version=2, independent_meanings=True)
        self.answer({'meaning': 'Fixed cooking meaning'})
        self.advance('bootstrap')
        self.answer({'meaning': 'Fixed food meaning'})
        self.advance('bootstrap')
        before = self.state()['nodes']
        self.answer({'meaning': 'Changed comparison meaning', 'relation': 'canonical_contains_local',
                     'reason': 'Fixture silently changes meaning'})
        self.advance('C001')
        state = self.state()
        self.assertEqual(state['nodes'], before)
        self.assertEqual(state['steps'][-1]['status'], 'held')
        self.assertIn('copy', state['steps'][-1]['reason'])
        self.assertEqual(state['steps'][-1]['selected_meaning'], 'Fixed food meaning')
        self.assertEqual(state['local_meanings']['1']['meaning'], 'Fixed food meaning')

    def test_all_comparison_cases_use_one_independent_meaning_receipt(self):
        self.setup_trial(schema_version=2, independent_meanings=True)
        self.answer({'meaning': 'Cooking meaning'})
        self.advance('bootstrap')
        self.answer({'meaning': 'Food meaning'})
        self.advance('bootstrap')
        self.answer({'meaning': 'Food meaning', 'relation': 'neither', 'reason': 'Separate'})
        self.advance('C001')
        self.answer({'meaning': 'Ingredients meaning'})
        self.advance('bootstrap')
        state = self.state()
        source = json.loads((Path(state['experiment']).parent / 'source.json').read_text())
        self.assertEqual(len(source['pairs']), 2)
        references = [pair['local_meaning_from'] for pair in source['pairs']]
        self.assertEqual(references[0], references[1])
        shown = json.loads(self.cli('show', state['experiment'], '--json').stdout)
        self.assertEqual([json.loads(c['inputs']['INPUT_JSON'])['local']['meaning']
                          for c in shown['cases']], ['Ingredients meaning'] * 2)
        self.assertEqual(len(fixtures.ExperimentTests.calls(self)), 4)

    def test_independent_meaning_run_next_executes_comparison_without_placement(self):
        self.setup_trial(schema_version=2, independent_meanings=True)
        self.answer({'meaning': 'Fixed cooking meaning'})
        self.advance('bootstrap')
        self.answer({'meaning': 'Fixed food meaning'})
        result = self.cli('advance-canonical-trial', 'trial', '--meaning-case', 'bootstrap',
                          '--comment', 'Reviewed standalone meaning', '--run-next',
                          '--max-new-attempts', '1', env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps({
                              'meaning': 'Fixed food meaning', 'relation': 'neither',
                              'reason': 'Separate fixture topic'})})
        self.assertEqual(self.state()['index'], 1)
        self.assertEqual(len(self.state()['nodes']), 1)
        batch = json.loads(result.stdout)['next_review']
        self.assertEqual(batch['local']['meaning'], 'Fixed food meaning')
        self.assertEqual(batch['cases'][0]['id'], 'C001')
        self.assertEqual(batch['summary']['valid'], 1)
        self.assertEqual(len(fixtures.ExperimentTests.calls(self)), 3)

    def test_null_independent_meaning_holds_without_comparison_calls(self):
        self.setup_trial(schema_version=2, independent_meanings=True)
        self.answer({'meaning': 'Fixed cooking meaning'})
        self.advance('bootstrap')
        self.answer({'meaning': None})
        self.advance('bootstrap')
        state = self.state()
        self.assertEqual(state['index'], 2)
        self.assertEqual(len(state['nodes']), 1)
        self.assertEqual(state['steps'][-1]['status'], 'held')
        self.assertEqual(state['phase'], 'meaning')
        self.assertEqual(len(fixtures.ExperimentTests.calls(self)), 2)

    def test_independent_meaning_reuses_native_upstream_requests(self):
        self.setup_trial(schema_version=2, independent_meanings=True)
        self.answer({'meaning': 'Native saved meaning'})
        self.cli('prepare-canonical-trial', 'reuse', '--spec', 'trial.json')
        state = json.loads((self.root / 'reuse/state.json').read_text())
        self.cli('run', state['experiment'])
        shown = json.loads(self.cli('show', state['experiment'], '--json').stdout)
        self.assertTrue(shown['cases'][0]['reused'])
        self.assertEqual(shown['cases'][0]['parsed']['meaning'], 'Native saved meaning')
        self.assertEqual(len(fixtures.ExperimentTests.calls(self)), 1)

    def test_same_note_roots_bootstrap_without_comparison(self):
        self.setup_trial(same_note=True)
        for i in range(3):
            source = json.loads((Path(self.state()['experiment']).parent / 'source.json').read_text())
            self.assertIn('nodes', source)
            self.assertNotIn('pairs', source)
            self.answer({'meaning': f'Independent root {i}'})
            self.advance('bootstrap')
        self.assertEqual(self.state()['status'], 'complete')
        self.assertEqual(len(self.state()['nodes']), 3)
        self.assertTrue(all(not n['parents'] for n in self.state()['nodes']))

    def test_reviewed_transition_runs_next_batch_without_applying_it(self):
        self.setup_trial()
        self.answer({'meaning': 'Cooking using heat'})
        result = self.cli('advance-canonical-trial', 'trial', '--meaning-case', 'bootstrap',
                          '--comment', 'Reviewed bootstrap meaning', '--run-next',
                          '--max-new-attempts', '1', env={
                              'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps({
                                  'meaning': 'Food intended for cooking',
                                  'relation': 'canonical_contains_local',
                                  'reason': 'Established cooking role'})})
        returned = json.loads(result.stdout)
        self.assertEqual(self.state()['index'], 1)
        self.assertEqual(len(self.state()['nodes']), 1)
        self.assertEqual(self.state()['steps'][0]['comment'], 'Reviewed bootstrap meaning')
        batch = returned['next_review']
        self.assertEqual(batch['local']['entry']['subject'], 'Food')
        self.assertEqual(batch['local']['post'], 'Second post')
        self.assertEqual(batch['summary']['valid'], 1)
        self.assertEqual(batch['cases'][0]['id'], 'C001')
        self.assertEqual(batch['cases'][0]['parsed']['relation'], 'canonical_contains_local')
        self.assertTrue(batch['cases'][0]['receipt']['record_sha256'])
        saved = json.loads(self.cli('show', self.state()['experiment'], '--json').stdout)
        self.assertEqual(batch['cases'][0]['parsed'], saved['cases'][0]['parsed'])
        self.assertEqual(len(fixtures.ExperimentTests.calls(self)), 2)

    def test_run_next_options_require_a_positive_bound_before_advancing(self):
        self.setup_trial()
        self.answer({'meaning': 'Cooking using heat'})
        before = self.state()
        for options in (('--run-next',), ('--run-next', '--max-new-attempts', '0'),
                        ('--max-new-attempts', '1'), ('--attempt-budget', 'budget.json')):
            with self.subTest(options=options):
                self.cli('advance-canonical-trial', 'trial', '--meaning-case', 'bootstrap',
                         '--comment', 'Reviewed meaning', *options, ok=False)
                self.assertEqual(self.state(), before)
        self.assertEqual(len(fixtures.ExperimentTests.calls(self)), 1)

    def test_hold_preserves_graph_and_runs_only_the_following_batch(self):
        self.setup_trial()
        self.answer({'meaning': 'Cooking using heat'})
        self.advance('bootstrap')
        self.answer({'meaning': 'Food intended for cooking', 'relation': 'canonical_contains_local',
                     'reason': 'Fixture claims containment'})
        before = self.state()['nodes']
        result = self.cli('advance-canonical-trial', 'trial', '--meaning-case', 'C001',
                          '--comment', 'Evidence does not support this placement',
                          '--hold', 'Semantic review needed', '--run-next',
                          '--max-new-attempts', '1', env={
                              'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps({
                                  'meaning': 'Ingredients used in cooking', 'relation': 'neither',
                                  'reason': 'Separate fixture topic'})})
        self.assertEqual(self.state()['nodes'], before)
        self.assertEqual(self.state()['steps'][-1]['status'], 'held')
        batch = json.loads(result.stdout)['next_review']
        self.assertEqual(batch['local']['entry']['subject'], 'Ingredients')
        self.assertEqual([c['id'] for c in batch['cases']], ['C001'])
        self.assertEqual(self.state()['index'], 2)

    def test_run_next_at_completion_makes_no_calls(self):
        self.setup_trial(root_order=[{'note_id': 'n1', 'number': '1'}])
        self.answer({'meaning': 'Cooking using heat'})
        result = self.cli('advance-canonical-trial', 'trial', '--meaning-case', 'bootstrap',
                          '--comment', 'Reviewed final root', '--run-next', '--max-new-attempts', '1')
        self.assertEqual(self.state()['status'], 'complete')
        self.assertNotIn('next_review', json.loads(result.stdout))
        self.assertEqual(len(fixtures.ExperimentTests.calls(self)), 1)

    def test_run_next_reuses_exact_answers_with_shared_native_budget(self):
        self.setup_trial()
        self.answer({'meaning': 'Cooking using heat'})
        self.advance('bootstrap')
        self.answer({'meaning': 'Food intended for cooking', 'relation': 'canonical_contains_local',
                     'reason': 'Established cooking role'})
        budget = self.write('budget.json', dict(schema_version=1, limit=1, used=0))
        self.cli('prepare-canonical-trial', 'trial-reuse', '--spec', 'trial.json')
        reused_state = json.loads((self.root / 'trial-reuse/state.json').read_text())
        self.cli('run', reused_state['experiment'])
        result = self.cli('advance-canonical-trial', 'trial-reuse', '--meaning-case', 'bootstrap',
                          '--comment', 'Reviewed exact saved bootstrap', '--run-next',
                          '--max-new-attempts', '1', '--attempt-budget', budget)
        batch = json.loads(result.stdout)['next_review']
        self.assertEqual(batch['summary']['reused'], 1)
        self.assertTrue(batch['cases'][0]['reused'])
        self.assertEqual(json.loads(budget.read_text())['used'], 0)
        self.assertEqual(len(fixtures.ExperimentTests.calls(self)), 2)

    def test_exhausted_next_budget_preserves_reviewed_transition_and_can_resume(self):
        self.setup_trial()
        self.answer({'meaning': 'Cooking using heat'})
        budget = self.write('budget.json', dict(schema_version=1, limit=1, used=1))
        self.cli('advance-canonical-trial', 'trial', '--meaning-case', 'bootstrap',
                 '--comment', 'Reviewed before next execution', '--run-next',
                 '--max-new-attempts', '1', '--attempt-budget', budget, ok=False)
        self.assertEqual(self.state()['index'], 1)
        self.assertEqual(len(self.state()['nodes']), 1)
        self.assertEqual(len(self.state()['steps']), 1)
        self.assertEqual(len(fixtures.ExperimentTests.calls(self)), 1)
        budget.write_text(json.dumps(dict(schema_version=1, limit=2, used=1)))
        self.cli('run', self.state()['experiment'], '--attempt-budget', budget, env={
            'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps({
                'meaning': 'Food intended for cooking', 'relation': 'canonical_contains_local',
                'reason': 'Established cooking role'})})
        self.assertEqual(self.state()['index'], 1)
        self.assertEqual(json.loads(budget.read_text())['used'], 2)
        self.assertEqual(len(fixtures.ExperimentTests.calls(self)), 2)

    def test_invalid_next_answer_is_reported_without_placement_or_retry(self):
        self.setup_trial()
        self.answer({'meaning': 'Cooking using heat'})
        self.cli('advance-canonical-trial', 'trial', '--meaning-case', 'bootstrap',
                 '--comment', 'Reviewed bootstrap', '--run-next', '--max-new-attempts', '1',
                 env={'FAKE_RUNNER_PROMPT_RESPONSE': '{"meaning": "Missing relation"}'}, ok=False)
        self.assertEqual(self.state()['index'], 1)
        self.assertEqual(len(self.state()['nodes']), 1)
        self.advance('C001', ok=False)
        self.assertEqual(len(fixtures.ExperimentTests.calls(self)), 2)

    def test_explicit_hold_of_failed_partial_batch_preserves_fixed_meaning_and_receipts(self):
        self.setup_trial(schema_version=2, independent_meanings=True, extra_root=True,
                         root_order=[{'note_id': 'n1', 'number': '1'},
                                     {'note_id': 'n2', 'number': '2'},
                                     {'note_id': 'n3', 'number': '3'},
                                     {'note_id': 'n2', 'number': '3'}])
        self.answer({'meaning': 'Cooking meaning'})
        self.advance('bootstrap')
        self.answer({'meaning': 'Food meaning'})
        self.advance('bootstrap')
        self.answer({'meaning': 'Food meaning', 'relation': 'neither', 'reason': 'Separate'})
        self.advance('C001')
        self.answer({'meaning': 'Fixed ingredients meaning'})
        self.advance('bootstrap')
        failed_experiment = self.state()['experiment']
        self.cli('run', failed_experiment, '--max-new-attempts', '1', ok=False, env={
            'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps({
                'meaning': 'Fixed ingredients meaning', 'relation': 'canonical_contains_local',
                'reason': 'Partial fixture positive'})})
        self.cli('run', failed_experiment, ok=False, env={'FAKE_RUNNER_FAIL_STAGE': 'prompt'})
        saved = json.loads(self.cli('show', failed_experiment, '--json').stdout)
        self.assertEqual([c['status'] for c in saved['cases']], ['valid', 'failed'])
        self.assertEqual(saved['cases'][1]['failure_kind'], 'unknown')
        before = self.state()
        ledger = Path(failed_experiment) / 'run/results.jsonl'
        old_receipts = ledger.read_bytes()
        rejected = self.advance('C001', ok=False)
        self.assertIn('all comparisons must be valid', rejected.stderr)
        self.assertEqual(self.state(), before)
        result = self.cli('advance-canonical-trial', 'trial', '--meaning-case', 'C002',
                          '--comment', 'Terminal unknown failure leaves this candidate unresolved',
                          '--hold', 'Manual review required; incomplete comparison batch',
                          '--run-next', '--max-new-attempts', '1', env={
                              'FAKE_RUNNER_PROMPT_RESPONSE': '{"meaning":"Next independent meaning"}'})
        state = self.state()
        self.assertEqual(state['index'], 3)
        self.assertEqual(state['nodes'], before['nodes'])
        self.assertEqual(ledger.read_bytes(), old_receipts)
        held = state['steps'][-1]
        self.assertEqual(held['status'], 'held')
        self.assertEqual(held['before'], held['after'])
        self.assertEqual(held['selected_meaning'], 'Fixed ingredients meaning')
        self.assertEqual(held['local_meaning_from'], before['local_meanings']['2'])
        self.assertEqual([a['status'] for a in held['answers']], ['valid', 'failed'])
        for evidence, native in zip(held['answers'], saved['cases']):
            self.assertEqual(evidence['receipt'], native['receipt'])
            self.assertEqual(evidence['output'], native.get('parsed'))
        self.assertEqual(held['answers'][1]['failure_kind'], 'unknown')
        self.assertEqual(held['answers'][1]['error'], saved['cases'][1]['error'])
        following = json.loads(result.stdout)['next_review']
        self.assertEqual(following['local']['entry']['subject'], 'Other root')
        self.assertEqual(following['summary']['valid'], 1)
        self.assertEqual(len(fixtures.ExperimentTests.calls(self)), 7)

    def test_failed_independent_meaning_can_be_held_without_freezing_a_meaning(self):
        self.setup_trial(schema_version=2, independent_meanings=True)
        failed_experiment = self.state()['experiment']
        self.cli('run', failed_experiment, ok=False, env={'FAKE_RUNNER_FAIL_STAGE': 'prompt'})
        before = self.state()
        saved = json.loads(self.cli('show', failed_experiment, '--json').stdout)['cases'][0]
        ledger = Path(failed_experiment) / 'run/results.jsonl'
        old_receipts = ledger.read_bytes()
        for options in (('--comment', '', '--hold', 'Unresolved meaning'),
                        ('--comment', 'Reviewed failure', '--hold', '   '),
                        ('--comment', 'Reviewed failure', '--hold', 'Unresolved meaning',
                         '--meaning-case', 'missing')):
            self.cli('advance-canonical-trial', 'trial', '--meaning-case', 'bootstrap',
                     *options, ok=False)
            self.assertEqual(self.state(), before)
        self.cli('advance-canonical-trial', 'trial', '--meaning-case', 'bootstrap',
                 '--comment', 'No valid meaning was generated', '--hold', 'Unresolved meaning')
        state = self.state()
        self.assertEqual(state['index'], 1)
        self.assertEqual(state['phase'], 'meaning')
        self.assertEqual(state['nodes'], [])
        self.assertEqual(state['local_meanings'], {})
        held = state['steps'][-1]
        self.assertEqual(held['status'], 'held')
        self.assertIsNone(held['selected_meaning'])
        self.assertNotIn('local_meaning_from', held)
        self.assertEqual(held['answers'][0]['receipt'], saved['receipt'])
        self.assertEqual(held['answers'][0]['failure_kind'], 'unknown')
        self.assertEqual(ledger.read_bytes(), old_receipts)
        self.assertEqual(len(fixtures.ExperimentTests.calls(self)), 1)

    def test_unrun_legacy_bootstrap_can_be_explicitly_held_without_teacher_calls(self):
        self.setup_trial()
        self.cli('advance-canonical-trial', 'trial', '--meaning-case', 'bootstrap',
                 '--comment', 'This candidate remains unreviewed', '--hold', 'Deferred candidate')
        state = self.state()
        self.assertEqual(state['index'], 1)
        self.assertEqual(state['nodes'], [])
        held = state['steps'][-1]
        self.assertIsNone(held['selected_meaning'])
        self.assertEqual(held['answers'], [{'id': 'bootstrap', 'output': None,
                                           'receipt': None, 'status': 'unrun'}])
        self.assertEqual(fixtures.ExperimentTests.calls(self), [])

    def test_explicit_hold_keeps_source_checks_for_nonvalid_batches(self):
        self.setup_trial()
        source = self.root / 'notes.json'
        source.write_text(source.read_text() + '\n')
        result = self.cli('advance-canonical-trial', 'trial', '--meaning-case', 'bootstrap',
                          '--comment', 'Source integrity must still hold',
                          '--hold', 'Unrun candidate', ok=False)
        self.assertIn('trial source changed', result.stderr)
        self.assertEqual(self.state()['index'], 0)
        self.assertEqual(fixtures.ExperimentTests.calls(self), [])

    def test_explicit_roots_preserve_order_and_compare_cross_note(self):
        roots = [{'note_id': 'n2', 'number': '2'},
                 {'note_id': 'n1', 'number': '1'},
                 {'note_id': 'n3', 'number': '3'}]
        self.setup_trial(root_order=roots, schema_version=2)
        self.assertEqual(self.state()['roots'], roots)
        self.answer({'meaning': 'Food intended for cooking'})
        self.advance('bootstrap')
        source = json.loads((Path(self.state()['experiment']).parent / 'source.json').read_text())
        self.assertEqual(source['pairs'][0]['local'], roots[1])
        self.assertEqual(source['pairs'][0]['canonical']['id'], 'C001')
        self.assertEqual(self.state()['steps'][0]['local'], roots[0])
        self.assertEqual(self.state()['nodes'][0]['subject'], 'Food')

    def test_explicit_root_selection_rejects_invalid_references(self):
        self.setup_trial()
        original = json.loads((self.root / 'trial.json').read_text())
        for roots in ([], 'n1', [{'note_id': 'n1', 'number': '1.1'}],
                      [{'note_id': 'missing', 'number': '1'}],
                      [{'note_id': 'n1', 'number': '99'}],
                      [{'note_id': 'n1', 'number': 1}],
                      [{'note_id': 'n1'}],
                      [{'note_id': 'n1', 'number': '1', 'extra': True}],
                      [{'note_id': 'n1', 'number': '1'}] * 2):
            with self.subTest(roots=roots):
                cfg = {key: value for key, value in original.items() if key != 'note_ids'}
                cfg['roots'] = roots
                self.write('invalid.json', cfg)
                result = self.cli('prepare-canonical-trial', 'invalid-trial',
                                  '--spec', 'invalid.json', ok=False)
                self.assertIn('unique existing local roots', result.stderr)
                self.assertFalse((self.root / 'invalid-trial').exists())
        cfg = {**original, 'roots': [{'note_id': 'n1', 'number': '1'}]}
        self.write('invalid.json', cfg)
        result = self.cli('prepare-canonical-trial', 'invalid-trial',
                          '--spec', 'invalid.json', ok=False)
        self.assertIn('invalid canonical trial spec', result.stderr)

    def test_explicit_root_selection_remains_source_frozen(self):
        self.setup_trial(root_order=[{'note_id': 'n1', 'number': '1'},
                                     {'note_id': 'n2', 'number': '2'}])
        self.answer({'meaning': 'Preparing food with heat'})
        cfg = json.loads((self.root / 'trial.json').read_text())
        cfg['roots'].reverse()
        self.write('trial.json', cfg)
        result = self.advance('bootstrap', ok=False)
        self.assertIn('trial source changed', result.stderr)
        self.assertEqual(self.state()['index'], 0)

    def test_any_matching_support_excludes_multi_note_canonical(self):
        self.setup_trial(extra_root=True)
        self.answer({'meaning': 'Fixed meaning'})
        self.advance('bootstrap')
        self.answer({'meaning': 'Equivalent meaning', 'relation': 'equivalent', 'reason': 'Same topic'})
        self.advance('C001')
        self.assertEqual(len(self.state()['nodes'][0]['entries']), 2)
        source = json.loads((Path(self.state()['experiment']).parent / 'source.json').read_text())
        self.assertIn('nodes', source)
        self.assertNotIn('pairs', source)
        self.answer({'meaning': 'Independent other topic'})
        self.advance('bootstrap')
        source = json.loads((Path(self.state()['experiment']).parent / 'source.json').read_text())
        self.assertEqual([p['id'] for p in source['pairs']], ['C001', 'C003'])

    def test_concurrency_change_only_applies_to_next_experiments(self):
        self.setup_trial()
        previous = Path(self.state()['experiment']).parent / 'spec.json'
        frozen = previous.read_bytes()
        self.answer({'meaning': 'Cooking'})
        self.cli('advance-canonical-trial', 'trial', '--meaning-case', 'bootstrap',
                 '--comment', 'User requested concurrency 32', '--concurrency', '32')
        self.assertEqual(previous.read_bytes(), frozen)
        following = Path(self.state()['experiment']).parent / 'spec.json'
        self.assertEqual(json.loads(following.read_text())['runner']['concurrency'], 32)
        self.assertEqual(self.state()['steps'][-1]['next_concurrency'], 32)

    def test_exact_saved_answers_are_reused_across_trials(self):
        self.setup_trial()
        self.answer({'meaning': 'Saved meaning'})
        self.cli('prepare-canonical-trial', 'trial-reuse', '--spec', 'trial.json')
        state = json.loads((self.root / 'trial-reuse/state.json').read_text())
        self.cli('run', state['experiment'], env={
            'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps({'meaning': 'Should not be called'})})
        records = [json.loads(line) for line in
                   (Path(state['experiment']) / 'run/results.jsonl').read_text().splitlines()]
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].get('execution'), 'cross_run_reuse')
        self.assertIn('Saved meaning', records[0]['final_output_raw'])

    def test_v2_trial_includes_descendants_and_keeps_bootstrap_v1(self):
        self.setup_trial(schema_version=2)
        self.answer({'meaning': 'Cooking'})
        self.advance('bootstrap')
        self.answer({'meaning': 'Food intended for cooking', 'relation': 'canonical_contains_local',
                     'reason': 'Established cooking role'})
        self.advance('C001')
        result = self.cli('show', self.state()['experiment'], '--case', 'C001', '--json')
        payload = json.loads(json.loads(result.stdout)['inputs']['INPUT_JSON'])
        self.assertEqual([n['id'] for n in payload['canonical']['descendants']], ['C002'])

    def test_roots_only_bootstrap_containment_and_contradiction_hold(self):
        self.setup_trial()
        self.assertEqual(len(self.state()['roots']), 3)
        self.assertEqual(self.state()['nodes'], [])
        self.answer({'meaning': 'Preparing food using heat.'})
        self.advance('bootstrap')
        self.assertEqual(len(self.state()['nodes']), 1)
        self.answer({'meaning': 'Food intended to be cooked.',
                     'relation': 'canonical_contains_local', 'reason': 'Cooking role'})
        self.advance('C001')
        self.assertEqual(self.state()['nodes'][1]['parents'], ['C001'])
        self.answer({'meaning': 'Cooking ingredients.', 'relation': 'equivalent',
                     'reason': 'Fixture deliberately claims equivalence with two nodes'})
        self.advance('C001')
        self.assertEqual(len(self.state()['nodes']), 2)
        self.assertEqual(self.state()['steps'][-1]['status'], 'held')
        self.assertEqual(self.state()['status'], 'complete')
        self.assertIn('multiple', self.state()['steps'][-1]['reason'])

    def test_equivalence_keeps_fixed_meaning_and_uncertainty_keeps_graph(self):
        self.setup_trial()
        self.answer({'meaning': 'Fixed original meaning.'})
        self.advance('bootstrap')
        self.answer({'meaning': 'Different wording for the same meaning.',
                     'relation': 'equivalent', 'reason': 'Equivalent fixture'})
        self.advance('C001')
        node = self.state()['nodes'][0]
        self.assertEqual(node['meaning'], 'Fixed original meaning.')
        self.assertEqual(len(node['entries']), 2)
        self.answer({'meaning': None, 'relation': 'uncertain', 'reason': 'Ambiguous'})
        self.advance('C001')
        self.assertEqual(self.state()['nodes'], [node])
        self.assertEqual(self.state()['steps'][-1]['status'], 'held')

    def test_incomplete_or_changed_source_cannot_advance(self):
        self.setup_trial()
        self.advance('bootstrap', ok=False)
        self.answer({'meaning': 'A meaning.'})
        path = self.root / 'notes.json'
        path.write_text(path.read_text() + '\n')
        self.advance('bootstrap', ok=False)
        self.assertEqual(self.state()['index'], 0)

    def test_transitive_contradiction_preserves_graph(self):
        self.setup_trial()
        self.answer({'meaning': 'Cooking'})
        self.advance('bootstrap')
        self.answer({'meaning': 'Food for cooking', 'relation': 'canonical_contains_local',
                     'reason': 'Child'})
        self.advance('C001')
        before = self.state()['nodes']
        self.cli('run', self.state()['experiment'], '--max-new-attempts', '1', ok=False,
                 env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps({
                     'meaning': 'Ingredients', 'relation': 'neither', 'reason': 'Contradiction fixture'})})
        self.answer({'meaning': 'Ingredients', 'relation': 'canonical_contains_local',
                     'reason': 'Below Food entails below Cooking'})
        self.advance('C002')
        self.assertEqual(self.state()['nodes'], before)
        self.assertIn('contradiction', self.state()['steps'][-1]['reason'])

    def test_equivalence_cannot_replace_a_settled_neither_with_containment(self):
        self.setup_trial(schema_version=2, independent_meanings=True)
        self.answer({'meaning': 'Things intended for storage'})
        self.advance('bootstrap')
        self.answer({'meaning': 'Objects admired for their appearance'})
        self.advance('bootstrap')
        self.answer({'meaning': 'Objects admired for their appearance',
                     'relation': 'neither', 'reason': 'Neither fixed topic contains the other'})
        self.advance('C001')
        previous = self.state()['steps'][-1]
        self.answer({'meaning': 'Objects admired for their appearance'})
        self.advance('bootstrap')
        before = self.state()['nodes']
        self.cli('run', self.state()['experiment'], '--max-new-attempts', '1', ok=False,
                 env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps({
                     'meaning': 'Objects admired for their appearance',
                     'relation': 'canonical_contains_local',
                     'reason': 'Deliberate conflict with the settled pair'})})
        self.answer({'meaning': 'Objects admired for their appearance',
                     'relation': 'equivalent', 'reason': 'Same fixed meaning as C002'})
        self.advance('C002')
        state = self.state()
        self.assertEqual(state['nodes'], before)
        held = state['steps'][-1]
        self.assertEqual(held['status'], 'held')
        self.assertEqual(held['before'], held['after'])
        self.assertIn('equivalence', held['reason'])
        witness = held['equivalence_contradiction']
        self.assertEqual(witness['equivalent_to'], 'C002')
        self.assertEqual(witness['other'], 'C001')
        self.assertEqual(witness['previous_step'], previous['index'])
        self.assertEqual(witness['previous_experiment'], previous['experiment'])
        self.assertEqual(witness['previous_answer'], previous['answers'][0])
        self.assertEqual(witness['previous_relation'], 'neither')
        self.assertEqual(witness['current_relation'], 'canonical_contains_local')
        self.assertEqual(state['nodes'][1]['meaning'], 'Objects admired for their appearance')
        self.assertEqual(len(state['nodes'][1]['entries']), 1)

    def test_multiple_compatible_parents_are_retained(self):
        self.setup_trial()
        self.answer({'meaning': 'First topic'})
        self.advance('bootstrap')
        self.answer({'meaning': 'Second topic', 'relation': 'neither', 'reason': 'Separate'})
        self.advance('C001')
        self.answer({'meaning': 'Shared narrower topic', 'relation': 'canonical_contains_local',
                     'reason': 'Both contain this topic'})
        self.advance('C001')
        self.assertEqual(self.state()['nodes'][-1]['parents'], ['C001', 'C002'])


if __name__ == '__main__':
    unittest.main()
