import unittest

import numpy as np
from scipy import sparse

from sse_multivector.local_graph_expansion import expand


def graph(size, edges):
    rows, columns, weights = [], [], []
    for a, b, weight in edges:
        rows.extend((a, b))
        columns.extend((b, a))
        weights.extend((weight, weight))
    return sparse.csr_matrix((weights, (rows, columns)), shape=(size, size))


class LocalGraphExpansionTests(unittest.TestCase):
    def test_stops_between_strongly_connected_neighborhoods(self):
        g = graph(8, [(0, 1, 1), (0, 2, 1), (1, 2, 1), (2, 3, .02),
                      (3, 4, 1), (3, 5, 1), (4, 5, 1), (6, 7, 1)])
        before = g.copy()
        result = expand(g, {0: .5, 1: .5})
        self.assertEqual(set(result['selected']), {0, 1, 2})
        row = next(r for r in result['curve'] if r['size'] == 3)
        self.assertAlmostEqual(row['cut'], .02)
        self.assertAlmostEqual(row['volume'], 6.02)
        self.assertAlmostEqual(row['conductance'], .02 / 6.02)
        self.assertEqual((before != g).nnz, 0)
        self.assertAlmostEqual(sum(result['pagerank']), 1)

    def test_zero_boundary_keeps_seed_group_without_forced_expansion(self):
        g = graph(4, [(0, 1, 2), (2, 3, 3)])
        result = expand(g, {0: .5, 1: .5})
        self.assertEqual(set(result['selected']), {0, 1})
        self.assertEqual(result['status'], 'seed_only')
        self.assertEqual(result['best']['conductance'], 0)

    def test_isolated_seeds_do_not_acquire_unrelated_entries(self):
        result = expand(graph(4, [(2, 3, 1)]), {0: 1})
        self.assertEqual(result['selected'], [0])
        self.assertEqual(result['status'], 'no_edges')

    def test_uniform_scaling_does_not_change_selected_boundary(self):
        g = graph(8, [(0, 1, 1), (0, 2, 1), (1, 2, 1), (2, 3, .02),
                      (3, 4, 1), (3, 5, 1), (4, 5, 1), (6, 7, 1)])
        a, b = expand(g, {0: .5, 1: .5}), expand(17 * g, {0: .5, 1: .5})
        self.assertEqual(a['selected'], b['selected'])
        self.assertAlmostEqual(a['best']['conductance'], b['best']['conductance'])

    def test_repeated_queries_do_not_change_the_graph_or_each_other(self):
        g = graph(6, [(0, 1, 1), (1, 2, 1), (2, 3, .05), (3, 4, 1), (4, 5, 1)])
        a = expand(g, {0: 1})
        expand(g, {5: 1})
        b = expand(g, {0: 1})
        self.assertEqual(a['selected'], b['selected'])
        np.testing.assert_array_equal(a['pagerank'], b['pagerank'])

    def test_rejects_invalid_graphs_and_seeds(self):
        for g, seeds in [(sparse.csr_matrix([[0, 1], [0, 0]]), {0: 1}),
                         (graph(2, [(0, 1, -1)]), {0: 1}),
                         (graph(2, [(0, 1, 1)]), {}),
                         (graph(2, [(0, 1, 1)]), {2: 1})]:
            with self.subTest(seeds=seeds):
                with self.assertRaises(ValueError):
                    expand(g, seeds)


if __name__ == '__main__':
    unittest.main()
