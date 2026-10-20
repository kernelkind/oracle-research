"""Scientific records use the production projection and source joins."""
import hashlib
import json
import unittest

from sse_multivector.title_study_records import project_record


class TitleStudyRecordTests(unittest.TestCase):
    def setUp(self):
        self.source = 'study/comparison.json'
        self.bindings = {self.source: 'a' * 64,
                         'study/calls/X/run/results.jsonl': 'b' * 64,
                         'study/calls/X/run/output.json': 'c' * 64}
        self.answer = dict(call_id='calls/X/run/output.json', prompt_id='X',
                           output='Coffee Beans',
                           output_sha256=hashlib.sha256(b'Coffee Beans').hexdigest(),
                           version='v21', input_ref='group-X',
                           source_path='study/calls/X/run/output.json')

    def project(self, value, role='final_comparison', **overrides):
        return project_record(value, role=role, source=self.source,
                              answers=overrides.get('answers', [self.answer]),
                              bindings=overrides.get('bindings', self.bindings))

    def test_comments_preserve_words_without_inventing_actor_or_approval(self):
        value = dict(schema_version=1, batch_sha256='d' * 64,
                     comments={'S0123456789': dict(assessment_summary='I would approve.',
                                                  comment='A narrower subject.')})
        result = self.project(value, 'recorded_review_comments')
        self.assertEqual(result['actor'], 'unknown')
        self.assertEqual(result['data'], value)
        self.assertEqual(result['source'], dict(path=self.source, sha256='a' * 64))

    def test_nested_trials_baselines_and_saved_output_links_survive(self):
        value = dict(schema_version=1, assessment_author='Main assistant; not user decisions',
                     groups=[dict(group='S0123456789', historical_v12=[dict(
                         trial='trial-1', raw_title='Historical title')],
                         trials=[dict(trial=2, title='Coffee Beans',
                             result_path='/old/repo/sse_multivector/study/calls/X/run/results.jsonl',
                             thread_id='private-thread', assessment='accept')])])
        before = json.dumps(value)
        result = self.project(value)
        group = result['data']['groups'][0]
        self.assertEqual(result['actor'], 'agent')
        self.assertEqual(group['historical_v12'][0]['raw_title'], 'Historical title')
        self.assertEqual(group['trials'][0]['trial'], 2)
        self.assertNotIn('thread_id', group['trials'][0])
        reference = group['trials'][0]['result_path']
        self.assertEqual(reference['source_ref'], 'study/calls/X/run/results.jsonl')
        self.assertEqual(reference['sha256'], 'b' * 64)
        self.assertEqual(reference['answer_refs'][0]['output_sha256'], self.answer['output_sha256'])
        self.assertEqual(json.dumps(value), before)

    def test_reused_selection_and_actual_decision_remain_distinct(self):
        value = dict(schema_version=1, groups=[dict(group='S0123456789',
                     title='Coffee Beans', source='reused',
                     result_path='calls/X/run/output.json',
                     alternative=None, user_approval=dict(item_id='case-1', outcome='approved'))])
        result = self.project(value, 'final_title_selection')['data']['groups'][0]
        self.assertEqual(result['source'], 'reused')
        self.assertEqual(result['user_approval'], value['groups'][0]['user_approval'])
        self.assertIsNone(result['alternative'])

    def test_unknown_scientific_field_fails_instead_of_disappearing(self):
        with self.assertRaisesRegex(ValueError, 'new_scientific_measurement'):
            self.project(dict(groups=[dict(group='S0123456789',
                                           new_scientific_measurement=0.75)]))

    def test_ambiguous_source_suffix_is_not_guessed(self):
        bindings = {self.source: 'a' * 64,
                    'one/run/results.jsonl': 'b' * 64,
                    'two/run/results.jsonl': 'c' * 64}
        with self.assertRaisesRegex(ValueError, 'ambiguous'):
            self.project(dict(results=[dict(result_path='run/results.jsonl')]),
                         bindings=bindings, answers=[])

    def test_unknown_private_source_path_has_explicit_opaque_reference(self):
        original = '/private/account/session.json'
        result = self.project(dict(source_session=original,
                                   source_session_sha256='e' * 64),
                              'recorded_assessments')
        self.assertEqual(result['data']['source_session'], {
            'unresolved_source_path_sha256': hashlib.sha256(original.encode()).hexdigest()})
        self.assertNotIn(original, json.dumps(result))
        self.assertEqual(result['data']['source_session_sha256'], 'e' * 64)

    def test_qualified_missing_file_does_not_join_an_unrelated_basename(self):
        bindings = {self.source: 'a' * 64, 'one/review.json': 'b' * 64,
                    'two/review.json': 'c' * 64}
        result = self.project(dict(source_session='/outside/study/review.json'),
                              'recorded_assessments', bindings=bindings)
        self.assertIn('unresolved_source_path_sha256', result['data']['source_session'])

    def test_draft_parameter_preserves_reference_without_temporary_filename(self):
        original = '/tmp/private-draft-123/prompt.md'
        result = self.project(dict(approved_draft=original), 'study_parameters')
        self.assertEqual(result['data']['approved_draft'], {
            'unresolved_source_path_sha256': hashlib.sha256(original.encode()).hexdigest()})
        self.assertNotIn(original, json.dumps(result))

    def test_input_description_is_scientific_text_rather_than_a_filename(self):
        value = dict(input='Only masks and candidate titles; no prior judgments.')
        self.assertEqual(self.project(value, 'recorded_assessments')['data'], value)

    def test_configuration_object_is_not_treated_as_scientific_data(self):
        with self.assertRaisesRegex(ValueError, 'config'):
            self.project(dict(results=[dict(config={'authorization': 'secret'})]))

    def test_native_observation_branches_remain_complete(self):
        value = dict(observations=[dict(node='S0123456789',
                                        v1=dict(response='Old'), v2=dict(response='New'))],
                     comparison_limit='Small fixed comparison.')
        self.assertEqual(self.project(value)['data'], value)

    def test_scientific_plan_survives_without_execution_or_account_details(self):
        value = dict(schema_version=1, experiment='comparison', question='Does wording help?',
                     hypothesis='The changed instruction may help.', repetitions=2,
                     groups=['S0123456789'], model='saved-model', reasoning_effort='low',
                     execution={'authorization': 'secret', 'codex_home': '/private/account'},
                     billing={'account': 'private'})
        result = self.project(value, 'study_parameters')['data']
        self.assertEqual(result['question'], value['question'])
        self.assertEqual(result['hypothesis'], value['hypothesis'])
        self.assertEqual(result['repetitions'], 2)
        self.assertNotIn('execution', result)
        self.assertNotIn('billing', result)

    def test_saved_prompt_format_metadata_has_hashes_without_rendered_bodies(self):
        value = dict(prompt=dict(fragment_template='“{fragment}”', fragment_order='Original',
                                  numbered_instance_template='{number}. {fragments}'))
        result = self.project(value, 'study_parameters')['data']['prompt']
        self.assertEqual(result['fragment_order'], 'Original')
        self.assertEqual(result['fragment_template'], {
            'template_sha256': hashlib.sha256('“{fragment}”'.encode()).hexdigest()})

    def test_selected_instances_become_reference_only_with_exact_input_proof(self):
        answer = dict(self.answer, input_instances=[dict(instance='V1', note_id='post-one',
                      byte_spans=[[0, 6]], fragments=['coffee'], text='coffee')])
        value = dict(groups=[dict(group='S0123456789', title='Coffee Beans',
                     result_path='calls/X/run/output.json', notes=['post-one'],
                     instances=[dict(instance='V1', fragments=['coffee'])])])
        result = self.project(value, 'final_title_selection', answers=[answer])['data']['groups'][0]
        self.assertNotIn('instances', result)
        self.assertNotIn('notes', result)
        self.assertEqual(result['input_ref'], 'group-X')
        changed = json.loads(json.dumps(value))
        changed['groups'][0]['instances'][0]['fragments'] = ['tea']
        result = self.project(changed, 'final_title_selection', answers=[answer])['data']['groups'][0]
        self.assertEqual(result['instances'][0]['fragments'], ['tea'])
        self.assertNotIn('input_ref', result)


if __name__ == '__main__':
    unittest.main()
