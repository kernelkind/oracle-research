"""Exercise the actual offline preparation path with complete-note examples."""
import json
import tempfile
import unittest
from pathlib import Path

from sse_multivector import distillation_data


class DistillationDataTests(unittest.TestCase):
    def test_saved_training_prompt_must_still_bind_full_instruction_and_note(self):
        from sse_multivector.distillation_run import load_data, read_json, write_json, sha256
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.prepare(root)
            output = root / "subjects"
            distillation_data.prepare(root / "source.json", root / "annotations.json", root / "subjects.txt",
                None, "AS-test", None, 2, "pilot", output, tasks=("subjects",))
            path = output / "train.jsonl"
            rows = [json.loads(line) for line in path.read_text().splitlines()]
            rows[0]["prompt"][0]["content"] = "Short instruction\n\n<post>\nwrong note\n</post>"
            path.write_text("".join(json.dumps(row) + "\n" for row in rows))
            manifest = read_json(output / "manifest.json")
            manifest["outputs"][path.name] = sha256(path)
            write_json(output / "manifest.json", manifest)
            with self.assertRaisesRegex(ValueError, "subject prompt differs"):
                load_data(output)

    def test_frozen_three_way_split_is_preserved_and_reserved(self):
        from sse_multivector.distillation_run import load_data
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.prepare(root)
            splits = root / "splits.json"
            assignments = {"train": ["3", "2"], "validation": ["0", "1"], "test": ["5", "4"]}
            splits.write_text(json.dumps(assignments))
            output = root / "three-way"
            manifest = distillation_data.prepare(root / "source.json", root / "annotations.json",
                root / "subjects.txt", None, "AS-test", None, 2, "pilot", output,
                tasks=("subjects",), splits_path=splits)
            data = load_data(output)
            self.assertEqual([r["note_id"] for r in data["train"]], assignments["train"])
            self.assertEqual([r["note_id"] for r in data["evaluation"]], assignments["validation"])
            self.assertEqual([r["note_id"] for r in data["test"]], assignments["test"])
            self.assertEqual(manifest["test_note_ids"], assignments["test"])
            self.assertEqual({r["split"] for r in data["references"].values()}, {"train", "evaluation", "test"})
            assignments["train"], assignments["test"] = ["2", "4"], ["3", "5"]
            splits.write_text(json.dumps(assignments))
            with self.assertRaisesRegex(ValueError, "author/content group"):
                distillation_data.prepare(root / "source.json", root / "annotations.json",
                    root / "subjects.txt", None, "AS-test", None, 2, "pilot", root / "bad",
                    tasks=("subjects",), splits_path=splits)

    def prepare(self, root, bad_fragment=False):
        text = "é Tea #tea"
        source = {"notes": [
            {"note_id": str(i), "text": text + str(i), "pubkey": str(i // 2)}
            for i in range(6)
        ]}
        annotations = {"notes": [
            {"note_id": n["note_id"], "text": n["text"], "subjects": [
                {"id": "a", "number": "1", "context": "Tea is named.", "subject": "Tea", "byte_spans": [[3, 6], [8, 11]],
                 "diagnostics": {"evidence": "Tea and tea name it.", "expressible": True, "meaning": "Tea"},
                 "fragments": ["wrong" if bad_fragment else "Tea", "tea"]},
                {"id": "b", "number": "2", "context": "Tea occurs again.", "subject": "Tea again", "byte_spans": [[3, 6], [8, 11]],
                 "diagnostics": {"meaning": "Tea again", "expressible": True, "evidence": "Tea is repeated."},
                 "fragments": ["Tea", "tea"]},
                {"id": "c", "number": "3", "context": "Tea is a drink.", "subject": "Drink", "byte_spans": [], "fragments": [],
                 "diagnostics": {"meaning": "Drinks generally", "expressible": False, "evidence": "Only tea is named."}},
            ]} for n in source["notes"]
        ]}
        paths = []
        for name, value in [("source", source), ("annotations", annotations)]:
            p = root / (name + ".json")
            p.write_text(json.dumps(value))
            paths.append(p)
        subject_prompt = root / "subjects.txt"
        subject_prompt.write_text("Return the subject hierarchy.")
        mask_prompt = root / "masks.txt"
        mask_prompt.write_text("{POST}\n{INDEXED_POST}\nFixed subject: {SUBJECT}")
        return distillation_data.prepare(*paths, subject_prompt, mask_prompt,
                                         "AS-test", "MP-test", 2, "pilot", root / "prepared")

    def test_complete_note_split_and_source_aligned_targets(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self.prepare(root)
            rows = {name: [json.loads(line) for line in
                    (root / "prepared" / (name + ".jsonl")).read_text().splitlines()]
                    for name in ["train", "evaluation", "references"]}
            self.assertEqual(len(rows["train"]), 16)
            self.assertEqual(len(rows["evaluation"]), 2)
            train_authors = {int(n) // 2 for n in manifest["train_note_ids"]}
            eval_authors = {int(n) // 2 for n in manifest["evaluation_note_ids"]}
            self.assertFalse(train_authors & eval_authors)
            subjects = [r for r in rows["train"] if r["task"] == "subjects"]
            masks = [r for r in rows["train"] if r["task"] == "mask"]
            self.assertEqual(len(subjects), 4)
            self.assertEqual(len(masks), 12)
            for row in subjects:
                target = json.loads(row["completion"][0]["content"])
                self.assertEqual(len(target["subjects"]), 3)
                self.assertEqual(set(target["subjects"][0]), {"number", "context", "subject"})
                self.assertNotIn("Tea again", row["prompt"][0]["content"])
            targets = [json.loads(r["completion"][0]["content"]) for r in masks]
            self.assertTrue(all(list(t) == ["meaning", "expressible", "evidence", "mask"] for t in targets))
            self.assertEqual(sum(not t["expressible"] for t in targets), 4)
            self.assertEqual(targets[0]["mask"], [[2, 2], {"word": 3, "text": "tea"}])
            self.assertIn("Fixed subject: Tea", masks[0]["prompt"][0]["content"])
            self.assertNotIn("Tea is named.", masks[0]["prompt"][0]["content"])
            self.assertTrue(all(set(row) == {"note_id", "messages"} for row in rows["evaluation"]))
            self.assertTrue(all(len(row["subjects"]) == 3 for row in rows["references"]))
            self.assertEqual(manifest["empty_subject_masks"], 6)
            self.assertEqual(manifest["training_examples"], {"subjects": 4, "mask": 12})
            with self.assertRaises(FileExistsError):
                self.prepare(root)

    def test_bad_source_alignment_stops_before_export(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaisesRegex(ValueError, "fragment"):
                self.prepare(root, bad_fragment=True)
            self.assertFalse((root / "prepared").exists())

    def test_subjects_only_preparation_needs_no_mask_labels_or_prompt(self):
        from sse_multivector.distillation_run import load_data
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.prepare(root)
            annotations = json.loads((root / "annotations.json").read_text())
            for note in annotations["notes"]:
                note["subjects"] = [{key: value for key, value in subject.items()
                                     if key in ("number", "context", "subject")}
                                    for subject in note["subjects"]]
            (root / "subject-labels.json").write_text(json.dumps(annotations))
            result = distillation_data.prepare(root / "source.json", root / "subject-labels.json",
                root / "subjects.txt", None, "AS-test", None, 2, "pilot", root / "subject-data",
                tasks=("subjects",))
            data = load_data(root / "subject-data", None)
            self.assertEqual(result["tasks"], {"subjects": "AS-test"})
            self.assertEqual(result["training_examples"], {"subjects": 4})
            self.assertEqual(len(data["train"]), 4)
            self.assertEqual({row["task"] for row in data["train"]}, {"subjects"})
            self.assertEqual({row["note_id"] for row in data["train"]}, set(result["train_note_ids"]))


if __name__ == "__main__":
    unittest.main()
