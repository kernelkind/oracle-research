"""Historical profiles use the source-bound offline publication path."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


def atomic_fixture(root):
    def write(name, value):
        path = root/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False)+'\n')
        return path
    def digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()
    inputs = write('study/input.json', dict(schema_version=1,
        notes=[dict(note_id='post-one', text='Tea is warm.')]))
    registry = write('study/prompts.json', {'ASv6.9': 'List subjects.'})
    config = write('study/config.json', dict(schema_version=1,
        input_path='input.json', subject=dict(prompt_registry_path='prompts.json',
            prompt_version='ASv6.9', model='saved-model', reasoning_effort='low')))
    schema = dict(type='object', properties={'subjects': dict(type='array',
                  items={'type':'string'})}, required=['subjects'])
    canonical = lambda v: (json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode()
    manifest = write('study/run/manifest.json', dict(schema_version=1,
        mode='atomic_subject_generation', input_sha256=digest(inputs),
        subject_envelope_version='xml-post-v1',
        subject_input_normalization_version='remove-long-ascii-nip19-identifiers-v2',
        wrapper_sha256='a'*64, codex_version='0.153.0',
        subject=dict(prompt_version='ASv6.9', prompt='List subjects.',
            prompt_sha256=hashlib.sha256(b'List subjects.').hexdigest(),
            prompt_registry_sha256=digest(registry), model='saved-model',
            reasoning_effort='low', response_schema=schema,
            response_schema_sha256=hashlib.sha256(canonical(schema)).hexdigest())))
    raw = '{"subjects":["Tea"]}'
    receipt = write('study/run/results.jsonl', dict(schema_version=1, stage='subject',
        status='succeeded', attempt=1, note_id='post-one', manifest_sha256=digest(manifest),
        model='saved-model', reasoning_effort='low', wrapper_sha256='a'*64,
        prompt_sha256=hashlib.sha256(b'List subjects.\n\n<post>\nTea is warm.\n</post>').hexdigest(),
        response_schema_sha256=hashlib.sha256(canonical(schema)).hexdigest(),
        final_output_raw=raw, final_output_sha256=hashlib.sha256(raw.encode()).hexdigest(),
        response=['Tea'], usage=dict(input_tokens=10, output_tokens=3),
        argv=['/private/account'], stderr='PRIVATE_RUNTIME'))
    output = write('study/run/output.json', dict(schema_version=1,
        manifest_sha256=digest(manifest), notes=[dict(note_id='post-one',
            text='Tea is warm.', subjects=[dict(source_index=0,text='Tea')])]))
    paths = [inputs,registry,config,manifest,receipt,output]
    selection = dict(profile='atomic', runs=[dict(output='study/run/output.json',
        manifest='study/run/manifest.json', receipt='study/run/results.jsonl',
        input='study/input.json', registry='study/prompts.json', config='study/config.json', trial=1)],
        validation_sources=[dict(path=p.relative_to(root).as_posix(),sha256=digest(p)) for p in paths],
        records=[], parameters=[], dependencies=[])
    spec = write('selection.json', dict(schema_version=1, studies={'atomic-test':selection}))
    return spec, selection, raw


class HistoricalStudyPublicationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def test_common_publisher_exports_a_real_atomic_profile_without_transport(self):
        from sse_multivector.historical_study_publication import export_results
        spec, _, raw = atomic_fixture(self.root)
        output = self.root/'published'
        result = export_results(self.root,spec,'atomic-test',output)
        self.assertEqual(Path(result['output']),output)
        answers = [json.loads(s) for s in (output/'answers.jsonl').read_text().splitlines()]
        self.assertEqual(answers[0]['output'],raw)
        self.assertEqual(answers[0]['note_id'],'post-one')
        self.assertNotIn('PRIVATE_RUNTIME',''.join(p.read_text() for p in output.iterdir()))
        self.assertNotIn('/private/account',''.join(p.read_text() for p in output.iterdir()))

    def test_unchanged_refresh_keeps_all_bytes_and_mtimes(self):
        from sse_multivector.historical_study_publication import export_results
        spec, _, _ = atomic_fixture(self.root)
        output = self.root/'published'
        export_results(self.root,spec,'atomic-test',output)
        before = {p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in output.iterdir()}
        export_results(self.root,spec,'atomic-test',output)
        self.assertEqual(before,{p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in output.iterdir()})

    def test_hash_mismatch_fails_before_destination_exists(self):
        from sse_multivector.historical_study_publication import export_results
        spec, _, _ = atomic_fixture(self.root)
        (self.root/'study/input.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'hash mismatch'):
            export_results(self.root,spec,'atomic-test',self.root/'published')
        self.assertFalse((self.root/'published').exists())

    def test_source_change_during_staging_preserves_previous_publication(self):
        from sse_multivector.historical_study_publication import export_results, Sources
        spec, _, _ = atomic_fixture(self.root)
        output = self.root/'published'
        export_results(self.root,spec,'atomic-test',output)
        before = {p.name:p.read_bytes() for p in output.iterdir()}
        original = Sources.raw
        changed = False
        def mutate(sources,path):
            nonlocal changed
            raw = original(sources,path)
            if path == 'study/input.json' and not changed:
                changed = True
                (self.root/path).write_bytes(raw+b' ')
            return raw
        with patch.object(Sources,'raw',mutate):
            with self.assertRaisesRegex(ValueError,'changed during export'):
                export_results(self.root,spec,'atomic-test',output)
        self.assertEqual(before,{p.name:p.read_bytes() for p in output.iterdir()})

    def test_declared_moved_file_symlink_is_verified_and_preserved(self):
        from sse_multivector.historical_study_publication import export_results
        spec, _, _ = atomic_fixture(self.root)
        with tempfile.TemporaryDirectory() as outside:
            path=self.root/'study/input.json'; raw=path.read_bytes()
            moved=Path(outside)/'input.json'; moved.write_bytes(raw)
            path.unlink(); path.symlink_to(moved)
            export_results(self.root,spec,'atomic-test',self.root/'published')
            self.assertTrue(path.is_symlink())
            self.assertEqual(moved.read_bytes(),raw)

    def test_missing_or_unsafe_selection_and_overlapping_destination_fail(self):
        from sse_multivector.historical_study_publication import export_results
        spec, _, _ = atomic_fixture(self.root)
        with self.assertRaisesRegex(ValueError,'not explicitly selected'):
            export_results(self.root,spec,'missing',self.root/'published')
        with self.assertRaisesRegex(ValueError,'overlaps'):
            export_results(self.root,spec,'atomic-test',self.root/'study')
        saved=json.loads(spec.read_text())
        saved['studies']['atomic-test']['validation_sources'][0]['path']='../escape.json'
        spec.write_text(json.dumps(saved))
        with self.assertRaisesRegex(ValueError,'repository-relative'):
            export_results(self.root,spec,'atomic-test',self.root/'published')

    def test_sources_and_selected_spec_are_never_changed(self):
        from sse_multivector.historical_study_publication import export_results
        spec, _, _ = atomic_fixture(self.root)
        before={p:(p.read_bytes(),p.stat().st_mtime_ns) for p in self.root.rglob('*') if p.is_file()}
        export_results(self.root,spec,'atomic-test',self.root/'published')
        self.assertEqual(before,{p:(p.read_bytes(),p.stat().st_mtime_ns) for p in before})


if __name__ == '__main__':
    unittest.main()
