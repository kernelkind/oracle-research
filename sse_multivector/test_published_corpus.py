"""Published starting subjects feed ordinary experiment preparation unchanged."""
import hashlib
import json
from pathlib import Path
import tracemalloc
import unittest

from sse_multivector import test_experiment as fixtures
from sse_multivector import test_hierarchy_generation_v3 as native_fixtures


class PublishedCorpusTests(unittest.TestCase):
    setUp = fixtures.ExperimentTests.setUp
    write = fixtures.ExperimentTests.write
    cli = fixtures.ExperimentTests.cli

    def inputs(self):
        notes = [dict(note_id='one', text='Tea\nwith é and \u2028 separators',
                      origin=dict(prompt_version='ASv6.100', receipt='PRIVATE RECEIPT'),
                      subjects=[dict(number='1', subject='Tea', context='Drinking tea'),
                                dict(number='1.1', subject='Green tea', context='Green tea drink')]),
                 dict(note_id='empty', text='No usable subjects', subjects=[],
                      origin=dict(prompt_version='ASv6.100')),
                 dict(note_id='unused', text='Unused post', subjects=[])]
        self.write('corpus.json', dict(schema_version=1, notes=notes))
        (self.root/'ids.txt').write_text('empty\none\n')
        (self.root/'posts.jsonl').write_text(''.join(
            json.dumps({k: n[k] for k in ('note_id', 'text')}, ensure_ascii=False)+'\n'
            for n in notes))
        return notes

    def export(self):
        return self.cli('export-hierarchy-inputs', 'corpus.json', '--note-ids', 'ids.txt',
                        '--output', 'published')

    def test_cli_retains_full_subject_trees_and_order_without_private_origins(self):
        notes = self.inputs()
        self.export()
        bundle = self.root/'published'
        with (bundle/'subjects.jsonl').open() as stream:
            rows = [json.loads(line) for line in stream]
        self.assertEqual([r['note_id'] for r in rows], ['empty', 'one'])
        self.assertEqual(rows[1]['subjects'], notes[0]['subjects'])
        self.assertEqual(rows[1]['origin'], dict(prompt_version='ASv6.100'))
        self.assertEqual(rows[1]['text_sha256'],
                         hashlib.sha256(notes[0]['text'].encode()).hexdigest())
        self.assertNotIn(b'PRIVATE RECEIPT', (bundle/'subjects.jsonl').read_bytes())
        self.assertNotIn(b'Unused post', (bundle/'subjects.jsonl').read_bytes())
        self.cli('prepare-corpus', '--posts', 'posts.jsonl', '--note-ids', 'ids.txt',
                 '--subjects', 'published', '--output', 'collected.json')
        collected = json.loads((self.root/'collected.json').read_bytes())['notes']
        self.assertEqual([n['note_id'] for n in collected], ['empty', 'one'])
        self.assertEqual(collected[1]['text'], notes[0]['text'])
        self.assertEqual(collected[1]['subjects'], notes[0]['subjects'])
        self.assertEqual(collected[0]['subjects'], [])

    def test_post_only_corpus_uses_the_native_subject_adapter(self):
        notes = self.inputs()
        self.cli('prepare-corpus', '--posts', 'posts.jsonl', '--note-ids', 'ids.txt',
                 '--output', 'collected.json')
        source = json.loads((self.root/'collected.json').read_bytes())
        self.assertTrue(all(set(n) == {'note_id', 'text'} for n in source['notes']))
        spec = json.loads(self.spec.read_text())
        spec['dataset'] = dict(adapter='subjects', path='collected.json')
        self.write('spec.json', spec)
        self.cli('prepare', 'AS', '--spec', 'spec.json', '--only', 'one')
        case = json.loads(self.cli('show', 'AS', '--case', 'one').stdout)
        self.assertEqual(case['inputs']['POST'], notes[0]['text'])
        self.assertIsNone(case['output'])
        self.assertEqual(fixtures.ExperimentTests.calls(self), [])

    def test_wrong_post_text_missing_posts_and_tampered_subjects_leave_no_output(self):
        self.inputs()
        self.export()
        original = (self.root/'posts.jsonl').read_bytes()
        for posts, message in [
                (b'{"note_id":"one","text":"changed"}\n'
                 b'{"note_id":"empty","text":"No usable subjects"}\n', 'text'),
                (b'{"note_id":"empty","text":"No usable subjects"}\n', 'missing'),
                (original+original, 'duplicate')]:
            with self.subTest(message=message):
                (self.root/'posts.jsonl').write_bytes(posts)
                result = self.cli('prepare-corpus', '--posts', 'posts.jsonl', '--note-ids',
                    'ids.txt', '--subjects', 'published', '--output', 'collected.json', ok=False)
                self.assertIn(message, result.stderr)
                self.assertFalse((self.root/'collected.json').exists())
        (self.root/'posts.jsonl').write_bytes(original)
        with (self.root/'published/subjects.jsonl').open('ab') as stream:
            stream.write(b'{}\n')
        result = self.cli('prepare-corpus', '--posts', 'posts.jsonl', '--note-ids', 'ids.txt',
            '--subjects', 'published', '--output', 'collected.json', ok=False)
        self.assertIn('hash', result.stderr)
        self.assertFalse((self.root/'collected.json').exists())

    def test_existing_outputs_and_invalid_selection_are_refused(self):
        self.inputs()
        self.export()
        bundle = self.root/'published'
        before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in bundle.iterdir()}
        self.export()
        self.assertEqual(before, {p.name: (p.read_bytes(), p.stat().st_mtime_ns)
                                  for p in bundle.iterdir()})
        output = self.root/'collected.json'
        output.write_text('KEEP')
        self.cli('prepare-corpus', '--posts', 'posts.jsonl', '--note-ids', 'ids.txt',
                 '--output', output, ok=False)
        self.assertEqual(output.read_text(), 'KEEP')
        for selection in ('one\none\n', 'unknown\n', ''):
            with self.subTest(selection=selection):
                (self.root/'ids.txt').write_text(selection)
                self.export_bad_selection()
                self.assertEqual(before, {p.name: (p.read_bytes(), p.stat().st_mtime_ns)
                                          for p in bundle.iterdir()})

    def export_bad_selection(self):
        self.cli('export-hierarchy-inputs', 'corpus.json', '--note-ids', 'ids.txt',
                 '--output', 'published', ok=False)

    def test_large_post_selection_does_not_accumulate_text_in_memory(self):
        from sse_multivector.published_corpus import prepare_corpus

        count = 400
        with (self.root/'posts.jsonl').open('w') as stream:
            for index in range(count):
                stream.write(json.dumps(dict(note_id=str(index), text='é' * 32768))+'\n')
        (self.root/'ids.txt').write_text(''.join(str(i)+'\n' for i in reversed(range(count))))
        tracemalloc.start()
        try:
            prepare_corpus(self.root/'posts.jsonl', self.root/'ids.txt', self.root/'result.json')
            _, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        self.assertLess(peak, 6*1024*1024, 'selected post text accumulated in memory')
        notes = json.loads((self.root/'result.json').read_bytes())['notes']
        self.assertEqual([n['note_id'] for n in notes], list(map(str, reversed(range(count)))))

    def test_native_bootstrap_requests_match_with_child_subjects_preserved(self):
        native = native_fixtures.HierarchyGenerationV3Tests('runTest')
        native.setUp()
        self.addCleanup(native.doCleanups)
        spec = native.prepare_v41(count=3)
        config = json.loads(spec.read_text())
        config.pop('bootstrap_hierarchy', None)
        config['generation_policy'] = 'hierarchy-generation-v5.3'
        corpus_path = (spec.parent/config['corpus']).resolve()
        corpus = json.loads(corpus_path.read_bytes())
        for note in corpus['notes']:
            note['subjects'].append(dict(number='1.999', subject='Child topic', context='Child evidence'))
            note['origin'] = dict(prompt_version='ASv6.100')
        corpus_path.write_text(json.dumps(corpus))
        spec.write_text(json.dumps(config))
        before_calls = native.calls()
        native.cli('prepare-hierarchy', 'original', '--spec', spec)
        ids = native.root/'ids.txt'
        ids.write_text(''.join(n+'\n' for n in config['note_ids']))
        native.cli('export-hierarchy-inputs', corpus_path, '--note-ids', ids,
                   '--output', 'published')
        native.cli('prepare-corpus', '--posts', corpus_path, '--note-ids', ids,
                   '--subjects', 'published', '--output', 'collected.json')
        config['corpus'] = 'collected.json'
        native.write('reproduction.json', config)
        corpus_path.unlink()
        native.cli('prepare-hierarchy', 'reproduction', '--spec', 'reproduction.json')
        states = [json.loads((native.root/name/'state.json').read_bytes())
                  for name in ('original', 'reproduction')]
        self.assertEqual(states[0]['originals'], states[1]['originals'])
        self.assertEqual(states[0]['note_ids'], states[1]['note_ids'])
        self.assertEqual(states[0]['experiments'][0]['inputs'],
                         states[1]['experiments'][0]['inputs'])
        self.assertEqual(native.calls(), before_calls)
