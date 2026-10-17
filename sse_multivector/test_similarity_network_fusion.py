"""Numerical contracts for the experimental bounded-neighbor fusion path."""
import unittest

import numpy as np
from scipy import sparse

from sse_multivector.similarity_network_fusion import local_graph, fuse, cluster


class FusionTests(unittest.TestCase):
    def test_unpruned_exchange_matches_dense_reference_equations(self):
        a = np.array([[1., .8, .2, .1], [.8, 1., .3, .2],
                      [.2, .3, 1., .9], [.1, .2, .9, 1.]])
        b = np.array([[1., .4, .1, .2], [.4, 1., .2, .1],
                      [.1, .2, 1., .7], [.2, .1, .7, 1.]])
        states = []
        for v in [a, b]:
            v = v / v.sum(axis=1, keepdims=True)
            states.append((v + v.T) / 2)
        transitions = [v / v.sum(axis=1, keepdims=True) for v in states]
        for _ in range(3):
            states = [(transitions[j] @ states[1-j] @ transitions[j].T + np.eye(4)) for j in range(2)]
            states = [(v + v.T) / 2 for v in states]
        expected = (states[0] + states[1]) / 2
        expected = expected / expected.sum(axis=1, keepdims=True)
        expected = (expected + expected.T + np.eye(4)) / 2
        out, _ = fuse([sparse.csr_matrix(a), sparse.csr_matrix(b)], neighbors=3, iterations=3)
        np.testing.assert_allclose(out.toarray(), expected, atol=1e-13)

    def test_degree_bound_and_view_order_invariance(self):
        rng = np.random.default_rng(42)
        a = local_graph(rng.normal(size=(40, 8)), neighbors=4)
        b = local_graph(rng.normal(size=(40, 8)), neighbors=4)
        before = [v.copy() for v in [a, b]]
        out, trace = fuse([a, b], neighbors=4, iterations=4)
        reverse, _ = fuse([b, a], neighbors=4, iterations=4)
        np.testing.assert_allclose(out.toarray(), reverse.toarray(), atol=1e-14)
        for x, z in zip([a, b], before):
            np.testing.assert_array_equal(x.toarray(), z.toarray())
        self.assertLessEqual(max(np.diff(out.indptr)), 5)
        self.assertTrue(np.all(np.isfinite(out.data)))
        self.assertTrue(np.all(out.data >= 0))
        self.assertEqual((out-out.T).nnz, 0)
        self.assertLessEqual(max(r['largest_product_nnz'] for r in trace), 40 * 5 * 5)

    def test_identical_views_do_not_depend_on_exchange(self):
        rng = np.random.default_rng(9)
        a = local_graph(rng.normal(size=(24, 6)), neighbors=5)
        cross, _ = fuse([a, a], neighbors=5, iterations=3, exchange=True)
        own, _ = fuse([a, a], neighbors=5, iterations=3, exchange=False)
        np.testing.assert_allclose(cross.toarray(), own.toarray(), atol=1e-14)

    def test_zero_iterations_still_preserves_isolated_entries(self):
        a = sparse.eye(5, format='csr')
        out, trace = fuse([a, a], neighbors=2, iterations=0)
        np.testing.assert_array_equal(out.toarray(), np.eye(5) * 1.5)
        groups, noise, _ = cluster(out)
        self.assertEqual(groups, [])
        self.assertEqual(noise, list(range(5)))
        self.assertEqual(len(trace), 1)

    def test_clustering_preserves_disconnected_groups_without_inventing_edges(self):
        a = sparse.block_diag([sparse.csr_matrix(np.ones((3, 3))),
                               sparse.csr_matrix(np.ones((3, 3))), sparse.eye(1)], format='csr')
        groups, noise, _ = cluster(a)
        self.assertEqual(groups, [[0, 1, 2], [3, 4, 5]])
        self.assertEqual(noise, [6])

    def test_invalid_vectors_and_controls_fail(self):
        for a in [np.zeros((4, 2)), np.array([[1., 0.], [np.nan, 1.]])]:
            with self.assertRaises(ValueError):
                local_graph(a, neighbors=2)
        with self.assertRaises(ValueError):
            fuse([sparse.eye(4), sparse.eye(5)], neighbors=2)


if __name__ == '__main__':
    unittest.main()
