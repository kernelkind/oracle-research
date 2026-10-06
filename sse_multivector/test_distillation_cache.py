"""Model download and offline checks through the actual Hub client."""
from contextlib import contextmanager
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch


@contextmanager
def fixture_hub(files, host='127.0.0.1'):
    revision, requests = 'a'*40, []
    class Hub(BaseHTTPRequestHandler):
        def do_HEAD(self):
            self.respond(False)
        def do_GET(self):
            self.respond(True)
        def respond(self, body):
            requests.append((self.command, self.path, self.headers.get('Authorization')))
            if self.path.startswith('/api/models/'):
                payload = json.dumps({'id': 'fixture/cached', 'sha': revision, 'siblings': [
                    {'rfilename': n, 'size': len(p), 'blobId': hashlib.sha1(
                        ('blob %d\0' % len(p)).encode()+p).hexdigest(),
                     **({'lfs': {'sha256': hashlib.sha256(p).hexdigest(), 'size': len(p),
                                'pointerSize': 128}} if n.endswith('.safetensors') else {})}
                    for n, p in files.items() if p is not None]}).encode()
            else:
                name = self.path.split('/resolve/'+revision+'/', 1)[-1]
                payload = files.get(name)
            if payload is None:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header('Content-Length', str(len(payload)))
            self.send_header('ETag', hashlib.sha256(payload).hexdigest())
            self.send_header('X-Repo-Commit', revision)
            self.end_headers()
            if body:
                self.wfile.write(payload)
        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer((host, 0), Hub)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        yield server.server_port, requests
    finally:
        server.shutdown()
        server.server_close()
        worker.join()


class CacheTests(unittest.TestCase):
    def test_local_completion_rejects_a_report_without_required_weights(self):
        from sse_multivector import distillation_cache as cache
        from sse_multivector.distillation_run import write_json
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = root / 'model-cache.json'
            write_json(manifest, {'version': 1, 'reserve_bytes': 0, 'models': [{
                'model': 'fixture/cached', 'revision': 'a'*40, 'files': [{
                    'path': 'model.safetensors', 'size': 8, 'sha256': 'b'*64}]}]})
            result = root / 'results'
            result.mkdir()
            write_json(result / 'verification.json', {'state': 'complete',
                'manifest_sha256': cache.sha256(manifest), 'files': []})
            with self.assertRaisesRegex(ValueError, 'required cache files'):
                cache.verify_results(manifest, result)

    def test_prepare_pins_index_shards_and_tokenizer_files_without_downloading_weights(self):
        from sse_multivector import distillation_cache as cache
        from sse_multivector.distillation_run import read_json, write_json
        files = {'config.json': b'{}', 'tokenizer_config.json': b'{}', 'tokenizer.json': b'{}',
            'model.safetensors.index.json': b'{"weight_map":{"layer":"model-01.safetensors"}}',
            'model-01.safetensors': b'weights', 'unused.safetensors': b'alternative weights',
            'README.md': b'model card', 'chat_templates/default.jinja': b'{{messages}}'}
        with fixture_hub(files) as (port, requests), tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / 'student.json'
            write_json(config, {'model': 'fixture/cached', 'revision': 'a'*40})
            with patch.dict(os.environ, {'HF_ENDPOINT': f'http://127.0.0.1:{port}'}):
                cache.prepare([config], root / 'inputs')
            manifest = read_json(root / 'inputs/model-cache.json')
            selected = {r['path'] for r in manifest['models'][0]['files']}
            self.assertEqual(selected, set(files)-{'README.md', 'unused.safetensors'})
            self.assertFalse(any('/resolve/' in path and path.endswith('.safetensors')
                                 for method, path, auth in requests))
            self.assertEqual(cache.verify_package(root / 'inputs')['timeout_seconds'], None)

    def test_failed_download_keeps_verification_evidence_and_good_files(self):
        from sse_multivector import distillation_cache as cache
        from sse_multivector.distillation_run import read_json, write_json
        files = {'config.json': b'{}', 'model.safetensors': None}
        with fixture_hub(files) as (port, requests), tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = root / 'manifest.json'
            write_json(manifest, {'version': 1, 'reserve_bytes': 0, 'models': [{
                'model': 'fixture/cached', 'revision': 'a'*40, 'files': [
                    {'path': n, 'size': len(p), 'sha256': hashlib.sha256(p).hexdigest()}
                    for n, p in [('config.json', b'{}'), ('model.safetensors', b'weights')]]}]})
            with patch.dict(os.environ, {'HF_HOME': str(root / 'cache'),
                    'HF_ENDPOINT': f'http://127.0.0.1:{port}'}):
                with self.assertRaisesRegex(ValueError, 'model download failed'):
                    cache.download(manifest, root / 'results')
                report = read_json(root / 'results/verification.json')
                self.assertEqual(report['state'], 'failed')
                self.assertEqual(len(report['files']), 1)
                self.assertTrue((root / 'results/volume.json').exists())
                self.assertTrue((root / 'results/download.jsonl').exists())
                files['model.safetensors'] = b'weights'
                before = len(requests)
                self.assertEqual(cache.download(manifest, root / 'repaired')['state'], 'complete')
                self.assertFalse(any(method == 'GET' and path.endswith('config.json')
                                     for method, path, auth in requests[before:]))

    def test_download_repairs_corruption_and_offline_check_never_downloads(self):
        from sse_multivector import distillation_cache as cache
        files = {'config.json': b'{"model_type":"gpt2"}',
                 'tokenizer_config.json': b'{}', 'tokenizer.json': b'{}',
                 'model.safetensors': b'complete public weights'}
        revision = 'a'*40
        with fixture_hub(files) as (port, requests):
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                manifest = root / 'manifest.json'
                manifest.write_text(json.dumps({'version': 1, 'reserve_bytes': 0, 'models': [{
                    'model': 'fixture/cached', 'revision': revision,
                    'files': [{'path': n, 'size': len(p), 'sha256': hashlib.sha256(p).hexdigest()}
                              for n, p in files.items()]}]}))
                with patch.dict(os.environ, {'HF_HOME': str(root / 'cache'),
                        'HF_ENDPOINT': f'http://127.0.0.1:{port}'}):
                    report = cache.download(manifest, root / 'results')
                    self.assertEqual(report['state'], 'complete')
                    self.assertEqual(len(report['files']), 4)
                    self.assertTrue((root / 'results/download.jsonl').is_file())
                    self.assertTrue((root / 'results/volume.json').is_file())
                    from huggingface_hub import hf_hub_download
                    weights = Path(hf_hub_download('fixture/cached', 'model.safetensors',
                        revision=revision, cache_dir=root / 'cache/hub', local_files_only=True))
                    before = list(requests)
                    weights.write_bytes(b'corrupt')
                    with self.assertRaisesRegex(ValueError, 'cache verification failed'):
                        cache.verify(manifest)
                    self.assertEqual(requests, before)
                    cache.download(manifest, root / 'repair')
                    self.assertEqual(weights.read_bytes(), files['model.safetensors'])
                    downloaded = [p for method, p, auth in requests[len(before):] if method == 'GET']
                    self.assertEqual(len(downloaded), 1)
                    self.assertTrue(downloaded[0].endswith('/model.safetensors'))
                    before = list(requests)
                    self.assertEqual(cache.verify(manifest)['state'], 'complete')
                    self.assertEqual(requests, before)
                    self.assertTrue(all(auth is None for method, p, auth in requests))
