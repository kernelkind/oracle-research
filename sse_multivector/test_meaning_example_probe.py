import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from sse_multivector import meaning_example_probe as probe
from sse_multivector import worker
from sse_multivector.test_worker import DeterministicEncoder


class MeaningExampleProbeTests(unittest.TestCase):
    def fixture(self, root):
        source = root / 'study'
        source.mkdir()
        original = source / 'original.txt'
        original.write_text('immutable input\n')
        (source / 'plan.json').write_text(json.dumps(dict(as_version='ASv6.100',
            sources={str(original): hashlib.sha256(original.read_bytes()).hexdigest()})))
        rows = [dict(entry='a', title='人', source_note_id='note-a',
                     meaning='People are human beings, including but not limited to athletes.'),
                dict(entry='b', title='People', source_note_id='note-b',
                     meaning='People are human beings.')]
        (source / 'group-composition.json').write_text(json.dumps([
            dict(root='root', group='group', members=rows)]))
        checkpoint = root / 'checkpoint'
        checkpoint.write_bytes(b'fixture')
        model = root / 'model'
        model.mkdir()
        (model / 'config.json').write_text('{}')
        config = dict(schema_version=1, request_path=str(root/'unused-request'),
            request_sha256='ab'*32, checkpoint_path=str(checkpoint),
            checkpoint_sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
            base_model_artifact_path=str(model),
            base_model_artifact_tree_sha256=worker.canonical_tree_sha256(model),
            model=dict(base_model='fixture/sentence-encoder', dimensions=3,
                maximum_tokens=512, pooling=worker.POOLING_RULE), device='cpu',
            container_image='sha256:'+'ef'*32, note_batch_size=2,
            output_path=str(root/'unused-output'))
        (source/'worker-config.json').write_text(json.dumps(config))
        return source, rows

    def test_prepares_bound_native_views_without_rewriting_meanings(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);source,rows=self.fixture(root);out=root/'probe'
            probe.prepare(source, 'root', 'group', out)
            inputs=json.loads((out/'inputs.json').read_text())
            proposal,notes=worker._load_request(out/'worker-request.json')
            self.assertEqual(proposal, hashlib.sha256((out/'inputs.json').read_bytes()).hexdigest())
            contexts={n.note_id:n for n in notes}
            self.assertEqual(inputs['records'][0]['meaning'],rows[0]['meaning'])
            a=inputs['records'][0]
            self.assertEqual(a['core'], 'People are human beings')
            original=contexts[a['views']['core_selected']['note_id']]
            self.assertIn('including but not limited',original.text)
            sid=a['views']['core_selected']['subject_id']
            spans=next(s.byte_spans for s in original.subjects if s.subject_id==sid)
            self.assertEqual(spans,((len('人\n\n'.encode()),len(('人\n\n'+a['core']).encode())),))
            short=contexts[a['views']['core_context']['note_id']]
            self.assertEqual(short.text,'人\n\nPeople are human beings')
            control=inputs['records'][1]['views']
            self.assertEqual(control['full'],control['core_selected'])
            self.assertEqual(control['full'],control['core_context'])
            with self.assertRaises(FileExistsError):probe.prepare(source,'root','group',out)

    def test_collects_real_worker_output_and_detects_changed_sources(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);source,_=self.fixture(root);out=root/'probe'
            probe.prepare(source,'root','group',out)
            with patch('sse_multivector.worker.OfficialSseEncoder',return_value=DeterministicEncoder()):
                worker.run_worker(out/'worker-config.json')
            report=probe.collect(out)
            self.assertEqual(report['records'],2)
            self.assertEqual(report['dimensions'],3)
            (source/'original.txt').write_text('changed\n')
            with self.assertRaisesRegex(ValueError,'source changed'):probe.collect(out)

    def test_does_not_strip_an_inclusion_that_is_not_explicitly_optional(self):
        self.assertEqual(probe.core_prefix('The topic includes required roles.'),
                         'The topic includes required roles.')
        self.assertEqual(probe.core_prefix('People are humans, including children.'),
                         'People are humans, including children.')


if __name__=='__main__':
    unittest.main()
