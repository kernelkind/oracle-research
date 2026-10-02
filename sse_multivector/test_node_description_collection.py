"""Source-bound node descriptions through the production experiment CLI."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from sse_multivector.test_extraction_pipeline import FAKE_RUNNER


CLI = Path(__file__).with_name('experiment.py')


class NodeDescriptionCollectionTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        runner = self.root / 'runner'
        runner.write_text(FAKE_RUNNER)
        runner.chmod(0o755)
        self.log = self.root / 'calls.json'
        post = dict(instance='V1', vector_id='vector1', note_id='N1',
                    text='Tea warms me.', byte_spans=[[0, 3]], fragments=['Tea'])
        self.write('packets.json', dict(packets=[dict(packet='G', instances=[post])]))
        self.write('hierarchy.json', dict(graph=dict(nodes=[dict(
            group='G', title='Tea', source_group_ids=['G'])]),
            memberships=dict(nodes=[dict(group='G', title='Tea', matched_instances=[post])])))
        self.write('source.json', dict(schema_version=1, source_packets='packets.json',
                                      hierarchy='hierarchy.json', nodes=['G']))
        (self.root / 'prompt.txt').write_text('GENERIC PROMPT {INPUT_JSON}')
        self.write('spec.json', dict(schema_version=1,
            prompt=dict(id='NodeDescription-v1', path='prompt.txt'),
            dataset=dict(adapter='node_descriptions', path='source.json'),
            runner=dict(runner_binary=str(runner), provider='openai-codex', auth_file=None,
                        model='fixture/model', reasoning_effort='low', concurrency=1)))
        self.answer = dict(node_id='G', node_title='Tea', description='Preparing and drinking tea.')

    def write(self, name, value):
        (self.root / name).write_text(json.dumps(value))

    def cli(self, *args, ok=True, env=None):
        result = subprocess.run([sys.executable, str(CLI), *map(str, args)],
            cwd=self.root, capture_output=True, text=True, timeout=30,
            env={**os.environ, 'FAKE_RUNNER_LOG': str(self.log), **(env or {})})
        self.assertEqual(result.returncode == 0, ok, result.stderr + result.stdout)
        return result

    def generate(self):
        self.cli('prepare', 'D', '--spec', 'spec.json')
        self.cli('run', 'D', env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(self.answer)})

    def test_collect_preserves_receipts_and_supplies_prominence_input(self):
        self.generate()
        receipts = self.root / 'D/run/results.jsonl'
        before = receipts.read_bytes()
        calls = self.log.read_bytes()
        self.cli('collect', 'D', '--output', 'collected')
        collected = json.loads((self.root / 'collected/node-descriptions.json').read_text())
        self.assertEqual(collected, dict(schema_version=1, nodes=[self.answer]))
        provenance = json.loads((self.root / 'collected/provenance.json').read_text())
        self.assertEqual(provenance['inference_calls'], 0)
        self.assertEqual(provenance['sources'][str(receipts)], hashlib.sha256(before).hexdigest())
        self.assertEqual(receipts.read_bytes(), before)
        self.assertEqual(self.log.read_bytes(), calls)
        self.write('subjects.json', dict(notes=[dict(note_id='N1', text='Tea warms me.',
            subjects=[dict(number='1', subject='Tea', context='Tea warms the writer.',
                           byte_spans=[[0, 3]], fragments=['Tea'])])]))
        self.write('contexts.json', dict(schema_version=1, subjects='subjects.json',
            hierarchy='hierarchy.json', descriptions='collected/node-descriptions.json', nodes=['G']))
        spec = json.loads((self.root / 'spec.json').read_text())
        spec['dataset'] = dict(adapter='subject_contexts', path='contexts.json',
                               prominence_basis='node_title')
        self.write('prominence.json', spec)
        self.cli('prepare', 'P', '--spec', 'prominence.json')
        plan = json.loads((self.root / 'P/experiment.json').read_text())['plan']
        payload = json.loads(plan['cases'][0]['inputs']['INPUT_JSON'])
        self.assertEqual(payload, dict(node_title='Tea', post='Tea warms me.',
                                      node_description=self.answer['description']))
        self.assertEqual(self.log.read_bytes(), calls)

    def test_collect_rejects_duplicate_nodes_and_changed_referenced_sources(self):
        self.generate()
        self.cli('collect', 'D', 'D', '--output', 'duplicate', ok=False)
        self.assertFalse((self.root / 'duplicate').exists())
        packets = self.root / 'packets.json'
        packets.write_text(packets.read_text() + '\n')
        self.cli('collect', 'D', '--output', 'changed', ok=False)
        self.assertFalse((self.root / 'changed').exists())


if __name__ == '__main__':
    unittest.main()
