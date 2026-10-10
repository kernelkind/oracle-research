"""Incremental corpus growth through native preparation and offline receipts."""
import hashlib
from contextlib import redirect_stdout
from io import StringIO
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from sse_multivector import test_canonical_continuation as fixtures
from sse_multivector import experiment as workflow


class CanonicalGrowthTests(unittest.TestCase):
    setUp = fixtures.CanonicalContinuationTests.setUp
    write = fixtures.CanonicalContinuationTests.write
    cli = fixtures.CanonicalContinuationTests.cli
    calls = fixtures.CanonicalContinuationTests.calls
    setup_trial = fixtures.CanonicalContinuationTests.setup_trial
    dynamic_runner = fixtures.CanonicalContinuationTests.dynamic_runner
    shared = fixtures.CanonicalContinuationTests.shared
    continue_trial = fixtures.CanonicalContinuationTests.continue_trial

    def state(self, directory='base-children'):
        return json.loads((self.root / directory / 'state.json').read_text())

    def completed_base(self, held_child=False):
        self.dynamic_runner()
        self.setup_trial(schema_version=2, independent_meanings=True, root_order=[
            {'note_id': 'n1', 'number': '1'}, {'note_id': 'n2', 'number': '2'}])
        corpus = json.loads((self.root / 'notes.json').read_text())
        corpus['notes'][0]['subjects'].append(
            {'number': '1.1.1', 'subject': 'Old grandchild', 'context': 'Old deeper evidence'})
        corpus['notes'][1]['subjects'].extend([
            {'number': '2.1', 'subject': 'Other child', 'context': 'Second child evidence'},
            {'number': '2.1.1', 'subject': 'Other grandchild', 'context': 'Old deeper evidence'}])
        corpus['notes'][2]['subjects'].extend([
            {'number': '3.1', 'subject': 'New child', 'context': 'New child evidence'},
            {'number': '4', 'subject': 'New other root', 'context': 'Independent root evidence'}])
        corpus['notes'].append({'note_id': 'n4', 'text': 'Fourth post', 'subjects': [
            {'number': '1', 'subject': 'Fourth root', 'context': 'Fourth root evidence'}]})
        self.write('notes.json', corpus)
        self.cli('prepare-canonical-trial', 'base', '--spec', 'trial.json')
        self.shared()
        self.continue_trial(directory='base', nodes=2, attempts=20)
        self.cli('prepare-canonical-child-trial', 'base-children', '--base-trial', 'base')
        env = {'FIXTURE_RELATIONS': json.dumps({
            'EXCLUDED CHILD': {'C001': 'canonical_contains_local'},
            'Other child': {'C002': 'neither' if held_child else 'canonical_contains_local'}})}
        self.continue_trial(directory='base-children', nodes=2, attempts=20, env=env)
        self.assertEqual((self.state()['status'], self.state()['index']), ('complete', 4))
        config = json.loads((self.root / 'trial.json').read_text())
        config['roots'] = [{'note_id': 'n3', 'number': '3'}, {'note_id': 'n3', 'number': '4'}]
        self.write('growth.json', config)

    def prepare_growth(self, destination='growth', base='base-children', **kwargs):
        return self.cli('prepare-canonical-trial', destination, '--spec', 'growth.json',
                        '--base-trial', base, **kwargs)

    def test_native_append_preserves_root_child_history_and_meaning_receipts(self):
        self.completed_base()
        before = self.state()
        base_path = self.root / 'base-children/state.json'
        original = base_path.read_bytes()
        calls = len(self.calls())
        self.prepare_growth()
        after = self.state('growth')
        self.assertEqual(base_path.read_bytes(), original)
        self.assertEqual(len(self.calls()), calls)
        for field in ('index', 'nodes', 'steps', 'local_meanings', 'children'):
            self.assertEqual(after[field], before[field])
        self.assertEqual(after['roots'][:2], before['roots'])
        self.assertEqual(after['roots'][2:], json.loads((self.root / 'growth.json').read_text())['roots'])
        self.assertEqual([row['local'] for row in after['queue'][:4]],
                         [row['local'] for row in before['steps']])
        self.assertEqual(after['queue'][4], {'local': {'note_id': 'n3', 'number': '3'},
                                           'mapped_parent': None})
        self.assertEqual(after['sources'][str(base_path)], hashlib.sha256(original).hexdigest())
        shown = json.loads(self.cli('show', after['experiment'], '--case', 'bootstrap', '--json').stdout)
        self.assertEqual(json.loads(shown['inputs']['INPUT_JSON'])['local']['entry']['subject'], 'Ingredients')

    def completed_growth(self, env=None):
        self.completed_base()
        self.prepare_growth()
        self.continue_trial(directory='growth', nodes=2, attempts=30, env=env)
        self.assertEqual(self.state('growth')['status'], 'complete')

    def test_unused_root_from_existing_note_preserves_history_and_same_note_exclusion(self):
        self.completed_base()
        config = json.loads((self.root / 'growth.json').read_text())
        config['roots'] = [{'note_id': 'n3', 'number': '3'}]
        self.write('growth.json', config)
        self.prepare_growth('first-root')
        self.continue_trial(directory='first-root', nodes=1, attempts=10)
        before = self.state('first-root')
        self.assertEqual(before['nodes'][-1]['id'], 'C005')
        base_path = self.root / 'first-root/state.json'
        original = base_path.read_bytes()
        calls = len(self.calls())
        config['roots'] = [{'note_id': 'n3', 'number': '4'}]
        self.write('unused-root.json', config)

        self.cli('prepare-canonical-trial', 'unused-root', '--spec', 'unused-root.json',
                 '--base-trial', 'first-root')
        after = self.state('unused-root')
        self.assertEqual(base_path.read_bytes(), original)
        self.assertEqual(len(self.calls()), calls)
        for field in ('index', 'nodes', 'steps', 'local_meanings', 'children'):
            self.assertEqual(after[field], before[field])
        self.assertEqual(after['queue'][:-1], before['queue'])
        self.assertEqual(after['queue'][-1], {
            'local': {'note_id': 'n3', 'number': '4'}, 'mapped_parent': None})
        self.assertEqual(after['sources'][str(base_path)], hashlib.sha256(original).hexdigest())

        self.continue_trial(directory='unused-root', nodes=1, attempts=10)
        finished = self.state('unused-root')
        self.assertEqual(finished['status'], 'complete')
        shown = json.loads(self.cli('show', finished['steps'][-1]['experiment'], '--json').stdout)
        self.assertEqual([c['id'] for c in shown['cases']], ['C001', 'C002', 'C003', 'C004'])
        self.assertEqual(base_path.read_bytes(), original)
        calls = len(self.calls())
        budget = (self.root / 'shared.json').read_bytes()
        config['roots'] = [{'note_id': 'n3', 'number': '3'}]
        self.write('replay.json', config)
        result = self.cli('prepare-canonical-trial', 'replay', '--spec', 'replay.json',
                          '--base-trial', 'unused-root', ok=False)
        self.assertIn('replay', result.stderr)
        self.assertFalse((self.root / 'replay').exists())
        self.assertEqual(len(self.calls()), calls)
        self.assertEqual((self.root / 'shared.json').read_bytes(), budget)

    def test_scoped_new_children_use_mapped_parent_and_do_not_filter_future_old_children(self):
        self.completed_growth()
        before = self.state('growth')
        original = (self.root / 'growth/state.json').read_bytes()
        self.cli('prepare-canonical-child-trial', 'new-children', '--base-trial', 'growth',
                 '--note-id', 'n3')
        child = self.state('new-children')
        self.assertEqual(child['queue'][:6], before['queue'])
        self.assertEqual(child['queue'][6:], [
            {'local': {'note_id': 'n3', 'number': '3.1'}, 'mapped_parent': 'C005'}])
        self.assertEqual(child['steps'], before['steps'])
        self.continue_trial(directory='new-children', nodes=1, attempts=1, ok=False)
        shown = json.loads(self.cli('show', self.state('new-children')['experiment'], '--json').stdout)
        self.assertEqual([c['id'] for c in shown['cases']], ['C001', 'C002', 'C003', 'C004', 'C005'])
        # The same-note root C006 is excluded; the mapped C005 is the exception.
        self.assertEqual((self.root / 'growth/state.json').read_bytes(), original)
        self.cli('prepare-canonical-child-trial', 'all-children', '--base-trial', 'growth')
        self.assertEqual({(r['local']['note_id'], r['local']['number'])
                          for r in self.state('all-children')['queue'][6:]},
                         {('n1', '1.1.1'), ('n2', '2.1.1'), ('n3', '3.1')})

    def test_growth_and_scoped_child_continuations_finish_then_allow_another_new_note(self):
        self.completed_growth()
        self.cli('prepare-canonical-child-trial', 'new-children', '--base-trial', 'growth', '--note-id', 'n3')
        env = {'FIXTURE_RELATIONS': json.dumps({'New child': {'C005': 'canonical_contains_local'}})}
        self.continue_trial(directory='new-children', nodes=1, attempts=10, env=env)
        before = self.state('new-children')
        self.assertEqual((before['status'], before['index']), ('complete', 7))
        self.assertEqual(before['nodes'][-1]['id'], 'C007')
        self.assertEqual(before['nodes'][-1]['parents'], ['C005'])
        config = json.loads((self.root / 'growth.json').read_text())
        config['roots'] = [{'note_id': 'n4', 'number': '1'}]
        self.write('fourth.json', config)
        self.cli('prepare-canonical-trial', 'fourth', '--spec', 'fourth.json', '--base-trial', 'new-children')
        after = self.state('fourth')
        self.assertEqual(after['queue'][:7], before['queue'])
        self.assertEqual(after['queue'][7]['local'], {'note_id': 'n4', 'number': '1'})
        self.assertEqual(after['index'], 7)
        self.assertEqual(after['nodes'], before['nodes'])
        self.assertEqual(after['steps'], before['steps'])
        self.assertEqual(after['local_meanings'], before['local_meanings'])
        self.continue_trial(directory='fourth', nodes=1, attempts=10)
        self.assertEqual(self.state('fourth')['nodes'][-1]['id'], 'C008')
        plan = json.loads((self.root / 'fourth/continuation/plan.json').read_text())['plan']
        self.assertEqual((plan['start_index'], plan['end_index']), (7, 8))

    def test_growth_continuation_cap_and_queue_are_frozen_across_resumes(self):
        self.completed_base()
        self.prepare_growth()
        before_calls = len(self.calls())
        first = json.loads(self.continue_trial(directory='growth', nodes=2, attempts=1, ok=False).stdout)
        self.assertEqual(first['status'], 'attempt_limit')
        before = self.state('growth')
        self.assertEqual((before['index'], before['phase']), (4, 'comparison'))
        resumed = json.loads(self.continue_trial(directory='growth', nodes=2, attempts=1, ok=False).stdout)
        self.assertEqual(resumed['attempts']['used'], 1)
        self.assertEqual(self.state('growth'), before)
        self.assertEqual(len(self.calls()), before_calls + 1)
        self.assertIn('cannot change', self.continue_trial(directory='growth', nodes=2, attempts=2, ok=False).stderr)
        before['queue'][4:] = before['queue'][4:][::-1]
        self.write('growth/state.json', before)
        self.assertIn('cannot change', self.continue_trial(directory='growth', nodes=2, attempts=1, ok=False).stderr)
        self.assertEqual(len(self.calls()), before_calls + 1)

    def test_processed_queue_cannot_be_reordered_before_first_continuation(self):
        self.completed_base()
        self.prepare_growth()
        state = self.state('growth')
        state['queue'][0], state['queue'][1] = state['queue'][1], state['queue'][0]
        self.write('growth/state.json', state)
        before = len(self.calls())
        result = self.continue_trial(directory='growth', nodes=2, attempts=20, ok=False)
        self.assertIn('processed history', result.stderr)
        self.assertEqual(len(self.calls()), before)

    def test_scoped_mapped_parent_mismatch_holds_and_audit_includes_new_note(self):
        self.completed_growth()
        before = self.state('growth')
        self.cli('prepare-canonical-child-trial', 'new-children', '--base-trial', 'growth', '--note-id', 'n3')
        self.continue_trial(directory='new-children', nodes=1, attempts=10)
        after = self.state('new-children')
        self.assertEqual(after['status'], 'complete')
        self.assertEqual(after['nodes'], before['nodes'])
        self.assertEqual(after['steps'][-1]['status'], 'held')
        self.assertIn('mapped canonical parent', after['steps'][-1]['reason'])
        self.cli('audit-canonical-trial', 'new-children', '--output', 'grown-audit.json')
        audit = json.loads((self.root / 'grown-audit.json').read_text())
        self.assertEqual(audit['note_coverage']['selected_count'], 3)
        self.assertEqual(audit['note_coverage']['reachable_count'], 3)

    def test_new_parent_contradiction_holds_without_rewriting_old_history(self):
        env = {'FIXTURE_RELATIONS': json.dumps({
            'Ingredients': {'C001': 'local_contains_canonical'}})}
        self.completed_growth(env)
        grown = self.state('growth')
        held = grown['steps'][4]
        self.assertEqual(held['status'], 'held')
        self.assertIn('contradiction at C003', held['reason'])
        self.assertEqual(held['before'], held['after'])
        self.assertEqual(grown['steps'][:4], self.state()['steps'])

    def test_equivalence_preserves_old_meaning_ids_and_entry_prefix(self):
        env = {'FIXTURE_RELATIONS': json.dumps({'Ingredients': {
            'C001': 'equivalent', 'C003': 'local_contains_canonical'}})}
        self.completed_growth(env)
        grown = self.state('growth')
        original = self.state()['nodes'][0]
        equivalent = grown['nodes'][0]
        self.assertEqual(grown['steps'][4]['status'], 'equivalent')
        self.assertEqual(equivalent['meaning'], original['meaning'])
        self.assertEqual(equivalent['id'], original['id'])
        self.assertEqual(equivalent['entries'][:len(original['entries'])], original['entries'])
        self.assertEqual(equivalent['entries'][-1], {'note_id': 'n3', 'number': '3'})
        self.assertEqual(grown['nodes'][-1]['id'], 'C006')

    def test_invalid_growth_inputs_rejected_before_destination_or_attempts(self):
        self.completed_base()
        original = json.loads((self.root / 'growth.json').read_text())
        before_calls = len(self.calls())
        for roots, expected in [([{'note_id': 'n1', 'number': '1'}], 'replay'),
                                ([{'note_id': 'n3', 'number': '3'}] * 2, 'unique'),
                                ([{'note_id': 'n3', 'number': '3.1'}], 'unique')]:
            with self.subTest(roots=roots):
                self.write('growth.json', {**original, 'roots': roots})
                result = self.prepare_growth(ok=False)
                self.assertIn(expected, result.stderr)
                self.assertFalse((self.root / 'growth').exists())
        self.write('growth.json', original)
        self.prepare_growth()
        result = self.prepare_growth('replay', base='growth', ok=False)
        self.assertIn('completed raw', result.stderr)
        self.assertFalse((self.root / 'replay').exists())
        self.assertEqual(len(self.calls()), before_calls)

    def test_changed_frozen_base_blocks_next_attempt(self):
        self.completed_base()
        self.prepare_growth()
        before_calls = len(self.calls())
        before = self.state('growth')
        base = self.root / 'base-children/state.json'
        base.write_bytes(base.read_bytes() + b'\n')
        result = self.continue_trial(directory='growth', nodes=2, attempts=10, ok=False)
        self.assertIn('trial source changed', result.stderr)
        self.assertEqual(self.state('growth'), before)
        self.assertEqual(len(self.calls()), before_calls)

    def test_corpus_change_and_unknown_child_scope_are_rejected(self):
        self.completed_base()
        original = json.loads((self.root / 'growth.json').read_text())
        self.write('other-notes.json', json.loads((self.root / 'notes.json').read_text()))
        self.write('growth.json', {**original, 'corpus': 'other-notes.json'})
        self.assertIn('same frozen corpus', self.prepare_growth(ok=False).stderr)
        for options in [('--note-id', 'n3'), ('--note-id', 'n1', '--note-id', 'n1')]:
            result = self.cli('prepare-canonical-child-trial', 'scoped', '--base-trial',
                              'base-children', *options, ok=False)
            self.assertIn('unique notes', result.stderr)
            self.assertFalse((self.root / 'scoped').exists())

    def test_explicit_new_prompt_specs_only_change_incoming_work(self):
        self.completed_base()
        original = self.state()
        self.write('new-bootstrap.json', {**json.loads((self.root / 'bootstrap.json').read_text()),
                                          'prompt': {'id': 'BootstrapNew', 'path': 'new-prompt.txt'}})
        self.write('new-comparison.json', {**json.loads((self.root / 'comparison.json').read_text()),
                                           'prompt': {'id': 'CompareNew', 'path': 'new-prompt.txt'}})
        (self.root / 'new-prompt.txt').write_text('GENERIC PROMPT {INPUT_JSON}\n')
        config = json.loads((self.root / 'growth.json').read_text())
        config.update(bootstrap_spec='new-bootstrap.json', comparison_spec='new-comparison.json')
        self.write('growth.json', config)
        self.prepare_growth()
        state = self.state('growth')
        self.assertEqual(state['bootstrap_spec']['prompt']['id'], 'BootstrapNew')
        self.assertEqual(state['comparison_spec']['prompt']['id'], 'CompareNew')
        self.assertEqual(state['local_meanings'], original['local_meanings'])
        self.assertEqual(state['nodes'], original['nodes'])
        self.assertEqual(state['steps'], original['steps'])
        for path, digest in original['sources'].items():
            self.assertEqual(state['sources'][path], digest)
        self.assertIn(str(self.root / 'new-prompt.txt'), state['sources'])
        self.continue_trial(directory='growth', nodes=2, attempts=30)
        self.assertEqual(self.state('growth')['status'], 'complete')
        shown = json.loads(self.cli('show', self.state('growth')['steps'][4]['experiment'], '--json').stdout)
        self.assertEqual(shown['prompt_id'], 'CompareNew')

    def test_old_hold_stays_in_history_without_new_attempts_for_its_input(self):
        self.completed_base(held_child=True)
        original = self.state()
        self.assertEqual(original['steps'][3]['status'], 'held')
        before = len(self.calls())
        self.prepare_growth()
        self.continue_trial(directory='growth', nodes=2, attempts=30)
        self.assertEqual(self.state('growth')['steps'][:4], original['steps'])
        self.assertTrue(all(json.loads(c['prompt'].removeprefix('GENERIC PROMPT '))['local']['post']
                            == 'Third post' for c in self.calls()[before:]))

    def test_native_58_root_89_child_prefix_keeps_all_147_indices(self):
        self.dynamic_runner()
        self.setup_trial(schema_version=2, independent_meanings=True,
                         root_order=[{'note_id': 'n1', 'number': '1'}])
        subjects = []
        for root in range(1, 59):
            subjects.append({'number': str(root), 'subject': 'Root', 'context': 'Root evidence'})
            for child in range(1, 3 if root <= 31 else 2):
                subjects.append({'number': f'{root}.{child}', 'subject': 'Child', 'context': 'Child evidence'})
        self.write('notes.json', {'schema_version': 1, 'notes': [
            {'note_id': 'n1', 'text': 'Old post', 'subjects': subjects},
            {'note_id': 'n2', 'text': 'New post', 'subjects': [
                {'number': '1', 'subject': 'New root', 'context': 'New root evidence'}]}]})
        config = json.loads((self.root / 'trial.json').read_text())
        config['roots'] = [{'note_id': 'n1', 'number': str(i)} for i in range(1, 59)]
        self.write('wide.json', config)
        self.cli('prepare-canonical-trial', 'wide', '--spec', 'wide.json')
        self.shared(limit=300)
        self.continue_trial(directory='wide', nodes=58, attempts=100)
        self.cli('prepare-canonical-child-trial', 'wide-children', '--base-trial', 'wide')
        # Run the real CLI entry in-process: this larger native fixture exceeds
        # the small fixtures' 30-second subprocess envelope. Only its transport
        # is fake; preparation, receipts, reuse and transitions remain real.
        with redirect_stdout(StringIO()), patch.dict(os.environ, {
                'FAKE_RUNNER_LOG': str(self.log), 'FIXTURE_RELATION': 'canonical_contains_local'}):
            self.assertEqual(workflow.main([
                'continue-canonical-trial', str(self.root / 'wide-children'), '--max-nodes', '89',
                '--max-new-attempts', '200', '--attempt-budget', str(self.root / 'shared.json')]), 0)
        old = self.state('wide-children')
        self.assertEqual((len(old['roots']), len(old['children']), old['index']), (58, 89, 147))
        self.assertEqual(old['status'], 'complete')
        original = (self.root / 'wide-children/state.json').read_bytes()
        config['roots'] = [{'note_id': 'n2', 'number': '1'}]
        self.write('wide-growth.json', config)
        count = len(self.calls())
        self.cli('prepare-canonical-trial', 'wide-growth', '--spec', 'wide-growth.json',
                 '--base-trial', 'wide-children')
        grown = self.state('wide-growth')
        for key in ('nodes', 'steps', 'index', 'local_meanings', 'children'):
            self.assertEqual(grown[key], old[key])
        self.assertEqual([row['local'] for row in grown['queue'][:147]],
                         [step['local'] for step in old['steps']])
        self.assertEqual(grown['queue'][147]['local'], {'note_id': 'n2', 'number': '1'})
        self.assertEqual((self.root / 'wide-children/state.json').read_bytes(), original)
        self.assertEqual(len(self.calls()), count)


if __name__ == '__main__':
    unittest.main()
