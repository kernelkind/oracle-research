"""Exercise the selector used by saved-comparison evaluation and native callers."""
import unittest
from itertools import combinations

from sse_multivector.canonical_graph_search import GraphSearch


def node(identifier, *parents):
    return dict(id=identifier, parents=list(parents))


class CanonicalGraphSearch(unittest.TestCase):
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

    def test_neither_keeps_descendants_available_for_child_relationships(self):
        search = GraphSearch([node('Parent'), node('Child', 'Parent')])
        search.record({'Parent': 'neither'})
        self.assertEqual(search.candidates(), ['Child'])
        search.record({'Child': 'local_contains_canonical'})
        self.assertTrue(search.result()['complete'])

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

    def test_parallel_batch_answers_remain_recordable_after_an_inference(self):
        search = GraphSearch([node('A'), node('B'), node('Parent', 'A'),
                              node('Shared child', 'Parent', 'B')])
        search.record({'A': 'canonical_contains_local', 'B': 'canonical_contains_local'})
        # Both native requests were selected before either answer returned.
        self.assertEqual(search.candidates(), ['Parent', 'Shared child'])
        search.record({'Shared child': 'equivalent'})
        self.assertEqual(search.candidates(), [])
        search.record({'Parent': 'canonical_contains_local'})
        self.assertEqual(search.result()['queried'].count('Parent'), 1)

    def test_ineligible_ancestors_do_not_hide_eligible_descendants(self):
        search = GraphSearch([node('Excluded'), node('Eligible', 'Excluded')],
                             eligible=['Eligible'])
        self.assertEqual(search.candidates(), ['Eligible'])
        search.record({'Eligible': 'neither'})
        self.assertEqual(search.result()['queried'], ['Eligible'])

    def test_required_mapped_parent_is_compared_even_if_inferred(self):
        search = GraphSearch([node('Parent'), node('Mapped', 'Parent')], required=['Mapped'])
        search.record({'Parent': 'local_contains_canonical'})
        self.assertEqual(search.candidates(), ['Mapped'])
        search.record({'Mapped': 'local_contains_canonical'})
        self.assertEqual(search.result()['queried'], ['Parent', 'Mapped'])

    def test_uncertain_makes_no_containment_inference(self):
        search = GraphSearch([node('Parent'), node('Child', 'Parent')])
        search.record({'Parent': 'uncertain'})
        self.assertEqual(search.result()['inferred'], {})
        self.assertEqual(search.candidates(), ['Child'])

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

    def test_matches_exhaustive_relationships_in_a_multiple_parent_graph(self):
        # A finite containment graph supplies an exact oracle for selection
        # mechanics; it makes no claims about real topic meanings.
        sets = [frozenset(s) for size in range(1, 4)
                for s in combinations(range(3), size)]
        graph = [node(str(i), *(str(j) for j, parent in enumerate(sets)
                      if child < parent and len(parent) == len(child) + 1))
                 for i, child in enumerate(sets)]
        for size in range(1, 5):
            for members in combinations(range(4), size):
                local = frozenset(members)
                expected = {str(i): ('equivalent' if local == canonical else
                    'canonical_contains_local' if local < canonical else
                    'local_contains_canonical' if canonical < local else 'neither')
                    for i, canonical in enumerate(sets)}
                with self.subTest(local=members):
                    search = GraphSearch(graph)
                    answers = {}
                    while search.candidates():
                        batch = {k: expected[k] for k in search.candidates()}
                        answers.update(batch)
                        search.record(batch)
                    self.assertEqual(dict(search.result()['inferred'], **answers), expected)
                    self.assertEqual(len(search.result()['queried']), len(set(answers)))

    def test_large_contained_branch_uses_one_comparison_without_recursion(self):
        graph = [node(str(i), *([str(i - 1)] if i else [])) for i in range(5000)]
        search = GraphSearch(graph)
        search.record({'0': 'local_contains_canonical'})
        self.assertEqual(search.result()['queried'], ['0'])
        self.assertEqual(len(search.result()['inferred']), 4999)
        self.assertTrue(search.result()['complete'])


if __name__ == '__main__':
    unittest.main()
