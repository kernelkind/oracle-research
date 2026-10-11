"""Bounded native comparisons verify graph consequences with actual receipts."""
import json
from pathlib import Path
import unittest

from sse_multivector import test_canonical_continuation as fixtures


class CanonicalComparisonPolicyTests(unittest.TestCase):
    setUp = fixtures.CanonicalContinuationTests.setUp
    write = fixtures.CanonicalContinuationTests.write
    cli = fixtures.CanonicalContinuationTests.cli
    calls = fixtures.CanonicalContinuationTests.calls
    dynamic_runner = fixtures.CanonicalContinuationTests.dynamic_runner
    shared = fixtures.CanonicalContinuationTests.shared
    continue_trial = fixtures.CanonicalContinuationTests.continue_trial

    def state(self, directory='trial'):
        return json.loads((self.root / directory / 'state.json').read_text())

    def completed_base(self, *, descendant=False, child_note='n2', child_subject='Baby potatoes',
                       same_note_root=False, base_relation='canonical_contains_local', limit=1, future_root=False):
        self.dynamic_runner()
        self.prompt.write_text('GENERIC PROMPT {INPUT_JSON}')
        notes = [
            dict(note_id='n1', text='Foods are used in meals.', subjects=[
                dict(number='1', subject='Food', context='Foods used in meals.')]),
            dict(note_id='n2', text='Vegetables include baby potatoes.', subjects=[
                dict(number='1', subject='Vegetables', context='Vegetables used in meals.')])]
        next(note for note in notes if note['note_id'] == child_note)['subjects'].append(
            dict(number='1.1', subject=child_subject, context='A selected culinary child topic.'))
        if descendant:
            notes.append(dict(note_id='n3', text='Carrots are vegetables used in meals.', subjects=[
                dict(number='1', subject='Carrots', context='Carrots used in meals.')]))
        roots = [dict(note_id=note['note_id'], number='1') for note in notes]
        if future_root:
            notes.append(dict(note_id='n4', text='Vegetables for a new meal.', subjects=[
                dict(number='1', subject='Vegetables', context='Vegetables for a meal.')]))
        if same_note_root:
            notes[1]['subjects'].append(dict(number='2', subject='Garden tools',
                context='Garden tools are a separate topic from vegetables.'))
            roots.append(dict(note_id='n2', number='2'))
        self.write('notes.json', dict(schema_version=1, notes=notes))
        base = json.loads(self.spec.read_text())
        schemas = Path(__file__).with_name('shr_single_pair')
        for name, schema in [('bootstrap', 'Hierarchy-bootstrap-v1.output.schema.json'),
                             ('comparison', 'Hierarchy-compare-v4.output.schema.json')]:
            self.write(name + '.json', {**base, 'runner': {**base['runner'],
                       'output_schema': json.loads((schemas / schema).read_text())}})
        self.write('trial.json', dict(schema_version=2, corpus='notes.json',
            roots=roots,
            bootstrap_spec='bootstrap.json', comparison_spec='comparison.json',
            independent_meanings=True))
        self.cli('prepare-canonical-trial', 'trial', '--spec', 'trial.json')
        self.shared()
        self.continue_trial(nodes=len(roots), attempts=16, env={'FIXTURE_RELATIONS': json.dumps({
            'Vegetables': {'C001': base_relation},
            'Carrots': {'C001': 'canonical_contains_local', 'C002': 'canonical_contains_local'}})})
        if base_relation == 'canonical_contains_local':
            self.assertEqual(self.state()['nodes'][1]['parents'], ['C001'])
        self.write('policy.json', dict(schema_version=1, limit=limit))

    def prepare_children(self, directory='children', *, policy=True):
        options = ['--comparison-policy', 'policy.json'] if policy else []
        return self.cli('prepare-canonical-child-trial', directory, '--base-trial', 'trial', *options)

    def comparison_calls(self, start):
        payloads = [json.loads(call['prompt'].removeprefix('GENERIC PROMPT '))
                    for call in self.calls()[start:]]
        return [payload for payload in payloads if 'canonical' in payload]

    def finish_child(self, relations, *, attempts=10, ok=True, extra_env=None):
        return self.continue_trial(nodes=1, attempts=attempts, directory='children', ok=ok,
            env={'FIXTURE_RELATIONS': json.dumps(relations), **(extra_env or {})})

    def enter_guard(self, *, shortlist_relation='canonical_contains_local'):
        self.prepare_children()
        state = self.state('children')
        self.cli('run', state['experiment'])
        self.cli('advance-canonical-trial', 'children', '--meaning-case', 'bootstrap',
                 '--comment', 'Check independently fixed child meaning.')
        shortlist = self.state('children')['experiment']
        self.cli('run', shortlist, env={'FIXTURE_RELATIONS': json.dumps({
            'Baby potatoes': {'C002': shortlist_relation}})})
        self.cli('advance-canonical-trial', 'children', '--meaning-case', 'C002',
                 '--comment', 'Check shortlisted containment before branch verification.')
        guard = self.state('children')['experiment']
        self.assertNotEqual(guard, shortlist)
        return shortlist, guard

    def test_policy_limit_stays_bounded_to_512_canonical_candidates(self):
        self.completed_base(limit=513)
        calls = self.calls()
        result = self.cli(
            'prepare-canonical-child-trial', 'over-limit', '--base-trial', 'trial',
            '--comparison-policy', 'policy.json', ok=False)
        self.assertIn('invalid canonical comparison policy', result.stderr)
        self.assertFalse((self.root / 'over-limit').exists())
        self.assertEqual(self.calls(), calls)

    def test_omitted_ancestor_rejection_is_verified_and_holds_placement(self):
        self.completed_base()
        before = self.state()['nodes']
        count = len(self.calls())
        self.prepare_children()
        self.finish_child({'Baby potatoes': {
            'C002': 'canonical_contains_local', 'C001': 'neither'}}, attempts=3)
        state = self.state('children')
        self.assertEqual(state['nodes'], before)
        self.assertEqual(state['steps'][-1]['status'], 'held')
        self.assertEqual(len(self.calls()) - count, 3)
        self.assertEqual([call['canonical']['id'] for call in self.comparison_calls(count)],
                         ['C002', 'C001'])

    def test_matched_ancestor_is_verified_before_success_and_keeps_original_meanings(self):
        self.completed_base()
        before = self.state()['nodes']
        count = len(self.calls())
        self.prepare_children()
        self.finish_child({'Baby potatoes': {'C002': 'canonical_contains_local',
                                            'C001': 'canonical_contains_local'}})
        state = self.state('children')
        self.assertEqual(state['steps'][-1]['status'], 'added')
        self.assertEqual(state['nodes'][-1]['parents'], ['C002'])
        self.assertEqual(state['nodes'][-1]['meaning'], 'Baby potatoes fixed meaning')
        self.assertEqual(state['nodes'][:2], before)
        calls = self.comparison_calls(count)
        self.assertEqual([call['canonical']['id'] for call in calls], ['C002', 'C001'])
        self.assertEqual(calls[0]['local'], calls[1]['local'])
        self.assertEqual([node['id'] for node in calls[1]['canonical']['descendants']], ['C002'])
        self.assertNotIn(state['nodes'][-1]['id'], json.dumps(calls[1]['canonical']))

    def test_omitted_descendant_rejection_holds_local_parent_proposal(self):
        self.completed_base(descendant=True, child_note='n1', child_subject='Vegetables for cooking', limit=2)
        before = self.state()['nodes']
        count = len(self.calls())
        self.prepare_children()
        self.finish_child({'Vegetables for cooking': {
            'C001': 'canonical_contains_local', 'C002': 'local_contains_canonical', 'C003': 'neither'}})
        state = self.state('children')
        self.assertEqual(state['nodes'], before)
        self.assertEqual(state['steps'][-1]['status'], 'held')
        self.assertEqual([call['canonical']['id'] for call in self.comparison_calls(count)],
                         ['C001', 'C002', 'C003'])

    def test_equivalence_verifies_both_ancestor_and_descendant_and_reuses_fixed_node(self):
        self.completed_base(descendant=True, same_note_root=True)
        before = self.state()['nodes']
        count = len(self.calls())
        self.prepare_children()
        self.finish_child({'Baby potatoes': {'C002': 'equivalent',
            'C001': 'canonical_contains_local', 'C003': 'local_contains_canonical'}})
        state = self.state('children')
        self.assertEqual(state['steps'][-1]['status'], 'equivalent')
        self.assertEqual(state['steps'][-1]['canonical_id'], 'C002')
        self.assertEqual(len(state['nodes']), len(before))
        self.assertEqual(state['nodes'][1]['meaning'], before[1]['meaning'])
        self.assertIn(dict(note_id='n2', number='1.1'), state['nodes'][1]['entries'])
        self.assertEqual([call['canonical']['id'] for call in self.comparison_calls(count)],
                         ['C002', 'C001', 'C003'])
        self.assertNotIn('C004', [call['canonical']['id'] for call in self.comparison_calls(count)])

    def test_positive_guard_with_wrong_equivalence_label_is_not_accepted(self):
        self.completed_base()
        before = self.state()['nodes']
        self.prepare_children()
        self.finish_child({'Baby potatoes': {'C002': 'canonical_contains_local', 'C001': 'equivalent'}})
        self.assertEqual(self.state('children')['nodes'], before)
        self.assertEqual(self.state('children')['steps'][-1]['status'], 'held')

    def test_uncertain_guard_holds_without_graph_changes(self):
        self.completed_base()
        before = self.state()['nodes']
        self.prepare_children()
        self.finish_child({'Baby potatoes': {'C002': 'canonical_contains_local', 'C001': 'uncertain'}})
        self.assertEqual(self.state('children')['nodes'], before)
        self.assertEqual(self.state('children')['steps'][-1]['status'], 'held')

    def test_all_neither_shortlist_does_not_launch_a_guard(self):
        self.completed_base()
        count = len(self.calls())
        before = self.state()['nodes']
        self.prepare_children()
        self.finish_child({'Baby potatoes': {'C002': 'neither'}})
        self.assertEqual(len(self.calls()) - count, 2)
        self.assertEqual([call['canonical']['id'] for call in self.comparison_calls(count)], ['C002'])
        self.assertEqual(self.state('children')['nodes'], before)
        self.assertEqual(self.state('children')['steps'][-1]['status'], 'held')

    def test_guard_is_pending_when_actual_attempt_cap_is_exhausted(self):
        self.completed_base()
        before = self.state()['nodes']
        count = len(self.calls())
        self.prepare_children()
        result = json.loads(self.finish_child({'Baby potatoes': {
            'C002': 'canonical_contains_local', 'C001': 'canonical_contains_local'}},
            attempts=2, ok=False).stdout)
        self.assertEqual(result['status'], 'attempt_limit')
        state = self.state('children')
        self.assertEqual(state['nodes'], before)
        self.assertEqual(state['index'], self.state()['index'])
        self.assertEqual(state['steps'], self.state()['steps'])
        shown = json.loads(self.cli('show', state['experiment'], '--json').stdout)
        self.assertEqual([(case['id'], case['status']) for case in shown['cases']], [('C001', 'unrun')])
        self.assertEqual(len(self.calls()) - count, 2)
        repeated = self.finish_child({'Baby potatoes': {'C001': 'canonical_contains_local'}},
                                     attempts=2, ok=False)
        self.assertEqual(json.loads(repeated.stdout)['status'], 'attempt_limit')
        self.assertEqual(self.state('children'), state)
        self.assertEqual(len(self.calls()) - count, 2)

    def test_resume_at_guard_does_not_repeat_shortlist_or_change_frozen_input(self):
        self.completed_base()
        original = self.state()
        shortlist, guard = self.enter_guard()
        state = self.state('children')
        self.assertEqual(state['nodes'], original['nodes'])
        self.assertEqual(state['index'], original['index'])
        shortlist_bytes = (Path(shortlist) / 'run/results.jsonl').read_bytes()
        count = len(self.calls())
        self.finish_child({'Baby potatoes': {'C001': 'canonical_contains_local'}}, attempts=1)
        self.assertEqual(len(self.calls()) - count, 1)
        self.assertEqual(self.state('children')['steps'][-1]['status'], 'added')
        self.assertEqual((Path(shortlist) / 'run/results.jsonl').read_bytes(), shortlist_bytes)
        self.assertEqual([call['canonical']['id'] for call in self.comparison_calls(count)], ['C001'])
        self.assertTrue((Path(guard) / 'run/results.jsonl').exists())

    def test_terminal_failed_guard_holds_without_retrying_the_shortlist(self):
        self.completed_base()
        before = self.state()['nodes']
        shortlist, guard = self.enter_guard()
        old_receipts = (Path(shortlist) / 'run/results.jsonl').read_bytes()
        self.cli('run', guard, ok=False, env={'FAKE_RUNNER_FAIL_STAGE': 'prompt'})
        count = len(self.calls())
        self.finish_child({})
        self.assertEqual(self.state('children')['nodes'], before)
        self.assertEqual(self.state('children')['steps'][-1]['status'], 'held')
        self.assertEqual(len(self.calls()), count)
        self.assertEqual((Path(shortlist) / 'run/results.jsonl').read_bytes(), old_receipts)

    def test_changed_policy_source_is_rejected_at_guard_without_spending(self):
        self.completed_base()
        self.enter_guard()
        before = self.state('children')
        count = len(self.calls())
        with (self.root / 'policy.json').open('a') as stream:
            stream.write('\n')
        result = self.finish_child({}, ok=False)
        self.assertIn('source changed', result.stderr)
        self.assertEqual(self.state('children'), before)
        self.assertEqual(len(self.calls()), count)

    def test_changed_shortlist_receipt_is_rejected_during_guard_resume(self):
        self.completed_base()
        shortlist, _ = self.enter_guard()
        before = self.state('children')
        count = len(self.calls())
        path = Path(shortlist) / 'run/results.jsonl'
        records = [json.loads(line) for line in path.read_bytes().splitlines()]
        altered = json.dumps(dict(meaning='Baby potatoes fixed meaning', relation='neither', reason='Tampered'))
        records[0].update(final_output_raw=altered, response=altered)
        path.write_text(''.join(json.dumps(record) + '\n' for record in records))
        self.finish_child({}, ok=False)
        self.assertEqual(self.state('children')['nodes'], before['nodes'])
        self.assertEqual(self.state('children')['index'], before['index'])
        self.assertEqual(len(self.calls()), count)

    def test_legacy_default_still_compares_all_eligible_nodes_in_one_batch(self):
        self.completed_base()
        count = len(self.calls())
        self.prepare_children(policy=False)
        self.finish_child({'Baby potatoes': {'C001': 'canonical_contains_local',
                                            'C002': 'canonical_contains_local'}})
        self.assertCountEqual([call['canonical']['id'] for call in self.comparison_calls(count)],
                              ['C001', 'C002'])
        self.assertEqual(self.state('children')['steps'][-1]['status'], 'added')

    def test_explicit_hold_cannot_finalize_an_unrun_verification(self):
        self.completed_base()
        self.enter_guard()
        before = self.state('children')
        count = len(self.calls())
        self.cli('advance-canonical-trial', 'children', '--meaning-case', 'C001',
                 '--comment', 'The verification is still unrun.',
                 '--hold', 'Manual hold must preserve pending verification.', ok=False)
        self.assertEqual(self.state('children'), before)
        self.assertEqual(len(self.calls()), count)

    def test_valid_shortlist_receipt_for_a_different_local_input_is_rejected_before_spending(self):
        self.completed_base()
        self.prepare_children()
        self.cli('run', self.state('children')['experiment'])
        self.cli('advance-canonical-trial', 'children', '--meaning-case', 'bootstrap',
                 '--comment', 'Freeze the correct local meaning before comparison.')
        state = self.state('children')
        self.write('wrong-source.json', dict(schema_version=2, corpus='notes.json',
            canonical_states={'current': state['nodes']}, pairs=[dict(id='C002',
                local=dict(note_id='n1', number='1'), canonical=dict(state='current', id='C002'),
                local_meaning='Baby potatoes fixed meaning', review={})]))
        self.write('wrong-spec.json', {**state['comparison_spec'],
            'dataset': {'adapter': 'hierarchy_node_pairs', 'path': 'wrong-source.json'}})
        self.cli('prepare', 'wrong-experiment', '--spec', 'wrong-spec.json')
        self.cli('run', 'wrong-experiment', env={'FIXTURE_RELATIONS': json.dumps({
            'Food': {'C002': 'canonical_contains_local'}})})
        shown = json.loads(self.cli('show', 'wrong-experiment', '--json').stdout)
        self.assertEqual(shown['cases'][0]['status'], 'valid')
        replacement = str(self.root / 'wrong-experiment')
        record = state['comparison_policy_steps'][str(state['index'])]
        record['comparison_phases'][0]['experiment'] = replacement
        state['experiment'] = replacement
        self.write('children/state.json', state)
        count = len(self.calls())
        self.finish_child({'Baby potatoes': {'C001': 'canonical_contains_local'}}, ok=False)
        after = self.state('children')
        self.assertEqual(after['nodes'], state['nodes'])
        self.assertEqual(after['index'], state['index'])
        self.assertEqual(len(self.calls()), count)

    def prepare_growth(self, *, policy=True, directory='growth'):
        config = json.loads((self.root / 'trial.json').read_text())
        config['roots'] = [dict(note_id='n4', number='1')]
        self.write('growth.json', config)
        options = ['--comparison-policy', 'policy.json'] if policy else []
        return self.cli('prepare-canonical-trial', directory, '--spec', 'growth.json',
                        '--base-trial', 'trial', *options)

    def test_growth_root_checks_omitted_ancestor_before_insertion(self):
        self.completed_base(future_root=True)
        before = self.state()['nodes']
        start = len(self.calls())
        self.prepare_growth()
        self.continue_trial(directory='growth', nodes=1, attempts=4, env={
            'FIXTURE_RELATIONS': json.dumps({'Vegetables': {
                'C002': 'canonical_contains_local', 'C001': 'neither'}})})
        state = self.state('growth')
        self.assertEqual(state['nodes'], before)
        self.assertEqual(state['steps'][-1]['status'], 'held')
        calls = self.comparison_calls(start)
        self.assertEqual([call['canonical']['id'] for call in calls], ['C002', 'C001'])
        self.assertEqual(calls[0]['local'], calls[1]['local'])
        self.assertEqual(state['steps'][-1]['comparison_selection']['omitted_relation'], 'unknown')

    def test_initial_root_policy_is_inherited_and_cannot_be_replaced(self):
        self.completed_base(future_root=True)
        self.prepare_growth()
        self.continue_trial(directory='growth', nodes=1, attempts=4, env={
            'FIXTURE_RELATIONS': json.dumps({'Vegetables': {
                'C002': 'canonical_contains_local', 'C001': 'canonical_contains_local'}})})
        self.assertEqual(self.state('growth')['steps'][-1]['status'], 'added')
        self.cli('prepare-canonical-child-trial', 'inherited', '--base-trial', 'growth')
        self.assertEqual(self.state('inherited')['comparison_policy'],
                         self.state('growth')['comparison_policy'])
        self.write('other-policy.json', dict(schema_version=1, limit=2))
        result = self.cli('prepare-canonical-child-trial', 'replaced', '--base-trial', 'growth',
                         '--comparison-policy', 'other-policy.json', ok=False)
        self.assertIn('cannot replace a frozen', result.stderr)
        self.assertFalse((self.root / 'replaced').exists())

    def test_missing_child_heading_vector_fails_before_any_teacher_call(self):
        from sse_multivector.test_canonical_selection_ranking import CanonicalSelectionRankingTests
        self.completed_base()
        self.probes = 0
        probe = CanonicalSelectionRankingTests.probe(self, {'Food': (1., 0.), 'Vegetables': (.8, .6)})
        self.write('policy.json', dict(schema_version=1, limit=1, subject_probe=str(probe)))
        start = len(self.calls())
        result = self.cli('prepare-canonical-child-trial', 'children', '--base-trial', 'trial',
                         '--comparison-policy', 'policy.json', ok=False)
        self.assertIn('missing saved SSE heading: Baby potatoes', result.stderr)
        self.assertEqual(len(self.calls()), start)
        self.assertFalse((self.root / 'children').exists())


    def test_growth_root_checks_omitted_descendant_before_insertion(self):
        self.completed_base(future_root=True, descendant=True)
        before = self.state()['nodes']
        start = len(self.calls())
        self.prepare_growth()
        self.continue_trial(directory='growth', nodes=1, attempts=4, env={
            'FIXTURE_RELATIONS': json.dumps({'Vegetables': {
                'C002': 'local_contains_canonical', 'C003': 'neither'}})})
        self.assertEqual(self.state('growth')['nodes'], before)
        self.assertEqual(self.state('growth')['steps'][-1]['status'], 'held')
        calls = self.comparison_calls(start)
        self.assertEqual([call['canonical']['id'] for call in calls], ['C002', 'C003'])
        self.assertEqual(calls[0]['local'], calls[1]['local'])

    def test_growth_guard_remains_pending_after_cap_and_resume(self):
        self.completed_base(future_root=True)
        before = self.state()['nodes']
        self.prepare_growth()
        relations = {'FIXTURE_RELATIONS': json.dumps({'Vegetables': {
            'C002': 'canonical_contains_local', 'C001': 'canonical_contains_local'}})}
        result = self.continue_trial(directory='growth', nodes=1, attempts=2, env=relations, ok=False)
        self.assertEqual(json.loads(result.stdout)['status'], 'attempt_limit')
        state = self.state('growth')
        self.assertEqual(state['nodes'], before)
        self.assertEqual(state['comparison_policy_steps'][str(state['index'])]['phase'], 'verification')
        count = len(self.calls())
        repeated = self.continue_trial(directory='growth', nodes=1, attempts=2, env=relations, ok=False)
        self.assertEqual(json.loads(repeated.stdout)['status'], 'attempt_limit')
        self.assertEqual(self.state('growth'), state)
        self.assertEqual(len(self.calls()), count)

    def test_initial_roots_support_policy_without_changing_first_bootstrap(self):
        self.completed_base()
        self.cli('prepare-canonical-trial', 'initial', '--spec', 'trial.json',
                 '--comparison-policy', 'policy.json')
        self.assertTrue(self.state('initial')['comparison_policy'])
        self.assertEqual(self.state('initial')['nodes'], [])
        self.continue_trial(directory='initial', nodes=2, attempts=5, env={
            'FIXTURE_RELATIONS': json.dumps({'Vegetables': {'C001': 'canonical_contains_local'}})})
        state = self.state('initial')
        self.assertEqual(state['status'], 'complete')
        self.assertEqual(state['nodes'][0]['meaning'], 'Food fixed meaning')
        self.assertEqual(state['nodes'][1]['parents'], ['C001'])
        self.assertNotIn('comparison_selection', state['steps'][0])
        self.assertEqual(state['steps'][1]['comparison_selection']['plan']['queried'], ['C001'])


if __name__ == '__main__':
    unittest.main()
