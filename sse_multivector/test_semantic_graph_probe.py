import unittest

from semantic_graph_probe import parse_sbn, select_inputs, decode_output


class SemanticGraphProbeTests(unittest.TestCase):
    def test_native_sequence_binds_exact_concepts(self):
        graph = parse_sbn('boy.n.01 buy.v.01 Agent -1 Theme +1 book.n.02')
        self.assertEqual([n['sense'] for n in graph['nodes']],
                         ['boy.n.01', 'buy.v.01', 'book.n.02'])
        self.assertEqual(graph['edges'], [
            {'source': 1, 'role': 'Agent', 'target': 0},
            {'source': 1, 'role': 'Theme', 'target': 2}])

    def test_inverse_role_preserves_direction_but_partof_is_native(self):
        graph = parse_sbn('bread.n.01 PatientOf +1 bake.v.01 '
                          'loaf.n.02 PartOf -2')
        self.assertEqual(graph['edges'], [
            {'source': 1, 'role': 'Patient', 'target': 0},
            {'source': 2, 'role': 'PartOf', 'target': 0}])

    def test_context_does_not_reset_concept_offsets(self):
        graph = parse_sbn('person.n.01 NEGATION <1 smile.v.01 Agent -1')
        self.assertEqual([n['context'] for n in graph['nodes']], [0, 1])
        self.assertEqual(graph['contexts'][1],
                         {'id': 1, 'relation': 'NEGATION', 'target': 0})
        self.assertEqual(graph['edges'][0]['target'], 0)

    def test_constants_are_not_concept_references(self):
        graph = parse_sbn('person.n.01 Name "Mary Jane" EQU speaker '
                          'number.n.01 Quantity 20 Name "+1"')
        self.assertEqual(graph['edges'], [])
        self.assertEqual(len(graph['anchors']), 4)
        self.assertEqual(graph['anchors'][-1]['value'], '"+1"')

    def test_rejects_incomplete_or_invalid_native_output(self):
        for source in ['', 'person.n.01 Agent', 'person.n.01 Agent +2',
                       'person.n.01 NEGATION <2 smile.v.01',
                       'Agent -1 person.n.01', 'person.n.01 garbage']:
            with self.subTest(source=source), self.assertRaises(ValueError):
                parse_sbn(source)

    def test_selection_retains_source_fields_without_rewriting(self):
        records = [{'row': 1, 'note': 'N01', 'subject': 'Cooking brisket.',
                    'text': 'original', 'fragments': ['brisket']}]
        selected = select_inputs(records, [1])
        self.assertEqual(selected, records)
        for rows in [[1, 1], [2]]:
            with self.assertRaises(ValueError):
                select_inputs(records, rows)

    def test_missing_eos_is_not_accepted_as_semantic_output(self):
        result = decode_output({'row': 1, 'output': 'bread.n.01',
                                'ended_with_eos': False})
        self.assertIsNone(result['graph'])
        self.assertIn('EOS', result['error'])

    def test_native_error_and_raw_output_both_preserved(self):
        record = {'row': 5, 'output': 'bread.n.01 Patient +9',
                  'ended_with_eos': True}
        result = decode_output(record)
        self.assertEqual(result['output'], record['output'])
        self.assertIsNone(result['graph'])
        self.assertTrue(result['error'])

    def test_context_separator_cannot_become_participant_role(self):
        for source in ['person.n.01 NEGATION +1 smile.v.01',
                       'person.n.01 NEGATION speaker',
                       'person.n.01 Agent <1']:
            with self.subTest(source=source), self.assertRaises(ValueError):
                parse_sbn(source)

    def test_documented_overlap_operator_is_not_a_context_separator(self):
        graph = parse_sbn('time.n.08 time.n.08 TOV -1')
        self.assertEqual(graph['edges'], [{'source': 1, 'role': 'TOV', 'target': 0}])


if __name__ == '__main__':
    unittest.main()
