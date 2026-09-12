import copy
import unittest

from semantic_graph_patterns import construct
from semantic_ontology_experiment import experiment
from semantic_ontology_order import parse_ontology


class OntologyExperimentTests(unittest.TestCase):
    def fixture(self):
        inputs = [{'row': i, 'note': f'N{i}', 'text': 'Original note',
                   'fragments': ['Original'], 'subject': 'original'} for i in [1, 2, 3]]
        graphs = [{'row': i, 'nodes': [{'id': 0, 'sense': 'cook.v.01', 'context': 0},
                   {'id': 1, 'sense': 'food.n.01', 'context': 0}],
                   'edges': [{'source': 0, 'role': 'Patient', 'target': 1}]} for i in [1, 2]]
        senses = {s: {'ancestors': [s], 'hypernyms': [], 'known': True}
                  for s in ['cook.v.01', 'food.n.01']}
        mappings = {s: {'offset': '00000001', 'pos': pos, 'file': 'mappings',
                       'line': 1, 'raw': 'raw annotation',
                       'mappings': [{'term': term, 'relation': '+'}]}
                    for s, pos, term in [('cook.v.01', 'v', 'Cooking'), ('food.n.01', 'n', 'Food')]}
        ontology = parse_ontology({'test.kif': '(subclass Cooking Process) (subclass Food Object)'})
        baseline = construct(inputs[:2], graphs, senses, relation_policy='connection')
        baseline.update(run_id='SGC02', excluded_rows=[{'row': 3, 'error': 'malformed'}])
        return inputs, graphs, senses, mappings, ontology, baseline

    def test_three_conditions_preserve_all_inputs_exclusions_and_frozen_evidence(self):
        args = self.fixture()
        original = copy.deepcopy(args)
        out = experiment(*args)
        self.assertEqual(args, original)
        self.assertEqual(out['inputs'], args[0])
        self.assertEqual(out['excluded_rows'], args[-1]['excluded_rows'])
        self.assertEqual([c['id'] for c in out['conditions']], ['wordnet', 'nouns', 'nouns_and_verbs'])
        conditions = out['conditions']
        self.assertNotIn('SUMO:Cooking', conditions[1]['augmentation']['senses'])
        self.assertIn('SUMO:Cooking', conditions[2]['augmentation']['senses'])
        self.assertEqual(len(out['comparisons']), 3)
        for comparison in out['comparisons']:
            self.assertTrue(comparison['baseline_patterns_unchanged'])

    def test_refuses_drift_from_frozen_baseline(self):
        args = list(self.fixture())
        args[-1]['source_notes'].append('N99')
        with self.assertRaisesRegex(ValueError, 'frozen'):
            experiment(*args)

    def test_existing_sumo_parent_can_gain_a_verb_witness_in_third_condition(self):
        inputs, graphs, senses, mappings, ontology, baseline = self.fixture()
        graphs[0]['nodes'][0]['sense'] = 'cooking.n.01'
        senses['cooking.n.01'] = {'ancestors': ['cooking.n.01'], 'hypernyms': [], 'known': True}
        mappings['cooking.n.01'] = dict(mappings['cook.v.01'], pos='n')
        baseline = construct(inputs[:2], graphs, senses, relation_policy='connection')
        baseline.update(run_id='SGC02', excluded_rows=[{'row': 3, 'error': 'malformed'}])
        out = experiment(inputs, graphs, senses, mappings, ontology, baseline)
        comparison = out['comparisons'][2]
        self.assertTrue(comparison['wordnet_patterns_unchanged'])
        self.assertFalse(comparison['baseline_patterns_unchanged'])
        change = next(p for p in comparison['changed_recurring_patterns']
                      if p['after']['key'] == ['SUMO:Cooking', 'SUMO:Food'])
        self.assertEqual(change['added_notes'], ['N2'])


if __name__ == '__main__':
    unittest.main()
