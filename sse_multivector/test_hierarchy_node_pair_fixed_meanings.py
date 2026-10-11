"""Fixed-meaning Compare preparation and diagnostics on native offline paths."""

import hashlib
import json
import unittest

from sse_multivector import experiment_inputs
from sse_multivector import extraction_pipeline as engine
from sse_multivector import test_hierarchy_node_pairs as fixtures


DIRECTIONS = ('local_contains_canonical', 'canonical_contains_local')


class HierarchyNodePairFixedMeaningTests(unittest.TestCase):
    setUp = fixtures.HierarchyNodePairsTests.setUp
    write = fixtures.HierarchyNodePairsTests.write
    cli = fixtures.HierarchyNodePairsTests.cli
    prepare = fixtures.HierarchyNodePairsTests.prepare
    show = fixtures.HierarchyNodePairsTests.show
    calls = fixtures.HierarchyNodePairsTests.calls
    source = fixtures.HierarchyNodePairsTests.source
    local_source = fixtures.HierarchyNodePairsTests.local_source
    saved_meaning_source = fixtures.HierarchyNodePairsTests.saved_meaning_source

    def original(self, *, with_meaning=True, schema_version=2):
        if with_meaning:
            source = self.saved_meaning_source(schema_version=4)
        else:
            source = self.source()
        source['schema_version'] = schema_version
        self.write('source.json', source)
        self.prepare('original')
        envelope_path = self.root / 'original/experiment.json'
        self.write('fixed-source.json', {
            'prepared_experiment': {'path': 'original',
                'sha256': hashlib.sha256(envelope_path.read_bytes()).hexdigest()},
            'input_view': 'fixed_meanings'})
        spec = json.loads(self.spec.read_text())
        (self.root / 'compare-v75.txt').write_text('GENERIC PROMPT Compare fixed meanings. {INPUT_JSON}')
        spec['prompt'] = {'id': 'Compare-v75-fixture', 'path': 'compare-v75.txt'}
        spec['dataset'] = {'adapter': 'hierarchy_node_pairs', 'path': 'fixed-source.json'}
        spec['runner']['output_schema'] = self.schema()
        self.write('fixed-spec.json', spec)
        return self.show('original')['cases'][0]

    @staticmethod
    def schema():
        text = {'type': 'string', 'minLength': 1}
        question = {'type': 'object', 'properties': {
            'id': {'type': 'string', 'enum': list(DIRECTIONS)}, 'question': text},
            'required': ['id', 'question'], 'additionalProperties': False}
        answer = {'type': 'object', 'properties': {
            'question_id': {'type': 'string', 'enum': list(DIRECTIONS)},
            'answer': {'type': ['string', 'null'], 'minLength': 1},
            'justification': text},
            'required': ['question_id', 'answer', 'justification'],
            'additionalProperties': False}
        return {'type': 'object', 'properties': {
            'meaning': text,
            'questions': {'type': 'array', 'minItems': 2, 'maxItems': 2, 'items': question},
            'answers': {'type': 'array', 'minItems': 2, 'maxItems': 2, 'items': answer},
            'relation': {'type': 'string', 'enum': ['equivalent', *DIRECTIONS, 'neither', 'uncertain']},
            'reason': text},
            'required': ['meaning', 'questions', 'answers', 'relation', 'reason'],
            'additionalProperties': False}

    def project(self, name='fixed', *, ok=True):
        return self.cli('prepare', name, '--spec', 'fixed-spec.json', ok=ok)

    @staticmethod
    def payload():
        return {'local': {'subject': 'Vegetables', 'meaning': 'Vegetables intended to be cooked.'},
                'canonical': {'id': 'C3', 'subject': 'C3', 'meaning': 'Fixed C3',
                              'parents': ['C1', 'C2'], 'ancestors': [], 'descendants': []}}

    @classmethod
    def answer(cls, relation='canonical_contains_local'):
        return {'meaning': cls.payload()['local']['meaning'],
                'questions': [dict(id=direction, question='Does this boundary admit a counterexample?')
                              for direction in DIRECTIONS],
                'answers': [dict(question_id=direction,
                                answer='A counterexample.' if i == 0 else 'Full coverage holds.',
                                justification='Decisive fixed-meaning scope basis.')
                            for i, direction in enumerate(DIRECTIONS)],
                'relation': relation, 'reason': 'Decisive relation basis.'}

    def validate(self, value):
        case = {'inputs': {'INPUT_JSON': json.dumps(self.payload())}}
        return experiment_inputs.validate({'adapter': 'hierarchy_node_pairs'}, case,
                                          json.dumps(value), self.schema())['parsed']

    def test_projection_preserves_native_evidence_and_removes_source_text(self):
        original = self.original()
        self.project()
        case = self.show('fixed')['cases'][0]
        before = json.loads(original['inputs']['INPUT_JSON'])
        after = json.loads(case['inputs']['INPUT_JSON'])
        self.assertEqual(case['id'], original['id'])
        self.assertEqual(after['local'], {'subject': before['local']['entry']['subject'],
                                        'meaning': before['local']['meaning']})
        expected = {key: before['canonical'][key] for key in
                    ('id', 'subject', 'meaning', 'parents', 'ancestors', 'descendants')}
        expected['ancestors'] = [{key: node[key] for key in ('id', 'subject', 'meaning', 'parents')}
                                 for node in before['canonical']['ancestors']]
        expected['descendants'] = [{key: node[key] for key in ('id', 'subject', 'meaning', 'parents')}
                                   for node in before['canonical']['descendants']]
        self.assertEqual(after['canonical'], expected)
        for key, value in original['evidence'].items():
            self.assertEqual(case['evidence'][key], value)
        self.assertEqual(case['evidence']['unprojected_input'], before)
        self.assertEqual(case['evidence']['input_view'], 'fixed_meanings')
        for private in ('FULL LOCAL POST', 'Local entry context', 'Original ancestor',
                        'Canonical support', 'REVIEW ONLY', 'bootstrap'):
            self.assertNotIn(private, case['prompt'])
        plan = json.loads((self.root / 'fixed/experiment.json').read_text())['plan']
        original_plan = json.loads((self.root / 'original/experiment.json').read_text())['plan']
        for name, digest in original_plan['sources'].items():
            self.assertEqual(plan['sources'][name], digest)
        for name, digest in original_plan['files'].items():
            self.assertEqual(plan['sources'][str(self.root / 'original' / name)], digest)
        self.assertEqual(len(self.calls()), 1)  # Only the offline meaning producer ran.

    def test_projection_requires_independent_fixed_meaning(self):
        self.original(with_meaning=False)
        failure = self.project(ok=False)
        self.assertIn('meaning', failure.stderr)
        self.assertFalse((self.root / 'fixed').exists())
        self.assertEqual(self.calls(), [])

    def test_projection_requires_recursive_schema_two_graph(self):
        self.original(schema_version=1)
        failure = self.project(ok=False)
        self.assertIn('descendants', failure.stderr)
        self.assertFalse((self.root / 'fixed').exists())

    def test_inherited_source_and_config_tampering_fail_preparation(self):
        self.original()
        for index, path in enumerate((self.root / 'notes.json',
                                      self.root / 'original/runner-config.json')):
            with self.subTest(path=path):
                before = path.read_bytes()
                path.write_bytes(before + b'\n')
                failure = self.project(f'changed-{index}', ok=False)
                self.assertIn('changed', failure.stderr)
                self.assertFalse((self.root / f'changed-{index}').exists())
                path.write_bytes(before)
        self.assertEqual(len(self.calls()), 1)

    def test_forged_pinned_envelope_fails_internal_digest(self):
        self.original()
        path = self.root / 'original/experiment.json'
        envelope = json.loads(path.read_text())
        envelope['plan']['cases'][0]['inputs']['INPUT_JSON'] = '{}'
        path.write_text(json.dumps(envelope))
        reference = json.loads((self.root / 'fixed-source.json').read_text())
        reference['prepared_experiment']['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.write('fixed-source.json', reference)
        failure = self.project(ok=False)
        self.assertIn('prepared experiment changed', failure.stderr)
        self.assertFalse((self.root / 'fixed').exists())

    def test_projection_cannot_inherit_mechanical_answers_or_other_adapters(self):
        self.original()
        path = self.root / 'original/experiment.json'
        original = json.loads(path.read_text())
        for index, issue in enumerate(('mechanical', 'adapter')):
            envelope = json.loads(json.dumps(original))
            if issue == 'mechanical':
                envelope['plan']['cases'][0]['mechanical'] = {'parsed': self.answer()}
            else:
                envelope['plan']['dataset']['adapter'] = 'generic'
            envelope['sha256'] = hashlib.sha256(
                engine._canonical_json_bytes(envelope['plan'])).hexdigest()
            path.write_text(json.dumps(envelope))
            source = json.loads((self.root / 'fixed-source.json').read_text())
            source['prepared_experiment']['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
            self.write('fixed-source.json', source)
            with self.subTest(issue=issue):
                failure = self.project(f'wrong-original-{index}', ok=False)
                self.assertIn('mechanical' if issue == 'mechanical' else 'hierarchy_node_pairs',
                              failure.stderr)
                self.assertFalse((self.root / f'wrong-original-{index}').exists())
        self.assertEqual(len(self.calls()), 1)

    def test_five_field_output_and_branch_uncertainty_on_native_offline_runner(self):
        original = self.original()
        self.project()
        value = self.answer(relation='uncertain')
        value['reason'] = 'Both selected answers settled; a canonical branch conflict remains.'
        self.cli('run', 'fixed', env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(value)})
        self.assertEqual(self.show('fixed')['cases'][0]['parsed'], value)
        self.assertEqual(value['meaning'], json.loads(original['inputs']['INPUT_JSON'])['local']['meaning'])
        self.assertEqual(self.validate(value), value)

    def test_diagnostic_question_and_answer_ids_are_bijective(self):
        valid = self.answer()
        self.assertEqual(self.validate(valid), valid)
        candidates = []
        for field, key in (('questions', 'id'), ('answers', 'question_id')):
            duplicate = json.loads(json.dumps(valid))
            duplicate[field][1][key] = duplicate[field][0][key]
            candidates.append(duplicate)
            missing = json.loads(json.dumps(valid))
            missing[field].pop()
            candidates.append(missing)
        unknown = json.loads(json.dumps(valid))
        unknown['answers'][0]['question_id'] = 'unasked-direction'
        candidates.append(unknown)
        extra = dict(valid, unexpected='unsupported')
        candidates.append(extra)
        for candidate in candidates:
            with self.subTest(candidate=candidate), self.assertRaises(ValueError):
                self.validate(candidate)

    def test_null_answers_and_meaning_copy_are_validated_without_semantic_gold(self):
        unresolved = self.answer(relation='uncertain')
        unresolved['answers'][0]['answer'] = None
        self.assertEqual(self.validate(unresolved), unresolved)
        for relation in ('neither', 'equivalent', *DIRECTIONS):
            bad = json.loads(json.dumps(unresolved))
            bad['relation'] = relation
            with self.subTest(relation=relation), self.assertRaises(ValueError):
                self.validate(bad)
        for field, replacement in (('meaning', 'A reinterpreted local meaning'), ('meaning', None)):
            bad = dict(unresolved, **{field: replacement})
            with self.subTest(replacement=replacement), self.assertRaises(ValueError):
                self.validate(bad)
        for key, replacement in (('answer', ''), ('answer', True), ('justification', '')):
            bad = json.loads(json.dumps(unresolved))
            bad['answers'][1][key] = replacement
            with self.subTest(key=key, replacement=replacement), self.assertRaises(ValueError):
                self.validate(bad)


class HierarchyNodePairSymmetricMeaningTests(unittest.TestCase):
    setUp = HierarchyNodePairFixedMeaningTests.setUp
    write = HierarchyNodePairFixedMeaningTests.write
    cli = HierarchyNodePairFixedMeaningTests.cli
    prepare = HierarchyNodePairFixedMeaningTests.prepare
    show = HierarchyNodePairFixedMeaningTests.show
    calls = HierarchyNodePairFixedMeaningTests.calls
    source = HierarchyNodePairFixedMeaningTests.source
    local_source = HierarchyNodePairFixedMeaningTests.local_source
    saved_meaning_source = HierarchyNodePairFixedMeaningTests.saved_meaning_source
    original = HierarchyNodePairFixedMeaningTests.original
    project = HierarchyNodePairFixedMeaningTests.project

    @staticmethod
    def schema():
        schema = HierarchyNodePairFixedMeaningTests.schema()
        del schema['properties']['meaning']
        schema['required'].remove('meaning')
        directions = ['A_contains_B', 'B_contains_A']
        schema['properties']['relation']['enum'] = ['equivalent', *directions, 'neither', 'uncertain']
        schema['properties']['questions']['items']['properties']['id']['enum'] = directions
        schema['properties']['answers']['items']['properties']['question_id']['enum'] = directions
        return schema

    def symmetric_source(self, *, projected=False):
        original = self.original()
        if projected:
            spec = json.loads((self.root / 'fixed-spec.json').read_text())
            spec['runner']['output_schema'] = HierarchyNodePairFixedMeaningTests.schema()
            self.write('legacy-fixed-source.json', json.loads((self.root / 'fixed-source.json').read_text()))
            spec['dataset']['path'] = 'legacy-fixed-source.json'
            self.write('legacy-fixed-spec.json', spec)
            self.cli('prepare', 'legacy-fixed', '--spec', 'legacy-fixed-spec.json')
            directory = 'legacy-fixed'
        else:
            directory = 'original'
        envelope = self.root / directory / 'experiment.json'
        self.write('fixed-source.json', {
            'prepared_experiment': {'path': directory,
                'sha256': hashlib.sha256(envelope.read_bytes()).hexdigest()},
            'input_view': 'symmetric_fixed_meanings'})
        return original, directory

    def test_symmetric_native_projection_strips_graph_and_keeps_receipts(self):
        original, directory = self.symmetric_source()
        self.project()
        case = self.show('fixed')['cases'][0]
        before = json.loads(original['inputs']['INPUT_JSON'])
        self.assertEqual(json.loads(case['inputs']['INPUT_JSON']), {
            'A': {'subject': before['local']['entry']['subject'],
                  'meaning': before['local']['meaning']},
            'B': {key: before['canonical'][key] for key in ('subject', 'meaning')}})
        self.assertEqual(case['evidence']['source_input'], before)
        self.assertEqual(case['evidence']['local_meaning_from'],
                         original['evidence']['local_meaning_from'])
        self.assertEqual(case['evidence']['input_view'], 'symmetric_fixed_meanings')
        for private in ('FULL LOCAL POST', 'Local entry context', 'REVIEW ONLY',
                        'parents', 'ancestors', 'descendants', 'C0', 'C1', 'C2', 'C4'):
            self.assertNotIn(private, case['prompt'])
        plan = json.loads((self.root / 'fixed/experiment.json').read_text())['plan']
        self.assertEqual(plan['preparation']['input_view'], 'symmetric_fixed_meanings')
        self.assertIn(str(self.root / directory / 'experiment.json'), plan['sources'])
        self.assertFalse(plan['preparation']['application_allowed'])
        self.assertEqual(len(self.calls()), 1)

    def test_symmetric_native_projection_accepts_existing_fixed_meanings(self):
        original, _ = self.symmetric_source(projected=True)
        self.project()
        case = self.show('fixed')['cases'][0]
        legacy = self.show('legacy-fixed')['cases'][0]
        self.assertEqual(case['evidence']['source_input'],
                         json.loads(legacy['inputs']['INPUT_JSON']))
        self.assertEqual(case['evidence']['source_input_view'], 'fixed_meanings')
        self.assertEqual(case['evidence']['unprojected_input'],
                         json.loads(original['inputs']['INPUT_JSON']))

    def test_symmetric_projection_requires_independent_meanings(self):
        self.original(with_meaning=False)
        source = json.loads((self.root / 'fixed-source.json').read_text())
        source['input_view'] = 'symmetric_fixed_meanings'
        self.write('fixed-source.json', source)
        failure = self.project(ok=False)
        self.assertIn('fixed meaning must be nonempty', failure.stderr)
        self.assertEqual(self.calls(), [])

    def test_symmetric_projection_does_not_require_recursive_graph_fields(self):
        self.original(schema_version=1)
        source = json.loads((self.root / 'fixed-source.json').read_text())
        source['input_view'] = 'symmetric_fixed_meanings'
        self.write('fixed-source.json', source)
        self.project()
        self.assertEqual(set(json.loads(self.show('fixed')['cases'][0]['inputs']['INPUT_JSON'])),
                         {'A', 'B'})

    def test_symmetric_four_field_output_on_native_runner_and_strict_validation(self):
        self.symmetric_source()
        self.project()
        directions = ['A_contains_B', 'B_contains_A']
        value = {'questions': [dict(id=d, question='Can the child escape this parent?')
                               for d in directions],
                 'answers': [dict(question_id=d, answer='A concrete counterexample.',
                                 justification='Whole-child admission and parent exclusion.')
                             for d in directions],
                 'relation': 'neither', 'reason': 'Both directions have counterexamples.'}
        self.cli('run', 'fixed', env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(value)})
        case = self.show('fixed')['cases'][0]
        self.assertEqual(case['status'], 'valid')
        self.assertEqual(case['parsed'], value)
        invalid = [dict(value, meaning='Removed output'),
                   dict(value, relation='local_contains_canonical')]
        for field, identifier in (('questions', 'id'), ('answers', 'question_id')):
            duplicate = json.loads(json.dumps(value))
            duplicate[field][1][identifier] = duplicate[field][0][identifier]
            invalid.append(duplicate)
        unresolved = json.loads(json.dumps(value))
        unresolved['answers'][0]['answer'] = None
        invalid.append(unresolved)
        for bad in invalid:
            with self.subTest(answer=bad), self.assertRaises(ValueError):
                experiment_inputs.validate({'adapter': 'hierarchy_node_pairs'}, case,
                                           json.dumps(bad), self.schema())
        unresolved['relation'] = 'uncertain'
        self.assertEqual(experiment_inputs.validate({'adapter': 'hierarchy_node_pairs'}, case,
            json.dumps(unresolved), self.schema())['parsed'], unresolved)


if __name__ == '__main__':
    unittest.main()
