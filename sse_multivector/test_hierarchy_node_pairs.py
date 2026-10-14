"""Source-bound local/canonical comparisons through the native experiment CLI."""

import hashlib
import json
from pathlib import Path
import unittest

from sse_multivector import experiment_inputs
from sse_multivector import test_experiment as fixtures


def saved_graph_fixture(test, *, equivalent=False):
    """Controlled historical review inputs with native meanings and comparisons.

    This is adapter evidence, not a V3-generated hierarchy or semantic gold.
    """
    from copy import deepcopy
    from sse_multivector import canonical_trial as trial
    notes=[dict(note_id='n1',text='First post',subjects=[
        dict(number='1',subject='Cooking',context='Using heat'),
        dict(number='1.1',subject='EXCLUDED CHILD',context='Child')]),
        dict(note_id='n2',text='Second post',subjects=[
            dict(number='2',subject='Food',context='Intended for cooking')]),
        dict(note_id='n3',text='Third post',subjects=[
            dict(number='3',subject='Ingredients',context='Cooking role')])]
    corpus=test.write('notes.json',dict(schema_version=1,notes=notes))
    test.prompt.write_text('GENERIC PROMPT {INPUT_JSON}')
    base=json.loads(test.spec.read_text())
    bootstrap={**base,'runner':{**base['runner'],'output_schema':{
        'type':'object','properties':{'meaning':{'type':['string','null']}},
        'required':['meaning'],'additionalProperties':False}}}
    comparison={**base,'runner':{**base['runner'],'output_schema':json.loads(
        Path(__file__).with_name('shr_single_pair').joinpath(
            'Hierarchy-compare-v4.output.schema.json').read_text())}}
    test.write('bootstrap.json',bootstrap)
    test.write('comparison.json',comparison)
    state=dict(schema_version=2,corpus=str(corpus),nodes=[],steps=[],index=0,
        roots=[dict(note_id=n['note_id'],number=n['subjects'][0]['number']) for n in notes],
        sources={str(corpus):trial._hash(corpus)},status='complete')
    meanings=['Fixed cooking meaning','Fixed food meaning','Independent meaning']
    for index,(local,meaning) in enumerate(zip(state['roots'],meanings,strict=True)):
        source=test.write(f'meaning-source-{index}.json',dict(schema_version=4,corpus=str(corpus),
            nodes=[dict(id='meaning',local=local,review={})]))
        spec=test.write(f'meaning-spec-{index}.json',{**bootstrap,
            'dataset':dict(adapter='hierarchy_local_nodes',path=str(source))})
        experiment=f'meaning-{index}'
        test.cli('prepare',experiment,'--spec',spec)
        test.cli('run',experiment,env={'FAKE_RUNNER_PROMPT_RESPONSE':json.dumps(dict(meaning=meaning))})
        before=deepcopy(state['nodes'])
        values={}
        if before:
            source=test.write(f'pair-source-{index}.json',dict(schema_version=2,corpus=str(corpus),
                canonical_states=dict(current=before),pairs=[dict(id=n['id'],local=local,
                    local_meaning_from=dict(experiment=experiment,case='meaning'),
                    canonical=dict(state='current',id=n['id']),review={}) for n in before]))
            spec=test.write(f'pair-spec-{index}.json',{**comparison,
                'dataset':dict(adapter='hierarchy_node_pairs',path=str(source))})
            comparison_experiment=f'comparison-{index}'
            test.cli('prepare',comparison_experiment,'--spec',spec)
            relation=('equivalent' if equivalent else 'canonical_contains_local') if index==1 else 'neither'
            test.cli('run',comparison_experiment,env={'FAKE_RUNNER_PROMPT_RESPONSE':json.dumps(
                dict(meaning=meaning,relation=relation,reason='Controlled adapter fixture'))})
            values={c['id']:c['parsed'] for c in test.show(comparison_experiment)['cases']}
        nodes,identifier,error,witness=trial._placement(state,local,meaning,values)
        test.assertIsNone(error)
        state['nodes']=nodes
        state['steps'].append(dict(index=index,local=local,before=before,after=deepcopy(nodes),
            canonical_id=identifier,status='equivalent' if equivalent and index==1 else 'added'))
        state['index']+=1
    (test.root/'trial').mkdir()
    test.write('trial/state.json',state)
    return state


