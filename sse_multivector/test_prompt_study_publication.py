"""Historical prompt studies export through the supported offline CLI."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


CLI = Path(__file__).with_name('experiment.py')


class PromptStudyPublicationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root/'study'
        self.output = self.root/'export'

    def write(self, name, value):
        path = self.source/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value)+'\n')
        return path

    def fixture(self, layout='as28'):
        self.write('input.json', dict(schema_version=1,
            notes=[dict(id='N1', note_id='post-one', text='Tea and coffee.')]))
        template = self.source/'prompts/SPv1.md'
        template.parent.mkdir(parents=True, exist_ok=True)
        template.write_text('List subjects.\n')
        prompt = 'List subjects.\n\n<post>\nTea and coffee.\n</post>'
        self.write('plan.json', dict(schema_version=1, prompts=['SPv1'],
            protected_sha256={'prompts/SPv1.md': hashlib.sha256(template.read_bytes()).hexdigest()},
            execution={'auth_file': '/private/credentials'}))
        self.write('calls.json', [dict(id='N1-sp-t1', note_id='N1',
            version='SPv1', trial=1, config='one/config.json', output='one/run/output.json')])
        self.write('one/config.json', dict(schema_version=1, model='saved-model',
            reasoning_effort='low', auth_file='/private/credentials',
            prompts=[dict(prompt_id='N1-sp-t1', text=prompt)]))
        manifest = self.write('one/run/manifest.json', dict(schema_version=1,
            config_sha256=hashlib.sha256((self.source/'one/config.json').read_bytes()).hexdigest(),
            prompts=[dict(prompt_id='N1-sp-t1', text=prompt)]))
        answer = '{"subjects":[{"context":"Drinks are named.","subject":"Tea"}]}'
        self.write('one/run/output.json', dict(schema_version=1,
            manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),
            responses=[dict(prompt_id='N1-sp-t1', response=answer)]))
        self.write('one/run/results.jsonl', dict(status='succeeded', attempt=1,
            manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),
            prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
            final_output_raw=answer, final_output_sha256=hashlib.sha256(answer.encode()).hexdigest()))
        self.write('review-key.json', [dict(review_id='R1', id='N1-sp-t1',
            note_id='N1', version='SPv1', trial=1)])
        self.write('review-input.json', dict(schema_version=1,
            notes=[dict(id='N1', note_id='post-one', text='Tea and coffee.')],
            outputs=[dict(review_id='R1', note_id='N1', subjects=['Tea'])]))
        self.write('review-judgments.json', dict(schema_version=1,
            reviewer='assistant', outputs=[dict(review_id='R1',
                definite_errors=[], coverage=[dict(probe='Tea', status='present')])]))
        self.write('summary.json', dict(schema_version=1, status='complete',
            calls=1, subjects_reviewed=1, decision='Retain the baseline.',
            auth_file='/private/credentials'))
        if layout in ('as26', 'as27'):
            self.write('calls.json', dict(schema_version=1, calls=[dict(
                id='N1-sp-t1', note='N1', prompt='SPv1', trial=1, config='one/config.json')]))
            key = dict(review_id='R1', id='N1-sp-t1', note='N1', prompt='SPv1', trial=1)
            if layout == 'as26':
                key['raw_sha256'] = hashlib.sha256(answer.encode()).hexdigest()
                self.write('review-key.json', dict(schema_version=1, entries=[key]))
                self.write('review-input.json', dict(schema_version=1, notes=[dict(
                    id='N1', note_id='post-one', text='Tea and coffee.',
                    outputs=[dict(review_id='R1', subjects=['Tea'])])]))
            else:
                self.write('review-key.json', dict(schema_version=1, mapping=[key]))
                self.write('review-input.json', dict(schema_version=1, outputs=[dict(
                    review_id='R1', note='N1', note_id='post-one',
                    text='Tea and coffee.', subjects=['Tea'])]))
        elif layout == 'fresh':
            for name in ('review-key.json', 'review-input.json', 'review-judgments.json'):
                (self.source/name).unlink()
            self.write('review.json', dict(schema_version=1,
                method='Main-assistant semantic review, not independent validation.',
                notes=[dict(id='N1', call_id='N1-sp-t1', subject_count=1,
                    reviewed_subject_indices=[1], fidelity_accepted_subject_indices=[1],
                    definite_error_indices=[], coverage=['Tea is independently named.'],
                    fidelity=['Supported by the complete post.'], caveat='One case only.')]))
        return answer

    def cli(self):
        return subprocess.run([sys.executable, str(CLI), 'export-evaluation-results',
            str(self.source), '--kind', 'prompt-study', '--output', str(self.output)],
            capture_output=True, text=True)

    def rows(self, name):
        return [json.loads(line) for line in (self.output/name).read_text().splitlines()]

    def test_saved_posts_answers_and_assessments_export_without_transport(self):
        answer = self.fixture()
        before = {p.relative_to(self.source): p.read_bytes()
                  for p in self.source.rglob('*') if p.is_file()}
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.rows('inputs.jsonl')[0]['text'], 'Tea and coffee.')
        self.assertEqual(self.rows('answers.jsonl')[0]['output'], answer)
        judgment = self.rows('judgments.jsonl')[0]
        self.assertEqual(judgment['call_id'], 'N1-sp-t1')
        self.assertEqual(judgment['actor'], 'agent')
        self.assertEqual(judgment['assessment']['coverage'][0]['status'], 'present')
        self.assertEqual(self.rows('results.jsonl')[0]['decision'], 'Retain the baseline.')
        exported = b''.join(p.read_bytes() for p in self.output.iterdir())
        self.assertNotIn(b'/private/credentials', exported)
        self.assertNotIn(b'<post>', exported)
        self.assertEqual(before, {p.relative_to(self.source): p.read_bytes()
                         for p in self.source.rglob('*') if p.is_file()})

    def test_all_four_saved_review_layouts_bind_the_same_call(self):
        for layout in ('as26', 'as27', 'as28', 'fresh'):
            with self.subTest(layout=layout):
                self.source = self.root/layout
                self.output = self.root/(layout+'-export')
                self.fixture(layout)
                result = self.cli()
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(self.rows('judgments.jsonl')[0]['call_id'], 'N1-sp-t1')
                self.assertEqual(self.rows('answers.jsonl')[0]['note_id'], 'post-one')

    def test_dynamic_final_measurements_and_predeclared_definitions_are_retained(self):
        self.fixture('as26')
        plan = json.loads((self.source/'plan.json').read_text())
        plan.update(detailed_meanings={'N1': ['Drinks are mentioned.']},
            coverage_probes={'N1': ['Tea']}, additional_predeclared_probes={'N1': ['Coffee']},
            decision='Diagnostic only; no automatic promotion.',
            comparisons='Fresh independent trials, no historical answer substitution.',
            git_head_at_preparation='b'*40,
            notes=[dict(id='N1', note_id='post-one', selection_reason='Positive control.',
                        source='/private/source', fidelity_checks=['Preserve named drinks.'])])
        plan['protected_sha256']['runtime.py'] = 'a'*64
        self.write('plan.json', plan)
        measurements = dict(schema_version=1, by_prompt={'SPv1': dict(outputs=1, subjects=1,
            definite_fidelity_errors=0, coverage={'Tea': dict(present=1, narrower=0, absent=0)})},
            by_version={'SPv1': dict(calls=1, unresolved=0, coverage={'Tea': dict(
                present=1, trials=[dict(note_id='N1', trial=1, review_id='R1',
                                       status='present', subject_indices=[1], reason='Named.')])})},
            notes=[dict(id='N1', note_id='post-one', coverage=[dict(probe='Tea',
                prompts={'SPv1': dict(present=1, partial=0, absent=0,
                    trials=[dict(trial=1, review_id='R1', status='present', subject_indices=[1])])})])],
            other_observation=dict(subject='Drinks', note='N1', predeclared_probe=False,
                independent_entries={'SPv1': 0}, meaning='Broader topic.'),
            auth_file='/private/credentials')
        self.write('summary.json', measurements)
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        published = self.rows('results.jsonl')[0]
        self.assertEqual(published, {k: v for k, v in measurements.items() if k != 'auth_file'})
        metadata = json.loads((self.output/'experiment.json').read_text())
        self.assertEqual(metadata['parameters']['detailed_meanings'], plan['detailed_meanings'])
        self.assertEqual(metadata['parameters']['additional_predeclared_probes'],
                         plan['additional_predeclared_probes'])
        self.assertEqual(metadata['parameters']['comparisons'], plan['comparisons'])
        self.assertEqual(metadata['code']['commit'], 'b'*40)
        self.assertEqual(metadata['code']['frozen_sources']['runtime.py'], 'a'*64)
        self.assertNotIn('/private/', ''.join(p.read_text() for p in self.output.iterdir()))

    def test_shared_interpretations_and_unknown_reviewer_are_preserved(self):
        self.fixture('as27')
        judgment = json.loads((self.source/'review-judgments.json').read_text())
        del judgment['reviewer']
        judgment['scope'] = 'Review style may reveal the condition.'
        judgment['interpretation_notes'] = [dict(review_ids=['R1'], subjects=[1],
            note='This heading names a topic, without asserting an event occurred.')]
        self.write('review-judgments.json', judgment)
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        assessed, interpretation = self.rows('judgments.jsonl')
        self.assertEqual(assessed['actor'], 'unknown')
        self.assertEqual(interpretation['call_ids'], ['N1-sp-t1'])
        self.assertEqual(interpretation['assessment'], dict(subjects=[1],
            note=judgment['interpretation_notes'][0]['note']))

    def test_explicit_user_review_is_distinct_from_agent_review(self):
        self.fixture()
        judgment = json.loads((self.source/'review-judgments.json').read_text())
        judgment['reviewer'] = 'user'
        self.write('review-judgments.json', judgment)
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.rows('judgments.jsonl')[0]['actor'], 'user')
        self.assertNotIn('approved', self.rows('judgments.jsonl')[0])

    def test_unchanged_refresh_preserves_all_bytes_and_mtimes(self):
        self.fixture()
        self.assertEqual(self.cli().returncode, 0)
        before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.output.iterdir()}
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(before, {p.name: (p.read_bytes(), p.stat().st_mtime_ns)
                                 for p in self.output.iterdir()})

    def test_mismatches_leave_no_new_publication_or_damage_to_prior_export(self):
        for failure in ('orphan', 'duplicate', 'subjects', 'post', 'assessment_post', 'manifest', 'config',
                        'request', 'raw_hash', 'missing', 'escape', 'symlink'):
            with self.subTest(failure=failure):
                self.source = self.root/failure
                self.output = self.root/(failure+'-export')
                self.fixture('as26')
                self.assertEqual(self.cli().returncode, 0)
                before = {p.name: p.read_bytes() for p in self.output.iterdir()}
                if failure in ('orphan', 'duplicate', 'raw_hash'):
                    key = json.loads((self.source/'review-key.json').read_text())
                    if failure == 'orphan':key['entries'][0]['id'] = 'not-a-call'
                    elif failure == 'duplicate':key['entries'].append(key['entries'][0])
                    else:key['entries'][0]['raw_sha256'] = '0'*64
                    self.write('review-key.json', key)
                elif failure in ('subjects', 'post'):
                    view = json.loads((self.source/'review-input.json').read_text())
                    if failure == 'subjects':view['notes'][0]['outputs'][0]['subjects'] = ['Different answer']
                    else:view['notes'][0]['text'] = 'A different post.'
                    self.write('review-input.json', view)
                elif failure == 'manifest':
                    output = json.loads((self.source/'one/run/output.json').read_text())
                    output['manifest_sha256'] = '0'*64
                    self.write('one/run/output.json', output)
                elif failure == 'assessment_post':
                    judgment = json.loads((self.source/'review-judgments.json').read_text())
                    judgment['outputs'][0]['note'] = 'another-post'
                    self.write('review-judgments.json', judgment)
                elif failure in ('config', 'request'):
                    config = json.loads((self.source/'one/config.json').read_text())
                    config['model'] = 'mutated-model'
                    if failure == 'request':config['prompts'][0]['text'] += 'Extra instructions.'
                    self.write('one/config.json', config)
                elif failure == 'missing':(self.source/'one/run/results.jsonl').unlink()
                elif failure in ('escape', 'symlink'):
                    calls = json.loads((self.source/'calls.json').read_text())
                    if failure == 'escape':calls['calls'][0]['config'] = '../outside/config.json'
                    else:
                        (self.source/'escape').symlink_to(self.root)
                        calls['calls'][0]['config'] = 'escape/config.json'
                    self.write('calls.json', calls)
                result = self.cli()
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(before, {p.name: p.read_bytes() for p in self.output.iterdir()})

    def test_source_change_during_staging_aborts_before_commit(self):
        from sse_multivector.prompt_study_publication import export_results
        from sse_multivector._runner_bootstrap import shared
        writer = shared('publication_files')
        self.fixture()
        original = writer.write_publication
        def changing_writer(output, metadata, payloads):
            answers = payloads['answers.jsonl']
            def changed_answers():
                yield from answers
                self.write('input.json', dict(notes=[]))
            return original(output, metadata, {**payloads, 'answers.jsonl': changed_answers()})
        with mock.patch.object(writer, 'write_publication', side_effect=changing_writer):
            with self.assertRaisesRegex(ValueError, 'changed during export'):
                export_results(self.source, self.output)
        self.assertFalse(self.output.exists())


if __name__ == '__main__':
    unittest.main()
