"""Offline comparison exercises the production renderer and contraction code."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from merge_tree_comparison import render_comparison


class MergeTreeComparisonTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        self.source = self.directory / 'posts.json'
        self.mapping = self.directory / 'mapping.json'
        self.source.write_text(json.dumps({'notes': [
            {'note_id': 'p1', 'text': 'Tea time.'},
            {'note_id': 'p2', 'text': 'Coffee time.'}]}))
        self.mapping.write_text(json.dumps({'vectors': [
            {'note_id': 'p1', 'note_short_id': 'N1'},
            {'note_id': 'p2', 'note_short_id': 'N2'}]}))
        instances = {
            'V1': dict(instance='V1', vector_id='v1', note_id='p1', text='Tea time.',
                       fragments=['Tea'], byte_spans=[[0, 3]]),
            'V2': dict(instance='V2', vector_id='v2', note_id='p2', text='Coffee time.',
                       fragments=['Coffee'], byte_spans=[[0, 6]])}
        self.tree = dict(root='root', edges=[['root','a'],['a','b'],['b','c'],['a','d']],
                         members={'root':['V1','V2'], 'a':['V1','V2'],
                                  'b':['V1'], 'c':['V1'], 'd':['V2']}, instances=instances)
        self.titles = {'a':'Drinks', 'b':'Tea', 'c':'Tea', 'd':'Coffee'}
        self.branches = [dict(root='a', label='Drinks', focus=True)]
        self.directed = {('a','b'):'no', ('b','a'):'no',
                         ('b','c'):'yes', ('c','b'):'yes',
                         ('a','d'):'yes', ('d','a'):'yes'}
        self.equivalent = {('a','b'):'yes', ('a','d'):'no'}

    def build(self, **kwargs):
        return render_comparison(self.tree, self.titles, self.branches,
                                 self.directed, self.equivalent, self.source,
                                 self.mapping, label='Saved comparison', **kwargs)

    def test_additional_model_view_keeps_same_pairs_and_separate_assessments(self):
        method = dict(label='Astra low · NMP-Jev-v2',
                      equivalent={('a','b'):'no', ('a','d'):'yes'},
                      assessments={('a','d'):['Astra-only concern.']})
        view, evidence = self.build(mask_comparisons={'astra':method})
        nodes = {n['node_id']:n for n in view['nodes']}
        self.assertIn('Astra low · NMP-Jev-v2', nodes['branch:0:astra']['label'])
        self.assertEqual(evidence['projections']['astra']['representative']['d'], 'a')
        self.assertEqual(evidence['projections']['astra']['representative']['c'], 'c')
        self.assertEqual(evidence['projections']['mask']['representative']['d'], 'd')
        self.assertIn('Astra-only concern.', nodes['astra:a']['analysis'])
        self.assertNotIn('Astra-only concern.', nodes['mask:a']['analysis'])
        self.assertEqual(view['mask_instances']['astra:a'], view['mask_instances']['original:a'])
        self.assertEqual(set(evidence['projections']['astra']['representative']),
                         set(self.tree['members']))
        for bad in [{('a','b'):'no'}, {('a','b'):'no', ('a','d'):'invalid'}]:
            with self.assertRaises(ValueError):
                self.build(mask_comparisons={'astra':dict(method, equivalent=bad)})
        with self.assertRaises(ValueError):
            self.build(mask_comparisons={'original':method})

    def test_same_tested_edges_and_recoverable_originals(self):
        before = copy.deepcopy(self.tree)
        view, evidence = self.build()
        self.assertEqual(self.tree, before)
        title = evidence['projections']['title']
        masks = evidence['projections']['mask']
        self.assertEqual(set(title['members'])-{'root'}, {'a','b','c'})
        self.assertEqual(set(masks['members'])-{'root'}, {'a','c','d'})
        self.assertEqual(title['representative']['c'], 'c')
        self.assertEqual(masks['representative']['c'], 'c')
        for mode in ('title','mask'):
            untested = [j for j in evidence['projections'][mode]['judgments']
                        if j['status']=='untested']
            self.assertEqual(untested, [dict(parent='b',child='c',status='untested')])
        nodes = {n['node_id']:n for n in view['nodes']}
        self.assertIn('original:b', nodes)
        self.assertNotIn('mask:b', nodes)
        self.assertIn('untested', nodes['mask:c']['analysis'].lower())
        self.assertIn('2/3', nodes['branch:0:mask']['label'])
        self.assertNotIn('forward', next(j for j in masks['judgments']
                                       if j.get('same_topic')=='yes'))

    def test_preserves_exact_masks_ids_titles_and_full_post_binding(self):
        view, _ = self.build()
        nodes = {n['node_id']:n for n in view['nodes']}
        for mode in ('original','title','mask'):
            self.assertEqual(nodes[mode+':a']['label'], 'Drinks')
            self.assertEqual(nodes[mode+':a']['note_ids'], ['N1','N2'])
            self.assertEqual(view['mask_instances'][mode+':a']['N1'],
                             [dict(ids=['V1'],byte_spans=[[0,3]])])
            self.assertEqual(view['mask_instances'][mode+':a']['N2'],
                             [dict(ids=['V2'],byte_spans=[[0,6]])])
        self.assertEqual({n['note_id'] for n in view['notes']}, {'p1','p2'})

    def test_invalid_or_unbound_decisions_are_refused(self):
        self.equivalent['a','c']='yes'
        with self.assertRaisesRegex(ValueError, 'original edges'):
            self.build()
        del self.equivalent['a','c']
        self.equivalent['a','b']='bogus'
        with self.assertRaisesRegex(ValueError, 'choice'):
            self.build()

    def test_changed_source_spans_are_refused(self):
        self.tree['instances']['V1']['byte_spans']=[[0,4]]
        with self.assertRaises(ValueError):
            self.build()

    def test_mask_assessments_identify_the_method_even_in_the_title_view(self):
        view, _ = render_comparison(
            self.tree, self.titles, self.branches, self.directed, self.equivalent,
            self.source, self.mapping, label='Comparison',
            assessments={('a','d'):['This mask answer is questionable.']})
        nodes = {n['node_id']:n for n in view['nodes']}
        for node in ('title:a', 'mask:d', 'original:d'):
            self.assertIn('assessment of the mask-based answer', nodes[node]['analysis'])


if __name__ == '__main__':
    unittest.main()
