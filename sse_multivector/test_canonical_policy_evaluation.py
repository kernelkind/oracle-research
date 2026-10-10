"""Policy accounting and graph quality through the native production CLI."""
import json
import unittest

from sse_multivector import test_canonical_continuation as fixtures


class CanonicalPolicyEvaluationTests(unittest.TestCase):
    setUp = fixtures.CanonicalContinuationTests.setUp
    write = fixtures.CanonicalContinuationTests.write
    cli = fixtures.CanonicalContinuationTests.cli
    calls = fixtures.CanonicalContinuationTests.calls
    setup_trial = fixtures.CanonicalContinuationTests.setup_trial
    state = fixtures.CanonicalContinuationTests.state
    dynamic_runner = fixtures.CanonicalContinuationTests.dynamic_runner
    shared = fixtures.CanonicalContinuationTests.shared
    continue_trial = fixtures.CanonicalContinuationTests.continue_trial

    def comparison_trials(self, *, baseline_failure=False, candidate_hold=False,
                          candidate_incomplete=False, retain_child=False, known_cost=False,
                          legacy_answer_status=False):
        self.dynamic_runner()
        self.setup_trial(schema_version=2, independent_meanings=True)
        self.shared()
        env = {'FAKE_RUNNER_RESULT_OVERRIDE': json.dumps({'usage': {
            'input': 11, 'cacheRead': 7, 'cacheWrite': 0, 'output': 5, 'reasoning': 3,
            **({'cost': {'total': 0.125}} if known_cost else {})}}),
            'FIXTURE_RELATIONS': json.dumps({'EXCLUDED CHILD': {'C001': 'canonical_contains_local'}})}
        self.continue_trial(attempts=6, env=env)
        if legacy_answer_status:
            state = json.loads((self.root / 'trial/state.json').read_text())
            del state['steps'][0]['answers'][0]['status']
            self.write('trial/state.json', state)
        for name in ('baseline', 'candidate'):
            self.cli('prepare-canonical-child-trial', name, '--base-trial', 'trial')
            if name == 'candidate' and candidate_incomplete:
                continue
            if name == 'baseline' and baseline_failure or name == 'candidate' and candidate_hold:
                pending = json.loads((self.root / name / 'state.json').read_text())
                self.cli('run', pending['experiment'], env=env)
                self.cli('advance-canonical-trial', name, '--meaning-case', 'bootstrap',
                         '--comment', 'Reviewed fixed fixture meaning')
                pending = json.loads((self.root / name / 'state.json').read_text())
                if baseline_failure:
                    self.cli('run', pending['experiment'], ok=False,
                             env={'FAKE_RUNNER_FAIL_STAGE': 'prompt'})
                    self.continue_trial(directory=name, nodes=4, attempts=4, env=env)
                else:
                    self.cli('run', pending['experiment'], env=env)
                    self.cli('advance-canonical-trial', name, '--meaning-case', 'C001',
                        '--hold', 'Fixture manual hold preserves previous graph',
                        '--comment', 'Reviewed hold, not an inferred negative')
            else:
                self.continue_trial(directory=name, nodes=4, attempts=4, env=env)
            if name == 'candidate' and candidate_hold:
                continue
            self.write(name + '-shape.json', {'schema_version': 1, 'trial': name,
                'roots': ['C004' if retain_child else 'C001', 'C002', 'C003'], 'children': {}})
            self.cli('shape-canonical-trial', '--source', name + '-shape.json',
                     '--output', name + '-menu')
        source = {'schema_version': 1, 'base_trial': 'trial',
            'baseline': 'baseline', 'candidate': 'candidate',
            'baseline_menu': 'baseline-menu'}
        if not candidate_hold and not candidate_incomplete:
            source['candidate_menu'] = 'candidate-menu'
        self.write('evaluation.json', source)

    def evaluate(self, output='evaluation-report.json', **kwargs):
        return self.cli('evaluate-canonical-policy-trial', '--source', 'evaluation.json',
                        '--output', output, **kwargs)

    def select_checkpoint_only(self, schema_version=2):
        # A valid selective schedule may need no suffix entries. The finished
        # menu still originates from its own exact, native raw checkpoint.
        self.write('checkpoint-shape.json', {'schema_version': 1, 'trial': 'trial',
            'roots': ['C001', 'C002', 'C003'], 'children': {}})
        self.cli('shape-canonical-trial', '--source', 'checkpoint-shape.json',
                 '--output', 'checkpoint-menu')
        source = json.loads((self.root / 'evaluation.json').read_text())
        source.update(schema_version=schema_version, candidate='trial',
                      candidate_menu='checkpoint-menu')
        self.write('evaluation.json', source)

    def test_selective_schedule_uses_native_checkpoint_and_reports_complete_catalog_cost(self):
        self.comparison_trials(known_cost=True)
        self.select_checkpoint_only()
        before = len(self.calls())
        self.evaluate()
        report = json.loads((self.root / 'evaluation-report.json').read_text())
        self.assertFalse(report['schedule']['matched'])
        self.assertEqual(report['schedule']['baseline_scheduled_entries'], 1)
        self.assertEqual(report['schedule']['candidate_scheduled_entries'], 0)
        self.assertTrue(report['quality']['preserved'])
        self.assertAlmostEqual(report['baseline']['generation_usage']['catalog_cost_estimate_usd'], 0.5)
        self.assertEqual(report['candidate']['generation_usage']['catalog_cost_estimate_usd'], 0)
        self.assertEqual(report['reductions']['catalog_cost_estimate_percent'], 100)
        self.assertEqual(report['decision_changes'][0]['local'],
                         json.loads((self.root / 'baseline/state.json').read_text())['steps'][-1]['local'])
        self.assertIsNone(report['decision_changes'][0]['candidate'])
        self.assertEqual(len(self.calls()), before)

    def test_selective_schedule_keeps_missing_catalog_cost_unknown(self):
        self.comparison_trials()
        self.select_checkpoint_only()
        self.evaluate()
        report = json.loads((self.root / 'evaluation-report.json').read_text())
        self.assertIsNone(report['baseline']['generation_usage']['catalog_cost_estimate_usd'])
        self.assertIsNone(report['reductions']['catalog_cost_estimate_percent'])
        self.assertIsNone(report['whole_construction']['reductions']['catalog_cost_estimate_percent'])

    def test_independent_complete_constructions_compare_without_shared_checkpoint(self):
        self.comparison_trials(known_cost=True)
        cfg = json.loads((self.root / 'trial.json').read_text())
        cfg.pop('note_ids')
        cfg['roots'] = [{'note_id': 'n3', 'number': '3'},
                        {'note_id': 'n2', 'number': '2'},
                        {'note_id': 'n1', 'number': '1'}]
        (self.root / 'independent-prompt.txt').write_text(self.prompt.read_text())
        for field in ('bootstrap_spec', 'comparison_spec'):
            spec = json.loads((self.root / cfg[field]).read_text())
            spec['prompt']['path'] = 'independent-prompt.txt'
            copied = 'independent-' + cfg[field]
            self.write(copied, spec)
            cfg[field] = copied
        self.write('independent.json', cfg)
        self.cli('prepare-canonical-trial', 'independent', '--spec', 'independent.json')
        self.continue_trial(directory='independent', attempts=6, env={
            'FAKE_RUNNER_RESULT_OVERRIDE': json.dumps({'usage': {
                'input': 11, 'cacheRead': 7, 'cacheWrite': 0, 'output': 5,
                'cost': {'total': 0.125}}})})
        self.write('independent-shape.json', {'schema_version': 1, 'trial': 'independent',
                                            'roots': ['C001', 'C002', 'C003'], 'children': {}})
        self.cli('shape-canonical-trial', '--source', 'independent-shape.json',
                 '--output', 'independent-menu')
        self.write('evaluation.json', {'schema_version': 3, 'baseline': 'baseline',
            'candidate': 'independent', 'baseline_menu': 'baseline-menu',
            'candidate_menu': 'independent-menu'})
        before = len(self.calls())
        self.evaluate()
        report = json.loads((self.root / 'evaluation-report.json').read_text())
        self.assertTrue(report['quality']['preserved'])
        self.assertEqual(report['schedule']['checkpoint_index'], 0)
        self.assertFalse(report['schedule']['matched'])
        self.assertEqual(report['whole_construction']['baseline']['generation_usage']['original_calls'], 10)
        self.assertEqual(report['whole_construction']['candidate']['generation_usage']['original_calls'], 6)
        self.assertAlmostEqual(report['whole_construction']['reductions']['catalog_cost_estimate_percent'], 40)
        self.assertEqual(len(self.calls()), before)

    def test_whole_construction_retains_shared_checkpoint_cost_and_deduplicates_reuse(self):
        self.comparison_trials(known_cost=True)
        self.select_checkpoint_only()
        before = len(self.calls())
        self.evaluate()
        report = json.loads((self.root / 'evaluation-report.json').read_text())
        whole = report['whole_construction']
        self.assertEqual(report['reductions']['catalog_cost_estimate_percent'], 100)
        self.assertEqual(whole['baseline']['generation_usage']['original_calls'], 10)
        self.assertEqual(whole['candidate']['generation_usage']['original_calls'], 6)
        self.assertAlmostEqual(whole['baseline']['generation_usage']['catalog_cost_estimate_usd'], 1.25)
        self.assertAlmostEqual(whole['candidate']['generation_usage']['catalog_cost_estimate_usd'], 0.75)
        self.assertAlmostEqual(whole['reductions']['catalog_cost_estimate_percent'], 40)
        self.assertEqual(whole['candidate']['actual_usage']['catalog_cost_estimate_usd'], 0.75)
        self.assertEqual(len(self.calls()), before)

    def test_legacy_checkpoint_answer_status_is_recovered_from_verified_receipt(self):
        self.comparison_trials(known_cost=True, legacy_answer_status=True)
        self.select_checkpoint_only()
        before = len(self.calls())
        self.evaluate()
        report = json.loads((self.root / 'evaluation-report.json').read_text())
        self.assertTrue(report['quality']['preserved'])
        self.assertEqual(report['whole_construction']['baseline']['generation_usage']['original_calls'], 10)
        self.assertEqual(len(self.calls()), before)

    def test_whole_construction_validates_older_native_checkpoint_receipts(self):
        self.dynamic_runner()
        self.setup_trial(schema_version=2, independent_meanings=True,
                         root_order=[{'note_id': 'n1', 'number': '1'}])
        self.shared()
        env = {'FAKE_RUNNER_RESULT_OVERRIDE': json.dumps({'usage': {
            'input': 11, 'output': 5, 'cost': {'total': 0.125}}}),
            'FIXTURE_RELATIONS': json.dumps({'EXCLUDED CHILD': {'C001': 'canonical_contains_local'}})}
        self.continue_trial(nodes=1, attempts=1, env=env)
        (self.root / 'current-prompt.txt').write_text('GENERIC PROMPT {INPUT_JSON}\n')
        for name in ('bootstrap', 'comparison'):
            spec = json.loads((self.root / (name + '.json')).read_text())
            spec['prompt'] = {'id': 'CurrentPrompt', 'path': 'current-prompt.txt'}
            self.write('current-' + name + '.json', spec)
        self.write('current-trial.json', {'schema_version': 2, 'corpus': 'notes.json',
            'roots': [{'note_id': 'n2', 'number': '2'}], 'independent_meanings': True,
            'bootstrap_spec': 'current-bootstrap.json', 'comparison_spec': 'current-comparison.json'})
        self.cli('prepare-canonical-trial', 'current', '--spec', 'current-trial.json',
                 '--base-trial', 'trial')
        self.continue_trial(directory='current', nodes=1, attempts=2, env=env)
        self.cli('prepare-canonical-child-trial', 'baseline', '--base-trial', 'current')
        self.continue_trial(directory='baseline', nodes=1, attempts=3, env=env)
        for name, raw in (('baseline-menu', 'baseline'), ('candidate-menu', 'current')):
            self.write(name + '-shape.json', {'schema_version': 1, 'trial': raw,
                'roots': ['C001', 'C002'], 'children': {}})
            self.cli('shape-canonical-trial', '--source', name + '-shape.json', '--output', name)
        self.write('evaluation.json', {'schema_version': 2, 'base_trial': 'current',
            'baseline': 'baseline', 'candidate': 'current',
            'baseline_menu': 'baseline-menu', 'candidate_menu': 'candidate-menu'})
        before = len(self.calls())
        self.evaluate()
        report = json.loads((self.root / 'evaluation-report.json').read_text())
        self.assertTrue(report['quality']['preserved'])
        self.assertAlmostEqual(report['whole_construction']['baseline']['generation_usage']
                               ['catalog_cost_estimate_usd'], 0.75)
        self.assertAlmostEqual(report['whole_construction']['candidate']['generation_usage']
                               ['catalog_cost_estimate_usd'], 0.375)
        self.assertEqual(report['whole_construction']['reductions']['catalog_cost_estimate_percent'], 50)
        self.assertEqual(len(self.calls()), before)

    def test_legacy_source_still_rejects_unequal_schedules(self):
        self.comparison_trials()
        self.select_checkpoint_only(schema_version=1)
        result = self.evaluate(ok=False)
        self.assertIn('preserve checkpoint and scheduled suffix', result.stderr)
        self.assertFalse((self.root / 'evaluation-report.json').exists())

    def test_selective_schedule_rejects_changed_settings_unknown_and_repeated_locals(self):
        self.comparison_trials()
        source = json.loads((self.root / 'evaluation.json').read_text())
        source['schema_version'] = 2
        self.write('evaluation.json', source)
        original = json.loads((self.root / 'candidate/state.json').read_text())
        for kind in ('settings', 'unknown', 'duplicate'):
            state = json.loads(json.dumps(original))
            if kind == 'settings':
                state['comparison_spec']['runner']['reasoning'] = 'high'
                expected = 'prompt and inference settings'
            else:
                state.pop('queue', None)
                if kind == 'unknown':
                    state['children'][-1]['local'] = {'note_id': 'n1', 'number': '404'}
                    state['steps'][-1]['local'] = state['children'][-1]['local']
                else:
                    state['children'].append(state['children'][-1])
                expected = 'unique original entries'
            self.write('candidate/state.json', state)
            result = self.evaluate(kind + '.json', ok=False)
            self.assertIn(expected, result.stderr)
            self.assertFalse((self.root / (kind + '.json')).exists())
        self.write('candidate/state.json', original)

    def test_reused_judgments_are_not_reported_as_policy_token_savings(self):
        self.comparison_trials()
        before = len(self.calls())
        self.evaluate(env={'FAKE_RUNNER_FAIL_STAGE': 'prompt'})
        report = json.loads((self.root / 'evaluation-report.json').read_text())
        self.assertEqual(report['inference_calls'], 0)
        self.assertTrue(report['schedule']['matched'])
        self.assertEqual(report['schedule']['scheduled_entries'], 1)
        self.assertEqual(report['reductions']['comparison_requests_percent'], 0)
        self.assertEqual(report['reductions']['total_tokens_percent'], 0)
        self.assertEqual(report['baseline']['generation_usage']['total_tokens'], 92)
        self.assertEqual(report['candidate']['generation_usage']['total_tokens'], 92)
        self.assertEqual(report['candidate']['actual_usage']['total_tokens'], 0)
        self.assertTrue(report['quality']['preserved'])
        self.assertEqual(len(self.calls()), before)

    def test_unknown_failed_usage_does_not_become_zero_or_full_token_reduction(self):
        self.comparison_trials(baseline_failure=True)
        before = len(self.calls())
        self.evaluate()
        report = json.loads((self.root / 'evaluation-report.json').read_text())
        self.assertFalse(report['baseline']['generation_usage']['usage_complete'])
        self.assertEqual(report['baseline']['generation_usage']['attempts_without_usage'], 3)
        self.assertEqual(report['baseline']['generation_usage']['total_tokens'], 23)
        self.assertIsNone(report['reductions']['total_tokens_percent'])
        self.assertIsNone(report['reductions']['comparison_tokens_percent'])
        self.assertTrue(any('missing failed usage' in warning for warning in report['warnings']))
        if report['baseline']['prepared_inputs']['tokenizer']:
            self.assertEqual(report['reductions']['rendered_input_tokens_percent'], 0)
            self.assertGreater(report['baseline']['prepared_inputs']['rendered_input_tokens'], 0)
        self.assertEqual(len(self.calls()), before)

    def test_missing_baseline_shape_node_reports_quality_failure_and_usage(self):
        self.comparison_trials(candidate_hold=True, retain_child=True)
        before = len(self.calls())
        self.evaluate()
        report = json.loads((self.root / 'evaluation-report.json').read_text())
        self.assertFalse(report['quality']['preserved'])
        self.assertIn('unknown canonical shape node', report['quality']['shape_error'])
        self.assertEqual(report['baseline']['generation_usage']['total_tokens'], 92)
        self.assertEqual(report['candidate']['generation_usage']['total_tokens'], 92)
        self.assertEqual(len(self.calls()), before)

    def test_incomplete_trial_retains_pending_input_and_defers_reduction_claim(self):
        self.comparison_trials(candidate_incomplete=True)
        before = len(self.calls())
        self.evaluate()
        report = json.loads((self.root / 'evaluation-report.json').read_text())
        self.assertFalse(report['schedule']['candidate_complete'])
        self.assertFalse(report['quality']['preserved'])
        self.assertEqual(report['candidate']['kinds']['meanings']['unrun'], 1)
        self.assertTrue(all(value is None for value in report['reductions'].values()))
        self.assertEqual(len(self.calls()), before)

    def test_pending_verification_keeps_earlier_shortlist_and_meaning_usage(self):
        from sse_multivector.test_canonical_comparison_policy import CanonicalComparisonPolicyTests
        CanonicalComparisonPolicyTests.completed_base(self)
        env = {'FAKE_RUNNER_RESULT_OVERRIDE': json.dumps({'usage': {
            'input': 11, 'cacheRead': 7, 'output': 5}}),
            'FIXTURE_RELATIONS': json.dumps({'Baby potatoes': {
                'C001': 'canonical_contains_local', 'C002': 'canonical_contains_local'}})}
        self.cli('prepare-canonical-child-trial', 'baseline', '--base-trial', 'trial')
        self.continue_trial(directory='baseline', nodes=3, attempts=3, env=env)
        self.write('baseline-shape.json', {'schema_version': 1, 'trial': 'baseline',
            'roots': ['C001', 'C002'], 'children': {}})
        self.cli('shape-canonical-trial', '--source', 'baseline-shape.json', '--output', 'baseline-menu')
        self.cli('prepare-canonical-child-trial', 'candidate', '--base-trial', 'trial',
                 '--comparison-policy', 'policy.json')
        for case in ('bootstrap', 'C002'):
            state = json.loads((self.root / 'candidate/state.json').read_text())
            self.cli('run', state['experiment'], env=env)
            self.cli('advance-canonical-trial', 'candidate', '--meaning-case', case,
                     '--comment', 'Check bound fixture phase before verification')
        self.write('evaluation.json', {'schema_version': 1, 'base_trial': 'trial',
            'baseline': 'baseline', 'candidate': 'candidate', 'baseline_menu': 'baseline-menu'})
        before = len(self.calls())
        self.evaluate()
        report = json.loads((self.root / 'evaluation-report.json').read_text())
        self.assertEqual(report['candidate']['kinds']['comparisons']['cases'], 2)
        self.assertEqual(report['candidate']['kinds']['comparisons']['unrun'], 1)
        self.assertEqual(report['candidate']['kinds']['meanings']['cases'], 1)
        self.assertEqual(report['candidate']['generation_usage']['total_tokens'], 46)
        self.assertEqual(report['candidate']['actual_usage']['total_tokens'], 0)
        self.assertIsNone(report['reductions']['total_tokens_percent'])
        self.assertEqual(len(self.calls()), before)

    def test_changed_receipt_and_checkpoint_are_rejected_and_output_is_not_overwritten(self):
        self.comparison_trials()
        self.evaluate()
        original = (self.root / 'evaluation-report.json').read_bytes()
        result = self.evaluate(ok=False)
        self.assertIn('output already exists', result.stderr)
        self.assertEqual((self.root / 'evaluation-report.json').read_bytes(), original)
        state = json.loads((self.root / 'candidate/state.json').read_text())
        state['steps'][-1]['answers'][0]['output']['relation'] = 'equivalent'
        self.write('candidate/state.json', state)
        result = self.evaluate('changed.json', ok=False)
        self.assertIn('differs from validated native receipt', result.stderr)
        self.assertFalse((self.root / 'changed.json').exists())
        state['steps'][0]['selected_meaning'] = 'Changed checkpoint'
        self.write('candidate/state.json', state)
        result = self.evaluate('changed-checkpoint.json', ok=False)
        self.assertIn('preserve checkpoint and scheduled suffix', result.stderr)
