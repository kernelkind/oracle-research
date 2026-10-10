"""Prepare source-bound Bootstrap pilot inputs through the production CLI."""
import hashlib
import json
import unittest

from sse_multivector import test_experiment as fixtures


class BootstrapStudentInputTests(unittest.TestCase):
    setUp = fixtures.ExperimentTests.setUp
    write = fixtures.ExperimentTests.write
    cli = fixtures.ExperimentTests.cli
    prepare = fixtures.ExperimentTests.prepare
    show = fixtures.ExperimentTests.show
    calls = fixtures.ExperimentTests.calls

    def source(self):
        posts = [dict(note_id=f'{i:064x}', pubkey=f'author-{i}', text=f'Original 🌿 post {i}')
                 for i in range(1, 4)]
        subjects = []
        registry_posts = []
        for post in posts:
            registry_posts.append({k: post[k] for k in ('note_id', 'pubkey')} | dict(
                split='train', text_sha256=hashlib.sha256(post['text'].encode()).hexdigest()))
            for number, subject in [('1', 'Plants'), ('1.1', 'Herbs'), ('1.1.1', 'Rosemary'),
                                    ('2', 'Other complete root')]:
                subjects.append(dict(index=len(subjects), note_id=post['note_id'], number=number,
                    subject=subject, context=f'Source context for {subject}', split='train'))
        self.write('posts.json', dict(schema_version=1, notes=posts))
        registry = self.write('registry.json', dict(schema_version=1,
            posts=registry_posts, subjects=subjects))
        self.write('manifest.json', dict(schema_version=1,
            files={'registry.json': hashlib.sha256(registry.read_bytes()).hexdigest()}))
        self.write('splits.json', dict(schema_version=2, tasks={'subjects': 'ASv6.100'},
            train_note_ids=[p['note_id'] for p in posts], evaluation_note_ids=['v'], test_note_ids=['t']))
        refs = {key: dict(path=name, sha256=hashlib.sha256((self.root/name).read_bytes()).hexdigest())
                for key, name in [('posts', 'posts.json'), ('registry', 'registry.json'),
                                  ('manifest', 'manifest.json'), ('split_manifest', 'splits.json')]}
        selection = dict(schema_version=1, **refs, seed='bootstrap-pilot-v1',
            train_notes=1, evaluation_notes=1, entries_per_note=3, role='train')
        self.write('selection.json', selection)
        self.prompt.write_text('Define the selected topic: {INPUT_JSON}')
        spec = json.loads(self.spec.read_text())
        spec['dataset'] = dict(adapter='bootstrap_student_inputs', path='selection.json')
        self.write('spec.json', spec)
        return selection, posts

    def test_native_preparation_keeps_complete_root_and_disjoint_data_roles(self):
        selection, posts = self.source()
        self.prepare('train')
        selection['role'] = 'evaluation'
        self.write('evaluation-selection.json', selection)
        spec = json.loads(self.spec.read_text())
        spec['dataset']['path'] = 'evaluation-selection.json'
        self.write('evaluation-spec.json', spec)
        self.cli('prepare', 'evaluation', '--spec', self.root/'evaluation-spec.json')
        train, evaluation = self.show('train'), self.show('evaluation')
        self.assertEqual(len(train['cases']), 3)
        self.assertEqual(len(evaluation['cases']), 3)
        train_ids = {c['evidence']['local']['note_id'] for c in train['cases']}
        eval_ids = {c['evidence']['local']['note_id'] for c in evaluation['cases']}
        self.assertFalse(train_ids & eval_ids)
        for role, result in [('train', train), ('evaluation', evaluation)]:
            for case in result['cases']:
                local = json.loads(case['inputs']['INPUT_JSON'])['local']
                self.assertEqual([r['number'] for r in local['hierarchy']['entries']],
                                 ['1', '1.1', '1.1.1'])
                self.assertEqual(local['post'], next(p['text'] for p in posts
                    if p['note_id'] == case['evidence']['local']['note_id']))
                self.assertEqual(case['evidence']['split'], 'train')
                self.assertEqual(case['evidence']['role'], role)
                self.assertNotIn('meaning', local)
        self.assertEqual(self.calls(), [])
        plan = json.loads((self.root/'evaluation/experiment.json').read_text())['plan']
        self.assertIn('bootstrap_student_inputs.py', plan['code'])

    def test_train_jsonl_checks_all_ids_before_decoding_post_or_answer_content(self):
        selection, _ = self.source()
        path = self.root/'train.jsonl'
        path.write_bytes(b'{"note_id":"t",invalid content that cannot be parsed}\n')
        checksum = hashlib.sha256(path.read_bytes()).hexdigest()
        splits = json.loads((self.root/'splits.json').read_text())
        splits['outputs'] = {'train.jsonl': checksum}
        self.write('splits.json', splits)
        selection['split_manifest']['sha256'] = hashlib.sha256((self.root/'splits.json').read_bytes()).hexdigest()
        selection['posts'] = dict(path='train.jsonl', sha256=checksum, format='subject_train_jsonl')
        self.write('selection.json', selection)
        failure = self.cli('prepare', 'bad', '--spec', self.spec, ok=False)
        self.assertIn('frozen TRAIN-only JSONL', failure.stderr)
        self.assertNotIn('JSONDecodeError', failure.stderr)
        self.assertEqual(self.calls(), [])

    def test_refuses_non_train_content(self):
        selection, posts = self.source()
        self.write('posts.json', dict(schema_version=1, notes=posts + [
            dict(note_id='t', pubkey='sealed-author', text='Fixture reserved post')]))
        selection['posts']['sha256'] = hashlib.sha256((self.root/'posts.json').read_bytes()).hexdigest()
        self.write('selection.json', selection)
        failure = self.cli('prepare', 'bad', '--spec', self.spec, ok=False)
        self.assertIn('TRAIN-only', failure.stderr)
        self.assertFalse((self.root/'bad').exists())
        self.assertEqual(self.calls(), [])

    def test_refuses_changed_source_bytes_before_preparation(self):
        self.source()
        path = self.root/'posts.json'
        path.write_bytes(path.read_bytes() + b'\n')
        failure = self.cli('prepare', 'bad', '--spec', self.spec, ok=False)
        self.assertIn('posts hash mismatch', failure.stderr)
        self.assertFalse((self.root/'bad').exists())
        self.assertEqual(self.calls(), [])

    def test_train_jsonl_reuses_only_original_post_inputs_and_never_completions(self):
        selection, posts = self.source()
        instruction = 'Frozen ASv6.100 instruction'
        rows = [dict(note_id=p['note_id'], task='subjects', prompt=[dict(role='user',
            content=instruction+'\n\n<post>\n'+p['text']+'\n</post>')],
            completion=[dict(role='assistant', content='Must never become a Bootstrap target')]) for p in posts]
        path = self.root/'train.jsonl'
        path.write_text(''.join(json.dumps(row)+'\n' for row in rows))
        checksum = hashlib.sha256(path.read_bytes()).hexdigest()
        splits = json.loads((self.root/'splits.json').read_text())
        splits.update(outputs={'train.jsonl': checksum},
                      subject_instruction_sha256=hashlib.sha256(instruction.encode()).hexdigest())
        self.write('splits.json', splits)
        selection['split_manifest']['sha256'] = hashlib.sha256((self.root/'splits.json').read_bytes()).hexdigest()
        selection['posts'] = dict(path='train.jsonl', sha256=checksum, format='subject_train_jsonl')
        self.write('selection.json', selection)
        self.prepare()
        for case in self.show()['cases']:
            self.assertNotIn('Must never become', case['prompt'])
            self.assertNotIn('Frozen ASv6.100 instruction', case['prompt'])
            self.assertIn('Original', json.loads(case['inputs']['INPUT_JSON'])['local']['post'])
        self.assertEqual(self.calls(), [])

    def test_same_author_cannot_fill_both_pilot_roles(self):
        selection, posts = self.source()
        registry = json.loads((self.root/'registry.json').read_text())
        for post, row in zip(posts, registry['posts']):
            post['pubkey'] = row['pubkey'] = 'same-author'
        self.write('posts.json', dict(schema_version=1, notes=posts))
        self.write('registry.json', registry)
        selection['registry']['sha256'] = hashlib.sha256((self.root/'registry.json').read_bytes()).hexdigest()
        selection['posts']['sha256'] = hashlib.sha256((self.root/'posts.json').read_bytes()).hexdigest()
        self.write('manifest.json', dict(schema_version=1,
            files={'registry.json': selection['registry']['sha256']}))
        selection['manifest']['sha256'] = hashlib.sha256((self.root/'manifest.json').read_bytes()).hexdigest()
        self.write('selection.json', selection)
        failure = self.cli('prepare', 'bad', '--spec', self.spec, ok=False)
        self.assertIn('not enough distinct TRAIN authors/texts', failure.stderr)
        self.assertFalse((self.root/'bad').exists())
        self.assertEqual(self.calls(), [])


if __name__ == '__main__':
    unittest.main()
