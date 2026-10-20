"""Saved prominence scores use the source-bound historical publication path."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from .historical_study_publication import export_results
from ._runner_bootstrap import shared


class ProminenceStudyPublicationTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name)
        self.paths={}
        self.source=self.save('study/source.json',dict(notes=[dict(note_id='source-note',
            text='Drink tea.',subjects=[dict(id='N01-S01',byte_spans=[[6,9]],fragments=['tea'])])]))
        prompt='Score prominence.\n{INPUT_JSON}\n'
        self.prompt=self.save_raw('study/PPv10.md',prompt.encode())
        masked=dict(mask=['tea'],marked_post='Drink ⟦tea⟧.')
        case=dict(id='R01',label='Tea',format='corpus',source='study/source.json',
            source_id='N01-S01',note_id='source-note',text='Drink tea.',
            character_spans=[[6,9]],input=masked)
        self.inputs=self.save('study/inputs.json',[case])
        plan=dict(experiment='test',prompt_version='PPv10',prompt_path='PPv10.md',
            prompt_sha256=self.prompt['sha256'],model='saved-model',reasoning_effort='low',
            provider='openai-codex',trials_per_case=1,selection='No gold labels.',
            cases=[{k:v for k,v in case.items() if k not in {'note_id','text','character_spans','input'}}],
            comparisons=[],limitations=['One saved call.'])
        self.plan=self.save('study/plan.json',plan)
        rendered=prompt.replace('{INPUT_JSON}',json.dumps(masked,ensure_ascii=False,indent=2))
        config=dict(schema_version=1,provider='openai-codex',model='saved-model',
            reasoning_effort='low',auth_file='/private/SECRET',runner_binary='/private/runner',
            run_directory='run',prompts=[dict(prompt_id='R01',text=rendered)])
        self.config=self.save('study/config.json',config)
        manifest=dict(schema_version=1,mode='prompt',provider='openai-codex',model='saved-model',
            reasoning_effort='low',config_sha256=self.config['sha256'],timeout_seconds=900,
            max_output_tokens=None,runner_version='saved-version',runner_sha256='a'*64,
            wrapper_sha256='b'*64,prompts=config['prompts'],auth_file='/private/SECRET')
        self.manifest=self.save('study/run/manifest.json',manifest)
        self.raw='{"prominence":0}'
        request=shared('extraction_pipeline')._prompt_request_key(manifest,rendered)
        receipt=dict(schema_version=1,stage='prompt',status='succeeded',exit_code=0,error=None,
            note_id='R01',job_key='prompt:R01',manifest_sha256=self.manifest['sha256'],
            provider='openai-codex',model='saved-model',reasoning_effort='low',
            runner_sha256='a'*64,runner_version='saved-version',wrapper_sha256='b'*64,
            prompt_sha256=hashlib.sha256(rendered.encode()).hexdigest(),request_sha256=request,
            response_schema_sha256=None,final_output_raw=self.raw,
            final_output_sha256=hashlib.sha256(self.raw.encode()).hexdigest(),response=self.raw,
            usage=dict(input=1,output=2,totalTokens=3),argv=['/private/SECRET'],stderr='PRIVATE_DIAGNOSTIC')
        self.receipt=self.save('study/run/results.jsonl',receipt)
        self.output=self.save('study/run/output.json',dict(schema_version=1,
            manifest_sha256=self.manifest['sha256'],responses=[dict(prompt_id='R01',response=self.raw)]))
        self.result=self.save('study/results.json',dict(experiment='test',prompt_sha256=self.prompt['sha256'],
            model='saved-model',reasoning_effort='low',cases=1,valid_scores=1,new_calls=1,
            usage=dict(input=1,output=2,totalTokens=3),results=[dict(id='R01',label='Tea',score=0,
                error=None,raw=self.raw,request_sha256=request,usage=receipt['usage'],execution='new_call')],
            comparisons=[],limitations=['One saved call.']))
        self.pinned=self.save('study/input-hashes.json',{str(self.root/b['path']):b['sha256']
            for b in [self.source,self.prompt,self.inputs,self.plan,self.config]})
        self.selection=dict(profile='prominence',plan=self.plan,inputs=self.inputs,
            configuration=self.config,manifest=self.manifest,receipt=self.receipt,
            output=self.output,result=self.result,prompt=self.prompt,pinned_inputs=self.pinned,
            origin_sources=[dict(**self.source,format='corpus')],assessments=[],
            subject_versions=[],subject_provenance_status='unknown')
        self.spec=self.root/'selection.json'

    def save_raw(self,path,raw):
        target=self.root/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        binding=dict(path=path,sha256=hashlib.sha256(raw).hexdigest());self.paths[path]=binding
        return binding

    def save(self,path,value):
        return self.save_raw(path,(json.dumps(value,ensure_ascii=False)+'\n').encode())

    def export(self):
        self.spec.write_text(json.dumps(dict(schema_version=1,studies={'test':self.selection})))
        output=self.root/'published'
        export_results(self.root,self.spec,'test',output)
        return {p.name:json.loads(p.read_text()) if p.name=='experiment.json' else [
            json.loads(line) for line in p.read_text().splitlines()] for p in output.iterdir()}

    def replace(self,path,value):
        binding=self.save(path,value)
        def update(node):
            if isinstance(node,dict):
                if node.get('path')==path and 'sha256' in node:
                    node['sha256']=binding['sha256']
                for item in node.values():update(item)
            elif isinstance(node,list):
                for item in node:update(item)
        update(self.selection)
        pinned_path=self.root/self.pinned['path']
        pinned=json.loads(pinned_path.read_bytes())
        name=str(self.root/path)
        if name in pinned:
            pinned[name]=binding['sha256']
            new=self.save(self.pinned['path'],pinned)
            self.selection['pinned_inputs']=new
        return binding

    def test_offline_export_retains_zero_score_raw_answer_and_exact_mask_context(self):
        result=self.export()
        self.assertEqual(result['answers.jsonl'][0]['output'],self.raw)
        self.assertEqual(result['results.jsonl'][0]['score'],0)
        self.assertEqual(result['inputs.jsonl'][0]['text'],'Drink tea.')
        self.assertEqual(result['answers.jsonl'][0]['character_spans'],[[6,9]])
        self.assertNotIn('/private/SECRET',json.dumps(result))
        self.assertNotIn('PRIVATE_DIAGNOSTIC',json.dumps(result))

    def test_final_score_and_rendered_request_mismatches_are_rejected(self):
        receipt=json.loads((self.root/self.receipt['path']).read_bytes())
        receipt['prompt_sha256']='0'*64
        self.replace(self.receipt['path'],receipt)
        with self.assertRaisesRegex(ValueError,'raw answer/request binding'):
            self.export()

    def test_changed_measurement_cannot_silently_override_the_raw_score(self):
        result=json.loads((self.root/self.result['path']).read_bytes())
        result['results'][0]['score']=1
        self.replace(self.result['path'],result)
        with self.assertRaisesRegex(ValueError,'final score/usage binding'):
            self.export()

    def test_original_selection_occurrence_is_bound_not_just_fragment_text(self):
        original=json.loads((self.root/self.source['path']).read_bytes())
        original['notes'][0]['subjects'][0].update(byte_spans=[[0,5]],fragments=['Drink'])
        self.replace(self.source['path'],original)
        with self.assertRaisesRegex(ValueError,'original selection'):
            self.export()

    def test_json_and_markdown_assessments_keep_science_and_explicit_actor(self):
        self.selection['assessments']=[dict(**self.save('study/assessment.json',dict(
            assessor='primary assistant; not a user verdict',findings=[dict(cases=['R01'],
            comparison=dict(tie=0,reversal=0))],recommendation_suggestion_only='Do not change prompt.',
            execution_notes='Subscription runner, selected account PRIVATE_ACCOUNT, no retries.',
            auth_file='/private/SECRET')),format='json'),dict(**self.save_raw(
            'study/assessment.md',b'These are assistant assessments, not user-approved labels.\n'),format='markdown')]
        data=self.export();judgments=data['judgments.jsonl']
        self.assertEqual([j['actor'] for j in judgments],['agent','agent'])
        self.assertEqual(judgments[0]['assessment']['findings'][0]['comparison']['tie'],0)
        self.assertEqual(judgments[0]['assessment']['recommendation_suggestion_only'],'Do not change prompt.')
        self.assertNotIn('PRIVATE_ACCOUNT',json.dumps(data))
        self.assertNotIn('/private/SECRET',json.dumps(data))

    def test_absent_execution_is_unknown_and_recorded_reuse_is_not_a_new_trial(self):
        result=json.loads((self.root/self.result['path']).read_bytes())
        result['results'][0]['execution']='cross_run_reuse';result['new_calls']=0
        self.replace(self.result['path'],result)
        data=self.export()
        self.assertEqual(data['answers.jsonl'][0]['execution'],'cross_run_reuse')
        self.assertIsNone(data['answers.jsonl'][0]['receipt_execution'])
        self.assertEqual(data['experiment.json']['reuse']['recorded_new_calls'],0)
        self.assertNotIn('independent_trial',data['answers.jsonl'][0])

    def test_source_changes_are_rejected_and_unchanged_exports_keep_mtimes(self):
        before={p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.export()
        output=self.root/'published'
        mtimes={p.name:p.stat().st_mtime_ns for p in output.iterdir()}
        self.export()
        self.assertEqual(mtimes,{p.name:p.stat().st_mtime_ns for p in output.iterdir()})
        self.assertEqual(before,{p:p.read_bytes() for p in before})
        (self.root/self.inputs['path']).write_text('{}')
        with self.assertRaisesRegex(ValueError,'hash mismatch'):
            self.export()

    def test_only_explicit_historical_code_pin_mismatches_become_limitations(self):
        helper=self.save_raw('study/old-helper.py',b'# relocated source\n')
        self.selection['validation_sources']=[helper]
        pinned=json.loads((self.root/self.pinned['path']).read_bytes())
        pinned[str(self.root/helper['path'])]='d'*64
        self.selection['pinned_inputs']=self.save(self.pinned['path'],pinned)
        with self.assertRaisesRegex(ValueError,'pinned source hash mismatch'):
            self.export()
        self.selection['historical_code_pins']={helper['path']:'d'*64}
        self.selection['historical_code_revisions']={helper['path']:'e'*40}
        data=self.export();limitation=data['experiment.json']['binding_limitations'][0]
        self.assertEqual(limitation['recorded_sha256'],'d'*64)
        self.assertEqual(limitation['current_source_sha256'],helper['sha256'])
        self.assertEqual(limitation['historical_source_git_revision'],'e'*40)

    def test_single_case_uses_exact_saved_mask_receipt_and_deprecated_as_lineage(self):
        case=json.loads((self.root/self.inputs['path']).read_bytes())[0]
        case={k:v for k,v in case.items() if k not in {'format','source','source_id','label'}}
        case.update(subject='Tea',mask_request_sha256='c'*64)
        self.replace(self.inputs['path'],case)
        plan=json.loads((self.root/self.plan['path']).read_bytes())
        plan.pop('cases');plan.pop('comparisons');plan.update(case='R01',scope='One saved scorer call.')
        self.replace(self.plan['path'],plan)
        result=json.loads((self.root/self.result['path']).read_bytes())
        measured=result['results'][0]
        single={k:v for k,v in result.items() if k not in {'results','cases','valid_scores','new_calls','comparisons'}}
        single.update({k:v for k,v in measured.items() if k!='id'})
        single.update(case='R01',subject='Tea',fragments=['tea'],mask_request_sha256='c'*64)
        self.replace(self.result['path'],single)
        original=dict(case,subject_origin='Verbatim saved ASv6.48 output')
        self.selection['origin_sources']=[]
        self.selection['validation_sources']=[self.source]
        raw=json.dumps(dict(meaning='Tea',expressible=True,evidence='Tea is present.',
                           mask=[dict(word=2,text='tea')]))
        mask_receipt=dict(note_id='R01',status='succeeded',request_sha256='c'*64,
            final_output_raw=raw,final_output_sha256=hashlib.sha256(raw.encode()).hexdigest())
        self.selection['mask_source']=dict(cases=self.save('study/mask-cases.json',[original]),
            receipt=self.save('study/mask-results.jsonl',mask_receipt))
        data=self.export()
        self.assertEqual(data['answers.jsonl'][0]['subject_provenance']['status'],'deprecated')
        self.assertEqual(data['answers.jsonl'][0]['subject_provenance']['version'],'ASv6.48')
        self.assertEqual(data['answers.jsonl'][0]['mask_request_sha256'],'c'*64)
        self.assertEqual(data['judgments.jsonl'],[])
        self.assertIsNone(data['experiment.json']['reuse']['recorded_new_calls'])


if __name__=='__main__':
    unittest.main()
