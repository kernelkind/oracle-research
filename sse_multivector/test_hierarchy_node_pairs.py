"""Source-bound local/canonical comparisons through the native experiment CLI."""

import hashlib
import json
from pathlib import Path
import unittest

from sse_multivector import experiment_inputs
from sse_multivector import test_experiment as fixtures


class HierarchyNodePairsTests(unittest.TestCase):
    setUp = fixtures.ExperimentTests.setUp
    write = fixtures.ExperimentTests.write
    cli = fixtures.ExperimentTests.cli
    prepare = fixtures.ExperimentTests.prepare
    show = fixtures.ExperimentTests.show
    calls = fixtures.ExperimentTests.calls

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
        from sse_multivector import test_canonical_trial as roots_fixtures
        roots_fixtures.CanonicalTrialTests.setup_trial(self, schema_version=2)
        state_path = self.root / 'trial/state.json'
        for case, value in (
                ('bootstrap', {'meaning': 'Fixed cooking meaning'}),
                ('C001', {'meaning': 'Fixed food meaning', 'relation': 'canonical_contains_local',
                          'reason': 'Contained fixture'}),
                ('C001', {'meaning': 'Independent meaning', 'relation': 'neither',
                          'reason': 'Independent fixture'})):
            state = json.loads(state_path.read_text())
            self.cli('run', state['experiment'], env={
                'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(value)})
            self.cli('advance-canonical-trial', 'trial', '--meaning-case', case,
                     '--comment', 'Reviewed fixture')
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
        self.assertEqual(len(self.calls()), 4)

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


if __name__ == '__main__':
    unittest.main()
