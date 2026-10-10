"""Compact loading retains saved subject-vector validation and nomination."""

from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from sse_multivector.ancestor_cosine_probe import load_vectors
from sse_multivector.subject_matching_probe import load_subject_vectors


def save(path, value):
    path.write_text(json.dumps(value))


def batch(root, words, *, reused=(), values=None):
    root.mkdir()
    result = root / 'worker-result'
    result.mkdir()
    inputs = dict(new_encodings=len(words), reused_probes=list(map(str, reused)),
        subjects=[dict(index=i, subject=word, context='Original context.',
            note_id=f'post-{i}', note_short_id=f'N{i:03d}') for i, word in enumerate(words)])
    save(root / 'inputs.json', inputs)
    proposal = hashlib.sha256((root / 'inputs.json').read_bytes()).hexdigest()
    notes, rows = [], []
    for word in words:
        digest = hashlib.sha256(word.encode()).hexdigest()
        notes.append(dict(note_id=digest, text=word,
            subjects=[dict(subject_id=digest[:16], byte_spans=[[0, len(word.encode())]])]))
        rows.append(dict(note_id=digest, subject_id=digest[:16]))
    request = root / 'worker-request.json'
    save(request, dict(schema_version=1, proposal_sha256=proposal, notes=notes))
    values = values or [(1.0, i + 0.25, 0.2) for i in range(len(words))]
    raw = result / 'raw-vectors.f32le'
    raw.write_bytes(struct.pack('<' + 'f' * (3 * len(words)),
                               *(v for row in values for v in row)))
    receipt = dict(checkpoint_sha256='checkpoint', base_model_artifact_tree_sha256='model',
        model='Saved SSE', runtime=dict(version=1), device='cpu', note_batch_size=16,
        rows=rows, row_count=len(rows), dimensions=3, proposal_sha256=proposal,
        request_sha256=hashlib.sha256(request.read_bytes()).hexdigest(),
        files={raw.name: dict(sha256=hashlib.sha256(raw.read_bytes()).hexdigest())})
    save(result / 'worker-receipt.json', receipt)
    return root


