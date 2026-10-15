"""V5 cuts and construction through the production hierarchy workflow."""

import json
import os
from copy import deepcopy
from pathlib import Path
import unittest
from unittest.mock import patch
from threading import Barrier, Lock

from sse_multivector import hierarchy_hdbscan as hdbscan
from sse_multivector.test_hierarchy_hdbscan import fixture
from sse_multivector import test_hierarchy_generation_v3 as native_fixtures


class V5ConstructionTests(unittest.TestCase):
    def setUp(self):
        self.native = native_fixtures.HierarchyGenerationV3Tests('runTest')
        self.native.setUp()
        self.addCleanup(self.native.doCleanups)

    def prepare(self, count=9, tied=False, bend=False):
        path = self.native.prepare_v41(count=count, tied=tied)
        if bend:
            binary = self.native.root/'hdbscan-fixture'
            binary.write_text(binary.read_text().replace(
                '1/((k-i-1)/10)', '1/(10-.01*i if i<k-5 else max(.01,(k-i-1)/10))'))
        cfg = json.loads(path.read_text())
        cfg['generation_policy'] = 'hierarchy-generation-v5'
        return self.native.write('v5.json', cfg)

    def test_native_v5_keeps_small_groups_as_leaves_and_freezes_three_two(self):
        from sse_multivector import hierarchy_generation as generation
        spec = self.prepare()
        self.native.cli('prepare-hierarchy', 'v5', '--spec', spec)
        result = json.loads(self.native.cli('run-hierarchy', 'v5').stdout)
        state = json.loads((self.native.root/'v5/state.json').read_text())
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(len(state['nodes']), 3)
        self.assertTrue(all(n['leaf'] for n in state['nodes']))
        request = json.loads(Path(state['families'][0]['rounds'][0]['hdbscan']['request']).read_text())
        self.assertEqual(request['hdbscan_configuration'], dict(
            min_samples=3, min_cluster_size=2, selection_method='excess_of_mass'))
        self.assertEqual(len(state['experiments']), 2)  # Bootstrap + group names.
        generation.check_state(state)

    def test_independent_parent_definitions_prepare_separate_native_batches(self):
        from sse_multivector import hierarchy_generation_v5 as generation_v5
        state = self.construct(self.prepare())
        parents = [n['id'] for n in state['nodes'][:2]]
        originals = [o['id'] for o in state['originals']]
        for parent in parents:
            generation_v5._definition(state, originals[:3], parent, 'group')
            generation_v5._definition(state, originals[3:6], parent, 'group')
        before = len(state['experiments'])
        calls = self.native.calls()
        generation_v5._prepare_definitions(self.native.root/'v5', state)
        batches = state['experiments'][before:]
        actual = [{json.loads(inputs['INPUT_JSON'])['parent']['title']
                   for inputs in record['inputs'].values()} for record in batches]
        self.assertEqual(len(batches), 2, 'unrelated parents share a batch completion barrier')
        self.assertTrue(all(len(group) == 1 for group in actual))
        self.assertEqual(self.native.calls(), calls)

    def test_native_advancement_reads_compact_clustering_results(self):
        from sse_multivector import hierarchy_generation as generation
        state = self.construct(self.prepare(count=43))
        before = (self.native.root/'v5/state.json').read_bytes()
        with patch.object(generation.workflow, 'read', wraps=generation.workflow.read) as read:
            generation.advance(self.native.root/'v5', 'Validate complete saved hierarchy')
        reads = [c for c in read.call_args_list if Path(c.args[0]).name == 'result.json']
        self.assertTrue(reads)
        self.assertTrue(all(c.kwargs.get('project') is not None for c in reads),
                        'unused distance matrices are parsed and retained as full results')
        self.assertEqual((self.native.root/'v5/state.json').read_bytes(), before)

    def test_cached_result_cannot_hide_a_changed_raw_clustering_file(self):
        from sse_multivector import hierarchy_generation as generation
        state = self.construct(self.prepare(count=43))
        path = Path(state['families'][0]['rounds'][0]['hdbscan']['result'])
        with generation.workflow.report_scope() as files:
            hdbscan.read_result(path)
            stamp, stat = files._stamp(path), files._stamp
            raw = path.read_bytes()
            changed = raw.replace(b'"min_samples":3', b'"min_samples":4', 1)
            self.assertNotEqual(raw, changed)
            path.write_bytes(changed)
            with patch.object(files, '_stamp', side_effect=lambda p: stamp if Path(p) == path else stat(p)):
                with self.assertRaisesRegex(ValueError, 'saved HDBSCAN evidence changed'):
                    generation.check_state(state, verify_receipts=False)

    def test_ready_native_batches_all_start_before_waiting(self):
        from sse_multivector import hierarchy_generation as generation
        directory = self.native.root/'concurrent'
        directory.mkdir()
        names = [str(directory/f'batch-{i}') for i in range(5)]
        barrier, lock, completed = Barrier(5, timeout=10), Lock(), set()

        def teacher(_directory, path, *_args):
            barrier.wait()
            with lock:
                completed.add(str(path))

        def advance(*_args):
            with lock:
                done = len(completed) == len(names)
            return dict(status='complete' if done else 'constructing',
                        experiments=[] if done else names, encodings=[],
                        generation_policy='hierarchy-generation-v5',
                        canonical_nodes=0, original_l1s=0)

        with patch.object(generation, '_native_teacher', side_effect=teacher), \
                patch.object(generation, '_native_advance', side_effect=advance):
            result = generation.run(directory)
        self.assertEqual(result['execution_status'], 'complete')
        self.assertEqual(result['errors'], [])
        self.assertEqual(completed, set(names))

    def test_completed_run_advances_without_restarting_the_python_process(self):
        from sse_multivector import hierarchy_generation as generation
        self.construct(self.prepare())
        directory = self.native.root/'v5'
        before = (directory/'state.json').read_bytes()
        with patch.object(generation.subprocess, 'run', side_effect=AssertionError('unnecessary advancement subprocess')):
            result = generation.run(directory)
        self.assertEqual(result['execution_status'], 'complete')
        self.assertEqual((directory/'state.json').read_bytes(), before)

    def construct(self, spec, name='v5'):
        from sse_multivector import hierarchy_generation as generation
        self.native.cli('prepare-hierarchy', name, '--spec', spec)
        with patch('sse_multivector.worker.OfficialSseEncoder', return_value=native_fixtures.FixtureEncoder()), \
                patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.native.log)):
            result = generation.run(self.native.root/name)
        self.assertEqual(result['status'], 'complete', result)
        return json.loads((self.native.root/name/'state.json').read_text())

    def test_recursive_children_use_original_entries_and_parent_scope(self):
        from sse_multivector import hierarchy_generation as generation
        state = self.construct(self.prepare(count=43))
        deeper = [f for f in state['families'] if f['parent'] is not None and f['rounds']]
        self.assertTrue(deeper)
        nodes = {n['id']: n for n in state['nodes']}
        for family in deeper:
            self.assertEqual(family['rounds'][0]['current'], nodes[family['parent']]['original_ids'])
            self.assertTrue(all(i.startswith('L') for i in family['rounds'][0]['current']))
        self.assertTrue(any(d['stage'] == 'section' for d in state['v5']['definitions'].values()))
        for d in state['v5']['definitions'].values():
            if d['stage'] == 'section':
                self.assertTrue(all(i.startswith('T') for i in d['members']))
            if d['parent'] is not None:
                p = nodes[d['parent']]
                self.assertEqual(d['payload']['parent'], dict(title=p['subject'], meaning=p['meaning']))
        generation.check_state(state)

    def test_roots_only_trial_keeps_original_noise_available_for_later_roots(self):
        from sse_multivector import hierarchy_generation as generation

        spec = self.prepare(count=43, bend=True)
        cfg = json.loads(spec.read_text())
        cfg['v5_options'] = dict(roots_only=True, include_original_unassigned=True)
        self.native.write('v5.json', cfg)
        state = self.construct(spec)
        self.assertEqual(len(state['families']), 1)
        self.assertTrue(all(not n['parents'] for n in state['nodes']))
        family = state['families'][0]
        first = family['rounds'][0]
        noise = set(first['unassigned'])
        self.assertTrue(noise)
        self.assertGreater(len(family['rounds']), 1)
        self.assertTrue(noise <= set(first['after']))
        self.assertTrue(noise <= set(family['rounds'][1]['current']))
        self.assertEqual(state['v5']['eligible_ids'], family['original_ids'])
        self.assertEqual(generation.summary(state)['scope'], 'roots only')
        altered = deepcopy(state)
        altered['v5_options']['include_original_unassigned'] = False
        with self.assertRaisesRegex(ValueError, 'frozen hierarchy definition'):
            generation.check_state(altered, verify_receipts=False)

    def test_roots_only_trial_preserves_original_noise_exclusion_by_default(self):
        spec = self.prepare(count=43, bend=True)
        cfg = json.loads(spec.read_text())
        cfg['v5_options'] = dict(roots_only=True)
        self.native.write('v5.json', cfg)
        state = self.construct(spec)
        self.assertEqual(len(state['families']), 1)
        family = state['families'][0]
        first = family['rounds'][0]
        noise = set(first['unassigned'])
        self.assertTrue(noise)
        self.assertFalse(noise & set(first['after']))
        self.assertFalse(noise & set(state['v5']['eligible_ids']))

    def test_v5_trial_options_require_known_boolean_fields(self):
        from sse_multivector import hierarchy_generation as generation

        spec = self.prepare()
        cfg = json.loads(spec.read_text())
        for options in (None, [], {'roots_only': 1},
                        {'include_original_unassigned': 'yes'}, {'other': True}):
            with self.subTest(options=options):
                self.native.write('v5.json', dict(cfg, v5_options=options))
                with self.assertRaisesRegex(ValueError, 'invalid hierarchy generation spec'):
                    generation.prepare(spec, self.native.root/'invalid')

    def test_original_noise_is_excluded_but_leftover_notes_survive_viewer_export(self):
        from sse_multivector.canonical_hierarchy_viewer import export_viewer
        state = self.construct(self.prepare(count=22, tied=True))
        self.assertEqual(len(state['nodes']), 6)
        self.assertEqual(len(state['v5']['original_unassigned_ids']), 1)
        self.assertEqual(len(state['direct_note_ids']), 3)
        result = export_viewer(self.native.root/'v5', self.native.root/'viewer')
        self.assertEqual(result['note_count'], 21)
        view = json.loads(Path(result['hierarchy']).read_text())
        self.assertEqual(len(view['nodes'][0]['note_ids']), 3)

    def test_amendment_retains_ownership_and_later_noise_stays_eligible(self):
        from sse_multivector import hierarchy_generation as generation
        state = self.construct(self.prepare(count=43, bend=True))
        root_family = state['families'][0]
        self.assertGreater(len(root_family['rounds']), 1)
        self.assertTrue(any(len(n['versions']) > 1 for n in state['nodes']))
        later_noise = 0
        for round_ in root_family['rounds'][1:]:
            later_noise += len(round_['unassigned'])
            removed = {i for p in round_['proposals'] for i in p['members']}
            for i in round_['unassigned']:
                if i not in removed:
                    self.assertIn(i, round_['after'])
            for p in round_['proposals']:
                if p['owner'] is not None:
                    self.assertEqual(p['node'], p['owner'])
        self.assertGreater(later_noise, 0)
        generation.check_state(state)

    def test_complete_resume_and_identical_second_run_reuse_native_answers(self):
        from sse_multivector import hierarchy_generation as generation
        spec = self.prepare()
        state = self.construct(spec)
        before = self.native.calls()
        generation.run(self.native.root/'v5')
        self.assertEqual(self.native.calls(), before)
        second = self.construct(spec, 'second')
        self.assertEqual(self.native.calls(), before)
        self.assertEqual([n['original_ids'] for n in second['nodes']],
                         [n['original_ids'] for n in state['nodes']])

    def test_new_preparation_defaults_to_v5(self):
        spec = self.prepare()
        cfg = json.loads(spec.read_text())
        del cfg['generation_policy']
        self.native.write('v5.json', cfg)
        state = self.construct(spec)
        self.assertEqual(state['generation_policy'], 'hierarchy-generation-v5')

    def test_all_initial_noise_finishes_without_inventing_groups(self):
        from sse_multivector import hierarchy_generation as generation
        spec = self.prepare()
        binary = self.native.root/'hdbscan-fixture'
        binary.write_text(binary.read_text().replace(
            'groups=[ids[i:i+3] for i in range(0,len(ids)-2,3)]', 'groups=[]'))
        directory = self.native.root/'v5'
        generation.prepare(spec, directory)
        result = generation.advance(directory, 'Collect empty HDBSCAN result')
        self.assertEqual(result['status'], 'complete')
        state = json.loads((directory/'state.json').read_text())
        self.assertEqual(state['nodes'], [])
        self.assertEqual(state['v5']['eligible_ids'], [])
        self.assertEqual(state['direct_note_ids'], [])

    def test_changed_leaf_membership_is_rejected_before_advancing(self):
        from sse_multivector import hierarchy_generation as generation
        state = self.construct(self.prepare())
        altered = deepcopy(state)
        altered['nodes'][0]['groups'] = []
        with self.assertRaisesRegex(ValueError, 'group|version'):
            generation.check_state(altered, verify_receipts=False)

    def test_fresh_bootstrap_path_uses_native_reuse_and_the_ordinary_encoder(self):
        spec = self.prepare()
        cfg = json.loads(spec.read_text())
        del cfg['bootstrap_hierarchy']
        self.native.write('v5.json', cfg)
        state = self.construct(spec)
        self.assertNotIn('bootstrap_hierarchy', state)
        self.assertTrue(state['encodings'])
        self.assertEqual([o['title'] for o in state['originals']],
                         [o['title'] for o in self.native.state()['originals']])

    def test_unresolved_only_topic_does_not_block_other_notes(self):
        from sse_multivector import hierarchy_generation as generation
        spec = self.native.prepare_v41(count=10, encode=False, null_first=True)
        cfg = json.loads(spec.read_text())
        cfg['generation_policy'] = 'hierarchy-generation-v5'
        del cfg['bootstrap_hierarchy']
        spec = self.native.write('v5.json', cfg)
        state = self.construct(spec)
        report = generation.summary(state)
        self.assertEqual(len(state['note_ids']), 10)
        self.assertEqual(len(state['originals']), 10)
        self.assertIsNone(state['originals'][0]['meaning'])
        self.assertNotIn('L00001', state['items'])
        self.assertIn('n0', report['notes_not_in_hierarchy'])
        self.assertEqual([row['case'] for row in report['skipped_bootstrap']], ['L00001'])
        generation.check_state(state)

    def test_finished_lineup_does_not_encode_representatives_with_nothing_left_to_add(self):
        spec = self.prepare(count=24)
        binary = self.native.root/'hdbscan-fixture'
        binary.write_text(binary.read_text().replace(
            '1/((k-i-1)/10)', '1/[10,9.99,9.98,1,.5,.3,.1][i]'))
        original_jobs = len(self.native.state()['encodings'])
        state = self.construct(spec)
        self.assertEqual(len(state['families'][0]['nodes']), 4)
        self.assertEqual(len(state['encodings']), original_jobs)


