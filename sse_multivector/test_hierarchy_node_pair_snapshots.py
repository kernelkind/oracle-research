"""Historical canonical graph inputs through native source-bound preparation."""
import hashlib
import json
from pathlib import Path
import unittest

from sse_multivector import test_hierarchy_node_pairs as fixtures


class HierarchyNodePairSnapshotTests(unittest.TestCase):
    setUp = fixtures.HierarchyNodePairsTests.setUp
    write = fixtures.HierarchyNodePairsTests.write
    cli = fixtures.HierarchyNodePairsTests.cli
    prepare = fixtures.HierarchyNodePairsTests.prepare
    show = fixtures.HierarchyNodePairsTests.show
    calls = fixtures.HierarchyNodePairsTests.calls
    saved_trial_source = fixtures.HierarchyNodePairsTests.saved_trial_source

    def historical_source(self):
        source = self.saved_trial_source()
        source['canonical_states']['current']['before_step'] = 1
        source['pairs'] = [{'id': 'one', 'local': {'note_id': 'n2', 'number': '2'},
                            'canonical': {'state': 'current', 'id': 'C001'}, 'review': {}}]
        self.write('source.json', source)
        return source

    def test_before_step_uses_original_graph_and_reuses_identical_request(self):
        self.historical_source()
        state_path = self.root / 'trial/state.json'
        original = state_path.read_bytes()
        self.cli('prepare', 'before-baseline', '--spec', self.spec)
        self.cli('run', 'before-baseline', env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(
            dict(meaning='Fixed food meaning', relation='canonical_contains_local', reason='Fixture'))})
        calls = len(self.calls())
        self.prepare()
        case = self.show()['cases'][0]
        canonical = json.loads(case['inputs']['INPUT_JSON'])['canonical']
        self.assertEqual(canonical['meaning'], 'Fixed cooking meaning')
        self.assertEqual(canonical['parents'], [])
        self.assertEqual(canonical['ancestors'], [])
        self.assertEqual(canonical['descendants'], [])
        self.assertEqual(case['evidence']['before_step'], 1)
        self.assertNotIn('before_step', case['prompt'])
        plan = json.loads((self.root / 'E1/experiment.json').read_text())['plan']
        self.assertEqual(plan['sources'][str(state_path)], hashlib.sha256(original).hexdigest())
        self.assertEqual(state_path.read_bytes(), original)
        self.assertEqual(len(self.calls()), calls)
        self.cli('run', 'E1')
        result = self.show()['cases'][0]
        self.assertTrue(result['reused'])
        self.assertEqual(result['parsed']['relation'], 'canonical_contains_local')
        self.assertEqual(len(self.calls()), calls)

    def test_historical_and_final_graphs_share_one_source_read(self):
        from unittest.mock import patch
        from sse_multivector import experiment_inputs
        source = self.historical_source()
        source['canonical_states']['final'] = {'trial': 'trial/state.json'}
        source['pairs'].append({**source['pairs'][0], 'id': 'two',
                                'canonical': {'state': 'final', 'id': 'C001'}})
        self.write('source.json', source)
        original_read = Path.read_bytes
        reads = []

        def tracked(path):
            reads.append(path)
            return original_read(path)

        spec = json.loads(self.spec.read_text())
        with patch.object(Path, 'read_bytes', tracked):
            cases, sources, _ = experiment_inputs.prepare_file(
                spec['dataset'], self.root / 'source.json', self.prompt.read_text())
        state_path = self.root / 'trial/state.json'
        self.assertEqual(reads.count(state_path), 1)
        self.assertIn(str(state_path), sources)
        before, final = [json.loads(case['inputs']['INPUT_JSON'])['canonical'] for case in cases]
        self.assertEqual(before['descendants'], [])
        self.assertEqual(final['descendants'], [{'id': 'C002', 'subject': 'Food',
                         'meaning': 'Fixed food meaning', 'parents': ['C001']}])

    def test_invalid_step_selectors_and_unavailable_nodes_are_rejected(self):
        source = self.historical_source()
        for index, selector in enumerate((-1, True, '1', None, 3)):
            with self.subTest(selector=selector):
                source['canonical_states']['current']['before_step'] = selector
                self.write('source.json', source)
                result = self.cli('prepare', f'bad-selector-{index}', '--spec', self.spec, ok=False)
                self.assertIn('before_step', result.stderr)
                self.assertFalse((self.root / f'bad-selector-{index}').exists())
        source['canonical_states']['current']['before_step'] = 1
        source['pairs'][0]['canonical']['id'] = 'C002'
        self.write('source.json', source)
        result = self.cli('prepare', 'future-node', '--spec', self.spec, ok=False)
        self.assertIn('unknown canonical', result.stderr)
        self.assertFalse((self.root / 'future-node').exists())

    def test_historical_reference_preserves_corpus_and_source_checks(self):
        source = self.historical_source()
        self.write('other-notes.json', json.loads((self.root / 'notes.json').read_text()))
        source['corpus'] = 'other-notes.json'
        self.write('source.json', source)
        result = self.cli('prepare', 'wrong-corpus', '--spec', self.spec, ok=False)
        self.assertIn('corpus does not match', result.stderr)
        source['corpus'] = 'notes.json'
        self.write('source.json', source)
        notes = self.root / 'notes.json'
        notes.write_bytes(notes.read_bytes() + b'\n')
        result = self.cli('prepare', 'changed-source', '--spec', self.spec, ok=False)
        self.assertIn('trial source changed', result.stderr)
        self.assertFalse((self.root / 'wrong-corpus').exists())
        self.assertFalse((self.root / 'changed-source').exists())

    def test_saved_producer_meaning_can_change_with_historical_graph_unchanged(self):
        source = self.historical_source()
        self.write('meaning-source.json', {'schema_version': 1, 'corpus': 'notes.json',
                   'nodes': [{'id': 'food', 'local': {'note_id': 'n2', 'number': '2'}, 'review': {}}]})
        spec = json.loads((self.root / 'bootstrap.json').read_text())
        spec['dataset'] = {'adapter': 'hierarchy_local_nodes', 'path': 'meaning-source.json'}
        self.write('meaning-spec.json', spec)
        self.cli('prepare', 'producer', '--spec', 'meaning-spec.json')
        self.cli('run', 'producer', env={'FAKE_RUNNER_PROMPT_RESPONSE': '{"meaning":"New food meaning"}'})
        source['pairs'][0]['local_meaning_from'] = {'experiment': 'producer', 'case': 'food'}
        self.write('source.json', source)
        original = (self.root / 'trial/state.json').read_bytes()
        self.prepare()
        case = self.show()['cases'][0]
        payload = json.loads(case['inputs']['INPUT_JSON'])
        self.assertEqual(payload['local']['meaning'], 'New food meaning')
        self.assertEqual(payload['canonical']['meaning'], 'Fixed cooking meaning')
        self.assertEqual(payload['canonical']['descendants'], [])
        self.assertEqual(case['evidence']['before_step'], 1)
        self.assertEqual(case['evidence']['local_meaning_from']['case'], 'food')
        self.assertEqual((self.root / 'trial/state.json').read_bytes(), original)

    def test_historical_selector_rejects_inconsistent_recorded_step_index(self):
        self.historical_source()
        state = json.loads((self.root / 'trial/state.json').read_text())
        state['steps'][1]['index'] = 2
        self.write('trial/state.json', state)
        result = self.cli('prepare', 'bad-history', '--spec', self.spec, ok=False)
        self.assertIn('before_step', result.stderr)
        self.assertFalse((self.root / 'bad-history').exists())

    def test_before_step_excludes_support_from_later_equivalence(self):
        fixtures.saved_graph_fixture(self, equivalent=True)
        self.write('source.json', {'schema_version': 2, 'corpus': 'notes.json',
                   'canonical_states': {'before': {'trial': 'trial/state.json', 'before_step': 1},
                                        'final': {'trial': 'trial/state.json'}},
                   'pairs': [{'id': name, 'local': {'note_id': 'n3', 'number': '3'},
                              'canonical': {'state': name, 'id': 'C001'}, 'review': {}}
                             for name in ('before', 'final')]})
        spec = json.loads((self.root / 'comparison.json').read_text())
        spec['dataset'] = {'adapter': 'hierarchy_node_pairs', 'path': 'source.json'}
        self.write('spec.json', spec)
        self.prepare()
        before, final = [json.loads(case['inputs']['INPUT_JSON'])['canonical']
                         for case in self.show()['cases']]
        self.assertEqual([entry['subject'] for entry in before['entries']], ['Cooking'])
        self.assertEqual([entry['subject'] for entry in final['entries']], ['Cooking', 'Food'])
        self.assertEqual(before['meaning'], final['meaning'])


if __name__ == '__main__':
    unittest.main()
