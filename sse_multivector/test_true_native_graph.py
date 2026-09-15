"""Native-answer graphs use saved generated classes, never a score surrogate."""
import copy
import json
from pathlib import Path
import unittest

from true_category_graph import build_graph, prepare_inputs
from true_graph_notes import derive_note_memberships


def fixture():
    titles = {'groups': [{'group': key, 'title': key,
                         'instances': [{'instance': 'V'+key, 'fragments': [key]}]}
                        for key in 'ABC']}
    packets = {'packets': [{'packet': key, 'instances': [dict(
        instance='V'+key, fragments=[key], text=key, note_id='note-'+key,
        vector_id='vector-'+key, byte_spans=[[0, 1]])]} for key in 'ABC']}
    rows = prepare_inputs(titles)
    for row in rows:
        row.update(entailment_score=0.1, threshold_predicted=False,
                   predicted=False, generated_text='0',
                   generated_token_ids=[0, 3, 632, 1], eos_terminated=True)
    return titles, packets, rows


def set_native(row, value):
    row.update(predicted=value, generated_text='1' if value else '0',
               generated_token_ids=[0, 209, 1] if value else [0, 3, 632, 1])


class NativeGraphTests(unittest.TestCase):
    def test_saved_native_class_controls_edges_without_changing_scores(self):
        titles, packets, rows = fixture()
        by = {(r['a_id'], r['b_id']): r for r in rows}
        for pair in [('A', 'B'), ('B', 'A'), ('B', 'C')]:
            by[pair].update(entailment_score=0.3, threshold_predicted=True)
        set_native(by['A', 'B'], True)
        # This deliberately separates the generated class from any numerical cutoff.
        set_native(by['A', 'C'], True)
        before = copy.deepcopy((titles, packets, rows))
        cutoff = build_graph(titles, rows)
        native = build_graph(titles, rows, decision_rule='native')
        self.assertEqual((titles, packets, rows), before)
        self.assertEqual(cutoff['cycle_components'], [['A', 'B']])
        self.assertEqual(native['cycle_components'], [])
        self.assertEqual(native['raw_edges'], [by['A', 'B'], by['A', 'C']])
        self.assertEqual(native['roots'], ['A'])
        self.assertEqual(native['edge_rule'], 'predicted is True')
        self.assertIsNone(native['threshold'])
        self.assertIsNone(native['threshold_rule'])
        memberships = derive_note_memberships(native, packets)['nodes']
        self.assertEqual(memberships[0]['recursive_note_ids'], ['note-A', 'note-B', 'note-C'])
        self.assertEqual(memberships[1]['recursive_note_ids'], ['note-B'])

    def test_indirect_native_rejection_is_not_a_cutoff_rejection(self):
        titles, _, rows = fixture()
        by = {(r['a_id'], r['b_id']): r for r in rows}
        for pair in [('A', 'B'), ('B', 'C')]:
            set_native(by[pair], True)
        by['A', 'C'].update(entailment_score=0.3, threshold_predicted=True)
        native = build_graph(titles, rows, decision_rule='native')
        self.assertEqual(native['reachable_rejected_pairs'], [by['A', 'C']])
        self.assertEqual(native['reachability']['A'], ['B', 'C'])
        self.assertEqual(native['transitive_reduced_edges'], native['raw_edges'])
        by['A', 'C'].update(predicted=None, generated_text='?', generated_token_ids=[0, 42, 1])
        unresolved = build_graph(titles, rows, decision_rule='native')
        self.assertEqual(unresolved['reachable_rejected_pairs'], [])
        self.assertEqual(unresolved['unresolved_native_rows'], [by['A', 'C']])

    def test_native_dag_reduction_retains_all_paths_and_multiple_parents(self):
        titles, _, rows = fixture()
        for row in rows:
            if (row['a_id'], row['b_id']) in {('A', 'B'), ('B', 'C'), ('A', 'C')}:
                set_native(row, True)
        native = build_graph(titles, rows, decision_rule='native')
        self.assertEqual([(r['a_id'], r['b_id']) for r in native['transitive_reduced_edges']],
                         [('A', 'B'), ('B', 'C')])
        self.assertEqual(native['reachability'], {'A': ['B', 'C'], 'B': ['C'], 'C': []})
        for row in rows:
            if (row['a_id'], row['b_id']) == ('A', 'B'):
                set_native(row, False)
        native = build_graph(titles, rows, decision_rule='native')
        self.assertEqual(native['roots'], ['A', 'B'])
        self.assertEqual(len(native['transitive_reduced_edges']), 2)

    def test_invalid_rule_fails_explicitly(self):
        titles, _, rows = fixture()
        for rule in ['score', 'argmax', None, True]:
            with self.subTest(rule=rule), self.assertRaises(ValueError):
                build_graph(titles, rows, decision_rule=rule)

    def test_default_reproduces_entire_saved_true10_graph(self):
        root = Path(__file__).parent / 'navigation-research-v1/TRUE10/derived'
        canonical = json.loads((root / 'canonical.json').read_text())
        saved = json.loads((root / 'graph.json').read_text())
        self.assertEqual(build_graph(canonical['titles'], canonical['scores']), saved)


if __name__ == '__main__':
    unittest.main()
