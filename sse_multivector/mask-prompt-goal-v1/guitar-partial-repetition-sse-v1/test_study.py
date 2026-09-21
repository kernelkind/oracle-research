"""Verify the fixed GPRv1 interventions through the actual worker input parser."""

from pathlib import Path
import tempfile
import unittest

import study


class StudyTests(unittest.TestCase):
    def test_same_additions_at_both_levels_and_exact_saved_full_masks(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            inputs = study.prepare(output)
            _, notes = study.bpr._load_request(output / "worker-request.json")
            self.assertEqual(len(notes), 16)
            self.assertEqual(sum(len(n.subjects) for n in notes), 28)
            variants = inputs["variants"]
            self.assertEqual(len(variants), 13)
            for name in ("hashtag", "prose", "all"):
                broad_added = set(map(tuple, variants[f"broad_{name}"]["byte_spans"])) - set(map(tuple, variants["broad_core"]["byte_spans"]))
                detailed_added = set(map(tuple, variants[f"detailed_{name}"]["byte_spans"])) - set(map(tuple, variants["detailed_core"]["byte_spans"]))
                self.assertEqual(broad_added, detailed_added)
            self.assertEqual(variants["broad_all"]["byte_spans"], inputs["saved_broad_ranges"])
            self.assertEqual(variants["detailed_all"]["byte_spans"], inputs["saved_detailed_ranges"])
            self.assertEqual(variants["detailed_core"]["fragments"], [
                "retune", "guitar every time you put a capo on and take it", "off"])
            singles = [v for v in variants.values() if v["single_mention"]]
            self.assertEqual(len(singles), 6)
            self.assertEqual(sorted(v["byte_spans"][0] for v in singles), inputs["saved_broad_ranges"])
            self.assertEqual(len(inputs["anchors"]), 15)
            with self.assertRaises(FileExistsError):
                study.prepare(output)


if __name__ == "__main__":
    unittest.main()
