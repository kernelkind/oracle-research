"""Source-bound auxiliary SSE preparation through the actual worker parser."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from sse_multivector import canonical_ranking_vectors as vectors
from sse_multivector import worker


class RankingVectorPreparation(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.state = self.root / 'state.json'
        self.config = self.root / 'config.json'
        self.state.write_text(json.dumps(dict(nodes=[
            dict(id='C001', subject='Meals', meaning='Occasions of eating food.'),
            dict(id='C002', subject='Meals', meaning='Food eaten together.')], steps=[
                dict(index=0, selected_meaning='Food eaten together.', local=dict(note_id='a'*64, number='1'))],
            corpus=str(self.root / 'corpus.json'), sources={})))
        (self.root / 'corpus.json').write_text(json.dumps(dict(notes=[dict(
            note_id='a'*64, text='Breakfast.', subjects=[dict(number='1', subject='Meals')])])) )
        self.config.write_text(json.dumps(dict(schema_version=1, request_path='/unused',
            request_sha256='a'*64, output_path='/unused', checkpoint_path='/checkpoint',
            checkpoint_sha256='b'*64, base_model_artifact_path='/model',
            base_model_artifact_tree_sha256='c'*64, container_image='sha256:'+'d'*64,
            device='cpu', note_batch_size=8, model=dict(base_model='sentence-transformers/sentence-t5-base',
                dimensions=768, maximum_tokens=512, pooling=worker.POOLING_RULE))))

    def test_same_heading_different_meanings_get_distinct_contextual_rows(self):
        output = self.root / 'vectors'
        summary = vectors.prepare(self.state, self.config, output, controls=['Meals'])
        proposal, notes = worker._load_request(output / 'worker-request.json')
        plan = json.loads((output / 'inputs.json').read_text())
        self.assertEqual(proposal, hashlib.sha256((output / 'inputs.json').read_bytes()).hexdigest())
        self.assertEqual(summary['meaning_pairs'], 2)
        self.assertEqual(summary['teacher_calls'], 0)
        meanings = [n for n in notes if n.text.startswith('Meals\n')]
        self.assertEqual(len(meanings), 2)
        self.assertEqual([len(n.subjects) for n in meanings], [2, 2])
        for note in meanings:
            self.assertEqual(note.subjects[0].byte_spans, ((0, 5),))
            self.assertEqual(note.subjects[1].byte_spans, ((6, len(note.text.encode())),))
        rows = [x['representations']['contextual_heading'] for x in plan['pairs']]
        self.assertNotEqual(rows[0], rows[1])
        self.assertEqual(plan['references']['step:0'], plan['references']['node:C002'])
        self.assertEqual(len(plan['controls']), 1)

    def test_source_change_refuses_collection(self):
        output = self.root / 'vectors'
        vectors.prepare(self.state, self.config, output)
        self.state.write_text(self.state.read_text() + '\n')
        with self.assertRaisesRegex(ValueError, 'source changed'):
            vectors.validate_sources(output)

    def test_null_meanings_are_not_encoded(self):
        state = json.loads(self.state.read_text())
        state['steps'].append(dict(index=1, selected_meaning=None, local=dict(note_id='a'*64, number='1')))
        self.state.write_text(json.dumps(state))
        output = self.root / 'vectors'
        vectors.prepare(self.state, self.config, output)
        plan = json.loads((output / 'inputs.json').read_text())
        self.assertNotIn('step:1', plan['references'])

    def test_existing_destination_is_preserved(self):
        output = self.root / 'vectors'
        output.mkdir()
        with self.assertRaises(FileExistsError):
            vectors.prepare(self.state, self.config, output)


if __name__ == '__main__':
    unittest.main()
