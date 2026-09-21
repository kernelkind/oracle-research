import json
import unittest

from study import decode_response


class DiagnosticDecodingTests(unittest.TestCase):
    def response(self, **changes):
        return {"meaning": "Art", "expressible": True, "evidence": "Art is named.",
                "mask": [{"word": 1, "text": "art"}], **changes}

    def test_preserves_diagnostics_and_uses_existing_position_decoder(self):
        raw = self.response()
        response, spans = decode_response(json.dumps(raw), "#artblog")
        self.assertEqual(response, raw)
        self.assertEqual(spans, [{"start": 1, "end": 4}])

    def test_valid_empty(self):
        raw = self.response(expressible=False, mask=[])
        self.assertEqual(decode_response(json.dumps(raw), "#artblog"), (raw, []))

    def test_rejects_verdict_mask_contradictions(self):
        for raw in (self.response(expressible=False), self.response(mask=[])):
            with self.subTest(raw=raw), self.assertRaisesRegex(ValueError, "contradicts"):
                decode_response(json.dumps(raw), "#artblog")

    def test_rejects_bad_diagnostic_structure(self):
        for raw in ({"mask": []}, self.response(expressible=1), self.response(meaning=""),
                    self.response(evidence=None), self.response(extra="unexpected")):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                decode_response(json.dumps(raw), "#artblog")

    def test_rejects_invalid_positions_without_repair(self):
        for mask in ([[0, 1]], [{"word": 1, "text": ""}], [[1, 1], [1, 1]]):
            with self.subTest(mask=mask), self.assertRaises(ValueError):
                decode_response(json.dumps(self.response(mask=mask)), "#artblog")

    def test_rejects_duplicate_fields(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            decode_response('{"mask":[],"mask":[]}', "#artblog")


if __name__ == "__main__":
    unittest.main()
