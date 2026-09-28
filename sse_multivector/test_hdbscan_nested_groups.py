"""Offline regression checks for retaining and merging saved HDBSCAN groups."""
import copy
import contextlib
import io
from pathlib import Path
import tempfile
import unittest

import hdbscan_nested_groups as nested
from hdbscan_nested_groups import project, bind_saved, missing_title_packets
from hierarchy_build import read, save
from merge_tree_nesting import contract_equivalence


def fixture():
    # 7 is an equal-distance intermediate group; 9 is an EOM root and stays
    # even though it has the same formation distance as its own raw parent.
    rows = [dict(id=g, left=a, right=b, size=size,
                 mutual_reachability_distance=d)
            for g,a,b,size,d in [(6,0,1,2,.1),(7,6,2,3,.2),
                                (8,7,3,4,.2),(9,8,4,5,.3),(10,9,5,6,.3)]]
    aliases = [[str(i)] for i in range(6)]
    aliases[0].append('alias')
    result = dict(canonical_unique_ids=[a[0] for a in aliases], alias_groups=aliases,
                  algorithm_result=dict(vector_count=6, single_linkage_tree=rows,
                                        clusters=[dict(id=40,members=list(range(5)))]))
    mapping = dict(vectors=[dict(vector_id=v,short_id='v'+v,note_id='p'+str(i),
                                 fragments=['x'],byte_spans=[[0,1]])
                           for i,a in enumerate(aliases) for v in a])
    posts = dict(notes=[dict(note_id='p'+str(i),text='x') for i in range(6)])
    return result,mapping,posts


class HdbscanNestedTests(unittest.TestCase):
    def test_prepares_selected_surviving_pairs_without_changing_saved_groups(self):
        result,mapping,posts=fixture()
        tree,packets=project(result,mapping,posts)
        with tempfile.TemporaryDirectory() as d, contextlib.redirect_stdout(io.StringIO()):
            root=Path(d)
            roots={b for a,b in tree['edges'] if a=='root'}
            values=dict(hdbscan=dict(artifact=dict(result=result)),mapping=mapping,posts=posts,
                        original_packets=dict(packets=[p for p in packets['packets'] if p['packet'] in roots]))
            for name,value in values.items():save(root/(name+'.json'),value)
            save(root/'manifest.json',dict(experiment_id='test',sources={k:k+'.json' for k in values},
                                          merges=[],titles=[],sample_plans=[]))
            base=root/'base';nested.prepare(root/'manifest.json',base)
            merged=nested.artifact_directory(base/'merged')
            choices={(a,b):'no' for a,b in tree['edges'] if a!='root'}
            surviving=contract_equivalence(tree,choices)
            save(merged/'tree.json',surviving)
            before={p:p.read_bytes() for p in base.rglob('*') if p.is_file()}
            groups=sorted(set(tree['members'])-{'root'})
            output=root/'pairs'
            nested.prepare_pairs(base,output,groups)
            cases=read(output/'cases.json')['cases']
            self.assertEqual(len(cases),3)
            self.assertEqual([tuple(c['evidence'][k] for k in ('original_a_id','original_b_id')) for c in cases],
                             [(groups[0],groups[1]),(groups[0],groups[2]),(groups[1],groups[2])])
            self.assertEqual(read(output/'selection.json')['groups'],groups)
            self.assertTrue((output/'.gitignore').exists())
            self.assertEqual(before,{p:p.read_bytes() for p in before})
            for bad in [[],groups[:1],[groups[0],groups[0]],['root',groups[0]],['unknown',groups[0]]]:
                with self.assertRaises(ValueError):nested.prepare_pairs(base,root/'bad',bad)
            # A removed group must not be silently selected from the original tree.
            removed=groups[0];del surviving['members'][removed]
            (merged/'tree.json').unlink();save(merged/'tree.json',surviving)
            with self.assertRaises(ValueError):nested.prepare_pairs(base,root/'removed',groups)

    def test_preserves_eom_roots_skips_plateaus_and_keeps_aliases_and_noise(self):
        inputs = fixture()
        before = copy.deepcopy(inputs)
        tree,packets = project(*inputs)
        by_raw = {v['raw_tree_id']:g for g,v in tree['groups'].items()}
        self.assertEqual(set(by_raw), {6,8,9})
        self.assertEqual(tree['edges'], [[by_raw[8],by_raw[6]],
                                         [by_raw[9],by_raw[8]],['root',by_raw[9]]])
        self.assertEqual(tree['groups'][by_raw[9]]['eom_cluster_id'],40)
        self.assertEqual(set(tree['members'][by_raw[6]]),{'v0','valias','v1'})
        self.assertIn('v5',tree['members']['root'])
        self.assertFalse(any(i['instance']=='v5' for p in packets['packets'] for i in p['instances']))
        self.assertEqual(inputs,before)

    def test_refuses_inconsistent_tree_and_alias_inventory(self):
        for mutate in [
            lambda r,m,p: r['algorithm_result']['single_linkage_tree'][0].update(size=3),
            lambda r,m,p: r['algorithm_result']['clusters'].append(dict(id=41,members=[0,1])),
            lambda r,m,p: r['alias_groups'][1].append('0'),
            lambda r,m,p: r['algorithm_result']['single_linkage_tree'][1].update(mutual_reachability_distance=.01),
        ]:
            inputs=fixture();mutate(*inputs)
            with self.assertRaises(ValueError):project(*inputs)

    def test_saved_answers_match_exact_prompts_prefer_original_ids_and_retain_receipts(self):
        first=dict(id='other',prompt='exact',value='yes',receipt={'record_sha256':'one'})
        same=dict(id='a',prompt='exact',value='no',receipt={'record_sha256':'two'})
        wanted=[dict(id='a',prompt='exact'),dict(id='b',prompt='different')]
        matches,missing=bind_saved(wanted,{'exact':[first,same]})
        self.assertEqual(matches,{'a':same})
        self.assertEqual(missing,[wanted[1]])
        matches,_=bind_saved([dict(id='new',prompt='exact')],{'exact':[first,same]})
        self.assertEqual(matches['new']['receipt'],first['receipt'])

    def test_only_surviving_untitled_inputs_need_titles(self):
        tree,packets=project(*fixture())
        choices={(a,b):'yes' for a,b in tree['edges'] if a!='root'}
        result=contract_equivalence(tree,choices)
        missing=missing_title_packets(result,packets,{})
        self.assertEqual(len(missing['packets']),1)
        survivor=missing['packets'][0]['packet']
        self.assertEqual(missing_title_packets(result,packets,{survivor:{}}),{'packets':[]})
        with self.assertRaises(ValueError):contract_equivalence(tree,{})


if __name__=='__main__':unittest.main()
