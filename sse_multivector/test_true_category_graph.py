"""TRUE10 graph tests exercise production input and graph-building paths."""
import copy
import unittest

import true_category_graph as graph
from true_category_probe import model_input


def titles():
    return {'groups': [
        {'group': 'A', 'title': '  Exact | title\ntext  ', 'note_ids': ['n1']},
        {'group': 'B', 'title': 'Second title', 'note_ids': ['n2']},
        {'group': 'C', 'title': 'Third title', 'note_ids': ['n2', 'n3']}]}


def scores(source, accepted=()):
    rows = graph.prepare_inputs(source)
    for row in rows:
        score = 0.9 if (row['a_id'], row['b_id']) in accepted else 0.1
        row.update(entailment_score=score, threshold_predicted=score > 0.142,
                   predicted=False, generated_text='0', generated_token_ids=[0, 3, 632, 1],
                   eos_terminated=True)
    return rows


def edges(rows):
    return {(row['a_id'], row['b_id']) for row in rows}


class TRUECategoryGraphTests(unittest.TestCase):
    def test_all_ordered_distinct_ids_keep_exact_titles_and_input_direction(self):
        source = titles()
        source['groups'][1]['title'] = source['groups'][0]['title']
        before = copy.deepcopy(source)
        rows = graph.prepare_inputs(source)
        self.assertEqual(source, before)
        self.assertEqual(len(rows), 6)
        self.assertEqual(len({row['id'] for row in rows}), 6)
        by_id = {group['group']: group['title'] for group in source['groups']}
        self.assertEqual(edges(rows), {(a, b) for a in by_id for b in by_id if a != b})
        for row in rows:
            self.assertEqual(row['a'], by_id[row['a_id']])
            self.assertEqual(row['b'], by_id[row['b_id']])
            self.assertEqual(row['format'], 'topic')
            self.assertEqual(row['model_input'], model_input(row, 'topic'))

    def test_dag_keeps_raw_score_edges_and_reduces_only_transitive_edges(self):
        source = titles()
        rows = scores(source, {('A', 'B'), ('B', 'C'), ('A', 'C')})
        before = copy.deepcopy((source, rows))
        result = graph.build_graph(source, rows)
        self.assertEqual((source, rows), before)
        self.assertEqual(result['nodes'], source['groups'])
        self.assertEqual(edges(result['raw_edges']), {('A', 'B'), ('B', 'C'), ('A', 'C')})
        self.assertEqual(result['raw_edges'], [r for r in rows if r['entailment_score'] > 0.142])
        self.assertEqual(edges(result['transitive_reduced_edges']), {('A', 'B'), ('B', 'C')})
        self.assertEqual(result['roots'], ['A'])
        self.assertEqual(result['reachability'], {'A': ['B', 'C'], 'B': ['C'], 'C': []})
        self.assertEqual(result['cycle_components'], [])
        self.assertEqual(result['mutual_acceptance'], [])
        self.assertEqual(result['transitive_reduction_status'], 'complete')
        self.assertEqual(result['stats']['nodes'], 3)
        self.assertEqual(result['stats']['scored_ordered_pairs'], 6)
        self.assertEqual(result['stats']['raw_edges'], 3)

    def test_strict_frozen_cutoff_does_not_replace_native_output(self):
        source = titles()
        rows = scores(source)
        rows[0].update(entailment_score=0.142, threshold_predicted=False)
        rows[1].update(entailment_score=0.14200000000000002, threshold_predicted=True,
                       predicted=None, generated_text='', generated_token_ids=[0, 3],
                       eos_terminated=False)
        result = graph.build_graph(source, rows)
        self.assertEqual(result['raw_edges'], [rows[1]])
        self.assertIsNone(result['raw_edges'][0]['predicted'])
        self.assertFalse(result['raw_edges'][0]['eos_terminated'])
        self.assertEqual(result['stats']['native_unresolved'], 1)
        self.assertEqual(result['threshold'], 0.142)
        self.assertEqual(result['threshold_rule'], 'entailment_score > 0.142')
        for threshold in (0.14, 0.143, True, None, '0.142', float('nan')):
            with self.subTest(threshold=threshold), self.assertRaises(ValueError):
                graph.build_graph(source, rows, threshold=threshold)

    def test_mutual_acceptance_flags_cycle_without_merging_identical_titles(self):
        source = titles()
        source['groups'][1]['title'] = source['groups'][0]['title']
        rows = scores(source, {('A', 'B'), ('B', 'A'), ('B', 'C'), ('A', 'C')})
        result = graph.build_graph(source, rows)
        self.assertEqual(result['nodes'], source['groups'])
        self.assertEqual(result['cycle_components'], [['A', 'B']])
        self.assertEqual(result['strongly_connected_components'], [['A', 'B'], ['C']])
        self.assertEqual(len(result['mutual_acceptance']), 1)
        self.assertEqual(result['mutual_acceptance'][0]['a_id'], 'A')
        self.assertEqual(result['mutual_acceptance'][0]['b_id'], 'B')
        self.assertEqual(edges(result['cycle_edges']), {('A', 'B'), ('B', 'A')})
        self.assertEqual(len(result['raw_edges']), 4)
        self.assertIsNone(result['transitive_reduced_edges'])
        self.assertEqual(result['transitive_reduction_status'], 'blocked_by_cycles')
        self.assertEqual(result['roots'], [])
        self.assertEqual(result['reachability']['A'], ['A', 'B', 'C'])

    def test_three_node_cycle_is_flagged_even_without_mutual_edge_pairs(self):
        source = titles()
        accepted = {('A', 'B'), ('B', 'C'), ('C', 'A')}
        result = graph.build_graph(source, scores(source, accepted))
        self.assertEqual(result['cycle_components'], [['A', 'B', 'C']])
        self.assertEqual(edges(result['cycle_edges']), accepted)
        self.assertEqual(result['mutual_acceptance'], [])
        self.assertIsNone(result['transitive_reduced_edges'])
        self.assertEqual(result['reachability'], {key: ['A', 'B', 'C'] for key in 'ABC'})

    def test_multiple_parents_and_disconnected_roots_do_not_force_a_tree(self):
        source = titles()
        source['groups'].append({'group': 'D', 'title': 'Isolated title'})
        accepted = {('A', 'C'), ('B', 'C')}
        result = graph.build_graph(source, scores(source, accepted))
        self.assertEqual(result['roots'], ['A', 'B', 'D'])
        self.assertEqual(edges(result['transitive_reduced_edges']), accepted)
        self.assertEqual(result['reachability']['D'], [])

    def test_single_node_and_empty_edge_graph_keep_all_roots(self):
        source = {'groups': [titles()['groups'][0]]}
        self.assertEqual(graph.prepare_inputs(source), [])
        result = graph.build_graph(source, [])
        self.assertEqual(result['roots'], ['A'])
        self.assertEqual(result['raw_edges'], [])
        self.assertEqual(result['transitive_reduced_edges'], [])
        self.assertEqual(result['reachability'], {'A': []})
        self.assertEqual(graph.build_graph(titles(), scores(titles()))['roots'], ['A', 'B', 'C'])

    def test_reduction_preserves_reachability_and_does_not_add_rejected_edges(self):
        source = titles()
        rows = scores(source, {('A', 'B'), ('B', 'C')})
        result = graph.build_graph(source, rows)
        self.assertEqual(edges(result['raw_edges']), {('A', 'B'), ('B', 'C')})
        self.assertEqual(edges(result['transitive_reduced_edges']), edges(result['raw_edges']))
        self.assertEqual(result['reachability']['A'], ['B', 'C'])
        self.assertEqual(edges(result['reachable_rejected_pairs']), {('A', 'C')})

    def test_all_four_node_dags_have_identical_reduced_reachability(self):
        source = titles()
        source['groups'].append({'group': 'D', 'title': 'Fourth title'})
        possible = [(a, b) for a in 'ABCD' for b in 'ABCD' if a < b]
        for mask in range(1 << len(possible)):
            accepted = {pair for index, pair in enumerate(possible) if mask & (1 << index)}
            rows = scores(source, accepted)
            result = graph.build_graph(source, rows)
            reduced = edges(result['transitive_reduced_edges'])
            reduced_graph = graph.build_graph(source, scores(source, reduced))
            with self.subTest(mask=mask):
                self.assertEqual(reduced_graph['reachability'], result['reachability'])
                for edge in reduced:
                    removed = graph.build_graph(source, scores(source, reduced - {edge}))
                    self.assertNotEqual(removed['reachability'], result['reachability'])

    def test_missing_duplicate_and_mismatched_rows_are_rejected(self):
        mutations = [
            lambda rows: rows.pop(),
            lambda rows: rows.append(copy.deepcopy(rows[0])),
            lambda rows: rows[0].update(id='unknown'),
            lambda rows: rows[0].update(id=[]),
            lambda rows: rows[0].update(id=rows[1]['id']),
            lambda rows: rows[0].update(a_id='unknown'),
            lambda rows: rows[0].update(a_id=[]),
            lambda rows: rows[0].update(a_id=rows[0]['b_id']),
            lambda rows: rows[0].update(a='Changed title'),
            lambda rows: rows[0].update(b='Changed title'),
            lambda rows: rows[0].update(model_input='premise: swapped hypothesis: wrong'),
            lambda rows: rows[0].update(format='bare'),
            lambda rows: rows[0].pop('domain'),
            lambda rows: rows.__setitem__(0, None),
        ]
        for index, mutate in enumerate(mutations):
            rows = scores(titles())
            mutate(rows)
            with self.subTest(mutation=index), self.assertRaises(ValueError):
                graph.build_graph(titles(), rows)
        for value in (None, {}, 'scores'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                graph.build_graph(titles(), value)

    def test_bad_scores_and_native_generation_provenance_are_rejected(self):
        mutations = [
            lambda row: row.pop('entailment_score'),
            lambda row: row.pop('threshold_predicted'),
            lambda row: row.update(threshold_predicted=True),
            lambda row: row.update(threshold_predicted=0),
            lambda row: row.pop('predicted'),
            lambda row: row.update(predicted=0),
            lambda row: row.update(predicted=True),
            lambda row: row.pop('generated_text'),
            lambda row: row.update(generated_text=0),
            lambda row: row.pop('generated_token_ids'),
            lambda row: row.update(generated_token_ids=[0]),
            lambda row: row.update(generated_token_ids=[0, True, 1]),
            lambda row: row.update(generated_token_ids=[0, -3, 1]),
            lambda row: row.pop('eos_terminated'),
            lambda row: row.update(eos_terminated=1),
            lambda row: row.update(eos_terminated=False),
            lambda row: row.update(generated_token_ids=[0, 3, 632]),
        ]
        for index, mutate in enumerate(mutations):
            rows = scores(titles())
            mutate(rows[0])
            with self.subTest(mutation=index), self.assertRaises(ValueError):
                graph.build_graph(titles(), rows)
        for score in (-0.1, 1.1, float('nan'), float('inf'), True, '0.9', None):
            rows = scores(titles())
            rows[0]['entailment_score'] = score
            with self.subTest(score=score), self.assertRaises(ValueError):
                graph.build_graph(titles(), rows)

    def test_unknown_complete_native_output_remains_unresolved(self):
        rows = scores(titles())
        rows[0].update(generated_text='?', generated_token_ids=[0, 42, 1], predicted=None)
        result = graph.build_graph(titles(), rows)
        self.assertEqual(result['stats']['native_unresolved'], 1)
        self.assertEqual(result['unresolved_native_rows'], [rows[0]])

    def test_invalid_source_groups_and_pair_id_collisions_are_rejected(self):
        mutations = [
            lambda source: source.update(groups=[]),
            lambda source: source.update(groups={}),
            lambda source: source['groups'].append(None),
            lambda source: source['groups'].append(copy.deepcopy(source['groups'][0])),
            lambda source: source['groups'][0].update(group=[]),
            lambda source: source['groups'][0].update(group=' \n '),
            lambda source: source['groups'][0].update(title=None),
            lambda source: source['groups'][0].update(title=' \n '),
        ]
        for index, mutate in enumerate(mutations):
            source = titles()
            mutate(source)
            with self.subTest(mutation=index), self.assertRaises(ValueError):
                graph.prepare_inputs(source)
        colliding = {'groups': [{'group': key, 'title': key}
                                for key in ('A', 'B-contains-C', 'A-contains-B', 'C')]}
        with self.assertRaisesRegex(ValueError, 'pair IDs'):
            graph.prepare_inputs(colliding)

    def test_output_and_input_do_not_share_mutable_source_payloads(self):
        source = titles()
        rows = scores(source, {('A', 'B')})
        result = graph.build_graph(source, list(reversed(rows)))
        self.assertEqual(result['raw_edges'], [rows[0]])
        result['nodes'][0]['note_ids'].append('changed')
        result['raw_edges'][0]['generated_token_ids'].append(999)
        self.assertEqual(source['groups'][0]['note_ids'], ['n1'])
        self.assertEqual(rows[0]['generated_token_ids'], [0, 3, 632, 1])


if __name__ == '__main__':
    unittest.main()
