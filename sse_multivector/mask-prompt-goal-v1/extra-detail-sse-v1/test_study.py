"""Check the narrow intervention through the production SSE request parser."""
from pathlib import Path
import tempfile
import unittest

import study


class StudyTests(unittest.TestCase):
    def test_only_named_words_are_removed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inputs = study.prepare(root)
            _, notes = study.bpr._load_request(root / "worker-request.json")
            self.assertEqual(len(notes), 23)
            self.assertEqual(sum(len(n.subjects) for n in notes), 27)
            parsed = {s.subject_id: (n.text, s.byte_spans) for n in notes for s in n.subjects}
            for case in inputs["cases"]:
                raw = case["text"].encode()
                variants = case["variants"]
                self.assertEqual(variants["current"]["fragments"], case["saved_fragments"])
                positions = {}
                for name, variant in variants.items():
                    text, spans = parsed[variant["subject_id"]]
                    self.assertEqual(text, case["text"])
                    self.assertEqual([list(s) for s in spans], variant["byte_spans"])
                    positions[name] = {i for a, b in spans for i in range(a, b) if not chr(raw[i]).isspace()}
                self.assertLess(positions["removed"], positions["current"])
                deleted = bytes(raw[i] for i in sorted(positions["current"] - positions["removed"]))
                self.assertEqual(deleted, b"tosee" if case["id"] == "F05" else b"Looking")
                self.assertEqual(case["anchors"][0]["text"], case["subject"])
                fragments = variants["removed"]["fragments"]
                if case["id"] == "B10":
                    self.assertIn("reaching for it.", fragments)
                if case["id"] == "B14":
                    self.assertIn("Going to wait a while longer to give her any, though.", fragments)
                if case["id"] == "F05":
                    self.assertIn("I was very pleased", fragments)
                    self.assertIn("this recipe turned out", fragments)
            with self.assertRaises(FileExistsError):
                study.prepare(root)


if __name__ == "__main__":
    unittest.main()
