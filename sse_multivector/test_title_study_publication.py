"""Saved title studies use the production offline publication command."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


CLI = Path(__file__).with_name('experiment.py')


class TitleStudyPublicationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root/'study'
        self.output = self.root/'publication'
        self.spec = self.root/'selection.json'

    def write(self, name, value):
        path = self.source/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False)+'\n')
        return path

    def bound(self, path):
        return dict(path=path.relative_to(self.root).as_posix(),
                    sha256=hashlib.sha256(path.read_bytes()).hexdigest())

    def fixture(self):
        packets = self.write('source-packets.json', dict(packets=[dict(packet='G1',
            instances=[dict(instance='V1', vector_id=1, note_id='post-one',
                            text='Tea is warm.', byte_spans=[[0, 3]], fragments=['Tea']),
                       dict(instance='V2', vector_id=2, note_id='post-one',
                            text='Tea is warm.', byte_spans=[[0, 3]], fragments=['Tea'])])]))
        prompt = 'Summarize these:\n1. “Tea”\n2. “Tea”\nTitle only.'
        config = self.write('call/config.json', dict(schema_version=1,
            model='saved-model', reasoning_effort='low', codex_home='/private/account',
            prompts=[dict(prompt_id='G1', text=prompt)]))
        manifest = self.write('call/run/manifest.json', dict(schema_version=1,
            config_sha256=hashlib.sha256(config.read_bytes()).hexdigest(),
            model='saved-model', reasoning_effort='low', codex_home='/private/account',
            prompts=[dict(prompt_id='G1', text=prompt)]))
        answer = 'Tea'
        template = self.source/'prompt.txt'
        template.write_text('Summarize these:\n{NUMBERED_INSTANCES}\nTitle only.')
        output = self.write('call/run/output.json', dict(schema_version=1,
            manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),
            responses=[dict(prompt_id='G1', response=answer)]))
        self.write('call/run/results.jsonl', dict(status='succeeded', attempt=1,
            manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),
            prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
            final_output_raw=answer, final_output_sha256=hashlib.sha256(answer.encode()).hexdigest(),
            argv=['/private/account'], stdout_jsonl='private runtime log'))
        binding = dict(self.bound(output), input='study/source-packets.json',
                       group='G1', mode='original_order', prompt='test-prompt')
        self.selection = dict(inputs=[self.bound(packets)], answers=[binding],
            prompts=[dict(self.bound(template), id='test-prompt', version='v1')],
            records=[], parameters=[], failed_receipts=[], dependencies=[])
        self.save_spec()
        return answer

    def save_spec(self):
        self.spec.write_text(json.dumps(dict(schema_version=1,
            studies={'study': self.selection}))+'\n')

    def cli(self):
        return subprocess.run([sys.executable, str(CLI), 'export-evaluation-results',
            str(self.source), '--kind', 'title-study', '--spec', str(self.spec),
            '--output', str(self.output)], capture_output=True, text=True)

    def rows(self, name):
        return [json.loads(line) for line in (self.output/name).read_text().splitlines()]

    def test_bound_final_title_and_exact_used_masks_export_without_runtime_data(self):
        answer = self.fixture()
        before = {p.relative_to(self.source): p.read_bytes()
                  for p in self.source.rglob('*') if p.is_file()}
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        titles = self.rows('answers.jsonl')
        self.assertEqual(len(titles), 1)
        self.assertEqual(titles[0]['output'], answer)
        inputs = self.rows('inputs.jsonl')
        self.assertEqual([r['text'] for r in inputs if r['type']=='post'], ['Tea is warm.'])
        group = next(r for r in inputs if r['type']=='group')
        self.assertEqual(len(group['instances']), 2)
        self.assertEqual(group['group'], 'G1')
        self.assertEqual(titles[0]['input_ref'], group['input_sha256'])
        exported = b''.join(p.read_bytes() for p in self.output.iterdir())
        self.assertNotIn(b'/private/account', exported)
        self.assertNotIn(b'private runtime log', exported)
        self.assertEqual(before, {p.relative_to(self.source): p.read_bytes()
                                  for p in self.source.rglob('*') if p.is_file()})

    def test_deduplicated_input_keeps_all_source_instance_origins(self):
        self.fixture()
        self.selection['answers'][0]['mode'] = 'exact_mask_deduplicated'
        self.rebind_request('Summarize these:\n1. “Tea”\nTitle only.')
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        group = next(r for r in self.rows('inputs.jsonl') if r['type']=='group')
        self.assertEqual(len(group['instances']), 1)
        self.assertEqual(group['instances'][0]['source_instances'], ['V1', 'V2'])

    def rebind_request(self, text):
        config_path = self.source/'call/config.json'
        config = json.loads(config_path.read_text()); config['prompts'][0]['text'] = text
        self.write('call/config.json', config)
        manifest_path = self.source/'call/run/manifest.json'
        manifest = json.loads(manifest_path.read_text())
        manifest['prompts'] = config['prompts']
        manifest['config_sha256'] = hashlib.sha256(config_path.read_bytes()).hexdigest()
        self.write('call/run/manifest.json', manifest)
        output = json.loads((self.source/'call/run/output.json').read_text())
        output['manifest_sha256'] = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        self.write('call/run/output.json', output)
        receipt = json.loads((self.source/'call/run/results.jsonl').read_text())
        receipt.update(manifest_sha256=output['manifest_sha256'],
                       prompt_sha256=hashlib.sha256(text.encode()).hexdigest())
        self.write('call/run/results.jsonl', receipt)
        self.selection['answers'][0].update(self.bound(self.source/'call/run/output.json'))
        self.save_spec()

    def test_flat_fragment_condition_preserves_repeated_fragments(self):
        self.fixture()
        template = self.source/'prompt.txt'
        template.write_text('Summarize:\n{FRAGMENTS}')
        self.selection['prompts'][0].update(self.bound(template))
        self.selection['answers'][0]['mode'] = 'flat_fragments'
        self.rebind_request('Summarize:\n“Tea”\n“Tea”')
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_hash_and_mask_mismatches_preserve_previous_publication(self):
        self.fixture()
        self.assertEqual(self.cli().returncode, 0)
        before = {p.name: p.read_bytes() for p in self.output.iterdir()}
        self.write('call/run/output.json', dict(responses=[]))
        result = self.cli()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('selected source hash', result.stderr)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.output.iterdir()})

    def test_declared_hashtag_condition_preserves_original_masks(self):
        self.fixture()
        packets = json.loads((self.source/'source-packets.json').read_text())
        for item in packets['packets'][0]['instances']:
            item.update(text='#Tea is warm.', byte_spans=[[1, 4]])
        self.write('source-packets.json', packets)
        condition = self.write('conditions.json', dict(conditions={
            'restored_hashtags': [['#Tea'], ['#Tea']]}))
        self.selection['inputs'][0].update(self.bound(self.source/'source-packets.json'))
        self.selection['records'] = [dict(self.bound(condition), role='final_comparison')]
        self.selection['answers'][0].update(mode='explicit_saved_condition:restored_hashtags',
            condition_source='study/conditions.json')
        self.rebind_request('Summarize these:\n1. “#Tea”\n2. “#Tea”\nTitle only.')
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        group = next(r for r in self.rows('inputs.jsonl') if r['type']=='group')
        self.assertEqual(group['instances'][0]['fragments'], ['Tea'])
        self.assertEqual(group['supplied_fragments'][0], ['#Tea'])

    def test_reused_answer_dependency_is_bound_without_an_additional_answer(self):
        self.fixture()
        earlier = self.root/'baseline/call'
        shutil.copytree(self.source/'call', earlier)
        self.selection['dependencies'] = [dict(self.selection['answers'][0],
            **self.bound(earlier/'run/output.json'))]
        self.save_spec()
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(self.rows('answers.jsonl')), 1)
        metadata = json.loads((self.output/'experiment.json').read_text())
        self.assertEqual(len(metadata['answer_dependencies']), 1)
        self.assertEqual(metadata['answer_dependencies'][0]['source_path'],
                         'baseline/call/run/output.json')

    def test_failed_attempt_has_no_answer_or_invented_zero_usage(self):
        self.fixture()
        failed = self.root/'study/failed'
        shutil.copytree(self.source/'call', failed)
        (failed/'run/output.json').unlink()
        receipt = json.loads((failed/'run/results.jsonl').read_text())
        receipt.update(status='failed', final_output_raw=None,
                       final_output_sha256=None, usage=None, error='/private/account quota')
        path = self.write('failed/run/results.jsonl', receipt)
        self.selection['failed_receipts'] = [dict(self.selection['answers'][0],
            **self.bound(path))]
        self.save_spec()
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        failures = [row for row in self.rows('results.jsonl') if row.get('type')=='failed_attempt']
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0]['status'], 'failed')
        self.assertIsNone(failures[0]['usage'])
        self.assertEqual(len(self.rows('answers.jsonl')), 1)
        self.assertNotIn('/private/account', (self.output/'results.jsonl').read_text())

    def test_failed_attempt_requires_the_declared_receipt_file_and_hash(self):
        self.fixture()
        receipt = json.loads((self.source/'call/run/results.jsonl').read_text())
        receipt.update(status='failed', final_output_raw=None,
                       final_output_sha256=None, usage=None)
        path = self.write('failed/run/results.jsonl', receipt)
        shutil.copy(self.source/'call/config.json', self.source/'failed/config.json')
        shutil.copy(self.source/'call/run/manifest.json', self.source/'failed/run/manifest.json')
        binding = dict(self.selection['answers'][0], **self.bound(path))
        for declared_path, digest, expected in [
                ('study/failed/run/missing.json', '0' * 64, 'failed receipt must name results.jsonl'),
                (binding['path'], '0' * 64, 'selected source hash')]:
            with self.subTest(declared_path=declared_path):
                self.selection['failed_receipts'] = [dict(binding, path=declared_path, sha256=digest)]
                self.save_spec()
                result = self.cli()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(expected, result.stderr)
                self.assertFalse(self.output.exists())

    def test_unchanged_refresh_preserves_file_bytes_and_mtimes(self):
        self.fixture()
        self.assertEqual(self.cli().returncode, 0)
        before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns)
                  for p in self.output.iterdir()}
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(before, {p.name: (p.read_bytes(), p.stat().st_mtime_ns)
                                  for p in self.output.iterdir()})

    def test_projection_and_input_validation_code_are_bound_to_the_export(self):
        self.fixture()
        self.assertEqual(self.cli().returncode, 0)
        metadata = json.loads((self.output/'experiment.json').read_text())
        for name in ['title_study_publication.py', 'title_study_records.py',
                     'prepare_category_title_inputs.py', 'prompt_study_publication.py']:
            path = Path(__file__).with_name(name)
            self.assertEqual(metadata['exporter_sources'][name],
                             hashlib.sha256(path.read_bytes()).hexdigest())

    def test_invalid_source_mask_cannot_be_published_even_with_updated_source_hash(self):
        self.fixture()
        packets = json.loads((self.source/'source-packets.json').read_text())
        packets['packets'][0]['instances'][0]['byte_spans'] = [[1, 4]]
        self.write('source-packets.json', packets)
        self.selection['inputs'][0].update(self.bound(self.source/'source-packets.json'))
        self.save_spec()
        result = self.cli()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('fragment does not match source byte span', result.stderr)
        self.assertFalse(self.output.exists())

    def test_source_change_while_staging_preserves_previous_publication(self):
        from . import title_study_publication as publisher
        self.fixture()
        self.assertEqual(self.cli().returncode, 0)
        before = {p.name: p.read_bytes() for p in self.output.iterdir()}
        writer = publisher.shared('publication_files')
        original = writer.write_publication

        def mutate(destination, metadata, payloads):
            records = payloads['inputs.jsonl']

            def inputs():
                yield from records
                path = self.source/'source-packets.json'
                path.write_bytes(path.read_bytes()+b' ')

            return original(destination, metadata, {**payloads, 'inputs.jsonl': inputs()})

        with mock.patch.object(writer, 'write_publication', side_effect=mutate):
            with self.assertRaisesRegex(ValueError, 'source changed during export'):
                publisher.export_results(self.source, self.spec, self.output)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.output.iterdir()})


if __name__ == '__main__':
    unittest.main()
