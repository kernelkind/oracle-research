"""Exercise the actual offline preparation path with complete-note examples."""
import json
import tempfile
import unittest
from pathlib import Path

from sse_multivector import distillation_data


class DistillationDataTests(unittest.TestCase):
    def prepare(self, root, bad_fragment=False):
        text = "é Tea #tea"
        source = {"notes": [
            {"note_id": str(i), "text": text + str(i), "pubkey": str(i // 2)}
            for i in range(6)
        ]}
        annotations = {"notes": [
            {"note_id": n["note_id"], "text": n["text"], "subjects": [
                {"id": "a", "subject": "Tea", "byte_spans": [[3, 6], [8, 11]],
                 "fragments": ["wrong" if bad_fragment else "Tea", "tea"]},
                {"id": "b", "subject": "Tea again", "byte_spans": [[3, 6], [8, 11]],
                 "fragments": ["Tea", "tea"]},
                {"id": "c", "subject": "Drink", "byte_spans": [], "fragments": []},
            ]} for n in source["notes"]
        ]}
        paths = []
        for name, value in [("source", source), ("annotations", annotations)]:
            p = root / (name + ".json")
            p.write_text(json.dumps(value))
            paths.append(p)
        prompt = root / "prompt.txt"
        prompt.write_text("Return masks for the complete note.")
        return distillation_data.prepare(*paths, prompt, "DPv1", 2, "pilot", root / "prepared")

    def test_complete_note_split_and_source_aligned_targets(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self.prepare(root)
            rows = {name: [json.loads(line) for line in
                    (root / "prepared" / (name + ".jsonl")).read_text().splitlines()]
                    for name in ["train", "evaluation", "references"]}
            self.assertEqual(len(rows["train"]), 4)
            self.assertEqual(len(rows["evaluation"]), 2)
            train_authors = {int(n) // 2 for n in manifest["train_note_ids"]}
            eval_authors = {int(n) // 2 for n in manifest["evaluation_note_ids"]}
            self.assertFalse(train_authors & eval_authors)
            for row in rows["train"]:
                target = json.loads(row["completion"][0]["content"])
                self.assertEqual(target, {"masks": [[[2, 2], {"word": 3, "text": "tea"}]]})
                self.assertNotIn("Tea again", row["prompt"][0]["content"])
            self.assertTrue(all(set(row) == {"note_id", "messages"} for row in rows["evaluation"]))
            self.assertTrue(all(len(row["subjects"]) == 3 for row in rows["references"]))
            self.assertEqual(manifest["empty_subject_masks"], 6)
            self.assertEqual(manifest["distinct_nonempty_masks"], 6)
            with self.assertRaises(FileExistsError):
                self.prepare(root)

    def test_bad_source_alignment_stops_before_export(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaisesRegex(ValueError, "fragment"):
                self.prepare(root, bad_fragment=True)
            self.assertFalse((root / "prepared").exists())


if __name__ == "__main__":
    unittest.main()
