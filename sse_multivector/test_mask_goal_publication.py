"""Historical mask studies use the shared offline publication entry point."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest


class MaskGoalPublicationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def save(self, name, value):
        path = self.root/name
        path.parent.mkdir(parents=True,exist_ok=True)
        raw = (json.dumps(value)+'\n').encode()
        path.write_bytes(raw)
        return dict(path=name,sha256=hashlib.sha256(raw).hexdigest())

    def fixture(self):
        prompt = 'Choose exact text.\n\n<post>\nTea and coffee.\n</post>\n\n<subject>\nTea\n</subject>\n'
        config = self.save('study/config.json',dict(schema_version=1,
            auth_file='/private/auth.json',model='saved-model',reasoning_effort='low',
            provider='saved-provider',prompts=[dict(prompt_id='M1',text=prompt)]))
        manifest = self.save('study/run/manifest.json',dict(schema_version=1,
            config_sha256=config['sha256'],auth_file='/private/auth.json',
            model='saved-model',reasoning_effort='low',provider='saved-provider',
            prompts=[dict(prompt_id='M1',text=prompt)]))
        answer = '["Tea"]'
        output = self.save('study/run/output.json',dict(schema_version=1,
            manifest_sha256=manifest['sha256'],responses=[dict(prompt_id='M1',response=answer)]))
        receipt = self.save('study/run/results.jsonl',dict(status='succeeded',attempt=1,
            manifest_sha256=manifest['sha256'],prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
            response=answer,final_output_raw=answer,final_output_sha256=hashlib.sha256(answer.encode()).hexdigest(),
            stdout_json={'secret':'PRIVATE_CANARY'},argv=['/private/runner'],request_sha256='a'*64))
        review = self.save('study/review.json',dict(schema_version=1,status='complete',
            assessment_author='assistant',decision='Keep the earlier judgment as recorded.',
            usage={'cost_usd':0.01},outputs=[dict(id='M1',judgment='accepted')]))
        correction = self.save('study/correction.json',dict(schema_version=1,
            earlier_judgment='accepted',current_judgment='unresolved',
            reason_for_reopening='The subject may be broader than the selected words.'))
        plan = self.save('study/plan.json',dict(schema_version=1,question='Does the mask select tea?',
            auth_file='/private/auth.json',execution={'command':'PRIVATE_CANARY'},
            approval={'status':'approved','scope':'preparation only'}))
        spec = dict(schema_version=1,studies={'mask-test':dict(profile='mask-goal',directory='study',
            answers=[dict(**output,manifest=manifest,configuration=config,receipt=receipt,role='mask_answer')],
            inputs=[],parameters=[plan],records=[dict(**review,role='assessment'),
                                               dict(**correction,role='correction')])})
        self.save('selection.json',spec)
        return self.root/'selection.json'

    def records(self, output, name):
        return [json.loads(line) for line in (output/name).read_text().splitlines()]

    def change(self, name, change):
        value = json.loads((self.root/name).read_text())
        change(value)
        binding = self.save(name,value)
        spec = json.loads((self.root/'selection.json').read_text())
        def update(value):
            if isinstance(value,dict):
                if value.get('path')==name and 'sha256' in value:
                    value['sha256'] = binding['sha256']
                for item in value.values():update(item)
            elif isinstance(value,list):
                for item in value:update(item)
        update(spec)
        self.save('selection.json',spec)
        return binding

    def replace_prompt(self, prompt):
        config = self.change('study/config.json',lambda x:x['prompts'][0].update(text=prompt))
        def manifest(x):
            x['prompts'][0]['text']=prompt
            x['config_sha256']=config['sha256']
        bound = self.change('study/run/manifest.json',manifest)
        self.change('study/run/output.json',lambda x:x.update(manifest_sha256=bound['sha256']))
        self.change('study/run/results.jsonl',lambda x:x.update(manifest_sha256=bound['sha256'],
                    prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest()))

    def export(self):
        from sse_multivector.historical_study_publication import export_results
        output = self.root/'publication'
        export_results(self.root,self.root/'selection.json','mask-test',output)
        return output

    def test_preserves_answers_separate_correction_and_scientific_usage(self):
        from sse_multivector.historical_study_publication import export_results
        spec = self.fixture()
        output = self.root/'publication'

        export_results(self.root,spec,'mask-test',output)

        answers = self.records(output,'answers.jsonl')
        self.assertEqual(answers[0]['raw_response'],'["Tea"]')
        inputs = self.records(output,'inputs.jsonl')
        case = next(row for row in inputs if row['type']=='prompt_input')
        self.assertEqual(case['variables']['post'],'Tea and coffee.')
        judgments = self.records(output,'judgments.jsonl')
        self.assertEqual([row['role'] for row in judgments],['assessment','correction'])
        self.assertEqual(judgments[0]['data']['usage'],{'cost_usd':0.01})
        self.assertEqual(judgments[1]['data']['earlier_judgment'],'accepted')
        self.assertEqual(judgments[1]['data']['current_judgment'],'unresolved')
        published = ''.join(path.read_text() for path in output.iterdir())
        self.assertNotIn('/private/',published)
        self.assertNotIn('PRIVATE_CANARY',published)

    def test_operational_billing_transport_and_auth_notes_not_published_as_parameters(self):
        self.fixture()
        self.change('study/plan.json',lambda x:x.update(
            billing={'account_id':'PRIVATE_CANARY'},transport={'auth_directory':'PRIVATE_CANARY'},
            authentication_note='PRIVATE_CANARY'))
        output = self.export()
        published = ''.join(path.read_text() for path in output.iterdir())
        self.assertNotIn('PRIVATE_CANARY',published)

    def test_scientific_execution_and_transport_methods_preserved_without_launch_credentials(self):
        self.fixture()
        execution = dict(provider='saved-provider',model='saved-model',reasoning='low',
            prompt_rendering='Replace {POST} with the complete original note; no normalization.',
            application_instructions='',schema=None,tools=[],prior_messages=0,
            reuse_policy='Duplicate hierarchy entries are not independent trials.',
            retries=0,maximum_concurrency=2,memory_per_job='2 GiB',
            auth_file='/private/auth.json',accounts={'selected':'PRIVATE_CANARY'},
            launcher={'command':'PRIVATE_CANARY'})
        transport = 'Current subscription runner, one independent user message; no history.'
        self.change('study/plan.json',lambda x:x.update(execution=execution,transport=transport,
            resources='One local CPU FP32 run; no model downloads.',
            cost='Subscription only; no additional monetary commitment.'))
        output = self.export()
        plan = next(row for row in self.records(output,'inputs.jsonl') if row['type']=='study_parameters')
        expected = {key:value for key,value in execution.items() if key not in ('auth_file','accounts','launcher')}
        self.assertEqual(plan['data']['execution'],expected)
        self.assertEqual(plan['data']['transport'],transport)
        self.assertEqual(plan['data']['resources'],'One local CPU FP32 run; no model downloads.')
        self.assertEqual(plan['data']['cost'],'Subscription only; no additional monetary commitment.')
        self.assertNotIn('PRIVATE_CANARY',''.join(path.read_text() for path in output.iterdir()))

    def test_examples_remain_in_template_and_exact_supplied_entities_stay_separate(self):
        self.fixture()
        prompt = '<example><post>\nExample post.\n</post><subject>\nExample subject\n</subject></example>\n'
        prompt += '<post>\nTea &amp; coffee.\n</post>\n<subject>\nTea\n</subject>'
        self.replace_prompt(prompt)
        canonical = self.save('study/cases.json',[dict(id='M1',text='Tea & coffee.',subject='Tea')])
        self.change('selection.json',lambda x:x['studies']['mask-test']['inputs'].append(canonical))
        output = self.export()
        inputs = self.records(output,'inputs.jsonl')
        template = next(row for row in inputs if row['type']=='prompt_template')
        supplied = next(row for row in inputs if row['type']=='prompt_input')
        self.assertIn('Example post.',template['text'])
        self.assertNotIn('Tea &amp; coffee.',template['text'])
        self.assertEqual(supplied['variables']['post'],'Tea &amp; coffee.')
        self.assertEqual(next(row for row in inputs if row['type']=='saved_input')['data'][0]['text'],
                         'Tea & coffee.')

    def test_subject_input_is_not_counted_as_mask_generation(self):
        self.fixture()
        self.replace_prompt('Give subjects.\n<post>\nTea and coffee.\n</post>')
        output = self.export()
        self.assertEqual(self.records(output,'answers.jsonl')[0]['role'],'subject_input')
        counts = json.loads((output/'experiment.json').read_text())['counts']
        self.assertEqual(counts['subject_input'],1)
        self.assertEqual(counts['mask_answer'],0)

    def test_comparison_and_position_tasks_keep_their_actual_supplied_inputs(self):
        for prompt,role,fields in [(
            'Compare.\n<subject>\nTea\n</subject>\n<candidate_A>\n⟦Tea⟧ and coffee.\n</candidate_A>'
            '\n<candidate_B>\nTea and ⟦coffee⟧.\n</candidate_B>',
            'mask_comparison_answer',{'subject','candidate_A','candidate_B'}),(
            'Find boundaries.\n<marked_original>\n⟦Tea⟧\n</marked_original>'
            '\n<indexed_original>\n[0]T[1]e[2]a[3]\n</indexed_original>',
            'position_answer',{'marked_original','indexed_original'})]:
            with self.subTest(role=role):
                self.fixture()
                self.replace_prompt(prompt)
                output = self.root/role
                from sse_multivector.historical_study_publication import export_results
                export_results(self.root,self.root/'selection.json','mask-test',output)
                self.assertEqual(self.records(output,'answers.jsonl')[0]['role'],role)
                supplied = next(row for row in self.records(output,'inputs.jsonl') if row['type']=='prompt_input')
                self.assertEqual(set(supplied['variables']),fields)

    def test_reused_receipt_keeps_exact_original_binding(self):
        self.fixture()
        self.change('study/run/results.jsonl',lambda x:x.update(execution='cross_run_reuse',
            reused_from=dict(manifest_sha256='b'*64,result_line=7,result_sha256='c'*64,
                results_path=str(self.root/'prior/run/results.jsonl'))))
        output = self.export()
        receipt = self.records(output,'answers.jsonl')[0]['receipts'][0]
        self.assertEqual(receipt['reused_from']['results_path'],'prior/run/results.jsonl')
        self.assertEqual(receipt['reused_from']['result_line'],7)
        self.assertEqual(json.loads((output/'experiment.json').read_text())['counts']['reused_receipt_rows'],1)

    def test_unknown_decision_and_later_user_claim_remain_as_recorded(self):
        self.fixture()
        self.change('study/review.json',lambda x:x.update(user_review='pending',
            user_decision={'M1':'uncertain'},recorded_claim='A user accepted the earlier fragment.'))
        output = self.export()
        data = self.records(output,'judgments.jsonl')[0]['data']
        self.assertEqual(data['user_review'],'pending')
        self.assertEqual(data['user_decision'],{'M1':'uncertain'})
        self.assertEqual(data['recorded_claim'],'A user accepted the earlier fragment.')

    def test_recorded_user_authorization_in_scientific_plan_is_preserved(self):
        self.fixture()
        text = 'User agreed to a small test of the character-boundary format.'
        self.change('study/plan.json',lambda x:x.update(authorization=text))
        output = self.export()
        plan = next(row for row in self.records(output,'inputs.jsonl') if row['type']=='study_parameters')
        self.assertEqual(plan['data']['authorization'],text)

    def test_source_and_receipt_mismatches_fail_before_publication(self):
        self.fixture()
        path = self.root/'study/run/output.json'
        path.write_text(path.read_text()+' ')
        with self.assertRaisesRegex(ValueError,'selected source hash mismatch'):
            self.export()
        self.assertFalse((self.root/'publication').exists())
        self.fixture()
        self.change('study/run/results.jsonl',lambda x:x.update(final_output_sha256='d'*64))
        with self.assertRaisesRegex(ValueError,'receipt response hash differs'):
            self.export()

    def test_scientific_path_reference_converted_without_rewriting_raw_source_text(self):
        self.fixture()
        self.change('study/review.json',lambda x:x.update(reason='See '+str(self.root/'study/run/output.json'),
            source_text='A source post may literally mention /tmp/public/example.'))
        output = self.export()
        data = self.records(output,'judgments.jsonl')[0]['data']
        self.assertEqual(data['reason'],'See study/run/output.json')
        self.assertEqual(data['source_text'],'A source post may literally mention /tmp/public/example.')

    def test_frozen_hash_map_keys_are_portable_without_losing_hashes(self):
        self.fixture()
        inputs = self.save('study/inputs.json',dict(protected_sha256={
            str(self.root/'study/encoder.py'):'e'*64}))
        self.change('selection.json',lambda x:x['studies']['mask-test']['inputs'].append(inputs))
        output = self.export()
        record = next(row for row in self.records(output,'inputs.jsonl') if row['type']=='saved_input')
        self.assertEqual(record['data']['protected_sha256'],{'study/encoder.py':'e'*64})

    def test_failed_attempt_has_status_counters_and_no_authentication_diagnostics(self):
        spec = self.fixture()
        status = self.save('study/status.json',dict(status='blocked_authentication',
            model_requests_sent=0,responses_generated=0,retries=0,
            authentication_check={'command':'PRIVATE_CANARY'},diagnosis='/private/auth.json'))
        selection = json.loads(spec.read_text())['studies']['mask-test']
        answer = selection['answers'][0]
        failed = dict(status=status,manifest=answer['manifest'],configuration=answer['configuration'],
                      receipt=answer['receipt'])
        self.change('selection.json',lambda x:x['studies']['mask-test'].update(answers=[],failed_attempt=failed))
        output = self.export()
        self.assertEqual(self.records(output,'answers.jsonl'),[])
        failure = next(row for row in self.records(output,'results.jsonl') if row['role']=='failed_attempt')
        self.assertEqual(failure['data']['status'],'blocked_authentication')
        self.assertEqual(failure['data']['responses_generated'],0)
        self.assertNotIn('PRIVATE_CANARY',''.join(path.read_text() for path in output.iterdir()))


if __name__ == '__main__':
    unittest.main()
