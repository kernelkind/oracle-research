"""Audit the prepared subject data without opening held-out answers."""
import json
import tempfile
import unittest
from pathlib import Path

from sse_multivector import distillation_audit, distillation_data
from sse_multivector.distillation_run import sha256, write_json


class DistillationAuditTests(unittest.TestCase):
    def prepare(self, root):
        notes = [{"note_id": str(i), "pubkey": str(i), "text": f"Tea discussion {i}"}
                 for i in range(4)]
        source = root / "source.json"
        write_json(source, {"schema_version": 1, "notes": notes})
        labels = root / "labels.json"
        write_json(labels, {"notes": [{**n, "subjects": [
            {"number": "1", "subject": "Tea", "context": "Tea generally."},
            {"number": "1.1", "subject": "Black tea", "context": "Black tea generally."},
        ]} for n in notes]})
        prompt = root / "prompt.txt"
        prompt.write_text("Return the subject hierarchy.")
        splits = root / "splits.json"
        write_json(splits, {"train": ["0", "1"], "validation": ["2"], "test": ["3"]})
        data = root / "prepared"
        distillation_data.prepare(source, labels, prompt, None, "AS-test", None,
                                  1, "fixed", data, tasks=("subjects",), splits_path=splits)
        # Neither of these files is needed for an input/training-only audit.
        labels.unlink()
        (data / "references.jsonl").unlink()
        return source, data

    def test_audits_complete_inputs_and_only_training_subjects(self):
        with tempfile.TemporaryDirectory() as temp:
            source, data = self.prepare(Path(temp))
            result = distillation_audit.audit(source, data)
            self.assertEqual(result["splits"]["train"]["notes"], 2)
            self.assertEqual(result["splits"]["test"]["authors"], 1)
            self.assertEqual(result["training_subjects"]["entries"], 4)
            self.assertEqual(result["training_subjects"]["parent_child_candidates"], 2)
            self.assertEqual(result["training_subjects"]["same_subject_cross_note_groups"], 2)
            self.assertEqual(result["shr_relation_labels"], 0)
            self.assertFalse(result["held_out_answers_opened"])
            self.assertEqual(set(result["hashes"]), {
                str(source), str(data / "manifest.json"),
                str(data / "train.jsonl"), str(data / "evaluation.jsonl"), str(data / "test.jsonl")})

    def test_changed_training_bytes_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            source, data = self.prepare(Path(temp))
            with (data / "train.jsonl").open("a") as output:
                output.write("\n")
            with self.assertRaisesRegex(ValueError, "hash mismatch: train.jsonl"):
                distillation_audit.audit(source, data)

    def test_hash_bound_source_cannot_cross_author_splits(self):
        with tempfile.TemporaryDirectory() as temp:
            source, data = self.prepare(Path(temp))
            notes = json.loads(source.read_text())
            notes["notes"][3]["pubkey"] = "0"
            write_json(source, notes)
            manifest = json.loads((data / "manifest.json").read_text())
            manifest["inputs"][str(source)] = sha256(source)
            write_json(data / "manifest.json", manifest)
            with self.assertRaisesRegex(ValueError, "author crosses frozen splits"):
                distillation_audit.audit(source, data)

    def test_rehashed_training_prompt_must_preserve_the_source(self):
        with tempfile.TemporaryDirectory() as temp:
            source, data = self.prepare(Path(temp))
            path = data / "train.jsonl"
            rows = [json.loads(line) for line in path.read_text().splitlines()]
            rows[0]["prompt"][0]["content"] += " extra instruction"
            path.write_text("".join(json.dumps(row) + "\n" for row in rows))
            manifest = json.loads((data / "manifest.json").read_text())
            manifest["outputs"][path.name] = sha256(path)
            write_json(data / "manifest.json", manifest)
            with self.assertRaisesRegex(ValueError, "prompt differs"):
                distillation_audit.audit(source, data)

    def test_input_only_test_file_cannot_contain_answers(self):
        with tempfile.TemporaryDirectory() as temp:
            source, data = self.prepare(Path(temp))
            path = data / "test.jsonl"
            row = json.loads(path.read_text())
            row["subjects"] = "forbidden"
            path.write_text(json.dumps(row) + "\n")
            manifest = json.loads((data / "manifest.json").read_text())
            manifest["outputs"][path.name] = sha256(path)
            write_json(data / "manifest.json", manifest)
            with self.assertRaisesRegex(ValueError, "input-only"):
                distillation_audit.audit(source, data)


if __name__ == "__main__":
    unittest.main()
