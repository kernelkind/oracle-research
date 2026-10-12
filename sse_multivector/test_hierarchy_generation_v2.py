"""V2 selection and finishing through production preparation and construction."""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

from sse_multivector.canonical_hierarchy_shape import finish_nodes
from sse_multivector.canonical_trial import _note_sets
from sse_multivector import test_canonical_traversal as traversal_fixture


class V2NativeTests(unittest.TestCase):
    setUp = traversal_fixture.CanonicalTraversalTests.setUp
    write = traversal_fixture.CanonicalTraversalTests.write
    cli = traversal_fixture.CanonicalTraversalTests.cli
    prepare = traversal_fixture.CanonicalTraversalTests.prepare
    state = traversal_fixture.CanonicalTraversalTests.state
    advance = traversal_fixture.CanonicalTraversalTests.advance
    automatic_fixture = traversal_fixture.CanonicalTraversalTests.automatic_fixture
    automatic_run = traversal_fixture.CanonicalTraversalTests.automatic_run

    def cached_runner(self):
        fixture = Path(__file__).resolve().parents[2]/'experiment-runner/tests/fixtures/fake-runner.py'
        self.runner.write_text(fixture.read_text().replace(
            'if prompt.startswith("GENERIC PROMPT"):',
            'if prompt.startswith("GENERIC PROMPT") or prompt.startswith("Prominence estimates"):'))

    def test_short_real_prominence_prefix_does_not_inherit_bootstrap_caching(self):
        self.cached_runner()
        self.prepare(count=2, runner_overrides=dict(prompt_cache=True,
            model='gpt-6.1-sol', transport='sse'),
            prompt_text='GENERIC PROMPT '+('Fixed instruction. '*1100)+'{INPUT_JSON}')
        state = self.state()
        self.assertTrue(state['bootstrap_spec']['runner']['prompt_cache'])
        self.assertTrue(state['comparison_spec']['runner']['prompt_cache'])
        self.assertTrue(state['consolidation_spec']['runner']['prompt_cache'])
        self.assertFalse(state['prominence_spec']['runner']['prompt_cache'])
        meaning = state['experiments'][0]['experiment']
        self.cli('run', meaning, env={'FAKE_RUNNER_PROMPT_RESPONSE':'{"meaning":"Fixed"}'})
        self.advance()
        prominence = next(r for r in self.state()['experiments'] if r['role']=='prominence')
        envelope = json.loads((Path(prominence['experiment'])/'experiment.json').read_text())
        self.assertNotIn('cache_warmup', envelope['plan'])
        self.assertTrue(envelope['plan']['prompt']['text'].startswith('Prominence estimates'))
        self.cli('run', prominence['experiment'], env={'FAKE_RUNNER_PROMPT_RESPONSE':json.dumps(dict(
            prominence=60, missing_meaning='Other', allocation=[dict(
                meaning='Complete post', points=100, represented=60, missing=40)]))})
        self.advance()
        self.assertTrue(all('prominence' in row for row in self.state()['inventory'] if '.' not in row['local']['number']))

    def test_separate_project_continuation_requires_reviewed_source_rebinding(self):
        project = Path(__file__).resolve().parents[1]
        self.project = self.root/'original-project'
        (self.project/'sse_multivector').mkdir(parents=True)
        shutil.copy2(project/'experiment-runner.json', self.project)
        for path in (project/'sse_multivector').glob('*.py'):
            shutil.copy2(path, self.project/'sse_multivector')
        shutil.copytree(project/'sse_multivector/prominence-prompt-goal-v1/ppv35-post-meaning-v1',
                        self.project/'sse_multivector/prominence-prompt-goal-v1/ppv35-post-meaning-v1')
        self.automatic_fixture(count=2, roots_only=True)
        self.write('allowance.json', dict(schema_version=1, limit=2, used=0))
        self.automatic_run(ok=False)
        saved = self.state()
        calls = traversal_fixture.fixtures.ExperimentTests.calls(self)
        receipts = {Path(r['experiment'])/'run/results.jsonl':
                    (Path(r['experiment'])/'run/results.jsonl').read_bytes()
                    for r in saved['experiments'] if 'answers' in r}
        new_project = self.root/'continuation-project'
        shutil.copytree(self.project, new_project)
        code = new_project/'sse_multivector/canonical_traversal.py'
        code.write_text(code.read_text()+'\n# Reviewed continuation fix.\n')
        self.project = new_project
        refused = self.automatic_run(ok=False)
        self.assertIn('trial source binding changed', refused.stderr)
        self.assertEqual(traversal_fixture.fixtures.ExperimentTests.calls(self), calls)
        self.write('allowance.json', dict(schema_version=1, limit=20, used=2))
        result = self.cli('run-canonical-traversal', 'trial', '--attempt-budget', 'allowance.json',
                          '--runner-upgrade-reason', 'Reviewed fix in isolated continuation checkout')
        self.assertEqual(json.loads(result.stdout)['status'], 'complete')
        state = self.state()
        for field in ('corpus','note_ids','bootstrap_spec','comparison_spec','consolidation_spec'):
            self.assertEqual(state[field], saved[field])
        self.assertEqual(state['experiments'][0], saved['experiments'][0])
        for path, raw in receipts.items():
            self.assertEqual(path.read_bytes(), raw)
        self.assertGreaterEqual(json.loads((self.root/'allowance.json').read_text())['used'], 2)
        upgrade = state['source_upgrades'][0]
        self.assertEqual(upgrade['reason'], 'Reviewed fix in isolated continuation checkout')
        self.assertIn(str(code), upgrade['after'])
        self.assertIn(str(code), state['sources'])
        old_code = self.root/'original-project/sse_multivector/canonical_traversal.py'
        self.assertIn(str(old_code), upgrade['before'])
        self.assertNotIn(str(old_code), state['sources'])

    def test_reviewed_upgrade_preserves_failed_unprepared_batch_and_meaning_receipts(self):
        self.cached_runner()
        project = Path(__file__).resolve().parents[1]
        self.project = self.root/'original-project'
        (self.project/'sse_multivector').mkdir(parents=True)
        shutil.copy2(project/'experiment-runner.json', self.project)
        for path in (project/'sse_multivector').glob('*.py'):
            shutil.copy2(path, self.project/'sse_multivector')
        shutil.copytree(project/'sse_multivector/prominence-prompt-goal-v1/ppv35-post-meaning-v1',
                        self.project/'sse_multivector/prominence-prompt-goal-v1/ppv35-post-meaning-v1')
        old_code = self.project/'sse_multivector/canonical_traversal.py'
        old_code.write_text(old_code.read_text().replace('    _prominence_cache(prominence_spec)\n', ''))
        original_code = old_code.read_bytes()
        self.prepare(count=2, runner_overrides=dict(prompt_cache=True,
            model='gpt-6.1-sol', transport='sse'),
            prompt_text='GENERIC PROMPT '+('Fixed instruction. '*1100)+'{INPUT_JSON}')
        self.write('allowance.json', dict(schema_version=1, limit=3, used=0))
        meaning = self.state()['experiments'][0]['experiment']
        self.cli('run', meaning, '--attempt-budget', 'allowance.json',
                 env={'FAKE_RUNNER_PROMPT_RESPONSE':'{"meaning":"Fixed"}'})
        failed = self.cli('advance-canonical-traversal','trial','--comment','Collect meanings',ok=False)
        self.assertIn('829 estimated o200k_base tokens; minimum is 1,024', failed.stderr)
        saved = self.state()
        native = Path(meaning)
        preserved = {path: path.read_bytes() for path in (native/'experiment.json',
            native/'run/results.jsonl', self.root/'trial/batch-00000/source.json',
            self.root/'trial/batch-00000/spec.json', self.prompt)}
        partial = self.root/'trial/batch-00001'
        partial_bytes = {name: (partial/name).read_bytes() for name in ('source.json','spec.json')}
        self.assertFalse((partial/'experiment').exists())
        calls = traversal_fixture.fixtures.ExperimentTests.calls(self)
        counter = (self.root/'allowance.json').read_bytes()
        new_project = self.root/'continuation-project'
        shutil.copytree(self.project, new_project)
        shutil.copy2(project/'sse_multivector/canonical_traversal.py',
                     new_project/'sse_multivector/canonical_traversal.py')
        self.project = new_project
        interruption = subprocess.run([sys.executable, '-c', '''
from pathlib import Path
import sys
from unittest.mock import patch
sys.path.insert(0, sys.argv[1])
sys.path.insert(0, sys.argv[3])
from sse_multivector import canonical_traversal as traversal
original = traversal.workflow.write
def interrupted(path, value):
    if Path(path).name == 'state.json':
        raise OSError('simulated state-write interruption')
    return original(path, value)
with patch.object(traversal.workflow, 'write', interrupted):
    traversal._resume_sources(Path(sys.argv[2]), 'Native prefix eligibility fix; original inputs preserved')
''', str(new_project), str(self.root/'trial'), str(project.parent/'experiment-runner')],
            capture_output=True, text=True)
        self.assertNotEqual(interruption.returncode, 0)
        self.assertIn('simulated state-write interruption', interruption.stderr)
        self.assertFalse(partial.exists())
        self.cli('run-canonical-traversal','trial','--attempt-budget','allowance.json',
            '--runner-upgrade-reason','Native prefix eligibility fix; original inputs preserved',ok=False)
        state = self.state()
        self.assertEqual((self.root/'allowance.json').read_bytes(), counter)
        self.assertEqual(traversal_fixture.fixtures.ExperimentTests.calls(self), calls)
        self.assertEqual(old_code.read_bytes(), original_code)
        for path, raw in preserved.items():
            self.assertEqual(path.read_bytes(), raw)
        for field in ('corpus','note_ids','bootstrap_spec','comparison_spec','consolidation_spec'):
            self.assertEqual(state[field], saved[field])
        self.assertEqual(state['experiments'][0]['inputs'], saved['experiments'][0]['inputs'])
        self.assertFalse(state['prominence_spec']['runner']['prompt_cache'])
        upgrade = state['source_upgrades'][0]
        self.assertEqual(upgrade['prominence_cache']['policy']['estimated_prefix_tokens'], 829)
        self.assertEqual(upgrade['unprepared_batch']['model_attempts'], 0)
        archive = Path(upgrade['unprepared_batch']['after'])
        for name, raw in partial_bytes.items():
            self.assertEqual((archive/name).read_bytes(), raw)
        self.assertEqual((partial/'source.json').read_bytes(), partial_bytes['source.json'])
        self.assertFalse(json.loads((partial/'spec.json').read_text())['runner']['prompt_cache'])
        self.write('allowance.json', dict(schema_version=1, limit=20, used=3))
        prominence = state['experiments'][1]['experiment']
        self.cli('run',prominence,'--attempt-budget','allowance.json',env={
            'FAKE_RUNNER_PROMPT_RESPONSE':json.dumps(dict(prominence=60, missing_meaning='Other',
                allocation=[dict(meaning='Complete post',points=100,represented=60,missing=40)]))})
        self.advance()
        comparison = self.state()['experiments'][2]['experiment']
        self.cli('run',comparison,'--attempt-budget','allowance.json',env={
            'FAKE_RUNNER_PROMPT_RESPONSE':'{"meaning":"Fixed","relation":"neither","reason":"Fixture"}'})
        self.advance()
        self.assertEqual(self.state()['status'], 'complete')
        for path, raw in preserved.items():
            self.assertEqual(path.read_bytes(), raw)

    def execute(self, notes, *, scores=None, relations=None):
        self.automatic_fixture(notes=notes)
        result = self.automatic_run(env={'AUTO_SCORES': json.dumps(scores or {}),
                                         'AUTO_RELATIONS': json.dumps(relations or {})})
        self.assertEqual(json.loads(result.stdout)['status'], 'complete')
        return self.state()

    def note(self, identifier, entries):
        return dict(note_id=identifier, text='Complete post '+identifier,
                    subjects=[dict(number=n, subject=t, context='Original '+t)
                              for n, t in entries])

    def test_all_guaranteed_roots_are_processed_even_after_early_coverage(self):
        notes = [self.note('a', [('1','Low'), ('2','High'), ('3','Also high')]),
                 self.note('b', [('1','Other'), ('2','Small')])]
        state = self.execute(notes, scores={'Low':49, 'High':80, 'Also high':50,
                                           'Other':70, 'Small':20})
        self.assertEqual([s['local'] for s in state['steps']], [
            dict(note_id='a', number='2'), dict(note_id='b', number='1'),
            dict(note_id='a', number='3')])
        self.assertEqual(len([r for r in state['inventory'] if 'prominence' in r]), 5)
        self.assertFalse(state['searches'])
        self.assertEqual(state['steps'][0]['selected_meaning'], 'High')

    def test_fallback_selects_only_highest_root_with_saved_order_for_ties(self):
        state = self.execute([self.note('a', [('1','Low'), ('2','Highest'), ('3','Tied')])],
                             scores={'Low':10, 'Highest':40, 'Tied':40})
        self.assertEqual([s['local']['number'] for s in state['steps']], ['2'])

    def test_held_guaranteed_root_uses_remaining_l1_only_until_note_is_covered(self):
        notes = [self.note('a', [('1','First')]),
                 self.note('b', [('1','Held'), ('2','Fallback'), ('3','Unused')])]
        state = self.execute(notes, scores={'Held':90,'Fallback':40,'Unused':30},
                             relations={'Held|First':'uncertain'})
        self.assertEqual([(s['local']['note_id'],s['local']['number'],s['status'])
                          for s in state['steps']],
                         [('a','1','added'),('b','1','held'),('b','2','added')])
        self.assertEqual(state['steps'][-1]['selection_phase'], 'coverage_l1')

    def test_matching_child_of_single_note_parent_gets_an_opportunity(self):
        notes = [self.note('a', [('1','Bread')]),
                 self.note('b', [('1','Food'), ('1.1','Bread'), ('1.2','Spices')])]
        state = self.execute(notes, relations={'Food|Bread':'local_contains_canonical', 'Bread|Bread':'equivalent',
                                               'Bread|Food':'canonical_contains_local'})
        self.assertEqual([s['local'] for s in state['steps']], [
            dict(note_id='a',number='1'),dict(note_id='b',number='1'),
            dict(note_id='b',number='1.1')])
        self.assertEqual(state['steps'][-1]['selection_phase'], 'heading_matches')
        self.assertEqual(state['steps'][-1]['status'], 'equivalent')
        self.assertFalse(any(r['subject']=='Spices' and 'producer' in r for r in state['inventory']))

    def test_leaf_selection_uses_supporting_branch_not_its_l1_siblings(self):
        notes = [self.note('a', [('1','Bread'), ('1.1','Sourdough')]),
                 self.note('b', [('1','Food'), ('1.1','Bread'),
                                 ('1.1.1','Sourdough'), ('1.2','Rosemary')])]
        state = self.execute(notes, relations={'Food|Bread':'local_contains_canonical', 'Bread|Bread':'equivalent',
            'Bread|Food':'canonical_contains_local', 'Sourdough|Food':'canonical_contains_local',
            'Sourdough|Bread':'canonical_contains_local','Sourdough|Sourdough':'equivalent'})
        selected = [s['local'] for s in state['steps']]
        self.assertIn(dict(note_id='b',number='1.1.1'), selected)
        self.assertNotIn(dict(note_id='b',number='1.2'), selected)
        self.assertTrue(state['stopping']['multi_note_leaves'])
        self.assertEqual(state['status'], 'complete')

    def test_invalid_score_is_not_zero_or_permission_to_pick_a_fallback(self):
        self.automatic_fixture(count=1, roots_only=True)
        self.runner.write_text(self.runner.read_text().replace('prominence=score', 'prominence=101'))
        result = self.automatic_run(ok=False)
        self.assertEqual(json.loads(result.stdout)['unresolved_scoring'], ['n0'])
        self.assertFalse(self.state()['nodes'])
        self.assertEqual(self.state()['guaranteed'], [])

    def test_saved_assessment_cannot_redefine_the_fixed_meaning(self):
        state = self.execute([self.note('a', [('1','Food')])])
        state['inventory'][0]['meaning'] = 'Changed meaning'
        self.write('trial/state.json', state)
        self.assertIn('meaning differs', self.cli('advance-canonical-traversal', 'trial',
                                                '--comment','Tampered',ok=False).stderr)

    drive = traversal_fixture.CanonicalTraversalTests.drive

    def test_equal_note_set_does_not_reject_a_valid_native_consolidation(self):
        notes = [self.note('a', [('1','Vegetables')]),
                 self.note('b', [('1','Vegetables'), ('2','Fruits')]),
                 *[self.note(n, [('1','Other '+n)]) for n in 'cdef']]
        self.prepare(notes=notes)
        def answer(role, local, identifier, payload, state):
            if role == 'meaning':
                return dict(meaning=next(r['subject'] for r in state['inventory'] if r['local'] == local))
            if role == 'consolidation':
                return dict(title='Food', meaning='Fixed Food', children=[
                    n['id'] for n in payload['siblings'] if n['title'] in ('Vegetables','Fruits')])
            a, b = payload['local']['subject'], payload['canonical']['subject']
            relation = ('equivalent' if a == b else 'local_contains_canonical'
                        if a == 'Food' and b in ('Vegetables','Fruits') else 'neither')
            return dict(meaning=payload['local']['meaning'], relation=relation, reason='Fixture')
        state = self.drive(answer)
        self.assertEqual([c['outcome'] for c in state['consolidations']], ['placed'])
        food = next(n for n in state['nodes'] if n['subject']=='Food')
        self.assertEqual(food['entries'], [])
        menu_food = next(n for n in state['menu']['nodes'] if n['subject']=='Food')
        self.assertEqual(menu_food['entries'], [])
        self.assertEqual(menu_food['note_ids'], ['a'])
        self.assertTrue(state['stopping']['strict_edges'])
        audit = json.loads(self.cli('audit-canonical-trial','trial','--output','audit.json').stdout)
        self.assertTrue(audit['structural_constraints_met'])
        view = json.loads(self.cli('export-canonical-viewer','trial','--output','viewer').stdout)
        self.assertEqual(view['note_count'], 6)
        exported = json.loads((self.root/'viewer/hierarchy.json').read_text())
        exported_food = next(n for n in exported['nodes'] if n['node_id']==food['id'])
        self.assertEqual(exported_food['note_ids'], ['N001'])
        self.assertIn('Direct supporting notes: \n', exported_food['analysis'])

    def test_symmetric_native_contract_keeps_both_directions_and_fixed_meanings(self):
        self.prepare(count=3, symmetric=True)
        def answer(role, local, identifier, payload, state):
            if role == 'meaning':
                return dict(meaning='Meaning '+local['note_id'])
            relation = 'B_contains_A' if local['note_id']=='n1' else 'A_contains_B'
            return dict(relation=relation, reason='Fixture',
                questions=[dict(id=d, question='Boundary?') for d in ('A_contains_B','B_contains_A')],
                answers=[dict(question_id=d, answer='Coverage', justification='Fixture')
                         for d in ('A_contains_B','B_contains_A')])
        state = self.drive(answer)
        self.assertEqual([s['status'] for s in state['steps']], ['added','added','added'])
        self.assertEqual(state['nodes'][1]['parents'], ['C001'])
        self.assertEqual(state['nodes'][0]['parents'], ['C003'])
        self.assertNotIn('meaning', state['steps'][1]['answers'][0]['output'])

    def test_each_native_producer_review_affects_only_its_own_note(self):
        self.prepare(count=2)
        experiment = self.state()['experiments'][0]['experiment']
        self.cli('run', experiment, env={'FAKE_RUNNER_PROMPT_RESPONSE':'{"meaning":"Fixed"}'})
        self.cli('review',experiment,'--case','L00000','--role','user','--verdict','reject',
                 '--comment','Missing original role')
        self.advance()
        self.assertIn('user producer review reject', self.state()['inventory'][0]['hold'])
        self.assertNotIn('hold', self.state()['inventory'][1])

    def test_prominence_review_can_hold_a_selected_search_before_placement(self):
        self.prepare(count=2)
        meaning = self.state()['experiments'][0]['experiment']
        self.cli('run',meaning,env={'FAKE_RUNNER_PROMPT_RESPONSE':'{"meaning":"Fixed"}'})
        self.advance()
        prominence = next(r['experiment'] for r in self.state()['experiments'] if r['role']=='prominence')
        self.cli('run',prominence,env={'FAKE_RUNNER_PROMPT_RESPONSE':json.dumps(dict(
            prominence=60,missing_meaning='Other',allocation=[dict(
                meaning='Complete post',points=100,represented=60,missing=40)]))})
        self.advance()
        comparison = next(r['experiment'] for r in self.state()['experiments'] if r['role']=='comparison')
        self.cli('review',prominence,'--case','L00001','--role','user','--verdict','reject',
                 '--comment','Incorrect prominence')
        self.cli('run',comparison,env={'FAKE_RUNNER_PROMPT_RESPONSE':json.dumps(dict(
            meaning='Fixed',relation='neither',reason='Fixture'))})
        self.advance()
        self.assertEqual(self.state()['steps'][-1]['status'],'held')
        self.assertIn('Incorrect prominence', self.state()['steps'][-1]['reason'])

    # Reuse the native CLI fixture, not the previous policy's test cases.
    def test_preparation_establishes_every_l1_before_selecting(self):
        self.prepare(count=2, extra_root=True)
        state = self.state()
        self.assertEqual(state['traversal_policy'], 'hierarchy-generation-v2')
        self.assertEqual(state['searches'], [])
        meaning = next(r for r in state['experiments'] if r['role'] == 'meaning')
        selected = [json.loads(i['INPUT_JSON'])['local']['hierarchy']['selected']
                    for i in meaning['inputs'].values()]
        self.assertEqual(selected, ['1', '1', '2'])
        self.assertEqual(len(meaning['inputs']), 3)



