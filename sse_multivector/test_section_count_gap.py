"""Production-path checks for the offline gap-statistic screen."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np

from sse_multivector import section_count_panel as panel
from sse_multivector.section_count_gap import dispersion, select_count, prepare, run


class SectionCountGapTests(unittest.TestCase):
    def _panel(self, root, constant=False, preserve_groups=False, group_size=3):
        rng = np.random.default_rng(123)
        angle = np.r_[rng.normal(0, .01, 12), rng.normal(1.5, .01, 12)]
        vectors = np.c_[np.cos(angle), np.sin(angle)]
        if constant:
            vectors[:] = [1, 0]
        sources = {}
        for name in ['development', 'reserved']:
            base = root / name
            base.mkdir()
            notes = np.array([name + str(i) for i in range(len(vectors))])
            np.savez(base / 'input.npz', vectors=vectors, notes=notes)
            (base / 'entries.json').write_text(json.dumps([
                dict(id=str(i), note_id=note, title='fixed', meaning='fixed',
                     source_group='G' + str(i // group_size))
                for i, note in enumerate(notes)]))
            sources[name] = dict(input=str(base / 'input.npz'), entries=str(base / 'entries.json'),
                files={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in [base / 'input.npz', base / 'entries.json']})
        spec = dict(sources=sources, counts=[1, 2, 3], seeds=[10, 11],
                    max_iterations=50, time_limit=30, cases=[
                        dict(id='D01', role='development', source='development',
                             selector={'kind': 'all'}, minimum_notes=0),
                        dict(id='V01', role='reserved', source='reserved',
                             selector={'kind': 'all'}, minimum_notes=0)])
        if preserve_groups:
            spec['cases'][0]['preserve_groups'] = True
            spec['cases'].append(dict(spec['cases'][0], id='D02', preserve_groups=False))
        (root / 'spec.json').write_text(json.dumps(spec))
        panel.prepare(root / 'spec.json', root / 'panel')
        panel.run(root / 'panel', 'D01')
        if preserve_groups:
            panel.run(root / 'panel', 'D02')
        return root / 'panel'

    def test_grouped_screen_uses_identical_reference_matrices_and_preserves_members(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self._panel(root, preserve_groups=True)
            plan = prepare(source, root / 'gap', references=8, seed=200,
                           cases=['D01', 'D02'], method='globalSEmax')
            run(root / 'gap', workers=2)
            groups = plan['cases'][0]['original_case']['groups']
            for i in range(8):
                a = json.loads((root / 'gap/D01' / f'reference-{i:03d}.json').read_text())
                b = json.loads((root / 'gap/D02' / f'reference-{i:03d}.json').read_text())
                self.assertEqual(a['reference_matrix_sha256'], b['reference_matrix_sha256'])
                for row in a['rows']:
                    self.assertEqual(len(set(zip(groups, row['labels']))), len(set(groups)))

    def test_one_preserved_group_stays_unsplit_without_reference_work(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self._panel(root, preserve_groups=True, group_size=24)
            prepare(source, root / 'gap', references=8, seed=200, cases=['D01'])
            result = run(root / 'gap', workers=1)
            self.assertEqual(result['cases'][0]['selected_count'], 1)
            self.assertEqual(result['cases'][0]['status'], 'single preserved group')
            self.assertFalse(list((root / 'gap/D01').glob('reference-*.json')))

    def test_dispersion_equals_published_pair_distance_definition(self):
        vectors = np.array([[1, 2], [3, 7], [8, 5], [9, 1]], dtype=float)
        labels = np.array([0, 0, 1, 1])
        expected = 0
        for k in [0, 1]:
            x = vectors[labels == k]
            expected += ((x[:, None] - x[None, :]) ** 2).sum() / (2 * len(x))
        self.assertAlmostEqual(dispersion(vectors, labels), expected)
        self.assertEqual(dispersion(vectors, np.arange(4)), 0)

    def test_published_one_standard_error_rule_includes_no_split(self):
        observed = [10, 4, 2]
        reference = np.exp(np.array([[3., 2., 1.], [3., 2., 1.]]))
        self.assertEqual(select_count([1, 2, 3], observed, reference)['selected_count'], 1)
        observed = [10, 1, .8]
        result = select_count([1, 2, 3], observed, reference)
        self.assertEqual(result['selected_count'], 2)
        np.testing.assert_allclose(result['gap'], [3 - np.log(10), 2, 1 - np.log(.8)])
        varied = np.exp(np.array([[3., 2.1, 1.], [3., 2.3, 1.]]))
        result = select_count([1, 2, 3], observed, varied)
        self.assertAlmostEqual(result['s'][1], .1 * np.sqrt(1.5))
        with self.assertRaisesRegex(ValueError, 'positive'):
            select_count([1, 2], [1, 0], np.ones((2, 2)))

    def test_global_rules_compare_later_peaks_without_changing_default(self):
        gap = np.array([.10, .08, .27, .30])
        error = np.array([.01, .02, .001, .06])
        delta = error / np.sqrt(1.5)
        reference = np.exp(np.array([-delta, delta]))
        observed = np.exp(-gap)
        counts = [1, 2, 3, 4]
        baseline = select_count(counts, observed, reference)
        self.assertEqual(baseline['selected_count'], 1)
        self.assertEqual(select_count(counts, observed, reference, method='globalmax')['selected_count'], 4)
        self.assertEqual(select_count(counts, observed, reference, method='globalSEmax')['selected_count'], 3)
        self.assertEqual(select_count(counts, observed, reference, method='adjacent'), baseline)
        with self.assertRaisesRegex(ValueError, 'Unknown'):
            select_count(counts, observed, reference, method='other')

    def test_global_rules_preserve_no_split_and_choose_first_tied_peak(self):
        reference = np.ones((2, 3))
        for method in ['globalmax', 'globalSEmax']:
            self.assertEqual(select_count([1, 2, 3], np.exp(-np.array([.3, .2, .1])),
                                          reference, method=method)['selected_count'], 1)
            self.assertEqual(select_count([1, 2, 3], np.exp(-np.array([.1, .3, .3])),
                                          reference, method=method)['selected_count'], 2)

    def test_cli_reuses_observed_fits_runs_references_and_leaves_reserved_alone(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self._panel(root)
            command = [sys.executable, '-m', 'sse_multivector.section_count_gap']
            prepared = subprocess.run(command + ['prepare', str(source), str(root / 'gap'),
                                      '--references', '8', '--seed', '200'],
                                      capture_output=True, text=True)
            self.assertEqual(prepared.returncode, 0, prepared.stderr)
            completed = subprocess.run(command + ['run', str(root / 'gap'), '--workers', '2'],
                                      capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = json.loads((root / 'gap/D01/result.json').read_text())
            self.assertEqual(result['selected_count'], 2)
            self.assertEqual(len(result['references']), 8)
            self.assertFalse((root / 'gap/V01').exists())
            self.assertFalse((source / 'V01').exists())
            before = (root / 'gap/D01/reference-000.json').read_bytes()
            saved = json.loads(before)
            self.assertEqual(saved['rows'][0]['trials'], [])
            run(root / 'gap', workers=1)
            self.assertEqual((root / 'gap/D01/reference-000.json').read_bytes(), before)
            saved['seed'] += 1
            (root / 'gap/D01/reference-000.json').write_text(json.dumps(saved))
            with self.assertRaisesRegex(ValueError, 'reference seed'):
                run(root / 'gap', workers=1)

    def test_identical_vectors_stop_without_random_reference_work(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self._panel(root, constant=True)
            prepare(source, root / 'gap', references=8, seed=200)
            result = run(root / 'gap', workers=1)
            self.assertEqual(result['cases'][0]['selected_count'], 1)
            self.assertEqual(result['cases'][0]['status'], 'zero observed dispersion')
            self.assertFalse(list((root / 'gap/D01').glob('reference-*.json')))

    def test_changed_observed_result_is_rejected_before_reference_work(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self._panel(root)
            prepare(source, root / 'gap', references=8, seed=200)
            (source / 'D01/count-2.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'Frozen source changed'):
                run(root / 'gap', workers=1)
            self.assertFalse(list((root / 'gap/D01').glob('reference-*.json')))

    def test_prepare_can_select_development_cases_without_changing_the_rule(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self._panel(root)
            result = prepare(source, root / 'subset', references=8, seed=200, cases=['D01'])
            self.assertEqual([c['id'] for c in result['cases']], ['D01'])
            self.assertEqual(result['role'], 'development')
            self.assertEqual(result['method'], 'adjacent')
            with self.assertRaisesRegex(ValueError, 'development cases'):
                prepare(source, root / 'bad', cases=['V01'])
            self.assertFalse((root / 'bad').exists())

    def test_cli_explicit_reserved_screen_freezes_and_applies_global_rule(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self._panel(root)
            with self.assertRaisesRegex(ValueError, 'explicit'):
                prepare(source, root / 'all-reserved', role='reserved')
            self.assertFalse((root / 'all-reserved').exists())
            with self.assertRaisesRegex(ValueError, 'reserved cases'):
                prepare(source, root / 'wrong-role', role='reserved', cases=['D01'])
            panel.run(source, 'V01')
            command = [sys.executable, '-m', 'sse_multivector.section_count_gap']
            prepared = subprocess.run(command + ['prepare', str(source), str(root / 'gap'),
                '--references', '8', '--seed', '200', '--role', 'reserved',
                '--method', 'globalSEmax', '--cases', 'V01'], capture_output=True, text=True)
            self.assertEqual(prepared.returncode, 0, prepared.stderr)
            plan = json.loads((root / 'gap/plan.json').read_text())
            self.assertEqual(plan['role'], 'reserved')
            self.assertEqual(plan['method'], 'globalSEmax')
            self.assertEqual([c['id'] for c in plan['cases']], ['V01'])
            self.assertEqual(plan['cases'][0]['original_case']['role'], 'reserved')
            completed = subprocess.run(command + ['run', str(root / 'gap'), '--workers', '2'],
                                       capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            cfg = plan['cases'][0]
            observed = [r['dispersion'] for r in cfg['observed']]
            values = [[r['dispersion'] for r in json.loads(
                (root / 'gap/V01' / f'reference-{i:03d}.json').read_text())['rows']]
                for i in range(8)]
            saved = json.loads((root / 'gap/V01/result.json').read_text())
            self.assertEqual(saved['selected_count'], select_count(
                cfg['counts'], observed, values, method='globalSEmax')['selected_count'])
            self.assertEqual(saved['separate_halves'], [select_count(
                cfg['counts'], observed, part, method='globalSEmax')['selected_count']
                for part in [values[:4], values[4:]]])
            self.assertFalse((root / 'gap/D01').exists())


if __name__ == '__main__':
    unittest.main()
