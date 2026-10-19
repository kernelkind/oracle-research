"""Production CLI checks for frozen multi-section count comparisons."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np

from sse_multivector.section_count_panel import prepare, run


class SectionCountPanelTests(unittest.TestCase):
    def _fixture(self, root):
        sources = {}
        for name, prefix in [('examined', 'a'), ('reserved', 'b')]:
            base = root / name
            base.mkdir()
            np.savez(base / 'input.npz', vectors=np.repeat(np.eye(2), 3, axis=0),
                     notes=np.array([prefix + str(i) for i in range(6)]))
            entries = [dict(id=str(i), note_id=prefix + str(i), title='topic',
                            meaning='fixed meaning', source_group=['G1', 'G1', 'G1', 'G2', 'G3', 'G3'][i])
                       for i in range(6)]
            (base / 'entries.json').write_text(json.dumps(entries))
            (base / 'labels.json').write_text(json.dumps({'best': {'labels': [0, 0, 0, 1, 1, 1]}}))
            sources[name] = {
                'input': str(base / 'input.npz'), 'entries': str(base / 'entries.json'),
                'labels': {'saved': str(base / 'labels.json')},
                'files': {str(base / file): hashlib.sha256((base / file).read_bytes()).hexdigest()
                          for file in ['input.npz', 'entries.json', 'labels.json']}}
        spec = dict(sources=sources, counts=[1, 2], seeds=[10, 11],
                    max_iterations=50, time_limit=30, cases=[
                        dict(id='D01', role='development', source='examined',
                             selector={'kind': 'all'}, minimum_notes=0),
                        dict(id='V01', role='reserved', source='reserved',
                             selector={'kind': 'all'}, minimum_notes=0)])
        manifest = root / 'spec.json'
        manifest.write_text(json.dumps(spec))
        return manifest, spec

    def test_no_split_and_two_children_use_same_inputs_without_running_reserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, spec = self._fixture(root)
            output = root / 'output'
            command = [sys.executable, '-m', 'sse_multivector.section_count_panel']
            prepared = subprocess.run(command + ['prepare', str(manifest), str(output)],
                                      capture_output=True, text=True)
            self.assertEqual(prepared.returncode, 0, prepared.stderr)
            subprocess.run(command + ['run', str(output), 'D01'], check=True,
                           capture_output=True, text=True)
            summary = json.loads((output / 'D01/summary.json').read_text())
            self.assertEqual(summary['counts'][0]['count'], 1)
            self.assertTrue(summary['counts'][0]['no_split'])
            self.assertIsNone(summary['counts'][0]['valid_refinement'])
            self.assertEqual(summary['counts'][1]['notes_per_child'], [3, 3])
            self.assertTrue(summary['counts'][1]['valid_refinement'])
            self.assertAlmostEqual(summary['counts'][1]['objective'], 0)
            self.assertFalse((output / 'V01').exists())
            before = (output / 'D01/count-2.json').read_bytes()
            subprocess.run(command + ['run', str(output), 'D01'], check=True,
                           capture_output=True, text=True)
            self.assertEqual((output / 'D01/count-2.json').read_bytes(), before)

    def test_saved_label_and_group_selectors_preserve_rows_and_singleton_baseline(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, spec = self._fixture(root)
            spec['cases'][0]['selector'] = {'kind': 'labels', 'mode': 'saved', 'value': 0}
            spec['cases'].append(dict(id='D02', role='development', source='examined',
                                     selector={'kind': 'source_group', 'value': 'G2'}, minimum_notes=0))
            manifest.write_text(json.dumps(spec))
            plan = prepare(manifest, root / 'out')
            self.assertEqual(plan['cases'][0]['indices'], [0, 1, 2])
            self.assertEqual(plan['cases'][2]['entry_ids'], ['3'])
            self.assertEqual(plan['cases'][2]['counts'], [1])
            result = run(root / 'out', 'D01')
            self.assertEqual(result['counts'][1]['nonempty_children'], 1)
            self.assertFalse(result['counts'][1]['valid_refinement'])
            singleton = run(root / 'out', 'D02')
            self.assertTrue(singleton['counts'][0]['no_split'])

    def test_cross_role_note_overlap_is_rejected_before_preparing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, spec = self._fixture(root)
            spec['cases'][1]['source'] = 'examined'
            manifest.write_text(json.dumps(spec))
            with self.assertRaisesRegex(ValueError, 'share original notes'):
                prepare(manifest, root / 'out')
            self.assertFalse((root / 'out').exists())

    def test_changed_source_is_rejected_before_case_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, spec = self._fixture(root)
            prepare(manifest, root / 'out')
            Path(spec['sources']['examined']['input']).write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'Frozen source changed'):
                run(root / 'out', 'D01')
            self.assertFalse((root / 'out/D01').exists())

    def test_native_exact_reuse_requires_settings_and_original_note_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, spec = self._fixture(root)
            native = root / 'native'
            subprocess.run([sys.executable, '-m', 'sse_multivector.direct_section_partition',
                            spec['sources']['examined']['input'], str(native), '--sections', '2',
                            '--minimum-notes', '0', '--minimum-total-notes', '6',
                            '--starts', '2', '--seed', '10'], check=True,
                           capture_output=True, text=True)
            spec['cases'][0]['reuse'] = {'2': {
                'plan': str(native / 'plan.json'), 'result': str(native / 'unconstrained.json'),
                'mode': 'unconstrained',
                'files': {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in [native / 'plan.json', native / 'unconstrained.json']}}}
            manifest.write_text(json.dumps(spec))
            prepare(manifest, root / 'out')
            result = run(root / 'out', 'D01')
            self.assertTrue(result['counts'][1]['reused_producer'])
            saved = json.loads((root / 'out/D01/count-2.json').read_text())
            self.assertEqual(saved['panel']['best'],
                             json.loads((native / 'unconstrained.json').read_text())['best'])
            spec['cases'][0]['source'] = 'reserved'
            spec['cases'][1]['source'] = 'examined'
            manifest.write_text(json.dumps(spec))
            prepare(manifest, root / 'wrong')
            with self.assertRaisesRegex(ValueError, 'different original input rows'):
                run(root / 'wrong', 'D01')
            self.assertFalse((root / 'wrong/D01/count-2.json').exists())


if __name__ == '__main__':
    unittest.main()
