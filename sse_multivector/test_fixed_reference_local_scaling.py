"""Local-affinity research through its actual scoring/boundary path."""
import math
import unittest
import numpy as np
from sse_multivector.fixed_reference_local_scaling import affinities, neighbor_scales
from sse_multivector.fixed_reference_bend import mean_support
from sse_multivector.fixed_reference_members import derive_boundary
from sse_multivector.similarity_network_fusion import local_graph


def directions(angles):
    return np.array([[math.cos(a), math.sin(a)] for a in angles])


class LocalScalingTests(unittest.TestCase):
    def test_closest_distinct_other_notes_define_the_scale(self):
        c=np.cos([[0., .05, .1, .3, .6, .9]])
        actual=neighbor_scales(c,['a'],['a','b','b','c','d','d'],neighbors=2)
        self.assertAlmostEqual(actual[0],(.05+.3)/2)

    def test_repeating_reference_from_the_same_note_does_not_add_neighbor_mass(self):
        c=np.cos([[.2,.4,.7],[.1,.5,.6]])
        baseline=neighbor_scales(c,['x','y'],['a','b','c'],neighbors=2)
        copied=neighbor_scales(c[:,[0,1,2,0]],['x','y'],['a','b','c','a'],neighbors=2)
        np.testing.assert_array_equal(baseline,copied)

    def test_each_query_is_independent_and_inputs_do_not_change(self):
        c=np.cos([[.1,.3,.7],[1.1,.8,.5]])
        old=c.copy();notes=['x','y'];refs=['a','b','c'];rs=np.array([.4,.5,.6])
        scales=neighbor_scales(c,notes,refs)
        together=affinities(c,scales,rs)
        for i in range(2):
            alone=affinities(c[i:i+1],neighbor_scales(c[i:i+1],notes[i:i+1],refs),rs)
            np.testing.assert_array_equal(alone[0],together[i])
        order=[1,0,0]
        reordered=affinities(c[order],neighbor_scales(c[order],[notes[i]for i in order],refs),rs)
        np.testing.assert_array_equal(reordered,together[order]);np.testing.assert_array_equal(c,old)

    def test_no_other_note_is_unavailable_and_exact_duplicate_angles_use_numeric_floor(self):
        self.assertTrue(np.isnan(neighbor_scales([[1.,.5]],['a'],['a','a'])[0]))
        r=neighbor_scales([[1.,1.]],['a'],['b','c'])
        self.assertEqual(r[0],np.finfo(float).eps)
        np.testing.assert_array_equal(affinities([[1.]],r,r),[[1.]])

    def test_self_normalized_kernel_has_unit_self_and_matches_scalar_equation(self):
        rho=np.array([.4,.8]);c=np.array([[1.,.5],[.5,1.]])
        a=affinities(c,rho,rho)
        np.testing.assert_allclose(a,a.T,atol=0,rtol=0)
        np.testing.assert_array_equal(np.diag(a),[1.,1.])
        d=math.acos(.5);scale=.5*(.4+.8+d)/3
        expected=(2*math.sqrt(.4*.8)/(.4+.8+d))*math.exp(-.5*(d/scale)**2)
        self.assertAlmostEqual(a[0,1],expected)
        self.assertTrue(np.all((a>=0)&(a<=1)))

    def test_matches_normalized_existing_fusion_kernel_with_distinct_notes(self):
        v=directions([0.,.3,.7,1.2]);c=np.clip(v@v.T,-1,1);np.fill_diagonal(c,1.)
        rho=neighbor_scales(c,list('abcd'),list('abcd'),neighbors=3)
        graph=local_graph(v,neighbors=3,sigma=.5).toarray()
        normalized=graph/np.sqrt(np.outer(graph.diagonal(),graph.diagonal()))
        np.testing.assert_allclose(affinities(c,rho,rho),normalized,atol=1e-14,rtol=1e-14)

    def test_same_cosine_changes_with_local_context(self):
        narrow=affinities([[.5]],[.3],[.3])[0,0]
        broad=affinities([[.5]],[.8],[.8])[0,0]
        self.assertGreater(broad,narrow)

    def test_existing_group_mean_and_minimum_boundary_use_the_new_affinities(self):
        r=directions([0.,.3,.7,1.2]);q=directions([.1,2.5]);notes=list('abcd')
        rc=np.clip(r@r.T,-1,1);np.fill_diagonal(rc,1.)
        qc=np.clip(q@r.T,-1,1)
        rs=neighbor_scales(rc,notes,notes);qs=neighbor_scales(qc,['x','y'],notes)
        boundary=derive_boundary(affinities(rc,rs,rs),notes,[0,1])
        scores=mean_support(affinities(qc,qs,rs),['x','y'],notes,[0,1])
        np.testing.assert_array_equal(scores>=boundary['threshold'],[True,False])

    def test_invalid_shapes_notes_cosines_scales_and_controls_are_rejected(self):
        for c,qn,rn,k in [([1.],['a'],['b'],1),([[1.]],[],['b'],1),([[float('nan')]],['a'],['b'],1),([[1.1]],['a'],['b'],1),([[.5]],['a'],['b'],0),([[.5]],['a'],['b'],True)]:
            with self.assertRaises(ValueError):neighbor_scales(c,qn,rn,neighbors=k)
        for c,q,r,s in [([[.5]],[0.],[.2],.5),([[.5]],[float('nan')],[.2],.5),([[.5]],[.2],[],.5),([[.5]],[.2],[.2],0.),([[float('inf')]],[.2],[.2],.5)]:
            with self.assertRaises(ValueError):affinities(c,q,r,sigma=s)


if __name__=='__main__':unittest.main()
