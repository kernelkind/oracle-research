"""Ordinary insertion preserves settled comparisons between fixed meanings."""
import json
import unittest

from sse_multivector import test_canonical_continuation as fixtures


class CanonicalSettledRelationTests(unittest.TestCase):
    setUp = fixtures.CanonicalContinuationTests.setUp
    write = fixtures.CanonicalContinuationTests.write
    cli = fixtures.CanonicalContinuationTests.cli
    calls = fixtures.CanonicalContinuationTests.calls
    setup_trial = fixtures.CanonicalContinuationTests.setup_trial
    dynamic_runner = fixtures.CanonicalContinuationTests.dynamic_runner
    shared = fixtures.CanonicalContinuationTests.shared
    continue_trial = fixtures.CanonicalContinuationTests.continue_trial
    state = fixtures.CanonicalContinuationTests.state

    def test_ordinary_insertion_holds_changed_settled_neither(self):
        self.dynamic_runner()
        self.setup_trial(schema_version=2, independent_meanings=True)
        self.shared()
        relations = {'Ingredients': {'C001': 'canonical_contains_local',
                                      'C002': 'local_contains_canonical'}}
        self.continue_trial(attempts=6, env={'FIXTURE_RELATIONS': json.dumps(relations)})
        state = self.state()
        step = state['steps'][-1]
        self.assertEqual(step['status'], 'held')
        self.assertEqual(step['before'], step['after'])
        self.assertEqual(len(state['nodes']), 2)
        witness = step['settled_relation_contradiction']
        self.assertEqual(witness['source'], 'C002')
        self.assertEqual(witness['other'], 'C001')
        self.assertEqual(witness['previous_relation'], 'neither')
        self.assertEqual(witness['before_relation'], 'neither')
        self.assertEqual(witness['current_relation'], 'canonical_contains_local')
        self.assertEqual(witness['previous_answer'], state['steps'][1]['answers'][0])
        self.assertEqual(len(self.calls()), 6)

    def test_changed_settled_pair_is_checked_in_reverse_input_order(self):
        self.dynamic_runner()
        self.setup_trial(schema_version=2, independent_meanings=True, root_order=[
            {'note_id': 'n2', 'number': '2'}, {'note_id': 'n1', 'number': '1'},
            {'note_id': 'n3', 'number': '3'}])
        self.shared()
        relations = {'Ingredients': {'C001': 'local_contains_canonical',
                                      'C002': 'canonical_contains_local'}}
        self.continue_trial(attempts=6, env={'FIXTURE_RELATIONS': json.dumps(relations)})
        step = self.state()['steps'][-1]
        self.assertEqual(step['status'], 'held')
        self.assertEqual(step['before'], step['after'])
        witness = step['settled_relation_contradiction']
        self.assertEqual((witness['source'], witness['other']), ('C002', 'C001'))
        self.assertEqual(witness['current_relation'], 'local_contains_canonical')
        self.assertEqual(witness['previous_relation'], 'neither')

    def test_ordinary_parent_checks_settled_pair_excluded_by_same_note(self):
        self.dynamic_runner()
        self.setup_trial(schema_version=2, independent_meanings=True, extra_root=True)
        corpus = json.loads((self.root / 'notes.json').read_text())
        corpus['notes'][0]['subjects'].append({
            'number': '4', 'subject': 'Extra branch', 'context': 'Narrower fixed topic'})
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
        relations = {'Extra branch': {'C002': 'canonical_contains_local'},
                     'Other root': {'C001': 'local_contains_canonical',
                                    'C003': 'canonical_contains_local'}}
        self.continue_trial(nodes=4, attempts=8, directory='branches', env={
            'FIXTURE_RELATIONS': json.dumps(relations)})
        state = json.loads((self.root / 'branches/state.json').read_text())
        step = state['steps'][-1]
        self.assertEqual([a['id'] for a in step['answers']], ['C001', 'C003'])
        self.assertEqual(step['status'], 'held')
        self.assertEqual(step['before'], step['after'])
        witness = step['settled_relation_contradiction']
        self.assertEqual((witness['source'], witness['other']), ('C002', 'C001'))
        self.assertEqual(witness['previous_relation'], 'neither')
        self.assertEqual(witness['current_relation'], 'local_contains_canonical')
        self.assertEqual(len(self.calls()), 8)

    def test_compatible_ordinary_insertion_keeps_settled_relations(self):
        self.dynamic_runner()
        self.setup_trial(schema_version=2, independent_meanings=True)
        self.shared()
        relations = {'Food': {'C001': 'canonical_contains_local'},
                     'Ingredients': {'C001': 'canonical_contains_local',
                                      'C002': 'local_contains_canonical'}}
        self.continue_trial(attempts=6, env={'FIXTURE_RELATIONS': json.dumps(relations)})
        step = self.state()['steps'][-1]
        self.assertEqual(step['status'], 'added')
        self.assertNotIn('settled_relation_contradiction', step)
        self.assertEqual(len(self.state()['nodes']), 3)

    def test_unchanged_legacy_conflict_does_not_block_unrelated_placement(self):
        from contextlib import redirect_stdout
        from io import StringIO
        import os
        from unittest.mock import patch
        from sse_multivector import canonical_trial, experiment as workflow

        self.dynamic_runner()
        self.setup_trial(schema_version=2, independent_meanings=True, extra_root=True)
        self.shared()
        relations = {'Other root': {'C001': 'canonical_contains_local',
                                    'C002': 'local_contains_canonical'}}
        # Arrange the saved legacy failure through native continuation: the old
        # equivalence-only guard allowed this ordinary insertion. All answers,
        # receipts, budgets and states are generated by the production path.
        with patch.object(canonical_trial, '_settled_relation_contradiction', return_value=None):
            with redirect_stdout(StringIO()), patch.dict(os.environ, {
                    'FAKE_RUNNER_LOG': str(self.log), 'FIXTURE_RELATIONS': json.dumps(relations)}):
                self.assertEqual(workflow.main([
                    'continue-canonical-trial', str(self.root / 'trial'), '--max-nodes', '3',
                    '--max-new-attempts', '6', '--attempt-budget', str(self.root / 'shared.json')]), 0)
        before = self.state()
        self.assertEqual([s['status'] for s in before['steps']], ['added'] * 3)
        self.cli('run', before['experiment'], env={'FIXTURE_RELATIONS': '{}'})
        self.cli('advance-canonical-trial', 'trial', '--meaning-case', 'bootstrap',
                 '--comment', 'Native unrelated legacy follow-up')
        self.cli('run', self.state()['experiment'], env={'FIXTURE_RELATIONS': '{}'})
        self.cli('advance-canonical-trial', 'trial', '--meaning-case', 'C001',
                 '--comment', 'Native unrelated legacy follow-up')
        after = self.state()
        self.assertEqual(after['steps'][-1]['status'], 'added')
        self.assertNotIn('settled_relation_contradiction', after['steps'][-1])
        self.assertEqual(after['steps'][-1]['before'], before['nodes'])
        self.assertEqual(len(after['nodes']), 4)
