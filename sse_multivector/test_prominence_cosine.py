import unittest
import json
import struct
import tempfile
from pathlib import Path

from sse_multivector.prominence_cosine import cosine, rank_rows


class ProminenceCosineTests(unittest.TestCase):
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
