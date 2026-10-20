"""Saved frontier evidence is exported through the shared historical API."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest


class FrontierStudyPublicationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def save(self, path, value):
        raw = (json.dumps(value, ensure_ascii=False) + '\n').encode()
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        return dict(path=path, sha256=hashlib.sha256(raw).hexdigest())

    def fixture(self):
        summary = self.save('study/summary.json', dict(status='interim',
            semantic_quality_assessed=False, successful_responses=0,
            usage=dict(cost=0, cached_tokens=None),
            methods=dict(reasoning_requested='high', tools=[], retry_count=2),
            auth_file='/private/ACCOUNT_CANARY/auth.json'))
        selection = dict(profile='frontier-study', directory='study',
                         records=[dict(**summary, role='measurement')])
        self.save('selection.json', dict(schema_version=1, studies={'frontier-test': selection}))

    def export(self):
        from sse_multivector.historical_study_publication import export_results
        destination = self.root / 'publication'
        export_results(self.root, self.root / 'selection.json', 'frontier-test', destination)
        return destination

    def rows(self, output, filename):
        return [json.loads(line) for line in (output / filename).read_text().splitlines()]

    def test_scientific_measurements_keep_zero_null_and_method_fields(self):
        self.fixture()
        output = self.export()
        record = self.rows(output, 'results.jsonl')[0]
        self.assertEqual(record['data']['usage'], dict(cost=0, cached_tokens=None))
        self.assertIs(record['data']['semantic_quality_assessed'], False)
        self.assertEqual(record['data']['methods'],
                         dict(reasoning_requested='high', tools=[], retry_count=2))
        self.assertNotIn('ACCOUNT_CANARY', ''.join(p.read_text() for p in output.iterdir()))

    def select(self, **fields):
        self.save('selection.json', dict(schema_version=1, studies={'frontier-test':
            dict(profile='frontier-study', directory='study', **fields)}))

    def native(self, *, selected=False):
        text = 'Identify subjects.\n<post>\nTea & coffee.\n</post>'
        prompts = [dict(prompt_id='P'+str(i), text=text+'\n'+str(i)) for i in range(3)]
        config = self.save('study/config.json', dict(model='saved-model', prompts=prompts))
        manifest = self.save('study/run/manifest.json', dict(schema_version=1,
            config_sha256=config['sha256'], model='saved-model', prompts=prompts,
            max_output_tokens=None, codex_version='saved-version',
            isolation=dict(system_instructions='Exact scientific instruction.',
                           fresh_process_per_job=True, history=[], tools=[]),
            auth_file='/private/ACCOUNT_CANARY/auth.json'))
        raw = '{ "subjects": [] }\n'
        rows = [dict(manifest_sha256=manifest['sha256'], note_id='P0',
                     prompt_sha256=hashlib.sha256(prompts[0]['text'].encode()).hexdigest(),
                     final_output_raw=raw, final_output_sha256=hashlib.sha256(raw.encode()).hexdigest(),
                     status='succeeded', attempt=1, usage=dict(cost=0), argv=['ACCOUNT_CANARY'],
                     model_result=dict(valid=True,http_attempts=2,stop_reason='stop',
                        response_model='observed-model',request=dict(headers=dict(authorization='ACCOUNT_CANARY'),
                            body=dict(model='saved-model',messages=[dict(role='user',content=prompts[0]['text'])],
                                      reasoning=dict(effort='high'))))),
                dict(manifest_sha256=manifest['sha256'], note_id='P1',
                     prompt_sha256=hashlib.sha256(prompts[1]['text'].encode()).hexdigest(),
                     final_output_raw='partial', final_output_sha256=hashlib.sha256(b'partial').hexdigest(),
                     status='failed', attempt=1, error='Recorded stream failure.',
                     retry_reason='retry after failed attempt')]
        path = self.root/'study/run/results.jsonl'
        path.write_text(''.join(json.dumps(row)+'\n' for row in rows))
        receipt = dict(path='study/run/results.jsonl', sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        run = dict(manifest=manifest, configuration=config, receipt=receipt, task='subject')
        if selected:
            imported=self.save('study/imported/experiment.json',dict(plan=dict(imported=True,
                manifest_sha256=manifest['sha256'],run_directory='study/run')))
            run['already_selected'] = dict(publication='prompts/previous', manifest_sha256=manifest['sha256'],
                imported_experiment=imported,
                answers={'P0':dict(case_id='native-imported-id', raw_response_sha256=hashlib.sha256(raw.encode()).hexdigest())})
        self.select(native_runs=[run])
        return raw

    def test_native_partial_preserves_exact_raw_and_unknown_input_outcome(self):
        raw = self.native()
        output = self.export()
        self.assertEqual(self.rows(output,'answers.jsonl')[0]['raw_response'],raw)
        results = self.rows(output,'results.jsonl')
        self.assertEqual(results[0]['partial_response'],'partial')
        self.assertEqual(results[0]['retry_reason'],'retry after failed attempt')
        self.assertEqual(results[1]['outcome'],'not_recorded')
        controls = next(r['controls'] for r in self.rows(output,'inputs.jsonl') if r['type']=='run_parameters')
        self.assertEqual(controls['isolation']['system_instructions'],'Exact scientific instruction.')
        self.assertEqual(controls['isolation']['tools'],[])
        self.assertIsNone(controls['max_output_tokens'])
        receipt=self.rows(output,'answers.jsonl')[0]['receipt']
        self.assertEqual(receipt['model_result']['http_attempts'],2)
        self.assertEqual(receipt['model_result']['response_model'],'observed-model')
        self.assertNotIn('ACCOUNT_CANARY',''.join(p.read_text() for p in output.iterdir()))

    def test_current_and_unknown_subject_lineages_are_not_marked_deprecated(self):
        for versions,unknown,expected in ((['ASv6.100'],False,False),([],True,None),
                (['ASv6.101'],True,None),(['ASv6.48','ASv6.100'],True,True)):
            with self.subTest(versions=versions,unknown=unknown):
                value=self.save('study/source.json',dict(status='saved'))
                self.select(records=[dict(**value,role='measurement')],subject_versions=versions,
                            subject_lineage_unknown=unknown)
                output=self.root/('lineage-'+str(len(versions))+str(unknown)+str(expected))
                from sse_multivector.historical_study_publication import export_results
                export_results(self.root,self.root/'selection.json','frontier-test',output)
                self.assertIs(json.loads((output/'experiment.json').read_text())['input']
                              ['generated_subjects_deprecated'],expected)

    def test_http_cells_in_same_source_have_distinct_ids_and_separate_completion_validity(self):
        binding=self.save('study/http.json',dict(results=[dict(raw_text='not JSON',valid=False,
            stop_reason='stop'),dict(raw_text='truncated',valid=False,stop_reason='length')]))
        self.select(http_results=[dict(**binding,field=['results',i],task='subject') for i in range(2)])
        output=self.export()
        answers=self.rows(output,'answers.jsonl')
        self.assertEqual(len({row['answer_id'] for row in answers}),2)
        self.assertEqual([r['status'] for r in answers],['completed','saved_partial'])
        results=self.rows(output,'results.jsonl')
        self.assertIs(results[0]['data']['valid'],False)

    def test_duplicate_http_selection_is_rejected(self):
        binding=self.save('study/http.json',dict(raw_text='saved',valid=True,stop_reason='stop'))
        self.select(http_results=[binding,binding])
        with self.assertRaisesRegex(ValueError,'duplicate selected'):
            self.export()

    def test_review_hierarchy_is_bound_to_original_post_and_answer(self):
        text='Identify.\n<post>\nTea.\n</post>'
        manifest=self.save('study/run/manifest.json',dict(prompts=[dict(prompt_id='N1',text=text)]))
        raw=json.dumps(dict(subjects=[dict(number='1',subject='Tea',context='Tea.')]))
        answer=self.save('study/run/output.json',dict(responses=[dict(prompt_id='N1',response=raw)]))
        packet=self.save('study/review.json',dict(notes=[dict(id='N1',title='Source',text='Tea.',
            results=[dict(model='saved',output='1  Tea',comment='Recorded assessment.')])]))
        self.select(review_packets=[dict(**packet,cells=[dict(case_id='N1',model='saved',
            view='hierarchy',answer=dict(**answer,format='output',case_id='N1',manifest=manifest))])])
        output=self.export()
        review=self.rows(output,'judgments.jsonl')[0]
        self.assertEqual(review['answer_ref']['source']['sha256'],answer['sha256'])
        self.assertEqual(review['answer_ref']['raw_response_sha256'],hashlib.sha256(raw.encode()).hexdigest())
        self.assertNotIn('output',review)

    def test_wrong_model_answer_is_rejected_even_for_the_same_post(self):
        manifest=self.save('study/manifest.json',dict(prompts=[dict(prompt_id='N1',
            text='Identify.\n<post>\nTea.\n</post>')]))
        answer=self.save('study/wrong-model.json',dict(responses=[dict(prompt_id='N1',
            response=json.dumps(dict(subjects=[dict(number='1',subject='Coffee',context='Tea.')])))]))
        packet=self.save('study/review.json',dict(notes=[dict(id='N1',title='Source',text='Tea.',
            results=[dict(model='saved',output='1  Tea',comment='Recorded assessment.')])]))
        self.select(review_packets=[dict(**packet,cells=[dict(case_id='N1',model='saved',
            view='hierarchy',answer=dict(**answer,format='output',case_id='N1',manifest=manifest))])])
        with self.assertRaisesRegex(ValueError,'review display differs'):
            self.export()

    def test_review_preserves_recorded_full_and_shortened_supplied_post(self):
        text='Identify.\n<post>\nTea.\n</post>'
        manifest=self.save('study/run/manifest.json',dict(prompts=[dict(prompt_id='N1',text=text)]))
        raw=json.dumps(dict(subjects=[dict(number='1',subject='Tea',context='Tea.')]))
        answer=self.save('study/run/output.json',dict(responses=[dict(prompt_id='N1',response=raw)]))
        selection=self.save('study/input-selection.json',dict(text='Tea. A longer original.',input_text='Tea.'))
        packet=self.save('study/review.json',dict(notes=[dict(id='N1',title='Source',text='Tea. A longer original.',
            results=[dict(model='saved',output='1  Tea',comment='Recorded assessment.')])]))
        self.select(review_packets=[dict(**packet,cells=[dict(case_id='N1',model='saved',view='hierarchy',
            answer=dict(**answer,format='output',case_id='N1',manifest=manifest,
                canonical_post=dict(**selection,field=['text']),supplied_post=dict(**selection,field=['input_text'])))])])
        output=self.export()
        ref=self.rows(output,'judgments.jsonl')[0]['answer_ref']
        self.assertNotEqual(ref['canonical_post_sha256'],ref['supplied_post_sha256'])

    def test_blinded_packet_mapping_is_checked_against_final_mask_and_input(self):
        final=self.save('study/results.json',dict(mask_cases=[dict(id='C1',text='Tea.',subject='Tea',
            reference_spans=[[0,3]])],mask={},sp={}))
        cases=self.save('study/sp-cases.json',[])
        mapping=self.save('study/blind-map.json',{'S1':dict(arm='astra-low',case_id='C1',kind='mask')})
        packet=self.save('study/packet.json',dict(items=[dict(slot='S1',kind='mask',post='Tea.',
            subject='Tea',answer='⟦WRONG⟧.',rubric=dict(verdicts=['acceptable']))]))
        self.select(blind_packets=[dict(**packet,mapping=mapping,results=final,sp_cases=cases)])
        with self.assertRaisesRegex(ValueError,'blinded packet answer differs'):
            self.export()

    def test_response_api_text_parts_retain_native_order_and_exact_supplied_text(self):
        binding=self.save('study/http.json',dict(raw_text='{}',stop_reason='stop',valid=True,
            request=dict(body=dict(input=[dict(type='message',role='user',content=[
                dict(type='input_text',text='Identify.\n<post>\nTea &amp; coffee.\n</post>')])]))))
        self.select(http_results=[binding])
        output=self.export()
        supplied=next(r for r in self.rows(output,'inputs.jsonl') if r['type']=='prompt_input')
        self.assertEqual(supplied['variables']['post'],'Tea &amp; coffee.')
        parameters=next(r for r in self.rows(output,'inputs.jsonl') if r['type']=='request_parameters')
        self.assertEqual(parameters['data']['message_context'][0]['parts'][0]['type'],'input_text')

    def test_provider_execution_ids_are_removed_without_losing_case_ids(self):
        value=self.save('study/activity.json',dict(request_id='REQUEST_CANARY',
            generation_id='GENERATION_CANARY',note_id='source-note',case_id='C1',
            provider_responses=[dict(id='PROVIDER_CANARY',provider='saved-provider',latency=0)],
            usage=dict(cost=0)))
        self.select(records=[dict(**value,role='measurement')])
        output=self.export()
        data=self.rows(output,'results.jsonl')[0]['data']
        self.assertEqual(data['note_id'],'source-note')
        self.assertEqual(data['provider_responses'],[dict(provider='saved-provider',latency=0)])
        self.assertNotIn('CANARY',''.join(p.read_text() for p in output.iterdir()))

    def test_recorded_assistant_attribution_requires_its_source_evidence(self):
        packet=self.save('study/review.json',dict(notes=[dict(id='N1',title='Source',text='Tea.',
            results=[dict(model='saved',output='No output.',comment='A recorded comment.')])]))
        proof=self.save('study/assessment.json',dict(method='Separate assistant-comment pane.'))
        self.select(review_packets=[dict(**packet,actor=dict(kind='assistant',source=proof,
            evidence='assistant-comment pane'),cells=[dict(case_id='N1',model='saved',
            view='recorded_outcome',display_sha256=hashlib.sha256(b'No output.').hexdigest())])])
        output=self.export()
        self.assertEqual(self.rows(output,'judgments.jsonl')[0]['actor']['kind'],'assistant')

    def test_only_selected_used_posts_preserve_canonical_and_case_identities(self):
        source=self.save('study/notes.json',dict(notes=[dict(id='N1',note_id='canonical-source',text='Tea.'),
            dict(id='UNUSED',note_id='unused-source',text='Unused private inventory.')]))
        self.select(posts=[dict(**source,cases=['N1'])])
        output=self.export()
        posts=[r for r in self.rows(output,'inputs.jsonl') if r['type']=='source_post']
        self.assertEqual(len(posts),1)
        self.assertEqual(posts[0]['data'],dict(id='N1',note_id='canonical-source',text='Tea.'))
        self.assertNotIn('Unused private inventory.',''.join(p.read_text() for p in output.iterdir()))

    def test_existing_native_publication_is_a_reference_without_new_raw_copy(self):
        self.native(selected=True)
        output = self.export()
        self.assertEqual(self.rows(output,'answers.jsonl'),[])
        ref = next(r for r in self.rows(output,'results.jsonl') if r['type']=='existing_answer_reference')
        self.assertEqual(ref['published_case_id'],'native-imported-id')
        self.assertNotIn('raw_response',ref)

    def test_existing_publication_import_must_bind_the_same_native_run(self):
        self.native(selected=True)
        selection=json.loads((self.root/'selection.json').read_text())
        run=selection['studies']['frontier-test']['native_runs'][0]
        run['already_selected']['imported_experiment']=self.save('study/imported/experiment.json',
            dict(plan=dict(imported=True,manifest_sha256='0'*64,run_directory='study/run')))
        self.save('selection.json',selection)
        with self.assertRaisesRegex(ValueError,'existing import source differs'):
            self.export()

    def test_http_nested_native_result_preserves_measurements_and_factors_request(self):
        body = dict(model='requested-model',messages=[
            dict(role='system',content='Exact isolation control.'),
            dict(role='user',content='Identify subjects.\n<post>\nTea & coffee.\n</post>')],
            reasoning=dict(effort='high'),tools=[],response_format=dict(type='json_object'))
        digest=hashlib.sha256(json.dumps(body,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
        result = dict(raw_text=' {"subjects":[]}\n',valid=True,model='observed-model',
            request_body_sha256=digest,request=dict(headers=dict(authorization='ACCOUNT_CANARY'),body=body),
            timing=dict(max_event_gap_ms=300000,event_trace=[dict(secret='ACCOUNT_CANARY')]),
            usage=dict(cost=0,completion_tokens_details=dict(reasoning_tokens=None)),
            response_id='ACCOUNT_CANARY')
        binding=self.save('study/compatibility.json',dict(results=[dict(label='saved',exit_code=0,result=result)]))
        self.select(http_results=[dict(**binding,field=['results',0,'result'],task='subject')])
        output=self.export()
        self.assertEqual(self.rows(output,'answers.jsonl')[0]['raw_response'],' {"subjects":[]}\n')
        measurement=self.rows(output,'results.jsonl')[0]['data']
        self.assertEqual(measurement['timing'],dict(max_event_gap_ms=300000))
        self.assertEqual(measurement['usage']['cost'],0)
        self.assertEqual(self.rows(output,'results.jsonl')[0]['context'][0]['data']['label'],'saved')
        supplied=next(r for r in self.rows(output,'inputs.jsonl') if r['type']=='request_parameters')
        self.assertEqual(supplied['data']['message_context'][0]['content'],'Exact isolation control.')
        self.assertNotIn('ACCOUNT_CANARY',''.join(p.read_text() for p in output.iterdir()))

    def test_review_cells_are_comments_with_native_outcomes_unchanged(self):
        packet=self.save('study/review.json',dict(schema_version=1,title='Comparison',notes=[
            dict(id='N1',title='Source',text='Tea.',results=[dict(model='saved model',
                output='(not completed)',comment='No semantic quality verdict.')])]))
        self.select(review_packets=[dict(**packet,cells=[dict(case_id='N1',model='saved model',
            view='recorded_outcome',display_sha256=hashlib.sha256(b'(not completed)').hexdigest())])])
        output=self.export()
        self.assertEqual(self.rows(output,'answers.jsonl'),[])
        review=self.rows(output,'judgments.jsonl')[0]
        self.assertEqual(review['comment'],'No semantic quality verdict.')
        self.assertEqual(review['actor'],dict(kind='unknown'))


if __name__ == '__main__':
    unittest.main()
