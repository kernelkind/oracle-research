"""Exercise the real experiment CLI, loopback transport and server protocol."""
from http.server import HTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest

from sse_multivector.local_model import endpoint
from sse_multivector.local_weight_model import Handler


class LocalModelTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.received = []
        self.answer = '{"relation":"neither","reason":"Independent topics."}'
        self.returned_model = 'fixture/immutable'
        self.server = HTTPServer(('127.0.0.1', 0), Handler)
        self.server.backend = self
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(self.server.shutdown)
        self.environment = {**os.environ,
            'LOCAL_MODEL_URL': f'http://127.0.0.1:{self.server.server_port}',
            'PATH': str(Path(sys.executable).parent) + os.pathsep + os.environ['PATH']}
        (self.root/'prompt.txt').write_text('Classify complete inputs: {DATA}')
        (self.root/'cases.json').write_text(json.dumps({'cases': [
            {'id': 'one', 'inputs': {'DATA': 'Steel 🌿 {DATA}'}}]}))
        spec = {'schema_version': 1, 'prompt': {'id': 'fixture-v1', 'path': 'prompt.txt'},
            'dataset': {'adapter': 'generic', 'path': 'cases.json'}, 'runner': {
                'provider': 'local', 'transport': 'http', 'auth_file': None,
                'model': 'fixture/immutable', 'reasoning_effort': 'off', 'concurrency': 1,
                'runner_binary': str(Path(__file__).with_name('run-local-model.sh')),
                'max_output_tokens': 128, 'timeout_seconds': 5,
                'output_schema': {'type': 'object', 'additionalProperties': False,
                    'required': ['relation', 'reason'], 'properties': {
                        'relation': {'type': 'string', 'enum': ['neither']},
                        'reason': {'type': 'string'}}}}}
        (self.root/'spec.json').write_text(json.dumps(spec))

    def complete(self, body):
        self.received.append(body)
        return {'model': self.returned_model, 'raw_text': self.answer, 'stop_reason': 'stop',
                'usage': {'input': 10, 'output': 10, 'cacheRead': 0, 'cacheWrite': 0},
                'metadata': {'config_sha256': 'a'*64}}

    def cli(self, *args, success=True):
        result = subprocess.run([sys.executable, str(Path(__file__).with_name('experiment.py')),
            *args], cwd=self.root, env=self.environment, text=True, capture_output=True, timeout=15)
        self.assertEqual(result.returncode == 0, success, result.stderr + result.stdout)
        return result

    def test_native_cli_preserves_exact_prompt_schema_and_reuses_receipts(self):
        self.cli('prepare', 'first', '--spec', 'spec.json', '--history-root', str(self.root))
        self.assertEqual(self.received, [])
        self.cli('run', 'first')
        self.assertEqual(self.received[0]['messages'], [
            {'role': 'user', 'content': 'Classify complete inputs: Steel 🌿 {DATA}'}])
        self.assertEqual(self.received[0]['max_tokens'], 128)
        shown = json.loads(self.cli('show', 'first', '--json').stdout)
        self.assertEqual(shown['summary']['valid'], 1)
        self.assertEqual(shown['cases'][0]['parsed']['relation'], 'neither')
        self.assertEqual(shown['relation_diagnostics']['relation_counts'], {'neither': 1})
        self.cli('prepare', 'second', '--from', 'first', '--history-root', str(self.root),
                 '--runner-binary', str(Path(__file__).with_name('run-local-model.sh')))
        self.cli('run', 'second')
        self.assertEqual(len(self.received), 1)

    def test_invalid_schema_answer_remains_failed_without_a_retry(self):
        self.answer = '{"relation":"wrong","reason":"Invalid option."}'
        self.cli('prepare', 'first', '--spec', 'spec.json', '--history-root', str(self.root))
        self.cli('run', 'first', success=False)
        shown = json.loads(self.cli('show', 'first', '--json').stdout)
        self.assertEqual(shown['summary']['valid'], 0)
        self.assertEqual(len(self.received), 1)

    def test_changed_model_identity_is_rejected(self):
        self.returned_model = 'different/immutable'
        self.cli('prepare', 'first', '--spec', 'spec.json', '--history-root', str(self.root))
        self.cli('run', 'first', success=False)
        self.assertEqual(len(self.received), 1)

    def test_endpoint_requires_explicit_loopback_without_credentials(self):
        for url in ['https://127.0.0.1:1234', 'http://example.com:1234',
                    'http://user:secret@127.0.0.1:1234', 'http://127.0.0.1',
                    'http://127.0.0.1:1234/path']:
            with self.assertRaises(ValueError):
                endpoint(url)


if __name__ == '__main__':
    unittest.main()
