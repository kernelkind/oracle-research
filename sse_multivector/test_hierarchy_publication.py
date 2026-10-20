"""Compact hierarchy results through the production CLI and native runner."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import threading
import tracemalloc
import unittest
from unittest.mock import patch

from sse_multivector import test_experiment as fixtures
from sse_multivector import test_hierarchy_generation_v3 as native_fixtures


class HierarchyPublicationTests(unittest.TestCase):
    setUp = fixtures.ExperimentTests.setUp
    write = fixtures.ExperimentTests.write
    cli = fixtures.ExperimentTests.cli

    def saved(self):
        directory = self.root / 'saved'
        directory.mkdir()
        corpus = self.write('posts.json', {'notes': []})
        state = dict(schema_version=3, status='constructing',
            generation_policy='hierarchy-generation-v3', corpus=str(corpus),
            note_ids=['post-b', 'post-a', 'unrepresented'], local_schema_version=4,
            max_siblings=6, min_notes=2,
            nodes=[dict(id='C1', subject='Food', meaning='Food and drink.', parents=[],
                        entries=[dict(note_id='post-a'), dict(note_id='post-b')]),
                   dict(id='C2', subject='Tea', meaning='Tea as a drink.', parents=['C1'],
                        entries=[dict(note_id='post-b')])],
            sources={str(corpus): hashlib.sha256(corpus.read_bytes()).hexdigest(),
                     '/private/source/sse_multivector/hierarchy_generation.py': 'ab'*32,
                     '/private/prompt.md': 'cd'*32},
            bootstrap_spec=dict(prompt=dict(id='Bootstrap-fixture-v1', path='/private/prompt.md'),
                runner=dict(provider='fixture', model='fixture/model', reasoning_effort='low',
                            auth_file='/private/auth.json', api_key='SECRET',
                            endpoint='https://user:password@example.invalid')),
            vectors={'INTERNAL VECTOR': [1, 2]},
            experiments=[dict(answers={'INTERNAL ANSWER': 'DO NOT EXPORT'})])
        self.write('saved/state.json', state)
        return directory

    def test_cli_exports_final_graph_selection_and_allowlisted_settings_without_sources(self):
        directory = self.saved()
        original = (directory/'state.json').read_bytes()
        # The final graph and recorded identities suffice; this is not a replay
        # of the original whole-file receipt verifier.
        (self.root/'posts.json').unlink()
        self.cli('export-hierarchy-results', 'saved', '--output', 'published')
        output = self.root/'published'
        self.assertEqual({p.name for p in output.iterdir()},
                         {'experiment.json', 'input-note-ids.txt', 'hierarchy.jsonl'})
        record = json.loads((output/'experiment.json').read_text())
        self.assertEqual(record['status'], 'constructing')
        self.assertEqual(record['execution_status'], 'not_recorded')
        self.assertEqual(record['input']['count'], 3)
        self.assertEqual(record['outcome'], dict(nodes=2, roots=1, represented_notes=2))
        self.assertEqual(record['prompts']['bootstrap']['id'], 'Bootstrap-fixture-v1')
        self.assertEqual(record['prompts']['bootstrap']['sha256'], 'cd'*32)
        self.assertEqual(record['input']['subject_prompt_versions'], None)
        self.assertIn('sse_multivector/hierarchy_publication.py', record['exporter']['sources'])
        self.assertEqual((output/'input-note-ids.txt').read_text(),
                         'post-b\npost-a\nunrepresented\n')
        events = [json.loads(line) for line in (output/'hierarchy.jsonl').read_text().splitlines()]
        self.assertEqual(len(events), 3)
        self.assertEqual(events[0]['content'], 'Tea as a drink.')
        self.assertEqual(events[-1]['kind'], 18680)
        exported = b''.join(p.read_bytes() for p in output.iterdir())
        for omitted in (b'/private/', b'SECRET', b'password', b'INTERNAL', b'auth_file'):
            self.assertNotIn(omitted, exported)
        for name, digest in record['files'].items():
            self.assertEqual(hashlib.sha256((output/name).read_bytes()).hexdigest(), digest)
        self.assertEqual((directory/'state.json').read_bytes(), original)
        self.assertEqual(fixtures.ExperimentTests.calls(self), [])

    def test_reexport_is_unchanged_and_resume_refreshes_the_same_output(self):
        directory = self.saved()
        self.cli('export-hierarchy-results', 'saved', '--output', 'published')
        output = self.root/'published'
        before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in output.iterdir()}
        self.cli('export-hierarchy-results', 'saved', '--output', 'published')
        self.assertEqual(before,
            {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in output.iterdir()})
        state = json.loads((directory/'state.json').read_text())
        state['status'] = 'complete'
        state['nodes'][1]['meaning'] = 'A revised final definition.'
        self.write('saved/state.json', state)
        self.cli('export-hierarchy-results', 'saved', '--output', 'published')
        record = json.loads((output/'experiment.json').read_text())
        self.assertEqual(record['execution_status'], 'not_recorded')
        self.assertEqual(record['status'], 'complete')
        self.assertIn('A revised final definition.', (output/'hierarchy.jsonl').read_text())

    def test_invalid_graph_or_unrelated_destination_leaves_existing_results_intact(self):
        directory = self.saved()
        self.cli('export-hierarchy-results', 'saved', '--output', 'published')
        output = self.root/'published'
        before = {p.name: p.read_bytes() for p in output.iterdir()}
        state = json.loads((directory/'state.json').read_text())
        state['nodes'][0]['parents'] = ['C2']
        self.write('saved/state.json', state)
        self.cli('export-hierarchy-results', 'saved', '--output', 'published', ok=False)
        self.assertEqual(before, {p.name:p.read_bytes() for p in output.iterdir()})
        (self.root/'unrelated').mkdir()
        (self.root/'unrelated/keep.txt').write_text('Keep me')
        self.cli('export-hierarchy-results', 'saved', '--output', 'unrelated', ok=False)
        self.assertEqual((self.root/'unrelated/keep.txt').read_text(), 'Keep me')

    def test_separate_runs_with_the_same_directory_name_cannot_overwrite_one_another(self):
        import shutil
        first = self.saved()
        second = self.root/'other'/'saved'
        shutil.copytree(first, second)
        self.cli('export-hierarchy-results', first, '--output', 'published')
        output = self.root/'published'
        original = {p.name:p.read_bytes() for p in output.iterdir()}
        result = self.cli('export-hierarchy-results', second, '--output', 'published', ok=False)
        self.assertIn('different experiment', result.stderr)
        self.assertEqual(original, {p.name:p.read_bytes() for p in output.iterdir()})

    def test_legacy_preparations_sharing_a_spec_and_history_root_remain_distinct(self):
        first = self.saved()
        state = json.loads((first/'state.json').read_text())
        state.update(definition='/private/common/spec.json', history_root='/private/shared-history')
        self.write('saved/state.json', state)
        second = self.root/'other'/'saved'
        second.mkdir(parents=True)
        (second/'state.json').write_text(json.dumps(state))
        self.cli('export-hierarchy-results', first, '--output', 'published')
        output = self.root/'published'
        original = {p.name:p.read_bytes() for p in output.iterdir()}

        refused = self.cli('export-hierarchy-results', second, '--output', 'published', ok=False)

        self.assertIn('different experiment', refused.stderr)
        self.assertEqual(original, {p.name:p.read_bytes() for p in output.iterdir()})

    def test_concurrent_refreshes_leave_payloads_bound_to_one_complete_record(self):
        from sse_multivector import hierarchy_publication as publication

        first = self.saved()
        state = json.loads((first/'state.json').read_text())
        state['publication_id'] = '24133e72-eb61-4e54-83d1-57cdf0b6fd02'
        self.write('saved/state.json', state)
        output = self.root/'published'
        publication.export_results(first, output)
        second = self.root/'copy'/'saved'
        second.mkdir(parents=True)
        for directory, label in [(first, 'first'), (second, 'second')]:
            changed = json.loads(json.dumps(state))
            changed['note_ids'].append(label+'-only')
            changed['nodes'][0]['meaning'] = label+' definition'
            (directory/'state.json').write_text(json.dumps(changed))
        first_payload, second_progress, release_first = (
            threading.Event(), threading.Event(), threading.Event())
        errors = []
        replace, flock = publication.os.replace, publication.fcntl.flock

        def replaced(source, destination):
            replace(source, destination)
            if (threading.current_thread().name == 'first-publication-writer'
                    and Path(destination).name == 'hierarchy.jsonl'):
                first_payload.set()
                if not release_first.wait(5):
                    raise RuntimeError('first exporter was not released')

        def locking(*args):
            if threading.current_thread().name == 'second-publication-writer':
                # A serialized second writer reaches its lock, then waits.
                second_progress.set()
            return flock(*args)

        def export(directory):
            try:
                publication.export_results(directory, output)
            except BaseException as error:
                errors.append(error)
            finally:
                # Without serialization it instead completes while the first
                # writer remains paused, exposing the original mixed payloads.
                if directory == second:
                    second_progress.set()

        threads = [threading.Thread(target=export, args=(first,), name='first-publication-writer'),
                   threading.Thread(target=export, args=(second,), name='second-publication-writer')]
        with patch.object(publication.os, 'replace', side_effect=replaced), \
                patch.object(publication.fcntl, 'flock', side_effect=locking):
            try:
                threads[0].start()
                self.assertTrue(first_payload.wait(5), 'first exporter did not replace its hierarchy')
                threads[1].start()
                self.assertTrue(second_progress.wait(5), 'second exporter made no progress')
            finally:
                release_first.set()
                for thread in threads:
                    if thread.ident is not None:
                        thread.join(5)
        self.assertFalse(any(thread.is_alive() for thread in threads), 'publication writer deadlocked')
        self.assertEqual(errors, [])
        record = json.loads((output/'experiment.json').read_text())
        self.assertEqual(set(record['files']), {'hierarchy.jsonl', 'input-note-ids.txt'})
        for name, digest in record['files'].items():
            self.assertEqual(hashlib.sha256((output/name).read_bytes()).hexdigest(), digest,
                             'concurrent exporters mixed payloads from different snapshots')

    def test_numerical_binary_binding_is_preserved_without_its_local_path(self):
        directory = self.saved()
        state = json.loads((directory/'state.json').read_text())
        state['hdbscan_binary'] = '/private/bin/hdbscan'
        state['sources'][state['hdbscan_binary']] = 'ef'*32
        self.write('saved/state.json', state)
        self.cli('export-hierarchy-results', 'saved', '--output', 'published')
        record = json.loads((self.root/'published/experiment.json').read_text())
        self.assertEqual(record['code']['hdbscan_binary_sha256'], 'ef'*32)
        self.assertNotIn('/private/', json.dumps(record))

    def test_old_subjects_and_recorded_code_upgrades_remain_explicit(self):
        directory = self.saved()
        state = json.loads((directory/'state.json').read_text())
        state['publication_provenance'] = dict(subject_prompt_versions=['ASv6.99'],
            code=dict(oracle=dict(commit='01'*20, modified=False)))
        state['source_upgrades'] = [dict(
            before={'/private/old/sse_multivector/hierarchy_generation.py':'12'*32},
            after={'/private/new/sse_multivector/hierarchy_generation.py':'34'*32},
            reason='PRIVATE DIAGNOSTIC')]
        self.write('saved/state.json', state)
        self.cli('export-hierarchy-results', 'saved')
        record = json.loads((directory/'publication/experiment.json').read_text())
        self.assertTrue(record['input']['deprecated'])
        self.assertEqual(record['code']['preparation']['oracle']['commit'], '01'*20)
        self.assertEqual(record['code']['upgrades'][0]['before'][0]['sha256'], '12'*32)
        self.assertEqual(record['code']['upgrades'][0]['after'][0]['sha256'], '34'*32)
        self.assertNotIn('PRIVATE DIAGNOSTIC', json.dumps(record))
        self.assertNotIn('/private/', json.dumps(record))

    def test_large_internal_working_data_is_not_materialized_during_export(self):
        from sse_multivector import hierarchy_publication as publication
        directory = self.saved()
        path = directory/'state.json'
        prefix = path.read_bytes().rstrip()[:-1]
        row = json.dumps('x'*4096 + '🌿').encode()
        with path.open('wb') as stream:
            stream.write(prefix + b',"working_cache":[')
            for index in range(4096):
                if index:
                    stream.write(b',')
                stream.write(row)
            stream.write(b']}\n')
        expected_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        tracemalloc.start()
        try:
            publication.export_results(directory)
            _, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        self.assertLess(peak, 8*1024**2, 'export materialized internal working data')
        record = json.loads((directory/'publication/experiment.json').read_text())
        self.assertEqual(record['source_state_sha256'], expected_hash)


class HierarchyPublicationExecutionTests(unittest.TestCase):
    def setUp(self):
        self.native = native_fixtures.HierarchyGenerationV3Tests('runTest')
        self.native.setUp()
        self.addCleanup(self.native.doCleanups)

    def test_construction_prompt_jobs_are_marked_internal(self):
        spec = self.native.configure(count=2)
        self.native.cli('prepare-hierarchy', 'trial', '--spec', spec)
        state = self.native.state()
        for job in state['experiments']:
            plan = json.loads((Path(job['experiment'])/'experiment.json').read_text())['plan']
            self.assertEqual(plan.get('publication_role'), 'internal')
            self.assertFalse((Path(job['experiment'])/'publication').exists())

    def test_prepare_records_selected_subject_and_code_versions_without_paths(self):
        import uuid
        spec = self.native.configure(count=2)
        self.native.cli('prepare-hierarchy', 'trial', '--spec', spec)
        state = self.native.state()
        uuid.UUID(state['publication_id'])
        self.native.cli('prepare-hierarchy', 'independent', '--spec', spec)
        other = json.loads((self.native.root/'independent/state.json').read_text())
        self.assertNotEqual(state['publication_id'], other['publication_id'])
        provenance = state['publication_provenance']
        self.assertEqual(provenance['subject_prompt_versions'], ['ASv6.100'])
        self.assertIn('oracle', provenance['code'])
        self.assertIn('runner', provenance['code'])
        self.assertNotIn(str(self.native.root), json.dumps(provenance))

    def test_numerical_settings_are_frozen_in_preparation_and_exported_without_running(self):
        spec = self.native.prepare_v41(count=9)
        self.native.cli('prepare-hierarchy', 'numerical', '--spec', spec)
        directory = self.native.root/'numerical'
        state = json.loads((directory/'state.json').read_text())
        expected = dict(min_samples=3, min_cluster_size=2, selection_method='excess_of_mass')
        self.assertEqual(state['hdbscan_configuration'], expected)
        calls = len(self.native.calls())
        self.native.cli('export-hierarchy-results', 'numerical')
        record = json.loads((directory/'publication/experiment.json').read_text())
        self.assertEqual(record['parameters']['hdbscan_configuration'], expected)
        self.assertEqual(record['code']['hdbscan_binary_sha256'],
                         state['sources'][state['hdbscan_binary']])
        self.assertEqual(len(self.native.calls()), calls)

    def test_initial_execution_failure_and_interruption_export_without_hiding_the_error(self):
        from sse_multivector import hierarchy_generation as generation
        spec = self.native.configure(count=2)
        for name, error, expected in [('failed', RuntimeError('SECRET local failure'), 'failed'),
                                      ('stopped', KeyboardInterrupt(), 'stopped')]:
            with self.subTest(name=name):
                self.native.cli('prepare-hierarchy', name, '--spec', spec)
                directory = self.native.root/name
                with patch.object(generation, '_native_advance', side_effect=error):
                    with self.assertRaises(type(error)):
                        generation.run(directory)
                record = json.loads((directory/'publication/experiment.json').read_text())
                self.assertEqual(record['execution_status'], expected)
                self.assertEqual(record['status'], 'bootstrap')
                self.assertEqual(record['failure_type'], type(error).__name__)
                self.assertNotIn('SECRET', json.dumps(record))

    def test_native_blocked_run_exports_and_resume_replaces_partial_results(self):
        from sse_multivector import hierarchy_generation as generation
        spec = self.native.configure(count=4)
        self.native.automatic_runner()
        self.native.cli('prepare-hierarchy', 'trial', '--spec', spec)
        directory = self.native.root/'trial'
        budget = self.native.write('budget.json', dict(schema_version=1, limit=2, used=0))
        with patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.native.log), FAKE_V3='1'), \
                patch('sse_multivector.worker.OfficialSseEncoder',
                      return_value=native_fixtures.FixtureEncoder()):
            self.assertEqual(generation.run(directory, budget)['execution_status'], 'blocked')
            output = directory/'publication'
            first = json.loads((output/'experiment.json').read_text())
            self.assertEqual(first['execution_status'], 'blocked')
            frozen = json.loads(budget.read_text())
            frozen['limit'] = 20
            budget.write_text(json.dumps(frozen))
            self.assertEqual(generation.run(directory, budget)['execution_status'], 'complete')
        final = json.loads((output/'experiment.json').read_text())
        self.assertEqual(final['execution_status'], 'complete')
        self.assertEqual(final['status'], 'complete')
        self.assertGreater(final['outcome']['nodes'], 0)
        for child in directory.glob('batch-*/experiment/publication'):
            self.fail(f'Internal construction job exported separately: {child}')


if __name__ == '__main__':
    unittest.main()
