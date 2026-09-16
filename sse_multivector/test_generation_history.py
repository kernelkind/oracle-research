"""Read-only compatibility for saved pre-pi generation evidence."""
import hashlib
import json
import unittest
import tempfile
from pathlib import Path


class GenerationHistoryTests(unittest.TestCase):
    def test_frozen_runner_bytes_remain_verifiable_without_an_execution_tool(self):
        from sse_multivector import generation_history as history

        path = Path(__file__).with_name("codex_exec.py")
        self.assertFalse(path.exists())
        self.assertEqual(
            "ebf1942737069a49146d7336c6936dd2fa5cdd8d4b6a2b24274f01bc9f83e2fe",
            hashlib.sha256(history.source_bytes(path)).hexdigest(),
        )
        self.assertFalse(hasattr(history, "run"))
        self.assertFalse(hasattr(history, "run_prompts"))

    def test_saved_config_can_be_read_without_live_credentials_or_generation(self):
        from sse_multivector import generation_history as history

        path = Path(__file__).parent / "subject-prompt-goal-v1/asv6.23-validation-v1/final/H01-t1/config.json"
        config = history.PromptRunnerConfig.load(path)
        self.assertEqual(config.model, "gpt-6-astra")
        self.assertEqual(config.reasoning_effort, "low")
        self.assertEqual(len(config.prompts), 1)

    def test_saved_receipt_references_preserve_exact_line_hashes(self):
        from sse_multivector import generation_history as history

        record = {
            "manifest_sha256": "a" * 64,
            "wrapper_sha256": history.LEGACY_WRAPPER_SHA256,
            "job_key": "prompt:example",
            "status": "succeeded",
            "attempt": 1,
        }
        payload = history._ordered_json_bytes(record).replace(b"\n", b"") + b"\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "results.jsonl"
            path.write_bytes(payload)
            references = {}
            result = history._load_latest_results(
                path, "a" * 64,
                history.RunnerProvenance(history.LEGACY_WRAPPER_SHA256,
                                         history.LEGACY_WRAPPER_SHA256, ()),
                references,
            )
            self.assertEqual(result["prompt:example"], record)
            reference = references["prompt:example"]
            self.assertEqual(reference.line, 1)
            self.assertEqual(reference.attempt, 1)
            self.assertEqual(reference.sha256, hashlib.sha256(payload).hexdigest())

    def test_existing_experiment_manifest_and_receipts_still_verify(self):
        from sse_multivector import generation_history as history

        directory = Path(__file__).parent / "subject-prompt-goal-v1/asv6.23-validation-v1/final/H01-t1"
        config = history.PromptRunnerConfig.load(directory / "config.json")
        manifest_path = config.run_directory / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        self.assertEqual(history._build_prompt_manifest(config, manifest["codex_version"]), manifest)
        results = history._load_latest_results(
            config.run_directory / "results.jsonl", history._sha256_file(manifest_path),
            history.RunnerProvenance(history.LEGACY_WRAPPER_SHA256,
                                     history.LEGACY_WRAPPER_SHA256, ()),
        )
        self.assertEqual(set(results), {"prompt:H01-t1"})
        self.assertEqual(results["prompt:H01-t1"]["status"], "succeeded")


if __name__ == "__main__":
    unittest.main()
