"""Offline node consolidation, title collection and browser integration."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from hierarchy_build import (consolidate_nodes, titles_from_report, name_merge,
                             package_merge, prepare_nodes, merge_saved)
from true_category_graph import prepare_inputs
from prepare_category_title_inputs import prepare
from true_graph_merge import merge_graph
from test_true_graph_categories import fixture


def report_for(packets):
    from hierarchy_build import TITLE
    return dict(prompt_id='v38', adapter='titles',
                settings=dict(provider='openai-codex', model='gpt-6-luna', reasoning_effort='max'),
                cases=[dict(id=g['group'], status='valid', parsed=dict(title='Title '+g['group']),
                            prompt=g['prompt'], evidence={'instances':g['instances'],
                                'packet':next(p for p in packets['packets'] if p['packet']==g['group'])},
                            receipt={'record_sha256':'test-receipt'})
                       for g in prepare(packets, TITLE.read_text(), [])])


class HierarchyBuildTests(unittest.TestCase):
    def test_only_identical_mask_sets_merge_and_aliases_survive(self):
        source = fixture()['canonical']['source_packets']
        source['packets'][1] = deepcopy(source['packets'][0])
        source['packets'][1]['packet'] = 'B'
        source['packets'][1]['instances'][0]['instance'] = 'alias'
        source['packets'][1]['instances'][0]['vector_id'] = 'alias-vector'
        # C is a strict superset of A/B, not equivalent.
        source['packets'][2]['instances'] += deepcopy(source['packets'][0]['instances'])
        before = deepcopy(source)
        result = consolidate_nodes(source)
        self.assertEqual(source, before)
        self.assertEqual(len(result['source_packets']['packets']), 3)
        merged = result['member_to_group']['A']
        self.assertEqual(merged, result['member_to_group']['B'])
        self.assertEqual(result['member_to_group']['C'], 'C')
        packet = next(p for p in result['source_packets']['packets'] if p['packet']==merged)
        self.assertEqual(len(packet['instances']), 1)
        self.assertEqual(len(packet['instances'][0]['origins']), 2)
        self.assertEqual(result['source'], source)
        source['packets'].reverse()
        self.assertEqual(consolidate_nodes(source)['member_to_group'], result['member_to_group'])

    def test_no_merge_preserves_existing_title_input_order(self):
        source = fixture()['canonical']['source_packets']
        result = consolidate_nodes(source)
        self.assertEqual(result['source_packets'], source)

    def test_title_inputs_settings_inventory_and_status_are_bound(self):
        packets = fixture()['canonical']['source_packets']
        report = report_for(packets)
        self.assertEqual(len(titles_from_report(packets, report)['groups']),4)
        for field in ('prompt', 'missing', 'duplicate', 'failed', 'model', 'effort', 'instances', 'packet'):
            wrong = deepcopy(report)
            if field=='prompt': wrong['cases'][0]['prompt'] += '!'
            elif field=='missing': wrong['cases'].pop()
            elif field=='duplicate': wrong['cases'].append(wrong['cases'][0])
            elif field=='failed': wrong['cases'][0]['status']='failed'
            elif field=='model': wrong['settings']['model']='other'
            elif field=='effort': wrong['settings']['reasoning_effort']='low'
            elif field=='instances': wrong['cases'][0]['evidence']['instances']=[]
            else: wrong['cases'][0]['evidence']['packet']['instances'][0]['text'] += '!'
            with self.subTest(field=field), self.assertRaises(ValueError):
                titles_from_report(packets,wrong)

    def test_astra_titles_preserve_reviews_without_filtering_nodes(self):
        packets = fixture()['canonical']['source_packets']
        report = report_for(packets)
        report['settings'].update(model='gpt-6-astra', reasoning_effort='low')
        reviews = [dict(role='user', verdict='reject', current=True, comment='')]
        report['cases'][0]['reviews'] = reviews
        titles = titles_from_report(packets, report, include_reviews=True)
        self.assertEqual(titles['settings'], report['settings'])
        self.assertEqual(len(titles['groups']), 4)
        self.assertEqual(titles['groups'][0]['reviews'], reviews)
        self.assertNotIn('reviews', titles_from_report(packets, report)['groups'][0])
        for effort in ('max', 'off'):
            report['settings']['reasoning_effort'] = effort
            with self.assertRaises(ValueError):
                titles_from_report(packets, report)

    def test_user_title_rejection_survives_merge_and_browser_export(self):
        values = fixture(); canonical = values['canonical']
        original = canonical['titles']['groups'][0]
        original['reviews'] = [dict(role='user', verdict='reject', current=True)]
        for row in canonical['scores']:
            if (row['a_id'], row['b_id']) in {('A','B'),('B','A')}:
                row.update(predicted=True, generated_text='1', generated_token_ids=[0,209,1])
        merged = merge_graph(**canonical)
        report = report_for(merged['naming_source_packets'])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            for field in ('source', 'mapping'):
                (path/(field+'.json')).write_text(json.dumps(values[field]))
            spec = package_merge(merged, report, path/'source.json', path/'mapping.json', path/'out')
            flagged = [n for n in spec['nodes'] if 'User rejected original title:' in n['analysis']]
            self.assertEqual(len(flagged), 1)
            self.assertIn(original['title'], flagged[0]['analysis'])
        report['settings'].update(model='gpt-6-astra', reasoning_effort='low')
        named = name_merge(merged, report)
        self.assertEqual(named['naming_report']['settings'], report['settings'])
        for field in ('raw_edges', 'transitive_reduced_edges', 'reachability'):
            self.assertEqual(named['graph'][field], merged['graph'][field])
        self.assertEqual({n['group']: n['title'] for n in named['graph']['nodes']
                          if n['title_status'] == 'generated'},
                         {c['id']: c['parsed']['title'] for c in report['cases']})
        report['settings']['reasoning_effort'] = 'max'
        with self.assertRaises(ValueError): name_merge(merged, report)

    def test_cycle_after_exact_merge_uses_original_ids(self):
        values=fixture(); canonical=values['canonical']
        for row in canonical['scores']:
            row.update(predicted=True,generated_text='1',generated_token_ids=[0,209,1])
        originals={'A':['a1','a2'],'B':['B'],'C':['C'],'D':['D']}
        result=merge_graph(**canonical, original_members=originals)
        self.assertEqual(result['graph']['nodes'][0]['source_group_ids'],['B','C','D','a1','a2'])
        self.assertEqual(result, merge_graph(**result['source']))
        bad=deepcopy(originals);bad['B']=['a1']
        with self.assertRaises(ValueError): merge_graph(**canonical, original_members=bad)

    def test_naming_changes_only_labels_and_browser_keeps_original_mask_ids(self):
        values=fixture(); canonical=values['canonical']
        for row in canonical['scores']:
            if (row['a_id'], row['b_id']) in {('A','B'),('B','A')}:
                row.update(predicted=True,generated_text='1',generated_token_ids=[0,209,1])
        merged=merge_graph(**canonical);before=deepcopy(merged)
        report=report_for(merged['naming_source_packets'])
        named=name_merge(merged,report)
        self.assertEqual(merged,before)
        for field in ('raw_edges','transitive_reduced_edges','reachability'):
            self.assertEqual(named['graph'][field],merged['graph'][field])
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)
            for field in ('source','mapping'):
                (path/(field+'.json')).write_text(json.dumps(values[field]))
            spec=package_merge(merged,report,path/'source.json',path/'mapping.json',path/'out')
            self.assertEqual(len(spec['nodes']),4)
            ids={identifier for notes in spec['mask_instances'].values()
                 for masks in notes.values() for mask in masks for identifier in mask['ids']}
            self.assertTrue({'VA','VB','VC','VD'} <= ids)
            with self.assertRaises(FileExistsError):
                package_merge(merged,report,path/'source.json',path/'mapping.json',path/'out')

    def test_pending_or_tampered_merge_cannot_be_published(self):
        canonical=fixture()['canonical']
        for row in canonical['scores']:
            row.update(predicted=True,generated_text='1',generated_token_ids=[0,209,1])
        merged=merge_graph(**canonical)
        with self.assertRaises(ValueError): name_merge(merged,None)
        report=report_for(merged['naming_source_packets'])
        merged['graph']['nodes'][0]['source_group_ids'].pop()
        with self.assertRaises(ValueError): name_merge(merged,report)

    def test_both_stages_through_saved_files_preserve_aliases_and_provenance(self):
        values = fixture()
        source = values['canonical']['source_packets']
        alias = deepcopy(source['packets'][0])
        alias['packet'] = 'X'
        alias['instances'][0].update(instance='VX', vector_id='vector-X')
        source['packets'].append(alias)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'source-packets.json').write_text(json.dumps(source))
            nodes = prepare_nodes(root/'source-packets.json', root/'nodes')
            report = report_for(nodes['source_packets'])
            titles = titles_from_report(nodes['source_packets'], report)
            scores = prepare_inputs(titles)
            merged_id = nodes['member_to_group']['A']
            for row in scores:
                yes = (row['a_id'], row['b_id']) in {(merged_id,'B'),('B',merged_id),('B','C')}
                row.update(predicted=yes, generated_text='1' if yes else '0',
                           generated_token_ids=[0,209 if yes else 632,1], eos_terminated=True,
                           entailment_score=.9 if yes else .1, threshold_predicted=yes)
            # Synthetic model outputs exercise the same file-driven path; no inference.
            (root/'titles').mkdir()
            for filename, payload in [('nodes',nodes),('title-report',report),('titles',titles),
                                      ('true-inputs',prepare_inputs(titles))]:
                (root/'titles'/f'{filename}.json').write_text(json.dumps(payload))
            (root/'scores.json').write_text(json.dumps(scores))
            merge_saved(root/'titles',root/'scores.json',root/'merged')
            merged = json.loads((root/'merged/merge.json').read_text())
            self.assertEqual(merged['node_consolidation']['source'], source)
            cycle = next(n for n in merged['graph']['nodes'] if n['title_status']=='pending')
            self.assertEqual(cycle['source_group_ids'],['A','B','X'])
            self.assertEqual(cycle['group'], 'merged-' + hashlib.sha256(b'["A","B","X"]').hexdigest())
            for field in ('source','mapping'):
                (root/f'{field}.json').write_text(json.dumps(values[field]))
            result = package_merge(merged,report_for(merged['naming_source_packets']),
                                   root/'source.json',root/'mapping.json',root/'browser')
            ids = {i for masks in result['mask_instances'][cycle['group']].values()
                   for mask in masks for i in mask['ids']}
            self.assertTrue({'VA','VX','VB','VC'} <= ids)
            saved = json.loads((root/'browser/provenance.json').read_text())
            self.assertEqual(saved['merge']['node_consolidation']['source'],source)


if __name__=='__main__': unittest.main()
