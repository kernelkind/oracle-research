import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from sse_multivector import title_selection_probe as probe
from sse_multivector import worker
from sse_multivector import test_meaning_example_probe as fixtures
from sse_multivector.test_worker import DeterministicEncoder


class TitleSelectionProbeTests(unittest.TestCase):
    def fixture(self, root):
        study, _ = fixtures.MeaningExampleProbeTests().fixture(root)
        plan = json.loads((study/'plan.json').read_text())
        plan['records'] = [dict(id='a', title='人 reactions', meaning='Responses by people.',
                                source_note_id='note-a'),
                           dict(id='b', title='Audience reactions', meaning='Audience responses.',
                                source_note_id='note-b')]
        (study/'plan.json').write_text(json.dumps(plan))
        return study

    def test_prepares_three_native_views_in_unchanged_utf8_context(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); study=self.fixture(root); out=root/'probe'
            probe.prepare(study, ['a','b'], 'reactions', out)
            inputs=json.loads((out/'inputs.json').read_text())
            proposal,notes=worker._load_request(out/'worker-request.json')
            self.assertEqual(proposal,hashlib.sha256((out/'inputs.json').read_bytes()).hexdigest())
            self.assertEqual(len(notes),2)
            self.assertEqual([r['entry'] for r in inputs['records']],['a','b'])
            contexts={n.note_id:n for n in notes}
            for r in inputs['records']:
                n=contexts[r['views']['selection']['note_id']]
                self.assertEqual(n.text,r['title']+'\n\n'+r['meaning'])
                for view,expected in [('title',r['title']),('meaning',r['meaning']),
                                      ('selection','reactions')]:
                    v=r['views'][view]
                    self.assertEqual(v['note_id'],n.note_id)
                    s=next(s for s in n.subjects if s.subject_id==v['subject_id'])
                    self.assertEqual(len(s.byte_spans),1)
                    start,end=s.byte_spans[0]
                    self.assertEqual(n.text.encode()[start:end].decode(),expected)
            with self.assertRaises(FileExistsError):
                probe.prepare(study,['a'],'reactions',out)

    def test_rejects_absent_ambiguous_or_duplicate_selection_before_writing(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);study=self.fixture(root)
            for entries,text in [(['a'],'Responses'),(['a','a'],'reactions'),([], 'reactions'),
                                 (['a'],''),(['missing'],'reactions')]:
                with self.assertRaises(ValueError):
                    probe.prepare(study,entries,text,root/'invalid')
                self.assertFalse((root/'invalid').exists())
            plan=json.loads((study/'plan.json').read_text())
            plan['records'][0]['title']='reactions reactions'
            (study/'plan.json').write_text(json.dumps(plan))
            with self.assertRaisesRegex(ValueError,'one exact title occurrence'):
                probe.prepare(study,['a'],'reactions',root/'invalid')
            self.assertFalse((root/'invalid').exists())

    def test_standalone_pools_only_selected_text_and_reuses_one_native_row(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);study=self.fixture(root);out=root/'standalone'
            probe.prepare(study,['a','b'],'reactions',out,standalone=True)
            inputs=json.loads((out/'inputs.json').read_text())
            _,notes=worker._load_request(out/'worker-request.json')
            self.assertEqual(inputs['views'],['standalone'])
            self.assertEqual(len(notes),1)
            self.assertEqual(notes[0].text,'reactions')
            self.assertEqual(len(notes[0].subjects),1)
            self.assertEqual(notes[0].subjects[0].byte_spans,((0,9),))
            self.assertEqual(inputs['records'][0]['views'],inputs['records'][1]['views'])
            self.assertEqual([r['source_note_id']for r in inputs['records']],['note-a','note-b'])
            self.assertEqual(inputs['records'][0]['meaning'],'Responses by people.')
            with patch('sse_multivector.worker.OfficialSseEncoder',return_value=DeterministicEncoder()):
                worker.run_worker(out/'worker-config.json')
            result=probe.collect(out)
            self.assertEqual(result['records'],2)
            self.assertEqual(set(result['files']),{'standalone-vectors.npy'})
            import numpy as np
            vectors=np.load(out/'standalone-vectors.npy')
            self.assertEqual(vectors.shape,(2,3))
            self.assertTrue(np.array_equal(vectors[0],vectors[1]))

    def test_collects_native_output_and_rejects_changed_source_and_raw_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);study=self.fixture(root);out=root/'probe'
            probe.prepare(study,['a','b'],'reactions',out)
            with patch('sse_multivector.worker.OfficialSseEncoder',return_value=DeterministicEncoder()):
                worker.run_worker(out/'worker-config.json')
            result=probe.collect(out)
            self.assertEqual(result['records'],2)
            self.assertEqual(set(result['files']),{'title-vectors.npy','meaning-vectors.npy',
                                                  'selection-vectors.npy'})
            self.assertEqual(probe.collect(out),result)
            raw=out/'worker-result/raw-vectors.f32le'
            original=raw.read_bytes();raw.write_bytes(original[:-1]+bytes([original[-1]^1]))
            with self.assertRaisesRegex(ValueError,'vector bytes'):
                probe.collect(out)
            raw.write_bytes(original)
            (study/'original.txt').write_text('changed')
            with self.assertRaisesRegex(ValueError,'source changed'):
                probe.collect(out)


if __name__=='__main__':
    unittest.main()