class SelectionRulesTests(unittest.TestCase):
    def test_a_new_heading_match_can_fill_a_free_search_slot(self):
        from sse_multivector.canonical_traversal import _next_locals
        rows = [dict(local=dict(note_id=n, number=k), subject=t, meaning=t, prominence=70)
                for n,k,t in [('a','1','Root A'), ('b','1','Root B'), ('c','1','Bread'),
                              ('a','1.1','Bread'), ('b','1.1','Other')]]
        state = dict(note_ids=['a','b','c'], inventory=rows,
            searches=[dict(local=rows[4]['local'],ordinal=4)],
            steps=[dict(local=rows[i]['local'],ordinal=i) for i in range(3)],
            nodes=[dict(id='C'+str(i),subject=rows[i]['subject'],meaning=rows[i]['meaning'],
                        parents=[],entries=[rows[i]['local']]) for i in range(3)])
        self.assertEqual([i for i,_ in _next_locals(state)], [3])
        self.assertEqual(state['selection_phase'], 'heading_matches')

    def test_overlapping_supporting_branches_select_a_local_entry_only_once(self):
        from sse_multivector.canonical_traversal import _next_locals
        rows = [dict(local=dict(note_id=n, number=k), subject=t, meaning=t, prominence=score)
                for n,k,t,score in [('a','1','Shared',80), ('b','1','Shared',80),
                    ('a','1.1','Shared',80), ('a','1.1.1','Detail',90),
                    ('a','1.2','Other',30)]]
        state = dict(note_ids=['a','b'], inventory=rows, searches=[],
                     steps=[dict(local=rows[i]['local'], ordinal=i) for i in range(3)],
                     nodes=[dict(id='C1',subject='Shared',meaning='Shared',parents=[],
                                 entries=[rows[i]['local'] for i in range(3)])])
        choices = list(_next_locals(state))
        self.assertEqual([i for i,_ in choices], [3,4])
        self.assertEqual(state['selection_phase'], 'multi_note_leaf')


