"""Exercise the production graph policies without running clustering."""

import copy
import json
import unittest

import igraph

from hidef_graph_policy import apply_graph_policy


class GraphPolicyTests(unittest.TestCase):
    @staticmethod
    def fixture():
        # Edge order deliberately differs from canonical endpoint order.
        graph = igraph.Graph(n=7, edges=[(1, 3), (0, 2), (0, 3), (1, 2),
                                       (2, 4), (3, 4), (4, 5), (3, 5)])
        graph.es['weight'] = [.9, .9, .9, .8, .7, .6, .5, .4]
        graph.es['original_index'] = list(range(8))
        graph.vs['name'] = [f'vector-{i}' for i in range(7)]
        graph['description'] = 'preserve graph and vertex attributes'
        return graph, [{'a'}, {'a'}, {'b'}, {'b'}, {'c'}, {'d'}, {'e'}]

    def test_mutual_note_choice_preserves_vertices_and_requires_both_endpoints(self):
        graph = igraph.Graph(n=4, edges=[(0, 2), (1, 2)])
        graph.es['weight'] = [.9, .8]
        result, audit = apply_graph_policy(graph, [{'a'}, {'a'}, {'b'}, {'c'}],
                                           'mutual_best_per_note')
        self.assertIsNot(result, graph)
        self.assertEqual(result.vcount(), 4)
        self.assertEqual(result.get_edgelist(), [(0, 2)])
        self.assertEqual(result.es['weight'], [.9])
        self.assertEqual(audit['retained_original_edge_indices'], [0])
        self.assertEqual(audit['removed_original_edge_indices'], [1])
        self.assertEqual(audit['isolated_vector_ids'], [1, 3])
        self.assertEqual(graph.get_edgelist(), [(0, 2), (1, 2)])
        self.assertEqual(graph.es['weight'], [.9, .8])

    def test_mutual_ties_use_canonical_vertex_index_not_edge_order(self):
        graph, sources = self.fixture()
        result, audit = apply_graph_policy(graph, sources, 'mutual_best_per_note')
        self.assertEqual(audit['retained_original_edge_indices'], [1, 4, 6, 7])
        self.assertEqual(audit['removed_original_edge_indices'], [0, 2, 3, 5])
        self.assertEqual(result.get_edgelist(), [(0, 2), (2, 4), (4, 5), (3, 5)])
        self.assertEqual(audit['isolated_vector_ids'], [1, 6])
        self.assertEqual(audit['nonisolated_note_ids'], ['a', 'b', 'c', 'd'])
        self.assertEqual(audit['distinct_note_count'], 5)
        self.assertEqual(audit['nonisolated_note_count'], 4)
        self.assertEqual(audit['nonisolated_vector_count'], 5)

    def test_control_matches_mutual_edge_count_but_uses_global_weight_ranking(self):
        graph, sources = self.fixture()
        result, audit = apply_graph_policy(graph, sources, 'strongest_edges_matched')
        self.assertEqual(audit['mutual_best_edge_count'], 4)
        self.assertEqual(audit['retained_edge_count'], 4)
        self.assertEqual(audit['retained_original_edge_indices'], [0, 1, 2, 3])
        self.assertEqual(result.es['weight'], [.9, .9, .9, .8])
        self.assertEqual(audit['isolated_vector_ids'], [4, 5, 6])

    def test_control_cutoff_ties_use_endpoint_indices_not_edge_order(self):
        graph = igraph.Graph(n=4, edges=[(1, 3), (0, 3), (0, 2)])
        graph.es['weight'] = [.9, .9, .9]
        result, audit = apply_graph_policy(graph, [{'a'}, {'a'}, {'b'}, {'b'}],
                                           'strongest_edges_matched')
        self.assertEqual(audit['mutual_best_edge_count'], 1)
        self.assertEqual(audit['retained_original_edge_indices'], [2])
        self.assertEqual(result.get_edgelist(), [(0, 2)])

    def test_each_policy_preserves_input_and_attributes_and_has_deterministic_audit(self):
        for policy in ('original', 'mutual_best_per_note', 'strongest_edges_matched'):
            with self.subTest(policy=policy):
                graph, sources = self.fixture()
                sources_before = copy.deepcopy(sources)
                edges_before = graph.get_edgelist()
                weights_before = list(graph.es['weight'])
                result, audit = apply_graph_policy(graph, sources, policy)
                again, audit_again = apply_graph_policy(graph, sources, policy)
                self.assertIsNot(result, graph)
                self.assertEqual(result.vcount(), graph.vcount())
                self.assertEqual(result.vs['name'], graph.vs['name'])
                self.assertEqual(result['description'], graph['description'])
                self.assertEqual(result.es['original_index'],
                                 audit['retained_original_edge_indices'])
                self.assertEqual(result.es['weight'],
                                 [weights_before[i] for i in audit['retained_original_edge_indices']])
                self.assertEqual(graph.get_edgelist(), edges_before)
                self.assertEqual(graph.es['weight'], weights_before)
                self.assertEqual(sources, sources_before)
                self.assertEqual(again.get_edgelist(), result.get_edgelist())
                self.assertEqual(json.dumps(audit, allow_nan=False),
                                 json.dumps(audit_again, allow_nan=False))
                self.assertEqual(audit['original_edge_count'], 8)
                self.assertEqual(audit['retained_edge_count'] + audit['removed_edge_count'], 8)
                self.assertEqual(audit['isolated_vector_count'] + audit['nonisolated_vector_count'], 7)
                self.assertTrue(audit['definition'])
                self.assertTrue(audit['tie_break'])
                if policy == 'original':
                    self.assertEqual(result.get_edgelist(), edges_before)
                    self.assertEqual(audit['retained_original_edge_indices'], list(range(8)))
                    self.assertEqual(audit['removed_original_edge_indices'], [])

    def test_empty_edge_set_keeps_all_vertices(self):
        graph = igraph.Graph(n=3)
        graph.es['weight'] = []
        for policy in ('original', 'mutual_best_per_note', 'strongest_edges_matched'):
            with self.subTest(policy=policy):
                result, audit = apply_graph_policy(graph, [{'a'}, {'a'}, {'b'}], policy)
                self.assertEqual(result.vcount(), 3)
                self.assertEqual(result.ecount(), 0)
                self.assertEqual(audit['isolated_vector_ids'], [0, 1, 2])
                self.assertEqual(audit['distinct_note_count'], 2)
                self.assertEqual(audit['nonisolated_note_ids'], [])

    def test_rejects_invalid_sources_same_note_edges_and_unknown_policy(self):
        graph = igraph.Graph(n=2, edges=[(0, 1)])
        graph.es['weight'] = [.5]
        for sources in ([{'a'}], [set(), {'b'}], [{'a', 'b'}, {'c'}], [{'a'}, {'a'}]):
            with self.subTest(sources=sources):
                with self.assertRaises(ValueError):
                    apply_graph_policy(graph, sources, 'original')
        with self.assertRaises(ValueError):
            apply_graph_policy(graph, [{'a'}, {'b'}], 'not_a_policy')

    def test_rejects_invalid_weights_and_non_simple_undirected_graphs(self):
        for weight in (0., -.1, float('nan'), float('inf'), None, '0.5'):
            with self.subTest(weight=weight):
                graph = igraph.Graph(n=2, edges=[(0, 1)])
                graph.es['weight'] = [weight]
                with self.assertRaises(ValueError):
                    apply_graph_policy(graph, [{'a'}, {'b'}], 'original')
        for graph in (igraph.Graph(n=2, edges=[(0, 1)], directed=True),
                      igraph.Graph(n=2, edges=[(0, 1), (0, 1)]),
                      igraph.Graph(n=2, edges=[(0, 0)])):
            graph.es['weight'] = [.5] * graph.ecount()
            with self.assertRaises(ValueError):
                apply_graph_policy(graph, [{'a'}, {'b'}], 'original')
        graph = igraph.Graph(n=2, edges=[(0, 1)])
        with self.assertRaises(ValueError):
            apply_graph_policy(graph, [{'a'}, {'b'}], 'original')


if __name__ == '__main__':
    unittest.main()
