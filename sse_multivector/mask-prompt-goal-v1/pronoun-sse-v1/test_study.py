"""Verify intervention positions through the real SSE worker request parser."""
from pathlib import Path
import tempfile
import unittest

import study


class StudyTests(unittest.TestCase):
    def test_only_the_requested_pronoun_is_added(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inputs = study.prepare(root)
            _, notes = study.bpr._load_request(root / "worker-request.json")
            self.assertEqual(sum(len(n.subjects) for n in notes), 22)
            self.assertEqual(len(notes), 16)
            expected = {"NF01-001": "they", "NF02-006": "you"}
            for case in inputs["cases"]:
                variants = case["variants"]
                original = variants["current"]["byte_spans"]
                added = sorted(set(map(tuple, variants["with_pronoun"]["byte_spans"])) - set(map(tuple, original)))
                self.assertEqual(len(added), 1)
                a, b = added[0]
                self.assertEqual(case["text"].encode()[a:b].decode(), expected[case["id"]])
                self.assertEqual(variants["pronoun_only"]["byte_spans"], [list(added[0])])
                self.assertEqual(variants["current"]["fragments"], case["saved_fragments"])
                self.assertEqual(variants["full_post"]["byte_spans"], [[0, len(case["text"].encode())]])
                self.assertEqual(case["anchors"][0]["text"], case["subject"])
            # The curly apostrophes in NF02 make character offsets != byte offsets.
            second = inputs["cases"][1]
            self.assertNotEqual(second["variants"]["current"]["byte_spans"][0][0], 85)
            with self.assertRaises(FileExistsError):
                study.prepare(root)


if __name__ == "__main__":
    unittest.main()
