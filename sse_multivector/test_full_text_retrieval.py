"""Full-text retrieval preparation through the production SSE parser/reader."""
import json
from pathlib import Path
import struct
import tempfile
import unittest

from sse_multivector import full_text_retrieval as retrieval
from sse_multivector import worker


class FullTextRetrieval(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.state = self.root / 'state.json'
        self.corpus = self.root / 'corpus.json'
        self.config = self.root / 'config.json'
        self.output = self.root / 'vectors'
        self.corpus.write_text(json.dumps(dict(notes=[
            dict(note_id='a'*64, text='Breakfast café ☕'),
            dict(note_id='b'*64, text='Tomatoes for breakfast.'),
            dict(note_id='c'*64, text='Outside this hierarchy.')])))
        self.state.write_text(json.dumps(dict(corpus=str(self.corpus), steps=[
            dict(index=0, local=dict(note_id='a'*64, number='3'),
                 selected_meaning='Breakfast is a meal.', before=[
                     dict(id='C001', subject='Meals', entries=[dict(note_id='b'*64, number='1')])]),
            dict(index=1, local=dict(note_id='b'*64, number='1'))])))
        self.config.write_text(json.dumps(dict(schema_version=1, request_path='/unused',
            request_sha256='a'*64, output_path='/unused', checkpoint_path='/checkpoint',
            checkpoint_sha256='b'*64, base_model_artifact_path='/model',
            base_model_artifact_tree_sha256='c'*64, container_image='sha256:'+'d'*64,
            device='cpu', note_batch_size=8, model=dict(base_model='fixture/t5',
                dimensions=3, maximum_tokens=512, pooling=worker.POOLING_RULE))))

    def prepare(self):
        return retrieval.prepare(self.state, 0, self.config, self.output)

    def test_full_meaning_and_every_selected_post_are_pooled_whole(self):
        summary = self.prepare()
        _, notes = worker._load_request(self.output / 'worker-request.json')
        self.assertEqual(summary['note_count'], 2)
        self.assertEqual(summary['vector_rows'], 3)
        self.assertEqual(notes[0].text, 'Breakfast is a meal.')
        self.assertEqual([n.note_id for n in notes[1:]], ['a'*64, 'b'*64])
        for n in notes:
            self.assertEqual(n.subjects[0].byte_spans, ((0, len(n.text.encode())),))
        plan = json.loads((self.output / 'inputs.json').read_text())
        self.assertEqual(plan['notes'][1]['canonical_support'], [dict(id='C001', subject='Meals')])

    def test_changed_original_text_refuses_ranking(self):
        self.prepare()
        self.corpus.write_text(self.corpus.read_text() + '\n')
        with self.assertRaisesRegex(ValueError, 'source changed'):
            retrieval.rank(self.output)

    def test_score_uses_all_receipted_rows_including_the_incoming_note(self):
        self.prepare()
        proposal, notes = worker._load_request(self.output / 'worker-request.json')
        raw = struct.pack('<9f', 1, 0, 0, 1, 0, 0, 0, 1, 0)
        out = self.output / 'worker-result'
        out.mkdir()
        (out / 'raw-vectors.f32le').write_bytes(raw)
        receipt = dict(proposal_sha256=proposal,
            request_sha256=worker._sha256_file(self.output / 'worker-request.json'),
            checkpoint_sha256='b'*64, base_model_artifact_tree_sha256='c'*64,
            model=json.loads(self.config.read_text())['model'], dimensions=3, row_count=3,
            rows=[dict(note_id=n.note_id, subject_id=n.subjects[0].subject_id) for n in notes],
            files={'raw-vectors.f32le':dict(sha256=worker._sha256_file(out / 'raw-vectors.f32le'))})
        (out / 'worker-receipt.json').write_text(json.dumps(receipt))
        result = retrieval.rank(self.output)
        self.assertEqual([r['note_id'] for r in result['rows']], ['a'*64, 'b'*64])
        self.assertEqual([r['cosine'] for r in result['rows']], [1.0, 0.0])
        self.assertTrue(result['rows'][0]['incoming_note'])
        receipt['request_sha256'] = '0'*64
        (out / 'worker-receipt.json').write_text(json.dumps(receipt))
        with self.assertRaisesRegex(ValueError, 'request binding'):
            retrieval.rank(self.output)


if __name__ == '__main__':
    unittest.main()