class V5SelectionTests(unittest.TestCase):
    def test_largest_counts_distinct_notes_instead_of_original_entries(self):
        from sse_multivector.hierarchy_generation_v5 import proposals
        groups = [[f'L{i+1:05d}' for i in range(10)], ['L00011', 'L00012']]+[[f'L{i+1:05d}'] for i in range(12, 17)]
        ids = [i for g in groups for i in g]
        state = dict(items={i: dict(original_ids=[i]) for i in ids}, originals=[
            dict(id=i, local=dict(note_id='one note' if i in groups[0] else i)) for i in ids])
        round_ = dict(current=ids, groups=groups, selection=dict(
            rule='trimmed-bend-10-percent-v1',
            sections=[dict(groups=[i+1]) for i in range(7)]))
        result = proposals(state, round_)
        self.assertEqual([p['members'] for p in result['proposals']], [['L00011', 'L00012']])

    def test_existing_representatives_never_become_a_new_merged_canonical_node(self):
        from sse_multivector.hierarchy_generation_v5 import proposals
        state = dict(items=dict(R1=dict(owner='C1'), R2=dict(owner='C2'), L1={}))
        round_ = dict(current=['R1', 'R2', 'L1'], groups=[['R1', 'R2', 'L1']],
                      selection=dict(rule='group-leaves-v5', sections=[dict(groups=[1])]))
        result = proposals(state, round_)
        self.assertEqual(result['proposals'], [])
        self.assertEqual(result['conflicting_sections'], [dict(groups=[0], owners=['C1', 'C2'])])


