"""Outside queries use both representations without modifying accepted graphs."""
import unittest

import numpy as np
from scipy import sparse

from sse_multivector.fixed_reference_query import query_support


class FixedReferenceQueryTests(unittest.TestCase):
    def test_connected_title_and_meaning_matches_combine(self):
        accepted=sparse.csr_matrix([[9.,1.],[1.,9.]])
        title=sparse.csr_matrix([[1.,0.]])
        meaning=sparse.csr_matrix([[0.,1.]])
        np.testing.assert_allclose(query_support(title,meaning,accepted),[np.sqrt(.5)])
        np.testing.assert_allclose(query_support(title,title,accepted),[0.])

    def test_matches_to_disconnected_parts_do_not_reinforce_each_other(self):
        accepted=sparse.csr_matrix([[1.,1.,0.,0.],[1.,1.,0.,0.],
                                    [0.,0.,1.,1.],[0.,0.,1.,1.]])
        title=sparse.csr_matrix([[1.,0.,0.,0.]])
        meaning=sparse.csr_matrix([[0.,0.,1.,0.]])
        np.testing.assert_array_equal(query_support(title,meaning,accepted),[0.])

    def test_queries_are_independent_and_inputs_stay_unchanged(self):
        accepted=sparse.csr_matrix([[7.,2.,1.],[2.,7.,3.],[1.,3.,7.]])
        title=sparse.csr_matrix([[.1,.2,.3],[.9,.8,.7]])
        meaning=sparse.csr_matrix([[.3,.5,.2],[.1,.6,.4]])
        originals=[a.copy() for a in [accepted,title,meaning]]
        together=query_support(title,meaning,accepted)
        apart=np.concatenate([query_support(title[i:i+1],meaning[i:i+1],accepted) for i in range(2)])
        np.testing.assert_allclose(together,apart)
        for a,b in zip([accepted,title,meaning],originals):
            np.testing.assert_array_equal(a.toarray(),b.toarray())
        np.testing.assert_allclose(together,query_support(meaning,title,accepted))

    def test_explicit_weighted_pair_sum_matches(self):
        accepted=sparse.csr_matrix([[0.,2.,0.],[2.,0.,1.],[0.,1.,0.]])
        t=np.array([.2,.8,.4]);m=np.array([.7,.3,.9])
        expected=np.sqrt((2*(t[0]*m[1]+t[1]*m[0])+(t[1]*m[2]+t[2]*m[1]))/6)
        np.testing.assert_allclose(query_support(sparse.csr_matrix(t[None]),
                                                 sparse.csr_matrix(m[None]),accepted),[expected])

    def test_self_connections_alone_are_unavailable(self):
        a=sparse.eye(3,format='csr');q=sparse.csr_matrix([[.1,.2,.3]])
        self.assertTrue(np.isnan(query_support(q,q,a)[0]))

    def test_invalid_affinities_and_alignment_are_rejected(self):
        a=sparse.csr_matrix([[0.,1.],[1.,0.]])
        for q in [sparse.csr_matrix([[np.nan,.3]]),sparse.csr_matrix([[-.1,.3]]),
                  sparse.csr_matrix([[1.1,.3]])]:
            with self.assertRaises(ValueError):query_support(q,q,a)
        with self.assertRaises(ValueError):query_support(sparse.eye(2),sparse.eye(3),a)
        with self.assertRaises(ValueError):query_support(sparse.eye(2),sparse.eye(2),sparse.csr_matrix([[0.,1.],[0.,0.]]))


if __name__=='__main__':
    unittest.main()
