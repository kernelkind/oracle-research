"""Saved mask decisions build a sparse hierarchy without repairs or inference."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

import cross_branch_merge as cross
from experiment_inputs import render
from prepare_category_title_inputs import prepare
from test_cross_branch_merge import packet
from true_category_graph import graph_from_decisions


def fixture(per_source=2, choices=None):
    packets = dict(packets=[packet(g) for g in 'abcde'])
    result = cross.consolidate(packets, {g: [g] for g in 'abcde'}, {}, [])
    instances = {p['instances'][0]['instance']: p['instances'][0]
                 for p in [packet(g) for g in 'abcdez']}
    state = dict(tree=dict(root='root', members={'root': list(instances)},
        instances=instances, edges=[['root', 'a'], ['a', 'b'], ['b', 'c']]),
        comparisons=[dict(groups=list(p)) for p in [('a','c'), ('a','d'), ('c','d'), ('d','e')]])
    selected = cross.parent_child_cases(state, result, per_source=per_source)
    titles = dict(groups=[dict(p, title=p['group'])
        for p in prepare(packets, cross.TITLE.read_text(), [])])
    text = (Path(cross.__file__).parent / 'node-subsumption-prompt-astra-masks-v1/prompt.txt').read_text()
    choices = choices or {('a','b'): 'a_parent', ('b','c'): 'a_parent'}
    cases = []
    for item in selected['cases']:
        choice = choices.get(tuple(item['evidence']['group_ids']), 'neither')
        cases.append(dict(item, status='valid', receipt={'record_sha256': item['id']},
            prompt=render(text, item['inputs']),
            parsed={'parent_child': {'type': 'choice', 'choice': choice}},
            reviews=[dict(role='user', verdict='reject', current=True)]))
    report = dict(prompt_id='NSP-Astra-Masks-v1', settings=dict(provider='openai-codex',
        model='gpt-6-astra', reasoning_effort='low'), cases=cases)
    return state, result, titles, selected, report


class MaskParentChildTests(unittest.TestCase):
    def test_sparse_graph_preserves_unasked_pairs_without_fabricating_decisions(self):
        nodes = [dict(group=g, title=g) for g in 'abc']
        rows = [dict(id='ab', a_id='a', b_id='b', predicted=True)]
        with self.assertRaisesRegex(ValueError, 'complete'):
            graph_from_decisions(nodes, rows)
        graph = graph_from_decisions(nodes, rows, require_complete=False)
        self.assertEqual(graph['raw_edges'], rows)
        self.assertEqual(graph['roots'], ['a', 'c'])
        self.assertEqual(graph['unresolved_native_rows'], [])
        self.assertEqual(graph['stats']['scored_ordered_pairs'], 1)
        for invalid in [rows * 2, [dict(rows[0], b_id='unknown')], [dict(rows[0], b_id='a')]]:
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                graph_from_decisions(nodes, invalid, require_complete=False)

    def test_native_choices_keep_all_groups_and_ignore_review_corrections(self):
        state, result, titles, selected, report = fixture()
        report['cases'][2]['parsed']['parent_child']['choice'] = 'uncertain'
        before = deepcopy((titles, selected, report))
        graph = cross.parent_child_graph(titles, selected, report)
        self.assertEqual(graph['nodes'], titles['groups'])
        self.assertEqual(sorted((r['a_id'], r['b_id']) for r in graph['raw_edges']), [('a','b'), ('b','c')])
        self.assertEqual(len(graph['pair_decisions']), 4)
        self.assertEqual(len(graph['decisions']), 8)
        self.assertEqual(len(graph['unresolved_pairs']), 1)
        self.assertEqual(len(graph['untested_candidate_pairs']), 2)
        self.assertEqual(graph['coverage']['candidate_pairs'], 6)
        self.assertEqual(graph['coverage']['tested_pairs'], 4)
        self.assertEqual(graph['coverage']['choice_counts']['neither'], 1)
        self.assertEqual(graph['reachability']['a'], ['b', 'c'])
        self.assertEqual((titles, selected, report), before)
        reordered = deepcopy(report)
        reordered['cases'].reverse()
        self.assertEqual(cross.parent_child_graph(titles, selected, reordered), graph)

    def test_cycles_and_reachable_rejections_are_reported_without_repairs(self):
        _, _, titles, selected, report = fixture(per_source=99)
        graph = cross.parent_child_graph(titles, selected, report)
        self.assertEqual([(r['a_id'], r['b_id']) for r in graph['reachable_rejected_pairs']], [('a','c')])
        for case in report['cases']:
            if case['evidence']['group_ids'] == ['a', 'c']:
                case['parsed']['parent_child']['choice'] = 'b_parent'
        graph = cross.parent_child_graph(titles, selected, report)
        self.assertEqual(graph['cycle_components'], [['a','b','c']])
        self.assertEqual(len(graph['nodes']), 5)
        self.assertEqual(len(graph['raw_edges']), 3)
        self.assertIsNone(graph['transitive_reduced_edges'])

    def test_incomplete_or_mismatched_receipts_inputs_and_settings_are_refused(self):
        _, _, titles, selected, original = fixture()
        for kind in ['missing', 'duplicate', 'inputs', 'ids', 'prompt', 'status', 'receipt', 'choice', 'type', 'model', 'version']:
            report = deepcopy(original)
            case = report['cases'][0]
            if kind == 'missing': report['cases'].pop()
            elif kind == 'duplicate': report['cases'].append(deepcopy(case))
            elif kind == 'inputs': case['inputs']['A_MASKS_JSON'] = '[]'
            elif kind == 'ids': case['evidence']['group_ids'].reverse()
            elif kind == 'prompt': case['prompt'] += ' changed'
            elif kind == 'status': case['status'] = 'failed'
            elif kind == 'receipt': case['receipt'] = None
            elif kind == 'choice': case['parsed']['parent_child']['choice'] = 'yes'
            elif kind == 'type': case['parsed']['parent_child']['type'] = 'noul'
            elif kind == 'model': report['settings']['model'] = 'other'
            elif kind == 'version': report['prompt_id'] = 'other'
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                cross.parent_child_graph(titles, selected, report)

    def test_export_preserves_masks_and_refuses_cycle_browsing(self):
        for cyclic in [False, True]:
            state, result, titles, selected, report = fixture(per_source=99)
            if cyclic:
                next(c for c in report['cases'] if c['evidence']['group_ids'] == ['a','c'])['parsed']['parent_child']['choice'] = 'b_parent'
            else:
                report['cases'][-1]['parsed']['parent_child']['choice'] = 'uncertain'
            graph = cross.parent_child_graph(titles, selected, report)
            with self.subTest(cyclic=cyclic), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                cross.save(root/'posts.json', dict(notes=[dict(note_id=g, text=g) for g in 'abcdez']))
                cross.save(root/'mapping.json', dict(vectors=[dict(vector_id=g, short_id='v'+g,
                    note_id=g, note_short_id='N'+g, fragments=[g], byte_spans=[[0,1]]) for g in 'abcdez']))
                args = (graph, result['source_packets'], state['tree'], root/'posts.json',
                        root/'mapping.json', root/'out', {'decision_report': report})
                before = deepcopy((graph, result, state, report))
                if cyclic:
                    with self.assertRaisesRegex(ValueError, 'cycle'):
                        cross.export_parent_child(*args)
                    self.assertFalse((root/'out/categories.json').exists())
                else:
                    spec = cross.export_parent_child(*args)
                    nodes = {n['node_id']: n for n in spec['nodes']}
                    self.assertEqual(set(nodes), {'root', *'abcde'})
                    self.assertEqual(nodes['a']['children'], ['b'])
                    self.assertEqual(nodes['a']['note_ids'], ['Na'])
                    self.assertEqual(spec['mask_instances']['root']['Nz'][0]['ids'], ['vz'])
                    self.assertEqual(spec['mask_instances']['a']['Na'][0]['ids'], ['va'])
                    self.assertNotIn('Jev', str(spec))
                    self.assertTrue(any('uncertain' in n['analysis'] for n in spec['nodes']))
                self.assertEqual(cross.read(root/'out/graph.json'), graph)
                self.assertTrue((root/'out/provenance.json').exists())
                self.assertEqual((graph, result, state, report), before)
                with self.assertRaises(FileExistsError):
                    cross.export_parent_child(*args)
