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
    write = fixtures.ExperimentTests.write

    def setUp(self):
        fixtures.ExperimentTests.setUp(self)
        self.runner.write_text(self.runner.read_text().replace(
            'if prompt.startswith("GENERIC PROMPT"):',
            'if prompt.startswith("GENERIC PROMPT") or prompt.startswith("Prominence estimates"):'))

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


    def automatic_fixture(self, count=2, roots_only=False, notes=None):
        original = '''    output_text = os.environ.get(
        "FAKE_RUNNER_PROMPT_RESPONSE", f"Response to: {prompt}"
    )'''
        replacement = '''    payload = json.loads(prompt.removeprefix("GENERIC PROMPT ") if prompt.startswith("GENERIC PROMPT ")
                         else prompt.rstrip().rsplit("\\n", 1)[-1])
    if "node_description" in payload:
        score = json.loads(os.environ.get("AUTO_SCORES", "{}")).get(payload["node_title"], 60)
        value = dict(prominence=score, missing_meaning="Other meaning",
                     allocation=[dict(meaning="Complete post", points=100, represented=score, missing=100-score)])
    elif "siblings" in payload:
        value = None
    elif "canonical" in payload:
        value = dict(meaning=payload["local"]["meaning"],
                     relation=json.loads(os.environ.get("AUTO_RELATIONS", "{}")).get(
                         payload["local"]["subject"]+"|"+payload["canonical"]["subject"],
                         os.environ.get("AUTO_RELATION", "neither")), reason="Fixture")
    else:
        branch = payload["local"]["hierarchy"]
        value = dict(meaning=next(e["subject"] for e in branch["entries"]
                                  if e["number"] == branch["selected"]))
    output_text = json.dumps(value)'''
        self.assertIn(original, fixtures.FAKE_RUNNER)
        self.runner.write_text(fixtures.FAKE_RUNNER.replace(original, replacement).replace(
            'if prompt.startswith("GENERIC PROMPT"):',
            'if prompt.startswith("GENERIC PROMPT") or prompt.startswith("Prominence estimates"):'))
        self.write('allowance.json', dict(schema_version=1, limit=100, used=0))
        if notes is None and roots_only:
            notes = [dict(note_id=f'n{i}', text=f'Original post {i}', subjects=[
                dict(number='1', subject=f'Root {i}', context='Original role')])
                for i in range(count)]
        return self.prepare(count=count, notes=notes)


    def automatic_run(self, *, ok=True, env=None):
        return self.cli('run-canonical-traversal', 'trial', '--attempt-budget',
                        'allowance.json', ok=ok, env=env)


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
        self.assertIn('n0', result['unresolved_scoring'])
        state = self.state()
        self.assertFalse(any(s['local']['note_id'] == 'n0' for s in state['steps']))
        self.assertTrue(any(step['status'] == 'added' for step in state['steps']))
        calls = fixtures.ExperimentTests.calls(self)
        failed_prompts = [c['prompt'] for c in calls if 'Root 0' in c['prompt']]
        self.assertEqual(len(failed_prompts), len(set(failed_prompts)))
        self.assertEqual(json.loads((self.root/'allowance.json').read_text())['used'], len(calls))


    def test_native_provider_retry_is_not_collected_as_terminal_failure(self):
        self.automatic_fixture(count=3)
        result = self.automatic_run(env={'FAKE_RUNNER_FAILURES': json.dumps({
            'Root 1': {'attempts': 1, 'metadata': {'http_status': 503}}
        })})
        self.assertEqual(json.loads(result.stdout)['held'], 0)
        first = next(record for record in self.state()['experiments']
                     if record['role'] == 'meaning')
        records = [json.loads(line) for line in
                   (Path(first['experiment'])/'run/results.jsonl').read_text().splitlines()]
        retried = [r for r in records if r['note_id'] == 'L00001']
        self.assertEqual([r['status'] for r in retried], ['failed', 'succeeded'])
        self.assertTrue(all(a['status'] == 'valid' for a in first['answers']))


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
        self.write('allowance.json', dict(schema_version=1, limit=3, used=1))
        self.assertEqual(json.loads(self.automatic_run().stdout)['status'], 'complete')
        self.assertEqual(len(fixtures.ExperimentTests.calls(self)), 3)
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
        shutil.copytree(project/'sse_multivector/prominence-prompt-goal-v1/ppv35-post-meaning-v1',
                        self.project/'sse_multivector/prominence-prompt-goal-v1/ppv35-post-meaning-v1')
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
        self.assertEqual(self.state()['status'], 'exhausted')
        self.assertEqual(self.state()['unresolved_scoring'], ['n0','n1'])
        self.assertEqual(self.state()['nodes'], [])


    def test_new_parent_cannot_change_a_settled_neither_relationship(self):
        self.settled_neither_fixture(symmetric=False)


    def test_symmetric_new_parent_cannot_change_a_settled_neither_relationship(self):
        self.settled_neither_fixture(symmetric=True)


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


    def drive(self, answer):
        """Exercise every phase with native inputs, execution and immutable receipts."""
        for _ in range(80):
            state = CanonicalTraversalTests.state(self)
            if state['status'] in ('complete', 'exhausted'):
                return state
            for record in state['experiments']:
                if 'answers' in record:
                    continue
                shown = json.loads(CanonicalTraversalTests.cli(
                    self, 'show', record['experiment'], '--json').stdout)
                for case in shown['cases']:
                    if case['status'] != 'unrun':
                        continue
                    local = (state['inventory'][int(case['id'][1:])]['local']
                             if record['role'] in ('meaning', 'prominence') else record['local'])
                    payload = json.loads(case['inputs']['INPUT_JSON'])
                    value = (dict(prominence=60, missing_meaning='Other meaning', allocation=[
                        dict(meaning='Whole post', points=100, represented=60, missing=40)])
                        if record['role'] == 'prominence' else
                        answer(record['role'], local, case['id'], payload, state))
                    CanonicalTraversalTests.cli(self, 'run', record['experiment'], '--only', case['id'],
                        env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(value)})
            CanonicalTraversalTests.advance(self)
        self.fail('native fixture construction did not finish')

    def finish(self, proposal=None):
        def answer(role, local, identifier, payload, state):
            if role == 'meaning':
                return dict(meaning='Meaning '+local['note_id'])
            if role == 'consolidation':
                return proposal if proposal and len(state['nodes']) == 7 else None
            relation = ('local_contains_canonical' if payload['local']['subject'] == 'Group'
                        and identifier in ('C001', 'C002') else 'neither')
            return dict(meaning=payload['local']['meaning'], relation=relation, reason='Fixture')
        return self.drive(answer)

    def settled_neither_fixture(self, *, symmetric):
        self.prepare(count=3, symmetric=symmetric)
        def answer(role, local, identifier, payload, state):
            note = local['note_id']
            if role == 'meaning':
                return dict(meaning='Meaning '+note)
            relation = (('canonical_contains_local' if identifier == 'C001' else
                         'local_contains_canonical') if note == 'n2' else 'neither')
            if not symmetric:
                return dict(meaning='Meaning '+note, relation=relation, reason='Graph fixture')
            relation = {'canonical_contains_local':'B_contains_A',
                        'local_contains_canonical':'A_contains_B'}.get(relation, relation)
            return dict(relation=relation, reason='Graph fixture',
                questions=[dict(id=d, question='Boundary?') for d in ('A_contains_B','B_contains_A')],
                answers=[dict(question_id=d, answer='Coverage or counterexample', justification='Fixture')
                         for d in ('A_contains_B','B_contains_A')])
        state = self.drive(answer)
        self.assertEqual(len(state['steps']), 3)
        step = state['steps'][2]
        self.assertEqual(step['status'], 'held')
        self.assertEqual(step['before'], step['after'])
        witness = step['settled_relation_contradiction']
        self.assertEqual((witness['source'], witness['other']), ('C002','C001'))
        self.assertEqual(witness['previous_relation'], 'neither')
        self.assertEqual(witness['current_relation'], 'canonical_contains_local')


