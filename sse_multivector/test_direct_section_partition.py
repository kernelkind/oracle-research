"""Check the same note-constrained assignment used by the numerical CLI."""
import itertools
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np

from sse_multivector.direct_section_partition import assign, partition


class AssignmentTests(unittest.TestCase):
    def test_whole_groups_use_summed_entry_cost_and_real_note_counts(self):
        costs = np.array([[0., 1.], [10., 0.], [0., 2.]])
        result = assign(costs, ['a', 'b', 'c'], minimum_notes=0, groups=[0, 0, 1])
        self.assertEqual(result['labels'], [1, 1, 0])
        self.assertEqual(result['section_notes'], [1, 2])
        self.assertAlmostEqual(result['objective'], 1)
        for bad in [[0, 1], [[0], [0], [1]]]:
            with self.assertRaises(ValueError):
                assign(costs, ['a', 'b', 'c'], minimum_notes=0, groups=bad)
        with self.assertRaisesRegex(ValueError, 'zero note minimum'):
            assign(costs, ['a', 'b', 'c'], minimum_notes=1, groups=[0, 0, 1])

    def test_minimum_counts_distinct_notes_instead_of_entries(self):
        costs = np.column_stack([np.zeros(6), np.arange(1, 7) / 10])
        notes = ['a', 'a', 'a', 'b', 'c', 'd']
        result = assign(costs, notes, minimum_notes=2)
        labels = np.asarray(result['labels'])
        self.assertEqual(labels.tolist(), [1, 0, 0, 1, 0, 0])
        self.assertAlmostEqual(result['objective'], .5)
        self.assertEqual(result['section_notes'], [3, 2])

    def test_assignment_matches_exhaustive_optimum_with_shared_notes(self):
        notes = ['a', 'a', 'b', 'c', 'd', 'd']
        candidates = []
        for labels in itertools.product(range(3), repeat=len(notes)):
            if all(len({n for n, label in zip(notes, labels) if label == k}) >= 2
                   for k in range(3)):
                candidates.append(labels)
        self.assertTrue(candidates)
        for seed in range(8):
            costs = np.random.default_rng(seed).uniform(-1, 2, size=(6, 3))
            expected = min(sum(costs[i, label] for i, label in enumerate(labels))
                           for labels in candidates)
            result = assign(costs, notes, minimum_notes=2)
            self.assertAlmostEqual(result['objective'], expected)
            self.assertGreaterEqual(min(result['section_notes']), 2)

    def test_impossible_note_distribution_is_rejected(self):
        # Six entries and four notes suffice in aggregate, but only note a can
        # appear in both sections: at most five distinct note/section witnesses.
        with self.assertRaisesRegex(ValueError, 'No optimal'):
            assign(np.ones((6, 2)), ['a', 'a', 'a', 'b', 'c', 'd'], minimum_notes=3)

    def test_existing_valid_nearest_assignments_are_preserved(self):
        result = assign([[0, 1], [0, 1], [1, 0], [1, 0]], ['a', 'b', 'a', 'c'],
                        minimum_notes=2)
        self.assertEqual(result['labels'], [0, 0, 1, 1])
        self.assertEqual(result['objective'], 0)
        self.assertEqual(result['section_notes'], [2, 2])

    def test_invalid_inputs_cannot_inflate_counts_or_bypass_assignment(self):
        for costs, notes, minimum in [([[0, 1]], ['a'], 2),
                                      ([[0, 1]], [], 0),
                                      ([[0, np.nan]], ['a'], 0),
                                      ([[0, 1]], ['a'], -1)]:
            with self.assertRaises(ValueError):
                assign(costs, notes, minimum_notes=minimum)


class PartitionTests(unittest.TestCase):
    def test_partition_keeps_original_group_members_together(self):
        vectors = np.eye(2)[[0, 0, 1, 0, 1, 1]]
        groups = [0, 0, 0, 1, 1, 1]
        result = partition(vectors, np.arange(6), sections=2, minimum_notes=0,
                           seed=12, groups=groups)
        labels = result['labels']
        self.assertEqual(len(set(labels[:3])), 1)
        self.assertEqual(len(set(labels[3:])), 1)
        self.assertNotEqual(labels[0], labels[3])
        self.assertEqual(result['section_notes'], [3, 3])
        self.assertTrue(result['converged'])
        trace = [r['objective'] for r in result['trace']]
        self.assertTrue(all(b <= a + 1e-8 for a, b in zip(trace, trace[1:])))
        with self.assertRaisesRegex(ValueError, 'groups'):
            partition(vectors, np.arange(6), sections=3, minimum_notes=0,
                      seed=12, groups=groups)

    def test_separated_meanings_are_recovered_without_discarding_entries(self):
        vectors = np.repeat(np.eye(3), 6, axis=0)
        notes = np.arange(18)
        before = vectors.copy()
        result = partition(vectors, notes, sections=3, minimum_notes=5, seed=17)
        labels = np.array(result['labels'])
        self.assertEqual(sorted(result['section_notes']), [6, 6, 6])
        self.assertEqual(len(labels), len(vectors))
        self.assertTrue(result['converged'])
        self.assertAlmostEqual(result['objective'], 0)
        self.assertEqual(len(set(labels[:6])), 1)
        self.assertEqual(len(set(labels[6:12])), 1)
        self.assertEqual(len(set(labels[12:])), 1)
        np.testing.assert_equal(vectors, before)

    def test_minimum_is_applied_during_clustering_and_cost_never_increases(self):
        vectors = np.repeat(np.eye(3), [8, 2, 2], axis=0)
        result = partition(vectors, np.arange(12), sections=3, minimum_notes=4, seed=12)
        self.assertEqual(result['section_notes'], [4, 4, 4])
        self.assertGreater(len(result['displaced_indices']), 0)
        costs = [r['objective'] for r in result['trace']]
        self.assertTrue(all(b <= a + 1e-8 for a, b in zip(costs, costs[1:])))
        again = partition(vectors, np.arange(12), sections=3, minimum_notes=4, seed=12)
        self.assertEqual(result['labels'], again['labels'])
        self.assertEqual(result['objective'], again['objective'])

    def test_cli_retains_inputs_and_freezes_shared_control_initialization(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            inputs, output = base / 'input.npz', base / 'out'
            np.savez(inputs, vectors=np.repeat(np.eye(3), 6, axis=0), notes=np.arange(18))
            command = [sys.executable, '-m', 'sse_multivector.direct_section_partition',
                       str(inputs), str(output), '--sections', '3', '--minimum-notes', '5',
                       '--minimum-total-notes', '18', '--starts', '2']
            subprocess.run(command, check=True, capture_output=True, text=True)
            a = json.loads((output / 'constrained.json').read_text())
            b = json.loads((output / 'unconstrained.json').read_text())
            plan = json.loads((output / 'plan.json').read_text())
            self.assertEqual(plan['minimum_total_notes'], 18)
            self.assertEqual(a['covered_notes'], 18)
            for ar, br in zip(a['trials'], b['trials']):
                self.assertEqual(ar['initial_indices'], br['initial_indices'])
            self.assertEqual(len(a['best']['labels']), 18)
            failed = subprocess.run(command[:-4] + ['--minimum-total-notes', '19'],
                                    capture_output=True, text=True)
            self.assertNotEqual(failed.returncode, 0)

    def test_invalid_vectors_are_rejected(self):
        with self.assertRaises(ValueError):
            partition([[0, 0], [1, 0]], ['a', 'b'], sections=2, minimum_notes=1, seed=0)


if __name__ == '__main__':
    unittest.main()
