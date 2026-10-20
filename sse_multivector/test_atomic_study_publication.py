"""Exercise legacy atomic bindings through the supported offline publisher."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from .historical_study_publication import export_results
from .test_historical_study_publication import atomic_fixture


class AtomicStudyPublicationTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name)
        self.spec,self.selection,self.raw=atomic_fixture(self.root)

    def save(self,path,value):
        path=self.root/path
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(value,ensure_ascii=False)+'\n')
        return dict(path=path.relative_to(self.root).as_posix(),
                    sha256=hashlib.sha256(path.read_bytes()).hexdigest())

    def freeze(self):
        for row in self.selection['validation_sources']:
            row['sha256']=hashlib.sha256((self.root/row['path']).read_bytes()).hexdigest()
        self.spec.write_text(json.dumps(dict(schema_version=1,studies={'atomic-test':self.selection})))

    def export(self):
        self.freeze()
        path=self.root/'published'
        export_results(self.root,self.spec,'atomic-test',path)
        return {p.name:json.loads(p.read_text()) if p.name=='experiment.json'
                else [json.loads(line) for line in p.read_text().splitlines()]
                for p in path.iterdir()}

    def test_raw_answer_is_not_duplicated_as_parsed_subject_text(self):
        data=self.export()
        answer=data['answers.jsonl'][0]
        self.assertEqual(answer['output'],self.raw)
        self.assertNotIn('subjects',answer)
        self.assertEqual(answer['subject_count'],1)
        self.assertIsNone(answer['independent_trial'])
        self.assertEqual(data['experiment.json']['deprecation']['status'],'deprecated_historical_evidence')

    def test_original_parsed_final_survives_when_raw_receipt_is_unavailable(self):
        self.selection['runs'][0].pop('receipt')
        self.selection['validation_sources']=[b for b in self.selection['validation_sources']
            if b['path']!='study/run/results.jsonl']
        data=self.export()
        answer=data['answers.jsonl'][0]
        self.assertEqual(answer['representation'],'original_parsed_subjects')
        self.assertEqual(answer['subjects'],[dict(source_index=0,text='Tea')])
        self.assertNotIn('output',answer)
        self.assertTrue(data['experiment.json']['binding_limitations'])

    def test_rendered_request_and_raw_parsed_bindings_are_enforced(self):
        path=self.root/'study/run/results.jsonl'
        row=json.loads(path.read_text());row['prompt_sha256']='0'*64
        path.write_text(json.dumps(row)+'\n')
        with self.assertRaisesRegex(ValueError,'raw answer/request binding'):
            self.export()

    def test_conflicting_source_indices_and_orphan_receipts_fail(self):
        path=self.root/'study/run/output.json'
        native=json.loads(path.read_text());native['notes'][0]['subjects'][0]['source_index']=2
        path.write_text(json.dumps(native))
        with self.assertRaisesRegex(ValueError,'parsed output/input'):
            self.export()
        native['notes'][0]['subjects'][0]['source_index']=0
        path.write_text(json.dumps(native))
        path=self.root/'study/run/results.jsonl'
        native=json.loads(path.read_text());native['note_id']='orphan'
        path.write_text(json.dumps(native))
        with self.assertRaisesRegex(ValueError,'orphaned atomic receipt'):
            self.export()

    def test_assessments_and_measurements_keep_zeros_without_execution_accounts(self):
        self.selection['records']=[dict(**self.save('study/assistant-analysis.json',dict(
            status='assistant_analysis_only',user_approvals_recorded=False,counts=[dict(
                observation='case',baseline=0,candidate=1)],notes=[dict(analysis='Open question',
                auth_file='/private/SECRET')],codex_home='/private/SECRET')),role='assistant_assessment')]
        self.selection['parameters']=[self.save('study/plan.json',dict(question='Which prompt?',
            planned_new_calls=1,account='PRIVATE_ACCOUNT',codex_home='/private/SECRET',
            runtime=dict(auth_file='/private/SECRET')))]
        self.selection['dependencies']=[dict(experiment_id='saved-baseline',
            run_ids=['baseline/run/output.json'],policy='reused, not new samples')]
        data=self.export()
        judgment=data['judgments.jsonl'][0]
        self.assertEqual(judgment['actor'],'agent')
        self.assertFalse(judgment['assessment']['user_approvals_recorded'])
        self.assertEqual(judgment['assessment']['counts'][0]['baseline'],0)
        self.assertEqual(data['experiment.json']['dependencies'][0]['experiment_id'],'saved-baseline')
        self.assertNotIn('PRIVATE_ACCOUNT',json.dumps(data))
        self.assertNotIn('/private/SECRET',json.dumps(data))

    def test_review_questions_without_an_actor_stay_unknown_and_new_fields_fail(self):
        binding=self.save('study/review-focus.json',dict(schema_version=1,
            items=[dict(question='Is this supported?',user_decisions=[])]))
        self.selection['records']=[dict(**binding,role='open_review_questions')]
        data=self.export()
        self.assertEqual(data['judgments.jsonl'][0]['actor'],'unknown')
        self.assertEqual(data['judgments.jsonl'][0]['assessment']['items'][0]['user_decisions'],[])
        binding=self.save('study/review-focus.json',dict(schema_version=1,
            new_scientific_measurement=0))
        self.selection['records']=[dict(**binding,role='open_review_questions')]
        with self.assertRaisesRegex(ValueError,'unsupported atomic final-assessment fields'):
            self.export()

    def test_fresh_execution_identity_is_bound_without_publishing_it(self):
        path=self.root/'study/run/results.jsonl'
        row=json.loads(path.read_text());row['thread_id']='PRIVATE_EXECUTION_ID'
        path.write_text(json.dumps(row)+'\n')
        data=self.export()
        self.assertTrue(data['answers.jsonl'][0]['independent_trial'])
        self.assertNotIn('PRIVATE_EXECUTION_ID',json.dumps(data))

    def test_plan_methods_provenance_and_recorded_task_authorization_survive(self):
        plan=dict(schema_version=1,status='fixed_before_generation',
            status_at_creation='planned_before_generation',
            runs=[dict(version='ASv6.9',trial=2),dict(version='ASv6.8',trial=1)],
            outputs='Preserve subjects unchanged; assistant assessment separate; no user decisions.',
            approved_by_user='Proceed with test.',user_authorization='proceed with test',
            prompt_path='../proposal/ASv6.9.md',prompt_source='../proposal/ASv6.9.md',
            prompt_file_sha256='a'*64,prompt_sources={'ASv6.9':dict(
                path='sse_multivector/proposal/ASv6.9.md',sha256='a'*64)},
            input='../baseline/input.json',input_path='../baseline/input.json',
            selection_path='../baseline/selection.json',subject_registry='prompts.json',
            saved_baseline='../baseline/run',baseline_run_directories=['../baseline/run'],
            runtime=dict(model='saved-model',reasoning_effort='low',sequential=True,
                max_attempts=1,no_retry=True,account='PRIVATE_ACCOUNT',
                auth_file='/private/SECRET',launcher_memory_max_bytes=123),
            account='PRIVATE_ACCOUNT',codex_home='/private/SECRET')
        self.selection['parameters']=[self.save('study/plan.json',plan)]
        data=self.export()
        parameters=data['experiment.json']['parameters'][0]
        projected=parameters['values']
        for key in set(plan)-{'account','codex_home','runtime'}:
            self.assertEqual(projected.get(key),plan[key],key)
        self.assertEqual(projected['runtime'],dict(model='saved-model',reasoning_effort='low',
            sequential=True,max_attempts=1,no_retry=True))
        self.assertIn('not result approval',parameters['authorization_scope'])
        self.assertNotIn('PRIVATE_ACCOUNT',json.dumps(data))
        self.assertNotIn('/private/SECRET',json.dumps(data))

    def user_review(self,outcome):
        run=self.selection['runs'][0]
        sha=lambda raw:hashlib.sha256(raw).hexdigest()
        compact=lambda value:json.dumps(value,ensure_ascii=False,separators=(',',':')).encode()
        identity=dict(review_protocol='atomic-subject-review-v1',
            **{key:sha((self.root/run[field]).read_bytes()) for key,field in [
                ('manifest_sha256','manifest'),('input_sha256','input'),
                ('results_sha256','receipt'),('output_sha256','output')]})
        generation=sha(compact(identity))
        session=dict(schema_version=1,review_protocol='atomic-subject-review-v2',
            generation_run_sha256=generation,current_note_index=0,notes=[dict(note_id='post-one',
                list_item_id='subject-list:post-one',list_item_sha256=sha(compact([
                    generation,'subject_list','post-one','Tea is warm.',['Tea']])),subjects=[dict(
                    item_id='subject:post-one:0',item_sha256=sha(compact([
                    generation,'subject','post-one','Tea is warm.',0,'Tea'])),outcome=outcome,comment='')],
                coverage=None,coverage_comment='',distinctness=None,distinctness_comment='',
                prior_combined_check=None,selected_index=0,finished=False)])
        binding=self.save('study/review-state.json',dict(schema_version=1,
            state_sha256=sha(compact(session)),session=session))
        run['user_review']=binding
        return binding

    def test_only_explicit_bound_user_outcomes_become_user_decisions(self):
        self.user_review('rejected')
        data=self.export()
        self.assertEqual(len(data['judgments.jsonl']),1)
        self.assertEqual(data['judgments.jsonl'][0]['actor'],'user')
        self.assertEqual(data['judgments.jsonl'][0]['verdict'],'rejected')
        self.assertEqual(data['judgments.jsonl'][0]['comment'],'')

    def test_undecided_user_state_is_not_an_approval_and_wrong_generation_fails(self):
        binding=self.user_review(None)
        data=self.export()
        self.assertEqual(data['judgments.jsonl'],[])
        saved=json.loads((self.root/binding['path']).read_text())
        saved['session']['generation_run_sha256']='0'*64
        saved['state_sha256']=hashlib.sha256(json.dumps(saved['session'],ensure_ascii=False,
            separators=(',',':')).encode()).hexdigest()
        self.selection['runs'][0]['user_review']=self.save(binding['path'],saved)
        with self.assertRaisesRegex(ValueError,'different generation'):
            self.export()


if __name__=='__main__':
    unittest.main()
