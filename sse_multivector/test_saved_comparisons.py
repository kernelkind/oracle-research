"""Receipt-bound fixed comparison inputs and reversals through the native CLI."""

import hashlib
import json
from pathlib import Path
import unittest

from sse_multivector import test_experiment as fixtures


class SavedComparisonsTests(unittest.TestCase):
    setUp = fixtures.ExperimentTests.setUp
    write = fixtures.ExperimentTests.write
    cli = fixtures.ExperimentTests.cli
    prepare = fixtures.ExperimentTests.prepare
    show = fixtures.ExperimentTests.show
    calls = fixtures.ExperimentTests.calls

    def producer(self, name='producer', *, payload=None, run=True, answer=None):
        self.prompt.write_text('GENERIC PROMPT {INPUT_JSON}')
        payload = payload if payload is not None else {
            'A': {'subject': 'Devices', 'meaning': 'Devices with lamps.'},
            'B': {'subject': 'Red devices', 'meaning': 'Devices with red lamps.'}}
        self.write(name + '-cases.json', {'cases': [{'id': 'pair',
            'inputs': {'INPUT_JSON': json.dumps(payload)},
            'evidence': {'private': 'OLD SOURCE EVIDENCE'}}]})
        spec = json.loads(self.spec.read_text())
        spec['dataset'] = {'adapter': 'generic', 'path': name + '-cases.json'}
        spec['runner']['output_schema'] = {'type': 'object'}
        self.write(name + '-spec.json', spec)
        self.cli('prepare', name, '--spec', name + '-spec.json')
        if run:
            self.cli('run', name, env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(
                self.answer() if answer is None else answer)})
        return {'path': name, 'sha256': hashlib.sha256(
            (self.root / name / 'experiment.json').read_bytes()).hexdigest()}

    @staticmethod
    def answer():
        directions = ('A_contains_B', 'B_contains_A')
        return {'questions': [{'id': key, 'question': 'OLD QUESTION ' + key}
                              for key in directions],
                'answers': [{'question_id': key, 'answer': 'OLD ANSWER ' + key,
                             'justification': 'OLD PROOF ' + key} for key in directions],
                'relation': 'neither', 'reason': 'OLD HISTORICAL LABEL'}

    def comparison_source(self, reference, *, reverse=False):
        source = {'schema_version': 1, 'saved_comparisons': [{
            'id': 'exact', 'experiment': reference, 'case_id': 'pair', 'reverse': reverse,
            'review': {'expected_relation': None, 'purpose': 'REVIEW ONLY'}}]}
        self.write('source.json', source)
        spec = json.loads(self.spec.read_text())
        spec['dataset'] = {'adapter': 'hierarchy_node_pairs', 'path': 'source.json'}
        schema = Path(__file__).with_name('shr_single_pair') / 'Hierarchy-compare-v179.output.schema.json'
        spec['runner']['output_schema'] = json.loads(schema.read_text())
        self.write('spec.json', spec)
        return source

    def test_saved_comparison_prepares_exact_input_without_old_answers(self):
        self.comparison_source(self.producer())
        self.prepare()
        saved = self.show('producer')['cases'][0]
        case = self.show()['cases'][0]
        self.assertEqual(case['inputs'], saved['inputs'])
        self.assertEqual(case['evidence']['saved_comparison']['receipt'], saved['receipt'])
        for excluded in ('OLD QUESTION', 'OLD ANSWER', 'OLD PROOF',
                         'OLD HISTORICAL LABEL', 'OLD SOURCE EVIDENCE', 'REVIEW ONLY'):
            self.assertNotIn(excluded, case['prompt'])
        self.assertEqual(len(self.calls()), 1)

    def test_saved_comparison_can_pin_exact_original_receipt(self):
        source = self.comparison_source(self.producer())
        receipt = self.show('producer')['cases'][0]['receipt']
        source['saved_comparisons'][0]['record_sha256'] = receipt['record_sha256']
        self.write('source.json', source)
        self.prepare()
        selected = self.show()['cases'][0]
        self.assertEqual(selected['evidence']['saved_comparison']['receipt'], receipt)
        self.assertEqual(len(self.calls()), 1)

    def test_saved_comparison_rejects_wrong_or_malformed_receipt_pin(self):
        source = self.comparison_source(self.producer())
        for index, digest in enumerate(('0' * 64, 'not-a-digest')):
            with self.subTest(digest=digest):
                source['saved_comparisons'][0]['record_sha256'] = digest
                self.write('source.json', source)
                result = self.cli('prepare', f'wrong-receipt-{index}', '--spec', self.spec, ok=False)
                self.assertIn('receipt hash differs' if index == 0 else 'SHA-256 digest',
                              result.stderr)
                self.assertFalse((self.root / f'wrong-receipt-{index}').exists())
        self.assertEqual(len(self.calls()), 1)

    def isolated_comparison_source(self):
        source = self.comparison_source(self.producer())
        source['saved_comparisons'][0]['review'].update(
            comparison_role='isolated-forward', reversal_pair='fixed-pair')
        source['saved_comparisons'].append({
            'id': 'reverse', 'experiment': source['saved_comparisons'][0]['experiment'],
            'case_id': 'pair', 'reverse': True, 'review': {
                'comparison_role': 'isolated-reverse', 'reversal_pair': 'fixed-pair'}})
        self.write('source.json', source)
        return source

    def test_saved_comparison_reports_receipt_bound_reversal_consistency(self):
        self.isolated_comparison_source()
        self.prepare()
        self.cli('run', 'E1', env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(self.answer())})
        summary = self.show()['node_pair_consistency']
        self.assertEqual(summary['reversals']['complete_pairs'], 1)
        self.assertEqual(summary['reversals']['conflicts'], [])
        self.assertEqual(summary['eligible_cases'], 2)
        self.assertTrue(summary['complete'])

    def test_saved_comparison_reports_reversal_conflict(self):
        self.isolated_comparison_source()
        self.prepare()
        answer = self.answer()
        answer['relation'] = 'A_contains_B'
        self.cli('run', 'E1', env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(answer)})
        summary = self.show()['node_pair_consistency']
        self.assertEqual(summary['reversals']['complete_pairs'], 1)
        self.assertEqual([row['pair_id'] for row in summary['reversals']['conflicts']],
                         ['fixed-pair'])

    def test_saved_comparison_consistency_does_not_join_unrelated_sources(self):
        first, second = self.producer('first'), self.producer('second')
        source = self.comparison_source(first)
        source['saved_comparisons'] = [
            {'id': name + '-' + direction, 'experiment': reference, 'case_id': 'pair',
             'reverse': direction == 'reverse', 'review': {
                 'comparison_role': 'isolated-' + direction, 'reversal_pair': name}}
            for name, reference in (('first', first), ('second', second))
            for direction in ('forward', 'reverse')]
        self.write('source.json', source)
        self.prepare()
        self.cli('run', 'E1', env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(self.answer())})
        summary = self.show()['node_pair_consistency']
        self.assertEqual(summary['reversals']['complete_pairs'], 2)
        self.assertEqual(summary['endpoints'], 4)
        self.assertTrue(summary['complete'])

    def test_saved_comparison_consistency_rejects_changed_binding(self):
        from sse_multivector import hierarchy_node_pair_consistency as consistency
        self.isolated_comparison_source()
        self.prepare()
        native = self.show()['cases']
        for change in ('payload', 'receipt', 'original', 'reverse', 'role'):
            with self.subTest(change=change):
                cases = json.loads(json.dumps(native))
                saved = cases[0]['evidence']['saved_comparison']
                if change == 'payload':
                    payload = json.loads(cases[0]['inputs']['INPUT_JSON'])
                    payload['A']['meaning'] += ' changed'
                    cases[0]['inputs']['INPUT_JSON'] = json.dumps(payload)
                elif change == 'receipt':
                    saved.pop('receipt')
                elif change == 'original':
                    saved['original_input']['A']['meaning'] += ' changed'
                elif change == 'reverse':
                    saved['selection']['reverse'] = True
                else:
                    cases[0]['evidence']['review']['comparison_role'] = 'isolated-reverse'
                summary = consistency.summarize(cases)
                self.assertEqual(summary['skipped_cases'], [{'case_id': 'exact',
                    'reason': 'invalid_saved_comparison_binding'}])
                self.assertFalse(summary['complete'])

    def test_multiple_experiments_reverse_entire_nodes_and_protect_receipts(self):
        first = self.producer('first')
        second = self.producer('second', payload={
            'A': {'subject': 'Blue devices', 'meaning': 'Devices with blue lamps.'},
            'B': {'subject': 'Devices', 'meaning': 'Devices with lamps.'}})
        source = self.comparison_source(first)
        source['saved_comparisons'].extend([
            {'id': 'reversed', 'experiment': first, 'case_id': 'pair', 'reverse': True},
            {'id': 'second', 'experiment': second, 'case_id': 'pair', 'reverse': False}])
        self.write('source.json', source)
        self.prepare()
        cases = self.show()['cases']
        original = json.loads(self.show('first')['cases'][0]['inputs']['INPUT_JSON'])
        self.assertEqual(json.loads(cases[1]['inputs']['INPUT_JSON']),
                         {'A': original['B'], 'B': original['A']})
        self.assertEqual(cases[2]['inputs'], self.show('second')['cases'][0]['inputs'])
        self.assertEqual(cases[0]['evidence']['saved_comparison']['parsed'], self.answer())
        self.assertNotIn('expected', cases[0])
        plan = json.loads((self.root / 'E1/experiment.json').read_text())['plan']
        for name in ('first', 'second'):
            for relative in ('experiment.json', 'runner-config.json',
                             'run/manifest.json', 'run/results.jsonl'):
                path = self.root / name / relative
                self.assertEqual(plan['sources'][str(path)],
                                 hashlib.sha256(path.read_bytes()).hexdigest())
        self.cli('run', 'E1', env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(self.answer())})
        self.assertEqual(self.show()['summary']['valid'], 3)
        self.prepare('E2')
        self.cli('run', 'E2')
        self.assertTrue(all(case['reused'] for case in self.show('E2')['cases']))
        self.assertEqual(len(self.calls()), 5)

    def test_saved_comparison_requires_strict_fixed_A_B_meanings(self):
        valid = {'A': {'subject': 'Devices', 'meaning': 'Devices with lamps.'},
                 'B': {'subject': 'Red devices', 'meaning': 'Devices with red lamps.'}}
        changes = [('extra-role', {**valid, 'post': 'SOURCE POST'}),
                   ('extra-node-field', {**valid, 'A': {**valid['A'], 'context': 'CONTEXT'}}),
                   ('missing-meaning', {**valid, 'A': {'subject': 'Devices'}}),
                   ('null-meaning', {**valid, 'B': {**valid['B'], 'meaning': None}}),
                   ('blank-meaning', {**valid, 'B': {**valid['B'], 'meaning': '  '}}),
                   ('legacy-roles', {'local': valid['A'], 'canonical': valid['B']})]
        for index, (name, payload) in enumerate(changes):
            with self.subTest(name=name):
                self.comparison_source(self.producer(f'producer-{index}', payload=payload))
                result = self.cli('prepare', f'invalid-{index}', '--spec', self.spec, ok=False)
                self.assertIn('saved comparison', result.stderr)
                self.assertFalse((self.root / f'invalid-{index}').exists())

    def test_saved_comparison_selector_and_reference_are_strict(self):
        source = self.comparison_source(self.producer())
        for index, (field, value) in enumerate((('reverse', 1), ('review', None),
                ('case_id', 'missing'), ('experiment', {}),
                ('experiment', {'path': 'producer', 'sha256': '0' * 64}),
                ('experiment', {'path': 'producer', 'sha256': 'not-a-hash'}))):
            with self.subTest(field=field, value=value):
                candidate = json.loads(json.dumps(source))
                candidate['saved_comparisons'][0][field] = value
                self.write('source.json', candidate)
                self.cli('prepare', f'bad-reference-{index}', '--spec', self.spec, ok=False)
                self.assertFalse((self.root / f'bad-reference-{index}').exists())
        source['saved_comparisons'].append(dict(source['saved_comparisons'][0]))
        self.write('source.json', source)
        result = self.cli('prepare', 'duplicate', '--spec', self.spec, ok=False)
        self.assertIn('duplicate saved comparison id', result.stderr)

    def test_unrun_saved_comparison_has_no_valid_receipt(self):
        self.comparison_source(self.producer(run=False))
        result = self.cli('prepare', 'unrun', '--spec', self.spec, ok=False)
        self.assertIn('valid receipt-bound case', result.stderr)
        self.assertFalse((self.root / 'unrun').exists())
        self.assertEqual(self.calls(), [])

    def test_schema_valid_generic_output_must_also_be_a_comparison(self):
        self.comparison_source(self.producer(answer={'relation': 'neither'}))
        result = self.cli('prepare', 'not-a-comparison', '--spec', self.spec, ok=False)
        self.assertIn('expected questions, answers, relation, and reason', result.stderr)
        self.assertFalse((self.root / 'not-a-comparison').exists())

    def test_saved_hierarchy_node_pair_case_retains_exact_native_input(self):
        source = self.comparison_source(self.producer())
        self.write('native-source.json', source)
        spec = json.loads(self.spec.read_text())
        spec['dataset']['path'] = 'native-source.json'
        self.write('native-spec.json', spec)
        self.cli('prepare', 'native', '--spec', 'native-spec.json')
        self.cli('run', 'native', env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(self.answer())})
        native_case = self.show('native')['cases'][0]
        source = self.comparison_source({'path': 'native', 'sha256': hashlib.sha256(
            (self.root / 'native/experiment.json').read_bytes()).hexdigest()})
        source['saved_comparisons'][0]['case_id'] = 'exact'
        self.write('source.json', source)
        self.prepare()
        selected = self.show()['cases'][0]
        self.assertEqual(selected['inputs'], native_case['inputs'])
        self.assertEqual(selected['evidence']['saved_comparison']['receipt'], native_case['receipt'])
        self.assertEqual(len(self.calls()), 2)

    def test_changed_original_source_or_receipt_is_rejected(self):
        for index, field in enumerate(('source', 'receipt')):
            with self.subTest(field=field):
                name = f'producer-{index}'
                self.comparison_source(self.producer(name))
                if field == 'source':
                    path = self.root / (name + '-cases.json')
                    path.write_text(path.read_text() + '\n')
                else:
                    path = self.root / name / 'run/results.jsonl'
                    record = json.loads(path.read_text())
                    record['final_output_raw'] = '{"relation":"equivalent"}'
                    path.write_text(json.dumps(record) + '\n')
                self.cli('prepare', f'changed-{index}', '--spec', self.spec, ok=False)
                self.assertFalse((self.root / f'changed-{index}').exists())


if __name__ == '__main__':
    unittest.main()
