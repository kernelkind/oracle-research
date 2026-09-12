import unittest

from semantic_connection_comparison import compare
from semantic_graph_patterns import construct


class SemanticConnectionComparisonTests(unittest.TestCase):
    def inputs(self, same_role=False):
        records = [{'row': 1, 'note': 'N01'}, {'row': 2, 'note': 'N02'}]
        nodes = [{'id': 0, 'sense': 'activity.n.01', 'context': 0},
                 {'id': 1, 'sense': 'food.n.01', 'context': 0}]
        graphs = [
            {'row': 1, 'nodes': nodes,
             'edges': [{'source': 0, 'role': 'Theme', 'target': 1}]},
            {'row': 2, 'nodes': nodes,
             'edges': [{'source': 0 if same_role else 1,
                        'role': 'Theme' if same_role else 'Goal',
                        'target': 1 if same_role else 0}]},
        ]
        return records, graphs

    def test_compares_every_exact_counterpart_without_unioning_the_control(self):
        records, graphs = self.inputs()
        exact = construct(records, graphs, {})
        connected = construct(records, graphs, {}, relation_policy='connection')
        result = compare(exact, connected)
        item = result['conditions'][1]['recurring_connections'][0]
        self.assertEqual(item['notes'], ['N01', 'N02'])
        self.assertTrue(item['expanded_beyond_each_exact_counterpart'])
        self.assertEqual(item['complete_exact_counterpart_ids'], [])
        self.assertEqual([p['notes'] for p in item['exact_counterparts']],
                         [['N01'], ['N02']])

    def test_does_not_claim_gain_when_one_exact_pattern_already_covers_the_notes(self):
        records, graphs = self.inputs(same_role=True)
        result = compare(construct(records, graphs, {}),
                         construct(records, graphs, {}, relation_policy='connection'))
        item = result['conditions'][1]['recurring_connections'][0]
        self.assertFalse(item['expanded_beyond_each_exact_counterpart'])
        self.assertEqual(len(item['complete_exact_counterpart_ids']), 1)

    def test_rejects_mismatched_sources(self):
        records, graphs = self.inputs()
        exact = construct(records, graphs, {})
        connected = construct(records, graphs, {}, relation_policy='connection')
        connected['source_rows'] = [1]
        with self.assertRaisesRegex(ValueError, 'source'):
            compare(exact, connected)


if __name__ == '__main__':
    unittest.main()
