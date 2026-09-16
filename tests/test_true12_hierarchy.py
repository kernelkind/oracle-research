"""Package saved Coffee/Tea additions through the real category browser format."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT / 'sse_multivector'
RUN = CODE / 'navigation-research-v1/TRUE12'
BASE = CODE / 'navigation-research-v1/TRUE11/categories.json'
PACKAGER = CODE / 'true_membership_categories.py'
COFFEE = 'S9c440e7f47'
TEA = 'S78e7660d1d'


def read(path):
    return json.loads(path.read_text())


def recursive_notes(nodes, key):
    result = set(nodes[key]['note_ids'])
    for child in nodes[key]['children']:
        result.update(recursive_notes(nodes, child))
    return result


class TRUE12HierarchyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='true12-hierarchy-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.output = Path(cls.temp.name) / 'view'
        cls.inputs = [BASE, RUN / 'scores.jsonl', RUN / 'data/reviewed-input.json']
        before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in cls.inputs}
        result = subprocess.run(
            [sys.executable, str(PACKAGER), '--output', str(cls.output)],
            cwd='/', capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            raise AssertionError('Coffee/Tea hierarchy packaging failed: ' + result.stderr)
        if before != {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in cls.inputs}:
            raise AssertionError('packaging modified frozen inputs')
        cls.expanded = read(cls.output / 'categories.json')
        cls.baseline = read(cls.output / 'baseline-categories.json')
        cls.original = read(BASE)

    def test_expanded_memberships_are_additive_with_exact_expected_notes(self):
        nodes = {n['node_id']: n for n in self.expanded['nodes']}
        expected_coffee = {
            'N004', 'N005', 'N017', 'N018', 'N024', 'N029', 'N035', 'N036',
            'N038', 'N041', 'N043', 'N045', 'N048', 'N052', 'N058', 'N060',
            'N065', 'N071', 'N079', 'N086', 'N094', 'N095',
        }
        self.assertEqual(recursive_notes(nodes, COFFEE), expected_coffee)
        self.assertEqual(recursive_notes(nodes, TEA), {'N042', 'N072', 'N073', 'N080'})
        self.assertEqual(len(nodes[COFFEE]['note_ids']), 18)
        self.assertEqual(len(nodes[TEA]['note_ids']), 4)
        self.assertEqual(recursive_notes(nodes, 'root'), expected_coffee | {'N042', 'N072', 'N073', 'N080'})
        originals = {n['node_id']: n for n in self.original['nodes']}
        for key in (COFFEE, TEA):
            self.assertTrue(recursive_notes(originals, key) <= recursive_notes(nodes, key))

    def test_only_focus_root_and_memberships_change_not_category_links_or_children(self):
        nodes = {n['node_id']: n for n in self.expanded['nodes']}
        originals = {n['node_id']: n for n in self.original['nodes']}
        self.assertEqual(nodes['root']['children'], [COFFEE, TEA])
        children = originals[COFFEE]['children']
        self.assertEqual(set(nodes), {'root', COFFEE, TEA, *children})
        for key in (COFFEE, TEA, *children):
            self.assertEqual(nodes[key]['label'], originals[key]['label'])
            self.assertEqual(nodes[key]['children'], originals[key]['children'])
        for child in children:
            self.assertEqual(nodes[child], originals[child])
            self.assertEqual(self.expanded['note_masks'][child], self.original['note_masks'][child])
        self.assertNotIn('S8ea08f1aff', nodes, 'do not manually add the approved Music edge')

    def test_all_passing_masks_are_overlaid_without_sibling_or_rejected_masks(self):
        expected = {key: {note: {tuple(span) for span in spans}
                          for note, spans in self.original['note_masks'][key].items()}
                    for key in (COFFEE, TEA)}
        accepted_counts = {COFFEE: 0, TEA: 0}
        for line in (RUN / 'scores.jsonl').read_text().splitlines():
            row = json.loads(line)
            if row['entailment_score'] <= 0.142:
                continue
            for mask in row['masks']:
                accepted_counts[row['category_id']] += 1
                expected[row['category_id']].setdefault(mask['note_short_id'], set()).update(
                    tuple(span) for span in mask['byte_spans'])
        self.assertEqual(accepted_counts, {COFFEE: 70, TEA: 5})
        for key in (COFFEE, TEA):
            self.assertEqual(self.expanded['note_masks'][key],
                             {note: [list(span) for span in sorted(spans)]
                              for note, spans in expected[key].items()})
        self.assertEqual(self.expanded['note_masks'][TEA]['N080'],
                         self.original['note_masks'][TEA]['N080'])
        root_masks = {}
        for masks in expected.values():
            for note, spans in masks.items():
                root_masks.setdefault(note, set()).update(spans)
        self.assertEqual(self.expanded['note_masks']['root'],
                         {note: [list(span) for span in sorted(spans)]
                          for note, spans in root_masks.items()})

    def test_baseline_view_and_original_source_are_preserved(self):
        nodes = {n['node_id']: n for n in self.baseline['nodes']}
        self.assertEqual(len(recursive_notes(nodes, COFFEE)), 9)
        self.assertEqual(len(recursive_notes(nodes, TEA)), 2)
        originals = {n['node_id']: n for n in self.original['nodes']}
        for key in set(nodes) - {'root'}:
            self.assertEqual(nodes[key], originals[key])
            self.assertEqual(self.baseline['note_masks'][key], self.original['note_masks'][key])
        for spec in (self.baseline, self.expanded):
            self.assertEqual(spec['schema_version'], 2)
            self.assertEqual(spec['source_sha256'], self.original['source_sha256'])
            self.assertEqual(len(spec['notes']), len({n['note_id'] for n in spec['notes']}))

    def test_saved_view_passes_production_browser_validation(self):
        binary = ROOT / 'target/infomap-review-build/debug/sse-subject-navigation'
        if not binary.exists():
            self.skipTest('prebuilt browser unavailable; run launcher --check after building')
        for name, counts in [('categories.json', ('Coffee · 22 notes', 'Tea as a beverage · 4 notes')),
                             ('baseline-categories.json', ('Coffee · 9 notes', 'Tea as a beverage · 2 notes'))]:
            result = subprocess.run([str(binary), '--categories', str(self.output / name),
                                     str(RUN / 'data/reviewed-input.json'), '--check'],
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            for count in counts:
                self.assertIn(count, result.stdout)

    def test_packaging_refuses_to_overwrite_saved_view(self):
        before = (self.output / 'categories.json').read_bytes()
        result = subprocess.run([sys.executable, str(PACKAGER), '--output', str(self.output)],
                                capture_output=True, text=True, timeout=30)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(before, (self.output / 'categories.json').read_bytes())

    def test_packaging_is_byte_reproducible(self):
        outputs = []
        for seed in ('0', '1'):
            output = Path(self.temp.name) / ('replay-' + seed)
            result = subprocess.run([sys.executable, str(PACKAGER), '--output', str(output)],
                                    env={**os.environ, 'PYTHONHASHSEED': seed},
                                    capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            outputs.append({name: (output / name).read_bytes() for name in
                            ('categories.json', 'baseline-categories.json', 'manifest.json')})
        self.assertEqual(outputs[0], outputs[1])


class TRUE12HierarchyLauncherTests(unittest.TestCase):
    def setUp(self):
        self.launcher = CODE / 'run-true12-hierarchy.sh'
        self.assertTrue(self.launcher.is_file(), 'Coffee/Tea hierarchy launcher is missing')
        temporary = tempfile.TemporaryDirectory(prefix='true12 viewer ')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.script = self.root / 'sse_multivector/run-true12-hierarchy.sh'
        self.script.parent.mkdir(parents=True)
        shutil.copy2(self.launcher, self.script)
        self.binary = self.root / 'target/infomap-review-build/debug/sse-subject-navigation'
        self.binary.parent.mkdir(parents=True)
        self.binary.write_text('#!/usr/bin/env bash\nprintf "%s\\n" "$@"\nexit 23\n')
        self.binary.chmod(0o755)

    def test_expanded_and_baseline_options_resolve_from_any_working_directory(self):
        for options, filename in [([], 'categories.json'),
                                  (['--baseline'], 'baseline-categories.json')]:
            result = subprocess.run(['bash', str(self.script), *options, '--check'], cwd='/',
                                    capture_output=True, text=True, timeout=5)
            self.assertEqual(result.returncode, 23, result.stderr)
            self.assertEqual(result.stdout.splitlines(), [
                '--categories',
                str(self.root / 'sse_multivector/navigation-research-v1/TRUE12/hierarchy' / filename),
                str(self.root / 'sse_multivector/navigation-research-v1/TRUE12/data/reviewed-input.json'),
                '--check',
            ])

    def test_bad_option_is_rejected_without_launching(self):
        result = subprocess.run(['bash', str(self.script), '--wrong'], capture_output=True,
                                text=True, timeout=5)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, '')
        self.assertIn('Usage:', result.stderr)

    def test_missing_binary_prints_build_instruction_without_building(self):
        self.binary.unlink()
        result = subprocess.run(['bash', str(self.script)], capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 1)
        self.assertIn('--bin sse-subject-navigation', result.stderr)
        self.assertFalse(self.binary.exists())


if __name__ == '__main__':
    unittest.main()
