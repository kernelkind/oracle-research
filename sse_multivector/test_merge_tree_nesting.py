"""Offline coverage for the isolated merge-tree nesting experiment."""
import copy
import json
import tempfile
from pathlib import Path
import unittest

from merge_tree_nesting import project, contract, pair_cases, validate_decisions, view
from experiment_inputs import render


class MergeTreeNestingTests(unittest.TestCase):
    def test_explicit_plain_title_normalization_preserves_original_receipt(self):
        from merge_tree_nesting import normalize_title_reports, bind_title_reports, TITLE
        from prepare_category_title_inputs import prepare
        packet=dict(packet='a',instances=[dict(instance='v',vector_id='v',note_id='p',
                    text='x',fragments=['x'],byte_spans=[[0,1]])])
        packets={'packets':[packet]}
        case=dict(id='a',status='malformed',output='Exact original title',
                  receipt={'record_sha256':'0'*64,'results_path':'saved/results.jsonl'},
                  prompt=prepare(packets,TITLE.read_text(),[])[0]['prompt'],
                  evidence={'packet':packet})
        report=dict(prompt_id='v38',adapter='titles',settings=dict(provider='openai-codex',
                    model='gpt-6-luna',reasoning_effort='max'),cases=[case])
        original=copy.deepcopy(report)
        with self.assertRaises(ValueError):bind_title_reports(packets,[report])
        normalized,receipts=normalize_title_reports([report],['a'])
        self.assertEqual(bind_title_reports(packets,normalized),{'a':'Exact original title'})
        self.assertEqual(report,original)
        self.assertEqual(receipts,[dict(case_id='a',receipt=case['receipt'],
                         original_output=case['output'],title=case['output'],
                         operation='user-approved plain title to JSON object')])
        with self.assertRaises(ValueError):normalize_title_reports([report],['unknown'])
        with self.assertRaises(ValueError):normalize_title_reports([report],['a','a'])
        for text in ['', 'Title\nComment', '{"title":broken']:
            bad=copy.deepcopy(report);bad['cases'][0]['output']=text
            with self.assertRaises(ValueError):normalize_title_reports([bad],['a'])

    def test_combined_title_reports_preserve_successes_without_duplicate_results(self):
        from merge_tree_nesting import bind_title_reports, TITLE
        from prepare_category_title_inputs import prepare
        packets={'packets':[dict(packet=g,instances=[dict(instance=g,vector_id=g,
                  note_id=g,text='x',fragments=['x'],byte_spans=[[0,1]])]) for g in ['a','b']]}
        prepared=prepare(packets,TITLE.read_text(),[])
        cases=[dict(id=g['group'],status='valid',receipt={'verified':True},prompt=g['prompt'],
                    parsed={'title':g['group']},evidence={'packet':p})
               for g,p in zip(prepared,packets['packets'])]
        common=dict(prompt_id='v38',adapter='titles',settings=dict(provider='openrouter',
                    model='meta/muse-spark-1.3-contributor',reasoning_effort='high'))
        original=dict(common,cases=[cases[0],dict(cases[1],status='unrun')])
        resumed=dict(common,cases=[cases[1]])
        self.assertEqual(bind_title_reports(packets,[original,resumed]),{'a':'a','b':'b'})
        with self.assertRaises(ValueError):bind_title_reports(packets,[original,dict(common,cases=cases)])

    def test_luna_max_completion_preserves_muse_titles_and_rejects_other_settings(self):
        from merge_tree_nesting import bind_title_reports, TITLE
        from prepare_category_title_inputs import prepare
        packets={'packets':[dict(packet=g,instances=[dict(instance=g,vector_id=g,
                  note_id=g,text='x',fragments=['x'],byte_spans=[[0,1]])]) for g in ['a','b']]}
        prepared=prepare(packets,TITLE.read_text(),[])
        cases=[dict(id=g['group'],status='valid',receipt={'verified':True},prompt=g['prompt'],
                    parsed={'title':g['group']},evidence={'packet':p})
               for g,p in zip(prepared,packets['packets'])]
        muse=dict(prompt_id='v38',adapter='titles',settings=dict(provider='openrouter',
                  model='meta/muse-spark-1.3-contributor',reasoning_effort='high'),
                  cases=[cases[0],dict(cases[1],status='failed')])
        luna=dict(prompt_id='v38',adapter='titles',settings=dict(provider='openai-codex',
                  model='gpt-6-luna',reasoning_effort='max'),cases=[cases[1]])
        self.assertEqual(bind_title_reports(packets,[muse,luna]),{'a':'a','b':'b'})
        for field,value in [('provider','openrouter'),('model','gpt-6-astra'),
                            ('reasoning_effort','low')]:
            bad=copy.deepcopy(luna);bad['settings'][field]=value
            with self.assertRaises(ValueError):bind_title_reports(packets,[muse,bad])
        bad=copy.deepcopy(luna);bad['cases'][0]['prompt']+=' changed'
        with self.assertRaises(ValueError):bind_title_reports(packets,[muse,bad])

    def test_projection_matches_viewer_and_preserves_all_masks(self):
        history = dict(vector_count=4, alias_groups=[['a'], ['b'], ['c'], ['d']],
                       canonical_unique_ids=['a', 'b', 'c', 'd'], merges=[
                           dict(id=4, left=0, right=1, size=2),
                           dict(id=5, left=4, right=2, size=3),
                           dict(id=6, left=5, right=3, size=4)])
        mapping = {'vectors': [dict(vector_id=k, short_id='V'+k, note_id=n,
                                   note_short_id=n, fragments=['x'], byte_spans=[[0, 1]])
                               for k, n in zip('abcd', ['p', 'q', 'q', 'r'])]}
        posts = {'notes': [dict(note_id=n, text='x') for n in ['p', 'q', 'r']]}
        tree, packets = project(history, mapping, posts)
        self.assertEqual(tree['root'], 'M06-6')
        self.assertEqual(tree['edges'], [['M06-6', 'M06-5']])
        self.assertEqual(tree['members']['M06-6'], ['Va', 'Vb', 'Vc', 'Vd'])
        self.assertEqual(len(packets['packets']), 1)
        self.assertEqual(len(packets['packets'][0]['instances']), 3)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'posts.json').write_text(json.dumps(posts))
            (root/'mapping.json').write_text(json.dumps(mapping))
            exported=view(tree, {'M06-5':'X'}, root/'posts.json', root/'mapping.json', label='test')
            masks=exported['mask_instances']['root']
            self.assertEqual({i for ms in masks.values() for m in ms for i in m['ids']},
                             {'Va','Vb','Vc','Vd'})
            self.assertEqual(len(exported['notes']),3)
            self.assertEqual(exported['nodes'][1]['note_ids'],['p','q'])
        bad = copy.deepcopy(history)
        bad['merges'][0]['size'] = 3
        with self.assertRaises(ValueError): project(bad, mapping, posts)

    def test_only_mutual_yes_collapses_keep_other_edges_and_top_title(self):
        tree = dict(root='root', edges=[['root','a'],['a','b'],['b','c'],['b','d']],
                    members={'root':['1','2','3'], 'a':['1','2','3'],
                             'b':['1','2'], 'c':['1'], 'd':['2']})
        decisions = {('a','b'):'yes',('b','a'):'yes',('b','c'):'no',
                     ('c','b'):'yes',('b','d'):'uncertain',('d','b'):'no'}
        result = contract(tree, decisions)
        self.assertEqual(result['representative']['b'], 'a')
        self.assertEqual(result['edges'], [['root','a'], ['a','c'], ['a','d']])
        self.assertEqual([e['status'] for e in result['judgments']],
                         ['equivalent','reversed','uncertain'])
        self.assertEqual(result['members']['a'], tree['members']['a'])
        self.assertEqual(tree['edges'][2], ['b','c'])

    def test_pair_inventory_exact_and_titles_json_escaped(self):
        tree = dict(root='root', edges=[['root','a'], ['a','b']])
        titles = {'a':'A', 'b':'B "quoted"'}
        cases = pair_cases(tree, titles)
        self.assertEqual(len(cases), 2)
        prompt = dict(id='NSP-Jev-v3', text='{"A":"{A_TITLE}","B":"{B_TITLE}"}')
        self.assertEqual(json.loads(render(prompt['text'], cases[0]['inputs'])),
                         {'A':'A','B':'B "quoted"'})
        with self.assertRaises(ValueError): validate_decisions(tree, titles, {}, prompt)
        titles['b'] = 'B'
        report = dict(prompt_id=prompt['id'], settings=dict(provider='openrouter',
                      model='typesafe/jev-1.13', reasoning_effort='provider-default'), cases=[])
        for c in pair_cases(tree,titles):
            report['cases'].append(dict(c, status='valid', receipt={'verified':True},
                                      prompt=render(prompt['text'],c['inputs']),
                                      parsed={'contains':{'choice':'no'}}))
        self.assertEqual(len(validate_decisions(tree,titles,report,prompt)),2)
        report['cases'][0]['inputs']['A_TITLE']='wrong'
        with self.assertRaises(ValueError): validate_decisions(tree,titles,report,prompt)


if __name__ == '__main__': unittest.main()
