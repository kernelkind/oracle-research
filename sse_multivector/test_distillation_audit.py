"""Audit selected inputs while mixed sources and final-test content are sealed."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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
        selected = root / "registry" / "inputs.json"
        write_json(selected, {"schema_version": 1, "posts": [
            {"note_id": n["note_id"], "pubkey": n["pubkey"],
             "split": "train" if i < 2 else "validation",
             "text_sha256": hashlib.sha256(n["text"].encode()).hexdigest()}
            for i, n in enumerate(notes[:3])]})
        write_json(selected.parent / "manifest.json", {
            "schema_version": 1, "files": {"inputs.json": sha256(selected)},
            "protected_sources": {str(source): sha256(source), str(labels): sha256(labels)}})
        # An audit must work without these mixed or sealed files.
        source.unlink()
        labels.unlink()
        (data / "references.jsonl").unlink()
        (data / "test.jsonl").unlink()
        return selected, data

    def test_selected_registry_needs_no_mixed_source_or_final_test_content(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            selected, data = self.prepare(root)
            forbidden = {root / "source.json", data / "test.jsonl",
                         data / "references.jsonl", root / "labels.json"}
            original_open = Path.open

            def allowed_open(path, *args, **kwargs):
                if path in forbidden:
                    raise AssertionError(f"opened sealed or mixed file: {path}")
                return original_open(path, *args, **kwargs)

            with patch.object(Path, "open", allowed_open):
                result = distillation_audit.audit(selected, data)
            self.assertEqual(result["splits"]["test"], {"notes": 1, "content_opened": False})
            self.assertFalse(result["reserved_final_test_content_opened"])
            self.assertEqual(result["training_subjects"]["entries"], 4)

    def test_audits_complete_inputs_and_only_training_subjects(self):
        with tempfile.TemporaryDirectory() as temp:
            source, data = self.prepare(Path(temp))
            result = distillation_audit.audit(source, data)
            self.assertEqual(result["splits"]["train"]["notes"], 2)
            self.assertEqual(result["splits"]["validation"]["authors"], 1)
            self.assertEqual(result["splits"]["test"], {"notes": 1, "content_opened": False})
            self.assertEqual(result["training_subjects"]["entries"], 4)
            self.assertEqual(result["training_subjects"]["parent_child_candidates"], 2)
            self.assertEqual(result["training_subjects"]["same_subject_cross_note_groups"], 2)
            self.assertEqual(result["shr_relation_labels"], 0)
            self.assertFalse(result["reserved_final_test_answers_opened"])
            self.assertFalse(result["validation_references_opened"])
            self.assertEqual(set(result["hashes"]), {
                str(source), str(source.parent / "manifest.json"), str(data / "manifest.json"),
                str(data / "train.jsonl"), str(data / "evaluation.jsonl")})

    def test_changed_training_bytes_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            source, data = self.prepare(Path(temp))
            with (data / "train.jsonl").open("a") as output:
                output.write("\n")
            with self.assertRaisesRegex(ValueError, "hash mismatch: train.jsonl"):
                distillation_audit.audit(source, data)

    def test_hash_bound_registry_cannot_cross_author_splits(self):
        with tempfile.TemporaryDirectory() as temp:
            source, data = self.prepare(Path(temp))
            notes = json.loads(source.read_text())
            notes["posts"][2]["pubkey"] = "0"
            write_json(source, notes)
            path = source.parent / "manifest.json"
            manifest = json.loads(path.read_text())
            manifest["files"][source.name] = sha256(source)
            write_json(path, manifest)
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

    def test_input_only_validation_file_cannot_contain_answers(self):
        with tempfile.TemporaryDirectory() as temp:
            source, data = self.prepare(Path(temp))
            path = data / "evaluation.jsonl"
            row = json.loads(path.read_text())
            row["subjects"] = "forbidden"
            path.write_text(json.dumps(row) + "\n")
            manifest = json.loads((data / "manifest.json").read_text())
            manifest["outputs"][path.name] = sha256(path)
            write_json(data / "manifest.json", manifest)
            with self.assertRaisesRegex(ValueError, "input-only"):
                distillation_audit.audit(source, data)

    def test_changed_registry_bytes_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            source, data = self.prepare(Path(temp))
            with source.open("a") as output:
                output.write("\n")
            with self.assertRaisesRegex(ValueError, "selected registry hash mismatch"):
                distillation_audit.audit(source, data)


if __name__ == "__main__":
    unittest.main()
