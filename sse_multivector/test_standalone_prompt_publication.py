"""Early TP/MP evidence uses the supported historical publication API."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class StandalonePromptPublicationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def save(self, name, value):
        path = self.root/name
        path.parent.mkdir(parents=True,exist_ok=True)
        raw = (json.dumps(value,ensure_ascii=False)+'\n').encode()
        path.write_bytes(raw)
        return dict(path=name,sha256=hashlib.sha256(raw).hexdigest())

    def fixture(self, *, partial=False):
        prompts = [dict(prompt_id='case-'+str(i),text='Choose exact fragments.\n<post>\nTea '+str(i)+
            ' and coffee.\n</post>\n<takeaway>\nThe post names tea.\n</takeaway>')
            for i in range(5 if partial else 1)]
        if partial:
            prompts = [dict(prompt_id=p['prompt_id'],text='List takeaways.\n<post>\nPost '+str(i)+
                '.\n</post>') for i,p in enumerate(prompts)]
        config = self.save('study/config.json',dict(schema_version=1,model='saved-model',
            reasoning_effort='low',codex_home='/private/auth',prompts=prompts))
        manifest = self.save('study/run/manifest.json',dict(schema_version=1,
            config_sha256=config['sha256'],model='saved-model',reasoning_effort='low',
            codex_home='/private/auth',prompts=prompts))
        receipt_path = self.root/'study/run/results.jsonl'
        rows = [dict(schema_version=1,status='succeeded',stage='prompt',note_id=p['prompt_id'],
            attempt=1,manifest_sha256=manifest['sha256'],
            prompt_sha256=hashlib.sha256(p['text'].encode()).hexdigest(),
            final_output_raw='["Tea"]',final_output_sha256=hashlib.sha256(b'["Tea"]').hexdigest(),
            response='["Tea"]',stderr='PRIVATE_CANARY',argv=['/private/runner'])
            for p in prompts[:2 if partial else 1]]
        receipt_path.write_text(''.join(json.dumps(row)+'\n' for row in rows))
        receipt = dict(path='study/run/results.jsonl',sha256=hashlib.sha256(receipt_path.read_bytes()).hexdigest())
        selection = dict(profile='standalone-prompt',directory='study',inputs=[],parameters=[],records=[])
        if partial:
            selection['receipt_only_answers'] = [dict(**receipt,manifest=manifest,
                configuration=config,task='takeaway')]
        else:
            output = self.save('study/run/output.json',dict(schema_version=1,
                manifest_sha256=manifest['sha256'],responses=[dict(prompt_id='case-0',response='["Tea"]')]))
            selection['answers'] = [dict(**output,manifest=manifest,configuration=config,
                                        receipt=receipt,task='mask')]
        self.save('selection.json',dict(schema_version=1,studies={'early-test':selection}))

    def export(self):
        from sse_multivector.historical_study_publication import export_results
        output = self.root/'publication'
        export_results(self.root,self.root/'selection.json','early-test',output)
        return output

    def records(self, output, name):
        return [json.loads(line) for line in (output/name).read_text().splitlines()]

    def test_parameter_field_selection_retains_scientific_scope_without_ledger_prose(self):
        self.fixture()
        plan = self.save('study/plan.json',dict(model='saved-model',cost=0,
            execution='Existing subscription route; no paid fallback.',
            spending='PRIVATE_CANARY: global ledger reservation.'))
        fields = [['model'],['cost'],['execution']]
        self.change('selection.json',lambda x:x['studies']['early-test']['parameters'].append(
            dict(**plan,fields=fields)))
        output = self.export()
        row = next(x for x in self.records(output,'inputs.jsonl') if x['type']=='study_parameters')
        self.assertEqual(row['source'],dict(**plan,fields=fields))
        self.assertEqual(row['data'],dict(model='saved-model',cost=0,
            execution='Existing subscription route; no paid fallback.'))
        self.assertNotIn('PRIVATE_CANARY',''.join(path.read_text() for path in output.iterdir()))

    def change(self, name, change):
        value=json.loads((self.root/name).read_text())
        change(value)
        binding=self.save(name,value)
        spec=json.loads((self.root/'selection.json').read_text())
        def update(value):
            if isinstance(value,dict):
                if value.get('path')==name and 'sha256' in value:value['sha256']=binding['sha256']
                for child in value.values():update(child)
            elif isinstance(value,list):
                for child in value:update(child)
        update(spec)
        self.save('selection.json',spec)
        return binding

    def test_early_mask_retains_fixed_takeaway_and_byte_exact_response(self):
        self.fixture()

        output = self.export()

        answer = self.records(output,'answers.jsonl')[0]
        self.assertEqual(answer['role'],'mask_answer')
        self.assertEqual(answer['raw_response'],'["Tea"]')
        supplied = next(row for row in self.records(output,'inputs.jsonl') if row['type']=='prompt_input')
        self.assertEqual(supplied['variables']['takeaway'],'The post names tea.')
        self.assertNotIn('subject',supplied['variables'])
        self.assertNotIn('PRIVATE_CANARY',''.join(path.read_text() for path in output.iterdir()))

    def test_receipt_only_partial_trial_has_two_answers_and_three_unknown_cases(self):
        self.fixture(partial=True)
        output=self.export()
        answers=self.records(output,'answers.jsonl')
        self.assertEqual(len(answers),2)
        self.assertEqual({row['role'] for row in answers},{'takeaway_answer'})
        outcomes=self.records(output,'results.jsonl')
        self.assertEqual(len(outcomes),3)
        self.assertEqual({row['outcome'] for row in outcomes},{'not_recorded'})
        supplied=[row for row in self.records(output,'inputs.jsonl') if row['type']=='prompt_input']
        self.assertEqual(len(supplied),5)
        self.assertTrue(all(row['canonical_note_id'] is None for row in supplied))

    def test_partial_outcomes_follow_native_manifest_order_across_python_hash_seeds(self):
        self.fixture(partial=True)
        snapshots=[]
        for seed in ('1','2'):
            output=self.root/('export-seed-'+seed)
            result=subprocess.run([sys.executable,'-c',
                'from sse_multivector.historical_study_publication import export_results; '
                'import sys; export_results(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4])',
                str(self.root),str(self.root/'selection.json'),'early-test',str(output)],
                env={**os.environ,'PYTHONHASHSEED':seed},capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual([row['prompt_id'] for row in self.records(output,'results.jsonl')],
                             ['case-2','case-3','case-4'])
            snapshots.append({path.name:path.read_bytes() for path in output.iterdir()})
        self.assertEqual(snapshots[0],snapshots[1])

    def test_helper_code_hash_is_part_of_publication_provenance(self):
        self.fixture()
        output=self.export()
        metadata=json.loads((output/'experiment.json').read_text())
        from sse_multivector import mask_goal_publication
        self.assertEqual(metadata['exporter_sources']['sse_multivector/mask_goal_publication.py'],
                         hashlib.sha256(Path(mask_goal_publication.__file__).read_bytes()).hexdigest())

    def test_local_cli_launcher_omitted_while_execution_methods_remain(self):
        self.fixture()
        plan=self.save('study/plan.json',dict(execution=dict(cli='/nix/store/local/bin/runner',
            prompt_rendering='No normalization.',prior_messages=0,tools=[])))
        self.change('selection.json',lambda x:x['studies']['early-test']['parameters'].append(plan))
        output=self.export()
        parameter=next(row for row in self.records(output,'inputs.jsonl') if row['type']=='study_parameters')
        self.assertEqual(parameter['data']['execution'],dict(prompt_rendering='No normalization.',
                                                           prior_messages=0,tools=[]))

    def test_known_subject_lineage_is_verified_and_marked_deprecated_without_deprecating_posts(self):
        self.fixture()
        manifest=self.save('baseline/manifest.json',dict(schema_version=1,subject=dict(prompt_version='ASv6.8')))
        source=self.save('baseline/output.json',dict(schema_version=1,manifest_sha256=manifest['sha256'],
            notes=[dict(note_id='source-post',text='Tea 0 and coffee.',subjects=[
                dict(source_index=0,text='The post names tea.')])]))
        cases=self.save('study/cases.json',dict(items=[dict(note_id='source-post',note='Tea 0 and coffee.',
            source_index=0,subject='The post names tea.')]))
        self.change('selection.json',lambda x:x['studies']['early-test'].update(inputs=[cases],
            baseline_references=[dict(**source,manifest=manifest)],subject_provenance=dict(
                status='known',versions=['ASv6.8'],version_sources=[dict(**manifest,field=['subject','prompt_version'])],
                used_inputs=[cases],basis='Exact native subject and source post bindings.')))
        output=self.export()
        lineage=json.loads((output/'experiment.json').read_text())['input']
        self.assertEqual(lineage['subject_prompt_versions'],['ASv6.8'])
        self.assertIs(lineage['generated_subjects_deprecated'],True)
        self.assertIs(lineage['raw_posts_deprecated'],False)

    def test_unresolved_tp_lineage_is_unknown_rather_than_inferred_from_task(self):
        self.fixture(partial=True)
        output=self.export()
        lineage=json.loads((output/'experiment.json').read_text())['input']
        self.assertEqual(lineage['lineage_status'],'unknown')
        self.assertIsNone(lineage['generated_subjects_deprecated'])

    def test_source_hash_mismatch_does_not_publish_any_files(self):
        self.fixture()
        path=self.root/'study/run/output.json'
        path.write_text(path.read_text()+' ')
        with self.assertRaisesRegex(ValueError,'selected source hash mismatch'):
            self.export()
        self.assertFalse((self.root/'publication').exists())

    def test_duplicate_answer_source_cannot_be_counted_as_another_trial(self):
        self.fixture()
        self.change('selection.json',lambda x:x['studies']['early-test']['answers'].append(
            x['studies']['early-test']['answers'][0].copy()))
        with self.assertRaisesRegex(ValueError,'duplicate final answer identity'):
            self.export()

    def test_selected_final_answer_count_is_checked(self):
        self.fixture()
        self.change('selection.json',lambda x:x['studies']['early-test'].update(expected_final_answers=2))
        with self.assertRaisesRegex(ValueError,'final answer count differs'):
            self.export()

    def test_recorded_failure_is_distinct_from_an_unrecorded_case(self):
        self.fixture(partial=True)
        path=self.root/'study/run/results.jsonl'
        rows=[json.loads(line) for line in path.read_text().splitlines()]
        rows.append(dict(status='failed',note_id='case-2',attempt=1,
            manifest_sha256=rows[0]['manifest_sha256'],exit_code=1,
            error='PRIVATE_CANARY',stderr='/private/auth.json'))
        raw=''.join(json.dumps(row)+'\n' for row in rows).encode()
        path.write_bytes(raw)
        self.change('selection.json',lambda spec:spec['studies']['early-test']['receipt_only_answers'][0].update(
            sha256=hashlib.sha256(raw).hexdigest()))
        output=self.export()
        outcomes={row['prompt_id']:row for row in self.records(output,'results.jsonl')}
        self.assertEqual(outcomes['case-2']['outcome'],'recorded_unsuccessful')
        self.assertEqual(outcomes['case-2']['receipts'][0]['status'],'failed')
        self.assertEqual(outcomes['case-3']['outcome'],'not_recorded')
        self.assertNotIn('PRIVATE_CANARY',''.join(path.read_text() for path in output.iterdir()))

    def test_marked_supplied_post_and_canonical_source_note_remain_distinct(self):
        self.fixture()
        case=self.save('study/cases.json',dict(items=[dict(note_id='source-post',
            note='Tea 0 and coffee.',masked_post='⟦Tea⟧ 0 and coffee.',
            subject='The post names tea.',fragments=[dict(text='Tea',occurrence=1)])]))
        self.change('selection.json',lambda x:x['studies']['early-test']['inputs'].append(case))
        output=self.export()
        original=next(row for row in self.records(output,'inputs.jsonl') if row['type']=='saved_input')
        self.assertEqual(original['data']['items'][0]['note'],'Tea 0 and coffee.')
        self.assertEqual(original['data']['items'][0]['masked_post'],'⟦Tea⟧ 0 and coffee.')

    def test_setup_subjects_validate_used_inputs_without_publishing_unused_inventory(self):
        self.fixture()
        manifest=self.save('setup/run/manifest.json',dict(schema_version=1,subject=dict(
            prompt_version='ASv6.8',prompt_sha256='a'*64,model='saved-model'),
            subject_input_normalization_version='saved-v1'))
        setup=self.save('setup/run/output.json',dict(schema_version=1,manifest_sha256=manifest['sha256'],
            notes=[dict(note_id='note-one',text='Original post.',subjects=[
                dict(source_index=0,text='Used meaning'),dict(source_index=1,text='UNUSED_SUBJECT_CANARY')])]))
        cases=self.save('study/selection.json',dict(selection_rule='Use this one item.',
            previous_note_ids=['UNUSED_POST_CANARY'],exclusion_source_files=['UNUSED_PATH_CANARY'],
            items=[dict(note_id='note-one',source_index=0,subject='Used meaning',note='Original post.')]))
        self.change('selection.json',lambda x:x['studies']['early-test'].update(
            setup_outputs=[dict(**setup,manifest=manifest)],inputs=[cases]))
        output=self.export()
        self.assertEqual(len(self.records(output,'answers.jsonl')),1)
        published=''.join(path.read_text() for path in output.iterdir())
        self.assertNotIn('UNUSED_SUBJECT_CANARY',published)
        self.assertNotIn('UNUSED_POST_CANARY',published)
        self.assertNotIn('UNUSED_PATH_CANARY',published)

    def test_setup_join_validates_original_post_context(self):
        self.fixture()
        manifest=self.save('setup/manifest.json',dict(schema_version=1))
        setup=self.save('setup/output.json',dict(schema_version=1,manifest_sha256=manifest['sha256'],
            notes=[dict(note_id='note-one',text='Actual original post.',subjects=[
                dict(source_index=0,text='Used meaning')])]))
        cases=self.save('study/cases.json',dict(items=[dict(note_id='note-one',source_index=0,
            subject='Used meaning',note='Different source context.')]))
        self.change('selection.json',lambda x:x['studies']['early-test'].update(
            setup_outputs=[dict(**setup,manifest=manifest)],inputs=[cases]))
        with self.assertRaisesRegex(ValueError,'selected post differs'):
            self.export()

    def test_reused_baseline_snapshot_must_equal_its_original_bound_source(self):
        self.fixture()
        baseline=dict(schema_version=1,manifest_sha256='a'*64,notes=[dict(note_id='original',
            text='Original post.',subjects=[dict(source_index=0,text='Original meaning')])])
        source=self.save('baseline/output.json',baseline)
        snapshot=self.save('study/baseline-snapshot.json',dict(schema_version=1,
            source_path='baseline/output.json',source_sha256=source['sha256'],output={
                **baseline,'notes':[]}))
        self.change('selection.json',lambda x:x['studies']['early-test'].update(
            baseline_references=[dict(**snapshot,source=source)]))
        with self.assertRaisesRegex(ValueError,'baseline snapshot differs'):
            self.export()

    def test_user_review_and_assistant_interpretation_remain_separate(self):
        self.fixture()
        review=self.save('study/human-review.json',dict(
            user_review=dict(item_id='M09-medium-trial3',outcome='rejected'),
            assistant_application=dict(trials=[1,2],judgment='Apply the same scope interpretation.'),
            occurrence_ambiguity='unresolved'))
        self.change('selection.json',lambda x:x['studies']['early-test']['records'].append(
            dict(**review,role='user_review')))
        output=self.export()
        data=self.records(output,'judgments.jsonl')[0]['data']
        self.assertEqual(data['user_review']['outcome'],'rejected')
        self.assertEqual(data['assistant_application']['trials'],[1,2])
        self.assertEqual(data['occurrence_ambiguity'],'unresolved')

    def review_fixture(self):
        self.fixture()
        batch_value=dict(schema_version=1,batch_id='original',items=[dict(item_id='case-0',
            note_id='original-post',subject='The post names tea.',note='Tea 0 and coffee.',
            fragments=[dict(text='Tea',occurrence=1)])])
        batch=self.save('study/review-batch.json',batch_value)
        compact=lambda value:json.dumps(value,ensure_ascii=False,separators=(',',':')).encode()
        session=dict(schema_version=1,batch_sha256=hashlib.sha256(compact(batch_value)).hexdigest(),
            decisions={'case-0':dict(outcome='approved',comment='')})
        state=dict(schema_version=1,state_sha256=hashlib.sha256(compact(session)).hexdigest(),session=session)
        binding=self.save('study/review-state.json',state)
        review=self.save('study/review-evidence.json',dict(v3=state,scope='Original batch only.'))
        self.change('selection.json',lambda x:x['studies']['early-test'].update(
            review_sessions=[dict(**binding,batch=batch,answer_sources=['study/run/output.json'])],
            records=[dict(**review,role='prior_user_review')],
            review_snapshot_references=[dict(source=review,field=['v3'],session=binding,batch=batch)]))
        return batch,binding

    def test_original_review_decisions_are_minimal_and_embedded_snapshot_is_a_reference(self):
        self.review_fixture()
        output=self.export()
        judgments=self.records(output,'judgments.jsonl')
        decisions=[row for row in judgments if row.get('type')=='user_decision']
        self.assertEqual(len(decisions),1)
        self.assertEqual(decisions[0]['outcome'],'approved')
        self.assertEqual(decisions[0]['item_id'],'case-0')
        self.assertNotIn('session',decisions[0])
        reference=next(row for row in judgments if row.get('role')=='prior_user_review')['data']['v3']
        self.assertEqual(reference['type'],'review_snapshot_reference')
        self.assertNotIn('decisions',reference)

    def test_review_state_hash_mismatch_is_rejected(self):
        self.review_fixture()
        self.change('study/review-state.json',lambda x:x.update(state_sha256='f'*64))
        with self.assertRaisesRegex(ValueError,'review state hash'):
            self.export()

    def test_recorded_display_permutation_does_not_reorder_original_raw_answer(self):
        self.review_fixture()
        raw=json.dumps(['Tea','coffee','and'])
        self.change('study/run/output.json',lambda x:x['responses'][0].update(response=raw))
        self.change('study/run/results.jsonl',lambda x:x.update(response=raw,final_output_raw=raw,
            final_output_sha256=hashlib.sha256(raw.encode()).hexdigest()))
        fragments=[dict(text=text,occurrence=1) for text in ['Tea','and','coffee']]
        self.change('study/review-batch.json',lambda x:x['items'][0].update(fragments=fragments))
        batch=json.loads((self.root/'study/review-batch.json').read_text())
        compact=lambda value:json.dumps(value,ensure_ascii=False,separators=(',',':')).encode()
        state=json.loads((self.root/'study/review-state.json').read_text())
        state['session']['batch_sha256']=hashlib.sha256(compact(batch)).hexdigest()
        state['state_sha256']=hashlib.sha256(compact(state['session'])).hexdigest()
        self.change('study/review-state.json',lambda x:x.update(state))
        self.change('study/review-evidence.json',lambda x:x.update(v3=state))
        preparation=self.save('study/review-preparation.json',dict(items=[dict(item_id='case-0',
            generated_fragment_numbers_in_display_order=[1,3,2],
            generated_fragments=['Tea','coffee','and'],display_fragments=fragments)]))
        self.change('selection.json',lambda x:x['studies']['early-test']['review_sessions'][0].update(
            preparation=preparation))
        output=self.export()
        self.assertEqual(self.records(output,'answers.jsonl')[0]['raw_response'],raw)
        decision=next(row for row in self.records(output,'judgments.jsonl') if row.get('type')=='user_decision')
        self.assertEqual(decision['display_fragment_numbers'],[1,3,2])


if __name__ == '__main__':
    unittest.main()
