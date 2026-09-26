"""Native decision reports reuse graph analysis and the existing mask browser."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from decision_hierarchy import make_cases, graph_from_report, package_view, PROMPT
from experiment_inputs import render
from test_true_graph_categories import fixture


def decision_report(titles, accepted=(), uncertain=()):
    cases = make_cases(titles)
    for case in cases:
        pair = case['evidence']['original_a_id'], case['evidence']['original_b_id']
        choice = 'yes' if pair in accepted else 'uncertain' if pair in uncertain else 'no'
        case.update(status='valid', receipt={'record_sha256': 'fixture'},
                    prompt=render(PROMPT.read_text(), case['inputs']),
                    parsed={'contains': {'type': 'choice', 'choice': choice}})
    return dict(prompt_id='NSP-Jev-v1', settings=dict(provider='openrouter', model='typesafe/jev-1.13',
                reasoning_effort='provider-default'), cases=cases)


class DecisionHierarchyTests(unittest.TestCase):
    def test_jev_cycles_use_existing_merge_naming_and_browser_path(self):
        from decision_hierarchy import merge_report
        from hierarchy_build import name_merge, package_merge, validate_merge
        from test_hierarchy_build import report_for
        values = fixture()
        titles = values['canonical']['titles']
        packets = values['canonical']['source_packets']
        report = decision_report(titles, [('A','B'), ('B','C'), ('C','A'), ('C','D')])
        merged = merge_report(titles, packets, report,
                              prompt=dict(id='NSP-Jev-v1', text=PROMPT.read_text()))
        validate_merge(merged)
        self.assertNotIn('scores', merged['source'])
        self.assertEqual(len(merged['source']['decisions']), 12)
        self.assertEqual(merged['graph']['stats']['nodes'], 2)
        self.assertEqual(merged['graph']['stats']['merged_components'], 1)
        group = merged['member_to_group']['A']
        self.assertEqual(merged['graph']['reachability'][group], ['D'])
        self.assertIn('A-contains-D', [r['id'] for r in merged['raw_graph']['reachable_rejected_pairs']])
        naming = report_for(merged['naming_source_packets'])
        named = name_merge(merged, naming)
        self.assertEqual(named['graph']['raw_edges'], merged['graph']['raw_edges'])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for key in ['source', 'mapping']:
                (root / (key+'.json')).write_text(json.dumps(values[key]))
            spec = package_merge(merged, naming, root/'source.json', root/'mapping.json', root/'view')
            self.assertIn('Jev', spec['hierarchy_id'])
            self.assertNotIn('TRUE', json.dumps(spec))
            ids = {i for notes in spec['mask_instances'].values()
                   for masks in notes.values() for mask in masks for i in mask['ids']}
            self.assertTrue({'VA','VB','VC','VD'} <= ids)
        merged['graph']['raw_edges'] = []
        with self.assertRaises(ValueError):
            validate_merge(merged)

    def test_jev_merge_refuses_unresolved_or_changed_inputs(self):
        from decision_hierarchy import merge_report
        values = fixture()['canonical']
        for kind in ['uncertain', 'input', 'missing']:
            report = decision_report(values['titles'])
            if kind == 'uncertain': report['cases'][0]['parsed']['contains']['choice'] = 'uncertain'
            elif kind == 'input': report['cases'][0]['inputs']['A_TITLE'] = 'changed'
            else: report['cases'].pop()
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                merge_report(values['titles'], values['source_packets'], report,
                             prompt=dict(id='NSP-Jev-v1', text=PROMPT.read_text()))

    def test_saved_prompt_version_is_validated_and_labeled_in_browser(self):
        values = fixture()
        titles = values['canonical']['titles']
        report = decision_report(titles, [('A','C')])
        prompt = dict(id='NSP-Jev-v3', text=(PROMPT.parent.parent /
                      'node-subsumption-prompt-jev-v3/prompt.txt').read_text())
        report['prompt_id'] = prompt['id']
        for case in report['cases']:
            case['prompt'] = render(prompt['text'], case['inputs'])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for key in ['source', 'mapping']:
                (root / (key+'.json')).write_text(json.dumps(values[key]))
            spec = package_view(titles, values['canonical']['source_packets'], report,
                                root/'source.json', root/'mapping.json', root/'view', prompt=prompt)
            self.assertIn('NSP-Jev-v3', spec['hierarchy_id'])
            graph = json.loads((root/'view/graph.json').read_text())
            self.assertEqual(graph['prompt_id'], prompt['id'])
            self.assertEqual(len(graph['decisions']), 12)
        for kind in ['wrong_version', 'wrong_text']:
            changed = deepcopy(report)
            if kind == 'wrong_version': changed['prompt_id'] = 'NSP-Jev-v1'
            else: changed['cases'][0]['prompt'] += 'Changed'
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                graph_from_report(titles, changed, prompt=prompt)

    def test_complete_pairs_and_reduction_retain_disconnected_node(self):
        titles = fixture()['canonical']['titles']
        report = decision_report(titles, [('A','B'), ('B','C'), ('A','C')], [('D','A')])
        graph = graph_from_report(titles, report)
        self.assertEqual(len(report['cases']), 12)
        self.assertEqual(graph['roots'], ['A', 'D'])
        self.assertEqual([(e['a_id'], e['b_id']) for e in graph['transitive_reduced_edges']], [('A','B'), ('B','C')])
        self.assertEqual(graph['stats']['native_unresolved'], 1)
        self.assertNotIn('threshold', graph)
        self.assertTrue(all('receipt' in e for e in graph['raw_edges']))

    def test_incomplete_changed_or_unvalidated_answers_are_rejected(self):
        titles = fixture()['canonical']['titles']
        for kind in ['missing', 'duplicate', 'input', 'prompt', 'status', 'receipt', 'choice', 'model']:
            report = decision_report(titles)
            if kind == 'missing': report['cases'].pop()
            elif kind == 'duplicate': report['cases'].append(deepcopy(report['cases'][0]))
            elif kind == 'input': report['cases'][0]['inputs']['A_TITLE'] = 'Changed'
            elif kind == 'prompt': report['cases'][0]['prompt'] += 'Changed'
            elif kind == 'status': report['cases'][0]['status'] = 'failed'
            elif kind == 'receipt': report['cases'][0].pop('receipt')
            elif kind == 'choice': report['cases'][0]['parsed']['contains']['choice'] = 'maybe'
            else: report['settings']['model'] = 'different'
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                graph_from_report(titles, report)

    def test_cycles_and_transitive_rejections_remain_diagnostics(self):
        titles = fixture()['canonical']['titles']
        graph = graph_from_report(titles, decision_report(titles, [('A','B'), ('B','C'), ('C','A')]))
        self.assertEqual(graph['cycle_components'], [['A','B','C']])
        self.assertIsNone(graph['transitive_reduced_edges'])
        self.assertEqual(len(graph['nodes']), 4)
        self.assertEqual(len(graph['reachable_rejected_pairs']), 3)

    def test_identical_titles_do_not_merge_or_drop_nodes(self):
        titles = fixture()['canonical']['titles']
        titles['groups'][1]['title'] = titles['groups'][0]['title']
        graph = graph_from_report(titles, decision_report(titles, [('A','B'), ('B','A')]))
        self.assertEqual(len(graph['nodes']), 4)
        self.assertEqual(graph['cycle_components'], [['A','B']])

    def test_existing_browser_retains_all_nodes_and_exact_individual_masks(self):
        values = fixture()
        titles = values['canonical']['titles']
        report = decision_report(titles, [('A','C'), ('C','D'), ('A','D')])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for key in ['source', 'mapping']:
                (root / (key+'.json')).write_text(json.dumps(values[key]))
            spec = package_view(titles, values['canonical']['source_packets'], report,
                                root/'source.json', root/'mapping.json', root/'view')
            self.assertEqual({n['node_id'] for n in spec['nodes']}, {'root','A','B','C','D'})
            self.assertTrue(all('Jev' in n['analysis'] for n in spec['nodes'] if n['node_id'] != 'root'))
            self.assertIn('mask_instances', spec)
            cycle = decision_report(titles, [('A','B'), ('B','A')])
            with self.assertRaisesRegex(ValueError, 'cycle'):
                package_view(titles, values['canonical']['source_packets'], cycle,
                             root/'source.json', root/'mapping.json', root/'cycle')
            self.assertTrue((root/'cycle/graph.json').exists())
            self.assertFalse((root/'cycle/categories.json').exists())
