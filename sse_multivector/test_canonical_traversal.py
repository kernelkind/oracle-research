"""Exercise the approved construction policy through native CLI and receipts."""
import json
import os
from pathlib import Path
import subprocess
import time
import signal
import shutil
import unittest

from sse_multivector import test_experiment as fixtures


class CanonicalTraversalTests(unittest.TestCase):
    setUp = fixtures.ExperimentTests.setUp
    write = fixtures.ExperimentTests.write
    def cli(self, *args, ok=True, env=None):
        project = getattr(self, 'project', Path(__file__).resolve().parents[1])
        launcher = Path(__file__).resolve().parents[2]/'experiment-runner/bin/experiment-runner'
        result = subprocess.run([str(launcher), '--project-root', str(project), *map(str,args)],
            cwd=self.root, env={**os.environ, 'FAKE_RUNNER_LOG':str(self.log), **(env or {})},
            text=True, capture_output=True,
            timeout=120 if args and args[0] == 'run-canonical-traversal' else 30)
        self.assertEqual(result.returncode == 0, ok, result.stderr+result.stdout)
        return result

    def test_shared_launcher_has_one_constructor_without_retired_alternatives(self):
        help_text = self.cli('--help').stdout
        self.assertIn('prepare-canonical-traversal', help_text)
        self.assertIn('advance-canonical-traversal', help_text)
        self.assertIn('run-canonical-traversal', help_text)
        for retired in ('prepare-canonical-trial', 'fork-canonical-trial',
                        'prepare-canonical-child-trial', 'advance-canonical-trial',
                        'continue-canonical-trial', 'prepare-canonical-selection-trial'):
            with self.subTest(command=retired):
                self.assertNotIn(retired, help_text)

    def prepare(self, count=4, extra_root=False, notes=None, symmetric=False):
        self.prompt.write_text('GENERIC PROMPT {INPUT_JSON}')
        subjects = lambda i: [dict(number='1', subject=f'Root {i}', context='Original role'),
                              dict(number='1.1', subject=f'Child {i}', context='Narrower role')]
        if notes is None:
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
            if name == 'comparison' and symmetric:
                schema = json.loads(Path(__file__).with_name('shr_single_pair').joinpath(
                    'Hierarchy-compare-v179.output.schema.json').read_text())
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

    def automatic_fixture(self, count=2, roots_only=False):
        original = '''    output_text = os.environ.get(
        "FAKE_RUNNER_PROMPT_RESPONSE", f"Response to: {prompt}"
    )'''
        replacement = '''    payload = json.loads(prompt.removeprefix("GENERIC PROMPT "))
    if "siblings" in payload:
        value = None
    elif "canonical" in payload:
        value = dict(meaning=payload["local"]["meaning"],
                     relation=os.environ.get("AUTO_RELATION", "neither"), reason="Fixture")
    else:
        branch = payload["local"]["hierarchy"]
        value = dict(meaning=next(e["subject"] for e in branch["entries"]
                                  if e["number"] == branch["selected"]))
    output_text = json.dumps(value)'''
        self.assertIn(original, fixtures.FAKE_RUNNER)
        self.runner.write_text(fixtures.FAKE_RUNNER.replace(original, replacement))
        self.write('allowance.json', dict(schema_version=1, limit=100, used=0))
        notes = [dict(note_id=f'n{i}', text=f'Original post {i}', subjects=[
            dict(number='1', subject=f'Root {i}', context='Original role')])
            for i in range(count)] if roots_only else None
        return self.prepare(count=count, notes=notes)

    def automatic_run(self, *, ok=True, env=None):
        return self.cli('run-canonical-traversal', 'trial', '--attempt-budget',
                        'allowance.json', ok=ok, env=env)

    def test_symmetric_compare_maps_both_directions_and_preserves_native_answers(self):
        self.prepare(count=3)
        spec = json.loads((self.root/'comparison.json').read_text())
        spec['runner']['output_schema'] = json.loads(Path(__file__).with_name(
            'shr_single_pair').joinpath('Hierarchy-compare-v179.output.schema.json').read_text())
        self.write('comparison.json', spec)
        self.cli('prepare-canonical-traversal', 'symmetric-trial', '--spec', 'traversal.json')
        self.trial = 'symmetric-trial'
        for _ in range(12):
            state = json.loads((self.root/self.trial/'state.json').read_text())
            if len(state['steps']) >= 3:
                break
            for record in state['experiments']:
                if 'answers' in record:
                    continue
                if record['role'] == 'meaning':
                    answer = {'meaning': 'Meaning '+record['local']['note_id']}
                else:
                    payload = json.loads(next(iter(record['inputs'].values()))['INPUT_JSON'])
                    self.assertEqual(set(payload), {'A', 'B'})
                    self.assertEqual(set(payload['B']), {'subject', 'meaning'})
                    direction = ('B_contains_A' if record['local']['note_id'] == 'n1'
                                 else 'A_contains_B')
                    answer = dict(relation=direction, reason='Fixture coverage',
                        questions=[dict(id=d, question='Boundary?') for d in
                                   ('A_contains_B', 'B_contains_A')],
                        answers=[dict(question_id=d, answer='Coverage or counterexample',
                                      justification='Fixture condition') for d in
                                 ('A_contains_B', 'B_contains_A')])
                self.cli('run', record['experiment'], env={
                    'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(answer)})
            self.cli('advance-canonical-traversal', self.trial, '--comment', 'Symmetric trial')
        state = json.loads((self.root/self.trial/'state.json').read_text())
        self.assertEqual([s['status'] for s in state['steps']], ['added', 'added', 'added'])
        self.assertEqual(state['nodes'][1]['parents'], ['C001'])
        self.assertEqual(state['nodes'][0]['parents'], ['C003'])
        raw = state['steps'][1]['answers'][0]['output']
        self.assertEqual(raw['relation'], 'B_contains_A')
        self.assertNotIn('meaning', raw)

    def test_automatic_run_finishes_multiple_frontiers_and_consolidation(self):
        self.automatic_fixture(count=7)
        result = json.loads(self.automatic_run().stdout)
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(result['execution_status'], 'complete')
        state = self.state()
        self.assertEqual(len(state['nodes']), 7)
        self.assertEqual([c['outcome'] for c in state['consolidations']], ['null', 'null'])
        calls = fixtures.ExperimentTests.calls(self)
        self.assertGreater(len(calls), 7)
        used = json.loads((self.root/'allowance.json').read_text())['used']
        claims = (self.root/'allowance.json.claims.jsonl').read_text().splitlines()
        self.assertEqual(used, len(claims))
        # Stop can cancel a reserved launch; native admission never refunds it.
        self.assertGreaterEqual(used, len(calls))
        frozen = (self.root/'trial/state.json').read_bytes()
        self.automatic_run()
        self.assertEqual(fixtures.ExperimentTests.calls(self), calls)
        self.assertEqual((self.root/'trial/state.json').read_bytes(), frozen)

    def test_automatic_budget_stop_resumes_without_repeating_successful_calls(self):
        self.automatic_fixture()
        self.write('allowance.json', dict(schema_version=1, limit=1, used=0))
        result = json.loads(self.automatic_run(ok=False).stdout)
        self.assertEqual(result['status'], 'constructing')
        self.assertEqual(result['execution_status'], 'attempt_budget_exhausted')
        calls = fixtures.ExperimentTests.calls(self)
        self.assertLessEqual(len(calls), 1)
        self.assertEqual(json.loads((self.root/'allowance.json').read_text())['used'], 1)
        # An explicitly enlarged allowance keeps the same irreversible counter.
        self.write('allowance.json', dict(schema_version=1, limit=100, used=1))
        self.assertEqual(json.loads(self.automatic_run().stdout)['status'], 'complete')
        repeated = [call['prompt'] for call in fixtures.ExperimentTests.calls(self)]
        self.assertEqual(len(repeated), len(set(repeated)))

    def test_automatic_terminal_failure_is_held_and_other_notes_continue(self):
        self.automatic_fixture()
        failure = {'AUTO_RELATION': 'equivalent', 'FAKE_RUNNER_FAILURES': json.dumps({
            'Root 0': {'metadata': {'abort_reason': {'name': 'TimeoutError'}}}})}
        result = json.loads(self.automatic_run(ok=False, env=failure).stdout)
        self.assertEqual(result['execution_status'], 'exhausted')
        self.assertGreater(result['held'], 0)
        state = self.state()
        self.assertEqual(state['steps'][0]['status'], 'held')
        self.assertTrue(any(step['status'] == 'added' for step in state['steps']))
        calls = fixtures.ExperimentTests.calls(self)
        failed_prompts = [c['prompt'] for c in calls if 'Root 0' in c['prompt']]
        self.assertEqual(len(failed_prompts), len(set(failed_prompts)))
        self.assertEqual(json.loads((self.root/'allowance.json').read_text())['used'], len(calls))

    def test_automatic_search_advances_before_other_meaning_batches_finish(self):
        self.automatic_fixture(count=3)
        marker = self.root/'comparison-started'
        result = self.automatic_run(env={'FAKE_RUNNER_SEQUENCE': json.dumps({
            '"subject": "Root 2"': {'wait_for': str(marker)},
            '"canonical"': {'touch': str(marker)},
        })})
        self.assertEqual(json.loads(result.stdout)['status'], 'complete')
        self.assertTrue(marker.exists())
        self.assertEqual(json.loads(result.stdout)['held'], 0)

    def test_native_provider_retry_is_not_collected_as_terminal_failure(self):
        self.automatic_fixture(count=3)
        result = self.automatic_run(env={'FAKE_RUNNER_FAILURES': json.dumps({
            'Root 1': {'attempts': 1, 'metadata': {'http_status': 503}}
        })})
        self.assertEqual(json.loads(result.stdout)['held'], 0)
        first = next(record for record in self.state()['experiments']
                     if record['role'] == 'meaning' and record['local']['note_id'] == 'n1')
        records = [json.loads(line) for line in
                   (Path(first['experiment'])/'run/results.jsonl').read_text().splitlines()]
        self.assertEqual([r['status'] for r in records], ['failed', 'succeeded'])
        self.assertEqual(first['answers'][0]['status'], 'valid')

    def test_automatic_run_rejects_missing_or_changed_allowance_before_dispatch(self):
        self.automatic_fixture()
        missing = self.cli('run-canonical-traversal', 'trial', '--attempt-budget',
                           'missing.json', ok=False)
        self.assertIn('attempt budget', missing.stderr)
        self.assertEqual(fixtures.ExperimentTests.calls(self), [])
        self.automatic_run()
        calls = fixtures.ExperimentTests.calls(self)
        self.write('other-allowance.json', dict(schema_version=1, limit=100, used=0))
        changed = self.cli('run-canonical-traversal', 'trial', '--attempt-budget',
                           'other-allowance.json', ok=False)
        self.assertIn('prepared step differs from saved state', changed.stderr)
        self.assertEqual(fixtures.ExperimentTests.calls(self), calls)

    def test_native_retry_without_remaining_allowance_is_resumable(self):
        self.automatic_fixture(count=1, roots_only=True)
        self.write('allowance.json', dict(schema_version=1, limit=1, used=0))
        result = self.automatic_run(ok=False, env={'FAKE_RUNNER_FAILURES': json.dumps({
            'Root 0': {'attempts': 1, 'metadata': {'http_status': 503}}
        })})
        summary = json.loads(result.stdout)
        self.assertEqual(summary['execution_status'], 'attempt_budget_exhausted')
        self.assertEqual(summary['held'], 0)
        self.assertEqual(len(fixtures.ExperimentTests.calls(self)), 1)
        self.assertNotIn('answers', self.state()['experiments'][0])
        self.write('allowance.json', dict(schema_version=1, limit=2, used=1))
        self.assertEqual(json.loads(self.automatic_run().stdout)['status'], 'complete')
        self.assertEqual(len(fixtures.ExperimentTests.calls(self)), 2)
        records = [json.loads(line) for line in (self.root/
                   'trial/batch-00000/experiment/run/results.jsonl').read_text().splitlines()]
        self.assertEqual([r['status'] for r in records], ['failed', 'succeeded'])

    def test_second_driver_is_rejected_without_dispatch(self):
        import fcntl
        self.automatic_fixture()
        with (self.root/'trial/.traversal-run.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            result = self.automatic_run(ok=False)
        self.assertIn('traversal execution is already active', result.stderr)
        self.assertEqual(fixtures.ExperimentTests.calls(self), [])

    def test_killed_driver_resumes_saved_graph_and_completed_receipts(self):
        self.automatic_fixture(count=2, roots_only=True)
        marker = self.root/'comparison-waiting'
        project = Path(__file__).resolve().parents[1]
        launcher = project.parent/'experiment-runner/bin/experiment-runner'
        with (self.root/'driver.log').open('w') as log:
            process = subprocess.Popen([str(launcher), '--project-root', str(project),
                'run-canonical-traversal', 'trial', '--attempt-budget', 'allowance.json'],
                cwd=self.root, stdout=log, stderr=log, start_new_session=True,
                env={**os.environ, 'FAKE_RUNNER_LOG': str(self.log),
                    'FAKE_RUNNER_SEQUENCE': json.dumps({'"canonical"': {
                        'touch': str(marker), 'wait_for': str(self.root/'never-created')}})})
            try:
                deadline = time.monotonic()+20
                while not marker.exists() and process.poll() is None and time.monotonic() < deadline:
                    time.sleep(.02)
                self.assertTrue(marker.exists(), (self.root/'driver.log').read_text())
                saved = self.state()
                self.assertEqual(len(saved['nodes']), 1)
                receipts = {Path(r['experiment'])/'run/results.jsonl':
                    (Path(r['experiment'])/'run/results.jsonl').read_bytes()
                    for r in saved['experiments'] if 'answers' in r}
                used = json.loads((self.root/'allowance.json').read_text())['used']
            finally:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=10)
        self.assertEqual(json.loads(self.automatic_run().stdout)['status'], 'complete')
        self.assertEqual(self.state()['nodes'][0], saved['nodes'][0])
        for path, raw in receipts.items():
            self.assertEqual(path.read_bytes(), raw)
        self.assertGreaterEqual(json.loads((self.root/'allowance.json').read_text())['used'], used)
        meanings = [c['prompt'] for c in fixtures.ExperimentTests.calls(self)
                    if '"canonical"' not in c['prompt']]
        self.assertEqual(len(meanings), len(set(meanings)))

    def test_reviewed_code_fix_resumes_without_changing_graph_inputs_or_receipts(self):
        # Isolate code to exercise a real source transition without editing a
        # checkout bound to another test's experiments.
        project = Path(__file__).resolve().parents[1]
        self.project = self.root/'project'
        (self.project/'sse_multivector').mkdir(parents=True)
        shutil.copy2(project/'experiment-runner.json', self.project)
        for path in (project/'sse_multivector').glob('*.py'):
            shutil.copy2(path, self.project/'sse_multivector')
        self.automatic_fixture(count=2, roots_only=True)
        self.write('allowance.json', dict(schema_version=1, limit=2, used=0))
        self.automatic_run(ok=False)
        saved = self.state()
        calls = fixtures.ExperimentTests.calls(self)
        code = self.project/'sse_multivector/canonical_traversal.py'
        code.write_text(code.read_text()+'\n# Reviewed continuation fix.\n')
        refused = self.automatic_run(ok=False)
        self.assertIn('trial source changed', refused.stderr)
        self.assertEqual(fixtures.ExperimentTests.calls(self), calls)
        self.write('allowance.json', dict(schema_version=1, limit=20, used=2))
        result = self.cli('run-canonical-traversal', 'trial', '--attempt-budget', 'allowance.json',
                          '--runner-upgrade-reason', 'Reviewed continuation fix; inputs unchanged')
        self.assertEqual(json.loads(result.stdout)['status'], 'complete')
        state = self.state()
        self.assertEqual(state['nodes'][:len(saved['nodes'])], saved['nodes'])
        for before, after in zip(saved['experiments'], state['experiments']):
            if 'answers' in before:
                self.assertEqual(after, before)
        self.assertEqual(state['source_upgrades'][0]['reason'],
                         'Reviewed continuation fix; inputs unchanged')
        for field in ('corpus', 'note_ids', 'bootstrap_spec', 'comparison_spec', 'consolidation_spec'):
            self.assertEqual(state[field], saved[field])
        # An execution upgrade must never authorize changing frozen post evidence.
        corpus = self.root/'notes.json'
        corpus.write_text(corpus.read_text()+'\n')
        self.cli('run-canonical-traversal', 'trial', '--attempt-budget', 'allowance.json',
                 '--runner-upgrade-reason', 'Cannot authorize different inputs', ok=False)

    def test_reviewed_upgrade_pins_new_shaping_code_for_a_legacy_resume(self):
        self.automatic_fixture(count=2, roots_only=True)
        self.write('allowance.json', dict(schema_version=1, limit=2, used=0))
        self.automatic_run(ok=False)
        saved = self.state()
        shape = str(Path(__file__).with_name('canonical_hierarchy_shape.py').resolve())
        # Earlier constructor states did not bind this newly used component.
        state = json.loads(json.dumps(saved))
        state['sources'].pop(shape)
        state.pop('menu')
        for step in state['steps']:
            step.pop('ordinal', None)
            step.pop('selection_index', None)
        for slot in state['searches']:
            slot.pop('selection_index', None)
        self.write('trial/state.json', state)
        self.write('allowance.json', dict(schema_version=1, limit=20, used=2))
        self.cli('run-canonical-traversal', 'trial', '--attempt-budget', 'allowance.json',
                 '--runner-upgrade-reason', 'Adopt reviewed finished-menu implementation')
        resumed = self.state()
        self.assertIn(shape, resumed['sources'])
        self.assertIsNone(resumed['source_upgrades'][0]['before'][shape])
        self.assertEqual(resumed['source_upgrades'][0]['after'][shape], resumed['sources'][shape])
        self.assertEqual(resumed['nodes'][:len(saved['nodes'])], saved['nodes'])
        for before, after in zip(saved['experiments'], resumed['experiments']):
            if 'answers' in before:
                self.assertEqual(after, before)

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

    def test_singleton_routes_elsewhere_do_not_finish_a_shared_leaf(self):
        notes = [dict(note_id=f'n{i}', text=f'Original post {i}', subjects=[
            dict(number='1', subject='Shared', context='Shared topic'),
            dict(number='2', subject=f'Solo {i}', context='Independent topic')])
            for i in range(2)]
        self.prepare(notes=notes)
        for _ in range(12):
            state = self.state()
            if state['status'] in ('complete', 'exhausted'):
                break
            for record in state['experiments']:
                if 'answers' in record:
                    continue
                local = record['local']
                meaning = 'Shared' if local['number'] == '1' else 'Solo '+local['note_id']
                for identifier in record['inputs']:
                    value = dict(meaning=meaning)
                    if record['role'] == 'comparison':
                        value.update(relation='equivalent' if local['number'] == '1'
                                     else 'neither', reason='Fixture fixed meanings')
                    self.cli('run', record['experiment'], '--only', identifier, env={
                        'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(value)})
            self.advance()
        state = self.state()
        self.assertEqual(state['status'], 'exhausted')
        self.assertTrue(state['stopping']['individual_access'])
        self.assertTrue(state['stopping']['strict_edges'])
        self.assertFalse(state['stopping']['single_note_leaves'])
        self.assertEqual(state['stopping']['multi_note_leaves'], [
            dict(id='C001', note_ids=['n0', 'n1'])])
        report = json.loads(self.cli('audit-canonical-trial', 'trial',
                                     '--output', 'audit.json').stdout)
        self.assertFalse(report['structural_constraints_met'])
        audit = json.loads((self.root/'audit.json').read_text())
        self.assertIn(dict(kind='multi_note_leaf', node='C001', note_ids=['n0', 'n1']),
                      audit['violations'])

    def test_note_supported_by_a_parent_does_not_need_its_own_canonical_node(self):
        from sse_multivector.canonical_traversal import _stopping
        state = dict(note_ids=['n0', 'n1'], nodes=[
            dict(id='F', subject='Food', meaning='Food', parents=[], entries=[
                dict(note_id='n0', number='1'), dict(note_id='n1', number='1')]),
            dict(id='V', subject='Vegetables', meaning='Vegetables', parents=['F'], entries=[
                dict(note_id='n0', number='1.1')])])
        result = _stopping(state)
        self.assertTrue(result['individual_access'])
        self.assertTrue(result['strict_edges'])
        self.assertTrue(result['single_note_leaves'])

    def test_equal_note_steps_retain_the_deeper_heading_and_original_supports(self):
        from sse_multivector.canonical_traversal import _stopping
        nodes = [
            dict(id='R', subject='Topics', meaning='All topics', parents=[], entries=[
                dict(note_id='n2', number='1')]),
            dict(id='F', subject='Food', meaning='Food', parents=['R'], entries=[
                dict(note_id='n0', number='1'), dict(note_id='n1', number='1')]),
            dict(id='V', subject='Vegetables', meaning='Vegetables', parents=['F'], entries=[
                dict(note_id='n0', number='1.1'), dict(note_id='n1', number='1.1')])]
        original = json.loads(json.dumps(nodes))
        state = dict(note_ids=['n0', 'n1', 'n2'], nodes=nodes)
        result = _stopping(state)
        self.assertTrue(result['strict_edges'])
        self.assertFalse(result['single_note_leaves'])
        self.assertEqual(state['menu']['omitted_nodes'], ['F'])
        self.assertEqual(state['menu']['nodes'], [nodes[0], {**nodes[2], 'parents': ['R']}])
        self.assertEqual(state['nodes'], original)
        root_state = dict(note_ids=['n0', 'n1'], nodes=[
            {**nodes[1], 'parents': []}, nodes[2]])
        _stopping(root_state)
        self.assertEqual(root_state['menu']['nodes'], [{**nodes[2], 'parents': []}])
        # New evidence can make a formerly redundant broad heading useful again.
        state['nodes'].append(dict(id='X', subject='Other food', meaning='Other food',
            parents=['F'], entries=[dict(note_id='n2', number='2')]))
        _stopping(state)
        self.assertIn('F', [n['id'] for n in state['menu']['nodes']])

    def test_removing_equal_parent_preserves_other_branches_without_new_containments(self):
        from sse_multivector.canonical_traversal import _stopping
        nodes = [
            dict(id='R', subject='Topics', meaning='All topics', parents=[], entries=[
                dict(note_id='n3', number='1')]),
            dict(id='O', subject='Other parent', meaning='Other parent', parents=['R'], entries=[
                dict(note_id='n2', number='1')]),
            dict(id='F', subject='Food', meaning='Food', parents=['R'], entries=[
                dict(note_id='n0', number='1'), dict(note_id='n1', number='1')]),
            dict(id='V', subject='Vegetables', meaning='Vegetables', parents=['F', 'O'], entries=[
                dict(note_id='n0', number='1.1'), dict(note_id='n1', number='1.1')]),
            dict(id='S', subject='Side branch', meaning='Side branch', parents=['F'], entries=[
                dict(note_id='n0', number='2')])]
        state = dict(note_ids=['n0', 'n1', 'n2', 'n3'], nodes=nodes)
        _stopping(state)
        menu = {n['id']: n for n in state['menu']['nodes']}
        self.assertNotIn('F', menu)
        self.assertEqual(menu['V']['parents'], ['O', 'R'])
        self.assertEqual(menu['S']['parents'], ['R'])
        self.assertEqual(menu['S']['entries'], nodes[-1]['entries'])

    def test_after_coverage_selects_deeper_nodes_only_from_multi_note_leaves(self):
        self.prepare(count=4)
        for _ in range(18):
            state = self.state()
            if state['status'] in ('complete', 'exhausted'):
                break
            for record in state['experiments']:
                if 'answers' in record:
                    continue
                local = record['local']
                subject = next(r['subject'] for r in state['inventory'] if r['local'] == local)
                for identifier in record['inputs']:
                    value = dict(meaning=subject)
                    if record['role'] == 'comparison':
                        value.update(reason='Fixture consistent topics', relation=(
                            'equivalent' if local == dict(note_id='n1', number='1')
                            and identifier == 'C001' else 'canonical_contains_local'
                            if '.' in local['number'] and identifier == 'C001' else 'neither'))
                    self.cli('run', record['experiment'], '--only', identifier, env={
                        'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(value)})
            self.advance()
        state = self.state()
        selected = [r['local'] for r in state['experiments'] if r['role'] == 'meaning']
        self.assertNotIn(dict(note_id='n2', number='1.1'), selected)
        self.assertNotIn(dict(note_id='n3', number='1.1'), selected)
        self.assertEqual(state['status'], 'complete')
        self.assertTrue(state['stopping']['single_note_leaves'])
        audit = json.loads(self.cli('audit-canonical-trial', 'trial', '--output', 'audit.json').stdout)
        self.assertTrue(audit['structural_constraints_met'])
        tasks = json.loads((self.root/'audit.json').read_text())['individual_tasks']
        self.assertEqual(next(t for t in tasks if t['note_id'] == 'n1')['node'], 'C001')

    def test_skipped_locals_are_unused_and_filtered_selection_resumes(self):
        self.prepare(count=5)
        for _ in range(20):
            state = self.state()
            if state['status'] in ('complete', 'exhausted'):
                break
            for record in state['experiments']:
                if 'answers' in record:
                    continue
                local = record['local']
                subject = next(r['subject'] for r in state['inventory'] if r['local'] == local)
                for identifier in record['inputs']:
                    value = dict(meaning=subject)
                    if record['role'] == 'comparison':
                        parent = {'n0': 'C001', 'n1': 'C002', 'n3': 'C004', 'n4': 'C004'}
                        value.update(reason='Fixture consistent topics', relation=(
                            'equivalent' if local == dict(note_id='n4', number='1')
                            and identifier == 'C004' else 'canonical_contains_local'
                            if '.' in local['number'] and identifier == parent.get(local['note_id'])
                            else 'neither'))
                    self.cli('run', record['experiment'], '--only', identifier, env={
                        'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(value)})
            self.advance()
        state = self.state()
        self.assertEqual(state['status'], 'complete')
        self.assertNotIn(dict(note_id='n2', number='1.1'),
                         [r['local'] for r in state['experiments'] if r['role'] == 'meaning'])
        step = next(s for s in state['steps'] if s['local'] == dict(note_id='n3', number='1.1'))
        self.assertEqual((step['ordinal'], step['selection_index']), (8, 7))
        saved = (self.root/'trial/state.json').read_bytes()
        self.advance()
        self.assertEqual((self.root/'trial/state.json').read_bytes(), saved)

    def test_unused_entries_can_become_eligible_again_after_leaf_changes(self):
        from sse_multivector.canonical_traversal import _next_locals
        rows = [dict(local=dict(note_id=f'n{i}', number='1.1'), subject=f'Child {i}')
                for i in range(2)]
        state = dict(inventory=rows, steps=[], searches=[], stopping=dict(
            individual_access=True, multi_note_leaves=[dict(id='L', note_ids=['n1', 'other'])]))
        self.assertEqual(list(_next_locals(state)), [(1, rows[1])])
        state['searches'] = [rows[1]]
        state['stopping']['multi_note_leaves'] = [dict(id='L', note_ids=['n0', 'n1'])]
        self.assertEqual(list(_next_locals(state)), [(0, rows[0])])

    def test_saved_menu_cannot_change_a_canonical_meaning(self):
        self.prepare(count=1)
        self.run_pending(dict(meaning='Fixed meaning'))
        self.advance()
        state = self.state()
        self.assertEqual(state['status'], 'complete')
        state['menu']['nodes'][0]['meaning'] = 'Changed meaning'
        self.write('trial/state.json', state)
        rejected = self.cli('advance-canonical-traversal', 'trial', '--comment',
                            'Refuse an altered menu', ok=False)
        self.assertIn('saved browsing hierarchy differs', rejected.stderr)

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
        audit = json.loads(self.cli('audit-canonical-trial', 'trial', '--output', 'audit.json').stdout)
        self.assertTrue(audit['structural_constraints_met'])
        report = json.loads((self.root/'audit.json').read_text())
        self.assertEqual(report['choice_warnings'], [dict(kind='too_many_roots', count=7)])
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

    def test_failed_native_meaning_is_held_and_failure_receipt_cannot_be_tampered(self):
        self.prepare(count=2)
        experiment = self.state()['experiments'][0]['experiment']
        self.cli('run', experiment, env={'FAKE_RUNNER_FAIL_STAGE':'prompt'}, ok=False)
        record = Path(experiment)/'run/results.jsonl'
        saved = record.read_bytes()
        state_bytes = (self.root/'trial/state.json').read_bytes()
        rows = [json.loads(line) for line in saved.splitlines()]
        rows[0]['stderr'] = 'Changed failure bytes'
        record.write_text(''.join(json.dumps(row)+'\n' for row in rows))
        self.cli('advance-canonical-traversal', 'trial', '--comment', 'Reject changed receipt', ok=False)
        self.assertEqual((self.root/'trial/state.json').read_bytes(), state_bytes)
        record.write_bytes(saved)
        self.advance()
        step = self.state()['steps'][0]
        self.assertEqual(step['status'], 'held')
        self.assertEqual(step['before'], step['after'])

    def test_new_parent_cannot_change_a_settled_neither_relationship(self):
        self.settled_neither_fixture(symmetric=False)

    def test_symmetric_new_parent_cannot_change_a_settled_neither_relationship(self):
        self.settled_neither_fixture(symmetric=True)

    def settled_neither_fixture(self, *, symmetric):
        self.prepare(count=3, symmetric=symmetric)
        for _ in range(12):
            state = self.state()
            if len(state['steps']) >= 3:
                break
            for record in state['experiments']:
                if 'answers' in record:
                    continue
                note = record['local']['note_id']
                for identifier in record['inputs']:
                    value = dict(meaning='Meaning '+note)
                    if record['role'] == 'comparison':
                        value.update(reason='Controlled graph fixture', relation=(
                            'canonical_contains_local' if identifier == 'C001'
                            else 'local_contains_canonical') if note == 'n2' else 'neither')
                    if record['role'] == 'comparison' and symmetric:
                        relation = {'canonical_contains_local': 'B_contains_A',
                                    'local_contains_canonical': 'A_contains_B'}.get(
                                        value['relation'], value['relation'])
                        value = dict(relation=relation, reason=value['reason'],
                            questions=[dict(id=d, question='Boundary?') for d in
                                       ('A_contains_B', 'B_contains_A')],
                            answers=[dict(question_id=d, answer='Coverage or counterexample',
                                          justification='Fixture condition') for d in
                                     ('A_contains_B', 'B_contains_A')])
                    self.cli('run', record['experiment'], '--only', identifier, env={
                        'FAKE_RUNNER_PROMPT_RESPONSE':json.dumps(value)})
            self.advance()
        state = self.state()
        self.assertEqual(len(state['steps']), 3)
        step = state['steps'][2]
        self.assertEqual(step['status'], 'held')
        self.assertEqual(step['before'], step['after'])
        witness = step['settled_relation_contradiction']
        self.assertEqual((witness['source'], witness['other']), ('C002', 'C001'))
        self.assertEqual(witness['previous_relation'], 'neither')
        self.assertEqual(witness['current_relation'], 'canonical_contains_local')

    def test_finished_graph_remains_usable_by_saved_review_and_shaping_tools(self):
        self.prepare(count=3)
        state = self.finish()
        self.assertEqual(state['status'], 'complete')
        source_bytes = (self.root/'trial/state.json').read_bytes()
        shown = json.loads(self.cli('export-canonical-viewer', 'trial', '--output', 'view').stdout)
        self.assertEqual(shown['note_count'], 3)
        originals = json.loads((self.root/'view/notes.json').read_text())['notes']
        self.assertEqual([n['text'] for n in originals], [f'Original post {i}' for i in range(3)])
        self.write('shape.json', dict(schema_version=1, trial='trial',
            roots=[n['id'] for n in state['nodes']], children={}))
        self.cli('shape-canonical-trial', '--source', 'shape.json', '--output', 'shaped')
        shaped = json.loads((self.root/'shaped/state.json').read_text())
        self.assertEqual(shaped['nodes'], state['nodes'])
        self.assertEqual((self.root/'trial/state.json').read_bytes(), source_bytes)


def saved_traversal_fixture(test, *, equivalent=False):
    """Create reviewed graph evidence through the standalone native constructor."""
    notes = [dict(note_id='n1', text='First post', subjects=[
        dict(number='1', subject='Cooking', context='Using heat'),
        dict(number='1.1', subject='EXCLUDED CHILD', context='Child')]),
        dict(note_id='n2', text='Second post', subjects=[
            dict(number='2', subject='Food', context='Intended for cooking')]),
        dict(note_id='n3', text='Third post', subjects=[
            dict(number='3', subject='Ingredients', context='Cooking role')])]
    CanonicalTraversalTests.prepare(test, notes=notes)
    meanings = dict(n1='Fixed cooking meaning', n2='Fixed food meaning', n3='Independent meaning')
    for _ in range(12):
        state = CanonicalTraversalTests.state(test)
        if len(state['steps']) >= 3:
            return state
        for record in state['experiments']:
            if 'answers' in record:
                continue
            if record['role'] == 'meaning':
                value = dict(meaning=meanings[record['local']['note_id']])
            else:
                note = record['local']['note_id']
                value = dict(meaning=meanings[note], reason='Controlled graph fixture',
                    relation=('equivalent' if equivalent else 'canonical_contains_local')
                             if note == 'n2' else 'neither')
            test.cli('run', record['experiment'], env={
                'FAKE_RUNNER_PROMPT_RESPONSE':json.dumps(value)})
        CanonicalTraversalTests.advance(test)
    test.fail('native fixture did not process its three roots')


if __name__ == '__main__':
    unittest.main()
