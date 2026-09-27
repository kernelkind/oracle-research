import unittest
import json
import struct
import tempfile
from argparse import Namespace
from unittest.mock import patch
from pathlib import Path

from sse_multivector.prominence_cosine import cosine, rank_rows


class ProminenceCosineTests(unittest.TestCase):
    def test_prepare_selected_generic_prominence_validates_exact_model_input(self):
        from sse_multivector import prominence_cosine as pc
        from sse_multivector.experiment_inputs import prepare_prominence
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = dict(id='photo-V1', node_id='photo', node_title='Photography',
                            note_id='a'*64, text='Take photos.', mask_ids=['V1'],
                            byte_spans=[[5, 11]])
            case = prepare_prominence({'cases': [evidence]})[0]
            case.update(status='valid', parsed={'prominence': 20, 'allocation': []})
            other = dict(id='other', status='unrun', evidence={'node_id': 'other'})
            encoder = dict(checkpoint_sha256='b'*64, base_model_artifact_tree_sha256='c'*64,
                           model={'dimensions': 2}, note_batch_size=1)
            config = root/'config.json'
            config.write_text(json.dumps(dict(encoder, device='cpu')))
            (root/'experiment.json').write_text('{}')
            (root/'results.jsonl').write_text('{}\n')
            vectors = root/'vectors'
            vectors.write_bytes(struct.pack('<2f', 1, 0))
            row = dict(short_id='V1', ordinal=0, note_id='a'*64, note_short_id='N1',
                       byte_spans=[[5, 11]], fragments=['photos'])
            args = Namespace(output=root/'out', vectors=root, experiments=[root],
                             worker_config=config, replay=['V1'], node=['photo'])
            plan = {'dataset': {'adapter': 'generic'}, 'run_directory': str(root)}
            with patch.object(pc, 'load_vectors', return_value=([row], encoder, vectors, 'f', {})), \
                 patch.object(pc.experiment, 'load', return_value=(plan, None, None)), \
                 patch.object(pc.experiment, 'report', return_value={'cases': [case, other]}):
                pc.prepare(args)
                saved = json.loads((args.output/'plan.json').read_text())
                self.assertEqual([c['id'] for c in saved['cases']], ['photo-V1'])
                request = json.loads((args.output/'worker-request.json').read_text())
                self.assertEqual([n['text'] for n in request['notes']], ['Photography', 'Take photos.'])
                args.output = root/'bad-input'
                case['inputs']['INPUT_JSON'] = json.dumps({'mask': ['Take'], 'marked_post': '⟦Take⟧ photos.'})
                with self.assertRaisesRegex(ValueError, 'input'):
                    pc.prepare(args)
                self.assertFalse(args.output.exists())
                args.node = ['absent']
                with self.assertRaisesRegex(ValueError, 'node'):
                    pc.prepare(args)

    def test_linear_product_matches_viewer_formula(self):
        rows = [dict(id='a', prominence=80, cosine=0),
                dict(id='b', prominence=50, cosine=1),
                dict(id='c', prominence=90, cosine=-1)]
        ranks = rank_rows(rows)
        self.assertEqual([r['linear_product'] for r in rows], [40, 50, 0])
        self.assertEqual(ranks['linear_product'], ['b', 'a', 'c'])

    def test_refresh_vectors_are_loaded_with_verified_rows_spans_and_bytes(self):
        from sse_multivector.prominence_cosine import load_vectors, sha
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "worker-result").mkdir()
            request = {"proposal_sha256": "source", "notes": [dict(note_id="N", text="Tea",
                       subjects=[dict(subject_id="S", byte_spans=[[0, 3]])]) ]}
            mapping = {"vectors": [dict(note_id="N", worker_subject_id="S", short_id="V1",
                       byte_spans=[[0, 3]], fragments=["Tea"])]}
            (root / "worker-request.json").write_text(json.dumps(request))
            (root / "vector-map.json").write_text(json.dumps(mapping))
            raw = root / "worker-result/raw-vectors.f32le"
            raw.write_bytes(struct.pack('<2f', 3, 4))
            receipt = dict(request_sha256=sha(root / "worker-request.json"),
                           proposal_sha256="source", model={"dimensions": 2}, row_count=1,
                           rows=[dict(note_id="N", subject_id="S", ordinal=0)],
                           files={raw.name: {"sha256": sha(raw)}})
            (root / "worker-result/worker-receipt.json").write_text(json.dumps(receipt))
            rows, encoder, vector_file, code, protected = load_vectors(root)
            self.assertEqual(rows[0]['ordinal'], 0)
            self.assertEqual((vector_file, code), (raw, 'f'))
            self.assertEqual(protected[str(raw)], sha(raw))
            mapping['vectors'][0]['byte_spans'] = [[1, 3]]
            (root / "vector-map.json").write_text(json.dumps(mapping))
            with self.assertRaisesRegex(ValueError, 'span'):
                load_vectors(root)
            mapping['vectors'][0]['byte_spans'] = [[0, 3]]
            (root / "vector-map.json").write_text(json.dumps(mapping))
            raw.write_bytes(struct.pack('<2f', 4, 3))
            with self.assertRaisesRegex(ValueError, 'hash'):
                load_vectors(root)

    def test_cosine_is_normalized_and_product_is_unclipped(self):
        self.assertAlmostEqual(cosine([3, 4], [6, 8]), 1)
        self.assertAlmostEqual(cosine([1, 0], [0, 3]), 0)
        self.assertAlmostEqual(cosine([1, 0], [-1, 0]), -1)
        with self.assertRaises(ValueError):
            cosine([0, 0], [1, 0])
        with self.assertRaises(ValueError):
            cosine([1], [1, 2])

    def test_three_rankings_preserve_cases_and_distinguish_the_product(self):
        rows = [dict(id="a", prominence=100, cosine=.2),
                dict(id="b", prominence=60, cosine=.8),
                dict(id="c", prominence=0, cosine=1),
                dict(id="d", prominence=90, cosine=-.1)]
        result = rank_rows(rows)
        self.assertEqual(result["prominence"], ["a", "d", "b", "c"])
        self.assertEqual(result["cosine"], ["c", "b", "a", "d"])
        self.assertEqual(result["product"], ["b", "a", "c", "d"])
        self.assertEqual(rows[-1]["product"], -9)


if __name__ == "__main__":
    unittest.main()
