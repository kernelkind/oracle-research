"""Compact numerical exports exercise the same production entry point as runs."""
import json
from pathlib import Path
import struct
import tempfile
import tracemalloc
import unittest
import zipfile


class NumericalPublicationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def write(self, name, value):
        path = self.root/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))
        return path

    def records(self, output, name='results.jsonl'):
        return [json.loads(line) for line in (Path(output)/name).read_text().splitlines()]

    def geometric(self, method='diffusion'):
        self.write('run/configuration.json', dict(run_id='G01', method=method, config={}))
        self.write('run/hierarchy.json', dict(method=method, roots=[0],
            nodes=[dict(id=0, children=[], members=[0], note_ids=['n1'])]))
        self.write('run/evidence.json', [dict(row=0, canonical_id='v1',
            aliases=[dict(vector_id='v1', note_id='n1')])])
        return self.root/'run'

    def test_geometric_export_retains_result_and_mapping_without_coordinates_or_post_text(self):
        from sse_multivector.numerical_publication import export_results
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run = root/'run'
            run.mkdir()
            for name, value in {
                'configuration.json': dict(run_id='G01', method='diffusion', config={'epsilon': .2},
                    sources={'vectors': {'path': '/private/vectors', 'sha256': 'a'*64}},
                    elapsed_seconds=2, max_rss_kib=100),
                'hierarchy.json': dict(method='diffusion', roots=[0],
                    nodes=[dict(id=0, children=[], members=[0], note_ids=['N001'])],
                    final_coordinates=[[1234.5]]),
                'evidence.json': [dict(row=0, canonical_id='vector-a', aliases=[
                    dict(vector_id='vector-a', note_id='post-a', note_short_id='N001',
                         byte_spans=[[0, 4]], fragments=['mask'], text='Full private post')])],
            }.items():
                (run/name).write_text(json.dumps(value))
            before = {p.name: p.read_bytes() for p in run.iterdir()}

            result = export_results(run)

            output = Path(result['output'])
            self.assertEqual(output, run/'publication')
            records = [json.loads(line) for line in (output/'results.jsonl').read_text().splitlines()]
            self.assertIn(dict(type='node', id=0, children=[], members=[0], note_ids=['N001']), records)
            mapping = [json.loads(line) for line in (output/'inputs.jsonl').read_text().splitlines()]
            self.assertEqual(mapping[0]['canonical_id'], 'vector-a')
            self.assertEqual(mapping[0]['aliases'][0]['note_id'], 'post-a')
            published = ''.join(p.read_text() for p in output.iterdir())
            self.assertNotIn('/private/', published)
            self.assertNotIn('Full private post', published)
            self.assertNotIn('1234.5', published)
            self.assertEqual(before, {name: (run/name).read_bytes() for name in before})

    def test_merge_history_is_final_result_and_has_its_canonical_alias_mapping(self):
        from sse_multivector.numerical_publication import export_results
        path = self.write('M01.json', dict(schema_version='merge-rule-experiment-v1',
            canonical_unique_ids=['a', 'b'], alias_groups=[['a', 'a-alias'], ['b']],
            merges=[dict(id=2, left=0, right=1, size=2, merge_score=.7)],
            distances=[[1234.5]], summary={'notes': 2}))

        output = export_results(path)['output']

        self.assertEqual(Path(output), self.root/'publication/M01')
        self.assertIn(dict(type='merge', id=2, left=0, right=1, size=2, merge_score=.7),
                      self.records(output))
        self.assertEqual(self.records(output, 'inputs.jsonl'), [
            dict(row=0, canonical_id='a', aliases=['a', 'a-alias']),
            dict(row=1, canonical_id='b', aliases=['b'])])
        self.assertNotIn('1234.5', (Path(output)/'results.jsonl').read_text())

    def test_hidef_preserves_dag_and_empty_persistence_outcomes_without_raw_partitions(self):
        from sse_multivector.numerical_publication import export_results
        self.write('run/configuration.json', dict(schema_version='hidef-configuration-v1',
            parameters={'persistence': 5}, resolutions=[.1, 1]))
        self.write('run/hierarchy.json', dict(schema_version='containment-hierarchy-v1',
            root=2, canonical_unique_ids=['a'], alias_groups=[['a']]))
        self.write('run/strict-dag.json', dict(groups=[dict(id=0, vector_ids=[0],
            note_ids=['n1'], parents=[1, 2], children=[])]))
        self.write('run/persistent-groups.json', dict(groups=[dict(family_id=7,
            vector_ids=[], note_ids=[], support_count=5, empty_after_consensus=True)]))
        self.write('run/timings.json', dict(elapsed_seconds=1.25, peak_rss_kib=500))
        (self.root/'run/raw-partitions.json').write_text('INVALID WORKING FILE')

        output = export_results(self.root/'run')['output']

        rows = self.records(output)
        self.assertEqual(next(r for r in rows if r['type'] == 'group')['parents'], [1, 2])
        self.assertTrue(next(r for r in rows if r['type'] == 'persistent_group')['empty_after_consensus'])
        metadata = json.loads((Path(output)/'experiment.json').read_text())
        self.assertNotIn('raw-partitions.json', metadata['sources'])

    @staticmethod
    def npy(values, shape):
        header = repr(dict(descr='<f8', fortran_order=False, shape=shape)).encode()
        header += b' '*((-(10+len(header)+1)) % 64)+b'\n'
        return b'\x93NUMPY\x01\x00'+struct.pack('<H', len(header))+header+struct.pack(
            '<'+'d'*len(values), *values)

    def test_fuzzy_preserves_native_memberships_and_final_interpolation_only(self):
        from sse_multivector.numerical_publication import export_results
        run = self.geometric('fmc')
        self.write('run/native-fuzzy.json', dict(method='fmc2005_experimental_fuzzy',
            levels=[dict(level=0, membership=dict(array='array_0000', shape=[1, 2]),
                         distance=dict(array='array_0001', shape=[1, 2]))],
            transitions=[dict(level=0, interpolation=dict(array='array_0002', shape=[1, 2]),
                interpolation_before_refinement=dict(array='array_0003', shape=[1, 2]))]))
        with zipfile.ZipFile(run/'native-fuzzy-arrays.npz', 'w') as archive:
            for name, values in [('array_0000', [0, .2]), ('array_0001', [1234.5, 1234.5]),
                                 ('array_0002', [.25, .75]), ('array_0003', [6789, 6789])]:
                archive.writestr(name+'.npy', self.npy(values, (1, 2)))

        output = export_results(run)['output']

        rows = self.records(output)
        membership = next(r for r in rows if r.get('role') == 'membership' and r['type'] == 'fuzzy_row')
        self.assertEqual(membership['columns'], [1])
        self.assertEqual(membership['values'], [.2])
        interpolation = next(r for r in rows if r.get('role') == 'interpolation' and r['type'] == 'fuzzy_row')
        self.assertEqual(interpolation['values'], [.25, .75])
        self.assertEqual(next(r for r in rows if r['type'] == 'node')['representation'], 'hard_projection')
        text = (Path(output)/'results.jsonl').read_text()
        self.assertNotIn('1234.5', text)
        self.assertNotIn('6789', text)
        before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in Path(output).iterdir()}
        values = {name: json.loads((run/name).read_text()) for name in (
            'configuration.json', 'hierarchy.json', 'evidence.json', 'native-fuzzy.json')}
        from unittest.mock import patch
        with patch.dict('sys.modules', {'ijson': None}):
            export_results(run, source_values=values)
        self.assertEqual(before, {p.name: (p.read_bytes(), p.stat().st_mtime_ns)
                                  for p in Path(output).iterdir()})

    def test_performance_preserves_measurements_and_incomplete_status_without_checkpoint(self):
        from sse_multivector.numerical_publication import export_results
        self.write('benchmark/report.json', dict(schema_version=1, workload='synthetic tokens',
            config={'model': 'example/model', 'pointer_config': '/private/model.json'},
            complete=False, checkpoint_saved=True, training=[dict(median_step_seconds=.5,
            peak_cuda_allocated_bytes=123)], checkpoint_hashes={'optimizer.pt': 'b'*64}))
        (self.root/'benchmark/checkpoint').mkdir()

        output = export_results(self.root/'benchmark')['output']

        self.assertIn(dict(type='training', median_step_seconds=.5, peak_cuda_allocated_bytes=123),
                      self.records(output))
        meta = json.loads((Path(output)/'experiment.json').read_text())
        self.assertEqual(meta['status'], 'incomplete')
        self.assertNotIn('checkpoint_hashes', (Path(output)/'results.jsonl').read_text())
        self.assertNotIn('/private', (Path(output)/'experiment.json').read_text())

    def test_saved_rust_reports_preserve_final_schedules_partitions_and_roots(self):
        from sse_multivector.numerical_publication import export_results
        reports = {
            'partition': dict(pilot_id='sse-fine-region-partition-v1', schema_version=1,
                vectors=[dict(ordinal=0, note_id='post-a', embedding=[1234.5])],
                resolutions=[dict(level={'cosine': .4}, complete_linkage={'regions': [{'members': [0]}]})]),
            'hierarchy': dict(pilot_id='sse-fine-region-hierarchy-v2', schema_version=2,
                hierarchy=dict(fine_segments=[{'members': [0]}], merges=[], root={'leaf': 0})),
            'scc': dict(pilot_id='scc-hierarchy-preflight-v1', schema_version=1,
                report=dict(variants=[dict(schedule_id='fixed', hierarchy={'roots': [0]},
                                           node_comparisons=[{'scc_merge_index': 1}])])),
        }
        for name, report in reports.items():
            with self.subTest(name=name):
                path = self.write(name+'.json', report)
                output = export_results(path, family='fine-region')['output']
                self.assertTrue(self.records(output))
                self.assertNotIn('1234.5', ''.join(p.read_text() for p in Path(output).iterdir()))

    def test_pair_scores_reject_unknown_schema_instead_of_copying_arbitrary_json(self):
        from sse_multivector.numerical_publication import export_results
        self.write('pairs/config.json', dict(model_id='test/model'))
        self.write('pairs/scores.json', [dict(premise='Mask meaning', hypothesis='Parent', score=.8)])
        result = export_results(self.root/'pairs', family='pair-scores')
        self.assertEqual(self.records(result['output'])[0]['score'], .8)
        old = (Path(result['output'])/'results.jsonl').read_bytes()
        self.write('pairs/scores.json', [dict(unknown='not a numerical result')])
        with self.assertRaisesRegex(ValueError, 'unsupported numerical pair-score'):
            export_results(self.root/'pairs', family='pair-scores')
        self.assertEqual((Path(result['output'])/'results.jsonl').read_bytes(), old)

    def test_native_decisions_preserve_complete_generated_labels_without_input_token_arrays(self):
        from sse_multivector.numerical_publication import export_results
        self.write('native/config.json', dict(model_id='true/model'))
        row = dict(id='case-1', a='Parent', b='Child', generated_text='0',
                   generated_token_ids=[0, 3, 632, 1], eos_terminated=True, predicted=False,
                   expected=True, model_input='Repeated rendered request', token_ids=[777777])
        (self.root/'native/scores.jsonl').write_text(json.dumps(row)+'\n')
        output = export_results(self.root/'native', family='pair-scores')['output']
        result = self.records(output)[0]
        self.assertEqual(result['generated_token_ids'], [0, 3, 632, 1])
        self.assertEqual(result['predicted'], False)
        self.assertNotIn('token_ids', result)
        self.assertNotIn('Repeated rendered request', (Path(output)/'results.jsonl').read_text())

    def test_affinity_neighborhoods_are_final_results_without_all_pairs_or_vectors(self):
        from sse_multivector.numerical_publication import export_results
        self.write('affinity/config.json', dict(run_id='PPR01', condition='base', model_id='test/model'))
        self.write('affinity/inputs.json', [dict(row=0, note='N001', subject='Coffee')])
        self.write('affinity/neighborhoods.json', {'0': {'cosine': [dict(row=1, note='N002', score=.8)]}})
        (self.root/'affinity/scores.npz').write_text('unnecessary working table')
        (self.root/'affinity/vectors.npy').write_text('unnecessary vectors')
        output = export_results(self.root/'affinity', family='pair-scores')['output']
        self.assertEqual(self.records(output), [dict(type='neighbors', query='0', metric='cosine',
            neighbors=[dict(row=1, note='N002', score=.8)])])
        self.assertEqual(self.records(output, 'inputs.jsonl')[0]['subject'], 'Coffee')
        metadata = json.loads((Path(output)/'experiment.json').read_text())
        self.assertNotIn('scores.npz', metadata['sources'])

    def test_reexport_is_stable_and_refuses_other_sources_and_ancestor_destinations(self):
        from sse_multivector.numerical_publication import export_results
        run = self.geometric()
        output = Path(export_results(run)['output'])
        before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in output.iterdir()}
        export_results(run)
        self.assertEqual(before, {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in output.iterdir()})
        with self.assertRaisesRegex(ValueError, 'source directory'):
            export_results(run, self.root)
        with self.assertRaisesRegex(ValueError, 'source directory'):
            export_results(run, run)
        for path in run.iterdir():
            if path.is_file():
                self.write('other/'+path.name, json.loads(path.read_text()))
        with self.assertRaisesRegex(ValueError, 'different source'):
            export_results(self.root/'other', output)

    def test_symlink_publication_destination_is_refused(self):
        from sse_multivector.numerical_publication import export_results
        run = self.geometric()
        output = Path(export_results(run)['output'])
        alias = self.root/'alias'
        alias.symlink_to(output, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            export_results(run, alias)

    def test_large_discarded_coordinates_do_not_expand_in_memory(self):
        from sse_multivector.numerical_publication import export_results
        run = self.geometric()
        with (run/'hierarchy.json').open('w') as stream:
            stream.write('{"roots":[0],"nodes":[{"id":0,"children":[],"members":[0]}],"final_coordinates":[')
            for index in range(500000):
                stream.write((',' if index else '')+'1234.5')
            stream.write(']}')
        tracemalloc.start()
        try:
            result = export_results(run)
            _, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        self.assertLess(peak, 5*1024*1024)
        self.assertLess((Path(result['output'])/'results.jsonl').stat().st_size, 1000)

    def test_comparison_export_retains_measured_differences_and_qualifications(self):
        from sse_multivector.numerical_publication import export_results
        path = self.write('comparison.json', dict(schema_version='hidef-graph-policy-comparison-v1',
            validation={'all_strict_dags_verified': True}, interpretation='Counts are not semantic scores.',
            parameters_except_seed={'persistence': 5},
            correspondence=[dict(group_id=1, matches=[dict(group_id=2, jaccard=.5)])],
            runs=[dict(seed=123, groups=4)]))
        output = export_results(path, family='comparison')['output']
        rows = self.records(output)
        self.assertEqual(rows[0]['interpretation'], 'Counts are not semantic scores.')
        self.assertEqual(next(r for r in rows if r['type'] == 'correspondence')['group_id'], 1)

    def test_hidef_final_writer_automatically_calls_the_offline_export_path(self):
        from unittest.mock import MagicMock, patch
        from sse_multivector import hidef_experiment as hidef
        graph_file = self.root/'graph.net'
        graph_file.write_text('*Vertices 1\n0 "v0"\n*Edges\n')
        graph = MagicMock()
        graph.vcount.return_value = 1
        graph.ecount.return_value = 0
        graph.es.__getitem__.return_value = []
        reference = dict(sources={}, canonical_unique_ids=['v0'], alias_groups=[['v0']])
        self.write('hierarchy.json', reference)
        arguments = ['--graph-directory', str(self.root), '--data-directory', str(self.root),
                     '--output', str(self.root/'run')]
        with (patch.object(hidef, 'dependency_provenance', return_value={}),
              patch.object(hidef, 'load_inputs', return_value=(graph, reference, [{'n0'}], graph_file)),
              patch.object(hidef, 'apply_graph_policy', return_value=(graph, {'retained_original_edge_indices': []})),
              patch.object(hidef, 'resolution_schedule', return_value=([1.], MagicMock())),
              patch.object(hidef, 'discover', return_value=(MagicMock(), [], [], MagicMock())),
              patch.object(hidef, 'persistent_groups', return_value=[]),
              patch.object(hidef, 'verify_weaver', return_value={'status': 'verified'}),
              patch('builtins.print')):
            hidef.main(arguments)
        metadata = json.loads((self.root/'run/publication/experiment.json').read_text())
        self.assertEqual(metadata['family'], 'hidef')
        self.assertEqual(self.records(self.root/'run/publication', 'inputs.jsonl'),
                         [dict(row=0, canonical_id='v0', aliases=['v0'])])

    def test_unknown_nested_parameter_fields_cannot_publish_credentials(self):
        from sse_multivector.numerical_publication import export_results
        sentinel = 'PRIVATE-CREDENTIAL-SENTINEL'
        run = self.geometric()
        self.write('run/configuration.json', dict(method='diffusion',
            config=dict(epsilon=.2, headers={'Authorization': sentinel},
                        endpoint='https://user:'+sentinel+'@provider.example',
                        future_settings={'authorization': sentinel}),
            sources={'vectors': dict(path='/private/vectors', sha256='a'*64, extra=sentinel)},
            dependencies=dict(authorization=sentinel),
            code={'geometric_experiment.py': 'b'*64, 'extra': {'headers': sentinel}}))
        self.write('run/hierarchy.json', dict(roots=[0],
            nodes=[dict(id=0, children=[], members=[0])],
            config=dict(epsilon=.2, headers={'Authorization': sentinel}),
            diagnostics=dict(n_rows=1, extension=dict(headers=sentinel))))
        output = export_results(run)['output']
        self.assertNotIn(sentinel, ''.join(p.read_text() for p in Path(output).iterdir()))
        metadata = json.loads((Path(output)/'experiment.json').read_text())
        self.assertEqual(metadata['parameters']['config']['epsilon'], .2)
        self.assertTrue(metadata['omitted_settings'])

        self.write('benchmark/report.json', dict(workload='synthetic tokens', complete=True,
            config=dict(model='example/model', lengths=[32], unknown={'headers': sentinel}),
            versions=dict(torch='2.0', unknown={'authorization': sentinel}),
            system=dict(gpu='Example GPU', endpoint=sentinel), training=[]))
        output = export_results(self.root/'benchmark')['output']
        self.assertNotIn(sentinel, ''.join(p.read_text() for p in Path(output).iterdir()))

    def test_scientific_free_text_is_preserved_without_generic_string_redaction(self):
        from sse_multivector.numerical_publication import export_results
        interpretation = '/ means division in this scientific finding.'
        path = self.write('comparison.json', dict(schema_version='hidef-graph-policy-comparison-v1',
            interpretation=interpretation, runs=[]))
        output = export_results(path, family='comparison')['output']
        self.assertEqual(self.records(output)[0]['interpretation'], interpretation)

    def test_pair_configuration_keeps_known_settings_without_unknown_nested_credentials(self):
        from sse_multivector.numerical_publication import export_results
        sentinel = 'PRIVATE-PAIR-CREDENTIAL-SENTINEL'
        self.write('pairs/config.json', dict(model_id='test/model', max_input_tokens=512,
            packages=dict(torch='2.0', extension={'authorization': sentinel}),
            pooling=dict(pooling_mode_mean_tokens=True, endpoint=sentinel),
            model_labels={'0': 'contradiction', '1': 'entailment', 'headers': sentinel},
            label_token_ids={'0': [3, 632], '1': [209], 'authorization': sentinel},
            generation=dict(do_sample=False, max_new_tokens=3, headers={'token': sentinel})))
        self.write('pairs/scores.json', [dict(premise='Child', hypothesis='Parent', score=.8)])

        output = Path(export_results(self.root/'pairs', family='pair-scores')['output'])

        self.assertNotIn(sentinel, ''.join(path.read_text() for path in output.iterdir()))
        metadata = json.loads((output/'experiment.json').read_text())
        settings = metadata['parameters']
        self.assertEqual(settings['packages'], {'torch': '2.0'})
        self.assertEqual(settings['pooling'], {'pooling_mode_mean_tokens': True})
        self.assertEqual(settings['model_labels'], {'0': 'contradiction', '1': 'entailment'})
        self.assertEqual(settings['label_token_ids'], {'0': [3, 632], '1': [209]})
        self.assertEqual(settings['generation'], {'do_sample': False, 'max_new_tokens': 3})
        self.assertTrue(metadata['omitted_settings'])


if __name__ == '__main__':
    unittest.main()
