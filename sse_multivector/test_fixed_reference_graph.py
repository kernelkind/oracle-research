import unittest

import numpy as np
from scipy import sparse

from sse_multivector.fixed_reference_graph import derive_boundary, qualify_boundary


def graph(size, edges):
    rows, columns, weights = [], [], []
    for a, b, weight in edges:
        rows.extend((a, b))
        columns.extend((b, a))
        weights.extend((weight, weight))
    return sparse.csr_matrix((weights, (rows, columns)), shape=(size, size))


def affinities(size=8):
    a = np.eye(size)
    a[0, 1] = a[1, 0] = .95
    for i in range(2, size):
        a[i, :2] = a[:2, i] = 1 - .1 * i
    return a


def neighborhoods():
    return graph(8, [(0, 1, 1), (0, 2, 1), (1, 2, 1), (2, 3, .02),
                     (3, 4, 1), (3, 5, 1), (4, 5, 1), (6, 7, 1)])


class FixedReferenceGraphTests(unittest.TestCase):
    def test_reference_connections_choose_gap_in_unchanged_mean_scores(self):
        a = affinities()
        notes = list('abcdefgh')
        result = derive_boundary(a, notes, [0, 1], neighborhoods())
        self.assertEqual(result['status'], 'boundary')
        self.assertEqual(result['selected_indices'], [0, 1, 2])
        self.assertAlmostEqual(result['threshold'], .75)
        self.assertAlmostEqual(result['curve'][1]['cut'], .02)
        self.assertAlmostEqual(result['curve'][1]['volume'], 6.02)
        self.assertAlmostEqual(result['curve'][1]['conductance'], .02 / 6.02)
        larger = graph(8, [(a, b, 1) for start in [0, 4]
                           for a in range(start, start + 4)
                           for b in range(a + 1, start + 4)] + [(3, 4, .02)])
        other = derive_boundary(a, notes, [0, 1], larger)
        self.assertAlmostEqual(other['threshold'], .65)
        self.assertEqual([r['score'] for r in result['curve']],
                         [r['score'] for r in other['curve']])

    def test_uniform_graph_has_no_false_valley_at_half_volume(self):
        uniform = graph(8, [(a, b, 1) for a in range(8) for b in range(a + 1, 8)])
        result = derive_boundary(affinities(), list('abcdefgh'), [0, 1], uniform)
        self.assertEqual(result['status'], 'no_resolved_minimum')
        self.assertIsNone(result['threshold'])

    def test_whole_source_note_is_excluded_from_scores_graph_and_folds(self):
        a, g, notes = affinities(), neighborhoods(), list('abcdeefg')
        result = derive_boundary(a, notes, [0, 1, 4, 5], g, excluded_notes={'e'})
        reduced = derive_boundary(a[np.ix_([0, 1, 2, 3, 6, 7], [0, 1, 2, 3, 6, 7])],
                                  list('abcdfg'), [0, 1], g[[0, 1, 2, 3, 6, 7]][:, [0, 1, 2, 3, 6, 7]])
        self.assertEqual(result['threshold'], reduced['threshold'])
        self.assertEqual(result['group_indices'], [0, 1])
        self.assertEqual(result['context_indices'], [0, 1, 2, 3, 6, 7])
        model = qualify_boundary(a, notes, [0, 1, 4, 5], g)
        fold = next(f for f in model['folds'] if f['excluded_note'] == 'e')
        self.assertEqual(fold['boundary'], result)
        self.assertEqual(fold['held_indices'], [4, 5])

    def test_scaling_permutation_ties_and_inputs_are_preserved(self):
        a, g, notes = affinities(), neighborhoods(), list('abcdefgh')
        original = g.copy()
        base = derive_boundary(a, notes, [0, 1], g)
        scaled = derive_boundary(a, notes, [0, 1], 17 * g)
        self.assertEqual(base['threshold'], scaled['threshold'])
        self.assertEqual((g != original).nnz, 0)
        order = [7, 1, 3, 0, 6, 4, 2, 5]
        moved = derive_boundary(a[np.ix_(order, order)], [notes[i] for i in order],
                                [order.index(0), order.index(1)], g[order][:, order])
        self.assertEqual(base['threshold'], moved['threshold'])
        self.assertEqual({order[i] for i in moved['selected_indices']}, {0, 1, 2})
        self.assertEqual(base['curve'][0]['indices'], [0, 1])

    def test_isolated_or_empty_reference_does_not_invent_boundary(self):
        result = derive_boundary(affinities(), list('abcdefgh'), [0, 1], sparse.csr_matrix((8, 8)))
        self.assertEqual(result['status'], 'no_edges')
        self.assertIsNone(result['threshold'])
        empty = derive_boundary(affinities(), list('abcdefgh'), [0, 1], neighborhoods(),
                                 excluded_notes={'a', 'b'})
        self.assertEqual(empty['status'], 'no_group_reference')

    def test_invalid_graph_and_affinity_are_rejected(self):
        with self.assertRaises(ValueError):
            derive_boundary(affinities(), list('abcdefgh'), [0, 1], sparse.eye(7))
        asymmetry = neighborhoods().tolil()
        asymmetry[0, 1] = 2
        with self.assertRaises(ValueError):
            derive_boundary(affinities(), list('abcdefgh'), [0, 1], asymmetry)
        a = affinities()
        a[0, 1] = .2
        with self.assertRaises(ValueError):
            derive_boundary(a, list('abcdefgh'), [0, 1], neighborhoods())


if __name__ == '__main__':
    unittest.main()
