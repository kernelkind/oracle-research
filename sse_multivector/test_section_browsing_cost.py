"""Hand-worked checks of the offline browsing-cost diagnostic and its CLI."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np

from sse_multivector.section_browsing_cost import analyze, summarize


class BrowsingCostTests(unittest.TestCase):
    def test_disjoint_children_save_one_note_inspection_before_menu_cost(self):
        result = summarize(['a', 'b', 'c', 'd'], [0, 0, 1, 1])
        self.assertEqual(result['parent_notes'], 4)
        self.assertEqual(result['child_note_counts'], [2, 2])
        self.assertEqual(result['flat_expected_note_inspections'], 2.5)
        for profile in result['conditional_profiles'].values():
            self.assertEqual(profile['expected_note_inspections'], 1.5)
            self.assertEqual(profile['maximum_extra_navigation_cost'], 1)

    def test_overlap_counts_each_target_once_and_bounds_valid_routes(self):
        result = summarize(['a', 'b', 'c', 'a'], [0, 0, 0, 1])
        profiles = result['conditional_profiles']
        self.assertEqual(result['parent_notes'], 3)
        self.assertEqual(result['extra_note_child_memberships'], 1)
        self.assertAlmostEqual(profiles['best_valid']['expected_note_inspections'], 5 / 3)
        self.assertAlmostEqual(profiles['uniform_valid']['expected_note_inspections'], 11 / 6)
        self.assertEqual(profiles['worst_valid']['expected_note_inspections'], 2)
        self.assertFalse(result['all_children_narrow'])

    def test_repeated_entries_do_not_inflate_a_notes_weight(self):
        base = summarize(['a', 'b', 'c', 'a'], [0, 0, 0, 1])
        repeated = summarize(['a', 'b', 'c', 'a', 'a', 'a'], [0, 0, 0, 1, 1, 0])
        self.assertEqual(base, repeated)

    def test_identical_child_note_sets_save_nothing(self):
        result = summarize(['a', 'b', 'a', 'b'], [0, 0, 1, 1])
        self.assertFalse(result['distinct_child_note_sets'])
        self.assertFalse(result['all_children_narrow'])
        for profile in result['conditional_profiles'].values():
            self.assertEqual(profile['maximum_extra_navigation_cost'], 0)

    def test_shuffling_meaningless_memberships_can_leave_cost_exactly_unchanged(self):
        # One entry per note: six two-note lists cost the same regardless of
        # which unrelated topics the shuffled children mix together.
        result = analyze([str(i) for i in range(12)], np.repeat(np.arange(6), 2),
                         shuffles=8, seed=7)
        observed = result['observed']['conditional_profiles']
        for trial in result['shuffled_memberships']:
            self.assertEqual(trial['conditional_profiles'], observed)
            self.assertEqual(trial['child_entry_counts'], [2] * 6)
        self.assertEqual(result, analyze([str(i) for i in range(12)],
                                        np.repeat(np.arange(6), 2), shuffles=8, seed=7))

    def test_invalid_or_misaligned_memberships_are_rejected(self):
        for notes, labels in [([], []), (['a'], []), ([''], [0]),
                              (['a'], [-1]), (['a'], [1]), (['a'], [.5])]:
            with self.subTest(notes=notes, labels=labels), self.assertRaises(ValueError):
                summarize(notes, labels)
        with self.assertRaises(ValueError):
            analyze(['a'], [0], shuffles=0, seed=0)

    def test_cli_freezes_sources_and_does_not_change_saved_experiment(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / 'source'
            (source / 'direct').mkdir(parents=True)
            np.savez(source / 'input.npz', notes=np.array(['a', 'b', 'c', 'd']))
            checksum = hashlib.sha256((source / 'input.npz').read_bytes()).hexdigest()
            (source / 'plan.json').write_text(json.dumps({'input_sha256': checksum}))
            (source / 'direct/constrained.json').write_text(json.dumps({
                'best': {'labels': [0, 0, 1, 1], 'section_notes': [2, 2]}}))
            before = {p: p.read_bytes() for p in source.rglob('*') if p.is_file()}
            output = base / 'output'
            command = [sys.executable, '-m', 'sse_multivector.section_browsing_cost',
                       str(source), str(output), '--shuffles', '8', '--seed', '7']
            subprocess.run(command, check=True, capture_output=True, text=True)
            saved = json.loads((output / 'result.json').read_text())
            self.assertEqual(saved['observed']['parent_notes'], 4)
            self.assertEqual(len(saved['shuffled_memberships']), 8)
            frozen = json.loads((output / 'plan.json').read_text())
            self.assertEqual(frozen['sources'][str(source / 'input.npz')], checksum)
            self.assertEqual(before, {p: p.read_bytes() for p in before})
            self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)
            (source / 'input.npz').write_bytes(b'changed')
            failed = subprocess.run(command[:4] + [str(base / 'bad')]
                                    + command[5:], capture_output=True, text=True)
            self.assertNotEqual(failed.returncode, 0)
            self.assertFalse((base / 'bad').exists())


if __name__ == '__main__':
    unittest.main()
