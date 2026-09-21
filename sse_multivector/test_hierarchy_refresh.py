"""Refresh preparation exercises the actual saved-batch configuration parser."""
import tempfile
import unittest
import subprocess
from pathlib import Path
from sse_multivector import hierarchy_refresh as refresh


class RefreshTests(unittest.TestCase):
    def test_frozen_subject_mask_registry_resolves_to_refresh_prompt(self):
        registry = refresh.read(refresh.SSE / "mask-prompt-versions.json")
        self.assertIn("frozen_subject_mask_prompt", registry)
        self.assertNotIn("frozen_mask_prompt_version", registry)
        frozen = registry["frozen_subject_mask_prompt"]
        self.assertEqual(frozen["version"], "MPv3.43")
        prompt = refresh.SSE / frozen["prompt_path"]
        self.assertEqual(prompt, refresh.MP)
        self.assertEqual(refresh.sha(prompt), frozen["prompt_sha256"])
        self.assertEqual(frozen["mask_format"], "word_positions")
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            refresh.save(out / "subjects.json", {"schema_version": 1, "notes": [{
                "note_id": "test", "text": "Tea helps.", "subjects": ["Tea"]}]})
            refresh.save(out / "config.json", {
                "schema_version": 1, "runner_binary": str(refresh.SSE / "run-model.sh"),
                "provider": "openai-codex", "auth_file": None,
                "input_path": "subjects.json", "prompt_path": str(prompt),
                "run_directory": "run", "model": "gpt-6-astra", "reasoning_effort": "low",
                "mask_format": frozen["mask_format"],
                "output_schema": refresh.read(refresh.SSE / frozen["output_schema_path"]),
            })
            config, metadata, _ = refresh.pipeline._load_mask_batch(out / "config.json")
        self.assertEqual(metadata["prompt_sha256"], frozen["prompt_sha256"])
        self.assertEqual(metadata["mask_format"], "word_positions")
        self.assertEqual(len(config.prompts), 1)
        self.assertIn("[1]Tea [2]helps.", config.prompts[0].text)
        self.assertNotIn("{SUBJECT}", config.prompts[0].text)
        self.assertEqual(config.output_schema["required"], ["meaning", "expressible", "evidence", "mask"])

    def test_legacy_mask_configs_still_resolve_their_pinned_versions(self):
        registry = refresh.read(refresh.SSE / "mask-prompt-versions.json")
        self.assertEqual(registry.get("frozen_takeaway_mask_prompt_version"), "MPv3.4")
        for name in ("crec-119-generation-v1.json", "crec-119-generation-v2.json"):
            with self.subTest(config=name):
                raw = refresh.read(refresh.SSE / name)["mask"]
                config = refresh.pipeline.StageConfig.load(raw, "mask", refresh.SSE)
                self.assertEqual(config.prompt_version, raw["prompt_version"])
                self.assertEqual(config.prompt, registry[raw["prompt_version"]])

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