class FinishedHierarchyTests(unittest.TestCase):
    def node(self, identifier, parents, notes):
        return dict(id=identifier, subject=identifier, meaning='Fixed '+identifier,
                    parents=parents, entries=[dict(note_id=n, number='1') for n in notes])

    def test_consolidated_parent_survives_and_equal_child_is_bypassed_on_its_branch(self):
        nodes = [self.node('Food', [], []), self.node('Other', [], ['C']),
                 self.node('Vegetables', ['Food', 'Other'], ['A', 'B']),
                 self.node('Potatoes', ['Vegetables'], ['A']),
                 self.node('Broccoli', ['Vegetables'], ['B']),
                 self.node('Fruits', ['Food'], ['B'])]
        before = deepcopy(nodes)
        menu = {n['id']: n for n in finish_nodes(nodes)}
        self.assertIn('Food', menu)
        self.assertEqual(menu['Vegetables']['parents'], ['Other'])
        self.assertEqual(menu['Potatoes']['parents'], ['Food', 'Vegetables'])
        self.assertEqual(menu['Broccoli']['parents'], ['Food', 'Vegetables'])
        self.assertEqual(menu['Fruits']['parents'], ['Food'])
        represented, children = _note_sets(list(menu.values()))
        self.assertTrue(all(represented[c] < represented[p]
                            for p, kids in children.items() for c in kids))
        self.assertEqual(nodes, before)
        for n in menu.values():
            self.assertEqual(n['entries'], next(o['entries'] for o in nodes if o['id'] == n['id']))

    def test_bypassed_leaf_notes_remain_accessible_without_fabricated_support(self):
        nodes = [self.node('Food', [], []),
                 self.node('Vegetables', ['Food'], ['A', 'B']),
                 self.node('Fruits', ['Food'], ['B'])]
        menu = {n['id']: n for n in finish_nodes(nodes)}
        self.assertEqual(set(menu), {'Food', 'Fruits'})
        self.assertEqual(menu['Food']['entries'], [])
        self.assertEqual(menu['Food']['note_ids'], ['A'])
        self.assertEqual(_note_sets(list(menu.values()))[0]['Food'], {'A', 'B'})

    def test_single_child_parent_is_still_omitted_in_favor_of_specific_child(self):
        nodes = [self.node('Food', [], []), self.node('Vegetables', ['Food'], ['A', 'B'])]
        self.assertEqual(finish_nodes(nodes), [{**nodes[1], 'parents': []}])


if __name__ == '__main__':
    unittest.main()
