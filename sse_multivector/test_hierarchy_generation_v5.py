"""V5 cuts and construction through the production hierarchy workflow."""

import json
import os
from copy import deepcopy
from pathlib import Path
import subprocess
import sys
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

    def test_preparation_can_select_the_complete_collected_corpus(self):
        spec = self.prepare(count=9)
        config = json.loads(spec.read_text())
        expected = config.pop('note_ids')
        spec.write_text(json.dumps(config))
        before = len(self.native.calls())
        self.native.cli('prepare-hierarchy', 'all-notes', '--spec', spec)
        state = json.loads((self.native.root / 'all-notes/state.json').read_text())
        self.assertEqual(state['note_ids'], expected)
        self.assertEqual(len(self.native.calls()), before)
        result = json.loads(self.native.cli('run-hierarchy', 'all-notes').stdout)
        self.assertEqual(result['status'], 'complete')

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
        reader = generation.workflow.engine.ReceiptFiles.json
        with patch.object(generation.workflow.engine.ReceiptFiles, 'json',
                          autospec=True, side_effect=reader) as read:
            generation.advance(self.native.root/'v5', 'Validate complete saved hierarchy')
        reads = [c for c in read.call_args_list if Path(c.args[1]).name == 'result.json']
        self.assertTrue(reads)
        self.assertTrue(all(c.kwargs.get('project') is not None for c in reads),
                        'unused distance matrices are parsed and retained as full results')
        self.assertEqual((self.native.root/'v5/state.json').read_bytes(), before)

    def test_native_generation_requests_hierarchy_output(self):
        spec = self.prepare()
        binary = self.native.root/'hdbscan-fixture'
        binary.write_text(binary.read_text().replace(
            'import json, sys',
            'import json, sys\nassert "--hierarchy-output" in sys.argv[2:], "compact output not requested"'))
        self.construct(spec)

    def test_structural_audit_reuses_unchanged_numerical_checks_with_bounded_results(self):
        from sse_multivector import canonical_hierarchy_audit

        state = self.construct(self.prepare())
        expected = sum(len(f['rounds']) for f in state['families'])
        budgets = []
        original = hdbscan._validate_saved_round

        def checked(*args, **kwargs):
            files = hdbscan._RESULT_FILES.get()
            budgets.append(None if files is None else files._projected_limit)
            return original(*args, **kwargs)

        with hdbscan.cpu_scope(1), patch.object(hdbscan, '_validate_saved_round', side_effect=checked) as validate:
            canonical_hierarchy_audit.audit_trial(self.native.root/'v5', self.native.root/'audit.json')
        self.assertEqual(validate.call_count, expected, 'audit replayed unchanged numerical history')
        self.assertEqual(budgets, [16 * 1024 * 1024] * expected)

    def test_structural_audit_rechecks_changed_numerical_evidence_before_writing(self):
        from sse_multivector import canonical_hierarchy_audit, canonical_trial

        state = self.construct(self.prepare())
        result = Path(state['families'][0]['rounds'][0]['hdbscan']['result'])
        output = self.native.root/'audit.json'
        original, calls = canonical_trial._check, 0

        def checked(*args, **kwargs):
            nonlocal calls
            value = original(*args, **kwargs)
            calls += 1
            if calls == 1:
                before, stamp = result.read_bytes(), result.stat()
                changed = before.replace(b'"min_samples":3', b'"min_samples":4', 1)
                self.assertNotEqual(changed, before)
                result.write_bytes(changed)
                os.utime(result, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
            return value

        with hdbscan.cpu_scope(1), patch.object(canonical_trial, '_check', side_effect=checked):
            with self.assertRaisesRegex(ValueError, 'saved HDBSCAN evidence changed'):
                canonical_hierarchy_audit.audit_trial(self.native.root/'v5', output)
        self.assertFalse(output.exists())

    def test_structural_audit_starts_fresh_inside_an_existing_source_scope(self):
        from sse_multivector import canonical_hierarchy_audit, hierarchy_generation

        state = self.construct(self.prepare())
        expected = sum(len(f['rounds']) for f in state['families'])
        with hdbscan.cpu_scope(1), hdbscan.source_scope():
            hierarchy_generation.check_state(state)
            parent = hdbscan._RESULT_FILES.get()
            with patch.object(hdbscan, '_validate_saved_round', wraps=hdbscan._validate_saved_round) as validate:
                canonical_hierarchy_audit.audit_trial(self.native.root/'v5', self.native.root/'audit.json')
            self.assertEqual(validate.call_count, expected, 'audit inherited an earlier verification verdict')
            self.assertIs(hdbscan._RESULT_FILES.get(), parent)

    def test_legacy_numerical_binary_can_still_resume_with_its_full_output(self):
        spec = self.prepare()
        binary = self.native.root/'hdbscan-fixture'
        binary.write_text(binary.read_text().replace('import json, sys',
            'import json, sys\n'
            'if "--hierarchy-output" in sys.argv[2:]:\n'
            '    print("usage: fine-segmentation-candidate REQUEST.json [--threads N]", file=sys.stderr)\n'
            '    sys.exit(1)'))
        state = self.construct(spec)
        self.assertEqual(state['status'], 'complete')

    def test_native_validation_uses_processes_for_independent_saved_rounds(self):
        from concurrent.futures import ProcessPoolExecutor
        from sse_multivector import hierarchy_generation as generation, hierarchy_hdbscan
        self.construct(self.prepare(count=43))
        before = (self.native.root/'v5/state.json').read_bytes()
        with (hierarchy_hdbscan.cpu_scope(2),
              patch.object(hierarchy_hdbscan, '_PARALLEL_MIN_VECTORS', 1, create=True),
              patch.object(hierarchy_hdbscan, 'ProcessPoolExecutor',
                           wraps=ProcessPoolExecutor, create=True) as pools):
            generation.advance(self.native.root/'v5', 'Validate independent numerical evidence concurrently')
        pools.assert_called()
        self.assertEqual((self.native.root/'v5/state.json').read_bytes(), before)

    def test_native_resume_records_explicit_binary_upgrade_and_cpu_budget(self):
        self.construct(self.prepare(count=43))
        before = (self.native.root/'v5/state.json').read_bytes()
        saved = json.loads(before)
        replacement = self.native.root/'parallel-hdbscan'
        replacement.write_bytes(Path(saved['hdbscan_binary']).read_bytes()+b'\n# parallel runtime\n')
        replacement.chmod(0o755)
        result = json.loads(self.native.cli(
            'run-hierarchy', 'v5', '--hdbscan-binary', str(replacement),
            '--cpu-workers', '2', '--runner-upgrade-reason', 'Reviewed exact numerical runtime upgrade').stdout)
        self.assertEqual(result['status'], 'complete')
        state = json.loads((self.native.root/'v5/state.json').read_bytes())
        self.assertEqual(state['nodes'], saved['nodes'])
        self.assertEqual(state['hdbscan_binary'], str(replacement))
        self.assertIn(saved['hdbscan_binary'], state['sources'])
        self.assertIn(str(replacement), state['sources'])
        self.assertEqual(state['source_upgrades'][-1]['hdbscan_binary'],
                         dict(before=saved['hdbscan_binary'], after=str(replacement)))
        settings = [json.loads(line) for line in
                    (self.native.root/'v5/execution-settings.jsonl').read_text().splitlines()]
        self.assertEqual(settings[-1]['cpu_workers'], 2)
        state['source_upgrades'][-1]['hdbscan_binary']['before'] = str(replacement)
        with self.assertRaisesRegex(ValueError, 'executable upgrade history changed'):
            from sse_multivector import hierarchy_generation as generation
            generation.check_state(state, verify_receipts=False)

    def test_cpu_scope_limits_children_and_restores_original_affinity(self):
        import os
        from sse_multivector import hierarchy_hdbscan
        if not hasattr(os, 'sched_getaffinity'):
            self.skipTest('CPU affinity is unavailable')
        before = os.sched_getaffinity(0)
        with hierarchy_hdbscan.cpu_scope(min(2, len(before))) as count:
            self.assertEqual(count, min(2, len(before)))
            self.assertEqual(len(os.sched_getaffinity(0)), count)
            observed = subprocess.check_output(
                [sys.executable, '-c', 'import os; print(len(os.sched_getaffinity(0)))'], text=True)
            self.assertEqual(int(observed), count)
        self.assertEqual(os.sched_getaffinity(0), before)
        with self.assertRaisesRegex(ValueError, 'positive integer'):
            with hierarchy_hdbscan.cpu_scope(0):
                self.fail('zero CPU budget accepted')

    def test_hdbscan_scope_retains_larger_saved_views_without_reparsing(self):
        state = self.construct(self.prepare(count=10))
        result = Path(state['families'][0]['rounds'][0]['hdbscan']['result'])
        response = json.loads(result.read_text())
        response['artifact']['manifest']['description'] = 'x' * (6 * 1024 * 1024)
        paths = [self.native.root/f'large-result-{i}.json' for i in range(3)]
        for path in paths:
            path.write_text(json.dumps(response))
        with hdbscan.source_scope(), patch.object(hdbscan.json, 'loads', wraps=json.loads) as decode:
            for _ in range(2):
                for path in paths:
                    value = hdbscan.read_result(path)
                    self.assertEqual(value['artifact']['manifest'], response['artifact']['manifest'])
            self.assertEqual(decode.call_count, 3, 'saved clustering views were repeatedly parsed')

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

    def test_completed_run_advances_once_and_still_writes_summary(self):
        from sse_multivector import hierarchy_generation as generation
        self.construct(self.prepare())
        directory = self.native.root/'v5'
        with patch.object(generation, '_native_advance', wraps=generation._native_advance) as advance:
            result = generation.run(directory)
        self.assertEqual(result['execution_status'], 'complete')
        self.assertEqual(advance.call_count, 1, 'completed hierarchy was advanced again')
        self.assertEqual(json.loads((directory/'run-summary.json').read_text()), result)

    def test_completion_drains_remaining_jobs_without_another_advancement(self):
        from threading import Event
        from sse_multivector import hierarchy_generation as generation
        directory = self.native.root/'drain'
        directory.mkdir()
        started, release, finished = Event(), Event(), Event()
        calls = []

        def teacher(_directory, path, *_args):
            if path.name == 'second':
                started.set()
                self.assertTrue(release.wait(10))
                finished.set()
            else:
                self.assertTrue(started.wait(10))

        def advance(*_args):
            calls.append(True)
            self.assertLessEqual(len(calls), 2, 'completed graph advanced while jobs drained')
            complete = len(calls) == 2
            if complete:
                release.set()
            return dict(status='complete' if complete else 'constructing',
                        experiments=[] if complete else [str(directory/'first'), str(directory/'second')],
                        encodings=[], generation_policy='hierarchy-generation-v5',
                        canonical_nodes=0, original_l1s=0)

        with patch.object(generation, '_native_teacher', side_effect=teacher), \
                patch.object(generation, '_native_advance', side_effect=advance):
            result = generation.run(directory)
        self.assertTrue(finished.is_set())
        self.assertEqual(result['execution_status'], 'complete')
        self.assertEqual(result['errors'], [])
        self.assertEqual(len(calls), 2)

    def test_unchanged_numerical_evidence_is_validated_once_per_run_scope(self):
        from sse_multivector import hierarchy_generation as generation
        self.construct(self.prepare(count=43))
        directory = self.native.root/'v5'
        with hdbscan.cpu_scope(1), hdbscan.source_scope(), \
                patch.object(hdbscan, '_validate_saved_round', wraps=hdbscan._validate_saved_round) as validate:
            generation.advance(directory, 'Check saved numerical evidence')
            initial = validate.call_count
            self.assertGreater(initial, 0)
            generation.advance(directory, 'Unchanged evidence needs no replay')
            self.assertEqual(validate.call_count, initial, 'unchanged history was replayed')
        with hdbscan.cpu_scope(1), \
                patch.object(hdbscan, '_validate_saved_round', wraps=hdbscan._validate_saved_round) as validate:
            generation.advance(directory, 'Fresh operation rechecks saved evidence')
            self.assertGreater(validate.call_count, 0)

    def test_validation_reuse_rejects_changed_results_even_with_restored_mtime(self):
        from sse_multivector import hierarchy_generation as generation
        state = self.construct(self.prepare(count=43))
        path = Path(state['families'][0]['rounds'][0]['hdbscan']['result'])
        with hdbscan.cpu_scope(1), hdbscan.source_scope():
            generation.check_state(state, verify_receipts=False)
            stamp = path.stat()
            data = path.read_bytes()
            changed = data.replace(b'"min_samples":3', b'"min_samples":4', 1)
            self.assertNotEqual(data, changed)
            path.write_bytes(changed)
            os.utime(path, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
            with self.assertRaisesRegex(ValueError, 'saved HDBSCAN evidence changed'):
                generation.check_state(state, verify_receipts=False)

    def test_validation_reuse_rejects_changed_vector_file_and_changed_round(self):
        from sse_multivector import hierarchy_generation as generation, worker
        state = self.construct(self.prepare(count=43))
        with hdbscan.cpu_scope(1), hdbscan.source_scope():
            generation.check_state(state, verify_receipts=False)
            altered = deepcopy(state)
            round_ = altered['families'][0]['rounds'][0]
            round_['groups'][0].reverse()
            with self.assertRaises(ValueError):
                generation.check_state(altered, verify_receipts=False)
            config = worker.WorkerConfig.load(Path(state['encodings'][0]['config']))
            path = config.output_path/'raw-vectors.f32le'
            data = bytearray(path.read_bytes())
            data[0] ^= 1
            path.write_bytes(data)
            with self.assertRaisesRegex(ValueError, 'vector hash or shape differs'):
                generation.check_state(state, verify_receipts=False)

    def construct(self, spec, name='v5'):
        from sse_multivector import hierarchy_generation as generation
        self.native.cli('prepare-hierarchy', name, '--spec', spec)
        with patch('sse_multivector.worker.OfficialSseEncoder', return_value=native_fixtures.FixtureEncoder()), \
                patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.native.log)):
            result = generation.run(self.native.root/name)
        self.assertEqual(result['status'], 'complete', result)
        return json.loads((self.native.root/name/'state.json').read_text())

    def test_v53_adds_global_untracked_members_after_all_roots_are_built(self):
        from sse_multivector import hierarchy_generation as generation

        spec = self.prepare(count=10)
        cfg = json.loads(spec.read_text())
        del cfg['generation_policy']
        self.native.write('v5.json', cfg)
        binary = self.native.root/'hdbscan-fixture'
        source = self.native.state()
        request, _ = hdbscan.request_for(source, list(source['items']),
                                       generation._vectors(source, list(source['items'])))
        noise = max(i['opaque_id'] for i in request['inputs'])
        binary.write_text(binary.read_text().replace(
            'n=len(ids); k=len(groups)',
            'if "/memberships/" in sys.argv[1]:\n'
            '    ordered=[i["opaque_id"] for i in r["inputs"]]\n'
            f'    noise={noise!r}\n'
            '    groups=[[next(i for i in ordered if i != noise), noise]]\n'
            'n=len(ids); k=len(groups)'))
        state = self.construct(spec)
        originals = {i for n in state['nodes'] for i in state['items'][n['item']]['original_ids']}
        untracked = set(state['v5']['eligible_ids']) - originals
        self.assertEqual(len(untracked), 1)
        for node in state['nodes']:
            self.assertTrue(untracked <= set(node['original_ids']),
                            'a shared HDBSCAN group did not add its untracked entry')
            self.assertTrue(set(state['items'][node['item']]['original_ids']) <= set(node['original_ids']))
        self.assertEqual(state['generation_policy'], 'hierarchy-generation-v5.3')
        self.assertEqual(len(state['experiments']), 2, 'membership grouping added model calls')
        self.assertEqual(state['families'][0]['direct_original_ids'], [])
        record = state['v5']['membership_passes'][0]
        self.assertEqual(set(record['untracked_ids']), untracked)
        self.assertEqual(set(record['rounds']), set(state['families'][0]['nodes']))
        for identifier, round_ in record['rounds'].items():
            node = next(n for n in state['nodes'] if n['id'] == identifier)
            before = state['items'][node['item']]['original_ids']
            self.assertEqual(round_['current'], sorted(set(before) | untracked))
            self.assertEqual(record['additions'][identifier], sorted(untracked))
            self.assertTrue(set(before) & set(round_['unassigned']),
                            'fixture must exercise preservation of old ungrouped members')
        self.assertEqual(len(generation.summary(state)['hdbscan_membership_passes']), 1)
        generation.check_state(state)
        for change, message in [('pool', 'global untracked'), ('addition', 'shared group'),
                                ('membership', 'canonical membership')]:
            with self.subTest(tampering=change):
                altered = deepcopy(state)
                if change == 'pool':
                    altered['v5']['membership_passes'][0]['untracked_ids'] = []
                elif change == 'addition':
                    altered['v5']['membership_passes'][0]['additions'][state['nodes'][0]['id']] = []
                else:
                    node = altered['nodes'][0]
                    node['original_ids'].remove(next(iter(untracked)))
                    node['entries'] = [altered['originals'][int(i[1:])-1]['local']
                                       for i in node['original_ids']]
                with self.assertRaisesRegex(ValueError, message):
                    generation.check_state(altered, verify_receipts=False)
        before = (self.native.root/'v5/state.json').read_bytes()
        calls = self.native.calls()
        with patch.object(hdbscan, 'round_for', side_effect=AssertionError('repeated membership pass')):
            generation.run(self.native.root/'v5')
        self.assertEqual((self.native.root/'v5/state.json').read_bytes(), before)
        self.assertEqual(self.native.calls(), calls)
        cfg['generation_policy'] = 'hierarchy-generation-v5.2'
        frozen = self.construct(self.native.write('v52.json', cfg), 'v52')
        self.assertNotIn('membership_passes', frozen['v5'])
        self.assertFalse(untracked & {i for n in frozen['nodes'] for i in n['original_ids']})
        self.assertEqual(self.native.calls(), calls, 'unchanged teacher answers were not reused')

    def test_v53_untracked_only_groups_do_not_add_membership(self):
        spec = self.prepare(count=11)
        cfg = json.loads(spec.read_text())
        cfg['generation_policy'] = 'hierarchy-generation-v5.3'
        spec = self.native.write('v53.json', cfg)
        from sse_multivector import hierarchy_generation as generation
        source = self.native.state()
        request, _ = hdbscan.request_for(source, list(source['items']),
                                       generation._vectors(source, list(source['items'])))
        noise = sorted(i['opaque_id'] for i in request['inputs'])[-2:]
        binary = self.native.root/'hdbscan-fixture'
        binary.write_text(binary.read_text().replace(
            'n=len(ids); k=len(groups)',
            f'if "/memberships/" in sys.argv[1]: groups=[{noise!r}]\n'
            'n=len(ids); k=len(groups)'))
        state = self.construct(spec)
        record = state['v5']['membership_passes'][0]
        self.assertEqual(len(record['untracked_ids']), 2)
        self.assertTrue(all(not v for v in record['additions'].values()))
        self.assertEqual(set(state['families'][0]['direct_original_ids']), set(record['untracked_ids']))
        for node in state['nodes']:
            self.assertEqual(node['original_ids'], state['items'][node['item']]['original_ids'])

    def test_v53_children_use_global_untracked_entries_outside_the_parent_pool(self):
        from sse_multivector import hierarchy_generation as generation
        spec = self.prepare(count=43, bend=True)
        cfg = json.loads(spec.read_text())
        cfg['generation_policy'] = 'hierarchy-generation-v5.3'
        spec = self.native.write('v53.json', cfg)
        source = self.native.state()
        request, mapping = hdbscan.request_for(source, list(source['items']),
                                             generation._vectors(source, list(source['items'])))
        noise = max(i['opaque_id'] for i in request['inputs'])
        original = mapping[noise]
        binary = self.native.root/'hdbscan-fixture'
        binary.write_text(binary.read_text().replace(
            'n=len(ids); k=len(groups)',
            f'noise={noise!r}\n'
            'if "/memberships/" in sys.argv[1]:\n'
            '    groups=[]\n'
            '    if "/F00000/" not in sys.argv[1] and noise in ids:\n'
            '        groups=[[next(i for i in ids if i != noise), noise]]\n'
            'else:\n'
            '    eligible=[i for i in ids if i != noise]\n'
            '    groups=[eligible[i:i+3] for i in range(0,len(eligible)-2,3)]\n'
            'n=len(ids); k=len(groups)'))
        state = self.construct(spec)
        nodes = {n['id']: n for n in state['nodes']}
        matches = [(p, n) for p in state['v5']['membership_passes']
                   for n, ids in p['additions'].items() if original in ids]
        self.assertTrue(matches, 'no child recovered the global untracked entry')
        for record, identifier in matches:
            family = next(f for f in state['families'] if f['id'] == record['family'])
            self.assertIsNotNone(family['parent'])
            self.assertNotIn(original, family['original_ids'])
            self.assertIn(original, nodes[identifier]['original_ids'])
        root_pass = state['v5']['membership_passes'][0]
        self.assertTrue(all(not ids for ids in root_pass['additions'].values()))
        generation.check_state(state)

    def test_v53_independent_membership_jobs_start_before_waiting(self):
        spec = self.prepare(count=10)
        cfg = json.loads(spec.read_text())
        cfg['generation_policy'] = 'hierarchy-generation-v5.3'
        spec = self.native.write('v53.json', cfg)
        started = self.native.root/'membership-jobs-started'
        started.mkdir()
        binary = self.native.root/'hdbscan-fixture'
        binary.write_text(binary.read_text().replace(
            'r=json.load(open(sys.argv[1]))',
            'from pathlib import Path\n'
            'import time\n'
            'if "/memberships/" in sys.argv[1]:\n'
            f'    started=Path({str(started)!r})\n'
            '    (started/Path(sys.argv[1]).parents[1].name).touch()\n'
            '    deadline=time.monotonic()+5\n'
            '    while len(list(started.iterdir())) < 3:\n'
            '        if time.monotonic() >= deadline:\n'
            '            sys.stderr.write("membership jobs were serialized")\n'
            '            sys.exit(1)\n'
            '        time.sleep(.01)\n'
            'r=json.load(open(sys.argv[1]))'))
        state = self.construct(spec)
        self.assertEqual(len(list(started.iterdir())), 3)
        self.assertEqual(state['status'], 'complete')
        self.assertTrue(state['v5']['membership_passes'][0]['applied'])

    def test_v53_membership_results_are_processed_in_separate_cpu_processes(self):
        spec = self.prepare(count=10)
        cfg = json.loads(spec.read_text())
        cfg['generation_policy'] = 'hierarchy-generation-v5.3'
        spec = self.native.write('v53.json', cfg)
        started = self.native.root/'membership-parents'
        started.mkdir()
        binary = self.native.root/'hdbscan-fixture'
        binary.write_text(binary.read_text().replace(
            'r=json.load(open(sys.argv[1]))',
            'from pathlib import Path\nimport os,time\n'
            'if "/memberships/" in sys.argv[1]:\n'
            f'    started=Path({str(started)!r})\n'
            '    (started/Path(sys.argv[1]).parents[1].name).write_text(str(os.getppid()))\n'
            '    deadline=time.monotonic()+5\n'
            '    while len(list(started.iterdir())) < 3:\n'
            '        if time.monotonic() >= deadline:\n'
            '            raise RuntimeError("membership workers did not start together")\n'
            '        time.sleep(.01)\n'
            'r=json.load(open(sys.argv[1]))'))
        state = self.construct(spec)
        parents = [p.read_text() for p in started.iterdir()]
        self.assertEqual(len(parents), 3)
        self.assertEqual(len(set(parents)), 3, 'all result parsing shares one Python process')
        self.assertEqual(state['status'], 'complete')

    def test_v53_failed_membership_clustering_preserves_a_resumable_frozen_pool(self):
        from sse_multivector import hierarchy_generation as generation
        spec = self.prepare(count=10)
        cfg = json.loads(spec.read_text())
        cfg['generation_policy'] = 'hierarchy-generation-v5.3'
        spec = self.native.write('v53.json', cfg)
        marker = self.native.root/'membership-failed-once'
        binary = self.native.root/'hdbscan-fixture'
        binary.write_text(binary.read_text().replace(
            'r=json.load(open(sys.argv[1]))',
            'from pathlib import Path\n'
            f'marker=Path({str(marker)!r})\n'
            'if "/memberships/C00002/" in sys.argv[1] and not marker.exists():\n'
            '    marker.write_text("failed once")\n'
            '    sys.stderr.write("temporary local clustering failure")\n'
            '    sys.exit(1)\n'
            'r=json.load(open(sys.argv[1]))'))
        directory = self.native.root/'v53'
        generation.prepare(spec, directory)
        with patch('sse_multivector.worker.OfficialSseEncoder', return_value=native_fixtures.FixtureEncoder()), \
                patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.native.log)):
            with self.assertRaisesRegex(ValueError, 'temporary local clustering failure'):
                generation.run(directory)
            interrupted = json.loads((directory/'state.json').read_text())
            self.assertEqual(len(interrupted['v5'].get('membership_passes', [])), 1,
                             'global membership inputs were not checkpointed before clustering')
            self.assertFalse(interrupted['families'][0]['complete'])
            self.assertFalse(interrupted['v5']['membership_passes'][0]['applied'])
            generation.check_state(interrupted)
            results = directory/'F00000/memberships/C00001/hdbscan-00000/result.json'
            before, calls = results.read_bytes(), self.native.calls()
            other = directory/'F00000/memberships/C00003/hdbscan-00000/result.json'
            self.assertTrue(other.exists(), 'successful sibling work was abandoned after another failed')
            other_before = other.read_bytes()
            result = generation.run(directory)
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(self.native.calls(), calls)
        self.assertEqual(results.read_bytes(), before)
        self.assertEqual(other.read_bytes(), other_before)
        state = json.loads((directory/'state.json').read_text())
        self.assertTrue(state['v5']['membership_passes'][0]['applied'])
        self.assertEqual(state['v5']['membership_passes'][0]['canonical_items'],
                         interrupted['v5']['membership_passes'][0]['canonical_items'])
        generation.check_state(state)

    def test_v53_checkpoints_allow_other_unstarted_leaf_group_families(self):
        from sse_multivector import hierarchy_generation as generation
        spec = self.prepare(count=25)
        cfg = json.loads(spec.read_text())
        cfg['generation_policy'] = 'hierarchy-generation-v5.3'
        spec = self.native.write('v53.json', cfg)
        binary = self.native.root/'hdbscan-fixture'
        code = binary.read_text().replace(
            'n=len(ids); k=len(groups)',
            'if "/memberships/" in sys.argv[1]: groups=[]\n'
            'n=len(ids); k=len(groups)')
        code = code.replace('clusters=[', '''if k==8:
    edges=[]
    for parent,children,value in [
        (n,[n+1,n+2],1), (n+1,[n+3,n+4],2), (n+2,[n+5,n+6],2),
        (n+3,leaves[:2],4), (n+4,leaves[2:4],4),
        (n+5,leaves[4:6],4), (n+6,leaves[6:],4)]:
        edges.extend({"parent":parent,"child":child,"child_size":3,"lambda":value}
                     for child in children)
clusters=[''')
        binary.write_text(code)
        state = self.construct(spec)
        families = [f for f in state['families'] if 'leaf_groups' in f]
        self.assertGreater(len(families), 1)
        self.assertTrue(all(f['complete'] for f in families))
        self.assertTrue(all(p['applied'] for p in state['v5']['membership_passes']))
        generation.check_state(state)

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

    def test_leftover_notes_stay_in_state_but_not_the_viewer_container(self):
        from sse_multivector.canonical_hierarchy_viewer import export_viewer
        state = self.construct(self.prepare(count=22, tied=True))
        self.assertEqual(len(state['nodes']), 6)
        self.assertEqual(len(state['v5']['original_unassigned_ids']), 1)
        self.assertEqual(len(state['direct_note_ids']), 3)
        state_path = self.native.root/'v5/state.json'
        original = state_path.read_bytes()
        result = export_viewer(self.native.root/'v5', self.native.root/'viewer')
        self.assertEqual(result['note_count'], 18)
        view = json.loads(Path(result['hierarchy']).read_text())
        self.assertEqual(view['nodes'][0]['note_ids'], [])
        self.assertEqual(state_path.read_bytes(), original)

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

    def test_new_preparation_defaults_to_v53_and_recurses_with_initial_noise(self):
        from sse_multivector import hierarchy_generation as generation

        spec = self.prepare(count=43, bend=True)
        cfg = json.loads(spec.read_text())
        del cfg['generation_policy']
        self.native.write('v5.json', cfg)
        state = self.construct(spec)
        self.assertEqual(state['generation_policy'], 'hierarchy-generation-v5.3')
        family = state['families'][0]
        first = family['rounds'][0]
        self.assertTrue(first['unassigned'])
        self.assertTrue(set(first['unassigned']) <= set(first['after']))
        self.assertEqual(state['v5']['eligible_ids'], family['original_ids'])
        self.assertTrue(any(f['parent'] is not None and f['rounds'] for f in state['families']))
        generation.check_state(state)
        before = (self.native.root/'v5/state.json').read_bytes()
        calls = self.native.calls()
        generation.run(self.native.root/'v5')
        self.assertEqual(self.native.calls(), calls)
        self.assertEqual((self.native.root/'v5/state.json').read_bytes(), before)

    def test_v51_retains_original_noise_without_an_eligibility_option_and_recurses(self):
        from sse_multivector import hierarchy_generation as generation

        spec = self.prepare(count=43, bend=True)
        cfg = json.loads(spec.read_text())
        cfg['generation_policy'] = 'hierarchy-generation-v5.1'
        self.native.write('v5.json', cfg)
        state = self.construct(spec)
        family = state['families'][0]
        first = family['rounds'][0]
        self.assertTrue(first['unassigned'])
        self.assertTrue(set(first['unassigned']) <= set(first['after']))
        self.assertTrue(set(first['unassigned']) <= set(family['rounds'][1]['current']))
        self.assertEqual(state['v5']['eligible_ids'], family['original_ids'])
        self.assertGreater(len(state['families']), 1)
        self.assertTrue(any(n['parents'] for n in state['nodes']))
        self.assertEqual(generation.summary(state)['scope'],
                         'recursive fresh HDBSCAN trees with group leaves')
        generation.check_state(state)
        from sse_multivector.canonical_hierarchy_viewer import export_viewer
        viewer = export_viewer(self.native.root/'v5', self.native.root/'v51-viewer')
        self.assertEqual(len(state['note_ids']), 43)
        self.assertEqual(viewer['note_count'], 41)

    def test_v51_and_v52_reuse_saved_v5_bootstrap_without_mutating_the_source(self):
        from sse_multivector import hierarchy_generation as generation

        spec = self.prepare()
        source = self.construct(spec)
        source_path = self.native.root/'v5/state.json'
        before = source_path.read_bytes()
        calls = self.native.calls()
        cfg = json.loads(spec.read_text())
        cfg['bootstrap_hierarchy'] = str(source_path)
        for version in ('v5.1', 'v5.2', 'v5.3'):
            with self.subTest(version=version):
                cfg['generation_policy'] = f'hierarchy-generation-{version}'
                spec = self.native.write(f'{version}.json', cfg)
                prepared = self.native.root/version
                generation.prepare(spec, prepared)
                state = json.loads((prepared/'state.json').read_text())
                self.assertEqual(state['experiments'][0], source['experiments'][0])
                self.assertEqual(state['vectors'], source['vectors'])
                self.assertEqual(state['encodings'], source['encodings'])
                self.assertEqual(self.native.calls(), calls)
                self.assertEqual(source_path.read_bytes(), before)
                generation.check_state(state)

    def test_v51_and_v52_cannot_disable_their_eligibility_rule(self):
        from sse_multivector import hierarchy_generation as generation

        spec = self.prepare()
        cfg = json.loads(spec.read_text())
        for policy in ('hierarchy-generation-v5.1', 'hierarchy-generation-v5.2',
                       'hierarchy-generation-v5.3'):
            with self.subTest(policy=policy):
                cfg.update(generation_policy=policy,
                           v5_options=dict(include_original_unassigned=False))
                self.native.write('v5.json', cfg)
                with self.assertRaisesRegex(ValueError, 'invalid hierarchy generation spec'):
                    generation.prepare(spec, self.native.root/'invalid')

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

    def test_v53_preserves_empty_subject_notes_without_blocking_other_notes(self):
        from sse_multivector import hierarchy_generation as generation
        spec = self.prepare(count=9)
        cfg = json.loads(spec.read_text())
        cfg['generation_policy'] = 'hierarchy-generation-v5.3'
        del cfg['bootstrap_hierarchy']
        corpus_path = (spec.parent/cfg['corpus']).resolve()
        corpus = json.loads(corpus_path.read_text())
        corpus['notes'].append(dict(note_id='empty', text='https://example.com/photo.png', subjects=[]))
        cfg['note_ids'].append('empty')
        corpus_path.write_text(json.dumps(corpus))
        original_bytes = corpus_path.read_bytes()
        spec.write_text(json.dumps(cfg))
        state = self.construct(spec)
        self.assertEqual(len(state['note_ids']), 10)
        self.assertEqual(len(state['originals']), 9)
        self.assertEqual(corpus_path.read_bytes(), original_bytes)
        report = generation.summary(state)
        self.assertEqual(report['notes_without_original_l1s'], ['empty'])
        self.assertIn('empty', report['notes_not_in_hierarchy'])
        self.assertEqual(len(state['experiments'][0]['inputs']), 9)
        generation.check_state(state)
        exported = json.loads(self.native.cli('export-canonical-viewer', 'v5', '--output', 'empty-subject-view').stdout)
        self.assertEqual(exported['note_count'], 9)
        self.native.cli('audit-canonical-trial', 'v5', '--output', 'empty-subject-audit.json')
        audited = json.loads((self.native.root/'empty-subject-audit.json').read_text())
        self.assertEqual(audited['note_coverage']['selected_count'], 10)
        self.assertEqual(audited['note_coverage']['reachable_count'], 9)
        self.assertEqual(audited['note_coverage']['missing'], ['empty'])

    def test_v53_rejects_a_corpus_with_no_original_subjects_before_preparing_calls(self):
        spec = self.prepare(count=9)
        cfg = json.loads(spec.read_text())
        cfg['generation_policy'] = 'hierarchy-generation-v5.3'
        del cfg['bootstrap_hierarchy']
        corpus_path = (spec.parent/cfg['corpus']).resolve()
        corpus = json.loads(corpus_path.read_text())
        for note in corpus['notes']:
            note['subjects'] = []
        corpus_path.write_text(json.dumps(corpus))
        spec.write_text(json.dumps(cfg))
        before = self.native.calls()
        result = self.native.cli('prepare-hierarchy', 'empty-v53', '--spec', spec, ok=False)
        self.assertIn('requires at least one original L1 subject', result.stderr)
        self.assertEqual(self.native.calls(), before)
        self.assertFalse((self.native.root/'empty-v53').exists())

    def test_read_only_audit_preserves_archived_source_bindings_and_rejects_tampering(self):
        state = self.construct(self.prepare(count=9))
        bound = next(p for p in state['sources'] if p.endswith('/hierarchy_generation.py'))
        archived = self.native.root/'archived-source/sse_multivector/hierarchy_generation.py'
        archived.parent.mkdir(parents=True)
        archived.write_bytes(Path(bound).read_bytes())
        state['sources'][str(archived)] = state['sources'].pop(bound)
        path = self.native.root/'v5/state.json'
        path.write_text(json.dumps(state))
        original = path.read_bytes()
        self.native.cli('audit-canonical-trial', 'v5', '--output', 'archived-audit.json')
        audited = json.loads((self.native.root/'archived-audit.json').read_text())
        self.assertEqual(audited['note_coverage']['selected_count'], 9)
        self.assertIn(str(archived), audited['sources'])
        self.assertEqual(path.read_bytes(), original)
        archived.write_bytes(archived.read_bytes()+b'\n# changed after generation\n')
        failed = self.native.cli('audit-canonical-trial', 'v5', '--output', 'tampered-audit.json', ok=False)
        self.assertIn('changed', failed.stderr)
        self.assertFalse((self.native.root/'tampered-audit.json').exists())
        self.assertEqual(path.read_bytes(), original)

    def test_v53_still_rejects_nonempty_subject_trees_with_missing_parents(self):
        spec = self.prepare(count=9)
        cfg = json.loads(spec.read_text())
        cfg['generation_policy'] = 'hierarchy-generation-v5.3'
        del cfg['bootstrap_hierarchy']
        corpus_path = (spec.parent/cfg['corpus']).resolve()
        corpus = json.loads(corpus_path.read_text())
        corpus['notes'][0]['subjects'] = [dict(number='1.1', subject='Missing parent', context='Original post')]
        corpus_path.write_text(json.dumps(corpus))
        spec.write_text(json.dumps(cfg))
        result = self.native.cli('prepare-hierarchy', 'invalid-v53', '--spec', spec, ok=False)
        self.assertIn('requires a valid original local tree', result.stderr)
        self.assertFalse((self.native.root/'invalid-v53').exists())

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
    def overlapping_sections(self, policy='hierarchy-generation-v5.2'):
        # Five siblings already cover 174 notes. Two available sections each
        # cover 33 notes, but add two and ten previously uncovered notes.
        note_ids = (list(range(174)) + list(range(31)) + [174, 175]
                    + list(range(23)) + list(range(176, 186)))
        originals = [dict(id=f'L{i+1:05d}', local=dict(note_id=f'n{n}'))
                     for i, n in enumerate(note_ids)]
        items = {o['id']: dict(original_ids=[o['id']]) for o in originals}
        existing = []
        for i in range(5):
            identifier = f'R{i+1}'
            items[identifier] = dict(owner=f'C{i+1}',
                                     original_ids=[o['id'] for o in originals[i:174:5]])
            existing.append(identifier)
        groups = [[i] for i in existing] + [
            [o['id'] for o in originals[174:207]],
            [o['id'] for o in originals[207:]],
        ]
        state = dict(generation_policy=policy, items=items, originals=originals)
        round_ = dict(current=existing + groups[-2] + groups[-1], groups=groups,
                      selection=dict(rule='trimmed-bend-10-percent-v1',
                                     sections=[dict(groups=[i+1]) for i in range(7)]))
        return state, round_

    def test_v52_selects_ten_uncovered_notes_instead_of_two_in_the_33_note_tie(self):
        from sse_multivector.hierarchy_generation_v5 import proposals
        state, round_ = self.overlapping_sections()
        result = proposals(state, round_)
        self.assertEqual([p['members'] for p in result['proposals']], [round_['groups'][-1]])

    def test_v52_prefers_more_uncovered_notes_even_when_the_section_is_smaller(self):
        from sse_multivector.hierarchy_generation_v5 import proposals
        state, round_ = self.overlapping_sections()
        # Discard the coffee section's already-covered entries: ten total/new
        # notes must still beat 33 total notes of which only two are new.
        round_['groups'][-1] = round_['groups'][-1][-10:]
        round_['current'] = [i for group in round_['groups'] for i in group]
        result = proposals(state, round_)
        self.assertEqual([p['members'] for p in result['proposals']], [round_['groups'][-1]])

    def test_v52_largest_group_fallback_also_ranks_uncovered_notes(self):
        from sse_multivector.hierarchy_generation_v5 import proposals
        state, round_ = self.overlapping_sections()
        round_['selection']['rule'] = 'largest-groups-v5'
        result = proposals(state, round_)
        self.assertEqual([p['members'] for p in result['proposals']], [round_['groups'][-1]])

    def test_v52_counts_existing_siblings_even_when_they_are_unassigned(self):
        from sse_multivector.hierarchy_generation_v5 import proposals
        state, round_ = self.overlapping_sections()
        round_['groups'] = round_['groups'][-2:]
        round_['selection']['sections'] = [dict(groups=[1]), dict(groups=[2])]
        result = proposals(state, round_)
        self.assertEqual([p['members'] for p in result['proposals']], [round_['groups'][-1]])

    def test_v52_child_lineup_ignores_coverage_in_other_branches(self):
        from sse_multivector.hierarchy_generation_v5 import proposals
        state, round_ = self.overlapping_sections()
        state['nodes'] = [dict(id=f'C{i+1}', parents=['P'],
                               original_ids=state['items'][f'R{i+1}']['original_ids'])
                          for i in range(5)]
        state['nodes'].append(dict(id='other-root', parents=[],
                                   original_ids=round_['groups'][-1]))
        result = proposals(state, round_)
        self.assertEqual([p['members'] for p in result['proposals']], [round_['groups'][-1]])

    def test_v52_preserves_saved_order_when_uncovered_note_counts_tie(self):
        from sse_multivector.hierarchy_generation_v5 import proposals
        state, round_ = self.overlapping_sections()
        for first, second in zip(round_['groups'][-2], round_['groups'][-1]):
            state['originals'][int(first[1:])-1]['local'] = dict(
                state['originals'][int(second[1:])-1]['local'])
        result = proposals(state, round_)
        self.assertEqual([p['members'] for p in result['proposals']], [round_['groups'][-2]])

    def test_v5_and_v51_preserve_total_note_ranking(self):
        from sse_multivector.hierarchy_generation_v5 import proposals
        for policy in ('hierarchy-generation-v5', 'hierarchy-generation-v5.1'):
            with self.subTest(policy=policy):
                state, round_ = self.overlapping_sections(policy)
                result = proposals(state, round_)
                self.assertEqual([p['members'] for p in result['proposals']],
                                 [round_['groups'][-2]])

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
