"""Direct node/post sorting through the source-bound production experiment CLI."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from sse_multivector.test_extraction_pipeline import FAKE_RUNNER


CLI = Path(__file__).with_name('experiment.py')


class NodeSortingTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        runner = self.root/'runner'
        runner.write_text(FAKE_RUNNER)
        runner.chmod(0o755)
        self.log = self.root/'calls.json'
        self.write('subjects.json', dict(notes=[dict(note_id='N1', text='Tea warms me.',
            subjects=[dict(id=sid, subject='Tea', context=context) for sid, context in
                      [('SP1', 'Tea brings warmth.'), ('SP2', 'Tea is enjoyed.')]]),
            dict(note_id='N2', text='A cup of tea with breakfast.',
                 subjects=[dict(id='SP3', subject='Tea', context='Tea accompanies breakfast.')])]))
        self.write('hierarchy.json', dict(graph=dict(nodes=[dict(group='G', title='Tea')])))
        self.source = dict(schema_version=1, subjects='subjects.json', hierarchy='hierarchy.json',
            selections=[dict(id=cid, node_id='G', note_id=note_id, subject_id=sid)
                        for cid, note_id, sid in [('first', 'N1', 'SP1'),
                        ('duplicate', 'N1', 'SP2'), ('second', 'N2', 'SP3')]])
        self.write('source.json', self.source)
        (self.root/'prompt.txt').write_text('GENERIC PROMPT {INPUT_JSON}')
        self.write('spec.json', dict(schema_version=1,
            prompt=dict(id='NodeSorting-v1', path='prompt.txt'),
            dataset=dict(adapter='node_sorting', path='source.json'),
            runner=dict(runner_binary=str(runner), provider='openai-codex', auth_file=None,
                        model='fixture/model', reasoning_effort='low', concurrency=1)))

    def write(self, name, value):
        (self.root/name).write_text(json.dumps(value))

    def cli(self, *args, ok=True, answer=None):
        env = {**os.environ, 'FAKE_RUNNER_LOG': str(self.log)}
        if answer is not None:
            env['FAKE_RUNNER_PROMPT_RESPONSE'] = json.dumps(answer)
        result = subprocess.run([sys.executable, str(CLI), *map(str, args)],
            cwd=self.root, capture_output=True, text=True, timeout=30, env=env)
        self.assertEqual(result.returncode == 0, ok, result.stderr + result.stdout)
        return result

    def prepare(self):
        self.cli('prepare', 'S', '--spec', 'spec.json')

    def test_direct_scores_collect_once_per_post_with_descending_order_without_sse(self):
        self.prepare()
        self.cli('run', 'S', '--max-new-attempts', '1', ok=False,
                 answer=dict(sorting_score=80, reason='Focused tea post.'))
        self.cli('run', 'S', answer=dict(sorting_score=20, reason='Tea accompanies another subject.'))
        plan = json.loads((self.root/'S/experiment.json').read_text())['plan']
        self.assertEqual(len(plan['cases']), 3)
        for case in plan['cases']:
            payload = json.loads(case['inputs']['INPUT_JSON'])
            self.assertEqual(set(payload), {'node_title', 'post'})
            self.assertEqual(payload['node_title'], 'Tea')
            self.assertIn('context', case['evidence'])
        self.assertEqual(len(json.loads(self.log.read_text())), 2)
        calls = self.log.read_bytes()
        self.cli('collect', 'S', '--output', 'collected')
        result = json.loads((self.root/'collected/node-sorting.json').read_text())
        node = result['nodes'][0]
        self.assertEqual((node['node_id'], node['node_title'], node['order']), ('G', 'Tea', ['N1', 'N2']))
        self.assertEqual([(p['note_id'], p['sorting_score']) for p in node['posts']], [('N1', 80), ('N2', 20)])
        self.assertEqual(set(node['posts'][0]['case_ids']), {'first', 'duplicate'})
        self.assertEqual(self.log.read_bytes(), calls)
        self.assertFalse(list(self.root.rglob('worker-request.json')))
        provenance = json.loads((self.root/'collected/provenance.json').read_text())
        self.assertEqual(provenance['inference_calls'], 0)
        self.assertIn(str(self.root/'subjects.json'), provenance['sources'])

    def test_optional_description_is_source_bound_and_changed_source_blocks_collection(self):
        self.write('descriptions.json', dict(schema_version=1, nodes=[dict(node_id='G',
            node_title='Tea', description='Preparing and drinking tea.')]))
        self.write('source.json', {**self.source, 'descriptions': 'descriptions.json'})
        self.prepare()
        plan = json.loads((self.root/'S/experiment.json').read_text())['plan']
        for case in plan['cases']:
            self.assertEqual(json.loads(case['inputs']['INPUT_JSON'])['node_description'],
                             'Preparing and drinking tea.')
        self.cli('run', 'S', answer=dict(sorting_score=70, reason='Concerns drinking tea.'))
        (self.root/'descriptions.json').write_text('{}')
        self.cli('collect', 'S', '--output', 'changed', ok=False)
        self.assertFalse((self.root/'changed').exists())

    def test_invalid_score_output_is_not_collected(self):
        from sse_multivector import experiment
        self.prepare()
        self.cli('run', 'S', ok=False,
                 answer=dict(sorting_score=True, reason='A boolean is not a score.'))
        self.assertEqual(experiment.report(self.root/'S')['cases'][0]['status'], 'malformed')
        self.cli('collect', 'S', '--output', 'invalid', ok=False)
        self.assertFalse((self.root/'invalid').exists())

    def test_collection_rejects_conflicting_scores_for_same_node_post(self):
        self.prepare()
        self.cli('run', 'S', answer=dict(sorting_score=80, reason='Focused tea post.'))
        self.cli('prepare', 'different', '--spec', 'spec.json', '--repeat')
        self.cli('run', 'different', answer=dict(sorting_score=20, reason='Different independent judgment.'))
        self.cli('collect', 'S', 'different', '--output', 'conflicting', ok=False)
        self.assertFalse((self.root/'conflicting').exists())


if __name__ == '__main__':
    unittest.main()
