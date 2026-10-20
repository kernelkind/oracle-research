"""Saved SSE diagnostics use the existing offline numerical export path."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import subprocess
import sys


class RepresentationPublicationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def save(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def fixture(self):
        source = self.root/'study'
        experiment_id = 'mask-fidelity-location-v1'
        proposal = dict(schema_version=1, experiment_id=experiment_id,
            review_status='approved', question='Does context affect this manually selected span?',
            notes=[dict(id='N1', text='café', mask='café')])
        proposal_sha = self.save(source/'experiment.json', proposal)
        request = dict(schema_version=1, proposal_sha256=proposal_sha,
            notes=[dict(note_id='a'*64, text='café', subjects=[
                dict(subject_id='b'*16, byte_spans=[[0, 5]])])])
        request_sha = self.save(source/'worker-input.json', request)
        model = dict(base_model='sentence-transformers/sentence-t5-base', dimensions=2,
                     maximum_tokens=512, pooling='selected-contextual-token-mean-linear-relu-linear-v1')
        settings = dict(schema_version=1, request_sha256=request_sha,
            request_path='/private/request', output_path='/private/output',
            checkpoint_path='/private/checkpoint', base_model_artifact_path='/private/model',
            checkpoint_sha256='c'*64, base_model_artifact_tree_sha256='d'*64,
            model=model, device='cpu', container_image='image@sha256:'+'e'*64, note_batch_size=1)
        settings_sha = self.save(source/'worker-config.json', settings)
        receipt = dict(schema_version=1, proposal_sha256=proposal_sha, request_sha256=request_sha,
            checkpoint_sha256='c'*64, base_model_artifact_tree_sha256='d'*64,
            model=model, dimensions=2, device='cpu', container_image=settings['container_image'],
            note_batch_size=1, row_count=1, rows=[dict(ordinal=0, note_id='a'*64,
                subject_id='b'*16, token_count=2, selected_token_indices=[0])],
            runtime=dict(worker_sha256='f'*64, packages={'torch':'1'}, python='3.12'),
            vector_format='row-major-f32le-v1', files={
                'raw-vectors.f32le':dict(bytes=8,sha256='1'*64)})
        receipt_sha = self.save(source/'result/worker-receipt.json', receipt)
        analysis = dict(schema_version=1, experiment_id=experiment_id,
            vector_order=['N1'], dimensions=2, cosine_matrix=[[1.0000000000000002]],
            primary_comparisons=[], overall_passed=True)
        analysis_sha = self.save(source/'result/analysis.json', analysis)
        self.save(source/'result/manifest.json', dict(schema_version=1,
            experiment_id=experiment_id,experiment_sha256=proposal_sha,
            worker_input_sha256=request_sha,worker_config_sha256=settings_sha,
            files={name:dict(sha256=sha,bytes=(source/'result'/name).stat().st_size)
                   for name,sha in [('analysis.json',analysis_sha),('worker-receipt.json',receipt_sha)]},
            worker_sha256='f'*64,checkpoint_sha256='c'*64))
        return source

    def records(self, output, name):
        return [json.loads(line) for line in (Path(output)/name).read_text().splitlines()]

    def modify(self, path, change):
        value = json.loads(path.read_text())
        change(value)
        self.save(path,value)

    def rebind(self, source):
        """Keep synthetic fixture receipts coherent after an intentional test edit."""
        digest = lambda name: hashlib.sha256((source/name).read_bytes()).hexdigest()
        self.modify(source/'worker-input.json', lambda x:x.update(proposal_sha256=digest('experiment.json')))
        self.modify(source/'worker-config.json',lambda x:x.update(request_sha256=digest('worker-input.json')))
        self.modify(source/'result/worker-receipt.json',lambda x:x.update(
            proposal_sha256=digest('experiment.json'),request_sha256=digest('worker-input.json')))
        def manifest(x):
            x.update(experiment_sha256=digest('experiment.json'),
                worker_input_sha256=digest('worker-input.json'),worker_config_sha256=digest('worker-config.json'))
            for name in ('analysis.json','worker-receipt.json'):
                x['files'][name] = dict(sha256=digest('result/'+name),bytes=(source/'result'/name).stat().st_size)
        self.modify(source/'result/manifest.json',manifest)

    def context_fixture(self):
        mask = self.fixture()
        source = self.root/'context-result'
        source.mkdir()
        receipt = json.loads((mask/'result/worker-receipt.json').read_text())
        contract = {key:receipt[key] for key in ('checkpoint_sha256','base_model_artifact_tree_sha256',
                                               'container_image','device','note_batch_size','dimensions')}
        contract.update(receipt['model'])
        contract['worker_sha256'] = receipt['runtime']['worker_sha256']
        notes_sha = self.save(self.root/'context-counterfactual-source-notes-v1.json',
            dict(schema_version=1,evidence_id='source-notes',notes=[dict(note_id='9'*64,text='café')]))
        fixture = dict(schema_version=1,fixture_id='sse-context-counterfactual-v1',
            review_status='approved',question='context',sse_execution_contract=contract,
            counts=dict(total_vectors=1,target_vectors=1,reference_vectors=0),
            source_artifacts=[dict(path='sse_multivector/context-counterfactual-source-notes-v1.json',
                                  sha256=notes_sha)],reference_groups=[],mixed_note_cases=[],
            context_resolution_cases=[],self_contained_cases=[dict(case_id='case',variants=[
                dict(fixture_note_id='target',text='café',mask=[dict(text='café',occurrence=1)])])])
        fixture_sha = self.save(self.root/'context-counterfactual-v1.json',fixture)
        receipt.update(proposal_sha256=fixture_sha,request_sha256='8'*64)
        receipt_sha = self.save(source/'worker-receipt.json',receipt)
        analysis = dict(schema_version=1,fixture_id=fixture['fixture_id'],fixture_sha256=fixture_sha,
            request_sha256='8'*64,dimensions=2,predictions=[dict(target_id='target',target_ordinal=0,
                 reference_cosines={},group_medians={},comparisons=[],passed=True)],verdicts={})
        analysis_sha = self.save(source/'analysis.json',analysis)
        self.save(source/'manifest.json',dict(schema_version=1,fixture_id=fixture['fixture_id'],
            fixture_sha256=fixture_sha,request_sha256='8'*64,compile_manifest_sha256='7'*64,
            files={name:dict(sha256=sha,bytes=(source/name).stat().st_size)
                   for name,sha in [('analysis.json',analysis_sha),('worker-receipt.json',receipt_sha)]}))
        return source

    def test_export_preserves_native_analysis_and_manual_fixture_with_bound_sources(self):
        from sse_multivector.numerical_publication import export_results
        source = self.fixture()
        original = {p.relative_to(source):p.read_bytes() for p in source.rglob('*') if p.is_file()}

        output = Path(export_results(source, family='representation')['output'])

        self.assertEqual({p.name for p in output.iterdir()},
                         {'experiment.json','inputs.jsonl','results.jsonl'})
        results = self.records(output,'results.jsonl')
        self.assertEqual(results[0]['data'], json.loads((source/'result/analysis.json').read_text()))
        self.assertEqual(results[0]['data']['cosine_matrix'], [[1.0000000000000002]])
        inputs = self.records(output,'inputs.jsonl')
        self.assertEqual(inputs[0]['data']['review_status'], 'approved')
        self.assertEqual(inputs[1]['data']['notes'][0]['subjects'][0]['byte_spans'], [[0,5]])
        metadata = json.loads((output/'experiment.json').read_text())
        self.assertEqual(metadata['input']['subject_generation'], 'not_applicable')
        self.assertEqual(metadata['input']['span_origin'], 'manually_supplied')
        self.assertNotIn('/private/', ''.join(p.read_text() for p in output.iterdir()))
        for path,raw in original.items():
            self.assertEqual((source/path).read_bytes(),raw)

    def test_cli_uses_representation_family(self):
        source = self.fixture()
        result = subprocess.run([sys.executable,'sse_multivector/experiment.py',
            'export-numerical-results',str(source),'--family','representation'],
            capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertTrue((source/'publication/experiment.json').is_file())

    def test_selected_file_hash_mismatch_is_rejected_before_publication(self):
        from sse_multivector.numerical_publication import export_results
        source = self.fixture()
        self.modify(source/'result/analysis.json',lambda x:x.update(overall_passed=False))
        with self.assertRaisesRegex(ValueError,'sha256 binding mismatch'):
            export_results(source,family='representation')
        self.assertFalse((source/'publication').exists())

    def test_input_hash_and_configuration_hash_mismatches_are_rejected(self):
        from sse_multivector.numerical_publication import export_results
        for name in ('worker-input.json','worker-config.json'):
            with self.subTest(name=name):
                source = self.fixture()
                self.modify(source/name,lambda x:x.update(schema_version=2))
                with self.assertRaises(ValueError):
                    export_results(source,family='representation')

    def test_utf8_split_and_invalid_spans_rejected_with_coherent_hashes(self):
        from sse_multivector.numerical_publication import export_results
        for spans in ([[0,4]],[[0,6]],[[1,2],[0,1]],[[0,0]]):
            with self.subTest(spans=spans):
                source = self.fixture()
                self.modify(source/'worker-input.json',lambda x:x['notes'][0]['subjects'][0].update(byte_spans=spans))
                self.rebind(source)
                with self.assertRaisesRegex(ValueError,'byte span'):
                    export_results(source,family='representation')

    def test_receipt_row_identity_mismatch_rejected(self):
        from sse_multivector.numerical_publication import export_results
        source = self.fixture()
        self.modify(source/'result/worker-receipt.json',lambda x:x['rows'][0].update(subject_id='2'*16))
        self.rebind(source)
        with self.assertRaisesRegex(ValueError,'row identity mismatch'):
            export_results(source,family='representation')

    def test_private_worker_configuration_omitted_but_runtime_versions_retained(self):
        from sse_multivector.numerical_publication import export_results
        source = self.fixture()
        self.modify(source/'worker-config.json',lambda x:x.update(
            authorization='PRIVATE_CANARY',headers={'X':'PRIVATE_CANARY'}))
        self.modify(source/'result/worker-receipt.json',lambda x:x['files']['raw-vectors.f32le'].update(
            secret='PRIVATE_CANARY'))
        self.rebind(source)
        output = Path(export_results(source,family='representation')['output'])
        published = ''.join(p.read_text() for p in output.iterdir())
        self.assertNotIn('PRIVATE_CANARY',published)
        metadata = json.loads((output/'experiment.json').read_text())
        self.assertEqual(metadata['receipt']['runtime']['python'],'3.12')
        self.assertEqual(metadata['receipt']['runtime']['packages'],{'torch':'1'})

    def test_unknown_scientific_fields_fail_instead_of_being_dropped(self):
        from sse_multivector.numerical_publication import export_results
        source = self.fixture()
        self.modify(source/'result/analysis.json',lambda x:x.update(new_final_measurement=1))
        self.rebind(source)
        with self.assertRaisesRegex(ValueError,'unsupported scientific document fields'):
            export_results(source,family='representation')

    def test_nested_auth_file_is_rejected_from_scientific_documents(self):
        from sse_multivector.numerical_publication import export_results
        source = self.fixture()
        self.modify(source/'experiment.json',lambda x:x.update(
            frozen_components={'auth_file':'/home/private/auth.json'}))
        self.rebind(source)
        with self.assertRaisesRegex(ValueError,'private configuration'):
            export_results(source,family='representation')

    def test_compile_span_binding_must_match_authoritative_worker_input(self):
        from sse_multivector.numerical_publication import export_results
        source = self.fixture()
        manifest = json.loads((source/'result/manifest.json').read_text())
        compiled = {key:manifest[key] for key in
                    ('experiment_id','experiment_sha256','worker_input_sha256','worker_config_sha256')}
        compiled['rows'] = [dict(ordinal=0,experiment_note_id='N1',worker_note_id='a'*64,
            worker_subject_id='b'*16,byte_spans=[[0,4]])]
        compiled_sha = self.save(source/'compile-manifest.json',compiled)
        self.modify(source/'result/manifest.json',lambda x:x.update(compile_manifest_sha256=compiled_sha))
        with self.assertRaisesRegex(ValueError,'byte_spans binding mismatch'):
            export_results(source,family='representation')

    def test_working_vectors_and_unrequired_csv_are_not_opened(self):
        from sse_multivector.numerical_publication import export_results
        source = self.fixture()
        # These are directories, so opening either as a payload would fail.
        (source/'result/raw-vectors.f32le').mkdir()
        (source/'result/cosine-matrix.csv').mkdir()
        output = Path(export_results(source,family='representation')['output'])
        self.assertEqual(len(self.records(output,'results.jsonl')),1)

    def test_encoder_image_identity_must_agree_with_recorded_result(self):
        from sse_multivector.numerical_publication import export_results
        source = self.fixture()
        self.modify(source/'result/manifest.json',lambda x:x.update(container_image_id='sha256:'+'0'*64))
        with self.assertRaisesRegex(ValueError,'container_image_id binding mismatch'):
            export_results(source,family='representation')

    def test_compound_matrix_preserves_saved_decimal_cells_and_order(self):
        from sse_multivector.numerical_publication import export_results
        source = self.fixture()
        identity = 'mask-fidelity-compound-subject-neighborhood-v1'
        for name in ('experiment.json','result/analysis.json','result/manifest.json'):
            self.modify(source/name,lambda x:x.update(experiment_id=identity))
        matrix = source/'result/cosine-matrix.csv'
        matrix.write_text(',A01\nA01,1.000000000\n')
        self.modify(source/'result/manifest.json',lambda x:x['files'].update({matrix.name:dict(
            bytes=matrix.stat().st_size,sha256=hashlib.sha256(matrix.read_bytes()).hexdigest())}))
        self.rebind(source)
        results = self.records(export_results(source,family='representation')['output'],'results.jsonl')
        self.assertEqual(results[-1]['type'],'cosine_matrix')
        self.assertEqual(results[-1]['order'],['A01'])
        self.assertEqual(results[-1]['values'],[['1.000000000']])
        self.assertEqual(results[0]['data']['cosine_matrix'],[[1.0000000000000002]])

    def test_context_keeps_original_fixture_and_records_missing_compilation_limit(self):
        from sse_multivector.numerical_publication import export_results
        source = self.context_fixture()
        output = Path(export_results(source,family='representation')['output'])
        metadata = json.loads((output/'experiment.json').read_text())
        self.assertIn('not rerun',metadata['binding_limitations'][0])
        self.assertEqual(self.records(output,'inputs.jsonl')[0]['data'],
                         json.loads((self.root/'context-counterfactual-v1.json').read_text()))

    def test_context_prediction_identity_must_match_frozen_target_order(self):
        from sse_multivector.numerical_publication import export_results
        source = self.context_fixture()
        self.modify(source/'analysis.json',lambda x:x['predictions'][0].update(target_id='wrong-target'))
        self.modify(source/'manifest.json',lambda x:x['files'].update({'analysis.json':dict(
            sha256=hashlib.sha256((source/'analysis.json').read_bytes()).hexdigest(),
            bytes=(source/'analysis.json').stat().st_size)}))
        with self.assertRaisesRegex(ValueError,'target identity'):
            export_results(source,family='representation')

    def test_reexport_is_stable_and_source_identity_survives_directory_relocation(self):
        from sse_multivector.numerical_publication import export_results
        source = self.fixture()
        output = Path(export_results(source,family='representation')['output'])
        original = {p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in output.iterdir()}
        export_results(source,family='representation')
        self.assertEqual(original,{p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in output.iterdir()})
        relocated = source.rename(self.root/'moved-study')
        export_results(relocated,family='representation')
        self.assertEqual(original,{p.name:(p.read_bytes(),p.stat().st_mtime_ns)
                                    for p in (relocated/'publication').iterdir()})


if __name__ == '__main__':
    unittest.main()
