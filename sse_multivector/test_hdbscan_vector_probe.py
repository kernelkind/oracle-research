"""Saved-vector controls through the production native HDBSCAN route."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np

from sse_multivector import hierarchy_hdbscan as hdbscan
from sse_multivector.hdbscan_vector_probe import prepare, run


@unittest.skipUnless(os.environ.get('HDBSCAN_TEST_BINARY'), 'Native HDBSCAN executable required')
class HdbscanVectorProbeTests(unittest.TestCase):
    def _source(self, root):
        rng = np.random.default_rng(7)
        x = np.repeat(np.eye(2), 6, axis=0) + rng.normal(0, .003, (12, 2))
        x /= np.linalg.norm(x, axis=1, keepdims=True)
        entries = [dict(id=f'L{i:03d}', title='fixed', meaning='fixed meaning',
                        note_id=f'n{i}', source_group='G1' if i < 6 else 'G2')
                   for i in range(12)]
        np.savez(root / 'input.npz', vectors=x, notes=np.array([e['note_id'] for e in entries]))
        (root / 'entries.json').write_text(json.dumps(entries))
        state = dict(items={e['id']: dict(vector_key=e['id']) for e in entries},
                     originals=[dict(id=e['id'], subject=e['title'], meaning=e['meaning'],
                                     local=dict(note_id=e['note_id'])) for e in entries])
        request, _ = hdbscan.request_for(state, [e['id'] for e in entries], x.tolist())
        (root / 'state.json').write_text(json.dumps(state))
        (root / 'request.json').write_text(json.dumps(request))
        spec = dict(as_version='ASv6.100', binary=os.environ['HDBSCAN_TEST_BINARY'],
                    source=dict(input=str(root / 'input.npz'), entries=str(root / 'entries.json'),
                                files={str(root / f): hashlib.sha256((root / f).read_bytes()).hexdigest()
                                       for f in ['input.npz', 'entries.json', 'state.json', 'request.json']}),
                    native_state=str(root / 'state.json'), native_request=str(root / 'request.json'),
                    cases=[dict(id='combined', groups=['G1', 'G2'])])
        (root / 'spec.json').write_text(json.dumps(spec))
        return root / 'spec.json', spec

    def test_cli_both_views_use_same_ids_and_native_results_resume_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec, _ = self._source(root)
            cli = [sys.executable, '-m', 'sse_multivector.hdbscan_vector_probe']
            p = subprocess.run(cli + ['prepare', str(spec), str(root / 'out')],
                               capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            a = run(root / 'out', 'combined', 'title')
            b = run(root / 'out', 'combined', 'meaning')
            self.assertEqual(len(a['groups']), 2)
            self.assertEqual(a['groups'], b['groups'])
            self.assertEqual(a['unassigned'], [])
            ar = json.loads(Path(a['native']['hdbscan']['request']).read_text())
            br = json.loads(Path(b['native']['hdbscan']['request']).read_text())
            self.assertEqual([i['opaque_id'] for i in ar['inputs']],
                             [i['opaque_id'] for i in br['inputs']])
            path = root / 'out/combined/title/result.json'
            before = path.read_bytes()
            self.assertEqual(run(root / 'out', 'combined', 'title'), a)
            self.assertEqual(path.read_bytes(), before)
            plan = json.loads((root / 'out/plan.json').read_text())
            Path(plan['cases'][0]['data']).write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'Frozen source changed'):
                run(root / 'out', 'combined', 'title')

    def test_unknown_group_and_mismatched_original_meaning_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec_path, spec = self._source(root)
            spec['cases'][0]['groups'] = ['missing']
            spec_path.write_text(json.dumps(spec))
            with self.assertRaisesRegex(ValueError, 'group'):
                prepare(spec_path, root / 'bad')
            self.assertFalse((root / 'bad').exists())
            spec['cases'][0]['groups'] = ['G1']
            state = json.loads((root / 'state.json').read_text())
            state['originals'][0]['meaning'] = 'different'
            (root / 'state.json').write_text(json.dumps(state))
            spec['source']['files'][str(root / 'state.json')] = hashlib.sha256(
                (root / 'state.json').read_bytes()).hexdigest()
            spec_path.write_text(json.dumps(spec))
            with self.assertRaisesRegex(ValueError, 'Original evidence'):
                prepare(spec_path, root / 'bad')
            self.assertFalse((root / 'bad').exists())

    def test_all_entries_includes_originally_unassigned_and_requires_one_selector(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec_path, spec = self._source(root)
            entries = json.loads((root / 'entries.json').read_text())
            entries[0]['source_group'] = None
            (root / 'entries.json').write_text(json.dumps(entries))
            spec['source']['files'][str(root / 'entries.json')] = hashlib.sha256(
                (root / 'entries.json').read_bytes()).hexdigest()
            spec['cases'] = [dict(id='all', all_entries=True)]
            spec_path.write_text(json.dumps(spec))
            plan = prepare(spec_path, root / 'out')
            self.assertEqual([e['id'] for e in plan['cases'][0]['entries']],
                             [e['id'] for e in entries])
            self.assertIsNone(plan['cases'][0]['entries'][0]['source_group'])
            result = run(root / 'out', 'all', 'meaning')
            self.assertEqual(result['input_entries'], 12)
            self.assertEqual(result['input_notes'], 12)
            for cfg in [dict(id='bad', all_entries=True, groups=['G1']),
                        dict(id='bad', all_entries=False), dict(id='bad')]:
                spec['cases'] = [cfg]
                spec_path.write_text(json.dumps(spec))
                with self.assertRaisesRegex(ValueError, 'selector'):
                    prepare(spec_path, root / 'bad')
                self.assertFalse((root / 'bad').exists())

    def test_resolved_bootstrap_title_is_compared_instead_of_original_subject(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec_path, spec = self._source(root)
            state = json.loads((root / 'state.json').read_text())
            state['originals'][0].update(subject='original wording', title='fixed')
            (root / 'state.json').write_text(json.dumps(state))
            spec['source']['files'][str(root / 'state.json')] = hashlib.sha256(
                (root / 'state.json').read_bytes()).hexdigest()
            spec_path.write_text(json.dumps(spec))
            plan = prepare(spec_path, root / 'out')
            self.assertEqual(plan['cases'][0]['entries'][0]['title'], 'fixed')

    def test_cli_combined_uses_mean_cosine_with_matched_ids_and_native_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec_path, spec = self._source(root)
            with np.load(root / 'input.npz') as data:
                title, notes = data['vectors'], data['notes']
            meaning = np.tile(np.eye(2), (6, 1))
            np.savez(root / 'input.npz', vectors=meaning, notes=notes)
            spec['source']['files'][str(root / 'input.npz')] = hashlib.sha256(
                (root / 'input.npz').read_bytes()).hexdigest()
            spec_path.write_text(json.dumps(spec))
            prepare(spec_path, root / 'out')
            p = subprocess.run([sys.executable, '-m', 'sse_multivector.hdbscan_vector_probe',
                                'run', str(root / 'out'), 'combined', 'combined'],
                               capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            report_path = root / 'out/combined/combined/result.json'
            report = json.loads(report_path.read_text())
            request = json.loads(Path(report['native']['hdbscan']['request']).read_text())
            vectors = np.array([e['normalized_vector'] for e in request['inputs']])
            self.assertEqual(vectors.shape, (12, 4))
            np.testing.assert_allclose(vectors @ vectors.T,
                                       (title @ title.T + meaning @ meaning.T) / 2,
                                       atol=1e-14)
            baseline = run(root / 'out', 'combined', 'title')
            baseline_request = json.loads(Path(baseline['native']['hdbscan']['request']).read_text())
            self.assertEqual([e['opaque_id'] for e in request['inputs']],
                             [e['opaque_id'] for e in baseline_request['inputs']])
            self.assertEqual(request['hdbscan_configuration'],
                             baseline_request['hdbscan_configuration'])
            before = report_path.read_bytes()
            self.assertEqual(run(root / 'out', 'combined', 'combined'), report)
            self.assertEqual(report_path.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
