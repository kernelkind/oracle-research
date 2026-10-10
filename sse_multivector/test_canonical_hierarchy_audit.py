"""Read-only structural audit through the production experiment CLI."""
import json
from pathlib import Path
import unittest

from sse_multivector import test_experiment as fixtures
from sse_multivector import test_canonical_trial as roots_fixtures


class CanonicalHierarchyAuditTests(unittest.TestCase):
    setUp = fixtures.ExperimentTests.setUp
    write = fixtures.ExperimentTests.write
    cli = fixtures.ExperimentTests.cli
    setup_trial = roots_fixtures.CanonicalTrialTests.setup_trial

    def completed_trial(self, second_relation='canonical_contains_local', third_relation='canonical_contains_local', hold_last=False):
        self.setup_trial(schema_version=2)
        for case, value in (
                ('bootstrap', {'meaning': 'Broad fixture topic'}),
                ('C001', {'meaning': 'Narrower fixture topic', 'relation': second_relation,
                          'reason': 'Fixture child'}),
                ('C002', {'meaning': 'Narrowest fixture topic', 'relation': third_relation,
                          'reason': 'Fixture grandchild'})):
            state = json.loads((self.root / 'trial/state.json').read_text())
            self.cli('run', state['experiment'], env={
                'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(value)})
            options = ('--hold', 'Manual fixture review') if hold_last and case == 'C002' else ()
            self.cli('advance-canonical-trial', 'trial', '--meaning-case', case,
                     '--comment', 'Reviewed fixture', *options)

    def test_audit_counts_recursive_notes_and_paths_without_graph_changes(self):
        self.completed_trial()
        path = self.root / 'trial/state.json'
        before = path.read_bytes()
        result = self.cli('audit-canonical-trial', 'trial', '--output', 'audit.json',
                          '--max-choices', '6', '--work-budget', '200000')
        summary = json.loads(result.stdout)
        report = json.loads((self.root / 'audit.json').read_text())
        self.assertEqual(report['metrics']['nodes'], 3)
        self.assertEqual(report['metrics']['edges'], 2)
        self.assertEqual(report['metrics']['roots'], 1)
        self.assertEqual(report['metrics']['equal_note_set_edges'], 0)
        self.assertEqual(report['metrics']['proper_subset_edges'], 2)
        self.assertEqual(report['nodes']['C001']['recursive_notes'], ['n1', 'n2', 'n3'])
        self.assertEqual(report['nodes']['C001']['direct_notes'], ['n1'])
        task = next(t for t in report['individual_tasks'] if t['note_id'] == 'n3')
        self.assertEqual(task['path'], ['C001', 'C002', 'C003'])
        self.assertEqual(task['option_counts'], [1, 1, 1])
        self.assertFalse(summary['done'])
        self.assertFalse(report['semantic_assessment']['graded'])
        self.assertEqual(report['root_menu']['full_corpus_roots'], ['C001'])
        self.assertEqual(report['group_task_coverage']['status'], 'unknown')
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(len(fixtures.ExperimentTests.calls(self)), 4)


    def test_individual_notes_isolate_in_independent_roots_without_semantic_claim(self):
        self.completed_trial(second_relation='neither', third_relation='neither')
        summary = json.loads(self.cli('audit-canonical-trial', 'trial', '--output', 'audit.json').stdout)
        report = json.loads((self.root / 'audit.json').read_text())
        self.assertTrue(summary['structural_constraints_met'])
        self.assertFalse(summary['done'])
        self.assertEqual(report['violations'], [])
        self.assertEqual(report['root_menu']['option_count'], 3)
        self.assertEqual(report['root_menu']['full_corpus_roots'], [])
        self.assertEqual([t['option_counts'] for t in report['individual_tasks']], [[3]] * 3)
        self.assertEqual(report['group_tasks'], [])

    def test_equal_note_set_edge_and_single_note_parent_are_reported(self):
        self.setup_trial(schema_version=2, root_order=[{'note_id': 'n1', 'number': '1'}])
        state = json.loads((self.root / 'trial/state.json').read_text())
        self.cli('run', state['experiment'], env={
            'FAKE_RUNNER_PROMPT_RESPONSE': '{"meaning": "Original canonical meaning"}'})
        self.cli('advance-canonical-trial', 'trial', '--meaning-case', 'bootstrap', '--comment', 'Reviewed')
        self.cli('prepare-canonical-child-trial', 'children', '--base-trial', 'trial')
        state = json.loads((self.root / 'children/state.json').read_text())
        self.cli('run', state['experiment'], env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps({
            'meaning': 'Narrower same-note meaning', 'relation': 'canonical_contains_local',
            'reason': 'Mapped-parent fixture'})})
        self.cli('advance-canonical-trial', 'children', '--meaning-case', 'C001', '--comment', 'Reviewed')
        self.cli('audit-canonical-trial', 'children', '--output', 'audit.json')
        report = json.loads((self.root / 'audit.json').read_text())
        self.assertEqual(report['metrics']['equal_note_set_edges'], 1)
        self.assertEqual(report['nodes']['C001']['recursive_notes'], ['n1'])
        self.assertEqual({v['kind'] for v in report['violations']},
                         {'equal_note_set_edge', 'single_note_parent'})

    def test_multiple_parent_shortest_path_and_child_choice_limit(self):
        self.completed_trial(second_relation='neither')
        self.cli('audit-canonical-trial', 'trial', '--output', 'audit.json', '--max-choices', '1')
        report = json.loads((self.root / 'audit.json').read_text())
        task = next(t for t in report['individual_tasks'] if t['note_id'] == 'n3')
        self.assertEqual(task['path'], ['C001', 'C003'])
        self.assertEqual(task['option_counts'], [2, 1])
        self.assertEqual(task['status'], 'exceeds_choice_limit')
        self.assertIn('too_many_roots', {v['kind'] for v in report['violations']})

    def test_child_menu_choice_limit_is_reported(self):
        self.setup_trial(schema_version=2)
        for case, value in (
                ('bootstrap', {'meaning': 'Broad fixture topic'}),
                ('C001', {'meaning': 'First child', 'relation': 'canonical_contains_local',
                          'reason': 'Fixture child'})):
            state = json.loads((self.root / 'trial/state.json').read_text())
            self.cli('run', state['experiment'], env={
                'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(value)})
            self.cli('advance-canonical-trial', 'trial', '--meaning-case', case, '--comment', 'Reviewed')
        state = json.loads((self.root / 'trial/state.json').read_text())
        self.cli('run', state['experiment'], '--max-new-attempts', '1', ok=False, env={
            'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps({'meaning': 'Second child',
            'relation': 'canonical_contains_local', 'reason': 'Broad parent contains child'})})
        self.cli('run', state['experiment'], env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps({
            'meaning': 'Second child', 'relation': 'neither', 'reason': 'Separate siblings'})})
        self.cli('advance-canonical-trial', 'trial', '--meaning-case', 'C001', '--comment', 'Reviewed')
        self.cli('audit-canonical-trial', 'trial', '--output', 'audit.json', '--max-choices', '1')
        report = json.loads((self.root / 'audit.json').read_text())
        self.assertEqual(report['metrics']['roots'], 1)
        self.assertEqual(report['metrics']['max_children'], 2)
        self.assertIn({'kind': 'too_many_children', 'node': 'C001', 'count': 2}, report['violations'])

    def test_missing_selected_note_is_reported_without_semantic_grading(self):
        self.completed_trial(hold_last=True)
        self.cli('audit-canonical-trial', 'trial', '--output', 'audit.json')
        report = json.loads((self.root / 'audit.json').read_text())
        self.assertEqual(report['note_coverage']['missing'], ['n3'])
        self.assertIn({'kind': 'unreachable_notes', 'note_ids': ['n3']}, report['violations'])
        self.assertFalse(report['structural_constraints_met'])

    def test_equal_note_sets_retain_distinct_named_topic_tasks(self):
        self.setup_trial(schema_version=2, root_order=[
            {'note_id': 'n1', 'number': '1'}, {'note_id': 'n2', 'number': '2'}])
        corpus = json.loads((self.root / 'notes.json').read_text())
        corpus['notes'][1]['subjects'].append({'number': '2.1', 'subject': 'Related child',
                                              'context': 'Narrower role'})
        self.write('notes.json', corpus)
        self.cli('prepare-canonical-trial', 'base', '--spec', 'trial.json')
        for case, answer in (
                ('bootstrap', {'meaning': 'Broad cooking role'}),
                ('C001', {'meaning': 'Same broad role', 'relation': 'equivalent', 'reason': 'Same topic'})):
            state = json.loads((self.root / 'base/state.json').read_text())
            self.cli('run', state['experiment'], env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(answer)})
            self.cli('advance-canonical-trial', 'base', '--meaning-case', case, '--comment', 'Reviewed')
        self.cli('prepare-canonical-child-trial', 'children', '--base-trial', 'base')
        state = json.loads((self.root / 'children/state.json').read_text())
        self.cli('run', state['experiment'], env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps({
            'meaning': 'Particular cooking role', 'relation': 'canonical_contains_local',
            'reason': 'Narrower role'})})
        self.cli('advance-canonical-trial', 'children', '--meaning-case', 'C001', '--comment', 'Reviewed')
        state = json.loads((self.root / 'children/state.json').read_text())
        self.cli('run', state['experiment'], '--max-new-attempts', '1', ok=False, env={
            'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps({'meaning': 'Same particular role',
            'relation': 'canonical_contains_local', 'reason': 'Broad parent contains role'})})
        self.cli('run', state['experiment'], env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps({
            'meaning': 'Same particular role', 'relation': 'equivalent', 'reason': 'Same narrower role'})})
        self.cli('advance-canonical-trial', 'children', '--meaning-case', 'C003', '--comment', 'Reviewed')
        self.cli('audit-canonical-trial', 'children', '--output', 'audit.json')
        report = json.loads((self.root / 'audit.json').read_text())
        self.assertEqual(len(report['group_tasks']), 1)
        tasks = {t['id']: t for t in report['topic_group_tasks']}
        self.assertEqual(set(tasks), {'C001', 'C003'})
        self.assertEqual(tasks['C001']['meaning'], 'Broad cooking role')
        self.assertEqual(tasks['C003']['meaning'], 'Particular cooking role')
        self.assertEqual(tasks['C001']['note_ids'], tasks['C003']['note_ids'])
        self.assertEqual(tasks['C001']['path'], ['C001'])
        self.assertEqual(tasks['C003']['path'], ['C001', 'C003'])

    def test_work_overflow_and_existing_output_are_rejected_without_source_writes(self):
        self.completed_trial()
        path = self.root / 'trial/state.json'
        before = path.read_bytes()
        result = self.cli('audit-canonical-trial', 'trial', '--output', 'budget.json',
                          '--work-budget', '1', ok=False)
        self.assertIn('work budget exceeded', result.stderr)
        self.assertFalse((self.root / 'budget.json').exists())
        existing = self.root / 'existing.json'
        existing.write_text('Preserve this report')
        self.cli('audit-canonical-trial', 'trial', '--output', existing, ok=False)
        self.assertEqual(existing.read_text(), 'Preserve this report')
        self.assertEqual(path.read_bytes(), before)

    def test_changed_source_and_cycles_are_rejected_without_report(self):
        self.completed_trial()
        corpus = self.root / 'notes.json'
        before = corpus.read_bytes()
        corpus.write_bytes(before + b'\n')
        result = self.cli('audit-canonical-trial', 'trial', '--output', 'changed.json', ok=False)
        self.assertIn('trial source changed', result.stderr)
        self.assertFalse((self.root / 'changed.json').exists())
        corpus.write_bytes(before)
        state_path = self.root / 'trial/state.json'
        state = json.loads(state_path.read_text())
        state['nodes'][0]['parents'] = ['C003']
        state_path.write_text(json.dumps(state))
        result = self.cli('audit-canonical-trial', 'trial', '--output', 'cyclic.json', ok=False)
        self.assertIn('contains a cycle', result.stderr)
        self.assertFalse((self.root / 'cyclic.json').exists())


if __name__ == '__main__':
    unittest.main()
