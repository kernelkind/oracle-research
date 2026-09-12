import unittest

from semantic_graph_construction import replay_native, canonicalize_graphs


class SemanticGraphConstructionTests(unittest.TestCase):
    def test_replay_excludes_control_and_invalid_outputs_but_keeps_evidence(self):
        records = [{'row': 1, 'note': 'N01', 'subject': 'Bread.'},
                   {'row': 2, 'note': 'N02', 'subject': 'Beef.'}]
        native = [{'row': -1, 'subject': 'I am a student.', 'output': 'person.n.01',
                   'ended_with_eos': True},
                  {'row': 1, 'subject': 'Bread.', 'note': 'N01',
                   'output': 'bread.n.01', 'ended_with_eos': True},
                  {'row': 2, 'subject': 'Beef.', 'note': 'N02',
                   'output': 'beef.n.01 Agent +9', 'ended_with_eos': True}]
        decoded, selected, graphs = replay_native(records, native)
        self.assertEqual([r['row'] for r in selected], [1])
        self.assertEqual([g['row'] for g in graphs], [1])
        self.assertEqual(len(decoded), 3)
        self.assertTrue(decoded[2]['error'])
        native[1]['subject'] = 'Changed source.'
        with self.assertRaises(ValueError):
            replay_native(records, native)

    def test_canonicalization_keeps_native_spelling_and_uses_saved_mapping(self):
        graph = {'row': 1, 'nodes': [{'id': 0, 'sense': 'alias.n.01', 'context': 0}],
                 'edges': []}
        lexicon = {'canonical_senses': {'alias.n.01': 'canonical.n.01'},
                   'senses': {'canonical.n.01': {'ancestors': ['canonical.n.01']}}}
        normalized = canonicalize_graphs([graph], lexicon)
        self.assertEqual(normalized[0]['nodes'][0]['sense'], 'canonical.n.01')
        self.assertEqual(normalized[0]['nodes'][0]['native_sense'], 'alias.n.01')
        self.assertEqual(graph['nodes'][0]['sense'], 'alias.n.01')


if __name__ == '__main__':
    unittest.main()
