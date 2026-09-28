"""Offline regression checks for retaining and merging saved HDBSCAN groups."""
import copy
import unittest

from hdbscan_nested_groups import project, bind_saved, missing_title_packets
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
