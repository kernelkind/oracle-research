"""Exercise the approved construction policy through native CLI and receipts."""
import json
import os
from pathlib import Path
import subprocess
import unittest

from sse_multivector import test_experiment as fixtures


class CanonicalTraversalTests(unittest.TestCase):
    setUp = fixtures.ExperimentTests.setUp
    write = fixtures.ExperimentTests.write
    def cli(self, *args, ok=True, env=None):
        project = Path(__file__).resolve().parents[1]
        launcher = project.parent/'experiment-runner/bin/experiment-runner'
        result = subprocess.run([str(launcher), '--project-root', str(project), *map(str,args)],
            cwd=self.root, env={**os.environ, 'FAKE_RUNNER_LOG':str(self.log), **(env or {})},
            text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode == 0, ok, result.stderr+result.stdout)
        return result

    def prepare(self, count=4, extra_root=False):
        self.prompt.write_text('GENERIC PROMPT {INPUT_JSON}')
        subjects = lambda i: [dict(number='1', subject=f'Root {i}', context='Original role'),
                              dict(number='1.1', subject=f'Child {i}', context='Narrower role')]
        notes = [dict(note_id=f'n{i}', text=f'Original post {i}', subjects=subjects(i))
                 for i in range(count)]
        if extra_root:
            notes[0]['subjects'].append(dict(number='2', subject='Second root', context='Other'))
        self.write('notes.json', dict(schema_version=1, notes=notes))
        base = json.loads(self.spec.read_text())
        for name in ('bootstrap', 'comparison', 'consolidation'):
            schema = (json.loads(Path(__file__).with_name('shr_single_pair').joinpath(
                'Hierarchy-compare-v4.output.schema.json').read_text()) if name == 'comparison' else
                {'type': ['object', 'null'], 'properties': {
                    'title': {'type':'string'}, 'meaning': {'type':'string'},
                    'children': {'type':'array', 'items': {'type':'string'}}},
                 'required': ['title', 'meaning', 'children'], 'additionalProperties': False}
                if name == 'consolidation' else
                {'type':'object', 'properties':{'meaning':{'type':['string','null']}},
                 'required':['meaning'], 'additionalProperties':False})
            self.write(name+'.json', {**base, 'runner':{**base['runner'],
                **({} if name == 'consolidation' else {'output_schema':schema})}})
        self.write('traversal.json', dict(schema_version=1, corpus='notes.json',
            note_ids=[n['note_id'] for n in notes], local_schema_version=4,
            bootstrap_spec='bootstrap.json', comparison_spec='comparison.json',
            consolidation_spec='consolidation.json'))
        return self.cli('prepare-canonical-traversal', 'trial', '--spec', 'traversal.json')

    def state(self):
        return json.loads((self.root/'trial/state.json').read_text())

    def advance(self):
        return self.cli('advance-canonical-traversal', 'trial', '--comment', 'Fixture mechanics')

    def run_pending(self, answer):
        current = self.state()
        for record in current['experiments']:
            if 'answers' not in record:
                value = answer(record) if callable(answer) else answer
                self.cli('run', record['experiment'], env={
                    'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(value)})

    def test_rotates_l1_then_l2_and_prepares_only_three_concurrent_searches(self):
        self.prepare(extra_root=True)
        state = self.state()
        self.assertEqual([r['local'] for r in state['inventory']], [
            dict(note_id=f'n{i}', number='1') for i in range(4)] +
            [dict(note_id='n0', number='2')] +
            [dict(note_id=f'n{i}', number='1.1') for i in range(4)])
        self.assertEqual([s['local']['note_id'] for s in state['searches']], ['n0','n1','n2'])
        self.assertEqual(len(state['experiments']), 3)
        self.assertEqual(fixtures.ExperimentTests.calls(self), [])

    def test_stops_during_l1_saves_inflight_answers_and_keeps_unplaced_searches(self):
        self.prepare(count=1, extra_root=True)
        self.run_pending({'meaning': 'Independent root meaning'})
        self.advance()
        state = self.state()
        self.assertEqual(state['status'], 'complete')
        self.assertEqual(len(state['nodes']), 1)
        self.assertEqual(len(state['steps']), 1)
        self.assertTrue(state['stopping']['individual_access'])
        self.assertTrue(state['stopping']['strict_edges'])
        self.assertEqual(len(state['searches']), 2)
        self.assertTrue(all('answers' in e for e in state['experiments']))
        frozen = (self.root/'trial/state.json').read_bytes()
        self.advance()
        self.assertEqual((self.root/'trial/state.json').read_bytes(), frozen)

    def test_revalidates_concurrent_search_against_first_placement_without_rebootstrap(self):
        self.prepare()
        self.run_pending(lambda r: {'meaning': 'Meaning '+r['local']['note_id']})
        self.advance()
        state = self.state()
        self.assertEqual(len(state['nodes']), 1)
        self.assertEqual(len(state['searches']), 3)
        pending = [e for e in state['experiments'] if 'answers' not in e]
        comparison = next(e for e in pending if e['role'] == 'comparison')
        shown = json.loads(self.cli('show', comparison['experiment'], '--json').stdout)
        payload = json.loads(shown['cases'][0]['inputs']['INPUT_JSON'])
        self.assertEqual(payload['local']['meaning'], 'Meaning n1')
        self.assertEqual(payload['canonical']['subject'], 'Root 0')
        self.assertEqual(state['steps'][0]['local'], dict(note_id='n0', number='1'))

    def test_revalidation_reuses_unchanged_root_and_compares_only_new_roots(self):
        self.prepare(count=4)
        self.run_pending(lambda r: dict(meaning='Meaning '+r['local']['note_id']))
        self.advance()
        def answer(record):
            meaning = 'Meaning '+record['local']['note_id']
            return dict(meaning=meaning) if record['role']=='meaning' else dict(
                meaning=meaning, relation='neither', reason='Fixture distinct roots')
        self.run_pending(answer)
        self.advance()
        self.run_pending(answer)
        self.advance()
        records = [r for r in self.state()['experiments'] if r['role']=='comparison'
                   and r['local']==dict(note_id='n3',number='1')]
        self.assertEqual([list(r['inputs']) for r in records], [['C001'], ['C002','C003']])

    def test_rejected_native_producer_is_held_before_placement(self):
        self.prepare(count=2)
        self.run_pending(dict(meaning='Fixed meaning'))
        record = self.state()['experiments'][0]
        self.cli('review', record['experiment'], '--case', 'meaning', '--role', 'user',
                 '--verdict', 'reject', '--comment', 'Missing the established source role')
        self.advance()
        first = self.state()['steps'][0]
        self.assertEqual(first['status'], 'held')
        self.assertIn('user producer review reject', first['reason'])
        self.assertEqual(first['after'], first['before'])

    def test_relative_output_schema_paths_are_resolved_and_frozen(self):
        self.prepare(count=2)
        spec = json.loads((self.root/'comparison.json').read_text())
        schema = spec['runner'].pop('output_schema')
        self.write('compare-schema.json', schema)
        spec['runner']['output_schema_path'] = 'compare-schema.json'
        self.write('comparison.json', spec)
        self.cli('prepare-canonical-traversal', 'path-trial', '--spec', 'traversal.json')
        state = json.loads((self.root/'path-trial/state.json').read_text())
        self.assertIn(str(self.root/'compare-schema.json'), state['sources'])
        self.assertEqual(state['comparison_spec']['runner']['output_schema'], schema)

    def finish(self, proposal=None):
        """Run fixture answers through native admission and receipt validation."""
        for _ in range(60):
            state = self.state()
            if state['status'] in ('complete', 'exhausted'):
                return state
            for record in state['experiments']:
                if 'answers' in record:
                    continue
                shown = json.loads(self.cli('show', record['experiment'], '--json').stdout)
                for case in shown['cases']:
                    if case['status'] != 'unrun':
                        continue
                    if record['role'] == 'meaning':
                        value = {'meaning': 'Meaning '+record['local']['note_id']}
                    elif record['role'] == 'consolidation':
                        value = proposal if proposal and len(state['nodes']) == 7 else None
                    else:
                        payload = json.loads(case['inputs']['INPUT_JSON'])
                        relation = ('local_contains_canonical' if
                            payload['local']['subject'] == 'Group' and case['id'] in ('C001', 'C002')
                            else 'neither')
                        value = dict(meaning=payload['local']['meaning'], relation=relation, reason='Fixture')
                    self.cli('run', record['experiment'], '--only', case['id'], env={
                        'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(value)})
            self.advance()
        self.fail('fixture construction did not finish')

    def test_six_triggers_null_before_stop_and_does_not_retry_without_an_addition(self):
        self.prepare(count=7)
        state = self.finish()
        self.assertEqual(state['status'], 'complete')
        self.assertEqual(len(state['nodes']), 7)
        self.assertEqual([len(c['siblings']) for c in state['consolidations']], [6, 7])
        self.assertEqual([c['outcome'] for c in state['consolidations']], ['null', 'null'])
        before = len(fixtures.ExperimentTests.calls(self))
        self.advance()
        self.assertEqual(len(fixtures.ExperimentTests.calls(self)), before)

    def test_synthetic_validation_groups_two_roots_and_retriggers_at_six(self):
        self.prepare(count=7)
        state = self.finish(dict(title='Group', meaning='Group meaning', children=['C001', 'C002']))
        self.assertEqual(state['status'], 'complete')
        group = next(n for n in state['nodes'] if n['subject'] == 'Group')
        self.assertEqual(group['entries'], [])
        self.assertIn('synthetic', group)
        self.assertEqual([n['parents'] for n in state['nodes'] if n['id'] in ('C001', 'C002')],
                         [[group['id']], [group['id']]])
        self.assertEqual([len(c['siblings']) for c in state['consolidations']], [6, 7, 6])
        self.assertEqual([c['outcome'] for c in state['consolidations']], ['null', 'placed', 'null'])
        self.assertTrue(state['stopping']['strict_edges'])
        result = self.cli('audit-canonical-trial', 'trial', '--output', 'audit.json')
        self.assertTrue(json.loads(result.stdout)['structural_constraints_met'])

    def test_same_note_canonical_is_compared_and_equivalence_keeps_immutable_meaning(self):
        self.prepare(count=2, extra_root=True)
        self.run_pending(lambda r: {'meaning':'Meaning '+r['local']['note_id']})
        self.advance()
        record = next(r for r in self.state()['experiments'] if r['role']=='comparison')
        self.cli('run', record['experiment'], env={'FAKE_RUNNER_PROMPT_RESPONSE':json.dumps(
            dict(meaning='Meaning n1', relation='equivalent', reason='Fixture equivalence'))})
        self.advance()
        state = self.state()
        self.assertEqual(state['nodes'][0]['meaning'], 'Meaning n0')
        self.assertEqual(len(state['nodes'][0]['entries']), 2)
        record = next(r for r in state['experiments'] if r['role']=='comparison' and 'answers' not in r)
        self.assertEqual(record['local'], dict(note_id='n0', number='2'))
        self.assertEqual(list(record['inputs']), ['C001'])
        before = state['nodes']
        self.cli('run', record['experiment'], env={'FAKE_RUNNER_PROMPT_RESPONSE':json.dumps(
            dict(meaning='Meaning n0', relation='uncertain', reason='Unresolved fixture'))})
        self.advance()
        self.assertEqual(self.state()['nodes'], before)
        self.assertEqual(self.state()['steps'][-1]['status'], 'held')

    def test_native_invalid_grouping_keeps_all_existing_nodes(self):
        self.prepare(count=7)
        state = self.finish(dict(title='Group', meaning='Group meaning', children=['C001', 'C003']))
        self.assertEqual(state['status'], 'complete')
        self.assertEqual(len(state['nodes']), 7)
        self.assertFalse(any(n['subject']=='Group' for n in state['nodes']))
        self.assertIn('nominated-child', state['consolidations'][-1]['outcome'])

    def test_consolidation_adapter_rejects_invented_or_whole_group_children(self):
        from sse_multivector import experiment_inputs
        payload = dict(parent=None, siblings=[dict(id=f'C{i}', title='Topic', meaning='Meaning')
                                             for i in range(6)])
        case = dict(inputs={'INPUT_JSON':json.dumps(payload)})
        for children in (['C0','invented'], ['C0','C0'], ['C0'], [f'C{i}' for i in range(6)]):
            with self.subTest(children=children), self.assertRaises(ValueError):
                experiment_inputs.validate(dict(adapter='canonical_consolidation'), case,
                    json.dumps(dict(title='Parent', meaning='Fixed', children=children)), None)
        result = experiment_inputs.validate(dict(adapter='canonical_consolidation'), case, 'null', None)
        self.assertEqual(result['status'], 'valid')
        self.assertIsNone(result['parsed'])

    def test_unchecked_group_keeps_one_pending_attempt_when_another_addition_changes_it(self):
        from sse_multivector.canonical_traversal import _triggers
        nodes = [dict(id='P', parents=[])] + [dict(id=f'C{i}', parents=['P']) for i in range(7)]
        state = dict(nodes=nodes, pending_groups=[])
        _triggers(state, 'C5')
        _triggers(state, 'C6')
        self.assertEqual(state['pending_groups'], [dict(parent='P', added='C6')])

    def test_final_stop_does_not_offer_unrun_experiments_for_dispatch(self):
        self.prepare(count=1, extra_root=True)
        first = self.state()['experiments'][0]['experiment']
        self.cli('run', first, env={'FAKE_RUNNER_PROMPT_RESPONSE': '{"meaning":"One note root"}'})
        result = json.loads(self.advance().stdout)
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(result['experiments'], [])
        self.assertEqual(len(self.state()['searches']), 2)

    def test_source_and_receipt_changes_cannot_apply(self):
        self.prepare()
        self.run_pending({'meaning': 'Meaning'})
        first = Path(self.state()['experiments'][0]['experiment'])/'run/results.jsonl'
        saved = first.read_bytes()
        records = [json.loads(line) for line in saved.splitlines()]
        records[0]['final_output_raw'] = '{"meaning":"Tampered"}'
        first.write_text(''.join(json.dumps(r)+'\n' for r in records))
        before = (self.root/'trial/state.json').read_bytes()
        self.cli('advance-canonical-traversal', 'trial', '--comment', 'Must reject', ok=False)
        self.assertEqual((self.root/'trial/state.json').read_bytes(), before)
        first.write_bytes(saved)
        original = (self.root/'notes.json').read_bytes()
        (self.root/'notes.json').write_bytes(original+b'\n')
        self.cli('advance-canonical-traversal', 'trial', '--comment', 'Must reject', ok=False)
        self.assertEqual((self.root/'trial/state.json').read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
