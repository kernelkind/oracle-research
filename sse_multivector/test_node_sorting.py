import unittest

from sse_multivector import node_sorting


def row(node, note, prominence, cosine, inverse, full):
    result = dict(node_id=node, note_id=note, prominence=prominence, cosine=cosine)
    if inverse is not None or full is not None:
        result.update(inverse_cosine=inverse, full_post_cosine=full)
    return result


class NodeSortingTests(unittest.TestCase):
    def fixture_rows(self):
        return [
            row('P', 'n1', 40, 1.0, 0.0, 0.5), row('P', 'n1', 30, 0.0, 1.0, 0.5),
            row('P', 'n2', 20, -1.0, -1.0, 0.5),
            row('C', 'n2', 100, 1.0, None, 0.5),
            row('C', 'n3', 60, 1.0, 0.0, 0.5), row('C', 'n4', 10, 1.0, 0.0, 0.5),
            row('D', 'n5', 50, 1.0, -1.0, 0.5),
        ]

    def fixture(self):
        scores = node_sorting.note_scores(self.fixture_rows())
        return scores, {'P': ['C', 'D'], 'C': [], 'D': []}, \
            {('P', 'C'): 0.6, ('P', 'D'): 0.4}

    def test_note_scores_take_maximum_masks_within_each_node(self):
        scores = node_sorting.note_scores(self.fixture_rows())
        self.assertEqual(scores[('P', 'n1')],
                         {'prominence': 40, 'score': 85.0, 'product': 40.0})
        self.assertEqual(scores[('P', 'n2')],
                         {'prominence': 20, 'score': 0.0, 'product': 0.0})
        self.assertEqual(scores[('C', 'n2')],
                         {'prominence': 100, 'score': 100.0, 'product': 100.0})
        self.assertEqual(scores[('C', 'n3')],
                         {'prominence': 60, 'score': 80.0, 'product': 60.0})

    def test_note_scores_reject_invalid_rows(self):
        for bad in [row('P', 'n1', 101, 1.0, 0.0, 0.5), row('P', 'n1', 40.0, 1.0, 0.0, 0.5),
                    row('P', 'n1', 40, 1.5, 0.0, 0.5), row('P', '', 40, 0.0, 0.0, 0.5),
                    dict(note_id='n1', prominence=40, cosine=0.0),
                    row('P', 'n1', 40, 1.0, None, 0.5),  # empty inverse under 100
                    row('P', 'n1', 40, 1.0, 0.0, None)]:  # incomplete inverse pair
            with self.assertRaises(ValueError):
                node_sorting.note_scores([bad])
        with self.assertRaises(ValueError):
            node_sorting.note_scores([row('P', 'n1', 40, 1.0, None, None)])

    def test_transfer_shapes(self):
        self.assertEqual(node_sorting.transfer(80, 0.25, 'identity'), 80.0)
        self.assertEqual(node_sorting.transfer(80, 0.25, 'multiply'), 20.0)
        self.assertEqual(node_sorting.transfer(80, 0.25, 'cap'), 25.0)
        self.assertEqual(node_sorting.transfer(10, 0.25, 'cap'), 10.0)
        for bad in [(80, 1.5, 'multiply'), (80, 0.5, 'clip'), (101, 0.5, 'multiply'),
                    (80, None, 'cap')]:
            with self.assertRaises(ValueError):
                node_sorting.transfer(*bad)

    def test_variant_scores_take_the_maximum_over_routes(self):
        scores, children, relevance = self.fixture()
        values = node_sorting.variant_scores(scores, 'P', children, relevance, 'multiply')
        self.assertEqual(values, {'n1': 85.0, 'n2': 60.0, 'n3': 48.0,
                                  'n4': 33.0, 'n5': 20.0})
        # n2 is direct at P (0.0) and in C (100.0): the transferred route wins.
        self.assertEqual(node_sorting.variant_scores(scores, 'P', children,
                                                     relevance, 'identity')['n2'], 100.0)
        self.assertEqual(node_sorting.variant_scores(scores, 'P', children,
                                                     relevance, 'cap')['n4'], 55.0)

    def test_variant_scores_take_the_maximum_across_children(self):
        rows = [row('C', 'x', 30, 1.0, -1.0, 0.5), row('D', 'x', 100, 1.0, None, 0.5),
                row('P', 'y', 50, 1.0, -1.0, 0.5)]
        scores = node_sorting.note_scores(rows)
        children = {'P': ['C', 'D'], 'C': [], 'D': []}
        relevance = {('P', 'C'): 0.6, ('P', 'D'): 0.4}
        values = node_sorting.variant_scores(scores, 'P', children,
                                             relevance, 'multiply')
        self.assertEqual(values, {'x': 40.0, 'y': 50.0})

    def test_orderings_include_recursive_notes_once_across_shared_children(self):
        rows = [row('P', 'local', 50, 1.0, -1.0, 0.5),
                row('G', 'deep', 100, 1.0, None, 0.5)]
        scores = node_sorting.note_scores(rows)
        children = {'P': ['C', 'D'], 'C': ['G'], 'D': ['G'], 'G': []}
        relevance = {('P', 'C'): 0.5, ('P', 'D'): 0.4,
                     ('C', 'G'): 0.8, ('D', 'G'): 0.9}

        self.assertEqual(
            node_sorting.variant_scores(scores, 'P', children, relevance, 'multiply'),
            {'local': 50.0, 'deep': 40.0})
        orderings = node_sorting.orderings(scores, 'P', children, relevance)

        self.assertEqual(orderings['Product'], ['deep', 'local'])
        self.assertEqual(orderings['multiply · score'], ['local', 'deep'])
        self.assertEqual(orderings['identity · score'], ['deep', 'local'])
        self.assertEqual(len(orderings['multiply · score']), 2)

    def test_orderings_cover_baseline_shapes_and_listings(self):
        rows = [row('P', 'd1', 20, 1.0, -1.0, 0.5),
                row('C', 'a', 100, 1.0, None, 0.5),
                row('D', 'b', 40, 1.0, -1.0, 0.5)]
        scores = node_sorting.note_scores(rows)
        children = {'P': ['C', 'D'], 'C': [], 'D': []}
        relevance = {('P', 'C'): 0.35, ('P', 'D'): 0.4}
        orderings = node_sorting.orderings(scores, 'P', children, relevance)
        self.assertEqual(set(orderings), {'Product'} |
                         {f'{shape} · {listing}' for shape in node_sorting.SHAPES
                          for listing in node_sorting.LISTINGS})
        for ordering in orderings.values():
            self.assertEqual(sorted(ordering), ['a', 'b', 'd1'])
        self.assertEqual(orderings['Product'], ['a', 'b', 'd1'])
        self.assertEqual(orderings['identity · score'], ['a', 'b', 'd1'])
        self.assertEqual(orderings['multiply · score'], ['a', 'd1', 'b'])
        self.assertEqual(orderings['cap · score'], ['b', 'a', 'd1'])
        self.assertEqual(orderings['multiply · direct-first'], ['d1', 'a', 'b'])
        self.assertEqual(orderings['cap · direct-first'], ['d1', 'b', 'a'])

    def test_direct_first_lists_direct_members_before_descendants(self):
        rows = [row('P', 'direct-low', 20, 1.0, -1.0, 0.5),
                row('C', 'child-high', 100, 1.0, None, 0.5)]
        scores = node_sorting.note_scores(rows)
        orderings = node_sorting.orderings(
            scores, 'P', {'P': ['C'], 'C': []}, {('P', 'C'): 1.0})
        self.assertEqual(orderings['identity · score'], ['child-high', 'direct-low'])
        self.assertEqual(orderings['identity · direct-first'],
                         ['direct-low', 'child-high'])

    def test_ties_break_by_note_id_only(self):
        rows = [row('P', 'n-b', 5, 1.0, -1.0, 0.5), row('C', 'n-a', 20, 1.0, -1.0, 0.5),
                row('D', 'n-c', 20, 1.0, -1.0, 0.5)]
        scores = node_sorting.note_scores(rows)
        children = {'P': ['C', 'D'], 'C': [], 'D': []}
        relevance = {('P', 'C'): 0.5, ('P', 'D'): 0.5}
        orderings = node_sorting.orderings(scores, 'P', children, relevance)
        self.assertEqual(orderings['multiply · score'], ['n-a', 'n-c', 'n-b'])

    def test_orderings_reject_inconsistent_inputs(self):
        scores, children, relevance = self.fixture()
        cases = [
            (scores, 'P', children, {('P', 'C'): 0.5}),
            (scores, 'P', children, {('P', 'C'): 0.5, ('P', 'D'): 0.5,
                                     ('P', 'E'): 0.5}),
            (scores, 'P', {'P': ['C', 'C'], 'C': []}, {('P', 'C'): 0.5}),
            (scores, 'P', {'P': ['C'], 'C': ['P']},
             {('P', 'C'): 0.5, ('C', 'P'): 0.5}),
            ({**scores, ('X', 'n9'): {'prominence': 1, 'score': 1.0, 'product': 1.0}},
             'P', children, relevance),
            ({}, 'P', children, relevance),
            (scores, 'P', children, {('P', 'C'): 1.5, ('P', 'D'): 0.5}),
        ]
        for args in cases:
            with self.assertRaises(ValueError):
                node_sorting.orderings(*args)


if __name__ == '__main__':
    unittest.main()
