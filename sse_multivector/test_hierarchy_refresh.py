"""Refresh preparation exercises the actual saved-batch configuration parser."""
import tempfile
import unittest
import subprocess
from pathlib import Path
from sse_multivector import hierarchy_refresh as refresh


class RefreshTests(unittest.TestCase):
    def test_review_launcher_rejects_unsupported_arguments(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                ["bash", str(refresh.SSE / "run-hierarchy-refresh.sh"), "--unknown"],
                cwd=directory, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("Usage:", result.stderr)

    def test_empty_and_duplicate_masks_preserve_all_subjects(self):
        source = {"notes": [{"note_id": "a" * 64, "text": "é Tea Tea", "subjects": [
            {"number": "1", "subject": "Tea"}, {"number": "2", "subject": "Drink"},
            {"number": "3", "subject": "Tea"}]}]}
        checks = [{"item_id": "M001", "status": "valid", "ranges": [{"start": 6, "end": 9}]},
                  {"item_id": "M002", "status": "valid", "ranges": []},
                  {"item_id": "M003", "status": "valid", "ranges": [{"start": 6, "end": 9}]}]
        request, mapping, preserved = refresh.encode_inputs(source, checks)
        self.assertEqual(len(request), 1)
        self.assertEqual(len(request[0]["subjects"]), 1)
        self.assertEqual(request[0]["subjects"][0]["byte_spans"], [[7, 10]])
        self.assertEqual(len(mapping["vectors"][0]["subject_entries"]), 2)
        self.assertEqual(len(preserved["notes"][0]["subjects"]), 3)
        self.assertEqual(preserved["notes"][0]["subjects"][1]["byte_spans"], [])

    def test_preserves_original_collection_and_reuses_saved_subjects(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            refresh.prepare(out)
            config = refresh.pipeline.PromptRunnerConfig.load(out / "subject-config.json")
            seeds = refresh.read(out / "saved-subjects.json")["notes"]
            self.assertEqual(len(seeds), 12)
            self.assertEqual(len(config.prompts), 88)
            self.assertEqual(len(refresh.read(out / "source.json")["notes"]), 100)
            self.assertEqual(config.model, "gpt-6-astra")
            self.assertEqual(config.reasoning_effort, "low")
            with self.assertRaises(FileExistsError):
                refresh.prepare(out)


if __name__ == "__main__":
    unittest.main()