def saved_traversal_fixture(test, *, equivalent=False):
    """Create reviewed graph evidence through the standalone V2 constructor."""
    notes = [dict(note_id='n1', text='First post', subjects=[
        dict(number='1', subject='Cooking', context='Using heat'),
        dict(number='1.1', subject='EXCLUDED CHILD', context='Child')]),
        dict(note_id='n2', text='Second post', subjects=[
            dict(number='2', subject='Food', context='Intended for cooking')]),
        dict(note_id='n3', text='Third post', subjects=[
            dict(number='3', subject='Ingredients', context='Cooking role')])]
    # Existing adapter tests use the ordinary fake transport; teach it the PP template.
    test.runner.write_text(test.runner.read_text().replace(
        'if prompt.startswith("GENERIC PROMPT"):',
        'if prompt.startswith("GENERIC PROMPT") or prompt.startswith("Prominence estimates"):'))
    CanonicalTraversalTests.prepare(test, notes=notes)
    meanings = dict(n1='Fixed cooking meaning', n2='Fixed food meaning', n3='Independent meaning')
    def answer(role, local, identifier, payload, state):
        if role == 'meaning':
            return dict(meaning=meanings[local['note_id']])
        return dict(meaning=meanings[local['note_id']], reason='Controlled graph fixture',
                    relation=('equivalent' if equivalent else 'canonical_contains_local')
                             if local['note_id'] == 'n2' else 'neither')
    return CanonicalTraversalTests.drive(test, answer)


if __name__ == '__main__':
    unittest.main()