class HierarchyNodePairsTests(unittest.TestCase):
    setUp = fixtures.ExperimentTests.setUp
    write = fixtures.ExperimentTests.write
    cli = fixtures.ExperimentTests.cli
    prepare = fixtures.ExperimentTests.prepare
    show = fixtures.ExperimentTests.show
    calls = fixtures.ExperimentTests.calls

    def counterexample_source(self, run=True, name='producer', symmetric=False,
                              input_json=None, answer_override=None):
        self.prompt.write_text('GENERIC PROMPT DIAGNOSTIC {INPUT_JSON}')
        payload = {'local': {'subject': 'Devices', 'meaning': 'Devices with lamps.'},
                   'canonical': {'id': 'C1', 'subject': 'Red devices',
                                 'meaning': 'Devices with red lamps.',
                                 'parents': [], 'ancestors': [], 'descendants': []}}
        direction = 'canonical_contains_local'
        answer = {
            'answers': [{'question_id': direction,
                'answer': 'A device with a blue lamp.',
                'justification': 'An ordinary device. A device with a red lamp. OLD LABEL.'}],
            'relation': 'neither'}
        if symmetric:
            payload = {role: {key: payload[old][key] for key in ('subject', 'meaning')}
                       for role, old in (('A', 'local'), ('B', 'canonical'))}
            direction = 'B_contains_A'
            answer = {'questions': [
                {'id': 'A_contains_B', 'question': 'Does A cover every B device?'},
                {'id': 'B_contains_A', 'question': 'Can a blue-lamp A device escape B?'}],
                'answers': [
                    {'question_id': 'A_contains_B', 'answer': 'A covers all B devices.',
                     'justification': 'A device with a red lamp. OLD LABEL.'},
                    {**answer['answers'][0], 'question_id': direction}],
                'relation': 'A_contains_B', 'reason': 'OLD VERDICT EXCLUDED'}
        if input_json is None:
            input_json = json.dumps(payload)
        if answer_override is not None:
            answer = answer_override
        self.write(name + '-cases.json', {'cases': [{'id': 'pair',
            'inputs': {'INPUT_JSON': input_json},
            'evidence': {'private': 'OLD TARGET EXCLUDED'}}]})
        spec = json.loads(self.spec.read_text())
        spec['dataset'] = {'adapter': 'generic', 'path': name + '-cases.json'}
        spec['runner']['output_schema'] = {'type': 'object'}
        self.write(name + '-spec.json', spec)
        self.cli('prepare', name, '--spec', name + '-spec.json',
                 *(['--repeat'] if symmetric else []))
        if run:
            self.cli('run', name, env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(answer)})
        envelope = self.root / name / 'experiment.json'
        selected = dict(id='blue', experiment={'path': name,
            'sha256': hashlib.sha256(envelope.read_bytes()).hexdigest()}, case_id='pair',
            direction=direction, field='answer', excerpt=None, reverse=False)
        source = dict(schema_version=1, saved_counterexamples=[selected])
        self.write('checks.json', source)
        spec['dataset']['path'] = 'checks.json'
        self.write('spec.json', spec)
        return source

    def test_saved_symmetric_counterexamples_prepare_blind_cases_and_reverse_nodes(self):
        source = self.counterexample_source(symmetric=True)
        source['saved_counterexamples'].append(dict(source['saved_counterexamples'][0],
            id='red', direction='A_contains_B', field='justification',
            excerpt='A device with a red lamp.', reverse=True))
        self.write('checks.json', source)
        self.prepare('checks')
        cases = self.show('checks')['cases']
        blue, red = [json.loads(case['inputs']['INPUT_JSON']) for case in cases]
        self.assertEqual(blue, {
            'A': {'subject': 'Devices', 'meaning': 'Devices with lamps.'},
            'B': {'subject': 'Red devices', 'meaning': 'Devices with red lamps.'},
            'case': 'A device with a blue lamp.'})
        self.assertEqual(red, {'A': blue['B'], 'B': blue['A'],
                              'case': 'A device with a red lamp.'})
        producer = self.show('producer')['cases'][0]
        for case in cases:
            for excluded in ('OLD TARGET', 'OLD LABEL', 'OLD VERDICT',
                             'A_contains_B', 'B_contains_A', 'justification'):
                self.assertNotIn(excluded, case['prompt'])
            self.assertEqual(case['evidence']['saved_counterexample']['receipt'],
                             producer['receipt'])
            self.assertEqual(case['evidence']['saved_counterexample']['parsed'],
                             producer['parsed'])
        plan = json.loads((self.root / 'checks/experiment.json').read_text())['plan']
        self.assertIn(str(self.root / 'producer/run/results.jsonl'), plan['sources'])
        self.assertFalse(plan['preparation']['application_allowed'])
        self.assertEqual(len(self.calls()), 1)

    def test_saved_counterexamples_reject_direction_and_input_family_mismatches(self):
        for symmetric, direction in ((True, 'canonical_contains_local'),
                                     (False, 'A_contains_B')):
            with self.subTest(symmetric=symmetric):
                source = self.counterexample_source(
                    symmetric=symmetric, name='producer-' + str(symmetric))
                source['saved_counterexamples'][0]['direction'] = direction
                self.write('checks.json', source)
                destination = 'mismatched-' + str(symmetric)
                failure = self.cli('prepare', destination, '--spec', self.spec, ok=False)
                self.assertIn('direction does not match saved input', failure.stderr)
                self.assertFalse((self.root / destination).exists())

    def test_saved_counterexamples_nodes_from_preserves_case_and_both_receipts(self):
        source = self.counterexample_source(symmetric=True)
        producer = self.show('producer')['cases'][0]
        target = {
            'A': {'subject': 'Equipment', 'meaning': 'Equipment for carrying cases.'},
            'B': {'subject': 'Portable equipment', 'meaning': 'Portable case equipment.'}}
        answer = json.loads(json.dumps(producer['parsed']))
        answer['answers'][1]['answer'] = 'TARGET CASE EXCLUDED'
        target_source = self.counterexample_source(symmetric=True, name='nodes',
            input_json=json.dumps(target), answer_override=answer)
        selected = source['saved_counterexamples'][0]
        selected['nodes_from'] = {
            'experiment': target_source['saved_counterexamples'][0]['experiment'],
            'case_id': 'pair'}
        source['saved_counterexamples'].append(dict(selected, id='reverse',
            field='justification', excerpt='A device with a red lamp.', reverse=True))
        self.write('checks.json', source)
        self.prepare('checks')
        cases = self.show('checks')['cases']
        self.assertEqual(json.loads(cases[0]['inputs']['INPUT_JSON']),
                         {**target, 'case': 'A device with a blue lamp.'})
        self.assertEqual(json.loads(cases[1]['inputs']['INPUT_JSON']), {
            'A': target['B'], 'B': target['A'], 'case': 'A device with a red lamp.'})
        target_case = self.show('nodes')['cases'][0]
        for case in cases:
            evidence = case['evidence']
            self.assertEqual(evidence['saved_counterexample']['receipt'], producer['receipt'])
            self.assertEqual(evidence['saved_counterexample']['original_input'],
                             json.loads(producer['inputs']['INPUT_JSON']))
            self.assertEqual(evidence['nodes_from']['receipt'], target_case['receipt'])
            self.assertEqual(evidence['nodes_from']['original_input'], target)
            for excluded in ('OLD LABEL', 'OLD VERDICT', 'TARGET CASE', 'nodes_from'):
                self.assertNotIn(excluded, case['prompt'])
        plan = json.loads((self.root / 'checks/experiment.json').read_text())['plan']
        for name in ('producer', 'nodes'):
            self.assertIn(str(self.root / name / 'experiment.json'), plan['sources'])
            self.assertIn(str(self.root / name / 'run/results.jsonl'), plan['sources'])
        for saved in (producer, target_case):
            self.assertIn(saved['receipt']['results_path'], plan['sources'])
            path = Path(saved['receipt']['results_path'])
            self.assertEqual(plan['sources'][str(path)],
                             hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(len(self.calls()), 2)

    def test_saved_counterexamples_nodes_from_rejects_invalid_selectors_and_sources(self):
        source = self.counterexample_source(symmetric=True)
        target = self.counterexample_source(symmetric=True, name='nodes')
        reference = {'experiment': target['saved_counterexamples'][0]['experiment'],
                     'case_id': 'pair'}
        invalid = [
            (None, 'nodes_from must be an object'),
            ({'experiment': reference['experiment']}, 'case_id'),
            ({**reference, 'reverse': True}, 'not supported'),
            ({**reference, 'case_id': 'missing'}, 'valid receipt-bound case'),
            ({**reference, 'experiment': {
                **reference['experiment'], 'sha256': '0' * 64}}, 'reference hash differs'),
        ]
        for index, (override, error) in enumerate(invalid):
            with self.subTest(index=index):
                source['saved_counterexamples'][0]['nodes_from'] = override
                self.write('checks.json', source)
                failure = self.cli('prepare', 'invalid-nodes-' + str(index),
                                   '--spec', self.spec, ok=False)
                self.assertIn(error, failure.stderr)
        unrun = self.counterexample_source(symmetric=True, name='unrun-nodes', run=False)
        source['saved_counterexamples'][0]['nodes_from'] = {
            'experiment': unrun['saved_counterexamples'][0]['experiment'], 'case_id': 'pair'}
        self.write('checks.json', source)
        failure = self.cli('prepare', 'unrun-nodes-check', '--spec', self.spec, ok=False)
        self.assertIn('valid receipt-bound case', failure.stderr)
        legacy = self.counterexample_source(name='legacy-source')
        legacy['saved_counterexamples'][0]['nodes_from'] = reference
        self.write('checks.json', legacy)
        failure = self.cli('prepare', 'legacy-nodes-check', '--spec', self.spec, ok=False)
        self.assertIn('requires a symmetric saved counterexample', failure.stderr)
        envelope = self.root / 'nodes/experiment.json'
        envelope.write_text(envelope.read_text() + '\n')
        source['saved_counterexamples'][0]['nodes_from'] = reference
        self.write('checks.json', source)
        failure = self.cli('prepare', 'changed-nodes-check', '--spec', self.spec, ok=False)
        self.assertIn('saved comparison reference hash differs', failure.stderr)

    def test_saved_counterexamples_nodes_from_rejects_mixed_or_malformed_targets(self):
        source = self.counterexample_source(symmetric=True)
        valid_answer = self.show('producer')['cases'][0]['parsed']
        a = {'subject': 'Devices', 'meaning': 'Devices with lamps.'}
        b = {'subject': 'Red devices', 'meaning': 'Devices with red lamps.'}
        mixed_answer = json.loads(json.dumps(valid_answer))
        mixed_answer['answers'][0]['question_id'] = 'local_contains_canonical'
        invalid = [
            ({'symmetric': False}, 'saved comparison input'),
            ({'input_json': json.dumps({'A': a, 'B': b, 'local': a})},
             'saved comparison input'),
            ({'input_json': json.dumps({'A': a})}, 'saved comparison input'),
            ({'input_json': json.dumps({'A': a, 'B': {**b, 'context': 'EXTRA'}})},
             'saved comparison B'),
            ({'input_json': json.dumps({'A': a, 'B': {**b, 'meaning': ' '}})},
             'nonempty text'),
            ({'input_json': json.dumps({'A': a, 'B': []})}, 'must be an object'),
            ({'input_json': '{"A":' + json.dumps(a) + ',"A":' + json.dumps(a)
                + ',"B":' + json.dumps(b) + '}'}, 'duplicate'),
            ({'answer_override': mixed_answer}, 'each containment direction'),
        ]
        for index, (options, error) in enumerate(invalid):
            with self.subTest(index=index):
                target = self.counterexample_source(name='bad-nodes-' + str(index),
                    **{'symmetric': True, **options})
                source['saved_counterexamples'][0]['nodes_from'] = {
                    'experiment': target['saved_counterexamples'][0]['experiment'],
                    'case_id': 'pair'}
                self.write('checks.json', source)
                destination = 'bad-nodes-check-' + str(index)
                failure = self.cli('prepare', destination, '--spec', self.spec, ok=False)
                self.assertIn(error, failure.stderr)
                self.assertFalse((self.root / destination).exists())

    def test_saved_symmetric_counterexamples_reject_malformed_inputs(self):
        a = {'subject': 'Devices', 'meaning': 'Devices with lamps.'}
        b = {'subject': 'Red devices', 'meaning': 'Devices with red lamps.'}
        malformed = [
            (json.dumps({'A': a, 'B': b, 'local': a}), 'direction does not match'),
            (json.dumps({'A': a}), 'direction does not match'),
            (json.dumps({'A': {**a, 'context': 'EXTRA'}, 'B': b}), 'fixed A'),
            (json.dumps({'A': a, 'B': {**b, 'meaning': ' '}}), 'nonempty text'),
            (json.dumps({'A': a, 'B': {**b, 'subject': None}}), 'fixed subject'),
            (json.dumps({'A': a, 'B': []}), 'fixed B'),
            ('{"A":' + json.dumps(a) + ',"A":' + json.dumps(a)
             + ',"B":' + json.dumps(b) + '}', 'duplicate'),
        ]
        for index, (raw, error) in enumerate(malformed):
            with self.subTest(index=index):
                self.counterexample_source(symmetric=True, name='producer-' + str(index),
                                           input_json=raw)
                destination = 'malformed-' + str(index)
                failure = self.cli('prepare', destination, '--spec', self.spec, ok=False)
                self.assertIn(error, failure.stderr)
                self.assertFalse((self.root / destination).exists())

    def test_saved_counterexamples_reject_mixed_directional_answers(self):
        self.counterexample_source(symmetric=True)
        valid = self.show('producer')['cases'][0]['parsed']
        invalid = []
        for field, identifier in (('questions', 'id'), ('answers', 'question_id')):
            changed = json.loads(json.dumps(valid))
            changed[field][0][identifier] = 'local_contains_canonical'
            invalid.append((changed, 'each containment direction'))
        changed = json.loads(json.dumps(valid))
        changed['relation'] = 'canonical_contains_local'
        invalid.append((changed, 'unknown hierarchy comparison relation'))
        for index, (answer, error) in enumerate(invalid):
            with self.subTest(index=index):
                self.counterexample_source(symmetric=True, name='mixed-' + str(index),
                                           answer_override=answer)
                destination = 'invalid-mixed-' + str(index)
                failure = self.cli('prepare', destination, '--spec', self.spec, ok=False)
                self.assertIn(error, failure.stderr)
                self.assertFalse((self.root / destination).exists())
        legacy = {'answers': [
            {'question_id': 'canonical_contains_local', 'answer': 'A blue-lamp device.',
             'justification': 'A blue-lamp device.'},
            {'question_id': 'A_contains_B', 'answer': 'A red-lamp device.',
             'justification': 'A red-lamp device.'}], 'relation': 'neither'}
        self.counterexample_source(name='mixed-legacy', answer_override=legacy)
        failure = self.cli('prepare', 'invalid-mixed-legacy', '--spec', self.spec, ok=False)
        self.assertIn('saved containment directions do not match input', failure.stderr)
        self.assertFalse((self.root / 'invalid-mixed-legacy').exists())
        legacy['answers'].pop()
        legacy['questions'] = [{'id': 'A_contains_B', 'question': 'An incompatible direction.'}]
        self.counterexample_source(name='mixed-legacy-question', answer_override=legacy)
        failure = self.cli('prepare', 'invalid-mixed-legacy-question',
                           '--spec', self.spec, ok=False)
        self.assertIn('saved containment directions do not match input', failure.stderr)
        self.assertFalse((self.root / 'invalid-mixed-legacy-question').exists())

    def test_saved_counterexamples_prepare_blind_cases_with_exact_receipts(self):
        source = self.counterexample_source()
        source['saved_counterexamples'].append(dict(source['saved_counterexamples'][0],
            id='red', field='justification', excerpt='A device with a red lamp.', reverse=True))
        self.write('checks.json', source)
        self.prepare('checks')
        cases = self.show('checks')['cases']
        blue, red = [json.loads(case['inputs']['INPUT_JSON']) for case in cases]
        self.assertEqual(blue, {'local': {'subject': 'Devices', 'meaning': 'Devices with lamps.'},
            'canonical': {'subject': 'Red devices', 'meaning': 'Devices with red lamps.'},
            'case': 'A device with a blue lamp.'})
        self.assertEqual(red, {'local': blue['canonical'], 'canonical': blue['local'],
                              'case': 'A device with a red lamp.'})
        for case in cases:
            for excluded in ('OLD TARGET', 'OLD LABEL', 'neither', 'justification'):
                self.assertNotIn(excluded, case['prompt'])
            self.assertEqual(case['evidence']['saved_counterexample']['receipt'],
                             self.show('producer')['cases'][0]['receipt'])
        plan = json.loads((self.root / 'checks/experiment.json').read_text())['plan']
        self.assertIn(str(self.root / 'producer/run/results.jsonl'), plan['sources'])
        self.assertFalse(plan['preparation']['application_allowed'])
        self.assertEqual(len(self.calls()), 1)
        self.cli('run', 'checks', env={'FAKE_RUNNER_PROMPT_RESPONSE':
            '{"local":{"verdict":"fits"},"canonical":{"verdict":"outside"}}'})
        self.assertEqual(self.show('checks')['summary']['valid'], 2)
        self.assertEqual(len(self.calls()), 3)

    def test_saved_counterexamples_refuse_invalid_selectors_and_unrun_answers(self):
        source = self.counterexample_source()
        for field, value, error in (
                ('case_id', 'missing', 'valid saved comparison'),
                ('direction', 'wrong', 'containment direction'),
                ('direction', ['A_contains_B'], 'containment direction'),
                ('field', 'relation', 'answer or justification'),
                ('excerpt', 'not in saved answer', 'exact unique excerpt'),
                ('reverse', 'yes', 'reverse must be boolean')):
            changed = json.loads(json.dumps(source))
            changed['saved_counterexamples'][0][field] = value
            self.write('checks.json', changed)
            result = self.cli('prepare', 'invalid-' + field, '--spec', self.spec, ok=False)
            self.assertIn(error, result.stderr)
            self.assertFalse((self.root / ('invalid-' + field)).exists())
        self.counterexample_source(run=False, name='unrun-producer')
        result = self.cli('prepare', 'unrun', '--spec', self.spec, ok=False)
        self.assertIn('valid saved comparison', result.stderr)

    def source(self):
        self.prompt.write_text('GENERIC PROMPT\n<input>\n{INPUT_JSON}\n</input>\n')
        self.write('notes.json', {'schema_version': 1, 'notes': [
            {'note_id': 'local-post', 'text': 'FULL LOCAL POST {INPUT_JSON}', 'subjects': [
                {'number': '1', 'subject': 'Food', 'context': 'Local root context'},
                {'number': '1.1', 'subject': 'Vegetables', 'context': 'Local entry context'},
                {'number': '1.1.1', 'subject': 'LOCAL DESCENDANT', 'context': 'Excluded'}]},
            {'note_id': 'canonical-post', 'text': 'CANONICAL POST EXCLUDED', 'subjects': [
                {'number': '1', 'subject': 'Preparation', 'context': 'Original ancestor'},
                {'number': '1.1', 'subject': 'Ingredients', 'context': 'Canonical support'}]}
        ]})
        reference = {'note_id': 'canonical-post', 'number': '1.1'}
        nodes = [
            {'id': identifier, 'subject': identifier, 'meaning': 'Fixed ' + identifier,
             'entries': [reference], 'parents': parents}
            for identifier, parents in [('C0', []), ('C1', ['C0']), ('C2', ['C0']),
                                        ('C3', ['C1', 'C2']), ('C4', ['C3'])]]
        source = {'schema_version': 1, 'corpus': 'notes.json',
                  'canonical_states': {'current': nodes}, 'pairs': [
            {'id': 'one', 'local': {'note_id': 'local-post', 'number': '1.1'},
             'canonical': {'state': 'current', 'id': 'C3'},
             'review': {'relation': 'canonical_contains_local', 'meaning': 'REVIEW ONLY'}}]}
        self.write('source.json', source)
        spec = json.loads(self.spec.read_text())
        spec['dataset'] = {'adapter': 'hierarchy_node_pairs', 'path': 'source.json'}
        schema = Path(__file__).with_name('shr_single_pair') / 'Hierarchy-compare-v4.output.schema.json'
        spec['runner']['output_schema'] = json.loads(schema.read_text())
        self.write('spec.json', spec)
        return source

    def local_source(self):
        source = self.source()
        local = {'schema_version': 1, 'corpus': source['corpus'], 'nodes': [
            {'id': 'one', 'local': source['pairs'][0]['local'],
             'review': {'meaning': 'REVIEW ONLY'}}]}
        self.write('source.json', local)
        spec = json.loads(self.spec.read_text())
        spec['dataset']['adapter'] = 'hierarchy_local_nodes'
        schema = Path(__file__).with_name('shr_single_pair') / 'Hierarchy-bootstrap-v1.output.schema.json'
        spec['runner']['output_schema'] = json.loads(schema.read_text())
        self.write('spec.json', spec)
        return local

    def test_local_source_requires_object_before_optional_field_access(self):
        self.local_source()
        for index, value in enumerate(([], None, 'not an object', 42)):
            with self.subTest(value=value):
                self.write('source.json', value)
                result = self.cli('prepare', f'bad-source-{index}', '--spec', self.spec, ok=False)
                self.assertIn('must be an object', result.stderr)
                self.assertNotIn('AttributeError', result.stderr)

    def saved_meaning_source(self, answer=None, run=True, name='bootstrap', schema_version=1):
        local = self.local_source()
        local['schema_version'] = schema_version
        self.write(name + '-source.json', local)
        spec = json.loads(self.spec.read_text())
        spec['dataset']['path'] = name + '-source.json'
        self.write(name + '-spec.json', spec)
        self.cli('prepare', name, '--spec', name + '-spec.json')
        if run:
            self.cli('run', name, env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(
                {'meaning': 'Vegetables intended to be cooked.'} if answer is None else answer)})
        source = self.source()
        source['pairs'][0]['local_meaning_from'] = {'experiment': name, 'case': 'one'}
        self.write('source.json', source)
        return source

    def saved_trial_source(self):
        saved_graph_fixture(self)
        source = {'schema_version': 2, 'corpus': 'notes.json',
                  'canonical_states': {'current': {'trial': 'trial/state.json'}},
                  'pairs': [{'id': 'one', 'local': {'note_id': 'n1', 'number': '1.1'},
                             'canonical': {'state': 'current', 'id': 'C002'}, 'review': {}},
                            {'id': 'two', 'local': {'note_id': 'n1', 'number': '1.1'},
                             'canonical': {'state': 'current', 'id': 'C001'}, 'review': {}}]}
        self.write('source.json', source)
        spec = json.loads((self.root / 'comparison.json').read_text())
        spec['dataset'] = {'adapter': 'hierarchy_node_pairs', 'path': 'source.json'}
        self.write('spec.json', spec)
        return source

    def test_saved_trial_state_supplies_exact_graph_without_mutation(self):
        self.saved_trial_source()
        state_path = self.root / 'trial/state.json'
        before = state_path.read_bytes()
        native_calls = len(self.calls())
        self.prepare()
        cases = self.show()['cases']
        food = json.loads(cases[0]['inputs']['INPUT_JSON'])['canonical']
        cooking = json.loads(cases[1]['inputs']['INPUT_JSON'])['canonical']
        self.assertEqual(food['meaning'], 'Fixed food meaning')
        self.assertEqual(food['parents'], ['C001'])
        self.assertEqual(food['ancestors'], [{'id': 'C001', 'subject': 'Cooking',
                         'meaning': 'Fixed cooking meaning', 'parents': []}])
        self.assertEqual(cooking['descendants'], [{'id': 'C002', 'subject': 'Food',
                         'meaning': 'Fixed food meaning', 'parents': ['C001']}])
        self.assertEqual(state_path.read_bytes(), before)
        plan = json.loads((self.root / 'E1/experiment.json').read_text())['plan']
        self.assertEqual(plan['sources'][str(state_path)], hashlib.sha256(before).hexdigest())
        self.assertNotIn('trial/state.json', cases[0]['prompt'])
        self.assertIn('canonical_trial', cases[0]['evidence'])
        self.assertEqual(len(self.calls()), native_calls)

    def test_saved_trial_reference_requires_same_corpus_and_unchanged_sources(self):
        source = self.saved_trial_source()
        self.write('other-notes.json', json.loads((self.root / 'notes.json').read_text()))
        source['corpus'] = 'other-notes.json'
        self.write('source.json', source)
        result = self.cli('prepare', 'wrong-corpus', '--spec', self.spec, ok=False)
        self.assertIn('corpus does not match', result.stderr)
        source['corpus'] = 'notes.json'
        self.write('source.json', source)
        path = self.root / 'notes.json'
        path.write_text(path.read_text() + '\n')
        result = self.cli('prepare', 'changed-source', '--spec', self.spec, ok=False)
        self.assertIn('trial source changed', result.stderr)
        self.assertFalse((self.root / 'wrong-corpus').exists())
        self.assertFalse((self.root / 'changed-source').exists())

    def test_saved_trial_reference_is_strict_and_requires_schema_two(self):
        source = self.saved_trial_source()
        for i, reference in enumerate(({}, {'trial': 'trial/state.json', 'extra': True},
                                       {'trial': None}, {'trial': 'absent.json'})):
            candidate = json.loads(json.dumps(source))
            candidate['canonical_states']['current'] = reference
            self.write('source.json', candidate)
            self.cli('prepare', f'invalid-trial-{i}', '--spec', self.spec, ok=False)
            self.assertFalse((self.root / f'invalid-trial-{i}').exists())
        source['schema_version'] = 1
        self.write('source.json', source)
        result = self.cli('prepare', 'schema-one', '--spec', self.spec, ok=False)
        self.assertIn('canonical state requires nodes', result.stderr)

    def test_saved_trial_state_is_read_once_for_multiple_references(self):
        from unittest.mock import patch
        source = self.saved_trial_source()
        source['canonical_states']['alias'] = {'trial': 'trial/state.json'}
        source['pairs'][1]['canonical']['state'] = 'alias'
        self.write('source.json', source)
        original = Path.read_bytes
        reads = []

        def tracked_read(path):
            reads.append(path)
            return original(path)

        spec = json.loads(self.spec.read_text())
        with patch.object(Path, 'read_bytes', tracked_read):
            cases, protected, _ = experiment_inputs.prepare_file(
                spec['dataset'], self.root / 'source.json', self.prompt.read_text())
        state_path = self.root / 'trial/state.json'
        self.assertEqual(reads.count(state_path), 1)
        self.assertEqual(len(cases), 2)
        self.assertIn(str(state_path), protected)

    def test_validated_saved_local_meaning_is_reused_as_input(self):
        self.saved_meaning_source()
        self.prepare()
        case = self.show()['cases'][0]
        payload = json.loads(case['inputs']['INPUT_JSON'])
        self.assertEqual(payload['local']['meaning'], 'Vegetables intended to be cooked.')
        self.assertEqual(len(self.calls()), 1)
        self.assertNotIn('bootstrap', case['prompt'])
        self.assertIn('local_meaning_from', case['evidence'])

    def test_tree_saved_meaning_is_bound_to_original_evidence_without_rewriting_compare_input(self):
        self.saved_meaning_source(schema_version=4)
        self.prepare()
        case = self.show()['cases'][0]
        local = json.loads(case['inputs']['INPUT_JSON'])['local']
        self.assertEqual(local['meaning'], 'Vegetables intended to be cooked.')
        self.assertEqual(local['entry']['subject'], 'Vegetables')
        self.assertEqual(local['entry']['ancestors'], [
            {'subject': 'Food', 'context': 'Local root context'}])
        self.assertEqual(set(local), {'entry', 'post', 'meaning'})
        self.assertIn('local_meaning_from', case['evidence'])
        plan = json.loads((self.root / 'E1/experiment.json').read_text())['plan']
        producer_plan = self.root / 'bootstrap/experiment.json'
        self.assertEqual(plan['sources'][str(producer_plan)],
                         hashlib.sha256(producer_plan.read_bytes()).hexdigest())
        self.assertEqual(len(self.calls()), 1)

    def test_tree_saved_meaning_rejects_changes_in_complete_root_tree_or_post(self):
        source = self.saved_meaning_source(schema_version=4)
        original = json.loads((self.root / 'notes.json').read_text())
        for index, field in enumerate(('selector', 'subject', 'context', 'ancestor',
                                       'descendant', 'post')):
            with self.subTest(field=field):
                changed = json.loads(json.dumps(original))
                candidate = json.loads(json.dumps(source))
                candidate['corpus'] = 'current-notes.json'
                if field == 'selector':
                    candidate['pairs'][0]['local']['number'] = '1'
                elif field in ('subject', 'context'):
                    changed['notes'][0]['subjects'][1][field] += ' changed'
                elif field == 'ancestor':
                    changed['notes'][0]['subjects'][0]['context'] += ' changed'
                elif field == 'descendant':
                    changed['notes'][0]['subjects'][2]['context'] += ' changed'
                else:
                    changed['notes'][0]['text'] += ' changed'
                self.write('current-notes.json', changed)
                self.write('source.json', candidate)
                result = self.cli('prepare', f'tree-mismatch-{index}', '--spec', self.spec, ok=False)
                self.assertIn('does not match original local input', result.stderr)
                self.assertFalse((self.root / f'tree-mismatch-{index}').exists())

    def test_saved_meaning_provenance_protects_sources_and_exact_answers_reuse(self):
        self.saved_meaning_source()
        self.prepare()
        plan = json.loads((self.root / 'E1/experiment.json').read_text())['plan']
        bootstrap = json.loads((self.root / 'bootstrap/experiment.json').read_text())['plan']
        protected = [self.root / 'bootstrap/experiment.json',
                     self.root / 'bootstrap/runner-config.json',
                     Path(bootstrap['run_directory']) / 'manifest.json',
                     Path(bootstrap['run_directory']) / 'results.jsonl',
                     self.root / 'bootstrap-source.json', self.root / 'notes.json']
        for path in protected:
            self.assertEqual(plan['sources'][str(path)], hashlib.sha256(path.read_bytes()).hexdigest())
        value = {'meaning': 'Vegetables intended to be cooked.', 'relation': 'neither',
                 'reason': 'Separate fixture topic'}
        self.cli('run', 'E1', env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(value)})
        self.prepare('E2')
        self.cli('run', 'E2')
        report = json.loads(self.cli('show', 'E2', '--json').stdout)
        self.assertTrue(report['cases'][0]['reused'])
        self.assertEqual(len(self.calls()), 2)

    def test_saved_meaning_reference_requires_valid_nonnull_bootstrap_answer(self):
        for index, (answer, run) in enumerate((({'meaning': None}, True),
                                              ({'meaning': 'Missing saved answer'}, False))):
            self.saved_meaning_source(answer=answer, run=run, name=f'bootstrap-{index}')
            result = self.cli('prepare', f'invalid-answer-{index}', '--spec', self.spec, ok=False)
            self.assertIn('meaning', result.stderr)
            self.assertFalse((self.root / f'invalid-answer-{index}').exists())

    def test_malformed_saved_answer_is_rejected(self):
        self.saved_meaning_source(run=False)
        self.cli('run', 'bootstrap', env={'FAKE_RUNNER_PROMPT_RESPONSE': '{"meaning": 42}'}, ok=False)
        result = self.cli('prepare', 'invalid', '--spec', self.spec, ok=False)
        self.assertIn('valid saved meaning', result.stderr)
        self.assertFalse((self.root / 'invalid').exists())

    def test_saved_meaning_reference_rejects_wrong_adapter(self):
        source = self.source()
        self.write('comparison-source.json', source)
        spec = json.loads(self.spec.read_text())
        spec['dataset']['path'] = 'comparison-source.json'
        self.write('comparison-spec.json', spec)
        self.cli('prepare', 'comparison', '--spec', 'comparison-spec.json')
        self.cli('run', 'comparison', env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps({
            'meaning': 'Local meaning', 'relation': 'neither', 'reason': 'Fixture'})})
        source['pairs'][0]['local_meaning_from'] = {'experiment': 'comparison', 'case': 'one'}
        self.write('source.json', source)
        result = self.cli('prepare', 'invalid', '--spec', self.spec, ok=False)
        self.assertIn('hierarchy_local_nodes experiment', result.stderr)

    def test_saved_meaning_requires_same_selector_and_every_local_evidence_field(self):
        source = self.saved_meaning_source()
        original = json.loads((self.root / 'notes.json').read_text())
        for index, field in enumerate(('selector', 'subject', 'context', 'ancestor', 'post')):
            with self.subTest(field=field):
                changed = json.loads(json.dumps(original))
                candidate = json.loads(json.dumps(source))
                candidate['corpus'] = 'current-notes.json'
                if field == 'selector':
                    candidate['pairs'][0]['local']['number'] = '1'
                elif field in ('subject', 'context'):
                    changed['notes'][0]['subjects'][1][field] += ' changed'
                elif field == 'ancestor':
                    changed['notes'][0]['subjects'][0]['context'] += ' changed'
                else:
                    changed['notes'][0]['text'] += ' changed'
                self.write('current-notes.json', changed)
                self.write('source.json', candidate)
                result = self.cli('prepare', f'mismatch-{index}', '--spec', self.spec, ok=False)
                self.assertIn('does not match original local input', result.stderr)
                self.assertFalse((self.root / f'mismatch-{index}').exists())

    def test_literal_and_saved_meaning_are_mutually_exclusive_and_reference_is_strict(self):
        source = self.saved_meaning_source()
        for index, reference in enumerate(({'experiment': 'bootstrap'},
                                           {'experiment': 'bootstrap', 'case': 'absent'},
                                           {'experiment': 'bootstrap', 'case': 'one', 'extra': True},
                                           None)):
            candidate = json.loads(json.dumps(source))
            candidate['pairs'][0]['local_meaning_from'] = reference
            self.write('source.json', candidate)
            self.cli('prepare', f'bad-reference-{index}', '--spec', self.spec, ok=False)
        source['pairs'][0]['local_meaning'] = 'Literal'
        self.write('source.json', source)
        result = self.cli('prepare', 'both', '--spec', self.spec, ok=False)
        self.assertIn('mutually exclusive', result.stderr)

    def test_changed_saved_receipt_is_rejected_before_preparation(self):
        self.saved_meaning_source()
        path = self.root / 'bootstrap/run/results.jsonl'
        record = json.loads(path.read_text())
        record['final_output_raw'] = '{"meaning": "Forged meaning"}'
        path.write_text(json.dumps(record) + '\n')
        self.cli('prepare', 'forged', '--spec', self.spec, ok=False)
        self.assertFalse((self.root / 'forged').exists())

    def test_one_saved_report_is_loaded_once_for_repeated_pairs(self):
        from unittest.mock import Mock
        from sse_multivector import experiment as workflow
        source = self.saved_meaning_source()
        source['pairs'] = [dict(source['pairs'][0], id=f'pair-{i}') for i in range(9)]
        self.write('source.json', source)
        spec = json.loads(self.spec.read_text())
        loader = Mock(wraps=workflow.report)
        cases, protected, _ = experiment_inputs.prepare_file(
            spec['dataset'], self.root / 'source.json', self.prompt.read_text(), loader)
        self.assertEqual(loader.call_count, 1)
        self.assertEqual(len(cases), 9)
        self.assertEqual(len({case['inputs']['INPUT_JSON'] for case in cases}), 1)
        self.assertIn(str(self.root / 'bootstrap/experiment.json'), protected)

    def test_fixed_local_meaning_is_explicit_input_not_review_leakage(self):
        source = self.source()
        source['pairs'][0]['local_meaning'] = 'Vegetables intended to be cooked.'
        self.write('source.json', source)
        self.prepare()
        case = self.show()['cases'][0]
        payload = json.loads(case['inputs']['INPUT_JSON'])
        self.assertEqual(payload['local']['meaning'], 'Vegetables intended to be cooked.')
        self.assertEqual(payload['local']['entry']['subject'], 'Vegetables')
        self.assertEqual(payload['local']['post'], 'FULL LOCAL POST {INPUT_JSON}')
        self.assertNotIn('REVIEW ONLY', case['prompt'])
        for index, bad in enumerate(('', '  ', None, 42)):
            source['pairs'][0]['local_meaning'] = bad
            self.write('source.json', source)
            result = self.cli('prepare', f'bad-meaning-{index}', '--spec', self.spec, ok=False)
            self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.calls(), [])

    def test_local_only_preparation_and_execution(self):
        self.local_source()
        self.prepare()
        case = self.show()['cases'][0]
        payload = json.loads(case['inputs']['INPUT_JSON'])
        self.assertEqual(set(payload), {'local'})
        self.assertEqual(payload['local']['entry']['ancestors'],
                         [{'subject': 'Food', 'context': 'Local root context'}])
        self.assertEqual(payload['local']['post'], 'FULL LOCAL POST {INPUT_JSON}')
        for excluded in ('REVIEW ONLY', 'CANONICAL POST EXCLUDED', 'LOCAL DESCENDANT'):
            self.assertNotIn(excluded, case['prompt'])
        self.assertEqual(case['evidence']['review'], {'meaning': 'REVIEW ONLY'})
        plan = json.loads((self.root / 'E1/experiment.json').read_text())['plan']
        path = self.root / 'notes.json'
        self.assertEqual(plan['sources'][str(path)], hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(self.calls(), [])
        value = {'meaning': 'A local definition'}
        self.cli('run', 'E1', env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(value)})
        self.assertEqual(self.show()['cases'][0]['parsed'], value)
        for value in ({'meaning': None}, {'meaning': 'A definition'}):
            self.assertEqual(experiment_inputs.validate({'adapter': 'hierarchy_local_nodes'},
                             case, json.dumps(value), None)['parsed'], value)
        for bad in ({'meaning': ''}, {'meaning': 42}, {'meaning': 'X', 'relation': 'neither'}):
            with self.assertRaises(ValueError):
                experiment_inputs.validate({'adapter': 'hierarchy_local_nodes'}, case,
                                           json.dumps(bad), None)

    def test_bootstrap_diagnostic_output_uses_native_post_bound_validation(self):
        self.local_source()
        spec = json.loads(self.spec.read_text())
        schema = Path(__file__).with_name('shr_single_pair') / 'Hierarchy-bootstrap-v71.output.schema.json'
        spec['runner']['output_schema'] = json.loads(schema.read_text())
        self.write('spec.json', spec)
        self.prepare()
        answer = {'meaning': 'A local definition', 'evidence': [
            {'quote': 'FULL LOCAL POST', 'supports': 'The selected scope', 'inference': None}]}
        self.cli('run', 'E1', env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(answer)})
        case = self.show()['cases'][0]
        self.assertEqual(case['parsed'], answer)
        for value in ({'meaning': None, 'evidence': []},
                      {'meaning': None, 'evidence': answer['evidence']}):
            self.assertEqual(experiment_inputs.validate({'adapter': 'hierarchy_local_nodes'},
                             case, json.dumps(value), spec['runner']['output_schema'])['parsed'], value)

    def test_local_hierarchy_contains_only_selected_root_and_marks_selected_entry(self):
        source = self.local_source()
        source['include_hierarchy'] = True
        self.write('source.json', source)
        corpus = json.loads((self.root / 'notes.json').read_text())
        corpus['notes'][0]['subjects'].extend([
            {'number': '10', 'subject': 'Unrelated root', 'context': 'Excluded root'},
            {'number': '1.10', 'subject': 'Later sibling', 'context': 'Later context'},
            {'number': '1.2', 'subject': 'Earlier sibling', 'context': 'Earlier context'}])
        self.write('notes.json', corpus)
        before = (self.root / 'notes.json').read_bytes()
        self.prepare()
        case = self.show()['cases'][0]
        local = json.loads(case['inputs']['INPUT_JSON'])['local']
        self.assertEqual(local['hierarchy']['selected'], '1.1')
        self.assertEqual([row['number'] for row in local['hierarchy']['entries']],
                         ['1', '1.1', '1.1.1', '1.2', '1.10'])
        selected = local['hierarchy']['entries'][1]
        self.assertEqual({k: selected[k] for k in ('subject', 'context')},
                         {k: local['entry'][k] for k in ('subject', 'context')})
        self.assertEqual(set(selected), {'number', 'subject', 'context'})
        self.assertIn('LOCAL DESCENDANT', case['prompt'])
        for excluded in ('Unrelated root', 'REVIEW ONLY', 'CANONICAL POST EXCLUDED'):
            self.assertNotIn(excluded, case['prompt'])
        self.assertEqual((self.root / 'notes.json').read_bytes(), before)
        source['nodes'][0]['subject_override'] = 'Changed selected subject'
        self.write('source.json', source)
        self.prepare('override')
        changed = json.loads(self.show('override')['cases'][0]['inputs']['INPUT_JSON'])['local']
        self.assertEqual(changed['hierarchy']['entries'][1]['subject'], 'Changed selected subject')
        self.assertEqual(changed['entry']['subject'], 'Changed selected subject')

    def test_local_hierarchy_rejects_bad_option_and_missing_selected_root_parents(self):
        source = self.local_source()
        for index, value in enumerate(('true', None, 1)):
            self.write('source.json', {**source, 'include_hierarchy': value})
            result = self.cli('prepare', f'bad-option-{index}', '--spec', self.spec, ok=False)
            self.assertIn('include_hierarchy must be boolean', result.stderr)
        corpus = json.loads((self.root / 'notes.json').read_text())
        corpus['notes'][0]['subjects'].append(
            {'number': '1.2.1', 'subject': 'Orphan', 'context': 'Missing immediate parent'})
        self.write('notes.json', corpus)
        self.write('source.json', {**source, 'include_hierarchy': True})
        result = self.cli('prepare', 'bad-parent', '--spec', self.spec, ok=False)
        self.assertIn('missing original local hierarchy parent', result.stderr)
        self.write('source.json', {**source, 'include_hierarchy': False})
        self.prepare('legacy')
        self.assertNotIn('hierarchy', json.loads(self.show('legacy')['cases'][0]['inputs']['INPUT_JSON'])['local'])

    def test_local_hierarchy_schema_three_omits_duplicate_ancestors_and_preserves_legacy_tree(self):
        source = self.local_source()
        source['schema_version'] = 3
        self.write('source.json', source)
        self.prepare()
        current = json.loads(self.show()['cases'][0]['inputs']['INPUT_JSON'])['local']
        self.assertEqual(set(current['entry']), {'subject', 'context'})
        self.assertEqual(current['hierarchy']['selected'], '1.1')
        self.assertEqual(current['hierarchy']['entries'][0],
                         {'number': '1', 'subject': 'Food', 'context': 'Local root context'})
        self.write('tree-source.json', source)
        self.write('source.json', {'schema_version': 2,
            'sources': [{'path': 'tree-source.json'}], 'review': {}})
        self.prepare('collection')
        collected = json.loads(self.show('collection')['cases'][0]['inputs']['INPUT_JSON'])['local']
        self.assertEqual(collected, current)
        self.write('source.json', {**source, 'schema_version': 1, 'include_hierarchy': True})
        self.prepare('legacy-tree')
        old = json.loads(self.show('legacy-tree')['cases'][0]['inputs']['INPUT_JSON'])['local']
        self.assertEqual(old['entry']['ancestors'],
                         [{'subject': 'Food', 'context': 'Local root context'}])
        self.assertEqual(old['hierarchy'], current['hierarchy'])
        self.assertEqual(old['post'], current['post'])

    def test_schema4_local_input_uses_only_post_and_selected_root_tree(self):
        source = self.local_source()
        source['schema_version'] = 4
        self.write('source.json', source)
        self.prepare()
        current = json.loads(self.show()['cases'][0]['inputs']['INPUT_JSON'])['local']
        self.assertEqual(set(current), {'post', 'hierarchy'})
        self.assertEqual(current['post'], 'FULL LOCAL POST {INPUT_JSON}')
        self.assertEqual(current['hierarchy'], {
            'selected': '1.1', 'entries': [
                {'number': '1', 'subject': 'Food', 'context': 'Local root context'},
                {'number': '1.1', 'subject': 'Vegetables', 'context': 'Local entry context'},
                {'number': '1.1.1', 'subject': 'LOCAL DESCENDANT', 'context': 'Excluded'}]})
        self.assertEqual(self.show()['cases'][0]['evidence']['version'],
                         'hierarchy-local-nodes-v4')
        self.write('tree-source.json', source)
        self.write('source.json', {'schema_version': 2,
            'sources': [{'path': 'tree-source.json'}], 'review': {}})
        self.prepare('collection')
        collected = json.loads(self.show('collection')['cases'][0]['inputs']['INPUT_JSON'])['local']
        self.assertEqual(collected, current)

    def test_bootstrap_title_uses_native_validation(self):
        self.local_source()
        spec = json.loads(self.spec.read_text())
        prompts = Path(__file__).with_name('shr_single_pair')
        identifier = 'Hierarchy-bootstrap-v130'
        spec['runner']['output_schema'] = json.loads(
            (prompts / (identifier + '.output.schema.json')).read_text())
        self.write('spec.json', spec)
        self.prepare()
        value = {'ambiguities': [], 'resolutions': [], 'meaning': 'Selected scope',
                 'title': 'Selected scope', 'evidence': [
                     {'quote': 'FULL LOCAL POST', 'supports': 'Selected scope', 'inference': None}]}
        case = self.show()['cases'][0]
        self.assertEqual(experiment_inputs.validate({'adapter': 'hierarchy_local_nodes'}, case,
                         json.dumps(value), spec['runner']['output_schema'])['parsed'], value)
        self.cli('run', 'E1', env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(value)})
        case = self.show()['cases'][0]
        self.assertEqual(case['status'], 'valid')
        self.assertEqual(case['parsed'], value)
        spec['prompt'] = {'id': identifier, 'path': str(prompts / (identifier + '.md'))}
        self.write('spec.json', spec)
        self.prepare('titled')
        sources = json.loads((self.root / 'titled/experiment.json').read_text())['plan']['sources']
        wrapper = prompts / 'prompt_sources/Hierarchy-bootstrap-v130.after.md'
        self.assertEqual(sources[str(wrapper)], hashlib.sha256(wrapper.read_bytes()).hexdigest())
        schema = spec['runner']['output_schema']
        unresolved = {**value, 'meaning': None, 'title': None}
        self.assertEqual(experiment_inputs.validate({'adapter': 'hierarchy_local_nodes'}, case,
                         json.dumps(unresolved), schema)['parsed'], unresolved)
        for title in ('', ' ', 42, [], {}):
            with self.subTest(title=title), self.assertRaisesRegex(ValueError, 'title must be nonempty'):
                experiment_inputs.validate({'adapter': 'hierarchy_local_nodes'}, case,
                                           json.dumps({**value, 'title': title}), schema)
        for invalid in ({**value, 'title': None}, {**value, 'meaning': None}):
            with self.subTest(answer=invalid), self.assertRaisesRegex(ValueError, 'title must be null'):
                experiment_inputs.validate({'adapter': 'hierarchy_local_nodes'}, case,
                                           json.dumps(invalid), schema)
        with self.assertRaises(ValueError):
            experiment_inputs.validate({'adapter': 'hierarchy_local_nodes'}, case,
                                       json.dumps({k: v for k, v in value.items() if k != 'title'}), schema)
        historical = json.loads((prompts / 'Hierarchy-bootstrap-v79.output.schema.json').read_text())
        with self.assertRaises(ValueError):
            experiment_inputs.validate({'adapter': 'hierarchy_local_nodes'}, case,
                                       json.dumps(value), historical)

    def test_bootstrap_ambiguity_diagnostics_use_native_validation(self):
        self.local_source()
        spec = json.loads(self.spec.read_text())
        schema = Path(__file__).with_name('shr_single_pair') / 'Hierarchy-bootstrap-v79.output.schema.json'
        spec['runner']['output_schema'] = json.loads(schema.read_text())
        self.write('spec.json', spec)
        self.prepare()
        value = {'ambiguities': [{'id': 'a1', 'question': 'Which scope?'}],
                 'resolutions': [{'ambiguity_id': 'a1', 'answer': 'Selected scope',
                                  'justification': 'Supported interpretation'}],
                 'meaning': 'Selected scope', 'evidence': [
                     {'quote': 'FULL LOCAL POST', 'supports': 'Selected scope', 'inference': None}]}
        self.cli('run', 'E1', env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(value)})
        self.assertEqual(self.show()['cases'][0]['status'], 'valid')
        self.assertEqual(self.show()['cases'][0]['parsed'], value)
        case = self.show()['cases'][0]
        value['resolutions'][0]['answer'] = None
        value['meaning'] = None
        parsed = experiment_inputs.validate({'adapter': 'hierarchy_local_nodes'}, case,
            json.dumps(value), spec['runner']['output_schema'])['parsed']
        self.assertEqual(parsed, value)

    def test_bootstrap_ambiguity_diagnostics_reject_invalid_links_and_quotes(self):
        self.local_source()
        self.prepare()
        case = self.show()['cases'][0]
        schema = json.loads((Path(__file__).with_name('shr_single_pair') /
                             'Hierarchy-bootstrap-v79.output.schema.json').read_text())
        question = {'id': 'a1', 'question': 'Which scope?'}
        resolution = {'ambiguity_id': 'a1', 'answer': 'Selected scope',
                      'justification': 'Supported interpretation'}
        value = {'ambiguities': [question], 'resolutions': [resolution],
                 'meaning': 'Selected scope', 'evidence': [
                     {'quote': 'FULL LOCAL POST', 'supports': 'Selected scope', 'inference': None}]}
        for bad in (
                {**value, 'ambiguities': [question, question]},
                {**value, 'ambiguities': 'not an array'},
                {**value, 'ambiguities': [{**question, 'id': ' '}]},
                {**value, 'ambiguities': [{**question, 'question': ''}]},
                {**value, 'ambiguities': [{**question, 'extra': 'rejected'}]},
                {**value, 'resolutions': []},
                {**value, 'resolutions': [resolution, resolution]},
                {**value, 'resolutions': 'not an array'},
                {**value, 'resolutions': [{**resolution, 'ambiguity_id': 'unknown'}]},
                {**value, 'resolutions': [{**resolution, 'answer': None}]},
                {**value, 'resolutions': [{**resolution, 'answer': ' '}]},
                {**value, 'resolutions': [{**resolution, 'justification': ''}]},
                {**value, 'resolutions': [{**resolution, 'extra': 'rejected'}]},
                {**value, 'evidence': [{**value['evidence'][0], 'quote': 'Local entry context'}]},
                {key: item for key, item in value.items() if key != 'ambiguities'}):
            with self.subTest(answer=bad), self.assertRaises(ValueError):
                experiment_inputs.validate({'adapter': 'hierarchy_local_nodes'}, case,
                                           json.dumps(bad), schema)
        empty = {**value, 'ambiguities': [], 'resolutions': []}
        self.assertEqual(experiment_inputs.validate({'adapter': 'hierarchy_local_nodes'}, case,
                         json.dumps(empty), schema)['parsed'], empty)
        legacy_schema = json.loads((Path(__file__).with_name('shr_single_pair') /
                                    'Hierarchy-bootstrap-v71.output.schema.json').read_text())
        with self.assertRaises(ValueError):
            experiment_inputs.validate({'adapter': 'hierarchy_local_nodes'}, case,
                                       json.dumps(value), legacy_schema)

    def test_local_collection_preserves_hierarchy_from_sources_and_saved_experiments(self):
        source = self.local_source()
        source['include_hierarchy'] = True
        self.write('tree-source.json', source)
        spec = json.loads(self.spec.read_text())
        spec['dataset']['path'] = 'tree-source.json'
        self.write('tree-spec.json', spec)
        self.cli('prepare', 'tree', '--spec', 'tree-spec.json')
        self.cli('run', 'tree', env={'FAKE_RUNNER_PROMPT_RESPONSE': '{"meaning":"A definition"}'})
        self.write('source.json', {'schema_version': 2,
            'sources': [{'path': 'tree-source.json'}],
            'experiments': [{'path': 'tree', 'select': ['one']}], 'review': {}})
        self.prepare()
        collected = self.show()['cases']
        self.assertEqual(len(collected), 1)
        original = json.loads(self.show('tree')['cases'][0]['inputs']['INPUT_JSON'])
        self.assertEqual(json.loads(collected[0]['inputs']['INPUT_JSON']), original)
        self.assertEqual(len(collected[0]['evidence']['review']['historical_witnesses']), 2)

    def test_bootstrap_diagnostics_reject_inexact_quotes_and_invalid_records(self):
        self.local_source()
        self.prepare()
        case = self.show()['cases'][0]
        record = {'quote': 'FULL LOCAL POST', 'supports': 'Selected scope', 'inference': None}
        schema = json.loads((Path(__file__).with_name('shr_single_pair') /
                             'Hierarchy-bootstrap-v71.output.schema.json').read_text())
        for bad in (
                {'meaning': 'X', 'evidence': []},
                {'meaning': 'X', 'evidence': 'not an array'},
                {'meaning': 'X', 'evidence': [{**record, 'quote': 'Local entry context'}]},
                {'meaning': 'X', 'evidence': [{**record, 'quote': 'FULL … POST'}]},
                {'meaning': 'X', 'evidence': [{**record, 'quote': ''}]},
                {'meaning': 'X', 'evidence': [{**record, 'supports': ' '}]},
                {'meaning': 'X', 'evidence': [{**record, 'inference': False}]},
                {'meaning': 'X', 'evidence': [{**record, 'inference': ''}]},
                {'meaning': 'X', 'evidence': [{'quote': 'FULL LOCAL POST'}]},
                {'meaning': 'X', 'evidence': [{**record, 'extra': 'rejected'}]}):
            with self.subTest(answer=bad), self.assertRaises(ValueError):
                experiment_inputs.validate({'adapter': 'hierarchy_local_nodes'}, case,
                                           json.dumps(bad), schema)

    def test_legacy_bootstrap_schema_stays_strict_and_diagnostic_schema_requires_evidence(self):
        self.local_source()
        self.prepare()
        case = self.show()['cases'][0]
        legacy = json.loads(self.spec.read_text())['runner']['output_schema']
        diagnostic = json.loads((Path(__file__).with_name('shr_single_pair') /
                                 'Hierarchy-bootstrap-v71.output.schema.json').read_text())
        answer = {'meaning': 'X', 'evidence': [
            {'quote': 'FULL LOCAL POST', 'supports': 'Scope', 'inference': None}]}
        with self.assertRaises(ValueError):
            experiment_inputs.validate({'adapter': 'hierarchy_local_nodes'}, case,
                                       json.dumps(answer), legacy)
        with self.assertRaises(ValueError):
            experiment_inputs.validate({'adapter': 'hierarchy_local_nodes'}, case,
                                       '{"meaning":"X"}', diagnostic)

    def test_local_collection_deduplicates_inputs_and_preserves_historical_reviews(self):
        original = self.local_source()
        self.write('first.json', original)
        second = json.loads(json.dumps(original))
        second['nodes'][0]['id'] = 'different-id'
        second['nodes'][0]['review'] = {'expected': {'meaning': 'HISTORICAL TARGET'}}
        overridden = {**second['nodes'][0], 'id': 'override',
                      'subject_override': 'Cooking vegetables'}
        second['nodes'].append(overridden)
        self.write('second.json', second)
        self.write('source.json', {'schema_version': 2, 'sources': [
            {'path': 'first.json'}, {'path': 'second.json'}],
            'review': {'criteria': ['POST GROUNDING CRITERION']}})
        self.prepare()
        cases = self.show()['cases']
        self.assertEqual(len(cases), 2)
        base = next(case for case in cases if json.loads(case['inputs']['INPUT_JSON'])
                    ['local']['entry']['subject'] == 'Vegetables')
        witnesses = base['evidence']['review']['historical_witnesses']
        self.assertEqual([w['case'] for w in witnesses], ['one', 'different-id'])
        self.assertEqual(witnesses[1]['evidence']['review'], second['nodes'][0]['review'])
        self.assertNotIn('expected', base['evidence']['review'])
        for case in cases:
            for text in ('REVIEW ONLY', 'HISTORICAL TARGET', 'POST GROUNDING CRITERION'):
                self.assertNotIn(text, case['prompt'])
        plan = json.loads((self.root / 'E1/experiment.json').read_text())['plan']
        for name in ('source.json', 'first.json', 'second.json', 'notes.json'):
            path = self.root / name
            self.assertEqual(plan['sources'][str(path)],
                             hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(self.calls(), [])

    def test_local_collection_uses_exact_post_context_and_ancestor_inputs(self):
        original = self.local_source()
        self.write('first.json', original)
        changed = json.loads((self.root / 'notes.json').read_text())
        changed['notes'][0]['subjects'][0]['context'] = 'Different ancestor context'
        self.write('changed-notes.json', changed)
        self.write('second.json', {**original, 'corpus': 'changed-notes.json'})
        self.write('source.json', {'schema_version': 2, 'sources': [
            {'path': 'first.json'}, {'path': 'second.json'}], 'review': {}})
        self.prepare()
        cases = self.show()['cases']
        self.assertEqual(len(cases), 2)
        self.assertNotEqual(cases[0]['id'], cases[1]['id'])
        spec = json.loads(self.spec.read_text())
        spec['dataset']['select'] = [cases[1]['id']]
        self.write('spec.json', spec)
        self.prepare('screen')
        self.assertEqual([row['id'] for row in self.show('screen')['cases']], [cases[1]['id']])
        self.assertEqual(self.calls(), [])

    def test_local_collection_subjects_only_drops_only_context(self):
        local = self.local_source()
        local['schema_version'] = 4
        self.write('original-local.json', local)
        collection = {'schema_version': 2, 'local_schema_version': 4,
                      'sources': [{'path': 'original-local.json'}], 'review': {}}
        self.write('source.json', collection)
        self.prepare('contextual')
        original = self.show('contextual')['cases'][0]
        self.assertEqual(json.loads(original['inputs']['INPUT_JSON']), {
            'local': {'post': 'FULL LOCAL POST {INPUT_JSON}', 'hierarchy': {
                'selected': '1.1', 'entries': [
                    {'number': '1', 'subject': 'Food', 'context': 'Local root context'},
                    {'number': '1.1', 'subject': 'Vegetables', 'context': 'Local entry context'},
                    {'number': '1.1.1', 'subject': 'LOCAL DESCENDANT', 'context': 'Excluded'}]}}})
        self.assertNotIn('input_view', original['evidence'])
        collection['input_view'] = 'subjects_only'
        self.write('source.json', collection)
        self.prepare('subjects-only')
        projected = self.show('subjects-only')['cases'][0]
        original_input = json.loads(original['inputs']['INPUT_JSON'])
        expected = json.loads(original['inputs']['INPUT_JSON'])
        for entry in expected['local']['hierarchy']['entries']:
            del entry['context']
        self.assertEqual(json.loads(projected['inputs']['INPUT_JSON']), expected)
        self.assertEqual(projected['id'], original['id'])
        self.assertNotEqual(projected['input_sha256'], original['input_sha256'])
        evidence = projected['evidence']
        self.assertEqual(evidence['input_view'], 'subjects_only')
        self.assertEqual(evidence['original_input'], original_input)
        self.assertEqual(evidence['original_input_sha256'], experiment_inputs.digest(original_input))
        self.assertEqual(evidence['local_input_sha256'], experiment_inputs.digest(expected))
        self.assertNotIn('Local entry context', projected['prompt'])
        plan = json.loads((self.root / 'subjects-only/experiment.json').read_text())['plan']
        self.assertEqual(plan['preparation']['input_view'], 'subjects_only')
        self.assertIn(str(self.root / 'notes.json'), plan['sources'])
        self.assertEqual(self.calls(), [])

    def test_local_collection_subjects_only_preserves_distinct_original_identities(self):
        local = self.local_source()
        local['schema_version'] = 4
        self.write('original-local.json', local)
        changed = json.loads(json.dumps(local))
        changed['nodes'][0]['context_overrides'] = {'1.1': 'Different original interpretation'}
        self.write('changed-local.json', changed)
        collection = {'schema_version': 2, 'local_schema_version': 4,
                      'sources': [{'path': 'original-local.json'}, {'path': 'changed-local.json'}],
                      'review': {}}
        self.write('source.json', collection)
        self.prepare('contextual')
        originals = self.show('contextual')['cases']
        collection['input_view'] = 'subjects_only'
        self.write('source.json', collection)
        self.prepare('subjects-only')
        projected = self.show('subjects-only')['cases']
        self.assertEqual([case['id'] for case in projected], [case['id'] for case in originals])
        self.assertEqual(len(projected), 2)
        self.assertEqual(projected[0]['inputs'], projected[1]['inputs'])
        self.assertNotEqual(projected[0]['evidence']['original_input'],
                            projected[1]['evidence']['original_input'])
        self.assertEqual(self.calls(), [])

    def test_local_collection_subjects_only_rejects_unsupported_views_and_schemas(self):
        local = self.local_source()
        local['schema_version'] = 4
        self.write('original-local.json', local)
        collection = {'schema_version': 2, 'local_schema_version': 4,
                      'sources': [{'path': 'original-local.json'}], 'review': {},
                      'input_view': 'subjects_only'}
        for index, value in enumerate((None, '', 'contexts_only', [], 4)):
            with self.subTest(view=value):
                self.write('source.json', {**collection, 'input_view': value})
                result = self.cli('prepare', f'bad-view-{index}', '--spec', self.spec, ok=False)
                self.assertIn('input_view must be subjects_only', result.stderr)
        legacy = {key: value for key, value in collection.items() if key != 'local_schema_version'}
        self.write('source.json', legacy)
        result = self.cli('prepare', 'legacy-collection', '--spec', self.spec, ok=False)
        self.assertIn('subjects_only requires collection local_schema_version 4', result.stderr)
        self.write('source.json', {**collection, 'local_schema_version': 3})
        result = self.cli('prepare', 'bad-schema', '--spec', self.spec, ok=False)
        self.assertIn('local_schema_version must be 4', result.stderr)
        self.write('source.json', {**local, 'input_view': 'subjects_only'})
        result = self.cli('prepare', 'standalone-view', '--spec', self.spec, ok=False)
        self.assertIn('local node source.input_view', result.stderr)
        self.assertEqual(self.calls(), [])

    def test_local_collection_subjects_only_does_not_bypass_saved_source_validation(self):
        self.saved_meaning_source(run=False, schema_version=4)
        self.write('source.json', {'schema_version': 2, 'local_schema_version': 4,
            'sources': [{'path': 'bootstrap-source.json'}],
            'experiments': [{'path': 'bootstrap'}], 'review': {}, 'input_view': 'subjects_only'})
        spec = json.loads(self.spec.read_text())
        spec['dataset']['adapter'] = 'hierarchy_local_nodes'
        self.write('spec.json', spec)
        corpus = json.loads((self.root / 'notes.json').read_text())
        corpus['notes'][0]['subjects'][1]['context'] = 'Tampered source context'
        self.write('notes.json', corpus)
        result = self.cli('prepare', 'tampered', '--spec', self.spec, ok=False)
        self.assertIn('source changed', result.stderr)
        self.assertFalse((self.root / 'tampered').exists())
        self.assertEqual(self.calls(), [])

    def test_local_collection_subjects_only_preserves_native_quote_validation(self):
        local = self.local_source()
        local['schema_version'] = 4
        self.write('original-local.json', local)
        self.write('source.json', {'schema_version': 2, 'local_schema_version': 4,
            'sources': [{'path': 'original-local.json'}], 'review': {}, 'input_view': 'subjects_only'})
        spec = json.loads(self.spec.read_text())
        schema = Path(__file__).with_name('shr_single_pair') / 'Hierarchy-bootstrap-v79.output.schema.json'
        spec['runner']['output_schema'] = json.loads(schema.read_text())
        self.write('spec.json', spec)
        self.prepare('valid-quote')
        answer = {'ambiguities': [], 'resolutions': [], 'meaning': 'Selected topic', 'evidence': [
            {'quote': 'FULL LOCAL POST', 'supports': 'Selected topic', 'inference': None}]}
        self.cli('run', 'valid-quote', env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(answer)})
        self.assertEqual(self.show('valid-quote')['cases'][0]['status'], 'valid')
        self.prepare('invalid-quote', '--repeat')
        answer['evidence'][0]['quote'] = 'Local entry context'
        self.cli('run', 'invalid-quote', env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(answer)},
                 ok=False)
        case = self.show('invalid-quote')['cases'][0]
        self.assertEqual(case['status'], 'malformed')
        self.assertIn('exact contiguous excerpt of the local post', case['error'])

    def test_local_collection_saved_answers_are_witnesses_not_meaning_inputs(self):
        self.saved_meaning_source()
        self.cli('review', 'bootstrap', '--case', 'one', '--role', 'agent',
                 '--verdict', 'uncertain', '--comment', 'HISTORICAL REVIEW')
        self.write('source.json', {'schema_version': 2,
            'sources': [{'path': 'bootstrap-source.json'}],
            'experiments': [{'path': 'bootstrap', 'select': ['one']}],
            'review': {'criteria': ['Ground every restriction in the post.']}})
        spec = json.loads(self.spec.read_text())
        spec['dataset']['adapter'] = 'hierarchy_local_nodes'
        self.write('spec.json', spec)
        before = self.calls()
        self.prepare()
        case = self.show()['cases'][0]
        self.assertEqual(set(json.loads(case['inputs']['INPUT_JSON'])['local']), {'entry', 'post'})
        witnesses = case['evidence']['review']['historical_witnesses']
        self.assertEqual(len(witnesses), 2)
        self.assertEqual(witnesses[1]['parsed'], {'meaning': 'Vegetables intended to be cooked.'})
        self.assertIsNotNone(witnesses[1]['receipt'])
        self.assertNotIn('Vegetables intended to be cooked.', case['prompt'])
        self.assertNotIn('expected', case['evidence']['review'])
        plan = json.loads((self.root / 'E1/experiment.json').read_text())['plan']
        for name in ('bootstrap/experiment.json', 'bootstrap/run/results.jsonl',
                     'bootstrap/reviews.jsonl', 'bootstrap/execution-settings.jsonl'):
            self.assertIn(str(self.root / name), plan['sources'])
        self.assertEqual(witnesses[1]['reviews'][0]['comment'], 'HISTORICAL REVIEW')
        self.assertNotIn('HISTORICAL REVIEW', case['prompt'])
        self.assertEqual(self.calls(), before)

    def test_local_collection_comparison_witness_preserves_failure_without_canonical_input(self):
        self.saved_meaning_source()
        self.prepare('comparison')
        self.cli('run', 'comparison', env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps({
            'meaning': 'Vegetables intended to be cooked.', 'relation': 'neither',
            'reason': 'HISTORICAL FAILURE REASON'})})
        self.write('collection.json', {'schema_version': 2,
            'sources': [{'path': 'bootstrap-source.json'}],
            'experiments': [{'path': 'comparison'}], 'review': {}})
        spec = json.loads(self.spec.read_text())
        spec['dataset'] = {'adapter': 'hierarchy_local_nodes', 'path': 'collection.json'}
        self.write('collection-spec.json', spec)
        before = self.calls()
        self.cli('prepare', 'collection', '--spec', self.root / 'collection-spec.json')
        case = self.show('collection')['cases'][0]
        self.assertEqual(set(json.loads(case['inputs']['INPUT_JSON'])), {'local'})
        witness = case['evidence']['review']['historical_witnesses'][1]
        self.assertEqual(witness['parsed']['relation'], 'neither')
        self.assertEqual(witness['evidence']['canonical']['id'], 'C3')
        self.assertEqual(json.loads(witness['inputs']['INPUT_JSON'])['canonical']['meaning'],
                         'Fixed C3')
        self.assertEqual(witness['input_sha256'], self.show('comparison')['cases'][0]['input_sha256'])
        for text in ('Fixed C3', 'HISTORICAL FAILURE REASON', 'Vegetables intended to be cooked.'):
            self.assertNotIn(text, case['prompt'])
        self.assertEqual(self.calls(), before)

    def test_local_collection_preserves_unrun_witnesses_and_rejects_bad_references(self):
        self.saved_meaning_source(run=False)
        self.write('collection.json', {'schema_version': 2,
            'sources': [{'path': 'bootstrap-source.json'}],
            'experiments': [{'path': 'bootstrap'}], 'review': {}})
        spec = json.loads(self.spec.read_text())
        spec['dataset'] = {'adapter': 'hierarchy_local_nodes', 'path': 'collection.json'}
        self.write('spec.json', spec)
        self.prepare()
        witness = self.show()['cases'][0]['evidence']['review']['historical_witnesses'][1]
        self.assertEqual(witness['status'], 'unrun')
        self.assertIsNone(witness['receipt'])
        self.assertIsNone(witness['parsed'])
        collection = json.loads((self.root / 'collection.json').read_text())
        for index, bad in enumerate((
                {**collection, 'sources': []},
                {**collection, 'sources': [{'path': 'bootstrap-source.json', 'select': ['missing']}]},
                {**collection, 'sources': collection['sources'] * 2},
                {**collection, 'sources': [{'path': 'collection.json'}]},
                {**collection, 'review': {'expected': {'meaning': 'DO NOT ENFORCE'}}},
                {**collection, 'experiments': [{'path': 'bootstrap', 'select': ['missing']}]},
                {**collection, 'schema_version': 2.0})):
            self.write('bad.json', bad)
            spec['dataset']['path'] = 'bad.json'
            self.write('spec.json', spec)
            self.cli('prepare', f'bad-{index}', '--spec', self.spec, ok=False)
        self.assertEqual(self.calls(), [])

    def test_local_collection_freezes_contributing_review_sources(self):
        original = self.local_source()
        self.write('first.json', original)
        self.write('source.json', {'schema_version': 2, 'sources': [
            {'path': 'first.json'}], 'review': {}})
        self.prepare()
        original['nodes'][0]['review']['new_review'] = 'Changed after preparation'
        self.write('first.json', original)
        self.write('new-collection.json', {'schema_version': 2,
            'sources': [{'path': 'first.json'}],
            'experiments': [{'path': 'E1'}], 'review': {}})
        spec = json.loads(self.spec.read_text())
        spec['dataset']['path'] = 'new-collection.json'
        self.write('new-spec.json', spec)
        result = self.cli('prepare', 'new-collection', '--spec',
                          self.root / 'new-spec.json', ok=False)
        self.assertIn('source changed', result.stderr)
        self.assertEqual(self.calls(), [])

    def test_local_collection_preserves_malformed_output_and_diagnostic_error(self):
        self.saved_meaning_source(run=False)
        raw = '{"meaning": 42}'
        self.cli('run', 'bootstrap', env={'FAKE_RUNNER_PROMPT_RESPONSE': raw}, ok=False)
        self.write('collection.json', {'schema_version': 2,
            'sources': [{'path': 'bootstrap-source.json'}],
            'experiments': [{'path': 'bootstrap'}], 'review': {}})
        spec = json.loads(self.spec.read_text())
        spec['dataset'] = {'adapter': 'hierarchy_local_nodes', 'path': 'collection.json'}
        self.write('collection-spec.json', spec)
        before = self.calls()
        self.cli('prepare', 'collection', '--spec', self.root / 'collection-spec.json')
        case = self.show('collection')['cases'][0]
        witness = case['evidence']['review']['historical_witnesses'][1]
        self.assertEqual(witness['status'], 'malformed')
        self.assertIsNone(witness['parsed'])
        self.assertEqual(witness['output'], raw)
        self.assertTrue(witness['error'])
        self.assertNotIn(raw, case['prompt'])
        self.assertEqual(self.calls(), before)

    def test_bootstrap_control_references_preserve_inputs_and_review_metadata(self):
        historical = self.local_source()
        historical['nodes'][0]['review'] = {
            'expected': {'meaning': 'Synthetic original meaning'},
            'user_quotes': ['Synthetic fixture judgment']}
        historical_path = self.write('historical-controls.json', historical)
        historical_bytes = historical_path.read_bytes()
        revised = json.loads(historical_bytes)
        revised['nodes'][0]['review'].update(
            expected={'meaning': 'Synthetic revised meaning'},
            meaning_variants='Synthetic allowed variation',
            user_quotes=['Synthetic revised fixture judgment'])
        self.assertEqual(revised['corpus'], historical['corpus'])
        self.assertEqual([(node['id'], node['local']) for node in revised['nodes']],
                         [(node['id'], node['local']) for node in historical['nodes']])
        prepared = []
        for label, source in [('historical', historical), ('revised', revised)]:
            self.write('source.json', source)
            self.prepare(label)
            prepared.append(json.loads(self.cli('show', label, '--inputs-only', '--json').stdout))
        self.assertEqual(prepared[0], prepared[1])
        plan = json.loads((self.root / 'revised/experiment.json').read_text())['plan']
        self.assertEqual(plan['cases'][0]['evidence']['review'], revised['nodes'][0]['review'])
        for case in plan['cases']:
            payload = json.loads(case['inputs']['INPUT_JSON'])
            self.assertEqual(set(payload), {'local'})
            self.assertEqual(set(payload['local']), {'entry', 'post'})
            self.assertNotIn('user_quotes', case['inputs']['INPUT_JSON'])
            self.assertNotIn('expected', case['inputs']['INPUT_JSON'])
        self.assertEqual(historical_path.read_bytes(), historical_bytes)
        self.assertEqual(self.calls(), [])

    def test_subject_override_changes_only_heading_and_records_original(self):
        source = self.local_source()
        original = dict(source['nodes'][0], id='original')
        source['nodes'][0]['subject_override'] = 'Alternate heading'
        source['nodes'].append(original)
        self.write('source.json', source)
        self.prepare()
        cases = self.show()['cases']
        changed = json.loads(cases[0]['inputs']['INPUT_JSON'])
        original_input = json.loads(cases[1]['inputs']['INPUT_JSON'])
        self.assertEqual(changed['local']['entry'].pop('subject'), 'Alternate heading')
        self.assertEqual(original_input['local']['entry'].pop('subject'), 'Vegetables')
        self.assertEqual(changed, original_input)
        self.assertEqual(cases[0]['evidence']['subject_override'],
                         {'original': 'Vegetables', 'replacement': 'Alternate heading'})
        self.assertNotIn('subject_override', cases[1]['evidence'])
        self.assertEqual(self.calls(), [])

    def test_local_only_invalid_sources(self):
        for problem in ('missing_entry', 'duplicate_id', 'canonical_field'):
            source = self.local_source()
            if problem == 'missing_entry':
                source['nodes'][0]['local']['number'] = '9'
            elif problem == 'duplicate_id':
                source['nodes'].append(dict(source['nodes'][0]))
            else:
                source['nodes'][0]['canonical'] = {}
            self.write('source.json', source)
            result = self.cli('prepare', problem, '--spec', self.spec, ok=False)
            expected = {'missing_entry': 'unknown local entry number',
                        'duplicate_id': 'duplicate local node ID',
                        'canonical_field': 'local node.canonical'}[problem]
            self.assertIn(expected, result.stderr)
            self.assertFalse((self.root / problem).exists())
            self.assertEqual(self.calls(), [])

    def test_prepare_resolves_original_entries_and_preserves_shared_ancestors(self):
        source = self.source()
        self.prepare()
        case = self.show()['cases'][0]
        payload = json.loads(case['inputs']['INPUT_JSON'])
        self.assertEqual(set(payload), {'local', 'canonical'})
        self.assertEqual(payload['local'], {
            'entry': {'subject': 'Vegetables', 'context': 'Local entry context',
                      'ancestors': [{'subject': 'Food', 'context': 'Local root context'}]},
            'post': 'FULL LOCAL POST {INPUT_JSON}'})
        canonical = payload['canonical']
        self.assertEqual(canonical['parents'], ['C1', 'C2'])
        self.assertEqual([n['id'] for n in canonical['ancestors']], ['C0', 'C1', 'C2'])
        self.assertEqual(canonical['ancestors'][1]['parents'], ['C0'])
        self.assertEqual(canonical['entries'][0]['ancestors'],
                         [{'subject': 'Preparation', 'context': 'Original ancestor'}])
        self.assertEqual(set(canonical['ancestors'][0]), {'id', 'subject', 'meaning', 'parents'})
        for excluded in ('REVIEW ONLY', 'CANONICAL POST EXCLUDED', 'LOCAL DESCENDANT', 'Fixed C4'):
            self.assertNotIn(excluded, case['prompt'])
        self.assertEqual(case['evidence']['review'], source['pairs'][0]['review'])
        plan = json.loads((self.root / 'E1/experiment.json').read_text())['plan']
        path = self.root / 'notes.json'
        self.assertEqual(plan['sources'][str(path)], hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertIn('hierarchy_node_pairs.py', plan['code'])
        self.assertEqual(self.calls(), [])

    def test_v2_includes_recursive_descendants_without_local_descendants(self):
        source = self.source()
        source['schema_version'] = 2
        nodes = source['canonical_states']['current']
        ref = nodes[0]['entries']
        nodes.extend([
            {'id': 'C5', 'subject': 'Shared descendant', 'meaning': 'Fixed C5',
             'entries': ref, 'parents': ['C3', 'C4']},
            {'id': 'C6', 'subject': 'Deep descendant', 'meaning': 'Fixed C6',
             'entries': ref, 'parents': ['C5']},
            {'id': 'C8', 'subject': 'Unrelated', 'meaning': 'Excluded sibling',
             'entries': ref, 'parents': ['C0']}])
        self.write('source.json', source)
        self.prepare()
        case = self.show()['cases'][0]
        canonical = json.loads(case['inputs']['INPUT_JSON'])['canonical']
        self.assertEqual([n['id'] for n in canonical['descendants']], ['C4', 'C5', 'C6'])
        self.assertEqual(canonical['descendants'][1]['parents'], ['C3', 'C4'])
        self.assertEqual(set(canonical['descendants'][0]), {'id', 'subject', 'meaning', 'parents'})
        self.assertEqual([n['id'] for n in canonical['ancestors']], ['C0', 'C1', 'C2'])
        for excluded in ('LOCAL DESCENDANT', 'Excluded sibling', 'CANONICAL POST EXCLUDED', 'REVIEW ONLY'):
            self.assertNotIn(excluded, case['prompt'])
        self.assertEqual(case['evidence']['version'], 'hierarchy-node-pairs-v2')
        self.assertEqual(self.calls(), [])

    def test_bad_graph_or_source_reference_fails_before_preparation(self):
        for problem in ('cycle', 'missing_parent', 'missing_entry', 'missing_ancestor',
                        'duplicate_node', 'duplicate_subject', 'extra_field'):
            with self.subTest(problem=problem):
                source = self.source()
                nodes = source['canonical_states']['current']
                if problem == 'cycle':
                    nodes[0]['parents'] = ['C3']
                elif problem == 'missing_parent':
                    nodes[3]['parents'] = ['absent']
                elif problem == 'missing_entry':
                    source['pairs'][0]['local']['number'] = '9'
                elif problem in ('missing_ancestor', 'duplicate_subject'):
                    corpus = json.loads((self.root / 'notes.json').read_text())
                    entries = corpus['notes'][0]['subjects']
                    if problem == 'missing_ancestor':
                        entries.pop(0)
                    else:
                        entries.append(dict(entries[0]))
                    self.write('notes.json', corpus)
                elif problem == 'duplicate_node':
                    nodes.append(dict(nodes[0]))
                else:
                    nodes[3]['expected'] = 'neither'
                self.write('source.json', source)
                result = self.cli('prepare', problem, '--spec', self.spec, ok=False)
                expected = {'cycle': 'contains a cycle', 'missing_parent': 'unknown canonical parent',
                            'missing_entry': 'unknown local entry number',
                            'missing_ancestor': 'missing original local ancestor',
                            'duplicate_node': 'duplicate canonical node ID',
                            'duplicate_subject': 'duplicate local hierarchy number',
                            'extra_field': 'canonical node.expected'}[problem]
                self.assertIn(expected, result.stderr)
                self.assertFalse((self.root / problem).exists())
                self.assertEqual(self.calls(), [])

    def test_output_contract_through_native_validation_and_offline_runner(self):
        self.source()
        self.prepare()
        value = {'meaning': 'A local definition', 'relation': 'canonical_contains_local',
                 'reason': 'Fixture conclusion'}
        self.cli('run', 'E1', env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(value)})
        self.assertEqual(self.show()['cases'][0]['parsed'], value)
        case = self.show()['cases'][0]
        for bad in [dict(value, meaning=None), dict(value, relation='a_parent_of_b'),
                    dict(value, meaning_B='echo')]:
            with self.assertRaises(ValueError):
                experiment_inputs.validate({'adapter': 'hierarchy_node_pairs'}, case,
                                           json.dumps(bad), None)
        valid = dict(value, meaning=None, relation='uncertain')
        self.assertEqual(experiment_inputs.validate({'adapter': 'hierarchy_node_pairs'}, case,
                         json.dumps(valid), None)['parsed'], valid)

    def meaning_diagnostic_source(self, answer=None, run=True, schema_version=4):
        local = self.local_source()
        local['schema_version'] = schema_version
        self.write('producer-source.json', local)
        spec = json.loads(self.spec.read_text())
        spec['dataset']['path'] = 'producer-source.json'
        self.write('producer-spec.json', spec)
        self.cli('prepare', 'producer', '--spec', 'producer-spec.json')
        if run:
            self.cli('run', 'producer', env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(
                {'meaning': 'Vegetables intended to be cooked.\nExact second clause.'}
                if answer is None else answer)})
        case = self.show('producer')['cases'][0]
        reference = {'experiment': 'producer', 'case': 'one',
                     'record_sha256': case.get('receipt', {}).get('record_sha256', '0' * 64)}
        source = {'schema_version': 1, 'corpus': 'notes.json', 'nodes': [
            {'id': 'meaning-only', 'producer': reference, 'include_source': False,
             'review': {'expected': 'REVIEW ONLY'}},
            {'id': 'with-source', 'producer': reference, 'include_source': True,
             'review': {'expected': 'REVIEW ONLY'}}]}
        self.write('source.json', source)
        spec['dataset'] = {'adapter': 'hierarchy_meaning_diagnostics', 'path': 'source.json'}
        spec['runner']['output_schema'] = {'type': 'object', 'properties': {
            'requires_consumption': {'type': 'boolean'}},
            'required': ['requires_consumption'], 'additionalProperties': False}
        self.write('spec.json', spec)
        return source


    def test_meaning_diagnostic_copies_exact_meaning_and_optional_original_source(self):
        source = self.meaning_diagnostic_source()
        producer = self.show('producer')['cases'][0]
        original = json.loads(producer['inputs']['INPUT_JSON'])['local']
        self.prepare()
        cases = self.show()['cases']
        meaning = producer['parsed']['meaning']
        self.assertEqual(json.loads(cases[0]['inputs']['INPUT_JSON']), {'meaning': meaning})
        self.assertEqual(json.loads(cases[1]['inputs']['INPUT_JSON']),
                         {'meaning': meaning, 'local': original})
        for case in cases:
            self.assertNotIn('REVIEW ONLY', case['prompt'])
            self.assertFalse(case['evidence']['application_allowed'])
            self.assertEqual(case['evidence']['producer']['receipt'], producer['receipt'])
            self.assertEqual(case['evidence']['review'], source['nodes'][0]['review'])
        self.assertEqual(len(self.calls()), 1)


    def test_meaning_diagnostic_freezes_producer_sources_and_reuses_exact_answers(self):
        self.meaning_diagnostic_source()
        self.prepare()
        plan = json.loads((self.root / 'E1/experiment.json').read_text())['plan']
        producer_plan = json.loads((self.root / 'producer/experiment.json').read_text())['plan']
        for path in (self.root / 'producer/experiment.json', self.root / 'producer/runner-config.json',
                     Path(producer_plan['run_directory']) / 'manifest.json',
                     Path(producer_plan['run_directory']) / 'results.jsonl',
                     self.root / 'producer-source.json', self.root / 'notes.json'):
            self.assertEqual(plan['sources'][str(path)], hashlib.sha256(path.read_bytes()).hexdigest())
        self.cli('run', 'E1', env={'FAKE_RUNNER_PROMPT_RESPONSE':
                                 '{"requires_consumption": false}'})
        report = self.show()
        self.assertEqual(report['adapter'], 'hierarchy_meaning_diagnostics')
        self.assertEqual(report['summary']['valid'], 2)
        self.assertTrue(all(case['parsed'] == {'requires_consumption': False}
                            for case in report['cases']))
        self.prepare('E2')
        self.cli('run', 'E2')
        self.assertTrue(all(case['reused'] for case in self.show('E2')['cases']))
        self.assertEqual(len(self.calls()), 3)


    def test_meaning_diagnostic_rejects_receipt_mismatch_and_missing_case(self):
        source = self.meaning_diagnostic_source()
        for index, change in enumerate(({'record_sha256': '0' * 64}, {'case': 'absent'})):
            candidate = json.loads(json.dumps(source))
            candidate['nodes'][0]['producer'].update(change)
            self.write('source.json', candidate)
            result = self.cli('prepare', f'bad-receipt-{index}', '--spec', self.spec, ok=False)
            self.assertIn('receipt' if index == 0 else 'valid saved meaning', result.stderr)
            self.assertFalse((self.root / f'bad-receipt-{index}').exists())


    def test_meaning_diagnostic_rejects_null_producer(self):
        self.meaning_diagnostic_source(answer={'meaning': None})
        result = self.cli('prepare', 'bad-null', '--spec', self.spec, ok=False)
        self.assertIn('nonempty text', result.stderr)
        self.assertFalse((self.root / 'bad-null').exists())


    def test_meaning_diagnostic_rejects_unrun_producer(self):
        self.meaning_diagnostic_source(run=False)
        result = self.cli('prepare', 'bad-unrun', '--spec', self.spec, ok=False)
        self.assertIn('valid saved meaning', result.stderr)
        self.assertFalse((self.root / 'bad-unrun').exists())


    def test_meaning_diagnostic_rejects_invalid_producer(self):
        self.meaning_diagnostic_source(run=False)
        self.cli('run', 'producer', env={'FAKE_RUNNER_PROMPT_RESPONSE':
                                       '{"meaning": 42}'}, ok=False)
        result = self.cli('prepare', 'bad-invalid', '--spec', self.spec, ok=False)
        self.assertIn('valid saved meaning', result.stderr)
        self.assertFalse((self.root / 'bad-invalid').exists())


    def test_meaning_diagnostic_requires_schema_four_original_source(self):
        self.meaning_diagnostic_source(schema_version=1)
        result = self.cli('prepare', 'legacy', '--spec', self.spec, ok=False)
        self.assertIn('original schema-4 local input', result.stderr)
        self.assertFalse((self.root / 'legacy').exists())


    def test_meaning_diagnostic_checks_full_post_and_every_root_tree_entry(self):
        source = self.meaning_diagnostic_source()
        original = json.loads((self.root / 'notes.json').read_text())
        source['corpus'] = 'current-notes.json'
        for index, field in enumerate(('post', 'subject', 'context', 'ancestor', 'descendant')):
            with self.subTest(field=field):
                changed = json.loads(json.dumps(original))
                if field == 'post':
                    changed['notes'][0]['text'] += ' changed'
                else:
                    row = changed['notes'][0]['subjects'][
                        0 if field == 'ancestor' else 2 if field == 'descendant' else 1]
                    row['subject' if field == 'subject' else 'context'] += ' changed'
                self.write('current-notes.json', changed)
                self.write('source.json', source)
                result = self.cli('prepare', f'bad-local-{index}', '--spec', self.spec, ok=False)
                self.assertIn('original schema-4 local input', result.stderr)
                self.assertFalse((self.root / f'bad-local-{index}').exists())


    def test_meaning_diagnostic_source_and_producer_reference_are_strict(self):
        source = self.meaning_diagnostic_source()
        variants = [None, {**source, 'schema_version': True}, {**source, 'nodes': []}]
        for field, value in (('include_source', 1), ('review', None), ('producer', None),
                             ('producer', {**source['nodes'][0]['producer'], 'extra': True}),
                             ('producer', {**source['nodes'][0]['producer'], 'record_sha256': 'bad'})):
            candidate = json.loads(json.dumps(source))
            candidate['nodes'][0][field] = value
            variants.append(candidate)
        variants.append({**source, 'nodes': source['nodes'] * 2})
        for index, candidate in enumerate(variants):
            with self.subTest(index=index):
                self.write('source.json', candidate)
                self.cli('prepare', f'bad-definition-{index}', '--spec', self.spec, ok=False)
                self.assertFalse((self.root / f'bad-definition-{index}').exists())


    def test_meaning_diagnostic_supports_schema_four_collection_producers(self):
        self.meaning_diagnostic_source(run=False)
        self.write('collection.json', {'schema_version': 2, 'local_schema_version': 4,
                                     'sources': [{'path': 'producer-source.json'}], 'review': {}})
        spec = json.loads((self.root / 'producer-spec.json').read_text())
        spec['dataset']['path'] = 'collection.json'
        self.write('collection-spec.json', spec)
        self.cli('prepare', 'collection', '--spec', 'collection-spec.json')
        self.cli('run', 'collection', env={'FAKE_RUNNER_PROMPT_RESPONSE':
                                         '{"meaning":"Exact collection meaning"}'})
        produced = self.show('collection')['cases'][0]
        source = json.loads((self.root / 'source.json').read_text())
        for node in source['nodes']:
            node['producer'] = {'experiment': 'collection', 'case': produced['id'],
                                'record_sha256': produced['receipt']['record_sha256']}
        self.write('source.json', source)
        self.prepare()
        self.assertEqual(json.loads(self.show()['cases'][0]['inputs']['INPUT_JSON']),
                         {'meaning': 'Exact collection meaning'})


    def test_meaning_diagnostic_binds_reused_producer_to_its_native_receipt(self):
        source = self.meaning_diagnostic_source()
        self.cli('prepare', 'producer-reuse', '--from', 'producer')
        self.cli('run', 'producer-reuse')
        produced = self.show('producer-reuse')['cases'][0]
        self.assertTrue(produced['reused'])
        for node in source['nodes']:
            node['producer'] = {'experiment': 'producer-reuse', 'case': produced['id'],
                                'record_sha256': produced['receipt']['record_sha256']}
        self.write('source.json', source)
        self.prepare()
        plan = json.loads((self.root / 'E1/experiment.json').read_text())['plan']
        self.assertIn(produced['receipt']['results_path'], plan['sources'])
        self.assertEqual(self.show()['cases'][0]['evidence']['producer']['receipt'],
                         produced['receipt'])
        self.assertEqual(len(self.calls()), 1)


    def test_meaning_diagnostic_rejects_wrong_producer_adapter(self):
        self.meaning_diagnostic_source()
        diagnostic_source = json.loads((self.root / 'source.json').read_text())
        diagnostic_spec = json.loads(self.spec.read_text())
        self.write('comparison-source.json', self.source())
        comparison_spec = json.loads(self.spec.read_text())
        comparison_spec['dataset']['path'] = 'comparison-source.json'
        self.write('comparison-spec.json', comparison_spec)
        self.cli('prepare', 'comparison', '--spec', 'comparison-spec.json')
        self.cli('run', 'comparison', env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps({
            'meaning': 'Comparison meaning', 'relation': 'neither', 'reason': 'Fixture'})})
        produced = self.show('comparison')['cases'][0]
        for node in diagnostic_source['nodes']:
            node['producer'] = {'experiment': 'comparison', 'case': produced['id'],
                                'record_sha256': produced['receipt']['record_sha256']}
        self.write('source.json', diagnostic_source)
        self.write('spec.json', diagnostic_spec)
        result = self.cli('prepare', 'bad-adapter', '--spec', self.spec, ok=False)
        self.assertIn('hierarchy_local_nodes experiment', result.stderr)
        self.assertFalse((self.root / 'bad-adapter').exists())


    def test_meaning_diagnostic_rejects_changed_producer_receipt(self):
        self.meaning_diagnostic_source()
        path = self.root / 'producer/run/results.jsonl'
        record = json.loads(path.read_text())
        record['final_output_raw'] = '{"meaning":"Forged meaning"}'
        path.write_text(json.dumps(record) + '\n')
        self.cli('prepare', 'forged-diagnostic', '--spec', self.spec, ok=False)
        self.assertFalse((self.root / 'forged-diagnostic').exists())


    def test_saved_controlled_meanings_are_rejected_as_original_node_pair_evidence(self):
        for index, control in enumerate(({'context_overrides': {'1.1': 'Served with a meal'}},
                                         {'post_override': 'Synthetic meal post'})):
            with self.subTest(control=control):
                local = self.local_source()
                local['schema_version'] = 4
                local['nodes'][0].update(control)
                name = f'controlled-bootstrap-{index}'
                self.write(name + '-source.json', local)
                spec = json.loads(self.spec.read_text())
                spec['dataset']['path'] = name + '-source.json'
                self.write(name + '-spec.json', spec)
                self.cli('prepare', name, '--spec', name + '-spec.json')
                self.cli('run', name, env={'FAKE_RUNNER_PROMPT_RESPONSE':
                                         '{"meaning":"Served vegetable food"}'})
                source = self.source()
                source['pairs'][0]['local_meaning_from'] = {'experiment': name, 'case': 'one'}
                self.write('source.json', source)
                result = self.cli('prepare', f'controlled-mismatch-{index}', '--spec', self.spec,
                                  ok=False)
                self.assertIn('saved local meaning evidence does not match original local input',
                              result.stderr)
                self.assertFalse((self.root / f'controlled-mismatch-{index}').exists())


    def test_schema4_context_controls_change_only_named_contexts(self):
        source = self.local_source()
        source['schema_version'] = 4
        self.write('source.json', source)
        self.prepare('baseline')
        baseline = self.show('baseline')['cases'][0]
        self.write('source.json', {**source, 'nodes': [
            {**source['nodes'][0], 'context_overrides': {}}]})
        self.prepare('empty-control')
        empty = self.show('empty-control')['cases'][0]
        for field in ('id', 'inputs', 'input_sha256', 'evidence'):
            self.assertEqual(empty[field], baseline[field])
        original_node = json.loads(json.dumps(source['nodes'][0]))
        source['nodes'][0]['id'] = 'controlled'
        source['nodes'][0]['context_overrides'] = {
            '1': 'Meal preparation', '1.1': 'Cooked vegetables served with a meal',
            '1.1.1': 'Vegetables already served'}
        source['nodes'].append(original_node)
        self.write('source.json', source)
        corpus = (self.root / 'notes.json').read_bytes()
        self.prepare()
        cases = self.show()['cases']
        changed = json.loads(cases[0]['inputs']['INPUT_JSON'])
        original = json.loads(cases[1]['inputs']['INPUT_JSON'])
        self.assertEqual(changed['local']['hierarchy']['entries'][1]['context'],
                         'Cooked vegetables served with a meal')
        for row, context in zip(changed['local']['hierarchy']['entries'],
                                ('Local root context', 'Local entry context', 'Excluded')):
            row['context'] = context
        self.assertEqual(changed, original)
        self.assertEqual(cases[0]['id'], 'controlled')
        self.assertEqual(cases[1]['id'], baseline['id'])
        self.assertEqual(cases[1]['inputs'], baseline['inputs'])
        self.assertEqual(cases[1]['input_sha256'], baseline['input_sha256'])
        self.assertEqual(cases[1]['evidence'], baseline['evidence'])
        self.assertEqual(cases[0]['evidence']['context_overrides'], {
            '1': {'original': 'Local root context', 'replacement': 'Meal preparation'},
            '1.1': {'original': 'Local entry context',
                    'replacement': 'Cooked vegetables served with a meal'},
            '1.1.1': {'original': 'Excluded', 'replacement': 'Vegetables already served'}})
        self.assertNotIn('context_overrides', cases[1]['evidence'])
        self.assertEqual((self.root / 'notes.json').read_bytes(), corpus)
        self.assertEqual(self.calls(), [])


    def test_schema4_post_control_supplies_native_diagnostic_quote_validation(self):
        source = self.local_source()
        source['schema_version'] = 4
        source['nodes'][0]['post_override'] = 'SYNTHETIC POST: vegetables were served with supper.'
        source['nodes'][0]['context_overrides'] = {'1.1': 'FULL LOCAL POST'}
        self.write('source.json', source)
        self.prepare()
        case = self.show()['cases'][0]
        local = json.loads(case['inputs']['INPUT_JSON'])['local']
        self.assertEqual(local['post'], source['nodes'][0]['post_override'])
        self.assertEqual(case['evidence']['post_override'], {
            'original': 'FULL LOCAL POST {INPUT_JSON}',
            'replacement': source['nodes'][0]['post_override']})
        self.assertNotIn('post_override', case['inputs']['INPUT_JSON'])
        self.assertNotIn('REVIEW ONLY', case['inputs']['INPUT_JSON'])
        schema = json.loads((Path(__file__).with_name('shr_single_pair') /
                             'Hierarchy-bootstrap-v71.output.schema.json').read_text())
        answer = {'meaning': 'Vegetables served as food', 'evidence': [
            {'quote': 'vegetables were served with supper', 'supports': 'Served food',
             'inference': None}]}
        self.assertEqual(experiment_inputs.validate({'adapter': 'hierarchy_local_nodes'}, case,
                         json.dumps(answer), schema)['parsed'], answer)
        answer['evidence'][0]['quote'] = 'FULL LOCAL POST'
        with self.assertRaisesRegex(ValueError, 'exact contiguous excerpt of the local post'):
            experiment_inputs.validate({'adapter': 'hierarchy_local_nodes'}, case,
                                       json.dumps(answer), schema)
        self.assertEqual(self.calls(), [])


    def test_schema4_diagnostic_quotes_match_nonbreaking_and_regular_spaces(self):
        schema = json.loads((Path(__file__).with_name('shr_single_pair') /
                             'Hierarchy-bootstrap-v130.output.schema.json').read_text())
        for index, (post_space, quote_space) in enumerate((('\u00a0', ' '), (' ', '\u00a0'))):
            with self.subTest(post_space=post_space, quote_space=quote_space):
                source = self.local_source()
                source['schema_version'] = 4
                source['nodes'][0]['post_override'] = (
                    'Dezeen Showroom:' + post_space + 'the extractor fan appears invisible.')
                self.write('source.json', source)
                self.prepare(f'space-{index}')
                case = self.show(f'space-{index}')['cases'][0]
                answer = {'ambiguities': [], 'resolutions': [],
                          'meaning': 'Extractor fans remove cooking fumes.',
                          'title': 'Extractor fans', 'evidence': [
                              {'quote': 'Showroom:' + quote_space + 'the extractor fan',
                               'supports': 'The post names the extractor fan.',
                               'inference': None}]}
                result = experiment_inputs.validate(
                    {'adapter': 'hierarchy_local_nodes'}, case, json.dumps(answer), schema)
                self.assertEqual(result['parsed'], answer)
                for quote in ('Showroom: the exhaust fan', 'Showroom:\tthe extractor fan',
                              'Showroom:  the extractor fan'):
                    answer['evidence'][0]['quote'] = quote
                    with self.assertRaisesRegex(ValueError, 'exact contiguous excerpt'):
                        experiment_inputs.validate(
                            {'adapter': 'hierarchy_local_nodes'}, case, json.dumps(answer), schema)
        self.assertEqual(self.calls(), [])


    def test_schema4_context_and_post_controls_reject_invalid_inputs(self):
        source = self.local_source()
        source['schema_version'] = 4
        corpus = json.loads((self.root / 'notes.json').read_text())
        corpus['notes'][0]['subjects'].append(
            {'number': '2', 'subject': 'Another root', 'context': 'Outside selected tree'})
        self.write('notes.json', corpus)
        invalid = [('context_overrides', value) for value in (
            None, [], 'not an object', {'9': 'Unknown'}, {'2': 'Off-tree'},
            {'1.01': 'Not an original number'}, {'1.1': None}, {'1.1': True},
            {'1.1': 7}, {'1.1': []}, {'1.1': ''}, {'1.1': ' '})]
        invalid.extend(('post_override', value) for value in (None, True, 7, [], {}, '', ' '))
        for index, (field, value) in enumerate(invalid):
            with self.subTest(field=field, value=value):
                candidate = json.loads(json.dumps(source))
                candidate['nodes'][0][field] = value
                self.write('source.json', candidate)
                result = self.cli('prepare', f'invalid-control-{index}', '--spec', self.spec,
                                  ok=False)
                self.assertIn(field, result.stderr)
                self.assertFalse((self.root / f'invalid-control-{index}').exists())
        self.assertEqual(self.calls(), [])


    def test_context_and_post_controls_require_schema4_standalone_local_nodes(self):
        for field, value in (('context_overrides', {'1.1': 'Replacement context'}),
                             ('post_override', 'Synthetic post')):
            for version in (1, 3):
                with self.subTest(field=field, version=version, adapter='hierarchy_local_nodes'):
                    source = self.local_source()
                    source['schema_version'] = version
                    source['nodes'][0][field] = value
                    self.write('source.json', source)
                    result = self.cli('prepare', f'bad-local-{field}-{version}', '--spec', self.spec,
                                      ok=False)
                    self.assertIn(f'local node.{field}', result.stderr)
            for version in (1, 2):
                with self.subTest(field=field, version=version, adapter='hierarchy_node_pairs'):
                    source = self.source()
                    source['schema_version'] = version
                    source['pairs'][0][field] = value
                    self.write('source.json', source)
                    result = self.cli('prepare', f'bad-pair-{field}-{version}', '--spec', self.spec,
                                      ok=False)
                    self.assertIn(field, result.stderr)
        self.assertEqual(self.calls(), [])


    def test_local_collection_schema4_regenerates_and_deduplicates_source_bound_inputs(self):
        original = self.local_source()
        self.write('legacy-source.json', original)
        spec = json.loads(self.spec.read_text())
        spec['dataset']['path'] = 'legacy-source.json'
        self.write('legacy-spec.json', spec)
        self.cli('prepare', 'legacy', '--spec', 'legacy-spec.json')
        self.cli('run', 'legacy', env={'FAKE_RUNNER_PROMPT_RESPONSE':
                                     '{"meaning":"HISTORICAL MEANING"}'})
        legacy = self.show('legacy')['cases'][0]
        self.write('tree-source.json', {**original, 'schema_version': 4})
        overridden = json.loads(json.dumps(original))
        overridden['nodes'][0]['subject_override'] = 'Cooking vegetables'
        self.write('override-source.json', overridden)
        self.write('source.json', {'schema_version': 2, 'local_schema_version': 4,
            'sources': [{'path': 'legacy-source.json'}, {'path': 'tree-source.json'},
                        {'path': 'override-source.json'}],
            'experiments': [{'path': 'legacy'}], 'review': {}})
        before = self.calls()
        self.prepare('collection')
        cases = self.show('collection')['cases']
        self.assertEqual(len(cases), 2)
        locals_ = [json.loads(row['inputs']['INPUT_JSON'])['local'] for row in cases]
        for local in locals_:
            self.assertEqual(set(local), {'post', 'hierarchy'})
            self.assertEqual(local['post'], 'FULL LOCAL POST {INPUT_JSON}')
            self.assertEqual(local['hierarchy']['selected'], '1.1')
            self.assertEqual(local['hierarchy']['entries'][0],
                             {'number': '1', 'subject': 'Food', 'context': 'Local root context'})
            self.assertEqual(local['hierarchy']['entries'][1]['context'], 'Local entry context')
            self.assertEqual(local['hierarchy']['entries'][2]['subject'], 'LOCAL DESCENDANT')
        self.assertEqual([local['hierarchy']['entries'][1]['subject'] for local in locals_],
                         ['Vegetables', 'Cooking vegetables'])
        witnesses = cases[0]['evidence']['review']['historical_witnesses']
        self.assertEqual(len(witnesses), 3)
        self.assertEqual(witnesses[0]['inputs'], legacy['inputs'])
        self.assertEqual(witnesses[2]['inputs'], legacy['inputs'])
        self.assertEqual(witnesses[2]['parsed'], {'meaning': 'HISTORICAL MEANING'})
        self.assertNotIn('HISTORICAL MEANING', cases[0]['prompt'])
        self.assertEqual(cases[1]['evidence']['subject_override']['replacement'],
                         'Cooking vegetables')
        plan = json.loads((self.root / 'collection/experiment.json').read_text())['plan']
        self.assertEqual(plan['sources'][str(self.root / 'notes.json')],
                         hashlib.sha256((self.root / 'notes.json').read_bytes()).hexdigest())
        self.assertEqual(self.calls(), before)


    def test_local_collection_schema4_rejects_changed_original_evidence(self):
        from sse_multivector import hierarchy_node_pairs

        self.local_source()
        self.prepare('legacy')
        report = self.show('legacy')
        original = json.loads(report['cases'][0]['inputs']['INPUT_JSON'])
        collection = {'schema_version': 2, 'local_schema_version': 4,
                      'sources': [{'path': 'source.json'}],
                      'experiments': [{'path': 'legacy'}], 'review': {}}
        for changed in (
                {'post': 'A different post'},
                {'entry': {**original['local']['entry'], 'subject': 'A different subject'}},
                {'entry': {**original['local']['entry'], 'context': 'A different context'}},
                {'entry': {**original['local']['entry'], 'ancestors': [
                    {'subject': 'Food', 'context': 'A different ancestor context'}]}},
                {'entry': {**original['local']['entry'], 'unknown': 'Malformed field'}},
                {'hierarchy': {'selected': '1.1', 'entries': []}}):
            with self.subTest(changed=changed):
                witness = json.loads(json.dumps(report))
                witness['cases'][0]['inputs']['INPUT_JSON'] = json.dumps(
                    {'local': {**original['local'], **changed}})
                with self.assertRaisesRegex(ValueError, 'does not match original local input'):
                    hierarchy_node_pairs.create_source(
                        collection, base=self.root,
                        read=lambda path: json.loads(Path(path).read_text()),
                        local_only=True, load_report=lambda path: witness)
        self.assertEqual(self.calls(), [])


    def test_local_collection_preserves_and_reconstructs_schema4_controls(self):
        source = self.local_source()
        source['schema_version'] = 4
        source['nodes'][0].update({
            'subject_override': 'Served vegetables',
            'context_overrides': {'1': 'Meal preparation', '1.1': 'Vegetables served as food'},
            'post_override': 'SYNTHETIC POST: vegetables were served with supper.'})
        self.write('controlled-source.json', source)
        spec = json.loads(self.spec.read_text())
        spec['dataset']['path'] = 'controlled-source.json'
        self.write('controlled-spec.json', spec)
        self.cli('prepare', 'controlled', '--spec', 'controlled-spec.json')
        original = self.show('controlled')['cases'][0]
        for name, target in (('preserved', {}), ('reconstructed', {'local_schema_version': 4})):
            self.write('source.json', {'schema_version': 2, **target,
                'sources': [{'path': 'controlled-source.json'}],
                'experiments': [{'path': 'controlled'}], 'review': {}})
            self.prepare(name)
            cases = self.show(name)['cases']
            self.assertEqual(len(cases), 1)
            self.assertEqual(cases[0]['inputs'], original['inputs'])
            for field in ('subject_override', 'context_overrides', 'post_override'):
                self.assertEqual(cases[0]['evidence'][field], original['evidence'][field])
            witnesses = cases[0]['evidence']['review']['historical_witnesses']
            self.assertEqual(len(witnesses), 2)
            self.assertEqual(witnesses[1]['inputs'], original['inputs'])
            self.assertNotIn('historical_witnesses', cases[0]['inputs']['INPUT_JSON'])
        self.assertEqual(self.show('preserved')['cases'][0]['id'],
                         self.show('reconstructed')['cases'][0]['id'])
        self.assertEqual(self.calls(), [])


    def test_local_collection_schema4_rejects_changed_control_evidence(self):
        from sse_multivector import hierarchy_node_pairs

        source = self.local_source()
        source['schema_version'] = 4
        source['nodes'][0].update({
            'context_overrides': {'1.1': 'Vegetables served as food'},
            'post_override': 'Synthetic meal post'})
        self.write('controlled-source.json', source)
        spec = json.loads(self.spec.read_text())
        spec['dataset']['path'] = 'controlled-source.json'
        self.write('controlled-spec.json', spec)
        self.cli('prepare', 'controlled', '--spec', 'controlled-spec.json')
        report = self.show('controlled')
        collection = {'schema_version': 2, 'local_schema_version': 4,
            'sources': [{'path': 'controlled-source.json'}],
            'experiments': [{'path': 'controlled'}], 'review': {}}
        for field, key in (('context_overrides', 'original'), ('context_overrides', 'replacement'),
                           ('post_override', 'original'), ('post_override', 'replacement')):
            with self.subTest(field=field, key=key):
                witness = json.loads(json.dumps(report))
                change = witness['cases'][0]['evidence'][field]
                if field == 'context_overrides':
                    change = change['1.1']
                change[key] = 'Changed control evidence'
                with self.assertRaisesRegex(ValueError, 'does not match original local input'):
                    hierarchy_node_pairs.create_source(
                        collection, base=self.root,
                        read=lambda path: json.loads(Path(path).read_text()),
                        local_only=True, load_report=lambda path: witness)
        witness = json.loads(json.dumps(report))
        witness['cases'][0]['evidence']['context_overrides'] = {}
        with self.assertRaisesRegex(ValueError, 'does not match original local input'):
            hierarchy_node_pairs.create_source(
                collection, base=self.root,
                read=lambda path: json.loads(Path(path).read_text()),
                local_only=True, load_report=lambda path: witness)
        self.assertEqual(self.calls(), [])


    def test_local_collection_schema4_resolves_each_original_entry_once(self):
        from sse_multivector import hierarchy_node_pairs

        source = self.local_source()
        source['nodes'].extend([{**source['nodes'][0], 'id': f'duplicate-{i}'} for i in range(3)])
        self.write('source.json', source)
        reads = []

        def read(path):
            reads.append(Path(path))
            return json.loads(Path(path).read_text())

        cases, summary = hierarchy_node_pairs.create_source(
            {'schema_version': 2, 'local_schema_version': 4,
             'sources': [{'path': 'source.json'}], 'review': {}},
            base=self.root, read=read, local_only=True)
        self.assertEqual(len(cases), 1)
        self.assertEqual(summary['historical_witnesses'], 4)
        self.assertEqual(reads.count(self.root / 'notes.json'), 2)
        self.assertEqual(self.calls(), [])


    def test_local_collection_schema4_rejects_invalid_target_schema(self):
        original = self.local_source()
        self.write('legacy-source.json', original)
        for index, version in enumerate((None, True, 1, 3, 4.0, '4')):
            with self.subTest(version=version):
                self.write('source.json', {'schema_version': 2,
                    'local_schema_version': version,
                    'sources': [{'path': 'legacy-source.json'}], 'review': {}})
                result = self.cli('prepare', f'bad-target-{index}', '--spec', self.spec, ok=False)
                self.assertIn('collection local_schema_version must be 4', result.stderr)
        self.assertEqual(self.calls(), [])




if __name__ == '__main__':
    unittest.main()
