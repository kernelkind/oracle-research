"""Historical title reviews keep exact answers, groups and recorded decisions."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from .historical_study_publication import export_results


class TitleAuditPublicationTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name)
        self.template='Instances:\n\n{NUMBERED_INSTANCES}\n\nName the shared subject.'
        registry=self.save('study/registry.json',{'v1':dict(prompt_template=self.template,
            fragment_order='source_order',instance_unit='one_vector')})
        partition=self.save('study/partition.json',dict(schema_version=1,rules=dict(
            complete_linkage='saved groups'),vectors=[dict(ordinal=i,note_id='note-'+str(i),
                subject_id='subject-'+str(i),takeaway='Tea',source_note=text,
                selected_source_fragments=[dict(text='Tea',occurrence=1)])
            for i,text in enumerate(['Tea for all.','Tea is nice.'])],
            resolutions=[dict(level=dict(percentile=50,pairwise_min_cosine=0.5),
                complete_linkage=dict(regions=[dict(region_index=0,members=[0,1],
                    distinct_note_count=2,minimum_within_cosine=0.6)]))]))
        reviews=self.save('study/reviews.json',dict(schema_version=1,decision_owner='user',
            criterion='Would every instance be expected?',decisions=[dict(segment_id='S001',
                minimum_cosine=0.6,title_reviewed='Tea enjoyment',decision='pass')]))
        self.raw='**Tea**'
        rendered=self.template.replace('{NUMBERED_INSTANCES}','1. “Tea”\n2. “Tea”')
        configuration=self.save('study/config.json',dict(schema_version=1,model='saved-model',
            reasoning_effort='low',codex_home='/private/SECRET',codex_binary='/private/runner',
            run_directory='run',prompts=[dict(prompt_id='S001',text=rendered)]))
        manifest=self.save('study/run/manifest.json',dict(schema_version=1,mode='prompt',
            model='saved-model',reasoning_effort='low',config_sha256=configuration['sha256'],
            codex_version='saved-version',wrapper_sha256='a'*64,prompts=[dict(prompt_id='S001',text=rendered)]))
        receipt=self.save('study/run/results.jsonl',dict(schema_version=1,stage='prompt',
            note_id='S001',job_key='prompt:S001',status='succeeded',attempt=1,error=None,exit_code=0,
            manifest_sha256=manifest['sha256'],prompt_sha256=hashlib.sha256(rendered.encode()).hexdigest(),
            model='saved-model',reasoning_effort='low',codex_version='saved-version',
            final_output_raw=self.raw,final_output_sha256=hashlib.sha256(self.raw.encode()).hexdigest(),
            response=self.raw,response_schema_sha256=None,thread_id='PRIVATE_THREAD',
            argv=['/private/SECRET'],stderr='PRIVATE_DIAGNOSTIC',usage=dict(input_tokens=10,output_tokens=2)))
        output=self.save('study/run/output.json',dict(schema_version=1,manifest_sha256=manifest['sha256'],
            responses=[dict(prompt_id='S001',response=self.raw)]))
        self.selection=dict(profile='title-audit',kind='cutoff',partition=partition,registry=registry,
            prompt_version='v1',reviews=reviews,runs=[dict(configuration=configuration,manifest=manifest,
                receipt=receipt,output=output,fragment_mode='exact_source')],groups=[dict(
                prompt_id='S001',members=[0,1],source_regions=[dict(percentile=50,region_index=0)])])
        self.spec=self.root/'selection.json'

    def save(self,name,value):
        path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True)
        raw=(json.dumps(value,ensure_ascii=False)+'\n').encode();path.write_bytes(raw)
        return dict(path=name,sha256=hashlib.sha256(raw).hexdigest())

    def export(self):
        self.spec.write_text(json.dumps(dict(schema_version=1,studies={'test':self.selection})))
        output=self.root/'published';export_results(self.root,self.spec,'test',output)
        return {p.name:json.loads(p.read_text()) if p.name=='experiment.json' else
                [json.loads(line) for line in p.read_text().splitlines()] for p in output.iterdir()}

    def replace(self,binding,value):
        fresh=self.save(binding['path'],value)
        binding['sha256']=fresh['sha256']

    def higher(self):
        partition=json.loads((self.root/self.selection['partition']['path']).read_bytes())
        partition['vectors'].append(dict(ordinal=2,note_id='note-2',subject_id='subject-2',
            takeaway='Tea plants',source_note='Tea grows.',selected_source_fragments=[dict(text='Tea',occurrence=1)]))
        self.replace(self.selection['partition'],partition)
        fine_reviews=self.save('study/fine-reviews.json',dict(schema_version=1,
            decision_owner='user',criterion='Membership',decisions=[dict(segment_id='S00'+str(i+1),
                decision='pass',title_reviewed=title,minimum_cosine=0.6)
                for i,title in enumerate(['Tea','Tea time','Tea plants'])]))
        fine_output=self.save('study/fine-output.json',dict(schema_version=1,responses=[dict(
            prompt_id='S00'+str(i+1),response='**'+title+'**')
            for i,title in enumerate(['Tea','Tea time','Tea plants'])]))
        hierarchy=self.save('study/hierarchy.json',dict(schema_version=1,rules=dict(fine_segments='saved'),
            partition_analysis_sha256=self.selection['partition']['sha256'],
            review_decisions_sha256=fine_reviews['sha256'],accepted_minimum_cosine=0.6,
            hierarchy=dict(fine_segments=[dict(segment_id='F00000'+str(i),members=[i]) for i in range(3)],
                merges=[dict(merge_index=0,children=[dict(kind='fine_segment',id='F000000'),
                    dict(kind='fine_segment',id='F000001')]),dict(merge_index=1,children=[
                    dict(kind='merge',id=0),dict(kind='fine_segment',id='F000002')])],
                root=dict(kind='merge',id=1))))
        projection=self.save('study/projection.json',dict(schema_version=1,inputs=dict(
            partition_analysis_sha256=self.selection['partition']['sha256'],
            hierarchy_analysis_sha256=hierarchy['sha256'],fine_title_review_decisions_sha256=fine_reviews['sha256'],
            fine_title_run_output_sha256=fine_output['sha256'],fine_title_prompt_registry_sha256='c'*64),
            rules=dict(implicit_root='H000001',prompt_version='v1'),fine_subject_titles=[dict(
                fine_segment_id='F00000'+str(i),source_prompt_id='S00'+str(i+1),title=title)
                for i,title in enumerate(['Tea','Tea time','Tea plants'])],mechanical_projection=dict(
                provisional_title_nodes=['H000000'],collapsed_equal_note_set_edges=[],duplicate_sibling_note_sets=[])))
        rendered=self.template.replace('{NUMBERED_INSTANCES}','1. “Tea”\n2. “Tea time”')
        run=self.selection['runs'][0]
        config=json.loads((self.root/run['configuration']['path']).read_bytes())
        config['prompts']=[dict(prompt_id='H000000',text=rendered)]
        self.replace(run['configuration'],config)
        manifest=json.loads((self.root/run['manifest']['path']).read_bytes())
        manifest.update(config_sha256=run['configuration']['sha256'],prompts=config['prompts'])
        self.replace(run['manifest'],manifest)
        receipt=json.loads((self.root/run['receipt']['path']).read_bytes())
        self.raw='**Tea activities**'
        receipt.update(note_id='H000000',job_key='prompt:H000000',manifest_sha256=run['manifest']['sha256'],
            prompt_sha256=hashlib.sha256(rendered.encode()).hexdigest(),final_output_raw=self.raw,
            final_output_sha256=hashlib.sha256(self.raw.encode()).hexdigest(),response=self.raw)
        self.replace(run['receipt'],receipt)
        self.replace(run['output'],dict(schema_version=1,manifest_sha256=run['manifest']['sha256'],
            responses=[dict(prompt_id='H000000',response=self.raw)]))
        self.replace(self.selection['reviews'],dict(schema_version=1,decision_owner='user',
            criterion='Every fine subject expected?',decisions=[]))
        self.selection.update(kind='higher',hierarchy=hierarchy,projection=projection,
            fine_reviews=fine_reviews,fine_outputs=[dict(**fine_output,
                projection_hash_field='fine_title_run_output_sha256')])
        return fine_reviews,fine_output

    def test_raw_title_and_differently_worded_user_review_remain_separate(self):
        data=self.export()
        self.assertEqual(data['answers.jsonl'][0]['output'],self.raw)
        judgment=data['judgments.jsonl'][0]
        self.assertEqual(judgment['actor'],'user')
        self.assertEqual(judgment['title_reviewed'],'Tea enjoyment')
        self.assertFalse(judgment['reviewed_title_matches_saved_answer'])
        self.assertEqual(judgment['decision'],'pass')
        self.assertNotIn('/private/SECRET',json.dumps(data))
        self.assertNotIn('PRIVATE_THREAD',json.dumps(data))
        self.assertNotIn('PRIVATE_DIAGNOSTIC',json.dumps(data))

    def test_source_masks_and_actual_supplied_display_are_both_preserved(self):
        partition=json.loads((self.root/self.selection['partition']['path']).read_bytes())
        for v in partition['vectors']:
            v.update(source_note='"Tea  time"',selected_source_fragments=[dict(text='"Tea  time"',occurrence=1)])
        self.replace(self.selection['partition'],partition)
        self.selection['runs'][0]['fragment_mode']='saved_display_normalization'
        run=self.selection['runs'][0]
        config=json.loads((self.root/run['configuration']['path']).read_bytes())
        config['prompts'][0]['text']=self.template.replace('{NUMBERED_INSTANCES}','1. “Tea time”\n2. “Tea time”')
        self.replace(run['configuration'],config)
        manifest=json.loads((self.root/run['manifest']['path']).read_bytes())
        manifest.update(config_sha256=run['configuration']['sha256'],prompts=config['prompts'])
        self.replace(run['manifest'],manifest)
        receipt=json.loads((self.root/run['receipt']['path']).read_bytes())
        receipt.update(manifest_sha256=run['manifest']['sha256'],prompt_sha256=hashlib.sha256(config['prompts'][0]['text'].encode()).hexdigest())
        self.replace(run['receipt'],receipt)
        self.replace(run['output'],dict(schema_version=1,manifest_sha256=run['manifest']['sha256'],
            responses=[dict(prompt_id='S001',response=self.raw)]))
        data=self.export();inputs=data['inputs.jsonl']
        self.assertEqual(next(r for r in inputs if r['kind']=='mask')['fragments'],['"Tea  time"'])
        self.assertEqual(next(r for r in inputs if r['kind']=='title_input')['supplied_fragments'],[['Tea time'],['Tea time']])

    def test_higher_inputs_follow_native_integer_merge_ids_without_inventing_a_review(self):
        self.higher();data=self.export()
        self.assertEqual(data['judgments.jsonl'],[])
        self.assertEqual(data['results.jsonl'][0]['unreviewed_call_ids'],['H000000'])
        group=next(row for row in data['inputs.jsonl'] if row['kind']=='title_input')
        self.assertEqual(group['fine_segment_ids'],['F000000','F000001'])
        self.assertEqual(group['supplied_fragments'],[['Tea'],['Tea time']])
        self.assertEqual(data['experiment.json']['parameters']['hierarchy_parameters']['accepted_minimum_cosine'],0.6)

    def test_reused_fine_title_must_remain_bound_to_its_original_pass_record(self):
        reviews,_=self.higher()
        native=json.loads((self.root/reviews['path']).read_bytes());native['decisions'][0]['decision']='reject'
        self.replace(reviews,native)
        projection=json.loads((self.root/self.selection['projection']['path']).read_bytes())
        projection['inputs']['fine_title_review_decisions_sha256']=reviews['sha256']
        self.replace(self.selection['projection'],projection)
        with self.assertRaisesRegex(ValueError,'reused evidence mismatch'):
            self.export()

    def test_orphan_review_or_changed_cutoff_cannot_attach_to_another_group(self):
        binding=self.selection['reviews'];native=json.loads((self.root/binding['path']).read_bytes())
        native['decisions'][0]['minimum_cosine']=0.2;self.replace(binding,native)
        with self.assertRaisesRegex(ValueError,'reviewed/source minimum cosine'):
            self.export()
        native['decisions'][0].update(minimum_cosine=0.6,segment_id='S999');self.replace(binding,native)
        with self.assertRaisesRegex(ValueError,'orphaned'):
            self.export()

    def test_six_decimal_saved_cutoff_is_retained_alongside_exact_native_value(self):
        partition=json.loads((self.root/self.selection['partition']['path']).read_bytes())
        partition['resolutions'][0]['complete_linkage']['regions'][0]['minimum_within_cosine']=0.6000004
        self.replace(self.selection['partition'],partition)
        data=self.export();judgment=data['judgments.jsonl'][0]
        self.assertEqual(judgment['minimum_cosine'],0.6)
        self.assertEqual(judgment['minimum_cosine_match'],'rounded_to_six_decimal_places')
        self.assertEqual(next(r for r in data['inputs.jsonl'] if r['kind']=='title_input')['minimum_within_cosine'],0.6000004)

    def test_prompt_or_source_membership_changes_fail_before_writing_output(self):
        self.selection['groups'][0]['members']=[1,0]
        with self.assertRaisesRegex(ValueError,'native region'):
            self.export()
        self.assertFalse((self.root/'published').exists())

    def test_source_files_remain_unchanged_and_refresh_preserves_mtimes(self):
        before={p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.export();output=self.root/'published'
        before_output={p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in output.iterdir()}
        self.export()
        self.assertEqual(before,{p:p.read_bytes() for p in before})
        self.assertEqual(before_output,{p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in output.iterdir()})

    def test_safe_isolation_and_final_call_measurements_are_preserved(self):
        run=self.selection['runs'][0]
        isolation=dict(fresh_process_per_job=True,ephemeral=True,web_search='disabled',
            shell_environment_inherit='none',disabled_features=['shell_tool'],
            runtime_context_overrides=['include_environment_context=false'],
            model_instructions="Follow the user's instructions.\n",
            model_instructions_sha256=hashlib.sha256(b"Follow the user's instructions.\n").hexdigest())
        manifest=json.loads((self.root/run['manifest']['path']).read_bytes())
        manifest['isolation']=isolation;self.replace(run['manifest'],manifest)
        receipt=json.loads((self.root/run['receipt']['path']).read_bytes())
        receipt.update(manifest_sha256=run['manifest']['sha256'],elapsed_seconds=0.25)
        self.replace(run['receipt'],receipt)
        self.replace(run['output'],dict(schema_version=1,manifest_sha256=run['manifest']['sha256'],
            responses=[dict(prompt_id='S001',response=self.raw)]))
        data=self.export();settings=next(iter(data['experiment.json']['settings'].values()))
        self.assertEqual(settings.get('isolation'),isolation)
        answer=data['answers.jsonl'][0]
        self.assertEqual(answer['elapsed_seconds'],0.25)
        self.assertEqual(answer['status'],'succeeded')
        self.assertEqual(answer['exit_code'],0)
        self.assertIsNone(answer['error'])
        self.assertIsNone(answer['response_schema_sha256'])

    def test_raw_receipt_tampering_and_missing_source_occurrences_fail(self):
        run=self.selection['runs'][0]
        receipt=json.loads((self.root/run['receipt']['path']).read_bytes())
        receipt['final_output_raw']='Changed title';self.replace(run['receipt'],receipt)
        with self.assertRaisesRegex(ValueError,'saved receipt/answer/settings'):
            self.export()
        receipt['final_output_raw']=self.raw;self.replace(run['receipt'],receipt)
        partition=json.loads((self.root/self.selection['partition']['path']).read_bytes())
        partition['vectors'][0]['selected_source_fragments'][0]['occurrence']=2
        self.replace(self.selection['partition'],partition)
        with self.assertRaisesRegex(ValueError,'fragment occurrence is absent'):
            self.export()

    def test_saved_model_instruction_hash_is_verified_before_publication(self):
        run=self.selection['runs'][0]
        manifest=json.loads((self.root/run['manifest']['path']).read_bytes())
        manifest['isolation']=dict(model_instructions='Saved instructions.',model_instructions_sha256='0'*64)
        self.replace(run['manifest'],manifest)
        receipt=json.loads((self.root/run['receipt']['path']).read_bytes())
        receipt['manifest_sha256']=run['manifest']['sha256'];self.replace(run['receipt'],receipt)
        self.replace(run['output'],dict(schema_version=1,manifest_sha256=run['manifest']['sha256'],
            responses=[dict(prompt_id='S001',response=self.raw)]))
        with self.assertRaisesRegex(ValueError,'model instructions hash mismatch'):
            self.export()


if __name__=='__main__':
    unittest.main()
