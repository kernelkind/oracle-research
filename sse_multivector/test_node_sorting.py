import unittest

from sse_multivector import node_sorting


def row(node, note, prominence, cosine):
    return dict(node_id=node, note_id=note, prominence=prominence, cosine=cosine)


class NodeSortingTests(unittest.TestCase):
    def fixture_rows(self):
        return [
            row('P', 'n1', 40, 1.0), row('P', 'n1', 30, 0.0),
            row('P', 'n2', 20, -1.0),
            row('C', 'n2', 100, 1.0), row('C', 'n3', 60, 1.0), row('C', 'n4', 10, 1.0),
            row('D', 'n5', 50, 1.0),
        ]

    def fixture(self):
        scores = node_sorting.note_scores(self.fixture_rows())
        return scores, ['C', 'D'], {'C': 0.5, 'D': 0.5}

    def test_note_scores_take_maximum_masks_within_each_node(self):
        scores = node_sorting.note_scores(self.fixture_rows())
        self.assertEqual(scores[('P', 'n1')], {'prominence': 40, 'score': 40.0})
        self.assertEqual(scores[('P', 'n2')], {'prominence': 20, 'score': 0.0})
        self.assertEqual(scores[('C', 'n2')], {'prominence': 100, 'score': 100.0})

    def test_note_scores_reject_invalid_rows(self):
        for bad in [row('P', 'n1', 101, 1.0), row('P', 'n1', 40.0, 1.0),
                    row('P', 'n1', 40, 1.5), row('P', '', 40, 0.0),
                    dict(note_id='n1', prominence=40, cosine=0.0)]:
            with self.assertRaises(ValueError):
                node_sorting.note_scores([bad])

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
        self.assertEqual(values, {'n1': 40.0, 'n2': 50.0, 'n3': 30.0,
                                  'n4': 5.0, 'n5': 25.0})
        # n2 is direct at P (0.0) and in C (50.0): the transferred route wins.
        self.assertEqual(node_sorting.variant_scores(scores, 'P', children,
                                                     relevance, 'identity')['n2'], 100.0)
        self.assertEqual(node_sorting.variant_scores(scores, 'P', children,
                                                     relevance, 'cap')['n3'], 50.0)

    def test_orderings_cover_baseline_shapes_and_listings(self):
        scores, children, relevance = self.fixture()
        orderings = node_sorting.orderings(scores, 'P', children, relevance)
        self.assertEqual(set(orderings), {'Prominence'} |
                         {f'{shape} · {listing}' for shape in node_sorting.SHAPES
                          for listing in node_sorting.LISTINGS})
        for ordering in orderings.values():
            self.assertEqual(sorted(ordering), ['n1', 'n2', 'n3', 'n4', 'n5'])
        self.assertEqual(orderings['Prominence'], ['n2', 'n3', 'n5', 'n1', 'n4'])
        self.assertEqual(orderings['multiply · score'], ['n2', 'n1', 'n3', 'n5', 'n4'])
        self.assertEqual(orderings['multiply · direct-first'],
                         ['n2', 'n1', 'n3', 'n5', 'n4'])
        self.assertEqual(orderings['cap · score'], ['n2', 'n3', 'n5', 'n1', 'n4'])
        self.assertEqual(orderings['identity · score'], ['n2', 'n3', 'n5', 'n1', 'n4'])
        self.assertEqual(orderings['identity · direct-first'],
                         ['n2', 'n1', 'n3', 'n5', 'n4'])

    def test_direct_first_lists_direct_members_before_descendants(self):
        rows = [row('P', 'direct-low', 20, 1.0), row('C', 'child-high', 100, 1.0)]
        scores = node_sorting.note_scores(rows)
        orderings = node_sorting.orderings(scores, 'P', ['C'], {'C': 1.0})
        self.assertEqual(orderings['identity · score'], ['child-high', 'direct-low'])
        self.assertEqual(orderings['identity · direct-first'],
                         ['direct-low', 'child-high'])

    def test_ties_break_by_note_id_only(self):
        rows = [row('P', 'n-b', 5, 1.0), row('C', 'n-a', 20, 1.0),
                row('D', 'n-c', 20, 1.0)]
        scores = node_sorting.note_scores(rows)
        orderings = node_sorting.orderings(scores, 'P', ['C', 'D'],
                                           {'C': 0.5, 'D': 0.5})
        self.assertEqual(orderings['multiply · score'], ['n-a', 'n-c', 'n-b'])

    def test_orderings_reject_inconsistent_inputs(self):
        scores, children, relevance = self.fixture()
        cases = [
            (scores, 'P', children, {'C': 0.5}),
            (scores, 'P', children, {'C': 0.5, 'D': 0.5, 'E': 0.5}),
            (scores, 'P', ['C', 'C'], {'C': 0.5}),
            (scores, 'P', ['C', 'P'], {'C': 0.5, 'P': 0.5}),
            ({**scores, ('X', 'n9'): {'prominence': 1, 'score': 1.0}},
             'P', children, relevance),
            ({}, 'P', children, relevance),
            (scores, 'P', children, {'C': 1.5, 'D': 0.5}),
        ]
        for args in cases:
            with self.assertRaises(ValueError):
                node_sorting.orderings(*args)


if __name__ == '__main__':
    unittest.main()