class V5CutTests(unittest.TestCase):
    def tree(self, groups, distances=None):
        return hdbscan.project(*fixture(groups, distances))

    def test_middle_eighty_percent_bend_can_keep_more_than_six_sections(self):
        tree = self.tree(14, [100, 99, 98, 97, 96, 95, 94, 93, 92, 80, 60, 30, 1])
        result = hdbscan.select_sections(tree)
        self.assertEqual(result['rule'], 'trimmed-bend-10-percent-v1')
        self.assertEqual(result['omitted_levels_per_end'], 2)
        self.assertEqual(result['epsilon'], 86)
        self.assertEqual(len(result['sections']), 10)
        self.assertEqual(sorted(g for s in result['sections'] for g in s['groups']),
                         list(range(1, 15)))

    def test_short_curve_uses_previous_six_section_cut(self):
        result = hdbscan.select_sections(self.tree(8))
        self.assertEqual(result['rule'], 'six-section-v4')
        self.assertEqual(len(result['sections']), 6)
        self.assertEqual(result['epsilon'], 2.5)

    def test_no_positive_bend_uses_previous_cut(self):
        result = hdbscan.select_sections(self.tree(8, [128, 64, 32, 16, 8, 4, 2]))
        self.assertEqual(result['rule'], 'six-section-v4')
        self.assertIn('positive bend', result['reason'])

    def test_impossible_tied_cut_returns_groups_for_largest_note_selection(self):
        result = hdbscan.select_sections(self.tree(8, [1]*7))
        self.assertEqual(result['rule'], 'largest-groups-v5')
        self.assertIsNone(result['epsilon'])
        self.assertEqual(len(result['sections']), 8)
        self.assertTrue(all(len(s['groups']) == 1 for s in result['sections']))

    def test_six_or_fewer_groups_are_direct_leaves(self):
        for count in (1, 4, 6):
            with self.subTest(count=count):
                result = hdbscan.select_sections(self.tree(count))
                self.assertEqual(result['rule'], 'group-leaves-v5')
                self.assertEqual(len(result['sections']), count)
                self.assertTrue(all(not s['children'] for s in result['sections']))


if __name__ == '__main__':
    unittest.main()
