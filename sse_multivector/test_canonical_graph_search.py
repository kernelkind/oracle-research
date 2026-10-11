"""Exercise the selector used by saved-comparison evaluation and native callers."""
import unittest

from sse_multivector.canonical_graph_search import GraphSearch


def node(identifier, *parents):
    return dict(id=identifier, parents=list(parents))


class CanonicalGraphSearch(unittest.TestCase):
    def test_neither_stops_only_that_branch_and_keeps_unknowns_unknown(self):
        search = GraphSearch([node('Food'), node('Other'), node('Meals', 'Food'),
                              node('Breakfast', 'Meals', 'Other')])
        search.record({'Food': 'canonical_contains_local', 'Other': 'canonical_contains_local'})
        self.assertEqual(search.candidates(), ['Meals'])
        search.record({'Meals': 'neither'})
        self.assertEqual(search.candidates(), ['Breakfast'])
        search.record({'Breakfast': 'neither'})
        self.assertTrue(search.result()['complete'])
        pruned = GraphSearch([node('Meals'), node('Breakfast', 'Meals')])
        pruned.record({'Meals': 'neither'})
        self.assertEqual(pruned.result()['inferred'], {})
        self.assertEqual(pruned.candidates(), [])

    def test_shared_descendant_waits_for_unfinished_ancestor(self):
        search = GraphSearch([node('A'), node('B'), node('Parent', 'A'),
                              node('Shared', 'Parent', 'B')])
        search.record({'A': 'canonical_contains_local', 'B': 'canonical_contains_local'})
        self.assertEqual(search.candidates(), ['Parent'])
        search.record({'Parent': 'local_contains_canonical'})
        self.assertEqual(search.candidates(), [])
        self.assertEqual(search.result()['inferred'], {'Shared': 'local_contains_canonical'})

    def test_required_parent_can_be_inferred_but_cannot_reopen_pruned_branch(self):
        graph = [node('Parent'), node('Mapped', 'Parent')]
        search = GraphSearch(graph)
        search.record({'Parent': 'local_contains_canonical'})
        self.assertEqual(search.candidates(), [])
        self.assertEqual(search.result()['inferred'], {'Mapped': 'local_contains_canonical'})
        pruned = GraphSearch(graph)
        pruned.record({'Parent': 'neither'})
        self.assertEqual(pruned.candidates(), [])
        self.assertEqual(pruned.result()['inferred'], {})

    def test_uncertain_holds_search_and_accepts_already_selected_answers(self):
        search = GraphSearch([node('A'), node('B'), node('Child', 'A')])
        self.assertEqual(search.candidates(), ['A', 'B'])
        search.record({'A': 'uncertain'})
        self.assertEqual(search.candidates(), [])
        search.record({'B': 'neither'})
        self.assertTrue(search.result()['held'])
        self.assertEqual(search.result()['queried'], ['A', 'B'])
        self.assertEqual(search.result()['inferred'], {})

    def test_candidates_follow_saved_node_order_after_partial_batches(self):
        search = GraphSearch([node('A'), node('Child', 'A'), node('B')])
        search.record({'A': 'canonical_contains_local'})
        self.assertEqual(search.candidates(), ['Child', 'B'])

    def test_starts_at_all_roots_then_follows_every_containing_branch(self):
        search = GraphSearch([node('Food'), node('Mental states'),
                              node('Meals', 'Food'), node('Hopes', 'Mental states')])
        self.assertEqual(search.candidates(), ['Food', 'Mental states'])
        search.record({'Food': 'canonical_contains_local',
                       'Mental states': 'canonical_contains_local'})
        self.assertEqual(search.candidates(), ['Meals', 'Hopes'])

    def test_broader_local_skips_the_contained_subtree(self):
        search = GraphSearch([node('Meals'), node('Breakfast', 'Meals'),
                              node('Pancake breakfast', 'Breakfast')])
        search.record({'Meals': 'local_contains_canonical'})
        result = search.result()
        self.assertTrue(result['complete'])
        self.assertEqual(result['queried'], ['Meals'])
        self.assertEqual(result['inferred'], {
            'Breakfast': 'local_contains_canonical',
            'Pancake breakfast': 'local_contains_canonical'})


    def test_equivalence_reuses_ancestors_and_descendants(self):
        search = GraphSearch([node('Food'), node('Meals', 'Food'),
                              node('Dinner', 'Meals'), node('Gardening')])
        search.record({'Food': 'canonical_contains_local', 'Gardening': 'neither'})
        search.record({'Meals': 'equivalent'})
        result = search.result()
        self.assertTrue(result['complete'])
        self.assertEqual(result['queried'], ['Food', 'Gardening', 'Meals'])
        self.assertEqual(result['inferred'], {'Dinner': 'local_contains_canonical'})

    def test_shared_child_is_compared_once(self):
        search = GraphSearch([node('Food'), node('Cooking'),
                              node('Ingredients', 'Food', 'Cooking')])
        search.record({'Food': 'canonical_contains_local',
                       'Cooking': 'canonical_contains_local'})
        self.assertEqual(search.candidates(), ['Ingredients'])
        search.record({'Ingredients': 'neither'})
        self.assertEqual(search.result()['queried'].count('Ingredients'), 1)





    def test_missing_answer_remains_pending_without_becoming_neither(self):
        search = GraphSearch([node('A'), node('B')])
        search.record({'A': 'neither'})
        result = search.result()
        self.assertFalse(result['complete'])
        self.assertEqual(result['pending'], ['B'])
        self.assertEqual(result['queried'], ['A'])
        self.assertEqual(result['inferred'], {})

    def test_repeated_answer_or_unselected_node_is_rejected(self):
        search = GraphSearch([node('Parent'), node('Child', 'Parent')])
        with self.assertRaises(ValueError):
            search.record({'Child': 'neither'})
        search.record({'Parent': 'neither'})
        with self.assertRaises(ValueError):
            search.record({'Parent': 'neither'})

    def test_invalid_graph_or_label_is_rejected_before_any_queries(self):
        for nodes in ([node('A'), node('A')], [node('A', 'missing')],
                      [node('A', 'B'), node('B', 'A')]):
            with self.assertRaises(ValueError):
                GraphSearch(nodes)
        search = GraphSearch([node('A')])
        with self.assertRaises(ValueError):
            search.record({'A': 'unknown'})
        self.assertEqual(search.result()['queried'], [])


    def test_large_contained_branch_uses_one_comparison_without_recursion(self):
        graph = [node(str(i), *([str(i - 1)] if i else [])) for i in range(5000)]
        search = GraphSearch(graph)
        search.record({'0': 'local_contains_canonical'})
        self.assertEqual(search.result()['queried'], ['0'])
        self.assertEqual(len(search.result()['inferred']), 4999)
        self.assertTrue(search.result()['complete'])


if __name__ == '__main__':
    unittest.main()