class CompactSubjectVectorTests(unittest.TestCase):
    def test_shared_cli_measures_compact_loading_and_refuses_overwrite(self):
        from sse_multivector.experiment import main

        with tempfile.TemporaryDirectory() as directory:
            source = batch(Path(directory) / 'probe', ['Food', 'Bread'])
            output = Path(directory) / 'measurement.json'
            arguments = ['measure-subject-vectors', '--probe', str(source),
                         '--compact', '--output', str(output)]
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(arguments), 0)
            original = output.read_bytes()
            self.assertEqual(json.loads(original)['vector_storage'], 'readonly_memmap_float32')
            errors = io.StringIO()
            with redirect_stderr(errors):
                self.assertEqual(main(arguments), 1)
            self.assertIn('already exists', errors.getvalue())
            self.assertEqual(output.read_bytes(), original)

    def test_loading_measurement_returns_only_statistics_and_equal_normalized_hashes(self):
        from sse_multivector.subject_matching_probe import measure_subject_vector_loading

        with tempfile.TemporaryDirectory() as directory:
            source = batch(Path(directory) / 'probe', ['Food', 'Bread', 'Cooking'])
            legacy = measure_subject_vector_loading(source)
            compact = measure_subject_vector_loading(source, compact=True)
            self.assertEqual(legacy['normalized_vectors_sha256'], compact['normalized_vectors_sha256'])
            self.assertEqual(legacy['word_order_sha256'], compact['word_order_sha256'])
            self.assertEqual(compact['raw_vector_bytes'], 36)
            self.assertEqual(compact['normalized_vector_bytes'], 72)
            self.assertEqual(compact['inference_calls'], 0)
            self.assertNotIn('vectors', compact)
            self.assertNotIn('subjects', compact)

    def test_compact_rows_are_read_only_memmap_views_and_legacy_tuples_are_unchanged(self):
        import numpy as np

        with tempfile.TemporaryDirectory() as directory:
            source = batch(Path(directory) / 'probe', ['Food', 'Bread'])
            legacy, receipt = load_vectors(source / 'worker-result')
            original_read = Path.read_bytes

            def bounded_read(path):
                if path.name == 'raw-vectors.f32le':
                    raise AssertionError('compact vectors must not read the whole raw file')
                return original_read(path)

            with patch.object(Path, 'read_bytes', bounded_read):
                compact, compact_receipt = load_vectors(source / 'worker-result', compact=True)
            self.assertEqual(receipt, compact_receipt)
            self.assertEqual(list(legacy), list(compact))
            for key, row in compact.items():
                self.assertIsInstance(legacy[key], tuple)
                self.assertIsInstance(row, np.memmap)
                self.assertEqual(row.dtype, np.dtype('<f4'))
                self.assertFalse(row.flags.writeable)
                self.assertEqual(tuple(map(float, row)), legacy[key])

    def test_normalized_vectors_and_production_candidate_neighbors_are_identical(self):
        from sse_multivector.bounded_hierarchy_candidates import HNSWSubjectNeighbors

        with tempfile.TemporaryDirectory() as directory:
            words = ['Food', 'Bread', 'Cooking', 'Dining', 'Ingredients', 'Meals']
            source = batch(Path(directory) / 'probe', words)
            legacy, receipt, protected = load_subject_vectors(source)
            compact, compact_receipt, compact_protected = load_subject_vectors(source, compact=True)
            self.assertEqual(receipt, compact_receipt)
            self.assertEqual(protected, compact_protected)
            inputs = dict(subjects=[dict(index=i, subject=word, context='Original context.',
                note_id=f'post-{i}', note_short_id=f'N{i:03d}') for i, word in enumerate(words)],
                edges=[])
            hierarchy = dict(groups=[[i] for i in range(len(words))], edges=[])
            left = HNSWSubjectNeighbors(inputs, hierarchy, legacy)
            right = HNSWSubjectNeighbors(inputs, hierarchy, compact)
            self.assertEqual(left._data.vectors.tobytes(), right._data.vectors.tobytes())
            for word in words:
                self.assertEqual(left.nearest(word, set()), right.nearest(word, set()))

    def test_corrupt_vectors_request_and_proposal_are_rejected_in_both_modes(self):
        for mode in (False, True):
            for change, expected in [('vectors', 'vector hash mismatch'),
                                     ('request', 'request hash differs'),
                                     ('proposal', 'saved SP inputs')]:
                with self.subTest(compact=mode, change=change), tempfile.TemporaryDirectory() as directory:
                    source = batch(Path(directory) / 'probe', ['Food', 'Bread'])
                    if change == 'vectors':
                        (source / 'worker-result/raw-vectors.f32le').write_bytes(b'changed')
                    elif change == 'request':
                        (source / 'worker-request.json').write_text('{}')
                    else:
                        save(source / 'inputs.json', dict(new_encodings=2, changed=True))
                    with self.assertRaisesRegex(ValueError, expected):
                        load_subject_vectors(source, compact=mode)

    def test_reused_duplicate_rows_are_equal_and_conflicts_and_model_changes_fail(self):
        for mode in (False, True):
            with self.subTest(compact=mode), tempfile.TemporaryDirectory() as directory:
                prior = batch(Path(directory) / 'prior', ['Food'], values=[(1.0, 0.25, 0.2)])
                source = batch(Path(directory) / 'probe', ['Food', 'Bread'], reused=[prior])
                rows, _, protected = load_subject_vectors(source, compact=mode)
                self.assertEqual(len(rows), 2)
                self.assertIn(str(prior / 'worker-result/raw-vectors.f32le'), protected)
                receipt_path = source / 'worker-result/worker-receipt.json'
                receipt = json.loads(receipt_path.read_text())
                receipt['runtime'] = dict(changed=True)
                save(receipt_path, receipt)
                with self.assertRaisesRegex(ValueError, 'SSE identity mismatch'):
                    load_subject_vectors(source, compact=mode)
            with self.subTest(compact=mode, conflict=True), tempfile.TemporaryDirectory() as directory:
                prior = batch(Path(directory) / 'prior', ['Food'], values=[(2.0, 0.25, 0.2)])
                source = batch(Path(directory) / 'probe', ['Food'], reused=[prior])
                with self.assertRaisesRegex(ValueError, 'conflicting saved vectors'):
                    load_subject_vectors(source, compact=mode)

    def test_shape_duplicate_identity_and_reuse_cycle_fail_in_both_modes(self):
        for mode in (False, True):
            for change, expected in [('shape', 'vector shape mismatch'),
                                     ('identity', 'duplicate worker row identities'),
                                     ('cycle', 'cyclic subject-vector reuse')]:
                with self.subTest(compact=mode, change=change), tempfile.TemporaryDirectory() as directory:
                    source = batch(Path(directory) / 'probe', ['Food', 'Bread'])
                    receipt_path = source / 'worker-result/worker-receipt.json'
                    receipt = json.loads(receipt_path.read_text())
                    if change == 'shape':
                        receipt['row_count'] = 1
                        save(receipt_path, receipt)
                    elif change == 'identity':
                        receipt['rows'][1] = receipt['rows'][0]
                        save(receipt_path, receipt)
                    else:
                        save(source / 'inputs.json', dict(new_encodings=2, reused_probes=[str(source)]))
                    with self.assertRaisesRegex(ValueError, expected):
                        load_subject_vectors(source, compact=mode)

    def test_hash_bound_request_proposal_text_and_row_identity_checks_remain(self):
        for mode in (False, True):
            for change, expected in [('proposal', 'request proposal differs'),
                                     ('text', 'standalone full subject text'),
                                     ('row', 'worker rows differ from request')]:
                with self.subTest(compact=mode, change=change), tempfile.TemporaryDirectory() as directory:
                    source = batch(Path(directory) / 'probe', ['Food', 'Bread'])
                    request_path = source / 'worker-request.json'
                    receipt_path = source / 'worker-result/worker-receipt.json'
                    request = json.loads(request_path.read_text())
                    receipt = json.loads(receipt_path.read_text())
                    if change == 'proposal':
                        request['proposal_sha256'] = '0' * 64
                    elif change == 'text':
                        request['notes'][0]['text'] = 'Food extra'
                    else:
                        receipt['rows'][0]['subject_id'] = '0' * 16
                    save(request_path, request)
                    receipt['request_sha256'] = hashlib.sha256(request_path.read_bytes()).hexdigest()
                    save(receipt_path, receipt)
                    with self.assertRaisesRegex(ValueError, expected):
                        load_subject_vectors(source, compact=mode)

    def test_reuse_only_probe_retains_original_receipt_and_mapped_rows(self):
        import numpy as np

        with tempfile.TemporaryDirectory() as directory:
            prior = batch(Path(directory) / 'prior', ['Food'])
            source = batch(Path(directory) / 'probe', [], reused=[prior])
            legacy, receipt, protected = load_subject_vectors(source)
            compact, compact_receipt, compact_protected = load_subject_vectors(source, compact=True)
            self.assertEqual(receipt, compact_receipt)
            self.assertEqual(protected, compact_protected)
            self.assertEqual(len(compact), 1)
            for key, row in compact.items():
                self.assertIsInstance(row, np.memmap)
                self.assertEqual(tuple(map(float, row)), legacy[key])

    def test_compact_loading_rejects_source_changes_during_hash_validation(self):
        from sse_multivector import ancestor_cosine_probe as loader

        with tempfile.TemporaryDirectory() as directory:
            source = batch(Path(directory) / 'probe', ['Food'])
            original_hash = loader._sha256_file

            def mutate_after_hash(path):
                digest = original_hash(path)
                before = path.stat()
                path.write_bytes(struct.pack('<fff', 9.0, 0.25, 0.2))
                # Same-length writes can retain the same filesystem timestamp.
                # Explicitly change mtime to exercise the loader's stat guard.
                os.utime(path, ns=(before.st_atime_ns,
                                  before.st_mtime_ns + 1_000_000_000))
                return digest

            with patch.object(loader, '_sha256_file', mutate_after_hash):
                with self.assertRaisesRegex(ValueError, 'changed during compact loading'):
                    load_vectors(source / 'worker-result', compact=True)


if __name__ == '__main__':
    unittest.main()
