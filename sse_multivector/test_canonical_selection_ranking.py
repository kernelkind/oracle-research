"""Exercise bounded production retrieval with real saved-vector receipt loading."""
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from sse_multivector.subject_order_probe import build_inputs


class CanonicalSelectionRankingTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.probes = 0

    def probe(self, rows):
        folder = self.root / f'probe-{self.probes}'
        self.probes += 1
        folder.mkdir()
        note = '1' * 64
        data, request = build_inputs({'notes': [dict(note_id=note, text='Saved fixture',
            subjects=[dict(number=str(i + 1), subject=heading, byte_spans=[], fragments=[])
                      for i, heading in enumerate(rows)])]}, {'vectors': [dict(
            note_id=note, note_short_id='N001', byte_spans=[], vector_id='offline')]}, ['N001'])
        data.update(new_encodings=len(rows), reused_probes=[])
        write = lambda path, value: path.write_text(json.dumps(value) + '\n')
        write(folder / 'inputs.json', data)
        proposal = hashlib.sha256((folder / 'inputs.json').read_bytes()).hexdigest()
        request.update(schema_version=1, proposal_sha256=proposal)
        write(folder / 'worker-request.json', request)
        raw = struct.pack('<' + 'f' * (2 * len(rows)),
                          *(value for node in request['notes'] for value in rows[node['text']]))
        result = folder / 'worker-result'
        result.mkdir()
        (result / 'raw-vectors.f32le').write_bytes(raw)
        write(result / 'worker-receipt.json', dict(checkpoint_sha256='saved-fixture',
            base_model_artifact_tree_sha256='saved-base', model='SSE fixture', runtime={},
            dimensions=2, row_count=len(rows), proposal_sha256=proposal,
            request_sha256=hashlib.sha256((folder / 'worker-request.json').read_bytes()).hexdigest(),
            rows=[dict(note_id=node['note_id'], subject_id=node['subjects'][0]['subject_id'])
                  for node in request['notes']],
            files={'raw-vectors.f32le': {'sha256': hashlib.sha256(raw).hexdigest()}}))
        return folder

    def rank(self, *args, **kwargs):
        from sse_multivector.canonical_selection_ranking import rank_candidates
        return rank_candidates(*args, **kwargs)

    def test_combines_complementary_candidates_without_teacher_or_encoder_calls(self):
        probe = self.probe({'Young greens': (1., 0.), 'Food': (.8, .6),
                            'Vegetables': (.1, 1.), 'Carrots': (1., 0.)})
        rows = [dict(id='C001', subject='Food', meaning='Food for eating.'),
                dict(id='C002', subject='Vegetables', meaning='Vegetables for eating.'),
                dict(id='C003', subject='Carrots', meaning='Carrots for eating.')]
        before = {path: path.read_bytes() for path in probe.rglob('*') if path.is_file()}
        with patch('subprocess.run', side_effect=AssertionError('teacher/encoder execution')):
            order, provenance = self.rank('Young greens', 'Vegetables for eating.', rows,
                                          subject_probe=probe)
            repeated = self.rank('Young greens', 'Vegetables for eating.', rows,
                                 subject_probe=probe)
        self.assertEqual(order, ['C003', 'C002', 'C001'])
        self.assertEqual((order, provenance), repeated)
        self.assertEqual(provenance['scores'], {'C003': 1., 'C002': .5, 'C001': 1/3})
        self.assertEqual(provenance['inference_calls'], 0)
        self.assertEqual(provenance['new_encodings'], 0)
        for path, content in before.items():
            self.assertEqual(provenance['sources'][str(path)], hashlib.sha256(content).hexdigest())
            self.assertEqual(path.read_bytes(), content)

    def test_shared_text_ranking_keeps_the_historical_order_and_scores(self):
        from sse_multivector.canonical_candidate_selection import _ranking
        from sse_multivector.canonical_selection_ranking import rank_text
        rows = [dict(id='C001', subject='Food', meaning='Food for eating.'),
                dict(id='C002', subject='Vegetables', meaning='Vegetables for eating.'),
                dict(id='C003', subject='Carrots', meaning='Carrots for eating.')]
        order, scores = rank_text('Young greens', 'Vegetables for eating.', rows)
        self.assertEqual(order, ['C002', 'C001', 'C003'])
        historical = _ranking(dict(before=rows, answers=[dict(id=row['id']) for row in rows],
            local_input={'entry': {'subject': 'Young greens'}},
            selected_meaning='Vegetables for eating.'))
        self.assertEqual((order, scores), historical)
        # Frozen values from the original reference implementation before extraction.
        self.assertEqual(scores, {'C001': 0.024559031082559014,
                                 'C002': 0.24271539736466882,
                                 'C003': 0.024559031082559014})

    def test_original_ancestor_headings_nominate_broader_topics_with_real_vectors(self):
        probe = self.probe({'Broccoli': (1., 0.), 'Cooking': (0., 1.), 'Carrots': (.6, .8)})
        rows = [dict(id='L1', subject='Cooking', meaning=''),
                dict(id='L2', subject='Broccoli', meaning=''),
                dict(id='L3', subject='Carrots', meaning='')]
        ordinary, before = self.rank('Broccoli', '', rows, subject_probe=probe)
        order, after = self.rank('Broccoli', '', rows, subject_probe=probe,
                                 query_ancestors=('Cooking',))
        self.assertEqual(ordinary[0], 'L2')
        self.assertEqual(order[0], 'L1')
        self.assertEqual(before['sse_scores']['L1'], 0.)
        self.assertEqual(after['sse_scores']['L1'], 1.)
        self.assertEqual(after['query_headings'], ['Broccoli', 'Cooking'])
        self.assertEqual(after['new_encodings'], 0)

    def test_text_only_empty_meanings_ties_and_duplicate_wordings_keep_distinct_ids(self):
        rows = [dict(id='L2', subject='Cooking', meaning='', relation='equivalent'),
                dict(id='L1', subject='Cooking', meaning='', relation='neither')]
        order, provenance = self.rank('Cooking', '', rows)
        self.assertEqual(order, ['L1', 'L2'])
        self.assertEqual(provenance['text_scores']['L1'], provenance['text_scores']['L2'])
        self.assertIsNone(provenance['sse_scores'])
        self.assertEqual(provenance['method'], 'text only')
        self.assertEqual(self.rank('Cooking', '', [dict(row, relation='uncertain') for row in rows]),
                         (order, provenance))
        empty, metadata = self.rank('Cooking', '', [])
        self.assertEqual((empty, metadata['scores']), ([], {}))

    def test_missing_nonfinite_zero_and_corrupt_saved_vectors_are_rejected(self):
        rows = [dict(id='L1', subject='Cooking', meaning='')]
        for vectors, message in (({'Cooking': (1., 0.), 'Unused': (0., 1.)}, 'missing saved SSE heading'),
                                 ({'Food': (1., 0.), 'Cooking': (0., 0.)}, 'zero vector'),
                                 ({'Food': (1., 0.), 'Cooking': (float('nan'), 1.)}, 'invalid vectors')):
            with self.subTest(message=message):
                probe = self.probe(vectors)
                with self.assertRaisesRegex(ValueError, message):
                    self.rank('Food', '', rows, subject_probe=probe)
        probe = self.probe({'Food': (1., 0.), 'Cooking': (0., 1.)})
        (probe / 'worker-result/raw-vectors.f32le').write_bytes(b'corrupt')
        with self.assertRaisesRegex(ValueError, 'vector hash mismatch'):
            self.rank('Food', '', rows, subject_probe=probe)

    def test_cached_probe_sources_remain_verified_and_metadata_is_not_shared(self):
        probe = self.probe({'Food': (1., 0.), 'Cooking': (0., 1.)})
        rows = [dict(id='L1', subject='Cooking', meaning='')]
        _, metadata = self.rank('Food', '', rows, subject_probe=probe)
        metadata['subject_vectors']['runtime']['injected'] = True
        _, again = self.rank('Food', '', rows, subject_probe=probe)
        self.assertEqual(again['subject_vectors']['runtime'], {})
        with (probe / 'worker-request.json').open('a') as stream:
            stream.write('\n')
        with self.assertRaisesRegex(ValueError, 'saved SSE source changed'):
            self.rank('Food', '', rows, subject_probe=probe)

    def test_unknown_ancestor_heading_cannot_invent_a_vector(self):
        probe = self.probe({'Broccoli': (1., 0.), 'Unused': (0., 1.)})
        with self.assertRaisesRegex(ValueError, 'missing saved SSE heading: Cooking'):
            self.rank('Broccoli', '', [dict(id='L1', subject='Broccoli', meaning='')],
                      subject_probe=probe, query_ancestors=('Cooking',))

    def test_local_inventory_ranking_preserves_all_4096_candidates(self):
        rows = [dict(id=f'L{i:04}', subject='Storage', meaning='') for i in range(4096)]
        rows[-1]['subject'] = 'Cooking'
        order, provenance = self.rank('Cooking', '', rows)
        self.assertEqual(order[0], 'L4095')
        self.assertEqual(set(order), {row['id'] for row in rows})
        self.assertEqual(len(provenance['text_scores']), 4096)
        self.assertEqual(provenance['inference_calls'], 0)

    def test_invalid_or_unbounded_inputs_are_rejected_before_loading_a_probe(self):
        row = dict(id='L1', subject='Cooking', meaning='')
        cases = (([dict(row, id=str(i)) for i in range(4097)], (), 'at most 4096'),
                 ([row], tuple('Cooking' for _ in range(65)), 'at most 64'),
                 ([row, row], (), 'duplicate candidate ID'),
                 ([dict(row, subject='x' * 16385)], (), 'field byte limit'),
                 ([dict(row, meaning='x' * 16384, id=str(i)) for i in range(256)],
                  (), 'total input byte limit'),
                 ([dict(row, meaning=None)], (), 'meaning must be text'))
        for rows, ancestors, message in cases:
            with self.subTest(message=message), patch(
                    'sse_multivector.canonical_selection_ranking.load_subject_vectors',
                    side_effect=AssertionError('source loading reached')):
                with self.assertRaisesRegex(ValueError, message):
                    self.rank('Cooking', '', rows, subject_probe='absent', query_ancestors=ancestors)


if __name__ == '__main__':
    unittest.main()
