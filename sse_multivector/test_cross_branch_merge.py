"""Production-path checks for bounded selection and reversible equivalence."""
import copy
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

import cross_branch_merge as cross


def packet(g, text=None):
    text=text or g
    return dict(packet=g,instances=[dict(instance='v'+g,vector_id=g,note_id=g,
        text=text,fragments=[text],byte_spans=[[0,len(text)]])])


class CrossBranchTests(unittest.TestCase):
    def test_launcher_uses_isolated_view_and_existing_browser_without_collapsing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            launcher=root/'sse_multivector/run-cross-branch-hierarchy.sh'
            launcher.parent.mkdir()
            shutil.copy(Path(__file__).with_name(launcher.name),launcher)
            def launch(*args):
                return subprocess.run(['bash',str(launcher),*args],cwd='/',
                                      text=True,capture_output=True)
            self.assertEqual(launch('--unknown').returncode,2)
            self.assertIn('missing',launch('--check').stderr)
            view=root/'target/hierarchy-build-v1/hr02-cross-branch-v1/view/categories.json'
            view.parent.mkdir(parents=True)
            view.write_text('{}')
            self.assertIn('browser is missing',launch().stderr)
            binary=root/'target/infomap-review-build/debug/sse-subject-navigation'
            binary.parent.mkdir(parents=True)
            binary.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\n')
            binary.chmod(0o755)
            result=launch('--check')
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(result.stdout.splitlines(),['--categories',str(view),
                str(root/'sse_multivector/hierarchy-refresh-v1/masked-posts.json'),'--check'])

    def test_saved_titles_are_kept_and_only_combined_masks_receive_new_titles(self):
        from test_hierarchy_build import report_for
        from prepare_category_title_inputs import prepare
        packets=dict(packets=[packet(g) for g in 'abc'])
        state=dict(title_bindings={g['group']:dict(value='saved '+g['group'],prompt=g['prompt'],
                    receipt={'record_sha256':'old'}) for g in prepare(packets,cross.TITLE.read_text(),[])})
        result=cross.consolidate(packets,{g:[g] for g in 'abc'},{('a','b'):'yes'},[])
        title_report=report_for(result['naming_source_packets'])
        title_report['settings'].update(model='gpt-6-astra',reasoning_effort='low')
        titles=cross.assemble_titles(state,result,title_report)
        self.assertEqual(len(titles['groups']),2)
        self.assertEqual(next(g['title'] for g in titles['groups'] if g['group']=='c'),'saved c')
        self.assertEqual(len(cross.make_cases(titles)),2)
        with self.assertRaises(ValueError):cross.assemble_titles(state,result,None)
        changed=copy.deepcopy(state);changed['title_bindings']['c']['prompt']='changed'
        with self.assertRaises(ValueError):cross.assemble_titles(changed,result,title_report)

    def test_placement_export_preserves_nested_mask_origins(self):
        from test_decision_hierarchy import decision_report
        from test_hierarchy_build import report_for
        from hierarchy_build import package_merge
        from decision_hierarchy import PROMPT
        from prepare_category_title_inputs import prepare
        packets=dict(packets=[packet(g) for g in 'abc'])
        state=dict(title_bindings={g['group']:dict(value=g['group'],prompt=g['prompt'],
                    receipt={'record_sha256':'old'}) for g in prepare(packets,cross.TITLE.read_text(),[])})
        result=cross.consolidate(packets,{g:[g] for g in 'abc'},{('a','b'):'yes'},[])
        title_report=report_for(result['naming_source_packets'])
        title_report['settings'].update(model='gpt-6-astra',reasoning_effort='low')
        titles=cross.assemble_titles(state,result,title_report)
        joined=result['member_to_group']['a']
        decisions=decision_report(titles,[(joined,'c')])
        merged=cross.merge_report(titles,result['source_packets'],decisions,
            prompt=dict(id='NSP-Jev-v1',text=PROMPT.read_text()),original_members=result['original_members'])
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            cross.save(root/'source.json',dict(notes=[dict(note_id=g,text=g) for g in 'abc']))
            cross.save(root/'mapping.json',dict(notes=[dict(note_id=g,short_id='N'+g) for g in 'abc'],
                vectors=[dict(vector_id=g,short_id='v'+g,note_id=g,note_short_id='N'+g,
                              fragments=[g],byte_spans=[[0,1]]) for g in 'abc']))
            spec=package_merge(merged,None,root/'source.json',root/'mapping.json',root/'out')
            ids={i for notes in spec['mask_instances'].values() for masks in notes.values() for m in masks for i in m['ids']}
            self.assertTrue({'va','vb','vc'}<=ids)

    def test_placed_view_keeps_ungrouped_masks_at_root_without_new_membership(self):
        from test_decision_hierarchy import decision_report
        from hierarchy_build import name_merge
        from decision_hierarchy import PROMPT
        from prepare_category_title_inputs import prepare
        packets=dict(packets=[packet(g) for g in 'ab'])
        titles=dict(groups=[dict(p,title=p['group']) for p in prepare(packets,cross.TITLE.read_text(),[])])
        decisions=decision_report(titles,[('a','b')])
        merged=cross.merge_report(titles,packets,decisions,
            prompt=dict(id='NSP-Jev-v1',text=PROMPT.read_text()))
        named=name_merge(merged,None)
        instances={p['instances'][0]['instance']:p['instances'][0] for p in [packet(g) for g in 'abc']}
        tree=dict(root='root',members={'root':list(instances)},instances=instances)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            cross.save(root/'posts.json',dict(notes=[dict(note_id=g,text=g) for g in 'abc']))
            cross.save(root/'mapping.json',dict(vectors=[dict(vector_id=g,short_id='v'+g,
                note_id=g,note_short_id='N'+g,fragments=[g],byte_spans=[[0,1]]) for g in 'abc']))
            spec=cross.render_placed(named,tree,root/'posts.json',root/'mapping.json',label='test')
            nodes={n['node_id']:n for n in spec['nodes']}
            self.assertEqual(nodes['root']['children'],['a'])
            self.assertEqual(nodes['a']['children'],['b'])
            self.assertEqual(nodes['a']['note_ids'],['Na'])
            self.assertEqual(nodes['b']['note_ids'],['Nb'])
            self.assertEqual(nodes['root']['note_ids'],['Na','Nb','Nc'])
            self.assertEqual(spec['mask_instances']['root']['Nc'][0]['ids'],['vc'])
            self.assertNotIn('Nc',spec['mask_instances']['a'])

    def test_placement_conflicts_report_no_answers_without_changing_graph(self):
        from test_decision_hierarchy import decision_report
        from decision_hierarchy import PROMPT
        from prepare_category_title_inputs import prepare
        packets=dict(packets=[packet(g) for g in 'abc'])
        result=cross.consolidate(packets,{g:[g] for g in 'abc'},
                                 {('a','b'):'no',('b','c'):'uncertain'},[])
        titles=dict(groups=[dict(p,title=p['group']) for p in prepare(packets,cross.TITLE.read_text(),[])])
        decisions=decision_report(titles,[('a','b'),('b','a')])
        merged=cross.merge_report(titles,packets,decisions,
            prompt=dict(id='NSP-Jev-v1',text=PROMPT.read_text()))
        before=copy.deepcopy(merged)
        conflicts=cross.placement_conflicts(result,merged)
        self.assertEqual(len(conflicts),1)
        self.assertEqual((conflicts[0]['a_title'],conflicts[0]['b_title']),('a','b'))
        self.assertEqual(conflicts[0]['placed_group'],merged['member_to_group']['a'])
        self.assertEqual(merged,before)

    def test_two_capped_lists_preserve_distant_title_matches_and_disjointness(self):
        packets=dict(packets=[packet(g) for g in 'abcd'])
        titles=dict(a='Coffee',b='Coffee beans',c='coffee',d='Other')
        vectors=[dict(opaque_id=g,normalized_vector=v) for g,v in
                 [('a',[1.,0.]),('b',[.8,.6]),('c',[-1.,0.]),('d',[-.8,.6])]]
        before=copy.deepcopy((packets,titles,vectors))
        rows=cross.select_pairs(packets,titles,vectors,k=1)
        pairs={tuple(r['groups']) for r in rows}
        self.assertEqual(pairs,{('a','b'),('a','c'),('c','d')})
        self.assertIn('same_title',next(r['reasons'] for r in rows if r['groups']==['a','c']))
        self.assertEqual((packets,titles,vectors),before)
        self.assertEqual(rows,cross.select_pairs(dict(packets=list(reversed(packets['packets']))),
                                                 titles,list(reversed(vectors)),k=1))
        # A nested group is not a cross-branch candidate, even with a shared title.
        nested=copy.deepcopy(packets);nested['packets'][0]['instances']+=packet('b')['instances']
        self.assertNotIn(('a','b'),{tuple(r['groups']) for r in cross.select_pairs(nested,titles,vectors,k=1)})
        with self.assertRaises(ValueError):cross.select_pairs(packets,titles,vectors,k=0)
        with self.assertRaises(ValueError):cross.select_pairs(packets,titles,vectors[:-1],k=1)

    def test_title_bucket_and_total_nominations_are_bounded(self):
        names=[str(i) for i in range(12)]
        packets=dict(packets=[packet(g) for g in names])
        rows=cross.select_pairs(packets,{g:'same' for g in names},
              [dict(opaque_id=g,normalized_vector=[1.,0.]) for g in names],k=2)
        self.assertLessEqual(len(rows),2*2*len(names))
        self.assertLess(len(rows),len(names)*(len(names)-1)//2)

    def test_yes_chains_merge_but_any_recorded_no_blocks_the_whole_component(self):
        packets=dict(packets=[packet(g) for g in 'abcdef'])
        originals={g:[g] for g in 'abcdef'}
        decisions={('a','b'):'yes',('b','c'):'yes',('d','e'):'yes',('e','f'):'uncertain'}
        before=copy.deepcopy((packets,originals,decisions))
        merged=cross.consolidate(packets,originals,decisions,[])
        self.assertEqual(sorted(map(len,merged['original_members'].values())),[1,2,3])
        self.assertEqual((packets,originals,decisions),before)
        blocked=cross.consolidate(packets,originals,decisions,[dict(a='a',b='c',source='saved')])
        self.assertEqual(sorted(map(len,blocked['original_members'].values())),[1,1,1,1,2])
        self.assertEqual(blocked['blocked_components'][0]['members'],['a','b','c'])
        self.assertEqual(len(blocked['source_packets']['packets']),5)
        self.assertEqual(len(blocked['naming_source_packets']['packets']),1)
        self.assertEqual(cross.consolidate(packets,originals,dict(reversed(list(decisions.items()))),[]),merged)
        self.assertEqual(len({i['note_id'] for p in merged['source_packets']['packets'] for i in p['instances']}),6)
        with self.assertRaises(ValueError):cross.consolidate(packets,originals,{('a','z'):'yes'},[])

    def test_current_no_also_blocks_and_exact_masks_keep_aliases(self):
        a=packet('a');b=packet('b');b['instances']+=copy.deepcopy(a['instances'])
        packets=dict(packets=[a,b,packet('c')]);originals={g:[g] for g in 'abc'}
        result=cross.consolidate(packets,originals,{('a','b'):'yes'},[])
        joined=result['naming_source_packets']['packets'][0]
        self.assertEqual(len(joined['instances']),2)
        self.assertEqual(sorted(len(i['origins']) for i in joined['instances']),[1,2])
        result=cross.consolidate(packets,originals,
                  {('a','b'):'yes',('b','c'):'yes',('a','c'):'no'},[])
        self.assertEqual(result['naming_source_packets'],dict(packets=[]))


if __name__=='__main__':unittest.main()
