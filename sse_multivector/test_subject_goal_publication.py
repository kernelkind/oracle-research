"""Source-bound historical subject evidence uses the production exporter."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest


class SubjectGoalPublicationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / 'source'
        self.output = self.root / 'publication'

    def write(self, name, value, raw=False):
        path = self.source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        data = value.encode() if raw else (json.dumps(value) + '\n').encode()
        path.write_bytes(data)
        return {'path': name, 'sha256': hashlib.sha256(data).hexdigest()}

    def export(self, selection):
        from .historical_study_publication import export_results
        spec = self.root / 'selection.json'
        spec.write_text(json.dumps({'schema_version': 1, 'studies': {
            'subject-fixture': {'profile': 'subject-goal', **selection}}}))
        return export_results(self.source, spec, 'subject-fixture', self.output)

    def rows(self, name):
        return [json.loads(line) for line in (self.output / name).read_text().splitlines()]

    def fixture(self, raw=False):
        inputs = self.write('input.json', {'notes': [
            {'note_id': 'post-1', 'id': 'N1', 'text': 'Tea and coffee.', 'origin': 'synthetic'}]})
        manifest = {'model': 'saved-model', 'reasoning_effort': 'low',
                    'auth_file': '/private/account/auth.json SECRET'}
        if raw:
            manifest['prompts'] = [{'prompt_id': 'N1-t1',
                'text': 'List subjects.\n<post>\nExample.\n</post>\n<post>\nTea and coffee.\n</post>'}]
            answer = {'responses': [{'prompt_id': 'N1-t1', 'response': '{"subjects":["Tea","Coffee"]}'}]}
        else:
            manifest.update(input_sha256=inputs['sha256'], subject={
                'prompt_version': 'ASv6.12', 'prompt': 'List subjects.',
                'prompt_sha256': hashlib.sha256(b'List subjects.').hexdigest(),
                'model': 'saved-model', 'reasoning_effort': 'low'})
            answer = {'notes': [{'note_id': 'post-1', 'text': 'Tea and coffee.',
                'subjects': [{'source_index': 0, 'text': 'Tea'}]}]}
        frozen = self.write('run/manifest.json', manifest)
        output = self.write('run/output.json', {'manifest_sha256': frozen['sha256'], **answer})
        binding = {**output, 'manifest': frozen, 'input': inputs}
        review = self.write('review.json', {'reviewer': 'assistant; no new user decisions',
            'versions': {'ASv6.12': {'coverage': {'tea': 0, 'coffee': 1}}},
            'current_review_decisions': ['An assistant correction.'],
            'outputs': [{'source_result': '/home/private/oracle-mvp/run/output.json',
                         'definite_errors': ['Coffee is absent.']}],
            'auth_file': '/private/account/auth.json SECRET'})
        return {'answers': [binding], 'records': [{**review, 'role': 'assessment'}],
                'inputs': [inputs], 'parameters': [], 'status': 'historical'}

    def test_parsed_answers_dynamic_reviews_and_unknown_actor_are_preserved(self):
        self.export(self.fixture())
        row = self.rows('answers.jsonl')[0]
        self.assertEqual(row['subjects'], [{'source_index': 0, 'text': 'Tea'}])
        self.assertEqual(row['raw_status'], 'not_saved_in_selected_source')
        self.assertNotIn('raw', row)
        review = self.rows('judgments.jsonl')[0]
        self.assertEqual(review['data']['versions']['ASv6.12']['coverage'], {'tea': 0, 'coffee': 1})
        self.assertEqual(review['actor'], {'kind': 'assistant', 'recorded': 'assistant; no new user decisions'})
        serialized = '\n'.join(p.read_text() for p in self.output.iterdir() if p.is_file())
        self.assertNotIn('/private/account', serialized)
        self.assertNotIn('/home/private', serialized)
        self.assertNotIn('SECRET', serialized)
        self.assertTrue(any(row.get('origin') == 'synthetic' for row in self.rows('inputs.jsonl')))

    def test_raw_answers_last_post_template_and_source_identity(self):
        self.export(self.fixture(raw=True))
        row = self.rows('answers.jsonl')[0]
        self.assertEqual(row['raw'], '{"subjects":["Tea","Coffee"]}')
        self.assertEqual(row['note_id'], 'post-1')
        prompts = [r for r in self.rows('inputs.jsonl') if r['kind'] == 'prompt']
        self.assertIn('<post>\nExample.\n</post>', prompts[0]['before_post'])
        self.assertNotIn('Tea and coffee.', prompts[0]['before_post'])

    def test_wrong_manifest_and_input_joins_fail_without_publication(self):
        selection = self.fixture()
        selection['answers'][0]['input'] = self.write('wrong.json', {'notes': [
            {'note_id': 'other', 'text': 'Unrelated.'}]})
        with self.assertRaisesRegex(ValueError, 'input.*hash|input.*binding'):
            self.export(selection)
        self.assertFalse(self.output.exists())

    def test_review_only_result_does_not_invent_model_answers_or_user_approval(self):
        correction = self.write('correction.json', {
            'previous_authority': 'Assistant judgment, not a user-approved example.',
            'previous_judgment': 'accepted', 'corrected_judgment': 'error',
            'totals_after_all_recorded_corrections': {'accepted': 0, 'error': 1}})
        self.export({'answers': [], 'inputs': [], 'parameters': [],
                     'records': [{**correction, 'role': 'correction_overlay'}],
                     'status': 'review_only'})
        self.assertEqual(self.rows('answers.jsonl'), [])
        review = self.rows('judgments.jsonl')[0]
        self.assertEqual(review['actor']['kind'], 'unknown')
        self.assertEqual(review['data']['corrected_judgment'], 'error')

    def test_legacy_receipt_recovers_exact_raw_and_verifies_rendered_request(self):
        from . import generation_history as history
        selection = self.fixture()
        binding = selection['answers'][0]
        raw = '{ "subjects": [ "Tea" ] }'
        rendered = history._render_subject_prompt('List subjects.', history.Note('post-1', 'Tea and coffee.'))
        receipt = {'status': 'succeeded', 'note_id': 'post-1',
            'manifest_sha256': binding['manifest']['sha256'],
            'prompt_sha256': hashlib.sha256(rendered.encode()).hexdigest(),
            'final_output_raw': raw, 'final_output_sha256': hashlib.sha256(raw.encode()).hexdigest(),
            'stderr': '/private/account/auth.json SECRET'}
        binding['receipts'] = self.write('run/results.jsonl', json.dumps(receipt)+'\n', raw=True)
        self.export(selection)
        self.assertEqual(self.rows('answers.jsonl')[0]['raw'], raw)
        (self.source/'run/results.jsonl').write_text(json.dumps({**receipt, 'prompt_sha256': '0'*64})+'\n')
        binding['receipts']['sha256'] = hashlib.sha256((self.source/'run/results.jsonl').read_bytes()).hexdigest()
        self.output = self.root/'invalid-publication'
        with self.assertRaisesRegex(ValueError, 'rendered.*prompt|prompt.*binding'):
            self.export(selection)

    def test_normalized_raw_post_retains_original_source_and_synthetic_identity(self):
        selection = self.fixture(raw=True)
        source = self.write('input.json', {'source_type': 'synthetic', 'id': 'N1',
            'note_id': 'post-1', 'text': 'Tea and coffee. nostr:npub1'+'q'*60})
        selection['inputs'] = [source]
        selection['answers'][0]['input'] = source
        # Preserve whitespace exactly: removing the identifier leaves its preceding space.
        manifest = json.loads((self.source/'run/manifest.json').read_text())
        manifest['prompts'][0]['text'] = 'List subjects.\n<post>\nTea and coffee. \n</post>'
        frozen = self.write('run/manifest.json', manifest)
        selection['answers'][0]['manifest'] = frozen
        output = json.loads((self.source/'run/output.json').read_text())
        selection['answers'][0].update(self.write('run/output.json', {**output, 'manifest_sha256': frozen['sha256']}))
        self.export(selection)
        row = self.rows('answers.jsonl')[0]
        self.assertEqual(row['note_id'], 'post-1')
        post = next(r for r in self.rows('inputs.jsonl') if r['kind'] == 'post')
        self.assertEqual(post['source_text'], 'Tea and coffee. nostr:npub1'+'q'*60)
        self.assertEqual(post['origin'], 'synthetic')

    def test_raw_receipt_config_bindings_and_unknown_lineage(self):
        selection = self.fixture(raw=True)
        binding = selection['answers'][0]
        manifest = json.loads((self.source/'run/manifest.json').read_text())
        config = self.write('config.json', {'prompts': manifest['prompts'], 'model': 'saved-model'})
        manifest['config_sha256'] = config['sha256']
        frozen = self.write('run/manifest.json', manifest)
        output = json.loads((self.source/'run/output.json').read_text())
        binding.update(self.write('run/output.json', {**output, 'manifest_sha256': frozen['sha256']}))
        binding.update(manifest=frozen, config=config)
        receipt = {'status': 'succeeded', 'note_id': 'N1-t1',
            'manifest_sha256': frozen['sha256'],
            'prompt_sha256': hashlib.sha256(manifest['prompts'][0]['text'].encode()).hexdigest(),
            'final_output_raw': output['responses'][0]['response'],
            'final_output_sha256': hashlib.sha256(output['responses'][0]['response'].encode()).hexdigest()}
        binding['receipts'] = self.write('run/results.jsonl', json.dumps(receipt)+'\n', raw=True)
        self.export(selection)
        metadata = json.loads((self.output/'experiment.json').read_text())
        self.assertEqual(metadata['subject_provenance']['status'], 'unknown')
        self.output = self.root/'wrong-receipt'
        receipt['final_output_raw'] = 'Unrelated answer'
        binding['receipts'] = self.write('run/results.jsonl', json.dumps(receipt)+'\n', raw=True)
        with self.assertRaisesRegex(ValueError, 'receipt.*binding|receipt.*answer'):
            self.export(selection)

    def test_execution_projection_keeps_measurements_and_drops_transport(self):
        selection = self.fixture()
        record = self.write('execution-review.json', {'reviewer': 'assistant',
            'execution': {'calls': 3, 'input_tokens': 12, 'usage': {'output_tokens': 5},
                          'command': 'provider --token SECRET', 'error': 'SECRET',
                          'conversation_history': ['SECRET']},
            'billing': {'additional_paid_api_spend_cents': 0, 'account': 'SECRET',
                        'route': 'SECRET'},
            'protected_sha256': {'/home/private/oracle-mvp/prompts/SPv1.md': 'a'*64},
            'runtime': {'seconds': 1.2, 'resource_samples': 3, 'thread': 'SECRET'}})
        selection['records'].append({**record, 'role': 'assessment'})
        self.export(selection)
        data = self.rows('judgments.jsonl')[1]['data']
        self.assertEqual(data['execution']['usage'], {'output_tokens': 5})
        self.assertEqual(data['runtime'], {'seconds': 1.2, 'resource_samples': 3})
        self.assertNotIn('SECRET', json.dumps(data))
        self.assertEqual(data['protected_sha256'], {'prompts/SPv1.md': 'a'*64})

    def test_execution_retains_recorded_repeat_method_and_anonymous_counts(self):
        selection = self.fixture()
        method = 'Intentional --repeat; distinct trials, no answer reuse; one user message and no tools.'
        admission = 'Reuse the first scheduled baseline result as its scheduled trial, not an extra call.'
        record = self.write('method-review.json', {'execution': {
            'isolation': method, 'tools': False, 'application_instructions': '',
            'model_tools': False, 'application_system_instructions': '',
            'conversation_history': False, 'history': False, 'one_user_message': True,
            'batches': 3, 'waves': [12, 3], 'admission': admission,
            'unique_workdirs': 6, 'unique_threads': 6,
            'thread_id': 'PRIVATE-THREAD', 'working_directory': '/private/account/work'}})
        selection['records'].append({**record, 'role': 'assessment'})
        private = self.write('private-method.json', {'execution': {
            'unique_workdirs': ['/private/account/work'], 'unique_threads': ['PRIVATE-THREAD'],
            'application_instructions': 'PRIVATE-INSTRUCTIONS',
            'application_system_instructions': 'PRIVATE-SYSTEM-INSTRUCTIONS',
            'history': ['PRIVATE-HISTORY'], 'conversation_history': ['PRIVATE-CONVERSATION'],
            'model_tools': [{'credentials': 'PRIVATE-TOOLS'}],
            'batches': ['PRIVATE-LAUNCHER'], 'waves': [{'path': '/private/account/wave'}],
            'batch': '/private/account/launcher.py',
            'tools': [{'credentials': 'PRIVATE-CREDENTIALS'}]},
            'eligible_notes': [{'text': 'PRIVATE-CANDIDATE'}]})
        selection['records'].append({**private, 'role': 'assessment'})
        self.export(selection)
        rows = self.rows('judgments.jsonl')
        self.assertEqual(rows[1]['data']['execution'], {
            'isolation': method, 'tools': False, 'application_instructions': '',
            'model_tools': False, 'application_system_instructions': '',
            'conversation_history': False, 'history': False, 'one_user_message': True,
            'batches': 3, 'waves': [12, 3], 'admission': admission,
            'unique_workdirs': 6, 'unique_threads': 6})
        self.assertEqual(rows[2]['data']['execution'], {})
        self.assertNotIn('PRIVATE-', json.dumps(rows))

    def test_case_parameters_keep_settings_without_republishing_unused_posts(self):
        selection = self.fixture(raw=True)
        cases = self.write('cases.json', {'prompt_version': 'ASv6.12',
            'eligible_notes': 387,
            'eligible_counts_by_length_band': {'short': 0, 'long': 4},
            'scope': 'One completed case.', 'cases': [
                {'id': 'N1', 'text': 'Tea and coffee.', 'note_id': 'post-1'},
                {'id': 'N2', 'text': 'UNUSED POST'}]})
        selection['inputs'] = [cases]
        selection['parameters'] = [{**cases, 'projection': 'case_settings'}]
        self.export(selection)
        data = self.rows('results.jsonl')[0]['data']
        self.assertEqual(data, {'prompt_version': 'ASv6.12', 'scope': 'One completed case.',
                              'eligible_notes': 387,
                              'eligible_counts_by_length_band': {'short': 0, 'long': 4}})
        self.assertNotIn('UNUSED POST', '\n'.join(path.read_text() for path in self.output.iterdir()))

    def test_review_sampler_binds_reused_answers_without_counting_new_calls(self):
        selection = self.fixture(raw=True)
        binding = selection['answers'].pop()
        selection['reused_answers'] = [{**binding, 'case_id': 'N1-t1', 'note_id': 'post-1'}]
        selection['status'] = 'review_only'
        self.export(selection)
        self.assertEqual(self.rows('answers.jsonl'), [])
        reused = self.rows('results.jsonl')[0]
        self.assertEqual(reused['role'], 'reused_answer_reference')
        self.assertEqual(reused['case_id'], 'N1-t1')
        self.assertEqual(reused['note_id'], 'post-1')
        self.assertEqual(len([r for r in self.rows('inputs.jsonl') if r['kind'] == 'post']), 1)
        self.output = self.root/'wrong-reused-answer'
        selection['reused_answers'][0]['note_id'] = 'wrong-post'
        with self.assertRaisesRegex(ValueError, 'reused.*identity|reused.*binding'):
            self.export(selection)

    def test_mixed_parsed_and_raw_saved_runs_use_the_same_source_posts(self):
        selection = self.fixture()
        frozen = self.write('raw/manifest.json', {'model': 'saved-model', 'prompts': [
            {'prompt_id': 'N1-t2', 'text': 'List subjects.\n<post>\nTea and coffee.\n</post>'}]})
        output = self.write('raw/output.json', {'manifest_sha256': frozen['sha256'],
            'responses': [{'prompt_id': 'N1-t2', 'response': '{"subjects":["Tea"]}'}]})
        selection['answers'].append({**output, 'manifest': frozen})
        self.export(selection)
        self.assertEqual(len(self.rows('answers.jsonl')), 2)
        self.assertEqual({row['run_id'] for row in self.rows('answers.jsonl')},
                         {'run/output.json', 'raw/output.json'})


if __name__ == '__main__':
    unittest.main()
