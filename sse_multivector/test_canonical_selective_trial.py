"""Selective preparation through the production CLI and native saved receipts."""
import hashlib
import json
from pathlib import Path
import unittest

from sse_multivector import test_canonical_continuation as fixtures


class CanonicalSelectiveTrialTests(unittest.TestCase):
    setUp = fixtures.CanonicalContinuationTests.setUp
    write = fixtures.CanonicalContinuationTests.write
    cli = fixtures.CanonicalContinuationTests.cli
    calls = fixtures.CanonicalContinuationTests.calls
    dynamic_runner = fixtures.CanonicalContinuationTests.dynamic_runner
    shared = fixtures.CanonicalContinuationTests.shared
    continue_trial = fixtures.CanonicalContinuationTests.continue_trial

    def state(self, directory='trial'):
        return json.loads((self.root / directory / 'state.json').read_text())

    def setup_completed_roots(self, *, extra_subjects=(), root_relations=None):
        # Replace only the transport. Source preparation, receipts, fixed
        # meanings, graph transitions and comparison inputs use production code.
        self.dynamic_runner()
        self.prompt.write_text('GENERIC PROMPT {INPUT_JSON}')
        self.write('notes.json', {'schema_version': 1, 'notes': [
            {'note_id': 'stock', 'text': 'Chicken stock is cooked in stock pots, '
             'then pressure-canned for storage in the pantry.', 'subjects': [
                 {'number': '3', 'subject': 'Cookware', 'context': 'Stock pots cook the stock.'},
                 {'number': '3.1', 'subject': 'Stock pots', 'context': 'The stock cooks in stock pots.'},
                 {'number': '8', 'subject': 'Food storage', 'context': 'The stock will be stored.'},
                 {'number': '8.1', 'subject': 'Pantry food storage', 'context': 'The stock will be stored in the pantry.'},
                 *extra_subjects]},
            {'note_id': 'beets', 'text': 'Garden-grown beets are vacuum-sealed and '
             'ready for freezer storage.', 'subjects': [
                 {'number': '2', 'subject': 'Garden harvests', 'context': 'Beets are prepared for freezer storage.'}]},
            {'note_id': 'ware', 'text': 'A cookware collection contains cast iron '
             'cocottes and frying pans.', 'subjects': [
                 {'number': '3', 'subject': 'Cookware', 'context': 'The collection contains cooking vessels.'},
                 {'number': '3.1', 'subject': 'Cast iron cookware', 'context': 'The vessels are cast iron.'}]}]})
        base = json.loads(self.spec.read_text())
        schemas = Path(__file__).with_name('shr_single_pair')
        for name, schema in [('bootstrap', 'Hierarchy-bootstrap-v1.output.schema.json'),
                             ('comparison', 'Hierarchy-compare-v4.output.schema.json')]:
            self.write(name + '.json', {**base, 'runner': {**base['runner'],
                       'output_schema': json.loads((schemas / schema).read_text())}})
        self.write('trial.json', dict(schema_version=2, corpus='notes.json',
                   roots=[dict(note_id='stock', number='8'),
                          dict(note_id='beets', number='2'),
                          dict(note_id='ware', number='3')],
                   bootstrap_spec='bootstrap.json', comparison_spec='comparison.json',
                   independent_meanings=True))
        self.relations = {
            'Garden harvests': {'C001': 'canonical_contains_local'},
            'Pantry food storage': {'C001': 'canonical_contains_local'},
            'Cookware': {'C003': 'equivalent'},
            'Stock pots': {'C003': 'canonical_contains_local'},
            'Cast iron cookware': {'C003': 'canonical_contains_local'}}
        self.cli('prepare-canonical-trial', 'trial', '--spec', 'trial.json')
        self.shared(limit=1000)
        self.finish('trial', nodes=3, relations=root_relations)
        self.write('selection-spec.json', dict(schema_version=1, max_choices=6,
                   max_entries=12, canonical_limit=16, local_candidate_limit=32,
                   topic_groups=[
                       dict(local=dict(note_id='stock', number='8'), note_ids=['stock', 'beets']),
                       dict(local=dict(note_id='ware', number='3'), note_ids=['stock', 'ware'])]))

    def finish(self, directory, nodes=1, *, relations=None):
        return self.continue_trial(directory=directory, nodes=nodes, attempts=40,
                                   env={'FIXTURE_RELATIONS': json.dumps(
                                       self.relations if relations is None else relations)})

    def select(self, directory, base='trial', **kwargs):
        return self.cli('prepare-canonical-selection-trial', directory,
                        '--base-trial', base, '--spec', 'selection-spec.json', **kwargs)

    def selected(self, directory):
        return self.state(directory)['queue'][-1]

    def discovery_spec(self, *, max_entries=12, policy_limit=16):
        self.write('policy.json', dict(schema_version=1, limit=policy_limit))
        self.write('selection-spec.json', dict(schema_version=2, max_choices=6,
                   max_entries=max_entries, local_candidate_limit=32,
                   comparison_policy='policy.json'))

    def test_singleton_roots_do_not_end_answer_free_discovery(self):
        self.setup_completed_roots(root_relations={})
        self.discovery_spec()
        before = (self.root / 'trial/state.json').read_bytes()
        calls = self.calls()
        result = json.loads(self.select('discover').stdout)
        self.assertEqual(result['selection']['problem']['kind'], 'discovery')
        self.assertEqual(result['selection']['tasks']['topic_groups'], [])
        self.assertEqual(result['selection']['tasks']['not_isolated'], [])
        self.assertEqual(result['selection']['status'], 'selected')
        self.assertTrue('.' in self.selected('discover')['local']['number']
                        or self.selected('discover')['local']['number'] == '3')
        self.assertEqual((self.root / 'trial/state.json').read_bytes(), before)
        self.assertEqual(self.calls(), calls)

    def test_discovery_scans_4096_original_entries_without_truncation_or_inference(self):
        extras = [dict(number=f'8.{index}', subject=f'Storage topic {index}',
                       context='Stock stored for later use.') for index in range(2, 4091)]
        self.setup_completed_roots(root_relations={}, extra_subjects=extras)
        self.discovery_spec()
        before = (self.root / 'trial/state.json').read_bytes()
        calls = self.calls()
        self.select('discover')
        report = json.loads((self.root / 'discover/selection.json').read_text())
        self.assertEqual(report['status'], 'selected')
        self.assertEqual(report['remaining_entries'], 4093)
        self.assertGreater(max(len(row['text_scores']) for row in report['ranking']), 512)
        self.assertLessEqual(len(report['nominees']), 32)
        self.assertEqual(self.state('discover')['nodes'], self.state()['nodes'])
        self.assertEqual((self.root / 'trial/state.json').read_bytes(), before)
        self.assertEqual(self.calls(), calls)

    def test_discovery_moves_to_next_topic_when_each_entry_adds_a_node(self):
        self.setup_completed_roots(root_relations={}, extra_subjects=[
            dict(number='8.2', subject='Additional food storage', context='Stock stored for later use.')])
        self.discovery_spec()
        self.select('first')
        first = json.loads((self.root / 'first/selection.json').read_text())
        self.assertEqual(first['ranking'][0]['query_canonical_id'], 'C001')
        self.finish('first')
        self.assertEqual(len(self.state('first')['nodes']), 4)
        self.select('second', base='first')
        second = json.loads((self.root / 'second/selection.json').read_text())
        self.assertEqual(second['ranking'][0]['query_canonical_id'], 'C002')

    def test_raw_child_count_does_not_reject_a_useful_shared_group(self):
        extras = [dict(number=f'8.{index}', subject=f'Storage topic {index}',
                       context='Stock stored for later use.') for index in range(2, 8)]
        self.setup_completed_roots(root_relations={}, extra_subjects=extras)
        self.cli('prepare-canonical-child-trial', 'crowded', '--base-trial', 'trial')
        relations = dict(self.relations)
        relations.update({row['subject']: {'C001': 'canonical_contains_local'} for row in extras})
        self.finish('crowded', nodes=8, relations=relations)
        self.discovery_spec(max_entries=16)
        self.select('discover', base='crowded')
        report = json.loads((self.root / 'discover/selection.json').read_text())
        self.assertTrue(report['tasks']['overcrowded'])
        self.assertEqual(report['problem']['kind'], 'discovery')
        nodes = self.state('discover')['nodes']
        relations['Cookware'] = {node['id']: (
            'equivalent' if node['subject'] == 'Cookware' else 'local_contains_canonical')
            for node in nodes if node['subject'] in ('Cookware', 'Cast iron cookware')}
        self.finish('discover', relations=relations)
        cookware = next(node for node in self.state('discover')['nodes']
                        if node['subject'] == 'Cookware')
        self.assertEqual({entry['note_id'] for entry in cookware['entries']}, {'stock', 'ware'})

    def test_discovery_uses_guarded_shortlist_and_verifies_omitted_ancestor(self):
        from sse_multivector.test_canonical_comparison_policy import CanonicalComparisonPolicyTests
        CanonicalComparisonPolicyTests.completed_base(self)
        self.discovery_spec(policy_limit=1)
        self.select('discover')
        before = self.state('discover')['nodes']
        result = self.continue_trial(directory='discover', nodes=1, attempts=3,
            env={'FIXTURE_RELATIONS': json.dumps({'Baby potatoes': {
                'C002': 'canonical_contains_local', 'C001': 'neither'}})})
        self.assertEqual(json.loads(result.stdout)['status'], 'complete')
        state = self.state('discover')
        step = state['steps'][-1]
        self.assertEqual(state['nodes'], before)
        self.assertEqual(step['status'], 'held')
        self.assertEqual(step['comparison_selection']['plan']['binding']['eligible'], ['C001', 'C002'])
        self.assertEqual(step['comparison_selection']['plan']['queried'], ['C002'])
        self.assertEqual(len(step['comparison_phases']), 2)

    def test_discovery_budget_reports_unexplored_entries_without_claiming_completion(self):
        self.setup_completed_roots(root_relations={})
        self.discovery_spec(max_entries=3)
        before = self.calls()
        result = json.loads(self.select('limited').stdout)
        self.assertEqual(result['status'], 'entry_limit')
        report = json.loads((self.root / 'limited/selection.json').read_text())
        self.assertEqual(report['remaining_entries'], 4)
        self.assertEqual(report['semantic_review'], 'pending')
        self.assertFalse((self.root / 'limited/state.json').exists())
        self.assertEqual(self.calls(), before)

    def test_discovery_can_establish_unused_anchor_and_share_it_without_declared_memberships(self):
        self.setup_completed_roots(root_relations={})
        self.discovery_spec(max_entries=7)
        base = 'trial'
        selected = []
        for index in range(4):
            directory = f'discovery-{index}'
            self.select(directory, base=base)
            state = self.state(directory)
            selected.append(state['queue'][-1]['local'])
            relations = {}
            for subject in ('Cookware', 'Stock pots', 'Cast iron cookware', 'Pantry food storage'):
                related = {}
                for node in state['nodes']:
                    if subject == 'Cookware' and node['subject'] == 'Cookware':
                        related[node['id']] = 'equivalent'
                    elif subject == 'Cookware' and node['subject'] == 'Cast iron cookware':
                        related[node['id']] = 'local_contains_canonical'
                    elif subject in ('Stock pots', 'Cast iron cookware') and node['subject'] == 'Cookware':
                        related[node['id']] = 'canonical_contains_local'
                    elif subject == 'Pantry food storage' and node['subject'] == 'Food storage':
                        related[node['id']] = 'canonical_contains_local'
                relations[subject] = related
            self.finish(directory, relations=relations)
            base = directory
        self.assertIn(dict(note_id='stock', number='3'), selected)
        self.assertIn(dict(note_id='ware', number='3.1'), selected)
        cookware = next(node for node in self.state(base)['nodes'] if node['subject'] == 'Cookware')
        self.assertEqual({entry['note_id'] for entry in cookware['entries']}, {'stock', 'ware'})
        result = json.loads(self.select('exhausted', base=base).stdout)
        self.assertEqual(result['status'], 'inventory_exhausted')

    def test_discovery_rejects_answer_bearing_config_without_dispatch(self):
        self.setup_completed_roots(root_relations={})
        self.discovery_spec()
        cfg = json.loads((self.root / 'selection-spec.json').read_text())
        self.write('selection-spec.json', dict(cfg, topic_groups=[]))
        before = self.calls()
        result = self.select('refused', ok=False)
        self.assertIn('without expected groups', result.stderr)
        self.assertFalse((self.root / 'refused').exists())
        self.assertEqual(self.calls(), before)

    def test_discovery_explicit_history_reuses_existing_meaning_before_comparison(self):
        self.setup_completed_roots(root_relations={})
        self.discovery_spec()
        cfg = json.loads((self.root / 'selection-spec.json').read_text())
        self.write('selection-spec.json', dict(cfg, history_root='.'))
        self.select('old-scope/discover')
        first = self.state('old-scope/discover')
        self.cli('run', first['experiment'])
        before = self.calls()
        self.select('new-scope/discover')
        state = self.state('new-scope/discover')
        self.assertEqual(state['history_root'], str(self.root))
        manifest = json.loads((Path(state['experiment']) / 'run/manifest.json').read_text())
        self.assertEqual(manifest['request_reuse']['history_root'], str(self.root))
        self.cli('run', state['experiment'], '--max-new-attempts', '1')
        report = json.loads(self.cli('show', state['experiment'], '--json').stdout)
        self.assertTrue(report['cases'][0]['reused'])
        self.assertEqual(self.calls(), before)

    def test_root_history_and_policy_are_preserved_by_discovery_and_child_preparation(self):
        self.setup_completed_roots(root_relations={})
        self.discovery_spec()
        self.cli('prepare-canonical-trial', 'policy-roots', '--spec', 'trial.json',
                 '--history-root', '.', '--comparison-policy', 'policy.json')
        original_policy = self.state('policy-roots')['comparison_policy']
        self.finish('policy-roots', nodes=3, relations={})
        self.select('discover', base='policy-roots')
        selected = self.state('discover')
        self.assertEqual(selected['history_root'], str(self.root))
        self.assertEqual(selected['comparison_policy'], original_policy)
        manifest = json.loads((Path(selected['experiment']) / 'run/manifest.json').read_text())
        self.assertEqual(manifest['request_reuse']['history_root'], str(self.root))
        self.finish('discover')
        self.cli('prepare-canonical-child-trial', 'children', '--base-trial', 'discover')
        child = self.state('children')
        self.assertEqual(child['history_root'], str(self.root))
        self.assertEqual(child['comparison_policy'], original_policy)
        self.assertEqual(child['candidate_selection']['schema_version'], 2)
        manifest = json.loads((Path(child['experiment']) / 'run/manifest.json').read_text())
        self.assertEqual(manifest['request_reuse']['history_root'], str(self.root))

    def test_missing_singleton_selects_immediate_child_without_inference_or_source_changes(self):
        self.setup_completed_roots()
        calls = self.calls()
        original = {p: p.read_bytes() for p in (self.root / 'trial').rglob('*') if p.is_file()}
        self.select('pantry', env={'FAKE_RUNNER_FAIL_STAGE': 'prompt'})
        selected = self.selected('pantry')
        self.assertEqual(selected['local'], dict(note_id='stock', number='8.1'))
        self.assertEqual(selected['mapped_parent'], 'C001')
        self.assertEqual(self.state('pantry')['phase'], 'meaning')
        self.assertEqual(self.state('pantry')['nodes'], self.state()['nodes'])
        self.assertEqual(self.state('pantry')['steps'], self.state()['steps'])
        self.assertTrue((self.root / 'pantry/selection.json').exists())
        spec = self.root / 'selection-spec.json'
        self.assertEqual(self.state('pantry')['sources'][str(spec)],
                         hashlib.sha256(spec.read_bytes()).hexdigest())
        self.assertEqual(self.calls(), calls)
        self.assertEqual({p: p.read_bytes() for p in original}, original)

    def test_unused_stock_entries_fill_group_and_reopen_previously_single_note_branch(self):
        self.setup_completed_roots()
        self.select('pantry')
        self.finish('pantry')
        self.select('stock-cookware', base='pantry')
        selected = self.selected('stock-cookware')
        self.assertEqual(selected['local']['note_id'], 'stock')
        self.assertIn(selected['local']['number'], ('3', '3.1'))
        self.assertIsNone(selected['mapped_parent'])
        self.finish('stock-cookware')
        self.select('cast-iron', base='stock-cookware')
        self.assertEqual(self.selected('cast-iron'), dict(
            local=dict(note_id='ware', number='3.1'), mapped_parent='C003'))
        self.finish('cast-iron')
        self.cli('audit-canonical-trial', 'cast-iron', '--output', 'audit.json')
        audit = json.loads((self.root / 'audit.json').read_text())
        self.assertTrue(audit['structural_constraints_met'])
        self.assertEqual(len(audit['individual_tasks']), 3)
        self.assertTrue(all(t['status'] == 'within_choice_limit'
                            for t in audit['individual_tasks']))
        cookware = audit['nodes']['C003']
        self.assertEqual(cookware['recursive_notes'], ['stock', 'ware'])

    def test_mapped_parent_remains_queried_under_quota_and_existing_guard_holds_rejection(self):
        self.setup_completed_roots()
        cfg = json.loads((self.root / 'selection-spec.json').read_text())
        cfg['canonical_limit'] = 1
        self.write('selection-spec.json', cfg)
        self.select('pantry')
        before = self.state('pantry')['nodes']
        self.cli('run', self.state('pantry')['experiment'])
        self.cli('advance-canonical-trial', 'pantry', '--meaning-case', 'bootstrap',
                 '--comment', 'Validate independent fixture meaning.')
        state = self.state('pantry')
        selection = state['comparison_selections'][str(state['index'])]
        self.assertEqual(selection['queried'], ['C001'])
        self.assertEqual(set(selection['omitted']), {'C002', 'C003'})
        self.assertEqual(selection['mapped_parent'], 'C001')
        batch = json.loads(self.cli('show', state['experiment'], '--json').stdout)
        self.assertEqual([c['id'] for c in batch['cases']], ['C001'])
        # The default offline answer is neither. Preparation must not treat
        # original ancestry as an accepted edge or bypass the mapped-parent guard.
        self.cli('run', state['experiment'])
        self.cli('advance-canonical-trial', 'pantry', '--meaning-case', 'C001',
                 '--comment', 'Exercise rejected mapped-parent comparison.')
        final = self.state('pantry')
        self.assertEqual(final['nodes'], before)
        self.assertEqual(final['steps'][-1]['status'], 'held')
        self.assertIn('mapped canonical parent', final['steps'][-1]['reason'])
        self.assertEqual(final['steps'][-1]['comparison_selection'], selection)

    def test_requirements_met_writes_report_without_new_trial_or_requests(self):
        self.setup_completed_roots()
        self.select('pantry')
        self.finish('pantry')
        self.select('stock-cookware', base='pantry')
        self.finish('stock-cookware')
        self.select('cast-iron', base='stock-cookware')
        self.finish('cast-iron')
        calls = self.calls()
        result = json.loads(self.select('done', base='cast-iron',
                                        env={'FAKE_RUNNER_FAIL_STAGE': 'prompt'}).stdout)
        self.assertEqual(result['status'], 'requirements_met')
        self.assertTrue((self.root / 'done/selection.json').exists())
        self.assertFalse((self.root / 'done/state.json').exists())
        self.assertEqual(list((self.root / 'done').rglob('experiment.json')), [])
        self.assertEqual(self.calls(), calls)

    def test_processed_entry_bound_includes_initial_roots(self):
        self.setup_completed_roots()
        cfg = json.loads((self.root / 'selection-spec.json').read_text())
        cfg['max_entries'] = 3
        self.write('selection-spec.json', cfg)
        calls = self.calls()
        before = (self.root / 'trial/state.json').read_bytes()
        result = json.loads(self.select('limited').stdout)
        self.assertEqual(result['status'], 'entry_limit')
        self.assertFalse((self.root / 'limited/state.json').exists())
        self.assertEqual((self.root / 'trial/state.json').read_bytes(), before)
        self.assertEqual(self.calls(), calls)

    def test_unhelpful_group_root_is_held_then_skipped_parent_child_remains_eligible(self):
        self.setup_completed_roots()
        self.select('pantry')
        self.finish('pantry')
        self.select('unhelpful-root', base='pantry')
        self.assertEqual(self.selected('unhelpful-root'), dict(
            local=dict(note_id='stock', number='3'), mapped_parent=None))
        before = self.state('unhelpful-root')['nodes']
        self.finish('unhelpful-root', relations={})
        held = self.state('unhelpful-root')
        self.assertEqual(held['nodes'], before)
        self.assertEqual(held['steps'][-1]['status'], 'held')
        self.assertIn('does not improve', held['steps'][-1]['reason'])
        self.assertTrue(all(answer['output']['relation'] == 'neither'
                            for answer in held['steps'][-1]['answers']))
        self.select('stock-pots', base='unhelpful-root')
        self.assertEqual(self.selected('stock-pots'), dict(
            local=dict(note_id='stock', number='3.1'), mapped_parent=None))
        self.cli('run', self.state('stock-pots')['experiment'])
        self.cli('advance-canonical-trial', 'stock-pots', '--meaning-case', 'bootstrap',
                 '--comment', 'Validate child with no accepted immediate parent.')
        pending = self.state('stock-pots')
        selection = pending['comparison_selections'][str(pending['index'])]
        self.assertIsNone(selection['mapped_parent'])
        self.assertIn('C003', selection['queried'])
        # Food storage and Pantry food storage share the incoming post. Neither
        # becomes an exception merely because its note is useful to this task.
        self.assertNotIn('C001', selection['queried'])
        self.assertNotIn('C004', selection['queried'])
        self.finish('stock-pots')
        applied = self.state('stock-pots')['steps'][-1]
        self.assertEqual(applied['status'], 'added')
        added = next(node for node in applied['after']
                     if node['id'] == applied['canonical_id'])
        self.assertEqual(added['parents'], ['C003'])

    def test_incomplete_shaped_and_changed_source_bases_are_refused_without_mutation(self):
        self.setup_completed_roots()
        self.select('pending')
        self.write('shape.json', dict(schema_version=1, trial='trial',
                   roots=['C001', 'C003'], children={'C001': ['C002']}))
        self.cli('shape-canonical-trial', '--source', 'shape.json', '--output', 'shaped')
        calls = self.calls()
        for base in ('pending', 'shaped'):
            with self.subTest(base=base):
                original = {p: p.read_bytes() for p in (self.root / base).rglob('*')
                            if p.is_file()}
                output = 'refused-' + base
                result = self.select(output, base=base, ok=False)
                self.assertIn('completed raw', result.stderr)
                self.assertFalse((self.root / output).exists())
                self.assertEqual({p: p.read_bytes() for p in original}, original)
                self.assertEqual(self.calls(), calls)
        before = (self.root / 'trial/state.json').read_bytes()
        with (self.root / 'notes.json').open('a') as source:
            source.write('\n')
        result = self.select('refused-source', ok=False)
        self.assertIn('trial source changed', result.stderr)
        self.assertFalse((self.root / 'refused-source').exists())
        self.assertEqual((self.root / 'trial/state.json').read_bytes(), before)
        self.assertEqual(self.calls(), calls)

    def test_bounded_overcrowding_nominees_include_later_witness_grouping_heading(self):
        self.setup_completed_roots()
        headings = [('garden', 'Garden plants'), ('utensils', 'Kitchen utensils'),
                    ('vessels', 'Cooking vessels'), ('budget', 'Household budgeting'),
                    ('travel', 'Travel'), ('sports', 'Sports'), ('music', 'Music')]
        notes = [dict(note_id=note_id, text=subject + ' post.', subjects=[
                     dict(number='1', subject=subject, context='The post concerns ' + subject + '.')])
                 for note_id, subject in headings]
        notes[0]['subjects'].extend([
            dict(number='2', subject='Garden plants in beds', context='Plants grown in garden beds.'),
            dict(number='3', subject='Garden plants in pots', context='Plants grown in garden pots.')])
        notes[3]['text'] = 'The household budget includes replacing kitchen utensils and cooking vessels.'
        notes[3]['subjects'].append(dict(number='2', subject='Kitchen equipment',
                                       context='Kitchen utensils and cooking vessels to be replaced.'))
        self.write('crowded-notes.json', dict(schema_version=1, notes=notes))
        cfg = json.loads((self.root / 'trial.json').read_text())
        cfg.update(corpus='crowded-notes.json', roots=[
            dict(note_id=note_id, number='1') for note_id, _ in headings])
        self.write('crowded-trial.json', cfg)
        self.cli('prepare-canonical-trial', 'crowded', '--spec', 'crowded-trial.json')
        self.finish('crowded', nodes=7, relations={})
        self.write('crowded-selection.json', dict(schema_version=1, max_choices=6,
                   max_entries=12, canonical_limit=16, local_candidate_limit=2,
                   topic_groups=[]))
        calls = self.calls()
        self.cli('prepare-canonical-selection-trial', 'nominees',
                 '--base-trial', 'crowded', '--spec', 'crowded-selection.json')
        report = json.loads((self.root / 'nominees/selection.json').read_text())
        self.assertEqual(report['problem']['kind'], 'choices')
        self.assertEqual(len(report['problem']['choices']), 7)
        self.assertLessEqual(len(report['nominees']), 2)
        # Kitchen equipment is nominated by the later Kitchen utensils witness.
        # The Garden plants witness must not fill the entire bounded list before
        # later queries contribute. No saved answer or menu supplies this order.
        self.assertIn('budget:2', report['nominees'])
        self.assertEqual(self.calls(), calls)


if __name__ == '__main__':
    unittest.main()
