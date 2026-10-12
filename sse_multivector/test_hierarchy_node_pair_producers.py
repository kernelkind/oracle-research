"""Canonical meanings bound to original Bootstrap receipts through the native CLI."""

import hashlib
import json
import unittest

from sse_multivector import test_hierarchy_node_pairs as fixtures


class HierarchyNodePairProducerTests(unittest.TestCase):
    setUp = fixtures.HierarchyNodePairsTests.setUp
    write = fixtures.HierarchyNodePairsTests.write
    cli = fixtures.HierarchyNodePairsTests.cli
    prepare = fixtures.HierarchyNodePairsTests.prepare
    show = fixtures.HierarchyNodePairsTests.show
    calls = fixtures.HierarchyNodePairsTests.calls
    source = fixtures.HierarchyNodePairsTests.source
    local_source = fixtures.HierarchyNodePairsTests.local_source

    def canonical_producer_source(self, *, answer=None, run=True, name='bootstrap'):
        producer = self.local_source()
        producer['schema_version'] = 4
        producer['nodes'][0]['local'] = {'note_id': 'canonical-post', 'number': '1.1'}
        self.write(name + '-source.json', producer)
        spec = json.loads(self.spec.read_text())
        spec['dataset']['path'] = name + '-source.json'
        self.write(name + '-spec.json', spec)
        self.cli('prepare', name, '--spec', name + '-spec.json')
        if run:
            self.cli('run', name, env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(
                {'meaning': 'Materials used in food preparation.'} if answer is None else answer)})
        source = self.source()
        node = source['canonical_states']['current'][3]
        node['subject'] = 'Ingredients'
        del node['meaning']
        node['meaning_from'] = {'experiment': name, 'case': 'one'}
        self.write('source.json', source)
        return source

    def test_canonical_meaning_from_copies_validated_original_producer(self):
        self.canonical_producer_source()
        self.prepare()
        case = self.show()['cases'][0]
        payload = json.loads(case['inputs']['INPUT_JSON'])
        self.assertEqual(payload['canonical']['meaning'], 'Materials used in food preparation.')
        self.assertNotIn('meaning_from', payload['canonical'])
        self.assertNotIn('bootstrap', case['prompt'])
        self.assertEqual(len(self.calls()), 1)

    def test_canonical_provenance_is_protected_and_excluded_from_symmetric_input(self):
        source = self.canonical_producer_source()
        source['pairs'][0]['local_meaning'] = 'Vegetables intended to be cooked.'
        self.write('source.json', source)
        self.prepare()
        plan = json.loads((self.root / 'E1/experiment.json').read_text())['plan']
        produced = self.show('bootstrap')['cases'][0]
        expected = {'C3': {'experiment': str(self.root / 'bootstrap'), 'case': 'one',
                           'receipt': produced['receipt']}}
        self.assertEqual(self.show()['cases'][0]['evidence']['canonical_meaning_from'], expected)
        producer_plan = json.loads((self.root / 'bootstrap/experiment.json').read_text())['plan']
        for path in (self.root / 'bootstrap/experiment.json',
                     self.root / 'bootstrap/runner-config.json',
                     self.root / 'bootstrap-source.json', self.root / 'notes.json',
                     self.root / 'bootstrap/run/manifest.json',
                     self.root / 'bootstrap/run/results.jsonl'):
            self.assertEqual(plan['sources'][str(path)], hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(producer_plan['dataset']['adapter'], 'hierarchy_local_nodes')
        self.write('symmetric.json', {'prepared_experiment': {'path': 'E1',
            'sha256': hashlib.sha256((self.root / 'E1/experiment.json').read_bytes()).hexdigest()},
            'input_view': 'symmetric_fixed_meanings'})
        spec = json.loads(self.spec.read_text())
        spec['dataset']['path'] = 'symmetric.json'
        self.write('symmetric-spec.json', spec)
        self.cli('prepare', 'symmetric', '--spec', 'symmetric-spec.json')
        case = self.show('symmetric')['cases'][0]
        self.assertEqual(json.loads(case['inputs']['INPUT_JSON']), {
            'A': {'subject': 'Vegetables', 'meaning': 'Vegetables intended to be cooked.'},
            'B': {'subject': 'Ingredients', 'meaning': 'Materials used in food preparation.'}})
        self.assertEqual(case['evidence']['canonical_meaning_from'], expected)
        for excluded in ('bootstrap', 'receipt', 'context', 'CANONICAL POST', 'REVIEW ONLY'):
            self.assertNotIn(excluded, case['prompt'])
        self.assertEqual(len(self.calls()), 1)

    def test_canonical_producer_rejects_mismatched_original_entry_post_or_tree(self):
        source = self.canonical_producer_source()
        original = json.loads((self.root / 'notes.json').read_text())
        for index, change in enumerate(('selector', 'subject', 'context', 'ancestor',
                                         'descendant', 'post')):
            with self.subTest(change=change):
                candidate = json.loads(json.dumps(source))
                corpus = json.loads(json.dumps(original))
                selected_note = corpus['notes'][1]
                candidate['corpus'] = 'current-notes.json'
                if change == 'selector':
                    candidate['canonical_states']['current'][3]['entries'][0]['number'] = '1'
                elif change in ('subject', 'context'):
                    selected_note['subjects'][1][change] += ' changed'
                elif change == 'ancestor':
                    selected_note['subjects'][0]['context'] += ' changed'
                elif change == 'descendant':
                    selected_note['subjects'].append({'number': '1.1.1',
                        'subject': 'Added ingredient', 'context': 'Not in the producer tree'})
                else:
                    selected_note['text'] += ' changed'
                self.write('current-notes.json', corpus)
                self.write('source.json', candidate)
                result = self.cli('prepare', f'mismatch-{index}', '--spec', self.spec, ok=False)
                self.assertIn('does not match original', result.stderr)
                self.assertFalse((self.root / f'mismatch-{index}').exists())
        self.assertEqual(len(self.calls()), 1)

    def test_canonical_producer_requires_valid_nonnull_answer(self):
        for index, (answer, run) in enumerate((({'meaning': None}, True),
                                              ({'meaning': 'Unrun'}, False))):
            with self.subTest(answer=answer, run=run):
                self.canonical_producer_source(answer=answer, run=run, name=f'bootstrap-{index}')
                result = self.cli('prepare', f'bad-answer-{index}', '--spec', self.spec, ok=False)
                self.assertIn('meaning', result.stderr)
                self.assertFalse((self.root / f'bad-answer-{index}').exists())

    def test_canonical_producer_rejects_malformed_saved_answer(self):
        self.canonical_producer_source(run=False)
        self.cli('run', 'bootstrap', env={'FAKE_RUNNER_PROMPT_RESPONSE': '{"meaning":42}'}, ok=False)
        result = self.cli('prepare', 'bad-output', '--spec', self.spec, ok=False)
        self.assertIn('valid saved meaning', result.stderr)
        self.assertFalse((self.root / 'bad-output').exists())

    def test_canonical_literal_and_producer_meanings_are_mutually_exclusive(self):
        source = self.canonical_producer_source()
        source['canonical_states']['current'][3]['meaning'] = 'Literal replacement'
        self.write('source.json', source)
        result = self.cli('prepare', 'both', '--spec', self.spec, ok=False)
        self.assertIn('canonical node.meaning', result.stderr)
        self.assertIn('not supported', result.stderr)
        self.assertFalse((self.root / 'both').exists())

    def test_canonical_producer_reference_is_strict(self):
        source = self.canonical_producer_source()
        for index, reference in enumerate((None, {}, {'experiment': 'bootstrap'},
                {'experiment': 'bootstrap', 'case': 'missing'},
                {'experiment': 'bootstrap', 'case': 'one', 'extra': True})):
            with self.subTest(reference=reference):
                candidate = json.loads(json.dumps(source))
                candidate['canonical_states']['current'][3]['meaning_from'] = reference
                self.write('source.json', candidate)
                self.cli('prepare', f'bad-reference-{index}', '--spec', self.spec, ok=False)
                self.assertFalse((self.root / f'bad-reference-{index}').exists())

    def test_canonical_producer_rejects_changed_receipt(self):
        self.canonical_producer_source()
        path = self.root / 'bootstrap/run/results.jsonl'
        record = json.loads(path.read_text())
        record['final_output_raw'] = '{"meaning":"Forged meaning"}'
        path.write_text(json.dumps(record) + '\n')
        self.cli('prepare', 'forged', '--spec', self.spec, ok=False)
        self.assertFalse((self.root / 'forged').exists())

    def test_canonical_producer_rejects_wrong_adapter(self):
        source = self.canonical_producer_source(run=False)
        self.write('generic-source.json', {'cases': [
            {'id': 'one', 'inputs': {'INPUT_JSON': '{"meaning":"Fake original input"}'}}]})
        spec = json.loads((self.root / 'bootstrap-spec.json').read_text())
        spec['dataset'] = {'adapter': 'generic', 'path': 'generic-source.json'}
        self.write('generic-spec.json', spec)
        self.cli('prepare', 'generic', '--spec', 'generic-spec.json')
        self.cli('run', 'generic', env={'FAKE_RUNNER_PROMPT_RESPONSE':
                                     '{"meaning":"Generic output is not a Bootstrap receipt"}'})
        source['canonical_states']['current'][3]['meaning_from']['experiment'] = 'generic'
        self.write('source.json', source)
        result = self.cli('prepare', 'wrong-adapter', '--spec', self.spec, ok=False)
        self.assertIn('hierarchy_local_nodes experiment', result.stderr)
        self.assertFalse((self.root / 'wrong-adapter').exists())

    def test_changed_protected_producer_source_prevents_fresh_preparation(self):
        self.canonical_producer_source()
        self.prepare()
        path = self.root / 'bootstrap-source.json'
        path.write_text(path.read_text() + '\n')
        result = self.cli('prepare', 'E2', '--spec', self.spec, ok=False)
        self.assertIn('saved meaning source changed', result.stderr)
        self.assertFalse((self.root / 'E2').exists())
        self.assertEqual(len(self.calls()), 1)

    def test_canonical_ancestor_producer_is_bound_and_recorded_outside_input(self):
        source = self.canonical_producer_source()
        ancestor = source['canonical_states']['current'][1]
        ancestor['subject'] = 'Ingredients'
        del ancestor['meaning']
        ancestor['meaning_from'] = {'experiment': 'bootstrap', 'case': 'one'}
        self.write('source.json', source)
        self.prepare()
        case = self.show()['cases'][0]
        payload = json.loads(case['inputs']['INPUT_JSON'])
        selected_ancestor = next(node for node in payload['canonical']['ancestors']
                                 if node['id'] == 'C1')
        self.assertEqual(selected_ancestor['meaning'], 'Materials used in food preparation.')
        self.assertNotIn('meaning_from', selected_ancestor)
        self.assertEqual(set(case['evidence']['canonical_meaning_from']), {'C1', 'C3'})
        self.assertEqual(case['evidence']['canonical_meaning_from']['C1'],
                         case['evidence']['canonical_meaning_from']['C3'])
        self.assertEqual(len(self.calls()), 1)

    def test_canonical_producer_requires_one_original_founder_and_its_subject(self):
        source = self.canonical_producer_source()
        for index, change in enumerate(('additional-founder', 'canonical-subject')):
            with self.subTest(change=change):
                candidate = json.loads(json.dumps(source))
                node = candidate['canonical_states']['current'][3]
                if change == 'additional-founder':
                    node['entries'].append({'note_id': 'canonical-post', 'number': '1'})
                    error = 'one original supporting entry'
                else:
                    node['subject'] = 'Changed canonical subject'
                    error = 'subject does not match original entry'
                self.write('source.json', candidate)
                result = self.cli('prepare', f'bad-founder-{index}', '--spec', self.spec, ok=False)
                self.assertIn(error, result.stderr)
                self.assertFalse((self.root / f'bad-founder-{index}').exists())
        self.assertEqual(len(self.calls()), 1)


if __name__ == '__main__':
    unittest.main()
