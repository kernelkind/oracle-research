"""Exercise child-level continuation through the production experiment CLI."""
import json
from pathlib import Path
import unittest

from sse_multivector import test_experiment as fixtures
from sse_multivector import test_canonical_trial as roots_fixtures


class CanonicalChildTrialTests(unittest.TestCase):
    setUp = fixtures.ExperimentTests.setUp
    write = fixtures.ExperimentTests.write
    cli = fixtures.ExperimentTests.cli
    setup_trial = roots_fixtures.CanonicalTrialTests.setup_trial

    def state(self, directory='base'):
        return json.loads((self.root / directory / 'state.json').read_text())

    def answer(self, value, directory='base'):
        self.cli('run', self.state(directory)['experiment'], env={
            'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(value)})

    def advance(self, case, directory='base', **kwargs):
        return self.cli('advance-canonical-trial', directory, '--meaning-case', case,
                        '--comment', 'Reviewed fixture meaning', **kwargs)

    def completed_base(self, relation='equivalent', held=False):
        self.setup_trial(schema_version=2)
        corpus = json.loads((self.root / 'notes.json').read_text())
        corpus['notes'][0]['subjects'].append({
            'number': '1.1.1', 'subject': 'GRANDCHILD', 'context': 'Never selected at L2'})
        for note, number in zip(corpus['notes'][1:], ('2.1', '3.1')):
            note['subjects'].append({'number': number, 'subject': 'Immediate child',
                                     'context': 'Original child context'})
        self.write('notes.json', corpus)
        self.cli('prepare-canonical-trial', 'base', '--spec', 'trial.json')
        self.answer({'meaning': 'Fixed shared meaning'})
        self.advance('bootstrap')
        self.answer({'meaning': 'Equivalent second wording', 'relation': relation,
                     'reason': 'Same fixture topic'})
        self.advance('C001')
        self.answer({'meaning': 'Single-note independent topic', 'relation': 'neither',
                     'reason': 'Independent fixture topic'})
        if held:
            self.cli('advance-canonical-trial', 'base', '--meaning-case', 'C001',
                     '--comment', 'Reviewed held fixture', '--hold', 'Fixture holds original root')
        else:
            self.advance('C001')
        self.assertEqual(self.state()['status'], 'complete')

    def test_independent_child_meaning_precedes_mapped_parent_comparison(self):
        self.setup_trial(schema_version=2, independent_meanings=True, root_order=[
            {'note_id': 'n1', 'number': '1'}, {'note_id': 'n2', 'number': '2'}])
        self.answer({'meaning': 'Original canonical meaning'}, directory='trial')
        self.advance('bootstrap', directory='trial')
        self.answer({'meaning': 'Equivalent local meaning'}, directory='trial')
        self.advance('bootstrap', directory='trial')
        self.answer({'meaning': 'Equivalent local meaning', 'relation': 'equivalent',
                     'reason': 'Same fixture topic'}, directory='trial')
        self.advance('C001', directory='trial')
        self.cli('prepare-canonical-child-trial', 'children', '--base-trial', 'trial')
        self.assertEqual(self.state('children')['phase'], 'meaning')
        self.answer({'meaning': 'Independent child meaning'}, directory='children')
        self.advance('bootstrap', directory='children')
        payload = self.payload('C001')
        self.assertEqual(payload['local']['meaning'], 'Independent child meaning')
        self.assertEqual(payload['canonical']['meaning'], 'Original canonical meaning')
        self.answer({'meaning': 'Independent child meaning', 'relation': 'canonical_contains_local',
                     'reason': 'Mapped parent contains child'}, directory='children')
        self.advance('C001', directory='children')
        state = self.state('children')
        self.assertEqual(state['status'], 'complete')
        self.assertEqual(state['nodes'][-1]['id'], 'C003')
        self.assertEqual(state['nodes'][-1]['parents'], ['C001'])
        self.assertEqual(state['nodes'][-1]['meaning'], 'Independent child meaning')
        self.assertEqual(state['nodes'][0]['meaning'], 'Original canonical meaning')

    def test_single_note_parent_child_is_still_compared(self):
        self.completed_base()
        state = self.prepare_children()
        self.assertIn({'local': {'note_id': 'n3', 'number': '3.1'},
                       'mapped_parent': 'C003'}, state['children'])

    def test_failed_mapped_parent_comparison_can_be_held_without_changing_graph(self):
        self.completed_base()
        self.prepare_children()
        failed_experiment = self.state('children')['experiment']
        self.cli('run', failed_experiment, ok=False, env={'FAKE_RUNNER_FAIL_STAGE': 'prompt'})
        before = self.state('children')
        ledger = Path(failed_experiment) / 'run/results.jsonl'
        old_receipts = ledger.read_bytes()
        calls_before = len(fixtures.ExperimentTests.calls(self))
        self.cli('advance-canonical-trial', 'children', '--meaning-case', 'C001',
                 '--comment', 'Mapped parent comparison failed; no relationships can be applied',
                 '--hold', 'Unresolved mapped-parent comparison')
        state = self.state('children')
        self.assertEqual(state['index'], before['index'] + 1)
        self.assertEqual(state['nodes'], before['nodes'])
        held = state['steps'][-1]
        self.assertEqual(held['status'], 'held')
        self.assertEqual(held['mapped_parent'], 'C001')
        self.assertIsNone(held['selected_meaning'])
        self.assertTrue(all(a['status'] == 'failed' for a in held['answers']))
        self.assertEqual(ledger.read_bytes(), old_receipts)
        self.assertEqual(len(fixtures.ExperimentTests.calls(self)), calls_before)

    def test_preparation_selects_immediate_children_and_preserves_completed_base(self):
        self.completed_base()
        before_bytes = (self.root / 'base/state.json').read_bytes()
        before = self.state()
        self.cli('prepare-canonical-child-trial', 'children', '--base-trial', 'base')
        after = self.state('children')
        self.assertEqual((self.root / 'base/state.json').read_bytes(), before_bytes)
        for field in ('roots', 'steps', 'index', 'nodes', 'bootstrap_spec', 'comparison_spec'):
            self.assertEqual(after[field], before[field])
        self.assertEqual(after['children'], [
            {'local': {'note_id': 'n1', 'number': '1.1'}, 'mapped_parent': 'C001'},
            {'local': {'note_id': 'n2', 'number': '2.1'}, 'mapped_parent': 'C001'},
            {'local': {'note_id': 'n3', 'number': '3.1'}, 'mapped_parent': 'C003'}])
        source = json.loads((Path(after['experiment']).parent / 'source.json').read_text())
        self.assertEqual([p['id'] for p in source['pairs']], ['C001', 'C003'])
        self.assertEqual(source['pairs'][0]['local'], after['children'][0]['local'])


    def prepare_children(self):
        self.cli('prepare-canonical-child-trial', 'children', '--base-trial', 'base')
        return self.state('children')

    def payload(self, case, directory='children'):
        shown = json.loads(self.cli('show', self.state(directory)['experiment'],
                                   '--case', case, '--json').stdout)
        return json.loads(shown['inputs']['INPUT_JSON'])

    def test_all_immediate_children_include_recursive_single_note_branches(self):
        self.completed_base(relation='canonical_contains_local')
        state = self.prepare_children()
        self.assertEqual(state['children'], [
            {'local': {'note_id': 'n1', 'number': '1.1'}, 'mapped_parent': 'C001'},
            {'local': {'note_id': 'n2', 'number': '2.1'}, 'mapped_parent': 'C002'},
            {'local': {'note_id': 'n3', 'number': '3.1'}, 'mapped_parent': 'C003'}])
        payload = self.payload('C001')
        self.assertEqual([n['id'] for n in payload['canonical']['descendants']], ['C002'])
        self.assertEqual(payload['canonical']['descendants'][0]['parents'], ['C001'])
        self.assertEqual(payload['local']['post'], 'First post')
        self.assertNotIn('GRANDCHILD', json.dumps(payload))
        self.assertNotIn('descendants', payload['local'])

    def test_roots_without_immediate_children_finish_without_new_experiments(self):
        self.setup_trial(same_note=True, schema_version=2)
        corpus = json.loads((self.root / 'notes.json').read_text())
        corpus['notes'][0]['subjects'] = [row for row in corpus['notes'][0]['subjects']
                                         if '.' not in row['number']]
        self.write('notes.json', corpus)
        self.cli('prepare-canonical-trial', 'base', '--spec', 'trial.json')
        for i in range(3):
            self.answer({'meaning': f'Independent root {i}'})
            self.advance('bootstrap')
        self.prepare_children()
        state = self.state('children')
        self.assertEqual(state['children'], [])
        self.assertEqual(state['status'], 'complete')
        self.assertIsNone(state['experiment'])
        self.assertEqual(len(fixtures.ExperimentTests.calls(self)), 3)

    def test_held_original_root_child_is_unmapped_and_compared_normally(self):
        self.completed_base(held=True)
        state = self.prepare_children()
        self.assertEqual([x['local']['note_id'] for x in state['children']], ['n1', 'n2', 'n3'])
        self.assertEqual(state['children'][-1]['mapped_parent'], None)
        self.assertFalse(any(n['id'] == 'C003' for n in state['nodes']))
        answer = {'meaning': 'Independent child meaning', 'relation': 'neither',
                  'reason': 'Separate fixture topic'}
        for _ in range(2):
            self.answer(answer, directory='children')
            self.advance('C001', directory='children')
            self.assertEqual(self.state('children')['steps'][-1]['status'], 'held')
        payload = self.payload('C001')
        self.assertEqual(payload['local']['post'], 'Third post')
        self.assertEqual(payload['local']['entry']['subject'], 'Immediate child')
        self.assertEqual(payload['local']['entry']['ancestors'][-1]['subject'], 'Ingredients')
        self.answer(answer, directory='children')
        self.advance('C001', directory='children')
        final = self.state('children')
        self.assertEqual(final['status'], 'complete')
        self.assertEqual(final['steps'][-1]['status'], 'added')
        self.assertEqual(final['nodes'][-1]['parents'], [])

    def test_incomplete_base_is_rejected_without_destination(self):
        self.setup_trial(schema_version=2)
        self.cli('prepare-canonical-child-trial', 'children', '--base-trial', 'trial', ok=False)
        self.assertFalse((self.root / 'children').exists())

    def test_changed_base_state_is_source_bound_before_child_placement(self):
        self.completed_base()
        self.prepare_children()
        self.answer({'meaning': 'Narrower child meaning', 'relation': 'canonical_contains_local',
                     'reason': 'Contained fixture'}, directory='children')
        before = self.state('children')
        path = self.root / 'base/state.json'
        path.write_bytes(path.read_bytes() + b'\n')
        result = self.advance('C001', directory='children', ok=False)
        self.assertIn('trial source changed', result.stderr)
        self.assertEqual(self.state('children'), before)

    def test_mapped_parent_mismatch_and_uncertainty_hold_without_graph_changes(self):
        self.completed_base()
        for relation in ('neither', 'local_contains_canonical', 'uncertain'):
            with self.subTest(relation=relation):
                directory = 'children-' + relation
                self.cli('prepare-canonical-child-trial', directory, '--base-trial', 'base')
                before = self.state(directory)['nodes']
                self.answer({'meaning': 'Child fixture meaning', 'relation': relation,
                             'reason': 'Fixture does not establish original-parent containment'},
                            directory=directory)
                self.advance('C001', directory=directory)
                state = self.state(directory)
                self.assertEqual(state['nodes'], before)
                self.assertEqual(state['steps'][-1]['status'], 'held')
                self.assertEqual(state['index'], 4)
                self.assertTrue(state['steps'][-1]['reason'])

    def test_child_continuation_runs_next_batch_and_keeps_ids_and_meanings(self):
        self.completed_base()
        before_bytes = (self.root / 'base/state.json').read_bytes()
        before = self.state()
        self.prepare_children()
        answer = {'meaning': 'Narrow child meaning', 'relation': 'canonical_contains_local',
                  'reason': 'Both fixture parents contain this child'}
        self.answer(answer, directory='children')
        result = self.cli('advance-canonical-trial', 'children', '--meaning-case', 'C001',
                          '--comment', 'Reviewed child', '--run-next', '--max-new-attempts', '3',
                          env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(answer)})
        state = self.state('children')
        self.assertEqual(state['index'], 4)
        self.assertEqual(state['nodes'][-1]['id'], 'C004')
        self.assertEqual(state['nodes'][-1]['parents'], ['C001', 'C003'])
        self.assertEqual(state['nodes'][0]['meaning'], 'Fixed shared meaning')
        self.assertEqual(state['roots'], before['roots'])
        self.assertEqual(state['steps'][:3], before['steps'])
        batch = json.loads(result.stdout)['next_review']
        self.assertEqual(batch['summary']['valid'], 3)
        self.assertEqual(batch['local']['entry']['subject'], 'Immediate child')
        self.advance('C001', directory='children')
        second = self.state('children')
        self.assertEqual(second['index'], 5)
        self.assertEqual(second['nodes'][-1]['id'], 'C005')
        self.assertEqual(second['nodes'][-1]['parents'], ['C004'])
        self.answer(answer, directory='children')
        self.advance('C003', directory='children')
        final = self.state('children')
        self.assertEqual(final['status'], 'complete')
        self.assertEqual(final['index'], 6)
        self.assertEqual(final['nodes'][-1]['id'], 'C006')
        self.assertEqual(final['nodes'][-1]['parents'], ['C005'])
        self.assertEqual((self.root / 'base/state.json').read_bytes(), before_bytes)

    def test_original_mapped_parent_is_only_same_note_exception(self):
        self.setup_trial(schema_version=2)
        corpus = json.loads((self.root / 'notes.json').read_text())
        corpus['notes'][0]['subjects'].extend([
            {'number': '4', 'subject': 'Other same-note root', 'context': 'Independent'},
            {'number': '4.1', 'subject': 'Other child', 'context': 'Single-note branch'}])
        corpus['notes'][1]['subjects'].append({
            'number': '2.1', 'subject': 'Second shared child', 'context': 'Original context'})
        self.write('notes.json', corpus)
        self.cli('prepare-canonical-trial', 'base', '--spec', 'trial.json')
        for meaning in ('Fixed shared meaning', 'Independent same-note root'):
            self.answer({'meaning': meaning})
            self.advance('bootstrap')
        self.cli('run', self.state()['experiment'], '--max-new-attempts', '1', ok=False,
                 env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps({
                     'meaning': 'Same topic', 'relation': 'equivalent', 'reason': 'Shared'})})
        self.answer({'meaning': 'Same topic', 'relation': 'neither', 'reason': 'Independent'})
        self.advance('C001')
        self.answer({'meaning': 'Third independent topic', 'relation': 'neither',
                     'reason': 'Independent'})
        self.advance('C001')
        state = self.prepare_children()
        self.assertEqual([c['local']['number'] for c in state['children']], ['1.1', '2.1', '4.1'])
        source = json.loads((Path(state['experiment']).parent / 'source.json').read_text())
        self.assertEqual([p['id'] for p in source['pairs']], ['C001', 'C004'])
        self.assertNotIn('C002', [p['id'] for p in source['pairs']])

    def test_later_level_does_not_repeat_processed_immediate_children(self):
        self.completed_base()
        self.prepare_children()
        answer = {'meaning': 'Unplaced child fixture', 'relation': 'neither',
                  'reason': 'Separate fixture topic'}
        for case in ('C001', 'C001', 'C003'):
            self.answer(answer, directory='children')
            self.advance(case, directory='children')
        before = self.state('children')
        self.assertEqual(before['status'], 'complete')
        self.cli('prepare-canonical-child-trial', 'later', '--base-trial', 'children')
        later = self.state('later')
        self.assertEqual(later['children'][:3], before['children'])
        self.assertEqual(later['children'][3:], [
            {'local': {'note_id': 'n1', 'number': '1.1.1'}, 'mapped_parent': None}])
        self.assertEqual(later['index'], 6)

    def test_equivalent_child_adds_support_without_rewriting_canonical_meaning(self):
        self.completed_base()
        self.prepare_children()
        # The first eligible node is the mapped original parent; the other is independent.
        self.cli('run', self.state('children')['experiment'], '--max-new-attempts', '1', ok=False,
                 env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps({
                     'meaning': 'Rephrased child meaning', 'relation': 'equivalent',
                     'reason': 'Equivalent fixture'})})
        self.answer({'meaning': 'Rephrased child meaning', 'relation': 'neither',
                     'reason': 'Separate fixture topic'}, directory='children')
        self.advance('C001', directory='children')
        state = self.state('children')
        self.assertEqual(len(state['nodes']), 2)
        self.assertEqual(state['nodes'][0]['meaning'], 'Fixed shared meaning')
        self.assertIn({'note_id': 'n1', 'number': '1.1'}, state['nodes'][0]['entries'])
        self.assertEqual(state['steps'][-1]['status'], 'equivalent')


if __name__ == '__main__':
    unittest.main()
