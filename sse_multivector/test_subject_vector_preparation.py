"""Standalone subject-vector preparation preserves unencoded source masks."""
import json
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from sse_multivector import subject_matching_probe
from sse_multivector import test_subject_matching_probe as fixtures
from sse_multivector import test_hierarchy_inputs as hierarchy_fixtures
from sse_multivector import worker
from sse_multivector.test_worker import DeterministicEncoder


class CollectedSubjectVectorPreparationTests(unittest.TestCase):
    setUp = hierarchy_fixtures.HierarchyInputTests.setUp
    write = hierarchy_fixtures.HierarchyInputTests.write
    cli = hierarchy_fixtures.HierarchyInputTests.cli
    prepare = hierarchy_fixtures.HierarchyInputTests.prepare
    show = hierarchy_fixtures.HierarchyInputTests.show
    calls = hierarchy_fixtures.HierarchyInputTests.calls
    subjects = hierarchy_fixtures.HierarchyInputTests.subjects

    def collected_subjects(self):
        entries = [dict(number=number, subject=subject, context='The post names plants.')
                   for number, subject in [('1', 'Plants'), ('1.1', 'Basil'), ('2', 'Basil')]]
        self.subjects(entries=entries)
        self.cli('collect', 'SP', '--output', 'subjects')
        checkpoint = self.root / 'checkpoint'
        checkpoint.write_bytes(b'checkpoint fixture')
        model = self.root / 'model'
        model.mkdir()
        (model / 'config.json').write_text('{}')
        config = dict(schema_version=1, request_path='unused-request', request_sha256='1' * 64,
            checkpoint_path=str(checkpoint), checkpoint_sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
            base_model_artifact_path=str(model), base_model_artifact_tree_sha256=worker.canonical_tree_sha256(model),
            model=dict(base_model='saved SSE', dimensions=3, maximum_tokens=512, pooling=worker.POOLING_RULE),
            device='cpu', container_image='sha256:' + 'a' * 64, note_batch_size=8, output_path='unused-output')
        settings = self.write('worker-settings.json', config)
        return self.root / 'subjects/subjects.json', settings, config

    def test_native_collected_subjects_prepare_full_heading_vectors_without_masks(self):
        subjects, settings, config = self.collected_subjects()
        before = {path: path.read_bytes() for path in (self.root / 'subjects').iterdir()}
        calls = self.calls()
        output = self.root / 'headings'
        result = subprocess.run([
            sys.executable, '-m', 'sse_multivector.subject_matching_probe', 'prepare',
            '--subjects', str(subjects),
            '--worker-config', str(settings), '--output', str(output),
        ], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        summary = json.loads(result.stdout)
        self.assertEqual((summary['posts'], summary['subjects'], summary['new_encodings']), (1, 3, 2))
        request = json.loads((output / 'worker-request.json').read_text())
        self.assertEqual([note['text'] for note in request['notes']], ['Plants', 'Basil'])
        for note in request['notes']:
            digest = hashlib.sha256(note['text'].encode()).hexdigest()
            self.assertEqual(note['note_id'], digest)
            self.assertEqual(note['subjects'], [dict(subject_id=digest[:16], byte_spans=[[0, len(note['text'].encode())]])])
        inputs = json.loads((output / 'inputs.json').read_text())
        self.assertEqual([entry['subject'] for entry in inputs['subjects']], ['Plants', 'Basil', 'Basil'])
        self.assertEqual(inputs['edges'], [[0, 1]])
        self.assertIn(str(self.root / 'subjects/provenance.json'), inputs['protected_sha256'])
        self.assertIn(str(self.root / 'SP/run/results.jsonl'), inputs['protected_sha256'])
        bound = worker.WorkerConfig.load(output / 'worker-config.json')
        self.assertEqual(bound.request_path, output / 'worker-request.json')
        self.assertEqual(bound.output_path, output / 'worker-result')
        self.assertEqual(bound.checkpoint_sha256, config['checkpoint_sha256'])
        self.assertFalse(bound.output_path.exists())
        self.assertFalse((self.root / 'subjects/masked-posts.json').exists())
        self.assertEqual(before, {path: path.read_bytes() for path in before})
        self.assertEqual(self.calls(), calls)

    def encoded_subjects(self):
        subjects, settings, _ = self.collected_subjects()
        output = self.root / 'headings'
        subject_matching_probe.prepare_collected_subjects(subjects, output, worker_config=settings)
        with patch.object(worker, 'OfficialSseEncoder', return_value=DeterministicEncoder()):
            worker.run_worker(output / 'worker-config.json')
        return subjects, output

    def test_native_worker_receipts_load_in_production_candidate_ranking(self):
        from sse_multivector import canonical_selection_ranking as ranking
        subjects, output = self.encoded_subjects()
        vectors, receipt, protected = subject_matching_probe.load_subject_vectors(output)
        self.assertEqual(len(vectors), 2)
        self.assertEqual(receipt['dimensions'], 3)
        self.assertIn(str(subjects), protected)
        self.assertIn(str(self.root / 'SP/run/results.jsonl'), protected)
        rows = [dict(id='C001', subject='Plants', meaning='Plants.'),
                dict(id='C002', subject='Basil', meaning='Basil plants.')]
        order, provenance = ranking.rank_candidates('Basil', 'Basil plants.', rows,
                                                   subject_probe=output, query_ancestors=['Plants'])
        self.assertEqual(set(order), {'C001', 'C002'})
        self.assertEqual(provenance['subject_vectors']['loaded_vectors'], 2)
        self.assertIn(str(subjects), provenance['sources'])
        self.assertEqual(provenance['new_encodings'], 0)

    def test_modified_native_collection_is_rejected_before_preparation(self):
        subjects, settings, _ = self.collected_subjects()
        value = json.loads(subjects.read_text())
        value['notes'][0]['subjects'][0]['subject'] = 'Changed heading'
        subjects.write_text(json.dumps(value))
        output = self.root / 'headings'
        with self.assertRaisesRegex(ValueError, 'canonical collection file differs from native receipts'):
            subject_matching_probe.prepare_collected_subjects(subjects, output, worker_config=settings)
        self.assertFalse(output.exists())

    def test_modified_upstream_subjects_block_loading_completed_vectors(self):
        subjects, output = self.encoded_subjects()
        subjects.write_text(subjects.read_text() + '\n')
        with self.assertRaisesRegex(ValueError, 'protected subject-vector source changed'):
            subject_matching_probe.load_subject_vectors(output)

    def test_wrong_worker_identity_or_runtime_block_loading(self):
        _, output = self.encoded_subjects()
        path = output / 'worker-result/worker-receipt.json'
        receipt = json.loads(path.read_text())
        for changed, expected in [
                (dict(receipt, checkpoint_sha256='f' * 64), 'worker identity differs'),
                (dict(receipt, runtime=dict(receipt['runtime'], worker_sha256='f' * 64)), 'worker runtime differs')]:
            with self.subTest(expected=expected):
                path.write_text(json.dumps(changed))
                with self.assertRaisesRegex(ValueError, expected):
                    subject_matching_probe.load_subject_vectors(output)

    def test_collected_mode_rejects_legacy_vector_reuse(self):
        output = self.root / 'headings'
        result = subprocess.run([
            sys.executable, '-m', 'sse_multivector.subject_matching_probe', 'prepare',
            '--subjects', str(self.root / 'subjects.json'), '--worker-config', str(self.root / 'settings.json'),
            '--reuse-probe', str(self.root / 'deprecated-probe'), '--output', str(output),
        ], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('does not accept legacy mask/reuse options', result.stderr)
        self.assertFalse(output.exists())


class SubjectVectorPreparationTests(unittest.TestCase):
    def test_explicit_subject_only_cli_does_not_require_mask_vectors(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source, _ = fixtures.SavedMatchingTests().fixture(directory)
            (source / 'worker-config.json').write_text(json.dumps({'device': 'cpu'}))
            shutil.rmtree(source / 'worker-result')
            before = {p: p.read_bytes() for p in source.iterdir()}
            output = directory / 'standalone'
            result = subprocess.run([
                sys.executable, '-m', 'sse_multivector.subject_matching_probe', 'prepare',
                '--source', str(source), '--output', str(output), '--subject-vectors-only',
            ], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads(result.stdout)
            self.assertEqual(summary['mask_vector_policy'], 'not_required_for_subject_vectors_v1')
            saved = json.loads((output / 'inputs.json').read_text())
            self.assertEqual(saved['mask_vector_policy'], summary['mask_vector_policy'])
            self.assertEqual([s['mask_vector_ids'] for s in saved['subjects']], [['v1'], [], ['v2'], []])
            self.assertFalse(any('/worker-result/' in p for p in saved['protected_sha256']))
            request = json.loads((output / 'worker-request.json').read_text())
            self.assertEqual({n['text'] for n in request['notes']}, {'Bread', 'Empty'})
            self.assertEqual(before, {p: p.read_bytes() for p in source.iterdir()})
            self.assertFalse((source / 'worker-result').exists())

    def test_default_preparation_still_requires_completed_mask_encoding(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source, _ = fixtures.SavedMatchingTests().fixture(directory)
            (source / 'worker-config.json').write_text(json.dumps({'device': 'cpu'}))
            shutil.rmtree(source / 'worker-result')
            with self.assertRaises(FileNotFoundError):
                subject_matching_probe.prepare(source, directory / 'default')

    def test_invalid_mode_rejected_before_output_creation(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            with self.assertRaisesRegex(ValueError, 'boolean'):
                subject_matching_probe.prepare(directory, directory / 'output', subject_vectors_only='yes')
            self.assertFalse((directory / 'output').exists())
